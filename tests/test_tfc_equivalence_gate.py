"""Phase-3 THE GATE: the simulator must reproduce every reference cell
trade-for-trade (VBT_BREADTH_PORT_PLAN.md). POLICY: no Python breadth number
enters the record unless this file is green.

First green: TVB-8 (2026-07-07), all 8 cells, 20,429 closed trades, fills to
2.8e-14, plus the two open-position boundary matches (R1E3, ctrlA).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tfc.equivalence import compare_cell  # noqa: E402
from tfc.tv_reference import REFERENCE_CELLS  # noqa: E402

_ORDERED = sorted(REFERENCE_CELLS, key=lambda n: not REFERENCE_CELLS[n].hard)


@pytest.mark.parametrize("name", _ORDERED)
def test_cell_trade_for_trade(name):
    rep = compare_cell(name)
    assert rep.passed, rep.summary()
    assert rep.sim_trades == rep.prefix_trades


def test_headline_net_matches_on_tail_free_cells():
    # where the dump has no tail drift, the compounded net must match too
    for name in ("ctrlB_0125_s1", "R1E1_0125_s1"):
        cell = REFERENCE_CELLS[name]
        from tfc.simulator import simulate
        from tfc.tv_reference import load_cell

        _, bars, dump = load_cell(name)
        sim = simulate(bars, cell.cfg)
        assert abs(sim.net - dump.net) < 1e-6, (name, sim.net, dump.net)
