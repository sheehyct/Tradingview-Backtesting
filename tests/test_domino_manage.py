"""Hand vectors for the TVB-37 product 3 engine (analysis/domino/manage.py), declared in the
prereg (def. 16) before the engine ran on data. Every series is built from daily bars; weeks
start on Monday 00:00 UTC, months on the 1st."""

from datetime import datetime, timezone

import pandas as pd
import pytest

from analysis.domino.census import DAY
from analysis.domino.manage import (
    CAP,
    against,
    beyond,
    cell,
    coin_manage_rows,
    paired,
    share,
    targets,
)


def ms(y, m, d):
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1000)


def bar(t, o, h, l, c, v=1000.0):  # noqa: E741
    return {"t": t, "o": o, "h": h, "l": l, "c": c, "v": v}


def flat(t0, n, h=110.0, l=90.0, o=100.0, c=101.0):  # noqa: E741
    return [bar(t0 + k * DAY, o, h, l, c) for k in range(n)]


def green(t, o=100.0, k=21):
    """k green days that never touch anything far away and never close against the week."""
    return [bar(t + j * DAY, o, o + 0.5, o - 0.2, o + 0.3) for j in range(k)]


META = {"coin": "T", "dex": "main", "liquid": True}
MON = ms(2026, 9, 21)  # a Monday; two flat weeks at 110 / 90 precede every daily vector
TUE = MON + 15 * DAY  # Tuesday 2026-10-06


def unit(daily, date, direction="up", tf="D"):
    rows, _ = coin_manage_rows(META, daily)
    return next(
        r for r in rows if r["date"] == date and r["direction"] == direction and r["tf"] == tf
    )


def test_v1_monday_entry_day_red_is_one_test_and_exits_at_its_own_close():
    daily = flat(MON, 14)
    daily.append(bar(MON + 14 * DAY, 100.5, 111.0, 99.0, 100.0))  # Monday breaks 110, closes red
    daily += green(MON + 15 * DAY)
    u = unit(daily, "2026-10-05")
    assert u["status"] == "exit" and u["exit_k"] == 0 and u["days"] == 0
    assert u["ret_C"] == pytest.approx((100.0 - 110.0) / 110.0 * 100)
    assert u["w_support"] == "with"  # L 110 above the week's open 100.5


def test_v2_tuesday_day_red_week_green_holds_then_both_red_exits_and_v13_stacked_inside():
    daily = flat(MON, 14)
    daily.append(bar(MON + 14 * DAY, 100.0, 101.5, 99.0, 101.0))  # Monday: inside the flat bar
    daily.append(bar(TUE, 101.0, 101.8, 100.0, 100.5))  # Tuesday: breaks 101.5, red, week green
    daily.append(bar(TUE + DAY, 100.5, 101.0, 99.0, 99.5))  # Wednesday: red, week red -> exit
    daily += green(TUE + 2 * DAY, o=99.5)
    u = unit(daily, "2026-10-06")
    assert u["kind"] == "inside" and u["anchor"] == "stacked"  # 1-1-2: no anchor in the two bars
    assert u["t1"] == 110.0 and u["t1_src"] == "W" and u["t2"] is None  # first rung is T1
    assert u["status"] == "exit" and u["exit_k"] == 1
    assert u["ret_C"] == pytest.approx((99.5 - 101.5) / 101.5 * 100)
    assert u["reached1"] is False and u["ret_A"] == u["ret_C"] and u["hit_A"] is False
    assert u["ret_D"] == u["ret_C"] and u["hit_D"] is False  # v14: exit before one R


def _v3_series(exit_day_bar):
    daily = flat(MON, 14)
    daily.append(bar(MON + 14 * DAY, 100.0, 101.5, 99.0, 101.0))
    daily.append(bar(TUE, 101.0, 102.0, 100.5, 101.8))  # entry, green
    daily.append(bar(TUE + DAY, 101.8, 103.0, 101.0, 102.5))  # green
    daily.append(exit_day_bar)  # day 2
    return daily


def test_v3_t1_on_day_two_exit_on_day_four_fills_each_book_as_declared_and_v14_book_d():
    daily = _v3_series(bar(TUE + 2 * DAY, 102.5, 110.5, 102.0, 109.0))  # touches T1 = 110
    daily.append(bar(TUE + 3 * DAY, 109.0, 109.5, 105.0, 106.0))  # red, week green: hold
    daily.append(bar(TUE + 4 * DAY, 106.0, 106.5, 98.0, 99.0))  # red, week red: exit
    daily += green(TUE + 5 * DAY, o=99.0)
    u = unit(daily, "2026-10-06")
    L = 101.5
    assert u["t1_k"] == 2 and u["exit_k"] == 4 and u["reached1"] is True
    assert u["ret_A"] == pytest.approx((110.0 - L) / L * 100) and u["hit_A"] is True
    assert u["t2"] is None and u["ret_B"] == u["ret_C"]  # no T2: book B is the exit
    assert u["ret_C"] == pytest.approx((99.0 - L) / L * 100)
    assert u["one_r_k"] == 2 and u["ret_D"] == pytest.approx(2.5 / L * 100) and u["hit_D"]
    assert u["mfe_x"] == pytest.approx((110.5 - L) / L * 100)
    assert u["mae_x"] == pytest.approx((L - 98.0) / L * 100)


def test_v4_t1_touch_and_exit_on_the_same_day_fill_a_at_t1_and_b_at_the_close():
    daily = _v3_series(bar(TUE + 2 * DAY, 102.5, 110.5, 98.0, 99.0))  # touch, red, week red
    daily += green(TUE + 3 * DAY, o=99.0)
    u = unit(daily, "2026-10-06")
    L = 101.5
    assert u["t1_k"] == 2 and u["exit_k"] == 2 and u["reached1"] is True
    assert u["ret_A"] == pytest.approx((110.0 - L) / L * 100)
    assert u["ret_B"] == pytest.approx((99.0 - L) / L * 100)


def test_v5_reversal_whose_anchor_wick_sits_at_the_trigger_has_no_t1():
    daily = flat(MON, 14)
    daily.append(
        bar(MON + 14 * DAY, 100.0, 110.0, 89.0, 95.0)
    )  # Monday: 2D (equal high, lower low)
    daily.append(bar(TUE, 95.0, 111.0, 94.0, 108.0))  # Tuesday breaks 110: 2-2 reversal
    daily += green(TUE + DAY, o=108.0)
    u = unit(daily, "2026-10-06")
    assert u["kind"] == "reversal" and u["anchor"] == "zero" and u["t1"] is None
    assert u["t1_src"] == "zero" and u["ladder_len"] == 0
    assert u["status"] in ("exit", "open") and u["ret_A"] == u["ret_C"]  # exit-only in every book


def _month_series():
    """From 2026-09-01: September flat at 110 / 90 with one 115 high, so the monthly level is
    beyond the weekly one."""
    t0 = ms(2026, 9, 1)
    daily = flat(t0, 30)
    daily[9] = bar(t0 + 9 * DAY, 100.0, 115.0, 90.0, 101.0)  # Sep 10: the month's high
    return t0, daily


def test_v6_exact_weekly_stack_is_not_a_rung_and_the_monthly_level_is_t1():
    t0, daily = _month_series()  # ends Sep 30 (Wednesday)
    oct1 = ms(2026, 10, 1)
    daily.append(bar(oct1, 100.0, 108.0, 95.0, 100.0))  # Thu: inside
    daily.append(bar(oct1 + DAY, 100.0, 109.0, 96.0, 105.0))  # Fri: 2U
    daily.append(bar(oct1 + 2 * DAY, 105.0, 109.5, 97.0, 106.0))  # Sat: 2U
    daily.append(bar(oct1 + 3 * DAY, 106.0, 110.0, 98.0, 107.0))  # Sun: 2U, high = last week's 110
    daily.append(bar(oct1 + 4 * DAY, 107.0, 112.0, 106.0, 111.0))  # Mon Oct 5: breaks 110
    daily += green(oct1 + 5 * DAY, o=111.0)
    u = unit(daily, "2026-10-05")
    assert u["kind"] == "continuation" and u["cls"] == "exact_shared"
    assert u["t1"] == 115.0 and u["t1_src"] == "M" and u["t2"] is None  # 110 is L, not a rung


def test_v7_a_rung_at_t1_is_skipped_and_t2_is_strictly_beyond():
    t0, daily = _month_series()
    oct1 = ms(2026, 10, 1)
    daily.append(bar(oct1, 100.0, 108.0, 95.0, 100.0))  # Thu
    daily.append(bar(oct1 + DAY, 100.0, 109.0, 96.0, 105.0))  # Fri
    daily.append(
        bar(oct1 + 2 * DAY, 105.0, 112.0, 90.0, 106.0)
    )  # Sat: X, high 112 = the week's high
    daily.append(bar(oct1 + 3 * DAY, 106.0, 105.0, 85.0, 95.0))  # Sun: 2D (low 85 < 90)
    daily.append(bar(oct1 + 4 * DAY, 95.0, 106.0, 94.0, 104.0))  # Mon: breaks 105, 2-2 reversal
    daily += green(oct1 + 5 * DAY, o=104.0)
    u = unit(daily, "2026-10-05")
    assert u["kind"] == "reversal" and u["t1"] == 112.0 and u["t1_src"] == "anchor"
    assert u["t2"] == 115.0 and u["t2_src"] == "M" and u["t3"] is None  # weekly 112 == T1: skipped


def test_v8_open_at_the_cap_is_marked_at_day_20_and_v10_equal_closes_are_not_against():
    daily = flat(MON, 14)
    daily.append(
        bar(MON + 14 * DAY, 100.0, 111.0, 99.0, 100.0)
    )  # Monday: breaks 110, close == open
    daily += green(MON + 15 * DAY, o=100.0, k=25)
    u = unit(daily, "2026-10-05")
    assert u["exit_k"] is None and u["status"] == "open" and u["days"] == CAP
    mark = daily[14 + CAP]["c"]
    assert u["ret_C"] == pytest.approx((mark - 110.0) / 110.0 * 100)
    assert u["ret_A"] == u["ret_C"]  # T1 never touched: the mark


def test_v9_data_ending_before_exit_and_cap_is_censored():
    daily = flat(MON, 14)
    daily.append(bar(MON + 14 * DAY, 100.5, 111.0, 99.0, 101.0))  # Monday: breaks 110, green
    daily += green(MON + 15 * DAY, o=101.0, k=7)
    u = unit(daily, "2026-10-05")
    assert u["status"] == "censored" and "ret_C" not in u


def test_v11_weekly_unit_daily_clock_exits_midweek_own_clock_at_the_week_close():
    t0 = ms(2026, 9, 1)
    daily = flat(t0, 30)  # September flat 110 / 90 (month open 100)
    oct1 = ms(2026, 10, 1)
    daily += [bar(oct1 + k * DAY, 100.0, 105.0, 95.0, 100.0) for k in range(4)]  # Thu..Sun inside
    daily.append(bar(oct1 + 4 * DAY, 100.0, 104.0, 96.0, 102.0))  # Mon Oct 5: week opens 100
    daily.append(bar(oct1 + 5 * DAY, 102.0, 111.0, 101.0, 108.0))  # Tue: breaks weekly 110, green
    daily.append(bar(oct1 + 6 * DAY, 108.0, 109.0, 97.0, 98.0))  # Wed: red, week red -> daily exit
    daily += [
        bar(oct1 + 7 * DAY + k * DAY, 98.0, 98.5, 96.5, 97.0) for k in range(4)
    ]  # Thu..Sun red
    daily += [bar(oct1 + 11 * DAY + k * DAY, 97.0, 98.0, 96.0, 97.0) for k in range(160)]  # flat
    u = unit(daily, "2026-10-06", tf="W")
    assert u["level"] == 110.0 and u["status"] == "exit" and u["exit_k"] == 1
    assert u["ret_C"] == pytest.approx((98.0 - 110.0) / 110.0 * 100)
    assert u["status_long"] == "exit" and u["days_long"] == 1
    assert u["status_own"] == "exit" and u["days_own"] == 5  # Sunday Oct 11: week red, month red
    assert u["ret_C_own"] == pytest.approx((97.0 - 110.0) / 110.0 * 100)


def test_v12_measured_move_is_the_two_bar_range_from_the_trigger():
    daily = flat(MON, 12)
    daily.append(bar(MON + 12 * DAY, 100.0, 108.0, 95.0, 105.0))  # Sat: inside
    daily.append(bar(MON + 13 * DAY, 105.0, 109.0, 96.0, 107.0))  # Sun: 2U
    daily.append(bar(MON + 14 * DAY, 107.0, 109.5, 106.0, 109.0))  # Mon: breaks 109, continuation
    daily += green(MON + 15 * DAY, o=109.0)
    u = unit(daily, "2026-10-05")
    assert u["kind"] == "continuation" and u["t1"] == 110.0 and u["t1_src"] == "W"
    assert u["mm_t1"] == pytest.approx(109.0 + (109.0 - 95.0))
    # the with-trend inside break uses X's range
    daily = flat(MON, 12)
    daily.append(bar(MON + 12 * DAY, 100.0, 111.0, 95.0, 108.0))  # Sat: 2U (X)
    daily.append(bar(MON + 13 * DAY, 108.0, 108.0, 97.0, 105.0))  # Sun: inside
    daily.append(bar(MON + 14 * DAY, 105.0, 108.5, 104.0, 108.0))  # Mon: breaks 108
    daily += green(MON + 15 * DAY, o=108.0)
    u = unit(daily, "2026-10-05")
    assert u["kind"] == "inside" and u["anchor"] == "ladder" and u["t1"] == 111.0
    assert u["mm_t1"] == pytest.approx(108.0 + (111.0 - 95.0))


def test_v15_week_side_at_entry_equality_is_against():
    daily = flat(MON, 14)
    daily.append(bar(MON + 14 * DAY, 110.0, 111.0, 105.0, 108.0))  # Monday opens AT the level
    daily += green(MON + 15 * DAY, o=108.0)
    u = unit(daily, "2026-10-05")
    assert u["level"] == 110.0 and u["w_support"] == "against"


def test_target_rules_direct():
    rungs = [(120.0, "W"), (130.0, "M")]
    ref2d = {"h": 115.0, "l": 90.0}
    t = targets("reversal", "up", 105.0, ref2d, "2D", rungs)
    assert (t["t1"], t["t1_src"], t["t2"], t["t3"]) == (115.0, "anchor", 120.0, 130.0)
    t = targets("inside", "up", 105.0, ref2d, "2D", rungs)  # 2d-1-2u: X's high
    assert (t["t1"], t["anchor"]) == (115.0, "anchor")
    t = targets("inside", "up", 105.0, ref2d, "3", rungs)  # 3-1-2: the 3's extreme
    assert (t["t1"], t["anchor"]) == (115.0, "anchor")
    t = targets("inside", "up", 105.0, ref2d, "2U", rungs)  # with-trend inside: the ladder
    assert (t["t1"], t["t1_src"], t["t2"], t["t3"]) == (120.0, "W", 130.0, None)
    t = targets("outside", "down", 105.0, ref2d, "2U", [(95.0, "W")])
    assert (t["t1"], t["t2"]) == (95.0, None)
    t = targets("continuation", "up", 105.0, None, None, [])
    assert t["t1"] is None and t["t1_src"] == "none"
    t = targets("reversal", "up", 105.0, None, None, rungs)
    assert t["t1"] is None and t["anchor"] == "unknown"
    assert (
        beyond(101.0, 100.0, "up")
        and not beyond(100.0, 100.0, "up")
        and beyond(99.0, 100.0, "down")
    )
    assert (
        against(99.0, 100.0, "up")
        and not against(100.0, 100.0, "up")
        and against(101.0, 100.0, "down")
    )


def test_cell_bookkeeping_sums_and_subsets():
    base = {
        "date": "2026-01-01",
        "kind": "reversal",
        "r_pct": 2.0,
        "out5": "stop",
        "mfe5": 1.2,
        "stop0": False,
        "t2": None,
        "t3": None,
        "anchor": "anchor",
        "t1_src": "anchor",
        "ceil1": True,
        "ceil2": False,
        "ceil3": False,
        "mfe_x": 1.0,
        "mae_x": 3.0,
        "hit_A": False,
        "hit_B": False,
        "hit_D": False,
        "mm_t1": None,
        "stop_saw": False,
        "later_r": False,
        "level": 100.0,
    }
    rows = [
        dict(
            base,
            t1=110.0,
            status="exit",
            exit_k=0,
            days=0,
            ret_C=-2.0,
            ret_A=-2.0,
            ret_B=-2.0,
            ret_D=-2.0,
            ret_ref=-2.0,
            reached1=False,
            reached2=False,
            reached3=False,
            later1=True,
        ),
        dict(
            base,
            t1=110.0,
            status="exit",
            exit_k=3,
            days=3,
            ret_C=1.0,
            ret_A=4.0,
            ret_B=1.0,
            ret_D=2.0,
            ret_ref=2.0,
            reached1=True,
            reached2=False,
            reached3=False,
            later1=False,
            hit_A=True,
            hit_D=True,
            out5="one_r",
        ),
        dict(
            base,
            t1=110.0,
            status="open",
            exit_k=None,
            days=20,
            ret_C=5.0,
            ret_A=5.0,
            ret_B=5.0,
            ret_D=2.0,
            ret_ref=2.0,
            reached1=False,
            reached2=False,
            reached3=False,
            later1=False,
            hit_D=True,
            out5="one_r",
        ),
        dict(
            base,
            t1=None,
            status="exit",
            exit_k=1,
            days=1,
            ret_C=-1.0,
            ret_A=-1.0,
            ret_B=-1.0,
            ret_D=-1.0,
            ret_ref=-2.0,
            reached1=False,
            reached2=False,
            reached3=False,
            later1=False,
            anchor="zero",
            t1_src="zero",
        ),
        dict(base, t1=110.0, status="censored"),
    ]
    c = cell(pd.DataFrame(rows))
    assert c["units"] == 5 and c["n"] == 4 and c["censored"] == 1
    assert c["reach1"] == {
        "k": 1,
        "n": 3,
        "p": pytest.approx(1 / 3),
        "lo": pytest.approx(c["reach1"]["lo"]),
        "hi": pytest.approx(c["reach1"]["hi"]),
    }
    assert c["died"]["n"] == 1 and c["died"]["entry_day"] == 1.0 and c["died"]["later1"]["k"] == 1
    assert c["books"]["A"]["n"] == 3 and c["book_C_all"]["n"] == 4
    assert c["books"]["A"]["avg_pct"] == pytest.approx((-2.0 + 4.0 + 5.0) / 3)
    assert c["diff"]["D_minus_ref"]["n"] == 3 and c["diff"]["D_minus_ref"]["diff"] == pytest.approx(
        0.0
    )
    assert c["tail"]["mae_gt1"] == 1.0 and c["tail"]["worst_pct"] == -2.0
    s = share(pd.Series([True, False, None]))
    assert s["k"] == 1 and s["n"] == 2  # a null is unknown, not a denominator
    p = paired(pd.Series([1.0, 2.0, 3.0]), pd.Series([0.0, 0.0, 0.0]))
    assert p["diff"] == pytest.approx(2.0) and p["lo"] < 2.0 < p["hi"]
