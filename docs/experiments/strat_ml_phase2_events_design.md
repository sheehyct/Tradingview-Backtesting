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

## 9. Stop placement head-to-head (2026-10-20, owner's ask): setup-bar stop vs the skill's bar-0 stop

Built as a second event file (`events build --stop-mode bar0`; inside breaks take bar 0's far
side, bar 0 = the first non-inside bar walking back past any stacked inside bars; every other
pattern unchanged). Same 119,926 inside-break rows. Full tables:
`analysis/strat_ml/reports/stop_compare_2026-10-20.md`; the bar-0 report:
`strat_ml_report_2026-10-20_bar0.html`.

| inside breaks | win % | stop first % | target first % | mean ret % of price | mean ret (ATR) | median stop (ATR) |
|---|---|---|---|---|---|---|
| setup-bar stop | 54.3 | 44.9 | 50.1 | -0.2 | -0.013 | 0.57 |
| bar-0 stop | 61.7 | 35.0 | 55.2 | -0.2 | -0.010 | 0.84 |

Reading: the wider stop (0.84 ATR vs 0.57) turns ten points of stop-outs into timeouts and
target touches and lifts the win rate by seven points, and the money per trade does not
move: -0.2% of price under both, in ATRs -0.013 vs -0.010. Same shape in every pattern,
direction, class and year. The whole book: -0.3% mean return per trade under both stops.
So the stop decides HOW the book loses (many small stop-outs vs fewer, larger ones), not
WHETHER it loses; the earlier phrase "stop placement is the mechanism" refers to the shape of
the blue-sky cell, not to a lever that fixes expectancy. Model A on the bar-0 file behaves the
same as on the setup file (R-squared 0.18 in-sample, -0.01 out-of-sample).

## 10. The excursion clock (2026-10-20, owner's question: does the setup show a favourable move SOON, and can "it turned against me" become a rule?)

Declared grid, read as a spread: favourable thresholds 0.25R / 0.5R / 1R; clocks 6 / 12 / 24 /
48 / 72 hours after the trigger hour. New columns in the event table: `h_fav_x`, `h_adv_x`
(hourly bars from entry to the first touch of +x R / x R against, within the 10-bar window),
`first_excursion` (which 0.25R came first; tie = against), `mfe_r_Hh`, `mae_r_Hh`,
`r_close_Hh` (excursions and the mark at fixed clock hours). Reader:
`analysis/strat_ml/excursion.py`; tables: `reports/excursion_2026-10-20.md`.

- **How soon the move shows.** Half of all triggers show +0.25R within 6 hours and 71% within
  24; +0.5R: 24% within 6 hours, 49% within 24, 82% within the 10 bars; +1R: 23% within 24
  hours, 65% within 10 bars. The adverse side is a mirror image at 0.5R and 1R (50% / 19%
  within 24 hours). Inside breaks move soonest (57% show +0.5R within 24 h), outside breaks
  slowest (40%). "Eventually" is real: a third of the +1R touches arrive after day 3.
- **The trigger hour's own low is an artefact, and it is large.** Counting the trigger
  bar's full range (pessimistic, the low may precede the break), 68% of trades go 0.25R
  against before 0.25R in favour. Ignoring the trigger hour's adverse print, 70% go in favour
  FIRST (+0.085R mean, 60% win) and 27% against first (-0.23R, 45% win). Which number is
  true needs sub-hourly bars; the archive has 15-minute klines (same file count, 4x rows).
- **The time-stop rule does almost nothing.** "At hour H, if +x R has not shown and the trade
  is open, exit at that close": the book moves from -0.032R to between -0.017R (0.5R at 6 h)
  and -0.033R (0.25R at 24 h). The split is dramatic (trades that showed +0.5R within 6 hours
  average +0.31R; those that did not and are still open average -0.15R), but the exit mark
  of the laggards (-0.12R) is already most of their eventual loss. By the time the trade has
  "not moved", the price already says so; the rule saves about 0.02R per laggard.
- **The continuity surprise is the blue-sky cell.** `tfc_score` = 1 (week AND month already
  Type 2 in the trade's direction) has the worst mean R in every family (-0.08 to -0.11), and
  it is the no-rung set by construction: both prior levels are already broken, nothing
  structural sits beyond the entry (no_rung share 100% for continuation and outside breaks).
  The colour-only `bias_score` goes the expected way in every family (reversal: +0.009R at 1.0
  vs -0.033R at 0). Two readings of continuity, two opposite signs: colour agreement helps a
  little, "already extended through both levels" hurts. Both match the skill (continuity vs
  exhaustion risk).
- Majors (4,429 rows) hold +0.026R across the grid; alts -0.032R. Too few majors to split.

For the owner's rule-making: the data supports "a trade that has not shown +0.5R inside its
first day is a laggard" as a description, not as an exit rule; the money the rule saves is
small because the mark has already moved. The first-excursion split (+0.085R vs -0.23R) is
the stronger lead, and it needs 15-minute bars to be believed.

## 11. The pivot ladder (2026-10-20, owner: "this is where the drift is")

The owner's live Pine (TheStrat Magnitude + Targets) projects T1 = the reclaim level (the anchor
bar's wick) and T2.. = the prior highs / lows NOT yet taken out, nearest first, up to 250 bars
back. The daily research line (TVB-37/38) kept only the week's and month's levels ("no daily
pivots" ruling) and the Pine never trades the bare 2-2 continuation at all (40% of the rows
here). The Pine ladder is now ported to the daily rows in `events.py` (`pivot_ladder`, the
paper engine's Pine-exact construction; reach convention from the TVB-22 ladder census;
columns `pivot_*`, `h_rung1..3`, `r_managed_pivot_10`); reader `pivot_ladder.py`; tables
`reports/pivot_ladder_2026-10-20.md`.

- **How far price climbs.** Six rungs exist on 97% of rows. Within 10 daily bars the
  favourable extreme reaches rung 1 on 81%, rung 2 on 64%, rung 3 on 50%, rung 4 on 38%;
  mean 2.8 rungs. Median hours to rung 1 / 2 / 3: 6 / 27 / 50. Inside breaks climb fastest
  (rung 1 at a median 4 hours), reversals slowest (11 hours; their rung 1 is the anchor,
  further away at 0.44R). Stable year to year (2.7 to 3.0 rungs).
- **The 60,715 rows the TVB-37 ladder left without a target** get a rung from the Pine on
  45,713, and 60% of those reach it within 10 bars (median R:R 0.33).
- **The Pine's T1 against the TVB-37 T1, same rows, same stop, same walk.** Identical for
  every reversal (100% the same level). For the continuation, the with-trend inside break and
  the outside break the Pine's T1 is the nearest untaken daily extreme (R:R 0.32 vs 1.44),
  touched 72% vs 40%, and the managed mean R improves by +0.01 to +0.07 (1-1-2 stacked inside
  +0.066, 2-1-2 continuation +0.047, 2-2 continuation +0.014) while staying at or below zero
  (-0.004 to -0.016). The owner's open A3 question (mother bar's far side as T1 for the
  with-trend inside break): on these rows it lifts the inside family from -0.030 to -0.009R
  and the hit rate from 55% to 71%. Reading: the ladder gives every break a near target and
  makes the book flatter and more frequent; it does not make it positive per R.

## 12. The overfit and underfit ticker census (2026-10-20, owner's ask; labelled, never a promotion)

`ticker_census.py`; `reports/ticker_census_2026-10-20.md`. 384 coins with 500+ rows.

- **The yardstick.** A coin with 1,000 rows and no edge shows a mean R anywhere within about
  +-0.07 by chance. The top of the table (GUN +0.107, SONIC +0.105, CETUS +0.100, all ~500
  rows, z 1.8 to 2.1; SOLUSDT +0.066 on 2,008 rows, z 2.6, the most credible) sits at the
  edge of that noise. The overfit end is barely distinguishable from luck.
- **The underfit end is real.** USDCUSDT -0.233R (z -7.3) is a stablecoin perp: a universe
  hygiene miss, its "yesterday's high" is noise with a tiny R; exclude stables from the next
  build (`STABLES` in ticker_census.py). Behind it a genuine tail: SFP -0.117 (z -5.1), AGLD
  -0.128 (z -4.3), BAN -0.159 (z -4.2), TST, HEI (z -4). A losing coin is far more reliably
  identifiable than a winning one, which is the same asymmetry the model showed (it ranks
  losers, not winners) and the same one the stop comparison showed.
- **Diversity vs momentum.** Across coins, mean R vs the effective number of patterns r =
  -0.21 and vs the continuation share r = +0.23: the coins that did best were the ones that
  trended (more 2-2 continuations), not the ones that printed the most varied patterns. The
  owner's suspicion ("or were we just trading momentum really") reads as yes. The most
  pattern-diverse coins (USDC, FOOTBALL, GPS, PAXG) are mostly the losers.

## 13. Equity perps two ways (2026-10-20, owner: "the one thing we did not test")

Hyperliquid xyz dex (HIP-3), 115 perps (77 US-listed stocks / ETFs / index perps, 16 non-US,
11 commodity and FX, 11 unclassified), hourly candles via the census's own fetcher
(`hl_fetch.py`; the venue serves ~208 days, so the window is 2026-03-29 to 2026-10-09).
Two builds of the same table (`events.py --session calendar|rth`): the 24/7 UTC day (every row
so far), and the New York regular session as the STRAT daily bar (weekday local hours 9..15 only,
triggers scanned inside the session, weeks and months by the local calendar; the 9:00 hourly bar
holds the 9:30 open, an approximation). Same stop, same ladder, same 10-day walk over ALL hours
(a held position lives 24/7). Control: Binance crypto alts in the same months. Reader
`equity_perps.py`; tables `reports/equity_perps_2026-10-20.md`.

| US-listed perps | rows | win % | target first % | stop first % | mean R | median R | mean ret % of price | mean R no stop |
|---|---|---|---|---|---|---|---|---|
| 24/7 calendar day | 9,925 | 46.8 | 40.2 | 50.8 | -0.096 | -1.000 | -0.3 | +0.250 |
| NY regular session as the bar | 7,246 | 55.6 | 47.6 | 42.6 | +0.117 | +0.097 | +0.3 | +0.337 |
| crypto alts, same window | 111,306 | 52.9 | 47.0 | 44.4 | -0.059 | +0.042 | -0.5 | +0.066 |

- **On the UTC day the equity perps are the worst cell in the vessel** (-0.10R, 47% win, worse
  than crypto alts in the same months). 2,177 of the 9,925 US-listed breaks happen in the 20:00
  New York hour, the UTC day roll, in the thin after-hours when the underlying is closed and the
  oracle frozen: the "day" opens and the first basis wobble breaks "yesterday's" high or low.
- **On the session day the sign flips in every family:** continuation -0.15 -> +0.08, inside
  -0.11 -> +0.16, outside -0.04 -> +0.26, reversal -0.05 -> +0.12; longs +0.19, shorts about
  flat. Overall +0.12R, 56% win, 0.3% of price per trade before fees; the unmanaged view
  improves too (+0.25 -> +0.34). This is the first positive-expectancy cell the vessel has
  produced, and the only place so far where a bar definition changed the money.
- **Read it with the sample in view.** Seven months, 76 names, 7,246 rows that are strongly
  correlated across names on the same days (US equities move together), so the effective sample
  is far smaller than the row count suggests; the two builds are different trade populations
  (different setup bars), not a paired test; no fees; one regime (2026-03 to 2026-10).
- **Mechanism, as a hypothesis:** the charter says the equity / RTH orthodoxy must not be
  imported blindly for 24/7 perps. For an equity perp the underlying DOES close, so the session
  is the real bar and the UTC day is the artefact; the same reasoning, the opposite conclusion,
  for the opposite instrument. Commodity, FX and non-US names on the UTC calendar read like the
  US names (-0.06 to -0.11R); their own sessions are not built here.
- Next, declared before any run: (a) the owner's TVB-36 ruling was "no session calendar first,
  then look at what a calendar would have done"; this is that look, and it says the calendar
  matters for equity perps; (b) a paired version (same session-day setup bars, triggers allowed
  24/7 vs session-only) to separate "better bars" from "better hours"; (c) the venue's daily
  candles go back to each listing (Nov 2025), so a daily-resolution version can double the
  window at the cost of the hourly ordering; (d) refetch monthly, the hourly window rolls.
