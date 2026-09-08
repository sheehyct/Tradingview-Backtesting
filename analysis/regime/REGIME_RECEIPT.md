# Macro-regime receipt (TVB-35) -- characterization only

Every closed trade of the three live ledgers labeled with the macro reference
set at ENTRY time; every decision row labeled at its hour. Labels were fixed
a-priori in `receipt.py`'s docstring before any number was read. 84-ish trades:
this shows the labels are computable and maps the ceiling; it validates nothing.
Price is the last 60m close at or before the instant; each reference keeps its own
session clock (daily open hour UTC below).

| ref | 60m bars | first | last | daily bar opens (UTC) |
|---|---|---|---|---|
| DXY | 300 | 08-21 08:00 | 09-08 22:00 | 23:00 |
| US10Y | 300 | 08-19 08:00 | 09-08 21:00 | 23:00 |
| CL1 | 300 | 08-20 20:00 | 09-08 23:00 | 22:00 |
| BRN1 | 300 | 08-20 10:00 | 09-08 21:00 | 00:00 |
| SPX | 300 | 07-09 14:30 | 09-08 19:30 | 13:30 |
| BTCUSD | 300 | 08-27 12:00 | 09-08 23:00 | 00:00 |

**Now (2026-09-08T23:33Z):** dollar daily down / weekly down; 10-year daily closed / weekly closed; WTI daily up; Brent daily closed; S&P daily closed; BTC daily down; macro_dir mixed (weekly mixed); whipsaw False.

## Pooled (all three ledgers)

**By alignment with the DAILY dollar+10-year label (with = long in tailwind / short in headwind)**

| label | n | wins | sum pnl% | median pnl% | sum $ |
|---|---|---|---|---|---|
| against | 7 | 1 | -4.4 | -1.106 | -1.34 |
| mixed | 59 | 18 | -21.9 | -0.635 | -7.52 |
| with | 18 | 7 | 4.25 | -0.157 | 1.05 |

**By alignment with the WEEKLY label**

| label | n | wins | sum pnl% | median pnl% | sum $ |
|---|---|---|---|---|---|
| against | 5 | 1 | -1.98 | -0.379 | -0.59 |
| mixed | 71 | 22 | -22.57 | -0.483 | -7.32 |
| with | 8 | 3 | 2.5 | -0.26 | 0.1 |

**By whipsaw (S&P or BTC running outside day at entry)**

| label | n | wins | sum pnl% | median pnl% | sum $ |
|---|---|---|---|---|---|
| False | 82 | 25 | -21.44 | -0.474 | -7.78 |
| True | 2 | 1 | -0.61 | -0.303 | -0.03 |

**By trade direction x daily macro label**

| label | n | wins | sum pnl% | median pnl% | sum $ |
|---|---|---|---|---|---|
| down|headwind | 12 | 6 | 6.59 | -0.129 | 1.61 |
| down|mixed | 26 | 5 | -16.24 | -0.97 | -7.66 |
| down|tailwind | 4 | 1 | -2.82 | -1.45 | -0.88 |
| up|headwind | 3 | 0 | -1.57 | -0.321 | -0.46 |
| up|mixed | 33 | 13 | -5.66 | -0.379 | 0.14 |
| up|tailwind | 6 | 1 | -2.34 | -0.157 | -0.56 |

## weekend1 (2026-08-22T14:26Z .. 2026-08-24T21:58Z)

Closed trades 34; decision rows 11909 (macro label unavailable on 6693); rows by macro_dir {'mixed': 10639, 'tailwind': 1270}; rows by whipsaw {'False': 11909}; entries by macro_dir {'mixed': 29, 'tailwind': 5}; entries by alignment {'mixed': 29, 'with': 2, 'against': 3}.

**Trades by alignment (daily)**

| label | n | wins | sum pnl% | median pnl% | sum $ |
|---|---|---|---|---|---|
| against | 3 | 1 | -1.46 | -1.533 | -0.43 |
| mixed | 29 | 8 | -16.28 | -0.976 | -3.97 |
| with | 2 | 0 | -2.5 | -1.249 | -0.75 |

**Trades by whipsaw**

| label | n | wins | sum pnl% | median pnl% | sum $ |
|---|---|---|---|---|---|
| False | 34 | 9 | -20.23 | -1.08 | -5.15 |

## round2 (2026-08-31T15:37Z .. 2026-09-04T17:13Z)

Closed trades 32; decision rows 22401 (macro label unavailable on 0); rows by macro_dir {'mixed': 8798, 'tailwind': 4524, 'headwind': 9079}; rows by whipsaw {'False': 22401}; entries by macro_dir {'mixed': 12, 'headwind': 15, 'tailwind': 5}; entries by alignment {'mixed': 12, 'with': 16, 'against': 4}.

**Trades by alignment (daily)**

| label | n | wins | sum pnl% | median pnl% | sum $ |
|---|---|---|---|---|---|
| against | 4 | 0 | -2.94 | -0.713 | -0.91 |
| mixed | 12 | 4 | 4.3 | -0.082 | 0.37 |
| with | 16 | 7 | 6.75 | -0.157 | 1.8 |

**Trades by whipsaw**

| label | n | wins | sum pnl% | median pnl% | sum $ |
|---|---|---|---|---|---|
| False | 32 | 11 | 8.11 | -0.205 | 1.26 |

## round3 (2026-09-06T19:52Z .. 2026-09-07T19:00Z)

Closed trades 18; decision rows 5343 (macro label unavailable on 5343); rows by macro_dir {'mixed': 5343}; rows by whipsaw {'False': 5102, 'True': 241}; entries by macro_dir {'mixed': 18}; entries by alignment {'mixed': 18}.

**Trades by alignment (daily)**

| label | n | wins | sum pnl% | median pnl% | sum $ |
|---|---|---|---|---|---|
| mixed | 18 | 6 | -9.93 | -0.519 | -3.92 |

**Trades by whipsaw**

| label | n | wins | sum pnl% | median pnl% | sum $ |
|---|---|---|---|---|---|
| False | 16 | 5 | -9.32 | -0.741 | -3.89 |
| True | 2 | 1 | -0.61 | -0.303 | -0.03 |

## Reading rules

- A cell with fewer than ~10 trades is a question, not a reading.
- `mixed` is the honest default: one of the two references disagreed or was closed.
- The whipsaw flag is a running check: a day can become an outside day AFTER the entry.
- Nothing here is a gate. A live label would be shadow-journaled first (the BTC drift
  veto is the template) and receipted again on the next tape.
