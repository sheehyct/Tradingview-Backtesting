"""Tests for analysis/l2_book_impact.py (book-walk and aggregation arithmetic)."""

from analysis.l2_book_impact import aggregate, snapshot_impact, walk_book

BOOK = {
    "time": 1,
    "levels": [
        # bids (best first)
        [
            {"px": "99.99", "sz": "5", "n": 1},
            {"px": "99.98", "sz": "10", "n": 1},
            {"px": "99.97", "sz": "100", "n": 1},
        ],
        # asks (best first)
        [
            {"px": "100.01", "sz": "2", "n": 1},
            {"px": "100.02", "sz": "3", "n": 1},
            {"px": "100.05", "sz": "20", "n": 1},
        ],
    ],
}


def test_walk_book_multi_level_vwap_exact():
    levels = [(100.01, 2.0), (100.02, 3.0), (100.05, 20.0)]
    w = walk_book(levels, 10.0)
    # 2 @ 100.01 + 3 @ 100.02 + 5 @ 100.05 = 1000.33 for 10
    assert abs(w["vwap"] - 100.033) < 1e-12
    assert w["worst_px"] == 100.05
    assert w["filled"] == 10.0
    assert not w["exhausted"]


def test_walk_book_exhausted_and_empty():
    levels = [(100.0, 1.0)]
    w = walk_book(levels, 5.0)
    assert w["exhausted"]
    assert w["filled"] == 1.0
    assert w["vwap"] == 100.0
    e = walk_book([], 5.0)
    assert e["vwap"] is None
    assert e["exhausted"]


def test_snapshot_impact_signs_and_mid():
    snap = snapshot_impact(BOOK, [4.0])
    assert abs(snap["mid"] - 100.0) < 1e-9
    assert abs(snap["spread_usd"] - 0.02) < 1e-9
    rows = {r["side"]: r for r in snap["rows"]}
    # buy 4: 2 @ 100.01 + 2 @ 100.02 -> vwap 100.015, impact vs mid +0.015
    assert abs(rows["buy"]["impact_usd"] - 0.015) < 1e-9
    # sell 4: all at best bid 99.99 -> impact vs mid (sign flipped) +0.01
    assert abs(rows["sell"]["impact_usd"] - 0.01) < 1e-9
    # both sides: positive impact = cost
    assert rows["buy"]["impact_frac"] > 0
    assert rows["sell"]["impact_frac"] > 0


def test_aggregate_median_and_tvticks():
    s1 = snapshot_impact(BOOK, [4.0])
    s2 = snapshot_impact(BOOK, [4.0])
    agg = aggregate([s1, s2], mintick=0.001)
    buy = next(a for a in agg if a["side"] == "buy")
    assert buy["n"] == 2
    assert abs(buy["med_usd"] - 0.015) < 1e-9
    # 0.015 USD / 0.001 mintick = 15 TV ticks
    assert abs(buy["med_tvticks"] - 15.0) < 1e-9
    assert buy["exhausted_n"] == 0
