"""Hand-vector tests for the TVB-37 domino census engine (analysis/domino/census.py).

Bars here are hand-made test vectors for the level logic, not market data.
"""

from datetime import datetime, timezone

from analysis.domino.census import (
    DAY,
    aggregate,
    analyze_coin,
    classify,
    distance_band,
    month_start,
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
    daily = [bar(t0 + k * DAY, 100 + k, 101 + k, 99 + k, 100.5 + k) for k in range(12)]  # Wed .. Sun of next week
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
    daily.append(bar(t3 + DAY, 101, 103, 100, 102.5))  # Tuesday: breaks yesterday's high AND last week's high
    daily.append(bar(t3 + 2 * DAY, 102.5, 104, 101, 103))  # Wednesday: new daily break, week already 2U
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
    daily.append(bar(t1 + 7 * DAY, 104.5, 106, 103, 105.5))  # Monday breaks 105: day and week at one price
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
    assert shape_flags(bar(0, 94.0, 101.0, 91.0, 93.0), "down") == (True, False)  # 2-point wick = 20%


def test_distance_bands():
    assert distance_band([100.0, 100.0])[1] == "exact"
    assert distance_band([100.0, 100.2])[1] == "near"
    assert distance_band([100.0, 100.8])[1] == "within1"
    assert distance_band([100.0, 102.0])[1] == "spread"
