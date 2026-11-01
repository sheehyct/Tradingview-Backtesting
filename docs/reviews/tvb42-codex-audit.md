# TVB-42 External Audit -- Codex (verbatim source, read CRITICALLY)

> External review of 2f3a3a8..57c054c captured 2026-11-01
> (TVB-42 post-session). Plain ASCII.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-42 -- run contract, importer/exporter, and viewer stage 2.
- **Reviewed:** `2f3a3a8..57c054c` on main.
- **Checkout inspected:** `8a5806cb1943e0024db2a1a9d6fd9f903186ef30`. The only changes after
  the pinned endpoint are two review-range lines in HANDOFF and REVIEW_REQUEST; source matches
  the pinned endpoint.
- **Reviewer:** Codex, local tools; Python and Node probes against the checkout and saved data.
- **Overall verdict:** **NEEDS-CHANGES**.
- **Findings:** two HIGH, five MEDIUM, one LOW.
- **Write scope:** this audit only. No implementation repair, data regeneration, configuration
  change, commit, or HANDOFF synthesis. Existing User_Notes.md and proto_codex/ left alone.

## 2. Verbatim audit

The saved management-book export is substantially better supported than its regression guard
alone implies. All 179,498 cards passed the existing check, and an independent comparison
against the saved CSV found no differences in 4,314,995 field checks, including the grouped
clock books' returns and timestamps. The two TVB-41 repairs also hold.

The problems are in importing/replacing runs, deriving sparse extras, explaining exits and
target shares, and changing runs while universe data is selected or loading. Passing the
existing tests does not cover these paths.

### F1 -- HIGH: accepted identifiers can escape the run's directory

**Evidence:** analysis/domino/contract.py:60-61, 97-98, 185-187, 507-508, 608-612, 632.

The run-id predicate accepts both "." and "..". Consequently an otherwise valid run with
id "." targets the entire runs directory, and id ".." resolves to its parent data directory.
import_run passes that destination to shutil.rmtree before importing. This is not just an
unusual filename: it exposes every saved run, and potentially the flat data, to deletion.

The single-file instrument path has the same missing containment boundary on Windows.
_fname replaces ":" and "/" but preserves backslashes, while validate_file accepts any
nonempty instrument string. The instrument string containing two parent-directory components
followed by "outside" produces a destination outside the selected run folder.

**Reproduction, without deleting or writing real data:** run_doc(id=".") and run_doc(id="..")
from the existing contract test fixture both return [] from validate_run. Resolving
Path("mock-data") / "runs" / ".." yields mock-data. An instrument name with two Windows parent
components passes validate_file and resolves its JSON file to mock-data/outside.json rather
than mock-data/runs/test-run/. Destructive calls were mocked for this audit.

**Fix:** reject dot segments and unsafe filenames, and check resolved containment before every
removal/write. Instrument names should map to safe, collision-checked basenames. Validate the
export-run --id destination before export_run writes as well; trade_viewer.py:417 currently
constructs and writes that path before the importer validates it.

### F2 -- HIGH: refusing a replacement run destroys the previously imported run

**Evidence:** analysis/domino/contract.py:602-612, 618-637; 538-551, 568-569.

Only the run-level metadata is validated before deleting an existing destination. The card
validation happens afterward. Importing an updated single-file run under an existing id with,
for example, a missing target-fill price removes the old run, then refuses and removes the
replacement. runs.json still advertises the old id, whose files are gone.

There is also an in-place path bug: importing the existing destination's run.json file is
supported by load_source, but the in_place check compares that file path with the destination
directory. It therefore treats the operation as a replacement and removes the directory
whose instrument files the source factory is about to read.

**Reproduction:** using the existing test fixture with book A's price set to None and mocked
filesystem mutations, import_run calls rmtree on the existing destination before producing
ContractError, then calls rmtree again during cleanup. Passing
mock-data/runs/test-run/run.json also records a removal of mock-data/runs/test-run.
The current tests only prove invalid first imports and directory-form in-place imports.

**Fix:** validate and derive a replacement in staging, then replace the old run only after
success. Resolve the source's effective directory for in-place detection, including run.json.
Preserve the old run and registry on validation, read, or write failure.

### F3 -- MEDIUM: a zip containing the single-file flavor silently imports zero cards

**Evidence:** analysis/domino/contract.py:538-551, 552-567;
analysis/domino/viewer/CONTRACT.md:204-205.

A direct single JSON file is split through _is_inline/_split_single. The zip branch locates
run.json and calls load_source on its parent directory instead. The directory branch never
splits inline instruments and explicitly excludes run.json from the instrument files.
Thus a zip containing only an inline run.json validates successfully as an empty run.
Importing it replaces the inline instruments with an empty derived list.

**Reproduction:** a one-card run.json held in an in-memory ZipFile, with extraction and disk
access mocked, traversed the actual zip branch and produced zero files, zero validation
problems, and zero derived trades. The same JSON has one inline card. Existing zip coverage
uses a folder-style run.json plus X.json, which misses this case.

**Fix:** route the discovered run.json through the JSON-file loader so both flavors use the
same split logic. Add an equivalence check for direct JSON, zipped inline JSON, and folder
input, including their card counts.

### F4 -- MEDIUM: extras first appearing on a later card are attached to earlier cards

**Evidence:** analysis/domino/contract.py:437-472, 500;
analysis/domino/viewer/stats.js:134-138.

A newly discovered extras column starts empty rather than being padded for previous cards.
The current value is appended at index zero, and the trailing padding loop adds only one -1.
For two cards where only the second has liquid=true, the published x:liquid column is
[1, -1], instead of [-1, 1]. The first trade becomes liquid and the actual liquid trade loses
its flag. Short categorical strings behave the same way. With a later first occurrence, the
column can remain too short and disappear entirely at universe().

**Reproduction:** Derive.add on two valid fixture cards with extras {} and
{"liquid": true, "label": "present"} publishes x:liquid=[1,-1] and x:label=[0,-1].
This can make universe filters select different trades from the per-instrument cards.
No corruption of run one's dense liquid column is claimed.

**Fix:** initialize a new column with self.n missing entries before appending the current
card's value. Test first appearance on the second and later cards, including across files.

### F5 -- MEDIUM: clock sentences assert false price relationships and use future daily closes

**Evidence:** analysis/domino/viewer/story.js:87-104.

The generic daily clock sentence still selects "above"/"below" from the trade direction.
That happened to fit the headline daily clock; it does not describe the observed candle for
under-water and own-clock exits.

On 0G-2025-10-01-D-reversal-up, selecting C_u produces:
"that day closed green at 2.75690000, below its open 2.51470000".
The close is above that open. The full saved-run scan found this own-open direction error on
10,814 C_u entries and 9,710 C_own entries, with corresponding affected A/D variants. This is
new generic-clock narration, not a repeat of the repaired D5/headline-clock finding.

The hourly branch reads day[4], the completed daily close, when saying which side the day
was on at the hourly exit. For 0G-2026-03-19-D-continuation-down, C_h exits at
2026-03-20 00:00 UTC. The hour closes 0.54244 against the day's open 0.5405, so the day is
green at that exit. The final daily close is 0.53488, and the page says "with the day red too".
There are 22,403 C_h exits where the final-day side differs from the side at the exit-hour
close; A_h and D_h clock-exit paragraphs can inherit the same error.

**Fix:** derive each stated price relationship from the actual compared values, including
equality. At an hourly exit compare the exit-hour close with that day's open; if describing
the eventual daily close instead, label it as later information. Remove the unconditional
Monday "two tests are one" assertion for books whose rule is different. These are viewer
prose defects; this review does not claim the engine used lookahead.

### F6 -- MEDIUM: "at target" now uses a different denominator than its on-page explanation

**Evidence:** analysis/domino/viewer/stats.js:43-44, 53;
analysis/domino/viewer/app.js:632, 669-670;
analysis/domino/viewer/NOTES.md:152-154.

The intentional False-to-null conversion for books without a target now excludes those
filled trades from withTarget. The metric is a target-eligible-trade share. The page still
calls it "the share of filled trades that left at the book's target."

Actual universe results from fromUniverse -> bookStats:

| Book | Filled trades | Non-null hit values | Target fills | Displayed share | Share of all filled trades |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 178,203 | 152,255 | 75,927 | 49.87% | 42.61% |
| B | 178,203 | 97,063 | 18,519 | 19.08% | 10.39% |

The explanation in NOTES and HANDOFF does not repair the meaning presented to someone using
Compare. In particular, the B card displays about 19% while the stated denominator gives 10%.

**Fix:** either explicitly label the conditional share and show its eligible denominator,
or calculate the all-filled-trades share that the current explanation describes. Preserve
the agreed null convention on the cards.

### F7 -- MEDIUM: run switching does not reload universe scope and accepts stale run responses

**Evidence:** analysis/domino/viewer/app.js:480-488, 637-643, 799-817, 852, 859-860.

loadRun clears state.uni but retains cmpScope="universe" and calScope="all". The run-picker
handler then opens one instrument without calling loadUniverse. Compare displays that
instrument's results while saying "loading the universe table...", indefinitely; the
all-instrument calendar is empty. Only toggling a scope control triggers the missing load.

An already pending loadUniverse is also not tied to the run that started it. If run A's
response arrives after switching to B, it assigns A's decoded rows to state.uni under B's
run label and book registry.

**Reproduction:** a Node harness executed the actual loadRun/loadUniverse/openCoin functions
with rendering stubbed and fetch responses controlled. Switching with both universe scopes
selected fetched only B/run.json, B/index.json, and B/X.json; uni stayed null and calMap was
empty. Resolving an older universe request after loadRun("B") left runId="B" with an
"A-only" instrument and its return in state.uni. The same harness confirmed both Compare
roots are disposed, an undeclared selected book resets to C, and units rebuild.

**Fix:** reload the current run's universe whenever a retained scope needs it. Capture a run
generation/id for every asynchronous load and ignore stale responses, or abort those requests.
Exercise both normal and deliberately reordered responses.

### F8 -- LOW: the documented check-run coverage is broader than the actual comparison

**Evidence:** analysis/domino/viewer/CONTRACT.md:217-219;
analysis/domino/run_export.py:689-692, 710-715, 741-758, 794-804, 811-812.

The contract and check_run docstring promise each ladder book's return/reason/day. The function
does not compare A/B/D reasons or settlement times. Its hourly check compares C_h's reason and
return, not entry/exit timestamps. In addition, it only iterates instruments in the imported
index, so omitting an entire instrument does not identify that instrument's missing cards.

**Reproduction:** in memory, changing a real card's A reason and day and moving C_h's entry
and exit by one hour still prints "1 cards compared; no differences". An empty imported
iterator prints "0 cards compared; no differences".

**Fix:** enumerate the exact covered fields wherever claiming equality, and identify these
additional limits alongside the already disclosed grouped-variant omissions. If this command
is the regression gate, compare instrument sets and expected counts as well as the missing
fields. The current saved run did compare all 179,498 cards; this finding does not invalidate
that observed count or the independent checks below.

### Verification and bounded conclusions

Commands used the existing environment directly, without syncing dependencies or regenerating
the ignored data:

- `.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider`,
  with PYTHONDONTWRITEBYTECODE=1: **471 passed, 2 skipped in 8.48s**.
- `.venv\Scripts\ruff.exe check --no-cache analysis/domino tests`:
  **All checks passed**.
- `.venv\Scripts\python.exe -B -m analysis.domino.trade_viewer check-run management-book-20261010`:
  **179,498 cards compared, no differences**, subject to F8.
- `.venv\Scripts\python.exe -B scripts/secret_scan.py --range 2f3a3a8`:
  **18 changed files scanned, no secrets found**. This includes the two post-endpoint
  review-range edits. An initial invocation incorrectly supplied a full range to a tool that
  expects a base revision; that command failed and was corrected.
- `git diff --name-status 2f3a3a8..HEAD` and
  `git diff --stat 57c054c..HEAD` confirmed the work-order scope.
  Data and vendor are ignored. No new private access link was identified in the reviewed
  changes. No Pine or engine modification is in this range.

Additional read-only probes:

1. **Saved mapping, beyond check_run.** Read the raw saved CSV using the typed row loader and
   independently built expected timestamps from each instrument's daily-bar index and CSV
   offsets. Across 179,498 cards: **4,314,995 field checks, zero differences, zero unmatched
   CSV rows within the indexed instruments**. These checks included every present book's
   return; C_u/C_own/C_long and their A variants' reasons and times; D_u fills; all three
   hourly entries, C_h/A_h/D_h times and fill reasons; the D_h day-resolution override;
   and measured-move A's reason/time. Present fill prices were also checked against their
   recorded returns to 1e-6 percentage points, with no mismatches. This supports mechanical
   export fidelity to the saved row, not a new engine replay or independent market-data proof.

2. **Validation and day offsets on run one.** validate_file over all files returned zero
   problems and zero warnings. No card entry day or non-null book exit day was missing from
   its daily bars. Thus prep's calendar fallback is not exercised by run one's settlements.
   Its behavior on external runs with missing exit days is not proven safe: downstream
   tradeSpan and clock/day words still interpret k as a bar offset and clamp to available
   bars (core.js:189-193; story.js:73-77, 100). Do not generalize the run-one result.

3. **The requested false-hit/touch question.** No non-hourly clock/cap entry had hit=false with
   its declared target's recorded touch at or before its exit. The hourly books do: **3,913
   A_h and 4,644 D_h entries**. These compare day-resolution first-touch timestamps with an
   hourly exit, so they are not proof that a target filled before the exit. A later touch on
   that same day is represented by the day's open. The story's "was not touched before the
   exit" can therefore be correct for those rows; do not change the engine or hit flag merely
   from this coarse timestamp comparison.

4. **TVB-41 F1 repaired.** There remain 24 D5 clock exits past an open headline cap.
   Full narrate() for BLUR-2026-07-24-W-inside-down correctly says day 24 / Aug 17, +13.10%,
   and separately identifies C's day-20 cap. The weekly/monthly/daily regression tests pass.
   The new F5 concerns other clocks and a different source of false prose.

5. **TVB-41 F2 repaired in substance.** Read committed manage.json at 3fa6990 and 74dcb28.
   Reversal hourly C-minus-C's interval spans zero in both; inside D-minus-D moves from
   -0.001989 to +0.008228 with both intervals spanning zero. Scored hourly counts move from
   55,112 to 54,851, with three old no_entry_hour exclusions versus 264 new partial-entry
   exclusions. The receipt/ledger corrections communicate those changes. No old CSV or
   engine rerun was performed.

6. **Marker logic.** Executed the current drawPane marker-construction code under Node with
   chart API calls stubbed, using real saved cards/bars: ACE 2026-04-29's C_h entry/exit
   arrows land at 02:00/03:00; ATOM 2026-05-09's D one-R circle and exit share May 11;
   BTC 2026-03-16 W ref's stop circle and exit share March 27, with the long close arrow
   pointing down; BLUR D5's short close arrow points up on Aug 17. settle keeps cap prices
   and takes entry-level resolution first. This is marker-data evidence, not a rendered
   browser or collision-layout check. Day-resolution touch circles can describe later hours
   of the same day than an hourly selected book's exit; the ACE stop circle appears at 18:00
   after its 03:00 exit. That marker distinction should be explicit when inspecting an
   hourly book.

7. **Validator/import boundaries.** The existing per-how price/time/return and entry<=at
   refusals pass. The target rule is currently existential: any target touched by the fill
   time satisfies it, even if the book declares another target; no stronger own-target
   consistency guarantee was verified. The 200-problem break is checked after a whole
   instrument file, so it is not a hard 200-message bound. Folder-form in-place import and
   the tested normal folder zip pass; F1-F3 describe the uncovered paths.

**Limits:** no fresh export/build, live venue pull, browser/device rendering pass, drawing
persistence test, or stage-3 phone-run end-to-end test. Optional-bar story rendering and
non-UTC roll calendars were not certified. No implementation change is proposed for the
pending inside-break T1 ruling. No finding here ranks strategies or promotes an arm.

## 3. Actionable items (reviewer's own list)

1. **F1 -- HIGH** -- contract.py:60, 507, 608; trade_viewer.py:417:
   validate ids and filenames and enforce resolved destination containment before mutations.
2. **F2 -- HIGH** -- contract.py:609-637:
   stage and validate replacements; recognize run.json-form in-place sources; preserve old data on failure.
3. **F3 -- MEDIUM** -- contract.py:560:
   split inline run.json inside zip/folder input through the same JSON loader.
4. **F4 -- MEDIUM** -- contract.py:439-472:
   backfill new extras columns before inserting the current card's value.
5. **F5 -- MEDIUM** -- story.js:95-104:
   narrate observed comparisons and day continuity at the exit hour, without borrowing a daily-clock rule.
6. **F6 -- MEDIUM** -- stats.js:43-53; app.js:669-670:
   make the target-share calculation and visible denominator description agree.
7. **F7 -- MEDIUM** -- app.js:480-488, 799-817, 852:
   reload retained universe scopes and reject responses from older run selections.
8. **F8 -- LOW** -- CONTRACT.md:217-219; run_export.py:689-812:
   state exact comparison coverage and guard missing instruments/empty comparisons.

Paths in this list are under analysis/domino/ (JavaScript and CONTRACT.md under viewer/).

## Suggested prompt

Repair F1-F7 without changing engine results. Add tests that exercise invalid replacement of
an existing run, source run.json inside the destination, dot-segment ids and Windows instrument
paths, zipped inline runs, sparse extras across cards/files, the named 0G clock sentences,
Compare's actual denominator, and reordered run-switch requests. Clarify F8's coverage.
Then repeat the existing suite, saved-row comparisons, and a browser run-switch check.
Keep stage 3 and the pending strategy rulings outside this repair.

