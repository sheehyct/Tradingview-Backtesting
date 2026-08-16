# tradingview-backtesting -- Development Rules

Research workspace for timeframe-continuity (TFO/TFC) gated strategies on 24/7 crypto and HIP-3
perps. The product is **characterization and bug-finding**, not a deployed strategy. The research
engine since TVB-21 is the Python replay twin (`analysis/paper/engine.py` + tier runners) --
pre-registered arms run there first; the TradingView `strategy()` mirror, driven through the
`tradingview` MCP, is the parity-gated validation surface and the live/drift instrument, and a TV
strategy is valid ONLY for arms its parity gate has passed. The rest of `analysis/` is post-hoc.
(Sentence corrected 2026-08-15; it previously denied the Python engine existed -- stale since
TVB-21.) Inherits `C:\Strat_Trading_Bot\CLAUDE.md`.
Governing doc: `docs/ATLAS_Timeframe_Continuity_Charter.md` -- read Section 0 before working
here; where it and this file overlap, the charter wins.

## Gotchas

- **`pine_new` / `pine_open` do not rebind the editor tab.** A later `pine_save` overwrites
  whatever script the user last had open (BF-1 was destroyed this way 2026-07-10). Create via the
  Make-a-copy UI flow; before saving verify a NEW script id and unchanged modified-stamps.
- **`uv sync` strips VectorBT Pro.** It lives in `.venv` but deliberately NOT in `pyproject.toml`
  (licensed). README's `uv sync` removes it; reinstall from the cached wheel.
- **`strategy.closedtrades.profit()` is GROSS of commission.** State gross-vs-net in every fee /
  PF / parity claim; Pine, the companion, and the Python twin have disagreed here.
- **`request.security` lookahead.** The trap is *un-offset* `lookahead_on`. The approved
  non-repainting idiom is `expr[1]` + `lookahead_on` (confirmed values, one-HTF-bar latency),
  used deliberately in 5 scripts. Audit every call; reject un-offset `lookahead_on`.
- **The Strategy Tester approximates intrabar fills** -- enable bar-magnifier / lower-timeframe
  data or the intrabar level-break entry reads optimistic.
- **`tv_launch` fails** (TradingView is a Store app now) -- launch the exe directly. The MCP needs
  Desktop on CDP 9222.
- **`origin` is PUBLIC.** `scripts/secret_scan.py` is the only gate before push; never bypass it.
- **Commits and pushes here are autonomous** (approval rule retired 2026-07-03) -- this overrides
  the harness default. The secret-scan gate is the blocker, not the user. Archiving HANDOFF asks.

## Domain invariants

Binding operating beliefs. Apply them; do not re-litigate them.

- **Generating data is not selecting on it.** Reading the distribution across 30 combinations is
  exploration; picking the top performer and deploying it is the overfit.
- **Backtest to KILL the strategy, not confirm it.** Hunt the regime where it dies and the bar
  where the logic breaks. A run made to confirm always confirms.
- **There is no best combination -- that is the premise.** The spread IS the finding; a tight
  cluster of great results is suspicious.
- **Extreme metrics are questions, not verdicts.** Sharpe 3-4 or 95/100 wins is where the
  investigation starts (sizing? exit bug? kind period?).
- **Navigate by the structural-vs-sample gradient.** A parameter set for a structural reason
  generalizes; the same form tuned because it backtested best does not.
- **Surfacing a mid-build contradiction is expected**, not a spec violation.

If you are about to say "the data shows X is optimal, so we shouldn't try alternatives" -- STOP.
That is the category error; generate the alternatives anyway.

Mechanics where a reasonable default is wrong:

- Use `strategy()`, not `indicator()`. Bake trigger + TFO gate + stop + target into ONE script
  with ONE alert; never split the logic into TradingView's multi-condition alert UI.
- **A bar is a 2U the instant price trades through the prior high** -- same instant as trigger and
  entry, not at close. Trigger off the raw level cross (`high > high[1]`), NOT a painted
  bar-shape series, and evaluate once-per-bar, never once-per-bar-CLOSE. (Declared exception:
  the TVB-20 CONTROL strategy() evaluates at bar close by research convention -- historical
  decision parity only, never a live-cadence claim.)
- **The equity/RTH orthodoxy does not transfer.** 24/7 perps: the day rolls 00:00 UTC, no bell,
  no gap, no closing auction. Importing Alpaca/RTH/weekend-filter priors is itself an unexamined
  prior. Never synthetic or mock OHLCV.
- Backtesting the OKX proxy while executing on Hyperliquid is a **venue mismatch** -- basis and
  after-hours structure differ.
- **Ablation, not tournament.** Pattern-world features enter as PRE-COMMITTED blocks chosen
  a-priori by the user (e.g. the Magnitude+Targets setup dictionary -- the TVB-20 layering arc)
  and must beat the control directly below them in the named ladder (C0 continuity-only ->
  C1 +BF exits -> C2 +M+T package; charter S3.1 amendments) to earn a place. A composite-
  package result adjudicates the package, never the pattern thesis alone. Ranking individual
  patterns or timeframes on sample performance and promoting the winner remains the forbidden
  move; labeled overfit censuses are ceiling-mapping, never promotion. (Reworded from "No
  pattern tournament" 2026-08-08; charter S3.1/S5 annotated same day + audit-F3 contrast
  ladder 2026-08-08.)
- **Timeframe sets are chosen a-priori and NOT tuned on the sample.** Picking "W/D/12h vs M/W/D"
  by performance is overfitting with fewer knobs.
- Research only -- no broker is attached to TradingView; `replay_trade` is simulation by
  implementation.
- Reporting: expand configs into words, lead with the finding, then mechanism, then numbers. No
  bare cell codes in user-facing text. `docs/ARM_LEDGER.md` is the standing translation (every
  arm in plain trading terms + numbers + cross-arm observations): update it with EVERY round,
  and in design sessions restate each proposed arm in its vocabulary, confirmed with the user,
  BEFORE the prereg is committed. Decision questions (AskUserQuestion) phrase every option in
  trader language too -- or dual (trader terms + code) (user requests 2026-08-16).

## Skills

- `strat-methodology` -- ANY bar classification, continuity logic, trigger/stop/target mechanics,
  or Pine detection code. STOP-and-ASK zone: design with the user before coding.
- `position-sizing-risk` -- any position-sizing or regime-layer size-scaling work.
- `/session-start` `/session-end` `/pre-commit` -- session and commit workflow.

The spine's Skill Methodology Ambiguity Policy applies in full: if a skill seems wrong or
conflicts with the charter or code, STOP and ASK rather than guess.

Ticket prefix `TVB-NNN`. Contracts: `docs/EXTERNAL_REVIEW_PROTOCOL.md`,
`docs/guides/TRADINGVIEW_MCP_SETUP.md`.
