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
- Session under review: TVB-26 -- the TVB-25 external audit folded IN
  FULL the same day it returned (NEEDS-CHANGES, 1 HIGH + 4 MEDIUM +
  2 LOW; zero disputes). (1) All seven findings reproduced in-repo
  BEFORE adjudication (F1 worse than the audit's lower bounds). (2) Two
  dated USER RULINGS: D14 entry-hour literal-inclusive (the entry hour
  counts; same-bar state_degenerate scratches) and, after the corrected
  census, risk-first STANDS. (3) Engine/runner repairs committed before
  the rerun: D9 census transition-accumulated + collision_pairs;
  zero-duration episode support end-to-end; DECLARED gate expectations;
  stop_src_ts. (4) Canonical artifacts REGENERATED under prereg
  amendment 2026-08-16b with a field-diff receipt (only S0 streams
  changed, by exactly the ruled scratches; stop arms additive-only;
  matched receipts unchanged to the 4th decimal). (5) Report + ledger
  corrected (Finding 5 retracted-in-place and rewritten; axis/units/
  comparator-universe fixes). (6) HANDOFF critical synthesis + archive
  split (TVB-18..21 moved verbatim to docs/session_archive/).
- SCOPE: standard.
- Requested: 2026-08-16
- Write the audit to: `docs/reviews/tvb26-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: tvb8/tvb9 remain unreturned (standing note).

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `53599c4^..7f91c9c` (7 commits, 30 paths: 53599c4 audit recorded + status flips; 4631dbd prereg amendment 2026-08-16b, before code; cea3372 engine/runner repairs + 7 tests; 0c95a60 regenerated canonical artifacts; 871ca78 report/ledger corrections; 3da1e20 critical synthesis; 7f91c9c session-end docs + HANDOFF archive split. RANGE-PIN RULE: the caret keeps 53599c4 in the diff; sanity-checked: `git diff --name-status 53599c4^..7f91c9c` lists every file the session touched. The pin commit after 7f91c9c is docs-only routing, out of range.) |

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0.
2. `docs/reviews/tvb25-codex-audit.md` (the audit being folded) and the
   critical synthesis in the TVB-25 entry's External Review block in
   `docs/HANDOFF.md` (written this session).
3. `docs/experiments/tvb25_exit_round_prereg.md` -- the amendment
   2026-08-16b section AND the risk-first revisit outcome (verify
   nothing above it was silently rewritten; git diff shows the exact
   edits).
4. `analysis/paper/engine.py` (the D9 census rewrite around
   `_tvb25_exit_race`; the D14 post-entry block in `_position_step`;
   the stop_src_ts freeze) + `analysis/paper/patterns.py`.
5. `analysis/paper/tier_b_exits.py` (zero-duration guards on both
   episode paths; `_expected_family_arms`; collision_pairs plumbing) +
   `tests/test_tvb25_exits.py` + `tests/test_tier_b_exits.py`.
6. `analysis/paper/tier_b_exits/` (regenerated: manifest, rollups,
   events, matched receipts).
7. `docs/experiments/tvb25_exit_round_report.md` (corrected) +
   `docs/ARM_LEDGER.md`.

## Focus areas (scrutinize these)

1. D9 correctness: independently reconstruct the collision census from
   ordered per-bar eligibility (the prior audit's suggested check) and
   compare to the stored counters AND collision_pairs. Verify the claim
   that every prot+tgt bar is the order-forced arm-and-fire chain (zero
   already-armed-floor collisions) -- that claim carried the user's
   risk-first ruling.
2. D14 implementation vs the dated ruling: post-entry check placement
   (race runs flat, so the entry bar needs its own check), i3-before-
   state order on a shared entry bar, strict-break boundary, and the
   mid-hour-consistency argument (pre-entry same-hour breaks already
   counted for mid-hour entries) -- is that argument TRUE in the
   committed streams?
3. The regeneration field-diff claims: non-S0 non-stop event streams
   byte-identical; D1S/PX additive stop_src_ts only (all old fields
   byte-equal); S0 deltas exactly the ruled scratches (14/14/15 July,
   6 roster fresh); matched-entry receipts unchanged to the 4th decimal.
4. Gate expectation: mutate at the caller boundary (remove a produced
   arm) under canonical AND smoke paths; verify the veto_counts modulo
   rule stayed exact-scope (new-zero-only, veto_counts only).
5. Zero-duration episodes: P&L retained, MFE/MAE/give-back excluded,
   BOTH runner episode paths guarded; would the month-end extension
   survive an i3_degenerate or state_degenerate event end-to-end?
6. Recompute the corrected report/ledger numbers: S-family July/fresh,
   matched sums AND means, the ~+19pp fresh S0a-vs-A0b combined gap,
   the scoped P1 per-trade claim vs the D5 receipt.
7. Language discipline: amendment 2026-08-16b dated and append-only;
   Finding 5 retraction named in place; no promotion anywhere; the
   HANDOFF archive split moved entries VERBATIM.
8. request.security: NO pine file changed this session -- verify none
   did.

Standing priorities apply (model fidelity; overfitting language; controls
are research instruments, never deployment claims).

## Output contract

- Verbatim audit -> `docs/reviews/tvb26-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value.
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
