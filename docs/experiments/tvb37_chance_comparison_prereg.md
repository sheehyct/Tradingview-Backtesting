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
