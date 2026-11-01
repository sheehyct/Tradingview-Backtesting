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
- Session under review: TVB-43 (2026-11-01) -- the TVB-42 audit folded in code (F1-F8) with an
  in-session Codex pass on the repairs (2 HIGH, 5 MEDIUM, all folded before the commit); stage 3
  of the viewer contract (the flat layout, `build` and `check-run` deleted; Compare across runs
  by role; the example single-file run imported and verified in Chrome); the page made ready for
  session-day runs (`clock.label_shift_hours`, `clock.calendar`, `cal.sessionOf`, label-date
  buckets, shipped `1w` / `1M` bars, bar offsets in the universe table); the bench prereg DRAFT.
- Requested: 2026-11-01
- Write the audit to: `docs/reviews/tvb43-codex-audit.md` (copy `docs/reviews/_TEMPLATE.md`)
- Note: the TVB-42 audit's eight findings and the in-session pass's seven are ADDRESSED in the
  TVB-43 HANDOFF entry; check that the repairs do what the entry says, do not re-find them.

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `8a5806c..HEAD` (8a5806c is the TVB-42 close-out the session started from; 70bacdf the audit fold; 7111720 stage 3; 4140285 the prereg draft; the close-out commit after it carries the session-calendar page support and the docs). Verify with `git diff --name-status 8a5806c..HEAD`. |

No sibling-repo commits. The viewer's data folder (`analysis/domino/viewer/data/`, the runs
included) and the vendored chart library are gitignored; `uv run python -m
analysis.domino.trade_viewer export-run --as-of 2026-10-10` (about three minutes) regenerates run
one; `trade_viewer import analysis/domino/viewer/examples/single_file_run.json` imports the
example run. The ES Databento cache lives in `vectorbt-workspace/data/databento_cache/` and is
read-only for this review (nothing in this range reads it in code yet).

## What to read first

1. `docs/HANDOFF.md` TVB-43 entry: both syntheses, stage 3, the session-calendar page work, the
   bench draft's data facts.
2. `analysis/domino/contract.py`: `_slug`, `_fname`, `_plain_name`, `_split_single`,
   `load_source` (inline routing), `recover`, `import_run` (staging and swap), `register`,
   `Derive` (`_extras` backfill, the label shift, `session()` and bar offsets).
3. `analysis/domino/viewer/core.js` (`setRun`'s shift and calendar, `aggregate`, `makeCalendar`,
   `prep`), `story.js` (`relWord` / `colourWord`, `clockWords`), `stats.js` (`bookStats`'s
   target fields, `roleRows`), `app.js` (`getJson`, `loadRun`, `loadUniverse`, `loadCoin`,
   `applyDate`, `select`, `loadOther`, `renderByRole`, `fillRunCompare`).
4. `tests/test_domino_contract.py`, `tests/test_domino_viewer_js.py`, `tests/test_domino_viewer.py`.
5. `analysis/domino/viewer/CONTRACT.md` (sections 4, 6, 7, 12), `NOTES.md` ("stage 3"),
   `docs/experiments/tvb43_bench_prereg.md`.

## Focus areas

- **The staged import on Windows**: `dest.rename(old)` and `stage.rename(dest)` while the viewer
  serves the folder (open handles); `recover`'s parse of `.old-<id>-<stamp>` for ids that hold
  dashes; two imports of the same id at once (out of scope: say so if it is not handled, do not
  design for it); the in-place import from `<dest>/run.json` reading before the swap.
- **Names**: anything that still folds two accepted ids or two instrument names onto one path
  (unicode case folding, trailing spaces, NTFS alternate data streams, long paths).
- **`cal.sessionOf` and the label shift**: for a 00:00 UTC run nothing may move. The audits'
  named rows on run one (ATOM 2026-05-09 D one R on day 2; ACE 2026-04-29 hourly enters 02:00
  and leaves 03:00, "1 hour after its entry hour"; BTC 2026-03-16 W chance book stopped on day
  11; BLUR 2026-07-24 W D5 on day 24 past the headline's day-20 cap) should read as in the
  TVB-42 entry. For a Globex shape: a Friday-to-Monday hold is one bar; an hour after midnight
  UTC stays with its session; a time inside a missing day now maps to the previous bar rather
  than to calendar arithmetic (is that the right reading for the page?).
- **`Derive`'s bar offsets** against the page's k on run one (the `:days` columns changed from
  calendar days to bar offsets; which coins have gaps in their daily bars, and does the universe
  median-days figure move?).
- **Compare across runs by role**: the unit-filter rule when the other run's units differ; the
  dashed curve on a shared axis; `loadOther`'s generation guard; `fillRunCompare` after a run
  switch; `state.other` cleared when the other run becomes the current run.
- **The clock prose**: `relWord` / `colourWord` and the hourly "with the day ... at that hour"
  reading on real cards (0G 2025-10-01 C_u; 0G 2026-03-19 C_h, the audit's examples).
- **The bench prereg draft against the charter**: declared variants and no promotion; the
  engine change gated by the byte-identical crypto regression; anything that reads as a tuned
  choice rather than a structural one.
- **Hygiene**: ruff clean; 500 passed, 2 skipped; no secrets; no private link; data and vendor
  gitignored; `proto_codex/` and `User_Notes.md` untracked.

## What is NOT in scope

The TVB-42 audit's findings and the in-session pass's findings themselves (adjudicated in the
TVB-43 entry); the engine (`manage.py`, `census.py`, `chance.py` are untouched this session); the
bench build (not started; the prereg awaits the owner); the STRAT ML vessel; the owner's cc menu.
