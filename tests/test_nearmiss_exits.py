"""Hand vectors for the exit lab (analysis/nearmiss/exits.py)."""

import numpy as np
import pandas as pd
import pytest

from analysis.nearmiss.exits import (
    MODES,
    Params,
    atr,
    bands,
    ema,
    indicators,
    rma,
    rsi,
    walk_exit,
)
from analysis.nearmiss.htf import Cand, aggregate, candidates, enter, walk_sub

# a 2-1-2 long: trigger 104, target 108, stop 95, the inside bar's low (other) 97
LONG = Cand("2-1-2 reversal", 1, 0, 104.0, 108.0, 95.0, 97.0)
SHORT = Cand("2-1-2 reversal", -1, 0, 96.0, 92.0, 105.0, 103.0)


def bars(rows):
    a = np.array(rows, dtype=float)
    return a[:, 0], a[:, 1], a[:, 2], a[:, 3]  # open, high, low, close


def blank(n):
    return {k: np.full(n, np.nan) for k in ("atr", "ema", "rsi", "upper", "lower")}


def run(rows, mode, cd=LONG, entry=None, d1=0, ind=None, p=Params()):
    o, h, l, c = bars(rows)
    entry = cd.trigger if entry is None else entry
    return walk_exit(o, h, l, c, cd, 0, entry, d1, mode, ind or blank(len(o)), p)


def test_ema_and_wilder_average_are_seeded_with_the_simple_average():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    e = ema(x, 3)  # seed (1+2+3)/3 = 2, alpha 0.5
    assert np.isnan(e[1]) and e[2] == 2.0 and e[3] == 3.0 and e[4] == 4.0
    r = rma(x, 3)  # alpha 1/3
    assert r[2] == 2.0 and r[3] == pytest.approx(2 + 2 / 3) and r[4] == pytest.approx(31 / 9)


def test_rsi_all_gains_is_100_and_a_mixed_run_matches_by_hand():
    assert rsi(np.array([1.0, 2.0, 3.0, 4.0]), 2)[-1] == 100.0
    r = rsi(np.array([10.0, 11.0, 10.0, 12.0]), 2)
    # changes +1 -1 +2: seed at index 2 up .5 dn .5 -> 50; then up 1.25 dn .25 -> 83.33
    assert np.isnan(r[1]) and r[2] == pytest.approx(50.0) and r[3] == pytest.approx(250 / 3)


def test_bands_use_the_population_standard_deviation():
    up, lo = bands(np.array([1.0, 3.0]), 2, 2.0)
    assert up[1] == pytest.approx(4.0) and lo[1] == pytest.approx(0.0)


def test_atr_first_bar_is_its_own_range():
    h, l, c = np.array([10.0, 12.0, 11.0]), np.array([8.0, 9.0, 7.0]), np.array([9.0, 11.0, 8.0])
    assert atr(h, l, c, 2)[1] == pytest.approx((2 + 3) / 2)  # ranges 2, 3, 4
    assert atr(h, l, c, 2)[2] == pytest.approx(0.5 * 4 + 0.5 * 2.5)


def test_pattern_and_fraction_modes_reproduce_the_near_miss_walker():
    rng = np.random.default_rng(11)
    n = 6000
    c = np.round(100 + np.cumsum(rng.normal(0, 1, n)), 1)
    o = np.round(np.r_[100, c[:-1]] + rng.normal(0, 0.3, n), 1)
    h = np.round(np.maximum(o, c) + np.abs(rng.normal(0, 0.6, n)), 1)
    l = np.round(np.minimum(o, c) - np.abs(rng.normal(0, 0.6, n)), 1)
    dates = pd.bdate_range("2000-01-03", periods=n)
    ind = indicators(h, l, c)
    big_o, big_h, big_l, big_c, first, last = aggregate(dates, o, h, l, c, "W")
    seen = 0
    for cd in candidates(big_o, big_h, big_l, big_c):
        d0, d1 = int(first[cd.i]), int(last[cd.i])
        status, e, entry = enter(cd, o, h, l, c, d0, d1)
        if status != "triggered":
            continue
        seen += 1
        for mode, k in (("pattern", 1.0), ("fraction", 0.4)):
            a = walk_sub(o, h, l, c, cd, e, entry, d1, k)
            b = walk_exit(o, h, l, c, cd, e, entry, d1, mode, ind)
            assert (a.outcome, a.j) == (b.outcome, b.j)
            if a.outcome != "open":
                assert a.fill == pytest.approx(b.fill)
        for mode in MODES:  # an added exit can only end a trade sooner, never later
            b = walk_exit(o, h, l, c, cd, e, entry, d1, mode, ind)
            a = walk_exit(o, h, l, c, cd, e, entry, d1, "pattern", ind)
            assert a.outcome == "open" or b.j <= a.j
    assert seen > 300


def test_prior_day_rests_at_the_previous_days_low_from_the_day_after_entry():
    # entry day low 101 does not count against itself; day 2 trades under day 1's low 103
    out = run(
        [[102, 105, 101, 104.5], [104.5, 106, 103, 105], [105, 105.5, 102.5, 103]], "prior_day"
    )
    assert (out.outcome, out.j, out.fill) == ("rule", 2, 103.0)


def test_prior_day_needs_a_strict_break_and_a_gap_fills_at_the_open():
    out = run([[102, 105, 101, 104.5], [104.5, 106, 101, 105], [105, 107, 101, 106]], "prior_day")
    assert out.outcome == "open"  # equal lows never break
    out = run([[102, 105, 101, 104.5], [100, 102, 99, 101]], "prior_day")
    assert (out.outcome, out.fill) == ("rule", 100.0)


def test_giveback_arms_a_third_of_the_way_and_trails_half_the_distance_from_the_best():
    # dist 4: armed at 105.33. Day 0 best 105 (not armed). Day 1 best 106.5 -> armed, level
    # 104.5 for day 2. Day 2 makes a new best 107 AND trades 104.4: the level known before the
    # day (104.5) is the one that fills.
    rows = [[102, 105, 101, 104.5], [104.5, 106.5, 104.2, 106], [106, 107, 104.4, 105]]
    out = run(rows, "giveback")
    assert (out.outcome, out.j, out.fill) == ("rule", 2, 104.5)


def test_giveback_never_arms_below_a_third_of_the_way():
    rows = [[102, 105, 101, 104.5], [104.5, 105.2, 98, 99], [99, 100, 96, 97]]
    out = run(rows, "giveback", d1=0)
    assert out.outcome == "open"  # 98 and 96 are above the stop 95, the entry bar has closed


def test_went_3_still_comes_first_when_it_sits_nearer_than_the_rules_level():
    # inside the entry bar (d1 = 2) the other side 97 is the invalidation; prior-day level is 96
    rows = [[102, 105, 96, 104.5], [104.5, 105, 96.5, 97.5]]
    out = run(rows, "prior_day", d1=2)
    assert (out.outcome, out.fill) == ("went3", 97.0)


def test_one_day_touching_the_target_and_the_rules_level_is_the_adverse_one():
    rows = [[102, 105, 101, 104.5], [104.5, 106, 103, 105], [105, 108.5, 102, 108]]
    out = run(rows, "prior_day")
    assert (out.outcome, out.j, out.fill) == ("both", 2, 103.0)


def test_chandelier_is_a_close_through_the_line_as_it_stood_the_day_before():
    ind = blank(3)
    ind["atr"][:] = 1.0  # line after day 0: 105 - 3 = 102; after day 1: 106 - 3 = 103
    rows = [[102, 105, 101, 104.5], [104.5, 106, 101.5, 102.5], [102.5, 104, 102, 102.9]]
    out = run(rows, "chandelier", ind=ind)
    assert (out.outcome, out.j, out.fill) == ("rule", 2, 102.9)  # day 1 closed above 102


def test_chandelier_line_only_tightens():
    ind = blank(4)
    ind["atr"][:] = [1.0, 1.0, 2.0, 2.0]  # day 2's fresh line 106 - 6 = 100 does not replace 103
    rows = [
        [102, 105, 101, 104.5],
        [104.5, 106, 104, 105.5],
        [105.5, 105.8, 103.5, 104],
        [104, 104.5, 102.5, 102.8],
    ]
    out = run(rows, "chandelier", ind=ind)
    assert (out.outcome, out.j, out.fill) == ("rule", 3, 102.8)


def test_ema_rule_can_fire_at_the_entry_days_close():
    ind = blank(2)
    ind["ema"][:] = 104.8
    out = run([[102, 105, 101, 104.5], [104.5, 106, 104, 105]], "ema", ind=ind)
    assert (out.outcome, out.j, out.fill) == ("rule", 0, 104.5)


def test_rsi_rule_waits_for_a_close_under_50():
    ind = blank(3)
    ind["rsi"][:] = [61.0, 50.0, 49.9]  # 50 exactly is not under 50
    rows = [[102, 105, 101, 104.5], [104.5, 106, 104, 105], [105, 105.5, 103, 103.5]]
    out = run(rows, "rsi", ind=ind)
    assert (out.outcome, out.j, out.fill) == ("rule", 2, 103.5)


def test_bollinger_tag_takes_the_close_of_the_day_that_touched_the_band():
    ind = blank(2)
    ind["upper"][:] = [105.5, 106.0]
    out = run([[102, 105, 101, 104.5], [104.5, 106, 104, 105.7]], "bollinger", ind=ind)
    assert (out.outcome, out.j, out.fill) == ("rule", 1, 105.7)


def test_time_stop_leaves_at_the_close_n_sessions_after_the_entry():
    rows = [[102, 105, 101, 104.5]] + [[104.5, 105, 104, 104.6]] * 5
    out = run(rows, "time", p=Params(time_bars=3))
    assert (out.outcome, out.j, out.fill) == ("rule", 3, 104.6)


def test_the_target_still_wins_before_any_rule():
    ind = blank(2)
    ind["ema"][:] = 200.0
    out = run([[102, 105, 104.2, 104.9], [105, 108, 104.5, 105]], "ema", ind=ind)
    assert (out.outcome, out.fill) == ("rule", 104.9)  # the entry day's close is already under
    ind["ema"][:] = [100.0, 200.0]
    out = run([[102, 105, 104.2, 104.9], [105, 108, 104.5, 105]], "ema", ind=ind)
    assert (out.outcome, out.fill) == ("won", 108.0)  # the target is touched before that close


def test_short_side_mirrors_the_prior_day_and_giveback_rules():
    # short from 96, target 92 (dist -4): prior-day level = the previous day's high
    rows = [[98, 99, 95, 95.5], [95.5, 97, 94, 95], [95, 97.5, 94.5, 97]]
    out = run(rows, "prior_day", cd=SHORT)
    assert (out.outcome, out.j, out.fill) == ("rule", 2, 97.0)
    # give-back: armed at 94.67; best 93.5 after day 1 -> level 95.5 for day 2
    rows = [[98, 99, 95, 95.5], [95.5, 95.8, 93.5, 94], [94, 95.6, 93.8, 95]]
    out = run(rows, "giveback", cd=SHORT)
    assert (out.outcome, out.j, out.fill) == ("rule", 2, 95.5)
