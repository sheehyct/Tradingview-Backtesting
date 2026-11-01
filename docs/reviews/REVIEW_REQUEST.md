# CURRENT REVIEW REQUEST -- tradingview-backtesting

> Entry point for external reviewers. If you are Codex (`/session-review`) or any other
> external review agent pointed at this repo: this file is your work order. It
> always describes the LATEST requested session review and is rewritten by
> `/session-end` each session. The permanent per-session record is the
> `### External Review` block in `docs/HANDOFF.md`; for the CURRENT request,
> this file wins if the two disagree. Full contract:
> `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Status

- Status: REQUESTED
  <!-- REQUESTED | RETURNED (audit file written) | ADDRESSED | N/A -->
- Session under review: TVB-42 (2026-10-31 to 2026-11-01) -- the TVB-41 Codex audit folded (two
  MEDIUM: book D5's story sentence, the rerun prose); the run and trade-card contract
  (`analysis/domino/viewer/CONTRACT.md`, designed with the owner and confirmed before code) built
  through stage 2: `analysis/domino/contract.py` (validate in plain words, derive index / dates /
  universe, import a folder / single file / zip, `runs.json`), `analysis/domino/run_export.py`
  (the management book's rows as cards, 17 books per card; `check_run` against the flat page data:
  179,498 cards, no differences), four `trade_viewer` subcommands, and the page rewritten to read
  runs (a run picker; `core.js` run registry with roles / groups / colours; `prep` deriving day
  offsets from the card's times against the run's bars; story / ladder / markers / Compare from
  the card's book entries; no engine column name left in any page module). The cc-menu repair
  is outside the repo.
- Requested: 2026-11-01
- Write the audit to: `docs/reviews/tvb42-codex-audit.md` (copy `docs/reviews/_TEMPLATE.md`)
- Note: the TVB-41 audit's two findings are ADDRESSED in the TVB-42 HANDOFF entry; check that the
  repairs do what the entry says, do not re-find them.

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `{pending push}` (2f3a3a8 is the TVB-41 close-out the session started from; 75626b7 the audit fold; bc79aa4 the contract spec; cba482e stage 1; ef5be09 stage 2; the close-out commit after it is docs only). Verify with `git diff --name-status 2f3a3a8..HEAD`. |

No sibling-repo commits. The viewer's data folder (`analysis/domino/viewer/data/`, the runs
included) and the vendored chart library are gitignored; `uv run python -m
analysis.domino.trade_viewer export-run --as-of 2026-10-10` (about three minutes) regenerates run
one from `analysis/domino/results/manage_trades.csv.gz` and the cached `*_1d_20261010.json` /
`*_1h_20261010.json` candles on the owner's machine; `trade_viewer check-run
management-book-20261010` compares it with the flat page data (`trade_viewer build --as-of
2026-10-10` writes that, if absent). The owner's cc menu scripts are out of scope.

## What to read first

1. `docs/HANDOFF.md` TVB-42 entry: the audit synthesis, the contract's design (the owner's three
   choices and the import ask), stage 1 and stage 2 with their verification.
2. `analysis/domino/viewer/CONTRACT.md`: the shape (sections 2-7), the mapping (section 9), what
   the stages settled (section 12).
3. `analysis/domino/run_export.py` (`card_from_row`, `check_run`) beside
   `analysis/domino/manage.py` (the caller block that writes the row fields, about lines 560-810).
4. `analysis/domino/contract.py` (`validate_run`, `validate_file`, `Derive`, `load_source`,
   `import_run`).
5. `analysis/domino/viewer/core.js` (`setRun`, `prep`, `settle`), `story.js` (`bookWords`,
   `clockWords`, `otherClocks`), `stats.js` (`fromUniverse`), `app.js` (`loadRun`, `drawPane`'s
   markers, `hourEntry`).
6. `tests/test_domino_contract.py`, `tests/test_domino_viewer_js.py`,
   `analysis/domino/viewer/NOTES.md` ("stage 1", "stage 2").

## Focus areas

- **The mapping (`card_from_row`) against the engine's columns**, especially the clock variants
  (`C_u` / `C_own` / `C_long` and their A / D books, `reached1_own` / `reached1_long` as `hit`),
  the measured-move book, `days_ref` for the chance book's `at`, and the hourly books' `entry` /
  `at` (the day-resolution one-R fill recorded at the latest time known to be at or before it,
  marked `resolution: day`). Is any card field a fabrication rather than a reading of the row?
- **`check_run`'s coverage**: it compares the six ladder books' returns and hits, the headline's /
  D5's / chance book's reason and day, T1's price and touch day, one R's touch day and the hourly
  clock; it does NOT compare the clock variants' days or the A / D variants' fills. Is the
  "no differences" claim stated with those limits everywhere it is quoted?
- **The universe table's hit convention** (null where a book has no target; the engine wrote
  False): stated in NOTES.md and the HANDOFF; does the page's "at target" share change meaning
  anywhere because of it?
- **`prep`'s day offsets**: bar index when the time's day is in the bars, calendar arithmetic
  otherwise; any card whose exit day is missing from the daily bars would get a calendar offset
  (does that happen on run one, and does the marker code tolerate it?).
- **`settle`**: `at` (the touch price) only for target / one_r / stop; a cap mark carries the
  recovered price; `res` from the entry's own resolution first.
- **The story's `pre` sentence** for a target book that left by the clock: "was only touched on
  day k, after the exit" when the touch is after the exit, "was not touched before the exit"
  otherwise; could a card have a touch at or before the exit with `hit` false?
- **The validator against the spec** (CONTRACT.md sections 3 and 5): the `at` / `price` / `ret`
  rules per `how`, `entry <= at`, the target-fill rule ("a target touched by then"), the
  single-file split, the zip path, the in-place import (files read before rewritten), the
  200-problem cutoff.
- **The page's run switch**: Compare charts disposed and rebuilt; `state.book` kept only when the
  new run declares it; the unit filter rebuilt from `run.units` (and re-wired).
- **Markers**: the hourly pane's entry arrow from `hourEntry` (the selected book's `entry`, else
  the first hour-resolution book's), the hour-resolution exit on its recorded hour, the group
  squares (the first book of each group), the stop branch's arrow direction.
- **Hygiene**: ruff clean; 471 passed, 2 skipped; no secrets; no private link; data and vendor
  gitignored; `proto_codex/` and `User_Notes.md` untracked.

## What is NOT in scope

The TVB-41 audit's findings themselves (adjudicated in the TVB-42 entry); the STRAT ML vessel;
the owner's cc menu scripts; stage 3 (not built); the inside-break T1 question (the owner's
ruling is pending); the engine (`manage.py` is untouched this session).
