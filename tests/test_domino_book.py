"""Hand-vector tests for the TVB-37 book view and R-matched check (analysis/domino/book.py)."""

from datetime import datetime, timezone

import pandas as pd
import pytest

from analysis.domino.book import book_cell, coin_book_rows, r_matched
from analysis.domino.census import DAY


def ms(y, m, d):
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1000)


def bar(t, o, h, l, c, v=1000.0):
    return {"t": t, "o": o, "h": h, "l": l, "c": c, "v": v}


def flat(t0, n, h=110.0, l=90.0):
    return [bar(t0 + k * DAY, 100.0, h, l, 101.0) for k in range(n)]


META = {"coin": "T", "dex": "main", "liquid": True}


def test_book_returns_one_r_stop_and_mark_to_market():
    t0 = ms(2026, 9, 21)
    daily = flat(t0, 14)  # two wide weeks: the weekly level sits far away
    daily.append(bar(t0 + 14 * DAY, 100.0, 101.5, 99.0, 101.0))  # Monday: inside
    daily.append(bar(t0 + 15 * DAY, 101.0, 101.8, 100.0, 101.6))  # Tuesday: breaks 101.5 (plain)
    daily += [bar(t0 + 16 * DAY + k * DAY, 101.8, 103.0, 100.0, 102.0) for k in range(6)]  # drifts
    units = coin_book_rows(META, daily)
    tue = next(u for u in units if u["date"] == "2026-10-06" and u["direction"] == "up")
    assert tue["tf"] == "D" and tue["cls"] == "plain"
    r_pct = 100 * 2.5 / 101.5  # level 101.5, stop 99.0
    assert tue["r_pct"] == pytest.approx(r_pct)
    assert tue["out3"] == "neither" and tue["out5"] == "neither"  # target 104 never, stop never
    mtm = 100 * (102.0 - 101.5) / 101.5  # marked at the close of the horizon's last bar
    assert tue["ret3"] == pytest.approx(mtm) and tue["ret5"] == pytest.approx(mtm)
    assert tue["rr5"] == pytest.approx(mtm / r_pct)
    # a one-R unit pays +R%; a stopped unit pays -R%
    daily2 = flat(t0, 14)
    daily2.append(bar(t0 + 14 * DAY, 100.0, 101.5, 99.0, 101.0))
    daily2.append(bar(t0 + 15 * DAY, 101.0, 104.5, 100.5, 104.0))  # 104 touched, 99 not
    daily2 += [bar(t0 + 16 * DAY + k * DAY, 104, 105, 103, 104) for k in range(6)]
    u2 = next(
        u
        for u in coin_book_rows(META, daily2)
        if u["date"] == "2026-10-06" and u["direction"] == "up"
    )
    assert u2["out3"] == "one_r" and u2["ret3"] == pytest.approx(r_pct) and u2["rr3"] == 1.0
    daily3 = flat(t0, 14)
    daily3.append(bar(t0 + 14 * DAY, 100.0, 101.5, 99.0, 101.0))
    daily3.append(bar(t0 + 15 * DAY, 101.0, 101.8, 100.5, 101.6))
    daily3.append(bar(t0 + 16 * DAY, 101.6, 102.0, 98.5, 99.0))  # stop 99 traded on day 1
    daily3 += [bar(t0 + 17 * DAY + k * DAY, 99, 100, 98.6, 99) for k in range(5)]
    u3 = next(
        u
        for u in coin_book_rows(META, daily3)
        if u["date"] == "2026-10-06" and u["direction"] == "up"
    )
    assert u3["out3"] == "stop" and u3["ret3"] == pytest.approx(-r_pct) and u3["rr3"] == -1.0
    # censored units carry no return
    short = daily[:17]
    u4 = next(
        u
        for u in coin_book_rows(META, short)
        if u["date"] == "2026-10-06" and u["direction"] == "up"
    )
    assert u4["out5"] == "censored" and u4["ret5"] is None


def test_book_cell_sums_equal_size_trades_and_tracks_drawdown():
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-01", "2026-01-02", "2026-01-03"],
            "ret5": [2.0, -1.0, -3.0, 4.0],
            "rr5": [1.0, -1.0, -1.0, 1.0],
            "out5": ["one_r", "stop", "stop", "one_r"],
            "r_pct": [2.0, 1.0, 3.0, 4.0],
        }
    )
    c, cum = book_cell(df, 5)
    assert c["n"] == 4 and c["dates"] == 3
    assert c["avg_pct"] == pytest.approx(0.5) and c["hit"] == 0.5 and c["exp_r"] == 0.0
    assert c["total_usd"] == pytest.approx(20.0)  # 2% of 1,000 per trade summed
    assert list(cum.round(2)) == [10.0, -20.0, 20.0]  # by entry date
    assert c["max_dd_usd"] == pytest.approx(-30.0)


def test_r_matched_removes_a_bar_size_mix_effect():
    # base: half tight bars that win 60%, half wide bars that win 20%; stacked: only tight bars at 60%
    rows = []
    for k in range(100):
        rows.append({"cls": "plain", "r_pct": 1.0, "out3": "one_r" if k < 60 else "stop"})
        rows.append({"cls": "plain", "r_pct": 10.0, "out3": "one_r" if k < 20 else "stop"})
        rows.append({"cls": "near", "r_pct": 1.0, "out3": "one_r" if k < 60 else "stop"})
    df = pd.DataFrame(rows)
    df["tf"], df["kind"], df["flag"] = "D", "continuation", "none"
    r = r_matched(df, "D", "continuation", "all", "stacked", 3)
    assert r["n_stacked"] == 100 and r["n_base"] == 200
    assert r["raw"] == pytest.approx(0.60 - 0.40)  # the raw gap is the bar-size mix
    assert r["matched"] == pytest.approx(0.0, abs=1e-9)  # within tight bars there is no gap
    assert r["lo"] < 0 < r["hi"] and r["covered"] == 1.0
    tight = [b for b in r["bins"] if b["n_stacked"]]
    assert (
        len(tight) == 1
        and tight[0]["p_stacked"] == pytest.approx(0.6)
        and tight[0]["p_base"] == pytest.approx(0.6)
    )
