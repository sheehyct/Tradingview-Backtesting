# TVB-2: Control A/B re-run (2x2 fee characterization)

**Date:** 2026-06-30 (Session TVB-2)
**Purpose:** Re-establish the baseline controls cleanly using the now-fixed TV MCP reader, before
any regime/two-layer work. Replaces the screenshot-era reads from TVB-1.
**Reader status:** `tradingview-mcp-jackson` Strategy Tester readers FIXED + deployed this session
(see memory `tvb1-tv-mcp-reader-newui`). All numbers below are clean JSON reads from
`reportData().performance`, cross-checked against a standalone CDP probe.

## Fixed conditions (identical across all four runs)

- **Instrument:** `OKX:MSTRUSDT.P`
- **Strategy:** `Baseline TFC [TVB-1]` (= `pine/baseline_continuity.pine`, saved slot, v12)
  [TVB-3 CORRECTION: the slot content is NOT the repo file verbatim -- it is the TVB-1
  "Control A + HIP-3 fee test" variant (v6-converted, commission 0.10 hardcoded, NO leverage
  input, sizing = 100% equity = structurally 1x). Input-id layout matches the map used in
  these runs. See "TVB-3 addendum: settings dump" at the end of this file.]
- **Backtest window:** 2026-02-25 10:00Z -> 2026-06-30 ~10:00Z (~4 months). Comparable to TVB-1's
  Feb 25 - Jun 28, extended ~2 days. `buyHold` over the window: **-29% to -31.5%** (DOWN regime).
- **Directions:** `allow_long = allow_short = TRUE` (genuinely bidirectional; long+short counts shown).
- **Sizing:** 100% of equity, first-trade notional ~= equity => **effective 1x** (leverage-agnostic edge read).
- **Initial capital:** 10,000 USDT. **State-stop** exits (confirmed via exit_signal = "state-stop").
- **Fee model:** TradingView strategy commission, `percent` type. `0%` = edge isolation;
  `0.1%` = HIP-3 level. NOTE: TV commission is per FILL (entry and exit each), so 0.1%/fill is
  **~0.2% round-trip** -- this is the ~0.2% round-trip the deployability bar refers to.

## Results

| Control | TF set (chart) | Fee | Trades (L/S) | Net % | PF | Win % | MaxDD % | Sharpe | Commission |
|---------|----------------|-----|--------------|-------|------|-------|---------|--------|-----------|
| **B** | 60/30/15 (15m) | 0%   | 2301 (1132/1169) | **+85.8%** | 1.186 | 35.5% | 21.7% | 1.02 | 0 |
| **B** | 60/30/15 (15m) | 0.1% | 2301 (1132/1169) | **-98.1%** | 0.400 | 21.5% | 98.2% | -2.47 | 10,545 |
| **A** | M/W/D/60 (60m) | 0%   | 261 (147/114)    | **+48.2%** | 1.373 | 39.1% | 11.6% | 1.84 | 0 |
| **A** | M/W/D/60 (60m) | 0.1% | 261 (147/114)    | **-12.0%** | 0.906 | 30.3% | 22.4% | -1.15 | 4,755 |

## Key findings

1. **Raw edge is positive for BOTH controls** in a ~-30% down market: B +85.8% (PF 1.186),
   A +48.2% (PF 1.373). The bidirectional continuity gate carries a real edge zero-of-fee.
2. **Control A dominates Control B on risk-adjusted terms:** Sharpe 1.84 vs 1.02, PF 1.373 vs
   1.186, MaxDD 11.6% vs 21.7% -- at **~9x fewer trades** (261 vs 2301).
3. **At HIP-3 fees both controls are net losers:** B catastrophically (-98.1%, PF 0.400, 98% DD),
   A mildly (-12.0%, PF 0.906). The slow gate "almost clears" (PF 0.906 -> needs modest per-trade
   edge to exceed ~0.2% round-trip); the fast gate is hopeless via churn.
4. **Turnover is the dominant lever, end-to-end:** B's 2301 trades pay **10,545 commission --
   larger than the 10,000 starting capital**, inverting a +8,576 gross edge into -9,814 net.
   A's 261 trades pay 4,755. Fees do not dent these strategies; they invert them.
5. **Neither control is deployable at HIP-3 fees.** A is the closer candidate.

## Reconciliation with TVB-1

| | TVB-1 (Feb25-Jun28) | TVB-2 (Feb25-Jun30) |
|--|--|--|
| B @ 0% | PF 1.284 | PF 1.186 |
| B @ 0.1% (HIP-3) | (not run) | PF 0.400 |
| A @ OKX (~0.05%) | PF 1.131 | (not run this session) |
| A @ 0.1% (HIP-3) | PF 0.921 | PF 0.906 |

Structure replicates: positive raw edge, A > B risk-adjusted, both die at HIP-3, A closest.
A @ 0.1% (0.906) ~= TVB-1's A @ HIP-3 (0.921). Numeric drift is attributable to the +2-day window
and a direction-config difference (see caveats).

## Fee model — verified real HIP-3 rates (supersedes the fee assumptions above)

Source: backed out from real Hyperliquid fills (fee / notional per order, this account, May-Jun 2026).
The 0.1% used above was NOT too high -- it is ~16% above the real taker rate; the taker verdicts
barely move. (This also corrects the loose "OKX fees" framing from TVB-1: the data proxy is OKX, but
EXECUTION is HL HIP-3; the operative cost is the HIP-3 builder-inclusive rate below, not an OKX fee.)

**Verified schedule (all-in, incl. HIP-3 builder fee):**
| dex | maker | taker |
|---|---|---|
| xyz (HIP-3 equity = the MSTR proxy) | 0.0086% | **0.0864%** (TradeXYZ builder ~2x HL base taker) |
| cash (HIP-3 equity) | 0.0086% | unobserved (assume ~= xyz taker; VERIFY) |
| crypto (native HL) | 0.0144% | 0.0432% (= HL published base; validation) |

Controls use **stop orders -> taker**, so the operative rate is **xyz taker 0.0864%**.
(Account blended realized 0.0142% is mostly manual maker fills -- NOT valid for a taker backtest.)

**Fee is the single most sensitive parameter.** %-equity sizing compounds fees: equity x= (1-f)^(2N)
(A: N=261 -> (1-f)^522; B: N=2301 -> (1-f)^4602). NEVER report a single-fee verdict -- always sweep.

**Corrected verdict sweep** (0% and 0.1% are ACTUAL backtest re-runs; intermediate rates are the
geometric model anchored on them -- CONFIRM BY ACTUAL RE-RUN):
| control | 0% (actual) | maker 0.0086% | xyz taker 0.0864% | 0.1% (actual) |
|---|---|---|---|---|
| A (261t, M/W/D/60, 60m) | +48% | **+42%** | -6% | -12% |
| B (2301t, 60/30/15, 15m) | +86% | **+25%** | -96% | -98% |

**Headline:** at the operative taker rate the prior verdict HOLDS (A barely fails -6%, B dead -96%).
But **at maker (limit entries) BOTH flip positive** (A +42%, B +25%). The deployability question is
therefore **maker-vs-taker execution, not the continuity gate** -- a limit-entry variant is decisive.

### Measured fill profile (maker/taker) -- and why it does NOT auto-flip the verdict

Real fills were MEASURED (credit: Claude Desktop fill analysis), not assumed: **87% maker / 13%
taker blended**, hiding two venue profiles:

| dex | entry taker% | exit taker% | profile |
|---|---|---|---|
| xyz (HIP-3, the deployment venue) | 2.6% | 3.7% | ~97% maker, both legs |
| cash (HIP-3) | 0% | 0% | 100% maker |
| crypto (native HL) | 97.3% | 89.1% | ~taker, both legs |

So the all-taker assumption was wrong; "never use limit orders" holds only on crypto. On xyz the
user fills ~97% maker, entries included. This does NOT make the maker column the deployed baseline:

- **The +42%/+25% maker numbers are a FEE SWAP on a TAKER backtest** -- same stop-order fills, cheaper
  fee. You cannot physically earn a maker fee on a stop-triggered breakout: a maker buy rests BELOW
  the market and fills when price comes DOWN to it (buying a dip/retest); a breakout long crosses UP
  through the level (taker). Opposite microstructure events.
- Therefore **~97% maker xyz *entries* strongly implies the user's real xyz entries are NOT
  stop-breakouts** -- they are resting-limit / retest entries (or thin-book rests). That is a
  *different strategy* than the backtested stop-breakout control: different trade set, different
  per-fill prices -- not merely a cheaper fee on the same trades. (CONFIRM: how are xyz entries placed?)
- Charter S6 in the fee domain: **a real mechanism (genuine 97% maker xyz fills) is the most effective
  cover for an optimistic conclusion (deployable).** The mechanism is real; that it transfers to the
  backtested breakout entry is the unverified part.

**Disposition:** the taker controls remain the honest baseline for the stop-breakout AS BUILT
(A -6%, B -96%); the maker column is an optimistic UPPER BOUND, not the expectation. The measured
maker data RE-RANKS the work: build the **limit-entry / retest variant as a first-class strategy**
with realistic maker-fill modeling (including NON-fills when price runs away), and test whether ITS
backtested fills reproduce the user's real xyz edge. +42%/+25% must be EARNED by that variant, not
inherited via a fee swap. The load-bearing open item is the fill MECHANISM (UI default order type?
retest entries? book thinness?), since the variant's realism depends on it.

**UPDATE -- the maker classification is DISPUTED; do not trust the 97% maker read yet.** The user
reports trading xyz almost exclusively with MARKET orders (entries, and TP/SL set "at market"). A
market order is taker; a trigger order that fires a market order is taker on execution; a "resting"
stop/TP is NOT maker liquidity (it provides nothing to the book until it triggers, then takes). A
97%-maker rate requires ~97% resting-LIMIT liquidity provision, which the user does not do -- and the
data claims 97% maker ENTRIES, which a market entry physically cannot be. So the maker/taker split
(INFERRED from fee/notional, not read from HL's flag) is almost certainly a MISCLASSIFICATION.

Most likely reality: the user's effective xyz rate really is ~0.0086%, but as a CHEAP TAKER rate
(fee tier / builder structure), mislabeled "maker" by the rate heuristic -- or notional was mis-scaled
(e.g., leverage notional) making fee/notional read artificially low. **Consequential fork:**
- If xyz **taker ~= 0.0086%** (cheap): the stop-breakout control AS BUILT pays that rate -> **A +42%,
  B +25% -> potentially deployable as-is, NO limit variant needed.** The breakout-is-taker objection
  becomes moot (you don't need maker; taker is just cheap on xyz).
- If xyz **taker ~= 0.0864%** and the 0.0086% fills are genuinely maker: the as-built strategy fails
  and only a mechanically-dubious limit variant could capture maker.

**Resolve DEFINITIVELY before any verdict:** (1) re-classify the fills by HL's authoritative
maker/taker liquidity flag (the `crossed` field in the fills API), NOT by backing out fee/notional;
(2) read the effective fee directly on orders known to be market (the user's entries). That single
check settles whether this strategy is already viable or still blocked.

### RESOLVED -- ground-truth fee via HL `crossed` flag (operative fee; supersedes ALL rate figures above)

Fills re-pulled from the HL API and classified by the authoritative **`crossed`** liquidity flag
(true=taker), NOT by backing out fee/notional. n=2,425 fills, 2026-05-03..06-30 (API-served set;
incomplete tail, but large/representative for ratios; same fills used for both classifications).
**Method validated:** native-crypto TAKER by `crossed` = 0.0432%, matching HL's published base taker
exactly. No separate builder-fee field (1/2425 fills) -- the HIP-3 deployer fee is baked into `fee`.

**The earlier inference was backwards.** xyz is **86.5% TAKER** (entries 79.8% taker) -- the
"I trade xyz with market orders" self-report was correct. The fee/notional method had anchored on
wrong reference rates (assumed xyz taker=0.0864%, maker=0.0086%); ground truth is that **xyz TAKER is
the cheap rate**: ~**0.0086% modal**, **0.0125% notional-weighted**, 0.0143% mean, 0.0864% only a ~7%
tail. Maker is lower still (~0.0029%).

| dex | fills | taker% | operative TAKER rate (all-in) |
|---|---|---|---|
| **xyz** (deployment venue) | 1868 | 86.5% | **~0.0086% modal / 0.0125% notional-wtd** |
| cash | 219 | 94.5% | 0.0086% |
| crypto (native HL) | 307 | 97.4% | 0.0432% (= HL published; validation) |

**Operative fee for the controls (stop orders -> taker) = ~0.0086-0.0125%: ~8-12x BELOW the 0.1% used
in the runs above, and below even HL crypto taker.** This REVERSES the fee-based verdict:

| control | at 0.1% (actual run) | at ~0.0086-0.0125% (GEOMETRIC MODEL -- CONFIRM BY RE-RUN) |
|---|---|---|
| A (261t) | -12% | **+38 to +42%** (clear winner) |
| B (2301t) | -98% | **+5 to +25%** (roughly breakeven) |

So "turnover is fatal for B" was largely a fee artifact. At real cost A is clearly positive, B is not dead.

**BUT the binding constraint MOVED; it did not vanish (charter: fixing one cost promotes the next).**
With fees ~10x cheaper, the next under-modeled cost dominates -- and it is **slippage**:
- [TVB-3 CORRECTION: the runs were NOT slippage-free. The strategy declares `slippage = 1` and the
  TVB-3 settings dump confirms `in_24` (internalID `slippage`) = 1 tick, applied by TV to every
  market/stop fill. At mintick 0.01 on MSTRUSDT.P that is ~2 ticks/round-trip (~0.02 on a ~$100
  price, ~0.02%/RT at the lows -- the SAME order as the real taker fee 2x0.0125%). So the numbers
  above already carry a 1-tick cost; the open question is whether 1 tick is REALISTIC (depth,
  order size, venue), not whether slippage was modeled at all.]
- The user fills **market/taker on both legs**, so every entry and exit gaps (user confirmed
  ~symmetric in ticks). **B = 2,301 market round-trips = 2,301x slippage; A = 261 (~9x less).**
- B near-breakeven at real fee + 1-tick slippage is precisely where the slippage REALISM check
  (1 tick vs actual book depth at market-order size) decides the sign. **The churn concern is NOT
  exonerated by cheap fees** -- its slippage exposure remains ~9x A's.
- Intrabar fill fidelity / bar-magnifier still unverified -- matters most when per-trade edge is
  thin (B). [TVB-3: bar magnifier CONFIRMED OFF for these runs -- `in_32` `use_bar_magnifier`
  defaults false and no record of enabling it exists.]

**Disposition:** at real fees, **A is a genuinely promising control** (clear positive, low turnover,
low slippage exposure); **B is "alive but fragile"** pending slippage -- do NOT call it viable yet.
Next, in order: (1) re-run A and B in TV at commission **0.0086% and 0.0125%** to replace the
geometric estimates with actual numbers; (2) THEN model slippage (asymmetric tick offsets). Fee is no
longer the blocker -- slippage + fill fidelity are.

## Caveats / things for Codex to scrutinize

- **Direction config drift (TVB-1 vs TVB-2).** This session also observed a *separate, now-gone*
  strategy instance that produced **389 trades, ALL long, zero shorts** (template-added mid-session).
  That instance almost certainly had `allow_short = false` or an asymmetric gate. The numbers in
  THIS table are bidirectional (shorts present). Exact numeric reconciliation with TVB-1 requires
  matching the direction config TVB-1 actually used (unspecified in the TVB-1 HANDOFF).
- **Intrabar fill fidelity / bar-magnifier NOT verified** (Codex trap #2). Fills use resting
  breakout STOP orders; without bar-magnifier / LTF data the intrabar level-break entry may read
  optimistic. [TVB-3: the setting is now CONFIRMED -- `use_bar_magnifier` (in_32) was OFF for
  these runs. The fidelity CHECK (re-run with it on, compare) remains open.]
- **HTF-open currency NOT yet verified** (P2a). The gate may read a stale (prior-period) open --
  a fidelity issue, not a leak, but it changes *which* strategy these numbers characterize. The
  `Timeframe Continuity [TFO]` indicator is now on the chart to enable the overlay check.
- **Fee semantics:** confirm 0.1%/fill (~0.2% round-trip) vs the intended venue cost; A @ OKX
  (~0.05%/fill) was NOT re-run this session (TVB-1 had it net-positive at PF 1.131).
- **Single regime.** This window is one ~4-month downtrend -> regime-flattery risk (charter trap
  #4). A second window/regime is needed before trusting the ranking.
- **Control "A" caveat:** run on a 60m chart with M/W/D/60 (faithful to TVB-1's Control A). The
  earlier hybrid on-chart config (M/W/D/60 on a *15m* chart) is neither control and was not used here.

## Deferred to next session (token budget)

- **Cherry-picked "obviously-profitable window" sanity test (brittle-on-purpose, charter S1):**
  pick a clean strong MSTR/MSTRUSDT trend window where the gate should be unmissably profitable
  zero-of-fee. If it is NOT, that exposes a bug (gate staleness, exit logic, short-side). High-value
  cheap bug-finder.
- **P2a:** verify HTF-open currency (overlay strategy FTFC coloring vs the TFO indicator).
- **P2b:** adopt local period-open reconstruction `ta.valuewhen(timeframe.change(tf), open, 0)`,
  trigger tick-offset (`high + syminfo.mintick`), chart-TF <= enabled-TF guard.
- **Confirm the fee sweep by ACTUAL re-run** (set `in_23` to **0.0086% and 0.0125%** for A and B) --
  the intermediate-rate verdicts above are the geometric model, not fresh backtests.
  [TVB-3 / Codex 3: target corrected from "0.0086% and 0.0864%" -- 0.0864% was the superseded
  pre-ground-truth taker guess; the operative pair is modal 0.0086% / notional-wtd 0.0125%.]
- ~~**Build the limit-entry (maker) variant** and run at 0.0086% (Pine change = STOP-and-ASK). Model
  says A -> +42%, B -> +25%; this is the real test of whether the edge survives execution.~~
  [SUPERSEDED by the `crossed`-flag resolution: xyz TAKER is the cheap rate, so the maker variant
  is no longer needed to rescue the fee verdict -- +38..42%/+5..25% are now the TAKER-rate
  expectations. A maker/retest variant, if ever built, is a DISTINCT strategy (different fills,
  non-fill risk), not a fee swap on these controls; carried as a charter S8 open question.]
- ~~**Verify the cash-dex taker rate** directly (only maker fills observed so far).~~
  [RESOLVED by the `crossed` re-pull: cash is 94.5% taker at 0.0086% -- see the resolved table.]
- **Slippage realism (re-scoped by TVB-3):** the runs already included `slippage = 1` tick/fill
  (see correction above), so the open work is INCREMENTAL -- validate 1 tick against real book
  depth at market-order size, and model asymmetric/deeper offsets if warranted.
- Add a **second regime window** (current window is a single ~4-month downtrend).

## Chart left in state

Strategy `35dVw8` restored to its as-found config: TFs **M/W/D/60**, fee **0.1%**, chart **15m**
(the non-canonical hybrid). Set Control B = enable 60/30/15 + disable M/W/D, chart 15m;
Control A = enable M/W/D/60 + disable 30/15, chart 60m. Input ids: in_2=M, in_4=W, in_6=D, in_8=60,
in_10=30, in_12=15 (bool enables); in_23 = commission percent.
[TVB-3: entity `35dVw8` no longer exists -- the user's layout churned between sessions. A fresh
instance (`mDKhus` at dump time; RE-DERIVE each session) was added from the same slot; its input-id
layout is identical to the map above.]

---

## TVB-3 addendum: settings dump (reproducibility record, 2026-07-02)

Full decode of the strategy instance's inputs + properties via CDP (`study.getInputValues()` +
`metaInfo().inputs` on the dataSources path). Instance = fresh add of saved slot `TFC Baseline`
(`USER;e7c8fd62...`, v13, saved 2026-06-30 during TVB-2). The TVB-2 entity `35dVw8` is gone, so
this dump is the SLOT-DEFAULT state; the TVB-2 run state = these defaults + the overrides TVB-2
documented setting via `indicator_set_inputs` (TF enables in_2..in_12, commission in_23 = 0 / 0.1,
direction in_0/in_1). Residual (recorded, not resolvable): any manual properties-dialog override
on `35dVw8` during TVB-2 would be invisible here; none is recorded or suspected -- every documented
manipulation went through the MCP.

**Slot-content finding:** the slot is the TVB-1 "CONTROL A + HIP-3 FEE TEST" variant, NOT
`pine/baseline_continuity.pine` verbatim: Pine v6 (auto-converted), `commission_value = 0.10`
hardcoded, defaults = Control A (M/W/D/60 on), **no leverage input** (`strategy.entry` has no
`qty`), so sizing is structurally `percent_of_equity` @ 100 = 1x. The doc's "v12" vs the current
v13: input-id layouts match exactly (in_23 = commission, etc.), so v12->v13 was content-equivalent
for run semantics.

Decoded properties (`strategy_props`; id -> internalID = value):

| id | internalID | value (slot default) | note |
|---|---|---|---|
| in_16 | default_qty_type | percent_of_equity | with in_17=100 -> 1x equity |
| in_17 | default_qty_value | 100 | |
| in_18 | initial_capital | 10000 | |
| in_19 | pyramiding | 0 | |
| in_20 | process_orders_on_close | false | exits fill next-bar open |
| in_21 | calc_on_every_tick | false | |
| in_22 | commission_type | percent | |
| in_23 | commission_value | 0.1 | the per-run override knob |
| in_24 | **slippage** | **1** (ticks) | **runs included 1 tick/fill** |
| in_25 | calc_on_order_fills | false | |
| in_26 | backtest_fill_limits_assumption | 0 | |
| in_27 | currency | NONE | |
| in_28 | close_entries_rule | FIFO | |
| in_29/in_30 | margin_long/short | 100/100 | |
| in_31 | risk_free_rate | 2 | affects Sharpe only |
| in_32 | **use_bar_magnifier** | **false** | **runs un-magnified** (trap #2 open) |
| in_33 | fill_orders_on_standard_ohlc | false | |
| in_40 | calc_on_every_history_tick | false | |

User inputs: in_0/in_1 = Allow Long/Short (true/true); in_2..in_13 = TF enable/TF pairs
(M,W,D,60 = true; 30,15 = false -- Control A defaults); in_14/in_15 = display bools.

Symbol (OKX:MSTRUSDT.P): type swap, minmov 1, pricescale 100 -> **mintick 0.01**.
Slippage cost at 1 tick: 0.01/price per fill (~0.01%/leg at the window's ~$100 lows, less at
higher prices), ~2 ticks/round-trip -- same order as the real taker fee (2 x 0.0125%).

### TVB-3 P2a result: the HTF-open gate is STALE (preflight N1 CONFIRMED)

Method: single-TF isolation on the live strategy instance (NOT the visual TFO overlay -- the TFO
indicator itself uses lookahead_on and is not a trustworthy reference). Gate set to D-only, then
60m-only; the strategy's own plotted period-open series (plot_1/plot_2) read via CDP and compared
to ground-truth period opens from the main series. TV's OKX daily bars confirmed to roll at
00:00 UTC (checked against the D chart directly).

Result (historical bars, both isolations, zero unexplained rows):
- D-only: every 15m bar of day N shows **open(N-1)**; only the LAST bar of the day (23:45,
  which closes simultaneously with the daily bar) shows open(N).
- 60m-only on 15m chart: bars :00/:15/:30 of hour H show **open(H-1)**; the :45 bar shows open(H).
  Summary over 57 bars: 43 prior-period, 14 current (all = last-bar-of-period merges), 0 other.

So `request.security(tf, open, lookahead_off)` returns the PRIOR period's open on historical
bars (the standard lookahead_off confirmed-bar merge). The TVB-1 header comment ("returns the
CURRENT period's open") is WRONG on historical bars. Consequently the TVB-1/2 numbers
characterize a **"close vs prior-period opens" gate**, not the intended TFO-style
"close vs current period opens" -- on Control A's 60m chart the 60m component is the classic
same-TF one-bar security lag. The realtime side (live bar returning the DEVELOPING period's
open -> backtest-vs-live asymmetry) is documented TV behavior but not yet directly observed
(needs a fresh bar to arrive with the study running). Fix = P2b local period-open
reconstruction; the staleness delta will be quantified by one bridge run (A @ 0.1%, fixed gate,
same window) vs the -12.0% above.

### TVB-3 P2b: gate FIXED + two more artifacts found and removed

The canonical source (`pine/baseline_continuity.pine`, now Pine v6, byte-identical to the TV
slot) replaces the security-based gate with **local period-open reconstruction**
`ta.valuewhen(timeframe.change(tf), open, 0)` -- chart-local data only, backtest == live by
construction. Regression: the P2a 60m-only probe on the fixed gate reads CURRENT on 57/57
bars (0 stale). Also added: trigger tick-offsets (`high + syminfo.mintick` / `low - mintick`;
strat-methodology trigger = level + one tick, enforcing the strict H > H[1] break), a
chart-TF <= enabled-TF guard (`runtime.error`, verified firing), and the corrected fee header.

**Artifact 1 discovered by the first bridge attempt -- margin-call deadlock.** With
100%-equity sizing and `margin_long/short = 100` (the silent defaults in ALL TVB-1/2 runs),
the emulator margin-calls every short on its first adverse tick (equity == required margin at
entry, so any adverse move violates). Worse: on 2026-04-02 a margin-call partially reduced a
short (88.118 -> 87.006) and the state-stop's `strategy.close` then filled the ORIGINAL
88.118, leaving an orphan +1.112-contract LONG that neither `close('Long')` nor
`close('Short')` could target -- the strategy sat not-flat and entered NOTHING for 3 months
(verified: order log ends Apr 2; orphan position numbers match openPL/-margin to the cent).
FIX: `margin_long = 0, margin_short = 0` in the source -- margin enforcement OFF; the
state-stop is the ONLY exit (as designed). NOTE: the TVB-1/2 SHORT legs were structurally
contaminated by partial margin-call liquidations (forced early truncation); another reason
those numbers do not characterize the designed strategy.

**Artifact 2 -- input ids DID shift** when the margin args were added (margin_long/short
materialized at in_25/in_26, pushing currency to in_29, close_entries_rule to in_30 etc.).
A stale-id write set currency=0 and broke the study ("Can't parse pine") until re-derived
and repaired. The "re-derive ids after ANY source change" rule is not optional.

### TVB-3 corrected-gate results: full fee sweep (replaces the geometric estimates)

All ACTUAL backtest runs (not models). Corrected gate + tick-offset triggers + margin off;
slippage 1 tick/fill; bar magnifier OFF; bidirectional; 1x (100% equity); initial 10k;
window 2026-02-25 10:00Z -> 2026-07-03 ~03:00Z (same start as TVB-2 = the data boundary;
ends +3 days later, and those 3 days add a violent +19% tail rally -- buyHold is -22.5%
here vs -29..-31.5% in TVB-2). All exits state-stop; 0 margin calls; 0 open residuals.

| Control | fee/fill | Trades (L/S) | Net % | PF | Win % | MaxDD % | Sharpe |
|---|---|---|---|---|---|---|---|
| A (M/W/D/60, 60m) | 0% | 317 (164/153) | **+50.0%** | 1.316 | 38.8% | - | - |
| A | 0.0086% (modal) | 317 | **+42.0%** | 1.267 | 37.5% | - | - |
| A | 0.0125% (ntl-wtd) | 317 | **+38.6%** | 1.245 | 36.9% | 16.4% | 0.87 |
| A | 0.1% (bridge) | 317 | -20.4% | 0.864 | 30.0% | 36.6% | -0.45 |
| B (60/30/15, 15m) | 0% | 2801 (1354/1447) | **+86.5%** | 1.143 | 36.7% | - | - |
| B | 0.0086% | 2801 | **+15.2%** | 1.031 | 34.9% | - | - |
| B | 0.0125% | 2801 | **-7.4%** | 0.983 | 34.1% | - | - |
| B | 0.1% (bridge) | 2801 | -99.3% | 0.385 | 22.1% | - | - |

Long/short split at 0.0125%: A = long +34.7% (PF 1.50) / short +3.9% (PF 1.04);
B = long +15.4% / short -22.8%.

**Reading (charter: questions, not verdicts):**
1. **The stale gate materially mis-characterized the strategy.** Corrected gate: A trades
   317 vs 261 (+21%), B 2801 vs 2301 (+22%) -- the current-period gate flickers MORE (the
   same-TF component now demands the current chart bar be green/red from its own open).
   Bridge points (0.1%): A -20.4%/PF 0.864 vs stale -12.0%/0.906; B -99.3%/0.385 vs
   -98.1%/0.400. Similar qualitative story at the too-high fee, but the trade SET is
   different -- old numbers should not be quoted for this strategy.
2. **A at real fees: the geometric prediction (+38..42%) is CONFIRMED almost exactly
   (+38.6..+42.0%)** -- partly coincidence (stronger raw edge +50 vs +48.2 offset by more
   trades), but the conclusion stands on actuals now: **A is clearly net-positive at real
   cost, PF 1.25-1.27, maxDD ~16%, both directions non-negative.**
3. **B's sign now FLIPS inside the real-fee band: +15.2% at modal 0.0086% but -7.4% at
   notional-weighted 0.0125%** (PF 0.98-1.03 straddling 1.0). The model band was +5..25%;
   the corrected gate's extra churn (+500 trades) pushed B onto the knife's edge. B's short
   side is decisively negative at real fees (-12 to -23%). Turnover remains the lever, now
   via fee-band sensitivity rather than outright death.
4. Treat A's numbers as a QUESTION per charter S0: single window (now with a +19% tail
   rally inside it), regime flattery unresolved (second window still pending), bar-magnifier
   fidelity unchecked, slippage realism (is 1 tick right for ~90-contract market orders?)
   unmodeled. The corrected-gate edge concentrates in longs during a window that crashed
   then V-rallied -- hunt the regime where it dies before believing PF 1.25.

Caveats on attribution: the old-vs-new deltas bundle {gate fix + tick offsets (expected
~epsilon) + margin-enforcement removal + 3-day window extension}; decomposition runs were
deliberately not spent (the corrected configuration is the go-forward baseline).
