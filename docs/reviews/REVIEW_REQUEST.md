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
- Session under review: TVB-44 (2026-11-02) -- the TVB-43 audit folded IN CODE the same
  session (F1 HIGH gap-through entries: the owner ruled the declared comparison as a pair,
  open-fill and missed-entry, prereg section 9, built in the runner with no engine change; F2
  the staged export; F3 the comparison restart on a run switch; F4 the roll flag named as the
  headline window with `roll_ref` beside it; F5 ASCII ids; the smaller reporting items); both
  ES runs regenerated with the control rows byte-identical; `BENCH_RECEIPT.md` section 1b and
  every section re-read both ways; the ledger card; the card's gap sentence on the viewer;
  housekeeping (the prototype folder and the flat viewer files deleted on the owner's word).
  THEN the matched-pair study (`docs/experiments/tvb44_matched_pairs_prereg.md`, the twelve
  variables and the theme rule frozen by the owner before any row was read): `analysis/pairs/`
  (`features.py`, `cells.py`, `run_pairs.py`), `tests/test_pairs.py`, `analysis/pairs/results/`
  (tables and JSON), `analysis/pairs/PAIRS_RECEIPT.md`, the ledger card. An in-session Codex
  pass found ten things (prereg section 12) and all were folded before the receipt: the reach
  outcome over units WITH a target and "has a target" read beside it, liquidity withdrawn, the
  month side of weekly / monthly units from the unit's own trigger, `r_pct` as the expansion
  numerator, venue-era bars, the ladder's depth and the nearest level's timeframe, "other"
  cells shown. Three themes by the rule (late entry; an expanded setup bar; room to T1, a
  construction): the receipt's claims are in scope; do not re-find the ten.
- Requested: 2026-11-02
- Write the audit to: `docs/reviews/tvb44-codex-audit.md` (copy `docs/reviews/_TEMPLATE.md`)
- Note: the TVB-43 audit's findings are ADDRESSED in the TVB-44 HANDOFF entry (every one
  confirmed independently, none disputed); check that the repairs do what the entry says, do
  not re-find them. An in-session Codex pass ran on the diff before the commit; its findings
  and their fold are in the same entry.

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `5ee9b84..099025c` (5ee9b84 is the TVB-43 close-out pin the session started from; 099025c carries the whole session's work in one commit; the docs-only pin commit after it names this range). Verify with `git diff --name-status 5ee9b84..099025c`. |

No sibling-repo commits. The viewer's data folder (`analysis/domino/viewer/data/`, the runs
included) and the vendored chart library are gitignored; `uv run python -m
analysis.bench.run_bench --variant globex` (and `rth`) rebuilds runs two and three in about
fifteen seconds each from the ES Databento cache in `vectorbt-workspace/data/databento_cache/`
(read-only; `BENCH_CACHE` overrides the path) and regenerates `analysis/bench/results/`. The
byte-identical gate: `uv run python -m analysis.domino.manage --as-of 2026-10-10` (about 90 s)
then `git diff --stat -- analysis/domino/results/manage.json analysis/domino/results/manage_tables.md`
must be empty (it was, after this session's `manage.py` change).

## What to read first

1. `docs/HANDOFF.md` TVB-44 entry: the synthesis of the TVB-43 audit, the entry-fill readings,
   the in-session pass.
2. `docs/experiments/tvb43_bench_prereg.md` section 9 (the amendment: the rule the code implements).
3. `analysis/bench/run_bench.py`: `gap_flags`, `_hit`, `open_fill`, `_at_entry`, `fill_blocks`,
   `table_fill`, `roll_flags` (`roll_ref`), `splits`, `export_run`, `_finite`, `run_card`.
4. `analysis/bench/BENCH_RECEIPT.md` (section 1b first, then every section's "at the trigger"
   framing), `analysis/bench/results/bench_*_tables.md` (the amendment blocks at the end),
   `bench_*.json` (`gap`, `fill`, `roll_ref`).
5. `analysis/domino/contract.py` (`_plain_char`, `_slug`, `_fname`), `analysis/domino/manage.py`
   (`table_candidates`), `analysis/domino/viewer/app.js` (`loadRun` after `fillRunCompare`),
   `core.js` (`prep`: `gap`, `session_open`), `story.js` (`gapWords`).
6. `tests/test_domino_bench_runner.py`, the new tests in `tests/test_domino_contract.py` and
   `tests/test_domino_viewer_js.py`.

## Focus areas

- **The entry-fill pair against the prereg's section 9**: `gap_flags` strict and direction-aware
  (a short's gap opens below; the open AT the trigger is not a gap); `open_fill`'s exit recovery
  (`level * (1 + sign * ret / 100)`) exact for every book; the targets-behind-the-open rule for
  longs and shorts, the chance book's hit read as `out5 == "one_r"`; the under-water books
  excluded and said so; the hourly books' entry hour on a gap unit is the session's first hour
  (consistent with re-measuring from the session open); `_at_entry` agrees with `open_fill`
  row for row; non-gap units carry the control's bytes; the control rows in the regenerated
  tables byte-identical to the committed ones.
- **The receipt's section 1b and the ledger card against the tables and the JSON**: every
  number traceable; both directions with equal weight; nothing promoted; the "gap that holds /
  gap that fills" sub-split (computed from the rows, not in the tables: 1,029 / 165 units) and
  the year-by-year counts stated correctly; every other section says "at the trigger".
- **The staged export**: `.export-*` under `data` (not under `data/runs`, where `recover`
  sweeps); the importer's own staging untouched; a write failure on a rerun; an open handle
  on the destination `run.json` during a rerun (what happens to the old run and the listing).
- **The comparison restart** (`resumeOther` on both paths of `loadRun`; `loadOther`'s request
  number `state.otherReq`): any path where `state.other` stays `{loading:true}`; an older
  request for the same run can never win over a newer one; no metadata write after an await
  that a later switch could have overtaken; `init`'s `cmpRun` restore; the `cmpRun` select's
  `onchange` while a restart is in flight. The in-session pass found three gaps here and they
  were folded; look for a fourth.
- **The crypto exporter's file names** (`run_export.file_names`): two coins that map to one
  file (unicode letters to underscore; case folded) are refused before any write.
- **The roll diagnostic**: `roll` unchanged for every row (the function was restructured);
  `roll_ref` on the entry case and on censored rows; the relabeled split rows.
- **ASCII ids**: anywhere else an id or a stem is accepted (`run_export`, `trade_viewer`, the
  validator) that could still take a non-ASCII spelling the listing folds.
- **The card's gap sentence**: `gapWords` uses the trade's side words (`w.above`); run one's
  cards unchanged (no `gap` key); the sentence on a real ES card (2011-01-12 RTH long
  continuation: "opened at 1,278.50, above the trigger ... did not print at all that session").
- **The matched-pair study against its prereg**: leakage (every bar variable strictly before
  the entry session; the setup index for weekly and monthly units; bitcoin's PREVIOUS day only;
  the week position under the session calendar); the within-cell terciles and the
  cell-stratified pooled difference; the theme rule as the owner ruled it; the two themes
  recomputed from the row files; whether room-to-T1's reach reading is said to be construction
  everywhere it appears; whether the receipt reports every variable both ways and promotes
  nothing; the by-direction and by-unit splits in the receipt against the rows.
- **Hygiene**: ruff clean; 523 passed, 2 skipped; `node --check` on every viewer module; no
  secrets; no private link; data, vendor and the study's row files gitignored; `User_Notes.md`
  untracked.

## What is NOT in scope

The TVB-43 audit's findings themselves (adjudicated in the TVB-44 entry); the engine
(`manage.py` beyond `table_candidates`, `census.py`, `chance.py`, `book.py`: untouched); the
research questions the receipt leaves to the owner (which lines become arms or kill tests);
the STRAT ML vessel; the owner's cc menu; the strategy assessment the owner asked Codex for
separately (`docs/strategy-assessment-2026-11-02.md`, untracked, the owner's to read).
