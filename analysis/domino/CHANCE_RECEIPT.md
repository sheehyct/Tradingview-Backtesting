# The chance comparison -- RECEIPT (TVB-37, 2026-10-10)

**What this is:** arithmetic on outcomes, pre-registered in
`docs/experiments/tvb37_chance_comparison_prereg.md` (owner go 2026-10-10 "Full go on my end";
amendments A1 and A2 appended the same day, labelled, before the numbers below were read). It
asks one question: does a STRAT pattern whose trigger also sits on a higher-timeframe level (the
"A+" setup, the domino) have a better CHANCE of one R before its stop than the same pattern taking
yesterday's level alone? **Gross, no fees or funding, no sizing, no management, no P&L.** Engine:
`analysis/domino/chance.py` (event detection shared with the audited census); tests
`tests/test_domino_chance.py` (9 hand vectors); every table for every split and sample:
`results/chance_tables.md`; headline cells: `results/chance.json`; the unit rows:
`results/trades.csv.gz` (regenerable, not committed).

**The defect found and fixed before reporting (amendments A1, A2):** the first run classed a daily
unit by which higher levels BROKE THAT DAY. A trader at the daily break cannot know that, and the
"spread" and "within 1%" classes under that rule select on the day's own travel: they showed
one-R chances of 60-80%, an artifact. The class is now the distance to the nearest UNBROKEN
weekly or monthly level at the moment of the daily break, whether or not the day reaches it. The
same leak sat in two context columns (the month "in stack", the quarter "breaks today") and was
removed. The first version is kept in the tables once, headed TRAP, so nobody rebuilds it. The
weekly and monthly units were clean by construction (at the weekly break, yesterday's level is
already behind price). The exact same-price stack was clean in both versions (both levels break at
the same instant).

## Trader's glossary for the tables

| term | what it means on the chart |
|---|---|
| unit | one break of one level on one timeframe for one coin and direction: the day's (yesterday's high or low), the week's (last week's), the month's (last month's). A day that takes yesterday's high AND last week's high is one daily unit and one weekly unit, kept in separate tables |
| setup | what the bar whose level broke was, against its predecessor: 2-2 reversal, 2-2 continuation, inside break (1-2), outside break (3-2) |
| flag | the shape of that setup bar in the break's direction: none, THIRD (closed in its far third: hammer on an up break, shooter on a down break), STRICT (THIRD and only a sliver of wick on the far side). THIRD rows include the STRICT ones |
| normal hammer | a 2-2 reversal whose setup bar is THIRD or STRICT. momo hammer, 2-2 form = a 2-2 continuation whose setup bar is; momo hammer, 1-2 form = an inside bar that is |
| plain (daily units) | no unbroken weekly or monthly level within 1% beyond yesterday's level: the trigger stands alone |
| exact, shared open | yesterday's level IS last week's or last month's level and today is Monday or the 1st: yesterday closed the old bar on its extreme |
| exact, plain day | same price on any other day (yesterday retouched the higher level without breaking it) |
| near / within 1% | an unbroken higher level sits up to a quarter percent / up to one percent beyond yesterday's level, in the trade's direction (it can never sit short of it) |
| spread (weekly and monthly units only) | yesterday's level sat more than 1% inside the higher level: the day had already run 1%+ before the higher level broke |
| stacked | exact or near, the owner's definition |
| entry, stop, R, one R | buy or sell at the broken level the instant it breaks; stop at the other side of the setup bar; R = that distance; one R = the same distance beyond the entry. Orders fill on touch |
| one R by 1 / 3 / 5 | the share of units whose target traded before the stop, by the close of the 1st / 3rd / 5th bar of the unit's timeframe after the entry bar (the entry bar counts) |
| stopped by 5 | stop traded first within the same window; the rest is neither |
| stop traded on entry day | the stop level traded on the entry day itself. The daily candle cannot say whether that was before or after the break, so it counts as a stop (pessimistic). The owner's "a 2 going 3" |
| next bar with / against / inside / outside | what the next bar of the unit's timeframe did against the entry bar: broke it the trade's way, the other way, stayed inside, or both ways |
| median R % | the setup bar's range as a percent of price: how far the stop sits |
| [lo, hi] | 95% interval per unit. Units on the same day across coins move together, so read them with the distinct-date count |
| censored | the data ended before the horizon; excluded from that horizon's count |
| variant stop | the owner's idea: stop at the other side of last week's bar instead. R is then a different distance, so one R is a different target |

## Sample and bookkeeping (VENUE ERA: each coin from its first traded day)

| | daily units | weekly units | monthly units |
|---|---|---|---|
| units | 153,931 | 21,520 | 4,462 |
| censored by 5 bars | 1,371 | 1,659 | 1,218 |

292 coins. Dropped and counted: 779 setup bars without a classifiable predecessor, 25 zero-range
setup bars, 0 nesting violations, 0 days skipped, 9,052 daily units whose variant stop sat on the
wrong side of the entry (last week's bar entirely beyond yesterday's). LIQUID (141 coins, 85,501
units) and ALL (with the index-price prefix, 232,085 units) are in `chance_tables.md`; their
headline shares sit within two points of the venue era everywhere a cell has 100+ units.

Daily units by class: plain 143,423; exact at a shared open 4,261; exact on a plain day 40; near
1,410; within 1% 4,797. Exact shared-open stacks are almost all 2-2 continuations (3,619) and
outside breaks (633): yesterday closed the bar on its extreme, so it was a 2 or a 3, not a
reversal setup. The reversal and inside-bar stacks are thin (reversal near 148; inside near 231).

## Daily units: the same pattern, plain against stacked (all flags; one R by 1 / 3 / 5 bars)

| setup | class | n | one R by 1 | by 3 | by 5 | stopped by 5 | stop on entry day | next bar against | median R % |
|---|---|---|---|---|---|---|---|---|---|
| 2-2 reversal | plain | 43,809 | 24.8% | 34.3% | 38.2% | 51.7% | 25.9% | 26.9% | 5.95 |
| 2-2 reversal | near | 148 | 27.7% | 37.8% | 38.4% | 53.4% | 32.4% | 25.7% | 4.67 |
| 2-2 reversal | within 1% | 750 | 26.7% | 33.5% | 35.5% | 56.8% | 33.1% | 27.8% | 3.73 |
| 2-2 continuation | plain | 55,976 | 24.8% | 34.4% | 39.1% | 46.0% | 18.3% | 31.7% | 6.88 |
| 2-2 continuation | exact, shared open | 3,619 | 26.6% | 32.9% | 36.9% | 50.7% | 19.5% | 34.0% | 7.20 |
| 2-2 continuation | near | 804 | 31.5% | 40.8% | 46.1% | 41.7% | 19.8% | 28.0% | 4.91 |
| 2-2 continuation | within 1% | 2,555 | 30.0% | 38.6% | 43.4% | 44.6% | 20.7% | 30.6% | 5.11 |
| inside break | plain | 30,762 | 31.1% | 38.3% | 40.7% | 55.1% | 32.2% | 28.7% | 4.61 |
| inside break | near | 231 | 27.3% | 33.0% | 33.5% | 64.3% | 43.7% | 37.7% | 3.86 |
| inside break | within 1% | 774 | 28.8% | 34.4% | 36.2% | 62.3% | 39.1% | 34.4% | 3.47 |
| outside break | plain | 12,876 | 21.2% | 31.7% | 36.5% | 41.2% | 13.9% | 28.8% | 8.00 |
| outside break | exact, shared open | 633 | 22.1% | 29.1% | 32.0% | 57.1% | 17.4% | 38.7% | 7.52 |
| outside break | near | 227 | 26.0% | 33.9% | 38.1% | 45.0% | 18.5% | 33.9% | 5.26 |
| outside break | within 1% | 718 | 23.0% | 31.9% | 35.5% | 47.9% | 24.9% | 28.8% | 5.01 |

Exact stacks on reversal and inside setups: 7 and 12 units, counted, not read.

### Stacked minus plain, same pattern (percentage points of one-R chance, [95%])
| setup | comparison | n | by 1 | by 3 | by 5 |
|---|---|---|---|---|---|
| 2-2 continuation | exact shared open vs plain | 3,619 | +1.8 [+0, +3] | -1.5 [-3, +0] | -2.2 [-4, -1] |
| 2-2 continuation | near vs plain | 804 | +6.7 [+3, +10] | +6.4 [+3, +10] | +7.0 [+3, +11] |
| 2-2 continuation | within 1% vs plain | 2,555 | +5.2 [+3, +7] | +4.2 [+2, +6] | +4.3 [+2, +6] |
| 2-2 reversal | stacked (exact or near) vs plain | 155 | +2.2 [-5, +9] | +3.7 [-4, +11] | +0.3 [-7, +8] |
| inside break | near vs plain | 231 | -3.9 [-10, +2] | -5.2 [-11, +1] | -7.3 [-13, -1] |
| inside break | within 1% vs plain | 774 | -2.3 [-6, +1] | -3.9 [-7, -0] | -4.5 [-8, -1] |
| outside break | exact shared open vs plain | 633 | +0.9 [-2, +4] | -2.6 [-6, +1] | -4.5 [-8, -1] |
| outside break | near vs plain | 227 | +4.8 [-1, +11] | +2.2 [-4, +8] | +1.6 [-5, +8] |

### Hypothesis 1 (owner): same-price stacks at a shared open do worse than plain and than near
| setup | n exact shared | one R by 1 / 3 / 5 | minus plain | minus near |
|---|---|---|---|---|
| 2-2 continuation | 3,619 | 26.6% / 32.9% / 36.9% | +1.8 / -1.5 / -2.2 | -4.9 / -7.9 / -9.2 |
| outside break | 633 | 22.1% / 29.1% / 32.0% | +0.9 / -2.6 / -4.5 | -3.9 / -4.9 / -6.1 |
| outside break, THIRD | 32 | 15.6% / 21.9% / 25.0% | -6.3 / -12.4 / -13.8 | about 0 |

Reversal and inside-bar shared-open stacks: 3 and 6 units.

## The hammer and shooter shape, plain daily units (the flag is known at entry)

| setup | flag | n | one R by 1 | by 3 | by 5 | stopped by 5 | stop on entry day |
|---|---|---|---|---|---|---|---|
| 2-2 reversal (normal hammer / shooter) | all | 43,809 | 24.8% | 34.3% | 38.2% | 51.7% | 25.9% |
| 2-2 reversal | THIRD | 7,721 | 28.2% | 38.0% | 42.4% | 43.5% | 14.8% |
| 2-2 reversal | STRICT | 3,722 | 27.7% | 37.5% | 41.6% | 41.9% | 13.8% |
| 2-2 continuation (momo, 2-2 form) | all | 55,976 | 24.8% | 34.4% | 39.1% | 46.0% | 18.3% |
| 2-2 continuation | THIRD | 910 | 31.9% | 41.1% | 44.1% | 48.3% | 17.5% |
| 2-2 continuation | STRICT | 225 | 32.9% | 42.2% | 44.2% | 47.8% | 16.9% |
| inside break (momo, 1-2 form) | all | 30,762 | 31.1% | 38.3% | 40.7% | 55.1% | 32.2% |
| inside break | THIRD | 2,481 | 36.2% | 43.6% | 46.2% | 49.9% | 23.3% |
| inside break | STRICT | 1,003 | 36.1% | 44.4% | 47.5% | 48.8% | 22.2% |

Hammer-flagged units stacked with a level: reversal THIRD within 1% (136) 43.4% by 3 vs 38.0%
plain THIRD (+5.4 [-3, +14]); continuation THIRD within 1% (32) 46.9%; the near cells hold 9 to 30
units. Counted, not read.

## Weekly units (entry at last week's level; all flags; one R by 1 / 3 / 5 weeks)

| setup | class | n | by 1 | by 3 | by 5 | stopped by 5 | next week against | median R % |
|---|---|---|---|---|---|---|---|---|
| 2-2 reversal | exact, shared open | 731 | 24.5% | 35.1% | 40.1% | 48.2% | 38.7% | 18.2 |
| 2-2 reversal | near | 354 | 30.0% | 39.4% | 46.0% | 42.5% | 27.4% | 13.6 |
| 2-2 reversal | within 1% | 992 | 28.1% | 40.1% | 45.0% | 42.3% | 27.0% | 14.3 |
| 2-2 reversal | spread | 4,061 | 27.3% | 39.6% | 43.5% | 44.0% | 25.5% | 17.9 |
| 2-2 continuation | exact, shared open | 1,929 | 20.9% | 29.1% | 32.8% | 45.4% | 40.8% | 23.7 |
| 2-2 continuation | near | 443 | 30.7% | 44.7% | 49.9% | 36.3% | 27.9% | 13.6 |
| 2-2 continuation | within 1% | 1,255 | 30.1% | 40.4% | 44.9% | 42.7% | 29.9% | 15.0 |
| 2-2 continuation | spread | 4,816 | 31.9% | 41.6% | 45.8% | 38.1% | 24.1% | 19.9 |
| inside break | exact, shared open | 821 | 25.9% | 35.0% | 39.4% | 53.0% | 42.3% | 15.4 |
| inside break | near | 288 | 37.1% | 44.7% | 48.1% | 45.4% | 33.2% | 11.7 |
| inside break | spread | 2,905 | 35.6% | 43.6% | 46.9% | 47.0% | 29.7% | 14.4 |
| outside break | exact, shared open | 529 | 20.4% | 30.2% | 33.6% | 44.6% | 42.3% | 26.7 |
| outside break | spread | 1,203 | 20.7% | 34.4% | 38.1% | 39.9% | 24.9% | 23.9 |

Stacked minus the rest (within 1% + spread), by 3 weeks: reversal -3.4 [-7, -0], exact shared
open alone -4.6 [-8, -1]; continuation exact shared open -12.2 [-15, -10], near +3.3 [-2, +8];
inside exact shared open -8.3 [-12, -5], near +1.4 [-5, +7]; outside exact shared open -3.6 [-8,
+1]. With the hammer flag: reversal stacked +2.6 [-4, +9] (281 vs 741), near +6.6 [-6, +19];
inside exact shared open -19.0 [-30, -8] (99 vs 273).

Monthly units are thin: 2-2 reversal exact shared open 37 units at 30.3% by 3 months against
31.5% for spread (1,097); 2-2 continuation exact shared open 121 at 25.0% against 27.6% (1,445),
difference -3.3 [-12, +6]; near cells 36 to 80 units. Counted, not read.

## The variant stop (owner's idea: last week's bar as the stop; daily units)

| setup | class | n | median R %, setup bar / weekly bar | one R by 5, setup-bar stop / weekly stop | stopped by 5, weekly stop |
|---|---|---|---|---|---|
| 2-2 reversal | plain | 38,730 | 5.8 / 10.1 | 38.4% / 24.0% | 36.3% |
| 2-2 continuation | plain | 53,965 | 6.9 / 16.0 | 39.2% / 20.0% | 20.3% |
| 2-2 continuation | exact, shared open | 3,619 | 7.2 / 21.9 | 36.9% / 11.0% | 16.0% |
| inside break | plain | 27,093 | 4.6 / 12.0 | 41.0% / 22.9% | 28.8% |
| outside break | plain | 12,485 | 8.0 / 12.3 | 36.7% / 23.7% | 27.6% |

The weekly stop is two to three times further away, so one R is a two to three times bigger move:
far fewer targets inside five days, far fewer stops, most trades still open. It is not the same
target and is not compared to the primary; the owner's reasoning (let trades run until invalidated)
needs an exit rule and a sizing rule before it can be tested as a trade.

## Splits (daily, stacked vs plain, one R by 3 bars; fixed a priori, none picked)

- Direction: the continuation stack reads +0.4 [-2, +2] on shorts and -0.6 [-3, +2] on longs.
  Inside-bar stacks read -10.5 [-18, -3] on longs (123 units) and +1.0 on shorts.
- Year: the continuation stack reads +4.7 [-1, +11] in 2023, +2.1 [-1, +5] in 2024, -0.9 in 2025,
  -1.2 in 2026. Outside-break stacks read -11.4 [-18, -5] in 2024 (179 units), about 0 elsewhere.
- Liquid: identical to the rest (continuation +0.3 vs -0.4).
- The month's open with the trade: continuation stack -0.7 [-2, +1]; against it: +2.0 [-2, +6].
- Quarter (recorded only): the continuation stack reads -4.8 [-8, -2] when the quarter is still
  inside and the level sits on the trade's side of its open (1,179 units), about 0 in every other
  state.

## What the arithmetic says (and nothing more)

- **The same-price stack at the open adds nothing on the daily and costs on the weekly.** A 2-2
  continuation that opens Monday or the 1st with yesterday's high on last week's or last month's
  high reached one R as often as a plain 2-2 continuation by 3 bars (32.9% vs 34.4%), less often
  by 5 (-2.2 [-4, -1]), and stopped out more (50.7% vs 46.0%). On the weekly units the gap is
  wide: a weekly 2-2 continuation broken on that Monday open reached one R 29% of the time against
  42% for the rest (-12 [-15, -10]), with the next week going against it 41% of the time. The
  owner's hypothesis 1 reads as supported on the weekly, weakly on the daily (no gain, more stops),
  and untestable on reversal and inside-bar setups (too few). The setup bars of these stacks are
  the biggest in the tables (median R 7.2% daily, 24% weekly), so one R is also a bigger move;
  that confound is noted, not resolved.
- **A level just beyond the trigger helped the 2-2 continuation and hurt the inside break.** A
  2-2 continuation with an unbroken weekly or monthly level within a quarter percent beyond
  yesterday's high reached one R 40.8% of the time by 3 bars against 34.4% plain (+6.4 [+3,
  +10]); within 1%, +4.2 [+2, +6]. Those triggers are tighter bars (median R 4.9% vs 6.9%). The
  same compression under a level made inside-bar breaks worse (-5.2, -3.9) with more stops (64%
  vs 55%) and more entry-day stop touches (44% vs 32%). Outside breaks: about 0.
- **The hammer shape lifted every pattern by four to seven points.** A top-third close on the
  setup bar: 2-2 reversal 38.0% vs 34.3% by 3 bars, 2-2 continuation 41.1% vs 34.4%, inside break
  43.6% vs 38.3%, with fewer stops and far fewer entry-day stop touches (reversal 14.8% vs 25.9%).
  STRICT (sliver wick) added nothing over THIRD.
- **One in four to one in three plain daily units traded their stop on the entry day** (reversal
  25.9%, inside break 32.2%, continuation 18.3%, outside 13.9%), the owner's "a 2 going 3". Every
  one counts as a stop here, the pessimistic call; the daily candle cannot order them.
- **Across splits nothing flips.** Direction, year, liquidity and the month's open leave the
  continuation stack within two points of plain; the inside-bar stack reads worst on longs.
- **The look-ahead version of the class is in the tables under TRAP**: 60-80% one-R, the day's
  own travel, not a setup.

Not said here, by design: whether any of this makes money after fees, funding and sizing; which
cell is "best"; any rule. Price travel medians (MFE / MAE in R) are in `chance.json`; for plain
daily reversals the median adverse travel exceeds the favourable at every horizon (0.87 vs 0.64 R
by 1 bar, 1.22 vs 1.20 by 5).

## Limitations

- Pessimistic same-day rule: a unit whose stop and target both traded on one day is a stop, and
  an entry-day stop touch counts even if it came before the break. The share is shown per cell.
- Per-unit intervals overstate precision: units on the same day across coins move together.
  Distinct-date counts sit beside every count in `chance_tables.md`.
- R-size confound: classes differ in setup-bar size (exact shared-open stacks are the biggest
  bars, near stacks the tightest). An R-matched comparison was not pre-registered and is not run.
- Survivors only; venue era only (ALL as a check line); no fees, funding or slippage; no
  Underlying-RTH mirror run (confound stated); no intraday ordering.
- Horizons are bars of the unit's own timeframe: 5 monthly bars is five months, so monthly cells
  are thin and heavily censored at the end of the sample.
