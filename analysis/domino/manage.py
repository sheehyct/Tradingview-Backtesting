"""TVB-37 product 3 -- the STRAT-management book: CHARACTERIZATION, NO STRATEGY, NO P&L CLAIM.

Pre-registration: docs/experiments/tvb37_management_book_prereg.md (definitions fixed 2026-10-11,
BEFORE this file existed; owner's forks ruled "both for the data" the same day). The short form:

  units      exactly the chance comparison's (chance.coin_units): every first break of the day's,
             week's or month's level, venue era, same labels, flags, classes and drops
  entry      at the level L the instant it breaks; R = the setup-bar distance, a measuring stick
             only -- there is NO price stop and no invalidation exit (same price on these units)
  exit       the close of a daily bar that closed against the trade (red for a long) with the
             week against it at that close (under the Monday open); fill = that close; the entry
             day counts; equality on either test is not against; Monday = one test
  targets    T1 = the pattern's own magnitude (reversal: the far wick of the bar BEFORE the setup
             bar; inside break off a 2 against or a 3: that bar's far wick); patterns with no
             magnitude of their own (2-2 continuation, with-trend inside, 3-2, stacked inside)
             take the first unbroken weekly / monthly level beyond L; T2, T3 = the next rungs
             strictly beyond; ladder fixed at entry; targets fill on touch
  cap        20 daily bars after the entry bar; still open = marked at that close (OPEN); data
             ends first = CENSORED (excluded, counted)
  books      A all out at T1 | B hold through T2 with the exit | C exit only | D one R or the
             exit (the lead's declared addition) | reference = the chance book on the same rows
             (one R or the setup-bar stop, marked at 5 bars)
  variants   fork 1: the measured move (two-bar range projected from L) as T1 for the continuation
             and the with-trend inside break; fork 2: the own-bar clock for weekly and monthly
             units at a cap of 20 own bars, the daily clock beside it at the same cap

Everything here is arithmetic on the unit rows. No fee, funding, sizing or leverage exists here.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd

from analysis.domino.book import (
    UNIT_USD,
    _curve_points,
    _pct,
    _usd,
    coin_book_rows,
    strict_json,
)
from analysis.domino.census import (
    DAY,
    HOUR,
    _context,
    _dec,
    aggregate,
    cached_hourly,
    cached_universe,
    day_events,
    day_start,
    fetch_daily,
    fetch_hourly,
    liquid,
    normalize,
    normalize_hourly,
    parse_as_of,
    universe,
)
from analysis.domino.chance import (
    CLASSES,
    KINDS,
    MIN_CELL,
    PATTERN_TFS,
    STACKED,
    flag_mask,
    horizon_ends,
    venue_era,
    wilson,
)

HERE = Path(__file__).parent
RESULTS = HERE / "results"
CAP = 20  # headline cap: daily bars after the entry bar
CAP_OWN = 20  # fork-2 table: bars of the unit's own timeframe
RUNGS = {"D": ("W", "M"), "W": ("M",), "M": ()}
BOOKS = ("A", "B", "C", "D", "D5", "ref")
BOOK_LABEL = {
    "A": "A: all out at T1",
    "B": "B: hold through T2, exit rule live",
    "C": "C: exit only, no target",
    "D": "D: one R or the exit",
    "D5": "D5: one R or the exit, five-bar horizon (the stop-isolating line)",
    "ref": "reference: one R or the setup-bar stop, 5 bars",
}
T_SRC_LABEL = {
    "anchor": "the far wick of the bar before the setup bar",
    "W": "last week's level",
    "M": "last month's level",
    "mm": "measured move (two-bar range from L)",
}
CURVES = (
    ("D", "reversal", "all", "plain"),
    ("D", "continuation", "all", "plain"),
    ("D", "inside", "all", "plain"),
    ("D", "continuation", "all", "near"),
    ("W", "continuation", "all", "exact_shared"),
    ("W", "continuation", "all", "rest"),
)
SPLITS = ("direction", "year", "liquid", "m_support", "w_support", "stop0")
# amendment A2.4: the venue's taker fee per fill, percent of notional (TVB-2, by the `crossed` flag)
TAKER = {"main": 0.0432, "xyz": 0.0125}
BOOK_RET = {
    "A": "ret_A",
    "B": "ret_B",
    "C": "ret_C",
    "D": "ret_D",
    "D5": "ret_D5",
    "ref": "ret_ref",
}
CAND_LABEL = {
    "week": "A2.1 the week's side at entry as a condition",
    "hourly": "A2.2 the hourly exit clock (hour red AND day red; entry stays the daily level)",
    "half": "A2.3 half at T1, the rest on the exit (book E)",
    "fees": "A2.4 the venue's taker fee on both legs",
    "under": "A2.5 'against' read as under water (close through the entry price AND the week against)",
}


# ----------------------------------------------------------------------------- mechanics


def beyond(price: float, ref: float, direction: str) -> bool:
    """Strictly beyond `ref` on the trade's side."""
    return price > ref if direction == "up" else price < ref


def against(close: float, open_: float, direction: str) -> bool:
    """A close on the wrong side of an open (strict; equality is not against)."""
    return close < open_ if direction == "up" else close > open_


def ladder(direction: str, level: float, ctx: dict, i: int, tfs: tuple) -> list[tuple[float, str]]:
    """The unbroken higher-timeframe levels strictly beyond L at the break, sorted outward.

    Fresh = the current bar of that timeframe has not traded through its previous bar's level
    before today (the same test as the chance study's entry-time class); nothing here depends on
    the day's own travel. Equal prices on two timeframes are one rung (strict ordering)."""
    rungs: list[tuple[float, str]] = []
    for tf in tfs:
        c = ctx[tf].get(i)
        if c is None or c["prev"] is None:
            continue
        lvl = c["prev"]["h"] if direction == "up" else c["prev"]["l"]
        if direction == "up":
            fresh = c["run_h"] is None or c["run_h"] <= lvl
        else:
            fresh = c["run_l"] is None or c["run_l"] >= lvl
        if fresh and beyond(lvl, level, direction):
            rungs.append((lvl, tf))
    rungs.sort(key=lambda r: r[0], reverse=(direction == "down"))
    out: list[tuple[float, str]] = []
    for r in rungs:
        if not out or beyond(r[0], out[-1][0], direction):
            out.append(r)
    return out


def structural(
    kind: str, direction: str, level: float, refbar: dict | None, ref_type: str | None
) -> tuple[str, float | None]:
    """T1's source for a unit: ('anchor', wick) for a structural magnitude, ('ladder', None) for
    a pattern with no magnitude of its own, ('stacked', None) for an inside bar whose predecessor
    is inside too, ('zero', None) when the anchor wick sits at L, ('unknown', None) when the bar
    before the setup bar is missing (data gap)."""
    if kind in ("continuation", "outside"):
        return "ladder", None
    if refbar is None:
        return "unknown", None
    wick = refbar["h"] if direction == "up" else refbar["l"]
    if kind == "reversal":
        return ("anchor", wick) if beyond(wick, level, direction) else ("zero", None)
    # inside break: the bar before the inside bar decides
    if ref_type is None:
        return "unknown", None
    if ref_type == "1":
        return "stacked", None
    if ref_type == "3" or (ref_type == "2U") != (direction == "up"):
        return ("anchor", wick) if beyond(wick, level, direction) else ("zero", None)
    return "ladder", None  # a 2 with the break: the with-trend inside bar


def targets(
    kind: str,
    direction: str,
    level: float,
    refbar: dict | None,
    ref_type: str | None,
    rungs: list[tuple[float, str]],
) -> dict:
    """T1 / T2 / T3 with their sources (prereg def. 5). None where the ladder runs out."""
    src, t1 = structural(kind, direction, level, refbar, ref_type)
    t1_src = src
    if src in ("ladder", "stacked"):
        if rungs:
            t1, t1_src = rungs[0]
        else:
            t1, t1_src = None, "none"
    elif src != "anchor":
        t1 = None
    rest = [r for r in rungs if t1 is not None and beyond(r[0], t1, direction)]
    t2, t2_src = rest[0] if rest else (None, None)
    t3, t3_src = rest[1] if len(rest) > 1 else (None, None)
    return {
        "t1": t1,
        "t1_src": t1_src,
        "t2": t2,
        "t2_src": t2_src,
        "t3": t3,
        "t3_src": t3_src,
        "anchor": src,
    }


def measured_move(
    direction: str, level: float, sbar: dict, refbar: dict | None, rungs: list
) -> dict | None:
    """Fork-1 variant: the two-bar range (setup bar + the bar before it) projected from L."""
    if refbar is None:
        return None
    # built in the venue's decimals so an exact touch fills (audit F1: a float projection can
    # land a hair beyond the printed price)
    rng = max(_dec(sbar["h"]), _dec(refbar["h"])) - min(_dec(sbar["l"]), _dec(refbar["l"]))
    if rng <= 0:
        return None
    t1_d = _dec(level) + rng if direction == "up" else _dec(level) - rng
    t1 = float(t1_d)
    rest = [r for r in rungs if beyond(r[0], t1, direction)]
    return {
        "t1": t1,
        "t1_d": t1_d,
        "t1_src": "mm",
        "t2": rest[0][0] if rest else None,
        "t2_src": rest[0][1] if rest else None,
        "t3": rest[1][0] if len(rest) > 1 else None,
        "t3_src": rest[1][1] if len(rest) > 1 else None,
    }


def own_close_days(tf: str, buckets: dict) -> dict[int, float]:
    """Day index -> that timeframe's open, for days that CLOSE a complete bar of it."""
    out = {}
    for b in buckets[tf]:
        if b["complete"]:
            out[b["days"][-1]] = b["o"]
    return out


def walk(
    daily: list[dict],
    i: int,
    direction: str,
    level: float,
    prices: dict[str, float | None],
    ctx: dict,
    last: int,
    own: dict | None = None,
) -> dict:
    """One pass over the days from the entry day through `last` (inclusive).

    Records the first touch day of every named target price (equality fills, decimals), the
    running favourable / adverse travel from L per day (price units), the daily-clock exit day
    (first close against the day's open AND the week's open) and, when `own` is given, the
    own-bar-clock exit day: {'close_days': {j: open}, 'confirm': {j: higher open} or None}.
    """
    lv = _dec(level)
    tgt = {
        k: (p if isinstance(p, Decimal) else _dec(p)) for k, p in prices.items() if p is not None
    }
    touch: dict[str, int | None] = dict.fromkeys(prices, None)
    fav: list[float] = []
    adv: list[float] = []
    run_f = run_a = 0.0
    exit_d = exit_o = exit_u = None
    for j in range(i, last + 1):
        bar = daily[j]
        bh, bl = _dec(bar["h"]), _dec(bar["l"])
        if direction == "up":
            f, a = bar["h"] - level, level - bar["l"]
        else:
            f, a = level - bar["l"], bar["h"] - level
        run_f, run_a = max(run_f, f), max(run_a, a)
        fav.append(run_f)
        adv.append(run_a)
        for k, p in tgt.items():
            if touch[k] is None:
                if k == "stop":  # the chance book's stop sits on the far side of the entry
                    hit = bl <= p if direction == "up" else bh >= p
                else:
                    hit = bh >= p if direction == "up" else bl <= p
                if hit:
                    touch[k] = j
        if exit_d is None:
            wk = ctx["W"].get(j)
            if (
                wk is not None
                and against(bar["c"], bar["o"], direction)
                and against(bar["c"], wk["open"], direction)
            ):
                exit_d = j
        if exit_u is None:  # amendment A2.5: through the entry price AND the week against
            wk = ctx["W"].get(j)
            if (
                wk is not None
                and against(bar["c"], level, direction)
                and against(bar["c"], wk["open"], direction)
            ):
                exit_u = j
        if own is not None and exit_o is None and j in own["close_days"]:
            ok = against(bar["c"], own["close_days"][j], direction)
            if ok and own["confirm"] is not None:
                ok = j in own["confirm"] and against(bar["c"], own["confirm"][j], direction)
            if ok:
                exit_o = j
    _ = lv
    return {
        "touch": touch,
        "fav": fav,
        "adv": adv,
        "exit_d": exit_d,
        "exit_o": exit_o,
        "exit_u": exit_u,
    }


def settle(
    w: dict,
    daily: list[dict],
    i: int,
    direction: str,
    level: float,
    cap_end: int | None,
    clock: str,
) -> dict:
    """Status and fills at one cap under one clock: exit / open / censored, the end day, the
    close the exit-only book fills at, travel through the end, days held."""
    exit_j = {"daily": w["exit_d"], "own": w["exit_o"], "under": w.get("exit_u")}[clock]
    if cap_end is None:
        if exit_j is None:
            return {"status": "censored"}
        status, end = "exit", exit_j
    elif exit_j is not None and exit_j <= cap_end:
        status, end = "exit", exit_j
    else:
        status, end = "open", cap_end
    sign = 1.0 if direction == "up" else -1.0
    close = daily[end]["c"]
    return {
        "status": status,
        "end": end,
        "days": end - i,
        "ret_c": sign * (close - level) / level * 100.0,
        "mfe": w["fav"][end - i] / level * 100.0,
        "mae": w["adv"][end - i] / level * 100.0,
    }


def book_fill(
    s: dict, w: dict, key: str, price: float | None, direction: str, level: float
) -> tuple[float | None, bool]:
    """A book's return in percent of L: the target when touched on or before the end day
    (targets are intraday, the exit is at the close), else the exit-only fill."""
    if s["status"] == "censored":
        return None, False
    j = w["touch"].get(key)
    if price is not None and j is not None and j <= s["end"]:
        sign = 1.0 if direction == "up" else -1.0
        return sign * (price - level) / level * 100.0, True
    return s["ret_c"], False


def long_cap_end(tf: str, i: int, daily: list[dict], buckets: dict, bucket_of: dict) -> int | None:
    """Last day index of the own-timeframe cap, None when the data ends first."""
    if tf == "D":
        j = i + CAP
        return j if j < len(daily) else None
    b = bucket_of[tf].get(i)
    bl = buckets[tf]
    k = None if b is None else b + CAP_OWN
    return bl[k]["days"][-1] if k is not None and k < len(bl) and bl[k]["complete"] else None


def hours_by_day(hourly: list[dict]) -> dict[int, list[int]]:
    """Day start (ms) -> the indices of that day's cached hours, ascending."""
    out: dict[int, list[int]] = {}
    for k, b in enumerate(hourly):
        out.setdefault(b["t"] - b["t"] % DAY, []).append(k)
    return out


def walk_hourly(
    hourly: list[dict],
    by_day: dict[int, list[int]],
    daily: list[dict],
    i: int,
    direction: str,
    level: float,
    prices: dict,
    cap_end: int | None,
) -> dict | None:
    """Amendment A2.2: the hourly exit clock. None when the entry day has no cached hours or no
    hour reached the level (the caller counts which). Otherwise the entry hour (the first hour of
    the entry day whose high / low reached L), the first hour at or after it that closed against
    its own open AND the day's open (fill = that close), the first touch hour of every named
    price from the entry hour on, and the status: exit / open (marked at the last hour of the cap
    day) / censored (the hourly data ends before the cap day's last hour)."""
    hs = by_day.get(daily[i]["t"])
    if not hs:
        return None
    lv = _dec(level)
    entry = None
    for h in hs:
        b = hourly[h]
        if (direction == "up" and _dec(b["h"]) >= lv) or (
            direction == "down" and _dec(b["l"]) <= lv
        ):
            entry = h
            break
    if entry is None:
        return {"status": "no_entry_hour"}
    last_h = None
    if cap_end is not None:
        cap_hs = by_day.get(daily[cap_end]["t"])
        if cap_hs and hourly[cap_hs[-1]]["t"] == daily[cap_end]["t"] + 23 * HOUR:
            last_h = cap_hs[-1]
    day_idx = {d["t"]: k for k, d in enumerate(daily)}
    tgt = {
        k: (p if isinstance(p, Decimal) else _dec(p)) for k, p in prices.items() if p is not None
    }
    touch: dict[str, int | None] = dict.fromkeys(prices, None)
    exit_h = None
    stop = last_h if last_h is not None else len(hourly) - 1
    for h in range(entry, stop + 1):
        b = hourly[h]
        bh, bl = _dec(b["h"]), _dec(b["l"])
        for k, p in tgt.items():
            if touch[k] is None and (bh >= p if direction == "up" else bl <= p):
                touch[k] = h
        di = day_idx.get(b["t"] - b["t"] % DAY)
        if (
            di is not None
            and against(b["c"], b["o"], direction)
            and against(b["c"], daily[di]["o"], direction)
        ):
            exit_h = h
            break
    if exit_h is not None:
        status, end = "exit", exit_h
    elif last_h is not None:
        status, end = "open", last_h
    else:
        return {"status": "censored", "entry": entry}
    sign = 1.0 if direction == "up" else -1.0
    close = hourly[end]["c"]
    return {
        "status": status,
        "entry": entry,
        "entry_hour": (hourly[entry]["t"] - daily[i]["t"]) // HOUR,
        "end": end,
        "hours": end - entry,
        "ret_c": sign * (close - level) / level * 100.0,
        "touch": touch,
    }


def hourly_fill(wh: dict, key: str, price, direction: str, level: float) -> tuple[float, bool]:
    """A book's fill on the hourly clock: the target when touched at or before the exit hour,
    else the exit hour's close."""
    h = wh["touch"].get(key)
    if price is not None and h is not None and h <= wh["end"]:
        sign = 1.0 if direction == "up" else -1.0
        return sign * (float(price) - level) / level * 100.0, True
    return wh["ret_c"], False


# ----------------------------------------------------------------------------- units per coin


def coin_manage_rows(
    meta: dict, daily: list[dict], hourly: list[dict] | None = None
) -> tuple[list[dict], Counter]:
    """The chance units of one coin with the management book's targets, exits and fills.
    `hourly`: the coin's closed hourly bars for amendment A2.2 (None or [] = no hourly arm)."""
    counts: Counter = Counter()
    units = coin_book_rows(meta, daily)
    if not units:
        return [], counts
    by_day = hours_by_day(hourly) if hourly else {}
    buckets = {tf: aggregate(daily, tf) for tf in ("W", "M", "Q")}
    ctx = _context(daily, buckets)
    bucket_of = {
        tf: {di: b for b, bk in enumerate(buckets[tf]) for di in bk["days"]} for tf in ("W", "M")
    }
    own_days = {"W": own_close_days("W", buckets), "M": own_close_days("M", buckets)}
    idx = {
        datetime.fromtimestamp(d["t"] / 1000, tz=timezone.utc).strftime("%Y-%m-%d"): k
        for k, d in enumerate(daily)
    }
    setups_at: dict[tuple[int, str], dict] = {}
    out: list[dict] = []
    for u in units:
        i = idx[u["date"]]
        direction, tf, level = u["direction"], u["tf"], u["level"]
        key = (i, direction)
        if key not in setups_at:
            evs = day_events(daily, i, ctx) or []
            for d_, _broken, setups in evs:
                setups_at[(i, d_)] = setups
        ptype, sbar, ref_type, refbar = setups_at[key][tf]
        if ctx["W"].get(i) is None:
            counts[f"no_week_context_{tf}"] += 1
            continue
        rungs = ladder(direction, level, ctx, i, RUNGS[tf])
        tg = targets(u["kind"], direction, level, refbar, ref_type, rungs)
        counts[f"anchor_{tf}_{u['kind']}_{tg['anchor']}"] += 1
        mm = None
        if u["kind"] == "continuation" or (u["kind"] == "inside" and tg["anchor"] == "ladder"):
            mm = measured_move(direction, level, sbar, refbar, rungs)
        # one R in the venue's decimals, exactly as the chance walker builds it (audit F1)
        r_d = (_dec(level) - _dec(u["stop"])).copy_abs()
        one_r_d = _dec(level) + r_d if direction == "up" else _dec(level) - r_d
        one_r = float(one_r_d)
        prices = {
            "t1": tg["t1"],
            "t2": tg["t2"],
            "t3": tg["t3"],
            "one_r": one_r_d,
            "stop": u["stop"],  # the chance book's stop, for the reference's own fill day
            "mm1": mm["t1_d"] if mm else None,
            "mm2": mm["t2"] if mm else None,
            "mm3": mm["t3"] if mm else None,
        }
        cap_end = i + CAP if i + CAP < len(daily) else None
        lcap_end = long_cap_end(tf, i, daily, buckets, bucket_of) if tf != "D" else cap_end
        last = min(len(daily) - 1, max(x for x in (cap_end, lcap_end, i) if x is not None))
        if cap_end is None or (tf != "D" and lcap_end is None):
            last = len(daily) - 1
        own = None
        if tf in ("W", "M"):
            own = {
                "close_days": own_days[tf],
                "confirm": (
                    {j: c["open"] for j, c in ctx["M"].items() if c is not None}
                    if tf == "W"
                    else None
                ),
            }
            if tf == "W" and ctx["M"].get(i) is None:
                own = None
                counts["no_month_context_W"] += 1
        # the reference's horizon (five bars of the unit's timeframe): book D5 settles there
        ref_end = horizon_ends(tf, i, daily, buckets, bucket_of)[5]
        if ref_end is not None and ref_end > last:
            last = ref_end
        w = walk(daily, i, direction, level, prices, ctx, last, own)
        s = settle(w, daily, i, direction, level, cap_end, "daily")
        s5 = settle(w, daily, i, direction, level, ref_end, "daily")
        wk = ctx["W"][i]
        if direction == "up":
            w_support = "with" if level > wk["open"] else "against"
        else:
            w_support = "with" if level < wk["open"] else "against"
        row = dict(u)
        row.update(
            {
                "t1": tg["t1"],
                "t1_src": tg["t1_src"],
                "t2": tg["t2"],
                "t2_src": tg["t2_src"],
                "t3": tg["t3"],
                "t3_src": tg["t3_src"],
                "anchor": tg["anchor"],
                "ladder_len": sum(1 for k in ("t1", "t2", "t3") if tg[k] is not None),
                "w_support": w_support,
                "status": s["status"],
                "ret_ref": u["ret5"],
            }
        )
        for k in ("t1", "t2", "t3", "one_r", "mm1", "stop"):
            j = w["touch"][k]
            row[f"{k}_k"] = None if j is None else j - i  # first touch, offset from entry
        row["ref_k"] = None if ref_end is None else ref_end - i
        # the reference's own fill day: the stop (first, or the same day as one R), else one R,
        # else its fifth-bar mark (audit F4)
        sk, rk, fk = row["stop_k"], row["one_r_k"], row["ref_k"]
        if fk is None:
            row["days_ref"] = None
        elif sk is not None and sk <= fk and (rk is None or sk <= rk):
            row["days_ref"] = sk
        elif rk is not None and rk <= fk:
            row["days_ref"] = rk
        else:
            row["days_ref"] = fk
        if s["status"] != "censored":
            row.update(
                {
                    "exit_k": s["days"] if s["status"] == "exit" else None,
                    "days": s["days"],
                    "ret_C": s["ret_c"],
                    "mfe_x": s["mfe"],
                    "mae_x": s["mae"],
                    "mfe_c": None if cap_end is None else w["fav"][cap_end - i] / level * 100.0,
                    "mae_c": None if cap_end is None else w["adv"][cap_end - i] / level * 100.0,
                }
            )
            row["ret_A"], row["hit_A"] = book_fill(s, w, "t1", tg["t1"], direction, level)
            row["ret_B"], row["hit_B"] = book_fill(s, w, "t2", tg["t2"], direction, level)
            row["ret_D"], row["hit_D"] = book_fill(s, w, "one_r", one_r, direction, level)
            # amendment A2.5: the under-water exit on the same walk, same cap
            su = settle(w, daily, i, direction, level, cap_end, "under")
            row["status_u"] = su["status"]
            if su["status"] != "censored":
                row["ret_C_u"] = su["ret_c"]
                row["days_u"] = su["days"]
                row["exit_k_u"] = su["days"] if su["status"] == "exit" else None
                row["mae_u"] = su["mae"]
                row["ret_A_u"], row["hit_A_u"] = book_fill(su, w, "t1", tg["t1"], direction, level)
                row["ret_D_u"], row["hit_D_u"] = book_fill(su, w, "one_r", one_r, direction, level)
            # amendment A2.2: the hourly exit clock on the hourly-window subset
            row["status_h"] = None
            if by_day:
                wh = walk_hourly(hourly, by_day, daily, i, direction, level, prices, cap_end)
                if wh is None:
                    counts["hourly_outside_window"] += 1
                elif wh["status"] == "no_entry_hour":
                    counts["hourly_no_entry_hour"] += 1
                    row["status_h"] = "no_entry_hour"
                else:
                    row["status_h"] = wh["status"]
                    counts[f"hourly_{wh['status']}"] += 1
                    if wh["status"] != "censored":
                        row["entry_h"] = wh["entry_hour"]
                        row["hours_h"] = wh["hours"]
                        row["exit_h"] = wh["hours"] if wh["status"] == "exit" else None
                        row["ret_C_h"] = wh["ret_c"]
                        row["ret_A_h"], row["hit_A_h"] = hourly_fill(
                            wh, "t1", tg["t1"], direction, level
                        )
                        row["ret_D_h"], row["hit_D_h"] = hourly_fill(
                            wh, "one_r", one_r_d, direction, level
                        )
                        t1h = wh["touch"].get("t1")
                        row["t1_h"] = (
                            t1h - wh["entry"] if t1h is not None and t1h <= wh["end"] else None
                        )
            # each book's own holding time: the day it filled its target, else the exit / mark
            # day (audit F4)
            row["days_A"] = row["t1_k"] if row["hit_A"] else s["days"]
            row["days_B"] = row["t2_k"] if row["hit_B"] else s["days"]
            row["days_C"] = s["days"]
            row["days_D"] = row["one_r_k"] if row["hit_D"] else s["days"]
            end = s["end"]
            row["reached1"] = (
                tg["t1"] is not None and w["touch"]["t1"] is not None and w["touch"]["t1"] <= end
            )
            row["reached2"] = (
                row["reached1"]
                and tg["t2"] is not None
                and w["touch"]["t2"] is not None
                and w["touch"]["t2"] <= end
            )
            row["reached3"] = (
                row["reached2"]
                and tg["t3"] is not None
                and w["touch"]["t3"] is not None
                and w["touch"]["t3"] <= end
            )
            # the exit's own "saw the target anyway": T1 touched after the exit, inside the cap.
            # None (unknown) when the 20-day follow-up is not complete (audit F3)
            j1 = w["touch"]["t1"]
            if cap_end is None:
                row["later1"] = None
            else:
                row["later1"] = (
                    s["status"] == "exit"
                    and not row["reached1"]
                    and tg["t1"] is not None
                    and j1 is not None
                    and end < j1 <= cap_end
                )
            # book D's own early exit: one R touched after the exit, inside the cap
            jr = w["touch"]["one_r"]
            if cap_end is None:
                row["later_r"] = None
            else:
                row["later_r"] = (
                    s["status"] == "exit"
                    and not row["hit_D"]
                    and jr is not None
                    and end < jr <= cap_end
                )
            # the no-exit ceiling: touched any time inside the cap
            if cap_end is not None:
                row["ceil1"] = tg["t1"] is not None and j1 is not None and j1 <= cap_end
                row["ceil2"] = (
                    row["ceil1"]
                    and tg["t2"] is not None
                    and w["touch"]["t2"] is not None
                    and w["touch"]["t2"] <= cap_end
                )
                row["ceil3"] = (
                    row["ceil2"]
                    and tg["t3"] is not None
                    and w["touch"]["t3"] is not None
                    and w["touch"]["t3"] <= cap_end
                )
            else:
                row["ceil1"] = row["ceil2"] = row["ceil3"] = None
            # product 2's stopped-then-saw-the-target on the same rows (5-bar travel >= 1R)
            row["stop_saw"] = u["out5"] == "stop" and u["mfe5"] is not None and u["mfe5"] >= 1.0
            # book D5: the same target and the same five-bar horizon as the reference, only the
            # stop swapped for the close exit (audit F2); its own early-exit flag is read inside
            # that same window, so H3 compares like with like
            row["status5"] = s5["status"]
            if s5["status"] != "censored":
                row["ret_D5"], row["hit_D5"] = book_fill(s5, w, "one_r", one_r, direction, level)
                row["days_D5"] = row["one_r_k"] if row["hit_D5"] else s5["days"]
                # unknown (null) when the data ends before the fifth bar: the window is incomplete
                row["later_r5"] = (
                    None
                    if ref_end is None
                    else (
                        s5["status"] == "exit"
                        and not row["hit_D5"]
                        and jr is not None
                        and s5["end"] < jr <= ref_end
                    )
                )
            else:
                row["ret_D5"] = row["hit_D5"] = row["days_D5"] = row["later_r5"] = None
            # fork 1: the measured move
            if mm is not None:
                row["mm_t1"] = mm["t1"]
                row["ret_A_mm"], row["hit_A_mm"] = book_fill(
                    s, w, "mm1", mm["t1"], direction, level
                )
                row["ret_B_mm"], row["hit_B_mm"] = book_fill(
                    s, w, "mm2", mm["t2"], direction, level
                )
                row["reached1_mm"] = w["touch"]["mm1"] is not None and w["touch"]["mm1"] <= end
            else:
                row["mm_t1"] = None
        else:
            counts[f"censored_{tf}"] += 1
        # fork 2: weekly and monthly units at the long cap, both clocks
        if tf in ("W", "M"):
            sl = settle(w, daily, i, direction, level, lcap_end, "daily")
            row["status_long"] = sl["status"]
            if sl["status"] != "censored":
                row["ret_C_long"] = sl["ret_c"]
                row["days_long"] = sl["days"]
                row["ret_A_long"], _ = book_fill(sl, w, "t1", tg["t1"], direction, level)
                row["reached1_long"] = (
                    tg["t1"] is not None
                    and w["touch"]["t1"] is not None
                    and w["touch"]["t1"] <= sl["end"]
                )
            if own is not None:
                so = settle(w, daily, i, direction, level, lcap_end, "own")
                row["status_own"] = so["status"]
                if so["status"] != "censored":
                    row["ret_C_own"] = so["ret_c"]
                    row["days_own"] = so["days"]
                    row["ret_A_own"], _ = book_fill(so, w, "t1", tg["t1"], direction, level)
                    row["reached1_own"] = (
                        tg["t1"] is not None
                        and w["touch"]["t1"] is not None
                        and w["touch"]["t1"] <= so["end"]
                    )
            else:
                row["status_own"] = "n/a"
        out.append(row)
        counts[f"units_{tf}"] += 1
    return out, counts


# ----------------------------------------------------------------------------- aggregation


def select(df: pd.DataFrame, tf: str, kind: str, level: str, cls: str) -> pd.DataFrame:
    sub = df[(df["tf"] == tf) & (df["kind"] == kind) & flag_mask(df, level)]
    if cls == "rest":
        return sub[~sub["cls"].isin(STACKED)]
    if cls == "stacked":
        return sub[sub["cls"].isin(STACKED)]
    if cls == "all":
        return sub
    return sub[sub["cls"] == cls]


def share(mask: pd.Series) -> dict:
    n = int(mask.notna().sum()) if mask.dtype == object else int(len(mask))
    k = int(mask.fillna(False).astype(bool).sum())
    lo, hi = wilson(k, n) if n else (math.nan, math.nan)
    return {"k": k, "n": n, "p": k / n if n else math.nan, "lo": lo, "hi": hi}


def book_stats(ret: pd.Series, dates: pd.Series, hit: pd.Series | None, days: pd.Series) -> dict:
    v = ret.notna()
    ret, dates, days = ret[v].astype(float), dates[v], days[v]
    m = int(len(ret))
    if m == 0:
        return {"n": 0}
    by_day = (ret.groupby(dates).sum().sort_index() * UNIT_USD / 100.0).astype(float)
    cum = by_day.cumsum()
    peak = cum.cummax().clip(lower=0.0)
    return {
        "n": m,
        "avg_pct": float(ret.mean()),
        "med_pct": float(ret.median()),
        "win": float((ret > 0).mean()),
        "at_target": None if hit is None else float(hit[v].astype(bool).mean()),
        "total_usd": float(ret.sum() * UNIT_USD / 100.0),
        "max_dd_usd": float(min(0.0, (cum - peak).min())),
        "med_days": float(days.median()),
        "curve": cum,
    }


def paired(a: pd.Series, b: pd.Series) -> dict:
    d = (a.astype(float) - b.astype(float)).dropna()
    n = int(len(d))
    if n < 2:
        return {"n": n, "diff": math.nan, "lo": math.nan, "hi": math.nan}
    m, sd = float(d.mean()), float(d.std(ddof=1))
    h = 1.96 * sd / math.sqrt(n)
    return {"n": n, "diff": m, "lo": m - h, "hi": m + h}


def cell(df: pd.DataFrame) -> dict:
    """Every number for one cell (prereg def. 9-12), headline cap and clock."""
    c: dict = {"units": int(len(df)), "dates": int(df["date"].nunique())}
    live = df[df["status"] != "censored"]
    c["n"] = int(len(live))
    c["censored"] = int(len(df) - len(live))
    if c["n"] == 0:
        return c
    has1 = live["t1"].notna()
    c["has_t1"] = float(has1.mean())
    c["has_t2"] = float(live["t2"].notna().mean())
    c["has_t3"] = float(live["t3"].notna().mean())
    c["anchor"] = {k: int(v) for k, v in live["anchor"].value_counts().items()}
    c["t1_src"] = {k: int(v) for k, v in live["t1_src"].value_counts().items()}
    t1u = live[has1]
    c["reach1"] = share(t1u["reached1"])
    r1 = t1u[t1u["reached1"].astype(bool) & t1u["t2"].notna()]
    c["reach2"] = share(r1["reached2"])
    r2 = r1[r1["reached2"].astype(bool) & r1["t3"].notna()]
    c["reach3"] = share(r2["reached3"])
    capped = t1u[t1u["ceil1"].notna()]
    c["ceil1"] = share(capped["ceil1"])
    c1 = capped[capped["ceil1"].astype(bool) & capped["t2"].notna()]
    c["ceil2"] = share(c1["ceil2"])
    c2 = c1[c1["ceil2"].astype(bool) & c1["t3"].notna()]
    c["ceil3"] = share(c2["ceil3"])
    c["exited"] = float((live["status"] == "exit").mean())
    c["open"] = float((live["status"] == "open").mean())
    c["entry_day_exit"] = float((live["exit_k"] == 0).mean())
    c["med_days"] = float(live["days"].median())
    # how the pre-T1 exits died
    died = t1u[(~t1u["reached1"].astype(bool)) & (t1u["status"] == "exit")]
    c["died"] = {
        "n": int(len(died)),
        "entry_day": float((died["exit_k"] == 0).mean()) if len(died) else math.nan,
        "med_days": float(died["days"].median()) if len(died) else math.nan,
        "avg_pct": float(died["ret_C"].mean()) if len(died) else math.nan,
        "avg_r": float((died["ret_C"] / died["r_pct"]).mean()) if len(died) else math.nan,
        "stop0": float(died["stop0"].astype(bool).mean()) if len(died) else math.nan,
        "later1": share(died["later1"]) if len(died) else {"k": 0, "n": 0, "p": math.nan},
        "stop_saw": share(t1u[t1u["out5"] == "stop"]["stop_saw"]),
        "stopped5": float((t1u["out5"] == "stop").mean()),
    }
    # book D's early exits, on the T1 cohort the stop comparison uses (audit F2): the 20-day
    # window (unknown without a complete cap, audit F3) and the five-bar window matched to the
    # chance book's stopped-then-saw-one-R
    died_r = t1u[(~t1u["hit_D"].astype(bool)) & (t1u["status"] == "exit")]
    died_r5 = t1u[(t1u["status5"] == "exit") & (~t1u["hit_D5"].fillna(False).astype(bool))]
    c["died_r"] = {
        "n": int(len(died_r)),
        "later_r": share(died_r["later_r"]) if len(died_r) else {"k": 0, "n": 0, "p": math.nan},
        "n5": int(len(died_r5)),
        "later_r5": share(died_r5["later_r5"]) if len(died_r5) else {"k": 0, "n": 0, "p": math.nan},
    }
    c["med_t1_pct"] = (
        float(((t1u["t1"] - t1u["level"]).abs() / t1u["level"] * 100).median())
        if len(t1u)
        else math.nan
    )
    c["med_r_pct"] = float(live["r_pct"].median())
    # the tail
    mae_r = live["mae_x"] / live["r_pct"]
    c["tail"] = {
        "mae_gt1": float((mae_r > 1).mean()),
        "mae_gt2": float((mae_r > 2).mean()),
        "mae_gt3": float((mae_r > 3).mean()),
        "worst_pct": float(live["ret_C"].min()),
        "med_mae_r": float(mae_r.median()),
        "med_mfe_r": float((live["mfe_x"] / live["r_pct"]).median()),
        "to_cap": c["open"],
    }
    # the books on the same rows: units with a T1 and a reference return
    rows = t1u[t1u["ret_ref"].notna()]
    c["book_rows"] = int(len(rows))
    c["book_dates"] = int(rows["date"].nunique())
    c["has_t2_in_books"] = float(rows["t2"].notna().mean()) if len(rows) else math.nan
    c["books"] = {}
    for b in BOOKS:
        hit = {"A": "hit_A", "B": "hit_B", "D": "hit_D", "D5": "hit_D5", "C": None, "ref": None}[b]
        st = book_stats(
            rows[f"ret_{b}"],
            rows["date"],
            None if hit is None else rows[hit],
            rows[f"days_{b}"],  # each book's own holding time (audit F4)
        )
        if b == "ref" and st.get("n"):
            st["at_target"] = float((rows["out5"] == "one_r").mean())
        c["books"][b] = st
    allc = book_stats(live["ret_C"], live["date"], None, live["days"])
    c["book_C_all"] = allc
    c["diff"] = {
        f"{b}_minus_ref": paired(rows[f"ret_{b}"], rows["ret_ref"])
        for b in ("A", "B", "C", "D", "D5")
    }
    # fork 1: the measured move on the units that have it
    if "mm_t1" in live:
        mmu = rows[rows["mm_t1"].notna()]
        if len(mmu):
            c["mm"] = {
                "n": int(len(mmu)),
                "reach1_head": share(mmu["reached1"]),
                "reach1_mm": share(mmu["reached1_mm"]),
                "A_head": book_stats(mmu["ret_A"], mmu["date"], mmu["hit_A"], mmu["days"]),
                "A_mm": book_stats(mmu["ret_A_mm"], mmu["date"], mmu["hit_A_mm"], mmu["days"]),
                "B_head": book_stats(mmu["ret_B"], mmu["date"], mmu["hit_B"], mmu["days"]),
                "B_mm": book_stats(mmu["ret_B_mm"], mmu["date"], mmu["hit_B_mm"], mmu["days"]),
                "med_t1_head_pct": float(
                    ((mmu["t1"] - mmu["level"]).abs() / mmu["level"] * 100).median()
                ),
                "med_t1_mm_pct": float(
                    ((mmu["mm_t1"] - mmu["level"]).abs() / mmu["level"] * 100).median()
                ),
            }
    return c


def cell_clocks(df: pd.DataFrame) -> dict | None:
    """Fork 2: weekly / monthly units at the long cap, daily clock beside own-bar clock."""
    if "status_own" not in df:
        return None
    both = df[
        (df["status_long"].isin(["exit", "open"])) & (df["status_own"].isin(["exit", "open"]))
    ]
    if both.empty:
        return None
    t1 = both[both["t1"].notna()]
    return {
        "n": int(len(both)),
        "dates": int(both["date"].nunique()),
        "daily": {
            "exited": float((both["status_long"] == "exit").mean()),
            "med_days": float(both["days_long"].median()),
            "reach1": share(t1["reached1_long"]),
            "C": book_stats(both["ret_C_long"], both["date"], None, both["days_long"]),
            "A": book_stats(t1["ret_A_long"], t1["date"], None, t1["days_long"]),
        },
        "own": {
            "exited": float((both["status_own"] == "exit").mean()),
            "med_days": float(both["days_own"].median()),
            "reach1": share(t1["reached1_own"]),
            "C": book_stats(both["ret_C_own"], both["date"], None, both["days_own"]),
            "A": book_stats(t1["ret_A_own"], t1["date"], None, t1["days_own"]),
        },
        "C_diff": paired(both["ret_C_own"], both["ret_C_long"]),
    }


# ----------------------------------------------------------------------------- tables


def _g(n: int, text: str) -> str:
    return f"({text})" if n < MIN_CELL else text


def _sh(s: dict) -> str:
    if not s or not s.get("n"):
        return "-"
    t = f"{100 * s['p']:.1f}% [{100 * s['lo']:.0f}, {100 * s['hi']:.0f}] n={s['n']:,}"
    return _g(s["n"], t)


def _f(x, fmt: str = "+.2f") -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "-"
    return format(x, fmt)


def classes_for(tf: str) -> tuple:
    return CLASSES if tf == "D" else CLASSES[1:]


def iter_cells(df: pd.DataFrame, tf: str, levels: tuple = ("all",), classes: tuple | None = None):
    for kind in KINDS:
        for level in levels:
            for cls in classes or classes_for(tf):
                part = select(df, tf, kind, level, cls)
                if part.empty:
                    continue
                yield kind, level, cls, part


def table_reach(df: pd.DataFrame, tf: str, title: str, cells: dict) -> list[str]:
    lines = [f"### {title}", ""]
    lines.append(
        "| setup | class | units | dates | censored | has T1 / T2 / T3 | median T1 distance % (R %) | T1 before the exit [95%] | "
        "T1 any time in the cap | T2 after T1 | T3 after T2 | exited | open at cap | exit at entry close | median days |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for kind, level, cls, part in iter_cells(df, tf):
        c = cells[(tf, kind, level, cls)]
        if not c.get("n"):
            continue
        lines.append(
            f"| {kind} | {cls} | {c['n']:,} | {c['dates']:,} | {c['censored']:,} | "
            f"{_pct(c['has_t1'])} / {_pct(c['has_t2'])} / {_pct(c['has_t3'])} | "
            f"{_f(c['med_t1_pct'], '.2f')} ({c['med_r_pct']:.2f}) | {_sh(c['reach1'])} | "
            f"{_sh(c['ceil1'])} | {_sh(c['reach2'])} | {_sh(c['reach3'])} | {_pct(c['exited'])} | "
            f"{_pct(c['open'])} | {_pct(c['entry_day_exit'])} | {c['med_days']:.0f} |"
        )
    lines += [
        "",
        "T1 before the exit = of the units with a T1, the share that touched it on or before the exit day "
        "(a touch is intraday, the exit is at the close). T2 after T1 = of the units that reached T1 and "
        "have a T2. 'Any time in the cap' ignores the exit (the ceiling). Cells in parentheses hold "
        "fewer than 30. Censored = the data ends before the exit and before the cap (excluded).",
        "",
    ]
    return lines


def table_deaths(df: pd.DataFrame, tf: str, title: str, cells: dict) -> list[str]:
    lines = [f"### {title}", ""]
    lines.append(
        "| setup | class | pre-T1 exits | at the entry close | median days | avg % | avg R | "
        "entry day went outside | touched T1 later, inside the cap | book D: exited before one R, touched one R later | "
        "chance book on the same units: stopped by 5 | stopped, saw the target anyway |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for kind, level, cls, part in iter_cells(df, tf):
        c = cells[(tf, kind, level, cls)]
        if not c.get("n"):
            continue
        d = c["died"]
        g = lambda t: _g(d["n"], t)  # noqa: E731
        lines.append(
            f"| {kind} | {cls} | {d['n']:,} | {g(_pct(d['entry_day']))} | {g(_f(d['med_days'], '.0f'))} | "
            f"{g(_f(d['avg_pct']))} | {g(_f(d['avg_r']))} | {g(_pct(d['stop0']))} | {_sh(d['later1'])} | "
            f"{_sh(c['died_r']['later_r'])} | {_pct(d['stopped5'])} | {_sh(d['stop_saw'])} |"
        )
    lines += [
        "",
        "Pre-T1 exits = units with a T1 that exited on the close rule before touching it. 'Touched T1 "
        "later' = the exit's own 'saw the target anyway'; beside it, on the same units, the chance book's "
        "stop share and its stopped-then-saw-one-R share (5-bar travel).",
        "",
    ]
    return lines


def table_tail(df: pd.DataFrame, tf: str, title: str, cells: dict) -> list[str]:
    lines = [f"### {title}", ""]
    lines.append(
        "| setup | class | n | MAE over 1R | over 2R | over 3R | median MAE R | median MFE R | worst trade % | held to the cap |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for kind, level, cls, part in iter_cells(df, tf):
        c = cells[(tf, kind, level, cls)]
        if not c.get("n"):
            continue
        t = c["tail"]
        g = lambda s: _g(c["n"], s)  # noqa: E731
        lines.append(
            f"| {kind} | {cls} | {c['n']:,} | {g(_pct(t['mae_gt1']))} | {g(_pct(t['mae_gt2']))} | "
            f"{g(_pct(t['mae_gt3']))} | {g(_f(t['med_mae_r'], '.2f'))} | {g(_f(t['med_mfe_r'], '.2f'))} | "
            f"{g(_f(t['worst_pct']))} | {_pct(t['to_cap'])} |"
        )
    lines += [
        "",
        "MAE = the furthest adverse travel from L through the exit (or the cap mark), in units of the "
        "setup-bar R; a stopless book lives on this tail.",
        "",
    ]
    return lines


def table_books(
    df: pd.DataFrame, tf: str, title: str, cells: dict, levels: tuple = ("all",)
) -> list[str]:
    lines = [f"### {title}", ""]
    lines.append(
        "| setup | flag | class | book | trades | avg % per trade | median % | closed in profit | closed at the target | "
        "total $ at 1,000 per trade | max drawdown $ | median days | minus reference [95%] |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for kind, level, cls, part in iter_cells(df, tf, levels):
        c = cells[(tf, kind, level, cls)]
        if not c.get("n"):
            continue
        for b in BOOKS if c.get("book_rows") else ():
            s = c["books"][b]
            if not s.get("n"):
                continue
            g = lambda t: _g(s["n"], t)  # noqa: E731
            dkey = f"{b}_minus_ref"
            if b == "ref":
                dtxt = "-"
            else:
                d = c["diff"][dkey]
                dtxt = g(f"{_f(d['diff'])} [{_f(d['lo'])}, {_f(d['hi'])}]")
            lines.append(
                f"| {kind} | {level} | {cls} | {BOOK_LABEL[b]} | {s['n']:,} | {g(_f(s['avg_pct']))} | "
                f"{g(_f(s['med_pct']))} | {g(_pct(s['win']))} | {g(_pct(s['at_target']))} | "
                f"{g(_usd(s['total_usd']))} | {g(_usd(s['max_dd_usd']))} | {s['med_days']:.0f} | {dtxt} |"
            )
        ca = c["book_C_all"]
        if ca.get("n") and (not c.get("book_rows") or ca["n"] != c["books"]["C"].get("n")):
            lines.append(
                f"| {kind} | {level} | {cls} | C on every unit (with or without a T1) | {ca['n']:,} | "
                f"{_f(ca['avg_pct'])} | {_f(ca['med_pct'])} | {_pct(ca['win'])} | - | {_usd(ca['total_usd'])} | "
                f"{_usd(ca['max_dd_usd'])} | {ca['med_days']:.0f} | - |"
            )
    lines += [
        "",
        "Same rows for all six books: units with a T1 and a 5-bar reference return. One unit of notional "
        "per trade, long or short as the break, no leverage, fees, funding or slippage, every trade taken, "
        "no compounding; open trades marked at the cap's close (day 20), D5 and the reference at the "
        "fifth bar of the unit's timeframe. Median days = each book's own holding time (the day its "
        "target filled, else its exit or mark day). "
        "Dollar columns are the SUM of equal-size trades at 1,000 dollars each, not an account balance. "
        "'Minus reference' is the paired per-trade difference against the chance book on the identical "
        "units, with a normal 95% interval; the holding periods differ (shown), so A / B / C against the "
        "reference is rule against rule, while D changes only the loss side.",
        "",
    ]
    return lines


def table_mm(df: pd.DataFrame, tf: str, title: str, cells: dict) -> list[str]:
    lines = [f"### {title}", ""]
    lines.append(
        "| setup | class | units with a measured move | median T1 distance % level / move | "
        "T1 reached before the exit: level | move | book A avg %: level | move | book B avg %: level | move |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for kind, level, cls, part in iter_cells(df, tf):
        c = cells[(tf, kind, level, cls)]
        m = c.get("mm")
        if not m:
            continue
        g = lambda t: _g(m["n"], t)  # noqa: E731
        lines.append(
            f"| {kind} | {cls} | {m['n']:,} | {m['med_t1_head_pct']:.2f} / {m['med_t1_mm_pct']:.2f} | "
            f"{_sh(m['reach1_head'])} | {_sh(m['reach1_mm'])} | {g(_f(m['A_head']['avg_pct']))} | "
            f"{g(_f(m['A_mm']['avg_pct']))} | {g(_f(m['B_head']['avg_pct']))} | {g(_f(m['B_mm']['avg_pct']))} |"
        )
    lines += [
        "",
        "Fork 1, declared variant: for the 2-2 continuation and the with-trend inside break, T1 as the "
        "measured move (the setup bar's and the prior bar's combined range projected from L) beside the "
        "headline (the first unbroken weekly / monthly level). Same units, same exit, same cap; nothing "
        "promoted.",
        "",
    ]
    return lines


def table_clocks(df: pd.DataFrame, tf: str, title: str, clocks: dict) -> list[str]:
    lines = [f"### {title}", ""]
    lines.append(
        "| setup | class | n | dates | exited: daily clock | own-bar clock | median days: daily | own | "
        "T1 before the exit: daily | own | book C avg %: daily | own | own minus daily [95%] | book A avg %: daily | own |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for kind, level, cls, part in iter_cells(df, tf):
        k = clocks.get((tf, kind, level, cls))
        if not k:
            continue
        g = lambda t: _g(k["n"], t)  # noqa: E731
        d = k["C_diff"]
        lines.append(
            f"| {kind} | {cls} | {k['n']:,} | {k['dates']:,} | {_pct(k['daily']['exited'])} | {_pct(k['own']['exited'])} | "
            f"{k['daily']['med_days']:.0f} | {k['own']['med_days']:.0f} | {_sh(k['daily']['reach1'])} | {_sh(k['own']['reach1'])} | "
            f"{g(_f(k['daily']['C'].get('avg_pct', math.nan)))} | {g(_f(k['own']['C'].get('avg_pct', math.nan)))} | "
            f"{g(f'{_f(d["diff"])} [{_f(d["lo"])}, {_f(d["hi"])}]')} | "
            f"{g(_f(k['daily']['A'].get('avg_pct', math.nan)))} | {g(_f(k['own']['A'].get('avg_pct', math.nan)))} |"
        )
    lines += [
        "",
        f"Fork 2, declared variant: {tf} units at a cap of {CAP_OWN} of their own bars, the headline "
        "daily clock (a red day with the week red at that close) beside the own-bar clock (a weekly unit: "
        "a red weekly close with the month red at that close; a monthly unit: a red monthly close). Same "
        "units, both settled at the same cap; nothing promoted.",
        "",
    ]
    return lines


def table_hypotheses(cells: dict) -> list[str]:
    lines = ["### Hypotheses, read as declared (plain daily units)", ""]
    lines.append(
        "| setup | n | H2: D5 minus the reference (same target, same five-bar horizon, only the stop swapped) [95%] | "
        "D minus the reference (20-day cap) [95%] | "
        "H3: D5 exited before one R, touched one R inside the five bars | chance book: stopped, saw one R inside the five bars | "
        "D exited before one R, touched one R inside 20 days (complete follow-up only) | pre-T1 exits that touched T1 inside 20 days (complete follow-up only) |"
    )
    lines.append("|---|---|---|---|---|---|---|---|")
    for kind in KINDS:
        c = cells.get(("D", kind, "all", "plain"))
        if not c or not c.get("book_rows"):
            continue
        d = c["diff"]["D_minus_ref"]
        d5 = c["diff"]["D5_minus_ref"]
        lines.append(
            f"| {kind} | {d5['n']:,} | {_f(d5['diff'])} [{_f(d5['lo'])}, {_f(d5['hi'])}] | "
            f"{_f(d['diff'])} [{_f(d['lo'])}, {_f(d['hi'])}] | {_sh(c['died_r']['later_r5'])} | "
            f"{_sh(c['died']['stop_saw'])} | {_sh(c['died_r']['later_r'])} | {_sh(c['died']['later1'])} |"
        )
    lines += [
        "",
        "H2 (the owner's suspect): swapping the setup-bar stop for the close exit lifts the average trade "
        "of every plain daily pattern -- D5 is the stop-isolating read (same target, same horizon, same "
        "mark day as the reference; audit F2); D adds the longer horizon. H3 (the lead's counter): the "
        "close exit is itself an early exit at least as often as the stop was -- compare D5's column with "
        "the chance book's (same cohort: units with a T1; same five-bar window); the two right-hand "
        "columns are the 20-day reads on the units whose follow-up is complete (audit F3). Neither "
        "promotes anything.",
        "",
    ]
    return lines


def table_splits(df: pd.DataFrame, tf: str = "D") -> list[str]:
    lines = [
        f"### Splits, {tf} units, plain class (entry-time context, one retrospective label, one outcome-side split)",
        "",
    ]
    lines.append(
        "| split | value | setup | n | T1 before the exit | book A avg % | book C avg % | book D avg % | reference avg % |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|")
    base = df[(df["tf"] == tf) & (df["cls"] == "plain") & (df["status"] != "censored")]
    for col in SPLITS:
        for val in sorted(base[col].dropna().unique(), key=str):
            for kind in KINDS:
                part = base[(base[col] == val) & (base["kind"] == kind)]
                rows = part[part["t1"].notna() & part["ret_ref"].notna()]
                if rows.empty:
                    continue
                g = lambda t: _g(len(rows), t)  # noqa: E731
                lines.append(
                    f"| {col} | {val} | {kind} | {len(rows):,} | {_sh(share(rows['reached1']))} | "
                    f"{g(_f(rows['ret_A'].mean()))} | {g(_f(rows['ret_C'].mean()))} | "
                    f"{g(_f(rows['ret_D'].mean()))} | {g(_f(rows['ret_ref'].mean()))} |"
                )
    lines += [
        "",
        "direction, year, m_support and w_support are known at the break. `liquid` is the census's "
        "snapshot label (median notional over the LAST 30 days of the data), inherited for parity with "
        "products 1 and 2 and RETROSPECTIVE: a trader at a 2024 break did not know it (audit F6). "
        "`stop0` (the entry day traded through the far side of the setup bar, the chance book's "
        "pessimistic stop) is decided by the entry day's own travel and is OUTCOME-SIDE: it shows what "
        "the invalidation was worth, it is not a filter a trader at the break could apply.",
        "",
    ]
    return lines


def _mean(s: pd.Series) -> float:
    s = s.dropna().astype(float)
    return float(s.mean()) if len(s) else math.nan


def _ci(s: pd.Series) -> dict:
    s = s.dropna().astype(float)
    n = int(len(s))
    if n < 2:
        return {"n": n, "avg": _mean(s), "lo": math.nan, "hi": math.nan}
    m, h = float(s.mean()), 1.96 * float(s.std(ddof=1)) / math.sqrt(n)
    return {"n": n, "avg": m, "lo": m - h, "hi": m + h}


def candidates(df: pd.DataFrame) -> dict:
    """Amendment A2: the five candidates beside the headline, plain daily, the book cohort."""
    base = df[(df["tf"] == "D") & (df["cls"] == "plain") & (df["status"] != "censored")]
    out: dict = {}
    for kind in KINDS:
        rows = base[(base["kind"] == kind) & base["t1"].notna() & base["ret_ref"].notna()]
        if rows.empty:
            continue
        c: dict = {"n": int(len(rows))}
        # A2.1 the week's side at entry
        c["week"] = {}
        for val in ("with", "against"):
            part = rows[rows["w_support"] == val]
            c["week"][val] = {
                "n": int(len(part)),
                "reach1": share(part["reached1"]),
                **{b: _ci(part[BOOK_RET[b]]) for b in BOOKS},
            }
        # A2.3 half at T1
        e = (
            rows["ret_C"]
            .astype(float)
            .where(
                ~rows["hit_A"].fillna(False).astype(bool),
                (rows["ret_A"].astype(float) + rows["ret_C"].astype(float)) / 2.0,
            )
        )
        c["half"] = {
            "E": _ci(e),
            "A": _ci(rows["ret_A"]),
            "C": _ci(rows["ret_C"]),
            "E_minus_A": paired(e, rows["ret_A"]),
            "E_minus_C": paired(e, rows["ret_C"]),
        }
        # A2.4 fees: two fills at the dex's taker rate
        fee = rows["dex"].map(TAKER).astype(float) * 2.0
        c["fees"] = {"rt_avg": _mean(fee), "books": {}}
        for b in BOOKS:
            g = rows[BOOK_RET[b]].astype(float)
            c["fees"]["books"][b] = {"gross": _ci(g), "net": _ci(g - fee)}
        c["fees"]["books"]["E"] = {"gross": _ci(e), "net": _ci(e - fee)}
        # A2.5 under water
        ru = rows[rows["status_u"].isin(["exit", "open"])]
        c["under"] = {
            "n": int(len(ru)),
            "C": paired(ru["ret_C_u"], ru["ret_C"]),
            "A": paired(ru["ret_A_u"], ru["ret_A"]),
            "D": paired(ru["ret_D_u"], ru["ret_D"]),
            "C_u": _ci(ru["ret_C_u"]),
            "A_u": _ci(ru["ret_A_u"]),
            "D_u": _ci(ru["ret_D_u"]),
            "C_d": _ci(ru["ret_C"]),
            "A_d": _ci(ru["ret_A"]),
            "D_d": _ci(ru["ret_D"]),
            "reach1_u": share(ru["hit_A_u"]),
            "reach1_d": share(ru["reached1"]),
            "med_days_u": float(ru["days_u"].median()) if len(ru) else math.nan,
            "med_days_d": float(ru["days"].median()) if len(ru) else math.nan,
            "tail_u": share((ru["mae_u"].astype(float) / ru["r_pct"].astype(float)) > 1.0),
            "tail_d": share((ru["mae_x"].astype(float) / ru["r_pct"].astype(float)) > 1.0),
        }
        # A2.2 the hourly clock, on the rows that have it
        if "status_h" in rows.columns:
            rh = rows[rows["status_h"].isin(["exit", "open"])]
        else:
            rh = rows.iloc[0:0]
        losers_h = rh[rh["ret_C_h"].astype(float) < 0] if len(rh) else rh
        losers_d = rh[rh["ret_C"].astype(float) < 0] if len(rh) else rh
        c["hourly"] = {
            "n": int(len(rh)),
            "C": paired(rh["ret_C_h"], rh["ret_C"])
            if len(rh)
            else paired(pd.Series(dtype=float), pd.Series(dtype=float)),
            "A": paired(rh["ret_A_h"], rh["ret_A"])
            if len(rh)
            else paired(pd.Series(dtype=float), pd.Series(dtype=float)),
            "D": paired(rh["ret_D_h"], rh["ret_D"])
            if len(rh)
            else paired(pd.Series(dtype=float), pd.Series(dtype=float)),
            "C_h": _ci(rh["ret_C_h"]) if len(rh) else {"n": 0},
            "A_h": _ci(rh["ret_A_h"]) if len(rh) else {"n": 0},
            "D_h": _ci(rh["ret_D_h"]) if len(rh) else {"n": 0},
            "C_d": _ci(rh["ret_C"]) if len(rh) else {"n": 0},
            "A_d": _ci(rh["ret_A"]) if len(rh) else {"n": 0},
            "D_d": _ci(rh["ret_D"]) if len(rh) else {"n": 0},
            "reach1_h": share(rh["hit_A_h"]) if len(rh) else share(pd.Series(dtype=object)),
            "reach1_d": share(rh["reached1"]) if len(rh) else share(pd.Series(dtype=object)),
            "med_hours_h": float(rh["hours_h"].median()) if len(rh) else math.nan,
            "med_hours_d": float(rh["days"].median() * 24) if len(rh) else math.nan,
            "exit_share_h": share(rh["status_h"] == "exit")
            if len(rh)
            else share(pd.Series(dtype=object)),
            "loser_avg_h": _mean(losers_h["ret_C_h"]) if len(rh) else math.nan,
            "loser_avg_d": _mean(losers_d["ret_C"]) if len(rh) else math.nan,
            "loser_share_h": float((rh["ret_C_h"].astype(float) < 0).mean())
            if len(rh)
            else math.nan,
            "loser_share_d": float((rh["ret_C"].astype(float) < 0).mean()) if len(rh) else math.nan,
        }
        out[kind] = c
    return out


def _ci_s(x: dict) -> str:
    if not x or not x.get("n"):
        return "-"
    return f"{_f(x['avg'])} [{_f(x['lo'])}, {_f(x['hi'])}]"


def _pr(x: dict) -> str:
    if not x or not x.get("n") or x["n"] < 2:
        return "-"
    return f"{_f(x['diff'])} [{_f(x['lo'])}, {_f(x['hi'])}]"


def table_candidates(cands: dict) -> list[str]:
    lines = [
        "### Amendment A2: the lead's five candidates, plain daily, the book cohort (declared variants, one change each)",
        "",
        "#### " + CAND_LABEL["week"],
        "",
        "| setup | side | n | T1 before the exit | A avg % | C avg % | D avg % | D5 avg % | reference avg % |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for kind, c in cands.items():
        for val in ("with", "against"):
            w = c["week"][val]
            lines.append(
                f"| {kind} | {val} | {w['n']:,} | {_sh(w['reach1'])} | {_ci_s(w['A'])} | {_ci_s(w['C'])} | "
                f"{_ci_s(w['D'])} | {_ci_s(w['D5'])} | {_ci_s(w['ref'])} |"
            )
    lines += ["", "#### " + CAND_LABEL["hourly"], ""]
    lines.append(
        "| setup | n (hourly window) | exit fired | T1 before exit: hourly / daily | median hours held: hourly / daily | "
        "C hourly | C daily | C_h - C | A hourly | A daily | A_h - A | D hourly | D daily | D_h - D | losing trade avg: hourly / daily | losers: hourly / daily |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for kind, c in cands.items():
        h = c["hourly"]
        if not h["n"]:
            lines.append(f"| {kind} | 0 | | | | | | | | | | | | | | |")
            continue
        lines.append(
            f"| {kind} | {h['n']:,} | {_sh(h['exit_share_h'])} | {_sh(h['reach1_h'])} / {_sh(h['reach1_d'])} | "
            f"{h['med_hours_h']:.0f} / {h['med_hours_d']:.0f} | {_ci_s(h['C_h'])} | {_ci_s(h['C_d'])} | {_pr(h['C'])} | "
            f"{_ci_s(h['A_h'])} | {_ci_s(h['A_d'])} | {_pr(h['A'])} | {_ci_s(h['D_h'])} | {_ci_s(h['D_d'])} | {_pr(h['D'])} | "
            f"{_f(h['loser_avg_h'])} / {_f(h['loser_avg_d'])} | {h['loser_share_h'] * 100:.1f}% / {h['loser_share_d'] * 100:.1f}% |"
        )
    lines += ["", "#### " + CAND_LABEL["half"], ""]
    lines.append("| setup | n | A avg % | E avg % | C avg % | E - A | E - C |")
    lines.append("|---|---|---|---|---|---|---|")
    for kind, c in cands.items():
        hf = c["half"]
        lines.append(
            f"| {kind} | {c['n']:,} | {_ci_s(hf['A'])} | {_ci_s(hf['E'])} | {_ci_s(hf['C'])} | "
            f"{_pr(hf['E_minus_A'])} | {_pr(hf['E_minus_C'])} |"
        )
    lines += ["", "#### " + CAND_LABEL["fees"], ""]
    lines.append(
        "| setup | n | round trip avg % | "
        + " | ".join(f"{b} gross / net" for b in (*BOOKS, "E"))
        + " |"
    )
    lines.append("|---|---|---|" + "---|" * (len(BOOKS) + 1))
    for kind, c in cands.items():
        f = c["fees"]
        cells = []
        for b in (*BOOKS, "E"):
            g, n = f["books"][b]["gross"], f["books"][b]["net"]
            cells.append(f"{_f(g['avg'])} / {_f(n['avg'])} [{_f(n['lo'])}, {_f(n['hi'])}]")
        lines.append(f"| {kind} | {c['n']:,} | {f['rt_avg']:.4f} | " + " | ".join(cells) + " |")
    lines += ["", "#### " + CAND_LABEL["under"], ""]
    lines.append(
        "| setup | n | T1 before exit: under / colour | median days: under / colour | past one R against: under / colour | "
        "C under | C colour | C_u - C | A under | A colour | A_u - A | D under | D colour | D_u - D |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for kind, c in cands.items():
        u = c["under"]
        lines.append(
            f"| {kind} | {u['n']:,} | {_sh(u['reach1_u'])} / {_sh(u['reach1_d'])} | {u['med_days_u']:.0f} / {u['med_days_d']:.0f} | "
            f"{_sh(u['tail_u'])} / {_sh(u['tail_d'])} | {_ci_s(u['C_u'])} | {_ci_s(u['C_d'])} | {_pr(u['C'])} | "
            f"{_ci_s(u['A_u'])} | {_ci_s(u['A_d'])} | {_pr(u['A'])} | {_ci_s(u['D_u'])} | {_ci_s(u['D_d'])} | {_pr(u['D'])} |"
        )
    lines += [
        "",
        "Each candidate is one change to the headline on the same rows (prereg amendment A2); the paired "
        "differences are mean and normal 95% interval of the per-trade difference. The hourly arm is the "
        "subset of rows inside the venue's hourly window (about 208 days) whose entry day had an hour that "
        "reached the level; its targets fill only from the entry hour on, so it differs from the daily "
        "books by the clock AND by that ordering. Fees: two fills at the dex's taker rate (main 0.0432%, "
        "xyz 0.0125%, TVB-2 by the venue's own flag); the stop-swap difference is fee-neutral.",
        "",
    ]
    return lines


# ----------------------------------------------------------------------------- main


def compute(df: pd.DataFrame) -> tuple[dict, dict]:
    cells: dict = {}
    clocks: dict = {}
    for tf in PATTERN_TFS:
        levels = ("all", "third", "strict") if tf == "D" else ("all", "third")
        for kind, level, cls, part in iter_cells(df, tf, levels):
            cells[(tf, kind, level, cls)] = cell(part)
            if tf != "D":
                k = cell_clocks(part)
                if k:
                    clocks[(tf, kind, level, cls)] = k
        if tf == "W":
            for kind in KINDS:
                for cls in ("rest", "stacked"):
                    part = select(df, tf, kind, "all", cls)
                    if not part.empty:
                        cells[(tf, kind, "all", cls)] = cell(part)
    return cells, clocks


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="TVB-37 product 3: the STRAT-management book")
    ap.add_argument(
        "--as-of",
        help="YYYY-MM-DD: rerun OFFLINE on the cached candle snapshot of that date (no venue call); "
        "default = today with the live universe and a fresh fetch",
    )
    args = ap.parse_args(argv)
    RESULTS.mkdir(parents=True, exist_ok=True)
    if args.as_of:
        as_of = parse_as_of(args.as_of)
        uni = cached_universe(as_of)
        print(f"universe: {len(uni)} cached perps (offline, as of {args.as_of})", flush=True)
    else:
        as_of = day_start(int(time.time() * 1000))
        uni = universe()
        print(f"universe: {len(uni)} live perps", flush=True)
    rows: list[dict] = []
    counts: Counter = Counter()
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
        try:
            raw_h = (
                cached_hourly(u["coin"], as_of) if args.as_of else fetch_hourly(u["coin"], as_of)
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  hourly fetch failed for {u['coin']}: {exc}", flush=True)
            raw_h = []
        hourly = normalize_hourly(raw_h, as_of)
        r, c = coin_manage_rows(meta, venue_era(daily), hourly)
        rows += r
        counts.update(c)
        if n % 50 == 0:
            print(f"  {n}/{len(uni)} coins, {len(rows):,} units", flush=True)
    df = pd.DataFrame(rows)
    cells, clocks = compute(df)
    cands = candidates(df)
    stamp = datetime.fromtimestamp(as_of / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    md = [
        f"# The STRAT-management book, as of {stamp} UTC (generated by analysis/domino/manage.py; venue era)",
        "",
        f"{df['coin'].nunique()} coins, {len(df):,} units ("
        + ", ".join(f"{tf} {int((df.tf == tf).sum()):,}" for tf in PATTERN_TFS)
        + f"). Headline: daily clock, cap {CAP} daily bars. Drops and anchors: "
        + ", ".join(f"{k} {v:,}" for k, v in sorted(counts.items()))
        + ".",
        "",
    ]
    for tf, name in (("D", "daily"), ("W", "weekly"), ("M", "monthly")):
        md += table_reach(df, tf, f"Reach rates, {name} units", cells)
        md += table_deaths(df, tf, f"How the pre-T1 exits died, {name} units", cells)
        md += table_tail(df, tf, f"The tail, {name} units", cells)
        md += table_books(df, tf, f"The books, {name} units", cells)
    md += table_books(
        df, "D", "The books, daily units, hammer / shooter flag", cells, levels=("third", "strict")
    )
    md += table_mm(df, "D", "Fork 1: the measured move beside the level, daily units", cells)
    md += table_mm(df, "W", "Fork 1: the measured move beside the level, weekly units", cells)
    md += table_clocks(df, "W", "Fork 2: the exit clock, weekly units", clocks)
    md += table_clocks(df, "M", "Fork 2: the exit clock, monthly units", clocks)
    md += table_hypotheses(cells)
    md += table_splits(df, "D")
    md += table_candidates(cands)
    (RESULTS / "manage_tables.md").write_text("\n".join(md), encoding="utf-8")
    out_cells = []
    curves = {}
    for (tf, kind, level, cls), c in cells.items():
        c2 = dict(c)
        if "books" in c2:
            c2["books"] = {
                b: {k: v for k, v in s.items() if k != "curve"} for b, s in c2["books"].items()
            }
            c2["book_C_all"] = {k: v for k, v in c2["book_C_all"].items() if k != "curve"}
            if "mm" in c2:
                c2["mm"] = {
                    k: (
                        {kk: vv for kk, vv in v.items() if kk != "curve"}
                        if isinstance(v, dict)
                        else v
                    )
                    for k, v in c2["mm"].items()
                }
        c2.update({"tf": tf, "kind": kind, "flag": level, "cls": cls})
        if (tf, kind, level, cls) in clocks:
            k = clocks[(tf, kind, level, cls)]
            c2["clocks"] = {
                ck: (
                    {
                        kk: (
                            {a: b for a, b in vv.items() if a != "curve"}
                            if isinstance(vv, dict)
                            else vv
                        )
                        for kk, vv in v.items()
                    }
                    if isinstance(v, dict)
                    else v
                )
                for ck, v in k.items()
            }
        out_cells.append(c2)
        if (tf, kind, level, cls) in CURVES and c.get("books"):
            curves["|".join((tf, kind, level, cls))] = {
                b: _curve_points(c["books"][b]["curve"]) for b in BOOKS if c["books"][b].get("n")
            }
    out = {
        "as_of_utc": stamp,
        "definitions": "docs/experiments/tvb37_management_book_prereg.md",
        "cap_daily_bars": CAP,
        "cap_own_bars": CAP_OWN,
        "unit_usd": UNIT_USD,
        "units": {tf: int((df.tf == tf).sum()) for tf in PATTERN_TFS},
        "counts": dict(counts),
        "excluded": excluded,
        "book_label": BOOK_LABEL,
        "cells": strict_json(out_cells),
        "curves": strict_json(curves),
        "taker_pct": TAKER,
        "candidate_label": CAND_LABEL,
        "candidates": strict_json(cands),
    }
    with open(RESULTS / "manage.json", "w") as fh:
        json.dump(out, fh, indent=1, allow_nan=False)
    keep = [
        c
        for c in df.columns
        if c not in ("v_r_pct", "vout1", "vout3", "vout5", "cls_la", "ret3", "rr3", "rr5")
    ]
    with gzip.open(RESULTS / "manage_trades.csv.gz", "wt", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keep, extrasaction="ignore")
        w.writeheader()
        for r in df[keep].to_dict("records"):
            w.writerow(r)
    print(f"wrote manage_tables.md, manage.json, manage_trades.csv.gz ({len(df):,} units)")


if __name__ == "__main__":
    sys.exit(main())
