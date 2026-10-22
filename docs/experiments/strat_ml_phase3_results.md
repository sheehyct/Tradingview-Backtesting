# STRAT trigger research: phase 3 results (stopped at the test-1 gate)

Built 2026-10-22 by analysis/strat_ml/report_v3.py from the corrected phase-1 event table (554,939 rows, 898 coins). Full page: analysis/strat_ml/reports/STRAT Trigger Research v3.md (and .html).

**Gate: FAILED. No family clears net 5-bar forward return > 0 with clustered z >= 2 on the test period (2025-26) after costs: continuation -0.085 ATR (-0.78% of price, -0.081R), z -2.3, n 118,267; inside -0.046 ATR (-0.39% of price, +0.003R), z -1.8, n 64,825; outside -0.035 ATR (-0.35% of price, -0.000R), z -1.0, n 25,985; reversal +0.010 ATR (+0.02% of price, +0.069R), z +0.3, n 85,976.**

## Verdicts, verbatim

- *0a. Headline numbers: as published, corrected, and after costs*: Verdict: contradicts -- dropping the stablecoin perps changes phase 1's headline materially, because the whole-book mean R moves by +0.0004 (+0.04 dollars per $100 risked) on 554,939 rows.
- *0b. The stablecoin perps dropped (logged to analysis/strat_ml/stablecoins_dropped.json)*: Verdict: supports -- the universe held stablecoin perps that drag the book, because 1 symbol(s) matched the rule, worst USDCUSDT at mean R -0.233 on 1,153 rows.
- *0c. Section 3f re-rendered: strongest feature pairs (interactions, model A refit on coded categoricals)*: Verdict: supports -- the BTC-vol regime feature also drives the strongest feature pairs, because the top pair is long or short x BTC 30-day realized volatility vs the last year (0-1) at 0.0195.
- *1a. Parameters*: Verdict: supports -- costs are on the order of half the phase-1 loss, because the mean cost is +0.176% of price per trade against a mean managed result of -0.331% of price (53% of the loss).
- *1b. Cost per trade by liquidity tier and family, phase-1 exits*: Verdict: supports -- any cell that reads positive before fees is at or under zero after them, because 2 of 12 cells (300+ rows) were positive before costs and 0 stay positive after; the mean cost is +0.029R per trade.
- *2a. Which 0.25R move came first: hourly clock vs 15-minute clock, same rows*: Verdict: supports -- the hourly 'against first' majority is an artefact of the trigger hour's own range, because against-first is 67.8% on the hourly clock and 55.7% on 15-minute bars with the trigger bar counted (47.5% ignoring the trigger bar's own adverse print; phase 1 estimated 27%).
- *3a. By family and horizon (the headline table)*: Verdict: inconclusive -- after a daily STRAT trigger price keeps going the break's way on average over 5 bars, net of costs (whole sample, by family), because every cell is inside its own noise, e.g. inside -0.029 ATR, z -1.7, n 117,267.
- *3b. By pattern and direction, 10-bar hold*: Verdict: contradicts -- after a daily STRAT trigger price keeps going the break's way on average over 10 bars, net of costs (by pattern and direction), because 1-1-2 stacked inside long -0.165 ATR, z -2.3, n 6,494 (the other 19 cells with 300+ rows are inside their own noise).
- *3c. By BTC 30-day realized-vol tercile and family, 5-bar hold*: Verdict: contradicts -- after a daily STRAT trigger price keeps going the break's way on average over 5 bars, net of costs in some BTC-volatility regime, because high vol continuation -0.101 ATR, z -2.3, n 60,925 (the other 11 cells with 300+ rows are inside their own noise).
- *3d. By year and family, 5-bar hold*: Verdict: contradicts -- after a daily STRAT trigger price keeps going the break's way on average over 5 bars, net of costs consistently across years, because 2022 inside -0.099 ATR, z -2.1, n 8,814; 2026 inside -0.064 ATR, z -2.2, n 33,940 (the other 26 cells with 300+ rows are inside their own noise).
- *3e. By liquidity tier, 5-bar hold*: Verdict: inconclusive -- after a daily STRAT trigger price keeps going the break's way on average over 5 bars, net of costs in some liquidity tier, because every cell is inside its own noise, e.g. tier 3 -0.031 ATR, z -1.9, n 441,132.
- *3f. Train vs test: by family and horizon (the gate table)*: Verdict: contradicts -- after a daily STRAT trigger price keeps going the break's way on average over 5 bars, net of costs on the unseen 2025-26 period (the gate), because continuation 5-bar -0.085 ATR, z -2.3, n 118,267 (inconclusive for inside 5-bar, outside 5-bar, reversal 5-bar).
- *3g. Train vs test: by BTC-vol tercile and family, 5-bar hold*: Verdict: inconclusive -- after a daily STRAT trigger price keeps going the break's way on average over 5 bars, net of costs in some BTC-volatility regime, on both train and test, because every cell is inside its own noise, e.g. high vol continuation -0.110 ATR, z -1.7, n 28,049.

## What the next phase should be

Next phase: the alt-coin line stops here; the HIP-3 session branch (brief section 11: test 1 on the session build clustered by date, leave-one-ticker-out, the gap rule, the fair-line sweep) is the next run, and the underlying-stock control needs an equity feed this environment does not have.
