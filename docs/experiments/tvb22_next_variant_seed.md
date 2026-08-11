# TVB-22 next-variant seed -- T1-floor round: depth axis + retracement census

STATUS: SEED FOR A DESIGN SESSION. Nothing here is declared. Every value and
arm below is an OPEN RULING for the user; the pre-registration is written and
committed only after those rulings, BEFORE any code. Inherits the charter
(ablation-not-tournament; the spread is the finding; no arm/depth promoted).

## Where this comes from (mechanism, not scoreboard)

Post-hoc decomposition of the ruled containment rerun (committed window,
10-symbol roster; deterministic replays, no artifacts modified):

- A2's losses are almost entirely the BORN-BEYOND class (75 trades, -21.3pp,
  3% win: entered at or past their own frozen target). Its small gains are
  the TINY-TARGET class (53 trades, +4.4pp, 100% win, ~0.08% avg each:
  frozen T1 sat under 0.25% from the fill; 17 of 53 had a real target at
  the trigger that a LATE FILL compressed below 0.25%). One a-priori floor
  on target distance kills both classes. This is the user's own rule-base
  rule ("Target 1 must be far enough away to cover fees and ensure real
  profit") arriving as the mechanism-motivated repair.
- Ladder-traversal census on A1 (control exits give price room). RECEIPT
  (2026-08-10, external audit F2): the original 70/40/43 figures here were
  unpinned post-hoc reads mixing denominators -- superseded by
  analysis/paper/tier_b/ladder_census_receipt.json (regenerate:
  `uv run python -m analysis.paper.ladder_census`; conventions pinned in
  the module docstring; determinism-guarded against the committed A1
  rows). Receipt figures, all 137 closed trades, reach touch: 65.0%
  reached >= 2 frozen rungs before exit, 37.2% reached >= 4, 39.4%
  stalled at 1-2, 13.9% never reached rung 1; the 86 bf-harvest exits
  fired after 3.62 rungs on average (zero-rung excluded; 3.41 including).
  The book stays BIMODAL (stall-at-1-2 39% vs run-4+ 37%) -- no single
  fixed depth serves both modes, which is mechanically why the live
  playbook harvests along the ladder.
- Depth costs: A3 vs A2 shifted the book toward real magnitudes but paid
  -28.8pp across 9 backstop exits; the package's MAE-tail collapse (worst
  9% vs 37%) comes from exiting fast and will erode with depth.
- Chop veto: fixed 2% suppresses 47-100% of candidates per symbol
  (accidental symbol filter); ATR scaling is the named repair.

## Proposed arm menu (all ablations vs C1 + the A0b matched control)

1. T1-FLOOR ARM(S): pattern entries + veto any candidate whose frozen exit
   target sits closer than FLOOR_PCT to the prospective fill (directional).
   Kills born-beyond (<=0) and tiny classes by construction.
2. DEPTH SWEEP (labeled ceiling-map, NOT candidates): exit-all-at-rung-N
   for N = 1..5, T1-floor ON, fallback per ruling below. Read as a curve;
   no N promoted; a deployed depth needs a structural reason.
3. ATR-SCALED VETOES: replace fixed 1%/2% with ATR multiples (window and
   multiplier ruled a-priori).
4. RETRACEMENT CENSUS (read-only diagnostic, NO exit change): port the M+T
   pine's position-health rules (RETRACEMENT = developing signal-TF bar
   inside and against the held direction; POTENTIAL 3 = against-side level
   taken, or with-side break closing against) into the twin as a
   measurement layer with fixture tests; census = rungs reached before the
   first label of each kind, per trade, per arm book. The pine's own rules,
   nothing tuned. Informs (never decides) the reserved revisit-exits lane.
   The user's stated prior, on record 2026-08-10: a retracement-label EXIT
   would likely hurt by exiting early; untested; census first.

## Open rulings (the design session's agenda)

- FLOOR_PCT value (fixed % vs ATR-scaled vs fee-multiple; the user's rule
  cites fees -- note xyz taker ~0.0086-0.0125%/side measured in TVB-2).
- Depth set for the sweep (N = 1..5? include no-target-exit i.e. C1-exits
  with floor on, as the depth-infinity endpoint?).
- Fallback when the entry snapshot lacks rung N (shallower rung vs skip).
- ATR window + multipliers for both vetoes; keep fixed-percent arms as
  comparators or drop.
- Whether the retracement census rides this round or waits.
- Signal TF stays 1H (structural); confirm.

## Standing constraints

Same window/universe/units as Tier B unless re-ruled; conclusions attach to
named contrasts only; package arms never adjudicate charter S3.1; the TV
package strategy (parity-gated 9/9) mirrors any engine change BEFORE its
next live use, then re-gates.
