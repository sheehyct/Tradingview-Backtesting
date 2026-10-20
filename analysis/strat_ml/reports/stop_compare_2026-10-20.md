# Stop placement head-to-head on inside breaks (2026-10-20)

Same 119,926 inside-break rows (setup bar Type 1), two stops: the far side of the setup bar (TVB-37 R) vs the far side of bar 0 (the skill's structural stop). Everything else identical: entry at the level, the same target, 10 daily bars, stop-first on ties. 'ret % of price' and 'ret (ATR)' are the units that do not move with the stop; R moves with it by construction.

## Inside breaks, all rows

| mode | n | win % | stop first % | target first % | mean R | median R | mean ret % of price | median ret % | mean ret (ATR) | median R:R | median stop (ATR) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bar-0 stop | 119,926 | 61.7% | 35.0% | 55.2% | -0.015 | +0.085 | -0.2% | 0.7% | -0.010 | 0.49 | 0.84 |
| setup-bar stop | 119,926 | 54.3% | 44.9% | 50.1% | -0.027 | +0.048 | -0.2% | 0.2% | -0.013 | 0.72 | 0.57 |

## By pattern

| pattern | mode | n | win % | stop first % | target first % | mean R | median R | mean ret % of price | median ret % | mean ret (ATR) | median R:R | median stop (ATR) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1-1-2 stacked inside | bar-0 stop | 14,003 | 44.7% | 48.8% | 30.2% | -0.029 | -0.541 | -0.3% | -2.5% | -0.023 | 1.51 | 0.90 |
| 1-1-2 stacked inside | setup-bar stop | 14,003 | 30.9% | 68.3% | 23.1% | -0.062 | -1.000 | -0.4% | -2.9% | -0.024 | 2.96 | 0.47 |
| 2-1-2 continuation | bar-0 stop | 40,168 | 46.6% | 48.7% | 34.6% | -0.035 | -0.469 | -0.5% | -2.2% | -0.028 | 1.30 | 0.82 |
| 2-1-2 continuation | setup-bar stop | 40,168 | 38.5% | 60.2% | 30.2% | -0.052 | -1.000 | -0.5% | -2.9% | -0.028 | 1.91 | 0.56 |
| 2-1-2 reversal | bar-0 stop | 48,051 | 74.7% | 23.7% | 73.4% | +0.001 | +0.124 | 0.0% | 0.9% | +0.002 | 0.29 | 0.80 |
| 2-1-2 reversal | setup-bar stop | 48,051 | 69.4% | 30.0% | 68.6% | -0.004 | +0.136 | -0.0% | 0.7% | -0.004 | 0.40 | 0.58 |
| 3-1-2 continuation | bar-0 stop | 7,763 | 83.8% | 14.9% | 82.5% | +0.016 | +0.090 | 0.2% | 0.8% | +0.020 | 0.14 | 1.05 |
| 3-1-2 continuation | setup-bar stop | 7,763 | 75.7% | 24.1% | 75.1% | +0.005 | +0.123 | 0.0% | 0.6% | +0.004 | 0.25 | 0.59 |
| 3-1-2 reversal | bar-0 stop | 9,726 | 67.1% | 30.7% | 65.9% | -0.008 | +0.147 | -0.0% | 1.2% | +0.001 | 0.44 | 0.84 |
| 3-1-2 reversal | setup-bar stop | 9,726 | 61.9% | 37.2% | 61.0% | -0.007 | +0.143 | -0.0% | 0.8% | -0.001 | 0.60 | 0.64 |
| x-1-2 (no bar before) | bar-0 stop | 215 | 38.1% | 54.4% | 0.0% | -0.158 | -1.000 | -0.8% | -4.7% | +nan | nan | nan |
| x-1-2 (no bar before) | setup-bar stop | 215 | 32.1% | 64.2% | 0.0% | -0.151 | -1.000 | -0.5% | -4.4% | +nan | nan | nan |

## By direction

| direction | mode | n | win % | stop first % | target first % | mean R | median R | mean ret % of price | median ret % | mean ret (ATR) | median R:R | median stop (ATR) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| long | bar-0 stop | 59,675 | 59.4% | 37.4% | 54.7% | -0.037 | +0.068 | -0.4% | 0.5% | -0.022 | 0.54 | 0.82 |
| long | setup-bar stop | 59,675 | 52.4% | 46.7% | 49.7% | -0.060 | +0.028 | -0.4% | 0.1% | -0.026 | 0.77 | 0.57 |
| short | bar-0 stop | 60,251 | 64.0% | 32.8% | 55.8% | +0.008 | +0.101 | 0.1% | 0.8% | +0.002 | 0.45 | 0.86 |
| short | setup-bar stop | 60,251 | 56.1% | 43.1% | 50.5% | +0.006 | +0.068 | -0.0% | 0.4% | -0.001 | 0.67 | 0.56 |

## Majors vs alts

| asset class | mode | n | win % | stop first % | target first % | mean R | median R | mean ret % of price | median ret % | mean ret (ATR) | median R:R | median stop (ATR) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| alt | bar-0 stop | 118,858 | 61.7% | 35.0% | 55.2% | -0.015 | +0.085 | -0.2% | 0.7% | -0.010 | 0.49 | 0.84 |
| alt | setup-bar stop | 118,858 | 54.3% | 44.8% | 50.1% | -0.027 | +0.048 | -0.2% | 0.2% | -0.014 | 0.72 | 0.57 |
| major | bar-0 stop | 1,068 | 61.5% | 34.9% | 55.5% | +0.036 | +0.097 | -0.1% | 0.4% | +0.021 | 0.64 | 0.88 |
| major | setup-bar stop | 1,068 | 51.7% | 47.8% | 48.9% | +0.012 | +0.026 | -0.1% | 0.1% | +0.013 | 1.01 | 0.55 |

## By year

| year | mode | n | win % | stop first % | mean ret % of price | median ret % | mean ret (ATR) |
|---|---|---|---|---|---|---|---|
| 2,020 | bar-0 stop | 3,015 | 60.9% | 35.8% | -0.1% | 0.7% | +0.018 |
| 2,020 | setup-bar stop | 3,015 | 53.4% | 45.7% | -0.2% | 0.2% | +0.009 |
| 2,021 | bar-0 stop | 7,919 | 63.1% | 32.4% | -0.2% | 1.1% | +0.027 |
| 2,021 | setup-bar stop | 7,919 | 55.7% | 42.9% | -0.4% | 0.5% | +0.005 |
| 2,022 | bar-0 stop | 8,981 | 62.2% | 34.9% | -0.3% | 0.6% | -0.024 |
| 2,022 | setup-bar stop | 8,981 | 56.6% | 42.6% | -0.4% | 0.3% | -0.024 |
| 2,023 | bar-0 stop | 15,876 | 61.5% | 35.0% | -0.2% | 0.6% | -0.014 |
| 2,023 | setup-bar stop | 15,876 | 52.6% | 46.9% | -0.3% | 0.1% | -0.027 |
| 2,024 | bar-0 stop | 17,875 | 63.7% | 33.6% | -0.2% | 0.7% | -0.001 |
| 2,024 | setup-bar stop | 17,875 | 57.2% | 42.1% | -0.2% | 0.4% | -0.003 |
| 2,025 | bar-0 stop | 31,575 | 61.2% | 34.7% | -0.1% | 0.7% | -0.016 |
| 2,025 | setup-bar stop | 31,575 | 54.5% | 44.2% | -0.2% | 0.3% | -0.014 |
| 2,026 | bar-0 stop | 34,685 | 60.8% | 36.7% | -0.2% | 0.6% | -0.014 |
| 2,026 | setup-bar stop | 34,685 | 52.4% | 47.0% | -0.2% | 0.1% | -0.016 |

## The whole book (all patterns; only the inside rows changed)

| mode | n | win % | stop first % | mean ret % of price | median ret % |
|---|---|---|---|---|---|
| setup-bar stop | 556,844 | 53.1% | 43.4% | -0.3% | 0.3% |
| bar-0 stop | 556,844 | 54.7% | 41.3% | -0.3% | 0.5% |
