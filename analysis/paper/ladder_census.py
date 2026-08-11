"""TVB-22 audit F2 receipt: A1 ladder-traversal census with pinned conventions.

The TVB-22 next-variant seed quoted a ladder-traversal census (70% of trades
touched >= 2 frozen rungs, 40% >= 4, 43% stalled at 1-2, harvest exits after
~3.6 rungs) from post-hoc reads whose denominator, touch convention, and
open-trade treatment were never committed (external audit F2, LOW,
2026-08-10). This module IS the reproducible receipt: it replays arm A1
deterministically (same warm/seed/replay path as analysis/paper/tier_b.py,
which stays untouched -- its blob hash is pinned in the committed manifest),
counts frozen-ladder rungs reached per trade under DECLARED conventions, and
writes analysis/paper/tier_b/ladder_census_receipt.json with exact counts.

PINNED CONVENTIONS (restated machine-readably in the receipt):

- Scope: arm A1 over the frozen week-1 roster MINUS the parity symbol
  (xyz:DRAM) -- the same 10-symbol set as every Tier B rollup. Window
  2026-07-06 -> 2026-08-03 (the committed Tier B window).
- Ladder: each trade's ENTRY-SNAPSHOT ladder, frozen at entry (rung 1 =
  ladder[0], nearest). rungs_reached = DEEPEST rung index satisfied by any
  counted bar; 0 if none. Zero-rung trades stay IN every denominator.
- Bars counted: strictly AFTER the entry bar (the engine's exit race cannot
  fire on the entry bar, and intrabar order there is unknowable from 5m
  OHLC) through the exit bar INCLUSIVE (the exit race sees its full range).
- Touch conventions -- BOTH reported, every published figure labeled:
  * reach: favorable extreme at/past the rung (long high >= rung, short
    low <= rung). Measures PRICE TRAVEL; a gap past a rung counts.
  * containment: low <= rung <= high -- the ruled FILL convention
    (2026-08-09 prereg amendment). What a containment target-exit could
    have captured; a bar wholly past a rung does NOT count.
- Denominators, one per figure: "closed" = all closed A1 trades;
  "closed_open" adds each symbol's open trade marked through the window's
  last bar; "bf"/"brk"/"flip" = closed subsets by exit kind.
- Determinism guard (fail-closed): per-symbol closed-trade counts and open
  direction must equal the committed A1 rows in
  analysis/paper/tier_b/results_by_symbol.jsonl or the run FAILS.

Run: uv run python -m analysis.paper.ladder_census
"""

from __future__ import annotations

import argparse
import json
from bisect import bisect_left
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from analysis.paper.engine import Twin, TwinConfig
from analysis.paper.sweep_tier_a import (
    PARITY_SYMBOL,
    WINDOW_END,
    WINDOW_START,
    _rows,
    _warm_symbol,
)
from analysis.paper.tier_b import ARMS, WARM_KEY

REPO = Path(__file__).resolve().parents[2]
TIER_B_DIR = REPO / "analysis" / "paper" / "tier_b"
RECEIPT_DEFAULT = TIER_B_DIR / "ladder_census_receipt.json"

A1 = next(a for a in ARMS if a["arm_id"] == "A1")
CONVENTIONS = ("reach", "containment")


def rungs_reached(
    rows_5m: list, i_start: int, i_end: int, ladder: list, direction: str, convention: str
) -> int:
    """Deepest 1-based rung index satisfied on rows_5m[i_start:i_end]; 0 if none.

    Every rung is scanned independently (no monotonicity assumption): under
    containment a gap can skip a shallow rung while a deeper one is contained.
    """
    deepest = 0
    for i, tgt in enumerate(ladder):
        for r in rows_5m[i_start:i_end]:
            h, low = r[2], r[3]
            if convention == "reach":
                hit = h >= tgt if direction == "long" else low <= tgt
            else:
                hit = low <= tgt <= h
            if hit:
                deepest = max(deepest, i + 1)
                break
    return deepest


def _replay_a1(entry: dict, warm: dict, ws: int, we: int, bars_dir: str):
    """A1 replay, seeding mirrored line-for-line from tier_b._replay_arm."""
    coin = entry["name"]
    rows_5m = _rows(coin, "5m", bars_dir)
    ts_5m = [r[0] for r in rows_5m]
    cfg = TwinConfig(symbol=coin, mintick=float(entry["tv_mintick"]), **A1["twin"])
    twin = Twin(cfg)
    twin.pools = deepcopy(warm["pools"])
    twin.gate_open = dict(warm["gate_open"])
    twin.gate_key = dict(warm["gate_key"])
    lo_i = bisect_left(ts_5m, ws - cfg.arm_tf_s)
    hi_i = bisect_left(ts_5m, ws)
    seed_win = rows_5m[lo_i:hi_i]
    if seed_win:
        twin.seed_arm(max(r[2] for r in seed_win), min(r[3] for r in seed_win))
    if twin.pattern is not None:
        pre_1h = [r for r in _rows(coin, "1h", bars_dir) if r[0] < ws]
        twin.pattern.seed_history(pre_1h[-twin.pattern.HISTORY_CAP :])
    events: list[dict] = []
    wi, wj = bisect_left(ts_5m, ws), bisect_left(ts_5m, we)
    for r in rows_5m[wi:wj]:
        events.extend(twin.replay_bar(int(r[0]), r[1], r[2], r[3], r[4], bar_s=300))
    return events, rows_5m, ts_5m, wj, twin


def _census_rows(symbols: list[dict], ws: int, we: int, bars_dir: str) -> list[dict]:
    rows: list[dict] = []
    for entry in symbols:
        warm = _warm_symbol(entry, WARM_KEY, ws, bars_dir)
        events, rows_5m, ts_5m, wj, twin = _replay_a1(entry, warm, ws, we, bars_dir)
        entries_by_ts = {e["ts"]: e for e in events if e["action"] == "enter"}
        trades = [
            (e["entry_ts"], e["ts"], e["kind"], e["dir"]) for e in events if e["action"] == "exit"
        ]
        if twin.pos != 0:
            trades.append((twin.entry_ts, None, "open", "long" if twin.pos == 1 else "short"))
        for entry_ts, exit_ts, kind, d in trades:
            ee = entries_by_ts[entry_ts]
            i_entry = bisect_left(ts_5m, entry_ts)
            i_end = bisect_left(ts_5m, exit_ts) + 1 if exit_ts is not None else wj
            row = {
                "symbol": entry["name"],
                "dir": d,
                "entry_ts": entry_ts,
                "exit_ts": exit_ts,
                "exit_kind": kind,
                "pattern": ee.get("pattern"),
                "ladder_len": len(ee.get("ladder") or []),
            }
            for conv in CONVENTIONS:
                row[f"rungs_{conv}"] = rungs_reached(
                    rows_5m, i_entry + 1, i_end, ee.get("ladder") or [], d, conv
                )
            rows.append(row)
    return rows


def _shares(rows: list[dict], conv: str) -> dict:
    n = len(rows)
    reached = [r[f"rungs_{conv}"] for r in rows]
    hist: dict[str, int] = {}
    for v in reached:
        hist[str(v)] = hist.get(str(v), 0) + 1

    def share(pred):
        k = sum(1 for v in reached if pred(v))
        return {"n": k, "of": n, "pct": round(100.0 * k / n, 1) if n else None}

    return {
        "n": n,
        "histogram": dict(sorted(hist.items(), key=lambda kv: int(kv[0]))),
        "ge1": share(lambda v: v >= 1),
        "ge2": share(lambda v: v >= 2),
        "ge4": share(lambda v: v >= 4),
        "stall_1_2": share(lambda v: v in (1, 2)),
        "mean": round(sum(reached) / n, 4) if n else None,
        "mean_excl_zero": (
            round(sum(v for v in reached if v) / max(1, sum(1 for v in reached if v)), 4)
            if any(reached)
            else None
        ),
        "n_zero": sum(1 for v in reached if v == 0),
    }


def _determinism_check(rows: list[dict], symbols: list[dict]) -> dict:
    committed: dict[str, dict] = {}
    with open(TIER_B_DIR / "results_by_symbol.jsonl", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if rec["arm_id"] == "A1":
                committed[rec["symbol"]] = rec
    mismatches = []
    for e in symbols:
        coin = e["name"]
        base = committed.get(coin)
        n_closed = sum(1 for r in rows if r["symbol"] == coin and r["exit_kind"] != "open")
        open_dirs = [r["dir"] for r in rows if r["symbol"] == coin and r["exit_kind"] == "open"]
        if base is None:
            mismatches.append({"symbol": coin, "field": "(committed A1 row missing)"})
            continue
        if n_closed != base["n_trades"]:
            mismatches.append(
                {
                    "symbol": coin,
                    "field": "n_trades",
                    "ours": n_closed,
                    "committed": base["n_trades"],
                }
            )
        if (open_dirs[0] if open_dirs else None) != base["open_dir"]:
            mismatches.append(
                {
                    "symbol": coin,
                    "field": "open_dir",
                    "ours": open_dirs[0] if open_dirs else None,
                    "committed": base["open_dir"],
                }
            )
    return {"n_committed_rows": len(committed), "mismatches": mismatches}


def main() -> None:
    ap = argparse.ArgumentParser(description="TVB-22 A1 ladder-traversal census receipt")
    ap.add_argument("--roster", default=str(REPO / "analysis" / "paper" / "roster_week1.json"))
    ap.add_argument("--bars-dir", default=str(REPO / "analysis" / "paper" / "bars"))
    ap.add_argument("--out", default=str(RECEIPT_DEFAULT))
    args = ap.parse_args()

    roster = json.loads(Path(args.roster).read_text())
    symbols = [e for e in roster["symbols"] if e["name"] != PARITY_SYMBOL]
    ws = int(datetime.fromisoformat(WINDOW_START).replace(tzinfo=timezone.utc).timestamp())
    we = int(datetime.fromisoformat(WINDOW_END).replace(tzinfo=timezone.utc).timestamp())

    rows = _census_rows(symbols, ws, we, args.bars_dir)
    check = _determinism_check(rows, symbols)
    closed = [r for r in rows if r["exit_kind"] != "open"]

    aggregates: dict[str, dict] = {}
    for conv in CONVENTIONS:
        aggregates[conv] = {
            "closed": _shares(closed, conv),
            "closed_open": _shares(rows, conv),
            "by_exit_kind": {
                k: _shares([r for r in closed if r["exit_kind"] == k], conv)
                for k in ("bf", "brk", "flip")
            },
        }

    receipt = {
        "generated_utc": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "purpose": "TVB-22 audit F2: reproducible A1 ladder-traversal census receipt",
        "conventions": {
            "scope": f"arm A1, week-1 roster minus parity symbol {PARITY_SYMBOL} (10 symbols)",
            "window": {"start": WINDOW_START, "end": WINDOW_END},
            "ladder": "entry-snapshot ladder frozen at entry; rung 1 = ladder[0] (nearest); "
            "rungs_reached = deepest rung satisfied; zero-rung trades stay in denominators",
            "bars_counted": "strictly after the entry bar through the exit bar inclusive; "
            "open trades marked through the window's last bar",
            "touch_reach": "favorable extreme at/past rung (long high >= rung, short low <= rung); "
            "price travel, gap-past counts",
            "touch_containment": "low <= rung <= high (ruled fill convention, 2026-08-09 "
            "amendment); gap-past does not count",
        },
        "symbols": [e["name"] for e in symbols],
        "determinism_check_vs_committed_a1_rows": check,
        "aggregates": aggregates,
        "per_trade": rows,
    }
    Path(args.out).write_text(json.dumps(receipt, indent=1) + "\n")

    for conv in CONVENTIONS:
        a = aggregates[conv]["closed"]
        print(
            f"{conv:12s} closed n={a['n']}: >=1 {a['ge1']['pct']}%, >=2 {a['ge2']['pct']}%, "
            f">=4 {a['ge4']['pct']}%, stall 1-2 {a['stall_1_2']['pct']}%, "
            f"mean {a['mean']} (excl-zero {a['mean_excl_zero']})"
        )
        for k, s in aggregates[conv]["by_exit_kind"].items():
            print(
                f"  {k:4s} n={s['n']}: mean {s['mean']} (excl-zero {s['mean_excl_zero']}, "
                f"zero-rung {s['n_zero']})"
            )
    ok = not check["mismatches"]
    print(f"determinism vs committed A1 rows: {'PASS' if ok else 'FAIL'}")
    print(f"receipt: {args.out}")
    if not ok:
        for m in check["mismatches"]:
            print(f"  mismatch: {m}")
        raise SystemExit("census replay does not reproduce the committed A1 book")


if __name__ == "__main__":
    main()
