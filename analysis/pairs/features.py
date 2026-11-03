"""The pre-entry variables of the matched-pair study (prereg section 5, frozen by the owner
2026-11-02; section 12, the in-session Codex pass folded the same day). Every bar-based variable
reads bars strictly BEFORE the entry session: the setup bar (the bar whose high or low is the
trigger) and the bars before it, on the UNIT'S OWN timeframe (daily bars for a daily unit, the
census's weekly / monthly buckets for a weekly / monthly unit). The card-based variables are
fields the engine fixed at the trigger. Nothing after the trigger.

As built from the twelve declared: the liquidity flag is WITHDRAWN (the engine computes it from
the snapshot's last 30 days and copies it onto every historical unit: retrospective, not
pre-entry; venue stays); the ladder's depth and the nearest higher-timeframe level's timeframe
are reported as the prereg's variables 6 and 7 name them; the entry-day stack is NOT a variable
(it records which levels broke the same day: outcome-side).

Bar windows (prereg section 11): the normal range and the volume baseline are the 20 bars before
the setup bar; the run-up is the 3 bars before the setup bar; the distance travelled is from the
lowest low (long) or highest high (short) of the 20 bars ending WITH the setup bar. The setup
bar's size is the engine's `r_pct` (trigger to far side, percent of the trigger). A unit whose
setup bar has fewer bars behind it than a window needs carries no value for that variable
(absent, counted, never filled)."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from analysis.domino.census import aggregate

LOOK = 20  # the normal-range and volume window, bars of the unit's own timeframe
RUNUP = 3  # the run-up window

# name -> (kind, trader label); the order is the receipt's order
VARS: dict[str, tuple[str, str]] = {
    "v_setup_pct": (
        "numeric",
        "the setup bar's size (trigger to far side, percent of the trigger)",
    ),
    "v_setup_vs_norm": (
        "numeric",
        "the setup bar against the instrument's normal range (20 bars before it)",
    ),
    "v_runup": (
        "numeric",
        "volatility building: the 3 bars before the setup bar against the 20 before it",
    ),
    "v_travel": (
        "numeric",
        "how far price had already run: the trigger from the 20-bar low (long) or high (short), in average ranges",
    ),
    "v_room_r": ("numeric", "room to the first target, in R (the setup bar's own size)"),
    "cls": ("category", "a weekly or monthly level at the trigger (the domino class)"),
    "near_tf": ("category", "the timeframe of the nearest higher level at the trigger"),
    "anchor": ("category", "how the targets were anchored"),
    "ladder_len": ("category", "how deep the target ladder is (targets fixed at entry, 0 to 3)"),
    "flag": ("category", "hammer or shooter on the setup bar"),
    "v_vol_vs_norm": ("numeric", "volume on the setup bar against the 20 bars before it"),
    "v_week": ("category", "where in the week the entry session sits"),
    "v_index": (
        "category",
        "the index at the trigger: bitcoin's previous session, green or red, and above or below its week's open (crypto only)",
    ),
    "dex": ("category", "venue, main or xyz (crypto only)"),
}
NUMERIC = tuple(k for k, (kind, _) in VARS.items() if kind == "numeric")
CATEGORY = tuple(k for k, (kind, _) in VARS.items() if kind == "category")
# the two-level categories the theme rule can read as high against low (prereg section 7.1)
BINARY_HIGH = {"flag": ("third", "strict"), "dex": ("main",)}
BAR_VARS = ("v_setup_vs_norm", "v_runup", "v_travel", "v_vol_vs_norm")

WEEKDAY = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def date_of(t_ms: int) -> str:
    return datetime.fromtimestamp(t_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def unit_bars(daily: list[dict], tf: str) -> tuple[list[dict], list[int]]:
    """The bars of the unit's own timeframe, and for every daily index the index of the unit bar
    holding it (-1 when the census dropped it: a partial first bucket). Weekly and monthly bars
    are the census's buckets under whatever calendar is active, with the volume summed."""
    if tf == "D":
        return daily, list(range(len(daily)))
    buckets = aggregate(daily, tf)
    of = [-1] * len(daily)
    out = []
    for k, b in enumerate(buckets):
        out.append(
            {
                "t": b["t"],
                "o": b["o"],
                "h": b["h"],
                "l": b["l"],
                "c": b["c"],
                "v": float(sum(daily[i]["v"] for i in b["days"])),
                "days": list(b["days"]),
            }
        )
        for i in b["days"]:
            of[i] = k
    return out, of


def _f(x) -> float | None:
    if x is None:
        return None
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return None if not math.isfinite(x) else x


class TapeVars:
    """One instrument's bars on one unit timeframe with the rolling windows precomputed, so a
    unit's variables are a lookup at its setup bar. Build it under the calendar the rows were
    made with (the census's `use_calendar` for a session tape)."""

    def __init__(self, daily: list[dict], tf: str):
        self.tf = tf
        self.bars, self.of = unit_bars(daily, tf)
        h = np.array([b["h"] for b in self.bars], dtype=float)
        low = np.array([b["l"] for b in self.bars], dtype=float)
        c = np.array([b["c"] for b in self.bars], dtype=float)
        v = np.array([b["v"] for b in self.bars], dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            rng_pct = np.where(c > 0, (h - low) / c * 100.0, np.nan)
        rng_px = h - low
        s = pd.Series
        n = len(self.bars)
        if n:
            # at index s: the mean over the LOOK (RUNUP) bars BEFORE s; the min / max over the LOOK bars ending WITH s
            self.norm_pct = s(rng_pct).rolling(LOOK).mean().shift(1).to_numpy()
            self.norm_px = s(rng_px).rolling(LOOK).mean().shift(1).to_numpy()
            self.norm_vol = s(v).rolling(LOOK).mean().shift(1).to_numpy()
            self.runup_pct = s(rng_pct).rolling(RUNUP).mean().shift(1).to_numpy()
            self.low20 = s(low).rolling(LOOK).min().to_numpy()
            self.high20 = s(h).rolling(LOOK).max().to_numpy()
        else:
            self.norm_pct = self.norm_px = self.norm_vol = self.runup_pct = np.array([])
            self.low20 = self.high20 = np.array([])
        self.vol = v

    def setup_index(self, i: int) -> int:
        """The setup bar of a unit whose entry session is daily index `i`: the previous daily bar
        for a daily unit; the unit bar BEFORE the one holding the entry session otherwise. -1 when
        there is none."""
        if self.tf == "D":
            return i - 1
        k = self.of[i] if 0 <= i < len(self.of) else -1
        return k - 1 if k > 0 else -1

    def at(self, i: int, direction: str, level: float, r_pct) -> dict:
        """The four bar-based variables of the unit entered at daily index `i`; `r_pct` is the
        engine's setup-bar size (percent of the trigger), the expansion variable's numerator as
        the prereg wrote it."""
        out: dict = {k: None for k in BAR_VARS}
        s = self.setup_index(i)
        if s < 0 or s >= len(self.bars):
            return out
        np_ = _f(self.norm_pct[s])
        rp = _f(r_pct)
        if np_ is not None and np_ > 0:
            out["v_setup_vs_norm"] = None if rp is None else rp / np_
            ru = _f(self.runup_pct[s])
            out["v_runup"] = None if ru is None else ru / np_
        npx = _f(self.norm_px[s])
        if npx is not None and npx > 0:
            lo, hi = _f(self.low20[s]), _f(self.high20[s])
            if direction == "up" and lo is not None:
                out["v_travel"] = (float(level) - lo) / npx
            elif direction == "down" and hi is not None:
                out["v_travel"] = (hi - float(level)) / npx
        nv = _f(self.norm_vol[s])
        if nv is not None and nv > 0:
            out["v_vol_vs_norm"] = _f(self.vol[s] / nv)
        return out


def room_r(level, t1, r_pct) -> float | None:
    """Room to the first target in R: the T1 distance in percent of the trigger over the setup
    bar's own size in percent."""
    t1, level, r_pct = _f(t1), _f(level), _f(r_pct)
    if t1 is None or level is None or r_pct is None or level <= 0 or r_pct <= 0:
        return None
    return abs(t1 - level) / level * 100.0 / r_pct


def month_side(daily: list[dict], i: int, level: float, direction: str) -> str:
    """The month's side at entry read from the UNIT'S OWN trigger against the month's open (the
    census's month bucket holding the entry session, under the active calendar): "with" when
    the trigger is beyond the open in the trade's direction, "against" otherwise (equality =
    against, the census's rule), "unknown" when the entry month has no month before it. The
    engine's label on weekly and monthly units compared the DAILY trigger (Codex, TVB-44), so
    the cell key is rebuilt here for those units."""
    months = aggregate(daily, "M")
    for k, b in enumerate(months):
        if i in b["days"]:
            if k == 0:
                return "unknown"
            with_ = float(level) > b["o"] if direction == "up" else float(level) < b["o"]
            return "with" if with_ else "against"
    return "unknown"


def week_position(daily: list[dict], i: int) -> str | None:
    """first / middle / last session of the entry session's week, under the active calendar
    (the session tape's reading of "where in the week"). At the very end of a tape the last
    session cannot know whether its week went on; a limit, not a leak of outcomes."""
    weeks = aggregate(daily, "W")
    for b in weeks:
        if i in b["days"]:
            if len(b["days"]) == 1:
                return "first"
            return "first" if i == b["days"][0] else "last" if i == b["days"][-1] else "middle"
    return None


def weekday_of(date: str) -> str:
    """The 24/7 tape's reading of "where in the week": the entry session's day of the week."""
    return WEEKDAY[datetime.strptime(date, "%Y-%m-%d").weekday()]


class IndexState:
    """Bitcoin's state at the trigger for a crypto unit, from BTC's own daily bars: its PREVIOUS
    session green or red, and its close at that session above or below its week's open (the
    census's week under the 24/7 calendar). Four states, all known at the trigger."""

    def __init__(self, btc_daily: list[dict]):
        self.by_date = {date_of(b["t"]): b for b in btc_daily}
        self.week_open: dict[str, float] = {}
        for b in aggregate(btc_daily, "W"):
            for i in b["days"]:
                self.week_open[date_of(btc_daily[i]["t"])] = b["o"]

    def at(self, entry_date: str) -> str | None:
        prev = (datetime.strptime(entry_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        b = self.by_date.get(prev)
        wo = self.week_open.get(prev)
        if b is None or wo is None:
            return None
        colour = "green" if b["c"] > b["o"] else "red" if b["c"] < b["o"] else "flat"
        side = "above" if b["c"] >= wo else "below"
        return f"{colour}-{side}"


def _cat(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return v


def card_vars(r: dict) -> dict:
    """The card-based variables: fields the engine fixed at the trigger."""
    ll = _f(r.get("ladder_len"))
    return {
        "v_setup_pct": _f(r.get("r_pct")),
        "v_room_r": room_r(r.get("level"), r.get("t1"), r.get("r_pct")),
        "cls": _cat(r.get("cls")),
        "near_tf": _cat(r.get("near_tf")) or "none",
        "anchor": _cat(r.get("anchor")),
        "ladder_len": None if ll is None else str(int(ll)),
        "flag": _cat(r.get("flag")),
        "dex": _cat(r.get("dex")),
    }
