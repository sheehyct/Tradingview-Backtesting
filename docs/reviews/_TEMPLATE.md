<!--
Copy to docs/reviews/tvb{N}-codex-audit.md and fill in.
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-{N} External Audit -- {Codex CLI | cloud Codex | Claude Code web} (verbatim source, read CRITICALLY)

> External review of {what was reviewed: files / commit range} captured {YYYY-MM-DD}
> ({TVB-N} post-session). Lightly ASCII-normalized (em-dashes -> --, curly quotes -> straight);
> wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-{N} -- {brief title}
- **Reviewed:** {commit range `base..head` on main, or "local working tree @ sha"}
- **Reviewer:** {model id / tool}
- **Overall verdict:** APPROVE | APPROVE-WITH-NITS | NEEDS-CHANGES | BLOCK

## 2. Verbatim audit

{Paste the external agent's output here, unedited except ASCII normalization.
If the agent wrote structured findings, keep them; if prose, keep the prose.}

## 3. Actionable items (reviewer's own list, if provided)

1. {finding} -- [CRITICAL|HIGH|MEDIUM|LOW] -- {file:line} -- {suggested fix}
2. ...

## Suggested prompt (optional)

{If a better review prompt exists than the one implied by the HANDOFF focus areas, propose it.}
