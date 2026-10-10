# TVB-37 -- the chance comparison: the same pattern with and without the stacked level -- pre-registration

**LABEL: CHARACTERIZATION, NO STRATEGY, NO P&L. Definitions fixed here BEFORE any
outcome was read. Second data product under the owner's 2026-10-04 redirect
(data first; trade the daily, weekly and monthly only; rank by levels broken
together). It asks one question: does a STRAT pattern whose trigger also takes
a higher-timeframe level ("A+ setup", the domino) have a better CHANCE than the
same pattern taking yesterday's level alone? Chance is measured in R against a
fixed stop, with counts and intervals. It ranks nothing and promotes nothing;
every cell is reported, none is picked.**

- Declared: 2026-10-10, before the script existed. Owner approval of the card
  (restated in trader terms in chat): 2026-10-10 "Full go on my end", with
  three answers folded in: (1) in-favour wiggle = YES (the higher level may sit
  at or a hair beyond yesterday's level in the trade's direction; a level a
  hair short does not count); (2) no coin-flip baseline -- the owner's
  reference is the three scenarios ("a 2 going 3"), about one in three, and
  is recorded, not asserted; (3) the stop idea "move the stop off the daily to
  the weekly, exit when a higher timeframe goes against the trade" is logged
  as the OWNER'S IDEA, not sold on it, and the setup-bar stop below is the
  primary. Sizing against liquidation by the setup bar's distance is noted
  for later, not here.
- Engine: `analysis/domino/chance.py`, reusing the audited census event
  detection (`analysis/domino/census.py: day_events`). Data: the same cached
  daily candles (`analysis/domino/data/`). Results: `analysis/domino/results/
  chance.json`, `chance_tables.md`, `trades.csv.gz` (regenerable, ignored).
  Receipt: `analysis/domino/CHANCE_RECEIPT.md`.

## Definitions (a-priori)

1. **Sample.** The census universe (292 live perps, survivors only), counted in
   the VENUE ERA: each coin from its first day with traded volume on the
   venue, because the API serves zero-volume index-price candles before that
   (census audit F11). ALL (with the index-price prefix) is reported as one
   check line, not the headline. LIQUID (census definition) is a split.
2. **Pattern unit.** Every first break of a level on the day, the week or the
   month (quarter excluded as a rule, recorded as context), as the census
   detects it: strict break, first break of the current bar only, calendar
   bars from dailies. One unit per (coin, day, direction, timeframe). A day
   that breaks yesterday's high AND last week's high is one DAILY unit and one
   WEEKLY unit; they are evaluated in their own tables and never pooled.
3. **Pattern label** = the setup kind of that timeframe's setup bar (the bar
   whose level broke) against its predecessor: 2-2 REVERSAL, 2-2
   CONTINUATION, 1-2 (inside break), 3-2 (outside break); plus the shape flag
   of the setup bar in the break's direction: NONE, THIRD (body in the far
   third, the resource's 33% rule), STRICT (THIRD and a far-side wick of at
   most one tenth of the bar's range). Named signals, for the owner:
   - **normal hammer / shooter** = REVERSAL + THIRD (or STRICT);
   - **momo hammer / shooter, 2-2 form** (owner 2026-10-10: a 2 with the trend,
     sold hard inside the bar, held the prior extreme, closed as a hammer,
     then 2 again) = CONTINUATION + THIRD (or STRICT);
   - **momo hammer / shooter, 1-2 form** (the resource's inside-bar form) =
     INSIDE + THIRD (or STRICT), kept apart from the 2-2 form.
   Setup bars with no classifiable predecessor are dropped from the pattern
   tables and counted.
4. **Stack class (the "A+" axis).** For a DAILY unit, over the daily, weekly
   and monthly levels broken that day (quarter ignored):
   - PLAIN: only yesterday's level broke (rank 1 on day / week / month);
   - EXACT, SHARED OPEN: a weekly or monthly level broke at the SAME price as
     yesterday's level and the day is that bar's calendar open (yesterday was
     the old bar's last day);
   - EXACT, PLAIN DAY: same price on any other day (yesterday retouched the
     higher level without breaking it);
   - NEAR: every higher level within 0.25% beyond yesterday's level
     (inclusive); WITHIN 1%; SPREAD (over 1%) -- the largest gap decides.
   The owner's "stacked" = EXACT or NEAR. The owner's "wiggle only in favour"
   is automatic: when both levels break for the first time on the same day,
   calendar nesting puts the higher level at or beyond yesterday's level in
   the trade's direction, never short of it (yesterday is inside the higher
   bar or closed the previous one). The engine asserts this.
   For a WEEKLY or MONTHLY unit the class is the gap between that level and
   yesterday's level the same way (EXACT at a shared open / EXACT plain day /
   NEAR / WITHIN 1% / SPREAD); there is no PLAIN class, since the day always
   breaks with it; the comparison is stacked (EXACT or NEAR) against the rest.
5. **Trade model (arithmetic only, gross, no fees or funding, no slippage).**
   Entry at the broken level L the instant it breaks (fill at L). Stop S = the
   other side of the setup bar of the pattern's timeframe (for a long off a
   daily break: yesterday's low; off a weekly break: last week's low). R =
   |L - S|; units with R = 0 are dropped and counted. Target = L + R (long) /
   L - R (short). Stop and target fill on touch (equality fills; this is an
   order, not a break, so R10 does not apply).
6. **Outcome, by horizon.** Walked on daily bars from the entry day. For each
   day in order: both S and target touched the same day = STOP (pessimistic:
   the daily candle cannot order them); S touched = STOP; target touched =
   ONE R; else continue. Horizon N = 1, 3, 5 bars of the pattern's timeframe:
   through the close of the Nth bar after the entry bar (the entry bar
   itself always included). Result per horizon: ONE R FIRST, STOPPED FIRST,
   NEITHER. A unit whose data ends before the horizon is CENSORED for that
   horizon and excluded from its denominator (counted).
7. **Follow-through.** The type of the NEXT bar of the pattern's timeframe
   relative to the entry bar: 1 (inside), 2 WITH the trade, 2 AGAINST, 3
   (both sides, the owner's "a 2 going 3"). Requires the next bar complete.
8. **Travel.** Furthest favourable and adverse excursion in R from L through
   each horizon (medians per cell).
9. **Variant stop (the owner's idea, daily units only, one table).** S_W =
   the other side of the previous complete WEEKLY bar; same arithmetic. R is
   measured to S_W, so one R is a different distance. Reported beside the
   primary, never pooled with it.
10. **Splits, fixed now:** direction (long / short); year of the entry day;
    LIQUID; the month's open relative to the trade (daily units whose month
    did not break: level on the trade's side of the month's open or not).
    The quarter state is recorded per unit, never a split that is read.
11. **Hypothesis 1 (owner, 2026-10-10, direction stated):** EXACT SHARED OPEN
    stacks have a LOWER one-R chance than the same pattern's PLAIN class and
    than its NEAR class. Evaluated per pattern label, daily units.
12. **Cell statistics.** Every proportion carries its count and a Wilson 95%
    interval; every A+ minus PLAIN difference carries a normal-approximation
    interval. Trades on the same day across coins are correlated (market-wide
    days), so per-trade intervals overstate precision: the number of DISTINCT
    ENTRY DATES is shown beside every count. Cells under 30 trades are shown
    greyed (counted, not read).
13. **Bug tests, declared:** the nesting assertion in 4; a unit's stop never
    sits on the trade's side of its entry; ONE R + STOPPED + NEITHER +
    CENSORED = n for every horizon; the daily-unit PLAIN + stack classes sum
    to the census rank counts for the same sample; hand vectors for the
    walker (same-day both-touched = stop; stop on day 2; target on day 0;
    censored), the next-bar type, the class assignment and the horizons.

## Reporting

Headline tables (VENUE ERA): for each timeframe, pattern label x stack class
with n, distinct dates, one-R chance at N = 1 / 3 / 5 with intervals, stopped
and neither shares, next-bar distribution, MFE / MAE medians. A difference
table (A+ class minus PLAIN) per pattern label. Hypothesis 1 read-out. The
variant stop table. Splits in `chance_tables.md`. The receipt opens with a
trader's glossary and leads with what the arithmetic says, and nothing more.

## Not in this product

No fees, funding, slippage, sizing or liquidation arithmetic (the owner's
sizing note is parked). No trade management beyond the fixed stop and one R:
no trailing, no higher-timeframe exit rule (the owner's "run until invalidated"
idea is recorded, not tested). No intraday ordering (the daily candle decides
pessimistically). No Underlying-RTH mirror run (the confound is stated). No
tuning of the 0.25% / 1% bands, the sliver, the horizons or the one-R target on
what the outcomes show. No cell is promoted.

## Amendment A1 (2026-10-10, post-hoc, labelled): the daily stack class is decided at ENTRY TIME

The first run classed a daily unit by which higher levels BROKE THAT DAY
(definition 4 as first written). Reading the first tables showed the defect
before any number was reported: a "spread" or "within 1%" stack under that
definition means today's range already ran through a level 1% or more beyond
the entry, so those cells select on the day's own travel, which a trader at
the daily break cannot know. Their one-R chances (60-80%) are the selection,
not a finding. The EXACT class was unaffected (both levels break at the same
instant) and the weekly / monthly classes were unaffected (at the weekly
break, yesterday's level is already behind price).

Definition 4 for DAILY units now reads: the class is the distance from
yesterday's level to the nearest weekly or monthly level that is still
UNBROKEN in its bar at the time of the daily break, whether or not today
reaches it: EXACT (same price; shared open or plain day), NEAR (within 0.25%
beyond), WITHIN 1%, else PLAIN (no fresh higher level within 1%). The
nesting argument still holds (a fresh higher level is never short of
yesterday's level; asserted). The first run's class is kept per unit as
`cls_la` and shown once, labelled as the trap, so nobody rebuilds it. Which
levels actually broke today is recorded as outcome-side information
(`stack`). The walker also records whether the stop level traded on the entry
day itself, so the size of the pessimistic same-day call is visible per cell.
The corrected numbers were not read before this amendment was written.

## Amendment A2 (2026-10-10, post-hoc, labelled): the context splits are entry-time too

The same defect sat in two recorded splits. "The month's open relative to the
trade" had an "in stack" value (the month broke today) and the quarter state
had "breaks today"; both are decided by the day's own travel and showed the
same inflated chances (60-77%) in the first corrected tables. Both splits now
use only what is known at the daily break: the broken level's side of the
month's open (with / against / unknown; equality = against) and the quarter's
state BEFORE today (unknown / already broken out the trade's way / inside with
/ inside against / opposite / both). Whether the month or quarter broke today
stays in `stack` as outcome-side information. Read before this amendment:
the first corrected tables, which are discarded; nothing in them was reported.

## Amendment A3 (2026-10-10, declared BEFORE computing): product 2b, two views of the same rows

Owner request after the receipt: an R-matched check, and the results in terms
they can see -- a hypothetical book in percent and charts ("it is hard for me
to understand the impact ... unless talking in terms of p/l or percent
performance even if it's a hypothetical account (no leverage, no fees, single
buy)"). Both are VIEWS of the unit rows product 2 already produced; no new
condition, no new cut, nothing promoted. Engine: `analysis/domino/book.py`,
reading the same units through `chance.coin_units`. Receipt:
`analysis/domino/BOOK_RECEIPT.md`.

- **R-matched check.** Within each (timeframe, setup), units are binned by
  setup-bar size (R as a percent of price) into five bins whose edges are the
  quintiles of the comparison base (PLAIN for daily units; WITHIN 1% + SPREAD
  for weekly and monthly). For each bin, stacked minus base one-R chance at 3
  and 5 bars. The R-matched difference = those bin differences weighted by the
  STACKED group's bin shares, i.e. the base reweighted to the stacked group's
  bar sizes. Reported beside the raw difference; stacked groups under 30 units
  greyed. Bins are declared here, not tuned.
- **The book view.** Every unit is traded at ONE unit of notional, long or
  short as the break's direction: no leverage, no fees, no funding, no
  slippage, every trade taken, no compounding. A trade closes at +R% of
  notional on one R, at -R% on the stop, and otherwise is marked to the close
  of the horizon's last bar (3 bars and 5 bars of the unit's timeframe);
  censored units are left out. Per cell: trades, average and median return per
  trade in percent, hit rate, expectancy in R, and on a 1,000-dollar-per-trade
  book the total and the maximum drawdown of the cumulative P/L by entry date,
  plus distinct dates. Because every trade is taken at full size, the book
  holds many positions at once and its dollar total is NOT an account balance;
  it is the sum of equal-size trades, shown so the chances can be read as
  money. The pessimistic same-day rule carries straight into it.
- **Curves and charts.** Cumulative P/L curves for a declared handful of
  cells: daily 2-2 continuation plain / exact shared open / near / within 1%;
  daily 2-2 reversal plain all vs THIRD; weekly 2-2 continuation exact shared
  open vs the rest; weekly 2-2 reversal exact shared open vs the rest. A
  private chart page renders the same numbers for the owner. The page is a
  view; `BOOK_RECEIPT.md` and `results/book_tables.md` are the record. No
  number is read from the charts that is not in the tables.

## Amendment A4 (2026-10-10, post-hoc, labelled): the second Codex audit, folded

`docs/reviews/tvb37-chance-codex-audit.md` (NEEDS-CHANGES, eight findings, no
remaining look-ahead found) changes the following, each tagged:

- **Touch fills in decimals (F1).** The target and the stop are compared to the
  bar's prices as decimals (the strings the venue prints), so a bar whose high
  is exactly one R above the entry fills. Binary floats put a few exact
  touches a hair short. The engine is re-run; moved cells are listed in the
  receipt.
- **Reporting contract, corrected (F2).** Definition 12 said every proportion
  carries an interval and every count its distinct dates. As built: the one-R
  chances and their differences carry Wilson / normal intervals; the stop,
  neither and next-bar shares are shown with the valid count they are taken
  from, without intervals, to keep the tables readable. Every table now shows
  the VALID count per horizon (censored and n/a excluded) beside the unit
  count, greys a cell when that horizon's valid count is under 30, and greys a
  difference when either side's valid count is under 30. Distinct dates are
  shown in the pattern tables; the difference tables show the two valid
  counts. This is the contract; the earlier sentence was the intent.
- **Split bookkeeping (F3).** Dropped-unit counters are universe-level and are
  printed once, under the headline sample; censored counts are computed per
  sample.
- **The original exact class was not fully clean (F6).** The first run's class
  took the largest gap among the levels that broke that day, so a same-price
  weekly stack could leave the exact cell when the day also reached a farther
  monthly level (292 of today's exact-shared units sat elsewhere). The
  entry-time class fixed this; the receipt's "exact was clean in both versions"
  is corrected to "nearly".
- **Zero-volume days (F8).** Only the prefix before a coin's first traded day
  is removed; a later zero-volume day stays in the sample.
- **Bug test 13, reconciled.** The entry-time classes partition the DAILY units
  (plain + exact + near + within 1% = all daily units after the unclassified
  and zero-R drops); they no longer map onto the census rank counts, which
  counted levels that broke. The census reconciliation is retired as a test.
- **Hypothesis 1 scope (F5).** It was declared on DAILY units. The weekly
  shared-open comparison is a descriptive result of the weekly tables, read
  with its R-matched check, not a test of hypothesis 1.
