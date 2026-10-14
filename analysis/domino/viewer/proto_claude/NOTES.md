# proto_claude: the trade viewer on amCharts 5 Stock Chart

Built 2026-10-14 (TVB-40 seed: "charting upgrade for the viewer"), one shot, go-for-it mode.
This is the builder's own receipt. `analysis/domino/MANAGE_RECEIPT.md` is untouched.

Run it beside the reference page (same server, same data folder):

    uv run python -m http.server 8766 --directory analysis/domino/viewer --bind 127.0.0.1
    http://127.0.0.1:8766/proto_claude/index.html#coin=BTC&date=2026-03-25&tf=D&dir=up&view=1D&book=C

The library is vendored in `proto_claude/vendor/amcharts5/` (gitignored; one line in `.gitignore`),
fetched from `https://cdn.amcharts.com/lib/5/{index,xy,stock}.js` and `themes/Dark.js`, amCharts 5.21.1,
free tier, logo kept (bottom-left of the chart). If the folder is missing the page says so and stops.

## The founding rule holds

The page reads `../data/<coin>.json` and `../data/index.json` / `dates.json` exactly as `index.html`
does. `settle()`, `tradeSpan()`, `stackLevels()`, `setupDays()` and the calendar bucketing (Monday
00:00 UTC weeks, calendar months) are copied verbatim from the reference `app.js`; no trade logic
is re-run. The chart engine is the only replacement. Data grouping on the date axis is OFF
(`groupData: false`), so a zoomed-out daily chart still shows the census's daily bars, never a
library-made weekly candle; 1W and 1M are the page's own calendar buckets, as before.

## What this page does that index.html does not

1. **A real drawing toolbar** (amCharts `DrawingControl`): trend / horizontal / vertical lines,
   rays, channels, Fibonacci, rectangles, labels, measure, and the rest of the stock-chart set,
   with the library's own edit / move / delete handling. The reference page has only the magnet
   ray.
2. **Save / restore is the library's own** (`DataSaveControl`, the disk icon in the toolbar: Save,
   Restore, Clear, Auto-save). The page keys the storage per coin (`am5-stock-domino-<coin>-drawings`
   in browser storage) and saves on every `drawingsupdated` event, so drawings survive a reload and
   a timeframe change without the owner pressing anything. The toolbar's own buttons still work on
   top of that.
3. **Two visibility layers**: "System levels" (the row's level, ladder targets, one R, setup-bar
   stop, measured move, the same-day triggers with the gap band, every marker) and "My drawings"
   (the toolbar's), each a toggle in the header. System levels are axis ranges, not drawings, so
   the drawing tools cannot select, move or delete them: read-only by construction. The address
   can preset them (`&show=sys`, `&show=man`, `&show=none`).
4. **The week's and month's bar type at entry as chips** on every card and on the trade line
   ("closed bar at entry: W 2U  M 2D"). Definition: the last CLOSED week (month) before the entry
   day, typed as a STRAT bar against the complete week (month) before it, ruling R10 operators
   (strict breaks; an equal high or low never breaks, so it is a 1). The bar the entry sits in is
   still forming and is never typed (closed bars only). Inside bars (the owner's hazard) are amber
   with a border so they stand out in the card strip. A "?" means the data starts too late for two
   complete bars. Hover a chip for the dates and the two highs and lows it compared. Checked by an
   independent recomputation in Python on the four BTC entries 03-22 / 03-23 / 03-25 / 03-27: all
   four agree with the page (03-22 sits after an inside week, Mar 9 to 15; the other three after a
   2U week; every one after a 2D month, February against January).
5. **The gap band**: on a stacked row the space between the lowest and highest same-day trigger is
   shaded with the gap percent and the census band in its label, beside the dashed trigger lines.
6. A crosshair with axis read-outs on both axes (the library's cursor), and the amCharts settings
   control (log / percent scale, fills) for free.

## What it lost against index.html

- **The magnet ray tool** (R key, click near open / high / low / close). The toolbar's horizontal
  line snaps to the bar under the cursor (`snapToData`) but it is not the one-key magnet the owner
  used on the first pass. Rays saved by the reference page (`domino-viewer-rays:<coin>`) are not
  read here.
- **Marker text placement is cruder**: LWC stacks marker labels for you; here each marker is a
  shape bullet plus a label bullet at fixed offsets, so two markers on neighbouring bars can
  overlap ("in" and "out" on a two-day trade; the 03-27 short's T1 / out / under-water trio).
- **Line title tags are a shim**: the title sits in an axis-range label shifted to the plot's left
  edge by the plot width (re-shifted on resize and each frame). When two levels are within a few
  pixels the tags overlap (03-27: entry, daily trigger, exit and T1 anchor all inside 2.5%).
- The y axis does not auto-fit as tightly as LWC on the 1W / 1M views: with the 2025 highs in the
  window the trade compresses into a band near the bottom. Same data, different axis heuristics.
- No bar-magnifier / intrabar fills (neither page has them; noted so nobody expects them).
- Page weight: ~1.1 MB of library against 160 KB for lightweight-charts; first paint is slower.
- Animations are off (Dark theme only, no Animated theme), so zooms jump rather than glide.

## The proof (headless Edge, `shots/`)

Drawings for the proof were made through the same `DrawingControl.addLine()` call the pointer
makes (the page's `&seed=1` address flag puts a Horizontal Line at the row's setup-bar stop and a
Vertical Line on the entry day, then calls the save control). `&then=1W` / `&then=1M` switches the
timeframe inside the same session after the restore, through the same code as the 1W / 1M button.
Neither flag is written back into the address bar. Captured with a DevTools-protocol script
(viewport fixed to 1600x1000 before navigation, six to seven seconds of real time to settle); the
`--screenshot --virtual-time-budget` route left the chart pane half-resized in some captures
and is not trustworthy for this page.

BTC 2026-03-25, daily inside break long (-6.99% on the daily clock):

- `btc_0325_1D_drawn.png`  : the two drawings made in-session, system levels, the trade coloured
- `btc_0325_1D_reload.png` : fresh page load, no flag: both drawings restored from storage
- `btc_0325_1W_switch.png` : loaded on 1D, switched to 1W in-session: both drawings still on the chart
- `btc_0325_1H_reload.png` : fresh load on 1H: both drawings on the hourly bars, hourly markers

BTC 2026-03-27, weekly reversal short (+0.81%):

- `btc_0327_1D_drawn.png`  : drawings made in-session; the D+W stack with the gap band
- `btc_0327_1D_reload.png` : fresh load: both restored
- `btc_0327_1M_switch.png` : loaded on 1D, switched to 1M in-session: both still there
- `btc_0327_1W_reload.png` : fresh load on 1W: both there
- `btc_0327_1D_show_man_only.png` : System levels off, drawings on
- `btc_0327_1D_show_sys_only.png` : drawings off, System levels on

Not proven here: a drawing made by an actual mouse drag (the trend line's two-point flow), and
the drawings' behaviour on a coin switch (the page parks the current coin's set, re-keys the save
control and restores the new coin's; the code path ran on every load above, but only for BTC).

Python side: no Python added; `uv run ruff check .` clean; `uv run pytest tests/ -q` 372 passed,
2 skipped (2026-10-14).

## The three things I would do next

1. **Port the magnet ray** as a toolbar-native tool: a one-click horizontal line that snaps to the
   nearest open / high / low / close of the bar under the cursor, saved through the same
   `DataSaveControl` slot, so one storage holds both the owner's rays and the library's drawings.
2. **Collision-aware tags and markers**: stack the left-edge title tags when levels are within a
   tag's height, and let marker labels alternate sides when bars neighbour, so the two-day trades
   read without hovering.
3. **A second data source behind the same page**: the seed says the dedicated workspace waits until
   the viewer serves a second source. The drawing / save layer is now source-agnostic; the next
   step is an executor-ledger or Parallax paper row adapter that produces the same row fields,
   which would test whether "the page reads rows and never computes them" survives a second author.

## The one decision for the owner

Whether the library's own drawing + save layer (what this page proves) is worth giving up
lightweight-charts' tighter marker and label layout. If yes, the next session makes this page the
viewer and ports the magnet ray; if no, the amCharts toolbar is still the shortest route to
"drawings that survive", and the reference page stays as is.
