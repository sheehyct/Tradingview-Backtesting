# Strategy Implementation Assessment

Date: 2026-08-14

Status: Independent architecture and implementation assessment. Research only.

Scope: The three indicator families, their Pine strategy ports, the Python
replay engines, the experiment record through TVB-23, and the architecture
required for a possible far-future live implementation. This assessment does
not promote an arm, choose a "best" parameter set, modify strategy logic, or
authorize deployment.

## Executive assessment

The project deserves to continue, but it is not yet one implementable live
strategy.

It is currently an unusually well-instrumented research program containing
several related strategy contracts:

- the original continuity baseline and its manual companion;
- the TFC plus BF live watch state machine and historical control port;
- the Magnitude plus Targets detector, ladder, signal-memory, chop, and
  position-health state machine;
- a package strategy that ports only selected M+T sections into the TFC-BF
  machinery; and
- Python twins that reproduce historical decision events under declared
  bar-close conventions.

Those objects share ideas, but they do not yet share one authoritative clock,
signal identity, fill model, risk model, or position lifecycle. The important
conceptual correction is therefore:

> These are not three Boolean indicators waiting to be joined. They are three
> interacting temporal state machines, each with its own clock, memory,
> invalidation rules, and historical-versus-realtime behavior.

The implementation demonstrates strong local understanding of each pinned
experiment. The pre-registrations, correction history, parity gates, and
explicit limitations are materially better than a typical strategy research
repository. What is still missing is global understanding made executable as
one canonical semantic contract. Copying more Pine sections into the package
will not create that contract by itself.

My recommended direction is:

1. Close the existing TVB-24 Pine mirror and parity work without changing its
   contract.
2. Freeze the current scripts as historical research oracles.
3. Define a canonical event-time strategy specification and an explicit
   signal lifecycle.
4. Implement that specification once as a pure, deterministic Python kernel.
5. Treat Pine as an independent visualization and conformance oracle, not as
   the sole future execution brain.
6. Replace OHLC-implied fills with causal order-event simulation before
   interpreting another P&L improvement.
7. Add portfolio, cost, margin, and catastrophic-risk layers before any live
   shadow test.
8. Progress through shadow, testnet/paper, and tiny isolated-capital gates;
   never jump from TradingView parity to broker automation.

### Bottom-line decision table

| Question | Assessment |
|---|---|
| Is the research record credible? | Yes, within its declared one-window, gross, historical-event scope. |
| Is Pine-to-Python historical decision parity credible? | Yes for the specifically gated cells; it is not fill/P&L or realtime parity. |
| Did the package establish edge over its matched control? | No. D1 improved the package and risk shape, but still trailed A0b in the only tested window. |
| Are the three indicators fully represented in the package? | No. M+T remember, reversal-chop, and health/status semantics are intentionally omitted. |
| Is C1 proven to add value over the original C0? | No. The named C1 is useful operationally, but the original C0-to-C1 increment has not been isolated. |
| Can current backtest fills support live expectancy claims? | No. Entry causality and same-bar exit ordering remain unresolved. |
| Is the roster rollup a portfolio backtest? | No. It is an additive per-position percentage-point research summary. |
| Is the system ready for live trading? | No, and the repository correctly makes no such claim. |
| Is a future live implementation feasible? | Yes, after the semantic, causal, portfolio, and operational gates in this document. |

## What I reviewed and verified

The assessment was based on the current repository state, including:

- the governing charter and its named C0/C1/C2 amendments
  (docs/ATLAS_Timeframe_Continuity_Charter.md:7-23,
  docs/ATLAS_Timeframe_Continuity_Charter.md:52-88);
- the original baseline and manual companion
  (pine/baseline_continuity.pine:3-53,
  pine/tfc_companion.pine:6-110);
- the TFC-BF watch and historical control
  (pine/tfc_bf_watch.pine:3-100,
  pine/tfc_bf_control_strategy.pine:3-33);
- the full M+T indicator and the package subset
  (pine/strat_magnitude_targets_plus.pine:4-25,
  pine/tfc_mt_package_strategy.pine:3-24);
- the Python twin, pattern detector, Tier B runner, and generated experiment
  reports (analysis/paper/engine.py:1-49,
  analysis/paper/patterns.py:1-27,
  analysis/paper/tier_b.py:142-180,
  analysis/paper/tier_b.py:289-350);
- the historical handoffs, pre-registrations, parity reports, external-review
  record, and current TVB-24 startup work order.

Read-only local verification:

- 181 tests passed and 2 skipped.
- Ruff reported no findings.
- No strategy, engine, test, configuration, artifact, git branch, commit, or
  deployment was changed.
- Independent replay diagnostics were run in memory against the committed
  bars and current engine; they wrote no artifacts.

Validation limits:

- I did not modify or compile Pine in TradingView.
- I did not rerun a new performance experiment or select parameters.
- I did not connect to a wallet, exchange account, webhook, or broker.
- I did not independently certify the economic quality of the underlying
  market data.
- A passing unit suite does not resolve tick ordering, true order
  marketability, partial fills, or cold-start operational readiness.

## 1. What the system actually contains

### 1.1 The original continuity family

The baseline is a full strategy, not merely a filter. Its default Control B
uses a 60/30/15 execution gate, raw prior-bar breakout stop orders, a
close-based state stop, 100 percent equity sizing, 0.1 percent commission per
fill, and one tick of slippage
(pine/baseline_continuity.pine:3-39,
pine/baseline_continuity.pine:42-53,
pine/baseline_continuity.pine:250-273).

The companion is another state machine that exposes:

- state versus full-flip exits;
- close-only versus live revocable intrabar entry arming;
- execution and regime gates;
- a re-entry governor;
- pending entry stops, simulated fills, and alerts.

Its own header correctly says historical intrabar timing is only as precise as
the chart timeframe, while realtime execution observes updates inside the bar
(pine/tfc_companion.pine:33-53,
pine/tfc_companion.pine:389-443).

This family is the closest expression of the charter's original
continuity-first thesis. It is not the state machine currently called the
package control.

### 1.2 The TFC-BF family

The watch indicator changed the strategy materially:

- the entry gate is D/W/M period-open alignment;
- the trigger is the prior completed arm-timeframe extreme;
- four independent BF pools run on 12h, D, W, and M candles;
- each pool detects the smallest qualifying rolling compound-3;
- line sides move through alive, consumed, crossed, superseded, or ghost
  states;
- harvest touches, adverse-line breaks, and full gate flips race as exits.

The relevant contract is documented directly in
pine/tfc_bf_watch.pine:56-99, while the pool state and eviction machinery
lives at pine/tfc_bf_watch.pine:181-392.

This is sophisticated stateful market structure. Its output depends on far
more than the current bar:

- which base candles were loaded;
- which formations were born;
- which sides were superseded or ghosted;
- which lines were touched while flat;
- which formations were evicted; and
- the line value at the current event time.

The historical strategy port deliberately preserves this machine, but changes
the Pine execution surface to bar-close market orders. Its parity claim is
decision-event parity on historical bars, not realtime cadence or price
parity (pine/tfc_bf_control_strategy.pine:10-29,
docs/experiments/tvb20_control_port_parity.md:42-61).

### 1.3 The Magnitude plus Targets family

The full indicator is not merely a pattern detector. It contains at least five
separable mechanisms:

1. local higher-timeframe bar aggregation and STRAT classification;
2. a precedence-ordered setup dictionary;
3. a nearest-first, strictly monotone target ladder;
4. persistent "most recent signal" adoption, morph, and invalidation rules;
5. reversal-since-T1 chop state and live position-health labels.

The ladder is built at pine/strat_magnitude_targets_plus.pine:553-587.
Persistent signal adoption and invalidation are at
pine/strat_magnitude_targets_plus.pine:589-662. The actual reversal counter is
at pine/strat_magnitude_targets_plus.pine:672-692, and health/status is at
pine/strat_magnitude_targets_plus.pine:694-717.

The package and Python detector intentionally port only aggregation,
classification, PMG, detection, and ladder construction. They do not port the
remember, reversal-chop, or position-health state
(pine/tfc_mt_package_strategy.pine:9-19,
analysis/paper/patterns.py:1-9).

That is a legitimate experimental choice, but it means "the M+T indicator" and
"the M+T package layer" are not interchangeable names.

### 1.4 The current package

The TVB-22 package combines:

- D/W/M gate state;
- M+T developing 1h pattern detection;
- entry-snapshot target ladders;
- BF line state used for exit or proximity veto;
- a gate-open proximity veto currently named chop;
- BF, target, adverse-break, and full-flip exit variants.

It supports the TVB-22 A1/A2/A3 arms and has a declared 9-cell historical
parity result (pine/tfc_mt_package_strategy.pine:59-65,
pine/tfc_mt_package_strategy.pine:100-113).

It does not yet mirror the TVB-23 floor and ATR arms. The current work order
correctly restricts the mounted package strategy to TVB-22 arms until the new
GOOGL/TSLA/DRAM by D1/DINF/D1ATR gate passes
(.session_startup_prompt.md:14-35).

### 1.5 The Python implementation

The repository documentation still calls Python "post-hoc" and says there is
no Python engine (README.md:21-27, CLAUDE.md:3-6). That is no longer true.

analysis/paper/engine.py is an executable historical replay twin. It owns:

- BF formation state;
- D/W/M gates;
- arm and pattern entries;
- pattern, floor, BF proximity, and gate-open proximity vetoes;
- frozen targets;
- exit sequencing;
- event and P&L generation.

The Tier B runner then constructs a mark-to-market percentage curve for each
symbol and sums those curves for the roster
(analysis/paper/tier_b.py:162-180,
analysis/paper/tier_b.py:289-305).

This Python engine is already the natural seed for a canonical implementation,
but it is currently optimized for reproducing experiment contracts, not for
being a broker-grade strategy core.

## 2. What the evidence establishes

### 2.1 Strong evidence already present

The project has several genuinely strong practices:

- The charter says to kill the strategy, treat extreme metrics as questions,
  and distinguish data generation from selection
  (docs/ATLAS_Timeframe_Continuity_Charter.md:7-23).
- Experimental arms and contrasts are named before code.
- The project preserves invalidated reports and explains why they were
  superseded instead of rewriting history.
- Pine/Python parity claims are qualified by symbol, cell, clock, event keys,
  and known price residuals.
- Cold-start behavior, history dependence, venue mismatch, clock disagreement,
  and selection-lookahead failures have been surfaced instead of buried.
- The TVB-22 containment correction converted impossible target fills into a
  reproducible contract and retained the negative package verdict
  (docs/experiments/tvb22_tier_b_rerun_report.md:23-34).
- The TVB-23 report explicitly labels its 98-99 percent win rate as an exit
  construction artifact, not proof of edge
  (docs/experiments/tvb23_t1floor_report.md:66-71).

These are signs of real implementation understanding. The repository is not
casually overclaiming its current results.

### 2.2 Current performance evidence

The corrected TVB-22 one-window roster result was:

| Arm | Combined gross pp | Roster maxDD pp | Interpretation |
|---|---:|---:|---|
| A0a, 15m control cadence | +47.4 | 131.5 | Operational comparison, cadence differs from pattern arms |
| A0b, matched 1h control | +104.8 | 122.2 | Primary matched control |
| A1, pattern entries plus control exits | -7.7 | 116.3 | Pattern block did not beat matched continuity entry |
| A2, package with T1 exit | +24.6 | 67.8 | Tail improved, expectancy still below control |
| A3, package with T2/fallback | +31.0 | 73.3 | Same broad conclusion |

Source: docs/experiments/tvb22_tier_b_rerun_report.md:36-63.

TVB-23 then added a T1 distance floor. D1 improved A2 from +24.6 to +83.8
gross pp and reduced roster maxDD from 67.8 to 22.1 pp, but remained below
A0b's +104.8 pp. The report also found the depth curve non-monotone and ATR
scaling materially reduced the fixed-percent veto's accidental symbol filter
(docs/experiments/tvb23_t1floor_report.md:17-54).

The right conclusion is narrow:

- the floor removed a real self-inflicted class of entries;
- the package's risk geometry changed materially;
- the package still did not earn its place over C1 in that window;
- no edge, target depth, pattern, or veto parameter has been validated out of
  sample.

### 2.3 Evidence that remains absent

The current record does not establish:

- a clean C0 versus C0-plus-BF incremental result;
- causal entry prices after every predicate becomes observable;
- same-bar target-versus-stop event ordering;
- fee, funding, spread, depth, latency, or partial-fill-adjusted expectancy;
- an investable portfolio equity curve;
- an as-of universe across multiple chronological windows;
- venue-local transfer from proxy data to execution data;
- realtime Pine-to-kernel state parity;
- restart/reconnect recovery from durable state;
- broker reconciliation or risk-limit behavior.

This is not criticism of the reports, which usually state these limits. It is
the boundary between a sound research harness and an implementable trading
system.

## 3. Findings and recommendations

### P0-1: There is no single canonical strategy contract

The charter defines:

- C0 = trigger + TFO gate + state stop;
- C1 = C0 + BF exits;
- C2 = C1 + the full M+T package.

See docs/ATLAS_Timeframe_Continuity_Charter.md:75-88.

However, the original baseline C0 family uses configurable execution FTFC
sets, raw prior-chart-bar breakout stop orders, and a state stop
(pine/baseline_continuity.pine:60-72,
pine/baseline_continuity.pine:197-204,
pine/baseline_continuity.pine:250-273).

The mounted C1 uses a D/W/M gate, prior completed arm-timeframe extremes,
BF/brk/flip exits, zero-cost reporting, and close-market strategy orders
(pine/tfc_bf_watch.pine:103-121,
pine/tfc_bf_control_strategy.pine:19-29,
pine/tfc_bf_control_strategy.pine:512-574).

Therefore the historical move from the original C0 to the named C1 changes
more than one layer:

- gate set and role;
- trigger clock;
- entry timing;
- exit family;
- fee/slippage convention;
- Pine order type.

The TVB-21 pre-registration itself records that C0 was not run
(docs/experiments/tvb21_tier_b_prereg.md:26-31).

Impact:

- C1 remains a valid operational control for A0b/A1/A2/A3 because those
  contrasts are internally defined.
- It is not evidence that BF exits add value over the original minimal
  continuity strategy.
- The C0 -> C1 -> C2 naming currently implies more experimental isolation than
  the full history provides.

Recommendation:

Build a true current-kernel C0 and C1 pair with identical:

- symbol data and warm state;
- D/W/M or other pre-registered gate;
- arm timeframe and trigger;
- entry order/fill convention;
- cost and sizing model;
- position occupancy rule.

Only the exit policy should change:

- C0-current: a specified state-stop;
- C1-current: the same entry stream with BF harvest/adverse-break/flip policy.

Retain the existing C1 name for historical compatibility, but distinguish
"historical C1 control" from "isolated C0/C1 experiment" in future reports.

### P0-2: Pattern entry fills are not causally identified

The developing 1h pattern detector consumes one completed 5m OHLC bar at a
time. It updates the developing 1h high, low, and current close, then detects a
signal whose color can flicker until the 1h bar closes
(analysis/paper/patterns.py:14-26,
analysis/paper/patterns.py:135-155).

The engine subsequently books a long entry at
max(trigger + tick, 5m bar open), with the mirrored short rule
(analysis/paper/engine.py:632-645). In other words, the engine can use the
completed 5m close to establish the color predicate but assign a price from
earlier in that same 5m bar.

That price may be causal on some bars, but 5m OHLC cannot prove it. The unknown
sequence is:

1. Did the trigger trade first?
2. Was the developing 1h bar already the required color then?
3. Did the D/W/M gate agree then?
4. Was the veto state the same then?
5. What executable quote existed after the final predicate became true?

The package Pine does not hide the mismatch. It reports market fills at the
5m close and claims event parity only
(pine/tfc_mt_package_strategy.pine:67-73,
pine/tfc_mt_package_strategy.pine:1133-1148).

Independent read-only D1 diagnostic, roster scope excluding DRAM:

- 102 entries were compared with the same 5m bar's close.
- The engine's internal price was favorable relative to that close on 61
  entries and adverse on 41.
- Mean signed advantage was +0.0809 percentage points; median +0.0375 pp.
- The 90th percentile absolute difference was 0.7271 pp.
- The maximum absolute difference was 2.0426 pp.

"Signed advantage" means long close minus internal entry, or internal entry
minus short close, divided by internal entry. This is not proof that the close
is the right fill. It disproves the blanket description of the internal price
as conservatively biased and quantifies the unresolved within-bar interval.

Recommendation:

Introduce a causal event replay before further P&L interpretation:

- Prefer exchange trades or at least 1m bars beneath the 5m decision clock.
- Track the exact first timestamp at which all predicates are simultaneously
  true.
- If the strategy uses a resting stop, create/cancel that order when the gate
  opens/closes and fill it only on later executable events.
- If the strategy uses market-on-signal, fill from the first quote/trade after
  decision time, including spread, impact, and latency.
- Where historical sequencing is unavailable, compute optimistic and
  pessimistic bounds and mark the trade unresolved; do not choose one silent
  precedence rule.

This is the highest-value next engine improvement.

### P0-3: The research rollup is not a capital portfolio

Each symbol replay starts from zero percentage points, marks one 1x
per-position-notional position, and records percent P&L
(analysis/paper/tier_b.py:142-180). The roster rollup forward-fills every
symbol curve and sums the values
(analysis/paper/tier_b.py:289-305). It then sums realized and open percentage
points (analysis/paper/tier_b.py:341-350).

That is useful for equal-weight mechanism comparison. It is not a portfolio
simulation because it does not model:

- one shared cash balance;
- simultaneous gross and net exposure;
- position sizing from risk;
- margin reserved across symbols and DEXs;
- correlated equity-perp exposure;
- order-book capacity;
- funding;
- portfolio liquidation;
- cross versus isolated margin;
- capital contention when signals overlap.

The pre-registration correctly labels the units as 1x gross percentage points
of per-position notional and no fees/funding/slippage
(docs/experiments/tvb21_tier_b_prereg.md:144-151). The danger is only that
terms such as combined and roster maxDD can later be mistaken for investable
account returns.

Recommendation:

Keep the existing additive rollup for research and rename it explicitly
"sum of symbol strategy pp." Add a separate portfolio simulator with:

- timestamped desired positions;
- shared equity and free collateral;
- risk-based order sizing;
- per-symbol, per-sector, per-DEX, gross, and net caps;
- funding and fees as cash ledger entries;
- fill-level positions and weighted average prices;
- cross/isolated margin and liquidation monitoring;
- rejected/deferred signals when capital is unavailable.

Do not retrofit capital semantics into historical result files. Create a new
versioned portfolio result schema.

### P0-4: BF state readiness is operationally load-bearing

The BF machine consumes and retires levels even while flat. It also has
bounded pool history and can evict an alive formation if no fully retired
formation is available
(pine/tfc_bf_watch.pine:296-306). The watch itself states that pool history is
limited to loaded chart history (pine/tfc_bf_watch.pine:90-99).

The project has already reproduced the consequence: a fresh chart mount can
have a materially different nearest exit line, and the monthly gate cannot
become ready until a month boundary appears inside loaded history
(docs/HANDOFF.md:1027-1030,
docs/experiments/tvb20_control_port_parity.md:94-116).

Impact:

- identical current price and recent bars do not imply identical strategy
  state;
- a restart can silently change exits and vetoes;
- display caps are currently also semantic caps;
- a "healthy" process can still be unready to trade.

Recommendation:

Make BF state durable and auditable:

- assign stable formation_id and side_id values from timeframe, N, anchors,
  and semantic version;
- record born, superseded, consumed, crossed, and evicted events;
- separate display retention from semantic retention;
- never silently evict an alive risk-relevant line;
- checkpoint state with the last processed exchange sequence/timestamp;
- on restart, load a checkpoint and replay all events after it;
- expose readiness per symbol and per component;
- fail closed on gaps, invalid timestamps, insufficient warm history, or
  unresolved checkpoint lineage.

Pine can continue reconstructing from chart history for visualization. A live
engine should not depend on chart scroll depth.

### P1-1: Candidate counts currently count evaluations, not opportunities

The pattern entry function increments candidates every time a qualifying
signal is evaluated while flat
(analysis/paper/engine.py:641-644). The detector can return the same developing
1h signal on multiple 5m closes. After an exit, that same signal can become an
entry again because no persistent signal identity has been consumed.

Independent read-only D1 diagnostic, roster scope excluding DRAM:

- 4,111 candidate evaluations;
- 682 distinct identities using
  (symbol, 1h signal-bar open, direction, pattern, trigger);
- 6.03 evaluations per distinct identity;
- 569 identities evaluated more than once;
- maximum 12 evaluations for one identity;
- 102 entries but only 86 distinct entry identities;
- 16 identities entered twice.

This does not mean the current counters are arithmetically wrong. It means the
reported veto rates answer "what fraction of flat 5m evaluations were
vetoed?" rather than "what fraction of trading opportunities were vetoed?"
Position occupancy also changes how often an arm gets evaluated, as the
TVB-23 report correctly notes
(docs/experiments/tvb23_t1floor_report.md:99-109).

Recommendation:

Create an explicit signal identity and lifecycle:

    signal_id = hash(
        contract_version,
        venue,
        symbol,
        signal_tf,
        signal_bar_open,
        direction,
        setup_id,
        trigger_version
    )

Suggested states:

    detected -> eligible -> order_pending -> entered
             -> vetoed(reason)
             -> expired
             -> invalidated
             -> consumed

Store evaluation events separately from opportunity events. Report both:

- candidate_evaluations and veto_evaluation_rate;
- unique_signals and unique_signal_veto_rate;
- order attempts, fills, cancels, rejections, and explicit retries.

Default to one entry attempt per signal_id. If same-signal re-entry is desired,
make retry eligibility an explicit pre-registered policy, not an accidental
consequence of returning to flat.

### P1-2: Exit ordering is deterministic but not market-causal

The current replay evaluates:

1. BF harvest or frozen target;
2. adverse-line break;
3. full gate flip.

See analysis/paper/engine.py:564-588 and
pine/tfc_mt_package_strategy.pine:1051-1088.

For a long, one 5m range can contain both an upper target and an adverse lower
event. OHLC does not reveal which happened first. Target-first precedence is
optimistic in that collision. The reverse precedence would be pessimistic,
but neither is established without lower-timeframe data.

There is also an order-type assumption. Filling exactly at a target is
reasonable only if a reduce-only limit was actually resting before the touch.
It is not equivalent to detecting the touch at bar close and then sending a
market order.

Recommendation:

- Define each exit as an actual order lifecycle.
- Place the frozen target only after the entry fill is confirmed.
- Use reduce-only semantics and actual remaining filled size.
- Model partial target fills and cancel/replace behavior.
- Treat thesis exits and catastrophic risk exits as separate priorities.
- Resolve same-bar collisions from lower-timeframe events or report bounded
  outcomes.
- Store why the order existed before the price touched it.

### P1-3: "Chop" names two unrelated mechanisms

The full M+T indicator's chop state counts confirmed direction reversals since
T1 was last hit (pine/strat_magnitude_targets_plus.pine:672-692).

The package's chop veto checks whether the prospective fill is within a fixed
percent or ATR multiple of any D/W/M period open
(analysis/paper/engine.py:672-684).

These are not alternative implementations of one formula. One is a
post-signal reversal state; the other is pre-entry gate-level proximity.

Recommendation:

Rename them in the canonical contract:

- reversal_streak_since_t1;
- gate_open_proximity_veto.

Then decide independently whether each belongs in the trading policy. Do not
say that "M+T chop" has been tested when only gate-open proximity was tested.

### P1-4: The full M+T signal lifecycle has not been adjudicated

The display indicator can:

- keep an earlier strong signal when a weak opposite signal appears;
- relabel a same-bar morph;
- clear an outside-bar morph with no remaining match;
- invalidate weak/fragile signals;
- update live position-health labels.

See pine/strat_magnitude_targets_plus.pine:606-662.

The package instead treats the detector's current return as the candidate,
then freezes a target only after entry. This can be the correct strategy
contract, but it is not simply "the display indicator, now backtested."

Recommendation:

Split the M+T design into named pure policies:

- SetupDetector: current-bar shape and trigger.
- SignalMemoryPolicy: adoption, morph, supersede, and invalidation.
- LadderBuilder: structural target levels.
- EntryEligibilityPolicy: gate, floor, BF proximity, and gate-open proximity.
- PositionHealthObserver: retracement, potential-3, and reversal streak.
- ExitPolicy: whether any observer becomes an order.

Default the display-only memory and health observers to non-trading until a
pre-registration explicitly promotes them. This preserves the current
research record while making future choices testable.

### P1-5: The strategy lacks a config-invariant catastrophic risk boundary

The historical paper record found three adverse runners at roughly -22,
-13, and -11 percent after about 49 hours. The full D/W/M flip never armed
because the gate stayed mixed, and the nearest adverse BF line did not cross
the price path
(docs/session_archive/HANDOFF_TVB10-TVB17.md:175-183).

This is a structural open-air state, not a one-symbol parameter mistake.
Neither a distant future BF line nor a full opposite gate guarantees bounded
loss.

Recommendation:

Keep thesis exits and account protection separate:

- thesis exits: target, BF harvest, adverse BF break, state/flip invalidation;
- risk exits: hard maximum loss, maximum holding risk, data-stale exit,
  liquidation-distance guard, margin/collateral guard, and operator kill.

The exact risk policy is a user design decision and should be pre-registered.
However, a finite worst-case loss boundary is mandatory before position sizing
or live testing can be meaningful. A canonical intrabar-3 invalidation can be
one research arm, but it should not be smuggled in as the universal answer;
the current work order correctly records that it is absent
(.session_startup_prompt.md:47-57).

### P1-6: Venue and clock are part of the strategy, not metadata

The charter correctly identifies HIP-3 as 24/7 but oracle-linked to underlying
assets that have different market hours
(docs/ATLAS_Timeframe_Continuity_Charter.md:38-46).

The project later measured a 30.84 percent disagreement between UTC and
RTH-anchored D/W/M gate readings on scored 5m bars
(docs/HANDOFF.md:843-850). The historical record also found venue-specific
results and warns that proxy backtests are not execution-venue tests.

Recommendation:

Every event and result must carry:

- venue and DEX namespace;
- canonical contract/asset identifier;
- exchange event timestamp and ingestion timestamp;
- bar clock/calendar version;
- oracle/mark/index context;
- source-data revision;
- tick and size rules effective at that time.

UTC and RTH clocks should remain separate named arms. Never switch clocks
dynamically because one currently performs better.

### P1-7: Historical parity is necessary but not sufficient

The TVB-20 control parity matched historical decision events, and TVB-22
reports 487/487 events over its gated cells
(docs/experiments/tvb20_control_port_parity.md:82-92,
pine/tfc_mt_package_strategy.pine:100-113).

That is valuable. It proves the two historical implementations agree under
the declared feed and cadence. It does not establish:

- one true implementation rather than two matching assumptions;
- correct within-bar event order;
- realtime tick parity;
- identical restart state;
- identical cash fills;
- robust failure behavior if an artifact is empty, partial, duplicated, or
  stale.

Recommendation:

Retain parity but expand it into a conformance matrix:

| Gate | Required proof |
|---|---|
| Semantic | Same state transitions from the same ordered events |
| Event | Same signal/order-intent identity and reason |
| Causal | Every decision uses only information available by decision_at |
| Fill | Same explicit order model, or a declared engine-specific residual |
| Cold start | Same readiness and state after checkpoint plus replay |
| Adversarial | Fail closed on missing symbols, rows, fields, non-finite values, duplicate events, and one-way joins |
| Realtime | Shadow comparison of live events, including later-revoked intrabar states |

### P2 observations

These are not immediate blockers, but they should be cleaned up before the
system becomes a shared implementation platform:

- README.md:21-27 and CLAUDE.md:3-6 are stale about the Python engine.
- The M+T PMG prefix is documented as structurally unreachable for the current
  setup block; keep the flag out of any edge claim until repaired and tested.
- The BF watch explicitly allows one structural object to exist in multiple
  pools; cross-pool deduplication is still future work
  (pine/tfc_bf_watch.pine:80-83).
- A semantic pool cap should not be inherited from Pine's drawing-resource
  constraints.
- The M+T health comments say outside bars are included, but the Python port
  records the as-built one-sided predicate where an outside bar sets neither
  u0 nor d0 (analysis/paper/patterns.py:157-180). The report corrected the
  interpretation; the contract should make it impossible for prose and code
  to diverge again.
- Current watch alerts carry human text but no strategy version, signal ID,
  state version, or idempotency key
  (pine/tfc_bf_watch.pine:553-558).

## 4. The implementation I would build

### 4.1 One pure semantic kernel

I would make a Python strategy kernel authoritative for replay, shadow, and
eventual live decisions. "Authoritative" means it owns the versioned semantic
contract, not that Pine becomes unimportant.

Pine would remain:

- the chart-native visual explanation;
- an independent implementation oracle;
- a historical/realtime drift detector;
- an operator-facing discretionary surface.

The kernel would be:

- pure where possible;
- deterministic for an ordered input event stream;
- free of exchange I/O;
- versioned at every semantic boundary;
- serializable and replayable;
- based on Decimal for currency/order values;
- explicit about event time versus processing time.

Suggested high-level flow:

    Exchange trades/books/candles
                |
                v
       Canonical market-data log
                |
                v
       Bar builder and clock service
                |
                v
       Pure strategy transition kernel <---- Pine conformance oracle
                |
                v
        Desired order-intent ledger
                |
                v
          Portfolio risk gate
                |
                v
        Hyperliquid broker adapter
                |
                v
     Order/fill/account reconciler
                |
                +----> durable event log/checkpoints/telemetry

No component below the strategy kernel should rediscover patterns or gates.
No component above it should invent fills.

### 4.2 Canonical events

At minimum:

Market and clock events:

- TradeObserved
- BookSnapshotObserved
- CandleUpdated
- CandleClosed
- GatePeriodOpened
- GatePeriodClosed
- DataGapDetected
- InstrumentSpecChanged

Strategy events:

- GateStateChanged
- PatternDetected
- SignalAdopted
- SignalMorphed
- SignalInvalidated
- BfFormationBorn
- BfSideRetired
- EntryEvaluated
- EntryVetoed
- EntryIntentCreated
- TargetSnapshotCreated
- ExitIntentCreated

Execution events:

- OrderSubmitted
- OrderAccepted
- OrderRejected
- OrderCanceled
- OrderPartiallyFilled
- OrderFilled
- PositionReconciled
- FundingApplied
- RiskHaltRaised

Every event should include:

- event_id;
- semantic_version;
- venue and namespaced instrument;
- event_time;
- observed_at;
- source sequence or source hash;
- causation_id;
- correlation_id;
- component readiness version.

The kernel must never use data with event_time later than its decision time.
Tests should enforce this availability frontier.

### 4.3 Canonical state

Suggested StrategyState:

- instrument specification and clock version;
- current bar-builder state for every required timeframe;
- gate period opens and readiness;
- current developing and completed signal bars;
- signal registry and lifecycle;
- BF formation registry and side lifecycle;
- ATR and other explicitly approved derived state;
- strategy position intent, separate from broker position;
- target geometry snapshot;
- last processed source sequence;
- semantic and schema versions.

Suggested AccountState, owned by the portfolio/execution layer:

- actual positions and average fill;
- open orders by deterministic client order ID;
- free collateral and margin mode;
- mark/oracle prices and liquidation distance;
- realized/unrealized P&L;
- accumulated fees and funding;
- risk limits and halt state.

Do not combine desired strategy position with actual exchange position. The
reconciler exists precisely because those can differ.

### 4.4 Component boundaries

#### ClockService

Own:

- UTC 5m/15m/1h/12h/D/W/M boundaries;
- any separately versioned RTH calendar;
- holiday/session attribution if that arm is tested;
- timestamp normalization and late-event policy.

No pattern or gate code should hand-roll time keys.

#### BarBuilder

Build all timeframes from one ordered venue-local event stream. It should emit
developing updates and immutable closes, detect gaps, and be reconstructible
from the event log.

#### TfcGate

Input: a price event and versioned period opens.

Output:

- up, down, neutral;
- ready/not-ready;
- exact contributing legs;
- transition reason.

Keep execution and regime gates separate even if they share code.

#### PatternDetector

Input: completed history plus the current developing signal bar.

Output: immutable PatternObservation values, not orders.

Carry:

- setup_id and human label separately;
- direction;
- trigger;
- anchors;
- weak/fragile/reversal/boom/PMG flags;
- observed_at and whether the observation is provisional;
- source signal-bar identity.

Preserve the 10-setup dictionary as one pre-committed block. Do not rank and
select individual patterns from the current window.

#### SignalMemoryPolicy

Make the full M+T remember/morph behavior optional and explicit. Its output is
SignalLifecycle events. This prevents the detector from silently deciding
whether an older signal remains actionable.

#### BfRegistry

Own formation and side IDs, lifecycle events, line valuation, and readiness.
Geometry must be independent of how lines are used:

- harvest target;
- adverse structural exit;
- entry proximity feature;
- chart context.

One line can serve multiple policies without duplicating its lifecycle.

#### LadderBuilder

Pure function:

    completed signal history + detected setup + threshold rules
        -> ordered structural levels + provenance

Separate target geometry from exit policy. Snapshot the geometry at the
declared strategy event. After a real entry fill, create reduce-only order
intents from the actual filled size and price-dependent eligibility rules.

#### EntryPolicy

Consumes:

- signal lifecycle;
- gate state;
- BF state;
- target geometry;
- floor;
- gate-open proximity;
- portfolio permission.

Returns one reasoned eligibility result. It does not submit orders.

#### ExitPolicy

Evaluate thesis exits and risk exits separately. Emit DesiredOrderIntent with
priority and causation. Do not directly mutate broker position state.

#### PortfolioRisk

Required before live shadow:

- risk per trade;
- symbol and correlated-group caps;
- gross/net caps;
- DEX/collateral caps;
- open-order worst-case exposure;
- daily/rolling loss limits;
- maximum strategy drawdown halt;
- data/oracle/mark staleness;
- liquidation-distance floor;
- funding and fee budgets;
- operator and automatic kill switches.

### 4.5 Fill and order model

Each strategy entry must choose one actual model:

Resting stop/limit model:

- intent exists before touch;
- exchange order acceptance is recorded;
- fills occur only after acceptance;
- cancel/revoke latency is modeled;
- partial fills and gap-through are possible.

Market-on-decision model:

- decision is timestamped after all predicates are known;
- fill uses the first executable book after decision plus modeled latency;
- spread and depth impact are charged;
- rejected/partial outcomes are represented.

The current hybrid - decide from a completed bar, fill at an earlier level -
should remain available only as a named legacy research convention.

For coarse historical data, produce:

- best-case fill;
- worst-case fill;
- decision-close fill;
- unresolved-order flag.

Performance reports should show sensitivity to those alternatives.

### 4.6 Costs and capacity

The repository already contains older fee, funding, and L2-impact components
(analysis/funding_model.py:1-16,
analysis/l2_book_impact.py:1-17,
analysis/fee_rates_by_dex.py:1-19,
tfc/simulator.py:1-21). Their concepts should be reused, but they should be
integrated through one versioned cost service rather than copied into the
Tier B loop.

The live/replay cost ledger should include:

- maker/taker fee actually applicable to the account and HIP-3 DEX;
- deployer or builder fee where applicable;
- spread;
- depth-based impact;
- latency drift;
- hourly funding;
- failed/retried order costs where relevant;
- liquidation and forced-deleveraging scenarios.

Never hardcode one "real fee" permanently. Query or snapshot the effective
schedule and store its version with the result.

### 4.7 Position sizing

Current 100 percent equity strategy sizing and 1x per-symbol replay sizing are
research normalizations, not a live policy.

I would size from:

    allowed_loss / conservative_stop_distance

where conservative_stop_distance includes:

- the selected hard risk boundary;
- gap/impact allowance;
- a volatility/liquidity floor;
- venue tick and size rounding.

Then cap that size by:

- available isolated/cross collateral;
- liquidation-distance requirement;
- instrument and group exposure;
- order-book capacity;
- portfolio loss budget.

Without a finite risk boundary, risk-based sizing is undefined. This is why
the open-air stop design must precede live sizing.

## 5. Research program I would run

### Phase R0: Finish the current contract

Complete the existing TVB-24 task exactly as already specified:

- mirror floor and ATR semantics into the package Pine;
- add the D1/DINF/D1ATR arm selector;
- rerun the 9-cell parity gate;
- keep the mounted package restricted to TVB-22 arms until PASS.

Do not mix the architecture refactor into this change. It should close the
current experiment lineage cleanly.

### Phase R1: Write the semantic specification

Before another strategy feature:

- document every clock and decision point;
- define provisional versus committed signals;
- define signal identity, expiry, invalidation, and retry;
- define BF identity and lifecycle;
- define target geometry snapshot time;
- define actual entry and exit order types;
- define same-event precedence;
- define cost, sizing, and portfolio units;
- version the historical legacy conventions.

Acceptance gate: two independent implementers should be able to produce the
same state transitions without reading the old implementation.

### Phase R2: Build the kernel and conformance suite

Extract pure behavior from the Python twin into components, preserving a
legacy adapter that reproduces current artifacts.

Tests:

- golden Pine/Python event fixtures;
- property tests for monotone target ladders;
- BF lifecycle and cross-pool identity tests;
- signal morph/revocation tests;
- empty, duplicate, missing, NaN, and out-of-order input tests;
- cold start, checkpoint, replay, and removal/reordering tests;
- timezone and period-boundary tests;
- same-signal re-entry tests;
- deterministic Decimal rounding tests.

Acceptance gate: the legacy adapter reproduces committed current events while
the new schema records richer identities and causality.

### Phase R3: Establish causal execution bounds

For the current matched-control and D1 arms:

- replay lower-timeframe venue-local data;
- determine first all-predicates-true time;
- compare resting-order, market-on-decision, close-fill, optimistic, and
  pessimistic conventions;
- enumerate same-bar target/stop collisions;
- add spread, fee, impact, latency, and funding sensitivity.

Acceptance gate: no headline result depends on an unreported OHLC ordering
assumption.

### Phase R4: Restore identified layer contrasts

Run a current clean ladder:

1. C0-current: one entry stream plus state stop.
2. C1-current: identical entry stream plus BF exit policy.
3. Pattern-only: pattern entry substitution with C1 exits.
4. Floor-only over pattern entries.
5. BF-proximity-only.
6. Gate-open-proximity-only.
7. Target substitution, each depth named before the run.
8. Full package.

The exact set should be pre-registered with the user. The point is
identification, not more arms for their own sake.

Report opportunity-level and evaluation-level funnels separately.

### Phase R5: Fresh chronological evidence

Use:

- multiple non-overlapping chronological windows;
- an as-of universe and listing history;
- venue-local HIP-3 data wherever execution is proposed;
- regime and liquidity labels defined without future data;
- frozen contract and parameters;
- no pattern or depth promotion from the existing window.

The current report already calls fresh-window replication the largest evidence
gap (.session_startup_prompt.md:37-40). I agree.

Minimum outputs:

- per-window and pooled results;
- fees/funding/impact;
- directional and venue decomposition;
- unique-signal funnel;
- concurrent exposure and portfolio result;
- failure regime inventory;
- parameter-neighborhood sensitivity without selecting the winner.

### Phase R6: Exit and risk design

Only after R3-R5:

- compare state, partial/full flip, BF break, target scale-out, and any
  intrabar-3 invalidation as pre-registered variants;
- add a mandatory catastrophic-risk overlay to all arms;
- test partial T1 realization plus runner versus all-out T1;
- inspect winner/loser paths, not win rate alone;
- stress stale data, gaps, oracle changes, and thin books.

No exit should be adopted merely because it creates a high win rate.

## 6. Far-future live architecture

### 6.1 TradingView's role

TradingView should not be the sole source of live truth for this strategy.

Official Pine documentation confirms that indicators and strategies differ on
realtime bars, strategies default to close-only execution, and temporary
intrabar state is not preserved after reload. See the current
[TradingView execution model](https://www.tradingview.com/pine-script-docs/language/execution-model/).

TradingView alerts are snapshots of the script, inputs, symbol, and timeframe;
changing the chart script does not update an existing alert. See
[TradingView alerts](https://www.tradingview.com/pine-script-docs/concepts/alerts/).

Recommended role:

- independent shadow oracle;
- operator visualization;
- discrepancy alerting;
- optional advisory signal input.

If a TradingView webhook is retained:

- acknowledge and durably persist it quickly;
- never put credentials in the payload;
- apply receiving-edge authentication and source validation supported by the
  deployed gateway and TradingView's documented capabilities;
- use a deterministic idempotency key;
- revalidate signal version, market state, and risk in the canonical service;
- never execute a duplicate delivery twice.

TradingView documents a short webhook processing timeout and possible delivery
failures in its
[webhook configuration guide](https://www.tradingview.com/support/solutions/43000529348-how-to-configure-webhook-alerts/).
It can retry qualifying failed webhook deliveries, so idempotency is required;
see [webhook resubmission](https://www.tradingview.com/support/solutions/43000735201-webhook-resubmission/).

### 6.2 Hyperliquid integration

Use the exchange's websocket and account streams as the live source of market,
order, fill, funding, and account truth.

Current official capabilities relevant to the design:

- order client IDs, reduce-only orders, GTC/IOC/ALO limits, trigger orders,
  cancel by client ID, modify, expiry, and scheduled cancel are exposed by the
  [exchange endpoint](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint);
- orderUpdates, userFills, userFundings, books, trades, candles, and account
  streams are exposed through
  [websocket subscriptions](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions);
- automated clients must reconnect and recover snapshots/missed state, per the
  [websocket guide](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket);
- API wallets sign for a master account but account queries use the master or
  subaccount address; signer nonce state requires careful process isolation,
  per [nonces and API wallets](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/nonces-and-api-wallets);
- price and size serialization must respect current asset metadata and
  [tick and lot size rules](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/tick-and-lot-size);
- integration design must obey the current
  [rate and user limits](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/rate-limits-and-user-limits).

Broker adapter requirements:

- one dedicated API wallet per trading process/account boundary;
- deterministic client order ID derived from order_intent_id;
- idempotent submit/cancel/modify;
- reduce-only exits;
- explicit handling of partial fills and rejected sizes/prices;
- order-status recovery by order ID or client ID;
- desired-versus-actual position reconciliation;
- heartbeat and dead-man cancel policy;
- no strategy decision inside the adapter.

All exchange constants should be refreshed from current official metadata and
covered by integration tests. They should not be copied from this dated
assessment into permanent code.

### 6.3 HIP-3-specific controls

HIP-3 deployers control market definition, oracle operation, leverage limits,
and settlement behavior. See
[HIP-3 builder-deployed perpetuals](https://hyperliquid.gitbook.io/hyperliquid-docs/hyperliquid-improvement-proposals-hips/hip-3-builder-deployed-perpetuals).

The live risk service should therefore monitor:

- DEX and asset identity, including namespaced coin;
- halt/settlement and exchange status;
- oracle, mark, mid, and basis divergence;
- effective leverage and margin tier;
- open-interest and market limits;
- fee/deployer-fee changes;
- book depth and stale/no-book conditions;
- hourly funding
  ([funding documentation](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding));
- liquidation distance under the actual margin mode
  ([margining](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/margining),
  [liquidations](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/liquidations)).

Fail closed if instrument metadata is missing, non-finite, inconsistent, or
not fresh enough for the intended order.

### 6.4 Durable execution lifecycle

For every signal:

1. Kernel emits EntryIntentCreated.
2. PortfolioRisk accepts, resizes, delays, or rejects it.
3. Broker creates deterministic client order ID.
4. Submission response is stored.
5. Websocket order updates and fills reconcile actual state.
6. Target/stop orders are created only from confirmed filled size.
7. Cancels and replaces are idempotent.
8. On restart, open orders and positions are queried before new decisions.
9. Any mismatch raises a risk halt; the system never guesses.

For every process restart:

1. load last valid checkpoint;
2. reconnect market and user streams;
3. ingest snapshot acknowledgements;
4. query actual open orders and positions;
5. replay missed market events;
6. compare desired versus actual state;
7. become ready per symbol only after all components agree.

No global "service healthy" flag should imply every coin is strategy-ready.

## 7. Migration plan against the current repository

The current files should not be rewritten wholesale. They are valuable
historical oracles.

| Current object | Future role | Migration action |
|---|---|---|
| pine/baseline_continuity.pine | Original C0-family oracle | Freeze; use to define historical contract and a clean current C0 variant |
| pine/tfc_companion.pine | Manual/realtime timing oracle | Preserve; use shadow observations for close versus intrabar arming |
| pine/tfc_bf_watch.pine | BF visualization and realtime Pine oracle | Preserve; enrich future alert payloads only after semantic IDs exist |
| pine/strat_magnitude_targets_plus.pine | Full display-behavior oracle | Preserve; split detector, memory, chop, and health semantics in the spec |
| pine/tfc_bf_control_strategy.pine | Historical C1 parity oracle | Freeze by semantic version |
| pine/tfc_mt_package_strategy.pine | TVB-22/23 package parity oracle | Finish TVB-24 mirror, then freeze version |
| analysis/paper/engine.py | Legacy executable twin | Wrap as legacy contract; extract pure components incrementally |
| analysis/paper/patterns.py | Seed for pure detector/ladder | Add immutable observation IDs and event-time semantics |
| analysis/paper/tier_b.py | Research runner | Retain additive pp rollup; add separate portfolio runner |
| Existing result folders | Immutable evidence | Never rewrite across semantic versions; manifests point to exact contract |

Suggested new boundaries, when implementation is authorized:

    strategy_core/
        events.py
        clocks.py
        bars.py
        tfc_gate.py
        patterns.py
        signal_lifecycle.py
        bf_registry.py
        targets.py
        entry_policy.py
        exit_policy.py
        state.py

    execution/
        intents.py
        portfolio_risk.py
        cost_model.py
        hyperliquid_adapter.py
        reconciler.py
        checkpoints.py

    validation/
        conformance/
        causality/
        portfolio/
        live_shadow/

These paths are proposals, not changes made by this assessment.

## 8. Live-readiness gates

### G0: Research lineage closed

- TVB-24 mirror passes.
- Existing reports and artifacts remain reproducible.
- No unreviewed semantic drift.

Rollback boundary: return to the last parity-gated Pine/Python versions.

### G1: Semantic readiness

- One versioned contract.
- Signal, BF, target, position, and order identities defined.
- Every provisional/committed clock explicit.
- Legacy contracts named.

Rollback boundary: kernel version; events remain replayable under their
original version.

### G2: Causal replay readiness

- Lower-timeframe or bounded fill model.
- Same-bar collisions measured.
- Fees/funding/spread/impact/latency included.
- No future data crosses decision time.

Rollback boundary: performance claims revert to research-only legacy
conventions.

### G3: Research readiness

- True C0/C1 isolation.
- Orthogonal package ablations.
- Fresh chronological windows.
- As-of universe and venue-local data.
- Portfolio results and failure regimes.

Passing does not authorize trading. It only permits shadow evaluation.

### G4: Shadow readiness

- Live kernel runs with no order authority.
- Pine and kernel events compared in realtime.
- At least one monthly gate transition and restart/reconnect cycle observed.
- Every discrepancy has a durable receipt.
- Readiness, staleness, and event lag are monitored per symbol.

Rollback boundary: stop shadow process; no market state was changed.

### G5: Execution rehearsal

- Testnet or no-risk paper adapter.
- Partial fills, reject, cancel race, duplicate delivery, websocket loss,
  process crash, stale data, and reconciliation fault injection.
- Dead-man behavior verified.
- Operator runbook and kill switch rehearsed.

Rollback boundary: cancel all test orders and disable adapter authority.

### G6: Tiny isolated canary

Requires explicit separate authorization.

- isolated collateral and minimum viable size;
- one symbol or tightly bounded set;
- hard per-trade, daily, and account loss caps;
- no automatic scaling;
- continuous reconciliation and independent alerts;
- immediate disable on any semantic or execution discrepancy.

Rollback boundary: reduce-only flatten, cancel all, revoke/disable the API
wallet, preserve the event log.

### G7: Controlled scale

Only after enough live observations to cover:

- calm and volatile regimes;
- weekends and underlying-market transitions;
- monthly/weekly/day boundaries;
- multiple fill and partial-fill paths;
- funding and liquidity stress;
- restarts and exchange disruptions.

Scaling is a new risk decision, not the automatic reward for a profitable
canary.

## 9. Recommended work order

If I were responsible for the next implementation sequence:

1. Finish TVB-24 mirror and parity exactly as already planned.
2. Write the canonical strategy semantic contract and signal lifecycle.
3. Add the causal entry/exit audit harness to the current engine.
4. Create an isolated current C0/C1 contrast with identical entries and costs.
5. Run fresh-window, venue-local replication under causal fill bounds.
6. Build the separate capital portfolio and risk simulator.
7. Extract the pure kernel behind a legacy-compatible replay adapter.
8. Run live shadow with zero order authority.
9. Build and fault-test the Hyperliquid adapter.
10. Reassess whether a tiny live canary is justified.

I would not spend the next major block adding more pattern choices or tuning
target depth. The current project has enough signal features to answer much
harder questions about causality, layer identification, and risk.

## 10. Non-goals

This assessment does not recommend:

- deploying the current package;
- promoting D1, D1ATR, A0b, a pattern, or a target depth;
- replacing the charter's exploratory stance with optimization;
- discarding Pine or the existing historical artifacts;
- using TradingView webhooks as an unaudited broker command bus;
- treating a high win rate as evidence of edge;
- hiding risk protection inside the alpha rule;
- tuning UTC versus RTH clocks from the current sample;
- refactoring the engine before the current TVB-24 lineage is closed.

## Final judgment

The current state is stronger than "three indicators plus some backtests."
It contains real state-machine work, disciplined experiment design, and a
valuable record of failed assumptions.

The central weakness is not lack of code. It is that the code has advanced
faster than the single strategy contract:

- original C0 and operational C1 are not an isolated layer pair;
- the package is a selected subset of M+T semantics;
- historical event parity is stronger than fill causality;
- symbol rollups are stronger than portfolio accounting;
- chart reconstruction is stronger than restart-safe live state;
- human alerts are stronger than broker-grade order identity.

Those gaps are all feasible to close. The best next contribution is a
canonical event-time kernel and causal execution harness, built around the
evidence already earned rather than replacing it. If that work is done first,
the eventual live implementation can be smaller, safer, and easier to prove.
