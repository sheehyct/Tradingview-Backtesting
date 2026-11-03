# TVB-44 -- the matched-pair study: same trigger, different outcome, what else was on the card -- pre-registration (CONFIRMED by the owner 2026-11-02, before any row was read)

**LABEL: CHARACTERIZATION, NO SELECTOR, NO P&L CLAIM.** The owner's direction (2026-11-02): "if we
can find correlations about why something did something once but not at another time, it could
lead to something. Take this information and see what happens on a different ticker of a
different class like bitcoin. Is there a common theme? Are we missing things like variations in
candlestick sizes preceding the move as a potential sign of volatility?" This file fixes the
question, the rows, the match, the outcomes and the variable list BEFORE any row is read, so that
whatever separates is a declared reading and not a pick. Every variable is reported, both
directions, whether it separates or not. Nothing here becomes a filter, a rule or a parameter.

## Glossary (trader terms first)

- **A unit**: one trade as the management book defines it (run one on 292 Hyperliquid perps;
  the ES bench on both day definitions): the first break of a session's, week's or month's level
  in one direction, with the pattern (2-2 reversal, 2-2 continuation, inside break, outside
  break), the week's and month's side at entry, the targets and the one-R yardstick fixed at
  the trigger.
- **The match (a cell)**: units that look the same at the trigger: same pattern, same unit
  timeframe, same direction, same week side, same month side. Inside a cell the trigger and the
  continuity say the same thing about every unit; whatever differs between the ones that paid
  and the ones that did not is something else.
- **Paid / did not**: the primary outcome is **T1 reached before the exit** (the pattern did
  what it promised, a yes or no the exit clock barely touches). The secondary outcome is the
  **exit-only book's return** (C: hold until a session closes against the trade with the week
  against it; 20-session cap), as a sign and as a size.
- **A pre-entry variable**: something known at the trigger, from the bars before it and the
  card's own fields. Nothing that happens after the trigger is a variable (the first hour, the
  travel, the exit are outcomes, not causes).
- **Terciles**: each variable is cut into its lowest third, middle third and highest third
  INSIDE each cell, so "high" means high for that pattern on that timeframe, not high overall.
- **A theme**: a variable whose terciles separate the outcome in the SAME direction on the
  crypto universe and on ES (section 7 fixes the rule). A variable that separates on one tape
  only is reported as that, never as a theme.

## 1. The question

For trades that were identical at the trigger (same pattern, same timeframe, same continuity
state), what else that was visible at the trigger differed between the ones that reached their
first target and the ones that did not? Does the same thing differ on a stock-index future and
on bitcoin and on the altcoin universe (a common theme), or is each tape its own story?

## 2. Rows and instruments (fixed)

- **Run one**: `analysis/domino/results/manage_trades.csv.gz` (179,498 units, 292 perps, as of
  2026-10-10; daily, weekly and monthly units) plus the daily bars per coin from the census
  cache (and BTC's daily bars as the crypto "index").
- **Bitcoin alone**: run one's BTC rows (one coin, two venue years: a small sample, reported
  with its intervals and never read past them).
- **ES, both days**: `analysis/bench/results/bench_globex_trades.csv.gz` and
  `bench_rth_trades.csv.gz` (4,823 and 4,788 units) plus the session bars from the tape. The
  **no-gap units** (the trigger was an available fill, `gap` null) are the primary ES rows;
  the all-units reading at the trigger is shown beside them and labelled.
- Not in this file: the hourly clock as an outcome (post-entry), the September executor book,
  the ML vessel's rows, any instrument outside these.

## 3. The match (cells)

A cell = pattern (reversal / continuation / inside / outside) x unit timeframe (D / W / M) x
direction (long / short) x week side at entry (with / against) x month side at entry (with /
against / unknown). A cell is read when it holds at least 200 units (crypto) or 50 (ES);
smaller cells are pooled into "other" and shown, never dropped.

## 4. The outcomes (fixed)

1. **T1 reached before the exit** (`reached1`): primary, binary.
2. **Exit-only return** (`ret_C`): secondary, sign and mean.
3. **The one-R book** (`ret_D`): a check that the reading is not an artefact of the target
   ladder (one R is the setup bar's own size, not a structural level).

## 5. The declared variables (a-priori; every one reported; none added after the first row is read)

Trader words first, then what is computed. All are known at the trigger.

1. **The setup bar's size** (`r_pct`: the trigger to the setup bar's far side, percent of
   price). Big setup bar or small one.
2. **The setup bar against normal** (`r_pct` divided by the average range of the 20 bars
   before the setup bar): was the setup bar an expansion or a compression of what this
   instrument normally does. The owner's "candlestick sizes preceding the move" question,
   first half.
3. **The run-up before the setup** (the average range of the 3 bars before the setup bar
   divided by the 20-bar average): was volatility already building, or quiet. The second half.
4. **How far price had already travelled** (the trigger's distance from the 20-bar low for a
   long, the 20-bar high for a short, in units of the 20-bar average range): early in the move
   or late. The discretionary "late entry".
5. **Room to the first target** (`t1` minus the trigger, in R: divided by `r_pct`): a target
   next door or a target far away. The discretionary "room ahead".
6. **A higher-timeframe level at the trigger** (`cls`: same price, near, within 1%, spread,
   plain; `stack` and `near_tf`): the daily break was also a weekly or monthly break, or stood
   alone. The domino class.
7. **The target's anchor** (`anchor`: the pattern's own magnitude, the ladder, stacked, zero)
   and **the ladder's depth** (`ladder_len`): how the targets were built.
8. **Hammer / shooter flag** (`flag`): the setup bar's shape.
9. **Volume on the setup bar** (the setup bar's volume divided by the 20-bar average volume;
   crypto and ES both carry volume).
10. **When in the week** (the entry session's position: first, middle, last session of its
    week) and, for crypto, **the day of the week** (24/7 tape: the weekend sessions are
    sessions).
11. **The index at the trigger** (crypto: BTC's day so far, up or down from its open at the
    entry day's open; ES: not applicable, it is the index). The discretionary "the index is
    breaking with it".
12. **Liquidity and venue** (`liquid`, `dex` main / xyz; crypto only).

Not declared, does not run: anything from after the trigger; any composite score; any
interaction between two variables beyond the cell itself.

## 6. Method and tables

- Per cell, per variable: the T1-reach rate in each tercile (Wilson 95% intervals) and the
  exit-only mean per tercile (normal 95% interval), the number of units in each. For flags and
  classes (variables 6, 7, 8, 10, 11, 12) the categories stand in for terciles.
- Pooled: the same per variable with the cell as the stratum (each cell's tercile difference
  weighted by its units), so a variable that separates only because big cells differ from
  small cells does not read as a separation.
- Side by side: run one (all coins), BTC alone, ES Globex no-gap, ES RTH no-gap, with the ES
  all-units columns beside them.
- **The direction of every separation is stated** (high tercile pays more, or less), with the
  size (percentage points of T1 reach; percent per trade), and the intervals. A table of every
  variable, whether it separated or not.
- A book view (the owner's standing preference): the equal-size exit-only book per tercile for
  any variable that reads as a theme, run one and ES, percent and USD at 1,000 per unit.

## 7. Kill tests and confounds (declared, equal weight)

1. **Many comparisons.** Twelve variables, three terciles, two outcomes, four tapes: something
   will separate by chance. The rule, fixed here: a variable is a **theme** only if its tercile
   direction is the same on run one (all coins) AND on at least one ES no-gap day, with the
   pooled interval clear of zero on both. Anything else is a reading on one tape.
2. **Post-entry leakage.** Every variable is recomputed from bars strictly before the entry
   session; the receipt lists the bar window of each. A variable that uses the entry bar is a
   bug.
3. **The fill on ES** (the bench's amendment 2026-11-02): the no-gap rows first; the all-units
   rows beside them and labelled.
4. **The drift.** Longs and shorts are separate cells; a theme that holds for longs only is
   reported as that.
5. **Bitcoin alone is small.** Its intervals will be wide; it is a third tape for the theme
   rule's direction only, never the deciding one.
6. **Survivorship in the altcoin universe** (run one's coins are the ones listed as of
   2026-10-10): named, not corrected.
7. **The outcome is the engine's target ladder.** The one-R book (section 4.3) is the check
   that a separation is not the ladder's construction.

## 8. Outputs

- `analysis/pairs/PAIRS_RECEIPT.md`: glossary first; the table of every variable with its
  direction, size and intervals on every tape; the themes (section 7 rule) in both directions;
  the book view; the confounds. Both directions of every reading with equal weight.
- `analysis/pairs/results/pairs_*.json` and `pairs_tables.md` (committed); the rows with the
  variables appended (ignored, regenerable).
- A `docs/ARM_LEDGER.md` card in plain terms before the first row is read.
- No viewer work in this file (the owner's reading of the viewer, 2026-11-02: clunky; a plain
  chart mode or the TradingView route is a separate decision).

## 9. Build order (each lands tested before the next; no engine change)

1. The variable builder on bars (`analysis/pairs/features.py`): hand vectors for each of the
   twelve (a compression, an expansion, a late entry, a near target, the week's first session,
   an index-down day), the bar window of each stated in its docstring.
2. The cells and the terciles (`analysis/pairs/cells.py`): a cell with a known split reads
   back its known rates.
3. The run (`analysis/pairs/run_pairs.py`) on run one, BTC, ES both days; the tables, the JSON,
   the receipt, the ledger card's numbers.

## 10. What the owner was asked to rule on

- The outcomes (section 4): T1 reached before the exit as primary, the exit-only return as
  secondary, the one-R book as the check.
- The twelve variables (section 5): add or remove before the first row is read.
- The theme rule (section 7.1): same direction on run one AND an ES no-gap day, both intervals
  clear; or another rule the owner prefers.
- Confirm no engine change and no selector: the study reads rows and bars that exist.

## 11. The ruling (2026-11-02, in one message)

- The twelve variables: **"Freeze the twelve as drafted."** Nothing is added after the first
  row is read; a later addition is a dated amendment.
- The theme rule: **"Same direction on crypto AND an ES day."** A variable is a theme only if
  its terciles separate the same way on the 292-coin run and on at least one ES clean-fill day,
  with both pooled intervals clear of zero; bitcoin alone shows the direction only.
- The outcomes and the no-engine-change, no-selector frame stand as drafted.

**Refinements fixed at build time, before the first row was read** (the prereg's wording made
precise, not changed): the "normal range" and the volume baseline are 20 bars of the UNIT'S OWN
timeframe (daily bars for a daily unit, weekly for a weekly, monthly for a monthly; a unit
without 20 prior bars has no value and is counted as absent); the run-up is the 3 bars before
the setup bar on the same timeframe; the distance travelled is from the lowest low (long) or
highest high (short) of the 20 bars ending with the setup bar, in units of the 20-bar average
range; the index variable is BTC's previous session (green or red) combined with BTC's close
against its week's open at that close (above or below), four states, known at the trigger;
"where in the week" is the day of the week for the 24/7 tape and first / middle / last session
of the week for ES.

## 12. Amendment 2026-11-02b (the in-session Codex pass on the study, folded before the commit)

Each item is a correction of the build against this file, or a limit named; none changes the
question, the match, the outcomes as ruled, the twelve as frozen or the theme rule.

1. **The reach outcome is read over the units that HAVE a first target.** The engine encodes "no
   target exists" (no unbroken level beyond the entry, `t1` null) as "not reached". A unit
   without a target is a different fact: the share of units WITH a target is reported per
   level beside the reach rate, and its pooled high-minus-low difference beside the theme table
   (not part of the rule). This changed the first run's reading of late entry (section 1 of the
   receipt says how).
2. **The liquidity flag is withdrawn** from the variables: the engine computes it from the
   snapshot's last 30 days and copies it onto every historical unit (retrospective by its own
   docstring); it is not known at the trigger. Venue (main / xyz) stays.
3. **The month side of weekly and monthly units is rebuilt from the unit's own trigger** against
   the month's open (the census's month bucket holding the entry session; equality = against;
   the first month unknown). The engine's label on those units compared the DAILY trigger, so
   the cell key as stored did not match the definition in section 3 (1,632 weekly and 372
   monthly crypto rows, 62 and 86 ES rows). The engine's label is kept on the rows as
   `m_support_engine`; daily units are unchanged.
4. **The expansion variable's numerator is `r_pct`** (trigger to far side, percent of the
   trigger) as section 5.2 wrote it; the first build used the setup bar's range over its close.
5. **The bars are trimmed to the venue era** as the engine trims them before it makes a unit
   (the venue's earlier candles are index prices); the first build let 3,164 units read a
   history the engine never saw.
6. **The ladder's depth and the nearest higher level's timeframe are reported** as variables 6
   and 7 name them; the entry-day stack (which levels broke the same day) is outcome-side and is
   not a variable.
7. **Cells below the minimum are pooled as "other" and shown** per level (they enter no pooled
   difference), as section 3 promised.
8. **Limits named:** a book level with no values reads absent, not zero; the last session of a
   tape cannot know whether its week went on (the week position at the very end of a tape); the
   intervals assume independent units and the units overlap in time and across coins (no
   clustered interval was computed).
