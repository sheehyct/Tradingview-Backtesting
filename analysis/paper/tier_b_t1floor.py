"""TVB-23 T1-floor round: floor repair + depth ceiling-map (8 new arms).

LABEL (binding): PRE-COMMITTED LAYER ABLATION plus a LABELED OVERFIT
CEILING-MAP. No deployment claims, no arm/depth promotion. Pre-registration:
docs/experiments/tvb23_t1floor_prereg.md (committed 58f08d7 BEFORE any
floor/ATR/retracement code existed; dated amendments included). Arms,
contrasts, mechanics, and reading rules live there; this module only
executes them.

Mechanics reuse the Tier B path: per symbol, pools warm from pre-window 1h
bars, gates seed from the 1h stream, the pattern detector (and the ATR, for
the ATR arm) seeds from the same pre-window 1h bars, then the window's 5m
bars replay through the extended engine. All arms share the one deployed
warm-key.

Gates (fail-closed, prereg "Execution + provenance"):
- DETERMINISM: the five Tier B arms (A0a/A0b/A1/A2/A3) re-run through
  tier_b._replay_arm itself (the code path that produced the committed
  artifacts); their per-symbol rows must be field-equal to the committed
  analysis/paper/tier_b/results_by_symbol.jsonl rows, modulo NEW
  veto-counter keys that are zero-valued (the TVB-22 no_target_vetoed
  precedent).
- ENTRY-STREAM GATE (prereg ruling 3 as corrected 2026-08-10; docstring
  reconciled 2026-08-15, TVB-23 audit F4): depth-arm event streams are NOT
  identical -- one-position occupancy funnels entries as exits deepen. Per
  symbol, every PAIR of depth-arm streams must be identical up to a first
  divergence that is an EXIT event (a strict prefix passes only if the
  longer stream continues with an exit), with equal symbol sets. The depth
  curve reads exit depth WITH its occupancy consequence, never in
  isolation.
- COUNTER RECONCILIATION: entries = candidates - no_target - (both +
  bf_prox + chop - no_target_vetoed) - t1_floor_only, per (arm, symbol).

Outputs (analysis/paper/tier_b_t1floor/): per-(arm,symbol) rows JSONL,
per-arm rollup JSONL, per-arm event dumps JSONL (entries with ladders +
exits with retracement first-label stamps -- the census tooling's input),
manifest with executed blob hashes, git dirty state INCLUDING the dirty
path list, bar hashes, and every gate result.

Run:
    uv run python -m analysis.paper.tier_b_t1floor
    uv run python -m analysis.paper.tier_b_t1floor --symbols xyz:DRAM --arms D1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from bisect import bisect_left, bisect_right
from copy import deepcopy
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

from analysis.giveback import episode_metrics
from analysis.paper.engine import Twin, TwinConfig
from analysis.paper.sweep_tier_a import (
    PARITY_SYMBOL,
    WEEK_S,
    WINDOW_END,
    WINDOW_START,
    _med,
    _pct,
    _rows,
    _warm_symbol,
)
from analysis.paper.tier_b import ARMS as TIER_B_ARMS
from analysis.paper.tier_b import WARM_KEY, EXIT_KINDS, _replay_arm as _tier_b_replay_arm

REPO = Path(__file__).resolve().parents[2]
OUT_DIR_DEFAULT = REPO / "analysis" / "paper" / "tier_b_t1floor"
TIER_B_BY_SYMBOL = REPO / "analysis" / "paper" / "tier_b" / "results_by_symbol.jsonl"

FLOOR_PCT = 0.25  # prereg ruling 1: fixed, fee-grounded
FIXED_VETOES = {"bf_prox_veto_pct": 1.0, "chop_veto_pct": 2.0}
ATR_VETOES = {"bf_prox_veto_atr": 1.0, "chop_veto_atr": 2.0, "atr_window": 14}
BASE = {
    "entry_mode": "pattern",
    "arm_tf_s": 3600,
    "t1_floor_pct": FLOOR_PCT,
    "retrace_census": True,
}

VETO_KEYS = (
    "candidates",
    "no_target",
    "no_target_vetoed",
    "bf_prox",
    "chop",
    "both",
    "t1_floor",
    "t1_floor_le0",
    "t1_floor_small",
    "t1_floor_only",
    "entries",
)


def _depth_arm(n: int) -> dict:
    return {
        "arm_id": f"D{n}",
        "label": f"floored package, exit rung {n} (fallback shallower)",
        "twin": {**BASE, **FIXED_VETOES, "exit_targets": n, "bf_harvest_exit": False},
    }


NEW_ARMS: list[dict] = [
    *[_depth_arm(n) for n in range(1, 6)],
    {
        "arm_id": "DINF",
        "label": "depth infinity: floored entries, fixed vetoes, C1 exits",
        "twin": {**BASE, **FIXED_VETOES},
    },
    {
        "arm_id": "A1F",
        "label": "floored isolation: floor only, no vetoes, C1 exits",
        "twin": {**BASE},
    },
    {
        "arm_id": "D1ATR",
        "label": "floored package, ATR(14) vetoes 1x/2x, exit rung 1",
        "twin": {**BASE, **ATR_VETOES, "exit_targets": 1, "bf_harvest_exit": False},
    },
]

ENTRY_BOOK_ARMS = ("D1", "D2", "D3", "D4", "D5", "DINF")


def _replay_arm_ext(entry: dict, arm: dict, warm: dict, ws: int, we: int, bars_dir: str) -> dict:
    """tier_b._replay_arm extended for the TVB-23 arms: same metrics path,
    plus the raw event stream (census input), ATR seeding, and open-trade
    retracement stamps. Metric construction mirrors tier_b.py line-for-line;
    the determinism arms run through tier_b's own function instead."""
    coin = entry["name"]
    rows_5m = _rows(coin, "5m", bars_dir)
    ts_5m = [r[0] for r in rows_5m]
    cfg = TwinConfig(symbol=coin, mintick=float(entry["tv_mintick"]), **arm["twin"])
    twin = Twin(cfg)
    twin.pools = deepcopy(warm["pools"])
    twin.gate_open = dict(warm["gate_open"])
    twin.gate_key = dict(warm["gate_key"])
    arm_s = cfg.arm_tf_s
    lo_i = bisect_left(ts_5m, ws - arm_s)
    hi_i = bisect_left(ts_5m, ws)
    seed_win = rows_5m[lo_i:hi_i]
    if seed_win:
        twin.seed_arm(max(r[2] for r in seed_win), min(r[3] for r in seed_win))
    pre_1h = [r for r in _rows(coin, "1h", bars_dir) if r[0] < ws]
    if twin.pattern is not None:
        twin.pattern.seed_history(pre_1h[-twin.pattern.HISTORY_CAP :])
    if twin.atr is not None:
        twin.atr.seed(pre_1h[-twin.pattern.HISTORY_CAP :])

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

    entries_by_ts = {e["ts"]: e for e in events if e["action"] == "enter"}
    exits = [e for e in events if e["action"] == "exit"]
    pnls = [e["pnl_pct"] for e in exits]
    kinds = {k: [e["pnl_pct"] for e in exits if e["kind"] == k] for k in EXIT_KINDS}
    episodes = []
    for e in exits:
        i, j = bisect_left(ts_5m, e["entry_ts"]), bisect_right(ts_5m, e["ts"])
        m = episode_metrics(
            rows_5m[i:j], e["dir"], e["entry_ts"], e["entry_px"], e["ts"], e["price"]
        )
        episodes.append((m["mfe"] * 100, m["mae"] * 100, m["give_back_pp"]))
    open_mtm = None
    open_dir = None
    open_pattern = None
    open_row: dict | None = None
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
        oe = entries_by_ts.get(twin.entry_ts)
        open_pattern = oe.get("pattern") if oe else None
        # census artifact: the open position as a pseudo-event so its
        # retracement stamps and entry linkage survive the run
        open_row = {
            "ts": int(last[0]),
            "sym": coin,
            "action": "open_mark",
            "dir": open_dir,
            "price": last[4],
            "entry_ts": twin.entry_ts,
            "entry_px": twin.entry_px,
            "first_retrace_ts": twin.first_retrace_ts,
            "first_p3_ts": twin.first_p3_ts,
        }
    weekly = {}
    for wnum in range(4):
        a, b = ws + wnum * WEEK_S, ws + (wnum + 1) * WEEK_S
        wp = [e["pnl_pct"] for e in exits if a <= e["entry_ts"] < b]
        weekly[f"W{wnum + 1}"] = {"n": len(wp), "pnl_pp": round(sum(wp), 4)}
    mfes = [x[0] for x in episodes]
    maes = [x[1] for x in episodes]
    gbs = [x[2] for x in episodes]

    census: dict[str, dict] = {}
    boom_split = {
        "boom": {"n": 0, "pnl_pp": 0.0, "wins": 0},
        "plain": {"n": 0, "pnl_pp": 0.0, "wins": 0},
    }
    ladder_depth = {"0": 0, "1": 0, "2plus": 0}
    n_tgt_rung2 = 0
    for ee in entries_by_ts.values():
        lad_n = len(ee.get("ladder") or [])
        ladder_depth["0" if lad_n == 0 else "1" if lad_n == 1 else "2plus"] += 1
        if ee.get("tgt_rung") == 2:
            n_tgt_rung2 += 1
    for x in exits:
        ee = entries_by_ts.get(x["entry_ts"])
        if ee is None:
            continue
        name = ee.get("pattern") or "?"
        c = census.setdefault(name, {"n": 0, "pnl_pp": 0.0, "wins": 0})
        c["n"] += 1
        c["pnl_pp"] = round(c["pnl_pp"] + x["pnl_pct"], 4)
        c["wins"] += 1 if x["pnl_pct"] > 0 else 0
        if name.lstrip("PMG+").startswith("3-2") and not name.lstrip("PMG+").startswith(("3-2-2",)):
            b = boom_split["boom" if ee.get("boom") else "plain"]
            b["n"] += 1
            b["pnl_pp"] = round(b["pnl_pp"] + x["pnl_pct"], 4)
            b["wins"] += 1 if x["pnl_pct"] > 0 else 0

    vc = dict(twin.veto_counts)
    recon_ok = (
        vc["entries"]
        == vc["candidates"]
        - vc["no_target"]
        - (vc["both"] + vc["bf_prox"] + vc["chop"] - vc["no_target_vetoed"])
        - vc["t1_floor_only"]
    )

    rec = {
        "arm_id": arm["arm_id"],
        "symbol": coin,
        "tail": entry["tail"],
        "n_trades": len(exits),
        "sum_pnl_pp": round(sum(pnls), 4),
        "med_pnl_pct": round(_med(pnls), 4) if pnls else None,
        "win_rate": round(sum(1 for p in pnls if p > 0) / len(pnls), 4) if pnls else None,
        "n_bf": len(kinds["bf"]),
        "n_brk": len(kinds["brk"]),
        "n_flip": len(kinds["flip"]),
        "n_tgt": len(kinds["tgt"]),
        "pnl_bf_pp": round(sum(kinds["bf"]), 4),
        "pnl_brk_pp": round(sum(kinds["brk"]), 4),
        "pnl_flip_pp": round(sum(kinds["flip"]), 4),
        "pnl_tgt_pp": round(sum(kinds["tgt"]), 4),
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
        "veto_counts": vc,
        "counter_reconciliation_ok": recon_ok,
        "open_pattern": open_pattern,
        "pattern_census": census,
        "boom_split_3_2": boom_split,
        "ladder_depth_at_entry": ladder_depth,
        "n_tgt_rung2": n_tgt_rung2,
        "open_first_retrace_ts": twin.first_retrace_ts if twin.pos != 0 else None,
        "open_first_p3_ts": twin.first_p3_ts if twin.pos != 0 else None,
    }
    if open_row is not None:
        events = events + [open_row]
    return {"rec": rec, "curve": curve, "episodes": episodes, "pnls": pnls, "events": events}


def _rollup_arm(arm: dict, sym_results: list[dict]) -> dict:
    """Roster rollup (tier_b._rollup_arm with the TVB-23 veto keys)."""
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
    veto = {k: sum(r["veto_counts"][k] for r in recs) for k in VETO_KEYS}
    census: dict[str, dict] = {}
    for r in recs:
        for name, c in (r["pattern_census"] or {}).items():
            t = census.setdefault(name, {"n": 0, "pnl_pp": 0.0, "wins": 0})
            t["n"] += c["n"]
            t["pnl_pp"] = round(t["pnl_pp"] + c["pnl_pp"], 4)
            t["wins"] += c["wins"]
    return {
        "arm_id": arm["arm_id"],
        "label": arm["label"],
        "n_trades": sum(r["n_trades"] for r in recs),
        "realized_pp": round(sum(r["sum_pnl_pp"] for r in recs), 4),
        "open_mtm_pp": round(sum(r["open_mtm_pp"] or 0.0 for r in recs), 4),
        "combined_pp": round(
            sum(r["sum_pnl_pp"] for r in recs) + sum(r["open_mtm_pp"] or 0.0 for r in recs), 4
        ),
        "roster_max_dd_pp": round(dd, 4),
        "n_bf": sum(r["n_bf"] for r in recs),
        "n_brk": sum(r["n_brk"] for r in recs),
        "n_flip": sum(r["n_flip"] for r in recs),
        "n_tgt": sum(r["n_tgt"] for r in recs),
        "pnl_bf_pp": round(sum(r["pnl_bf_pp"] for r in recs), 4),
        "pnl_brk_pp": round(sum(r["pnl_brk_pp"] for r in recs), 4),
        "pnl_flip_pp": round(sum(r["pnl_flip_pp"] for r in recs), 4),
        "pnl_tgt_pp": round(sum(r["pnl_tgt_pp"] for r in recs), 4),
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
        "veto_counts": veto,
        "pattern_census": census,
    }


def _strip_new_zero_keys(ours: dict, committed: dict) -> dict:
    """veto_counts comparison rule: NEW keys are tolerated iff zero-valued."""
    return {k: v for k, v in ours.items() if k in committed or v not in (0, None)}


_MISSING = "(missing)"


def _determinism_check(recs: list[dict]) -> dict:
    """Fail-closed field equality vs the committed Tier B rows (hardened
    2026-08-15, TVB-23 audit F1): every committed (arm, symbol) row must be
    produced exactly once; fields compare over the UNION of key sets, so a
    missing produced field, a missing row, a duplicate, or an unexpected
    extra row all mismatch. veto_counts keeps the declared modulo rule:
    NEW keys are tolerated iff zero-valued."""
    committed: dict[tuple, dict] = {}
    with open(TIER_B_BY_SYMBOL, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            committed[(row["arm_id"], row["symbol"])] = row
    produced: dict[tuple, dict] = {}
    mismatches = []
    for rec in recs:
        key = (rec["arm_id"], rec["symbol"])
        if key in produced:
            mismatches.append({"arm": key[0], "symbol": key[1], "field": "(duplicate replay row)"})
        produced[key] = rec
    for key, base in committed.items():
        rec = produced.get(key)
        if rec is None:
            mismatches.append(
                {"arm": key[0], "symbol": key[1], "field": "(row missing from replay)"}
            )
            continue
        for fld in sorted(set(base) | set(rec)):
            ours = rec.get(fld, _MISSING)
            theirs = base.get(fld, _MISSING)
            if fld == "veto_counts" and isinstance(ours, dict) and isinstance(theirs, dict):
                ours = _strip_new_zero_keys(ours, theirs)
            if ours != theirs:
                mismatches.append(
                    {
                        "arm": key[0],
                        "symbol": key[1],
                        "field": fld,
                        "ours": ours,
                        "committed": theirs,
                    }
                )
    for key in produced:
        if key not in committed:
            mismatches.append({"arm": key[0], "symbol": key[1], "field": "(unexpected replay row)"})
    return {"n_committed_rows": len(committed), "n_compared": len(recs), "mismatches": mismatches}


def _stream_key(e: dict) -> tuple:
    """Comparable event identity for the entry-stream gate (prereg ruling 3,
    2026-08-10 correction): entries by (ts, dir, pattern, trig), exits by
    (ts, dir, kind). open_mark pseudo-events are census artifacts, excluded."""
    if e["action"] == "enter":
        return ("enter", e["ts"], e["dir"], e.get("pattern"), e.get("trig"))
    return ("exit", e["ts"], e["dir"], e["kind"])


def _first_divergence_is_exit(a: list[tuple], b: list[tuple]) -> bool:
    """True iff the streams are equal OR their first differing event is an
    exit on BOTH sides -- entries may only diverge DOWNSTREAM of an
    exit divergence (position-occupancy effect on a one-position book;
    deeper exits hold longer). Hardened 2026-08-15 (TVB-23 audit F1): a
    strict prefix passes ONLY if the longer stream's next event is an exit.
    Two arms flat at the same point face the identical candidate rule, so a
    prefix continuing with an ENTRY (including an empty stream against an
    entry-opening one) is a mechanics violation and fails. Hardened again
    2026-08-16 (TVB-24 audit F3): when BOTH streams have an event at the
    first difference, both must be exits -- up to the divergence the arms
    hold the identical position, so the still-holding side's next event
    cannot legitimately be an entry; an exit opposite an entry can mask a
    deleted or substituted exit. The committed round satisfies the
    stricter rule."""
    for x, y in zip(a, b):
        if x != y:
            return x[0] == "exit" and y[0] == "exit"
    if len(a) == len(b):
        return True
    longer = a if len(a) > len(b) else b
    return longer[min(len(a), len(b))][0] == "exit"


def _entry_stream_gate(
    arm_streams: dict[str, dict[str, list[tuple]]],
    arm_recs: dict[str, dict[str, dict]],
    expected_arms: tuple[str, ...],
    replayed_syms: set[str],
) -> list[dict]:
    """Fail-closed entry-stream gate (hardened 2026-08-16, TVB-24 audit F3).

    (a) exact arm set, BOTH directions (TVB-26 audit LOW-2 hardened the
        reverse side 2026-08-26): a missing expected arm fails instead of
        silently shrinking the pair matrix, and a produced arm outside the
        expected set fails instead of being silently accepted (a selector
        or caller regression could otherwise write an unrequested arm
        under a PASS);
    (b) stream-vs-rec reconciliation per arm+symbol: enter/exit counts in
        the comparison stream must equal the replay rec's n_trades/open_dir.
        This anchors the streams to the authoritative per-symbol rows, so a
        symbol whose events are deleted from EVERY arm still fails. (The
        audit sketched roster-initialized stream maps instead; that would
        NOT catch this mutation, because three roster symbols legitimately
        have zero events in every depth arm -- the chop-veto shut-outs --
        and empty-vs-empty streams compare equal.)
    (c) equal symbol sets across arms, and rec scope == replayed roster;
    (d) all arm pairs, per symbol, under _first_divergence_is_exit.
    """
    fails: list[dict] = []
    missing_arms = sorted(set(expected_arms) - set(arm_streams))
    if missing_arms:
        fails.append({"reason": "expected depth arm missing", "arms": missing_arms})
    unexpected_arms = sorted(set(arm_streams) - set(expected_arms))
    if unexpected_arms:
        fails.append({"reason": "produced arm outside expected set", "arms": unexpected_arms})
    checked = [a for a in expected_arms if a in arm_streams]
    for a in checked:
        recs = arm_recs.get(a, {})
        rec_syms = set(recs)
        stream_syms = set(arm_streams[a])
        if not stream_syms <= rec_syms:
            fails.append(
                {
                    "arm": a,
                    "reason": "stream symbol without a replay rec",
                    "symbol": sorted(stream_syms - rec_syms),
                }
            )
        if rec_syms != replayed_syms:
            fails.append(
                {
                    "arm": a,
                    "reason": "rec symbol scope != replayed roster",
                    "symbol": sorted(rec_syms ^ replayed_syms),
                }
            )
        for sym in sorted(rec_syms & replayed_syms):
            evs = arm_streams[a].get(sym, [])
            n_enter = sum(1 for k in evs if k[0] == "enter")
            n_exit = sum(1 for k in evs if k[0] == "exit")
            want_closed = recs[sym]["n_trades"]
            want_open = 1 if recs[sym].get("open_dir") else 0
            if n_exit != want_closed or n_enter != want_closed + want_open:
                fails.append(
                    {
                        "arm": a,
                        "symbol": sym,
                        "reason": "stream-vs-rec count mismatch",
                        "stream": {"enter": n_enter, "exit": n_exit},
                        "rec": {"n_trades": want_closed, "open": want_open},
                    }
                )
    if len(checked) > 1:
        sym_sets = {a: set(arm_streams[a]) for a in checked}
        for other in checked[1:]:
            if sym_sets[other] != sym_sets[checked[0]]:
                fails.append(
                    {
                        "arms": (checked[0], other),
                        "symbol": sorted(sym_sets[other] ^ sym_sets[checked[0]]),
                        "reason": "symbol set mismatch",
                    }
                )
        for a, b in combinations(checked, 2):
            for sym in sorted(sym_sets[a] | sym_sets[b]):
                if not _first_divergence_is_exit(
                    arm_streams[a].get(sym, []), arm_streams[b].get(sym, [])
                ):
                    fails.append({"arms": (a, b), "symbol": sym})
    return fails


def main() -> None:
    ap = argparse.ArgumentParser(description="TVB-23 T1-floor round (8 new arms + gates)")
    ap.add_argument("--roster", default=str(REPO / "analysis" / "paper" / "roster_week1.json"))
    ap.add_argument("--bars-dir", default=str(REPO / "analysis" / "paper" / "bars"))
    ap.add_argument("--out-dir", default=str(OUT_DIR_DEFAULT))
    ap.add_argument("--arms", help="smoke runs only: comma-separated new-arm subset")
    ap.add_argument("--symbols", help="smoke runs only: comma-separated subset")
    ap.add_argument("--skip-determinism", action="store_true", help="smoke runs only")
    args = ap.parse_args()

    roster = json.loads(Path(args.roster).read_text())
    symbols = roster["symbols"]
    if args.symbols:
        keep = set(args.symbols.split(","))
        symbols = [e for e in symbols if e["name"] in keep]
    new_arms = NEW_ARMS
    if args.arms:
        keep = set(args.arms.split(","))
        new_arms = [a for a in new_arms if a["arm_id"] in keep]
    smoke = bool(args.symbols or args.arms or args.skip_determinism)
    ws = int(datetime.fromisoformat(WINDOW_START).replace(tzinfo=timezone.utc).timestamp())
    we = int(datetime.fromisoformat(WINDOW_END).replace(tzinfo=timezone.utc).timestamp())

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO
    ).stdout.strip()
    dirty_paths = [
        ln
        for ln in subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, cwd=REPO
        ).stdout.splitlines()
        if ln.strip()
    ]
    executed_blobs = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:16]
        for p in (
            Path(__file__).resolve(),
            REPO / "analysis" / "paper" / "tier_b.py",
            REPO / "analysis" / "paper" / "engine.py",
            REPO / "analysis" / "paper" / "patterns.py",
        )
    }
    bar_hashes = {}
    for e in symbols:
        for iv in ("5m", "1h", "1d"):
            p = Path(args.bars_dir) / f"{e['name'].replace(':', '_')}_{iv}.json"
            bar_hashes[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()[:16]

    t0 = time.time()
    warms = {e["name"]: _warm_symbol(e, WARM_KEY, ws, args.bars_dir) for e in symbols}
    print(f"warmed {len(warms)} symbols in {time.time() - t0:.1f}s", flush=True)

    # gate 1: determinism re-runs through tier_b's own replay function
    determinism: dict = {"skipped": smoke and args.skip_determinism}
    if not (smoke and args.skip_determinism):
        det_recs = []
        for arm in TIER_B_ARMS:
            det_recs.extend(
                _tier_b_replay_arm(e, arm, warms[e["name"]], ws, we, args.bars_dir)["rec"]
                for e in symbols
            )
            print(f"determinism {arm['arm_id']} replayed", flush=True)
        determinism = _determinism_check(det_recs)
        if determinism["mismatches"]:
            for m in determinism["mismatches"][:20]:
                print(f"  determinism mismatch: {m}")
            raise SystemExit("DETERMINISM GATE FAILED vs committed Tier B rows")
        print(f"determinism gate PASS ({determinism['n_compared']} rows)", flush=True)

    sym_rows: list[dict] = []
    rollups: list[dict] = []
    arm_streams: dict[str, dict[str, list[tuple]]] = {}
    arm_recs: dict[str, dict[str, dict]] = {}
    entry_counts: dict[str, int] = {}
    recon_fail = []
    for arm in new_arms:
        results = [
            _replay_arm_ext(e, arm, warms[e["name"]], ws, we, args.bars_dir) for e in symbols
        ]
        recs = [r["rec"] for r in results]
        sym_rows.extend(recs)
        rollups.append(_rollup_arm(arm, results))
        streams: dict[str, list[tuple]] = {}
        for r in results:
            for e in r["events"]:
                if e["action"] in ("enter", "exit"):
                    streams.setdefault(e["sym"], []).append(_stream_key(e))
        arm_streams[arm["arm_id"]] = streams
        arm_recs[arm["arm_id"]] = {r["rec"]["symbol"]: r["rec"] for r in results}
        entry_counts[arm["arm_id"]] = sum(
            1 for evs in streams.values() for k in evs if k[0] == "enter"
        )
        recon_fail.extend(
            (r["arm_id"], r["symbol"]) for r in recs if not r["counter_reconciliation_ok"]
        )
        events = sorted(
            (e for r in results for e in r["events"]), key=lambda e: (e["sym"], e["ts"])
        )
        with open(out_dir / f"events_{arm['arm_id']}.jsonl", "w", encoding="utf-8") as f:
            for e in events:
                f.write(json.dumps(e, sort_keys=True) + "\n")
        print(f"{arm['arm_id']} done ({arm['label']})", flush=True)

    if recon_fail:
        raise SystemExit(f"COUNTER RECONCILIATION FAILED: {recon_fail}")

    # gate 2 (prereg ruling 3, 2026-08-10 correction): per symbol, depth-arm
    # event streams must be identical until a first divergence that is an
    # EXIT -- entries diverge only downstream of exit divergences (the
    # one-position occupancy effect). The per-arm entry funnel is reported.
    # Hardened 2026-08-15 (TVB-23 audit F1) + 2026-08-16 (TVB-24 audit F3):
    # exact arm set, stream-vs-rec reconciliation, equal symbol sets, all
    # pairs, both-sides-exit divergence -- see _entry_stream_gate.
    requested = {a["arm_id"] for a in new_arms}
    expected_arms = tuple(a for a in ENTRY_BOOK_ARMS if a in requested or not smoke)
    stream_fail = _entry_stream_gate(
        arm_streams, arm_recs, expected_arms, {e["name"] for e in symbols}
    )
    if stream_fail:
        for m in stream_fail[:10]:
            print(f"  entry-stream gate: {m}")
        raise SystemExit("ENTRY-STREAM GATE FAILED")
    checked = [a for a in expected_arms if a in arm_streams]
    if len(checked) > 1:
        funnel = {a: entry_counts[a] for a in checked}
        print(f"entry-stream gate PASS across {checked}; entry funnel {funnel}", flush=True)

    manifest = {
        "prereg": "docs/experiments/tvb23_t1floor_prereg.md",
        # audit F3 (2026-08-15): hash the BINDING prereg content at run time so
        # a future rerun's manifest proves which correction text governed it
        "prereg_blob_sha256": hashlib.sha256(
            (REPO / "docs" / "experiments" / "tvb23_t1floor_prereg.md").read_bytes()
        ).hexdigest(),
        "label": "PRE-COMMITTED LAYER ABLATION + LABELED OVERFIT CEILING-MAP",
        "git_head": head,
        "git_dirty": bool(dirty_paths),
        "git_dirty_paths": dirty_paths,
        "executed_blobs": executed_blobs,
        "window": {"start": WINDOW_START, "end": WINDOW_END},
        "arms": [{k: a[k] for k in ("arm_id", "label", "twin")} for a in new_arms],
        "determinism_arms": [a["arm_id"] for a in TIER_B_ARMS],
        "warm_key": repr(WARM_KEY),
        "n_symbols": len(symbols),
        "smoke_subset": smoke,
        "bar_hashes": bar_hashes,
        "tier_b_determinism_check": determinism,
        "entry_stream_gate": {
            "rule": "per symbol, ALL depth-arm stream pairs identical until a "
            "first divergence that is an exit; a strict prefix requires the "
            "longer stream's next event to be an exit; symbol sets equal "
            "(prereg ruling 3, 2026-08-10 correction; hardened 2026-08-15 "
            "audit F1)",
            "arms": checked,
            "pass": (not stream_fail) if len(checked) > 1 else None,
            "entry_funnel": {a: entry_counts[a] for a in checked},
            "entries_per_arm": entry_counts,
        },
        "a1f_entries_per_symbol": {
            r["symbol"]: r["veto_counts"]["entries"] for r in sym_rows if r["arm_id"] == "A1F"
        },
        "run_start_utc": datetime.fromtimestamp(t0, tz=timezone.utc).isoformat(timespec="seconds"),
        "run_end_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    suffix = "_smoke" if smoke else ""
    (out_dir / f"manifest{suffix}.json").write_text(json.dumps(manifest, indent=1) + "\n")
    with open(out_dir / f"results_by_symbol{suffix}.jsonl", "w", encoding="utf-8") as f:
        for r in sorted(sym_rows, key=lambda r: (r["arm_id"], r["symbol"])):
            f.write(json.dumps(r, sort_keys=True) + "\n")
    with open(out_dir / f"results_rollup{suffix}.jsonl", "w", encoding="utf-8") as f:
        for r in rollups:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    print(
        f"wrote {len(sym_rows)} symbol rows, {len(rollups)} rollups -> {out_dir}",
        flush=True,
    )


if __name__ == "__main__":
    main()
