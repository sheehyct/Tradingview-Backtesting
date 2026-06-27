---
name: pre-commit
description: Run quality checks before committing code
---

# Pre-Commit Quality Checks

Execute all checks and report results. Do NOT auto-fix -- report for user decision.

## Check 1: Changed files

```bash
git -C "C:/Strat_Trading_Bot/tradingview-backtesting" status --short
git -C "C:/Strat_Trading_Bot/tradingview-backtesting" diff --stat
```
Status: {X files changed}

## Check 2: request.security lookahead audit (DOMAIN-CRITICAL)

For every changed `*.pine` file, grep for `request.security`. Each call MUST use
`lookahead_off` (and confirm-on-close offsets). A lookahead-on call makes the whole backtest
fiction -- this is the cardinal trap (charter Section 7.1).

```bash
grep -rn "request.security" "C:/Strat_Trading_Bot/tradingview-backtesting/pine" || echo "no pine request.security calls"
```
Status: PASS / NEEDS ATTENTION (list any call missing lookahead_off)

## Check 3: Pine trigger-timing sanity

For changed strategy scripts, confirm the entry triggers off the raw level cross
(`high > high[1]` / `low < low[1]`), evaluated once-per-bar -- NOT off a painted bar-shape
series at bar close (charter Section 3.4). Flag any script that gates entry on bar close.

Status: PASS / NEEDS ATTENTION

## Check 4: Python lint (analysis layer)

```bash
uv run ruff check analysis/ tests/
```
Status: PASS / ISSUES

## Check 5: HANDOFF.md size

```bash
wc -l "C:/Strat_Trading_Bot/tradingview-backtesting/docs/HANDOFF.md"
```
< 1500 = PASS; >= 1500 = NEEDS ARCHIVE.

## Check 6: README / CLAUDE.md accuracy

Do README.md and CLAUDE.md still reflect the actual workspace state? Flag drift.

## Summary

```
PRE-COMMIT CHECK RESULTS
========================
[PASS/FAIL] Changed files: X
[PASS/WARN] request.security lookahead: {status}
[PASS/WARN] Pine trigger timing: {status}
[PASS/WARN] Python lint: {status}
[PASS/WARN] HANDOFF.md: {X lines}
[PASS/WARN] README/CLAUDE.md: {status}

OVERALL: READY TO COMMIT / ISSUES TO ADDRESS
```

## Rules

- Report ALL issues, even minor ones. Do NOT auto-fix. User decides whether to commit.
- The request.security lookahead check is non-negotiable for any `.pine` change.
