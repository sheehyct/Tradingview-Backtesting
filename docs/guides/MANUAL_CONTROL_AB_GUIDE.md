# Manual Control A/B backtesting guide (TradingView, no MCP)

How to run the canonical control strategy on any perp ticker by hand, exactly the
way the TVB sessions run it, so your numbers land in the same datasheet-comparable
format. Written for someone who has not used the TradingView Strategy Tester before.

## What you are running

- The strategy is **"TFC Baseline"** in your TradingView Pine library (byte-identical
  to `pine/baseline_continuity.pine`). It is a CONTROL: {2-trigger level break +
  FTFC continuity gate + close-based state-stop}, bidirectional, 1x, no target.
- Two fixed configurations. Do NOT invent new TF sets per ticker (charter S5/S7 --
  sets are a-priori; tuning them on the sample is the overfit):
  - **Control A** = gates M / W / D / 60 on a **60-minute chart**
  - **Control B** = gates 60 / 30 / 15 on a **15-minute chart**
- Ticker universe: 24/7 crypto/equity **perps** (e.g. `OKX:MSTRUSDT.P`-class). RTH
  instruments (stocks, CME futures) break the premises (gaps, sessions) -- skip them.

## Per-run procedure

1. **Symbol**: type the perp ticker into the symbol box (e.g. `OKX:COINUSDT.P`).
2. **Chart timeframe = the LOWEST enabled gate TF**: 60m for Control A, 15m for
   Control B. The script throws a loud red runtime error if any enabled gate TF is
   finer than the chart -- that error means your chart TF / enables disagree.
   Stick to exactly 60m/15m; odd chart TFs that do not divide the gate TFs make the
   period-open reconstruction approximate (Codex TVB-3 finding).
3. **Add the strategy**: Indicators button (top toolbar) -> "My scripts" /
   Personal tab -> **TFC Baseline**. (Alternative: Pine Editor -> Open -> TFC
   Baseline -> "Add to chart".) NEVER edit the source -- inputs and properties
   only. If the editor ever shows a 3-line "E2E Test" stub instead of ~170 lines,
   the slot got clobbered; restore from `pine/baseline_continuity.pine`.
4. **Inputs** (double-click the strategy label on the chart, or its gear icon ->
   Inputs tab): six TF rows with checkboxes.
   - Control A: check M, W, D, 60; uncheck 30, 15.
   - Control B: check 60, 30, 15; uncheck M, W, D.
   - Leave Allow Long / Allow Short both ON (the controls are bidirectional).
5. **Properties tab** (same dialog):
   - **Commission**: this is your fee ladder knob (percent PER FILL). Run the run
     at each of **0**, **0.0086**, **0.0125** (real xyz taker band; 0.1 only if you
     want the HIP-3 bridge comparison). NEVER report a single-fee verdict --
     knife-edge configs (B!) flip sign inside the real-fee band.
   - **Slippage**: leave at 1 (tick). Note different tickers have different tick
     sizes, so "1 tick" is a different %-cost per ticker -- worth a note column.
   - **"Use bar magnifier"**: leave UNCHECKED (verified immaterial for this
     state-stop architecture in TVB-4, but keep OFF for comparability).
   - Margin long/short: should read 0 / 0 (baked into the script -- protects
     against the TV margin-call deadlock artifact from TVB-3).
6. **Load FULL history -- this is the step everyone misses.** TradingView only
   backtests bars loaded on the chart. Grab the chart and fling it left repeatedly
   (or hold left-arrow) until it stops loading older bars. Then check the Strategy
   Tester trade list: the FIRST trade's date tells you where the compute actually
   starts. Record the window (first bar date -> now). Data floors differ per
   ticker; that is fine, just record them.
7. **Read results**: open the **Strategy Tester** tab (bottom panel) ->
   "Performance" / performance summary (not just the Overview headline). Record
   from the ALL column plus the Long/Short columns.
8. **Sanity gates -- check EVERY run before recording** (contamination signatures
   from TVB-3):
   - **Margin calls = 0.** If > 0 the run is invalid (emulator liquidation
     artifact) -- do not record it, flag it.
   - **Open trades = 0 or 1** (one live position at the right edge is normal). If
     the trade list simply STOPS months before today, the strategy is deadlocked
     on a stuck position -- run invalid, flag it.
   - Trade count plausibility: B runs ~8-10x more trades than A on the same window.

## Record one row per run

| ticker | control | fee % | window | B&H % | trades (L/S) | net % | PF | win % | maxDD % | Sharpe | margin calls | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

"B&H %" = the Strategy Tester's Buy & hold return for the same window -- it is the
regime context (a continuity gate flatters in trends, bleeds in chop; charter S6.4).
Notes: tick size, data floor, anything weird.

## Discipline (charter, short version)

- Pick your ticker list BEFORE looking at any results; run the whole list; record
  the ugly ones. The SPREAD across tickers is the finding -- a tight cluster of
  great results is suspicious, not reassuring.
- You are generating data, not selecting on it. Do not crown the best ticker; do
  not drop the worst; do not adjust anything per-ticker.
- Treat extreme numbers as questions (sizing? stuck trade? kind window?), not wins.
- These venues are PROXIES for HL execution -- basis/liquidity differ (venue
  mismatch, charter S7.3). Characterization only, no deployability verdicts.

## Reference values to validate your procedure (OKX:MSTRUSDT.P, window 2026-02-25 -> 2026-07-03)

- A @ 0.0125%: about **+38%**, ~317-319 trades, PF ~1.24, maxDD ~16%.
- B @ 0.0125%: about **-7 to -10%** (knife-edge; moves with the window tail).
- B @ 0%: about **+82-87%**.
If your first MSTR run is far off these, the usual cause is not enough history
loaded (step 6) or a TF-enable mismatch (step 4).

## Troubleshooting

- Strategy missing from Indicators: use the dialog's search box, "TFC Baseline",
  Personal/My scripts tab.
- Red exclamation on the strategy: open its tooltip -- if it is the gate-TF guard,
  your chart TF is coarser than an enabled gate TF.
- Tiny trade counts / short window: history not loaded (step 6).
- Empty Strategy Tester: the strategy is not the selected report -- click the
  strategy's name in the Strategy Tester's dropdown.
- Changing inputs/properties re-runs the backtest automatically; give it a few
  seconds on big windows before reading numbers.
