# The pivot ladder (2026-10-20)

556,092 daily trigger rows with a full 10-bar window. The ladder is the owner's Pine ported to daily bars (anchors first, then prior highs / lows not yet taken out, six rungs, 250 bars back). 'reached k' = the favourable extreme touched rung k within 10 bars (reach convention). Hours = hourly bars after the trigger bar.

## 1. How far price climbs the ladder

| all | n | ladder len median | no rung pct | reached 1 pct | reached 2 pct | reached 3 pct | reached 4 pct | mean rungs reached | median h rung1 | median h rung2 | median h rung3 | t1 dist r median | t3 dist r median |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 556,092 | 6.00 | 2.7% | 81.4% | 64.3% | 49.8% | 38.0% | +2.841 | 6.00 | 27.00 | 50.00 | 0.35 | 1.37 |

### by family

| family | n | ladder len median | no rung pct | reached 1 pct | reached 2 pct | reached 3 pct | reached 4 pct | mean rungs reached | median h rung1 | median h rung2 | median h rung3 | t1 dist r median | t3 dist r median |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| continuation | 223,620 | 6.00 | 6.0% | 77.7% | 60.2% | 46.5% | 35.6% | +2.676 | 5.00 | 24.00 | 48.00 | 0.32 | 1.30 |
| inside | 119,821 | 6.00 | 0.0% | 86.8% | 68.0% | 52.2% | 39.3% | +2.975 | 4.00 | 25.00 | 48.00 | 0.34 | 1.65 |
| outside | 49,725 | 6.00 | 3.0% | 81.9% | 64.9% | 50.3% | 38.7% | +2.878 | 4.00 | 24.00 | 47.00 | 0.24 | 1.01 |
| reversal | 162,926 | 6.00 | 0.0% | 82.4% | 67.0% | 52.5% | 40.3% | +2.959 | 11.00 | 33.00 | 55.00 | 0.44 | 1.40 |

### by pattern

| pattern | n | ladder len median | no rung pct | reached 1 pct | reached 2 pct | reached 3 pct | reached 4 pct | mean rungs reached | median h rung1 | median h rung2 | median h rung3 | t1 dist r median | t3 dist r median |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1-1-2 stacked inside | 13,998 | 6.00 | 0.0% | 92.2% | 76.7% | 57.3% | 43.3% | +3.262 | 2.00 | 16.00 | 39.00 | 0.25 | 1.65 |
| 1-2-2 rev strat | 32,202 | 6.00 | 0.0% | 88.0% | 75.3% | 58.0% | 44.2% | +3.236 | 5.00 | 19.00 | 41.00 | 0.31 | 1.24 |
| 2-1-2 continuation | 40,119 | 6.00 | 0.1% | 88.0% | 65.7% | 49.8% | 37.1% | +2.888 | 3.00 | 20.00 | 44.00 | 0.30 | 1.61 |
| 2-1-2 reversal | 48,017 | 6.00 | 0.0% | 85.2% | 67.9% | 52.8% | 39.9% | +2.981 | 6.00 | 32.00 | 56.00 | 0.40 | 1.69 |
| 2-2 continuation | 223,620 | 6.00 | 6.0% | 77.7% | 60.2% | 46.5% | 35.6% | +2.676 | 5.00 | 24.00 | 48.00 | 0.32 | 1.30 |
| 2-2 reversal | 114,549 | 6.00 | 0.0% | 81.8% | 65.5% | 51.6% | 39.7% | +2.919 | 12.00 | 36.00 | 59.00 | 0.46 | 1.43 |
| 3-1-2 continuation | 7,760 | 6.00 | 0.0% | 90.3% | 72.8% | 56.8% | 43.4% | +3.211 | 2.00 | 17.00 | 39.00 | 0.26 | 1.44 |
| 3-1-2 reversal | 9,712 | 6.00 | 0.0% | 78.7% | 63.3% | 49.3% | 37.1% | +2.754 | 15.00 | 36.00 | 61.00 | 0.60 | 1.77 |
| 3-2 outside break | 49,725 | 6.00 | 3.0% | 81.9% | 64.9% | 50.3% | 38.7% | +2.878 | 4.00 | 24.00 | 47.00 | 0.24 | 1.01 |
| 3-2-2 reversal | 16,175 | 6.00 | 0.0% | 75.3% | 61.8% | 48.0% | 36.4% | +2.696 | 22.00 | 42.00 | 65.00 | 0.65 | 1.55 |
| x-1-2 (no bar before) | 215 | 1.00 | 0.5% | 80.9% | 0.0% | 0.0% | 0.0% | +0.809 | 7.00 |  |  | 0.42 |  |

### majors vs alts

| asset class | n | ladder len median | no rung pct | reached 1 pct | reached 2 pct | reached 3 pct | reached 4 pct | mean rungs reached | median h rung1 | median h rung2 | median h rung3 | t1 dist r median | t3 dist r median |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alt | 551,663 | 6.00 | 2.7% | 81.4% | 64.3% | 49.8% | 38.0% | +2.841 | 6.00 | 27.00 | 50.00 | 0.35 | 1.37 |
| major | 4,429 | 6.00 | 4.2% | 81.4% | 64.0% | 50.3% | 39.0% | +2.869 | 5.00 | 25.50 | 47.00 | 0.33 | 1.36 |

### by year

| year | n | ladder len median | no rung pct | reached 1 pct | reached 2 pct | reached 3 pct | reached 4 pct | mean rungs reached | median h rung1 | median h rung2 | median h rung3 | t1 dist r median | t3 dist r median |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2020.00 | 12460.00 | 6.00 | 5.3% | 79.6% | 62.8% | 48.9% | 38.0% | +2.802 | 5.00 | 23.00 | 45.00 | 0.34 | 1.32 |
| 2021.00 | 37819.00 | 6.00 | 2.9% | 81.0% | 64.1% | 51.1% | 39.6% | +2.891 | 7.00 | 30.00 | 54.00 | 0.37 | 1.36 |
| 2022.00 | 47115.00 | 6.00 | 2.7% | 81.6% | 64.3% | 49.5% | 37.3% | +2.819 | 6.00 | 29.00 | 52.00 | 0.35 | 1.38 |
| 2023.00 | 62898.00 | 6.00 | 1.5% | 83.1% | 67.0% | 52.5% | 40.8% | +2.996 | 6.00 | 27.00 | 50.00 | 0.35 | 1.37 |
| 2024.00 | 94746.00 | 6.00 | 2.1% | 82.2% | 65.5% | 51.1% | 39.8% | +2.938 | 7.00 | 29.00 | 53.00 | 0.36 | 1.40 |
| 2025.00 | 147442.00 | 6.00 | 2.6% | 80.0% | 62.6% | 48.0% | 36.2% | +2.733 | 6.00 | 27.00 | 49.00 | 0.36 | 1.41 |
| 2026.00 | 153612.00 | 6.00 | 3.4% | 81.8% | 64.3% | 49.5% | 37.4% | +2.821 | 6.00 | 25.00 | 48.00 | 0.34 | 1.34 |

## 2. Rows the TVB-37 ladder left without a target: 60,478; of those the Pine ladder gives a rung to 45,512, and 60.1% of them reach rung 1 within 10 bars (median R:R 0.33)

## 3. The Pine's T1 against the TVB-37 T1, same rows, same stop, same walk

| family | n | same t1 pct | tvb37 rr median | pine rr median | tvb37 tgt first pct | pine tgt first pct | tvb37 win pct | pine win pct | tvb37 mean r | pine mean r | diff mean r |
|---|---|---|---|---|---|---|---|---|---|---|---|
| continuation | 180,860 | 19.4% | 1.44 | 0.32 | 40.5% | 72.0% | 47.3% | 72.6% | -0.031 | -0.016 | +0.015 |
| inside | 109,350 | 64.7% | 0.72 | 0.34 | 54.9% | 71.4% | 57.2% | 71.7% | -0.030 | -0.009 | +0.021 |
| outside | 43,343 | 18.1% | 1.08 | 0.24 | 45.6% | 76.7% | 53.2% | 77.3% | -0.012 | -0.004 | +0.008 |
| reversal | 162,061 | 100.0% | 0.44 | 0.44 | 67.5% | 67.5% | 68.1% | 68.1% | -0.012 | -0.012 | +0.000 |

### by pattern

| pattern | n | same t1 pct | tvb37 rr median | pine rr median | tvb37 tgt first pct | pine tgt first pct | tvb37 win pct | pine win pct | tvb37 mean r | pine mean r | diff mean r |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1-1-2 stacked inside | 11,986 | 0.5% | 2.96 | 0.24 | 26.9% | 76.7% | 32.5% | 76.7% | -0.080 | -0.014 | +0.066 |
| 1-2-2 rev strat | 31,903 | 100.0% | 0.31 | 0.31 | 72.6% | 72.6% | 72.7% | 72.7% | -0.033 | -0.033 | +0.000 |
| 2-1-2 continuation | 32,594 | 18.1% | 1.91 | 0.29 | 37.2% | 74.2% | 41.9% | 74.4% | -0.061 | -0.013 | +0.048 |
| 2-1-2 reversal | 47,474 | 100.0% | 0.40 | 0.40 | 69.4% | 69.4% | 69.9% | 69.9% | -0.007 | -0.007 | +0.000 |
| 2-2 continuation | 180,860 | 19.4% | 1.44 | 0.32 | 40.5% | 72.0% | 47.3% | 72.6% | -0.031 | -0.016 | +0.015 |
| 2-2 reversal | 114,018 | 100.0% | 0.46 | 0.46 | 67.1% | 67.1% | 67.7% | 67.7% | -0.008 | -0.008 | +0.000 |
| 3-1-2 continuation | 7,632 | 100.0% | 0.25 | 0.25 | 76.3% | 76.3% | 76.6% | 76.6% | +0.006 | +0.006 | +0.000 |
| 3-1-2 reversal | 9,664 | 100.0% | 0.60 | 0.60 | 61.3% | 61.3% | 62.0% | 62.0% | -0.009 | -0.009 | +0.000 |
| 3-2 outside break | 43,343 | 18.1% | 1.08 | 0.24 | 45.6% | 76.7% | 53.2% | 77.3% | -0.012 | -0.004 | +0.008 |
| 3-2-2 reversal | 16,140 | 100.0% | 0.65 | 0.65 | 60.6% | 60.6% | 61.8% | 61.8% | +0.004 | +0.004 | +0.000 |

### majors vs alts

| asset class | n | same t1 pct | tvb37 rr median | pine rr median | tvb37 tgt first pct | pine tgt first pct | tvb37 win pct | pine win pct | tvb37 mean r | pine mean r | diff mean r |
|---|---|---|---|---|---|---|---|---|---|---|---|
| alt | 491,703 | 55.6% | 0.78 | 0.35 | 53.0% | 70.8% | 56.8% | 71.3% | -0.023 | -0.012 | +0.011 |
| major | 3,911 | 55.9% | 0.79 | 0.33 | 54.5% | 72.5% | 57.7% | 72.8% | -0.004 | +0.006 | +0.010 |
