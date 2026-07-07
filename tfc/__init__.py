"""TFC breadth-engine port (VBT_BREADTH_PORT_PLAN.md, TVB-8).

Python port of pine/baseline_continuity.pine (TFC Baseline+Regime [TVB-4],
pineVersion 20). The Pine source and the committed TV dumps in
analysis/reference/ are the ground truth; nothing from this package enters
the record before the Phase-3 equivalence gate (8 cells trade-for-trade) is
green.
"""
