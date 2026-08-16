"""TVB-25 runner regression tests: arm table integrity, gate-stream
collapsing for tranche arms, the determinism comparison, and the
matched-entry frozen-state contract (F5 carried forward)."""

from __future__ import annotations

import pytest

from analysis.paper.engine import TwinConfig
from analysis.paper.tier_b_exits import (
    CONTROL_FAMILY,
    NEW_ARMS,
    PACKAGE_FAMILY,
    TRANCHE_ARMS,
    _gate_stream_events,
    _matched_entry,
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
