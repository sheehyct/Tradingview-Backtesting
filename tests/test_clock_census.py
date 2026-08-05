"""RTH calendar + tracker-convention tests for the TVB-19 clock census."""

from datetime import datetime, timezone
from pathlib import Path

from analysis.clock_census import make_trackers, rth_rolls

REPO = Path(__file__).resolve().parents[1]


def _utc(y, mo, d, h=0, mi=0):
    return int(datetime(y, mo, d, h, mi, tzinfo=timezone.utc).timestamp())


def test_rth_day_rolls_skip_weekend_and_holiday():
    rolls = set(rth_rolls()["D"])
    # 9:30 ET = 13:30 UTC during EDT
    assert _utc(2026, 7, 2, 13, 30) in rolls
    assert _utc(2026, 7, 3, 13, 30) not in rolls  # Independence Day observed
    assert _utc(2026, 7, 4, 13, 30) not in rolls  # Saturday
    assert _utc(2026, 7, 5, 13, 30) not in rolls  # Sunday
    assert _utc(2026, 7, 6, 13, 30) in rolls  # Monday reopens


def test_rth_week_and_month_rolls():
    rolls = rth_rolls()
    assert _utc(2026, 7, 6, 13, 30) in set(rolls["W"])  # Monday week open
    assert _utc(2026, 7, 1, 13, 30) in set(rolls["M"])  # July: the 1st trades
    assert _utc(2026, 8, 3, 13, 30) in set(rolls["M"])  # August: 1st-2nd weekend
    assert _utc(2026, 8, 1, 13, 30) not in set(rolls["M"])


def test_weekend_bars_belong_to_friday_session():
    _, rth = make_trackers()
    kf = rth.keyers["D"]
    fri = kf(_utc(2026, 7, 10, 14, 0))
    sat = kf(_utc(2026, 7, 11, 3, 0))
    sun = kf(_utc(2026, 7, 12, 22, 0))
    mon_pre = kf(_utc(2026, 7, 13, 13, 25))
    mon_post = kf(_utc(2026, 7, 13, 13, 30))
    assert fri == sat == sun == mon_pre
    assert mon_post == fri + 1


def test_open_sampling_first_bar_at_or_after_roll():
    _, rth = make_trackers()
    # bar starting exactly at the roll instant opens the new period
    rth.feed(_utc(2026, 7, 13, 13, 25), 100.0)
    d_key = rth.key["D"]
    rth.feed(_utc(2026, 7, 13, 13, 30), 101.0)
    assert rth.key["D"] == d_key + 1
    assert rth.open["D"] == 101.0
    # next bar inside the same period does not resample the open
    rth.feed(_utc(2026, 7, 13, 13, 35), 102.0)
    assert rth.open["D"] == 101.0
