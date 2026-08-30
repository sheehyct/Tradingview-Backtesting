"""TVB-23 audit F1 regression: the round's guard families are fail-closed.

The audit reproduced three false-PASS paths in the committed TVB-23 runner:
(a) the Tier B determinism comparison iterated only produced rows/fields, so
empty replays, missing rows, and missing fields passed; (b) the entry-stream
helper accepted any prefix (including an empty stream against an
entry-opening one) and the caller compared only D1 against the other arms;
(c) the census determinism guard compared only per-symbol closed counts, so
deleting every open_mark still passed. Each case below reproduces the
audit's mutation against the hardened gates and pins the committed
artifacts still PASSING them (the audit's own independent replay cleared
the committed round; these tests keep the next regression from certifying
incomplete evidence).
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from analysis.paper import round_census as rc
from analysis.paper.tier_b_t1floor import (
    ENTRY_BOOK_ARMS,
    NEW_ARMS,
    TIER_B_BY_SYMBOL,
    CANONICAL_ARM_IDS,
    _determinism_check,
    _entry_stream_gate,
    _first_divergence_is_exit,
    _gate_scope,
    _resolve_requested_arms,
    _stream_key,
)

REPO = Path(__file__).resolve().parents[1]
ROUND_DIR = REPO / "analysis" / "paper" / "tier_b_t1floor"
BARS_DIR = str(REPO / "analysis" / "paper" / "bars")


def _committed_rows() -> list[dict]:
    with open(TIER_B_BY_SYMBOL, encoding="utf-8") as f:
        return [json.loads(ln) for ln in f]


def _events(arm: str) -> list[dict]:
    p = ROUND_DIR / f"events_{arm}.jsonl"
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _committed_streams() -> dict[str, dict[str, list[tuple]]]:
    streams: dict[str, dict[str, list[tuple]]] = {}
    for arm in ENTRY_BOOK_ARMS:
        per_sym: dict[str, list[tuple]] = {}
        for e in _events(arm):
            if e["action"] in ("enter", "exit"):
                per_sym.setdefault(e["sym"], []).append(_stream_key(e))
        streams[arm] = per_sym
    return streams


def _committed_recs() -> dict[str, dict[str, dict]]:
    recs: dict[str, dict[str, dict]] = {a: {} for a in ENTRY_BOOK_ARMS}
    with open(ROUND_DIR / "results_by_symbol.jsonl", encoding="utf-8") as f:
        for ln in f:
            row = json.loads(ln)
            if row["arm_id"] in recs:
                recs[row["arm_id"]][row["symbol"]] = row
    return recs


def _roster_syms() -> set[str]:
    roster = json.loads((REPO / "analysis" / "paper" / "roster_week1.json").read_text())
    return {e["name"] for e in roster["symbols"]}


NEW_ARM_IDS = tuple(a["arm_id"] for a in NEW_ARMS)


def _committed_streams_all_arms() -> dict[str, dict[str, list[tuple]]]:
    """The REAL canonical caller shape: every NEW_ARMS product (8 arms),
    not just the entry-book six -- TVB-28 audit MEDIUM-1 regression."""
    streams: dict[str, dict[str, list[tuple]]] = {}
    for arm in NEW_ARM_IDS:
        per_sym: dict[str, list[tuple]] = {}
        for e in _events(arm):
            if e["action"] in ("enter", "exit"):
                per_sym.setdefault(e["sym"], []).append(_stream_key(e))
        streams[arm] = per_sym
    return streams


def _committed_recs_all_arms() -> dict[str, dict[str, dict]]:
    recs: dict[str, dict[str, dict]] = {a: {} for a in NEW_ARM_IDS}
    with open(ROUND_DIR / "results_by_symbol.jsonl", encoding="utf-8") as f:
        for ln in f:
            row = json.loads(ln)
            if row["arm_id"] in recs:
                recs[row["arm_id"]][row["symbol"]] = row
    return recs


# --- caller/gate contract (TVB-28 audit MEDIUM-1) ---------------------------


def test_gate_scope_canonical_eight_arm_shape_passes():
    # The defect: main() previously handed all eight produced arms to a
    # six-arm expected set, so the hardened reverse-set check failed the
    # canonical CLI on A1F/D1ATR while every unit test stayed green. The
    # scoped caller path must pass the committed canonical artifacts.
    streams = _committed_streams_all_arms()
    recs = _committed_recs_all_arms()
    book_streams, book_recs, expected, scope_fail = _gate_scope(
        streams, recs, set(NEW_ARM_IDS), smoke=False
    )
    assert scope_fail == []
    assert expected == ENTRY_BOOK_ARMS
    assert set(book_streams) == set(ENTRY_BOOK_ARMS) == set(book_recs)
    fails = _entry_stream_gate(book_streams, book_recs, expected, _roster_syms())
    assert fails == []


def test_gate_scope_rejects_unrequested_produced_arm():
    # keeps the TVB-26 LOW-2 protection at the caller boundary
    streams = _committed_streams_all_arms()
    recs = _committed_recs_all_arms()
    streams["ZZ"] = streams["D1"]
    recs["ZZ"] = recs["D1"]
    _, _, _, scope_fail = _gate_scope(streams, recs, set(NEW_ARM_IDS), smoke=False)
    assert any(f["reason"] == "produced arms != requested arms" for f in scope_fail)


def test_gate_scope_smoke_subset_scopes_to_requested_family_arms():
    streams = {a: _committed_streams_all_arms()[a] for a in ("D1", "A1F")}
    recs = {a: _committed_recs_all_arms()[a] for a in ("D1", "A1F")}
    book_streams, book_recs, expected, scope_fail = _gate_scope(
        streams, recs, {"D1", "A1F"}, smoke=True
    )
    assert scope_fail == []
    assert expected == ("D1",)
    assert set(book_streams) == {"D1"} == set(book_recs)


# --- raw-request validation (TVB-29 audit MEDIUM-5) -------------------------


def test_resolve_requested_rejects_unknown_and_duplicate_ids():
    # The audit's probe: "--arms D1,ZZ" previously selected only D1 and the
    # scope gate, comparing against a requested set re-derived from that
    # filtered list, returned no failure. The raw request is now validated.
    with pytest.raises(SystemExit, match="unknown arm ids"):
        _resolve_requested_arms("D1,ZZ")
    with pytest.raises(SystemExit, match="duplicate arm ids"):
        _resolve_requested_arms("D1,D1")


def test_resolve_requested_subset_and_default():
    all_ids = [a["arm_id"] for a in NEW_ARMS]
    arms, req = _resolve_requested_arms(None)
    assert req == set(all_ids) and [a["arm_id"] for a in arms] == all_ids
    arms, req = _resolve_requested_arms("D1")
    assert req == {"D1"} and [a["arm_id"] for a in arms] == ["D1"]


def test_scope_gate_catches_selector_mutation_against_raw_request():
    # Main-level selector mutation vs the INDEPENDENT expectation: a faulty
    # selector that DROPS an arm now fails the scope gate (with the old
    # circular derivation the expectation shrank with the product and
    # passed). The extra-arm direction is pinned above
    # (test_gate_scope_rejects_unrequested_produced_arm).
    streams = _committed_streams_all_arms()
    recs = _committed_recs_all_arms()
    raw_request = set(NEW_ARM_IDS)
    dropped_streams = {a: s for a, s in streams.items() if a != "D1"}
    dropped_recs = {a: r for a, r in recs.items() if a != "D1"}
    _, _, _, fail = _gate_scope(dropped_streams, dropped_recs, raw_request, smoke=False)
    assert any(f["reason"] == "produced arms != requested arms" for f in fail)


# --- determinism comparison ------------------------------------------------


def test_committed_rows_pass_verbatim():
    r = _determinism_check(copy.deepcopy(_committed_rows()))
    assert r["n_committed_rows"] == 55
    assert r["n_compared"] == 55
    assert r["mismatches"] == []


def test_empty_replay_fails():
    # the audit's _determinism_check([]) reproduction: 55 rows must be missing
    r = _determinism_check([])
    assert len(r["mismatches"]) == 55
    assert all(m["field"] == "(row missing from replay)" for m in r["mismatches"])


def test_missing_produced_field_fails():
    # the audit's delete-sum_pnl_pp reproduction
    rows = copy.deepcopy(_committed_rows())
    del rows[0]["sum_pnl_pp"]
    r = _determinism_check(rows)
    assert any(m["field"] == "sum_pnl_pp" for m in r["mismatches"])


def test_missing_row_fails():
    r = _determinism_check(copy.deepcopy(_committed_rows())[1:])
    assert [m["field"] for m in r["mismatches"]] == ["(row missing from replay)"]


def test_duplicate_row_fails():
    rows = copy.deepcopy(_committed_rows())
    r = _determinism_check(rows + [copy.deepcopy(rows[0])])
    assert any(m["field"] == "(duplicate replay row)" for m in r["mismatches"])


def test_unexpected_row_fails():
    rows = copy.deepcopy(_committed_rows())
    extra = copy.deepcopy(rows[0])
    extra["symbol"] = "xyz:FAKE"
    r = _determinism_check(rows + [extra])
    assert any(m["field"] == "(unexpected replay row)" for m in r["mismatches"])


def test_new_veto_key_zero_tolerated_nonzero_fails():
    rows = copy.deepcopy(_committed_rows())
    rows[0]["veto_counts"] = {**rows[0]["veto_counts"], "novel_counter": 0}
    assert _determinism_check(rows)["mismatches"] == []
    rows[0]["veto_counts"]["novel_counter"] = 7
    assert any(m["field"] == "veto_counts" for m in _determinism_check(rows)["mismatches"])


# --- entry-stream gate -----------------------------------------------------

_ENTER = ("enter", 1, "long", "2-2u", 1.0)
_EXIT = ("exit", 2, "long", "tgt")


def test_stream_equal_passes():
    assert _first_divergence_is_exit([_ENTER, _EXIT], [_ENTER, _EXIT])


def test_stream_divergence_at_exit_passes():
    other_exit = ("exit", 3, "long", "brk")
    assert _first_divergence_is_exit([_ENTER, _EXIT], [_ENTER, other_exit])


def test_stream_divergence_at_entries_fails():
    other_enter = ("enter", 5, "short", "2-2d", 2.0)
    assert not _first_divergence_is_exit([_ENTER], [other_enter])


def test_empty_stream_vs_entry_opening_fails():
    # the audit's empty/missing-stream reproduction
    assert not _first_divergence_is_exit([], [_ENTER, _EXIT])


def test_prefix_continuing_with_exit_passes():
    # deeper arm still holding: shorter stream ends in-position
    assert _first_divergence_is_exit([_ENTER], [_ENTER, _EXIT])


def test_prefix_continuing_with_entry_fails():
    # both arms flat after a shared exit face the same candidate rule, so a
    # prefix continuing with an ENTRY is a mechanics violation
    next_enter = ("enter", 9, "long", "2-2u", 3.0)
    assert not _first_divergence_is_exit([_ENTER, _EXIT], [_ENTER, _EXIT, next_enter])


def test_divergence_exit_vs_entry_fails():
    # TVB-24 audit F3: an exit opposite an ENTRY at the first difference can
    # be a deleted/substituted exit -- up to the divergence both arms hold
    # the identical position, so the non-exiting side cannot legally enter
    other_enter = ("enter", 3, "short", "2-2d", 2.0)
    assert not _first_divergence_is_exit([_ENTER, _EXIT], [_ENTER, other_enter])


def test_entry_stream_gate_committed_passes():
    # in-memory re-verification of the committed round under the hardened
    # gate: exact arm set, stream-vs-rec reconciliation, equal symbol sets,
    # all 15 pairs, both-sides-exit divergence rule
    fails = _entry_stream_gate(
        _committed_streams(), _committed_recs(), ENTRY_BOOK_ARMS, _roster_syms()
    )
    assert fails == []


def test_entry_stream_gate_symbol_removed_from_all_arms_fails():
    # TVB-24 audit F3: deleting one symbol's events from EVERY arm keeps all
    # cross-arm symbol sets equal; the stream-vs-rec reconciliation catches it
    streams = _committed_streams()
    for arm in ENTRY_BOOK_ARMS:
        assert "xyz:DRAM" in streams[arm]
        del streams[arm]["xyz:DRAM"]
    fails = _entry_stream_gate(streams, _committed_recs(), ENTRY_BOOK_ARMS, _roster_syms())
    assert any(f.get("reason") == "stream-vs-rec count mismatch" for f in fails)


def test_entry_stream_gate_whole_arm_missing_fails():
    # TVB-24 audit F3: a missing whole arm previously shrank the pair matrix
    streams = _committed_streams()
    del streams["D3"]
    fails = _entry_stream_gate(streams, _committed_recs(), ENTRY_BOOK_ARMS, _roster_syms())
    assert any(f.get("reason") == "expected depth arm missing" for f in fails)


def test_entry_stream_gate_unexpected_produced_arm_fails():
    # TVB-26 audit LOW-2: the advertised exact-set check was one-way -- an
    # extra produced arm passed silently because later checks iterate only
    # the expected arms
    streams = _committed_streams()
    streams["ZZ"] = streams[ENTRY_BOOK_ARMS[0]]
    fails = _entry_stream_gate(streams, _committed_recs(), ENTRY_BOOK_ARMS, _roster_syms())
    assert any(
        f.get("reason") == "produced arm outside expected set" and f.get("arms") == ["ZZ"]
        for f in fails
    )


def test_entry_stream_gate_partial_symbol_deletion_fails():
    # deleting one symbol's events from ONE arm must fail at least via the
    # symbol-set or reconciliation checks
    streams = _committed_streams()
    del streams["D2"]["xyz:GOOGL"]
    fails = _entry_stream_gate(streams, _committed_recs(), ENTRY_BOOK_ARMS, _roster_syms())
    assert fails


# --- census determinism guard ----------------------------------------------


def test_census_committed_d2_passes():
    rows = rc._trade_rows(_events("D2"), BARS_DIR)
    opens = [r for r in rows if r["exit_kind"] == "open"]
    assert len(rows) == 85 and len(opens) == 3  # the audit's committed D2 shape
    check = rc._determinism(rows, "D2", ROUND_DIR / "results_by_symbol.jsonl")
    assert check["mismatches"] == []


def test_census_open_mark_deletion_fails():
    # TVB-23 audit F1 reproduction, superseded 2026-08-16 by the injective
    # linkage check: deleting the open_marks leaves their entries with zero
    # outcomes, so _trade_rows now fails closed BEFORE _determinism sees it
    events = [e for e in _events("D2") if e["action"] != "open_mark"]
    with pytest.raises(ValueError, match="non-injective"):
        rc._trade_rows(events, BARS_DIR)


def test_census_direction_flip_raises():
    # TVB-24 audit F3: a closed roster exit with its direction flipped kept
    # linked rows and an empty mismatch list; the entry-vs-outcome direction
    # consistency check now fails closed
    events = _events("D2")
    ex = next(e for e in events if e["action"] == "exit" and e["sym"] != rc.PARITY_SYMBOL)
    ex["dir"] = "short" if ex["dir"] == "long" else "long"
    with pytest.raises(ValueError, match="direction mismatch"):
        rc._trade_rows(events, BARS_DIR)


def test_census_duplicated_outcome_raises():
    # TVB-24 audit F3: duplicating a real outcome must not census silently
    events = _events("D2")
    ex = next(e for e in events if e["action"] == "exit" and e["sym"] != rc.PARITY_SYMBOL)
    with pytest.raises(ValueError, match="non-injective"):
        rc._trade_rows(events + [dict(ex)], BARS_DIR)


def test_census_substituted_exit_raises():
    # TVB-24 audit F3: rewiring an exit onto another trade's entry keeps the
    # aggregate closed count unchanged; injectivity catches the orphaned
    # entry (0 outcomes) and the double-linked one (2 outcomes)
    events = _events("D2")
    # same symbol AND same direction, so the direction-consistency check
    # passes and the injectivity check is what fires
    by_key: dict[tuple, list[dict]] = {}
    for e in events:
        if e["action"] == "exit" and e["sym"] != rc.PARITY_SYMBOL:
            by_key.setdefault((e["sym"], e["dir"]), []).append(e)
    exits = next(v for v in by_key.values() if len(v) >= 2)
    exits[0]["entry_ts"] = exits[1]["entry_ts"]
    with pytest.raises(ValueError, match="non-injective"):
        rc._trade_rows(events, BARS_DIR)


def test_census_duplicate_entry_raises():
    events = _events("D2")
    en = next(e for e in events if e["action"] == "enter")
    with pytest.raises(ValueError, match="duplicate entry"):
        rc._trade_rows(events + [dict(en)], BARS_DIR)


def test_census_broken_event_linkage_raises():
    events = _events("D2")
    # roster scope skips the parity symbol before linkage; orphan a roster exit
    exits = [e for e in events if e["action"] == "exit" and e["sym"] != rc.PARITY_SYMBOL]
    orphaned = [
        e
        for e in events
        if not (
            e["action"] == "enter"
            and e["sym"] == exits[0]["sym"]
            and e["ts"] == exits[0]["entry_ts"]
        )
    ]
    with pytest.raises(ValueError, match="event-linkage broken"):
        rc._trade_rows(orphaned, BARS_DIR)


# -- TVB-30 audit MEDIUM-4: default/malformed arm contract --------------------


def test_canonical_roster_pinned_literally():
    # The eight declared ids, pinned as LITERALS here too -- deriving them
    # from NEW_ARMS would track the very mutation this guards against.
    assert CANONICAL_ARM_IDS == ("D1", "D2", "D3", "D4", "D5", "DINF", "A1F", "D1ATR")
    assert [a["arm_id"] for a in NEW_ARMS] == list(CANONICAL_ARM_IDS)


def test_resolve_rejects_blank_and_empty_components():
    # Blank / commas-only input used to resolve to ZERO arms with every gate
    # passing vacuously; empty components were silently dropped.
    for bad in ("", "   ", ",,", "D1,,D2", "D1,", ",D1"):
        with pytest.raises(SystemExit, match="malformed --arms"):
            _resolve_requested_arms(bad)


def test_resolve_default_is_independent_of_new_arms_mutation(monkeypatch):
    # Shrinking or duplicating NEW_ARMS used to shrink the default
    # expectation with it (no gate could fail); the canonical literal now
    # catches the drift at resolve time.
    import analysis.paper.tier_b_t1floor as t1f

    monkeypatch.setattr(t1f, "NEW_ARMS", t1f.NEW_ARMS[:-1])
    with pytest.raises(SystemExit, match="drifted"):
        t1f._resolve_requested_arms(None)
    monkeypatch.setattr(t1f, "NEW_ARMS", [*t1f.NEW_ARMS, t1f.NEW_ARMS[0]])
    with pytest.raises(SystemExit, match="duplicate arm id"):
        t1f._resolve_requested_arms(None)
