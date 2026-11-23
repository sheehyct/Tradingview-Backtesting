"""Exit lab: the near-miss entries with a choice of exit laid over the pattern's own exits.

EXPLORATORY (TVB-47, the owner's question 2026-11-23): the pattern gives a target and a stop and
nothing in between. Entry, target, stop and the went-3 exit are exactly htf.py's. Each mode adds
ONE more way out, at its usual default setting, never tuned:

  pattern     nothing added (the control)
  fraction    out at k of the way to the target (the owner's 40% fallback)
  prior_day   a day trades through the previous day's low (longs) / high (shorts): out at that
              level. Resting from the day after the entry.
  giveback    Guardian's trailing stop in stock terms: armed once the trade has gone `arm` of the
              way to the target, then out after giving back `give` of the entry-to-target distance
              from the best price. Resting from the day after it arms.
  chandelier  a close through the line hung atr_mult x ATR(atr_len) off the best price since the
              entry (the line only tightens)
  ema         a close on the wrong side of the EMA(ema_len)
  rsi         a close with RSI(rsi_len) on the wrong side of 50
  bollinger   the day's range tags the outer band (bb_len, bb_mult) on the trade's side: out at
              that close (a take-profit)
  time        still open time_bars sessions after the entry: out at that close

Fill conventions, the same cautious ones as the receipts: a resting level is known before the
day starts and fills at the level (the open when the day gaps through it); a close rule is read
at the close and fills at that close; a day that touches both the profit exit and an adverse
level counts as the adverse one ("both"). Resting levels use the best price as it stood at the
previous close, so nothing inside the day is ordered by guesswork.

Indicators follow TradingView's arithmetic (EMA and Wilder's average seeded with a simple
average, population standard deviation) so the Pine mirror can be held to these numbers.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from analysis.nearmiss.htf import Cand

MODES = (
    "pattern",
    "fraction",
    "prior_day",
    "giveback",
    "chandelier",
    "ema",
    "rsi",
    "bollinger",
    "time",
)


@dataclass(frozen=True)
class Params:
    k: float = 0.40
    arm: float = 1 / 3
    give: float = 0.5
    atr_len: int = 22
    atr_mult: float = 3.0
    ema_len: int = 9
    rsi_len: int = 14
    bb_len: int = 20
    bb_mult: float = 2.0
    time_bars: int = 10


@dataclass(frozen=True)
class Out:
    outcome: str  # won | went3 | failed | rule | both | open
    j: int  # index of the day that ended it (the last day if open)
    fill: float


def sma(x: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        cs = np.cumsum(np.insert(x, 0, 0.0))
        out[n - 1 :] = (cs[n:] - cs[:-n]) / n
    return out


def _smoothed(x: np.ndarray, n: int, alpha: float) -> np.ndarray:
    """Recursive average seeded with the simple average of the first n valid values."""
    out = np.full(len(x), np.nan)
    valid = np.flatnonzero(~np.isnan(x))
    if len(valid) < n:
        return out
    start = valid[0] + n - 1
    out[start] = x[valid[0] : start + 1].mean()
    for i in range(start + 1, len(x)):
        out[i] = alpha * x[i] + (1 - alpha) * out[i - 1]
    return out


def ema(x: np.ndarray, n: int) -> np.ndarray:
    return _smoothed(x, n, 2 / (n + 1))


def rma(x: np.ndarray, n: int) -> np.ndarray:
    return _smoothed(x, n, 1 / n)


def atr(h: np.ndarray, l: np.ndarray, c: np.ndarray, n: int) -> np.ndarray:
    pc = np.r_[np.nan, c[:-1]]
    tr = np.fmax(h - l, np.fmax(np.abs(h - pc), np.abs(l - pc)))
    return rma(tr, n)


def rsi(c: np.ndarray, n: int) -> np.ndarray:
    ch = np.r_[np.nan, np.diff(c)]
    up, dn = (
        rma(np.where(np.isnan(ch), np.nan, np.maximum(ch, 0)), n),
        rma(np.where(np.isnan(ch), np.nan, np.maximum(-ch, 0)), n),
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        out = 100 - 100 / (1 + up / dn)
    out = np.where(dn == 0, 100.0, out)
    return np.where(np.isnan(up), np.nan, out)


def bands(c: np.ndarray, n: int, mult: float) -> tuple[np.ndarray, np.ndarray]:
    mid = sma(c, n)
    var = sma(c * c, n) - mid * mid
    sd = np.sqrt(np.maximum(var, 0))
    return mid + mult * sd, mid - mult * sd


def indicators(h, l, c, p: Params = Params()) -> dict[str, np.ndarray]:
    upper, lower = bands(c, p.bb_len, p.bb_mult)
    return dict(
        atr=atr(h, l, c, p.atr_len),
        ema=ema(c, p.ema_len),
        rsi=rsi(c, p.rsi_len),
        upper=upper,
        lower=lower,
    )


def walk_exit(
    o, h, l, c, cd: Cand, e: int, entry: float, d1: int, mode: str, ind: dict, p: Params = Params()
) -> Out:
    """From the entry day e to the first of: the target (k of the way in 'fraction' mode), the
    invalidation (the setup bar's other side while the entry bar is still open, through day d1),
    the stop, or the mode's own exit."""
    if mode not in MODES:
        raise ValueError(mode)
    side = cd.side
    dist = cd.target - entry
    tk = entry + (p.k if mode == "fraction" else 1.0) * dist
    stop_nearer = side * (cd.stop - cd.other) > 0

    def close_rule(j: int, line: float) -> bool:
        if mode == "ema":
            return side * (c[j] - ind["ema"][j]) < 0
        if mode == "rsi":
            return side * (ind["rsi"][j] - 50.0) < 0
        if mode == "bollinger":
            return h[j] >= ind["upper"][j] if side > 0 else l[j] <= ind["lower"][j]
        if mode == "time":
            return j - e >= p.time_bars
        if mode == "chandelier":
            return side * (c[j] - line) < 0  # False while the line is still nan
        return False

    def lines(j: int, best: float, line: float) -> tuple[float, float]:
        """After day j's close: (the resting level for day j+1, the chandelier line)."""
        rest = np.nan
        if mode == "prior_day":
            rest = l[j] if side > 0 else h[j]
        elif mode == "giveback" and (best - entry) / dist >= p.arm:
            rest = best - p.give * dist
        if mode == "chandelier" and not np.isnan(ind["atr"][j]):
            fresh = best - side * p.atr_mult * ind["atr"][j]
            line = fresh if np.isnan(line) or side * (fresh - line) > 0 else line
        return rest, line

    best = h[e] if side > 0 else l[e]
    if side * (best - tk) >= 0:
        return Out("won", e, tk)
    if stop_nearer and side * (c[e] - cd.stop) < 0:  # closed beyond the stop: after the entry
        return Out("failed", e, cd.stop)
    if close_rule(e, np.nan):
        return Out("rule", e, c[e])
    rest, line = lines(e, best, np.nan)
    for j in range(e + 1, len(h)):
        fav, adv = (h[j], l[j]) if side > 0 else (l[j], h[j])
        if j <= d1 and not stop_nearer:
            level, kind = cd.other, "went3"
        else:
            level, kind = cd.stop, "failed"
        if not np.isnan(rest) and side * (rest - level) > 0:  # the rule's level sits nearer
            level, kind = rest, "rule"
        if side * (o[j] - level) < 0:
            return Out(kind, j, o[j])
        if side * (o[j] - tk) >= 0:
            return Out("won", j, tk)
        hit_t = side * (fav - tk) >= 0
        hit_a = side * (adv - level) < 0
        if hit_t and hit_a:
            return Out("both", j, level)
        if hit_t:
            return Out("won", j, tk)
        if hit_a:
            return Out(kind, j, level)
        if close_rule(j, line):
            return Out("rule", j, c[j])
        if side * (fav - best) > 0:
            best = fav
        rest, line = lines(j, best, line)
    return Out("open", len(h) - 1, float("nan"))
