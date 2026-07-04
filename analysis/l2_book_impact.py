"""Live L2 order-book impact sampling for taker orders at strategy size.

Question (TVB-6 carry): the backtest charges slippage as a FIXED s ticks/fill
({1,10,25,50} pre-registered band). What does crossing the real xyz book cost
at strategy size? This module samples the live Hyperliquid L2 book (public
info API, type=l2Book) and prices a market order of each requested size
against it, reporting impact vs MID (half-spread + depth walk = the honest
per-fill cost, comparable to the s-band) and vs TOUCH (depth walk only).

Venue tick note: HL prices to 5 significant figures, so the venue's effective
price granularity is price-dependent (at $106 it is $0.01) while the TV chart
mintick for xyz:MSTR is 0.001. Impacts are therefore reported in bps AND in
TV-tick equivalents (impact_usd / mintick) for direct comparison with the
slippage-band rows in docs/TVB2_control_AB_rerun.md.

The raw samples are TIME-PERISHABLE evidence (the book is live state); commit
the --out file alongside the datasheet section it supports.

Usage:
    uv run python analysis/l2_book_impact.py --coin xyz:MSTR \\
        --sizes 10,30,60,90,150,300 --samples 20 --interval 15 \\
        --mintick 0.001 --out analysis/reference/tvb7_l2_xyzMSTR.json
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.request

API_URL = "https://api.hyperliquid.xyz/info"


def parse_levels(raw_side: list[dict]) -> list[tuple[float, float]]:
    """[{px, sz, n}, ...] -> [(px, sz), ...] floats, order preserved (best first)."""
    return [(float(lv["px"]), float(lv["sz"])) for lv in raw_side]


def walk_book(levels: list[tuple[float, float]], size: float) -> dict:
    """Price a taker fill of `size` against one book side (best level first).

    Returns {vwap, worst_px, filled, exhausted}. vwap is None when the side is
    empty; exhausted=True means the visible book held less than `size` (vwap
    then covers only the filled part -- an UNDERSTATEMENT of true impact).
    """
    remaining = size
    cost = 0.0
    filled = 0.0
    worst = None
    for px, sz in levels:
        take = min(sz, remaining)
        if take <= 0.0:
            break
        cost += take * px
        filled += take
        worst = px
        remaining -= take
        if remaining <= 1e-12:
            break
    if filled <= 0.0:
        return {"vwap": None, "worst_px": None, "filled": 0.0, "exhausted": True}
    return {
        "vwap": cost / filled,
        "worst_px": worst,
        "filled": filled,
        "exhausted": filled + 1e-12 < size,
    }


def snapshot_impact(book: dict, sizes: list[float]) -> dict:
    """Per-size, per-side impact rows for one l2Book response."""
    bids = parse_levels(book["levels"][0])
    asks = parse_levels(book["levels"][1])
    if not bids or not asks:
        return {"time": book.get("time"), "error": "empty book side", "rows": []}
    best_bid, best_ask = bids[0][0], asks[0][0]
    mid = 0.5 * (best_bid + best_ask)
    rows = []
    for size in sizes:
        for side, levels, sign, touch in (
            ("buy", asks, 1.0, best_ask),
            ("sell", bids, -1.0, best_bid),
        ):
            w = walk_book(levels, size)
            if w["vwap"] is None:
                continue
            impact_usd = sign * (w["vwap"] - mid)
            touch_usd = sign * (w["vwap"] - touch)
            rows.append(
                {
                    "size": size,
                    "side": side,
                    "vwap": w["vwap"],
                    "worst_px": w["worst_px"],
                    "filled": w["filled"],
                    "exhausted": w["exhausted"],
                    "impact_usd": impact_usd,
                    "impact_frac": impact_usd / mid,
                    "touch_usd": touch_usd,
                }
            )
    return {
        "time": book.get("time"),
        "mid": mid,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread_usd": best_ask - best_bid,
        "spread_frac": (best_ask - best_bid) / mid,
        "rows": rows,
    }


def fetch_l2(coin: str, timeout_s: float = 10.0) -> dict:
    body = json.dumps({"type": "l2Book", "coin": coin}).encode()
    req = urllib.request.Request(API_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return json.load(resp)


def aggregate(samples: list[dict], mintick: float) -> list[dict]:
    """Median/p90/max impact per (side, size) across snapshot samples."""
    groups: dict[tuple[str, float], list[dict]] = {}
    for s in samples:
        for r in s.get("rows", []):
            groups.setdefault((r["side"], r["size"]), []).append(r)

    def _pctile(vals: list[float], q: float) -> float:
        vs = sorted(vals)
        return vs[min(len(vs) - 1, int(q * (len(vs) - 1) + 0.5))]

    out = []
    for (side, size), rows in sorted(groups.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        usd = [r["impact_usd"] for r in rows]
        frac = [r["impact_frac"] for r in rows]
        out.append(
            {
                "side": side,
                "size": size,
                "n": len(rows),
                "exhausted_n": sum(1 for r in rows if r["exhausted"]),
                "med_usd": _pctile(usd, 0.5),
                "p90_usd": _pctile(usd, 0.9),
                "max_usd": max(usd),
                "med_bps": 1e4 * _pctile(frac, 0.5),
                "p90_bps": 1e4 * _pctile(frac, 0.9),
                "med_tvticks": _pctile(usd, 0.5) / mintick,
                "p90_tvticks": _pctile(usd, 0.9) / mintick,
            }
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--coin", default="xyz:MSTR")
    ap.add_argument("--sizes", default="10,30,60,90,150,300")
    ap.add_argument("--samples", type=int, default=20)
    ap.add_argument("--interval", type=float, default=15.0, help="seconds between samples")
    ap.add_argument("--mintick", type=float, default=0.001, help="TV chart mintick")
    ap.add_argument("--out", help="save raw samples JSON (time-perishable evidence)")
    args = ap.parse_args()

    sizes = [float(s) for s in args.sizes.split(",") if s]
    samples: list[dict] = []
    for i in range(args.samples):
        try:
            book = fetch_l2(args.coin)
            snap = snapshot_impact(book, sizes)
            samples.append(snap)
            mid = snap.get("mid")
            print(f"sample {i + 1}/{args.samples}: mid={mid} spread={snap.get('spread_usd'):.4g}")
        except Exception as e:  # noqa: BLE001 -- sampling loop must survive blips
            print(f"sample {i + 1}/{args.samples}: FETCH ERROR {e}")
        if i + 1 < args.samples:
            time.sleep(args.interval)

    spreads = [s["spread_frac"] for s in samples if "spread_frac" in s]
    if spreads:
        spreads.sort()
        print(
            f"\nspread: n={len(spreads)} median {1e4 * spreads[len(spreads) // 2]:.2f} bps"
            f"  max {1e4 * spreads[-1]:.2f} bps"
        )
    print(
        f"{'side':<5} {'size':>6} {'n':>3} {'exh':>4} {'med bps':>8} {'p90 bps':>8} "
        f"{'med tvt':>8} {'p90 tvt':>8}"
    )
    for a in aggregate(samples, args.mintick):
        print(
            f"{a['side']:<5} {a['size']:>6.0f} {a['n']:>3} {a['exhausted_n']:>4} "
            f"{a['med_bps']:>8.2f} {a['p90_bps']:>8.2f} "
            f"{a['med_tvticks']:>8.1f} {a['p90_tvticks']:>8.1f}"
        )

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "coin": args.coin,
                    "sizes": sizes,
                    "interval_s": args.interval,
                    "mintick": args.mintick,
                    "samples": samples,
                },
                f,
            )
        print(f"raw samples -> {args.out}")


if __name__ == "__main__":
    main()
