"""Near-miss study on higher timeframes: patterns on weekly / monthly / quarterly bars, walked on
the DAILY bars inside them so the order of events inside the entry bar is known.

Same families and levels as core.py, plus the 3-2-2 (owner's ruling 2026-11-21: the stop is the
3 bar's extreme; that the reversing 2 traded through it before the entry does not matter).

  3-2-2 reversal  [3, 2 against, entry]  trigger = the 2's near side, target = the 3's wick on
                                          the trade side, stop = the 3's other extreme

What the daily bars add:
  entry        the first DAY inside the entry bar that trades strictly through the trigger; price
               = the trigger, or that day's open when it gaps through mid-bar. The entry BAR
               opening beyond the trigger is a missed entry.
  other side   if a day takes the setup bar's other side BEFORE the trigger breaks, the entry bar
  first        is no longer this pattern (dropped, counted).
  same day     one day breaks the trigger and the other side: order unknown (set apart, counted).
  both
  went 3       AFTER the entry, inside the entry bar, a day takes the setup bar's other side:
               the invalidation exit, at that level. Once the entry bar has closed, only the
               stop and the target remain.
  failed       the stop is strictly broken before the target is touched.

With one daily bar per period (tf "D") this reproduces core.py's daily study, where "same day
both" is core's "went 3 on the entry day" (tests/test_nearmiss.py checks that).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from analysis.nearmiss.core import ONE, THREE, TWO_DOWN, TWO_UP, Walk, classify


@dataclass(frozen=True)
class Cand:
    family: str
    side: int
    i: int  # index of the entry bar on the pattern's own timeframe
    trigger: float
    target: float
    stop: float
    other: float


def aggregate(dates, o, h, l, c, tf: str):
    """Daily bars to tf bars ('D', 'W', 'M', 'Q'). Returns O, H, L, C and each bar's first and
    last daily index. Weeks are ISO weeks; months and quarters are calendar."""
    if tf == "D":
        key = np.arange(len(dates))
    elif tf == "W":
        iso = dates.isocalendar()
        key = iso["year"].astype(int).values * 100 + iso["week"].astype(int).values
    elif tf == "M":
        key = np.asarray(dates.year * 100 + dates.month)
    elif tf == "Q":
        key = np.asarray(dates.year * 10 + dates.quarter)
    else:
        raise ValueError(tf)
    first = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
    last = np.r_[first[1:] - 1, len(key) - 1]
    big_h = np.array([h[a : b + 1].max() for a, b in zip(first, last)])
    big_l = np.array([l[a : b + 1].min() for a, b in zip(first, last)])
    return o[first], big_h, big_l, c[last], first, last


def candidates(o, h, l, c) -> list[Cand]:
    """Every setup's levels on its own timeframe, both sides, before any entry test."""
    t = classify(h, l)
    out: list[Cand] = []
    for i in range(3, len(h)):
        s, a = i - 1, i - 2
        for side in (1, -1):
            against = TWO_DOWN if side > 0 else TWO_UP
            fav_s, adv_s = (h[s], l[s]) if side > 0 else (l[s], h[s])
            fav_a, adv_a = (h[a], l[a]) if side > 0 else (l[a], h[a])
            if t[s] == against and t[a] in (TWO_UP, TWO_DOWN):
                out.append(Cand("2-2 reversal", side, i, fav_s, fav_a, adv_s, adv_s))
            elif t[s] == against and t[a] == THREE:
                out.append(Cand("3-2-2 reversal", side, i, fav_s, fav_a, adv_a, adv_s))
            elif t[s] == ONE and t[a] == against:
                out.append(Cand("2-1-2 reversal", side, i, fav_s, fav_a, adv_a, adv_s))
            elif t[s] == ONE and t[a] == THREE:
                colour = np.sign(c[a] - o[a]) * side
                kind = "reversal" if colour < 0 else "continuation" if colour > 0 else "flat"
                out.append(Cand(f"3-1-2 {kind}", side, i, fav_s, fav_a, adv_a, adv_s))
    return out


def enter(cd: Cand, o, h, l, c, d0: int, d1: int) -> tuple[str, int, float]:
    """Status of the entry bar read on its daily bars d0..d1: (status, entry day, entry price)."""
    side = cd.side
    if side * (cd.trigger - cd.stop) <= 0:
        return "stop beyond trigger", -1, np.nan
    if side * (cd.target - cd.trigger) <= 0:
        return "no room", -1, np.nan
    if side * (o[d0] - cd.trigger) > 0:
        return "gap past trigger", -1, np.nan
    if side * (o[d0] - cd.other) < 0:
        return "opened through", -1, np.nan
    stop_nearer = side * (cd.stop - cd.other) > 0
    for d in range(d0, d1 + 1):
        fav, adv = (h[d], l[d]) if side > 0 else (l[d], h[d])
        trig = side * (fav - cd.trigger) > 0
        oth = side * (adv - cd.other) < 0
        if not trig and not oth:
            continue
        if not trig:
            return "other side first", -1, np.nan
        if oth:
            return "same day both", -1, np.nan
        entry = cd.trigger if side * (o[d] - cd.trigger) <= 0 else o[d]
        if side * (cd.target - entry) <= 0:
            return "no room at fill", -1, np.nan
        # the stop sits nearer than the other side (the 3-2-2): a day that opened on the trade's
        # side of the stop, dipped through it and closed back cannot be ordered against the entry
        dipped = side * (adv - cd.stop) < 0
        if stop_nearer and dipped and side * (o[d] - cd.stop) >= 0 and side * (c[d] - cd.stop) >= 0:
            return "same day both", -1, np.nan
        return "triggered", d, entry
    return "not triggered", -1, np.nan


def walk_sub(o, h, l, c, cd: Cand, e: int, entry: float, d1: int, k: float = 1.0) -> Walk:
    """From the entry day e to the first of: the exit level (k of the way to the target), the
    invalidation (the other side, while the entry bar is still open, through day d1), the stop.
    Outcomes: won | went3 | failed | both (one day touched the exit and the adverse level) | open.
    """
    side = cd.side
    dist = cd.target - entry
    tk = entry + k * dist
    stop_nearer = side * (cd.stop - cd.other) > 0

    def prog(x):
        return (x - entry) / dist

    best = h[e] if side > 0 else l[e]
    if side * (best - tk) >= 0:
        return Walk("won", e, tk, prog(best), prog(best))
    if stop_nearer and side * (c[e] - cd.stop) < 0:  # closed beyond the stop: after the entry
        return Walk("failed", e, cd.stop, prog(best), prog(best))
    for j in range(e + 1, len(h)):
        fav, adv = (h[j], l[j]) if side > 0 else (l[j], h[j])
        if j <= d1 and not stop_nearer:
            level, kind = cd.other, "went3"
        else:
            level, kind = cd.stop, "failed"
        if side * (o[j] - level) < 0:
            return Walk(kind, j, o[j], prog(best), prog(best))
        if side * (o[j] - tk) >= 0:
            return Walk("won", j, tk, prog(best), prog(o[j]))
        hit_t = side * (fav - tk) >= 0
        hit_a = side * (adv - level) < 0
        further = fav if side * (fav - best) > 0 else best
        if hit_t and hit_a:
            return Walk("both", j, level, prog(best), prog(further))
        if hit_t:
            return Walk("won", j, tk, prog(best), prog(further))
        if hit_a:
            return Walk(kind, j, level, prog(best), prog(further))
        best = further
    return Walk("open", len(h) - 1, float("nan"), prog(best), prog(best))
