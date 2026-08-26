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
- Session under review: TVB-28 -- weekend-1 ledger analysis closed out and
  BOTH outstanding audits folded. The TVB-27 audit (returned 2026-08-25,
  NEEDS-CHANGES, folded same session) already reproduced and corrected
  the analysis THROUGH hip3-executor commit 2daf6a4 -- do not re-litigate
  what it settled; THIS request covers what came after: the conviction
  census (explicitly outside the prior audit's pin), the TVB-26 fold
  (D9 relabel + user re-ruling 2026-08-24 + the new collision-receipt
  instrument + 3 LOW fixes), the TVB-27 fold edits themselves, and the
  session docs.
- Requested: 2026-08-26
- Write the audit to: `docs/reviews/tvb28-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: tvb8/tvb9 remain unreturned (standing note).

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `4a07107^..{pending push}` -- the TVB-27 review-scope docs commits (4a07107, c772864, 4bb6780, 3782383), the TVB-26/27 fold commit df291ef (engine collision receipts + two-way gate + round-once fee + 5 tests + D9 doc corrections + audit committed), and the session-end docs. RANGE-PIN RULE: the caret keeps 4a07107 in the diff; sanity-check with `git diff --name-status`. |
| hip3-executor (PRIVATE github.com/sheehyct/hip3-executor; local transport only) | `C:\Strat_Trading_Bot\hip3-executor` | `21bd2a9^..e782e57` (3 commits: conviction census 21bd2a9 -- UNREVIEWED by the TVB-27 audit, which was pinned at 2daf6a4; audit-fold corrections dd1a591; operator-context addendum e782e57) |

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0. Then `docs/reviews/tvb27-codex-audit.md`
   (the prior audit whose findings this session folded -- the baseline for
   judging the corrections).
2. This repo: `analysis/paper/engine.py` (collision receipts around the
   exit race), `tier_b_exits.py` (fee_sides + receipts in rec/rollup),
   `tier_b_t1floor.py` (two-way gate), `tests/test_tvb25_exits.py` +
   `tests/test_t1floor_gates.py` + `tests/test_tier_b_exits.py` (new
   tests), `docs/experiments/tvb25_exit_round_report.md` Finding 5 +
   prereg amendment + `docs/ARM_LEDGER.md` (D9 corrections).
3. hip3-executor: `runs/2026-08-22_weekend1/ANALYSIS.md` (conviction
   census + corrections + operator context), `analysis/weekend1.py`,
   `analysis.json`, repo `README.md` (the binding pre-live gate).
4. This repo's `docs/HANDOFF.md` TVB-28 entry (the session record incl
   the critical synthesis of the TVB-27 audit).

## Focus areas (scrutinize these)

1. Collision-receipt emitter correctness: candidate fills follow the
   ruled fill classes (protective = level / open on gap-through; profit =
   containment level; close-evaluated = 5m close), mid-race prot arming
   is captured, executed rows come from the actual race, and the change
   is PURELY ADDITIVE -- committed event streams must replay
   byte-identically; only new rec/rollup fields appear on the next regen.
2. D9 relabel fidelity: report Finding 5, the prereg's append-only
   amendment, and ARM_LEDGER all now state the convention basis (user
   re-ruling 2026-08-24), the retracted worse-fill claim, the 4/2 + 7/9
   sign evidence, and the 56->58 membership correction -- verify against
   the TVB-26 audit's MEDIUM and the committed artifacts.
3. Round-once fee (LOW-3 fix): fee_sides threads through `_rollup_arm`;
   NO committed canonical artifact may have been modified this session --
   the expected deltas (P1 fees_pp 1.0002->1.0000 July / 0.6502->0.6500
   fresh) appear only on the NEXT regeneration.
4. Conviction census (21bd2a9): method + claims under the same
   upper-bound-census discipline the TVB-27 audit enforced on the MMQB
   pools -- the near-target/anti-R:R finding, the 32x per-trade risk
   dispersion, and the pre-floor decomposition. Flag any sentence that
   turns the census into promotion or diagnosis.
5. The corrected ANALYSIS.md: does every retained claim now stay inside
   the mechanics-test boundary (observed-in-this-ledger framing), and are
   the corrections faithful to the audit's required changes (observed
   +17.34pp flip split, census reframing, structural-vs-sample cont
   wording)?
6. request.security: NO Pine file changed this session -- verify none did.

Standing priorities apply (model fidelity; overfitting language; the
weekend was a MECHANICS test -- any P&L sentence beyond characterization
is over-claim; the operator-context section is a USER a-priori thesis,
not a data conclusion -- flag it if it reads otherwise).

## Output contract

- Verbatim audit -> `docs/reviews/tvb28-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value:
  the VPS IP and the master wallet ADDRESS must both stay out of the
  audit (this repo is public -- the address lives only in the private
  hip3-executor repo: run README, analysis source, venue ledger record).
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
