# CURRENT REVIEW REQUEST -- tradingview-backtesting

> Entry point for external reviewers. If you are Codex (`/session-review`) or any other
> external review agent pointed at this repo: this file is your work order. It
> always describes the LATEST requested session review and is rewritten by
> `/session-end` each session. The permanent per-session record is the
> `### External Review` block in `docs/HANDOFF.md`; for the CURRENT request,
> this file wins if the two disagree. Full contract:
> `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Status

- Status: REQUESTED
  <!-- REQUESTED | RETURNED (audit file written) -->
- Session under review: TVB-24 -- both pending reviews folded + TV mirror
  parity-gated. (1) TVB-23 Codex audit fold: all five findings reproduced
  before adjudication; the three guard families hardened fail-closed with
  17 adversarial regression tests; the two prereg-bound diagnostics
  delivered post-hoc as receipts (ATR%-of-price context; matched-entry
  exits-in-isolation); dated prereg/report corrections incl. the
  provenance downgrade + prereg_blob_sha256 in future manifests. (2) The
  2026-08-14 strategy-implementation assessment folded: both of its
  numerical diagnostics reproduced exactly, then committed as
  entry_audit.py receipts (identity funnel, decision-close fill benchmark,
  NEW entry-containment finding: 11/765 fills outside the entry bar's
  range, all pessimistic-direction); CLAUDE.md/README constitution sync.
  (3) Prereg step 7 closed: floor/ATR/arm-selector mirrored into the
  package pine (H8), TV-synced sha-verified, and the 9-cell parity gate
  PASSED (218/218 events, all six arms now TV-valid).
- SCOPE: standard.
- Requested: 2026-08-15
- Write the audit to: `docs/reviews/tvb24-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: tvb8/tvb9 remain unreturned (standing note).

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `674c7f6^..130013e` (4 commits: 674c7f6 audit fold; 33c7138 assessment fold; b58688e TV mirror + gate PASS; 130013e session-end docs. Sanity-checked -- `git diff --name-status 674c7f6^..130013e` lists all files the session touched) |

## Read first (in this order)

1. `CLAUDE.md` (note: the header sentence about the Python engine was
   corrected this session); charter Section 0 (S3.1 amendments unchanged).
2. `docs/HANDOFF.md` -- the TVB-24 entry at top, INCLUDING the TVB-23
   audit critical synthesis inside the TVB-23 entry's External Review
   block (written this session).
3. `docs/reviews/tvb23-codex-audit.md` (the audit folded this session) and
   `docs/strategy-implementation-assessment.md` (the second review folded
   this session; its adjudication is in the TVB-24 conversation record and
   HANDOFF entry).
4. `docs/experiments/tvb23_t1floor_prereg.md` + `_report.md` -- read the
   2026-08-15 dated corrections and verify nothing above them was
   silently rewritten (git diff shows the exact edits).
5. `analysis/paper/tier_b_t1floor.py`, `analysis/paper/round_census.py`
   (hardened gates), `tests/test_t1floor_gates.py` (the adversarial
   suite), `analysis/paper/t1floor_diagnostics.py`,
   `analysis/paper/entry_audit.py` (new receipts + their tests).
6. `pine/tfc_mt_package_strategy.pine` H8 hunk vs
   `analysis/paper/engine.py` (the verbatim-semantics claim);
   `scripts/tvb23_pkg_harvest.mjs`; `analysis/paper/pkg_parity.py`
   (--arms extension); `analysis/reference/pkg_parity/tvb23_parity_result.json`.
7. `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Focus areas (scrutinize these)

1. Gate hardening: are the three families NOW genuinely fail-closed
   (union-of-field comparison + row cardinality both directions; all 15
   depth pairs + symbol-set equality + prefix-next-must-be-exit; census
   open count/direction + event linkage)? Do the 17 adversarial tests
   actually kill each mutation (try mutations the tests missed)?
2. Receipt integrity: t1floor_diagnostics + entry_audit reproduce from
   committed artifacts; the matched-exit "exits-in-isolation" read
   declares its survivor-shape boundary honestly (subset = closed in ALL
   six arms); the ATR% context math is engine-verbatim (_Atr reuse, seed
   slice mirrors the runner).
3. Pine H8 semantics vs engine.py: floor evaluated BEFORE the extended
   no-target skip with the exact counter split; strict d < floor;
   ATR Wilder math + completed-bar update ORDER vs replay_bar; pct/ATR
   mutual exclusion by arm; the startswith chain tests D1ATR before D1;
   TVB-22 arms decision-identical (arm-gated off paths).
4. Parity gate extension: harvest prefix routing (tvb22 vs tvb23 files),
   generation-scoped result artifact (the committed TVB-22 pin can never
   be overwritten), the claim that the gate twin's ATR is seed-exact vs
   the pine (both warm from the same loaded bars -- check twin_events).
5. The 9-cell PASS itself: re-derive a cell from the committed dumps +
   tv_deep feeds if possible; verify beyond-feed clipping is honest and
   the in-window coverage is complete.
6. Language discipline: dated corrections only, no silent rewrites; the
   three-benchmark fill framing used consistently; no promotion anywhere.
7. request.security: no new calls in the range (H8 is local aggregation
   only; verify).

Standing priorities apply (model fidelity; overfitting language; controls
are research instruments, never deployment claims).

## Output contract

- Verbatim audit -> `docs/reviews/tvb24-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value.
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
