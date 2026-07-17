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
- Session under review: TVB-13 -- TVB-12 audit fold-in (every recomputation
  independently re-run; C1 extended to all four winner watch surfaces; the
  champion strategy exonerated via resting stop orders; C4 relabels applied);
  BF Comprehension [TVB-13] designed with the user, built, and deployed
  (order-free indicator, two line-anchor modes incl. Rob-canonical
  price-proximity, freeze-as-of fixture tool); give-back instrumentation v1
  (calculator + archived DRAM June bars + hand-labeled acceptance tests that
  reproduce the user's live episode to the decimal).
- SCOPE: FULL (the deep review the user reserved when scoping TVB-12 light).
- Requested: 2026-07-17
- Write the audit to: `docs/reviews/tvb13-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: tvb8/tvb9 requests remain unreturned (standing note).

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `1f53463^..` head-at-session-end (1f53463 = BF design draft, first TVB-13 commit; head = the session-end docs commits; sanity-check with `git diff --name-status`) |

No sibling-repo changes this session.

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0.
2. `docs/HANDOFF.md` -- the TVB-13 entry at top (critical synthesis of the
   TVB-12 audit, the BF comprehension arc, give-back instrumentation).
3. `docs/design/bf_comprehension_indicator_design.md` -- the shipped design
   incl. both line-anchor modes and the behavioral semantics.
4. `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Focus areas (full scope -- scrutinize these)

1. `pine/bf_comprehension.pine`: strict R10 operators everywhere (equality
   never breaks); chart-side HTF aggregation correctness on 24/7 perps and
   its honesty notes; the price-proximity anchor scan (nearest prior low
   strictly above the 3's low / high strictly below); per-side independent
   anchoring; freeze-as-of semantics; repaint honesty of provisional
   (dashed) drawings; the rolling-mode window comparison and its buffer
   guard; supersede/fade lifecycle.
2. The TVB-12 synthesis C1 ADJUDICATION (docs/HANDOFF.md TVB-13 entry):
   does the resting-stop-order argument really exonerate the champion
   STRATEGY's early arm_last snapshot roll at EVERY child-bar position
   (tvb_exp_champion.pine:213-231 vs :313-345), including chart==ARM_TF
   cells and intrabar fills? This claim protects the entire TVB-11/12
   record -- attack it.
3. `analysis/giveback.py` + `tests/test_giveback_fixture.py` + the archived
   `analysis/reference/tvb13_dram_jun_15m_hl.json`: is the episode-pinning
   method (last downward cross before the bottom / first exit-level touch
   after) sound and honestly derived, or curve-fit to the user's account?
   Are the metric definitions (MFE/MAE window, give_back_pp/frac) correct
   and unambiguous?
4. The C4 relabels (TVB-12 status line, tvb12_replay_plan.md standing-verdict
   correction): do the dated corrections fully cure the overreach the TVB-12
   audit named, without touching raw results?
5. The frozen winner-surface header notes (pine/winner_*.pine): are the
   claims in them (entry-dead at chart==ARM_TF; final-child suppression;
   backtest unaffected) each independently verifiable from the code?

Standing priorities apply (request.security lookahead -- note the pending F7
amendment: the trap is UN-OFFSET lookahead_on; bf_comprehension.pine has ZERO
security calls by design, verify; model fidelity; overfitting language;
fee/turnover math).

## Output contract

- Verbatim audit -> `docs/reviews/tvb13-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value.
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
