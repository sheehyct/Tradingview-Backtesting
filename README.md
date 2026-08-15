# tradingview-backtesting

Research workspace for **timeframe-continuity (TFO/TFC) gated strategies** on 24/7 crypto and
HIP-3 builder-deployed perpetuals (Hyperliquid, OKX proxy perps).

This is a sibling project under `C:\Strat_Trading_Bot\` and inherits the spine rules in
`C:\Strat_Trading_Bot\CLAUDE.md`. See `CLAUDE.md` here for workspace-specific rules.

## The premise

STRAT "2"-based patterns are lower-resolution re-descriptions of timeframe continuity, which a
TFO indicator measures directly and continuously. So instead of a pattern tournament, the
system is **continuity-first, patterns-minimal**: the signal is just (1) a level-break trigger
and (2) the TFO being FTC-aligned. The work is to **explore** which timeframe sets define
useful continuity across regimes -- to map the terrain and find where the logic breaks, not to
crown a winner.

Read `docs/ATLAS_Timeframe_Continuity_Charter.md` (Section 0 first) -- it governs how work is
done here.

## Architecture

- **Research engine: the Python replay twin** (`analysis/paper/engine.py` + tier runners) --
  pre-registered experiment arms run here first, gated by determinism / entry-stream /
  reconciliation checks against committed artifacts. Managed by `uv`.
- **Validation + live surface: TradingView `strategy()` scripts** (in `pine/`), run in the
  Strategy Tester, driven via the `tradingview` MCP server. The compound logic (trigger + TFO
  gate + stop + target) lives in one script firing one alert; each engine arm earns TV validity
  through an event-level parity gate, and the TV strategy is valid only for gated arms.
- **Analysis layer: Python** (rest of `analysis/`) -- regime tagging and the
  distribution/ablation analysis of results.

## Layout

```
pine/         TradingView strategy() scripts (the sim vehicle) + conventions
analysis/     Python: regime tagging, distribution + ablation analysis
results/       Strategy-Tester exports + sweep summaries (large data gitignored; JSON summaries tracked)
validation/    Cross-validation reports + screenshots
docs/          Charter, HANDOFF, INDEX, guides
tests/         pytest for the analysis layer
.claude/       Slash commands + settings (hooks, MCP enablement, ui_evaluate deny)
.mcp.json      MCP wiring (tradingview + openmemory) -- TRACKED on purpose (no secrets)
```

## Getting started

```bash
uv sync                       # create the analysis venv -- SEE WARNING BELOW
uv run pytest tests/ -q       # smoke test
```

**`uv sync` strips VectorBT Pro.** VBT Pro is installed in `.venv` but is deliberately NOT in
`pyproject.toml` (licensed, unpublishable), so `uv sync` removes it. If you run it, reinstall
from the cached wheel afterwards.

The TradingView MCP needs TradingView Desktop running with CDP on port 9222 -- see
`docs/guides/TRADINGVIEW_MCP_SETUP.md`.
