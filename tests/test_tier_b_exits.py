"""TVB-25 runner regression tests: arm table integrity, gate-stream
collapsing for tranche arms, the determinism comparison, and the
matched-entry frozen-state contract (F5 carried forward). TVB-26 audit
fold: the gate expectation is declaration-only (F4), the veto_counts
modulo rule is pinned (no wider), and zero-duration degenerate episodes
survive the runner end-to-end (F2)."""

from __future__ import annotations

import json

import pytest

from analysis.paper.engine import TwinConfig
from analysis.paper.sweep_tier_a import _warm_symbol
from analysis.paper.tier_b import WARM_KEY
from analysis.paper.tier_b_exits import (
    CONTROL_FAMILY,
    NEW_ARMS,
    PACKAGE_FAMILY,
    TRANCHE_ARMS,
    _determinism_vs,
    _entry_stream_gate,
    _expected_family_arms,
    _gate_stream_events,
    _matched_entry,
    _replay_arm_v25,
)


def test_arm_table_shape_and_constructibility():
    ids = [a["arm_id"] for a in NEW_ARMS]
    assert len(ids) == 10 and len(set(ids)) == 10
    for a in NEW_ARMS:
        cfg = TwinConfig(symbol="SYN", mintick=0.01, **a["twin"])  # must validate
        assert a["family"] in ("control", "package")
        if a["arm_id"] in TRANCHE_ARMS - {"PX"}:
            assert cfg.tranche_profile == a["arm_id"]
    assert set(CONTROL_FAMILY) == {"A0b", "S0a", "S0b", "S0c", "A0bS"}
    assert set(PACKAGE_FAMILY) == {"D1", "P1", "P2", "X1", "D1i3", "D1S", "PX"}


def test_s_family_exit_wiring():
    by_id = {a["arm_id"]: a["twin"] for a in NEW_ARMS}
    assert by_id["S0a"] == {
        "arm_tf_s": 3600,
        "bf_harvest_exit": False,
        "brk_exit": False,
        "flip_backstop": False,
        "state_stop": True,
    }
    assert by_id["S0b"]["flip_backstop"] is True and by_id["S0b"]["bf_harvest_exit"] is False
    assert by_id["S0c"]["bf_harvest_exit"] is True and by_id["S0c"]["flip_backstop"] is False
    assert by_id["A0bS"] == {"arm_tf_s": 3600, "stop_mode": "atr"}


def _ev(action, sym, ts, entry_ts=None, kind=None, frac=None):
    e = {"action": action, "sym": sym, "ts": ts, "dir": "long"}
    if action == "enter":
        e.update(pattern="2-2u", trig=1.0)
    else:
        e.update(entry_ts=entry_ts, kind=kind, price=1.0, pnl_pct=0.5, entry_px=1.0)
        if frac is not None:
            e["frac"] = frac
    return e


def test_gate_stream_collapses_tranche_exits_to_final():
    events = [
        _ev("enter", "xyz:T", 100),
        _ev("exit", "xyz:T", 200, entry_ts=100, kind="tgt", frac=0.4),
        _ev("exit", "xyz:T", 300, entry_ts=100, kind="floor", frac=0.5),
        _ev("exit", "xyz:T", 400, entry_ts=100, kind="bf", frac=0.1),
    ]
    stream = _gate_stream_events(events, tranche=True)
    kinds = [k[0] for k in stream["xyz:T"]]
    assert kinds == ["enter", "exit"]
    assert stream["xyz:T"][1][1] == 400  # only the position-freeing exit
    full = _gate_stream_events(events, tranche=False)
    assert [k[0] for k in full["xyz:T"]] == ["enter", "exit", "exit", "exit"]


def test_gate_stream_partial_open_entry_contributes_no_exit():
    # an open runner whose T1 half banked must NOT count as a stream exit
    events = [
        _ev("enter", "xyz:T", 100),
        _ev("exit", "xyz:T", 200, entry_ts=100, kind="tgt", frac=0.5),
    ]
    stream = _gate_stream_events(events, tranche=True)
    assert [k[0] for k in stream["xyz:T"]] == ["enter"]


def _entry_full(sym, ts, price=10.0, ladder=(11.0,)):
    return {
        "action": "enter",
        "sym": sym,
        "ts": ts,
        "dir": "long",
        "pattern": "2-2u",
        "trig": 9.9,  # constant: the identity must stay matched while the
        "price": price,  # frozen state (price) is what mutates
        "ladder": list(ladder),
        "boom": False,
        "pmg": False,
        "rev": True,
        "star": False,
    }


def test_matched_entry_frozen_state_contract():
    ok_a = [_entry_full("xyz:T", 100), _ev("exit", "xyz:T", 200, entry_ts=100, kind="tgt")]
    ok_b = [_entry_full("xyz:T", 100), _ev("exit", "xyz:T", 300, entry_ts=100, kind="bf")]
    out = _matched_entry({"A": ok_a, "B": ok_b}, ("A", "B"), pattern_family=True)
    assert out["n_matched_all"] == 1 and out["n_matched_all_closed"] == 1
    bad_b = [
        _entry_full("xyz:T", 100, price=10.5),  # frozen price differs
        _ev("exit", "xyz:T", 300, entry_ts=100, kind="bf"),
    ]
    with pytest.raises(ValueError, match="frozen entry state"):
        _matched_entry({"A": ok_a, "B": bad_b}, ("A", "B"), pattern_family=True)


def test_matched_entry_duplicate_identity_raises():
    dup = [
        _entry_full("xyz:T", 100),
        _entry_full("xyz:T", 100),
        _ev("exit", "xyz:T", 200, entry_ts=100, kind="tgt"),
    ]
    with pytest.raises(ValueError, match="duplicate entry identity"):
        _matched_entry({"A": dup}, ("A",), pattern_family=True)


# --- TVB-26 audit fold -------------------------------------------------------


def test_expected_family_arms_is_declaration_only():
    # F4: canonical expectation = the FULL declared family, independent of
    # anything produced; smoke expectation = requested subset + anchors
    assert _expected_family_arms(CONTROL_FAMILY, {"S0a"}, set(), smoke=False) == CONTROL_FAMILY
    assert _expected_family_arms(PACKAGE_FAMILY, {"P1"}, {"D1"}, smoke=True) == ("D1", "P1")
    assert _expected_family_arms(CONTROL_FAMILY, set(), set(), smoke=True) == ()


def test_gate_fails_on_missing_produced_arm_canonical():
    # caller-boundary mutation (audit F4): one produced arm removed; with
    # the declared-family expectation the exact-set check must flag it
    # instead of the expectation silently shrinking around the hole
    present = {a: {} for a in CONTROL_FAMILY if a != "S0c"}
    fails = _entry_stream_gate(present, {a: {} for a in present}, CONTROL_FAMILY, set())
    assert any(
        f.get("reason") == "expected depth arm missing" and f.get("arms") == ["S0c"] for f in fails
    )


def test_gate_fails_on_extra_produced_arm_canonical_and_smoke():
    # TVB-26 audit LOW-2 mirror mutation: an UNREQUESTED produced arm must
    # fail the exact-set check under both expectation shapes instead of
    # riding along under a PASS
    present = {a: {} for a in CONTROL_FAMILY}
    present["P2"] = {}
    fails = _entry_stream_gate(present, {a: {} for a in present}, CONTROL_FAMILY, set())
    assert any(
        f.get("reason") == "produced arm outside expected set" and f.get("arms") == ["P2"]
        for f in fails
    )
    smoke_expected = _expected_family_arms(PACKAGE_FAMILY, {"P1"}, {"D1"}, smoke=True)
    present = {"D1": {}, "P1": {}, "P2": {}}
    fails = _entry_stream_gate(present, {a: {} for a in present}, smoke_expected, set())
    assert any(
        f.get("reason") == "produced arm outside expected set" and f.get("arms") == ["P2"]
        for f in fails
    )


def test_determinism_vs_modulo_rule_exact_scope(tmp_path):
    # the 5796da2 correction is EXACTLY the declared TVB-23 rule, no wider:
    # new keys tolerated iff zero-valued, in veto_counts ONLY
    row = {
        "arm_id": "A2",
        "symbol": "xyz:T",
        "n_trades": 1,
        "veto_counts": {"chop": 2},
        "pattern_census": {"2-2u": {"n": 1}},
    }
    committed = tmp_path / "by_symbol.jsonl"
    committed.write_text(json.dumps(row) + "\n", encoding="utf-8")
    ours = {**row, "veto_counts": {"chop": 2, "t1_floor": 0}}
    assert _determinism_vs([ours], committed, {"A2"}) == []  # new zero key: ok
    ours = {**row, "veto_counts": {"chop": 2, "t1_floor": 3}}
    assert _determinism_vs([ours], committed, {"A2"})  # new NONZERO key: fail
    ours = {**row, "veto_counts": {"chop": 1}}
    assert _determinism_vs([ours], committed, {"A2"})  # changed value: fail
    ours = {**row, "pattern_census": {"2-2u": {"n": 1}, "x": 0}}
    assert _determinism_vs([ours], committed, {"A2"})  # other fields: strict


def test_replay_arm_v25_survives_zero_duration_episode(tmp_path):
    # F2 end-to-end: a D14 state-degenerate entry (enter + exit on the same
    # 5m bar) must flow through the runner's episode contracts instead of
    # aborting in episode_metrics; P&L retained, MFE/MAE excluded
    sym = "xyz:ZDT"
    stem = sym.replace(":", "_")
    bars_5m = [
        [0, 100.0, 101.0, 99.5, 100.5],
        [3300, 100.5, 100.8, 100.0, 100.2],
        [3600, 100.5, 100.9, 100.1, 100.6],
        [6900, 100.9, 102.0, 99.0, 101.5],  # hour-completing: BOTH sides break
        [7200, 101.5, 101.6, 101.4, 101.5],  # sacrificial forming bar
    ]
    bars_1h = [[0, 100.0, 101.0, 99.5, 100.5], [3600, 100.5, 102.0, 99.0, 101.5]]
    bars_1d = [[0, 100.0, 101.0, 99.5, 100.5], [86400, 101.5, 101.6, 101.4, 101.5]]
    for iv, bars in (("5m", bars_5m), ("1h", bars_1h), ("1d", bars_1d)):
        (tmp_path / f"{stem}_{iv}.json").write_text(json.dumps({"bars": bars}), encoding="utf-8")
    entry = {"name": sym, "tv_mintick": 0.01, "tail": "zdt"}
    warm = _warm_symbol(entry, WARM_KEY, 3600, str(tmp_path))
    arm = next(a for a in NEW_ARMS if a["arm_id"] == "S0a")
    res = _replay_arm_v25(entry, arm, warm, 3600, 7200, str(tmp_path))
    rec = res["rec"]
    assert rec["n_entries"] == 1 and rec["n_trades"] == 1
    assert rec["exit_kind_n"]["state"] == 1
    assert rec["exit_counters"]["state_degenerate"] == 1
    assert rec["mfe_avg_pct"] is None and rec["mae_avg_pct"] is None  # excluded
    assert rec["sum_pnl_pp"] == pytest.approx(
        (101.5 - 101.01) / 101.01 * 100.0, abs=1e-6
    )  # P&L retained
