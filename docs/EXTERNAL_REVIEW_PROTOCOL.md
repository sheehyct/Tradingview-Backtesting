# External Review Protocol -- tradingview-backtesting

How an external review agent reviews each TVB session's work. This workspace's
product is **characterization and bug-finding** (CLAUDE.md Section 1), and the
cardinal trap is `request.security` lookahead (Section 6) -- so external review
here is not a formality, it is a primary defense. The TVB-1 Codex audit already
caught the TFO indicator's `lookahead_on` `high/low` requests; that is the bar.

This document is the single source of truth. `/session-start` and `/session-end`
reference it.

---

## Two transports (both active)

1. **Local Codex CLI (primary).** Run Codex CLI against the local tree/commits;
   capture its output verbatim into `docs/reviews/` (see convention below). This
   is the existing, proven loop (`docs/reviews/tvb1-codex-audit.md`).
2. **Cloud review via the remote.** `/session-end` gate-then-pushes to
   `origin` (`https://github.com/sheehyct/Tradingview-Backtesting.git`, PUBLIC),
   so a cloud agent (Codex app, Claude Code web) can review the pushed repo.

Either transport writes its findings to the same place; `/session-start` reads
them the same way.

## The current-request pointer: `docs/reviews/REVIEW_REQUEST.md`

A stable single file external reviewers are pointed at (e.g. the Codex
`/session-review` custom prompt -- `~/.codex/prompts/session-review.md` -- reads
exactly this path; do NOT name the prompt `review.md`, Codex CLI has a NATIVE
built-in `/review` that shadows same-named custom prompts and only diffs the
working tree against a base branch). It always describes the LATEST requested
review: status, session, pinned commit ranges (including sibling-repo commits
reviewable only via the local transport), scope, focus areas, read-first order,
and the audit output path.

- `/session-end` rewrites it each session (same fields as the HANDOFF block, one
  writer, so they cannot drift). Concrete shas are pinned right after the push.
- `/session-start` reads it, and flips its status to RETURNED once the audit
  file exists.
- The HANDOFF `### External Review` block remains the permanent per-session
  record and the adjudication anchor; REVIEW_REQUEST.md is ephemeral and wins
  only for the CURRENT request.

## Why pushed + tracked context matters

A cloud reviewer reads the REMOTE, not your local tree. The repo is PUBLIC, so
every push is world-visible -- the `scripts/secret_scan.py` gate (below) runs
before every push to keep "commit the context" from leaking a secret.

## For Codex / other external review agents -- READ THIS

> If you are an external review agent pointed at this repository:
>
> 1. **Start at `docs/reviews/REVIEW_REQUEST.md`** -- it names the session, the
>    pinned commit ranges, the focus areas, and where your audit goes.
> 2. **Read the governing context:** `CLAUDE.md` (epistemic stance + backtest
>    traps), `docs/ATLAS_Timeframe_Continuity_Charter.md` (Section 0), and the top
>    `docs/HANDOFF.md` entry for the session under review (its `### External Review`
>    block is the permanent record of the same request).
> 3. **Review that work**, prioritizing: `request.security` lookahead in any Pine
>    (`lookahead_off`? offset? which fields requested?), model-fidelity honesty
>    (is the backtest measuring what it claims?), overfitting / sample-vs-structural
>    reasoning, and fee/turnover characterization correctness.
> 4. **Write your assessment** to `docs/reviews/tvb{N}-codex-audit.md` (see the
>    convention + `_TEMPLATE.md`). Be concrete; cite `file:line` and Pine docs.
>    A future session will write the critical synthesis in HANDOFF -- so your job
>    is the honest external read, not the final word.
> 5. If you think a better review prompt exists, propose it in a `Suggested prompt`
>    section.

## Review file convention

- One file per session: `docs/reviews/tvb{N}-codex-audit.md`.
- It captures the **verbatim external audit** under a skeptic preamble
  ("read CRITICALLY, do NOT assume correct") -- see `tvb1-codex-audit.md`.
- The **critical synthesis** (where Claude/the next session agrees, disputes, and
  acts) lives in `docs/HANDOFF.md`, not in the review file. The review file is the
  raw external input; HANDOFF is the adjudication.
- These files are tracked review records -- never paste a secret/IP/account value
  into one; cite `file:line` instead.

## The HANDOFF `### External Review` block

Every session entry in `docs/HANDOFF.md` carries:

```markdown
### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb{N}-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: REQUESTED | RETURNED | ADDRESSED | ACCEPTED | N/A
- Commits to review: `{base}..{head}` on `main`  (or "local working tree @ {sha}")
- Scope / what changed: {one or two lines}
- Focus areas (scrutinize these): {e.g. request.security lookahead, model fidelity, fee math}
- Reviewed by: {local Codex CLI | cloud Codex app | Claude Code web | pending}
- Findings: {blank until docs/reviews/tvb{N}-codex-audit.md exists}
```

## Status lifecycle

```
REQUESTED -> RETURNED (review file written) -> ADDRESSED (acted on) / ACCEPTED (no action) ; N/A for trivial sessions.
```

## Secret-scan gate

`scripts/secret_scan.py` blocks a push if it finds a secret in the content being
pushed. Public repo -> this gate is load-bearing.

```bash
# Normal push gate (scan only the outgoing diff):
uv run python scripts/secret_scan.py --range origin/main

# FIRST push (no origin/main yet) or a full audit -- scan the whole tracked tree:
uv run python scripts/secret_scan.py

# Staged-only:
uv run python scripts/secret_scan.py --staged
```

Exit 0 = clean (push allowed). Non-zero = a CRITICAL/HIGH finding: remove the
secret, gitignore the file, or add a reviewed entry to
`scripts/secret_scan_allowlist.txt`. Never bypass with `--no-verify`. The scanner
inspects only git-tracked content, so anything gitignored (real `.env`, `temporary/`)
is never scanned or pushed.
