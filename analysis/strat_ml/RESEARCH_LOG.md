# STRAT ML research vessel -- research log

For remembering threads, not for rigor (spec v0.1). One line per thread: date, thread, what
sparked it, status. Newest at the top.

| date | thread | spark | status |
|---|---|---|---|
| 2026-10-17 | Phase 1 data layer: Binance Vision downloader, raw zip cache, parquet build, universe manifest | spec v0.1 Phase 1 | built; test slice pulled (BTC, ETH, LINK, DOGE, SOL, AVAX, SRM delisted); see docs/experiments/strat_ml_phase1_data_plan.md |
| 2026-10-17 | Zombie files: the archive keeps publishing flat zero-volume months for dead contracts (BTCST frozen 2024-02 .. 2026-06, FTT flat at 1.59) | universe manifest showed only 31 delisted | delisting must be read from volume (manifest `last_traded`); Phase 2 trims the dead tail |
| 2026-10-17 | Survivorship: the archive keeps delisted perps (SRM, LUNA, BTCST, ...) plus 17 SETTLED stubs | spec question "does the archive have delisted symbols" | answered yes; delisted = last month < archive head month |
| 2026-10-17 | Metrics coverage is patchy: BTC backfilled to 2020-09 (rows doubled), most names 2021-12-01, small names stop mid-2024 | earliest-date check | noted; features stay null where missing |
| 2026-10-17 | Which classifier Phase 2 imports: census strict-break vs paper pine-exact vs the scanner's (other repo) | spec open decision 3 | OPEN, owner picks |
