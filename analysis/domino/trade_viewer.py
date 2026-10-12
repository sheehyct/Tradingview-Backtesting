"""Trade viewer for the domino books: a local candle page with the engine's trades drawn on it.

The viewer draws what the management book RECORDED (`results/manage_trades.csv.gz`) on the
raw candles the census cached (`data/*_1d_<stamp>.json`), so a chart that disagrees with a row
is evidence against the engine, never against the chart. It re-runs no trade logic: the entry
day, the targets, the touch days and the exit day are read off the row as the engine wrote them.

    uv run python -m analysis.domino.trade_viewer build  --as-of 2026-10-10
    uv run python -m analysis.domino.trade_viewer hourly --as-of 2026-10-10 BTC ETH   (or: all)
    uv run python -m analysis.domino.trade_viewer serve  [--port 8765]

`build` writes one compact JSON per coin into `viewer/data/` (gitignored, regenerable): the
closed daily bars exactly as the census normalised them, any cached hourly bars, and that
coin's trade rows. `hourly` fetches the venue's 1h candles (at most the most recent 5000, about
208 days) into the same cache the census uses, stamped with the as-of day, so a later `build`
picks them up. `serve` hosts `viewer/` on localhost (the page fetches JSON, which file:// forbids)
and opens the browser. Weekly and monthly candles are aggregated in the page from the daily
bars with the census's calendar rules (Monday 00:00 UTC weeks, calendar months).
"""

from __future__ import annotations

import argparse
import csv
import gzip
import http.server
import json
import math
import os
import sys
import time
import urllib.request
import webbrowser
from collections import defaultdict
from datetime import datetime, timezone
from functools import partial
from pathlib import Path

from analysis.domino.census import (
    CACHE,
    RESULTS,
    cached_universe,
    fetch_hourly,
    normalize,
    normalize_hourly,
    parse_as_of,
)

HERE = Path(__file__).parent
VIEWER = HERE / "viewer"
DATA = VIEWER / "data"
VENDOR = VIEWER / "vendor"
TRADES = RESULTS / "manage_trades.csv.gz"
LWC_URL = (
    "https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"
)
LWC_FILE = VENDOR / "lightweight-charts.standalone.production.js"

# the trade-row columns the page draws or filters on (everything else stays in the CSV)
NUMERIC = (
    "level",
    "stop",
    "r_pct",
    "t1",
    "t2",
    "t3",
    "mm_t1",
    "ret5",
    "ret_C",
    "ret_A",
    "ret_B",
    "ret_D",
    "ret_D5",
    "days",
    "exit_k",
    "t1_k",
    "t2_k",
    "t3_k",
    "one_r_k",
    "mm1_k",
    "stop_k",
    "ref_k",
    "days_ref",
    "days_A",
    "days_B",
    "days_D",
    "days_D5",
    "mfe_x",
    "mae_x",
    "ret_C_own",
    "days_own",
    "ret_C_long",
    "days_long",
    "exit_k_u",
    "ret_C_u",
    "entry_h",
    "exit_h",
    "ret_C_h",
    "hours_h",
)
TEXT = (
    "date",
    "direction",
    "tf",
    "kind",
    "flag",
    "cls",
    "stack",
    "near_tf",
    "t1_src",
    "t2_src",
    "t3_src",
    "anchor",
    "w_support",
    "status",
    "status5",
    "status_own",
    "status_long",
    "status_u",
    "status_h",
    "out5",
    "next_bar",
    "dex",
)
BOOLS = (
    "liquid",
    "hit_A",
    "hit_B",
    "hit_D",
    "hit_D5",
    "reached1",
    "reached2",
    "reached3",
    "stop_saw",
    "stop0",
)


def _num(v: str) -> float | None:
    if v in ("", "nan", "None"):
        return None
    try:
        f = float(v)
    except ValueError:
        return None
    return None if math.isnan(f) else f


def _bool(v: str) -> bool | None:
    return {"True": True, "False": False}.get(v)


def load_trades() -> dict[str, list[dict]]:
    """The management book's rows, slimmed to what the page uses, grouped by coin."""
    by_coin: dict[str, list[dict]] = defaultdict(list)
    with gzip.open(TRADES, "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            row: dict = {k: r[k] for k in TEXT}
            for k in NUMERIC:
                row[k] = _num(r.get(k, ""))
            for k in BOOLS:
                row[k] = _bool(r.get(k, ""))
            by_coin[r["coin"]].append(row)
    for rows in by_coin.values():
        rows.sort(key=lambda x: (x["date"], x["tf"], x["direction"]))
    return by_coin


def stamp_of(as_of_ms: int) -> str:
    return datetime.fromtimestamp(as_of_ms / 1000, tz=timezone.utc).strftime("%Y%m%d")


def cache_path(coin: str, interval: str, as_of_ms: int) -> Path:
    return CACHE / f"{coin.replace(':', '_')}_{interval}_{stamp_of(as_of_ms)}.json"


def compact(bars: list[dict]) -> list[list[float]]:
    return [[b["t"] // 1000, b["o"], b["h"], b["l"], b["c"], b["v"]] for b in bars]


def ensure_vendor() -> None:
    """The chart library, vendored once so the page works offline (Apache-2.0, TradingView)."""
    if LWC_FILE.exists():
        return
    VENDOR.mkdir(parents=True, exist_ok=True)
    print(f"fetching {LWC_URL}")
    with urllib.request.urlopen(LWC_URL, timeout=60) as resp:  # noqa: S310 (fixed https URL)
        LWC_FILE.write_bytes(resp.read())


def build(as_of_ms: int) -> None:
    ensure_vendor()
    DATA.mkdir(parents=True, exist_ok=True)
    trades = load_trades()
    universe = cached_universe(as_of_ms)
    index = []
    dates: dict[str, list] = defaultdict(list)
    for meta in universe:
        coin = meta["coin"]
        rows = trades.get(coin, [])
        daily = normalize(json.load(open(cache_path(coin, "1d", as_of_ms))), as_of_ms)
        hp = cache_path(coin, "1h", as_of_ms)
        hourly = normalize_hourly(json.load(open(hp)), as_of_ms) if hp.exists() else []
        out = {
            "coin": coin,
            "dex": meta["dex"],
            "as_of": stamp_of(as_of_ms),
            "daily": compact(daily),
            "hourly": compact(hourly),
            "trades": rows,
        }
        fn = coin.replace(":", "_") + ".json"
        with open(DATA / fn, "w") as fh:
            json.dump(out, fh, separators=(",", ":"))
        index.append(
            {
                "coin": coin,
                "file": fn,
                "n": len(rows),
                "hourly": bool(hourly),
                "first": daily[0]["t"] // 1000 if daily else None,
                "last": daily[-1]["t"] // 1000 if daily else None,
            }
        )
        for r in rows:
            dates[r["date"]].append(
                [coin, r["direction"], r["tf"], r["kind"], r["ret_C"], r["status"]]
            )
    with open(DATA / "index.json", "w") as fh:
        json.dump(
            {
                "as_of": stamp_of(as_of_ms),
                "built": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                "coins": index,
                "trades": sum(c["n"] for c in index),
            },
            fh,
            separators=(",", ":"),
        )
    with open(DATA / "dates.json", "w") as fh:
        json.dump(dates, fh, separators=(",", ":"))
    n_h = sum(1 for c in index if c["hourly"])
    print(
        f"viewer built: {len(index)} coins, {sum(c['n'] for c in index)} trades, "
        f"{n_h} coins with hourly bars -> {DATA}"
    )


def hourly(as_of_ms: int, coins: list[str]) -> None:
    universe = cached_universe(as_of_ms)
    names = [m["coin"] for m in universe]
    if coins == ["all"]:
        todo = names
    else:
        missing = [c for c in coins if c not in names]
        if missing:
            sys.exit(f"not in the cached universe: {missing}")
        todo = coins
    t0 = time.time()
    for k, coin in enumerate(todo, 1):
        cached = cache_path(coin, "1h", as_of_ms).exists()
        rows = fetch_hourly(coin, as_of_ms)
        print(f"[{k}/{len(todo)}] {coin}: {len(rows)} hourly bars{' (cached)' if cached else ''}")
    print(f"hourly fetch done in {time.time() - t0:.0f}s; run `build` to refresh the viewer data")


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):  # noqa: D102
        pass


def serve(port: int) -> None:
    if not (DATA / "index.json").exists():
        sys.exit("no viewer data: run `build --as-of YYYY-MM-DD` first")
    ensure_vendor()
    handler = partial(_Quiet, directory=str(VIEWER))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    url = f"http://127.0.0.1:{port}/"
    print(f"trade viewer at {url} (Ctrl+C stops it)")
    webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="write viewer/data from the trade CSV and the candle cache")
    b.add_argument("--as-of", required=True, help="the run's as-of day, YYYY-MM-DD")
    h = sub.add_parser("hourly", help="fetch and cache hourly candles for coins (or 'all')")
    h.add_argument("--as-of", required=True)
    h.add_argument("coins", nargs="+")
    s = sub.add_parser("serve", help="host viewer/ on localhost and open the browser")
    s.add_argument("--port", type=int, default=8765)
    args = ap.parse_args(argv)
    if args.cmd == "build":
        build(parse_as_of(args.as_of))
    elif args.cmd == "hourly":
        hourly(parse_as_of(args.as_of), args.coins)
    else:
        serve(args.port)


if __name__ == "__main__":
    os.chdir(HERE.parent.parent)
    main()
