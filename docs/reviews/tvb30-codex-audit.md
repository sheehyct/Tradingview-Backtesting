<!--
Copy to docs/reviews/tvb{N}-codex-audit.md and fill in.
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-30 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of tradingview-backtesting `aa1c795^..60bc7de`,
> hip3-executor `a23ac43^..a23ac43`, and hip3-scanner commit `fb1ec84`
> (merged unchanged at `6a7a53c`), captured 2026-08-30 (TVB-30
> post-session). Lightly ASCII-normalized (em-dashes -> --, curly quotes ->
> straight); wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-30 -- TVB-29 BLOCK audit fold, Monday live-run deferral, and HyPaper assessment
- **Reviewed:** PRIMARY `C:\Strat_Trading_Bot\tradingview-backtesting`, `aa1c795^..60bc7de` (4 commits, 9 paths); SIBLING `C:\Strat_Trading_Bot\hip3-executor`, `a23ac43^..a23ac43` (1 commit, 9 paths); SIBLING `C:\Strat_Trading_Bot\hip3-scanner`, commit `fb1ec84` (5 paths, merged unchanged at `6a7a53c`)
- **Reviewer:** Codex CLI (GPT-5)
- **Overall verdict:** BLOCK

## 2. Verbatim audit

The TVB-29 fold is not ready for a supervised live run. The dex sweep,
tri-state entry reconciliation, cross-dex zero/zero receipt, exit-fill
identity, reach fail-closed behavior, full-precision roster rollup, parity
preflight, and two-pivot nearest-wins logic are real corrections. They are not
enough to clear the prior BLOCK.

Four independently reproduced HIGH defects remain in the executor. Partial
IOC closes are accepted as complete and can remove both the tracked record and
the survivor's stop. KILL_FLAT can also cancel an untracked survivor's stop
when its initial venue poll fails. The scalar entry-block writers can clear a
block while a persisted entry intent remains unresolved. Finally, the
per-poll protection proof accepts any same-coin/same-OID order without proving
that it is a correctly sized, correctly sided, reduce-only stop at the ruled
price. These are failures in the exact safety boundary the session claims to
have folded, not missing performance evidence or documentation nits.

The primary repository still has one incomplete canonical arm-scope guard and
two reporting/fallback defects. The scanner's production parity preflight and
nearest-pivot implementation are correct today, but its mutation test does not
pin the actual fail-before-load control flow. No Pine file changed, so no
`request.security` surface changed in this range.

### Scope interpretation and validation

The primary range resolves to four commits and nine paths. Current primary
HEAD contains one later docs-only pinning commit outside the requested range;
the scoped Python files are unchanged after `60bc7de`. The executor pinned
commit is current `main`. Scanner `fb1ec84` is the second parent of merge
`6a7a53c`, and all five scoped blobs are byte-identical at the commit and the
merge. All three pinned diffs pass `git diff --check`.

Validation performed:

- Primary focused tests: 46 passed. Primary full suite: 280 passed, 2 skipped.
  Scoped Ruff checks passed. Independent malformed-selector, canonical-arm,
  fee-algebra, non-finite, and mixed-schema probes were also run.
- Executor full no-network suite: 64 passed. Additional in-memory probes
  exercised partial IOC fills, failed venue polling with an untracked
  survivor, block-writer ownership, mutated stop evidence, size tolerances,
  minimum-ticket boundaries, and provenance input. An optional current Ruff
  invocation reported eight SIM/RUF style diagnostics; Ruff is not declared
  as a project dependency, and these style diagnostics do not drive the
  verdict.
- Scanner full Node suite: 354 passed. The focused extraction/pivot tests
  passed 23/23; `parity:check` matched the 15,960-byte committed copy; all
  three worker extraction checks passed. A mutated-HTML harness probe exited
  before core loading and before any network call.
- No live venue, wallet, VPS, account, or secret-bearing endpoint was
  accessed. Scanner live-corpus parity was not rerun because it requires
  network calls and scratch artifacts. Python mirror consistency for the new
  scanner vectors was checked statically because that sibling's configured
  Python interpreter was unavailable.
- Existing unrelated untracked user files and local settings were not read or
  changed. This audit file is the only write.

### Findings, ranked

No CRITICAL finding was assigned. Four HIGH findings keep the live gate
blocked.

#### HIGH-1 -- Partial IOC closes are treated as full closes and can leave a naked, untracked residual

The locked SDK implements `market_close` as a reduce-only IOC order. IOC
cancels whatever portion does not fill, and the response's `totalSz` is the
filled quantity. `LiveBroker.market_close()` checks only that a `filled`
object exists, discards `totalSz`, and returns only the price
(`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\broker.py:218-225`;
SDK pin `C:\Strat_Trading_Bot\hip3-executor\uv.lock:530-542`; official
[exchange endpoint](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint)).

Every close caller then treats any nonzero fragment as complete. KILL_FLAT
cancels the coin's orders and removes its tracked record after that response
(`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\engine.py:479-499`).
The same ordering exists in startup intent reconciliation, protection-loss
flattening, software exits, and entry-failure reconciliation
(`hip3-executor/src/hip3_executor/engine.py:121-127,370-375,397-404,837-843`). A no-network response with
a partial `totalSz` was accepted as success. In the engine probe, a residual
position remained while `failed=[]`, its stop was canceled, and its tracked
record was removed. The next fresh proof can correctly keep a KILL_FLAT
receipt dirty, but that is too late: the survivor is already naked. The added
test covers an entirely unfilled close, not a partial fill
(`C:\Strat_Trading_Bot\hip3-executor\tests\test_gate_hardening.py:139-148`).

**Required change:** retain requested and filled close sizes, classify any
underfill as unresolved, and preserve protection and tracked state until a
fresh dex-scoped query proves zero position. Pin this at every close caller,
especially KILL_FLAT and protection-loss flattening.

#### HIGH-2 -- A failed KILL_FLAT venue poll can cancel an untracked survivor's stop

If KILL_FLAT's initial `pre_poll()` fails, the engine marks venue state
unknown and falls back to names in its tracked state only
(`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\engine.py:446-462`).
It then calls the global `cancel_all_orders(skip=failed)` anyway
(`hip3-executor/src/hip3_executor/engine.py:462-468`). An untracked live position is not in the fallback
name set, so its close is never attempted and its coin is not in `failed`.
The global cancellation sweep consequently removes its protective order
(`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\broker.py:265-279`).

The no-network probe left one position, zero orders, and a correctly dirty
receipt. Thus the zero/zero predicate prevents a false halt, but the position
has become naked. The regression only covers a known coin whose close throws;
it does not cover an unknown position after the poll itself fails
(`C:\Strat_Trading_Bot\hip3-executor\tests\test_gate_hardening.py:325-339`).

**Required change:** when position scope is unknown, never run an unscoped
cancel-all. Cancel orders only for coins freshly proved flat or fully closed;
preserve every other potentially protective order until venue state is known.

#### HIGH-3 -- Prefix-owned entry blocks can clear while a persisted intent remains unresolved

Failed startup reconciliation retains `pending_entry` and sets a scalar
`entry_block` (`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\engine.py:110-144`).
That reconciliation runs only during initialization
(`hip3-executor/src/hip3_executor/engine.py:53-64`). Later, the untracked-position and protection writers
overwrite the same scalar and clear it solely by string prefix
(`hip3-executor/src/hip3_executor/engine.py:307-321,383-387`). Candidate evaluation consults only the
scalar block, not `pending_entry`, and a new entry overwrites the single
pending-intent slot (`hip3-executor/src/hip3_executor/engine.py:552-560,655-667`).

The probe began with an unresolved pending-intent block, let the untracked
writer replace it, then removed the untracked position. The prefix clearer set
`entry_block=None` while `pending_entry` remained present. This reopens new
entries without the required zero-position/zero-order proof and can destroy
the only durable handle for the earlier ambiguous order. The regression pins
only the initial blocked state (`C:\Strat_Trading_Bot\hip3-executor\tests\test_gate_hardening.py:163-179`).

**Required change:** represent block reasons independently, derive the pending
intent block directly from persisted state on every cycle, and retry its
reconciliation until a fresh proof clears both the state and its owned block.
Never allow `_enter()` to replace an existing intent.

#### HIGH-4 -- "Stop resting" verifies only coin and OID, not protective semantics

Both fresh and cached stop predicates accept any open order whose coin and OID
match the record (`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\broker.py:162-168,227-245`).
They do not verify close side, remaining size, trigger/limit price, trigger
type, or reduce-only status. `_verify_protection()` separately compares the
position side and size, but it permits a 0.1% relative size difference and
never joins the expected stop semantics to the actual order row
(`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\engine.py:324-364`).

A same-coin/same-OID row with deliberately wrong side, size, price, type, and
`reduceOnly=False` returned true. A second probe let a recorded size of 1000.0
and venue size of 1000.9 pass without a block, even though an original-size
stop could leave a residual. The existing fakes and tests use coin/OID-only
rows and therefore cannot detect either mutation
(`C:\Strat_Trading_Bot\hip3-executor\tests\test_gate_hardening.py:41-69,238-300`;
`C:\Strat_Trading_Bot\hip3-executor\tests\conftest.py:83-87`). Hyperliquid's
richer open-order response exposes the fields needed for this proof (official
[info endpoint](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint)).

The restore call itself uses current venue size/direction and rerounds the
recorded stop. The defect is that neither steady-state nor post-restore
verification proves that those attributes are what actually rest. This
contradicts the unconditional safety statement at
`C:\Strat_Trading_Bot\hip3-executor\README.md:138-152`.

**Required change:** query a dex-scoped rich order row and verify OID, coin,
close side, exact size-step coverage, stop type, trigger/limit price, and
reduce-only status. Treat missing or unprovable fields as unprotected. Mutation
test each attribute and a one-step size shortfall.

#### MEDIUM-1 -- Minimum-ticket sizing still self-rejects at and just above the boundary

The upward quantization fix runs only when theoretical notional is strictly
below the venue minimum. At or slightly above that boundary, the normal floor
path can reduce the valid theoretical ticket below the minimum; `_enter()`
then rejects it (`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\engine.py:620-639,648-653`).
A probe at mid 105 produced a theoretical notional of exactly 10.00, floored
size 0.09, and actual notional 9.45 with no clamp reason. A theoretical
notional near 10.40 failed the same way, while a raw-below-minimum case
correctly ceiled to 0.10. Tests cover the latter and the coarse-step cap, not
the boundary interval (`C:\Strat_Trading_Bot\hip3-executor\tests\test_gate_hardening.py:351-368`).

**Required change:** quantize the risk-derived ticket, then apply the
ceil-minimum repair whenever the quantized result is below minimum, followed
by the max-notional check. Pin exact-boundary and just-above-boundary vectors.

#### MEDIUM-2 -- Emergency flatten still waits on a scanner timeout before touching the venue

The outer cycle now detects KILL_FLAT before the normal feed path, but
`_kill_flat_cycle()` immediately performs a best-effort scanner request before
its first broker poll or close (`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\engine.py:262-267,428-449`).
The feed timeout is 15 seconds
(`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\feed.py:9-22`). The
new test supplies an immediate exception, so it proves eventual continuation,
not scanner-independent emergency latency
(`C:\Strat_Trading_Bot\hip3-executor\tests\test_gate_hardening.py:307-323`).
This is narrower than TVB-29's abort-on-outage defect, but it still overstates
"before any scanner dependency" at
`C:\Strat_Trading_Bot\hip3-executor\README.md:153-161`.

**Required change:** poll and flatten from the broker first. Omit scanner
state entirely in live KILL_FLAT, or fetch optional mids only after exposure is
proved closed without delaying venue action.

#### MEDIUM-3 -- Post-fill leverage confirmation is fail-open when the confirmation query is unavailable

After entry, a failed `position_for()` query is swallowed. Missing leverage
fields remain `None`, and only a present mismatch is journaled or announced
(`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\engine.py:700-724,745-746`).
The entry therefore continues without a venue-confirmed mode/value and without
an explicit unverified receipt. The test covers a reported cross/magnitude
mismatch, not an absent position, missing fields, or failed query
(`C:\Strat_Trading_Bot\hip3-executor\tests\test_gate_hardening.py:485-500`).
The README appropriately leaves supervised live verification open, but its
fold summary still calls this post-fill confirmation
(`C:\Strat_Trading_Bot\hip3-executor\README.md:200-218,243-244`).

**Required change:** journal and announce `leverage_unverified` on missing or
unknown venue evidence, persist the reason, and decide explicitly whether that
state blocks further entries. Do not call the query a confirmation unless it
returned a valid mode and value.

#### MEDIUM-4 -- The default and malformed T1-floor arm contracts remain circular or multiplicity-blind

`_resolve_requested_arms()` correctly rejects unknown and duplicate nonempty
CLI IDs. It still derives the no-argument expectation from the same mutable
`NEW_ARMS` list that produces the run, treats explicit empty text as the
default-all request, and drops empty comma components
(`analysis/paper/tier_b_t1floor.py:596-615`). Distinct product results are
then keyed by arm ID before the set comparison, erasing declaration/selector
multiplicity (`analysis/paper/tier_b_t1floor.py:699-723`).

Independent probes confirmed that blank/commas-only inputs can resolve to
zero requested and zero produced arms; scope and entry gates then pass and the
smoke path writes empty result artifacts (`analysis/paper/tier_b_t1floor.py:633-645,740-764,803-810`).
Removing canonical non-family arms from `NEW_ARMS` also leaves the default
expectation and produced set equally shrunken, so no gate fails. The new tests
derive their canonical IDs from `NEW_ARMS` and mutate already-built maps; they
do not pin the eight declared IDs, malformed components, or production
multiplicity (`tests/test_t1floor_gates.py:78-101,145-178`).

**Required change:** distinguish absent from explicit-empty input, reject
empty components, declare the unique canonical roster independently of the
selector product, and compare produced ID sequence/cardinality before
dictionary collapse.

#### LOW-1 -- Per-symbol D10 net fields still subtract a rounded fee

`_replay_arm_v25()` computes a full-precision side count, rounds its fee into
the display field, then subtracts that rounded display fee from full-precision
realized/open P&L (`analysis/paper/tier_b_exits.py:336-376`). D10 requires
full-precision arithmetic with rounding only at reporting
(`docs/experiments/tvb25_exit_round_prereg.md:308-312`). An independent scan
found four real fresh-P1 symbol rows where the correct full-precision formula
and current staged-rounding formula differ by 0.0001pp. The roster path is now
correct because it uses an unrounded `fee_fp`, but tests exercise only that
rollup, not per-symbol net construction
(`analysis/paper/tier_b_exits.py:444-473`; `tests/test_tier_b_exits.py:46-112`).

**Required change:** retain the unrounded fee locally, derive every net field
from it, and round only the final reported value. Add a per-symbol fractional
case that distinguishes the two formulas.

#### LOW-2 -- The pre-amendment rollup fallback is not fail-closed

The compatibility path treats missing/null open MTM as zero, permits
non-finite precision values to propagate into non-standard JSON, and uses an
all-or-nothing `fee_sides` decision: one old row forces every new row back to
rounded display fees (`analysis/paper/tier_b_exits.py:444-458`). Probes
confirmed an open row could report `n_open=1` with silently zero MTM, `NaN`
could propagate to output, and one mixed old row changed the aggregate fee's
last digit. Current canonical rows are homogeneous and finite, so this is a
compatibility/failure-detection defect rather than a current roster delta. The
fallback test covers only all-old flat zero rows
(`tests/test_tier_b_exits.py:86-112`).

**Required change:** validate finite numeric inputs, reject an open row without
an MTM value, and apply fee fallback row by row (or reject mixed schema
versions explicitly).

#### LOW-3 -- `DEPLOYED_SHA` presence is mistaken for validated provenance

When no local `.git` exists, any nonempty text in `DEPLOYED_SHA` becomes the
authoritative source SHA; no full-length hexadecimal or archive/commit
validation occurs (`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\engine.py:75-103`).
The regression deliberately uses a short non-commit token and expects it to be
accepted (`C:\Strat_Trading_Bot\hip3-executor\tests\test_gate_hardening.py:472-482`).
This consumes the deployment receipt but does not satisfy TVB-29's
read-and-validate requirement.

**Required change:** require the intended full immutable commit format and
fail provenance closed (or explicitly journal invalid/unavailable) when the
receipt is malformed. Pin malformed, abbreviated, empty, and valid cases.

#### LOW-4 -- The scanner mutation test does not pin fail-before-load behavior

The production path is correct today: `run_parity.js` rebuilds the expected
core, byte-compares it, and exits before requiring the committed copy
(`C:\Strat_Trading_Bot\hip3-scanner\parity\run_parity.js:25-36`). The new
test mutates temporary HTML but asserts only that `build(temp)` differs from
the committed bytes (`C:\Strat_Trading_Bot\hip3-scanner\test\parity_extract_check.test.js:33-42`).
It never executes the loader. Deleting the preflight, moving `require()` above
it, or weakening the exit would therefore leave the committed test green.

An independent harness mutation did exit nonzero before core load or network,
so this is a regression-coverage gap, not a current stale-copy bypass.

**Required change:** execute the actual parity runner against an injected
mismatch and assert nonzero exit before both core loading and network access.

### Confirmed corrections and limits

- Position and order safety reads now sweep every configured dex, and
  `requery_flat()` aggregates a fresh per-dex zero/zero proof
  (`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\broker.py:139-177,247-294`).
- `user_fills` has no dex argument in the locked SDK. Builder-dex visibility
  remains NOT VERIFIED, as the work order states. It affects exit reason/price
  attribution after a position disappears; unmatched or unavailable evidence
  defers to `unknown_exit` rather than driving exposure management
  (`hip3-executor/src/hip3_executor/broker.py:344-408`).
- I found no dangerous ambiguous-as-definite `_parse_status` case in the
  documented response shapes. HTTP failures occur before parsing; malformed
  successful responses remain ambiguous; documented whole-request and
  per-order errors represent refusals (`hip3-executor/src/hip3_executor/broker.py:92-106`). Actual live
  top-level `status:"err"` behavior was not exercised.
- KILL_FLAT's terminal `clean` predicate correctly requires zero positions,
  zero orders, and no recorded failed close (`hip3-executor/src/hip3_executor/engine.py:464-476`). The
  HIGH findings concern what can happen before that truthful receipt.
- Booked risk now uses actual fill, actual size, and the venue-rounded stop;
  the ruled 1.5x risk warning is implemented
  (`hip3-executor/src/hip3_executor/engine.py:725-750,787-820`). Whether `max_notional_usd` is only a
  pre-trade estimate cap or must also bind actual slippage-adjusted fill
  notional remains unstated.
- Missing/zero ATR now fails closed as `reach_unavailable`
  (`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\rules.py:198-211`).
  Explicit closing fills now enforce time, direction, OID, and aggregate size,
  deferring ambiguous attribution (`hip3-executor/src/hip3_executor/broker.py:344-408`).
- The primary raw selector now rejects `D1,ZZ` and `D1,D1`, distinct missing
  and extra result IDs are caught, and the T1-floor smoke redirect uses
  resolved paths (`analysis/paper/tier_b_t1floor.py:596-615,635-640`). The
  roster rollup carries and sums full-precision realized/open values before
  final rounding (`analysis/paper/tier_b_exits.py:377-381,446-473`).
- Scanner parity has no executable committed-copy loader outside
  `run_parity.js`; the preflight is correctly before `require()` today.
  `extract_core.js` implements no-write build and `--check` paths
  (`C:\Strat_Trading_Bot\hip3-scanner\parity\extract_core.js:22-66`).
- The two new scanner vectors are valid k=2 pivots in both directions. Each
  has two qualifying pivots strictly beyond the trigger and selects the
  price-nearest one. A first-qualifying mutation fails both vectors
  (`C:\Strat_Trading_Bot\hip3-scanner\test\core_v3.test.js:96-138`;
  `C:\Strat_Trading_Bot\hip3-scanner\src\strat_core.js:64-82`).
- The README honestly leaves the equity formula and supervised live probes
  open. Green local suites do not validate venue response timing, real order
  modification semantics, builder-dex fill visibility, the equity formula,
  or the first supervised bracket path.
- The primary Pine tree is identical at both pinned endpoints. No new
  `request.security`, lookahead, performance-selection, census-promotion, or
  fee-turnover claim was introduced.

## 3. Actionable items (reviewer's own list, if provided)

1. Require full-close proof before canceling protection or deleting state -- **HIGH** -- `hip3-executor/broker.py:218-225`; `hip3-executor/engine.py:121-127,370-375,397-404,479-499,837-843` -- preserve partial IOC residuals as unresolved until a fresh zero-position query.
2. Preserve all potentially protective orders when the KILL_FLAT position poll fails -- **HIGH** -- `hip3-executor/engine.py:446-468`; `hip3-executor/broker.py:265-279` -- never globally cancel against an unknown position set.
3. Replace scalar/prefix-owned entry blocking with independent durable reasons -- **HIGH** -- `hip3-executor/engine.py:53-64,110-144,307-321,383-387,552-560,655-667` -- derive unresolved-intent blocking from persisted state every cycle.
4. Verify the complete stop contract, not only coin/OID -- **HIGH** -- `hip3-executor/broker.py:162-168,227-245`; `hip3-executor/engine.py:324-364` -- prove side, exact size-step coverage, price, stop type, and reduce-only status.
5. Apply minimum-ticket ceiling after normal quantization too -- **MEDIUM** -- `hip3-executor/engine.py:620-639,648-653` -- cover exact and just-above-minimum raw tickets.
6. Remove the scanner request from the live emergency critical path -- **MEDIUM** -- `hip3-executor/engine.py:262-267,428-449`; `hip3-executor/feed.py:9-22`.
7. Journal and handle unavailable leverage confirmation explicitly -- **MEDIUM** -- `hip3-executor/engine.py:700-724,745-746`.
8. Give the canonical T1-floor arm set an independent, multiplicity-preserving contract -- **MEDIUM** -- `analysis/paper/tier_b_t1floor.py:596-615,699-723,740-810`; `tests/test_t1floor_gates.py:78-101,145-178`.
9. Derive per-symbol D10 nets from unrounded fees -- **LOW** -- `analysis/paper/tier_b_exits.py:336-376`; `docs/experiments/tvb25_exit_round_prereg.md:308-312`.
10. Make the old-record rollup fallback finite, open-aware, and row-wise -- **LOW** -- `analysis/paper/tier_b_exits.py:444-458`.
11. Validate the deployed commit receipt -- **LOW** -- `hip3-executor/engine.py:75-103`; `hip3-executor/tests/test_gate_hardening.py:472-482`.
12. Mutation-test the scanner's actual fail-before-load path -- **LOW** -- `hip3-scanner/parity/run_parity.js:25-36`; `hip3-scanner/test/parity_extract_check.test.js:33-42`.

## Suggested prompt (optional)

Re-review only the repaired TVB-30 live-safety boundary. Require no-network
mutations for partial IOC fills, failed cross-dex polling with an untracked
survivor, concurrent block reasons with a retained pending intent, every stop
attribute, exact/near-minimum sizing, unavailable leverage confirmation, and
KILL_FLAT latency. Do not clear the prior BLOCK from green normal-path suites;
each mutation must preserve protection and durable state until fresh venue
proof closes the uncertainty.
