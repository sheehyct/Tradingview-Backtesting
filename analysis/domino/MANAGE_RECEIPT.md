# The STRAT-management book -- RECEIPT (TVB-37 product 3, built in TVB-38, 2026-10-11)

> Amended 2026-10-11, same session, after the Codex audit (`docs/reviews/tvb38-codex-audit.md`,
> prereg amendment A1): projected targets rebuilt in decimals (book D moved by under a hundredth
> of a point); book D5 added as the stop-isolating line; each book's own holding time; the
> 20-day follow-up flags unknown where the window is incomplete; H3 read on the matched window,
> which REVERSED it; sentences marked by the audit corrected against the tables.

**What this is:** the chance comparison's unit rows (`CHANCE_RECEIPT.md`, `BOOK_RECEIPT.md`)
traded a third way, declared in `docs/experiments/tvb37_management_book_prereg.md` before any
number below was computed: no price stop, out at a daily close against the trade with the week
against it at that close, profits at a ladder of structural targets. It exists because the chance
book lost on every plain daily pattern while the targets were in fact reached, which made the
setup-bar stop the SUSPECT. Engine `analysis/domino/manage.py`; tests `tests/test_domino_manage.py`
(14 hand vectors, written before the engine ran on data); every table
`results/manage_tables.md`; cells and curves `results/manage.json`; per-trade rows
`results/manage_trades.csv.gz` (regenerable, ignored). Run offline on the 2026-10-10 snapshot
(`uv run python -m analysis.domino.manage --as-of 2026-10-10`), so every count reconciles with
product 2. The private chart page draws these numbers beside the chance book's (link not in the
repo). Nothing here is a rule; no cell is promoted.

## Glossary, in trader terms

- **The trade:** every daily, weekly and monthly level break on the 292 live perps, venue era,
  long or short as the break, entered at the level the instant it breaks. Same trades as the
  chance book, same labels (2-2 reversal, 2-2 continuation, inside break, outside break), same
  hammer flags, same stack classes.
- **No stop.** Nothing takes you out intraday except a target. On these trades the setup-bar
  stop and STRAT's "the entry bar went outside" invalidation are the same price, so both are gone.
- **The exit:** at the close of a day that closed against you (a red candle for a long) with the
  week also against you at that close (price under Monday's open). You are filled at that
  close. On a Monday the two tests are one. The entry day counts.
- **T1, the pattern's own magnitude:** for a 2-2 reversal the far side of the bar before the
  pattern (where the "compound 3" completes); for an inside-bar break off a 2 against or a 3,
  that bar's far side; the 2-2 continuation, the with-trend inside bar and the 3-2 have no
  magnitude of their own and take the first unbroken weekly or monthly level beyond the entry.
  **T2, T3:** the next unbroken weekly / monthly levels beyond T1. Ladder fixed at entry.
- **Cap:** 20 trading days after the entry day; still open there = marked at that close (OPEN).
- **The books (percent of notional, one unit per trade, no leverage, fees or funding):** A all
  out at T1; B hold through T2 with the exit live; C exit only, no target; D one R or the exit
  (the chance book's target with the close exit in place of its stop, run to the 20-day cap);
  **D5** the same swap settled at the chance book's own five-bar horizon, so between D5 and the
  reference only the stop changes; **reference** = the chance book itself on the identical
  trades (one R or the setup-bar stop, marked at the fifth bar). Dollar columns are sums of equal-size trades at
  1,000 dollars each, never an account balance.
- **R** keeps its chance-book meaning (the setup bar's far side to the entry) and is only a
  measuring stick here. **MAE / MFE** = the furthest adverse / favourable travel from the entry.

## The finding, in one breath

Taking the stop away and managing the STRAT way turns every plain daily pattern from a loser into
roughly flat: the chance book lost -0.27% to -0.84% per trade, the management books sit between
-0.24% and +0.24%, and on the same trades, at the same five-bar horizon, the stop swap alone
(book D5) is worth +0.48 to +0.92 per trade with intervals clear of zero (H2, the owner's
suspect, holds in sign; the 20-day book D reads the same). It is not a
money machine: the median trade still loses in the two books that hold for structure (B and C)
on every pattern, two trades in three close in the red on the exit-only book, and the averages
are carried by the right tail.
The close exit is fast: it fires inside a median two to three days and closes 99% of trades
before the cap. The lead's counter-hypothesis (H3: the close exit is itself an early exit, at
least as often as the stop) does NOT hold on the like-for-like read: inside the same five bars,
16% to 32% of the trades the close exit took off before one R went on to touch it, against 24%
to 48% of the stopped trades. (The 20-day follow-up, which first made it look the other way,
is four times the stop's window and is reported separately.) The
price of no stop is the tail: two trades in five travel more than one setup-bar R against you
before the close exit, one in ten more than two R, and the worst single trades are shorts that
closed down 88% to 143% of notional. On weekly and monthly trades the daily clock cuts the
trade short and loses to the chance book's five-bar hold; the own-bar clock holds longer and
loses more. The stacked continuation stays the one A+ in the black under every rule.

## Reach rates, plain daily setups (headline clock, 20-day cap)

| setup | units | T1 median distance (R) | T1 before the exit | T1 any time in 20 days | T2 after T1 | T3 after T2 | exit at the entry close | median days held |
|---|---|---|---|---|---|---|---|---|
| 2-2 reversal | 43,475 | 2.64% (5.95%) | 63.8% [63, 64] | 87.5% | 40.4% | 27.5% | 20.3% | 2 |
| 2-2 continuation | 55,384 | 9.81% (6.87%) | 36.2% [36, 37] | 57.7% | 26.3% | - | 12.2% | 3 |
| inside break | 30,482 | 3.52% (4.61%) | 53.6% [53, 54] | 76.8% | 29.3% | 28.6% | 18.7% | 2 |
| outside break | 12,723 | 8.50% (8.01%) | 38.7% [38, 40] | 61.8% | 24.5% | - | 16.8% | 3 |

Every plain daily cell exits 99.2% to 99.5% of its trades before the cap; 0.5% to 0.8% are
marked open at day 20. The continuation has a T1 on 81% of its units (the rest had no unbroken
higher level beyond the entry); a reversal's T1 sits at the trigger on 110 units (no magnitude,
exit-only book only). The reversal's T1 is close (the bar before the pattern, a median 2.6% away,
less than half its R), which is why it is reached so often and why book A on reversals takes
small profits: 66% of its trades close in the black for an average of -0.05%.

## How the pre-T1 exits died, plain daily

| setup | exited before T1 | at the entry close | median days | avg % | avg R | touched T1 inside 20 days (complete follow-up only) | D5: exited before one R, touched one R inside the five bars | chance book, same trades: stopped, saw one R inside the five bars | D: exited before one R, touched one R inside 20 days (complete follow-up only) |
|---|---|---|---|---|---|---|---|---|---|
| 2-2 reversal | 15,709 | 41.4% | 1 | -4.86 | -0.78 | 65.1% [64, 66] n=15,126 | 25.0% [24, 26] n=23,262 | 35.9% [35, 37] n=22,356 | 58.6% [58, 59] n=23,278 |
| 2-2 continuation | 28,585 | 20.9% | 2 | -4.43 | -0.68 | 33.6% [33, 34] n=27,970 | 17.7% [17, 18] n=21,622 | 28.9% [28, 30] n=21,187 | 50.8% [50, 51] n=23,369 |
| inside break | 12,849 | 33.3% | 1 | -3.75 | -0.98 | 49.8% [49, 51] n=12,341 | 32.4% [32, 33] n=12,784 | 47.5% [47, 48] n=15,186 | 63.8% [63, 65] n=12,669 |
| outside break | 6,809 | 27.7% | 2 | -4.28 | -0.59 | 37.2% [36, 38] n=6,561 | 15.8% [15, 17] n=5,751 | 23.8% [23, 25] n=4,680 | 48.9% [48, 50] n=6,264 |

The trades the close exit kills before T1 lose about four percent each (0.6 to 1.0 R). Against
the same target and the same window (one R inside five bars, D5's column against the chance
book's, both on the units with a T1), the close exit throws away fewer target-bound trades than
the stop on every pattern. Read with one convention in mind: the chance book counts a day that
touched both the stop and one R as a stop that "saw the target", while the close exit never
faces that same-day race. The 20-day columns ignore the exit for four times as long and are
not comparable to the stop's five-bar travel; they are shown because the prereg declared them,
on the units whose 20-day follow-up is complete (the rest are unknown, not false).

## The tail, plain daily (no stop: this is where the book lives or dies)

| setup | MAE over 1R | over 2R | over 3R | median MAE R | median MFE R | worst single trade | held to the cap |
|---|---|---|---|---|---|---|---|
| 2-2 reversal | 42.5% | 9.7% | 3.7% | 0.92 | 0.82 | -88.2% | 0.6% |
| 2-2 continuation | 42.5% | 10.9% | 3.7% | 0.89 | 0.89 | -125.1% | 0.6% |
| inside break | 54.8% | 19.6% | 8.2% | 1.09 | 1.11 | -111.2% | 0.5% |
| outside break | 32.0% | 6.4% | 2.2% | 0.77 | 0.74 | -143.2% | 0.8% |

A trade beyond -100% is a short whose coin more than doubled before a green close with the week
green ended it. Nothing here sizes against liquidation; at any leverage a book with this tail has
a liquidation question this receipt states and does not answer.

## The books, plain daily, on the same trades (units with a T1 and a reference return)

| setup | book | trades | avg % per trade | median % | closed in profit | closed at the target | total $ (1,000 per trade) | max drawdown $ | median days (own fill) | minus reference [95%] |
|---|---|---|---|---|---|---|---|---|---|---|
| 2-2 reversal | A, all out at T1 | 43,209 | -0.05 | +0.84 | 66.3% | 63.8% | -20,344 | -81,073 | 0 | +0.80 [+0.73, +0.86] |
| | B, hold through T2 | | +0.12 | -1.39 | 40.3% | 23.1% | +51,539 | -48,952 | 1 | +0.96 [+0.88, +1.05] |
| | C, exit only | | +0.22 | -1.90 | 34.1% | - | +97,097 | -48,787 | 2 | +1.07 [+0.95, +1.18] |
| | D, one R or the exit (20 days) | | +0.08 | -0.30 | 49.0% | 44.4% | +36,599 | -60,928 | 1 | +0.93 [+0.87, +0.98] |
| | D5, one R or the exit (five bars) | | +0.07 | -0.21 | 49.3% | 43.4% | +31,998 | -65,910 | 1 | +0.92 [+0.86, +0.97] |
| | reference (chance book) | | -0.84 | -2.41 | 43.3% | 38.2% | -364,408 | -365,217 | 1 | - |
| 2-2 continuation | A | 44,673 | -0.23 | -0.65 | 47.3% | 36.2% | -102,624 | -186,087 | 1 | +0.22 [+0.15, +0.29] |
| | B | | -0.24 | -2.10 | 36.1% | 5.2% | -107,650 | -242,151 | 3 | +0.21 [+0.11, +0.30] |
| | C | | -0.24 | -2.15 | 35.4% | - | -107,701 | -268,190 | 3 | +0.21 [+0.09, +0.32] |
| | D | | +0.01 | +0.55 | 51.1% | 46.7% | +5,250 | -83,398 | 1 | +0.46 [+0.41, +0.51] |
| | D5 | | +0.06 | +0.70 | 51.8% | 44.6% | +28,413 | -75,086 | 1 | +0.51 [+0.46, +0.56] |
| | reference | | -0.45 | -1.83 | 46.0% | 39.4% | -199,465 | -201,265 | 1 | - |
| inside break | A | 27,623 | +0.02 | +0.49 | 60.3% | 53.6% | +6,017 | -24,191 | 0 | +0.54 [+0.47, +0.62] |
| | B | | -0.07 | -1.56 | 35.9% | 12.8% | -19,310 | -68,162 | 1 | +0.45 [+0.34, +0.57] |
| | C | | -0.02 | -1.79 | 32.9% | - | -6,854 | -88,599 | 2 | +0.50 [+0.35, +0.65] |
| | D | | +0.24 | +1.17 | 55.6% | 52.6% | +65,084 | -17,504 | 1 | +0.76 [+0.70, +0.82] |
| | D5 | | +0.24 | +1.17 | 55.6% | 51.9% | +66,617 | -17,041 | 1 | +0.76 [+0.70, +0.82] |
| | reference | | -0.52 | -1.72 | 43.0% | 40.8% | -144,381 | -145,054 | 0 | - |
| outside break | A | 11,050 | -0.00 | -0.51 | 48.2% | 38.9% | -550 | -21,607 | 1 | +0.26 [+0.12, +0.41] |
| | B | | +0.18 | -2.17 | 35.6% | 5.6% | +20,351 | -39,238 | 3 | +0.45 [+0.26, +0.65] |
| | C | | +0.18 | -2.23 | 35.0% | - | +20,133 | -44,041 | 3 | +0.45 [+0.24, +0.66] |
| | D | | +0.18 | -0.85 | 47.0% | 41.6% | +20,413 | -19,578 | 1 | +0.45 [+0.34, +0.56] |
| | D5 | | +0.21 | -0.51 | 48.2% | 38.9% | +23,742 | -17,007 | 1 | +0.48 [+0.38, +0.59] |
| | reference | | -0.27 | -1.04 | 47.5% | 37.0% | -29,728 | -31,648 | 2 | - |

Read it as a trader: on the 2-2 reversal, taking the near target (A) wins two trades in three
and still nets nothing, because the one-in-three losers lose four percent against the winners'
one or two; holding for structure (B, C) wins one trade in three and nets a little because the
winners run; keeping the one-R target and only swapping the stop at the chance book's own
horizon (D5) is the clean comparison, and it is worth almost a full percent per trade over the
chance book. Median days are each book's own: A fills its near target on the entry day or the
next, D and D5 within a day, the reference stops or fills within a day or two. The continuation
is the one
pattern where management does not get into the black: its T1 is far (a median 9.8% away, beyond
its own R) and its losers are as large as everyone else's. The exit-only book on every unit
(with or without a T1) is within three hundredths of the same-rows figure on every pattern.

A round trip at the venue's taker fee is a few hundredths of a percent per trade (two fills,
whatever the holding time), of the same order as these averages; funding over the days held is
a separate, uncomputed cost. The paired differences against the reference are fee-neutral only
where both books fill twice, which they do.

## The hammer flag (THIRD), plain daily

| setup | reference | A | C | D | D minus reference [95%] |
|---|---|---|---|---|---|
| 2-2 reversal, THIRD (7,620) | -0.12 | -0.20 | -0.07 | +0.02 | +0.14 [+0.01, +0.26] |
| 2-2 continuation, THIRD (788) | +0.13 | +0.17 | +0.04 | +0.44 | +0.32 [-0.02, +0.65] |
| inside break, THIRD (2,169) | -0.08 | +0.17 | +0.01 | +0.26 | +0.34 [+0.16, +0.52] |
| outside break, THIRD (697) | +0.31 | +0.28 | +0.22 | +0.49 | +0.18 [-0.24, +0.60] |

The hammer flag had already brought the chance book to about flat; management adds little on
top of it (a tenth to a third of a percent, two of four intervals touching zero). The stop swap's
value sits in the non-hammer bulk, where the setup bar is large and the stop far.

## The stacked daily cells (the A+ axis)

| setup, class | trades | reference | A | B | C | D | D minus reference [95%] |
|---|---|---|---|---|---|---|---|
| 2-2 continuation, near (level within 0.25%) | 778 | +0.44 | +0.06 | +0.18 | +0.23 | +0.87 | +0.43 [+0.11, +0.76] |
| 2-2 continuation, within 1% | 2,507 | +0.33 | +0.07 | +0.63 | +0.74 | +0.77 | +0.44 [+0.27, +0.62] |
| 2-2 continuation, same price at the Monday / 1st open | 1,863 | -1.19 | -1.28 | -1.75 | -1.75 | -0.69 | +0.50 [+0.26, +0.74] |
| 2-2 reversal, within 1% | 723 | -0.98 | +0.04 | -0.63 | -1.05 | -0.18 | +0.80 [+0.49, +1.11] |
| inside break, near | 229 | -1.25 | +0.04 | -1.10 | -1.35 | -0.56 | +0.70 [+0.20, +1.20] |
| outside break, same price at the open | 372 | -2.57 | -1.27 | -1.25 | -1.25 | -1.28 | +1.29 [+0.75, +1.84] |

On a near or within-1% stack the first rung IS T1 and sits a few tenths of a percent away, so
book A fills it on 97% to 89% of trades for next to nothing; the money in those cells comes from
holding (B, C) or from the one-R target with the close exit (D), and the stacked continuation
stays the one A+ in the black under every rule. The shared-open stacks lose under every book;
no management rescues a level that was only the old bar's last-day extreme.

## Weekly and monthly units (headline clock)

Weekly, exit-only book C by class: 2-2 reversal shared open -1.66, near -0.31, within 1% -0.64,
spread -0.57; 2-2 continuation shared open -2.15, near -0.01, within 1% +1.35, spread +0.74;
inside shared open -1.41, spread +0.47. The daily clock closes a weekly trade inside a median one
to five days, and on the classes where the chance book held five weeks and won (the continuation
spread +1.70, the reversal within 1% +0.91) the management books lose to it (A -1.18 [-1.92,
-0.44] on the continuation spread). Monthly: the reversal spread's reference +4.51 against A
-1.11 and D -1.23 (-5.74 [-8.64, -2.85]); the inside spread's reference +7.72 against C -2.54.
Not everywhere: the weekly continuation within 1% did better under B and C (+1.35) than under
the reference (+0.48), and the weekly spread continuation's D (+1.27) is within its interval of
the reference. But on the classes with the most weight the pattern holds: a weekly or monthly
level break traded on a daily exit clock is closed inside the week it was meant to ride, and the
five-bar hold kept more of those moves.

## Fork 1: the measured move beside the level (declared variant, same units, same exit)

| setup, class | units | median T1 distance: level / move | T1 reached before the exit: level / move | book A: level / move | book B: level / move |
|---|---|---|---|---|---|
| continuation, plain | 44,673 | 9.83% / 9.46% | 36.2% / 35.1% | -0.23 / +0.02 | -0.24 / -0.22 |
| continuation, near | 778 | 0.12% / 7.18% | 97.0% / 43.8% | +0.06 / +0.93 | +0.18 / +0.16 |
| continuation, within 1% | 2,507 | 0.61% / 7.34% | 88.4% / 42.6% | +0.07 / +0.85 | +0.63 / +0.95 |
| with-trend inside, plain | 7,593 | 9.37% / 8.10% | 33.5% / 36.9% | -0.11 / +0.12 | -0.19 / -0.08 |
| weekly continuation, spread | 2,225 | 14.07% / 26.19% | 37.0% / 14.7% | +0.53 / +1.10 | +0.74 / +0.66 |

On plain daily continuations the two targets sit at the same distance and are reached as often;
the measured move's book A is a quarter point better (it fills exactly at its projection, the
level fills at whatever the higher bar's extreme was). On the stacked cells the level is next
door and the measured move is the real target. On weekly units the two-bar range projects a
26% move that is rarely reached. Both shown; neither promoted.

## Fork 2: the exit clock on weekly and monthly units (declared variant, 20 own bars)

Weekly units, own-bar clock (a red weekly close with the month red) against the daily clock at
the same cap: the own clock holds a median 13 to 27 days against 1 to 5, reaches T1 before its
exit more often (48% to 65% against 28% to 50%), and loses more on the exit-only book on fourteen of
sixteen cells by the mean, nine of them with intervals clear of zero (continuation shared open
-2.67 [-4.13, -1.20], continuation within 1% -2.55 [-3.92, -1.19], inside shared open -3.03
[-4.43, -1.63], inside spread -2.06 [-3.06, -1.06]); the two exceptions are the reversal
shared open (+1.28 [-0.88, +3.45]) and the outside shared open (+0.12 [-4.85, +5.09]). Monthly units: the own clock holds 30 to 105 days;
differences are wide and mostly cross zero (continuation shared open -10.20 [-19.16, -1.23] on
114; inside shared open +22.70 [+0.17, +45.23] on 34). The lowest timeframe in the stack takes
the trade off early; the own-bar clock gives a weekly trade its week and pays for it in the
average. Both shown; neither promoted.

## The hypotheses, as declared

| setup | H2: D5 minus reference (stop only) | D minus reference (20 days) | H3: D5 exited before one R, touched one R inside the five bars | chance book: stopped, saw one R inside the five bars |
|---|---|---|---|---|
| 2-2 reversal | +0.92 [+0.86, +0.97] | +0.93 [+0.87, +0.98] | 25.0% | 35.9% |
| 2-2 continuation | +0.51 [+0.46, +0.56] | +0.46 [+0.41, +0.51] | 17.7% | 28.9% |
| inside break | +0.76 [+0.70, +0.82] | +0.76 [+0.70, +0.82] | 32.4% | 47.5% |
| outside break | +0.48 [+0.38, +0.59] | +0.45 [+0.34, +0.56] | 15.8% | 23.8% |

H2 holds in sign on all four patterns, on the stop-isolating read and on the 20-day one:
swapping the setup-bar stop for the close exit lifts the average trade. H3 does not hold: on
the same target, the same window and the same trades, the close exit throws away fewer
target-bound trades than the stop did (the first draft of this receipt read it the other way
from a 20-day follow-up; the audit's matched read corrected it). The lift comes from both
sides: fewer winners thrown away, and losers that average 0.6 to 1.0 R instead of a full R.

## Splits worth a trader's eye (plain daily, book D and the reference)

- **The week's side at entry.** A continuation entered against the week (price under Monday's
  open for a long) reaches T1 before the exit 14.7% of the time against 39.4% with the week;
  book D -0.24 against +0.05; the reference -0.85 against -0.39. A reversal against the week:
  T1 50.4% against 72.3%, D -0.16 against +0.24. Entry-time, known at the break.
- **Direction** (the split table shows A, C, D and the reference). The reference is worse on
  longs on every pattern (-0.62 to -0.88 against -0.19 to +0.06 on shorts). Book D is close to
  even on both sides except the inside break (shorts +0.43, longs +0.06). The exit-only book C
  swings by pattern: reversal longs +0.54 against shorts -0.07, continuation shorts -0.52
  against longs +0.04, outside longs +0.42 against shorts -0.03.
- **Year.** 2024 was the exit-only book's year (continuation C +1.10, outside C +1.21, inside C
  +0.83) while the reference lost in every cell; 2025 was the continuation's bad one (C -1.26,
  D -0.32, A -0.97); 2026 sits within a quarter point of zero on every book.
- **The entry day went outside (OUTCOME-SIDE: the entry day's own travel).** When it did, every
  management book loses 1.7 to 3.3 per trade and the reference 4.3 to 5.9; when it did not,
  every management book gains 0.5 to 1.2 and the reference 0.7 to 1.3. The invalidation the
  stop encoded was real information; it just cost a full R to act on it.

## Amendment A2 (TVB-39): the lead's five candidates, each one change on the same trades

The owner said "you may run your would-test-next" on 2026-10-12; the five were declared in the
prereg (amendment A2) before the engine changed, each with its reading written down first. All
five run on the plain daily book cohort (a T1 and a reference return), beside the headline, and
nothing is combined or promoted. Tables: `results/manage_tables.md`, "Amendment A2".

**In trader terms, what each one did.**

- **Only take it when the week is already on your side (A2.1).** On the 2-2 reversal, the 2-2
  continuation and the outside break, with-the-week trades beat against-the-week trades on books
  A and C (reversal A +0.04 against -0.19, C +0.28 against +0.13; continuation A -0.19 against
  -0.49, C -0.20 against -0.53; outside A +0.01 against -0.16, C +0.18 against +0.16). The inside
  break goes the other way: against the week it reaches T1 almost as often (49.8 against 55.8
  percent) and pays better on every book (A +0.18 against -0.07, C +0.16 against -0.13, D +0.38
  against +0.16). The declared reading R1 said "if AGAINST wins anywhere, the split was outcome
  noise, not a condition": it wins on the inside break, so the week's side is not a general
  condition; it is a pattern-specific read the owner can take or leave (an inside-bar break
  against the week is a counter-trend break with the week's open ahead of it as a level).
- **Manage on the hourly (A2.2).** On the hourly window (the venue keeps about 208 days of
  hours: 13,013 reversal, 12,521 continuation, 8,731 inside, 3,664 outside trades since
  2026-03-18), getting out on the first red hour while the day is red holds a median 9-11 hours
  against 48-72 on the daily clock, every trade exits inside the cap, and the losing trades
  shrink to less than half (average loser -1.5 to -1.9 against -3.8 to -4.9). The price is the
  targets: T1 before the exit falls from 65 to 45 percent on the reversal, 36 to 14 on the
  continuation, 51 to 32 on the inside, 39 to 16 on the outside. Net, paired on the same trades,
  the exit-only book moves -0.14 [-0.28, +0.01] on the reversal, 0.00 on the continuation, +0.21
  [+0.04, +0.37] on the inside break, -0.27 [-0.59, +0.05] on the outside; books A and D move by
  under a tenth with every interval over zero. R2 made no sign prediction; the declared
  expectations (sooner, smaller losers, fewer targets) all held. Small losers and few winners
  come out where big losers and more winners did. The hourly books fill a target only up to the
  exit hour, where the daily bar fills any touch on the exit day; that ordering is part of the
  difference and is not separated here.
- **Half off at T1 (A2.3).** Book E sits between A and C on every pattern (reversal A -0.05, E
  +0.09, C +0.22; outside -0.00, +0.09, +0.18; continuation and inside flat across all three).
  R3 holds. Nothing more: half at T1 buys half the exit-only book's right tail at half its cost.
- **Charge the taker fee (A2.4).** Two fills at the venue's rate are 0.077 to 0.082 per trade
  on these books. Net of that, the lines whose interval stays over zero are three: the reversal
  exit-only book +0.14 [+0.02, +0.27], the inside break's book D +0.16 [+0.08, +0.23] and D5
  +0.16 [+0.09, +0.24]. Every other management line is flat net (intervals through zero); the
  reference is -0.35 to -0.92 net. R4 asked which lines survive; these three do, on gross
  intervals that already cleared zero. Slippage is not charged (the entry is a taker at a level
  that just broke; TVB-2's finding that slippage, not the fee, is the binding cost stands).
- **"Against" as under water (A2.5).** Exiting on a daily close THROUGH the entry price (with
  the week against) instead of on a red candle holds about the same time (median 2-4 days on
  both), fattens the tail a little (past one R against: 44 to 57 percent against 42 to 54) and
  does NOT lose more on the exit-only book: C_u - C is +0.04 on the reversal, +0.20 [+0.09,
  +0.32] on the continuation, +0.04 on the inside, +0.23 [-0.02, +0.49] on the outside. Book A
  slips by a few hundredths (the under-water exit fires on some days the colour exit would not,
  a green day that opened and closed under the entry), book D does not move. R5 was the lead's
  call that the under-water exit loses MORE; it loses less or the same, so the lead was wrong on
  the continuation and unproven elsewhere. On the continuation a red candle above the entry
  price is not evidence against the trade; the under-water read keeps those trades on.

**What the lead takes from the five, for the owner to weigh.** The headline exit (red candle
with the week red) is not the best reading of "against": under water does better on the
continuation and no worse elsewhere. The hourly clock is a different trade, not a better one.
The week's side is a reversal / continuation condition, not an inside-break one. After fees
three lines stand: the reversal held to the exit, and the inside break managed to one R. None of
this is promoted; each is a declared variant whose rows are in `manage_trades.csv.gz`
(columns `*_u` for under water, `*_h` for the hourly clock, `w_support` for the week's side;
E and the fees are arithmetic on the recorded columns) and on the trade viewer.

## Limitations, stated

- No fees, funding, slippage, sizing or liquidation arithmetic. The averages are of the same
  order as a round-trip taker fee; the tail is unsized.
- The exit fill is the daily close; a trader watching the hourly would act sooner or later.
- Days held differ by book (shown); a book against the reference is rule against rule, and
  only D isolates the stop.
- Equal-size sums by entry date, hundreds of trades open at once, correlated across coins on
  the same day: intervals are tighter than the truth.
- MAE counts the entry day's whole adverse extreme, which a daily bar cannot place before or
  after the break; the tail is a conservative daily-bar bound.
- The LIQUID split is the census's snapshot label (last 30 days), retrospective, kept for parity
  with products 1 and 2.
- Survivors only, venue era, 2023-02 to 2026-10; the last 20 days are censored (1,027 daily
  units).
- The ladder is the weekly and monthly levels only, fixed at entry; no daily pivots, no
  quarter, no rolling.

## The trade viewer (TVB-39): every row on its own candles

Visual verification against TradingView was the slowest step of every earlier round and the
step that caught the errors the tables could not. The viewer puts the engine's rows on the raw
candles locally, with no TradingView and no re-run of any trade logic: the entry day, the
targets, the touch days and the exit day are read off `manage_trades.csv.gz` exactly as the
engine wrote them, so a chart that disagrees with a row is evidence against the engine.

    uv run python -m analysis.domino.trade_viewer hourly --as-of 2026-10-10 all   # once, ~9 min
    uv run python -m analysis.domino.trade_viewer build  --as-of 2026-10-10       # ~1 min
    uv run python -m analysis.domino.trade_viewer serve                            # opens the browser
    uv run python -m analysis.domino.trade_viewer serve --no-open                  # from an SSH shell; browse through a port forward

What it shows: one coin at a time (or every trade entered on one day, across coins); 1H / 1D /
1W / 1M toggles (weeks and months bucketed by the census's calendar rules; the venue serves
about 208 days of hourly bars, so older trades say so on the hourly view); candles not in a
trade grey, the setup bar amber, the bar before it dark amber, the trade's own candles green or
red by their close; lines for the entry level ("Position opened"), the exit close ("Position
closed"), T1 / T2 / T3 with their sources, one R, the chance book's setup-bar stop and the
measured move; markers on the first bar that touched each price (on the hourly view, the hour
inside the day); the exit day's test spelled out (close versus the day's open and the week's
open, with the colours); every book's fill for the row; and a strip of trade cards (filters by
unit timeframe, kind, side, liquid, has-T1; the book and an equal size in dollars for the
printed P/L). Arrow keys step through trades. The address bar carries the trade
(`#coin=BTC&date=2025-06-17&tf=D&dir=down&view=1D`), so a trade can be bookmarked or pasted
into a note (`&book=A` carries the book box). The worked example above is that address. The
viewer's data folder and the vendored chart library are regenerable and stay out of the repo.

Added on the owner's first pass (2026-10-12, same session): the book box drives the chart, not
just the cards. The trade's candles run to the selected book's own settle day (`days_X` on the
row), "Position closed" sits at that book's fill (the entry level moved by the recorded return,
so it is the engine's own number) and the out arrow lands on the bar that touched the target
when the book took one; the headline daily clock stays as a small "daily clock out" square when
it left on a different day. Every timeframe the row says broke that day is drawn: the trade's
own trigger as "Position opened", the others as dashed "daily / weekly / monthly trigger, broke
the same day", with a stack line in the details (each trigger's price, the gap between them,
the census band: same price / near / within 1% / spread). On a converged stack the entry line
is labelled "domino". The chart's previous-complete-bar level was checked against every row's
recorded level across all 179,498 units: no mismatch, so the amber "bug hypothesis" note on
that line should never print. A magnet ray tool (Draw / R): a click drops a one-pixel blue line
at the nearest open / high / low / close of the bar under the cursor on the active timeframe;
it stays across the 1H / 1D / 1W / 1M toggles and across trades on that coin (browser storage,
per coin); click near a ray to move it to a finer level on a faster view, Alt+click or the
cross beside its price removes it, Delete removes the last, Clear empties the coin. One viewer
bug fixed: the A2 markers had been spliced between the exit arrow's `if` and its `else`, so a
"data ends" square printed on every exited trade.

Promoted 2026-10-17 (TVB-40): the page above is retired (in git history to da7f4c2) and
`viewer/` is the amCharts 5 page built in the two-builder design-off, on the owner's call after
reviewing both builds. Same rows, same drawn levels and markers, same address form; what is new
is a calendar and sortable table in place of the card strip, the trade narrated in trader
language from the row with every book's fill in a ladder, a Compare tab across the six books
(this coin, this day, or the universe from `data/universe.json`, cross-checked against the CSV
in pandas), a Playbook tab, dual chart panes, the library's drawing toolbar with per-coin save /
restore, and the magnet ray as a drawing in that slot. Receipt, proofs and the open items:
`analysis/domino/viewer/NOTES.md`.

## Provenance

288 coins, 179,498 units (D 153,516, W 21,520, M 4,462): product 2's 179,913 less 415 daily
units in a coin's leading partial week (no week open to test the exit against). Censored at the
cap: 1,027 D, 231 W, 37 M. Anchors: reversal 44,516 anchor / 110 zero; inside 17,295 anchor /
10,519 ladder (with-trend) / 3,749 stacked / 68 zero / 14 unknown; continuation 62,822 ladder;
outside 14,423 ladder. The `census.day_events` extension (the bar before the setup bar) was
checked by rerunning the census offline before and after: `census.json` byte-identical. One BTC
short (2025-06-17) was reconciled by hand against the raw candles: anchor T1 at Sunday's low,
T2 at the prior week's low, T1 touched on the entry day, one R on day 4, the exit at the Monday
close when the day and the new week both turned green, every book's fill as printed. The
numbers above did not move between the first run and the rerun that added the book-D early-exit
column and the T1 distance. The post-audit rerun (amendment A1) moved book D's averages by less
than a hundredth of a point and its target-hit shares by less than 0.01 pp (the float-built
targets missed an exact touch only rarely), replaced the "median days" column with each book's
own holding time, left the 20-day follow-up shares on smaller denominators (incomplete windows
are unknown, not false), and added book D5 and the matched H3 read.
