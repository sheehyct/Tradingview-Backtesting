# pine/ -- TradingView strategy() scripts

This directory holds the TradingView Pine scripts that ARE the backtest vehicle for this
workspace (charter Section 4). The Strategy Tester output + webhook alerts come from these.

> **This README is a SPEC, not an implementation.** No strategy logic is written yet on
> purpose. Writing the bar-classification / continuity / trigger logic is a
> **strat-methodology STOP-and-ASK zone** -- invoke the `strat-methodology` skill and design
> the baseline WITH the user before coding (CLAUDE.md Sections 3-4; spine ambiguity policy).

## Conventions

- Use **`strategy()`**, never `indicator()`, for anything that gets backtested.
- One script = the entire compound condition (trigger + TFO gate + stop + target). One alert
  on it ("order fills only"). Do not split logic across code and the alert UI.
- File naming: `baseline_continuity.pine`, then variants like
  `var_a_compression_filter.pine`, `var_b_reversal_context.pine` (charter Section 5 ablation).
- Header comment block in every script: purpose, the exact timeframe set(s) fed to each TFO
  layer, the stop type (price vs state), and a one-line note on which charter section it tests.

## Hard requirements (charter Sections 3.4, 6 -- these are correctness, not style)

1. **Trigger off the raw level cross** -- `high > high[1]` (long) / `low < low[1]` (short), or
   the stored prior-bar level being crossed -- NOT an indicator's painted bar-shape series.
2. **Evaluate once-per-bar, not once-per-bar-close.** `calc_on_every_tick` / alert frequency
   must not reintroduce close-lag on the intrabar break.
3. **Every `request.security` call uses `lookahead_off`** and confirm-on-close offsets. This is
   THE trap that makes the whole backtest fiction -- audit it in code review every time.
4. **Enable the bar-magnifier / lower-timeframe data** in the Strategy Tester, or the intrabar
   level-break entry reads optimistic.

## The baseline (control) to build first

`{2-trigger (raw level cross, once-per-bar) + TFO FTC-gate + state-stop}` with a FIXED,
a-priori timeframe set chosen by reasoning (e.g. regime layer `M/W/D` or `W/D/12h`; execution
layer `60/30/15`) and then NOT tuned on the sample. Two TFO layers (charter Section 3.3):

- **Regime layer (slow):** governs position size (grey -> size down or stand aside -- OPEN
  question, charter Section 8). Red/green -> execution layer may trade that direction.
- **Execution layer (fast):** generates the signal; state-stop exits when the lowest
  execution-TF bar closes neutral/opposite.

Everything beyond the baseline (compression filter, reversal-vs-continuation, vol-conditional
timeframe sets) is tested by **ablation against this control**, never added by default.

## Implemented: `baseline_continuity.pine` (TVB-1)

ONE parameterized `strategy()` expresses both a-priori controls via the gate-timeframe inputs:

| Control | Gate set | Chart TF | Set inputs |
|---------|----------|----------|------------|
| **B** (file default) | `60/30/15` | 15m | enable y4/y5/y6 (60/30/15) |
| **A** | `M/W/D/60` | 60m | enable y1/y2/y3/y4 (M/W/D/60), disable y5/y6 |

Mechanics: trigger = breakout STOP at the prior bar's high/low (intrabar fill, no
`calc_on_every_tick`); gate = `close > period-open` per enabled TF (`lookahead_off`);
exit = close-based state-stop when the gate de-aligns. `leverage` input scales notional
(set `=1` for sizing-agnostic edge reads -- PF/win-rate are leverage-invariant).

**TVB-1 result (`OKX:MSTRUSDT.P`, Feb 25 - Jun 28 2026, 1x):** Control B = 2263 trades, PF 0.645,
~ -81% (churn/fees kill a raw-positive signal: zero-fee PF 1.284). Control A = 258 trades, PF
1.131 at OKX fees but **PF 0.921 at HIP-3 fees (0.10%)** -> not deployable at real venue cost.
Lever is **turnover / per-trade edge**, not the gate alone. Next: two-layer regime+execution
(charter Section 3.3). See `docs/HANDOFF.md` TVB-1.
