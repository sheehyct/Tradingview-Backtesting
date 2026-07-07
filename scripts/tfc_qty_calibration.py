"""Phase-0 calibration: verify the TV qty rule + fill/PnL conventions dump-driven.

For every gate cell (no simulator involved) this re-derives, trade by trade:
  trigger   = prev-bar high + mintick (long) / low - mintick (short)
  basis     = trigger +/- slip (the EXPECTED slipped stop fill; qty basis stays
              the slipped stop even when the bar gaps through -- calibrated fact)
  qty       = floor(equity / (basis * (1 + comm_rate)) / step) * step
  entry ep  = basis normally, open +/- slip on gap-through bars
  exit  xp  = exit-bar open -/+ slip (market close(), adverse slippage)
  pv        = q * sign * (xp - ep) - comm_rate * q * (ep + xp)
  pp        = pv / (q * ep * (1 + comm_rate))   [TVB-8 CORRECTION: return on
              entry COST BASIS incl. entry commission, NOT return on equity --
              indistinguishable at 100% sizing except on gap-through fills]
with equity chained 10000 + cumsum(serialized pv) for the qty rule. Exit
code 2 if any cell exceeds the documented tolerances (plan risks 1-2).

Usage: uv run python scripts/tfc_qty_calibration.py [cell ...]
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tfc.tv_reference import REFERENCE_CELLS, load_cell  # noqa: E402

# Documented tolerances (VBT_BREADTH_PORT_PLAN.md risks 1-2, TVB-7 planning)
MAX_Q_BOUNDARY_PER_CELL = 3  # one-step floor-boundary cases from serialized-pv chaining
PV_ABS_TOL = 1e-4  # worst reconstruction error seen in planning: 4.9e-5
PP_ABS_TOL = 2e-8  # corrected pp formula reproduces dumps to <= 8.3e-9 (TVB-8)


def calibrate_cell(name: str) -> dict:
    cell, bars, dump = load_cell(name)
    cfg = cell.cfg
    idx = bars.index_of_ms()
    slip = cfg.slip
    step = cfg.qty_step

    eq = cfg.initial_capital
    stats = {
        "cell": name,
        "closed": 0,
        "q_exact": 0,
        "q_boundary": 0,
        "q_bad": 0,
        "gap_entries": 0,
        "ep_bad": 0,
        "xp_bad": 0,
        "tail_skipped": 0,
        "pv_max_err": 0.0,
        "pp_max_err": 0.0,
        "first_bad": None,
    }

    last_ms = int(bars.ts[-1]) * 1000
    for k, r in enumerate(dump.closed_rows):
        if r["xt"] > last_ms:
            # live tail drift past the committed bars (contiguous prefix rule,
            # asserted by the loader test) -- not calibratable on this bar file
            stats["tail_skipped"] += 1
            continue
        i = idx[r["et"]]
        j = idx[r["xt"]]
        long = r["dir"] == "le"
        sign = 1.0 if long else -1.0
        trigger = bars.high[i - 1] + cfg.mintick if long else bars.low[i - 1] - cfg.mintick
        basis = trigger + slip if long else trigger - slip

        # fill conventions
        gap = bars.open[i] > trigger if long else bars.open[i] < trigger
        ep_expect = (bars.open[i] + slip if long else bars.open[i] - slip) if gap else basis
        xp_expect = bars.open[j] - slip if long else bars.open[j] + slip
        if gap:
            stats["gap_entries"] += 1
        if abs(ep_expect - r["ep"]) > 1e-9:
            stats["ep_bad"] += 1
            stats["first_bad"] = stats["first_bad"] or ("ep", k, r["et"], ep_expect, r["ep"])
        if abs(xp_expect - r["xp"]) > 1e-9:
            stats["xp_bad"] += 1
            stats["first_bad"] = stats["first_bad"] or ("xp", k, r["xt"], xp_expect, r["xp"])

        # qty rule (strict floor, then epsilon-floor boundary classification)
        ratio = eq / (basis * (1.0 + cfg.comm_rate)) / step
        q_strict = math.floor(ratio) * step
        q_row = round(r["q"] / step)
        if round(q_strict / step) == q_row:
            stats["q_exact"] += 1
        elif (
            abs(round(q_strict / step) - q_row) <= 1
            or round(math.floor(ratio + 1e-9) * step / step) == q_row
        ):
            stats["q_boundary"] += 1
        else:
            stats["q_bad"] += 1
            stats["first_bad"] = stats["first_bad"] or ("q", k, r["et"], q_strict, r["q"])

        # pv / pp reconstruction from the row's own fields
        q = r["q"]
        pv_expect = q * sign * (r["xp"] - r["ep"]) - cfg.comm_rate * q * (r["ep"] + r["xp"])
        stats["pv_max_err"] = max(stats["pv_max_err"], abs(pv_expect - r["pv"]))
        pp_expect = r["pv"] / (q * r["ep"] * (1.0 + cfg.comm_rate))
        stats["pp_max_err"] = max(stats["pp_max_err"], abs(pp_expect - r["pp"]))

        eq += r["pv"]  # serialized-pv chaining
        stats["closed"] += 1

    return stats


def main(argv: list[str]) -> int:
    names = argv or list(REFERENCE_CELLS)
    failed = False
    hdr = (
        f"{'cell':<20} {'closed':>6} {'q_exact':>8} {'q_bnd':>6} {'q_bad':>6} "
        f"{'gaps':>5} {'ep_bad':>6} {'xp_bad':>6} {'tail':>5} {'pv_err':>10} {'pp_err':>10}"
    )
    print(hdr)
    print("-" * len(hdr))
    for name in names:
        s = calibrate_cell(name)
        print(
            f"{s['cell']:<20} {s['closed']:>6} {s['q_exact']:>8} {s['q_boundary']:>6} "
            f"{s['q_bad']:>6} {s['gap_entries']:>5} {s['ep_bad']:>6} {s['xp_bad']:>6} "
            f"{s['tail_skipped']:>5} {s['pv_max_err']:>10.2e} {s['pp_max_err']:>10.2e}"
        )
        bad = (
            s["q_bad"] > 0
            or s["q_boundary"] > MAX_Q_BOUNDARY_PER_CELL
            or s["ep_bad"] > 0
            or s["xp_bad"] > 0
            or s["pv_max_err"] > PV_ABS_TOL
            or s["pp_max_err"] > PP_ABS_TOL
        )
        if bad:
            failed = True
            print(f"  FAIL: outside documented tolerances; first_bad={s['first_bad']}")
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
