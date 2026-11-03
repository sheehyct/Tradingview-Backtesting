# HANDOFF -- tradingview-backtesting

> Newest session entry at the TOP. Keep under 1500 lines; archive older entries to
> `docs/session_archive/` when it grows past that.

---

## Session TVB-44: the TVB-43 audit folded in code, the entry-fill pair owner-ruled and run as a prereg amendment, the receipt and ledger re-read both ways, the card's gap label, housekeeping (COMPLETE)

**Date:** 2026-11-02
**Status:** COMPLETE. Commits on `main`, pushed: `099025c` (the audit fold, the entry-fill
pair, the receipt and ledger, the viewer, the tests), `29b9faa` (a docs pin), `c8e4a6f` (the
matched-pair study with its in-session Codex fold) and the docs-only close-out pin after it.
Suite 525 passed, 2 skipped; ruff clean; `node --check` clean; the crypto gate (`manage.py --as-of
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

### The owner's reading, and the matched-pair study (the second half of the session)

The owner opened the viewer for the first time and said so plainly: clunky to navigate, the
charts messy, the candles without their real colour context; the run names and the catalogue
of exit tweaks impossible to keep track of; not enough footing to decide anything, review
still paramount; a thought of naming the strategies on a reference card and viewing them on
the TradingView backtester again. The question the owner wanted answered: out of everything
run, is there really no correlation that says why a trade of the same pattern and continuity
went one way once and the other way another time. The honest answer given: there are
correlations, but almost all of them are known AFTER the trigger (the fill, the first hour,
the exit); the pre-entry variables tried so far do not separate, or separate the wrong way;
the study not yet done is matched pairs. The owner chose it ("if we can find correlations
about why something did something once but not at another time, it could lead to
something"), asked for a different class (bitcoin against ES) and for candle sizes before the
move. The reference card and the plain chart mode (or the TradingView route) were offered and
not yet chosen.

**Prereg first** (`docs/experiments/tvb44_matched_pairs_prereg.md`): the cell (pattern x unit
x direction x week side x month side), the outcomes (T1 reached before the exit; the exit-only
book; the one-R book as the construction check), twelve pre-entry variables, the tapes (292
coins, bitcoin alone, ES both days clean-fill first), the theme rule. The owner froze the
twelve and chose the theme rule in one message ("Freeze the twelve as drafted"; "Same direction
on crypto AND an ES day"). Built as `analysis/pairs/` (`features.py`: the variables on the
unit's own timeframe with the windows strictly before the entry session; `cells.py`: the match,
the within-cell terciles, the cell-stratified pooled difference, the theme rule;
`run_pairs.py`: the run, the tables, the JSON, the book view); `tests/test_pairs.py` (6: the
windows on hand vectors, weekly units, room / week position / the index state, a known split
recovered, the theme rule). Run in about ninety seconds; no engine change.

**The in-session Codex pass on the study (before the commit; read-only, 7 minutes through the
runtime's `status` / `result`) changed the reading, and was folded before the receipt was
written.** VERIFIED by the reviewer: every bar window strictly before the entry session (all
189,109 rows recomputed, no discrepancy), the terciles, the pooled arithmetic, the headline
differences reproduced, the card fields' provenance. DISPUTED and folded, all ten:
(1) HIGH, the reach outcome mixed "no target exists" (the engine's `t1` null, stored as not
reached) with "target not reached"; late entries lack a target far more often, and excluding
them REVERSED the travel theme on all three tapes: the reach outcome is now read over units
with a target and "has a target" is its own reading beside it; (2) HIGH, `liquid` is computed
from the snapshot's last 30 days and copied onto history: withdrawn; (3) HIGH, the engine's
`m_support` on weekly and monthly units compared the daily trigger (1,632 W + 372 M crypto
rows, 62 + 86 ES): rebuilt from the unit's own trigger (`features.month_side`), the engine's
label kept as `m_support_engine`; (4) MEDIUM, room-to-T1 is a target-definition effect and its
ES money points the other way inside the interval: said so; (5) MEDIUM, travel not uniform by
direction, unit or outcome: the splits are in the receipt; (6) MEDIUM, small cells vanished
instead of "other": shown; (7) MEDIUM, the expansion variable used the setup bar's range over
its close instead of `r_pct`: fixed; (8) MEDIUM, pre-venue index candles (3,164 units): the
bars trimmed with the engine's `venue_era`; (9) MEDIUM, `ladder_len` and `near_tf` declared but
unreported: added; `stack` excluded as outcome-side; (10) LOW, an all-missing book level read
as 0.0 and the tape's last week cannot know it is the last: the first fixed, the second named.
UNVERIFIED: clustered intervals (named as a limit). Prereg section 12 records the fold.

**The readings after the fold** (`analysis/pairs/PAIRS_RECEIPT.md`, the ledger card): three
themes by the rule, two of them saying less than their label. Late entry is first of all "no
target ahead" (the late third has a structural target 76% of the time on the 292 coins against
95% for the early third; 58% against 90% on ES), reaches the target it has slightly MORE (+2 pp
crypto, +7 to +9 pp ES) and makes less on crypto (-0.31 per trade) and the Globex day (-0.19).
An expanded setup bar reaches its target a little more on every tape (+3 to +7 pp) and on
crypto has fewer targets and makes less (-0.59; shorts -1.58, longs +0.47); ES money nil. Room
to T1 is construction on reach with crypto-only money. The candle-size answer is unchanged: a
loud run-up (-9.9 pp of reach, -0.67 per trade), a big setup bar (-1.08 per trade) and heavy
volume (-0.33) matter on the 292 coins and not on ES. New: open air (no target at all) is not
bad money on crypto (+0.38 per trade on 14% of units; ES -0.17). Crypto-only readings as
before: the shared level (+0.76), Sunday (-0.45, reach 40.8%), bitcoin's day (1.3 points of
money, no reach effect), the main dex (+0.47). Nothing anywhere: hammer or shooter on money,
the anchor beyond construction, the week's position on ES. Paths named, none run.

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
- The study: `analysis/pairs/__init__.py`, `features.py`, `cells.py`, `run_pairs.py`,
  `PAIRS_RECEIPT.md`, `results/pairs.json`, `results/pairs_tables.md` (new; the row files
  ignored), `tests/test_pairs.py` (new, 6), `docs/experiments/tvb44_matched_pairs_prereg.md`
  (new), `docs/ARM_LEDGER.md` (the study's card), `.gitignore`

### Open

- [x] The TVB-43 audit folded in code the same session; the entry-fill pair owner-ruled,
      prereg'd, built, run, received and carded; the card's gap label; housekeeping.
- [x] The matched-pair study: prereg frozen by the owner, built, run, received, carded.
- [x] The owner chose (2026-11-02): the TradingView route as the quick intermediary viewing
      surface (the plain chart mode on the viewer dropped) and the reference card, built as
      `docs/STRATEGY_CARD.md` (one screen, twelve rows, the names the owner's to change). The
      HANDOFF archived to 1,008 lines on the owner's word (`docs/session_archive/HANDOFF_TVB39-TVB40.md`).
- [ ] **The first TradingView port, on the owner's word:** the management book's headline (exit
      only C) as a parity-gated `strategy()` mirror on BTC and ES; then the hourly clock; then
      the chance book. Prereg the parity cells first; STOP-and-ASK on the bar logic.
- [ ] **The owner's reading of `analysis/pairs/PAIRS_RECEIPT.md`**: which named paths become
      declared arms ("early in the move", both tapes) or kill tests ("a loud run-up", "the
      weekend sessions", crypto); a direction-relative bitcoin variable as an amendment.
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
- Commits to review: `5ee9b84..c8e4a6f` on `main` (5ee9b84 is the TVB-43 close-out pin;
  099025c the audit fold and the entry-fill pair; 29b9faa a docs pin; c8e4a6f the matched-pair
  study with its Codex fold; the pin commit after it is docs only), as pinned in
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
  literal vertical-tab where the backslashes of `.claude-rc	rade-viewer.log` and `cc-tools
iewer.ps1`
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
