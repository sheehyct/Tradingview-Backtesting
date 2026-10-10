<!--
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit is below; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-37 External Audit, second request -- Codex CLI (verbatim source, read CRITICALLY)

> External review of tradingview-backtesting `4560e7c..c0f1826` (the chance comparison: prereg
> with amendments A1 / A2, engine, tests, receipt, ledger card, HANDOFF Product 2, and the census
> refactor exposing `day_events`), captured 2026-10-10 (TVB-37 MID-session, owner-requested).
> Run as `codex exec -s read-only` against the local tree at cff7932 (the review-request pointer;
> the uncommitted book-view work was excluded by the reviewer); work order
> `docs/reviews/REVIEW_REQUEST.md`. Lightly ASCII-normalized; wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md` (TVB-37 entry). Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-37 -- chance comparison
- **Reviewed:** 4560e7c..c0f1826 on main
- **Reviewer:** GPT-6 / Codex
- **Overall verdict:** NEEDS-CHANGES

## 2. Verbatim audit

> Read CRITICALLY. External reviewers can be wrong. This is the external assessment; the critical synthesis belongs in docs/HANDOFF.md.

The corrected condition logic held up under review. I found no additional outcome-based leak in the amended daily class or the weekly/monthly class. Changes are needed for decimal touch fills, statistical presentation, and receipt claims that exceed or contradict the tables.

Verification:

- `uv run --no-sync pytest tests/test_domino_chance.py tests/test_domino_census.py -q -p no:cacheprovider`: **25 passed**.
- Recomputed all **477 committed JSON cells** from the existing saved unit rows: zero field mismatches.
- Regenerated the complete Markdown report in memory from those rows: exact match with committed `chance_tables.md`.
- Compared old and refactored `analyze_coin` on 80 additional hand-generated contiguous/gapped sequences: identical results.
- Ran additional read-only probes for decimal touches, entry-condition invariance, sample differences, censoring, and row uniqueness.
- No repository files were written. The working-tree prereg amendment and concurrent book work were excluded. The only committed change after the reviewed endpoint was the review-request pointer.
- Neither engine was run end to end. Saved-row agreement establishes reporting consistency, not independent candle-to-outcome reproduction.

### 1. Remaining look-ahead

**[NOTE] Corrected condition logic checks out, with the declared retrospective sample qualifications.**

- Daily `entry_class` reads previous complete weekly/monthly levels and running extrema before today, not today's higher-level hits: `analysis/domino/chance.py:151`, `analysis/domino/chance.py:157`, `analysis/domino/census.py:343`.
- The nearest fresh level determines the daily class. Whether the day subsequently reaches it does not enter that decision: `analysis/domino/chance.py:167`.
- Weekly/monthly class uses their own level against yesterday's level. Both prices are already known at the higher-level break. Their `spread` class describes distance already traversed relative to yesterday's level, rather than selecting a daily entry by its subsequent travel: `analysis/domino/chance.py:117`, `analysis/domino/chance.py:123`, `analysis/domino/chance.py:337`.
- `kind` and `flag` use the completed setup bar; year and direction are available at entry: `analysis/domino/chance.py:323`, `analysis/domino/chance.py:338`.
- Month support uses the known daily trigger price and month open. Quarter state explicitly passes `False` for today's break and uses pre-day running extrema: `analysis/domino/chance.py:313`, `analysis/domino/chance.py:318`, `analysis/domino/census.py:365`.
- `stack` is not used as a headline condition or split. `cls_la` is used only in explicitly labelled TRAP tables: `analysis/domino/chance.py:354`, `analysis/domino/chance.py:695`.
- An additional perturbation of today's and subsequent candles preserved the condition columns of existing daily and weekly long units.

`liquid` is deliberately retrospective: the end-of-sample liquidity classification is applied to earlier entries. This is inherited from the census definition and disclosed in `analysis/domino/RECEIPT.md:24`; it is not a historical entry-time liquidity signal. See `analysis/domino/chance.py:761` and `analysis/domino/census.py:536`. Live-universe survivor selection is also explicitly declared.

### 2. Nesting assertion

**[NOTE] Checks out on the accepted contiguous calendar grid.**

On a plain day, yesterday's extreme is included in the current higher bar's pre-day running extreme. If the higher level is still fresh, that running extreme cannot have passed the previous higher bar's level. On Monday or the first of the month, yesterday belongs to the previous higher bar, whose extreme bounds yesterday's extreme.

That establishes the asserted ordering for both directions: `analysis/domino/chance.py:126`, `analysis/domino/chance.py:163`.

The chance runner rejects coins containing missing days, duplicates, or off-grid stamps before building units: `analysis/domino/chance.py:757`. Context also requires an adjacent complete predecessor: `analysis/domino/census.py:323`. The existing nesting vectors and additional old/new extraction comparisons passed.

### 3. Walker

**[MEDIUM] F1: Exact decimal target touches can fail to fill.**

Although comparisons use inclusive operators, the target is calculated with binary floats:

- `analysis/domino/chance.py:202`
- `analysis/domino/chance.py:203`
- `analysis/domino/chance.py:214`
- `analysis/domino/chance.py:217`

Confirmed read-only vectors:

```text
Long:  level=0.10, stop=0.08, high=0.12, low=0.09
Target calculated: 0.12000000000000001
Actual out1: neither
Required out1: one_r

Short: level=0.12, stop=0.14, low=0.10, high=0.13
Target calculated: 0.09999999999999998
Actual out1: neither
Required out1: one_r
```

These are exact decimal one-R touches under the declared model. The prevalence in the committed market results was not measured.

**[NOTE] The other reviewed walker mechanics check out.**

Stop wins when both levels touch; entry-day stop touches count even if they occurred before entry; the entry day is included; a later resolution cannot affect an earlier horizon; incomplete horizons remain censored even after an observed resolution. See `analysis/domino/chance.py:210`, `analysis/domino/chance.py:222`, `analysis/domino/chance.py:230`, and `analysis/domino/chance.py:233`.

MFE/MAE deliberately continue as price travel after trade resolution, matching the declared description: `analysis/domino/chance.py:200`, `analysis/domino/chance.py:218`.

The entry-day pessimism is clearly disclosed in `analysis/domino/CHANCE_RECEIPT.md:42` and `analysis/domino/CHANCE_RECEIPT.md:219`.

### 4. Horizons

**[NOTE] Checks out against the prereg's explicit definition.**

Daily horizons end at `i + N`. Weekly/monthly horizons end on the last day of bucket `b + N`, only when that bucket is complete: `analysis/domino/chance.py:185`, `analysis/domino/chance.py:191`.

Thus "by 1" includes the entry bar and the following bar. This matches the explicit prereg definition, rather than an entry-bar-only interpretation.

The runner's whole-coin gap rejection guarantees bucket adjacency. An entry in the incomplete final higher bucket has no complete future horizon and is censored. Existing weekly and daily horizon vectors passed: `tests/test_domino_chance.py:74`.

### 5. Follow-through

**[NOTE] Implementation checks out; monthly coverage is missing.**

Daily follow-through compares tomorrow with the entry day. Higher-timeframe follow-through requires both the entry bucket and next bucket complete: `analysis/domino/chance.py:248`, `analysis/domino/chance.py:252`.

The with/against mapping correctly reverses for shorts: `analysis/domino/chance.py:259`. Existing daily direction vectors and weekly end-to-end vector passed: `tests/test_domino_chance.py:112`, `tests/test_domino_chance.py:144`.

### 6. Unit separation across timeframes

**[NOTE] Checks out clean.**

Every analytical table filters by timeframe before calculating its cells:

- Pattern tables: `analysis/domino/chance.py:457`
- Differences: `analysis/domino/chance.py:494`
- Hypothesis 1: `analysis/domino/chance.py:557`
- Splits: `analysis/domino/chance.py:595`
- Variant: `analysis/domino/chance.py:624`
- JSON cells: `analysis/domino/chance.py:650`

Combined unit totals are bookkeeping, not pooled chances. The Monday vector produces separate daily and weekly units. Saved rows contained zero duplicate `(sample, coin, date, direction, tf)` keys.

### 7. Variant stop

**[NOTE] Checks out clean, subject to F1's shared walker defect.**

The variant uses the previous complete week's opposite extreme, requires a strictly correct-side stop, and counts wrong-side exclusions: `analysis/domino/chance.py:371`, `analysis/domino/chance.py:374`, `analysis/domino/chance.py:381`.

The variant table compares primary and variant arithmetic on the same eligible subset: `analysis/domino/chance.py:624`, `analysis/domino/chance.py:630`.

The different R distance and target are prominently disclosed: `analysis/domino/CHANCE_RECEIPT.md:165`. No equal-target or trading-performance conclusion is claimed.

### 8. Cell statistics and difference intervals

**[MEDIUM] F2: Reported counts and small-cell treatment do not follow the actual horizon denominators.**

`cell` correctly excludes censored and n/a outcomes and stores `n1`, `n3`, and `n5`: `analysis/domino/chance.py:395`, `analysis/domino/chance.py:400`.

The Markdown tables display total `n`, however, and greying uses total `n` rather than the applicable valid count: `analysis/domino/chance.py:438`, `analysis/domino/chance.py:472`, `analysis/domino/chance.py:537`.

Concrete example:

- Monthly reversal `exact_shared` displays `n=37` and an ungreyed five-bar chance of 33.3%.
- Its actual five-bar denominator is **27**, below MIN_CELL.
- Monthly reversal `near` displays `n=42`; its five-bar denominator is **22**.

See `analysis/domino/results/chance_tables.md:287` and `analysis/domino/results/chance_tables.md:288`.

Difference, hypothesis, variant, and split tables also omit distinct-date counts. Hypothesis greying considers only total exact-group size, not the comparator's size: `analysis/domino/chance.py:583`. These presentations fall short of the count/date contract in `docs/experiments/tvb37_chance_comparison_prereg.md:106`.

Stops and next-bar proportions are shown without their own Wilson intervals, despite the literal "every proportion" requirement.

**[LOW] F3: LIQUID bookkeeping repeats full-universe counters.**

The LIQUID report receives `counts_venue` unchanged: `analysis/domino/chance.py:777`.

Consequently, its heading reports full-universe censored counts:

```text
Displayed LIQUID censored by 5: D=1371, W=1659, M=1218
Actual LIQUID censored by 5:   D=673,  W=838,  M=611
```

See `analysis/domino/results/chance_tables.md:507`. Dropped/wrong-side counters are likewise not LIQUID-specific.

**[NOTE] Core formulas check out.**

Wilson arithmetic, subtraction sign, horizon-specific valid denominators, nested THIRD/STRICT masks, and timeframe-specific comparison bases are correct: `analysis/domino/chance.py:262`, `analysis/domino/chance.py:279`, `analysis/domino/chance.py:418`, `analysis/domino/chance.py:501`, `analysis/domino/chance.py:512`.

The normal difference intervals implement the prereg's approximation. Their independence assumption remains a disclosed limitation, not evidence of cluster-adjusted significance.

### 9. Venue era

**[LOW] F8: Later zero-volume days are retained but not explicitly explained in the chance receipt.**

The implementation removes only the prefix before the first positive-volume day: `analysis/domino/chance.py:85`, `analysis/domino/chance.py:87`.

A probe with volumes `[0, 1, 0]` correctly retains the last two days. The chance receipt explains the prefix removal but does not explicitly state that later zero-volume candles remain eligible: `analysis/domino/CHANCE_RECEIPT.md:49`, `analysis/domino/CHANCE_RECEIPT.md:225`.

**[NOTE] The ALL check sample is present and separately calculated:** `analysis/domino/chance.py:762`, `analysis/domino/chance.py:765`, `analysis/domino/chance.py:778`.

### 10. Census refactor

**[NOTE] Checks out within the extraction-only scope.**

The diff preserves:

- Previous-day and predecessor adjacency checks.
- Strict hits and higher-bar freshness.
- Direction ordering.
- Empty-event omission.
- Missing-yesterday counts.
- Nesting checks.
- Unknown-kind counters and shape accounting.
- Break-day and rank-2-plus-day counts.

See `analysis/domino/census.py:398`, `analysis/domino/census.py:455`, `analysis/domino/census.py:465`, `analysis/domino/census.py:475`, and `analysis/domino/census.py:530`.

Source comparison and 80 additional old/new comparisons found no difference. I did not independently reproduce the reported full-census byte-identical run.

### 11. Receipt honesty

**[MEDIUM] F4: The two-percentage-point sample-stability claim is false.**

`analysis/domino/CHANCE_RECEIPT.md:60` says ALL and LIQUID headline shares stay within two points of venue era wherever a cell has 100+ units.

Counterexamples with more than 100 valid observations:

- Plain daily outside STRICT, by 1: venue era **23.9%**, LIQUID **29.9%**, approximately **+5.9 points**. See `analysis/domino/results/chance_tables.md:61` and `analysis/domino/results/chance_tables.md:563`.
- Weekly reversal THIRD within1, by 5: venue era **33.3%**, ALL **39.7%**, approximately **+6.3 points**. See `analysis/domino/results/chance_tables.md:183` and `analysis/domino/results/chance_tables.md:1055`.

**[MEDIUM] F5: Several synthesis sentences overgeneralize the comparisons.**

- "Across splits nothing flips" and continuation stacks remaining within two points contradict the reported **+4.7 points in 2023**: `analysis/domino/CHANCE_RECEIPT.md:174`, `analysis/domino/CHANCE_RECEIPT.md:207`, `analysis/domino/results/chance_tables.md:430`.
- "The hammer shape lifted every pattern by four to seven points" omits outside setups, whose plain THIRD uplift by 3 is approximately **2.6 points**: `analysis/domino/CHANCE_RECEIPT.md:200`, `analysis/domino/results/chance_tables.md:52`, `analysis/domino/results/chance_tables.md:57`.
- The HANDOFF's general "with fewer stops" does not hold for daily continuation THIRD: **48.3% stopped versus 46.0% all flags**. See `analysis/domino/CHANCE_RECEIPT.md:116`, `analysis/domino/CHANCE_RECEIPT.md:117`, and `docs/HANDOFF.md:162`.
- "One in four to one in three plain daily units" excludes the displayed continuation and outside rates, **18.3% and 13.9%**: `analysis/domino/CHANCE_RECEIPT.md:204`.
- Hypothesis 1 was expressly a **daily-unit** hypothesis: `docs/experiments/tvb37_chance_comparison_prereg.md:105`. Calling it "supported on the weekly" extends its scope. The weekly result is a descriptive comparison with different R distributions, not an isolated shared-open effect: `analysis/domino/CHANCE_RECEIPT.md:190`.

The R-size and clustering caveats are present and useful. They do not make these broader sentences accurate. Related summaries appear in `docs/ARM_LEDGER.md:566` and `docs/HANDOFF.md:164`.

**[LOW] F6: The claim that the original exact class was clean/unaffected is inaccurate.**

The original daily class takes the largest gap among levels that broke today: `analysis/domino/chance.py:125`. A same-price weekly stack can therefore leave the original exact cell when the day also reaches a farther monthly level. Original exact-cell membership consequently depends on subsequent travel.

Saved venue-era daily rows confirm:

- **292** current `exact_shared` units were originally near/within1/spread.
- **5** current `exact_plain` units were originally within1/spread.

The corrected nearest-fresh-level class fixes this. The historical claims should nevertheless be corrected at `analysis/domino/CHANCE_RECEIPT.md:22` and `docs/experiments/tvb37_chance_comparison_prereg.md:145`.

**[NOTE] The TRAP tables are unmistakably labelled, and the headline arithmetic reproduces exactly.** See `analysis/domino/results/chance_tables.md:68`.

### 12. Tests

**[LOW] F7: Important regression vectors remain absent.**

The nine chance tests pass, but the suite lacks explicit vectors for:

- Decimal equality fills on both directions, including F1.
- Monthly horizons and follow-through.
- Weekly/monthly class coverage beyond weekly near/shared-exact.
- A2 month/quarter invariance under current-day outcome changes.
- `cell` censored/n/a denominators and horizon-aware greying.
- `flag_mask` with a non-default index.
- Later zero-volume days.
- Variant wrong-side exclusions and their counter.

See `tests/test_domino_chance.py:36`, `tests/test_domino_chance.py:74`, `tests/test_domino_chance.py:89`, `tests/test_domino_chance.py:137`, and `tests/test_domino_chance.py:180`.

Daily censoring and a short-side walker are already covered; the missing short case is exact equality, not short walking generally.

The original census-rank/class accounting test declaration also needs reconciliation with A1's changed entry-time classes: `docs/experiments/tvb37_chance_comparison_prereg.md:114`.

### 13. Public-repo hygiene

**[NOTE] Checks out within the reviewed range.**

The pinned added-line secret scan found zero findings across the ten changed files. No new secret, host/IP/account value, or unrelated personal remark was identified.

Both `trades.csv.gz` and `chance_run.log` are ignored; verified with `git check-ignore`. See `.gitignore:108` and `.gitignore:109`.

### 14. request.security

**[NOTE] Checks out clean.**

The pinned changed-file inventory contains no Pine file. `git diff --name-only 4560e7c..c0f1826 -- '*.pine'` returned no paths. No `request.security` implementation changed in scope.

## 3. Actionable items

1. F1: Decimal target touches can miss fills -- **MEDIUM** -- `analysis/domino/chance.py:202` -- Calculate price thresholds using exact decimal arithmetic consistent with venue decimal prices; add long and short equality vectors, then regenerate affected results.

2. F2: Counts and greying use total units rather than valid horizon samples -- **MEDIUM** -- `analysis/domino/chance.py:438` -- Display valid counts and corresponding date counts per horizon; grey each comparison using both valid denominators. Supply the declared proportion intervals or explicitly amend the reporting contract.

3. F3: LIQUID diagnostics reuse full-universe counters -- **LOW** -- `analysis/domino/chance.py:777` -- Accumulate LIQUID-specific diagnostics, or label inherited counters as full-universe bookkeeping.

4. F4: Sample-stability claim contradicts committed cells -- **MEDIUM** -- `analysis/domino/CHANCE_RECEIPT.md:60` -- Replace the blanket two-point assertion with a correctly scoped summary and the observed exceptions.

5. F5: Receipt and summary claims overgeneralize -- **MEDIUM** -- `analysis/domino/CHANCE_RECEIPT.md:184` -- Scope statements to the actual patterns, horizons, and splits; describe weekly shared-open results as confounded descriptive comparisons; synchronize ledger and HANDOFF wording.

6. F6: Original exact-class membership was outcome-dependent -- **LOW** -- `analysis/domino/CHANCE_RECEIPT.md:22` -- Explain that a farther same-day break could remove a same-price stack from the old exact cell; correct the prereg's historical claim.

7. F7: Regression coverage omits important boundaries -- **LOW** -- `tests/test_domino_chance.py:180` -- Add the missing vectors listed in focus area 12 and update the obsolete pre-A1 accounting declaration.

8. F8: Later zero-volume eligibility is implicit -- **LOW** -- `analysis/domino/CHANCE_RECEIPT.md:49` -- State explicitly that only the initial zero-volume prefix is removed and later zero-volume days remain.
