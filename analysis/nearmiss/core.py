"""Near-miss study core: daily STRAT reversal setups with a hard target, and the walk after entry.

Definitions (agreed with the owner 2026-11-21, before this file was run; RECEIPT.md restates them):

  families   2-2 reversal    [2, 2 against, entry]   trigger = the setup 2's near side
                                                     target  = the far wick of the bar BEFORE it
                                                     stop    = the setup 2's far side
             2-1-2 reversal  [2 against, 1, entry]   trigger = the inside bar's side
                                                     target  = the 2's far wick
                                                     stop    = the 2's other extreme (NOT the
                                                               inside bar's)
             3-1-2           [3, 1, entry]           trigger = the inside bar's side
                                                     target  = the 3's wick on the trade side
                                                     stop    = the 3's other extreme
                             (reversal when the 3 closed against the trade, continuation with it)
  entry      the next daily bar trades strictly through the trigger; price = the trigger level.
             A bar that OPENS beyond the trigger is a missed entry (gap rule); a bar that opens
             through the setup bar's other side is not this pattern.
  went 3     the entry bar also takes the setup bar's other side. On daily bars the order of the
             two breaks is unknown, so these are counted apart and are neither failed nor won.
  won        the target is touched before the stop.
  failed     the stop is strictly broken on a later bar before the target is touched.
  progress   for a failed pattern, the furthest point reached toward the target as a fraction
             of the entry-to-target distance: `p_lo` excludes the stop bar (certain), `p_hi`
             includes the stop bar's own extreme (possible).

Strict breaks only (equality never breaks a level). Setup bars are closed bars. Held out, pending
the owner's ruling on the stop: the rev strats (1-2-2, 1-3-2, 1-3) and the 3-2-2.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

REF, ONE, TWO_UP, TWO_DOWN, THREE = 0, 1, 2, -2, 3


def classify(high: np.ndarray, low: np.ndarray) -> np.ndarray:
    """Bar types against the previous bar; the first bar is the reference (0)."""
    out = np.zeros(len(high), dtype=int)
    for i in range(1, len(high)):
        up = high[i] > high[i - 1]
        dn = low[i] < low[i - 1]
        out[i] = THREE if (up and dn) else TWO_UP if up else TWO_DOWN if dn else ONE
    return out


@dataclass(frozen=True)
class Setup:
    family: str
    side: int  # +1 long, -1 short
    i: int  # index of the entry bar
    trigger: float
    target: float
    stop: float
    other: float  # the setup bar's other side: taking it makes the entry bar a 3
    status: str  # triggered | not triggered | no room | gap past trigger | opened through | flat setup bar
    went3: bool


def _fav(high, low, j, side):
    return high[j] if side > 0 else low[j]


def _adv(high, low, j, side):
    return low[j] if side > 0 else high[j]


def find_setups(o, h, l, c) -> list[Setup]:
    """Every candidate setup with the entry bar's status. Both sides are scanned."""
    t = classify(h, l)
    out: list[Setup] = []
    for i in range(3, len(h)):
        s, a = i - 1, i - 2
        for side in (1, -1):
            against = TWO_DOWN if side > 0 else TWO_UP
            if t[s] == against and t[a] in (TWO_UP, TWO_DOWN):
                family = "2-2 reversal"
                trigger, target = _fav(h, l, s, side), _fav(h, l, a, side)
                stop = other = _adv(h, l, s, side)
            elif t[s] == ONE and t[a] in (against, THREE):
                trigger, target = _fav(h, l, s, side), _fav(h, l, a, side)
                stop, other = _adv(h, l, a, side), _adv(h, l, s, side)
                if t[a] == against:
                    family = "2-1-2 reversal"
                else:
                    colour = np.sign(c[a] - o[a]) * side
                    family = "3-1-2 " + (
                        "reversal" if colour < 0 else "continuation" if colour > 0 else "flat"
                    )
            else:
                continue
            went3 = False
            if side * (trigger - stop) <= 0:
                status = "flat setup bar"  # a zero-range bar: no stop distance, a data artifact
            elif side * (target - trigger) <= 0:
                status = "no room"
            elif side * (o[i] - trigger) > 0:
                status = "gap past trigger"
            elif side * (o[i] - other) < 0:
                status = "opened through"
            elif side * (_fav(h, l, i, side) - trigger) > 0:
                status = "triggered"
                went3 = side * (_adv(h, l, i, side) - other) < 0
            else:
                status = "not triggered"
            out.append(Setup(family, side, i, trigger, target, stop, other, status, went3))
    return out


@dataclass(frozen=True)
class Walk:
    outcome: str  # won | failed | both | open
    j: int  # index of the bar that ended it (the last bar if open)
    fill: float  # exit price for won / failed; the stop for 'both' (the cautious reading)
    p_lo: float  # progress before the ending bar (fraction of entry-to-target)
    p_hi: float  # progress including the ending bar's own extreme


def walk(o, h, l, st: Setup, k: float = 1.0) -> Walk:
    """Follow a triggered setup that did not go 3, to a target set at k of the way (k=1: the
    target itself). 'both' = one later bar touched the target and broke the stop (order unknown).
    """
    side, entry = st.side, st.trigger
    dist = st.target - entry
    tk = entry + k * dist

    def prog(x):
        return (x - entry) / dist

    best = _fav(h, l, st.i, side)
    if side * (best - tk) >= 0:
        return Walk("won", st.i, tk, prog(best), prog(best))
    for j in range(st.i + 1, len(h)):
        fav, adv = _fav(h, l, j, side), _adv(h, l, j, side)
        if side * (o[j] - st.stop) < 0:
            return Walk("failed", j, o[j], prog(best), prog(best))
        if side * (o[j] - tk) >= 0:
            return Walk("won", j, tk, prog(best), prog(o[j]))
        hit_t = side * (fav - tk) >= 0
        hit_s = side * (adv - st.stop) < 0
        further = fav if side * (fav - best) > 0 else best
        if hit_t and hit_s:
            return Walk("both", j, st.stop, prog(best), prog(further))
        if hit_t:
            return Walk("won", j, tk, prog(best), prog(further))
        if hit_s:
            return Walk("failed", j, st.stop, prog(best), prog(further))
        best = further
    return Walk("open", len(h) - 1, float("nan"), prog(best), prog(best))
