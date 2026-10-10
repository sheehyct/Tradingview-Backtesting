# The book view and the R-matched check -- RECEIPT (TVB-37 product 2b, 2026-10-10; numbers re-run after the second audit's decimal-fill fix)

**What this is:** the chance comparison's unit rows (`CHANCE_RECEIPT.md`) read two more ways,
both declared in the prereg's amendment A3 before any number below was computed, at the owner's
request to see impact "in terms of p/l or percent performance even if it's a hypothetical account
(no leverage, no fees, single buy)". Nothing here adds a condition or a cut. Engine
`analysis/domino/book.py` (reads the same units through `chance.coin_units`); tests
`tests/test_domino_book.py`; every table `results/book_tables.md`; cells and curves
`results/book.json`; a private chart page built by `analysis/domino/chart_page.py` draws these
numbers for the owner (the page is a view, this file is the record; its link is not in the repo).

**The book's rules, in one breath:** every daily, weekly and monthly level break on the 292 live
perps (venue era), one unit of notional each, long or short as the break, entered at the level,
stop at the other side of the setup bar, target one R. A trade closes at +R% of notional on one R,
-R% on the stop, and otherwise is marked at the close of the fifth bar of its timeframe. No
leverage, no fees, no funding, no slippage, every trade taken, no compounding. A day that trades
both the stop and the target is a stop, and so is a stop level traded on the entry day (the
pessimistic call from the chance study; one in four to one in three plain daily triggers). Dollar
columns are the SUM of equal-size trades at 1,000 dollars each, so they are not an account balance:
hundreds of trades are open at once. Fees would make every number worse. Glossary of the setup and
class names: `CHANCE_RECEIPT.md`.

## The book, daily triggers, all shape flags, closed or marked at 5 bars

| setup | class | trades | avg % per trade | median % | hit (one R) | stopped | expectancy in R | total $ (1,000 per trade) | max drawdown $ | median R % |
|---|---|---|---|---|---|---|---|---|---|---|
| 2-2 reversal | plain | 43,442 | -0.84 | -2.39 | 38.3% | 51.7% | -0.134 | -363,813 | -364,720 | 5.96 |
| 2-2 reversal | near | 146 | -0.81 | -0.46 | 38.4% | 53.4% | -0.158 | -1,190 | -1,678 | 4.73 |
| 2-2 reversal | within 1% | 732 | -0.97 | -0.81 | 35.5% | 56.8% | -0.215 | -7,123 | -8,164 | 3.84 |
| 2-2 continuation | plain | 55,462 | -0.43 | -1.72 | 39.1% | 46.0% | -0.073 | -240,824 | -241,536 | 6.89 |
| 2-2 continuation | same price at the Monday / 1st open | 3,600 | -1.19 | -3.13 | 36.9% | 50.7% | -0.153 | -42,668 | -52,150 | 7.20 |
| 2-2 continuation | near | 779 | +0.44 | +0.36 | 46.1% | 41.7% | +0.044 | +3,408 | -2,033 | 5.02 |
| 2-2 continuation | within 1% | 2,511 | +0.33 | -0.22 | 43.4% | 44.6% | -0.012 | +8,200 | -3,498 | 5.15 |
| inside break | plain | 30,599 | -0.54 | -1.67 | 40.7% | 55.1% | -0.143 | -166,304 | -166,944 | 4.62 |
| inside break | near | 230 | -1.24 | -1.88 | 33.5% | 64.3% | -0.306 | -2,845 | -3,369 | 3.91 |
| inside break | within 1% | 767 | -1.05 | -1.15 | 36.2% | 62.3% | -0.259 | -8,016 | -8,494 | 3.48 |
| outside break | plain | 12,695 | -0.21 | -0.89 | 36.5% | 41.2% | -0.047 | -27,216 | -27,508 | 8.04 |
| outside break | same price at the Monday / 1st open | 631 | -2.23 | -3.96 | 32.0% | 57.1% | -0.254 | -14,073 | -15,053 | 7.51 |
| outside break | near | 218 | +0.28 | -0.41 | 38.1% | 45.0% | -0.075 | +604 | -783 | 5.43 |
| outside break | within 1% | 699 | -0.32 | -0.66 | 35.5% | 47.9% | -0.125 | -2,212 | -2,313 | 5.07 |

Same-price stacks on reversal and inside setups: 3 and 6 trades, counted, not read. The median
trade is a loss in every cell: most trades end at the stop or marked slightly under water; the
average is pulled up by the one-R winners.

## The hammer shape on the plain daily book

| setup | flag | trades | avg % per trade | hit | stopped | expectancy in R | total $ | max drawdown $ |
|---|---|---|---|---|---|---|---|---|
| 2-2 reversal | all | 43,442 | -0.84 | 38.3% | 51.7% | -0.134 | -363,813 | -364,720 |
| 2-2 reversal | THIRD | 7,660 | -0.10 | 42.4% | 43.5% | -0.010 | -7,543 | -21,088 |
| 2-2 reversal | STRICT | 3,698 | -0.01 | 41.6% | 41.8% | +0.002 | -542 | -11,270 |
| 2-2 continuation | all | 55,462 | -0.43 | 39.1% | 46.0% | -0.073 | -240,824 | -241,536 |
| 2-2 continuation | THIRD | 903 | -0.04 | 44.1% | 48.3% | -0.035 | -399 | -4,560 |
| 2-2 continuation | STRICT | 224 | +0.25 | 44.2% | 47.8% | -0.030 | +564 | -1,139 |
| inside break | all | 30,599 | -0.54 | 40.7% | 55.1% | -0.143 | -166,304 | -166,944 |
| inside break | THIRD | 2,460 | -0.05 | 46.2% | 49.9% | -0.039 | -1,286 | -4,041 |
| inside break | STRICT | 994 | +0.19 | 47.5% | 48.8% | -0.016 | +1,902 | -2,168 |
| outside break | all | 12,695 | -0.21 | 36.5% | 41.2% | -0.047 | -27,216 | -27,508 |
| outside break | THIRD | 801 | +0.28 | 38.8% | 35.3% | +0.052 | +2,272 | -4,733 |
| outside break | STRICT | 308 | +0.31 | 41.2% | 30.2% | +0.125 | +950 | -2,113 |

## The book, weekly triggers, all shape flags, closed or marked at 5 weeks

| setup | class | trades | avg % per trade | median % | hit | stopped | expectancy in R | total $ | max drawdown $ | median R % |
|---|---|---|---|---|---|---|---|---|---|---|
| 2-2 reversal | same price at the Monday open | 643 | -0.88 | -3.08 | 40.1% | 48.2% | -0.056 | -5,639 | -8,100 | 18.8 |
| 2-2 reversal | near | 315 | +0.04 | +3.03 | 46.0% | 42.5% | +0.045 | +137 | -2,392 | 13.9 |
| 2-2 reversal | within 1% | 886 | +0.91 | +4.02 | 45.0% | 42.3% | +0.048 | +8,041 | -7,013 | 14.7 |
| 2-2 reversal | spread | 3,760 | -0.04 | +3.75 | 43.5% | 44.0% | +0.009 | -1,580 | -31,582 | 18.1 |
| 2-2 continuation | same price at the Monday open | 1,847 | -1.25 | -5.04 | 32.8% | 45.4% | -0.091 | -23,035 | -45,736 | 24.1 |
| 2-2 continuation | near | 397 | +2.06 | +4.92 | 49.9% | 36.3% | +0.147 | +8,197 | -2,306 | 14.3 |
| 2-2 continuation | within 1% | 1,149 | +0.44 | +2.10 | 44.9% | 42.7% | +0.022 | +5,067 | -8,213 | 15.6 |
| 2-2 continuation | spread | 4,492 | +1.75 | +7.78 | 45.8% | 38.1% | +0.089 | +78,507 | -30,635 | 20.4 |
| inside break | same price at the Monday open | 770 | -0.82 | -8.27 | 39.4% | 53.0% | -0.120 | -6,282 | -13,221 | 15.6 |
| inside break | near | 260 | +0.07 | +0.66 | 48.1% | 45.4% | +0.019 | +174 | -2,660 | 11.8 |
| inside break | spread | 2,676 | +0.60 | +3.88 | 46.9% | 47.0% | +0.010 | +16,133 | -16,843 | 14.5 |
| outside break | same price at the Monday open | 482 | -3.15 | -8.19 | 33.6% | 44.6% | -0.110 | -15,188 | -28,296 | 27.7 |
| outside break | spread | 1,122 | -0.53 | +0.46 | 38.1% | 39.9% | -0.008 | -5,935 | -23,365 | 24.5 |

Weekly R is a whole week's range (median 14-28% of price), so one R is a big move and five weeks
is a long hold; the monthly book (in `book_tables.md`) is thinner still and not read here.

## The R-matched check: is the stack effect the bar size?

Stacked minus base one-R chance, raw and after reweighting the base to the stacked group's
setup-bar sizes (five bins at the base's R quintiles). Daily base = plain; weekly base = within 1%
plus spread.

| timeframe | setup | stacked class | n stacked | raw diff by 3 | matched by 3 [95%] | matched by 5 [95%] |
|---|---|---|---|---|---|---|
| daily | 2-2 continuation | near | 789 | +6.4 | +4.7 [+1, +8] | +6.0 [+3, +10] |
| daily | 2-2 continuation | same price at the open | 3,619 | -1.5 | -0.7 [-2, +1] | -1.4 [-3, +0] |
| daily | inside break | near | 230 | -5.2 | -5.0 [-11, +1] | -6.6 [-13, -0] |
| daily | outside break | same price at the open | 633 | -2.6 | -3.5 [-7, +0] | -5.3 [-9, -2] |
| daily | 2-2 reversal | stacked (exact or near) | 155 | +3.7 | +2.7 [-5, +10] | -0.1 [-8, +7] |
| weekly | 2-2 continuation | same price at the open | 1,880 | -12.2 | -8.0 [-10, -6] | -8.9 [-11, -6] |
| weekly | 2-2 continuation | near | 414 | +3.3 | -0.2 [-5, +5] | +1.3 [-4, +6] |
| weekly | 2-2 reversal | same price at the open | 669 | -4.6 | -3.7 [-8, +0] | -2.9 [-7, +1] |
| weekly | inside break | same price at the open | 805 | -8.3 | -7.0 [-11, -3] | -6.7 [-11, -3] |
| weekly | outside break | same price at the open | 493 | -3.6 | -1.9 [-6, +3] | -2.2 [-7, +3] |

Bins for the weekly 2-2 continuation at the shared open: the deficit holds in every bar-size bin
(-10.2, -8.4, -12.9, -6.0, -6.0 points from the tightest to the widest fifth). For the daily 2-2
continuation stacked (exact or near) against plain, the bins read +0.5, +1.1, -2.4, -0.4, +1.9:
nothing. Monthly rows are in `book_tables.md` (30 to 150 stacked units; intervals span zero).

## What the arithmetic says (and nothing more)

- **Under these mechanical exits every plain daily pattern loses on the equal-size book.** 2-2
  reversals -0.84% per trade, 2-2 continuations -0.43%, inside breaks -0.54%, outside breaks
  -0.21%, before fees. Hit rates of 36-41% against stop rates of 41-55%, with the pessimistic
  same-day call inside those stops. The exits here are the fixed one-R target and the setup-bar
  stop, not STRAT management; the owner's "run until invalidated" idea is not tested.
- **The hammer shape brings each pattern to about flat.** Reversal THIRD -0.10% and STRICT
  -0.01% per trade; continuation THIRD -0.04%, STRICT +0.25%; inside THIRD -0.05%, STRICT +0.19%;
  outside THIRD +0.28%, STRICT +0.31%, with stop rates 8 to 11 points lower than the unflagged
  book. These are the only daily cells near or above zero besides the stacked continuations.
- **The stacked 2-2 continuation is the one daily A+ class in the black:** +0.44% per trade with
  a level within a quarter percent beyond, +0.33% within 1%, and the R-matched check keeps the
  chance gap (+4.7 [+1, +8] by 3 bars, +6.0 [+3, +10] by 5). The same-price stack at the open is
  worse than plain (-1.19% vs -0.43%), and after matching its chance gap is -0.7 [-2, +1]:
  nothing, once bar size is held equal.
- **On the weekly, the Monday-open stack loses on every setup** (-0.9% to -3.2% per trade) and
  the deficit survives matching at two thirds of its raw size (-8.0 [-10, -6] for the 2-2
  continuation), in every bar-size bin. The weekly 2-2 continuation whose day had already run 1%+
  before the level broke is the biggest positive in the book (+1.75% per trade over 4,492 trades,
  +78k on the 1,000-per-trade book, drawdown -31k), with near behind it (+2.06% on 397).
- **Hypothesis 1 (owner), in money:** the same-price-at-the-open stack underperforms its plain
  pattern on the daily (continuation -1.19% vs -0.43%; outside -2.23% vs -0.21%) and the rest of
  its pattern on the weekly (every setup). On the daily the chance gap vanishes once bar size is
  matched; on the weekly it does not.

Not said here, by design: that any cell is a strategy, or what fees, funding, sizing and real
exits would do to it. The receipt that owns the chances is `CHANCE_RECEIPT.md`.

## Limitations

- The pessimistic same-day call drives the stop counts; an intraday pass would move money from the
  stop column into one R or neither for some share of the 14-32% entry-day stop touches.
- Equal-size, every-trade sums: many positions open at once, a 1,000-per-trade book with 43,000
  trades is not an account anyone runs. Read the average per trade and the hit / stop pair first.
- Marked at the horizon: an open trade's value at the fifth bar's close is counted as if closed.
- Same-day clustering across coins; survivors only; venue era only; no fees, funding or slippage;
  no Underlying-RTH mirror run.
- The R-matched reweighting holds bar size equal within five bins; it does not hold anything
  else equal (coin, date, regime).
