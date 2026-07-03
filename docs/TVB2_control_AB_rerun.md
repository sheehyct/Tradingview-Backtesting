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

---

## TVB-4 (2026-07-03): preflight 1 -- bar-magnifier fidelity check

Setup: the TV slot "TFC Baseline" was found OVERWRITTEN by a 3-line "E2E Test" indicator
stub (side-effect of the jackson e2e compile tests run during TVB-3 -- the suite writes into
whatever slot the editor has open; jackson backlog: e2e must create + verify its own slot).
Restored byte-identical from `pine/baseline_continuity.pine` (slot pineVersion 16 -> 17),
re-added to the chart => NEW entity `xJzX3B`. Input ids re-derived: map UNCHANGED from TVB-3
(in_23 commission, in_24 slippage, in_25/26 margins, in_32 magnifier; TF enables in_2..in_13).
History loaded to the floor before every read (12280 15m bars / 3074 60m bars, first bar
2026-02-25 10:00Z). Window here ends 2026-07-03 ~11:30Z (~8h later than the TVB-3 sweep).
Observed: a fresh strategy add computes over full deep history even while the chart series
holds only ~300 bars -- history was still reloaded to the floor for method consistency.

All runs at fee 0.0125%/fill, slippage 1 tick, margin 0/0, bidirectional, 1x, initial 10k:

| Control | Magnifier | Trades (L/S) | Net % | PF | Win % | MaxDD % | Sharpe |
|---|---|---|---|---|---|---|---|
| B (60/30/15, 15m) | OFF | 2811 (1360/1451) | -10.06% | 0.978 | 34.0% | 37.3% | -0.13 |
| B | ON | 2810 (1360/1450) | -11.13% | 0.975 | 33.8% | 37.8% | -0.14 |
| A (M/W/D/60, 60m) | OFF | 319 (166/153) | +38.00% | 1.241 | 36.7% | 16.4% | 0.88 |
| A | ON | 319 (166/153) | +38.00% (bit-identical) | 1.241 | 36.7% | 16.4% | 0.88 |

A's bit-identical ON read was verified against a live recompute path, not a stale report:
with the magnifier flag ON, nudging commission to 0.02% recomputed to +31.5%, and restoring
0.0125% returned the EXACT original bits. The magnifier changes zero fills on Control A.

**Reading:**
1. **No sign flip anywhere; the intrabar-fill approximation (charter trap 7.2) is NOT
   materially distorting the corrected controls.** B: -1.07pp net / -0.0026 PF / one fewer
   trade; A: literally zero.
2. Mechanism: this architecture is nearly path-independent intrabar -- entries are stop
   orders that fill AT the stop price, the only exit is the close-based state-stop filling
   at the NEXT bar's open, no intrabar targets/stops, pyramiding 0. The magnifier only bites
   where a sub-bar gaps THROUGH an armed stop (worse fill) or re-sequences a fill; rare
   (B's 2810 trades accumulate ~1pp of drag; A's 319 trades hit zero occurrences).
3. Consequence for the sweep: magnifier can stay OFF (add ~1pp pessimism mentally on
   15m-class high-churn configs). CARVE-OUT: a future PRICE-stop variant (intrabar stop
   exits) would be magnifier-SENSITIVE -- re-run this check before trusting any price-stop
   numbers (charter S8 open question).
4. Window-tail note: B-OFF reads -10.06% here vs -7.4% in the TVB-3 sweep, from ~8h more
   tail + 10 more trades alone -- B's knife-edge fee-band sensitivity re-demonstrated by
   pure window drift. A moved +38.6% -> +38.0% (stable).
5. Operational: trade/fill timestamps stay bar-granular with the magnifier ON (all 320 A
   entries stamp on exact hour boundaries), so fill times CANNOT be used to audit whether
   the magnifier applied -- use the recompute-control method above.

## TVB-4 (2026-07-03): preflight 2 -- kind-window bug-test (charter S1, brittle-on-purpose)

Protocol fixed a-priori: (1) pick the obviously-favorable window from PRICE DATA ALONE
(sliding-window scan of the 60m closes, no strategy output consulted); (2) at ZERO fee the
gate's trades inside that window must be unmissably profitable and directionally coherent,
else hunt a logic bug before generating sweep data. Windows found by the scan:
KIND-UP = Apr 12 13:00Z -> Apr 22 13:00Z (+43.8% B&H, max in-window DD 7.9%), with core
Apr 12-17 (+36.0%, DD 3.9%); KIND-DOWN mirror = Jun 16 10:00Z -> Jun 26 10:00Z (-36.5% B&H).
Method: zero-fee full runs; per-trade percents from `reportData().trades` compounded over
trades ENTERED in-window (100%-equity sizing makes product(1+pp) the right aggregate;
validated full-list: B 81.6% == reported net; A 50.4% vs 49.5% incl. open trade).

| Control | Window | Trades (L/S) | Win % | Compounded | Longs | Shorts |
|---|---|---|---|---|---|---|
| A | KIND-UP Apr12-22 | 35 (34/1) | 37% | **+20.2%** | +20.6% | -0.3% |
| A | KIND-UP-CORE Apr12-17 | 20 (19/1) | 50% | **+24.7%** | +25.1% | -0.3% |
| A | KIND-DOWN Jun16-26 | 36 (0/36) | 28% | **+8.9%** | -- | +8.9% |
| B | KIND-UP Apr12-22 | 211 (108/103) | 40% | **+19.5%** | +26.0% | -5.1% |
| B | KIND-UP-CORE Apr12-17 | 106 (58/48) | 42% | **+23.7%** | +21.3% | +2.0% |
| B | KIND-DOWN Jun16-26 | 220 (95/125) | 37% | **+15.7%** | -0.1% | +15.8% |

**VERDICT: PASS -- no logic-bug signature.** Both controls are unmissably positive zero-fee
in the kind windows, and the direction gating is coherent where it matters most: A takes
ZERO longs inside the -36.5% crash and 34-of-35 longs inside the rally -- the FTFC
directional agreement is real, not an artifact.

**Findings (surprises are deliverables):**
1. **A's down-capture is structurally weak, and it is NOT a fee story.** +8.9% captured of
   a -36.5% crash (25% capture) vs +24.7% of a +36% rally core (69% capture), at ZERO fee,
   in the kindest possible short regime, 28% win rate. The full-run long-heavy skew
   (long +34.7% / short +3.9%) is now visible as a structural short-side weakness --
   plausibly the close-based state-stop giving back violent counter-trend bounces, which
   crashes have more of. Question to carry, not verdict.
2. **B spends ~half its kind-window trades FIGHTING the trend.** In the Apr rally B took
   108 longs (+26.0%) and 103 shorts (-5.1%); the 60/30/15 set flips short on every
   pullback deep enough to crack the 60m open. Direct, data-generated motivation for the
   charter 3.3 two-layer design: an HTF regime layer would have suppressed ~103
   counter-trend shorts inside a +43.8% rally. (Generated for a different question --
   noted, not selected on.)
3. Win rates stay 28-50% even in the kindest windows; the edge is the ~2:1 win/loss
   asymmetry, not hit rate -- normal for stop-entry trend-following, worth remembering
   when a sweep row shows a "bad" win rate.
4. Method note for future probes: in `reportData().trades`, direction is `e.tp`
   ("le"/"se"); `e.b` is a BAR INDEX (an initial all-long misread came from decoding
   `e.b` as a buy flag -- caught by the impossible zero-shorts-in-a-crash split).

## TVB-4 (2026-07-03): two-layer regime ablation (charter 3.3 + S8 decision)

The regime layer (`pine/baseline_continuity.pine` TVB-4 rev; regression GREEN -- reg_mode
off reproduces all 2811 reference trades byte-identically) adds an HTF M/W/D FTFC gate over
the Control-B execution layer (60/30/15, 15m). `reg_mode`: off = control; `stand_aside` =
enter only when the regime agrees with the trade direction (grey and opposite both block);
`size_down` = full size when aligned, HALF (fixed a-priori 50%) when grey, opposite blocks.
No regime exit in v1. Ablation vs the B-alone control (NOT a tournament). Window Feb 25
10:00Z -> Jul 3 16:15Z (~2.5h more tail than the preflights; B-alone control re-read in this
same window: @0 +84.7%, @0.0125 -8.60%). Entity re-added post-restart (9lQ6Gn); id map
unchanged. All runs marginCalls 0, open trades <= 1.

| reg_mode | fee/fill | Trades (L/S) | Net % | PF | MaxDD % | Sharpe | Long % | Short % |
|---|---|---|---|---|---|---|---|---|
| off (control) | 0 | 2814 (1361/1453) | +84.70 | 1.139 | 22.3 | 0.83 | +66.35 | +18.35 |
| off (control) | 0.0125 | 2814 (1361/1453) | **-8.60** | 0.981 | 37.3 | -0.10 | +15.59 | -24.19 |
| stand_aside | 0 | 922 (488/435) | +76.63 | 1.355 | 11.2 | 1.15 | +48.06 | +28.57 |
| stand_aside | 0.0086 | 922 (488/435) | +50.72 | 1.242 | 12.9 | 0.89 | +35.15 | +15.57 |
| stand_aside | 0.0125 | 922 (488/435) | **+40.26** | 1.195 | 14.3 | 0.75 | +29.80 | +10.46 |
| size_down | 0 | 2390 (1212/1179) | +68.73 | 1.204 | 18.2 | 0.92 | +43.52 | +25.21 |
| size_down | 0.0125 | 2390 (1212/1179) | **+12.84** | 1.044 | 26.4 | 0.26 | +16.00 | -3.15 |

Kind-window compounding (zero-fee, product(1+pp) over trades ENTERED in-window; split by `e.tp`):

| mode | KIND-UP Apr12-22 | KIND-UP-CORE Apr12-17 | KIND-DOWN Jun16-26 |
|---|---|---|---|
| B-alone | +19.5% (L108/S103) | +23.7% (L58/S48) | +15.7% (L95/S125) |
| stand_aside | +20.4% (L83/S4) | +16.7% (L46/S4) | +13.1% (L0/S104) |
| size_down | +16.6% (L111/S64) | +16.9% (L58/S31) | +20.1% (L49/S131) |

**Predictions scorecard (pre-registered in the plan; surprises are the deliverable):**
- **P1 CONFIRMED** -- stand_aside cuts trades 2814 -> 922 (67% fewer; grey + counter-regime
  suppression). size_down 2814 -> 2390 (blocks opposite, halves grey).
- **P2 CONFIRMED** -- KIND-UP stand_aside +20.4% >= B-alone +19.5%: it killed 99 of 103
  counter-trend shorts (-5.1% -> -0.2%), at the cost of 25 longs (+26.0% -> +20.6%).
- **P3 PARTIAL** -- KIND-DOWN stand_aside +13.1% vs B-alone +15.7% (~2.6pp cost, not
  "~="): killed all 95 counter-trend longs but also dropped 21 shorts (125 -> 104) to
  regime timing. Small honest cost, not free.
- **P4 CONFIRMED (dramatically)** -- THE thesis. At real fee 0.0125 stand_aside is
  **+40.26% vs the control's -8.60%** -- a ~49pp swing, a sign flip, drawdown more than
  halved (37.3% -> 14.3%), Sharpe -0.10 -> +0.75. The suppressed trades were
  disproportionately fee-burners: at ZERO fee stand_aside kept 90% of the P&L (+76.6 vs
  +84.7) on 33% of the trades; removing their fee drag is what flips the sign.
- **P5 CONFIRMED + LOCATED** -- transition-lag cost is real. At zero fee stand_aside
  gives up ~8pp (+76.6 vs +84.7), and it concentrates at trend births: KIND-UP-CORE
  (the sharpest rally leg) stand_aside +16.7% vs B-alone +23.7% (-7pp) because the slow
  M/W/D regime had not flipped up yet during the V-bottom -- it blocked the earliest,
  best longs (46 vs 58). The slow gate pays a documented late-entry tax; at real fees the
  chop-savings dwarf it, but the tax is visible and structural.
- **P6 CONFIRMED** -- size_down (+12.84%) lands between control (-8.60%) and stand_aside
  (+40.26%) at 0.0125. Keeping grey exposure at half-size retains half the fee drag.

**S8 DECISION (data-driven): STAND ASIDE beats SIZE DOWN on grey.** Charter Section 8's
load-bearing open question is answered by the ablation: at real fees stand_aside dominates
size_down on every axis (net +40.26 vs +12.84, PF 1.195 vs 1.044, DD 14.3 vs 26.4, Sharpe
0.75 vs 0.26). This confirms the expectancy argument -- sizing down a fee-negative churn
stream still loses to skipping it; "stand aside when the playbook stops" beats "trade
smaller." Recommend stand_aside as the grey rule going forward (Fable to ratify post-reset).

**Surprise flagged:** size_down WINS the KIND-DOWN window (+20.1% vs stand_aside +13.1% and
B-alone +15.7%) -- the one window where half-size grey exposure paid, because the crash had
grey stretches where reduced shorts still profited and stand_aside sat out. It does NOT
survive to the full-fee sample (stand_aside dominates overall), but it says the grey rule is
regime-dependent: in a sustained one-way move, staying partially in beats standing aside;
across mixed regimes with real fees, standing aside wins. A vol/trend-conditional grey rule
is a (parked) charter S6 avenue this surfaces -- do NOT tune it on this sample.

**Caveats (charter S0 -- questions, not verdicts):** single instrument, single window with a
crash + V-rally inside it; the +40.26% still concentrates long (+29.80 vs short +10.46); the
regime late-entry tax (P5) will bite harder in a sample with more sharp reversals; slippage
realism and the OKX->HL venue gap remain unmodeled. stand_aside is a strong ablation result,
not a deployability verdict. The two-layer earns its place as the go-forward ablation
baseline for the priority-4 timeframe-set sweep.

## TVB-5 (2026-07-03): S8 ratification + default-vs-input decision (Fable 5)

**S8 stand_aside RATIFIED** as the grey rule for the two-layer baseline. Independent read
supports it beyond the fee story:

- **The suppressed stream is zero-expectancy churn GROSS, not sacrificed edge.** Control ->
  stand_aside at ZERO fee gives up only a 1.8470/1.7663 = +4.6% compounded factor across the
  ~1,892 suppressed trades, i.e. ~+0.002% per trade gross -- an order of magnitude below the
  0.025% round-trip commission alone (before slippage). Any positive fee makes that stream
  strictly negative net; halving it (size_down) halves the bleed, skipping it removes it.
  P6's in-between landing (+12.84) is that expectancy arithmetic playing out, which is why
  the S8 conclusion is trusted: the three modes cohere under one mechanism.
- **Not purely a fee story.** At zero fee stand_aside already dominates risk-adjusted
  (PF 1.355 vs 1.204/1.139, DD 11.2 vs 18.2/22.3, Sharpe 1.15 vs 0.92/0.83): the
  regime-aligned subset is higher-quality per trade even gross.
- **P5 reading RATIFIED as fair and structural.** M/W/D cannot flip inside a V-bottom by
  construction, so the late-entry tax concentrates at trend births (46 vs 58 core-rally
  longs, -7pp). Structural property of any slow gate, not sample noise.
- **Named kill-regime for the S8 rule (hunt it in the second window):** trendy-but-sharply-
  reversing samples, where the late-entry tax recurs at every flip while the chop savings
  shrink. Extended CHOP should conversely favor stand_aside (sits flat) over size_down
  (keeps half-size churn bleed). The TVB-4 window (crash + V-rally = two clean trends) is
  KIND to a regime gate -- regime flattery applies to the regime layer itself, so the S8
  decision is provisional on the second-window read.
- **size_down KIND-DOWN surprise stays PARKED** (vol/trend-conditional grey rule, charter
  S6 avenue) -- not tuned on this sample.

**DEFAULT-VS-INPUT DECIDED: `reg_mode` stays an INPUT, default `off`.** (a) Defaults ==
TVB-3 control is the regression anchor (2811-trade byte-identity); flipping the default
silently breaks every future regression read. (b) The run harness sets in_16 explicitly per
cell; a code default buys nothing operationally. (c) stand_aside is one-instrument /
one-window data -- baking it into code before the second regime window runs would fossilize
a sample-derived choice as if structural. Instead the **TVB-5 two-layer baseline
configuration is declared as `reg_mode = stand_aside`, explicitly set per run.** Revisit
the default only if the second window confirms.

Counting note (Codex TVB-4 LOW 2): the L/S splits in the ablation tables above include the
open trade (e.g. 488+435 = 923 = 922 closed + 1 open); `tv_dump.mjs` is fixed in TVB-5 to
report closed-basis splits.

### TVB-5 reproducibility re-run (Codex TVB-4 LOW 3): headline rows re-run + committed

Fresh re-stage (TV restart, entity re-added as `bNqlkZ`; id map re-derived, UNCHANGED from
TVB-4 at pineVersion 18.0). Window Feb 25 10:00Z (floor, 12,306 bars) -> **Jul 3 18:00Z**
(~1.75h more tail than the TVB-4 reads at 16:15Z -- the deltas below are that tail plus the
open-trade mark). All runs: marginCalls 0, open trades 1, history verified at floor before
every read. Dumps committed as `analysis/reference/tvb5_R*.json`; every ablation-table row
now has a committed artifact (this set, plus TVB-4's zero-fee `tvb4_R1a`/`tvb4_R2a` and
`tvb4_trades_B_0fee` for the older window end).

| cell | TVB-5 fresh (18:00Z end) | TVB-4 table (16:15Z end) | artifact |
|---|---|---|---|
| off @0 | +83.84%, 2815 (1362/1453), PF 1.137, DD 22.3, Sh 0.82 | +84.70%, 2814, PF 1.139, DD 22.3, Sh 0.83 | tvb5_R0a_off_0fee.json |
| off @0.0125 | **-9.06%**, PF 0.980, DD 37.3, Sh -0.11 | -8.60%, PF 0.981, DD 37.3, Sh -0.10 | tvb5_R0b_off_0125.json |
| stand_aside @0 | +76.18%, 923 (488/435), PF 1.352, DD 11.2, Sh 1.15 | +76.63%, PF 1.355, DD 11.2, Sh 1.15 | tvb5_R1a_standaside_0fee.json |
| stand_aside @0.0086 | +50.31%, PF 1.240, DD 12.9, Sh 0.89 | +50.72%, PF 1.242, DD 12.9, Sh 0.89 | tvb5_R1b_standaside_0086.json |
| stand_aside @0.0125 | **+39.86%**, PF 1.193, DD 14.3, Sh 0.75 | +40.26%, PF 1.195, DD 14.3, Sh 0.75 | tvb5_R1c_standaside_0125.json |
| size_down @0.0125 | **+12.53%**, 2391 (1212/1179), PF 1.043, DD 26.4, Sh 0.26 | +12.84%, PF 1.044, DD 26.4, Sh 0.26 | tvb5_R2b_sizedown_0125.json |

Every row reproduces within tail drift; MaxDD and Sharpe match exactly on all six cells.
The sign-flip headline (control negative, stand_aside strongly positive at real fee) and the
S8 ordering (stand_aside > size_down > off) are CONFIRMED in the fresh window. L/S splits
above are CLOSED-basis (the fixed `tv_dump.mjs`): stand_aside's 923 closed = TVB-4's 922
closed + the then-open trade having since closed in the tail; its closed 488/435 equals the
TVB-4 open-inclusive split, as expected. Trade-list side-note for future probes: the open
position appears in `reportData().trades` as a pseudo-closed row whose exit is a
mark-to-market at a WALL-CLOCK ms timestamp (not a bar boundary); closed set = first
`performance.all.totalTrades` list entries (entry-ordered).

## TVB-5 (2026-07-03): priority-4 timeframe-set sweep -- PRE-REGISTRATION (locked before any run)

Design chosen a-priori WITH the user (charter S5/S8.3); sets are structural candidates and
will NOT be tuned on results. Ablation vs controls, not a tournament: no winner is crowned;
the spread, the mechanism reads on poor cells, and flagged surprises are the deliverables.

**Grid (3 regime x 3 exec, all reg_mode=stand_aside per the ratified S8 rule):**

| code | Regime set | structural reason (fixed a-priori) |
|---|---|---|
| R1 | M/W/D | incumbent calendar-institutional anchor (baseline regime) |
| R2 | W/D/12h | 24/7-native: drops the near-static month, adds the 12h UTC half-day; prediction: less P5 tax, more chop admitted |
| R3 | D/12h/4h | fast regime; stress-tests S8/P5 from the other side; prediction: converges toward B-alone |

| code | Exec set (chart TF = lowest gate TF) | structural reason |
|---|---|---|
| E1 | 60/30/15 (15m chart) | incumbent Control-B execution |
| E2 | 240/60/15 (15m chart) | span stretched upward 16:4:1; does a stricter exec span SUBSTITUTE for the regime layer? |
| E3 | 240/120/60 (60m chart) | A-like turnover with the two-layer structure intact; most fee-robust column expected |

**Windows / passes (fixed before results):**
- **W1** OKX:MSTRUSDT.P, Feb 25 floor -> present: full grid x {0, 0.0125} fees + fresh
  Control-A re-read (60m). R1E1 cells already dumped (tvb5_R1a/R1c above).
- **W2 (instrument robustness)** Trade[XYZ] HIP-3 Hyperliquid:SP500USDC.P, 15m, same
  calendar window: B-alone + R1E1 baseline @ {0, 0.0125}; remaining 15m grid cells
  (R{1,2,3} x E{1,2}) @0.0125; Control A @0.0125. SELECTION RULE (a-priori): use
  SP500USDC.P if its 15m history floor is on or before 2026-03-15; else fall back to
  OKX:BTCUSDT.P. Index-class perp on the TARGET venue = maximum instrument diversity
  available there.
- **W-venue (fidelity check, NEW -- HIP-3 listings hit TV 2026-07-02)** Trade[XYZ]
  MSTRUSDC.P 15m, same window: B-alone + R1E1 stand_aside @0.0125 (+@0) vs the OKX
  MSTRUSDT.P equivalents. Directly measures the standing "OKX->HL venue gap" caveat on the
  SAME underlying. Expectation: same sign/direction, different magnitude; a large gap
  QUANTIFIES the caveat, a small gap validates the proxy.
- **W3 (time robustness)** OKX:BTCUSDT.P, 60m chart (floor expected ~1.5y back):
  Control A + R{1,2,3} x E3 @0.0125 (+@0 for decomposition); ONE size_down spot-check on
  R1E3 (S8 decision-robustness in a different sample, NOT a tuning pass). The named
  kill-regime hunt (sharp alternating trends / extended chop sub-windows) lives here.

**Pre-registered predictions:**
- SP1: regime-speed gradient -- trade count rises R1 -> R2 -> R3; the P5 late-entry tax
  shrinks in the same order; R3 lands closest to B-alone.
- SP2: exec-span substitution -- E2 cuts trades vs E1, with SMALLER marginal benefit under
  slower regimes (layer redundancy visible as sub-additive improvements).
- SP3: E3 is the most fee-robust column (lowest fee sensitivity 0 -> 0.0125).
- SP4: the 9-cell spread at real fee is WIDE and the incumbent R1E1 does NOT top the table;
  a tight cluster of great results is itself a red flag to investigate.
- SP5: W2 preserves directions but shifts magnitudes substantially; tight replication would
  itself be suspicious (shared macro window).
- SP6: W3 contains at least one sub-regime where the two-layer UNDERPERFORMS its control --
  locating the kill-regime is a deliverable, not a failure.

Dump naming: `analysis/reference/tvb5_{W1|W2|WV|W3}_R{r}E{e}_{fee}.json` (fee 0 | 0086 |
0125); controls `tvb5_{W}_ctrlA_{fee}.json` / `tvb5_{W}_ctrlB_{fee}.json`. Sanity gates
EVERY run: marginCalls 0, open trades <= 1, history at floor before reading, closed-basis
L/S. Fees: commission only at 0.0086/0.0125 percent per fill + slippage 1 tick/fill (the
TVB-3 convention); NEVER report a single-fee verdict.

## TVB-5 (2026-07-03): sweep RESULTS (35 runs, all sanity gates green)

**Window discovery notes (pre-registration amendments, justified in-flight):**
Trade[XYZ] SP500USDC.P has NO TV backfill (feed starts 2026-07-03 18:00Z -- listed on the
dex ~yesterday) -> the pre-registered fallback fired, W2 = OKX:BTCUSDT.P. But xyz
**MSTRUSDC.P HAS deep backfill** (19,772 15m bars to 2025-12-02) -> W-venue upgraded: full
7-month runs + analytical window-slicing via `analysis/window_compound.py` (per-trade pp is
size-invariant; product(1+pp) over in-window entries -- the validated kind-window method;
unit-tested, 9/9 suite green). BTC 15m floors 2025-12-01 (~20.6k bar cap); BTC 60m reaches
**2024-01-01** (2.5 years) -- W3 got a far longer look-back than planned.

### W1 -- OKX:MSTRUSDT.P grid (Feb 25 10:00Z -> Jul 3 ~18:00Z)

| cell | chart | trades (L/S closed) | @0 | @0.0125 | PF / DD / Sharpe @0.0125 |
|---|---|---|---|---|---|
| ctrlB (B-alone) | 15m | 2815 (1362/1453) | +83.84 | **-9.06** | 0.980 / 37.3 / -0.11 |
| ctrlA (M/W/D/60) | 60m | 321 (168/153) | +50.03 | **+38.45** | 1.243 / 16.4 / 0.87 |
| R1E1 (baseline) | 15m | 923 (488/435) | +76.18 | **+39.86** | 1.193 / 14.3 / 0.75 |
| R1E2 | 15m | 824 (432/392) | +58.18 | +28.72 | 1.154 / 14.5 / 0.98 |
| R1E3 | 60m | 277 (143/134) | +43.41 | +33.80 | 1.253 / 13.9 / 0.93 |
| R2E1 | 15m | 1108 (545/563) | +62.08 | +22.85 | 1.093 / 14.6 / 0.75 |
| R2E2 | 15m | 1035 (504/531) | +45.68 | +12.45 | 1.056 / 16.7 / 0.65 |
| R2E3 | 60m | 342 (165/177) | +24.23 | +14.03 | 1.089 / 24.7 / 0.65 |
| R3E1 | 15m | 1600 (795/805) | +13.33 | **-24.05** | 0.909 / 31.0 / -0.67 |
| R3E2 | 15m | 1653 (821/832) | +16.88 | -22.70 | 0.917 / 29.9 / -0.66 |
| R3E3 | 60m | 541 (261/280) | +7.27 | -6.32 | 0.970 / 31.4 / -0.21 |

Spread at real fee: **-24.05 to +39.86** across 9 a-priori cells -- wide, as wanted.
Regime-set columns are MONOTONE: R1 (M/W/D) > R2 (W/D/12h) > R3 (D/12h/4h) in every exec
column, at both fees, on every risk metric.

### W2 -- OKX:BTCUSDT.P 15m (Dec 1 -> Jul 3; instrument robustness)

| cell | trades | @0 | @0.0125 | PF @0.0125 |
|---|---|---|---|---|
| ctrlB | 4835 | -11.82 | **-73.67** | 0.771 |
| R1E1 | 1303 | +14.64 | **-17.23** | 0.899 |
| R1E2 | 1170 | -- | -20.03 | 0.869 |
| R2E1 | 1881 | -- | -33.24 | 0.824 |
| R2E2 | 1763 | -- | -37.49 | 0.791 |
| R3E1 | 2711 | -- | -44.05 | 0.829 |
| R3E2 | 2795 | -- | -47.66 | 0.816 |

Sub-window split (window_compound, @0.0125): ctrlB shared-window -52.3% / prefix -44.8%;
R1E1 shared -11.5% / prefix -6.5%. **The strategy has NO edge on BTC in any tested
stretch** -- B-alone is negative even at ZERO fee (-11.8%). Yet the regime-column ordering
(R1 > R2 > R3) and the layer benefit (ctrlB -73.67 -> R1E1 -17.23) replicate exactly.

### W3 -- OKX:BTCUSDT.P 60m, 2024-01-01 -> 2026-07-03 (2.5y; time robustness + kill-regime)

| cell | trades | @0 | @0.0125 | PF / DD @0.0125 |
|---|---|---|---|---|
| E3-only (reg off) | 5212 | -- | **-90.43** | 0.805 / 90.7 |
| R1E3 size_down | 4771 | -- | -68.10 | 0.852 / 69.2 |
| R1E3 stand_aside | 1780 | -1.22 | **-36.71** | 0.907 / 44.7 |
| R2E3 | 2552 | -25.69 | -60.74 | 0.853 / 62.2 |
| R3E3 | 3896 | -40.03 | -77.36 | 0.822 / 77.7 |
| ctrlA | 2070 | +8.88 | -35.12 | 0.918 / 49.7 |

S8 spot-check: **off -90.43 < size_down -68.10 < stand_aside -36.71** -- the TVB-4 grey
ordering holds in a 2.5-year, different-instrument sample. R1E3 gross over 2.5y = -1.22%:
the continuity edge on BTC is ZERO before fees.

### W-venue -- Trade[XYZ] MSTRUSDC.P 15m (Dec 2 -> Jul 3) vs the OKX proxy

Full-window runs: ctrlB @0 +216.85 (4306 tr) / @0.0125 +7.98 (PF 1.015, DD 58.9);
R1E1 @0 +121.46 (1300 tr) / @0.0125 +60.01 (PF 1.239, DD 23.9).

Shared-window comparison (Feb 25 10:00Z ->, method-matched compounding, closed trades):

| config, fee | OKX MSTRUSDT.P | xyz MSTRUSDC.P | trade counts |
|---|---|---|---|
| ctrlB @0.0125 | **-9.05%** (L+19.3/S-23.8) | **+80.17%** (L+59.8/S+12.8) | 2815 vs 2708 |
| R1E1 @0.0125 | +39.88% (L+29.8/S+7.8) | **+83.07%** (L+37.6/S+33.0) | 923 vs 917 |
| ctrlB @0 | +83.85% | +254.54% | -- |
| R1E1 @0 | +76.18% | +130.22% | -- |

Prefix (Dec 2 -> Feb 25, the pre-crash stretch, xyz): ctrlB @0 **-10.68%** / @0.0125
-40.09%; R1E1 @0 -3.83% / @0.0125 -12.61%. **The kill-regime is located ON the target
instrument:** the same system that makes +254% gross in Feb-Jul chops to negative gross in
Dec-Feb.

### Predictions scorecard (pre-registered above)

- **SP1 half-REFUTED (mechanism found):** trade count does rise R1->R2->R3, but value
  FALLS monotonically and R3 lands BELOW B-alone even at zero fee (W1: +13.3 vs +83.8
  gross). The fast regime is ANTI-selective, not convergent: at D/12h/4h scale the regime
  is a lagged momentum signal correlated with the exec layer -- it re-admits chop late and
  blocks trend births. This is the charter S6 "second strategy with its own error,
  correlated with what it chases" failure mode, observed empirically. The M/W/D "late-entry
  tax" (P5) is the price of the ONLY regime slow enough to be a filter instead of a
  follower.
- **SP2 REFUTED:** E2 (240/60/15) does not substitute for the regime layer -- it degrades
  every pairing it touches (R1E2 +28.72 < R1E1 +39.86). Widening the exec span is not a
  regime layer.
- **SP3 CONFIRMED strongly:** E3 fee sensitivity 9.6-13.6pp vs 29-40pp for E1/E2 columns.
- **SP4 REFUTED (flagged honestly):** the incumbent R1E1 DID top W1 at real fee (+39.86,
  narrowly over ctrlA +38.45 and R1E3 +33.80). The spread was wide as predicted. Note the
  caveat: the S8 grey rule inside R1E1 was data-decided on this same window (TVB-4); the
  robustness passes are what keep this from being circular -- and they show the edge is
  regime-local, not that the config is special.
- **SP5 CONFIRMED:** BTC preserves every ORDERING (layer benefit, regime-speed gradient,
  S8 triplet) while the strategy itself is dead there. Structure generalizes; edge does not.
- **SP6 CONFIRMED + LOCATED:** the kill-regime is Dec2025-Feb2026 MSTR chop (negative
  GROSS) and all of BTC. A continuity system needs a continuity-rich instrument/period;
  MSTR-class high-vol equity perps in trending regimes are where the edge lives.

### Session surprises (primary deliverables)

1. **The venue gap REVERSES the assumed direction and is huge.** Same underlying, same
   window, near-identical trade counts: xyz fills capture dramatically more per trade than
   OKX (ctrlB @0.0125: +80 vs -9). OPEN QUESTION, not a verdict: the xyz TV backfill's
   provenance/quality is unverified (feed went live on TV 2026-07-02; history presumably
   HL-sourced). MUST cross-validate xyz TV bars against Hyperliquid SDK candles before
   trusting any xyz number. If real, the OKX proxy has been the CONSERVATIVE estimate for
   the target venue -- basis/wick structure on the thinner oracle-priced book appears to
   FAVOR stop-entry trend-following. If artifactual (bad backfill, sparse bars synthesized
   wide), every xyz number dies. This is TVB-6's first job.
2. **The regime layer is universal damage containment.** In every pairing across four
   samples, adding M/W/D stand_aside massively improved the result (-73.67 -> -17.23;
   -90.43 -> -36.71; -40.09 -> -12.61 prefix; -9.06 -> +39.86). Where there is edge it
   unlocks it; where there is none it caps the bleeding. This -- not return enhancement --
   is the correct one-line description of what the two-layer does.
3. **Regime speed is monotone-destructive.** No interior optimum appeared between M/W/D
   and D/12h/4h; every step faster was worse everywhere tested. (A regime SLOWER than
   M/W/D was not in the grid -- noted as a gap, not tuned in.)

### Caveats / standing questions

xyz data provenance unverified (surprise 1); slippage realism at size still unmodeled
(1 tick/fill baked in); short-leg MAE/solvency check still deferred -- NO deployability
language anywhere above; the W1 top cells (R1E1/ctrlA/R1E3 at +34-40% @0.0125) remain
single-instrument, single-regime results whose gross edge disappears in the Dec-Feb prefix
of the very same instrument. The system as characterized is a REGIME-LOCAL edge with a
universal containment layer, not an all-weather strategy.

## TVB-6 (2026-07-03): xyz backfill VERIFIED against Hyperliquid venue candles

Resolves TVB-5 surprise 1 (the open question gating every xyz number). Method: pull HL
candles for `xyz:MSTR` from the public info API (`candleSnapshot`), export the TV
`HIP3XYZ:MSTRUSDC.P` series via CDP (`scripts/tv_bars.mjs`, new), compare OHLCV
bar-by-bar on the timestamp intersection. Reproduce with
`uv run python analysis/verify_xyz_backfill.py` against the committed evidence
(`analysis/reference/tvb6_*.json`, 7 files). NOTE: the evidence is TIME-PERISHABLE --
HL serves only the most-recent ~5000 candles per interval (15m floor 2026-05-12, 1h
floor 2025-12-07 at pull time), so these raw pulls cannot be re-fetched later; the
committed JSONs are the reproducibility.

**API floor facts (pulled 2026-07-03 ~20:00Z):** HL 4h/1d are UNCAPPED and start
2025-12-02 -- the venue's actual listing date, which the TV backfill start matches
exactly. TV's first 60m bar (Dec 2 15:00Z) equals HL's first 4h candle (12:00Z bucket)
on all four fields AND volume (6365.513), i.e. first trades occurred 15:00-16:00Z and
TV is missing nothing at the start. All HL series are gap-free (placeholder candles on
zero-trade intervals); TV omits zero-trade bars instead (behavior difference, not data
loss).

**Comparison results (all five checks; per-field float-exact match rates):**

| check | window | overlap | all-4-exact | vol-match | max rel err |
|---|---|---|---|---|---|
| 15m native vs HL 15m | May12->Jul3 | 4,971 | 98.73% | 99.92% | 3.7e-03 |
| 60m native vs HL 1h | Dec7->Jul3 | 4,989 | 97.41% | 99.92% | 2.7e-02 |
| 1D native vs HL 1d | Dec2->Jul3 (full) | 214 | 85.05% (opens 100%, closes 99.5%) | 98.6% | 2.7e-02 |
| TV60m->4h vs HL 4h | Dec2->Dec7 hole | 30 | 96.67% | 100% | 4.0e-04 |
| TV15m->60m internal | Dec2->Jul3 (full) | 5,103 | 99.98% | 99.98% | 1.9e-04 (live bar) |

60m diff rates are the SAME in the Dec-Feb chop (97.47%) and the Feb-Jul trend (97.36%)
-- no regime-dependent data-quality issue.

**Residuals, fully characterized:** (a) 39/40 HL-only 15m bars are zero-trade
placeholders; exactly ONE traded bar is missing from TV (2026-06-28 16:00Z, 25 trades,
vol 323.3 -- reappears in the 60m volume diff to the decimal: a one-off TV ingestion
blip). (b) The non-exact bars are wick-level: TV's high/low is consistently slightly
MORE extreme than HL's candle (worst single case 2026-01-04: TV day-high 172.65 vs HL
167.95, 2.7%) -- direction-consistent with HL's snapshot scrubbing/rebuilding a few
extreme prints that TV's live ingest kept. (c) Last-bar diffs are live-bar snapshot
timing, not data. (d) Honest residual: the PRE-May-12 15m subdivision cannot be checked
natively (HL 15m cap); it is pinned by the internal 15m->60m aggregation being exact
against the HL-verified 60m series INCLUDING volume -- fabricating subdivisions that
aggregate float-exactly to venue OHLCV+volume is not a plausible failure mode.

**VERDICT: the TV xyz backfill is genuine Hyperliquid venue data.** The TVB-5 venue gap
(shared window ctrlB @0.0125: xyz +80.17% vs OKX -9.05%) is therefore REAL price-behavior
difference between the venues, not a data artifact -- OKX was the CONSERVATIVE proxy for
the target venue. Impact bound for the residuals: wick diffs touch ~1.3-2.6% of bars at
<0.5% magnitude (one 2.7% outlier); TV-more-extreme wicks marginally over-trigger stop
entries in both directions -- orders of magnitude too small to produce an 89pp gap.
Per the Codex TVB-5 wording rule this verdict is sample-scoped: verified for MSTRUSDC.P
over Dec-2->Jul-3; a new xyz instrument or a TV feed change re-opens the question (and
SP500USDC.P has no backfill to verify -- its history only accrues from 2026-07-03).

WHY the venues differ that much is a separate (mechanism) question -- NOT answered by
this verification; candidates: wick/basis structure on the thinner oracle-priced book
interacting with stop-entry fills, and venue-local liquidity events. Tooling: NEW
`scripts/tv_bars.mjs` (CDP main-series OHLCV export), NEW `analysis/verify_xyz_backfill.py`
(+4 tests; suite 13/13).

### Mechanism peek: the venue gap is a knife-edge integral, not different price structure

OKX (tvb4_bars_60m.json) vs xyz (tvb6_tv_xyzMSTR_60m.json) over the 3,074 shared 60m
bars (Feb 25 -> Jul 3): close-to-close return correlation **0.9923**; cumulative close
path **-18.00% vs -18.09%** (indistinguishable); basis band 0.985-1.007; bar structure
nearly identical (mean range 1.081% vs 1.062% -- xyz slightly TIGHTER; wick means within
1bp). Trigger-relevant divergence: ~4% of bars break the prior high on one venue only
(122 OKX-only vs 101 xyz-only of ~3,000).

The implication: the ctrlB shared-window gap (-9.05% vs +80.17%, 2,708-2,815 trades)
requires only ~**0.025% per trade** of edge difference ((1.8017/0.9095)^(1/2708)-1) --
about one round-trip commission -- and R1E1's gap (+39.88 vs +83.07 over ~920 trades)
is the same order (~0.03%/trade). Nothing exotic is needed: slightly tighter xyz ranges
(fewer whipsaw state-stop exits), ~200 divergent trigger events, and marginally
different fill prints sum to 2-3bp/trade and COMPOUND into a 90pp headline under
100%-equity sizing. READ IT THIS WAY: high-churn configs sit so close to zero per-trade
edge that venue microstructure decides their SIGN -- the +80% is not "the edge was
bigger than we thought," it is "B-class net results are venue-texture noise." The
structural readings (orderings, containment, regime-speed gradient) replicate across
venues; per-venue MAGNITUDES at the churn end do not generalize. Both venues do agree
R1E1 is solidly positive at real fee -- sign robust, magnitude not.

**DECIDED (with user, 2026-07-03): xyz MSTRUSDC.P is the PRIMARY backtest chart for
MSTR work.** Rationale: it is the target venue (dissolves the charter S7.3
venue-mismatch trap for MSTR) and its TV 15m history is DEEPER than the OKX proxy's
(Dec-2 vs Feb-25 floor). OKX:MSTRUSDT.P is retained as the standing cross-venue
sign-robustness check -- per the knife-edge finding, sign agreement across venues now
outranks any single venue's magnitude as the reported result. Follow-through: xyz-native
headline rows for the 60m cells the TVB-5 venue pass did not run (ctrlA, R1E3), with a
regression re-read of the committed WV cells first.

### xyz-native headline rows (primary-chart baseline table)

Re-stage regression first (fresh TV launch, study re-added as `SCn1V9`, id map verified
against Pine source -- unchanged): ctrlB @0.0125 net +7.94% / 4,308 closed vs TVB-5's
+7.98% / 4,306+1-open; R1E1 @0.0125 +59.96% / 1,302 vs +60.01% / 1,300+1-open. PF/DD/
Sharpe match to the reported precision on both -- tail drift only (~2h more data).
GREEN; the new `tv_dump.mjs` fail-loud assertions (Codex TVB-5 LOW 1: list length ==
closed+open, entry-time ordering; raw exit ts `xt` now preserved per row) passed on
every dump below.

Full backfill window (Dec 2 15:00Z -> Jul 3 20:00Z), HIP3XYZ:MSTRUSDC.P, all sanity
gates green (marginCalls 0, open <= 1, floor 19,779/5,104 bars verified before every
read):

| cell | chart | trades (L/S closed) | @0 | @0.0125 | PF / DD / Sharpe @0.0125 | dump |
|---|---|---|---|---|---|---|
| ctrlB | 15m | 4308 (2151/2157) | +216.85 (TVB-5) | **+7.94** | 1.014 / 58.9 / 0.14 | tvb6_WV_ctrlB_0125 |
| R1E1 | 15m | 1302 (669/633) | +121.46 (TVB-5) | **+59.96** | 1.239 / 23.9 / 0.44 | tvb6_WV_R1E1_0125 |
| ctrlA | 60m | 474 (241/233) | +65.62 | **+47.10** | 1.220 / 19.3 / 0.65 | tvb6_WV_ctrlA_* |
| R1E3 | 60m | 408 (206/202) | +61.92 | **+46.21** | 1.240 / 19.6 / 0.73 | tvb6_WV_R1E3_* |

Window slices (window_compound over the new dumps, closed trades entered in-window):

| cell, fee | shared Feb25-> (vs OKX W1) | prefix Dec2-Feb25 (kill-window) |
|---|---|---|
| ctrlA @0.0125 | **+44.06%** (OKX +38.45) | **+2.12%** (L -15.6 / S +20.9) |
| ctrlA @0 | +56.76% | +5.64% |
| R1E3 @0.0125 | **+39.75%** (OKX +33.80) | **+4.63%** (L -12.6 / S +19.8) |
| R1E3 @0 | +50.26% | +7.76% |

**Reads (flagged, not tuned on):**
1. Shared-window venue lift on the slow cells is MODEST and same-sign (ctrlA +44.1 vs
   +38.5; R1E3 +39.8 vs +33.8) -- ~0.01%/trade, the knife-edge story at low churn:
   venue texture matters less when you trade 300x instead of 2,800x.
2. **The Dec-Feb kill-regime is TURNOVER-DEPENDENT, not absolute.** The same window
   that takes ctrlB to -40.09% and R1E1 to -12.61% leaves ctrlA at +2.12% and R1E3 at
   +4.63% (positive GROSS and NET). The chop kills the churn cells; the slow 60m cells
   tread water through it -- with shorts carrying the prefix (+20% short vs -15% long
   on ctrlA). Refines TVB-5 SP6: "kill-regime" = where per-trade edge dips slightly
   negative; only high-turnover configs compound that into disaster.
3. R1E1 (+59.96) tops both 60m cells on the full xyz window at real fee -- but its
   kill-window loss (-12.61) vs R1E3's gain (+4.63) is the risk-shape difference the
   headline number hides. Same S8/containment caveats as TVB-5; no deployability
   language.

### Short-leg MAE / 1x-cash solvency check (Codex TVB-3 finding 2 -- CLEARED)

Question: TV simulates with margin 0/0 (no margin calls -- the TVB-3 deadlock fix), so
it rides any adverse excursion; would the short leg have LIQUIDATED on the real venue
at 1x cash? Model: HL isolated margin, xyz:MSTR maxLev 10 -> maintenance 5%; a short at
leverage L liquidates at adverse move (1+L)/(L*1.05)-1: **+90.5% at 1x**, +42.9% at 2x,
+27.0% at 3x, +14.3% at 5x. A 1x long cannot liquidate. Method: per-trade MAE vs ENTRY
price off bar extremes over [et, xt] (verified venue bars; entry-bar extreme may
precede the intrabar entry -- measured MAE can only OVERSTATE). NEW
`analysis/trade_mae.py` (+4 tests; suite 17/17); dumps re-captured with
entry/exit price + TV per-trade drawdown/run-up fields (`ep/xp/ddp/rnp`; tv_dump
TVB-6 format). Cross-check vs TV's own ddp: median |diff| 0.05-0.08pp.

| config | shorts | median MAE | p99 | worst | 1x/2x/3x/5x breaches | max survivable short lev |
|---|---|---|---|---|---|---|
| ctrlB | 2157 | 0.28% | 2.45% | **8.11%** | 0 / 0 / 0 / 0 | 7.40x |
| R1E1 | 633 | 0.31% | 2.77% | 3.82% | 0 / 0 / 0 / 0 | 11.09x |
| ctrlA | 233 | 0.58% | 4.49% | 8.00% | 0 / 0 / 0 / 0 | 7.46x |
| R1E3 | 202 | 0.60% | 4.49% | 8.00% | 0 / 0 / 0 / 0 | 7.46x |

(Long worst MAE 3.7-5.4% across configs -- context only; 1x longs are unliquidatable.)

**Read: at 1x cash the short leg is solvent by an order of magnitude throughout the
sample -- TV's margin-0/0 simulation is a FAIR model of a 1x cash deployment for this
strategy class (no margin call would ever have fired).** The state-stop exits fast
enough that excursions stay single-digit. Honest bounds: worst OBSERVED MAE is not
worst POSSIBLE (MSTR-class earnings gaps can exceed 8% overnight; the +90.5% 1x
cushion is what makes the claim robust, not the 8.11% sample max); leverage above ~3x
starts leaning on the sample; perp FUNDING cost/credit on held positions is NOT
modeled (belongs to the slippage/cost-realism item, still open). This closes the
solvency precondition; deployability language remains gated on slippage realism at
size. All backtest %s in this document are 1x (100%-of-equity notional, no leverage).

Leverage-clearance corollary (isolated margin): the backtest describes reality only
while the liquidation threshold clears every intra-trade MAE. Sample clearance:
~7.4x short / ~9.8x long (worst observed MAE 8.11% / 5.43%). ABOVE clearance,
liquidation acts as an intrabar hard stop the (close-based, state-stop) backtest
never modeled -- the measured strategy no longer exists at that leverage; e.g. at a
venue-max 20x (mm 2.5%, liq ~ +/-2.5%) the p99 MAE band (2.4-4.5%) implies routine
noise knockouts. Below clearance, per-position isolated leverage with a small posted
margin is strictly risk-REDUCING vs 1x-all-in cross for the same notional (caps the
catastrophe/gap loss at the posted margin) -- leverage is the OUTPUT of
exposure-vs-margin choices, not a return dial. Sizing proper (vol-target /
loss-limit / multi-instrument) remains future work at the scanner-integration stage.

### Slippage sensitivity band + tick-size asymmetry (venue-gap decomposition REVISED)

**Tick-size discovery (verified via CDP symbolInfo): xyz MSTRUSDC.P mintick = 0.001;
OKX MSTRUSDT.P mintick = 0.01.** The standing "slippage = 1 tick/fill" convention
therefore charged OKX ~10x more modeled slippage per fill than xyz in every TVB-5
venue comparison. The venue gap was partly a MODELING ARTIFACT, not venue reality.

Band design (declared before running, with predictions SB1-SB4): slippage {1, 10, 25,
50} ticks at commission 0.0125, all four xyz-native configs, full Dec2->Jul3 window.
At ~$130 avg price: ~0.08 / 0.8 / 1.9 / 3.8 bp per fill; the 10-tick point equals
OKX's 1-tick model in absolute $/fill ($0.01) -- the venue-model equalizer. Dumps:
`tvb6_WV_{cfg}_0125_s{10|25|50}.json`.

| config (trades) | s1 | s10 | s25 | s50 |
|---|---|---|---|---|
| ctrlB (4308) | +7.94 | **-37.56** | -74.92 | -94.52 |
| R1E1 (1302) | +59.96 | +34.76 | **+1.29** | -37.07 |
| ctrlA (474) | +47.10 | +38.22 | +24.60 | **+4.79** |
| R1E3 (408) | +46.21 | +38.58 | +26.73 | **+9.19** |

Scorecard: SB1 CONFIRMED (ctrlB deeply negative by 10t). SB2 REFUTED on magnitude --
R1E1 at 25t is ~breakeven (+1.29), not comfortably positive; 100%-equity compounding
amplifies the linear per-trade cost (~59pp lost, vs ~39pp from the naive per-trade
estimate). SB3 CONFIRMED (both 60m cells positive at 50t, thin). R1E3 >= ctrlA at
every elevated slippage -- fewer trades AND higher PF headroom.

**Venue-gap decomposition (SB4 CONFIRMED ~exactly):** shared-window Feb25->,
equal-$-slippage comparison: R1E1 xyz@s10 +61.78% vs OKX@s1 +39.88% (raw xyz@s1 was
+83.07) -- equalization closes ~49% of the gap; ctrlB xyz@s10 +25.77% vs OKX -9.05%
(raw +80.17) -- closes ~61%. REVISED one-line: the TVB-5 venue gap was roughly HALF
tick-size modeling artifact, HALF real venue texture; the remaining texture gap still
sign-flips the churn config (knife-edge conclusion unchanged and reinforced -- the
modeled-cost term alone, at $0.01/fill, moves ctrlB by 90pp).

Which ABSOLUTE slippage is realistic per venue remains OPEN (needs live xyz book
sampling at ~90-contract size; also perp funding). Until then the convention for
xyz runs: report s1 alongside s10 (s10 = "OKX-equivalent-$" pessimistic floor for
book-crossing cost); never quote an xyz churn-config number at s1 alone.

## TVB-6: re-entry governor (charter S8) -- design + PRE-REGISTRATION (locked before any governed run)

**DESIGNED WITH USER (2026-07-03; two explicit decisions + one amendment):** the
governor is a zero-parameter LEVEL RATCHET. After a LOSING exit (net of fees; scratch
counts as losing), same-direction entries re-arm only at a trigger STRICTLY beyond the
failed trade's trigger (long: higher; short: lower). RESET: a winning same-direction
exit OR any completed opposite-direction trade -- the amendment (user-approved) that
prevents the foreseeable deadlock where a stop-out near the December high (~181) would
have blocked longs for the entire sample (price never re-exceeded 181; April topped
~172). The ratcheted level is the TRIGGER, not the fill price, so slippage settings do
not change governor semantics. Mechanism targeted: within an aligned flicker episode
(up -> grey -> up), the breakout trigger FALLS with each bar, so the control re-buys
successively lower highs at full round-trip cost; no opposite trade can complete
inside such an episode, so the ratchet holds exactly there and releases on genuine
structure flips. Skill reconciliation: strat-methodology's only re-entry canon (X-1-3
Rev Strat same-bar reversal) is pattern-world machinery outside this charter's scope;
the governor is a pre-entry condition and entry timing stays instant-on-break.

Implementation: `pine/baseline_continuity.pine` gov_mode input (off | ratchet),
DEFAULT off (= regression anchor). Deployed at pineVersion 19.0; id map: gov_mode =
in_25; strategy properties shift +1 (commission in_33, slippage in_34, margins
in_35/36, magnifier in_42). REGRESSION: governor-off reproduces the pre-governor
ctrlB @0.0125 run BYTE-IDENTICALLY (all 4,308 committed closed trades prefix-match
exactly; trade 4,309 is the previously-open trade closing in the live tail).
Operational: TV 2026-07 renders a fiber-less DECOY `.monaco-editor.pine-editor-monaco`
node that broke the MCP's first-match Monaco finder; fixed in jackson
(`src/core/pine.js`, multi-candidate walk) -- MCP restart picks it up next session;
this session deployed via a direct-CDP bridge script.

**Pre-registered predictions (before any governed run):**
- G1: trade count falls in every governed cell; relative cut largest ctrlB > R1E1 > R1E3.
- G2: @0.0125 s1 net improves for ctrlB (material) and R1E1 (modest).
- G3: the improvement GROWS at s10 (the governor is a turnover lever; cost-sensitive
  marginal trades are what it deletes).
- G4: zero-fee GROSS slightly DECREASES (honest cost -- the blocked re-entry stream is
  ~zero-to-slightly-positive gross, by the TVB-4/5 suppressed-stream precedent).
- G5: window split -- the Dec-Feb kill-window improves most; the Feb-Jul trend window
  is ~flat (pullback-then-higher-high clears the ratchet in trends).
- G6: R1E3 (low churn) barely moves (<5pp either way) -- the governor should be nearly
  inert where turnover is already low.

Run set (all @ xyz full window, governed = gov_mode ratchet): ctrlB+gov {s1@0.0125,
s10@0.0125, s1@0}; R1E1+gov {s1@0.0125, s10@0.0125, s1@0}; R1E3+gov {s1@0.0125}.
Dumps: `tvb6_WV_{cfg}gov_{fee}[_s10].json`. Keep-rule (charter S5): the governor is
kept only if it beats the continuity-only baseline at real cost assumptions.
