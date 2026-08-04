# TVB-15 paper-trading week 1 -- twin scoreboard

Week window: 2026-07-20 00:00 -> 2026-07-27 00:00 UTC (v6 defaults frozen; no mid-week tuning)
Roster frozen: 2026-07-20T14:31:21+00:00 | rule: {'universe': 'xyz', 'min_vol_usd': 5000000.0, 'min_oi_usd': 3000000.0, 'tail_size': 5}

Fill conventions (a-priori): entry at trigger; BF exit at the line value;
break/flip exits at the 5m close. 1x, gross, no fees/funding. The twin
records CLOSED 5m bars only and starts FLAT at the week boundary.

| symbol | tail | data through | trades | bf | brk | flip | wins | sum pnl% | med pnl% | avg MFE% | avg gb pp | open |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| xyz:MRVL | long | 07-27 00:00 | 1 | 0 | 1 | 0 | 0 | -14.32 | -14.32 | 1.31 | 15.63 | -- |
| xyz:GOOGL | long | 07-27 00:00 | 6 | 4 | 0 | 2 | 4 | 5.15 | 0.84 | 2.15 | 1.29 | short @321.5 since 07-23 13:30 |
| xyz:AMZN | long | 07-27 00:00 | 5 | 3 | 2 | 0 | 3 | 0.55 | 0.07 | 0.93 | 0.82 | short @235.3 since 07-23 14:00 |
| xyz:MSFT | long | 07-27 00:00 | 1 | 0 | 1 | 0 | 0 | -3.18 | -3.18 | 1.57 | 4.75 | -- |
| xyz:GOLD | long | 07-27 00:00 | 7 | 6 | 0 | 1 | 6 | 3.44 | 0.65 | 0.63 | 0.13 | long @4158 since 07-22 14:05 |
| xyz:AAPL | short | 07-27 00:00 | 1 | 0 | 1 | 0 | 0 | -1.06 | -1.06 | 0.09 | 1.15 | -- |
| xyz:SKHX | short | 07-27 00:00 | 0 | 0 | 0 | 0 | 0 | -- | -- | -- | -- | short @1169 since 07-24 18:30 |
| xyz:SKHY | short | 07-27 00:00 | 7 | 3 | 1 | 3 | 3 | -10.36 | -1.19 | 2.90 | 4.38 | long @161.1 since 07-26 03:30 |
| xyz:NBIS | short | 07-27 00:00 | 1 | 0 | 1 | 0 | 0 | -26.82 | -26.82 | 1.28 | 28.10 | -- |
| xyz:TSLA | short | 07-27 00:00 | 8 | 8 | 0 | 0 | 8 | 18.99 | 1.80 | 2.77 | 0.39 | short @322.9 since 07-23 14:50 |
| xyz:DRAM | parity | 07-27 00:00 | 0 | 0 | 0 | 0 | 0 | -- | -- | -- | -- | short @52.56 since 07-20 02:25 |

## By exit class (closed trades, all symbols)

| exit class | n | win rate | avg pnl% | med pnl% | avg give-back pp |
|---|---|---|---|---|---|
| BF S/L Exit (harvest touch) | 24 | 100% | 1.86 | 0.98 | 0.24 |
| BF Break L/S Exit (adverse close-through) | 7 | 0% | -8.15 | -3.18 | 9.19 |
| Flip S/L Exit (full-gate backstop) | 6 | 0% | -2.54 | -1.87 | 4.38 |

Notes: the scanner score SELECTED the roster; the twin's D/W/M gate decides
entries -- different TFC measurements, so zero-entry symbols are the gate
doing its job, not a defect. xyz:DRAM is the parity instrument (live v6
front chart), not rule-selected. Divergences user-vs-twin get numbered
TVB15-D1.. in the protocol doc.
