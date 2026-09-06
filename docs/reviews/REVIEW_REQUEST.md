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
- Session under review: TVB-34 -- the deep-dive external review folded (five
  executor mechanics repairs, halfway synthesizer fix + re-run, replay port),
  the feasible-fill research contrast, the round-3 package (weekly dot on gate
  and flip, four seats, $1 risk / $200 cap, rank + session shadows), go-live,
  and the agent-pruning incident.
- Requested: 2026-09-06
- Write the audit to: `docs/reviews/tvb34-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: TVB-31, TVB-32 and TVB-33 audits were never returned and stay open.
  The separate DEEP-DIVE review (docs/reviews/deep-dive-2026-09-05-astra.md)
  was RETURNED and FOLDED (HANDOFF TVB-33 section 7); do not re-review it,
  review the fold.

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `7ad92f4..00d243e` -- docs, the review file, `analysis/paper/engine.py` entry_fill, `tier_b_exits.py --entry-fill`, `tests/test_paper_engine.py`, `analysis/paper/tier_b_exits_feasible/` |
| hip3-executor (PRIVATE; local transport only) | `C:\Strat_Trading_Bot\hip3-executor` | main `d8a07b0..5cd2b0d`: 0562f14 (the fold: liq clearance, malformed-flat guard, Stop Market, partial-close fragments, dead sponsor, replay port, halfway decision price), c0074e0 (README amendment b, PREREG j/k, re-run receipts, before_amend_j/), 8beb8e8 (amendment c prereg), c531a8a (the package: stack_tfs, seats, risk, rank shadow), 9f39ba9 (session shadow; DEPLOYED), 3767c2f + 5cd2b0d (STATUS: live + incident) |

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0. Then the TVB-34 HANDOFF entry and TVB-33 section 7.
2. `docs/reviews/deep-dive-2026-09-05-astra.md` (what was folded) and the
   executor README amendments 2026-09-06b / 2026-09-06c.
3. Executor `src/hip3_executor/rules.py` (liq_distance / clearing_leverage,
   dots_dir / stack_dir, htf_reversal_backing exclude_invalidated,
   xyz_session_now), `broker.py` (_positions_state guard, PartialClose,
   _stop_row_ok), `engine.py` (_enter leverage + liq receipt, _close_record
   fragments, _exit_reason stack), `analysis/replay/{gates,recon,one_three}.py`,
   `tests/test_deep_dive_fold.py`, `tests/test_round3_package.py`.
4. `analysis/paper/engine.py` `_entry_step` + `tier_b_exits.py` ENTRY_FILL; the
   feasible receipt vs the canonical `analysis/paper/tier_b_exits/`.

## Focus areas (scrutinize these)

1. Liquidation formula and clearing-leverage selection vs the venue docs
   (tier-0 m = 1/(2 x maxLeverage); does anything change for larger tiers?);
   the post-fill `liq_inside_stop` receipt is warn-only by ruling.
2. The weekly dot: executor-computed `dots_dir` vs the scanner's coinSummary
   (missing slot, dead-even candle, the derived 1w candle's open); its use in
   BOTH the gate and the flip; the as-built four still reads the scanner field.
3. Partial-close fragments across a restart (state persisted before retry?);
   `_close_record` VWAP with `fill_sz` absent.
4. Amendment j: is "decision price = the cross minute's close" the right
   successor to D4's "fill at the halfway line"? The candidate set is still
   conditional on later far-side completion.
5. The feasible-fill twin change: only the arm-mode `_entry_step` should differ;
   determinism gates passed; the July anchors (A0b) are missing from the
   contrast receipt -- does that matter for the ARM_LEDGER watermark text?
6. Three admission changes on round 2 (fee floor, weekly dot, seats) plus
   risk/cap: are the journaled shadows sufficient to separate them at close?
7. The agent-pruning incident: fail-closed reconciliation held; is the
   "re-approve before re-funding" rule enough, or should the loop refuse to
   start when `extraAgents` does not list the .env agent?
8. request.security: NO Pine file changed -- verify none did.

## Output contract

- Verbatim audit -> `docs/reviews/tvb34-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value: the VPS
  IP, the master wallet address and the agent address stay out (this repo is
  public).
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
