---
name: session-start
description: Automate tradingview-backtesting session startup sequence
---

# Session Start Command

Execute the following steps in order.

## Step 1: Read session context

Read and summarize key points from:

1. `docs/ATLAS_Timeframe_Continuity_Charter.md` -- **Section 0 first** (it governs how work is
   done here). Skim the rest if not already in context.
2. `.session_startup_prompt.md` -- current mission + priorities
3. `docs/HANDOFF.md` -- recent session history (last 1-2 entries)
4. `CLAUDE.md` -- workspace rules (STRICT COMPLIANCE; confirm read, do not summarize)

## Step 1.5: Check for prior-session external review

Before forming today's priorities, check whether the previous session was reviewed
(local Codex CLI or cloud):

1. Read the previous session's `### External Review` block in `docs/HANDOFF.md`
   (its `Review status` + `Commits to review`).
2. Check `docs/reviews/` for a matching `tvb{prev}-codex-audit.md`.
3. If a review file exists (status RETURNED): read it CRITICALLY (it may be wrong),
   summarize its verdict + findings, fold actionable items into TODAY'S PRIORITIES
   (CRITICAL/HIGH first), and plan to write the critical synthesis into HANDOFF.
4. If status is REQUESTED but no review file yet: note "External review pending" and
   ask whether to (a) wait, (b) proceed, or (c) run Codex CLI on the named range now.

See `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Step 2: Query OpenMemory

Call `mcp__openmemory__openmemory_query` with:
- `query`: "{previous session ticket, e.g. TVB-0} {2-3 domain keywords: timeframe continuity, TFO, perps}"
- `k`: 5

Do NOT use a generic query -- old high-salience sessions outrank recent ones. Anchor on the
latest `TVB-*` ticket + domain terms. Extract the most recent 1-2 summaries, any blockers, and
any decisions that constrain today's work.

## Step 3: Output session brief

```
SESSION STARTUP COMPLETE
========================

Session: TVB-{N} (from .session_startup_prompt.md)
Branch: {current git branch}

TODAY'S PRIORITIES:
1. {from .session_startup_prompt.md}
2. {from .session_startup_prompt.md}
3. {from .session_startup_prompt.md}

RECENT CONTEXT:
- {key point from HANDOFF.md}
- {key point from OpenMemory}

EXTERNAL REVIEW (prior session):
- {RETURNED: verdict + top finding(s), folded into priorities | PENDING: awaiting review of {range} | N/A}

REMINDERS:
- Charter Section 0 governs: explore to KILL the strategy, not confirm; the spread is the finding.
- strat-methodology skill MANDATORY before any bar/continuity/Pine detection logic (STOP-and-ASK).
- Audit every request.security for lookahead_off.
- TradingView strategy() is the backtest vehicle; TV MCP needs TradingView Desktop on CDP 9222.

Awaiting user direction...
```

## Step 4: Wait for user direction

Do NOT start any development work until the user provides direction.

## Rules

- Do NOT skip any steps.
- Do NOT summarize CLAUDE.md -- just confirm it was read.
- Do NOT start work without user direction.
- The baseline strategy and any detection logic are STOP-and-ASK zones -- design before coding.
