# The overfit and underfit ticker census (2026-10-20)

384 coins with at least 500 daily trigger rows (of 900). Per coin: rows, years of history, the effective number of patterns (1 = one pattern, 11 = all equally), the share of rows that were 2-2 continuations, win %, mean R (winsorized) with the setup-bar stop, the sum of R, mean return in % of price, mean R with no stop, and z = mean R divided by the coin's own noise (sd / sqrt n). A labelled overfit census: ceiling-mapping, never a promotion.

The honest yardstick first: a coin with 1,000 rows and no edge would show a mean R anywhere within about +-0.068 by chance (two noise sd). The top of the table should be read against that.

## The overfit end: top 15 by mean R

| rank | symbol | n | years | eff patterns | continuation share | win pct | mean r | sum r | mean ret pct | mean r no stop | z | liq rank median | stable |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | GUNUSDT | 509 | 1.51 | 5.91 | 43% | 55.8% | +0.107 | +54.468 | 0.8% | +0.078 | 1.84 | 202.50 |  |
| 2 | SONICUSDT | 581 | 1.73 | 5.56 | 42% | 58.2% | +0.105 | +61.118 | 0.4% | +0.019 | 2.13 | 413.00 |  |
| 3 | CETUSUSDT | 618 | 1.90 | 6.06 | 41% | 56.3% | +0.100 | +61.777 | 0.5% | +0.256 | 1.98 | 347.00 |  |
| 4 | MEUSDT | 585 | 1.81 | 5.77 | 40% | 57.6% | +0.075 | +44.128 | 0.2% | +0.058 | 1.58 | 240.50 |  |
| 5 | WAVESUSDT | 1,254 | 3.79 | 6.33 | 38% | 55.9% | +0.075 | +94.457 | 0.6% | +0.259 | 2.20 | 52.00 |  |
| 6 | KAIAUSDT | 601 | 1.83 | 5.64 | 43% | 57.4% | +0.070 | +41.882 | 0.5% | +0.214 | 1.51 | 335.00 |  |
| 7 | WLDUSDT | 1,040 | 3.20 | 5.74 | 43% | 57.1% | +0.069 | +71.568 | 0.4% | +0.203 | 1.91 | 25.00 |  |
| 8 | BTSUSDT | 510 | 1.50 | 5.83 | 40% | 57.1% | +0.069 | +35.074 | 0.1% | +0.047 | 1.36 | 122.00 |  |
| 9 | MBOXUSDT | 559 | 1.74 | 5.97 | 41% | 56.0% | +0.068 | +38.136 | 0.4% | +0.138 | 1.38 | 311.00 |  |
| 10 | LUMIAUSDT | 563 | 1.79 | 6.40 | 38% | 57.0% | +0.067 | +37.535 | 0.6% | +0.212 | 1.29 | 329.00 |  |
| 11 | SOLUSDT | 2,008 | 6.05 | 5.77 | 42% | 58.3% | +0.066 | +132.592 | 0.5% | +0.132 | 2.59 | 4.00 |  |
| 12 | SRMUSDT | 737 | 2.15 | 5.27 | 43% | 57.8% | +0.066 | +48.641 | 0.1% | +0.228 | 1.60 | 66.00 |  |
| 13 | BMTUSDT | 512 | 1.55 | 6.36 | 39% | 55.5% | +0.054 | +27.850 | 0.3% | +0.221 | 1.01 | 378.00 |  |
| 14 | BANANAUSDT | 709 | 2.13 | 5.71 | 44% | 55.1% | +0.054 | +38.022 | -0.0% | +0.049 | 1.22 | 222.00 |  |
| 15 | TRXUSDT | 2,281 | 6.72 | 5.87 | 40% | 55.2% | +0.050 | +114.191 | -0.1% | +0.207 | 1.98 | 48.00 |  |

## The underfit end: bottom 15 by mean R

| rank | symbol | n | years | eff patterns | continuation share | win pct | mean r | sum r | mean ret pct | mean r no stop | z | liq rank median | stable |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 384 | USDCUSDT | 1,153 | 3.56 | 7.43 | 33% | 42.7% | -0.233 | -268.998 | -0.0% | -0.066 | -7.34 | 265.00 | yes |
| 383 | TSTUSDT | 546 | 1.65 | 6.66 | 34% | 47.8% | -0.172 | -94.151 | -2.2% | +0.117 | -3.96 | 228.50 |  |
| 382 | BANUSDT | 630 | 1.87 | 6.63 | 37% | 50.3% | -0.159 | -99.949 | -1.4% | -0.092 | -4.21 | 316.00 |  |
| 381 | HEIUSDT | 544 | 1.63 | 6.52 | 37% | 50.4% | -0.156 | -84.693 | -1.6% | +0.046 | -3.75 | 340.00 |  |
| 380 | FOOTBALLUSDT | 506 | 1.53 | 7.11 | 34% | 48.4% | -0.134 | -67.967 | -0.6% | +0.165 | -2.90 | 166.00 |  |
| 379 | HIVEUSDT | 615 | 1.77 | 6.33 | 40% | 49.3% | -0.134 | -82.578 | -0.7% | -0.060 | -3.26 | 399.00 |  |
| 378 | YFIIUSDT | 541 | 1.56 | 5.88 | 40% | 49.7% | -0.131 | -70.607 | -1.2% | -0.006 | -3.05 | 88.00 |  |
| 377 | FIOUSDT | 504 | 1.52 | 5.81 | 40% | 51.0% | -0.128 | -64.654 | -1.0% | -0.072 | -2.83 | 350.00 |  |
| 376 | AGLDUSDT | 1,095 | 3.18 | 6.20 | 41% | 51.1% | -0.128 | -139.640 | -0.8% | -0.081 | -4.29 | 242.00 |  |
| 375 | MOCAUSDT | 618 | 1.80 | 5.86 | 41% | 51.1% | -0.121 | -74.678 | -0.9% | -0.046 | -2.92 | 410.00 |  |
| 374 | NEIROUSDT | 671 | 2.05 | 6.26 | 39% | 51.7% | -0.120 | -80.531 | -1.2% | -0.023 | -3.22 | 98.50 |  |
| 373 | SFPUSDT | 1,901 | 5.60 | 6.32 | 38% | 51.2% | -0.117 | -222.426 | -0.9% | -0.095 | -5.10 | 179.00 |  |
| 372 | KEYUSDT | 517 | 1.49 | 6.74 | 35% | 51.1% | -0.115 | -59.427 | -0.8% | +0.032 | -2.43 | 172.00 |  |
| 371 | NILUSDT | 520 | 1.52 | 5.58 | 42% | 53.5% | -0.110 | -57.120 | -1.0% | -0.099 | -2.60 | 220.50 |  |
| 370 | VTHOUSDT | 573 | 1.69 | 5.79 | 42% | 51.8% | -0.109 | -62.457 | -0.7% | -0.055 | -2.61 | 442.00 |  |

## Most pattern-diverse coins (top 10 by effective patterns), with their results

| rank | symbol | n | years | eff patterns | continuation share | win pct | mean r | sum r | mean ret pct | mean r no stop | z | liq rank median | stable |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 384 | USDCUSDT | 1,153 | 3.56 | 7.43 | 33% | 42.7% | -0.233 | -268.998 | -0.0% | -0.066 | -7.34 | 265.00 | yes |
| 380 | FOOTBALLUSDT | 506 | 1.53 | 7.11 | 34% | 48.4% | -0.134 | -67.967 | -0.6% | +0.165 | -2.90 | 166.00 |  |
| 326 | GPSUSDT | 517 | 1.62 | 6.85 | 37% | 52.8% | -0.071 | -36.729 | -0.7% | -0.017 | -1.53 | 257.00 |  |
| 332 | PAXGUSDT | 518 | 1.52 | 6.77 | 35% | 45.9% | -0.075 | -38.749 | -0.1% | +0.424 | -1.33 | 59.00 |  |
| 372 | KEYUSDT | 517 | 1.49 | 6.74 | 35% | 51.1% | -0.115 | -59.427 | -0.8% | +0.032 | -2.43 | 172.00 |  |
| 344 | DEXEUSDT | 597 | 1.77 | 6.73 | 38% | 50.9% | -0.082 | -48.928 | -0.4% | +0.178 | -1.74 | 199.00 |  |
| 81 | LUNA2USDT | 1,284 | 4.06 | 6.73 | 34% | 56.2% | +0.003 | +4.044 | -0.2% | +0.145 | 0.10 | 152.00 |  |
| 333 | TUTUSDT | 500 | 1.54 | 6.70 | 34% | 51.8% | -0.075 | -37.407 | -0.5% | +0.296 | -1.52 | 263.00 |  |
| 99 | MUBARAKUSDT | 500 | 1.54 | 6.68 | 35% | 55.2% | -0.002 | -1.187 | -0.0% | +0.132 | -0.05 | 216.00 |  |
| 138 | CATIUSDT | 674 | 2.03 | 6.68 | 37% | 53.3% | -0.013 | -9.021 | -0.1% | +0.033 | -0.30 | 301.00 |  |

## Across coins (stables excluded)

- mean R vs pattern diversity: r = -0.16 (more variety, slightly worse)
- mean R vs continuation share: r = +0.19 (the coins that did best were the ones that trended: more 2-2 continuations)
- mean R vs liquidity rank: r = -0.14; vs years of history: r = +0.10
- spread of per-coin mean R: 5th pct -0.100, median -0.026, 95th pct +0.040
