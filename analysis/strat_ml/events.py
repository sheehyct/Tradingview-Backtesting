"""Phase 2: the STRAT trigger event table (one row per coin, day, direction).

Definitions: docs/experiments/strat_ml_phase2_events_design.md, fixed before this file ran on
data. The bar classifier, calendar and setup-kind come from analysis/domino/census.py (owner's
ruling 2026-10-17: reuse, do not rewrite); the stop (R) and the magnitude ladder are the TVB-37
management-book prereg's. Everything "as of the trigger hour" uses hourly bars strictly before
that hour or closed higher-timeframe bars; the trigger hour's own range is never a feature.

Research only. Fill at the level, no fees, no funding paid, no sizing: R is a measuring stick.

CLI:
  uv run python -m analysis.strat_ml.events build [--symbols BTCUSDT ...] [--workers 4]
  uv run python -m analysis.strat_ml.events summary
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.domino.census import (
    DAY,
    HOUR,
    _context,
    aggregate,
    classify,
    setup_kind,
    shape_flags,
)
from analysis.strat_ml.binance_vision import DATA, SUMMARY_PATH, load

HERE = Path(__file__).parent
EVENTS_PATH = DATA / "events.parquet"
EVENTS_SUMMARY = HERE / "events_summary.json"
MAJORS = frozenset({"BTCUSDT", "ETHUSDT"})
HORIZONS = (1, 3, 5, 10)
ATR_N = 14
PCT_WINDOW = 365
PCT_MIN = 60

# ----------------------------------------------------------------------------- bars


def to_ms(ts: pd.Series) -> np.ndarray:
    """tz-aware timestamps -> epoch ms, whatever the stored resolution (pandas 3 keeps ms)."""
    return ts.astype("datetime64[ms, UTC]").astype("int64").to_numpy()


def hourly_frame(symbol: str, last_traded: str | None) -> pd.DataFrame:
    """The cached 1h klines as ms-int columns, trimmed at the last real trade."""
    df = load(symbol, "klines")
    if last_traded:
        df = df[df["open_time"] <= pd.Timestamp(last_traded)]
    out = pd.DataFrame(
        {
            "t": to_ms(df["open_time"]),
            "o": df["open"].to_numpy(float),
            "h": df["high"].to_numpy(float),
            "l": df["low"].to_numpy(float),
            "c": df["close"].to_numpy(float),
            "v": df["volume"].to_numpy(float),
            "qv": df["quote_volume"].to_numpy(float),
        }
    )
    return out.drop_duplicates("t").sort_values("t").reset_index(drop=True)


def daily_from_hourly(hf: pd.DataFrame) -> pd.DataFrame:
    """Calendar-day bars (00:00 UTC) from hourly bars; a partial first day is dropped."""
    day = hf["t"] // DAY
    g = hf.groupby(day, sort=True)
    d = pd.DataFrame(
        {
            "t": g["t"].first().index.to_numpy() * DAY,
            "o": g["o"].first().to_numpy(),
            "h": g["h"].max().to_numpy(),
            "l": g["l"].min().to_numpy(),
            "c": g["c"].last().to_numpy(),
            "v": g["v"].sum().to_numpy(),
            "qv": g["qv"].sum().to_numpy(),
            "hours": g.size().to_numpy(),
            "first_t": g["t"].first().to_numpy(),
            "h0": np.array([ix[0] for ix in g.indices.values()]),  # first hourly index
        }
    )
    if len(d) and d["first_t"].iloc[0] != d["t"].iloc[0]:
        d = d.iloc[1:].reset_index(drop=True)
    return d


SESSION_TZ = "America/New_York"


def session_labels(
    t: np.ndarray, tz: str = SESSION_TZ
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per hourly bar: New York local hour, local calendar day (as a pseudo-UTC midnight in ms,
    so the census calendar helpers bucket weeks and months by the local date) and the session
    label: 'rth' = weekday, local hour 9..15 (the 9:00 bar holds the 9:30 open at hourly
    resolution: an approximation, stated), 'extended' = weekday 4..8 or 16..19, else 'overnight'
    (weekends included)."""
    loc = pd.to_datetime(t, unit="ms", utc=True).tz_convert(tz)
    hour = loc.hour.to_numpy()
    wd = loc.weekday.to_numpy()
    local_day = (
        pd.to_datetime(loc.strftime("%Y-%m-%d")).to_numpy().astype("datetime64[ms]").astype("int64")
    )
    weekday = wd < 5
    label = np.where(
        weekday & (hour >= 9) & (hour <= 15),
        "rth",
        np.where(
            weekday & (((hour >= 4) & (hour <= 8)) | ((hour >= 16) & (hour <= 19))),
            "extended",
            "overnight",
        ),
    )
    return hour, local_day, label


def session_bars(
    hf: pd.DataFrame, in_session: np.ndarray, local_day: np.ndarray
) -> tuple[pd.DataFrame, list]:
    """Regular-hours daily bars: one bar per LOCAL day from the in-session hours only. Returns the
    frame (same columns as daily_from_hourly) and, per bar, the hourly indices it is made of."""
    idx = np.flatnonzero(in_session)
    if len(idx) == 0:
        return pd.DataFrame(
            columns=["t", "o", "h", "l", "c", "v", "qv", "hours", "first_t", "h0"]
        ), []
    sub = hf.iloc[idx].copy()
    sub["_ld"] = local_day[idx]
    sub["_ix"] = idx
    g = sub.groupby("_ld", sort=True)
    d = pd.DataFrame(
        {
            "t": g["_ld"].first().to_numpy(),
            "o": g["o"].first().to_numpy(),
            "h": g["h"].max().to_numpy(),
            "l": g["l"].min().to_numpy(),
            "c": g["c"].last().to_numpy(),
            "v": g["v"].sum().to_numpy(),
            "qv": g["qv"].sum().to_numpy(),
            "hours": g.size().to_numpy(),
            "first_t": g["t"].first().to_numpy(),
            "h0": g["_ix"].first().to_numpy(),
        }
    )
    hidx = [list(map(int, v)) for v in g["_ix"].apply(list)]
    return d, hidx


def session_aggregate(daily: list[dict], tf: str, session: str = "calendar") -> list[dict]:
    """The census's calendar buckets; in rth mode a bucket is complete when it is OVER (its end is
    at or before the day after the last session bar), because session days skip weekends and
    holidays and the census's every-calendar-day rule would leave every week incomplete."""
    buckets = aggregate(daily, tf)
    if session == "rth" and daily:
        last_end = daily[-1]["t"] + DAY
        for b in buckets:
            b["complete"] = b["end"] <= last_end
    return buckets


def types_of(h: np.ndarray, l: np.ndarray) -> list[str | None]:  # noqa: E741
    """Strict-break types via the census classifier (literal reuse); first bar None."""
    out: list[str | None] = [None]
    for i in range(1, len(h)):
        out.append(classify({"h": h[i], "l": l[i]}, {"h": h[i - 1], "l": l[i - 1]}))
    return out


def wilder_atr(d: pd.DataFrame, n: int = ATR_N) -> np.ndarray:
    pc = d["c"].shift(1)
    tr = pd.concat([d["h"] - d["l"], (d["h"] - pc).abs(), (d["l"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean().to_numpy()


def rolling_pct(s: pd.Series, window: int = PCT_WINDOW, min_periods: int = PCT_MIN) -> np.ndarray:
    return s.rolling(window, min_periods=min_periods).rank(pct=True).to_numpy()


# ----------------------------------------------------------------------------- pattern / levels


def bar_color(bar: dict) -> int:
    return 1 if bar["c"] > bar["o"] else -1 if bar["c"] < bar["o"] else 0


def pattern_name(t1: str, t2: str | None, direction: str, bar2: dict | None) -> tuple[str, str]:
    """(name, family) from the setup bar type t1, the bar-before type t2 and the break direction.

    The design doc's table (skill 3.1 router; reversal vs continuation for X-1-2 by bar 0's
    direction, a Type 3 bar 0 by its close colour).
    """
    with_dir = "2U" if direction == "up" else "2D"
    against = "2D" if direction == "up" else "2U"
    family = setup_kind(t1, direction)
    if t1 == "3":
        return "3-2 outside break", family
    if t1 == "1":
        if t2 == "1":
            return "1-1-2 stacked inside", family
        if t2 == "3":
            col = bar_color(bar2) if bar2 is not None else 0
            same = (col > 0) == (direction == "up") and col != 0
            return ("3-1-2 continuation" if same else "3-1-2 reversal"), family
        if t2 == with_dir:
            return "2-1-2 continuation", family
        if t2 == against:
            return "2-1-2 reversal", family
        return "x-1-2 (no bar before)", family
    if t1 == against:
        if t2 == "1":
            return "1-2-2 rev strat", family
        if t2 == "3":
            return "3-2-2 reversal", family
        return "2-2 reversal", family
    return "2-2 continuation", family


def far_side(bar: dict, direction: str) -> float:
    """The wick on the trade's side: high for a long, low for a short."""
    return bar["h"] if direction == "up" else bar["l"]


def near_side(bar: dict, direction: str) -> float:
    return bar["l"] if direction == "up" else bar["h"]


def bar0_index(dtypes: list, i: int) -> int:
    """Bar 0 of an inside break on day i (setup bar i-1 is Type 1): walk back from i-2 past any
    further inside bars; the first non-inside bar's range contains the whole coil (skill 3.2).
    Falls back to i-2 when the walk runs out of classified bars."""
    j = i - 2
    while j - 1 >= 0 and dtypes[j] == "1":
        j -= 1
    return j


def beyond(price: float, level: float, direction: str) -> bool:
    return price > level if direction == "up" else price < level


def ladder_rungs(direction: str, level: float, wm: dict) -> list[tuple[float, str]]:
    """Previous complete week / month levels strictly beyond L and unbroken before the trigger hour,
    nearest first. wm[tf] = (prev_level, partial_extreme_before) with None where unknown."""
    rungs = []
    for tf in ("W", "M"):
        prev_level, partial = wm.get(tf, (None, None))
        if prev_level is None:
            continue
        if not beyond(prev_level, level, direction):
            continue
        broken = partial is not None and beyond(partial, prev_level, direction)
        if not broken:
            rungs.append((prev_level, tf))
    rungs.sort(key=lambda r: abs(r[0] - level))
    return rungs


PIVOT_LOOKBACK = 250  # the Pine / paper-engine history cap
PIVOT_LEVELS = 6  # extTargets 5 + Target 1


def pivot_ladder(
    daily: list[dict], i: int, direction: str, t1: str, t2: str | None
) -> tuple[list[float], str]:
    """The owner's Pine ladder (TheStrat Magnitude + Targets; analysis/paper/patterns.py port) on
    daily bars for the break on day i: anchors first, then prior highs (lows) NOT yet taken out,
    nearest first, strict breaks, capped at PIVOT_LEVELS and PIVOT_LOOKBACK bars.

    Anchor rules as the Pine writes them (setup bar = i-1, bar 0 = i-2, i-3 where named):
      2-2 reversal / 3-2-2 / shot-gun: anchor = bar 0's far wick; 1-2-2: anchor = the inside bar
      (i-2) far wick, anchor2 = i-3's far wick when the setup bar traded through i-3's near side;
      X-1-2 (every inside break, with or against): anchor = i-2's far wick (the reclaim level);
      1-3-2: anchor = i-3's far wick; bare 3-2 and the 2-2 continuation: no anchor, the ladder
      starts at the trigger. Returns (levels nearest first, anchor_source).
    """
    setup = daily[i - 1]
    level = far_side(setup, direction)
    bar2 = daily[i - 2] if i >= 2 else None
    bar3 = daily[i - 3] if i >= 3 else None
    against = "2D" if direction == "up" else "2U"
    ladder: list[float] = []
    src = "trigger"
    if bar2 is not None and t1 == against:
        ladder.append(far_side(bar2, direction))
        src = "bar0_wick"
        if t2 == "1" and bar3 is not None:
            crossed = setup["l"] < bar3["l"] if direction == "up" else setup["h"] > bar3["h"]
            if crossed:
                ladder.append(far_side(bar3, direction))
                src = "inside_then_bar0"
    elif bar2 is not None and t1 == "1":
        ladder.append(far_side(bar2, direction))
        src = "reclaim_bar0"
    elif t1 == "3" and t2 == "1" and bar3 is not None:
        ladder.append(far_side(bar3, direction))
        src = "bar_before_outside"
    ladder = [x for x in ladder if beyond(x, level, direction)]
    run = ladder[-1] if ladder else level
    for j in range(i - 1, max(-1, i - 1 - PIVOT_LOOKBACK), -1):
        if len(ladder) >= PIVOT_LEVELS:
            break
        v = far_side(daily[j], direction)
        if beyond(v, run, direction):
            ladder.append(v)
            run = v
    return ladder, src


def magnitude(
    name: str, family: str, direction: str, level: float, bar2: dict | None, rungs: list
) -> tuple[float | None, str | None]:
    """T1 per the TVB-37 management-book prereg definition 5 (the design doc's section 4)."""
    anchor = family == "reversal" or name in (
        "2-1-2 reversal",
        "3-1-2 reversal",
        "3-1-2 continuation",
    )
    if anchor:
        if bar2 is None:
            return None, None
        t1 = far_side(bar2, direction)
        return (t1, "bar0_wick") if beyond(t1, level, direction) else (None, "zero_magnitude")
    if rungs:
        return rungs[0][0], "ladder_" + rungs[0][1]
    return None, "no_rung"


# ----------------------------------------------------------------------------- per-symbol engine


def symbol_events(
    symbol: str,
    hf: pd.DataFrame,
    liq_rank: pd.Series | None = None,
    btc_ctx: pd.DataFrame | None = None,
    funding: pd.DataFrame | None = None,
    stop_mode: str = "setup",
    session: str = "calendar",
    asset_class: str | None = None,
) -> tuple[pd.DataFrame, dict]:
    """All trigger rows of one symbol. Pure function of the frames passed in (testable).

    session: "calendar" = the 00:00 UTC day (24/7 perps, every row so far); "rth" = the STRAT
    daily bar is the New York regular session (weekday local hours 9..15) built from those hours
    only, keyed by the local date, triggers scanned inside the session only; the outcome walk
    still runs over every hour (a held position lives 24/7). Weeks and months follow the local
    calendar in rth mode. The trigger hour's session label rides every row in both modes.

    stop_mode: "setup" = the far side of the setup bar for every pattern (TVB-37 R);
    "bar0" = for an inside break (setup bar Type 1) the far side of bar 0, the first non-inside
    bar walking back from the bar before the setup bar (skill 5.2 structural stop, production
    ruling: bar 0, NOT the inside bar); every other pattern unchanged.
    """
    if stop_mode not in ("setup", "bar0"):
        raise ValueError(stop_mode)
    if session not in ("calendar", "rth"):
        raise ValueError(session)
    drops: dict[str, int] = {"no_setup_type": 0, "zero_range": 0, "no_levels": 0}
    local_hour, local_day, sess_label = session_labels(hf["t"].to_numpy())
    if session == "rth":
        d, day_hidx = session_bars(hf, sess_label == "rth", local_day)
    else:
        d = daily_from_hourly(hf)
        day_hidx = None
    if len(d) < 4:
        return pd.DataFrame(), drops
    daily = [
        {"t": int(r.t), "o": r.o, "h": r.h, "l": r.l, "c": r.c, "v": r.v}
        for r in d.itertuples(index=False)
    ]
    dtypes = types_of(d["h"].to_numpy(), d["l"].to_numpy())
    atr = wilder_atr(d)
    atr_pct = rolling_pct(pd.Series(atr))
    vol20 = d["v"].shift(1).rolling(20, min_periods=10).mean().to_numpy()
    buckets = {tf: session_aggregate(daily, tf, session) for tf in ("W", "M", "Q")}
    ctx = _context(daily, buckets)
    first_day = d["t"].iloc[0]

    t = hf["t"].to_numpy()
    h = hf["h"].to_numpy()
    l = hf["l"].to_numpy()  # noqa: E741
    c = hf["c"].to_numpy()
    v = hf["v"].to_numpy()
    n = len(t)
    day_of_hour = t // DAY
    # hourly types (previous hour vs the one before), same strict rule as the classifier
    up = np.r_[False, h[1:] > h[:-1]]
    dn = np.r_[False, l[1:] < l[:-1]]
    htype = np.where(up & dn, "3", np.where(up, "2U", np.where(dn, "2D", "1")))
    htype[0] = ""
    vol168 = pd.Series(v).shift(1).rolling(168, min_periods=48).mean().to_numpy()
    # 4H groups: partial-before-hour extremes and the previous complete 4H bar
    g4 = t // (4 * HOUR)
    s4 = pd.Series(np.arange(n))
    grp = s4.groupby(g4)
    h4_run_h = pd.Series(h).groupby(g4).cummax().shift(1).to_numpy().copy()
    h4_run_l = pd.Series(l).groupby(g4).cummin().shift(1).to_numpy().copy()
    first_in_g4 = grp.transform("first").to_numpy() == np.arange(n)
    h4_run_h[first_in_g4] = np.nan
    h4_run_l[first_in_g4] = np.nan
    g4_h = pd.Series(h).groupby(g4).max()
    g4_l = pd.Series(l).groupby(g4).min()
    prev_g4 = pd.Series(g4) - 1
    h4_prev_h = prev_g4.map(g4_h).to_numpy()
    h4_prev_l = prev_g4.map(g4_l).to_numpy()
    # effective touch arrays: a zero-volume hour is a flat placeholder, not a print
    h_eff = np.where(v > 0, h, np.nan)
    l_eff = np.where(v > 0, l, np.nan)

    rows = []
    for i in range(2, len(d)):
        t1 = dtypes[i - 1]
        if t1 is None:
            drops["no_setup_type"] += 1
            continue
        setup = daily[i - 1]
        bar2 = daily[i - 2] if i >= 2 else None
        t2 = dtypes[i - 2]
        if setup["h"] - setup["l"] <= 0:
            drops["zero_range"] += 1
            continue
        k0 = int(d["h0"].iloc[i])
        if day_hidx is None:
            k1 = int(d["h0"].iloc[i + 1]) if i + 1 < len(d) else n
            hidx = np.arange(k0, k1)
        else:
            hidx = np.asarray(day_hidx[i])
        hh, ll = h[hidx], l[hidx]
        brk = {"up": np.flatnonzero(hh > setup["h"]), "down": np.flatnonzero(ll < setup["l"])}
        both = len(brk["up"]) > 0 and len(brk["down"]) > 0
        for direction, idx in brk.items():
            if len(idx) == 0:
                continue
            pos = int(idx[0])  # position inside the day's (session) hours
            k = int(hidx[pos])
            level = setup["h"] if direction == "up" else setup["l"]
            setup_stop = near_side(setup, direction)
            if setup["h"] - setup["l"] <= 0:
                drops["zero_range"] += 1
                continue
            j0 = bar0_index(dtypes, i) if t1 == "1" else None
            bar0_stop = near_side(daily[j0], direction) if j0 is not None else setup_stop
            if stop_mode == "bar0" and t1 == "1":
                stop, alt_stop, stop_src = bar0_stop, setup_stop, "bar0"
            else:
                stop, alt_stop, stop_src = setup_stop, bar0_stop, "setup_bar"
            r = abs(level - stop)
            if r <= 0:
                drops["zero_range"] += 1
                continue
            name, family = pattern_name(t1, t2, direction, bar2)
            # partial week / month before hour k
            wm: dict[str, tuple] = {}
            part: dict[str, dict] = {}
            for tf in ("W", "M"):
                cx = ctx[tf].get(i)
                if cx is None:
                    part[tf] = {}
                    continue
                run_h, run_l = cx["run_h"], cx["run_l"]
                if pos > 0:
                    dh, dl = hh[:pos].max(), ll[:pos].min()
                    run_h = dh if run_h is None else max(run_h, dh)
                    run_l = dl if run_l is None else min(run_l, dl)
                prev = cx["prev"]
                ptype = None
                if run_h is not None and prev is not None:
                    ptype = classify({"h": run_h, "l": run_l}, prev)
                color = 0
                if pos > 0 or cx["run_h"] is not None:
                    pc = c[k - 1]
                    color = 1 if pc > cx["open"] else -1 if pc < cx["open"] else 0
                part[tf] = {
                    "type": ptype,
                    "prev_type": cx["prev_type"],
                    "color": color,
                    "run_h": run_h,
                    "run_l": run_l,
                    "prev": prev,
                }
                if prev is not None:
                    lvl = far_side(prev, direction)
                    partial = run_h if direction == "up" else run_l
                    wm[tf] = (lvl, partial)
            rungs = ladder_rungs(direction, level, wm)
            t1_price, t1_src = magnitude(name, family, direction, level, bar2, rungs)
            # alignment scores (skill 4.3 and the colour-only version)
            aligned = []
            biased = []
            for tf in ("W", "M"):
                p = part.get(tf, {})
                col = p.get("color", 0)
                want = 1 if direction == "up" else -1
                ty = p.get("type")
                ok = col == want and (ty == ("2U" if direction == "up" else "2D") or ty == "3")
                aligned.append(1.0 if ok else 0.0)
                biased.append(1.0 if col == want else 0.0)
            breaks_w = False
            breaks_m = False
            for tf, flag in (("W", "breaks_w"), ("M", "breaks_m")):
                lvl, partial = wm.get(tf, (None, None))
                if lvl is not None:
                    unbroken = partial is None or not beyond(partial, lvl, direction)
                    hit = unbroken and (level >= lvl if direction == "up" else level <= lvl)
                    if tf == "W":
                        breaks_w = hit
                    else:
                        breaks_m = hit
            # 4H / 1H
            h4_type = None
            if not np.isnan(h4_run_h[k]) and not np.isnan(h4_prev_h[k]):
                h4_type = classify(
                    {"h": h4_run_h[k], "l": h4_run_l[k]}, {"h": h4_prev_h[k], "l": h4_prev_l[k]}
                )
            h4_broke = h4_type in (("2U", "3") if direction == "up" else ("2D", "3"))
            # outcomes
            out = {}
            end_idx = {}
            for hz in HORIZONS:
                e = int(np.searchsorted(day_of_hour, day_of_hour[k0] + hz + 1)) - 1
                end_idx[hz] = e
            e10 = end_idx[10]
            win_h = h_eff[k : e10 + 1]
            win_l = l_eff[k : e10 + 1]
            sign = 1.0 if direction == "up" else -1.0
            fav = (win_h - level) * sign if direction == "up" else (level - win_l)
            adv = (level - win_l) if direction == "up" else (win_h - level)
            cum_fav = np.fmax.accumulate(np.where(np.isnan(fav), -np.inf, fav))
            cum_adv = np.fmax.accumulate(np.where(np.isnan(adv), -np.inf, adv))
            stop_hits = np.flatnonzero((win_l <= stop) if direction == "up" else (win_h >= stop))
            tgt_hits = (
                np.flatnonzero((win_h >= t1_price) if direction == "up" else (win_l <= t1_price))
                if t1_price is not None
                else np.array([], dtype=int)
            )
            s_idx = int(stop_hits[0]) if len(stop_hits) else None
            g_idx = int(tgt_hits[0]) if len(tgt_hits) else None
            ambiguous = (s_idx is not None and g_idx is not None and s_idx == g_idx) or (s_idx == 0)
            if s_idx is not None and (g_idx is None or s_idx <= g_idx):
                first_touch, touch_at = "stop", s_idx
            elif g_idx is not None:
                first_touch, touch_at = "target", g_idx
            else:
                first_touch, touch_at = "timeout", None
            for hz in HORIZONS:
                e = end_idx[hz]
                want_end = (day_of_hour[k0] + hz) * DAY + 23 * HOUR
                cens = t[e] < want_end if e >= 0 else True
                # Codex PR #3 P2: an hourly gap INSIDE the window hides prices the walk never saw
                if not cens and (e - k + 1) != (t[e] - t[k]) // HOUR + 1:
                    cens = True
                w = e - k
                if cens or w < 0:
                    out[f"mfe_r_{hz}"] = out[f"mae_r_{hz}"] = out[f"r_close_{hz}"] = np.nan
                    out[f"r_managed_{hz}"] = np.nan
                    continue
                mfe = cum_fav[w]
                mae = cum_adv[w]
                out[f"mfe_r_{hz}"] = mfe / r
                out[f"mae_r_{hz}"] = mae / r
                out[f"r_close_{hz}"] = (c[e] - level) * sign / r
                if first_touch == "stop" and touch_at <= w:
                    out[f"r_managed_{hz}"] = -1.0
                elif first_touch == "target" and touch_at <= w:
                    out[f"r_managed_{hz}"] = abs(t1_price - level) / r
                else:
                    out[f"r_managed_{hz}"] = out[f"r_close_{hz}"]
            # the excursion clock (owner's question 2026-10-20): hourly bars from entry to the
            # first touch of +x R in favour / x R against, which 0.25R came first, and the
            # excursions and the mark at fixed clock hours (NaN when the window is shorter)
            for x, tag in ((0.25, "025"), (0.5, "05"), (1.0, "1")):
                fi = np.flatnonzero(fav >= x * r)
                ai = np.flatnonzero(adv >= x * r)
                out[f"h_fav_{tag}"] = float(fi[0]) if len(fi) else np.nan
                out[f"h_adv_{tag}"] = float(ai[0]) if len(ai) else np.nan
            f25, a25 = out["h_fav_025"], out["h_adv_025"]
            if np.isnan(f25) and np.isnan(a25):
                out["first_excursion"] = "none"
            elif np.isnan(a25) or (not np.isnan(f25) and f25 < a25):
                out["first_excursion"] = "fav"
            else:
                out["first_excursion"] = "adv"  # tie inside one hour -> against (pessimistic)
            n_win = len(fav)
            for ch in (6, 12, 24, 48, 72):
                ok = ch <= n_win and t[k + ch - 1] - t[k] == (ch - 1) * HOUR
                out[f"mfe_r_{ch}h"] = cum_fav[ch - 1] / r if ok else np.nan
                out[f"mae_r_{ch}h"] = cum_adv[ch - 1] / r if ok else np.nan
                out[f"r_close_{ch}h"] = (c[k + ch - 1] - level) * sign / r if ok else np.nan
            # the Pine pivot ladder (owner, 2026-10-20: "this is where drift is happening"):
            # rungs reached within the 10-bar window under the TVB-22 census's REACH convention
            # (favourable extreme at or past the rung), hours to the first three rungs, and the
            # managed result when the Pine's T1 replaces the TVB-37 T1 (same stop, same walk)
            rungs, rung_src = pivot_ladder(daily, i, direction, t1, t2)
            hrs = []
            for lvl_ in rungs:
                hit = np.flatnonzero((win_h >= lvl_) if direction == "up" else (win_l <= lvl_))
                hrs.append(float(hit[0]) if len(hit) else np.nan)
            reached = 0
            for hv in hrs:
                if np.isnan(hv):
                    break
                reached += 1
            out["pivot_rungs"] = len(rungs)
            out["pivot_src"] = rung_src
            out["pivot_t1"] = rungs[0] if rungs else np.nan
            out["pivot_t1_dist_r"] = abs(rungs[0] - level) / r if rungs else np.nan
            out["pivot_t3_dist_r"] = abs(rungs[2] - level) / r if len(rungs) >= 3 else np.nan
            out["pivot_reached_10"] = reached
            for q in range(3):
                out[f"h_rung{q + 1}"] = hrs[q] if q < len(hrs) else np.nan
            if rungs:
                p_idx = int(hrs[0]) if not np.isnan(hrs[0]) else None
                if s_idx is not None and (p_idx is None or s_idx <= p_idx):
                    out["pivot_first_touch"] = "stop"
                    out["r_managed_pivot_10"] = -1.0
                elif p_idx is not None:
                    out["pivot_first_touch"] = "target"
                    out["r_managed_pivot_10"] = out["pivot_t1_dist_r"]
                else:
                    out["pivot_first_touch"] = "timeout"
                    out["r_managed_pivot_10"] = out.get("r_close_10", np.nan)
            else:
                out["pivot_first_touch"] = "none"
                out["r_managed_pivot_10"] = np.nan
            a = atr[i - 1]
            third, strict = shape_flags(setup, direction)
            pw, pm = part.get("W", {}), part.get("M", {})
            row = {
                "symbol": symbol,
                "asset_class": asset_class or ("major" if symbol in MAJORS else "alt"),
                "session_mode": session,
                "trigger_session": str(sess_label[k]),
                "local_hour": int(local_hour[k]),
                "trigger_tf": "1D",
                "direction": "long" if direction == "up" else "short",
                "pattern": name,
                "family": family,
                "sequence": f"{t2 or '?'}-{t1}-{'2U' if direction == 'up' else '2D'}",
                "trigger_time": int(t[k]),
                "day": int(d["t"].iloc[i]),
                "hours_since_daily_open": pos,
                "day_of_week": int(
                    datetime.fromtimestamp(d["t"].iloc[i] / 1000, tz=timezone.utc).weekday()
                ),
                "symbol_age_days": int((d["t"].iloc[i] - first_day) // DAY),
                "opposite_also_triggered": bool(both),
                "level": level,
                "stop": stop,
                "r": r,
                "stop_alt_r": abs(level - alt_stop) / r,
                "stop_mode": stop_mode,
                "stop_src": stop_src,
                "stop_bar_offset": (i - 1 - j0) if j0 is not None else 0,
                "t1": t1_price,
                "t1_source": t1_src,
                "has_target": t1_price is not None,
                "t1_dist_r": abs(t1_price - level) / r if t1_price is not None else np.nan,
                "t1_dist_atr": abs(t1_price - level) / a
                if t1_price is not None and a and not np.isnan(a)
                else np.nan,
                "atr": a,
                "atr_pct_1y": atr_pct[i - 1],
                "setup_range_atr": (setup["h"] - setup["l"]) / a
                if a and not np.isnan(a)
                else np.nan,
                "stop_atr": r / a if a and not np.isnan(a) else np.nan,
                "setup_color": bar_color(setup),
                "setup_dcr": (setup["c"] - setup["l"]) / (setup["h"] - setup["l"]),
                "setup_third": bool(third),
                "setup_strict": bool(strict),
                "bar2_type": t2,
                "w_partial_type": pw.get("type"),
                "m_partial_type": pm.get("type"),
                "w_prev_type": pw.get("prev_type"),
                "m_prev_type": pm.get("prev_type"),
                "w_bias": pw.get("color", 0),
                "m_bias": pm.get("color", 0),
                "tfc_score": float(np.mean(aligned)),
                "bias_score": float(np.mean(biased)),
                "breaks_week_too": bool(breaks_w),
                "breaks_month_too": bool(breaks_m),
                "h4_partial_type": h4_type,
                "h4_broke_before": bool(h4_broke),
                "h1_prev_type": htype[k - 1] if k >= 1 else None,
                "relvol_d1": setup["v"] / vol20[i - 1]
                if vol20[i - 1] and not np.isnan(vol20[i - 1])
                else np.nan,
                "relvol_prev_hour": v[k - 1] / vol168[k]
                if k >= 1 and vol168[k] and not np.isnan(vol168[k])
                else np.nan,
                "liq_rank": float(liq_rank.get(int(d["t"].iloc[i - 1]), np.nan))
                if liq_rank is not None
                else np.nan,
                "first_touch": first_touch,
                "touch_hours": touch_at,
                "ambiguous": bool(ambiguous),
                "censored": bool(np.isnan(out.get("r_managed_10", np.nan))),
                "window_gap_hours": int((t[e10] - t[k]) // HOUR + 1 - (e10 - k + 1))
                if e10 >= k
                else 0,
                **out,
            }
            rows.append(row)
    df = pd.DataFrame(rows)
    if len(df):
        df["liq_tier"] = pd.cut(df["liq_rank"], [0, 10, 50, 10_000], labels=[1, 2, 3]).astype(
            "float"
        )
        if funding is not None and len(funding):
            df = attach_funding(df, funding)
        if btc_ctx is not None:
            df = attach_btc(df, btc_ctx)
    return df, drops


# ----------------------------------------------------------------------------- joins


def attach_funding(df: pd.DataFrame, funding: pd.DataFrame) -> pd.DataFrame:
    f = funding.sort_values("t").reset_index(drop=True)
    s = pd.Series(f["rate"].to_numpy(), index=pd.to_datetime(f["t"], unit="ms", utc=True))
    f["funding_7d"] = s.rolling("7D", min_periods=3).mean().to_numpy()
    f["funding_pct_1y"] = s.rolling("365D", min_periods=60).rank(pct=True).to_numpy()
    f = f.rename(columns={"rate": "funding_last"})
    left = df.sort_values("trigger_time")
    merged = pd.merge_asof(
        left,
        f[["t", "funding_last", "funding_7d", "funding_pct_1y"]],
        left_on="trigger_time",
        right_on="t",
        direction="backward",
    )
    return merged.drop(columns=["t"]).sort_index()


def funding_frame(symbol: str) -> pd.DataFrame:
    try:
        f = load(symbol, "fundingRate")
    except FileNotFoundError:
        return pd.DataFrame(columns=["t", "rate"])
    return pd.DataFrame(
        {
            "t": to_ms(f["calc_time"]),
            "rate": f["last_funding_rate"].to_numpy(float),
        }
    )


def btc_context(hf: pd.DataFrame) -> pd.DataFrame:
    """Per hour: BTC's partial-day type before that hour, its week / month colour, 30d realized-vol
    percentile as of the previous day. Indexed by hour open time (ms)."""
    d = daily_from_hourly(hf)
    daily = [
        {"t": int(r.t), "o": r.o, "h": r.h, "l": r.l, "c": r.c, "v": r.v}
        for r in d.itertuples(index=False)
    ]
    t = hf["t"].to_numpy()
    h, l, c = hf["h"].to_numpy(), hf["l"].to_numpy(), hf["c"].to_numpy()  # noqa: E741
    day = t // DAY
    run_h = pd.Series(h).groupby(day).cummax().shift(1).to_numpy().copy()
    run_l = pd.Series(l).groupby(day).cummin().shift(1).to_numpy().copy()
    first = pd.Series(np.arange(len(t))).groupby(day).transform("first").to_numpy() == np.arange(
        len(t)
    )
    run_h[first] = np.nan
    run_l[first] = np.nan
    dmap = {int(r.t): (r.h, r.l) for r in d.itertuples(index=False)}
    prev_h = np.array([dmap.get(int(dd * DAY - DAY), (np.nan, np.nan))[0] for dd in day])
    prev_l = np.array([dmap.get(int(dd * DAY - DAY), (np.nan, np.nan))[1] for dd in day])
    ptype = []
    for i in range(len(t)):
        if np.isnan(run_h[i]) or np.isnan(prev_h[i]):
            ptype.append(None)
        else:
            ptype.append(classify({"h": run_h[i], "l": run_l[i]}, {"h": prev_h[i], "l": prev_l[i]}))
    buckets = {tf: aggregate(daily, tf) for tf in ("W", "M", "Q")}
    ctx = _context(daily, buckets)
    day_index = {int(r.t): i for i, r in enumerate(d.itertuples(index=False))}
    prev_close = np.r_[np.nan, c[:-1]]
    wb, mb = [], []
    for i in range(len(t)):
        di = day_index.get(int(day[i] * DAY))
        for tf, acc in (("W", wb), ("M", mb)):
            cx = ctx[tf].get(di) if di is not None else None
            if cx is None or np.isnan(prev_close[i]) or (cx["run_h"] is None and first[i]):
                acc.append(0)
            else:
                acc.append(
                    1 if prev_close[i] > cx["open"] else -1 if prev_close[i] < cx["open"] else 0
                )
    lr = np.log(d["c"] / d["c"].shift(1))
    rv30 = lr.rolling(30, min_periods=20).std()
    rv_pct = rolling_pct(rv30)
    rv_by_day = {int(r): p for r, p in zip(d["t"].to_numpy(), rv_pct)}
    rv = np.array([rv_by_day.get(int(dd * DAY - DAY), np.nan) for dd in day])
    return pd.DataFrame(
        {
            "t": t,
            "btc_day_partial_type": ptype,
            "btc_w_bias": wb,
            "btc_m_bias": mb,
            "btc_rv30_pct": rv,
        }
    )


def attach_btc(df: pd.DataFrame, btc: pd.DataFrame) -> pd.DataFrame:
    left = df.sort_values("trigger_time")
    merged = pd.merge_asof(left, btc, left_on="trigger_time", right_on="t", direction="backward")
    return merged.drop(columns=["t"]).sort_index()


def liquidity_ranks(daily_qv: dict[str, pd.Series]) -> pd.DataFrame:
    """days x symbols rank (1 = most quote volume) of the trailing-30-day mean daily quote volume."""
    wide = pd.DataFrame(daily_qv).sort_index()
    roll = wide.rolling(30, min_periods=10).mean()
    return roll.rank(axis=1, ascending=False, method="min")


# ----------------------------------------------------------------------------- driver


def _roster(path: Path = SUMMARY_PATH) -> dict:
    return json.loads(path.read_text())["rows"]


def _daily_qv(symbol: str, last_traded: str | None) -> tuple[str, pd.Series]:
    hf = hourly_frame(symbol, last_traded)
    d = daily_from_hourly(hf)
    return symbol, pd.Series(d["qv"].to_numpy(), index=d["t"].to_numpy())


_G: dict = {}


def _init(
    btc: pd.DataFrame,
    ranks: pd.DataFrame,
    stop_mode: str = "setup",
    session: str = "calendar",
    classes: dict | None = None,
) -> None:
    _G["btc"] = btc
    _G["ranks"] = ranks
    _G["stop_mode"] = stop_mode
    _G["session"] = session
    _G["classes"] = classes or {}


def _one(args) -> tuple[str, pd.DataFrame, dict, float]:
    symbol, last_traded = args
    t0 = time.time()
    try:
        hf = hourly_frame(symbol, last_traded)
    except FileNotFoundError:  # a roster symbol with nothing in the cache (pinned pulls)
        return symbol, pd.DataFrame(), {"no_parquet": 1}, time.time() - t0
    ranks = _G.get("ranks")
    liq = ranks[symbol].dropna() if ranks is not None and symbol in ranks else None
    df, drops = symbol_events(
        symbol,
        hf,
        liq,
        _G.get("btc"),
        funding_frame(symbol),
        _G.get("stop_mode", "setup"),
        _G.get("session", "calendar"),
        _G.get("classes", {}).get(symbol),
    )
    return symbol, df, drops, time.time() - t0


def build_tag(stop_mode: str = "setup", session: str = "calendar", roster_tag: str = "") -> str:
    parts = [
        roster_tag,
        session if session != "calendar" else "",
        stop_mode if stop_mode != "setup" else "",
    ]
    return "_".join(x for x in parts if x)


def events_path(stop_mode: str, session: str = "calendar", roster_tag: str = "") -> Path:
    tag = build_tag(stop_mode, session, roster_tag)
    return EVENTS_PATH if not tag else DATA / f"events_{tag}.parquet"


def summary_path(stop_mode: str, session: str = "calendar", roster_tag: str = "") -> Path:
    tag = build_tag(stop_mode, session, roster_tag)
    return EVENTS_SUMMARY if not tag else HERE / f"events_summary_{tag}.json"


def build(
    symbols: list[str] | None = None,
    workers: int = 4,
    log=print,
    stop_mode: str = "setup",
    session: str = "calendar",
    roster_path: Path = SUMMARY_PATH,
    roster_tag: str = "",
) -> pd.DataFrame:
    roster = _roster(roster_path)
    classes = {s: ("equity_perp" if s.startswith("XYZ_") else None) for s in roster}
    syms = sorted(symbols or roster.keys())
    t0 = time.time()
    log(f"pass 1: daily quote volume for the liquidity rank ({len(roster)} symbols)")
    qv: dict[str, pd.Series] = {}
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for sym, s in ex.map(
            _daily_qv, roster.keys(), [roster[s]["last_traded"] for s in roster.keys()], chunksize=8
        ):
            qv[sym] = s
    ranks = liquidity_ranks(qv)
    log(f"  ranks: {ranks.shape[0]} days x {ranks.shape[1]} symbols, {time.time() - t0:.0f}s")
    btc_last = (roster.get("BTCUSDT") or _roster(SUMMARY_PATH)["BTCUSDT"])["last_traded"]
    btc = btc_context(hourly_frame("BTCUSDT", btc_last))
    log(f"  BTC context: {len(btc)} hours")
    frames, drops, slow = [], {}, []
    with ProcessPoolExecutor(
        max_workers=workers, initializer=_init, initargs=(btc, ranks, stop_mode, session, classes)
    ) as ex:
        futs = [ex.submit(_one, (s, roster[s]["last_traded"])) for s in syms]
        for n, f in enumerate(as_completed(futs), 1):
            sym, df, dr, secs = f.result()
            frames.append(df)
            for k, v in dr.items():
                drops[k] = drops.get(k, 0) + v
            slow.append((secs, sym))
            if n % 50 == 0 or n == len(syms):
                log(
                    f"  [{n}/{len(syms)} {time.time() - t0:.0f}s] rows so far {sum(len(x) for x in frames)}"
                )
    ev = pd.concat([f for f in frames if len(f)], ignore_index=True)
    ev["trigger_ts"] = pd.to_datetime(ev["trigger_time"], unit="ms", utc=True)
    ev["day_ts"] = pd.to_datetime(ev["day"], unit="ms", utc=True)
    if "session_class" not in ev.columns:
        extra = {s: r.get("session_class") for s, r in roster.items()}
        ev["session_class"] = ev["symbol"].map(extra)
    out = events_path(stop_mode, session, roster_tag)
    out.parent.mkdir(parents=True, exist_ok=True)
    ev.to_parquet(out, index=False)
    write_summary(
        ev, drops, time.time() - t0, len(syms), summary_path(stop_mode, session, roster_tag)
    )
    log(f"  {len(ev)} rows -> {out}; drops {drops}; slowest {sorted(slow)[-3:]}")
    return ev


def write_summary(
    ev: pd.DataFrame, drops: dict, secs: float, n_symbols: int, path: Path = EVENTS_SUMMARY
) -> dict:
    by = ev.groupby(["pattern", "asset_class", "direction"]).size()
    doc = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seconds": round(secs),
        "symbols": n_symbols,
        "rows": int(len(ev)),
        "rows_with_target": int(ev["has_target"].sum()),
        "rows_censored": int(ev["censored"].sum()),
        "rows_ambiguous": int(ev["ambiguous"].sum()),
        "first_day": ev["day_ts"].min().strftime("%Y-%m-%d"),
        "last_day": ev["day_ts"].max().strftime("%Y-%m-%d"),
        "drops": drops,
        "counts": {" | ".join(k): int(v) for k, v in by.items()},
        "first_touch": {k: int(v) for k, v in ev["first_touch"].value_counts().items()},
    }
    doc["stop_mode"] = str(ev["stop_mode"].iloc[0]) if "stop_mode" in ev else "setup"
    path.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    return doc


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--symbols", nargs="*", default=None)
    b.add_argument("--workers", type=int, default=4)
    b.add_argument("--stop-mode", default="setup", choices=["setup", "bar0"])
    b.add_argument("--session", default="calendar", choices=["calendar", "rth"])
    b.add_argument("--roster", default=None, help="roster json (default: the Binance universe)")
    b.add_argument("--roster-tag", default="", help="file tag for a non-default roster, e.g. xyz")
    sub.add_parser("summary")
    a = ap.parse_args(argv)
    if a.cmd == "build":
        build(
            a.symbols,
            a.workers,
            stop_mode=a.stop_mode,
            session=a.session,
            roster_path=Path(a.roster) if a.roster else SUMMARY_PATH,
            roster_tag=a.roster_tag,
        )
    else:
        print(json.dumps(json.loads(EVENTS_SUMMARY.read_text()), indent=1)[:4000])


if __name__ == "__main__":
    main(sys.argv[1:])
