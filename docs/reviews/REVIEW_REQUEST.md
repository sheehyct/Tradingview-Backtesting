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
- Session under review: TVB-18 -- week-1 close-out (archive/replay,
  week-end pass, fresh-mount parity), the TVB-15 audit fold-in (all four
  findings independently reproduced; freeze_slice tool; doc corrections +
  status flips), the Magnitude+Targets [Custom] indicator pair, the
  week-1 adjudication + design-direction records, and the thestrat_ai
  corpus gitignore protection.
- SCOPE: standard.
- Requested: 2026-08-04
- Write the audit to: `docs/reviews/tvb18-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: TVB-15 RETURNED 2026-08-04 (docs/reviews/tvb15-codex-audit.md,
  NEEDS-CHANGES) and was folded in the same day -- its adjudication lives
  in the TVB-18 HANDOFF entry and the protocol doc fold-in section.
  tvb8/tvb9 requests remain unreturned (standing note).

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `a1a886f^..{pending push -- pinned by the session-end follow-up commit}` (week-1 close-out; indicator pair; audit fold-in; adjudication; corpus gitignore; session-end docs. Sanity-check with `git diff --name-status a1a886f^ HEAD`) |

Context only, NOT in the range: `docs/thestrat_ai/` is a gitignored
LOCAL-ONLY corpus (scraped stratalerts.ai curriculum mirror; public repo,
not ours to republish). A local-transport reviewer may read it; a cloud
reviewer will not see it -- that asymmetry is deliberate.

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0.
2. `docs/HANDOFF.md` -- the TVB-18 entry at top (the External Review
   block there mirrors this request), then the TVB-15 entry's RETURNED
   block + in-place F4 annotation.
3. `docs/experiments/tvb15_paper_week1_protocol.md` -- the TVB-18
   week-end pass, the audit fold-in section, and the week-1 adjudication
   (user decisions; part of the reviewed claim set).
4. `docs/reviews/tvb15-codex-audit.md` (the audit TVB-18 folded in; its
   findings are load-bearing context for everything this session did).
5. `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Focus areas (scrutinize these)

1. `analysis/paper/freeze_slice.py` correctness: the slice boundary
   semantics (closed trades split by entry_ts vs the freeze, events
   counted by ts; parity-symbol exclusion; open-at-window-end
   attribution) -- and whether the +14.37pp clean-slice number is framed
   anywhere as performance evidence, which the user's adjudication
   explicitly forbids (week 1 = process test run, NO official number).
2. `analysis/paper/parity_state.py` fidelity to replay.py conventions
   (warm-up boundary, seed windows, last-bar drop via load_rows, arm
   seeding) and whether the TVB-18 parity claims honestly bound what a
   FRESH-MOUNT comparison can and cannot show (census not comparable;
   operative-rung deltas 0.004-0.04%; the DRAM gate read-gap resolution).
3. The fold-in adjudications vs the audit text: were F1-F4 reproduced
   faithfully (18/81 + 12/37 counts, the 13:26:36Z snapshot decode, the
   TSLA 07-16 lifecycle repro, the Pine ev_alive semantics) and were the
   actions proportionate (docs corrected now, code repairs greenlit but
   deferred to the design bundle)?
4. The pre-commit Check 2 amendment vs pine/README.md rule 3 (same rule,
   no drift), and the TVB-17-era claim that /pre-commit false-FAILed 5
   files now being cleared.
5. The new indicator pair (pine/strat_magnitude_targets_plus.pine +
   README): the zero-request.security claim, the defaults-render-
   identical-to-original claim, and byte-identity vs the canonical
   tv_indicators copy (local transport only).
6. Repo hygiene of the corpus protection: .gitignore entry placement and
   whether anything from docs/thestrat_ai/ leaked into tracked content.

Standing priorities apply (request.security lookahead; model fidelity;
overfitting language -- the week-1 adjudication language should nowhere
morph into a performance claim).

## Output contract

- Verbatim audit -> `docs/reviews/tvb18-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value.
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
