"""TVB-19 Tier A deliberate-overfit sweep over the existing TwinConfig knobs.

LABEL (binding): DELIBERATE OVERFIT / in-sample ceiling / secondary control.
No deployment claims. Pre-registration: docs/experiments/tvb19_tier_a_prereg.md
(committed 2a78ec2, BEFORE this runner was written). Grid, window, metrics,
and exclusions live there; this module only executes them.

Mechanics are compare_config.py's replay path generalized to the full knob
grid: per symbol, pools warm from pre-window 1h bars (M from 1d), gates seed
from the 1h stream, the arm window seeds from the last arm_tf_s of pre-window
5m bars, then the window's 5m bars replay through the committed v6.1 engine.
Neither engine.py nor any frozen week-1 artifact is touched. Warm-up state
depends only on (12h pool, n_max, min_sep, pool_cap), so cells are grouped by
that warm-key: each task warms its 11 symbols once and deep-copies the pools
into the 16 (arm_tf, brk, flip) replay variants.

Outputs (analysis/paper/sweeps/tvb19_tier_a/): results_by_symbol.jsonl,
results_rollup.jsonl, manifest.json (grid + window + git HEAD + bar hashes +
wall timestamps). Per-cell event logs are deliberately not stored; every cell
reproduces deterministically from this runner + the committed bars.

Estimators: every "med" field is the sample median (statistics.median: mean
of the middle pair on even n); p90 is the nearest-rank observation. Roster
rollups carry the full pre-registered metric set (trade median/win rate and
episode MFE/give-back summaries), computed from the raw per-trade and
per-episode values, not from per-symbol aggregates.

Run:
    uv run python -m analysis.paper.sweep_tier_a          # full 864-cell grid
    uv run python -m analysis.paper.sweep_tier_a --limit-cells 2 --symbols xyz:DRAM
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import statistics
import subprocess
import time
from bisect import bisect_left, bisect_right
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from analysis.giveback import episode_metrics
from analysis.paper.engine import Twin, TwinConfig
from analysis.paper.replay import load_rows

REPO = Path(__file__).resolve().parents[2]
OUT_DIR_DEFAULT = REPO / "analysis" / "paper" / "sweeps" / "tvb19_tier_a"
WINDOW_START = "2026-07-06"
WINDOW_END = "2026-08-03"
PARITY_SYMBOL = "xyz:DRAM"  # excluded from roster rollups (week-1 convention)

# Pre-registered axes (prereg doc, "Grid"). Order fixes cell_id enumeration.
ARM_TF_S = (300, 900, 1800, 3600)
POOL_12H = (True, False)
N_MAX = (3, 6, 9)
MIN_SEP = (0.5, 1.0, 2.0)
POOL_CAP = (6, 12, None)
BRK_EXIT = (True, False)
FLIP_BACKSTOP = (True, False)

WEEK_S = 7 * 86400

_bars_cache: dict[tuple[str, str], list] = {}


def grid() -> list[dict]:
    cells = []
    for i, (arm, p12, nmax, msep, cap, brk, flip) in enumerate(
        itertools.product(ARM_TF_S, POOL_12H, N_MAX, MIN_SEP, POOL_CAP, BRK_EXIT, FLIP_BACKSTOP)
    ):
        cells.append(
            {
                "cell_id": i,
                "tag": (
                    f"arm{arm}_12h{'ON' if p12 else 'OFF'}_n{nmax}_s{msep}"
                    f"_c{cap if cap is not None else 'NONE'}"
                    f"_brk{'ON' if brk else 'OFF'}_flip{'ON' if flip else 'OFF'}"
                ),
                "arm_tf_s": arm,
                "pool_12h": p12,
                "n_max": nmax,
                "min_sep": msep,
                "pool_cap": cap,
                "brk_exit": brk,
                "flip_backstop": flip,
            }
        )
    return cells


def warm_key(cell: dict) -> tuple:
    return (cell["pool_12h"], cell["n_max"], cell["min_sep"], cell["pool_cap"])


def _rows(sym: str, interval: str, bars_dir: str) -> list:
    k = (sym, interval)
    if k not in _bars_cache:
        _bars_cache[k] = load_rows(sym, interval, Path(bars_dir))
    return _bars_cache[k]


def _warm_symbol(entry: dict, wk: tuple, ws: int, bars_dir: str):
    """Warm one symbol's pools + gate opens for a warm-key. Returns reusable state."""
    p12, nmax, msep, cap = wk
    coin = entry["name"]
    rows_1h = _rows(coin, "1h", bars_dir)
    rows_1d = _rows(coin, "1d", bars_dir)
    cfg = TwinConfig(
        symbol=coin, mintick=float(entry["tv_mintick"]), n_max=nmax, min_sep=msep, pool_cap=cap
    )
    twin = Twin(cfg)
    if not p12:
        twin.pools = [p for p in twin.pools if p.name != "12h"]
    pre_1h = [r for r in rows_1h if r[0] < ws]
    for name in ("12h", "D", "W"):
        if any(p.name == name for p in twin.pools):
            twin.warm_pool(name, pre_1h)
    pre_1d = [r for r in rows_1d if r[0] < ws]
    twin.warm_pool("M", pre_1d)
    twin.seed_gates(pre_1h)
    return {
        "pools": twin.pools,
        "gate_open": dict(twin.gate_open),
        "gate_key": dict(twin.gate_key),
        "warmup_1h_bars": len(pre_1h),
        "warmup_1d_bars": len(pre_1d),
    }


def _pct(vals: list[float], q: float):
    """Nearest-rank quantile (single observed element). NOT for medians."""
    if not vals:
        return None
    s = sorted(vals)
    return s[max(0, min(len(s) - 1, int(round(q * (len(s) - 1)))))]


def _med(vals: list[float]):
    """Sample median: mean of the middle pair on even n."""
    return statistics.median(vals) if vals else None


def _replay_cell(entry: dict, cell: dict, warm: dict, ws: int, we: int, bars_dir: str) -> dict:
    """One (cell, symbol) replay. Returns the per-symbol record + curve for rollup."""
    coin = entry["name"]
    rows_5m = _rows(coin, "5m", bars_dir)
    ts_5m = [r[0] for r in rows_5m]
    cfg = TwinConfig(
        symbol=coin,
        mintick=float(entry["tv_mintick"]),
        flip_backstop=cell["flip_backstop"],
        brk_exit=cell["brk_exit"],
        n_max=cell["n_max"],
        min_sep=cell["min_sep"],
        pool_cap=cell["pool_cap"],
        arm_tf_s=cell["arm_tf_s"],
    )
    twin = Twin(cfg)
    twin.pools = deepcopy(warm["pools"])
    twin.gate_open = dict(warm["gate_open"])
    twin.gate_key = dict(warm["gate_key"])
    arm_s = cell["arm_tf_s"]
    lo_i = bisect_left(ts_5m, ws - arm_s)
    hi_i = bisect_left(ts_5m, ws)
    seed_win = rows_5m[lo_i:hi_i]
    if seed_win:
        twin.seed_arm(max(r[2] for r in seed_win), min(r[3] for r in seed_win))
    events: list[dict] = []
    realized = 0.0
    peak = dd = 0.0
    curve: list[tuple[int, float]] = []
    wi, wj = bisect_left(ts_5m, ws), bisect_left(ts_5m, we)
    for r in rows_5m[wi:wj]:
        ts = int(r[0])
        evs = twin.replay_bar(ts, r[1], r[2], r[3], r[4], bar_s=300)
        for e in evs:
            if e["action"] == "exit":
                realized += e["pnl_pct"]
        events.extend(evs)
        eq = realized
        if twin.pos != 0:
            sign = 1.0 if twin.pos == 1 else -1.0
            eq += sign * (r[4] - twin.entry_px) / twin.entry_px * 100.0
        peak = max(peak, eq)
        dd = max(dd, peak - eq)
        curve.append((ts, eq))
    exits = [e for e in events if e["action"] == "exit"]
    pnls = [e["pnl_pct"] for e in exits]
    kinds = {k: [e["pnl_pct"] for e in exits if e["kind"] == k] for k in ("bf", "brk", "flip")}
    episodes = []
    for e in exits:
        i, j = bisect_left(ts_5m, e["entry_ts"]), bisect_right(ts_5m, e["ts"])
        m = episode_metrics(
            rows_5m[i:j], e["dir"], e["entry_ts"], e["entry_px"], e["ts"], e["price"]
        )
        episodes.append((m["mfe"] * 100, m["mae"] * 100, m["give_back_pp"]))
    open_mtm = None
    open_dir = None
    if twin.pos != 0 and wi < wj:
        last = rows_5m[wj - 1]
        open_dir = "long" if twin.pos == 1 else "short"
        sign = 1.0 if twin.pos == 1 else -1.0
        open_mtm = sign * (last[4] - twin.entry_px) / twin.entry_px * 100.0
        i = bisect_left(ts_5m, twin.entry_ts)
        m = episode_metrics(
            rows_5m[i:wj], open_dir, twin.entry_ts, twin.entry_px, int(last[0]), last[4]
        )
        episodes.append((m["mfe"] * 100, m["mae"] * 100, m["give_back_pp"]))
    weekly = {}
    for wnum in range(4):
        a, b = ws + wnum * WEEK_S, ws + (wnum + 1) * WEEK_S
        wp = [e["pnl_pct"] for e in exits if a <= e["entry_ts"] < b]
        weekly[f"W{wnum + 1}"] = {"n": len(wp), "pnl_pp": round(sum(wp), 4)}
    mfes = [x[0] for x in episodes]
    maes = [x[1] for x in episodes]
    gbs = [x[2] for x in episodes]
    rec = {
        "cell_id": cell["cell_id"],
        "tag": cell["tag"],
        "symbol": coin,
        "tail": entry["tail"],
        "n_trades": len(exits),
        "sum_pnl_pp": round(sum(pnls), 4),
        "med_pnl_pct": round(_med(pnls), 4) if pnls else None,
        "win_rate": round(sum(1 for p in pnls if p > 0) / len(pnls), 4) if pnls else None,
        "n_bf": len(kinds["bf"]),
        "n_brk": len(kinds["brk"]),
        "n_flip": len(kinds["flip"]),
        "pnl_bf_pp": round(sum(kinds["bf"]), 4),
        "pnl_brk_pp": round(sum(kinds["brk"]), 4),
        "pnl_flip_pp": round(sum(kinds["flip"]), 4),
        "open_dir": open_dir,
        "open_mtm_pp": round(open_mtm, 4) if open_mtm is not None else None,
        "combined_pp": round(realized + (open_mtm or 0.0), 4),
        "max_dd_pp": round(dd, 4),
        "mfe_avg_pct": round(sum(mfes) / len(mfes), 4) if mfes else None,
        "mfe_med_pct": round(_med(mfes), 4) if mfes else None,
        "mae_avg_pct": round(sum(maes) / len(maes), 4) if maes else None,
        "gb_avg_pp": round(sum(gbs) / len(gbs), 4) if gbs else None,
        "gb_med_pp": round(_med(gbs), 4) if gbs else None,
        "gb_p90_pp": round(_pct(gbs, 0.9), 4) if gbs else None,
        "worst_mae_pct": round(max(maes), 4) if maes else None,
        "weekly": weekly,
        "warmup_1h_bars": warm["warmup_1h_bars"],
        "warmup_1d_bars": warm["warmup_1d_bars"],
        "n_5m_bars": wj - wi,
    }
    return {"rec": rec, "curve": curve, "episodes": episodes, "pnls": pnls}


def _rollup(cell: dict, sym_results: list[dict]) -> dict:
    """Roster rollup for one cell; parity symbol excluded (pre-reg)."""
    rs = [r for r in sym_results if r["rec"]["symbol"] != PARITY_SYMBOL]
    recs = [r["rec"] for r in rs]
    curves = [r["curve"] for r in rs]
    all_ts = sorted({t for c in curves for t, _ in c})
    idx = [0] * len(curves)
    last = [0.0] * len(curves)
    peak = dd = 0.0
    for t in all_ts:
        for k, c in enumerate(curves):
            while idx[k] < len(c) and c[idx[k]][0] <= t:
                last[k] = c[idx[k]][1]
                idx[k] += 1
        eq = sum(last)
        peak = max(peak, eq)
        dd = max(dd, peak - eq)
    eps = [e for r in rs for e in r["episodes"]]
    gbs = [e[2] for e in eps]
    maes = [e[1] for e in eps]
    mfes = [e[0] for e in eps]
    all_pnls = [p for r in rs for p in r["pnls"]]
    worst = None
    if recs:
        wr = max(recs, key=lambda r: r["worst_mae_pct"] or 0.0)
        if wr["worst_mae_pct"] is not None:
            worst = {"symbol": wr["symbol"], "mae_pct": wr["worst_mae_pct"]}
    weekly = {}
    for w in ("W1", "W2", "W3", "W4"):
        weekly[w] = {
            "n": sum(r["weekly"][w]["n"] for r in recs),
            "pnl_pp": round(sum(r["weekly"][w]["pnl_pp"] for r in recs), 4),
        }
    n_trades = sum(r["n_trades"] for r in recs)
    pnl = sum(r["sum_pnl_pp"] for r in recs)
    open_mtm = sum(r["open_mtm_pp"] or 0.0 for r in recs)
    return {
        "cell_id": cell["cell_id"],
        "tag": cell["tag"],
        **{
            k: cell[k]
            for k in (
                "arm_tf_s",
                "pool_12h",
                "n_max",
                "min_sep",
                "pool_cap",
                "brk_exit",
                "flip_backstop",
            )
        },
        "n_trades": n_trades,
        "realized_pp": round(pnl, 4),
        "open_mtm_pp": round(open_mtm, 4),
        "combined_pp": round(pnl + open_mtm, 4),
        "roster_max_dd_pp": round(dd, 4),
        "n_bf": sum(r["n_bf"] for r in recs),
        "n_brk": sum(r["n_brk"] for r in recs),
        "n_flip": sum(r["n_flip"] for r in recs),
        "pnl_bf_pp": round(sum(r["pnl_bf_pp"] for r in recs), 4),
        "pnl_brk_pp": round(sum(r["pnl_brk_pp"] for r in recs), 4),
        "pnl_flip_pp": round(sum(r["pnl_flip_pp"] for r in recs), 4),
        "n_open": sum(1 for r in recs if r["open_dir"]),
        "med_pnl_pct": round(_med(all_pnls), 4) if all_pnls else None,
        "win_rate": (
            round(sum(1 for p in all_pnls if p > 0) / len(all_pnls), 4) if all_pnls else None
        ),
        "mfe_avg_pct": round(sum(mfes) / len(mfes), 4) if mfes else None,
        "mfe_med_pct": round(_med(mfes), 4) if mfes else None,
        "gb_avg_pp": round(sum(gbs) / len(gbs), 4) if gbs else None,
        "gb_med_pp": round(_med(gbs), 4) if gbs else None,
        "gb_p90_pp": round(_pct(gbs, 0.9), 4) if gbs else None,
        "mae_avg_pct": round(sum(maes) / len(maes), 4) if maes else None,
        "worst_runner": worst,
        "weekly": weekly,
    }


def run_task(args: tuple) -> dict:
    """One warm-key task: warm 11 symbols once, replay the key's cells."""
    wk, cells, roster_symbols, ws, we, bars_dir = args
    t0 = time.time()
    warms = {e["name"]: _warm_symbol(e, wk, ws, bars_dir) for e in roster_symbols}
    sym_rows: list[dict] = []
    rollups: list[dict] = []
    for cell in cells:
        results = [
            _replay_cell(e, cell, warms[e["name"]], ws, we, bars_dir) for e in roster_symbols
        ]
        sym_rows.extend(r["rec"] for r in results)
        rollups.append(_rollup(cell, results))
    return {
        "warm_key": repr(wk),
        "elapsed_s": round(time.time() - t0, 1),
        "sym_rows": sym_rows,
        "rollups": rollups,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="TVB-19 Tier A deliberate-overfit sweep")
    ap.add_argument("--roster", default=str(REPO / "analysis" / "paper" / "roster_week1.json"))
    ap.add_argument("--bars-dir", default=str(REPO / "analysis" / "paper" / "bars"))
    ap.add_argument("--out-dir", default=str(OUT_DIR_DEFAULT))
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    ap.add_argument("--limit-cells", type=int, help="smoke runs only: first N cells")
    ap.add_argument("--symbols", help="smoke runs only: comma-separated subset")
    args = ap.parse_args()

    roster = json.loads(Path(args.roster).read_text())
    symbols = roster["symbols"]
    if args.symbols:
        keep = set(args.symbols.split(","))
        symbols = [e for e in symbols if e["name"] in keep]
    cells = grid()
    if args.limit_cells:
        cells = cells[: args.limit_cells]
    ws = int(datetime.fromisoformat(WINDOW_START).replace(tzinfo=timezone.utc).timestamp())
    we = int(datetime.fromisoformat(WINDOW_END).replace(tzinfo=timezone.utc).timestamp())

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO
    ).stdout.strip()
    bar_hashes = {}
    for e in symbols:
        for iv in ("5m", "1h", "1d"):
            p = Path(args.bars_dir) / f"{e['name'].replace(':', '_')}_{iv}.json"
            bar_hashes[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    manifest = {
        "prereg": "docs/experiments/tvb19_tier_a_prereg.md",
        "label": "DELIBERATE OVERFIT / in-sample ceiling / secondary control",
        "git_head": head,
        "window": {"start": WINDOW_START, "end": WINDOW_END},
        "n_cells": len(cells),
        "n_symbols": len(symbols),
        "grid": {
            "arm_tf_s": ARM_TF_S,
            "pool_12h": POOL_12H,
            "n_max": N_MAX,
            "min_sep": MIN_SEP,
            "pool_cap": POOL_CAP,
            "brk_exit": BRK_EXIT,
            "flip_backstop": FLIP_BACKSTOP,
        },
        "bar_hashes": bar_hashes,
        "run_start_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_end_utc": None,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")

    by_key: dict[tuple, list[dict]] = {}
    for c in cells:
        by_key.setdefault(warm_key(c), []).append(c)
    tasks = [(wk, cl, symbols, ws, we, args.bars_dir) for wk, cl in by_key.items()]
    print(
        f"{len(cells)} cells in {len(tasks)} warm-key tasks, {len(symbols)} symbols, "
        f"workers={args.workers}",
        flush=True,
    )

    sym_rows: list[dict] = []
    rollups: list[dict] = []
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for i, res in enumerate(ex.map(run_task, tasks), 1):
            sym_rows.extend(res["sym_rows"])
            rollups.extend(res["rollups"])
            print(
                f"[{i}/{len(tasks)}] {res['warm_key']} done in {res['elapsed_s']}s "
                f"(total {time.time() - t0:.0f}s)",
                flush=True,
            )

    sym_rows.sort(key=lambda r: (r["cell_id"], r["symbol"]))
    rollups.sort(key=lambda r: r["cell_id"])
    with open(out_dir / "results_by_symbol.jsonl", "w", encoding="utf-8") as f:
        for r in sym_rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    with open(out_dir / "results_rollup.jsonl", "w", encoding="utf-8") as f:
        for r in rollups:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    manifest["run_end_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"wrote {len(sym_rows)} symbol rows, {len(rollups)} rollups -> {out_dir}", flush=True)


if __name__ == "__main__":
    main()
