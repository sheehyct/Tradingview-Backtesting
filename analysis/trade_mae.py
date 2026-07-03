"""Per-trade MAE and 1x-cash-margin solvency check (Codex TVB-3 finding 2).

Question: would the SHORT leg have survived on the real venue at 1x cash margin?
TradingView simulates with margin 0/0 (no margin calls -- the TVB-3 deadlock fix),
so it happily rides any adverse excursion; a real venue liquidates.

Hyperliquid isolated-margin model: maintenance margin fraction mm = 1/(2*maxLev)
(xyz:MSTR maxLev=10 -> mm=5%). A short at leverage L (notional = L*equity)
liquidates when price reaches r* = (1+L)/(L*(1+mm)) of entry: L=1 -> +90.5%
adverse, L=2 -> +42.9%, L=3 -> +27.0%, L=5 -> +14.3%. A 1x long cannot liquidate.

MAE here = worst adverse excursion vs ENTRY PRICE from bar extremes over the
trade's bar span [et, xt] (long: 1 - min(low)/ep; short: max(high)/ep - 1).
CONSERVATIVE: the entry bar's extreme may precede the intrabar entry, so measured
MAE can only overstate true MAE. Cross-checked against TV's own per-trade
drawdown (ddp) captured in the TVB-6 dumps.

Usage:
    uv run python analysis/trade_mae.py <dump.json> <bars.json> [--max-lev 10]

bars.json = scripts/tv_bars.mjs export; dump.json = scripts/tv_dump.mjs (TVB-6+
format with et/xt/ep/ddp).
"""

from __future__ import annotations

import argparse
import json
from bisect import bisect_left, bisect_right


def liq_threshold_short(leverage: float, mm: float) -> float:
    """Adverse-move fraction at which an isolated short liquidates.

    account = E*(1 + L - L*r), maintenance = mm*L*E*r -> r* = (1+L)/(L*(1+mm));
    returns r* - 1 (e.g. 0.905 at L=1, mm=0.05).
    """
    return (1.0 + leverage) / (leverage * (1.0 + mm)) - 1.0


def max_survivable_leverage(worst_mae: float, mm: float) -> float:
    """Largest L whose liquidation threshold still exceeds worst_mae."""
    r = 1.0 + worst_mae
    denom = r * (1.0 + mm) - 1.0
    return float("inf") if denom <= 0 else 1.0 / denom


def trade_maes(trades: list[dict], bars: list[list[float]]) -> list[dict]:
    """MAE vs entry for each closed trade with usable fields.

    bars: sorted [t_ms, o, h, l, c, ...] rows. Trades missing et/xt/ep/dir or
    marked open are skipped (counted by the caller via len()).
    """
    ts = [b[0] for b in bars]
    out = []
    for t in trades:
        if t.get("open") or t.get("et") is None or t.get("xt") is None:
            continue
        ep, d = t.get("ep"), t.get("dir")
        if ep is None or d not in ("le", "se"):
            continue
        lo_i = bisect_left(ts, t["et"])
        hi_i = bisect_right(ts, t["xt"])
        span = bars[lo_i:hi_i]
        if not span:
            continue
        if d == "le":
            mae = max(0.0, 1.0 - min(b[3] for b in span) / ep)
        else:
            mae = max(0.0, max(b[2] for b in span) / ep - 1.0)
        out.append(
            {"dir": d, "mae": mae, "ep": ep, "et": t["et"], "ddp": t.get("ddp"), "pp": t.get("pp")}
        )
    return out


def _pct(v, n):
    return f"{100.0 * v / n:.1f}%" if n else "n/a"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dump")
    ap.add_argument("bars")
    ap.add_argument(
        "--max-lev",
        type=float,
        default=10.0,
        help="venue max leverage for the instrument (sets mm = 1/(2*maxLev))",
    )
    args = ap.parse_args()

    with open(args.dump, encoding="utf-8") as f:
        dump = json.load(f)
    with open(args.bars, encoding="utf-8") as f:
        bars = [[b[0] * 1000, *b[1:]] for b in json.load(f)["bars"]]
    bars.sort(key=lambda b: b[0])

    mm = 1.0 / (2.0 * args.max_lev)
    rows = trade_maes(dump.get("list", []), bars)
    print(f"{args.dump}: {len(rows)} closed trades analyzed (mm={mm:.3f})")

    for d, label in (("se", "SHORT"), ("le", "LONG")):
        sub = sorted((r["mae"] for r in rows if r["dir"] == d))
        if not sub:
            continue
        n = len(sub)
        worst = sub[-1]
        p99 = sub[int(0.99 * (n - 1))]
        med = sub[n // 2]
        print(
            f"  {label}: n={n}  median {med * 100:.2f}%  p99 {p99 * 100:.2f}%  "
            f"worst {worst * 100:.2f}%"
        )
        if d == "se":
            for lev in (1, 2, 3, 5):
                thr = liq_threshold_short(lev, mm)
                breaches = sum(1 for m in sub if m >= thr)
                print(
                    f"    {lev}x liq threshold +{thr * 100:.1f}%: "
                    f"{breaches} breaches ({_pct(breaches, n)})"
                )
            print(
                f"    max survivable short leverage at worst MAE: "
                f"{max_survivable_leverage(worst, mm):.2f}x"
            )

    # cross-check vs TV's per-trade drawdown where present
    pairs = [(r["mae"], r["ddp"]) for r in rows if r["ddp"] is not None]
    if pairs:
        diffs = sorted(abs(a - b) for a, b in pairs)
        print(
            f"  ddp cross-check: n={len(pairs)}  median |mae-ddp| "
            f"{diffs[len(diffs) // 2] * 100:.3f}pp  max {diffs[-1] * 100:.3f}pp"
        )


if __name__ == "__main__":
    main()
