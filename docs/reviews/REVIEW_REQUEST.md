# CURRENT REVIEW REQUEST -- tradingview-backtesting

> Entry point for external reviewers. If you are Codex (`/session-review`) or any other
> external review agent pointed at this repo: this file is your work order. It
> always describes the LATEST requested session review and is rewritten by
> `/session-end` each session. The permanent per-session record is the
> `### External Review` block in `docs/HANDOFF.md`; for the CURRENT request,
> this file wins if the two disagree. Full contract:
> `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Status

- Status: RETURNED (audit file written 2026-08-16; verdict NEEDS-CHANGES,
  1 HIGH + 4 MEDIUM + 2 LOW; fold in progress TVB-26)
  <!-- REQUESTED | RETURNED (audit file written) -->
- Session under review: TVB-25 -- TVB-24 audit folded + the exit round
  built, run, and reported in one session. (1) Audit fold: F3-F6 fixed
  with every false-PASS path reproduced first (entry-stream gate with
  stream-vs-rec reconciliation; canonical parity artifact protection +
  wrapper validation; matched-identity frozen-state binding; additive
  receipt provenance with field-diff proof). (2) F1/F2 became a dated
  prereg AMENDMENT ruled live by the user (S0c arm, risk-first collision
  race + two fill classes, P2/X1/i3/stop mechanics pinned, D9-D14). (3)
  The round executed per the prereg's binding order: fresh harvest with
  the D13 window pin, engine extensions behind inert defaults, the
  tier_b_exits.py runner (two gate-caught corrections committed BEFORE
  the clean rerun, forward protocol), canonical run with all gates PASS
  on both windows, report, and the new plain-language ARM_LEDGER.
- SCOPE: standard.
- Requested: 2026-08-16
- Write the audit to: `docs/reviews/tvb25-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: tvb8/tvb9 remain unreturned (standing note).

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `b31c11d^..6597a68` (11 commits, 98 paths: b31c11d audit fold; 2411821 prereg amendment; 047d695 harvest + D13 pin; 007208e engine; 209d2ef runner; 5796da2 + 7f3626e the two forward-protocol gate corrections; 62ff310 canonical run; 40c94ce report; b38e0ad ARM_LEDGER; 6597a68 session-end docs. The range-pin commit after 6597a68 is docs-only routing, out of range. Sanity-checked: `git diff --name-status b31c11d^..6597a68` lists every file the session touched) |

## Read first (in this order)

1. `CLAUDE.md` (new binding Reporting rule: ARM_LEDGER practice); charter
   Section 0.
2. `docs/HANDOFF.md` -- the TVB-25 entry at top, INCLUDING the TVB-24
   audit critical synthesis inside the TVB-24 entry's External Review
   block (written this session).
3. `docs/experiments/tvb25_exit_round_prereg.md` -- the ruled base text
   AND the 2026-08-16 amendment + pins (verify nothing above the
   amendment was silently rewritten; git diff shows the exact edits).
4. `docs/reviews/tvb24-codex-audit.md` (the audit folded this session).
5. `analysis/paper/engine.py` (TVB-25 features: the ruled race, fill
   classes, state stop, i3, stops, tranches) + `analysis/paper/patterns.py`
   (stop-anchor table) + `tests/test_tvb25_exits.py`.
6. `analysis/paper/tier_b_exits.py` + `tests/test_tier_b_exits.py` +
   `analysis/paper/tier_b_exits/` (manifest, results, matched-entry
   receipts, event streams).
7. `docs/experiments/tvb25_exit_round_report.md` + `docs/ARM_LEDGER.md`.
8. Audit-fold code: `analysis/paper/tier_b_t1floor.py` (_entry_stream_gate,
   both-sides-exit rule), `analysis/paper/round_census.py` (injective
   linkage), `analysis/paper/pkg_parity.py` (canonical protection +
   wrapper validation), `analysis/paper/t1floor_diagnostics.py` +
   `analysis/paper/entry_audit.py` (frozen-state contract, provenance),
   `scripts/tvb23_pkg_harvest.mjs` (arm read-back), and the three test
   files extended for them.

## Focus areas (scrutinize these)

1. Amendment coherence: can an independent implementer now derive ONE
   exact event stream from the prereg + amendment (collision order, two
   fill classes, P2 fold-to-runner / arm-and-fire / reading-A breakeven,
   X1 arming, i3 level+scope+degenerate, stop_anchor immutability and
   degeneracy, D14 inclusive state stop)? Does the ENGINE match the
   amendment clause by clause?
2. Inert defaults: the 55 Tier B + 88 T1-floor committed rows replayed
   field-equal through the extended engine -- verify the claim and try
   mutations the fixtures missed (the new race must not perturb any
   default-path decision; the incumbent tgt/bf/brk/flip relative order is
   claimed preserved inside the new race so overlay-minus-overlay equals
   base).
3. Runner gates: the tranche final-exit stream convention (partially
   banked OPEN entries contribute no exit -- is that fail-closed against
   deleted final exits?); family anchors (A0b replayed in-memory, D1 from
   committed events); tranche fraction reconciliation; the veto-counter
   modulo-rule fix (is it exactly the declared TVB-23 rule, no wider?).
4. The two forward-protocol corrections: were they genuinely committed
   before the clean rerun, and are their regression tests adversarial?
5. Report + ledger vs artifacts: recompute the headline contrasts (S0a/
   S0c/A0bS vs A0b; P1/P2/X1/D1i3/D1S/PX vs D1; matched-entry aggregates)
   and check every occupancy-vs-per-trade claim against the matched
   receipts; D10 fee math; the D9 near-zero collision claim.
6. Harvest integrity: the merge-check claim (zero July-window rows
   changed; exactly the three 2026-08-04 forming-bar rows completed);
   the D13 pin language.
7. Language discipline: dated amendment only (no silent rewrites above
   it); no promotion anywhere; extreme numbers framed as questions;
   survivor-shape boundaries declared on every matched read.
8. request.security: NO pine file changed this session -- verify none
   did.

Standing priorities apply (model fidelity; overfitting language; controls
are research instruments, never deployment claims).

## Output contract

- Verbatim audit -> `docs/reviews/tvb25-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value.
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
