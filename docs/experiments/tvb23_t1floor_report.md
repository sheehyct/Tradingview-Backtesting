# TVB-23 T1-floor round -- report

**LABEL: PRE-COMMITTED LAYER ABLATION + LABELED OVERFIT CEILING-MAP. One
~4-week window (2026-07-06 -> 08-03 UTC), 10-symbol roster (DRAM
parity-excluded), 1x GROSS, in-sample. No arm, depth, or setup is promoted;
every conclusion attaches to its named contrast
(docs/experiments/tvb23_t1floor_prereg.md, committed 58f08d7 BEFORE code,
with three dated corrections). Extreme numbers below are QUESTIONS.**

Provenance: analysis/paper/tier_b_t1floor/ (rows, rollups, per-arm event
dumps, per-arm census receipts, manifest with executed blob hashes + dirty
path list). Gates all PASS: Tier B determinism (55 rows field-equal through
tier_b's own replay path, modulo zero-valued new counter keys),
entry-stream (first divergence between depth arms is always an exit),
counter reconciliation per (arm, symbol), census determinism per arm.

## Findings first

1. **The T1-floor repairs the package's self-inflicted losses -- and the
   repaired package STILL does not earn its place over the control.** D1
   (floored A2) swings +59.2pp against A2 (+24.6 -> +83.8 combined) by
   construction-killing the born-beyond and tiny-target classes. But
   against the matched control the ladder contrast stays negative: D1
   +83.8 vs A0b +104.8 (-21.0pp). C2F does not beat C1 on this window.
   What DOES change character is the risk shape: roster max drawdown 22.1
   vs the control's 122.2, average episode MAE 1.47% vs 2.63%, zero open
   runners vs -67.7pp of open drag. Same edge verdict, very different
   book geometry -- relevant to the leverage arc, never a promotion.
2. **The floor alone flips the pattern-isolation arm positive.** A1F
   (floor only, control exits, no vetoes) turns A1's -7.7pp into +23.0pp
   while cutting the book roughly in half (87 entries from 1422
   candidates; the floor vetoes 88% of them: 607 born-beyond + 644 tiny).
   Read against the control, the pattern layer stays deeply negative
   (A1F +23.0 vs A0b +104.8), so charter S3.1's standing verdict is
   unmoved; the floor is damage removal, not pattern edge.
3. **The depth curve is NOT monotone, and its top is the shallowest
   exit.** Combined: D1 +83.8, D2 +38.5, D3 +51.3, D4 +60.0, D5 +65.4,
   DINF +19.4. Realized P&L rises monotonically with depth (83.8 ->
   104.0 at D5) but open-runner drag (-38.5pp parked on the same three
   open positions from D3 up) and eroding tail metrics eat it. The
   MAE-tail collapse decays with depth exactly as the seed predicted:
   worst runner 14.95% (D1) -> 28.7-29.7% (D3+), avg MAE 1.47% -> 2.98%.
   DINF (never cap the trade) collapses to +19.4 with the worst average
   MAE of the family (5.43%). Ceiling-map read only; no N promoted; a
   deployed depth still needs a structural reason.
4. **ATR scaling dissolves most of the chop veto's accidental symbol
   filter.** Fixed 2% suppression spanned 43-100% per symbol and shut
   three symbols out entirely (GOLD 100%, AAPL 96.5%, AMZN 91.9% -> 0
   entries each). ATR(14) x2 compresses the spread to 58-80% and unlocks
   all three (AAPL 3, GOLD 1, AMZN 1 entries) while tightening the
   loosest symbols. That is the transfer question answered in the
   affirmative. P&L: D1ATR +68.7 vs D1 +83.8 (-15.1pp) -- stated, not
   adjudicated; the veto-rate geometry, not this window's P&L, was the
   pre-registered read.
5. **The retracement census supports the user's prior: a
   retracement-label exit would fire far too early.** The first
   POTENTIAL-3 label arrives before almost any ladder progress (mean
   rungs reached before the first label: 0.02 in D1, 0.56 in D5, 1.27 in
   A1F) and labeling is near-universal on any book that holds trades
   long (ever-labeled: 49% of D1's fast book, 90% of A1F, 97% of DINF;
   100% of LOSERS in every arm -- but also 48-96% of winners). At 1H
   cadence the label is early, frequent, and barely discriminating on
   timing; as an EXIT it would have cut winners before their first rung
   far more often than it would have saved losers. Measured, per the
   pre-registered read; the exit-design lane stays reserved.
6. **A 98-99% win rate is an exit-construction artifact, not edge.** D1:
   100 of 102 closed trades exit at their frozen floored target
   (+105.4pp) against 2 break exits (-21.6pp). A floor-gated T1-always
   book wins by definition unless a stop fires first; the information is
   in the loss-channel thinning (2 stops all window) and the drawdown
   geometry, not the win percentage.

## Named contrasts (numbers)

| Contrast | Result |
|----------|--------|
| D1 vs A2 (primary repair) | +83.8 vs +24.6 combined; win 98.0% vs 60.2% (constructed); maxDD 22.1 vs 67.8; closed 102 vs 186 |
| D2 vs A3 (repair at depth 2) | +38.5 vs +31.0; maxDD 64.1 vs 73.3; worst MAE 29.7 vs 28.7 |
| D1 vs A0b (C2F-vs-C1 ladder) | +83.8 vs +104.8: the floored package still trails the control by 21.0pp |
| A1F vs A1 (floor under C1 exits) | +23.0 vs -7.7; entries 87 vs A1's 137 closed; floor vetoes 1251/1422 candidates |
| D1ATR vs D1 (veto transfer) | suppression spread 58-80% vs 43-100%; shut-outs unlocked; P&L -15.1pp |
| Depth curve (ceiling-map) | 83.8 / 38.5 / 51.3 / 60.0 / 65.4 / 19.4 (D1..D5, DINF) -- non-monotone, shallow-top |

Full rollup table: analysis/paper/tier_b_t1floor/results_rollup.jsonl.
Controls quoted from the committed Tier B rerun rollups (reproduced
field-exact by this run's determinism gate).

## Floor kill counters (rollup)

D1: 4111 candidates -> t1_floor 3291 (born-beyond d<=0: 1644; tiny
0<d<0.25%: 1647), of which 605 were floor-ONLY (passed every other veto).
The born-beyond machinery TVB-22 located is real at candidate scale, not
just among the trades that happened to enter: ~40% of all candidates
arrive at or past their own frozen T1. D1ATR: 3226 floor-vetoed of 4172.
A1F (no other vetoes): 1251 of 1422. Candidate counts differ across arms
through position occupancy (a held book evaluates fewer candidates), so
rates, not raw counts, are the comparable object.

## Entry funnel (the occupancy effect, prereg ruling 3 correction)

D1 137 -> D2 108 -> D3 93 -> D4 89 -> D5 85 -> DINF 50 entries
(11-symbol event streams). Deeper exits hold longer, so later candidates
fire while shallow arms are flat and deep arms are not. The depth curve
therefore reads exit depth WITH its book-occupancy consequence -- never
exits in isolation. The entry-stream gate verified every depth-arm
divergence originates at an exit event. (This correction was caught by
the gate itself on the first full run, before any results were read;
the wrongly-claimed identical-book consequence was the design session's
gloss, not a user ruling.)

## Per-setup census (declared reading, ruling 7; n < 10 = sign-indeterminate)

D1 (n>=10): 2-2d n=25 +24.9pp (25W), 1-2u-2d n=18 +23.2pp (18W), 2-1-2d
n=17 +11.6pp (17W), 3-2d n=15 +12.2pp (15W). A1F: 2-2d n=25 +19.3pp
(15W), 2-2u n=12 +17.3pp (9W). D5: 2-2d n=15 +20.1pp, 2-1-2d n=14
+27.4pp, 1-2u-2d n=10 +41.1pp. Reading: the book is overwhelmingly
SHORT-side setups in a window whose short legs worked -- the direction
skew is regime-confounded and per-setup n never exceeds 25. Mechanism
hunting only; nothing here re-ranks the dictionary, and the small
negative cells (1-3d: -8.0pp n=7 in D1) are sign-indeterminate.

## What this round did NOT establish

- No edge claim: every number is one gross in-sample window; the
  fresh-window replication is a named future round.
- No depth, arm, or setup promotion; no S3.1 revision (the standing
  negative verdict is if anything reinforced by A1F-vs-A0b).
- No fee/funding/slippage modeling; no live-cadence claim (the TV mirror
  + re-gate is step 7 and gates any live use of the new arms).
- The retracement census informs the reserved exit-design lane; it does
  not decide it.

## Receipts index

- Rows/rollups/manifest: analysis/paper/tier_b_t1floor/
- Per-arm event dumps: events_{D1..D5,DINF,A1F,D1ATR}.jsonl
- Per-arm ladder+retracement receipts: census_{arm}.json (roster scope,
  conventions pinned in analysis/paper/round_census.py)
- Runner + gates: analysis/paper/tier_b_t1floor.py
