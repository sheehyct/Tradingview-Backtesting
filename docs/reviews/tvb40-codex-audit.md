# TVB-40 External Audit -- Codex (verbatim source, read CRITICALLY)

> External review of `9f6c5c8..2c7fe1c`, captured 2026-10-29 (TVB-40 post-session).
> Plain ASCII. This is the external assessment, not the critical synthesis.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs
> variant, or over/under-state a risk. The next Claude session should adjudicate these
> findings in `docs/HANDOFF.md`.

---

## 1. Metadata

- **Session:** TVB-40 -- amCharts trade-viewer promotion, narration, Compare and calendar.
- **Reviewed:** `9f6c5c8..2c7fe1c` on main. No sibling repositories.
- **Reviewer:** Codex; local source review, recorded-data probes, Python and Node execution.
- **Overall verdict:** **NEEDS-CHANGES** -- six new MEDIUM finding groups below.
- **Authority:** `docs/reviews/REVIEW_REQUEST.md` was REQUESTED and this audit did not exist.
  Followed the session-review skill, local protocol/template, governing context, and the
  work order's read-first packet.
- **Checkout:** `8351054586c5299784e02d6a4e510e6912fad56d`. Later work exists, but
  `git diff 2c7fe1c HEAD -- analysis/domino/viewer analysis/domino/trade_viewer.py
  tests/test_domino_viewer.py` is empty. The referenced `manage.py` also matches the pin.
  Source citations below therefore apply to `2c7fe1c`.
- **Exclusions:** the maintenance hooks, untracked `proto_codex/`, engine redesign, and
  re-adjudication of TVB-39 F1-F8. Existing `User_Notes.md` was left alone.
- **Write scope:** this audit only. No source, generated data, vendor, HANDOFF, request status,
  git state, or configuration changes. No build, fetch, commit, or push.

## 2. Verbatim audit

The columnar universe and most arithmetic reproduce. The promotion also preserves the old
settlement logic, including its already-reported defects. New problems remain in the
drawdown definition, magnet candle selection, narrative claims, selected-book travel,
calendar averages, and table sorting. These matter because the viewer is meant to help
identify modeling errors; its own explanations must not manufacture contradictory evidence.

### F1 -- MEDIUM -- Compare drawdown uses a different path from the engine and plotted curve

**Evidence:** `analysis/domino/viewer/stats.js:25-32` versus
`analysis/domino/manage.py:815-827`; the claimed agreement is in
`analysis/domino/viewer/NOTES.md:74-83`.

The engine sums returns by entry date before calculating cumulative equity and drawdown.
The viewer updates its peak and drawdown after every row, ordered by date, coin and row
index, then collapses those intermediate points for the displayed daily curve. The card
therefore measures an artificial within-day path that neither the engine nor the chart uses.
The comment that this ordering is "the engine's" is incorrect.

**Reproduced:** all six universe books differ. At equal size 1,000, using exactly the same
three-decimal universe returns on both sides:

| Book | Viewer max drawdown magnitude | Drawdown of its daily curve |
|---|---:|---:|
| C | 629,980.77 | 629,820.35 |
| A | 370,576.71 | 370,407.05 |
| B | 529,318.11 | 529,157.69 |
| D | 104,496.58 | 103,822.80 |
| D5 | 94,965.97 | 94,212.09 |
| Chance | 797,742.47 | 797,598.64 |

This is not rounding. With full-precision BTC rows, book A reports 1,745.648520861 in the
viewer versus 1,732.066668528 in the engine and daily curve. The receipt's universe C value
reproduces the viewer's row-level definition, not the engine's definition.

**Action:** calculate drawdown from completed daily sums, as `manage.book_stats()` does.
If a separate row-sequenced metric is desired, name it separately and disclose that the
sequence is not observed execution order. Correct the verification receipt and test
opposing same-day returns and the BTC A example.

### F2 -- MEDIUM -- The magnet selects the next candle on the current candle's right half

**Evidence:** `analysis/domino/viewer/app.js:123-130`; the proof flag's click position is
`analysis/domino/viewer/app.js:372`.

The axis conversion yields a time within the candle's interval. The following search picks
the nearest bar OPEN timestamp. Candles are centered within their intervals, so after the
interval midpoint that search prefers the next bar, even while the pointer is beside or
inside the current candle. Correct pixel-to-axis inversion does not fix this selection step.

**Reproduced in memory using the installed amCharts `GaplessDateAxis` and `AxisRendererX`
methods plus the actual `magnetDrop()`:** BTC 2026-03-25, 1D, an 11-day visible range.
At the March 25 high's y coordinate, x fractions 0.25 and 0.49 within that day's cell snap
to its high, 72,034. Fractions 0.51 and 0.75 snap to 71,411, the March 26 high. The latter
click remains within March 25's interval. The supplied proof instead starts at the bar's
opening timestamp plus three pixels; it does not test the two sides of the candle center.

**Action:** select the axis cell/candle under the pointer, or compare candle-center pixel
coordinates, before choosing among that candle's O/H/L/C. Test both sides of candle centers
at several zooms and on 1H/1D/1W/1M, including variable-length months. This reproduction
used actual library axis methods with chart/render stubs; it is not a fresh mouse/browser test.

### F3 -- MEDIUM -- New exit narration contradicts direction, status, and ordering evidence

**Evidence:** `analysis/domino/viewer/story.js:92,97,103,114,126,223`.

Three independently reproduced branches overstate what the recorded columns say:

- **Short hourly exits use the long rule.** `otherClocks()` always says "first red hour
  while the day is red." BTC daily short, 2026-03-18, has `entry_h=11`, `exit_h=37`, and
  exits at 2026-03-20 00:00. That hour opens at 69,920 and closes at 70,189; the day's open
  is also 69,920. Both tests are green, correctly against the short. The wrong explanation
  is emitted for 27,674 recorded short rows with `status_h=exit`. The Playbook also states
  the hourly and own-bar rules only in long-side colors.
- **A mark is described as a clock exit.** ADA daily long, 2024-01-30, book A has
  `status=open`, `exit_k=null`, `days_A=20`, `hit_A=false`, and no T1 touch. The story says
  it "left with the daily clock," immediately followed by the correct statement that no
  daily exit fired and the row was marked at the cap. There are 66 A rows with this
  open/no-hit/present-T1 combination. B and D have the same unconditional exit wording.
- **A pessimistic daily tie is described as known stop-first chronology.** BTC daily long,
  2023-04-09, chance book has `stop_k=one_r_k=0`, `out5=stop`. Its story says the stop was
  hit "before one R." The daily row proves a same-day tie; the engine assigns the stop
  pessimistically (`analysis/domino/manage.py:594-603`). It does not establish intraday
  order. There are 7,061 filled chance rows with equal stop and one-R touch days.

**Action:** use direction-aware colors, branch on exit/open/censored status, and distinguish
known earlier-day stops from same-day pessimistic ordering. Add narrative assertions for
these recorded examples. Keep the existing engine rules; these are readback corrections.

### F4 -- MEDIUM -- Selected-book travel is actually book C's later travel

**Evidence:** `analysis/domino/viewer/app.js:419` and
`analysis/domino/viewer/story.js:159-160`; producer semantics at
`analysis/domino/manage.py:606-616`.

The selected book drives the exit and holding days, but both the facts strip and the story
always read `mfe_x`/`mae_x`, which are measured through the headline C settlement. The story
says "Between the entry and the exit" without identifying that different horizon.

**Reproduced:** BTC daily long, 2023-04-09, chance book leaves on day 0. C leaves on day 8.
The selected chance story nevertheless reports +10.27% best travel, from C's eight-day
window. The entry day's high is only 28,524 against entry 28,143, a maximum full-day
favorable move of 1.353800235%. The claimed 10.27% cannot belong to this selected holding
window, even before accounting for unknown intraday order.

This is separate from TVB-39 F6: the selected chance result here exists and there is no
settlement fallback. It is the new travel text/strip that combines incompatible windows.

**Action:** explicitly label these columns as travel through book C's exit/mark. If the UI
needs selected-book travel, record book-specific fields upstream and read those; do not
silently rerun trade logic in the page. Cover a valid target/stop exit earlier than C.

### F5 -- MEDIUM -- The calendar average treats censored rows as zero returns

**Evidence:** `analysis/domino/viewer/app.js:481-497` and
`analysis/domino/viewer/stats.js:86-95`.

`calendarDays()` correctly tracks both total rows and filled rows. The month footer sums
only available returns but divides by all rows (`mPct / mN`). Missing results thus dilute
the average toward zero. The day tooltip and Compare instead use filled counts.

**Reproduced:** all-coins calendar, October 2026, book C, all filters unrestricted:
2,802 rows, 1,656 filled, total -55,091.89 at size 1,000. The footer's arithmetic prints
-1.97%; the average of its available returns is -3.33%. An entirely censored selection
would print an apparent 0.00% average instead of unavailable.

**Action:** accumulate a monthly filled count and divide by that, showing unavailable when
it is zero. Retain the all-row trade count as a separate count and disclose incomplete
outcomes. Test mixed filled/censored and all-censored months.

### F6 -- MEDIUM -- Changing the book leaves a return/duration sort in the previous book's order

**Evidence:** `analysis/domino/viewer/app.js:436-439,513-523,755`.

`setBook()` refreshes row values and all views but never calls `sortItems()`. The sort
comparators read the selected book's return or holding days, so "best", "worst", and
"longest held" become false labels after changing the book through any of the selector,
ladder, or KPI-card paths.

**Reproduced by executing the actual `sortItems()` and `setBook()` with DOM stubs:** sort
BTC by best return in C, then select A. The first rows retain C's order, including A returns
7.233770701%, 1.097963143%, 16.144170295%. The +1.10% row (2024-02-24 daily) remains above
the +16.14% row (2023-03-12 daily) under the best-first selector. Reselecting the sort fixes
the ordering, confirming the missing update path.

**Action:** re-sort on book changes before rendering, retaining selection by row identity.
Exercise all three book-dependent sort modes and all book-selection controls.

### Inherited findings, held checks, and boundaries

- **TVB-39 remains pending:** see `docs/reviews/tvb39-codex-audit.md`, F4-F7. Their promoted
  paths remain at `core.js:90-128` and `app.js:274-311`: reconstructed-price thresholds,
  reference stops placed at day-end, unavailable-book fallback, and whole-stack class labels.
  They are not counted as new TVB-40 findings. The new story/strip also consume that shared
  logic, so the pending repairs must cover all consumers.
- **Founding rule:** compared `settle`, `tradeSpan`, `stackLevels`, and `setupDays` against
  `git show da7f4c2^:analysis/domino/viewer/app.js`. Apart from comments, calendar injection,
  and the default book changing from `state.book` to `C`, their behavior is preserved.
  Reviewed callers pass the selected book explicitly. No new trade-outcome engine was found
  in the new modules; derived fills and hourly marker searches retain the inherited limits.
- **Universe:** rebuilding `universe_table()` in memory from the CSV and serializing its
  code tuples to JSON arrays reproduces the existing universe object exactly: 179,498 rows.
  The first direct Python-object comparison differed only because tuples and JSON arrays
  have different Python types; JSON-normalized comparison passes. Decoding versus per-coin
  rows passed 4,307,952 field comparisons with the declared 0.0005 return-rounding bound,
  plus T1 presence and exit-day fallback checks for every row. Missing enum values decode
  as unavailable; they are not used to invent returns.
- **Statistics and filters:** 620 independent CSV-derived comparisons passed across all,
  liquid-only, T1-only, and combined scopes: row/filled counts, means, medians, totals,
  positive share, target share, holding days, win/loss means, extremes, paired D5-minus-chance
  results/counts, and histogram proportions including overflow bins. Both universe and coin
  paths use `filtered()` (`app.js:459,510-511,684`). These checks exclude the drawdown
  definition challenged in F1. An initial oracle used pandas rounding and differed by
  cents on half-way values; using round-trip CSV floats and Python's built-in `round`, as
  the exporter does, eliminated all 620-check discrepancies.
- **Closed bars:** the census calendar tests pass. Across the actual per-coin data, all
  38,326 week/month buckets' `complete` flags agree with full contiguous day coverage.
  `htfType()` excludes the entry bucket and requires both preceding buckets complete;
  `barType()` uses strict high/low breaks. No new lookahead/edge-coverage finding here.
- **Drawing persistence:** source-reviewed `makePane`, `swapDrawings`, `loadCoin`, layout
  and tab paths, plus the installed library's save/restore code. Pane slots are distinct,
  and ordinary timeframe/tab changes do not call `swapDrawings`. This is NOT proof of
  persistence across coin switching, rapid switches, hidden-pane restoration, manual
  toolbar autosave, or delayed library deserialization. `unserializeDrawings()` is
  asynchronous and the application's guard is a fixed 500 ms; the library also has its
  own autosave listener. Those paths need isolated browser tests before a broad persistence
  claim. No data-loss finding is asserted from source inspection alone.
- **Visual evidence:** inspected the committed BTC magnet screenshot. It confirms a
  previously rendered line, not the full pointer-selection behavior or a fresh browser run.
  No live browser, real drag, reload, or persistence test was performed in this audit.
- **Hygiene:** Ruff passes. The scoped secret scan found no findings; output was restricted
  to locations, never token/IP contents. `git check-ignore` confirms viewer data, vendor,
  and prototype vendor are ignored. The prototype remains untracked. The pinned range has
  no net `.gitignore` diff despite the handoff's mention of edits. No Pine changed.
  CDN fetching was not invoked; its floating 5.x URL and existing-file skip mean a future
  clean download is not proven equivalent to the locally inspected vendor.

### Validation record and reproduction notes

Commands executed without bytecode/cache writes:

```text
$env:PYTHONDONTWRITEBYTECODE='1'
python -B -m pytest tests/test_domino_viewer.py tests/test_domino_manage.py tests/test_domino_manage_a2.py tests/test_domino_census.py -q -p no:cacheprovider
44 passed in 0.62s
ruff check . --no-cache
All checks passed!
```

The four viewer tests also passed separately. The historical 372-pass/2-skip full-suite
claim was not rerun; the selected suite and read-only probes are the evidence here.

Node probes loaded `core.js`, `stats.js`, and `story.js` into a VM. For application probes,
only the in-memory copy of app.js's final `init().catch(...)` call was replaced with exports
of its existing functions and state. DOM/chart sinks were stubbed; source files were not
edited. The magnet probe additionally loaded the installed amCharts bundles and invoked
their actual axis prototype methods. No synthetic market data was used.

Useful reproducible checks:

```javascript
// After loading core.js/stats.js and decoding universe.json into u:
const s = DV.stats.bookStats(u.map(t => ({coin: t.coin, t})), "D5", 1000);
let peak = 0, dailyDD = 0;
for (const point of s.curve) {
  peak = Math.max(peak, point.v);
  dailyDD = Math.max(dailyDD, peak - point.v);
}
// s.maxDD = 94965.97000000036; dailyDD = 94212.09000000029.
```

For F2, use BTC daily bars, the March 25 index k, axis start `(k-5)/N`, end `(k+6)/N`,
and a 1,000-pixel renderer width. Convert `(k+0.49)/N` and `(k+0.51)/N` through the actual
X renderer, with y at March 25's high, and call `magnetDrop`. The snapped prices are 72,034
and 71,411 respectively. The y stub was a regular linear price axis, sufficient to preserve
nearest-OHLC ordering; logarithmic/percent scale interaction remains untested.

Local evidence SHA256 fingerprints (gitignored evidence is not pinned by a source commit):

```text
manage_trades.csv.gz
9a5299c30e648b490e05c1e54f11d8a380a6c9f0b19d00683cedcb3a406ff591
viewer/data/universe.json
f4aec2928a5f61447b3fc579ac155460d12deeca9630b2470976b4e08a2effdd
viewer/vendor/amcharts5/xy.js
8dffc855499938353f51649654364be895160c1aceb461097ec58feda54948ff
viewer/vendor/amcharts5/stock.js
522a63710f062384e033e7d25a85819e83bf64b5859e1da1efea75dbed3e91fd
```

## 3. Actionable items (reviewer's own list)

1. **F1 -- MEDIUM** -- `analysis/domino/viewer/stats.js:31`: compute drawdown after daily
   aggregation; reconcile the receipt's verification claim with `manage.py:815-827`.
2. **F2 -- MEDIUM** -- `analysis/domino/viewer/app.js:125`: choose the candle by its cell
   or visual center before snapping its OHLC; cover center boundaries and zoom/timeframe changes.
3. **F3 -- MEDIUM** -- `analysis/domino/viewer/story.js:92,114,126`: make color, settlement
   status, and same-day uncertainty faithful to the row; correct the Playbook counterparts.
4. **F4 -- MEDIUM** -- `analysis/domino/viewer/story.js:159` and `app.js:419`: label the
   C-window travel explicitly or consume separately recorded selected-book travel.
5. **F5 -- MEDIUM** -- `analysis/domino/viewer/app.js:497`: divide monthly return sums by
   filled rows, not all rows; show unavailable for all-censored selections.
6. **F6 -- MEDIUM** -- `analysis/domino/viewer/app.js:436-439`: reapply the active sort when
   the book changes, preserving selection identity.

## Suggested prompt

Adjudicate the pending TVB-39 audit first, then TVB-40 F1-F6 with the recorded examples above.
Keep model-rule changes separate from display corrections. Add focused JS coverage for
daily drawdown, magnet candle selection, narrative direction/status/ties, travel horizon,
censored calendar denominators, and book-dependent sorting. Verify drawing persistence in
isolated browser storage across both panes and coin switches, including toolbar autosave
and delayed restoration. Update NOTES only with checks actually rerun, and write the critical
synthesis in HANDOFF.
