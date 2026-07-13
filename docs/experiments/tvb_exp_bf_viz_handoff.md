# BF-Exit Experiments -- Visualization Handoff (paste-ready)

> USER NOTE: paste or attach this ENTIRE file into Claude Desktop or GPT Desktop.
> It is self-contained: all data, definitions, flags, and chart guidance are below.
> No repo access is needed. Everything is plain ASCII.

---

## Your task

You are a data-visualization assistant. Build an interactive dashboard (or a set of
charts) from the datasets below. They come from a live-trading research program:
two independent AI implementations (labeled `claude` and `gpt`) backtested the same
timeframe-continuity (TFC) trading system with a Broadening-Formation (BF) exit
overlay on TradingView, on Hyperliquid HIP-3 perpetual contracts, plus a separate
448-run parameter sweep. The human trades these signals live with real money and
wants to SEE the structure of the results, not re-derive it from tables.

Prioritize clarity over chart count. The five stories that matter, in order:

1. THE FORK: two implementations of the same spec agree almost exactly on the
   non-ratchet cells and diverge wildly on the ratchet cells (D4, D5 vs D3, D7).
2. DUAL ACCOUNTING: closed-trade profit and total profit (including open positions)
   disagree about which configuration wins (D4, D5, D6).
3. CONCENTRATION: one symbol (MU) dominates all aggregate upside; SPCX is a
   universal disaster (D3, D5, D8).
4. CHURN: reactive "state" exits produce 10-100x the trades of "flip" exits and
   lose money doing it (D1, D8-G grid).
5. ROBUSTNESS DECAY: the apparent 5m edge weakens at 15m and mostly dies on
   30m/2024+ equity data (D9).

## Non-negotiable rules for every chart

- NEVER pool or average `claude` and `gpt` values for cells C3, C5, C6 without an
  implementation label. Their ratchet mechanisms differ (see THE FORK below); a
  pooled number would be fiction.
- Every profit chart must state which accounting it shows: `closed` (realized
  trades only) or `total` (closed + open position mark-to-market). Show both
  side-by-side where feasible.
- MU is an extreme outlier (+38% to +76% total). Use medians, small multiples, or
  a with/without-MU toggle; never let one symbol's bar set the axis for the rest.
  Consider symlog or capped axes (SPCX reaches -35%, MU +76% in the same panels).
- These are IN-SAMPLE research results on ~8-12 weeks of data. Do not title
  anything "best strategy" or "recommended". Neutral framing: "under these
  assumptions, on this window". No configuration is deployable.
- Currency values are USDC on 10,000 initial capital; percent values are relative
  to initial capital as reported by TradingView.

## Background in one minute

The system: enter long (short) the instant price breaks the prior completed
arming-timeframe bar's high + 1 tick (low - 1 tick), but ONLY while six timeframes
(60m, 120m, 240m, Daily, Weekly, Monthly) are unanimously aligned -- every one's
current price above (below) its current period open. That unanimous condition is
the "full6 gate". Exits are the experiment variable.

- Native exit `flip`: hold until ALL six timeframes align in the OPPOSITE
  direction. Very slow; rides whole regimes.
- Native exit `state`: exit at the first 15m close where the gate is no longer
  fully aligned. Very fast; exits on every flicker.
- BF exit: a Broadening Formation indicator (expanding megaphone drawn from 30m
  swing pivots, strength 10) projects an upper and lower line. While long, a
  resting limit sits at the projected upper line ("the leg is exhausted -- take
  it"). First of {BF fill, native exit} wins.
- The recycle problem: after a BF exit the gate is usually still aligned, so the
  system immediately re-enters on the same conditions (churn). The fix tested is
  the "ratchet": after a BF exit, same-direction re-entry is blocked until price
  exceeds the most extreme price printed since that exit.

Costs modeled: 0.0125% commission per side, 1 tick slippage. NOT modeled: funding,
spread variation, market impact, alert latency. Fills are TradingView bar-based
simulation (bar magnifier on), not tick truth.

## Glossary

Cells of the core experiment (all use flip as the native exit):

| Cell | BF exit | Re-entry | Arm TF | Exit TF | Meaning |
|---|---|---|---:|---:|---|
| C1 | off | -- | 15 | 15 | control = user's live configuration |
| C2 | on (same side) | recycle | 15 | 15 | naive BF exit race, churn allowed |
| C3 | on (same side) | ratchet | 15 | 15 | the re-entry fix, everything else unchanged |
| C4 | off | -- | 5 | 15 | faster arming alone, no BF |
| C5 | on (same side) | ratchet | 5 | 15 | the user's intended live system |
| C6 | on (same side) | ratchet | 5 | 30 | slower exit clock |

Symbols: HIP3XYZ:<SYM>USDC.P perpetuals on Hyperliquid (24/7 trading). AMZN,
XYZ100 (a 100-stock index perp), MU, SPCX, CL (crude oil) are the pre-registered
core; SP500, BRENTOIL, SNDK were added by protocol after extreme results.
SPCX listed 2026-05-17 (youngest, shortest history). All other core windows run
from late April / early May 2026 to 2026-07-11/12. In the sweep only, NASDAQ:AMZN,
NASDAQ:MU, NASDAQ:QQQ, AMEX:SPY are equity proxies with longer history but session
gaps (the perps trade continuously; the proxies do not -- structural difference).

Sweep vocabulary: `full6` = the 6-TF gate above. `slow4` = full6 minus the 120m
and 240m members, i.e. 60/D/W/M (inferred from the report's finding that the 120
and 240 gates are the only difference). `intraday3`, `fast3`, `mid4`, `dw4` are
alternative gate sets whose exact composition is NOT documented in the source
report -- treat them as categorical labels. `gov` = a loss-governor that stands
down after losing trades. `regime stand_aside` = an extra Weekly+Daily filter
(redundant under full6). `both/long_only/short_only` = direction permission.

## THE FORK (the most important flag in this document)

The pre-registered spec said: after a BF exit, re-enter same-direction "only at a
trigger strictly beyond the most extreme price printed since that exit." Two
independent implementations read that sentence differently:

- `claude` ratchet (loose / momentum-continuation): entry stop at
  max(normal trigger, post-exit extreme + 1 tick). Effect observed: trade counts
  UNCHANGED vs recycle; re-entries happen at strictly better PRICES. C3 became the
  best aggregate cell on both accountings.
- `gpt` ratchet (strict / stand-down): far fewer re-entries; median wait to
  re-enter same-direction exploded from 5 minutes to 280-5160 minutes. C3 lost to
  the control C1 on ALL five core symbols.

Both implementations were validated against each other on C1/C2/C4 (identical
first-entry timestamps on all 5 symbols, exact trade-count matches, profits within
~1-day window drift; see D4). So the fork is real semantics, not a bug or noise.
The economic verdict on "does the ratchet fix the BF exit" FLIPS with the reading.
This is the single decision the human still has to adjudicate from live-trading
intent. Any chart touching C3/C5/C6 must make the two implementations visually
distinct (color or panel), never merged.

Window-drift note: `gpt` ran ~1 day later than `claude`, so even the replicated
cells differ by a few final trades (worst case AMZN C2: claude +102 vs gpt -213,
one extra losing day at 100% equity). Expected drift on C1/C2/C4: tens of USDC on
most symbols.

## Datasets

### D1. E0 pilot -- AMZN only, exit-mode x BF-mode grid (claude, run 2026-07-10)

Window 2026-04-30..2026-07-10 (~71 days, 5m chart). Buy-hold over window: -7.09%.
`any_side` = BF exit also places a protective stop at the ADVERSE line (measured
negative; dropped from later experiments). state cells 5 and 6 are byte-identical
because the adverse line is never reached before a state exit -- mechanical, not
an error.

```csv
cell,exit_mode,bf_exit,net_usdc,net_pct,pf,trades,win_pct,maxdd_pct,long_net,short_net
1,flip,off,64.3,0.64,1.068,12,16.7,10.12,-472.1,536.4
3,flip,same_side,103.4,1.03,1.058,20,40.0,8.15,-29.6,133.0
4,flip,any_side,-337.7,-3.38,0.850,23,39.1,9.96,-105.6,-232.1
2,state,off,-539.6,-5.40,0.766,168,32.7,5.86,-458.9,-80.8
5,state,same_side,-334.4,-3.34,0.852,170,34.1,5.05,-337.8,3.5
6,state,any_side,-334.4,-3.34,0.852,170,34.1,5.05,-337.8,3.5
```

Key E0 story: the BF exit converted the control's single +1010 ridden short into
harvested slices (+95, +1088) plus re-entry whipsaw (-123, -249, -211). It won the
window only because long-side swing harvesting (-472 -> -30) outweighed the
short-trend give-up (+536 -> +133). Win rate is NOT profit: 16.7% -> 40.0% while
net barely moved.

### D2. E1 generality check -- 5 symbols x 2 cells (claude, run 2026-07-11)

flip/off = C1 control; flip/same_side = C2 equivalent. SKHX and SKHY (also
selected by the volume rule) had zero tradeable history -- valid empty results,
omitted below.

```csv
symbol,variant,closed_net,closed_pct,pf,trades,win_pct,maxdd_pct,open_pl,total_net
XYZ100,flip_off,198,1.98,1.25,16,6,7.9,60,258
XYZ100,flip_same_side,294,2.94,1.18,28,43,11.5,-269,25
MU,flip_off,5288,52.9,2.15,6,33,28.5,2174,7462
MU,flip_same_side,5017,50.2,1.69,19,68,35.1,2202,7219
SPCX,flip_off,-2867,-28.7,0.02,9,11,33.9,463,-2404
SPCX,flip_same_side,-3209,-32.1,0.53,16,44,49.7,-28,-3237
CL,flip_off,1714,17.1,2.20,9,22,12.4,247,1961
CL,flip_same_side,3175,31.7,2.70,19,58,13.8,-443,2732
```

E1 verdict: BF-as-naive-exit-race is regime-shaped, not superior -- it wins on
swingy symbols (CL, best case), loses on burst-trend symbols (MU), and cannot
rescue a hostile one (SPCX). Win rate rises everywhere; trade count 2-3x.

### D3. E2 core -- 5 symbols x 6 cells, closed net USDC (claude, run 2026-07-11)

Per-cell PF/trades/DD were not recorded at this granularity for claude (only nets
plus the aggregates in D4); the full-metric equivalent is the gpt table in D5.

```csv
symbol,cell,closed_net
AMZN,C1,64
AMZN,C2,102
AMZN,C3,-11
AMZN,C4,8
AMZN,C5,-99
AMZN,C6,336
XYZ100,C1,198
XYZ100,C2,294
XYZ100,C3,264
XYZ100,C4,194
XYZ100,C5,264
XYZ100,C6,272
MU,C1,5288
MU,C2,5017
MU,C3,7247
MU,C4,4696
MU,C5,6646
MU,C6,4301
SPCX,C1,-2867
SPCX,C2,-3209
SPCX,C3,-2237
SPCX,C4,-2860
SPCX,C5,-2240
SPCX,C6,-2274
CL,C1,1714
CL,C2,3175
CL,C3,3109
CL,C4,1684
CL,C5,3086
CL,C6,3578
```

### D4. Aggregate comparison -- 5-symbol sums, both accountings, both implementations

This is the fork in one table. Note how close the two implementations are on
C1/C2/C4 (shared engine validated) and how far apart on C3/C5/C6 (ratchet fork).
claude's best cell is C3; gpt's C3 is nearly its worst.

```csv
cell,claude_closed,claude_total,gpt_closed,gpt_total
C1,4397,7808,4376,7854
C2,5379,7268,5134,7180
C3,8373,10578,1208,2854
C4,3722,7057,4054,7516
C5,7657,9785,1673,3641
C6,6213,8067,410,2054
```

### D5. GPT core replication -- 5 symbols x 6 cells, full metrics (run 2026-07-11/12)

total_net = closed_net + open_pl (mark-to-market snapshot at collection time).

```csv
symbol,cell,closed_net,closed_pct,open_pl,total_net,total_pct,pf,trades,win_pct,maxdd_pct,commission,long_net,short_net,first_entry_utc
AMZN,C1,63.96,0.64,68.53,132.49,1.32,1.07,12,16.7,10.1,30.07,-472.08,536.04,2026-05-01 00:05
AMZN,C2,-213.40,-2.13,38.59,-174.82,-1.75,0.90,21,38.1,10.3,52.04,-303.02,89.62,2026-05-01 00:05
AMZN,C3,-68.47,-0.68,0.00,-68.47,-0.68,0.95,17,41.2,6.6,41.88,-78.46,9.99,2026-05-01 00:05
AMZN,C4,68.52,0.69,68.15,136.67,1.37,1.07,12,16.7,10.1,30.07,-468.74,537.26,2026-05-01 00:05
AMZN,C5,104.62,1.05,0.00,104.62,1.05,1.07,16,43.8,6.1,39.55,-155.26,259.88,2026-05-01 00:05
AMZN,C6,555.72,5.56,0.00,555.72,5.56,1.52,14,50.0,5.9,34.83,311.39,244.33,2026-05-01 00:05
XYZ100,C1,183.91,1.84,69.62,253.53,2.54,1.23,16,6.3,8.0,44.28,507.89,-323.99,2026-05-04 00:05
XYZ100,C2,311.05,3.11,-257.36,53.69,0.54,1.20,28,42.9,11.2,75.49,431.73,-120.67,2026-05-04 00:05
XYZ100,C3,-33.15,-0.33,-276.46,-309.61,-3.10,0.98,24,41.7,12.3,63.64,281.68,-314.82,2026-05-04 00:05
XYZ100,C4,225.18,2.25,70.03,295.21,2.95,1.30,16,6.3,7.7,44.37,523.92,-298.74,2026-05-04 00:05
XYZ100,C5,-377.05,-3.77,0.00,-377.05,-3.77,0.76,22,31.8,14.1,56.71,123.81,-500.86,2026-05-04 00:05
XYZ100,C6,-389.74,-3.90,0.00,-389.74,-3.90,0.75,20,35.0,14.1,51.43,126.25,-515.99,2026-05-04 00:05
MU,C1,5287.79,52.88,2262.17,7549.95,75.50,2.15,6,33.3,28.5,26.00,7722.93,-2435.15,2026-05-04 00:05
MU,C2,5065.60,50.66,2292.06,7357.66,73.58,1.69,19,68.4,35.1,73.86,7719.30,-2653.70,2026-05-04 00:05
MU,C3,3762.72,37.63,2092.81,5855.54,58.56,1.74,17,64.7,26.9,58.60,4666.72,-903.99,2026-05-04 00:05
MU,C4,4836.81,48.37,2193.46,7030.27,70.30,1.97,7,28.6,30.6,29.84,7464.90,-2628.09,2026-05-04 00:05
MU,C5,4067.53,40.68,2139.37,6206.90,62.07,1.95,17,70.6,24.6,58.61,4810.79,-743.26,2026-05-04 00:05
MU,C6,1983.35,19.83,1822.32,3805.67,38.06,1.33,16,68.8,36.6,53.65,4337.88,-2354.53,2026-05-04 00:05
SPCX,C1,-2938.06,-29.38,479.83,-2458.23,-24.58,0.01,9,11.1,34.5,21.70,-2627.65,-310.40,2026-06-01 00:05
SPCX,C2,-3317.60,-33.18,1.83,-3315.77,-33.16,0.53,16,43.8,50.4,34.87,-2094.36,-1223.24,2026-06-01 00:05
SPCX,C3,-3453.48,-34.53,0.00,-3453.48,-34.53,0.43,13,30.8,50.5,28.07,-1985.06,-1468.42,2026-06-01 00:05
SPCX,C4,-2857.08,-28.57,507.17,-2349.91,-23.50,0.02,9,11.1,33.5,21.76,-2547.66,-309.42,2026-06-01 00:05
SPCX,C5,-3531.83,-35.32,0.00,-3531.83,-35.32,0.40,13,30.8,49.2,27.99,-1899.79,-1632.03,2026-06-01 00:05
SPCX,C6,-3562.11,-35.62,0.00,-3562.11,-35.62,0.39,12,33.3,49.3,25.50,-1866.39,-1695.72,2026-06-01 00:05
CL,C1,1778.69,17.79,597.58,2376.26,23.76,2.29,9,22.2,12.4,23.67,-847.23,2625.92,2026-05-04 00:45
CL,C2,3288.12,32.88,-28.69,3259.42,32.59,2.77,19,57.9,13.8,52.11,327.83,2960.28,2026-05-04 00:45
CL,C3,1000.15,10.00,-169.67,830.48,8.30,1.72,17,52.9,13.6,42.40,492.29,507.86,2026-05-04 00:45
CL,C4,1780.77,17.81,622.65,2403.43,24.03,2.30,9,22.2,12.4,23.67,-845.71,2626.48,2026-05-04 00:45
CL,C5,1410.16,14.10,-171.43,1238.73,12.39,2.32,15,66.7,13.3,37.96,516.18,893.98,2026-05-04 00:45
CL,C6,1822.59,18.23,-177.78,1644.81,16.45,2.97,12,75.0,12.8,31.21,906.87,915.72,2026-05-04 00:45
```

### D6. GPT exploratory widening -- 3 additional symbols x 6 cells

Added by protocol (extreme MU/SPCX results require widening the sample, not
tuning). Selected mechanically: next-highest 24h volume names from the user's
HIP-3 screener (SP500 vol 44.6M / OI 545M; BRENTOIL 44.2M / 171M; SNDK 22.0M /
81M). Same columns as D5. Note: under gpt's STRICT ratchet these three symbols
partly disagree with its core -- C3 beats C1 on BRENTOIL and SNDK closed net.

```csv
symbol,cell,closed_net,closed_pct,open_pl,total_net,total_pct,pf,trades,win_pct,maxdd_pct,commission,long_net,short_net,first_entry_utc
SP500,C1,24.64,0.25,65.05,89.69,0.90,1.05,15,13.3,2.6,38.93,206.89,-182.25,2026-05-04 00:10
SP500,C2,-87.94,-0.88,64.32,-23.63,-0.24,0.90,25,32.0,3.4,63.85,130.97,-218.91,2026-05-04 00:10
SP500,C3,-138.60,-1.39,63.97,-74.62,-0.75,0.79,19,26.3,3.7,48.13,-102.79,-35.81,2026-05-04 00:10
SP500,C4,35.19,0.35,65.10,100.29,1.00,1.07,15,13.3,2.6,38.95,212.84,-177.65,2026-05-04 00:10
SP500,C5,-129.04,-1.29,64.02,-65.02,-0.65,0.79,20,30.0,3.1,50.87,-26.50,-102.54,2026-05-04 00:10
SP500,C6,-158.49,-1.58,58.99,-99.50,-0.99,0.76,19,31.6,3.0,48.66,-45.25,-113.23,2026-05-04 00:10
BRENTOIL,C1,768.74,7.69,671.35,1440.09,14.40,1.33,14,14.3,11.8,35.48,-1122.91,1891.65,2026-05-04 00:45
BRENTOIL,C2,959.49,9.59,276.74,1236.23,12.36,1.32,24,45.8,13.9,60.98,-762.52,1722.01,2026-05-04 00:45
BRENTOIL,C3,1220.89,12.21,0.00,1220.89,12.21,1.56,21,42.9,14.0,51.44,-870.66,2091.55,2026-05-04 00:45
BRENTOIL,C4,791.35,7.91,662.10,1453.45,14.53,1.34,14,14.3,11.7,35.49,-1119.02,1910.37,2026-05-04 00:45
BRENTOIL,C5,1430.15,14.30,0.00,1430.15,14.30,1.67,21,42.9,13.5,51.69,-839.37,2269.53,2026-05-04 00:45
BRENTOIL,C6,982.56,9.83,0.00,982.56,9.83,1.64,16,50.0,12.4,39.52,-404.61,1387.17,2026-05-04 00:45
SNDK,C1,1315.14,13.15,744.17,2059.31,20.59,1.30,18,11.1,38.1,56.20,2935.37,-1620.23,2026-05-04 00:05
SNDK,C2,1509.05,15.09,-1375.27,133.79,1.34,1.20,29,34.5,42.3,81.04,2727.80,-1218.74,2026-05-04 00:05
SNDK,C3,4765.50,47.66,-1943.34,2822.16,28.22,2.08,24,29.2,28.2,71.57,4099.26,666.24,2026-05-04 00:05
SNDK,C4,1152.81,11.53,734.55,1887.36,18.87,1.25,19,10.5,39.0,58.95,2891.15,-1738.34,2026-05-04 00:05
SNDK,C5,1147.75,11.48,-2139.13,-991.38,-9.91,1.17,26,26.9,41.2,72.60,2774.22,-1626.47,2026-05-04 00:05
SNDK,C6,2077.29,20.77,-2317.63,-240.34,-2.40,1.36,24,25.0,38.5,68.57,2610.83,-533.54,2026-05-04 00:05
```

### D7. Fork mechanism statistics -- recycle (C2) vs ratchet (C3)

How each implementation's ratchet changed BEHAVIOR, not just P/L. wait = median
minutes until a same-direction re-entry after a BF exit; extension = median price
move beyond the exit level required before the re-entry filled.

```csv
implementation,scope,metric,recycle_C2,ratchet_C3
gpt,5 core symbols,closed_trades,103,88
gpt,5 core symbols,bf_exits,55,46
gpt,5 core symbols,same_dir_reentries,48,32
gpt,8 symbols pooled,closed_trades,181,152
gpt,8 symbols pooled,bf_exits,86,69
gpt,8 symbols pooled,same_dir_reentries,76,45
gpt,8 symbols pooled,median_wait_minutes,5,685
gpt,8 symbols pooled,median_extension_pct,0.003,1.37
gpt,CL,median_wait_minutes,5,5160
gpt,CL,median_extension_pct,0.14,4.07
claude,5 core symbols,trade_count_change,baseline,unchanged
claude,MU,short_side_net,-2653,-627
```

claude's ratchet signature: trade counts approximately equal to C2 on every
symbol, but re-entries fill at strictly better prices (the money was in the
prices, not the counts -- e.g. MU's short-side whipsaw damage shrank -2653 ->
-627, flipping MU C3 above its control). gpt's ratchet signature: fewer, much
later re-entries. Same spec sentence, different machines.

### D8. Parameter sweep aggregates (gpt, 448 runs, 2026-07-12)

All rows: median/worst/best of TOTAL return % across the listed sample size;
sparse = count of runs with fewer than ~10 trades. 5m charts unless noted.
Baseline configuration unless the profile says otherwise: full6 gate, flip exit,
BF off, arm 15 / exit 15, regime stand_aside, governor on, both directions.
IMPORTANT: every ratchet row in the B grid uses gpt's STRICT ratchet semantics
(see THE FORK); claude's looser ratchet was not swept.

Gate x native-exit screen (10 tickers each: 6 HIP-3 perps + 4 equity proxies):

```csv
profile,gate,exit,positive_of_10,sparse,median_total_pct,worst_pct,best_pct,median_pf,median_dd_pct,median_trades
G01,full6,flip,9,3,8.34,-24.73,152.49,1.55,11.26,14.5
G02,full6,state,4,0,-2.96,-14.19,31.10,0.90,8.52,196.5
G03,intraday3,flip,1,0,-16.29,-37.87,12.14,0.74,23.19,388.0
G04,intraday3,state,2,0,-18.64,-37.75,65.20,0.78,21.27,668.5
G05,fast3,flip,2,0,-22.53,-31.60,29.20,0.77,24.47,719.0
G06,fast3,state,2,0,-26.20,-35.33,53.59,0.72,27.70,1024.5
G07,mid4,flip,1,0,-16.18,-36.48,9.46,0.74,23.65,381.5
G08,mid4,state,2,0,-21.89,-31.57,69.14,0.75,22.26,771.0
G09,slow4,flip,9,3,8.17,-24.72,152.49,1.58,11.26,14.5
G10,slow4,state,4,0,-0.93,-17.31,51.26,0.96,8.50,200.0
G11,dw4,flip,3,0,-7.31,-24.18,48.98,0.83,15.55,71.0
G12,dw4,state,2,0,-13.15,-27.07,34.89,0.76,13.55,447.0
```

Arm/exit timing screen (6 representative tickers each):

```csv
profile,arm_tf,exit_tf,positive_of_6,sparse,median_total_pct,worst_pct,best_pct,median_pf,median_dd_pct,median_trades
T01,5,5,5,1,8.57,-1.70,158.06,1.64,12.83,15.5
T02,5,15,6,1,8.21,0.89,154.63,1.56,11.80,14.0
T03,5,30,6,1,7.39,0.54,184.03,1.53,11.69,13.0
T04,15,15,6,1,8.34,0.78,152.49,1.62,12.13,14.5
T05,15,30,6,1,6.91,0.38,174.07,1.48,13.11,13.5
T06,15,60,5,1,4.81,-0.21,123.48,1.33,14.44,12.0
T07,30,30,6,1,7.45,0.43,172.09,1.49,13.48,13.5
T08,30,60,5,1,5.42,-0.33,121.19,1.36,14.67,12.0
```

BF sensitivity grid (6 representative tickers each; pivot_tf in minutes,
strength = bars each side required to confirm a pivot):

```csv
profile,bf_pivot_tf,bf_strength,bf_reentry,positive_of_6,sparse,median_total_pct,worst_pct,best_pct,median_pf,median_dd_pct,median_trades
B01,15,5,recycle,4,0,4.36,-4.35,129.98,1.12,14.29,48.5
B02,15,5,ratchet,4,0,5.46,-8.33,54.15,1.28,9.90,31.5
B03,15,10,recycle,6,0,5.33,0.30,118.32,1.18,12.66,34.0
B04,15,10,ratchet,4,0,0.51,-4.95,78.42,1.01,10.67,25.5
B05,15,20,recycle,4,0,5.84,-1.94,134.20,1.28,13.06,26.0
B06,15,20,ratchet,4,0,9.34,-1.59,90.16,1.41,11.42,23.0
B07,30,5,recycle,6,0,3.57,0.09,143.57,1.14,12.80,31.5
B08,30,5,ratchet,4,0,4.85,-5.74,89.95,1.12,11.18,26.0
B09,30,10,recycle,4,0,4.57,-2.09,136.47,1.21,13.14,26.0
B10,30,10,ratchet,4,0,9.04,-0.84,90.75,1.42,11.42,22.5
B11,30,20,recycle,5,0,8.92,-0.11,164.41,1.43,13.63,20.5
B12,30,20,ratchet,5,0,7.78,-4.16,164.89,1.59,10.87,18.0
B13,60,5,recycle,4,0,6.01,-3.27,119.52,1.34,13.16,27.0
B14,60,5,ratchet,4,0,6.59,-2.74,67.64,1.28,12.53,23.5
B15,60,10,recycle,6,0,9.05,0.65,164.51,1.43,12.89,21.0
B16,60,10,ratchet,5,0,7.94,-4.64,165.01,1.59,11.57,18.5
B17,60,20,recycle,5,1,8.76,-0.17,141.59,1.39,13.60,19.0
B18,60,20,ratchet,5,1,12.92,-0.15,122.90,1.66,10.09,18.5
```

Regime/governor/direction grid, BF off (6 representatives each). The striking
result: regime layer and governor are nearly INERT -- rows differ only by
direction. Long-only looks great and short-only terrible because the window was
bullish (launch-regime bias, flagged, not actionable):

```csv
profile,regime,governor,direction,positive_of_6,sparse,median_total_pct,worst_pct,best_pct,median_pf,median_dd_pct,median_trades
R01,stand_aside,on,both,6,1,8.34,0.82,152.49,1.62,12.13,14.5
R02,stand_aside,on,long_only,5,4,12.79,-2.86,141.91,2.32,5.69,8.0
R03,stand_aside,on,short_only,1,4,-1.14,-10.53,2.43,0.55,10.16,8.0
R04,stand_aside,off,both,6,1,8.00,0.88,153.03,1.53,11.86,14.5
R05,stand_aside,off,long_only,5,4,12.79,-2.86,142.25,2.32,5.69,8.0
R06,stand_aside,off,short_only,1,4,-1.14,-10.53,2.43,0.55,10.16,8.0
R07,off,on,both,6,1,8.34,0.80,152.49,1.62,12.13,14.5
R08,off,on,long_only,5,4,12.79,-2.86,141.91,2.32,5.69,8.0
R09,off,on,short_only,1,4,-1.14,-10.53,2.43,0.55,10.16,8.0
R10,off,off,both,6,1,8.00,0.88,153.03,1.53,11.86,14.5
R11,off,off,long_only,5,4,12.79,-2.86,142.25,2.32,5.69,8.0
R12,off,off,short_only,1,4,-1.14,-10.53,2.43,0.55,10.16,8.0
```

Same grid with BF 60/10 recycle overlay (medians shift slightly; same
inertness/direction pattern): both-direction median 9.05 vs 8.34 without BF,
long-only 12.54, short-only -2.65 (positive counts 6/6, 5/6, 1/6 respectively).

### D9. Robustness across chart timeframe / calendar depth (gpt)

Same strategy re-run on higher-timeframe charts, which ALSO loads deeper history.
CONFOUND (flagged in the source): changing chart TF changes entry sampling too,
so this is a stress test, not a clean holdout. 15m = 10 tickers (history back to
2025-04..2026-01). 30m = 4 equity proxies only (history from 2024-01-02).

```csv
chart_tf,config,sample,positive,median_total_pct,worst_pct,best_pct,median_pf,median_dd_pct,median_trades
5m,no_BF_baseline,10 tickers,9/10,8.34,-24.73,152.49,1.55,11.26,14.5
15m,no_BF_baseline,10 tickers,6/10,3.26,-24.61,695.57,1.08,24.27,41.0
15m,BF60_10_recycle,10 tickers,6/10,5.23,-29.50,697.95,1.11,25.95,63.0
30m,no_BF_baseline,4 equity proxies,2/4,-4.76,-45.71,759.69,0.96,29.93,118.0
30m,BF60_10_recycle,4 equity proxies,2/4,-0.11,-48.65,487.76,1.01,40.87,154.5
```

The best% outliers at 15m/30m are NASDAQ:MU again (+696% / +760% -- one symbol's
multi-year run, not a strategy property). At 30m NASDAQ:AMZN loses 46-49% and QQQ
is negative.

### D10. GPT's ranked configurations (its own consistency-first ranking)

```csv
rank,configuration,positive,median_total_pct,worst_pct,median_pf,median_dd_pct,judgment
1,no BF full6 flip 15/15 both,9/10,8.34,-24.73,1.55,11.26,best 5m cross-ticker; fails longer-window tests
2,no BF slow4 flip 15/15 both,9/10,8.17,-24.72,1.58,11.26,near-identical to full6 with fewer gate inputs
3,BF60/10 recycle full6 flip 15/15,6/6,9.05,0.65,1.43,12.89,small median uplift; lower PF; worse long-window risk
4,no BF full6 flip arm5 exit15,6/6,8.21,0.89,1.56,11.80,close second; no holdout win
5,BF60/20 ratchet full6 flip 15/15,5/6,12.92,-0.15,1.66,10.09,best B-grid medians; selection risk
6,no BF long-only full6 flip 15/15,5/6,12.79,-2.86,2.32,5.69,launch-regime bias; rejected
```

GPT's own caveat, endorsed: this ranking came from hierarchical adaptive testing
(gate -> timing -> BF -> risk branches selected sequentially), so the winner
carries selection bias and cannot be validated on the data that chose it.

## Suggested visualizations (priority order)

1. THE FORK dumbbell: for each core symbol, closed net of C1 vs C3, one panel per
   implementation (or claude/gpt paired dumbbells). The reader should see in one
   glance: claude C3 improves 4 of 5 symbols; gpt C3 improves 0 of 5. Add the D4
   aggregate as a summary strip. (D3, D5, D4)
2. Replication-quality scatter: claude closed net vs gpt closed net, one point per
   (symbol, cell), diagonal y=x reference, color by cell-family (C1/C2/C4 =
   "shared engine" vs C3/C5/C6 = "forked ratchet"). Shared-engine points should
   hug the diagonal; forked points scatter off it. This is the single most
   honest picture of the whole exercise. (D3 joined to D5)
3. Dual-accounting slope chart: closed_net -> total_net per (symbol, cell) for
   gpt data; highlight sign flips (SNDK C5 +1148 -> -991, XYZ100 C2 +311 -> +54).
   Title suggestion: "Open positions decide arguments". (D5, D6)
4. Symbol x cell heatmap of total %, separate small-multiple per implementation,
   diverging palette centered at 0, MU row visibly clipped/annotated. (D3, D5, D6)
5. Sweep risk-return map: median_total_pct (y) vs median_dd_pct (x), bubble size =
   median_trades (log), color by grid family (G/T/B/R), annotate G01, G09, B15,
   B18. The state-exit profiles form a distinct high-trade losing cluster --
   label it "churn". (D8)
6. Robustness decay bars: positive-fraction and median PF for the same baseline at
   5m -> 15m -> 30m, with the confound caveat printed on the chart. (D9)
7. Churn quantification: trades (log x) vs total % for G-grid profiles -- flip vs
   state as two colors; 14 trades vs 200-1000 trades tells the story alone. (D8)
8. Ratchet behavior shift: median re-entry wait 5 min -> 685 min (log scale) and
   extension 0.003% -> 1.37% for gpt, with a note that claude's ratchet instead
   left counts unchanged and improved prices -- no wait data exists for claude.
   (D7)
9. Win-rate-is-not-profit scatter: win_pct vs closed_net per (symbol, cell), gpt
   data; BF cells cluster high-win-rate without clustering high-profit. (D5, D6)

## Caveats to print on or near the charts

- In-sample; ~8-12 week window (Apr/May-Jul 2026) for all 5m results; one macro
  regime; no out-of-sample confirmation exists.
- 100% of equity per trade, compounding: path-dependence and outliers are
  magnified by construction. MU's numbers are a regime ride, not an edge estimate.
- Costs: 0.0125%/side + 1 tick only. No funding, spreads, impact, or latency.
- TradingView bar-based fills (5m granularity, bar magnifier on) approximate
  intrabar truth; BF exits modeled as resting limits, which is BETTER than the
  live alert-driven workflow they emulate.
- SPCX listed 2026-05-17: youngest contract, shortest window, worst results --
  partly a listing-age artifact, partly real hostility to the system.
- The sweep winner was chosen by adaptive multiple testing; treat rankings as
  hypotheses, not results.
- Nothing in this document is a deployment recommendation. The program's stance:
  backtests characterize and kill ideas; consistency across symbols and variables
  is the deliverable, not any single stellar cell.

## Source files (home PC, for provenance)

- Claude experiment record: `C:\Strat_Trading_Bot\tradingview-backtesting\docs\experiments\tvb_exp_bf_exit_2026-07-10.md`
- GPT blind replication: `C:\Strat_Trading_Bot\tradingview-backtesting\docs\experiments\tvb_exp_bf_exit_gpt.md`
- GPT 448-run sweep (includes all per-run rows not embedded here): `C:\Strat_Trading_Bot\tradingview-backtesting\docs\experiments\tvb_exp_bf_sweep_gpt.md`
- Strategy source: `C:\Strat_Trading_Bot\tradingview-backtesting\pine\tvb_exp_bf_exit.pine`
