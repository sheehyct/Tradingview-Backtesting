# tradingview-backtesting -- Development Rules

> Sibling project under `C:\Strat_Trading_Bot\`. INHERITS the spine rules in
> `C:\Strat_Trading_Bot\CLAUDE.md` (safety, communication, conventional commits).
> This file SUPPLEMENTS the spine with rules specific to this workspace.
>
> **Governing design document:** `docs/ATLAS_Timeframe_Continuity_Charter.md`. It is a
> CHARTER, not a frozen spec -- read its Section 0 before doing any work here. Where this
> file and the charter touch the same topic, the charter's reasoning wins; cite it.

## 1. What this workspace is

Exploration of **timeframe-continuity (TFO/TFC) gated strategies** on **24/7 crypto and
HIP-3 builder-deployed perpetuals** (Hyperliquid, OKX proxy perps, related crypto/equity
perps). The backtest vehicle is **TradingView**, not a Python engine (see Section 4).

This is a research workspace. Its product is **characterization and bug-finding**, not a
deployed strategy. See the exploration protocol (Section 7) and the charter Section 5.

## 2. Epistemic stance (BINDING -- from charter Sections 0-1)

These are operating beliefs, not suggestions. Do not re-litigate them; apply them.

- **Generating data is not selecting on it.** Running 30 timeframe combinations and reading
  the distribution is exploratory analysis. Picking the top performer and deploying it is the
  overfit. This workspace does a lot of the first and is deliberately cautious about the second.
- **Backtest to KILL the strategy, not to confirm it.** A run made to confirm is worthless --
  with enough free parameters it always confirms. Optimize for finding the regime where it
  dies and the bar where the logic breaks.
- **There is no best combination; that is the premise, not a problem.** The spread across
  combinations IS the finding. A tight cluster of great results is suspicious.
- **Treat extreme metrics as questions, not verdicts.** Sharpe 3-4 or 95/100 wins is where the
  investigation STARTS (sizing? exit bug? kind period?), not a target hit.
- **Deviation-with-justification is the EXPECTED mode.** If mid-build you find something that
  contradicts the charter or this file, SURFACE it. Do not suppress that instinct in the name
  of "following the spec." That pushback is the desired behavior here.
- **Navigate by the structural-vs-sample gradient.** A parameter set by a structural reason
  generalizes; the same form tuned because it backtested best does not. The signature of the
  bad kind is a generalization gap (great in-sample, dead out-of-sample).

If you are ever about to say "the data shows X is optimal, so we shouldn't try alternatives"
-- STOP. That is the category error. Generate the alternatives anyway.

## 3. Mandatory skills (ZERO TOLERANCE)

Invoke BEFORE writing related code (use the Skill tool):

| Skill | Invoke when |
|-------|-------------|
| `strat-methodology` | ANY bar classification (1/2U/2D/3), continuity logic, trigger/stop/target mechanics, or Pine detection code. The charter is STRAT-derived; this is the authority. |
| `position-sizing-risk` | Any position-sizing / regime-layer size-scaling work (charter Section 3.3). |

The spine's "Skill Methodology Ambiguity Policy" applies in FULL: if the skill seems wrong,
contradictory, or in conflict with the charter or code, **STOP and ASK.** Writing Pine
detection/continuity logic is a STOP-and-ASK zone -- design with the user first.

## 4. Implementation vehicle: TradingView `strategy()` (charter Section 4)

- Use TradingView's **`strategy()`** script type, NOT `indicator()`. It simulates entries/exits,
  produces the full Strategy Tester backtest, and fires webhook alerts on simulated fills.
- Bake the **entire compound logic into ONE script** (trigger + TFO gate + stop + target) and
  put **one alert** on it ("order fills only"). Do not split logic across code and the
  multi-condition alert UI.
- The signal is only TWO conditions: (1) the **trigger** (a level break) and (2) the **TFO is
  FTC-aligned** in the trade direction. The TFO already aggregates the per-timeframe flags.
- **2U timing:** a bar is a 2U the instant price trades through the prior high -- the same
  instant as the trigger and entry, NOT at bar close. Trigger off the raw level cross
  (`high > high[1]`), NOT an indicator's painted bar-shape series. Evaluate **once-per-bar**,
  not once-per-bar-close, or you reintroduce lag.
- The TradingView MCP server (`tradingview`) is the primary instrument for driving the chart,
  injecting/compiling Pine, reading the Strategy Tester, and capturing screenshots. See
  `docs/guides/TRADINGVIEW_MCP_SETUP.md`.

## 5. Data sources (crypto perps -- NOT the ATLAS equity rules)

The ATLAS/equity orthodoxy (Alpaca, RTH, weekend/holiday filters, closing auction) does NOT
transfer here and assuming it does is itself an unexamined prior (charter Section 2).

| Source | Use |
|--------|-----|
| TradingView native chart data | The backtest data -- loaded by symbol on the chart. |
| OKX public REST (perp candles) | The reference/proxy for the underlying outside RTH (~98% `MSTRUSDT`-class). Python analysis only. |
| Hyperliquid SDK | HL perp / HIP-3 reference data for analysis. |

- The "day" rolls at **00:00 UTC** (no market bell, no overnight gap, no closing auction).
- NEVER synthetic/mock OHLCV.
- Backtesting on the OKX proxy while executing on Hyperliquid is a **venue mismatch** -- basis
  and after-hours structure differ; do not treat the proxy backtest as identical to live HL.

## 6. Backtest traps -- MUST respect (charter Section 7)

1. **`request.security` lookahead is the cardinal trap.** Lookahead-on lets the script see the
   HTF bar's outcome before it would be known live and makes the whole backtest fiction. Use
   `lookahead_off` + confirm-on-close offsets. **Audit every `request.security` call.**
2. **Intrabar fill approximation** -- enable bar-magnifier / lower-timeframe data, or the
   intrabar level-break entry reads optimistic.
3. **Venue mismatch** (Section 5).
4. **Regime flattery** -- a continuity-gated trend system looks gorgeous in a trend and bleeds
   in chop. Weight performance BY regime; hunt the regime where it dies.

## 7. Exploration protocol (charter Section 5): ablation, not tournament

- Run many timeframe-set combinations (both layers) across distinct regimes **against a
  control baseline** = `{2-trigger + TFO-gate + state-stop}` with a fixed, a-priori TF set.
- Expect numbers all over the place -- the spread is the signal. Always compare to the control.
- For poor combinations, ask WHY (mechanism). For surprising results, FLAG them explicitly --
  surprises are a primary deliverable, not noise.
- **Do NOT build a pattern tournament.** Keep at most ONE thing from the pattern world
  (compression = a "1" preceding the break; possibly the "3"/expansion) as a binary feature
  with a prior. Test it by ablation vs the continuity-only baseline; keep only if it beats it.
- **Timeframe sets are chosen a-priori and then NOT tuned on the sample.** Choosing
  "W/D/12h vs M/W/D" by performance is overfitting with fewer knobs. Choose, accept, don't tune.

## 8. Communication & session protocol (inherits spine)

- ASCII only, NO emojis/unicode. NO AI attribution. Conventional commits (`feat:`/`fix:`/
  `docs:`/`test:`/`refactor:`). Professional, declarative tone.
- Ticket prefix for this workspace: **`TVB-NNN`** (TradingView Backtesting). Session N+1 is
  seeded in `.session_startup_prompt.md` by `/session-end`.
- Session start: read `docs/HANDOFF.md`, then `.session_startup_prompt.md`, then this file.
  `/session-start` automates it. Session end: `/session-end`.
- Timestamps: market data in UTC (24/7 perps); system events in UTC.

## 9. Account / live-trading constraints

- This workspace is **research only**. No live order execution is wired and there is **no
  broker/account attached to TradingView** (see the MCP setup guide). If that ever changes,
  re-read the broker-safety section of the master MCP install guide first.
- `replay_trade` (TV MCP) is replay-simulation only by implementation -- it never touches a
  live broker.

## 10. DO NOT

- Skip the charter's Section 0 or this file at session start.
- Skip `strat-methodology` before writing any bar/continuity/Pine detection logic.
- Build a pattern tournament, or tune timeframe sets on the backtest sample.
- Leave `request.security` on lookahead, or report a backtest without auditing for it.
- Inherit the equity-RTH data orthodoxy (Alpaca, weekend filters) for these 24/7 perps.
- Use synthetic/mock OHLCV, emojis, or AI attribution.
- Treat an extreme metric as a verdict instead of a question.
- Refuse to engage with a mid-development discovery because "that's not what the spec says."

---
**Version:** 0.1 (2026-06-27, bootstrap). Supplements `C:\Strat_Trading_Bot\CLAUDE.md`.
