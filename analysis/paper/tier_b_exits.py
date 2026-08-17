"""TVB-25 exit-round runner (docs/experiments/tvb25_exit_round_prereg.md
+ the 2026-08-16 amendment; run per the prereg's binding order, step 4).

Ten new arms in two entry families, replayed over TWO windows:

- July window (in-sample comparability): the 10 new arms only; committed
  comparators (tier_b/ and tier_b_t1floor/) are NOT regenerated.
- Fresh window (D13 pin: 2026-08-03 00:00 -> 2026-08-16 00:00 UTC, labeled
  SHORT / sign-indeterminate): the 10 new arms PLUS all 13 existing arms
  rerun as replication (D8).

Families (entry mechanics identical within a family by construction):
- control (1H C1-breakout entries): S0a / S0b / S0c / A0bS, anchored on A0b.
- package (D1 entry config: pattern entries, 0.25% floor, fixed 1%/2%
  vetoes): P1 / P2 / X1 / D1i3 / D1S / PX, anchored on D1.

Arm-id mapping to the prereg names: A0bS = "A0b+stop", D1i3 = "D1+i3",
D1S = "D1+stop"; the rest match.

Gates (all fail-closed, TVB-24-hardened families):
1a. Tier B determinism: the five committed Tier B arms replayed through
    tier_b._replay_arm must be field-equal vs committed rows.
1b. T1-floor determinism: the eight committed TVB-23 arms replayed through
    tier_b_t1floor._replay_arm_ext must be field-equal vs committed rows.
2.  Entry-stream gate per family+window (_entry_stream_gate: exact arm
    set, stream-vs-rec reconciliation, equal symbol sets, all pairs,
    both-sides-exit first divergence). Tranche arms enter the streams with
    their FINAL (position-freeing) exit only -- partial banks do not free
    the one-position book, so the occupancy contract binds the resolving
    event (declared convention).
3.  Tranche reconciliation: per entry, exit fractions (+ open remainder)
    sum to 1.0 exactly (1e-9); non-tranche entries have exactly one
    outcome.

Fees (D7/D10, reporting-only): taker 0.0125%/side; entry fee on the full
position, each exit charged on its exited fraction, a window-end open
fraction carries its entry-fee share only (flagged by n_open).

Run: uv run python -m analysis.paper.tier_b_exits
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
from pathlib import Path

from analysis.giveback import episode_metrics
from analysis.paper.engine import Twin, TwinConfig
from analysis.paper.patterns import PatternDetector
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
from analysis.paper.tier_b import WARM_KEY, _replay_arm as _tier_b_replay_arm
from analysis.paper.tier_b_t1floor import (
    BASE,
    FIXED_VETOES,
    NEW_ARMS as T1FLOOR_ARMS,
    TIER_B_BY_SYMBOL,
    _entry_stream_gate,
    _replay_arm_ext as _t1floor_replay_arm,
)

REPO = Path(__file__).resolve().parents[2]
OUT_DIR_DEFAULT = REPO / "analysis" / "paper" / "tier_b_exits"
T1FLOOR_BY_SYMBOL = REPO / "analysis" / "paper" / "tier_b_t1floor" / "results_by_symbol.jsonl"
T1FLOOR_EVENTS_DIR = REPO / "analysis" / "paper" / "tier_b_t1floor"
PREREG = REPO / "docs" / "experiments" / "tvb25_exit_round_prereg.md"

# D13 pin (amendment): resolved at harvest time, before any run
FRESH_START = "2026-08-03"
FRESH_END = "2026-08-16"

FEE_SIDE_PCT = 0.0125  # D7: taker per side, reporting-only

EXIT_KINDS_V25 = ("bf", "brk", "flip", "tgt", "i3", "stop", "floor", "be", "state")

D1_TWIN = {**BASE, **FIXED_VETOES, "exit_targets": 1, "bf_harvest_exit": False}
PKG = {**BASE, **FIXED_VETOES}
S_BASE = {
    "arm_tf_s": 3600,
    "bf_harvest_exit": False,
    "brk_exit": False,
    "flip_backstop": False,
    "state_stop": True,
}

NEW_ARMS: list[dict] = [
    {
        "arm_id": "S0a",
        "family": "control",
        "label": "ladder bottom: state stop only (ruled 2-against at 1H close)",
        "twin": dict(S_BASE),
    },
    {
        "arm_id": "S0b",
        "family": "control",
        "label": "ladder bottom: state stop + flip backstop",
        "twin": {**S_BASE, "flip_backstop": True},
    },
    {
        "arm_id": "S0c",
        "family": "control",
        "label": "amendment A: state stop + BF harvest touch (BF isolation over S0a)",
        "twin": {**S_BASE, "bf_harvest_exit": True},
    },
    {
        "arm_id": "A0bS",
        "family": "control",
        "label": "A0b+stop: matched control (C1 exits) + ATR stop overlay",
        "twin": {"arm_tf_s": 3600, "stop_mode": "atr"},
    },
    {
        "arm_id": "P1",
        "family": "package",
        "label": "two-piece: 50% at frozen T1, 50% runner to the BF touch",
        "twin": {**PKG, "tranche_profile": "P1"},
    },
    {
        "arm_id": "P2",
        "family": "package",
        "label": "runner profile: skip T1, 40/20/20/10 at T2-T5, armed floor, BE runner",
        "twin": {**PKG, "tranche_profile": "P2"},
    },
    {
        "arm_id": "X1",
        "family": "package",
        "label": "BF overlay at extension: harvest armed once rung 3 reached",
        "twin": {**PKG, "bf_arm_rung": 3},
    },
    {
        "arm_id": "D1i3",
        "family": "package",
        "label": "D1+i3: D1 + intrabar-3 invalidation overlay",
        "twin": {**D1_TWIN, "intrabar3_exit": True},
    },
    {
        "arm_id": "D1S",
        "family": "package",
        "label": "D1+stop: D1 + structural/ATR stop overlay",
        "twin": {**D1_TWIN, "stop_mode": "structural"},
    },
    {
        "arm_id": "PX",
        "family": "package",
        "label": "composite (reading only): P2 + intrabar-3 + structural/ATR stops",
        "twin": {**PKG, "tranche_profile": "P2", "intrabar3_exit": True, "stop_mode": "structural"},
    },
]

A0B_TWIN = {"arm_tf_s": 3600}  # the family anchor, replayed in-memory for July
CONTROL_FAMILY = ("A0b", "S0a", "S0b", "S0c", "A0bS")
PACKAGE_FAMILY = ("D1", "P1", "P2", "X1", "D1i3", "D1S", "PX")

TRANCHE_ARMS = {"P1", "P2", "PX"}

FROZEN_ENTRY_FIELDS = ("price", "ladder", "boom", "pmg", "rev", "star")


def _entry_frac_open(twin: Twin) -> float | None:
    """Remaining open fraction, or None when the twin is flat / whole-pos."""
    if twin.pos == 0:
        return None
    if twin.tranches is None and twin.runner_frac is None:
        return 1.0
    return sum(t["frac"] for t in (twin.tranches or [])) + (twin.runner_frac or 0.0)


def _replay_arm_v25(entry: dict, arm: dict, warm: dict, ws: int, we: int, bars_dir: str) -> dict:
    """t1floor._replay_arm_ext adapted for the TVB-25 arms: fraction-weighted
    P&L (tranche exits carry `frac`), per-ENTRY episode metrics, the new
    exit kinds, exit_counters, and the D10 fee columns. Control arms with
    an ATR stop seed _Atr via the class HISTORY_CAP (no detector exists)."""
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
        twin.atr.seed(pre_1h[-PatternDetector.HISTORY_CAP :])

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
                realized += e.get("frac", 1.0) * e["pnl_pct"]
        events.extend(evs)
        eq = realized
        open_frac = _entry_frac_open(twin)
        if open_frac:
            sign = 1.0 if twin.pos == 1 else -1.0
            eq += open_frac * sign * (r[4] - twin.entry_px) / twin.entry_px * 100.0
        peak = max(peak, eq)
        dd = max(dd, peak - eq)
        curve.append((ts, eq))

    entries_by_ts = {e["ts"]: e for e in events if e["action"] == "enter"}
    exits = [e for e in events if e["action"] == "exit"]
    exits_by_entry: dict[int, list[dict]] = {}
    for e in exits:
        exits_by_entry.setdefault(e["entry_ts"], []).append(e)

    # tranche reconciliation (gate 3): fractions per entry sum to 1.0; the
    # open remainder (if any) accounts for the tail
    open_frac = _entry_frac_open(twin)
    recon_bad = []
    for ets, exs in exits_by_entry.items():
        tot = sum(e.get("frac", 1.0) for e in exs)
        if twin.pos != 0 and twin.entry_ts == ets:
            tot += open_frac or 0.0
        if abs(tot - 1.0) > 1e-9:
            recon_bad.append({"entry_ts": ets, "sum_frac": tot})
        if arm["arm_id"] not in TRANCHE_ARMS and len(exs) != 1:
            recon_bad.append({"entry_ts": ets, "n_outcomes": len(exs)})

    # per-entry trade P&L (fraction-weighted) + episode metrics
    trade_pnls: list[float] = []
    episodes = []
    for ets, exs in sorted(exits_by_entry.items()):
        still_open = twin.pos != 0 and twin.entry_ts == ets
        if still_open:
            continue  # counted with the open position below
        trade_pnls.append(sum(e.get("frac", 1.0) * e["pnl_pct"] for e in exs))
        last = max(exs, key=lambda e: e["ts"])
        if last["ts"] <= ets:
            # zero-duration episode (i3/state degenerate: enter and exit on
            # the same 5m bar). P&L stays in trade_pnls; MFE/MAE/give-back
            # are excluded (episode_metrics requires exit_time > entry_time
            # and a one-bar window has no excursion to measure); the engine
            # exit_counters carry the counted reason. TVB-25 audit F2.
            continue
        i, j = bisect_left(ts_5m, ets), bisect_right(ts_5m, last["ts"])
        m = episode_metrics(
            rows_5m[i:j], last["dir"], ets, last["entry_px"], last["ts"], last["price"]
        )
        episodes.append((m["mfe"] * 100, m["mae"] * 100, m["give_back_pp"]))

    kinds_n = {k: 0 for k in EXIT_KINDS_V25}
    kinds_pp = {k: 0.0 for k in EXIT_KINDS_V25}
    for e in exits:
        kinds_n[e["kind"]] += 1
        kinds_pp[e["kind"]] += e.get("frac", 1.0) * e["pnl_pct"]

    open_mtm = None
    open_dir = None
    open_pattern = None
    open_row: dict | None = None
    if twin.pos != 0 and wi < wj:
        last_bar = rows_5m[wj - 1]
        open_dir = "long" if twin.pos == 1 else "short"
        sign = 1.0 if twin.pos == 1 else -1.0
        open_mtm = (open_frac or 1.0) * sign * (last_bar[4] - twin.entry_px) / twin.entry_px * 100.0
        i = bisect_left(ts_5m, twin.entry_ts)
        if int(last_bar[0]) > twin.entry_ts:
            # same zero-duration guard as the closed path: a position opened
            # on the window's final bar has no excursion window yet
            m = episode_metrics(
                rows_5m[i:wj], open_dir, twin.entry_ts, twin.entry_px, int(last_bar[0]), last_bar[4]
            )
            episodes.append((m["mfe"] * 100, m["mae"] * 100, m["give_back_pp"]))
        oe = entries_by_ts.get(twin.entry_ts)
        open_pattern = oe.get("pattern") if oe else None
        open_row = {
            "ts": int(last_bar[0]),
            "sym": coin,
            "action": "open_mark",
            "dir": open_dir,
            "price": last_bar[4],
            "entry_ts": twin.entry_ts,
            "entry_px": twin.entry_px,
            "first_retrace_ts": twin.first_retrace_ts,
            "first_p3_ts": twin.first_p3_ts,
        }
        if arm["arm_id"] in TRANCHE_ARMS:
            open_row["frac"] = open_frac

    n_entries = len(entries_by_ts)
    n_closed = len(trade_pnls)
    weekly = {}
    for wnum in range(4):
        a, b = ws + wnum * WEEK_S, ws + (wnum + 1) * WEEK_S
        wp = [
            sum(e.get("frac", 1.0) * e["pnl_pct"] for e in exs)
            for ets, exs in exits_by_entry.items()
            if a <= ets < b and not (twin.pos != 0 and twin.entry_ts == ets)
        ]
        weekly[f"W{wnum + 1}"] = {"n": len(wp), "pnl_pp": round(sum(wp), 4)}
    mfes = [x[0] for x in episodes]
    maes = [x[1] for x in episodes]
    gbs = [x[2] for x in episodes]

    census: dict[str, dict] = {}
    for ets, exs in exits_by_entry.items():
        if twin.pos != 0 and twin.entry_ts == ets:
            continue
        ee = entries_by_ts.get(ets)
        name = (ee or {}).get("pattern") or "?"
        c = census.setdefault(name, {"n": 0, "pnl_pp": 0.0, "wins": 0})
        pnl = sum(e.get("frac", 1.0) * e["pnl_pct"] for e in exs)
        c["n"] += 1
        c["pnl_pp"] = round(c["pnl_pp"] + pnl, 4)
        c["wins"] += 1 if pnl > 0 else 0

    # D10 fee columns (reporting-only): entry side on the full position per
    # entry; each exit side on its exited fraction; open entries carry the
    # entry side only (flagged by open_dir)
    exited_fracs = sum(e.get("frac", 1.0) for e in exits)
    fees_pp = round(FEE_SIDE_PCT * (n_entries + exited_fracs), 4)

    vc = dict(twin.veto_counts)
    recon_counter_ok = (
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
        "n_trades": n_closed,
        "n_entries": n_entries,
        "n_exit_events": len(exits),
        "sum_pnl_pp": round(realized, 4),
        "med_pnl_pct": round(_med(trade_pnls), 4) if trade_pnls else None,
        "win_rate": (
            round(sum(1 for p in trade_pnls if p > 0) / n_closed, 4) if n_closed else None
        ),
        "exit_kind_n": kinds_n,
        "exit_kind_pp": {k: round(v, 4) for k, v in kinds_pp.items()},
        "open_dir": open_dir,
        "open_frac": round(open_frac, 4) if (open_dir and open_frac is not None) else None,
        "open_mtm_pp": round(open_mtm, 4) if open_mtm is not None else None,
        "combined_pp": round(realized + (open_mtm or 0.0), 4),
        "fees_pp": fees_pp,
        "net_realized_pp": round(realized - fees_pp, 4),
        "net_combined_pp": round(realized + (open_mtm or 0.0) - fees_pp, 4),
        "max_dd_pp": round(dd, 4),
        "mfe_avg_pct": round(sum(mfes) / len(mfes), 4) if mfes else None,
        "mae_avg_pct": round(sum(maes) / len(maes), 4) if maes else None,
        "gb_avg_pp": round(sum(gbs) / len(gbs), 4) if gbs else None,
        "gb_p90_pp": round(_pct(gbs, 0.9), 4) if gbs else None,
        "worst_mae_pct": round(max(maes), 4) if maes else None,
        "weekly": weekly,
        "warmup_1h_bars": warm["warmup_1h_bars"],
        "warmup_1d_bars": warm["warmup_1d_bars"],
        "n_5m_bars": wj - wi,
        "veto_counts": vc,
        "counter_reconciliation_ok": recon_counter_ok,
        "exit_counters": dict(twin.exit_counters),
        "collision_pairs": dict(twin.collision_pairs),
        "open_pattern": open_pattern,
        "pattern_census": census,
        "tranche_reconciliation_bad": recon_bad,
    }
    if open_row is not None:
        events = events + [open_row]
    return {"rec": rec, "curve": curve, "episodes": episodes, "pnls": trade_pnls, "events": events}


def _rollup_arm(arm: dict, sym_results: list[dict]) -> dict:
    """Roster rollup over the v25 recs (parity symbol excluded)."""
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
    all_pnls = [p for r in rs for p in r["pnls"]]
    eps = [e for r in rs for e in r["episodes"]]
    maes = [e[1] for e in eps]
    mfes = [e[0] for e in eps]
    gbs = [e[2] for e in eps]
    kinds_n = {k: sum(r["exit_kind_n"][k] for r in recs) for k in EXIT_KINDS_V25}
    kinds_pp = {k: round(sum(r["exit_kind_pp"][k] for r in recs), 4) for k in EXIT_KINDS_V25}
    counters = {k: sum(r["exit_counters"][k] for r in recs) for k in recs[0]["exit_counters"]}
    pairs: dict[str, int] = {}
    for r in recs:
        for k, v in r.get("collision_pairs", {}).items():
            pairs[k] = pairs.get(k, 0) + v
    return {
        "arm_id": arm["arm_id"],
        "label": arm["label"],
        "family": arm.get("family"),
        "n_trades": sum(r["n_trades"] for r in recs),
        "n_entries": sum(r["n_entries"] for r in recs),
        "realized_pp": round(sum(r["sum_pnl_pp"] for r in recs), 4),
        "open_mtm_pp": round(sum(r["open_mtm_pp"] or 0.0 for r in recs), 4),
        "combined_pp": round(
            sum(r["sum_pnl_pp"] for r in recs) + sum(r["open_mtm_pp"] or 0.0 for r in recs), 4
        ),
        "fees_pp": round(sum(r["fees_pp"] for r in recs), 4),
        "net_realized_pp": round(sum(r["net_realized_pp"] for r in recs), 4),
        "net_combined_pp": round(sum(r["net_combined_pp"] for r in recs), 4),
        "roster_max_dd_pp": round(dd, 4),
        "exit_kind_n": kinds_n,
        "exit_kind_pp": kinds_pp,
        "exit_counters": counters,
        "collision_pairs": dict(sorted(pairs.items())),
        "n_open": sum(1 for r in recs if r["open_dir"]),
        "med_pnl_pct": round(_med(all_pnls), 4) if all_pnls else None,
        "win_rate": (
            round(sum(1 for p in all_pnls if p > 0) / len(all_pnls), 4) if all_pnls else None
        ),
        "mfe_avg_pct": round(sum(mfes) / len(mfes), 4) if mfes else None,
        "mae_avg_pct": round(sum(maes) / len(maes), 4) if maes else None,
        "gb_avg_pp": round(sum(gbs) / len(gbs), 4) if gbs else None,
        "gb_p90_pp": round(_pct(gbs, 0.9), 4) if gbs else None,
        "worst_mae_pct": round(max(maes), 4) if maes else None,
    }


def _gate_stream_events(events: list[dict], tranche: bool) -> dict[str, list[tuple]]:
    """Per-symbol comparable streams for the entry-stream gate. Tranche arms
    contribute entries + the FINAL (position-freeing) exit of FULLY-RESOLVED
    entries only: a partially-banked entry still occupies the one-position
    book, so it contributes its entry alone until its fractions sum to 1.0
    (the first canonical launch caught exactly this -- an open P1 runner
    whose T1 half had banked counted as an extra stream exit)."""
    from analysis.paper.tier_b_t1floor import _stream_key

    per_sym: dict[str, list[tuple]] = {}
    if not tranche:
        for e in events:
            if e["action"] in ("enter", "exit"):
                per_sym.setdefault(e["sym"], []).append(_stream_key(e))
        return per_sym
    finals: dict[tuple, dict] = {}
    fracs: dict[tuple, float] = {}
    for e in events:
        if e["action"] == "exit":
            k = (e["sym"], e["entry_ts"])
            fracs[k] = fracs.get(k, 0.0) + e.get("frac", 1.0)
            if k not in finals or e["ts"] >= finals[k]["ts"]:
                finals[k] = e
    keep = {id(e) for k, e in finals.items() if fracs[k] >= 1.0 - 1e-9}
    for e in events:
        if e["action"] == "enter" or (e["action"] == "exit" and id(e) in keep):
            per_sym.setdefault(e["sym"], []).append(_stream_key(e))
    return per_sym


def _committed_stream(arm_id: str) -> tuple[dict[str, list[tuple]], dict[str, dict]]:
    """Committed t1floor events + recs for a July family anchor (e.g. D1)."""
    from analysis.paper.tier_b_t1floor import _stream_key

    events = [
        json.loads(ln)
        for ln in (T1FLOOR_EVENTS_DIR / f"events_{arm_id}.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if ln.strip()
    ]
    per_sym: dict[str, list[tuple]] = {}
    for e in events:
        if e["action"] in ("enter", "exit"):
            per_sym.setdefault(e["sym"], []).append(_stream_key(e))
    recs = {}
    with open(T1FLOOR_BY_SYMBOL, encoding="utf-8") as f:
        for ln in f:
            row = json.loads(ln)
            if row["arm_id"] == arm_id:
                recs[row["symbol"]] = row
    return per_sym, recs


def _determinism_vs(recs: list[dict], committed_path: Path, arm_ids: set[str]) -> list[dict]:
    """Field-equality of replayed rows vs a committed by-symbol file
    (union-of-fields both directions; the TVB-24-hardened shape),
    restricted to arm_ids. veto_counts keeps the declared modulo rule
    (tier_b_t1floor._strip_new_zero_keys): keys the committed row predates
    are tolerated iff zero-valued."""
    from analysis.paper.tier_b_t1floor import _strip_new_zero_keys

    committed: dict[tuple, dict] = {}
    with open(committed_path, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if row["arm_id"] in arm_ids:
                committed[(row["arm_id"], row["symbol"])] = row
    produced = {(r["arm_id"], r["symbol"]): r for r in recs}
    mismatches = []
    if len(produced) != len(recs):
        mismatches.append({"field": "(duplicate replay row)"})
    for key, base in committed.items():
        rec = produced.get(key)
        if rec is None:
            mismatches.append({"arm": key[0], "symbol": key[1], "field": "(row missing)"})
            continue
        for fld in sorted(set(base) | set(rec)):
            ours = rec.get(fld, "(missing)")
            theirs = base.get(fld, "(missing)")
            if fld == "veto_counts" and isinstance(ours, dict) and isinstance(theirs, dict):
                ours = _strip_new_zero_keys(ours, theirs)
            if ours != theirs:
                mismatches.append({"arm": key[0], "symbol": key[1], "field": fld})
    for key in produced:
        if key not in committed:
            mismatches.append({"arm": key[0], "symbol": key[1], "field": "(unexpected row)"})
    return mismatches


def _matched_entry(
    arm_events: dict[str, list[dict]], family: tuple[str, ...], pattern_family: bool
) -> dict:
    """Matched-entry diagnostic with the F5 frozen-state contract: identity
    (sym, entry_ts, dir[, pattern, trig]); shared identities must agree on
    the frozen entry fields; per-identity P&L is fraction-weighted."""
    per_arm: dict[str, dict] = {}
    frozen: dict[str, dict] = {}
    for arm_id in family:
        events = arm_events[arm_id]
        entries = {}
        for e in events:
            if e["action"] != "enter" or e["sym"] == PARITY_SYMBOL:
                continue
            k = (
                (e["sym"], e["ts"], e["dir"], e.get("pattern"), e.get("trig"))
                if pattern_family
                else (e["sym"], e["ts"], e["dir"])
            )
            if k in entries:
                raise ValueError(f"{arm_id}: duplicate entry identity {k}")
            entries[k] = e
        outcomes: dict[tuple, dict] = {}
        for e in events:
            if e["action"] not in ("exit", "open_mark") or e["sym"] == PARITY_SYMBOL:
                continue
            ek = (e["sym"], e["entry_ts"])
            ee = next((v for k, v in entries.items() if (k[0], k[1]) == ek), None)
            if ee is None:
                raise ValueError(f"{arm_id}: outcome without entry at {ek}")
            k = (
                (e["sym"], e["entry_ts"], ee["dir"], ee.get("pattern"), ee.get("trig"))
                if pattern_family
                else (e["sym"], e["entry_ts"], ee["dir"])
            )
            o = outcomes.setdefault(k, {"pnl_pp": 0.0, "n_exits": 0, "open": False})
            if e["action"] == "exit":
                o["pnl_pp"] += e.get("frac", 1.0) * e["pnl_pct"]
                o["n_exits"] += 1
            else:
                sign = 1.0 if e["dir"] == "long" else -1.0
                mtm = sign * (e["price"] - e["entry_px"]) / e["entry_px"] * 100.0
                o["pnl_pp"] += e.get("frac", 1.0) * mtm
                o["open"] = True
        per_arm[arm_id] = {k: {**v, "pnl_pp": round(v["pnl_pp"], 4)} for k, v in outcomes.items()}
        frozen[arm_id] = {
            k: {f: ee.get(f) for f in FROZEN_ENTRY_FIELDS} for k, ee in entries.items()
        }
    # F5 contract on shared identities
    n_checked = 0
    from itertools import combinations

    for a, b in combinations(family, 2):
        for k in set(per_arm[a]) & set(per_arm[b]):
            n_checked += 1
            if frozen[a].get(k) != frozen[b].get(k):
                raise ValueError(f"frozen entry state differs for {k}: {a} vs {b}")
    all_shared = set.intersection(*(set(per_arm[a]) for a in family))
    closed_everywhere = [k for k in all_shared if not any(per_arm[a][k]["open"] for a in family)]
    agg = {}
    for a in family:
        pnls = [per_arm[a][k]["pnl_pp"] for k in closed_everywhere]
        agg[a] = {
            "n": len(pnls),
            "sum_pnl_pp": round(sum(pnls), 4),
            "mean_pnl_pp": round(sum(pnls) / len(pnls), 4) if pnls else None,
            "win_rate": round(sum(1 for p in pnls if p > 0) / len(pnls), 4) if pnls else None,
        }
    return {
        "family": list(family),
        "identity": "sym/entry_ts/dir" + ("/pattern/trig" if pattern_family else ""),
        "frozen_fields_bound": list(FROZEN_ENTRY_FIELDS),
        "pairwise_identities_checked": n_checked,
        "per_arm_identities": {a: len(per_arm[a]) for a in family},
        "n_matched_all": len(all_shared),
        "n_matched_all_closed": len(closed_everywhere),
        "matched_closed_aggregate": agg,
    }


def _expected_family_arms(
    fam: tuple[str, ...], requested_ids: set[str], anchor_ids: set[str], smoke: bool
) -> tuple[str, ...]:
    """Declared entry-stream-gate expectation. NEVER derived from produced
    streams (TVB-25 audit F4: passing the produced set as expected_arms
    removes a missing arm from the exact-set check before it runs).
    Canonical runs expect the FULL declared family; smoke runs expect the
    requested arm subset plus the supplied anchors."""
    if not smoke:
        return fam
    return tuple(a for a in fam if a in requested_ids or a in anchor_ids)


def _run_window(
    label: str,
    ws: int,
    we: int,
    arms: list[dict],
    symbols: list[dict],
    bars_dir: str,
    out_dir: Path,
    anchors: dict,
    smoke: bool,
) -> dict:
    """Replay one window: all `arms` + in-memory family anchors; gates."""
    t0 = time.time()
    warms = {e["name"]: _warm_symbol(e, WARM_KEY, ws, bars_dir) for e in symbols}
    print(f"[{label}] warmed {len(warms)} symbols in {time.time() - t0:.1f}s", flush=True)

    sym_rows: list[dict] = []
    rollups: list[dict] = []
    arm_events: dict[str, list[dict]] = {}
    arm_streams: dict[str, dict[str, list[tuple]]] = {}
    arm_recs: dict[str, dict[str, dict]] = {}
    recon_fail: list = []
    for arm in arms:
        results = [_replay_arm_v25(e, arm, warms[e["name"]], ws, we, bars_dir) for e in symbols]
        recs = [r["rec"] for r in results]
        sym_rows.extend(recs)
        rollups.append(_rollup_arm(arm, results))
        events = sorted(
            (e for r in results for e in r["events"]), key=lambda e: (e["sym"], e["ts"])
        )
        arm_events[arm["arm_id"]] = events
        arm_streams[arm["arm_id"]] = _gate_stream_events(events, arm["arm_id"] in TRANCHE_ARMS)
        arm_recs[arm["arm_id"]] = {r["rec"]["symbol"]: r["rec"] for r in results}
        recon_fail.extend(
            (r["arm_id"], r["symbol"], r["tranche_reconciliation_bad"])
            for r in recs
            if r["tranche_reconciliation_bad"]
        )
        with open(out_dir / f"events_{label}_{arm['arm_id']}.jsonl", "w", encoding="utf-8") as f:
            for e in events:
                f.write(json.dumps(e, sort_keys=True) + "\n")
        print(f"[{label}] {arm['arm_id']} done ({arm['label']})", flush=True)

    if recon_fail:
        for r in recon_fail[:10]:
            print(f"  tranche reconciliation: {r}")
        raise SystemExit(f"[{label}] TRANCHE RECONCILIATION FAILED")

    # entry-stream gates per family (anchors joined in, filtered to the
    # replayed symbol scope so smoke subsets stay comparable)
    replayed = {e["name"] for e in symbols}
    requested_ids = {a["arm_id"] for a in arms}
    anchor_ids = {k for k in anchors if not k.endswith("_events")}
    gate_results = {}
    for fam_name, fam, pattern_family in (
        ("control", CONTROL_FAMILY, False),
        ("package", PACKAGE_FAMILY, True),
    ):
        streams = {a: arm_streams[a] for a in fam if a in arm_streams}
        recs_f = {a: arm_recs[a] for a in fam if a in arm_recs}
        for a in fam:
            if a not in streams and a in anchors:
                a_streams, a_recs = anchors[a]
                streams[a] = {s: v for s, v in a_streams.items() if s in replayed}
                recs_f[a] = {s: v for s, v in a_recs.items() if s in replayed}
        expected = _expected_family_arms(fam, requested_ids, anchor_ids, smoke)
        fails = _entry_stream_gate(streams, recs_f, expected, replayed)
        if fails:
            for m in fails[:10]:
                print(f"  [{label}/{fam_name}] entry-stream gate: {m}")
            raise SystemExit(f"[{label}] ENTRY-STREAM GATE FAILED ({fam_name})")
        gate_results[fam_name] = {"arms": list(expected), "pass": True}
        print(f"[{label}] entry-stream gate PASS ({fam_name}: {expected})", flush=True)

    # matched-entry diagnostics with the F5 frozen-state contract
    fam_events = dict(arm_events)
    matched = {}
    for fam_name, fam, pattern_family in (
        ("control", CONTROL_FAMILY, False),
        ("package", PACKAGE_FAMILY, True),
    ):
        evs = {a: fam_events[a] for a in fam if a in fam_events}
        for a in fam:
            if a not in evs and a in anchors:
                evs[a] = anchors[a + "_events"] if (a + "_events") in anchors else None
        evs = {a: v for a, v in evs.items() if v is not None}
        matched[fam_name] = _matched_entry(evs, tuple(evs), pattern_family)

    with open(out_dir / f"results_by_symbol_{label}.jsonl", "w", encoding="utf-8") as f:
        for rec in sym_rows:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
    with open(out_dir / f"results_rollup_{label}.jsonl", "w", encoding="utf-8") as f:
        for r in rollups:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    (out_dir / f"matched_entry_{label}.json").write_text(
        json.dumps(matched, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {"rollups": rollups, "gates": gate_results, "matched": matched}


def main() -> None:
    ap = argparse.ArgumentParser(description="TVB-25 exit round (10 new arms + gates)")
    ap.add_argument("--roster", default=str(REPO / "analysis" / "paper" / "roster_week1.json"))
    ap.add_argument("--bars-dir", default=str(REPO / "analysis" / "paper" / "bars"))
    ap.add_argument("--out-dir", default=str(OUT_DIR_DEFAULT))
    ap.add_argument("--arms", help="smoke runs only: comma-separated new-arm subset")
    ap.add_argument("--symbols", help="smoke runs only: comma-separated subset")
    ap.add_argument("--skip-determinism", action="store_true", help="smoke runs only")
    ap.add_argument("--skip-fresh", action="store_true", help="smoke runs only")
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
    smoke = bool(args.symbols or args.arms or args.skip_determinism or args.skip_fresh)
    if smoke and args.out_dir == str(OUT_DIR_DEFAULT):
        # F4 lesson (TVB-24 audit): a smoke run must never write where the
        # canonical round artifacts live
        args.out_dir = str(OUT_DIR_DEFAULT.parent / "tier_b_exits_smoke")
        print(f"SMOKE SCOPE: artifacts -> {args.out_dir}")
    ws = int(datetime.fromisoformat(WINDOW_START).replace(tzinfo=timezone.utc).timestamp())
    we = int(datetime.fromisoformat(WINDOW_END).replace(tzinfo=timezone.utc).timestamp())
    fs = int(datetime.fromisoformat(FRESH_START).replace(tzinfo=timezone.utc).timestamp())
    fe = int(datetime.fromisoformat(FRESH_END).replace(tzinfo=timezone.utc).timestamp())

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
            REPO / "analysis" / "paper" / "tier_b_t1floor.py",
            REPO / "analysis" / "paper" / "engine.py",
            REPO / "analysis" / "paper" / "patterns.py",
            REPO / "analysis" / "paper" / "sweep_tier_a.py",
        )
    }
    bar_hashes = {}
    for e in symbols:
        for iv in ("5m", "1h", "1d"):
            p = Path(args.bars_dir) / f"{e['name'].replace(':', '_')}_{iv}.json"
            bar_hashes[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()[:16]

    # gates 1a/1b: committed-arm determinism through the extended engine
    determinism: dict = {"skipped": bool(args.skip_determinism)}
    if not args.skip_determinism:
        t0 = time.time()
        warms = {e["name"]: _warm_symbol(e, WARM_KEY, ws, args.bars_dir) for e in symbols}
        tb_recs = []
        for arm in TIER_B_ARMS:
            tb_recs.extend(
                _tier_b_replay_arm(e, arm, warms[e["name"]], ws, we, args.bars_dir)["rec"]
                for e in symbols
            )
        mis_a = _determinism_vs(tb_recs, TIER_B_BY_SYMBOL, {a["arm_id"] for a in TIER_B_ARMS})
        t1_recs = []
        for arm in T1FLOOR_ARMS:
            t1_recs.extend(
                _t1floor_replay_arm(e, arm, warms[e["name"]], ws, we, args.bars_dir)["rec"]
                for e in symbols
            )
        mis_b = _determinism_vs(t1_recs, T1FLOOR_BY_SYMBOL, {a["arm_id"] for a in T1FLOOR_ARMS})
        determinism = {
            "tier_b_rows": len(tb_recs),
            "t1floor_rows": len(t1_recs),
            "mismatches": mis_a + mis_b,
            "elapsed_s": round(time.time() - t0, 1),
        }
        if determinism["mismatches"]:
            for m in determinism["mismatches"][:20]:
                print(f"  determinism mismatch: {m}")
            raise SystemExit("DETERMINISM GATES FAILED vs committed rows")
        print(
            f"determinism gates PASS ({len(tb_recs)} tier_b + {len(t1_recs)} t1floor rows, "
            f"{determinism['elapsed_s']}s)",
            flush=True,
        )

    # July window: the new arms + in-memory family anchors (committed D1
    # stream; A0b replayed in-memory -- never rewritten)
    july_warms = {e["name"]: _warm_symbol(e, WARM_KEY, ws, args.bars_dir) for e in symbols}
    a0b_arm = {"arm_id": "A0b", "family": "control", "label": "anchor", "twin": dict(A0B_TWIN)}
    a0b_results = [
        _replay_arm_v25(e, a0b_arm, july_warms[e["name"]], ws, we, args.bars_dir) for e in symbols
    ]
    anchors_july = {
        "A0b": (
            _gate_stream_events([e for r in a0b_results for e in r["events"]], False),
            {r["rec"]["symbol"]: r["rec"] for r in a0b_results},
        ),
        "A0b_events": sorted(
            (e for r in a0b_results for e in r["events"]), key=lambda e: (e["sym"], e["ts"])
        ),
    }
    d1_stream, d1_recs = _committed_stream("D1")
    anchors_july["D1"] = (d1_stream, d1_recs)
    anchors_july["D1_events"] = [
        json.loads(ln)
        for ln in (T1FLOOR_EVENTS_DIR / "events_D1.jsonl").read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    july = _run_window(
        "july", ws, we, new_arms, symbols, args.bars_dir, out_dir, anchors_july, smoke
    )

    # fresh window (D8): all arms -- 13 existing rerun + the new arms
    fresh = None
    if not args.skip_fresh:
        existing = [
            {**a, "family": "control" if a["arm_id"] in ("A0a", "A0b") else "existing"}
            for a in TIER_B_ARMS
        ] + [
            {**a, "family": "package" if a["arm_id"] == "D1" else "existing"} for a in T1FLOOR_ARMS
        ]
        fresh = _run_window(
            "fresh", fs, fe, existing + new_arms, symbols, args.bars_dir, out_dir, {}, smoke
        )

    manifest = {
        "prereg": "docs/experiments/tvb25_exit_round_prereg.md",
        "prereg_blob_sha256": hashlib.sha256(PREREG.read_bytes()).hexdigest(),
        "label": "PRE-COMMITTED LAYER ABLATION + LADDER-BOTTOM VALIDATION + FRESH REPLICATION",
        "git_head": head,
        "git_dirty": bool(dirty_paths),
        "git_dirty_paths": dirty_paths,
        "executed_blobs": executed_blobs,
        "bar_hashes": bar_hashes,
        "windows": {
            "july": {"start": WINDOW_START, "end": WINDOW_END},
            "fresh": {
                "start": FRESH_START,
                "end": FRESH_END,
                "label": "SHORT / sign-indeterminate (D13 pin)",
            },
        },
        "fee_side_pct": FEE_SIDE_PCT,
        "arms": [{k: a[k] for k in ("arm_id", "family", "label", "twin")} for a in NEW_ARMS],
        "smoke": smoke,
        "determinism": determinism,
        "gates": {"july": july["gates"], "fresh": fresh["gates"] if fresh else None},
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"manifest written -> {out_dir / 'manifest.json'}")
    for label, res in (("july", july), ("fresh", fresh)):
        if res is None:
            continue
        print(f"--- {label} rollups (gross realized / net / combined) ---")
        for r in res["rollups"]:
            print(
                f"  {r['arm_id']:6} n={r['n_trades']:3} realized={r['realized_pp']:+9.4f} "
                f"net={r['net_realized_pp']:+9.4f} combined={r['combined_pp']:+9.4f} "
                f"dd={r['roster_max_dd_pp']:7.4f} collisions={r['exit_counters']['collision_bars']}"
            )


if __name__ == "__main__":
    main()
