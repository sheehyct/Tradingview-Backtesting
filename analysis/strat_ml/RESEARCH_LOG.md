# STRAT ML research vessel -- research log

For remembering threads, not for rigor (spec v0.1). One line per thread: date, thread, what
sparked it, status. Newest at the top.

| date | thread | spark | status |
|---|---|---|---|
| 2026-10-20 | The owner's live Pine (Magnitude + Targets) star setups cut from the table: 64% win vs 52%, same money per R; 1-3 reads as a setup-bar-stop artefact | owner shared the original script | four Pine parts never carried into the daily line listed in HANDOFF (pivot ladder, potential-3 exit, momo filter, chop counter) |
| 2026-10-20 | Excursion clock: time to +x R / x R against, fixed-hour marks, time-stop rule vs hold | owner: can "it turned against me" become a rule | rule saves ~0.02R per laggard; the mark already carries the loss; first-excursion split is the lead but needs 15m bars (trigger-hour artefact) |
| 2026-10-20 | tfc_score = 1 is the blue-sky set by construction (both levels already broken, no rung); colour-only bias goes the expected way | context slice surprise | two continuity readings with opposite signs: colour helps a little, extension through both levels hurts |
| 2026-10-20 | Stop head-to-head on inside breaks: bar-0 stop (0.84 ATR) vs setup-bar stop (0.57 ATR) on the same 119,926 rows | owner's ask | win rate +7 pts, stop-outs -10 pts, money per trade unchanged (-0.2% of price both); the stop shapes the loss, it does not remove it |
| 2026-10-20 | Phase 2 event table (565,687 rows) + phases 3-5 report: baseline, k-means, LightGBM/SHAP on a 2025 time split, depth-3 tree, phone HTML | owner: run to the end | DONE; read-out in the phase 2 design doc section 8 |
| 2026-10-20 | Leak caught: `opposite_also_triggered` ranked second in the first fit; it is end-of-day knowledge | AUC 0.85 looked too good | excluded from every model; kept as the spec's overlap flag |
| 2026-10-20 | Geometry dominates target-first: <0.5R targets 81-84% hit, >3R 8-15%, mean R flat | first SHAP read | models split: money question on context only (model A), geometry shown on purpose (model B) |
| 2026-10-20 | Blue-sky breaks (no week/month level beyond entry): 59k rows, 30% win, -0.11R, stop hit 61%; unmanaged view slightly positive | cluster 4 | hypothesis: stop placement, exhaustion risk; majors opposite sign on 393 rows; owner to decide if it becomes a domino-book arm |
| 2026-10-20 | Context ranks losers not winners: model A bottom decile -0.25R / 33% win on 2025-26, top decile +0.03R | time-split deciles | BTC realized-vol percentile is the top feature; nothing beats zero before costs |
| 2026-10-17 | Full-universe pull (every USDT perp, klines + funding) started in the cloud session; raw cache is per-container, the committable roster is `analysis/strat_ml/universe_summary.json` | owner go-ahead | DONE: 900 symbols, 57,319 files, 0 errors; 160 delisted by volume (not 31); roster committed; plan doc section 6 |
| 2026-10-17 | Phase 1 data layer: Binance Vision downloader, raw zip cache, parquet build, universe manifest | spec v0.1 Phase 1 | built; test slice pulled (BTC, ETH, LINK, DOGE, SOL, AVAX, SRM delisted); see docs/experiments/strat_ml_phase1_data_plan.md |
| 2026-10-17 | Zombie files: the archive keeps publishing flat zero-volume months for dead contracts (BTCST frozen 2024-02 .. 2026-06, FTT flat at 1.59, SRM last trade 2022-11-15 but files to 2024-05) | universe manifest showed only 31 delisted | delisting must be read from volume (manifest `last_traded`); Phase 2 trims the dead tail |
| 2026-10-17 | Survivorship: the archive keeps delisted perps (SRM, LUNA, BTCST, ...) plus 17 SETTLED stubs | spec question "does the archive have delisted symbols" | answered yes; delisted = last month < archive head month |
| 2026-10-17 | Metrics coverage is patchy: BTC backfilled to 2020-09 (rows doubled), most names 2021-12-01, small names stop mid-2024 | earliest-date check | noted; features stay null where missing |
| 2026-10-17 | Which classifier Phase 2 imports: census strict-break vs paper pine-exact vs the scanner's (other repo) | spec open decision 3 | DECIDED 2026-10-17: the census strict-break classifier (`analysis/domino/census.py:classify`) plus its calendar bucketing; EXP-013 code not used |
