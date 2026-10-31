# TVB-41 External Audit -- Codex (verbatim source, read CRITICALLY)

> External review of `8351054..74dcb28` captured 2026-10-30
> (TVB-41 post-session). Plain ASCII throughout.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-41 -- hourly-clock repair, viewer repairs, rerun and framing.
- **Reviewed:** `8351054..74dcb28` on `main`, as requested by `docs/reviews/REVIEW_REQUEST.md`.
- **Checkout:** `2f3a3a84281b89fb5f000c141b86fa03a2dfd68a`. Changes after the pinned head affect
  only `.session_startup_prompt.md`, `docs/HANDOFF.md` and `docs/reviews/REVIEW_REQUEST.md`.
  Reviewed implementation and results match the pinned head.
- **Reviewer:** Codex, local source review, cached-data replay and Python/Node probes.
- **Overall verdict:** **NEEDS-CHANGES** -- two MEDIUM findings, one viewer narration defect
  and one inaccurate account of the rerun. No new engine correctness defect established.
- **Scope:** Check the repairs and their claims, not re-adjudicate TVB-39/40. No sibling
  repositories, STRAT ML work, cc scripts, or ruling on the pending inside-break T1 question.

## 2. Verbatim audit

The hourly-clock repair reproduces on the cached snapshot. The committed daily aggregates
are unchanged, and the new hourly columns reproduce from the normalized candles. Most viewer
repairs also pass direct checks. Two remaining problems prevent accepting the session's
readback as fully correct: D5 can still describe its fill as a day-20 mark when it exited
later, and the receipt describes statistical changes that did not happen.

### F1 -- MEDIUM -- D5's corrected exit reason still appends book C's clock narrative

**Evidence:** `analysis/domino/viewer/story.js:85`, `analysis/domino/viewer/story.js:111`,
`analysis/domino/viewer/story.js:78`; the corresponding coverage stops at settlement in
`tests/test_domino_viewer_js.py:156`.

The repaired `settle()` correctly reads `status5` for D5, including weekly/monthly units
whose five-bar window extends beyond the headline's 20-day cap. However, the D5 exit branch
appends `clock`, which was built from `t.status` and `t.exit_k`, the headline book's fields.
When D5 exits after day 20 and C is OPEN, the paragraph says both that the daily clock fired
and that the row was marked at the day-20 close. It never describes D5's actual exit day.

**Reproduced on saved data:** BLUR, 2026-07-24, weekly short, book D5:

- `status = open`, `days = 20`, `ret_C = 12.844158429...`.
- `status5 = exit`, `days_D5 = 24`, `hit_D5 = false`, `ret_D5 = 13.096264844...`.
- `settle(t, "D5")` correctly returns day 24, price 0.013099, `daily-close exit`.
- The marker probe places the exit on 2026-08-17 at 23:00 UTC.
- The story says: "The daily clock fired first. No daily close went against the trade with
  the week against it inside the 20-day cap, so the row is marked at the day-20 close.
  Result +13.10% ..."

There are **24 recorded rows** matching `status5 == exit`, `status == open`,
`hit_D5 == false`, with a recorded D5 return. This is a remaining integration defect in
the TVB-41 cold-review M4 repair, not a dispute over the engine's exit rule. The numeric
result and chart exit can be correct while the selected book's explanation names the wrong
time and mechanism.

**Fix:** Make clock narration accept the selected book's status and exit offset. For this
D5 branch, describe `status5` and `days_D5`, reading that day's candle and weekly open.
Keep headline-C narration separately identified if it is useful. Extend the existing
weekly-row test through `S.narrate()`, asserting day 27/the actual date and rejecting the
day-20 marking sentence; add a monthly example too.

Minimal reproduction, from the repository root, using the existing viewer data:

```powershell
@'
const fs = require('fs'), vm = require('vm');
global.window = {}; global.document = {getElementById: () => null};
for (const f of ['core', 'stats', 'story'])
  vm.runInThisContext(fs.readFileSync('analysis/domino/viewer/' + f + '.js', 'utf8'));
const d = JSON.parse(fs.readFileSync('analysis/domino/viewer/data/BLUR.json'));
const t = d.trades.find(t => t.date === '2026-07-24' && t.tf === 'W' && t.direction === 'down');
const C = window.DV.core;
console.log(C.settle(t, 'D5'));
console.log(window.DV.story.narrate({t, coin: d.coin, cal: C.makeCalendar(d),
  book: 'D5', size: 1000, p: 6}).split('What book D5 did.')[1].split('</p>')[0]);
'@ | node
```

### F2 -- MEDIUM -- The rerun summary invents an interval transition and misses a sign change

**Evidence:** `analysis/domino/MANAGE_RECEIPT.md:309` through line 312,
`docs/HANDOFF.md:63` through line 65, and `docs/ARM_LEDGER.md:679`.
The underlying table is `analysis/domino/results/manage_tables.md:990` and line 992;
the exact values are in `manage.json`, under `candidates.<kind>.hourly` at both commits.

The receipt says no paired line changed sign or changed whether its interval cleared zero,
except the reversal exit-only line, whose interval "now spans zero." The committed numbers
contradict both parts:

| Paired comparison | Before, `3fa6990` | After, `74dcb28` | Actual change |
|---|---|---|---|
| Reversal C_h - C, 95% interval | [-0.283879, +0.007148] | [-0.263347, +0.029019] | Both already span zero; no transition |
| Inside D_h - D, mean difference | -0.001988765 | +0.008228212 | Point estimate changes sign; both intervals span zero |

The receipt itself prints the old reversal interval as `[-0.28, +0.01]`, so the claimed
transition is contradicted even by its rounded figures. "No sign moved" is also repeated
in the handoff and ledger. The inside-D change is small and does not establish an advantage,
but it must not be described as absent.

The same paragraph says the hourly subset lost 264 rows. The actual contraction is
**261 scored rows**, from 55,112 to 54,851. There are 264 partial-entry exclusions after
the repair: 261 formerly scored rows plus three formerly excluded `no_entry_hour` rows.
The in-memory replay reproduced all these counts.

**Fix:** Say that the reversal paired interval continues to span zero, that the small
inside-D paired point estimate crosses zero while its interval continues to span zero,
and distinguish the 264 exclusion count from the 261-row contraction. Correct the receipt,
handoff and ledger together. No change to research parameters or engine arithmetic is
needed. Do not substitute a strategy verdict for these descriptive corrections.

### Verified repairs and bounded evidence

**Hourly engine and snapshot.** Reviewed `walk_hourly` and its caller, the unchanged v17
vectors, v20a-e, and the dated prereg clarification. The strict-break operators agree with
the repository's methodology reference. Replay used the cached `20261010` daily/hourly
candles, the current normalizers, the recorded row's prices, and each row's cap. The old
`walk_hourly` function was loaded from `3fa6990` into memory for comparison; no checkout or
generated result was changed.

| Check | Reproduced result |
|---|---|
| Source universe / saved row count | 288 coins / 179,498 rows |
| New hourly status counts on headline-scored rows | 54,851 exit; 264 partial_entry_day; 123,088 outside_window |
| Old hourly status counts | 55,112 exit; 3 no_entry_hour; 123,088 outside_window |
| Changed hourly rows | 1,473 |
| New hourly fields versus saved CSV | No mismatches across status, entry/exit/duration, C/A/D returns, A/D hits and T1 hour |
| Partial-entry rows at first calendar day of hourly cache | All 264, across 204 coins; cache starts at hours 2-7 UTC |
| Internal gaps after hourly normalization | Zero |
| Open / censored hourly results on this snapshot | Zero / zero |
| Scored rows with `cap_end is None` | 5,050; all have an observed hourly exit |
| Normalized cached bars versus viewer-exported bars | No daily or hourly mismatches across the active 288 coins |

Numeric CSV comparisons used absolute tolerance 1e-10 and relative tolerance 1e-12;
categorical fields matched exactly. The zero censored count is supported by the paths,
not inferred merely from the absence of gaps. Additional in-memory checks with
`cap_end=None` return censored without an exit and exit when an observed qualifying hour
exists. The existing tests cover strict long/short entry, gaps before/after entry and exit,
missing cap hours, later data beyond the cap, and an exactly observed cap.

**Daily-headline claim.** Recursive comparison of committed `manage.json` at `3fa6990`
and `74dcb28` found 221 changed leaf paths, all inside hourly candidate blocks or hourly
counters; **zero non-hourly changes**. The markdown diff contains only the hourly counters
and four A2.2 table rows. This verifies the work order's committed-artifact alternative.
I did not regenerate the entire old management CSV, so the stronger claim that every old
non-hourly CSV field is byte-identical is not independently established here.

Saved CSV inspected: `analysis/domino/results/manage_trades.csv.gz`, SHA256
`1de152388297a076c2bd165b2b4904ea13c90ccd1f593afc4e2c3807e99b1122`.

**Viewer settlement and stacks.** All six books were checked over the saved viewer rows.
There were 10,715 missing settlements, no borrowed return/price, no wrong book identity,
and no non-finite end index. D5's 74,133 target exits all select the same one-R price as
the core helper. The selected-book callers were inspected, including the ladder, strip,
table title, story, span and chart missing-result marker. Missing non-C books use the
final cold-review contract, `k = 0`, rather than the superseded borrowed-window proposal.

The final classed-pair implementation was checked against the daily-denominator directional
bands: 35,239 available pairs with zero band mismatches; 143,008 plain daily rows keep only
their own level in the pair. For 1,251 other rows the nearest classed level did not break
that day and is absent from the day's stack. The 1,387 extra levels on the negative side of
entry remain outside the selected pair and retain their signed distance. No new class
selection error was established.

**Markers.** Executed the actual marker-construction source block from `app.js` under Node
with normalized exported bars, without the DOM/renderer. Named checks include ATOM
2026-05-09 long book D (one-R circle and exit together on May 11 at 09:00), ACE 2026-06-14
long book D (both on June 15 at 12:00), BTC 2026-03-16 weekly long reference (stop and exit
together on March 27 at 14:00), and ACE 2026-04-29 long (entry 02:00, hourly exit 03:00).

A separate threshold audit covered 121,512 recorded target/stop exits with candles on the
exit day, including 13,540 short reference-stop exits. The 1e-9 tolerance repaired 222
floating-point touch selections and produced zero differences from exact-decimal touch
selection. Seventeen searches had no observed touch; the code provides a labelled last-bar
fallback for such multi-hour days. No new silent-drop defect was established. Maximum
relative one-R reconstruction error across the rows was about 7.35e-13, below the tolerance.
Exits outside the hourly window were excluded from this threshold check.

**Statistics and remaining readback.** Daily-sum drawdown reproduces independently in
pandas. Node's universe figures differ from full-precision CSV figures by at most 1.26
at the 1,000-per-row display size, consistent with the universe export's three-decimal
returns. The month denominator uses filled rows; the zero-filled case says n/a. Tests and
source checks support direction-aware hourly wording, exact same-day stop/one-R tie wording,
open/censored no-target wording, the book-C travel label, and re-sorting on book changes.
The unequal-month cell and first/last-bar tests pass. These are arithmetic and source-level
checks, not proof of mouse coordinates or rendering in amCharts.

The fee-prose repair agrees with the unchanged A2.4 table: six management lines are
negative net with intervals clear of zero. The charter change preserves the author's
neutral characterization stance and the warning against confirmation-seeking. No Pine
code changed, and no new `request.security` call was introduced.

### Commands, hygiene and limits

- `git diff --name-status 8351054..74dcb28`: scope matched the work order.
- `git diff --check 8351054..74dcb28`: clean.
- With `PYTHONDONTWRITEBYTECODE=1`, `.venv\Scripts\python.exe -B -m pytest tests/ -q -p no:cacheprovider`:
  **435 passed, 2 skipped**, 7.63 seconds of reported pytest time.
- `.venv\Scripts\ruff.exe check --no-cache .`: clean.
- `node --check` on `core.js`, `stats.js`, `story.js`, `app.js`: all passed.
- `.venv\Scripts\python.exe -B scripts/secret_scan.py --range 8351054`: clean, 20 files.
  This scanner accepts a base, so its range also includes the subsequent docs-only pinning.
- No private chat links found in the changed files. Data, vendor library and the row CSV
  remain gitignored; `proto_codex/` and `User_Notes.md` were pre-existing untracked content.
- No fresh rendered-browser pass, mouse interaction, or drawing-persistence check was done.
  The session already records those limits; passing Node checks does not remove them.
- All probes were read-only or transient test execution. The sole persistent review write
  is this audit. No source repair, data rebuild, request-status update or critical synthesis
  was performed.

## 3. Actionable items (reviewer's own list, if provided)

1. **F1 -- MEDIUM** -- `analysis/domino/viewer/story.js:111`: narrate a D5 daily-close exit
   from `status5` and `days_D5`; test the complete paragraph on weekly/monthly exits after
   the headline cap, not only `settle()`.
2. **F2 -- MEDIUM** -- `analysis/domino/MANAGE_RECEIPT.md:309`, `docs/HANDOFF.md:63`,
   `docs/ARM_LEDGER.md:679`: correct the interval/sign account and separate 264 partial-entry
   exclusions from 261 formerly scored rows removed. Preserve the verified engine results.
