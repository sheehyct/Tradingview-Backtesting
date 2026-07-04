# VBT Breadth-Engine Port: TFC Baseline -> ATLAS Python (TVB-7 design)

> Approved by the user in plan mode, TVB-7 (2026-07-04). Implementation executes in
> a vectorbt-workspace session; this document is the design of record on the TVB
> side. Companion evidence: the calibrated facts below were verified against the
> committed `analysis/reference/tvb6_*` artifacts during planning.

## Context

The TFC baseline (timeframe-continuity gated breakout + regime layer + governor v2)
is fully characterized in TradingView on ONE instrument, ONE 7-month path -- single-
sample fragility is the binding constraint (TVB-6). Direction: breadth -- many
symbols, longer history -- via a Python engine in `vectorbt-workspace`. TV stays the
fidelity anchor. HARD GATE (user-mandated): the Python engine must reproduce the TV
backtest TRADE-FOR-TRADE on the committed venue-verified xyz bars before ANY Python
number enters the record.

User-approved forks (AskUserQuestion, this session):
1. **Engine shape: custom bar-loop simulator** (not VBT-native callbacks). The
   governor reads net closed-trade PnL (simulation feedback), entries are one-bar
   resting stops armed only when flat, sizing is 100%-equity compounding -- and
   trade-for-trade equivalence leaves no room for VBT's own fill conventions. VBT
   Pro enters only at the breadth layer (optional `Portfolio.from_orders` wrap for
   tearsheets, behind the mandatory 5-step MCP workflow).
2. **Hard gate = 4-cell mechanism cover**: ctrlB@0.0125s1 (gate mechanics, 4,308
   trades), R1E1@0.0125s1 (regime), R1E1gov2@0.0125s1 (governor), R1E3@0.0125s1
   on 60m (TF-set + chart-TF variation). PLUS 4 secondary regression cells in the
   same parametrized test (same code, ~1s each): ctrlB@0.0125_s10 (slippage inside
   the qty basis), ctrlBgov2@0 (zero-fee governor regression; gross==net there, so
   it is insensitive to the gross-arming correction above -- the fee'd gov2 cells
   are the sensitive ones), ctrlBgov2@0.0125 (governor at scale), ctrlA@0.0125 60m
   (W/M warmup in the EXEC gate). Governor v1 dumps EXCLUDED (pre-v2 script
   revision).
3. **Breadth universe: crypto perps first** (OKX REST + Hyperliquid candleSnapshot);
   equities (RTH gaps, session-anchored periods) are a separately-designed later
   phase -- only the seam is built now.

## Calibrated facts (verified against committed dumps during planning -- treat as spec)

- Bar files: `tvb6_tv_xyzMSTR_{15m,60m,1D}.json`, `bars=[[epochSec,o,h,l,c,v],...]`,
  epochSec = bar OPEN, UTC; 1D anchors 00:00 UTC. 15m: 19,778 bars to Jul-3 19:45Z.
- Dump trade rows `{et,xt,ep,xp,dir,pp,pv,q,ddp,rnp,open}`: et/xt = FILL-bar open
  times (ms). `pp = pv / equity_before_entry`.
- PnL: `pv = q*sign*(xp-ep) - comm_rate*q*(ep+xp)`; commission on each fill's
  notional at the SLIPPED price (worst reconstruction error 4.9e-5 from dumps).
- **Qty convention (calibrated): `q = floor(equity / (basis*(1+comm_rate)) / step)*step`,
  step=0.001, basis = stop +/- slip*mintick (the expected slipped stop fill, NOT the
  actual fill when a bar gaps through).** 0 mismatches on R1E1/R1E3; 1-3 per 4,300
  on ctrlB family, all one-step floor-boundary cases attributable to serialized-pv
  equity chaining -- expected to vanish at full precision (fallback: epsilon-floor).
- Fills: entry stop fills at `stop +/- slip` intrabar, at `open +/- slip` when the
  bar opens through the stop; exits at next-bar open, slippage adverse.
- Pine semantics spec (verified line-by-line, `pine/baseline_continuity.pine`):
  gate = close strictly >/< ALL enabled period opens (equality or na => neutral;
  na until a TF's first period boundary -- `change[0]=False` is load-bearing);
  exits submitted before entries; one-bar re-arm gap; governor captures the TRIGGER
  (`high[1]+mintick`) on the fill bar, arms on GROSS profit <= 0 exits [CORRECTED
  2026-07-04: the TVB-7 Codex-review diagnostic proved `strategy.closedtrades.
  profit()` is GROSS of commission in this TV build -- an earlier draft of this spec
  said "net", which would have failed the gate cells; see the TVB-7 synthesis in
  docs/TVB2_control_AB_rerun.md], resets on winning (gross > 0) same-dir exit OR
  full-opposite exec alignment (loss-arm BEFORE alignment-reset, same bar); entries
  armed only when flat, stop lives exactly one bar.

## Where it lives (vectorbt-workspace; mirrors `strat/backtesting/futures/` precedent)

```
strat/backtesting/tfc/
  config.py         TFCConfig dataclass + Pine f_guard validation (loud errors)
  periods.py        UTC period ids (intraday ts//secs; week (ts//86400+3)//7 Monday-
                    anchored; month via datetime64), period_open_series (valuewhen
                    semantics, NaN before first boundary), ftfc() aggregation
  simulator.py      simulate(bars, cfg) -> SimResult; _simulate_core() two-phase loop:
                    Phase A (fills at open i): pending exit fill -> pending stop fill
                    (gap-through => open fill; qty from calibrated rule) -> clear stops
                    Phase B (close i, Pine order): exits -> governor (capture, loss-arm,
                    alignment-reset, ok-flags) -> entries (flat only) -> bookkeeping
                    Pure NumPy first; @njit(cache=True) only AFTER the gate passes
  tv_reference.py   loaders (validate dump asserts) + REFERENCE_CELLS registry
  equivalence.py    compare_prefix(): prefix window = dump rows with xt <= last bar ts;
                    require sim count == k; open-position boundary check; et/xt/dir
                    exact, ep/xp <= 1e-9, q within step/2, pp <= 1e-9 (pv ~ serialization
                    tol); report first-mismatch context
  data_providers/   (phase B) base.py Protocol; okx_provider.py (history-candles,
                    paginated, throttled; fetch INTRADAY ONLY -- OKX HTF candles anchor
                    UTC+8, avoid by resampling locally); hyperliquid_provider.py
                    (candleSnapshot, ~5000-candle cap recorded in cache meta);
                    utc_resampler.py (UTC roll; unit-tested vs committed TV 1D file);
                    reuse futures ParquetCache(cache_dir="data/perp_cache")
  runners/breadth_runner.py  (phase B) TFCRunSpec grid per equity162 sweep precedent
scripts/tfc_qty_calibration.py | tfc_gate_report.py | tfc_breadth_sweep.py
tests/test_backtesting/test_tfc/  (+ register `tfc_gate`, `network` markers -- strict)
tests/fixtures/tfc_reference/     8 dumps + 3 bar files (~4.7MB) COPIED + committed
                                  with MANIFEST.json (source commit + sha256); env var
                                  TFC_REFERENCE_DIR enables extended sibling-path sweep
```

## Sequencing (phase boundaries are gates)

- **Phase 0**: fixtures + loaders + `tfc_qty_calibration.py` as a committed testable
  fact (dump-driven, NO simulator yet).
- **Phase 1**: `periods.py` + tests (monthly NaN until Jan-1 on the 15m file; weekly
  seeds Monday Dec-8; 240m ids on 60m bars).
- **Phase 2**: simulator to a full 4,308-trade prefix match on ctrlB@0.0125s1, driven
  by `tfc_gate_report.py` first-mismatch output; micro-behavior unit tests on real
  bar slices (re-arm gap, gap-through fill, governor arm/reset).
- **Phase 3 = THE GATE**: all 8 cells green (0 field mismatches in prefix window).
  POLICY: no Python breadth number is recorded anywhere before this test is green.
- **Phase 4**: providers + cache + resampler; HL provider cross-checked against the
  committed `tvb6_hl_xyzMSTR_15m.json` overlap; live-fetch tests marked network/slow.
- **Phase 5**: breadth runner + sweep CLI; xyz-MSTR-on-HL-bars pilot as sanity anchor;
  grid = R/E cells x fees {0, 0.0125} x slippage {1,10}; per-run JSON artifacts with
  coverage metadata; metrics computed from trades/equity directly (TV-comparable);
  optional VBT from_orders wrap LAST via the 5-step MCP workflow + guardian markers.

## Risks (ranked, from planning verification)

1. Qty floor-boundary flips (1-3/4,300 under serialized-pv chaining) -- expected to
   vanish at full precision; epsilon-floor fallback must pass ALL cells or the
   specific trades get adjudicated against a fresh TV export.
2. pp tolerance chaining (equity compounds every prior trade) -- loosen to rel 1e-8
   only if trades are otherwise exact; report per-cell max diffs.
3. size_down qty basis UNVERIFIED (no tvb6 R2 dump exists) -- size_down is EXCLUDED
   from recorded breadth cells (S8 ratified stand_aside anyway); capture a TV R2 dump
   first if it's ever needed.
4. Week/month anchors implicitly proven by R1E1 + ctrlA cells (errors break trade
   sequences immediately).
5. Venue caps at breadth (HL ~5000 candles, OKX pagination/floors) -- recorded in
   cache meta + run artifacts so short histories can't masquerade as long backtests.

## Session logistics

- Implementation runs in a **vectorbt-workspace session** (its CLAUDE.md + hooks
  govern; `backtesting-validation` skill mandatory; `strat-methodology` invoked
  before the continuity-port code -- the charter's close-vs-period-open gate governs
  over the skill's bar-type TFC, per the TVB-1 reconciliation; VBT 5-step workflow
  only at the optional VBT touchpoint).
- This session (TVB-7) closes the loop by recording the approved design in
  `tradingview-backtesting` (datasheet/HANDOFF pointer + commit this plan doc into
  `docs/VBT_BREADTH_PORT_PLAN.md`) at session-end.
- Equities seam: `periods.py` functions stay behind a future `PeriodIndexer`
  protocol; the simulator only consumes precomputed gate/permit arrays, so session-
  anchored logic never touches the core loop.

## Verification

- The gate itself is the verification: `tests/test_backtesting/test_tfc/
  test_equivalence_gate.py` parametrized over the 8 REFERENCE_CELLS, hard-gate 4
  first; `scripts/tfc_gate_report.py` prints per-cell first-mismatch context.
- Provider fidelity: HL fetch vs committed HL candles overlap; resampler vs
  committed TV 1D bars.
- Breadth pilot: xyz MSTR on HL venue bars ~ reproduces gate-cell economics
  (documented venue-bar differences allowed).
