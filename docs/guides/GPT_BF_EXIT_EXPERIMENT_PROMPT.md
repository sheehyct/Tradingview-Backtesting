# Experiment Prompt for GPT -- BF-Deviation Exit Ablation v2 (TVB-EXP-BF1/E2)

Copy everything below the line into the GPT session after it has completed MCP setup
per `GPT_TVMCP_GUIDE.md`. Claude Code ran the identical experiment first (results in
`docs/experiments/tvb_exp_bf_exit_2026-07-10.md`); the user wants an INDEPENDENT
implementation and replication. Do NOT read Claude's results file before producing
your own numbers.

---

## Role and context

You are assisting with a live-trading research experiment in the workspace
`C:\Strat_Trading_Bot\tradingview-backtesting` (read its `CLAUDE.md` and
`docs/guides/GPT_TVMCP_GUIDE.md` first; obey both). The user trades a
timeframe-continuity (TFC) system manually with real money: enter on full
multi-timeframe alignment (intrabar, STRAT 2U-timing), exit on either the system's
own exit or a Broadening Formation (BF) line deviation -- whichever hits first --
and after a BF exit they do NOT re-enter on the same conditions. The questions:
does the BF exit improve on the native exit alone, and does re-entry hysteresis
(standing down after a BF exit) fix the churn that naive exit-racing creates?

This is EXPLORATORY data collection (user accepts slight overfitting; signals are
traded live either way). Honest measurement, not promotion. No lookahead
(`request.security` only via the completed-bar `[1]` + `lookahead_on` idiom or
`lookahead_off`), no synthetic data, record the test window per symbol.

## Reference sources (read before coding)

- `pine/tfc_companion.pine` (v5) -- the entry/exit state machine semantics.
- `c:\Users\Chris\Downloads\bf.txt` -- Broadening Formation MTF [BF-1] v1; port its
  pivot + trendline + deviation engine verbatim.
- `docs/ATLAS_Timeframe_Continuity_Charter.md` Section 0 and Section 7.

## Fixed live configuration (all cells)

- Symbols: `HIP3XYZ:<SYM>USDC.P` for SYM in {AMZN, XYZ100, MU, SPCX, CL}, chart 5m.
  (Universe = top xyz names by 24h volume from the user's HIP-3 screener + CL as
  a flagged discretionary add; SKHX/SKHY were selected too but have zero tradeable
  history -- a zero-trade or empty report is a VALID result there.)
- Execution gate: FULL continuity, close vs CURRENT period open of ALL SIX TFs:
  60, 120, 240, D, W, M (unanimous; anything mixed/flat = grey). NO
  request.security for the gate -- reconstruct period opens locally via
  `ta.valuewhen(timeframe.change(tf), open, 0)` (TVB-3 staleness fix).
- Regime layer: stand_aside on W + D (M unchecked) -- redundant given D/W/M in the
  gate; implement for fidelity.
- Entry arming: INTRABAR -- breakout stop in force the instant the live gate
  aligns, at the prior COMPLETED arming-TF bar's high + 1 tick (long) / low - 1
  tick (short); revoked the instant the gate unaligns. Long priority if both.
- Governor: loss-ratchet ON (TVB-6 semantics), slippage 1 tick.
- BF engine: pivot timeframe 30m, pivot strength 10, per bf.txt. IMPORTANT
  SEMANTICS: only line DEVIATIONS are real-time events. The pivot DOTS confirm
  `strength` pivot-TF bars after the turn BY DEFINITION (~5h at 30m/10) and must
  NOT be used as exit signals.
- Costs: commission 0.0125% per side, slippage 1 tick, margin_long=0,
  margin_short=0 (TVB-3 margin-call fix), initial 10000, 100% equity per trade,
  use_bar_magnifier=true (drop and disclose if the plan rejects it).

## Definitions

- Native exit `state`: exit at the first exit-TF close where the gate is no longer
  fully aligned with the position. `flip`: exit only on full OPPOSITE alignment.
  Decide on the LAST 5m bar of each exit-TF period (its close IS the period close)
  so the market exit fills at the next 5m open = the period open.
- BF exit `same_side`: while LONG, resting sell LIMIT at the projected UPPER line
  for the NEXT bar; while SHORT, buy LIMIT at the LOWER line. (`any_side` adds the
  adverse line as a protective STOP -- measured NEGATIVE by Claude's E0; you may
  skip it.) First of {BF fill, native exit} wins; cancel leftovers after any exit.
  Track line projections bar by bar; when the BF engine invalidates a line, cancel
  the order until a new formation validates.
- BF re-entry `recycle`: nothing blocks re-entry (the naive control -- if the gate
  is still aligned, the next breakout re-enters immediately).
- BF re-entry `ratchet` (the user's intended behavior): after a BF exit,
  same-direction re-entry only at a trigger STRICTLY beyond the most extreme price
  printed since that exit (track the running high/low from the exit bar). The
  block clears when the re-entry fills or when the gate reaches full OPPOSITE
  alignment at an exit-TF close. Zero parameters. TFC exits never set the block.
- arm_tf / exit_tf split: arm_tf = which prior completed bar extreme is the
  breakout trigger; exit_tf = the clock exits commit on (also the governor and
  BF-block reset clock). Guards: chart tiles arm_tf; arm_tf tiles exit_tf;
  exit_tf tiles every gate TF.

## Cells (6 per symbol, all flip exit mode; 30 runs)

| Cell | bf_exit | bf_reentry | arm_tf | exit_tf | Purpose |
|---|---|---|---|---|---|
| C1 | off | -- | 15 | 15 | control |
| C2 | same_side | recycle | 15 | 15 | naive exit race (churn control) |
| C3 | same_side | ratchet | 15 | 15 | re-entry fix, config otherwise unchanged |
| C4 | off | -- | 5 | 15 | arming split alone |
| C5 | same_side | ratchet | 5 | 15 | user's intended live system |
| C6 | same_side | ratchet | 5 | 30 | exit-clock comparison |

Build ONE strategy() script named `TVB-EXP BF Exit [GPT]` with these as inputs and
sweep via `indicator_set_inputs`. Create the script via the Make-a-copy UI flow in
the MCP guide section 7 -- do NOT use `pine_new` (it silently reuses the current
editor tab's cloud binding and will overwrite a user script; this bit Claude).
After every save, verify via `pine_list_scripts` that ONLY your script's modified
stamp changed. Never touch `TFC Baseline`, the Companion scripts,
`Broadening Formation MTF [BF-1]`, or `TVB-EXP BF Exit [Claude]`.

## Procedure

1. `tv_health_check`; stage each symbol at 5m; wait ~15s after a symbol switch and
   ~10s after every input change before reading results.
2. Per cell record: net profit (abs, %), profit factor, total closed trades, win
   rate, max drawdown %, open P/L, commission paid, long/short net split, and the
   first trade's entry timestamp.
3. Sanity checks: C1/C2/C3 must share the same first entry per symbol (same arming
   structure). C4/C5/C6 may differ from C1 -- the 5m trigger is a DIFFERENT
   structure, and can even be later/worse, not just earlier. If two consecutive
   cells return byte-identical results, re-read once after 10s before accepting.
   Zero-trade cells and extreme metrics are questions, not verdicts -- investigate
   before reporting.

## Report format

The 30-cell table, then per-question findings in prose: does the BF exit improve
the control; does ratchet re-entry fix the recycle churn and HOW (fewer re-entries
or better-priced re-entries? -- check the trade lists); what does the arming split
do alone; what does the exit clock do. Report BOTH closed-trade net AND net
including open P/L -- the two accountings can disagree about which cell wins
(harvest-vs-hold moves P/L between realized and unrealized). State all caveats:
in-sample, one ~10-week window, 5m intrabar grade, next-bar order fills,
resting-limit vs exit-on-alert semantics, young listings. Flag surprises
explicitly. Do NOT conclude "deploy X"; conclude "the data shows X under these
caveats."
