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
- Session under review: TVB-39 (2026-10-12) -- the trade viewer (a local page + a build /
  hourly / serve CLI that draws the management book's recorded rows on the cached candles and
  claims to re-run no trade logic) and prereg amendment A2 (the lead's five candidates, each
  one change on the same trades: the week's side as a split, the hourly exit clock, book E =
  half at T1, fees at two taker fills, the under-water reading of "against"). The same
  evening the owner's first pass on the viewer produced three viewer additions and one viewer
  bug fix (7f3fc88) and surfaced an OPEN code-versus-skill question (the with-trend inside
  break's T1); that question is the owner's to rule, not the reviewer's, but the reviewer may
  say which reading the prereg text and the skill text actually support.
- Requested: 2026-10-12
- Write the audit to: `docs/reviews/tvb39-codex-audit.md` (copy `docs/reviews/_TEMPLATE.md`)

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `{pending push}` -- pinned after the session-end push as `4dc5f6b..{head}` (4dc5f6b is the pre-session sha; the range holds dbeaffe viewer, f505f9d A2 prereg, 340c86e A2 build, ed08ae5 serve flags, 7f3fc88 viewer second pass, then the close-out). Verify with `git diff --name-status 4dc5f6b..HEAD`. |

No sibling-repo commits. The candle cache (daily and hourly), the unit rows
(`manage_trades.csv.gz`), the viewer's data folder and vendored chart library, the page output
and the run logs are gitignored; the run is reproducible offline with
`uv run python -m analysis.domino.manage --as-of 2026-10-10` (about 10 minutes with the hourly
cache; needs the cached `*_1d_20261010.json` and `*_1h_20261010.json` files, which the owner's
machine has), then `uv run python -m analysis.domino.trade_viewer build --as-of 2026-10-10`.

## What to read first

1. `docs/experiments/tvb37_management_book_prereg.md`, "Amendment A2" -- the five definitions
   (A2.1-A2.5), the readings R1-R5 and the vectors v16-v19, written BEFORE the code (f505f9d
   precedes 340c86e); one labelled in-flight correction (the hourly ordering difference is on
   the exit day).
2. `analysis/domino/manage.py` -- `walk()` (unchanged except `exit_u` recorded on the same
   pass), `settle(clock="under")`, `hours_by_day`, `walk_hourly`, `hourly_fill`,
   `coin_manage_rows(meta, daily, hourly)`, `candidates()`, `table_candidates()`.
3. `analysis/domino/census.py` -- `HOUR`, `fetch_hourly`, `cached_hourly`, `normalize_hourly`.
4. `tests/test_domino_manage_a2.py` (7 vectors) and `tests/test_domino_viewer.py` (calendar
   bucketing through node against `census.week_start` / `month_start`).
5. `analysis/domino/trade_viewer.py` and `analysis/domino/viewer/app.js` -- `settle()`,
   `tradeSpan()`, `stackLevels()`, `draw()`, the ray tool; `index.html` for the controls.
6. `analysis/domino/MANAGE_RECEIPT.md` (viewer section with the first-pass additions; A2
   section) and `results/manage_tables.md` ("Amendment A2" tables), `manage.json`
   (`candidates`, `taker_pct`, `candidate_label`).
7. `docs/HANDOFF.md` TVB-39 entry, "The owner's first pass on the viewer" -- the two walked
   trades and the open question.

## Focus areas

- **`walk_hourly` cap and censor logic.** Entry hour = the first hour of the entry day
  reaching L (strict); exit = the first hour (entry hour included) closing against its own
  open AND the day's open (strict, both); the week is NOT tested; cap = the last hour (23:00)
  of day 20, OPEN marked at that close; CENSORED if the hours end first. Check the hour
  indexing (`hours_by_day`), the day-open the hour is tested against (the daily bar's open,
  not the hour's), and what happens on an entry day whose hours are partial.
- **The ordering claim.** The prereg says a target on the trade's side cannot be touched
  before the entry hour, so the hourly-versus-daily ordering difference is only on the EXIT
  day (the daily bar fills any touch that day; the hourly clock fills only up to the exit
  hour). Is that true for every target source, including the measured move and one R?
- **`exit_u` on the shared walk.** Under water = first daily close through L (strict) AND the
  week against; recorded on the same pass as the headline exit WITHOUT changing it. The
  headline tables are claimed byte-identical (179,498 units, same numbers). Verify.
- **Book E and the fees.** E = (A + C) / 2 when A hit T1 else C; fees = two taker fills at the
  dex's rate (main 0.0432%, xyz 0.0125% per fill), net = gross minus round trip. Arithmetic on
  recorded columns only.
- **The week's side.** `w_support` = price above / below the week's open at entry (colour),
  not the week's bar type. Confirm the split and the reach denominators.
- **The viewer's claim of re-running no logic.** `settle()` derives the fill from the row's
  recorded return (level moved by the return): is that always the engine's own fill price,
  including OPEN marks, shorts beyond -100%, and the reference book's five-bar mark?
  `stackLevels()` computes the previous complete bar's extreme per stack timeframe; the
  session checked it equals every row's `level` on its own timeframe (no mismatch on 179,498
  rows), but the OTHER timeframes' levels are drawn without a row to check against: is "first
  break of the current higher-timeframe bar" needed for them to be the census's levels?
- **The "data ends" marker fix.** The A2 markers had split the exit arrow's `if` / `else`;
  confirm no other marker is misbound and that the headline clock square appears only when
  the book box left on a different day.
- **The open question (opinion only).** Prereg definition: a with-trend inside break has no
  magnitude of its own and takes the first weekly / monthly rung. Skill R14 / R18: unfilled
  structure containing the trigger is a real structural magnitude. Which does the prereg text
  say, and does the skill's 2-1-2 continuation row ("reversal-exit" paradigm) point at the
  mother bar's far side? State the texts; do not rule.
- **Hygiene.** ruff clean; tests 372 passed, 2 skipped; no secrets; no private link in the
  repo; the `.gitignore` additions (`viewer/vendor/`); `serve --host` binds only on request.

## What is NOT in scope

The TVB-38 management-book engine as audited and folded (`tvb38-codex-audit.md`, A1); the
TVB-37 chance / book engines (audited twice); the TVB-31..35 executor findings (private repo).
