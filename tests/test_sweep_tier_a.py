"""Plumbing invariants for the TVB-19 Tier A sweep runner.

Deliberately NOT numeric goldens: the sweep is a labeled deliberate-overfit
artifact and its numbers are not a contract. What is a contract: the runner
is deterministic over committed bars, its accounting identities hold, and it
touches no frozen week-1 artifact. Engine fidelity itself is covered by the
existing paper goldens.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from analysis.paper.sweep_tier_a import (
    WINDOW_END,
    WINDOW_START,
    _med,
    _pct,
    _replay_cell,
    _rollup,
    _warm_symbol,
    grid,
    warm_key,
)

REPO = Path(__file__).resolve().parents[1]
BARS_DIR = str(REPO / "analysis" / "paper" / "bars")


def _deployed_cell():
    for c in grid():
        if (
            c["arm_tf_s"] == 900
            and c["pool_12h"]
            and c["n_max"] == 6
            and c["min_sep"] == 1.0
            and c["pool_cap"] == 12
            and c["brk_exit"]
            and c["flip_backstop"]
        ):
            return c
    raise AssertionError("deployed-defaults cell missing from grid")


def test_grid_is_the_preregistered_864():
    cells = grid()
    assert len(cells) == 864
    assert len({c["tag"] for c in cells}) == 864
    assert len({warm_key(c) for c in cells}) == 54


def test_median_is_true_median_on_even_samples():
    assert _med([10.9755, 30.5233]) == 20.7494
    assert _med([1.0, 2.0, 3.0, 4.0]) == 2.5
    assert _med([3.0, 1.0, 2.0]) == 2.0
    assert _med([]) is None
    assert _pct([1.0, 2.0], 0.9) == 2.0  # p90 stays nearest-rank


def test_rollup_carries_preregistered_metric_schema():
    required = {
        "n_trades",
        "realized_pp",
        "open_mtm_pp",
        "combined_pp",
        "roster_max_dd_pp",
        "med_pnl_pct",
        "win_rate",
        "mfe_avg_pct",
        "mfe_med_pct",
        "gb_avg_pp",
        "gb_med_pp",
        "gb_p90_pp",
        "mae_avg_pct",
        "worst_runner",
        "weekly",
    }
    roll = _rollup(grid()[0], [])
    missing = required - set(roll)
    assert not missing, f"rollup missing preregistered fields: {missing}"


def test_deployed_cell_replay_deterministic_and_consistent():
    roster = json.loads((REPO / "analysis" / "paper" / "roster_week1.json").read_text())
    entry = next(e for e in roster["symbols"] if e["name"] == "xyz:DRAM")
    cell = _deployed_cell()
    ws = int(datetime.fromisoformat(WINDOW_START).replace(tzinfo=timezone.utc).timestamp())
    we = int(datetime.fromisoformat(WINDOW_END).replace(tzinfo=timezone.utc).timestamp())
    warm = _warm_symbol(entry, warm_key(cell), ws, BARS_DIR)
    r1 = _replay_cell(entry, cell, warm, ws, we, BARS_DIR)
    warm2 = _warm_symbol(entry, warm_key(cell), ws, BARS_DIR)
    r2 = _replay_cell(entry, cell, warm2, ws, we, BARS_DIR)
    assert r1["rec"] == r2["rec"]
    rec = r1["rec"]
    assert rec["n_trades"] == rec["n_bf"] + rec["n_brk"] + rec["n_flip"]
    assert rec["combined_pp"] == round(rec["sum_pnl_pp"] + (rec["open_mtm_pp"] or 0.0), 4)
    assert rec["max_dd_pp"] >= 0.0
    assert sum(rec["weekly"][w]["n"] for w in ("W1", "W2", "W3", "W4")) == rec["n_trades"]
    n_eps = rec["n_trades"] + (1 if rec["open_dir"] else 0)
    assert len(r1["episodes"]) == n_eps
    roll = _rollup(cell, [r1])
    assert roll["n_trades"] == 0  # DRAM is the parity symbol: excluded from rollups
