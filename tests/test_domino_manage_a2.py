"""Hand vectors v16-v19 for prereg amendment A2 (the lead's five candidates), declared before the
engine ran on data. Built on the same daily fixtures as tests/test_domino_manage.py; the hourly
vectors add 24 cached hours per day."""

from decimal import Decimal

import pandas as pd
import pytest

from analysis.domino.census import DAY, HOUR
from analysis.domino.manage import (
    TAKER,
    candidates,
    coin_manage_rows,
    hourly_fill,
    hours_by_day,
    walk_hourly,
)
from tests.test_domino_manage import META, MON, TUE, bar, flat, green, unit

L = 101.5  # the v3 entry level: the setup bar's high


def _series(days_after_entry: list[dict]) -> list[dict]:
    daily = flat(MON, 14)
    daily.append(bar(MON + 14 * DAY, 100.0, 101.5, 99.0, 101.0))  # setup bar (Monday)
    daily.append(bar(TUE, 101.0, 102.0, 100.5, 101.8))  # entry day, green, above L
    daily += days_after_entry
    return daily


# ----------------------------------------------------------------------------- v16 under water


def test_v16_red_day_above_the_entry_is_not_under_water_but_a_green_day_under_it_is():
    daily = _series(
        [
            bar(TUE + DAY, 101.8, 103.0, 101.6, 101.7),  # day 1: red candle, still above L
            bar(TUE + 2 * DAY, 101.7, 102.0, 100.0, 100.5),  # day 2: red, under L, week green
            bar(
                TUE + 3 * DAY, 99.0, 99.8, 98.5, 99.5
            ),  # day 3: opened under L, GREEN, under L, week red
        ]
    )
    daily += green(TUE + 4 * DAY, o=99.5)
    u = unit(daily, "2026-10-06")
    # the colour clock: day 2 is the first red day with the week red? week open = 100.0 (Monday)
    # day 2 closed 100.5 > 100.0: week green -> hold; day 3 is green -> hold; so the colour
    # clock does not exit on these three days
    assert u["exit_k"] is None or u["exit_k"] > 3
    # the under-water clock: day 1 is above L (not through); day 2 is through L but the week is
    # green (100.5 > 100.0); day 3 is through L AND the week is red (99.5 < 100.0): exit at 99.5
    assert u["status_u"] == "exit" and u["exit_k_u"] == 3
    assert u["ret_C_u"] == pytest.approx((99.5 - L) / L * 100)
    assert u["days_u"] == 3 and u["mae_u"] == pytest.approx((L - 98.5) / L * 100)
    assert u["hit_A_u"] is False and u["ret_A_u"] == u["ret_C_u"]


def test_v16b_under_water_entry_day_can_exit_and_equality_is_not_through():
    # the entry day itself closes exactly on L with the week red: equality is not through
    daily = flat(MON, 14)
    daily.append(bar(MON + 14 * DAY, 100.0, 101.5, 99.0, 101.0))
    daily.append(bar(TUE, 101.0, 102.0, 99.0, 101.5))  # closes ON L; week open 100 -> green anyway
    daily.append(
        bar(TUE + DAY, 101.5, 101.6, 99.0, 99.2)
    )  # red, under L, week red: both clocks exit
    daily += green(TUE + 2 * DAY, o=99.2)
    u = unit(daily, "2026-10-06")
    assert u["exit_k_u"] == 1 and u["exit_k"] == 1
    assert u["ret_C_u"] == u["ret_C"] == pytest.approx((99.2 - L) / L * 100)


# ----------------------------------------------------------------------------- v17 hourly clock


def hours(daily_bars: list[dict], custom: dict | None = None) -> list[dict]:
    """24 flat hours per daily bar at the day's close, except the days given in `custom`
    (day start -> a full list of 24 (o, h, l, c) tuples)."""
    out = []
    for d in daily_bars:
        spec = (custom or {}).get(d["t"])
        for k in range(24):
            t = d["t"] + k * HOUR
            if spec is None:
                out.append({"t": t, "o": d["c"], "h": d["c"], "l": d["c"], "c": d["c"], "v": 1.0})
            else:
                o, h, lo, c = spec[k]
                out.append({"t": t, "o": o, "h": h, "l": lo, "c": c, "v": 1.0})
    return out


def _entry_day_hours():
    """The entry day (open 101.0, high 102.0 at hour 7, low 100.5 at hour 2, close 101.8):
    hour 5 is the first hour whose high reaches L = 101.5 (the entry hour); hour 6 is a red hour
    while the day is green (hold); hour 7 touches the T1 of the vector."""
    h = [(101.0, 101.2, 100.9, 101.1)] * 24
    h[2] = (101.1, 101.3, 100.5, 100.7)  # the day's low, before the entry hour
    h[5] = (101.1, 101.6, 101.0, 101.55)  # entry hour: high 101.6 >= L; closes green
    h[6] = (101.55, 101.7, 101.4, 101.45)  # red hour but the day is GREEN (101.45 > 101.0): hold
    h[7] = (101.45, 102.0, 101.3, 101.9)  # touches 101.9 target
    for k in range(8, 24):
        h[k] = (101.9, 101.95, 101.7, 101.8)
    return h


def test_v17_entry_hour_touches_and_exit_on_the_hourly_clock():
    daily = _series(
        [
            bar(TUE + DAY, 101.8, 102.2, 100.0, 100.4),  # day 1: red, under the day open
            *green(TUE + 2 * DAY, o=100.4),
        ]
    )
    day1 = [(101.8, 102.0, 101.6, 101.9)] * 24
    day1[3] = (101.9, 102.1, 101.0, 101.2)  # red hour, day red (101.2 < 101.8): EXIT here
    for k in range(4, 24):
        day1[k] = (101.2, 101.3, 100.0, 100.4)
    day1[8] = (101.2, 102.2, 100.0, 100.4)  # the day's high, after the exit hour
    hourly = hours(daily, {TUE: _entry_day_hours(), TUE + DAY: day1})
    by_day = hours_by_day(hourly)
    i = next(k for k, d in enumerate(daily) if d["t"] == TUE)
    prices = {"t1": 101.9, "late": 102.15, "one_r": Decimal("103.0")}
    wh = walk_hourly(hourly, by_day, daily, i, "up", L, prices, i + 20)
    assert wh["status"] == "exit"
    assert wh["entry_hour"] == 5  # hour 2 did not reach 101.5; hour 5 did
    # 102.15 is touched on day 1 at hour 8, AFTER the exit hour: the hourly clock does not fill
    # it, where the daily bar (exit day, "targets are intraday") would have
    assert wh["touch"]["late"] is None
    assert wh["touch"]["t1"] == wh["entry"] + 2  # hour 7 of the entry day
    assert wh["touch"]["one_r"] is None
    assert wh["hours"] == (24 - 5) + 3  # hour 3 of day 1
    assert wh["ret_c"] == pytest.approx((101.2 - L) / L * 100)
    r, hit = hourly_fill(wh, "t1", 101.9, "up", L)
    assert hit and r == pytest.approx((101.9 - L) / L * 100)
    r, hit = hourly_fill(wh, "one_r", Decimal("103.0"), "up", L)
    assert not hit and r == wh["ret_c"]


def test_v17b_hourly_cap_marks_at_the_last_hour_of_day_20_and_censors_when_hours_end():
    daily = _series(list(green(TUE + DAY, o=101.8, k=25)))
    # every hour green and above the day open: no exit ever
    hourly = hours(daily)
    for b in hourly:
        b["o"], b["c"] = b["c"] - 0.1, b["c"]  # green hours
    by_day = hours_by_day(hourly)
    i = next(k for k, d in enumerate(daily) if d["t"] == TUE)
    wh = walk_hourly(hourly, by_day, daily, i, "up", 101.0, {"t1": 150.0}, i + 20)
    # hour 0 of the entry day to hour 23 of day 20
    assert wh["status"] == "open" and wh["hours"] == 20 * 24 + 23 and wh["entry_hour"] == 0
    assert wh["end"] == by_day[daily[i + 20]["t"]][-1]
    # the cap day's hours missing: censored
    short_hourly = [b for b in hourly if b["t"] < daily[i + 20]["t"] + 12 * HOUR]
    wh2 = walk_hourly(short_hourly, hours_by_day(short_hourly), daily, i, "up", 101.0, {}, i + 20)
    assert wh2["status"] == "censored"
    # no hours on the entry day at all: None (outside the window)
    late = [b for b in hourly if b["t"] >= TUE + DAY]
    assert walk_hourly(late, hours_by_day(late), daily, i, "up", 101.0, {}, i + 20) is None


def test_v17c_through_the_engine_hourly_columns_and_headline_rows_unchanged():
    daily = _series(
        [
            bar(TUE + DAY, 101.8, 102.2, 100.0, 100.4),
            *green(TUE + 2 * DAY, o=100.4),
        ]
    )
    rows0, _ = coin_manage_rows(META, daily)
    u0 = next(r for r in rows0 if r["date"] == "2026-10-06" and r["direction"] == "up")
    assert u0["status_h"] is None
    day1 = [(101.8, 102.0, 101.6, 101.9)] * 24
    day1[3] = (101.9, 102.2, 101.0, 101.2)
    for k in range(4, 24):
        day1[k] = (101.2, 101.3, 100.0, 100.4)
    hourly = hours(daily, {TUE: _entry_day_hours(), TUE + DAY: day1})
    rows, counts = coin_manage_rows(META, daily, hourly)
    u = next(r for r in rows if r["date"] == "2026-10-06" and r["direction"] == "up")
    assert u["status_h"] == "exit" and u["entry_h"] == 5 and u["exit_h"] == 22
    assert u["ret_C_h"] == pytest.approx((101.2 - L) / L * 100)
    # the headline columns did not move
    for k in ("ret_C", "ret_A", "ret_D", "exit_k", "status", "t1_k", "status_u", "ret_C_u"):
        assert u[k] == u0[k], k
    assert counts["hourly_exit"] >= 1


# ----------------------------------------------------------------------------- v18 / v19 arithmetic


def _fixture_rows() -> pd.DataFrame:
    base = {
        "tf": "D",
        "cls": "plain",
        "status": "exit",
        "kind": "reversal",
        "t1": 1.0,
        "ret_ref": -1.0,
        "reached1": True,
        "ret_B": 0.0,
        "ret_D": 0.5,
        "ret_D5": 0.5,
        "status_u": "exit",
        "ret_C_u": 0.0,
        "ret_A_u": 0.0,
        "ret_D_u": 0.0,
        "hit_A_u": False,
        "days_u": 2,
        "days": 2,
        "mae_u": 1.0,
        "mae_x": 1.0,
        "r_pct": 2.0,
        "status_h": None,
    }
    rows = [
        dict(base, dex="main", w_support="with", hit_A=True, ret_A=2.0, ret_C=-1.0),
        dict(base, dex="main", w_support="with", hit_A=False, ret_A=-0.5, ret_C=-0.5),
        dict(base, dex="xyz", w_support="against", hit_A=True, ret_A=1.0, ret_C=3.0),
        dict(base, dex="xyz", w_support="against", hit_A=False, ret_A=-2.0, ret_C=-2.0),
    ]
    return pd.DataFrame(rows)


def test_v18_half_at_t1_and_fee_arithmetic():
    c = candidates(_fixture_rows())["reversal"]
    # E = (A + C) / 2 when A hit its target, else C: (0.5, -0.5, 2.0, -2.0) -> mean 0.0
    assert c["half"]["E"]["avg"] == pytest.approx(0.0)
    assert c["half"]["A"]["avg"] == pytest.approx(0.125)
    assert c["half"]["C"]["avg"] == pytest.approx(-0.125)
    assert c["half"]["E_minus_A"]["diff"] == pytest.approx(-0.125)
    # fees: two fills at the dex's rate; main 0.0864 round trip, xyz 0.025
    assert c["fees"]["rt_avg"] == pytest.approx((2 * TAKER["main"] + 2 * TAKER["xyz"]) / 2)
    a = c["fees"]["books"]["A"]
    assert a["net"]["avg"] == pytest.approx(0.125 - (2 * 0.0432 * 2 + 2 * 0.0125 * 2) / 4)
    assert c["fees"]["books"]["E"]["net"]["avg"] == pytest.approx(0.0 - c["fees"]["rt_avg"])


def test_v19_week_side_condition_counts():
    c = candidates(_fixture_rows())["reversal"]
    w = c["week"]
    assert w["with"]["n"] == 2 and w["against"]["n"] == 2
    assert w["with"]["A"]["avg"] == pytest.approx(0.75)
    assert w["against"]["C"]["avg"] == pytest.approx(0.5)
    assert w["with"]["reach1"]["k"] == 2
    # under water on the fixture: every row exits, paired diffs computed on all four
    assert c["under"]["n"] == 4 and c["under"]["C"]["n"] == 4
    assert c["under"]["C"]["diff"] == pytest.approx(0.0 - (-0.125))
    # no hourly rows in the fixture: the hourly block is empty, not an error
    assert c["hourly"]["n"] == 0
