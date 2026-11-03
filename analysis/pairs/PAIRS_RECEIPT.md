# The matched-pair study: same trigger, different outcome, what else was on the card (receipt)

**LABEL: CHARACTERIZATION, NO SELECTOR, NO P&L CLAIM.** Pre-registration
`docs/experiments/tvb44_matched_pairs_prereg.md` (the twelve variables and the theme rule frozen
by the owner 2026-11-02 before any row was read; section 12, the in-session Codex pass on the
build, folded the same day before this receipt). Generated 2026-11-02 by
`analysis/pairs/run_pairs.py`; the full tables are `analysis/pairs/results/pairs_tables.md`
(every variable, every tape, every level, the pooled differences, the "other" group, the book
view), the summary `pairs.json`, the per-cell readings `pairs_cells.json` and the rows with the
variables `pairs_rows_*.csv.gz` (the last two regenerable, ignored). Every reading below is
shown in both directions; a separation is a path worth naming, a non-separation a path worth
closing; nothing here is a filter, a rule or a recommendation.

**What the Codex pass changed before this receipt was written.** The first run read "T1
reached" the way the engine stores it, where a unit with NO first target at all (no unbroken
level beyond the entry) counts as "not reached". That made "late entry reaches less" look like
a finding when most of it was "late entry has no structural target ahead". The reach outcome is
now read over the units that HAVE a target, and the share with a target is its own reading,
beside it, on every table. The liquidity flag was withdrawn (retrospective), the month side of
weekly and monthly units rebuilt from the unit's own trigger, the expansion variable's numerator
set to the engine's `r_pct`, the bars trimmed to the venue era, the ladder's depth and the
nearest level's timeframe added, small cells shown as "other". The themes changed; the
candle-size answer did not.

## Glossary (trader terms first)

- **A unit**: one trade of the management book (run one on 292 Hyperliquid perps, two venue
  years; the ES bench on the Globex day and the regular-hours day, fifteen years): the first
  break of a session's, week's or month's level in one direction.
- **A cell (the match)**: units that looked the same at the trigger: same pattern (2-2
  reversal, 2-2 continuation, inside break, outside break), same unit timeframe, same direction,
  the week and the month on the same side at entry (the month's side read from the unit's own
  trigger). Inside a cell the trigger and the continuity say the same thing about every unit.
- **Has a target**: the engine found a first target for the unit (the pattern's own magnitude
  or an unbroken weekly / monthly level beyond the entry). A unit with none is "open air": no
  structural level ahead to aim at. Read per level as its own fact.
- **Reached T1**: among the units WITH a target, the first target touched before the exit-only
  book's exit. The primary outcome. **Exit only (C)**: the management book's headline, hold until
  a session closes against the trade with the week against it, 20-session cap; percent of price
  per trade, equal size, no fees; read over every unit. **One R**: one setup-bar range from the
  trigger, or the exit; the check that a reading is not the target ladder's construction.
- **Low / mid / high**: each numeric variable cut into thirds INSIDE each cell, so "high" means
  high for that pattern on that timeframe in that direction.
- **High minus low, pooled**: the top third's outcome minus the bottom third's, cell by cell,
  weighted by the cell's units, with a normal 95% interval; in percentage points (pp) for the
  shares, in percent per trade for the books.
- **A theme (the owner's rule)**: the pooled high-minus-low difference in T1 reach has the same
  sign on the 292-coin run and on at least one ES clean-fill day, both intervals clear of zero.
  Anything else is a reading on one tape.
- **Clean-fill (ES)**: the units whose session did not open past the trigger (the bench's
  amendment 2026-11-02); the all-units reading is in the tables beside them.
- **The variables**, all known at the trigger: the setup bar's size (`r_pct`, percent of the
  trigger); the setup bar against the instrument's normal range (the 20 bars before it); the
  run-up (the 3 bars before the setup bar against the 20 before them); how far price had
  already run (the trigger from the 20-bar low for a long, the 20-bar high for a short, in
  average ranges); room to T1 in R; a weekly or monthly level at the trigger (the domino class)
  and the nearest level's timeframe; how the targets were anchored and how deep the ladder is;
  hammer or shooter; volume on the setup bar against normal; where in the week; bitcoin's
  previous day for crypto (green or red, above or below its week's open); venue. Bar-based
  variables use the unit's own timeframe. Liquidity was withdrawn (not known at the trigger);
  the entry-day stack is outcome-side and is not a variable.

## What ran

| | 292 coins | bitcoin alone | ES Globex clean | ES RTH clean |
|---|---:|---:|---:|---:|
| units with an exit-only outcome | 178,203 | 1,403 | 4,548 | 2,842 |
| of which with a first target | 152,255 | 1,196 | 3,402 | 2,164 |
| cells read (at 200 / 50 / 50 units) | 62 to 66 | 9 | 22 to 23 | 19 to 20 |
| "other" (cells below the minimum, shown, not pooled) | 35 cells, 1,652 units | | 51 cells, 666 | 47 cells, 511 |
| month side of weekly / monthly units relabelled from the unit's own trigger | 1,971 | 17 | 59 | 78 |
| units without a 20-bar history (bar variables absent) | 9,032 | 0 | 55 | 34 |

Bitcoin alone is nine cells and reads for direction only.

## 1. The answer, both ways

**Three variables met the theme rule; one of them is the engine's construction and the other
two say less than their label.**

- **Late entry (how far price had already run) is, first of all, "no target ahead".** The late
  third has a first target far less often on every tape: 292 coins 75.7% against 94.6% for the
  early third, bitcoin 65% against 97%, ES Globex 58% against 90%, ES RTH 61% against 88%. When
  a target exists, the late third reaches it slightly MORE often (+2.1 pp on the 292 coins,
  +8.9 on Globex, +6.6 on RTH: the theme by the rule). And the exit-only book is worse when late
  on the 292 coins (-0.31 per trade) and on the Globex day (-0.19), inside its interval on the
  regular-hours day (-0.12). The three facts together, in trader words: a late entry is usually
  into open air; when there is a level ahead it gets hit; the trade still makes less.
- **An expanded setup bar (against the instrument's normal range) reaches its target a little
  more often on every tape** (+3.3 pp on the 292 coins, +6.3 and +6.6 on ES): the one clean
  reach theme. On the 292 coins it also has fewer targets (80.5% against 90.5%) and makes less
  money (-0.59 per trade; the shorts -1.58, the longs +0.47); on ES it makes no difference to
  the money either way. Reach and money disagree on crypto, and only reach moves on ES.
- **Room to the first target is a theme by the rule and a construction in substance**: a nearer
  target is reached more because it is nearer (76 to 81 percent against 24 to 29 on every tape).
  Its content is the books that never use T1: on the 292 coins a near first target (a large setup
  bar against the distance to the next level) is the better trade on both (-0.74 exit only, -0.57
  one R, high against low); on ES both read a few hundredths the other way, inside their
  intervals. A crypto reading, not a common one.

**The owner's candle-size question keeps its two-tape answer.** On the 292 coins, volatility
building into the setup (the three bars before the setup bar running hot against the twenty
before them) reaches its target less (-9.9 pp, longs -9.3 and shorts -10.5, daily -9.3, weekly
-15.5, monthly -28.9) and makes less (-0.67 per trade; +0.17 on the quiet third, -0.54 on the
loud third). A big setup bar makes less too (-1.08 per trade, the largest money effect of all),
and heavy volume on it (-0.33). On ES none of the three moves reach or money. Candle sizes
before the move are information on the altcoin tape and noise on the index future.

**Open air is not bad money on crypto.** Units with no target at all (ladder depth 0: 14% of the
292-coin units, 22% of ES) read +0.38 per trade on the exit-only book on the 292 coins, better
than the average unit (-0.05); on ES -0.17 and -0.03. "No level ahead" means "no target to be
stopped at" on the altcoin tape; the exit-only book rides it.

## 2. The three themes, and the two readings beside them

### How far price had already run (`v_travel`)

| tape | level | n | has a target | T1 reached (of those) | C exit only | | pooled high minus low: has a target | reached | C | one R |
|---|---|---:|---|---|---|---|---|---|---|---|
| 292 coins | low / mid / high | 55,167 / 55,145 / 55,123 | 94.6 / 88.1 / 75.7% | 48.0 / 50.2 / 50.9% | -0.03 / -0.08 / -0.30 | | -18.7 pp [-19.0, -18.4] | +2.1 pp [+1.5, +2.7] | -0.31 [-0.47, -0.15] | -0.24 [-0.34, -0.14] |
| bitcoin | low / mid / high | 243 / 242 / 237 | 96.7 / 88.8 / 65.3% | 54.7 / 55.3 / 54.6% | +0.08 / -0.02 / +0.44 | | -31.4 pp [-37.1, -25.8] | +0.2 pp [-9.1, +9.6] | +0.36 [-0.65, +1.37] | +0.18 [-0.45, +0.80] |
| ES Globex clean | low / mid / high | 1,298 / 1,289 / 1,282 | 89.8 / 73.5 / 58.2% | 51.8 / 56.9 / 64.3% | +0.01 / -0.03 / -0.17 | | -31.6 pp [-33.8, -29.4] | +8.9 pp [+4.5, +13.3] | -0.19 [-0.32, -0.05] | -0.14 [-0.25, -0.02] |
| ES RTH clean | low / mid / high | 782 / 772 / 769 | 88.4 / 74.6 / 60.5% | 50.7 / 56.0 / 60.0% | -0.02 / -0.07 / -0.15 | | -27.9 pp [-30.6, -25.1] | +6.6 pp [+0.9, +12.3] | -0.12 [-0.29, +0.05] | -0.12 [-0.25, +0.02] |

By direction and by unit (pooled high minus low; has a target, reached, C):

| | longs | shorts | daily units | weekly units | monthly units |
|---|---|---|---|---|---|
| 292 coins | -20.5 pp; +3.8 pp; C +0.29 [+0.02, +0.56] | -17.0 pp; +0.4 pp [-0.4, +1.3]; C -0.87 [-1.04, -0.70] | -18.3; +2.1; C -0.32 | -23.4; +1.7 [-0.5, +3.9]; C -0.40 [-0.89, +0.10] | -4.2; +15.8 [+6.1, +25.5]; C +1.83 [-0.01, +3.67] (4 cells) |
| ES Globex clean | -36.2 pp; +10.5 [+4.3, +16.7]; C -0.25 [-0.42, -0.08] | -25.4 pp; +7.2 [+0.9, +13.4]; C -0.10 [-0.33, +0.13] | -32.0; +8.6; C -0.20 | -33.7; +11.8 [-5.0, +28.6]; C -0.10 | no cell |
| ES RTH clean | -31.3 pp; +9.7 [+1.4, +18.0]; C -0.05 [-0.26, +0.16] | -23.4 pp; +3.5 [-4.3, +11.4]; C -0.21 [-0.48, +0.06] | -27.9; +6.6; C -0.12 | -32.0; +6.6 [-13.0, +26.2]; C -0.16 | no cell |

**Both ways.** "No target ahead" when late holds on every tape, both directions, daily and
weekly units, by twenty to thirty-six points. "Reaches the target it has" holds on every tape
in sign and is clear of zero on the 292 coins and both ES days pooled; by direction it is clear
for crypto longs and ES longs and inside the interval for shorts on three of four lines. The
money splits: the late crypto SHORT is the loser (-0.87 per trade) while the late crypto LONG
makes more (+0.29) with far fewer targets (the drift inside the cell); on the Globex day the
late long is the loser (-0.25). The equal-size exit-only book at 1,000 USD a unit: 292 coins
early +238 USD, mid -41,783, late -165,560 (55,000 units each); ES Globex clean +159, -51,
-2,282; ES RTH clean -182, -854, -1,283; bitcoin alone +360, +204, +2,359 (the money goes the
other way on 430 units, interval through zero).

### The setup bar against the instrument's normal range (`v_setup_vs_norm`)

| tape | level | n | has a target | T1 reached (of those) | C exit only | | pooled: has a target | reached | C | one R |
|---|---|---:|---|---|---|---|---|---|---|---|
| 292 coins | low / mid / high | 55,167 / 55,145 / 55,123 | 90.5 / 87.6 / 80.5% | 47.8 / 49.9 / 51.1% | +0.16 / -0.01 / -0.55 | | -9.9 pp [-10.2, -9.5] | +3.3 pp [+2.7, +3.9] | -0.59 [-0.75, -0.44] | -0.47 [-0.57, -0.37] |
| bitcoin | low / mid / high | 243 / 242 / 237 | 92.6 / 85.9 / 72.4% | 53.3 / 53.2 / 59.8% | +0.30 / +0.04 / +0.14 | | -20.2 pp [-26.2, -14.2] | +5.3 pp [-3.8, +14.3] | -0.16 [-1.15, +0.83] | +0.08 [-0.56, +0.72] |
| ES Globex clean | low / mid / high | 1,298 / 1,289 / 1,282 | 73.8 / 74.3 / 73.6% | 52.8 / 57.1 / 57.3% | -0.04 / -0.09 / -0.06 | | -0.2 pp [-2.9, +2.4] | +6.3 pp [+2.1, +10.6] | -0.02 [-0.16, +0.12] | -0.01 [-0.13, +0.10] |
| ES RTH clean | low / mid / high | 782 / 772 / 769 | 75.2 / 74.6 / 73.9% | 50.6 / 57.6 / 54.7% | -0.11 / -0.06 / -0.07 | | -1.3 pp [-4.5, +1.9] | +6.6 pp [+1.1, +12.2] | +0.04 [-0.12, +0.21] | -0.02 [-0.15, +0.12] |

By direction: 292 coins longs reached +6.6 pp, C +0.47 [+0.20, +0.73]; shorts reached +0.0 pp,
C -1.58 [-1.75, -1.41]. ES Globex longs reached +1.1 pp [-4.9, +7.2], shorts +11.5 [+5.5, +17.5];
ES RTH longs +1.1, shorts +11.8 [+4.1, +19.5]; ES money inside the interval on every line. The
equal-size book on the 292 coins: +62,057 USD on the modest third, -265,496 on the expanded third.

**Both ways.** The reach theme is carried by crypto longs and ES shorts; the money on crypto is
carried the other way by the shorts (an expanded setup bar before a short is the losing trade
on the altcoin tape, a point and a half per trade) while the longs make more. The one R book
agrees with the exit-only book on the 292 coins (-0.47) and reads nothing on ES.

### Room to the first target, in R (`v_room_r`)

| tape | level | n | T1 reached | C exit only | | pooled: reached | C | one R |
|---|---|---:|---|---|---|---|---|---|
| 292 coins | low / mid / high | 50,452 / 50,440 / 50,412 | 76.2 / 48.1 / 23.8% | +0.31 / -0.01 / -0.50 | | -51.3 pp [-51.8, -50.8] | -0.74 [-0.91, -0.57] | -0.57 [-0.67, -0.47] |
| bitcoin | low / mid / high | 205 / 201 / 198 | 75.6 / 57.9 / 30.6% | -0.31 / +0.54 / +0.16 | | -44.2 pp [-52.1, -36.4] | +0.41 [-0.58, +1.40] | +0.34 [-0.26, +0.94] |
| ES Globex clean | low / mid / high | 966 / 955 / 949 | 80.5 / 55.3 / 29.1% | -0.11 / -0.05 / -0.04 | | -49.8 pp [-53.4, -46.2] | +0.06 [-0.10, +0.22] | +0.06 [-0.07, +0.18] |
| ES RTH clean | low / mid / high | 584 / 581 / 574 | 77.3 / 55.4 / 28.3% | -0.14 / -0.00 / -0.12 | | -47.3 pp [-52.1, -42.6] | +0.02 [-0.18, +0.22] | +0.11 [-0.04, +0.26] |

Every unit here has a target by definition. The reach difference is the variable's construction
and is reported as such. The equal-size book on the 292 coins: +143,748 USD on the near third,
-239,946 on the far third; on ES -1,108 / -612 / -488 and -917 / -297 / -950.

## 3. The candle-size question (the setup bar, the run-up, the volume)

Pooled high minus low: has a target; reached; C exit only:

| | 292 coins | bitcoin | ES Globex clean | ES RTH clean |
|---|---|---|---|---|
| the setup bar's size (`v_setup_pct`) | -7.6 pp; -0.8 pp [-1.4, -0.2]; C -1.08 [-1.24, -0.92] | -20.2 pp; -0.5 pp; C -1.32 [-2.28, -0.36] | +6.2 pp [+3.7, +8.7]; -2.6 pp [-6.9, +1.7]; C -0.03 | +3.2 pp [+0.1, +6.3]; -2.8 pp [-8.3, +2.7]; C -0.12 |
| the run-up, 3 bars before against 20 (`v_runup`) | -7.6 pp; -9.9 pp [-10.5, -9.3]; C -0.67 [-0.82, -0.51] | -14.4 pp; -9.5 pp [-18.7, -0.3]; C -0.48 | +2.8 pp [+0.2, +5.4]; +0.2 pp [-4.0, +4.5]; C -0.02 | +0.9 pp; -2.9 pp [-8.3, +2.5]; C -0.06 |
| volume on the setup bar against normal (`v_vol_vs_norm`) | -8.4 pp; +0.6 pp [+0.0, +1.2]; C -0.33 [-0.49, -0.17] | -18.1 pp; +0.4 pp; C +0.30 | -2.8 pp [-5.5, -0.1]; -1.3 pp; C -0.05 | -2.6 pp; -1.4 pp; C +0.07 |

The run-up on the 292 coins by level: has a target 89.4 / 87.0 / 82.0%, reached 54.2 / 49.3 /
44.7%, exit only +0.17 / -0.03 / -0.54. The setup bar's size on ES by direction: the big-bar
long has a target more often (+22 pp on both days) and reaches it less (-11.1 pp [-17.2, -5.1]
Globex, -12.3 RTH); the big-bar short the reverse (-16 pp, +6 pp inside the interval); money flat.

**Both ways.** On the altcoin universe a quiet approach pays and a loud one does not: a modest
setup bar after calm bars, with ordinary volume, is the better trade on every book; a big bar
after a volatile run-up with heavy volume is the worse one, by about a point per trade on the
exit-only book for the bar's size alone, consistent across longs and shorts and across daily,
weekly and monthly units. On the index future the same three variables leave the money where it
was, and the one reach reading there (a big setup bar before a long reaches less) is a single
direction on a single variable.

## 4. The rest: the level at the trigger, the anchor and the ladder, the flag, the week, the index, venue

Standardized to the cell sizes (per level: units, has a target, reached, C exit only):

- **A weekly or monthly level at the trigger (the domino class).** 292 coins: near (a higher
  level within 0.25%) 2,651 units, 95.1% have a target, 89.1% reach it, +0.15; within 1% 8,314,
  95.4%, 77.2%, +0.09; plain 141,789, 88.9%, 48.9%, -0.05; spread 15,484, 66.7%, 43.7%, +0.25;
  exact shared (the daily and the weekly level at one price) 8,233, 48.7%, 27.1%, +0.76. ES
  Globex clean: near 449, 91.1%, 82.9%, -0.13; within 1% 919, 91.8%, 64.7%, +0.03; plain 2,030,
  70.0%, 45.2%, -0.09; exact shared 436, 41.5%, 32.5%, -0.03. The target pattern is the ladder's
  construction (a near level IS the first target; a shared level pushes T1 to the next one, or
  leaves none) and reads the same on both tapes. The money is not construction: on the 292
  coins the exact-shared break earns +0.76 per trade on the exit-only book against -0.05 for a
  plain break (run one's "stacked" reading again); on ES it earns nothing. A crypto reading.
- **The nearest level's timeframe.** 292 coins: none (no higher level near) 20,870 units, 39.1%
  have a target, 62.1% reach it, +0.35; a weekly level 108,075, 97.8%, 53.9%, -0.03; a monthly
  level 23,259, 99.3%, 37.4%, -0.36; the daily level alone 24,347, 66.1%, 41.0%, -0.08. ES Globex:
  none 653, 32.4%, 55.8%, -0.43; weekly 2,143, 90.1%, 63.1%, -0.04; monthly 517, 98.0%, 43.0%,
  +0.07. A monthly level as the nearest target is reached least on both tapes (it is far);
  "no level near" is good money on crypto and bad on ES.
- **How the targets were anchored, and the ladder's depth.** The pattern's own magnitude always
  has a target and reaches it 64 to 67% on every tape; the ladder 38 to 50%; money flat. Ladder
  depth 0 (no target) is 14% of the 292-coin units at +0.38 per trade, 22% of ES at -0.17 and
  -0.03; depth 3 reaches 69 / 69 / 65% and makes +0.12 / -0.08 / -0.12.
- **Hammer or shooter.** 292 coins: flagged against none reached -3.5 pp [-4.7, -2.2], has a
  target +2.5 pp, money +0.13 [-0.20, +0.47]; ES: nothing clear. No money reading anywhere.
- **Where in the week.** 292 coins (day of the week): Sunday entries have a target 82.0%, reach
  40.8%, -0.45 on the exit-only book; Saturday 83.3%, 45.4%, -0.10; Monday 88.0%, 54.9%, -0.23;
  Thursday 85.5%, 54.6%, +1.25; Friday 84.9%, 50.3%, +0.54. The weekend sessions reach less and
  the money swings by weekday more than any other category here, both ways. ES (first / middle
  / last session of the week): reached 55.5 / 56.4 / 54.1% on the Globex day, money -0.06 /
  -0.11 / +0.05; nothing on the regular-hours day either. A crypto reading.
- **The index at the trigger (crypto only; bitcoin's previous day).** Green and above its
  week's open: 65,291 units, 49.9% reach, +0.56 per trade; red and below: 60,433, 49.9%, -0.76;
  green-below 23,479, 45.7%, -0.13; red-above 27,264, 51.5%, +0.21. The reach rate does not
  move; the exit-only book moves by 1.3 points per trade between bitcoin's best and worst state.
  The variable as declared is not direction-relative (a short after a red bitcoin day is "with"
  it), so this is bitcoin's state lifting or sinking every trade, not a continuity read; a
  direction-relative version would be a dated amendment.
- **Venue (crypto only).** Main dex against xyz: reached +0.0 pp, has a target +1.7 pp, exit only
  +0.47 [+0.34, +0.60] and one R +0.35 per trade: the main-dex units earn half a point per trade
  more than the xyz units in the same cells. A venue reading.

## 5. What this says, both ways

- **The one fact that holds on every tape is "late entry is into open air".** How far price
  had already run predicts whether a structural target exists at all, by twenty to thirty-six
  points, on the 292 coins, on bitcoin and on both ES days. When a target exists the late entry
  reaches it a little more often; the exit-only book is worse when late on crypto and on the
  Globex day. "Early in the move" stays the common theme in money terms, with the caveat that
  the money difference on the regular-hours day sits inside its interval.
- **Before the trigger, on the altcoin universe, there is information in the bars**: a quiet
  run-up, a modest setup bar, ordinary volume, a near first target, a shared higher level, a
  weekday, bitcoin's day, the main dex. Each separates the exit-only book clearly in its own
  direction. Several are the same thing seen twice (a modest setup bar and a near target in R
  are one fact; a quiet run-up and a modest setup bar are neighbours).
- **On the index future the bars before the trigger say almost nothing about money.** Late
  entry is the one variable with a clear exit-only difference there (Globex). The expanded
  setup bar reaches more on ES without making more. Candle sizes before the move are a crypto
  reading.
- **Reach and money are different questions.** An expanded setup bar reaches its target more
  on every tape and makes less on crypto; open air reaches nothing and makes more on crypto.
  A selector built on "reached T1" would be built on the ladder, not on the trade.
- **Paths, not rules.** "Early in the move" is worth naming as a declared arm on both tapes
  (as a split of the management book beside its complement); "a loud run-up into the setup",
  "an expanded setup bar before a short" and "the weekend sessions" as kill tests on crypto;
  a direction-relative bitcoin variable as an amendment. None has been run as an arm.
- **What did not separate anywhere**: the hammer or shooter flag on money, the anchor beyond
  its construction, the week's position on ES, the setup bar's shape on ES money.

## 6. Confounds and limits, named

- **Many comparisons.** Fourteen variables as built, three levels, four outcomes, six tapes.
  The theme rule is the guard; the crypto-only readings above are readings, and the ones a few
  tenths wide should be read as such.
- **Construction.** Room to T1, the domino class, the nearest level's timeframe, the anchor and
  the ladder's depth separate the reach rate by how the target ladder is built; their money
  readings are the content. The one-R book is the check and agrees with the exit-only book on
  the 292 coins.
- **The "no target" encoding** was the first run's error and is now a reading of its own; a
  variable that predicts "no target" (late entry, a big setup bar, heavy volume on crypto) is
  not a variable that predicts "misses the target".
- **Overlap between variables.** The setup bar's size, the setup bar against normal, room in R
  and the run-up are correlated by construction (R is the setup bar). No interaction was
  declared and none is read.
- **The drift.** Longs and shorts are separate cells; the late-long reading on crypto (fewer
  targets, money up) is the drift inside the cell, and the expanded-bar reading splits by
  direction on both tapes.
- **Bitcoin alone** is nine cells and about 240 units a level; its money readings cross zero on
  every theme and are not read past their direction.
- **The fill on ES** (the bench's amendment): clean-fill units first; the all-units columns in
  the tables agree in sign on every variable.
- **The intervals assume independent units**; the units overlap in time and across coins, so
  the intervals are descriptive, not calibrated (no clustered interval was computed).
- **The altcoin universe** is the coins listed as of 2026-10-10 (survivorship, not corrected),
  on their venue-era bars as the engine saw them.
- **The last session of a tape** cannot know whether its week went on (the week position at the
  tape's end); a limit, not a leak.
- **Nothing here is out of sample.** The variables were frozen before the rows were read; the
  rows are the same rows every receipt in this repo has used.

## Rebuild

    uv run python -m analysis.pairs.run_pairs      # about two and a half minutes

Reads `analysis/domino/results/manage_trades.csv.gz`, the census's daily cache (as of
2026-10-10, venue era), `analysis/bench/results/bench_*_trades.csv.gz` and the ES tape; writes
`analysis/pairs/results/`.
