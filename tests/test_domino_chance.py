"""Hand-vector tests for the TVB-37 chance comparison (analysis/domino/chance.py).

Bars here are hand-made vectors for the walker, the horizons and the class logic, not market data.
"""

from datetime import datetime, timezone

import pytest

from analysis.domino.census import DAY, _context, aggregate
from analysis.domino.chance import (
    HORIZONS,
    coin_units,
    diff_interval,
    horizon_ends,
    next_bar,
    stack_class,
    venue_era,
    walk,
    wilson,
)


def ms(y, m, d):
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1000)


def bar(t, o, h, l, c, v=1000.0):
    return {"t": t, "o": o, "h": h, "l": l, "c": c, "v": v}


def flat(t0, n, h=102.0, l=98.0):
    return [bar(t0 + k * DAY, 100.0, h, l, 101.0) for k in range(n)]


def test_walker_target_on_entry_day_and_pessimistic_same_day_stop():
    t0 = ms(2026, 9, 21)
    daily = flat(t0, 6)
    daily[2] = bar(
        t0 + 2 * DAY, 100.0, 103.0, 99.0, 102.5
    )  # entry day: target 102 touched, stop 98 not
    ends = {1: 3, 3: 5, 5: None}
    out = walk(daily, 2, "up", 100.0, 98.0, ends)
    assert out["out1"] == "one_r" and out["out3"] == "one_r" and out["out5"] == "censored"
    assert out["mfe1"] == pytest.approx(1.5) and out["mae1"] == pytest.approx(1.0)
    assert out["mfe5"] is None
    daily[2] = bar(t0 + 2 * DAY, 100.0, 103.0, 97.0, 102.5)  # both touched the same day = stop
    out = walk(daily, 2, "up", 100.0, 98.0, ends)
    assert out["out1"] == "stop" and out["out3"] == "stop"


def test_walker_stop_on_day_two_and_neither_inside_the_short_horizon():
    t0 = ms(2026, 9, 21)
    daily = [
        bar(t0, 100, 101.0, 99.0, 100.5),  # entry day: nothing
        bar(t0 + DAY, 100, 101.5, 99.0, 100.5),  # day 1: nothing
        bar(t0 + 2 * DAY, 100, 101.0, 97.9, 98.0),  # day 2: stop 98 touched
        bar(
            t0 + 3 * DAY, 98, 105.0, 97.0, 104.0
        ),  # day 3: target later is irrelevant, trade is out
    ]
    ends = {1: 1, 3: 3, 5: None}
    out = walk(daily, 0, "up", 100.0, 98.0, ends)
    assert out["out1"] == "neither" and out["out3"] == "stop" and out["out5"] == "censored"
    # short mirror: level 100, stop 102, target 98
    daily_s = [
        bar(t0, 100, 101.0, 99.0, 99.5),
        bar(t0 + DAY, 99.5, 100.5, 97.9, 98.0),  # target 98 touched, stop 102 not
    ]
    out = walk(daily_s, 0, "down", 100.0, 102.0, {1: 1, 3: None, 5: None})
    assert out["out1"] == "one_r" and out["mfe1"] == pytest.approx(1.05)


def test_horizons_for_weekly_units_and_censoring():
    t0 = ms(2026, 9, 21)  # Monday
    daily = flat(t0, 7 * 3 + 2)  # three full weeks and two days of a fourth
    buckets = {tf: aggregate(daily, tf) for tf in ("W", "M", "Q")}
    bucket_of = {
        tf: {di: b for b, bk in enumerate(buckets[tf]) for di in bk["days"]} for tf in ("W", "M")
    }
    i = 8  # Tuesday of week 2
    ends = horizon_ends("W", i, daily, buckets, bucket_of)
    assert ends[1] == 20  # last day (Sunday) of week 3
    assert ends[3] is None and ends[5] is None  # the data ends first
    ends_d = horizon_ends("D", 20, daily, buckets, bucket_of)
    assert ends_d == {1: 21, 3: None, 5: None}


def test_stack_class_daily_and_weekly_units():
    shared = {"W": True, "M": False, "Q": False}
    assert stack_class("D", "up", {"D": 100.0}, shared) == ("plain", 0.0, "D")
    assert stack_class("D", "up", {"D": 100.0, "W": 100.0}, shared)[0] == "exact_shared"
    assert (
        stack_class("D", "up", {"D": 100.0, "W": 100.0}, {"W": False, "M": False, "Q": False})[0]
        == "exact_plain"
    )
    cls, gap, tfs = stack_class("D", "up", {"D": 100.0, "W": 100.25}, shared)
    assert (cls, tfs) == ("near", "D+W") and gap == pytest.approx(0.25)
    assert stack_class("D", "up", {"D": 100.0, "W": 100.0, "M": 100.9}, shared)[0] == "within1"
    assert (
        stack_class("D", "down", {"D": 100.0, "W": 98.0}, shared)[0] == "spread"
    )  # 2% beyond, short side
    # weekly unit: its own level against yesterday's
    assert stack_class("W", "up", {"D": 100.0, "W": 100.1}, shared)[0] == "near"
    assert stack_class("W", "up", {"D": 100.0, "W": 100.0}, shared)[0] == "exact_shared"
    with pytest.raises(AssertionError):
        stack_class(
            "D", "up", {"D": 100.0, "W": 99.0}, shared
        )  # a higher level short of the daily one


def test_next_bar_types_for_daily_units():
    t0 = ms(2026, 9, 21)
    entry = bar(t0, 100, 102, 98, 101)
    daily = [entry, bar(t0 + DAY, 101, 103, 99, 102)]
    assert next_bar("D", 0, daily, {}, {}, "up") == "with"
    assert next_bar("D", 0, daily, {}, {}, "down") == "against"
    daily[1] = bar(t0 + DAY, 101, 101.5, 98.5, 101)
    assert next_bar("D", 0, daily, {}, {}, "up") == "inside"
    daily[1] = bar(t0 + DAY, 101, 103, 97, 101)
    assert next_bar("D", 0, daily, {}, {}, "up") == "outside"
    assert next_bar("D", 1, daily, {}, {}, "up") == "n/a"


def test_intervals():
    lo, hi = wilson(50, 100)
    assert lo == pytest.approx(0.404, abs=0.002) and hi == pytest.approx(0.596, abs=0.002)
    d, lo, hi = diff_interval(60, 100, 50, 100)
    assert (
        d == pytest.approx(0.10)
        and lo < 0.10 < hi
        and hi - lo == pytest.approx(2 * 1.96 * 0.0700, abs=0.002)
    )
    assert all(x != x for x in wilson(0, 0))  # nan, nan


def test_venue_era_drops_the_zero_volume_prefix():
    t0 = ms(2026, 9, 21)
    daily = [bar(t0 + k * DAY, 100, 101, 99, 100, v=(0.0 if k < 3 else 5.0)) for k in range(6)]
    assert [d["t"] for d in venue_era(daily)] == [t0 + k * DAY for k in range(3, 6)]
    assert venue_era([bar(t0, 1, 1, 1, 1, v=0.0)]) == []


def test_coin_units_end_to_end_on_the_monday_exact_stack():
    # the census vector: two flat weeks, Sunday makes the weekly high at 105, Monday breaks it
    t0 = ms(2026, 9, 21)
    daily = flat(t0, 7) + flat(t0 + 7 * DAY, 6)
    daily.append(bar(t0 + 13 * DAY, 101, 105, 100, 104.5))  # Sunday 10-04
    daily.append(bar(t0 + 14 * DAY, 104.5, 106, 103, 105.5))  # Monday 10-05: D + W at 105
    daily.append(
        bar(t0 + 15 * DAY, 105.5, 112, 105, 111)
    )  # Tuesday: one R (110) hit, stop (100) not
    daily += [
        bar(t0 + 16 * DAY + k * DAY, 111, 112, 110, 111) for k in range(13)
    ]  # quiet through the whole next week, plus one day of the week after
    units, counts = coin_units({"coin": "T", "dex": "main", "liquid": True}, daily)
    mon = [u for u in units if u["date"] == "2026-10-05" and u["direction"] == "up"]
    assert sorted(u["tf"] for u in mon) == ["D", "W"]
    d = next(u for u in mon if u["tf"] == "D")
    w = next(u for u in mon if u["tf"] == "W")
    assert d["cls"] == "exact_shared" and d["stack"] == "D+W" and d["kind"] == "continuation"
    assert d["level"] == 105 and d["stop"] == 100 and d["r_pct"] == pytest.approx(100 * 5 / 105)
    assert d["out1"] == "one_r" and d["out3"] == "one_r" and d["out5"] == "one_r"
    assert d["next_bar"] == "with"
    assert w["cls"] == "exact_shared" and w["level"] == 105 and w["stop"] == 98  # last week's low
    assert w["out1"] == "one_r"  # 105 + 7 = 112 touched on the Tuesday, inside the next week
    assert w["out3"] == "censored"  # three weeks out, the data ends
    assert w["next_bar"] == "inside"  # the quiet week sits inside the entry week's 100..112
    # the variant stop for the daily unit = last week's low (98), a different R
    assert d["v_r_pct"] == pytest.approx(100 * 7 / 105) and d["vout1"] == "one_r"
    for u in units:
        for n in HORIZONS:
            assert u[f"out{n}"] in ("one_r", "stop", "neither", "censored")
    assert counts["nesting_violation"] == 0
    ctx = _context(daily, {tf: aggregate(daily, tf) for tf in ("W", "M", "Q")})
    assert ctx["W"][14]["is_first_day"] is True
    assert d["cls_la"] == "exact_shared" and d["stop0"] is False


def test_entry_time_class_does_not_look_at_whether_the_level_broke_today():  # amendment A1
    # two flat weeks (high 102), then a Monday whose daily level sits 0.1% under the weekly level
    t0 = ms(2026, 9, 21)
    daily = flat(t0, 13)
    daily.append(bar(t0 + 13 * DAY, 101, 101.898, 99, 101.5))  # Sunday: high 0.1% under 102
    daily.append(bar(t0 + 14 * DAY, 101.5, 101.95, 100.5, 101.9))  # Monday: breaks 101.898, NOT 102
    daily += flat(t0 + 15 * DAY, 8, h=101.9, l=100.0)
    units, _ = coin_units({"coin": "T", "dex": "main", "liquid": True}, daily)
    mon = [u for u in units if u["date"] == "2026-10-05" and u["direction"] == "up"]
    assert [u["tf"] for u in mon] == ["D"]  # the week did not break
    d = mon[0]
    assert (
        d["cls"] == "near"
        and d["near_tf"] == "W"
        and d["gap_pct"] == pytest.approx(100 * 0.102 / 101.898, abs=1e-6)
    )
    assert d["cls_la"] == "plain" and d["stack"] == "D"  # the look-ahead version called it plain
    # a Monday with the weekly level 2% away is PLAIN at entry time even if the day later takes it
    daily2 = flat(t0, 13)
    daily2.append(bar(t0 + 13 * DAY, 100, 100.0, 99, 99.5))  # Sunday high 100, weekly high 102
    daily2.append(
        bar(t0 + 14 * DAY, 99.5, 103, 97.0, 102.5)
    )  # Monday runs through both, and the stop
    daily2 += flat(t0 + 15 * DAY, 8, h=102.0, l=101.0)
    units2, _ = coin_units({"coin": "T", "dex": "main", "liquid": True}, daily2)
    d2 = next(
        u for u in units2 if u["date"] == "2026-10-05" and u["tf"] == "D" and u["direction"] == "up"
    )
    assert d2["cls"] == "plain" and d2["cls_la"] == "spread" and d2["stack"] == "D+W"
    assert (
        d2["stop0"] is True and d2["out1"] == "stop"
    )  # 97 < 99 traded on the entry day: pessimistic
