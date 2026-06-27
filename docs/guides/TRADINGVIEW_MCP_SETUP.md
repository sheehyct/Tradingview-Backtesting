# TradingView MCP -- Setup for this workspace

The TradingView MCP is the **primary instrument** of this workspace (it drives the Strategy
Tester, injects/compiles Pine, reads results, captures screenshots). This page is the local
pointer + the deltas specific to `tradingview-backtesting`.

> **Master guide (read this first):**
> `C:\Strat_Trading_Bot\vectorbt-workspace\docs\guides\TRADINGVIEW_MCP_INSTALL.md`
> It has the full install procedure, the MSIX launch fix, the pine-editor overwrite trap, the
> permission posture, broker-safety history, and the upstream re-sync status. Everything there
> applies here -- the SAME server install is shared by both workspaces.

## What is already wired in this workspace

- `.mcp.json` registers the `tradingview` (stdio) + `openmemory` (http) servers. Unlike
  vbt-workspace, **`.mcp.json` is committed here** (no secrets in it), so the wiring travels
  with the repo.
- `.claude/settings.json` enables both servers, denies `mcp__tradingview__ui_evaluate`
  (Tier 1), and adds `C:\Strat_Trading_Bot\tradingview-mcp-jackson` as an allowed directory.
- The server itself lives at `C:\Strat_Trading_Bot\tradingview-mcp-jackson` (shared clone,
  installed once -- see the master guide to (re)install it).

## To use it (each session)

1. Launch TradingView Desktop with CDP (MSIX install -- `tv_launch` cannot find it):
   ```powershell
   $tv = Get-AppxPackage -Name "*TradingView*"
   Start-Process -FilePath (Join-Path $tv.InstallLocation "TradingView.exe") -ArgumentList "--remote-debugging-port=9222"
   ```
2. In Claude Code (launched with this workspace), verify: ask for `tv_health_check`
   (expect `cdp_connected: true`).

## Workspace-specific gotchas (on top of the master guide)

- **`strategy()` not `indicator()`.** This workspace backtests with TradingView strategy
  scripts. When injecting Pine, use the safe order (open pine-editor panel -> verify focused
  script -> `pine_check` -> `pine_set_source` -> compile) so you never overwrite an open
  script. See the master guide's pine-editor overwrite trap.
- **No broker attached.** There is no trading account on TradingView; `replay_trade` is
  replay-simulation only. If a broker is ever reconnected, re-read the master guide's
  broker-safety section first.
- **Reading the TFO/continuity indicator:** grey/neutral = the timeframes in the set are not
  all in agreement (a flip OR a non-resolving bar); solid red/green = full FTC down/up;
  grey-with-green-outline = inside bar closed up within prior range; grey-with-red-outline =
  inside bar closed down. (Charter Section 3.2.)
- **Trigger off the raw level cross, not the indicator's painted bar-shape.** Some indicators
  only plot the 2U label at bar close even though the break is intrabar-real. (Charter 3.4.)
