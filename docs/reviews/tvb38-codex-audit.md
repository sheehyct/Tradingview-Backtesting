<!--
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit is section 2; the CRITICAL SYNTHESIS is in docs/HANDOFF.md (TVB-38 entry), not here.
-->

# TVB-38 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of `a0c52df..058395f` on `main` (the product-3 prereg caaba12 and the build
> 058395f) captured 2026-10-11 (TVB-38, same session, before the fold). Run as `codex exec -s
> read-only -c 'windows.sandbox="unelevated"'` (CLI 0.162.1) with the prompt pointing at
> docs/reviews/REVIEW_REQUEST.md; the `-o` file is reproduced below. Lightly ASCII-normalized
> (em-dashes -> --, minus signs and curly quotes -> ASCII, absolute file links made relative);
> wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-38 -- product 3, the STRAT-management book
- **Reviewed:** `a0c52df..058395f` on `main`
- **Reviewer:** Codex CLI 0.162.1 (local, read-only sandbox)
- **Overall verdict:** NEEDS-CHANGES (F1 F2 HIGH; F3-F7 MEDIUM; F8 LOW)

## 2. Verbatim audit

# TVB-38 external audit

**Overall verdict: NEEDS-CHANGES**

Reviewed `a0c52df..058395f` on `main`: preregistration `caaba12`, then build `058395f`. The preregistration is unchanged by the build.

This is an external assessment, not an adjudicated synthesis. No files were modified and the data run was not performed.

## Findings

### F1 -- HIGH -- Decimal equality can miss a one-R target and turn a winner into a loser

**Location:** [manage.py:386](analysis/domino/manage.py:386), also lines 208-211 and 250.

> `one_r = level + r if direction == "up" else level - r`

The target is calculated with binary floats before `walk()` converts it to Decimal. That conversion preserves the arithmetic error.

**Verified reproduction:** a long with `L=0.1`, stop `0.09`, and entry-day high `0.11` should fill its one-R target. The calculated target is `0.11000000000000001`. With the entry-day close at `0.0945`, the management engine reports:

```text
one_r_k=None, exit_k=0, hit_D=False, ret_D=-5.5%
```

The reference correctly reports `out5='one_r'`, return `+10%`. This directly violates target equality filling. The measured-move calculation has the same premature-float construction.

**Fix:** calculate projected targets from Decimal inputs, preserving that representation through touch comparisons. Add equality-touch vectors for both directions and both projected-target types.

### F2 -- HIGH -- The comparison does not isolate the stop

**Location:** [MANAGE_RECEIPT.md:132](analysis/domino/MANAGE_RECEIPT.md:132), [manage.py:396](analysis/domino/manage.py:396), and lines 434, 508, 648-654.

> "keeping the one-R target and only swapping the stop (D) is the clean comparison"

D also changes the horizon: 20 daily bars versus the reference's five own-timeframe bars. Consequently, its difference includes returns earned after the reference has already marked the trade.

**Verified saved-row example:** AAVE, daily long, 2025-02-10:

```text
Reference: neither target nor stop by bar 5; return +0.3683%
D: one R touched on day 7; return +9.1129%
Close exit: day 8
```

The plain-daily paired cohorts contain **1,330** rows where the reference says `neither` and D subsequently fills one R after day five.

The stronger H3 interpretation is also confounded: management follow-up uses 20 days, `stop_saw` uses `mfe5`, and `died_r` includes units without T1 while the stop comparison is restricted to T1 units.

**Fix:** retain the declared comparisons but describe them as comparisons of complete rule sets. A stop-isolating comparison needs matched horizons and eligibility. H3 needs matched follow-up windows and cohorts before concluding that one exit discards target-bound trades more often.

The fee sentence at receipt lines 138-140 also needs correction: holding longer does not itself increase a per-fill trading fee. Funding and transaction fees require separate calculations.

### F3 -- MEDIUM -- Incomplete follow-up becomes false, including observed target touches

**Location:** [manage.py:473](analysis/domino/manage.py:473), lines 478 and 483-488.

> `and cap_end is not None`

A unit can legitimately settle at its exit before the dataset ends, while its full 20-day follow-up remains unavailable. The code then records `later1=False` and `later_r=False`, regardless of observed subsequent touches.

**Verified saved-row example:** 0G, daily reversal, 2026-10-01:

```text
exit_k=1, t1_k=7, later1=False, ceil1=null
```

The target demonstrably touched after exit and within 20 days. Across plain-daily patterns, **733 such observed T1 touches** are marked false among units lacking a complete cap.

**Why it matters:** the early-exit shares and their Wilson intervals understate observed successes and treat incomplete observation as failure.

**Fix:** distinguish observed touches from unavailable follow-up. Use a complete-cap cohort or an explicit censoring method for follow-up rates; keep already-settled book returns eligible.

### F4 -- MEDIUM -- Reported holding periods are not each book's holding periods

**Location:** [manage.py:685](analysis/domino/manage.py:685).

> `rows["days"] if b != "ref" else pd.Series(5.0, index=rows.index)`

A, B and D receive C's close-exit duration even when their target filled earlier. Every reference trade receives five, including early fills and weekly/monthly trades displayed under "median days."

Recomputing durations from saved target-touch offsets gives:

| Plain daily pattern | A actual / displayed | B actual / displayed | D actual / displayed |
|---|---:|---:|---:|
| Reversal | 0 / 2 | 1 / 2 | 1 / 2 |
| Continuation | 1 / 3 | 3 / 3 | 1 / 3 |
| Inside | 0 / 2 | 1 / 2 | 1 / 2 |
| Outside | 1 / 3 | 3 / 3 | 1 / 3 |

**Fix:** record each book's fill day and calculate elapsed days from it. Preserve the reference's actual target/stop/mark day, converting weekly/monthly durations to days consistently.

### F5 -- MEDIUM -- C-only cells disappear from the headline book tables

**Location:** [manage.py:877](analysis/domino/manage.py:877).

> `if not c.get("book_rows"): continue`

This skips the whole cell before reaching the `book_C_all` output. Cells without any eligible T1 trades therefore lose their promised exit-only line.

**Verified:** all monthly continuation and outside-break cells are omitted. For example, monthly continuation/spread has **1,434 settled C-only trades averaging +0.936%** in `manage.json`, but no headline book-table line.

**Fix:** render C-on-every-unit independently of whether the five-book paired cohort exists.

### F6 -- MEDIUM -- LIQUID is incorrectly described as entry-time information

**Location:** [manage.py:1030](analysis/domino/manage.py:1030), line 1093; [census.py:562](analysis/domino/census.py:562).

> "Every split but the last is known at the break."

However:

> `tail = daily[-LIQUID_DAYS:]`

LIQUID uses the snapshot's final 30 days and assigns that classification to historical entries. It is not known at those entries.

The committed table is additionally stale: [manage_tables.md:811](analysis/domino/results/manage_tables.md:811) still says "entry-time context only," including `stop0`.

**Fix:** preserve the inherited snapshot classification if required for product parity, but label it retrospective. Regenerate the table's explanatory text. An entry-time liquidity variant would require trailing data available before each entry.

### F7 -- MEDIUM -- Several receipt conclusions contradict the saved tables

**Location:** [MANAGE_RECEIPT.md:181](analysis/domino/MANAGE_RECEIPT.md:181), lines 204-207 and 233-239.

Verified examples:

- **Weekly/monthly conclusion:** "the chance book's five-bar hold did better ... than anything with a daily close exit" is too broad. Weekly continuation/within1 has B and C **+1.35%**, versus reference **+0.48%** (`manage_tables.md:333-336`).
- **Own-clock count:** "loses more ... on ten of sixteen cells" should be **14 of 16** eligible weekly cells by the displayed mean differences (`manage_tables.md:751-770`). If statistical significance was intended, state that separately.
- **Direction:** "within a tenth ... on every book but ... B" is false. Reversal C is **+0.54% long versus -0.07% short**; inside D is **+0.06% versus +0.43%**. The cited continuation `+0.04/-0.52` values are **C**, not B.
- **Year:** the quoted B values are also C values; the split table has no B column.
- **Outside-day split:** the claimed reference-loss range excludes inside's **-4.32%**; the claimed non-outside reference range excludes inside's **+1.25%** (`manage_tables.md:869,873`).
- **Finding paragraph:** "the median trade still loses in every book that holds past T1" needs narrower wording. The displayed D medians include **+0.55%** and **+1.17%**.

**Fix:** correct these statements against explicitly named cells, then synchronize the repeated conclusions in ARM_LEDGER and HANDOFF.

### F8 -- LOW -- Hypothesis-table cells under 30 are not faded

**Location:** [chart_page.py:515](analysis/domino/chart_page.py:515).

> `M.hyp.map((r) => \`<tr>...`

Unlike the management-book rows, hypothesis rows have no small-cell styling. Their conditional-share cells also have separate denominators that are never checked.

**Verified:** rendering with an in-memory hypothesis denominator of one produces an unfaded row. Current saved plain-daily hypothesis rows are large, so this does not alter their present appearance.

**Fix:** apply fading using the relevant denominator for each statistic, and add a small-denominator rendering test.

## What I checked and found sound

- **Targets and chronology:** reversal anchors use the bar before the setup; inside-against/3 anchors and the declared ladder fallbacks match definition 5. The local resource's reversal anatomy supports the anchor choice. The restricted higher-timeframe ladder and two-bar measured move remain declared research choices, rather than the entirety of skill 5.1.
- **Ladder look-ahead:** `_context` stores running extremes before updating them with the entry day's travel. Rungs use previous complete bars, exclude L, deduplicate equal levels, and remain fixed.
- **Ordering:** target touches on the exit day precede the close exit. Strict exit comparisons exclude equality. The projected-target decimal defect is F1.
- **Same rows:** joining the saved management rows to product 2's venue-era rows produced **179,498 matches, 415 omitted daily units, no extra units**, and no mismatches in the compared entry fields. `ret_ref` equals retained `ret5`.
- **Aggregation:** five-book eligibility, paired sample-standard-deviation intervals, T2/T3 conditional denominators, ceiling eligibility, and `died`/`died_r` membership are implemented as described. Plain-daily book statistics reproduced from saved rows; paired interval differences were at floating-point round-trip scale.
- **Invariants:** saved rows had no target-order or reach-subset violations; B equalled C wherever T2 was absent.
- **Settlement and clocks:** 16 settlement boundary probes passed. Complete-week filtering, independent month confirmation, monthly no-confirmation behavior, long-cap dates, and truncated long caps checked out.
- **Tail arithmetic:** the four reported worst plain-daily returns match saved rows and are shorts. Losses beyond -100% are arithmetically possible under this uncapped short-return model.
- **Page:** management values originate from `manage.json`; current payload fields resolve. A Node render with DOM/chart stubs produced all 60 book rows and four hypothesis rows. Reach bars and book rows carry their small-cell flags.
- **Hygiene:** 14 management tests passed; Ruff passed. `uv` itself failed on cache permissions, so I used the existing virtual environment with caches disabled. The changed-line secret scan found nothing; the diff introduced no URLs. Cache, unit-row, log and page ignore rules resolve correctly.
- **Census changes:** the tuple extension and consumers are consistent; all three output paths honor `--out`. Moved-helper exports and cache selection passed an in-memory check. I did not rerun the census.

## Open questions and verification limits

- All 15 declared vector labels are represented, but some promises are weaker than their tests: v5/v9/v13 do not assert the declared counting behavior; v7 covers a rung equal to T1, not inside it, and contains invalid OHLC at `tests/test_domino_manage.py:156` (`open=106`, `high=105`); v10 combines day/week equality instead of isolating each; v11 uses identical week/month opens and therefore does not independently test the month veto. Decimal equality and short-side engine vectors are missing.
- `walk()` includes the entire entry day's adverse extreme. Should the tail be labelled a conservative daily-bar bound? Daily OHLC cannot establish whether that adverse extreme occurred before entry.
- I did not verify the historical "tests before data run," byte-identical census rerun, or unchanged-between-runs claims independently. No full data run, full test suite, browser-pixel check or hosted-page check was performed.
- The audit is returned here, following your no-file-modification instruction. An unrelated edit to `tests/test_domino_census.py` appeared during review; it was left untouched and excluded from the pinned audit.

