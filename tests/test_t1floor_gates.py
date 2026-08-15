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
    TIER_B_BY_SYMBOL,
    _determinism_check,
    _first_divergence_is_exit,
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


def test_committed_depth_streams_pass_all_pairs():
    # in-memory re-verification of the committed round under the hardened
    # rule: all 15 depth-arm pairs, equal symbol sets, prefix rule
    from itertools import combinations

    streams: dict[str, dict[str, list[tuple]]] = {}
    for arm in ENTRY_BOOK_ARMS:
        per_sym: dict[str, list[tuple]] = {}
        for e in _events(arm):
            if e["action"] in ("enter", "exit"):
                per_sym.setdefault(e["sym"], []).append(_stream_key(e))
        streams[arm] = per_sym
    sym_sets = {a: set(streams[a]) for a in ENTRY_BOOK_ARMS}
    assert all(sym_sets[a] == sym_sets["D1"] for a in ENTRY_BOOK_ARMS)
    for a, b in combinations(ENTRY_BOOK_ARMS, 2):
        for sym in sym_sets[a]:
            assert _first_divergence_is_exit(streams[a][sym], streams[b][sym]), (a, b, sym)


# --- census determinism guard ----------------------------------------------


def test_census_committed_d2_passes():
    rows = rc._trade_rows(_events("D2"), BARS_DIR)
    opens = [r for r in rows if r["exit_kind"] == "open"]
    assert len(rows) == 85 and len(opens) == 3  # the audit's committed D2 shape
    check = rc._determinism(rows, "D2", ROUND_DIR / "results_by_symbol.jsonl")
    assert check["mismatches"] == []


def test_census_open_mark_deletion_fails():
    # the audit's reproduction: 85 rows with three opens -> 82 with none
    events = [e for e in _events("D2") if e["action"] != "open_mark"]
    rows = rc._trade_rows(events, BARS_DIR)
    assert len(rows) == 82
    check = rc._determinism(rows, "D2", ROUND_DIR / "results_by_symbol.jsonl")
    assert len([m for m in check["mismatches"] if m["field"] == "open"]) == 3


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
