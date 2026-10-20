# TVB-39 External Audit -- Codex (verbatim source, read CRITICALLY)

> External review of `4dc5f6b..30391fb`, captured 2026-10-14 (TVB-39 post-session).
> Plain ASCII. This is the external assessment, not the critical synthesis.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs
> variant, or over/under-state a risk. The next Claude session should adjudicate these
> findings in `docs/HANDOFF.md`.

---

## 1. Metadata

- **Session:** TVB-39 -- trade viewer and management-book amendment A2.
- **Reviewed:** `4dc5f6b..30391fb` on main: six commits, 17 changed paths. No sibling repos.
- **Reviewer:** Codex, local source review, offline replay, adversarial probes, and browser checks.
- **Overall verdict:** **NEEDS-CHANGES** -- one HIGH and seven MEDIUM findings.
- **Authority:** `docs/reviews/REVIEW_REQUEST.md` was REQUESTED; this audit did not exist.
  Followed the session-review skill, local protocol/template, CLAUDE.md, charter Section 0,
  and the work order's read-first packet.
- **Checkout:** `785caed0a964df06de8208b931b8692412e4aced`. Post-pin changes are documentation
  only; reviewed source, tests, and results match the pinned head. Findings below cite those
  source files at `30391fb`. The open T1 question is an interpretation, not an owner ruling.
- **Write scope:** this file only. The pre-existing untracked `User_Notes.md` was left alone.
  No engine, results, HANDOFF, request status, git state, or configuration edits.

## 2. Verbatim audit

The new arithmetic reproduces, and A2 did not change the headline engine's previous fields.
However, the hourly arm can exit before the census trade enters, incomplete hourly coverage is
accepted as a known path, and the viewer can misrepresent recorded outcomes. Those are material
for a tool whose purpose is to detect modeling mistakes visually. The fee summary also calls
several negative results flat. Repair and rerun the affected evidence before accepting TVB-39.

### F1 -- HIGH -- Hourly entry accepts equality and can exit before the trade exists

**Evidence:** `analysis/domino/manage.py:424-430`; the strict-break contract is explicit in
`docs/reviews/REVIEW_REQUEST.md:62-65`, and the unchanged event detector uses strict operators
at `analysis/domino/census.py:480-482,492-498`.

`walk_hourly()` enters on `high >= L` / `low <= L`. A touch is not the census's first break.
Because the exit test includes that hour, an earlier equality hour can realize a loss before
the actual break occurs. This changes the trades, not just the reported holding time.

**Reproduced on the cached run:** 1,210 settled hourly rows choose an equality hour before the
first strict-break hour; 863 belong to the plain-daily T1/reference cohort used in A2's tables.
312 rows exit before the first strict break, including 228 in that reporting cohort.

Concrete case: ACE, 2026-04-29, daily long, L=0.1255. The 00:00 UTC candle's high is exactly
0.1255 and its close is 0.1246. The walker enters and exits there, recording -0.7171314741%.
The first high strictly above L is in the 02:00 candle, whose high is 0.1261. The recorded
hourly loss therefore precedes the trade's entry. The viewer independently makes the same
entry-marker mistake at `analysis/domino/viewer/app.js:252-254`.

**Action:** use strict operators for entry and inclusive operators only for target/stop
touches. Add long and short equality-before-break cases, including an equality hour satisfying
both exit tests. Rerun the hourly rows, paired tables, and associated narrative; preserve the
unchanged daily headline. A2's word "reached" at prereg line 298 should also be made explicit.

### F2 -- MEDIUM -- A partial first day is treated as a fully observed entry day

**Evidence:** `analysis/domino/manage.py:419-432,643-646` and
`analysis/domino/census.py:168-185`.

Having some hours on the entry day is sufficient for acceptance. Nothing establishes that the
earlier part of that day was observed, so the first cached qualifying hour is reported as the
first entry hour. An earlier entry, target, or exit may already have happened. Even the first
cached candle opening beyond L is accepted at an L fill that candle never visited.

**Reproduced on the cached run:** 261 accepted hourly rows have a partial entry day; 220 enter
the A2 reporting cohort. In 28 rows the first cached hour already opens strictly beyond L
(15 in the cohort). APEX daily long on 2026-03-18 has L=0.29706. The cache starts at 06:00,
opening 0.30702 with low 0.30381. The row nevertheless records `entry_h=6`, filled at L.
These prices establish that the claimed entry cannot occur inside the selected hour; the
unobserved preceding hours cannot establish when its exit clock should have started.

**Action:** require coverage from the day's start through entry, or a separately justified
proof that no earlier entry was possible. Otherwise count and exclude the hourly observation
as unknown. Do not silently substitute the first available hour. Publish the dropped count
and rerun the paired cohort. This does not require dropping the daily unit.

### F3 -- MEDIUM -- A missing cap-hour candle removes the cap instead of censoring

**Evidence:** `analysis/domino/manage.py:433-445,459-474`.

If the cap day's final hour is absent, `last_h` remains None and `stop` becomes the end of the
entire hourly cache. With later candles present, the walker can take targets or exit after day
20. It also skips internal gaps and measures `hours` as list-index distance, understating
elapsed time and shifting the viewer's alternative-clock marker when hours are missing.

**Reproduced fault injection, not observed corruption of this snapshot:** starting with the
existing v17b fixture, remove only day 20's 23:00 candle and retain later days. Make the first
qualifying exit day 21 at 01:00. The result is `status='exit'`, end day 21, `hours=504`, and
return -1.9801980198%, rather than a censored day-20 observation. Actual elapsed time to that
hour is 505 hours. The 584 supplied daily/hourly cache files had no internal hourly gaps after
normalization, so this vector does not explain the current tables.

**Action:** bound the scan by the absolute cap timestamp independently of candle presence;
require continuous hourly coverage through the first settled event or cap. Missing required
hours must produce an explicit unknown/censored result. Derive durations and exit timestamps
from timestamps, not array offsets. Cover a missing middle hour and missing 23:00 cap hour
with subsequent data, as well as the existing truncated-tail case.

### F4 -- MEDIUM -- Price reconstruction and a fallback put target exits on untouched hours

**Evidence:** `analysis/domino/viewer/app.js:76,239-241,252,255,264`.

The inverse return formula is mathematically correct, but its floating-point result is used
as an exact candle-touch threshold. A one-ULP difference can miss the recorded price. If no
hour qualifies, `touchBar()` silently chooses the day's first candle. Thus an accurate printed
fill can coexist with a wrong exit arrow. The independently recomputed one-R price can also
move its touch circle away from the exit arrow.

**Reproduced:** ATOM daily long, 2026-05-09, book A. Recorded T1 is 1.9853; reconstructing it
from the return gives 1.9853000000000003. The first exact touch is 01:00 UTC. No hour reaches
the reconstructed value that day, so the out arrow falls back to 00:00, an hour that did not
touch T1. Executed the actual `draw()` path with captured chart calls and inspected the real
rendered page. Across the supplied rows, exact-target versus reconstructed-price hour searches
differed in 24 book-A, 7 book-B, and 21 book-D cases. These are book-case counts, not unique
trades; the D oracle used the engine's decimal one-R construction.

Another actual case, ACE daily short 2026-06-14, has book D's out arrow at 17:00 and its one-R
circle at 18:00 because the two price calculations differ. The existing TVB-38 decimal fix
does not protect the new JavaScript reconstruction.

**Action:** carry canonical recorded fill/target prices into the viewer, using consistent
decimal/tick normalization for comparisons. Missing touch evidence should be displayed as
unverified, not assigned to the first candle. Test `draw()` markers against exact-touch long
and short cases, including the two cached examples above.

### F5 -- MEDIUM -- Reference stop exits are drawn at the end of the day

**Evidence:** `analysis/domino/viewer/app.js:88,262-265`.

`settle(ref)` sets `target=false` for a setup-bar stop. `draw()` then sends that stop fill
through the close/mark branch and places its out arrow on the day's last hour. This contradicts
the stop circle, which already searches for the hour touching the stop. The old misplaced
`else` was fixed, but this separate branch error remains.

**Reproduced:** BTC weekly long entered 2026-03-16, reference book. Its recorded stop fill is
65,780 on day 11, 2026-03-27. Capturing `draw()` produces the stop circle at 14:00 UTC and
`out 65,780.00 (setup-bar stop)` at 23:00. Across the viewer data, 25,968 reference stop cases
with cached exit-day hours have a first stop touch before the hour chosen for the out arrow.
The entry in this example predates the hourly window, which the viewer correctly discloses;
the stop day is fully covered.

**Action:** distinguish target, stop, close, and horizon-mark settlement reasons. Place a
reference stop on the adverse-side touch hour of its recorded day. Preserve and label the
reference engine's daily pessimistic ordering when an entry-day stop may precede the entry;
do not silently invent a different trade from hourly observations.

### F6 -- MEDIUM -- An unavailable selected book silently falls back to book C

**Evidence:** `analysis/domino/viewer/app.js:77-82,91-96,235,335,372`.

When a requested book lacks its return or holding-day field, `settle()` returns the headline
book C object. The selector and card return still refer to the requested book, while the chart,
settlement explanation, and card caption use C. This defeats the first-pass correction that
the book selector should drive the chart.

**Reproduced in the actual browser and Node draw harness:** select the reference book for 0G,
2026-05-17, monthly short. The row's reference is censored and its card says `n/a`, but the
caption says `daily-close exit` and the detail shows book C's -1.09% exit on day 1. There are
4,239 reference selections that take the fallback in the supplied viewer data; this total
includes cases where the headline itself is censored, not only false drawn closures.

**Action:** keep the requested book identity and show its missing/censored status. Do not
borrow another book's price, holding time, or out arrow. Test a censored reference alongside
a valid C result, plus unavailable D5 and fully censored rows.

### F7 -- MEDIUM -- The whole same-day stack is labeled with a different subset's class

**Evidence:** `analysis/domino/viewer/app.js:231-234,326-334`; field meanings are defined at
`analysis/domino/chance.py:139-180,356-362`.

For daily rows, `cls` describes the nearest fresh higher level at entry. `stack` lists all
levels that eventually broke that day. The viewer computes the full stack's max-to-min gap,
then labels it with `cls` and applies the "domino" label to the whole stack. Those are different
sets. An exact D/W pair does not make a distant M level part of an exact three-level stack.

**Reproduced in the browser:** 0G daily long, 2026-08-31. D=W=0.17296, M=0.23279. The details
say `gap 34.59% (same price)` and the entry line says `domino D+W+M (same price)`. The daily
row correctly belongs to the exact D/W class; the viewer incorrectly extends that label to M.
The scan found 1,135 cases whose full displayed stack band differs from the near/within1/
exact_shared row label under the viewer's own gap calculation.

**Action:** label the actual converged subset, and present the other same-day breaks separately.
Keep the entry-time class distinct from the retrospective full-day stack. Use an appropriate
gap calculation for the stated subset; do not change the census class to make the display fit.
Include a D=W/M-distant case and an exact_plain case in viewer regression coverage.

### F8 -- MEDIUM -- The fee narrative calls six negative management lines flat

**Evidence:** `analysis/domino/MANAGE_RECEIPT.md:310-315`, `docs/ARM_LEDGER.md:678-680`, and
`docs/HANDOFF.md:89-91` at the pinned head; contradicted by
`analysis/domino/results/manage_tables.md:1008-1010` and the matching `manage.json` candidates.

The three named positive net lines are correctly identified. The additional claim "Every other
management line is flat net (intervals through zero)" is false under the report's own intervals:

| Kind / book | Net mean % | Reported 95% interval % |
|---|---:|---:|
| Reversal A | -0.1275 | [-0.1767, -0.0782] |
| Continuation A | -0.3112 | [-0.3924, -0.2300] |
| Continuation B | -0.3224 | [-0.4326, -0.2123] |
| Continuation C | -0.3225 | [-0.4451, -0.2000] |
| Continuation E | -0.3169 | [-0.4097, -0.2241] |
| Inside B | -0.1492 | [-0.2735, -0.0248] |

All six intervals are entirely negative. This is a prose error, not a fee calculation error.
Calling losing lines flat hides precisely the unfavorable evidence this research is meant to
surface. These are the declared normal intervals, not new claims of independent observations
or out-of-sample significance.

**Action:** distinguish positive, negative, and zero-crossing lines throughout the receipt,
ledger, and handoff synthesis. Retain the three-positive-lines statement with its sample and
cost-model qualifications. Check any republished explanatory text against the same data.

### Attacked, held, and boundaries

- **Headline preservation:** ran the base `coin_manage_rows()` loaded directly from
  `git show 4dc5f6b:analysis/domino/manage.py` and the reviewed version over all eligible cached
  coins. All 179,498 rows match on all 16,609,608 pre-existing field comparisons. Independently
  compared the reviewed replay to the saved CSV: 20,642,270 fields match exactly after type
  decoding. An initial pandas check mapped literal `n/a` to NaN; corrected the probe to read
  raw CSV strings before making this exact-match claim.
- **Committed aggregates:** every old `manage.json` top-level field except the additive counts
  block is identical to the base; every old count is preserved. All old Markdown table lines
  are identical. The entire Markdown FILE is not byte-identical: line 3 adds hourly counters
  and the A2 section is appended. This is consistent with unchanged headline numbers.
- **A2 replay:** fresh 179,498-row replay reproduces all count values and candidate summaries
  (numeric aggregate tolerance 1e-12). Reproduction does not repair F1/F2.
- **Under-water exit:** an independent daily-bar oracle checked 178,203 eligible status values
  and 177,665 settled durations/returns, with zero differences. Strict close-through-L and
  week-against predicates hold. The original colour clock remains unchanged.
- **Week side:** independently checked all 179,498 `w_support` values against entry price and
  calendar week open, including equality-as-against. Zero differences. Candidate WITH/AGAINST
  reach denominators are the same T1/reference cohort as their book lines, not all daily units.
- **E and fees:** E implements `(A+C)/2` on target hits and C otherwise. No-hit A equals C.
  The declared main/xyz rate mapping and `gross - 2*taker` arithmetic reproduce. For E this is
  two full-notional-equivalent charges, although its exits may be two half fills. These are
  the preregistered fixed percentages of entry notional, not a fresh validation of current
  venue pricing, funding, slippage, or fees on changing exit notional.
- **Ordering claim:** for any valid target strictly beyond L, a touch implies a strict break
  of L. This includes the positive-range measured move and nonzero one R, long or short.
  Thus it cannot precede the true entry hour on a fully observed price path. The hourly exit
  day's suffix is excluded while daily OHLC includes the whole day; the exit day can itself
  be the entry day. This geometric fact does not cure missing coverage or equality entry.
- **Hourly normal path:** entry-hour inclusion, two strict exit tests using the hour's own open
  and the daily candle's open, no week test, a fully covered day-20 23:00 OPEN mark, and a
  truncated tail's CENSORED result pass the existing vectors. F3 attacks a different shape.
- **Viewer fill algebra:** for available books the return inversion agrees with the engine's
  intended fill within floating-point tolerance, including OPEN marks, reference five-bar
  marks, and all 11 headline shorts below -100%. There is no reciprocal-return or sign bug.
  F4 concerns reusing that approximate number as an exact predicate; F6 concerns missing books.
- **Other stack prices:** checked all 236,814 displayed timeframe/row level instances against
  the census's actual `day_events()` broken-level dictionary, with zero mismatches. `stack`
  already restricts the other frames to their first break in the current bar, and the census
  requires a complete adjacent predecessor. No second freshness detector is needed for these
  recorded rows. This validates the prices, not the full-stack labels in F7.
- **Marker binding:** the repaired `if/else` at app.js:264-266 is correctly contiguous. The
  headline square at line 268 requires a different settled day and a real headline exit.
  The A2 squares no longer bind the data-end branch. F5 is an independent settlement-kind bug.
- **Calendar and ray limits:** the two-year Node/Python calendar test passes. The ray source
  snaps to OHLC on the active view and stores by coin; persistent ray interaction was not
  exercised. No claim of exhaustive interaction, mobile layout, or concurrent-fetch testing.
- **Scope:** no Pine changed, so no new `request.security` call was introduced. This audit does
  not reopen the folded TVB-38/A1 engine or the private executor findings. No strategy is
  promoted, and no live order or venue data request was made.

### Open T1 question -- texts and interpretation only

The prereg is explicit: `docs/experiments/tvb37_management_book_prereg.md:83-88` assigns the
with-trend 2-1-2 inside break no own magnitude and uses the first weekly/monthly rung.
`analysis/domino/manage.py:185-192,205-210` follows that definition. This is not a new TVB-39
implementation deviation from the prereg.

The local skill consulted was
`C:/Users/Chris/.claude/skills/strat-methodology/SKILL.md`. Its 2-1-2 continuation row at line 56
says `reversal-exit`; lines 70-73 define that term as magnitude at unfilled structure containing
the trigger, otherwise a measured move, with a reversal combo as the exit signal. Lines
388-393 repeat that R14/R18 rule. Read together, these support treating an unfilled containing
mother bar's far side as magnitude. The row's `reversal-exit` label is not an instruction to
skip that structure and jump to W/M. It also does not force an all-out exit at magnitude;
management there is profile-dependent.

For the recorded BTC 2026-03-25 example, that reading supports examining the mother high as
a magnitude, while the existing prereg still directs the engine to the W/M ladder. This is
the already-open methodological discrepancy. The owner decides whether to amend it. No A3,
new target rule, or replacement daily-exit rule is authorized by this audit.

### Verification and reproduction notes

Commands used from the resolved repository root:

```text
git diff --name-status 4dc5f6b..30391fb
git diff --name-status 30391fb..HEAD
.venv\Scripts\python.exe -B -m pytest tests/ -q -p no:cacheprovider --tb=short
.venv\Scripts\ruff.exe check --no-cache .
node --check analysis/domino/viewer/app.js
```

Results: **372 passed, 2 skipped**; Ruff clean; JavaScript syntax clean. The first sandboxed
test attempts produced 361 passes and 11 fixture setup errors because temporary directories
were denied. The same suite passed outside that sandbox; those were environment failures.
The scanner's `scan_file()` and existing allowlist were applied to the 17 pinned changed paths:
zero findings. Both viewer data and vendor paths are ignored. `serve()` and its CLI default to
loopback; broader binding requires an explicit host argument (`trade_viewer.py:272,280-281,305`).
No private report link was found in the reviewed additions.

Offline replays called functions directly and retained rows/results in memory; neither the
management CLI nor viewer build CLI was run because they write generated artifacts. All
584 stamped daily/hourly files were present. Evidence fingerprints:

```text
manage_trades.csv.gz SHA256:
9a5299c30e648b490e05c1e54f11d8a380a6c9f0b19d00683cedcb3a406ff591
cache manifest SHA256:
ba515d1170e48c6521e5e4e86c6fb2b6ae4b0391620196f4373ae75ecb99702e
```

The cache digest hashes each sorted `*_1[dh]_20261010.json` filename, a NUL byte, and the binary
SHA256 digest of that file. These identify local evidence; gitignored cache provenance is not
made immutable by a source commit. The current viewer's existing data was inspected, not rebuilt.

F1 can be reproduced without generating files by loading ACE's stamped daily/hourly JSON,
normalizing at `parse_as_of('2026-10-10')`, locating daily 2026-04-29, and calling
`walk_hourly(hours, hours_by_day(hours), days, i, 'up', 0.1255, {}, i+20)`. It returns entry
hour 0, zero hours held, and -0.7171314741%; independently searching `high > 0.1255` gives hour 2.
F2 uses the same procedure on APEX 2026-03-18 at L=0.29706.

Minimal F3 fixture extension (run in memory after importing the existing test helpers):

```python
from tests.test_domino_manage_a2 import _series, hours, green, TUE
from analysis.domino.census import DAY, HOUR
from analysis.domino.manage import walk_hourly, hours_by_day
daily = _series(list(green(TUE + DAY, o=101.8, k=25)))
hourly = hours(daily)
for b in hourly:
    b['o'] = b['c'] - 0.1
i = next(j for j, d in enumerate(daily) if d['t'] == TUE)
cap = daily[i + 20]['t']
hourly = [b for b in hourly if b['t'] != cap + 23 * HOUR]
for b in hourly:
    if b['t'] == cap + DAY + HOUR:
        b.update(o=102.0, h=102.1, l=99.0, c=99.0)
w = walk_hourly(hourly, hours_by_day(hourly), daily, i, 'up', 101.0, {}, i + 20)
print(w['status'], (hourly[w['end']]['t'] - TUE) // DAY, w['hours'])
# reviewed code: exit 21 504
```

Viewer probes executed app.js in Node with initialization replaced in memory by exports of
the existing functions and state, supplying recorded viewer JSON and chart-method capture
stubs. No source file was edited. Rendered desktop checks also inspected these bookmark
fragments on a temporary local server:

```text
#coin=ATOM&date=2026-05-09&tf=D&dir=up&view=1H&book=A
#coin=0G&date=2026-05-17&tf=M&dir=down&view=1D&book=ref
#coin=0G&date=2026-08-31&tf=D&dir=up&view=1D&book=C
#coin=BTC&date=2026-03-16&tf=W&dir=up&view=1H&book=ref
```

The temporary server and browser tab were closed. Screenshots were inspected in the tool
session, not saved as additional artifacts. Checks demonstrate the named defects and normal
paths, not exhaustive viewer correctness or live execution readiness.

## 3. Actionable items (reviewer's own list)

1. **F1 -- HIGH** -- `analysis/domino/manage.py:426-427`: strict hourly entry; mirror in
   `viewer/app.js:254`; add equality-before-break cases and rerun A2 hourly results.
2. **F2 -- MEDIUM** -- `analysis/domino/manage.py:419-430`: reject unknown entry prefixes,
   count missing coverage, and rebuild the paired cohort.
3. **F3 -- MEDIUM** -- `analysis/domino/manage.py:434-445,472`: enforce the absolute cap and
   coverage continuity; use timestamp durations; test holes followed by later data.
4. **F4 -- MEDIUM** -- `analysis/domino/viewer/app.js:76,252,264`: canonical prices for touch
   matching, and an explicit unknown marker when no candle matches.
5. **F5 -- MEDIUM** -- `analysis/domino/viewer/app.js:88,265`: route stop exits to the recorded
   stop-day touch, keeping daily ordering assumptions visible.
6. **F6 -- MEDIUM** -- `analysis/domino/viewer/app.js:81`: preserve the selected book when its
   outcome is unavailable; never substitute C's closure.
7. **F7 -- MEDIUM** -- `analysis/domino/viewer/app.js:232-234,329-331`: distinguish the
   converged subset and entry-time class from the retrospective whole-day stack.
8. **F8 -- MEDIUM** -- `analysis/domino/MANAGE_RECEIPT.md:313` and
   `docs/ARM_LEDGER.md:680`: correct the six negative net lines and reconcile downstream prose.

## Suggested prompt

Adjudicate TVB-39 F1-F8 individually. Repair the hourly entry and coverage contracts, preserve
the existing daily headline, and rerun on the same snapshot. Add viewer tests of settlement
identity, canonical prices, stop/target/mark hours, unknown evidence, and subset labels, using
the named cached cases. Correct the fee narrative against the generated tables. Record which
findings are accepted or disputed with evidence in HANDOFF. Keep the with-trend inside-break
T1 and replacement exit rules open for the owner's ruling; do not fold a methodology change
into these correctness repairs.
