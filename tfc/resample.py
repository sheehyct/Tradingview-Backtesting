"""UTC resampler: build higher-TF bars from lower-TF bars (Phase 4 seam).

Semantics verified against the committed TV files (tests/test_tfc_resample.py):
- A resampled bar is timestamped at its PERIOD START even when history begins
  mid-period (TV's 1D file starts 2025-12-02T00:00Z although trading data
  begins 15:00Z).
- O = first bar's open, H/L = extremes, C = last bar's close, V = sum, over
  the bars whose OPEN falls in the period (same rule as the gate's period
  ids). Periods with no source bars produce no bar (TV omits them too).
- The day rolls at 00:00 UTC; weeks are Monday-anchored; months calendar UTC.
"""

from __future__ import annotations

import numpy as np

from tfc.periods import period_ids
from tfc.tv_reference import Bars

__all__ = ["period_start", "resample"]


def period_start(pid: np.ndarray, tf: str) -> np.ndarray:
    """Inverse of period_ids: the period's UTC start time (epoch seconds)."""
    pid = np.asarray(pid, dtype=np.int64)
    if tf == "M":
        return pid.astype("datetime64[M]").astype("datetime64[s]").astype(np.int64)
    if tf == "W":
        return (pid * 7 - 3) * 86400  # inverse of (day + 3) // 7, Monday-anchored
    if tf == "D":
        return pid * 86400
    return pid * (int(tf) * 60)


def resample(bars: Bars, target_tf: str) -> Bars:
    pid = period_ids(bars.ts, target_tf)
    if not np.all(np.diff(pid) >= 0):
        raise AssertionError("bar open times must be non-decreasing per period id")
    starts = np.flatnonzero(np.r_[True, pid[1:] != pid[:-1]])
    ends = np.r_[starts[1:], len(pid)] - 1
    return Bars(
        symbol=bars.symbol,
        interval=target_tf,
        ts=period_start(pid[starts], target_tf),
        open=bars.open[starts],
        high=np.maximum.reduceat(bars.high, starts),
        low=np.minimum.reduceat(bars.low, starts),
        close=bars.close[ends],
        volume=np.add.reduceat(bars.volume, starts),
    )
