# HANDOFF -- tradingview-backtesting

> Newest session entry at the TOP. Keep under 1500 lines; archive older entries to
> `docs/session_archive/` when it grows past that.

---

## Session TVB-44: the TVB-43 audit folded in code, the entry-fill pair owner-ruled and run as a prereg amendment, the receipt and ledger re-read both ways, the card's gap label, housekeeping (COMPLETE)

**Date:** 2026-11-02
**Status:** COMPLETE. Commits on `main`, pushed: `099025c` (the whole session's work: the audit
fold, the entry-fill pair, the receipt and ledger, the viewer, the tests) and the docs-only
close-out pin after it. Suite 517 passed, 2 skipped; ruff clean; `node --check` clean; the crypto gate (`manage.py --as-of
2026-10-10`, then `git diff` on `results/manage.json` and `manage_tables.md`) EMPTY after the
rerun through the touched `manage.py`. The owner's direction at the start: run `/session-start`;
the brief's three forks were answered in one message: audit F1's declared comparison = "Both, as
a pair"; next after the fold = the owner's reading of the bench receipt; housekeeping = delete
`proto_codex/` and the old flat viewer files. Everything below was done the same session, on
the standing direction (fold audits in code, in-session Codex pass before the commit, few
check-ins). OpenMemory was unavailable (429) for the whole session; the memory index carried.

### TVB-43 audit: critical synthesis (F1-F5 and the smaller items), all ACCEPTED and repaired

Every finding was re-read against the cited lines and the saved rows before acting; all held.
None was disputed.

- **F1 HIGH, gap-through entries credited at a trigger the session never offered:** CONFIRMED
  by an independent count on the saved rows and the tape (Globex 204 of 3,824 session units
  open past the trigger, 39 never print it; regular hours 1,610 of 3,797, 581 never print it;
  the 2011-01-12 example holds: session low 1,276.00, trigger 1,273.75). The mechanism: the
  hourly walker's entry is `high > level` on the first hour and every book measures from
  `level`; a 24/7 tape always trades through the trigger, a session tape excises the overnight.
  The repair is NOT an engine change. The owner ruled the declared comparison as a pair
  (`docs/experiments/tvb43_bench_prereg.md` section 9, written BEFORE the code): F1 open-fill
  (the fill at the session's open where it opened past the trigger; every price and exit path
  the control's; a target the open had passed is reached at the entry, zero; the under-water
  books excluded because their exit reads the entry price) and F2 missed-entry (the unit not
  taken; the control on the units that did not gap). Built in the runner (`run_bench.gap_flags`,
  `open_fill`, `fill_blocks`, `table_fill`, `_at_entry`): the exit price is recovered exactly
  from the control's return and re-measured from the open; non-gap units keep the control's
  bytes; the control rows in the regenerated tables are byte-identical (git diff shows only the
  header line, the footer, the relabeled roll rows and the new blocks). Labels at three levels:
  the run card's entry rule and notes (counts), `extras.gap` (open / untraded / null) and
  `extras.session_open` on every card, and the card's plain-words story ("The session opened
  at 1,278.50, above the trigger, so a fill at the trigger was not on offer at the open ...";
  `story.gapWords`, `core.prep` reads the two keys; run one's cards carry neither). The
  reviewer's exits-fixed sensitivity reproduced (RTH exit only +0.08 to -0.08; the hourly clock
  +0.16 to -0.00). Readings in the next block.
- **F2 MEDIUM, the bench exporter truncated the live run before the staged importer:** CONFIRMED
  in code (`export_run` opened `data/runs/<id>/run.json` for writing). Now the source is a
  `tempfile.mkdtemp(prefix=".export-", dir=data)` folder handed to `import_run` and removed in
  `finally`; `export_run` takes `data=` for tests. Test: a `json.dump` failure on the instrument
  file during a rerun leaves the registered run's files and `runs.json` byte-identical and no
  `.export-*` / `.import-*` debris; a clean rerun replaces through the staged swap with one
  listing entry.
- **F3 MEDIUM, a run switch stranded a pending comparison in "loading run B...":** CONFIRMED in
  code (`loadOther` dropped the stale response by generation and nothing cleared `loading`).
  `loadRun` now, after `fillRunCompare` (which drops a comparison that became the current run),
  restarts `loadOther` for a comparison that has no table yet (loading or failed) under the new
  generation. Source-level test (DOM-bound). In Chrome: Compare against run one restored from
  the address, then the RUN select switched to the Globex run: the by-role table re-rendered
  for the new run (4,823 rows against 179,498), no console errors. The pending-race shape itself
  was the reviewer's Node reproduction; it was not timed by hand in the browser.
- **F4 MEDIUM, the roll split is the headline window and "adds about a point" was causal:**
  AGREED. The 235 Globex and 202 regular-hours null-flag rows whose reference window crosses a
  roll reproduced exactly (D 36 / 23, W 107 / 89, M 92 / 90). `roll_flags` now also writes
  `roll_ref` (the chance book's own window, `days_ref`); the splits read "no roll through C's
  window (headline)", "roll inside C's window" and add a diagnostic row (no roll through C's nor
  the chance book's window: 3,574 / 3,547 session units; the chance book moves a hundredth or
  two). The receipt and the ledger withdraw the "adds about a point" reading (the cohort is
  selected by how long C stays open) and name a back-adjusted rerun as the declared way to
  size the roll. `extras.roll_ref` on every card.
- **F5 LOW, unicode casefold merged two ids into one listing:** CONFIRMED (`_slug` accepted any
  unicode alphanumeric; `register` casefolds; KELVIN SIGN folds to k). Ids and instrument file
  stems are ASCII only (`_plain_char`; `_fname` maps a unicode letter to an underscore, and the
  casefold collision check then refuses K beside KELVIN SIGN). Test with U+212A and a combining
  mark.
- **Smaller, all CONFIRMED and fixed:** the receipt's RTH hours 26,900 -> 26,570 (120 early
  closes); "twelve of fifteen years" -> thirteen positive (2012 within a hundredth of zero) and
  two negative; the crypto footer under the ES candidates table -> `manage.table_candidates(cands,
  footer=...)` with the default text byte-identical (the gate proves it) and a bench footer
  (no 208-day window, no dex taker fee, gross of every cost); `bench_*.json` strict (`_finite`
  maps NaN / inf to null, `allow_nan=False`; 12 literal NaN before, 0 after); "the intervals are
  honest" -> descriptive, overlapping trades are not independent observations.
- **Held by the audit and not re-done:** the crypto gate hashes, the ES rows reproduced to
  1e-12, the calendar and tape checks, the export-time mapping (21,838 checks), the earlier
  importer and viewer repairs on the named cards. The reviewer's browser host was unavailable;
  this session's Chrome pass covered the ES card, the Compare restore and the run switch.

### The entry-fill pair: what the bench reads now (both ways; `analysis/bench/BENCH_RECEIPT.md` section 1b, the ledger card)

- **The regular-hours day's positive sign was the fill, not the trade.** At the trigger the
  exit-only book reads +0.08 [+0.03, +0.14] per trade; from the open -0.08 [-0.13, -0.03]; on
  the 2,187 units that did not gap -0.08 [-0.15, -0.01]. The hourly clock's +0.16, the one clock
  with every setup clear of zero, is -0.00 from the open and +0.02 on the no-gap units. Both
  read as the Globex day does (-0.05 at the trigger, -0.07 from the open, 204 gap units): the two
  days do not read a different sign once the fill is one the session offered.
- **The gap units themselves, both ways:** where the trigger never printed, the strongest line
  under BOTH fills (RTH +1.06 at the trigger, +0.42 [+0.27, +0.58] from the open; Globex +1.28
  and +0.85): a gap that holds all session carries on. Where the gap filled back through the
  trigger inside the session, the losing line from the open (RTH 1,029 units -0.36; Globex 165
  -0.52). A declared-arm path and a kill test, named, not picked; "holds all session" is known
  at the close.
- **Longs and shorts from the open (RTH):** longs +0.06 (from +0.21), shorts -0.25 (from -0.09):
  the gap is directional on a rising index. **Targets the open had passed:** RTH 343 of 1,610 A
  fills, 162 one-R fills, 150 chance-book one-R fills (wins at the trigger, zero from the open).
  **Paired difference on gap units:** +0.38 [+0.36, +0.40] per RTH session unit, +0.24 Globex;
  +0.41 / +0.33 per weekly unit. Weekly RTH +0.01 -> -0.13; monthly +0.15 -> +0.04.
- **What survives the fill:** the setup-bar stop loses on session units (the swap keeps its
  direction by the row means), the monthly reversal of the swap, the hourly clock halving the
  losers (an exit reading), the T1 reach rates. **What does not:** the "different sign by day
  definition" reading, the regular-hours hourly clock clear of zero, and the roll's "survives
  the roll split" sign difference (it was the gap).

### Housekeeping (owner's word 2026-11-02)

`analysis/domino/viewer/proto_codex/` deleted (19 MB, untracked); the 295 old flat files under
`viewer/data/*.json` deleted (302 MB, gitignored; `data/runs/` and `data/runs.json` stay); the
`.gitignore` line for `proto_codex/vendor/` dropped. `User_Notes.md` stays untracked.

### In-session Codex pass on the diff (before the commit): 5 items, all folded

Run through the `codex:codex-rescue` agent as a read-only background job (7 min; the agent
itself is a forwarder, the report came back through the runtime's `status` / `result`).

- **REPAIRED, verified by the reviewer:** F1's arithmetic on mirrored never-printed probes
  (long 102/105 from a 100 trigger = +2.941%, short 98/95 = +3.061%), targets behind the open
  zero, the chance book's hit on `out5`, all nine fill columns and both fill tables reproduced;
  every gap row's hourly entry is hour zero whose open is the session open; the control rows
  and the legacy summary values unchanged; F2 under an injected write failure AND an actual
  Windows open handle on the destination `run.json` (PermissionError, old run and listing
  byte-identical, no debris); F4 `roll` identical on all 9,611 saved rows, `roll_ref`
  recomputed; F5 K accepted, U+212A refused, `run_export.export_run` refuses the id before
  writing; the default crypto footer identical and both crypto artifact diffs empty; strict
  JSON; 516 passed at that point, ruff and `node --check` clean.
- **DISPUTED (incomplete repairs), all folded the same hour:**
  1. **F3, a FAILED run switch still stranded the comparison** (the catch restored the old run
     and nobody restarted the pending load). Now `resumeOther(gen)` runs on the failure path
     and on the success path alike.
  2. **F3, an older request for the same run could win** (a restart beside the select's own
     request shared one generation; a late rejection turned a success into an error). Every
     `loadOther` request carries its own number (`state.otherReq`); a request writes only when
     generation, id AND number are still its own.
  3. **F3, the restart's await let a later switch's metadata be overwritten.** The restart now
     comes after the page's metadata and `localStorage` writes (no await between the generation
     check and those writes) and re-checks the generation before the universe load.
  4. **F5, the crypto exporter folded two instrument names onto one file** (`ABC` + KELVIN SIGN
     and `ABC` + e-acute both become `ABC_.json`; the second was written over the first).
     `run_export.file_names` refuses any pair that shares a file, compared without case (the
     inline importer's rule), before anything is written.
  5. **F1 reporting, longs and shorts were shown for the open-fill only** though section 9 asks
     for them under both variants. The fill blocks carry "longs / shorts, missed-entry" rows;
     both variants regenerated (control rows still byte-identical); the receipt's 1b bullet
     has the numbers (RTH missed-entry longs +0.04, shorts -0.22; Globex +0.15, -0.31).
- **UNVERIFIED by the reviewer:** F3 at runtime (source-level only; this session's Chrome pass
  covered the loaded-comparison switch, not the pending race); the full regeneration (done
  here: both variants rerun, the crypto gate empty); the receipt and ledger prose.
- Source-level tests updated for 1-3 (`test_run_switch_restarts_a_pending_comparison_under_the_new_generation`)
  and 4 (`test_run_ids_and_file_names_are_ascii_so_the_listing_and_the_folder_fold_alike`).

### Files created/modified (TVB-44)

- `analysis/bench/run_bench.py` (gap flag, open-fill, fill blocks and table, `roll_ref`, the
  relabeled splits, the staged export, strict JSON, the bench footer, the run card's entry rule
  and notes, the extras), `analysis/bench/BENCH_RECEIPT.md` (section 1b, every section
  re-read), `analysis/bench/results/bench_*.json`, `bench_*_tables.md` (regenerated; control
  rows byte-identical)
- `analysis/domino/contract.py` (`_plain_char`, ASCII `_slug` / `_fname`), `analysis/domino/manage.py`
  (`table_candidates(footer=)`), `analysis/domino/viewer/app.js` (the comparison restart),
  `core.js` (`gap`, `session_open`), `story.js` (`gapWords`)
- `tests/test_domino_bench_runner.py` (new, 6), `tests/test_domino_contract.py` (+1),
  `tests/test_domino_viewer_js.py` (+2)
- `docs/experiments/tvb43_bench_prereg.md` (section 9, the amendment), `docs/ARM_LEDGER.md`
  (the bench card: the amendment bullet, the numbers re-read), `docs/reviews/tvb43-codex-audit.md`
  (committed as RETURNED), `docs/reviews/REVIEW_REQUEST.md`, `.gitignore`,
  `.session_startup_prompt.md`, this file
- Deleted (untracked / ignored): `analysis/domino/viewer/proto_codex/`, `viewer/data/*.json`
  except `runs.json`

### Open

- [x] The TVB-43 audit folded in code the same session; the entry-fill pair owner-ruled,
      prereg'd, built, run, received and carded; the card's gap label; housekeeping.
- [ ] **The owner's reading of `BENCH_RECEIPT.md`**, now with section 1b: which lines become
      declared arms (the never-printed gap units? the hourly exit?) and which kill tests (the
      gap-that-fills units; the regular-hours sign; the monthly stop swap). Candidate declared
      variants if asked (prereg amendment first, one change each): a back-adjusted series (the
      declared way to size the roll); NQ / RTY / the micros from the same cache; a retest fill
      or a next-session entry for the gap units; the session-time against traded-time hold.
- [ ] The with-trend inside break's T1 STOP-and-ASK (open since TVB-39; the owner rules; A3
      before code); the exit and hierarchy rulings (carried).
- [ ] Viewer: the open-fill and missed-entry books as a GROUP on the page (today the pair lives
      in the receipt and the tables; a card shows the gap sentence and the extras); the other
      run's curve on its own axis in Compare across runs; drawing persistence across coin
      switches proven in a live browser; the journal layer; the hourly archive.
- [ ] Carried: the phone review page's four Codex findings; the paper rule set for the other
      workspace; the monthly broadening-formation target; the Friday-close oracle / SOXL
      research; fresh wallet and executor restart checklist; scanner STRAT rulings.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range below) and write
> a verbatim assessment to docs/reviews/tvb44-codex-audit.md. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
> The next session folds it IN CODE the same session (owner's direction 2026-11-01).

- Review status: REQUESTED
- Commits to review: `5ee9b84..099025c` on `main` (5ee9b84 is the TVB-43 close-out pin; 099025c
  the session's one working commit; the pin commit after it is docs only), as pinned in
  `docs/reviews/REVIEW_REQUEST.md`.
- Scope / what changed: see "Files created/modified" above.
- Focus areas: **the entry-fill pair** (`run_bench.gap_flags` strictness and direction;
  `open_fill`'s exit recovery and the targets-behind-the-open rule, shorts mirrored; the hourly
  books' entry hour on a gap unit; `_at_entry` against `open_fill`; the control rows
  byte-identical in the regenerated tables; the receipt's section 1b against the tables and the
  JSON, both directions, nothing promoted); **the staged export** (`.export-*` under `data`, the
  importer's `recover` untouched by it; an open handle on the destination during a rerun);
  **the comparison restart** (`loadRun` after `fillRunCompare`; the old response can never win;
  `cmpRun` restore in `init`); **the roll diagnostic** (`roll_ref` for the entry case; `roll`
  unchanged for every row); **ASCII ids** (`_plain_char` everywhere an id or stem is accepted);
  **the card's gap sentence** (`gapWords` reads `w.above` for the trade's side; run one's cards
  unchanged); hygiene (ruff, 517 passed, 2 skipped; no secrets; data and vendor gitignored).
- Reviewed by: pending
- Findings: {blank until docs/reviews/tvb44-codex-audit.md exists}

---

## Session TVB-43: the TVB-42 audit folded in code with an in-session Codex pass, the contract's stage 3 built and verified in Chrome, the session calendar built into the engine with the crypto book byte-identical, the ES bench run as runs two and three with its receipt (COMPLETE)

**Date:** 2026-11-01
**Status:** COMPLETE. Commits on `main`, pushed: `70bacdf` (the audit fold), `7111720` (stage 3),
`4140285` (the bench prereg draft), `b05c7da` (the page's session-calendar support, the first
close-out), `95f6a50` (pin), then the bench commit (the engine's session calendar, the ES tape,
the runner, runs two and three, the receipt, this entry's update). Suite 508 passed, 2 skipped.
Run one re-imported in place through the new importer (twice, 69 s each, no leftovers). The
owner's direction at the start of the session: "proceed with our priorities as listed"; move back
to the autonomous side; the stop-early, request-Codex, sessions-of-small-fixes loop is the thing
to avoid; a one-screen priorities list; few check-ins. Recorded as a standing memory and applied:
the audit was folded IN CODE the same session and the adversarial pass ran IN-SESSION on the diff
before the commit. Mid-session the owner ruled on the bench prereg in one message ("The three
items you flagged are approved on my end"; the HANDOFF archive approved too) and the bench went
from draft to two imported runs and a receipt the same day. HANDOFF archived to 1,265 lines
(`docs/session_archive/HANDOFF_TVB36-TVB38.md`).

### TVB-42 audit: critical synthesis (F1-F8), all ACCEPTED and repaired

Every finding was re-read against the cited lines before acting; all eight held.

- **F1 HIGH, ids and file names could escape the runs folder:** `_slug` now requires an id to
  start AND end with a letter or digit and not be a Windows device name (`.`, `..`, `x.`,
  `CON` refused); `_fname` turns every character outside letters, digits, dot, dash, underscore
  into an underscore, strips leading and trailing dots, prefixes device names and suffixes
  reserved files (`RUN` -> `RUN_instrument.json`); `_plain_name` and `_inside` guard every write;
  `export-run` checks its id before any folder is made. Run one's 292 file names are unchanged.
- **F2 HIGH, a refused replacement destroyed the old run:** `import_run` builds the run in a
  staging folder beside the runs and swaps it in only after every card passes; a refused
  replacement leaves the old run and `runs.json` exactly as they were (test: byte-identical
  files, unchanged listing); the in-place import now recognises `<dest>/run.json` as its own
  source.
- **F3 MEDIUM, a zipped inline run imported zero cards:** the folder branch recognises an inline
  `run.json` and splits it like a direct file (the zip branch goes through it); a folder that
  mixes the two flavours is refused; direct file, zipped file and folder give one card count.
- **F4 MEDIUM, a sparse extras column shifted onto earlier cards:** a key first seen on card n
  starts its column with n absent marks; tested across cards and files.
- **F5 MEDIUM, clock sentences asserted false relationships:** "above / below / level with"
  and "red / green / flat" are read off the two prices compared, never the trade's direction;
  the hourly branch states the day's side AT THE EXIT HOUR (the hour's close against the day's
  open) and never the day's final close; the Monday sentence is a bar fact ("the week's first
  session: the day's open is also the week's open"), not a rule claim.
- **F6 MEDIUM, "at target" divided by a different count than its note described:** the KPI
  shows "51% of 135k with one"; the note names the denominator (filled trades that HAD a target,
  one R for the one-R books); `bookStats` returns `withTarget`, `targets`, `targetAll`.
- **F7 MEDIUM, a run switch kept the universe scope stale and accepted stale responses:**
  `loadRun` bumps a generation and reloads the universe for a retained scope; every async load
  compares the generation before writing state; one universe fetch in flight at a time.
- **F8 LOW, `check-run` claimed more than it compared:** its exact coverage and its omissions
  are now stated in `CONTRACT.md` section 7; the command was retired with the flat layout in
  stage 3 (below). The audit's own 4,314,995-field probe is recorded as the broader receipt.
- **Held by the audit and not re-done:** the saved-row probe (zero differences, clock variants
  included); both TVB-41 repairs; probe 3 (3,913 A_h and 4,644 D_h rows with hit false and a
  day-resolution touch at or before an hourly exit are a coarse-timestamp comparison, no engine
  or flag change); probe 7 (the target-fill rule stays existential; the 200-problem stop is
  after the file that crosses it, now said in the docstring).

### The in-session Codex pass on the repairs (before the commit): 2 HIGH, 5 MEDIUM, all repaired

Run with the `codex:codex-rescue` agent on the uncommitted diff, read-only. Areas 3 (zip and
folder routing), 4 (extras backfill) and 5 (clock prose) came back CLEAN.

- **#1 HIGH, an interrupted swap plus the next import's sweep could destroy a run:** the stepped-
  aside copy (`.old-<id>-<stamp>`) is the only copy if the process dies between the two renames,
  and `_sweep` deleted it. Now `recover()` runs first and PUTS BACK a stepped-aside run whose name
  is empty (and removes one whose swap had completed); a failed second rename renames the old
  run straight back; the stamp carries no dash so an id with dashes splits off cleanly. Tests:
  the interrupted shape restored byte-identical; a simulated rename failure leaves files and
  listing untouched.
- **#2 HIGH, `Foo` / `foo` / `Foo.` are one folder on Windows while the listing compared ids
  exactly:** ids must end with a letter or digit; `register` folds case (one listing, the newer
  id's words win).
- **#3, #4 MEDIUM, case-sensitive collision checks and device names:** `_split_single` keys
  collisions by casefold (`BTC` and `btc` refused); reserved files compared without case
  (`INDEX.json`); `NUL` -> `_NUL.json`; `_plain_name` refuses both.
- **#5 MEDIUM, a load could capture the new generation with the OLD address:** `loadRun` nulls
  `runId` / `base` / `index` while the switch is in flight and every loader bails on a null base.
- **#6 MEDIUM, `applyDate` and `select` committed stale selections:** `applyDate` awaits every
  instrument file, re-checks the generation, then commits; `select` stops when `loadCoin`
  reports the run changed.
- **#7 MEDIUM, a failed universe load left "loading..." forever:** the failure is caught, said
  in the meta line and on the Compare scope note ("pick the scope again to retry"), never spun on.
- One more found in the browser pass, not by either review: **the page trusted a cached
  `runs.json`** (the server sends no cache headers) and showed one run after a second had been
  imported. Every JSON the page reads now goes through `getJson` with `cache: "no-cache"`
  (SimpleHTTPRequestHandler answers 304s).

### Stage 3 of the contract (on the owner's word, read from "proceed with our priorities as listed")

- `trade_viewer build`, `check-run`, the flat loader and the flat universe table are DELETED;
  `serve` wants `data/runs.json`. The old flat files under `viewer/data/*.json` (302 MB,
  gitignored) are unread and can be deleted by the owner.
- **Compare across runs, by role.** An "Against run" list on the Compare tab; the chosen run's
  card and universe table load and a by-role table lines its ladder books up with this run's:
  headline against headline, the target books in order, stop books, the chance book against
  the chance book (`stats.roleRows` pairs the k-th book of each role; a gap where a run has
  none); both sides over their whole universe table with the page's filters (the unit filter
  only where the other run shares a unit name); the other run's headline is a dashed curve on
  the equity chart; `cmpRun=` in the address. Rough edge kept: the dashed curve shares the y
  axis, so a tiny run's curves flatten beside run one's hundreds of thousands.
- **The example single-file run** (`analysis/domino/viewer/examples/single_file_run.json`,
  rebuilt by `make_example.py`): one `run.json` with BTC inline, the venue's REAL last 100 daily
  bars from run one's file and six of the engine's own daily cards trimmed to three books. It
  is the shape a phone backtest writes and not a result. Imported beside run one and verified in
  Chrome: the picker lists both runs; the switch loads 6 cards and 100 bars, the book select and
  the unit filter follow the run card (D only), the ladder and story read the cards; Compare
  against run one shows the by-role table (6 rows against 153,516 daily rows of run one under
  the page's Daily filter) and the dashed headline; no console errors.
- `NOTES.md` ("stage 3"), `CONTRACT.md` (header, sections 7, 10, 12), `MANAGE_RECEIPT.md` (the
  command block) updated; `tests/test_domino_viewer.py` points at the exporter's typed cell
  (`run_export._val`) now that the flat loader is gone.

### The page made ready for session-day runs (the bench prereg's build order, item 1; page work, Plan Mode OFF)

- Two optional run-card fields, validated: `clock.label_shift_hours` (the hours added to a
  bar's open before its calendar date names the session; 6 for the Globex day, whose Sunday
  22:00 or 23:00 UTC open is Monday's session) and `clock.calendar` (`utc_day`, the default, or
  `session`: sparse, no weekend, holidays).
- `core.js`: `cal.sessionOf(ts)` (a time belongs to the session whose open is the latest at or
  before it, so an hour of a Globex session that crosses midnight UTC stays with its session;
  binary search over the daily opens); the day index keyed by LABEL date; week and month
  buckets by label date; a session calendar is complete once a later bucket has begun; shipped
  `1w` / `1M` bars replace the aggregate's prices for the matching week or month; `prep` labels
  the entry by its session and counts offsets in BARS; `weekOpenAt` by session. The story and
  the strip read labels through `cal.dateOf`; the hourly pane maps hours by session.
- `contract.py` `Derive`: the dates file and the universe's `date` carry the label; the
  universe's `:days` columns are BAR offsets (sessions), as the page's k, no longer calendar
  days (run one re-imported so its table matches; a coin with a gap in its daily bars now
  counts bars across the gap).
- Tests under node on a Globex-shaped tape (Sunday to Thursday 22:00 UTC opens, a Monday 20:00
  UTC hour, a shipped weekly bar) and on the unchanged 24/7 shape; Python tests on the
  validator and on `Derive`'s label and offsets (a Friday-to-Monday hold is one bar).

### The bench: prereg confirmed, the engine's session calendar, the ES tape, runs two and three, the receipt

**The prereg** (`docs/experiments/tvb43_bench_prereg.md`) was drafted first, with the data facts:
`ES.n.0` in `vectorbt-workspace/data/databento_cache/` (Databento GLBX MDP3, 1-minute source
2011-01-02 to 2025-12-31, resampled to 5m to 1M); the cache's `1D` bar IS the Globex session
(22:00 UTC summer, 23:00 UTC winter; 3,859 bars; 139 shorter early-close sessions); `1W` opens
Sunday evening; roll sessions come from the 1-minute source's `instrument_id`, which switches 60
times at 00:00 UTC inside a session (the draft said `symbol`; that column never changes;
corrected at build time). The engine could not run a session tape: the census treated a day as
a calendar day, a week as complete only with seven days, "yesterday" as the previous calendar
day (`day_events` returned None on every Monday), and the hourly walker assumed 24 hours a day
with the cap at hour 23 and a one-hour step between sessions. **The owner confirmed the three
items in one message:** the arms (V0 the Globex day, V1 the RTH day as the declared pair, the
C0 / C1 / C2 continuity ladder as a split of recorded context), roll sessions flagged and split
never dropped, and the engine change under its byte-identical gate.

**The engine change** (`census.use_calendar("session")`, a module switch with a context
manager; the default path is byte-identical with the switch absent): `aggregate` marks a bucket
complete once the data runs past it or a later bucket has begun; `_context` takes the bucket's
first session as the week's first day; `day_events` takes the previous session as yesterday;
`manage._walk_hourly_session` walks a session's hours from its open to its last traded hour and
steps to the next session's first, the cap at the cap session's last hour; `t1_h` is session
time there. **The gate:** `manage.py --as-of 2026-10-10` rerun through the switched code,
`results/manage.json` and `manage_tables.md` byte-identical (`git diff` empty), before any ES
row existed. `run_export.Tape` gained `opens_by_date` and `hour_time(date, offset)` so a session
tape's cards carry the exchange's real times (a Friday hold that exits on Monday's first hour
lands on Monday's real open plus one hour, not Friday's open plus 53); run one's path unchanged.
Tests: `tests/test_domino_bench_calendar.py` (8: the switch, complete weeks, the holiday week's
first session, Monday's level is Friday's, the hourly clock across the overnight break and the
weekend, the cap and a missing hour, the book end to end on a session tape, the tape's clock).

**The tape and the runner** (`analysis/bench/es_tape.py`, `run_bench.py`): the engine sees
SESSION TIME (a session's daily bar at its trade date 00:00 UTC, its hours at offsets from its
open), the exporter puts real times back; V1 is built from the 1-minute source (09:30 to 16:00
ET, seven 60-minute bins, the last a half hour); the roll flag per unit (entry / window); traded
hours for the hourly clock beside the session-time count; run one's table functions on the
bench's frame plus the prereg's splits; the run in the contract with `clock.label_shift_hours`
6 (V0) / 0 (V1), `clock.calendar: session`, the exchange's `1w` / `1M` bars shipped (V0).
Both variants run in about fifteen seconds. The first export was refused by the validator
(A_h's target time landed in the maintenance hour: `t1_h` was a list offset across the
session's end), which is how the session-time `t1_h` rule above was found: the gate did its job.

**Runs two and three on the viewer:** `es-globex-2011-2025` (4,823 units: 3,824 session, 818
weekly, 181 monthly; hourly clock 4,789 exits, 13 censored, 18 partial) and `es-rth-2011-2025`
(4,788 units). Checked in Chrome: a Friday entry that leaves on Monday reads "day 1, the week's
first session"; the hourly clock's entry is the session's real 23:00 UTC open; the calendar
shows Monday-to-Friday sessions; Compare by role lines ES up against run one (ES exit only
-0.05% over 4,820 filled against run one's -0.09%; the chance book -0.05% against -0.45%).

**The receipt** (`analysis/bench/BENCH_RECEIPT.md`, glossary first, both directions, with the
tables in `analysis/bench/results/`). The readings, each in both directions: on the Globex day
every management book sits within a few hundredths of zero and the chance book is the one line
clearly below (-0.11 [-0.15, -0.06]); on the regular-hours day every book, the chance book
included, sits a few hundredths above zero with the intervals clear (exit only +0.08 [+0.03,
+0.14]): the same rules read a different sign when the day is cut differently. The stop swap
replicates in direction on the daily unit of both days (+0.11 [+0.08, +0.15] and +0.04 [+0.01,
+0.06]) at a fifth to a tenth of crypto's size, is flat on weekly units and reverses on monthly
units (-0.97 and -1.06, intervals clear): the one place the setup-bar stop book is the better
line. Longs carry both days, shorts lose on both (Globex shorts -0.32 [-0.41, -0.23]); the index
rose five-fold. A roll inside the window adds about a point to every book (a contract switch
scored as a move); without a roll the sign difference between the days survives. The continuity
ladder as a split: the complement (the week against or unknown) reads higher than the gated rung
for the exit-only book on both days (RTH +0.21 [+0.11, +0.31] against +0.04); a gate would have
removed the better-reading half. The hourly clock halves the losers on both days and is the one
clock with every setup's interval clear of zero on the regular-hours day. T1 is reached at run
one's rates. Nothing promoted; the ledger card carries the numbers.

Two page-side items found on the way and fixed: `serve` now sends `Cache-Control: no-cache`
on every file (Chrome served a day-old `app.js` and a stale run list from its heuristics, twice
in one session; a server started before the change needs a restart), and the page fetches every
JSON with `cache: "no-cache"`.

### Files created/modified (TVB-43)

- `analysis/domino/contract.py` (staging swap, `recover`, ids and names, inline routing, extras
  backfill, `label_shift_hours` / `calendar`, bar offsets), `analysis/domino/run_export.py`
  (`check_run` removed, id check), `analysis/domino/trade_viewer.py` (`build` / `check-run`
  removed, `serve` precondition, id check)
- `analysis/domino/viewer/app.js`, `core.js`, `story.js`, `stats.js`, `index.html`,
  `CONTRACT.md`, `NOTES.md`, `examples/make_example.py`, `examples/single_file_run.json` (new)
- `tests/test_domino_contract.py` (+15), `tests/test_domino_viewer_js.py` (+5),
  `tests/test_domino_viewer.py`; `analysis/domino/MANAGE_RECEIPT.md`; `docs/ARM_LEDGER.md`;
  `docs/experiments/tvb43_bench_prereg.md` (new); `docs/reviews/tvb42-codex-audit.md` (committed
  as RETURNED), `REVIEW_REQUEST.md`, `.session_startup_prompt.md`, this file
- The bench: `analysis/domino/census.py` (`use_calendar`, the three session rules),
  `analysis/domino/manage.py` (`_walk_hourly_session`, `t1_h`), `analysis/domino/run_export.py`
  (`Tape.opens_by_date`, `hour_time`), `analysis/domino/trade_viewer.py` (`Cache-Control`),
  `analysis/bench/__init__.py`, `es_tape.py`, `run_bench.py`, `BENCH_RECEIPT.md`,
  `results/bench_globex.json`, `bench_globex_tables.md`, `bench_rth.json`, `bench_rth_tables.md`
  (new; the CSVs ignored), `tests/test_domino_bench_calendar.py` (new, 8), `.gitignore`,
  `docs/session_archive/HANDOFF_TVB36-TVB38.md` (new), `analysis/domino/viewer/NOTES.md`

### Open

- [x] The TVB-42 audit folded in code; the in-session Codex pass folded; stage 3 built and
      verified in Chrome; the page ready for session-day runs; the bench prereg drafted,
      confirmed by the owner, built and run: the engine's session calendar (gate passed), the ES
      tape, runs two and three on the viewer, the receipt, the ledger card's numbers; HANDOFF
      archived on the owner's word.
- [ ] **The owner's reading of `analysis/bench/BENCH_RECEIPT.md`**: which lines become declared
      arms and which kill tests (the monthly reversal of the stop swap; the continuity split's
      complement; the roll; the two days' opposite signs). Candidate declared variants, if the
      owner wants them: a back-adjusted series; the other index futures in the cache (NQ, RTY and
      the micros); the session-time against traded-time hold.
- [ ] The with-trend inside break's T1 STOP-and-ASK (open since TVB-39; the owner rules; A3
      before code); the exit and hierarchy rulings (carried).
- [ ] Viewer: the other run's curve on its own axis in Compare across runs; drawing persistence
      across coin switches proven in a live browser; the journal layer; the hourly archive.
- [ ] Housekeeping on the owner's word: `proto_codex/` deleted or kept; the old flat files under
      `viewer/data/` deleted; `User_Notes.md` stays untracked.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range below) and write
> a verbatim assessment to docs/reviews/tvb43-codex-audit.md. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
> The next session folds it IN CODE the same session (owner's direction 2026-11-01); it does not
> block the bench.

- Review status: RETURNED (audit written 2026-11-02; to be folded IN CODE in TVB-44)
- Commits to review: `8a5806c..HEAD` on `main` (8a5806c is the TVB-42 close-out; 70bacdf the
  audit fold; 7111720 stage 3; 4140285 the prereg draft; b05c7da the page's session-calendar
  support; 95f6a50 a pin; then the bench commit and its pin). The exact end is pinned in
  `docs/reviews/REVIEW_REQUEST.md`.
- Scope / what changed: see "Files created/modified" above (the viewer work and the bench).
- Focus areas: **the engine's session calendar** (`census.use_calendar`: does any default-path
  line differ from before; the three session rules against the prereg's section 2; the holiday
  week; the data-start partial bucket; `_walk_hourly_session` against the 24/7 walker's rules,
  the early-close session, the cap, a missing hour; `t1_h` in session time) and **the gate**
  (`git diff` empty on `results/manage.json` and `manage_tables.md` after the rerun: reproduce
  it); **the tape** (`es_tape`: the trade-date label, the hour offsets, the 1-minute RTH bins,
  the roll sessions from `instrument_id`, the short sessions); **the exporter's real times**
  (`Tape.hour_time` across a weekend and a DST change; `A_h`'s target time; the validator
  accepted both runs with gap warnings only); **the receipt against the tables** (every number
  in `BENCH_RECEIPT.md` and the ledger card is in `bench_*_tables.md` or `bench_*.json`; both
  directions stated; nothing promoted); the staged import's swap and `recover` on Windows;
  `_slug` / `_fname` / `_plain_name`; `cal.sessionOf` and the label shift against a 00:00 UTC
  run (nothing may move for run one: ATOM 2026-05-09, ACE 2026-04-29 hourly, BTC 2026-03-16 W,
  BLUR 2026-07-24 W) and against the ES runs (a Friday-to-Monday hold is one bar; an hour after
  midnight UTC stays with its session); `Derive`'s bar offsets; Compare across runs by role.
- Reviewed by: Codex, local CLI, 2026-11-02 (`docs/reviews/tvb43-codex-audit.md`)
- Findings: NEEDS-CHANGES. F1 HIGH gap-through entries on the ES tapes are credited at a trigger price the session never traded (RTH 1,610 of 3,797 daily units open beyond the trigger, 581 never trade it; counts reproduced in TVB-44); F2 MEDIUM the bench exporter truncates the live run before the staged importer; F3 MEDIUM a run switch strands a pending Compare load; F4 MEDIUM the roll split is the headline window only, the "adds a point" reading is not causal; F5 LOW unicode casefold merges two ids into one listing; smaller: RTH hours 26,900 should read 26,570, 13 positive years not twelve, the crypto table footer, NaN in bench_rth.json, interval wording. Default crypto path, ES arithmetic, calendar, export times and the earlier repairs all CLEAN. Synthesis in the TVB-44 entry.

---

## Session TVB-42: the TVB-41 audit folded, the cc menu's viewer entry repaired, the viewer row contract designed with the owner and built through stage 2 (the page reads runs) (COMPLETE)

**Date:** 2026-10-31 to 2026-11-01
**Status:** COMPLETE. The TVB-41 Codex audit (NEEDS-CHANGES, two MEDIUM) adjudicated and both
findings repaired. The cc menu's viewer entries, which had never worked (two control bytes in two
paths), repaired, extended with `cc viewer` / `cc viewer stop` and exercised end to end. The run and
trade-card contract (`analysis/domino/viewer/CONTRACT.md`) designed with the owner in trader terms
and confirmed before code; stage 1 (validator, importer, the management book as run one, checked
row for row) and stage 2 (the page reads runs: a run picker, the run's books with roles, cards as
the row, markers from timestamps) built, verified under node and in Chrome, committed and pushed.
Stage 3 waits for the owner's word. Mid-session the owner switched the account to purchased API
credits (the subscription's window ran out; the credits expire within a month) and later back;
nothing on the list needed Remote Control or the artifacts tools.

### TVB-41 audit: critical synthesis (F1-F2)

Read critically; both reproduced before acting (the BLUR probe and the manage.json diff at both commits).

- **F1 MEDIUM, book D5's "daily-close exit" sentence appended book C's clock: ACCEPTED, repaired.**
  `clockWords` read the headline fields (`status`, `exit_k`), so a weekly / monthly row whose headline
  is open at day 20 while D5 exits later (24 rows; BLUR 2026-07-24 W short, D5 out on day 24) said
  "the daily clock fired" and "marked at the day-20 close" in one breath. `clockWords` now takes the
  selected book's status and exit offset (defaults: the headline's); the D5 branch passes `status5` /
  `days_D5`, names its horizon (five days / weeks / months) and, when the headline is open or
  censored, says so in a separate sentence. The weekly-row test runs through `narrate()` on weekly
  and monthly rows (day 27 / day 45 named, the day-20 sentence absent) and on a daily row where both
  clocks are one exit. The BLUR paragraph now reads: day 24, Monday Aug 17, past the headline's cap
  where book C is marked open, +13.10%.
- **F2 MEDIUM, the rerun prose: ACCEPTED, corrected** in the receipt, the ledger and the TVB-41 entry
  (annotated, not rewritten). The reversal paired interval was through zero before and after
  ([-0.28, +0.01] then [-0.26, +0.03]): no transition. The inside D_h - D point estimate did cross
  zero (-0.002 to +0.008, interval through zero both times), so "no sign moved" was wrong by that one
  line. The 264 are partial-entry exclusions; 261 of them were formerly scored (55,112 to 54,851) and 3
  were already out as `no_entry_hour`. No research parameter or engine arithmetic touched.
- **Held by the audit, not re-done here:** every new hourly column reproduced from the cached candles
  (54,851 / 264 / 123,088; 1,473 changed rows; zero censored, zero open, 5,050 `cap_end` None rows all
  with an observed exit); zero non-hourly leaf changes in `manage.json` between 3fa6990 and 74dcb28;
  the 264 partial days all on the first calendar day of a coin's hourly cache; settlement over every
  book, the classed pairs (35,239, zero band mismatches), the markers (121,512 exits, the 1e-9 tolerance
  repaired 222 float touches with zero differences from exact decimals), drawdown, month denominator,
  the fee prose, the charter wording. Limits the audit states and this entry keeps: the old CSV was not
  regenerated (the committed-artifact route verified instead); no browser pass, no drawing-persistence
  check.

### Also this session

- **The cc menu's viewer entries (TVB-41) had never worked.** `menu.ps1` held a literal tab and a
  literal vertical-tab where the backslashes of `.claude-rc	rade-viewer.log` and `cc-toolsiewer.ps1`
  belonged (an escape-interpreting write; the TradeViewer task was never registered and nothing
  listened on 8765). Repaired with numeric byte writes (the first repair attempt through the tool layer
  reproduced the same corruption, which is the lesson: write Windows paths with byte values, never with
  backslash escapes through a tool that un-escapes). Added `cc viewer` / `cc viewer stop` as direct
  commands. Proven on this PC: parse clean, the task registers and runs, HTTP 200 on 127.0.0.1:8765
  (Domino Trade Viewer), the log writes, stop clears the port. The laptop side (the tunnel in the
  laptop's ssh config) is in the owner's hands; the exact lines are in this entry's close-out.

### The viewer row contract: designed with the owner, stage 1 built

The owner's three choices (AskUserQuestion, trader terms): one card per trade with the books as
a list on it; every "when" an exact timestamp with a declared resolution; each run names its own
books with a role (headline / target / stop / clock / reference). The owner's added ask: a run
made outside this workspace (a phone backtest) must be viewable by writing the same shape;
answered as JSON (a folder, one file or a zip) through `import` with a plain-words validator,
bars optional, CSV deferred (a card holds a list of books, which one CSV table cannot). Spec:
`analysis/domino/viewer/CONTRACT.md`, confirmed by the owner before code ("greenlighted for
go"), read as stage 1 only; stages 2 and 3 wait for the owner's word.

Stage 1, same day: `analysis/domino/contract.py` (validate, derive index / dates / universe,
import from folder / file / zip, `runs.json`), `analysis/domino/run_export.py` (the management
book's mapping, CONTRACT.md section 9, plus `check_run`), four CLI commands on `trade_viewer`
(`export-run`, `import`, `validate`, `check-run`), `tests/test_domino_contract.py` (31). The
management book is run one: 292 instruments, 179,498 cards, 17 books per card, 486 MB (the flat
layout is 302 MB), 56 s to export, about a minute to validate and derive. `check-run` against
the page's flat data: 179,498 cards, NO differences (level, the six ladder books' returns, the
headline's / D5's / chance book's reason and day, T1's price and touch day, one R's touch day,
the hourly clock); the derived universe table equals the old one on every return column and
the headline status, and differs on the hit columns only where a book has no target (25,948
rows without T1, 81,140 without T2, 335 with no reachable one R), the contract's "not
applicable" against the engine's "not hit".

Two things the gate and the build surfaced:

- **A real shape defect on the first export, caught by the validator:** 339 shorts (278
  monthly, 48 weekly, 13 daily) carry a one R at or below zero (the setup range exceeds the
  price; `2 x level - far side` for a short) and 964 rows a measured move at or below zero.
  None ever filled (the engine's `hit_D` is False on all 335 scored ones). The card carries no
  one-R / measured-move price there, the D books say "no one-R fill is possible", and the raw
  numbers stay in `extras` (`one_r_raw`, `mm_raw`). The engine's numbers are untouched; this is
  the card refusing to call a negative number a price. Named in CONTRACT.md section 9.
- **Two honest limits of the row:** `B_mm` is not exported (the row holds neither the second
  measured-move rung's price nor its touch day); `D_h`'s one-R fill carries the touch DAY with
  a note (the row has no touch hour for one R). Both on the run card's `notes`.

Stage-1 settlements written into CONTRACT.md section 12: the universe table carries the ladder
books only (grouped clock variants stay on the cards); flags and short strings in `extras`
become coded columns; `runs.json` newest first, same id replaces; an export in place is
allowed; a folder streams file by file.

The escape trap bit twice more while building (a `sys.exit` string's newline escapes became
real line breaks through the Bash heredoc): the rule from the cc-menu repair stands, no
backslash escapes through Bash, use the Edit / Write tools for source.

### Files created/modified (TVB-42)

- `analysis/domino/contract.py`, `analysis/domino/run_export.py` (new), `analysis/domino/trade_viewer.py`
  (four subcommands), `tests/test_domino_contract.py` (new, 31)
- `analysis/domino/viewer/CONTRACT.md` (new), `analysis/domino/viewer/NOTES.md` (stage-1 section),
  `analysis/domino/viewer/story.js`, `tests/test_domino_viewer_js.py` (audit F1)
- `analysis/domino/MANAGE_RECEIPT.md`, `docs/ARM_LEDGER.md` (audit F2), `docs/reviews/REVIEW_REQUEST.md`,
  `docs/reviews/tvb41-codex-audit.md` (committed as returned), `docs/HANDOFF.md`
- Outside the repo: `~/Documents/WindowsPowerShell/cc-tools/menu.ps1` (two bytes, `cc viewer`)

### Open

- [x] The viewer row contract, stage 1 (see the section above): spec confirmed by the owner,
      validator / importer / exporter / check built, the management book imported as run one
      with no differences against the page's data.
- [x] Stage 2, 2026-11-01 on the owner's word ("Stage 2 now: the page reads runs"): the run
      picker, `core.js` over the run's books (roles, groups, colours), `prep` deriving day
      offsets from the card's times against the run's bars, the story / ladder / markers /
      Compare reading the card's book entries, the node tests on the card shape (21), the
      audits' named rows re-checked under node and in Chrome (BLUR D5 day 24 past the cap, ACE
      hourly entry 02:00 / exit 03:00, ATOM one-R circle and out arrow on one bar, BTC weekly
      stop and out on one bar, Compare universe 179,498 rows with book C's drawdown -629,820,
      no console errors). Two contract additions (`target` on a book definition; `entry` and an
      entry-level `resolution` on a book entry), the second after the validator refused the
      re-export on 2Z 2026-08-12 (an hourly one-R fill known only to the day sat before the
      book's entry hour; the exporter now records the latest time known to be at or before the
      fill). Write-up: `analysis/domino/viewer/NOTES.md`, "stage 2". No engine column name
      survives in any page module (a test asserts it). Suite 471 passed, 2 skipped.
- [ ] Stage 3 (the flat layout and `build` retired; Compare across runs; the phone-made
      single-file run on the page end to end): on the owner's word.
- [ ] The one-instrument bench after the contract
- [ ] The with-trend inside break's T1 STOP-and-ASK; the viewer list; the hierarchy rulings; the
      carried items (see the TVB-41 entry)
- [ ] HANDOFF.md archive (over the limit; the owner's word); `proto_codex/` disposition

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb42-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED (docs/reviews/tvb42-codex-audit.md, 2026-11-01; critical synthesis in the TVB-43 entry)
- Commits to review: `2f3a3a8..57c054c` on `main` (2f3a3a8 is the TVB-41 close-out the
  session started from; 75626b7 the audit fold; bc79aa4 the contract spec; cba482e stage 1;
  ef5be09 stage 2; the close-out commit after it is docs only). Pinned after the push.
  Sanity-check: `git diff --name-status 2f3a3a8..HEAD`.
- Scope / what changed: `analysis/domino/contract.py` (new: validate, derive, import),
  `analysis/domino/run_export.py` (new: the management book's mapping, `check_run`),
  `analysis/domino/trade_viewer.py` (four subcommands), the four page modules rewritten to the
  card shape, `index.html` (run picker), `CONTRACT.md` and `NOTES.md`, the viewer and contract
  tests (21 + 32), the TVB-41 audit's two repairs (story.js, receipt, ledger), the cc-menu repair
  (outside the repo).
- Focus areas (scrutinize these): the mapping in `card_from_row` against the engine's columns
  (CONTRACT.md section 9), especially the clock variants (`C_u` / `C_own` / `C_long` and their
  A / D books), the measured-move book, `days_ref` for the chance book, and the hourly books'
  `entry` / `at` (the day-resolution one-R fill recorded at the latest time known to be at or
  before it); whether `check_run` compares enough (it covers the six ladder books, the headline's
  / D5's / chance book's reason and day, T1 and one R touch days, the hourly clock; it does NOT
  compare the clock variants' days or the A / D variants) and whether the universe table's hit
  convention (null = no target) is stated everywhere it matters; `prep`'s day offsets when the
  exit time's day is missing from the bars (the arithmetic fallback); `settle`'s `at` for a
  cap mark; the story's `pre` sentence for a target book whose touch time is before the exit
  yet `hit` is false (should not occur; say if it does); the validator's rules against the
  spec (section 3 and 5), the `entry <= at` rule, the single-file split, the zip path, the
  in-place import; the page's run switch (Compare charts disposed and rebuilt; `state.book`
  kept only when the new run declares it); the hourly pane's entry arrow (`hourEntry`) and the
  group squares; hygiene (no private link, data and vendor gitignored, ruff clean, 471 passed).
- Reviewed by: Codex (local tools, Python and Node probes), 2026-11-01
- Findings: NEEDS-CHANGES. Two HIGH: F1 run ids "." / ".." and backslash instrument names escape the runs folder before rmtree; F2 a refused replacement import destroys the old run, and a run.json-form in-place import deletes its own source. Five MEDIUM: F3 a zipped inline run imports zero cards; F4 a sparse extras column lands on earlier cards; F5 clock sentences pick above/below from the trade direction and read the final daily close at an hourly exit; F6 Compare "at target" divides by target-eligible trades while the note says all filled; F7 a run switch keeps the universe scope without reloading and accepts stale universe responses. One LOW: F8 check-run compares less than the contract states. Held: 4,314,995 saved-row field checks, zero differences; both TVB-41 repairs hold; 471 passed. Lead spot-checked F1-F6 against the cited lines at session start: all six confirmed by reading.

---

## Session TVB-41: the two audits synthesized and repaired (hourly clock, viewer), the neutral framing, the cc menu's viewer entry (COMPLETE)

**Date:** 2026-10-29 to 2026-10-30
**Status:** COMPLETE. The TVB-39 Codex audit (returned 2026-10-14, never synthesized) and the
TVB-40 Codex audit (returned 2026-10-29, the owner's first SSH-launched review) are both
adjudicated below and every accepted finding is repaired, rerun and receipted. The daily
headline is byte-identical. The owner's direction this session: go slowly, stop tweaking
strategies until review is done, organise priorities; two rulings recorded (the 18:00 ET Globex
roll is "the day" for any futures bench; "backtest to KILL" replaced by "characterize, do not
adjudicate" in the charter, CLAUDE.md and the session-start reminder).

### Context pulled in at the start

- Local main was 32 commits behind origin (the two cloud STRAT ML sessions, PRs #3-#6, merged
  2026-10-28 by the owner); fast-forwarded to 8351054. VectorBT Pro is retired (CLAUDE.md
  gotcha rewritten in the cloud); `uv sync` is safe. The cloud-to-local handoff is
  `docs/experiments/strat_ml_cloud_handoff_2026-10-28.md`; nothing of the vessel was run here.
- The owner's first SSH Codex run (13:41 local, 2026-10-29) came through but carried the
  plugin's generic "last five commits" prompt, not the work order: it reviewed PR #6's phone
  review page (four findings: blind mode leaks the outcome through the anchor description and
  the result shown on tap; a blind call stays editable after the reveal; clearing a verdict
  deletes the whole record; an empty filter leaves the previous trade on screen) and wrote no
  file. Those findings live only in the Codex session log and in this entry; the phone page is
  the vessel's, not this thread's. The second run (15:11) followed the work order and wrote
  `docs/reviews/tvb40-codex-audit.md`.
- A stale git worktree from the TVB-12 era (`.claude/worktrees/agent-aba898ce6f7f356c9`, one
  commit: a 330-line BF paired-detector design draft never on main) was removed with its
  branch on the owner's word.

### TVB-39 audit: critical synthesis (F1-F8)

Read critically; every finding reproduced in the code or the data before acting.

- **F1 HIGH, the hourly entry on equality: ACCEPTED, repaired.** `walk_hourly` entered on
  `>=` / `<=` where the census breaks strictly. The audit's count (1,210 rows entered on a
  touch, 312 exited before the trade existed) and its worked case (ACE 2026-04-29: entered and
  lost -0.72% at 00:00 on a high exactly at the level; the first strict break is 02:00)
  reproduce: in the rebuilt viewer data that row now enters at hour 2 and leaves an hour later
  at -0.16%. Fix: strict entry; target, one-R and stop touches stay inclusive.
- **F2 MEDIUM, a partial entry day accepted: ACCEPTED, repaired.** The entry day must be
  observed from 00:00 through the entry hour without a gap, else the unit's hourly result is
  `partial_entry_day` (counted, excluded; the daily unit untouched). 264 rows (the audit's 261
  plus the 3 old `no_entry_hour` rows, which were also partial days).
- **F3 MEDIUM, a missing cap hour removed the cap: ACCEPTED, repaired** (the audit's fault
  injection; not observed in the snapshot). The scan is bounded by the cap day's 23:00
  timestamp whatever candles exist; a missing hour before the exit censors; `hours` and
  `entry_hour` are timestamp differences.
  Vectors first: `tests/test_domino_manage_hourly_fix.py` (v20a-e: long and short equality
  before the break, an equality hour that would have exited, a partial entry day and a gap
  before the entry hour, a gap before / after the exit, the missing cap hour with later data,
  hours from timestamps); all five failed on the old walker and pass on the new one; the
  existing v17 vectors unchanged. Prereg A2.2 carries a dated clarification of "reached".
  Rerun `manage --as-of 2026-10-10`: every non-hourly column of the 179,498 rows identical to
  the baseline, zero non-hourly fields of manage.json moved, the markdown differs only in the
  hourly counters and the A2.2 table; 1,473 hourly rows changed, `hourly_exit` 55,112 -> 54,851.
  The paired lines: reversal C_h - C -0.14 -> -0.12 [-0.26, +0.03] (its interval now spans
  zero), continuation 0.00, inside +0.21 -> +0.23 [+0.06, +0.40], outside -0.27 -> -0.26; A and
  D within about a tenth. No sign moved. Receipt, ledger and the TVB-39 R2 line updated.
  *[Corrected 2026-10-31, TVB-41 Codex audit F2: the reversal interval was already through
  zero before the rerun ([-0.28, +0.01]), so nothing transitioned; the inside D_h - D point
  estimate did cross zero (-0.002 to +0.008, its interval through zero both times); and the
  264 are exclusions, of which 261 were formerly scored (the scored hourly subset shrank
  55,112 to 54,851). Receipt and ledger corrected in TVB-42.]*
- **F4 MEDIUM, the reconstructed fill as a touch threshold with a first-candle fallback:
  ACCEPTED, repaired.** `settle` now carries `at`, the recorded price the book left on (T1, T2,
  one R, the stop); the marker search uses it with a one-in-a-billion tolerance and never falls
  back to the day's first bar (a miss sits on the last bar and says "no bar of the day reaches
  the price"). The one-R circle and the out arrow now use the same price (the ACE 2026-06-14
  17:00 / 18:00 split).
- **F5 MEDIUM, the reference stop drawn at the end of the day: ACCEPTED, repaired.** The chance
  book's stop exit sits on the adverse-side touch hour; an entry-day stop is labelled "the daily
  bar does not order the entry and the stop, the engine takes the stop first".
- **F6 MEDIUM, the silent book-C fallback: ACCEPTED, repaired.** A selected book without a
  result keeps its name (`missing: true`, the window it would have run, no price); the ladder,
  the strip, the story and the chart say so instead of borrowing C.
- **F7 MEDIUM, the whole stack labelled with the entry-time class: ACCEPTED, repaired.**
  `stackSubset` splits the day's breaks into the converged subset (the daily level plus the
  levels inside the class's own census band of it: exact 0, near 0.25%, within 1%) and the far
  ones; the domino label, the band, the strip chip, the context chip and the story name the
  subset and label the far levels with their distance (0G 2026-08-31: "D+W same price; M
  +34.59% beyond"). Weekly and monthly rows are classed on the whole stack, unchanged.
- **F8 MEDIUM, the fee narrative: ACCEPTED, corrected** in the receipt, the ledger and the
  TVB-39 HANDOFF line: six management lines are negative net with the interval clear (reversal
  A -0.13; continuation A, B, C, E -0.31 to -0.32; inside B -0.15), not "flat".
- **Open question the audit named and did not rule:** the with-trend inside break's T1 (the
  prereg's ladder versus the skill's mother-bar far side) stays the owner's STOP-and-ASK.

### TVB-40 audit: critical synthesis (F1-F6)

All six confirmed against the source on receipt; all six display / readback; none touches a
row or the engine.

- **F1 Compare drawdown by row, not by day: ACCEPTED, repaired.** `bookStats` scores the
  drawdown on completed daily sums (the engine's `book_stats`, peak clipped at zero). Verified
  on the universe table against pandas on the engine CSV: every book within about a dollar
  (C -629,820 page / -629,821 engine; the old row-level figure was -629,981). NOTES corrected.
- **F2 the magnet picks the next candle on the right half: ACCEPTED, repaired.** `cellIndex`
  picks the bar whose axis cell holds the time (the last bar opening at or before it); the
  audit's 0.49 / 0.51 case is a unit test.
- **F3 exit narration: ACCEPTED, repaired.** The hourly clock in the trade's own colours (a
  short leaves on a green hour in a green day; 27,674 short rows read wrong before); a no-target
  row reads its status (exit / marked at the cap / censored) instead of "left with the daily
  clock"; a same-day stop and one-R tie says the bar cannot order them and the engine takes the
  stop. The Playbook's clock sentences are direction-neutral.
- **F4 travel is book C's window: ACCEPTED, labelled** in the strip and the story (the engine
  records travel once; the page does not rerun it for the selected book).
- **F5 the calendar month average counts censored rows as zero: ACCEPTED, repaired.**
  `monthSummary` divides by the rows with a result and prints the filled count.
- **F6 a book change leaves the old sort: ACCEPTED, repaired.** `setBook` re-sorts.
- Held by the audit and not re-done here: the universe round trip, 620 Compare statistics, the
  closed-bar chips, the founding rule. Not proven by anyone yet: drawing persistence across coin
  switches in a live browser (the audit's own caveat; still on the viewer's list).

Coverage: `tests/test_domino_viewer_js.py` (14 cases, node on core / stats / story with the
audits' named shapes). Suite 433 passed, 2 skipped; ruff clean.

### In-session cold review (a separate Claude agent, static read, no access to the lead's reasoning)

Five MEDIUM on the repairs above, four accepted and folded before the commit, one accepted in
part:

- **M1 the 1H entry arrow still used the equality touch: ACCEPTED, repaired.** On the hourly
  pane the entry arrow sits on the engine's own entry hour (`entry_h`) when the hourly clock
  recorded one, else on the first bar strictly through the level; ACE 2026-04-29 now shows the
  arrow at 02:00 beside the hourly-clock exit, not at 00:00.
- **M2 a missing book got a borrowed window and a false reason: ACCEPTED, repaired.** The data
  settles it: 1,295 of the 1,296 null-D5 rows are headline-censored rows the engine never
  scored (237 of them with a complete chance window), and a weekly / monthly chance window runs
  to 41 / 183 days, not five. A missing book now borrows no window (the entry day only), the
  Held fact reads n/a, and the reason is the row's own status (`status5` for the five-bar books,
  `status` for the others: "not scored: the headline row is censored" where that is the case).
- **M3 weekly rows still carried the whole-stack label: ACCEPTED, repaired.** `chance.stack_class`
  classes a weekly / monthly unit on its OWN level against the daily level; the converged pair
  is now read from the row (daily rows: the daily level and `near_tf`; weekly / monthly rows:
  the unit's level and the daily level) and no census band is re-derived in the browser. The
  test fixture now has the engine's shape (the daily level is always in the stack).
- **M4 book D5's reason on weekly / monthly units: ACCEPTED, repaired.** `status5` decides
  "daily-close exit" versus "marked at the 5-bar horizon"; the D5 horizon runs past the daily cap
  on those units.
- **M5 the marker repairs have no behavioural test: ACCEPTED IN PART.** `drawPane` is DOM-bound
  and stays checked at the source (the fallback greps now also catch `|| ks[0]`; the entry-hour
  wiring is asserted); `cellIndex` is tested on unequal month cells too; the missing-book
  story test now asserts the paragraph carries none of book C's figures. A headless-browser
  marker test on the audits' named rows (ATOM 2026-05-09, ACE 2026-06-14, BTC 2026-03-16 W)
  is on the viewer's list, not done.

M5's tail: `oneR` in the page is a float rebuild of the engine's decimal one R (the 1e-9
tolerance covers it; the audits' ATOM / ACE rows are not exercised by the tests), and NOTES
claimed marker behaviour without a rerun (NOTES now says the repairs are node-tested and the
browser shots predate them). LOW, fixed: the tie sentence said "the same week / month" for
weekly / monthly rows (the offsets are days: now "the same day"); "before one R" printed when
one R was never touched (now says so; the test covers both); the v20c assertion now says
`censored`; the prereg's v17 line now cites the strict reading; CLS_LABEL has a "plain" label;
the ladder footer no longer prints "fills at - for" for a book without a result. LOW, noted and
left: `walk_hourly` rebuilds the day-index dict per unit (performance only); its "stop" touch
uses the target-side comparison and is never read (an engine edit, so a rerun: next engine
round); the v20e timestamp claim is unobservable while contiguity is enforced (kept as a guard);
the magnet snaps to the first or last bar from any distance outside the data. Held by the
review (checked, correct): the strict entry against the census, the partial-day rule, `open`
only at the cap timestamp, the caller's status handling, the paired comparison under the
prereg's own wording, no caller assuming book C, the drawdown and month bounds, the stack bands,
the stop marker's side and the labelled miss, the direction- and status-aware words, the magnet's
edge bars and the proof flag. Suite after the fold: 435 passed, 2 skipped.

### Also this session

- **Framing (owner, 2026-10-30):** the insights report showed the lead turning "do the targets
  get hit?" into a stop verdict; the owner traced it to "backtest to KILL the strategy". Charter
  S0, the CLAUDE.md invariant and the session-start reminder now read "characterize, do not
  adjudicate: both directions with equal weight; a positive cell a path to a declared arm, a
  negative cell a path to a kill test; no verdict, parameter change or recommendation unless
  asked; answer the question asked". The run-to-confirm warning stays.
- **The cc menu (the owner's SSH menu on this PC, `~/Documents/WindowsPowerShell/cc-tools/`):**
  entries 6 and 7 start / stop the trade viewer as a scheduled task (`viewer.ps1`, port 8765,
  survives the SSH session); the laptop reaches it with `ssh -L 8765:127.0.0.1:8765 pc` then
  `http://127.0.0.1:8765/`. Not in this repo (the owner's profile); parse-checked, not yet
  exercised from the laptop.
- **Ruling: the 18:00 ET Globex roll is "the day"** for the futures bench the owner is
  considering (ES / NQ / MES / MNQ from the ATLAS Databento cache, 1-minute source 2011-01 to
  2025-12, resampled 5m to monthly, `vectorbt-workspace/data/databento_cache/`). Recorded
  before any run; the equity-perp session-bar result in the vessel showed the bar choice alone
  flips every family's sign.
- **The owner's direction:** stop tweaking until review is done; one neutral row contract so
  any run (either line) exports rows the viewer draws, then the one-instrument bench to see
  entry / exit / target / continuity options side by side; the lead's ranking of the current
  implementations by evidence state was given in session (management book, stacked 2-2
  continuation, equity perps on the session bar, continuity strategies, alt break book, the
  round-3 executor book), as a reading, not a promotion.

### Files created/modified

- `analysis/domino/manage.py` (`walk_hourly`, its caller), `tests/test_domino_manage_hourly_fix.py`
- `analysis/domino/viewer/{core.js,stats.js,story.js,app.js,NOTES.md}`, `tests/test_domino_viewer_js.py`
- `analysis/domino/results/{manage_tables.md,manage.json,manage_trades.csv.gz}` (hourly columns
  and the A2.2 table only), the viewer's data rebuilt (gitignored)
- `analysis/domino/MANAGE_RECEIPT.md`, `docs/ARM_LEDGER.md`, `docs/experiments/tvb37_management_book_prereg.md`
- `docs/ATLAS_Timeframe_Continuity_Charter.md` (S0), `CLAUDE.md`, `.claude/commands/session-start.md`
- `docs/reviews/tvb40-codex-audit.md` (committed as returned), `docs/reviews/REVIEW_REQUEST.md`,
  `docs/HANDOFF.md`, `.session_startup_prompt.md`

### Open

- [ ] The viewer row contract: one neutral export so any run (the management book, the vessel,
      a futures bench) draws on the same page; then import runs for review (owner's direction)
- [ ] The one-instrument bench (ES on the Globex day, or an equity perp) after the contract
- [ ] The with-trend inside break's T1 STOP-and-ASK (owner rules; amendment A3 before code)
- [ ] Drawing persistence across coin switches in a live browser (never proven)
- [ ] Viewer: journal layer; one drawing slot across panes; an hourly archive beyond ~208 days
- [ ] The phone review page's four Codex findings (vessel thread; blind calls so far were not blind)
- [ ] HANDOFF.md archive (over the limit; the owner's word); `proto_codex/` disposition
- [ ] The vessel's cloud handoff section 5 questions, when that thread resumes locally

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb41-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: ADDRESSED (returned 2026-10-30; both findings repaired in TVB-42)
- Commits to review: `8351054..74dcb28` on `main` (8351054 is the post-cloud-merge sha the session
  started from; 5e71b05 commits the TVB-40 audit as returned, 3fa6990 the viewer repairs and the
  framing, f24a4ce the engine repair, the rerun's results, the review fold and the docs, 74dcb28
  the review tail; the sha-pinning commit after 74dcb28 is docs only).
  Sanity-check: `git diff --name-status 8351054..HEAD`.
- Scope / what changed: `walk_hourly` (strict entry, entry-day coverage, cap bound, gap
  censoring, timestamp hours) with five vectors; the hourly columns and the A2.2 table rerun;
  the viewer's four modules on ten audit findings with 14 node cases; prose corrections.
- Focus areas: the byte-identical claim (every non-hourly column of manage_trades.csv.gz
  against 2c7fe1c's file, which this repo does not keep: regenerate from `git stash` or trust the
  method in the entry); whether `partial_entry_day` should also censor rows whose entry day is
  complete but whose later days have gaps that the scan now treats as censored (it does; is the
  count surfaced anywhere other than `hourly_censored`?); `stackSubset`'s bands against
  `chance.py`; `settle`'s missing-book contract against every caller; the magnet's `cellIndex`
  on the 1M pane; the `near` tolerance on sub-cent coins; the story's new sentences against the
  rows; the cold in-session review's findings (listed in this entry once returned).
- Reviewed by: Codex (local CLI, source review + cached-data replay), `docs/reviews/tvb41-codex-audit.md`
- Findings: NEEDS-CHANGES, two MEDIUM, no engine defect. F1: book D5's "daily-close exit"
  sentence in `story.js` appends `clockWords`, which reads the headline book's `status` /
  `exit_k`, so a weekly / monthly row whose headline is open at day 20 while D5 exits later says
  both "the daily clock fired" and "marked at the day-20 close" (BLUR 2026-07-24 W short; 24
  rows). F2: the rerun prose above says the reversal paired interval "now spans zero" (it
  already did: [-0.28, +0.01] before) and "no sign moved" (the inside D_h - D point estimate
  went -0.002 to +0.008, interval through zero both times), and "lost 264 rows" conflates the
  264 partial-entry exclusions with the 261-row contraction of the scored subset (3 of the 264
  were already excluded as `no_entry_hour`). Verified repairs: the hourly engine and every new
  hourly column reproduce from the cached candles; zero non-hourly changes in `manage.json`;
  settlement, stacks, markers (121,512 exits, 1e-9 repaired 222 float touches, zero differences
  from exact decimals), drawdown, month denominator, fee prose all held. Critical synthesis and
  repairs: the TVB-42 entry.

---

## Side thread 2026-10-22 (not a TVB session): STRAT ML research vessel, Phase 3 to the test-1 gate (STOPPED AT THE GATE, as the brief orders)

**Date:** 2026-10-22 (cloud session, branch claude/jolly-babbage-vlk7yz; the owner's brief
`docs/experiments/strat_ml_phase3_brief.md` is the spec: fixes, then test 1, then stop and report
the gate before tests 2-5)
**Status:** Test 1 run, gate FAILED on the alt-coin table. Tests 2-5 NOT run (the brief forbids
running them on alts "anyway"); the HIP-3 session branch (brief section 11) is the next run and
needs the owner's word.

- **Read first:** `docs/experiments/strat_ml_phase3_results.md` (the gate line and every verdict,
  verbatim) and the page `analysis/strat_ml/reports/STRAT Trigger Research v3.md` (or .html,
  self-contained, phone-readable; glossary first, a What-this-means above and a verdict below
  every table, every R after costs, every z clustered by trigger date).
- **Built:** `analysis/strat_ml/report_v3.py` (extends `report.py`, which is untouched: the
  phase-1 table is read through the phase-1 loader; the table helper refuses to render without
  its two texts; cost model as a config block; the gate as the first line of the page),
  `analysis/strat_ml/m15_check.py` (15-minute klines pulled into their own raw folder for a
  block-random 20,000-row sample), `tests/test_strat_ml_report_v3.py` (11 hand vectors: glossary
  verbatim vs the brief, clustered z, cost arithmetic and funding marks, the 15-minute walk, the
  gate rule). Data bootstrap per the brief's appendix reproduced phase 1's rows exactly
  (565,687 built, 9,595 censored, 556,092 with a 10-bar outcome; HIP-3 15,844 / 11,324).
- **Section-5 fixes:** 3f re-rendered (model A refit on integer-coded categoricals; top pair =
  direction x BTC 30-day realized-vol percentile); stablecoin drop caught only USDCUSDT (1,153
  rows, -0.233R; log `analysis/strat_ml/stablecoins_dropped.json`), the headline moves by
  +0.0004R; the v3 page is numbered in page order with the caveats last (the phase-1 outputs stay
  as published, per the brief).
- **Cost model:** mean cost 0.176% of price per phase-1 trade (53% of the -0.331% loss, the
  brief's "about half" holds); 0.02-0.04R per trade by tier; the two tier x family cells that
  were positive before fees are under zero after them; whole book -0.031R -> -0.054R after costs.
- **15-minute check (reported, not fixed):** against-first 67.8% on the hourly clock, 55.7% on
  15-minute bars with the trigger bar counted, 47.5% with its own adverse print ignored (phase 1
  guessed 27%). The hourly artefact is real but smaller than estimated; sections 7b-7c of phase
  1 read with the 15-minute version. The fav-first / adv-first split in mean R survives
  (+0.18R vs -0.23R after costs) and is partly mechanical (adverse first = nearer the stop).
- **Test 1, the gate: FAILED.** Held N bars with no stop and no target, costs paid, on 2025-26:
  continuation -0.085 ATR (-0.78% of price) at 5 bars, z -2.3 (significantly AGAINST the break,
  -0.158 ATR at 10 bars, z -3.2); inside -0.046 ATR, z -1.8; outside -0.035 ATR, z -1.0;
  reversal +0.010 ATR, z +0.3 (flat). Whole book -0.045 ATR at 5 bars, z -2.1. On 2020-24 the
  same cells were flat (whole book -0.001 ATR at 5 bars); the continuation drift was +0.03 ATR
  there and -0.085 on test, the regime story the brief named. No BTC-vol tercile, year or
  liquidity tier cell clears the bar either. Reading in trader terms: after a daily break on an
  alt, price does not keep going; in 2025-26 it leans back the other way, and no stop, target or
  trail can harvest a drift that is not there.
- **The R-unit trap, stated on the page:** "mean R no stop" at 10 bars reads +0.05R after costs
  (+0.09R before, phase 1's number) while the same rows are -0.38% of price and -0.03 ATR: the
  R clip is one-sided and tiny setup bars turn ordinary moves into many R. The gate is read in
  ATR, as the brief's worked example does.
- **Not available here:** an underlying-stock feed for the HIP-3 control (brief run 2) is not
  wired into the environment; the HIP-3 snapshot has no funding series (charged 0, flagged).
- **Next (the brief's order):** section 11, the HIP-3 session branch (test 1 on the session
  build clustered by date, leave-one-ticker-out, the gap rule, the fair-line sweep at n >= 300),
  on the owner's word; the alt-coin line closes unless the owner re-opens it.

- **Addendum 2026-10-24 to 10-27 (same thread, after the gate; exploratory cuts, no arms, nothing
  promoted):** (1) Test-1 drift cut by the continuity columns already on every row, train beside
  test: every higher-timeframe context cell FLIPS SIGN between 2020-24 and 2025-26. "Week or
  month inside but coloured our way" was the best cell on train (+0.13 ATR at 10 bars, z +3.2;
  the only managed cell at or above zero) and the worst on test (-0.11, z -2.9); full
  continuity (week and month both already 2 our way) +0.19 train / -0.14 test, managed book
  39% win in both periods (7 in 10 have no target left); the week-only domino break (the daily
  break also takes last week's extreme) is flat on train and one of the worst cells on test
  (-0.34 ATR at 5 days, z -2.4), but that is the day's geometry, not the week's trade. Reading:
  on alts, higher-timeframe context is a regime read, not a filter; what is stable across
  regimes is the WIN RATE by structure (week-with / month-against 41% both periods, both-coiled
  59-61% both), what flips is the drift. The skill's Tier C (week and month 2 against) reads
  -0.10 ATR on test, mildly negative on train. (2) Regime anchor days found by averaging the
  net 5-bar drift across all coins per trigger day: the market-wide days come in PAIRS, a day
  when every break failed followed within 48 h by a day when every break the other way ran
  (2024-11-04 -> 11-05/06; 2025-01-30/31 -> 02-01/02; 2025-05-04/06 -> 05-07/08). On the
  2025-10-10 liquidation day the mechanical book was short with the owner (502 shorts, 91% won,
  +0.73R after costs); the trap was 10-12, the bounce longs above the inside day with week and
  month both 2-down (Tier C), 7 of 9 stopped 4-5 days later. (3) The owner's visual review list:
  `analysis/strat_ml/reports/v3_visual_review_list.md` (and .csv, force-added past the *.csv
  rule): BTC, ETH, SOL, XRP, DOGE, ZEC on 20 anchor dates, entry / stop / target / outcome.
  (4) **A phone review page** (private claude.ai artifact, link NOT in the repo; source
  `analysis/strat_ml/phone_review/page.html`, data pack `build_pack.py` -> the gitignored
  `analysis/strat_ml/data/phone_review/`): every trade of those six coins on candles, two
  stacked panes (trade 1H/1D above, week or month context below) with the context bar drawn AS
  OF THE TRIGGER HOUR (partial bar from the hours before the trigger, the table's own rule),
  last bar's high / low and the period's open as lines, a blind mode (both panes stop at the
  trigger hour; "would take / would skip" recorded before the reveal; the score line averages
  the takes against the skips) and a verdict + note per trade kept in the browser, exported as
  text. Chart library: lightweight-charts 4.2.0 from a CDN (the owner's TVB-40 preference was
  amCharts for the desktop; the phone page is a format test, owner's word 2026-10-26). The
  owner's first read: the hard part on a phone is the multi-timeframe context; v2 is the answer
  to that. (5) `/adhd` skill added at `.claude/skills/adhd/SKILL.md` (owner's draft, verbatim).
  (6) The owner's market-data MCP server (underlying-stock bars for the HIP-3 names) is wired
  into cloud sessions now: daily bars for any US ticker, 200 bars (back to 2026-01-08 on
  2026-10-24, a ROLLING window), 60-minute bars 09:30-anchored but only ~24 trading days deep.
  So the brief's HIP-3 run 2 (the underlying control) is possible at DAILY resolution, and the
  bars should be pulled and frozen as a snapshot before late December, when the HIP-3 window's
  start falls off. (7) Two commits on this branch (9155973, f354eff) carry an AI attribution
  trailer against the spine's "no AI attribution" rule (the harness asked for it); later commits
  omit it; history not rewritten.
- **Owner's direction at close (2026-10-27):** move the research off alts (one market, two
  regimes, every context effect flipped between them) to an instrument class with many regimes
  (index futures or their ETFs, session bars, 15+ years) with the continuity arms declared as an
  ablation ladder BEFORE running; a $100 live data run on Hyperliquid (crypto 24/7 plus equity
  perps) is planned; the lead's ranking and the bar-definition warning for equity perps (UTC day
  -0.10R vs NY session +0.12R, section 13) are in the session transcript and summarised below.

### Open

- [ ] Merge `claude/jolly-babbage-vlk7yz` into main (PR on the owner's word) so the PC pull
      brings phase 3, the review list, the phone page source and the /adhd skill.
- [ ] HIP-3 session branch (brief section 11), on the owner's word; run 2 at daily resolution via
      the market-data server, bars frozen as a snapshot first.
- [ ] Design session for the next instrument set (index / ETF, session bars, multi-regime) and
      the continuity ablation ladder; prereg before code.
- [ ] The owner's blind calls from the phone page, pasted back, scored against the rows.
- [ ] XAUUSDT / XAGUSDT (Binance gold and silver perps) sit in the "alt" universe; a hygiene
      note like the stablecoin one, not applied.

---

## Side thread 2026-10-20 (not a TVB session): STRAT ML research vessel, Phases 2-5 run to the end (COMPLETE)

**Date:** 2026-10-20 (cloud session, branch ccr-84c65430-bqc01u; owner's word: run it to the end,
cloud container, no Railway)
**Status:** COMPLETE for the spec's v0.1 pipeline. Everything is exploratory; nothing is promoted.

- **Read first:** `docs/experiments/strat_ml_phase2_events_design.md` (definitions declared before
  the build; section 8 = the first read-out) and the report
  `analysis/strat_ml/reports/strat_ml_report_2026-10-20.html` (self-contained, phone-readable,
  plain-words explainer on every section; also published as a claude.ai page for the owner).
- **Built:** `analysis/strat_ml/events.py` (one row per coin, day, direction; the census
  strict-break classifier and calendar reused; TVB-37 R and magnitude ladder; point-in-time
  week / month / 4H context; hourly-resolved outcomes at 1 / 3 / 5 / 10 daily bars, stop-first
  on ties), `analysis/strat_ml/report.py` (baseline tables with counts and Wilson bands, k-means,
  LightGBM + SHAP on a 2025-01-01 time split, depth-3 tree, HTML), 9 hand-vector tests.
  565,687 rows in 77 s; the report in 72 s. Cache (events.parquet) is per-container; the
  roster and the summary JSONs are committed.
- **Findings (hypotheses):** (1) a look-ahead feature was caught by ranking too high and is now
  excluded; (2) target-before-stop is mostly target distance, so the money question is modelled
  on context only; (3) context ranks the losers (bottom decile -0.25R on 2025-26) far better
  than the winners (top decile +0.03R); BTC's realized-vol percentile is the top feature;
  (4) the blue-sky break (no week / month level beyond the entry; 59k rows) loses -0.11R with
  the setup-bar stop hit 61% of the time, while its unmanaged view is slightly positive: a
  stop-placement question, the TVB-37 suspect again; (5) majors and alts look alike per pattern
  within their bands, but majors are two coins and the test period is 99.6% alts.
- **Stop head-to-head DONE (owner's ask, same day):** `events build --stop-mode bar0` + 
  `compare_stops.py`. On the same 119,926 inside-break rows the bar-0 stop (0.84 ATR median)
  lifts the win rate from 54% to 62% and cuts stop-outs from 45% to 35%, and the mean return
  per trade is -0.2% of price under BOTH stops; whole book -0.3% under both. The stop shapes
  the loss, it does not remove it. Design doc section 9; `reports/stop_compare_2026-10-20.md`.
- **Excursion clock DONE (owner's question, same day):** new columns (`h_fav_x`, `h_adv_x`,
  `first_excursion`, `mfe/mae/r_close_{6,12,24,48,72}h`) and `excursion.py`. Half of triggers
  show +0.25R within 6 h; a time-stop rule saves ~0.02R per laggard because the mark already
  carries the loss; the first-excursion split (+0.085R vs -0.23R) is the lead but the trigger
  hour's own low is an artefact that needs 15-minute bars. `tfc_score` = 1 is the blue-sky
  set by construction. Design doc section 10.
- **The lead's read of the whole book, 2026-10-20 (owner asked "what would you change, what
  would you test next"; advice, not rulings; grounded in the event table):**
  (1) The setup-bar stop (median 0.74 ATR) sits inside the daily noise: the median trade is
  0.9R against by day 3 and 1.6R by day 10. With no stop at all the book marks +0.09R (alts) /
  +0.23R (majors) at 10 bars against -0.03R managed, median still negative: the same shape
  TVB-38 found on Hyperliquid (+0.5..0.9 per trade from the stop swap). Widening to bar 0
  does not change the expectancy; removing the price stop does, and buys a tail.
  (2) The blue-sky break (no week / month level beyond the entry) is the worst cell WITH the
  stop (-0.10..-0.17R, stopped 59-74%) and the best cell WITHOUT it (+0.09R continuation,
  +0.30R inside break, unmanaged). The stop is chopping out the trend trades.
  (3) The owner's hazard (lower-timeframe entries inside higher-timeframe inside bars) does
  NOT show in the aggregate: month-inside / week-inside is the flattest cell (0.00R, n 103k);
  the bad cells are extension (month 2U with week 2U -0.09R, week 3 -0.14R). A confirmation-
  bias check the owner asked for in their preferences.
  (4) BTC's 30-day realized-vol percentile is the strongest regime feature: top decile -0.09R
  managed / -0.10R unmanaged, bottom decile +0.24R unmanaged.
  (5) Longs and shorts flip sign by year (2021 longs +0.09R, 2022 shorts +0.11R, 2025 longs
  -0.13R): the year's trend, not the pattern.
  What the lead would test next, in order, each a declared arm, never a pick: (a) replicate
  the TVB-37/38 chance book and management book rule-for-rule on the Binance table (different
  venue, 2020-2026, dead coins in) to see whether the stop-swap lift and the stacked
  continuation survive out of venue; (b) a pre-committed skip-list arm (skip blue-sky breaks,
  skip BTC top-vol-decile days) against the control, in the ablation shape; (c) the no-stop
  book with a declared tail rule (the hourly clock or an ATR-scaled disaster stop at 2-3 ATR)
  since the tail is the price of (1); (d) 15-minute bars to settle the first-excursion split.
  Not worth more time: exit clocks (the hourly, under-water and time-stop variants all move
  the book by a few hundredths of an R).
- **The original Pine (TheStrat Magnitude + Targets, the owner's live indicator) read against the
  table, 2026-10-20 (owner's ask; thoughts, not rulings):** its "star" (high-conviction) setups
  cut from the daily rows: Shot-Gun 2-2-2 (42k rows: 71% win, target-first 70%, mean -0.00R,
  median reward-to-risk 0.38), 1-2-2 rev strat (32k: 72% win, -0.03R, R:R 0.31), 1-3-2 (15k:
  48% win, -0.05R), 3-2 Boom on a hammer / shooter proxy (2.2k: 52%, -0.07R), 1-3 one-bar rev
  strat (18.7k; the setup-bar stop is ALREADY inside the day's range for a 1-3, so its -0.14R is
  a stop artefact; rerun on the bar-0 file). Star vs the rest: 64% win vs 52%, the same money
  (-0.04R vs -0.03R managed, +0.09R both unmanaged); unmanaged, the stars beat the rest in
  2020-22 and lost to it in 2023-25. Reading: the high-conviction patterns win MORE OFTEN
  because their targets are the reversal anchor (closer), not because they pay more per unit
  of risk; win rate is what a discretionary trader feels.
  Parts of the Pine that the daily research line never carried, each testable on the table:
  (1) the pivot ladder beyond T1 (prior highs / lows not yet taken out, nearest first, 250 bars
  back): the management book holds week / month levels only ("no daily pivots" ruling) and
  59,130 rows have NO target at all; (2) the Potential-3 / invalidation status (the other side
  of the setup bar breaks AFTER entry): the table carries both triggers' hours, so "exit at the
  hour the other side breaks" is a declared exit arm against the stop, cheap to run; (3) the
  2-1-2 momentum filter (inside bar in the upper / lower half of the prior 2's range) as a
  flag; (4) the chop counter (reversals since the last target hit) as a symbol-level regime
  feature. The BF harvest exit belongs to the TFC indicator, not this Pine, and cannot be read
  from the table without the BF line logic.
- **PR #3 opened on the owner's word** (https://github.com/sheehyct/Tradingview-Backtesting/pull/3):
  the whole vessel, branch ccr-84c65430-bqc01u into main.
- **Pivot ladder ported (owner: "this is where the drift is"):** the Pine's ladder on the daily
  rows (`events.py:pivot_ladder`, `pivot_ladder.py`). Rung 1 reached 81%, rung 2 64%, rung 3 50%
  within 10 bars, mean 2.8 rungs; the Pine's T1 gives 45,713 of the 60,715 no-target rows a
  target and lifts the continuation / inside cells by +0.01..+0.07R, all still at or under
  zero. The A3 question (mother bar as T1 for the with-trend inside break) has its number:
  inside family -0.030 -> -0.009R, hit rate 55% -> 71%. Design doc section 11.
- **Ticker census (owner's ask, labelled overfit):** the top coins sit at the edge of noise
  (z about 2), the bottom coins are real (z -4 to -7); the best coins are the trending ones
  (continuation share r +0.23), not the pattern-diverse ones. USDCUSDT is a stablecoin perp in
  the universe: exclude stables on the next build. Design doc section 12.
- **Equity perps two ways (owner: "the one thing we did not test"):** the xyz dex's 115 perps
  fetched through the census's own fetcher (`hl_fetch.py`, ~208 days of hourly bars, roster
  `xyz_summary.json`), the builder given `--session calendar|rth` and `--roster`. US-listed
  perps on the UTC day: -0.096R (the worst cell in the vessel; 2,177 of 9,925 breaks in the
  20:00 NY roll hour). The NY regular session as the STRAT bar: +0.117R, 56% win, every
  family flips sign, +0.3% of price per trade before fees. The first positive cell in the
  vessel, on a 7-month, 76-name, cross-correlated sample: a lead, not a finding. Design doc
  section 13 lists the declared next tests (paired bars-vs-hours, the daily-candle window back
  to listing, a monthly refetch).
- **PR #3 close-out (2026-10-20):** main (TVB-40) merged into the branch, the HANDOFF conflict
  resolved by keeping both entry sets; Codex's four PR findings (partial-download build, hourly
  gaps inside the outcome window, winsorization bounds leaking test labels, a denominator
  mismatch) fixed in 884e2cf, every receipt rebuilt (numbers within rounding), threads answered
  and resolved; `page.py` now assembles the phone page from the receipts. The PR reads clean
  and waits only on the owner's merge.
- **Phase 3 is briefed (owner, 2026-10-21):** `docs/experiments/strat_ml_phase3_brief.md` is the
  complete spec for the next cloud session (opening prompt inside it); its appendix carries the
  environment bootstrap (the data re-pull, what the brief assumes that is not on disk: no
  15-minute bars, the event table is built by events.py). Merge PR #3 before starting it.
  Data pinning (owner, 2026-10-22, option 1): the HIP-3 hourly bars are committed as a frozen
  snapshot (`analysis/strat_ml/snapshots/xyz_2026-10-20/`, 22 MB, gitignore exception;
  `hl_fetch --from-snapshot`), the Binance pull is pinned with `--until 2026-10-16`. A bucket
  for the whole cache (option 2) is deferred until more cloud sessions are planned.
- **STOP-and-ASK for the owner before more code:** exclude stablecoin perps from the
  universe (USDC, FDUSD, BUSD, TUSD, USDP, DAI, USD1)? pull 15-minute klines for the universe (same
  file count as 1h, 4x rows, ~2.5 h) to settle the first-excursion question? Make the blue-sky cell a declared arm in
  the domino book (wider stop / no-stop clock)? Pull metrics (OI, taker ratio) for the alts the
  trigger table uses? The with-trend inside break's T1 ruling is still open (ladder used).
- **Dependencies:** lightgbm, shap, scikit-learn added to pyproject (uv sync is safe; VectorBT
  Pro retired 2026-10-17).

---

## Side thread 2026-10-17 (not a TVB session): STRAT ML research vessel, Phase 1 data layer (COMPLETE)

**Date:** 2026-10-17 (cloud session, branch ccr-84c65430-bqc01u)
**Status:** COMPLETE for Phase 1 of the owner's `STRAT_ML_RESEARCH_SPEC.md` v0.1: data
acquisition only. Exploratory research, nothing deployed. No event detection, no bar
classification written (the owner's rule: reuse the existing classifier when Phase 2 starts).
TVB numbering untouched; the TVB-40 startup prompt still governs the main thread.

- **Plan and findings:** `docs/experiments/strat_ml_phase1_data_plan.md` (read this first).
- **Code:** `analysis/strat_ml/binance_vision.py` (S3 listing, checksum-verified raw zip cache,
  parquet build, point-in-time universe manifest; CLI `fetch` / `build` / `universe` / `status`),
  13 offline tests in `tests/test_strat_ml_binance_vision.py`, thread log
  `analysis/strat_ml/RESEARCH_LOG.md`. Cache under `analysis/strat_ml/data/` (gitignored).
- **Archive facts (USDT-M, futures/um):** delisted perps ARE in the archive (SRM, LUNA, BTCST,
  17 SETTLED stubs excluded); klines monthly from 2020-01 (daily from 2019-12-31; Sep-Dec 2019
  absent), fundingRate monthly only from 2020-01, metrics daily only (5-minute rows) from
  2021-12-01 for most names, BTCUSDT backfilled to 2020-09-01 with every row doubled.
- **Finding that changes Phase 2:** Binance keeps publishing flat zero-volume files for dead
  contracts (SRMUSDT: last real trade 2022-11-15, files to 2024-05; BTCSTUSDT frozen at one
  price 2024-02 .. 2026-06). Delisting is read from volume (`last_traded` in each klines
  manifest), never from file presence; the listing-based universe flag (31 of 900) is a floor.
- **Test slice pulled:** BTC, ETH, LINK, DOGE, SOL, AVAX, SRM (delisted), 1h klines + funding,
  full history, 1,070 files, zero errors; table in the plan doc section 5.
- **Cloud-session gotcha:** `data.binance.vision` is refused by the egress proxy; the bucket
  endpoint `s3-ap-northeast-1.amazonaws.com/data.binance.vision` works and the module tries
  both in order. The live API is unreachable and never used.
- **`uv add pyarrow`** touched pyproject/uv.lock: on the workstation reinstall VectorBT Pro
  from the cached wheel after the next `uv sync` (standing gotcha).
- **Full-universe pull DONE (owner's go-ahead, same day):** 900 USDT perps, 57,319 files,
  0 errors, ~2.5 h; 160 symbols delisted by volume (the listing-based flag said 31), 108 of
  them with a year or more of real history; the committed roster is
  `analysis/strat_ml/universe_summary.json`; plan doc section 6 has the counts. The raw /
  parquet cache (1.9 GB) is per-container: a later cloud session re-pulls (~2.5 h, free), or
  the workstation runs the two CLI commands once and keeps it.
- **Owner rulings 2026-10-17:** Phase 2 imports `analysis/domino/census.py:classify` (strict
  break) with its calendar bucketing, not the scanner's EXP-013 code; VectorBT Pro is RETIRED
  (licence not renewed, nothing imports it; CLAUDE.md gotcha rewritten; the workstation session
  should save this to private memory); no Railway for pulls (cloud container or workstation).
- **Remaining OPEN:** spec open decisions 1-2 and 4 assumed at their defaults (`analysis/domino/census.py:classify`
  strict-break, prereg'd on perps, is the lead's suggestion; the pine-exact
  `analysis/paper/patterns.py` and the scanner's EXP-013 code in the other workspace are the
  alternatives); metrics (open interest, taker ratios)
  not pulled for the universe (~1.3 M daily files; pull for the trigger subset in Phase 2).

---

## Session TVB-40: the charting upgrade: the amCharts trade viewer, built as a two-builder design-off and promoted (COMPLETE)

**Date:** 2026-10-14 to 2026-10-17
**Status:** COMPLETE on the owner's call of 2026-10-17 ("I say move forward with this ...
pushing this out first would be the ideal scenario just to be able to trade review quicker,
though I would include the universe for comparison"). Two builders prototyped the same thing in
parallel, each in its own folder (CLAUDE `proto_claude/`, CODEX `proto_codex/`); the owner
reviewed both and chose CLAUDE's ("night and day"). `analysis/domino/viewer/` is now that page;
the TVB-39 lightweight-charts page is retired (in git history to da7f4c2). The page's receipt is
`analysis/domino/viewer/NOTES.md`; the viewer section of `MANAGE_RECEIPT.md` points to it.
`proto_codex/` is untracked and untouched (the owner may still take ideas from it).

### What was accomplished

- **Round one (e79f8d3, 2026-10-14)**: the reference rows on amCharts 5 Stock Chart (data
  grouping off), the library's drawing toolbar with its own save / restore per coin, System
  levels as read-only axis ranges, the week's and month's closed-bar STRAT type as chips (R10
  operators, checked in Python), drawings proven across reload and timeframe switches.
- **Round two (da7f4c2, 2026-10-15), the design-off**: a calendar (census weeks, equal-size
  dollars per entry day, week totals, year strip) and a sortable trade table in place of the
  card strip; a facts strip; the trade narrated in trader language from the row (setup and
  magnitude source, the plan with every touch day, what the book did and the exit-day test, the
  other clocks, travel); a six-book ladder per trade; a Compare tab (KPI cards, overlaid equity,
  distribution against the chance book, by-setup with D5 minus the chance book); a Playbook tab;
  dual chart panes; stacked tags and markers. Compare figures cross-checked against Python on BTC.
- **Promotion (this session, 2026-10-17)**: the page moved to `viewer/`; `trade_viewer build`
  vendors amCharts 5 (the CDN needs a browser-like agent) and writes `data/universe.json`
  (every coin's rows, columnar, 15 MB) so the Compare tab and the all-coins calendar have a
  universe scope with every book and every filter; the universe figures agree with the engine's
  CSV in pandas to the printed precision (returns stored to three decimals); the magnet ray is
  back as a magnet mode that drops the library's own Horizontal Line at the nearest open / high /
  low / close (saved, moved and erased with the other drawings; proven exact on BTC 03-25);
  `test_domino_viewer` reads the calendar functions from `core.js`. Ruff clean, 372 passed, 2
  skipped.

### Context for next session

- The viewer is `analysis/domino/viewer/`: `uv run python -m analysis.domino.trade_viewer serve`
  (port 8765, opens the browser); from the laptop, `serve --no-open` on the desktop and
  `ssh -L 8765:127.0.0.1:8765 <desktop>` then `http://127.0.0.1:8765/`; on a machine without
  `viewer/data/`, `build --as-of 2026-10-10` first (and `hourly --as-of 2026-10-10 all` for the
  1H view, ~9 min). `build` also vendors amCharts and writes the universe table.
- The page reads rows and never computes them; `core.js` holds the TVB-39 row logic as it was,
  so the TVB-39 audit's viewer findings (F4 the reconstructed fill price as an exact touch
  threshold with a first-candle fallback, F5 the reference stop exit drawn at the end of the
  day, F6 the silent book-C fallback when the selected book has no result, F7 the stack class
  label) carry over to this page until they are adjudicated.
- Drawings live in browser storage per coin and pane (`am5-stock-domino-<coin>-drawings`,
  `...-<coin>-b-drawings`); the retired page's rays (`domino-viewer-rays:<coin>`) are not read.
- `proto_codex/` is untracked and untouched; `User_Notes.md` stays untracked.
- HANDOFF.md is over the 1,500-line limit at close (1,556 lines); archiving waits for the
  owner's word.

### Files created/modified

- `analysis/domino/viewer/`: `index.html`, `app.js`, `core.js`, `story.js`, `stats.js` (the
  page), `NOTES.md` (its receipt), `shots/` (17 PNGs); the TVB-39 `index.html` / `app.js` removed
- `analysis/domino/trade_viewer.py` (amCharts vendor fetch with a browser-like agent,
  `universe_table`, docstring)
- `tests/test_domino_viewer.py` (reads the calendar functions from `core.js`)
- `analysis/domino/MANAGE_RECEIPT.md` (viewer section: the promotion paragraph)
- `.gitignore` (the proto_claude vendor line removed; `proto_codex/vendor/` ignored)
- `docs/HANDOFF.md`, `docs/reviews/REVIEW_REQUEST.md`, `.session_startup_prompt.md`
- `docs/reviews/tvb39-codex-audit.md` committed as returned (captured 2026-10-14; the
  synthesis is the next session's first item)

### Open

- [ ] TVB-39 Codex audit synthesis: F1 HIGH (the hourly entry accepts equality and can exit
      before the trade exists), F2-F8 MEDIUM; agree / dispute / act in HANDOFF, fold, rerun
      `manage` if the engine changes, then `trade_viewer build`
- [ ] The with-trend inside break's T1 STOP-and-ASK (the owner rules; amendment A3 before code)
- [ ] Viewer: a journal layer (a note and a one-tap verdict per row, on the calendar and the table)
- [ ] Viewer: one drawing slot across both panes; the retired page's rays imported once
- [ ] Viewer: an hourly archive beyond the venue's ~208 days
- [ ] HANDOFF.md archive (over the limit; the owner's word)
- [ ] `proto_codex/` disposition (delete, or keep for ideas; the owner's call)

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb40-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED 2026-10-29 (`docs/reviews/tvb40-codex-audit.md`, NEEDS-CHANGES, six MEDIUM, all display / readback; synthesis pending)
- Commits to review: `9f6c5c8..2c7fe1c` on `main` (9f6c5c8 is the pre-session sha, so the
  range holds e79f8d3 round one, da7f4c2 round two and 2c7fe1c the promotion; it also contains
  the two maintenance pull requests merged 2026-10-16 (45f83fc, 2dde483, 706cb3d, 46de307:
  cloud hooks and the safety guard, with their own HANDOFF entries), which are not viewer
  work; the session-end docs commit after 2c7fe1c is docs only). Sanity-check:
  `git diff --name-status 9f6c5c8..2c7fe1c` lists every file the session touched.
- Scope / what changed: a new viewer page on amCharts 5 (five files, a receipt, proof shots),
  the build script's vendor fetch and universe table, one test path, the receipt's viewer
  paragraph. No engine, prereg or results change.
- Focus areas (scrutinize these): the founding rule (`core.js` `settle` / `tradeSpan` /
  `stackLevels` / `setupDays` against the TVB-39 `app.js` and the row semantics, including the
  TVB-39 audit's F5-F7, which this page inherits); `stats.js` arithmetic (drawdown order,
  target and days semantics per book, histogram bins) against `manage.py`; `story.js` claims
  per book against the row columns (`hit_X`, `days_X`, `out5`, `exit_k_u`, the exit-day test,
  the Monday one-test case) and the closed-bar chip definition (R10, closed bars only);
  `universe_table` (code books, -1 sentinels, three-decimal rounding, day numbers) and its
  decoding in `fromUniverse`; the magnet's coordinate math (`toAxisPosition` over
  `axisLength`) and the proof flag; the Playbook's receipt numbers; hygiene (vendor and data
  gitignored, the CDN agent string, no private link in the repo, `proto_codex/` untracked).
- Reviewed by: Codex (local, via SSH), 2026-10-29
- Findings: F1 Compare drawdown measured row by row instead of on daily sums (engine does daily); F2 magnet picks the next candle on the right half of a candle; F3 exit narration: hourly clock worded long-only on 27,674 short rows, open rows told they "left with the daily clock", same-day stop / one-R ties told "before one R"; F4 best / worst travel is book C's window whatever book is selected; F5 calendar month average divides by all rows, censored rows count as zero; F6 changing the book does not re-sort the table. All six confirmed against the source on receipt; synthesis + repairs with the TVB-39 viewer findings F4-F7.

---

## Session TVB-39: the trade viewer (every row on its own candles, locally) and the lead's five candidates run as prereg amendment A2 (COMPLETE)

**Date:** 2026-10-12
**Status:** COMPLETE -- two pieces on the owner's word of 2026-10-12: "You may run your 'would
test next'", and a request to start implementing a local chart tool so the rows can be checked
visually without TradingView ("visually verifying via TradingView is one of the most time
consuming tasks, almost impossible to accurately do ... the numbers were there and seemed right
until visually verified, which showed inaccuracies"), styled like the owner's screenshot (grey
context candles, the trade's candles coloured, opened / closed lines, a strip of trade cards,
1H / 1D / 1W / 1M toggles). Both delivered, pushed. The owner began their own pass the same
evening on the viewer (two BTC trades walked, section below): three viewer additions and one
viewer bug fix came out of it, plus one STRAT STOP-and-ASK question (the with-trend inside
break's T1) that is OPEN, and two direction signals from the owner recorded below (the
daily-close exit is likely to be retired; higher-timeframe inside bars are the hazard the domino
test was meant to answer). Nothing is promoted; nothing is read into the hierarchy rulings.

### What was accomplished

- **The trade viewer** (`analysis/domino/trade_viewer.py` + `analysis/domino/viewer/`): a local
  page served on localhost that draws the management book's recorded rows on the census's raw
  candles. It re-runs NO trade logic: the entry day, targets, touch days, exit day and every
  book's fill come off `manage_trades.csv.gz` as the engine wrote them, so a chart that
  disagrees with a row is evidence against the engine. One coin at a time or every trade
  entered on one day across coins; 1H / 1D / 1W / 1M (weeks and months bucketed by the census's
  calendar rules, tested against `census.week_start` / `month_start` through node); candles not
  in a trade grey, the setup bar amber, the bar before it dark amber, the trade's candles green /
  red by close; lines for the entry level, the exit close, T1 / T2 / T3 with sources, one R, the
  setup-bar stop, the measured move; markers on the first bar (hour, on the hourly view) that
  touched each price; the exit day's test spelled out (close against the day's open and the
  week's open, with colours); every book's fill; the two A2 exits (under water on the daily,
  the hourly clock on the hourly view); filters (unit timeframe, kind, side, liquid, has T1),
  book and equal-size selectors for the printed P/L; arrow keys; bookmarkable addresses
  (`#coin=BTC&date=2025-06-17&tf=D&dir=down&view=1D`, the receipt's worked example). On the
  owner's first pass (BTC 2026-03-27 weekly short: "we hit T1, no exit") three additions and
  one fix, same day: the book box now drives the chart (candles, closed line and out arrow at
  the selected book's own settle day and fill, read off the row; the headline clock kept as a
  small square); every timeframe that broke the same day is drawn with the gap band and a
  "domino" label on a converged stack (the chart's calendar level checked equal to every row's
  recorded level, all 179,498 units); a magnet ray tool (Draw / R, snaps to the bar's OHLC on
  the active view, persists across timeframes per coin); and the misplaced "data ends" marker
  (the A2 markers had split the exit arrow's `if` from its `else`) fixed. `serve` takes
  `--host` and `--no-open` for the owner's laptop over SSH / Tailscale. Hourly
  candles fetched for all 292 coins (the venue serves ~208 days) into the census cache, stamped.
  Recipe in the receipt's viewer section: `hourly --as-of ... all` (once), `build --as-of ...`,
  `serve`. The data folder and the vendored chart library are gitignored and regenerable.
- **Prereg amendment A2, declared before code (f505f9d):** the five candidates restated in
  trader terms, each one change on the same trades, with readings R1-R5 and vectors v16-v19
  written first. One sentence was corrected while writing v17, labelled in the prereg: a target
  on the trade's side cannot be touched before the level, so the hourly ordering difference is
  on the EXIT day (the daily bar fills any touch that day, the hourly clock only up to the exit
  hour).
- **Engine (`manage.py`):** the under-water exit recorded on the same walk (`exit_u`, books
  C_u / A_u / D_u); the hourly clock (`walk_hourly`: entry hour = first hour reaching L; exit =
  first hour closing against its own open AND the day's open; cap = the last hour of day 20;
  censored when the hours end; books C_h / A_h / D_h) on the hourly-window subset; book E and
  the fees as arithmetic on the recorded columns; the week's side as a split of every book.
  Hourly helpers (`fetch_hourly`, `cached_hourly`, `normalize_hourly`, `HOUR`) live in
  `census.py`. `candidates()` + `table_candidates()`; `manage.json` carries a `candidates`
  block; the CSV carries the new columns. Offline rerun as before (`--as-of 2026-10-10`, ~10
  min with the hourly). Headline numbers did not move (same rows, same walk; the hourly and
  under-water columns are additions).
- **Receipt** (`MANAGE_RECEIPT.md`): a viewer section and an A2 section (what each candidate
  did, in trader terms, against its declared reading). **Ledger** card extended. **Page**
  republished (version 5) with a candidates section. 23 manage vectors + 7 A2 vectors + 4
  viewer tests; full suite green.

### The five, against their declared readings (plain daily, the book cohort)

- **R1 the week's side at entry: NOT a general condition.** With beats against on the reversal,
  the continuation and the outside break (reversal C +0.28 with / +0.13 against; continuation
  C -0.20 / -0.53), but the inside break pays MORE against the week (A +0.18 / C +0.16 / D +0.38
  against; -0.07 / -0.13 / +0.16 with) and reaches T1 nearly as often. The declared rule said
  one reversal of the split means it is not a condition. An inside-bar break against the week is
  a counter-trend break with the week's open ahead as a level: a pattern-specific read.
- **R2 the hourly clock: a different trade, not a better one.** On ~38k trades inside the
  hourly window: held 9-11 hours against 48-72; every trade exits inside the cap; losers shrink
  to less than half (-1.5..-1.9 against -3.8..-4.9); T1 before the exit falls by a third to a
  half. Net paired (rerun 2026-10-30 under the repaired walker, TVB-39 audit F1-F3; the
  original read -0.14 / 0.00 / +0.21 / -0.27): C_h - C reversal -0.12 [-0.26, +0.03],
  continuation 0.00, inside +0.23 [+0.06, +0.40], outside -0.26 [-0.58, +0.06]; A and D within
  about a tenth. The declared expectations (sooner, smaller losers, fewer targets) all held; no
  sign was predicted.
- **R3 half at T1: holds.** E between A and C on every kind (reversal -0.05 / +0.09 / +0.22).
- **R4 fees: three lines survive.** Two taker fills cost 0.077-0.082 per trade; net of that,
  intervals clear of zero: reversal C +0.14 [+0.02, +0.27]; inside D +0.16 [+0.08, +0.23] and
  D5 +0.16 [+0.09, +0.24]. Six lines are negative net with the interval clear: reversal A -0.13
  [-0.18, -0.08]; continuation A -0.31, B -0.32, C -0.32, E -0.32; inside B -0.15 [-0.27, -0.02].
  The rest flat net; the reference -0.35..-0.92 net. (Corrected 2026-10-30 per the TVB-39 audit
  F8; this line previously called everything else flat.)
- **R5 under water: the lead was wrong.** The lead called C_u < C (holds longer, loses more).
  Holding time is the same (median 2-4 days), the tail a little fatter (44-57% past one R
  against 42-54%), and the exit-only book loses LESS or the same: C_u - C +0.20 [+0.09, +0.32]
  on the continuation, +0.04 / +0.04 / +0.23 elsewhere; A slips a few hundredths; D unchanged.
  On the continuation a red candle above the entry is not evidence against the trade.

### The owner's first pass on the viewer (same evening; two BTC trades)

**Trade 1, BTC 2026-03-27 weekly reversal short, "we hit T1, no exit; a second trip through
T1, no exit; hard to tell which level is the domino level".** The row was right; the viewer was
the problem. The book box was on C (exit only, no target by rule) and the "Position closed"
line was hard-wired to the headline exit whatever the box said; the trade's only level drawn
was its own weekly trigger, and "spread D+W" (the daily trigger broke the same day more than 1%
away) was printed as a chip, not drawn. Fixed the same evening (7f3fc88): the book box now
drives the chart (candles to the selected book's own settle day, the closed line at that
book's fill read off the row's return, the out arrow on the bar that touched the target when
the book took one, the headline clock kept as a small square); every timeframe the row says
broke that day is drawn, with a stack line in the details (each trigger's price, the gap, the
census band) and a "domino" label on a converged stack; the chart's previous-complete-bar
level was checked equal to the recorded entry level on all 179,498 rows (no mismatch); a magnet
ray tool (the owner's TradingView habit: a one-pixel blue line at 70% opacity snapped to the
bar's open / high / low / close, kept across the timeframe toggles per coin, moved by clicking
near it on a faster view); `&book=` in the address. One viewer bug found on the owner's
screenshot: the A2 markers had been spliced between the exit arrow's `if` and its `else`, so a
"data ends" square printed on every exited trade. Also `serve --host / --no-open` (ed08ae5) so
the owner can browse the viewer from their laptop over an SSH port forward or the tailnet.

**Trade 2, BTC 2026-03-25 daily inside break long, -6.99% in two days, "a 2D week and an
inside month, a recipe for disaster, yet it hit its daily target, and a weekly target on the
upside on a 2D week?"** Checked against the candles:

- The week was NOT 2D at entry: through 03-24 the week of 03-23 ran 67,404-71,785 inside the
  prior week's 67,313-75,972, with price above the week's open at 67,831 (the row's "week
  with"). It went 2D on 03-27, the exit day. The 2D week is hindsight.
- The month was inside (March 65,000-75,972 inside February's 60,000-79,417). The engine reads
  neither the month nor the week's bar type; it takes every daily break by design, and the
  only week read is its colour at entry (A2.1).
- T1 75,972 [W] is last week's high, the first unbroken weekly level above the entry: a level
  from the ladder, not the week's direction.
- The owner's "daily target" at 71,785 is the mother bar's high (03-23, a 2U). It was hit on
  the entry day (high 72,034); book A would have left at +0.56%. **Code-versus-skill drift,
  STOP-and-ASK raised, OPEN:** the prereg's definition says a with-trend inside break has no
  magnitude of its own and takes the first weekly / monthly rung (`anchor = ladder`); the
  strat-methodology skill's rulings R14 / R18 say unfilled structure containing the trigger is
  a real structural magnitude, and the 2U mother bar's far side contains this trigger. The
  owner's ruling decides; any change is prereg amendment A3 BEFORE code (rerun ~10 min). The
  question put to the owner: "Mother bar's far side as T1 for the with-trend inside break:
  amend?" Not answered this session.
- Why -6.99%: 03-26 closed red on the day but above the week's open, so the two-test exit did
  not fire; 03-27 closed below both, out at 66,396. The week-colour test let it ride through a
  3.6% red day; the setup-bar stop (68,904, the inside bar's low) would have cost 3.48%.
- Feed note: the venue API prints the inside bar's high at 71,385, TradingView at 71,387.

**The owner's closing words, as direction (not rulings):** the trade is "the danger of trading
lower timeframes when you have higher timeframes as inside bars", which is "why we tried to go
with the domino test" (the coincident-level event, TVB-37); "I think the daily exit close also
is going to be thrown out, the amount of trades this affects is pretty ridiculous"; more trade
reviews to come ("it does take time"); "we are making progress ... still some bugs to work
out". The owner's first pass is BEGUN, not finished.

### What the lead would say next (not done; the owner decides)

- The with-trend inside break's T1 is the first amendment candidate (A3): the mother bar's far
  side per the skill, against the prereg's ladder. The viewer should draw the mother bar's far
  side on every inside break so the owner can see the skill's reading trade by trade before
  ruling.
- If the daily-close exit is retired, the replacements are already measured on the same rows:
  under water (A2.5, loses less or the same), the hourly clock (A2.2, a different trade, flat
  net), the own-bar clock (fork 2, holds longer and loses more), the chance book's setup-bar
  stop (the reference). The owner picks; prereg before any rerun; no pick-the-winner.
- The owner's hazard (higher-timeframe inside bars around a lower-timeframe entry) is a
  context split the rows can already carry: the week's and month's bar type at entry (inside /
  2 with / 2 against / 3) as a declared split of every book, like A2.1 did for the week's
  colour. A one-line amendment if the owner wants it.
- The headline's "against" is the weaker reading on the continuation (A2.5); the week's side
  belongs to the reversal and the continuation (A2.1).

### Files created/modified

- New: `analysis/domino/trade_viewer.py`, `analysis/domino/viewer/{index.html,app.js}`,
  `tests/test_domino_viewer.py`, `tests/test_domino_manage_a2.py`.
- Modified: `analysis/domino/{manage.py,census.py,chart_page.py,MANAGE_RECEIPT.md}`,
  `results/{manage.json,manage_tables.md}` (+ the gitignored CSV / log / viewer data),
  `docs/experiments/tvb37_management_book_prereg.md` (A2), `docs/ARM_LEDGER.md`, `.gitignore`,
  `docs/reviews/REVIEW_REQUEST.md`, `.session_startup_prompt.md`, this file.
- Commits: dbeaffe (viewer), f505f9d (A2 prereg), 340c86e (A2 build), ed08ae5 (serve flags),
  7f3fc88 (viewer: book box, same-day triggers, ray tool, marker fix), then the close-out.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb39-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED (docs/reviews/tvb39-codex-audit.md, captured 2026-10-14; critical synthesis pending)
- Commits to review: `4dc5f6b..30391fb` on `main` (4dc5f6b is the pre-session sha; the range
  is dbeaffe, f505f9d, 340c86e, ed08ae5, 7f3fc88, 30391fb close-out; the sha-pin commit after
  it is docs only). Sanity-check: `git diff --name-status 4dc5f6b..30391fb` lists every file
  above (verified at pin time: 16 source / doc files plus the gitignore).
- Scope / what changed: the trade viewer (a static page + a build / hourly / serve CLI that
  draws recorded rows on cached candles and claims to re-run no trade logic) and prereg
  amendment A2 in `manage.py` / `census.py` (the under-water exit on the shared walk, the
  hourly clock on the hourly window, book E and fees as arithmetic, the week's side as a
  split, `candidates()` and its tables / page section).
- Focus areas (scrutinize these): `walk_hourly` (entry hour = first hour reaching L, exit =
  first hour closing against its own open AND the day's open, cap = the last hour of day 20,
  censoring when the hours end; the ordering claim that a target cannot be touched before
  the entry hour and the exit-day difference); `exit_u` sharing the headline `walk()` without
  changing it (headline numbers byte-identical: 179,498 units, same tables); book E and the fee
  arithmetic against the prereg's A2.3 / A2.4 definitions; the viewer's calendar bucketing
  (`weekStart` / `monthStart` against `census.week_start` / `month_start`), its `settle()`
  (the fill = level moved by the recorded return; is that always the engine's own price?),
  `stackLevels()` (previous complete bar's extreme per stack timeframe; checked equal to every
  row's `level` for its own timeframe) and the claim of re-running no trade logic; the "data
  ends" marker fix.
- Reviewed by: Codex, local source review + offline replay, 2026-10-14
- Findings: {blank until docs/reviews/tvb39-codex-audit.md exists}

### Open

- [ ] The owner's own pass over the management book on the viewer (BEGUN 2026-10-12 evening,
      two BTC trades; continues) before anything is read into the hierarchy rulings.
- [ ] STOP-and-ASK, open: the with-trend inside break's T1 (the mother bar's far side per
      skill R14 / R18, against the prereg's weekly / monthly ladder). The owner rules; prereg
      amendment A3 BEFORE code; rerun ~10 min.
- [ ] The owner's signal that the daily-close exit "is going to be thrown out": a declared
      replacement (prereg) before any rerun. Already measured on the same rows: under water
      (A2.5), the hourly clock (A2.2), the own-bar clock (fork 2), the setup-bar stop
      (reference).
- [ ] Viewer: draw the mother bar's far side on every inside break; optionally the week's and
      month's bar type at entry as chips (the owner's hazard).
- [ ] Codex review of `4dc5f6b..HEAD` (block above): REQUESTED at session end.
- [ ] The hierarchy rulings the owner deferred (stop owner in a stack, continuation ranking,
      seat competition, which higher-timeframe event ends a trade).
- [x] HANDOFF is over the 1,500-line limit (2,100+; TVB-33..34 are the next archive
      candidates): archiving asks the owner. CLOSED 2026-10-14 (after the TVB-39
      close-out, on the owner's word): TVB-33..35 archived verbatim to
      docs/session_archive/HANDOFF_TVB33-TVB35.md (TVB-33..34 alone left ~1,640
      lines; the three make the round-3 arc); HANDOFF now ~1,420 lines.
- [ ] Executor repairs owed before any real-money restart (TVB-31..35 syntheses); fresh
      wallet; scanner STRAT rulings; the carried list in the TVB-37 entry.

---
