# TheStrat Magnitude + Targets (MTF) [Custom] -- publish description

> Companion README for `strat_magnitude_targets_plus.pine` (Pine v6). This is
> a logic-identical fork of `strat_magnitude_targets.pine` (the partner-
> authored original): detection, triggers, targets, status, and chop logic are
> byte-for-byte the same. Everything this fork adds is display customization
> and settings-panel quality of life. With every input left at its default,
> the chart renders identically to the original.

## What it does

Identical to the original: when a Strat-style setup goes in-force on the
signal timeframe, it projects the trigger, Target 1 (the reclaim level), and
a ladder of prior highs/lows not yet taken out; keeps the most recent
signal's levels on the chart until replaced; and summarizes pattern,
direction, trigger, targets, live distances, open profit, position status,
and a chop counter in a table. Works on the chart timeframe or any higher
one (local aggregation, no data requests).

What the fork adds, all cosmetic or informational:

- Every visual element is user-controlled: every line has color, width, and
  (for triggers and active targets) style inputs; every text element has a
  color and a five-step size input; the table and the chop banner each take
  any of the nine chart positions.
- Inputs grey out when their parent toggle is off (Pine v6 `active`), so the
  panel shows only what currently matters.
- Optional bold on the two table header rows (Pine v6 text formatting).
- Optional MAGNITUDE table row: the trigger-to-Target-1 distance. Off by
  default to match the original layout.
- A separate show/hide for the chop banner (the alert condition and the
  table row are unaffected by hiding the banner).
- A tooltip on every input, including colors: what it controls, what the
  default is, and when to change it.

## What it does NOT do

- NOT backtested; no default is a tested value. Chart-reading aid for
  discretionary use only.
- Places no orders, manages nothing, predicts nothing. Targets are
  structural reference levels (prior highs/lows), not forecasts.
- Changes nothing about detection relative to the original. If you want the
  original's exact behavior, this fork at defaults IS that behavior.

## How to read it

Same as the original; short version:

- Solid labeled lines: active targets, T1 heavier and tagged "(reclaim)".
- Dashed line: the trigger. Star-trigger styling (default fuchsia, width 3)
  marks the high-priority patterns (Shot-Gun, Randy Jackson, Rev-Strats,
  3-2 Boom); plain triggers are thin grey.
- Greyed dotted levels with a check mark: already taken out. Gold with a
  return arrow: taken out, then price returned across ("reclaimed").
- STATUS: IN-FORCE / STILL GOOD / RETRACEMENT / POTENTIAL 3. While
  POTENTIAL 3 is active, optional 3-trigger and continuity (live open)
  lines appear.
- REVS / CHOP: direction flips since the last Target 1 hit; at the threshold
  the banner and the alert condition fire.
- "PMG +" prefix: the reversal fired into a lower-high / higher-low run.
  "Boom": the 3-2's outside bar qualifies as a hammer / shooter under the
  script's shape rule (dominant wick >= 50 percent of range, body <= 40
  percent).

## Inputs

- Timeframe: signal timeframe (blank = chart timeframe).
- Logic: break/reclaim distance (1 tick or fixed amount), extended target
  count, invalidation of held targets.
- Display: label offsets; trigger toggles; label text color and size; table
  master toggle and per-row toggles (To-Go, Profit, # Targets, Magnitude,
  Revs/Chop).
- Chop: detection toggle and threshold; banner toggle, position, text size;
  chop color and banner text color.
- Style: Up / Down / Neutral colors; table position (nine-way grid).
- Table Style: table text size; row-label text color; header background;
  bold header rows; frame color and transparency.
- Lines: normal trigger color/transparency/width; star trigger color/width;
  trigger line style; Target 1 and extended widths; active target style.
- Taken-out targets: grey-out toggle; taken color/transparency/width and
  style; reclaimed highlight toggle and color/transparency/width.
- Position status: retracement and potential-3 colors; status label toggle;
  3-trigger line toggle and width; continuity line toggle and
  color/transparency/width.
- Setup Dictionary: unchanged from the original -- one toggle per pattern,
  long names vs zipcodes, PMG toggle and bar count.

## Assumptions and limitations

Identical to the original; restated because they matter:

- Signals are detected on the DEVELOPING signal-timeframe bar and can
  appear, relabel, or clear intrabar until that bar closes. By design (live
  in-force detection), not a defect -- but treat mid-bar signals as
  provisional.
- All drawings and the table render on the last bar only; nothing is painted
  into history, so there is no historical "track record" to misread.
- The chop counter advances on confirmed bars only.
- No `request.security()` anywhere: higher-timeframe bars are aggregated
  locally from loaded chart bars. The script keeps the most recent 250
  completed signal-timeframe bars; the ladder cannot reach further back.
- Timeframe boundaries come from `timeframe.change()` on the session
  TradingView serves for the symbol; the script does no timezone arithmetic
  of its own, so DST handling is TradingView's.
- Signal timeframe should be the chart timeframe or higher; a lower value is
  not rejected, it just degrades to chart-timeframe behavior.
- Volume is never used; no-volume instruments are fine.
- Drawing caps: 60 lines, 60 labels. Two auxiliary lines (continuity and
  3-trigger) keep a fixed dashed style by design; their color, transparency,
  and width are inputs.
- The Chop Warning alert condition snapshots inputs at alert creation;
  changing inputs requires recreating the alert. Hiding the chop banner does
  not silence the alert; turning off chop detection does.
- Two input titles were shortened versus the original to fit paired rows
  ("Taken-out transparency" and "Reclaimed transparency" are now "Transp"
  next to their colors). Defaults are unchanged.

## Version notes

- 2026-07-30 -- Initial release. Fork of the v6-migrated original
  (`strat_magnitude_targets.pine`, which includes the v6 warm-up guards in
  CLASSIFY and the restored LADDER section comment). Logic byte-identical;
  adds the customization layer described above. Defaults render identically
  to the original.
