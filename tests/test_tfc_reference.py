"""Phase-0 tests: reference loaders, gate-cell registry, and f_guard port."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tfc.config import GuardError, TFCConfig  # noqa: E402
from tfc.tv_reference import REFERENCE_CELLS, load_cell  # noqa: E402


def test_registry_has_eight_cells_four_hard():
    assert len(REFERENCE_CELLS) == 8
    assert sum(c.hard for c in REFERENCE_CELLS.values()) == 4


@pytest.mark.parametrize("name", list(REFERENCE_CELLS))
def test_cell_loads_and_self_asserts(name):
    cell, bars, dump = load_cell(name)
    assert dump.trades == len(dump.closed_rows)
    assert dump.open_trades == len(dump.rows) - dump.trades
    # PREFIX rule (plan, equivalence.py): dumps captured later in the session
    # than the bar files carry live tail-drift trades past the last committed
    # bar. Only rows with xt <= last bar time are comparable -- those must
    # resolve to bars exactly; everything after the first out-of-window row
    # must also be out of window (contiguous prefix).
    idx = bars.index_of_ms()
    last_ms = int(bars.ts[-1]) * 1000
    in_prefix = True
    prefix_n = 0
    for r in dump.closed_rows:
        if in_prefix and r["xt"] > last_ms:
            in_prefix = False
        if in_prefix:
            assert r["et"] in idx and r["xt"] in idx
            assert idx[r["et"]] >= 1  # trigger needs a prior bar
            prefix_n += 1
        else:
            assert r["xt"] > last_ms, "non-contiguous prefix: in-window row after tail"
    assert prefix_n > 0.99 * dump.trades  # tail drift is a handful of trades at most


def test_ctrlb_anchor_trade_count():
    _, _, dump = load_cell("ctrlB_0125_s1")
    assert dump.trades == 4308  # TVB-6 regression anchor


def test_guard_rejects_finer_gate_tf():
    with pytest.raises(GuardError, match="finer than the chart TF"):
        TFCConfig(chart_tf="60", exec_tfs=("15",))


def test_guard_rejects_non_tiling_intraday():
    with pytest.raises(GuardError, match="integer multiple"):
        TFCConfig(chart_tf="25", exec_tfs=("60",))


def test_guard_rejects_chart_not_dividing_day():
    with pytest.raises(GuardError, match="does not divide 1D"):
        TFCConfig(chart_tf="7", exec_tfs=("D",))


def test_guard_rejects_unported_modes():
    with pytest.raises(GuardError, match="size_down|not ported"):
        TFCConfig(chart_tf="15", exec_tfs=("60",), reg_mode="size_down")
    with pytest.raises(GuardError, match="reg_exit"):
        TFCConfig(chart_tf="15", exec_tfs=("60",), reg_exit=True)


def test_guard_accepts_gate_cell_shapes():
    TFCConfig(chart_tf="15", exec_tfs=("60", "30", "15"), reg_mode="stand_aside")
    TFCConfig(chart_tf="60", exec_tfs=("M", "W", "D", "60"))
