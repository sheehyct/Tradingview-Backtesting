"""TVB-23 prereg-bound diagnostics delivered post-hoc (TVB-23 audit F2).

The preregistration's "Metrics + pre-committed diagnostics" section binds two
diagnostics the committed round omitted (docs/experiments/tvb23_t1floor_prereg.md,
"Veto suppression per symbol ... with ATR% of price stated per symbol for
context" and "matched-entry (shared-prefix) per-trade exit comparison as the
exits-in-isolation diagnostic"). This module computes both from the COMMITTED
round artifacts and archived bars -- it regenerates nothing and writes only
its own two receipts:

- atr_context_receipt.json: per roster symbol, Wilder ATR(14) on the engine's
  own 1H aggregation as a PERCENT OF PRICE over the window (value as of each
  completed 1H bar, matching the veto layer's read), side by side with the
  committed D1 vs D1ATR per-symbol veto counters. Seed mirrors the runner:
  the last HISTORY_CAP pre-window archived 1h bars.
- matched_exit_receipt.json: trades matched ACROSS the six depth arms
  (D1..D5, DINF) by entry identity (sym, entry_ts, dir, pattern, trig) --
  identical identity = the same candidate fire from the same flat state.
  Identity matching is a superset of strict stream-prefix matching (it also
  captures re-convergence after an occupancy divergence); the convention is
  stated here and in the receipt. Per matched entry: each arm's exit kind,
  exit ts, and P&L (open positions marked from the open_mark price and
  flagged). Aggregates read exits in isolation on the subset CLOSED in all
  six arms; roster scope (parity symbol excluded) throughout.

Run: uv run python -m analysis.paper.t1floor_diagnostics
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

from analysis.paper.engine import _Atr
from analysis.paper.patterns import PatternDetector
from analysis.paper.sweep_tier_a import (
    PARITY_SYMBOL,
    WINDOW_END,
    WINDOW_START,
    _rows,
)

REPO = Path(__file__).resolve().parents[2]
ROUND_DIR = REPO / "analysis" / "paper" / "tier_b_t1floor"
DEPTH_ARMS = ("D1", "D2", "D3", "D4", "D5", "DINF")
VETO_FIELDS = ("candidates", "no_target", "bf_prox", "chop", "both", "t1_floor", "entries")


def _window() -> tuple[int, int]:
    ws = int(datetime.fromisoformat(WINDOW_START).replace(tzinfo=timezone.utc).timestamp())
    we = int(datetime.fromisoformat(WINDOW_END).replace(tzinfo=timezone.utc).timestamp())
    return ws, we


def atr_pct_series(sym: str, bars_dir: str) -> dict:
    """ATR(14, 1H) as % of the completed bar's close, engine-verbatim math.

    Seeds _Atr exactly as the runner does (last HISTORY_CAP pre-window
    archived 1h bars), then walks the in-window 5m stream through the SAME
    hour-key aggregation _Atr.update uses; a 1H bar completes when a later
    hour key arrives, so the window's final partial hour never contributes
    (the engine's completed-bars-only convention)."""
    ws, we = _window()
    pre_1h = [r for r in _rows(sym, "1h", bars_dir) if r[0] < ws]
    atr = _Atr(3600, 14)
    atr.seed(pre_1h[-PatternDetector.HISTORY_CAP :])
    seed_value = atr.value
    seed_close = pre_1h[-1][4] if pre_1h else None
    samples: list[float] = []
    cur_key = None
    cur_h = cur_l = cur_c = None
    for r in _rows(sym, "5m", bars_dir):
        ts = int(r[0])
        if ts < ws or ts >= we:
            continue
        k = ts - ts % 3600
        if cur_key is None or k != cur_key:
            if cur_key is not None:
                atr.push_completed(cur_h, cur_l, cur_c)
                if atr.value is not None and cur_c:
                    samples.append(atr.value / cur_c * 100.0)
            cur_key, cur_h, cur_l, cur_c = k, r[2], r[3], r[4]
        else:
            cur_h = max(cur_h, r[2])
            cur_l = min(cur_l, r[3])
            cur_c = r[4]
    med = None
    if samples:
        s = sorted(samples)
        n = len(s)
        med = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0
    return {
        "seed_atr_pct": (
            round(seed_value / seed_close * 100.0, 4) if seed_value and seed_close else None
        ),
        "n_completed_1h": len(samples),
        "mean_pct": round(sum(samples) / len(samples), 4) if samples else None,
        "median_pct": round(med, 4) if med is not None else None,
        "min_pct": round(min(samples), 4) if samples else None,
        "max_pct": round(max(samples), 4) if samples else None,
    }


def _round_rows() -> list[dict]:
    p = ROUND_DIR / "results_by_symbol.jsonl"
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def atr_context(bars_dir: str) -> dict:
    rows = {(r["arm_id"], r["symbol"]): r for r in _round_rows()}
    symbols = sorted({s for a, s in rows if a == "D1"})
    per_symbol = {}
    for sym in symbols:
        counters = {}
        for arm in ("D1", "D1ATR"):
            vc = rows[(arm, sym)]["veto_counts"]
            c = {k: vc[k] for k in VETO_FIELDS}
            cand = c["candidates"]
            c["chop_rate_pct"] = round(100.0 * c["chop"] / cand, 1) if cand else None
            c["bf_prox_rate_pct"] = round(100.0 * c["bf_prox"] / cand, 1) if cand else None
            c["any_prox_or_chop_rate_pct"] = (
                round(100.0 * (c["chop"] + c["bf_prox"] + c["both"]) / cand, 1) if cand else None
            )
            counters[arm] = c
        per_symbol[sym] = {
            "parity_symbol": sym == PARITY_SYMBOL,
            "atr_pct_of_price": atr_pct_series(sym, bars_dir),
            "veto_counters": counters,
        }
    return per_symbol


def _arm_trades(arm: str) -> dict[tuple, dict]:
    """entry identity -> outcome, roster scope. Every exit/open_mark links to
    its entry; a broken linkage raises (fail-closed)."""
    p = ROUND_DIR / f"events_{arm}.jsonl"
    events = [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    entries = {
        (e["sym"], e["ts"]): e
        for e in events
        if e["action"] == "enter" and e["sym"] != PARITY_SYMBOL
    }
    out: dict[tuple, dict] = {}
    for e in events:
        if e["action"] not in ("exit", "open_mark") or e["sym"] == PARITY_SYMBOL:
            continue
        ee = entries.get((e["sym"], e["entry_ts"]))
        if ee is None:
            raise ValueError(f"{arm}: {e['action']} without entry at {e['sym']} {e['entry_ts']}")
        key = (e["sym"], e["entry_ts"], e["dir"], ee.get("pattern"), ee.get("trig"))
        if e["action"] == "exit":
            out[key] = {
                "kind": e["kind"],
                "exit_ts": e["ts"],
                "pnl_pp": round(e["pnl_pct"], 4),
                "open": False,
            }
        else:
            sign = 1.0 if e["dir"] == "long" else -1.0
            mtm = sign * (e["price"] - e["entry_px"]) / e["entry_px"] * 100.0
            out[key] = {"kind": "open", "exit_ts": None, "pnl_pp": round(mtm, 4), "open": True}
    n_entries = len(entries)
    if n_entries != len(out):
        raise ValueError(f"{arm}: {n_entries} entries but {len(out)} outcomes")
    return out


def matched_exits() -> dict:
    trades = {arm: _arm_trades(arm) for arm in DEPTH_ARMS}
    all_keys = sorted(set().union(*(set(t) for t in trades.values())))
    matrix = {
        f"{a}&{b}": len(set(trades[a]) & set(trades[b])) for a, b in combinations(DEPTH_ARMS, 2)
    }
    per_trade = []
    for key in all_keys:
        sym, entry_ts, direction, pattern, trig = key
        per_trade.append(
            {
                "symbol": sym,
                "entry_ts": entry_ts,
                "dir": direction,
                "pattern": pattern,
                "trig": trig,
                "arms": {a: trades[a].get(key) for a in DEPTH_ARMS if key in trades[a]},
            }
        )
    all6 = [r for r in per_trade if len(r["arms"]) == len(DEPTH_ARMS)]
    all6_closed = [r for r in all6 if not any(o["open"] for o in r["arms"].values())]

    def agg(rows: list[dict]) -> dict:
        out = {}
        for a in DEPTH_ARMS:
            pnls = [r["arms"][a]["pnl_pp"] for r in rows]
            kinds: dict[str, int] = {}
            for r in rows:
                k = r["arms"][a]["kind"]
                kinds[k] = kinds.get(k, 0) + 1
            s = sorted(pnls)
            n = len(s)
            out[a] = {
                "n": n,
                "sum_pnl_pp": round(sum(pnls), 4),
                "mean_pnl_pp": round(sum(pnls) / n, 4) if n else None,
                "median_pnl_pp": (
                    round(s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0, 4)
                    if n
                    else None
                ),
                "win_rate": round(sum(1 for p in pnls if p > 0) / n, 4) if n else None,
                "exit_kinds": dict(sorted(kinds.items())),
            }
        return out

    return {
        "per_arm_trades": {a: len(trades[a]) for a in DEPTH_ARMS},
        "pairwise_matched_counts": matrix,
        "n_matched_all6": len(all6),
        "n_matched_all6_closed_everywhere": len(all6_closed),
        "exits_in_isolation_closed_all6": agg(all6_closed),
        "matched_all6_incl_open": agg(all6),
        "per_trade": per_trade,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="TVB-23 prereg-bound diagnostics (audit F2)")
    ap.add_argument("--bars-dir", default=str(REPO / "analysis" / "paper" / "bars"))
    ap.add_argument("--out-dir", default=str(ROUND_DIR))
    args = ap.parse_args()
    out_dir = Path(args.out_dir)
    stamp = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    src_hashes = {
        f"events_{a}.jsonl": hashlib.sha256(
            (ROUND_DIR / f"events_{a}.jsonl").read_bytes()
        ).hexdigest()[:16]
        for a in DEPTH_ARMS
    }
    src_hashes["results_by_symbol.jsonl"] = hashlib.sha256(
        (ROUND_DIR / "results_by_symbol.jsonl").read_bytes()
    ).hexdigest()[:16]

    atr_receipt = {
        "generated_utc": stamp,
        "purpose": "TVB-23 prereg-bound diagnostic delivered post-hoc (audit F2): "
        "per-symbol ATR% of price beside the D1 vs D1ATR veto counters",
        "conventions": "module docstring analysis/paper/t1floor_diagnostics.py; "
        "ATR math engine-verbatim (_Atr), completed 1H bars only, runner seed slice",
        "source_hashes": src_hashes,
        "per_symbol": atr_context(args.bars_dir),
    }
    (out_dir / "atr_context_receipt.json").write_text(json.dumps(atr_receipt, indent=1) + "\n")

    me = matched_exits()
    me_receipt = {
        "generated_utc": stamp,
        "purpose": "TVB-23 prereg-bound diagnostic delivered post-hoc (audit F2): "
        "matched-entry per-trade exit comparison across D1..D5+DINF "
        "(exits in isolation on the closed-in-all-six subset)",
        "conventions": "module docstring analysis/paper/t1floor_diagnostics.py; "
        "entry identity (sym, entry_ts, dir, pattern, trig); identity matching is a "
        "superset of strict stream-prefix matching; roster scope (parity symbol "
        "excluded); open positions marked from open_mark price, flagged, and "
        "excluded from the exits-in-isolation aggregate",
        "source_hashes": src_hashes,
        **me,
    }
    (out_dir / "matched_exit_receipt.json").write_text(json.dumps(me_receipt, indent=1) + "\n")

    iso = me["exits_in_isolation_closed_all6"]
    print(
        f"atr_context_receipt.json: {len(atr_receipt['per_symbol'])} symbols; "
        f"matched_exit_receipt.json: all6={me['n_matched_all6']} "
        f"closed-everywhere={me['n_matched_all6_closed_everywhere']}"
    )
    for a in DEPTH_ARMS:
        r = iso[a]
        print(
            f"  {a}: n={r['n']} sum={r['sum_pnl_pp']} mean={r['mean_pnl_pp']} "
            f"win={r['win_rate']} kinds={r['exit_kinds']}"
        )


if __name__ == "__main__":
    main()
