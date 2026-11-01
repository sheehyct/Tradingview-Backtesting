"""The ES tape for the one-instrument bench (docs/experiments/tvb43_bench_prereg.md, section 1):
the Databento cache in vectorbt-workspace read into the census's bar format on the SESSION
calendar, with the table that puts every session back on the exchange's real clock.

Two day definitions, both declared in the prereg. V0, the Globex session: 18:00 ET open (22:00
or 23:00 UTC), the cache's own `1D`, `60m`, `1W` and `1M` bars. V1, the regular-hours day: 09:30
to 16:00 ET, built here from the 1-minute source. The engine sees SESSION TIME: a session's daily
bar sits at its trade date 00:00 UTC and its hours at whole-hour offsets from the session's open,
so the 24/7 engine's index arithmetic holds unchanged (`census.use_calendar("session")` covers
the rest); the exporter puts the real times back through `opens_by_date`
(`run_export.Tape`). Roll sessions come from the 1-minute source's `instrument_id`, which
switches at 00:00 UTC on each quarterly roll (the continuous `symbol` never changes).

Nothing here is trade logic. Nothing here is synthetic: every bar is the cache's, resampled or
grouped, never filled.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

# the cache lives in the sibling workspace (spine layout C:/Strat_Trading_Bot/<project>/);
# BENCH_CACHE overrides it
CACHE = Path(
    os.environ.get(
        "BENCH_CACHE",
        str(
            Path(__file__).resolve().parents[3] / "vectorbt-workspace" / "data" / "databento_cache"
        ),
    )
)
ET = ZoneInfo("America/New_York")
DAY_MS = 86_400_000
HOUR_MS = 3_600_000
GLOBEX_LABEL_SHIFT_H = 6  # a Globex open (22:00 / 23:00 UTC) plus six hours is its trade date
RTH_OPEN_MIN = 9 * 60 + 30  # 09:30 ET
RTH_CLOSE_MIN = 16 * 60  # 16:00 ET (exclusive)


@dataclass
class SessionTape:
    """One instrument's sessions in both clocks."""

    variant: str  # "globex" | "rth"
    symbol: str
    daily: list[dict]  # session time, ms: the engine's daily bars (t = trade date 00:00 UTC)
    hourly: list[dict]  # session time, ms: hour offsets from each session's open
    real_daily: list[list[float]]  # [open_s, o, h, l, c, v] on the exchange's clock, seconds
    real_hourly: list[list[float]]
    real_weekly: list[
        list[float]
    ]  # the cache's own weekly bars (Globex) or [] (RTH: aggregated on the page)
    real_monthly: list[list[float]]
    opens_by_date: dict[str, int]  # trade date -> the session's real open, seconds
    roll_dates: set[str]  # trade dates whose session is the first on a new contract
    short_sessions: dict[
        str, int
    ]  # trade date -> hours present, for sessions with fewer hours than the mode
    label_shift_hours: int

    @property
    def dates(self) -> list[str]:
        return [date_of_ms(d["t"]) for d in self.daily]


def date_of_ms(t_ms: int) -> str:
    return datetime.fromtimestamp(t_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def session_ms(date: str) -> int:
    """The engine's clock for a trade date: that date at 00:00 UTC, in ms."""
    return int(datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)


def _bar(t_ms: int, row) -> dict:
    return {
        "t": int(t_ms),
        "o": float(row["open"]),
        "h": float(row["high"]),
        "l": float(row["low"]),
        "c": float(row["close"]),
        "v": float(row["volume"]),
    }


def _compact(ts_s: int, row) -> list[float]:
    return [
        int(ts_s),
        float(row["open"]),
        float(row["high"]),
        float(row["low"]),
        float(row["close"]),
        float(row["volume"]),
    ]


def _frame_compact(df: pd.DataFrame) -> list[list[float]]:
    return [
        _compact(ts.value // 1_000_000_000, r) for ts, r in zip(df.index, df.to_dict("records"))
    ]


def roll_change_times(root: Path, symbol: str) -> list[pd.Timestamp]:
    """The times the continuous contract switched instrument (the 1-minute source's
    `instrument_id`); 60 quarterly switches for ES 2011-2025, each at 00:00 UTC."""
    s = pd.read_parquet(root / symbol / "source_1m.parquet", columns=["instrument_id"])
    ids = s["instrument_id"].to_numpy()
    chg = np.nonzero(ids[1:] != ids[:-1])[0] + 1
    return [s.index[k] for k in chg]


def _roll_dates(opens: pd.DatetimeIndex, dates: list[str], changes, side: str) -> set[str]:
    """The trade dates whose session is the first on a new contract. Globex (`side="right"`): the
    session already open at the switch (it opened the evening before); RTH (`side="left"`): the
    next regular session at or after the switch."""
    out: set[str] = set()
    vals = opens.values
    for c in changes:
        k = int(np.searchsorted(vals, np.datetime64(c.value, "ns"), side=side))
        if side == "right":
            k -= 1
        if 0 <= k < len(dates):
            out.add(dates[k])
    return out


def load_globex(root: Path = CACHE, symbol: str = "ES.n.0") -> SessionTape:
    """V0: the cache's Globex session bars. The `1D` bar IS the session (its open 22:00 or 23:00
    UTC); the `60m` bars inside [open_k, open_k+1) are its hours at whole-hour offsets; `1W` and
    `1M` are the exchange's own weekly and monthly bars, shipped to the page as they are."""
    d = pd.read_parquet(root / symbol / "1D.parquet")
    h = pd.read_parquet(root / symbol / "60m.parquet")
    w = pd.read_parquet(root / symbol / "1W.parquet")
    m = pd.read_parquet(root / symbol / "1M.parquet")
    opens = d.index
    dates = [(ts + pd.Timedelta(hours=GLOBEX_LABEL_SHIFT_H)).strftime("%Y-%m-%d") for ts in opens]
    if len(set(dates)) != len(dates):
        raise ValueError("two Globex sessions label the same trade date")
    daily = [_bar(session_ms(date), row) for date, row in zip(dates, d.to_dict("records"))]
    real_daily = _frame_compact(d)
    opens_by_date = {date: int(ts.value // 1_000_000_000) for date, ts in zip(dates, opens)}
    # hours: every 60m bar belongs to the session whose open is the latest at or before it
    pos = np.searchsorted(h.index.values, opens.values)
    hourly: list[dict] = []
    real_hourly: list[list[float]] = []
    counts: dict[str, int] = {}
    for k, date in enumerate(dates):
        lo = int(pos[k])
        hi = int(pos[k + 1]) if k + 1 < len(pos) else len(h)
        open_ms = int(opens[k].value // 1_000_000)
        n = 0
        for ts, row in zip(h.index[lo:hi], h.iloc[lo:hi].to_dict("records")):
            off = int(ts.value // 1_000_000) - open_ms
            if off % HOUR_MS != 0:
                continue  # an hour not on the session's hour grid is not an hour of the clock
            hourly.append(_bar(session_ms(date) + off, row))
            real_hourly.append(_compact(ts.value // 1_000_000_000, row))
            n += 1
        counts[date] = n
    mode = max(set(counts.values()), key=list(counts.values()).count) if counts else 0
    short = {date: n for date, n in counts.items() if n < mode}
    rolls = _roll_dates(opens, dates, roll_change_times(root, symbol), side="right")
    return SessionTape(
        variant="globex",
        symbol=symbol,
        daily=daily,
        hourly=hourly,
        real_daily=real_daily,
        real_hourly=real_hourly,
        real_weekly=_frame_compact(w),
        real_monthly=_frame_compact(m),
        opens_by_date=opens_by_date,
        roll_dates=rolls,
        short_sessions=short,
        label_shift_hours=GLOBEX_LABEL_SHIFT_H,
    )


def load_rth(root: Path = CACHE, symbol: str = "ES.n.0") -> SessionTape:
    """V1: the regular-hours day, 09:30 to 16:00 ET, from the 1-minute source. The daily bar is
    the day's first minute's open, the extremes, the last minute's close; the hours are
    60-minute bins from 09:30 (the seventh is the 15:30 to 16:00 half hour; an early close leaves
    fewer). The trade date is the ET calendar date, which is also the UTC date of the 13:30 /
    14:30 UTC open (label shift 0)."""
    s = pd.read_parquet(
        root / symbol / "source_1m.parquet", columns=["open", "high", "low", "close", "volume"]
    )
    et = s.index.tz_convert(ET)
    minutes = et.hour * 60 + et.minute
    mask = (minutes >= RTH_OPEN_MIN) & (minutes < RTH_CLOSE_MIN)
    s = s[mask]
    et = et[mask]
    date = pd.Index(et.strftime("%Y-%m-%d"), name="date")
    hour_bin = ((minutes[mask] - RTH_OPEN_MIN) // 60).astype(int)
    g = s.groupby(date)
    dd = g.agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
    )
    first_ts = pd.Series(s.index, index=date).groupby(level=0).first()
    dates = list(dd.index)
    daily = [_bar(session_ms(dt), row) for dt, row in zip(dates, dd.to_dict("records"))]
    opens_by_date = {dt: int(first_ts[dt].value // 1_000_000_000) for dt in dates}
    real_daily = [_compact(opens_by_date[dt], row) for dt, row in zip(dates, dd.to_dict("records"))]
    hb = s.groupby([date, pd.Index(hour_bin, name="bin")]).agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
    )
    hourly: list[dict] = []
    real_hourly: list[list[float]] = []
    counts: dict[str, int] = {}
    for (dt, b), row in zip(hb.index, hb.to_dict("records")):
        hourly.append(_bar(session_ms(dt) + int(b) * HOUR_MS, row))
        real_hourly.append(_compact(opens_by_date[dt] + int(b) * 3600, row))
        counts[dt] = counts.get(dt, 0) + 1
    mode = max(set(counts.values()), key=list(counts.values()).count) if counts else 0
    short = {dt: n for dt, n in counts.items() if n < mode}
    opens = pd.DatetimeIndex([first_ts[dt] for dt in dates])
    rolls = _roll_dates(opens, dates, roll_change_times(root, symbol), side="left")
    return SessionTape(
        variant="rth",
        symbol=symbol,
        daily=daily,
        hourly=hourly,
        real_daily=real_daily,
        real_hourly=real_hourly,
        real_weekly=[],
        real_monthly=[],
        opens_by_date=opens_by_date,
        roll_dates=rolls,
        short_sessions=short,
        label_shift_hours=0,
    )


def load(variant: str, root: Path = CACHE, symbol: str = "ES.n.0") -> SessionTape:
    if variant == "globex":
        return load_globex(root, symbol)
    if variant == "rth":
        return load_rth(root, symbol)
    raise ValueError(f"variant must be globex or rth, got {variant!r}")
