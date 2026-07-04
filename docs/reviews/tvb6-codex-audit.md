# TVB-6 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of `tradingview-backtesting` range `43fb973^..9a00d40`
> (`1f7815f..9a00d40`) plus local sibling `tradingview-mcp-jackson@27757bc`,
> captured 2026-07-04 (TVB-6 post-session). Lightly ASCII-normalized.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate
> control vs variant, or over/under-state a risk. The critical synthesis -- where
> we agree, dispute, and act -- is in `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-6 -- xyz backfill verification, venue-gap decomposition, MAE/solvency, slippage band, re-entry governor v1/v2
- **Reviewed:** `43fb973^..9a00d40` on `main`; sibling `C:\Strat_Trading_Bot\tradingview-mcp-jackson@27757bc`
- **Reviewer:** Codex CLI
- **Overall verdict:** APPROVE-WITH-NITS

## 2. Verbatim audit

I reviewed the requested read-first context, the 51-file pinned diff, the
committed evidence JSONs, the Pine governor implementation, and the sibling
Monaco finder fix. The repo has advanced beyond `9a00d40` to later TVB-7 commits,
so this audit is anchored to the requested TVB-6 range; later TVB-7 append-only
material was ignored except to confirm it did not modify the TVB-6 code/data
artifacts reviewed here.

### Findings

1. **LOW -- The MAE/solvency record understates the worst 60m short MAE.**

   Re-running the committed MAE script over the committed TVB-6 60m dumps returns
   `8.42%` worst short MAE and `7.22x` max survivable short leverage for both
   `ctrlA` and `R1E3`, but the datasheet table records `8.00%` and `7.46x`
   (`docs/TVB2_control_AB_rerun.md:992-997`). The follow-on text also says the
   sample worst is `8.11%` and clearance is `~7.4x short`
   (`docs/TVB2_control_AB_rerun.md:1001-1014`), which is false if the 60m rows are
   included. The helper is deterministic over the committed dump and bar files:
   `analysis/trade_mae.py:93-125` loads the JSONs, computes worst MAE, liquidation
   breaches, and max survivable leverage from `analysis/reference/tvb6_WV_ctrlA_0125.json:1`,
   `analysis/reference/tvb6_WV_R1E3_0125.json:1`, and
   `analysis/reference/tvb6_tv_xyzMSTR_60m.json:1`.

   Impact is limited: `8.42%` is still far below the 1x, 2x, 3x, and 5x short
   liquidation thresholds, so the "1x cash is solvent in-sample" conclusion still
   holds. But this is exactly the model-fidelity table requested for scrutiny, so
   the record should not understate the maximum adverse excursion. Also update the
   "Long worst MAE 3.7-5.4%" context line; the same rerun reports `5.54%` for the
   60m long side.

2. **LOW -- The tick-size equalizer is plausible, but the raw symbol metadata is not committed.**

   The tick-size decomposition is central to the TVB-6 venue-gap claim:
   `xyz MSTRUSDC.P mintick = 0.001`, `OKX MSTRUSDT.P mintick = 0.01`, so xyz
   `s10` equals OKX `s1` in absolute dollars per fill (`docs/TVB2_control_AB_rerun.md:1024-1035`).
   That equalizer is sound if the two min ticks are correct, and the slippage-band
   dump metrics reproduce the table (`docs/TVB2_control_AB_rerun.md:1037-1056`).
   The reproducibility gap is that the committed exporter captures `symbol`,
   `pro_symbol`, `interval`, `count`, and `bars`, but drops `minTick` / `pricescale`
   from the `symbolInfo()` object (`scripts/tv_bars.mjs:24-31`).

   This does not overturn the result. It does make the "roughly half artifact,
   half texture" claim less audit-complete than the backfill claim, whose raw
   evidence is committed and script-replayable. Add a tiny committed symbolInfo
   artifact, or extend `tv_bars.mjs` to persist the tick metadata alongside each
   bar export, before relying on the tick-size split as a permanent record.

3. **LOW -- Add one explicit governor profit-boundary diagnostic.**

   The Pine governor comments say loss detection is net of fees and scratch counts
   as losing (`pine/baseline_continuity.pine:212-219`), implemented with
   `strategy.closedtrades.profit(strategy.closedtrades - 1) > 0`
   (`pine/baseline_continuity.pine:235-238`). TradingView's strategy docs list
   per-trade `profit()`, `profit_percent()`, and `commission()` in the individual
   trade API, and separately describe commission as part of simulated performance
   results. I did not find a local micro-check proving the exact gross/net boundary
   for `strategy.closedtrades.profit()` under this Pine version.

   I am not treating this as a blocking bug because the governor v2 keep margin is
   not a one-trade rounding edge: R1E1+gov2 beats ungoverned at both real-cost
   points (`+71.80` vs `+59.96`, `+45.71` vs `+34.76`) and the dumps back those
   rows. Still, the rule's semantic intent depends on the fee boundary. Add a
   one-off Pine diagnostic or dump field that records, for the latest closed
   trade, `profit`, `commission`, and the sign used by the ratchet.

### Checks that passed

- **Backfill verification:** `analysis/verify_xyz_backfill.py` is a reasonable
  method for the sample-scoped claim that TV's xyz MSTR backfill is genuine HL
  venue data. It compares TV and HL OHLCV on timestamp intersections, separates
  HL-only zero-trade placeholders from traded bars, reports exact-field and
  worst-bar stats, closes the Dec2-Dec7 1h API cap hole with 4h aggregation, and
  checks TV 15m to TV 60m internal closure (`analysis/verify_xyz_backfill.py:88-132`,
  `analysis/verify_xyz_backfill.py:173-192`). My replay matched the written
  15m/60m/1D/4h/internal tables. The pre-May-12 15m residual is honestly bounded,
  not proven tick-by-tick; the record says that.

- **MAE method:** The liquidation formula and inverse are algebraically correct
  for the stated simplified isolated-margin model (`analysis/trade_mae.py:32-45`).
  Measuring adverse extremes over `[et, xt]` can overstate MAE when an entry-bar
  or exit-bar extreme falls outside the real holding subinterval; that is
  conservative for a solvency clearance, not optimistic
  (`analysis/trade_mae.py:48-74`). The docs should mention the exit-bar side too,
  but the direction of bias is acceptable for this use.

- **Pine lookahead/repaint:** I found no `request.security` path in the reviewed
  Pine. The gate/regime opens are reconstructed locally with
  `ta.valuewhen(timeframe.change(tf), open, 0)` (`pine/baseline_continuity.pine:124-188`),
  with explicit timeframe tiling guards (`pine/baseline_continuity.pine:100-123`).
  The strategy uses `process_orders_on_close = false` and
  `calc_on_every_tick = false` (`pine/baseline_continuity.pine:42-53`), consistent
  with TradingView's documented next-bar historical order processing and its
  warning that tick recalculation can repaint after reload.

- **Governor mechanics:** Trigger capture as `high[1] + syminfo.mintick` /
  `low[1] - syminfo.mintick` on the fill bar matches the stop orders placed on
  the prior bar (`pine/baseline_continuity.pine:226-233`,
  `pine/baseline_continuity.pine:255-268`). Loss detection executes before the v2
  full-opposite-alignment reset (`pine/baseline_continuity.pine:235-245`), so the
  documented same-bar ordering is implemented. The v1 failure mode is retained in
  the record (`docs/TVB2_control_AB_rerun.md:1109-1144`), and v2 was pre-registered
  before the v2 run (`docs/TVB2_control_AB_rerun.md:1155-1179`), which makes the
  amendment look mechanism-driven rather than post-hoc tuning.

- **Slippage/governor tables:** Parsing the committed TVB-6 dumps reproduces the
  slippage-band and governor rows, including dump assertions `lenOk=True` and
  `entryOrderOk=True` from `scripts/tv_dump.mjs:24-51`. The v2 keep rule is applied
  exactly as written: R1E1+gov2 beats ungoverned R1E1 at both `s1` and `s10`
  real-fee points (`docs/TVB2_control_AB_rerun.md:1173-1179`,
  `docs/TVB2_control_AB_rerun.md:1181-1206`).

- **Sibling repo:** `tradingview-mcp-jackson@27757bc` fixes the Monaco finder by
  iterating all `.monaco-editor.pine-editor-monaco` candidates and returning the
  first candidate whose React fiber walk reaches `monacoEnv`, instead of dead-ending
  on the first decoy node (`src/core/pine.js` in the sibling commit). This is a
  narrow local transport fix and does not affect strategy results already dumped
  through the direct CDP bridge.

### Validation performed

- `git diff --name-status 43fb973^..9a00d40` matched the requested 51-file range.
- `python analysis\verify_xyz_backfill.py` replayed the committed backfill tables.
- `python analysis\trade_mae.py ...` over all four headline dumps exposed the 60m
  MAE table mismatch above.
- Parsed committed slippage/governor dumps with PowerShell `ConvertFrom-Json`.
- `PYTHONDONTWRITEBYTECODE=1 python -m pytest tests\test_verify_xyz_backfill.py tests\test_trade_mae.py -q -p no:cacheprovider` -> `8 passed in 0.02s`.

I did not live-recompute TradingView/CDP strategy runs, re-fetch HL candles, or
query live symbolInfo. The backfill raw API pulls are time-perishable by design;
this audit is based on the committed evidence files plus deterministic replay.

### TradingView docs consulted

- Strategy broker emulator/order-fill model and bar magnifier caveats:
  https://www.tradingview.com/pine-script-docs/concepts/strategies/#broker-emulator
- Strategy calculation timing, `calc_on_every_tick`, `calc_on_order_fills`, and
  `process_orders_on_close`:
  https://www.tradingview.com/pine-script-docs/concepts/strategies/#calc_on_every_tick
- Strategy trade costs and commission/slippage behavior:
  https://www.tradingview.com/pine-script-docs/concepts/strategies/#simulating-trading-costs
- Individual trade information APIs:
  https://www.tradingview.com/pine-script-docs/concepts/strategies/#individual-trade-information

## 3. Actionable items (reviewer's own list, if provided)

1. Correct the MAE/solvency table -- LOW -- `docs/TVB2_control_AB_rerun.md:992` -- update ctrlA/R1E3 worst short MAE to `8.42%`, max survivable short leverage to `7.22x`, long context to `5.54%`, and the global worst/sample-clearance prose to match the committed `analysis/trade_mae.py` replay.
2. Persist tick-size metadata -- LOW -- `scripts/tv_bars.mjs:24` -- include `minTick`/`pricescale` (or commit a small `symbolInfo` artifact) for the xyz and OKX symbols so the `s10 == OKX s1` equalizer is reproducible from tracked files.
3. Add a governor profit-boundary diagnostic -- LOW -- `pine/baseline_continuity.pine:235` -- record or assert whether `strategy.closedtrades.profit()` is net of commission for the ratchet's winning/losing classification.

## Suggested prompt

Review the pinned TVB-6 range `43fb973^..9a00d40` plus sibling
`tradingview-mcp-jackson@27757bc`. First replay the committed deterministic
evidence (`analysis/verify_xyz_backfill.py`, `analysis/trade_mae.py`, and the
TVB-6 JSON dumps) and compare script output against every headline table. Then
inspect `pine/baseline_continuity.pine` for `request.security`/lookahead,
governor trigger capture, same-bar reset ordering, and the exact
`strategy.closedtrades.profit()` fee boundary. Finally, check whether all central
modeling claims have committed artifacts, especially symbol tick sizes used for
the xyz-vs-OKX slippage equalizer.
