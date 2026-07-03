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
**Prior-session review:** {REQUESTED -- next session checks docs/reviews/tvb{N}-codex-audit.md}

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

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb{N}-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: REQUESTED | RETURNED | ADDRESSED | ACCEPTED | N/A
- Commits to review: `{base}..{head}` on `main`  (or "local working tree @ {sha}")
- Scope / what changed: {one or two lines}
- Focus areas (scrutinize these): {e.g. request.security lookahead, model fidelity, fee/turnover math}
- Reviewed by: {local Codex CLI | cloud Codex app | Claude Code web | pending}
- Findings: {blank until docs/reviews/tvb{N}-codex-audit.md exists}

---
```

If HANDOFF.md exceeds 1500 lines, STOP and ask before archiving to `docs/session_archive/`.

### docs/reviews/REVIEW_REQUEST.md

Rewrite it for THIS session's review request. It is the stable entry point external
reviewers (Codex `/review`, cloud agents) are pointed at -- it always describes the
LATEST request; the permanent per-session record stays in the HANDOFF block above.
Both are written in this step, from the same fields, so they cannot drift.

- Status: REQUESTED; session TVB-{N} + title + request date.
- Audit output path: `docs/reviews/tvb{N}-codex-audit.md`.
- Commits to review: leave as `{pending push}` here; PIN concrete shas after the
  commit/push in Step 5. Include sibling-repo commits (with local paths) marked
  "local transport only".
- Scope + focus areas: same content as the HANDOFF block.
- Keep the read-first list and output contract sections (they are boilerplate;
  update only if the protocol changed).

## Step 3: Store in OpenMemory

Call `mcp__openmemory__openmemory_store` with a structured summary (session number, date, key
accomplishments, decisions, blockers).
- `tags`: ["TVB-{N}", "tradingview-backtesting", "{relevant-topic}", ...]
- `metadata`: {"session": "TVB-{N}", "date": "{YYYY-MM-DD}", "project": "tradingview-backtesting"}

Confirm the return shows a memory id before continuing.

## Step 4: Commit

Commit with a conventional-commit message (include the message + `git diff --stat` in the
Step 6 summary). Commits and pushes are AUTONOMOUS -- no per-commit user confirmation
(rule retired 2026-07-03; it predated auto mode). The blocking check is the secret-scan
gate in Step 5, not the user.

## Step 5: Secret-Scan Gate and Push

The remote is PUBLIC and feeds cloud review, so "pushed and current" is the default
end state. After the commit is made, gate then push:

1. Run the secret-scan gate:
   ```bash
   uv run python scripts/secret_scan.py --range origin/main   # normal
   uv run python scripts/secret_scan.py                        # first push (no origin/main yet) / full audit
   ```
2. If it exits 0 (clean): `git push origin main` (first push: `git push -u origin main`).
   Then fill the `Commits to review:` field in the HANDOFF `### External Review` block
   AND pin the same concrete shas in `docs/reviews/REVIEW_REQUEST.md` (this may need a
   small follow-up commit; that is expected and fine -- the request file must name real
   shas so a reviewer can check out the exact range).
3. If it exits non-zero (CRITICAL/HIGH finding): **DO NOT PUSH.** Remove the secret /
   gitignore the file / add a reviewed entry to `scripts/secret_scan_allowlist.txt`,
   then re-run. Never bypass with `--no-verify`.

Reviews can also be produced locally (Codex CLI) -- either way they land in
`docs/reviews/tvb{N}-codex-audit.md`. See `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Step 6: Output session summary

A short ACCOMPLISHED / BLOCKERS / NEXT PRIORITIES / PLAN MODE recommendation block.

## Rules

- Commits/pushes are autonomous (no confirmation needed); the secret-scan gate is the
  blocker, never bypass it.
- Do NOT skip quality checks.
- Do NOT archive HANDOFF.md without confirmation.
- ALWAYS push after a clean secret-scan gate -- cloud review reads the remote, not your local tree.
- NEVER bypass scripts/secret_scan.py (no `--no-verify`); fix the finding instead. Repo is PUBLIC.
- Keep summaries concise but complete.
