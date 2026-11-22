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


# ----------------------------------------------------------------------------- higher timeframes

import pandas as pd  # noqa: E402

from analysis.nearmiss.htf import Cand, aggregate, candidates, enter, walk_sub  # noqa: E402


def test_aggregate_weeks_first_open_last_close_and_extremes():
    dates = pd.bdate_range("2024-01-01", periods=10)  # two full ISO weeks
    o = np.arange(10, 20, dtype=float)
    h, l, c = o + 2, o - 2, o + 1
    big_o, big_h, big_l, big_c, first, last = aggregate(dates, o, h, l, c, "W")
    assert list(first) == [0, 5] and list(last) == [4, 9]
    assert list(big_o) == [10, 15] and list(big_c) == [15, 20]
    assert list(big_h) == [16, 21] and list(big_l) == [8, 13]


def test_322_bull_levels_stop_is_the_3s_extreme():
    # owner's ruling 2026-11-21: stop = the 3 bar's extreme, though the 2D traded through it
    o, h, l, c = bars(
        [[105, 108, 102, 104], [104, 110, 100, 103], [103, 109, 98, 100], [100, 109.5, 99, 109]]
    )
    cd = [x for x in candidates(o, h, l, c) if x.side == 1]
    assert len(cd) == 1
    assert (cd[0].family, cd[0].trigger, cd[0].target, cd[0].stop, cd[0].other) == (
        "3-2-2 reversal",
        109,
        110,
        100,
        98,
    )


def test_one_day_per_bar_reproduces_the_daily_study():
    rng = np.random.default_rng(7)
    n = 3000
    c = np.round(100 + np.cumsum(rng.normal(0, 1, n)), 1)
    o = np.round(np.r_[100, c[:-1]] + rng.normal(0, 0.3, n), 1)
    h = np.round(np.maximum(o, c) + np.abs(rng.normal(0, 0.6, n)), 1)
    l = np.round(np.minimum(o, c) - np.abs(rng.normal(0, 0.6, n)), 1)
    daily = {(s.i, s.family, s.side): s for s in find_setups(o, h, l, c)}
    seen = 0
    for cd in candidates(o, h, l, c):
        if cd.family == "3-2-2 reversal":
            continue
        s = daily[(cd.i, cd.family, cd.side)]
        status, e, entry = enter(cd, o, h, l, c, cd.i, cd.i)
        if s.status == "triggered" and s.went3:
            assert status == "same day both"
        elif s.status == "flat setup bar":
            assert status == "stop beyond trigger"
        elif s.status == "not triggered":  # the daily study does not split this status
            assert status in ("not triggered", "other side first")
        else:
            assert status == s.status
        if status != "triggered":
            continue
        seen += 1
        assert (e, entry) == (cd.i, cd.trigger)
        for k in (1.0, 0.9):
            a, b = walk(o, h, l, s, k), walk_sub(o, h, l, c, cd, e, entry, cd.i, k)
            assert (a.outcome, a.j) == (b.outcome, b.j)
            assert a.p_lo == pytest.approx(b.p_lo) and a.p_hi == pytest.approx(b.p_hi)
            if a.outcome != "open":
                assert a.fill == pytest.approx(b.fill)
    assert seen > 300


# a weekly 2-1-2 long: trigger 104, target 108, stop 95, the inside week's low (other) 97
WEEK = Cand("2-1-2 reversal", 1, 0, 104.0, 108.0, 95.0, 97.0)


def days(rows):
    return bars(rows)


def test_enter_first_day_through_the_trigger():
    o, h, l, c = days([[100, 103, 99, 102], [102, 105, 101, 104.5], [104, 106, 103, 105]])
    assert enter(WEEK, o, h, l, c, 0, 2) == ("triggered", 1, 104.0)


def test_enter_mid_bar_gap_fills_at_the_open_but_a_bar_open_gap_is_missed():
    o, h, l, c = days([[100, 103, 99, 102], [105, 106, 104.5, 105.5]])
    assert enter(WEEK, o, h, l, c, 0, 1) == ("triggered", 1, 105.0)
    assert enter(WEEK, o, h, l, c, 1, 1)[0] == "gap past trigger"


def test_enter_other_side_first_is_not_this_pattern():
    o, h, l, c = days([[100, 103, 96, 98], [98, 105, 97.5, 104.5]])
    assert enter(WEEK, o, h, l, c, 0, 1)[0] == "other side first"


def test_enter_one_day_breaking_both_is_set_apart():
    o, h, l, c = days([[100, 105, 96, 98]])
    assert enter(WEEK, o, h, l, c, 0, 0)[0] == "same day both"


def test_walk_sub_other_side_inside_the_entry_bar_is_went_3():
    # entry day 0; day 1 is still inside the entry week (d1 = 1) and takes 97
    o, h, l, c = days([[100, 105, 99, 104.5], [104, 106, 96, 97]])
    w = walk_sub(o, h, l, c, WEEK, 0, 104.0, 1)
    assert (w.outcome, w.j, w.fill) == ("went3", 1, 97.0)
    assert w.p_lo == pytest.approx(0.25) and w.p_hi == pytest.approx(0.5)


def test_walk_sub_after_the_entry_bar_closes_only_the_stop_counts():
    # the same two days, but the entry week ended on day 0: 96 is above the stop at 95
    o, h, l, c = days([[100, 105, 99, 104.5], [104, 106, 96, 97], [97, 98, 94, 94.5]])
    w = walk_sub(o, h, l, c, WEEK, 0, 104.0, 0)
    assert (w.outcome, w.j, w.fill) == ("failed", 2, 95.0)
    assert w.p_lo == pytest.approx(0.5)


def test_walk_sub_target_first_wins():
    o, h, l, c = days([[100, 105, 99, 104.5], [104, 108, 103, 107]])
    assert walk_sub(o, h, l, c, WEEK, 0, 104.0, 1).outcome == "won"


# a 3-2-2 long: trigger 109, target 115, stop 100 (the 3's low), the 2D's low (other) 98
T322 = Cand("3-2-2 reversal", 1, 0, 109.0, 115.0, 100.0, 98.0)


def test_322_entry_day_that_opened_under_the_stop_is_not_stopped_by_its_own_open():
    o, h, l, c = days([[99, 110, 98.5, 109.5]])
    status, e, entry = enter(T322, o, h, l, c, 0, 0)
    assert (status, entry) == ("triggered", 109.0)
    assert walk_sub(o, h, l, c, T322, 0, 109.0, 0).outcome == "open"


def test_322_entry_day_closing_beyond_the_stop_failed_that_day():
    o, h, l, c = days([[101, 110, 99, 99.5]])
    assert enter(T322, o, h, l, c, 0, 0)[0] == "triggered"
    w = walk_sub(o, h, l, c, T322, 0, 109.0, 0)
    assert (w.outcome, w.j, w.fill) == ("failed", 0, 100.0)


def test_322_entry_day_dipping_through_the_stop_and_closing_back_is_set_apart():
    o, h, l, c = days([[101, 110, 99, 105]])
    assert enter(T322, o, h, l, c, 0, 0)[0] == "same day both"


def test_322_stop_applies_inside_the_entry_bar_too():
    o, h, l, c = days([[101, 110, 100.5, 109.5], [109, 111, 99.5, 100.2]])
    w = walk_sub(o, h, l, c, T322, 0, 109.0, 1)
    assert (w.outcome, w.fill) == ("failed", 100.0)
