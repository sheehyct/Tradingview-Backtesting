"""TVB-15 roster-rule tests on a trimmed REAL /api/state snapshot
(analysis/reference/tvb15_apistate_trimmed.json, captured 2026-07-20)."""

import json
from pathlib import Path

from analysis.paper.roster import DEFAULT_RULE, select_roster

REPO = Path(__file__).resolve().parents[1]
STATE = json.loads((REPO / "analysis" / "reference" / "tvb15_apistate_trimmed.json").read_text())


def test_default_rule_tails_and_floors():
    r = select_roster(STATE)
    assert r["long_names"] == ["xyz:NBIS", "xyz:GOOGL", "xyz:SKHY", "xyz:AMD", "xyz:GOLD"]
    assert r["short_names"] == ["xyz:ORCL", "xyz:CRCL", "xyz:TSLA", "xyz:MSTR", "xyz:ZHIPU"]
    names = {c["name"] for c in r["symbols"]}
    # floor exclusions: vol (LLY 0.21M, HYUNDAI 1.19M, KR200 1.14M), universe (BTC)
    assert names.isdisjoint({"xyz:LLY", "xyz:HYUNDAI", "xyz:KR200", "BTC"})
    # mid-score floor-passers stay out of the tails
    assert names.isdisjoint({"xyz:SKHX", "xyz:EWY"})
    assert all(c["tv_mintick"] is None for c in r["symbols"])  # filled post-freeze
    assert r["rule"] == DEFAULT_RULE


def test_oi_floor_dial():
    r = select_roster(STATE, {"min_oi_usd": 200_000_000.0})
    assert r["long_names"] == ["xyz:SKHX"]
    assert r["short_names"] == []


def test_tails_are_sign_constrained():
    # tail_size larger than the candidate pool: longs stop at score > 0
    r = select_roster(STATE, {"tail_size": 10})
    assert r["long_names"] == [
        "xyz:NBIS",
        "xyz:GOOGL",
        "xyz:SKHY",
        "xyz:AMD",
        "xyz:GOLD",
        "xyz:SKHX",
        "xyz:EWY",
    ]
    assert len(r["short_names"]) == 5
    assert all(c["score"] > 0 for c in r["symbols"] if c["tail"] == "long")
    assert all(c["score"] < 0 for c in r["symbols"] if c["tail"] == "short")
