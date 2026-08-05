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

Observed TV depth (2026-08-05):

- 5m: uniform floor 2026-05-25 00:00Z (~10 weeks, ~20k bars) -- ~4x the
  HL 5m floor. Boundary identical across symbols: a TV-side depth
  window, not listing.
- 15m: venue listing date for younger symbols (e.g. MRVL 2026-05-04,
  SKHYNIX 2026-02-19); ~20k-bar cap for older ones (majors reach
  2026-01-01, ~7 months).
- 60m: venue listing for all (deepest: GOOGL 2025-11-18).

Symbol-name trap: HL `xyz:SKHX` is listed on TV as
`HIP3XYZ:SKHYNIXUSDC.P` (files here use the TV coin string SKHYNIX).
TV symbol search does NOT index HIP3XYZ at all -- found by direct chart
load. Identity verified: 9,183/9,187 overlapping 5m closes float-exact
vs the HL SKHX archive, and the 15m series starts on the HL listing
date. Related catch: roster_week1.json carries SKHX with
`tv_mintick 0.1, mintick_source hl_inferred, tv_symbol null`; TV
metadata says mintick 0.001. The week-1 roster stays frozen
(adjudicated); future rosters should backfill `tv_symbol` and re-pull
the tick from TV metadata.
