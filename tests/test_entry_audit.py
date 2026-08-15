"""Entry-audit receipt pins (TVB-24 assessment fold).

Pins the independently verified diagnostic numbers (2026-08-15 session:
both assessment diagnostics reproduced exactly, containment check new) so a
regression in the dumps, bars, or module is visible. The instrumented D1
evaluation funnel is NOT re-run here (receipt-generation-time only); its
committed receipt block is pinned as literals instead.
"""

from __future__ import annotations

import json
from pathlib import Path

from analysis.paper.entry_audit import ARM_IDS, ROUND_DIR, entry_stats

REPO = Path(__file__).resolve().parents[1]
BARS_DIR = str(REPO / "analysis" / "paper" / "bars")


def _minticks() -> dict[str, float]:
    roster = json.loads((REPO / "analysis" / "paper" / "roster_week1.json").read_text())
    return {e["name"]: float(e["tv_mintick"]) for e in roster["symbols"]}


def test_d1_close_benchmark_and_identity_pins():
    s = entry_stats("D1", BARS_DIR, _minticks())
    assert s["n_entries_roster"] == 102
    c = s["vs_decision_bar_close_roster"]
    assert (c["favorable"], c["adverse"]) == (61, 41)
    assert c["mean_signed_pp"] == 0.0809
    assert c["sum_signed_pp"] == 8.2503
    assert c["p90_abs_pp"] == 0.7271
    assert c["max_abs_pp"] == 2.0426
    ident = s["identity"]
    assert ident["distinct"] == 86
    assert ident["reentered_identities"] == 16
    assert ident["max_entries_one_identity"] == 2


def test_containment_totals_and_pessimistic_direction():
    mt = _minticks()
    total_entries = 0
    total_outside = 0
    for arm in ARM_IDS:
        s = entry_stats(arm, BARS_DIR, mt)
        total_entries += s["n_entries_all_symbols"]
        for row in s["containment"]["outside"]:
            # max/min fill construction puts an uncontained fill on the FAR
            # side of the bar: always the worse price for the trade
            if row["dir"] == "short":
                assert row["price"] < row["bar_low"]
            else:
                assert row["price"] > row["bar_high"]
        total_outside += s["containment"]["n_outside_entry_bar_range"]
    assert total_entries == 765
    assert total_outside == 11


def test_committed_receipt_matches_recomputation():
    receipt = json.loads((ROUND_DIR / "entry_audit_receipt.json").read_text())
    mt = _minticks()
    for arm in ARM_IDS:
        assert receipt["per_arm"][arm] == entry_stats(arm, BARS_DIR, mt), arm
    funnel = receipt["d1_evaluation_funnel"]
    assert funnel["candidate_evaluations"] == 4111
    assert funnel["distinct_identities"] == 682
    assert funnel["identities_evaluated_more_than_once"] == 569
    assert funnel["max_evaluations_one_identity"] == 12
