# Sector continuity breadth: first look -- RECEIPT (TVB-46, 2026-11-19)

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
```

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
the theme having stayed out. The printed shares imply roughly 19% to 25% when the theme is out
against 13% to 19% when it is in; that split was worked out from the shares, not counted
directly.

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

## Read both ways

- A path worth naming: the count of large names already out, and a theme fund that has stayed
  out, both raise the odds that a sector crack goes deep. The lift is modest.
- A kill test worth naming: a sector fund is the weighted sum of its members, so part of the
  by-count gradient is arithmetic (how close the fund already sits to its own level), not
  foresight. Whether the count adds anything beyond the fund's own cushion is NOT yet checked.
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
