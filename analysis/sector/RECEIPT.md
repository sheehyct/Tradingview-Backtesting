# Sector continuity breadth: first look -- RECEIPT (TVB-45, 2026-11-19)

> Numbering note: the first commit of this work (3095029) says TVB-46 in its message. The
> session is TVB-45; the commit message is wrong and is left as pushed.

**Status: EXPLORATORY.** No prereg, no tests, no external audit. Definitions were agreed with
the owner in conversation before each count was run and are restated below. Everything here is
a count of states or a description of how prices moved together on daily closes. **No entry,
stop, target, trade or P&L exists here, and nothing here is a rule.** One cross-check was done:
the states this code prints for 2026-11-19 match a separate hand calculation from TradingView
monthly bars for all eleven sector funds.

## What this is

The owner's idea (2026-11-18/19): read timeframe continuity across the market as breadth and
sector rotation, and watch sectors move from agreement into conflict and back. The hourly is out
(noise); the stack is **week, month, quarter, half-year, year**; the day is early warning only.

## Definitions

| term | meaning |
|---|---|
| level | a period's opening price (week, month, quarter, half-year, year). NOT a prior bar's high or low; do not read this as the domino census |
| shared open | when two or more periods opened at the same price they are ONE level (the STRAT skill's coupling rule). Quarter = half-year = year all of Q1; half-year = year in Q2; quarter = half-year in Q3. All five are distinct only in November and December (14% of days) |
| full agreement up / down | the daily close is above every distinct level / at or below every one (a close exactly at an open counts as below) |
| conflict | anything else |
| crack | the day a fund leaves full agreement |
| healed | it returns to the same full agreement |
| every level | it reaches full agreement the other way |
| deep | the crack lost three or more distinct levels, or every level |
| by-count read | how many of the fund's ten largest holdings had already left full agreement the day before the crack |

## Data

Yahoo daily bars through `yfinance` (not a project dependency; run with `--with yfinance`),
unadjusted open and close for states, adjusted close for returns. Eleven sector SPDRs
(nine from 1998-12-22, XLRE from 2015-10, XLC from 2018-06) through 2026-11-19. Holdings and
weights are **today's** top-ten lists from the fund data. Raw bars are cached under `data/` and
`members/` and are not committed (re-fetchable).

## How to run

```
uv run --no-project --with yfinance --with pandas --with numpy python analysis/sector/fetch.py analysis/sector/data
uv run --no-project --with pandas --with numpy python analysis/sector/levels.py analysis/sector/data analysis/sector
uv run --no-project --with yfinance --with pandas python analysis/sector/holdings.py analysis/sector
uv run --no-project --with pandas --with numpy python analysis/sector/inside.py analysis/sector
uv run --no-project --with yfinance --with pandas --with numpy python analysis/sector/themes.py analysis/sector
uv run --no-project --with yfinance --with pandas --with numpy python analysis/sector/followers.py analysis/sector
uv run --no-project --with pandas --with numpy --with scikit-learn python analysis/sector/cushion.py analysis/sector
uv run --no-project --with pandas --with numpy python analysis/sector/stayed_out.py analysis/sector
```

`stayed_out.py` reads the files `inside.py` and `cushion.py` write, so run it last.

`census.py` and `refine.py` are the first two passes, kept because they hold the TRAP below.
`probe.py` is the feasibility probe for theme funds and one follower example.

## TRAP (kept so nobody rebuilds it)

Counting the five periods separately makes each further "domino" look MORE likely than the last
(58%, 64%, 70%) and shows funds going from full agreement up to full agreement down in a median
of one to two days. That is one shared opening price being counted two or three times. With
shared opens counted once the progression reverses (below).

## What the counts say

**1. Cracks, eleven sector funds, shared opens as one level.**
Leaving full agreement up with four or more distinct levels (2,387 cracks): about half heal
after losing one level, usually within three trading days. Of cracks that lost at least one
level, 47% lost two; of those, 37% lost three; of those, 28% lost four. Every level lost: 6%
(four levels in play, median nine days) to 9% (five). Leaving full agreement down (970 cracks):
52%, 45%, 49%; every level regained 14% to 18%.

**2. Breadth.** For the nine long-history sectors: no sector in full agreement either way on
10.5% of days; five or more in full agreement up on 19.3%; five or more in full agreement down
on 8.4%. On 2026-11-19 all eleven were in conflict.

**3. Inside the sector (2010 on, today's ten largest holdings, 2,848 cracks on 1,432 dates).**
The day before a typical crack five of the ten largest names have already cracked.

| largest names already out the day before | heals after one level | goes deep |
|---|---|---|
| 0 to 2 of 10 | 70% | 10% |
| 3 to 4 | 59% | 14% |
| 5 to 6 | 55% | 18% |
| 7 to 10 | 44% | 23% |

Base rate 55% / 17%. The single largest name already being out moves it little (19% deep
against 16%). Recoveries out of full agreement down show a steeper gradient: 0 to 2 names
already recovering 14% deep, 7 to 10 names 41%.

**4. Does a theme fund crack before its sector? (themes fixed first: SMH and IGV inside XLK,
KRE inside XLF, ITB inside XLY.)** Share of days the theme fund was already out of full
agreement up:

| theme inside sector | any day the sector is in full agreement | day before a shallow sector crack | day before a deep sector crack |
|---|---|---|---|
| semiconductors in technology | 35% | 40% | 55% |
| software in technology | 33% | 43% | 64% |
| regional banks in financials | 48% | 52% | 61% |
| homebuilders in discretionary | 53% | 52% | 61% |

Looking forward, the DAY a theme first cracks carries no lift: a deep sector crack began within
ten days 13% to 18% of the time against 16% to 22% on any full-agreement day. The lift sits in
the theme having stayed out; item 7 counts that directly.

**5. Followers.** A follower is a liquid name outside the parent sector fund's ten largest whose
beta to that fund is 1.5 or higher (owner's rule). The first attempt, "highest beta among a
broad theme fund's top holdings", returned large names with beta near one (KLAC, ASML, TSM,
CRWD, NOW, ORCL, DHI, LEN): the top holdings of a broad theme fund are its heavyweights. With
the 1.5 floor and candidates pooled from narrower theme funds the rule returns the intended
kind of name: against technology NBIS, HUT, CRWV, MRVL, IREN, ENTG, LRCX, HOOD; against
financials AFRM, HOOD, SOFI, COIN, SHOP, CRCL, COF, XYZ; against discretionary W, CVNA, KSS.
No regional bank and no homebuilder passes the floor.

| against | names | down-day beta above up-day beta | median down / up beta | calm / sector-weak beta | capture on the sector's 30 worst / 30 best days |
|---|---|---|---|---|---|
| technology | 8 | 6 of 8 | 1.48 / 1.34 | 1.50 / 1.42 | 1.36 / 1.32 |
| financials | 8 | 5 of 8 | 1.54 / 1.54 | 1.30 / 1.54 | 1.27 / 1.29 |
| discretionary | 3 | 0 of 3 | 1.88 / 2.12 | 1.50 / 1.98 | 1.85 / 2.01 |

The followers amplify the sector about as much up as down. The down-day lean is concentrated in
the neocloud and miner names (NBIS 2.50 down / 1.80 up, IREN 2.23 / 1.28, HUT 1.48 / 1.03), all
with short histories. On days after the sector had lost two or more levels, the sector and the
followers averaged UP; followers did not fall by more than their calm-day beta predicts.

**6. Kill test: is the count of large names just the sector fund's own cushion? (`cushion.py`)**
The cushion is measured the day before the crack in units of the fund's own daily swing (20-day
standard deviation of daily returns): to the nearest level, and to the THIRD level, the line a
crack has to reach to count as deep.

| leaving full agreement up, 2,846 cracks since 2010 | thin cushion | middle | thick |
|---|---|---|---|
| deep rate by cushion to the nearest level (medians 0.1 / 0.6 / 1.7 daily swings) | 22% | 17% | 13% |
| deep rate by cushion to the third level (medians 3.2 / 7.1 / 13.5 daily swings) | 31% | 12% | 10% |

Inside each third-level band, the deep rate by count of large names already out (0-2 / 3-4 /
5-6 / 7-10): thin 23% / 26% / 30% / 35%; middle 8% / 12% / 12% / 12%; thick 9% / 8% / 10% / 13%.
The count and the cushion move together (correlation -0.46 with the nearest level). A model fit
on cracks before 2019 and scored on the cracks after ranks them 0.694 with the cushion alone
and 0.694 with the count added (0.50 is a coin flip; the count alone 0.589). **On breakdowns
the count is mostly arithmetic: it adds a little only when the cushion is already thin.** On
recoveries out of full agreement down (1,056 cracks) the count holds up better: 0.664 cushion
only, 0.670 with the count, 0.646 the count alone, and its weight in the joint model stays
clearly above zero when whole dates are resampled (+0.13 to +0.43).

The strongest single read in this whole look is the cushion to the third level: how tightly the
levels are stacked under price.

**7. The theme fund staying out, counted directly (`stayed_out.py`).** On days the sector is in
full agreement up, the share of days followed by a DEEP sector crack within ten trading days:

| state of the theme fund | semis / technology | software / technology | regional banks / financials | homebuilders / discretionary |
|---|---|---|---|---|
| in full agreement | 14% | 13% | 19% | 15% |
| cracked today | 13% | 14% | 18% | 18% |
| out 2 to 5 days | 13% | 22% | 24% | 16% |
| out 6 to 20 days | 26% | 29% | 36% | 26% |
| out 21 days or more | 28% | 25% | 20% | 16% |

The day the theme cracks and the first few days after carry nothing. Out for 6 to 20 days about
doubles the rate in all four pairs; beyond that it fades for banks and homebuilders. When a
sector does crack, a theme that had been out six or more days goes with 21% to 28% deep against
11% to 17% when the theme was in agreement. Technology with both themes out two or more days:
29% deep, one of two 20%, neither 9% (70 / 162 / 202 cracks). The two reads stack (cracks since
2010, four pairs pooled): neither 10% deep, large names only 17%, theme only 18%, both 26%.

Against the cushion (third-level bands, theme out six or more days against not): thin 38%
against 29%, middle 17% against 9%, thick 6% against 10%. The theme read keeps part of its lift
where the cushion is thin or middling and none where it is thick; a theme that has stayed out
goes with a thinner cushion (median 5.3 daily swings against 8.4), so part of it is the cushion
too. The days in each row come in runs (between 66 and 445 separate spells per row), so the
rows are fewer independent observations than their day counts.

## Addendum, TVB-46 (2026-11-21): the November 2026 drop and the all-in-conflict state

Same status: EXPLORATORY, count only, no prereg, no tests, no audit. The owner's question: after
the sharp fall in the indices, would this read have warned of anything in advance, and would
the trade have been a pair, the big names or the sector fund? Bars were re-fetched through
2026-11-20 into `nov_data/` (gitignored). The definitions for item 11 were written down before
that count was run.

```
uv run --no-project --with yfinance --with pandas --with numpy python analysis/sector/nov_fetch.py analysis/sector
uv run --no-project --with pandas --with numpy python analysis/sector/nov_drop.py analysis/sector
uv run --no-project --with pandas --with numpy python analysis/sector/conflict_state.py analysis/sector
```

**8. The tape (`nov_drop.py` A to C, F).** SPY's high close was 2026-10-06; at the 11-20 close
it was 11.5% below it, QQQ 19.9%. The equal-weight S&P fund held its high until 11-04 (7.1%
below at the end); small caps peaked 08-14 (15.7% below). At the SPY high only 2 of 11 sector
funds were in full agreement up. Communications had been out since 04-21, utilities since
07-27, industrials since 08-17, and none returned. The semiconductor fund was below its
half-year open through the whole run-up (68 sessions out at the SPY high). Technology cracked
on 10-08, two sessions after the high; the day before, its cushion to the third level was 6.9
daily swings (the middle band) and 2 of its 10 largest names were out. The other seven sectors
cracked between 11-02 and 11-16. Nine of the eleven last cracks have lost three or more levels.

Read the other way. A narrow tape at an index high has not been a warning: on the 2,318 days
since 1999 that SPY closed within 1% of its one-year high, a close 7% or more lower came within
40 sessions 6.2% of the time when 0 to 2 of nine sectors were in full agreement up, 9.8% with 3
to 4, 11.7% with 5 to 6 and 13.7% with 7 to 9 (10.0% over all such days). The read did not call
the top.

**9. Would acting on the cracks have paid? (`nov_drop.py` D.)** Short the sector fund at the
close of EVERY crack since 2026-06-01 and cover at the close of the day it heals (equal size,
no leverage, no fees): 99 cracks; 87 healed, costing 1.04% each on average (90.4% in total,
median two sessions, 17% of them profitable); the 12 that did not heal made 96.2%; the book
+5.8%. Technology alone: seven healed cracks cost 6.9%, the eighth made 24.7%. Six of those
seven false alarms had the semiconductor fund out 24 sessions or more, the same flag the real
crack carried. Split by what was known the day before, the only row not carried by one trade
is the thick cushion: 33 cracks, 3 deep, the book -27.4%. The "theme fund out six or more
days" row (+27.6% over 15 cracks) and the "0 to 2 large names out" row (+23.7% over 8) are the
single technology trade.

**10. Which vehicle? (`nov_drop.py` E; HINDSIGHT, each sector's last crack is by construction
the one that did not heal.)** Short from the crack-day close to the 11-20 close:

| sector, crack day | fund | ten largest names, equal weight | followers | short the fund, long SPY |
|---|---|---|---|---|
| communications 04-21 | +14.1% | +11.8% | none | +12.6% |
| utilities 07-27 | +5.9% | +5.2% | none | -0.6% |
| industrials 08-17 | +15.8% | +19.1% | none | +5.3% |
| technology 10-08 | +24.7% | +28.3% | +48.4% (8 names) | +13.8% |
| energy 11-02 | +10.0% | +9.8% | none | +1.7% |
| materials 11-05 | +7.6% | +7.5% | none | +1.7% |
| real estate 11-12 | +4.3% | +4.4% | none | -4.6% |
| discretionary 11-13 | +6.3% | +4.1% | +11.3% (3 names) | -2.3% |
| financials 11-16 | +6.2% | +7.3% | +14.5% (8 names) | -0.6% |
| staples 11-16 | +2.3% | +2.2% | none | -4.5% |
| health care 11-16 | +5.7% | +5.6% | none | -1.1% |

The largest names tracked their fund within a few points. The followers made about twice the
fund, in line with their beta; they were not priced on the false alarms. Inside technology the
spread between names was wider than the spread between vehicles: among the ten largest, INTC
+52.1%, NVDA +45.5%, MU +42.6% down to MSFT +7.1% and AAPL -0.7%; among the followers, IREN
+66.9% and NBIS +63.0% down to ENTG +23.2%. Nothing in this look selects the name. The pair
against SPY paid where the sector was the source of the weakness (technology, communications,
industrials) and gave the gain back in the November cracks, when the whole market fell.

**11. All nine long-history sectors in conflict, as a state (`conflict_state.py`).** A day on
which no sector is in full agreement up or down: 10.6% of days since 1999, 362 separate
spells, median length one session (the week's open resets on Monday). A spell of five or more
sessions happened 27 times before this one; 2026-11-20 was day five of the 28th.

| SPY after | next 20 sessions | next 40 sessions | a close 5%+ lower within 20 |
|---|---|---|---|
| every day | +0.75%, higher 64% | +1.49%, higher 67% | 18.2% |
| first day of a spell (362) | +1.16%, higher 68% | +2.19%, higher 70% | 17.1% |
| day five of a long spell (27 with a future) | +3.36%, higher 23 of 27 | +5.61%, higher 23 of 27 | 2 of 27 |

The lowest close inside the next 20 sessions was never more than 5.9% below day five. The
state is not only the pullback seen from inside: with SPY more than 10% off its high, day five
of a long spell averaged +4.46% over 20 sessions (12 cases, 10 higher) against +0.22% on other
days that far down; within 3% of the high +2.19% (7 cases) against +0.48%; between, +2.73% (8
cases) against +1.32%.

Read the other way, and why this spell only partly fits. Most of the deep-drawdown cases
entered the state from BELOW, sectors climbing out of full agreement down after a low was
already in (October and November 2001, March 2009, March and April 2020). This spell entered
from above and SPY fell 8.6% during its five sessions; the largest fall inside any earlier
long spell was 5.5% (November 2011, the closest twin: entered from above, SPY 11.7% off its
high and at a 20-day low on day five; +4.8% over 20 sessions, +11.1% over 40). Eight earlier
long spells entered from above with SPY at a 20-day low on day five: seven were higher 20
sessions later, six at 40 (the two that were not: -6.2% November 2015, -1.1% June 2007); six
of the eight were shallow pullbacks, under 5% off the high. The worst 40-session outcome
after any long spell was -7.7% (December 2002). Long spells cluster in a few years (2001-02,
2011, 2013, 2020), so 27 is fewer independent events than it reads.

Without the week level (month, quarter, half-year, year) the state is rarer: 3.3% of days, 93
spells, 14 of five sessions or more; SPY after a spell start +1.87% over 20 sessions. On
2026-11-20 the market was NOT in that state: staples was still above its month, quarter,
half-year and year opens and below only the week. The count of sectors in full agreement whips
within a week (5, 1, 5) for the same reason: on Monday the week's level is the day.

## Read both ways

- A path worth naming (addendum): a persisting all-in-conflict state has been followed by a
  stronger SPY than an ordinary day, inside every distance-off-the-high band. A kill test for
  it: the favourable cases were mostly recoveries entered from below; the November 2026 spell
  entered from above at a speed outside the sample.
- A kill test that landed (addendum): a narrow tape at an index high was not followed by more
  drops than a broad one; and shorting every crack was flat (many small losses, a few large
  gains), with nothing here telling the real crack from the false ones in advance.
- A path worth naming: how tightly the levels are stacked under price (the cushion to the third
  level) separates shallow from deep cracks better than anything else here, and it is known
  before the crack.
- A path worth naming: a theme fund that has been out for one to four weeks about doubles the
  odds of a deep sector crack, in all four pairs, and keeps part of that inside thin and
  middling cushions.
- A kill test that landed: on breakdowns the count of large names already out is mostly the
  cushion seen from the inside. It does not improve the ranking of cracks it has not seen.
- A kill test worth naming: on daily closes the follower adds size, not information. Weakness
  did not carry into the next day on average.
- Not settled either way: the trade the owner describes happens inside the day, during the
  crack. Daily closes cannot see it.

## Limitations

- Hindsight lists: today's ten largest holdings and today's high-beta names. A name that passes
  the beta floor is by construction one that has recently been volatile.
- Clustered dates: sectors crack together, so the cracks are far fewer independent events than
  the counts suggest. No intervals are given for that reason.
- Survivors only (current funds, current holdings); the newest theme funds have under a year of
  history and are for live watching, not for testing.
- Daily closes only; a level is tested at the close, so an intraday break that is reclaimed by
  the close is invisible.
- Equity funds in regular hours. Nothing here has been run on perps or on a 24/7 clock.
- `followers.json` and `holdings.json` are the selection receipts for the lists used.
