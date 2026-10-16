# Cloud session context (printed by the SessionStart hook only when CLAUDE_CODE_REMOTE=true)

You are in a Claude Code CLOUD session: a fresh Linux clone of this repo on
Anthropic's servers, not the owner's Windows workstation. On the workstation the
spine file C:\Strat_Trading_Bot\CLAUDE.md, the user-level hooks and Claude Code
auto-memory load automatically; here they do not. This file carries the parts of
the spine that apply here. It is a snapshot taken 2026-10-16: if it disagrees
with the spine, the spine wins and this file should be refreshed.

## This repository is PUBLIC on GitHub

Never commit secrets, API keys, account identifiers, wallet addresses or private
notes. scripts/secret_scan.py exists for checking.

## Session start in this repo

1. docs/ATLAS_Timeframe_Continuity_Charter.md, Section 0 first.
2. .session_startup_prompt.md: current mission and priorities.
3. docs/HANDOFF.md: newest entry at the TOP; read the last 1-2 entries.
4. CLAUDE.md: workspace rules (strict compliance).
5. Tests: `uv run pytest tests/ -q` (the Stop hook runs them too).

## Not available in a cloud session

- TradingView Desktop and the tradingview MCP server (it runs on the
  workstation over CDP). No strategy() backtest runs, no chart reads, no Pine
  compile checks here. Python analysis, tests, docs and reviews are fine.
  Backtests stay on the workstation.
- The tradingview-mcp-jackson folder and any Windows path (C:\...).
- .env files and local secrets. No exchange or broker keys exist here; do not
  place orders or run anything against live accounts from a cloud session.
- The openmemory MCP server works only if its host is on this environment's
  network allowlist; if it fails, fall back to docs/HANDOFF.md.

## Safety rules (ZERO TOLERANCE, from the spine)

Enforced by .claude/hooks/safety_guard.py (exit 2 = blocked). Do NOT work around them.

Universal:
- NEVER write to .env files (use .env.template for examples)
- NEVER `rm -rf` on project root directories, `/`, or `~`
- NEVER `git push --force` or `git push -f` to any remote
- NEVER `git branch -D main` or `git branch -D master`
- NEVER run destructive SQL (DROP TABLE/DATABASE, TRUNCATE, DELETE FROM without WHERE)
- NEVER `chmod 777` on anything
- NEVER `pip install` outside a virtual environment (use `uv pip install`)

Trading-specific:
- NEVER use `api.tradier.com` (production); use `sandbox.tradier.com`
- NEVER expose COINBASE_API_KEY values in commands
- NEVER write to .credentials.json files
- NEVER hardcode VPS IP addresses in source code or docs (`<VPS_IP>` in docs, `$VPS_IP` in code)

## Communication standards (from the spine)

- NO emojis or unicode characters; plain ASCII only
- NO AI attribution in commits or docs
- Conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`
- Timestamps timezone-aware (America/New_York for market data, UTC for system events)
- Prices: Decimal where possible, never float for currency

## Methodology ambiguity (from the spine)

If the strat-methodology skill (or any skill) is confusing, contradictory, or
conflicts with code, comments or tests: STOP and ask the owner before writing code.
