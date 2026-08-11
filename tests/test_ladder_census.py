"""TVB-22 audit F2: ladder-traversal census counting-rule tests.

Pins the rungs_reached conventions the committed receipt declares: reach
(favorable extreme at/past the rung; gap-past counts) vs containment (the
ruled fill convention; a bar wholly past a rung does not count), deepest-index
semantics without a monotonicity assumption, and the caller-side bar slice
(entry bar excluded).
"""

from analysis.paper.ladder_census import rungs_reached

# rows: (ts, open, high, low, close)
ENTRY_BAR = (0, 9.9, 10.4, 9.8, 10.0)


def test_reach_counts_gap_past_containment_does_not():
    rows = [ENTRY_BAR, (300, 10.2, 10.5, 10.2, 10.4)]  # gapped over rung 1 at 10.0
    ladder = [10.0]
    assert rungs_reached(rows, 1, 2, ladder, "long", "reach") == 1
    assert rungs_reached(rows, 1, 2, ladder, "long", "containment") == 0


def test_containment_deepest_index_survives_a_skipped_shallow_rung():
    rows = [ENTRY_BAR, (300, 11.6, 12.5, 11.5, 12.0)]  # contains rung 3, gaps rungs 1-2
    ladder = [10.0, 11.0, 12.0]
    assert rungs_reached(rows, 1, 2, ladder, "long", "containment") == 3
    assert rungs_reached(rows, 1, 2, ladder, "long", "reach") == 3


def test_short_direction_mirrors():
    rows = [ENTRY_BAR, (300, 9.6, 9.6, 8.4, 8.5)]
    ladder = [9.0, 8.0]  # short rungs descend
    assert rungs_reached(rows, 1, 2, ladder, "short", "reach") == 1
    assert rungs_reached(rows, 1, 2, ladder, "short", "containment") == 1
    deep = [ENTRY_BAR, (300, 9.6, 9.6, 7.9, 8.1)]
    assert rungs_reached(deep, 1, 2, ladder, "short", "reach") == 2


def test_entry_bar_excluded_by_slice():
    rows = [(0, 9.9, 10.4, 9.8, 10.0), (300, 10.0, 10.05, 9.9, 10.0)]
    ladder = [10.3]  # only the entry bar reached it
    assert rungs_reached(rows, 1, 2, ladder, "long", "reach") == 0
    assert rungs_reached(rows, 0, 2, ladder, "long", "reach") == 1


def test_empty_ladder_and_empty_slice_are_zero():
    rows = [ENTRY_BAR]
    assert rungs_reached(rows, 1, 1, [10.0], "long", "reach") == 0
    assert rungs_reached(rows, 0, 1, [], "long", "reach") == 0
