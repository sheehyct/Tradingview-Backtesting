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
- Session under review: TVB-40 (2026-10-14 to 2026-10-17) -- the charting upgrade: the trade
  viewer rebuilt on amCharts 5 as a two-builder design-off (CLAUDE `proto_claude/`, CODEX
  `proto_codex/`; the owner chose CLAUDE's) and promoted to `analysis/domino/viewer/`. The
  page keeps the viewer's founding rule (it reads the recorded rows and re-runs no trade
  logic) and adds: a calendar + sortable table rail, a facts strip, the trade narrated in
  trader language from the row, a six-book ladder per trade, a Compare tab (KPI cards,
  overlaid equity, distribution, by-setup with D5 minus the chance book) with a universe scope
  from a new columnar table, a Playbook tab, dual chart panes, the library's drawing toolbar
  with per-coin save / restore, and the magnet ray as a saved drawing. The build script
  vendors amCharts and writes the universe table. The TVB-39 page is retired.
- Requested: 2026-10-17
- Write the audit to: `docs/reviews/tvb40-codex-audit.md` (copy `docs/reviews/_TEMPLATE.md`)
- Note: the TVB-39 audit (`docs/reviews/tvb39-codex-audit.md`, RETURNED 2026-10-14,
  NEEDS-CHANGES) has NOT been synthesized yet; it is TVB-41's first item. Its viewer findings
  F4-F7 are inherited by the promoted page (same row logic in `core.js`), so this request does
  not ask for them to be found again: cite them and look for what is NEW.

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `9f6c5c8..2c7fe1c` (9f6c5c8 is the pre-session sha; the range holds e79f8d3 round one, da7f4c2 round two, 2c7fe1c the promotion. It ALSO contains the two maintenance pull requests merged 2026-10-16, 45f83fc / 2dde483 / 706cb3d / 46de307, cloud hooks and the safety guard, which have their own HANDOFF entries and are not viewer work. The session-end docs commit after 2c7fe1c is docs only.) Verify with `git diff --name-status 9f6c5c8..2c7fe1c`. |

No sibling-repo commits. The candle cache, the unit rows (`manage_trades.csv.gz`), the
viewer's data folder (`viewer/data/`, including `universe.json`) and the vendored library
(`viewer/vendor/amcharts5/`) are gitignored; the data is reproducible offline with
`uv run python -m analysis.domino.trade_viewer build --as-of 2026-10-10` (needs the cached
`*_1d_20261010.json` and `*_1h_20261010.json` files, which the owner's machine has; the build
fetches amCharts 5 from cdn.amcharts.com with a browser-like agent). `proto_codex/` is
untracked and out of scope.

## What to read first

1. `analysis/domino/viewer/NOTES.md` -- the page's receipt: the tour, the address keys, the
   verification record (universe figures against the engine's CSV in pandas, BTC against
   Python, the drawing and magnet proofs in `viewer/shots/`), what is not proven, what it lacks.
2. `analysis/domino/viewer/core.js` -- `settle`, `tradeSpan`, `stackLevels`, `setupDays`
   (the TVB-39 row logic with the calendar passed in), `aggregate` / `makeCalendar`, `barType`
   / `htfType` (the week's and month's closed-bar STRAT type, R10 operators).
3. `analysis/domino/viewer/stats.js` -- `bookStats` (equity by entry date, max drawdown, target
   and days semantics per book), `bySetup` (D5 minus the chance book paired), `histogram`,
   `calendarDays`, `fromUniverse` (decoding the columnar table).
4. `analysis/domino/viewer/story.js` -- `narrate` (setup words, target words, the clocks, the
   per-book paragraphs), `ladder`, `context`, `playbook` (the receipt's numbers in prose).
5. `analysis/domino/viewer/app.js` -- `drawPane` (candle roles, system levels as axis ranges,
   markers and their slots, the zoom), `shiftTitles`, `magnetDrop`, `proofStep` (`&seed`,
   `&then`, `&ray`), `renderCalendar`, `renderCompare`, `syncHash` / `fromHash`.
6. `analysis/domino/trade_viewer.py` -- `ensure_vendor`, `universe_table` (code books, -1
   sentinels, three-decimal rounding, day numbers from 2020-01-01), `build`.
7. `tests/test_domino_viewer.py` (the calendar test now reads `core.js`) and
   `analysis/domino/MANAGE_RECEIPT.md` (viewer section, the promotion paragraph).
8. `docs/reviews/tvb39-codex-audit.md` F4-F7 (inherited viewer findings; do not re-find them).

## Focus areas

- **The founding rule.** `core.js` claims the TVB-39 row logic unchanged apart from the
  calendar argument: diff `settle` / `tradeSpan` / `stackLevels` / `setupDays` against
  `git show da7f4c2^:analysis/domino/viewer/app.js` (the retired page). Does any path in
  `drawPane`, `strip`, `story.js` or `stats.js` compute a trade outcome instead of reading it?
- **`stats.js` against `manage.py`.** The drawdown runs by entry date with same-day rows in
  the file's order; "at target" uses `hit_X` for A / B / D / D5 and `out5 == one_r` for the
  chance book; median days uses `exit_k` (or `days`) for C and `days_X` otherwise; the
  histogram's end bins collect everything beyond. Is any of that a different reading of the
  columns than the engine's own tables?
- **`story.js` claims.** Every sentence is meant to be a column read back: the exit-day test
  (close against the day's open AND the week's open; a Monday is one test), the A / B / D /
  D5 branches on `hit_X` and `days_X`, the chance book on `out5` / `stop_k` / `one_r_k`,
  under water on `exit_k_u`, the hourly clock on `entry_h` / `exit_h`, the own-bar clock on
  `days_own` / `ret_C_own`, the setup words on `kind` / `anchor` / `t1_src`. Find a row where
  the words and the row disagree.
- **The closed-bar chips.** The last COMPLETE week / month before the entry day typed against
  the complete bar before it, strict breaks, equality never breaks; `?` when fewer than two
  complete bars. Check `aggregate`'s `complete` flag at the data's edges.
- **The universe table.** `universe_table` and `fromUniverse` round-trip: codes, `-1` for a
  missing int, `null` for a missing return, `exit_k` falling back to `days`, three-decimal
  rounding; is any field the page reads from it absent or mis-decoded? Does the universe
  Compare apply the same filters as the coin view (`liquid`, `t1`)?
- **The magnet ray.** `magnetDrop`: pixel to axis position through `toAxisPosition(px /
  axisLength())` (the renderer has no `coordinateToPosition` in 5.21.x), nearest bar by time,
  nearest of O / H / L / C by pixel, the library's Horizontal Line at that price with the
  control's stroke settings restored afterwards. The proof flag `&ray=high` snapped exactly on
  BTC 03-25; find a timeframe or zoom where it does not.
- **Drawing persistence.** `swapDrawings` clears, re-keys the save control per coin and pane,
  restores, and holds autosave off for 500 ms; `drawingsupdated` saves otherwise. Any path
  that clears a slot or saves an empty set over a full one (a coin switch, a dual-pane open,
  a tab switch)?
- **Hygiene.** ruff clean; tests 372 passed, 2 skipped; no secrets; vendor and data
  gitignored; no private link; `proto_codex/` untracked; the CDN user-agent string; the
  `.gitignore` edits.

## What is NOT in scope

The TVB-39 audit's findings F1-F8 themselves (their synthesis is TVB-41's first item); the
TVB-38 management-book engine as audited and folded (`tvb38-codex-audit.md`, A1); the TVB-37
chance / book engines (audited twice); the TVB-31..35 executor findings (private repo); the
`.claude/` hooks merged 2026-10-16 (reviewed on their own pull requests).
