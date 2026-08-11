"""TVB-22 package-port parity gate regression tests.

Pins the pattern-layer fail-closed hardening (TVB-22 external audit F1,
returned 2026-08-10). The pattern layer is the drift-detection payload the
package port exists for: every matched entry must agree on pattern name and
on trigger within mintick/2. The pre-fix gate compared the TV trigger against
``te.get("trig", float("nan"))``; any comparison with NaN is False, so a twin
entry that LOST its trig field (or carried NaN) contributed no violation and
the gate still PASSed -- reproduced on the committed GOOGL/A1 cell (79
matched events, 40 pattern checks, zero violations) before the fix. A +inf
trig already failed via the comparison; missing/NaN were the silent paths.

The hardened gate (a) rejects entries without a finite numeric trig or a
non-empty pattern name at validation, on both sides, and (b) treats a
non-finite twin trig as a pattern violation even if validation is bypassed.
The committed nine-cell artifact must keep passing with identical counts
(GOOGL/A1 pinned here; the full 9/9 sweep is the committed result artifact).
"""

import copy
import json
import math

import pytest

from analysis.paper.pkg_parity import PKG, compare, gate, twin_events, validate_events

# --- synthetic pattern world --------------------------------------------------
# Two-bar stream: pattern entry fills at bar 1000 close 10.0, break exit at bar
# 2000 close 11.0. The twin entry carries the pattern payload (name + trig);
# the TV entry_signal encodes the same payload as "<pattern> t=<trig>".

CLOSED_TRADE = {
    "index": 0,
    "direction": "L",
    "entry_time": 1000 * 1000,
    "entry_price": 10.0,
    "entry_signal": "SYN-2-2 t=9.5",
    "exit_signal": "Break D",
    "exit_time": 2000 * 1000,
    "exit_price": 11.0,
}


def _twin():
    return [
        {
            "ts": 1000,
            "action": "enter",
            "dir": "long",
            "kind": "entry",
            "price": 9.501,
            "pattern": "SYN-2-2",
            "trig": 9.5,
        },
        {"ts": 2000, "action": "exit", "dir": "long", "kind": "brk", "price": 11.0},
    ]


def _gate(trades=None, twin=None):
    closes = {1000: 10.0, 2000: 11.0}
    port = {
        "chart": {"mintick": 0.001, "first_bar_ts": 1000},
        "trades": trades if trades is not None else [dict(CLOSED_TRADE)],
    }
    return gate("SYN", "A1", twin if twin is not None else _twin(), 2000, closes, 2, port)


def test_gate_passes_clean_synthetic_pattern_stream():
    r = _gate()
    assert r["pass"] is True
    assert r["structural_violations"] == []
    assert r["twin_events"] == r["tv_events_in_feed"] == r["matched"] == 2
    assert r["pattern_layer"] == {"checked": 1, "violations": []}


@pytest.mark.parametrize(
    "mutate, needle",
    [
        (lambda e: e.pop("trig"), "not a finite number"),
        (lambda e: e.update(trig=float("nan")), "not a finite number"),
        (lambda e: e.update(trig=float("inf")), "not a finite number"),
        (lambda e: e.update(trig="9.5"), "not a finite number"),
        (lambda e: e.pop("pattern"), "missing pattern name"),
        (lambda e: e.update(pattern=""), "missing pattern name"),
    ],
)
def test_gate_fails_closed_on_malformed_twin_entry_payload(mutate, needle):
    twin = _twin()
    mutate(twin[0])
    r = _gate(twin=twin)
    assert r["pass"] is False
    assert any(v.startswith("twin") and needle in v for v in r["structural_violations"])


def test_non_finite_twin_trig_is_a_pattern_violation_even_past_validation():
    # defense in depth: bypass validate_events and hit the comparison directly
    twin = _twin()
    twin[0]["trig"] = float("nan")
    problems = validate_events(twin, "twin")
    assert any("not a finite number" in p for p in problems)
    r = _gate(twin=twin)
    bad = r["pattern_layer"]["violations"]
    assert len(bad) == 1 and math.isnan(bad[0]["twin_trig"])


def test_gate_fails_on_pattern_name_mismatch():
    twin = _twin()
    twin[0]["pattern"] = "SYN-3-2"
    r = _gate(twin=twin)
    assert r["pass"] is False
    assert r["pattern_layer"]["violations"][0]["tv_pattern"] == "SYN-2-2"


def test_gate_fails_on_trig_drift_beyond_half_tick():
    twin = _twin()
    twin[0]["trig"] = 9.5 + 0.001  # one full mintick away
    r = _gate(twin=twin)
    assert r["pass"] is False
    assert r["pattern_layer"]["violations"] == [
        {"key": (1000, "enter", "long", "entry"), "tv_trig": 9.5, "twin_trig": 9.5 + 0.001}
    ]


def test_committed_googl_a1_parity_survives_hardened_gate():
    r = compare("GOOGL", "A1")
    assert r["pass"] is True
    assert r["structural_violations"] == []
    assert r["twin_events"] == r["tv_events_in_feed"] == r["matched"] == 79
    assert r["pattern_layer"]["checked"] == 40
    assert r["pattern_layer"]["violations"] == []


def test_committed_googl_a1_artifact_false_passed_prefix_defect_shape():
    # the audit's reproduction, kept adversarial: delete one committed twin trig
    # in memory and require the hardened gate to fail structurally
    port = json.loads((PKG / "tvb22_GOOGL_A1_trades.json").read_text())
    tw_evs, feed_end, closes, n_bars = twin_events(
        "GOOGL", "A1", port["chart"]["first_bar_ts"], port["chart"]["mintick"]
    )
    evs = copy.deepcopy(tw_evs)
    next(e for e in evs if e["action"] == "enter").pop("trig")
    r = gate("GOOGL", "A1", evs, feed_end, closes, n_bars, port)
    assert r["pass"] is False
    assert any("not a finite number" in v for v in r["structural_violations"])
