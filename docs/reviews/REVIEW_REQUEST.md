# CURRENT REVIEW REQUEST -- tradingview-backtesting

> Entry point for external reviewers. If you are Codex (`/session-review`) or any other
> external review agent pointed at this repo: this file is your work order. It
> always describes the LATEST requested session review and is rewritten by
> `/session-end` each session. The permanent per-session record is the
> `### External Review` block in `docs/HANDOFF.md`; for the CURRENT request,
> this file wins if the two disagree. Full contract:
> `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Status

- Status: RETURNED 2026-07-17  <!-- REQUESTED | RETURNED (audit file written) -->
  (Codex CLI / GPT-5.6 Sol Max, run by the user; verdict NEEDS-CHANGES;
  audit: docs/reviews/tvb12-codex-audit.md; critical synthesis: the TVB-13
  entry in docs/HANDOFF.md)
- Session under review: TVB-12 -- TVB-11 audit fold-in + critical synthesis;
  fail-closed bounded replay (68 cells + 3 anchors, TVB-11 record verified
  36 CLEAN/18 DRIFT/0 SUSPECT, direction repair mapped); champion harness v2
  (nonce echo + realtime-bar table fix); Winner: ShortChamp MU5 indicator
  shipped; session ends with a user redirect to the TVB-13 exit arc.
- SCOPE: LIGHT (user decision) -- this session was mostly verification work;
  the TVB-13 exit-arc implementation gets the full review next.
- Requested: 2026-07-16
- Write the audit to: `docs/reviews/tvb12-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: tvb8/tvb9 requests remain unreturned (standing note).

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `f97646e^..` head-at-session-end (f97646e = review fold-in commit; head = the session-end docs commit; sanity-check with `git diff --name-status`) |

No sibling-repo changes this session.

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0.
2. `docs/HANDOFF.md` -- the TVB-12 entry at top (incl. the critical synthesis
   of the TVB-11 audit and the session-end redirect).
3. `docs/experiments/tvb12_replay_plan.md` -- plan + results (the record).
4. `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Focus areas (light scope -- scrutinize these four)

1. `pine/winner_shortchamp_mu5.pine`: written fast premarket by mirroring
   `pine/winner_generalizer.pine`. Verify the long->short mirror is faithful:
   short trigger = strict break of the prior COMPLETED 15m bar low (- 1 tick);
   STATE exit fires at the first 60m close where full D/W/M DOWN alignment is
   LOST (not only on opposite); ratchet_c block tracks the post-harvest LOW
   via math.min and re-entry requires strictly below it; the block clears only
   on re-entry fill or full OPPOSITE (up) alignment at a 60m close; harvest =
   LOWER-line deviation only.
2. `scripts/tvb12_replay_collect.mjs`: is acceptance now fully causal (nonce
   echo AND entity-bound applied readback AND closed-side report<->table
   binding, stable x2, no time escape)? Any remaining path to accept a stale
   or wrong-config report?
3. `scripts/tvb12_replay_compare.mjs`: is the CLEAN/DRIFT/SUSPECT method sound
   (overlap-window trade matching, matched-fraction 0.8 threshold)? Could it
   mask contamination as DRIFT?
4. Prose vs data: do the HANDOFF/plan-doc claims ("record VERIFIED",
   "F1/F4 closed") overreach the raw JSONLs?

Standing priorities apply (request.security lookahead; model fidelity;
overfitting language; fee/turnover math) but the deep dive is deferred to the
TVB-13 implementation review.

## Output contract

- Verbatim audit -> `docs/reviews/tvb12-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value.
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
