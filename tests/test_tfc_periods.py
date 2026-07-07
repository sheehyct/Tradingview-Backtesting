"""Phase-1 tests: period ids + Pine valuewhen period-open semantics (tfc/periods.py).

Seed-date pins are against the committed venue-verified xyz bar files: the
15m history starts 2025-12-02T15:00Z (listing), so D seeds Dec-3 00:00, W
seeds Monday Dec-8 00:00, M seeds Jan-1 00:00. Getting any of these wrong
shifts the first trades and cascades through 100%-equity compounding.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tfc.periods import ftfc, period_ids, period_open_series, tf_seconds  # noqa: E402
from tfc.tv_reference import load_bars  # noqa: E402


def _first_seed_ts(bars, tf):
    op = period_open_series(bars.ts, bars.open, tf)
    seeded = np.flatnonzero(~np.isnan(op))
    assert len(seeded) > 0, f"{tf} never seeds"
    return seeded[0], op


def test_valuewhen_nan_before_first_boundary():
    # first bar of history is never a boundary (timeframe.change[0] == False)
    ts = np.array([0, 900, 1800, 2700, 3600, 4500], dtype=np.int64)
    opens = np.array([10.0, 11.0, 12.0, 13.0, 14.0, 15.0])
    op = period_open_series(ts, opens, "60")
    assert np.isnan(op[:4]).all()  # first 60m period: no boundary yet
    assert op[4] == 14.0 and op[5] == 14.0  # boundary bar's own open, held


def test_monthly_nan_until_jan1_on_15m_file():
    bars = load_bars("tvb6_tv_xyzMSTR_15m.json")
    i, op = _first_seed_ts(bars, "M")
    assert bars.ts[i] == 1767225600  # 2026-01-01T00:00:00Z
    assert np.isnan(op[:i]).all()
    assert op[i] == bars.open[i]


def test_weekly_seeds_monday_dec8_on_15m_file():
    bars = load_bars("tvb6_tv_xyzMSTR_15m.json")
    i, op = _first_seed_ts(bars, "W")
    assert bars.ts[i] == 1765152000  # Monday 2025-12-08T00:00:00Z
    assert np.isnan(op[:i]).all()


def test_daily_seeds_dec3_on_15m_file():
    bars = load_bars("tvb6_tv_xyzMSTR_15m.json")
    i, _ = _first_seed_ts(bars, "D")
    assert bars.ts[i] == 1764720000  # 2025-12-03T00:00:00Z


def test_240m_ids_anchor_to_utc_windows():
    # ids partition time into [k*4h, (k+1)*4h) windows anchored at 00:00 UTC --
    # NOT at the 15:00Z listing-start bar. (Missing bars are fine: change fires
    # on the first PRESENT bar of a new window, which is Pine's behavior too.)
    bars = load_bars("tvb6_tv_xyzMSTR_60m.json")
    pid = period_ids(bars.ts, "240")
    assert (pid == bars.ts // 14400).all()
    # a full UTC day holds exactly six 240m periods
    day = bars.ts // 86400
    full_days = [d for d in np.unique(day) if (day == d).sum() == 24]
    assert full_days, "no complete 24-bar day in the 60m file"
    sel = day == full_days[0]
    assert len(np.unique(pid[sel])) == 6
    # within one window all four hourly bars share the id
    w0 = full_days[0] * 86400
    sel4 = (bars.ts >= w0) & (bars.ts < w0 + 14400)
    assert sel4.sum() == 4 and len(np.unique(pid[sel4])) == 1


def test_weekly_id_monday_anchor():
    sun = np.array([1765065600], dtype=np.int64)  # Sunday 2025-12-07
    mon = np.array([1765152000], dtype=np.int64)  # Monday 2025-12-08
    assert period_ids(mon, "W")[0] == period_ids(sun, "W")[0] + 1


def test_ftfc_strictness_and_nan():
    close = np.array([100.0, 100.0, 100.0])
    above = np.array([99.0, 99.0, 99.0])
    equal = np.array([99.0, 100.0, 99.0])
    withnan = np.array([99.0, 99.0, np.nan])
    up, dn = ftfc(close, [above])
    assert up.all() and not dn.any()
    up, dn = ftfc(close, [above, equal])
    assert list(up) == [True, False, True] and not dn.any()  # equality => grey
    up, dn = ftfc(close, [above, withnan])
    assert list(up) == [True, True, False]  # NaN => grey
    up, dn = ftfc(close, [])
    assert not up.any() and not dn.any()  # n_enabled == 0


def test_tf_seconds_ordering():
    assert tf_seconds("15") == 900
    assert tf_seconds("240") == 14400
    assert tf_seconds("D") == 86400
    assert tf_seconds("15") < tf_seconds("60") < tf_seconds("D") < tf_seconds("W") < tf_seconds("M")
