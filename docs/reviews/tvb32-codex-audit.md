<!--
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-32 External Audit -- Codex (verbatim source, read CRITICALLY)

> External review of the pinned TVB-32 changes captured 2026-10-10
> (TVB-32 post-session). Plain ASCII; wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-32 -- entry invalidation repair and overnight analysis.
- **Reviewed:** public repo `5b194a2..7a29dad`; local hip3-executor commits `fd4db97`, `35a73a4`, `2dc9490`, `68dca79`, `cbea184` (merged as `e2a91ad`), `4b5d248`, each inspected as its parent-to-commit diff. Executor endpoint source at `4b5d248`.
- **Reviewer:** GPT-6 / Codex, local tools; more specific runtime model id unavailable.
- **Overall verdict:** NEEDS-CHANGES.
- **Range verification:** `git diff --name-status` run for the public range and every listed executor commit before reading. The public range changes exactly three documentation files; `analysis/round2.py` is in hip3-executor. Both repositories exist locally. Citations below use endpoint line numbers, qualified by repo.
- **Evidence:** exact-source inspection, pure-function probes, independent fill-size/direction assertions, snapshot row comparison, and committed JSON/prose checks. No execution of the analysis main routine, no account or trading API calls, and no private numerical account data copied here. Current public tests: 324 passed, 2 skipped; no claim that these test the historical executor.
- **Finding counts:** CRITICAL 0, HIGH 1, MEDIUM 3, LOW 1. NOTE checks are not counted as defects.

## 2. Verbatim audit

### Entry-gate fix, deployment line endings

**[NOTE] Clean for the specified mechanism:** `hip3-executor/src/hip3_executor/rules.py:187` rejects the candidate's own timeframe when `formingType == '3'`, except `rev3`. It sits after in-force/target checks and before stop geometry, matching the already-existing invalidation exit. The five added tests distinguish a normal setup, the explicit Rev Strat exception, another timeframe, and the scanner's string contract. This fixes entry on an already invalidated bar without changing when a break becomes live. It does not resolve scanner mid-union versus trade-candle differences. `hip3-executor/.gitattributes:5` pins text to LF for archive deployment; no remote deployment was attempted by this audit.

### Spot hold and equity reading

**[NOTE] Checks out for the recorded isolated-account snapshot:** recomputed the relationships inside the pinned `analysis.json` reconciliation object without emitting balances. Spot hold approximately equals the two dexes' isolated margins, and free spot plus those account components approximately equals spot total. The reporting defect and the proposed isolated-account correction follow from those observations. `hip3-executor/analysis/round2.py:620` makes sequential live reads when its main routine is rerun; those are a timestamped observation, not an atomic snapshot or a universal account-mode identity. The analysis correctly does not trade on that display. No present account-state claim is made here.

### Flip proxy, coupled-open split, decoupled counterfactual

**F1 [HIGH] The decoupled counterfactual disables every continuity flip forever.** `hip3-executor/analysis/round2.py:510` requires every timeframe to have age at least `COUPLING_MIN=60` minutes. A 15-minute forming bar has age below 15 minutes and an hourly bar below 60 minutes. Therefore the `ok` branch at `:520` is unreachable regardless of prices. An exhaustive one-day minute-grid check returned `False` for both timeframes' ability to pass. The nine recorded outcomes are four stops, one target, four open marks, and zero flips. This is a bracket-only hold after the observed exit, not a working delayed/coupling-aware flip rule. `hip3-executor/runs/2026-08-31_round2/ANALYSIS.md:78` and `:92` consequently cannot support the conclusion that waiting an hour to let the bars mature loses more than it saves. Define which slow/shared opens are suppressed and how neutral/exempt votes work, demonstrate a reachable flip, then rerun the comparison and change the prose.

**[NOTE] Proxy and descriptive split:** the reconstruction explicitly uses the exit fill price versus venue forming opens, whereas the live decision used scanner mids. The 14/18 agreement limitation is disclosed. The fresh-bar split measures elapsed time since a 4h boundary; its 25% reference is a uniform-time comparator, not a tested event-time null. The observed split and binding margins are descriptive. They do not establish that the boundary caused an exit, nor do they rescue F1.

### Fill matching and entry accuracy

**[NOTE] Clean on the recorded closed trades:** independently paired all 28 closed trades from pinned journal objects, matched entries by client id, and reproduced both entry and exit size assertions. All matched closing fills also had the expected long/short direction. Two open positions were excluded. `hip3-executor/analysis/round2.py:279` uses client-id entry matching; `:290` bounds exit matching by entry time and the earlier of the next entry or the exit-plus-tolerance limit. This is sufficient for the inspected evidence; equal size alone would not prove identity under arbitrary external account activity.

**[NOTE] Accuracy census is properly split:** `hip3-executor/analysis/round2.py:395` reports strict pre-entry-minute and inclusive-minute classifications separately. The strict classification avoids claiming the entry minute's completed high/low was already visible. Setup bars are closed and strict-break classified. The 28/28 setup/trigger claims are against venue bars, not complete scanner-state fidelity. Thin-bar discrepancies and the 1-3 trigger ruling remain explicit. The headline's older 27-entry denominator is addressed below.

### Pool simulation, temporal limits, and receipt tables

**F2 [MEDIUM] A pre-entry or pre-exit wick can be scored as a later counterfactual fill.** `hip3-executor/analysis/round2.py:172` includes the whole minute containing `start_ms`, then returns that minute's open time. Pinned-source vector: candle at time 0 with high 110 and low 90, long entry at 50 seconds, stop 95, target 105 -> `('stop', 0)`. The fill is booked before the proposed entry; the candle provides no evidence that the stop happened after it. The same helper is used for post-exit first touch. `excursions` at `:189` similarly includes complete boundary-minute ranges, and `price_at` at `:202` can read a close not yet completed at the requested instant. Stop-first is a same-bar ordering convention, not a cure for pre-start data. Exclude ambiguous boundary minutes or expose both bounds, enforce nonnegative durations, and use only a completed close for an as-of mark.

**F3 [MEDIUM] The gate census omits 777 refusal rows from the claimed window.** `hip3-executor/analysis/round2.py:220` consumes the sliced decisions file without a completeness receipt. Comparing the pin with the later closed-ledger snapshot restored exactly 777 rows within the old snapshot interval, all `skip`, confirming the TVB-33 handoff disclosure. The trade count is unaffected, but pool counts, setup selection, and the sparse flip timeline are incomplete. At `hip3-executor/runs/2026-08-31_round2/ANALYSIS.md:315` the funnel is presented as the window's count. Keep the historical file, but watermark these populations as incomplete and issue a corrected, separately pinned census from the repaired slice. This is a known later-discovered limitation, not a newly alleged loss of trade rows.

**F4 [MEDIUM] The stated 48-hour horizon is a duration-dependent exclusion, not a horizon mark.** `hip3-executor/analysis/round2.py:1190` walks until any eventual touch/flip or the cache end, then `:1201` discards the setup if that endpoint exceeds 48 hours. A trade still open at hour 48 and stopped at hour 49 vanishes; a comparable trade stopped at hour 47 remains. A horizon census must mark the former at hour 48 or explicitly treat it as censored, not select on later resolution. The pinned pool objects report zero `dropped_over_cap`, so this code defect is latent in the committed sample; it matters to the claimed model and future reruns. Clip all paths to the earlier of snapshot and declared horizon, and state the denominator for censored cases.

**F5 [LOW] The prose table and headline retain obsolete denominators.** `hip3-executor/runs/2026-08-31_round2/ANALYSIS.md:294` lists 1,524 aligned R:R-refused setups; the final pinned JSON records 1,536 unique setups, 1,535 simulated, and one without candles. `ANALYSIS.md:32` still says four of 27 entries while the final accuracy census is 28. Also, `hip3-executor/analysis/round2.py:1313` computes the R:R distribution from all R:R refusals, even though it attaches those statistics to the aligned subset. Refresh the table from the final object, distinguish unique/simulated/missing counts, and use the same aligned filter for its statistics.

**[NOTE] Other pool boundaries:** the code labels no-seat/no-cooldown comparisons as an opportunity census and does not implement a controlled allocator swap. The pinned rows are chronological and lie within the stated start/snapshot interval; direct checks found zero timestamp descents and zero non-earliest `setdefault` choices within that file. That ordering result does not establish completeness (F3). Claims that a gate "cost nothing measurable" should remain population descriptions, especially given F1-F4, not isolated causal effects or evidence for promotion.

### Public documentation and Pine

**[NOTE] Clean in scope:** reviewed the public handoff and request deltas against the private source, retaining the run-live-at-snapshot qualification. The entry repair's later deployment status is distinguished from the overnight draft. No Pine file changes in any verified range, hence no new `request.security` surface.

## 3. Actionable items

1. Decoupled flip is unreachable -- HIGH -- hip3-executor/analysis/round2.py:510 -- Specify a reachable coupling rule, add an eventual-flip vector, recompute the nine cases, and withdraw the waiting-hour conclusion until then.
2. Boundary-minute history used after the start instant -- MEDIUM -- hip3-executor/analysis/round2.py:172 -- Censor or bound ambiguous start/end minutes, prohibit negative holds, and use completed closes for as-of marks.
3. Incomplete refusal snapshot -- MEDIUM -- hip3-executor/analysis/round2.py:220 -- Preserve and watermark the old snapshot; regenerate an explicitly separate census with the 777 restored rows and a completeness receipt.
4. Horizon implemented as late-outcome exclusion -- MEDIUM -- hip3-executor/analysis/round2.py:1201 -- Clip at the declared horizon/snapshot and mark or censor unresolved setups without conditioning inclusion on a later exit.
5. Stale or mixed census denominators -- LOW -- hip3-executor/runs/2026-08-31_round2/ANALYSIS.md:294 -- Generate final table counts from the pinned object and apply the aligned population filter consistently to its R:R statistics.
