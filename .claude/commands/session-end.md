---
name: session-end
description: Automate tradingview-backtesting session closure with quality checks
---

# Session End Command

Execute in order. Pause for user confirmation where noted.

## Step 1: Pre-commit checks

Run `/pre-commit` (or perform its checks inline). Report any issues. If critical, STOP and ask.

## Step 2: Update documentation

### .session_startup_prompt.md

Replace contents with the next session's plan:
```markdown
# Session Startup Prompt -- TVB-{N+1}

**Previous Session:** TVB-{N} ({today's date})
**Current Branch:** `{branch}`
**Commit state:** {pushed/local}
**Plan Mode:** {ON/OFF recommendation}

---

## READ FIRST
{1-3 sentences on the current state and the single most important next move}

## NEXT (in order)
1. {priority 1}
2. {priority 2}
3. {priority 3}

## Open questions carried from the charter (Section 8)
{any still-open decisions touched this session}

## Reference
- docs/ATLAS_Timeframe_Continuity_Charter.md (Section 0 first)
- CLAUDE.md (STRICT COMPLIANCE)
```

### docs/HANDOFF.md

Add a new entry at the TOP:
```markdown
## Session TVB-{N}: {Brief Title} (COMPLETE)

**Date:** {today's date}
**Status:** COMPLETE -- {one-line summary}

### What was accomplished
{detailed list}

### Context for next session
{what to know}

### Files created/modified
{list}

---
```

If HANDOFF.md exceeds 1500 lines, STOP and ask before archiving to `docs/session_archive/`.

## Step 3: Store in OpenMemory

Call `mcp__openmemory__openmemory_store` with a structured summary (session number, date, key
accomplishments, decisions, blockers).
- `tags`: ["TVB-{N}", "tradingview-backtesting", "{relevant-topic}", ...]
- `metadata`: {"session": "TVB-{N}", "date": "{YYYY-MM-DD}", "project": "tradingview-backtesting"}

Confirm the return shows a memory id before continuing.

## Step 4: Prepare commit

Show the user a proposed conventional-commit message + `git diff --stat`, and WAIT for
confirmation before committing. Never commit without confirmation.

## Step 5: Output session summary

A short ACCOMPLISHED / BLOCKERS / NEXT PRIORITIES / PLAN MODE recommendation block.

## Rules

- Do NOT commit without user confirmation.
- Do NOT skip quality checks.
- Do NOT archive HANDOFF.md without confirmation.
- Keep summaries concise but complete.
