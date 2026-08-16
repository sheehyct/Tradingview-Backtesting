"""TVB-23 audit F2 diagnostics: conventions pinned against committed artifacts.

The two prereg-bound diagnostics delivered post-hoc must stay reproducible
from the committed round artifacts: the ATR%-of-price walk must equal an
engine-driven _Atr.update replay bar for bar, and the matched-exit receipt's
headline aggregates are pinned to the committed values so a regression in
either module or the dumps is visible.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from analysis.paper.engine import _Atr
from analysis.paper.patterns import PatternDetector
from analysis.paper.sweep_tier_a import WINDOW_END, WINDOW_START, _rows
from analysis.paper.t1floor_diagnostics import (
    DEPTH_ARMS,
    ROUND_DIR,
    atr_pct_series,
    matched_exits,
)

REPO = Path(__file__).resolve().parents[1]
BARS_DIR = str(REPO / "analysis" / "paper" / "bars")


def _update_driven_samples(sym: str) -> list[float]:
    """Reference walk through _Atr.update itself (the engine's own path)."""
    ws = int(datetime.fromisoformat(WINDOW_START).replace(tzinfo=timezone.utc).timestamp())
    we = int(datetime.fromisoformat(WINDOW_END).replace(tzinfo=timezone.utc).timestamp())
    pre_1h = [r for r in _rows(sym, "1h", BARS_DIR) if r[0] < ws]
    atr = _Atr(3600, 14)
    atr.seed(pre_1h[-PatternDetector.HISTORY_CAP :])
    samples: list[float] = []
    prev_key = None
    prev_c = None
    for r in _rows(sym, "5m", BARS_DIR):
        ts = int(r[0])
        if ts < ws or ts >= we:
            continue
        k = ts - ts % 3600
        if prev_key is not None and k != prev_key:
            # update() completes the prior hour on rollover; sample after it
            atr.update(ts, r[2], r[3], r[4])
            if atr.value is not None and prev_c:
                samples.append(atr.value / prev_c * 100.0)
        else:
            atr.update(ts, r[2], r[3], r[4])
        if k != prev_key:
            prev_key = k
        prev_c = r[4]
    return samples


def test_atr_walk_matches_engine_update_path():
    got = atr_pct_series("xyz:GOLD", BARS_DIR)
    ref = _update_driven_samples("xyz:GOLD")
    assert got["n_completed_1h"] == len(ref)
    assert got["mean_pct"] == round(sum(ref) / len(ref), 4)


def test_atr_pct_pins():
    gold = atr_pct_series("xyz:GOLD", BARS_DIR)
    assert gold["n_completed_1h"] == 671
    assert gold["mean_pct"] == 0.2601
    dram = atr_pct_series("xyz:DRAM", BARS_DIR)
    assert dram["mean_pct"] == 1.5016


def test_matched_exits_pins_and_invariants():
    me = matched_exits()
    assert me["per_arm_trades"]["D1"] == 102
    assert me["n_matched_all6"] == 41
    assert me["n_matched_all6_closed_everywhere"] == 37
    iso = me["exits_in_isolation_closed_all6"]
    # exits in isolation: realized P&L rises monotonically with depth on the
    # common closed book (the whole-arm shallow-top is an occupancy effect)
    sums = [iso[a]["sum_pnl_pp"] for a in ("D1", "D2", "D3", "D4", "D5")]
    assert sums == sorted(sums)
    assert iso["D1"]["sum_pnl_pp"] == 38.3996
    assert iso["D5"]["sum_pnl_pp"] == 66.2171
    assert iso["DINF"]["sum_pnl_pp"] == 55.0068
    # DINF's 37 closed trades ARE the matched set: its matched sum equals its
    # committed whole-arm realized_pp (modulo per-trade rounding)
    rollup = {
        json.loads(ln)["arm_id"]: json.loads(ln)
        for ln in (ROUND_DIR / "results_rollup.jsonl").read_text().splitlines()
        if ln.strip()
    }
    assert abs(iso["DINF"]["sum_pnl_pp"] - rollup["DINF"]["realized_pp"]) < 0.001
    for row in me["per_trade"]:
        if len(row["arms"]) == len(DEPTH_ARMS):
            kinds = {o["kind"] for o in row["arms"].values()}
            assert kinds  # every matched arm has an outcome
            assert all(o["pnl_pp"] is not None for o in row["arms"].values())


def test_committed_receipts_match_recomputation():
    atr_receipt = json.loads((ROUND_DIR / "atr_context_receipt.json").read_text())
    fresh = atr_pct_series("xyz:AAPL", BARS_DIR)
    assert atr_receipt["per_symbol"]["xyz:AAPL"]["atr_pct_of_price"] == fresh
    me_receipt = json.loads((ROUND_DIR / "matched_exit_receipt.json").read_text())
    me = matched_exits()
    assert me_receipt["exits_in_isolation_closed_all6"] == me["exits_in_isolation_closed_all6"]
    assert me_receipt["n_matched_all6"] == me["n_matched_all6"]


# --- TVB-24 audit F5: the matched identity binds frozen entry state ---------

import pytest  # noqa: E402

from analysis.paper import t1floor_diagnostics as t1d  # noqa: E402

SYN_ENTRY = {
    "action": "enter",
    "sym": "xyz:TEST",
    "ts": 1000,
    "dir": "long",
    "pattern": "2-2u",
    "trig": 10.0,
    "price": 10.01,
    "ladder": [10.5, 11.0],
    "boom": 0,
    "pmg": 0,
    "rev": 0,
    "star": 0,
    "tgt_rung": 1,
}
SYN_EXIT = {
    "action": "exit",
    "sym": "xyz:TEST",
    "ts": 2000,
    "entry_ts": 1000,
    "dir": "long",
    "kind": "tgt",
    "pnl_pct": 1.5,
}


def _syn_round(tmp_path, per_arm_mutator=None):
    """One identity, closed, in every depth arm; mutator edits one arm."""
    for arm in t1d.DEPTH_ARMS:
        entry = json.loads(json.dumps(SYN_ENTRY))
        events = [entry, dict(SYN_EXIT)]
        if per_arm_mutator:
            per_arm_mutator(arm, entry, events)
        p = tmp_path / f"events_{arm}.jsonl"
        p.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")


def test_matched_state_committed_binding_reported():
    st = matched_exits()["matched_entry_state"]
    assert st["fields_bound"] == list(t1d.FROZEN_ENTRY_FIELDS)
    assert st["mismatches"] == 0
    assert st["pairwise_identities_checked"] == 942  # committed shared identities


def test_synthetic_round_passes(tmp_path, monkeypatch):
    _syn_round(tmp_path)
    monkeypatch.setattr(t1d, "ROUND_DIR", tmp_path)
    me = t1d.matched_exits()
    assert me["n_matched_all6"] == 1
    assert me["n_matched_all6_closed_everywhere"] == 1


@pytest.mark.parametrize("field, value", [("price", 10.11), ("ladder", [10.6, 11.0])])
def test_matched_frozen_state_mutation_raises(tmp_path, monkeypatch, field, value):
    _syn_round(
        tmp_path, lambda arm, entry, evs: entry.update({field: value}) if arm == "D3" else None
    )
    monkeypatch.setattr(t1d, "ROUND_DIR", tmp_path)
    with pytest.raises(ValueError, match="frozen entry state"):
        t1d.matched_exits()


def test_tgt_rung_difference_is_tolerated(tmp_path, monkeypatch):
    # arm-dependent by construction: each depth arm stamps its own target
    # config; a tgt_rung difference must NOT fail the matched contract
    _syn_round(
        tmp_path, lambda arm, entry, evs: entry.update({"tgt_rung": 5}) if arm == "D5" else None
    )
    monkeypatch.setattr(t1d, "ROUND_DIR", tmp_path)
    assert t1d.matched_exits()["n_matched_all6"] == 1


def test_duplicate_raw_entry_identity_raises(tmp_path, monkeypatch):
    def dup_entry(arm, entry, events):
        if arm == "D1":
            events.append(json.loads(json.dumps(SYN_ENTRY)))

    _syn_round(tmp_path, dup_entry)
    monkeypatch.setattr(t1d, "ROUND_DIR", tmp_path)
    with pytest.raises(ValueError, match="duplicate raw entry"):
        t1d.matched_exits()


def test_duplicate_outcome_raises(tmp_path, monkeypatch):
    def dup_exit(arm, entry, events):
        if arm == "D1":
            events.append(dict(SYN_EXIT))

    _syn_round(tmp_path, dup_exit)
    monkeypatch.setattr(t1d, "ROUND_DIR", tmp_path)
    with pytest.raises(ValueError, match="duplicate outcome"):
        t1d.matched_exits()
