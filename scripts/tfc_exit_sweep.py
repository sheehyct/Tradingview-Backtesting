"""TVB-10: pre-registered exit-symmetry ablation (state-stop vs flip-stop).

Pre-registration (BINDING): docs/TVB2_control_AB_rerun.md section "TVB-10:
exit-symmetry ablation -- PRE-REGISTRATION (APPROVED by user 2026-07-08)".
One variable: TFCConfig.exit_mode 'state' (baseline, first loss of full
exec alignment) vs 'flip' (only full OPPOSITE alignment exits; holds
through grey). Everything else -- universe, committed pulls, cells, costs,
conventions -- is the TVB-9 breadth grid verbatim.

Method locks enforced here:
- Committed pulls ONLY (`tvb9_hl_{slug}_1h.json`); a missing file is a hard
  error, never a fresh fetch (the HL cap slides daily).
- mintick / qty_step read from the committed tvb9_breadth_results.json
  symbols block (identical conventions by construction, fully offline).
- REGRESSION: every exit_mode='state' row must reproduce the committed
  TVB-9 row (net_pct, trades, pf, win_pct, maxdd) EXACTLY or the runner
  exits 2 without writing an artifact.
- C1 (governor inertness under flip) reported per symbol/fee/slip.
- C2 (one-per-regime, amended form): between consecutive same-direction
  flip entries there must exist an opposite-full-alignment close.
- Dual accounting (binding): closed-only net_pct (TVB-9 convention) AND
  mtm_net_pct (open trade marked at last close, exit-side slip+commission).

Usage:
    uv run --no-sync python scripts/tfc_exit_sweep.py [--symbols xyz:MU ...]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis.tfc_hl_pilot import iso, run_metrics  # noqa: E402
from scripts.tfc_breadth_sweep import CONFIGS, FEES, SLIPS, UNIVERSE  # noqa: E402
from tfc.config import TFCConfig  # noqa: E402
from tfc.simulator import compute_gates, simulate  # noqa: E402
from tfc.tv_reference import REFERENCE_DIR, load_bars  # noqa: E402

TVB9_RESULTS = REFERENCE_DIR / "tvb9_breadth_results.json"
RESULTS_FILE = "tvb10_exit_results.json"
EXIT_MODES = ("state", "flip")
REGRESSION_KEYS = ("net_pct", "trades", "pf", "win_pct", "maxdd_closed_pct")


def get_committed_bars(slug: str):
    path = REFERENCE_DIR / f"tvb9_hl_{slug}_1h.json"
    if not path.exists():
        raise SystemExit(f"FATAL: committed pull missing: {path} (pre-reg forbids fresh fetches)")
    bars = load_bars(path)
    # replicate the TVB-9 runner exactly: drop the (then-live) last bar
    return type(bars)(
        symbol=bars.symbol,
        interval=bars.interval,
        ts=bars.ts[:-1],
        open=bars.open[:-1],
        high=bars.high[:-1],
        low=bars.low[:-1],
        close=bars.close[:-1],
        volume=bars.volume[:-1],
    )


def mtm_net_pct(res, bars, cfg: TFCConfig) -> float:
    """Closed-chain equity plus the open trade marked at the last close.

    Exit-side slippage (adverse) and commission applied to the mark, mirroring
    the simulator's next-open exit fill economics.
    """
    eq = res.final_equity
    if res.open_trade is not None:
        ot = res.open_trade
        sign = 1.0 if ot["dir"] == "le" else -1.0
        xp = float(bars.close[-1]) - sign * cfg.slip
        gross = ot["q"] * sign * (xp - ot["ep"])
        eq += gross - cfg.comm_rate * ot["q"] * (ot["ep"] + xp)
    return round(100.0 * (eq - cfg.initial_capital) / cfg.initial_capital, 4)


def c2_violations(res, bars, cfg: TFCConfig) -> int:
    """Amended C2: consecutive same-direction flip entries require an
    intervening opposite-full-alignment close."""
    up, dn, _, _ = compute_gates(bars, cfg)
    ts_ms = bars.ts * 1000
    idx_of = {int(t): i for i, t in enumerate(ts_ms)}
    entries = [(idx_of[r["et"]], r["dir"]) for r in res.closed]
    if res.open_trade is not None:
        entries.append((idx_of[res.open_trade["et"]], res.open_trade["dir"]))
    entries.sort()
    bad = 0
    for (i0, d0), (i1, d1) in zip(entries, entries[1:]):
        if d0 == d1:
            opp = dn if d0 == "le" else up
            if not opp[i0:i1].any():
                bad += 1
    return bad


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--symbols", nargs="*", default=list(UNIVERSE))
    ap.add_argument("--out", default=str(REFERENCE_DIR / RESULTS_FILE))
    args = ap.parse_args(argv)

    tvb9 = json.loads(TVB9_RESULTS.read_text())
    tvb9_rows = {(r["symbol"], r["cell"], r["fee_rate"], r["slip_ticks"]): r for r in tvb9["runs"]}

    symbols_out: dict[str, dict] = {}
    runs: list[dict] = []
    regression_fails: list[str] = []
    c2_total = 0

    for coin in args.symbols:
        s9 = tvb9["symbols"][coin]
        if "skipped" in s9:
            symbols_out[coin] = {"skipped": s9["skipped"]}
            continue
        mintick, qty_step = float(s9["mintick"]), float(s9["qty_step"])
        bars = get_committed_bars(UNIVERSE[coin]["slug"])
        if len(bars) != s9["bars"]:
            raise SystemExit(f"FATAL: {coin} bar count {len(bars)} != committed TVB-9 {s9['bars']}")
        symbols_out[coin] = {
            "mintick": mintick,
            "qty_step": qty_step,
            "window": s9["window"],
            "bars": len(bars),
            "descriptors": s9["descriptors"],
            "provenance": "committed tvb9 pull + tvb9 symbols block (offline)",
        }
        print(f"{coin}: {len(bars)} bars {iso(int(bars.ts[0]))} .. {iso(int(bars.ts[-1]))}")
        for cell, kw in CONFIGS.items():
            for fee in FEES:
                for s in SLIPS:
                    for mode in EXIT_MODES:
                        cfg = TFCConfig(
                            comm_rate=fee,
                            slip_ticks=s,
                            mintick=mintick,
                            qty_step=qty_step,
                            exit_mode=mode,
                            **kw,
                        )
                        res = simulate(bars, cfg)
                        m = run_metrics(res)
                        row = {
                            "symbol": coin,
                            "cell": cell,
                            "fee_rate": fee,
                            "slip_ticks": s,
                            "exit_mode": mode,
                            **m,
                            "mtm_net_pct": mtm_net_pct(res, bars, cfg),
                        }
                        if mode == "state":
                            ref = tvb9_rows[(coin, cell, fee, s)]
                            for k in REGRESSION_KEYS:
                                if row.get(k if k != "maxdd_closed_pct" else k) != ref.get(k):
                                    regression_fails.append(
                                        f"{coin}/{cell}/{fee}/s{s} {k}: "
                                        f"{row.get(k)} != committed {ref.get(k)}"
                                    )
                        else:
                            bad = c2_violations(res, bars, cfg)
                            row["c2_violations"] = bad
                            c2_total += bad
                        runs.append(row)
        # per-symbol console read @ the operative cost point
        for cell in CONFIGS:
            st = next(
                r
                for r in runs
                if r["symbol"] == coin
                and r["cell"] == cell
                and r["fee_rate"] > 0
                and r["slip_ticks"] == 1
                and r["exit_mode"] == "state"
            )
            fl = next(
                r
                for r in runs
                if r["symbol"] == coin
                and r["cell"] == cell
                and r["fee_rate"] > 0
                and r["slip_ticks"] == 1
                and r["exit_mode"] == "flip"
            )
            print(
                f"   {cell:9s} @0.0125 s1: state {st['net_pct']:+8.2f}% ({st['trades']:4d})"
                f"  flip {fl['net_pct']:+8.2f}% ({fl['trades']:3d})"
                f"  mtm {fl['mtm_net_pct']:+8.2f}%  c2v {fl['c2_violations']}"
            )

    if regression_fails:
        print("STATE-ARM REGRESSION FAILURES (artifact NOT written):")
        for f in regression_fails:
            print("  " + f)
        return 2

    # C1: governor deltas under flip (expected ~0)
    c1 = []
    for coin in args.symbols:
        if "skipped" in symbols_out.get(coin, {}):
            continue
        for fee in FEES:
            for s in SLIPS:
                base = next(
                    r
                    for r in runs
                    if r["symbol"] == coin
                    and r["cell"] == "R1E3"
                    and r["fee_rate"] == fee
                    and r["slip_ticks"] == s
                    and r["exit_mode"] == "flip"
                )
                gov = next(
                    r
                    for r in runs
                    if r["symbol"] == coin
                    and r["cell"] == "R1E3gov2"
                    and r["fee_rate"] == fee
                    and r["slip_ticks"] == s
                    and r["exit_mode"] == "flip"
                )
                c1.append(
                    {
                        "symbol": coin,
                        "fee_rate": fee,
                        "slip_ticks": s,
                        "delta_net_pp": round(gov["net_pct"] - base["net_pct"], 4),
                        "delta_trades": gov["trades"] - base["trades"],
                    }
                )
    worst_c1 = max(c1, key=lambda x: abs(x["delta_net_pp"])) if c1 else None

    # Expectation-1 cadence summary (flip trades as a fraction of state trades)
    ratios = []
    for r in runs:
        if r["exit_mode"] != "flip":
            continue
        st = next(
            x
            for x in runs
            if x["exit_mode"] == "state"
            and (x["symbol"], x["cell"], x["fee_rate"], x["slip_ticks"])
            == (r["symbol"], r["cell"], r["fee_rate"], r["slip_ticks"])
        )
        if st["trades"] > 0:
            ratios.append(r["trades"] / st["trades"])
    ratios = np.array(ratios)
    cadence = {
        "cells_with_ratio": int(len(ratios)),
        "median_ratio": round(float(np.median(ratios)), 4),
        "pct_cells_le_40pct": round(100.0 * float((ratios <= 0.40).mean()), 1),
    }

    doc = {
        "purpose": "TVB-10 pre-registered exit-symmetry ablation (state vs flip)",
        "prereg": "docs/TVB2_control_AB_rerun.md: TVB-10 exit-symmetry pre-registration",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "symbols": symbols_out,
        "runs": runs,
        "checks": {
            "state_regression": "PASS (all rows reproduce committed TVB-9)",
            "c1_governor_flip": c1,
            "c1_worst": worst_c1,
            "c2_total_violations": c2_total,
            "cadence_expectation1": cadence,
        },
    }
    Path(args.out).write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(
        f"\nwrote {args.out} ({len(runs)} runs) | state regression PASS | "
        f"c2 violations {c2_total} | c1 worst {worst_c1} | cadence {cadence}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
