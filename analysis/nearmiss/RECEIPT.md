# Near-miss study: how close failed daily patterns came to their target -- RECEIPT (TVB-46, 2026-11-21)

**Status: EXPLORATORY.** No prereg, no external audit. The definitions below were agreed with the
owner in conversation before the code was run. The pattern and walk logic has hand-vector tests
(`tests/test_nearmiss.py`, 25 cases, including the STRAT skill's equal-boundary vectors). Nothing
here is a rule, and the P/L lines are theoretical: equal size, no leverage, no fees, fills at the
levels.

## The question (the owner's)

The exit being considered is "within 5 to 10 percent of the distance from entry to the target",
because the target levels tend to be exhaustion points and price often gets near without tagging
them. So: take patterns that FAILED (triggered, did not go scenario 3, never reached the target)
and measure how close they came, as a percent of the way from entry to target.

## Definitions

| term | meaning |
|---|---|
| bars | daily, split-adjusted, strict breaks (equal never breaks a level), setup bars closed |
| 2-2 reversal | a 2, then a 2 the other way is the setup bar, entry through the setup bar's near side. Target = the far wick of the bar BEFORE the setup bar. Stop = the setup bar's far side. The bar before the setup must itself be a 2 (an inside bar there is a rev strat, an outside bar a 3-2-2) |
| 2-1-2 reversal | a 2 against the trade, an inside bar, entry through the inside bar. Target = the 2's far wick. Stop = the 2's other extreme, not the inside bar's |
| 3-1-2 | an outside bar, an inside bar, entry through the inside bar. Target = the 3's wick on the trade side. Stop = the 3's other extreme. Reversal when the 3 closed against the trade, continuation when with it |
| entry | the next daily bar trades strictly through the trigger; price = the trigger level. A bar that opens beyond the trigger is a missed entry; a bar that opens through the setup bar's other side is not this pattern |
| went 3 | the entry bar also took the setup bar's other side. On daily bars the order of the two breaks is unknown. Counted apart; neither won nor failed |
| won | the target was touched before the stop |
| failed | the stop was strictly broken on a later bar before the target was touched |
| progress | for a failed pattern, the furthest point reached toward the target before the stop bar, as a share of the entry-to-target distance ("certain"); "possible" adds the stop bar's own extreme |

**Held out, pending the owner's ruling on the stop:** the rev strats (1-2-2, 1-3-2; the skill
says "trap or inside bar extreme") and the 3-2-2 (the skill says "outside bar extreme", which
the reversing 2 has already broken). The 1-3 needs the order of breaks inside the day.

## Data and how to run

142 symbols: the eleven sector funds, SPY, QQQ, IWM, each sector fund's ten largest holdings and
the high-beta followers (today's lists from `analysis/sector/`), Yahoo daily bars 2000-01 to
2026-11-20. Raw bars are gitignored and re-fetchable.

```
uv run --no-project --with yfinance --with pandas python analysis/nearmiss/fetch.py
uv run python -m analysis.nearmiss.run
uv run pytest tests/test_nearmiss.py -q
```

## What the counts say

**1. The funnel.** 184,917 triggered setups on 6,745 days.

| family | triggered | went 3 on the entry day | of the rest: won | failed | median target distance | median stop distance | target in units of stop |
|---|---|---|---|---|---|---|---|
| 2-2 reversal | 143,714 | 20% | 73% | 27% | 0.95% of price | 1.86% | 0.52 |
| 2-1-2 reversal | 30,428 | 28% | 86% | 14% | 0.49% | 1.98% | 0.24 |
| 3-1-2 reversal | 5,773 | 24% | 78% | 22% | 0.74% | 2.05% | 0.36 |
| 3-1-2 continuation | 5,002 | 27% | 89% | 11% | 0.38% | 2.31% | 0.15 |

The typical win comes on the entry day itself (median zero sessions held); the typical failure
one to two sessions later. The win rates are high because the target is close and the stop is
far: the target sits a fraction of one stop distance away.

**2. How close the failed patterns came.** 34,940 failed patterns. The median one got 43% of
the way (average 45%).

| furthest point reached | under 25% | 25 to 50% | 50 to 75% | 75 to 90% | 90 to 95% | 95% or more |
|---|---|---|---|---|---|---|
| share of failed patterns | 29.5% | 27.6% | 23.8% | 12.4% | 3.8% | 2.9% |

Reached 90% of the way or more: 6.6% for certain, 7.1% possible. Reached 95% or more: 2.9%,
3.0% possible. By family the median runs 42% (2-2 reversal) to 52% (3-1-2 continuation), and the
share that got within the last 10% runs 6.5% to 7.7%.

In 5-point steps the share of failures falls steadily toward the target and is lowest in the
last step: 4.7, 6.1, 6.1, 6.5, 6.1, 5.8, 6.0, 5.7, 5.3, 4.9, 5.2, 4.9, 4.8, 4.6, 4.2, 4.3, 4.2,
3.9, 3.8, 2.9. **There is no pile-up of failures just short of the target on daily bars.**

**3. Moving the exit in.** Same trades in every row (triggered, did not go 3 on the entry day,
resolved at the full target or the stop; 144,651 trades). A bar that touched both the exit and
the stop counts as the stop.

| exit at | wins | per trade, % of price | per trade, R |
|---|---|---|---|
| the target | 75.2% | +0.200% | +0.101 |
| 95% of the way | 76.0% | +0.188% | +0.097 |
| 90% of the way | 76.9% | +0.185% | +0.095 |
| 75% of the way | 80.1% | +0.174% | +0.091 |
| 50% of the way | 86.1% | +0.152% | +0.078 |

Exit at 95%: rescues 1,074 of 35,847 losers (3%) and gives up more than that on the 108,804
winners: net -0.012% per trade. Exit at 90%: rescues 2,477 (7%), net -0.015% per trade. The
ordering (the full target best, each step in a little worse) holds in each family, long and
short, funds and single names, and since 2020 (where the gap narrows to -0.004% and -0.007%).

**4. The whole book, with the went-3 days put back.** The rows in item 3 leave out the 40,266
entries (22%) whose entry day went 3, which no one knows at entry. On 28% of those days the bar
also touched the target, order unknown. Counting every went-3 day as a loss at the setup bar's
other side (average -1.79%), the book at the full target is **-0.234% per trade**; counting the
ones that touched the target as wins, **-0.081%**. Both ends are negative, in every family except
the hopeful end of the 2-1-2 reversal (-0.007%). The early exits do not change the sign:
-0.243% to -0.088% at 95%, -0.246% to -0.084% at 90%.

**5. Splits (the item 3 cohort).** Longs +0.274% per trade and shorts +0.129% at the full target
(survivors: today's large names went up). Funds +0.147%, single names +0.205%. Since 2020
+0.156%. Failed patterns' median progress is 42 to 43% in every split.

## Addendum, same day: the week, the month and the quarter; the 3-2-2 added

The owner's two rulings (2026-11-21): the 3-2-2's stop is the 3 bar's extreme (that the
reversing 2 traded through it before the entry does not matter, no trade was on yet); and the
higher timeframes are the ones of interest. `htf.py` finds the same families on weekly, monthly
and quarterly bars and walks each one on the DAILY bars inside them, so the order of events
inside the entry bar is known:

- entry = the first day inside the entry bar that trades through the trigger (the open on a
  mid-bar gap; the entry BAR opening past the trigger is still a missed entry);
- if the setup bar's other side breaks on an earlier day than the trigger, it is not this
  pattern (dropped);
- **went 3 is now a real exit**: after the entry, while the entry bar is still open, a day takes
  the setup bar's other side, out at that level. Once the entry bar closes only the stop and
  the target remain;
- a single day that breaks both the trigger and the other side is still unknown, but on the
  week and above that is about 1% of entries or less (on the day it is the 22% of item 4).

Run on one daily bar per period, the new code reproduces items 1 to 3 above to the trade
(2-2 reversal: 114,584 trades, 72.7% wins, +0.195%), and a randomized test holds the two walkers
equal (`tests/test_nearmiss.py`, 39 cases). Run: `uv run python -m analysis.nearmiss.run_htf`.

**6. The same measure on each timeframe (five families, both sides).**

| pattern timeframe | entries | won | stopped | went 3 after entry | stopped: median progress | went 3: median progress | stopped that got within the last 10% | sessions to a win (2-2 reversal) |
|---|---|---|---|---|---|---|---|---|
| day | 154,363 | 74% | 25% | not seen (one bar) | 42% | n/a | 6.4% | 0 |
| week | 42,611 | 68% | 23% | 10% | 41% | 21% | 6.7% | 2 |
| month | 10,610 | 69% | 21% | 10% | 43% | 20% | 5.9% | 7 |
| quarter | 3,337 | 68% | 21% | 11% | 43% | 20% | 5.1% | 18 |

Of everything that did not reach its target (stopped or went 3), the share by 10-point step of
the way falls from the first step to the last on every timeframe: week 18.0, 14.5, 12.4, 10.9,
9.2, 9.0, 7.7, 6.6, 6.4, 5.3; month 17.7, 15.0, 12.0, 10.6, 9.6, 8.8, 8.0, 6.6, 7.1, 4.6;
quarter 16.9, 14.9, 13.3, 10.5, 9.4, 7.9, 7.9, 6.5, 8.4, 4.3. **No pile-up just short of the
target on any timeframe; the last tenth of the way holds the fewest.** A pattern that goes 3
after the entry dies early: half of them never got a quarter of the way.

**7. Moving the exit in, by timeframe (every resolved entry; went-3 exits included).**

| pattern timeframe | per trade at the target | at 95% of the way | at 90% | losers rescued at 95% / 90% | net of the early exit at 95% / 90% |
|---|---|---|---|---|---|
| day (the unknown entry days left out) | +0.204% | +0.192% | +0.189% | 2.9% / 6.7% | -0.012% / -0.015% |
| week | -0.062% | -0.077% | -0.080% | 2.3% / 5.4% | -0.014% / -0.017% |
| month | +0.131% | +0.081% | +0.041% | 2.1% / 4.6% | -0.050% / -0.091% |
| quarter | -0.186% | -0.360% | -0.462% | 1.7% / 4.3% | -0.174% / -0.276% |

The early exit costs more the higher the timeframe: fewer near-misses to rescue and a larger
distance given up on each winner. The books themselves sit near zero and split by side with
the names' drift: week longs +0.273% and shorts -0.398%; month +1.166% and -0.877%; quarter
+3.709% and -3.910% (today's large names went up for 25 years; this is the survivor list
talking, not the pattern).

**8. Geometry by timeframe (medians).** The target is always a fraction of the stop distance
for the reversals off a 2 or an inside bar, and about one stop distance for the 3-2-2:

| family | week: target / stop, % of price | month | quarter |
|---|---|---|---|
| 2-2 reversal | 2.07 / 4.39 | 4.38 / 9.57 | 7.38 / 16.85 |
| 2-1-2 reversal | 1.20 / 4.77 | 2.77 / 11.33 | 4.87 / 20.38 |
| 3-1-2 reversal | 1.86 / 4.80 | 3.39 / 10.70 | 6.18 / 21.71 |
| 3-1-2 continuation | 0.78 / 6.06 | 1.67 / 14.73 | 3.30 / 19.06 |
| 3-2-2 reversal | 3.06 / 2.82 | 6.60 / 6.06 | 10.38 / 11.69 |

**9. The 3-2-2 with the owner's stop.** About half win on every timeframe (week 52%, month
49%, quarter 52%) with a target about as far as the stop; it never goes 3 as a separate exit
because its stop sits nearer than the setup bar's other side. Per trade: week +0.038%, month
-0.233%, quarter +0.468%. Its failures got the least of the way (median 26 to 27%).

## Read both ways

- A kill test that landed on every timeframe: failed patterns do not cluster just under the
  target, on the day, week, month or quarter. The early exit rescues 2 to 7% of losers and
  costs more than it saves, increasingly so on the higher timeframes.
- A path worth naming: going 3 after the entry is an early death (median 20% of the way) and is
  one trade in ten on the week and above; a rule that leaves at that moment is what this walk
  already does, and anything that anticipates it is worth more than the exit's placement.
- A path worth naming: time to the target when it works. Week targets (about 1 to 3% away)
  were reached in a median of one to two sessions, month targets (about 3 to 7%) in three to
  nine: the holding period an option on these would need.
- A kill test that landed: on daily bars, for these families, failed patterns do not cluster
  just under the target. An exit 5 to 10% short rescues 3 to 7% of the losers and costs slightly
  more on the winners than it saves.
- A path worth naming: the pattern's own daily target is usually a same-day event and close
  (under 1% of price). The owner's observation may belong to larger targets (the week's or
  month's high and low) or to the path inside the day; neither is counted here.
- A path worth naming: the entry day going 3 is the whole difference between a positive and a
  negative book (22% of entries). Anything known at the entry that lowers that share matters
  more than where the exit sits. The order of breaks on those days needs intraday bars.
- Agrees with the earlier work: targets get reached (three in four of the entries that did not
  go 3) and the book still loses once every entry is counted.

## Limitations

- Survivors and hindsight: today's sector holdings and today's high-beta names, back to 2000.
- Daily bars: the order of events inside one bar is unknown. That is why went-3 days are set
  apart and why a bar touching both the exit and the stop is given to the stop.
- Fills at the level: entry at the trigger, exit at the target or the stop; a gap through the
  stop fills at the open. No fees, no slippage, no option pricing.
- Clustered dates: 142 names break on the same days; the trade count overstates independent
  events.
- The rev strats (1-2-2, 1-3-2, 1-3) are still held out: their stop ("trap or inside bar
  extreme") is not ruled. The 3-2-2 runs in the addendum with the owner's stop; items 1 to 5
  are the first three families only.
- A 3-2-2 entry day that opened beyond the stop and closed back on the trade's side is taken as
  not stopped by its own open (the dip is read as coming before the entry).
