# STRAT ML research vessel -- Phase 2 design: the event table (declared before the build)

Spec: the owner's `STRAT_ML_RESEARCH_SPEC.md` v0.1. Owner's word 2026-10-20: run it to the end,
cloud container, no Railway. This file fixes every definition BEFORE `analysis/strat_ml/events.py`
runs on data. Findings later are hypotheses, never conclusions (spec). Nothing is traded.

Plain-words version of what this phase does: for every coin and every day, look at whether
price broke yesterday's high or low, write down what the chart looked like the moment it broke
(the setup bars, the week and month so far, volatility, funding, what BTC was doing), then
watch the next ten days and write down how far the trade went for and against before it hit
the stop, the target, or ran out of time. One row per break. The ML phases then ask which of the
"what it looked like" columns go with the "how it went" columns.

## 1. Universe, bars, timing

- Every USDT perp in `universe_summary.json` (900, delisted included), each trimmed at its last
  real trade (`last_traded`). Majors = BTCUSDT, ETHUSDT; everything else = alt (spec default).
  Liquidity tier, point-in-time: the symbol's rank by trailing-30-day mean daily quote volume
  among all symbols on the day BEFORE the trigger (tier 1 = top 10, 2 = 11-50, 3 = the rest).
- Day = 00:00 UTC; week = Monday 00:00 UTC; month = the 1st (spec defaults, the census's
  calendar: `analysis/domino/census.py` week_start / month_start / aggregate). Daily bars are
  built from the hourly bars; the first calendar day of a symbol's data is dropped when it does
  not start at 00:00 (a partial first bucket, the census's rule). Hour gaps inside a day are
  kept and the day's `hours` count recorded; nothing is filled.
- Bar classification = `analysis/domino/census.py:classify` (strict break, equality never
  breaks; owner's ruling 2026-10-17 for this vessel). Setup bars are CLOSED daily bars; the
  trigger bar is read live from the hourly bars (skill invariant 1 and 6).

## 2. The trigger (one row per coin, day, direction)

- Long trigger on day D = the FIRST hourly bar of D whose high is strictly above day D-1's
  high. Short = the first hourly bar whose low is strictly below D-1's low. A day that breaks
  both sides gives two rows; both carry `opposite_also_triggered`. A perp's day opens at the
  prior close, which is inside D-1's range, so every trigger is an intraday break (no gap case).
- Entry level L = the broken level (D-1's high or low). Fill at L, no fees, no slippage, no
  funding paid (the TVB-37 convention; R is a measuring stick, not a P&L claim).
- `trigger_timestamp` = that hourly bar's open time; `hours_since_daily_open` = its index in the
  day (0-23); `day_of_week` from the daily bar.
- Dropped and counted: day D-1 unclassifiable (no D-2), setup-bar range zero.

## 3. Pattern label (from the two closed bars before the trigger day)

t1 = type of D-1 (the setup bar), t2 = type of D-2, read against the trigger direction:

| setup bar t1 | bar before t2 | name | family |
|---|---|---|---|
| 2 against the break | 2 (either) | 2-2 reversal | reversal |
| 2 against the break | 1 | 1-2-2 rev strat | reversal |
| 2 against the break | 3 | 3-2-2 reversal | reversal |
| 2 with the break | any | 2-2 continuation | continuation |
| 1 | 2 against the break | 2-1-2 reversal | inside |
| 1 | 2 with the break | 2-1-2 continuation | inside |
| 1 | 3, close colour against the break | 3-1-2 reversal | inside |
| 1 | 3, close colour with the break | 3-1-2 continuation | inside |
| 1 | 1 | 1-1-2 stacked inside | inside |
| 3 | any | 3-2 outside break | outside |

The raw three-bar code (`sequence`, e.g. `2D-1-2U`) is kept beside the name. The family is the
census's `setup_kind`. One name per direction, so "overlapping patterns on one bar" reduces to
the opposite-direction flag above (spec rule: keep, flag).

## 4. Geometry (the measuring sticks)

- **Stop / R** = the far side of the setup bar D-1 (D-1's low for a long, high for a short);
  R = |L - stop|. This is the TVB-37 products' R, so every number here reads beside the domino
  books. DECLARED ALTERNATIVE kept as a column, not used for labels: the skill's structural stop
  for an X-1-2 is bar 0's far side (D-2), not the inside bar's; `stop_alt_r` = that distance in
  R (equals 1.0 for every non-inside pattern). The owner can flip the label stop to it and
  rebuild (minutes).
- **Magnitude T1** = the TVB-37 management-book prereg definition 5, verbatim: 2-2 reversal /
  rev strat / 3-2-2: the far wick of D-2; inside break with D-2 against the break or a 3: D-2's
  far wick; with-trend inside break, continuation, outside break, stacked inside: the first
  ladder rung = the nearest of the previous complete week's and month's level (high for a
  long, low for a short) that is strictly beyond L and still unbroken in its current bar at the
  trigger hour. No rung = no T1 (`has_target` false; the row stays for MFE / MAE). The owner's
  open STOP-and-ASK on the with-trend inside break's T1 (mother bar vs ladder) is NOT ruled
  here; the ladder is the prereg's headline and is used as such.
- `setup_range_atr` = D-1's range / ATR; `stop_atr` = R / ATR; `t1_dist_r` = (T1 - L) / R
  signed in the trade's favour; `t1_dist_atr` likewise in ATR. ATR = 14-day Wilder on daily
  bars as of D-1's close. `atr_pct_1y` = percentile of that ATR in the trailing 365 daily bars
  (NaN until 60 bars exist).

## 5. Context as of the trigger hour (point-in-time, the spec's main leakage risk)

Everything below is computed from hourly bars strictly BEFORE the trigger hour, or from closed
higher-timeframe bars. The trigger hour's own range is never used for context.

- Partial week and month: open, high, low from the week's / month's first hour to the hour
  before the trigger (`w_partial_type`, `m_partial_type` = classify(partial, previous complete
  bar); NaN when the trigger is the first hour of the period). Direction = colour: the previous
  hour's close vs the period's open (`w_bias`, `m_bias` in +1 / -1 / 0).
- Prior completed week and month bar types (`w_prev_type`, `m_prev_type`).
- `tfc_score` (skill 4.3, direction-relative): share of {W, M} aligned, where aligned = partial
  type is 2 in the trigger direction (or 3 with the close colour in the direction) AND colour in
  the direction; Type 1, the wrong colour, or an empty partial = not aligned. Values 0 / 0.5 / 1.
  `bias_score` = share of {W, M} whose colour alone is with the trade (the cheaper definition).
- `breaks_week_too`, `breaks_month_too`: L is at or beyond the previous complete week's /
  month's level and that level was still unbroken in the partial bar (the census's domino rank).
- 4H: the 4H bar containing the trigger hour, partial through the hour before, classified
  against the previous complete 4H bar (`h4_partial_type`); `h4_broke_before` = that partial
  was already 2 in the trigger direction (or 3). 1H: the previous hour's type (`h1_prev_type`).
- Volume: `relvol_d1` = D-1 volume / mean of the 20 prior days; `relvol_prev_hour` = the
  previous hour's volume / mean of the prior 168 hours.
- Funding: `funding_last` = the last rate settled at or before the trigger hour; `funding_7d`
  = mean of the rates in the prior 7 days; `funding_pct_1y` = percentile of `funding_last` in
  the prior 365 days of rates.
- Open interest and taker ratios: NULL in this build (metrics not pulled for the universe;
  spec: leave null where missing).
- BTC: `btc_day_partial_type` (BTC's day so far vs BTC's prior day), `btc_w_bias`, `btc_m_bias`
  (BTC's colour vs its week / month open), `btc_rv30_pct` (percentile over 365 days of the
  30-day standard deviation of BTC's daily log returns, as of D-1). For BTCUSDT rows these
  describe the symbol itself.
- `symbol_age_days` = days from the symbol's first bar to D.

## 6. Outcomes (labels), hourly walk from the trigger hour

- Horizons h = 1, 3, 5, 10 daily bars AFTER the entry day: through the last hour of day D+h.
  `mfe_r_h`, `mae_r_h` (in R, from L, over hours k..end_h; the trigger hour is included),
  `mfe_atr_h`, `mae_atr_h`, `r_close_h` = (close at end_h - L) / R signed in the trade's favour.
- First touch inside the 10-bar horizon: the first hour whose low <= stop (long) and the first
  hour whose high >= T1 (touch fills, equality fills, the prereg's order convention). Earlier
  hour wins; the same hour = `ambiguous` and resolved STOP FIRST (pessimistic). A stop touched in
  the trigger hour itself is also ambiguous (the hour's low may precede the break). Result in
  `first_touch` in {target, stop, timeout} with `touch_hours` (hours from entry).
- `r_managed_h` = -1 if the stop came first by end_h, `t1_dist_r` if the target came first by
  end_h, else `r_close_h`. This is the label the ML phases use; `r_close_h` is the no-stop view.
- Rows whose data ends before end_10 are `censored` (horizons past the data NaN).

## 7. What the build writes

`analysis/strat_ml/data/events.parquet` (one row per trigger, all columns above; gitignored,
re-runnable from the parquet cache in minutes) and `analysis/strat_ml/events_summary.json`
(committed: row counts per pattern x asset class x direction, drops, build time). Rules kept:
no ticker as a feature (the ML phases get `asset_class`, `liq_tier`, `symbol_age_days`).

## 8. First run read-out (2026-10-20; hypotheses, not conclusions)

Build: 565,687 rows, 556,844 with a 10-bar outcome; target-first 53%, stop-first 44%, timeout
10%; 1.2% ambiguous ties. Report: `analysis/strat_ml/reports/strat_ml_report_2026-10-20.html`
(numbers in `report_numbers_2026-10-20.json`); `analysis/strat_ml/report.py` builds it.

- **A leak was caught by its own strength.** `opposite_also_triggered` (the day also broke the
  other side) ranked second in the first LightGBM fit. It is known at the END of the day, not
  at the trigger hour. It stays in the data as the spec's overlap flag and is excluded from
  every model (`LEAKS` in report.py). Lesson for later phases: a feature that is too good on
  a time split is a look-ahead until proven otherwise.
- **Geometry, not edge, drives "target before stop".** Reward-to-risk under 0.5R: 81-84%
  target-first in every family; over 3R: 8-15%. Mean R barely moves across those buckets
  (within +-0.2R). A model allowed to see the target distance scores AUC 0.81 on 2025-26;
  the same label without geometry still scores 0.72 because pattern and family proxy the
  target source (bar-0 wick targets are near, ladder targets are far). So the honest money
  question is the R regression on context only.
- **Context ranks the losers, not the winners.** Model A (context -> R, trained 2020-24):
  R-squared 0.17 in-sample, -0.01 on 2025-26 (the level shifted down), but the RANKING
  survives: the bottom decile of its predictions made -0.25R mean / 33% win on unseen data,
  the top decile +0.03R / 51%. Rank correlation is small (0.07). Reading: the chart context
  identifies breaks to skip far better than breaks to take; nothing in the top decile beats
  zero materially before costs. Top SHAP features: BTC 30-day realized-vol percentile (by
  far), the week-so-far bar type, direction, day of week, pattern, the coin's own ATR
  percentile, the week/month colour score, BTC's week colour.
- **The blue-sky break is the biggest single cell.** Rows with NO structural level beyond the
  entry (`t1_source = no_rung`: price already past last week's AND last month's extreme in
  the break direction; mostly 2-2 continuations): 59,130 rows, 30% win, -0.11R mean, median
  -1R, and worsening every year since 2023 (-0.21R in 2026). The stop is the mechanism: the
  setup-bar stop is hit 61% of the time against 50% for ladder rows, while the UNMANAGED
  close-to-close view of the same rows is slightly positive with a long right tail. In the
  skill's words this is exhaustion risk (clearing one timeframe's magnitude with no larger
  magnitude beyond); in TVB-37's words the setup-bar stop is again the suspect. Majors show
  the opposite sign on 393 rows (+0.40R): a question, not a verdict.
- **Majors vs alts (the spec's axis):** at the pattern level the two classes look alike
  within their bands; majors are 0.6% of rows (two coins), so most major cells are grey.
  The test period is 99.6% alts by construction (the universe doubled in 2025-26).
- **Year to year the aggregate is flat** (53-56% win, mean R within +-0.05 of zero every
  year); the regime shows up inside the model (BTC realized vol is the top feature), not in
  the headline rate.
- **Clustering** separates one bucket cleanly and it is the no-target bucket above (39k rows,
  23% win); the other five buckets differ by a few points of win rate only.
- **The three-question tree** splits first on BTC's 30-day realized-vol percentile, then on
  the week/month colour score and the week-so-far bar type; its best pre-2025 leaf (+0.28R)
  did not hold in 2025-26 (-0.06R). Rules are prompts for charts, not trade plans.

Open for the owner (next session, STOP-and-ASK items): whether to re-label with the skill's
bar-0 stop for inside breaks (`stop_alt_r` is in the rows, rebuild is minutes); whether the
blue-sky cell deserves its own declared arm in the domino book (a wider stop or a no-stop
clock on those rows); whether to pull metrics (open interest, taker ratio) for the alts the
trigger table actually uses.
