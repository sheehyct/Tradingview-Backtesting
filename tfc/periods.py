"""UTC period identifiers and Pine-equivalent period-open reconstruction.

Mirrors the gate reconstruction in pine/baseline_continuity.pine:

    f_open(tf) => ta.valuewhen(timeframe.change(tf), open, 0)

Semantics that MUST be preserved (verified against the deployed Pine):
- timeframe.change(tf) is False on the first bar of loaded history (there is
  no prior bar to compare against), so the reconstructed period open is NaN
  until the FIRST period boundary inside the data. A NaN open makes that
  timeframe read neither-above-nor-below => the gate is grey until every
  enabled TF has seeded.
- The "day" rolls at 00:00 UTC on these 24/7 perps (charter S2). Weeks are
  Monday-anchored. Months are calendar UTC months.
- A chart bar belongs to the period containing its OPEN time (bars are
  keyed by open timestamp, and chart bars tile gate periods by f_guard).
"""

from __future__ import annotations

import numpy as np

__all__ = ["tf_seconds", "period_ids", "period_open_series", "ftfc"]


def tf_seconds(tf: str) -> int:
    """Pine timeframe string -> period length in seconds.

    Intraday timeframes are minutes ('15', '60', '240'). 'D'/'W'/'M' are
    calendar periods; W and M have variable length -- the returned value is
    only used for f_guard ordering/tiling checks (>= 86400 branch), never
    for period-id arithmetic.
    """
    if tf == "D":
        return 86400
    if tf == "W":
        return 7 * 86400
    if tf == "M":
        return 28 * 86400  # ordering sentinel only; ids use calendar months
    return int(tf) * 60


def period_ids(ts: np.ndarray, tf: str) -> np.ndarray:
    """Integer period id per bar (ts = bar OPEN, epoch seconds, UTC).

    Two bars share an id iff they belong to the same tf-period.
    """
    ts = np.asarray(ts, dtype=np.int64)
    if tf == "M":
        return ts.astype("datetime64[s]").astype("datetime64[M]").astype(np.int64)
    if tf == "W":
        # epoch day 0 = Thursday 1970-01-01; +3 shifts the week roll to Monday
        return (ts // 86400 + 3) // 7
    if tf == "D":
        return ts // 86400
    secs = int(tf) * 60
    # Intraday periods anchor to 00:00 UTC; every enabled intraday gate TF
    # divides 1D (f_guard), so epoch-anchored == day-anchored.
    return ts // secs


def period_open_series(ts: np.ndarray, opens: np.ndarray, tf: str) -> np.ndarray:
    """ta.valuewhen(timeframe.change(tf), open, 0) over the whole series.

    NaN until the first period boundary (change is False on bar 0), then the
    open of the most recent boundary bar, inclusive of the boundary bar
    itself (valuewhen with occurrence 0 sees the current bar's own event).
    """
    ts = np.asarray(ts, dtype=np.int64)
    opens = np.asarray(opens, dtype=np.float64)
    pid = period_ids(ts, tf)
    n = len(ts)
    change = np.zeros(n, dtype=bool)
    if n > 1:
        change[1:] = pid[1:] != pid[:-1]
    idx = np.where(change, np.arange(n), -1)
    idx = np.maximum.accumulate(idx)
    out = np.full(n, np.nan)
    seeded = idx >= 0
    out[seeded] = opens[idx[seeded]]
    return out


def ftfc(close: np.ndarray, open_series_list: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """FTFC aggregation, verbatim port of the Pine gate loop.

    up requires close strictly above EVERY enabled period open; dn strictly
    below. Equality or NaN on ANY timeframe forces both False (grey) for
    that bar. Zero enabled timeframes => both False everywhere.
    """
    close = np.asarray(close, dtype=np.float64)
    n = len(close)
    if not open_series_list:
        z = np.zeros(n, dtype=bool)
        return z, z.copy()
    up = np.ones(n, dtype=bool)
    dn = np.ones(n, dtype=bool)
    for op in open_series_list:
        with np.errstate(invalid="ignore"):
            up &= close > op  # NaN compares False, matching Pine na-comparison
            dn &= close < op
    return up, dn
