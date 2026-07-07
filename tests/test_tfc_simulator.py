"""Phase-2 micro-behavior tests on synthetic bars (mechanics documentation).

The 8-cell equivalence gate is the load-bearing test; these pin the
individual mechanisms so a future refactor that breaks one fails with a
readable name instead of a 4,000-trade prefix divergence.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tfc.config import TFCConfig  # noqa: E402
from tfc.simulator import simulate  # noqa: E402
from tfc.tv_reference import Bars  # noqa: E402

# single exec TF == chart TF: gate is simply close vs the CURRENT bar's own
# open (seeds at bar 1), which makes scenarios easy to author
CFG = TFCConfig(chart_tf="15", exec_tfs=("15",), comm_rate=0.0)


def mk(rows):
    a = np.array(rows, dtype=np.float64)
    n = len(a)
    ts = (np.arange(n, dtype=np.int64) * 900) + 900_000
    return Bars(
        symbol="TEST",
        interval="15",
        ts=ts,
        open=a[:, 0],
        high=a[:, 1],
        low=a[:, 2],
        close=a[:, 3],
        volume=np.ones(n),
    )


def test_long_roundtrip_intrabar_fill_and_state_stop():
    bars = mk(
        [
            (100.0, 101.0, 99.0, 100.5),  # bar0: no period open yet -> grey
            (100.5, 101.0, 100.0, 100.8),  # bar1: up -> arm stop 101.001
            (100.9, 101.5, 100.5, 101.4),  # bar2: fills 101.002 (slip 1t); still up
            (101.3, 101.6, 101.0, 101.2),  # bar3: close < open -> grey -> exit queued
            (101.0, 101.2, 100.8, 101.1),  # bar4: exit fills at 100.999
        ]
    )
    r = simulate(bars, CFG)
    assert len(r.closed) == 1 and r.open_trade is None
    t = r.closed[0]
    assert t["dir"] == "le"
    assert t["et"] == int(bars.ts[2]) * 1000 and t["xt"] == int(bars.ts[4]) * 1000
    assert abs(t["ep"] - 101.002) < 1e-9  # stop + 1 tick slip
    assert abs(t["xp"] - 100.999) < 1e-9  # next open - 1 tick slip
    assert abs(t["q"] - np.floor(10000 / 101.002 / 0.001) * 0.001) < 1e-9


def test_gap_through_fills_at_open_but_qty_basis_stays_stop():
    bars = mk(
        [
            (100.0, 101.0, 99.0, 100.5),
            (100.5, 101.0, 100.0, 100.8),  # arm stop 101.001
            (102.0, 102.5, 101.8, 102.2),  # opens through: fill 102.001, basis 101.002
            (102.0, 102.1, 101.5, 101.8),  # close < open -> exit queued
            (101.5, 101.6, 101.0, 101.2),
        ]
    )
    r = simulate(bars, CFG)
    t = r.closed[0]
    assert abs(t["ep"] - 102.001) < 1e-9  # open + slip
    assert abs(t["q"] - np.floor(10000 / 101.002 / 0.001) * 0.001) < 1e-9  # slipped-stop basis


def test_stop_lives_one_bar_and_rearms_at_new_level():
    bars = mk(
        [
            (100.0, 101.0, 99.0, 100.5),
            (100.5, 101.0, 100.0, 100.8),  # arm 101.001
            (100.6, 100.9, 100.4, 100.7),  # no fill (high 100.9 < 101.001); re-arm 100.901
            (100.7, 100.95, 100.5, 100.9),  # fills at 100.902 -- the NEW level, not the old
            (100.7, 100.8, 100.4, 100.5),  # grey -> exit
            (100.4, 100.5, 100.2, 100.3),
        ]
    )
    r = simulate(bars, CFG)
    assert len(r.closed) == 1
    assert abs(r.closed[0]["ep"] - 100.902) < 1e-9
    assert r.closed[0]["et"] == int(bars.ts[3]) * 1000


def test_equality_is_grey_no_entry():
    bars = mk(
        [
            (100.0, 101.0, 99.0, 100.5),
            (100.5, 101.0, 100.0, 100.5),  # close == own open -> grey, nothing arms
            (100.5, 105.0, 100.0, 104.0),  # would have filled if armed
            (104.0, 104.0, 100.0, 100.1),
        ]
    )
    r = simulate(bars, CFG)
    assert len(r.closed) == 0 and r.open_trade is None


def test_governor_ratchet_blocks_until_higher_trigger_then_resets_on_opposite():
    gov = TFCConfig(chart_tf="15", exec_tfs=("15",), comm_rate=0.0, gov_mode="ratchet")
    bars = mk(
        [
            (100.0, 101.0, 99.0, 100.5),
            (100.5, 101.0, 100.0, 100.8),  # arm 101.001
            (100.9, 101.5, 100.5, 101.4),  # fill long 101.002 (trigger 101.001)
            (101.3, 101.6, 101.0, 101.2),  # grey -> exit queued
            (
                100.8,
                101.0,
                100.6,
                100.9,
            ),  # exit 100.799 -> LOSS -> ratchet=101.001; up (100.9>100.8) but
            #   candidate 101.0+.001 == ratchet -> NOT strictly beyond -> no arm
            (
                100.9,
                101.0,
                100.7,
                100.95,
            ),  # up; high 101.0 -> candidate 101.001 == ratchet -> still blocked
            (100.9, 101.8, 100.8, 101.5),  # up; high 101.8 -> candidate 101.801 > ratchet -> arm
            (101.5, 102.0, 101.4, 101.9),  # fills at 101.802
            (101.9, 102.0, 101.0, 101.5),  # close < open -> exit
            (101.4, 101.5, 101.0, 101.2),
        ]
    )
    r = simulate(bars, gov)
    assert len(r.closed) == 2
    assert r.closed[1]["et"] == int(bars.ts[7]) * 1000
    assert abs(r.closed[1]["ep"] - 101.802) < 1e-9
    # control: with the governor off, the re-entry happens two bars earlier
    r_off = simulate(bars, CFG)
    assert len(r_off.closed) >= 2
    assert r_off.closed[1]["et"] < r.closed[1]["et"]


def test_governor_winning_exit_does_not_ratchet():
    gov = TFCConfig(chart_tf="15", exec_tfs=("15",), comm_rate=0.0, gov_mode="ratchet")
    bars = mk(
        [
            (100.0, 101.0, 99.0, 100.5),
            (100.5, 101.0, 100.0, 100.8),  # arm 101.001
            (100.9, 101.5, 100.5, 101.4),  # fill long 101.002
            (101.4, 103.0, 101.3, 102.8),  # up, hold
            (102.8, 103.0, 102.0, 102.2),  # grey -> exit queued
            (102.5, 102.6, 102.0, 102.55),  # exit 102.499 -> WIN -> no ratchet; up -> arm 102.601
            (102.6, 102.7, 102.4, 102.65),  # fills 102.602 immediately (no governor block)
            (102.6, 102.7, 102.0, 102.1),  # exit
            (102.0, 102.1, 101.8, 101.9),
        ]
    )
    r = simulate(bars, gov)
    assert len(r.closed) == 2
    assert r.closed[1]["et"] == int(bars.ts[6]) * 1000
