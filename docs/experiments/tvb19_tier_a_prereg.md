# TVB-19 Tier A overnight sweep -- pre-registration

**LABEL: DELIBERATE OVERFIT / in-sample ceiling / secondary control.
NO deployment claims. Nothing in this sweep selects a configuration
for live use. The spread is the finding; extreme cells are questions,
not verdicts; any winner gets tagged structural-vs-sample before it is
even discussed.**

- Declared: 2026-08-05T03:44Z (UTC), before any sweep code was written
  or any cell was executed. Git HEAD at declaration: 3a3911d.
- Author: TVB-19 overnight session, executing the user's post-TVB-18
  seed (".session_startup_prompt.md", "Overnight overfit-sweep seed",
  2026-08-04) under explicit user direction to run Tier A tonight.
- Engine: the committed Python twin (analysis/paper/engine.py, v6.1
  defaults) over committed archived Hyperliquid bars
  (analysis/paper/bars/, merged spans through 2026-08-04). Headless; no
  TradingView contention. TV spot-verification of chosen cells is a
  LATER, separate step and is out of scope tonight.
- Relation to the champion-baseline request (TVB-12, revived by the
  seed): this is the Tier A slice only -- existing TwinConfig knobs,
  no exit-semantics variants. Tier B (target-ladder harvest variants,
  partial-flip backstops) is design-gated and NOT run tonight.

## What is being asked

The deliberate-overfit question: across the full existing-knob space of
the deployed tier-1 TFC-BF watch twin, what is the in-sample ceiling on
this one archived window, where does the config space die, and which
knobs move outcomes for a structural reason vs a sample reason? The
week-1 finding this feeds: the adverse-runner exit gap
(config-invariant in the TVB-16 two-cell ablation) -- the grid's
brk/flip corners quantify open-air exposure across the whole knob
space with zero design commitment.

## Grid (declared exhaustively; 864 cells)

Existing TwinConfig knobs only, per the seed. Axes and levels:

| axis | levels | deployed value |
|---|---|---|
| arm_tf_s (arm timeframe) | 300 (5m), 900 (15m), 1800 (30m), 3600 (1H) | 900 |
| 12h pool | on, off (pool removed before warm-up, compare_config.py mechanism) | on |
| n_max (max compound width) | 3, 6, 9 | 6 |
| min_sep (anchor separation, base periods) | 0.5, 1.0, 2.0 | 1.0 |
| pool_cap (formations per pool) | 6, 12, uncapped (None) | 12 |
| brk_exit (adverse close-through exit) | on, off | on |
| flip_backstop (full-gate flip exit) | on, off | on |

4 x 2 x 3 x 3 x 3 x 2 x 2 = 864 cells. The deployed-defaults cell
(900, 12h on, 6, 1.0, 12, brk on, flip on) is the control anchor
inside the grid; every readout states cells relative to it.

Fixed at deployed values, NOT swept (declared exclusions):

- allow_long / allow_short: both on (the seed's axis list does not
  include direction toggles; TVB-9's long-only question stays open).
- supersede_per_side / evict_retired_first: True/True (v6.1). The
  v6.0-parity pair is a fidelity mode, not a strategy knob.
- Gate set D/W/M, gate predicate (close vs period open), trigger
  (+/- 1 tick strict break of prior completed arm-TF extremes), exit
  race order bf -> brk -> flip: engine semantics, untouched. No
  flip-semantics or ladder code tonight (user order).
- Fill conventions: week-1 a-priori set -- entry at trigger, BF exit
  at line value, brk/flip exits at the 5m close. 1x, GROSS, no
  fees/funding/slippage. Twin evaluates CLOSED 5m bars only.
- bar_s = 300 (5m replay stream) for every cell including arm 5m
  (arm_tf_s=300 means the arm snapshot rolls every bar).

The brk-off + flip-off corner leaves BF harvest as the ONLY exit; it
is retained deliberately as the open-air-exposure measurement.

## Window (declared)

- W_full: 2026-07-06 00:00 UTC -> 2026-08-03 00:00 UTC (28 days,
  Monday-to-Monday, 4 complete W-gate periods). One window, one
  regime sample -- stated plainly: THIS IS ONE ~4-WEEK WINDOW in one
  macro regime; nothing here generalizes beyond it, which is the
  point of the in-sample-ceiling label.
- Warm-up: all archived 1h bars before window start feed the
  12h/D/W pools and gate seeding; all archived 1d bars before window
  start feed the M pool; the arm seed is the last arm_tf_s of 5m bars
  before the boundary (compare_config.py convention). Warm-up depth
  is LISTING-BOUND and varies by symbol (1h history from 2025-12-24
  for the majors down to 2026-07-09 for SKHY); per-run warm-up bar
  counts are recorded in the results. The known F3 fidelity delta
  (coarse warm-up changes lifecycle state) applies to every cell
  equally; its repair is deferred to the repairs bundle, not tonight.
- xyz:SKHY has no 5m bars before 2026-07-09 13:05 UTC; its replay
  effectively begins there (flat, ~3.5 days late). Declared, not
  patched.
- Positions start FLAT at the window boundary; open positions at
  window end are marked to the last in-window 5m close.
- Post-hoc weekly slices by ENTRY timestamp (freeze_slice.py
  convention): W1 07-06..07-13, W2 07-13..07-20, W3 07-20..07-27,
  W4 07-27..08-03. The W3 slice does NOT reproduce the frozen week-1
  record -- different warm boundary and carried positions -- and the
  week-1 adjudication (protocol doc, 2026-08-04) stands: week 1 has
  NO official number. The frozen week-1 artifacts are not touched.

## Universe

All 11 roster_week1.json symbols with their frozen tv_mintick values.
Roster rollups EXCLUDE xyz:DRAM (parity instrument, not
rule-selected -- week-1 convention); DRAM is still run and reported
per-symbol. The roster itself froze 2026-07-20T14:31Z; window weeks
W1-W2 predate any selection-freeze protection. That is acceptable
HERE ONLY because this sweep is labeled deliberate-overfit ceiling,
not a graded run; the F1 lesson is answered by declaring it, and the
freeze-boundary invariant repair remains greenlit for future graded
runs.

## Metrics (per cell x symbol, then roster rollup)

Closed trades: count, sum pnl pp, median pnl %, win rate, exit-class
mix (bf / brk / flip counts and per-class pnl). Episodes (closed
trades AND the open position at window end, metered to window end):
MFE %, MAE %, give-back pp (avg, median, p90). Open MTM pp at window
end and combined pp (realized + open MTM). Equity path: per-symbol
bar-level curve (cumulative realized + open-position MTM per 5m bar)
and its max drawdown pp; roster curve = sum of per-symbol curves
aligned on the 5m grid (forward-filled), roster max drawdown pp.
Worst-runner depth = max episode MAE including the open position.
Weekly entry-ts slices: per-slice closed count + sum pnl pp.

All in percentage points of per-position notional at 1x gross -- the
same unit as every week-1 artifact.

## Execution + provenance

- Runner: analysis/paper/sweep_tier_a.py (written AFTER this doc;
  reuses the compare_config.py replay mechanism verbatim; touches
  neither engine.py nor any frozen week-1 artifact).
- Outputs: analysis/paper/sweeps/tvb19_tier_a/ -- per-(cell,symbol)
  JSONL, per-cell roster rollup JSONL, run manifest (grid, window,
  git HEAD, run start/end UTC wall timestamps). Per-cell event logs
  are NOT stored; any cell reproduces deterministically from the
  committed runner + bars + config.
- Reading rules bound in advance: the spread is the finding; a tight
  cluster of great results is suspicious; extreme cells are
  questions (sizing? exit bug? kind window?); every discussed winner
  gets a structural-vs-sample tag; no bare cell codes in
  user-facing text -- configs are expanded into words.
