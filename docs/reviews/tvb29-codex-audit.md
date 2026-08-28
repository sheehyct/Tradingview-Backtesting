<!--
Copy to docs/reviews/tvb{N}-codex-audit.md and fill in.
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-29 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of tradingview-backtesting `ddca002^..7531a12`,
> hip3-executor `7d4fd86^..36d5541`, and hip3-scanner commit `dccfd06`,
> captured 2026-08-28 (TVB-29 post-session). Lightly ASCII-normalized
> (em-dashes -> --, curly quotes -> straight); wording and code otherwise
> unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-29 -- TVB-28 audit fold, Ruleset v1, continuation targets, and executor pre-live gate
- **Reviewed:** PRIMARY `C:\Strat_Trading_Bot\tradingview-backtesting`, `ddca002^..7531a12` (4 commits, 14 paths); SIBLING `C:\Strat_Trading_Bot\hip3-executor`, `7d4fd86^..36d5541` (4 commits, 17 paths); SIBLING `C:\Strat_Trading_Bot\hip3-scanner`, commit `dccfd06` on `tvb29-cont-targets` (5 paths)
- **Reviewer:** Codex CLI (GPT-5)
- **Overall verdict:** BLOCK

## 2. Verbatim audit

The primary-repository fold is largely faithful. Executable-only D9 replays
to 45 `prot+tgt` memberships, the 13 removed labels really are inert floor
armings, all 45 surviving members carry an executed floor or breakeven exit,
the roster-wide inert count is 17, and the affected event streams remain
byte-identical. The T1-floor runner now waits until its gates pass before it
writes event files. The continuation-target implementation also follows the
ruled k=2 pivot ladder and 1.5x stop-distance fallback, with matching current
HTML, worker, parity-copy, and Python-mirror behavior. No Pine file changed.

The executor pre-live gate does not hold. The newly enabled builder-dex order
path is dex-aware while every position/order safety query remains scoped to
the main dex. A deterministic probe therefore obtained a clean zero-position,
zero-order proof while the simulated builder dex still held both. Independent
main-dex probes also showed that an unknown venue query or an unproved close
can clear the persisted entry intent and leave entries unblocked. KILL_FLAT
still depends on the scanner responding before it starts, and it cancels all
orders even when a close failed. Those are live-safety defects in the exact
round-2 scope, not documentation nits or missing performance evidence. The
Friday live run, especially any equity-perp probe, must remain blocked.

### Scope interpretation and validation

The primary and executor ranges resolve to the requested four commits each.
The scanner request was written while `dccfd06` was unmerged; it has since
merged into current `main`, but all five scoped files are unchanged between
`dccfd06` and that merge, so current file:line citations remain valid. Before
writing this audit, the primary worktree contained only the pre-existing
untracked `User_Notes.md`, the executor had no visible change, and the scanner
contained only its pre-existing local settings file. None was read or changed.

Validation performed:

- Primary full suite: 275 passed, 2 skipped. The 68 focused D9, T1-floor,
  fee, and exit tests also passed. A current two-window replay reproduced
  `prot+tgt` 14/16/8/7 and inert 6/5/3/3 across P2/PX July/fresh; regenerated
  P2/PX event files were text- and raw-byte-identical to the committed files.
- Executor suite: 35 passed. Additional in-memory probes covered dex routing,
  query failures, non-filling close responses, ambiguous `BrokerError`,
  min-ticket flooring, and unmatched exit OIDs. No live venue, wallet, VPS,
  or supervised order was exercised.
- Scanner current-descendant suite: 349 passed; the focused core/extraction
  tests passed, and `npm run extract:check` confirmed the worker extraction.
  An independent no-write marker comparison confirmed the parity extraction
  currently matches the HTML exactly. Live-corpus parity was not rerun because
  it requires network calls and scratch artifacts.
- Both sibling pinned diffs pass `git diff --check`. The primary diff check has
  one blank line at EOF in the returned TVB-28 audit, with no source effect.
  The Pine tree is identical at both primary endpoints, so no
  `request.security` surface changed.
- No secret, IP, wallet address, credential, or account value is reproduced in
  this audit.

### Findings, ranked

No CRITICAL finding was assigned. Four HIGH findings block live use.

#### HIGH-1 -- Builder-dex positions and orders are invisible to every safety proof

`LiveBroker` correctly configures builder-dex metadata and order routing
(`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\broker.py:88-101`).
Its safety reads do not carry that scope. Poll caching calls `user_state()` and
`open_orders()` without a dex, stop verification does the same, single-coin
reconciliation uses the default `user_state()`, KILL_FLAT counts only the
default state/orders, and coin/all-order cancellation again reads only the
default orders (`...\broker.py:107-119,162-202,235-241`). The locked SDK is
0.24.0 (`C:\Strat_Trading_Bot\hip3-executor\uv.lock:530-542`); in that API,
these omitted arguments mean the empty-string main dex.

A no-network fake exposed one builder-dex position and one builder-dex order
only when its dex argument was supplied. The production methods made every
query with the empty dex: cached positions were empty, `verify_resting()` was
false, `position_for()` was `None`, and `requery_flat()` returned zero/zero.
That creates two direct safety failures. An equity-perp entry can place a real
position and stop, fail the main-dex stop check, then have reconciliation miss
the position and clear its intent. KILL_FLAT can also journal clean and halt
while builder-dex exposure or orders remain. Existing coverage tests only
metadata merging, not dex-scoped lifecycle operations
(`C:\Strat_Trading_Bot\hip3-executor\tests\test_broker.py:118-130`). The
paper broker is main-dex-only too, while its fake metadata always says every
coin is known, so the dry-run suite cannot reveal this boundary
(`...\broker.py:297-305`; `...\tests\conftest.py:13-24,168-189`).

**Required change:** carry dex identity on every intent and position; query,
verify, cancel, reconcile, and classify in that dex; and aggregate KILL_FLAT's
terminal proof across every configured dex. Add a builder-dex-only position
and order fixture that must prevent a clean receipt and halt.

#### HIGH-2 -- Entry reconciliation clears UNKNOWN and unproved exposure as if it were flat

`position_for()` catches every venue-query exception and maps it to `None`
(`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\broker.py:173-183`).
Startup interprets `None` as confirmed absence, skips order cancellation in
that branch, removes the pending intent, and saves
(`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\engine.py:94-122`).
Runtime reconciliation closes once, calls a cancellation helper that swallows
individual failures, and clears the intent without freshly proving either
zero position or zero orders (`...\engine.py:623-645`;
`...\broker.py:235-241`). `market_close()` itself accepts an OK response with
no fill and returns `px=None` (`...\broker.py:157-160`).

The open path has a second hole. A `BrokerError` from `market_open()` clears
the intent without reconciliation, even though `BrokerError` also represents
response-shape/status failures after the request was sent
(`...\engine.py:519-550`; `...\broker.py:63-69,150-155`). A synthetic broker
that created a position and then raised `BrokerError` left that position live,
with no pending intent and no entry block. Separately, a query exception
returned `None`, and an unproved non-fill close removed the intent with no
block. The client ID is not used to resolve either ambiguity, and `_cloid()`
can silently downgrade it to `None` (`...\engine.py:724-732`). These paths
contradict the fail-closed safety contract
(`C:\Strat_Trading_Bot\hip3-executor\README.md:124-130,161-168,183-188`).

**Required change:** make venue lookup tri-state (present, absent, unknown),
retain the intent and block entries on unknown, distinguish a definite
pre-order rejection from every post-send ambiguity, reconcile by dex and
client ID, verify actual close quantity, cancel relevant siblings, and require
a fresh zero-position/zero-order proof before clearing intent.

#### HIGH-3 -- A tracked position is never rechecked for its required resting stop

Startup blindly hands saved records to `adopt()`, whose live implementation is
a no-op (`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\engine.py:46-48`;
`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\broker.py:243-245`).
Steady-state reconciliation asks only whether a coin name appears in the venue
position map; it does not compare side, size, leverage, or expected stop OID
(`...\engine.py:293-315`). `verify_resting()` is called only during the initial
entry sequence (`...\engine.py:543-548`). A stop canceled manually, rejected
after restart, or removed by another failure can therefore leave a tracked
position naked indefinitely without setting `entry_block`. That contradicts
the current statement that a position is never held without a verified venue
stop (`C:\Strat_Trading_Bot\hip3-executor\README.md:124-130`).

**Required change:** reconcile every tracked record against venue side, size,
and the correctly scoped resting stop at startup and on each poll. Missing or
ambiguous protection must block entries and either restore a verified stop or
flatten under a freshly proved reconciliation.

#### HIGH-4 -- Emergency flatten waits on the scanner and can strip protection after a failed close

`cycle()` fetches scanner state before it checks the local KILL_FLAT file
(`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\engine.py:238-253`). A
scanner outage therefore exits the cycle before emergency flattening begins.
The flatten loop catches and suppresses close exceptions, after which the
caller unconditionally cancels every order (`...\engine.py:253-267,357-376`).
On a failed close that sequence can remove the surviving position's protective
stop. The later proof correctly prevents a main-dex false success, but the
position remains exposed until another cycle, and that retry still depends on
the scanner. The dirty-path test checks only that halt remains false; it does
not preserve or re-establish protection
(`C:\Strat_Trading_Bot\hip3-executor\tests\test_engine.py:177-195`).

**Required change:** inspect KILL_FLAT before any feed dependency, obtain all
needed positions/orders directly from the broker, and do not remove protective
orders from a position whose close is unproved. Retain or restore protection
for every survivor, then halt only after the cross-dex zero/zero receipt.

#### MEDIUM-1 -- Min-ticket flooring and post-fill drift break the ruled sizing contract

The preregistration says risk-normalized tickets are clamped by the venue
minimum and `szDecimals` (`C:\Strat_Trading_Bot\hip3-executor\README.md:77-83`).
The implementation first sets notional to exactly the minimum and then floors
quantity (`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\engine.py:488-505`;
`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\broker.py:53-57`). The
entry check then rejects the now-subminimum ticket
(`...\engine.py:513-517`). A real-step probe turned a nominal 10.00 clamp into
9.52, so this is a systematic skip for many prices, not a theoretical edge.

Sizing is also frozen at scanner mid and the unrounded signal stop, while
actual risk uses the later market fill and venue-rounded stop
(`...\engine.py:513-568`; `...\broker.py:204-233`). There is no post-fill risk
bound, resize, or close, and the entry receipt stores the unrounded stop rather
than the venue stop (`...\engine.py:577-616`). The announced amount can reveal
the drift after the fact, but it does not enforce the budget.

**Required change:** quantize the minimum ticket upward to a valid size step
while preserving the configured maximum, receipt the venue-rounded stop, and
recompute booked risk from actual fill, actual size, and actual resting stop.
Define and enforce the allowed post-fill tolerance or reconcile the entry.

#### MEDIUM-2 -- Exit identity can override an explicitly unmatched closing fill

The fill scan now filters to closing fills after entry and VWAPs fragments for
one OID, which is a real improvement. But if the selected closing fill's OID
matches neither bracket leg, the sibling-survival fallbacks can still label it
as stop or target (`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\broker.py:247-294`).
An in-memory row with an unrelated closing OID and a surviving target leg was
classified as `stop`. Direction, total closed size, multi-OID completion, and
full-position identity are not checked. That violates the gate's instruction
to defer ambiguous classifications (`C:\Strat_Trading_Bot\hip3-executor\README.md:204-206`).

The timestamp regression is weaker than its name: its hard-coded millisecond
value does not match the declared entry timestamp, and it asserts only the
reason, not that the alleged pre-entry price was excluded
(`C:\Strat_Trading_Bot\hip3-executor\tests\test_broker.py:39-40,84-98`).

**Required change:** once an explicit post-entry closing fill is present, do
not override an unmatched OID with survivor heuristics. Validate close
direction and aggregate enough fragments/OIDs to reconcile the position size;
otherwise emit `unknown_exit`. Correct the timestamp fixture and assert the
excluded fill cannot supply either reason or price.

#### MEDIUM-3 -- Missing ATR is an unregistered fail-open exception to the frozen reachability rule

The Ruleset v1 preregistration applies reachability to all targeted entries
(`C:\Strat_Trading_Bot\hip3-executor\README.md:84-89`). The implementation
tests a target only when `atr` is truthy; missing or zero ATR passes with no
reach value (`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\rules.py:198-208`).
The test explicitly pins that pass (`C:\Strat_Trading_Bot\hip3-executor\tests\test_rules.py:69-81`),
and the exception appears in implementation comments rather than a dated user
amendment (`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\config.py:60-63`).
Scanner/executor unit analysis confirmed the units themselves are correct:
both values are percentage points.

**Required change:** fail closed with a distinct `reach_unavailable` reason,
or obtain and record a dated user ruling that explicitly allows unmeasurable
target reach before live use.

#### MEDIUM-4 -- The pre-live STATUS marks three incomplete gate items as implemented

The README says items 1-7 are implemented while separately acknowledging an
open equity verification (`C:\Strat_Trading_Bot\hip3-executor\README.md:170-180`).
Three item-level contracts remain incomplete:

- Leverage verification accepts any dictionary whose top-level status is OK;
  the test says that bare acknowledgement is sufficient, and the position
  persists requested rather than venue-confirmed mode/leverage
  (`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\broker.py:142-149`;
  `...\engine.py:513-566`; `...\tests\test_broker.py:23-34`). This does not
  meet item 4's venue-confirmed contract (`...\README.md:202-203`).
- `account_value()` still uses the unchanged sum that the TVB-27 audit
  independently found inflated non-flat isolated states
  (`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\broker.py:121-140`;
  `docs/reviews/tvb27-codex-audit.md:259-280`). This turn did not access live
  account data, so current venue behavior is NOT VERIFIED; the known formula
  was not replaced.
- Startup obtains `source_sha` only from `git rev-parse`
  (`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\engine.py:68-90`).
  Deployment intentionally ships `git archive`, which has no `.git`, and
  writes the authoritative SHA to `DEPLOYED_SHA`; the engine never reads it
  (`C:\Strat_Trading_Bot\hip3-executor\deploy\deploy_from_dev.ps1:20-40`).
  An archive-only deployment therefore journals no source SHA; a leftover
  parent repository could instead supply stale metadata.

**Required change:** keep the gate status OPEN until each contract is actually
met. Re-query correct-dex venue state to confirm leverage mode/value, replace
or validate the equity field before trusting it, and read/validate the deployed
SHA receipt when `.git` is absent (or embed the immutable SHA in the archive).

#### MEDIUM-5 -- The T1-floor caller's produced-vs-requested check is circular

`main()` filters `NEW_ARMS` using the CLI set, then later reconstructs
`requested` from that already-filtered list
(`analysis/paper/tier_b_t1floor.py:611-614,716-719`). `_gate_scope()` compares
the produced maps to that derived set (`analysis/paper/tier_b_t1floor.py:145-163`).
The check cannot detect the caller/selector regression it claims to guard.
A request containing `D1,ZZ` silently selected only D1 and returned no scope
failure; simulating a selector that produced an extra arm also passed once the
caller derived `requested` from that faulty product.

The new tests inject an unexpected arm while separately holding the expected
set fixed, so they do not exercise the real caller boundary
(`tests/test_t1floor_gates.py:106-139`). The family-scoped stream gate still
catches missing canonical depth arms, but it cannot protect omitted or extra
non-family products after this circular handoff.

**Required change:** preserve and validate the raw declared/CLI request before
selection, reject unknown and duplicate IDs, compare the selected and produced
sets against that independent expectation, and add a main-level selector
mutation regression.

#### MEDIUM-6 -- The scanner parity harness can still certify stale JavaScript

The scoped parity copy is fresh today, but the harness directly requires the
committed `strat_core_extracted.js` and never reads the HTML or invokes its
extractor (`C:\Strat_Trading_Bot\hip3-scanner\parity\run_parity.js:16-29`).
The parity extractor derives the right marker block only when manually run and
has no check mode (`C:\Strat_Trading_Bot\hip3-scanner\parity\extract_core.js:17-24,42`).
The package and automated extraction gate cover the worker copy, not the parity
copy (`C:\Strat_Trading_Bot\hip3-scanner\package.json:7-14`;
`C:\Strat_Trading_Bot\hip3-scanner\test\extract_check.test.js:13-17`).
Therefore a future HTML/reference edit that forgets the second manual
extraction can still produce a false-green JS-vs-Python parity run -- the exact
stale-copy failure the work order asks to exclude.

**Required change:** make `run_parity.js` derive the expected module in memory
and byte-compare it to the committed parity copy before `require()`, fail on
drift, and add an HTML-mutation regression plus a package/CI preflight.

#### LOW-1 -- Roster net algebra still begins from rounded per-symbol gross values

The new roster formula correctly subtracts one roster-rounded fee. Per-symbol
realized and open values, however, are rounded before the rollup, and the
rollup sums those display fields (`analysis/paper/tier_b_exits.py:355-376,439-462`).
A current fresh-P2 replay produced last-digit differences between the shipped
gross/net fields and full-precision event aggregation. The fee itself was
correct and no conclusion changed, but this remains short of D10's aggregate-
then-round contract (`docs/experiments/tvb25_exit_round_prereg.md:308-312`).
The new invariant test uses exact whole-number gross inputs, so it cannot
detect the drift (`tests/test_tier_b_exits.py:46-83`).

**Required change:** carry unrounded realized/open totals into `_rollup_arm()`,
derive gross and net there, then round once. Add fractional per-symbol inputs
whose rounded sum differs from the rounded full-precision sum.

#### LOW-2 -- Continuation-target tests do not pin the word "nearest"

The implementation itself is correct: `pivotTarget()` uses two bars on each
side, requires a pivot beyond the trigger, and picks the closest qualifying
price (`C:\Strat_Trading_Bot\hip3-scanner\hip3_strat_screener.html:537-562,649-684`),
with a matching Python mirror
(`C:\Strat_Trading_Bot\hip3-scanner\parity\reference.py:52-68,99-142`). The
new continuation test contains only one qualifying bullish pivot
(`C:\Strat_Trading_Bot\hip3-scanner\test\core_v3.test.js:76-94`). An in-memory
mutation that chose the first qualifying pivot instead of the nearest passed
the whole core test file.

**Required change:** add bullish and bearish vectors with at least two valid
k=2 pivots beyond the trigger, and assert the price-nearest one wins.

### Confirmed corrections and limits

- Executable-only D9 is implemented consistently across the engine, report,
  preregistration, and arm ledger. The 45/13/17 claims reproduce, every
  surviving `prot+tgt` receipt has an executable protective fill, and event
  behavior did not change (`analysis/paper/engine.py:946-957,1070-1100,1125-1164`;
  `docs/experiments/tvb25_exit_round_report.md:211-240`).
- The collision receipt is now honestly named and documented as a first-fill
  diagnostic, not path-aware alternative pricing. No new claim treats it as a
  full multi-fill counterfactual.
- A gate failure no longer writes T1-floor events before abort. Promotion is
  still a sequence of direct writes rather than an atomic directory swap, and
  the smoke redirect compares raw path strings
  (`analysis/paper/tier_b_t1floor.py:615-619,736-786`). A relative spelling of
  the canonical directory can bypass that redirect; this is an unranked
  robustness issue requiring an explicit output override.
- Scanner continuation targets currently match the ruled pivot/fallback
  semantics in all four continuation branches. Target-distance and scanner ATR
  use compatible percentage units. Crypto-only drift scope, the scanner-shaped
  string Type-3 fix, and the main-dex dirty KILL_FLAT no-success behavior all
  pass their focused tests.
- The ruleset language properly labels its short sample, censuses, and P&L as
  characterization rather than promotion evidence. I found no new
  request.security, lookahead, fee-turnover, or pattern-tournament claim.
- Green suites validate the covered normal paths. They do not validate the
  builder-dex safety boundary, unknown venue states, persistent stop loss,
  scanner-independent emergency handling, or actual live response ordering.

## 3. Actionable items (reviewer's own list, if provided)

1. Make every venue safety operation dex-aware and aggregate KILL_FLAT proof across configured dexs -- **HIGH** -- `hip3-executor/broker.py:88-119,162-202,235-241` -- pin a builder-dex-only position/order fixture before any equity-perp order.
2. Make entry reconciliation tri-state and zero-proofed -- **HIGH** -- `hip3-executor/engine.py:94-122,519-550,623-645,724-732`; `hip3-executor/broker.py:63-69,150-183,235-241` -- retain intent and block on every ambiguous send/query/close/cancel result.
3. Reconcile tracked positions against their expected resting stops at startup and every poll -- **HIGH** -- `hip3-executor/engine.py:46-48,293-315,543-548`; `hip3-executor/broker.py:243-245` -- restore protection or flatten fail-closed.
4. Make KILL_FLAT scanner-independent and preserve protection after failed closes -- **HIGH** -- `hip3-executor/engine.py:238-267,357-376` -- inspect the kill file first and protect every survivor until cross-dex zero/zero is proved.
5. Enforce min-step and actual-fill risk sizing -- **MEDIUM** -- `hip3-executor/engine.py:488-517,543-616`; `hip3-executor/broker.py:53-57,204-233` -- quantize valid minimum tickets and receipt/bound actual booked risk.
6. Defer unmatched or size-ambiguous exit classification -- **MEDIUM** -- `hip3-executor/broker.py:247-294`; `hip3-executor/tests/test_broker.py:39-115` -- validate OID, direction, fragments, time, and closed size.
7. Resolve the missing-ATR reachability contract before live use -- **MEDIUM** -- `hip3-executor/rules.py:198-208`; `hip3-executor/tests/test_rules.py:69-81` -- fail closed or record a dated user amendment.
8. Finish pre-live items 4, 6, and 7 before marking them implemented -- **MEDIUM** -- `hip3-executor/broker.py:121-149`; `hip3-executor/engine.py:68-90,513-566`; `hip3-executor/deploy/deploy_from_dev.ps1:20-40` -- venue-confirm leverage, replace/verify equity, and consume the deployed SHA receipt.
9. Give the T1-floor caller an independent declared/requested arm set -- **MEDIUM** -- `analysis/paper/tier_b_t1floor.py:145-163,611-614,716-719`; `tests/test_t1floor_gates.py:106-139` -- validate raw selectors and mutation-test the real caller.
10. Put the parity-owned extraction behind a mandatory drift preflight -- **MEDIUM** -- `hip3-scanner/parity/run_parity.js:16-29`; `hip3-scanner/parity/extract_core.js:17-24,42` -- compare against HTML before loading the module.
11. Aggregate roster gross/open and fee inputs at full precision before final rounding -- **LOW** -- `analysis/paper/tier_b_exits.py:355-376,439-462`; `tests/test_tier_b_exits.py:46-83`.
12. Pin price-nearest continuation pivots in both directions -- **LOW** -- `hip3-scanner/test/core_v3.test.js:76-94` -- use two valid k=2 candidates per side.
