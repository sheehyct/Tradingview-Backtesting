"""TVB-15 HL bar archive: fetch + merge for the frozen week-1 roster.

The HL candleSnapshot floor slides (~5000 candles per interval: ~17 days of
5m, ~208 days of 1h), so each run fetches the full available window and
MERGES into a canonical per-symbol file -- union by bar-open timestamp,
newest fetch wins on overlap. Committed under analysis/paper/bars/ so the
week's replay is reproducible from tracked data. Run cadence <= 3 days
(5m floor); session touchpoints are fine.

    uv run python -m analysis.paper.archive --roster analysis/paper/roster_week1.json

--update-roster-ticks also writes PROVISIONAL minticks into the roster
(smallest power-of-ten step that makes every archived price integral,
mintick_source="hl_inferred"). The TV symbol_info capture supersedes these
(mintick_source="tv_symbolinfo") -- TV is the parity-correct source for the
+/- 1 tick triggers.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from tfc.providers import bars_from_rows, fetch_hl, save_bars

REPO = Path(__file__).resolve().parents[2]
BARS_DIR = REPO / "analysis" / "paper" / "bars"

# fetch spans (days back from now); the server floors to what it has
SPANS_DAYS = {"5m": 21, "1h": 250, "1d": 600}
INTERVALS = ("5m", "1h", "1d")


def bars_path(coin: str, interval: str, bars_dir: Path = BARS_DIR) -> Path:
    return bars_dir / f"{coin.replace(':', '_')}_{interval}.json"


def merge_rows(old_rows: list[list], new_rows: list[list]) -> list[list]:
    """Union by bar-open ts; the NEW fetch wins on overlap (bar revisions)."""
    by_ts = {int(r[0]): list(r) for r in old_rows}
    for r in new_rows:
        by_ts[int(r[0])] = list(r)
    return [by_ts[t] for t in sorted(by_ts)]


def infer_tick(rows: list[list]) -> float:
    """Smallest power-of-ten step that makes every OHLC price integral.
    PROVISIONAL tick source only (see module docstring)."""
    for k in range(0, 7):
        scale = 10**k
        if all(
            abs(p * scale - round(p * scale)) < 1e-6 for r in rows for p in (r[1], r[2], r[3], r[4])
        ):
            return 10.0**-k
    return 10.0**-6


def archive_symbol(coin: str, interval: str, bars_dir: Path = BARS_DIR) -> dict:
    """Fetch the full available window and merge into the canonical file."""
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_ms = now_ms - SPANS_DAYS[interval] * 86400 * 1000
    bars, meta = fetch_hl(coin, interval, start_ms, now_ms)
    path = bars_path(coin, interval, bars_dir)
    new_rows = [
        [int(t), o, h, l, c, v]
        for t, o, h, l, c, v in zip(
            bars.ts, bars.open, bars.high, bars.low, bars.close, bars.volume
        )
    ]
    merged_from = 0
    if path.exists():
        old = json.loads(path.read_text())
        merged_from = old["count"]
        rows = merge_rows(old["bars"], new_rows)
        meta = dict(meta, merged_from_count=merged_from, merges=old["meta"].get("merges", 0) + 1)
        bars = bars_from_rows(rows, symbol=coin, interval=interval)
    save_bars(bars, meta, path)
    return {
        "coin": coin,
        "interval": interval,
        "served": meta["served_count"],
        "total": len(bars),
        "merged_from": merged_from,
        "first": datetime.fromtimestamp(int(bars.ts[0]), tz=timezone.utc).strftime("%m-%d %H:%M"),
        "last": datetime.fromtimestamp(int(bars.ts[-1]), tz=timezone.utc).strftime("%m-%d %H:%M"),
        "floor_hit": meta["floor_hit"],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Archive HL bars for the frozen roster")
    ap.add_argument("--roster", required=True)
    ap.add_argument("--intervals", default=",".join(INTERVALS))
    ap.add_argument("--bars-dir", default=str(BARS_DIR))
    ap.add_argument(
        "--update-roster-ticks",
        action="store_true",
        help="write PROVISIONAL hl_inferred minticks into the roster file",
    )
    args = ap.parse_args()
    roster_path = Path(args.roster)
    roster = json.loads(roster_path.read_text())
    bars_dir = Path(args.bars_dir)
    intervals = args.intervals.split(",")
    for sym in roster["symbols"]:
        coin = sym["name"]
        for interval in intervals:
            r = archive_symbol(coin, interval, bars_dir)
            flag = " FLOOR" if r["floor_hit"] else ""
            print(
                f"{coin:12} {interval:3} served={r['served']:5} total={r['total']:5} "
                f"({r['first']} .. {r['last']}){flag}"
            )
            time.sleep(0.3)
        if args.update_roster_ticks and sym.get("mintick_source") != "tv_symbolinfo":
            rows = json.loads(bars_path(coin, "5m", bars_dir).read_text())["bars"]
            sym["tv_mintick"] = infer_tick(rows)
            sym["mintick_source"] = "hl_inferred"
            print(f"{coin:12} provisional mintick {sym['tv_mintick']} (hl_inferred)")
    if args.update_roster_ticks:
        roster_path.write_text(json.dumps(roster, indent=1) + "\n")
        print(f"roster ticks updated -> {roster_path}")


if __name__ == "__main__":
    main()
