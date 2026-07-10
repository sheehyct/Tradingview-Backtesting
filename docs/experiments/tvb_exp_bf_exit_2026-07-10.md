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
