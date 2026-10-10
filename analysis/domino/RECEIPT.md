# Daily / weekly / monthly domino census -- RECEIPT (TVB-37, 2026-10-10)

**What this is:** a count, pre-registered in `docs/experiments/tvb37_domino_census_prereg.md`
(definitions fixed before the script existed; owner approval of the card 2026-10-09). It answers
one question with arithmetic: how often do the venue's perps break two, three or four
higher-timeframe levels together, how close did those levels sit, what kind of setup each level
completed, how often the setup bar was a hammer or shooter, and where the quarter stood.
**No entry, stop, target, outcome or P&L exists here.** Engine: `analysis/domino/census.py`;
numbers: `results/census.json`; every table for every split: `results/tables.md`; the rank 2+
event rows: `results/events_rank2plus.csv.gz` (regenerable, not committed).

Data: the venue's public daily candles, full available history per coin, read 2026-10-10 UTC
(closed days only). Week, month and quarter are built on the calendar from the dailies (Monday
00:00 UTC; the 1st; Jan / Apr / Jul / Oct). Universe: every live perp on the main dex and the xyz
dex, 292 coins. LIQUID = median daily notional over the last 30 closed days of at least 1M USD.

## Trader's glossary for the tables

| term in the tables | what it means on the chart |
|---|---|
| event | one coin, one day, one direction: the day traded through yesterday's high (up) or yesterday's low (down) |
| rank 1 | the day took only yesterday's level |
| rank 2 / 3 / 4 | the day also took last week's, last month's and/or last quarter's high (or low) for the first time in that bar |
| day + week | yesterday's high and last week's high both taken today (mirror for lows) |
| EXACT | yesterday's level and the higher-timeframe level are the same price |
| NEAR | the levels sit within a quarter percent of each other |
| WITHIN 1% / SPREAD | up to 1% apart / more than 1% apart |
| shared open | a Monday, the 1st of the month or the 1st of a quarter: the new bar opened with the day, and yesterday was the last day of the old bar |
| plain day | any other day |
| reversal | the bar before the break was a 2 the other way, so today's break prints a 2-2 reversal |
| continuation | the bar before was a 2 the same way: a 2-2 continuation |
| inside break | the bar before was an inside bar: a 1-2 |
| outside break | the bar before was an outside bar: a 3-2 |
| THIRD | the setup bar closed in its far third: a hammer (up break) or a shooter (down break) by the 33% rule |
| STRICT | THIRD, and no wick beyond the body on the far side except a sliver (one tenth of the bar's range or less) |
| quarter states | where price sits against last quarter's high and low at the moment of the break: taking it today, already through it the break's way, still inside on the break's side of the quarter's open, inside on the other side, already through it the OTHER way, both sides already taken, or no full prior quarter yet |
| month outside the stack | the month did not break today: is price on the break's side of this month's open, and had the month already broken that way earlier this month |

## Depth

| coins | with a complete prior week | prior month | prior quarter | liquid |
|---|---|---|---|---|
| 292 | 287 | 280 | 258 | 141 |

214,861 coin-days in ALL; 105,907 in LIQUID. The xyz dex (114 coins) holds 19,058 coin-days, so
most of its coins have no complete prior quarter yet (quarter state "unknown" below).

## Checks (bug tests declared in the prereg)

- Nesting: every week, month and quarter first break was also a daily break that day. Violations:
  0 in every split.
- Week outside the stack: whenever a month or quarter broke without the week breaking that day,
  the week had already broken the same way (3,499 of 3,499). That is the calendar nesting showing
  up where it must; it is a consistency check, not a finding.
- Row totals reconcile across tables (quarter states, support columns, rank counts).

## Headline tables, ALL (292 coins)

### Events by rank
| rank | up | down | share |
|---|---|---|---|
| 1 (the day alone) | 82,357 | 84,838 | 84.1% |
| 2 | 13,249 | 14,390 | 13.9% |
| 3 | 1,296 | 2,039 | 1.7% |
| 4 | 153 | 374 | 0.3% |

Rank 2+ = 31,501 events. Per coin, rank 2+ runs at a median 14.7 per 100 closed days (lower
quartile 14.1, upper 15.3, min 11.8, max 18.4 across 258 coins with 100+ days).

### Which levels broke together (rank 2+)
| timeframes | up | down | share of rank 2+ |
|---|---|---|---|
| day + week | 11,599 | 12,959 | 78.0% |
| day + month | 1,368 | 1,140 | 8.0% |
| day + week + month | 1,072 | 1,629 | 8.6% |
| day + quarter | 282 | 291 | 1.8% |
| day + week + quarter | 102 | 114 | 0.7% |
| day + month + quarter | 122 | 296 | 1.3% |
| day + week + month + quarter | 153 | 374 | 1.7% |

### How close the broken levels sat (rank 2+; largest gap, percent of the lowest level)
| band | rank 2 | rank 3 | rank 4 | all rank 2+ | share |
|---|---|---|---|---|---|
| EXACT (same price) | 4,951 | 95 | 10 | 5,056 | 16.1% |
| NEAR (up to 0.25%) | 1,451 | 90 | 10 | 1,551 | 4.9% |
| WITHIN 1% | 4,119 | 280 | 31 | 4,430 | 14.1% |
| SPREAD (over 1%) | 17,118 | 2,870 | 476 | 20,464 | 65.0% |

The owner's "stacked" (EXACT or NEAR) = 6,607 events, 21.0% of rank 2+, which is about 3 per
coin per 100 days at the median rate. Among rank 3 and 4 events (3,862), EXACT or NEAR = 205
(5.3%).

### Shared-open days (a new week, month or quarter opened with the day)
| day type | rank 2+ | exact | near | within 1% | spread |
|---|---|---|---|---|---|
| shared open | 13,453 | 5,003 | 561 | 1,656 | 6,233 |
| plain day | 18,048 | 53 | 990 | 2,774 | 14,231 |

Exact stacks live almost entirely on shared-open days (5,003 of 5,056). Near stacks split the
other way (990 of 1,551 on plain days).

### Setup kind per timeframe (all events)
| timeframe | reversal | continuation | inside break | outside break |
|---|---|---|---|---|
| day | 29.2% | 40.7% | 20.9% | 9.2% |
| week | 28.8% | 39.6% | 22.1% | 9.5% |
| month | 29.7% | 40.9% | 20.7% | 8.8% |
| quarter | 34.7% | 39.4% | 22.1% | 3.8% |

### Hammer / shooter flags on reversal setup bars (the resource's normal hammer)
| timeframe | reversal setups | THIRD | STRICT (third + sliver wick) |
|---|---|---|---|
| day | 57,912 | 10,283 (17.8%) | 4,921 (8.5%) |
| week | 7,999 | 1,344 (16.8%) | 636 (8.0%) |
| month | 1,757 | 363 (20.7%) | 135 (7.7%) |
| quarter | 535 | 106 (19.8%) | 46 (8.6%) |

### Quarter state at rank 2+ breaks
| state | up breaks | down breaks |
|---|---|---|
| quarter breaks today (in the stack) | 659 | 1,075 |
| already broken out the break's way | 2,022 | 4,958 |
| inside, level on the break's side of the quarter's open | 4,406 | 3,756 |
| inside, level on the other side | 1,310 | 2,188 |
| already broken out the OTHER way | 3,932 | 1,910 |
| already an outside quarter | 227 | 258 |
| unknown (no complete prior quarter) | 2,142 | 2,658 |

### Month outside the stack (rank 2+ events where the month did not break)
Level on the break's side of the month's open: 17,817; other side: 6,207. Month already broken
the break's way: 7,971; not yet: 16,053; unknown: 1,323.

## LIQUID (141 coins) in one line each

Rank 2+ = 15,664 of 98,364 events (15.9%); EXACT 2,521 + NEAR 845 = 3,366 (21.5% of rank 2+);
day + week = 12,207 (77.9%); median rank 2+ rate 14.9 per 100 days; hammer flags on reversal
setups: THIRD 17.5% / STRICT 8.0% on the day, 17.7% / 8.0% on the week, 22.3% / 8.8% on the
month. The liquid split moves no headline share by more than a point. Full tables in
`results/tables.md`, with the main-dex and xyz-dex splits.

## What the arithmetic says (and nothing more)

- About one day in six with a daily break also took a higher-timeframe level for the first time.
  Nearly four in five of those were day plus week.
- One rank 2+ event in five had its levels at one price or within a quarter percent. The exact
  ones are a shared-open phenomenon: the last day of the old bar made its extreme, so Monday or
  the 1st opened with the levels stacked.
- Three- and four-level days are rare (1.7% and 0.3% of events) and almost never stacked tight.
- Reversal setups are under a third of breaks on every timeframe; of those, about one in six
  setup bars passes the top-third test and about one in twelve the strict no-wick version.
- Up and down are close to symmetric in count; down leads slightly on the higher ranks.

Not said here, by design: whether any of these events made money, which band or rank is "better",
or any rule. Those need outcomes, a prereg of their own, and the owner's hierarchy rulings.

## Limitations

- Daily candles carry no intraday order: when two levels sit apart and both broke the same day,
  the count cannot say which broke first or whether price ran through both in one push. An
  intraday pass on the venue's 1h history (about 200 days) is a separate product.
- History is the venue's: the oldest main-dex coins reach back to 2023; xyz coins mostly under a
  year, so their quarter state is usually unknown and their monthly samples are small.
- 24/7 calendar bars on perps are not the underlying's regular-hours bars; the Underlying-RTH
  mirror rule applies to performance tests, and this confound is stated, not resolved.
- The bands (0.25%, 1%), the 10% sliver and the 1M floor were declared a priori and were not
  moved on what the count shows.
