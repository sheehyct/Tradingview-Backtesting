# HANDOFF -- tradingview-backtesting

> Newest session entry at the TOP. Keep under 1500 lines; archive older entries to
> `docs/session_archive/` when it grows past that.

---

## Session TVB-2: TV MCP reader fix + clean controls + fee saga resolved (COMPLETE)

**Date:** 2026-06-30
**Status:** COMPLETE -- TV MCP Strategy Tester readers FIXED + deployed + verified live; controls A/B
re-characterized cleanly; fee model resolved to GROUND TRUTH (real xyz taker ~10x cheaper than
assumed), REVERSING the "B dead by fees" verdict; binding constraint re-identified as slippage.

### What was accomplished
- **TV MCP reader FIXED + deployed + verified (P1, the session's main effort).** The new TV Strategy
  Tester UI broke the `tradingview-mcp-jackson` readers. Root cause was NOT what TVB-1 assumed:
  (a) finder false-positive -- matched `s.performance`, a profiling method on EVERY study, so it
  grabbed the first indicator; and `metaInfo().isStrategy` does not exist in the new UI. (b) data
  shape -- `reportData()`/`ordersData()` are methods; metrics in `reportData().performance.{all,long,
  short}`; trades in `reportData().trades`. Fixed all three readers (getStrategyResults/getTrades/
  getEquity) to detect via `isTVScriptStrategy` and pull the new shapes. Verified live on
  OKX:MSTRUSDT.P. Committed to jackson `main` (commit `fb2a788`).
  - The TVB-1 "relaunch to load the diagnostic" premise was a red herring: the diagnostic ran but its
    output was dropped by the reader's node-side outer return (field-pick). The right instrument was
    a standalone CDP probe reusing jackson's `connection.js` evaluate() -- iterate freely vs live TV,
    restart the MCP only to DEPLOY.
- **Controls A/B re-characterized cleanly** (clean JSON, no screenshots). 2x2 (A/B x fee 0%/0.1%),
  same window (Feb 25 - Jun 30, ~-30% downtrend), 1x, bidirectional:
  - B (60/30/15, 15m): 2301 trades; @0% +85.8% PF 1.186; @0.1% -98.1% PF 0.400 (commission 10545 > capital).
  - A (M/W/D/60, 60m): 261 trades; @0% +48.2% PF 1.373 Sharpe 1.84; @0.1% -12.0% PF 0.906.
  - Replicates + extends TVB-1; A dominates B risk-adjusted at ~9x fewer trades.
  - NOTE: the on-chart strategy was found as a HYBRID (M/W/D/60 on a 15m chart) -- neither control;
    inputs decoded to pin config. A vanished template-added instance was long-only (the "all-long"
    389-trade run); the bidirectional instance is the real one.
- **Fee saga RESOLVED to ground truth (the session's biggest finding).** User supplied real HL fills.
  An initial fee/notional inference gave a wrong "97% maker" read; the user's "I trade market orders"
  testimony flagged it; re-classified by HL's authoritative `crossed` flag (validated: native-crypto
  taker = HL published 0.0432% exactly). Result: xyz is 86.5% TAKER, and the real xyz TAKER rate is
  CHEAP -- ~0.0086% modal / 0.0125% notional-weighted, ~8-12x BELOW the 0.1% the backtest used.
  - REVERSES the fee verdict: at real cost A ~= +38-42% (clear winner), B ~= +5-25% (near breakeven),
    NOT dead. "Turnover fatal for B" was largely a fee artifact (~10x too high). These are GEOMETRIC-
    MODEL estimates -- must be CONFIRMED by actual re-run.
  - BUT the binding constraint MOVED to SLIPPAGE: user fills market/taker both legs; B = 2301
    round-trips = 2301x slippage; B near-breakeven at zero slippage is exactly where realistic
    slippage decides the sign. Charter S6 flag: a real mechanism (cheap fees) must not launder an
    optimistic "deployable" verdict.

### Context for next session
- Reader WORKS -- clean JSON via data_get_strategy_results/data_get_trades/data_get_equity. TV must
  run on CDP (MSIX: `Get-AppxPackage *TradingView*` + Start-Process `--remote-debugging-port=9222`).
  Each Claude relaunch kills the Claude-launched TV -> relaunch it.
- The A/B-at-real-fee numbers are MODEL estimates, NOT fresh backtests -- re-run at 0.0086% and 0.0125%.
- SLIPPAGE is the new binding constraint (deferred so far) -- model before any deployability call.
- Strategy `35dVw8` (`Baseline TFC [TVB-1]` / slot "VIX Spike Alert" / id `USER;e7c8...`) left at
  M/W/D/60, 0.1% fee, 15m chart (as-found hybrid). Input ids: in_2=M, in_4=W, in_6=D, in_8=60,
  in_10=30, in_12=15 (bool enables); in_23 = commission percent.
- P2a (HTF-open currency) + P2b (period-open recon + tick-offset + TF guard) still pending; the
  `Timeframe Continuity [TFO]` indicator is now on the chart for the overlay.

### Files created/modified
- NEW `docs/TVB2_control_AB_rerun.md` (control 2x2 + fee model + ground-truth resolution; canonical).
- MOD `docs/HANDOFF.md`, `.session_startup_prompt.md`.
- SEPARATE repo (committed): `tradingview-mcp-jackson/src/core/data.js` reader fix (`fb2a788`, main).
- Memory: updated `tvb1-tv-mcp-reader-newui` (FIXED + new-API ref); new `feedback-relaunch-is-cheap`;
  new `tvb2-fee-resolved-real-taker`.
- User-side: `Downloads/TVB2_fee_handling.md` (Claude Desktop fee analysis -- superseded by the repo datasheet).

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range below) and write a
> verbatim assessment to docs/reviews/tvb2-codex-audit.md. See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: REQUESTED
- Commits to review: `bd2c760..HEAD` on `main` (workspace) + `fb2a788` in `tradingview-mcp-jackson` (reader fix)
- Scope / what changed: TV MCP reader fix (jackson); clean A/B control re-characterization; fee model
  resolved to ground truth (real taker ~10x cheaper -> verdict reversed; slippage now binding).
- Focus areas (scrutinize these): (1) fee ground-truth method (HL `crossed` flag + validation);
  (2) the geometric-model A/B-at-real-fee estimates -- should be confirmed by actual re-run, not trusted;
  (3) the "slippage is now binding, esp. for B" claim and the churn math; (4) whether the
  "breakout entry is intrinsically taker -> maker is not a free fee swap" reasoning holds;
  (5) reader-fix correctness in `jackson/src/core/data.js`.
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb2-codex-audit.md exists)

---

## Session TVB-1: Baseline continuity strategy + A/B fee characterization (COMPLETE)

**Date:** 2026-06-28
**Status:** COMPLETE -- baseline control built + characterized; naive baseline KILLED at real
HIP-3 fees; turnover identified as the dominant lever.

### What was accomplished
- Built `pine/baseline_continuity.pine`: ONE parameterized `strategy()` =
  `{2-trigger (raw level cross via breakout STOP orders -> intrabar fill) + FTFC gate
  (chart close vs each enabled TF period-open, lookahead_off) + close-based state-stop}`,
  both directions, `leverage` input. Compiles clean; lookahead audit PASS (single
  `request.security`, `lookahead_off`; gate uses only period-open = non-leaking).
- Designed WITH user (plan approved): two a-priori controls, single-layer, state-stop only,
  fixed-size, `OKX:MSTRUSDT.P`. FTFC gate reconciled to the TFO indicator's `close > period-open`
  (NOT the skill's bar-type TFC) -- flagged per ambiguity policy; charter governs.
- Results on `OKX:MSTRUSDT.P`, Feb 25 - Jun 28 2026, 1x:
  - **Control B** (60/30/15, 15m): 2263 trades, 27.04% win, **PF 0.645**, MaxDD 81.79%, ~ -81%.
  - Fee-isolation (B, zero fees): **PF 1.284**, 37.65% win, MaxDD 14.66% -> raw edge POSITIVE;
    fees/churn (2263 round-trips) are the killer, not the signal.
  - **Control A** (M/W/D/60, 60m): 258 trades (~9x fewer), 34.11% win, **PF 1.131 (net +)**,
    MaxDD 14.79% -- clears OKX fees.
  - **Control A @ HIP-3 fees** (commission 0.10%): **PF 0.921 (net LOSER)**, 30.62% win,
    MaxDD 22.37% -- does NOT clear real venue costs.
- **VERDICT:** continuity gate has a faint real edge; turnover reduction (B->A) was necessary
  but NOT sufficient at real HIP-3 fees. A deployable version needs per-trade edge clearing
  ~0.2% round-trip -> MORE selectivity (two-layer regime filter, compression filter, re-entry
  governor), not just a slower gate. The exploration did its job: killed the naive baseline and
  located the bar.
- Fixed the `tradingview-mcp-jackson` reader FINDER (overlay strategies now matched; was
  wrongly `is_price_study`-gated) in `src/core/data.js` (SEPARATE repo, uncommitted). The new
  TV Strategy Tester UI ALSO changed the data-access API (`ordersData`/`reportData` reshaped);
  a diagnostic is staged but needs a full Claude Code relaunch to load + finish.

### Incident (resolved)
- Overwrote the user's saved "VIX Spike Alert" TV script with the baseline (`pine_new` did not
  create a separate slot; `smart_compile` auto-saved over it). User has a backup; baseline source
  is safe in the repo. LESSON: `pine_get_source` to verify the slot BEFORE `pine_set_source`.

### Context for next session
- Reader: a full Claude Code relaunch loads the staged `data.js` diagnostic -> read its dump
  (new TV data API) -> apply data-access fix -> relaunch -> clean JSON reads. Until then,
  screenshots (close editor via its X ~1884,33; dismiss CLUSDT.P alert popups).
- Canonical strategy = `pine/baseline_continuity.pine` (leverage 2x default, Control B 60/30/15
  defaults). Set `leverage=1` for sizing-agnostic edge reads. Control A = enable M/W/D/60 + chart 60m.
- Leverage is NOT an edge lever (per-trade metrics invariant; compounded curve concave +
  liquidation cap). Characterize at 1x; size via vol-targeting on a ROBUST edge later.

### Codex external audit + Claude critical review (post-TVB-1)
Codex audited `baseline_continuity.pine` + the TFO indicator (full verbatim text in
`docs/reviews/tvb1-codex-audit.md` -- read it against this synthesis, don't trust either blindly).
My critical synthesis -- do NOT assume Codex right; the starred item cuts both ways:

- **No classic lookahead LEAK in the baseline** (HTF `open` + `lookahead_off`). The TFO indicator
  IS unsafe as a backtest source (HTF `high/low` under `lookahead_on`) but we never used it as one.
  => TVB-1 results are NOT leak-inflated fiction. CONFIRMED.
- ***MUST VERIFY -- HTF-open currency.** My code comment asserts `lookahead_off` returns the
  CURRENT period's open. That was OVERCONFIDENT and may be WRONG: `lookahead_off` reveals an HTF
  bar aligned to its CLOSE and applies to the whole `[o,h,l]` tuple, so for true HTFs (D/W/M on a
  60m chart) it may return the PRIOR period's open => a stale/lagged gate. This is a FIDELITY bug,
  NOT a leak (prior open is fully known; results stay honest). VERIFY empirically: overlay the
  strategy's FTFC bar-coloring vs the TFO indicator (lookahead_on = current period). Match => fine;
  differ => stale opens. Either way ADOPT the unambiguous local reconstruction:
  `f_period_open(tf) => ta.valuewhen(timeframe.change(tf), open, 0)` (no `request.security`).
- **Model fidelity (valid):** the baseline is a "prior-close TFC-gate + resting breakout stop",
  NOT "check TFC at the exact intrabar break". Both legitimate; ours is the conservative, safe one.
- **The 1m reframe (the gem -- resolves the parked 1m idea):** for "TFC-at-the-break", run on a
  LOWER chart TF (1m/2m/5m) for intrabar fidelity but reconstruct the EXECUTION-TF (15/30/60) prior
  highs/lows for the TRIGGER and check the gate intrabar -- do NOT trigger off 1m bars (the naive
  version's flaw). A distinct VARIANT to build/compare, not a fix.
- **Adopt (low-risk fidelity):** trigger tick-offset (`stop = high + syminfo.mintick` /
  `low - syminfo.mintick`) to force a strict break vs equal-high touch (matches strat-methodology
  `H[1]+tick`); enforce chart-TF <= enabled-TF via `runtime.error`.
- **Variant, NOT control (charter ablation discipline):** catastrophic price fail-safe stop and the
  re-entry governor are charter Section 8 open questions -- test as ablations, do NOT bake into the
  minimal control (fail-safe matters more once leverage > 1; state-stop is close-based).
- **`close == open`:** TFO treats equality as down; ours as neutral (intentional). Negligible on
  liquid perps; only matters for exact TFO replication.
- **Proposed next-session order:** VERIFY HTF-open currency -> adopt local period-open recon +
  tick-offset + TF guard -> RERUN A/B fee characterization (confirm findings hold) -> THEN
  two-layer / TFC-at-break variant / governor as ablations.

### Files created/modified
- NEW `pine/baseline_continuity.pine`; MOD `pine/README.md` (control presets), `docs/HANDOFF.md`,
  `.session_startup_prompt.md`.
- Reference (user-added at root): `Timeframe_Continuity_Claude_Discussion.md`,
  `Timeframe_Continuity_Pinescript.pine` (the source discussion + the TFO indicator).
- SEPARATE repo, uncommitted: `tradingview-mcp-jackson/src/core/data.js` (reader finder fix + diagnostic).
- Memory: `tvb1-controlB-fee-churn-finding.md`, `tvb1-tv-mcp-reader-newui.md`.

---

## Session TVB-0: Workspace Bootstrap (COMPLETE)

**Date:** 2026-06-27
**Status:** COMPLETE -- standalone workspace scaffolded, MCP wired, conventions mirrored.

### What was accomplished

- Created standalone git repo `C:\Strat_Trading_Bot\tradingview-backtesting` (branch `main`).
- Wrote `CLAUDE.md` adapted for this domain: Pine-first vehicle, crypto-perp data rules (NOT
  the ATLAS equity/RTH orthodoxy), and the charter's epistemic stance encoded as binding rules.
- Moved the governing design doc out of vbt-workspace `Temporary/` to
  `docs/ATLAS_Timeframe_Continuity_Charter.md`.
- Wired the `tradingview` + `openmemory` MCP servers in `.mcp.json` (TRACKED here on purpose --
  no secrets -- so the wiring travels with the repo, fixing the vbt-workspace gitignore gotcha).
- `.claude/settings.json`: `ui_evaluate` denied (Tier 1), MCP servers enabled, and only the
  domain-agnostic global hooks kept (trading safety guard, ruff lint, test gate). The
  VBT/STRAT-Python guardians from vbt-workspace were intentionally NOT ported (Pine-first repo).
- Light `uv` Python project (`pyproject.toml`) for the analysis layer; smoke test added.
- Ported + adapted slash commands: `/session-start`, `/session-end`, `/pre-commit`.
- Seeded `.session_startup_prompt.md` with the TVB-1 plan.

### Context for next session

- Nothing strategic is built yet -- only the scaffold. The first real task (TVB-1) is to design
  and write the **baseline strategy()** WITH the user (charter Sections 3-4). This touches STRAT
  detection logic, so it is a strat-methodology STOP-and-ASK zone -- design before coding.
- The TradingView MCP install/gotchas are documented in the master guide at
  `vectorbt-workspace/docs/guides/TRADINGVIEW_MCP_INSTALL.md`; this workspace's
  `docs/guides/TRADINGVIEW_MCP_SETUP.md` is the local pointer + delta.

### Files created

Scaffold only -- see `git log` for the bootstrap commit. No strategy or analysis logic yet.

---
