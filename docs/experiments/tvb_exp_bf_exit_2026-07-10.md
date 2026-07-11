# TVB-EXP-BF1 -- BF-Deviation Exit Ablation (one-off, 2026-07-10)

**Status:** COMPLETE (Claude run; GPT parallel run pending -- see
`docs/guides/GPT_BF_EXIT_EXPERIMENT_PROMPT.md`).
**Context:** user-directed live-trading side session, outside the TVB-11 pre-reg
queue. The user trades these signals live with real money and explicitly accepted
slight overfitting; this is characterization, not promotion. No cell below is a
deployment recommendation.

## Question

Does adding a Broadening-Formation (BF-1, 30m pivots, strength 10) line-deviation
exit to the TFC strategy improve exits over the strategy's native exit alone,
"whichever hits first"?

## Setup

- Vehicle: TradingView strategy() `TVB-EXP BF Exit [Claude]` (repo:
  `pine/tvb_exp_bf_exit.pine`; TV script id USER;20f62fb840c649ebae9e087c8d517283).
- Symbol/window: `HIP3XYZ:AMZNUSDC.P`, 5m chart, 21,615 bars ~= 2026-04-30 13:25 UTC
  to 2026-07-10 (~71 days). In-sample, one symbol, one macro regime (contains the
  Jun-11..Jul-6 FTFC-down burst). Buy-hold over the window: -7.09%.
- Entry engine (all cells identical, = user live config): 15m Strategy TF; 6-TF gate
  60/120/240/D/W/M unanimous close-vs-period-open; intrabar arming at prior 15m
  extreme +/- 1 tick (revocable in-force window); regime stand_aside W+D (redundant
  given D/W/M in the gate -- kept for fidelity); ratchet governor (inert under flip).
- Exits: native `state` (first non-aligned 15m close) or `flip` (full opposite
  alignment only); BF exits as resting orders at the NEXT bar's projected line
  (same_side = exhaustion limit; any_side = + adverse-line protective stop).
  First fill wins.
- Costs: 0.0125% commission per side, slippage 1 tick, margin 0/0, 10k initial,
  100% equity per trade. use_bar_magnifier=true was declared; whether the account
  plan honored it was not independently verifiable -- unknown, shared by all cells.

## Results (closed trades; cell 1 additionally had 1 open long, openPL +25)

| Cell | exit_mode | bf_exit | Net USDC | Net % | PF | Trades | Win% | MaxDD% | Long net | Short net |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 (live ctrl) | flip | off | +64.3 | +0.64 | 1.068 | 12 | 16.7 | 10.12 | -472.1 | +536.4 |
| 3 | flip | same_side | **+103.4** | **+1.03** | 1.058 | 20 | 40.0 | **8.15** | -29.6 | +133.0 |
| 4 | flip | any_side | -337.7 | -3.38 | 0.850 | 23 | 39.1 | 9.96 | -105.6 | -232.1 |
| 2 (deploy ctrl) | state | off | -539.6 | -5.40 | 0.766 | 168 | 32.7 | 5.86 | -458.9 | -80.8 |
| 5 | state | same_side | -334.4 | -3.34 | 0.852 | 170 | 34.1 | 5.05 | -337.8 | +3.5 |
| 6 | state | any_side | -334.4 | -3.34 | 0.852 | 170 | 34.1 | 5.05 | -337.8 | +3.5 |

Screenshots: `tradingview-mcp-jackson/screenshots/bfexp_cell*.png`,
`bfexp_final_chart_flip_same.png`. Cells 1/3 verified to share the same first entry
(2026-04-30 13:25 UTC) -- entries were not contaminated by the exit change.

## Findings

1. **BF same-side exit improved the live config** (cell 3 vs 1): net +64 -> +103,
   win rate 16.7% -> 40%, maxDD 10.1% -> 8.2%. 9 of 20 exits were BF fills. All five
   long-side BF harvests were profitable (+92, +190, +85, +139, +211): they took
   swing profit at the upper line that the flip exit later gave back. The long side
   went from -472 to -30.
2. **...but it CUT the June mega-trend** (the mechanism, not a wash): the control's
   single +1010 short (May-31 entry ridden to Jun-30) became BF-harvested slices:
   +95, +1088, then re-entry whipsaw -123, -249, -211 = net ~+600 over the same
   regime. Short side degraded +536 -> +133. Net across the window BF still won, but
   ONLY because the long-side swing harvesting outweighed the trend give-up. This is
   the TVB-10 exit-symmetry result surfacing again at the exit-overlay level: harvest
   beats hold in swings, hold beats harvest in bursts -- a regime-shape bet.
3. **The adverse-side BF stop ("stop the bleed") measured NEGATIVE** (cell 4:
   -338 net). Under flip it converts drawdowns the flip exit would have survived
   into realized losses and re-entry churn. Under state it never fires at all
   (cells 5/6 byte-identical: state exits at ~1h average hold always beat a traverse
   to the far line). The bleed-stopping intuition did not survive contact with data
   ON THIS SYMBOL/WINDOW.
4. **State exit on this config is a churn machine** (cell 2: 168 trades, -5.4%,
   415 USDC commission = ~4.2% of capital). This quantifies the user's live EWY-day
   diagnosis: the 15m state clock + deep gate exits on every grey flicker. The user's
   live flip+intrabar setting beat the deployed-baseline state exit by ~6pp here.
5. **"BF hits first" selection-bias question answered**: yes, BF hits first almost by
   construction (a resting level inside the price path always beats a close-decided
   exit), and one artifact makes it worse: a line can be born already-deviated (price
   beyond the projection at creation after the pivot confirmation lag), which
   force-exits the position immediately -- the -123/-249 "BF lower dev" losses in
   cell 3 were this. Hitting first is NOT the same as exiting better: it was better
   on longs (swings) and worse on shorts (trend) in this window.

## Caveats (all binding)

In-sample, single symbol, single ~10-week window dominated by one down-burst; young
HIP-3 listing; historical intrabar granularity is 5m (chart-TF-grade, same for all
cells); strategy orders fill from the next 5m bar (up to one bar later than the
Companion display); BF same-bar validate+deviate events are missed (no resting order
yet); resting-limit semantics differ from live exit-on-alert (market exit after the
5m bar that fires the alert); bar-magnifier status unverified; n is small everywhere
(12-23 trades on flip cells). Treat cell 3's win as "the mechanism is worth watching
live", not "deploy same_side".

## Suggested live read-through (user workflow)

The same_side BF exit is mechanically equivalent to STRAT's pivot-ladder exit rule
("once a pivot high is taken out, be out of your longs") applied at 30m structure --
methodologically grounded, not arbitrary. Its cost is trend give-up on the short
burst side; the TVB-10 result suggests which side wins is regime-shaped. A live
two-alert workflow (flip exit alert + BF deviation alert, take whichever first,
skip the adverse-side stop) matches cell 3, the only cell that beat its control.

## Extension E1 -- multi-ticker generality check (pre-registered 2026-07-11, BEFORE runs)

**Question:** does the cell-3 result (BF same_side improves the flip control) generalize
beyond AMZNUSDC.P, or was it window/symbol luck?

**Universe rule (mechanical, fixed a-priori):** top 5 xyz-dex names by 24h notional
volume from the HIP-3 screener `/api/state` (all pass an oiUsd >= $2M floor), excluding
the already-run AMZN: SKHX, SKHY, XYZ100, MU, SPCX. Plus CL flagged DISCRETIONARY
(rank 9; the user's live reference symbol). Charts: `HIP3XYZ:<SYM>USDC.P` @ 5m.

**Cells per symbol (2):** flip/off (control) vs flip/same_side (the AMZN winner).
The refuted cells (any_side, state) are not re-run; TVB-10 already characterized
state-vs-flip at scale.

**Predictions (recorded before results):**
1. Sign-mixed outcome across symbols; the SPREAD is the expected finding, not a
   uniform win. A uniform BF win across all 6 would itself be suspicious.
2. MU is flip's burst-trend champion (TVB-10: ctrlA +15 -> +137 under flip). Predict
   BF same_side HURTS MU -- harvesting should give up the burst, as it did on the
   AMZN June short.
3. Swingy/range symbols should favor BF same_side (harvest > hold in swings).
4. Some symbols may have short/no tradeable windows (young listings; M-boundary
   warmup blocks the 6-TF gate until the first monthly open in loaded history).

**Determination rule (a-priori):** BF same_side is "worth watching live" only if it
improves net vs flip control on >= 4 of 6 symbols OR improves the aggregate
(sum of nets) while degrading no symbol catastrophically (>5pp). Anything weaker =
"regime-shaped overlay, symbol-local, do not promote".

### E1 results (run 2026-07-11, ~10 weeks of 5m history per symbol where available)

| Symbol | Cell | Net (closed) | Net % | PF | Trades | Win% | MaxDD% | OpenPL | Net+Open |
|---|---|---|---|---|---|---|---|---|---|
| SKHX | both | 0 trades | -- | -- | 0 | -- | -- | -- | -- |
| SKHY | both | 0 trades | -- | -- | 0 | -- | -- | -- | -- |
| XYZ100 | flip/off | +198 | +1.98 | 1.25 | 16 | 6 | 7.9 | +60 | +258 |
| XYZ100 | flip/same_side | +294 | +2.94 | 1.18 | 28 | 43 | 11.5 | -269 | +25 |
| MU | flip/off | +5288 | +52.9 | 2.15 | 6 | 33 | 28.5 | +2174 | +7462 |
| MU | flip/same_side | +5017 | +50.2 | 1.69 | 19 | 68 | 35.1 | +2202 | +7219 |
| SPCX | flip/off | -2867 | -28.7 | 0.02 | 9 | 11 | 33.9 | +463 | -2404 |
| SPCX | flip/same_side | -3209 | -32.1 | 0.53 | 16 | 44 | 49.7 | -28 | -3237 |
| CL | flip/off | +1714 | +17.1 | 2.20 | 9 | 22 | 12.4 | +247 | +1961 |
| CL | flip/same_side | +3175 | +31.7 | 2.70 | 19 | 58 | 13.8 | -443 | +2732 |

First-entry identity check passed on all four trading symbols. SKHX returned an
empty report (history too short to generate one), SKHY a populated all-zero report
-- both consistent with young listings / monthly-warmup gate block. SPCX first
entry 2026-06-01 vs 2026-05-04 elsewhere (later listing).

### E1 verdict against the pre-registered rule

- Branch 1 (improve >= 4 of 6 symbols): **FAIL** -- improved 2 (XYZ100, CL),
  degraded 2 (MU, SPCX), no-data 2.
- Branch 2 (aggregate improves, no catastrophic degradation): **ACCOUNTING-
  SENSITIVE.** Closed-trade aggregate: control +4,333 vs BF +5,277 (BF +944,
  no symbol degraded >5pp -> PASS). Mark-to-market aggregate (incl. open
  positions): control +7,277 vs BF +6,739 (BF -538 -> FAIL). The controls are
  still HOLDING open winners that BF harvested; whether BF "won" depends on
  whether you count unrealized marks. This is exactly why TVB-10 ran dual
  closed+MTM accounting.

**Verdict: NOT "slightly superior" in general.** The AMZN cell-3 result does not
generalize as a uniform improvement; it is a regime-shaped overlay, as predicted:
BF harvesting wins on swingy symbols (CL +17.1 -> +31.7 closed AND better MTM;
XYZ100 closed-better/MTM-worse), loses on burst-trend symbols (MU, prediction 2
confirmed), and rearranges rather than rescues a hostile symbol (SPCX). Universal
mechanical effects: win rate up everywhere (6-33% -> 43-68% -- giveback converted
to banked wins), trade count 2-3x (more fees, more re-entry exposure), and on
3 of 4 symbols higher maxDD. Strongest single case: CL -- the user's own live
reference symbol -- better on every accounting.

**Standing conclusion:** use BF same_side as a DISCRETIONARY overlay on
swing-shaped regimes, not as a default exit upgrade. The paper-trading shadow-exit
ledger (see screener-integration discussion) is the right instrument to decide
per-regime, since regime shape is only known in hindsight in backtests.

## Extension E2 -- re-entry hysteresis + arm/exit TF split (pre-registered 2026-07-11, BEFORE runs)

**Motivation (user design review):** E0/E1 tested a variant the user never intended.
The BF exit was meant as "this leg is exhausted -- stand down", but the build allowed
immediate re-entry on the still-aligned gate (the recycle loop = all of the 2-3x trade
multiplication). Separately, one knob (Strategy TF) coupled two unrelated decisions:
the entry trigger structure and the exit decision clock. User decisions: add a
post-exit-high ratchet (zero-parameter re-entry hysteresis); split Strategy TF into
arm_tf (trigger structure) and exit_tf (exit clock); keep BF pivots at 30m/10 this
round (STRAT-combo pivot redesign deferred to its own session).

**Script:** v2 of `pine/tvb_exp_bf_exit.pine`. New inputs: bf_reentry
(recycle|ratchet), arm_tf, exit_tf. ratchet = after a BF exit, same-direction
re-entry only at a trigger strictly beyond the most extreme price since that exit;
block clears on the re-entry fill or on full opposite gate alignment at an exit_tf
close (mirrors the governor's episode reset). TFC exits never set the block.

**Cells (6 per symbol; symbols = AMZN, XYZ100, MU, SPCX, CL; SKHX/SKHY dropped,
zero history):** all flip exit mode.

| Cell | bf_exit | bf_reentry | arm_tf | exit_tf | Purpose |
|---|---|---|---|---|---|
| C1 | off | -- | 15 | 15 | v1 control (regression ref) |
| C2 | same_side | recycle | 15 | 15 | v1 cell-3 (regression ref) |
| C3 | same_side | ratchet | 15 | 15 | isolate the re-entry fix |
| C4 | off | -- | 5 | 15 | isolate the arming split |
| C5 | same_side | ratchet | 5 | 15 | the user's intended live system |
| C6 | same_side | ratchet | 5 | 30 | exit-clock comparison |

**Predictions (recorded before results):**
- P1: C1/C2 approximately reproduce E0/E1 (exact reproduction impossible -- the
  live window slid ~1 day; gate = trade counts within ~+/-3 and same sign/order).
- P2: C3 vs C2: trade counts fall back toward C1; MU recovers most of its BF
  give-up; CL keeps most of its BF gain; win rate stays elevated vs C1.
- P3: C4 vs C1: more entries (nearer the alignment instant), better burst capture,
  more flip-line false starts; net effect sign-mixed by symbol.
- P4: C5 is the headline: expected >= C1 on CL and XYZ100, MU recovered vs C2.
- P5: C6 vs C5: small differences (flip exits are rare; the exit clock mostly
  shifts fill timing).

### E2 results (run 2026-07-11; net = closed trades; MTM = net + openPL)

| Symbol | C1 ctrl | C2 recycle | C3 ratchet | C4 arm5 | C5 arm5+rat | C6 exit30 |
|---|---|---|---|---|---|---|
| AMZN net | +64 | +102 | -11 | +8 | -99 | **+336** |
| XYZ100 net | +198 | **+294** | +264 | +194 | +264 | +272 |
| MU net | +5288 | +5017 | **+7247** | +4696 | +6646 | +4301 |
| SPCX net | -2867 | -3209 | **-2237** | -2860 | -2240 | -2274 |
| CL net | +1714 | +3175 | +3109 | +1684 | +3086 | **+3578** |
| Aggregate net | +4397 | +5379 | **+8373** | +3722 | +7657 | +6213 |
| Aggregate MTM | +7808 | +7268 | **+10578** | +7057 | +9785 | +8067 |

Trade counts: ratchet did NOT reduce them (C3 ~= C2 counts everywhere).
First-entry parity C1==C2==C3 held on all symbols; C5 (arm5) entered LATER and
worse on AMZN (00:30 vs 00:05) -- finer arming changes the trigger STRUCTURE,
it does not merely shrink it.

### E2 verdict vs predictions

- P1 (regression) PASS -- C1/C2 reproduced E0/E1 essentially exactly.
- P2 (ratchet) CONFIRMED IN EFFECT, WRONG IN MECHANISM: trade counts did not
  fall; instead re-entries moved to strictly-better levels (post-exit-extreme
  break), which is where the money was: MU short whipsaw -2653 -> -627,
  SPCX -3209 -> -2237. MU now BEATS its pure-flip control (+7247 vs +5288):
  the E1 objection ("BF gives up bursts") is substantially FIXED by re-entry
  hysteresis. AMZN is the one loser (+102 -> -11).
- P3 (arm5) WRONG DIRECTION: fine arming alone was a small uniform NEGATIVE
  (C4 <= C1 on every symbol; AMZN +64 -> +8). The 15m structural confirmation
  is earning its keep in this window. The split knob exists now, but the data
  do not support using it at 5m.
- P4 (intended system C5) CONFIRMED in aggregate: beats control on both
  accountings (+7657/+9785 vs +4397/+7808), though C3 (15m arming + ratchet,
  i.e. NO arming change) is the stronger cell on both.
- P5 (exit30 small) WRONG: large and sign-mixed (best AMZN and CL cells; worst
  MU BF-cell -- slower exit clock held MU's bad shorts longer). Another
  regime-shape knob; noted, NOT to be tuned per symbol.

**Standing conclusion (supersedes E1's):** the user's intended system is
BF same_side exit + post-exit-high re-entry ratchet ON TOP of the unchanged
live config (C3). On this 5-symbol/10-week sample it is the best aggregate cell
on both accountings, beats both controls on 3 of 5 symbols, and its two losses
are small (AMZN -75 vs control) while its wins are large (MU +1959, SPCX +630,
CL +1395). Cell rankings still differ by symbol (no universal winner -- charter
expectation intact); AMZN uniquely prefers the slower exit clock. In-sample,
one window, n small -- the live shadow-exit ledger remains the decision
instrument; C3 is what it should shadow first.

## Incident log (full disclosure)

While staging the experiment script, `pine_new` + a content-based focus check proved
insufficient: the MCP server's pine_new/pine_open only swap text in the CURRENT
editor tab and never change its cloud binding, so the first save overwrote the
user's "Broadening Formation MTF [BF-1]" script (v2->v4). Restored within minutes
from the session's verbatim copy of the source (bf.txt) as v5; chart study and the
30m pivot-TF input re-verified; TradingView version history additionally retains
every version. BF-1's later `modified` stamp (v5.0) is from this restore. Guide
updated with the root cause and a validated safe procedure
(`docs/guides/GPT_TVMCP_GUIDE.md` section 7).
