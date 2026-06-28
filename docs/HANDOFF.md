# HANDOFF -- tradingview-backtesting

> Newest session entry at the TOP. Keep under 1500 lines; archive older entries to
> `docs/session_archive/` when it grows past that.

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
