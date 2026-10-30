# TVB-37 product 3 -- the STRAT-management book: no price stop, a bar-close exit, a ladder of structural targets -- pre-registration

**LABEL: CHARACTERIZATION, NO STRATEGY, NO P&L CLAIM. Definitions fixed here BEFORE any
outcome was read. Third data product under the owner's 2026-10-04 redirect (data first; trade
the daily, weekly and monthly only; rank by levels broken together). It asks one question that
product 2b left open: the equal-size book lost under a fixed one-R target and a setup-bar stop
while the targets were in fact reached, so the setup-bar stop is the SUSPECT. This product
trades the SAME units with no price stop, exits on a daily close against the trade with the week
against it at that close, and takes profits at a ladder of structural targets. It reports reach
rates and books in percent, on the same rows as product 2b, so the two rule sets can be read side
by side. It ranks nothing and promotes nothing; every declared variant is shown in one table and
none is picked afterwards.**

- Declared: 2026-10-11 (TVB-38), before `analysis/domino/manage.py` existed. The design was
  carded in the TVB-37 HANDOFF entry ("Context for next session") with two forks; the owner ruled
  2026-10-11: run BOTH sides of BOTH forks for the data ("I believe it involved both forks for the
  data"; "try both and see the results"), and agreed the headline combination below ("Yes we may
  proceed with this"). The restatement in trader terms (ARM_LEDGER card) was put to the owner
  before this file was committed.
- Engine: `analysis/domino/manage.py`, reading the unit rows through `chance.coin_units` and
  the audited event detection (`census.day_events`, extended to return the bar BEFORE the setup
  bar with its prices; the census is re-run offline and `splits` and `coins` must be
  byte-identical before the extension is used). Data: the same cached daily candles, run offline
  on the 2026-10-10 snapshot (`--as-of 2026-10-10`) so every count reconciles with product 2.
  Results: `analysis/domino/results/manage.json`, `manage_tables.md`, `manage_trades.csv.gz`
  (regenerable, ignored). Receipt: `analysis/domino/MANAGE_RECEIPT.md`. Tests:
  `tests/test_domino_manage.py` (hand vectors below, written before the engine runs on data).
  Chart page: the existing private page gains the management book's tables and curves.

## Definitions (a-priori)

1. **Sample and units.** Exactly product 2's: the census universe in the VENUE ERA, every first
   break of the day's, week's or month's level (quarter = context), one unit per (coin, day,
   direction, timeframe), the same pattern label (2-2 REVERSAL, 2-2 CONTINUATION, 1-2 inside
   break, 3-2 outside break), the same shape flag (NONE / THIRD / STRICT), the same entry-time
   stack class, the same drops (unclassifiable setup bar, zero setup-bar range). Entry at the
   broken level L the instant it breaks, fill at L. R keeps product 2's meaning, the distance from
   L to the far side of the setup bar, and is used here ONLY as a measuring stick for travel; no
   order sits there.
2. **No price stop.** Nothing exits a trade intraday except a target. In STRAT terms the
   setup-bar stop and the "entry bar went Type 3" invalidation are the SAME price on these units
   (the far side of the setup bar), so this book removes both; whether the entry bar went outside
   is recorded per unit (`stop0`, already in the rows) and is a declared split, not an exit.
3. **The exit (owner's rule).** At the close of a daily bar, on or after the entry day, when BOTH
   hold at that close: (a) the day closed against the trade, meaning the day's close is on the
   wrong side of the day's own open (below it for a long, above it for a short; the candle's
   colour, not whether the trade is under water); (b) the week is against the trade at that
   close, meaning that close is on the wrong side of the calendar week's open (the Monday 00:00
   UTC open; below it for a long). Equality on either test is NOT against (a close exactly on
   the open is neither colour). The exit fill is that day's close. On a Monday the day's open
   IS the week's open, so the two tests are one. The entry day counts: a break day that closes
   red with the week red exits at its own close. The week's open is read from the census's
   calendar week buckets; a unit whose walk reaches a day with no week bucket (the leading
   partial week of a coin's data) is dropped and counted.
4. **The exit clock for weekly and monthly units (fork 2).** HEADLINE: the same daily clock as
   the daily units, definition 3 unchanged ("like the daily trades": the lowest timeframe in
   the stack carries the risk; a weekly trade that checks itself only on Friday has no risk
   control for a week). DECLARED VARIANT, own-bar clock: a weekly unit exits at the close of a
   calendar week that closed against the trade (week close on the wrong side of the week's
   open) with the MONTH against the trade at that close (on the wrong side of the month's
   open); a monthly unit exits at the close of a calendar month that closed against the trade,
   with no higher confirmation (the quarter is context only, owner 2026-10-04 and 2026-10-10).
   The variant is shown in one table beside the headline clock on the SAME units at the SAME
   cap (definition 6, long cap), never pooled with the headline.
5. **The target ladder.** All levels are known at the instant of the break (nothing in the
   ladder depends on the day's own travel; the TVB-37 look-ahead lesson). Targets fill on touch
   (equality fills; an order, not a break). Every target is strictly beyond L on the trade's
   side; T1 < T2 < T3 strictly.
   - **Ladder rungs** = the weekly and monthly levels (previous complete bar's high for a long,
     low for a short) that are still UNBROKEN in their current bar at the break and sit strictly
     beyond L, sorted outward. For a daily unit the rungs are the week's and the month's; for a
     weekly unit the month's; a monthly unit has none (the quarter is excluded by ruling). The
     ladder is FIXED at entry: a week or month that rolls during the trade does not add a rung
     (a rolling ladder is a management rule for a later round). Daily pivot highs and lows are
     not rungs here (the owner's ladder language is the higher-timeframe level; a pivot
     definition would be a new knob).
   - **T1 = the pattern's own magnitude** (strat-methodology skill 5.1; the resource's
     reversal anatomy: "the target is always the high or low of the bar prior to the trigger
     bar"):
     - 2-2 REVERSAL: the far wick of the bar BEFORE the setup bar (X in X-2d-2u: X's high for a
       long, X's low for a short). The setup bar is a 2 against the trade, so X's far wick is
       never short of L; equal to L = zero magnitude, no T1, counted.
     - 1-2 inside break: the bar before the inside bar is X. X a 2 AGAINST the break
       (2d-1-2u) or X a 3 (3-1-2 either colour; the 3's extreme is the unfilled structure that
       contains the trigger): T1 = X's far wick. X a 2 WITH the break (2u-1-2u, the with-trend
       inside bar): no magnitude of its own, T1 = the first ladder rung. X an inside bar itself
       (stacked inside bars, the anchor lies further back than the two bars held): T1 = the
       first ladder rung, counted separately.
     - 2-2 CONTINUATION (fork 1, HEADLINE): no magnitude of its own ("continuation signals
       take their target from the higher timeframe"); T1 = the first ladder rung. DECLARED
       VARIANT, the measured move: T1 = L plus the two-bar range (the highest high minus the
       lowest low of the setup bar and the bar before it), projected from L on the trade's
       side. This is the smallest-footprint leg definition that uses only the bars already
       held; the resource's own examples measure a multi-bar swing, which needs a swing
       definition this product does not introduce. The same variant applies to the with-trend
       inside break (X's range projected from L). Shown in one table beside the headline,
       never pooled.
     - 3-2 outside break: no magnitude of its own; T1 = the first ladder rung.
   - **T2** = the first ladder rung strictly beyond T1; **T3** = the next. When T1 is itself a
     rung, T2 and T3 are the rungs after it. Units with no T1 (zero magnitude, or no rung for a
     ladder pattern) are counted per pattern and sit in the exit-only book only. The share of
     units with a T1, a T2 and a T3 is reported per cell ("ladder length").
6. **Cap.** HEADLINE: through the close of the 20th daily bar after the entry bar; a trade still
   open there is marked at that close and labelled OPEN. LONG CAP (the fork-2 variant table
   only, weekly and monthly units): 20 bars of the unit's own timeframe, both clocks shown at
   it. A unit whose data ends before its exit and before its cap is CENSORED, excluded and
   counted (the last 20 days before the snapshot are therefore thin).
7. **Order of events inside a day.** A target touch is intraday and the exit is at the close, so
   on any day targets are filled first, in ladder order (price must pass T1 to reach T2), then
   the exit test runs on the close. On the entry day the break precedes any target touch (a
   perp's daily bar opens at the prior close, inside the setup bar's range for a daily unit and
   at or below a weekly or monthly level that first breaks that day), so no pessimistic
   ordering is needed. Nothing here has a stop to race.
8. **Per-unit record.** Entry date, L, R, the targets T1 / T2 / T3 with their sources (anchor
   wick / week level / month level / measured move), the day each was touched, the exit day and
   close (headline clock), the own-bar exit day and close (variant), the cap mark, days held,
   MFE and MAE in R and in percent of L through the exit and through the cap, the entry-time
   context already in the rows (class, flag, month-open side, quarter state, `stop0`) and a new
   entry-time field: the week's side (`w_support`: L on the trade's side of the week's open =
   with; equality = against, the census F7 convention).
9. **Reach rates.** Per cell, with counts and Wilson 95% intervals: the share of units with a T1
   that touched it BEFORE the exit (and before the cap); of those, the share touching T2 before
   the exit (units with a T2); of those, T3. Beside each: the same shares with no exit at all,
   touched any time inside the cap (the ceiling the exit is measured against).
10. **How the pre-T1 exits died.** For units exited before T1: the share exiting at the entry
    day's close, the distribution of days held, the exit return in R and in percent, the share
    whose entry day had gone outside (`stop0`), and the share that then touched T1 inside the cap
    AFTER the exit (the exit's own "saw the target anyway" number, the counterpart of product
    2's stopped-then-reached share). Per cell, cells under 30 greyed.
11. **Where the no-stop book bleeds.** The distribution of MAE in R at the exit (shares beyond
    1R, 2R, 3R), the worst single trade per cell, and the share of trades held to the cap. These
    are the kill views: a book without a price stop lives or dies on its tail.
12. **The books (percent, equal size).** Every unit is traded at ONE unit of notional, long or
    short as the break; no leverage, fees, funding or slippage; every trade taken; no
    compounding; a trade's return = the signed move from L to its fill in percent of L. Per
    cell: trades, average and median return per trade, hit rate (closed in profit), total and
    maximum drawdown from zero on a 1,000-dollar-per-trade book by entry date, median days held,
    distinct entry dates. Four books on the SAME rows (units with a T1), plus the exit-only
    book on all units as one extra line:
    - **A, all out at T1:** fill at T1 when touched before the exit; else the exit close; else
      the cap mark.
    - **B, hold through T2 with the exit:** T1 is passed through; fill at T2 when touched
      before the exit; else the exit close; else the cap mark. A unit with no T2 is an exit-only
      trade inside book B (its share is shown).
    - **C, exit only:** the exit close, else the cap mark. No target.
    - **D, one R or the exit (the lead's addition, declared):** product 2's one-R target with
      the close exit in place of the setup-bar stop. Same entry, same target, only the loss side
      changes: this is the direct test of the suspect. The owner may strike it.
    - **Reference, product 2b on the same rows:** one R or the setup-bar stop, marked at the
      fifth bar of the unit's timeframe (the rows' existing `ret5`), so the comparison is on
      identical units. Holding periods differ between the books (shown), and the reference also
      differs in its target horizon, so "A beats the reference" is rule against rule, not the
      stop alone; book D is the stop-only comparison.
13. **Hypotheses (direction stated before running).**
    - **H2 (the owner's suspect, from product 2b):** on plain daily units, book D's average
      return per trade is higher than the reference's for every pattern label.
    - **H3 (the lead's counter, explore-to-kill):** the close exit is itself an early exit: the
      share of pre-T1 exits that touch T1 inside the cap after exiting is at least as large as
      product 2's stopped-then-reached share (a third to a half).
    Both are read from the headline tables with their intervals; neither promotes anything.
14. **Splits, fixed now:** direction; year of entry; LIQUID; stack class (the A+ axis, same
    cells as product 2); shape flag; the month's side at entry (`m_support`); the week's side at
    entry (`w_support`, new); the entry day went outside (`stop0`). The quarter state is
    recorded, never read as a split.
15. **Cell statistics.** Counts and Wilson intervals on every reach share; the number of
    distinct entry dates beside every count (market-wide days are correlated); cells under 30
    units greyed (counted, not read); differences between books on the same rows carry a
    paired-difference normal interval.
16. **Hand vectors, declared** (`tests/test_domino_manage.py`, written before the data run):
    (1) Monday entry, entry day closes red: exit at the entry close, the two tests are one;
    (2) Tuesday entry, day red but week still green at that close: no exit; next day red with
    week red: exit at that close; (3) T1 touched on day 2, exit on day 4: book A fills at T1,
    books B and C at the day-4 close, reach flags set; (4) T1 touched and the exit on the same
    day: A at T1, B at that close; (5) a 2-2 reversal whose anchor wick equals L: no T1, counted,
    exit-only book only; (6) a daily continuation at an exact weekly stack: the weekly level at L
    is not a rung, the monthly level beyond is T1, no T2; (7) a reversal whose ladder rung sits
    at or inside T1: skipped, T2 strictly beyond T1; (8) no exit through bar 20: marked at bar
    20's close, OPEN; (9) data ends at bar 7 with no exit: CENSORED, counted; (10) close equal to
    the week's open or the day's open: not against, no exit; (11) a weekly unit: daily clock
    exits at a Wednesday close, own-bar clock exits at the week's last close only when the week
    closed red with the month red; (12) measured move: the two-bar range projected from L, and
    X's range for the with-trend inside break; (13) a 1-1-2 (stacked inside): first rung as T1,
    counted separately; (14) book D: one R touched before the exit = +R, exit first = the exit
    close; (15) the week's side at entry with equality = against.
17. **Bug tests, declared:** reached-T1 + died-before-T1 + OPEN + CENSORED = n per cell; T2
    reached is a subset of T1 reached, T3 of T2; every target strictly beyond L and T1 < T2 <
    T3; every exit close is strictly against on both tests; exit day >= entry day; book C's
    return equals the signed move L to the exit close; for units with no T2, book B equals book
    C row by row; the census `splits` and `coins` are byte-identical before and after the
    `day_events` extension; the unit count and every entry-time field equal product 2's for the
    same snapshot.

## Reporting

Headline tables (VENUE ERA, daily clock, 20-daily-bar cap): per timeframe, pattern label x
stack class: n, distinct dates, ladder length, T1 / T2 / T3 reach before the exit with intervals
and the no-exit ceiling, pre-T1 death table, MAE tail, days held, and the five book lines (A, B,
C, D, reference) in percent with totals and drawdowns. The fork-1 variant table: the
continuation's and the with-trend inside break's T1 as the measured move, beside the headline, on
the same units. The fork-2 variant table: weekly and monthly units at the long cap, daily clock
beside own-bar clock. Hypothesis read-outs H2 and H3. Splits in `manage_tables.md`. Curves for a
declared handful of cells (books A / B / C / D / reference on one axis each): daily 2-2 reversal
plain; daily 2-2 continuation plain; daily inside break plain; daily 2-2 continuation near
(the one A+ in the black); weekly 2-2 continuation shared open against the rest, book C. The
receipt opens with a trader's glossary and leads with what the arithmetic says, and nothing more.

## Not in this product

No fees, funding, slippage, sizing or liquidation arithmetic (a no-stop book at any leverage
has a liquidation question the receipt states and does not answer). No intraday ordering (the
daily candle decides; here nothing races). No scaling (half at T1 and the rest held is a later
variant if asked). No rolling ladder, no daily pivots, no quarter rung. No Underlying-RTH mirror
run (the confound is stated). No tuning of the cap, the leg definition, the rung set or the exit
tests on what the outcomes show. No cell is promoted; the hierarchy rulings the owner deferred
(who owns the stop in a stack, whether continuation breaks rank, seat competition, which
higher-timeframe event ends a trade) are read from these tables in a design session, not
decided by the engine.

## Amendment A1 (2026-10-11, post-hoc, labelled): the Codex audit of the build, folded

`docs/reviews/tvb38-codex-audit.md` (NEEDS-CHANGES; F1 F2 HIGH, F3-F7 MEDIUM, F8 LOW; no
look-ahead and no T1-rule error found) changes the following, each tagged. The engine was rerun;
the receipt lists every number that moved.

- **Projected targets in the venue's decimals (F1).** One R and the measured move were built
  as binary floats, so an exact touch could land a hair beyond the printed price and miss. Both
  are now built in decimals exactly as the chance walker builds its target; hand vectors for the
  exact touch, long and short, and for the measured move were added.
- **Book D5, the stop-isolating line (F2).** Definition 12 called book D "only the loss side
  changes"; D also extends the horizon from the reference's five bars to the 20-day cap, so its
  difference includes returns earned after the reference marked. A sixth book, **D5 = one R or
  the exit, settled at the reference's own five-bar horizon**, is added on the same rows: the
  same target, the same horizon, the same mark day, only the stop swapped for the close exit.
  H2 is read on D5 first and on D second. The fee sentence is corrected: the fee is per fill,
  not per day held.
- **H3 on matched cohorts and windows (F2, F3).** The chance book's "stopped, saw one R" is read
  on units with a T1 over its five-bar travel; book D's early-exit counterpart was read on every
  unit over 20 days, and the 20-day follow-up flags were set FALSE when the cap was not yet
  reachable in the data. Now: `later_r5` = D5's exits before one R that touched one R inside the
  same five bars, on the T1 cohort (the like-for-like H3 read); the 20-day flags (`later1`,
  `later_r`) are UNKNOWN (null, excluded from the denominator) when the 20-day follow-up is
  incomplete, and reported as such.
- **Each book's own holding time (F4).** "Median days" showed the exit-only duration for A, B
  and D and a constant five for the reference. Each book now records the day its target filled,
  else its exit or mark day; the reference its own stop / one-R / fifth-bar day (the stop first,
  or the same day as one R, as the chance walker decides it).
- **Exit-only cells keep their line (F5).** Cells with no five-book cohort (every monthly
  continuation and outside-break cell) dropped out of the book tables; the "C on every unit"
  line is now printed regardless.
- **LIQUID is retrospective (F6).** The census's LIQUID label is the median notional over the
  LAST 30 days of the snapshot, inherited for parity with products 1 and 2; the split footnote
  says so and the split is not read as entry-time information.
- **Receipt sentences corrected against the tables (F7):** the weekly / monthly sentence
  narrowed (the weekly continuation within 1% beat the reference under B and C); the own-clock
  count stated by the mean and by the interval; the direction and year bullets rewritten from
  the split table's actual columns (A, C, D, reference; there is no B column); the entry-day-
  outside ranges include every pattern; "the median trade loses in every book that holds past
  T1" narrowed to B and C.
- **Page (F8):** hypothesis-table rows and share cells fade on their own denominators.
- **Vectors (audit open questions):** v7's setup bar had an open above its high (fixed); v10's
  two equality tests are now each tested alone; v11 tests the month veto on its own; v5 / v9 /
  v13 assert their counters; decimal-touch vectors long and short added.
- **Noted, not changed:** the entry day's adverse extreme is counted in MAE although a daily bar
  cannot say whether it came before the break; the tail is therefore a conservative daily-bar
  bound (receipt limitation added).

## Amendment A2 (2026-10-12, TVB-39, declared BEFORE code): the lead's five candidates, on the owner's word

The owner: "You may run your 'would test next'" (2026-10-12). Each candidate is ONE change to
the headline book on the SAME units and is reported beside the headline as a declared variant.
None is a tuning pass; nothing is promoted; the owner reads the numbers themselves. Plain-English
restatements first, then the definitions, then the readings declared before the run.

**In trader terms.** (1) Only take the trade when the week is already on your side at the
break. (2) Manage the trade on the hourly instead of waiting for the daily close: get out on the
first red hour while the day is red (mirror for shorts). (3) Take half off at the first target
and let the rest ride to the exit. (4) Charge the venue's real taker fee on both legs of every
book. (5) Read "against" as "under water": the day closed through your entry price, not merely
a red candle.

### A2.1 The week's side at entry, as a condition

- Already recorded per unit as `w_support`: WITH when the entry price is on the week's side of
  the Monday 00:00 UTC open (long above it, short below it), AGAINST otherwise. Known at the
  break; no engine change.
- The condition's book = every headline book (A, B, C, D, D5, reference) on the WITH rows; the
  AGAINST rows are printed beside it. Per kind, plain daily, the book cohort (a T1 and a
  reference return).

### A2.2 The hourly exit clock

- Data: the venue's closed 1h candles, cached stamped like the daily (`*_1h_<stamp>.json`; the
  venue serves at most the most recent 5000 hours, about 208 days), normalised the same way
  (hour starts only, the forming hour cut, the last copy of a duplicate wins).
- Rows: units whose entry day lies inside the hourly window and whose entry hour exists; a unit
  with no hour that reached the level on the entry day is dropped and counted. The hourly arm is
  therefore a SUBSET of the headline's rows; every comparison is paired on that subset only.
- Entry hour: the first hour of the entry day whose high reached the level (long) or whose low
  reached it (short); the fill stays L.
  *Clarified 2026-10-30 after the TVB-39 external audit (F1-F3; wording, not a rule change: the
  intent was always the census's strict break): "reached" means traded strictly THROUGH the level;
  an hour whose high (low) merely equals the level is not the entry hour, while target, one-R and
  stop touches stay inclusive. The entry day must be observed from its first hour through the
  entry hour without a gap, otherwise the unit's hourly result is "partial entry day" (counted,
  excluded; the daily unit is untouched). The scan ends at the cap day's 23:00 timestamp whatever
  candles exist; a missing hour before the exit censors the unit; elapsed hours are timestamp
  differences. The hourly rows, counts and A2.2 tables were rerun under this reading on
  2026-10-30; the daily headline did not move.*
- Exit: the first hour, the entry hour included, whose close is against its OWN open (strict)
  AND against the DAY's open (strict; the daily bar's open of that UTC day). The clock steps
  down one rung as a whole: the headline tests the day and its parent the week, the hourly tests
  the hour and its parent the day. The week is not tested. Fill = that hour's close.
- Targets: the same prices as the headline (T1, one R); a target fills on the first hour that
  touched it, the entry hour or later (equality fills). [Corrected while writing vector v17,
  before the run was read: a target on the trade's side cannot be touched before the level, so
  "before the entry hour" is empty; the ordering that DOES differ is on the exit day, where the
  daily bar fills a target touched any time that day ("targets are intraday") and the hourly
  clock fills only a touch at or before the exit hour.] The hourly books therefore differ from
  the daily books by the clock AND by this ordering; the receipt says so.
- Cap: the last hour of the headline's twentieth day after entry (status OPEN, marked at that
  hour's close); CENSORED when the hourly data ends first.
- Books on the hourly clock: C_h (exit only), A_h (all out at T1), D_h (one R or the exit),
  each paired with C, A, D on the same rows. Recorded per row: the entry hour, the exit hour,
  hours held, the T1 touch hour.

### A2.3 Half at T1 (book E)

- E = half the position filled at T1 when T1 is touched on or before the exit day (the
  headline's A fill), the other half at the exit-only fill (C): E = (A + C) / 2 when A hit its
  target, else C. On the T1 cohort, from the recorded columns; no engine change.

### A2.4 Fees at the venue's taker rate

- Per fill, in percent of L: main dex 0.0432, xyz dex 0.0125 (TVB-2's measurement by the
  venue's own `crossed` flag; the published base-tier figure for native crypto, the
  notional-weighted figure for xyz). Every book is two fills (one entry, one exit; A and D fill
  their target or the exit, never both): net = gross - 2 x taker. Applied to every line,
  including the reference and book E; the paired stop-swap difference is fee-neutral by
  construction (both sides pay the same), so only the sign of each line is at stake.

### A2.5 "Against" read as under water

- Exit at the first daily close THROUGH the entry price (long: close under L; short: close over
  L; equality is not through) AND the week against at that close (the headline's second test,
  unchanged: close under the Monday open for a long, over it for a short). The entry day can
  exit. Fill = that close. The candle's colour is not tested.
- Books C_u, A_u, D_u, each paired with C, A, D on the same rows; days held and the adverse
  travel to the exit recorded (the tail moves when the exit waits).

### Readings declared before the run

- **R1 (week side).** WITH beats AGAINST on books A and C for every plain daily kind (the T1
  reach gap seen in the splits, 39 vs 15 percent on the continuation, says so). If AGAINST wins
  anywhere, the split was outcome noise, not a condition.
- **R2 (hourly clock).** No prediction on the sign. Declared expectation: the hourly exits
  sooner (fewer hours held than the daily's days x 24), the exit-only book loses less per losing
  trade, and fewer trades reach T1 before the exit. Read C_h - C and A_h - A paired.
- **R3 (half at T1).** E sits between A and C on every kind.
- **R4 (fees).** Every plain daily book line within one round trip of zero gross is read as
  flat net; the lines that stay positive net are listed, nothing else is claimed.
- **R5 (under water).** The lead's call: the under-water exit holds longer, reaches T1 more
  often, and loses MORE on the exit-only book (C_u < C) with a fatter tail (more trades past one
  R against). If C_u > C the candle-colour exit was too quick and the lead was wrong.

### Bug tests (hand vectors, before the run)

- v16 under water: a long whose first day closes red but above L does not exit; a day that
  opened under L and closed green but under L, with the week against, exits at that close; the
  colour clock on the same bars gives a different day.
- v17 hourly: the entry hour is the first hour whose high reaches L; a target touched on the
  exit day AFTER the exit hour does not fill (corrected as above); a red hour while the day is green does not exit; the first
  red hour with the day red exits at that hour's close; the hourly cap marks at the last hour of
  the twentieth day; a coin with no hourly bars yields no hourly rows and the headline rows are
  unchanged.
- v18 arithmetic: book E and the fee arithmetic on fixed rows, main and xyz rates.
- v19 the with / against condition counts on a fixture.

### Not in A2

No hourly ENTRY (the entry stays the daily level, the hourly only times the exit). No hourly
clock on weekly or monthly units beyond what the subset holds (reported only for plain daily).
No funding, slippage or sizing. No combination of candidates (each is one change; a package is a
later declaration).
