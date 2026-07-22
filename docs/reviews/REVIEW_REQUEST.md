# CURRENT REVIEW REQUEST -- tradingview-backtesting

> Entry point for external reviewers. If you are Codex (`/session-review`) or any other
> external review agent pointed at this repo: this file is your work order. It
> always describes the LATEST requested session review and is rewritten by
> `/session-end` each session. The permanent per-session record is the
> `### External Review` block in `docs/HANDOFF.md`; for the CURRENT request,
> this file wins if the two disagree. Full contract:
> `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Status

- Status: REQUESTED  <!-- REQUESTED | RETURNED (audit file written) -->
- Session under review: TVB-15 -- the paper-trading twin layer (Python port
  of the live v6/v6.1 Pine + scanner-fed roster + HL archive +
  deterministic replay + fixture-parity goldens), the week-1 frozen
  artifacts, and the same-day TVB-14 audit fold-in (both HIGH findings
  reproduced, fixed as v6.1, deployed, parity-verified live).
- SCOPE: standard.
- Requested: 2026-07-20
- Write the audit to: `docs/reviews/tvb15-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: tvb8/tvb9 requests remain unreturned (standing note). tvb14 was
  returned AND addressed same day (see the TVB-14 HANDOFF block). TVB-16
  (2026-07-22) was a light session -- ride-along refresh + a read-only
  ablation tool + docs notes -- and was intentionally NOT submitted for
  review (user decision); TVB-15 remains the current outstanding request.

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `75eba90^..b9b93cb` (5 commits: 75eba90 = paper twin tooling; 416c84e = week-1 freeze; 73670ff = v6.1 fix; 142dfe6 = audit RETURNED docs; b9b93cb = session-end docs; sanity-check with `git diff --name-status 75eba90^ b9b93cb`) |

Sibling-workspace delivery (context only, NOT part of this repo's range):
`C:\Strat_Trading_Bot\hip3-scanner\docs\SCORE_METHODOLOGY_DUAL_REVIEW_2026-07-20.md`
(uncommitted there; local transport only).

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0.
2. `docs/HANDOFF.md` -- the TVB-15 entry at top (four arcs; the External
   Review block there mirrors this request).
3. `docs/experiments/tvb15_paper_week1_protocol.md` (the week's a-priori
   contract + fix-forward record -- part of the reviewed claim set).
4. `docs/reviews/tvb14-codex-audit.md` (the prior audit this session
   folded in; its findings are load-bearing context for v6.1).
5. `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Focus areas (scrutinize these)

1. Engine-vs-Pine port fidelity (analysis/paper/engine.py vs
   pine/tfc_bf_watch.pine): per-bar processing order (sweep -> accumulate
   -> collect-before-transition scan -> exit race bf>brk>flip -> entry ->
   arm roll LAST), direction-relative eligibility, float trigger
   arithmetic, the v6.0/v6.1 behavior flags.
2. Golden methodology: byte-for-byte parity vs fixture-generated text
   (tests/golden/) with the two FIXTURE_SUPERSEDE_SHADOWS exceptions --
   attack the soundness of pinning the engine's formatter against the
   fixture's output, and the exception invariant test.
3. v6.1 fix edges: per-side supersede vs the dup-ghost scan ordering;
   retired-first eviction under sustained all-alive pressure (residual
   evict-alive counting); the Pine 13-array array.remove lockstep.
4. Replay conventions honesty: fill prices (bf at line value, brk/flip at
   close), last-bar drop, warm-up boundary + flat start, 5m confirmed
   semantics, seeded arm window; declared-deltas completeness.
5. Roster selector (analysis/paper/roster.py) vs its a-priori claims;
   archive merge newest-wins semantics; provisional-vs-TV mintick
   provenance handling (SKHX hl_inferred path).
6. The session's own verification claims: the audit census reproductions
   (12h 54/42/22, D 27/15/6), the roster live-impact sweep (note its
   uncapped-as-truth caveat), post-fix parity numbers (13/11/2/0;
   evict-alive 14 vs 13+1), and the identical-18-events continuity claim.
7. Deploy verification (version 6.0 -> 7.0 on USER;7c28fa0b, table title
   v6.1) and the restored header bullets (repo-vs-deployed drift).

Standing priorities apply (request.security lookahead -- the Pine still
claims zero; model fidelity; overfitting language -- min_sep is now labeled
provisional example-derived, check the relabel landed everywhere it should).

## Output contract

- Verbatim audit -> `docs/reviews/tvb15-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value.
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
