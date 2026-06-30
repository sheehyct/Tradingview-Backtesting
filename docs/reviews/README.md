# docs/reviews/

External review of TVB sessions. One file per session:

```
docs/reviews/tvb{N}-codex-audit.md
```

## Convention (matches tvb1-codex-audit.md)

- The file captures the **verbatim external audit** (Codex CLI locally, or a cloud
  agent against the pushed repo) under a skeptic preamble: *read CRITICALLY, do NOT
  assume it is correct.* External reviewers can be wrong, can conflate control vs
  variant, and can over- or under-state a risk.
- The **critical synthesis** -- where the next session agrees, disputes, and decides
  what to act on -- lives in `docs/HANDOFF.md` (e.g. a "Codex external audit +
  critical review" block), NOT in the review file. The review file is raw input;
  HANDOFF is the adjudication.

## Flow

1. `/session-end` records an `### External Review` block in the session's HANDOFF
   entry (status `REQUESTED`, commit range, focus areas) and gate-then-pushes.
2. A reviewer (local Codex CLI or cloud) reviews that range and writes
   `tvb{N}-codex-audit.md` (copy `_TEMPLATE.md`).
3. The next `/session-start` detects the new review, summarizes it, and folds
   actionable items into priorities -- writing the critical synthesis into HANDOFF.

See `docs/EXTERNAL_REVIEW_PROTOCOL.md` for the full contract. Review files are
tracked records: never paste a secret/IP/account value -- cite `file:line`.
