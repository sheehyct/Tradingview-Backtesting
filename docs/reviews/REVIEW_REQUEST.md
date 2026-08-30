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
- Session under review: TVB-31 -- the TVB-30 audit (verdict BLOCK,
  0 CRITICAL / 4 HIGH / 4 MEDIUM / 4 LOW) folded SAME DAY across all
  three repos: every finding reproduced before adjudication (10/10
  no-network executor probes against the old code -> 0/10 after;
  M4a/M4b/L1/L2 primary probes; L4 static), zero disputes, two new
  dated user rulings 2026-08-30 (leverage-unverified = journal +
  announce, warn-only, never blocks; actual-fill notional = receipt
  every entry + warn past 5% over the cap, never auto-close). Also:
  the scanner Railway checklist item resolved by VERIFICATION (cont
  targets already live; deliberate no-redeploy), and the HyPaper
  adoption spike (docs/experiments/tvb31_hypaper_spike.md -- claims
  checkable against the public github.com/GigabrainGG/HyPaper repo
  @ b054fdd).
- Requested: 2026-08-30
- Write the audit to: `docs/reviews/tvb31-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: tvb8/tvb9 remain unreturned (standing note).

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `0d7437c^..7bfde0f` (4 commits, 10 paths: HyPaper spike 0d7437c, M4/L1/L2 fold + audit + HANDOFF synthesis 371c37d, PR-10 docs f8921f4, session-end 7bfde0f. RANGE-PIN RULE: the caret keeps 0d7437c in the diff; sanity-checked with `git diff --name-status` = 10 paths. The pin commit after 7bfde0f is docs-only, outside the range by construction.) |
| hip3-executor (PRIVATE github.com/sheehyct/hip3-executor; local transport only) | `C:\Strat_Trading_Bot\hip3-executor` | `4e384bb^..4e384bb` (ONE commit = the whole executor fold: proved-close-or-raise, scope-unknown sweep skip, keyed entry blocks + per-cycle intent retry, full stop-contract verification via frontendOpenOrders, boundary sizing, live KILL_FLAT scanner independence, leverage_unverified + notional receipts, DEPLOYED_SHA validation; 90-test suite) |
| hip3-scanner (PRIVATE github.com/HIP-3-Solutions/hip3-scanner) | `C:\Strat_Trading_Bot\hip3-scanner` | branch `tvb31-parity-mutation-test` @ `d0fe9e7` (PR #10: runner-mutation test; MERGED to `main` 2026-08-30 @ `7723462` -- the scoped file is identical at both) |

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0. Then `docs/reviews/tvb30-codex-audit.md`
   (the BLOCK audit this session folded) and the TVB-31 HANDOFF entry
   (the critical synthesis, including the reproduce-first probe results).
2. hip3-executor: `src/hip3_executor/broker.py` (market_close proved
   close, _stop_row_ok / verify_stop / stop_ok_cached, frontendOpenOrders
   _orders_state) + `engine.py` (entry_blocks, _reconcile_pending_intent
   per-cycle, _verify_protection, _kill_flat_cycle, _sized, _enter),
   README (2026-08-30 amendments + rewritten STATUS incl open items e/f),
   `tests/test_gate_hardening.py` (the TVB-30 fold battery).
3. This repo: `analysis/paper/tier_b_t1floor.py`
   (CANONICAL_ARM_IDS + _resolve_requested_arms + the produced-sequence
   multiset gate), `analysis/paper/tier_b_exits.py` (_net_fields + the
   fail-closed row-wise rollup fallback), the new tests in
   `tests/test_t1floor_gates.py` / `tests/test_tier_b_exits.py`,
   `docs/experiments/tvb31_hypaper_spike.md`.
4. hip3-scanner: `test/parity_extract_check.test.js` (the new
   runner-mutation test; the meta-check claim is in the PR body).

## Focus areas (scrutinize these)

1. market_close proved-close: any caller where the fresh position query
   can mislead (same-coin refill race between close and requery, the
   PaperBroker mirror's fidelity, position_for raising vs returning).
2. The KILL_FLAT scope-unknown sweep skip: any path that still cancels
   orders against an unknown position set; the order_sweep receipt
   field; interaction with per-coin cancels inside _flatten_all.
3. Keyed entry blocks: any writer that can still clear another owner's
   key; the per-cycle intent retry (announce throttling, retry cadence
   on a persistently down venue); the _enter pending-intent guard.
4. _stop_row_ok semantics: the "Stop" substring match on orderType, the
   remaining-sz (not origSz) coverage choice, the triggerPx tolerance,
   half-step size coverage, missing-fields-as-unprotected; ALSO the
   engine's half-step size compare and the restore path's stop_venue
   update. Note: venue field VALUES are asserted from SDK docs, flagged
   open (README STATUS item f) pending the supervised probe.
5. requery_flat / cancel_all after the frontendOpenOrders switch: same
   order universe as openOrders? (counts, skip sets, explain_exit oids).
6. _sized restructure: the fixed-notional path now ALSO gets the
   min-repair (behavior change, journaled) -- boundary vectors, the
   max-then-floor-then-repair ordering.
7. This repo M4: multiset gate placement (before dict collapse?),
   CANONICAL literal + NEW_ARMS assertion, absent-vs-explicit-empty.
8. L1/L2: _net_fields round-once; the row-wise fee fallback; the
   DOCUMENTED expected delta on committed per-symbol rows (until the
   month-end regen) -- is it stated everywhere a reader would recompute?
9. HyPaper spike: verify the factual claims against the public repo
   (exchange.ts wallet requirement + trigger validation, info.ts dex
   handling, worker subscriptions, slippage.ts fill model).
10. request.security: NO Pine file changed this session -- verify none did.

Standing priorities apply (model fidelity; overfitting language; every
census claim stays characterization; the gate STATUS must not
over-claim -- the equity formula, stop-row field values, and supervised
probes are still open).

## Output contract

- Verbatim audit -> `docs/reviews/tvb31-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value:
  the VPS IP and the master wallet ADDRESS must both stay out of the
  audit (this repo is public -- the address lives only in the private
  hip3-executor repo).
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
