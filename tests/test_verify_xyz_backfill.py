"""Unit tests for analysis/verify_xyz_backfill.py (bar comparison helpers)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

from verify_xyz_backfill import HOUR_MS, aggregate, diff_stats


def _bar(o, h, lo, c, v=0.0):
    return [o, h, lo, c, v]


def test_aggregate_folds_ohlcv_within_bucket():
    # three 15m bars inside one UTC hour: open=first, close=last, h=max, l=min, v=sum
    bars = {
        0: _bar(10.0, 11.0, 9.5, 10.5, 1.0),
        900_000: _bar(10.5, 12.0, 10.4, 11.8, 2.0),
        1_800_000: _bar(11.8, 11.9, 10.0, 10.2, 3.0),
    }
    agg = aggregate(bars, HOUR_MS)
    assert agg == {0: [10.0, 12.0, 9.5, 10.2, 6.0]}


def test_aggregate_is_input_order_independent_and_splits_buckets():
    # dict deliberately built in reverse timestamp order; two buckets
    bars = {
        3_600_000: _bar(20.0, 21.0, 19.0, 20.5, 1.0),
        900_000: _bar(10.5, 12.0, 10.4, 11.8, 2.0),
        0: _bar(10.0, 11.0, 9.5, 10.5, 1.0),
    }
    agg = aggregate(bars, HOUR_MS)
    assert agg[0] == [10.0, 12.0, 9.5, 11.8, 3.0]  # open from ts=0, close from ts=900k
    assert agg[3_600_000] == [20.0, 21.0, 19.0, 20.5, 1.0]


def test_diff_stats_exact_and_mismatch_counting():
    tv = {0: _bar(10.0, 11.0, 9.5, 10.5, 5.0), 1: _bar(10.5, 12.0, 10.0, 11.0, 6.0)}
    hl = {
        0: [10.0, 11.0, 9.5, 10.5, 5.0, 3],  # exact
        1: [10.5, 12.5, 10.0, 11.0, 6.0, 4],  # high differs
    }
    s = diff_stats(tv, hl)
    assert s["overlap"] == 2 and s["all4_exact"] == 1
    assert s["per_field"]["high"]["exact"] == 1
    assert s["per_field"]["open"]["exact"] == 2
    assert abs(s["per_field"]["high"]["max_rel"] - 0.5 / 12.5) < 1e-12
    assert s["vol_match"] == 2


def test_diff_stats_hl_only_split_placeholders_vs_traded():
    tv = {0: _bar(10.0, 11.0, 9.5, 10.5, 5.0)}
    hl = {
        0: [10.0, 11.0, 9.5, 10.5, 5.0, 3],
        1: [10.5, 10.5, 10.5, 10.5, 0.0, 0],  # zero-trade placeholder
        2: [10.6, 10.7, 10.5, 10.6, 2.0, 7],  # genuinely missing from TV
    }
    s = diff_stats(tv, hl)
    assert s["hl_only"] == 2
    assert s["hl_only_placeholders"] == 1
    assert s["hl_only_traded"] == [2]
