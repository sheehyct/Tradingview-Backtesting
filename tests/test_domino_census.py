"""Hand-vector tests for the TVB-37 domino census engine (analysis/domino/census.py).

Bars here are hand-made test vectors for the level logic, not market data.
"""

from datetime import datetime, timezone

from analysis.domino.census import (
    DAY,
    _context,
    _quarter_state,
    aggregate,
    analyze_coin,
    classify,
    distance_band,
    liquid,
    month_start,
    nesting_violation,
    next_start,
    normalize,
    quarter_start,
    shape_flags,
    week_start,
)


def ms(y, m, d):
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1000)


def bar(t, o, h, l, c, v=1000.0):
    return {"t": t, "o": o, "h": h, "l": l, "c": c, "v": v}


def test_calendar_starts():
    mon = ms(2026, 10, 5)  # a Monday
    assert week_start(mon) == mon
    assert week_start(ms(2026, 10, 8)) == mon  # Thursday -> that Monday
    assert week_start(ms(2026, 10, 4)) == ms(2026, 9, 28)  # Sunday belongs to the week before
    assert month_start(ms(2026, 10, 17)) == ms(2026, 10, 1)
    assert quarter_start(ms(2026, 11, 20)) == ms(2026, 10, 1)
    assert quarter_start(ms(2026, 9, 30)) == ms(2026, 7, 1)


def test_classify_equality_never_breaks():
    prev = bar(0, 100, 105.00, 98.00, 101)
    assert classify(bar(0, 100, 105.00, 99.00, 101), prev) == "1"
    assert classify(bar(0, 100, 104.00, 98.00, 101), prev) == "1"
    assert classify(bar(0, 100, 105.01, 98.50, 101), prev) == "2U"
    assert classify(bar(0, 100, 104.00, 97.99, 101), prev) == "2D"
    assert classify(bar(0, 100, 105.01, 97.99, 101), prev) == "3"


def test_aggregate_drops_partial_first_week_and_marks_completeness():
    # start on a Wednesday: the first (partial) week must be dropped
    t0 = ms(2026, 9, 30)
    daily = [
        bar(t0 + k * DAY, 100 + k, 101 + k, 99 + k, 100.5 + k) for k in range(12)
    ]  # Wed .. Sun of next week
    weeks = aggregate(daily, "W")
    assert weeks[0]["t"] == ms(2026, 10, 5)
    assert weeks[0]["complete"] is True
    assert weeks[0]["h"] == max(d["h"] for d in daily[5:12])
    assert len(weeks) == 1


def test_first_break_only_and_nesting():
    # two complete weeks then a third week where the prior-week high breaks on day 2, not again on day 3
    t0 = ms(2026, 9, 21)  # Monday
    daily = []
    for k in range(14):
        daily.append(bar(t0 + k * DAY, 100, 102, 98, 101))  # weeks 1 and 2 flat: high 102 / low 98
    t3 = t0 + 14 * DAY
    daily.append(bar(t3, 101, 101.5, 99, 101))  # Monday: inside
    daily.append(
        bar(t3 + DAY, 101, 103, 100, 102.5)
    )  # Tuesday: breaks yesterday's high AND last week's high
    daily.append(
        bar(t3 + 2 * DAY, 102.5, 104, 101, 103)
    )  # Wednesday: new daily break, week already 2U
    res = analyze_coin(daily)
    tue = [r for r in res["rows"] if r["date"] == "2026-10-06"]
    assert len(tue) == 1 and tue[0]["tfs"] == "D+W" and tue[0]["direction"] == "up"
    assert tue[0]["band"] == "within1"  # 101.5 vs 102.0 is about 0.5%
    wed = [r for r in res["rows"] if r["date"] == "2026-10-07"]
    assert wed == []  # the week does not break twice
    assert res["agg"]["violations"] == 0
    assert res["agg"]["rank"][("up", 2)] == 1


def test_exact_stack_when_sunday_made_the_weekly_high():
    t0 = ms(2026, 9, 21)
    daily = [bar(t0 + k * DAY, 100, 102, 98, 101) for k in range(7)]
    t1 = t0 + 7 * DAY
    daily += [bar(t1 + k * DAY, 100, 102, 98, 101) for k in range(6)]
    daily.append(bar(t1 + 6 * DAY, 101, 105, 100, 104.5))  # Sunday makes the week's high at 105
    daily.append(
        bar(t1 + 7 * DAY, 104.5, 106, 103, 105.5)
    )  # Monday breaks 105: day and week at one price
    res = analyze_coin(daily)
    mon = [r for r in res["rows"] if r["date"] == "2026-10-05" and r["direction"] == "up"]
    assert len(mon) == 1 and mon[0]["tfs"] == "D+W" and mon[0]["band"] == "exact"
    assert mon[0]["shared_open"] == "W"


def test_shape_flags_third_and_strict():
    # hammer: range 10, body 100..101 at the top, no upper wick
    assert shape_flags(bar(0, 100.0, 101.0, 91.0, 101.0), "up") == (True, True)
    # body in the top third but a 2-point upper wick on a 10-point range (20% > sliver)
    assert shape_flags(bar(0, 98.5, 101.0, 91.0, 99.0), "up") == (True, False)
    # body in the middle: neither
    assert shape_flags(bar(0, 95.0, 101.0, 91.0, 96.0), "up") == (False, False)
    # shooter mirror
    assert shape_flags(bar(0, 91.0, 101.0, 91.0, 92.0), "down") == (True, True)
    assert shape_flags(bar(0, 94.0, 101.0, 91.0, 93.0), "down") == (
        True,
        False,
    )  # 2-point wick = 20%


def test_distance_bands():
    assert distance_band([100.0, 100.0])[1] == "exact"
    assert distance_band([100.0, 100.2])[1] == "near"
    assert distance_band([100.0, 100.8])[1] == "within1"
    assert distance_band([100.0, 102.0])[1] == "spread"


# --- vectors added after the TVB-37 Codex audit (docs/reviews/tvb37-codex-audit.md) ---


def raw(t, o, h, l, c, v="1000"):
    """A candle as the venue serves it: strings, with the day start in ms."""
    return {"t": t, "o": str(o), "h": str(h), "l": str(l), "c": str(c), "v": str(v)}


def test_band_boundaries_are_inclusive_in_decimal():  # audit F3
    assert distance_band([0.1, 0.10025])[1] == "near"  # exactly 0.25%
    assert distance_band([0.1, 0.101])[1] == "within1"  # exactly 1%
    assert distance_band([0.1, 0.1010001])[1] == "spread"  # just over
    assert distance_band([7.0, 7.0175])[1] == "near"  # 0.25% of an awkward base
    frac, band = distance_band([100.0, 101.0])
    assert frac == 0.01 and band == "within1"


def test_wick_boundary_exactly_ten_percent_is_strict():  # audit F6
    assert shape_flags(bar(0, 0.19, 0.2, 0.1, 0.19), "up") == (True, True)
    assert shape_flags(bar(0, 0.19, 0.2, 0.1, 0.19), "down") == (False, False)
    assert shape_flags(bar(0, 0.11, 0.2, 0.1, 0.11), "down") == (True, True)
    assert shape_flags(bar(0, 0.189, 0.2, 0.1, 0.189), "up") == (True, False)  # 11% wick
    # body exactly on the third line counts (open at the two-thirds mark of a 91..100 range)
    assert shape_flags(bar(0, 97.0, 100.0, 91.0, 100.0), "up") == (True, True)
    assert shape_flags(bar(0, 96.99, 100.0, 91.0, 100.0), "up") == (False, False)
    assert shape_flags(bar(0, 100.0, 100.0, 100.0, 100.0), "up") == (False, False)  # zero range


def test_nesting_violation_catches_a_week_only_hit():  # audit F2
    assert nesting_violation({"W": 1.0}) is True
    assert nesting_violation({"M": 1.0, "Q": 1.0}) is True
    assert nesting_violation({"D": 1.0, "W": 1.0}) is False
    assert nesting_violation({"D": 1.0}) is False
    assert nesting_violation({}) is False


def test_duplicate_masking_a_missing_day_is_not_complete():  # audit F1
    mon = ms(2026, 9, 28)
    rows = [raw(mon + k * DAY, 100, 101, 99, 100) for k in range(7) if k != 2]  # no Wednesday
    rows.append(raw(mon + DAY, 100, 150, 99, 100))  # Tuesday served twice; the LAST copy wins
    rows += [raw(mon + 7 * DAY + k * DAY, 100, 101, 99, 100) for k in range(7)]  # full next week
    st = {}
    daily = normalize(rows, mon + 20 * DAY, st)
    assert st == {"duplicates": 1, "unaligned": 0, "gap_days": 1}
    assert len(daily) == 13 and daily[1]["h"] == 150.0  # one Tuesday, the later copy
    weeks = aggregate(daily, "W")
    assert [w["complete"] for w in weeks] == [False, True]  # six bars never make a week
    assert normalize([raw(mon + 1, 1, 1, 1, 1)], mon + 20 * DAY, st) == [] and st["unaligned"] == 1


def test_gap_day_carries_no_event_and_is_not_a_shared_open():  # audit F1
    t0 = ms(2026, 9, 21)
    daily = [bar(t0 + k * DAY, 100, 102, 98, 101) for k in range(7)]  # a full week
    daily.append(bar(t0 + 8 * DAY, 101, 110, 100, 109))  # Tuesday; Monday is missing
    daily.append(bar(t0 + 9 * DAY, 109, 112, 108, 111))  # Wednesday breaks Tuesday's high
    res = analyze_coin(daily)
    assert res["agg"]["skipped_no_yesterday"] == 1
    assert [
        r["date"] for r in res["rows"]
    ] == []  # Tuesday skipped; the week broke there, not on Wed
    assert res["agg"]["violations"] == 0
    ctx = _context(daily, {tf: aggregate(daily, tf) for tf in ("W", "M", "Q")})
    assert ctx["W"][7]["is_first_day"] is False  # Tuesday is not the week's open
    assert ctx["W"][0]["is_first_day"] is True


def test_month_aggregation_leap_february_and_year_roll():
    t0 = ms(2024, 1, 1)
    daily = [bar(t0 + k * DAY, 100, 101, 99, 100) for k in range(31 + 29 + 31)]
    months = aggregate(daily, "M")
    assert [len(m["days"]) for m in months] == [31, 29, 31]
    assert all(m["complete"] for m in months)
    assert next_start("M", ms(2025, 12, 1)) == ms(2026, 1, 1)
    assert next_start("Q", ms(2025, 10, 1)) == ms(2026, 1, 1)
    assert next_start("W", ms(2026, 9, 28)) == ms(2026, 10, 5)


def test_quarter_states_are_exhaustive_and_equality_to_the_open_is_against():  # audit F7, F8
    prev = {"h": 110.0, "l": 90.0}
    base = {"prev": prev, "open": 100.0}
    assert _quarter_state(None, False, "up", 1.0) == "unknown"
    assert _quarter_state({"prev": None}, False, "up", 1.0) == "unknown"
    assert _quarter_state(base | {"run_h": 105.0, "run_l": 95.0}, True, "up", 1.0) == "breaks_today"
    assert (
        _quarter_state(base | {"run_h": 111.0, "run_l": 95.0}, False, "up", 1.0)
        == "broken_out_before"
    )
    assert _quarter_state(base | {"run_h": 105.0, "run_l": 89.0}, False, "up", 1.0) == "opposite"
    assert _quarter_state(base | {"run_h": 111.0, "run_l": 89.0}, False, "up", 1.0) == "both"
    assert (
        _quarter_state(base | {"run_h": 105.0, "run_l": 95.0}, False, "up", 101.0) == "inside_with"
    )
    assert (
        _quarter_state(base | {"run_h": 105.0, "run_l": 95.0}, False, "up", 100.0)
        == "inside_against"
    )
    assert (
        _quarter_state(base | {"run_h": None, "run_l": None}, False, "down", 99.0) == "inside_with"
    )
    assert (
        _quarter_state(base | {"run_h": 105.0, "run_l": 89.0}, False, "down", 1.0)
        == "broken_out_before"
    )
    assert _quarter_state(base | {"run_h": 111.0, "run_l": 95.0}, False, "down", 1.0) == "opposite"


def test_liquid_is_a_median_over_exactly_thirty_days():
    days = [bar(k * DAY, 1, 1, 1, 10.0, v=100_000.0) for k in range(30)]  # 1M notional each
    assert liquid(days) is True  # exactly on the floor counts
    assert liquid(days[:29]) is False  # fewer than 30 closed days
    spiky = [bar(k * DAY, 1, 1, 1, 10.0, v=(1e9 if k < 14 else 0.0)) for k in range(30)]
    assert liquid(spiky) is False  # the median is zero even though the mean is huge


def test_outside_day_counts_two_events_and_one_day():  # audit F8
    t0 = ms(2026, 9, 21)
    daily = [bar(t0 + k * DAY, 100, 102, 98, 101) for k in range(14)]
    daily.append(bar(t0 + 14 * DAY, 101, 101.5, 99, 100))  # Monday inside
    daily.append(
        bar(t0 + 15 * DAY, 100, 104, 96, 97)
    )  # Tuesday takes both sides of Monday + the week
    res = analyze_coin(daily)
    assert res["agg"]["rank"][("up", 2)] == 1 and res["agg"]["rank"][("down", 2)] == 1
    assert res["agg"]["break_days"] == 1 and res["agg"]["rank2plus_days"] == 1
    assert res["agg"]["days"] == 15
