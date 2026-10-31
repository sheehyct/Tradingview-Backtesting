# The trade viewer (TVB-40): the amCharts page, promoted 2026-10-17

The TVB-39 viewer (lightweight-charts, `index.html` + `app.js` up to commit da7f4c2) is retired.
This page replaced it on the owner's call of 2026-10-17 after a two-builder design-off (CLAUDE in
`proto_claude/`, CODEX in `proto_codex/`, two rounds: e79f8d3 proved the amCharts drawing toolbar
and its save / restore on the same rows; da7f4c2 was the UI / UX overhaul). This file is the
page's receipt; the viewer section of `analysis/domino/MANAGE_RECEIPT.md` points here.

    uv run python -m analysis.domino.trade_viewer hourly --as-of 2026-10-10 all   # once, ~9 min
    uv run python -m analysis.domino.trade_viewer build  --as-of 2026-10-10       # ~1 min
    uv run python -m analysis.domino.trade_viewer serve                            # opens the browser
    http://127.0.0.1:8765/#coin=BTC&date=2026-03-25&tf=D&dir=up&view=1D&book=C

`build` vendors amCharts 5 into `viewer/vendor/amcharts5/` (gitignored; free tier, logo kept; the
CDN serves the current 5.x: 5.21.2 at promotion) and writes `data/` (gitignored): one JSON per
coin, `index.json`, `dates.json` and `universe.json` (every coin's rows, columnar, 15 MB).

## The founding rule holds

The page reads what `build` wrote and draws each row off the row. `settle()`, `tradeSpan()`,
`stackLevels()`, `setupDays()` and the calendar bucketing (Monday 00:00 UTC weeks, calendar
months) live in `core.js`, the TVB-39 logic with the calendar passed in; `test_domino_viewer`
checks the bucketing against the census's own. No trade logic is re-run; the chart's data
grouping is OFF, so a zoomed-out daily chart never shows a library-made weekly candle. Every
number in the story, the ladder, the Compare tab and the calendar is arithmetic on recorded rows
(`stats.js`, `story.js`).

## The page, in one tour

- **Top bar**: coin, or a day across all coins; three tabs (Trade, Compare books, Playbook);
  Single / Dual charts; the two visibility toggles (System levels, My drawings).
- **Left rail**: the book and the equal size (they drive everything on the page), the filters
  (unit, side, setup, liquid, has T1), a **month calendar** with census weeks (Monday first),
  each entry day's equal-size dollars and trade count, a week-total column, a year strip, and a
  **This coin / All coins** scope (all coins = the universe table: every coin, the page's book,
  every filter); under it a **sortable trade table** (newest, oldest, best, worst, longest held)
  with the W / M closed-bar chips on every row.
- **Centre (Trade)**: a **facts strip** (side, setup and stack, entry, the book's exit, days
  held, result in percent and dollars, best / worst travel, the week's side at entry, the
  closed-bar chips), then the chart pane(s): timeframe, **Magnet**, the amCharts toolbar (Draw,
  the save control, settings). **Dual** adds a Context pane (defaults to 1W) with its own
  timeframe, toolbar and drawing slot.
- **Magnet ray** (the Magnet button or `R`, `Esc` leaves): a click drops a line at the nearest
  open / high / low / close of the bar under the pointer, on that pane's own bars. The line is
  the library's Horizontal Line, so it is saved with every other drawing in the coin's slot and
  the toolbar's select / move / erase / clear work on it. Proof: `&ray=high` makes the same call
  4 px off the entry bar's high; the console prints "snapped to 72034 (exact)" on BTC 03-25.
- **Right side**: **In plain words**, the trade narrated from the row (the setup and why its
  magnitude is what it is, the plan at entry with every touch day, what the selected book did
  and the exact exit-day test, the other clocks, travel); **Every book on this trade**, a ladder
  of all six books' fills (click one to make it the page's book); **Context at entry** chips.
- **Compare books**: a scope switch, **This coin / day** or **Universe, every coin** (179,498
  rows, loaded once, every filter applied); six KPI cards (average, green share, median, total,
  max drawdown, at target, median days, average win / loss, best / worst); overlaid equity
  curves by entry date at equal size; a one-percent distribution of the page's book against the
  chance book; a by-setup table of every book's average with **D5 minus the chance book** (the
  stop swap, the owner's H2) as the last column. Click a card to switch the book everywhere.
- **Playbook**: what the trade is, how it leaves (the daily clock and the other clocks), the
  targets, the six books in a table, where the receipt says they stand, how to read the chart
  and the chips, what the page never does.

Address keys: `#coin=&date=&tf=&dir=&view=&book=` (the TVB-39 form) plus `layout=dual&view2=1W`,
`tab=compare|playbook`, `cmp=universe`, `cal=all`, `day=YYYY-MM-DD` (the all-coins day); the
read-only `&show=sys|man|none` and the proof flags `&seed=1`, `&then=1W`, `&ray=high`.

## Verification

- **Compare, universe scope, against the engine's CSV in pandas** (2026-10-17, all filters on,
  1,000 per trade): every card figure agrees to the printed precision (C: 178,203 filled, 35%
  green, -0.09 average, -2.06 median, -152,675 total, 3 median days; max drawdown -629,820 on the page
  against the engine's -629,821, both on completed daily sums since the TVB-40 audit F1 repair of
  2026-10-30 (the page scored a within-day path before: -629,981; every book now agrees with
  `manage.book_stats` within about a dollar, the universe table's three-decimal returns);
  the chance book: 175,259 filled, -0.45 average, -796,301 total, 39% at target); totals differ
  by a few dollars because the universe table carries returns to three decimals. The by-setup
  rows agree (daily 2-2 reversal: C +0.19, chance -0.84, D5 minus chance +0.91 on 44,181 pairs;
  continuation +0.54; inside +0.79; outside +0.54), and the chance book's daily averages are
  the receipt's own (-0.84 reversal, -0.57 inside, -0.44 continuation, -0.30 outside up to the
  receipt's T1 cohort).
- **Compare, this coin, against Python on BTC** (2026-10-15): every card and by-setup figure.
- **The every-coin calendar** gives the same March 2026 as the old dates.json route (6,998
  trades, -61,126 USD on book C).
- **Drawings** (headless Edge, DevTools protocol, `shots/`): `btc_0325_1D_drawn / _reload /
  _1W_switch / _1H_reload`, `btc_0327_1D_drawn / _reload / _1M_switch`, `btc_0327_dual_1D_1W`,
  the two toggles; the magnet ray `btc_0325_1D_magnet_high` (dropped), `_magnet_reload`
  (restored), `_1W_magnet_switch` (still there on the weekly bars).
- The rest: `compare_btc_book_C`, `compare_universe_book_C`, `calendar_every_coin`,
  `day_2026-03-25_all_coins`, `playbook`.
- Python: `uv run ruff check .` clean; `uv run pytest tests/ -q` 428 passed, 2 skipped (2026-10-30;
  `tests/test_domino_viewer_js.py` runs core.js / stats.js / story.js under node on the audits'
  named shapes).
- **Audit repairs, 2026-10-30** (TVB-39 F4-F7, TVB-40 F1-F6; see the TVB-41 HANDOFF entry): the
  touch markers search the RECORDED price (level, target, one R, stop) with a one-in-a-billion
  tolerance and never fall back to the day's first bar (a miss sits on the last bar and says so);
  the chance book's stop exit sits on its touch hour; a selected book without a result keeps its
  name, borrows no window and states the row's own status (no book-C fall-back); the domino
  label and band cover the classed PAIR read from the row (daily rows: the daily level and
  `near_tf`; weekly / monthly rows: the unit's level and the daily level) and the other same-day
  breaks are labelled with their distance; on the hourly pane the entry arrow sits on the
  engine's entry hour; the Compare drawdown runs on daily sums;
  the magnet picks the candle whose cell is under the pointer; the story reads the row's status
  and direction (a short's hourly clock is green-in-green; an open row is marked, not clocked out;
  a same-day stop / one-R tie is named as the engine's pessimistic order); travel is labelled as
  book C's window; the calendar month averages over the rows with a result; a book change
  re-sorts the table. These repairs are proven under node (`tests/test_domino_viewer_js.py`) and
  by the universe drawdown check above; the browser shots in `shots/` predate them and were not
  re-taken, so marker placement on the audits' named rows (ATOM 2026-05-09, ACE 2026-06-14, BTC
  2026-03-16 W) is not yet proven on a rendered page.

Not proven: a drawing made by a real mouse drag (the trend line's two-point flow); drawings
across a coin switch (the slot swap runs on every load, but only BTC was loaded headless); the
Context pane's own slot across a reload (same control, same code path, a different key).

## What it still lacks

- The two panes do not share drawings or a crosshair (slots `am5-stock-domino-<coin>-drawings`
  and `...-<coin>-b-drawings` in browser storage); rays from the retired page's storage
  (`domino-viewer-rays:<coin>`) are not read.
- The universe table is 15 MB and loads on first use of the universe scope or the every-coin
  calendar (a second or two from localhost); returns in it are rounded to three decimals.
- The trade table and the chart stay per coin or per day; the universe is a Compare and
  calendar scope, never a 179,498-row table.
- Weekly and monthly panes fit the y axis loosely when the 2025 highs are in view.
- The hourly window is the venue's ~208 days; older trades say so on the 1H view.

## The run contract, stage 1 (2026-10-31, TVB-42)

`CONTRACT.md` is the one card shape every run exports and this page will draw (stage 2): a run
card (name, as-of, bar clock, rule card in words, the books with a role), one card per trade
with the books as a list on it, every time an exact timestamp. Stage 1 built the gate and the
first run, no page change:

- `analysis/domino/contract.py` validates a run in plain words with the card named, lays it out
  under `data/runs/<id>/` with `index.json`, `dates.json` and `universe.json` derived from the
  cards, and lists it in `data/runs.json`; a folder, a single JSON file or a zip imports
  (`trade_viewer import`), so a run made elsewhere, a phone included, is viewable by writing the
  shape. Bars are optional; `--bars-from-cache` fills a Hyperliquid coin's from the census cache.
- `analysis/domino/run_export.py` writes the management book as run one
  (`trade_viewer export-run --as-of 2026-10-10`): 292 instruments, 179,498 cards, 17 books per
  card (the six ladder books, the hourly, under-water, own and long clocks with their A / D
  variants, the measured-move A), 486 MB against 302 MB for the flat layout, 56 s to export and
  about a minute to validate and derive. Times come from the engine's daily bar list by index
  (the census fills no gaps); clock-exit prices are recovered from the recorded return.
- The gate caught a real shape defect on the first export: 339 shorts (278 monthly, 48 weekly,
  13 daily) carry a one R at or below zero (the setup range exceeds the price) and 964 rows a
  measured move at or below zero; none ever filled. The card now carries no price for those,
  says why on the D books, and keeps the raw numbers in `extras` (`one_r_raw`, `mm_raw`).
- `trade_viewer check-run management-book-20261010` compared every card with this page's flat
  data: 179,498 cards, no differences in level, the six ladder books' returns, the headline's
  reason and day, D5's and the chance book's reason and day, T1's price and touch day, one R's
  touch day, the hourly clock. The derived universe table matches the old one row for row on
  every return column and the headline status; its hit columns differ only where a book has no
  target (25,948 rows without T1, 81,140 without T2, 335 with no reachable one R): the engine
  wrote "not hit" there, the contract says "not applicable" (null), by rule.
- Tests: `tests/test_domino_contract.py` (31: the validator's refusals by name, the derived
  shapes, single-file / zip / in-place import, the mapping on the audits' row shapes).

## The three things next

1. **A journal layer**: a note and a one-tap verdict per row, saved beside the drawings and
   surfaced on the calendar and the table, so a pass over hundreds of trades leaves a record.
2. **One drawing slot for both panes** (serialize on change, unserialize in the other), and the
   retired page's rays imported into it once.
3. **An hourly archive**: the venue serves ~208 days of hours; `hourly` runs appended to a
   cache keyed by month would let the 1H view and the hourly clock reach older trades.
