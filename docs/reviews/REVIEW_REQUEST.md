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
- Session under review: TVB-23 -- TVB-22 audit fold-in (pkg_parity pattern
  layer hardened fail-closed after reproducing the NaN/missing-trig false
  PASS; ladder-census receipt reproducing the audit's readings exactly;
  metadata fixes) + the T1-floor round: design session (7 user rulings),
  prereg committed BEFORE code with three dated corrections (pine
  comment-vs-code edge; counter-equation reconciliation; the
  identical-entry-book gloss corrected after the run-time gate caught the
  one-position occupancy funnel 137->50), engine floor/ATR/retracement
  extensions behind inert defaults (20 fixtures), runner with
  determinism/entry-stream/reconciliation gates (all PASS), full 13-arm
  run, per-arm census receipts, report. Also: TV-side header sync
  (byte-verified) after the prior session's audit item.
- SCOPE: standard.
- Requested: 2026-08-12
- Write the audit to: `docs/reviews/tvb23-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: tvb8/tvb9 remain unreturned (standing note).

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `{pending push -- pinned by the session-end follow-up commit}` |

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0 (S3.1 amendments unchanged this session).
2. `docs/HANDOFF.md` -- the TVB-23 entry at top (incl. the TVB-22 audit
   synthesis inside the TVB-22 entry's External Review block).
3. `docs/experiments/tvb23_t1floor_prereg.md` (binding spec; note the
   three DATED corrections and verify each predates the code/results it
   governs) and `docs/experiments/tvb23_t1floor_report.md`.
4. `analysis/paper/tier_b_t1floor.py` docstring (the gates) and
   `analysis/paper/round_census.py` docstring (census conventions);
   `analysis/paper/ladder_census.py` (the TVB-22 F2 receipt).
5. `docs/reviews/tvb22-codex-audit.md` (the audit folded this session).
6. `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Focus areas (scrutinize these)

1. Fold-in fidelity: the F1 reproduction (missing/NaN false PASS on
   committed GOOGL/A1; +inf already failed), the two-layer fail-closed
   fix in `analysis/paper/pkg_parity.py`, the deliberate NON-regeneration
   of the committed parity artifact, the 12 regression tests.
2. Receipt integrity: `ladder_census.py` receipt vs its committed
   numbers; `round_census.py` conventions vs the prereg (entry bar
   excluded, exit bar included, label bar EXCLUSIVE for before-label
   rungs, roster scope excluding xyz:DRAM); every determinism guard
   fail-closed.
3. Floor veto semantics vs prereg + amendments: strict `d < floor`,
   born-beyond/tiny/only counter split, empty-ladder uniform structural
   skip across ALL floor arms (incl. C1-exit shapes), the DINF/A1F split
   design note, the counter reconciliation equation.
4. ATR: Wilder seed (SMA of first 14 TRs) + smoothing math, first-bar
   TR = h-l convention, price-unit veto predicates, and that the PCT
   predicate arithmetic is byte-untouched (determinism arms depend on it).
5. Retracement layer: truly read-only (nothing the position machine
   reads; golden event shape unchanged when the flag is off); the
   as-built one-sided-flag edge fixture vs
   `pine/strat_magnitude_targets_plus.pine:192-206,694-716`.
6. Runner gates: determinism arms replayed through `tier_b._replay_arm`
   itself, field-equality modulo zero-valued NEW veto keys only;
   entry-stream first-divergence-is-exit logic; the occupancy funnel
   (137/108/93/89/85/50) reproduced.
7. Report + language discipline: rerun the rollup arithmetic; contrasts
   only; no arm/depth/setup promoted; constructed win rates flagged;
   S3.1 never adjudicated by package arms.
8. request.security: no executable Pine change in the range (the package
   header edit is comment-only; TV-side copy byte-verified in-session).

Standing priorities apply (model fidelity; overfitting language; controls
are research instruments, never deployment claims).

## Output contract

- Verbatim audit -> `docs/reviews/tvb23-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value.
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
