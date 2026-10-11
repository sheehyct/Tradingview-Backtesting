# Macro-regime receipt (TVB-35) -- characterization only

Amended 2026-10-11 (TVB-38, Codex TVB-35 audit F6/F7): labels now use only bars completed at entry; whipsaw states are true/false/unknown. Numbers below regenerated.

Every closed trade of the three live ledgers labeled with the macro reference
set as it was KNOWN at entry time; every decision row labeled at its own instant.
Labels were fixed a-priori in `receipt.py`'s docstring before any number was read.
84 trades: this shows the labels are computable and maps the
ceiling; it validates nothing. Known-at-entry holds by construction: a 60m bar counts
only from its close (open + 60 minutes); price now is the latest COMPLETED 60m close;
the running day uses only completed 60m bars; a reference whose latest completed
60m bar closed more than 2 hours earlier is closed at that instant, and a day or week
whose first 60m bar has not started yet has no known open. Each reference keeps its
own session clock (daily open hour UTC below).

| ref | 60m bars | first | last | daily bar opens (UTC) |
|---|---|---|---|---|
| DXY | 300 | 08-21 08:00 | 09-08 22:00 | 23:00 |
| US10Y | 300 | 08-19 08:00 | 09-08 21:00 | 23:00 |
| CL1 | 300 | 08-20 20:00 | 09-08 23:00 | 22:00 |
| BRN1 | 300 | 08-20 10:00 | 09-08 21:00 | 00:00 |
| SPX | 300 | 07-09 14:30 | 09-08 19:30 | 13:30 |
| BTCUSD | 300 | 08-27 12:00 | 09-08 23:00 | 00:00 |

**At harvest (2026-09-08T23:30Z):** dollar daily down / weekly down; 10-year daily flat / weekly flat; WTI daily down; Brent daily up; S&P daily closed; BTC daily down; macro_dir mixed (weekly mixed); whipsaw unknown.

**Coverage first.** Both the dollar and the 10-year daily dots were live at entry on 36 of 84 trades; of those, 17 had a directional label (13 with, 4 against) and 19 disagreed or were flat. The whipsaw flag was true on 0, false on 10, and unknown on 74. Unknown means a reference was missing or closed and is never counted as false, so this coverage supports no reading about the flag's effect.

## Pooled (all three ledgers)

**Inputs available at entry (trades whose input was live, of n)**

| ledger | n | dollar d | 10-yr d | dollar AND 10-yr d | WTI d | Brent d | S&P d | BTC d | dollar w | 10-yr w | S&P running day | BTC running day |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| weekend1 | 34 | 12 | 9 | 9 | 12 | 12 | 3 | 0 | 12 | 9 | 3 | 0 |
| round2 | 32 | 32 | 27 | 27 | 32 | 28 | 10 | 32 | 32 | 28 | 10 | 28 |
| round3 | 18 | 14 | 0 | 0 | 14 | 14 | 0 | 18 | 14 | 0 | 0 | 14 |
| pooled | 84 | 58 | 36 | 36 | 58 | 54 | 13 | 50 | 58 | 37 | 13 | 42 |

**Daily macro label state at entry, and whipsaw true / false / unknown**

| ledger | n | unavailable | available but mixed | directional | of which with | of which against | whipsaw true | whipsaw false | whipsaw unknown |
|---|---|---|---|---|---|---|---|---|---|
| weekend1 | 34 | 25 | 6 | 3 | 2 | 1 | 0 | 0 | 34 |
| round2 | 32 | 5 | 13 | 14 | 11 | 3 | 0 | 10 | 22 |
| round3 | 18 | 18 | 0 | 0 | 0 | 0 | 0 | 0 | 18 |
| pooled | 84 | 48 | 19 | 17 | 13 | 4 | 0 | 10 | 74 |

**By alignment with the DAILY dollar+10-year label (with = long in tailwind / short in headwind)**

| label | n | wins | sum pnl% | median pnl% | sum $ |
|---|---|---|---|---|---|
| against | 4 | 0 | -4.33 | -1.237 | -1.33 |
| mixed | 67 | 21 | -11.35 | -0.483 | -5.39 |
| with | 13 | 5 | -6.37 | -0.267 | -1.1 |

**By daily label state (unavailable / available but mixed / directional)**

| label | n | wins | sum pnl% | median pnl% | sum $ |
|---|---|---|---|---|---|
| directional | 17 | 5 | -10.7 | -0.321 | -2.42 |
| mixed_available | 19 | 6 | 6.49 | -0.379 | 0.01 |
| unavailable | 48 | 15 | -17.84 | -0.559 | -5.4 |

**By alignment with the WEEKLY label**

| label | n | wins | sum pnl% | median pnl% | sum $ |
|---|---|---|---|---|---|
| against | 3 | 0 | -2.06 | -0.379 | -0.62 |
| mixed | 75 | 23 | -19.76 | -0.483 | -6.69 |
| with | 6 | 3 | -0.23 | -0.651 | -0.51 |

**By whipsaw (S&P or BTC running outside day at entry; unknown kept apart)**

| label | n | wins | sum pnl% | median pnl% | sum $ |
|---|---|---|---|---|---|
| false | 10 | 4 | -0.58 | -0.072 | -0.47 |
| unknown | 74 | 22 | -21.47 | -0.555 | -7.35 |

**By trade direction x daily macro label**

| label | n | wins | sum pnl% | median pnl% | sum $ |
|---|---|---|---|---|---|
| down|headwind | 7 | 4 | -1.68 | 0.041 | 0.56 |
| down|mixed | 33 | 8 | -7.9 | -0.717 | -6.59 |
| down|tailwind | 2 | 0 | -2.9 | -1.45 | -0.9 |
| up|headwind | 2 | 0 | -1.43 | -0.713 | -0.42 |
| up|mixed | 34 | 13 | -3.45 | -0.216 | 1.2 |
| up|tailwind | 6 | 1 | -4.69 | -0.554 | -1.66 |

## weekend1 (2026-08-22T14:26Z .. 2026-08-24T21:58Z)

Closed trades 34; decision rows 11909 (dollar or 10-year daily dot unavailable on 7126); rows by label state {'unavailable': 7126, 'directional': 1041, 'mixed_available': 3742}; rows by macro_dir {'mixed': 10868, 'tailwind': 1041}; rows by whipsaw {'unknown': 11909}; entries by macro_dir {'mixed': 31, 'tailwind': 3}; entries by alignment {'mixed': 31, 'against': 1, 'with': 2}.

**Trades by alignment (daily)**

| label | n | wins | sum pnl% | median pnl% | sum $ |
|---|---|---|---|---|---|
| against | 1 | 0 | -1.53 | -1.533 | -0.45 |
| mixed | 31 | 8 | -16.26 | -0.976 | -3.96 |
| with | 2 | 1 | -2.44 | -1.22 | -0.73 |

**Trades by whipsaw**

| label | n | wins | sum pnl% | median pnl% | sum $ |
|---|---|---|---|---|---|
| unknown | 34 | 9 | -20.23 | -1.08 | -5.15 |

## round2 (2026-08-31T15:37Z .. 2026-09-04T17:13Z)

Closed trades 32; decision rows 22401 (dollar or 10-year daily dot unavailable on 2414); rows by label state {'mixed_available': 8043, 'unavailable': 2414, 'directional': 11944}; rows by macro_dir {'mixed': 10457, 'headwind': 8037, 'tailwind': 3907}; rows by whipsaw {'false': 6890, 'unknown': 15511}; entries by macro_dir {'mixed': 18, 'headwind': 9, 'tailwind': 5}; entries by alignment {'mixed': 18, 'against': 3, 'with': 11}.

**Trades by alignment (daily)**

| label | n | wins | sum pnl% | median pnl% | sum $ |
|---|---|---|---|---|---|
| against | 3 | 0 | -2.79 | -1.106 | -0.87 |
| mixed | 18 | 7 | 14.84 | -0.082 | 2.49 |
| with | 11 | 4 | -3.93 | -0.267 | -0.36 |

**Trades by whipsaw**

| label | n | wins | sum pnl% | median pnl% | sum $ |
|---|---|---|---|---|---|
| false | 10 | 4 | -0.58 | -0.072 | -0.47 |
| unknown | 22 | 7 | 8.69 | -0.31 | 1.72 |

## round3 (2026-09-06T19:52Z .. 2026-09-07T19:00Z)

Closed trades 18; decision rows 5343 (dollar or 10-year daily dot unavailable on 5343); rows by label state {'unavailable': 5343}; rows by macro_dir {'mixed': 5343}; rows by whipsaw {'unknown': 5343}; entries by macro_dir {'mixed': 18}; entries by alignment {'mixed': 18}.

**Trades by alignment (daily)**

| label | n | wins | sum pnl% | median pnl% | sum $ |
|---|---|---|---|---|---|
| mixed | 18 | 6 | -9.93 | -0.519 | -3.92 |

**Trades by whipsaw**

| label | n | wins | sum pnl% | median pnl% | sum $ |
|---|---|---|---|---|---|
| unknown | 18 | 6 | -9.93 | -0.519 | -3.92 |

## Reading rules

- A cell with fewer than ~10 trades is a question, not a reading.
- `mixed` in the alignment tables pools two different things: an input that was
  unavailable (closed or no history) and two live inputs that disagreed or were flat.
  The label-state table keeps them apart; read coverage before any alignment cell.
- The whipsaw flag is a running check: a day can become an outside day AFTER the entry.
  `unknown` means a reference's running day was not computable at entry (no history,
  reference closed, or no completed hour yet in its day). It is never folded into false.
- Nothing here is a gate. A live label would be shadow-journaled first (the BTC drift
  veto is the template) and receipted again on the next tape.
