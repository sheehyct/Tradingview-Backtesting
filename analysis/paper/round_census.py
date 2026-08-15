"""TVB-23 per-arm census receipts: ladder traversal + retracement labels.

Consumes the tier_b_t1floor event dumps (events_{arm}.jsonl: entry events
carry the frozen snapshot ladder; exit events and the open_mark pseudo-event
carry the read-only retracement first-label stamps) plus the archived 5m
bars, and writes one receipt per arm with every convention pinned.

CONVENTIONS (inherited from the committed A1 receipt,
analysis/paper/ladder_census.py -- restated machine-readably per receipt):
- rungs_reached = deepest 1-based rung of the trade's ENTRY-SNAPSHOT ladder
  satisfied on bars strictly AFTER the entry bar through the exit bar
  INCLUSIVE (open trades: through the window's last bar). Both touch
  conventions reported: reach (favorable extreme at/past the rung; price
  travel, gap-past counts) and containment (low <= rung <= high, the ruled
  fill convention). Zero-rung trades stay in every denominator.
- Retracement census (prereg ruling 5): rungs reached BEFORE each first
  label = the same walk truncated at the label bar EXCLUSIVE (the travel
  known before the label appeared). Labels are the engine's read-only
  first-occurrence stamps (RETRACEMENT / POTENTIAL 3, pine-exact
  predicates, as-built one-sided-flag edge documented in the prereg).
- Determinism guard (fail-closed; hardened 2026-08-15, TVB-23 audit F1):
  per symbol vs the round's results_by_symbol.jsonl rows for the arm --
  closed-trade counts equal, OPEN-trade count and direction equal to the
  row's open_dir (a deleted open_mark now mismatches), no unknown symbols;
  exit/open_mark events without a matching entry fail event linkage.

Run: uv run python -m analysis.paper.round_census [--arms D1,D2,...]
"""

from __future__ import annotations

import argparse
import json
from bisect import bisect_left
from datetime import datetime, timezone
from pathlib import Path

from analysis.paper.ladder_census import CONVENTIONS, rungs_reached
from analysis.paper.sweep_tier_a import PARITY_SYMBOL, _rows

REPO = Path(__file__).resolve().parents[2]
ROUND_DIR = REPO / "analysis" / "paper" / "tier_b_t1floor"
ARM_IDS = ("D1", "D2", "D3", "D4", "D5", "DINF", "A1F", "D1ATR")


def _trade_rows(events: list[dict], bars_dir: str) -> list[dict]:
    entries = {(e["sym"], e["ts"]): e for e in events if e["action"] == "enter"}
    rows: list[dict] = []
    for e in events:
        if e["action"] not in ("exit", "open_mark") or e["sym"] == PARITY_SYMBOL:
            # roster scope: the parity symbol is excluded from every rollup
            # and from the committed A1 receipt -- same convention here
            continue
        ee = entries.get((e["sym"], e["entry_ts"]))
        if ee is None:
            # fail-closed event linkage (2026-08-15, audit F1): a dump whose
            # exit/open_mark lost its entry must never census silently
            raise ValueError(
                f"census event-linkage broken: {e['action']} {e['sym']} ts={e['ts']} "
                f"has no matching entry at entry_ts={e['entry_ts']}"
            )
        rows_5m = _rows(e["sym"], "5m", bars_dir)
        ts_5m = [r[0] for r in rows_5m]
        i_entry = bisect_left(ts_5m, e["entry_ts"])
        i_end = bisect_left(ts_5m, e["ts"]) + 1
        ladder = ee.get("ladder") or []
        d = e["dir"]
        row = {
            "symbol": e["sym"],
            "dir": d,
            "entry_ts": e["entry_ts"],
            "exit_ts": e["ts"] if e["action"] == "exit" else None,
            "exit_kind": e["kind"] if e["action"] == "exit" else "open",
            "pnl_pct": e.get("pnl_pct"),
            "pattern": ee.get("pattern"),
            "ladder_len": len(ladder),
            "first_retrace_ts": e.get("first_retrace_ts"),
            "first_p3_ts": e.get("first_p3_ts"),
        }
        for conv in CONVENTIONS:
            row[f"rungs_{conv}"] = rungs_reached(rows_5m, i_entry + 1, i_end, ladder, d, conv)
        # rungs known BEFORE each first label (label bar exclusive)
        for label in ("retrace", "p3"):
            lts = e.get(f"first_{label}_ts")
            row[f"rungs_reach_before_{label}"] = (
                rungs_reached(rows_5m, i_entry + 1, bisect_left(ts_5m, lts), ladder, d, "reach")
                if lts is not None
                else None
            )
        rows.append(row)
    return rows


def _share(rows: list[dict], pred) -> dict:
    n = len(rows)
    k = sum(1 for r in rows if pred(r))
    return {"n": k, "of": n, "pct": round(100.0 * k / n, 1) if n else None}


def _ladder_aggregates(rows: list[dict]) -> dict:
    out: dict = {}
    for conv in CONVENTIONS:
        reached = [r[f"rungs_{conv}"] for r in rows]
        hist: dict[str, int] = {}
        for v in reached:
            hist[str(v)] = hist.get(str(v), 0) + 1
        out[conv] = {
            "n": len(rows),
            "histogram": dict(sorted(hist.items(), key=lambda kv: int(kv[0]))),
            "ge2": _share(rows, lambda r: r[f"rungs_{conv}"] >= 2),
            "ge4": _share(rows, lambda r: r[f"rungs_{conv}"] >= 4),
            "stall_1_2": _share(rows, lambda r: r[f"rungs_{conv}"] in (1, 2)),
            "zero": _share(rows, lambda r: r[f"rungs_{conv}"] == 0),
            "mean": round(sum(reached) / len(reached), 4) if rows else None,
        }
    return out


def _retrace_aggregates(rows: list[dict]) -> dict:
    def block(sub: list[dict], label: str) -> dict:
        labeled = [r for r in sub if r[f"first_{label}_ts"] is not None]
        before = [r[f"rungs_reach_before_{label}"] for r in labeled]
        return {
            "ever": _share(sub, lambda r: r[f"first_{label}_ts"] is not None),
            "rungs_before_mean": round(sum(before) / len(before), 4) if before else None,
            "rungs_before_hist": {str(v): before.count(v) for v in sorted(set(before))},
        }

    closed = [r for r in rows if r["exit_kind"] != "open"]
    winners = [r for r in closed if (r["pnl_pct"] or 0) > 0]
    losers = [r for r in closed if (r["pnl_pct"] or 0) <= 0]
    out = {}
    for label in ("retrace", "p3"):
        out[label] = {
            "all": block(rows, label),
            "closed": block(closed, label),
            "winners": block(winners, label),
            "losers": block(losers, label),
            "by_exit_kind": {
                k: block([r for r in closed if r["exit_kind"] == k], label)
                for k in sorted({r["exit_kind"] for r in closed})
            },
        }
    return out


def _determinism(rows: list[dict], arm_id: str, results_path: Path) -> dict:
    """Hardened 2026-08-15 (TVB-23 audit F1): closed counts AND open-trade
    count/direction must match the round rows; unknown symbols mismatch."""
    committed: dict[str, dict] = {}
    with open(results_path, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if rec["arm_id"] == arm_id and rec["symbol"] != PARITY_SYMBOL:
                committed[rec["symbol"]] = {
                    "n_trades": rec["n_trades"],
                    "open_dir": rec.get("open_dir"),
                }
    mismatches = []
    for sym, exp in sorted(committed.items()):
        closed = sum(1 for r in rows if r["symbol"] == sym and r["exit_kind"] != "open")
        opens = [r for r in rows if r["symbol"] == sym and r["exit_kind"] == "open"]
        if closed != exp["n_trades"]:
            mismatches.append(
                {"symbol": sym, "field": "closed", "ours": closed, "rows": exp["n_trades"]}
            )
        want_open = 1 if exp["open_dir"] else 0
        if len(opens) != want_open:
            mismatches.append(
                {"symbol": sym, "field": "open", "ours": len(opens), "rows": want_open}
            )
        elif opens and opens[0]["dir"] != exp["open_dir"]:
            mismatches.append(
                {
                    "symbol": sym,
                    "field": "open_dir",
                    "ours": opens[0]["dir"],
                    "rows": exp["open_dir"],
                }
            )
    for sym in sorted({r["symbol"] for r in rows} - set(committed)):
        mismatches.append({"symbol": sym, "field": "(unknown symbol)", "ours": None, "rows": None})
    return {"n_symbols": len(committed), "mismatches": mismatches}


def main() -> None:
    ap = argparse.ArgumentParser(description="TVB-23 per-arm census receipts")
    ap.add_argument("--arms", default=",".join(ARM_IDS))
    ap.add_argument("--round-dir", default=str(ROUND_DIR))
    ap.add_argument("--bars-dir", default=str(REPO / "analysis" / "paper" / "bars"))
    args = ap.parse_args()
    round_dir = Path(args.round_dir)
    results_path = round_dir / "results_by_symbol.jsonl"

    failures = []
    for arm_id in args.arms.split(","):
        events_path = round_dir / f"events_{arm_id}.jsonl"
        events = [json.loads(ln) for ln in events_path.read_text(encoding="utf-8").splitlines()]
        rows = _trade_rows(events, args.bars_dir)
        check = _determinism(rows, arm_id, results_path)
        receipt = {
            "generated_utc": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
            "arm_id": arm_id,
            "purpose": "TVB-23 per-arm ladder-traversal + retracement census receipt",
            "conventions": "module docstring analysis/paper/round_census.py (pinned); "
            "ladder walk inherits the committed A1 receipt's conventions",
            "determinism_check_vs_round_rows": check,
            "ladder": {
                "closed": _ladder_aggregates([r for r in rows if r["exit_kind"] != "open"]),
                "closed_open": _ladder_aggregates(rows),
            },
            "retracement": _retrace_aggregates(rows),
            "per_trade": rows,
        }
        out = round_dir / f"census_{arm_id}.json"
        out.write_text(json.dumps(receipt, indent=1) + "\n")
        closed = [r for r in rows if r["exit_kind"] != "open"]
        ever_p3 = sum(1 for r in closed if r["first_p3_ts"] is not None)
        print(
            f"{arm_id}: {len(closed)} closed / {len(rows) - len(closed)} open; "
            f"reach >=2 {receipt['ladder']['closed']['reach']['ge2']['pct']}%, "
            f"ever-P3 {ever_p3}/{len(closed)}; "
            f"determinism {'PASS' if not check['mismatches'] else 'FAIL'} -> {out.name}"
        )
        if check["mismatches"]:
            failures.append(arm_id)
    if failures:
        raise SystemExit(f"census determinism FAILED for {failures}")


if __name__ == "__main__":
    main()
