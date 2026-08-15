"""Entry-layer audit receipts: identity funnel, containment, fill benchmarks.

Folds the 2026-08-14 strategy-implementation assessment's two verified
entry-layer diagnostics (docs/strategy-implementation-assessment.md, P0-2 and
P1-1) plus the TVB-24 session's containment check into committed, receipt-backed
tooling over the COMMITTED TVB-23 round artifacts. Nothing is regenerated;
the module writes only its own receipt (entry_audit_receipt.json).

THE THREE FILL BENCHMARKS (adjudicated 2026-08-15; every fill claim must name
its benchmark):
1. vs the level/open pair: the engine books max(trig + tick, bar open) for
   longs (mirror shorts) -- always the WORSE of the two, so it is
   conservative-by-construction against those references (the sense every
   prior "CONSERVATIVE" claim is scoped to).
2. vs the decision-bar close (the replay's own confirmation clock): the same
   fills come out FAVORABLE on a majority of entries (the bar tends to keep
   moving with the trade after the cross) -- quantified here per arm.
3. vs live intrabar execution (the user's actual behavior): UNRESOLVED by 5m
   OHLC -- the moment the last predicate became true within the bar is not
   observable at this resolution.

CONTAINMENT: a persisting 1H signal can book a level fill on a later 5m bar
whose range never traded the level (the entry-side analogue of TVB-21's
born-beyond exits). By construction of the max/min fill rule such a fill is
always on the FAR side of the bar -- i.e. PESSIMISTIC for the trade -- so it
deflates rather than inflates P&L; it is a model-fidelity blemish, not an
edge source. Counted and listed per arm, all symbols (fidelity property, so
the parity symbol is included and flagged).

SIGNAL IDENTITY (assessment P1-1): identity = (symbol, 1H signal-bar open,
direction, pattern, trigger). Candidate counters count flat-bar EVALUATIONS
(a persisting 1H signal recounts on successive 5m closes, up to 12); entry
identities count opportunities. Entry-side stats come from the committed
dumps; the evaluation-level funnel requires an instrumented replay and is
computed for D1 (the assessment's diagnostic arm) at receipt-generation time.

Run: uv run python -m analysis.paper.entry_audit
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from analysis.paper.sweep_tier_a import PARITY_SYMBOL, _rows

REPO = Path(__file__).resolve().parents[2]
ROUND_DIR = REPO / "analysis" / "paper" / "tier_b_t1floor"
ARM_IDS = ("D1", "D2", "D3", "D4", "D5", "DINF", "A1F", "D1ATR")

_bar_maps: dict[str, dict[int, tuple]] = {}


def _bar(sym: str, ts: int, bars_dir: str):
    if sym not in _bar_maps:
        _bar_maps[sym] = {int(r[0]): r for r in _rows(sym, "5m", bars_dir)}
    return _bar_maps[sym].get(ts)


def _entries(arm: str) -> list[dict]:
    p = ROUND_DIR / f"events_{arm}.jsonl"
    evs = [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return [e for e in evs if e["action"] == "enter"]


def _identity(e: dict) -> tuple:
    ts = int(e["ts"])
    return (e["sym"], ts - ts % 3600, e["dir"], e["pattern"], float(e["trig"]))


def entry_stats(arm: str, bars_dir: str, minticks: dict[str, float]) -> dict:
    """Identity, containment, and close-benchmark stats for one arm's dump."""
    entries = _entries(arm)
    roster = [e for e in entries if e["sym"] != PARITY_SYMBOL]

    ids = Counter(_identity(e) for e in roster)
    reentered = {k: v for k, v in ids.items() if v > 1}

    outside = []
    diffs = []
    for e in entries:
        r = _bar(e["sym"], int(e["ts"]), bars_dir)
        if r is None:
            raise ValueError(f"{arm}: no 5m bar for entry {e['sym']} ts={e['ts']}")
        h, low, close = float(r[2]), float(r[3]), float(r[4])
        p = float(e["price"])
        tick = minticks[e["sym"]]
        eps = max(abs(p), 1.0) * 1e-9 + tick * 1e-9
        if not (low - eps <= p <= h + eps):
            # far-side by construction of max/min fill => pessimistic booking
            outside.append(
                {
                    "symbol": e["sym"],
                    "parity_symbol": e["sym"] == PARITY_SYMBOL,
                    "ts": e["ts"],
                    "dir": e["dir"],
                    "price": p,
                    "bar_low": low,
                    "bar_high": h,
                    "dist_pp": round(((p - h) / h if p > h else (low - p) / low) * 100.0, 4),
                }
            )
        if e["sym"] != PARITY_SYMBOL:
            adv = ((close - p) / p if e["dir"] == "long" else (p - close) / p) * 100.0
            diffs.append(adv)

    absd = sorted(abs(d) for d in diffs)
    n = len(absd)
    med = None
    if diffs:
        s = sorted(diffs)
        med = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0
    return {
        "n_entries_all_symbols": len(entries),
        "n_entries_roster": len(roster),
        "identity": {
            "distinct": len(ids),
            "reentered_identities": len(reentered),
            "max_entries_one_identity": max(ids.values()) if ids else 0,
        },
        "containment": {
            "n_checked_all_symbols": len(entries),
            "n_outside_entry_bar_range": len(outside),
            "outside": outside,
        },
        "vs_decision_bar_close_roster": {
            "n": n,
            "favorable": sum(1 for d in diffs if d > 0),
            "adverse": sum(1 for d in diffs if d < 0),
            "mean_signed_pp": round(sum(diffs) / n, 4) if n else None,
            "median_signed_pp": round(med, 4) if med is not None else None,
            "p90_abs_pp": round(absd[int(0.9 * (n - 1))], 4) if n else None,
            "max_abs_pp": round(absd[-1], 4) if n else None,
            "sum_signed_pp": round(sum(diffs), 4) if n else None,
        },
    }


def d1_evaluation_funnel(bars_dir: str) -> dict:
    """Instrumented D1 replay: evaluation-level identity funnel, roster scope.

    Monkeypatches Twin._pattern_entry (restored in finally) to log one
    identity per candidate evaluation, then replays the D1 arm through the
    runner's own _replay_arm_ext. Read-only; used only at receipt time."""
    from datetime import datetime as _dt

    from analysis.paper.engine import Twin
    from analysis.paper.sweep_tier_a import WINDOW_END, WINDOW_START, _warm_symbol
    from analysis.paper.tier_b import WARM_KEY
    from analysis.paper.tier_b_t1floor import NEW_ARMS, _replay_arm_ext

    ws = int(_dt.fromisoformat(WINDOW_START).replace(tzinfo=timezone.utc).timestamp())
    we = int(_dt.fromisoformat(WINDOW_END).replace(tzinfo=timezone.utc).timestamp())
    d1 = next(a for a in NEW_ARMS if a["arm_id"] == "D1")
    roster = json.loads((REPO / "analysis" / "paper" / "roster_week1.json").read_text())
    symbols = [e for e in roster["symbols"] if e["name"] != PARITY_SYMBOL]

    eval_log: list[tuple] = []
    orig = Twin._pattern_entry

    def patched(self, ts, o, sig, prox_vals, events):
        eval_log.append((self.cfg.symbol, int(ts) - int(ts) % 3600, sig.dir, sig.name, sig.trig))
        return orig(self, ts, o, sig, prox_vals, events)

    Twin._pattern_entry = patched
    try:
        for e in symbols:
            warm = _warm_symbol(e, WARM_KEY, ws, bars_dir)
            _replay_arm_ext(e, d1, warm, ws, we, bars_dir)
    finally:
        Twin._pattern_entry = orig

    ec = Counter(eval_log)
    return {
        "arm": "D1",
        "scope": "roster (parity symbol excluded)",
        "candidate_evaluations": len(eval_log),
        "distinct_identities": len(ec),
        "evaluations_per_identity": round(len(eval_log) / len(ec), 2) if ec else None,
        "identities_evaluated_more_than_once": sum(1 for v in ec.values() if v > 1),
        "max_evaluations_one_identity": max(ec.values()) if ec else 0,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Entry-layer audit receipt (TVB-24 fold)")
    ap.add_argument("--bars-dir", default=str(REPO / "analysis" / "paper" / "bars"))
    ap.add_argument("--out-dir", default=str(ROUND_DIR))
    ap.add_argument("--skip-funnel", action="store_true", help="skip the instrumented replay")
    args = ap.parse_args()

    roster = json.loads((REPO / "analysis" / "paper" / "roster_week1.json").read_text())
    minticks = {e["name"]: float(e["tv_mintick"]) for e in roster["symbols"]}
    src_hashes = {
        f"events_{a}.jsonl": hashlib.sha256(
            (ROUND_DIR / f"events_{a}.jsonl").read_bytes()
        ).hexdigest()[:16]
        for a in ARM_IDS
    }

    per_arm = {a: entry_stats(a, args.bars_dir, minticks) for a in ARM_IDS}
    receipt = {
        "generated_utc": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "purpose": "entry-layer audit: identity funnel, fill containment, and "
        "decision-close fill benchmark over the committed TVB-23 arms "
        "(2026-08-14 assessment P0-2/P1-1 fold + TVB-24 containment check)",
        "conventions": "module docstring analysis/paper/entry_audit.py (the three "
        "fill benchmarks; identity tuple; containment scope all symbols, close "
        "benchmark roster scope)",
        "source_hashes": src_hashes,
        "per_arm": per_arm,
        "d1_evaluation_funnel": None if args.skip_funnel else d1_evaluation_funnel(args.bars_dir),
    }
    out = Path(args.out_dir) / "entry_audit_receipt.json"
    out.write_text(json.dumps(receipt, indent=1) + "\n")

    tot_outside = sum(p["containment"]["n_outside_entry_bar_range"] for p in per_arm.values())
    tot_entries = sum(p["n_entries_all_symbols"] for p in per_arm.values())
    print(
        f"entry_audit_receipt.json: {tot_entries} entries across {len(ARM_IDS)} arms, "
        f"{tot_outside} outside entry-bar range (all pessimistic-direction)"
    )
    d1 = per_arm["D1"]
    c = d1["vs_decision_bar_close_roster"]
    print(
        f"  D1 roster vs close: n={c['n']} fav={c['favorable']} adv={c['adverse']} "
        f"mean={c['mean_signed_pp']} sum={c['sum_signed_pp']} max|.|={c['max_abs_pp']}"
    )
    if receipt["d1_evaluation_funnel"]:
        f = receipt["d1_evaluation_funnel"]
        print(
            f"  D1 funnel: {f['candidate_evaluations']} evaluations -> "
            f"{f['distinct_identities']} identities "
            f"({f['evaluations_per_identity']}/identity, max {f['max_evaluations_one_identity']})"
        )


if __name__ == "__main__":
    main()
