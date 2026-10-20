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
