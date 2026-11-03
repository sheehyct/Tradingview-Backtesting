"""The match and the readings of the matched-pair study (prereg sections 3, 4, 6, 7; section 12
for the in-session Codex fold). A cell is the set of units that looked the same at the trigger:
pattern, unit timeframe, direction, the week's side and the month's side at entry. Inside a cell
each numeric variable is cut into its lowest, middle and highest third (ties broken by order),
and the outcome is read per third; a category is read per level. The pooled reading stratifies
by cell (each cell's high-minus-low difference weighted by the cell's units), so a variable that
only tracks which cells are big does not read as a separation.

The primary outcome, T1 reached before the exit, is read over the units that HAVE a first
target: the engine encodes "no target exists" as not reached, and a unit without a target is
a different fact (reported beside it, per level, as the share with a target). Cells below the
minimum are pooled into "other" and shown, never dropped (they enter no pooled difference).
Readings, never rankings; every variable is reported."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from analysis.domino import manage as M
from analysis.pairs.features import BINARY_HIGH, CATEGORY, NUMERIC

CELL = ["kind", "tf", "direction", "w_support", "m_support"]
LEVELS = ("low", "mid", "high")
BOOKS = {"C": "ret_C", "D": "ret_D"}
OUTCOMES = ("has_t1", "reach", "C", "D")


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """The frame the readings run on: the cell key; `has_t1` (the unit had a first target at
    all); `reached1` as a boolean where a target existed and absent where none did; a unit with
    no exit-only outcome (censored) is dropped; the month side's unknowns as a level of their
    own."""
    d = df.copy()
    d["m_support"] = d["m_support"].fillna("unknown")
    d["w_support"] = d["w_support"].fillna("unknown")
    d = d[d["ret_C"].notna()].copy()
    d["has_t1"] = d["t1"].notna()
    reached = d["reached1"].astype(object)
    reached[~d["has_t1"] | d["reached1"].isna()] = np.nan
    d["reached1"] = reached
    d["cell"] = d[CELL].astype(str).agg("|".join, axis=1)
    return d


def tercile(d: pd.DataFrame, var: str) -> pd.Series:
    """low / mid / high within each cell, over the units that carry the variable; absent otherwise."""
    out = pd.Series(index=d.index, dtype=object)
    have = d[var].notna()
    if not have.any():
        return out
    sub = d.loc[have, ["cell", var]]
    rank = sub.groupby("cell")[var].rank(method="first")
    size = sub.groupby("cell")[var].transform("size")
    third = np.minimum((((rank - 1) * 3) // size).astype(int), 2)
    out.loc[have] = np.array(LEVELS, dtype=object)[third.to_numpy()]
    return out


def _share(mask: pd.Series) -> dict:
    mask = mask.dropna()
    return (
        M.share(mask.astype(bool).astype(object))
        if len(mask)
        else {"k": 0, "n": 0, "p": math.nan, "lo": math.nan, "hi": math.nan}
    )


def _mean(s: pd.Series) -> dict:
    return (
        M._ci(s.dropna())
        if s.notna().sum()
        else {"n": 0, "avg": math.nan, "lo": math.nan, "hi": math.nan}
    )


def _var_mean(s: pd.Series) -> tuple[float, int]:
    s = s.dropna().astype(float)
    n = int(len(s))
    return (float(s.var(ddof=1)) if n > 1 else math.nan), n


def _pooled(parts: list[tuple[float, float, float]]) -> dict:
    """Stratified difference: parts = (weight, difference, variance of the difference) per cell."""
    parts = [(w, d, v) for w, d, v in parts if math.isfinite(d) and math.isfinite(v)]
    if not parts:
        return {"cells": 0, "diff": math.nan, "lo": math.nan, "hi": math.nan}
    w = np.array([p[0] for p in parts], dtype=float)
    d = np.array([p[1] for p in parts], dtype=float)
    v = np.array([p[2] for p in parts], dtype=float)
    diff = float((w * d).sum() / w.sum())
    se = float(math.sqrt((w * w * v).sum()) / w.sum())
    return {"cells": int(len(parts)), "diff": diff, "lo": diff - 1.96 * se, "hi": diff + 1.96 * se}


def _prop_part(hi: pd.Series, lo: pd.Series) -> tuple[float, float, float] | None:
    """A cell's high-minus-low difference of proportions with its variance, over the units that
    carry the outcome; None when either side has fewer than two."""
    hi, lo = hi.dropna().astype(bool), lo.dropna().astype(bool)
    if len(hi) < 2 or len(lo) < 2:
        return None
    ph, pl = float(hi.mean()), float(lo.mean())
    return (float(len(hi) + len(lo)), ph - pl, ph * (1 - ph) / len(hi) + pl * (1 - pl) / len(lo))


def _mean_part(hi: pd.Series, lo: pd.Series) -> tuple[float, float, float] | None:
    vh, nh = _var_mean(hi)
    vl, nl = _var_mean(lo)
    if nh < 2 or nl < 2:
        return None
    return (float(nh + nl), float(hi.mean() - lo.mean()), vh / nh + vl / nl)


def levels_of(var: str, d: pd.DataFrame, col: pd.Series) -> list:
    if var in NUMERIC:
        return list(LEVELS)
    vals = [v for v in col.dropna().unique()]
    try:
        return sorted(vals)
    except TypeError:
        return sorted(vals, key=str)


def high_low(var: str, levels: list) -> tuple[list, list] | None:
    """Which levels the pooled difference compares: the top and bottom third of a numeric
    variable; the declared side of a two-level category; nothing for a multi-level category."""
    if var in NUMERIC:
        return ["high"], ["low"]
    if var in BINARY_HIGH:
        hi = [lv for lv in levels if lv in BINARY_HIGH[var]]
        lo = [lv for lv in levels if lv not in BINARY_HIGH[var]]
        return (hi, lo) if hi and lo else None
    return None


def _per_level(g: pd.DataFrame, c: pd.Series, levels: list) -> dict:
    per = {}
    for lv in levels:
        sub = g[c == lv]
        if not len(sub):
            continue
        per[lv] = {
            "n": int(len(sub)),
            "has_t1": _share(sub["has_t1"]),
            "reach": _share(sub["reached1"]),
            "C": _mean(sub["ret_C"]),
            "D": _mean(sub["ret_D"]),
        }
    return per


def reading(d: pd.DataFrame, var: str, min_n: int) -> dict:
    """One variable on one tape: per cell (at least `min_n` units) and per level the unit count,
    the share with a first target, the T1-reach rate over those (Wilson 95%), the exit-only and
    one-R means (normal 95%); the stratified high-minus-low difference per outcome; the per-level
    rates standardized to the cell sizes; the small cells pooled as "other"; the count of units
    that carry no value."""
    col = tercile(d, var) if var in NUMERIC else d[var]
    levels = levels_of(var, d, col)
    cells = {}
    parts: dict[str, list] = {k: [] for k in OUTCOMES}
    hl = high_low(var, levels)
    std: dict = {
        lv: {"w": 0.0, "wr": 0.0, "wc": 0.0, "has_t1": 0.0, "reach": 0.0, "C": 0.0, "n": 0}
        for lv in levels
    }
    small = []
    for cell, g in d.groupby("cell"):
        if len(g) < min_n:
            small.append(g)
            continue
        c = col.loc[g.index]
        per = _per_level(g, c, levels)
        w = float(len(g))
        for lv, s in per.items():
            std[lv]["n"] += s["n"]
            std[lv]["w"] += w
            std[lv]["has_t1"] += w * s["has_t1"]["p"]
            if s["reach"]["n"]:
                std[lv]["wr"] += w
                std[lv]["reach"] += w * s["reach"]["p"]
            if s["C"]["n"]:
                std[lv]["wc"] += w
                std[lv]["C"] += w * s["C"]["avg"]
        cells[cell] = {"n": int(len(g)), "levels": per}
        if hl is None:
            continue
        hi = g[c.isin(hl[0])]
        lo = g[c.isin(hl[1])]
        for key, part in (
            ("has_t1", _prop_part(hi["has_t1"], lo["has_t1"])),
            ("reach", _prop_part(hi["reached1"], lo["reached1"])),
            ("C", _mean_part(hi["ret_C"], lo["ret_C"])),
            ("D", _mean_part(hi["ret_D"], lo["ret_D"])),
        ):
            if part is not None:
                parts[key].append(part)
    pooled = {k: _pooled(v) for k, v in parts.items()} if hl is not None else None
    standardized = {
        lv: {
            "n": s["n"],
            "has_t1": (s["has_t1"] / s["w"]) if s["w"] else math.nan,
            "reach": (s["reach"] / s["wr"]) if s["wr"] else math.nan,
            "C": (s["C"] / s["wc"]) if s["wc"] else math.nan,
        }
        for lv, s in std.items()
        if s["n"]
    }
    other = None
    if small:
        og = pd.concat(small)
        other = {
            "cells": len(small),
            "n": int(len(og)),
            "levels": _per_level(og, col.loc[og.index], levels),
        }
    return {
        "var": var,
        "levels": levels,
        "compares": None if hl is None else {"high": hl[0], "low": hl[1]},
        "absent": int(d[var].isna().sum()),
        "units": int(len(d)),
        "cells_read": len(cells),
        "units_read": int(sum(c["n"] for c in cells.values())),
        "pooled": pooled,
        "standardized": standardized,
        "other": other,
        "cells": cells,
    }


def readings(d: pd.DataFrame, min_n: int) -> dict:
    return {var: reading(d, var, min_n) for var in (*NUMERIC, *CATEGORY) if var in d}


def clear(p: dict | None) -> bool:
    return bool(p) and math.isfinite(p.get("lo", math.nan)) and (p["lo"] > 0 or p["hi"] < 0)


def _sign(p: dict | None) -> dict | None:
    if not p or not math.isfinite(p.get("diff", math.nan)):
        return None
    return {
        "diff": p["diff"],
        "lo": p["lo"],
        "hi": p["hi"],
        "clear": clear(p),
        "sign": 1 if p["diff"] > 0 else -1 if p["diff"] < 0 else 0,
    }


def themes(by_tape: dict[str, dict], crypto: str, es_days: tuple[str, ...]) -> dict:
    """The owner's rule (prereg 7.1 and 11): a variable is a theme when its pooled high-minus-low
    difference on the primary outcome (T1 reached, over the units with a target) has the same sign
    on the crypto run and on at least one ES clean-fill day, both intervals clear of zero.
    Reported per variable with the sign on every tape, and beside it the same reading of the
    share WITH a target (not part of the rule); a variable that separates on one tape only is a
    reading there, not a theme."""
    out = {}
    for var in (*NUMERIC, *CATEGORY):
        signs, has = {}, {}
        for tape, rd in by_tape.items():
            r = rd.get(var)
            p = r["pooled"] if r and r["pooled"] else None
            signs[tape] = _sign(p["reach"]) if p else None
            has[tape] = _sign(p["has_t1"]) if p else None
        c = signs.get(crypto)
        theme = False
        with_day = None
        if c and c["clear"]:
            for day in es_days:
                e = signs.get(day)
                if e and e["clear"] and e["sign"] == c["sign"]:
                    theme, with_day = True, day
                    break
        out[var] = {"theme": theme, "with": with_day, "signs": signs, "has_t1": has}
    return out
