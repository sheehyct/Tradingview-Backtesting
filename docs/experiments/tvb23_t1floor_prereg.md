# TVB-23 T1-floor round -- floor repair + depth ceiling-map -- pre-registration

**LABEL: PRE-COMMITTED LAYER ABLATION plus a LABELED OVERFIT CEILING-MAP
(charter S3.1/S5 amendments, audit-F3 contrast ladder). NO deployment
claims. NO cell, arm, or depth promotion -- the depth sweep is read as a
curve and a deployed depth would need a structural reason ruled a-priori.
Every conclusion attaches to the contrast that isolates it; package arms
NEVER adjudicate charter S3.1. Kill-first reading: the job is to find where
the floor repair fails, not to confirm it.**

- Declared: 2026-08-10 (session TVB-23), BEFORE any floor/ATR/retracement
  code exists. Git HEAD at declaration: 0023852.
- Author: TVB-23 design session (2026-08-10). Every design variable below
  was ruled by the user IN the design session; the agenda was
  `docs/experiments/tvb22_next_variant_seed.md`.
- Engine: the committed Python twin (analysis/paper/engine.py, containing
  the TVB-21 extensions under the 2026-08-09 containment amendment),
  extended per this document, over the same committed archived Hyperliquid
  bars as Tier A/B (analysis/paper/bars/). Headless. The TV-side mirror of
  the new arms is step 7 of the round (own parity gate) and gates the
  strategy's next live use; it is not part of the headless run.
- Relation to Tier B: same window, universe, units, fill convention,
  detection layer, and exit-race semantics as
  `docs/experiments/tvb21_tier_b_prereg.md` INCLUDING its 2026-08-09
  amendment (containment targets, vetoes-before-skip, source-bound
  manifest). This document only ADDS the floor, the ATR veto variant, the
  retracement measurement layer, and the depth arms. The committed Tier B
  rerun rows (analysis/paper/tier_b/) are this round's comparators.

## Where this round comes from (mechanism, not scoreboard)

The TVB-22 decomposition located the package's loss machinery in two
classes killed by the user's own rule-base rule ("Target 1 must be far
enough away to cover fees and ensure real profit"): BORN-BEYOND (entered
at/past the frozen target; A2: 75 trades, -21.3pp, 3% win) and TINY-TARGET
(frozen T1 under 0.25% away; +4.4pp of hollow 100%-win trades). The A1
ladder-traversal census (committed receipt,
analysis/paper/tier_b/ladder_census_receipt.json: 39.4% stall at 1-2
rungs, 37.2% run 4+) motivates the depth axis as a ceiling-map. The chop
veto's fixed 2% suppressed 47-100% of candidates per symbol (accidental
symbol filter); ATR scaling is the named repair.

## User rulings (2026-08-10 design session, all a-priori)

1. **T1-floor = FIXED 0.25% of fill.** Directional distance from the
   prospective fill to the frozen Target 1; veto the entry when the
   distance is below the floor (born-beyond, distance <= 0, included by
   construction). Ground: 10x the worst measured xyz round-trip taker
   (2 x 0.0125%, TVB-2); fees are fixed, so the floor is fixed. Provenance
   declared: 0.25% is also the TVB-22 decomposition's tiny-class boundary
   (named there as a round number, not tuned on performance).
2. **Depth sweep N = 1..5 plus the depth-infinity endpoint** (C1 exits
   with the floor on). Labeled ceiling-map; floor ON in every cell; read
   as a curve; no N promoted.
3. **Rung fallback = SHALLOWER** (exit at the deepest available rung when
   the snapshot lacks rung N) -- the ruled A3 semantics. Consequence,
   asserted at run time: the entry book is IDENTICAL across every
   depth cell, so the curve isolates exit depth alone.
4. **ATR vetoes ride:** Wilder ATR(14) on the aggregated 1H signal-TF
   bars; BF-proximity veto = within 1.0 x ATR of the line; chop veto =
   within 2.0 x ATR of a gate open (preserves the ruled 1:2 fixed-pair
   shape). Fixed-percent veto arms stay as in-round comparators.
5. **Retracement census rides** (read-only diagnostic, NO exit change):
   pine-exact position-health predicates from
   `pine/strat_magnitude_targets_plus.pine:694-716`. RETRACEMENT = the
   developing 1H bar is inside (in0) and colored against the held
   direction. POTENTIAL 3 = the against-side level is taken (d0 for
   longs, u0 for shorts) OR a with-side break is closing against
   (u0-and-r0 for longs, d0-and-g0 for shorts). Per-bar, no latch.
   [Correction 2026-08-10, dated BEFORE code: the pine's own comment
   (:696-701) claims an outside-bar 3 is included, but its CODE uses the
   one-sided flags (d0 = bl0 and not bh0), so an outside bar labels
   POTENTIAL 3 only through the intrabar phase where exactly the
   against-side is broken; if the with-side breaks first, the flags skip
   to out0 and the label never fires. Pine-exact means the CODE; this
   as-built edge is documented, kept, and pinned by fixture -- same
   policy as the TVB-21 detection divergences.] Declared substitution: the held
   trade's direction replaces the pine's remember-layer `mrDir`. User
   prior on record (2026-08-10): a retracement-label EXIT would likely
   hurt by exiting early -- the census measures, never decides.
6. **Signal TF = 1H only** (structural: the timeframe the user trades
   these setups live). The 15m/30m arms stay named-deferred.
7. **Per-setup census = a DECLARED report reading**: per-pattern-name
   n / pnl / wins per arm, n stated everywhere, small-n cells flagged
   sign-indeterminate, mechanism-hunting only. The no-promotion rule is
   unchanged: no setup is toggled off this sample's ranking; dictionary
   membership changes remain a-priori re-commitments from the user's live
   reasoning.

## Arms (9 new + 5 determinism re-runs; declared exhaustively)

Every new arm: pattern entries (10-setup dictionary, pine-exact, 1H),
D/W/M gate, T1-floor 0.25% ON, deployed pool knobs (12h ON, n_max 6,
min_sep 1.0, pool_cap 12).

| Arm | Vetoes | Exits |
|-----|--------|-------|
| D1 "floored package, T1" | fixed BF-prox 1% + chop 2% | frozen rung 1 + brk + flip (the floored A2) |
| D2 "floored package, T2" | fixed 1% + 2% | rung 2, fallback shallower, + brk + flip (the floored A3) |
| D3 / D4 / D5 | fixed 1% + 2% | rung 3 / 4 / 5, fallback shallower, + brk + flip |
| DINF "depth infinity" | fixed 1% + 2% | C1 exits (bf + brk + flip); floor still vetoes entries |
| A1F "floored isolation" | NONE (floor only) | C1 exits (bf + brk + flip) |
| D1ATR "ATR vetoes" | BF-prox 1.0 x ATR(14,1H) + chop 2.0 x ATR(14,1H) | frozen rung 1 + brk + flip |

Design note (declared at prereg, resolves a seed ambiguity): the seed's
single "depth-infinity endpoint" carried two jobs with contradictory veto
requirements. It is split: DINF keeps the D-family vetoes so the depth
curve D1..D5 -> DINF holds entries fixed and varies ONLY exit depth; A1F
drops the vetoes so the floor's effect under control exits is read against
A1 unconfounded. One extra arm buys two clean contrasts.

Empty-ladder rule (uniform across ALL floor arms, including DINF/A1F): a
candidate with an empty entry snapshot ladder has no Target 1, so the
floor rule is unsatisfiable -- structural skip (existing `no_target`
counter; vetoes still evaluated first per the 2026-08-09 amendment).
Consequence: D1..D5 and DINF share ONE entry book exactly; A1F's book is
A1's minus floor-vetoed and empty-ladder candidates.

Determinism re-runs: A0a, A0b, A1, A2, A3 (tier_b.ARMS verbatim, new
engine flags inert). Their per-symbol rows must be field-equal to the
committed `analysis/paper/tier_b/results_by_symbol.jsonl` rows or the run
FAILS. This pins the extended engine's default-path invariance at artifact
scale and gives the round one-manifest provenance for its comparators.

## Contrast statements (binding; conclusions attach here and nowhere else)

- **D1 vs A2, D2 vs A3** = the floor's isolated effect under the package
  exits -- the PRIMARY repair test (same vetoes, same exits, floor added).
- **D1 vs A0b** = the C2F-vs-C1 ladder contrast: does the FLOORED package
  earn its place over the matched control. D2..D5 are ceiling-map cells
  and never carry this contrast.
- **A1F vs A1** = the floor's effect with exits held at C1 and no vetoes.
- **D1ATR vs D1** = veto transferability. Read per-symbol suppression
  rates FIRST (does ATR dissolve the fixed veto's accidental symbol
  filter), then P&L.
- **Depth curve D1..D5 + DINF** = labeled overfit ceiling-map, read as a
  curve; includes where the MAE-tail collapse erodes with depth.
- The spread is the finding. Extreme numbers are questions, not verdicts.

## Mechanics (pinned; everything not stated here inherits the TVB-21
## prereg + its 2026-08-09 amendment verbatim)

T1-FLOOR VETO (entry layer, all new arms): for each candidate with a
non-empty snapshot ladder, T1 = ladder[0] (nearest rung) and
fill = the prospective pattern fill (max(trig + tick, bar open) longs,
mirror shorts). Distance d = (T1 - fill)/fill for longs, (fill - T1)/fill
for shorts. Veto when d < 0.0025. Evaluated for EVERY such candidate
alongside the other vetoes, BEFORE the no-target skip. Counters:
`t1_floor` (total floor-vetoed), split `t1_floor_le0` (d <= 0, the
born-beyond class) and `t1_floor_small` (0 < d < floor, the tiny class),
plus `t1_floor_only` (floor-vetoed and passed by every other veto -- the
floor's marginal suppression). [Amended 2026-08-10, before the engine
change landed: reconciliation is asserted via the exact counter equation
`entries = candidates - no_target - (both + bf_prox + chop -
no_target_vetoed) - t1_floor_only` per (arm, symbol) -- equivalent to the
originally-worded direct skip counter, but it keeps every NEW counter
zero-valued on the determinism arms, so their field-equality check stays
strict modulo zero-valued new keys (the TVB-22 no_target_vetoed
precedent).]

ATR (D1ATR): true range on COMPLETED aggregated 1H signal-TF bars
(TR = max(h - l, |h - prev_close|, |l - prev_close|)); Wilder smoothing,
window 14 (seed = SMA of the first 14 TRs, then
atr = (13 x atr_prev + tr)/14). The 1H stream is the pattern detector's
own aggregation; the ATR seed consumes the same pre-window 1h bars as
`seed_history`, so ATR is always formed in-window. Veto predicates use the
ATR value as of the last COMPLETED 1H bar, in PRICE units:
BF-prox veto when 0 < (line - fill) <= 1.0 x ATR (longs; mirror shorts);
chop veto when |fill - gate_open| <= 2.0 x ATR for ANY of the three D/W/M
period opens. The floor in D1ATR stays the fixed 0.25% (ruling 1: the
floor is fee-grounded, not vol-grounded).

RETRACEMENT MEASUREMENT LAYER (read-only; every new arm): evaluated per
5m bar while a position is held, on bars strictly AFTER the entry bar,
from the detector's existing developing-1H classification flags:
- RETRACEMENT bar: in0 AND (r0 if long else g0).
- POTENTIAL-3 bar: long: d0 OR (u0 AND r0); short: u0 OR (d0 AND g0).
First-occurrence timestamps of each label are recorded on the trade's
exit event (and on the open-position record at window end). Decisions,
exits, and every existing counter are untouched -- the layer writes no
state the position machine reads. Census read (post-run): frozen-ladder
rungs reached (reach convention, entry bar excluded -- the committed
receipt's conventions) BEFORE each first label, per trade, per arm.

DEPTH (D1..D5): existing `exit_targets` semantics -- exit at frozen rung
N, fallback to the deepest available rung; containment touch per the
2026-08-09 amendment; exit race target -> brk -> flip unchanged.

Window / universe / units: Tier A/B conventions verbatim -- window
2026-07-06 00:00 -> 2026-08-03 00:00 UTC; warm-up from archived
pre-window bars; flat at the boundary; open positions marked at the last
in-window 5m close; 11 roster symbols, frozen minticks, rollups exclude
xyz:DRAM; 1x GROSS, no fees/funding/slippage; UTC clock; percentage
points of per-position notional. THIS IS ONE ~4-WEEK WINDOW in one macro
regime, labeled in-sample characterization; nothing generalizes beyond
it. A fresh-window replication is a FUTURE round with its own prereg.

## Metrics + pre-committed diagnostics

Per (arm, symbol) rows + roster rollups on the Tier B schema (closed
count, sum pp, median %, win rate, exit-class mix incl. tgt, episode
MFE/MAE/give-back, open MTM, combined pp, max drawdown, weekly slices,
veto counters), PLUS:

- Floor kill counters: `t1_floor_le0` / `t1_floor_small` /
  `t1_floor_only` per symbol and rollup -- the born-beyond and tiny
  classes suppressed, measured not assumed.
- Per-setup census per arm (ruling 7): n / pnl_pp / wins per pattern
  name; report flags n < 10 as sign-indeterminate.
- Ladder-traversal census receipts per arm (analysis/paper/ladder_census.py
  generalized; same pinned conventions as the committed A1 receipt;
  determinism-guarded against the round's own rows).
- Retracement census per arm: share of trades ever labeled, rungs reached
  before first RETRACEMENT and first POTENTIAL 3, split by exit class and
  by winner/loser.
- Veto suppression per symbol, D1ATR vs D1 side by side (the transfer
  question), with ATR% of price stated per symbol for context.
- MAE-tail table across all arms vs the controls' 30-40% tail and the
  package's known collapse (worst 9-28.7%) -- where does depth erode it.
- Entry-book invariance receipt: D1..D5 + DINF entry event streams
  (ts, dir, pattern, trig) byte-equal; A1F book size delta vs A1 stated.

## Named deferred (NOT run in v1; on record so they cannot be smuggled in)

Retracement-label EXIT variants (the user's stated prior: likely hurts;
census first); ATR-scaled FLOOR; skill-canonical detection arm; 15m/30m
signal-TF arms; fresh-window / extended-window replication; per-veto
ablation singles; re-targeting of open trades; flip-uncoupling exit
redesigns; RTH-anchored clock arms; weekend protocol arms; any depth
promotion (a deployed depth needs a structural reason in its own future
prereg).

## Execution + provenance

- Runner: `analysis/paper/tier_b_t1floor.py`, written AFTER this document;
  `tier_b.py` and its committed artifacts are untouched. Engine extensions
  land behind config defaults that leave every existing code path
  bit-identical (regression: full suite green; pkg_parity 9/9 committed
  cells unchanged; determinism re-runs field-equal).
- Outputs: `analysis/paper/tier_b_t1floor/` -- per-(arm,symbol) JSONL,
  per-arm rollup JSONL, manifest (arms, window, git HEAD, executed blob
  hashes of runner/engine/patterns, git dirty state incl. dirty PATH LIST
  (TVB-22 audit note), bar hashes, determinism + invariance results, wall
  timestamps). Deterministic reproduction from committed runner + bars +
  this doc.
- Reading rules bound in advance: findings-first in words, no bare cell
  codes; every discussed difference gets a structural-vs-sample tag;
  package arms never adjudicate S3.1; kill-first.
- TV mirror + re-gate (step 7): floor/ATR/arm-selector mirrored into
  `pine/tfc_mt_package_strategy.pine` with semantics verbatim, then the
  hardened parity gate over GOOGL/TSLA/DRAM x {D1, DINF, D1ATR} before
  the strategy's next live use. Until that gate passes, the TV strategy
  stays on the TVB-22 arms.
