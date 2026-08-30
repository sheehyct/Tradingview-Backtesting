# HANDOFF -- tradingview-backtesting

> Newest session entry at the TOP. Keep under 1500 lines; archive older entries to
> `docs/session_archive/` when it grows past that.

---

## Session TVB-31 (in progress): scanner deploy verified w/o redeploy; HyPaper spike; TVB-30 audit (BLOCK) folded

**Date:** 2026-08-30
**Status:** IN PROGRESS -- three work blocks done: (1) the scanner Railway
item resolved by VERIFICATION, not deploy; (2) the HyPaper adoption spike
(docs/experiments/tvb31_hypaper_spike.md, 0d7437c); (3) the TVB-30 audit
returned BLOCK and was folded same-day across all three repos.

### Scanner Railway item (startup checklist item 2) -- resolved, no deploy

Cont targets are ALREADY LIVE: the live payload serves cont signals with
targets (xyz:XYZ100 live 2D-1-2D, entry 29580 / stop 29595 / target
29544), live display_v d9cb6247159c52f8 matches local main exactly, and
everything merged since PR #1 (PRs #5/#6) is docs/parity/tests/npm-alias
only. `railway up` deliberately SKIPPED: a no-op redeploy restarts the
worker and resets in-memory alert state the day before go-live.
Verification ticks all green: /health ok (279 coins), payload probe,
SMOKE GREEN vs the live URL, local extract:check + 354/354.

### HyPaper spike (docs/experiments/tvb31_hypaper_spike.md)

Verdict: adoptable for continuous multi-strategy paper on MAIN-DEX
CRYPTO ONLY, not drop-in. (a) zero builder-dex support end to end (meta/
mids/asset-map are main-dex only); (b) three SDK blockers, all small --
/exchange demands a `wallet` field the SDK never sends (400 on every
action; ~30-line shim), trigger orders are DEAD via the API (route
validation rejects non-limit wires while the engine's own trigger path
sits unreachable; ~2-line upstream patch), HTTP-400-on-err reads as
ambiguous BrokerError not OrderRejected; broker.py needs a base_url
config and HyPaper mode must run perp_dexs=[""] (it ignores the dex
param on reads -- our re-prefixing would mint phantom xyz positions);
(c) fills are mid-cross detected but priced by REAL L2-book VWAP with
maker/taker split + 8h live funding -- more realistic than PaperBroker
-- with named optimisms: triggers fire on MID not MARK, maker fills on
touch (no queue), no partials, no liquidation engine. Key value
unchanged: it runs the REAL LiveBroker code path (where HIGH-1 hid) and
per-wallet auto-created accounts = the user's parallel-strategies goal.
Orthogonal to Monday's live run.

### External review fold -- critical synthesis (TVB-30 audit, verdict BLOCK)

The audit returned 2026-08-30: BLOCK, 0 CRITICAL / 4 HIGH / 4 MEDIUM /
4 LOW. All four HIGHs were again executor live-safety defects inside the
boundary TVB-30 claimed folded; the auditor's summary -- "the TVB-29
fold is not ready for a supervised live run" -- was CORRECT. Every
finding REPRODUCED before adjudication: 10 executor no-network probes
10/10 -> 0/10 after the fold, M4a/M4b/L1/L2 primary probes all
reproduced (L1 via the exact formula mechanism on P1-shaped
half-fraction fee_sides; committed rows predate the fp fields), L4
confirmed statically (the mutation test never spawned the runner). ZERO
disputes. Fold commits: executor 4e384bb (pushed, 90 tests, was 64),
this repo (this commit, 287 tests, was 280), scanner PR #10 (branch
tvb31-parity-mutation-test @ d0fe9e7, 356 tests; NEEDS USER MERGE).

Where we agree (everything, with receipts):

- HIGH-1 (partial IOC close read as complete): market_close discarded
  totalSz; every caller deleted the record and cancelled the stop on ANY
  nonzero fill -- a partial left a NAKED UNTRACKED residual (probe: 0.3
  residual, failed_closes=[], stop stripped). Fixed: market_close proves
  flat with a fresh dex-scoped query INSIDE the broker or raises
  (underfilled = unresolved); every caller already handles the raise --
  record kept, stop kept, KILL_FLAT books it failed and retries.
- HIGH-2 (failed poll + cancel-all): with pre_poll down, KILL_FLAT
  flattened tracked names then ran the GLOBAL cancel sweep anyway -- an
  unseen survivor's stop was stripped (probe: GHOST's stop gone). Fixed:
  scope-unknown skips the sweep entirely (receipt order_sweep:
  skipped_scope_unknown); only proved closes lose their orders.
- HIGH-3 (scalar entry_block): the untracked writer's clear erased the
  pending-intent block while state["pending_entry"] persisted (probe:
  block None, intent retained), and _enter could overwrite the only
  durable handle. Fixed: independent keyed blocks (intent / untracked /
  protection), each writer owns exactly its key, the intent block
  re-derives from persisted state EVERY cycle with reconciliation
  retried (announce-throttled), and _enter refuses while an intent
  exists (pending_intent_unresolved).
- HIGH-4 (coin/oid-only stop proof): a same-coin/oid row with wrong
  side, size, price, type, and reduceOnly=False verified as protection
  (probe: True); 1000.0-vs-1000.9 passed the 0.1% size tolerance. Fixed:
  _orders_state moved to frontendOpenOrders (rich rows, dex param
  intact) and the predicate proves the FULL contract -- reduce-only,
  isTrigger, "Stop" orderType, close side, remaining-size coverage to
  half a size step, venue-rounded trigger price; missing fields read
  UNPROTECTED; mutation-tested per attribute; the engine size compare is
  half a step (was 0.1% relative); restore updates stop_venue and
  re-proves the contract fresh. Venue field VALUES asserted from SDK
  docs -- confirm against a real resting bracket in the supervised probe
  (added to README STATUS open list).
- M1 (boundary sizing): exactly-$10.00 and $10.40 tickets floored to
  $9.45 and self-rejected (probe digit-for-digit). Fixed: quantize
  first, ceil-repair ANY under-minimum result, cap guard unchanged.
- M2 (kill-flat scanner touch): live KILL_FLAT fetched scanner state
  (15s timeout exposure) before the broker. Fixed: LIVE never touches
  the scanner (the live broker ignores mids); the paper twin keeps the
  best-effort fetch for its fills.
- M3 + USER RULING 2026-08-30 (warn-only): a failed/incomplete leverage
  confirmation was swallowed silently. Fixed: leverage_unverified
  journal + announce with the reason (query_failed /
  position_not_visible / leverage_fields_missing); entries NEVER block
  on it (risk is set by the stop; matches the risk-drift ruling shape).
- NEW USER RULING 2026-08-30 (the audit's unstated question): the
  max-notional cap binds the PRE-TRADE estimate; the ACTUAL fill
  notional rides every entry receipt (notional_usd_filled) and warns
  past 5% over the cap -- never auto-closed.
- M4 (this repo, t1floor): blank/commas-only --arms resolved to ZERO
  arms with every gate passing vacuously; the default expectation
  tracked a mutated NEW_ARMS; dict-keying erased production
  multiplicity. Fixed: CANONICAL_ARM_IDS literal + NEW_ARMS assertion,
  absent-vs-explicit-empty distinction (empty components hard-error),
  produced-sequence multiset gate before any dict collapse; tests pin
  the eight ids literally.
- L1 (this repo): per-symbol nets subtracted the ROUNDED display fee
  from full-precision P&L (0.0001pp drift on P1 half-fraction rows).
  Fixed: _net_fields helper -- every net derives from the unrounded fee,
  rounds once; regression distinguishes the two formulas exactly.
  EXPECTED DELTA: committed results_by_symbol rows keep the staged
  values until the month-end regen re-pins them (same treatment as the
  TVB-30 LOW-1 rollup delta).
- L2 (this repo): rollup fallback silently zeroed an open row's missing
  MTM, propagated NaN into JSON, and one old row flipped EVERY row to
  rounded display fees. Fixed: fail-closed finiteness validation, open
  rows REQUIRE an MTM value, row-wise fee fallback.
- L3 (executor): any nonempty DEPLOYED_SHA text became provenance.
  Fixed: 40-hex or journaled deployed_sha_invalid; four vectors pinned.
- L4 (scanner): the parity mutation test re-implemented the comparison
  inline and never executed run_parity.js -- deleting the preflight left
  every test green. Fixed (PR #10): the new test spawns the ACTUAL
  runner against a poisoned tmp replica, asserts exit 1 + STALE message
  + the poison never executed; META-CHECKED (deleting the preflight
  fails exactly this test).

New dated user rulings this session (2026-08-30): (1) leverage
unverified = journal + announce, warn-only, never blocks entries;
(2) actual-fill notional = receipt every entry + warn past 5% over the
cap, never auto-close.

Suites after the fold: executor 90 (was 64), this repo 287 (was 280),
scanner 356 (PR #10). request.security untouched (no Pine changed --
audit confirmed independently).

### Context for next session

- Go-live checklist unchanged for Monday: executor VPS deploy now at
  4e384bb+ (SSH needs explicit user go), VPS dry-run + KILL_FLAT drill,
  supervised probes (bracket receipt + STOP-CONTRACT field confirmation
  vs a real resting bracket / equity formula with ONE isolated position
  -- STILL UNVERIFIED / first xyz fill + user_fills dex question).
- Scanner PR #10 MERGED (user, 2026-08-30 @ 7723462; test-only, runtime
  untouched -- no Railway deploy needed). The whole TVB-30 fold is now
  on main in all three repos.
- Month-end regen ~Sep 1 now ALSO re-pins the per-symbol L1 net fields
  (net_realized_pp/net_combined_pp staged-vs-round-once, 0.0001pp class)
  alongside the TVB-28/TVB-30 deltas already documented.
- HyPaper adoption decision pending the Monday discussion; the spike doc
  is the input.

---

## Session TVB-30: TVB-29 audit (BLOCK) folded before go-live; run deferred to Monday (COMPLETE)

**Date:** 2026-08-28
**Status:** COMPLETE -- the TVB-29 audit (verdict BLOCK, 4 HIGH executor
live-safety) folded same-day across all three repos, every finding
reproduced first, zero disputes, three new dated rulings; the round-2
live run was then USER-DEFERRED to Monday 2026-08-31 (scheduling +
Friday late-day OPEX pinning); HyPaper assessed for the Monday
discussion.

### External review fold -- critical synthesis (TVB-29 audit, verdict BLOCK)

The audit returned 2026-08-28: BLOCK, 0 CRITICAL / 4 HIGH / 6 MEDIUM /
2 LOW. All four HIGHs were hip3-executor live-safety defects inside the
exact round-2 scope; the auditor's own summary -- "the executor pre-live
gate does not hold" -- was CORRECT, and the 2026-08-26 "items 1-7
IMPLEMENTED" claim was over-stated. Every finding was REPRODUCED before
adjudication (16/16 no-network probes against the old code; 0/16
reproduce after the fold). ZERO disputes. Fold commits: executor
a23ac43 (pushed), this repo (this commit), scanner PR #6 (branch
tvb30-parity-gate @ fb1ec84).

Where we agree (everything, with receipts):

- HIGH-1 (dex-blind safety reads): SDK 0.24.0's user_state/open_orders
  take dex="" = MAIN dex only, while the order path was perp_dexs-aware
  -- writes succeeded into a universe the reads could not see. Probe:
  a fake venue holding an xyz:TSLA position + resting order yielded a
  clean {positions:0, open_orders:0} KILL_FLAT proof. Fixed: every
  venue read sweeps every configured dex (coin-name prefix = dex
  identity), requery_flat proves zero/zero ACROSS dexs with a by_dex
  breakdown, and a builder-dex-only exposure fixture pins that a clean
  receipt is impossible.
- HIGH-2 (unknown read as flat): position_for mapped ANY query
  exception to None = "confirmed absent"; startup then cleared the
  intent while a real position sat live (probe H2b); a BrokerError
  after a sent order cleared the intent with the position live (H2c);
  market_close accepted an unfilled close (H2d/H2e). Fixed: tri-state
  lookup (present / absent / raises), OrderRejected = the ONLY
  definite-rejection class that skips reconciliation, unfilled closes
  raise, and intents clear only after a fresh zero-position zero-order
  proof. Live cloid downgrade is journaled.
- HIGH-3 (no post-entry stop verification): verify_resting was called
  exactly once, in the entry sequence; a stop canceled/rejected later
  left the position naked indefinitely (probe H3b: no reaction). Fixed
  + USER-RULED 2026-08-28 (restore, else flatten): every poll rechecks
  venue side/size vs the record and the stop's presence in the cached
  cross-dex order set; a missing stop is re-placed once and verified
  fresh, else the position is closed (protection_lost); mismatch or an
  unclosable naked position blocks entries.
- HIGH-4 (KILL_FLAT gaps): the kill file was checked AFTER feed.state()
  -- a scanner outage aborted the cycle before flattening (probe H4a);
  a failed close was followed by an unconditional cancel-all that
  stripped the survivor's stop (H4b). Fixed: kill honored before any
  feed dependency (mids best-effort), failed closes KEEP their coin's
  protective orders (cancel_all skip set + failed_closes in the
  receipt), clean requires no failed closes.
- M1 (sizing): the $10 min-clamp floored its own size back under $10
  (probe: $9.45 at mid 105 -> self-reject below_min_notional) -- a
  systematic skip, exactly as the audit said. Fixed + USER-RULED
  2026-08-28 (receipt + warn): min tickets ceil to a valid size step,
  one-step-over-cap refused min_ticket_exceeds_max_notional, entries
  receipt stop_venue + risk_usd_booked (actual fill x actual size x
  venue-rounded stop), RISK DRIFT alert past 1.5x budget, never
  auto-close.
- M2 (exit identity): an unmatched closing-fill OID was relabeled
  "stop" by the survivor heuristic (probe reproduced). Fixed: an
  explicit closing fill classifies by OID alone; unmatched, partial
  (size-unreconciled), or wrong-direction fills defer to unknown_exit;
  survivor heuristics only when no fill is visible. The audit also
  caught our test fixture: ENTRY_MS sat TWO DAYS after ENTRY_TS, so the
  pre-entry exclusion test never tested the exclusion -- now derived
  from ENTRY_TS, and the pre-entry fill carries the sl_oid so a filter
  regression would visibly misclassify.
- M3 (reach fail-open): missing ATR silently passed the reachability
  gate; the exception lived in code comments, never a dated ruling.
  USER-RULED 2026-08-28: fail closed, reason reach_unavailable
  (targetless entries untouched). Prereg amendment recorded in the
  executor README.
- M4 (gate status over-claim): leverage was "verified" by a bare
  status:ok; account_value keeps the TVB-27-flagged sum; source_sha
  came only from rev-parse (an archive deploy journals a PARENT repo's
  HEAD). Fixed: post-fill venue leverage confirmation (mismatch
  journaled + announced, venue values persisted), rev-parse trusted
  only when ROOT/.git exists with DEPLOYED_SHA consumed otherwise, and
  the README STATUS rewritten to say what is STILL OPEN -- the equity
  formula is UNCHANGED and UNVERIFIED until the supervised
  one-isolated-position probe.
- M5 (this repo, t1floor): the produced-vs-requested check was
  CIRCULAR -- `requested` was re-derived from the already-filtered arm
  list, so "--arms D1,ZZ" silently selected D1 and passed. Fixed:
  _resolve_requested_arms validates the RAW CLI request (unknown /
  duplicate ids are hard errors) and the scope gate compares against
  that independent expectation; selector-mutation regressions added
  both directions; the smoke redirect now compares resolved paths.
- M6 (scanner): the parity harness require()d its committed extraction
  blind -- the exact stale-copy failure TVB-29 said to exclude.
  Fixed: run_parity.js derives the expected module from the HTML in
  memory and byte-compares BEFORE loading (proved end-to-end: a
  mutated copy exits 1 before any network call); extract_core.js gains
  build() + --check; npm run parity:check; HTML-mutation test pinned.
- LOW-1 (this repo): roster rollups summed 4dp-rounded per-symbol
  display fields. Fixed: full-precision realized_fp/open_mtm_fp ride
  every rec, the rollup aggregates those and rounds ONCE (D10 holds
  end to end), with a fallback for pre-amendment recs; a fractional
  three-symbol vector (0.12344 x3 -> 0.3703 not 0.3702) pins it. The
  committed round artifacts keep their last-digit drift until the
  month-end regen re-pins them (documented expected delta).
- LOW-2 (scanner): the single-pivot cont vector could not catch a
  first-qualifying scan-order mutation; two-pivot vectors both
  directions now assert the price-NEAREST pivot wins.

New dated user rulings this session (2026-08-28, recorded in the
executor README prereg amendments): (1) reach fail-closed
(reach_unavailable); (2) risk drift = receipt + warn at 1.5x budget,
never auto-close; (3) naked stop = restore once verified, else flatten,
entries blocked while unprotected.

Suites after the fold: executor 64 (was 35), this repo 280 (was 275),
scanner 354 (was 349). request.security untouched (no Pine changed --
audit confirmed independently).

### Context for next session

- The go-live checklist (.session_startup_prompt.md) remains the
  contract, now unblocked by the fold: scanner PR #6 merge + railway
  deploy, executor VPS deploy (a23ac43+), VPS dry-run + KILL_FLAT
  drill, supervised probes (bracket / equity formula with ONE isolated
  position -- still the open half of gate item 6 / first xyz fill),
  manual KILL_FLAT at 18:00 ET.
- Builder-dex coin naming in dex-scoped venue responses is normalized
  defensively (re-prefixed if bare) but the first xyz probe should
  confirm the venue's actual naming.
- Month-end regen ~Sep 1 now ALSO re-pins the LOW-1 full-precision
  rollup fields alongside the TVB-28 deltas already documented.

### HyPaper assessment (user-raised 2026-08-28, for the Monday discussion)

github.com/GigabrainGG/HyPaper (MIT, Node/TS + Redis, ~29 stars /
17 commits -- young): a drop-in paper-trading twin of the HL API --
swap the base URL, add a wallet field, no signing; a worker fills paper
orders on every live WS mid tick with maker/taker fees at live rates,
8h funding from live rates, GTC/IOC/ALO, cancel-by-cloid,
updateLeverage; /info mirrors HL (paper user-state + proxied live
market data). Why it is interesting HERE: our dry-run exercises
PaperBroker, a parallel twin -- the TVB-29 audit itself noted the
dry-run can never reveal LiveBroker defects (HIGH-1 hid exactly there).
Pointing LiveBroker at HyPaper would run the REAL, just-hardened code
path (dex-scoped reads, tri-state reconcile, resting-stop verify,
KILL_FLAT proofs) continuously against a simulated venue; multiple
wallets = multiple strategies on one ticker. Open questions before any
adoption (a spike, not a rewrite): (1) builder-dex support -- does it
serve xyz:* assets and dex-scoped user_state/open_orders/meta, the
exact seam we just fixed; (2) SDK compatibility -- the Python SDK signs
actions, HyPaper wants unsigned JSON + wallet field; (3) fill realism
is mid-cross (optimistic vs spread/queue) -- still better than our
poll-cadence mid fills with no fees/funding; (4) new infra (Redis +
Node service). Neighbors seen: chainstacklabs/hyperliquid-trading-bot
(grid bot + SDK examples, not a paper venue), horn111/hip4-mm-simulator
(HIP-4 MM queue modeling, different problem).

### Files created/modified

- hip3-executor (a23ac43, pushed): broker.py (dex_of/_dex_name, dex-swept
  pre_poll/verify_resting/position_for/open_orders_for/cancel sweeps/
  requery_flat by_dex, OrderRejected + _parse_status classification,
  market_close raises on unfilled, stop_resting_cached, place_bracket
  sl_px, OID-only explain_exit), engine.py (_kill_flat_cycle,
  _flatten_all failed-set, _verify_protection, tri-state intent
  reconciliations, OrderRejected split, ceil-step _sized, risk receipt +
  warn, post-fill leverage confirm, DEPLOYED_SHA provenance), rules.py
  (reach_unavailable), config.py comment, README (amendments + honest
  STATUS), tests/ (conftest, test_broker, test_rules,
  test_gate_hardening NEW; 64 total).
- hip3-scanner (PR #6, branch tvb30-parity-gate @ fb1ec84): parity/
  extract_core.js (build() + --check), parity/run_parity.js (in-memory
  byte-compare preflight), package.json (parity:extract/parity:check),
  test/parity_extract_check.test.js NEW, test/core_v3.test.js
  (two-pivot nearest-wins vectors); 354 tests.
- This repo (aa1c795, c2bf6ea, 41a542d + session-end): tier_b_t1floor.py
  (_resolve_requested_arms + independent requested set + resolved-path
  smoke redirect), tier_b_exits.py (realized_fp/open_mtm_fp +
  aggregate-then-round rollup), tests (t1floor M5 regressions, exits
  fractional-precision vectors; 280 total), audit recorded, HANDOFF
  synthesis + HyPaper assessment, startup prompt, archive
  HANDOFF_TVB22-TVB23.md.

### Open

- [ ] MONDAY 2026-08-31: discussion (HyPaper adoption + parallel
      strategy comparison shape), then the go-live checklist
      (.session_startup_prompt.md) -- scanner PR #6 merge + railway
      deploy first
- [ ] HyPaper spike decision (xyz-dex + SDK-compat probe before any
      adoption; assessment above; user goal: multiple parallel
      strategies on the same tickers, results compared)
- [ ] user_fills has NO dex parameter in SDK 0.24.0 -- whether
      builder-dex fills appear in it is UNVERIFIED; exit classification
      falls back to unknown_exit if not, but confirm on the first xyz
      fill
- [ ] Month-end fresh-window regen ~Sep 1 (adds LOW-1 fp re-pin)
- [ ] Carried: TV mirror on demand; TVB-18 repairs; jackson set_inputs
      fix; tvb8/tvb9 unreturned

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb30-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: REQUESTED
- Commits to review: this repo `aa1c795^..60bc7de` on `main` (4 commits,
  9 paths: audit recorded aa1c795, fold c2bf6ea, Monday-deferral docs
  41a542d, session-end 60bc7de; caret keeps aa1c795 in the diff,
  sanity-checked via `git diff --name-status`). Sibling hip3-executor
  (PRIVATE, local path C:\Strat_Trading_Bot\hip3-executor):
  `a23ac43^..a23ac43` (one commit, the whole executor fold). Sibling
  hip3-scanner (PRIVATE, HIP-3-Solutions org): branch `tvb30-parity-gate`
  @ `fb1ec84` (PR #6; merged to main 2026-08-30 @ 6a7a53c, scoped files
  identical).
- Scope / what changed: the TVB-29 BLOCK audit folded in full (4 HIGH +
  6 MEDIUM + 2 LOW, all reproduced first via 16 no-network probes);
  three new dated user rulings 2026-08-28 (reach fail-closed, risk
  receipt+warn 1.5x, stop restore-else-flatten); live run deferred to
  Monday; HyPaper assessed.
- Focus areas (scrutinize these): (1) dex-scoping COMPLETENESS -- did
  any venue read escape the sweep? user_fills notably has NO dex param
  in SDK 0.24.0 (explain_exit depends on it; flagged Open); (2) the
  OrderRejected definite-vs-ambiguous split in _parse_status -- is
  status:"err" truly always nothing-placed on this venue?; (3)
  _verify_protection: restore path re-places at rec["stop"] for
  abs(venue szi) -- any wrong-size/wrong-price hole, and the
  entry_block interplay between the untracked/protection writers; (4)
  _kill_flat_cycle ordering incl the venue_ok fallback to tracked
  records and the clean = zero/zero AND no-failed-closes rule; (5)
  ceil-step sizing math and the risk receipt/warn (min-clamp
  interaction); (6) t1floor _resolve_requested_arms + the independent
  requested set -- truly non-circular now?; LOW-1 fp rollup incl the
  pre-amendment fallback; (7) scanner parity preflight -- any path that
  still loads the committed copy without the byte-compare; the
  two-pivot vectors' correctness; (8) request.security: NO Pine changed
  -- verify.
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb30-codex-audit.md exists)

---

## Session TVB-29: TVB-28 audit folded + round-2 design session + pre-live gate LANDED (COMPLETE)

**Date:** 2026-08-26..28
**Status:** COMPLETE -- the TVB-28 audit folded same-day (all 8 findings
reproduced first, zero disputes), the round-2 design session produced five
dated user rulings + a prereg BEFORE code, and the entire executor
pre-live gate + rule changes landed with a new 35-test suite. Round-2
live test (Fri 08-28, ~$100, crypto + xyz equity perps to 18:00 ET) is
staged for TVB-30.

### What was accomplished

- TVB-28 AUDIT FOLD (this repo ddca002/7b4ae6a/3fb0631; executor
  7d4fd86): critical synthesis in the TVB-28 External Review block below.
  Highlights: D9 executable-only USER RULING (membership 58 -> 45, the 13
  inert armings ride floor_armed_inert; events byte-identical); receipt
  relabeled FIRST-FILL diagnostic (delta_vs_first_fill_pct); t1floor
  _gate_scope caller contract + staged event promotion + smoke redirect
  (the canonical 8-arm CLI had been failing its own hardened gate);
  round-once roster net algebra + invariant test; executor census medians
  corrected (statistics.median, 9v18/6v20 denominators, decision-clock
  membership, STX exemption), backing-target counterfactual IMPLEMENTED
  + receipted (7/7 stop-first stands; 6/7-within-0.2pp corrected to 4/7),
  MMQB language pass, README INTENDED-vs-CURRENT + gate items restored.
- ROUND-2 DESIGN SESSION (plan mode, trader-terms questions anchored on
  real weekend trades -- STX cont walkthrough, MOVE/CHIP vs kFLOKI):
  five dated USER RULINGS 2026-08-26 prereg'd BEFORE code (executor
  f986716 "Ruleset v1"): (1) cont targets = pivot-ladder near bank,
  scanner-side; (2) symmetric stand-aside vs BTC daily-open sign; (3)
  risk-normalized $0.50/trade (min $10 / max $100 notional clamps); (4)
  reachability 1.5x daily ATR, all targeted entries (stated consequence:
  conts fall under the rr floor once targeted); (5) universe = crypto +
  xyz during underlying RTH. AMENDMENT 2026-08-28 (user-ruled): drift
  veto scoped to main-dex crypto -- BTC's color never vetoes an equity
  perp (36d5541). User flags recorded in the prereg: short window = weak
  evidence; -6.85 vs $50 budget = refinements not repairs; STRAT-vs-algo
  boundary answered in writing.
- SCANNER CONT TARGETS (hip3-scanner PR #1, branch tvb29-cont-targets @
  dccfd06 -- the repo moved to the HIP-3-Solutions org, main is PR-only
  now): contTarget() in the HTML STRAT-CORE block wires the existing
  pivotTarget() into the cont branches (3-2 measured-move fallback);
  extract:check OK, 346/346 node tests, Python parity mirror updated,
  parity harness 125 live pairs + 12 aggregations ZERO mismatches
  (NOTE: the parity harness keeps its OWN extraction -- regenerate
  parity/extract_core.js too or parity lies), bar-level hand checks
  (TSLA 352.02 pivot / MSFT 487.19 / NVDA fallback).
- PRE-LIVE GATE LANDED (executor 60d57a7, all 7 items + tests): entry
  fail-closed (persisted intent + cloid before any order, resting-stop
  re-query, ANY-exception reconciliation, entry_block on untracked
  positions/failed reconcile, startup intent reconciliation); KILL_FLAT
  venue-authoritative union flatten + cancel-all + durable zero/zero
  kill_flat_receipt (dirty result never announces success); NEW HIGH
  found in design exploration: the Type-3 invalidation exit was DEAD
  CODE all weekend-1 (engine compared formingType == 3 int vs the
  scanner's string "3") -- fixed + pinned; leverage response verified;
  exit identity (closing-fills-after-entry, VWAP by oid, tp_oid-None
  guard); P/L rebuild-then-append double-count fixed; provenance
  (startup journals source SHA + config + uv.lock hashes; lock now
  committed; deploy script archives git HEAD only, refuses dirty trees).
  Rule changes wired: risk sizing, drift gate, reachability gate, xyz
  RTH clock gate + SDK perp_dexs routing (incl "" main dex -- verified
  live that meta(dex="xyz") serves prefixed names). 35-test pytest suite
  (fake broker, payload fixtures, no network); local dry-run poll
  verified against the live scanner (880 keys baselined, provenance row).
- Memory: new standing feedback memory (trader-visualization gap: design
  questions in trader terms + bar-by-bar walkthroughs are the
  verification tool).

### Context for next session

- TVB-30 = the Friday live run. Go-live checklist is in
  .session_startup_prompt.md: scanner PR merge + railway deploy FIRST
  (cont targets don't exist live until then), executor VPS deploy (new
  git-archive script; SSH needs explicit user go), VPS dry-run + KILL_FLAT
  drill, deliberate rm data/KILL_FLAT, supervised probes (bracket /
  equity formula with one isolated position / first xyz fill), manual
  KILL_FLAT ~18:00 ET. Agent wallet ACTIVE (user confirmed 08-28).
- Month-end regen ~Sep 1 re-pins rollups with MORE than fee fields:
  corrected collision census (P2 14/9, PX 21/10, prot+tgt 45) +
  collision_receipts + fee_sides + net-from-roster-fee algebra. All
  deltas documented in the report amendments.
- User_Notes.md stays untracked.

### Files created/modified

- This repo: analysis/paper/engine.py (executable-only D9 +
  floor_armed_inert + first-fill receipt), tier_b_t1floor.py
  (_gate_scope + staged promotion + smoke redirect), tier_b_exits.py
  (roster net algebra + fee_sides), tests (+5 = 275), report/prereg/
  ARM_LEDGER amendments, .gitignore (smoke dirs), audit committed,
  HANDOFF synthesis, session docs.
- hip3-executor: README (Ruleset v1 prereg + amendment + gate STATUS +
  safety model), config.json/config.py (5 new fields), engine.py,
  broker.py, rules.py, deploy/deploy_from_dev.ps1, tests/ (NEW, 35),
  uv.lock committed, analysis/weekend1.py + ANALYSIS.md + analysis.json
  (audit fold regen).
- hip3-scanner: hip3_strat_screener.html STRAT-CORE + regenerated
  src/strat_core.js + parity/strat_core_extracted.js +
  parity/reference.py + test/core_v3.test.js (branch tvb29-cont-targets,
  PR #1).

### Open

- [ ] TVB-30: run the Friday round-2 live test per the go-live checklist
      (scanner PR merge + deploy, executor VPS deploy, dry-run + drill,
      probes, 18:00 ET KILL_FLAT)
- [ ] Month-end fresh-window regen ~Sep 1 (re-pins collision census +
      receipts + fee algebra; expected deltas documented)
- [ ] TVB-29 review fold when returned (incl the drift-scope amendment
      and the gate implementation)
- [ ] Equity-side drift reference: deliberately unchosen (future a-priori
      design decision)
- [ ] Runner profiles past T1: future prereg lane
- [ ] Carried: TV mirror per arm on demand; TVB-18 repairs bundle; M+T
      PMG+ nudge; jackson set_inputs fix; tvb8/tvb9 unreturned

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb29-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED (2026-08-28, verdict BLOCK: 0C/4H/6M/2L; folded in
  TVB-30 -- critical synthesis in the TVB-30 entry)
- Commits to review: this repo `ddca002^..7531a12` on `main` (4 commits,
  14 paths; caret keeps ddca002 in the diff; sanity-checked via
  `git diff --name-status`; the pin commit after 7531a12 is routing,
  out of range). Sibling hip3-executor (PRIVATE, local path
  C:\Strat_Trading_Bot\hip3-executor): `7d4fd86^..36d5541` (audit fold,
  Ruleset v1 prereg, gate + rules, drift amendment). Sibling
  hip3-scanner (PRIVATE, HIP-3-Solutions org): branch
  `tvb29-cont-targets` @ `dccfd06` (PR #1).
- Scope / what changed: TVB-28 audit fold (both repos), Ruleset v1 prereg
  + five rulings + drift amendment, scanner cont targets (PR #1), the
  full pre-live gate implementation + 35-test suite.
- Focus areas (scrutinize these): (1) executable-only D9 semantics vs the
  ruled definition (satisfiable = could fire; the 45/13/17 split); (2)
  the t1floor _gate_scope contract -- does the caller-level exact-set
  check truly preserve LOW-2's protection; (3) entry fail-closed paths
  (any exception class that still escapes?); (4) KILL_FLAT receipt --
  can any path announce success without the fresh zero/zero proof; (5)
  scanner contTarget correctness vs pivotTarget semantics + the parity
  harness's own extraction; (6) sizing clamp math (min/max notional,
  risk actually booked); (7) request.security: no Pine changed -- verify.
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb29-codex-audit.md exists)

---

## Session TVB-28: Weekend-1 analysis + BOTH audits folded + D9 re-ruling (COMPLETE)

**Date:** 2026-08-24..26 (spans the /clear on 08-24; audit returned 08-25)
**Status:** COMPLETE -- the weekend-1 ledger analyzed in the binding
dual-language form, the TVB-27 external audit returned and folded same
session, the twice-deferred TVB-26 fold executed with a user re-ruling,
and the collision-receipt instrument landed. All work pushed both repos.

### What was accomplished

- WEEKEND-1 LEDGER ANALYSIS (hip3-executor commits c8e65f4..2daf6a4 +
  corrections dd1a591, e782e57; report runs/2026-08-22_weekend1/
  ANALYSIS.md + analysis.json + analysis/weekend1.py): books reconcile
  against the venue TO THE CENT (52.60 - 6.0327 closedPnl - 0.8082 fees
  - 0.0084 funding = 45.7507 vs 45.75); 4 unknown_exit rows reclassified
  from venue fills (3 target / 1 stop -> true mix 15 flip / 9 stop /
  8 target / 2 kill_flat); flip exits: 14/15 observed stop-first after
  exit, 0 target-first, observed savings +17.34pp = +$5.20 (XMR
  +12.38pp quarantined as unresolved scenario); conts 0/7 with the
  structural no-TP fact scoped from the sample outcome; rr-floor census
  (904 aligned refusals, 68.9% winners, mean -0.154%/trade gross =
  tiny-target/reclaim class as named by TVB-22); fees $0.81 = 0.040% of
  notional (not the TVB-1 churn regime); account-field double-count
  found + verified (exact when flat, +~1 margin lot per open position).
- MMQB + CONVICTION CENSUSES (user-requested; ddbd9d0, 21bd2a9): rails-
  blocked pool (211) sims WORSE than the taken book (-0.843 vs
  -0.595%/trade) -- no flattering survivorship; stack-blocked pool (256)
  +0.238%/trade BUT median -0.28% and top-8 = 93% of profit
  (confirmation-lag question, one regime, upper-bound census); kind x
  direction decomposition: rev-long +$1.11 NET (6/13) vs all other
  quadrants negative (third sighting of the short-whipsaw signature);
  conviction census REFUTED the intuitive tier -- winners had NEAR
  targets (median 1.59% vs losers 4.48%) and LOWER R:R at fill (1.09 vs
  1.87); per-trade risk was a 32x accident of stop distance
  ($0.12-$3.83) -> risk-normalize before any tier.
- TVB-27 AUDIT RETURNED 2026-08-25 (NEEDS-CHANGES: no CRITICAL, 2 HIGH /
  7 MEDIUM / 2 LOW) and FOLDED same session. Critical synthesis: the
  audit reproduced EVERY published number, then correctly flagged (and
  we accepted): the flip headline mixed observed savings with an
  unresolved scenario (MEDIUM-3, corrected + full-precision aggregation);
  my match_fills size check was a no-op bug (MEDIUM-2, now a hard
  assert, passes on real data); MMQB language over-claimed fair-swap/
  population inference (MEDIUM-4, reframed as upper-bound census with
  the auditor's flip-proxy calibration recorded -- median 2.36h late, no
  fixed sign, brackets-only +0.435%); mechanics-boundary language pass
  (MEDIUM-5); candle-cache "committed" docstring corrected (MEDIUM-7);
  wallet-inventory + webhook echo fixed (LOW-1); weekday erratum -- the
  run was SAT 08-22 -> MON 08-24 UTC (LOW-2, annotated in place here).
  The 2 HIGH executor lifecycle defects (bracket not fail-closed;
  KILL_FLAT can announce success unverified) + 4 MEDIUMs are now the
  BINDING round-2 pre-live gate in hip3-executor README. DISPUTED:
  nothing material. Scope note: the review was pinned at 2daf6a4, so
  the conviction census (21bd2a9) is UNREVIEWED -> in the TVB-28 range.
- TVB-26 FOLD (owed since 08-17, df291ef; all four findings REPRODUCED
  first): MEDIUM D9 -- the "books the worse fill by design" claim is
  FALSE per-bar (PX-fresh counterexample verified to the tick: shared
  level 1184.2, i3 close-fill 1184.4 BETTER; own sign census 4 worse /
  2 better of 6; auditor 16-bar replay 7/9); USER RE-RULING 2026-08-24:
  risk-first STANDS as a priority CONVENTION, not a pessimism guarantee
  -- relabeled in report Finding 5, prereg (append-only dated
  amendment), ARM_LEDGER; prot+tgt membership corrected 56 -> 58. NEW
  INSTRUMENT: the engine emits per-collision candidate-fill RECEIPTS
  (classes, candidate fills incl gap rules, executed fills, signed
  deltas) into recs + rollups; tests pin the audit counterexample class.
  LOW-2 two-way arm-set gate + mutations; LOW-3 round-once roster fee
  from fee_sides; LOW-4 stop_src_ts regression-bound. 270 tests pass.
- DESIGN SEEDS for round 2 (user questions answered in-session):
  strat-methodology loaded -- the cont-target idea (walk UP timeframes
  incl atypical aggregations to find the containing structure) maps to
  the skill's R14/R18 continuation-magnitude rule; committed
  counterfactual: inheriting the escalation-backing target changes
  NOTHING (all 7 conts still stop first; backing structures +1.4% to
  +27.6% away) -> the design question is a NEAR bank + reachability.
  position-sizing-risk loaded -- sizing amplifies edge, never creates
  it; notional-vs-leverage distinction recorded.
- USER REGIME FRAMING recorded (ANALYSIS.md operator context): the
  window was post-ignition digestion after the best 1-2 days in crypto
  in years -- a mild edge case; the DESIGN regime (in position when
  momentum ignites; shorts exit via stop/invalidation/flip and reverse)
  went untested by this window.

### Context for next session

- FIRST TASK: the round-2 design session (plan mode ON) -- cont-target
  contract, regime/direction input, risk-normalized sizing, pre-live
  gate implementation plan. All rule changes are dated USER rulings.
- The pre-live gate is BINDING: no live run until the 2 HIGH + 4 MEDIUM
  executor fixes land. Agent approval expired ~08-29; rm data/KILL_FLAT
  deliberately before any future run.
- Next canonical regen re-pins rollups with collision_receipts +
  fee_sides + round-once fee (expected deltas: P1 fee 1.0002->1.0000
  July, 0.6502->0.6500 fresh).
- User_Notes.md at repo root is the user's personal untracked scratch --
  leave untracked, never sweep into a commit.

### Files created/modified

- This repo: analysis/paper/engine.py (+receipts), tier_b_exits.py,
  tier_b_t1floor.py, tests (+5), docs/experiments/tvb25_exit_round_
  report.md + prereg (D9 corrections), docs/ARM_LEDGER.md,
  docs/reviews/tvb27-codex-audit.md (committed), REVIEW_REQUEST.md,
  HANDOFF annotations, .session_startup_prompt.md.
- hip3-executor (PRIVATE): analysis/weekend1.py + analysis.json +
  ANALYSIS.md (analysis, censuses, audit corrections, operator context),
  runs README, repo README (pre-live gate), deploy/set_webhook.sh,
  venue/ ground truth (fills/funding/ledger committed; candle cache
  gitignored).

### Open

- [ ] Round-2 design session -> dated rulings + prereg (cont targets,
      regime input, sizing, pre-live gate plan)
- [ ] Pre-live gate implementation in hip3-executor (2 HIGH + 4 MEDIUM;
      BINDING before any live run)
- [ ] Month-end fresh-window extension through 2026-08-31 24:00 UTC
      (~Sep 1; regen re-pins rollups with receipts/fee_sides)
- [ ] TVB-28 review fold when returned (incl the conviction census,
      unreviewed by the TVB-27 audit)
- [ ] Agent re-approval + deliberate KILL_FLAT removal before round 2
- [ ] Carried: TV mirror per arm on demand; assessment owner decisions;
      TVB-18 repairs bundle; M+T PMG+ nudge; jackson set_inputs fix;
      tvb8/tvb9 unreturned

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb28-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED 2026-08-26 (docs/reviews/tvb28-codex-audit.md;
  NEEDS-CHANGES, 0 CRITICAL / 0 new HIGH / 7 MEDIUM / 1 LOW; flipped at
  TVB-29 session start; critical synthesis owed by the folding session)
- Commits to review: this repo `4a07107^..9a964e1` on `main` (6 commits,
  13 paths: the TVB-27 scope-extension docs commits + the fold commit
  df291ef + session-end docs 9a964e1; sanity-checked via
  `git diff --name-status`; the pin commit after 9a964e1 is routing,
  out of range). Sibling hip3-executor (PRIVATE, local path
  C:\Strat_Trading_Bot\hip3-executor): `21bd2a9^..e782e57` -- the
  conviction census (EXPLICITLY unreviewed by the TVB-27 audit, which
  was pinned at 2daf6a4), the audit-fold corrections dd1a591, and the
  operator-context addendum e782e57.
- Scope / what changed: TVB-26 fold (D9 relabel + user re-ruling +
  collision receipts + 3 LOW fixes + 5 tests); TVB-27 fold (analysis
  corrections, pre-live gate); conviction census; session docs.
- Focus areas (scrutinize these): (1) the collision-receipt emitter --
  candidate fills incl gap rules and mid-race prot arming, executed-row
  capture, no behavior change to the race itself (all committed streams
  must replay byte-identically; only NEW fields appear in recs/rollups
  on the next regen); (2) D9 relabel fidelity across report/prereg/
  ledger vs the audit's finding and the 2026-08-24 re-ruling; (3) the
  round-once fee change (P1 1.0002->1.0000 expected on regen -- verify
  no committed artifact was modified THIS session); (4) the conviction
  census method + claims (near-target/anti-R:R finding, 32x risk
  dispersion) under the same upper-bound caveats the TVB-27 audit
  enforced; (5) the corrected ANALYSIS.md staying inside the
  mechanics-test boundary; (6) request.security: no Pine changed --
  verify.
- Reviewed by: Codex CLI (GPT-5), returned 2026-08-26; FOLDED by TVB-29
  same day (this repo ddca002 + 7b4ae6a; hip3-executor 7d4fd86)
- Findings / critical synthesis (TVB-29): ALL EIGHT findings reproduced
  or confirmed BEFORE adjudication -- several digit-for-digit -- and
  accepted with ZERO material disputes. The auditor first revalidated
  our evidence base (suite 270 green, full tier_b_exits replay, 20
  event streams byte-identical, the 58 memberships, the D9 signs), so
  every finding attacks the instrument/contract layer, not the P&L.
  - M1 REPRODUCED live: the canonical 8-arm t1floor caller fails its
    own hardened 6-arm gate on A1F/D1ATR (probe confirmed), with event
    files written pre-abort into the canonical dir; smoke runs also
    wrote there unsuffixed (our finding, same class). FIX: _gate_scope
    caller contract (produced==requested both ways + family-scoped gate
    maps), staged event promotion after all gates, smoke out-dir
    redirect, 3 real-shape caller regressions.
  - M2 REPRODUCED exactly (58 members; 13 with no executable protective
    exit: July P2 4/18, July PX 5/21, fresh P2 2/10, fresh PX 2/9).
    USER RULED 2026-08-26: EXECUTABLE-ONLY -- corrected membership 45
    (14/16/8/7), the arming-only transitions ride the new
    floor_armed_inert counter (17 roster-wide: the 13 + 4 on bars never
    collision-labeled). Event streams verified byte-identical under the
    fix; report/prereg/ledger amended (dated); canonical rollups re-pin
    at the month-end regen. Also explains the earlier 56-vs-58 split
    (exact-pair vs superset counting).
  - M3 REPRODUCED (the PX-July NBIS receipt scores BF +0.9pp "vs
    executed" when BF was 60% of the actual path). USER RULED: honest
    FIRST-FILL diagnostic -- field renamed delta_vs_first_fill_pct,
    every both-ways claim narrowed; path-aware pricing deferred behind
    a prereg.
  - M4 CONFIRMED (e782e57 was prose-only) and the counterfactual is now
    IMPLEMENTED with per-trade touch receipts + candle-cache sha256 in
    analysis.json: 7/7 stop-first STANDS; the 6/7-within-0.2pp claim
    did NOT reproduce -- corrected to 4/7 full precision (STX's venue
    stop filled 1.0pp past its level; KAITO-down flipped 0.9pp before
    its stop). ANALYSIS.md header cache claim corrected.
  - M5 REPRODUCED exactly: med() picked the upper middle on even
    samples (losers 4.48->4.465, R:R 1.87->1.745, align 108->104.5 /
    69->68.4); denominators 9v18 + 6v20 now disclosed; frozen-rule
    membership recomputed on the DECISION-time clock (same five coins
    -- accidental parity, now stated); pre/post-freeze separated; the
    STX targetless cont is exempt from the R:R gate and carries -3.84
    of the -5.45 pre-freeze pp ("the process ruled it away" corrected).
    Every census DIRECTION survives correction.
  - M6/M7 ACCEPTED: causal/controlled-swap language rewritten to
    upper-bound-census framing; README safety model states INTENDED vs
    CURRENT per line until the gate lands; the two silently-shortened
    gate requirements (durable KILL_FLAT zero/zero receipt;
    candle/touch-receipt provenance) restored from the TVB-27 audit's
    original wording.
  - LOW-1 CONFIRMED: roster net now = roster gross minus the single
    round-once roster fee, rollup returns fee_sides, invariant test
    pins the algebra (drift case 2.9988 vs 2.9989 constructed).
  - DISPUTED: nothing material.
  - Regen note for the month-end extension: the canonical rollups now
    re-pin with MORE deltas than previously listed -- receipts +
    fee_sides + round-once fee (P1 1.0002->1.0000 July etc.), PLUS
    net fields becoming gross-minus-roster-fee, PLUS the corrected
    collision census (P2 14/9, PX 21/10, prot+tgt 45) and
    floor_armed_inert. All expected, all documented in the report
    amendments.

---

## Session TVB-27: Live pivot -- hip3-executor built, VPS-deployed, weekend-1 live test run and closed (COMPLETE)

**Date:** 2026-08-21..24 (multi-day session; user on remote control)
**Status:** COMPLETE -- USER-DIRECTED pivot away from the planned TVB-26
fold: a new PRIVATE repo (hip3-executor) was built from scratch, deployed
to the ATLAS VPS, and traded a dedicated $52.60 Hyperliquid agent-wallet
account live and unattended Fri 14:26 -> Sun 21:58 UTC [erratum
2026-08-26, TVB-27 audit LOW-2: the run days were SAT 08-22 14:26 -> MON
08-24 21:58 UTC; every date/timestamp is correct, the weekday names in
this entry are off by one]. Killed FLAT by
user decision (momentum stalled). Mechanics verdict: PASS on the
pre-registered success metric (enters/sizes/brackets/exits as designed).
The TVB-26 fold was flipped RETURNED at session start and DEFERRED (user
ruling) -- it remains owed.

### What was accomplished

- TVB-26 review flipped RETURNED (audit committed this session-end:
  NEEDS-CHANGES, 1 MEDIUM + 3 LOW; the MEDIUM carries a user checkpoint
  on the D9 risk-first ruling's worse-fill premise). Fold deferred by
  user direction; owed to TVB-28.
- hip3-executor BUILT (github.com/sheehyct/hip3-executor, PRIVATE; local
  C:\Strat_Trading_Bot\hip3-executor; commits e93d748..f4011b6): Python
  3.12/uv + hyperliquid-python-sdk; consumes hip3-scanner /api/state
  (single detection source -- the executor never analyzes bars); paper
  and live brokers behind one interface; venue-resident stop+target
  brackets; software exits (Type-3 invalidation with rev3 exemption,
  ftfc opposite-flip, hold-through-mixed); decision/trade/tracker JSONL
  journals; KILL / KILL_FLAT kill switches; agent wallet signs orders
  only (cannot withdraw -- blast radius = wallet balance); key entered
  only via hidden-prompt scripts in the user's own SSH session, never
  through chat (a mid-session user offer to relax this was declined).
- RULESET v0, all dated user rulings: rev signals on 1h/4h/1d + full
  15m/1h/4h/1d ftfc alignment; transition-based entries with
  per-signal-per-bar dedup + restart baseline; $30 fixed notional,
  isolated 10x (venue max clamp); MAE-clearance (stop inside 0.8/lev or
  skip); full exit at structural T1 + 24h post-exit rung tracking; main
  dex crypto only (xyz excluded -- weekend oracle dynamics), $1M 24h
  volume floor; max 2 concurrent, 60min cooldown, 12 entries/UTC day.
- MID-WEEKEND RULINGS (all dated, all before the Saturday freeze):
  continuation ESCALATE mode (a cont qualifies only with a live in-force
  higher-TF reversal behind it -- the user's "go up in timeframes until
  you find it", mechanized); min_reward_risk 1.0 entry floor (refuses
  the tiny-target/reclaim class the TVB-22 research named; fired on 22
  candidates at first snapshot); operator-grade alerts (dollar
  notional/margin/risk on entry; dollar P/L + unified-account balance on
  exit); hourly Discord P/L report (day resets 00:00 UTC + since-start).
- VPS DEPLOY (ATLAS VPS, atlas@, IP in session chat only -- never
  committed): tar-over-scp deploy kit, remote setup, phone runbook,
  hidden-prompt env + webhook scripts, preflight (derives agent address
  from the key WITHOUT exposing it, checks venue approval + balance --
  caught the user pasting the agent ADDRESS instead of the private key).
- WEEKEND-1 LIVE LEDGER (characterization only -- the pre-registered
  adjudication is mechanics-pass + 52.60 -> 45.75; qualifier added
  2026-08-26 per audit MEDIUM-5): 34 round trips, 9/34 winners, gross
  -6.04 USD; account 52.60 -> 45.75 (-6.85 net incl fees; day P/L by UTC
  date 08-22 -2.01 / 08-23 -0.33 / 08-24 -3.70 [weekdays Sat/Sun/Mon,
  erratum 2026-08-26]); exits 15 ftfc_flip / 8 stop / 5 target / 4
  unknown_exit (all pre-fix first hours) / 2 kill_flat; 11,909 decisions
  journaled. First trades: PENDLE long (bracketed on venue, verified via
  public API) and PYTH long booked AT target to the tick 17s after entry.
- LIVE LESSONS FIXED SAME DAY: Hyperliquid AUTO-CANCELS the reduce-only
  sibling when a position closes (exit classification now matches the
  closing fill's oid); paper positions rehydrate across restarts; a lint
  hook stripped a briefly-unused import between edits (verify against
  the source tree, not the cached build).
- CLOSED FLAT 2026-08-24 21:58 UTC via KILL_FLAT (user decision):
  0 positions, 0 orders verified via public API; canonical ledger
  committed at hip3-executor/runs/2026-08-22_weekend1/ (f4011b6);
  data/KILL_FLAT left on the VPS as a restart interlock.

### Context for next session

- FIRST TASK (user directive): heavy analysis of the weekend ledger,
  BINDING FORM = every finding in both code/automation vocabulary AND
  plain trader English. Seeded questions in .session_startup_prompt.md.
- TVB-26 fold still owed (deferred twice); the MEDIUM needs the user.
- Month-end fresh-window extension ~Sep 1.
- Agent approval expires ~2026-08-29; rm data/KILL_FLAT deliberately
  before any future live run.

### Files created/modified

- This repo: docs/reviews/REVIEW_REQUEST.md + docs/HANDOFF.md (TVB-26
  status flips at session start; this entry + rewritten request at
  close), .session_startup_prompt.md, docs/reviews/tvb26-codex-audit.md
  (returned audit, committed).
- Sibling repo hip3-executor (PRIVATE, all work): full build -- see
  commits e93d748..f4011b6 there.

### Open

- [ ] Weekend-1 ledger analysis, dual-language form (TVB-28 first task)
- [ ] Fold the TVB-26 external review (owed since 2026-08-17; MEDIUM has
      a user checkpoint on the D9 risk-first worse-fill premise)
- [ ] Month-end fresh-window extension through 2026-08-31 24:00 UTC (~Sep 1)
- [ ] Executor round-2 decisions after the analysis (user-owned; agent
      re-approval needed ~08-29; KILL_FLAT interlock on the VPS)
- [ ] Carried from TVB-26: TV mirror per arm on demand + pine header
      wording; assessment owner decisions; TVB-18 repairs bundle; M+T
      PMG+ nudge; jackson set_inputs fix; tvb8/tvb9 unreturned

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb27-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: REQUESTED
- Commits to review: this repo `59cda10^..59cda10` (docs only; the pin
  commit after it is routing, out of range). PRIMARY REVIEW TARGET is
  the sibling repo hip3-executor at C:\Strat_Trading_Bot\hip3-executor
  (PRIVATE remote; local access), range `e93d748^..f4011b6` -- the
  entire executor build, the weekend rulings, and the committed ledger
  (+ post-range docs commit 39255a9, the private ledger README).
- Scope / what changed: live micro-capital executor built + deployed +
  run + closed; this repo carries only status flips and session docs.
- Focus areas (scrutinize these): (1) order lifecycle correctness in
  broker.py (bracket placement, reconcile-on-vanish, oid-match exit
  classification, the never-hold-without-a-stop abort); (2) rules.py
  gates vs the dated rulings (escalation, R:R floor, MAE clearance,
  in-force); (3) ledger integrity -- journals vs venue fills (the
  runs/2026-08-22_weekend1 artifacts; 4 unknown_exit rows predate the
  oid fix, dated); (4) no secrets anywhere in the committed tree; (5)
  the mid-weekend change discipline (every change reporting-side or
  entry-side, dated, none retro-applied).
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb27-codex-audit.md exists)

---

## Session TVB-26: TVB-25 audit folded in full, canonical rerun (COMPLETE)

**Date:** 2026-08-16
**Status:** COMPLETE -- the TVB-25 external audit (NEEDS-CHANGES, 1 HIGH +
4 MEDIUM + 2 LOW) folded the same day it returned: all seven findings
reproduced in-repo BEFORE adjudication, zero disputes, two user rulings,
engine/runner repaired, canonical artifacts regenerated under prereg
amendment 2026-08-16b, report + ledger corrected. Seven commits pushed.

### What was accomplished

- ALL SEVEN FINDINGS REPRODUCED FIRST (read-only scripts against
  committed artifacts): F1 executed multi-class bars P2 July 21
  all-symbols / 14 roster vs 0 stored (WORSE than the audit's lower
  bounds; the audit's counts were roster-scoped); F3 D14 entry-hour
  joins 14/14/15 July + 8 (6 roster) fresh, matching the audit; F5
  arithmetic verified to the decimal (A0b fresh combined +76.4784 vs the
  quoted realized +55.65; matched means +0.7118 vs +0.3214; D5 receipt
  +1.7897); F7 D13 git-diff 31/33 files at two timestamps; F2/F4/F6
  confirmed by inspection.
- USER RULING 1 (D14 entry-hour, audit F3): literal-inclusive -- the
  entry hour COUNTS. Key fold fact: mid-hour entries ALREADY counted
  pre-entry same-hour breaks, so only this reading closes the
  evaluation-order gap without rewriting committed behavior. Engine
  post-entry check on the hour-completing entry bar (state_degenerate
  counter, i3-before-state order), long/short/one-tick boundary tests.
- ENGINE/RUNNER REPAIRS (cea3372, committed before the rerun, forward
  protocol): D9 census transition-accumulated (the bar-start snapshot
  could not see the bank->floor and retrace->breakeven armings) +
  collision_pairs per-combination diagnostic + fixture assertion;
  zero-duration episodes guarded on BOTH runner episode paths with an
  end-to-end regression; entry-stream gate expectation DECLARED
  (_expected_family_arms: full family canonical, requested+anchors
  smoke) + caller-boundary mutation test + veto_counts modulo rule
  pinned exact-scope; Signal.stop_src_ts absolute source timestamp
  (frozen, drift-asserted, on stop-arm entry events). 7 new tests
  (suite 265 passed, 2 skipped).
- CANONICAL RERUN (0c95a60): both windows, all gates PASS. Field-diff
  receipt vs the pre-fix snapshot: every non-S0 non-stop event stream
  byte-identical; D1S/PX additive stop_src_ts only; S0a/S0b/S0c changed
  by exactly the ruled D14 scratches (July S0a 866 -> 877 trades,
  +194.8 -> +195.3 combined; fresh 6 roster scratches per arm);
  matched-entry receipts unchanged to the FOURTH DECIMAL in both
  families. Corrected census: P2 18/11 july/fresh, PX 25/12, A0bS 5/4.
- USER RULING 2 (D9 revisit, promised by the prereg): risk-first STANDS
  on the corrected census -- collision_pairs shows EVERY prot+tgt bar
  (18+19+10+9) is the order-FORCED bank->floor arm-and-fire chain (zero
  already-armed collisions); genuinely order-sensitive bars (stop vs
  bf/brk/flip, i3 vs stop) are 3-6 per arm-window and the ruled order
  books the worse fill there by design. Dated in the prereg amendment.
- REPORT + LEDGER CORRECTED (871ca78): Finding 5 rewritten with the
  retraction named in place; C0 label removed from S0a (D12); the fresh
  S0a-vs-A0b comparison fixed to combined-vs-combined (+95.9 vs +76.5,
  ~+19pp -- the axis error is named in-text); matched values stated as
  sums WITH means; P1's per-trade claim scoped to this round's
  shared-trade set vs the D5 receipt on its own universe; S-family
  numbers refreshed.
- Prereg amendment 2026-08-16b (4631dbd, append-only, before code):
  D14 ruling, D9 semantics, P2 90%->100% no-bank correction,
  stop_src_ts, D13 31/33 correction, zero-duration treatment, declared
  gate expectations, and the dated risk-first revisit outcome.

### Context for next session

- TVB-26 review REQUESTED (range covers the census repair vs the prior
  reviewer's suggested reconstruction, the D14 implementation vs the
  ruling, the regeneration field-diff claims, and the corrected
  report/ledger numbers). Fold before new work.
- Month-end extension through Aug 31 under the same prereg (after the
  month completes, ~Sep 1). The F2 abort path is now supported, so the
  extension cannot crash on a degenerate episode.
- No new arm is TV-valid; mirroring per arm on demand with its own gate.
- The P2 per-trade underperformance remains the USER-OWNED design
  question; any refinement is a new a-priori variant.

### Files created/modified

- Modified: analysis/paper/engine.py (D9 rewrite, D14 post-entry check,
  stop_src_ts freeze), analysis/paper/patterns.py (Signal.stop_src_ts),
  analysis/paper/tier_b_exits.py (zero-duration guards, declared gate
  expectations, collision_pairs plumbing), tests/test_tvb25_exits.py
  (+4 tests + census asserts), tests/test_tier_b_exits.py (+4 tests),
  docs/experiments/tvb25_exit_round_prereg.md (amendment 2026-08-16b +
  revisit outcome), docs/experiments/tvb25_exit_round_report.md,
  docs/ARM_LEDGER.md, analysis/paper/tier_b_exits/ (17 regenerated
  artifact files), docs/reviews/REVIEW_REQUEST.md, docs/HANDOFF.md,
  .session_startup_prompt.md.
- New: docs/reviews/tvb25-codex-audit.md (the returned verbatim audit).
- Suite: 265 passed, 2 skipped (7 new tests); ruff clean; secret scan
  clean; pushed.

### Open

- [ ] Fold the TVB-26 external review when returned
      (docs/reviews/tvb26-codex-audit.md)
- [ ] Month-end fresh-window extension through 2026-08-31 24:00 UTC under
      the same prereg incl. 2026-08-16b (harvest -> pin -> rerun, ~Sep 1)
- [ ] P2 T1-retrace per-trade underperformance: user decides whether a
      refined a-priori variant enters a future round
- [ ] TV mirror per arm on demand + per-arm parity gates; package pine
      header "seed-exact" wording fix at the next TV sync
- [ ] Assessment owner decisions: kernel-vs-Pine charter question;
      1m/trade archiving start; spine CLAUDE.md project-map row (outside
      this repo)
- [ ] Greenlit repairs bundle (TVB-18, carried): F2 roster receipts +
      fail-closed, F3 5m-lifecycle warm-up regression, F4 eviction
      telemetry split, freeze-boundary invariant, SKHX tv_symbol/mintick
      backfill
- [ ] Nudge the M+T collaborator: PMG+ prefix structurally unreachable
      (carried from TVB-21)
- [ ] jackson MCP indicator_set_inputs kills Pine user scripts (carried;
      fix in tradingview-mcp-jackson)
- [ ] tvb8/tvb9 external reviews still unreturned (standing)

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb26-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED (2026-08-17, docs/reviews/tvb26-codex-audit.md --
  NEEDS-CHANGES, 1 MEDIUM + 3 LOW; critical synthesis pending the TVB-27 fold)
- Commits to review: `53599c4^..7f91c9c` on `main` (7 commits, 30 paths;
  RANGE-PIN RULE: the caret keeps 53599c4 in the diff; sanity-checked
  with `git diff --name-status`; the pin commit after 7f91c9c is
  docs-only routing, out of range).
- Scope / what changed: the TVB-25 audit fold -- reproductions, two user
  rulings (D14 entry-hour; risk-first stands), D9 census repair +
  collision_pairs, zero-duration episode support, declared gate
  expectations, stop_src_ts, canonical regeneration under amendment
  2026-08-16b, report/ledger corrections.
- Focus areas (scrutinize these): (1) reconstruct D9 independently from
  ordered per-bar eligibility (the prior reviewer's suggested check) and
  compare to the stored counters + collision_pairs; (2) the D14
  implementation vs the dated ruling -- post-entry check placement,
  i3-before-state order, boundary behavior, and the mid-hour-consistency
  claim used to justify the recommendation; (3) the regeneration
  field-diff claims (byte-identity of untouched streams, additive-only
  stop_src_ts, matched receipts unchanged); (4) the declared gate
  expectation -- mutate at the caller boundary (remove a produced arm,
  canonical and smoke) and check the modulo rule stayed exact-scope;
  (5) zero-duration episodes: P&L retained, MFE/MAE excluded, both
  runner paths; (6) recompute the corrected report/ledger numbers
  (S-family, matched sums AND means, the ~+19pp fresh gap, the scoped
  P1 claim); (7) amendment 2026-08-16b language: dated, append-only, no
  silent rewrites above it; (8) request.security: NO pine file changed
  -- verify none did.
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb26-codex-audit.md exists)

---

## Session TVB-25: audit folded + exit round built, run, reported (COMPLETE)

**Date:** 2026-08-16
**Status:** COMPLETE -- TVB-24 audit folded (F3-F6 fixed same session with
27 adversarial tests; F1/F2 became a user-ruled prereg amendment via live
walkthrough), then the exit round executed end to end per the amended
prereg: fresh harvest, engine extensions, runner, both windows, all gates
PASS, report + ARM_LEDGER. Ten commits pushed.

### What was accomplished

- TVB-24 AUDIT FOLDED (b31c11d; critical synthesis in the TVB-24 entry's
  External Review block below): every false-PASS path reproduced BEFORE
  adjudication. F3 entry-stream/census gates hardened (both-sides-exit
  divergence; _entry_stream_gate with exact arm set + stream-vs-rec
  reconciliation -- deviation-with-justification: the audit's roster-init
  sketch cannot catch its own mutation because AAPL/AMZN/GOLD are
  legitimate zero-event chop-veto shut-outs; census direction-consistency
  + injective one-outcome-per-entry). F4 canonical parity artifact
  protected (only the exact 3x3 writes it; wrapper metadata inside the
  PASS predicate; harvester arm read-back + strategy_count=1). F5 matched
  identity binds frozen entry state (price/ladder/boom/pmg/rev/star;
  tgt_rung excluded -- the only arm-dependent field across 942 shared
  identities). F6 receipts regenerated ADDITIVELY with provenance hashes
  (field-diff proof: all numbers byte-identical); pkg_parity seed wording
  narrowed; the pine header wording deferred to the next TV sync.
- PREREG AMENDED (2411821, committed before any code; user-ruled in three
  AskUserQuestion rounds): S0c state+BF arm restores the F1 BF isolation,
  A0b relabeled exit-family reference; deterministic exit state machine --
  risk-first pessimistic same-bar race (PROVISIONAL, D9 collision census
  makes its bite observable), two fill classes (protective = D3
  gap-through-at-open; profit = containment-only), P2 short-ladder
  fold-to-runner + same-bar arm-and-fire, i3 = prior-1H opposite extreme
  frozen at entry + entry-hour-only, X1 arming cases, immutable
  Signal.stop_anchor with strict-loss-side degeneracy -> ATR fallback;
  D9-D14 bundle; P2 runner post-retrace = reading A (BF target +
  breakeven floor).
- ROUND EXECUTED per the prereg's binding order: (2) fresh harvest +
  D13 pin Aug 3 -> Aug 16 00:00 UTC (047d695; merge-integrity verified --
  zero July-window rows changed, only the three 2026-08-04 forming-bar
  rows completed); (3) engine extensions behind inert defaults (007208e;
  20 fixtures; 55/55 committed Tier B rows field-equal through the
  extended engine); (4) runner tier_b_exits.py (209d2ef) with two
  gate-caught corrections committed BEFORE the clean rerun (5796da2
  veto-counter modulo rule; 7f3626e partially-banked open entries
  contribute no stream exit); (5) canonical run 62ff310 -- determinism
  55+88 rows field-equal, entry-stream gates PASS both families both
  windows, tranche reconciliation clean; report 40c94ce.
- FINDINGS (gross, contrasts only, no promotion -- full text in
  docs/experiments/tvb25_exit_round_report.md): (1) the bare state stop
  transforms the control through OCCUPANCY, not per-trade exit quality
  (S0a +194.8 July vs A0b +104.8 whole-arm; loses matched 27.4-vs-34.2;
  866 vs 172 trades); (2) the BF layer over the state base = +96.2pp
  (S0c +291.1) but worst-in-family per matched trade -- book
  composition; (3) the ATR stop (A0bS +214.9, dd 55-vs-122) is the FIRST
  overlay winning whole-arm AND matched axes -- it amputates the
  adverse-runner class; (4) every thesis exit loses to plain D1 on July
  (P1 +32.5 but WINS matched 18.5-vs-8.4; P2 +6.1 loses both axes -- the
  T1-retrace dump is the suspect; X1 -37.8/dd 119 = the stall-mode cost
  of extension-only protection; D1S -33.6 vs A0bS +110: STOP VALUE IS
  BOOK-DEPENDENT); (5) D9 collisions near zero -- the ruled convention
  does not distort (user's caveat answered). Fresh window: 13 committed
  arms directionally stable, A1F the lone near-zero negative.
- ARM_LEDGER (b38e0ad + refinement; USER REQUEST, standing): every arm in
  plain trading terms + numbers + What-Claude-notices; binding CLAUDE.md
  Reporting rule -- ledger updated every round, design-session arm
  restatements user-confirmed before prereg, AskUserQuestion options in
  trader language (or dual). User clarified their 50/30/10 phrasing was a
  hypothetical example, not a mis-recall (record corrected).

### Context for next session

- TVB-25 review REQUESTED (range covers amendment coherence, the engine
  race vs the amendment, runner gates incl. the final-exit stream
  convention, the two forward-protocol corrections, report claims vs
  artifacts). Fold before new work.
- Month-end extension through Aug 31 under the same prereg (after the
  month completes).
- No new arm is TV-valid; mirroring per arm on demand with its own gate.
- The P2 per-trade underperformance is a USER-OWNED design question; any
  refinement is a new a-priori variant.

### Files created/modified

- New: analysis/paper/tier_b_exits.py + analysis/paper/tier_b_exits/ (40
  artifacts: events x 33 arm-windows, results, matched-entry receipts,
  manifest), tests/test_tvb25_exits.py (20), tests/test_tier_b_exits.py
  (6), docs/experiments/tvb25_exit_round_report.md, docs/ARM_LEDGER.md,
  docs/reviews/tvb24-codex-audit.md.
- Modified: analysis/paper/{engine,patterns}.py (TVB-25 features, inert
  defaults), analysis/paper/{tier_b_t1floor,round_census,pkg_parity,
  t1floor_diagnostics,entry_audit}.py (audit fold), the three t1floor
  receipts (additive provenance), scripts/tvb23_pkg_harvest.mjs
  (read-back), tests/test_{t1floor_gates,pkg_parity,t1floor_diagnostics}.py,
  docs/experiments/tvb25_exit_round_prereg.md (amendment + pins),
  analysis/paper/bars/ (33 files, fresh harvest), CLAUDE.md (ledger
  rule), HANDOFF + REVIEW_REQUEST + .session_startup_prompt.md.
- Suite: 258 passed, 2 skipped (53 new tests); ruff clean.

### Open

- [x] Fold the TVB-25 external review when returned
      (docs/reviews/tvb25-codex-audit.md) -- DONE TVB-26 2026-08-16
      (all seven findings folded; two user rulings; canonical rerun)
- [ ] Month-end fresh-window extension through 2026-08-31 24:00 UTC under
      the same prereg (harvest -> pin -> rerun)
- [ ] P2 T1-retrace per-trade underperformance: user decides whether a
      refined a-priori variant enters a future round
- [ ] TV mirror per arm on demand + per-arm parity gates; package pine
      header "seed-exact" wording fix at the next TV sync
- [ ] Assessment owner decisions: kernel-vs-Pine charter question;
      1m/trade archiving start; spine CLAUDE.md project-map row (outside
      this repo)
- [ ] Greenlit repairs bundle (TVB-18, carried): F2 roster receipts +
      fail-closed, F3 5m-lifecycle warm-up regression, F4 eviction
      telemetry split, freeze-boundary invariant, SKHX tv_symbol/mintick
      backfill
- [ ] Nudge the M+T collaborator: PMG+ prefix structurally unreachable
      (carried from TVB-21)
- [ ] jackson MCP indicator_set_inputs kills Pine user scripts (carried;
      fix in tradingview-mcp-jackson)
- [ ] tvb8/tvb9 external reviews still unreturned (standing)

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb25-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED (2026-08-16, docs/reviews/tvb25-codex-audit.md;
  verdict NEEDS-CHANGES, 1 HIGH + 4 MEDIUM + 2 LOW) -- FOLDED by TVB-26
  same day, critical synthesis below.
- CRITICAL SYNTHESIS (TVB-26, 2026-08-16): the audit is accepted IN FULL
  -- all seven findings reproduced in-repo before adjudication, zero
  disputes. The reviewer had independently replayed the entire
  evidentiary base first (55+88 inert-default rows, rollups, receipts,
  hashes, fees, tranche fractions), so the findings attack the
  DIAGNOSTIC/CONTRACT layer, not the P&L: that framing held up exactly.
  - F1 (HIGH, D9 census) reproduced WORSE than the audit's lower bounds
    (executed multi-class bars all-symbols: P2 July 21, PX 24; the
    audit's 14/16 were roster-scoped -- scope note, not a dispute).
    Root cause confirmed at engine bar-start snapshot vs the target
    loop's mid-bar floor arming. Repaired to transition-accumulated
    satisfiability + a collision_pairs decomposition; the arm-and-fire
    fixture now asserts the counter. Corrected census: P2 18/11
    july/fresh, PX 25/12 -- and the decomposition shows every prot+tgt
    bar is the order-FORCED bank->floor chain (zero already-armed
    collisions); order-sensitive bars are 3-6 per arm-window. USER
    RULING on the corrected census: risk-first STANDS (prereg dated
    note). The retracted "max 6 / no revisit" Finding 5 is rewritten
    in place with the retraction named.
  - F3 (D14 entry-hour) reproduced exactly (14/14/15 July; the audit's
    fresh 6 = roster scope of our 8). Key fact surfaced during the fold:
    mid-hour entries ALREADY counted pre-entry same-hour breaks, so only
    the literal-inclusive reading closes the gap without rewriting
    committed behavior. USER RULING: literal-inclusive -- the entry hour
    counts; engine post-entry check + state_degenerate counter +
    long/short/one-tick boundary tests.
  - F2/F4/F6/F7 all confirmed by inspection or replay and fixed:
    zero-duration episodes guarded on both runner episode paths +
    end-to-end regression; gate expectation is now DECLARED (full family
    canonical, requested+anchors smoke) with a caller-boundary mutation
    test + the modulo rule pinned exact-scope; prereg corrected 90%->100%
    no-bank runner + stop_src_ts absolute source timestamp implemented
    (frozen, drift-asserted, on entry events); D13 note corrected to
    31/33 files at two timestamps (git-verified).
  - F5 (report/ledger axes) verified to the decimal (A0b fresh combined
    +76.4784 vs the quoted realized +55.7; matched means +0.71 vs +0.32)
    and corrected: sums labeled as sums with means beside them, the P1
    best-per-trade claim scoped against the D5 receipt's +1.79/trade on
    its own universe, the C0 label removed per D12.
  - Canonical artifacts REGENERATED under amendment 2026-08-16b with a
    field-diff receipt: every non-S0 non-stop event stream byte-identical;
    D1S/PX additive stop_src_ts only; S0 arms changed by exactly the
    ruled D14 scratches (July S0a +194.8 -> +195.3, 866 -> 877 trades);
    matched-entry receipts unchanged to the fourth decimal. No research
    conclusion flipped; the round's contrast readings all survive with
    corrected instruments.
- Commits to review: `b31c11d^..6597a68` on `main` (11 commits, 98 paths;
  RANGE-PIN RULE: the caret keeps b31c11d in the diff; sanity-checked
  with `git diff --name-status`; the pin commit after 6597a68 is
  docs-only routing, out of range).
- Scope / what changed: TVB-24 audit fold (F3-F6 code + tests, receipts
  additive-regenerated); the user-ruled prereg amendment; fresh harvest +
  D13 pin; engine TVB-25 exit features behind inert defaults; runner +
  two forward-protocol gate corrections; canonical run artifacts; report;
  ARM_LEDGER + CLAUDE.md practice rule.
- Focus areas (scrutinize these): (1) amendment vs rulings coherence and
  whether an independent implementer can now derive one event stream;
  (2) engine race vs the amendment (order, two fill classes, i3
  level/scope/degenerate, stop freeze + degeneracy, P2 fold/arm-and-fire/
  reading-A breakeven, X1 arming, D14 inclusive state stop) and the
  inert-defaults claim (55/88-row field equality); (3) runner gates: the
  final-exit stream convention for tranche arms, family anchors (A0b
  in-memory, committed D1), tranche reconciliation, the modulo-rule fix;
  (4) report + ledger claims vs committed artifacts (esp. matched-entry
  numbers and every occupancy reading); (5) D10 fee math; (6) harvest
  merge integrity (the three completed forming bars); (7) request.security:
  no pine changes this session -- verify none slipped in.
- Reviewed by: OpenAI Codex CLI (GPT-5), returned 2026-08-16
- Findings: 1 HIGH (D9 census undercount -- P2/PX arm-and-fire bars
  invisible to the bar-start snapshot) + 4 MEDIUM (i3-degenerate runner
  abort; D14 entry-hour ordering unruled; gate wrapper defeated the
  exact-arm-set check; report/ledger axis + units errors) + 2 LOW (P2
  90%-vs-100% prose + missing stop-source record; D13 merge-note count).
  All folded same day by TVB-26 -- see the synthesis above.

---

## Session TVB-24: both reviews folded + TV mirror parity-gated PASS (COMPLETE)

**Date:** 2026-08-15 (autonomous overnight; user in and out)
**Status:** COMPLETE -- TVB-23 Codex audit folded (every finding reproduced
before adjudication), the 2026-08-14 strategy-implementation assessment
folded (both diagnostics reproduced exactly), and prereg step 7 closed:
TV mirror built, saved, and 9-cell parity gate PASS. Three commits pushed.

### What was accomplished

- TVB-23 AUDIT FOLDED (674c7f6; NEEDS-CHANGES, 3 MEDIUM + 2 LOW, all
  reproduced BEFORE adjudication -- critical synthesis in the TVB-23
  entry's External Review block below): F1 guards hardened fail-closed
  (determinism union-of-fields + row cardinality both directions;
  entry-stream all 15 depth pairs + equal symbol sets +
  prefix-next-must-be-exit; census open count/direction + event linkage)
  with 17 adversarial regression tests (tests/test_t1floor_gates.py);
  committed artifacts re-verified PASS in memory, NOT regenerated. F2 the
  two prereg-bound diagnostics delivered post-hoc
  (analysis/paper/t1floor_diagnostics.py): atr_context_receipt.json
  (roster ATR% spread 0.26-1.98%, grounds the accidental-symbol-filter
  mechanism) + matched_exit_receipt.json (NEW mechanism reading: on the
  37 trades closed in ALL six depth arms realized P&L rises strictly with
  depth 38.4 -> 66.2pp, so the whole-arm shallow-top is an occupancy
  effect; survivor boundary declared); report finding 5 narrowed by dated
  correction (label-bar-exclusive census cannot support the exit
  counterfactual). F3 provenance downgraded to self-attested for the two
  same-commit corrections (dated prereg note); runner now records
  prereg_blob_sha256. F4/F5 dated text corrections (arm count 9 -> 8,
  superseded entry-book language, the realized-P&L D2 dip).
- ASSESSMENT FOLDED (33c7138): docs/strategy-implementation-assessment.md
  committed as source; BOTH its diagnostics reproduced exactly before
  adoption (D1 entry-vs-close 61/41 mean +0.0809pp sum +8.25pp; identity
  funnel 4111 evals -> 682 identities, 102 entries / 86 / 16 re-entered)
  and folded into committed tooling analysis/paper/entry_audit.py +
  entry_audit_receipt.json with pinned tests. NEW finding beyond the
  assessment: 11/765 committed entries (4 distinct events) booked level
  fills OUTSIDE the entry bar's range -- entry-side born-beyond analogue,
  but structurally PESSIMISTIC-direction (far side of the max/min fill
  rule) and immaterial (~0.7pp against the arms). Three-benchmark fill
  framing pinned (vs level/open = conservative-by-construction; vs
  decision close = favorable-majority; vs live intrabar = unresolved at
  5m). Constitution sync: CLAUDE.md + README no longer deny the Python
  engine exists (stale since TVB-21); engine comment disambiguates the
  gate-open-proximity veto from M+T's reversal-streak chop (P1-3).
  Adjudication delivered to the user in-session: adopt the
  research-integrity spine now, park the G0-G7 execution architecture
  until the live arc opens (tension with the loss-tolerable micro-canary
  philosophy surfaced, user's call).
- TV MIRROR + RE-GATE (b58688e; prereg step 7 CLOSED): floor/ATR/
  arm-selector into pine/tfc_mt_package_strategy.pine, semantics verbatim
  from engine.py (H8 header hunk; ATR update-order verified against
  replay_bar; comma-free labels; D1ATR tested before D1 in the startswith
  chain). Editor binding verified BEFORE save (byte-equal to committed
  base modulo the known cp1252 dump artifact); injection disk -> Monaco
  via node CDP with SHA-256 round-trip verification (70,537 chars
  byte-equal); compiled clean; saved (same script evolves, v10+). GATE
  PASS 9/9 (GOOGL/TSLA/DRAM x D1/DINF/D1ATR): 218/218 events matched,
  zero twin-only/tv-only, offset 0s every cell, break/flip float-exact,
  pattern layer clean on all 111 checked entries. The TV strategy is now
  parity-valid for ALL SIX arms. New tooling:
  scripts/tvb23_pkg_harvest.mjs (TVB_TARGET target pinning),
  pkg_parity.py --arms with generation-scoped artifacts (committed TVB-22
  pin never overwritten; gate twin's ATR seed-exact vs the pine).
- OPERATIONAL (memory tv-mcp-tvb24-ops): layout_switch false-success
  (create-new-layout UI flow works); Add-to-chart is icon-only, findable
  by title attribute; screenshots hang when the session is locked (drove
  the whole TV phase blind via DOM probes); worked in a NEW
  "TVB24-mirror" layout so the user's layouts/live tab were never driven.
- MORNING DESIGN SESSION (user present, plan mode; the research fork
  RESOLVED): the TVB-25 exit round designed and PRE-REGISTERED
  (docs/experiments/tvb25_exit_round_prereg.md, committed BEFORE any
  code). User rulings: all four exit candidates enter (thesis exits
  individual, overlays as with/without, one composite endpoint); C0 state
  stop = 2-against at 1H close; ladder bottom = TWO arms (S0a pure /
  S0b +flip) vs A0b; BOTH partial profiles (P1 two-piece 50@T1+runner;
  P2 the user's runner profile: skip T1, 40/20/20/10 at T2-T5, 10%
  runner to the BF touch, floor arms after the T2 bank, T1 retrace exits
  the middles, runner exits at breakeven, -0.25% variant named-deferred);
  risk overlay = per-setup STRUCTURAL stops (skill 5.2 table in the
  prereg) with ATR(14,1H)x3 default for controls/undefined anchors;
  intrabar-3 invalidation as an overlay contrast; fresh window = Aug 3 ->
  latest complete day now, extended through Aug 31 under the same prereg;
  headless first, TV mirror on demand per arm. Also logged to memory:
  the $50-or-less separate-wallet live canary + realism layer
  (sizing/dollar P&L/leverage/margin) as a named future lane; the user's
  vol/time-compression observation (instrument/regime-dependent minimal
  continuity, a-priori-only future variant).

### Context for next session

- Prereg step 7 CLOSED -- nothing blocks the research fork; it needs the
  USER's direction (exit-design [plan mode ON] vs fresh-window vs the
  assessment-motivated C0-current/C1-current isolated pair).
- The assessment's owner-level items stay parked: kernel-vs-Pine charter
  question, 1m/trade archiving start, spine CLAUDE.md project-map row
  (outside this repo, still says Pine-first).
- Workbench: TV Desktop on CDP 9222, TVB24-mirror layout, package
  strategy mounted (DRAM 5m, arm D1ATR), editor bound to the package
  script, TV source byte-equal to committed HEAD.

### Files created/modified

- New: analysis/paper/t1floor_diagnostics.py, analysis/paper/entry_audit.py,
  scripts/tvb23_pkg_harvest.mjs, tests/test_t1floor_gates.py,
  tests/test_t1floor_diagnostics.py, tests/test_entry_audit.py,
  docs/reviews/tvb23-codex-audit.md, docs/strategy-implementation-assessment.md,
  tier_b_t1floor/{atr_context,matched_exit,entry_audit}_receipt.json,
  analysis/reference/pkg_parity/tvb23_*_trades.json (9) + tvb23_parity_result.json.
- Modified: analysis/paper/tier_b_t1floor.py + round_census.py (fail-closed
  gates), analysis/paper/pkg_parity.py (TVB-23 arms), analysis/paper/engine.py
  (comment only), pine/tfc_mt_package_strategy.pine (H8 + gate-pass header;
  TV-synced sha-verified), docs/experiments/tvb23_t1floor_{prereg,report}.md
  (dated corrections), CLAUDE.md, README.md, HANDOFF + REVIEW_REQUEST flips,
  .session_startup_prompt.md.
- Suite: 205 passed, 2 skipped (24 new tests); ruff clean.

### Open

- [x] Research fork (user direction) -- CLOSED same session by the morning
      design session: all three lanes merged into ONE pre-registered round
      (docs/experiments/tvb25_exit_round_prereg.md); TVB-25 builds + runs it
- [ ] TVB-25 round: build + run per the committed prereg (engine tranche
      machinery, structural/ATR stops, state stop, intrabar-3, X1 arming;
      fresh-bar harvest FIRST; hardened gates); month-end window extension
- [ ] Assessment owner decisions: kernel-vs-Pine charter question; start
      1m/trade archiving for causal-fill work; spine CLAUDE.md
      project-map row stale (outside this repo)
- [ ] Greenlit repairs bundle (TVB-18, carried): F2 roster receipts +
      fail-closed, F3 5m-lifecycle warm-up regression, F4 eviction
      telemetry split, freeze-boundary invariant, SKHX tv_symbol/mintick
      backfill
- [ ] Nudge the M+T collaborator: PMG+ prefix structurally unreachable
      (carried from TVB-21)
- [ ] jackson MCP indicator_set_inputs kills Pine user scripts (carried;
      fix in tradingview-mcp-jackson)
- [ ] tvb8/tvb9 external reviews still unreturned (standing)

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb24-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED (2026-08-16, docs/reviews/tvb24-codex-audit.md;
  NEEDS-CHANGES -- critical synthesis to be written by TVB-25)
- Commits to review: `674c7f6^..e92e59c` on `main` (6 commits incl. the TVB-25 prereg e92e59c: 674c7f6
  audit fold; 33c7138 assessment fold; b58688e TV mirror + gate PASS;
  130013e session-end docs. RANGE-PIN RULE: the caret keeps 674c7f6 in
  the diff; sanity-checked with `git diff --name-status`).
- Scope / what changed: TVB-23 audit fold (fail-closed gate hardening +
  adversarial tests; prereg-bound diagnostics as receipts; dated
  corrections; provenance hashing); assessment fold (entry_audit receipts,
  constitution sync, chop-naming disambiguation); TV mirror of the TVB-23
  arms + 9-cell parity gate PASS (harvest variant, pkg_parity --arms).
- Focus areas (scrutinize these): (1) hardened gates genuinely fail-closed
  (union-of-fields, all-pairs, prefix rule, census open checks) and the
  adversarial tests actually bite; (2) t1floor_diagnostics + entry_audit
  receipts reproduce from committed artifacts (conventions honest,
  survivor-shape boundary on the matched-exit read); (3) pine H8 hunk
  semantics verbatim vs engine.py (floor order before no-target skip; ATR
  Wilder math + update order; pct/ATR mutual exclusion; arm derivation
  startswith chain D1ATR-before-D1); (4) parity gate extension (prefix
  routing, generation-scoped artifact never overwrites the TVB-22 pin;
  ATR seed-exactness claim for the gate twin); (5) dated corrections
  never silently rewrite (prereg/report); (6) request.security: no new
  calls; pine change is the H8 logic + header (TV-synced, sha-verified).
- Reviewed by: OpenAI Codex (GPT-5), returned 2026-08-15/16
- Findings: NEEDS-CHANGES -- 1 HIGH + 4 MEDIUM + 1 LOW. CRITICAL SYNTHESIS
  (written by TVB-25, 2026-08-16; every finding reproduced BEFORE
  adjudication):
  - The committed TVB-24 evidence is NOT disputed: the reviewer
    independently re-ran the 9-cell parity gate (9/9, same 218 events) and
    recomputed all five diagnostic receipts to the published values. The
    verdict targets forward-looking contracts (the TVB-25 prereg and the
    residual gate false-PASS paths), not the results.
  - F3/F4/F5/F6 AGREED and FIXED by TVB-25 same session, all false-PASS
    paths reproduced first: (F3) exit-vs-entry first divergence, one
    symbol deleted from ALL six arms, a whole arm missing, and a census
    direction flip all passed the old gates -- hardened with a
    both-sides-exit divergence rule, an extracted _entry_stream_gate
    (exact arm set + stream-vs-rec reconciliation + roster scope), and
    census direction-consistency + injective one-outcome-per-entry
    linkage. DEVIATION with justification: the audit's roster-initialized
    stream-map sketch would NOT catch its own mutation -- three roster
    symbols (AAPL/AMZN/GOLD) are legitimately zero-event chop-veto
    shut-outs, so empty-vs-empty streams still compare equal; anchoring
    each arm's stream against its own per-symbol replay rows
    (n_trades/open_dir) does catch it. (F4) a 1-cell smoke run reproduced
    targeting the canonical artifact; now only the exact 3x3 writes
    {gen}_parity_result.json (subsets write scope-named smoke files),
    wrapper metadata is validated inside compare(), and the harvester
    reads the arm input back and rejects strategy_count != 1. (F5) the 41
    all-six identities verified equal on entry price + ladder (the
    committed exits-in-isolation read is supported by the data); the
    matched contract now binds frozen entry state
    (price/ladder/boom/pmg/rev/star), with tgt_rung excluded by declared
    reason (per-arm target config -- the ONLY differing field across the
    942 shared identities); duplicates fail closed. (F6) the three
    receipts regenerated ADDITIVELY with provenance hashes
    (bars/roster/minticks/executed code) -- field diff proves every
    numerical field byte-identical, only provenance/matched_entry_state/
    timestamps/conventions added or changed; the pkg_parity ATR comment
    narrowed to observed-decision-parity language. The package pine's
    header wording (seed-exact, ~line 164) is DEFERRED to the next TV
    sync so a comment edit does not drift the sha-verified mirror.
    27 new adversarial regression tests; suite 232 passed / 2 skipped.
  - F1 (HIGH) + F2 (MEDIUM) target the TVB-25 prereg and are USER-RULING
    territory. Factual basis CONFIRMED: A0b's twin override is arm
    cadence only -- it inherits BF harvest + brk + flip and TwinConfig
    has no state-stop field, so S0a/S0b-vs-A0b is an exit-FAMILY
    replacement, not a BF isolation; and the exit state machine's
    same-bar collision precedence, P2 short-ladder/gap cases, X1 arming
    snapshot, intrabar-3 level freeze, stop_anchor immutability, and
    partial-position fee formula are genuinely underdetermined. Both go
    to a design session before any TVB-25 code (dated prereg amendment).
  - Shading, not dispute: the audit reads S0a's 2-against state stop as
    a charter-3.5 naming mismatch; that form was the user's explicit
    design-session ruling, so the fix is labeling it as the ruled
    variant, not correcting an error.

---


> Older sessions: TVB-22..TVB-23 archived 2026-08-28 to
> docs/session_archive/HANDOFF_TVB22-TVB23.md (verbatim). Earlier:
> HANDOFF_TVB18-TVB21.md, HANDOFF_TVB10-TVB17.md, HANDOFF_TVB0-TVB9.md.
