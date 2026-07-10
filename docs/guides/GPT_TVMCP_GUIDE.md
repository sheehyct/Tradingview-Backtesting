# TradingView MCP -- Onboarding Guide for GPT / Codex

**Audience:** A GPT (Codex CLI or any MCP-capable agent harness) that needs to install,
connect to, and safely operate the TradingView MCP server on this workstation.

**Written:** 2026-07-10, for the BF-exit backtest experiment (see the companion prompt
`GPT_BF_EXIT_EXPERIMENT_PROMPT.md`). Everything here is machine-specific to
`C:\Strat_Trading_Bot\` on this Windows 11 box.

---

## 1. What this server is (read this or nothing else makes sense)

The TradingView MCP is NOT a web-API client. It is a local Node.js bridge that attaches
to the running **TradingView Desktop** app over the Chrome DevTools Protocol (CDP, port
9222) and drives the chart, Pine editor, Strategy Tester, replay engine, and alerts via
TradingView's own internal JavaScript APIs.

```
Agent  --stdio-->  node src/server.js  --CDP (localhost:9222)-->  TradingView Desktop
```

Consequences:
- TradingView Desktop must be RUNNING, LOGGED IN, and launched with
  `--remote-debugging-port=9222` before any tool works.
- There is exactly ONE chart window. Two agents driving it simultaneously will fight
  over the same UI. **One driver at a time** -- the user sequences the sessions.
- No API keys, no .env, no build step. Plain Node ESM.
- The server executes JS inside TradingView's page context. Internals can shift with
  TradingView updates; a tool erroring is often fragility, not your mistake.

## 2. Already installed on this machine

| Layer | Value |
|---|---|
| Server repo | `C:\Strat_Trading_Bot\tradingview-mcp-jackson` (fork: LewisWJackson/tradingview-mcp-jackson) |
| Entry point | `node C:\Strat_Trading_Bot\tradingview-mcp-jackson\src\server.js` |
| Dependencies | Already `npm install`-ed. Do NOT run `npm audit fix` (locked decision; the 2 reported Hono CVEs are unreachable over stdio). |
| Transport | stdio |
| TradingView install | MSIX (Windows Store style) -- automatic launchers CANNOT find it |

You do NOT need to clone or npm-install anything. You only need to (a) register the
server with your harness, (b) ensure TradingView Desktop is up with CDP.

## 3. Register the server with your harness

### Codex CLI

Add to `~/.codex/config.toml` (create the file if missing):

```toml
[mcp_servers.tradingview]
command = "node"
args = ["C:\\Strat_Trading_Bot\\tradingview-mcp-jackson\\src\\server.js"]
```

Newer Codex CLI builds also accept:

```
codex mcp add tradingview -- node "C:\Strat_Trading_Bot\tradingview-mcp-jackson\src\server.js"
```

Restart the Codex CLI session after editing config -- MCP servers spawn at startup.

### Any other MCP client

Register a stdio server: command `node`, single arg = the `src\server.js` path above.
Empty env. No cwd requirement.

## 4. Launch TradingView Desktop with CDP

TradingView here is an MSIX install; the server's `tv_launch` tool and the bundled
launch scripts CANNOT find it ("not found" is expected, not a bug). Launch manually
with PowerShell:

```powershell
$tv = Get-AppxPackage -Name "*TradingView*"
Start-Process -FilePath (Join-Path $tv.InstallLocation "TradingView.exe") -ArgumentList "--remote-debugging-port=9222"
```

GOTCHA: if TradingView is ALREADY running without the flag, the new process just joins
the existing instance and the port never opens. Check and restart:

```powershell
netstat -ano | Select-String ":9222"    # empty = port not open
Stop-Process -Name "TradingView" -Force  # then relaunch with the flag
```

Verify: `curl http://localhost:9222/json/version` returns JSON.
Note: restarting TradingView drops studies/layout state back to the last cloud save.
That is accepted here; the user's layout is cloud-saved.

## 5. Verify the bridge

Call `tv_health_check`. Expect `cdp_connected: true` plus current symbol/timeframe.

| Symptom | Fix |
|---|---|
| tools not found | server not registered / harness not restarted (step 3) |
| `cdp_connected: false` | TradingView not on port 9222 (step 4) |
| tools return empty | not logged in to TradingView, or no chart loaded |

## 6. Core tool vocabulary (81 tools; these are the ones you need)

Reading:
- `chart_get_state` -- symbol, timeframe, all loaded studies + entity IDs. Call first.
- `data_get_indicator(entity_id)` -- a study's input values (settings).
- `data_get_strategy_results` -- Strategy Tester performance metrics.
- `data_get_trades(max_trades)` -- Strategy Tester trade list.
- `capture_screenshot(region)` -- regions: `full`, `chart`, `strategy_tester`.
- `data_get_ohlcv(summary=true)` -- price bars (cap 500, ignores viewport).

Chart control:
- `chart_set_symbol`, `chart_set_timeframe` (e.g. `5`, `60`, `D`).
- `indicator_set_inputs(entity_id, inputs)` -- change study inputs WITHOUT recompiling.
  Input keys are positional IDs `in_0`, `in_1`, ... in source declaration order.
  This also works on strategy() scripts added to the chart -- it is the cheap way to
  sweep experiment cells (change inputs, wait a beat, re-read results).

Pine (DANGER ZONE -- see section 7):
- `ui_open_panel(pine-editor, open)` -- must be open before pine work.
- `pine_new` -- DO NOT USE. See section 7 for why and for the working alternative.
- `pine_list_scripts`, `pine_open(name)`, `pine_get_source` (can be 200KB -- avoid),
  `pine_set_source(source)`, `pine_save`, `pine_smart_compile` (compiles + SAVES +
  reports errors), `pine_get_errors`.

Strategy Tester:
- `ui_open_panel(strategy-tester, open)` then `data_get_strategy_results` /
  `data_get_trades`. Metrics live under `reportData().performance.{all,long,short}`
  internally; the tools decode this for you.

## 7. The Pine editor overwrite trap (the one dangerous mistake)

ROOT CAUSE, verified by reading the server source AND by a live incident on 2026-07-10
(Claude overwrote the user's BF-1 script and restored it): the server has NO concept of
editor tabs or script bindings. `pine_new` and `pine_open` both just call
`monaco.editor.setValue(...)` on the CURRENT editor tab. The tab's CLOUD BINDING (which
saved script a save writes to) NEVER changes. Consequences:

- `pine_new` shows you a blank template but the tab is still bound to whatever script
  the user last had open. Saving writes YOUR code into THEIR script.
- Verifying "focus" by reading the source is USELESS -- you will see the template and
  still be bound to the wrong script. The only real check: after saving, a NEW script
  id must appear in `pine_list_scripts` (count goes up). If the count did not go up,
  you just overwrote an existing script.

WORKING procedure to create your own script (validated 2026-07-10):
1. `ui_open_panel(pine-editor, open)`.
2. Open the editor's script-title dropdown: `ui_click(by=text, value=<current script
   title shown in the editor header>)`.
3. `ui_click(by=text, value="Make a copy…")` (note the unicode ellipsis U+2026). A
   name dialog opens with the name field focused.
4. `ui_keyboard(Ctrl+A)`, `ui_type_text("TVB-EXP BF Exit [GPT]")`, `ui_keyboard(Enter)`.
5. `pine_list_scripts` -- confirm a NEW id exists with your name and the count went UP.
   The editor tab is now bound to the copy (header shows your name).
6. `pine_set_source(<your full source>)`, then `pine_save`.
7. `pine_list_scripts` again -- YOUR script's title/modified changed; every OTHER
   script's `modified` stamp is UNCHANGED. If any user script's stamp moved, stop and
   confess.
8. To put it on the chart: `ui_click(by=text, value="Add to chartAdd to chart")` (the
   header button's text content is doubled -- match it exactly), then `chart_get_state`
   to confirm a new study appeared.

Recovery if an overwrite happens: you or the user can restore via the script title
dropdown -> "Version history...". If you have the original source on disk, the faster
path is `pine_set_source(<original>)` + `pine_save` on the same tab. Confess
immediately either way; TradingView versions every save, so nothing is truly lost.

`chart_manage_indicator` adds BUILT-IN indicators only -- it cannot add user Pine
scripts. To put your compiled script on the chart, `pine_smart_compile` /
`pine_compile` handles add-to-chart.

## 8. Hard safety rules (this workspace, zero tolerance)

1. NEVER call `ui_evaluate` (arbitrary JS injection). It is deny-listed for Claude and
   the same posture applies to you. Every legitimate workflow has a tool-shaped path.
2. NEVER open/save/modify these user scripts: `TFC Baseline` (title "TFC
   Baseline+Regime [TVB-4]", pineVersion 20 -- the anchored STRATEGY slot),
   `TFC Companion [TVB-10/11]`, `Broadening Formation MTF [BF-1]`, or any other
   existing user script. CREATE YOUR OWN script and work only in it.
   Suggested name: `TVB-EXP BF Exit [GPT]`.
3. No live trading surface exists: no broker is attached to TradingView, and
   `replay_trade` is replay-simulation only. Keep it that way; if you ever see a
   broker/trading panel connected, STOP and tell the user.
4. Do not create/delete the user's alerts or drawings unless asked.
5. ASCII only in anything you write to this repo (no emojis/unicode); no AI
   attribution in commits.
6. This is a RESEARCH workspace. Backtests here characterize behavior; they never
   justify deployment on their own.

## 9. Known operational gotchas

- TradingView loads a finite history window per timeframe; the Strategy Tester
  computes over loaded bars only. RECORD the backtest window (first/last trade
  timestamps, total bars) with every result you report -- comparisons across agents
  are meaningless without it.
- `data_get_ohlcv` returns the last N bars regardless of viewport; cap 500.
- Pine `plotshape`/`plotchar` outputs are not programmatically readable -- evidence of
  on-chart signals = screenshots.
- Tool responses can lag the live tick by ~1s; re-fetch if precision matters.
- The server logs startup notices to stderr -- not errors.
- After `indicator_set_inputs` on a strategy, give TradingView a moment to recompute
  before reading `data_get_strategy_results` (poll until numbers change or stabilize).
- Strategies with `use_bar_magnifier=true` require a Premium-tier plan; if compile or
  results look wrong, drop that property and note it in the report.

## 10. Etiquette for the parallel-agent experiment

Claude Code runs first, then you. Do not assume the chart is where Claude left it --
call `chart_get_state` and re-stage symbol/timeframe yourself. Do not modify or delete
Claude's experiment script (`TVB-EXP BF Exit [Claude]`); build your own. Write nothing
to `docs/HANDOFF.md` or the session files; report results in your chat and, if asked,
to a NEW file under `docs/experiments/`.
