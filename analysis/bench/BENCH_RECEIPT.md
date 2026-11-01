# The one-instrument bench: run one's management book on ES, 2011-2025 (receipt)

**LABEL: CHARACTERIZATION, NO STRATEGY, NO P&L CLAIM.** Pre-registration
`docs/experiments/tvb43_bench_prereg.md` (confirmed by the owner 2026-11-01, before any ES row
existed). Generated 2026-11-01 by `analysis/bench/run_bench.py`; the full tables are
`analysis/bench/results/bench_globex_tables.md` and `bench_rth_tables.md` (run one's table
shapes), the summaries `bench_globex.json` / `bench_rth.json`, the rows `bench_*_trades.csv.gz`
(regenerable, ignored). Both runs are on the trade viewer as `es-globex-2011-2025` (run two) and
`es-rth-2011-2025` (run three), beside run one, and Compare lines them up by role. Every reading
below is shown in both directions; nothing here is a verdict, a parameter change or a
recommendation. A positive line is a path worth naming as a declared arm; a negative line a path
worth naming as a kill test.

## Glossary (trader terms first)

- **Run one**: the management book on 292 Hyperliquid perps, two venue years (`management-book-20261010`).
- **V0, the Globex day (run two)**: ES where "the day" is the Globex session, 18:00 ET open to
  17:00 ET close the next afternoon; weeks run Sunday evening to Friday; the owner's ruling for
  a futures bench (2026-10-30). The exchange's own daily, weekly and monthly bars.
- **V1, the regular-hours day (run three)**: the same book where "the day" is 09:30 to 16:00
  ET only, built from the 1-minute tape; the paired reading the standing mirror rule asks for.
  Not the ruled day: a second way to cut the same tape.
- **Session**: one day of either kind. Offsets count sessions (a Friday-to-Monday hold is one).
- **Unit**: one trade, the first break of a session's, week's or month's level in one direction.
- **The books**: C exit only (hold until a session closes against the trade with the week
  against it at that close; 20-session cap); A all out at T1; B hold through T2; D one R or the
  exit; D5 one R or the exit inside five bars of the unit; the **chance book** (reference: one R or
  the setup-bar stop, marked at bar five). The hourly clock C_h (exit on the first hour closing
  against its open with the session against it) and under water C_u are grouped books.
- **The stop swap**: D5 minus the chance book on the same rows: the setup-bar stop replaced by
  the close exit, everything else equal (run one's headline finding: +0.48 to +0.92 per trade).
- **Roll**: the continuous contract switches to the next quarterly contract 60 times in the
  sample, at 00:00 UTC inside a session; the series is not back-adjusted, so a roll's price jump
  is a contract switch, not a move. `roll = entry` when the entry session is a roll session,
  `window` when a roll falls inside the headline window after the entry.
- **The continuity ladder, as a split**: C0 every unit; C1 the units whose week was on the
  trade's side at entry; C2 the week and the month both on the trade's side. Read off the cards'
  recorded context, no new engine path; each rung shown with its complement.
- **Percent per trade**: percent of price, equal size, no fees, no leverage, no margin
  arithmetic; `[a, b]` is a 95% interval on the mean.

## What ran

| | V0 Globex day | V1 regular-hours day |
|---|---|---|
| sessions | 3,859 (2011-01-03 to 2025-12-31) | 3,851 |
| hours on the hourly clock | 88,137 (23 per session; 139 short sessions) | 26,900 (7 per session; early closes shorter) |
| units: session / week / month | 3,824 / 818 / 181 | 3,797 / 809 / 182 |
| hourly clock scored | 4,789 exits, 13 censored, 18 partial entry days | 4,786 exits, 0 censored |
| roll flag: entry / window | 80 / 196 | 81 / 213 |

The engine is run one's (`analysis/domino/manage.py`), unchanged, on the session calendar
(`census.use_calendar("session")`: yesterday is the previous session, a holiday week is complete,
the hourly clock steps from a session's last hour to the next session's first). The crypto book
reproduced byte-identically through the switched code before any ES row existed.

## 1. The books on session units (the daily units of the futures tape)

Percent per trade, every unit of the timeframe; the chance book on the same rows.

| | n | C exit only | A all out at T1 | B through T2 | D one R or exit | D5 five bars | chance book | T1 reached |
|---|---:|---|---|---|---|---|---|---|
| V0 Globex, all | 3,824 | -0.05 [-0.11, +0.00] | -0.02 [-0.06, +0.02] | -0.04 [-0.10, +0.01] | +0.00 [-0.04, +0.05] | +0.01 [-0.04, +0.05] | -0.11 [-0.15, -0.06] | 45% |
| V1 RTH, all | 3,797 | +0.08 [+0.03, +0.14] | +0.09 [+0.05, +0.13] | +0.08 [+0.03, +0.13] | +0.09 [+0.05, +0.13] | +0.10 [+0.06, +0.13] | +0.06 [+0.02, +0.10] | 48% |

By setup (C exit only; the chance book; T1 reached; the hourly clock's exit-only line and its median hold in traded hours):

| setup | V0 n | V0 C | V0 chance | V0 T1 | V0 C_h (hold) | V1 n | V1 C | V1 chance | V1 T1 | V1 C_h (hold) |
|---|---:|---|---|---|---|---:|---|---|---|---|
| 2-2 reversal | 1,136 | -0.02 [-0.12, +0.09] | -0.13 [-0.21, -0.05] | 64% | +0.06 [+0.02, +0.10] (8 h) | 1,288 | +0.10 [+0.01, +0.19] | +0.04 [-0.02, +0.11] | 65% | +0.16 [+0.11, +0.21] (3 h) |
| 2-2 continuation | 1,722 | -0.06 [-0.15, +0.03] | -0.08 [-0.15, -0.00] | 31% | -0.02 [-0.05, +0.01] (7 h) | 1,711 | +0.09 [+0.00, +0.18] | +0.07 [+0.02, +0.13] | 33% | +0.17 [+0.13, +0.21] (3 h) |
| inside break | 562 | -0.01 [-0.17, +0.14] | -0.13 [-0.24, -0.03] | 62% | +0.02 [-0.06, +0.09] (8 h) | 485 | +0.06 [-0.06, +0.18] | +0.03 [-0.05, +0.12] | 65% | +0.14 [+0.08, +0.21] (2 h) |
| outside break | 404 | -0.17 [-0.34, -0.01] | -0.14 [-0.30, +0.03] | 33% | -0.04 [-0.09, +0.02] (8 h) | 313 | -0.01 [-0.19, +0.17] | +0.10 [-0.06, +0.25] | 35% | +0.13 [+0.04, +0.23] (2 h) |

**What this says, both ways.** On the Globex day every management book sits within a few
hundredths of zero and the chance book is the one line clearly below it (-0.11, interval clear
of zero): the setup-bar stop loses on this tape too, by a smaller margin than on crypto. On the
regular-hours day every book, the chance book included, sits a few hundredths above zero with
the intervals clear: the same rules read a different sign when the day is cut differently. The
targets get reached at the same rates on both days (T1 before the exit about two thirds of the
reversals and inside breaks, a third of the continuations and outside breaks), which is run
one's shape. The outside break is the one setup negative on both days for the exit-only book.

## 2. The stop swap (D5 minus the chance book, same rows)

| unit | V0 Globex | V1 RTH | run one (crypto) |
|---|---|---|---|
| session / daily | +0.11 [+0.08, +0.15] (n 3,820) | +0.04 [+0.01, +0.06] (n 3,793) | +0.48 to +0.92 by setup |
| weekly | +0.04 [-0.15, +0.23] (812) | -0.05 [-0.23, +0.13] (802) | |
| monthly | -0.97 [-1.83, -0.11] (176) | -1.06 [-1.91, -0.21] (177) | |

**Both ways.** The swap replicates in direction on the daily unit of both days (the close exit
beats the setup-bar stop on the same rows, intervals clear of zero) at a fifth to a tenth of the
crypto size. It is flat on weekly units. On monthly units it reverses: the chance book (one R or
the setup-bar stop) is the better line by about a point per trade on both days, with the
interval clear of zero on each. A monthly setup bar's one R is a large distance on an index
future, and five monthly bars is a long horizon; the receipt names that line as the one where
the reference beats the management books, and leaves it there.

## 3. Longs and shorts (session units)

| | V0 longs | V0 shorts | V1 longs | V1 shorts |
|---|---|---|---|---|
| n | 2,143 | 1,681 | 2,121 | 1,676 |
| C exit only | +0.15 [+0.08, +0.23] | -0.32 [-0.41, -0.23] | +0.21 [+0.14, +0.28] | -0.09 [-0.17, -0.00] |
| A all out at T1 | +0.11 [+0.06, +0.16] | -0.18 [-0.24, -0.11] | +0.16 [+0.11, +0.21] | +0.00 [-0.05, +0.06] |
| chance book | -0.00 [-0.06, +0.06] | -0.24 [-0.32, -0.17] | +0.13 [+0.09, +0.18] | -0.03 [-0.09, +0.03] |

**The drift confound the prereg named.** ES rose from about 1,260 to about 6,900 over the sample.
Longs carry the book on both days; shorts lose on both, more on the Globex day (the overnight
session is where the index's upward drift and the gap risk sit for a short). Year by year the
Globex exit-only line on session units runs from -0.31 (2011, 2012, 2022) to +0.32 (2018) with
no monotone pattern; the regular-hours line is positive in twelve of fifteen years and negative
in 2016 (-0.14) and 2022 (-0.30). A reading that holds for longs only is reported as that.

## 4. The roll (session units)

| | V0 no roll | V0 roll on entry | V0 roll in window | V1 no roll | V1 roll on entry | V1 roll in window |
|---|---|---|---|---|---|---|
| n | 3,610 | 69 | 145 | 3,570 | 68 | 159 |
| C exit only | -0.11 [-0.16, -0.05] | -0.19 [-0.57, +0.19] | +1.37 [+0.89, +1.86] | +0.05 [-0.01, +0.10] | -0.25 [-0.70, +0.20] | +1.00 [+0.67, +1.33] |
| chance book | -0.13 [-0.18, -0.08] | -0.39 [-0.70, -0.08] | +0.64 [+0.35, +0.94] | +0.06 [+0.02, +0.10] | -0.43 [-0.75, -0.12] | +0.33 [+0.14, +0.52] |

**Both ways, and a confound confirmed.** A roll inside the window adds about a point to every
book on both days: the unadjusted series jumps to the next contract and the jump is scored as a
move. A roll on the entry session reads negative on both. Without any roll in the window the
Globex exit-only line is -0.11 [-0.16, -0.05] and the regular-hours line +0.05 [-0.01, +0.10]:
the sign difference between the two days survives the roll split. Rolls are flagged on every
card (`extras.roll`), never dropped, as the prereg declared; a back-adjusted rerun would be a
declared variant, not a correction.

## 5. The continuity ladder, read as a split

| rung | V0 n | V0 C exit only | V0 chance | V1 n | V1 C exit only | V1 chance |
|---|---:|---|---|---:|---|---|
| C0 every unit | 3,824 | -0.05 [-0.11, +0.00] | -0.11 [-0.15, -0.06] | 3,797 | +0.08 [+0.03, +0.14] | +0.06 [+0.02, +0.10] |
| C1 the week with the trade | 3,142 | -0.07 [-0.13, -0.01] | -0.09 [-0.14, -0.04] | 2,823 | +0.04 [-0.03, +0.10] | +0.03 [-0.01, +0.07] |
| C1 complement (week against or unknown) | 682 | +0.03 [-0.11, +0.17] | -0.17 [-0.28, -0.06] | 974 | +0.21 [+0.11, +0.31] | +0.15 [+0.08, +0.23] |
| C2 the week and the month with | 2,217 | -0.09 [-0.16, -0.02] | -0.08 [-0.14, -0.02] | 1,882 | +0.04 [-0.04, +0.11] | +0.03 [-0.02, +0.08] |
| C2 complement | 1,607 | -0.00 [-0.10, +0.09] | -0.15 [-0.22, -0.08] | 1,915 | +0.12 [+0.04, +0.20] | +0.09 [+0.04, +0.14] |

**Both ways.** On this tape the week's and month's side at entry do not select the better
exit-only trades: on both days the complement (the week against the trade, or unknown) reads
higher than the rung for the exit-only book, with the regular-hours complement clearly above
zero (+0.21 [+0.11, +0.31] against +0.04). For the chance book on the Globex day the gate goes
the other way (the complement is the worse line, -0.17 against -0.09). Weekly units read the
same way (V1: C1 -0.08 against its complement +0.32 [+0.12, +0.52]). Run one's amendment A2.1
found the same shape on crypto inside breaks and the opposite on reversals; here it is the
whole session-unit cohort. A continuity gate that removed the "against" units would have
removed the better-reading half on this tape: that is the reading, not a recommendation either
way.

## 6. The clocks (session units, rows scored on all three)

| | n | C session clock | C_u under water | C_h hourly clock |
|---|---:|---|---|---|
| V0 Globex | 3,800 | -0.06 [-0.12, +0.00] | -0.09 [-0.16, -0.01] | +0.01 [-0.01, +0.03] |
| V1 RTH | 3,794 | +0.08 [+0.03, +0.13] | +0.07 [-0.01, +0.15] | +0.16 [+0.13, +0.19] |

The hourly clock by setup (exit only; the hold in TRADED hours, the session clock's hold in
sessions times 24 as in run one's table; the losing trade's average): V0 reversal C_h +0.08
[+0.03, +0.14] against C +0.01 [-0.13, +0.14], holds 7 traded hours against two sessions, losers
-0.39 against -0.98; continuation -0.01 against -0.18 (C_h minus C +0.16 [-0.00, +0.33]); inside
-0.03 difference; outside +0.21 [-0.05, +0.47]. V1: the hourly clock is positive on all four
setups (+0.16 to +0.20, intervals clear of zero), holds two to three traded hours against one to
three sessions, losers -0.45 against -0.90; its difference from the session clock is +0.04 on the
reversal and +0.13 to +0.23 elsewhere, intervals through zero. On both days the hourly clock
takes T1 before its exit about half as often as the session clock (V0 reversal 36% against 60%).

**Both ways.** The hourly clock cuts the losers to less than half their size on both days, as it
did on crypto, and on the regular-hours day it is the one clock with every setup's interval
clear of zero. Under water is the weakest line on the Globex day. None of the three clocks moves
the Globex session-unit book away from zero by more than a tenth.

## 7. Weekly and monthly units, briefly

Weekly units (V0 818, V1 809): exit only -0.07 [-0.20, +0.05] and +0.01 [-0.11, +0.12]; longs
+0.12 on both, shorts -0.38 [-0.61, -0.15] and -0.18; the chance book -0.05 and +0.12; T1 before
the exit 27% and 28% (half of the reversals, a tenth of the continuations). Monthly units (181
and 182): the management books +0.14 and about +0.2 with intervals through zero; the chance book
+1.22 [+0.27, +2.16] on the Globex day and +1.0 to +2.6 by setup on the regular-hours day: the
monthly unit is the one place the setup-bar stop book is the better line on this tape, and the
stop swap is negative there (section 2).

## 8. Confounds and limits, named

- The roll (section 4) and the drift (section 3) are both inside every "all" line; read the
  no-roll and the longs / shorts rows first.
- One instrument, one era. The intervals are honest for this tape; they say nothing about another
  index or another fifteen years.
- 139 Globex sessions are shorter than 23 hours (early closes) and count as sessions; the
  regular-hours day's seventh hour is the 15:30 to 16:00 half hour.
- The hourly clock's `hours_h` on the rows is session time (a weekend adds 48 empty hours); the
  tables and `hours_traded_h` on the cards count traded hours.
- The page labels a Globex session by its trade date (`clock.label_shift_hours` 6): the
  Sunday-evening open is Monday's session on every card.
- Not in this file: fees, funding (none on futures; margin and financing are not modelled),
  points or ticks (percent of price only), a back-adjusted series, any session other than the
  two declared.

## Rebuild

    uv run python -m analysis.bench.run_bench --variant globex
    uv run python -m analysis.bench.run_bench --variant rth
    uv run python -m analysis.domino.trade_viewer serve --no-open      # runs two and three beside run one

The cache is `vectorbt-workspace/data/databento_cache/ES.n.0/` (`BENCH_CACHE` overrides the
path); each variant runs in about fifteen seconds.
