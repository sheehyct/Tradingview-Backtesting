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
- Session under review: TVB-20 -- audit fold-ins (TVB-18 + TVB-19, every
  finding reproduced before adjudication), the layering-arc alignment
  (design-session seed + charter S3.1/S5 amendments + the CLAUDE.md
  "Ablation, not tournament" reword), and the v6.1 CONTROL strategy()
  port: pine/tfc_bf_control_strategy.pine, parity gate PASS (full-span,
  GOOGL/TSLA/DRAM, zero mismatches, break/flip float-exact), and the
  TwinConfig.pine_gate_warmup engine flag.
- SCOPE: standard.
- Requested: 2026-08-08
- Write the audit to: `docs/reviews/tvb20-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: tvb8/tvb9 remain unreturned (standing note).

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `bef6dae^..fffbacb` (5 commits: bef6dae TVB-18 fold-in; 9f11a74 TVB-19 fold-in; bbdb10b layering-arc seed + charter/CLAUDE.md amendments; 2d1f25b CONTROL port + parity gate; fffbacb session-end docs; sanity-checked -- `git diff --name-status bef6dae^..fffbacb` lists all 34 files the session touched) |

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0, then the 2026-08-08 S3.1/S5 amendments.
2. `docs/HANDOFF.md` -- the TVB-20 entry at top (its External Review block
   mirrors this request); the TVB-18/19 blocks for the fold-in context.
3. `docs/experiments/tvb20_design_session_seed.md` (the alignment record)
   and `docs/experiments/tvb20_control_port_parity.md` (conventions +
   results + the Pine gate warm-up finding).
4. `docs/reviews/tvb18-codex-audit.md` + `docs/reviews/tvb19-codex-audit.md`
   (the audits whose fold-ins open this range).
5. `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Focus areas (scrutinize these)

1. ZERO-SEMANTIC-CHANGE claim: diff `pine/tfc_bf_control_strategy.pine`
   against `pine/tfc_bf_watch.pine`. The claim is exactly 4 hunks (contract
   header, strategy() declaration, order-emission block, table title) and
   that the emission block cannot feed back into decisions
   (strategy.position_size never read; at most one order action per bar by
   the machine's same-bar re-entry block).
2. Parity method validity (`analysis/paper/port_parity.py`): the ts-offset
   selection (0/+300/-300 scored on entries), beyond_feed handling (dump
   ends 2026-08-05, trades harvested 2026-08-08), OPEN-trade handling
   (entry-only), the close-fill cross-check, and whether the
   full-span-beats-window argument is sound.
3. `TwinConfig.pine_gate_warmup` isolation: default False must leave
   compare_config and the committed TVB-19 sweep replays bit-identical --
   verify no committed artifact changes when re-run; verify the True path
   matches Pine's ta.valuewhen(timeframe.change) boundary semantics
   (including the first-chart-bar false convention).
4. Decision-exact residual accounting: entry/BF close-fill residuals are
   DECLARED, and no claim anywhere treats TV-reported P&L as twin P&L.
5. Audit fold-in fidelity: `bef6dae` / `9f11a74` against the two audit
   files -- every finding addressed or explicitly deferred with reasons;
   the regenerated sweep artifacts changed ONLY in the declared med fields.
6. No frozen week-1 artifact modified anywhere in the range
   (events_week1.jsonl, scoreboard_week1.md, roster_week1.json).
7. request.security lookahead: the new .pine must add none (it forks v6.1
   verbatim -- verify no un-offset lookahead_on anywhere in the range).
8. Charter amendment coherence: the S3.1/S5 annotations + CLAUDE.md reword
   must not quietly weaken the anti-overfit invariants (per-pattern winner
   promotion must remain forbidden in every formulation).

Standing priorities apply (model fidelity; overfitting language; the
control is a research instrument, never a deployment claim).

## Output contract

- Verbatim audit -> `docs/reviews/tvb20-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value.
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
