<!--
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-37 Close-out External Audit -- Codex (verbatim source, read CRITICALLY)

> External review of the pinned TVB-37 close-out changes captured 2026-10-11
> (TVB-37 post-session). Plain ASCII; wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-37 close-out -- audit folds, equal-size book, R matching, chart page, and closing documentation.
- **Reviewed:** public repo `ea58c6c..9e0f95e`, emphasizing unreviewed `4560e7c`, `cff7932`, `dadf8ef`, and `9e0f95e`. Prior reviewed ranges `ecc4d6c..8b800a7` and `4560e7c..c0f1826` were checked for disposition of their findings, not reviewed anew. No sibling-repo work and no TVB-36 review.
- **Reviewer:** GPT-6 / Codex, local tools; more specific runtime model id unavailable.
- **Overall verdict:** NEEDS-CHANGES.
- **Range verification:** `git diff --name-status` checked the exact close-out interval and both prior subranges before source inspection. All citations below refer to `9e0f95e`, unless another pin is explicitly named.
- **Evidence:** committed source/diffs and receipts; current source equality to the pinned four domino modules confirmed before imports; offline pure-function probes; local saved unit rows and cached closing prices as supplemental evidence. All 233 saved book cells, both horizons, 12 curves, and the saved R-matched summary statistics reproduced within numerical tolerance. This checks reporting consistency, not independent candle-to-outcome fidelity. Neither census nor chance main was run, and no public API was called.
- **Tests:** current public suite 324 passed, 2 skipped, with bytecode/cache writing disabled. Existing tests inspected for scope; no tests or implementation files were edited. The chart page has no committed test and was not browser-rendered or published by this review.
- **Finding counts:** CRITICAL 0, HIGH 0, MEDIUM 7, LOW 2. NOTE items are coverage/limitations, not additional actionable findings.

## 2. Verbatim audit

### A. Book arithmetic, censoring, cumulative sums, and drawdown

[NOTE] Return arithmetic checks out for the declared unit model. `analysis/domino/book.py:94` awards +R% and +1R on one R, lines 96-97 award -R% and -1R on a stop, and lines 99-101 apply the correct direction sign to the horizon-close move otherwise. Censored outcomes get no return at line 103 and `book_cell` excludes them at line 114. A mirrored short-side mark-to-market vector returned +0.507614% for a fall from 98.5 to 98; a separate cell probe retained one valid trade and excluded one censored trade. The existing three vectors cover long mark-to-market, resolution payoffs, a censored unit, one positive-start cumulative path, and one matching example. They do not cover these short/cell-censor cases, zero-start drawdown, matching coverage failure, or downsampling.

[MEDIUM] F1 -- Drawdown omits the initial zero and understates loss from inception. `analysis/domino/book.py:122` subtracts `cum.cummax()` without admitting zero as the initial high-water mark. A synthetic one-trade loss of 2% on the declared equal-size unit returns max drawdown 0 instead of -20; losses of 2% then 3% return -30 instead of -50. The existing test starts positive and cannot expose this. Reconstructing returns from the saved venue-era units and local horizon closes reproduced every stored book field under the existing formula; seeding the peak with zero changed 110 cell/horizon drawdowns. Fix with a zero-seeded high-water mark and regenerate the cells/tables/page inputs. This is drawdown of the declared entry-date outcome sum, not a claim about actual account equity.

[NOTE] Date aggregation and dollars are otherwise consistent: `book.py:120` sums fixed-notional returns by ENTRY date and sorts before accumulation. The receipt at `analysis/domino/BOOK_RECEIPT.md:19` explicitly denies an account-balance interpretation. Outcomes may be known only weeks/months later and positions overlap; these curves are a retrospective attribution of final outcomes to entry dates, not a tradable equity path or a daily mark-to-market portfolio. Drawdown cannot support a capital/risk-of-ruin conclusion even after F1 is repaired.

### B. R-matched reweighting, coverage, and uncertainty

[NOTE] The weighting algebra checks out when overlap exists. `analysis/domino/book.py:208` selects the daily plain base and the higher-timeframe non-stacked base; lines 223-225 compute base quintiles and put equality on the right side with searchsorted. Lines 253-255 use stacked bin shares for both the mean difference and the squared-weight binomial variance. Renormalization at lines 257-259 is algebraically correct for the covered subset, including the variance scaling. An offline partial-overlap probe reported covered=0.1 and the expected conditional difference. All saved matched statistics reproduce; every saved matched row with a defined coverage field has full coverage. This is coarse distribution matching within five bins, not exact matching of continuous R, coin, date, or regime. The normal 1.96-SE interval assumes independent units and does not estimate clustered uncertainty.

[MEDIUM] F2 -- Zero common support divides by zero; partial support is hidden in the displayed interpretation. At `analysis/domino/book.py:258`, used can be zero. A base of 30 units all at R=10 and ten stacked units all at R=1 puts them in disjoint bins and raises ZeroDivisionError. With one overlapping stacked unit, computation succeeds but represents only 10% of the group. The JSON has covered; `table_r_matched` and `chart_page.build_data` omit it while calling the result a reweighting to the stacked group's sizes. No saved row currently has partial support, so this is a reproduced latent failure and reporting contract gap. Return an unavailable result when used=0; publish covered and the effective stacked count, and label partial-overlap estimates as conditional.

[MEDIUM] F3 -- Horizon-specific counts and small-cell safeguards are still not carried through all views. `analysis/domino/book.py:293` greys BOTH matched horizons using the three-bar stacked count and the table prints only those three-bar counts. Saved monthly reversal exact_shared has n3=33 but n5=27; near has 31 versus 22; monthly inside exact_shared has 30 versus 29. All three five-bar estimates remain ungreyed in `analysis/domino/results/book_tables.md:188`, line 189, and line 200. The chart has a related denominator regression: `analysis/domino/chart_page.py:49` returns total units as n alongside a by-3 probability; daily plain reversal displays 43,809 instead of its 43,629 valid observations. It also renders three-unit exact-shared reversal results without the promised small-cell treatment.

The claimed A4 fold remains incomplete in the chance tables too. `analysis/domino/chance.py:546` correctly uses each horizon for greying, but the difference rows print only five-bar counts at line 548; hypothesis and variant own chances at lines 577 and 644 are still bare shares without the intervals A4 says one-R chances carry. Thus the blanket every-table/each-horizon claim at `analysis/domino/CHANCE_RECEIPT.md:30` and prereg A4 lines 225-234 outruns the implementation. Carry each displayed horizon's valid denominators, coverage, and small-cell state to every table and chart; implement or explicitly narrow the interval promise.

### C. Curves and the chart-page data mapping

[NOTE] `_curve_points` at `analysis/domino/book.py:325` preserves the last point after downsampling, including when the stride does not naturally select it. A 601-point vector retained the correct endpoints. All 12 stored curves reproduced exactly from the saved rows and cached closes. They remain dated by entries, not exits. Sampling preserves endpoints, not every trough or peak; use the full series for the reported drawdown and disclose that a drawn line is sampled.

[NOTE] Numerical mapping mostly checks out: `analysis/domino/chart_page.py:39` selects venue-era chance cells, line 46 uses one_r rather than a general profitable-trade rate, and lines 60-72 take book values from h5. In particular hit is the one-R share, not the share of positive marked returns. Lines 76-87 select flag=all and n_stacked >=30 for the by-3 matching chart; an offline build produced 32 such rows. Curves are passed from book.json. No numeric value was invented by build_data, though F3 gives the wrong denominator context to some values. Source-level mapping was verified; no browser, hosted-page, accessibility, or pixel-rendering claim is made. There is no chart-page test.

[MEDIUM] F4 -- Chart labels change the comparison and the shared-open mechanism. `analysis/domino/chart_page.py:198` calls every R-matched comparison stacked minus plain, but weekly and monthly rows use within1 plus spread as their base. The data include all three timeframes, so plain is not a harmless daily-only abbreviation. At line 189 the weekly description requires Sunday to have CLOSED on the old week's extreme; the actual class uses equality of yesterday's high/low with the prior-week level and a shared calendar open, without a close-at-extreme condition. That incorrect close requirement is also present in the chance glossary at `analysis/domino/CHANCE_RECEIPT.md:44`. Use timeframe-aware base/class explanations and distinguish making an extreme from closing at it. State explicitly that the curve dates attribute eventual returns to entry dates; many concurrent trades alone does not explain that timing convention.

### D. Book receipt sentences versus tables

[MEDIUM] F5 -- Several categorical book claims contradict the receipt's own tables. The individual displayed metrics agree with book.json, but the following interpretations do not:

- `analysis/domino/BOOK_RECEIPT.md:43` says the median trade loses in every cell; daily near continuation at line 32 has a positive median (+0.36%).
- Lines 118-120 call stacked continuation the only positive daily A+ class. The daily near outside-break row at line 39 is also positive (+0.28%, 218 trades). Its chance uplift is a separate question; a negative expectancy in R does not erase positive equal-notional percent arithmetic.
- Line 117 says hammer stop rates are 8-11 points lower. Versus the displayed all-flags base, continuation THIRD/STRICT actually have HIGHER stop rates (48.3%/47.8% versus 46.0%); inside reductions are about 5-6 points. The literal comparator unflagged is not the displayed all-flags group either.
- Line 18 repeats one-in-four to one-in-three entry-day stops for all plain daily triggers, despite the corrected chance receipt giving 13.9%-32.2% across patterns. The chart repeats the old range at `chart_page.py:211`.
- Lines 127-128 call weekly spread continuation the biggest positive with near behind it. Spread is largest by total equal-size dollars in the displayed table, while near has the larger average (+2.06% versus +1.75%). Name the ranking metric. The weekly shared-open inside return at line 75 is -0.82%, so the stated -0.9% lower magnitude bound at line 124 also needs rounding correction.
- Lines 129-132 reuse hypothesis 1 across daily and weekly results, although A4 explicitly confines that hypothesis to daily units. The weekly result is descriptive. Even on daily units, the matched five-bar outside exact-shared difference remains below zero in the displayed interval; the broad gap-vanishes claim should name the continuation, horizon, and uncertainty.

What DOES check out: all four plain daily all-flags averages are negative; the listed hammer averages are near zero on this cost-free model; near and within1 continuation averages are positive; every displayed weekly shared-open setup average is negative; the weekly continuation matched deficit is about two thirds of its raw gap and negative in all five reported bins. These bounded statements survive. The tables do not warrant the excluded alternatives or causal/promotional language.

### E. Census fold against F1-F12 and the replay/refactor claim

[NOTE] The census mechanics fold is substantially implemented as the synthesis says. I checked `4560e7c` against each prior finding, then traced the extraction to the close-out source:

- Prior F1: `analysis/domino/census.py:153` drops/counts off-grid stamps, keeps/counts the last duplicate, and sorts; line 224 requires exact calendar coverage, `day_events` at line 398 requires an adjacent yesterday, and shared-open state uses the actual calendar boundary. The duplicate policy is explicit, rather than a claim that conflicting duplicates are authentic.
- Prior F2: `census.py:261` detects ANY higher-only nesting violation, independent of rank.
- Prior F3/F6: decimal band and wick comparisons at lines 278 and 296 implement inclusive boundaries; added vectors reproduce the old failures and now pass.
- Prior F4: event output now calls the field gap_pct and multiplies the fraction by 100.
- Prior F5: unknown setup kinds remain counted, and shape reference counters are retained independently; the tables state their classified denominator.
- Prior F7: equality to an open is expressly included in against in the amended definitions and receipt.
- Prior F8: directional event counts and distinct break-day counts are separately emitted and disclosed in `analysis/domino/RECEIPT.md:38` and lines 193-195.
- Prior F9/F10: exclusions and data quality are emitted at `census.py:791` and line 871; `RECEIPT.md:21` declares survivor selection and retrospective liquidity membership. The recorded exclusion list is empty.
- Prior F11: the detailed census receipt corrects quarter denominators, rank asymmetry, and history dates; `census.py:816` adds the explicit first-positive-volume cutoff. The zero-volume prefix is observable; identifying its upstream feed as index prices is a provenance claim not independently authenticated by this local arithmetic review.
- Prior F12: the nine added tests include the reproduced calendar, nesting, decimal, wick, and denominator failures. They are targeted additions, not coverage of every suggested failure mode.

The recorded census split and coin objects at `4560e7c` and `c0f1826` compare equal. Inspection of the extraction preserves ordering, adjacency, context, and aggregation; the previous audit also records its own 80-sequence comparison. This makes the no-change claim plausible and checks the saved artifacts. I did not rerun the census main or independently reproduce a complete API-to-census run, and equal saved objects alone do not prove that a historical regeneration happened.

### F. Chance fold, close-out synthesis, and causal restraint

[NOTE] Several second-audit repairs check out: decimal target/stop touches in `analysis/domino/chance.py:202`; per-horizon greying for the chance cells; per-sample censor counters at line 690; explicit later-zero-volume eligibility; amended exact-class history; and eight additional vectors in `tests/test_domino_chance_audit2.py`. The request-pointer commit `cff7932` changes the review work order only. The two original reviews remain intact as skeptical source material. Their full dispositions are not all closed, as F3 and F6 show.

[MEDIUM] F6 -- The second audit's prose fold introduces wrong outside-break numbers and leaves the disputed HANDOFF conclusions in place. `analysis/domino/CHANCE_RECEIPT.md:217` says outside THIRD is 28.9% versus 31.7% by 3, and 33.2% versus 36.5% by 5, explicitly calling it a deterioration. The saved table at `analysis/domino/results/chance_tables.md:59` and JSON instead show THIRD 34.3% by 3 and 38.8% by 5, versus all-flags 31.7% and 36.5%; its stop share is 35.3%, not the 39.3% stated at receipt line 219. The broad heading and its explanation even disagree about the sign.

Meanwhile `docs/HANDOFF.md:331` still says nothing flips across splits and calls hypothesis 1 supported on the weekly at line 332, although its own synthesis at line 278 says those statements were corrected. The census overview at line 154 also reverts to a days-based one-in-six claim despite the fixed event denominator. The chance limitations at lines 242-244 still promise distinct dates beside every count and say the R-matched check was neither preregistered nor run, contrary to A3 and the book receipt. Update every active summary from the actual endpoint tables rather than marking the fold complete while contradictory copies remain.

[MEDIUM] F7 -- Close-out conclusions turn descriptive reweighting and price travel into causal evidence. `.session_startup_prompt.md:31` declares that the stop is the problem rather than the target, and `docs/HANDOFF.md:57` makes the same claim. A path reaching a target after a pessimistically assigned stop does not show that removing the stop produces a better managed book; it leaves timing, adverse travel, holding costs, liquidation, and the alternate exit unspecified. Likewise `analysis/domino/chart_page.py:198` says a shrinking matched gap means the raw gap WAS bar size. Binned observational reweighting shows sensitivity to a distribution, not causal identification; it does not hold date/coin/regime equal. Present these as questions motivating the separately preregistered management comparison and describe the matching result as attenuation after reweighting. Do not promote the next exit design from this receipt.

### G. Prereg A3/A4, machine-readable artifacts, and hygiene

[NOTE] A3's declared mechanics are largely present: `book.py:48` uses 3 and 5; the return rule, fixed-notional totals, entry-date grouping, and base quintiles match its formulas. Horizons inherit chance's explicit convention: the entry bar plus the stated subsequent bar boundary, with incomplete horizons censored. The main additional curve cells are the inside all/THIRD comparison; they are a presentation extension and should be named alongside the original declared handful. A4 is explicitly post-hoc and does not conceal its reporting amendment. F3 identifies the remaining implementation/contract mismatch. No new entry-class look-ahead was established in the added book or display code; inherited pessimistic entry-day ordering remains a model limitation, not live fill fidelity.

[LOW] F8 -- The new book artifact is not strict JSON. `analysis/domino/book.py:419` leaves allow_nan at its default; the default callback at line 423 is not called for native float NaN/infinity. The pinned book.json contains 141 NaN/Infinity tokens, including unbounded bin edges, and a strict JSON parse rejects it. Python's permissive loader and the page's JavaScript literal happen to accept these values; a normal JSON consumer need not. Normalize non-finite values deliberately, encode open-ended bounds explicitly, and serialize with allow_nan=False.

[LOW] F9 -- The close-out HANDOFF includes personal feedback despite its own public-record rule. `docs/HANDOFF.md:20` records the owner's closing praise/effort remark; `.session_startup_prompt.md:103` says personal remarks must not be committed. This is unrelated to the characterization evidence and need not be quoted again in this audit. Remove that feedback from the public handoff while retaining technical rulings and review status.

[NOTE] The pinned added-line secret/address scan covered all 26 changed files and returned zero findings. The artifact-link requirement checks out: no private artifact link was found in the pinned changed text or the repository-wide tracked text at the pin/current HEAD. A pre-existing conversation link in an unchanged discussion document is a different link type, outside this change; its value is not reproduced. The page output, unit gzip, candle cache, and run logs are ignored and absent from the pinned tracked artifact paths. `git diff --name-status` contains no Pine file, so request.security did not change. This was a local review, with no publication or external messages. The six requested audit files are the only intended writes.

## 3. Actionable items

1. F1: Include the initial zero in drawdown -- MEDIUM -- `analysis/domino/book.py:122` -- Seed the running peak with zero, add negative-first-day vectors, and regenerate all affected cells and displays.
2. F2: Handle and disclose matching coverage -- MEDIUM -- `analysis/domino/book.py:258` -- Return unavailable on zero overlap; expose covered fraction and effective counts in tables/page; label partial-overlap results conditionally.
3. F3: Carry correct denominators and small-cell states through all horizons/views -- MEDIUM -- `analysis/domino/book.py:293`, `analysis/domino/chart_page.py:49`, `analysis/domino/chance.py:548` -- Show each horizon's valid counts; grey the matching horizon; restore the declared intervals or narrow A4 accurately.
4. F4: Correct chart comparison and shared-open labels -- MEDIUM -- `analysis/domino/chart_page.py:189`, `analysis/domino/chart_page.py:198` -- Name the higher-timeframe base, remove the close-at-extreme requirement, and label entry-date attribution explicitly.
5. F5: Replace book receipt generalizations with supported statements -- MEDIUM -- `analysis/domino/BOOK_RECEIPT.md:43`, `analysis/domino/BOOK_RECEIPT.md:117` -- Include the positive outside-near cell and positive continuation median, correct stop-rate claims, and name the ranking metric and hypothesis scope.
6. F6: Finish the second audit's prose fold -- MEDIUM -- `analysis/domino/CHANCE_RECEIPT.md:217`, `docs/HANDOFF.md:331` -- Correct the outside THIRD figures/sign and remove stale denominator, split, hypothesis, date-count, and matching-status claims from every active summary.
7. F7: Keep descriptive findings from becoming causal conclusions -- MEDIUM -- `.session_startup_prompt.md:31`, `analysis/domino/chart_page.py:198` -- State the stop-management hypothesis and the attenuation after reweighting; reserve conclusions for the separately declared comparison.
8. F8: Emit standards-compliant JSON -- LOW -- `analysis/domino/book.py:419` -- Normalize non-finite fields and unbounded edges, serialize with allow_nan=False, and verify with a strict parser.
9. F9: Remove unrelated personal feedback from the public handoff -- LOW -- `docs/HANDOFF.md:20` -- Retain research decisions and status; keep personal remarks out of the public record.
