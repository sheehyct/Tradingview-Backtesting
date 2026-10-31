# CURRENT REVIEW REQUEST -- tradingview-backtesting

> Entry point for external reviewers. If you are Codex (`/session-review`) or any other
> external review agent pointed at this repo: this file is your work order. It
> always describes the LATEST requested session review and is rewritten by
> `/session-end` each session. The permanent per-session record is the
> `### External Review` block in `docs/HANDOFF.md`; for the CURRENT request,
> this file wins if the two disagree. Full contract:
> `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Status

- Status: ADDRESSED (audit written 2026-10-30; verdict NEEDS-CHANGES, two MEDIUM, both repaired in TVB-42: F1 the D5
  narration appends book C's clock sentence, F2 the rerun prose claims an interval transition
  that did not happen and misses a point-estimate sign change; synthesis in the TVB-42 HANDOFF entry)
  <!-- REQUESTED | RETURNED (audit file written) | ADDRESSED | N/A -->
- Session under review: TVB-41 (2026-10-29 to 2026-10-30) -- the two outstanding Codex audits
  (TVB-39 F1-F8, TVB-40 F1-F6) adjudicated and repaired: the hourly exit clock in
  `analysis/domino/manage.py` (`walk_hourly`: strict entry, the entry day observed from 00:00
  through the entry hour, the scan bounded by the cap timestamp, a gap before the exit censors,
  hours from timestamps) with five vectors written before the change; the hourly columns and the
  A2.2 table rerun with the daily headline byte-identical; the trade viewer's four modules
  repaired on ten findings (recorded exit price for the markers, no first-candle fallback, the
  reference stop on its touch hour, the missing book named, the converged stack subset, daily
  drawdown, the magnet's cell, direction- and status-aware narration, the travel label, the
  calendar's filled denominator, re-sort on a book change) with 14 node cases; the fee prose
  corrected; the charter / CLAUDE.md / session-start framing reworded to "characterize, do not
  adjudicate" on the owner's word.
- Requested: 2026-10-30
- Write the audit to: `docs/reviews/tvb41-codex-audit.md` (copy `docs/reviews/_TEMPLATE.md`)
- Note: both earlier audits are now ADDRESSED in the TVB-41 HANDOFF entry (agree / dispute /
  act per finding). Do not re-find them; check that the repairs do what the entry says.

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `8351054..74dcb28` (8351054 is the post-cloud-merge sha the session started from: 5e71b05 commits the TVB-40 audit as returned and flips the status; 3fa6990 the viewer repairs, the F8 prose and the framing; f24a4ce the engine repair, the rerun's results, the prereg clarification, the in-session review fold and the docs; 74dcb28 the review's tail; the sha-pinning commit after it is docs only). Verify with `git diff --name-status 8351054..74dcb28`. |

No sibling-repo commits. The candle cache, the viewer's data folder and the vendored library
are gitignored; `uv run python -m analysis.domino.manage --as-of 2026-10-10` (about 10 min)
regenerates `analysis/domino/results/` from the cached `*_1d_20261010.json` and
`*_1h_20261010.json` files on the owner's machine, and `uv run python -m
analysis.domino.trade_viewer build --as-of 2026-10-10` the viewer data. The owner's cc menu
scripts (`~/Documents/WindowsPowerShell/cc-tools/`) are outside the repo and out of scope.

## What to read first

1. `docs/HANDOFF.md` TVB-41 entry: the two syntheses (what was accepted, what each repair
   claims, the byte-identical method, the rerun's deltas).
2. `analysis/domino/manage.py` `walk_hourly` (the docstring states the contract) and its
   caller (`status_h` handling, the `hourly_*` counters).
3. `tests/test_domino_manage_hourly_fix.py` (v20a-e) beside `tests/test_domino_manage_a2.py`
   (v17a-c, unchanged).
4. `analysis/domino/viewer/core.js` (`settle` with `missing` / `at` / `stop`, `stackSubset`,
   `stackWords`, `cellIndex`), `stats.js` (`maxDrawdown`, `monthSummary`), `story.js`
   (`bookWords` `noTarget`, the tie sentence, `otherClocks` colours, the stack sentence),
   `app.js` (`drawPane` markers: `near`, `putTouch`, `st.at`, the stop branch, the missing
   book; `magnetDrop`; `setBook`; the calendar footer).
5. `tests/test_domino_viewer_js.py` and `analysis/domino/viewer/NOTES.md` (the verification
   paragraph and the repairs paragraph).
6. `docs/experiments/tvb37_management_book_prereg.md` A2.2 (the dated clarification).

## Focus areas

- **The byte-identical claim.** Every non-hourly column of `manage_trades.csv.gz` (179,498
  rows) matched the pre-rerun file row for row, zero non-hourly fields of `manage.json`
  changed, and the markdown differs only in the hourly counters and the A2.2 table. The row
  file is gitignored, so reproduce the claim either from the committed `manage.json` /
  `manage_tables.md` (every non-hourly field and line identical between 3fa6990 and HEAD) or by
  checking out 3fa6990's `manage.py`, rerunning (about 10 min) and diffing the two CSVs on the
  non-hourly columns.
- **`walk_hourly` edge cases.** An entry day whose hours start at 00:00 but have a gap AFTER the
  entry hour must not be `partial_entry_day` (it is a scan gap: censored if before the exit,
  irrelevant after). `open` only when the last scanned hour is exactly the cap timestamp. A unit
  whose `cap_end` is None (the daily data ends inside the cap). The counters: `hourly_censored`
  stays zero on this snapshot; is that right given the audit found no internal gaps after
  normalisation?
- **The hourly subset's new composition.** 264 rows left as `partial_entry_day`; are any of them
  the first day of a coin's hourly window where the window started mid-day (expected) versus a
  genuine mid-history gap (unexpected)?
- **`stackSubset`.** The bands against `census.NEAR_BAND` / `WITHIN_BAND` and `chance.entry_class`
  (gap as a fraction of the daily level in the trade's direction); `plain` rows with a stack;
  weekly / monthly rows unchanged; a far level on the WRONG side of the entry (negative gap).
- **`settle`'s missing contract.** Every caller handles `ret == null` with `missing: true`:
  the ladder's `has`, the strip's Result cell, the table row title, the story, `tradeSpan`'s
  end index (the window the book would have run), the chart's "data ends" marker.
- **The markers.** `near` at one part in a billion on sub-cent coins (0G at 0.17296: is the
  cached float ever further off than that?); the stop branch for a short (the touch side);
  `st.at` for D5 when `hit_D5` and the one-R price; any marker now silently dropped.
- **The story's new sentences** against the rows: the tie wording requires `one_r_k ==
  stop_k`; the `noTarget` wording for a censored row; the hourly colours for a short.
- **The magnet on the 1M pane** (variable cell lengths) and the first / last bar.
- **Hygiene.** ruff clean; 433 passed, 2 skipped; no secrets; no private link; vendor and data
  gitignored; `proto_codex/` untracked; the charter edit keeps the author's voice.

## What is NOT in scope

The TVB-39 and TVB-40 audits' findings themselves (adjudicated in the TVB-41 entry); the STRAT
ML vessel (`analysis/strat_ml/`, its own cloud handoff and PR reviews); the owner's cc menu
scripts; the with-trend inside break's T1 question (the owner's ruling is pending).
