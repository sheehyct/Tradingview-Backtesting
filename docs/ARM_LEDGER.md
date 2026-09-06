# Arm Ledger -- every run, in plain trading terms

> **Why this exists (user request, 2026-08-16):** the arm codes (A0b, D1,
> P2, S0c...) are artifact vocabulary, not trading vocabulary. This file is
> the standing translation: what each arm actually DOES in trader terms,
> what it scored, and how it differs from its neighbors. It is updated
> with EVERY round, and plan-mode design sessions translate in both
> directions against it (a proposed profile is restated in trader terms
> here BEFORE it is coded).
>
> Numbers are GROSS combined percentage points (realized + open
> mark-to-market) on a one-position book, July window / fresh window
> (Aug 3-16), from the committed artifacts. They are readings, not
> rankings -- nothing in this file promotes an arm.

## The shared machinery, once

Every arm below trades the same way at the front door unless its card
says otherwise:

- **The gate:** no entry unless price is on the same side of the Daily,
  Weekly, AND Monthly opens (full timeframe continuity in that
  direction).
- **One bullet:** the book holds ONE position per symbol. An arm that
  exits faster gets to reload sooner. This matters constantly -- see
  "What Claude notices" at the bottom.
- **Control entries** ("breakout style"): buy the tick that breaks the
  prior completed hour's high (short the mirror), gate permitting.
- **Package entries** ("pattern style"): buy the trigger break of one of
  the ten STRAT setups you pre-committed (2-2 rev, 2-1-2, 3-1-2, 3-2,
  1-3, 1-2-2, 1-3-2, 3-2-2, 2-1-2 momo, 1-3-1-2) on the 1-hour,
  filtered by: skip if the nearest first target is closer than 0.25% of
  price (the "floor"), skip if a harvest line sits within 1% ahead, skip
  if a D/W/M open sits within 2% ("chop"). D1ATR swaps the fixed 1%/2%
  for ATR-scaled versions.

## The exit toolbox, in trader terms

- **Target (tgt):** take profit at a pre-drawn pivot level from the
  entry snapshot ("rung N of the ladder"). Fills only if price actually
  trades the level -- a gap past it earns nothing extra.
- **BF harvest (bf):** take profit when price touches a live broadening-
  formation line beyond the entry (the "let the structure pay you" exit).
- **Level break (brk):** bail at market when a bar CLOSES through a
  structure line against you.
- **Flip:** bail at market when D/W/M continuity fully flips against the
  position. The panic backstop.
- **State stop (state):** the minimal STRAT exit -- if a completed hour
  breaks the PRIOR hour's opposite extreme against you (a 2-down against
  a long), you're out at that hour's close. Your ruled "2-against"
  variant: a neutral inside hour does NOT exit.
- **Structural stop (stop):** the classic STRAT stop -- parked at the
  setup's anchor bar extreme (e.g. the 3's low for a 3-1-2 long). If the
  setup has no defined anchor, or the anchor sits on the wrong side of
  the fill, fall back to 3x the hourly ATR(14) below entry. Fills at the
  level; a gap through it fills at that bar's open (worse for us, on
  purpose).
- **Invalidation (i3):** if the ENTRY HOUR itself turns into an outside
  bar (takes out the prior hour's other side too), the pattern premise
  is dead -- out at market immediately. Active only during the entry
  hour.
- **Floor / breakeven (floor, be):** P2-only machinery -- see its card.

**Same-bar tie-break (the ruled 2026-08-16 order):** when several exits
could fire inside one 5-minute bar, the risk exits are checked first:
invalidation, then stop, then protective floors, then profit targets,
then BF harvest, then level break, then flip, then the hourly state
check. CORRECTED 2026-08-16b (the audit caught the counter missing
same-bar armings): collisions are actually common on the tranche arms --
18 of P2's 55 July entries hit one -- but nearly all are the
bank-then-floor chain, where the order is forced by the mechanics (the
floor does not exist until the bank arms it) and no convention could
change the outcome. Where order genuinely matters (a stop racing a
harvest, break, or flip), it is 3-6 bars per arm-window. CORRECTED
2026-08-26: risk-first does NOT reliably take the worse fill there --
exits that fill at the bar's close and exits that fill at a level rank
either way per bar (4 worse / 2 better across the six
invalidation-vs-stop bars; the auditor's 16-bar replay: 7 better /
9 worse) -- so the ruling is a safety CONVENTION ("assume the emergency
exit happened first"), re-ruled as exactly that by the user 2026-08-24.
CORRECTED 2026-08-26b (user-ruled, executable-only): a "collision" now
requires that both exits could actually FIRE on the bar. 13 of the
counted bars were really the floor arming AFTER the banks had already
consumed every tranche -- nothing left to protect, nothing fired --
and those now sit under their own counter instead (corrected counts:
P2 14 July / 9 fresh, PX 21 / 10; every surviving protective-vs-target
bar carries a real floor or breakeven fill). The receipt riding the
rollups is a FIRST-FILL diagnostic: exact where one exit would have
replaced one other exit (every genuinely order-sensitive bar found),
but on a bar that banked part at target and harvested the rest, it
does not re-price the whole alternative path -- that stays future,
prereg-gated work.

## Control family (breakout entries)

> WATERMARK 2026-09-06 (deep-dive review, reproduced): the arm-mode
> entry books the prior hour's level even when the bar had already opened
> beyond it, so 58 of 106 fresh-window A0b entries (63/123 A0bS, 81/492
> S0a, 82/492 S0b, 115/549 S0c) were filled at a price their own 5m
> candle never traded, some 4-7% better than available. Every number in
> this family is an UPPER BOUND until read beside the feasible-fill
> contrast receipt (`analysis/paper/tier_b_exits_feasible/`, engine
> `entry_fill: "feasible"` = max/min of level and open, the rule the
> package family already used; D1 is 1/39). The directions may survive;
> the magnitudes and the control-vs-package comparisons do not stand as
> written. FEASIBLE-FILL CONTRAST (run 2026-09-06, determinism gates
> PASS, combined pp, level -> feasible): July S0a 195.3 -> 159.5, S0b
> 197.7 -> 160.0, S0c 291.4 -> 155.0, A0bS 214.9 -> 88.2 (drawdown 55
> -> 73); fresh A0a 50.2 -> 19.6, A0b 76.5 -> 20.0, A0bS 111.1 -> 44.8
> (drawdown 36.5 -> 59.5), S0a 95.9 -> 69.5, S0b 97.2 -> 69.6, S0c 131.6
> -> 67.3; D1 28.4 -> 28.4 (unchanged, as expected). Readings that
> change: the BF-harvest state-stop arm S0c loses its lead over S0a/S0b;
> the ATR-stop overlay no longer halves drawdown (it deepens it); and in
> the fresh window the breakout control (+20.0) no longer leads the
> floored package (D1 +28.4). "The control still leads" (TVB-23) is
> withdrawn as a finding pending the July A0b anchor under feasible fills
> (not written by the runner; owed).

- **A0a -- "the control at 15-minute speed."** Breakout entries armed on
  the 15m clock; exits BF harvest + level break + flip. July +47.4 /
  fresh +50.2. Exists as the deployed-cadence reference.
- **A0b -- "THE control."** Same, armed on the 1-hour clock. July
  +104.8 / fresh +76.5. Every ladder-bottom and control-overlay claim is
  priced against this arm. Its known weakness: it can sit in a losing
  trade for days (July max drawdown 122pp roster-wide, and two-thirds of
  its realized edge was clawed back by open positions at window end).
- **A0bS -- "the control with a hard stop."** A0b plus a stop 3x hourly
  ATR from entry, frozen at fill. July +214.9 / fresh +111.1, drawdown
  roughly HALVED. The stops themselves lose money (-180pp July across 60
  stop-outs); the win is that each stop-out amputates a would-be
  catastrophic runner AND hands the bullet back for the next trade. The
  only overlay so far that also wins per-matched-trade.
- **S0a -- "enter on strength, leave the moment an hour closes against
  you."** Breakout entries; ONLY exit is the state stop -- INCLUDING the
  hour you entered on (ruled 2026-08-16b: enter on the last bar of an
  hour that already broke the other side and you are out at that same
  close; 14 such one-bar scratches in July, 6 fresh). July +195.3 /
  fresh +95.9 -- but 877 July trades vs A0b's 172. Per shared trade it
  exits WORSE than A0b; the whole-arm win is pure reload speed.
- **S0b -- "S0a plus the panic backstop."** State stop + flip. The flip
  fired five times in July for -3.0pp: once a state stop exists, the
  flip backstop is nearly dead weight. July +197.7 / fresh +97.2.
- **S0c -- "S0a that also cashes structure touches."** State stop + BF
  harvest. July +291.4 / fresh +131.6 -- the biggest number the program
  has produced, and the most misleading if read naively: on the shared
  trades it is the WORST control-family exit (harvests winners early);
  everything it gains is faster recycling plus free structure touches on
  a book the state stop keeps flat. Extreme number = question, not
  verdict.

## Package family (pattern entries with the floor + filters)

- **A1 -- "patterns, no filters, control exits."** July -7.7 / fresh
  +11.2. The original demonstration that raw pattern entries without the
  floor bleed.
- **A1F -- "A1 plus only the floor."** July +23.0 / fresh +5.3. The
  floor alone flips A1 positive; the S3.1 comparison lives here.
- **A2 / A3 -- "full package, take everything at T1 / at T2."** July
  +24.6 / +31.0; fresh +17.0 / +24.8. Pre-floor package generations.
- **D1 -- "the floored package, take the whole position at the first
  target."** July +83.8 / fresh +28.4. THE package comparator. Boring,
  effective, tiny drawdown (22pp July).
- **D2-D5 -- "same, but hold for rung 2/3/4/5 (fallback shallower)."**
  July +38.5 / +51.3 / +60.0 / +65.4; fresh +35.0 / +18.0 / +14.3 /
  +6.1. Deeper targets earn more per matched trade but hold the bullet
  longer; whole-arm July had the shallow-top shape for exactly that
  reason.
- **DINF -- "floored entries, never take a target, exit on structure."**
  July +19.4 / fresh +19.3.
- **D1ATR -- "D1 with ATR-scaled filters."** July +68.7 / fresh +21.6,
  smallest drawdowns on the board (10.6 / 5.6). Un-shuts-out the quiet
  symbols the fixed 2% chop filter was accidentally banning.
- **D1i3 -- "D1 plus the invalidation exit."** July +73.7 / fresh
  +23.1. The invalidation fired 7 times in July for -7.7pp: cheap, rare,
  behaves exactly as the methodology says. Costs about a tenth of D1's
  edge on this sample -- insurance priced slightly negative.
- **D1S -- "D1 plus the structural stop table."** July +50.2 / fresh
  +20.0. The SAME overlay that transformed the control book COSTS a
  third of D1's edge here: the floored, target-exited book has no
  catastrophic-runner class left to amputate, so the stop only clips
  recoverable dips. Stop value is book-dependent -- the cleanest
  mechanism statement of TVB-25.
- **P1 -- "bank half at the first target, run half to the structure
  touch."** July +32.5 / fresh +20.9 whole-arm -- but on the 26 shared
  trades it BEATS D1 (+18.5 vs +8.4 summed; +0.71 vs +0.32 per trade).
  Scope that claim carefully (audit correction): P1 wins per trade
  against D1 and the other NEW exits on this round's shared-trade set;
  the deeper D2-D5 targets still earn more per matched trade on their
  own earlier receipt (D5: +1.79 per trade). P1 loses whole-arm only
  because its runners occupy the bullet.
- **P2 -- "your runner profile, mechanized."** Skip T1; bank 40% at T2,
  20% at T3, 20% at T4, 10% at T5 (missing rungs fold into the runner);
  10% runner rides to the BF touch. After the first bank, a return to
  T1 dumps every un-hit middle at T1, and the runner is then protected
  at breakeven while still aiming for the BF line (your ruled reading
  A). July +6.1 / fresh +3.4, and it loses to D1 on the matched trades
  too (-3.8 vs +8.4 summed over the 26 shared July trades; -0.15 vs
  +0.32 per trade). On this sample the middles wait too long and
  the retrace rule sells them at the worst permitted price; the
  machinery is faithful to the rulings -- the profile itself
  underperformed. The ruled fractions are 40/20/20/10 + a 10% runner
  (2026-08-15) -- always check this card before quoting the profile from
  memory; nearby variants are easy to conflate.
- **X1 -- "no targets; only start harvesting once the trade proves
  extension (rung 3)."** July -37.8, drawdown 119 -- the worst cell of
  the round. The 43%-of-trades stall mode never reaches rung 3 and rides
  unprotected into level-break and flip losses. Protecting only the run
  mode is the wrong half of the bimodality.
- **PX -- "everything on at once"** (P2 + invalidation + stops). July
  +35.7 / fresh -3.3. A labeled composite reading only; it inherits its
  parts' problems simultaneously and never adjudicates any of them.

## Live executor family (Ruleset v1 control -> v2 arms; added 2026-09-04)

Different machine, different units. These arms run on the LIVE
hip3-executor (scanner-fed STRAT pattern entries on Hyperliquid perps, one
$0.50-risk ticket per signal, venue stop + take-profit resting, software
exits for a dead pattern and for the whole 15m/1h/4h/1d stack turning
against the trade). Numbers are net DOLLARS and percentage points on a
~$100 wallet from the closed live ledgers (weekend 1: 34 trades; round 2:
32 trades) and from the ledger REPLAY that receipts each arm before it goes
live. Readings, not rankings.

The control (Ruleset v1, 2026-08-26), once:
- **CONT-NB -- "continuations take profit at the near bank."** A
  continuation's take-profit rests at the nearest swing pivot beyond entry
  on its own timeframe. Round 2: 0 of 5 (0 of 12 cumulative).
- **DRIFT -- "don't fight BTC's day."** No crypto longs while BTC is below
  its midnight-UTC open, no shorts while above. Round 2: 72 refusals, pool
  positive only through eight trades, median refusal -0.65%.
- **RISK50 -- "every ticket risks half a dollar."** Size = $0.50 / stop
  distance, $10 to $100 notional. Round 2: 24 of 32 tickets landed
  $0.45-0.56 (21 was the 28-trade snapshot; corrected 2026-09-06); the
  clamps under- and over-risked the two tails (range $0.10-$1.49).
- **REACH -- "the target must live inside the tape's reach."** Refuse when
  the target is farther than 1.5x the coin's daily ATR. Round 2: 22
  refused, 2 would have won.
- **BELL -- "stock perps only while the stock market is open."** Weekday
  09:30-16:00 ET for EVERY xyz coin. Round 2: 2,491 aligned refusals,
  zero-mean in the census; the reject dig showed the bell also refused
  oil's and CRCL's pre-market runs.
- **SEATS2 / ARRIVAL / FAR-13 / T1 -- ** two positions at once, first
  qualified signal takes the seat, the 1-3 enters at the far side, full
  exit at the first target.

The replay receipt (ledger replay 1, 2026-09-04/05; hip3-executor
runs/2026-09-04_replay1/REPLAY.md): the control replays round 2 to the
decision -- all 22,401 refusals and admissions agree, 32 of 32 entries,
exit reasons 30 of 32 with both misses in a declared class (the scanner's
mid-union forming bar read an entry bar as a Type 3 that trade candles did
not, or the reverse), worst exit timing 2.8 min, net within $0.44 of the
venue. It took three fidelity amendments to get there, each calibrated on
served fields or journaled facts and never on outcomes: the scanner's
post-roll FREEZE (a bar that just rolled keeps showing the old bar for one
refetch sweep per timeframe, ~75 s each, so the daily dot lags ~6 min),
the BTC drift sign read from the live refusal where the row reveals it,
and matched trades freeing their seat at the journaled exit instant.
Weekend 1 replays 34 of 34 entries and 33 of 34 exit reasons but FAILS the
P&L check by $0.11 -- two thin weekend fills (PURR's entry 0.9% worse than
the decision mid, STX's stop 1.05% through the level) -- so its arm
numbers below are WATERMARKED and contrast against a v1 replay control
(net -$2.16 on 27 trades), not the v0 book that actually traded (-$6.86
on 34).

The control's replay card (round 2): 32 trades, net +$0.70, +8.5pp, 44%
winners, worst drawdown $1.43, both seats busy 95% of the window, median
hold 3.7 h.

The v2 arms (2026-09-04), one change each. Round 2 first (gate PASSED),
weekend 1 second (watermarked). "Matched" = the trades both books took;
"displaced" = control trades the arm refused; "admitted" = trades only
the arm took. Readings, not rankings.
- **A1 EXT -- "stock perps trade the extended session."** 04:00-20:00 ET
  weekdays, one window for every xyz coin. Round 2: 36 trades, net +$0.75
  vs +$0.70, +10.0pp, drawdown $1.89; 31 matched (identical), 1 displaced,
  5 admitted netting -$0.18. Only ONE bell-refused row ever became a
  trade (GOLD 1h at 19:51 ET); of the 6,358 bell refusals, 3,069 fall
  outside even the extended window, 1,159 fail the volume floor and 979
  the reward-to-risk floor. Oil and CRCL: 77 rows pass the bell under this
  arm, 39 die at the R:R floor, and the two 4h continuations that passed
  (BRENTOIL and CL, 08:06 ET Sep 1) found no seat. Weekend 1: no xyz
  trades on a weekend, identical to control.
- **A2 NODRIFT -- "crypto trades its own signals."** Round 2: 41 trades,
  net +$1.20 vs +$0.70 but -4.1pp (the dollars came from a few larger
  tickets), drawdown $2.87; 18 matched, 14 displaced (they had netted
  +$0.67), 23 admitted (+$1.17). Weekend 1: 31 trades, -$3.10 vs -$2.16,
  -17.0pp. Sign flips between ledgers: no reading.
- **A3 DWM -- "continuations need the big picture, not a reversal."**
  Round 2: 36 trades, +$1.26 vs +$0.70, +9.9pp, drawdown unchanged $1.43;
  24 matched, 8 displaced (-$0.21), 12 admitted (+$0.35). Weekend 1: 26
  trades, -$2.01 vs -$2.16; 23 matched, 4 displaced, 3 admitted. Small
  positive on both, inside the noise of a dozen trades; the D/W/M
  continuity it needs is reconstructed, never journaled.
- **A4 HTF1 -- "the bigger bar gets the seat."** Round 2: IDENTICAL to
  control -- the ranking never bound; no poll ever held two qualified
  candidates where the order changed the pick. Weekend 1: 2 swaps,
  -$2.73 vs -$2.16. Inert on these ledgers.
- **A5 HALF13 -- CORRECTED 2026-09-06.** The first receipt was empty by a
  BUG (the synthetic candidate's decision price equalled the halfway line,
  and the strict in-force gate refused every one; the "268 no longer
  beyond the line at the cross minute's close" story below was wrong).
  Re-run under amendment j (decision price = the cross minute's close):
  round 2 STILL has zero halfway entries, now for honest reasons -- of
  875 candidates, 359 fail the volume floor, 248 the bell, 109 the
  reward-to-risk floor (the halfway stop is the running extreme, the
  target bar 0's wick), 44 find no seat, 44 close back inside the line,
  41 lack the stack, 18 the drift veto; whole-arm numbers unchanged
  (+$0.36). Weekend 1 (watermarked): FIVE halfway entries (INJ 1h twice,
  BOME 1h, ACE 1d, TRX 1h), zero winners, -$1.67 on the five, arm -$5.85
  vs -$2.16 with the rest of the gap displacement. Five trades is a
  sighting, not a reading; and the candidate set is still conditional on
  the setup later completing a far-side 1-3 (prospective generator
  deferred). Original card (pre-fix, kept for the record): Round 2: 39 trades,
  +$0.36 vs +$0.70, -6.5pp; 25 matched, 7 displaced (incl. the SOL 4h
  far-side 1-3, +$0.36), 14 admitted (+$0.02). BUT zero halfway entries
  happened: of 1,217 scanner 1-3 rows, 875 could be re-timed to a
  halfway cross and every one was refused -- 359 volume floor, 248
  outside the bell, 268 no longer beyond the line at the cross minute's
  close (the D4 in-force convention). As run, this arm is "far-side 1-3
  removed", not "halfway 1-3 added"; the halfway tier cannot be receipted
  on this ledger under D4 as declared. Weekend 1: identical to control.
- **A6 WALKUP -- "your walk-up, on the timeframes that exist."** Round 2:
  35 trades, net -$1.51 vs +$0.70, +4.6pp, median hold 1.8 h (control 3.7
  h); on the 14 matched trades the walk-up gave back $1.30 (3 worse, 11
  same); 18 displaced, 21 admitted (-$1.44). Weekend 1: 27 trades, -$3.83
  vs -$2.16; on 26 matched trades -$1.94 (4 worse). Only 10 of 35 round-2
  holds printed a rung at all; the walked stop is what ends them.
  Ladder: 40 retained 4h bars, weekly from dailies (caveat).
- **A7 BANKHALF -- "half off at T1, run the rest to the next pivot."**
  Round 2: 30 trades, +$0.82 vs +$0.70, +9.9pp, 50% winners, drawdown
  $1.10 (best of the book); on 18 matched -$0.48 (2 worse); 14 displaced
  (-$0.32), 12 admitted (+$0.29). Weekend 1: -$2.21 vs -$2.16; matched
  -$0.33. Neutral on the trades it shares; the whole-book edge is the
  reshuffle.
- **A8 SEATS5 -- "five positions at once."** Round 2: 55 trades, -$0.14
  vs +$0.70, +15.2pp, drawdown $2.70, median hold 1.1 h; 14 matched, 18
  displaced (+$1.33), 41 admitted (+$0.50); the five seats were 46% busy
  (= 114% of two seats). Weekend 1: 31 trades, -$1.83 vs -$2.16. More
  trades, shorter holds, no dollar change: seats are not the constraint,
  candidate quality is.
- **A9 NETRR -- "the trade must clear the stop after fees."** Round 2: 32
  trades, +$3.30 vs +$0.70, +20.8pp, drawdown $0.94 (best), 47% winners;
  21 matched (identical, delta $0.00), 11 displaced, 11 admitted.
  CORRECTED 2026-09-06 (deep-dive review, reproduced): only SIX of the
  eleven displaced tickets fail the net floor directly (SP500 1h, TAO 1h
  twice, XMR 1h, GOLD 1h, VVV 4h; net -$0.90, INCLUDING the XMR winner
  +$0.51), and all six sat at net R:R 0.95-0.9997 -- in practice the arm
  is "gross floor about 1.07". The other five (ZEC, MORPHO, MINIMAX, MU,
  PAXG; -$0.71) left through the seat reshuffle, not fees. The 11
  admitted (CRCL 4h, KIOXIA 4h x2, PURR, PENGU, ZORA ...) added +$0.99,
  so the +$2.60 delta is 62% avoided losses, 38% admitted tickets.
  Weekend 1: 26 trades, -$0.36 vs -$2.16; 7 displaced had netted -$1.64,
  6 admitted +$0.16. Reading: the accounting argument (pay both legs'
  fees before counting the reward) stands on its own; the money argument
  is thin, in-sample, and partly replacement luck.

## What Claude notices (cross-arm, things easy to miss)

1. **The one-bullet lens explains almost every surprise.** Whenever a
   whole-arm number and the matched-trade receipt disagree, the gap is
   reload speed, not exit skill. Ask "did this exit make the trade
   better, or did it just hand the bullet back sooner?" before believing
   any headline.
2. **The same stop is medicine on one book and a tax on another.**
   Control book: +110pp. Floored package book: -34pp. Any future overlay
   should be priced per-book, never assumed to transfer.
3. **Your two profiles ranked opposite to intuition per-trade:** simple
   P1 beats D1 per matched trade; the sophisticated P2 loses to it. The
   T1-retrace rule is the main suspect -- it liquidates the middles at
   the lowest price the profile permits, exactly on the trades that
   already came back. Worth a targeted look before this becomes live
   habit.
4. **Breakeven exits look worthless in the P&L splits (zero by
   construction) -- their value is counterfactual** (what the runner
   would have lost). Never judge "be" by its column.
5. **Redundant safety layers cost nothing but add nothing:** the flip
   backstop fired 5 times in 866 S0b trades. Once a faster exit exists,
   slower backstops go inert -- fine to keep, wrong to credit.
6. **Fees do not kill churn at the real taker rate** (~1.25bp/side: 982
   trades cost ~24.6pp against +291). CORRECTED 2026-09-06 (deep-dive
   review): at the 0.1%/side assumption from the early rounds the July
   family stays POSITIVE (S0a +19.8, S0b +22.0, S0c +94.9 net of fees
   only); in the fresh window two of three go negative (S0a -2.2, S0b
   -0.9, S0c +22.1). The fee tier is load-bearing for the fresh-window
   readings, not a kill switch for the family.
7. **The invalidation exit (i3) is the best-behaved overlay:** rare,
   cheap, mechanically faithful to the methodology, and its cost is
   mostly composition drift rather than the exits themselves.

ROUND 3 RULING (user, 2026-09-05): v1 + A9 NETRR goes live; A1-A8 stay
off and are shadow-journaled for the next replay; walk-up deferred to a
daily-entries-only variant; per-coin fee rates (A9c) named-deferred (the
A9 receipt used dex-default rates -- amendment 2026-09-04i).

ROUND 3 PACKAGE (user-approved 2026-09-06 after the deep-dive fold; prereg
before code). The cards, trader terms first, numbers blank until the
round-3 ledger closes:
- **WEEK5 -- "the week has to agree too."** Enter only when the 15-minute,
  hourly, 4-hour, daily and weekly candles all lean the trade's way; leave
  when all five lean against it. Fewer candidates, more conviction; flips
  come later and fewer. The four-dot verdict rides every row as the
  counterfactual. Numbers: pending.
- **SEATS4 -- "four positions at once on $200."** More tape, not better
  tape (the five-seat replay took 55 trades for the same dollars). Numbers:
  pending.
- **RISK100 -- "every ticket risks a dollar."** Half a percent of the
  wallet, as round 2 was; the venue's $10 minimum now distorts only stops
  wider than 10%. Percent results are unchanged by construction; dollars
  double. Numbers: pending.
- **RANK (shadow only) -- "the strongest, most liquid fresh setup gets the
  seat."** Score times the log of 24-hour dollar volume, highest for longs,
  lowest for shorts, continuity as the tie-break; journaled on every row,
  receipted on the round-3 ledger before it trades. Numbers: pending.
- STRAT rulings for the next scanner release: 3-1-2 continuation target =
  the outside bar's wick first, then a higher-timeframe pattern's target;
  3-2-2 stop = the outside bar's wick; nested inside bars keep the bar the
  whole coil sits inside as bar x.

Live executor family, after ledger replay 1 (2026-09-05):
- The receipt was hard to earn and that is the finding: three fidelity
  amendments (roll freeze, drift pin, settle pin) were needed before the
  replay reproduced the live book, and each was a live-loop mechanism
  nobody had written down. Any counterfactual arm run without them would
  have been reading a different machine.
- CORRECTED 2026-09-06: A9 is NEUTRAL on matched trades (identical by
  construction); A6's loss is the only reading that shows on the matched
  axis. A9's whole-book gain is six direct refusals plus a reshuffle.
  Everything else is a reshuffle of a dozen trades around a two-seat book.
- CORRECTED 2026-09-06: A5 was empty BY A BUG (the synthetic decision
  price equalled the halfway line and the strict in-force gate refused
  every candidate; executor PREREG amendment 2026-09-06j), not by D4's
  convention -- the halfway entry had never been tested. A4 is inert as
  run (no poll ever ranked two candidates) -- an arm that never binds is
  a design fact, not a null result.
- MECHANICS (deep-dive review R1, repaired 2026-09-06): under the
  1/leverage clearance rail three round-2 stops (LITE, ACE, NBIS) and
  weekend-1's XMR rested BEYOND the venue's liquidation price; the $0.50
  ticket was not a $0.50 ticket on those. Round 3 sets the leverage per
  ticket so the stop clears and receipts the venue's liquidation price.
- Sizing makes dollars and percentage points disagree (A2: +$0.50 and
  -12.6pp vs control). Read both or neither.

## Maintenance rule

Every round: add a card per new arm (trader terms FIRST, then numbers),
update the numbers on re-run arms, and record cross-arm observations.
Plan-mode design sessions restate every proposed arm in this file's
vocabulary before the prereg is committed, and check the restatement
with the user.
