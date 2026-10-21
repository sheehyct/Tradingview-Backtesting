"""Hand-vector tests for analysis/strat_ml/events.py (no network; synthetic hourly bars)."""

import numpy as np
import pandas as pd
import pytest

from analysis.domino.census import DAY, HOUR, classify
from analysis.strat_ml import events as ev


def hours(
    day_bars: list[tuple[float, float, float, float]], start_day: int = 19000
) -> pd.DataFrame:
    """Build 24 flat-ish hourly bars per day from daily (o, h, l, c): the high prints in hour 10,
    the low in hour 14, the open in hour 0 and the close in hour 23."""
    rows = []
    for di, (o, h, l, c) in enumerate(day_bars):  # noqa: E741
        base = (start_day + di) * DAY
        for k in range(24):
            price = o + (c - o) * k / 23
            hi = lo = price
            if k == 10:
                hi = h
            if k == 14:
                lo = l
            rows.append((base + k * HOUR, price, max(hi, price), min(lo, price), price, 1.0, 1.0))
    return pd.DataFrame(rows, columns=["t", "o", "h", "l", "c", "v", "qv"])


def test_daily_from_hourly_matches_input():
    bars = [(10, 12, 9, 11), (11, 13, 10, 12), (12, 12.5, 10.5, 11)]
    d = ev.daily_from_hourly(hours(bars))
    assert len(d) == 3
    assert list(d["h"]) == [12, 13, 12.5] and list(d["l"]) == [9, 10, 10.5]
    assert list(d["hours"]) == [24, 24, 24]


def test_partial_first_day_dropped():
    hf = hours([(10, 12, 9, 11), (11, 13, 10, 12)]).iloc[5:]  # first day starts at hour 5
    d = ev.daily_from_hourly(hf)
    assert len(d) == 1 and d["t"].iloc[0] == 19001 * DAY


def test_to_ms_is_resolution_proof():
    s = pd.Series(pd.to_datetime([1577836800000, 1577840400000], unit="ms", utc=True))
    assert list(ev.to_ms(s)) == [1577836800000, 1577840400000]
    assert list(ev.to_ms(s.astype("datetime64[ns, UTC]"))) == [1577836800000, 1577840400000]


def test_types_match_census_classifier():
    rng = np.random.default_rng(1)
    h = 100 + rng.normal(size=50).cumsum()
    l = h - rng.uniform(0.1, 3, size=50)  # noqa: E741
    got = ev.types_of(h, l)
    assert got[0] is None
    for i in range(1, 50):
        assert got[i] == classify({"h": h[i], "l": l[i]}, {"h": h[i - 1], "l": l[i - 1]})


def test_pattern_names_follow_the_router():
    red3 = {"o": 10, "h": 12, "l": 8, "c": 9}
    green3 = {"o": 9, "h": 12, "l": 8, "c": 11}
    assert ev.pattern_name("2D", "2U", "up", None) == ("2-2 reversal", "reversal")
    assert ev.pattern_name("2D", "1", "up", None) == ("1-2-2 rev strat", "reversal")
    assert ev.pattern_name("2D", "3", "up", red3) == ("3-2-2 reversal", "reversal")
    assert ev.pattern_name("2U", "2U", "up", None) == ("2-2 continuation", "continuation")
    assert ev.pattern_name("2U", "2D", "down", None) == ("2-2 reversal", "reversal")
    assert ev.pattern_name("1", "2D", "up", None) == ("2-1-2 reversal", "inside")
    assert ev.pattern_name("1", "2U", "up", None) == ("2-1-2 continuation", "inside")
    assert ev.pattern_name("1", "3", "up", red3) == ("3-1-2 reversal", "inside")
    assert ev.pattern_name("1", "3", "up", green3) == ("3-1-2 continuation", "inside")
    assert ev.pattern_name("1", "1", "down", None) == ("1-1-2 stacked inside", "inside")
    assert ev.pattern_name("3", "2U", "down", None) == ("3-2 outside break", "outside")


def test_magnitude_and_ladder():
    bar2 = {"o": 10, "h": 15, "l": 9, "c": 14}
    # reversal: the far wick of bar 0 (the bar before the setup bar)
    assert ev.magnitude("2-2 reversal", "reversal", "up", 12.0, bar2, []) == (15, "bar0_wick")
    # bar 0's wick not beyond the level = zero magnitude
    assert ev.magnitude("2-2 reversal", "reversal", "up", 15.0, bar2, []) == (
        None,
        "zero_magnitude",
    )
    # inside break against a 2: the anchor; with-trend inside: the ladder
    assert ev.magnitude("2-1-2 reversal", "inside", "down", 10.0, bar2, [])[0] == 9
    rungs = ev.ladder_rungs("up", 12.0, {"W": (13.0, 12.5), "M": (20.0, 12.5)})
    assert rungs == [(13.0, "W"), (20.0, "M")]
    assert ev.magnitude("2-1-2 continuation", "inside", "up", 12.0, bar2, rungs) == (
        13.0,
        "ladder_W",
    )
    assert ev.magnitude("2-2 continuation", "continuation", "up", 12.0, bar2, []) == (
        None,
        "no_rung",
    )
    # a rung already broken in the partial bar is not a rung; a level not beyond L is not a rung
    assert ev.ladder_rungs("up", 12.0, {"W": (13.0, 13.5), "M": (11.0, 10.0)}) == []


def test_one_reversal_event_end_to_end():
    # day0 ref, day1 2U (bar before setup), day2 2D setup (red), day3 breaks day2's high in hour 10
    # then the walk: day4 reaches bar0's high (target) in hour 10; stop (day2 low) never touched.
    bars = [
        (10.0, 12.0, 9.0, 11.0),
        (11.0, 14.0, 10.0, 13.0),  # 2U, bar 0: target wick = 14
        (13.0, 13.5, 9.5, 11.0),  # 2D setup: level 13.5 (long), stop 9.5, R = 4
        (11.0, 13.8, 11.0, 13.0),  # trigger day: breaks 13.5 at hour 10
        (13.0, 14.5, 12.5, 14.0),  # target 14 touched at hour 10
    ] + [(14.0, 14.2, 13.8, 14.0)] * 12
    df, drops = ev.symbol_events("TESTUSDT", hours(bars))
    longs = df[(df["direction"] == "long") & (df["day"] == 19003 * DAY)]
    assert len(longs) == 1
    e = longs.iloc[0]
    assert e["pattern"] == "2-2 reversal" and e["sequence"] == "2U-2D-2U"
    assert e["level"] == 13.5 and e["stop"] == 9.5 and e["r"] == 4.0
    assert e["t1"] == 14.0 and e["t1_source"] == "bar0_wick"
    assert e["hours_since_daily_open"] == 10
    assert e["first_touch"] == "target" and e["touch_hours"] == 24 and not e["ambiguous"]
    assert e["r_managed_1"] == pytest.approx((14.0 - 13.5) / 4.0)
    assert e["r_managed_10"] == pytest.approx((14.0 - 13.5) / 4.0)
    assert e["mfe_r_1"] == pytest.approx((14.5 - 13.5) / 4.0)
    assert e["mae_r_1"] == pytest.approx((13.5 - 11.0) / 4.0)
    assert not e["censored"]
    # the excursion clock: +0.25R (1.0 pts) first at day 4 hour 10 = 24 bars after entry.
    # Against: the trigger hour's own low (11.87 = 0.41R) counts at hour 0 (pessimistic, the
    # low may precede the break); 0.5R came at day 3 hour 14 (low 11.0 = 0.625R), 4 bars in
    assert e["h_fav_025"] == 24 and e["h_adv_025"] == 0 and e["h_adv_05"] == 4
    assert np.isnan(e["h_adv_1"]) and e["first_excursion"] == "adv"
    assert e["mfe_r_24h"] == pytest.approx((13.8 - 13.5) / 4.0)  # day 4 hour 10 is bar 24, outside
    assert e["mfe_r_48h"] == pytest.approx((14.5 - 13.5) / 4.0)
    assert e["mae_r_24h"] == pytest.approx((13.5 - 11.0) / 4.0)
    close_day4_h9 = 13.0 + 1.0 * 9 / 23
    assert e["r_close_24h"] == pytest.approx((close_day4_h9 - 13.5) / 4.0)
    # the short side of the same trigger day never fired (day3 low 11.0 is not below day2 low 10.5)
    assert (
        not (df["direction"] == "short").any()
        or (df[df["direction"] == "short"]["day"] != 19003 * DAY).all()
    )


def test_stop_first_and_ambiguity_and_censoring():
    bars = [
        (10.0, 12.0, 9.0, 11.0),
        (11.0, 14.0, 10.0, 13.0),
        (13.0, 13.5, 12.0, 12.5),  # setup 2D-ish? h 13.5 < 14 and l 12 > 10 -> Type 1 (inside)
        (
            12.5,
            13.6,
            11.9,
            12.0,
        ),  # trigger day: breaks 13.5 (hour 10) AND 12.0 (hour 14): both sides
        (
            12.0,
            12.2,
            11.0,
            11.5,
        ),  # long: stop 12.0 touched hour 14 of day 4 ... but already day3 h14
    ]
    df, _ = ev.symbol_events("TESTUSDT", hours(bars))
    day3 = df[df["day"] == 19003 * DAY]
    assert set(day3["direction"]) == {"long", "short"}
    assert day3["opposite_also_triggered"].all()
    lng = day3[day3["direction"] == "long"].iloc[0]
    assert lng["pattern"] == "2-1-2 continuation"  # bar0 2U with the break, inside setup
    # the long's stop (12.0) is touched on the trigger day at hour 14, 4 hours after entry
    assert lng["first_touch"] == "stop" and lng["touch_hours"] == 4
    assert lng["r_managed_1"] == -1.0
    assert lng["censored"]  # only 2 days follow the trigger: horizon 10 cannot complete
    assert np.isnan(lng["r_managed_10"])
    assert not np.isnan(lng["r_managed_1"])


def test_zero_volume_hours_do_not_touch():
    bars = [
        (10.0, 12.0, 9.0, 11.0),
        (11.0, 14.0, 10.0, 13.0),
        (13.0, 13.5, 9.5, 11.0),
        (11.0, 13.8, 11.0, 13.0),
        (13.0, 14.5, 12.5, 14.0),
    ] + [(14.0, 14.2, 13.8, 14.0)] * 12
    hf = hours(bars)
    # kill the volume of day 4 (where the target would print): the touch must move or vanish
    hf.loc[(hf["t"] // DAY) == 19004, "v"] = 0.0
    df, _ = ev.symbol_events("TESTUSDT", hf)
    e = df[(df["direction"] == "long") & (df["day"] == 19003 * DAY)].iloc[0]
    # with volume the target prints at +24 h (day 4, hour 10); the flat day 5 opens exactly at
    # the target (equality fills), so the first countable touch is +38 h
    assert e["first_touch"] == "target" and e["touch_hours"] == 38


def test_bar0_stop_for_inside_breaks():
    # day1 is bar 0 (2U, low 10.0); day2 inside (h 13.5 < 14, l 12 > 10); day3 breaks 13.5 up
    bars = [
        (10.0, 12.0, 9.0, 11.0),
        (11.0, 14.0, 10.0, 13.0),
        (13.0, 13.5, 12.0, 12.5),
        (12.5, 13.6, 12.4, 13.0),
        (13.0, 13.2, 12.8, 13.0),
    ] + [(13.0, 13.2, 12.8, 13.0)] * 11
    hf = hours(bars)
    a, _ = ev.symbol_events("TESTUSDT", hf)
    b, _ = ev.symbol_events("TESTUSDT", hf, stop_mode="bar0")
    ea = a[(a["direction"] == "long") & (a["day"] == 19003 * DAY)].iloc[0]
    eb = b[(b["direction"] == "long") & (b["day"] == 19003 * DAY)].iloc[0]
    assert ea["pattern"] == eb["pattern"] == "2-1-2 continuation"
    assert ea["stop"] == 12.0 and ea["r"] == 1.5 and ea["stop_src"] == "setup_bar"
    assert eb["stop"] == 10.0 and eb["r"] == 3.5 and eb["stop_src"] == "bar0"
    assert eb["stop_bar_offset"] == 1 and ea["stop_bar_offset"] == 1
    # each file carries the other stop as a ratio
    assert ea["stop_alt_r"] == pytest.approx(3.5 / 1.5)
    assert eb["stop_alt_r"] == pytest.approx(1.5 / 3.5)
    # the setup-bar stop (12.0) is touched on day 4 (low 12.4? no) -> day 3 low 12.4 > 12 ... not hit
    assert ea["first_touch"] == "timeout" and eb["first_touch"] == "timeout"
    assert ea["mae_r_1"] == pytest.approx(eb["mae_r_1"] * 3.5 / 1.5)


def test_bar0_walks_back_through_stacked_inside_bars():
    types = [None, "2U", "1", "1", "1"]  # day1 = bar 0, days 2-4 inside, break on day 5
    assert ev.bar0_index(types, 5) == 1
    assert ev.bar0_index([None, "2D", "2U", "1"], 4) == 2
    assert ev.bar0_index([None, "1", "1"], 3) == 0  # runs out: falls back to the first bar


def test_pivot_ladder_follows_the_pine():
    # daily bars (o, h, l, c); day 6 breaks day 5's high (long). Day 5 = 2D setup, day 4 = 2U bar 0.
    bars = [
        (10, 20, 9, 11),  # 0: an old high at 20 (a far rung)
        (11, 15, 10, 14),  # 1
        (14, 17, 13, 16),  # 2: high 17
        (16, 16.5, 12, 13),  # 3
        (13, 18, 12.5, 17),  # 4: 2U, bar 0 -> anchor = 18
        (17, 17.5, 14, 15),  # 5: 2D setup (h 17.5 < 18, l 14 < 12.5? no: 14 > 12.5 -> inside!)
    ]
    # fix day 5 so it is a real 2D: low below day 4's low
    bars[5] = (17, 17.5, 12, 15)
    daily = [
        {"t": k * DAY, "o": o, "h": h, "l": l, "c": c, "v": 1}
        for k, (o, h, l, c) in enumerate(bars)
    ]
    rungs, src = ev.pivot_ladder(daily, 6, "up", "2D", "2U")
    # anchor 18 (bar 0), then prior highs above 18 walking back: 20 (day 0); 17 / 17.5 are below
    assert rungs == [18, 20] and src == "bar0_wick"
    # with-trend inside break: reclaim = bar 0's far wick even though the trend is with the break
    daily2 = [
        {"t": k * DAY, "o": 10, "h": h, "l": l, "c": 10, "v": 1}
        for k, (h, l) in enumerate([(30, 5), (12, 8), (14, 9), (13, 10)])
    ]
    rungs2, src2 = ev.pivot_ladder(daily2, 4, "up", "1", "2U")
    assert rungs2 == [14, 30] and src2 == "reclaim_bar0"
    # bare continuation: no anchor, ladder from the trigger
    rungs3, src3 = ev.pivot_ladder(daily2, 3, "up", "2U", "2U")
    assert src3 == "trigger" and rungs3 == [30]


def test_pivot_outcomes_in_the_row():
    bars = [
        (10.0, 12.0, 9.0, 11.0),
        (11.0, 14.0, 10.0, 13.0),  # bar 0, anchor 14
        (13.0, 13.5, 9.5, 11.0),  # 2D setup
        (11.0, 13.8, 11.0, 13.0),  # trigger day
        (13.0, 14.5, 12.5, 14.0),  # rung 1 (14) reached at hour 10 of day 4 = +24 h
    ] + [(14.0, 14.2, 13.8, 14.0)] * 12
    df, _ = ev.symbol_events("TESTUSDT", hours(bars))
    e = df[(df["direction"] == "long") & (df["day"] == 19003 * DAY)].iloc[0]
    assert e["pivot_src"] == "bar0_wick" and e["pivot_t1"] == 14.0 and e["pivot_rungs"] == 1
    assert e["pivot_reached_10"] == 1 and e["h_rung1"] == 24 and np.isnan(e["h_rung2"])
    assert e["pivot_first_touch"] == "target"
    assert e["r_managed_pivot_10"] == pytest.approx(0.5 / 4.0)


def test_session_labels_and_bars():
    # 2026-07-01 (EDT, UTC-4) is a Wednesday: local 09:00 = 13:00 UTC
    base = int(pd.Timestamp("2026-07-01", tz="UTC").timestamp() * 1000)
    t = np.array([base + k * HOUR for k in range(48)])
    hour, local_day, label = ev.session_labels(t)
    assert hour[13] == 9 and label[13] == "rth" and label[19] == "rth" and label[20] == "extended"
    assert label[12] == "extended" and label[3] == "overnight" and label[8] == "extended"
    assert local_day[13] == int(pd.Timestamp("2026-07-01").timestamp() * 1000)
    assert local_day[3] == int(
        pd.Timestamp("2026-06-30").timestamp() * 1000
    )  # 03:00 UTC is still June 30 in NY
    hf = pd.DataFrame({"t": t, "o": 1.0, "h": 2.0, "l": 0.5, "c": 1.5, "v": 1.0, "qv": 1.0})
    d, hidx = ev.session_bars(hf, label == "rth", local_day)
    assert len(d) == 2 and list(d["hours"]) == [7, 7] and d["h0"].iloc[0] == 13
    assert hidx[0] == list(range(13, 20)) and hidx[1] == list(range(37, 44))


def test_rth_mode_scans_only_the_session():
    # calendar mode: a break at 03:00 local (overnight) is a trigger; rth mode: it is not
    base = int(pd.Timestamp("2026-07-06", tz="UTC").timestamp() * 1000)  # a Monday
    rows = []
    for day in range(6):
        for k in range(24):
            hi, lo = 10.5, 9.5  # a flat range day after day: every bar an inside / equal bar
            if day == 3 and k == 7:  # 07:00 UTC = 03:00 NY on day 3: a spike above every prior high
                hi = 12.0
            if day == 4 and k == 15:  # day 4, 11:00 NY: an in-session spike
                hi = 13.0
            rows.append((base + (day * 24 + k) * HOUR, 10.0, hi, lo, 10.0, 1.0, 1.0))
    hf = pd.DataFrame(rows, columns=["t", "o", "h", "l", "c", "v", "qv"])
    cal, _ = ev.symbol_events("TESTUSDT", hf)
    rth, _ = ev.symbol_events("TESTUSDT", hf, session="rth")
    cal_days = set(cal[cal["direction"] == "long"]["trigger_session"])
    assert "overnight" in cal_days
    assert (rth["trigger_session"] == "rth").all() and (rth["session_mode"] == "rth").all()


def test_session_aggregate_marks_finished_weeks_complete():
    # five weekday session bars (Mon-Fri 2026-07-06..10) then Monday 07-13: the first week is over
    days = [
        pd.Timestamp(d).timestamp() * 1000
        for d in (
            "2026-07-06",
            "2026-07-07",
            "2026-07-08",
            "2026-07-09",
            "2026-07-10",
            "2026-07-13",
        )
    ]
    daily = [{"t": int(x), "o": 1, "h": 2, "l": 0.5, "c": 1, "v": 1} for x in days]
    cal = ev.session_aggregate(daily, "W", "calendar")
    rth = ev.session_aggregate(daily, "W", "rth")
    assert not cal[0]["complete"]  # the census rule: Saturday and Sunday are missing
    assert rth[0]["complete"] and not rth[1]["complete"]


def test_hourly_gap_inside_the_window_censors_the_horizon():
    bars = [
        (10.0, 12.0, 9.0, 11.0),
        (11.0, 14.0, 10.0, 13.0),
        (13.0, 13.5, 9.5, 11.0),
        (11.0, 13.8, 11.0, 13.0),  # trigger day (day 3)
        (13.0, 14.5, 12.5, 14.0),
    ] + [(14.0, 14.2, 13.8, 14.0)] * 12
    hf = hours(bars)
    full, _ = ev.symbol_events("TESTUSDT", hf)
    e_full = full[(full["direction"] == "long") & (full["day"] == 19003 * DAY)].iloc[0]
    assert not e_full["censored"] and e_full["window_gap_hours"] == 0
    # remove six hours in the middle of day 6: horizons 3, 5, 10 lose prices, horizon 1 does not
    gap = hf[~((hf["t"] // DAY == 19006) & ((hf["t"] // HOUR) % 24).between(10, 15))]
    cut, _ = ev.symbol_events("TESTUSDT", gap)
    e = cut[(cut["direction"] == "long") & (cut["day"] == 19003 * DAY)].iloc[0]
    assert (
        not np.isnan(e["r_managed_1"])
        and np.isnan(e["r_managed_3"])
        and np.isnan(e["r_managed_10"])
    )
    assert e["censored"] and e["window_gap_hours"] == 6
