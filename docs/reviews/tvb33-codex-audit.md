<!--
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-33 External Audit -- Codex (verbatim source, read CRITICALLY)

> External review of the pinned TVB-33 changes captured 2026-10-10
> (TVB-33 post-session). Plain ASCII; wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-33 -- round-3 preregistration, replay harness, and executor build.
- **Reviewed:** public repo `7a29dad..7ad92f4`; local hip3-executor `4b5d248..d8a07b0`.
- **Reviewer:** GPT-6 / Codex, local tools; more specific runtime model id unavailable.
- **Overall verdict:** NEEDS-CHANGES.
- **Range verification:** `git diff --name-status` run for both ranges before reading their changes. Executor log confirms the derived interval: TVB-32 endpoint through the ready round-3 build immediately preceding TVB-34's starting point. The public interval includes `6e124e2`, the TVB-32 pin. Citations below refer to the pinned endpoint, except explicit current HANDOFF synthesis references.
- **Scope:** read TVB-33 section 7 first, including its existing deep-dive fold. That review is not repeated. The executor exists locally and was reviewed locally; no private account values or access details are reproduced.
- **Evidence:** exact committed source, saved receipt comparisons, in-memory pure-function probes, and fee semantics checked against the official venue API reference. No replay fetch/main routine or trading API was executed. Current public tests: 324 passed, 2 skipped; these are not tests of the historical executor.
- **Finding counts:** CRITICAL 0, HIGH 1, MEDIUM 2, LOW 0. NOTE items are coverage and limitations, not additional actionable findings.

## 2. Verbatim audit

### A. Preregistration, rulings, and the meaning of parity

[NOTE] Checks out as a disclosed, amended characterization contract, not an independent validation sample. Public `docs/HANDOFF.md:1327` starts the deep-dive fold; the pinned round-3 prereg and amendments explicitly change the interpretation of the replay. I checked the twelve rulings, arm definitions, and amendments against implementation. The selected 75-second roll freeze was chosen after observing agreement on this ledger. The journaled drift refusal/pass classification and settlement-time pins condition the replay on historical decisions and exits. A high agreement percentage therefore cannot establish source fidelity, profitable edge, or live safety.

[NOTE] The three fidelity amendments are implemented in the places they claim: executor `analysis/replay/__main__.py:182` passes the per-timeframe freeze into reconstruction and allocation; `analysis/replay/recon.py:433` pins drift sign only where the live decision actually reveals the veto result; `analysis/replay/__main__.py:219` constructs the settlement pin, and `analysis/replay/allocator.py:365` applies it to seat release without replacing replay exit prices or PnL. The conditional interpretation is essential: comparing actual replay entry/exit intervals can show more simultaneous positions than the nominal seat count, because settlement timing follows the journal instead. This is an acknowledged model construction, not a newly discovered deep-dive issue.

[NOTE] The existing A5 and A9 deep-dive findings are visibly folded in public `docs/HANDOFF.md:1327` onward. In particular, the explanation of the empty halfway tier is corrected to the strict trigger gate and synthetic decision-price issue; A9 distinguishes matched trades from admission/seat churn. I did not count those already-folded findings again. The different weekend contrast control is real: executor `analysis/replay/__main__.py:268` applies settlement pins only to the original epoch object; the amended contrast epochs do not silently inherit them.

### B. Ledger replay harness and parity gate

[HIGH] F1 -- Runtime sweep settings are outside the parity pins, so PASS is reusable for a different replay model. Executor `analysis/replay/__main__.py:299` hashes files, ledger inputs, candles, and package source, but never includes `roll_freeze_ms`. The parity command records that setting only as a top-level field at line 371. The run command constructs a context from the current `--sweep-seconds` at line 394 and checks only `ctx.pins()` at line 396. Thus a PASS produced with 75 seconds can authorize an unwatermarked run with zero seconds and unchanged files. An in-memory probe of the actual gate with a saved PASS and unchanged pins returned `(True, 'parity_round2.json verdict PASS')`; the saved freeze was not inspected. This directly weakens the preregistered stop gate. Include normalized runtime model settings in the compared pins, and refuse a mismatch unless explicitly forced and watermarked.

[MEDIUM] F2 -- P1 silently collapses duplicate ledger entries while claiming complete entry parity. Executor `analysis/replay/parity.py:334` assigns ledger pairs into a dictionary keyed by identity and decision index. Only replay positions receive the uniqueness assertion at line 335. The PASS predicate at line 345 checks missing/extra/unmapped keys, not multiplicity or matched cardinality. Pure-function reproduction with two identical ledger pairs, one matching decision, and one replay position returned `ok=True`, `n_ledger=2`, `n_replay=1`, `n_matched=1`, and `pct=50.0`, with empty missing/extra/unmapped lists. This is a latent failure of the gate, not an allegation that the saved ledgers contain duplicates. Reject duplicate keys on both sides and require exact cardinality.

[NOTE] Other gate mechanics checked out within their declared scope. Executor `analysis/replay/parity.py:303` does reject duplicate replay identities. I inspected the complete check assembly: P0 is descriptive; entry identity, timing/reason classifications, P5 tolerances, and validator coverage are separated. Missing validator inputs do not become an unconditional PASS; declared zero-denominator cases are explicit. The report compares pin keys in both directions and ignores only the declared git-head exception. Funding-history files are included through ledger pins. None of this repairs F1 or F2.

[NOTE] The saved weekend P5 failure remains a failure and forced output is watermarked. Independent residual aggregation confirmed that the two named exceptional trades explain most, but not literally all, of the aggregate discrepancy. The remaining trades have a small nonzero residual. Read the receipt's approximate language as approximate; it is not an exact venue-PnL reconstruction. Round-2 agreement and weekend failure must not be combined into a blanket parity claim.

### C. Cost model and receipt arithmetic

[MEDIUM] F3 -- Builder fees are added twice when nonzero. Executor `analysis/replay/costs.py:69` returns `fee + builderFee`; `analysis/replay/__main__.py:290` repeats the same addition for ledger venue totals. The official user-fills API defines `fee` as inclusive of `builderFee`, so the latter is a component, not an additional charge. A synthetic fill with fee 0.04 and builder component 0.01 is charged 0.05 by the pinned helper. Both inspected saved ledgers have zero nonzero builder-fee records, so this does not establish a numerical error in their existing tables. It does bias inferred fee rates and replay net outcomes for a supported nonzero-builder input, and using the same wrong formula on both sides can conceal it in parity. Sum the inclusive fee once and report the component separately.

[NOTE] Funding sign and interval treatment were inspected separately from fee arithmetic. Executor `analysis/replay/__main__.py:293` converts venue cash flow into the declared paid-positive convention. The ledger-specific history pins and declared approximations bound reproducibility; they do not turn a historical funding model into a quote of future funding.

### D. Round-3 executor build and admissions

[NOTE] The live fee-aware gate is wired consistently with the approved build, within its stated approximations. Executor `src/hip3_executor/rules.py:133` computes net reward/risk from percentage reward, percentage risk, and the round-trip fee. At lines 229-241 it gates on the unrounded value, records a rounded value for receipts, and refuses an unavailable fee rate. The configured per-dex fee model and the per-coin shadow are distinct. I traced configuration validation, gate evaluation, and decision journaling at `src/hip3_executor/engine.py:713`; there is no evidence here that the shadow silently changes admission.

[NOTE] DWM, funding, poll, and alternate fee fields are characterization receipts in this build. Executor `src/hip3_executor/engine.py:713` and entry-record construction at line 906 carry the declared fields; the account-parts reporting adjustment at line 260 does not feed the admission calculation. Funding estimates retain their declared directional/time-horizon assumptions. This source review does not verify deployment, venue rounding on an actual order, or realized execution costs.

[NOTE] Scope hygiene: the public interval contains documentation, not a Pine strategy change. No claim of TradingView export parity, profitable edge, or readiness follows from this audit. No sibling files were modified.

## 3. Actionable items

1. F1: Pin runtime sweep/freeze settings in the parity contract -- HIGH -- hip3-executor `analysis/replay/__main__.py:299` -- Include normalized behavior-changing arguments in parity/run pins; test that a changed sweep setting requires a new PASS or an explicit watermarked force.
2. F2: Preserve ledger multiplicity in P1 -- MEDIUM -- hip3-executor `analysis/replay/parity.py:334` -- Assert ledger-key uniqueness before dictionary construction and require ledger, replay, and matched counts to agree.
3. F3: Count inclusive venue fees once -- MEDIUM -- hip3-executor `analysis/replay/costs.py:69`, `analysis/replay/__main__.py:290` -- Remove the additional builder component from charged fees and venue totals; verify with a nonzero-builder fixture.
