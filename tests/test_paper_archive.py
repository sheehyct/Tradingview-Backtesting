"""TVB-15 archive merge tests on committed real bars (mechanics vectors)."""

import json
from pathlib import Path

from analysis.paper.archive import infer_tick, merge_rows

REPO = Path(__file__).resolve().parents[1]
ROWS = json.loads((REPO / "analysis" / "reference" / "tvb14_dram_1h_hl.json").read_text())["bars"]


def test_merge_union_newest_wins():
    old = [list(r) for r in ROWS[:100]]
    new = [list(r) for r in ROWS[50:150]]
    new[10][4] = new[10][4] + 0.001  # overlap row revised in the newer fetch
    merged = merge_rows(old, new)
    assert len(merged) == 150
    ts = [r[0] for r in merged]
    assert ts == sorted(ts) and len(set(ts)) == len(ts)
    revised_ts = new[10][0]
    got = next(r for r in merged if r[0] == revised_ts)
    assert got[4] == new[10][4]  # newest fetch won


def test_merge_disjoint_and_idempotent():
    a, b = [list(r) for r in ROWS[:50]], [list(r) for r in ROWS[50:100]]
    merged = merge_rows(a, b)
    assert [r[0] for r in merged] == [r[0] for r in ROWS[:100]]
    assert merge_rows(merged, merged) == merged


def test_infer_tick_on_real_prices():
    # DRAM trades in 0.001 steps in the committed data
    assert infer_tick(ROWS) == 0.001
