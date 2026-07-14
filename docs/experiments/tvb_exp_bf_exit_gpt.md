# TVB-EXP-BF1/E2 BF-Deviation Exit Ablation v2 - Independent Replication

Date run: 2026-07-11 America/New_York (market timestamps reported in UTC)

Status: exploratory research only. This report characterizes the continuity-plus-BF-exit skeleton. It is not a deployment recommendation.

## Method and integrity checks

- TradingView Desktop was used in place. It was not restarted or relaunched. CDP remained connected on port 9222.
- The strategy was created with the required Pine editor `Make a copy` flow. The saved-script count rose from 14 to 15 and produced a new saved ID for `TVB-EXP BF Exit [GPT]`. After every save, only that script's modified timestamp changed.
- The script compiled without errors and remained separate from `TVB-EXP BF Exit [Claude]`, `TFC Baseline`, the Companion script, and both BF indicators.
- The pre-registered core is exactly 5 symbols x 6 cells = 30 runs. Every C1/C2/C3 group had the same first-entry timestamp for its symbol.
- Symbol switches received at least 15 seconds to load. Every input change received at least 10 seconds before collection. The script echoed the active symbol and all four cell inputs into its machine-readable output, and each run was rejected unless both matched.
- The execution gate uses local current-period-open reconstruction for 60/120/240/D/W/M. It makes no `request.security` call. The only `request.security` call is the BF-1 pivot stream, using completed values `[1]` with `lookahead_on` exactly as allowed by the pre-registration.
- BF pivot dots are not signals. Only projected BF lines place exits. Longs use the projected upper line for the next 5m bar; shorts use the projected lower line.
- Fixed costs and properties: initial capital 10,000 USDC; 100% equity per trade; 0.0125% commission per side; 1 tick slippage; margin long/short 0; bar magnifier accepted and enabled.
- The loss governor classifies wins and losses gross of commission, using slippage-adjusted entry and exit prices. A final audit found three marginal trades where Pine's net `closedtrades.profit()` straddled zero after commission; the governor was corrected to explicit gross P/L and those three cells were rerun. Closed-trade sequences were unchanged.
- Blindness exception: after the independent GPT implementation was already written and compiled, one initial generic Strategy Tester read selected the first strategy data source on the chart and exposed one Claude result set. It was identified because it contradicted the GPT cell echo, rejected immediately, and never entered this dataset or the analysis. Claude's Pine source and report file were never opened.

## Pre-registered cell matrix

| Cell | BF exit | BF re-entry | Arm TF | Exit TF |
|---|---|---|---:|---:|
| C1 | off | not applicable | 15 | 15 |
| C2 | same_side | recycle | 15 | 15 |
| C3 | same_side | ratchet | 15 | 15 |
| C4 | off | not applicable | 5 | 15 |
| C5 | same_side | ratchet | 5 | 15 |
| C6 | same_side | ratchet | 5 | 30 |

## Loaded history windows

The Strategy Tester uses the history TradingView loaded for each 5m chart. The representative C1 loaded windows were:

| Symbol | Loaded first bar UTC | Loaded last bar UTC | Bars |
|---|---|---|---:|
| AMZN | 2026-04-20 00:00 | 2026-07-12 00:05 | 21845 |
| XYZ100 | 2026-04-27 00:00 | 2026-07-12 00:05 | 21878 |
| MU | 2026-04-27 00:00 | 2026-07-12 00:10 | 21831 |
| SPCX | 2026-05-17 22:30 | 2026-07-12 00:10 | 15857 |
| CL | 2026-04-27 00:00 | 2026-07-12 00:10 | 21867 |

The per-run `Bars` column below is the exact count captured with that result. Counts can differ by a few bars because the market remained live while runs were collected.

## Core results - 30 pre-registered runs

`Closed net` is TradingView `strategy.netprofit`. TradingView books paid entry commission immediately, so when a trade remains open this value can include its entry commission. `Total net` is `strategy.netprofit + strategy.openprofit`. Long and short net include the paid entry commission for an open trade and reconcile to closed net. All currency values are USDC.

| Symbol | Cell | Closed net | Closed % | Open P/L | Total net | Total % | PF | Trades | Win % | Max DD % | Comm. | Long net | Short net | First entry UTC | Last event UTC | Bars |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|
| AMZN | C1 | 63.96 | 0.64 | 68.53 | 132.49 | 1.32 | 1.07 | 12 | 16.7 | 10.1 | 30.07 | -472.08 | 536.04 | 2026-05-01 00:05 | 2026-07-09 18:30 | 21845 |
| AMZN | C2 | -213.40 | -2.13 | 38.59 | -174.82 | -1.75 | 0.90 | 21 | 38.1 | 10.3 | 52.04 | -303.02 | 89.62 | 2026-05-01 00:05 | 2026-07-11 00:45 | 21845 |
| AMZN | C3 | -68.47 | -0.68 | 0.00 | -68.47 | -0.68 | 0.95 | 17 | 41.2 | 6.6 | 41.88 | -78.46 | 9.99 | 2026-05-01 00:05 | 2026-07-10 13:30 | 21849 |
| AMZN | C4 | 68.52 | 0.69 | 68.15 | 136.67 | 1.37 | 1.07 | 12 | 16.7 | 10.1 | 30.07 | -468.74 | 537.26 | 2026-05-01 00:05 | 2026-07-09 18:30 | 21845 |
| AMZN | C5 | 104.62 | 1.05 | 0.00 | 104.62 | 1.05 | 1.07 | 16 | 43.8 | 6.1 | 39.55 | -155.26 | 259.88 | 2026-05-01 00:05 | 2026-07-10 13:30 | 21845 |
| AMZN | C6 | 555.72 | 5.56 | 0.00 | 555.72 | 5.56 | 1.52 | 14 | 50.0 | 5.9 | 34.83 | 311.39 | 244.33 | 2026-05-01 00:05 | 2026-07-10 13:30 | 21845 |
| XYZ100 | C1 | 183.91 | 1.84 | 69.62 | 253.53 | 2.54 | 1.23 | 16 | 6.3 | 8.0 | 44.28 | 507.89 | -323.99 | 2026-05-04 00:05 | 2026-06-23 03:20 | 21878 |
| XYZ100 | C2 | 311.05 | 3.11 | -257.36 | 53.69 | 0.54 | 1.20 | 28 | 42.9 | 11.2 | 75.49 | 431.73 | -120.67 | 2026-05-04 00:05 | 2026-07-07 14:15 | 21878 |
| XYZ100 | C3 | -33.15 | -0.33 | -276.46 | -309.61 | -3.10 | 0.98 | 24 | 41.7 | 12.3 | 63.64 | 281.68 | -314.82 | 2026-05-04 00:05 | 2026-07-07 14:35 | 21878 |
| XYZ100 | C4 | 225.18 | 2.25 | 70.03 | 295.21 | 2.95 | 1.30 | 16 | 6.3 | 7.7 | 44.37 | 523.92 | -298.74 | 2026-05-04 00:05 | 2026-06-23 03:20 | 21878 |
| XYZ100 | C5 | -377.05 | -3.77 | 0.00 | -377.05 | -3.77 | 0.76 | 22 | 31.8 | 14.1 | 56.71 | 123.81 | -500.86 | 2026-05-04 00:05 | 2026-07-07 05:15 | 21878 |
| XYZ100 | C6 | -389.74 | -3.90 | 0.00 | -389.74 | -3.90 | 0.75 | 20 | 35.0 | 14.1 | 51.43 | 126.25 | -515.99 | 2026-05-04 00:05 | 2026-07-07 05:15 | 21878 |
| MU | C1 | 5287.79 | 52.88 | 2262.17 | 7549.95 | 75.50 | 2.15 | 6 | 33.3 | 28.5 | 26.00 | 7722.93 | -2435.15 | 2026-05-04 00:05 | 2026-07-01 00:20 | 21831 |
| MU | C2 | 5065.60 | 50.66 | 2292.06 | 7357.66 | 73.58 | 1.69 | 19 | 68.4 | 35.1 | 73.86 | 7719.30 | -2653.70 | 2026-05-04 00:05 | 2026-07-01 00:10 | 21831 |
| MU | C3 | 3762.72 | 37.63 | 2092.81 | 5855.54 | 58.56 | 1.74 | 17 | 64.7 | 26.9 | 58.60 | 4666.72 | -903.99 | 2026-05-04 00:05 | 2026-07-01 00:10 | 21831 |
| MU | C4 | 4836.81 | 48.37 | 2193.46 | 7030.27 | 70.30 | 1.97 | 7 | 28.6 | 30.6 | 29.84 | 7464.90 | -2628.09 | 2026-05-04 00:05 | 2026-07-01 00:20 | 21831 |
| MU | C5 | 4067.53 | 40.68 | 2139.37 | 6206.90 | 62.07 | 1.95 | 17 | 70.6 | 24.6 | 58.61 | 4810.79 | -743.26 | 2026-05-04 00:05 | 2026-07-01 00:10 | 21831 |
| MU | C6 | 1983.35 | 19.83 | 1822.32 | 3805.67 | 38.06 | 1.33 | 16 | 68.8 | 36.6 | 53.65 | 4337.88 | -2354.53 | 2026-05-04 00:05 | 2026-07-01 00:10 | 21831 |
| SPCX | C1 | -2938.06 | -29.38 | 479.83 | -2458.23 | -24.58 | 0.01 | 9 | 11.1 | 34.5 | 21.70 | -2627.65 | -310.40 | 2026-06-01 00:05 | 2026-07-02 06:50 | 15857 |
| SPCX | C2 | -3317.60 | -33.18 | 1.83 | -3315.77 | -33.16 | 0.53 | 16 | 43.8 | 50.4 | 34.87 | -2094.36 | -1223.24 | 2026-06-01 00:05 | 2026-07-10 20:00 | 15857 |
| SPCX | C3 | -3453.48 | -34.53 | 0.00 | -3453.48 | -34.53 | 0.43 | 13 | 30.8 | 50.5 | 28.07 | -1985.06 | -1468.42 | 2026-06-01 00:05 | 2026-07-08 15:45 | 15857 |
| SPCX | C4 | -2857.08 | -28.57 | 507.17 | -2349.91 | -23.50 | 0.02 | 9 | 11.1 | 33.5 | 21.76 | -2547.66 | -309.42 | 2026-06-01 00:05 | 2026-07-02 06:30 | 15857 |
| SPCX | C5 | -3531.83 | -35.32 | 0.00 | -3531.83 | -35.32 | 0.40 | 13 | 30.8 | 49.2 | 27.99 | -1899.79 | -1632.03 | 2026-06-01 00:05 | 2026-07-10 19:55 | 15857 |
| SPCX | C6 | -3562.11 | -35.62 | 0.00 | -3562.11 | -35.62 | 0.39 | 12 | 33.3 | 49.3 | 25.50 | -1866.39 | -1695.72 | 2026-06-01 00:05 | 2026-07-10 19:55 | 15857 |
| CL | C1 | 1778.69 | 17.79 | 597.58 | 2376.26 | 23.76 | 2.29 | 9 | 22.2 | 12.4 | 23.67 | -847.23 | 2625.92 | 2026-05-04 00:45 | 2026-07-07 14:35 | 21867 |
| CL | C2 | 3288.12 | 32.88 | -28.69 | 3259.42 | 32.59 | 2.77 | 19 | 57.9 | 13.8 | 52.11 | 327.83 | 2960.28 | 2026-05-04 00:45 | 2026-07-08 08:30 | 21867 |
| CL | C3 | 1000.15 | 10.00 | -169.67 | 830.48 | 8.30 | 1.72 | 17 | 52.9 | 13.6 | 42.40 | 492.29 | 507.86 | 2026-05-04 00:45 | 2026-07-08 09:00 | 21870 |
| CL | C4 | 1780.77 | 17.81 | 622.65 | 2403.43 | 24.03 | 2.30 | 9 | 22.2 | 12.4 | 23.67 | -845.71 | 2626.48 | 2026-05-04 00:45 | 2026-07-07 14:25 | 21868 |
| CL | C5 | 1410.16 | 14.10 | -171.43 | 1238.73 | 12.39 | 2.32 | 15 | 66.7 | 13.3 | 37.96 | 516.18 | 893.98 | 2026-05-04 00:45 | 2026-07-08 09:10 | 21868 |
| CL | C6 | 1822.59 | 18.23 | -177.78 | 1644.81 | 16.45 | 2.97 | 12 | 75.0 | 12.8 | 31.21 | 906.87 | 915.72 | 2026-05-04 00:45 | 2026-07-08 09:10 | 21868 |

## Core findings by question

### Does the BF exit improve the native flip control?

No consistent improvement appeared in the pre-registered core.

- C2 versus C1 improved closed net on 2 of 5 symbols and total net on 1 of 5. The median delta was -222.19 USDC closed and -199.84 USDC including open P/L.
- C3 versus C1 improved neither closed nor total net on any of the 5 core symbols. The median delta was -515.42 USDC closed and -995.26 USDC total.
- C5 versus its direct 5m-arm control C4 improved closed net only on AMZN and improved total net on 0 of 5 symbols. The core median delta was -602.23 USDC closed and -823.37 USDC total.

BF exits often raised win rate by harvesting moves, but more wins did not imply more net profit. MU and SPCX are the clearest opposites: MU stayed strongly profitable across all cells while BF variants trailed the control, and SPCX stayed deeply negative while BF increased trade count and drawdown.

### Does ratchet re-entry fix recycle churn, and how?

It fixes the mechanical churn, but not consistently the economics.

- C3 had fewer trades than C2 on every core symbol: AMZN -4, XYZ100 -4, MU -2, SPCX -3, and CL -2.
- Across the 5 core symbols, closed trades fell from 103 in C2 to 88 in C3. BF exits fell from 55 to 46, and same-direction re-entries immediately following a BF exit fell from 48 to 32.
- Recycle commonly re-entered on the next 5m bar. Ratchet changed the price and time, not just the count: per-symbol median same-direction waits moved from mostly 5 minutes in C2 to 280-5160 minutes in C3. The re-entry trigger was also farther in the original direction, as intended.
- That filtering improved both closed and total net only on AMZN in the core. It worsened both on XYZ100, MU, SPCX, and CL. CL is the strongest counterexample: the median same-direction wait rose from 5 to 5160 minutes and the directional price extension rose from 0.14% to 4.07%, yet closed net fell from 3288.12 to 1000.15 USDC.

The data therefore shows that ratchet implements the intended stand-down behavior. It does not show that every suppressed recycle entry was bad; in strong trends it can skip productive re-entry opportunities.

### What does the 5m arming split do by itself?

C4 versus C1 was nearly neutral on most symbols. It improved closed and total net on 4 of 5 core symbols, but the median changes were only +4.56 USDC closed and +27.16 USDC total. Trade count was unchanged on AMZN, XYZ100, SPCX, and CL and rose by one on MU. MU was the material negative outlier at -450.97 USDC closed and -519.68 USDC total.

The 5m trigger is structurally different, but it did not behave like a universal earlier-or-better entry. All eight sampled symbols happened to retain the same first-entry timestamp across C1/C2/C3 and C4/C5/C6, while later entry prices and sequences could diverge.

### What does the 30m exit clock do?

C6 always reduced closed trades versus C5, by one to three in the core, but improved closed and total net on only 2 of 5 core symbols. The median delta was -12.69 USDC for both accountings.

The symbol spread is the finding: AMZN gained 451.10 USDC and CL gained about 406.09 USDC total, while MU lost 2401.23 USDC total. The slower clock changes native-exit and BF-block-reset cadence; it did not dominate the 15m clock.

### Closed versus total accounting

Open P/L changes several apparent rankings. XYZ100 C2 reports +311.05 USDC closed but only +53.69 total. MU controls carry more than +2100 USDC open profit. The widened SNDK sample is more severe: C5 reports +1147.75 closed but -991.38 total, and C6 reports +2077.29 closed but -240.34 total. A BF exit can move P/L from unrealized to realized without improving total equity.

## Exploratory sample widening - 18 additional runs

MU and SPCX were opposite extreme results, so the protocol required widening the symbol sample rather than tuning those symbols. A live [HIP-3 screener state snapshot](https://hip3-alerts-production.up.railway.app/api/state) at 2026-07-12 00:24:29 UTC was ranked by 24h notional volume. Known zero-history SKHX/SKHY were skipped. The three highest remaining tradeable names outside the core were:

| Symbol | 24h notional volume | Open interest USD |
|---|---:|---:|
| SP500 | 44,559,922.71 | 545,266,936.40 |
| BRENTOIL | 44,210,137.44 | 170,534,823.55 |
| SNDK | 22,047,723.07 | 81,413,565.29 |

These 18 runs are exploratory and are not part of the pre-registered 30-cell core.

| Symbol | Cell | Closed net | Closed % | Open P/L | Total net | Total % | PF | Trades | Win % | Max DD % | Comm. | Long net | Short net | First entry UTC | Last event UTC | Bars |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|
| SP500 | C1 | 24.64 | 0.25 | 65.05 | 89.69 | 0.90 | 1.05 | 15 | 13.3 | 2.6 | 38.93 | 206.89 | -182.25 | 2026-05-04 00:10 | 2026-07-09 15:20 | 21885 |
| SP500 | C2 | -87.94 | -0.88 | 64.32 | -23.63 | -0.24 | 0.90 | 25 | 32.0 | 3.4 | 63.85 | 130.97 | -218.91 | 2026-05-04 00:10 | 2026-07-09 15:20 | 21885 |
| SP500 | C3 | -138.60 | -1.39 | 63.97 | -74.62 | -0.75 | 0.79 | 19 | 26.3 | 3.7 | 48.13 | -102.79 | -35.81 | 2026-05-04 00:10 | 2026-07-09 15:20 | 21885 |
| SP500 | C4 | 35.19 | 0.35 | 65.10 | 100.29 | 1.00 | 1.07 | 15 | 13.3 | 2.6 | 38.95 | 212.84 | -177.65 | 2026-05-04 00:10 | 2026-07-09 15:20 | 21885 |
| SP500 | C5 | -129.04 | -1.29 | 64.02 | -65.02 | -0.65 | 0.79 | 20 | 30.0 | 3.1 | 50.87 | -26.50 | -102.54 | 2026-05-04 00:10 | 2026-07-09 15:20 | 21885 |
| SP500 | C6 | -158.49 | -1.58 | 58.99 | -99.50 | -0.99 | 0.76 | 19 | 31.6 | 3.0 | 48.66 | -45.25 | -113.23 | 2026-05-04 00:10 | 2026-07-09 15:40 | 21885 |
| BRENTOIL | C1 | 768.74 | 7.69 | 671.35 | 1440.09 | 14.40 | 1.33 | 14 | 14.3 | 11.8 | 35.48 | -1122.91 | 1891.65 | 2026-05-04 00:45 | 2026-07-07 14:05 | 21855 |
| BRENTOIL | C2 | 959.49 | 9.59 | 276.74 | 1236.23 | 12.36 | 1.32 | 24 | 45.8 | 13.9 | 60.98 | -762.52 | 1722.01 | 2026-05-04 00:45 | 2026-07-11 22:15 | 21855 |
| BRENTOIL | C3 | 1220.89 | 12.21 | 0.00 | 1220.89 | 12.21 | 1.56 | 21 | 42.9 | 14.0 | 51.44 | -870.66 | 2091.55 | 2026-05-04 00:45 | 2026-07-11 22:10 | 21855 |
| BRENTOIL | C4 | 791.35 | 7.91 | 662.10 | 1453.45 | 14.53 | 1.34 | 14 | 14.3 | 11.7 | 35.49 | -1119.02 | 1910.37 | 2026-05-04 00:45 | 2026-07-07 14:05 | 21855 |
| BRENTOIL | C5 | 1430.15 | 14.30 | 0.00 | 1430.15 | 14.30 | 1.67 | 21 | 42.9 | 13.5 | 51.69 | -839.37 | 2269.53 | 2026-05-04 00:45 | 2026-07-11 22:10 | 21857 |
| BRENTOIL | C6 | 982.56 | 9.83 | 0.00 | 982.56 | 9.83 | 1.64 | 16 | 50.0 | 12.4 | 39.52 | -404.61 | 1387.17 | 2026-05-04 00:45 | 2026-07-11 22:10 | 21856 |
| SNDK | C1 | 1315.14 | 13.15 | 744.17 | 2059.31 | 20.59 | 1.30 | 18 | 11.1 | 38.1 | 56.20 | 2935.37 | -1620.23 | 2026-05-04 00:05 | 2026-07-01 13:30 | 21820 |
| SNDK | C2 | 1509.05 | 15.09 | -1375.27 | 133.79 | 1.34 | 1.20 | 29 | 34.5 | 42.3 | 81.04 | 2727.80 | -1218.74 | 2026-05-04 00:05 | 2026-07-06 17:25 | 21820 |
| SNDK | C3 | 4765.50 | 47.66 | -1943.34 | 2822.16 | 28.22 | 2.08 | 24 | 29.2 | 28.2 | 71.57 | 4099.26 | 666.24 | 2026-05-04 00:05 | 2026-07-06 17:55 | 21820 |
| SNDK | C4 | 1152.81 | 11.53 | 734.55 | 1887.36 | 18.87 | 1.25 | 19 | 10.5 | 39.0 | 58.95 | 2891.15 | -1738.34 | 2026-05-04 00:05 | 2026-07-01 13:30 | 21820 |
| SNDK | C5 | 1147.75 | 11.48 | -2139.13 | -991.38 | -9.91 | 1.17 | 26 | 26.9 | 41.2 | 72.60 | 2774.22 | -1626.47 | 2026-05-04 00:05 | 2026-07-07 05:00 | 21820 |
| SNDK | C6 | 2077.29 | 20.77 | -2317.63 | -240.34 | -2.40 | 1.36 | 24 | 25.0 | 38.5 | 68.57 | 2610.83 | -533.54 | 2026-05-04 00:05 | 2026-07-07 05:00 | 21820 |

## Cross-sample synthesis and surprises

- Across all 8 symbols, C2 beat C1 on closed net in 4 cases but on total net in only 1. C3 beat C1 on closed net in 2 and total net in 1.
- The direct intended-system comparison remained unfavorable on total equity: C5 beat C4 on closed net in 2 of 8 symbols and on total net in 0 of 8. The median delta was -267.43 USDC closed and -747.82 USDC total.
- Ratchet continued to suppress churn across the wider sample. C2 had 181 closed trades, 86 BF exits, and 76 same-direction BF re-entries. C3 had 152 closed trades, 69 BF exits, and 45 same-direction BF re-entries. The pooled median same-direction wait rose from 5 to 685 minutes, and the median directional price extension rose from about 0.003% to 1.37%.
- Ratchet versus recycle improved closed net in 3 of 8 symbols and total net in 2 of 8. The mechanism works, but its performance effect depends on which re-entries it suppresses.
- C4 versus C1 was the most stable ablation mechanically: it improved closed and total net in 6 of 8 symbols, but median changes were only +7.55 and +11.98 USDC. MU and SNDK remained material counterexamples.
- C6 versus C5 improved closed and total net in 3 of 8 and reduced trade count in all 8. It is a cadence change, not a robust improvement.
- Extreme positive and negative regimes remained. MU ranged from +19.83% to +52.88% closed net with 24.6%-36.6% drawdown. SPCX ranged from -28.57% to -35.62% closed net with 33.5%-50.5% drawdown. SNDK C3 reached +47.66% closed but only +28.22% total because of -1943.34 USDC open P/L.
- The low control win rates are not automatically bugs. The native flip control can express a few long trend rides. Conversely, BF variants can post much higher win rates while reducing net profit through extra commissions, truncated winners, and later losing exposure.

## Caveats

- This is in-sample, one roughly 8-12 week window, not an out-of-sample test. SPCX is younger and begins on 2026-05-17; most other widened symbols begin on 2026-04-27.
- Historical intrabar timing is only 5m chart-grade. The script recalculates intrabar live, but historical stop and limit orders become active on the next chart bar. Bar magnifier improves fill ordering inside eligible bars but does not reconstruct the exact tick at which a historical live gate first aligned.
- The BF test uses a resting next-bar limit. A manual exit-on-alert is different: the line deviation must first be detected, the alert transported, and a marketable exit sent. A touch fill at the modeled limit can be materially better than an alert-driven fill.
- BF pivots confirm 10 completed 30m bars after the turn, plus propagation lag. Pivot dots are delayed structure annotations and were never used as exit events.
- Open P/L was live while cells were collected sequentially. Closed metrics and trade sequences are stable; total net is a timestamped snapshot and can move with the current bar. This is why both accountings are reported.
- The model includes commission and one tick of slippage, but not funding, spread variation, queue position, market impact, venue outages, or manual reaction latency.
- The fixed skeleton deliberately omits scanner selection, pattern/timeframe selection, liquidity/volume/OI gates, targets, and other discretionary context. The extreme symbol spread is evidence that those omitted layers matter, not evidence to select a cell from this sample.
- No conclusion here says to deploy a cell. Under these assumptions, the data shows that BF ratchet changes re-entry behavior substantially, while BF-exit performance and exit-clock effects remain inconsistent across symbols and accounting methods.
