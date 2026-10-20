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
) -> tuple[pd.DataFrame, dict]:
    """All trigger rows of one symbol. Pure function of the frames passed in (testable)."""
    drops: dict[str, int] = {"no_setup_type": 0, "zero_range": 0, "no_levels": 0}
    d = daily_from_hourly(hf)
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
    buckets = {tf: aggregate(daily, tf) for tf in ("W", "M", "Q")}
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
        k1 = int(d["h0"].iloc[i + 1]) if i + 1 < len(d) else n
        hh, ll = h[k0:k1], l[k0:k1]
        brk = {"up": np.flatnonzero(hh > setup["h"]), "down": np.flatnonzero(ll < setup["l"])}
        both = len(brk["up"]) > 0 and len(brk["down"]) > 0
        for direction, idx in brk.items():
            if len(idx) == 0:
                continue
            k = k0 + int(idx[0])
            level = setup["h"] if direction == "up" else setup["l"]
            stop = near_side(setup, direction)
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
                if k > k0:
                    dh, dl = hh[: k - k0].max(), ll[: k - k0].min()
                    run_h = dh if run_h is None else max(run_h, dh)
                    run_l = dl if run_l is None else min(run_l, dl)
                prev = cx["prev"]
                ptype = None
                if run_h is not None and prev is not None:
                    ptype = classify({"h": run_h, "l": run_l}, prev)
                color = 0
                if k > k0 or cx["run_h"] is not None:
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
            if bar2 is not None:
                alt_stop = near_side(bar2, direction) if t1 == "1" else stop
            else:
                alt_stop = stop
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
            a = atr[i - 1]
            third, strict = shape_flags(setup, direction)
            pw, pm = part.get("W", {}), part.get("M", {})
            row = {
                "symbol": symbol,
                "asset_class": "major" if symbol in MAJORS else "alt",
                "trigger_tf": "1D",
                "direction": "long" if direction == "up" else "short",
                "pattern": name,
                "family": family,
                "sequence": f"{t2 or '?'}-{t1}-{'2U' if direction == 'up' else '2D'}",
                "trigger_time": int(t[k]),
                "day": int(d["t"].iloc[i]),
                "hours_since_daily_open": int((t[k] - d["t"].iloc[i]) // HOUR),
                "day_of_week": int(
                    datetime.fromtimestamp(d["t"].iloc[i] / 1000, tz=timezone.utc).weekday()
                ),
                "symbol_age_days": int((d["t"].iloc[i] - first_day) // DAY),
                "opposite_also_triggered": bool(both),
                "level": level,
                "stop": stop,
                "r": r,
                "stop_alt_r": abs(level - alt_stop) / r,
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
                "censored": bool(t[e10] < (day_of_hour[k0] + 10) * DAY + 23 * HOUR)
                if e10 >= 0
                else True,
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


def _roster() -> dict:
    return json.loads(SUMMARY_PATH.read_text())["rows"]


def _daily_qv(symbol: str, last_traded: str | None) -> tuple[str, pd.Series]:
    hf = hourly_frame(symbol, last_traded)
    d = daily_from_hourly(hf)
    return symbol, pd.Series(d["qv"].to_numpy(), index=d["t"].to_numpy())


_G: dict = {}


def _init(btc: pd.DataFrame, ranks: pd.DataFrame) -> None:
    _G["btc"] = btc
    _G["ranks"] = ranks


def _one(args) -> tuple[str, pd.DataFrame, dict, float]:
    symbol, last_traded = args
    t0 = time.time()
    hf = hourly_frame(symbol, last_traded)
    ranks = _G.get("ranks")
    liq = ranks[symbol].dropna() if ranks is not None and symbol in ranks else None
    df, drops = symbol_events(symbol, hf, liq, _G.get("btc"), funding_frame(symbol))
    return symbol, df, drops, time.time() - t0


def build(symbols: list[str] | None = None, workers: int = 4, log=print) -> pd.DataFrame:
    roster = _roster()
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
    btc = btc_context(hourly_frame("BTCUSDT", roster["BTCUSDT"]["last_traded"]))
    log(f"  BTC context: {len(btc)} hours")
    frames, drops, slow = [], {}, []
    with ProcessPoolExecutor(max_workers=workers, initializer=_init, initargs=(btc, ranks)) as ex:
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
    EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ev.to_parquet(EVENTS_PATH, index=False)
    write_summary(ev, drops, time.time() - t0, len(syms))
    log(f"  {len(ev)} rows -> {EVENTS_PATH}; drops {drops}; slowest {sorted(slow)[-3:]}")
    return ev


def write_summary(ev: pd.DataFrame, drops: dict, secs: float, n_symbols: int) -> dict:
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
    EVENTS_SUMMARY.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    return doc


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--symbols", nargs="*", default=None)
    b.add_argument("--workers", type=int, default=4)
    sub.add_parser("summary")
    a = ap.parse_args(argv)
    if a.cmd == "build":
        build(a.symbols, a.workers)
    else:
        print(json.dumps(json.loads(EVENTS_SUMMARY.read_text()), indent=1)[:4000])


if __name__ == "__main__":
    main(sys.argv[1:])
