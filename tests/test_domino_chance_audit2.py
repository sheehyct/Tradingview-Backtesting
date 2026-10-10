"""Vectors added after the second Codex audit of the chance comparison
(docs/reviews/tvb37-chance-codex-audit.md): decimal touch fills, monthly horizons, class coverage,
entry-time invariance of the context columns, cell denominators, flag masks, venue era, the variant.
"""

from datetime import datetime, timezone

import pandas as pd

from analysis.domino.census import DAY, aggregate
from analysis.domino.chance import (
    _ci,
    cell,
    coin_units,
    flag_mask,
    horizon_ends,
    next_bar,
    stack_class,
    venue_era,
    walk,
)


def ms(y, m, d):
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1000)


def bar(t, o, h, l, c, v=1000.0):
    return {"t": t, "o": o, "h": h, "l": l, "c": c, "v": v}


def flat(t0, n, h=102.0, l=98.0):
    return [bar(t0 + k * DAY, 100.0, h, l, 101.0) for k in range(n)]


META = {"coin": "T", "dex": "main", "liquid": True}
ONE = {1: 0, 3: None, 5: None}


def test_decimal_touch_fills_on_both_sides():  # second audit F1
    t0 = ms(2026, 9, 21)
    out = walk([bar(t0, 0.09, 0.12, 0.09, 0.11)], 0, "up", 0.10, 0.08, ONE)  # high = exactly one R
    assert out["out1"] == "one_r"
    out = walk([bar(t0, 0.13, 0.13, 0.10, 0.11)], 0, "down", 0.12, 0.14, ONE)  # low = exactly one R
    assert out["out1"] == "one_r"
    out = walk([bar(t0, 0.10, 0.11, 0.08, 0.10)], 0, "up", 0.10, 0.08, ONE)  # stop touched exactly
    assert out["out1"] == "stop" and out["stop0"] is True
    out = walk([bar(t0, 0.10, 0.1199, 0.0801, 0.10)], 0, "up", 0.10, 0.08, ONE)
    assert out["out1"] == "neither"


def test_monthly_horizons_and_follow_through():
    t0 = ms(2026, 1, 1)
    daily = flat(t0, 31 + 28 + 31 + 30 + 5)  # Jan .. Apr complete, five days of May
    buckets = {tf: aggregate(daily, tf) for tf in ("W", "M", "Q")}
    bucket_of = {
        tf: {di: b for b, bk in enumerate(buckets[tf]) for di in bk["days"]} for tf in ("W", "M")
    }
    i = 31 + 10  # 11 February
    ends = horizon_ends("M", i, daily, buckets, bucket_of)
    assert ends[1] == 31 + 28 + 31 - 1  # the last day of March
    assert ends[3] is None  # May is incomplete
    assert (
        next_bar("M", i, daily, buckets, bucket_of, "up") == "inside"
    )  # flat months: equal ranges


def test_weekly_and_monthly_classes_cover_within1_and_spread():
    shared = {"W": False, "M": True, "Q": False}
    assert stack_class("W", "up", {"D": 100.0, "W": 100.5}, shared)[0] == "within1"
    assert stack_class("W", "down", {"D": 100.0, "W": 97.0}, shared)[0] == "spread"
    assert stack_class("M", "up", {"D": 100.0, "W": 100.0, "M": 100.0}, shared)[0] == "exact_shared"
    assert stack_class("M", "up", {"D": 100.0, "M": 100.2}, shared)[0] == "near"


def test_context_columns_do_not_move_with_todays_candle():  # amendment A2
    t0 = ms(2026, 9, 21)
    base = flat(t0, 14, h=110.0, l=90.0) + [bar(t0 + 14 * DAY, 100.0, 101.5, 99.0, 101.0)]
    quiet = (
        base + [bar(t0 + 15 * DAY, 101.0, 101.8, 100.0, 101.6)] + flat(t0 + 16 * DAY, 6, 103, 100)
    )
    wild = (
        base + [bar(t0 + 15 * DAY, 101.0, 125.0, 100.0, 120.0)] + flat(t0 + 16 * DAY, 6, 126, 118)
    )

    def pick(units):
        return next(
            u
            for u in units
            if u["date"] == "2026-10-06" and u["tf"] == "D" and u["direction"] == "up"
        )

    ua, ub = pick(coin_units(META, quiet)[0]), pick(coin_units(META, wild)[0])
    for col in ("cls", "kind", "flag", "m_support", "quarter", "near_tf", "level", "stop"):
        assert ua[col] == ub[col]
    assert ua["stack"] == "D" and ub["stack"] == "D+W"  # outcome-side information only


def test_cell_denominators_exclude_censored_and_greying_uses_valid_counts():  # second audit F2
    row = {
        "date": "2026-01-01",
        "out1": "one_r",
        "out3": "censored",
        "out5": "censored",
        "mfe1": 1.0,
        "mae1": 0.2,
        "mfe3": None,
        "mae3": None,
        "mfe5": None,
        "mae5": None,
        "next_bar": "with",
        "r_pct": 5.0,
        "stop0": False,
    }
    c = cell(pd.DataFrame([row] * 40))
    assert c["n"] == 40 and c["n1"] == 40 and c["n3"] == 0 and c["one_r1"] == 1.0
    assert _ci(c, 1).startswith("100.0%") and _ci(c, 1).endswith("n=40") and _ci(c, 3) == "-"
    assert _ci(cell(pd.DataFrame([row] * 10)), 1).startswith("(")  # ten valid units: greyed


def test_flag_mask_follows_the_frame_index():
    df = pd.DataFrame({"flag": ["none", "third", "strict"]}, index=[5, 7, 9])
    assert list(flag_mask(df, "all").index) == [5, 7, 9] and bool(flag_mask(df, "all").all())
    assert list(flag_mask(df, "third")) == [False, True, True]
    assert list(flag_mask(df, "strict")) == [False, False, True]


def test_venue_era_keeps_later_zero_volume_days():  # second audit F8
    t0 = ms(2026, 9, 21)
    daily = [bar(t0 + k * DAY, 1, 1, 1, 1, v=v) for k, v in enumerate([0.0, 5.0, 0.0, 3.0])]
    assert len(venue_era(daily)) == 3


def test_variant_stop_on_the_wrong_side_is_counted_and_skipped():
    # last week 110..90; Monday collapses below 90, Tuesday breaks Monday's high at 88 < 90
    t0 = ms(2026, 9, 21)
    daily = flat(t0, 14, h=110.0, l=90.0)
    daily.append(bar(t0 + 14 * DAY, 88.0, 88.0, 80.0, 82.0))
    daily.append(bar(t0 + 15 * DAY, 82.0, 89.0, 81.0, 88.0))
    daily += flat(t0 + 16 * DAY, 6, h=88.5, l=85.0)  # inside bars after: no further breaks
    units, counts = coin_units(META, daily)
    u = next(
        u for u in units if u["date"] == "2026-10-06" and u["tf"] == "D" and u["direction"] == "up"
    )
    assert u["vout1"] == "n/a" and u["v_r_pct"] is None
    assert counts["variant_stop_wrong_side"] == 1
