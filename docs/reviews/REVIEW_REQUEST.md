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
- Session under review: TVB-29 -- the TVB-28 audit folded (all 8 findings
  reproduced before adjudication, zero disputes), the round-2 design
  session (five dated user rulings 2026-08-26 + drift-scope amendment
  2026-08-28, prereg BEFORE code), scanner continuation near-bank targets
  (PR #1), and the FULL executor pre-live gate implementation with a new
  35-test suite. A NEW HIGH was found and fixed in design exploration:
  the Type-3 invalidation exit was dead code all weekend-1 (int-vs-string
  formingType compare).
- Requested: 2026-08-28
- Write the audit to: `docs/reviews/tvb29-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: tvb8/tvb9 remain unreturned (standing note).

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | {pending push -- pinned after the session-end commit} |
| hip3-executor (PRIVATE github.com/sheehyct/hip3-executor; local transport only) | `C:\Strat_Trading_Bot\hip3-executor` | `7d4fd86^..36d5541` (4 commits: audit-fold corrections 7d4fd86, Ruleset v1 prereg f986716, gate + rules implementation 60d57a7, drift-scope amendment 36d5541) |
| hip3-scanner (PRIVATE github.com/HIP-3-Solutions/hip3-scanner; local transport only) | `C:\Strat_Trading_Bot\hip3-scanner` | branch `tvb29-cont-targets` @ `dccfd06` (PR #1, unmerged at request time -- one commit off `main`) |

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0. Then `docs/reviews/tvb28-codex-audit.md`
   (the audit this session folded) and the TVB-28/TVB-29 HANDOFF entries
   (the critical synthesis + this session's record).
2. This repo: `analysis/paper/engine.py` (executable-only D9,
   floor_armed_inert, first-fill receipt), `tier_b_t1floor.py`
   (_gate_scope + staged promotion), `tier_b_exits.py` (roster net
   algebra), the new tests, and the report/prereg/ARM_LEDGER amendments.
3. hip3-executor: README (Ruleset v1 prereg + amendment + gate STATUS),
   `src/hip3_executor/engine.py` / `broker.py` / `rules.py`, `tests/`
   (35 tests), `deploy/deploy_from_dev.ps1`.
4. hip3-scanner branch: `hip3_strat_screener.html` STRAT-CORE block
   (contTarget), regenerated `src/strat_core.js` +
   `parity/strat_core_extracted.js`, `parity/reference.py`,
   `test/core_v3.test.js`.

## Focus areas (scrutinize these)

1. Executable-only D9 semantics: does the implementation match the ruled
   definition (satisfiable = could actually fire) on every prot path
   (bar-start floor, arm-and-fire, runner breakeven)? Verify the 45
   membership / 13 relabeled / 17 floor_armed_inert split and that event
   streams are truly byte-identical.
2. t1floor `_gate_scope`: does the caller-level produced==requested check
   preserve the TVB-26 LOW-2 protection now that the entry-stream gate
   sees family-scoped maps only? Staged event promotion: can any gate
   failure still leave a partially overwritten canonical dir?
3. Executor entry fail-closed: hunt an exception class or ordering that
   still leaves a venue position unrecorded or unprotected (intent
   persistence, cloid, resting-stop re-query, reconciliation, entry_block).
4. KILL_FLAT: any path that announces success or halts without the fresh
   zero/zero venue proof; the receipt row's durability.
5. Scanner contTarget: correctness vs pivotTarget's k=2 swing semantics
   and the 3-2 fallback; the parity harness's OWN extraction
   (parity/extract_core.js) -- confirm both extractions regenerate from
   the HTML and the harness cannot silently run stale JS again.
6. Sizing math: risk actually booked per ticket under the min/max
   notional clamps + szDecimals flooring; the drift gate scope
   (crypto-only) and reachability gate (missing-ATR pass) vs the prereg
   text.
7. request.security: NO Pine file changed this session -- verify none did.

Standing priorities apply (model fidelity; overfitting language; every
census claim stays characterization; the pre-live gate STATUS section
must not over-claim -- probe steps are still open).

## Output contract

- Verbatim audit -> `docs/reviews/tvb29-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value:
  the VPS IP and the master wallet ADDRESS must both stay out of the
  audit (this repo is public -- the address lives only in the private
  hip3-executor repo).
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
