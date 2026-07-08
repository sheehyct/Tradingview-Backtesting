"""TVB-10 diagnostic D1 (pre-registered): flip-line clustering of losers.

Pre-registration (BINDING): docs/TVB2_control_AB_rerun.md, TVB-10 section,
"Diagnostic D1". For every state-stop entry at the operative cost point
(fee 0.0125%, slip 1 tick) on the committed TVB-9 pulls: distance from the
entry price to the NEAREST ACTIVE {M, W, D} period open, in bp of entry
price. Winner vs loser populations compared WITHIN each cell (absolute
distances are confounded by open-coupling); cells with >= 30 closed trades
only. Prediction: loser median bp < winner median bp in the majority of
qualifying cells.

Zero-cost: re-simulates deterministically from committed pulls; no fetches.

Usage:
    uv run --no-sync python analysis/flipline_distance.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.tfc_breadth_sweep import CONFIGS, UNIVERSE  # noqa: E402
from scripts.tfc_exit_sweep import get_committed_bars  # noqa: E402
from tfc.config import TFCConfig  # noqa: E402
from tfc.periods import period_open_series  # noqa: E402
from tfc.simulator import simulate  # noqa: E402
from tfc.tv_reference import REFERENCE_DIR  # noqa: E402

FEE, SLIP = 0.000125, 1
HTF_SET = ("M", "W", "D")
MIN_TRADES = 30
OUT = REFERENCE_DIR / "tvb10_flipline_distance.json"


def main() -> int:
    s9 = json.loads((REFERENCE_DIR / "tvb9_breadth_results.json").read_text())["symbols"]
    cells_out: list[dict] = []
    for coin, u in UNIVERSE.items():
        if "skipped" in s9[coin]:
            continue
        bars = get_committed_bars(u["slug"])
        opens = [period_open_series(bars.ts, bars.open, tf) for tf in HTF_SET]
        ts_ms = bars.ts * 1000
        idx_of = {int(t): i for i, t in enumerate(ts_ms)}
        for cell, kw in CONFIGS.items():
            cfg = TFCConfig(
                comm_rate=FEE,
                slip_ticks=SLIP,
                mintick=float(s9[coin]["mintick"]),
                qty_step=float(s9[coin]["qty_step"]),
                **kw,
            )
            res = simulate(bars, cfg)
            if len(res.closed) < MIN_TRADES:
                continue
            win_d, loss_d = [], []
            for r in res.closed:
                i = idx_of[r["et"]]
                ds = [abs(r["ep"] - o[i]) / r["ep"] * 1e4 for o in opens if not np.isnan(o[i])]
                if not ds:  # before the first M/W/D boundary: no active open yet
                    continue
                (win_d if r["pv"] > 0 else loss_d).append(min(ds))
            if not win_d or not loss_d:
                continue
            wm, lm = float(np.median(win_d)), float(np.median(loss_d))
            cells_out.append(
                {
                    "symbol": coin,
                    "cell": cell,
                    "trades": len(res.closed),
                    "winners": len(win_d),
                    "losers": len(loss_d),
                    "winner_median_bp": round(wm, 1),
                    "loser_median_bp": round(lm, 1),
                    "losers_closer": lm < wm,
                }
            )
    hits = sum(1 for c in cells_out if c["losers_closer"])
    print(f"D1: losers closer to nearest active M/W/D open in {hits}/{len(cells_out)} cells")
    for c in cells_out:
        mark = "HIT " if c["losers_closer"] else "miss"
        print(
            f"  {mark} {c['symbol']:12s} {c['cell']:9s} n={c['trades']:4d}  "
            f"loser {c['loser_median_bp']:7.1f}bp  winner {c['winner_median_bp']:7.1f}bp"
        )
    doc = {
        "purpose": "TVB-10 D1 flip-line clustering diagnostic (pre-registered)",
        "prereg": "docs/TVB2_control_AB_rerun.md: TVB-10 Diagnostic D1",
        "operative_point": {"fee_rate": FEE, "slip_ticks": SLIP, "exit_mode": "state"},
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hits": hits,
        "cells": len(cells_out),
        "detail": cells_out,
    }
    OUT.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
