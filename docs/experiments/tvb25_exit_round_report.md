# TVB-25 exit round -- report

**LABEL: PRE-COMMITTED LAYER ABLATION + LADDER-BOTTOM VALIDATION +
FRESH-WINDOW REPLICATION. All numbers are GROSS percentage points of
position on a one-position book unless a net-of-fee column is named; the
July window is one in-sample month; the fresh window is SHORT and
sign-indeterminate by declaration (D13). Nothing here promotes an arm,
profile, or threshold. Conclusions attach to the named contrasts and
nowhere else.**

- Prereg: `docs/experiments/tvb25_exit_round_prereg.md` incl. the
  2026-08-16 amendment (committed before any code; manifest pins the
  post-amendment blob sha).
- Run: 2026-08-16, `analysis/paper/tier_b_exits.py`, artifacts in
  `analysis/paper/tier_b_exits/`. All gates PASS (determinism 55 Tier B +
  88 T1-floor committed rows field-equal through the extended engine;
  entry-stream gates both families both windows; tranche reconciliation).
  Two gate-caught runner corrections were committed BEFORE the clean run
  (forward protocol): the veto-counter modulo rule, and partially-banked
  open entries contributing a phantom stream exit.
- REGENERATED 2026-08-16 under prereg amendment 2026-08-16b (TVB-25
  external-audit fold): the D14 entry-hour ruling applied (S0 arms gain
  same-bar state exits on entry-hour 2-against breaks), the D9 collision
  census repaired (transition-accumulated; the original counters
  understated P2/PX collisions and the first version of Finding 5 was
  WRONG), stop-arm entries gain the stop_src_ts audit field. Field-diff
  receipt: every other event stream is byte-identical to the first run;
  matched-entry receipts unchanged to the fourth decimal.
- Windows: July = 2026-07-06 -> 2026-08-03 (the committed comparator
  window); fresh = 2026-08-03 -> 2026-08-16 00:00 UTC (D13 pin).
- Comparators (committed, not regenerated): A0b combined +104.8 (realized
  +172.4, open drag -67.7, maxDD 122.2, 172 trades); D1 combined +83.8
  (102 trades, maxDD 22.1).

## Finding 1 -- the ladder bottom: a bare state stop transforms the
## control's SHAPE through occupancy, not through per-trade exit quality

S0a is the user-ruled 2-against state stop on the control's 1H-breakout
entries: the ONLY exit is a completed hour breaking the prior hour's
opposite extreme, filled at that hour's close (per amendment D12 this is
deliberately NARROWER than the charter 3.5 example -- the C0-pure label
is retired, and S0a is not the charter's C0 rung). Under the 2026-08-16b
entry-hour ruling the entry hour itself counts: 14 July entries (6
fresh, roster scope) land on an hour-completing bar whose hour had
already broken the opposite extreme and become one-bar scratches
(state_degenerate, counted). On July S0a books +195.3 combined against
the A0b reference's +104.8, with max drawdown 37.8 against 122.2 -- and
it does it with 877 trades against A0b's 172, a five-fold churn.

The matched-entry receipt says WHERE that comes from, and it is not exit
quality: on the 39 identities closed in every control-family arm, S0a's
exits sum to +27.4pp where A0b's sum to +34.2pp (means +0.70 vs +0.88
per trade) -- per matched trade the state stop is WORSE than the C1 exit
stack. The whole-arm reversal is the one-position book being freed every
2-against hour and recycled into the next trigger. This is the same
occupancy mechanism the TVB-23/24 matched-exit receipt isolated on the
depth arms, now appearing on the control family. Fresh window, same
shape, sharper: matched S0a +1.9 vs A0b +25.7 summed over 24 identities
(means +0.08 vs +1.07), whole-arm S0a +95.9 vs A0b +76.5 combined (the
first version of this report compared S0a's combined against A0b's
REALIZED +55.7 -- an axis error the external audit caught; the true
occupancy gap fresh is ~+19pp, not +40). Structural tag: the occupancy
mechanism is structural (it follows from the one-position book and exit
speed); the SIGN of the whole-arm advantage is sample-local.

Fees do not dissolve it at the real taker rate (D10 columns): July S0a
net +172.7 after 21.9pp of fees. The flip backstop is priced near inert
on this book: S0b minus S0a = +2.4pp July, +1.2 fresh (five/three flip
events). Extreme-number flag: +195.3 on a minimal exit is a QUESTION --
the state stop exits every adverse hour near its close, which on this
sample systematically dodged the overnight adverse runners; a regime
where 2-against hours precede continuation rather than mean-reversion
inverts it.

## Finding 2 -- the BF layer DOES earn its place over the state-stop base
## (the repaired F1 contrast), but almost entirely as book composition

S0c = state stop + BF harvest touch, the amendment's matched arm. July
+291.4 combined vs S0a's +195.3: the BF layer's standalone price on the
state-stop base is +96.1pp gross -- the largest single-layer delta this
program has measured. Fresh: +131.6 vs +95.9 (+35.7). Mechanism: 108 BF
touches collect +195.6 while S0c's remaining state exits collect only
+95.2 (S0a's state exits alone: +194.7) -- the BF touch consumes the big
winners BEFORE their state exit would, and frees the book earlier still
(982 trades). The layers do not add; they re-compose the book.

The matched receipt cuts the other way and must be said in the same
breath: on the 39 matched-closed control identities S0c is the WORST arm
in the family (+11.1) -- harvesting at the first alive line exits matched
winners early. Every point of S0c's whole-arm lead is occupancy. Note the
asymmetry with TVB-23's verdict on the PACKAGE side ("C2F does not earn
its place over C1"): there the BF layer was priced against target
ladders on a floor-vetoed book; here it is priced against a bare state
stop on the unfiltered control book. Both stand; they answer different
questions.

## Finding 3 -- the ATR stop is the first overlay that wins on BOTH the
## whole-arm and the matched-trade axis, and it wins on the control book

A0bS = the matched control plus a 3x ATR(14,1H) stop frozen at entry.
July +214.9 combined vs A0b +104.8; drawdown 55.2 vs 122.2; and on the
matched subset it ALSO wins: +50.5 vs +34.2 per the same 39 identities.
Decomposition: the stop realizes -180.0 across 60 stop exits, and buys
+408.9 of BF harvests (114 vs A0b's fewer, freed-book effect) while
cutting the open drag from -67.7 to +10.4 across 9 opens. This is the
adverse-runner class from the TVB-16/18 live weeks being amputated
mechanically. Fresh replicates the direction: +111.1 vs +76.5 whole-arm,
matched +22.9 vs +25.7 (per-trade roughly a wash fresh). Structural tag:
"cut the catastrophic runner, recycle the book" is a structural
mechanism; its measured price is sample-local. The stop_atr_unavailable
counter fired twice (SKHY's 1h archive starts 2026-07-09, so its first
July entries predate a formed ATR window) -- declared, not hidden.

## Finding 4 -- every thesis exit LOSES to plain D1 on the July package
## book, and the composite inherits the losses

Against D1's +83.8 combined (its exits: 91-97 target fills at rung 1):

- P1 (bank half at T1, run half to the BF touch): +32.5 combined. Its
  banked halves and harvests are fine (+27.3 tgt, +74.2 bf) but the
  runner halves ride brk/flip losses (-51.2 combined) and hold the book
  (37 closed entries vs D1's 102). Yet on the 26 matched-closed package
  identities P1 SUMS +18.5pp vs D1's +8.4pp (means +0.71 vs +0.32 per
  trade) -- within THIS family comparison the two-piece profile beats
  the full T1 exit per matched trade; the whole-arm loss is again
  occupancy. Comparator boundary: this ranks P1 against D1 and the other
  package-family arms on the exit round's matched set ONLY -- the
  TVB-23 depth receipt (a different matched universe) has D5 at
  +1.79pp mean per matched trade, so deeper targets still out-earn P1
  per trade on their own receipt. Fresh: matched +13.8 vs +12.9 summed
  over 15 (means +0.92 vs +0.86), whole-arm +20.9 vs +28.4.
- P2 (the user's runner profile): July +6.1 combined. The machinery
  works as ruled -- 51 banks, 49 floor exits at T1 collecting +6.0, 26
  breakeven exits collecting zero by construction, 17 BF harvests
  (+74.4) -- but brk/flip on the residues (-86.2) and deep occupancy
  (maxDD 73.4) consume it. Matched: -3.8 vs D1 +8.4 summed (means -0.15
  vs +0.32); this profile loses on BOTH axes in July. Fresh: +3.4
  whole-arm, matched +3.8 vs +12.9 summed over 15.
- X1 (no targets, BF armed only at rung 3): July -37.8 combined, maxDD
  119.0 -- the worst cell in the round. The stall mode (never reaches
  rung 3) rides unprotected into brk -47.9 and flip -31.8; only 11
  trades ever armed and harvested (+55.5). The bimodality boundary D1
  encoded is real, and this arm demonstrates its cost the hard way:
  protecting ONLY the run mode abandons the 43%-stall mode entirely.
  Matched: -24.2 summed over the 26 (mean -0.93), worst of the family.
  Fresh: realized -6.3, combined +5.5 only through open marks.
- D1i3 (+intrabar-3): -10.1 vs D1 July. The invalidation itself is small
  and behaves as designed (7 firings, -7.7pp -- cheap exits near the
  entry); the rest is composition drift on the freed book. Fresh: -5.3
  delta. The canonical invalidation exit is affordable insurance priced
  slightly negative on both samples.
- D1S (+structural/ATR stops): -33.6 vs D1 July (27 stops realizing
  -44.8). The same overlay that adds +110 on the control book COSTS a
  third of the package book's edge: the floor-vetoed, target-exited
  package book contains no catastrophic runner class to amputate, so the
  stop only clips recoverable excursions. Stop value is BOOK-DEPENDENT
  -- that is this round's cleanest mechanism statement. Fresh: -8.3
  delta, same sign.
- PX (everything on): July +35.7, fresh -3.3 -- a reading, not an
  adjudicator, and it reads as the sum of its parts' problems: the
  composite inherits P2's occupancy, the stops' clipping, and i3's
  small tax simultaneously.

## Finding 5 -- the D9 collision census answers the convention question
## (CORRECTED 2026-08-16b; the first version was wrong)

The first version of this finding claimed a maximum of six collision
bars and "no revisit indicated" -- from a broken counter that snapshot
satisfiability at bar start and could not see the classes a bar itself
arms (the external audit's HIGH finding). The corrected census
(transition-accumulated, roster scope): P2 18 July / 11 fresh, PX 25 /
12, A0bS 5 / 4, P1 1 / 1, S0b 1 / 1, S0c 1 / 0. Collisions are NOT
rare on the tranche arms -- 18 of P2's 55 July entries hit one.

What the collision_pairs decomposition adds: every bar containing the
prot+tgt pair -- 58 across the tranche arm-windows: 56 exact two-class
prot+tgt keys (18 P2-July + 19 PX-July + 10 P2-fresh + 9 PX-fresh) plus
2 three-class bf+prot+tgt supersets on PX July (membership CORRECTED
2026-08-26; the first version quoted only the exact keys as "every
prot+tgt bar") -- is the bank->floor ARM-AND-FIRE chain, where the
order is structurally forced -- the floor does not exist until the bank
arms it, so no alternative convention could change those outcomes (zero
already-armed-floor collisions were found). The genuinely
order-sensitive bars -- a stop racing a harvest/break/flip on A0bS
(bf+stop 1, brk+stop 2, flip+stop 1 July; brk+stop 1, flip+stop 3
fresh), invalidation racing a stop on PX (i3+stop 3 + 3) plus one
prot+stop, and one bf+state on S0c -- are 3-6 per arm-window, where the
ruled order fixes WHICH class fires first.

CORRECTED 2026-08-26 (TVB-26 external audit MEDIUM, reproduced before
adjudication): the earlier clause "the ruled order books the worse fill
on those by design" is FALSE as a per-bar statement. Close-evaluated
classes (i3/brk/flip/state) fill at the 5m close while stops and
protective levels fill at their level, and the close can land on either
side of the level. Committed counterexample: the PX fresh i3+stop bar
whose shared level is 1184.2 exits i3-first at the 1184.4 close --
BETTER for the long than the stop's level fill. Our independent sign
census on all six PX i3+stop bars: 4 worse / 2 better under the ruled
order; the auditor's focused replay of all 16 order-sensitive roster
bars: 7 better / 9 worse.

USER RULING (2026-08-16 on the corrected census; BASIS RE-RULED
2026-08-24 on the corrected fill evidence): the risk-first order STANDS
as a priority CONVENTION -- when one bar could fire two exits, assume
the risk exit happened first -- explicitly NOT a worse-fill guarantee.
The named alternatives remain unpriced. From 2026-08-26 the engine
emits a per-collision RECEIPT (satisfiable classes, candidate fills,
executed fill, signed deltas) into the rollups, so order-sensitivity is
priced on every future run instead of reconstructed forensically.

## Fresh-window replication of the thirteen existing arms (D8)

All five Tier B arms and all eight T1-floor arms were rerun on the fresh
window. Directionally: the controls stay positive (A0b +76.5 combined
leading the committed families again), the floored depth arms replicate
positive but shallower (D1 +28.4, D2 +35.0, monotone decay D3-D5), DINF
+19.3, A1F is the only committed arm negative (-2.8 realized), D1ATR
+21.6 with the smallest drawdown on the board (5.6). No committed-arm
sign reversals beyond A1F hovering at zero -- the July structure
broadly survives a fresh two-week sample, with the usual caveat that the
window is short and sign-indeterminate by declaration.

## Boundaries (binding)

Gross of funding; taker fees only in the D10 columns. One-position book;
every whole-arm number confounds exit quality with occupancy -- the
matched-entry receipts are the per-trade instrument and they are
survivor-shaped (identities closed in ALL family arms). 5m OHLC fills
under the declared conventions; no live-cadence claim; TV mirror and
per-arm parity gates remain ON DEMAND and no arm here is TV-valid until
its gate passes. The August month-end extension runs under the same
prereg when the month completes.
