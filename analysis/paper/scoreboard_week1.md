# TVB-15 paper-trading week 1 -- twin scoreboard

Week window: 2026-07-20 00:00 -> 2026-07-27 00:00 UTC (v6 defaults frozen; no mid-week tuning)
Roster frozen: 2026-07-20T14:31:21+00:00 | rule: {'universe': 'xyz', 'min_vol_usd': 5000000.0, 'min_oi_usd': 3000000.0, 'tail_size': 5}

Fill conventions (a-priori): entry at trigger; BF exit at the line value;
break/flip exits at the 5m close. 1x, gross, no fees/funding. The twin
records CLOSED 5m bars only and starts FLAT at the week boundary.

| symbol | tail | data through | trades | bf | brk | flip | wins | sum pnl% | med pnl% | avg MFE% | avg gb pp | open |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| xyz:MRVL | long | 07-22 02:05 | 0 | 0 | 0 | 0 | 0 | -- | -- | -- | -- | short @189.6 since 07-20 00:50 |
| xyz:GOOGL | long | 07-22 02:05 | 2 | 0 | 0 | 2 | 0 | -3.27 | -1.63 | 1.40 | 3.03 | short @348.9 since 07-21 14:35 |
| xyz:AMZN | long | 07-22 02:05 | 1 | 0 | 1 | 0 | 0 | -0.45 | -0.45 | 2.10 | 2.55 | -- |
| xyz:MSFT | long | 07-22 02:05 | 0 | 0 | 0 | 0 | 0 | -- | -- | -- | -- | long @397 since 07-20 15:15 |
| xyz:GOLD | long | 07-22 02:05 | 5 | 4 | 0 | 1 | 4 | 2.52 | 0.67 | 0.66 | 0.15 | long @4123 since 07-22 01:40 |
| xyz:AAPL | short | 07-22 02:05 | 1 | 0 | 1 | 0 | 0 | -1.06 | -1.06 | 0.09 | 1.15 | -- |
| xyz:SKHX | short | 07-22 02:05 | 0 | 0 | 0 | 0 | 0 | -- | -- | -- | -- | -- |
| xyz:SKHY | short | 07-22 02:05 | 4 | 2 | 0 | 2 | 2 | 3.51 | -0.27 | 4.47 | 3.59 | long @175.2 since 07-22 00:20 |
| xyz:NBIS | short | 07-22 02:05 | 0 | 0 | 0 | 0 | 0 | -- | -- | -- | -- | short @179.8 since 07-20 01:00 |
| xyz:TSLA | short | 07-22 02:05 | 2 | 2 | 0 | 0 | 2 | 1.34 | 0.67 | 1.07 | 0.40 | short @375.6 since 07-20 14:00 |
| xyz:DRAM | parity | 07-22 02:10 | 0 | 0 | 0 | 0 | 0 | -- | -- | -- | -- | short @52.56 since 07-20 02:25 |

## By exit class (closed trades, all symbols)

| exit class | n | win rate | avg pnl% | med pnl% | avg give-back pp |
|---|---|---|---|---|---|
| BF S/L Exit (harvest touch) | 8 | 100% | 1.82 | 0.69 | 0.14 |
| BF Break L/S Exit (adverse close-through) | 2 | 0% | -0.75 | -0.75 | 1.85 |
| Flip S/L Exit (full-gate backstop) | 5 | 0% | -2.10 | -1.19 | 4.18 |

Notes: the scanner score SELECTED the roster; the twin's D/W/M gate decides
entries -- different TFC measurements, so zero-entry symbols are the gate
doing its job, not a defect. xyz:DRAM is the parity instrument (live v6
front chart), not rule-selected. Divergences user-vs-twin get numbered
TVB15-D1.. in the protocol doc.
