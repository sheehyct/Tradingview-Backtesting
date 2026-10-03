# Sharp-move event study: do sharp bars continue or revert? (TVB-36, 2026-10-03)

Question from the owner: is a momentum arm built on the Sharp Move Detector, with Bollinger bands
and STRAT levels as targets or exhaustion areas, worth exploring on altcoins? This study generates
the data; it selects nothing and is not a strategy. Definitions were fixed in
`sharp_move_study.py`'s docstring before the first read; the post-hoc cuts are labeled as such.

**Event:** the detector's own default tiers (`tv_indicators/pine/sharp_move_detector_v2.pine`):
true range at least 2 / 3 / 4 times the PRIOR bar's ATR(14), with the 1.5x volume confirmation on
the two lower tiers. Direction = the bar's close against its open.
**Universe:** the 40 crypto perps with the highest median daily volume in the September decision
journal (`top40_main.json`). **Bars:** 1h over 202 days and 15m over 51 days, public candles ending
2026-10-03 12:00Z. **Outcome:** return from the event bar's CLOSE to the close h bars later, signed
by the event direction (plus = continued, minus = reverted). t-stats are on per-bar means; the
longer horizons overlap, so those t-stats are overstated.

## A-priori results

| 1h bars, 7,912 events | h=1 | h=4 | h=12 | h=24 |
|---|---|---|---|---|
| all bars (baseline) | -0.02% | -0.03% | -0.04% | -0.01% |
| all sharp events | +0.00% | -0.05% | +0.01% | +0.13% |
| mild (2-3x) | -0.01% | -0.04% | -0.01% | +0.06% |
| strong (3-4x) | +0.08% | +0.01% | +0.12% | +0.22% |
| extreme (4x+) | -0.06% | -0.25% | -0.02% | +0.44% |
| compression before: yes / no | +0.07 / -0.03 | +0.05 / -0.10 | -0.04 / +0.03 | +0.02 / +0.17 |
| closes beyond the band: yes / no | +0.02 / -0.02 | +0.01 / -0.13 | +0.23 / -0.28 | +0.46 / -0.31 |
| beyond prior-day high/low: yes / no | -0.02 / +0.02 | -0.10 / -0.00 | +0.09 / -0.08 | +0.37 / -0.12 |

| 15m bars, 7,903 events | h=1 | h=4 (1 h) | h=12 (3 h) | h=24 (6 h) |
|---|---|---|---|---|
| all bars (baseline) | +0.00% | -0.02% | -0.03% | -0.04% |
| all sharp events | -0.01% | -0.11% (t -3.3) | -0.12% (t -2.3) | -0.03% |
| compression before: yes / no | -0.02 / -0.01 | -0.11 / -0.11 | -0.14 / -0.12 | -0.13 / +0.01 |
| closes beyond the band: yes / no | -0.01 / -0.02 | -0.13 / -0.08 | -0.13 / -0.11 | -0.05 / +0.01 |
| beyond prior-day high/low: yes / no | +0.00 / -0.02 | -0.12 / -0.11 | -0.16 / -0.10 | -0.01 / -0.04 |

Share of events that continued: 47-49% at 1h, 43-47% at 15m.

Reading of the declared cuts: entering in the direction of a sharp bar at its close did not pay on
average. At 15m sharp bars REVERTED over the next one to three hours; at 1h the mean is zero out
to twelve hours. Tier did not order the result. Compression-then-expansion (charter S5) showed no
continuation at either timeframe. The band split matters at 1h only: sharp bars that close beyond
the band continued over 12-24 h, those that did not reverted.

## Post-hoc cuts (added after the first read; interpretation only)

The direction-signed statistic hid that price rose after sharp bars in BOTH directions, so raw
price-direction returns were added against the unconditional drift.

| Raw forward return | h=1 | h=4 | h=12 | h=24 |
|---|---|---|---|---|
| 1h: all bars (drift) | +0.02% | +0.06% | +0.18% | +0.36% |
| 1h: after sharp UP bars | +0.08% | +0.09% | +0.28% | +0.72% |
| 1h: after sharp DOWN bars | +0.10% | +0.23% | +0.31% | +0.57% |
| 15m: all bars (drift) | +0.01% | +0.05% | +0.14% | +0.29% |
| 15m: after sharp UP bars | +0.05% | +0.02% | +0.07% | +0.26% |
| 15m: after sharp DOWN bars | +0.08% | +0.25% | +0.33% | +0.34% |

- The universe drifted up hard over the window, and it was SELECTED on September volume, which
  favors coins that had risen: the drift is inflated by survivorship.
- 15m: a sharp DOWN bar was followed by a bounce. 61% bounced within the hour, mean +0.25% against
  drift of +0.05%. Down bars that closed BELOW the lower band bounced hardest: 65% within the hour,
  mean +0.34% (t -6.5 on the signed statistic). Sharp UP bars showed no continuation beyond drift.
- 1h: sharp UP bars that closed beyond the upper band continued, +0.93% at 24 h against drift of
  +0.36%. Sharp DOWN bars bounced, +0.57% at 24 h.
- By month the 1h result is unstable: the 24 h number is -0.68% in April and +0.98% in August. In
  September, sharp 1h bars reverted in the next hour (41% continued).

## What this does and does not say

- It does not support a symmetric momentum arm that follows sharp bars at the close.
- It shows an ASYMMETRY in this window: flushes bounce, and upside bursts beyond the band carry at
  1h over half a day to a day. Both are what a rising market does, so both are regime-conditional
  and both would likely invert in a falling tape.
- It agrees with the September book from an independent angle: the book's shorts were its worst
  cell (10 of 50 against 20 expected), and shorts taken with a falling index went 0 for 8.
- Not tested: entering DURING the move. The detector is an intrabar alarm; this study enters at the
  bar close because public history is too shallow at 1m (about 3.5 days). Costs are excluded;
  the taker round trip is about 0.086% against a median event ATR of 0.66% (15m) and 1.10% (1h).

## Files

`sharp_move_study.py`, `sharp_move_study.json`, `top40_main.json`, `as_of.json`. Candle caches
under `data/` are gitignored and refetch from the public API.
