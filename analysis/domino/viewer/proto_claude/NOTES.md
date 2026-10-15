# proto_claude: the trade viewer on amCharts 5, round two (the design-off)

Round one (2026-10-14, commit e79f8d3) proved the amCharts drawing toolbar with the library's own
save / restore on the same rows as the reference viewer. Round two (2026-10-15) is the UI / UX
overhaul the owner asked both builders for: comparison easy to see, the trade in plain trader
language, analytics instead of an endless card strip, two charts side by side, a professional
page. This is the builder's own receipt; `analysis/domino/MANAGE_RECEIPT.md` is untouched.

Run it beside the reference page (same server, same data folder):

    uv run python -m http.server 8766 --directory analysis/domino/viewer --bind 127.0.0.1
    http://127.0.0.1:8766/proto_claude/index.html#coin=BTC&date=2026-03-25&tf=D&dir=up&view=1D&book=C

The library is vendored in `proto_claude/vendor/amcharts5/` (gitignored, one line in `.gitignore`),
fetched from `https://cdn.amcharts.com/lib/5/{index,xy,stock}.js` and `themes/Dark.js`, amCharts
5.21.1, free tier, logo kept. If the folder is missing the main pane says so and stops.

## The founding rule still holds

The page reads `../data/<coin>.json`, `../data/index.json` and `../data/dates.json` exactly as
`index.html` does. `settle()`, `tradeSpan()`, `stackLevels()`, `setupDays()` and the calendar
bucketing (Monday 00:00 UTC weeks, calendar months) are the reference's logic, now in `core.js`
with the calendar passed in instead of read from a global; no trade logic is re-run. The chart
is a GaplessDateAxis with data grouping OFF, so a zoomed-out daily chart never shows a
library-made weekly candle. Every number in the plain-words story, the book ladder, the Compare
tab and the calendar is arithmetic on the recorded rows (`stats.js`, `story.js`).

## The page, in one tour

- **Top bar**: coin, or a day across all coins; three tabs (Trade, Compare books, Playbook);
  Single / Dual charts; the two visibility toggles (System levels, My drawings).
- **Left rail**: the book and the equal size (they drive everything on the page), the filters
  (unit, side, setup, liquid, has T1), a **month calendar** with census weeks (Monday first),
  each day's equal-size dollars and trade count, a week-total column, a year strip to jump
  months, and a **This coin / All coins** scope (all coins = `dates.json`, book C, the day's
  trades across the universe); under it a **sortable trade table** (newest, oldest, best, worst,
  longest held) with the W / M closed-bar chips on every row.
- **Centre (Trade)**: a **facts strip** (side, setup and stack, entry, the book's exit, days
  held, result in percent and dollars, best / worst travel, the week's side at entry, the
  closed-bar chips), then the chart pane(s) with the amCharts toolbar: Draw, the save control,
  settings. **Dual** adds a second pane (Context, defaults to 1W) with its own timeframe, toolbar
  and drawing slot.
- **Right side**: **In plain words**, the trade narrated from the row (the setup and why its
  magnitude is what it is, the plan at entry with every touch day, what the selected book did
  and the exact exit-day test, the other clocks, travel); **Every book on this trade**, a ladder
  of all six books' fills on the row (click one to make it the page's book); **Context at
  entry** chips with their meanings on hover.
- **Compare books**: six KPI cards (average, green share, median, total, max drawdown, at
  target, median days, average win / loss, best / worst) on the trades shown; overlaid equity
  curves by entry date at equal size; a one-percent distribution of the page's book against the
  chance book; a by-setup table of every book's average with **D5 minus the chance book** (the
  stop swap, the owner's H2) as the last column. Click a card to switch the book everywhere.
- **Playbook**: what the trade is, how it leaves (the daily clock and the other clocks), the
  targets, the six books in a table, where the receipt says they stand, how to read the chart
  and the chips, what the page never does.

Address keys: the reference's `#coin=&date=&tf=&dir=&view=&book=` plus `layout=dual&view2=1W`,
`tab=compare|playbook`, `day=YYYY-MM-DD` (the all-coins day), `cal=all`; the read-only
`&show=sys|man|none` and the proof flags `&seed=1`, `&then=1W` stay.

## What this page does that index.html does not

1. The trade in trader language, generated from the row and checked against the row: the BTC
   03-25 story reads the inside break as a with-trend break with no magnitude of its own (the
   row's `anchor = ladder`), T1 as the first unbroken weekly level, the stop as a yardstick, the
   exit-day test with the day's open and the week's open, under-water and hourly clocks, travel
   in R. The 03-27 story reads the weekly reversal, the same-day daily trigger with the gap, a
   Monday exit as one test, the week's own clock beside the daily clock.
2. Every book on one trade in one ladder, and every trade on one book in one table: the two
   comparisons the owner asked for, one click apart.
3. The Compare tab. Cross-checked against an independent Python recomputation on BTC (all
   filters on, 1,000 per trade): every figure on the six cards (filled count, green share,
   average, median, total, max drawdown, at-target share, median days) and the by-setup rows
   agree; the only difference found (one book's drawdown by a few dollars) came from the order
   of same-day trades and is pinned to the file's order now.
4. The calendar: a month of entry days with dollars and counts, week totals, a year strip, and
   the all-coins scope that opens the day across the universe (03-25: 186 trades shown).
5. Dual charts: a weekly or monthly context pane beside the daily (or hourly) main pane, each
   with its own toolbar and its own drawing slot, both drawing the same row.
6. The chart's text now stacks instead of colliding: left-edge title tags lift off each other
   when their levels are within a tag's height, markers on the same or a neighbouring bar step
   outward, and a gap band thinner than its label keeps the fill and drops the words.
7. From round one, still here: the amCharts drawing toolbar with the library's save / restore,
   keyed per coin (the main pane keeps round one's slot, so drawings made then are still there),
   System levels as read-only axis ranges, the W / M closed-bar chips (R10 operators).

## What it lost, or still lacks

- The magnet ray (R key) is still not ported; the toolbar's horizontal line snaps to the bar
  under the cursor but is not the one-key magnet. Rays saved by the reference page are not read.
- Dual panes do not share drawings or a crosshair: each pane is its own chart with its own
  slot (`am5-stock-domino-<coin>-drawings` and `...-<coin>-b-drawings` in browser storage).
- The all-coins scope is book C only and ignores the liquid / has-T1 filters: `dates.json`
  carries one return per trade. A per-book universe compare needs a server-side aggregate.
- The Compare tab is per coin (or per day across coins), never the whole universe; the
  receipt's tables remain the universe view.
- The weekly and monthly panes still fit the y axis loosely when the 2025 highs are in view.
- The old trade cards are gone; the table shows date, side, unit, setup, chips and the book's
  result, and the rest moved to the facts strip and the story.
- Page weight ~1.1 MB of library against 160 KB; animations off.

## The proof (headless Edge, `shots/`, 1600x1000)

Drawings for the proof are made through the same `DrawingControl.addLine()` call the pointer
makes (`&seed=1` puts a Horizontal Line at the row's setup-bar stop and a Vertical Line on the
entry day, then calls the save control); `&then=1W` / `&then=1M` switches the main pane's
timeframe in-session after the restore. Captured with a DevTools-protocol script (viewport set
before navigation, a real-time settle), because `--screenshot --virtual-time-budget` captures
the pane mid-resize.

BTC 2026-03-25, daily inside break long (-6.99% on book C):

- `btc_0325_1D_drawn.png`, `btc_0325_1D_reload.png`, `btc_0325_1W_switch.png`, `btc_0325_1H_reload.png`

BTC 2026-03-27, weekly reversal short (+0.81%):

- `btc_0327_1D_drawn.png`, `btc_0327_1D_reload.png`, `btc_0327_1M_switch.png`
- `btc_0327_dual_1D_1W.png`: the dual layout on a fresh load, the main pane's drawings restored
- `btc_0327_1D_show_man_only.png`, `btc_0327_1D_show_sys_only.png`: each toggle hides its own layer

The rest of the page:

- `compare_btc_book_C.png`: the Compare tab on BTC, book C selected
- `playbook.png`: the Playbook tab
- `day_2026-03-25_all_coins.png`: the day across all coins, the all-coins calendar, BTC's row selected

Not proven: a drawing made by a real mouse drag (the trend line's two-point flow); drawings
across a coin switch (the slot swap runs on every load, but only BTC was loaded); the Context
pane's own drawing slot surviving a reload (it is the same control and the same code path as
the main pane, with a different storage key, and was not seeded).

Python side: no Python added or changed; `uv run ruff check .` clean; `uv run pytest tests/ -q`
372 passed, 2 skipped (2026-10-15).

## The three things I would do next

1. **A universe Compare**: a small build step that writes per-book, per-setup aggregates for
   all 292 coins (the receipt's tables as JSON), so the Compare tab can switch between this
   coin, this day and everything, with the same cards and curves.
2. **The magnet ray as a toolbar tool** saved in the same slot as the library's drawings, and
   a shared drawing slot across the two panes (serialize on change, unserialize in the other).
3. **A trade journal layer**: a note and a one-tap verdict per row, saved beside the drawings,
   surfaced on the calendar and the table, so the owner's pass over hundreds of trades leaves
   a record the next session can read.

## The one decision for the owner

Which page becomes the viewer. If this one, the magnet ray and the universe Compare are the
next two sessions and the reference page retires; if the reference page stays, the parts worth
porting back are the story, the ladder and the calendar, which are plain DOM and do not depend
on amCharts.
