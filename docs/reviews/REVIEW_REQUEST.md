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
- Session under review: TVB-30 -- the TVB-29 audit (verdict BLOCK,
  0 CRITICAL / 4 HIGH / 6 MEDIUM / 2 LOW) folded SAME DAY across all
  three repos: every finding reproduced before adjudication (16/16
  no-network probes against the old executor code -> 0/16 after), zero
  disputes, three new dated user rulings 2026-08-28 (reach fail-closed
  `reach_unavailable`; risk drift = receipt + warn at 1.5x budget,
  never auto-close; naked stop = restore once verified, else flatten).
  The round-2 live run was then user-deferred to Monday 2026-08-31
  (scheduling + Friday late-day OPEX pinning). HyPaper assessed for the
  Monday discussion (HANDOFF TVB-30 entry).
- Requested: 2026-08-28
- Write the audit to: `docs/reviews/tvb30-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: tvb8/tvb9 remain unreturned (standing note).

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `aa1c795^..60bc7de` (4 commits, 9 paths: audit recorded aa1c795, fold c2bf6ea, Monday-deferral docs 41a542d, session-end 60bc7de. RANGE-PIN RULE: the caret keeps aa1c795 in the diff; sanity-checked with `git diff --name-status` = 9 paths.) |
| hip3-executor (PRIVATE github.com/sheehyct/hip3-executor; local transport only) | `C:\Strat_Trading_Bot\hip3-executor` | `a23ac43^..a23ac43` (ONE commit = the whole executor fold: dex-aware safety reads, tri-state reconciliation, per-poll protection verification, scanner-independent KILL_FLAT, sizing/exit-identity/reach/provenance fixes, 64-test suite) |
| hip3-scanner (PRIVATE github.com/HIP-3-Solutions/hip3-scanner) | `C:\Strat_Trading_Bot\hip3-scanner` | branch `tvb30-parity-gate` @ `fb1ec84` (PR #6: parity stale-copy preflight + two-pivot nearest-wins vectors; MERGED to `main` 2026-08-30 @ 6a7a53c -- the scoped files are identical at fb1ec84 and the merge) |

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0. Then `docs/reviews/tvb29-codex-audit.md`
   (the BLOCK audit this session folded) and the TVB-30 HANDOFF entry
   (the critical synthesis, including the reproduce-first probe results).
2. hip3-executor: `src/hip3_executor/broker.py` + `engine.py` (the bulk
   of the fold), `rules.py`, README (Ruleset v1 amendments 2026-08-28 +
   the rewritten gate STATUS), `tests/test_gate_hardening.py` (the new
   regression suite) + the updated conftest/test_broker/test_rules.
3. This repo: `analysis/paper/tier_b_t1floor.py`
   (`_resolve_requested_arms` + the independent requested set),
   `analysis/paper/tier_b_exits.py` (full-precision rollup), the new
   tests in `tests/test_t1floor_gates.py` / `tests/test_tier_b_exits.py`.
4. hip3-scanner branch: `parity/extract_core.js` (build()/--check),
   `parity/run_parity.js` (preflight), `test/parity_extract_check.test.js`,
   `test/core_v3.test.js` (two-pivot vectors).

## Focus areas (scrutinize these)

1. Dex-scoping COMPLETENESS: did any venue read escape the sweep?
   `user_fills` notably has NO dex parameter in SDK 0.24.0 and
   `explain_exit` depends on it -- whether builder-dex fills appear
   there is UNVERIFIED (flagged Open; falls back to unknown_exit).
2. The OrderRejected definite-vs-ambiguous split in `_parse_status`:
   is a `status:"err"` response truly always nothing-placed on this
   venue? Any response shape that is definite but classified ambiguous
   (harmless) or ambiguous but classified definite (dangerous)?
3. `_verify_protection`: the restore path re-places at `rec["stop"]`
   for `abs(venue szi)` -- hunt a wrong-size/wrong-price/wrong-side
   hole; also the `entry_block` interplay between the untracked-
   positions writer and the protection writer (string-prefix clearing).
4. `_kill_flat_cycle`: ordering (kill file before feed), the venue_ok
   fallback to tracked records, `clean = zero/zero AND no failed
   closes`, and whether any path can still cancel a survivor's stop.
5. Sizing: ceil-step min-ticket math (float edges), the
   `min_ticket_exceeds_max_notional` guard, risk_usd_booked/stop_venue
   receipt correctness, the 1.5x warn (min-clamp interaction).
6. This repo: is the t1floor produced-vs-requested check truly
   non-circular now (raw-request validation, selector mutation both
   directions)? LOW-1 rollup: full-precision aggregation incl the
   pre-amendment fallback (`realized_fp`/`open_mtm_fp` absent).
7. Scanner: any path that still loads the committed parity copy
   without the byte-compare preflight; the two-pivot vectors' bar
   classifications and pivot qualification (k=2) -- verify by hand.
8. request.security: NO Pine file changed this session -- verify none did.

Standing priorities apply (model fidelity; overfitting language; every
census claim stays characterization; the gate STATUS must not
over-claim -- the equity formula and supervised probes are still open).

## Output contract

- Verbatim audit -> `docs/reviews/tvb30-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value:
  the VPS IP and the master wallet ADDRESS must both stay out of the
  audit (this repo is public -- the address lives only in the private
  hip3-executor repo).
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
