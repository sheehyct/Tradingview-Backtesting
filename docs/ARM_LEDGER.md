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
could fire inside one 5-minute bar, we assume the worst order for us:
invalidation, then stop, then protective floors, then profit targets,
then BF harvest, then level break, then flip, then the hourly state
check. The collision counter (D9) shows this near-never matters in
practice (max 6 bars in any arm-window so far).

## Control family (breakout entries)

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
  you."** Breakout entries; ONLY exit is the state stop. July +194.8 /
  fresh +96.1 -- but 866 July trades vs A0b's 172. Per shared trade it
  exits WORSE than A0b; the whole-arm win is pure reload speed.
- **S0b -- "S0a plus the panic backstop."** State stop + flip. The flip
  fired five times in July for -3.0pp: once a state stop exists, the
  flip backstop is nearly dead weight. July +197.3 / fresh +97.3.
- **S0c -- "S0a that also cashes structure touches."** State stop + BF
  harvest. July +291.1 / fresh +131.8 -- the biggest number the program
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
  touch."** July +32.5 / fresh +20.9 whole-arm -- but on the shared
  trades it BEATS D1 (+18.5 vs +8.4 July). The simple two-piece is the
  best per-trade package exit measured so far; it loses whole-arm only
  because its runners occupy the bullet.
- **P2 -- "your runner profile, mechanized."** Skip T1; bank 40% at T2,
  20% at T3, 20% at T4, 10% at T5 (missing rungs fold into the runner);
  10% runner rides to the BF touch. After the first bank, a return to
  T1 dumps every un-hit middle at T1, and the runner is then protected
  at breakeven while still aiming for the BF line (your ruled reading
  A). July +6.1 / fresh +3.4, and it loses to D1 on the matched trades
  too (-3.8 vs +8.4 July). On this sample the middles wait too long and
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
6. **Fees do not kill churn at the real taker rate** (~1.25bp/side: 971
   trades cost ~24pp against +291). At the 0.1% fee assumption from the
   early TVB rounds the whole state-stop family would flip negative --
   the fee tier is load-bearing for every high-churn reading.
7. **The invalidation exit (i3) is the best-behaved overlay:** rare,
   cheap, mechanically faithful to the methodology, and its cost is
   mostly composition drift rather than the exits themselves.

## Maintenance rule

Every round: add a card per new arm (trader terms FIRST, then numbers),
update the numbers on re-run arms, and record cross-arm observations.
Plan-mode design sessions restate every proposed arm in this file's
vocabulary before the prereg is committed, and check the restatement
with the user.
