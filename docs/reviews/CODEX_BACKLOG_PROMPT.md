# Codex paste prompt -- the review backlog (written 2026-10-10 at TVB-37 close)

Paste the block below into Codex CLI started in
`C:\Strat_Trading_Bot\tradingview-backtesting` (workspace-write, so it can save
the audit files). It covers every session review that was requested and never
returned, plus the TVB-37 close-out. One audit file per session. Claude folds
the findings at the start of TVB-38, before any plan-mode work.

Who runs audits: nobody automatically. In this repo an audit happens either
when Claude launches the local Codex CLI from inside a session (as it did twice
in TVB-37) or when the owner runs Codex with this prompt or the
`session-review` skill. See `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

---

```text
You are the external reviewer for the git repository at the current working directory
(tradingview-backtesting, branch main; confirm with `git rev-parse --show-toplevel`). This is
a public research repo. Read docs/EXTERNAL_REVIEW_PROTOCOL.md and CLAUDE.md first, then
docs/ATLAS_Timeframe_Continuity_Charter.md Section 0. Review CRITICALLY: the product of this
workspace is characterization and bug-finding, and the traps are look-ahead, model-fidelity
claims, overfitting language, and receipts whose sentences outrun their tables.

Six session reviews are open. For EACH one, read its "### External Review" block in the
HANDOFF (docs/HANDOFF.md for TVB-33..37; docs/session_archive/HANDOFF_TVB27-TVB32.md for
TVB-31 and TVB-32), review exactly the pinned range with that block's focus areas, and
write ONE audit file. Verify every range with `git diff --name-status <range>` before
reading. Sibling-repo ranges (hip3-executor, PRIVATE, local path
C:\Strat_Trading_Bot\hip3-executor; hip3-scanner, C:\Strat_Trading_Bot\hip3-scanner) are
reviewable only locally: review them if the path exists, otherwise say so in the file.

  1. TVB-31 -> docs/reviews/tvb31-codex-audit.md
     this repo 0d7437c^..7bfde0f; hip3-executor 4e384bb^..4e384bb; hip3-scanner d0fe9e7
     (merged unchanged at 7723462). Focus: the ten items in the TVB-31 block (executor
     safety boundary: proved closes, sweep-scope guard, keyed entry blocks, stop contract).
  2. TVB-32 -> docs/reviews/tvb32-codex-audit.md
     this repo 5b194a2..7a29dad (docs + analysis/round2.py); hip3-executor fd4db97, 35a73a4,
     2dc9490, 68dca79, cbea184 (merged e2a91ad), 4b5d248. Focus: the entry-gate fix, the
     flip proxy / coupling split, fill matching, the pools and accuracy censuses.
  3. TVB-33 -> docs/reviews/tvb33-codex-audit.md
     this repo 7a29dad..7ad92f4 (the first commit, 6e124e2, is TVB-32's pin); hip3-executor
     4b5d248..d8a07b0 (derived: between TVB-32's deployed sha and TVB-34's range start;
     confirm in that repo's log). Read the TVB-33 entry's section 7 (the deep-dive fold)
     FIRST; the deep-dive review itself is already folded, do not re-review it. Focus: the
     round-3 prereg and rulings, the ledger replay harness and its parity claim, the
     round-3 build.
  4. TVB-34 -> docs/reviews/tvb34-codex-audit.md
     this repo 7ad92f4..00d243e; hip3-executor d8a07b0..5cd2b0d. Focus: the liquidation
     formula and clearing leverage, the weekly-dot verdict in gate and flip, partial-close
     VWAP across a restart, the feasible-fill twin change, the admission changes.
  5. TVB-35 -> docs/reviews/tvb35-codex-audit.md
     this repo 848db00..3f087b0 (5b028a5, 0406503, 3f087b0); hip3-executor 5cd2b0d..fc90368.
     Focus: the seat-stage gating of the l2Book read, the per-poll cache keyed by coin, the
     weekly-dot-duplicates-daily claim on Sun/Mon, Labor Day labelling, the ZEC liquidation
     placement, the macro-regime receipt's labeler.
  6. TVB-37 close-out -> docs/reviews/tvb37-close-codex-audit.md
     this repo ea58c6c..9e0f95e. Two sub-ranges were already audited and folded
     (docs/reviews/tvb37-codex-audit.md for ecc4d6c..8b800a7; tvb37-chance-codex-audit.md
     for 4560e7c..c0f1826): check that their findings were folded as the HANDOFF syntheses
     say, then review the UNREVIEWED commits 4560e7c, cff7932, dadf8ef and the close-out
     docs per docs/reviews/REVIEW_REQUEST.md (the book arithmetic, the R-matched
     reweighting, the chart-page data mapping, BOOK_RECEIPT.md sentences vs tables, prereg
     A3/A4, hygiene: no claude.ai artifact link anywhere in the repo).

TVB-36 was waived by the owner (N/A); do not review it.

Rules for every file: copy docs/reviews/_TEMPLATE.md (keep its skeptic preamble); sections
"## 1. Metadata" (session, reviewed range, your model id, verdict APPROVE |
APPROVE-WITH-NITS | NEEDS-CHANGES | BLOCK), "## 2. Verbatim audit" (findings grouped by the
block's focus areas, each with file:line and a severity tag CRITICAL | HIGH | MEDIUM | LOW |
NOTE; say explicitly when an area checks out clean and how you verified it), "## 3.
Actionable items" (numbered: finding -- severity -- file:line -- fix). Plain ASCII only (no
em-dashes, curly quotes or emoji). You may run `uv run pytest tests/ -q` and read any file;
do NOT run analysis/domino/census.py or chance.py end to end (they hit a public API), do not
modify any file other than the six audit files, and never paste a secret, host, IP, wallet
address, account value or claude.ai link into them: this repository is public. When all six
are written, print one summary line per session: file, verdict, number of findings by
severity.
```
