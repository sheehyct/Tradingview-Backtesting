# HANDOFF archive -- TVB-39 and TVB-40, with the three STRAT ML side threads of October 2026

> Archived 2026-11-02 (TVB-44, on the owner's word) from docs/HANDOFF.md, verbatim. Newest first:
> the three side threads (the STRAT ML research vessel: 2026-10-22 Phase 3 to the test-1 gate,
> 2026-10-20 Phases 2-5, 2026-10-17 the Phase 1 data layer), then TVB-40 (the amCharts trade
> viewer, the two-builder design-off) and TVB-39 (the trade viewer on its own candles and the
> lead's five candidates run as prereg amendment A2).

## Side thread 2026-10-22 (not a TVB session): STRAT ML research vessel, Phase 3 to the test-1 gate (STOPPED AT THE GATE, as the brief orders)

**Date:** 2026-10-22 (cloud session, branch claude/jolly-babbage-vlk7yz; the owner's brief
`docs/experiments/strat_ml_phase3_brief.md` is the spec: fixes, then test 1, then stop and report
the gate before tests 2-5)
**Status:** Test 1 run, gate FAILED on the alt-coin table. Tests 2-5 NOT run (the brief forbids
running them on alts "anyway"); the HIP-3 session branch (brief section 11) is the next run and
needs the owner's word.

- **Read first:** `docs/experiments/strat_ml_phase3_results.md` (the gate line and every verdict,
  verbatim) and the page `analysis/strat_ml/reports/STRAT Trigger Research v3.md` (or .html,
  self-contained, phone-readable; glossary first, a What-this-means above and a verdict below
  every table, every R after costs, every z clustered by trigger date).
- **Built:** `analysis/strat_ml/report_v3.py` (extends `report.py`, which is untouched: the
  phase-1 table is read through the phase-1 loader; the table helper refuses to render without
  its two texts; cost model as a config block; the gate as the first line of the page),
  `analysis/strat_ml/m15_check.py` (15-minute klines pulled into their own raw folder for a
  block-random 20,000-row sample), `tests/test_strat_ml_report_v3.py` (11 hand vectors: glossary
  verbatim vs the brief, clustered z, cost arithmetic and funding marks, the 15-minute walk, the
  gate rule). Data bootstrap per the brief's appendix reproduced phase 1's rows exactly
  (565,687 built, 9,595 censored, 556,092 with a 10-bar outcome; HIP-3 15,844 / 11,324).
- **Section-5 fixes:** 3f re-rendered (model A refit on integer-coded categoricals; top pair =
  direction x BTC 30-day realized-vol percentile); stablecoin drop caught only USDCUSDT (1,153
  rows, -0.233R; log `analysis/strat_ml/stablecoins_dropped.json`), the headline moves by
  +0.0004R; the v3 page is numbered in page order with the caveats last (the phase-1 outputs stay
  as published, per the brief).
- **Cost model:** mean cost 0.176% of price per phase-1 trade (53% of the -0.331% loss, the
  brief's "about half" holds); 0.02-0.04R per trade by tier; the two tier x family cells that
  were positive before fees are under zero after them; whole book -0.031R -> -0.054R after costs.
- **15-minute check (reported, not fixed):** against-first 67.8% on the hourly clock, 55.7% on
  15-minute bars with the trigger bar counted, 47.5% with its own adverse print ignored (phase 1
  guessed 27%). The hourly artefact is real but smaller than estimated; sections 7b-7c of phase
  1 read with the 15-minute version. The fav-first / adv-first split in mean R survives
  (+0.18R vs -0.23R after costs) and is partly mechanical (adverse first = nearer the stop).
- **Test 1, the gate: FAILED.** Held N bars with no stop and no target, costs paid, on 2025-26:
  continuation -0.085 ATR (-0.78% of price) at 5 bars, z -2.3 (significantly AGAINST the break,
  -0.158 ATR at 10 bars, z -3.2); inside -0.046 ATR, z -1.8; outside -0.035 ATR, z -1.0;
  reversal +0.010 ATR, z +0.3 (flat). Whole book -0.045 ATR at 5 bars, z -2.1. On 2020-24 the
  same cells were flat (whole book -0.001 ATR at 5 bars); the continuation drift was +0.03 ATR
  there and -0.085 on test, the regime story the brief named. No BTC-vol tercile, year or
  liquidity tier cell clears the bar either. Reading in trader terms: after a daily break on an
  alt, price does not keep going; in 2025-26 it leans back the other way, and no stop, target or
  trail can harvest a drift that is not there.
- **The R-unit trap, stated on the page:** "mean R no stop" at 10 bars reads +0.05R after costs
  (+0.09R before, phase 1's number) while the same rows are -0.38% of price and -0.03 ATR: the
  R clip is one-sided and tiny setup bars turn ordinary moves into many R. The gate is read in
  ATR, as the brief's worked example does.
- **Not available here:** an underlying-stock feed for the HIP-3 control (brief run 2) is not
  wired into the environment; the HIP-3 snapshot has no funding series (charged 0, flagged).
- **Next (the brief's order):** section 11, the HIP-3 session branch (test 1 on the session
  build clustered by date, leave-one-ticker-out, the gap rule, the fair-line sweep at n >= 300),
  on the owner's word; the alt-coin line closes unless the owner re-opens it.

- **Addendum 2026-10-24 to 10-27 (same thread, after the gate; exploratory cuts, no arms, nothing
  promoted):** (1) Test-1 drift cut by the continuity columns already on every row, train beside
  test: every higher-timeframe context cell FLIPS SIGN between 2020-24 and 2025-26. "Week or
  month inside but coloured our way" was the best cell on train (+0.13 ATR at 10 bars, z +3.2;
  the only managed cell at or above zero) and the worst on test (-0.11, z -2.9); full
  continuity (week and month both already 2 our way) +0.19 train / -0.14 test, managed book
  39% win in both periods (7 in 10 have no target left); the week-only domino break (the daily
  break also takes last week's extreme) is flat on train and one of the worst cells on test
  (-0.34 ATR at 5 days, z -2.4), but that is the day's geometry, not the week's trade. Reading:
  on alts, higher-timeframe context is a regime read, not a filter; what is stable across
  regimes is the WIN RATE by structure (week-with / month-against 41% both periods, both-coiled
  59-61% both), what flips is the drift. The skill's Tier C (week and month 2 against) reads
  -0.10 ATR on test, mildly negative on train. (2) Regime anchor days found by averaging the
  net 5-bar drift across all coins per trigger day: the market-wide days come in PAIRS, a day
  when every break failed followed within 48 h by a day when every break the other way ran
  (2024-11-04 -> 11-05/06; 2025-01-30/31 -> 02-01/02; 2025-05-04/06 -> 05-07/08). On the
  2025-10-10 liquidation day the mechanical book was short with the owner (502 shorts, 91% won,
  +0.73R after costs); the trap was 10-12, the bounce longs above the inside day with week and
  month both 2-down (Tier C), 7 of 9 stopped 4-5 days later. (3) The owner's visual review list:
  `analysis/strat_ml/reports/v3_visual_review_list.md` (and .csv, force-added past the *.csv
  rule): BTC, ETH, SOL, XRP, DOGE, ZEC on 20 anchor dates, entry / stop / target / outcome.
  (4) **A phone review page** (private claude.ai artifact, link NOT in the repo; source
  `analysis/strat_ml/phone_review/page.html`, data pack `build_pack.py` -> the gitignored
  `analysis/strat_ml/data/phone_review/`): every trade of those six coins on candles, two
  stacked panes (trade 1H/1D above, week or month context below) with the context bar drawn AS
  OF THE TRIGGER HOUR (partial bar from the hours before the trigger, the table's own rule),
  last bar's high / low and the period's open as lines, a blind mode (both panes stop at the
  trigger hour; "would take / would skip" recorded before the reveal; the score line averages
  the takes against the skips) and a verdict + note per trade kept in the browser, exported as
  text. Chart library: lightweight-charts 4.2.0 from a CDN (the owner's TVB-40 preference was
  amCharts for the desktop; the phone page is a format test, owner's word 2026-10-26). The
  owner's first read: the hard part on a phone is the multi-timeframe context; v2 is the answer
  to that. (5) `/adhd` skill added at `.claude/skills/adhd/SKILL.md` (owner's draft, verbatim).
  (6) The owner's market-data MCP server (underlying-stock bars for the HIP-3 names) is wired
  into cloud sessions now: daily bars for any US ticker, 200 bars (back to 2026-01-08 on
  2026-10-24, a ROLLING window), 60-minute bars 09:30-anchored but only ~24 trading days deep.
  So the brief's HIP-3 run 2 (the underlying control) is possible at DAILY resolution, and the
  bars should be pulled and frozen as a snapshot before late December, when the HIP-3 window's
  start falls off. (7) Two commits on this branch (9155973, f354eff) carry an AI attribution
  trailer against the spine's "no AI attribution" rule (the harness asked for it); later commits
  omit it; history not rewritten.
- **Owner's direction at close (2026-10-27):** move the research off alts (one market, two
  regimes, every context effect flipped between them) to an instrument class with many regimes
  (index futures or their ETFs, session bars, 15+ years) with the continuity arms declared as an
  ablation ladder BEFORE running; a $100 live data run on Hyperliquid (crypto 24/7 plus equity
  perps) is planned; the lead's ranking and the bar-definition warning for equity perps (UTC day
  -0.10R vs NY session +0.12R, section 13) are in the session transcript and summarised below.

### Open

- [ ] Merge `claude/jolly-babbage-vlk7yz` into main (PR on the owner's word) so the PC pull
      brings phase 3, the review list, the phone page source and the /adhd skill.
- [ ] HIP-3 session branch (brief section 11), on the owner's word; run 2 at daily resolution via
      the market-data server, bars frozen as a snapshot first.
- [ ] Design session for the next instrument set (index / ETF, session bars, multi-regime) and
      the continuity ablation ladder; prereg before code.
- [ ] The owner's blind calls from the phone page, pasted back, scored against the rows.
- [ ] XAUUSDT / XAGUSDT (Binance gold and silver perps) sit in the "alt" universe; a hygiene
      note like the stablecoin one, not applied.

---

## Side thread 2026-10-20 (not a TVB session): STRAT ML research vessel, Phases 2-5 run to the end (COMPLETE)

**Date:** 2026-10-20 (cloud session, branch ccr-84c65430-bqc01u; owner's word: run it to the end,
cloud container, no Railway)
**Status:** COMPLETE for the spec's v0.1 pipeline. Everything is exploratory; nothing is promoted.

- **Read first:** `docs/experiments/strat_ml_phase2_events_design.md` (definitions declared before
  the build; section 8 = the first read-out) and the report
  `analysis/strat_ml/reports/strat_ml_report_2026-10-20.html` (self-contained, phone-readable,
  plain-words explainer on every section; also published as a claude.ai page for the owner).
- **Built:** `analysis/strat_ml/events.py` (one row per coin, day, direction; the census
  strict-break classifier and calendar reused; TVB-37 R and magnitude ladder; point-in-time
  week / month / 4H context; hourly-resolved outcomes at 1 / 3 / 5 / 10 daily bars, stop-first
  on ties), `analysis/strat_ml/report.py` (baseline tables with counts and Wilson bands, k-means,
  LightGBM + SHAP on a 2025-01-01 time split, depth-3 tree, HTML), 9 hand-vector tests.
  565,687 rows in 77 s; the report in 72 s. Cache (events.parquet) is per-container; the
  roster and the summary JSONs are committed.
- **Findings (hypotheses):** (1) a look-ahead feature was caught by ranking too high and is now
  excluded; (2) target-before-stop is mostly target distance, so the money question is modelled
  on context only; (3) context ranks the losers (bottom decile -0.25R on 2025-26) far better
  than the winners (top decile +0.03R); BTC's realized-vol percentile is the top feature;
  (4) the blue-sky break (no week / month level beyond the entry; 59k rows) loses -0.11R with
  the setup-bar stop hit 61% of the time, while its unmanaged view is slightly positive: a
  stop-placement question, the TVB-37 suspect again; (5) majors and alts look alike per pattern
  within their bands, but majors are two coins and the test period is 99.6% alts.
- **Stop head-to-head DONE (owner's ask, same day):** `events build --stop-mode bar0` + 
  `compare_stops.py`. On the same 119,926 inside-break rows the bar-0 stop (0.84 ATR median)
  lifts the win rate from 54% to 62% and cuts stop-outs from 45% to 35%, and the mean return
  per trade is -0.2% of price under BOTH stops; whole book -0.3% under both. The stop shapes
  the loss, it does not remove it. Design doc section 9; `reports/stop_compare_2026-10-20.md`.
- **Excursion clock DONE (owner's question, same day):** new columns (`h_fav_x`, `h_adv_x`,
  `first_excursion`, `mfe/mae/r_close_{6,12,24,48,72}h`) and `excursion.py`. Half of triggers
  show +0.25R within 6 h; a time-stop rule saves ~0.02R per laggard because the mark already
  carries the loss; the first-excursion split (+0.085R vs -0.23R) is the lead but the trigger
  hour's own low is an artefact that needs 15-minute bars. `tfc_score` = 1 is the blue-sky
  set by construction. Design doc section 10.
- **The lead's read of the whole book, 2026-10-20 (owner asked "what would you change, what
  would you test next"; advice, not rulings; grounded in the event table):**
  (1) The setup-bar stop (median 0.74 ATR) sits inside the daily noise: the median trade is
  0.9R against by day 3 and 1.6R by day 10. With no stop at all the book marks +0.09R (alts) /
  +0.23R (majors) at 10 bars against -0.03R managed, median still negative: the same shape
  TVB-38 found on Hyperliquid (+0.5..0.9 per trade from the stop swap). Widening to bar 0
  does not change the expectancy; removing the price stop does, and buys a tail.
  (2) The blue-sky break (no week / month level beyond the entry) is the worst cell WITH the
  stop (-0.10..-0.17R, stopped 59-74%) and the best cell WITHOUT it (+0.09R continuation,
  +0.30R inside break, unmanaged). The stop is chopping out the trend trades.
  (3) The owner's hazard (lower-timeframe entries inside higher-timeframe inside bars) does
  NOT show in the aggregate: month-inside / week-inside is the flattest cell (0.00R, n 103k);
  the bad cells are extension (month 2U with week 2U -0.09R, week 3 -0.14R). A confirmation-
  bias check the owner asked for in their preferences.
  (4) BTC's 30-day realized-vol percentile is the strongest regime feature: top decile -0.09R
  managed / -0.10R unmanaged, bottom decile +0.24R unmanaged.
  (5) Longs and shorts flip sign by year (2021 longs +0.09R, 2022 shorts +0.11R, 2025 longs
  -0.13R): the year's trend, not the pattern.
  What the lead would test next, in order, each a declared arm, never a pick: (a) replicate
  the TVB-37/38 chance book and management book rule-for-rule on the Binance table (different
  venue, 2020-2026, dead coins in) to see whether the stop-swap lift and the stacked
  continuation survive out of venue; (b) a pre-committed skip-list arm (skip blue-sky breaks,
  skip BTC top-vol-decile days) against the control, in the ablation shape; (c) the no-stop
  book with a declared tail rule (the hourly clock or an ATR-scaled disaster stop at 2-3 ATR)
  since the tail is the price of (1); (d) 15-minute bars to settle the first-excursion split.
  Not worth more time: exit clocks (the hourly, under-water and time-stop variants all move
  the book by a few hundredths of an R).
- **The original Pine (TheStrat Magnitude + Targets, the owner's live indicator) read against the
  table, 2026-10-20 (owner's ask; thoughts, not rulings):** its "star" (high-conviction) setups
  cut from the daily rows: Shot-Gun 2-2-2 (42k rows: 71% win, target-first 70%, mean -0.00R,
  median reward-to-risk 0.38), 1-2-2 rev strat (32k: 72% win, -0.03R, R:R 0.31), 1-3-2 (15k:
  48% win, -0.05R), 3-2 Boom on a hammer / shooter proxy (2.2k: 52%, -0.07R), 1-3 one-bar rev
  strat (18.7k; the setup-bar stop is ALREADY inside the day's range for a 1-3, so its -0.14R is
  a stop artefact; rerun on the bar-0 file). Star vs the rest: 64% win vs 52%, the same money
  (-0.04R vs -0.03R managed, +0.09R both unmanaged); unmanaged, the stars beat the rest in
  2020-22 and lost to it in 2023-25. Reading: the high-conviction patterns win MORE OFTEN
  because their targets are the reversal anchor (closer), not because they pay more per unit
  of risk; win rate is what a discretionary trader feels.
  Parts of the Pine that the daily research line never carried, each testable on the table:
  (1) the pivot ladder beyond T1 (prior highs / lows not yet taken out, nearest first, 250 bars
  back): the management book holds week / month levels only ("no daily pivots" ruling) and
  59,130 rows have NO target at all; (2) the Potential-3 / invalidation status (the other side
  of the setup bar breaks AFTER entry): the table carries both triggers' hours, so "exit at the
  hour the other side breaks" is a declared exit arm against the stop, cheap to run; (3) the
  2-1-2 momentum filter (inside bar in the upper / lower half of the prior 2's range) as a
  flag; (4) the chop counter (reversals since the last target hit) as a symbol-level regime
  feature. The BF harvest exit belongs to the TFC indicator, not this Pine, and cannot be read
  from the table without the BF line logic.
- **PR #3 opened on the owner's word** (https://github.com/sheehyct/Tradingview-Backtesting/pull/3):
  the whole vessel, branch ccr-84c65430-bqc01u into main.
- **Pivot ladder ported (owner: "this is where the drift is"):** the Pine's ladder on the daily
  rows (`events.py:pivot_ladder`, `pivot_ladder.py`). Rung 1 reached 81%, rung 2 64%, rung 3 50%
  within 10 bars, mean 2.8 rungs; the Pine's T1 gives 45,713 of the 60,715 no-target rows a
  target and lifts the continuation / inside cells by +0.01..+0.07R, all still at or under
  zero. The A3 question (mother bar as T1 for the with-trend inside break) has its number:
  inside family -0.030 -> -0.009R, hit rate 55% -> 71%. Design doc section 11.
- **Ticker census (owner's ask, labelled overfit):** the top coins sit at the edge of noise
  (z about 2), the bottom coins are real (z -4 to -7); the best coins are the trending ones
  (continuation share r +0.23), not the pattern-diverse ones. USDCUSDT is a stablecoin perp in
  the universe: exclude stables on the next build. Design doc section 12.
- **Equity perps two ways (owner: "the one thing we did not test"):** the xyz dex's 115 perps
  fetched through the census's own fetcher (`hl_fetch.py`, ~208 days of hourly bars, roster
  `xyz_summary.json`), the builder given `--session calendar|rth` and `--roster`. US-listed
  perps on the UTC day: -0.096R (the worst cell in the vessel; 2,177 of 9,925 breaks in the
  20:00 NY roll hour). The NY regular session as the STRAT bar: +0.117R, 56% win, every
  family flips sign, +0.3% of price per trade before fees. The first positive cell in the
  vessel, on a 7-month, 76-name, cross-correlated sample: a lead, not a finding. Design doc
  section 13 lists the declared next tests (paired bars-vs-hours, the daily-candle window back
  to listing, a monthly refetch).
- **PR #3 close-out (2026-10-20):** main (TVB-40) merged into the branch, the HANDOFF conflict
  resolved by keeping both entry sets; Codex's four PR findings (partial-download build, hourly
  gaps inside the outcome window, winsorization bounds leaking test labels, a denominator
  mismatch) fixed in 884e2cf, every receipt rebuilt (numbers within rounding), threads answered
  and resolved; `page.py` now assembles the phone page from the receipts. The PR reads clean
  and waits only on the owner's merge.
- **Phase 3 is briefed (owner, 2026-10-21):** `docs/experiments/strat_ml_phase3_brief.md` is the
  complete spec for the next cloud session (opening prompt inside it); its appendix carries the
  environment bootstrap (the data re-pull, what the brief assumes that is not on disk: no
  15-minute bars, the event table is built by events.py). Merge PR #3 before starting it.
  Data pinning (owner, 2026-10-22, option 1): the HIP-3 hourly bars are committed as a frozen
  snapshot (`analysis/strat_ml/snapshots/xyz_2026-10-20/`, 22 MB, gitignore exception;
  `hl_fetch --from-snapshot`), the Binance pull is pinned with `--until 2026-10-16`. A bucket
  for the whole cache (option 2) is deferred until more cloud sessions are planned.
- **STOP-and-ASK for the owner before more code:** exclude stablecoin perps from the
  universe (USDC, FDUSD, BUSD, TUSD, USDP, DAI, USD1)? pull 15-minute klines for the universe (same
  file count as 1h, 4x rows, ~2.5 h) to settle the first-excursion question? Make the blue-sky cell a declared arm in
  the domino book (wider stop / no-stop clock)? Pull metrics (OI, taker ratio) for the alts the
  trigger table uses? The with-trend inside break's T1 ruling is still open (ladder used).
- **Dependencies:** lightgbm, shap, scikit-learn added to pyproject (uv sync is safe; VectorBT
  Pro retired 2026-10-17).

---

## Side thread 2026-10-17 (not a TVB session): STRAT ML research vessel, Phase 1 data layer (COMPLETE)

**Date:** 2026-10-17 (cloud session, branch ccr-84c65430-bqc01u)
**Status:** COMPLETE for Phase 1 of the owner's `STRAT_ML_RESEARCH_SPEC.md` v0.1: data
acquisition only. Exploratory research, nothing deployed. No event detection, no bar
classification written (the owner's rule: reuse the existing classifier when Phase 2 starts).
TVB numbering untouched; the TVB-40 startup prompt still governs the main thread.

- **Plan and findings:** `docs/experiments/strat_ml_phase1_data_plan.md` (read this first).
- **Code:** `analysis/strat_ml/binance_vision.py` (S3 listing, checksum-verified raw zip cache,
  parquet build, point-in-time universe manifest; CLI `fetch` / `build` / `universe` / `status`),
  13 offline tests in `tests/test_strat_ml_binance_vision.py`, thread log
  `analysis/strat_ml/RESEARCH_LOG.md`. Cache under `analysis/strat_ml/data/` (gitignored).
- **Archive facts (USDT-M, futures/um):** delisted perps ARE in the archive (SRM, LUNA, BTCST,
  17 SETTLED stubs excluded); klines monthly from 2020-01 (daily from 2019-12-31; Sep-Dec 2019
  absent), fundingRate monthly only from 2020-01, metrics daily only (5-minute rows) from
  2021-12-01 for most names, BTCUSDT backfilled to 2020-09-01 with every row doubled.
- **Finding that changes Phase 2:** Binance keeps publishing flat zero-volume files for dead
  contracts (SRMUSDT: last real trade 2022-11-15, files to 2024-05; BTCSTUSDT frozen at one
  price 2024-02 .. 2026-06). Delisting is read from volume (`last_traded` in each klines
  manifest), never from file presence; the listing-based universe flag (31 of 900) is a floor.
- **Test slice pulled:** BTC, ETH, LINK, DOGE, SOL, AVAX, SRM (delisted), 1h klines + funding,
  full history, 1,070 files, zero errors; table in the plan doc section 5.
- **Cloud-session gotcha:** `data.binance.vision` is refused by the egress proxy; the bucket
  endpoint `s3-ap-northeast-1.amazonaws.com/data.binance.vision` works and the module tries
  both in order. The live API is unreachable and never used.
- **`uv add pyarrow`** touched pyproject/uv.lock: on the workstation reinstall VectorBT Pro
  from the cached wheel after the next `uv sync` (standing gotcha).
- **Full-universe pull DONE (owner's go-ahead, same day):** 900 USDT perps, 57,319 files,
  0 errors, ~2.5 h; 160 symbols delisted by volume (the listing-based flag said 31), 108 of
  them with a year or more of real history; the committed roster is
  `analysis/strat_ml/universe_summary.json`; plan doc section 6 has the counts. The raw /
  parquet cache (1.9 GB) is per-container: a later cloud session re-pulls (~2.5 h, free), or
  the workstation runs the two CLI commands once and keeps it.
- **Owner rulings 2026-10-17:** Phase 2 imports `analysis/domino/census.py:classify` (strict
  break) with its calendar bucketing, not the scanner's EXP-013 code; VectorBT Pro is RETIRED
  (licence not renewed, nothing imports it; CLAUDE.md gotcha rewritten; the workstation session
  should save this to private memory); no Railway for pulls (cloud container or workstation).
- **Remaining OPEN:** spec open decisions 1-2 and 4 assumed at their defaults (`analysis/domino/census.py:classify`
  strict-break, prereg'd on perps, is the lead's suggestion; the pine-exact
  `analysis/paper/patterns.py` and the scanner's EXP-013 code in the other workspace are the
  alternatives); metrics (open interest, taker ratios)
  not pulled for the universe (~1.3 M daily files; pull for the trigger subset in Phase 2).

---

## Session TVB-40: the charting upgrade: the amCharts trade viewer, built as a two-builder design-off and promoted (COMPLETE)

**Date:** 2026-10-14 to 2026-10-17
**Status:** COMPLETE on the owner's call of 2026-10-17 ("I say move forward with this ...
pushing this out first would be the ideal scenario just to be able to trade review quicker,
though I would include the universe for comparison"). Two builders prototyped the same thing in
parallel, each in its own folder (CLAUDE `proto_claude/`, CODEX `proto_codex/`); the owner
reviewed both and chose CLAUDE's ("night and day"). `analysis/domino/viewer/` is now that page;
the TVB-39 lightweight-charts page is retired (in git history to da7f4c2). The page's receipt is
`analysis/domino/viewer/NOTES.md`; the viewer section of `MANAGE_RECEIPT.md` points to it.
`proto_codex/` is untracked and untouched (the owner may still take ideas from it).

### What was accomplished

- **Round one (e79f8d3, 2026-10-14)**: the reference rows on amCharts 5 Stock Chart (data
  grouping off), the library's drawing toolbar with its own save / restore per coin, System
  levels as read-only axis ranges, the week's and month's closed-bar STRAT type as chips (R10
  operators, checked in Python), drawings proven across reload and timeframe switches.
- **Round two (da7f4c2, 2026-10-15), the design-off**: a calendar (census weeks, equal-size
  dollars per entry day, week totals, year strip) and a sortable trade table in place of the
  card strip; a facts strip; the trade narrated in trader language from the row (setup and
  magnitude source, the plan with every touch day, what the book did and the exit-day test, the
  other clocks, travel); a six-book ladder per trade; a Compare tab (KPI cards, overlaid equity,
  distribution against the chance book, by-setup with D5 minus the chance book); a Playbook tab;
  dual chart panes; stacked tags and markers. Compare figures cross-checked against Python on BTC.
- **Promotion (this session, 2026-10-17)**: the page moved to `viewer/`; `trade_viewer build`
  vendors amCharts 5 (the CDN needs a browser-like agent) and writes `data/universe.json`
  (every coin's rows, columnar, 15 MB) so the Compare tab and the all-coins calendar have a
  universe scope with every book and every filter; the universe figures agree with the engine's
  CSV in pandas to the printed precision (returns stored to three decimals); the magnet ray is
  back as a magnet mode that drops the library's own Horizontal Line at the nearest open / high /
  low / close (saved, moved and erased with the other drawings; proven exact on BTC 03-25);
  `test_domino_viewer` reads the calendar functions from `core.js`. Ruff clean, 372 passed, 2
  skipped.

### Context for next session

- The viewer is `analysis/domino/viewer/`: `uv run python -m analysis.domino.trade_viewer serve`
  (port 8765, opens the browser); from the laptop, `serve --no-open` on the desktop and
  `ssh -L 8765:127.0.0.1:8765 <desktop>` then `http://127.0.0.1:8765/`; on a machine without
  `viewer/data/`, `build --as-of 2026-10-10` first (and `hourly --as-of 2026-10-10 all` for the
  1H view, ~9 min). `build` also vendors amCharts and writes the universe table.
- The page reads rows and never computes them; `core.js` holds the TVB-39 row logic as it was,
  so the TVB-39 audit's viewer findings (F4 the reconstructed fill price as an exact touch
  threshold with a first-candle fallback, F5 the reference stop exit drawn at the end of the
  day, F6 the silent book-C fallback when the selected book has no result, F7 the stack class
  label) carry over to this page until they are adjudicated.
- Drawings live in browser storage per coin and pane (`am5-stock-domino-<coin>-drawings`,
  `...-<coin>-b-drawings`); the retired page's rays (`domino-viewer-rays:<coin>`) are not read.
- `proto_codex/` is untracked and untouched; `User_Notes.md` stays untracked.
- HANDOFF.md is over the 1,500-line limit at close (1,556 lines); archiving waits for the
  owner's word.

### Files created/modified

- `analysis/domino/viewer/`: `index.html`, `app.js`, `core.js`, `story.js`, `stats.js` (the
  page), `NOTES.md` (its receipt), `shots/` (17 PNGs); the TVB-39 `index.html` / `app.js` removed
- `analysis/domino/trade_viewer.py` (amCharts vendor fetch with a browser-like agent,
  `universe_table`, docstring)
- `tests/test_domino_viewer.py` (reads the calendar functions from `core.js`)
- `analysis/domino/MANAGE_RECEIPT.md` (viewer section: the promotion paragraph)
- `.gitignore` (the proto_claude vendor line removed; `proto_codex/vendor/` ignored)
- `docs/HANDOFF.md`, `docs/reviews/REVIEW_REQUEST.md`, `.session_startup_prompt.md`
- `docs/reviews/tvb39-codex-audit.md` committed as returned (captured 2026-10-14; the
  synthesis is the next session's first item)

### Open

- [ ] TVB-39 Codex audit synthesis: F1 HIGH (the hourly entry accepts equality and can exit
      before the trade exists), F2-F8 MEDIUM; agree / dispute / act in HANDOFF, fold, rerun
      `manage` if the engine changes, then `trade_viewer build`
- [ ] The with-trend inside break's T1 STOP-and-ASK (the owner rules; amendment A3 before code)
- [ ] Viewer: a journal layer (a note and a one-tap verdict per row, on the calendar and the table)
- [ ] Viewer: one drawing slot across both panes; the retired page's rays imported once
- [ ] Viewer: an hourly archive beyond the venue's ~208 days
- [ ] HANDOFF.md archive (over the limit; the owner's word)
- [ ] `proto_codex/` disposition (delete, or keep for ideas; the owner's call)

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb40-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED 2026-10-29 (`docs/reviews/tvb40-codex-audit.md`, NEEDS-CHANGES, six MEDIUM, all display / readback; synthesis pending)
- Commits to review: `9f6c5c8..2c7fe1c` on `main` (9f6c5c8 is the pre-session sha, so the
  range holds e79f8d3 round one, da7f4c2 round two and 2c7fe1c the promotion; it also contains
  the two maintenance pull requests merged 2026-10-16 (45f83fc, 2dde483, 706cb3d, 46de307:
  cloud hooks and the safety guard, with their own HANDOFF entries), which are not viewer
  work; the session-end docs commit after 2c7fe1c is docs only). Sanity-check:
  `git diff --name-status 9f6c5c8..2c7fe1c` lists every file the session touched.
- Scope / what changed: a new viewer page on amCharts 5 (five files, a receipt, proof shots),
  the build script's vendor fetch and universe table, one test path, the receipt's viewer
  paragraph. No engine, prereg or results change.
- Focus areas (scrutinize these): the founding rule (`core.js` `settle` / `tradeSpan` /
  `stackLevels` / `setupDays` against the TVB-39 `app.js` and the row semantics, including the
  TVB-39 audit's F5-F7, which this page inherits); `stats.js` arithmetic (drawdown order,
  target and days semantics per book, histogram bins) against `manage.py`; `story.js` claims
  per book against the row columns (`hit_X`, `days_X`, `out5`, `exit_k_u`, the exit-day test,
  the Monday one-test case) and the closed-bar chip definition (R10, closed bars only);
  `universe_table` (code books, -1 sentinels, three-decimal rounding, day numbers) and its
  decoding in `fromUniverse`; the magnet's coordinate math (`toAxisPosition` over
  `axisLength`) and the proof flag; the Playbook's receipt numbers; hygiene (vendor and data
  gitignored, the CDN agent string, no private link in the repo, `proto_codex/` untracked).
- Reviewed by: Codex (local, via SSH), 2026-10-29
- Findings: F1 Compare drawdown measured row by row instead of on daily sums (engine does daily); F2 magnet picks the next candle on the right half of a candle; F3 exit narration: hourly clock worded long-only on 27,674 short rows, open rows told they "left with the daily clock", same-day stop / one-R ties told "before one R"; F4 best / worst travel is book C's window whatever book is selected; F5 calendar month average divides by all rows, censored rows count as zero; F6 changing the book does not re-sort the table. All six confirmed against the source on receipt; synthesis + repairs with the TVB-39 viewer findings F4-F7.

---

## Session TVB-39: the trade viewer (every row on its own candles, locally) and the lead's five candidates run as prereg amendment A2 (COMPLETE)

**Date:** 2026-10-12
**Status:** COMPLETE -- two pieces on the owner's word of 2026-10-12: "You may run your 'would
test next'", and a request to start implementing a local chart tool so the rows can be checked
visually without TradingView ("visually verifying via TradingView is one of the most time
consuming tasks, almost impossible to accurately do ... the numbers were there and seemed right
until visually verified, which showed inaccuracies"), styled like the owner's screenshot (grey
context candles, the trade's candles coloured, opened / closed lines, a strip of trade cards,
1H / 1D / 1W / 1M toggles). Both delivered, pushed. The owner began their own pass the same
evening on the viewer (two BTC trades walked, section below): three viewer additions and one
viewer bug fix came out of it, plus one STRAT STOP-and-ASK question (the with-trend inside
break's T1) that is OPEN, and two direction signals from the owner recorded below (the
daily-close exit is likely to be retired; higher-timeframe inside bars are the hazard the domino
test was meant to answer). Nothing is promoted; nothing is read into the hierarchy rulings.

### What was accomplished

- **The trade viewer** (`analysis/domino/trade_viewer.py` + `analysis/domino/viewer/`): a local
  page served on localhost that draws the management book's recorded rows on the census's raw
  candles. It re-runs NO trade logic: the entry day, targets, touch days, exit day and every
  book's fill come off `manage_trades.csv.gz` as the engine wrote them, so a chart that
  disagrees with a row is evidence against the engine. One coin at a time or every trade
  entered on one day across coins; 1H / 1D / 1W / 1M (weeks and months bucketed by the census's
  calendar rules, tested against `census.week_start` / `month_start` through node); candles not
  in a trade grey, the setup bar amber, the bar before it dark amber, the trade's candles green /
  red by close; lines for the entry level, the exit close, T1 / T2 / T3 with sources, one R, the
  setup-bar stop, the measured move; markers on the first bar (hour, on the hourly view) that
  touched each price; the exit day's test spelled out (close against the day's open and the
  week's open, with colours); every book's fill; the two A2 exits (under water on the daily,
  the hourly clock on the hourly view); filters (unit timeframe, kind, side, liquid, has T1),
  book and equal-size selectors for the printed P/L; arrow keys; bookmarkable addresses
  (`#coin=BTC&date=2025-06-17&tf=D&dir=down&view=1D`, the receipt's worked example). On the
  owner's first pass (BTC 2026-03-27 weekly short: "we hit T1, no exit") three additions and
  one fix, same day: the book box now drives the chart (candles, closed line and out arrow at
  the selected book's own settle day and fill, read off the row; the headline clock kept as a
  small square); every timeframe that broke the same day is drawn with the gap band and a
  "domino" label on a converged stack (the chart's calendar level checked equal to every row's
  recorded level, all 179,498 units); a magnet ray tool (Draw / R, snaps to the bar's OHLC on
  the active view, persists across timeframes per coin); and the misplaced "data ends" marker
  (the A2 markers had split the exit arrow's `if` from its `else`) fixed. `serve` takes
  `--host` and `--no-open` for the owner's laptop over SSH / Tailscale. Hourly
  candles fetched for all 292 coins (the venue serves ~208 days) into the census cache, stamped.
  Recipe in the receipt's viewer section: `hourly --as-of ... all` (once), `build --as-of ...`,
  `serve`. The data folder and the vendored chart library are gitignored and regenerable.
- **Prereg amendment A2, declared before code (f505f9d):** the five candidates restated in
  trader terms, each one change on the same trades, with readings R1-R5 and vectors v16-v19
  written first. One sentence was corrected while writing v17, labelled in the prereg: a target
  on the trade's side cannot be touched before the level, so the hourly ordering difference is
  on the EXIT day (the daily bar fills any touch that day, the hourly clock only up to the exit
  hour).
- **Engine (`manage.py`):** the under-water exit recorded on the same walk (`exit_u`, books
  C_u / A_u / D_u); the hourly clock (`walk_hourly`: entry hour = first hour reaching L; exit =
  first hour closing against its own open AND the day's open; cap = the last hour of day 20;
  censored when the hours end; books C_h / A_h / D_h) on the hourly-window subset; book E and
  the fees as arithmetic on the recorded columns; the week's side as a split of every book.
  Hourly helpers (`fetch_hourly`, `cached_hourly`, `normalize_hourly`, `HOUR`) live in
  `census.py`. `candidates()` + `table_candidates()`; `manage.json` carries a `candidates`
  block; the CSV carries the new columns. Offline rerun as before (`--as-of 2026-10-10`, ~10
  min with the hourly). Headline numbers did not move (same rows, same walk; the hourly and
  under-water columns are additions).
- **Receipt** (`MANAGE_RECEIPT.md`): a viewer section and an A2 section (what each candidate
  did, in trader terms, against its declared reading). **Ledger** card extended. **Page**
  republished (version 5) with a candidates section. 23 manage vectors + 7 A2 vectors + 4
  viewer tests; full suite green.

### The five, against their declared readings (plain daily, the book cohort)

- **R1 the week's side at entry: NOT a general condition.** With beats against on the reversal,
  the continuation and the outside break (reversal C +0.28 with / +0.13 against; continuation
  C -0.20 / -0.53), but the inside break pays MORE against the week (A +0.18 / C +0.16 / D +0.38
  against; -0.07 / -0.13 / +0.16 with) and reaches T1 nearly as often. The declared rule said
  one reversal of the split means it is not a condition. An inside-bar break against the week is
  a counter-trend break with the week's open ahead as a level: a pattern-specific read.
- **R2 the hourly clock: a different trade, not a better one.** On ~38k trades inside the
  hourly window: held 9-11 hours against 48-72; every trade exits inside the cap; losers shrink
  to less than half (-1.5..-1.9 against -3.8..-4.9); T1 before the exit falls by a third to a
  half. Net paired (rerun 2026-10-30 under the repaired walker, TVB-39 audit F1-F3; the
  original read -0.14 / 0.00 / +0.21 / -0.27): C_h - C reversal -0.12 [-0.26, +0.03],
  continuation 0.00, inside +0.23 [+0.06, +0.40], outside -0.26 [-0.58, +0.06]; A and D within
  about a tenth. The declared expectations (sooner, smaller losers, fewer targets) all held; no
  sign was predicted.
- **R3 half at T1: holds.** E between A and C on every kind (reversal -0.05 / +0.09 / +0.22).
- **R4 fees: three lines survive.** Two taker fills cost 0.077-0.082 per trade; net of that,
  intervals clear of zero: reversal C +0.14 [+0.02, +0.27]; inside D +0.16 [+0.08, +0.23] and
  D5 +0.16 [+0.09, +0.24]. Six lines are negative net with the interval clear: reversal A -0.13
  [-0.18, -0.08]; continuation A -0.31, B -0.32, C -0.32, E -0.32; inside B -0.15 [-0.27, -0.02].
  The rest flat net; the reference -0.35..-0.92 net. (Corrected 2026-10-30 per the TVB-39 audit
  F8; this line previously called everything else flat.)
- **R5 under water: the lead was wrong.** The lead called C_u < C (holds longer, loses more).
  Holding time is the same (median 2-4 days), the tail a little fatter (44-57% past one R
  against 42-54%), and the exit-only book loses LESS or the same: C_u - C +0.20 [+0.09, +0.32]
  on the continuation, +0.04 / +0.04 / +0.23 elsewhere; A slips a few hundredths; D unchanged.
  On the continuation a red candle above the entry is not evidence against the trade.

### The owner's first pass on the viewer (same evening; two BTC trades)

**Trade 1, BTC 2026-03-27 weekly reversal short, "we hit T1, no exit; a second trip through
T1, no exit; hard to tell which level is the domino level".** The row was right; the viewer was
the problem. The book box was on C (exit only, no target by rule) and the "Position closed"
line was hard-wired to the headline exit whatever the box said; the trade's only level drawn
was its own weekly trigger, and "spread D+W" (the daily trigger broke the same day more than 1%
away) was printed as a chip, not drawn. Fixed the same evening (7f3fc88): the book box now
drives the chart (candles to the selected book's own settle day, the closed line at that
book's fill read off the row's return, the out arrow on the bar that touched the target when
the book took one, the headline clock kept as a small square); every timeframe the row says
broke that day is drawn, with a stack line in the details (each trigger's price, the gap, the
census band) and a "domino" label on a converged stack; the chart's previous-complete-bar
level was checked equal to the recorded entry level on all 179,498 rows (no mismatch); a magnet
ray tool (the owner's TradingView habit: a one-pixel blue line at 70% opacity snapped to the
bar's open / high / low / close, kept across the timeframe toggles per coin, moved by clicking
near it on a faster view); `&book=` in the address. One viewer bug found on the owner's
screenshot: the A2 markers had been spliced between the exit arrow's `if` and its `else`, so a
"data ends" square printed on every exited trade. Also `serve --host / --no-open` (ed08ae5) so
the owner can browse the viewer from their laptop over an SSH port forward or the tailnet.

**Trade 2, BTC 2026-03-25 daily inside break long, -6.99% in two days, "a 2D week and an
inside month, a recipe for disaster, yet it hit its daily target, and a weekly target on the
upside on a 2D week?"** Checked against the candles:

- The week was NOT 2D at entry: through 03-24 the week of 03-23 ran 67,404-71,785 inside the
  prior week's 67,313-75,972, with price above the week's open at 67,831 (the row's "week
  with"). It went 2D on 03-27, the exit day. The 2D week is hindsight.
- The month was inside (March 65,000-75,972 inside February's 60,000-79,417). The engine reads
  neither the month nor the week's bar type; it takes every daily break by design, and the
  only week read is its colour at entry (A2.1).
- T1 75,972 [W] is last week's high, the first unbroken weekly level above the entry: a level
  from the ladder, not the week's direction.
- The owner's "daily target" at 71,785 is the mother bar's high (03-23, a 2U). It was hit on
  the entry day (high 72,034); book A would have left at +0.56%. **Code-versus-skill drift,
  STOP-and-ASK raised, OPEN:** the prereg's definition says a with-trend inside break has no
  magnitude of its own and takes the first weekly / monthly rung (`anchor = ladder`); the
  strat-methodology skill's rulings R14 / R18 say unfilled structure containing the trigger is
  a real structural magnitude, and the 2U mother bar's far side contains this trigger. The
  owner's ruling decides; any change is prereg amendment A3 BEFORE code (rerun ~10 min). The
  question put to the owner: "Mother bar's far side as T1 for the with-trend inside break:
  amend?" Not answered this session.
- Why -6.99%: 03-26 closed red on the day but above the week's open, so the two-test exit did
  not fire; 03-27 closed below both, out at 66,396. The week-colour test let it ride through a
  3.6% red day; the setup-bar stop (68,904, the inside bar's low) would have cost 3.48%.
- Feed note: the venue API prints the inside bar's high at 71,385, TradingView at 71,387.

**The owner's closing words, as direction (not rulings):** the trade is "the danger of trading
lower timeframes when you have higher timeframes as inside bars", which is "why we tried to go
with the domino test" (the coincident-level event, TVB-37); "I think the daily exit close also
is going to be thrown out, the amount of trades this affects is pretty ridiculous"; more trade
reviews to come ("it does take time"); "we are making progress ... still some bugs to work
out". The owner's first pass is BEGUN, not finished.

### What the lead would say next (not done; the owner decides)

- The with-trend inside break's T1 is the first amendment candidate (A3): the mother bar's far
  side per the skill, against the prereg's ladder. The viewer should draw the mother bar's far
  side on every inside break so the owner can see the skill's reading trade by trade before
  ruling.
- If the daily-close exit is retired, the replacements are already measured on the same rows:
  under water (A2.5, loses less or the same), the hourly clock (A2.2, a different trade, flat
  net), the own-bar clock (fork 2, holds longer and loses more), the chance book's setup-bar
  stop (the reference). The owner picks; prereg before any rerun; no pick-the-winner.
- The owner's hazard (higher-timeframe inside bars around a lower-timeframe entry) is a
  context split the rows can already carry: the week's and month's bar type at entry (inside /
  2 with / 2 against / 3) as a declared split of every book, like A2.1 did for the week's
  colour. A one-line amendment if the owner wants it.
- The headline's "against" is the weaker reading on the continuation (A2.5); the week's side
  belongs to the reversal and the continuation (A2.1).

### Files created/modified

- New: `analysis/domino/trade_viewer.py`, `analysis/domino/viewer/{index.html,app.js}`,
  `tests/test_domino_viewer.py`, `tests/test_domino_manage_a2.py`.
- Modified: `analysis/domino/{manage.py,census.py,chart_page.py,MANAGE_RECEIPT.md}`,
  `results/{manage.json,manage_tables.md}` (+ the gitignored CSV / log / viewer data),
  `docs/experiments/tvb37_management_book_prereg.md` (A2), `docs/ARM_LEDGER.md`, `.gitignore`,
  `docs/reviews/REVIEW_REQUEST.md`, `.session_startup_prompt.md`, this file.
- Commits: dbeaffe (viewer), f505f9d (A2 prereg), 340c86e (A2 build), ed08ae5 (serve flags),
  7f3fc88 (viewer: book box, same-day triggers, ray tool, marker fix), then the close-out.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb39-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED (docs/reviews/tvb39-codex-audit.md, captured 2026-10-14; critical synthesis pending)
- Commits to review: `4dc5f6b..30391fb` on `main` (4dc5f6b is the pre-session sha; the range
  is dbeaffe, f505f9d, 340c86e, ed08ae5, 7f3fc88, 30391fb close-out; the sha-pin commit after
  it is docs only). Sanity-check: `git diff --name-status 4dc5f6b..30391fb` lists every file
  above (verified at pin time: 16 source / doc files plus the gitignore).
- Scope / what changed: the trade viewer (a static page + a build / hourly / serve CLI that
  draws recorded rows on cached candles and claims to re-run no trade logic) and prereg
  amendment A2 in `manage.py` / `census.py` (the under-water exit on the shared walk, the
  hourly clock on the hourly window, book E and fees as arithmetic, the week's side as a
  split, `candidates()` and its tables / page section).
- Focus areas (scrutinize these): `walk_hourly` (entry hour = first hour reaching L, exit =
  first hour closing against its own open AND the day's open, cap = the last hour of day 20,
  censoring when the hours end; the ordering claim that a target cannot be touched before
  the entry hour and the exit-day difference); `exit_u` sharing the headline `walk()` without
  changing it (headline numbers byte-identical: 179,498 units, same tables); book E and the fee
  arithmetic against the prereg's A2.3 / A2.4 definitions; the viewer's calendar bucketing
  (`weekStart` / `monthStart` against `census.week_start` / `month_start`), its `settle()`
  (the fill = level moved by the recorded return; is that always the engine's own price?),
  `stackLevels()` (previous complete bar's extreme per stack timeframe; checked equal to every
  row's `level` for its own timeframe) and the claim of re-running no trade logic; the "data
  ends" marker fix.
- Reviewed by: Codex, local source review + offline replay, 2026-10-14
- Findings: {blank until docs/reviews/tvb39-codex-audit.md exists}

### Open

- [ ] The owner's own pass over the management book on the viewer (BEGUN 2026-10-12 evening,
      two BTC trades; continues) before anything is read into the hierarchy rulings.
- [ ] STOP-and-ASK, open: the with-trend inside break's T1 (the mother bar's far side per
      skill R14 / R18, against the prereg's weekly / monthly ladder). The owner rules; prereg
      amendment A3 BEFORE code; rerun ~10 min.
- [ ] The owner's signal that the daily-close exit "is going to be thrown out": a declared
      replacement (prereg) before any rerun. Already measured on the same rows: under water
      (A2.5), the hourly clock (A2.2), the own-bar clock (fork 2), the setup-bar stop
      (reference).
- [ ] Viewer: draw the mother bar's far side on every inside break; optionally the week's and
      month's bar type at entry as chips (the owner's hazard).
- [ ] Codex review of `4dc5f6b..HEAD` (block above): REQUESTED at session end.
- [ ] The hierarchy rulings the owner deferred (stop owner in a stack, continuation ranking,
      seat competition, which higher-timeframe event ends a trade).
- [x] HANDOFF is over the 1,500-line limit (2,100+; TVB-33..34 are the next archive
      candidates): archiving asks the owner. CLOSED 2026-10-14 (after the TVB-39
      close-out, on the owner's word): TVB-33..35 archived verbatim to
      docs/session_archive/HANDOFF_TVB33-TVB35.md (TVB-33..34 alone left ~1,640
      lines; the three make the round-3 arc); HANDOFF now ~1,420 lines.
- [ ] Executor repairs owed before any real-money restart (TVB-31..35 syntheses); fresh
      wallet; scanner STRAT rulings; the carried list in the TVB-37 entry.

---
