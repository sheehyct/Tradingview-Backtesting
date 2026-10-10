# TVB-37 -- daily / weekly / monthly domino census -- pre-registration

**LABEL: CHARACTERIZATION COUNT, NO P&L. Definitions fixed here BEFORE any
number was read. Nothing in this document is a strategy; it is the first data
product under the owner's 2026-10-04 redirect ("step back to focus on the data
aspect"; trade the daily, weekly and monthly only; rank by levels broken
together). It counts how often the venue's perps break two, three or four
higher-timeframe levels together, with the distances, the setup kinds, the
hammer / shooter flags and the quarter state attached. It cannot validate a
rule and is not read as one.**

- Declared: 2026-10-10, before the script existed. Owner approval of the
  definitions card: 2026-10-09 ("Yes the card reads right we can go when
  ready"). Rulings behind it: 2026-10-04 (domino = at least two levels stacked,
  any time, not only at shared opens; quarter = context), 2026-10-05 (calendar
  quarter; quarter preference = not inside and in favor, or inside but the
  trade's color; hammer = the resource's basic shape, momo left out),
  2026-10-09 (a sliver of wick allowed; every break of the prior bar's high or
  low is taken for data, continuations included).
- Engine: `analysis/domino/census.py` (this repo). Data: the venue's public
  daily candles, full available history per coin, cached locally
  (`analysis/domino/data/`, gitignored). Results: `analysis/domino/results/`.
  Receipt: `analysis/domino/RECEIPT.md`.

## Definitions (a-priori)

1. **Universe.** Every perp listed on the main dex and the xyz dex at run time,
   delisted names excluded. Two reporting splits, declared now: ALL, and
   LIQUID = median daily notional volume over the last 30 closed days of at
   least 1 million USD (the bot's own floor). Listing depth is recorded per
   coin; nothing is dropped for being new, it just has fewer complete bars.
2. **Bars.** Day = the venue's 1d candle (00:00 UTC). Week, month and quarter
   are built from daily candles on the calendar: week opens Monday 00:00 UTC,
   month on the 1st, quarter on Jan 1 / Apr 1 / Jul 1 / Oct 1. A partial first
   bucket is dropped, as the scanner does, so no level is understated. The
   forming day is excluded; only closed days are read. (The venue's own 1w /
   1M candles are NOT calendar bars and are not used.)
3. **Levels.** For a day inside a given week / month / quarter, that
   timeframe's levels are the previous COMPLETE calendar bar's high and low.
   The day's own levels are the previous day's high and low.
4. **Break.** Strict: a day breaks a level up when its high is above the level
   and the running high of the current higher-timeframe bar BEFORE that day
   was not above it (first break only; equality never breaks, ruling R10).
   Mirror for down. The daily level is fresh every day.
5. **Event and rank.** One coin, one day, one direction. S = the set of
   timeframes among day, week, month, quarter whose levels that day broke for
   the first time. Rank = the size of S. Rank 1 = a plain daily break. Rank 2+
   is the domino candidate set.
6. **Stack distance.** Among the levels in S, the largest pairwise distance as
   a percent of the lowest level. Bands, declared now: EXACT (zero), NEAR
   (above zero, up to 0.25%, the dashboard's domino band), WITHIN 1%, SPREAD
   (above 1%). The owner's "stacked" is EXACT or NEAR; the ruling on where
   stacked ends is still theirs, so every band is reported.
7. **Setup kind per timeframe in S.** From the previous bar of that timeframe
   relative to its own predecessor: 2 against the break = REVERSAL (a 2-2
   reversal), 2 with the break = CONTINUATION (2-2 continuation), inside bar =
   INSIDE BREAK, outside bar = OUTSIDE BREAK. The current bar's final type is
   not known at the break and is not used.
8. **Hammer / shooter flags**, on the previous bar of each timeframe in S.
   THIRD (the resource and ruling R20): open and close both in the far third
   of that bar's own range, on the side the break goes (top third before an
   up break = hammer; bottom third before a down break = shooter). STRICT
   (the owner's trial, 2026-10-09 "sliver allowed"): THIRD and the wick beyond
   the body on the closing side at most 10% of the bar's own range. Reported
   on the REVERSAL subset (the resource's "normal" hammer: a 2 against the
   break that closes as a hammer) and on all setup bars for reference. The
   bar before the setup bar is recorded, never used to filter.
9. **Quarter state** at the break, for the break's direction: UNKNOWN (no
   complete prior quarter); BREAKS TODAY (quarter in S); BROKEN OUT BEFORE
   (the quarter already past the prior quarter's level on the break's side
   before this day); INSIDE WITH (still inside, and the broken level sits on
   the break's side of the quarter's open); INSIDE AGAINST (inside, other
   side of its open); OPPOSITE (already broken out the other way); BOTH
   (already an outside quarter).
10. **Support outside the stack.** For week and month when not in S: whether
    the broken level sits on the break's side of that timeframe's open
    (green for an up break, red for a down break) and whether that timeframe
    had already broken out the break's way. Counted, never gated.
11. **Shared opens.** Days where the day shares its open with a new week, a
    new month or a new quarter are flagged (coupling, skill 4.5). Rank 2+
    events are split by whether they fell on such a day.
12. **Sanity checks, declared as bug tests:** every week / month / quarter
    first break must also be a daily break that day (the nesting of calendar
    bars makes it so; a violation is a bug, not a finding); rank 2+ events
    must have at least two distinct timeframes.

## Reporting

Counts and shares only: events by rank and direction; composition of S;
distance bands within rank 2+; setup kinds and hammer flags per timeframe;
quarter states; support outside the stack; shared-open split; per-coin event
rates as a distribution (median and spread per 100 days), with NO coin
ranked or named as best. The LIQUID split repeats the headline tables.

## Not in this census

No entry prices, stops, targets, outcomes or P&L. No intraday ordering of the
breaks within a day (daily candles do not carry it; an intraday pass on the
venue's 1h history is a separate, later product). No underlying-equity
mirror run (the Underlying-RTH mirror rule applies to performance tests; the
confound is stated in the receipt). No tuning of the 0.25% band, the 10%
sliver or the 1 million floor on what the count shows.
