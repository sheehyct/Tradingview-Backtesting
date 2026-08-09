# TVB-21 Tier B -- Magnitude+Targets layer ablation -- pre-registration

**LABEL: PRE-COMMITTED LAYER ABLATION with named contrasts (charter S3.1/S5
amendments, audit-F3 contrast ladder). NO deployment claims, NO cell or arm
promotion. Every conclusion attaches to the contrast that isolates it; the
package arms can NEVER adjudicate charter S3.1 (they co-mingle vetoes and
exits with the pattern dictionary); only the isolation arm bears on it.
Kill-first reading: the job is to find where the layer dies, not to confirm
it.**

- Declared: 2026-08-09T03:45Z (UTC; session date 2026-08-08 ET), BEFORE any
  pattern/veto/target code exists. Git HEAD at declaration: f90d0c9.
- Author: TVB-21 design session. Every design variable below was ruled by
  the user IN the design session (same day); the seed is
  `docs/experiments/tvb20_design_session_seed.md`, the contrast contract is
  the charter S3.1 second amendment (2026-08-08).
- Engine: the committed Python twin (analysis/paper/engine.py) extended per
  this document, over the same committed archived Hyperliquid bars as Tier A
  (analysis/paper/bars/). Headless; no TradingView contention; the mounted
  TV CONTROL is untouched. A TV-side strategy() port of the package is a
  named deferred item with its own future parity gate.
- Relation to Tier A: same window, universe, units, and fill-convention
  spirit, so Tier A's exit-cost numbers (brk ~47pp / flip ~35pp median
  in-window) and the 30-40% MAE tail remain comparable context.

## The layer ladder (audit-F3 naming, binding)

- C0 = charter S5 minimal continuity-only baseline (not run here).
- C1 = C0 + BF-exit layer = v6.1 semantics = the parity-gated CONTROL.
- C2 = C1 + the Magnitude+Targets package (dictionary + triggers + target
  ladder + vetoes) with the exit substitution ruled below.

## User rulings (2026-08-08 design session, all a-priori)

1. **Dictionary spec: PINE-EXACT** port of
   `pine/strat_magnitude_targets_plus.pine` (the as-built, as-traded
   object; logic byte-identical to the partner original). Divergences vs
   the strat-methodology skill are DOCUMENTED, not re-designed:
   (a) 1-3 Rev-Strat goes in-force at the inside bar's completion side
   (skill R22 prefers the reclaim side and calls this LATE); (b) the
   1-3-2's hammer/shooter close is optional and label-only (skill R17
   requires it, else routes to plain 3-2); (c) detection is color-gated
   (developing signal-TF bar green for longs / red for shorts; the skill
   triggers on the raw break regardless of color). A skill-canonical
   variant is a named deferred arm, never a per-pattern cherry-pick.
2. **Dictionary subset (the user's live list, 10 setups ON):** 1-2-2
   (2-Bar Rev-Strat), bare 2-2 reversal, 1-3 (1-Bar Rev-Strat), 1-3-2,
   3-2, 3-2-2, 3-1-2 Chicago (reversal AND continuation), 2-1-2 reversal,
   2-1-2 momentum, 1-3-1-2. OFF: Shot-Gun, Randy Jackson, Gap-Up/Down,
   Inside-Bar Breakout, Outside-Bar Continuation, Going-3. PMG context
   flag ON (name prefix + logged flag only, never a gate; pmgBars=5).
   Precedence = the pine's else-if chain verbatim; a shape whose specific
   toggle is OFF reroutes to the coarsest enabled name that matches (e.g.
   a Shot-Gun-shaped 2u-2d-2u enters as a bare 2-2 reversal) -- declared
   behavior, logged via the name field.
3. **3-2 scope: ALL 3-2s enter.** Boom (the pine shape rule: dominant wick
   >= 50% of range, body <= 40% of range) is logged per trade as a flag; the
   Boom/non-Boom split is a pre-committed post-hoc read, never a gate.
4. **Signal TF: 1H only** (structural ground: the timeframe the user
   trades these setups live; Tier A's arm-TF performance gradient is
   explicitly NOT a justification and was not used).
5. **Contrasts: C2-vs-C1 package + one pattern-isolation arm** (below).
6. **BF-proximity veto reference: nearest ALIVE harvest-side line across
   ALL enabled pools** (12h/D/W/M) -- the minimum-magnitude reading (layers
   2 and 3 meet in the same object). USER FLAG recorded: possible
   excessive entry suppression -> pre-committed diagnostic (below).
7. **C2 exit substitution: M+T target exits REPLACE the BF-touch harvest
   exit;** the adverse-line break (brk) and full-flip backstop stay ON.
   Any revisit after visualization = a NEW pre-registered variant, never a
   mid-run change.
8. **Veto thresholds: FIXED 1% (BF-proximity) and 2% (chop),** exactly the
   user's stated placeholders, no calibration. ATR-scaled variants are
   named deferred arms; the cross-symbol transfer concern becomes the
   per-symbol veto-rate diagnostic.

## Arms (5; declared exhaustively)

| Arm | Entries | Vetoes | Exits |
|-----|---------|--------|-------|
| A0a "control, deployed cadence" | C1 arm-trigger, arm_tf 15m (deployed default cell: 12h pool on, n_max 6, min_sep 1.0, pool_cap 12) | none | bf + brk + flip |
| A0b "control, matched cadence" | C1 arm-trigger, arm_tf 1H, same knobs | none | bf + brk + flip |
| A1 "pattern isolation" | pattern dictionary (10 setups, pine-exact, 1H) + D/W/M gate | none | bf + brk + flip (C1 exits UNCHANGED) |
| A2 "package, T1-always" | as A1 | BF-prox 1% + chop 2% | exit ALL at Target 1 + brk + flip (bf-harvest OFF) |
| A3 "package, 2 targets" | as A1 | BF-prox 1% + chop 2% | exit ALL at Target 2 (ladder rung 2; fallback T1 if the entry snapshot has no rung 2) + brk + flip (bf-harvest OFF) |

A0a and A0b are committed Tier A grid cells re-replayed by the Tier B
runner for one-manifest provenance; their rows must reproduce the committed
Tier A per-symbol numbers exactly (free determinism regression).

## Contrast statements (binding; conclusions attach here and nowhere else)

- **A2/A3 vs A0b** = the package at matched trigger cadence -- the primary
  identified C2-vs-C1 contrast.
- **A2/A3 vs A0a** = the operational headline vs the deployed control
  (cadence change included and stated in every readout).
- **A1 vs A0b** = do pattern-gated entries carry information beyond the
  continuity break, with exits held fixed -- the ONLY contrast here that
  bears on charter S3.1.
- **A2/A3 vs A1** = the increment from vetoes + target exits, given
  pattern entries.
- The spread is the finding. No arm is promoted. Extreme numbers are
  questions (sizing? exit bug? kind window?), not verdicts.

## Mechanics (pinned)

Detection (pattern arms): the twin replays 5m bars; a local 1H aggregator
mirrors the pine (new period at each 3600s ts boundary pushes the completed
bar into a 250-bar history; the developing 1H bar updates with every 5m
bar). Break/inside flags use the pine's `>= 1 tick` strict-break form with
the pine's warm-up guards; hammer/shooter use the pine shape rule; the
16-branch precedence chain runs verbatim with the toggles above.

Entry (pattern arms), evaluated once per 5m bar while flat:
- the detection chain yields a signal (shape + trigger broken + developing
  1H bar color agrees), AND
- the D/W/M gate is aligned in the signal direction (existing layer-1
  gate, unchanged), AND
- no veto (A2/A3 only), THEN
- enter at fill = max(trigger + 1 tick, this 5m bar's open) for longs
  (mirror with min for shorts). The max/min term makes late-in-hour
  entries (signal persisting after a veto/gate cleared) fill at the
  available price instead of the stale level -- a CONSERVATIVE bias
  relative to the controls' level fills, declared here. One position at a
  time; same-bar re-entry blocked (existing engine rule).

Vetoes (A2/A3, evaluated against the prospective fill price):
- BF-proximity: veto a long when the nearest ALIVE upper-side line across
  all enabled pools, valued at this bar's open time on the BAR-OPEN alive
  set (before this bar's lifecycle transitions), sits within 1.0% of fill
  ((line - fill)/fill <= 0.01); mirror for shorts with lower-side lines.
  No qualifying alive line -> no veto.
- Chop: veto when |fill - gate_open| / fill <= 0.02 for ANY of the three
  current D/W/M period opens (literal reading of the rule-base's plural
  "flip levels").

Targets (A2/A3): the ladder is the pine's, snapshotted AT ENTRY and frozen
for the trade: anchor (and conditional anchor2) first, then prior 1H
extremes not yet taken out, nearest-first strictly-monotone walk, capped at
extTargets=5 beyond T1, 250-bar history depth. Exit on touch (5m bar range
reaches the level), fill AT the level -- the bf-touch convention. Exit race
per bar: target -> brk -> flip (the target occupies the bf slot). Later
signals while in a position never re-target the open trade.

Window / universe / units: Tier A conventions verbatim (see
tvb19_tier_a_prereg.md): window 2026-07-06 00:00 -> 2026-08-03 00:00 UTC;
warm-up from archived pre-window bars (listing-bound, recorded); flat at
the boundary; open positions marked at the last in-window 5m close; all 11
roster symbols with frozen minticks; roster rollups exclude xyz:DRAM;
1x GROSS, no fees/funding/slippage; UTC clock; percentage points of
per-position notional. THIS IS ONE ~4-WEEK WINDOW in one macro regime,
labeled in-sample characterization; nothing generalizes beyond it.

## Metrics + pre-committed diagnostics

Per arm x symbol, then roster rollup, matching the Tier A schema (closed
count, sum pp, median %, win rate, exit-class mix incl. the new `tgt`
class, episode MFE/MAE/give-back, open MTM, combined pp, equity-path max
drawdown, weekly entry-ts slices), PLUS:

- Per-symbol and roster VETO RATES (A2/A3): candidate entries vetoed by
  BF-prox, by chop, by both; entry-count delta vs A1 (the user's
  excessive-suppression flag, measured not assumed).
- Per-pattern-name frequency x outcome census (labeled exploration /
  ceiling-mapping; per-pattern winner promotion stays forbidden).
- Boom split on 3-2 trades (flag read, no gate).
- PMG-prefix split (flag read).
- Ladder-depth stats at entry (rungs available; how often A3's rung 2
  exists) and target-vs-backstop exit attribution.
- Adverse-runner class vs Tier A's config-invariant 30-40% MAE tail.

## Named deferred (NOT run in v1; on record so they cannot be smuggled in)

ATR-scaled veto variants; skill-canonical detection arm (R22 reclaim +
R17 hammer-required + no color gate, applied together); 15m/30m signal-TF
arms; flip-uncoupling / day-leg-flip exit redesigns; open-air stop;
RTH-anchored clock arms (census justified, still pre-registered only);
weekend/low-liquidity protocol arms; per-veto ablation singles; TV-side
strategy() port of the package (requires its own parity gate); any
re-targeting of open trades.

## Amendment 2026-08-09 (TVB-22, user-ruled, declared BEFORE the F1 rerun)

Follows `docs/reviews/tvb21-codex-audit.md` (F1 HIGH + F2 LOW, both
independently reproduced in TVB-22 before adjudication). Rulings made by the
user 2026-08-09; the rerun happens only after this amendment is committed.

1. **Target exit contract (F1): containment touch.** A frozen target exits
   the trade on the first 5m bar whose RANGE CONTAINS the level
   (`low <= tgt <= high`), fill AT the level -- the same containment-touch
   convention the C1 bf-harvest exit already uses, gap-past edge included
   (a bar wholly beyond the level does NOT exit; on 24/7 perp 5m bars a
   true gap across a level without containment is rare). This applies
   uniformly, INCLUDING trades whose frozen target was at-or-behind the
   fill at entry (born-beyond): they exit at the first bar that actually
   trades the level. The as-built one-sided predicates (long `h >= tgt` /
   short `l <= tgt`) are the DEFECT this amendment removes. Marketable-at-
   entry targets are neither exited at entry nor vetoed -- the T1-floor
   entry guard stays a separate named deferred variant, values a-priori.
2. **No-target signals (F2): structural skip retained; vetoes evaluated
   first.** A package-arm candidate with an empty entry-snapshot ladder
   still never enters (it cannot satisfy its exit contract), but BOTH veto
   diagnostics are now evaluated for EVERY candidate before the skip, so
   veto-rate denominators are coherent (share-of-candidates statements
   include all candidates). Counters: `both`/`bf_prox`/`chop` count the
   vetoed set over ALL candidates; `no_target` counts all empty-ladder
   candidates; a new `no_target_vetoed` counts the overlap, so
   `entries = candidates - (vetoed + no_target - no_target_vetoed)`.
3. **Manifest source-binding (F4):** the rerun manifest additionally
   records sha256 blob hashes of the executed `tier_b.py` / `engine.py` /
   `patterns.py` and the git clean/dirty state at run time.

Everything else is unchanged. The rerun regenerates `analysis/paper/tier_b/`
IN PLACE (git history preserves the invalidated run). Fix-isolation
invariants, checked before the new artifacts are accepted: A0a / A0b / A1
per-symbol rows must equal the invalidated run's rows on every field except
the `veto_counts` dict gaining the zero-valued `no_target_vetoed` key, and
the A0 determinism check vs the committed Tier A cells must still pass.

## Execution + provenance

- Runner: analysis/paper/tier_b.py, written AFTER this document; reuses
  the compare_config/sweep warm mechanism; engine extensions land behind
  config defaults that leave every existing code path bit-identical
  (regression: full suite green, port-parity compare unchanged at
  89/67/87, A0a/A0b rows reproduce committed Tier A cells).
- Outputs: analysis/paper/tier_b/ -- per-(arm,symbol) JSONL, per-arm
  roster rollup JSONL, manifest (arms, window, git HEAD, wall timestamps).
  Deterministic reproduction from committed runner + bars + this doc.
- Reading rules bound in advance: findings-first in words, no bare cell
  codes; every discussed difference gets a structural-vs-sample tag; the
  package arms never adjudicate S3.1; kill-first.
