"""Trade viewer for the domino books: a local candle page with recorded trades drawn on it.

The page reads RUNS in the viewer contract (`viewer/CONTRACT.md`): `viewer/data/runs.json` lists
them and `viewer/data/runs/<id>/` holds one file per instrument (the bars the engine saw and one
card per trade) beside the importer's derived `index.json`, `dates.json` and `universe.json`. The
page re-runs no trade logic: every level, target, touch time and fill is the card the run wrote,
so a chart that disagrees with a card is evidence against the engine, never against the chart.

    uv run python -m analysis.domino.trade_viewer export-run --as-of 2026-10-10      # the management book as run one (~3 min)
    uv run python -m analysis.domino.trade_viewer import <folder | run.json | zip>   # a run made anywhere, in the contract
    uv run python -m analysis.domino.trade_viewer validate <folder | run.json | zip> # plain-words check; imports nothing
    uv run python -m analysis.domino.trade_viewer hourly --as-of 2026-10-10 BTC ETH   # cache the venue's 1h candles (or: all)
    uv run python -m analysis.domino.trade_viewer serve [--port 8765] [--host 0.0.0.0] [--no-open]

`export-run` writes the management book (`results/manage_trades.csv.gz` with the census's cached
candles) as a run folder and imports it. `import` validates a run (a folder, a single JSON file,
or a zip of either) and lays it out under `viewer/data/runs/<id>/`; `validate` only says what is
wrong. `hourly` fetches the venue's 1h candles (at most the most recent 5000, about 208 days) into
the census cache, stamped with the as-of day, so a later `export-run` ships them. `serve` hosts
`viewer/` on localhost (the page fetches JSON, which file:// forbids) and opens the browser.
Weekly and monthly candles are aggregated in the page from the daily bars with the census's
calendar rules (Monday 00:00 UTC weeks, calendar months). The chart library (amCharts 5, free
tier, logo kept) is vendored into `viewer/vendor/amcharts5/` on the first `serve`. The page is
the TVB-40 amCharts viewer (core.js / story.js / stats.js / app.js; `viewer/NOTES.md` is its
receipt). The flat `viewer/data/*.json` layout with its `build` and `check-run` commands was
retired in stage 3 of the contract (2026-11-01); the files it wrote are no longer read.
"""

from __future__ import annotations

import argparse
import http.server
import json
import os
import sys
import time
import urllib.request
import webbrowser
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
# amCharts 5 (free tier, logo kept): the CDN serves the current 5.x at these paths (5.21.1 when
# the viewer was built, 5.21.2 when promoted); the four files the page loads, vendored once so
# the page works offline
AM5_BASE = "https://cdn.amcharts.com/lib/5/"
AM5_FILES = ("index.js", "xy.js", "stock.js", "themes/Dark.js")
AM5_DIR = VENDOR / "amcharts5"


def stamp_of(as_of_ms: int) -> str:
    return datetime.fromtimestamp(as_of_ms / 1000, tz=timezone.utc).strftime("%Y%m%d")


def cache_path(coin: str, interval: str, as_of_ms: int) -> Path:
    return CACHE / f"{coin.replace(':', '_')}_{interval}_{stamp_of(as_of_ms)}.json"


def compact(bars: list[dict]) -> list[list[float]]:
    return [[b["t"] // 1000, b["o"], b["h"], b["l"], b["c"], b["v"]] for b in bars]


def ensure_vendor() -> None:
    """The chart library, vendored once so the page works offline (amCharts 5, free tier)."""
    for name in AM5_FILES:
        dest = AM5_DIR / name
        if dest.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        url = AM5_BASE + name
        print(f"fetching {url}")
        # the CDN answers 403 to urllib's default agent string; any browser-like agent is served
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (trade_viewer build)"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (fixed https URL)
            dest.write_bytes(resp.read())


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
    print(
        f"hourly fetch done in {time.time() - t0:.0f}s; run `export-run` again to ship them in run one"
    )


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):  # noqa: D102
        pass


def serve(port: int, host: str = "127.0.0.1", open_browser: bool = True) -> None:
    """Host viewer/ over plain HTTP. `host` 127.0.0.1 = this machine only (the default); a
    Tailscale address or 0.0.0.0 lets a laptop on the tailnet browse it; an SSH tunnel
    (`ssh -L 8765:127.0.0.1:8765 ...`) needs no host change. `open_browser` False for SSH
    shells, where opening a browser on the desktop is noise."""
    if not (DATA / "runs.json").exists():
        sys.exit(
            "no runs: import one first (`trade_viewer export-run --as-of YYYY-MM-DD` for the "
            "management book, or `trade_viewer import <folder | run.json | zip>`)"
        )
    ensure_vendor()
    handler = partial(_Quiet, directory=str(VIEWER))
    httpd = http.server.ThreadingHTTPServer((host, port), handler)
    shown = "127.0.0.1" if host in ("0.0.0.0", "") else host
    url = f"http://{shown}:{port}/"
    print(f"trade viewer at {url} (Ctrl+C stops it)")
    if open_browser:
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
    h = sub.add_parser("hourly", help="fetch and cache hourly candles for coins (or 'all')")
    h.add_argument("--as-of", required=True)
    h.add_argument("coins", nargs="+")
    e = sub.add_parser(
        "export-run",
        help="the management book as a run in the contract (viewer/CONTRACT.md), imported under viewer/data/runs/<id>",
    )
    e.add_argument("--as-of", required=True)
    e.add_argument("--id", default=None, help="run id (default management-book-<stamp>)")
    im = sub.add_parser(
        "import",
        help="validate a run (folder, run.json or zip) and lay it out under viewer/data/runs/<id>",
    )
    im.add_argument("path")
    im.add_argument("--id", default=None, help="import under this run id")
    im.add_argument(
        "--bars-from-cache",
        metavar="AS_OF",
        default=None,
        help="fill missing bars for Hyperliquid coins from the census cache stamped AS_OF",
    )
    va = sub.add_parser(
        "validate", help="say in plain words whether a run fits the contract; imports nothing"
    )
    va.add_argument("path")
    s = sub.add_parser("serve", help="host viewer/ on localhost and open the browser")
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--host", default="127.0.0.1", help="bind address (0.0.0.0 = every interface)")
    s.add_argument("--no-open", action="store_true", help="do not open a browser (SSH shells)")
    args = ap.parse_args(argv)
    if args.cmd == "export-run":
        from analysis.domino import contract
        from analysis.domino.run_export import export_run, run_card

        as_of_ms = parse_as_of(args.as_of)
        run_id = run_card(as_of_ms, args.id)["id"]
        if not contract.valid_id(run_id):
            # checked BEFORE any folder is made: an id like ".." would otherwise name the data
            # folder itself as the export's destination (TVB-42 audit F1)
            sys.exit("run " + contract.ID_RULE)
        folder = export_run(as_of_ms, DATA / "runs" / run_id, args.id)
        try:
            contract.import_run(folder, DATA)
        except contract.ContractError as e:
            sys.exit(
                f"the export does not fit the contract ({len(e.problems)} problems):\n  "
                + "\n  ".join(e.problems[:40])
            )
    elif args.cmd == "import":
        from analysis.domino import contract

        lookup = None
        if args.bars_from_cache:
            as_of_ms = parse_as_of(args.bars_from_cache)

            def lookup(coin: str) -> dict | None:
                dp = cache_path(coin, "1d", as_of_ms)
                if not dp.exists():
                    return None
                hp = cache_path(coin, "1h", as_of_ms)
                return {
                    "1d": compact(normalize(json.load(open(dp)), as_of_ms)),
                    "1h": compact(normalize_hourly(json.load(open(hp)), as_of_ms))
                    if hp.exists()
                    else [],
                }

        try:
            contract.import_run(Path(args.path), DATA, args.id, lookup)
        except contract.ContractError as e:
            sys.exit("the run does not fit the contract:\n  " + "\n  ".join(e.problems))
    elif args.cmd == "validate":
        from analysis.domino import contract

        try:
            problems, _ = contract.check(Path(args.path))
        except contract.ContractError as e:
            sys.exit("\n".join(e.problems))
        if problems:
            sys.exit(1)
    elif args.cmd == "hourly":
        hourly(parse_as_of(args.as_of), args.coins)
    else:
        serve(args.port, args.host, not args.no_open)


if __name__ == "__main__":
    os.chdir(HERE.parent.parent)
    main()
