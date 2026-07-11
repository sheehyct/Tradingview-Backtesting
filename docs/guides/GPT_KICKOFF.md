# GPT kickoff message (paste this verbatim into the GPT session)

---

You are working on the home PC in `C:\Strat_Trading_Bot\tradingview-backtesting`
(a git repo; use it as your working directory). Read these IN ORDER before doing
anything else:

1. `C:\Strat_Trading_Bot\tradingview-backtesting\docs\guides\GPT_TVMCP_GUIDE.md`
   -- TradingView MCP setup, usage, and safety rules. Follow section 7 EXACTLY.
2. `C:\Strat_Trading_Bot\tradingview-backtesting\docs\guides\GPT_BF_EXIT_EXPERIMENT_PROMPT.md`
   -- the experiment you will run, including the pre-registered cell matrix.
3. `C:\Strat_Trading_Bot\CLAUDE.md` and
   `C:\Strat_Trading_Bot\tradingview-backtesting\CLAUDE.md` -- workspace rules
   (binding: ASCII only, no emojis, conventional commits, no AI attribution).

Reference sources the experiment prompt cites:
- `C:\Users\Chris\Downloads\bf.txt` -- the Broadening Formation indicator source
  you will port.
- `C:\Strat_Trading_Bot\tradingview-backtesting\pine\tfc_companion.pine` -- the
  entry/exit state-machine semantics to replicate.
- `C:\Strat_Trading_Bot\tradingview-backtesting\docs\ATLAS_Timeframe_Continuity_Charter.md`
  -- read Section 0 and Section 7.

Environment state right now:
- TradingView Desktop is ALREADY RUNNING with the debug port open (CDP 9222).
  Do NOT restart or relaunch it. The chart is on HIP3XYZ:AMZNUSDC.P at 5m.
- The MCP server lives at
  `C:\Strat_Trading_Bot\tradingview-mcp-jackson\src\server.js` (stdio transport,
  command `node`, no env vars). Register it per the guide if your session does
  not already have the tradingview tools.
- Claude Code ran the same experiment first. Its script "TVB-EXP BF Exit
  [Claude]" is saved and on the chart -- do NOT open, modify, or read it, and do
  NOT read `docs/experiments/tvb_exp_bf_exit_2026-07-10.md` until your own
  numbers are produced (this is a blind replication). Never touch any other
  user script (especially "TFC Baseline", the Companion scripts, and
  "Broadening Formation MTF [BF-1]").
- Create your own script named "TVB-EXP BF Exit [GPT]" using the Make-a-copy
  procedure in the guide, section 7. NEVER use pine_new. NEVER use ui_evaluate.
- Write your results to a NEW file:
  `C:\Strat_Trading_Bot\tradingview-backtesting\docs\experiments\tvb_exp_bf_exit_gpt.md`.
  Do not edit docs/HANDOFF.md or any session files.

I am supervising from a mobile device. Ask before anything destructive or
ambiguous; otherwise proceed autonomously and report the full results table plus
findings when done.
