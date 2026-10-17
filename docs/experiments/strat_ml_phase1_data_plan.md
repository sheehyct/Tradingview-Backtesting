# STRAT ML research vessel -- Phase 1 plan: data acquisition

Spec: the owner's `STRAT_ML_RESEARCH_SPEC.md` v0.1 (exploratory research, nothing deployed).
Phase 1 covers ONLY the data layer. No event detection, no bar classification, no features here.
Written 2026-10-17 in a cloud session (no TradingView, no exchange keys; public archive only).

## 1. What was checked before building (findings)

### 1a. The archive is reachable, but only through the bucket endpoint from this session

- `https://data.binance.vision` (the CDN hostname Binance documents) is REFUSED by this cloud
  session's egress proxy (CONNECT 403). The bucket behind it,
  `https://s3-ap-northeast-1.amazonaws.com/data.binance.vision`, is reachable, serves the same
  objects and also answers S3 `ListBucket` queries (prefix / delimiter / marker paging).
- The live API (`fapi.binance.com`) is refused too, as the spec expected (geo-restriction; here
  also the proxy). Nothing in Phase 1 touches it.
- Consequence: the downloader takes an ordered list of base URLs and uses the first that answers;
  default order is the CDN first (the workstation), the bucket second (here).

### 1b. Delisted USDT-M perps ARE in the archive

Checked by name against the monthly 1h klines listing (1,056 symbol folders; 900 end in USDT):

| symbol | 1h klines | fundingRate | metrics (daily) | note |
|---|---|---|---|---|
| SRMUSDT | 2020-09 .. 2024-05 | 2020-09 .. 2024-07 | 2021-12-01 .. 2023-06-16 | delisted (FTX-era); chosen as the test delisted alt |
| LUNAUSDT | 2021-01 .. 2022-05 | 2021-01 .. 2022-05 | 2021-12-01 .. 2024-06-20 | the Terra collapse; alternative delisted example |
| BTCSTUSDT, CVCUSDT, RAYUSDT, HNTUSDT, TOMOUSDT, SCUSDT, BLUEBIRDUSDT, DODOUSDT, COCOSUSDT, ANTUSDT, BTSUSDT, FOOTBALLUSDT, DGBUSDT, KLAYUSDT, CTKUSDT, STRAXUSDT | present | present | partial | all known delistings found by name |
| USTUSDT, MULTIUSDT | absent | | | were never USDT-M perps, or were removed |

Two archive quirks that matter for the universe definition:

- 17 folders carry a `SETTLED` suffix (e.g. `AERGOUSDTSETTLED`, `ICPUSDT_SETTLED`, even
  `AERGOUSDTSETTLEDSETTLED`): single-month stubs created when a contract was settled and the
  ticker re-used. They are excluded from the universe and listed in the manifest.
- Delisting cannot be read from the live API here. The point-in-time definition used instead:
  a symbol is "delisted as of month M" when its last monthly klines file is older than the
  archive head month (the newest month any symbol has). This is also the definition the event
  build will want, because it is computable without survivorship knowledge from the present.

- FOUND WHILE BUILDING (the universe manifest, 2026-10-17): Binance keeps PUBLISHING monthly
  files for contracts that stopped trading. BTCSTUSDT's files run to 2026-06 but every bar
  from before 2024-02 onward is flat at one price with zero volume; FTTUSDT's 2026-09 file is
  720 zero-volume bars at 1.59. So "last monthly file older than the head month" is a FLOOR on
  delisting (31 of 900 USDT perps by that rule; the true count is higher). The usable
  point-in-time signal is the last bar with volume > 0: the klines manifest records
  `last_traded`, `zero_volume_hours` and `trailing_dead_hours` per symbol, the raw cache is
  never trimmed, and the event build (Phase 2) must drop the dead tail or the flat bars
  become an endless run of inside bars with a zero ATR. The full-universe pull will compute
  the real delisting month from volume; the listing-based manifest is the cheap first pass.

So survivorship is addressable: the full universe including dead contracts can be built from
the archive alone, with delisting read from volume rather than from file presence.

### 1c. Earliest dates per dataset (USDT-M, `futures/um`)

| dataset | files | earliest in archive | notes |
|---|---|---|---|
| klines 1h | monthly + daily | monthly 2020-01, daily 2019-12-31 (BTCUSDT, ETHUSDT) | Binance USDT-M launched 2019-09-08; Sep-Dec 2019 is NOT in the archive. Monthly files lag ~2 weeks; the current month comes from daily files. |
| fundingRate | monthly ONLY | 2020-01 (BTCUSDT) | 3 rows/day (8h). Columns: calc_time, funding_interval_hours, last_funding_rate. |
| metrics | daily ONLY | BTCUSDT 2020-09-01 (backfilled 2026-03); everything else 2021-12-01 or the listing date | 5-minute rows (288/day). Backfilled BTCUSDT files hold every row TWICE (dedupe needed). Coverage is spotty for small names (FTTUSDT metrics stop 2024-07-15 while its klines continue); leave null where missing, as the spec says. |

Alts list the same month their perp opened (DOGEUSDT 2020-07, SOLUSDT/AVAXUSDT 2020-09,
SUIUSDT 2023-05), so per-symbol `symbol_age_days` falls straight out of the first klines row.

### 1d. CSV layout changes mid-archive

- klines files before ~2022 have NO header row; newer files have one. The parser sniffs each file.
- Timestamps are milliseconds in every sampled futures file; a microsecond guard is still
  applied (Binance moved spot klines to microseconds in 2025) so a future change cannot shift
  every bar by 1000x silently.
- Every object has a `.CHECKSUM` sidecar (sha256). Verified on every download.

### 1e. Existing PyPI downloaders (checked 2026-10-17)

| package | version / date | fundingRate | metrics | host configurable | checksum | verdict |
|---|---|---|---|---|---|---|
| binance-bulk-downloader (aoki-h-jp) | 1.1 series, 2025-01 | yes | yes | NO: lists via the bucket, downloads via the hard-coded CDN host (blocked here) | no | closest fit; unusable in this session without monkeypatching |
| binance-vision (Njenjo) | 0.1.0, 2026-08, 2 commits | no | yes | no | yes | too new, no funding |
| binance-historical-data (stas-prokopiev) | 0.1.14, 2024-09, 162 stars | no | yes | no | no | CSV dump, pulls ipywidgets |
| binance-history, binance-downloader, binance-klines, binance_data | 2020-2023 | no | no | n/a | no | stale or live-API based |

Decision: a thin custom module (`analysis/strat_ml/binance_vision.py`, ~300 lines). The
reasons are concrete, not taste: no package covers funding AND metrics AND a configurable host
AND checksum verification, none builds the point-in-time universe manifest from the bucket
listing, and the raw-zip cache plus parquet normalisation (header sniff, metrics dedupe,
UTC-aware timestamps) is where the real work is anyway. The S3 listing/paging approach is the
same one binance-bulk-downloader uses.

## 2. Design

```
analysis/strat_ml/
  binance_vision.py     downloader + raw cache + parquet build + universe manifest (CLI)
  RESEARCH_LOG.md       the spec's thread log (date, thread, spark, status)
  data/                 gitignored (repo .gitignore has `data/`)
    raw/<dataset>/<SYMBOL>/<file>.zip        untouched archive objects, checksum-verified
    parquet/<dataset>/<SYMBOL>.parquet       normalised, one table per symbol per dataset
    parquet/<dataset>/<SYMBOL>.manifest.json rows, first/last, source files, base URL, built-at
    universe.parquet / universe.json         every USDT-M perp folder: first/last month, delisted flag
```

- Raw zips are the cache; the parquet build is re-runnable offline from them (spec rule).
- Monthly files are preferred; daily files fill the months after the last monthly file (klines)
  or are the only form (metrics). Which files exist is read from the bucket listing, never
  guessed, so a missing month is a logged gap, not a 404 storm.
- Parquet schemas (all times timezone-aware UTC):
  - klines: open_time, open, high, low, close, volume, close_time, quote_volume, count,
    taker_buy_volume, taker_buy_quote_volume (float64 prices: research arrays, same as the
    census and the paper twin; the spine's Decimal rule is for money, not OHLCV columns)
  - fundingRate: calc_time, funding_interval_hours (nullable), last_funding_rate
  - metrics: create_time, sum_open_interest, sum_open_interest_value,
    count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio, count_long_short_ratio,
    sum_taker_long_short_vol_ratio (5-minute rows kept raw; hourly alignment is Phase 2)
- Validation on build: strictly increasing time key after dedupe (keep last), and for klines
  the count of missing hours between first and last bar is recorded in the manifest (gaps are
  never filled).
- Network politeness: a shared session with retries, 4 workers, small delay between requests.
- Tests (`tests/test_strat_ml_binance_vision.py`) run WITHOUT network on zip fixtures: header
  sniff, microsecond guard, metrics dedupe, checksum verify, file selection (monthly then daily
  tail), universe classification of folder names.

## 3. Test slice (Phase 1 deliverable)

Symbols chosen a-priori by structure, not by performance:

- majors: BTCUSDT, ETHUSDT
- alts: LINKUSDT (listed 2020-01, longest alt history), DOGEUSDT (2020-07, meme/retail flow),
  SOLUSDT and AVAXUSDT (2020-09, 2021-cycle L1s), SRMUSDT (2020-09 .. 2024-05, DELISTED)

Datasets for the slice: 1h klines (full history) and fundingRate (full history). Metrics are
supported by the module and smoke-tested on a short window only; the full metrics pull is
deferred to the universe pull because it is ~2,000 small files per symbol.

## 4. Open decisions carried to the owner (not blocking Phase 1)

1. Spec open decisions 1-4 (bar boundary, majors, pattern list, stop/entry conventions):
   defaults assumed as written. Nothing in Phase 1 depends on them.
2. "Reuse the existing STRAT bar classification": this repo holds two. The strict-break
   classifier `analysis/domino/census.py:classify` (ruling R10, equality never breaks, used by
   the TVB-37 census, prereg'd) and the pine-exact `analysis/paper/patterns.py:PatternDetector`
   (mintick threshold, live intrabar, Tier B). The spec's "existing scanner / EXP-013" lives in
   another workspace (the STRAT scanner), not in this repo. The owner picks which one Phase 2
   imports; the census classifier plus `tfc/resample.py` for calendar bucketing is the lead's
   suggestion because it is already prereg'd on 24/7 perps and is the same strict-break rule
   the charter uses.
3. Universe breadth for the full pull: all ~880 USDT perps (excluding SETTLED stubs) is about
   40k monthly kline files plus funding; feasible (~1.5 GB raw) but a multi-hour pull. Run it
   once the slice is accepted.
4. `uv add pyarrow` touched `pyproject.toml` and `uv.lock`. On the workstation the next
   `uv sync` will strip VectorBT Pro (known gotcha): reinstall from the cached wheel.

## 5. Test slice result (run 2026-10-17, cloud session, served by the bucket endpoint)

| symbol | 1h bars | first bar | last bar | missing hours | last traded (volume > 0) | dead tail (hours) | funding rows |
|---|---|---|---|---|---|---|---|
| BTCUSDT | 59,544 | 2020-01-01 | 2026-10-16 | 0 | live | 0 | 7,395 |
| ETHUSDT | 59,544 | 2020-01-01 | 2026-10-16 | 0 | live | 0 | 7,395 |
| LINKUSDT | 59,152 | 2020-01-17 | 2026-10-16 | 0 | live | 0 | 7,346 |
| DOGEUSDT | 54,951 | 2020-07-10 | 2026-10-16 | 0 | live | 0 | 6,821 |
| SOLUSDT | 53,249 | 2020-09-14 | 2026-10-16 | 120 (72 h ending 2022-03-01, 48 h ending 2022-04-03; archive gaps, not filled) | live | 0 | 6,700 |
| AVAXUSDT | 53,153 | 2020-09-23 | 2026-10-16 | 0 | live | 0 | 6,598 |
| SRMUSDT (delisted) | 32,670 | 2020-09-05 | 2024-05-28 | 0 | 2022-11-15 04:00 UTC | 13,443 (560 days of flat 0.287 bars) | 4,241 (runs to 2024-07-19, i.e. past the last trade) |

- 1,070 archive files (and their CHECKSUM sidecars) fetched, zero checksum failures, zero
  errors; raw cache 17.9 MB, parquet 28.8 MB. Metrics smoke test: BTCUSDT 2026-10-10 ..
  2026-10-16, 2,016 five-minute rows, no duplicates.
- SRMUSDT is the survivorship lesson in one row: its archive files run 18 months past its
  last real trade. The event build must use `last_traded`, never the last file.
- Funding rows continue past the last trade for a dead contract (flat 0.0001 placeholder
  rate). Same trim applies.
