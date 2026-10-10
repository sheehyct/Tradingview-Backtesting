"""TVB-37 daily / weekly / monthly domino census -- CHARACTERIZATION COUNT, NO P&L.

Pre-registration: docs/experiments/tvb37_domino_census_prereg.md (definitions fixed 2026-10-10,
BEFORE this file existed; owner approval of the definitions card 2026-10-09). The short form:

  universe   every live perp on the main dex and the xyz dex; ALL and LIQUID (median daily notional
             over the last 30 closed days >= 1M USD) reported separately
  bars       day = the venue's 1d candle (00:00 UTC); week (Monday 00:00 UTC), month (1st) and
             quarter (Jan/Apr/Jul/Oct 1st) are built from the daily candles on the CALENDAR; a
             partial first bucket is dropped; the forming day is excluded
  levels     the previous COMPLETE bar's high and low on each timeframe (the day's = yesterday's)
  break      strict (equality never breaks); first break of the current higher-timeframe bar only
  event      one coin, one day, one direction; S = timeframes whose level that day broke first;
             rank = |S|; rank 2+ = the domino candidate set
  distance   largest pairwise gap between the broken levels, percent of the lowest; bands EXACT /
             NEAR (<= 0.25%) / WITHIN 1% / SPREAD
  setup kind per timeframe in S, from the previous bar vs its own predecessor: reversal /
             continuation / inside break / outside break
  hammer     THIRD = open and close in the far third of the setup bar's own range on the break's
             side; STRICT = THIRD and the wick beyond the body on that side <= 10% of the range
  quarter    state at the break: unknown / breaks_today / broken_out_before / inside_with /
             inside_against / opposite / both
  support    week and month outside S: colour of the broken level vs that bar's open, and whether
             that bar had already broken the same way
  checks     every W / M / Q first break must also be a daily break that day (bug test)

Everything here is counting. No entry, stop, target, outcome or P&L exists in this module.
"""

from __future__ import annotations

import csv
import gzip
import json
import statistics
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).parent
CACHE = HERE / "data"
RESULTS = HERE / "results"
INFO = "https://api.hyperliquid.xyz/info"
DAY = 86_400_000
TFS = ("D", "W", "M", "Q")
NEAR_BAND = Decimal("0.0025")  # the dashboard's domino band (fraction of the lowest level)
WITHIN_BAND = Decimal("0.01")
SLIVER = Decimal("0.10")  # TA-Lib's "very short shadow" figure, measured on the bar's OWN range
LIQUID_USD = 1_000_000.0
LIQUID_DAYS = 30
MAX_CANDLES = 5000


# ----------------------------------------------------------------------------- venue I/O


def post(body: dict, attempts: int = 6) -> object:
    import httpx

    last = None
    for attempt in range(attempts):
        try:
            r = httpx.post(INFO, json=body, timeout=30)
            if r.status_code == 429:
                time.sleep(12 * (attempt + 1))
                continue
            r.raise_for_status()
            time.sleep(0.7)
            return r.json()
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"venue request failed {body.get('type')}: {last}")


def universe() -> list[dict]:
    """Live perps on the main dex and the xyz dex. Names come prefixed ('xyz:SOXL') by the venue."""
    out = []
    for dex in (None, "xyz"):
        body = {"type": "meta"} if dex is None else {"type": "meta", "dex": dex}
        meta = post(body)
        for row in meta["universe"]:
            if row.get("isDelisted"):
                continue
            out.append({"coin": row["name"], "dex": dex or "main"})
    return out


def fetch_daily(coin: str, as_of_ms: int) -> list[dict]:
    """Full available 1d history (the venue serves at most the most recent 5000 candles)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.fromtimestamp(as_of_ms / 1000, tz=timezone.utc).strftime("%Y%m%d")
    p = CACHE / f"{coin.replace(':', '_')}_1d_{stamp}.json"
    if p.exists():
        return json.load(open(p))
    rows = post(
        {
            "type": "candleSnapshot",
            "req": {
                "coin": coin,
                "interval": "1d",
                "startTime": as_of_ms - MAX_CANDLES * DAY,
                "endTime": as_of_ms,
            },
        }
    )
    json.dump(rows, open(p, "w"))
    return rows


# ----------------------------------------------------------------------------- calendar


def day_start(t: int) -> int:
    return t - t % DAY


def week_start(t: int) -> int:
    """Monday 00:00 UTC. The epoch day (1970-01-01) was a Thursday."""
    dse = t // DAY
    wd = (dse + 4) % 7  # 0 = Sunday .. 6 = Saturday
    return (dse - (wd + 6) % 7) * DAY


def month_start(t: int) -> int:
    d = datetime.fromtimestamp(t / 1000, tz=timezone.utc)
    return int(datetime(d.year, d.month, 1, tzinfo=timezone.utc).timestamp() * 1000)


def quarter_start(t: int) -> int:
    d = datetime.fromtimestamp(t / 1000, tz=timezone.utc)
    m = ((d.month - 1) // 3) * 3 + 1
    return int(datetime(d.year, m, 1, tzinfo=timezone.utc).timestamp() * 1000)


def next_start(tf: str, key: int) -> int:
    if tf == "W":
        return key + 7 * DAY
    d = datetime.fromtimestamp(key / 1000, tz=timezone.utc)
    step = 1 if tf == "M" else 3
    m = d.month + step
    y = d.year + (m - 1) // 12
    m = (m - 1) % 12 + 1
    return int(datetime(y, m, 1, tzinfo=timezone.utc).timestamp() * 1000)


START = {"W": week_start, "M": month_start, "Q": quarter_start}


def normalize(rows: list[dict], now_ms: int, stats: dict | None = None) -> list[dict]:
    """Closed daily bars only, ascending, numeric, one bar per calendar day.

    The forming day (its end is in the future) is cut. A timestamp that is not a 00:00 UTC day
    start is dropped, and when the venue returns the same day twice the LAST copy wins; both are
    counted in `stats` so the run can disclose them (audit F1). Gaps are never filled.
    """
    by_t: dict[int, dict] = {}
    dup = unaligned = 0
    for r in rows:
        t = int(r["t"])
        if t + DAY > now_ms:
            continue
        if t % DAY != 0:
            unaligned += 1
            continue
        if t in by_t:
            dup += 1
        by_t[t] = {
            "t": t,
            "o": float(r["o"]),
            "h": float(r["h"]),
            "l": float(r["l"]),
            "c": float(r["c"]),
            "v": float(r.get("v", 0.0)),
        }
    out = [by_t[t] for t in sorted(by_t)]
    if stats is not None:
        stats["duplicates"] = dup
        stats["unaligned"] = unaligned
        stats["gap_days"] = gap_days(out)
    return out


def gap_days(daily: list[dict]) -> int:
    """Calendar days missing between the first and the last closed bar (0 when contiguous)."""
    if len(daily) < 2:
        return 0
    return (daily[-1]["t"] - daily[0]["t"]) // DAY + 1 - len(daily)


def aggregate(daily: list[dict], tf: str) -> list[dict]:
    """Calendar buckets of closed daily bars. A partial first bucket is dropped (the scanner's rule).

    Each bucket: t (start), end (next start), o/h/l/c, days (indices into `daily`), complete
    (every calendar day of the bucket is inside the closed data and no day is missing).
    """
    start = START[tf]
    buckets: list[dict] = []
    for i, d in enumerate(daily):
        k = start(d["t"])
        if not buckets or buckets[-1]["t"] != k:
            buckets.append(
                {
                    "t": k,
                    "end": next_start(tf, k),
                    "o": d["o"],
                    "h": d["h"],
                    "l": d["l"],
                    "c": d["c"],
                    "days": [i],
                }
            )
        else:
            b = buckets[-1]
            b["h"] = max(b["h"], d["h"])
            b["l"] = min(b["l"], d["l"])
            b["c"] = d["c"]
            b["days"].append(i)
    if buckets and daily and daily[0]["t"] > buckets[0]["t"]:
        buckets.pop(0)
    last_end = daily[-1]["t"] + DAY if daily else 0
    for b in buckets:
        have = [daily[i]["t"] for i in b["days"]]
        want = list(range(b["t"], b["end"], DAY))
        # complete = every calendar day of the bucket present exactly once (audit F1: a duplicate
        # masking a missing day used to pass on the count alone)
        b["complete"] = b["end"] <= last_end and have == want
    return buckets


# ----------------------------------------------------------------------------- bar logic


def classify(bar: dict, prev: dict) -> str:
    """Strict-break classifier (ruling R10): equality never breaks."""
    up = bar["h"] > prev["h"]
    dn = bar["l"] < prev["l"]
    if up and dn:
        return "3"
    if up:
        return "2U"
    if dn:
        return "2D"
    return "1"


def setup_kind(prev_type: str | None, direction: str) -> str | None:
    if prev_type is None:
        return None
    if prev_type == "1":
        return "inside"
    if prev_type == "3":
        return "outside"
    with_break = (prev_type == "2U") == (direction == "up")
    return "continuation" if with_break else "reversal"


def nesting_violation(broken: dict[str, float]) -> bool:
    """A week / month / quarter first break on a day that did not break the daily level.

    Impossible on contiguous data (yesterday either sits inside the higher bar, so its high is
    at or under the running high, or it closed the previous bar, so its high is at or under that
    bar's high), so any hit is a bug. Audit F2: the old check only looked at rank 2+ events, so a
    week-only hit was counted as a rank 1 event with no violation.
    """
    return "D" not in broken and any(tf in broken for tf in ("W", "M", "Q"))


def _dec(x: float) -> Decimal:
    """The price as the decimal the venue printed (str(float) is the shortest round-trip form), so
    a wick of exactly 10% or a gap of exactly 0.25% lands ON the boundary (audit F3, F6)."""
    return Decimal(str(x))


def shape_flags(bar: dict, direction: str) -> tuple[bool, bool]:
    """(THIRD, STRICT) for the bar as a hammer (up break) or shooter (down break)."""
    h, lo, o, c = _dec(bar["h"]), _dec(bar["l"]), _dec(bar["o"]), _dec(bar["c"])
    rng = h - lo
    if rng <= 0:
        return False, False
    top = max(o, c)
    bot = min(o, c)
    if direction == "up":
        third = (bot - lo) * 3 >= rng * 2  # body entirely in the top third
        wick = h - top
    else:
        third = (h - top) * 3 >= rng * 2  # body entirely in the bottom third
        wick = bot - lo
    strict = third and wick <= rng * SLIVER
    return third, strict


def distance_band(levels: list[float]) -> tuple[float, str]:
    """Largest gap between the broken levels as a FRACTION of the lowest (0.01 = 1%), and its band.
    Boundaries are inclusive: exactly 0.25% is NEAR, exactly 1% is WITHIN 1%."""
    lo, hi = _dec(min(levels)), _dec(max(levels))
    frac = (hi - lo) / lo if lo > 0 else Decimal(0)
    if frac == 0:
        band = "exact"
    elif frac <= NEAR_BAND:
        band = "near"
    elif frac <= WITHIN_BAND:
        band = "within1"
    else:
        band = "spread"
    return float(frac), band


# ----------------------------------------------------------------------------- per-coin engine


def _context(daily: list[dict], buckets: dict[str, list[dict]]) -> dict[str, dict[int, dict]]:
    """For every timeframe and every day index: the previous complete bar, the current bar's open and
    the running extremes of the current bar BEFORE that day. Missing pieces stay None."""
    ctx: dict[str, dict[int, dict]] = {tf: {} for tf in ("W", "M", "Q")}
    for tf in ("W", "M", "Q"):
        bl = buckets[tf]
        for bi, b in enumerate(bl):
            prev = bl[bi - 1] if bi >= 1 else None
            if prev is not None and not (prev["complete"] and prev["end"] == b["t"]):
                prev = None
            prev2 = bl[bi - 2] if bi >= 2 else None
            if (
                prev is not None
                and prev2 is not None
                and not (prev2["complete"] and prev2["end"] == prev["t"])
            ):
                prev2 = None
            prev_type = classify(prev, prev2) if prev is not None and prev2 is not None else None
            prev3 = bl[bi - 3] if bi >= 3 else None
            if (
                prev2 is not None
                and prev3 is not None
                and not (prev3["complete"] and prev3["end"] == prev2["t"])
            ):
                prev3 = None
            ref_type = classify(prev2, prev3) if prev2 is not None and prev3 is not None else None
            run_h, run_l = None, None
            for di in b["days"]:
                ctx[tf][di] = {
                    "prev": prev,
                    "prev_type": prev_type,
                    "ref_type": ref_type,
                    "open": b["o"],
                    "run_h": run_h,
                    "run_l": run_l,
                    "is_first_day": daily[di]["t"]
                    == b["t"],  # the calendar open, not the first bar seen
                }
                d = daily[di]
                run_h = d["h"] if run_h is None else max(run_h, d["h"])
                run_l = d["l"] if run_l is None else min(run_l, d["l"])
    return ctx


def _quarter_state(tf_ctx: dict | None, in_s: bool, direction: str, day_level: float) -> str:
    if tf_ctx is None or tf_ctx["prev"] is None:
        return "unknown"
    if in_s:
        return "breaks_today"
    qh, ql = tf_ctx["prev"]["h"], tf_ctx["prev"]["l"]
    hi = tf_ctx["run_h"] is not None and tf_ctx["run_h"] > qh
    lo = tf_ctx["run_l"] is not None and tf_ctx["run_l"] < ql
    if hi and lo:
        return "both"
    if direction == "up":
        if hi:
            return "broken_out_before"
        if lo:
            return "opposite"
        return "inside_with" if day_level > tf_ctx["open"] else "inside_against"
    if lo:
        return "broken_out_before"
    if hi:
        return "opposite"
    return "inside_with" if day_level < tf_ctx["open"] else "inside_against"


def analyze_coin(daily: list[dict]) -> dict:
    """Events for one coin from its closed daily bars. Returns aggregates plus rank 2+ rows."""
    buckets = {tf: aggregate(daily, tf) for tf in ("W", "M", "Q")}
    ctx = _context(daily, buckets)
    agg = {
        "days": max(0, len(daily) - 1),
        "rank": Counter(),  # (direction, rank) -> n
        "kind": Counter(),  # (tf, kind) -> n
        "shape": Counter(),  # (tf, kind, flag) -> n, flag in third/strict/any
        "ref": Counter(),  # (tf, ref_type) -> n for reversal setups
        "violations": 0,
        "skipped_no_yesterday": 0,  # days whose previous calendar day is missing (audit F1)
        "break_days": 0,  # distinct days with at least one event, either direction (audit F8)
        "rank2plus_days": 0,  # distinct days with at least one rank 2+ event
        "complete_w": sum(1 for b in buckets["W"] if b["complete"]),
        "complete_m": sum(1 for b in buckets["M"] if b["complete"]),
        "complete_q": sum(1 for b in buckets["Q"] if b["complete"]),
    }
    rows: list[dict] = []
    for i in range(1, len(daily)):
        d = daily[i]
        pd = daily[i - 1]
        if pd["t"] != d["t"] - DAY:
            # no closed bar for yesterday: the day has no daily level, so it carries no event
            # (audit F1: the previous array element used to stand in for yesterday across a gap)
            agg["skipped_no_yesterday"] += 1
            continue
        adj2 = i >= 2 and daily[i - 2]["t"] == pd["t"] - DAY
        adj3 = adj2 and i >= 3 and daily[i - 3]["t"] == daily[i - 2]["t"] - DAY
        pd_type = classify(pd, daily[i - 2]) if adj2 else None
        pd_ref = classify(daily[i - 2], daily[i - 3]) if adj3 else None
        day_hit = day_hit2 = False
        shared = {
            "W": ctx["W"].get(i, {}).get("is_first_day", False),
            "M": ctx["M"].get(i, {}).get("is_first_day", False),
            "Q": ctx["Q"].get(i, {}).get("is_first_day", False),
        }
        for direction in ("up", "down"):
            broken: dict[str, float] = {}
            setups: dict[str, tuple[str | None, dict, str | None]] = {}
            # the day itself
            lvl = pd["h"] if direction == "up" else pd["l"]
            hit = d["h"] > lvl if direction == "up" else d["l"] < lvl
            if hit:
                broken["D"] = lvl
                setups["D"] = (pd_type, pd, pd_ref)
            for tf in ("W", "M", "Q"):
                c = ctx[tf].get(i)
                if c is None or c["prev"] is None:
                    continue
                lvl = c["prev"]["h"] if direction == "up" else c["prev"]["l"]
                if direction == "up":
                    fresh = c["run_h"] is None or c["run_h"] <= lvl
                    hit = fresh and d["h"] > lvl
                else:
                    fresh = c["run_l"] is None or c["run_l"] >= lvl
                    hit = fresh and d["l"] < lvl
                if hit:
                    broken[tf] = lvl
                    setups[tf] = (c["prev_type"], c["prev"], c["ref_type"])
            if not broken:
                continue
            day_hit = True
            rank = len(broken)
            if nesting_violation(broken):
                agg["violations"] += 1
            agg["rank"][(direction, rank)] += 1
            kinds = {}
            for tf, (ptype, sbar, ref) in setups.items():
                kind = setup_kind(ptype, direction)
                kinds[tf] = kind
                # a setup bar with no classifiable predecessor is counted as "unknown" so the
                # setup-kind denominators are disclosed (audit F5); its shape still goes to the
                # all-setup reference counters
                key = kind or "unknown"
                agg["kind"][(tf, key)] += 1
                third, strict = shape_flags(sbar, direction)
                agg["shape"][(tf, key, "any")] += 1
                if third:
                    agg["shape"][(tf, key, "third")] += 1
                if strict:
                    agg["shape"][(tf, key, "strict")] += 1
                if kind == "reversal" and ref is not None:
                    agg["ref"][(tf, ref)] += 1
            if rank < 2:
                continue
            day_hit2 = True
            pct, band = distance_band(list(broken.values()))
            day_level = broken["D"] if "D" in broken else list(broken.values())[0]
            support = {}
            for tf in ("W", "M"):
                if tf in broken:
                    continue
                c = ctx[tf].get(i)
                if c is None or c["prev"] is None:
                    support[tf] = None
                    continue
                if direction == "up":
                    colour_with = day_level > c["open"]
                    broke_before = c["run_h"] is not None and c["run_h"] > c["prev"]["h"]
                else:
                    colour_with = day_level < c["open"]
                    broke_before = c["run_l"] is not None and c["run_l"] < c["prev"]["l"]
                support[tf] = {"colour_with": colour_with, "broke_before": broke_before}
            q_state = _quarter_state(ctx["Q"].get(i), "Q" in broken, direction, day_level)
            flags = {}
            for tf, (ptype, sbar, ref) in setups.items():
                third, strict = shape_flags(sbar, direction)
                flags[tf] = {"third": third, "strict": strict}
            rows.append(
                {
                    "t": d["t"],
                    "date": datetime.fromtimestamp(d["t"] / 1000, tz=timezone.utc).strftime(
                        "%Y-%m-%d"
                    ),
                    "direction": direction,
                    "rank": rank,
                    "tfs": "+".join(tf for tf in TFS if tf in broken),
                    "levels": {tf: broken[tf] for tf in TFS if tf in broken},
                    "gap_pct": 100.0
                    * pct,  # PERCENT of the lowest level (audit F4: was a fraction)
                    "band": band,
                    "kinds": kinds,
                    "flags": flags,
                    "quarter": q_state,
                    "support": support,
                    "shared_open": "+".join(tf for tf in ("W", "M", "Q") if shared[tf]) or "",
                }
            )
        agg["break_days"] += int(day_hit)
        agg["rank2plus_days"] += int(day_hit2)
    return {"agg": agg, "rows": rows}


def liquid(daily: list[dict]) -> bool:
    tail = daily[-LIQUID_DAYS:]
    if len(tail) < LIQUID_DAYS:
        return False
    return statistics.median(d["v"] * d["c"] for d in tail) >= LIQUID_USD


# ----------------------------------------------------------------------------- reporting


def _pct(n: int, d: int) -> str:
    return f"{100.0 * n / d:5.1f}%" if d else "    - "


def summarize(coins: list[dict]) -> dict:
    """coins: [{coin, dex, liquid, days, agg, rows}]. Returns the aggregate tables for a split."""
    rank = Counter()
    comp = Counter()
    band = Counter()
    band_by_rank = Counter()
    kind = Counter()
    shape = Counter()
    ref = Counter()
    quarter = Counter()
    support = Counter()
    shared = Counter()
    rates = []
    days_total = 0
    violations = 0
    skipped = break_days = rank2_days = 0
    for c in coins:
        a = c["agg"]
        days_total += a["days"]
        violations += a["violations"]
        skipped += a.get("skipped_no_yesterday", 0)
        break_days += a.get("break_days", 0)
        rank2_days += a.get("rank2plus_days", 0)
        for k, v in a["rank"].items():
            rank[k] += v
        for k, v in a["kind"].items():
            kind[k] += v
        for k, v in a["shape"].items():
            shape[k] += v
        for k, v in a["ref"].items():
            ref[k] += v
        n2 = 0
        for r in c["rows"]:
            n2 += 1
            comp[(r["direction"], r["tfs"])] += 1
            band[(r["direction"], r["band"])] += 1
            band_by_rank[(r["rank"], r["band"])] += 1
            quarter[(r["direction"], r["quarter"])] += 1
            for tf, s in r["support"].items():
                if s is None:
                    support[(tf, "unknown")] += 1
                else:
                    support[(tf, "colour_with" if s["colour_with"] else "colour_against")] += 1
                    support[(tf, "broke_before" if s["broke_before"] else "not_broken")] += 1
            shared[("shared" if r["shared_open"] else "plain", r["band"])] += 1
            shared[("shared" if r["shared_open"] else "plain", "all")] += 1
        if a["days"] >= 100:
            rates.append(100.0 * n2 / a["days"])

    def ser(cnt: Counter) -> dict:
        return {
            "|".join(str(x) for x in k): v
            for k, v in sorted(cnt.items(), key=lambda kv: str(kv[0]))
        }

    quant = {}
    if rates:
        rs = sorted(rates)
        q = (
            statistics.quantiles(rs, n=4)
            if len(rs) >= 4
            else [rs[0], statistics.median(rs), rs[-1]]
        )
        quant = {
            "coins": len(rs),
            "min": rs[0],
            "q1": q[0],
            "median": q[1],
            "q3": q[2],
            "max": rs[-1],
        }
    return {
        "coins": len(coins),
        "coin_days": days_total,  # eligible comparison days: closed days minus each coin's first
        "skipped_no_yesterday": skipped,
        "break_days": break_days,
        "rank2plus_days": rank2_days,
        "violations": violations,
        "rank": ser(rank),
        "composition": ser(comp),
        "band": ser(band),
        "band_by_rank": ser(band_by_rank),
        "kind": ser(kind),
        "shape": ser(shape),
        "ref_before_reversal_setup": ser(ref),
        "quarter": ser(quarter),
        "support": ser(support),
        "shared_open": ser(shared),
        "rank2plus_per_100_days": quant,
    }


def tables(name: str, s: dict) -> str:
    out = [
        f"## {name}: {s['coins']} coins, {s['coin_days']:,} coin-days, nesting violations {s['violations']}",
        "",
        f"Days with at least one break (either direction): {s.get('break_days', 0):,}; days with a "
        f"rank 2+ break: {s.get('rank2plus_days', 0):,}; days skipped because the previous calendar "
        f"day is missing: {s.get('skipped_no_yesterday', 0):,}. An outside day breaks both ways and "
        "counts as two events, so event counts exceed day counts.",
        "",
    ]
    out.append("### Events by rank and direction")
    out.append("| rank | up | down | share of all events |")
    out.append("|---|---|---|---|")
    tot = sum(s["rank"].values())
    for r in (1, 2, 3, 4):
        up = s["rank"].get(f"up|{r}", 0)
        dn = s["rank"].get(f"down|{r}", 0)
        out.append(f"| {r} | {up:,} | {dn:,} | {_pct(up + dn, tot)} |")
    out.append("")
    out.append("### Rank 2+ composition (which levels broke together)")
    out.append("| timeframes | up | down |")
    out.append("|---|---|---|")
    keys = sorted({k.split("|")[1] for k in s["composition"]}, key=lambda k: (len(k), k))
    for k in keys:
        out.append(
            f"| {k} | {s['composition'].get('up|' + k, 0):,} | {s['composition'].get('down|' + k, 0):,} |"
        )
    out.append("")
    out.append("### Rank 2+ by stack distance (largest gap between the broken levels)")
    out.append("| band | rank 2 | rank 3 | rank 4 | up | down |")
    out.append("|---|---|---|---|---|---|")
    for b, label in (
        ("exact", "EXACT (same price)"),
        ("near", "NEAR (<= 0.25%)"),
        ("within1", "WITHIN 1%"),
        ("spread", "SPREAD (> 1%)"),
    ):
        out.append(
            f"| {label} | {s['band_by_rank'].get(f'2|{b}', 0):,} | {s['band_by_rank'].get(f'3|{b}', 0):,} | "
            f"{s['band_by_rank'].get(f'4|{b}', 0):,} | {s['band'].get(f'up|{b}', 0):,} | {s['band'].get(f'down|{b}', 0):,} |"
        )
    out.append("")
    out.append(
        "### Setup kind per timeframe (the previous bar vs its own predecessor; percentages are of "
        "CLASSIFIED setups, the last column has no classifiable predecessor and sits outside them)"
    )
    out.append(
        "| timeframe | reversal | continuation | inside break | outside break | not classified |"
    )
    out.append("|---|---|---|---|---|---|")
    for tf in TFS:
        n = {
            k: s["kind"].get(f"{tf}|{k}", 0)
            for k in ("reversal", "continuation", "inside", "outside")
        }
        d = sum(n.values())
        unk = s["kind"].get(f"{tf}|unknown", 0)
        out.append(
            f"| {tf} | {n['reversal']:,} ({_pct(n['reversal'], d).strip()}) | {n['continuation']:,} ({_pct(n['continuation'], d).strip()}) | "
            f"{n['inside']:,} ({_pct(n['inside'], d).strip()}) | {n['outside']:,} ({_pct(n['outside'], d).strip()}) | {unk:,} |"
        )
    out.append("")
    out.append("### Hammer / shooter flags on REVERSAL setup bars (the resource's normal hammer)")
    out.append(
        "| timeframe | reversal setups | THIRD (top/bottom third) | STRICT (third + sliver wick) |"
    )
    out.append("|---|---|---|---|")
    for tf in TFS:
        a = s["shape"].get(f"{tf}|reversal|any", 0)
        t3 = s["shape"].get(f"{tf}|reversal|third", 0)
        st = s["shape"].get(f"{tf}|reversal|strict", 0)
        out.append(
            f"| {tf} | {a:,} | {t3:,} ({_pct(t3, a).strip()}) | {st:,} ({_pct(st, a).strip()}) |"
        )
    out.append("")
    out.append("### The bar before a reversal setup bar (recorded only)")
    out.append("| timeframe | 2 against the break | 2 with the break | inside | outside |")
    out.append("|---|---|---|---|---|")
    out.append("| (per direction the labels differ; raw types below) | | | | |")
    for tf in TFS:
        cells = {
            k: s["ref_before_reversal_setup"].get(f"{tf}|{k}", 0) for k in ("2U", "2D", "1", "3")
        }
        out.append(
            f"| {tf} | 2U {cells['2U']:,} | 2D {cells['2D']:,} | 1 {cells['1']:,} | 3 {cells['3']:,} |"
        )
    out.append("")
    out.append("### Quarter state at rank 2+ breaks")
    out.append("| state | up | down |")
    out.append("|---|---|---|")
    for q in (
        "breaks_today",
        "broken_out_before",
        "inside_with",
        "inside_against",
        "opposite",
        "both",
        "unknown",
    ):
        out.append(
            f"| {q} | {s['quarter'].get(f'up|{q}', 0):,} | {s['quarter'].get(f'down|{q}', 0):,} |"
        )
    out.append("")
    out.append(
        "### Week and month outside the stack (rank 2+ events where that timeframe did not break)"
    )
    out.append(
        "| timeframe | level on the break's side of the open | other side | already broken that way | not yet | unknown |"
    )
    out.append("|---|---|---|---|---|---|")
    for tf in ("W", "M"):
        g = lambda k: s["support"].get(f"{tf}|{k}", 0)  # noqa: E731
        out.append(
            f"| {tf} | {g('colour_with'):,} | {g('colour_against'):,} | {g('broke_before'):,} | {g('not_broken'):,} | {g('unknown'):,} |"
        )
    out.append("")
    out.append(
        "### Rank 2+ on shared-open days (a new week, month or quarter opened with the day) vs plain days"
    )
    out.append("| day type | all | exact | near | within 1% | spread |")
    out.append("|---|---|---|---|---|---|")
    for k, label in (("shared", "shared open"), ("plain", "plain day")):
        g = lambda b: s["shared_open"].get(f"{k}|{b}", 0)  # noqa: E731
        out.append(
            f"| {label} | {g('all'):,} | {g('exact'):,} | {g('near'):,} | {g('within1'):,} | {g('spread'):,} |"
        )
    out.append("")
    q = s["rank2plus_per_100_days"]
    if q:
        out.append(
            f"### Rank 2+ events per 100 closed days, per coin (coins with >= 100 days: {q['coins']}): "
            f"min {q['min']:.1f}, lower quartile {q['q1']:.1f}, median {q['median']:.1f}, upper quartile {q['q3']:.1f}, max {q['max']:.1f}"
        )
        out.append("")
    return "\n".join(out)


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
    coins = []
    excluded = []  # audit F9: every coin the census could not use, with the reason
    quality = Counter()
    for n, u in enumerate(uni, 1):
        try:
            raw = fetch_daily(u["coin"], as_of)
        except Exception as exc:  # noqa: BLE001
            print(f"  skip {u['coin']}: {exc}", flush=True)
            excluded.append({"coin": u["coin"], "dex": u["dex"], "reason": f"fetch failed: {exc}"})
            continue
        st: dict = {}
        daily = normalize(raw, as_of, st)
        quality.update(st)
        if len(daily) < 3:
            excluded.append(
                {
                    "coin": u["coin"],
                    "dex": u["dex"],
                    "reason": f"{len(daily)} closed day(s), fewer than the 3 a break needs",
                }
            )
            continue
        res = analyze_coin(daily)
        # venue era: the venue serves ZERO-volume candles from before a coin first traded (BTC
        # back to 2020-08-19 with no trade until 2023-02-26); those days are index prices, not
        # venue bars, so a second pass starts at each coin's first traded day (audit F11)
        first_traded = next((k for k, d in enumerate(daily) if d["v"] > 0), None)
        if first_traded is None:
            venue = None
        elif first_traded == 0:
            venue = res
        else:
            venue = analyze_coin(daily[first_traded:]) if len(daily) - first_traded >= 3 else None
        coins.append(
            {
                "coin": u["coin"],
                "dex": u["dex"],
                "liquid": liquid(daily),
                "days": res["agg"]["days"],
                "duplicates": st["duplicates"],
                "unaligned": st["unaligned"],
                "gap_days": st["gap_days"],
                "first_day": datetime.fromtimestamp(daily[0]["t"] / 1000, tz=timezone.utc).strftime(
                    "%Y-%m-%d"
                ),
                "venue_first_day": (
                    None
                    if first_traded is None
                    else datetime.fromtimestamp(
                        daily[first_traded]["t"] / 1000, tz=timezone.utc
                    ).strftime("%Y-%m-%d")
                ),
                "backfill_days": first_traded or 0,
                "venue": venue,
                "complete_w": res["agg"]["complete_w"],
                "complete_m": res["agg"]["complete_m"],
                "complete_q": res["agg"]["complete_q"],
                "agg": res["agg"],
                "rows": res["rows"],
            }
        )
        if n % 25 == 0:
            print(f"  {n}/{len(uni)} coins", flush=True)
    splits = {
        "ALL": coins,
        "LIQUID": [c for c in coins if c["liquid"]],
        "ALL main dex": [c for c in coins if c["dex"] == "main"],
        "ALL xyz dex": [c for c in coins if c["dex"] == "xyz"],
        "VENUE ERA (from each coin's first traded day)": [
            c["venue"] for c in coins if c["venue"] is not None
        ],
    }
    out = {
        "as_of_utc": datetime.fromtimestamp(as_of / 1000, tz=timezone.utc).strftime("%Y-%m-%d"),
        "definitions": "docs/experiments/tvb37_domino_census_prereg.md",
        "bands": {
            "near": float(NEAR_BAND),
            "within": float(WITHIN_BAND),
            "sliver": float(SLIVER),
            "liquid_usd": LIQUID_USD,
        },
        "excluded": excluded,
        "data_quality": dict(quality),  # duplicates / unaligned timestamps dropped, gap days seen
        "coins": [
            {
                k: c[k]
                for k in (
                    "coin",
                    "dex",
                    "liquid",
                    "days",
                    "duplicates",
                    "unaligned",
                    "gap_days",
                    "first_day",
                    "venue_first_day",
                    "backfill_days",
                    "complete_w",
                    "complete_m",
                    "complete_q",
                )
            }
            | {"rank2plus": len(c["rows"])}
            for c in coins
        ],
        "splits": {name: summarize(cs) for name, cs in splits.items()},
    }
    json.dump(out, open(RESULTS / "census.json", "w"), indent=1)
    with gzip.open(RESULTS / "events_rank2plus.csv.gz", "wt", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "coin",
                "dex",
                "liquid",
                "date",
                "direction",
                "rank",
                "tfs",
                "gap_pct",
                "band",
                "levels",
                "kinds",
                "flags",
                "quarter",
                "support",
                "shared_open",
            ]
        )
        for c in coins:
            for r in c["rows"]:
                w.writerow(
                    [
                        c["coin"],
                        c["dex"],
                        c["liquid"],
                        r["date"],
                        r["direction"],
                        r["rank"],
                        r["tfs"],
                        f"{r['gap_pct']:.6f}",
                        r["band"],
                        json.dumps(r["levels"]),
                        json.dumps(r["kinds"]),
                        json.dumps(r["flags"]),
                        r["quarter"],
                        json.dumps(r["support"]),
                        r["shared_open"],
                    ]
                )
    md = [
        f"# Domino census tables, as of {out['as_of_utc']} UTC (generated by analysis/domino/census.py)",
        "",
    ]
    depth = Counter()
    for c in coins:
        depth["coins"] += 1
        depth["with a complete prior week"] += c["complete_w"] >= 1
        depth["with a complete prior month"] += c["complete_m"] >= 1
        depth["with a complete prior quarter"] += c["complete_q"] >= 1
        depth["liquid"] += c["liquid"]
    md.append("## Depth")
    md.append(
        "| coins | complete prior week | complete prior month | complete prior quarter | liquid |"
    )
    md.append("|---|---|---|---|---|")
    md.append(
        f"| {depth['coins']} | {depth['with a complete prior week']} | {depth['with a complete prior month']} | "
        f"{depth['with a complete prior quarter']} | {depth['liquid']} |"
    )
    md.append("")
    for name, s in out["splits"].items():
        md.append(tables(name, s))
    (RESULTS / "tables.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    sys.exit(main())
