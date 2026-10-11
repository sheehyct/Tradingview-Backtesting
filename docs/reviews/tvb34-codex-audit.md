<!--
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-34 External Audit -- Codex (verbatim source, read CRITICALLY)

> External review of the pinned TVB-34 changes captured 2026-10-10
> (TVB-34 post-session). Plain ASCII; wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-34 -- mechanics fold, feasible-fill contrast, and round-3 admission package.
- **Reviewed:** public repo `7ad92f4..00d243e`; local hip3-executor `d8a07b0..5cd2b0d`.
- **Reviewer:** GPT-6 / Codex, local tools; more specific runtime model id unavailable.
- **Overall verdict:** NEEDS-CHANGES.
- **Range verification:** `git diff --name-status` run for both exact ranges before reading. The private sibling exists locally. Citations use the respective pinned endpoints.
- **Evidence:** source and diff inspection, official venue liquidation/API reference, offline AST-extracted arithmetic and lifecycle probes, and saved receipt inspection. Public current-checkout tests: 324 passed, 2 skipped. Historical executor tests were inspected, not run. No venue API, deployment, or trading operation was performed.
- **Finding counts:** CRITICAL 0, HIGH 2, MEDIUM 1, LOW 0. NOTE items are coverage/limitations, not additional actionable findings.

## 2. Verbatim audit

### A. Liquidation formula, clearing leverage, and venue protection

[NOTE] Formula and integer search check out under the explicitly stated isolated, tier-zero, pre-fee assumptions. Executor `src/hip3_executor/rules.py:144` takes maintenance fraction as half the reciprocal of maximum leverage. Lines 152-174 implement long `(1/L-m)/(1-m)`, short `(1/L-m)/(1+m)`, and descend from the capped leverage to the largest integer satisfying stop distance <= buffer times liquidation distance. I checked the algebra against the official venue liquidation formula and ran the actual pure functions: a synthetic maximum-10, leverage-10 case gives 5.2631579% long and 4.7619048% short. Missing maintenance information is refused at lines 394-398. Actual venue liquidation price is separately receipted and compared against the stop at `src/hip3_executor/engine.py:945`; the warning is not an automatic flatten policy. None of this proves clearance after arbitrary fees, funding, collateral changes, or mark movement.

[HIGH] F1 -- The malformed-flat repair validates the outer list but still accepts malformed position entries as proof of absence. Executor `src/hip3_executor/broker.py:169` rejects a missing/non-list `assetPositions`, but lines 175-177 turn an absent position or absent size into zero. Exact-function probes returned `{}` for both `{'assetPositions':[{}]}` and `{'assetPositions':[{'position':{'coin':'SYNTH'}}]}`. These responses are unknown, not authoritative flatness. A fresh close proof or kill-flat proof built from this parser can still declare absence and allow protection/state cleanup after a malformed response. This is an incomplete fold of the earlier malformed-flat finding, distinct from re-reviewing the old implementation. Validate every row, position object, required coin and finite size before using the aggregate as a safety proof.

[NOTE] The stop-type repair itself is correctly narrowed: executor `src/hip3_executor/broker.py:309` now requires exactly Stop Market rather than accepting any type containing Stop. This closes the Stop Limit acceptance reported for TVB-31. The broader stop contract still depends on valid venue data; this audit does not reinterpret a source predicate as an actual live stop-placement test.

### B. Weekly-dot verdict in both gate and flip

[NOTE] The intended gate/exit symmetry checks out. Executor `src/hip3_executor/rules.py:95` derives each selected dot from forming close versus open, returns mixed for a missing/non-numeric slot, and makes a flat dot break unanimity. The original four-dot stack preserves the served scanner verdict at line 119; the five-dot configuration is recomputed. Entry requires `extra['stack'] == direction` at line 407, while `src/hip3_executor/engine.py:535` calls the same stack helper and exits only on unanimous opposition. Pure-function probes confirmed up, flat/mixed, and missing/mixed cases. Mixed holds a position and cannot admit a new one. This is a comparison of served fields and logic, not proof of scanner candle freshness or TradingView fidelity.

### C. Partial-close VWAP, retry behavior, and restart

[NOTE] The arithmetic and persistence of a successfully booked fragment check out in the covered path. Executor `src/hip3_executor/engine.py:497` catches PartialClose from a software exit; lines 505-514 append price/size and immediately save state. The state writer uses replacement at line 222. Lines 652-658 compute the weighted exit price across fragments and the final residual. An offline extraction of that exact arithmetic, with the record passed through JSON serialization/reload, produced 96 for four units at 90 plus six units at 100. This establishes arithmetic and data survival, not a successful full process-crash/restart integration test.

[HIGH] F2 -- Protection-loss partial closes bypass fragment bookkeeping and become unretryable size mismatches on the next poll. Executor `src/hip3_executor/engine.py:468` calls market_close after stop restoration fails, but its generic exception handler at line 472 swallows PartialClose without `_book_fragment`. The record keeps its original size. On the next poll, the residual differs from `rec['sz']`, so lines 423-436 announce mismatch and continue BEFORE checking a stop, restoring one, or retrying the close. In a synthetic two-poll probe, an original size of 10 partially reduced to 6 produced `protection_flatten_failed`, then `protection_mismatch`; close calls and stop checks both stayed at one after a simulated state reload, and no fragments existed. The remaining exposure can stay unprotected indefinitely without operator intervention. Blocking new entries does not close or protect it.

The new software-exit fragment path also leaves `rec['sz']` as original size, so its legitimate residual receives the same mismatch classification on the next protection poll. Another software close occurs only if its transient exit condition still holds. Distinguish original size from expected residual, persist pending close intent and execution fragments, and route every close caller through the same resumable reconciliation path. A known fill followed by a failed fresh-position query also needs retained execution evidence rather than losing the fill inside a generic exception. The existing two-call VWAP test does not exercise these intervening poll/restart conditions.

### D. Amendment j and the feasible-fill twin contrast

[NOTE] Amendment j is coherent as a changed observation/fill convention, with an explicit future-conditioned population limitation. Executor `analysis/replay/one_three.py:181` sets the synthetic decision mid to the cross minute's close and keeps the halfway line as trigger. `runs/2026-09-04_replay1/PREREG.md:232` explicitly supersedes filling at the halfway line: fills now use the decision price. A candle closing back inside the trigger is refused by the strict gate. The same amendment at lines 245-249 states that candidates are harvested from setups that later completed a 3. Therefore this remains a retiming census conditional on the future, not a prospective halfway strategy. The old impossible equality gate is repaired, but its fix does not remove that selection bias.

[NOTE] The public twin change is limited to the intended arm-mode entry points. Public `analysis/paper/engine.py:324` defaults `entry_fill` to level; the new branches at lines 776 and 797 use max(level, open) for longs and min(level, open) for shorts. The package entry path is unchanged in this diff. `analysis/paper/tier_b_exits.py:847` redirects the feasible run to a separate default output directory, and line 995 records the mode in the manifest. I inspected the long/short test vectors and compared the default-path diff. The saved feasible receipt withdraws the old control ranking rather than presenting the feasible numbers as TradingView validation. This is a candle-feasible fill bound, not a spread/slippage/queue model. The missing July feasible anchor is explicitly listed as open in public `docs/HANDOFF.md:71` at this pin.

### E. Admission changes, shadows, and receipt claims

[MEDIUM] F3 -- The promised invalidated-sponsor shadow is computed and then dropped before journaling. Executor `src/hip3_executor/rules.py:280` computes the old license's sponsor when the new invalidation rule rejects it and places it in `extra['backing_invalidated']` at line 290. The decision writer at `src/hip3_executor/engine.py:742` enumerates fields through line 779 and never includes that key. Public `docs/HANDOFF.md:66` says the close-out replay will read this field journaled-first; executor `runs/2026-09-04_replay1/PREREG.md:255` likewise says live rows journal it. Source tracing shows the data never reaches those decision rows. A pure rule test asserting the extra field cannot validate this end-to-end receipt promise. Persist the field on the decision and test the actual journal record.

[NOTE] The three named admission changes are visibly active and distinct from the declared rank/session shadows: net fee floor, five-dot alignment, and seat count. Public `docs/experiments/tvb33_round3_prereg.md:350` declares the weekly stack and line 360 explicitly denies attributing the whole-book result to one change. Rank, sheet continuity, and session are emitted at executor `src/hip3_executor/engine.py:770`; they are not consulted as hidden selection gates in this range. Mechanics repairs also alter feasible admissions and leverage, so a future causal comparison must preserve those rule epochs rather than treating the phrase three changes as an exhaustive equality of executable models. F3 prevents one promised mechanical counterfactual from being reconstructed journaled-first.

[NOTE] Go-live and agent-pruning statements were checked as documented historical claims only. No deployment, account state, or order authorization was revalidated. Public artifacts here remain characterization and bug-finding evidence, not a recommendation to trade.

## 3. Actionable items

1. F1: Reject malformed inner position records before proving flatness -- HIGH -- hip3-executor `src/hip3_executor/broker.py:175` -- Validate the row/object, required coin, and finite signed size; return unknown by raising on any malformed member. Add missing-position and missing-size fixtures through close and kill-flat proof callers.
2. F2: Reconcile partial closes across every caller and restart -- HIGH -- hip3-executor `src/hip3_executor/engine.py:468`, `src/hip3_executor/engine.py:423` -- Persist execution fragments and pending close intent; track expected residual separately from original size; retry or protect the residual after reload instead of short-circuiting as an unexplained mismatch.
3. F3: Save the invalidated-sponsor counterfactual -- MEDIUM -- hip3-executor `src/hip3_executor/engine.py:742` -- Journal `backing_invalidated` from extra and verify the emitted decision row, including a refusal caused only by an invalidated sponsor.
