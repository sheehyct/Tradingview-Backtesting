"""The session calendar (the bench prereg, docs/experiments/tvb43_bench_prereg.md section 2.1,
the owner's word 2026-11-01): hand vectors written before any ES row existed.

Sessions are daily bars relabelled to their trade date (00:00 UTC of the trade date in the
engine's clock); there are no weekend bars and a holiday removes a session. Under
`census.use_calendar("session")`: a Monday's level is Friday's; a four-session week is complete;
the Tuesday after a Monday holiday opens its week; the hourly clock walks a session's hours from
its open to its last traded hour and steps to the next session's first hour; the cap is the cap
session's last hour. Under the default calendar every vector below reads as the 24/7 engine
always read it (the byte-identical gate on the committed crypto book is run separately)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from analysis.domino import census
from analysis.domino.census import DAY, HOUR, _context, aggregate, day_events, use_calendar
from analysis.domino.manage import coin_manage_rows, hours_by_day, walk_hourly
from analysis.domino.run_export import Tape


def ms(y, m, d, h=0):
    return int(datetime(y, m, d, h, tzinfo=timezone.utc).timestamp() * 1000)


def bar(t, o, h, l, c, v=1000.0):  # noqa: E741
    return {"t": t, "o": o, "h": h, "l": l, "c": c, "v": v}


MON = ms(2026, 9, 7)  # a Monday (Labor Day 2026 is this day, which the holiday vector uses)


def sessions(
    first_monday: int, weeks: int, skip: set[int] | None = None, o=100.0, h=101.0, l=99.0, c=100.5
):  # noqa: E741
    """Trade-date bars Monday to Friday for `weeks` weeks; `skip` holds day offsets with no session."""
    out = []
    for w in range(weeks):
        for d in range(5):
            k = 7 * w + d
            if skip and k in skip:
                continue
            out.append(bar(first_monday + k * DAY, o, h, l, c))
    return out


def test_use_calendar_sets_and_restores():
    assert census.CALENDAR == "utc_day"
    with use_calendar("session"):
        assert census.session_calendar()
    assert census.CALENDAR == "utc_day"
    with pytest.raises(ValueError):
        with use_calendar("lunar"):
            pass


def test_session_weeks_are_complete_without_weekend_days_and_a_holiday_week_too():
    daily = sessions(MON, 3, skip={7})  # the second Monday is a holiday: that week is Tue-Fri
    with use_calendar("session"):
        weeks = aggregate(daily, "W")
    assert [len(w["days"]) for w in weeks] == [5, 4, 5]
    assert [w["complete"] for w in weeks] == [True, True, False]  # the last week is still forming
    assert weeks[1]["t"] == MON + 7 * DAY and daily[weeks[1]["days"][0]]["t"] == MON + 8 * DAY
    # a tape that STARTS mid-week still drops its partial first bucket (the scanner's rule: the
    # bucket's open was not observed; a holiday at the data start cannot be told from a gap)
    with use_calendar("session"):
        late = aggregate(sessions(MON, 2, skip={0}), "W")
    assert len(late) == 1 and late[0]["t"] == MON + 7 * DAY
    # the default calendar on the same bars: no week has seven days, none is complete
    weeks24 = aggregate(daily, "W")
    assert all(not w["complete"] for w in weeks24)


def test_session_week_opens_on_its_first_session_after_a_holiday():
    daily = sessions(MON, 3, skip={7})  # the second Monday is a holiday
    with use_calendar("session"):
        ctx = _context(daily, {tf: aggregate(daily, tf) for tf in ("W", "M", "Q")})
    assert ctx["W"][0]["is_first_day"] is True  # the first Monday
    assert ctx["W"][5]["is_first_day"] is True  # the Tuesday after the holiday opens its week
    assert ctx["W"][6]["is_first_day"] is False
    assert ctx["W"][9]["is_first_day"] is True  # the third Monday
    ctx24 = _context(daily, {tf: aggregate(daily, tf) for tf in ("W", "M", "Q")})
    assert ctx24["W"][5]["is_first_day"] is False  # the 24/7 rule wants the calendar Monday


def test_a_monday_s_level_is_friday_s_on_sessions_and_nothing_on_the_default_calendar():
    daily = sessions(MON, 2)
    fri, mon2 = 4, 5
    daily[fri] = bar(daily[fri]["t"], 100.0, 103.0, 99.0, 102.0)  # Friday's high 103 is the level
    daily[mon2] = bar(daily[mon2]["t"], 102.0, 104.0, 101.0, 103.5)  # Monday breaks 103
    buckets = {tf: aggregate(daily, tf) for tf in ("W", "M", "Q")}
    with use_calendar("session"):
        buckets_s = {tf: aggregate(daily, tf) for tf in ("W", "M", "Q")}
        evs = day_events(daily, mon2, _context(daily, buckets_s))
    assert evs is not None
    up = next(e for e in evs if e[0] == "up")
    assert up[1]["D"] == 103.0 and up[2]["D"][1] is daily[fri]  # the setup bar is Friday's
    assert up[2]["D"][3] is daily[fri - 1]  # the bar before it is Thursday's
    assert day_events(daily, mon2, _context(daily, buckets)) is None  # 24/7: no bar "yesterday"


def _globex_hours(daily, per_day=23, o=100.0, c=100.2, h=100.6, l=99.6):  # noqa: E741
    """`per_day` contiguous hours from each session's open, in session time."""
    out = []
    for d in daily:
        for k in range(per_day):
            out.append(bar(d["t"] + k * HOUR, o, h, l, c))
    return out


def test_session_hourly_clock_crosses_the_overnight_break_and_the_weekend_as_one_step():
    daily = sessions(MON, 2)
    hourly = _globex_hours(daily)
    i = 4  # Friday's session
    # hour 20 of Friday trades through the level 100.5; the first hour closing against its own
    # open with the session against it is hour 1 of MONDAY's session (the hours in between stay green)
    for k in range(23):
        hourly[i * 23 + k] = bar(daily[i]["t"] + k * HOUR, 100.0, 100.4, 99.8, 100.2)
    hourly[i * 23 + 20] = bar(daily[i]["t"] + 20 * HOUR, 100.3, 100.9, 100.1, 100.6)
    j = 5  # Monday
    for k in range(23):
        hourly[j * 23 + k] = bar(daily[j]["t"] + k * HOUR, 100.0, 100.4, 99.9, 100.2)
    hourly[j * 23 + 1] = bar(
        daily[j]["t"] + 1 * HOUR, 100.3, 100.4, 99.5, 99.7
    )  # red, below the session's open
    daily[j] = bar(daily[j]["t"], 100.0, 101.0, 99.0, 100.5)
    by_day = hours_by_day(hourly)
    prices = {"t1": 110.0, "one_r": 101.0}
    with use_calendar("session"):
        wh = walk_hourly(hourly, by_day, daily, i, "up", 100.5, prices, cap_end=9)
    assert wh["status"] == "exit" and wh["entry_hour"] == 20
    # session time: Friday 20:00 to Monday 01:00 is 53 hours on the trade-date clock (the weekend's
    # 48 empty hours included); the exporter lands it on Monday's real hour 1 through the session table
    assert wh["hours"] == (7 - 4) * 24 + 1 - 20
    assert wh["end"] == j * 23 + 1
    # the 24/7 walk on the same bars censors: the hour after Friday's last is two session-time
    # hours on, a gap by its rule
    wh24 = walk_hourly(hourly, by_day, daily, i, "up", 100.5, prices, cap_end=9)
    assert wh24["status"] == "censored"


def test_session_hourly_clock_marks_the_cap_session_s_last_hour_and_censors_a_missing_hour():
    daily = sessions(MON, 2)
    hourly = _globex_hours(
        daily, c=100.3, h=100.4
    )  # every hour green and under the level: nothing fires
    i = 1
    hourly[i * 23 + 2] = bar(daily[i]["t"] + 2 * HOUR, 100.0, 100.9, 99.9, 100.3)  # the entry hour
    by_day = hours_by_day(hourly)
    with use_calendar("session"):
        wh = walk_hourly(hourly, by_day, daily, i, "up", 100.5, {"t1": 110.0}, cap_end=3)
        assert (
            wh["status"] == "open" and wh["end"] == 3 * 23 + 22
        )  # the cap session's last hour (offset 22)
        assert wh["hours"] == (2 * 24 + 22) - 2
        # a short session (an early close at hour 12) is not a gap: the walk steps on
        short = [b for b in hourly if not (daily[2]["t"] + 12 * HOUR <= b["t"] < daily[3]["t"])]
        wh2 = walk_hourly(
            short, hours_by_day(short), daily, i, "up", 100.5, {"t1": 110.0}, cap_end=3
        )
        assert wh2["status"] == "open" and short[wh2["end"]]["t"] == daily[3]["t"] + 22 * HOUR
        # a missing hour INSIDE a session before the exit censors
        gappy = [b for b in hourly if b["t"] != daily[2]["t"] + 5 * HOUR]
        wh3 = walk_hourly(
            gappy, hours_by_day(gappy), daily, i, "up", 100.5, {"t1": 110.0}, cap_end=3
        )
        assert wh3["status"] == "censored"
        # a session with no hours at all before the cap censors; no entry hour on a fully
        # observed short session is no_entry_hour, not partial
        none = [b for b in hourly if not (daily[2]["t"] <= b["t"] < daily[3]["t"])]
        wh4 = walk_hourly(none, hours_by_day(none), daily, i, "up", 100.5, {"t1": 110.0}, cap_end=3)
        assert wh4["status"] == "censored"
        quiet = [
            b for b in hourly if b["t"] < daily[i]["t"] + 10 * HOUR or b["t"] >= daily[i + 1]["t"]
        ]
        wh5 = walk_hourly(
            quiet, hours_by_day(quiet), daily, i, "up", 200.0, {"t1": 210.0}, cap_end=3
        )
        assert wh5["status"] == "no_entry_hour"


def test_the_management_book_runs_on_a_session_tape_and_scores_monday_units():
    """End to end: Friday's high breaks on Monday; the unit exists and the week's open is the
    Monday session's open (the first session of the trade-date week)."""
    daily = sessions(MON, 8)  # enough sessions for the 20-session cap after the entry
    fri = 9  # the second Friday
    daily[fri] = bar(daily[fri]["t"], 100.0, 103.0, 99.0, 102.0)
    daily[fri + 1] = bar(
        daily[fri + 1]["t"], 102.0, 104.0, 101.0, 103.5
    )  # Monday breaks 103, closes green
    meta = {"coin": "ES", "dex": "cme", "liquid": True}
    with use_calendar("session"):
        rows, counts = coin_manage_rows(meta, daily, None)
    mon = [
        r for r in rows if r["date"] == "2026-09-21" and r["direction"] == "up" and r["tf"] == "D"
    ]
    assert len(mon) == 1
    u = mon[0]
    assert (
        u["level"] == 103.0 and u["stop"] == 99.0 and u["w_support"] == "with"
    )  # 103 > the Monday open 102
    assert u["status"] in ("exit", "open")
    rows24, _ = coin_manage_rows(meta, daily, None)
    assert not [r for r in rows24 if r["date"] == "2026-09-21"]  # 24/7: Monday has no "yesterday"


def test_tape_maps_session_rows_to_real_opens_and_hours_across_the_weekend():
    """The exporter's clock for a session tape: row dates are trade dates, card times are the
    exchange's real opens (22:00 UTC the evening before); 24 hour steps is one session on."""
    # the contract's clock is seconds: Sunday 22:00 UTC, the Monday 2026-09-07 session's real open
    sun = ms(2026, 9, 6, 22) // 1000
    opens = {}
    daily = []
    for w in range(2):
        for d in range(5):
            # the clocks go back over the weekend: the second week's sessions open at 23:00 UTC
            t = sun + (7 * w + d) * 86_400 + (3600 if w == 1 else 0)
            date = datetime.fromtimestamp(t + 6 * 3600, tz=timezone.utc).strftime("%Y-%m-%d")
            opens[date] = t
            daily.append([t, 100.0, 101.0, 99.0, 100.5, 1.0])
    tape = Tape(daily, [], opens)
    fri_date, mon_date = "2026-09-11", "2026-09-14"
    assert tape.open_of(fri_date) == daily[4][0] and tape.open_of(mon_date) == daily[5][0]
    # entry at hour 20 of Friday's session; the hourly clock out at Monday's hour 1 is 53
    # session-time hours later (the weekend's 48 empty hours included): the real time is Monday's
    # real open plus one hour, not Friday's open plus 53
    assert tape.hour_time(fri_date, 20) == daily[4][0] + 20 * 3600
    assert tape.hour_time(fri_date, 20 + 53) == daily[5][0] + 1 * 3600
    assert tape.hour_time(fri_date, 20 + 53) != daily[4][0] + 73 * 3600
    # run one's clock is untouched: no session table, plain arithmetic from the 00:00 UTC day
    plain = Tape([[ms(2026, 9, 7) // 1000 + k * 86400, 1, 1, 1, 1, 1] for k in range(3)], [])
    t0 = plain.open_of("2026-09-07")
    assert t0 == ms(2026, 9, 7) // 1000 and plain.hour_time("2026-09-07", 25) == t0 + 25 * 3600
