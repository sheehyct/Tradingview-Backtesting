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
- Windows: July = 2026-07-06 -> 2026-08-03 (the committed comparator
  window); fresh = 2026-08-03 -> 2026-08-16 00:00 UTC (D13 pin).
- Comparators (committed, not regenerated): A0b combined +104.8 (realized
  +172.4, open drag -67.7, maxDD 122.2, 172 trades); D1 combined +83.8
  (102 trades, maxDD 22.1).

## Finding 1 -- the ladder bottom: a bare state stop transforms the
## control's SHAPE through occupancy, not through per-trade exit quality

S0a is the charter's never-run C0 rung mechanized: control 1H-breakout
entries whose ONLY exit is the ruled 2-against state stop (a completed
hour breaking the prior hour's opposite extreme, exit at that hour's
close). On July it books +194.8 combined against the A0b reference's
+104.8, with max drawdown 37.8 against 122.2 -- and it does it with 866
trades against A0b's 172, a five-fold churn.

The matched-entry receipt says WHERE that comes from, and it is not exit
quality: on the 39 identities closed in every control-family arm, S0a's
exits collect +27.4 where A0b's collect +34.2 -- per matched trade the
state stop is WORSE than the C1 exit stack. The whole-arm reversal is the
one-position book being freed every 2-against hour and recycled into the
next trigger. This is the same occupancy mechanism the TVB-23/24
matched-exit receipt isolated on the depth arms, now appearing on the
control family. Fresh window, same shape, sharper: matched S0a +1.9 vs
A0b +25.7 per-trade, whole-arm S0a +96.1 vs +55.7. Structural tag: the
occupancy mechanism is structural (it follows from the one-position book
and exit speed); the SIGN of the whole-arm advantage is sample-local.

Fees do not dissolve it at the real taker rate (D10 columns): July S0a
net +172.6 after 21.7pp of fees. The flip backstop is priced near inert
on this book: S0b minus S0a = +2.5pp July, +1.2 fresh (five/three flip
events). Extreme-number flag: +194.8 on a minimal exit is a QUESTION --
the state stop exits every adverse hour near its close, which on this
sample systematically dodged the overnight adverse runners; a regime
where 2-against hours precede continuation rather than mean-reversion
inverts it.

## Finding 2 -- the BF layer DOES earn its place over the state-stop base
## (the repaired F1 contrast), but almost entirely as book composition

S0c = state stop + BF harvest touch, the amendment's matched arm. July
+291.1 combined vs S0a's +194.8: the BF layer's standalone price on the
state-stop base is +96.2pp gross -- the largest single-layer delta this
program has measured. Fresh: +131.8 vs +96.1 (+35.7). Mechanism: 109 BF
touches collect +196.6 while S0c's remaining state exits collect only
+93.8 (S0a's state exits alone: +194.2) -- the BF touch consumes the big
winners BEFORE their state exit would, and frees the book earlier still
(971 trades). The layers do not add; they re-compose the book.

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
  identities P1 collects +18.5 vs D1's +8.4 -- per matched trade the
  two-piece profile BEATS the full T1 exit; the whole-arm loss is again
  occupancy. Fresh: matched +13.8 vs +12.9, whole-arm +20.9 vs +28.4.
- P2 (the user's runner profile): July +6.1 combined. The machinery
  works as ruled -- 51 banks, 49 floor exits at T1 collecting +6.0, 26
  breakeven exits collecting zero by construction, 17 BF harvests
  (+74.4) -- but brk/flip on the residues (-86.2) and deep occupancy
  (maxDD 73.4) consume it. Matched: -3.8 vs D1 +8.4; this profile loses
  on BOTH axes in July. Fresh: +3.3 whole-arm, matched +3.8 vs +12.9.
- X1 (no targets, BF armed only at rung 3): July -37.8 combined, maxDD
  119.0 -- the worst cell in the round. The stall mode (never reaches
  rung 3) rides unprotected into brk -47.9 and flip -31.8; only 11
  trades ever armed and harvested (+55.5). The bimodality boundary D1
  encoded is real, and this arm demonstrates its cost the hard way:
  protecting ONLY the run mode abandons the 43%-stall mode entirely.
  Matched: -24.2, worst of the family. Fresh: realized -6.3, combined
  +5.5 only through open marks.
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

The risk-first pessimistic same-bar precedence was PROVISIONAL pending
evidence it distorts. It does not: across all ten new arms and both
windows the maximum number of bars with two simultaneously satisfiable
exit classes in any arm-window is SIX (PX July); most cells show zero or
one. The ruled convention's bite is negligible on this data; no revisit
is indicated.

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
