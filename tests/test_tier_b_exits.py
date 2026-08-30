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
    EXIT_KINDS_V25,
    FEE_SIDE_PCT,
    NEW_ARMS,
    PACKAGE_FAMILY,
    TRANCHE_ARMS,
    _determinism_vs,
    _entry_stream_gate,
    _expected_family_arms,
    _gate_stream_events,
    _matched_entry,
    _net_fields,
    _replay_arm_v25,
    _rollup_arm,
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


def _fee_rec(sym: str, fee_sides: float) -> dict:
    """Minimal per-symbol result shaped like _replay_arm_v25 output, with
    only the fields _rollup_arm reads."""
    fees_pp = round(FEE_SIDE_PCT * fee_sides, 4)
    rec = {
        "arm_id": "P1",
        "symbol": sym,
        "n_trades": 1,
        "n_entries": 1,
        "sum_pnl_pp": 1.0,
        "open_mtm_pp": 0.0,
        "open_dir": None,
        "fees_pp": fees_pp,
        "fee_sides": fee_sides,
        "net_realized_pp": round(1.0 - fees_pp, 4),
        "net_combined_pp": round(1.0 - fees_pp, 4),
        "exit_kind_n": {k: 0 for k in EXIT_KINDS_V25},
        "exit_kind_pp": {k: 0.0 for k in EXIT_KINDS_V25},
        "exit_counters": {"collision_bars": 0},
        "collision_pairs": {},
        "collision_receipts": [],
    }
    return {"rec": rec, "curve": [(0, 1.0)], "episodes": [], "pnls": [1.0]}


def test_rollup_net_equals_gross_minus_round_once_roster_fee():
    # TVB-28 audit LOW-1: three symbols whose per-symbol display fees round
    # UP (0.0004 each at fee_sides=0.03) while the round-once roster fee is
    # 0.0011 -- summing per-symbol nets books 2.9988; the correct roster net
    # (gross minus the single rounded roster fee) is 2.9989. The rollup must
    # also expose the roster's unrounded side count.
    arm = {"arm_id": "P1", "label": "x", "family": "package"}
    roll = _rollup_arm(arm, [_fee_rec(f"S{i}", 0.03) for i in range(3)])
    assert roll["fees_pp"] == 0.0011
    assert roll["fee_sides"] == 0.09
    assert roll["realized_pp"] == 3.0
    assert roll["net_realized_pp"] == round(roll["realized_pp"] - roll["fees_pp"], 4) == 2.9989
    assert roll["net_combined_pp"] == round(roll["combined_pp"] - roll["fees_pp"], 4) == 2.9989


def test_rollup_aggregates_full_precision_before_rounding():
    # TVB-29 audit LOW-1: per-symbol display fields are rounded to 4dp; the
    # roster must aggregate the FULL-PRECISION values and round ONCE (D10).
    # Three symbols at 0.12344pp realized: summing the rounded displays gives
    # 0.3702; the full-precision sum 0.37032 rounds to 0.3703. Whole-number
    # inputs (the previous invariant test) cannot see this drift.
    arm = {"arm_id": "P1", "label": "x", "family": "package"}
    wraps = []
    for i in range(3):
        w = _fee_rec(f"S{i}", 0.03)
        w["rec"]["realized_fp"] = 0.12344
        w["rec"]["sum_pnl_pp"] = round(0.12344, 4)  # 0.1234 display
        w["rec"]["open_mtm_fp"] = None
        wraps.append(w)
    roll = _rollup_arm(arm, wraps)
    assert roll["realized_pp"] == 0.3703  # not 0.3702
    fee_fp = FEE_SIDE_PCT * 0.09
    assert roll["net_realized_pp"] == round(3 * 0.12344 - fee_fp, 4)
    assert roll["net_combined_pp"] == roll["net_realized_pp"]  # no opens


def test_rollup_falls_back_to_display_fields_for_old_recs():
    # Pre-amendment recs (no *_fp keys) must still roll up -- the fallback
    # reads the rounded display fields, matching the old behavior exactly.
    arm = {"arm_id": "P1", "label": "x", "family": "package"}
    roll = _rollup_arm(arm, [_fee_rec(f"S{i}", 0.03) for i in range(3)])
    assert roll["realized_pp"] == 3.0 and roll["net_realized_pp"] == 2.9989


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


# -- TVB-30 audit LOW-1: per-symbol nets from the UNROUNDED fee ---------------


def test_net_fields_round_once_distinguishes_staged_formula():
    # P1's half-fraction fee_sides (x.5) puts the unrounded fee on a
    # round-half boundary: fee_sides=1.5 -> fee 0.01875. At realized
    # -2.99998 the D10 round-once net is -3.0187 while the old staged
    # formula (subtract the ROUNDED display fee first) books -3.0188.
    nets = _net_fields(-2.99998, None, 1.5)
    fee_fp = FEE_SIDE_PCT * 1.5
    assert nets["net_realized_pp"] == round(-2.99998 - fee_fp, 4) == -3.0187
    staged = round(-2.99998 - round(fee_fp, 4), 4)
    assert staged == -3.0188  # the defect this pins against
    assert nets["net_combined_pp"] == nets["net_realized_pp"]
    assert nets["fees_pp"] == round(fee_fp, 4)


# -- TVB-30 audit LOW-2: rollup fallback is finite, open-aware, row-wise ------


def test_rollup_open_row_without_mtm_raises():
    arm = {"arm_id": "P1", "label": "x", "family": "package"}
    w = _fee_rec("S0", 0.03)
    w["rec"]["open_dir"] = "up"
    w["rec"]["open_mtm_pp"] = None
    w["rec"]["open_mtm_fp"] = None
    with pytest.raises(ValueError, match="open row without MTM"):
        _rollup_arm(arm, [w])


def test_rollup_nonfinite_input_raises():
    arm = {"arm_id": "P1", "label": "x", "family": "package"}
    w = _fee_rec("S0", 0.03)
    w["rec"]["realized_fp"] = float("nan")
    with pytest.raises(ValueError, match="non-finite"):
        _rollup_arm(arm, [w])
    w2 = _fee_rec("S1", 0.03)
    w2["rec"]["fee_sides"] = float("inf")
    with pytest.raises(ValueError, match="non-finite"):
        _rollup_arm(arm, [w2])


def test_rollup_mixed_schema_fee_is_row_wise():
    # One pre-amendment row (no fee_sides) used to force EVERY new row back
    # to its rounded display fee (all-or-nothing), shifting the aggregate's
    # last digit. Row-wise: new rows keep their unrounded fee, only the old
    # row contributes its display fee.
    arm = {"arm_id": "P1", "label": "x", "family": "package"}
    new1 = _fee_rec("S0", 3.3333)
    new2 = _fee_rec("S1", 3.3333)
    old = _fee_rec("S2", 0.0)
    old["rec"]["fee_sides"] = None
    old["rec"]["fees_pp"] = 0.05
    roll = _rollup_arm(arm, [new1, new2, old])
    row_wise = round(FEE_SIDE_PCT * 3.3333 * 2 + 0.05, 4)
    all_display = round(round(FEE_SIDE_PCT * 3.3333, 4) * 2 + 0.05, 4)
    assert row_wise != all_display  # the two policies are distinguishable
    assert roll["fees_pp"] == row_wise == 0.1333
    assert roll["fee_sides"] is None  # mixed schema: no roster side count
