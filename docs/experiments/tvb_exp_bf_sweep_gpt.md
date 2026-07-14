# TFC and Broadening Formation Parameter Exploration

Date: 2026-07-11

Status: exploratory research only. No configuration is ready for deployment.

## Bottom line

The best 5-minute configuration was the strict full6 TFC gate with flip exits, 15-minute arming, 15-minute exit checks, both directions, and BF disabled. It was positive on 9 of 10 symbols in the broad screen, with median total return +8.34%, median PF 1.55, and median max drawdown 11.26%. The failure was the very young HIP3XYZ:SPCXUSDC.P contract at -24.73% with 34.52% drawdown.

That result does not survive the stronger regime checks. On 15-minute charts the same no-BF configuration was positive on only 6 of 10, with median PF 1.08 and median drawdown 24.27%. On 30-minute equity proxies from January 2024 onward it was positive on only 2 of 4, with median return -4.76%, median PF 0.96, and median drawdown 29.93%. The 5-minute edge is therefore regime-sensitive and heavily influenced by MU's exceptional bullish path.

The BF overlay did not earn a core role. BF60, strength 10, recycle improved the 5-minute representative median from +8.34% to +9.05%, but reduced median PF, increased trades and drawdown, and produced worse long-window losses. It is an optional research branch, not a validated improvement.

## Scope

- 448 accepted structured runs collected 2026-07-12T02:20:08.483Z through 2026-07-12T03:15:17.815Z.
- 420 five-minute parameter runs, 20 fifteen-minute extension runs, and 8 thirty-minute equity stress runs.
- Six HIP-3 tickers: HIP3XYZ:AMZNUSDC.P, HIP3XYZ:MUUSDC.P, HIP3XYZ:XYZ100USDC.P, HIP3XYZ:SP500USDC.P, HIP3XYZ:CLUSDC.P, and HIP3XYZ:SPCXUSDC.P.
- Four longer-calendar proxies: NASDAQ:AMZN, NASDAQ:MU, NASDAQ:QQQ, and AMEX:SPY.
- Timing, BF, and risk grids used six direct representatives: HIP-3 AMZN, MU, SP500 plus NASDAQ AMZN, MU, and AMEX SPY.
- The 15-minute comparison used all 10 tickers. The 30-minute check used the four equity proxies.
- The two canary runs used to validate the collector are excluded from every result and count in this report.

## Backtest model

- Initial capital: $10,000.
- Position size: 100% of current equity, one position, no pyramiding.
- Commission: 0.0125% per strategy fill; slippage: one instrument tick.
- Margin fields: zero. Funding, liquidation, borrow, venue basis, and instrument-specific liquidity are not modeled.
- TradingView bar magnifier and calc-on-every-tick are enabled, but historical execution is still a bar-based simulation.
- Total % means closed net profit plus the current open P/L, divided by initial capital. Closed %, PF, and trade count are closed-trade statistics. Open d% is Total % minus Closed %.
- Entry anchors are the prior completed arming bar high plus one tick for longs and low minus one tick for shorts.
- Full6 continuity requires price above or below the current 60, 120, 240, daily, weekly, and monthly opens. Other gate sets are listed below.
- Flip exits close only when the full gate aligns in the opposite direction. State exits close when the current directional gate is no longer true.
- BF exits are same-side projected-line limit exits. Higher-timeframe BF pivots use completed values. Recycle permits the normal next setup; ratchet requires a new same-direction extreme after a BF exit.
- The loss governor advances after a gross losing trade. The W+D stand-aside layer is explicit but logically redundant when full6 already includes D and W.

## History actually loaded

These are chart-loaded windows, not claimed exchange inception dates. The final bar moved slightly during the live run; each detailed row preserves its own exact dates.

| TF | Ticker | Bars (typical) | Earliest loaded | Latest loaded |
|---:|---|---:|---|---|
| 5m | AMEX:SPY | 20153 | 2026-02-09 | 2026-07-10 |
| 5m | HIP3XYZ:AMZNUSDC.P | 21873 | 2026-04-20 | 2026-07-12 |
| 5m | HIP3XYZ:CLUSDC.P | 21894 | 2026-04-27 | 2026-07-12 |
| 5m | HIP3XYZ:MUUSDC.P | 21861 | 2026-04-27 | 2026-07-12 |
| 5m | HIP3XYZ:SP500USDC.P | 21915 | 2026-04-27 | 2026-07-12 |
| 5m | HIP3XYZ:SPCXUSDC.P | 15884 | 2026-05-17 | 2026-07-12 |
| 5m | HIP3XYZ:XYZ100USDC.P | 21905 | 2026-04-27 | 2026-07-12 |
| 5m | NASDAQ:AMZN | 20711 | 2026-02-02 | 2026-07-10 |
| 5m | NASDAQ:MU | 20136 | 2026-02-09 | 2026-07-10 |
| 5m | NASDAQ:QQQ | 20159 | 2026-02-09 | 2026-07-10 |
| 15m | AMEX:SPY | 20444 | 2025-04-01 | 2026-07-10 |
| 15m | HIP3XYZ:AMZNUSDC.P | 20523 | 2025-12-01 | 2026-07-12 |
| 15m | HIP3XYZ:CLUSDC.P | 17210 | 2026-01-06 | 2026-07-12 |
| 15m | HIP3XYZ:MUUSDC.P | 17655 | 2025-12-19 | 2026-07-12 |
| 15m | HIP3XYZ:SP500USDC.P | 11094 | 2026-03-18 | 2026-07-12 |
| 15m | HIP3XYZ:SPCXUSDC.P | 5299 | 2026-05-17 | 2026-07-12 |
| 15m | HIP3XYZ:XYZ100USDC.P | 21421 | 2025-12-01 | 2026-07-12 |
| 15m | NASDAQ:AMZN | 20412 | 2025-04-01 | 2026-07-10 |
| 15m | NASDAQ:MU | 20363 | 2025-04-01 | 2026-07-10 |
| 15m | NASDAQ:QQQ | 20442 | 2025-04-01 | 2026-07-10 |
| 30m | AMEX:SPY | 20187 | 2024-01-02 | 2026-07-10 |
| 30m | NASDAQ:AMZN | 20171 | 2024-01-02 | 2026-07-10 |
| 30m | NASDAQ:MU | 20080 | 2024-01-02 | 2026-07-10 |
| 30m | NASDAQ:QQQ | 20181 | 2024-01-02 | 2026-07-10 |

The key comparison is calendar coverage. The 5-minute equity proxies generally begin in February 2026, while 15-minute proxies begin April 2025 and 30-minute proxies begin January 2024. Changing chart timeframe also changes entry sampling, so the 15m/30m results are stress tests rather than a pure holdout of the exact 5m strategy.

## Profile map

### 5m gate and native-exit screen

| Profile | Full parameters |
|---|---|
| G01 | full6, flip, BF off, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| G02 | full6, state, BF off, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| G03 | intraday3, flip, BF off, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| G04 | intraday3, state, BF off, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| G05 | fast3, flip, BF off, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| G06 | fast3, state, BF off, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| G07 | mid4, flip, BF off, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| G08 | mid4, state, BF off, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| G09 | slow4, flip, BF off, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| G10 | slow4, state, BF off, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| G11 | dw4, flip, BF off, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| G12 | dw4, state, BF off, arm/exit 15/15, regime stand_aside, gov ratchet, both |

### 5m arming and exit timing screen

| Profile | Full parameters |
|---|---|
| T01 | full6, flip, BF off, arm/exit 5/5, regime stand_aside, gov ratchet, both |
| T02 | full6, flip, BF off, arm/exit 5/15, regime stand_aside, gov ratchet, both |
| T03 | full6, flip, BF off, arm/exit 5/30, regime stand_aside, gov ratchet, both |
| T04 | full6, flip, BF off, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| T05 | full6, flip, BF off, arm/exit 15/30, regime stand_aside, gov ratchet, both |
| T06 | full6, flip, BF off, arm/exit 15/60, regime stand_aside, gov ratchet, both |
| T07 | full6, flip, BF off, arm/exit 30/30, regime stand_aside, gov ratchet, both |
| T08 | full6, flip, BF off, arm/exit 30/60, regime stand_aside, gov ratchet, both |

### 5m BF sensitivity grid

| Profile | Full parameters |
|---|---|
| B01 | full6, flip, BF 15/5 recycle, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| B02 | full6, flip, BF 15/5 ratchet, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| B03 | full6, flip, BF 15/10 recycle, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| B04 | full6, flip, BF 15/10 ratchet, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| B05 | full6, flip, BF 15/20 recycle, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| B06 | full6, flip, BF 15/20 ratchet, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| B07 | full6, flip, BF 30/5 recycle, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| B08 | full6, flip, BF 30/5 ratchet, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| B09 | full6, flip, BF 30/10 recycle, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| B10 | full6, flip, BF 30/10 ratchet, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| B11 | full6, flip, BF 30/20 recycle, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| B12 | full6, flip, BF 30/20 ratchet, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| B13 | full6, flip, BF 60/5 recycle, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| B14 | full6, flip, BF 60/5 ratchet, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| B15 | full6, flip, BF 60/10 recycle, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| B16 | full6, flip, BF 60/10 ratchet, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| B17 | full6, flip, BF 60/20 recycle, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| B18 | full6, flip, BF 60/20 ratchet, arm/exit 15/15, regime stand_aside, gov ratchet, both |

### 5m regime, governor, and direction control without BF

| Profile | Full parameters |
|---|---|
| R01 | full6, flip, BF off, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| R02 | full6, flip, BF off, arm/exit 15/15, regime stand_aside, gov ratchet, long_only |
| R03 | full6, flip, BF off, arm/exit 15/15, regime stand_aside, gov ratchet, short_only |
| R04 | full6, flip, BF off, arm/exit 15/15, regime stand_aside, gov off, both |
| R05 | full6, flip, BF off, arm/exit 15/15, regime stand_aside, gov off, long_only |
| R06 | full6, flip, BF off, arm/exit 15/15, regime stand_aside, gov off, short_only |
| R07 | full6, flip, BF off, arm/exit 15/15, regime off, gov ratchet, both |
| R08 | full6, flip, BF off, arm/exit 15/15, regime off, gov ratchet, long_only |
| R09 | full6, flip, BF off, arm/exit 15/15, regime off, gov ratchet, short_only |
| R10 | full6, flip, BF off, arm/exit 15/15, regime off, gov off, both |
| R11 | full6, flip, BF off, arm/exit 15/15, regime off, gov off, long_only |
| R12 | full6, flip, BF off, arm/exit 15/15, regime off, gov off, short_only |

### 5m regime, governor, and direction grid with BF60/10 recycle

| Profile | Full parameters |
|---|---|
| R01 | full6, flip, BF 60/10 recycle, arm/exit 15/15, regime stand_aside, gov ratchet, both |
| R02 | full6, flip, BF 60/10 recycle, arm/exit 15/15, regime stand_aside, gov ratchet, long_only |
| R03 | full6, flip, BF 60/10 recycle, arm/exit 15/15, regime stand_aside, gov ratchet, short_only |
| R04 | full6, flip, BF 60/10 recycle, arm/exit 15/15, regime stand_aside, gov off, both |
| R05 | full6, flip, BF 60/10 recycle, arm/exit 15/15, regime stand_aside, gov off, long_only |
| R06 | full6, flip, BF 60/10 recycle, arm/exit 15/15, regime stand_aside, gov off, short_only |
| R07 | full6, flip, BF 60/10 recycle, arm/exit 15/15, regime off, gov ratchet, both |
| R08 | full6, flip, BF 60/10 recycle, arm/exit 15/15, regime off, gov ratchet, long_only |
| R09 | full6, flip, BF 60/10 recycle, arm/exit 15/15, regime off, gov ratchet, short_only |
| R10 | full6, flip, BF 60/10 recycle, arm/exit 15/15, regime off, gov off, both |
| R11 | full6, flip, BF 60/10 recycle, arm/exit 15/15, regime off, gov off, long_only |
| R12 | full6, flip, BF 60/10 recycle, arm/exit 15/15, regime off, gov off, short_only |

## Aggregate results

Means are intentionally omitted because MU creates extreme compounding outliers. Positive-ticker count, median, worst result, drawdown, and sample size drive the judgment.

### 5m gate and native-exit screen (120 runs)

| Profile | Parameters | Positive | Sparse | Median total % | Worst % | Best % | Median PF | Median DD % | Median trades |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| G01 | full6; flip | 9/10 | 3 | 8.34 | -24.73 | 152.49 | 1.55 | 11.26 | 14.5 |
| G02 | full6; state | 4/10 | 0 | -2.96 | -14.19 | 31.10 | 0.90 | 8.52 | 196.5 |
| G03 | intraday3; flip | 1/10 | 0 | -16.29 | -37.87 | 12.14 | 0.74 | 23.19 | 388.0 |
| G04 | intraday3; state | 2/10 | 0 | -18.64 | -37.75 | 65.20 | 0.78 | 21.27 | 668.5 |
| G05 | fast3; flip | 2/10 | 0 | -22.53 | -31.60 | 29.20 | 0.77 | 24.47 | 719.0 |
| G06 | fast3; state | 2/10 | 0 | -26.20 | -35.33 | 53.59 | 0.72 | 27.70 | 1024.5 |
| G07 | mid4; flip | 1/10 | 0 | -16.18 | -36.48 | 9.46 | 0.74 | 23.65 | 381.5 |
| G08 | mid4; state | 2/10 | 0 | -21.89 | -31.57 | 69.14 | 0.75 | 22.26 | 771.0 |
| G09 | slow4; flip | 9/10 | 3 | 8.17 | -24.72 | 152.49 | 1.58 | 11.26 | 14.5 |
| G10 | slow4; state | 4/10 | 0 | -0.93 | -17.31 | 51.26 | 0.96 | 8.50 | 200.0 |
| G11 | dw4; flip | 3/10 | 0 | -7.31 | -24.18 | 48.98 | 0.83 | 15.55 | 71.0 |
| G12 | dw4; state | 2/10 | 0 | -13.15 | -27.07 | 34.89 | 0.76 | 13.55 | 447.0 |

### 5m arming and exit timing screen (48 runs)

| Profile | Parameters | Positive | Sparse | Median total % | Worst % | Best % | Median PF | Median DD % | Median trades |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| T01 | arm 5; exit 5 | 5/6 | 1 | 8.57 | -1.70 | 158.06 | 1.64 | 12.83 | 15.5 |
| T02 | arm 5; exit 15 | 6/6 | 1 | 8.21 | 0.89 | 154.63 | 1.56 | 11.80 | 14.0 |
| T03 | arm 5; exit 30 | 6/6 | 1 | 7.39 | 0.54 | 184.03 | 1.53 | 11.69 | 13.0 |
| T04 | arm 15; exit 15 | 6/6 | 1 | 8.34 | 0.78 | 152.49 | 1.62 | 12.13 | 14.5 |
| T05 | arm 15; exit 30 | 6/6 | 1 | 6.91 | 0.38 | 174.07 | 1.48 | 13.11 | 13.5 |
| T06 | arm 15; exit 60 | 5/6 | 1 | 4.81 | -0.21 | 123.48 | 1.33 | 14.44 | 12.0 |
| T07 | arm 30; exit 30 | 6/6 | 1 | 7.45 | 0.43 | 172.09 | 1.49 | 13.48 | 13.5 |
| T08 | arm 30; exit 60 | 5/6 | 1 | 5.42 | -0.33 | 121.19 | 1.36 | 14.67 | 12.0 |

### 5m BF sensitivity grid (108 runs)

| Profile | Parameters | Positive | Sparse | Median total % | Worst % | Best % | Median PF | Median DD % | Median trades |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B01 | BF 15; strength 5; recycle | 4/6 | 0 | 4.36 | -4.35 | 129.98 | 1.12 | 14.29 | 48.5 |
| B02 | BF 15; strength 5; ratchet | 4/6 | 0 | 5.46 | -8.33 | 54.15 | 1.28 | 9.90 | 31.5 |
| B03 | BF 15; strength 10; recycle | 6/6 | 0 | 5.33 | 0.30 | 118.32 | 1.18 | 12.66 | 34.0 |
| B04 | BF 15; strength 10; ratchet | 4/6 | 0 | 0.51 | -4.95 | 78.42 | 1.01 | 10.67 | 25.5 |
| B05 | BF 15; strength 20; recycle | 4/6 | 0 | 5.84 | -1.94 | 134.20 | 1.28 | 13.06 | 26.0 |
| B06 | BF 15; strength 20; ratchet | 4/6 | 0 | 9.34 | -1.59 | 90.16 | 1.41 | 11.42 | 23.0 |
| B07 | BF 30; strength 5; recycle | 6/6 | 0 | 3.57 | 0.09 | 143.57 | 1.14 | 12.80 | 31.5 |
| B08 | BF 30; strength 5; ratchet | 4/6 | 0 | 4.85 | -5.74 | 89.95 | 1.12 | 11.18 | 26.0 |
| B09 | BF 30; strength 10; recycle | 4/6 | 0 | 4.57 | -2.09 | 136.47 | 1.21 | 13.14 | 26.0 |
| B10 | BF 30; strength 10; ratchet | 4/6 | 0 | 9.04 | -0.84 | 90.75 | 1.42 | 11.42 | 22.5 |
| B11 | BF 30; strength 20; recycle | 5/6 | 0 | 8.92 | -0.11 | 164.41 | 1.43 | 13.63 | 20.5 |
| B12 | BF 30; strength 20; ratchet | 5/6 | 0 | 7.78 | -4.16 | 164.89 | 1.59 | 10.87 | 18.0 |
| B13 | BF 60; strength 5; recycle | 4/6 | 0 | 6.01 | -3.27 | 119.52 | 1.34 | 13.16 | 27.0 |
| B14 | BF 60; strength 5; ratchet | 4/6 | 0 | 6.59 | -2.74 | 67.64 | 1.28 | 12.53 | 23.5 |
| B15 | BF 60; strength 10; recycle | 6/6 | 0 | 9.05 | 0.65 | 164.51 | 1.43 | 12.89 | 21.0 |
| B16 | BF 60; strength 10; ratchet | 5/6 | 0 | 7.94 | -4.64 | 165.01 | 1.59 | 11.57 | 18.5 |
| B17 | BF 60; strength 20; recycle | 5/6 | 1 | 8.76 | -0.17 | 141.59 | 1.39 | 13.60 | 19.0 |
| B18 | BF 60; strength 20; ratchet | 5/6 | 1 | 12.92 | -0.15 | 122.90 | 1.66 | 10.09 | 18.5 |

### 5m regime, governor, and direction control without BF (72 runs)

| Profile | Parameters | Positive | Sparse | Median total % | Worst % | Best % | Median PF | Median DD % | Median trades |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| R01 | regime stand_aside; gov ratchet; both | 6/6 | 1 | 8.34 | 0.82 | 152.49 | 1.62 | 12.13 | 14.5 |
| R02 | regime stand_aside; gov ratchet; long_only | 5/6 | 4 | 12.79 | -2.86 | 141.91 | 2.32 | 5.69 | 8.0 |
| R03 | regime stand_aside; gov ratchet; short_only | 1/6 | 4 | -1.14 | -10.53 | 2.43 | 0.55 | 10.16 | 8.0 |
| R04 | regime stand_aside; gov off; both | 6/6 | 1 | 8.00 | 0.88 | 153.03 | 1.53 | 11.86 | 14.5 |
| R05 | regime stand_aside; gov off; long_only | 5/6 | 4 | 12.79 | -2.86 | 142.25 | 2.32 | 5.69 | 8.0 |
| R06 | regime stand_aside; gov off; short_only | 1/6 | 4 | -1.14 | -10.53 | 2.43 | 0.55 | 10.16 | 8.0 |
| R07 | regime off; gov ratchet; both | 6/6 | 1 | 8.34 | 0.80 | 152.49 | 1.62 | 12.13 | 14.5 |
| R08 | regime off; gov ratchet; long_only | 5/6 | 4 | 12.79 | -2.86 | 141.91 | 2.32 | 5.69 | 8.0 |
| R09 | regime off; gov ratchet; short_only | 1/6 | 4 | -1.14 | -10.53 | 2.43 | 0.55 | 10.16 | 8.0 |
| R10 | regime off; gov off; both | 6/6 | 1 | 8.00 | 0.88 | 153.03 | 1.53 | 11.86 | 14.5 |
| R11 | regime off; gov off; long_only | 5/6 | 4 | 12.79 | -2.86 | 142.25 | 2.32 | 5.69 | 8.0 |
| R12 | regime off; gov off; short_only | 1/6 | 4 | -1.14 | -10.53 | 2.43 | 0.55 | 10.16 | 8.0 |

### 5m regime, governor, and direction grid with BF60/10 recycle (72 runs)

| Profile | Parameters | Positive | Sparse | Median total % | Worst % | Best % | Median PF | Median DD % | Median trades |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| R01 | regime stand_aside; gov ratchet; both | 6/6 | 0 | 9.05 | 0.65 | 164.51 | 1.43 | 12.89 | 21.0 |
| R02 | regime stand_aside; gov ratchet; long_only | 5/6 | 2 | 12.54 | -3.41 | 155.26 | 2.07 | 5.74 | 13.0 |
| R03 | regime stand_aside; gov ratchet; short_only | 1/6 | 2 | -2.65 | -10.53 | 5.89 | 0.78 | 10.80 | 11.5 |
| R04 | regime stand_aside; gov off; both | 6/6 | 0 | 8.71 | 0.72 | 165.05 | 1.38 | 12.85 | 21.0 |
| R05 | regime stand_aside; gov off; long_only | 5/6 | 2 | 12.54 | -3.07 | 159.77 | 2.07 | 5.74 | 13.0 |
| R06 | regime stand_aside; gov off; short_only | 1/6 | 2 | -2.65 | -10.53 | 5.89 | 0.78 | 10.80 | 11.5 |
| R07 | regime off; gov ratchet; both | 6/6 | 0 | 9.05 | 0.65 | 164.51 | 1.43 | 12.89 | 21.0 |
| R08 | regime off; gov ratchet; long_only | 5/6 | 2 | 12.54 | -3.39 | 155.26 | 2.07 | 5.74 | 13.0 |
| R09 | regime off; gov ratchet; short_only | 1/6 | 2 | -2.65 | -10.53 | 5.89 | 0.78 | 10.80 | 11.5 |
| R10 | regime off; gov off; both | 6/6 | 0 | 8.71 | 0.72 | 165.05 | 1.38 | 12.85 | 21.0 |
| R11 | regime off; gov off; long_only | 5/6 | 2 | 12.54 | -3.07 | 159.77 | 2.07 | 5.74 | 13.0 |
| R12 | regime off; gov off; short_only | 1/6 | 2 | -2.65 | -10.53 | 5.89 | 0.78 | 10.80 | 11.5 |

### 15m calendar-window extension (20 runs)

| Profile | Parameters | Positive | Sparse | Median total % | Worst % | Best % | Median PF | Median DD % | Median trades |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B15 | BF 60; strength 10; recycle | 6/10 | 0 | 5.23 | -29.50 | 697.95 | 1.11 | 25.95 | 63.0 |
| N00 | full6, flip, BF off, arm/exit 15/15, regime stand_aside, gov ratchet, both | 6/10 | 1 | 3.26 | -24.61 | 695.57 | 1.08 | 24.27 | 41.0 |

### 30m long-window equity stress test (8 runs)

| Profile | Parameters | Positive | Sparse | Median total % | Worst % | Best % | Median PF | Median DD % | Median trades |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B15 | BF 60; strength 10; recycle | 2/4 | 0 | -0.11 | -48.65 | 487.76 | 1.01 | 40.87 | 154.5 |
| N00 | full6, flip, BF off, arm/exit 30/30, regime stand_aside, gov ratchet, both | 2/4 | 0 | -4.76 | -45.71 | 759.69 | 0.96 | 29.93 | 118.0 |

## Ranked configurations

Ranking rule: consistency first, then median total return, worst result, drawdown, trade sufficiency, and simplicity. A large single-ticker return cannot outrank broad consistency. The evidence column is from the indicated five-minute phase; longer-window failures are included in the judgment.

| Rank | Configuration | Positive | Median total % | Worst % | Median PF | Median DD % | Median trades | Judgment |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | No BF: full6, flip, 15/15, both (G01/T04/R01) | 9/10 | 8.34 | -24.73 | 1.55 | 11.26 | 14.5 | Best 5m cross-ticker result. Keep only as a frozen research baseline; it fails the longer-window tests. |
| 2 | No BF: slow4, flip, 15/15, both (G09) | 9/10 | 8.17 | -24.72 | 1.58 | 11.26 | 14.5 | Nearly identical to full6 with fewer gate inputs. Attractive simplification, but not separately validated at 15m/30m. |
| 3 | BF60/10 recycle: full6, flip, 15/15, both (B15) | 6/6 | 9.05 | 0.65 | 1.43 | 12.89 | 21.0 | All six representatives positive and a small median uplift, offset by lower PF, more trades, and worse long-window risk. |
| 4 | No BF: full6, flip, arm 5, exit 15 (T02) | 6/6 | 8.21 | 0.89 | 1.56 | 11.80 | 14.0 | Close second to 15/15 with slightly lower median drawdown. No reason to prefer it without a holdout win. |
| 5 | BF60/20 ratchet: full6, flip, 15/15, both (B18) | 5/6 | 12.92 | -0.15 | 1.66 | 10.09 | 18.5 | Higher median and lower median DD, but one negative and one sparse ticker. More selection risk than B15. |
| 6 | No BF long-only: full6, flip, 15/15 (R02) | 5/6 | 12.79 | -2.86 | 2.32 | 5.69 | 8.0 | High median and low DD, but four of six samples are sparse and HIP-3 AMZN loses. Likely bullish-regime exposure, not a balanced edge. |

None passes a deployment standard. Rank 1 is simply the least-bad research candidate.

## Critical findings

1. The apparent 5m edge is not stable across calendar depth. Fifteen-minute results fall to 6/10 positives. Thirty-minute equity results fall to 2/4, with AMZN near -46% to -49% and QQQ negative.
2. MU dominates the upside. The no-BF configuration returns +152.49% on 5m NASDAQ:MU and +759.69% on 30m NASDAQ:MU. AMZN and QQQ fail in the same long-window test. This is cross-sectional concentration, not robust universality.
3. Full6 and slow4 are functionally close in this sample. Their 5m medians, drawdowns, and individual outputs are nearly identical. The 120 and 240 minute gates add complexity without demonstrated incremental value.
4. State exits are too reactive. They create roughly 200 to more than 1,000 median trades depending on the gate and generally lose money. Flip exits win the screen partly by holding much longer, which creates endpoint risk.
5. BF is not a clear improvement. The best robust BF cell adds exits and slightly improves the 5m median, but lowers PF and worsens longer-window drawdown. BF should remain off in the canonical baseline.
6. Long-only results expose regime bias. Long-only looks attractive in the short bullish window; short-only loses on five of six representatives. Selecting long-only now would encode the exact launch-regime bias the experiment is meant to avoid.
7. Open positions are material. Every leading both-direction run ends with an open position. NASDAQ:MU open P/L adds about 26 percentage points in the 5m baseline and about 90 points in the 30m baseline. Endpoint selection can materially move the headline.
8. The sizing model magnifies path dependence. Reinvesting 100% of equity with zero margin constraints produces explosive outliers and deep losses. A deployable test needs fixed risk per trade or volatility targeting, leverage and liquidation rules, and portfolio-level exposure limits.
9. Costs are under-modeled. One tick is not comparable across AMZN, indices, crude, and a young synthetic. HIP-3 funding, spread, market impact, mark/index behavior, and venue-specific fees are absent. State-exit profiles would deteriorate further under realistic costs.
10. Equity proxies are useful but not identical. Extended-hours equities have session gaps; HIP-3 trades continuously. QQQ and SPY are tradable proxies, not the same instrument as XYZ100 and SP500 perpetuals. Basis and funding can change both triggers and fills.
11. This is an adaptive multiple-testing exercise. Gate, timing, BF, risk, direction, and timeframe branches were selected hierarchically. The winner is subject to selection bias and cannot be evaluated on the same data that selected it.
12. The script is closer to a TFC state machine than a complete STRAT strategy. It uses continuity and strict one-tick breaks, but it does not classify full STRAT scenarios, actionable patterns, magnitude targets, or scenario invalidation. Calling the result a complete STRAT backtest would overstate it.
13. Historical TradingView fills are not tick truth. Bar magnifier helps, but stop/limit ordering, gaps across BF lines, and current-period multi-timeframe opens still need replay or lower-level execution validation.
14. The W+D regime switch is redundant under full6 and showed no measurable effect. The governor also changed little because the strict gate produces few sequences. Both should be justified with targeted state tests before remaining in a production script.

## What I would do next

1. Freeze two candidates before seeing new data: (A) slow4 or full6, flip, 15/15, BF off, both directions; (B) the same with BF60/10 recycle. Do not retune them on the confirmation set.
2. Build a true time split with at least one bearish and one sideways regime. Use longer equity/futures history outside the TradingView 5m bar window, and reserve the final segment untouched.
3. Add unused holdout instruments. The current ranking already saw AMZN, MU, QQQ/SPY proxies, indices, crude, and SPCX; confirmation should use exposures not involved in selection.
4. Replace 100% compounding with fixed fractional risk, ATR or structural-stop distance, a leverage ceiling, and portfolio concurrency limits. Report return on capital, exposure, turnover, and time in market.
5. Model instrument-specific spread, slippage, fees, and HIP-3 funding. Stress each cost at 1x, 2x, and 3x rather than relying on one tick.
6. Force-close at common month-end checkpoints and also report mark-to-market equity. This measures endpoint sensitivity instead of hiding it in one final open trade.
7. Compare long and short behavior by pre-declared market regime. Do not solve poor shorts by deleting them after observing a bullish sample.
8. Validate the multi-timeframe open reconstruction, one-tick stops, BF pivot delay, and stop/limit precedence with deterministic bar-replay fixtures against the companion state machine.
9. Promote a candidate only if the untouched set has positive median total return, PF above 1.15, median drawdown below 20%, no catastrophic instrument loss, at least 30 trades per representative sample where feasible, and stable neighboring parameters.

## Every run with a per-run view

The comments are intentionally terse. They judge the run itself; they do not override the cross-ticker ranking.

### 5m gate and native-exit screen

| Profile | TF | Ticker | Loaded window | Total % | Closed % | Open d% | PF | Trades | DD % | View |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| G01 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 9.11 | 8.09 | 1.02 | 2.08 | 22 | 5.72 | Promising, but sample-limited. |
| G01 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 0.96 | 0.64 | 0.32 | 1.07 | 12 | 10.13 | Marginal; no reliable edge shown. |
| G01 | 5m | HIP3XYZ:CLUSDC.P | 2026-04-27..2026-07-12 | 23.19 | 17.79 | 5.40 | 2.29 | 9 | 12.40 | Strong in-sample; needs a holdout. Sparse sample. |
| G01 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 75.73 | 52.88 | 22.86 | 2.15 | 6 | 28.48 | Large in-sample gain; concentration risk. Sparse sample. |
| G01 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.80 | 0.25 | 0.55 | 1.05 | 15 | 2.64 | Marginal; no reliable edge shown. |
| G01 | 5m | HIP3XYZ:SPCXUSDC.P | 2026-05-17..2026-07-12 | -24.73 | -29.38 | 4.65 | 0.01 | 9 | 34.52 | Reject: material loss. Sparse sample. |
| G01 | 5m | HIP3XYZ:XYZ100USDC.P | 2026-04-27..2026-07-12 | 2.71 | 1.84 | 0.87 | 1.23 | 16 | 8.03 | Promising, but sample-limited. |
| G01 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 7.56 | 4.60 | 2.96 | 1.17 | 27 | 16.01 | Promising, but sample-limited. |
| G01 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 152.49 | 126.48 | 26.01 | 4.91 | 14 | 14.13 | Large in-sample gain; concentration risk. Open P/L is material. |
| G01 | 5m | NASDAQ:QQQ | 2026-02-09..2026-07-10 | 10.38 | 12.58 | -2.21 | 1.87 | 24 | 8.17 | Strong in-sample; needs a holdout. |
| G02 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | -2.94 | -2.91 | -0.03 | 0.86 | 274 | 3.95 | Negative; fails this ticker. Churn and cost-sensitive. |
| G02 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -5.44 | -5.44 | 0.00 | 0.77 | 182 | 7.81 | Negative; fails this ticker. Churn and cost-sensitive. |
| G02 | 5m | HIP3XYZ:CLUSDC.P | 2026-04-27..2026-07-12 | -14.19 | -14.19 | 0.00 | 0.64 | 151 | 14.55 | Negative; fails this ticker. Churn and cost-sensitive. |
| G02 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 6.82 | 6.82 | 0.00 | 1.09 | 201 | 9.24 | Marginal; no reliable edge shown. Churn and cost-sensitive. |
| G02 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -4.81 | -4.81 | 0.00 | 0.59 | 183 | 4.81 | Negative; fails this ticker. Churn and cost-sensitive. |
| G02 | 5m | HIP3XYZ:SPCXUSDC.P | 2026-05-17..2026-07-12 | 3.92 | 3.92 | 0.00 | 1.10 | 99 | 9.62 | Promising, but sample-limited. |
| G02 | 5m | HIP3XYZ:XYZ100USDC.P | 2026-04-27..2026-07-12 | 2.70 | 2.70 | 0.00 | 1.19 | 192 | 2.65 | Promising, but sample-limited. Churn and cost-sensitive. |
| G02 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | -2.98 | -2.98 | 0.00 | 0.93 | 244 | 10.40 | Negative; fails this ticker. Churn and cost-sensitive. |
| G02 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 31.10 | 31.10 | 0.00 | 1.25 | 262 | 10.84 | Promising, but sample-limited. Churn and cost-sensitive. |
| G02 | 5m | NASDAQ:QQQ | 2026-02-09..2026-07-10 | -4.71 | -4.71 | 0.00 | 0.87 | 322 | 5.73 | Negative; fails this ticker. Churn and cost-sensitive. |
| G03 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | -15.24 | -15.21 | -0.03 | 0.70 | 385 | 16.15 | Reject: material loss. Churn and cost-sensitive. |
| G03 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -35.19 | -35.19 | 0.00 | 0.52 | 435 | 35.55 | Reject: severe loss or drawdown. Churn and cost-sensitive. |
| G03 | 5m | HIP3XYZ:CLUSDC.P | 2026-04-27..2026-07-12 | -23.64 | -23.44 | -0.20 | 0.75 | 375 | 27.62 | Reject: material loss. Churn and cost-sensitive. |
| G03 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 12.14 | 12.13 | 0.02 | 1.06 | 347 | 18.76 | Marginal; no reliable edge shown. Churn and cost-sensitive. |
| G03 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -17.34 | -17.34 | 0.00 | 0.54 | 414 | 17.63 | Reject: material loss. Churn and cost-sensitive. |
| G03 | 5m | HIP3XYZ:SPCXUSDC.P | 2026-05-17..2026-07-12 | -37.87 | -37.87 | 0.00 | 0.67 | 279 | 40.34 | Reject: severe loss or drawdown. Churn and cost-sensitive. |
| G03 | 5m | HIP3XYZ:XYZ100USDC.P | 2026-04-27..2026-07-12 | -7.88 | -7.88 | 0.00 | 0.84 | 391 | 10.57 | Negative; fails this ticker. Churn and cost-sensitive. |
| G03 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | -29.02 | -29.02 | 0.00 | 0.72 | 417 | 29.19 | Reject: material loss. Churn and cost-sensitive. |
| G03 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | -4.74 | -4.74 | 0.00 | 0.98 | 380 | 36.45 | Negative; fails this ticker. Churn and cost-sensitive. |
| G03 | 5m | NASDAQ:QQQ | 2026-02-09..2026-07-10 | -13.30 | -13.93 | 0.63 | 0.80 | 399 | 16.05 | Negative; fails this ticker. Churn and cost-sensitive. |
| G04 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | -16.21 | -16.18 | -0.03 | 0.71 | 692 | 16.29 | Reject: material loss. High churn. |
| G04 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -23.77 | -23.77 | 0.00 | 0.68 | 679 | 24.30 | Reject: material loss. High churn. |
| G04 | 5m | HIP3XYZ:CLUSDC.P | 2026-04-27..2026-07-12 | -28.82 | -28.65 | -0.17 | 0.75 | 629 | 30.60 | Reject: material loss. High churn. |
| G04 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 29.53 | 29.58 | -0.04 | 1.11 | 589 | 19.52 | Promising, but sample-limited. High churn. |
| G04 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -21.23 | -21.23 | 0.00 | 0.48 | 669 | 21.26 | Reject: material loss. High churn. |
| G04 | 5m | HIP3XYZ:SPCXUSDC.P | 2026-05-17..2026-07-12 | -37.75 | -37.75 | 0.00 | 0.69 | 447 | 41.34 | Reject: severe loss or drawdown. Churn and cost-sensitive. |
| G04 | 5m | HIP3XYZ:XYZ100USDC.P | 2026-04-27..2026-07-12 | -10.77 | -10.77 | 0.00 | 0.81 | 668 | 12.60 | Negative; fails this ticker. High churn. |
| G04 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | -21.08 | -21.08 | 0.00 | 0.80 | 672 | 22.83 | Reject: material loss. High churn. |
| G04 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 65.20 | 65.20 | 0.00 | 1.20 | 645 | 21.28 | Large in-sample gain; concentration risk. High churn. |
| G04 | 5m | NASDAQ:QQQ | 2026-02-09..2026-07-10 | -11.13 | -11.13 | 0.00 | 0.84 | 694 | 11.19 | Negative; fails this ticker. High churn. |
| G05 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | -20.89 | -20.86 | -0.03 | 0.68 | 733 | 21.17 | Reject: material loss. High churn. |
| G05 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -30.02 | -30.02 | 0.00 | 0.64 | 724 | 30.05 | Reject: severe loss or drawdown. High churn. |
| G05 | 5m | HIP3XYZ:CLUSDC.P | 2026-04-27..2026-07-12 | -31.60 | -31.42 | -0.18 | 0.75 | 676 | 34.27 | Reject: severe loss or drawdown. High churn. |
| G05 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 29.20 | 29.24 | -0.04 | 1.09 | 655 | 22.95 | Marginal; no reliable edge shown. High churn. |
| G05 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -24.24 | -24.24 | 0.00 | 0.49 | 721 | 24.26 | Reject: material loss. High churn. |
| G05 | 5m | HIP3XYZ:SPCXUSDC.P | 2026-05-17..2026-07-12 | -24.17 | -24.17 | 0.00 | 0.83 | 483 | 31.53 | Reject: material loss. Churn and cost-sensitive. |
| G05 | 5m | HIP3XYZ:XYZ100USDC.P | 2026-04-27..2026-07-12 | -16.28 | -16.28 | 0.00 | 0.74 | 717 | 18.04 | Reject: material loss. High churn. |
| G05 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | -25.17 | -25.17 | 0.00 | 0.79 | 728 | 25.81 | Reject: material loss. High churn. |
| G05 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 22.95 | 22.95 | 0.00 | 1.06 | 700 | 24.69 | Marginal; no reliable edge shown. High churn. |
| G05 | 5m | NASDAQ:QQQ | 2026-02-09..2026-07-10 | -17.04 | -17.06 | 0.01 | 0.79 | 742 | 17.59 | Reject: material loss. High churn. |
| G06 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | -25.26 | -25.23 | -0.02 | 0.63 | 1074 | 25.26 | Reject: material loss. High churn. |
| G06 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -28.33 | -28.33 | 0.00 | 0.68 | 1010 | 28.50 | Reject: material loss. High churn. |
| G06 | 5m | HIP3XYZ:CLUSDC.P | 2026-04-27..2026-07-12 | -35.33 | -35.33 | 0.00 | 0.75 | 1010 | 36.18 | Reject: severe loss or drawdown. High churn. |
| G06 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 22.52 | 22.57 | -0.05 | 1.07 | 978 | 19.69 | Marginal; no reliable edge shown. High churn. |
| G06 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -29.18 | -29.18 | 0.00 | 0.43 | 1058 | 29.20 | Reject: material loss. High churn. |
| G06 | 5m | HIP3XYZ:SPCXUSDC.P | 2026-05-17..2026-07-12 | -26.33 | -26.33 | 0.00 | 0.82 | 681 | 33.52 | Reject: material loss. High churn. |
| G06 | 5m | HIP3XYZ:XYZ100USDC.P | 2026-04-27..2026-07-12 | -22.16 | -22.16 | 0.00 | 0.68 | 1062 | 22.60 | Reject: material loss. High churn. |
| G06 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | -32.89 | -32.89 | 0.00 | 0.74 | 1026 | 33.90 | Reject: severe loss or drawdown. High churn. |
| G06 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 53.59 | 53.59 | 0.00 | 1.14 | 1023 | 18.60 | Large in-sample gain; concentration risk. High churn. |
| G06 | 5m | NASDAQ:QQQ | 2026-02-09..2026-07-10 | -26.07 | -26.08 | 0.01 | 0.70 | 1125 | 26.90 | Reject: material loss. High churn. |
| G07 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | -14.99 | -14.96 | -0.03 | 0.70 | 373 | 15.90 | Negative; fails this ticker. Churn and cost-sensitive. |
| G07 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -34.42 | -34.42 | 0.00 | 0.53 | 422 | 34.76 | Reject: severe loss or drawdown. Churn and cost-sensitive. |
| G07 | 5m | HIP3XYZ:CLUSDC.P | 2026-04-27..2026-07-12 | -23.18 | -22.96 | -0.22 | 0.75 | 360 | 27.24 | Reject: material loss. Churn and cost-sensitive. |
| G07 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 9.46 | 9.41 | 0.05 | 1.04 | 344 | 20.07 | Marginal; no reliable edge shown. Churn and cost-sensitive. |
| G07 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -17.37 | -17.37 | 0.00 | 0.54 | 406 | 17.66 | Reject: material loss. Churn and cost-sensitive. |
| G07 | 5m | HIP3XYZ:SPCXUSDC.P | 2026-05-17..2026-07-12 | -36.48 | -36.48 | 0.00 | 0.68 | 273 | 39.01 | Reject: severe loss or drawdown. Churn and cost-sensitive. |
| G07 | 5m | HIP3XYZ:XYZ100USDC.P | 2026-04-27..2026-07-12 | -9.59 | -9.59 | 0.00 | 0.81 | 387 | 11.90 | Negative; fails this ticker. Churn and cost-sensitive. |
| G07 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | -28.48 | -28.48 | 0.00 | 0.73 | 406 | 28.65 | Reject: material loss. Churn and cost-sensitive. |
| G07 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | -5.57 | -5.57 | 0.00 | 0.98 | 376 | 37.42 | Negative; fails this ticker. Churn and cost-sensitive. |
| G07 | 5m | NASDAQ:QQQ | 2026-02-09..2026-07-10 | -13.36 | -13.98 | 0.63 | 0.80 | 394 | 16.01 | Negative; fails this ticker. Churn and cost-sensitive. |
| G08 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | -19.55 | -19.52 | -0.03 | 0.65 | 804 | 19.55 | Reject: material loss. High churn. |
| G08 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -25.39 | -25.39 | 0.00 | 0.67 | 769 | 27.40 | Reject: material loss. High churn. |
| G08 | 5m | HIP3XYZ:CLUSDC.P | 2026-04-27..2026-07-12 | -30.43 | -30.23 | -0.20 | 0.75 | 744 | 31.54 | Reject: severe loss or drawdown. High churn. |
| G08 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 25.46 | 25.50 | -0.04 | 1.10 | 704 | 13.89 | Promising, but sample-limited. High churn. |
| G08 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -24.23 | -24.23 | 0.00 | 0.42 | 775 | 24.25 | Reject: material loss. High churn. |
| G08 | 5m | HIP3XYZ:SPCXUSDC.P | 2026-05-17..2026-07-12 | -31.57 | -31.57 | 0.00 | 0.74 | 494 | 39.69 | Reject: severe loss or drawdown. Churn and cost-sensitive. |
| G08 | 5m | HIP3XYZ:XYZ100USDC.P | 2026-04-27..2026-07-12 | -13.89 | -13.89 | 0.00 | 0.75 | 773 | 14.35 | Negative; fails this ticker. High churn. |
| G08 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | -25.79 | -25.79 | 0.00 | 0.77 | 767 | 27.95 | Reject: material loss. High churn. |
| G08 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 69.14 | 69.14 | 0.00 | 1.22 | 778 | 20.27 | Large in-sample gain; concentration risk. High churn. |
| G08 | 5m | NASDAQ:QQQ | 2026-02-09..2026-07-10 | -15.75 | -15.75 | 0.00 | 0.78 | 814 | 16.83 | Reject: material loss. High churn. |
| G09 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.78 | 7.76 | 1.02 | 2.01 | 24 | 5.36 | Promising, but sample-limited. |
| G09 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 0.96 | 0.64 | 0.32 | 1.07 | 12 | 10.13 | Marginal; no reliable edge shown. |
| G09 | 5m | HIP3XYZ:CLUSDC.P | 2026-04-27..2026-07-12 | 23.49 | 18.08 | 5.41 | 2.34 | 9 | 12.40 | Strong in-sample; needs a holdout. Sparse sample. |
| G09 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 75.77 | 52.88 | 22.89 | 2.15 | 6 | 28.48 | Large in-sample gain; concentration risk. Sparse sample. |
| G09 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.78 | 0.25 | 0.54 | 1.05 | 15 | 2.64 | Marginal; no reliable edge shown. |
| G09 | 5m | HIP3XYZ:SPCXUSDC.P | 2026-05-17..2026-07-12 | -24.72 | -29.38 | 4.66 | 0.01 | 9 | 34.52 | Reject: material loss. Sparse sample. |
| G09 | 5m | HIP3XYZ:XYZ100USDC.P | 2026-04-27..2026-07-12 | 2.53 | 1.66 | 0.87 | 1.20 | 18 | 8.19 | Promising, but sample-limited. |
| G09 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 7.56 | 4.60 | 2.96 | 1.17 | 27 | 16.01 | Promising, but sample-limited. |
| G09 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 152.49 | 126.48 | 26.01 | 4.91 | 14 | 14.13 | Large in-sample gain; concentration risk. Open P/L is material. |
| G09 | 5m | NASDAQ:QQQ | 2026-02-09..2026-07-10 | 11.05 | 13.25 | -2.21 | 1.96 | 24 | 8.09 | Strong in-sample; needs a holdout. |
| G10 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | -1.43 | -1.40 | -0.03 | 0.93 | 275 | 3.49 | Negative; fails this ticker. Churn and cost-sensitive. |
| G10 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -4.24 | -4.24 | 0.00 | 0.83 | 185 | 7.52 | Negative; fails this ticker. Churn and cost-sensitive. |
| G10 | 5m | HIP3XYZ:CLUSDC.P | 2026-04-27..2026-07-12 | -17.31 | -17.31 | 0.00 | 0.57 | 150 | 17.67 | Reject: material loss. |
| G10 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 23.55 | 23.55 | 0.00 | 1.34 | 194 | 9.39 | Strong in-sample; needs a holdout. Churn and cost-sensitive. |
| G10 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -3.77 | -3.77 | 0.00 | 0.67 | 177 | 4.02 | Negative; fails this ticker. Churn and cost-sensitive. |
| G10 | 5m | HIP3XYZ:SPCXUSDC.P | 2026-05-17..2026-07-12 | 7.05 | 7.05 | 0.00 | 1.18 | 99 | 10.78 | Promising, but sample-limited. |
| G10 | 5m | HIP3XYZ:XYZ100USDC.P | 2026-04-27..2026-07-12 | 1.32 | 1.32 | 0.00 | 1.08 | 206 | 3.84 | Marginal; no reliable edge shown. Churn and cost-sensitive. |
| G10 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | -0.43 | -0.43 | 0.00 | 0.99 | 247 | 10.73 | Negative; fails this ticker. Churn and cost-sensitive. |
| G10 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 51.26 | 51.26 | 0.00 | 1.44 | 251 | 9.39 | Large in-sample gain; concentration risk. Churn and cost-sensitive. |
| G10 | 5m | NASDAQ:QQQ | 2026-02-09..2026-07-10 | -5.41 | -5.41 | 0.00 | 0.86 | 325 | 7.61 | Negative; fails this ticker. Churn and cost-sensitive. |
| G11 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 0.55 | -0.34 | 0.89 | 0.99 | 96 | 6.90 | Positive only with open P/L; endpoint-fragile. |
| G11 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -20.65 | -20.63 | -0.02 | 0.44 | 64 | 20.73 | Reject: material loss. |
| G11 | 5m | HIP3XYZ:CLUSDC.P | 2026-04-27..2026-07-12 | 15.65 | 8.19 | 7.46 | 1.23 | 60 | 10.63 | Promising, but sample-limited. |
| G11 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 48.98 | 46.51 | 2.46 | 1.54 | 38 | 20.79 | Strong in-sample; needs a holdout. |
| G11 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -9.61 | -10.09 | 0.48 | 0.44 | 72 | 11.13 | Negative; fails this ticker. |
| G11 | 5m | HIP3XYZ:SPCXUSDC.P | 2026-05-17..2026-07-12 | -24.18 | -30.40 | 6.22 | 0.44 | 40 | 30.91 | Reject: material loss. |
| G11 | 5m | HIP3XYZ:XYZ100USDC.P | 2026-04-27..2026-07-12 | -4.88 | -4.98 | 0.10 | 0.79 | 70 | 8.91 | Negative; fails this ticker. |
| G11 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | -15.01 | -15.01 | 0.00 | 0.75 | 92 | 19.97 | Reject: material loss. |
| G11 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | -14.93 | -12.78 | -2.15 | 0.93 | 102 | 38.07 | Negative; fails this ticker. |
| G11 | 5m | NASDAQ:QQQ | 2026-02-09..2026-07-10 | -5.02 | -5.76 | 0.74 | 0.87 | 107 | 10.37 | Negative; fails this ticker. |
| G12 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | -10.98 | -10.95 | -0.03 | 0.75 | 543 | 11.29 | Negative; fails this ticker. High churn. |
| G12 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -14.25 | -14.25 | 0.00 | 0.71 | 356 | 14.34 | Negative; fails this ticker. Churn and cost-sensitive. |
| G12 | 5m | HIP3XYZ:CLUSDC.P | 2026-04-27..2026-07-12 | -22.27 | -22.27 | 0.00 | 0.69 | 340 | 23.22 | Reject: material loss. Churn and cost-sensitive. |
| G12 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 16.02 | 16.02 | 0.00 | 1.10 | 407 | 13.51 | Marginal; no reliable edge shown. Churn and cost-sensitive. |
| G12 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -13.58 | -13.58 | 0.00 | 0.54 | 443 | 13.58 | Negative; fails this ticker. Churn and cost-sensitive. |
| G12 | 5m | HIP3XYZ:SPCXUSDC.P | 2026-05-17..2026-07-12 | -27.07 | -27.07 | 0.00 | 0.68 | 224 | 34.50 | Reject: material loss. Churn and cost-sensitive. |
| G12 | 5m | HIP3XYZ:XYZ100USDC.P | 2026-04-27..2026-07-12 | -8.48 | -8.48 | 0.00 | 0.78 | 451 | 10.17 | Negative; fails this ticker. Churn and cost-sensitive. |
| G12 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | -19.70 | -19.70 | 0.00 | 0.76 | 494 | 20.62 | Reject: material loss. Churn and cost-sensitive. |
| G12 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 34.89 | 34.89 | 0.00 | 1.13 | 529 | 13.43 | Promising, but sample-limited. High churn. |
| G12 | 5m | NASDAQ:QQQ | 2026-02-09..2026-07-10 | -12.72 | -12.73 | 0.02 | 0.79 | 575 | 13.18 | Negative; fails this ticker. High churn. |

### 5m arming and exit timing screen

| Profile | TF | Ticker | Loaded window | Total % | Closed % | Open d% | PF | Trades | DD % | View |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| T01 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.08 | 7.06 | 1.02 | 1.81 | 27 | 5.92 | Promising, but sample-limited. |
| T01 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -1.70 | -1.97 | 0.26 | 0.84 | 14 | 11.02 | Negative; fails this ticker. |
| T01 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 77.79 | 54.59 | 23.21 | 2.22 | 7 | 27.70 | Large in-sample gain; concentration risk. Sparse sample. |
| T01 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 2.30 | 1.76 | 0.55 | 1.47 | 15 | 1.76 | Promising, but sample-limited. |
| T01 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 9.06 | 5.97 | 3.09 | 1.22 | 32 | 14.96 | Promising, but sample-limited. |
| T01 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 158.06 | 131.96 | 26.10 | 4.81 | 16 | 14.63 | Large in-sample gain; concentration risk. Open P/L is material. |
| T02 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 9.35 | 8.33 | 1.02 | 2.14 | 23 | 5.51 | Promising, but sample-limited. |
| T02 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 1.02 | 0.69 | 0.34 | 1.07 | 12 | 10.12 | Marginal; no reliable edge shown. |
| T02 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 70.35 | 48.37 | 21.98 | 1.97 | 7 | 30.59 | Large in-sample gain; concentration risk. Sparse sample. |
| T02 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.89 | 0.35 | 0.53 | 1.07 | 15 | 2.59 | Marginal; no reliable edge shown. |
| T02 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 7.07 | 4.10 | 2.96 | 1.15 | 29 | 17.00 | Promising, but sample-limited. |
| T02 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 154.63 | 128.62 | 26.01 | 5.22 | 13 | 13.48 | Large in-sample gain; concentration risk. Open P/L is material. |
| T03 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.14 | 7.12 | 1.02 | 1.84 | 23 | 6.20 | Promising, but sample-limited. |
| T03 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 4.42 | 1.92 | 2.50 | 1.23 | 10 | 9.39 | Promising, but sample-limited. Open P/L is material. |
| T03 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 73.06 | 50.60 | 22.46 | 2.07 | 6 | 29.53 | Large in-sample gain; concentration risk. Sparse sample. |
| T03 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.54 | 0.04 | 0.49 | 1.01 | 14 | 2.94 | Marginal; no reliable edge shown. |
| T03 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 6.63 | 3.67 | 2.96 | 1.13 | 25 | 16.87 | Promising, but sample-limited. |
| T03 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 184.03 | 154.77 | 29.26 | 7.24 | 12 | 14.00 | Large in-sample gain; concentration risk. Open P/L is material. |
| T04 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 9.11 | 8.09 | 1.02 | 2.08 | 22 | 5.72 | Promising, but sample-limited. |
| T04 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 0.98 | 0.64 | 0.34 | 1.07 | 12 | 10.13 | Marginal; no reliable edge shown. |
| T04 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 75.52 | 52.88 | 22.65 | 2.15 | 6 | 28.48 | Large in-sample gain; concentration risk. Sparse sample. |
| T04 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.78 | 0.25 | 0.53 | 1.05 | 15 | 2.64 | Marginal; no reliable edge shown. |
| T04 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 7.56 | 4.60 | 2.96 | 1.17 | 27 | 16.01 | Promising, but sample-limited. |
| T04 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 152.49 | 126.48 | 26.01 | 4.91 | 14 | 14.13 | Large in-sample gain; concentration risk. Open P/L is material. |
| T05 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.03 | 7.01 | 1.02 | 1.84 | 22 | 6.14 | Promising, but sample-limited. |
| T05 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 3.60 | 1.16 | 2.44 | 1.13 | 10 | 10.01 | Promising, but sample-limited. Open P/L is material. |
| T05 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 70.19 | 48.11 | 22.09 | 1.97 | 6 | 30.70 | Large in-sample gain; concentration risk. Sparse sample. |
| T05 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.38 | -0.11 | 0.49 | 0.98 | 14 | 3.04 | Positive only with open P/L; endpoint-fragile. |
| T05 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 5.79 | 2.83 | 2.96 | 1.10 | 24 | 17.04 | Marginal; no reliable edge shown. Open P/L is material. |
| T05 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 174.07 | 145.25 | 28.82 | 6.40 | 13 | 16.20 | Large in-sample gain; concentration risk. Open P/L is material. |
| T06 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 6.54 | 5.69 | 0.85 | 1.55 | 19 | 7.59 | Promising, but sample-limited. |
| T06 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -0.21 | -2.56 | 2.35 | 0.79 | 10 | 13.37 | Negative; fails this ticker. Open P/L is material. |
| T06 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 76.94 | 54.27 | 22.67 | 2.24 | 5 | 27.59 | Large in-sample gain; concentration risk. Sparse sample. |
| T06 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.95 | 0.52 | 0.44 | 1.11 | 12 | 3.68 | Promising, but sample-limited. |
| T06 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 3.07 | 0.49 | 2.57 | 1.02 | 21 | 15.52 | Marginal; no reliable edge shown. Open P/L is material. |
| T06 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 123.48 | 100.69 | 22.79 | 3.26 | 12 | 23.55 | Large in-sample gain; concentration risk. Open P/L is material. |
| T07 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.09 | 7.07 | 1.02 | 1.84 | 22 | 6.19 | Promising, but sample-limited. |
| T07 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 3.36 | 0.92 | 2.44 | 1.10 | 10 | 10.22 | Promising, but sample-limited. Open P/L is material. |
| T07 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 69.87 | 48.11 | 21.76 | 1.97 | 6 | 30.70 | Large in-sample gain; concentration risk. Sparse sample. |
| T07 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.43 | -0.06 | 0.49 | 0.99 | 14 | 2.95 | Positive only with open P/L; endpoint-fragile. |
| T07 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 6.81 | 3.93 | 2.88 | 1.14 | 23 | 16.91 | Promising, but sample-limited. |
| T07 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 172.09 | 144.70 | 27.39 | 6.33 | 13 | 16.75 | Large in-sample gain; concentration risk. Open P/L is material. |
| T08 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 6.98 | 6.16 | 0.82 | 1.60 | 18 | 7.66 | Promising, but sample-limited. |
| T08 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -0.33 | -2.68 | 2.35 | 0.79 | 10 | 13.47 | Negative; fails this ticker. Open P/L is material. |
| T08 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 76.94 | 54.27 | 22.67 | 2.24 | 5 | 27.59 | Large in-sample gain; concentration risk. Sparse sample. |
| T08 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.98 | 0.56 | 0.43 | 1.12 | 12 | 3.60 | Promising, but sample-limited. |
| T08 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 3.86 | 1.22 | 2.64 | 1.04 | 21 | 15.87 | Marginal; no reliable edge shown. Open P/L is material. |
| T08 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 121.19 | 99.66 | 21.52 | 3.23 | 12 | 24.03 | Large in-sample gain; concentration risk. Open P/L is material. |

### 5m BF sensitivity grid

| Profile | TF | Ticker | Loaded window | Total % | Closed % | Open d% | PF | Trades | DD % | View |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| B01 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 3.43 | 2.48 | 0.95 | 1.11 | 63 | 6.73 | Promising, but sample-limited. |
| B01 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -4.35 | -4.00 | -0.34 | 0.87 | 49 | 12.40 | Negative; fails this ticker. |
| B01 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 25.45 | 25.45 | 0.00 | 1.19 | 44 | 38.43 | Positive, but drawdown is excessive. |
| B01 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -0.63 | -0.26 | -0.37 | 0.97 | 41 | 3.19 | Negative; fails this ticker. |
| B01 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 5.28 | 6.25 | -0.97 | 1.13 | 60 | 16.18 | Promising, but sample-limited. |
| B01 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 129.98 | 134.79 | -4.81 | 1.79 | 48 | 28.57 | Large in-sample gain; concentration risk. |
| B02 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 7.13 | 6.11 | 1.02 | 1.50 | 44 | 5.02 | Promising, but sample-limited. |
| B02 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -8.33 | -8.33 | 0.00 | 0.59 | 28 | 11.20 | Negative; fails this ticker. |
| B02 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 3.79 | 3.79 | 0.00 | 1.05 | 28 | 40.37 | Positive, but drawdown is excessive. |
| B02 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -3.10 | -3.10 | 0.00 | 0.60 | 25 | 4.12 | Negative; fails this ticker. |
| B02 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 12.46 | 12.46 | 0.00 | 1.53 | 40 | 8.60 | Strong in-sample; needs a holdout. |
| B02 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 54.15 | 54.15 | 0.00 | 1.57 | 35 | 23.67 | Large in-sample gain; concentration risk. |
| B03 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 5.25 | 4.30 | 0.95 | 1.24 | 43 | 6.77 | Promising, but sample-limited. |
| B03 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 0.47 | 0.20 | 0.27 | 1.01 | 34 | 11.22 | Marginal; no reliable edge shown. |
| B03 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 52.60 | 55.05 | -2.44 | 1.69 | 26 | 34.46 | Large in-sample gain; concentration risk. |
| B03 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.30 | -0.24 | 0.54 | 0.97 | 27 | 3.00 | Positive only with open P/L; endpoint-fragile. |
| B03 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 5.41 | 4.14 | 1.27 | 1.11 | 48 | 14.11 | Promising, but sample-limited. |
| B03 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 118.32 | 99.98 | 18.34 | 1.93 | 34 | 21.94 | Large in-sample gain; concentration risk. Open P/L is material. |
| B04 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 4.56 | 3.61 | 0.95 | 1.25 | 37 | 5.62 | Promising, but sample-limited. |
| B04 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -4.95 | -4.63 | -0.32 | 0.74 | 20 | 8.90 | Negative; fails this ticker. |
| B04 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 0.89 | 0.89 | 0.00 | 1.01 | 20 | 40.71 | Positive, but drawdown is excessive. |
| B04 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -1.83 | -2.36 | 0.53 | 0.73 | 22 | 3.36 | Negative; fails this ticker. |
| B04 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 0.13 | 0.04 | 0.10 | 1.00 | 39 | 12.45 | Marginal; no reliable edge shown. |
| B04 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 78.42 | 68.02 | 10.40 | 1.69 | 29 | 29.93 | Large in-sample gain; concentration risk. Open P/L is material. |
| B05 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 9.42 | 8.40 | 1.02 | 1.58 | 36 | 5.74 | Promising, but sample-limited. |
| B05 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -1.94 | -1.99 | 0.04 | 0.90 | 21 | 10.11 | Negative; fails this ticker. |
| B05 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 73.85 | 50.82 | 23.03 | 1.73 | 19 | 35.10 | Large in-sample gain; concentration risk. Open P/L is material. |
| B05 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -1.60 | -2.13 | 0.53 | 0.80 | 25 | 4.35 | Negative; fails this ticker. |
| B05 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 2.25 | -0.57 | 2.82 | 0.98 | 34 | 16.01 | Positive only with open P/L; endpoint-fragile. Open P/L is material. |
| B05 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 134.20 | 110.80 | 23.41 | 2.29 | 27 | 23.28 | Large in-sample gain; concentration risk. Open P/L is material. |
| B06 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 7.26 | 6.23 | 1.02 | 1.53 | 33 | 5.03 | Promising, but sample-limited. |
| B06 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -0.77 | -0.77 | 0.00 | 0.95 | 17 | 6.62 | Negative; fails this ticker. |
| B06 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 58.60 | 37.56 | 21.04 | 1.79 | 17 | 26.66 | Large in-sample gain; concentration risk. Open P/L is material. |
| B06 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -1.59 | -2.12 | 0.53 | 0.74 | 20 | 3.96 | Negative; fails this ticker. |
| B06 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 11.43 | 8.33 | 3.10 | 1.29 | 31 | 16.21 | Promising, but sample-limited. |
| B06 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 90.16 | 70.66 | 19.51 | 1.77 | 26 | 28.74 | Large in-sample gain; concentration risk. Open P/L is material. |
| B07 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 5.52 | 4.57 | 0.95 | 1.26 | 41 | 6.77 | Promising, but sample-limited. |
| B07 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 0.65 | 0.32 | 0.34 | 1.01 | 31 | 11.38 | Marginal; no reliable edge shown. |
| B07 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 59.20 | 61.69 | -2.49 | 1.77 | 25 | 34.46 | Large in-sample gain; concentration risk. |
| B07 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.09 | -0.45 | 0.54 | 0.95 | 29 | 3.20 | Positive only with open P/L; endpoint-fragile. |
| B07 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 1.62 | 0.38 | 1.24 | 1.01 | 47 | 14.22 | Marginal; no reliable edge shown. |
| B07 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 143.57 | 118.87 | 24.71 | 1.98 | 32 | 26.68 | Large in-sample gain; concentration risk. Open P/L is material. |
| B08 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 5.73 | 4.70 | 1.02 | 1.33 | 37 | 5.62 | Promising, but sample-limited. |
| B08 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -5.74 | -5.74 | 0.01 | 0.70 | 19 | 9.90 | Negative; fails this ticker. |
| B08 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 7.10 | 7.10 | 0.00 | 1.10 | 20 | 39.08 | Positive, but drawdown is excessive. |
| B08 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -0.95 | -1.49 | 0.55 | 0.82 | 22 | 2.97 | Negative; fails this ticker. |
| B08 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 3.97 | 3.87 | 0.10 | 1.13 | 39 | 12.47 | Promising, but sample-limited. |
| B08 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 89.95 | 70.45 | 19.51 | 1.70 | 30 | 29.83 | Large in-sample gain; concentration risk. Open P/L is material. |
| B09 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 7.07 | 6.05 | 1.02 | 1.44 | 36 | 5.74 | Promising, but sample-limited. |
| B09 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -2.09 | -2.13 | 0.04 | 0.90 | 21 | 10.26 | Negative; fails this ticker. |
| B09 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 73.71 | 50.66 | 23.05 | 1.69 | 19 | 35.10 | Large in-sample gain; concentration risk. Open P/L is material. |
| B09 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -0.33 | -0.88 | 0.55 | 0.90 | 25 | 3.35 | Negative; fails this ticker. |
| B09 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 2.07 | -0.75 | 2.82 | 0.98 | 35 | 16.01 | Positive only with open P/L; endpoint-fragile. Open P/L is material. |
| B09 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 136.47 | 111.76 | 24.71 | 2.31 | 27 | 23.09 | Large in-sample gain; concentration risk. Open P/L is material. |
| B10 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 7.78 | 6.76 | 1.02 | 1.61 | 33 | 5.03 | Promising, but sample-limited. |
| B10 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -0.68 | -0.68 | 0.00 | 0.95 | 17 | 6.62 | Negative; fails this ticker. |
| B10 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 58.69 | 37.63 | 21.06 | 1.74 | 17 | 26.91 | Large in-sample gain; concentration risk. Open P/L is material. |
| B10 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -0.84 | -1.39 | 0.55 | 0.79 | 19 | 3.66 | Negative; fails this ticker. |
| B10 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 10.31 | 7.28 | 3.03 | 1.24 | 32 | 16.21 | Promising, but sample-limited. |
| B10 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 90.75 | 71.24 | 19.51 | 1.77 | 26 | 28.86 | Large in-sample gain; concentration risk. Open P/L is material. |
| B11 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.88 | 7.86 | 1.02 | 1.66 | 29 | 5.72 | Promising, but sample-limited. |
| B11 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -0.11 | -0.12 | 0.01 | 0.99 | 19 | 11.70 | Negative; fails this ticker. |
| B11 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 68.06 | 74.94 | -6.88 | 2.11 | 15 | 35.10 | Large in-sample gain; concentration risk. |
| B11 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.58 | 0.02 | 0.55 | 1.00 | 21 | 3.07 | Marginal; no reliable edge shown. |
| B11 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 8.96 | 5.93 | 3.03 | 1.20 | 33 | 16.01 | Promising, but sample-limited. |
| B11 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 164.41 | 137.10 | 27.31 | 4.07 | 20 | 15.57 | Large in-sample gain; concentration risk. Open P/L is material. |
| B12 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 10.43 | 9.41 | 1.02 | 2.07 | 26 | 5.72 | Strong in-sample; needs a holdout. |
| B12 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -4.16 | -3.84 | -0.32 | 0.74 | 17 | 8.15 | Negative; fails this ticker. |
| B12 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 64.59 | 73.75 | -9.17 | 2.70 | 13 | 27.05 | Large in-sample gain; concentration risk. |
| B12 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 1.16 | 0.60 | 0.56 | 1.11 | 17 | 2.31 | Promising, but sample-limited. |
| B12 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 5.12 | 2.23 | 2.89 | 1.08 | 31 | 16.01 | Marginal; no reliable edge shown. Open P/L is material. |
| B12 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 164.89 | 137.58 | 27.31 | 5.25 | 19 | 13.60 | Large in-sample gain; concentration risk. Open P/L is material. |
| B13 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 9.72 | 9.29 | 0.43 | 1.78 | 37 | 5.74 | Promising, but sample-limited. |
| B13 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -3.27 | -3.32 | 0.04 | 0.83 | 22 | 10.31 | Negative; fails this ticker. |
| B13 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 75.27 | 52.03 | 23.24 | 1.74 | 19 | 35.08 | Large in-sample gain; concentration risk. Open P/L is material. |
| B13 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -0.50 | -1.05 | 0.55 | 0.90 | 24 | 4.00 | Negative; fails this ticker. |
| B13 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 2.30 | -0.52 | 2.82 | 0.99 | 34 | 16.01 | Positive only with open P/L; endpoint-fragile. Open P/L is material. |
| B13 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 119.52 | 97.41 | 22.11 | 1.69 | 30 | 32.54 | Large in-sample gain; concentration risk. Open P/L is material. |
| B14 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 6.31 | 6.09 | 0.22 | 1.65 | 34 | 5.02 | Promising, but sample-limited. |
| B14 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -1.34 | -1.34 | 0.00 | 0.91 | 19 | 8.84 | Negative; fails this ticker. |
| B14 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 50.81 | 30.81 | 20.00 | 1.68 | 18 | 26.57 | Large in-sample gain; concentration risk. Open P/L is material. |
| B14 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -2.74 | -3.28 | 0.54 | 0.66 | 19 | 4.42 | Negative; fails this ticker. |
| B14 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 6.87 | 3.91 | 2.96 | 1.13 | 32 | 16.22 | Promising, but sample-limited. |
| B14 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 67.64 | 50.73 | 16.91 | 1.42 | 28 | 30.96 | Large in-sample gain; concentration risk. Open P/L is material. |
| B15 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.95 | 7.93 | 1.02 | 1.66 | 29 | 5.72 | Promising, but sample-limited. |
| B15 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 0.84 | 0.83 | 0.01 | 1.06 | 17 | 10.21 | Marginal; no reliable edge shown. |
| B15 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 67.24 | 74.09 | -6.85 | 2.09 | 14 | 35.43 | Large in-sample gain; concentration risk. |
| B15 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.65 | 0.09 | 0.55 | 1.01 | 22 | 3.07 | Marginal; no reliable edge shown. |
| B15 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 9.15 | 6.11 | 3.03 | 1.21 | 33 | 16.01 | Promising, but sample-limited. |
| B15 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 164.51 | 137.21 | 27.31 | 4.07 | 20 | 15.57 | Large in-sample gain; concentration risk. Open P/L is material. |
| B16 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 10.69 | 9.67 | 1.02 | 2.10 | 26 | 5.72 | Strong in-sample; needs a holdout. |
| B16 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -4.64 | -4.32 | -0.32 | 0.71 | 16 | 9.55 | Negative; fails this ticker. |
| B16 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 64.96 | 74.14 | -9.19 | 2.71 | 12 | 26.76 | Large in-sample gain; concentration risk. |
| B16 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.79 | 0.24 | 0.56 | 1.04 | 18 | 2.31 | Marginal; no reliable edge shown. |
| B16 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 5.19 | 2.30 | 2.89 | 1.08 | 31 | 16.01 | Marginal; no reliable edge shown. Open P/L is material. |
| B16 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 165.01 | 137.70 | 27.31 | 5.25 | 19 | 13.59 | Large in-sample gain; concentration risk. Open P/L is material. |
| B17 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.64 | 7.62 | 1.02 | 1.62 | 26 | 6.68 | Promising, but sample-limited. |
| B17 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 1.03 | 0.69 | 0.34 | 1.04 | 15 | 13.19 | Marginal; no reliable edge shown. |
| B17 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 75.17 | 52.48 | 22.69 | 2.03 | 8 | 28.48 | Large in-sample gain; concentration risk. Sparse sample. |
| B17 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -0.17 | -0.72 | 0.55 | 0.88 | 18 | 2.88 | Negative; fails this ticker. |
| B17 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 8.87 | 5.84 | 3.03 | 1.16 | 33 | 16.16 | Promising, but sample-limited. |
| B17 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 141.59 | 161.30 | -19.71 | 5.29 | 20 | 14.01 | Large in-sample gain; concentration risk. Open P/L is material. |
| B18 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 9.80 | 8.78 | 1.02 | 1.82 | 25 | 4.18 | Promising, but sample-limited. |
| B18 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 4.34 | 3.98 | 0.35 | 1.30 | 13 | 8.15 | Promising, but sample-limited. |
| B18 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 69.32 | 47.38 | 21.95 | 1.95 | 8 | 28.48 | Large in-sample gain; concentration risk. Sparse sample. |
| B18 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -0.15 | -0.70 | 0.55 | 0.89 | 17 | 2.70 | Negative; fails this ticker. |
| B18 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 16.04 | 12.81 | 3.24 | 1.49 | 29 | 12.02 | Strong in-sample; needs a holdout. |
| B18 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 122.90 | 141.20 | -18.30 | 4.54 | 20 | 16.93 | Large in-sample gain; concentration risk. Open P/L is material. |

### 5m regime, governor, and direction control without BF

| Profile | TF | Ticker | Loaded window | Total % | Closed % | Open d% | PF | Trades | DD % | View |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| R01 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 9.11 | 8.09 | 1.02 | 2.08 | 22 | 5.72 | Promising, but sample-limited. |
| R01 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 1.10 | 0.64 | 0.46 | 1.07 | 12 | 10.13 | Marginal; no reliable edge shown. |
| R01 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 75.69 | 52.88 | 22.81 | 2.15 | 6 | 28.48 | Large in-sample gain; concentration risk. Sparse sample. |
| R01 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.82 | 0.25 | 0.57 | 1.05 | 15 | 2.64 | Marginal; no reliable edge shown. |
| R01 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 7.56 | 4.60 | 2.96 | 1.17 | 27 | 16.01 | Promising, but sample-limited. |
| R01 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 152.49 | 126.48 | 26.01 | 4.91 | 14 | 14.13 | Large in-sample gain; concentration risk. Open P/L is material. |
| R02 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.82 | 7.89 | 0.93 | 2.42 | 15 | 4.48 | Promising, but sample-limited. |
| R02 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -2.86 | -3.31 | 0.45 | 0.05 | 7 | 4.99 | Negative; fails this ticker. Sparse sample. |
| R02 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 82.64 | 82.64 | 0.00 | 4.96 | 4 | 14.57 | Large in-sample gain; concentration risk. Too sparse to infer. |
| R02 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 2.89 | 2.30 | 0.58 | 1.97 | 8 | 2.07 | Promising, but sample-limited. Sparse sample. |
| R02 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 16.76 | 13.52 | 3.24 | 2.23 | 16 | 6.40 | Strong in-sample; needs a holdout. |
| R02 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 141.91 | 141.91 | 0.00 | 8.84 | 8 | 11.63 | Large in-sample gain; concentration risk. Sparse sample. |
| R03 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | -1.11 | -1.11 | 0.00 | 0.67 | 14 | 2.65 | Negative; fails this ticker. |
| R03 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 2.43 | 2.43 | 0.00 | 1.29 | 7 | 5.80 | Promising, but sample-limited. Sparse sample. |
| R03 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | -1.17 | -14.32 | 13.16 | 0.00 | 3 | 14.52 | Negative; fails this ticker. Too sparse to infer. |
| R03 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -0.95 | -0.95 | 0.00 | 0.48 | 8 | 1.71 | Negative; fails this ticker. Sparse sample. |
| R03 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | -5.84 | -5.84 | 0.00 | 0.62 | 16 | 15.65 | Negative; fails this ticker. |
| R03 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | -10.53 | -19.77 | 9.24 | 0.26 | 8 | 23.48 | Negative; fails this ticker. Sparse sample. |
| R04 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.30 | 7.28 | 1.02 | 1.88 | 24 | 6.00 | Promising, but sample-limited. |
| R04 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 1.10 | 0.64 | 0.46 | 1.07 | 12 | 10.13 | Marginal; no reliable edge shown. |
| R04 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 75.71 | 52.88 | 22.83 | 2.15 | 6 | 28.48 | Large in-sample gain; concentration risk. Sparse sample. |
| R04 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.88 | 0.32 | 0.56 | 1.06 | 15 | 2.57 | Marginal; no reliable edge shown. |
| R04 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 7.69 | 4.73 | 2.96 | 1.18 | 27 | 16.01 | Promising, but sample-limited. |
| R04 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 153.03 | 127.02 | 26.01 | 5.00 | 14 | 13.59 | Large in-sample gain; concentration risk. Open P/L is material. |
| R05 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.82 | 7.89 | 0.93 | 2.42 | 15 | 4.48 | Promising, but sample-limited. |
| R05 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -2.86 | -3.31 | 0.45 | 0.05 | 7 | 4.99 | Negative; fails this ticker. Sparse sample. |
| R05 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 82.64 | 82.64 | 0.00 | 4.96 | 4 | 14.57 | Large in-sample gain; concentration risk. Too sparse to infer. |
| R05 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 2.96 | 2.38 | 0.57 | 2.04 | 8 | 2.00 | Promising, but sample-limited. Sparse sample. |
| R05 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 16.76 | 13.52 | 3.24 | 2.23 | 16 | 6.40 | Strong in-sample; needs a holdout. |
| R05 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 142.25 | 142.25 | 0.00 | 9.01 | 8 | 11.62 | Large in-sample gain; concentration risk. Sparse sample. |
| R06 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | -1.11 | -1.11 | 0.00 | 0.67 | 14 | 2.65 | Negative; fails this ticker. |
| R06 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 2.43 | 2.43 | 0.00 | 1.29 | 7 | 5.80 | Promising, but sample-limited. Sparse sample. |
| R06 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | -1.17 | -14.32 | 13.16 | 0.00 | 3 | 14.52 | Negative; fails this ticker. Too sparse to infer. |
| R06 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -0.95 | -0.95 | 0.00 | 0.48 | 8 | 1.71 | Negative; fails this ticker. Sparse sample. |
| R06 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | -5.84 | -5.84 | 0.00 | 0.62 | 16 | 15.65 | Negative; fails this ticker. |
| R06 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | -10.53 | -19.77 | 9.24 | 0.26 | 8 | 23.48 | Negative; fails this ticker. Sparse sample. |
| R07 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 9.11 | 8.09 | 1.02 | 2.08 | 22 | 5.72 | Promising, but sample-limited. |
| R07 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 1.10 | 0.64 | 0.46 | 1.07 | 12 | 10.13 | Marginal; no reliable edge shown. |
| R07 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 75.71 | 52.88 | 22.83 | 2.15 | 6 | 28.48 | Large in-sample gain; concentration risk. Sparse sample. |
| R07 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.80 | 0.25 | 0.55 | 1.05 | 15 | 2.64 | Marginal; no reliable edge shown. |
| R07 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 7.56 | 4.60 | 2.96 | 1.17 | 27 | 16.01 | Promising, but sample-limited. |
| R07 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 152.49 | 126.48 | 26.01 | 4.91 | 14 | 14.13 | Large in-sample gain; concentration risk. Open P/L is material. |
| R08 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.82 | 7.89 | 0.93 | 2.42 | 15 | 4.48 | Promising, but sample-limited. |
| R08 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -2.86 | -3.31 | 0.45 | 0.05 | 7 | 4.99 | Negative; fails this ticker. Sparse sample. |
| R08 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 82.64 | 82.64 | 0.00 | 4.96 | 4 | 14.57 | Large in-sample gain; concentration risk. Too sparse to infer. |
| R08 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 2.87 | 2.30 | 0.57 | 1.97 | 8 | 2.07 | Promising, but sample-limited. Sparse sample. |
| R08 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 16.76 | 13.52 | 3.24 | 2.23 | 16 | 6.40 | Strong in-sample; needs a holdout. |
| R08 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 141.91 | 141.91 | 0.00 | 8.84 | 8 | 11.63 | Large in-sample gain; concentration risk. Sparse sample. |
| R09 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | -1.11 | -1.11 | 0.00 | 0.67 | 14 | 2.65 | Negative; fails this ticker. |
| R09 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 2.43 | 2.43 | 0.00 | 1.29 | 7 | 5.80 | Promising, but sample-limited. Sparse sample. |
| R09 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | -1.17 | -14.32 | 13.16 | 0.00 | 3 | 14.52 | Negative; fails this ticker. Too sparse to infer. |
| R09 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -0.95 | -0.95 | 0.00 | 0.48 | 8 | 1.71 | Negative; fails this ticker. Sparse sample. |
| R09 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | -5.84 | -5.84 | 0.00 | 0.62 | 16 | 15.65 | Negative; fails this ticker. |
| R09 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | -10.53 | -19.77 | 9.24 | 0.26 | 8 | 23.48 | Negative; fails this ticker. Sparse sample. |
| R10 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.30 | 7.28 | 1.02 | 1.88 | 24 | 6.00 | Promising, but sample-limited. |
| R10 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 1.10 | 0.64 | 0.46 | 1.07 | 12 | 10.13 | Marginal; no reliable edge shown. |
| R10 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 75.71 | 52.88 | 22.83 | 2.15 | 6 | 28.48 | Large in-sample gain; concentration risk. Sparse sample. |
| R10 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.88 | 0.32 | 0.55 | 1.06 | 15 | 2.57 | Marginal; no reliable edge shown. |
| R10 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 7.69 | 4.73 | 2.96 | 1.18 | 27 | 16.01 | Promising, but sample-limited. |
| R10 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 153.03 | 127.02 | 26.01 | 5.00 | 14 | 13.59 | Large in-sample gain; concentration risk. Open P/L is material. |
| R11 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.82 | 7.89 | 0.93 | 2.42 | 15 | 4.48 | Promising, but sample-limited. |
| R11 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -2.86 | -3.31 | 0.45 | 0.05 | 7 | 4.99 | Negative; fails this ticker. Sparse sample. |
| R11 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 82.64 | 82.64 | 0.00 | 4.96 | 4 | 14.57 | Large in-sample gain; concentration risk. Too sparse to infer. |
| R11 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 2.95 | 2.38 | 0.57 | 2.04 | 8 | 2.00 | Promising, but sample-limited. Sparse sample. |
| R11 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 16.76 | 13.52 | 3.24 | 2.23 | 16 | 6.40 | Strong in-sample; needs a holdout. |
| R11 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 142.25 | 142.25 | 0.00 | 9.01 | 8 | 11.62 | Large in-sample gain; concentration risk. Sparse sample. |
| R12 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | -1.11 | -1.11 | 0.00 | 0.67 | 14 | 2.65 | Negative; fails this ticker. |
| R12 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 2.43 | 2.43 | 0.00 | 1.29 | 7 | 5.80 | Promising, but sample-limited. Sparse sample. |
| R12 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | -1.17 | -14.32 | 13.16 | 0.00 | 3 | 14.52 | Negative; fails this ticker. Too sparse to infer. |
| R12 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -0.95 | -0.95 | 0.00 | 0.48 | 8 | 1.71 | Negative; fails this ticker. Sparse sample. |
| R12 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | -5.84 | -5.84 | 0.00 | 0.62 | 16 | 15.65 | Negative; fails this ticker. |
| R12 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | -10.53 | -19.77 | 9.24 | 0.26 | 8 | 23.48 | Negative; fails this ticker. Sparse sample. |

### 5m regime, governor, and direction grid with BF60/10 recycle

| Profile | TF | Ticker | Loaded window | Total % | Closed % | Open d% | PF | Trades | DD % | View |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| R01 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.95 | 7.93 | 1.02 | 1.66 | 29 | 5.72 | Promising, but sample-limited. |
| R01 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 0.88 | 0.83 | 0.04 | 1.06 | 17 | 10.21 | Marginal; no reliable edge shown. |
| R01 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 67.41 | 74.09 | -6.68 | 2.09 | 14 | 35.43 | Large in-sample gain; concentration risk. |
| R01 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.65 | 0.09 | 0.56 | 1.01 | 22 | 3.07 | Marginal; no reliable edge shown. |
| R01 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 9.15 | 6.11 | 3.03 | 1.21 | 33 | 16.01 | Promising, but sample-limited. |
| R01 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 164.51 | 137.21 | 27.31 | 4.07 | 20 | 15.57 | Large in-sample gain; concentration risk. Open P/L is material. |
| R02 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.87 | 7.95 | 0.93 | 2.11 | 20 | 4.48 | Promising, but sample-limited. |
| R02 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -3.41 | -3.45 | 0.04 | 0.51 | 9 | 5.07 | Negative; fails this ticker. Sparse sample. |
| R02 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 81.37 | 81.37 | 0.00 | 4.44 | 9 | 14.57 | Large in-sample gain; concentration risk. Sparse sample. |
| R02 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 2.86 | 2.29 | 0.57 | 1.81 | 12 | 2.50 | Promising, but sample-limited. |
| R02 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 16.20 | 12.96 | 3.24 | 2.02 | 19 | 6.40 | Strong in-sample; needs a holdout. |
| R02 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 155.26 | 155.26 | 0.00 | 5.93 | 14 | 16.51 | Large in-sample gain; concentration risk. |
| R03 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | -1.17 | -1.17 | 0.00 | 0.81 | 16 | 3.00 | Negative; fails this ticker. |
| R03 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 5.89 | 5.89 | 0.00 | 1.95 | 11 | 5.65 | Promising, but sample-limited. |
| R03 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | -5.81 | -2.05 | -3.76 | 0.93 | 6 | 23.20 | Negative; fails this ticker. Sparse sample. |
| R03 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -1.15 | -1.15 | 0.00 | 0.73 | 12 | 2.75 | Negative; fails this ticker. |
| R03 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | -4.14 | -4.14 | 0.00 | 0.75 | 19 | 15.95 | Negative; fails this ticker. |
| R03 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | -10.53 | -19.77 | 9.24 | 0.26 | 8 | 23.48 | Negative; fails this ticker. Sparse sample. |
| R04 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.15 | 7.12 | 1.02 | 1.55 | 31 | 6.00 | Promising, but sample-limited. |
| R04 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 1.21 | 0.83 | 0.38 | 1.06 | 17 | 10.21 | Marginal; no reliable edge shown. |
| R04 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 67.41 | 74.09 | -6.68 | 2.09 | 14 | 35.43 | Large in-sample gain; concentration risk. |
| R04 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.72 | 0.17 | 0.56 | 1.02 | 22 | 3.00 | Marginal; no reliable edge shown. |
| R04 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 9.28 | 6.25 | 3.03 | 1.21 | 33 | 16.01 | Promising, but sample-limited. |
| R04 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 165.05 | 137.75 | 27.31 | 4.12 | 20 | 15.49 | Large in-sample gain; concentration risk. Open P/L is material. |
| R05 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.87 | 7.95 | 0.93 | 2.11 | 20 | 4.48 | Promising, but sample-limited. |
| R05 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -3.07 | -3.45 | 0.39 | 0.51 | 9 | 5.07 | Negative; fails this ticker. Sparse sample. |
| R05 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 81.37 | 81.37 | 0.00 | 4.44 | 9 | 14.57 | Large in-sample gain; concentration risk. Sparse sample. |
| R05 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 2.94 | 2.37 | 0.57 | 1.86 | 12 | 2.43 | Promising, but sample-limited. |
| R05 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 16.20 | 12.96 | 3.24 | 2.02 | 19 | 6.40 | Strong in-sample; needs a holdout. |
| R05 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 159.77 | 159.77 | 0.00 | 6.06 | 14 | 16.46 | Large in-sample gain; concentration risk. |
| R06 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | -1.17 | -1.17 | 0.00 | 0.81 | 16 | 3.00 | Negative; fails this ticker. |
| R06 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 5.89 | 5.89 | 0.00 | 1.95 | 11 | 5.65 | Promising, but sample-limited. |
| R06 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | -5.81 | -2.05 | -3.76 | 0.93 | 6 | 23.20 | Negative; fails this ticker. Sparse sample. |
| R06 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -1.15 | -1.15 | 0.00 | 0.73 | 12 | 2.75 | Negative; fails this ticker. |
| R06 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | -4.14 | -4.14 | 0.00 | 0.75 | 19 | 15.95 | Negative; fails this ticker. |
| R06 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | -10.53 | -19.77 | 9.24 | 0.26 | 8 | 23.48 | Negative; fails this ticker. Sparse sample. |
| R07 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.95 | 7.93 | 1.02 | 1.66 | 29 | 5.72 | Promising, but sample-limited. |
| R07 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 0.90 | 0.83 | 0.07 | 1.06 | 17 | 10.21 | Marginal; no reliable edge shown. |
| R07 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 67.41 | 74.09 | -6.68 | 2.09 | 14 | 35.43 | Large in-sample gain; concentration risk. |
| R07 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.65 | 0.09 | 0.55 | 1.01 | 22 | 3.07 | Marginal; no reliable edge shown. |
| R07 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 9.15 | 6.11 | 3.03 | 1.21 | 33 | 16.01 | Promising, but sample-limited. |
| R07 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 164.51 | 137.21 | 27.31 | 4.07 | 20 | 15.57 | Large in-sample gain; concentration risk. Open P/L is material. |
| R08 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.87 | 7.95 | 0.93 | 2.11 | 20 | 4.48 | Promising, but sample-limited. |
| R08 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -3.39 | -3.45 | 0.07 | 0.51 | 9 | 5.07 | Negative; fails this ticker. Sparse sample. |
| R08 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 81.37 | 81.37 | 0.00 | 4.44 | 9 | 14.57 | Large in-sample gain; concentration risk. Sparse sample. |
| R08 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 2.86 | 2.29 | 0.57 | 1.81 | 12 | 2.50 | Promising, but sample-limited. |
| R08 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 16.20 | 12.96 | 3.24 | 2.02 | 19 | 6.40 | Strong in-sample; needs a holdout. |
| R08 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 155.26 | 155.26 | 0.00 | 5.93 | 14 | 16.51 | Large in-sample gain; concentration risk. |
| R09 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | -1.17 | -1.17 | 0.00 | 0.81 | 16 | 3.00 | Negative; fails this ticker. |
| R09 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 5.89 | 5.89 | 0.00 | 1.95 | 11 | 5.65 | Promising, but sample-limited. |
| R09 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | -5.81 | -2.05 | -3.76 | 0.93 | 6 | 23.20 | Negative; fails this ticker. Sparse sample. |
| R09 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -1.15 | -1.15 | 0.00 | 0.73 | 12 | 2.75 | Negative; fails this ticker. |
| R09 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | -4.14 | -4.14 | 0.00 | 0.75 | 19 | 15.95 | Negative; fails this ticker. |
| R09 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | -10.53 | -19.77 | 9.24 | 0.26 | 8 | 23.48 | Negative; fails this ticker. Sparse sample. |
| R10 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.15 | 7.12 | 1.02 | 1.55 | 31 | 6.00 | Promising, but sample-limited. |
| R10 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 1.23 | 0.83 | 0.40 | 1.06 | 17 | 10.21 | Marginal; no reliable edge shown. |
| R10 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 67.41 | 74.09 | -6.68 | 2.09 | 14 | 35.43 | Large in-sample gain; concentration risk. |
| R10 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 0.72 | 0.17 | 0.56 | 1.02 | 22 | 3.00 | Marginal; no reliable edge shown. |
| R10 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 9.28 | 6.25 | 3.03 | 1.21 | 33 | 16.01 | Promising, but sample-limited. |
| R10 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 165.05 | 137.75 | 27.31 | 4.12 | 20 | 15.49 | Large in-sample gain; concentration risk. Open P/L is material. |
| R11 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | 8.87 | 7.95 | 0.93 | 2.11 | 20 | 4.48 | Promising, but sample-limited. |
| R11 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | -3.07 | -3.45 | 0.39 | 0.51 | 9 | 5.07 | Negative; fails this ticker. Sparse sample. |
| R11 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | 81.37 | 81.37 | 0.00 | 4.44 | 9 | 14.57 | Large in-sample gain; concentration risk. Sparse sample. |
| R11 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | 2.94 | 2.37 | 0.57 | 1.86 | 12 | 2.43 | Promising, but sample-limited. |
| R11 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | 16.20 | 12.96 | 3.24 | 2.02 | 19 | 6.40 | Strong in-sample; needs a holdout. |
| R11 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | 159.77 | 159.77 | 0.00 | 6.06 | 14 | 16.46 | Large in-sample gain; concentration risk. |
| R12 | 5m | AMEX:SPY | 2026-02-09..2026-07-10 | -1.17 | -1.17 | 0.00 | 0.81 | 16 | 3.00 | Negative; fails this ticker. |
| R12 | 5m | HIP3XYZ:AMZNUSDC.P | 2026-04-20..2026-07-12 | 5.89 | 5.89 | 0.00 | 1.95 | 11 | 5.65 | Promising, but sample-limited. |
| R12 | 5m | HIP3XYZ:MUUSDC.P | 2026-04-27..2026-07-12 | -5.81 | -2.05 | -3.76 | 0.93 | 6 | 23.20 | Negative; fails this ticker. Sparse sample. |
| R12 | 5m | HIP3XYZ:SP500USDC.P | 2026-04-27..2026-07-12 | -1.15 | -1.15 | 0.00 | 0.73 | 12 | 2.75 | Negative; fails this ticker. |
| R12 | 5m | NASDAQ:AMZN | 2026-02-02..2026-07-10 | -4.14 | -4.14 | 0.00 | 0.75 | 19 | 15.95 | Negative; fails this ticker. |
| R12 | 5m | NASDAQ:MU | 2026-02-09..2026-07-10 | -10.53 | -19.77 | 9.24 | 0.26 | 8 | 23.48 | Negative; fails this ticker. Sparse sample. |

### 15m calendar-window extension

| Profile | TF | Ticker | Loaded window | Total % | Closed % | Open d% | PF | Trades | DD % | View |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| B15 | 15m | AMEX:SPY | 2025-04-01..2026-07-10 | 6.77 | 5.79 | 0.98 | 1.14 | 96 | 16.13 | Promising, but sample-limited. |
| B15 | 15m | HIP3XYZ:AMZNUSDC.P | 2025-12-01..2026-07-12 | 5.60 | 5.46 | 0.15 | 1.09 | 58 | 21.10 | Marginal; no reliable edge shown. |
| B15 | 15m | HIP3XYZ:CLUSDC.P | 2026-01-06..2026-07-12 | -4.92 | -8.81 | 3.88 | 0.88 | 39 | 33.28 | Negative; fails this ticker. Open P/L is material. |
| B15 | 15m | HIP3XYZ:MUUSDC.P | 2025-12-19..2026-07-12 | 139.96 | 149.62 | -9.65 | 1.93 | 42 | 34.67 | Large in-sample gain; concentration risk. |
| B15 | 15m | HIP3XYZ:SP500USDC.P | 2026-03-18..2026-07-12 | 10.08 | 9.48 | 0.59 | 2.04 | 29 | 3.33 | Strong in-sample; needs a holdout. |
| B15 | 15m | HIP3XYZ:SPCXUSDC.P | 2026-05-17..2026-07-12 | -29.50 | -33.87 | 4.37 | 0.34 | 11 | 40.77 | Reject: material loss. |
| B15 | 15m | HIP3XYZ:XYZ100USDC.P | 2025-12-01..2026-07-12 | -7.96 | -6.64 | -1.32 | 0.88 | 68 | 24.42 | Negative; fails this ticker. |
| B15 | 15m | NASDAQ:AMZN | 2025-04-01..2026-07-10 | -8.10 | -10.63 | 2.53 | 0.89 | 100 | 27.48 | Negative; fails this ticker. |
| B15 | 15m | NASDAQ:MU | 2025-04-01..2026-07-10 | 697.95 | 618.90 | 79.05 | 2.49 | 78 | 33.24 | Outlier gain; path and compounding dominated. Open P/L is material. |
| B15 | 15m | NASDAQ:QQQ | 2025-04-01..2026-07-10 | 4.86 | 6.79 | -1.92 | 1.13 | 86 | 17.15 | Promising, but sample-limited. |
| N00 | 15m | AMEX:SPY | 2025-04-01..2026-07-10 | 6.00 | 5.03 | 0.98 | 1.17 | 76 | 17.08 | Promising, but sample-limited. |
| N00 | 15m | HIP3XYZ:AMZNUSDC.P | 2025-12-01..2026-07-12 | -0.29 | -0.69 | 0.40 | 0.98 | 41 | 22.09 | Negative; fails this ticker. |
| N00 | 15m | HIP3XYZ:CLUSDC.P | 2026-01-06..2026-07-12 | 0.52 | -3.60 | 4.11 | 0.94 | 28 | 31.49 | Positive only with open P/L; endpoint-fragile. Open P/L is material. |
| N00 | 15m | HIP3XYZ:MUUSDC.P | 2025-12-19..2026-07-12 | 155.85 | 122.35 | 33.50 | 2.05 | 26 | 34.30 | Large in-sample gain; concentration risk. Open P/L is material. |
| N00 | 15m | HIP3XYZ:SP500USDC.P | 2026-03-18..2026-07-12 | 10.42 | 9.83 | 0.59 | 3.07 | 16 | 2.69 | Strong in-sample; needs a holdout. |
| N00 | 15m | HIP3XYZ:SPCXUSDC.P | 2026-05-17..2026-07-12 | -24.61 | -29.28 | 4.67 | 0.02 | 9 | 34.35 | Reject: material loss. Sparse sample. |
| N00 | 15m | HIP3XYZ:XYZ100USDC.P | 2025-12-01..2026-07-12 | -7.79 | -8.51 | 0.73 | 0.72 | 41 | 22.27 | Negative; fails this ticker. |
| N00 | 15m | NASDAQ:AMZN | 2025-04-01..2026-07-10 | -7.91 | -10.44 | 2.53 | 0.86 | 74 | 26.26 | Negative; fails this ticker. |
| N00 | 15m | NASDAQ:MU | 2025-04-01..2026-07-10 | 695.57 | 616.52 | 79.05 | 3.09 | 52 | 29.40 | Outlier gain; path and compounding dominated. Open P/L is material. |
| N00 | 15m | NASDAQ:QQQ | 2025-04-01..2026-07-10 | 8.84 | 10.90 | -2.06 | 1.26 | 71 | 14.90 | Promising, but sample-limited. |

### 30m long-window equity stress test

| Profile | TF | Ticker | Loaded window | Total % | Closed % | Open d% | PF | Trades | DD % | View |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| B15 | 30m | AMEX:SPY | 2024-01-02..2026-07-10 | 4.08 | 3.18 | 0.91 | 1.04 | 153 | 18.06 | Marginal; no reliable edge shown. Churn and cost-sensitive. |
| B15 | 30m | NASDAQ:AMZN | 2024-01-02..2026-07-10 | -48.65 | -50.00 | 1.35 | 0.69 | 184 | 60.45 | Reject: severe loss or drawdown. Churn and cost-sensitive. |
| B15 | 30m | NASDAQ:MU | 2024-01-02..2026-07-10 | 487.76 | 426.59 | 61.17 | 2.07 | 141 | 55.06 | Reject: severe loss or drawdown. Open P/L is material. |
| B15 | 30m | NASDAQ:QQQ | 2024-01-02..2026-07-10 | -4.31 | -2.29 | -2.02 | 0.98 | 156 | 26.68 | Negative; fails this ticker. Churn and cost-sensitive. |
| N00 | 30m | AMEX:SPY | 2024-01-02..2026-07-10 | 6.97 | 5.99 | 0.98 | 1.11 | 115 | 17.39 | Promising, but sample-limited. |
| N00 | 30m | NASDAQ:AMZN | 2024-01-02..2026-07-10 | -45.71 | -47.20 | 1.48 | 0.60 | 137 | 57.78 | Reject: severe loss or drawdown. |
| N00 | 30m | NASDAQ:MU | 2024-01-02..2026-07-10 | 759.69 | 669.89 | 89.80 | 3.15 | 90 | 29.40 | Outlier gain; path and compounding dominated. Open P/L is material. |
| N00 | 30m | NASDAQ:QQQ | 2024-01-02..2026-07-10 | -16.50 | -14.63 | -1.86 | 0.81 | 121 | 30.46 | Reject: material loss. |

## Integrity notes

- The sweep used only the separately copied script TVB-EXP BF Sweep [GPT].
- Every accepted cell matched a unique run tag, requested ticker, chart timeframe, and full parameter string before it was stored.
- The result store contains 448 structured rows represented above, plus two excluded collector canaries.
- No result from another experiment session was used for parameter selection or analysis.
- The live chart's final bar changed during collection. Loaded-window dates and open P/L are snapshots, not immutable future results.
