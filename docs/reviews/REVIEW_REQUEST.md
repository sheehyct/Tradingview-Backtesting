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
- Session under review: TVB-14 -- TFC-BF v4->v6: the tier-1 watch
  indicator's BF exit engine rebuilt as rolling compound-3 pools
  (12h/D/W/M), designed with the user from MU/DRAM examples, deployed
  before the Jul-20 weekly open, then twice field-fixed same day (v5:
  multi-TF pools + min-anchor-separation filter after the zero-BF-exit
  report; v6: adverse-line break exit after the CL/WTIOIL case).
- SCOPE: standard.
- Requested: 2026-07-20
- Write the audit to: `docs/reviews/tvb14-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: tvb8/tvb9 requests remain unreturned (standing note).

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `{pending push -- pinned after session-end commit}` |

No sibling-repo changes this session.

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0.
2. `docs/HANDOFF.md` -- the TVB-14 entry at top (the v4->v6 arc, ratified
   decisions, known deltas).
3. `pine/tfc_bf_watch.pine` header (the honest-deltas list is part of the
   reviewed claim set).
4. `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Focus areas (scrutinize these)

1. `pine/tfc_bf_watch.pine` f_pool: the rolling sweep (envelope window
   indexing `cnt-2n..cnt-n-1` / `cnt-n..cnt-1`, smallest-N-wins, novelty/
   supersede/per-side-ghost rules, min_sep ghosting, pool-cap eviction of
   13 parallel arrays in lockstep).
2. Pine semantics: f_pool called 4x with per-call-site `var` state; pos/
   entry_px passed as prior-bar state; any cross-instance leakage.
3. Exit correctness: direction-relative eligibility (v < entry_px shorts /
   v > entry_px longs), exit ordering (harvest -> break -> flip), same-bar
   edges (entry+touch consumes without exit; stranded-line one-bar break
   window), barstate.isconfirmed on historical bars.
4. Lifecycle: consumption on ANY containment touch (incl. while flat) --
   implications for rung availability; crossed vs consumed transitions.
5. min_sep (1.0 periods): the a-priori claim -- derived from the user's
   previously-validated examples vs fitted to the DRAM sample? Attack it.
6. Zero `request.security` claim; chart-TF-tiling aggregation honesty.
7. analysis/tvb14_bf_pool_fixture.py: parity method vs the deployed
   drawings (1h-resolution lifecycle vs 5m chart; TV-vs-HL wick variance
   attribution to the TVB-6 class); committed reference bars
   (tvb14_dram_{1d,1h}_hl.json) provenance.
8. Deploy-verification claims in HANDOFF (version bumps, drawn-line
   cross-checks to the penny, the F3-birth-at-the-roll prediction).

Standing priorities apply (request.security lookahead; model fidelity;
overfitting language -- note the charter S0 framing on a-priori dials).

## Output contract

- Verbatim audit -> `docs/reviews/tvb14-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value.
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
