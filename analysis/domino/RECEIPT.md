# Daily / weekly / monthly domino census -- RECEIPT (TVB-37, 2026-10-10, revised the same day after the external audit)

**What this is:** a count, pre-registered in `docs/experiments/tvb37_domino_census_prereg.md`
(definitions fixed before the script existed; owner approval of the card 2026-10-09). It answers
one question with arithmetic: how often do the venue's perps break two, three or four
higher-timeframe levels together, how close did those levels sit, what kind of setup each level
completed, how often the setup bar was a hammer or shooter, and where the quarter stood.
**No entry, stop, target, outcome or P&L exists here.** Engine: `analysis/domino/census.py`;
numbers: `results/census.json`; every table for every split: `results/tables.md`; the rank 2+
event rows: `results/events_rank2plus.csv.gz` (regenerable, not committed).

**Audit:** Codex reviewed commit 8b800a7 the same day (`docs/reviews/tvb37-codex-audit.md`,
verdict NEEDS-CHANGES, twelve findings, one HIGH). The engine was fixed on every finding, the
tests grew from 7 to 16 hand vectors, and the census was re-run from the cached candles. The
committed counts moved by at most four hammer flags (bars whose wick sat exactly on the ten
percent line now count, as the definition says). The wording corrections are applied below and
tagged with the finding they answer [F1 .. F12]; the prereg carries the labelled amendments.

Data: the venue's public daily candles, full available history per coin, read 2026-10-10 UTC
(closed days only). Week, month and quarter are built on the calendar from the dailies (Monday
00:00 UTC; the 1st; Jan / Apr / Jul / Oct). Universe: every perp LISTED on the main dex and the
xyz dex on the run day, 292 coins, so the count is **survivors only**: a coin delisted before the
run is absent with its whole history [F10]. LIQUID = median daily notional (candle volume in
coins times close) over the last 30 closed days of at least 1M USD; it is today's membership
applied to each coin's full history, not a historical label [F10]. Nothing was excluded for a
fetch failure or for being too new (the run records both; the lists are empty) [F9].

**Provenance [F11]:** the venue's API serves daily candles from before a coin ever traded there,
with zero volume: BTC's series starts 2020-08-19 and its first traded day is 2023-02-26. Those
bars are index prices, not venue bars. 94 coins carry such a prefix, 48,331 coin-days in all
(22% of ALL), every one on the main dex. The VENUE ERA split below starts each coin at its first
traded day so the reader can see what the backfill contributes.

## Trader's glossary for the tables

| term in the tables | what it means on the chart |
|---|---|
| event | one coin, one day, one direction: the day traded through yesterday's high (up) or yesterday's low (down). An outside day breaks both ways and is TWO events [F8] |
| break day | a coin-day with at least one event, either direction |
| rank 1 | the day took only yesterday's level |
| rank 2 / 3 / 4 | the day also took last week's, last month's and/or last quarter's high (or low) for the first time in that bar |
| day + week | yesterday's high and last week's high both taken today (mirror for lows) |
| EXACT | yesterday's level and the higher-timeframe level are the same price |
| NEAR | the levels sit within a quarter percent of each other (a quarter percent exactly counts) |
| WITHIN 1% / SPREAD | up to 1% apart / more than 1% apart |
| shared open | a Monday, the 1st of the month or the 1st of a quarter: the new bar opened with the day, and yesterday was the last day of the old bar |
| plain day | any other day |
| reversal | the bar before the break was a 2 the other way, so today's break prints a 2-2 reversal |
| continuation | the bar before was a 2 the same way: a 2-2 continuation |
| inside break | the bar before was an inside bar: a 1-2 |
| outside break | the bar before was an outside bar: a 3-2 |
| not classified | the setup bar has no bar before it to classify against (the first bars of a listing); counted, outside the percentages [F5] |
| THIRD | the setup bar closed in its far third: a hammer (up break) or a shooter (down break) by the 33% rule |
| STRICT | THIRD, and no wick beyond the body on the far side except a sliver (one tenth of the bar's range or less, one tenth exactly counts) |
| quarter states | where price sits against last quarter's high and low at the moment of the break: taking it today, already through it the break's way, still inside on the break's side of the quarter's open, inside on the other side (a level exactly AT the open counts as the other side [F7]), already through it the OTHER way, both sides already taken, or no full prior quarter yet |
| month outside the stack | the month did not break today: is price on the break's side of this month's open, and had the month already broken that way earlier this month |
| venue era | each coin counted from its first day with traded volume on the venue; the zero-volume index history before it is left out |

## Depth

| coins | with a complete prior week | prior month | prior quarter | liquid | with an index-price prefix |
|---|---|---|---|---|---|
| 292 | 287 | 280 | 258 | 141 | 94 |

214,861 coin-days in ALL (closed days minus each coin's first); 175,891 of them are break days.
LIQUID: 105,907 coin-days. VENUE ERA: 166,530 coin-days. The xyz dex (114 coins) holds 19,058
coin-days; 84 of its coins have at least one complete prior quarter, but most of their rank 2+
events happened before it existed, so their quarter state usually reads "unknown" [F11].

## Checks (bug tests declared in the prereg, strengthened after the audit)

- Nesting: every week, month and quarter first break was also a daily break that day, checked at
  every rank now, not only rank 2+ [F2]. Violations: 0 in every split.
- Data quality [F1]: 0 duplicate candles, 0 timestamps off the 00:00 UTC grid, 0 missing days
  inside any series, 0 days skipped for a missing yesterday. The engine now proves contiguity
  rather than assuming it; a complete bar means every calendar day present exactly once.
- Week outside the stack: whenever a month or quarter broke without the week breaking that day,
  the week had already broken the same way (3,499 of 3,499). Calendar nesting, not a finding.
- Row totals reconcile across tables (quarter states, support columns, rank counts, event rows
  against aggregates). 16 hand-vector tests pass, including the audit's reproduced failures.

## Headline tables, ALL (292 coins)

### Events by rank
| rank | up | down | share of events | down's share |
|---|---|---|---|---|
| 1 (the day alone) | 82,357 | 84,838 | 84.1% | 50.7% |
| 2 | 13,249 | 14,390 | 13.9% | 52.1% |
| 3 | 1,296 | 2,039 | 1.7% | 61.1% |
| 4 | 153 | 374 | 0.3% | 71.0% |

Rank 2+ = 31,501 events, 15.9% of 198,696 directional events. By days: 31,356 of the 175,891
break days carried a rank 2+ break, 17.8% [F8]. Per coin, rank 2+ runs at a median 14.7 events
per 100 eligible days (lower quartile 14.1, upper 15.3, min 11.8, max 18.4 across the 258 coins
with 100+ days).

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

The owner's "stacked" (EXACT or NEAR) = 6,607 events, 21.0% of rank 2+, about 3 per coin per
100 days at the median rate. Among rank 3 and 4 events (3,862), EXACT or NEAR = 205 (5.3%).

### Shared-open days (a new week, month or quarter opened with the day)
| day type | rank 2+ | exact | near | within 1% | spread |
|---|---|---|---|---|---|
| shared open | 13,453 | 5,003 | 561 | 1,656 | 6,233 |
| plain day | 18,048 | 53 | 990 | 2,774 | 14,231 |

99% of exact stacks fell on shared-open days (5,003 of 5,056): the last day of the old bar made
its extreme, so the new bar opened with yesterday's level and the higher level at one price. The
other 53 came on plain days where yesterday retouched the higher level without breaking it and
today broke both at that one price [F11]. Near stacks split the other way (990 of 1,551 on plain
days).

### Setup kind per timeframe (percent of CLASSIFIED setups; the last column sits outside) [F5]
| timeframe | reversal | continuation | inside break | outside break | not classified |
|---|---|---|---|---|---|
| day | 29.2% | 40.7% | 20.9% | 9.2% | 250 |
| week | 28.8% | 39.6% | 22.1% | 9.5% | 261 |
| month | 29.7% | 40.9% | 20.7% | 8.8% | 231 |
| quarter | 34.7% | 39.4% | 22.1% | 3.8% | 194 |

### Hammer / shooter flags on reversal setup bars (the resource's normal hammer)
| timeframe | reversal setups | THIRD | STRICT (third + sliver wick) |
|---|---|---|---|
| day | 57,912 | 10,285 (17.8%) | 4,923 (8.5%) |
| week | 7,999 | 1,344 (16.8%) | 637 (8.0%) |
| month | 1,757 | 363 (20.7%) | 135 (7.7%) |
| quarter | 535 | 106 (19.8%) | 46 (8.6%) |

### Quarter state at rank 2+ breaks
| state | up breaks | down breaks |
|---|---|---|
| quarter breaks today (in the stack) | 659 | 1,075 |
| already broken out the break's way | 2,022 | 4,958 |
| inside, level on the break's side of the quarter's open | 4,406 | 3,756 |
| inside, level on the other side (or exactly at the open) | 1,310 | 2,188 |
| already broken out the OTHER way | 3,932 | 1,910 |
| already an outside quarter | 227 | 258 |
| unknown (no complete prior quarter) | 2,142 | 2,658 |

### Month outside the stack (rank 2+ events where the month did not break)
Level on the break's side of the month's open: 17,817; other side: 6,207. Month already broken
the break's way: 7,971; not yet: 16,053; unknown: 1,323.

## VENUE ERA beside ALL (each coin from its first traded day) [F11]

| share | ALL | VENUE ERA |
|---|---|---|
| coin-days | 214,861 | 166,530 |
| rank 2+ of events | 15.9% | 15.8% |
| rank 2+ of break days | 17.8% | 17.8% |
| day + week of rank 2+ | 78.0% | 78.4% |
| stacked (EXACT or NEAR) of rank 2+ | 21.0% | 21.4% |
| exact stacks on shared-open days | 99.0% | 99.1% |
| down's share at rank 2 / 3 / 4 | 52% / 61% / 71% | 53% / 62% / 74% |
| reversal setups, day / week / month / quarter | 29% / 29% / 30% / 35% | 29% / 29% / 30% / 37% |
| THIRD on reversal setups, day / week / month / quarter | 17.8% / 16.8% / 20.7% / 19.8% | 17.6% / 16.6% / 20.8% / 21.8% |
| STRICT on reversal setups, day / week / month / quarter | 8.5% / 8.0% / 7.7% / 8.6% | 8.5% / 8.2% / 7.3% / 9.5% |
| median rank 2+ per 100 days | 14.7 | 14.7 |

Removing the 48,331 index-price days moves the day and week shares by half a point or less. The
quarter rows move more because they are small (399 reversal setups in the venue era).

## LIQUID (141 coins)

Rank 2+ = 15,664 of 98,364 events (15.9%; 17.9% of break days); EXACT 2,521 + NEAR 845 = 3,366
(21.5% of rank 2+); day + week = 12,207 (77.9%); median rank 2+ rate 14.9 per 100 days; down's
share at rank 2 / 3 / 4 = 50% / 56% / 65%. Hammer flags on reversal setups: THIRD 17.5% / STRICT
8.0% on the day, 17.7% / 8.0% on the week, 22.3% / 8.8% on the month, 13.5% / 5.5% on the quarter
(275 setups). Against ALL, the day and week shares move by less than a point; the monthly THIRD
share moves 1.6 points and the quarterly one 6 points on a few hundred bars [F11]. Full tables
in `results/tables.md`, with the main-dex, xyz-dex and venue-era splits.

## What the arithmetic says (and nothing more)

- About one directional break in six (15.9% of events) also took a higher-timeframe level for
  the first time; counted by days it is 17.8% of break days, because an outside day breaks both
  ways and is two events [F8]. Nearly four in five of those were day plus week (78.0%).
- One rank 2+ event in five (21.0%) had its levels at one price or within a quarter percent.
  99% of the exact ones fell on shared-open days: the last day of the old bar made its extreme.
  The rest are plain-day retouches [F11].
- Three- and four-level EVENTS are rare (1.7% and 0.3% of events) and seldom stacked tight (5.3%).
- Reversal setups are 29% to 30% of classified setups on the day, week and month, and 35% on
  the quarter (535 setups) [F11]. Of reversal setup bars, THIRD runs 16.8% (week) to 20.7%
  (month); STRICT, the sliver-wick version, runs 7.7% to 8.6% [F11].
- 51% of all events are down. Down's share rises with rank: 52% at rank 2, 61% at rank 3, 71% at
  rank 4 [F11].
- Starting each coin at its first traded day changes no day or week share by more than half a
  point [F11].

Not said here, by design: whether any of these events made money, which band or rank is "better",
or any rule. Those need outcomes, a prereg of their own, and the owner's hierarchy rulings.

## Limitations

- Daily candles carry no intraday order: when two levels sit apart and both broke the same day,
  the count cannot say which broke first or whether price ran through both in one push. An
  intraday pass on the venue's 1h history (about 200 days) is a separate product.
- History is what the venue's API serves: 48 coins reach back before 2023 and the oldest to
  2020-08-19, but no coin traded on the venue before 2023-02-26; the earlier bars are zero-volume
  index prices (see Provenance and the VENUE ERA split) [F11]. xyz coins mostly have under a year,
  so their quarter state is usually unknown and their monthly samples are small.
- Survivors only: delisted coins are absent with their whole history [F10].
- The candle cache is keyed by run day, so a later correction by the venue to a served candle
  would not be noticed inside the same day [F11].
- 24/7 calendar bars on perps are not the underlying's regular-hours bars; the Underlying-RTH
  mirror rule applies to performance tests, and this confound is stated, not resolved.
- The bands (0.25%, 1%), the 10% sliver and the 1M floor were declared a priori and were not
  moved on what the count shows. Boundary cases sit inside their band by decimal arithmetic [F3, F6].
