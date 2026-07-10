# Experiment Prompt for GPT -- BF-Deviation Exit Ablation (TVB-EXP-BF1)

Copy everything below the line into the GPT session after it has completed MCP setup
per `GPT_TVMCP_GUIDE.md`. Claude Code runs the identical experiment first; the user
wants to compare the two agents' independent implementations and results.

---

## Role and context

You are assisting with a live-trading research experiment in the workspace
`C:\Strat_Trading_Bot\tradingview-backtesting` (read its `CLAUDE.md` and
`docs/guides/GPT_TVMCP_GUIDE.md` first; obey both). The user trades a
timeframe-continuity (TFC) system manually with real money, entering on full
timeframe-continuity alignment and currently exiting either on the strategy's own
exit or on a Broadening Formation (BF) line deviation, whichever hits first. The
question: **does adding the BF-deviation exit to the TFC strategy improve exits over
the strategy's native exit alone?**

This is EXPLORATORY data collection. The user explicitly accepts slight overfitting
(the signals are being traded live either way); your job is honest measurement and
characterization, not promotion. Still avoid actual backtest fraud: no lookahead
(`request.security` only with the completed-bar `[1]` + `lookahead_on` idiom or
`lookahead_off`), no synthetic data, record the test window.

## Reference sources (read before coding)

- `pine/tfc_companion.pine` in the repo (v5) -- the entry/exit state machine you must
  replicate. Its header documents the semantics precisely.
- The user's BF indicator source -- `c:\Users\Chris\Downloads\bf.txt` (Broadening
  Formation MTF [BF-1] v1). Port its pivot + trendline + deviation engine verbatim.
- `docs/ATLAS_Timeframe_Continuity_Charter.md` Section 0 (epistemic stance) and
  Section 7 (backtest traps).

## The user's live configuration (fixed for all cells; read off the live chart)

- Symbol: `HIP3XYZ:AMZNUSDC.P`, chart timeframe 5m.
- Strategy (logic) TF: 15m -- all exit decisions commit at 15m closes.
- Execution gate: FULL continuity, close vs CURRENT period open of ALL SIX TFs:
  60, 120, 240, D, W, M (unanimous; any mixed/flat = grey).
- Regime layer: stand_aside on W + D (M unchecked). Note: redundant for entries given
  D/W/M sit inside the gate; implement anyway for fidelity.
- Entry arming: INTRABAR -- the breakout stop is in force the instant the live gate
  aligns, at the prior COMPLETED 15m bar's high + 1 tick (long) / low - 1 tick
  (short), and is revoked the instant the live gate unaligns. On historical bars this
  is chart-TF-grade (5m).
- Governor: ratchet ON, slippage 1 tick (inert under flip exits -- known TVB-10
  result -- but keep it for fidelity).
- BF indicator: pivot timeframe 30m, pivot strength 10, engine per bf.txt.
- Both directions enabled.

## Experiment cells (6)

One strategy() script, two inputs; sweep via `indicator_set_inputs`:

| Cell | exit_mode | bf_exit |
|---|---|---|
| 1 (live control) | flip | off |
| 2 (deployed control) | state | off |
| 3 | flip | same_side |
| 4 | flip | any_side |
| 5 | state | same_side |
| 6 | state | any_side |

Exit definitions:
- `state`: exit at the first 15m close where the gate is no longer fully aligned with
  the position (grey exits). Fills at the next 15m open.
- `flip`: exit only when the gate reaches full OPPOSITE alignment; holds through grey.
  Fills at the next 15m open.
- `bf same_side`: while LONG, a resting sell LIMIT at the projected UPPER broadening
  line (exhaustion harvest); while SHORT, a resting buy LIMIT at the projected LOWER
  line. First of {BF fill, native exit} wins.
- `bf any_side`: same_side PLUS the adverse line as a protective STOP -- long also
  exits on a break of the LOWER line, short on the UPPER (the "stop the bleed" arm).
- After any exit, cancel all working exit orders. BF exit orders track the line
  projection bar by bar (recompute the projected level for the next bar each bar);
  when the BF engine invalidates/freezes a line, the corresponding order is cancelled
  until a new formation validates.

## Strategy properties (identical across cells)

```
strategy(..., overlay=true, initial_capital=10000,
         default_qty_type=strategy.percent_of_equity, default_qty_value=100,
         commission_type=strategy.commission.percent, commission_value=0.0125,
         slippage=1, margin_long=0, margin_short=0, use_bar_magnifier=true)
```

`margin_long=0, margin_short=0` is deliberate (avoids TradingView margin-call
deadlock artifacts -- known TVB-3 issue). If bar magnifier is unavailable on the
account plan, drop it and say so in the report.

## Implementation requirements

1. Create your OWN new Pine script named `TVB-EXP BF Exit [GPT]` using the
   "Make a copy" UI procedure in the MCP guide section 7 -- do NOT use `pine_new`
   (it silently reuses the current tab's cloud binding and will overwrite a user
   script; this bit Claude on 2026-07-10). NEVER touch the existing user scripts
   (especially `TFC Baseline` -- the anchored strategy slot -- and the Companion/BF
   indicator scripts). After every save, verify via `pine_list_scripts` that only
   YOUR script's modified stamp changed. Claude's results for comparison live in
   `docs/experiments/tvb_exp_bf_exit_2026-07-10.md` -- do NOT read it before
   producing your own numbers if the user wants an independent replication.
2. Gate reconstruction: NO `request.security` for the gate -- reconstruct each TF's
   current period open locally via `ta.valuewhen(timeframe.change(tf), open, 0)`
   (this is the TVB-3 staleness fix; the Companion does exactly this). Guard that the
   chart TF tiles the logic TF and the logic TF tiles every gate TF.
3. BF engine: port from bf.txt -- 30m fractal pivots via
   `request.security(..., [value[1], ...], lookahead = barmerge.lookahead_on)`
   (completed-bar idiom, non-repainting BY CONSTRUCTION -- audit it, then leave it),
   absolute bar_index anchors, chart-TF validation walk, deviation = live high/low
   crossing the projected line.
4. Entry engine mirrors Companion v5 intrabar arming: evaluate the live gate each
   chart bar; while aligned+permitted, keep `strategy.entry` stop order at the prior
   completed 15m extreme +/- 1 tick; cancel when unaligned. Long priority if both
   (matches Companion).
5. Native exits: decide on the LAST 5m bar of each 15m period (its close IS the 15m
   close) and place a market exit so it fills at the next 5m open = the 15m open.
6. Known fidelity deltas to disclose, not fix: strategy orders placed at bar N fill
   from bar N+1 (the Companion can fill same-bar), so entries can lag the Companion
   display by up to one 5m bar; historical intrabar granularity is 5m, not tick.

## Procedure

1. `tv_health_check`; re-stage chart to `HIP3XYZ:AMZNUSDC.P` @ 5m if needed.
2. Build + compile the script (zero errors) and add it to the chart.
3. For each of the 6 cells: set the two inputs via `indicator_set_inputs`, allow
   recompute, then capture `data_get_strategy_results` and `data_get_trades`, plus a
   `strategy_tester` screenshot per cell.
4. Record for every cell: net profit (abs and %), gross profit/loss, profit factor,
   total trades, win rate, max drawdown, avg trade, long vs short split, first and
   last trade timestamps (the window), and open-trade P/L if any.
5. Sanity checks before reporting: identical entry COUNTS+timestamps across cells
   sharing exit_mode=flip vs state is NOT expected (exits recycle into re-entries),
   but cell 1 vs 3 vs 4 must share the same FIRST entry; if not, entries got
   contaminated by the exit change -- find the bug. Zero-trade or 100%-win cells are
   bugs or artifacts until proven otherwise (treat extreme metrics as questions).

## Report format

A compact table of the 6 cells x metrics, then plain-prose findings: did BF exits
help, on which exit mode, and WHY mechanically (earlier harvest? cut bleed? churn?).
Compare trade-by-trade where informative (which exits fired: BF limit, BF stop, or
native). State every fidelity caveat: in-sample, one symbol, one regime window, young
listing, 5m intrabar grade, order-lag delta, resting-limit vs exit-on-alert
semantics. Flag surprises explicitly -- surprises are a primary deliverable. Do NOT
conclude "deploy X"; conclude "the data shows X under these caveats."

Also answer the user's standing question honestly: the BF exit "hits first" almost by
construction (any resting level inside the path hits before a 15m-close-decided
exit). Quantify whether hitting first actually IMPROVED the exit price vs the native
exit on the same trades, which is the real test of whether this is signal or just
selection bias toward early exits.
