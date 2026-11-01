# TVB-43 -- the one-instrument bench: the management book on ES at the Globex day -- pre-registration (DRAFT)

**LABEL: CHARACTERIZATION, NO STRATEGY, NO P&L CLAIM. STATUS: DRAFT, awaiting the owner's word.
Nothing below runs on data until the owner confirms the arms in this file (standing rule: prereg
before code, declared variants, never a pick-the-winner). Definitions are fixed here BEFORE any
outcome is read.**

- Drafted: 2026-11-01 (TVB-43) by the lead, after the TVB-42 audit fold and stage 3 of the viewer
  contract. The owner's rulings it rests on: the Globex 18:00 ET roll is "the day" for any
  futures bench (2026-10-30); the bench is the next design item after the viewer row contract
  (TVB-42 close-out); every arm is declared a-priori and restated in trader terms before code.
- What this is: run one's rules (the STRAT-management book, pre-registered 2026-10-11 and run on
  292 Hyperliquid perps over roughly two venue years) read on ONE deep, session-traded
  instrument with fifteen years of tape. A second tape for the same books. It asks whether the
  book's readings (targets get reached; the setup-bar stop is what loses; the clocks differ)
  look the same on a tape with a bell, a roll and a weekend, or not. Both answers are findings.
- What this is NOT: a new strategy, a parameter search, a promotion. No book is added; no book
  is tuned. The continuity ladder below is a SPLIT of recorded context, not a new engine path.

## Glossary (trader terms first)

- **Session**: one Globex trading day of ES, opening 18:00 ET (Sunday through Thursday) and
  closing 17:00 ET the next afternoon, with the 17:00 to 18:00 maintenance break between
  sessions. A session is named by its trade date (the Monday session opens Sunday evening).
- **The day**: the session (owner's ruling 2026-10-30). Daily close = the 17:00 ET settlement
  close of the session. Daily open = the 18:00 ET open.
- **The week**: Sunday 18:00 ET through Friday 17:00 ET; on trade dates, Monday through Friday.
  The week's open is the Sunday-evening open. **The month**: the sessions whose trade date falls
  in the calendar month; the month's open is its first session's open.
- **Roll**: ES.n.0 is a continuous contract stitched by open interest and NOT back-adjusted; on a
  roll session the price series jumps from one contract to the next. That jump is a contract
  switch, not a move.
- **Run one**: the management book on Hyperliquid, `management-book-20261010` in the viewer.
  **Run two**: this bench on the Globex day. **Run three** (declared pair): the same book on the
  RTH day.
- **Book, card, headline, how it left**: as in `analysis/domino/viewer/CONTRACT.md` section 1.

## 1. Instrument and data (fixed)

- `ES.n.0` (CME E-mini S&P 500, continuous front month by open interest, unadjusted), Databento
  GLBX MDP3, 1-minute source bars 2011-01-02 23:00 UTC to 2025-12-31 21:59 UTC (5,231,844 rows),
  cached in `vectorbt-workspace/data/databento_cache/ES.n.0/` as `source_1m.parquet` (with the
  `symbol` and `instrument_id` columns, so every roll session is known exactly) and resampled
  there to `5m 15m 30m 60m 4H 1D 1W 1M` parquet files, each with a `.meta.json`
  (`source_version: resampled-from-source_1m-v1`, written 2026-04-21).
- The cache's `1D` bar IS the Globex session: 3,859 bars opening 22:00 UTC in summer and 23:00
  UTC in winter (18:00 ET both), 2011-01-02 to 2025-12-30. `1W` opens Sunday evening; `1M` on
  the first session of the month. The 1-minute tape has the daily 17:00 to 18:00 ET gap and the
  15-minute 16:15 to 16:30 ET break (seen 2024-07-09: 20:59 to 22:00 UTC and 22:28 to 22:30 UTC).
- Sample: every complete session from the first complete week of January 2011 to 2025-12-30.
  No venue era (one instrument, one venue). No liquidity screen (the card's `liquid` flag is
  always true; ES is the deepest equity-index future).
- Hourly bars for the hourly clock: the cache's `60m` bars, grouped by session (a session's
  hours span two UTC dates).

## 2. Mechanics that differ from run one (declared, structural, not knobs)

Everything not listed here is run one's rule, verbatim (`docs/experiments/tvb37_management_book_prereg.md`,
amendments A2 and A3 as applied in `analysis/domino/manage.py`).

1. **The session calendar replaces the 24/7 calendar.** Run one's engine treats a day as a
   calendar day and a week as complete only when all seven days are present (the census's
   `aggregate` completeness; `gap_days` as a data-quality exclusion). On a session tape there
   is no Saturday, no Sunday session of its own, and a holiday removes a session. So: the unit of
   time is the session; a week is the Monday-through-Friday trade dates (one Globex week); a
   month is the trade-date month; a bucket is COMPLETE when its last session is at or before the
   data end and its sessions are consecutive in the tape (a holiday week of four sessions is
   complete; a week cut by the data end is not). The 24/7 `gap_days` exclusion does not apply.
   The crypto tape must still reproduce run one byte-identically through the adapted code (every
   calendar day IS a session there): that is the regression test, run before any ES row exists.
2. **Caps count sessions.** The 20-day cap = 20 sessions after the entry session; "five bars of
   the unit" = 5 sessions / 5 weeks / 5 months; the long cap = 20 bars of the unit.
3. **The hourly clock groups the cache's 60-minute bars by session**, not by UTC date; the
   entry hour is the first hour strictly through the level inside the entry session; the maintenance
   hour is absent. The 15-minute 16:15 break leaves the 16:00 ET hour short; it is a bar like
   any other.
4. **The level is the previous complete session's high or low** (daily unit), the previous
   complete Globex week's (weekly), the previous complete trade-date month's (monthly), exactly
   as run one reads them off its buckets.
5. **Roll sessions are flagged, never dropped.** A unit whose entry session, or any session in
   its headline window, is a roll session carries `extras.roll` (`entry`, `window`, or null).
   Every table in the receipt splits by that flag. The price gap at a roll can break a level or
   fill a target by contract switch alone; the split shows how much of the book that is.
6. **Times on cards are real UTC opens** (the 18:00 ET open is 22:00 or 23:00 UTC), as the
   contract requires (CONTRACT.md section 4). The viewer gains a run-declared session label
   (`clock.label_shift_hours`, 6 for Globex) so the page calls the Sunday-evening open "Monday"
   and keys its day index by trade date; and it uses a run's shipped weekly and monthly bars
   (`1w`, `1M`) when present instead of aggregating Monday-00:00-UTC weeks from the dailies.
   Both are page changes (Plan Mode OFF), no engine change.
7. **Returns are percent of price, equal size, no fees, no leverage, no margin arithmetic**, as
   run one. Points and ticks are not reported here (a later receipt may add them beside percent).

## 3. Books (run one's seventeen, unchanged)

Headline C (exit only: a session close against the trade with the week against it at that
close; 20-session cap). A (all out at T1), B (hold through T2), D (one R or the exit), D5 (one R
or the exit inside five bars of the unit), ref (the chance book: one R or the setup-bar stop,
marked at bar five). Grouped: the hourly clock (C_h, A_h, D_h), under water (C_u, A_u, D_u), the
own clock (C_own, A_own; weekly and monthly units), the long cap (C_long, A_long), the measured
move (A_mm). Rules verbatim from `analysis/domino/run_export.py` `BOOKS`. No book is added here.

## 4. Declared variants (all shown side by side; none picked)

- **V0, the Globex day (run two).** Definitions 1 to 7 above. The headline run of this file.
- **V1, the RTH day (run three), the declared pair.** The same book with "the day" = the regular
  session, 09:30 to 16:00 ET, built from the 1-minute tape (the daily open 09:30, the daily close
  16:00; the week Monday to Friday RTH; the hourly clock on RTH hours only). The standing
  mirror rule (every perp test gets a paired regular-hours run; state the confound) applied to
  one instrument with two day definitions. Read beside V0 by role in the viewer's Compare
  across runs. V1 is NOT the owner's ruling for "the day"; it is the paired reading.
- **The continuity ladder, as a SPLIT of V0's recorded context** (charter S3.1 ablation ladder,
  no new engine path): C0 = every unit (the book as is); C1 = units whose week's side at entry
  is with the trade (`context.week_side == with`); C2 = C1 and the month's side with the trade
  too. Each rung is reported as a subset of the same rows, with the complement beside it, so
  the ladder reads as "what the gate would have removed" in both directions. No rung is a
  recommendation.

Anything else (an hourly-close entry, a points-based stop, a session-open gate, a different
cap) is NOT in this file and does not run.

## 5. Outputs

- Run two (and run three) exported in the viewer contract and imported beside run one; the
  page's Compare across runs lines them up by role (headline against headline, the target books
  by order, the chance book against the chance book).
- `analysis/domino/BENCH_RECEIPT.md`: glossary first; then, for V0 and V1 each: the counts
  (units by bar and pattern, roll-flagged units), reach rates, the books in percent per trade
  with the equal-size curve, the clocks, the continuity ladder as splits, longs and shorts
  separately, the roll split; every table on the same rows as run one's receipt where the row
  exists. Both directions of every reading with equal weight.
- An `docs/ARM_LEDGER.md` card for the bench in plain terms, before the engine runs on ES.

## 6. Kill tests and confounds (declared, equal weight)

1. **The calendar adaptation itself is a bug class.** Before any ES row: the crypto cache run
   through the session-calendar code path reproduces `analysis/domino/results/manage.json`
   byte-identically (the daily headline stays byte-identical, standing rule). Hand vectors: a
   Globex week with a holiday (Good Friday 2024-03-29: four sessions, complete); the week
   containing the data end (incomplete); a Sunday-evening open landing on Monday's trade date; a
   session's hours spanning two UTC dates grouped as one session.
2. **Roll gaps** (section 2.5): the roll split is read before anything else.
3. **One instrument, one era.** ES rose from about 1,260 to about 6,900 over the sample. An
   equal-size percent book on a single rising index is drift-dominated; the receipt reports
   longs and shorts separately and names the drift, and a reading that holds only for longs is
   reported as that.
4. **Hours and sessions that are short** (holiday half-sessions, the 16:15 break): counted,
   flagged in the receipt, not dropped.
5. **The page's labels**: a Sunday-evening open is Monday's session; a run's `label_shift_hours`
   governs the label; an off-by-one in the shift would misdate every card by a day and is a
   hand-vector test on the viewer side.

## 7. Build order (each lands tested before the next; Plan Mode for item 2)

1. Viewer: shipped weekly / monthly bars and the session label shift (page only).
2. Engine: the session calendar as a declared parameter of the census's bucketing and the
   manage walker's hour grouping, default = the 24/7 calendar; the byte-identical regression on
   the crypto cache passes before step 3. **This is an engine change: the owner's word first.**
3. Loader: `analysis/bench/es_tape.py` reads the cache's `1D` and `60m` parquet (and `source_1m`
   for roll sessions and for the RTH day), emits the census bar format with real UTC opens and
   the trade-date mapping.
4. The run: V0 then V1, exported as runs two and three, imported, viewed; the receipt; the
   ledger card.

## 8. What the owner is asked to rule on (one message, any order)

- Confirm the arms: V0 (ruled day), V1 (the RTH pair), the C0 / C1 / C2 split. Strike any.
- Confirm the roll handling: flag and split, never drop.
- Confirm the engine change in section 2.1 may be built (Plan Mode), with the byte-identical
  crypto regression as its gate.
