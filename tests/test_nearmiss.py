"""Hand vectors for the near-miss study core (STRAT skill section 7 plus the walk)."""

import numpy as np
import pytest

from analysis.nearmiss.core import (
    ONE,
    THREE,
    TWO_DOWN,
    TWO_UP,
    Setup,
    classify,
    find_setups,
    walk,
)


def bars(rows):
    a = np.array(rows, dtype=float)
    return a[:, 0], a[:, 1], a[:, 2], a[:, 3]  # open, high, low, close


@pytest.mark.parametrize(
    "high, low, expect",
    [
        (105.00, 99.00, ONE),  # equal high never breaks
        (104.00, 98.00, ONE),  # equal low never breaks
        (105.00, 98.00, ONE),  # equal both
        (105.01, 98.50, TWO_UP),  # one penny is a break
        (104.00, 97.99, TWO_DOWN),
        (105.01, 97.99, THREE),
        (104.50, 99.10, ONE),
    ],
)
def test_classify_equal_boundaries(high, low, expect):
    assert classify(np.array([105.0, high]), np.array([98.0, low]))[1] == expect


def only(setups, status="triggered"):
    got = [s for s in setups if s.status == status]
    assert len(got) == 1, [(s.family, s.side, s.status) for s in setups]
    return got[0]


def test_212_bull_reversal_levels():
    # ref, 2D, inside, entry: trigger = inside high, target = the 2D's HIGH, stop = the 2D's low
    o, h, l, c = bars(
        [
            [105, 110, 100, 104],
            [103, 108, 95, 97],  # 2D
            [98, 104, 97, 101],  # inside
            [100, 105, 98, 104],  # breaks 104, holds 97
        ]
    )
    s = only(find_setups(o, h, l, c))
    assert (s.family, s.side, s.i) == ("2-1-2 reversal", 1, 3)
    assert (s.trigger, s.target, s.stop, s.other) == (104, 108, 95, 97)
    assert not s.went3


def test_212_bear_reversal_levels():
    o, h, l, c = bars(
        [
            [95, 100, 90, 96],
            [97, 105, 92, 103],  # 2U
            [102, 103, 96, 99],  # inside
            [100, 102, 95, 96],  # breaks 96, holds 103
        ]
    )
    s = only(find_setups(o, h, l, c))
    assert (s.family, s.side) == ("2-1-2 reversal", -1)
    assert (s.trigger, s.target, s.stop, s.other) == (96, 92, 105, 103)


def test_22_bull_reversal_levels():
    # 2D, 2D, entry: trigger = the setup 2D's high, target = the high of the bar before it
    o, h, l, c = bars(
        [
            [108, 112, 104, 106],
            [106, 110, 100, 102],  # 2D (the reference 2)
            [102, 107, 96, 98],  # 2D setup
            [99, 108, 97, 107],  # breaks 107, holds 96
        ]
    )
    s = only(find_setups(o, h, l, c))
    assert (s.family, s.side) == ("2-2 reversal", 1)
    assert (s.trigger, s.target, s.stop, s.other) == (107, 110, 96, 96)


def test_router_inside_or_outside_reference_is_not_a_22_reversal():
    # [1, 2D, 2U] is rev strat context; [3, 2D, 2U] is a 3-2-2: both held out of this study
    inside_ref = bars(
        [[105, 110, 100, 104], [104, 109, 101, 103], [103, 108, 99, 100], [100, 109, 100, 108]]
    )
    outside_ref = bars(
        [[105, 108, 102, 104], [104, 110, 100, 103], [103, 109, 98, 100], [100, 110, 99, 108]]
    )
    for o, h, l, c in (inside_ref, outside_ref):
        assert not [s for s in find_setups(o, h, l, c) if s.side == 1]


def test_312_family_follows_the_colour_of_the_3():
    rows = [
        [105, 108, 102, 104],
        [104, 110, 100, 101],  # 3, closed red
        [102, 106, 101, 103],  # inside
        [103, 107, 102, 106],  # breaks 106
    ]
    s = only(find_setups(*bars(rows)))
    assert s.family == "3-1-2 reversal"  # long after a red 3
    assert (s.trigger, s.target, s.stop, s.other) == (106, 110, 100, 101)
    rows[1] = [101, 110, 100, 109]  # the 3 closed green
    assert only(find_setups(*bars(rows))).family == "3-1-2 continuation"


def test_gap_past_the_trigger_is_a_missed_entry():
    o, h, l, c = bars(
        [[105, 110, 100, 104], [103, 108, 95, 97], [98, 104, 97, 101], [104.5, 106, 104.2, 105]]
    )
    longs = [s for s in find_setups(o, h, l, c) if s.side == 1]
    assert [s.status for s in longs] == ["gap past trigger"]


def test_equal_to_the_trigger_is_not_a_break():
    o, h, l, c = bars(
        [[105, 110, 100, 104], [103, 108, 95, 97], [98, 104, 97, 101], [100, 104, 98, 103]]
    )
    longs = [s for s in find_setups(o, h, l, c) if s.side == 1]
    assert [s.status for s in longs] == ["not triggered"]


def test_entry_bar_taking_the_other_side_went_3():
    o, h, l, c = bars(
        [[105, 110, 100, 104], [103, 108, 95, 97], [98, 104, 97, 101], [100, 105, 96.5, 97]]
    )
    s = [x for x in find_setups(o, h, l, c) if x.side == 1][0]
    assert s.status == "triggered" and s.went3


def test_no_room_when_trigger_equals_target():
    o, h, l, c = bars(
        [[105, 110, 100, 104], [103, 108, 95, 97], [98, 108, 97, 101], [100, 109, 98, 108]]
    )
    longs = [s for s in find_setups(o, h, l, c) if s.side == 1]
    assert [s.status for s in longs] == ["no room"]


def test_zero_range_setup_bar_is_dropped():
    # the setup 2D has high == low: trigger and stop are the same price
    o, h, l, c = bars(
        [[108, 112, 104, 106], [106, 110, 100, 102], [99, 99, 99, 99], [99, 108, 99, 107]]
    )
    longs = [s for s in find_setups(o, h, l, c) if s.side == 1]
    assert [s.status for s in longs] == ["flat setup bar"]


LONG = Setup("2-1-2 reversal", 1, 1, 100.0, 110.0, 90.0, 95.0, "triggered", False)


def run(rows, k=1.0, st=LONG):
    o, h, l, _ = bars(rows)
    return walk(o, h, l, st, k)


def test_walk_won_on_the_entry_bar_touch_counts():
    w = run([[0, 0, 0, 0], [98, 110, 97, 109]])
    assert (w.outcome, w.j, w.fill) == ("won", 1, 110.0)


def test_walk_failed_reports_progress_both_ways():
    # entry bar reaches 106 (60% of the way); next bar makes 109 and breaks the stop
    w = run([[0, 0, 0, 0], [98, 106, 97, 105], [105, 109, 89, 90]])
    assert (w.outcome, w.j, w.fill) == ("failed", 2, 90.0)
    assert w.p_lo == pytest.approx(0.6) and w.p_hi == pytest.approx(0.9)


def test_walk_stop_needs_a_strict_break():
    w = run([[0, 0, 0, 0], [98, 106, 97, 105], [105, 107, 90, 91], [91, 111, 91, 110]])
    assert (w.outcome, w.j) == ("won", 3)


def test_walk_one_bar_touching_both_is_reported_as_both():
    w = run([[0, 0, 0, 0], [98, 106, 97, 105], [105, 110, 89, 95]])
    assert w.outcome == "both" and w.p_lo == pytest.approx(0.6)


def test_walk_gap_through_the_stop_fills_at_the_open():
    w = run([[0, 0, 0, 0], [98, 106, 97, 105], [88, 89, 85, 86]])
    assert (w.outcome, w.fill) == ("failed", 88.0)
    assert w.p_hi == pytest.approx(0.6)


def test_walk_open_at_the_end_of_data():
    w = run([[0, 0, 0, 0], [98, 106, 97, 105], [105, 108, 100, 107]])
    assert w.outcome == "open" and w.p_lo == pytest.approx(0.8)


def test_walk_exit_short_of_the_target_rescues_a_near_miss():
    rows = [[0, 0, 0, 0], [98, 106, 97, 105], [105, 109.5, 100, 101], [101, 102, 89, 90]]
    assert run(rows).outcome == "failed"
    near = run(rows, k=0.95)
    assert (near.outcome, near.j, near.fill) == ("won", 2, 109.5)


def test_walk_short_side_mirrors():
    st = Setup("2-1-2 reversal", -1, 1, 100.0, 90.0, 110.0, 105.0, "triggered", False)
    w = run([[0, 0, 0, 0], [102, 103, 94, 95], [95, 111, 91, 110]], st=st)
    assert (w.outcome, w.fill) == ("failed", 110.0)
    assert w.p_lo == pytest.approx(0.6) and w.p_hi == pytest.approx(0.9)
