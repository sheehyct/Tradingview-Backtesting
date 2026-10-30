"""Hand vectors v20 for the hourly exit clock's repairs (TVB-39 external audit F1-F3), written
BEFORE the engine change: the entry is a strict break (an hour whose high equals the level is
not the entry hour), the entry day must be observed from its first hour through the entry hour
without a gap, the scan ends at the cap timestamp whatever candles exist, a missing hour before
the exit censors the unit, and elapsed hours are timestamp differences."""

from __future__ import annotations

import pytest

from analysis.domino.census import DAY, HOUR
from analysis.domino.manage import hours_by_day, walk_hourly
from tests.test_domino_manage import TUE, bar, green
from tests.test_domino_manage_a2 import L, _series, hours

CAP = 20


def _entry_day(custom: dict[int, tuple]) -> list[tuple]:
    """24 quiet hours inside the entry day's bar (open 101.0): quiet = (101.0, 101.2, 100.9, 101.1)."""
    h = [(101.0, 101.2, 100.9, 101.1)] * 24
    for k, v in custom.items():
        h[k] = v
    return h


def _walk(daily, hourly, direction="up", level=L, prices=None, cap_end=None):
    i = next(k for k, d in enumerate(daily) if d["t"] == TUE)
    return walk_hourly(
        hourly,
        hours_by_day(hourly),
        daily,
        i,
        direction,
        level,
        prices or {},
        i + CAP if cap_end is None else cap_end,
    )


def _long_tape():
    # the entry day is green above L; the days after are green and never exit on the daily clock
    return _series(list(green(TUE + DAY, o=101.8, k=25)))


def test_v20a_long_equality_hour_is_not_the_entry_even_when_it_would_have_exited():
    """ACE 2026-04-29 shape: hour 0's high EQUALS the level and closes red under the day's open
    (the old walker entered and exited there, a loss before the trade existed); hour 2 trades
    through the level and is the entry; the first red-in-red hour after it is the exit."""
    daily = _long_tape()
    day0 = _entry_day(
        {
            0: (
                101.0,
                L,
                100.9,
                100.8,
            ),  # high == L exactly, red, under the day open: NOT an entry, NOT an exit
            2: (100.8, 101.6, 100.7, 101.2),  # through L: the entry hour (closes green: hold)
            6: (101.2, 101.3, 100.6, 100.7),  # red hour, day red (100.7 < 101.0): exit
        }
    )
    hourly = hours(daily, {TUE: day0})
    wh = _walk(daily, hourly, prices={"t1": 101.6, "t2": 101.65})
    assert wh["status"] == "exit"
    assert wh["entry_hour"] == 2 and wh["hours"] == 4
    assert wh["ret_c"] == pytest.approx((100.7 - L) / L * 100)
    # a target touch stays inclusive: the entry hour's high is exactly 101.6; 101.65 is never reached
    assert wh["touch"]["t1"] == wh["entry"] and wh["touch"]["t2"] is None


def test_v20b_short_equality_hour_is_not_the_entry():
    """The mirror: a short on the entry day's low; hour 0's low EQUALS the level and closes green
    above the day's open; hour 3 trades under the level; hour 5 (green in a green day) exits."""
    daily = _long_tape()
    lvl = 100.5
    # quiet hours close a touch under their open and under the day's open: with the short, a hold
    day0 = [(101.0, 101.2, 100.9, 100.95)] * 24
    day0[0] = (
        101.0,
        101.1,
        lvl,
        101.05,
    )  # low == level exactly, green above the day open: no entry, no exit
    day0[3] = (
        101.05,
        101.1,
        100.4,
        100.9,
    )  # through the level: entry; closes red (with the short): hold
    day0[5] = (100.9, 101.3, 100.8, 101.2)  # green hour, day green (101.2 > 101.0): exit
    hourly = hours(daily, {TUE: day0})
    wh = _walk(daily, hourly, direction="down", level=lvl)
    assert wh["status"] == "exit" and wh["entry_hour"] == 3 and wh["hours"] == 2
    assert wh["ret_c"] == pytest.approx(-(101.2 - lvl) / lvl * 100)


def test_v20c_partial_entry_day_is_not_observable():
    """APEX 2026-03-18 shape: the cache starts mid-day. The first cached hour is not the entry
    hour; the unit's hourly result is 'partial_entry_day' and no entry is recorded. A gap before
    the entry hour is the same case."""
    daily = _long_tape()
    day0 = _entry_day({2: (100.8, 101.6, 100.7, 101.2)})
    full = hours(daily, {TUE: day0})
    assert _walk(daily, full)["entry_hour"] == 2  # the complete day enters at hour 2
    from_hour_6 = [b for b in full if b["t"] >= TUE + 6 * HOUR]
    assert _walk(daily, from_hour_6)["status"] == "partial_entry_day"
    gap_at_1 = [b for b in full if b["t"] != TUE + 1 * HOUR]
    assert _walk(daily, gap_at_1)["status"] == "partial_entry_day"
    # a gap AFTER the entry hour on the entry day is not a partial entry day (it is a coverage gap: v20d)
    gap_at_10 = [b for b in full if b["t"] != TUE + 10 * HOUR]
    assert _walk(daily, gap_at_10)["status"] != "partial_entry_day"


def test_v20d_a_missing_hour_before_the_exit_censors_and_after_the_exit_does_not():
    daily = _series(
        [
            bar(TUE + DAY, 101.8, 102.2, 100.0, 100.4),  # day 1: red, under its open
            *green(TUE + 2 * DAY, o=100.4),
        ]
    )
    day0 = _entry_day({2: (100.8, 101.6, 100.7, 101.2)})
    day1 = [(101.8, 102.0, 101.6, 101.9)] * 24
    day1[3] = (101.9, 102.1, 101.0, 101.2)  # red hour, day red: the exit
    for k in range(4, 24):
        day1[k] = (101.2, 101.3, 100.0, 100.4)
    full = hours(daily, {TUE: day0, TUE + DAY: day1})
    ok = _walk(daily, full)
    assert ok["status"] == "exit" and ok["hours"] == (24 - 2) + 3
    # day 0 hour 10 missing, between the entry and the exit: censored (the path is not observed)
    gap_before = [b for b in full if b["t"] != TUE + 10 * HOUR]
    assert _walk(daily, gap_before)["status"] == "censored"
    # day 2 hour 5 missing, after the exit: the exit stands
    gap_after = [b for b in full if b["t"] != TUE + 2 * DAY + 5 * HOUR]
    assert _walk(daily, gap_after)["status"] == "exit"


def test_v20e_a_missing_cap_hour_censors_even_with_later_data_and_hours_come_from_timestamps():
    """The audit's fault injection on v17b: no exit ever, day 20's 23:00 candle removed, later
    days present and a qualifying exit hour on day 21. The old walker ran into day 21 and
    exited there; the scan now ends at the cap timestamp and the missing hour censors."""
    daily = _series(list(green(TUE + DAY, o=101.8, k=25)))
    hourly = hours(daily)
    for b in hourly:
        b["o"], b["c"] = b["c"] - 0.1, b["c"]  # every hour green and above its day's open: no exit
    i = next(k for k, d in enumerate(daily) if d["t"] == TUE)
    cap_t = daily[i + CAP]["t"]
    full = _walk(daily, hourly, level=101.0)
    assert full["status"] == "open" and full["hours"] == CAP * 24 + 23 and full["entry_hour"] == 0
    # make day 21 hour 1 a red hour in a red day (an exit if the scan ever got there)
    without_cap_hour = [dict(b) for b in hourly if b["t"] != cap_t + 23 * HOUR]
    for b in without_cap_hour:
        if b["t"] >= cap_t + DAY:
            b["o"], b["c"] = b["c"] + 0.1, b["c"] - 5.0
    wh = _walk(daily, without_cap_hour, level=101.0)
    assert wh["status"] == "censored"
    # the full tape with day 21 red as well: still open at the cap, never into day 21
    with_cap_hour = [dict(b) for b in hourly]
    for b in with_cap_hour:
        if b["t"] >= cap_t + DAY:
            b["o"], b["c"] = b["c"] + 0.1, b["c"] - 5.0
    wh2 = _walk(daily, with_cap_hour, level=101.0)
    assert wh2["status"] == "open" and wh2["hours"] == CAP * 24 + 23
