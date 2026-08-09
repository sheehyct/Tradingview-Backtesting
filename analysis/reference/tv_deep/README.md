# tv_deep -- TVB-19 deep-window TV bar harvest (2026-08-05)

One-time permanent harvest of TradingView's full loaded series per roster
symbol/interval, taken while TV was idle overnight (user request,
2026-08-04 seed). Harvester: `scripts/tvb19_harvest.mjs` (CDP, TVB-6
mechanism: requestMoreData to the data floor, then dump the whole main
series). Run on the TVB18-parity scratch layout; per-dataset provenance
(pro_symbol, minmov/pricescale, harvested_utc, first/last ISO) inside
each file; inventory in `tvb19_harvest_summary.json`.

Provenance rules (TVB-6): TV bars and HL-API bars differ at the
cents/wick level (97-99% float-exact where compared); these are TV-feed
bars and any analysis mixing them with `analysis/paper/bars/` (HL API)
must declare the venue-feed mix. The HL API floor (~5000 candles per
interval, ~17 days at 5m) is venue retention; this harvest is the
workaround, not a fix.

Observed TV depth (2026-08-05 inventory; per-dataset first/last in
tvb19_harvest_summary.json):

- 5m: a TV-side depth cap of ~20.2-21.6k bars, NOT a uniform calendar
  floor. Starts: 2026-05-18 (AMZN/MSFT/AAPL), 2026-05-25
  (MRVL/GOOGL/GOLD/TSLA/DRAM/SKHYNIX), venue listing for the young
  symbols (NBIS 2026-06-09, SKHY 2026-07-09). Still ~4x the HL 5m
  floor for the cap-bound symbols. [Corrected 2026-08-07, TVB-19 audit
  F3: the original "uniform floor 2026-05-25, boundary identical
  across symbols" claim was false -- three symbols reach deeper, two
  are listing-bound.]
- 15m: venue listing date for younger symbols (e.g. MRVL 2026-05-04,
  SKHYNIX 2026-02-19); ~20k-bar cap for older ones (majors reach
  2026-01-01, ~7 months).
- 60m: venue listing for all (deepest: GOOGL 2025-11-18).

Consumption caveats (declared 2026-08-07, TVB-19 audit F3): every
committed dump ends on TV's ACTIVE bar -- the final row may be a
still-forming bar; drop or close-gate it before any analysis. The
2026-08-05 harvest also predates the harvester's fail-closed floor
detection (it used a single unchanged 700ms poll and did not enforce
err/cap states), so floor termination is not recorded for these files:
the depth numbers above describe the committed inventory, not a
verified venue floor. Re-harvests now fail unless every dataset lands
with a clean floor state, and the summary merges by (coin, interval).

Summary provenance fields (TVB-20 audit F2, 2026-08-08): the harvester
now writes `run_complete` (this run's requested subset landed) SEPARATE
from `inventory_complete` (every canonical roster x interval row
present, error-free, and carrying the fail-closed floor receipt
`history.state == "floor"`). The committed 2026-08-05 summary predates
both fields and none of its 33 rows carries a floor receipt, so any
post-fix rerun reports `inventory_complete: false` until the full
inventory is re-harvested fail-closed -- that flag being false is the
honest state, not an error. Unknown or empty `TVB19_COINS` selectors
now fail before anything runs.

Symbol-name trap: HL `xyz:SKHX` is listed on TV as
`HIP3XYZ:SKHYNIXUSDC.P` (files here use the TV coin string SKHYNIX).
TV symbol search does NOT index HIP3XYZ at all -- found by direct chart
load. Identity verified: 9,183/9,187 overlapping 5m closes float-exact
vs the HL SKHX archive (executable check:
`uv run python -m analysis.verify_skhx_identity` regenerates
`skhx_identity_check.json` -- 4 mismatched closes, max delta 1.7, the
declared TV-vs-HL wick-level class), and the 15m series starts on the
HL listing date. Related catch: roster_week1.json carries SKHX with
`tv_mintick 0.1, mintick_source hl_inferred, tv_symbol null`; TV
metadata says mintick 0.001. The week-1 roster stays frozen
(adjudicated); future rosters should backfill `tv_symbol` and re-pull
the tick from TV metadata.
