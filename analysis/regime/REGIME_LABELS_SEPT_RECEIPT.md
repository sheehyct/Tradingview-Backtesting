# Two no-human regime labels on the September book -- characterization (TVB-36, 2026-10-03)

Question from the owner: can something other than the owner be the regime input? Two labels were
computed at the entry instant of every trade in the September strategy-chosen book (116 lost
signals replayed bracket-only + 24 filled trades; `analysis/parallax/RECEIPT.md`). Both labels use
only instruments the bot already receives on its own feed, so both are defined 24/7. Definitions
were fixed in each script's docstring before any number was read.

R = multiples of the planned stop distance. "Random exp" = the wins a driftless random walk would
produce inside the same brackets. One month, about 140 trades: a sighting, not a validation.

## 1. Venue-native "Tightening" (`venue_mrc.py`)

The Tightening sub-score of the owner's Macro Risk Conditions indicator
(`tv_indicators/pine/macro_risk_conditions_v1_2.pine`, script v2.0), same math and defaults
(15m calc bars, change over 4 or 8 bars, z over 100 bars capped at 3, EMA 3, hot/cold at +-30),
with venue perps substituted for the TradingView feeds: rates = xyz:TLT inverted, dollar = a
DXY-weighted basket of xyz:EUR / xyz:JPY / xyz:GBP, oil = xyz:CL. The Fear half has no venue
substitute (no VIX, VIX3M or credit perp) and is not computed.

Availability: defined at 140 of 140 entries. The five perps printed a 15m bar in every interval,
weekends included. xyz:TLT's 15m history begins about 09-18; before that the score ran on dollar
and oil. (The TVB-35 TradingView-fed label existed for 32 of 84 trades.)

| Change horizon | Share of all 15m bars: quiet / hot / cold | Entries in quiet |
|---|---|---|
| 4 bars (1 h, code default) | 87.8% / 5.5% / 6.6% | 117 of 140 |
| 8 bars (2 h, header's working value) | 82.4% / 9.2% / 8.4% | 107 of 140 |

| Alignment (hot = headwind for longs) | n (1 h) | R/trade (1 h) | n (2 h) | R/trade (2 h) |
|---|---|---|---|---|
| with | 10 | -0.49 | 16 | -0.32 |
| quiet | 117 | -0.32 | 107 | -0.31 |
| against | 10 | -0.30 | 14 | -0.49 |
| unmapped (energy names) | 3 | -0.86 | 3 | -0.86 |

Reading: no separation. An IMPULSE label is quiet for 82-88% of the tape by construction, so it
cannot act as a standing filter for a book that enters all day; it is an event flag. In the 12-18%
of time it is hot or cold the sample is 20-30 trades and the sign flips between the two horizons.
The indicator's LEVEL layer (10-year at a multi-decade high, and so on) is a slow state that did
not vary inside the month, so one month cannot test it at all.

## 2. Index continuity (`index_continuity.py`)

The charter's slow layer (S3.3): price of a reference against its own day, week and month open
(strat-methodology 4.1). Reference = BTC for crypto, xyz:XYZ100 for equity perps; commodity, FX
and energy names unmapped. DWM = all three agree; WM = week and month only (the BTC drift veto
already enforces the day on crypto).

Reference regime at entry (DWM): up 40, down 22, MIXED 73 of 135 mapped trades.

| DWM alignment | n | resolved | wins | random exp | z | sum R | R/trade |
|---|---|---|---|---|---|---|---|
| with | 36 | 31 | 8 | 12.5 | -1.65 | -11.2 | -0.31 |
| mixed | 73 | 66 | 17 | 26.5 | -2.41 | -28.0 | -0.38 |
| against | 26 | 18 | 6 | 7.1 | -0.54 | -3.9 | -0.15 |

| Reference x trade (DWM) | n | wins / resolved | random exp | R/trade |
|---|---|---|---|---|
| index up, long | 25 | 8 / 23 | 9.3 | -0.19 |
| index up, short | 15 | 3 / 8 | 3.3 | -0.07 |
| index mixed, long | 33 | 8 / 29 | 11.5 | -0.34 |
| index mixed, short | 40 | 9 / 37 | 15.0 | -0.42 |
| index down, long | 11 | 3 / 10 | 3.8 | -0.26 |
| index down, short | 11 | 0 / 8 | 3.2 | -0.60 |

Crypto only: with -0.18 R/trade (n 25), mixed -0.41 (n 60), against -0.53 (n 6). The WM variant
reads the same way (with -0.31, mixed -0.36, against -0.24 pooled).

Reading: more than half the entries were taken while the index itself had no continuity, and that
cell holds 28 of the 43 R lost. Standing aside on a mixed index would have cut the trade count from
135 to 62 and the loss from about 43 R to about 15 R: damage containment, the same verdict as
TVB-4 and TVB-5, not an edge. The best large cell (longs with the index up on all three) sits at
about random. Shorts taken WITH a falling index went 0 for 8. 56 of the 135 entries fell on a
Monday or the 1st, when the timeframes share an open and are one observation (skill 4.5).

## 3. Verdict

Neither label turns the September book positive. A regime filter on top of this entry logic
reduces how much it loses; it does not make it win. That extends the 2026-10-02 call: the missing
piece is not a regime gate on the same entries.

## Appendix: the owner's indicator inputs that exist as 24/7 venue perps

| Indicator input | Venue perp (mark 2026-10-02) | Note |
|---|---|---|
| US 10Y / 2Y yield | xyz:TLT (77.5) | long-bond ETF: price falls when yields rise; no 2-year |
| DXY | xyz:EUR (1.125), xyz:JPY (157.8), xyz:GBP (1.325) | xyz:JPY is quoted as USD/JPY, yen per dollar |
| Crude | xyz:CL (91.3), xyz:BRENTOIL (102.6) | |
| VIX, VIX/VIX3M, HYG/IEI | none | the Fear half cannot be rebuilt on-venue |
| NQ / ES / Nikkei futures | xyz:XYZ100, xyz:SP500, xyz:JP225 | |
| ZN (10-year note price) | xyz:TLT | longer duration: the yen monitor's 0.06% threshold would need restating |
| SMH, SK Hynix, Samsung, Kioxia | xyz:SMH, xyz:SKHX, xyz:SMSN, xyz:KIOXIA | |
| Memory complex legs + benchmark + index | xyz:MU, SNDK, WDC, SKHX, SMSN, DRAM, XYZ100, SP500 | every leg of the composite is already a venue perp |

Weekend caveat: Fri 20:00 -> Sun 20:00 New York is the internal-oracle window; an xyz perp's price
there is the perp crowd's, not an external market's.

## Files

`venue_mrc.py` / `venue_mrc.json`, `index_continuity.py` / `index_continuity.json`. Candle caches
under `data/` are gitignored and refetch from the public API.
