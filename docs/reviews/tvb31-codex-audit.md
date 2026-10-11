<!--
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-31 External Audit -- Codex (verbatim source, read CRITICALLY)

> External review of the pinned TVB-31 changes captured 2026-10-10
> (TVB-31 post-session). Plain ASCII; wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-31 -- safety-boundary fold and HyPaper spike.
- **Reviewed:** tradingview-backtesting `0d7437c^..7bfde0f`; local hip3-executor `4e384bb^..4e384bb`; local hip3-scanner `d0fe9e7^..d0fe9e7`, identical tree at merge `7723462`.
- **Reviewer:** GPT-6 / Codex, local tools. The runtime supplies no more specific model identifier.
- **Overall verdict:** NEEDS-CHANGES.
- **Range verification:** `git diff --name-status` run before source review for all three ranges; public range has the stated 10 paths. Scanner `git diff --name-status d0fe9e7 7723462` is empty. Repo root and `main` confirmed. All source line references below are at these endpoints, with sibling paths qualified by repo name.
- **Evidence:** pinned-source inspection and in-memory AST probes with fake inputs, plus public HyPaper source at `b054fdd`. No venue account queries or orders. Current public checkout tests: 324 passed, 2 skipped; this is not a test result for the historical executor pin. Existing untracked `User_Notes.md` left untouched.
- **Finding counts:** CRITICAL 0, HIGH 2, MEDIUM 2, LOW 0. Clean checks and limitations are not counted as defects. HIGH findings below are historical blockers at this pin; their documented TVB-34 repairs are acknowledged separately.

## 2. Verbatim audit

### 1. Proved market closes and the PaperBroker boundary

**F1 [HIGH] A malformed successful position response is accepted as proof of flat.** `hip3-executor/src/hip3_executor/broker.py:151` defaults missing `assetPositions` to an empty list. The new close proof at `broker.py:236` calls `position_for`, which consequently returns `None` for `{}`. An accepted partial close followed by that response is reported successful; callers cancel protection and remove the tracked position. The same parser feeds `requery_flat`, so a structurally incomplete response can also produce a clean emergency receipt. Pinned-source probe: fake `user_state -> {}` gave `position_for('T') -> None`, without an exception. Require the response and list schema before treating absence as flat. TVB-34 subsequently repairs the missing-list case; this finding describes the TVB-31 endpoint, not current deployment status.

**[NOTE] What held:** a valid nonzero residual raises before any caller's cancellation, and query exceptions propagate as unknown. Traced software exits, protection repair, pending-intent reconciliation, entry-failure reconciliation, and emergency flatten. A same-coin refill visible in the fresh read is conservatively unresolved. A refill after that read remains an unavoidable non-atomic boundary; this is not a claim of exclusive account ownership. PaperBroker synchronously removes its simulated position and returns its size, but does not exercise transport ambiguity or validate the rich live stop row.

### 2. Unknown-scope emergency sweep

**[NOTE] Clean for the exception path:** `hip3-executor/src/hip3_executor/engine.py:511` records poll failure, limits attempted closes to tracked records, and `engine.py:528` skips the global order sweep. `_flatten_all` cancels only after a proved close and puts any exception in `failed`. Live emergency handling reaches this before requesting scanner state. The fresh terminal proof remains required. Inspection of the new regression vectors supports those paths. F1 is the separate case where malformed data does not raise, so `venue_ok` is incorrectly true; the sweep guard alone cannot repair that parser.

### 3. Keyed entry blocks and retries

**[NOTE] Clean in the reviewed writers:** `hip3-executor/src/hip3_executor/engine.py:139`, `engine.py:355`, and `engine.py:439` mutate only their own intent, untracked, and protection keys. `_enter` at `engine.py:733` directly refuses an existing durable intent before replacing it. Retry announcements are throttled by the intent key; the reconciliation attempt itself recurs once per successful ordinary cycle. Scanner or pre-poll failure prevents that cycle reaching reconciliation, while the retained intent still prevents an entry. This is the actual limit of the phrase "every cycle". Tests inspect concurrent reasons, resolution, and pending-slot preservation.

### 4. Full stop contract, precision, and order counts

**F2 [HIGH] The stop proof accepts a Stop Limit as the required market stop.** `hip3-executor/src/hip3_executor/broker.py:256` checks only whether the type contains `Stop`. A correctly identified reduce-only `Stop Limit` passes all other fields, yet can remain unfilled after a gap. Pinned-source probe replacing only `orderType` returned `True`. Require the exact market-stop type the bracket constructor sends. TVB-34's exact-type repair addresses this historical finding.

**F3 [MEDIUM] Non-finite remaining size passes the coverage proof.** `hip3-executor/src/hip3_executor/broker.py:263` relies on a less-than comparison after `float()` conversion. With otherwise valid fields, both `sz='NaN'` and `sz='Infinity'` returned `True` in isolated probes. NaN makes the insufficiency comparison false; infinity is treated as unlimited coverage. This contradicts the function's missing/unparseable-is-unprotected contract. Require finite positive expected and actual sizes and finite prices before comparison. The existing mutation tests cover missing size, not these values.

**[NOTE] Checks that held and limits:** the verifier uses remaining `sz`, not `origSz`; oversize reduce-only protection is accepted and one-step undercoverage is rejected. Trigger price is compared with the production `MarketMeta.round_px` result with a small numeric tolerance. Side, trigger flag, reduce-only flag, identity, and price are required. `tests/conftest.py:31` makes fake price rounding an identity function, so its tests do not prove production tick rounding. `broker.py:168` consistently uses frontend orders for cached checks, fresh verification, and `requery_flat`; the official Info API documents both order-list variants and the rich fields. There is no recorded live cross-endpoint count comparison in this audit, so runtime count parity is unverified.

### 5. Quantize-then-repair sizing

**[NOTE] Clean by arithmetic and caller inspection:** `hip3-executor/src/hip3_executor/engine.py:711` floors size before checking the venue minimum, repairs upward by a size step, and refuses a repaired ticket above the cap. This fixes theoretical tickets at or just above the minimum that previously floored below it. The fixed-notional path deliberately reaches the same repair. The returned clamp is persisted in the entry receipt. The coarse-step cap and exact-minimum vectors in `tests/test_gate_hardening.py` cover the stated change. This says nothing about post-fill slippage; the added filled-notional receipt and warning explicitly address that separately.

### 6. M4 arm multiset contract

**[NOTE] Clean in direct pinned-source probes:** `analysis/paper/tier_b_t1floor.py:134` defines the independent literal roster. `_resolve_requested_arms` at `:609` rejects empty strings, commas-only input, empty components, duplicate requests, unknown arms, and a mutated declaration missing an arm. A valid explicit subset and the default eight-arm roster succeed. The production loop retains `produced_seq` and checks its cardinality before using collapsed maps for the final gates (`:759`). This gate runs after intermediate per-arm output construction; it is not an atomic publication guarantee, but it does detect the requested production drift.

### 7. Net fields, row-wise fallback, and artifact delta

**[NOTE] Clean for the changed arithmetic:** `analysis/paper/tier_b_exits.py:407` derives both net fields from the unrounded fee. Exact-source probe `realized=-2.99998, fee_sides=1.5` produced displayed fee `0.0188` and net `-3.0187`, distinguishing it from the old staged-rounding result `-3.0188`. The rollup at `:463` applies fallback per row, rejects non-finite inputs, and refuses an open row without either MTM field. The committed historical result files were not regenerated in this range; `docs/HANDOFF.md:162` records that delta and the later rerun obligation. Approval of the code arithmetic is not certification of unchanged old receipts.

### 8. Scanner runner mutation test

**[NOTE] Clean by test/runner inspection:** `hip3-scanner/test/parity_extract_check.test.js:45` copies the real HTML, extractor, and runner into the same relative directory layout, poisons the committed extracted module, and launches the actual runner. It requires the stale-extraction error and absence of the poison's core-load error. This detects deleting the preflight or moving module loading ahead of it; it does not merely test a reimplemented comparison. The merge tree is identical to the reviewed branch tree. No scanner runtime was started.

### 9. HyPaper factual claims and model fidelity

**F4 [MEDIUM] Small dollar risk does not make missing liquidation enforcement irrelevant.** `docs/experiments/tvb31_hypaper_spike.md:90` dismisses that omission because a small risk budget and resident stops are used. Liquidation ordering depends on leverage, maintenance margin, and stop distance, not the absolute dollars risked. A small position can liquidate before its stop, exactly the class later corrected in TVB-34. Retain liquidation as a standing simulator limitation until stop clearance is independently enforced; withdraw the "irrelevant" sentence.

**[NOTE] Public source checks:** fetched the pinned public `b054fdd` Info route, exchange route, and order engine into memory. The required top-level wallet field, trigger-wire validation failure, unguarded `wire.t.limit.tif`, main-universe asset indexing, and ignored dex on local account/order reads all match the spike. Frontend order queries are also implemented. The spike correctly requires integration probes before adoption. This audit did not run HyPaper, measure fill realism, or validate the complete worker/funding/liquidation implementation; those assertions remain source-spike claims, not demonstrated compatibility. Its old `verify_resting` probe name should be updated when implementing against this session's `verify_stop` interface.

### 10. Pine/lookahead surface

**[NOTE] Clean:** none of the three verified diffs changes a Pine file. There is no newly changed `request.security` call to approve. This is a diff-scope conclusion, not a blanket certification of historical Pine.

## 3. Actionable items

1. Malformed position data can prove flat -- HIGH -- hip3-executor/src/hip3_executor/broker.py:151 -- Require a valid assetPositions list and reject malformed rows; retain a regression at every close/flat caller. Confirm TVB-34's later repair rather than reopening it as an unfixed current issue.
2. Stop Limit passes market-stop proof -- HIGH -- hip3-executor/src/hip3_executor/broker.py:256 -- Require the exact market-stop type; retain the later TVB-34 regression.
3. Non-finite size passes stop coverage -- MEDIUM -- hip3-executor/src/hip3_executor/broker.py:263 -- Check finite positive sizes and finite prices before coverage/tolerance arithmetic; add NaN and infinity vectors using real metadata rounding.
4. Missing liquidation enforcement dismissed on dollar size -- MEDIUM -- docs/experiments/tvb31_hypaper_spike.md:90 -- State the actual liquidation/stop-clearance limitation and condition any adoption claim on an independent clearance check.
