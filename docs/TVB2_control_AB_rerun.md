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
With fees ~10x cheaper, the next unmodeled cost dominates -- and it is **slippage**, which we deferred:
- The user fills **market/taker on both legs**, so every entry and exit gaps (user confirmed
  ~symmetric in ticks). **B = 2,301 market round-trips = 2,301x slippage; A = 261 (~9x less).**
- At ~$130-540 price, a few ticks/fill is ~0.01-0.05%/leg -- i.e. **slippage is now the SAME order as
  the fee that previously killed B.** B at +5..+25% on ZERO slippage is precisely where realistic
  slippage decides the sign. **The churn concern is NOT exonerated by cheap fees** -- its slippage
  component remains, and still favors A (low turnover) over B.
- Intrabar fill fidelity / bar-magnifier still unverified -- matters most when per-trade edge is thin (B).

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
  optimistic. Status of the bar-magnifier setting for these runs is unconfirmed.
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
- **Confirm the fee sweep by ACTUAL re-run** (set `in_23` to 0.0086% and 0.0864% for A and B) -- the
  intermediate-rate verdicts above are the geometric model, not fresh backtests.
- **Build the limit-entry (maker) variant** and run at 0.0086% (Pine change = STOP-and-ASK). Model
  says A -> +42%, B -> +25%; this is the real test of whether the edge survives execution.
- **Verify the cash-dex taker rate** directly (only maker fills observed so far).
- **Slippage (out of fee scope, deferred):** market-order exits gap ~symmetrically in ticks; the
  commission-only verdicts are optimistic on fills. Model later as asymmetric tick offsets.
- Add a **second regime window** (current window is a single ~4-month downtrend).

## Chart left in state

Strategy `35dVw8` restored to its as-found config: TFs **M/W/D/60**, fee **0.1%**, chart **15m**
(the non-canonical hybrid). Set Control B = enable 60/30/15 + disable M/W/D, chart 15m;
Control A = enable M/W/D/60 + disable 30/15, chart 60m. Input ids: in_2=M, in_4=W, in_6=D, in_8=60,
in_10=30, in_12=15 (bool enables); in_23 = commission percent.
