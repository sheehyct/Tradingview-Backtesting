<!--
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit is below; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-37 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of tradingview-backtesting `ecc4d6c..8b800a7` (the daily / weekly /
> monthly domino census: prereg, engine, tests, receipt, ledger card), captured 2026-10-10
> (TVB-37 MID-session, at the owner's request, before any outcomes product reuses the
> engine). Run as `codex exec -s read-only` against the local tree at ea58c6c (one commit
> ahead of the range: the review request and the receipt glossary, which the reviewer
> excluded); work order `docs/reviews/REVIEW_REQUEST.md`. Lightly ASCII-normalized
> (em-dashes -> --, curly quotes -> straight); wording and code otherwise unchanged.
> The reviewer's first two attempts could not start their sandbox and returned a BLOCK
> about their own tooling; those are not recorded here. This is the third run.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md` (TVB-37 entry). Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-37 -- daily / weekly / monthly domino census
- **Reviewed:** ecc4d6c..8b800a7 on main
- **Reviewer:** GPT-6 / Codex; exact runtime model identifier not exposed
- **Overall verdict:** NEEDS-CHANGES

## 2. Verbatim audit

> Read CRITICALLY. Do NOT assume this audit is correct. Findings below distinguish reproduced defects, committed arithmetic, and supplemental local evidence. The subsequent critical synthesis belongs in HANDOFF.

All citations refer to 8b800a7. The working checkout is ahead of that commit; its later receipt glossary was excluded from this review. The engine, tests, results, and ledger card match the pinned versions.

Validation: **7 tests passed** using the existing virtual environment, with bytecode and pytest cache writing disabled. Additional probes ran in memory. I did not run the census end to end, call the candle API, or write files. Git status remained unchanged.

The existing, uncommitted cache and event dump were examined as supplemental evidence only. They match the committed day count and composition totals, but are not independently authenticated evidence of the original run.

### 1. Calendar bars from dailies

**[NOTE] Calendar calculations check out.** Timestamp-based bucketing preserves calendar membership rather than shifting later observations into missing dates. Monday/Sunday boundaries, a 31-day month, leap February, December rollover, and Q4 rollover were checked. The partial first bucket is dropped. A candle beginning at the cutoff is excluded; the preceding closed candle is retained. Evidence: `analysis/domino/census.py:120`, `analysis/domino/census.py:138`, `analysis/domino/census.py:157`, `analysis/domino/census.py:182`, `analysis/domino/census.py:201`; supplied vectors at `tests/test_domino_census.py:29` and `tests/test_domino_census.py:48`.

**[HIGH, F1] Completeness counts observations instead of validating calendar coverage.** `normalize` sorts but retains duplicate timestamps. `aggregate` declares completeness when observation count equals expected day count. A Monday-through-Sunday vector with Wednesday missing and Tuesday duplicated returns `complete=True`. The resulting high/low can therefore become an understated "complete" prior level. Evidence: `analysis/domino/census.py:169`, `analysis/domino/census.py:206`.

Missing days also affect the current bucket: its first observed day is treated as its actual opening day. With a complete prior week and missing Monday, Tuesday is incorrectly marked as a weekly shared open. Evidence: `analysis/domino/census.py:188`, `analysis/domino/census.py:306`, `analysis/domino/census.py:359`.

Supplemental cache inspection found **zero duplicate timestamps, gap edges, unaligned timestamps, or stale final days** across the 292 cached series. F1 is a reproduced engine defect; these checks do not establish that it affected the committed census.

### 2. Levels and first-break-only

**[NOTE] Strict comparisons and first-break state check out on contiguous data.** Higher-timeframe prior bars must be complete and adjacent. Running extremes are captured before incorporating today's candle. Equality remains fresh, allowing a later strict crossing; equality itself never breaks. Running extremes start empty in a new bucket. Evidence: `analysis/domino/census.py:279`, `analysis/domino/census.py:297`, `analysis/domino/census.py:309`, `analysis/domino/census.py:378`, `analysis/domino/census.py:381`.

**[HIGH, F1] Daily levels cross gaps without qualification.** The previous array element becomes "yesterday," regardless of elapsed calendar time. A Monday/Wednesday vector produces a Wednesday daily break against Monday's level. Daily setup classification similarly crosses gaps. This violates the preregistered previous-day level and predecessor semantics. Evidence: `docs/experiments/tvb37_domino_census_prereg.md:40`, `analysis/domino/census.py:355`, `analysis/domino/census.py:356`, `analysis/domino/census.py:367`.

### 3. Shared-open EXACT stack

**[NOTE] Equal-price handling checks out for the supplied market-price representation.** Daily prices are parsed once; higher-timeframe extrema retain those parsed values through `min` and `max`. No averaging or arithmetic reconstruction introduces a discrepancy between an identical daily and weekly price. The supplied Sunday/Monday vector produces an EXACT D+W stack. Evidence: `analysis/domino/census.py:162`, `analysis/domino/census.py:197`, `analysis/domino/census.py:255`, `tests/test_domino_census.py:79`.

The **53 plain-day EXACT stacks are valid under the strict-touch rule**. Yesterday can retouch the prior higher-timeframe extreme without breaking it; today then crosses that identical daily and higher-timeframe level.

Supplemental local rows contain 39 D+W, 7 D+M, 6 D+W+M, and 1 D+Q plain-day EXACT events. One inspected up example had prior-week high, yesterday's high, and pre-today running high all equal to 2.241, followed by today's high of 2.3. This explains the mechanism without requiring a shared open. Committed totals: `analysis/domino/results/tables.md:82` and `analysis/domino/results/tables.md:83`.

The missing-opening-day defect in F1 can incorrectly alter the shared-open classification.

### 4. Nesting invariant

**[MEDIUM, F2] The nesting check misses the simplest violation.** Higher-timeframe hits are calculated independently of the daily hit, which is good. However, violations increment only when `rank >= 2` and D is absent. A W-only, M-only, or Q-only event is precisely a nesting violation, but is counted as rank 1 with zero violations and discarded from the event rows. Evidence: `analysis/domino/census.py:372`, `analysis/domino/census.py:389`, `analysis/domino/census.py:407`.

An in-memory mutation supplying a W-only hit returned:

```text
rank = {('up', 1): 1}
violations = 0
```

The check is **not wholly vacuous**: committed compositions contain 28,002 weekly, 6,154 monthly, and 1,734 quarterly hits. But the reported zero is not a complete check of the preregistered invariant. Evidence: `docs/experiments/tvb37_domino_census_prereg.md:82`, `analysis/domino/RECEIPT.md:28`, `analysis/domino/results/tables.md:21`.

### 5. Distance band

**[NOTE] The formula and comparison operators match the intended bands for positive prices.** Maximum minus minimum is the largest pairwise gap, divided by the lowest level. EXACT is zero; the other upper boundaries use inclusive comparisons. Evidence: `docs/experiments/tvb37_domino_census_prereg.md:49`, `analysis/domino/census.py:255`.

**[MEDIUM, F3] Binary floating-point arithmetic defeats the declared boundary inclusivity.** Reproduced outputs:

```text
levels [0.1, 0.10025]: exactly 0.25%, classified WITHIN 1%
levels [0.1, 0.101]:   exactly 1%, classified SPREAD
```

The calculated fractions are slightly above their mathematical boundaries. Evidence: `analysis/domino/census.py:256`, `analysis/domino/census.py:259`, `analysis/domino/census.py:261`.

Supplemental decimal recomputation found **no band mismatches in the existing 31,501 local event rows**. The implementation still fails hand vectors at the preregistered boundaries.

**[LOW, F4] The event field has misleading units.** `distance_pct` stores a fraction: 0.01 means 1%, rather than 0.01%. The CSV retains this field name and writes the fraction without conversion. This creates a downstream interpretation hazard. Evidence: `analysis/domino/census.py:441`, `analysis/domino/census.py:765`, `analysis/domino/census.py:786`.

### 6. Setup kind

**[NOTE] Classification and direction mapping check out on valid contiguous input.** Strict high/low comparisons produce 1, 2U, 2D, and 3. The reversal/continuation mapping is correct in both directions. Higher-timeframe setup and predecessor bars must both be complete and adjacent; current-bar final classification is not used. Evidence: `analysis/domino/census.py:213`, `analysis/domino/census.py:226`, `analysis/domino/census.py:278`, `analysis/domino/census.py:285`.

**[LOW, F5] Setup percentages silently exclude unclassifiable events.** The table denominator is the sum of known kinds, rather than every break on that timeframe. Committed ALL totals are:

| Timeframe | Breaks | Classified setups | Unclassified |
|---|---:|---:|---:|
| D | 198,696 | 198,446 | 250 |
| W | 28,002 | 27,741 | 261 |
| M | 6,154 | 5,923 | 231 |
| Q | 1,734 | 1,540 | 194 |

This exclusion is reasonable when a predecessor is unavailable, but the "all events" heading does not disclose it. Quarter percentages are particularly sensitive to the denominator. Evidence: `analysis/domino/census.py:396`, `analysis/domino/census.py:589`, `analysis/domino/census.py:597`, `analysis/domino/results/tables.md:40`.

Daily setup classification inherits F1's gap defect.

### 7. Hammer / shooter flags

**[NOTE] Shape orientation, both-body-end requirement, and reversal reporting check out.** For up breaks, the lower body endpoint must lie in the top third; for down breaks, the upper endpoint must lie in the bottom third. Zero-range bars return both flags false. STRICT measures the wick on the break's side. The reversal table uses reversal-only counters, while JSON counters also retain other known setup kinds. Evidence: `analysis/domino/census.py:239`, `analysis/domino/census.py:245`, `analysis/domino/census.py:248`, `analysis/domino/census.py:400`, `analysis/domino/census.py:609`.

**[MEDIUM, F6] STRICT also fails an exact decimal boundary.** A bar with low 0.1, high 0.2, and open/close 0.19 has an upper wick exactly 10% of its range. The engine returns `(True, False)` instead of `(True, True)`. Evidence: `analysis/domino/census.py:246`, `analysis/domino/census.py:250`.

The promised all-setup reference counters also omit bars with unknown setup kind because flag aggregation occurs after the early `continue`. Evidence: `docs/experiments/tvb37_domino_census_prereg.md:65`, `analysis/domino/census.py:396`.

### 8. Quarter state

**[NOTE] Branch coverage and precedence check out for the declared directional cases.** In-memory vectors exercised unknown, breaks today, previously broken with the direction, opposite, both, inside with, and inside against, including directional mirrors. The branches are exhaustive and mutually exclusive. UNKNOWN depends on availability of the adjacent complete prior quarter, independently of whether its setup kind is classifiable. Evidence: `analysis/domino/census.py:314`, `analysis/domino/census.py:319`, `analysis/domino/census.py:329`, `analysis/domino/census.py:334`.

The pre-today running extremes avoid using today's final high/low as already-known state. This remains a daily-resolution proxy, not reconstruction of the quarter's exact state at an intraday break; the receipt discloses the absence of intraday ordering at `analysis/domino/RECEIPT.md:136`.

**[LOW, F7] Equality to the quarter open needs explicit wording.** A daily level equal to the quarter open becomes `inside_against`, although the preregistration describes that state as the "other side" of the open. The same complement convention appears in support colors. Define explicitly whether "against" includes equality. Evidence: `docs/experiments/tvb37_domino_census_prereg.md:71`, `analysis/domino/census.py:329`, `analysis/domino/census.py:420`.

### 9. Counting and denominators

**[NOTE] Event arithmetic and per-coin rates reconcile.** Both directions are evaluated independently, so an outside day can contribute two events. ALL has 198,696 events; 31,501 / 198,696 = 15.9%. LIQUID has 98,364 events and 15,664 rank 2+ events. The median 14.7 rate is independently reproduced from committed per-coin rank 2+ counts divided by eligible days, for coins with at least 100 such days. Evidence: `analysis/domino/census.py:363`, `analysis/domino/census.py:391`, `analysis/domino/census.py:509`, `analysis/domino/results/census.json:3403`, `docs/ARM_LEDGER.md:524`.

**[MEDIUM, F8] The receipt changes the denominator from events to days.** "About one day in six with a daily break" is not established by the event table, and the receipt does not explicitly disclose double-direction days. Evidence: `analysis/domino/RECEIPT.md:121`.

Supplemental local evidence makes the difference concrete:

- 175,891 distinct coin-days had at least one daily break.
- Those days produced 198,696 directional events.
- Rank 2+ occupied 31,356 distinct coin-days.
- The corresponding day share is **17.8%**, compared with the **15.9% event share**.

Also, `coin_days` counts eligible comparison days, `len(daily) - 1`, rather than every fetched closed day. That convention should be named. Evidence: `analysis/domino/census.py:342`.

### 10. LIQUID

**[NOTE] Base-volume arithmetic checks out.** The venue's official candle schema identifies `v` as volume in base units, so multiplying it by close is dimensionally USD notional, rather than multiplying an already-notional volume by price. Source: [official candle schema](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions#data-type-definitions).

The engine computes the median of the last 30 products, uses an inclusive million-dollar threshold, and returns false with fewer than 30 observations. An exact-threshold hand vector passed. Evidence: `analysis/domino/census.py:453`.

Two qualifications belong in the definition: `volume * close` is a close-valued notional proxy, rather than exact traded dollar turnover; and without F1's continuity validation, the last 30 observations need not be the last 30 calendar days. Current LIQUID membership also describes the run-time subset applied to its full history, rather than historical liquidity membership. Evidence: `analysis/domino/census.py:454`, `analysis/domino/census.py:721`.

### 11. Data fetch

**[NOTE] The cap, cutoff, and same-day cache key check out.** A single request spans the retained daily window. Paging cannot recover older candles beyond the documented most-recent-5,000 retention limit; its absence is not itself a defect. Source: [official candle retention documentation](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint#candle-snapshot). Evidence: `analysis/domino/census.py:94`, `analysis/domino/census.py:104`.

The date-keyed cache prevents reuse across different daily cutoffs. It does not detect later corrections or incomplete responses cached under the same cutoff. That is a provenance limitation, not demonstrated staleness in this run.

**[MEDIUM, F9] Universe exclusions can silently narrow the promised census.** Fetch failures are printed and skipped; coins with fewer than three daily observations are also skipped. Neither exclusion is recorded in the committed results. Dropping new coins conflicts with "nothing is dropped for being new." Evidence: `docs/experiments/tvb37_domino_census_prereg.md:30`, `analysis/domino/census.py:694`, `analysis/domino/census.py:698`.

**[LOW, F10] Survivorship is only implicit in the receipt.** The preregistration explicitly excludes delisted names, and code implements that exclusion. The receipt says "live perp" but does not explicitly explain the resulting survivor-only universe or the retrospective LIQUID selection. Evidence: `docs/experiments/tvb37_domino_census_prereg.md:27`, `analysis/domino/census.py:85`, `analysis/domino/RECEIPT.md:14`.

### 12. Receipt honesty

**[MEDIUM, F11] Several statements do not follow from the stated tables or denominators.**

Each sentence of "What the arithmetic says" was checked:

1. **"About one day in six..."** has the event/day problem in F8. **"Nearly four in five..."** checks out: D+W is 24,558 / 31,501 = 78.0%. Evidence: `analysis/domino/RECEIPT.md:121`, `analysis/domino/results/tables.md:23`.

2. **"One rank 2+ event in five..."** checks out: 6,607 / 31,501 = 21.0%. Shared opens contain 99.0% of EXACT events, supporting "almost entirely." The following mechanism sentence is too categorical: plain-day retouches also produce EXACT stacks, and the shared-open flag can concern a timeframe outside the broken set. Supplemental rows contain two such EXACT events. Evidence: `analysis/domino/RECEIPT.md:123`, `analysis/domino/census.py:447`, `analysis/domino/results/tables.md:83`.

3. **Three- and four-level frequency** checks out when expressed as events: 1.7% and 0.3%. Their combined tight-stack share is 205 / 3,862 = 5.3%. Replace "days" with "events" here too. Evidence: `analysis/domino/RECEIPT.md:126`, `analysis/domino/RECEIPT.md:68`.

4. **"Under a third ... on every timeframe"** does not follow from the displayed setup percentages: quarter reversal share is **34.7% among classified setups**. Using every quarterly break instead yields 30.9%, but that changes the table's denominator. THIRD ranges from 16.8% to 20.7%; "about one in six" compresses the monthly and quarterly results. STRICT is a sliver-wick definition, not literally "no-wick." Evidence: `analysis/domino/RECEIPT.md:127`, `analysis/domino/RECEIPT.md:86`, `analysis/domino/RECEIPT.md:91`.

5. **Overall directional symmetry** is a fair shorthand for 97,055 up versus 101,641 down events. **"Down leads slightly on the higher ranks"** understates the tables: down shares are 52.1% at rank 2, **61.1% at rank 3**, and **71.0% at rank 4**. Evidence: `analysis/domino/RECEIPT.md:129`, `analysis/domino/results/tables.md:14`.

Other receipt corrections:

- **"No headline share by more than a point"** fails even for the listed monthly THIRD share: 20.7% in ALL versus 22.3% in LIQUID, a 1.6-point difference. Evidence: `analysis/domino/RECEIPT.md:116`, `analysis/domino/results/tables.md:50`, `analysis/domino/results/tables.md:129`.
- **"Most" xyz coins lack a complete prior quarter** confuses event-time availability with current listing depth. Committed metadata has 84 of 114 xyz coins with at least one complete quarter, and 30 without. Historical rank 2+ events are often UNKNOWN; that is a different claim. Evidence: `analysis/domino/RECEIPT.md:24`, `analysis/domino/results/census.json:10`, `analysis/domino/results/tables.md:312`.
- **Oldest main-dex history reaching back to 2023** contradicts committed metadata beginning **2020-08-19**, with 48 coins beginning before 2023. The source/provenance of those older observations needs explanation, rather than an unsupported inference about where they originated. Evidence: `analysis/domino/RECEIPT.md:139`, `analysis/domino/results/census.json:16`.
- The ledger's "about 29% per timeframe" likewise obscures the quarter's displayed 34.7%. Evidence: `docs/ARM_LEDGER.md:527`.

**[NOTE] Internal reconciliation checks out.** All four committed split tables regenerate exactly from their JSON aggregates. Rank, composition, bands, band-by-rank, quarter states, shared-open totals, support denominators, coin counts, eligible days, and per-coin medians reconcile. This establishes arithmetic consistency, not independent verification of event generation.

### 13. Tests

**[MEDIUM, F12] The seven passing tests omit several required boundary and failure vectors.** Existing coverage includes basic calendar starts, equality classification, partial first-week dropping, weekly first-break behavior, a Monday EXACT stack, basic shapes, and interior distance bands. Evidence: `tests/test_domino_census.py:29`, `tests/test_domino_census.py:104`.

Missing committed hand vectors include:

- Month and quarter aggregation, leap February, year rollover, and incomplete final buckets.
- Missing opening/interior days, duplicate timestamps, and a duplicate masking a gap.
- Daily predecessor continuity across gaps.
- A prior touch followed by a strict break, with directional mirrors.
- A higher-timeframe-only violation that must increment the nesting counter.
- EXACT stacks on plain days.
- Exact 0.25%, 1%, third, and 10%-wick boundaries; zero-range shapes.
- Every quarter state, precedence, mirrors, and equality to its open.
- LIQUID median versus mean, exact threshold, fewer than 30 days, and discontinuous dates.
- Outside-day double counting and event-versus-distinct-day denominators.
- Higher-timeframe predecessor completeness and unknown-kind denominators.
- Mocked fetch/caching failures and recorded universe exclusions.

The in-memory probes reproduced F1, F2, F3, and F6 despite the supplied suite passing.

### 14. Public-repo hygiene

**[NOTE] Checks out within the pinned range.** Secret-pattern and public-address checks against the pinned changed blobs returned no findings; sensitive values were not printed. The census adds one public API URL literal. The cache, event dump, and run log are ignored, and cache/event paths are absent from the pinned tracked tree. Evidence: `analysis/domino/census.py:45`, `.gitignore:104`.

The archived HANDOFF body matches the prior body verbatim, so the archive move does not introduce new substantive disclosures. The additional documentation pin commit in the range was also skimmed; the range contains three documentation commits before 8b800a7, rather than the work order's stated two.

### 15. request.security

**[NOTE] Checks out clean.** `git diff --name-status ecc4d6c..8b800a7` contains no Pine files. No `request.security` implementation changed. The new engine's relevant lookahead defense is its pre-today running-extreme construction, checked under focus areas 2 and 8. Evidence: `analysis/domino/census.py:299`, `analysis/domino/census.py:309`.

## 3. Actionable items

1. F1: Validate daily continuity and bucket coverage -- **HIGH** -- `analysis/domino/census.py:169`, `analysis/domino/census.py:206`, `analysis/domino/census.py:355` -- Reject conflicting duplicates, require exact unique calendar coverage for complete buckets, avoid treating nonadjacent observations as yesterday, and distinguish observed bucket starts from actual calendar opens.

2. F2: Detect every higher-timeframe nesting violation -- **MEDIUM** -- `analysis/domino/census.py:389` -- Check for any W/M/Q hit without D, regardless of rank; add a mutation vector that currently returns zero violations.

3. F3: Preserve exact distance-band boundaries -- **MEDIUM** -- `analysis/domino/census.py:256` -- Use decimal prices or exact scaled-price comparisons derived from the original price strings; test equality and values immediately above both thresholds.

4. F4: Make distance units explicit -- **LOW** -- `analysis/domino/census.py:441`, `analysis/domino/census.py:786` -- Rename the fraction field or serialize actual percentage units and document the schema.

5. F5: Disclose classification denominators -- **LOW** -- `analysis/domino/census.py:597` -- Report classifiable and unknown setup counts alongside percentages; retain all-setup shape reference counts independently of kind availability.

6. F6: Preserve the inclusive wick boundary -- **MEDIUM** -- `analysis/domino/census.py:250` -- Use exact decimal/scaled arithmetic for shape thresholds and add the reproduced 10%-wick equality vector.

7. F7: Define open-price equality -- **LOW** -- `analysis/domino/census.py:329`, `analysis/domino/census.py:420` -- State explicitly whether equality belongs to "against" and use consistent labels in the preregistration and receipt.

8. F8: Correct event/day reporting -- **MEDIUM** -- `analysis/domino/RECEIPT.md:121` -- Say "directional events," disclose that outside days can contribute twice, and name eligible comparison days as the rate denominator. Report distinct-day shares separately if desired.

9. F9: Record universe exclusions -- **MEDIUM** -- `analysis/domino/census.py:694`, `analysis/domino/census.py:698` -- Preserve new listings in the universe metadata and record fetch failures, insufficient depth, and analyzed counts instead of silently narrowing coverage.

10. F10: State survivorship and liquidity selection -- **LOW** -- `analysis/domino/RECEIPT.md:14` -- Explicitly disclose delisted-name exclusion and that current LIQUID membership is applied retrospectively.

11. F11: Correct unsupported receipt and ledger wording -- **MEDIUM** -- `analysis/domino/RECEIPT.md:24`, `analysis/domino/RECEIPT.md:116`, `analysis/domino/RECEIPT.md:127`, `analysis/domino/RECEIPT.md:139`, `docs/ARM_LEDGER.md:527` -- Use the stated denominators, quantify higher-rank asymmetry, qualify the shared-open mechanism, correct quarter-depth and history claims, and explain pre-2023 candle provenance.

12. F12: Add the missing adversarial vectors -- **MEDIUM** -- `tests/test_domino_census.py:104` -- Prioritize the reproduced completeness, nesting, decimal-band, wick-boundary, and denominator failures before this engine supplies downstream comparisons.
