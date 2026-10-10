"""TVB-37 chance comparison -- CHARACTERIZATION, NO STRATEGY, NO P&L.

Pre-registration: docs/experiments/tvb37_chance_comparison_prereg.md (definitions fixed 2026-10-10,
BEFORE this file existed; owner go the same day). The short form:

  sample     the census universe in the VENUE ERA (each coin from its first traded day); ALL as a
             check line; LIQUID as a split
  unit       every first break of the day's, week's or month's level (quarter = context only),
             detected by the audited census engine (census.day_events); one unit per timeframe
  label      setup kind of that timeframe's setup bar (2-2 reversal / 2-2 continuation / 1-2 /
             3-2) + shape flag of the setup bar (none / THIRD / STRICT); named signals: normal
             hammer = reversal + flag, momo 2-2 = continuation + flag, momo 1-2 = inside + flag
  class      daily units: PLAIN (yesterday's level alone) / EXACT at a shared open / EXACT on a
             plain day / NEAR (<= 0.25% beyond) / WITHIN 1% / SPREAD, over the day + week + month
             levels broken that day; weekly and monthly units: the gap to yesterday's level, same
             bands, no PLAIN
  trade      entry at the level L on the break; stop S = the other side of the setup bar; R = |L-S|;
             target one R; orders fill on touch; a day touching both = STOP (pessimistic)
  horizon    N = 1 / 3 / 5 bars of the unit's timeframe after the entry bar; data ends first =
             CENSORED (excluded from that horizon)
  follow     the type of the next bar of the unit's timeframe vs the entry bar: inside / 2 with /
             2 against / outside
  variant    daily units only: the stop at the other side of the previous complete WEEKLY bar
             (the owner's idea, one table, never pooled)

Everything here is arithmetic on counts. No fee, funding, sizing or management exists in this module.
"""

from __future__ import annotations

import csv
import gzip
import json
import math
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from analysis.domino.census import (
    NEAR_BAND,
    WITHIN_BAND,
    _context,
    _dec,
    _quarter_state,
    aggregate,
    classify,
    day_events,
    day_start,
    fetch_daily,
    liquid,
    normalize,
    setup_kind,
    shape_flags,
    shared_opens,
    universe,
)

HERE = Path(__file__).parent
RESULTS = HERE / "results"
HORIZONS = (1, 3, 5)
PATTERN_TFS = ("D", "W", "M")
KINDS = ("reversal", "continuation", "inside", "outside")
CLASSES = ("plain", "exact_shared", "exact_plain", "near", "within1", "spread")
STACKED = ("exact_shared", "exact_plain", "near")
MIN_CELL = 30
SIGNALS = {
    ("reversal", "third"): "normal hammer / shooter (THIRD)",
    ("reversal", "strict"): "normal hammer / shooter (STRICT)",
    ("continuation", "third"): "momo hammer / shooter, 2-2 form (THIRD)",
    ("continuation", "strict"): "momo hammer / shooter, 2-2 form (STRICT)",
    ("inside", "third"): "momo hammer / shooter, 1-2 form (THIRD)",
    ("inside", "strict"): "momo hammer / shooter, 1-2 form (STRICT)",
}


# ----------------------------------------------------------------------------- helpers


def venue_era(daily: list[dict]) -> list[dict]:
    """The coin from its first day with traded volume (the venue's earlier candles are index prices)."""
    for k, d in enumerate(daily):
        if d["v"] > 0:
            return daily[k:]
    return []


def gap_frac(level: float, other: float, direction: str):
    """Signed gap of `other` beyond `level` in the trade's direction, as a decimal fraction of
    `level` (positive = beyond, i.e. in favour). Decimal so a gap of exactly 0.25% is exactly that."""
    lv, ot = _dec(level), _dec(other)
    diff = (ot - lv) if direction == "up" else (lv - ot)
    return diff / lv


def band_of(frac) -> str:
    if frac == 0:
        return "exact"
    if frac <= NEAR_BAND:
        return "near"
    if frac <= WITHIN_BAND:
        return "within1"
    return "spread"


def stack_class(tf: str, direction: str, broken: dict, shared: dict) -> tuple[str, float, str]:
    """(class, largest gap in percent, the timeframes in the stack) for one unit (prereg def. 4).

    Daily units measure every higher level against yesterday's level; weekly / monthly units
    measure their own level against yesterday's. Raises if a higher level sits short of the daily
    level (calendar nesting forbids it; prereg bug test).
    """
    tfs = "+".join(t for t in PATTERN_TFS if t in broken)
    base = broken["D"]
    if tf == "D":
        others = {t: broken[t] for t in ("W", "M") if t in broken}
        if not others:
            return "plain", 0.0, tfs
    else:
        others = {tf: broken[tf]}
    gaps = {t: gap_frac(base, lvl, direction) for t, lvl in others.items()}
    worst = max(gaps.values())
    if min(gaps.values()) < 0:
        raise AssertionError(f"higher level short of the daily level: {broken} {direction}")
    band = band_of(worst)
    if band == "exact":
        cls = "exact_shared" if all(shared[t] for t in others) else "exact_plain"
    else:
        cls = band
    return cls, float(worst) * 100.0, tfs


def entry_class(
    direction: str, level_d: float, ctx: dict, i: int, shared: dict
) -> tuple[str, float | None, str | None]:
    """Entry-time stack class of a DAILY unit (prereg amendment A1).

    At the instant yesterday's level breaks, the trader knows where last week's and last month's
    levels sit and whether they are still unbroken this bar; they do NOT know whether today will
    reach them. So the class is the distance to the nearest FRESH higher level beyond yesterday's
    level, whether or not it breaks today: EXACT (same price; at a shared open or on a plain day),
    NEAR (<= 0.25%), WITHIN 1%, else PLAIN (no fresh higher level within 1%). The first run used
    "broke today" as the condition, which selects on the day's own travel; that version is kept as
    `cls_la` and shown once as the trap it is. A fresh level is never short of yesterday's level
    (nesting), which the engine asserts.
    """
    best: tuple | None = None
    for tf in ("W", "M"):
        c = ctx[tf].get(i)
        if c is None or c["prev"] is None:
            continue
        lvl = c["prev"]["h"] if direction == "up" else c["prev"]["l"]
        if direction == "up":
            fresh = c["run_h"] is None or c["run_h"] <= lvl
        else:
            fresh = c["run_l"] is None or c["run_l"] >= lvl
        if not fresh:
            continue
        g = gap_frac(level_d, lvl, direction)
        if g < 0:
            raise AssertionError(
                f"fresh higher level short of the daily level: {tf} {lvl} vs {level_d}"
            )
        if best is None or g < best[0]:
            best = (g, tf)
    if best is None:
        return "plain", None, None
    g, tf = best
    if g > WITHIN_BAND:
        return "plain", float(g) * 100.0, tf
    band = band_of(g)
    if band == "exact":
        return ("exact_shared" if shared[tf] else "exact_plain"), 0.0, tf
    return band, float(g) * 100.0, tf


def horizon_ends(tf: str, i: int, daily: list[dict], buckets: dict, bucket_of: dict) -> dict:
    """Last day index (inclusive) of each horizon, or None when the data ends first (censored)."""
    ends = {}
    for n in HORIZONS:
        if tf == "D":
            j = i + n
            ends[n] = j if j < len(daily) else None
            continue
        b = bucket_of[tf].get(i)
        bl = buckets[tf]
        k = None if b is None else b + n
        ends[n] = bl[k]["days"][-1] if k is not None and k < len(bl) and bl[k]["complete"] else None
    return ends


def walk(daily: list[dict], i: int, direction: str, level: float, stop: float, ends: dict) -> dict:
    """Outcome per horizon plus price travel in R (prereg def. 5, 6, 8).

    Day by day from the entry day: the stop touched (alone or together with the target) = STOP;
    the target touched = ONE R; otherwise walk on. Travel = furthest favourable / adverse move
    from the level, in R, through each horizon (price travel, not a trade's).
    """
    r = abs(level - stop)
    target = level + r if direction == "up" else level - r
    res, res_j = None, None
    run_fav = run_adv = 0.0
    stop0 = False  # the stop level traded on the entry day itself (order unknown: pessimistic)
    out: dict = {}
    valid_ends = [e for e in ends.values() if e is not None]
    last = max(valid_ends) if valid_ends else i
    for j in range(i, last + 1):
        bar = daily[j]
        if direction == "up":
            fav, adv = (bar["h"] - level) / r, (level - bar["l"]) / r
            hit_s, hit_t = bar["l"] <= stop, bar["h"] >= target
        else:
            fav, adv = (level - bar["l"]) / r, (bar["h"] - level) / r
            hit_s, hit_t = bar["h"] >= stop, bar["l"] <= target
        run_fav, run_adv = max(run_fav, fav), max(run_adv, adv)
        if hit_s and j == i:
            stop0 = True
        if res is None:
            if hit_s:
                res, res_j = "stop", j
            elif hit_t:
                res, res_j = "one_r", j
        for n, end in ends.items():
            if end == j:
                out[f"mfe{n}"], out[f"mae{n}"] = run_fav, run_adv
    for n, end in ends.items():
        if end is None:
            out[f"out{n}"] = "censored"
            out[f"mfe{n}"] = out[f"mae{n}"] = None
        elif res is not None and res_j <= end:
            out[f"out{n}"] = res
        else:
            out[f"out{n}"] = "neither"
    out["stop0"] = stop0
    return out


def next_bar(
    tf: str, i: int, daily: list[dict], buckets: dict, bucket_of: dict, direction: str
) -> str:
    """Type of the next bar of the unit's timeframe against the entry bar (prereg def. 7)."""
    if tf == "D":
        if i + 1 >= len(daily):
            return "n/a"
        t = classify(daily[i + 1], daily[i])
    else:
        b = bucket_of[tf].get(i)
        bl = buckets[tf]
        if b is None or b + 1 >= len(bl) or not (bl[b]["complete"] and bl[b + 1]["complete"]):
            return "n/a"
        t = classify(bl[b + 1], bl[b])
    if t == "1":
        return "inside"
    if t == "3":
        return "outside"
    return "with" if (t == "2U") == (direction == "up") else "against"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return math.nan, math.nan
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return centre - half, centre + half


def diff_interval(
    k1: int, n1: int, k2: int, n2: int, z: float = 1.96
) -> tuple[float, float, float]:
    """(difference, low, high) of two proportions, normal approximation."""
    if n1 == 0 or n2 == 0:
        return math.nan, math.nan, math.nan
    p1, p2 = k1 / n1, k2 / n2
    d = p1 - p2
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    return d, d - z * se, d + z * se


# ----------------------------------------------------------------------------- units per coin


def coin_units(meta: dict, daily: list[dict]) -> tuple[list[dict], Counter]:
    """Every pattern unit of one coin with its class, outcomes, follow-through and variant stop."""
    counts: Counter = Counter()
    if len(daily) < 3:
        return [], counts
    buckets = {tf: aggregate(daily, tf) for tf in ("W", "M", "Q")}
    ctx = _context(daily, buckets)
    bucket_of = {
        tf: {di: b for b, bk in enumerate(buckets[tf]) for di in bk["days"]} for tf in ("W", "M")
    }
    units: list[dict] = []
    for i in range(1, len(daily)):
        evs = day_events(daily, i, ctx)
        if evs is None:
            counts["skipped_no_yesterday"] += 1
            continue
        shared = shared_opens(ctx, i)
        date = datetime.fromtimestamp(daily[i]["t"] / 1000, tz=timezone.utc)
        for direction, broken, setups in evs:
            if "D" not in broken:
                counts["nesting_violation"] += 1
                continue
            level_d = broken["D"]
            # context known at the daily break only (amendment A2): the quarter's state BEFORE
            # today (never "breaks today") and the broken level's side of the month's open
            # (never "in stack"); whether they broke today is outcome-side and lives in `stack`
            q_state = _quarter_state(ctx["Q"].get(i), False, direction, level_d)
            c = ctx["M"].get(i)
            if c is None or c["prev"] is None:
                m_support = "unknown"
            else:
                with_ = level_d > c["open"] if direction == "up" else level_d < c["open"]
                m_support = "with" if with_ else "against"  # equality = against (census F7)
            for tf in PATTERN_TFS:
                if tf not in broken:
                    continue
                ptype, sbar, _ref = setups[tf]
                kind = setup_kind(ptype, direction)
                if kind is None:
                    counts[f"unclassified_{tf}"] += 1
                    continue
                level = broken[tf]
                stop = sbar["l"] if direction == "up" else sbar["h"]
                if (direction == "up" and stop >= level) or (direction == "down" and stop <= level):
                    counts[f"zero_r_{tf}"] += 1
                    continue
                cls_la, gap_la, tfs = stack_class(tf, direction, broken, shared)
                if tf == "D":
                    cls, gap_pct, near_tf = entry_class(direction, level, ctx, i, shared)
                else:
                    cls, gap_pct, near_tf = cls_la, gap_la, "D"
                third, strict = shape_flags(sbar, direction)
                flag = "strict" if strict else "third" if third else "none"
                ends = horizon_ends(tf, i, daily, buckets, bucket_of)
                row = {
                    "coin": meta["coin"],
                    "dex": meta["dex"],
                    "liquid": meta["liquid"],
                    "date": date.strftime("%Y-%m-%d"),
                    "year": date.year,
                    "direction": direction,
                    "tf": tf,
                    "kind": kind,
                    "flag": flag,
                    "cls": cls,
                    "cls_la": cls_la,  # the look-ahead version: conditioned on breaking today
                    "near_tf": near_tf,
                    "stack": tfs,  # which levels actually broke today (outcome-side information)
                    "gap_pct": gap_pct,
                    "level": level,
                    "stop": stop,
                    "r_pct": 100.0 * abs(level - stop) / level,
                    "m_support": m_support,
                    "quarter": q_state,
                    "next_bar": next_bar(tf, i, daily, buckets, bucket_of, direction),
                }
                row.update(walk(daily, i, direction, level, stop, ends))
                for n in HORIZONS:
                    counts[f"censored_{tf}_{n}"] += row[f"out{n}"] == "censored"
                # the owner's variant: the stop at the previous complete weekly bar (daily units)
                row["v_r_pct"] = None
                for n in HORIZONS:
                    row[f"vout{n}"] = "n/a"
                if tf == "D":
                    cw = ctx["W"].get(i)
                    if cw is not None and cw["prev"] is not None:
                        vstop = cw["prev"]["l"] if direction == "up" else cw["prev"]["h"]
                        ok = vstop < level if direction == "up" else vstop > level
                        if ok:
                            v = walk(daily, i, direction, level, vstop, ends)
                            row["v_r_pct"] = 100.0 * abs(level - vstop) / level
                            for n in HORIZONS:
                                row[f"vout{n}"] = v[f"out{n}"]
                        else:
                            counts["variant_stop_wrong_side"] += 1
                units.append(row)
                counts[f"units_{tf}"] += 1
    return units, counts


# ----------------------------------------------------------------------------- aggregation


def cell(df: pd.DataFrame, out_prefix: str = "out") -> dict:
    """Counts and chances for one cell of units (prereg def. 12)."""
    c: dict = {"n": int(len(df)), "dates": int(df["date"].nunique()) if len(df) else 0}
    for n in HORIZONS:
        col = f"{out_prefix}{n}"
        valid = df[(df[col] != "censored") & (df[col] != "n/a")]
        m = int(len(valid))
        k = int((valid[col] == "one_r").sum())
        s = int((valid[col] == "stop").sum())
        lo, hi = wilson(k, m)
        c[f"n{n}"] = m
        c[f"k{n}"] = k
        c[f"one_r{n}"] = k / m if m else math.nan
        c[f"lo{n}"], c[f"hi{n}"] = lo, hi
        c[f"stop{n}"] = s / m if m else math.nan
        c[f"neither{n}"] = (m - k - s) / m if m else math.nan
        if out_prefix == "out":
            c[f"mfe{n}"] = float(valid[f"mfe{n}"].median()) if m else math.nan
            c[f"mae{n}"] = float(valid[f"mae{n}"].median()) if m else math.nan
    nb = df[df["next_bar"] != "n/a"]["next_bar"]
    c["nb_n"] = int(len(nb))
    for key in ("with", "against", "inside", "outside"):
        c[f"nb_{key}"] = float((nb == key).mean()) if len(nb) else math.nan
    c["r_pct_med"] = float(df["r_pct"].median()) if len(df) else math.nan
    c["stop0"] = float(df["stop0"].mean()) if len(df) else math.nan
    return c


def flag_mask(df: pd.DataFrame, level: str) -> pd.Series:
    """'all' = every unit; 'third' = THIRD or STRICT (nested); 'strict' = STRICT only."""
    if level == "all":
        return pd.Series(True, index=df.index)
    if level == "third":
        return df["flag"].isin(["third", "strict"])
    return df["flag"] == "strict"


def _p(x: float) -> str:
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.1f}%"


def _ci(c: dict, n: int) -> str:
    if c[f"n{n}"] == 0:
        return "-"
    return f"{_p(c[f'one_r{n}'])} [{100 * c[f'lo{n}']:.0f}, {100 * c[f'hi{n}']:.0f}]"


def _grey(c: dict, text: str) -> str:
    return f"({text})" if c["n"] < MIN_CELL else text


def table_pattern_by_class(
    df: pd.DataFrame,
    tf: str,
    title: str,
    out_prefix: str = "out",
    cls_col: str = "cls",
    levels: tuple = ("all", "third", "strict"),
) -> list[str]:
    """Rows = kind x flag level x class; columns = n, dates, one R at each horizon, stops, next bar."""
    lines = [f"### {title}", ""]
    hz = " | ".join(f"one R by {n}" for n in HORIZONS)
    lines.append(
        f"| setup | flag | class | n | dates | {hz} | stopped by 5 | stop traded on entry day | "
        "next bar with / against / inside / outside | median R % |"
    )
    lines.append("|---|---|---|---|---|" + "---|" * len(HORIZONS) + "---|---|---|---|")
    sub = df[df["tf"] == tf]
    classes = CLASSES if tf == "D" else CLASSES[1:]
    for kind in KINDS:
        for level in levels:
            base = sub[(sub["kind"] == kind) & flag_mask(sub, level)]
            if base.empty:
                continue
            for cls in classes:
                part = base[base[cls_col] == cls]
                if part.empty:
                    continue
                c = cell(part, out_prefix)
                cis = " | ".join(_grey(c, _ci(c, n)) for n in HORIZONS)
                nbs = f"{_p(c['nb_with'])} / {_p(c['nb_against'])} / {_p(c['nb_inside'])} / {_p(c['nb_outside'])}"
                lines.append(
                    f"| {kind} | {level} | {cls} | {c['n']:,} | {c['dates']:,} | {cis} | "
                    f"{_grey(c, _p(c['stop5']))} | {_p(c['stop0'])} | {nbs} | {c['r_pct_med']:.2f} |"
                )
    lines.append("")
    lines.append(
        "Cells in parentheses hold fewer than 30 units: counted, not read. Brackets are Wilson 95% "
        "intervals per unit; units on the same day across coins move together, so read them with the "
        "distinct-date count."
    )
    lines.append("")
    return lines


def table_differences(df: pd.DataFrame, tf: str, title: str) -> list[str]:
    """A+ class minus PLAIN (daily) or stacked minus the rest (weekly / monthly), per kind x flag."""
    lines = [f"### {title}", ""]
    lines.append(
        "| setup | flag | comparison | n A+ | n base | "
        + " | ".join(f"diff by {n} [95%]" for n in HORIZONS)
        + " |"
    )
    lines.append("|---|---|---|---|---|" + "---|" * len(HORIZONS))
    sub = df[df["tf"] == tf]
    for kind in KINDS:
        for level in ("all", "third", "strict"):
            base_all = sub[(sub["kind"] == kind) & flag_mask(sub, level)]
            if base_all.empty:
                continue
            if tf == "D":
                base = base_all[base_all["cls"] == "plain"]
                comps = [(cls, base_all[base_all["cls"] == cls], "vs plain") for cls in CLASSES[1:]]
                comps.insert(
                    0,
                    (
                        "stacked (exact or near)",
                        base_all[base_all["cls"].isin(STACKED)],
                        "vs plain",
                    ),
                )
            else:
                base = base_all[~base_all["cls"].isin(STACKED)]
                comps = [
                    (
                        "stacked (exact or near)",
                        base_all[base_all["cls"].isin(STACKED)],
                        "vs within1 + spread",
                    )
                ]
                comps += [
                    (cls, base_all[base_all["cls"] == cls], "vs within1 + spread")
                    for cls in STACKED
                ]
            cb = cell(base)
            for name, part, label in comps:
                if part.empty:
                    continue
                ca = cell(part)
                diffs = []
                for n in HORIZONS:
                    d, lo, hi = diff_interval(ca[f"k{n}"], ca[f"n{n}"], cb[f"k{n}"], cb[f"n{n}"])
                    txt = (
                        "-"
                        if math.isnan(d)
                        else f"{100 * d:+.1f} [{100 * lo:+.0f}, {100 * hi:+.0f}]"
                    )
                    diffs.append(txt if min(ca["n"], cb["n"]) >= MIN_CELL else f"({txt})")
                lines.append(
                    f"| {kind} | {level} | {name} {label} | {ca['n']:,} | {cb['n']:,} | "
                    + " | ".join(diffs)
                    + " |"
                )
    lines.append("")
    return lines


def table_hypothesis1(df: pd.DataFrame) -> list[str]:
    """Owner's hypothesis 1: exact shared-open stacks vs plain and vs near, daily units, per kind."""
    lines = [
        "### Hypothesis 1 (owner): same-price stacks at a shared open do WORSE than plain and than near",
        "",
    ]
    lines.append(
        "| setup | flag | n exact shared | one R by 1 / 3 / 5 | minus plain by 1 / 3 / 5 | minus near by 1 / 3 / 5 |"
    )
    lines.append("|---|---|---|---|---|---|")
    sub = df[df["tf"] == "D"]
    for kind in KINDS:
        for level in ("all", "third", "strict"):
            base = sub[(sub["kind"] == kind) & flag_mask(sub, level)]
            es = base[base["cls"] == "exact_shared"]
            if es.empty:
                continue
            ce, cp, cn = (
                cell(es),
                cell(base[base["cls"] == "plain"]),
                cell(base[base["cls"] == "near"]),
            )
            own = " / ".join(_p(ce[f"one_r{n}"]) for n in HORIZONS)

            def diffs(cb):
                parts = []
                for n in HORIZONS:
                    d, lo, hi = diff_interval(ce[f"k{n}"], ce[f"n{n}"], cb[f"k{n}"], cb[f"n{n}"])
                    parts.append(
                        "-"
                        if math.isnan(d)
                        else f"{100 * d:+.1f} [{100 * lo:+.0f}, {100 * hi:+.0f}]"
                    )
                return " / ".join(parts)

            row = f"| {kind} | {level} | {ce['n']:,} | {own} | {diffs(cp)} | {diffs(cn)} |"
            lines.append(row if ce["n"] >= MIN_CELL else row.replace("| " + own, "| (" + own + ")"))
    lines.append("")
    return lines


def table_split(df: pd.DataFrame, col: str, title: str) -> list[str]:
    """One-R chance by 3 bars, stacked vs plain (daily) per kind, within each value of `col`."""
    lines = [f"### {title}", ""]
    lines.append(
        "| split | setup | n plain | plain one R by 3 | n stacked | stacked one R by 3 | diff [95%] |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    sub = df[df["tf"] == "D"]
    for val in sorted(sub[col].dropna().unique(), key=str):
        part = sub[sub[col] == val]
        for kind in KINDS:
            k = part[part["kind"] == kind]
            cp, cs = cell(k[k["cls"] == "plain"]), cell(k[k["cls"].isin(STACKED)])
            if cp["n"] == 0 and cs["n"] == 0:
                continue
            d, lo, hi = diff_interval(cs["k3"], cs["n3"], cp["k3"], cp["n3"])
            txt = "-" if math.isnan(d) else f"{100 * d:+.1f} [{100 * lo:+.0f}, {100 * hi:+.0f}]"
            if min(cp["n"], cs["n"]) < MIN_CELL:
                txt = f"({txt})"
            lines.append(
                f"| {val} | {kind} | {cp['n']:,} | {_p(cp['one_r3'])} | {cs['n']:,} | {_p(cs['one_r3'])} | {txt} |"
            )
    lines.append("")
    return lines


def table_variant(df: pd.DataFrame) -> list[str]:
    """The owner's weekly-bar stop beside the primary, daily units, per kind x class."""
    lines = [
        "### Variant stop (owner's idea): stop at the previous WEEKLY bar's other side, daily units",
        "",
    ]
    lines.append(
        "| setup | class | n (variant) | median R % primary / variant | primary one R by 1 / 3 / 5 | variant one R by 1 / 3 / 5 | variant stopped by 5 |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    sub = df[(df["tf"] == "D") & (df["vout1"] != "n/a")]
    for kind in KINDS:
        for cls in CLASSES:
            part = sub[(sub["kind"] == kind) & (sub["cls"] == cls)]
            if part.empty:
                continue
            cp, cv = cell(part), cell(part, "vout")
            pr = " / ".join(_p(cp[f"one_r{n}"]) for n in HORIZONS)
            vr = " / ".join(_p(cv[f"one_r{n}"]) for n in HORIZONS)
            row = (
                f"| {kind} | {cls} | {cv['n']:,} | {cp['r_pct_med']:.2f} / {float(part['v_r_pct'].median()):.2f} | "
                f"{pr} | {vr} | {_p(cv['stop5'])} |"
            )
            lines.append(row if cv["n"] >= MIN_CELL else row.replace(f"| {pr} |", f"| ({pr}) |"))
    lines.append("")
    lines.append(
        "R is a different distance under the variant (measured to the weekly bar), so one R is not the same target."
    )
    lines.append("")
    return lines


def cells_json(df: pd.DataFrame) -> list[dict]:
    """Headline cells (tf x kind x flag level x class, both directions pooled) for census.json-style storage."""
    out = []
    for tf in PATTERN_TFS:
        sub = df[df["tf"] == tf]
        for kind in KINDS:
            for level in ("all", "third", "strict"):
                base = sub[(sub["kind"] == kind) & flag_mask(sub, level)]
                for cls in CLASSES:
                    part = base[base["cls"] == cls]
                    if part.empty:
                        continue
                    c = cell(part)
                    c.update({"tf": tf, "kind": kind, "flag": level, "cls": cls})
                    out.append(
                        {
                            k: (None if isinstance(v, float) and math.isnan(v) else v)
                            for k, v in c.items()
                        }
                    )
    return out


def report(name: str, df: pd.DataFrame, counts: Counter, full: bool) -> list[str]:
    lines = [
        f"## {name}: {df['coin'].nunique()} coins, {len(df):,} units ({', '.join(f'{tf} {int((df.tf == tf).sum()):,}' for tf in PATTERN_TFS)})",
        "",
    ]
    lines.append(
        f"Dropped and counted: unclassified setups "
        f"{sum(v for k, v in counts.items() if k.startswith('unclassified'))}, zero-R setups "
        f"{sum(v for k, v in counts.items() if k.startswith('zero_r'))}, nesting violations "
        f"{counts.get('nesting_violation', 0)}, days skipped for a missing yesterday "
        f"{counts.get('skipped_no_yesterday', 0)}, variant stops on the wrong side "
        f"{counts.get('variant_stop_wrong_side', 0)}. Censored units by horizon: "
        + ", ".join(
            f"{tf} {n}: {counts.get(f'censored_{tf}_{n}', 0):,}"
            for tf in PATTERN_TFS
            for n in HORIZONS
        )
        + "."
    )
    lines.append("")
    lines += table_pattern_by_class(
        df, "D", "Daily units: setup x shape flag x stack class (ENTRY-TIME class, amendment A1)"
    )
    lines += table_pattern_by_class(
        df,
        "D",
        "TRAP, not a finding: daily units classed by whether the higher level BROKE TODAY "
        "(the first run's definition; it selects on the day's own travel, which the trader cannot "
        "know at the daily break)",
        cls_col="cls_la",
        levels=("all",),
    )
    lines += table_differences(
        df, "D", "Daily units: A+ class minus PLAIN (one-R chance, percentage points)"
    )
    lines += table_hypothesis1(df)
    lines += table_pattern_by_class(
        df, "W", "Weekly units: setup x shape flag x gap to yesterday's level"
    )
    lines += table_differences(df, "W", "Weekly units: stacked minus the rest")
    lines += table_pattern_by_class(
        df, "M", "Monthly units: setup x shape flag x gap to yesterday's level"
    )
    lines += table_differences(df, "M", "Monthly units: stacked minus the rest")
    if full:
        lines += table_variant(df)
        lines += table_split(
            df, "direction", "Split: direction (daily, stacked vs plain, one R by 3)"
        )
        lines += table_split(
            df, "year", "Split: year of entry (daily, stacked vs plain, one R by 3)"
        )
        lines += table_split(df, "liquid", "Split: LIQUID (daily, stacked vs plain, one R by 3)")
        lines += table_split(
            df,
            "m_support",
            "Split: the month's open relative to the trade (daily, stacked vs plain, one R by 3)",
        )
        lines += table_split(
            df, "quarter", "Recorded only: quarter state (daily, stacked vs plain, one R by 3)"
        )
    return lines


# ----------------------------------------------------------------------------- main


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    now_ms = int(time.time() * 1000)
    as_of = day_start(now_ms)
    uni = universe()
    print(
        f"universe: {len(uni)} live perps; as_of {datetime.fromtimestamp(as_of / 1000, tz=timezone.utc):%Y-%m-%d} UTC",
        flush=True,
    )
    rows_venue: list[dict] = []
    rows_all: list[dict] = []
    counts_venue: Counter = Counter()
    counts_all: Counter = Counter()
    excluded = []
    for n, u in enumerate(uni, 1):
        try:
            raw = fetch_daily(u["coin"], as_of)
        except Exception as exc:  # noqa: BLE001
            excluded.append({"coin": u["coin"], "reason": f"fetch failed: {exc}"})
            continue
        st: dict = {}
        daily = normalize(raw, as_of, st)
        if st["gap_days"] or st["duplicates"] or st["unaligned"]:
            excluded.append({"coin": u["coin"], "reason": f"data quality {st}"})
            continue
        meta = {"coin": u["coin"], "dex": u["dex"], "liquid": liquid(daily)}
        ua, ca = coin_units(meta, daily)
        rows_all += ua
        counts_all.update(ca)
        uv, cv = coin_units(meta, venue_era(daily))
        rows_venue += uv
        counts_venue.update(cv)
        if n % 25 == 0:
            print(f"  {n}/{len(uni)} coins, {len(rows_venue):,} venue-era units", flush=True)
    df_v = pd.DataFrame(rows_venue)
    df_a = pd.DataFrame(rows_all)
    md = [
        f"# Chance comparison tables, as of {datetime.fromtimestamp(as_of / 1000, tz=timezone.utc):%Y-%m-%d} UTC (generated by analysis/domino/chance.py)",
        "",
    ]
    md += report("VENUE ERA (headline)", df_v, counts_venue, full=True)
    md += report("VENUE ERA, LIQUID only", df_v[df_v["liquid"]], counts_venue, full=False)
    md += report("ALL (with the index-price prefix; check line)", df_a, counts_all, full=False)
    (RESULTS / "chance_tables.md").write_text("\n".join(md), encoding="utf-8")
    out = {
        "as_of_utc": datetime.fromtimestamp(as_of / 1000, tz=timezone.utc).strftime("%Y-%m-%d"),
        "definitions": "docs/experiments/tvb37_chance_comparison_prereg.md",
        "horizons": list(HORIZONS),
        "excluded": excluded,
        "counts": {"venue_era": dict(counts_venue), "all": dict(counts_all)},
        "units": {"venue_era": int(len(df_v)), "all": int(len(df_a))},
        "cells": {
            "venue_era": cells_json(df_v),
            "venue_era_liquid": cells_json(df_v[df_v["liquid"]]),
            "all": cells_json(df_a),
        },
    }
    json.dump(out, open(RESULTS / "chance.json", "w"), indent=1)
    cols = list(df_v.columns)
    with gzip.open(RESULTS / "trades.csv.gz", "wt", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["sample"] + cols)
        for sample, df in (("venue_era", df_v), ("all", df_a)):
            for rec in df.itertuples(index=False):
                w.writerow([sample] + list(rec))
    print("\n".join(md[:60]))
    print(f"... tables written to {RESULTS / 'chance_tables.md'}")


if __name__ == "__main__":
    sys.exit(main())
