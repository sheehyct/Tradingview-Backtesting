"""TVB-19 RTH-vs-UTC clock census (read-only; no strategy code).

The question (user, seeded 2026-08-04): these are oracle-priced equity perps
living under TWO clocks -- the venue day rolls 00:00 UTC, the underlying's
session opens 9:30 ET. For the SAME symbol and the SAME deployed gate
predicate (strat-methodology 4.1 bias: close vs each timeframe's own period
open, composite = full D/W/M agreement), how often does the signal computed
on venue-clock opens disagree with the signal computed on RTH-anchored
opens, and in which hours do disagreements cluster? If rarely, the anchor
question settles cheaply; if often, full pre-registered backtest arms are
justified. This census DECIDES NOTHING -- it sizes the question.

Clock definitions:
- UTC (deployed): D/W/M keys from analysis.paper.engine (00:00 UTC day,
  Monday 00:00 week, 1st-of-month) -- imported, not reimplemented.
- RTH: day rolls 9:30 America/New_York on NYSE TRADING days (weekends and
  the holiday table skipped; weekend bars belong to Friday's session);
  week = roll of the first trading day of the ISO week; month = roll of
  the first trading day of the calendar month. zoneinfo handles DST.

Period-open sampling (both clocks, the twin's own convention): the open of
the first bar STARTING at/after the roll instant. Opens whose roll predates
the 5m archive seed from the 1h archive; UTC rolls align with 1h bar starts
exactly, RTH rolls land mid-bar, so 1h-seeded RTH opens carry up to a
30-minute sampling delta (declared in the output as seeded_legs).

Scored window: 2026-07-06 -> 2026-08-03 UTC (the Tier A sweep window).
Bars score only once BOTH trackers have all three legs seeded.

Run:
    uv run python -m analysis.clock_census
"""

from __future__ import annotations

import argparse
import json
from bisect import bisect_right
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from analysis.paper.engine import GATE_TFS
from analysis.paper.replay import load_rows

REPO = Path(__file__).resolve().parents[1]
OUT_DEFAULT = REPO / "analysis" / "reference" / "tvb19_clock_census.json"
NY = ZoneInfo("America/New_York")
WINDOW_START = "2026-07-06"
WINDOW_END = "2026-08-03"
CAL_START = date(2025, 12, 1)  # covers the deepest 1h archive (2025-12-24)
CAL_END = date(2026, 8, 31)

# NYSE full-day closures inside [CAL_START, CAL_END] (declared, not derived).
HOLIDAYS = {
    date(2025, 12, 25),
    date(2026, 1, 1),
    date(2026, 1, 19),
    date(2026, 2, 16),
    date(2026, 4, 3),
    date(2026, 5, 25),
    date(2026, 6, 19),
    date(2026, 7, 3),
}


def trading_days(start: date, end: date) -> list[date]:
    out = []
    d = start
    while d <= end:
        if d.weekday() < 5 and d not in HOLIDAYS:
            out.append(d)
        d += timedelta(days=1)
    return out


def rth_rolls() -> dict[str, list[int]]:
    """Roll instants (unix s) per leg: open of each RTH day/week/month."""
    days = trading_days(CAL_START, CAL_END)
    day_rolls = [int(datetime.combine(d, time(9, 30), tzinfo=NY).timestamp()) for d in days]
    week_rolls = []
    month_rolls = []
    seen_wk: set[tuple[int, int]] = set()
    seen_mo: set[tuple[int, int]] = set()
    for d, ts in zip(days, day_rolls):
        wk = d.isocalendar()[:2]
        if wk not in seen_wk:
            seen_wk.add(wk)
            week_rolls.append(ts)
        mo = (d.year, d.month)
        if mo not in seen_mo:
            seen_mo.add(mo)
            month_rolls.append(ts)
    return {"D": day_rolls, "W": week_rolls, "M": month_rolls}


class OpenTracker:
    """Latest period open per leg under one clock, twin sampling convention."""

    def __init__(self, keyers: dict):
        self.keyers = keyers  # leg -> callable(ts) -> period key
        self.key: dict[str, object] = {leg: None for leg in keyers}
        self.open: dict[str, float | None] = {leg: None for leg in keyers}
        self.seeded_from_1h: set[str] = set()

    def feed(self, ts: int, o: float, coarse: bool = False) -> None:
        for leg, kf in self.keyers.items():
            k = kf(ts)
            if k is not None and k != self.key[leg]:
                self.key[leg], self.open[leg] = k, o
                if coarse:
                    self.seeded_from_1h.add(leg)
                else:
                    self.seeded_from_1h.discard(leg)

    def ready(self) -> bool:
        return all(v is not None for v in self.open.values())

    def bias(self, c: float) -> dict[str, int]:
        return {leg: (1 if c > v else -1 if c < v else 0) for leg, v in self.open.items()}

    def composite(self, c: float) -> str:
        if c > max(self.open.values()):
            return "up"
        if c < min(self.open.values()):
            return "down"
        return "neutral"


def make_trackers() -> tuple[OpenTracker, OpenTracker]:
    utc = OpenTracker({name: kf for name, kf in GATE_TFS})
    rolls = rth_rolls()

    def keyer(rl: list[int]):
        def kf(ts: int):
            i = bisect_right(rl, ts) - 1
            return i if i >= 0 else None

        return kf

    rth = OpenTracker({leg: keyer(rl) for leg, rl in rolls.items()})
    return utc, rth


def census_symbol(coin: str, bars_dir: Path, ws: int, we: int) -> dict:
    rows_5m = load_rows(coin, "5m", bars_dir)
    rows_1h = load_rows(coin, "1h", bars_dir)
    utc, rth = make_trackers()
    first_5m = rows_5m[0][0]
    for r in rows_1h:
        if r[0] >= first_5m:
            break
        utc.feed(int(r[0]), r[1], coarse=True)
        rth.feed(int(r[0]), r[1], coarse=True)
    seeded_legs = sorted(rth.seeded_from_1h)
    n = n_dis = 0
    kinds = {"up_vs_neutral": 0, "down_vs_neutral": 0, "up_vs_down": 0}
    leg_dis = {"D": 0, "W": 0, "M": 0}
    hour_hist = [0] * 24
    prev_u = prev_r = None
    flips = {"utc": 0, "rth": 0, "utc_only": 0, "rth_only": 0, "hard_utc": 0, "hard_rth": 0}
    for r in rows_5m:
        ts, o, c = int(r[0]), r[1], r[4]
        utc.feed(ts, o)
        rth.feed(ts, o)
        if not (ws <= ts < we and utc.ready() and rth.ready()):
            continue
        cu, cr = utc.composite(c), rth.composite(c)
        n += 1
        if cu != cr:
            n_dis += 1
            pair = {cu, cr}
            if pair == {"up", "down"}:
                kinds["up_vs_down"] += 1
            elif "up" in pair:
                kinds["up_vs_neutral"] += 1
            else:
                kinds["down_vs_neutral"] += 1
            hour_hist[datetime.fromtimestamp(ts, tz=NY).hour] += 1
        bu, br = utc.bias(c), rth.bias(c)
        for leg in leg_dis:
            if bu[leg] != br[leg]:
                leg_dis[leg] += 1
        fu = prev_u is not None and cu != prev_u
        fr = prev_r is not None and cr != prev_r
        flips["utc"] += fu
        flips["rth"] += fr
        flips["utc_only"] += fu and not fr
        flips["rth_only"] += fr and not fu
        flips["hard_utc"] += fu and "neutral" not in (cu, prev_u)
        flips["hard_rth"] += fr and "neutral" not in (cr, prev_r)
        prev_u, prev_r = cu, cr
    return {
        "symbol": coin,
        "n_bars_scored": n,
        "n_disagree": n_dis,
        "disagree_rate": round(n_dis / n, 4) if n else None,
        "disagree_kinds": kinds,
        "per_leg_bias_disagree_rate": {
            leg: round(v / n, 4) if n else None for leg, v in leg_dis.items()
        },
        "disagree_by_hour_et": hour_hist,
        "flip_events": flips,
        "rth_legs_seeded_from_1h": seeded_legs,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="RTH-vs-UTC gate clock census")
    ap.add_argument("--roster", default=str(REPO / "analysis" / "paper" / "roster_week1.json"))
    ap.add_argument("--bars-dir", default=str(REPO / "analysis" / "paper" / "bars"))
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    args = ap.parse_args()
    roster = json.loads(Path(args.roster).read_text())
    ws = int(datetime.fromisoformat(WINDOW_START).replace(tzinfo=timezone.utc).timestamp())
    we = int(datetime.fromisoformat(WINDOW_END).replace(tzinfo=timezone.utc).timestamp())
    per_symbol = [census_symbol(e["name"], Path(args.bars_dir), ws, we) for e in roster["symbols"]]
    pooled_hist = [sum(s["disagree_by_hour_et"][h] for s in per_symbol) for h in range(24)]
    n = sum(s["n_bars_scored"] for s in per_symbol)
    nd = sum(s["n_disagree"] for s in per_symbol)
    doc = {
        "question": "deployed D/W/M gate composite under venue 00:00-UTC opens vs "
        "RTH-anchored opens (9:30 ET trading-day / first-trading-day week / "
        "first-trading-day month); same predicate, same bars, two clocks",
        "window_utc": [WINDOW_START, WINDOW_END],
        "holidays_declared": sorted(d.isoformat() for d in HOLIDAYS),
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pooled": {
            "n_bars_scored": n,
            "n_disagree": nd,
            "disagree_rate": round(nd / n, 4) if n else None,
            "disagree_by_hour_et": pooled_hist,
        },
        "per_symbol": per_symbol,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(doc, indent=1) + "\n")
    print(f"scored {n} bars, pooled disagree {nd} ({100 * nd / n:.2f}%) -> {args.out}")
    for s in per_symbol:
        top = max(range(24), key=lambda h: s["disagree_by_hour_et"][h])
        print(
            f"  {s['symbol']:12} rate={s['disagree_rate']!s:>7} "
            f"legs D/W/M={[s['per_leg_bias_disagree_rate'][x] for x in ('D', 'W', 'M')]} "
            f"peak ET hour={top:02d}"
        )


if __name__ == "__main__":
    main()
