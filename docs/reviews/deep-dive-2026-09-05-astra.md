# STRAT / timeframe-continuity program: independent deep-dive review

Date: 2026-09-05
Scope: research, detection, execution, closed live books, replay, and proposed changes.
Disposition: findings and experiments for the owner's decision. No promotion or deployment decision.

## 1. Metadata and the answer in ten minutes

The strongest reason to change something is currently a risk calculation, not an arm's return. The executor can accept a structural stop beyond the estimated isolated liquidation price. Separately, parts of the research comparison use unattainable entry prices, and the halfway-entry replay rejects its own synthetic prices by construction. The fee-aware floor is sensible cost accounting, but its reported mechanism is overstated: shared trades do not improve, and replacement trades contribute materially.

Those findings do not erase the useful work. The closed books reconcile, the audit history retains failures, current tests pass, and several earlier execution defects have been repaired. They do change which conclusions can be drawn from the receipts.

Reviewed versions:

| Repository | HEAD reviewed | Difference from brief |
|---|---|---|
| tradingview-backtesting | 60ffdb09671c363078148e1d243fac5c870bfea3 | One documentation-only commit after 7ad92f4: this review brief and its handoff/index pointers |
| hip3-executor | d8a07b0516f79f513c4c202c6d988422a4ce4716 | Matches |
| hip3-scanner | 62adc75b43b8ececcc82b1142f1e4a5aec39ea4b | Matches |

Citation convention: repository-prefixed paths below are relative to C:/Strat_Trading_Bot. In abbreviated references, executor = hip3-executor, scanner = hip3-scanner, research = tradingview-backtesting; round2 = hip3-executor/runs/2026-08-31_round2, weekend1 = hip3-executor/runs/2026-08-22_weekend1, and replay1 = hip3-executor/runs/2026-09-04_replay1. A filename following a fully named directory inherits that directory. SKILL means C:/Users/Chris/.claude/skills/strat-methodology/SKILL.md, v4. CORPUS means tradingview-backtesting/docs/thestrat_ai. These abbreviations identify actual files, not interchangeable strategy versions. JSON references include keys/timestamps where a candle cache occupies one physical line.

Read: governing rules and charter; ARM_LEDGER; current handoff and relevant archived sessions; round-3 preregistration; prior implementation assessment and relevant audits; current scanner/rules/engine/broker/config paths; replay contract, amendments and retained receipts; both live books' decisions, trades, trackers, venue fills/funding and local candle caches; research event streams, rollups, matched receipts, MFE/MAE utilities; methodology and relevant source-corpus chapters. This was targeted source and data review across the whole program, not a line-by-line certification of every historical file.

Ran, without writing repository caches:

- Research: existing Python environment, -B -m pytest tests -q -p no:cacheprovider, external temporary directory: 287 passed, 2 skipped.
- Executor: same read-only test configuration: 1,144 passed.
- Scanner: node --test --test-reporter=dot: passed. node scripts/extract_core.js --check: all three generated blocks match.
- Independent calculations from committed positions and raw venue records: arm decompositions, fee-floor predicates, flip first touches, late-fill distances, risk distribution, funding concentration, weekend residual attribution, research fee algebra and entry containment.
- In-memory adverse-case probes of current production methods, with fake inputs and no venue calls: liquidation gate, malformed account response, protective order type, partial-close accounting, and detector anchor examples.
- Official Hyperliquid maintenance-margin documentation and TradingView request.security documentation, consulted 2026-09-05.
- Report verification: repository secret_scan.py --paths on this file with --strict passed; ASCII, whitespace, prohibited identifier patterns and explicit repository-path citation checks passed. Three independent review lanes checked their numerical, operational and methodology sections after drafting.

The repository Python launchers initially encountered local access restrictions; the existing environments then ran under approved execution access. An intermediate bundled-Python attempt could not load the research environment's different-version NumPy binaries. The successful suite results above come from the correct existing environments.

Limits: no SSH, service changes, trading, account/API queries, deployment verification, TradingView compilation, or replay parity/run/report commands. Live venue behavior under failure was not exercised. The replay receipts were read and decomposed, not regenerated. Candle extremes do not identify within-minute order or the executable spread. Some caches and the corpus are local-only; public readers need access to those inputs to reproduce every walkthrough. Configuration is not wholly safe to quote: its endpoint is deliberately omitted here. Only this report was written inside the repositories.

## 2. The three findings that matter

### Finding 1 - The stop is not always ahead of liquidation

**Trader sentence:** A ticket can satisfy the advertised clearance check even though the venue would be expected to liquidate it before its structural stop.

**Code sentence:** rules.evaluate accepts stop_distance <= 0.8 / effective_leverage. That approximates initial margin, not liquidation distance after maintenance margin. The broker also drops liquidationPx when normalizing positions. Sources: hip3-executor/src/hip3_executor/rules.py:261-267; hip3-executor/src/hip3_executor/broker.py:148-159.

For tier-zero isolated positions, ignoring fees, funding, mark/entry differences and subsequent margin changes, let L be selected leverage and m the maintenance-margin fraction. Adverse liquidation distances are approximately:

    Long:  (1/L - m) / (1 - m)
    Short: (1/L - m) / (1 + m)

At selected and maximum leverage 10, m = 0.05. The distances are 5.263% long and 4.762% short, while the code admits stops out to 8%. The intended 80% buffer would be tighter still. This follows the official [liquidation formula](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/liquidations) and [margin-tier definition](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/margin-tiers). The program already uses the appropriate short formula in tradingview-backtesting/analysis/trade_mae.py:31-38.

**Real trade, bar by bar: LITE short.**

1. September 1, 12:00 UTC hour: high 897.39, low 892.67. The 13:00 hour expands to high 907.91 and low 863.19, making an outside bar.
2. At 14:03:11 the decision sees mid 859.46, below the 863.19 trigger, with stop 907.91 and target 796.11. It qualifies.
3. The entry fills at 859.71, size 0.012, selected leverage 10. The structural price risk is gross $0.5784. Estimated initial-margin liquidation is 900.6486, before the 907.91 stop. The entry minute trades 859.24-860.68.
4. The actual position exits on a continuity flip September 2 at 00:16:08, price 869.56, gross loss $0.1182. There was no observed liquidation. Subsequent tracker adverse prices reach 871.295 at the one/four-hour checkpoints and 886.005 by 24 hours.

Sources: hip3-executor/runs/2026-08-31_round2/decisions_r2.jsonl:4963; trades.jsonl:81,87; tracker.jsonl:120,127,141; venue/meta.json:1173-1175; venue/htf_xyz_LITE_1h.json:1 and venue/candles_xyz_LITE.json:1, timestamp keys in the walkthrough.

This is not isolated to that illustration. Using recorded fills, selected leverage and cached maximum leverage, ACE short and NBIS long also place stops beyond estimated initial-margin liquidation; ZHIPU and DOT violate the intended 80% buffer even where the stop precedes liquidation. Exact historical liquidation prices were not journaled, so these are geometry findings, not claims of historical liquidations. The current fee-aware production gate also admits the reconstructed LITE, ACE and NBIS candidates. See cards R1-R4 and Appendix A.

### Finding 2 - Important experiments do not yet represent the trade they claim to test

**Trader sentence:** The halfway entry has not been tested, and the research control sometimes buys or sells at a price its entry bar never offered.

**Code sentence:** the halfway builder sets decision mid equal to trigger, then the gate requires strict inequality; the research control assigns the old hourly trigger after checking only the favorable extreme. Sources: hip3-executor/analysis/replay/one_three.py:160-180; analysis/replay/recon.py:382-383; analysis/replay/gates.py:197-200; tradingview-backtesting/analysis/paper/engine.py:752-785.

**Real refusal, bar by bar: XYZ100 halfway reversal.**

1. August 31, 14:00 UTC hour: O/H/L/C = 29393/29398/29314/29370. The 15:00 inside hour is 29371/29396/29340/29345. Its halfway line is 29368.
2. The forming 16:00 hour breaks the inside low first.
3. At 16:26 the one-minute candle is 29364/29371/29362/29371. It crosses halfway and CLOSES ABOVE halfway.
4. A later scanner 1-3 row arrives at 16:53:38. The arm retimes that row to 16:26:59, but writes mid = trigger = 29368. The strict in-force gate therefore rejects it.
5. There is no halfway fill to study. The observed close above the line directly contradicts the explanation that this candidate had recrossed by minute close.

Sources: hip3-executor/runs/2026-08-31_round2/decisions_r2.jsonl:257; venue/htf_xyz_XYZ100_1h.json:1, bars at 1788184800000 and 1788188400000; venue/candles_xyz_XYZ100.json:1, bar 1788193560000.

The exact 875-candidate breakdown reproduces: 359 volume refusals, 248 clock refusals, 268 equality refusals. The last group is a deterministic implementation problem, not market behavior. Moreover, candidates are generated from later far-side 1-3 rows, so halfway reversals that never subsequently complete a far-side pattern are missing. It is a retiming census conditional on future pattern completion, not a prospective halfway universe. Sources: hip3-executor/analysis/replay/__main__.py:276-281; analysis/replay/one_three.py:138-155.

This does not imply XYZ100 would clear later gates after repair. DOT supplies another clean price-state example: the August 31 16:44 minute closes at 0.82763, above halfway 0.82696 and below target 0.83340, leaving gross reward:risk about 1.1563 against stop 0.82264. The synthetic equality still rejects it; later portfolio eligibility was not established. Source: hip3-executor/runs/2026-08-31_round2/decisions_r2.jsonl:268; venue/candles_DOT.json:1, timestamp 1788194640000.

The research fill issue is separate and wider. In the fresh August 3-16 window, excluding the designated DRAM parity symbol, 58 of 106 hourly-breakout control entries lie outside their own five-minute candle's range. The ATR-stop control has 63 such entries out of 123. For example, AAPL on August 3 at 10:40 records a long at 308.591 while its candle trades 310.29-310.54. That price is not available on that bar. This does not calculate the corrected return; it prevents treating the existing return as executable. The full census and a worked example are in Appendix C.

### Finding 3 - Cost accounting is structural; the observed gain is partly portfolio replacement

**Trader sentence:** A setup should be assessed after costs, but the fee-floor receipt does not show better exits on the same tickets or a pure ability to remove losers.

**Code sentence:** the live port applies (reward - round_trip_fee) / (risk + round_trip_fee); common positions in the replay remain unchanged, while the gate and seat sequence change which other positions exist. Source: hip3-executor/src/hip3_executor/rules.py:222-244; replay decomposition sources below.

Round-2 net replay decomposition:

| Component | Count | Net dollars |
|---|---:|---:|
| Shared tickets | 21 | Change exactly $0 |
| Control tickets displaced | 11 | Had contributed -$1.6115 |
| Replacement tickets admitted | 11 | Contribute +$0.9923 |
| Total change from rounded position components | | +$2.6038 |

Approximately 61.9% of that component sum is avoided displaced losses, 38.1% is admitted contribution. Only SIX displaced tickets directly fail the net floor; their prior net contribution is -$0.9006 and includes an XMR winner of net +$0.5123. FIVE others disappear through portfolio timing and had contributed net -$0.7109. Calling all eleven fee-rejected losers confuses the gate with its downstream book.

Sources: hip3-executor/runs/2026-09-04_replay1/round2.json:22980,23074-23078,23440,23622,25374, plus positions keyed by identity. Whole-arm rounded metrics are net +$3.3036 versus +$0.6999; tiny differences from component sums are receipt rounding. Weekend v1-control comparison has 20 unchanged tickets, seven displaced contributing net -$1.6368 and six admitted contributing net +$0.1594; it retains its failed-parity watermark. Sources: weekend1.json:16961,17023-17027,17372,17534,18960.

**Real displaced ticket, bar by bar: TAO long.**

1. September 1, 01:00 UTC hour: 231.77/232.57/229.64/230.53. The 02:00 trap down-hour: 230.43/230.53/228.98/229.84.
2. The 03:33:13 decision sees mid 230.585, trigger 230.53, stop 228.98, target 232.57. Gross reward:risk is about 1.237.
3. With the declared main-dex round-trip fee assumption of 0.0864% of notional, net reward:risk is 0.98977. This ticket directly fails the new floor of 1.
4. In the actual gross-floor book it fills at 230.59, briefly reaches 231.58, and exits on a continuity flip at 04:14:42 at 229.85. Actual gross loss is $0.2301; actual net loss is approximately $0.2929 after fees and funding.
5. The original stop is touched at 04:59. This illustrates a cost-sensitive loser; it cannot establish that future cost-sensitive tickets lose.

Sources: hip3-executor/runs/2026-08-31_round2/decisions_r2.jsonl:2707; trades.jsonl:77-78; venue/fills.json:148,166; analysis.json:462; candle/tracker details in section 5.

The accounting form deserves consideration independently of these outcomes. The cutoff of 1 is still a policy threshold, and the observed improvement was explored on the same books that motivated the arms. The statement that the fee floor improves matched trades is false. The statement that its entire gain is what it refuses is incomplete. Neither correction requires abandoning net cost accounting.

## 3. Verdict by review dimension

| Dimension | Verdict | Finding and pointer |
|---|---|---|
| 4.1 STRAT faithfulness | Mostly faithful foundations; deliberate departures and specific defects | Strict classification/closed setups are sound. Hybrid continuity, continuation targets, far-side 1-3 and stop variants need explicit labels. Compound-inside mother anchoring and invalid HTF sponsorship need attention. Appendix B; scanner/src/strat_core.js:150-265; SKILL:166-209 |
| 4.2 Candidate selection | Mixed structural constraints and sample-motivated overlays | First-refusal counts are conditional; transition-only decisions and occupancy shape the available book. No stable late-entry penalty emerges across both samples. Appendix D; executor/src/hip3_executor/rules.py:142-295 |
| 4.3 Entry and sizing | Defect in margin clearance; fixed risk remains a useful control | Minimum tickets can exceed the nominal risk; the full round has 24/32 in the cited risk band. Finding 1; Appendix A/D |
| 4.4 Targets | Structural reversals mostly faithful; continuation/pivot/fallback departures | Nearest loaded pivot and 1.5-stop projection are not the same as containing structure or higher-TF extension. Appendix B; SKILL:366-427 |
| 4.5 Exits | Legitimate configured management; incomplete transfer evidence | Flip protection has useful observed stop-first paths; coupled opens do not automatically make it useless. Five isolated exit experiments below; section 5 |
| 4.6 Regime, clock, session | Configured overlays; several open questions | UTC roll, US bell, BTC sign and funding are distinct mechanisms. A global xyz bell is not an underlying-market calendar. Appendix D; R17-R18 |
| 4.7 Fidelity and measurement | Material limitations and verified model defects | Halfway equality, noncontained control fills, outcome-conditioned settlement and quote/candle differences. Finding 2; Appendix C |
| 4.8 Code and operations | Significant repairs plus remaining high-priority gaps | Clearance, malformed-flat response, backing eligibility, stop-limit acceptance and partial-close bookkeeping. Appendix A |
| 4.9 Research process | Substantial discipline; overstated interpretations | Retained failures help. Preregistration before code is not before seeing the data; matched-family intersections are selected subsets. Appendix E |
| 4.10 Other considerations | Open measurement work | Correlated seats, carry concentration, provenance, private-cache reproducibility and event-time observability matter more than another ranked pattern list. R9/R19; Appendix D/E |

## 4. Ranked recommendation cards

Ranks below prioritize correctness and information quality. They are proposals, not instructions to change live configuration. For experiment cards, the comparison base is the exact currently specified round-3 policy, with all unrelated rules held fixed. If an implementation defect is corrected, create and name that new base first; do not silently compare a corrected arm with a defective control.

All statistical falsifiers refer to a future, frozen, non-overlapping observation window, with missing/unresolved trades retained explicitly. Both existing live books and the reviewed research windows are already observed. Old-window runs can check mechanics and characterize sensitivity; they cannot serve as untouched confirmation.

### R1 - Put the structural stop ahead of liquidation

- **Trader:** Choose collateral/leverage that lets the stop do its job.
- **Code:** Replace the 1/leverage approximation in executor rules.py:261-267 with direction-, margin-tier- and collateral-aware clearance; after fill compare the frozen stop with venue liquidationPx, retaining mark and funding context. See broker.py:148-159.
- **STRAT status:** Faithful risk implementation around the structural stop, SKILL:407-414. No pattern deviation.
- **Structural rationale:** Maintenance margin consumes part of the apparent initial-margin cushion. A wider stop cannot be made safe merely by calling isolated collateral a premium.
- **Data motivation:** LITE, ACE and NBIS above; a code/geometry finding rather than a return-selected rule.
- **Predicted effect / falsifier:** Some tickets require less leverage or refusal. Drop the implementation if it still admits a stop beyond the configured fraction of venue-confirmed clearance, or rejects a hand-checked adequately collateralized case.
- **Receipt:** Direction/tier truth tables, recorded-ticket screen, then read-only post-fill shadow comparisons. Never shrink a structural stop merely to pass this rail.
- **Cost/risk:** More collateral or fewer tickets; metadata and post-fill checks. Estimated clearance still needs allowance for funding, mark movements and execution through the stop.
- **Existing policy boundary:** Missing/mismatched post-fill leverage currently warns without blocking, by owner ruling (executor engine.py:830-868). That is a disclosed choice, not an unauthorized exception. A clearance repair must explicitly define its unknown-margin behavior; the present warning cannot support a claim that venue-confirmed clearance was established.

### R2 - Missing account fields are unknown, not flat

- **Trader:** Failure to see the position must not be reported as proof it is gone.
- **Code:** Require a valid account-response schema before broker._positions_state can return an empty position map; malformed payloads remain unknown through position_for/requery_flat. Current source: executor broker.py:148-160.
- **STRAT status:** Operational correctness, no methodology change.
- **Structural rationale:** Only a successful, well-formed empty response supports flatness.
- **Data motivation:** In-memory current-method probe: user_state returning {} and order queries returning [] produces a zero-position/zero-order result. No historical occurrence established.
- **Predicted effect / falsifier:** Corrupt responses block entry/flat completion; valid empty responses still work. Any malformed response yielding a flat receipt falsifies the fix.
- **Receipt:** Fault-injection tests for absent, null, malformed and exception responses on each dex, including flatten and restart.
- **Cost/risk:** Conservative temporary blocking and alerts; no new trading primitive.

### R3 - Verify a stop-market, not just an order containing the word Stop

- **Trader:** The protection must still execute when price jumps through it.
- **Code:** Tighten broker._stop_row_ok, currently substring-matching orderType at broker.py:273, to the actual required stop-market schema.
- **STRAT status:** Operational implementation of the standing stop contract; no signal change.
- **Structural rationale:** A stop-limit can remain unfilled after triggering.
- **Data motivation:** A correctly sided, sized, reduce-only Stop Limit row passes the present verifier in an in-memory probe. The normal placement path creates market-trigger stops; no wrong live order was found.
- **Predicted effect / falsifier:** Wrong order type is rejected while correct market stops remain recognized. Any accepted stop-limit falsifies the change.
- **Receipt:** Rich-order truth table and persistent-protection checks.
- **Cost/risk:** Possible false alarms if venue nomenclature is mishandled; use its exact schema, not another loose string test.

### R4 - Account for every fragment of a close

- **Trader:** A retry must not erase the price of the first partial fill.
- **Code:** Persist partial close fills and calculate size-weighted final proceeds before _close_record uses original position size. Current paths: executor broker.py:234-260; engine.py:605-635.
- **STRAT status:** Measurement/accounting correction, no exit change.
- **Structural rationale:** Protection surviving a partial close is necessary; accurate realized accounting is a separate requirement.
- **Data motivation:** Probe: one-unit long entered at 100; 0.6 closes at 95, then 0.4 at 90. Actual gross loss is $7; the final-fill/original-size path records gross loss $10. No live-book incidence asserted.
- **Predicted effect / falsifier:** Fragment sums reconcile through retries/restarts; any duplicated or omitted fragment falsifies the repair.
- **Receipt:** Fault-injected partial/unknown closes, immutable fill IDs and venue reconciliation.
- **Cost/risk:** Persistent fill bookkeeping and duplicate handling; no new exit rule.

### R5 - Make the halfway experiment executable before interpreting it

- **Trader:** Test an actual actionable crossing, not a price guaranteed to fail its own gate.
- **Code:** Align one_three.synthetic_row and replay gates.py:199 around one declared decision/fill convention, and generate candidates prospectively from inside-bar state rather than later far-side rows. Source: one_three.py:138-180; __main__.py:276-281.
- **STRAT status:** Reclaim plus actionable lower-TF confirmation follows SKILL:177-182. A standalone halfway entry is a DEVIATION from R19, SKILL:415-425; its reason would be testing earlier participation at the cost of weaker confirmation.
- **Structural rationale:** Trigger observation, decision price and executable fill are different quantities. Strict-break classification must remain strict.
- **Data motivation:** XYZ100 and deterministic emptiness; no favorable result was available to select.
- **Predicted effect / falsifier:** Eligible crossings can both enter and fail in coherent fixtures. Equality-only rejection, later-row dependence or future first-break knowledge falsifies the experiment.
- **Receipt:** Measurement repair first. Then separate reclaim-with-confirmation and halfway-only policies; do not conflate their stop/target conventions or run them as one change.
- **Cost/risk:** Tick/quote data or explicit one-minute bounds; earlier entry increases false reversals. No return estimate is defensible from current A5.

### R6 - Price entries where the order can actually fill

- **Trader:** A trigger crossed earlier is not a standing offer at the old price.
- **Code:** Add a declared causal entry model around research engine.py:752-785 and :1168-1183; separately preserve unpinned replay settlement in executor analysis/replay/__main__.py:219-242.
- **STRAT status:** SKILL:435-441 treats gap-beyond entry as missed. Filling at the next executable quote is a labeled DEVIATION from that gap-entry rule, structurally motivated by explicitly testing market execution. Neither convention permits an unavailable old price.
- **Structural rationale:** Decision-time gate and fill must coexist in time.
- **Data motivation:** Fresh control 58/106 noncontained entries; see Appendix C. Designed after inspected data.
- **Predicted effect / falsifier:** Every fill has causal market support or an explicit bounded gap convention. A fill outside observed prices without a justified order lifecycle falsifies the model.
- **Receipt:** Preserve old receipts; add one price-model contrast with independent shared-entry and whole-book results. For live replay retain separate journal-conditioned and unpinned runs.
- **Cost/risk:** Rankings may change; raw time-series capture and wider uncertainty bounds. Do not count merely reconciling to known exits as independent fidelity.

### R7 - Keep the fee-floor explanation honest

- **Trader:** Compare what the target pays after costs with what the stop loses after costs.
- **Code:** Retain the net_reward_risk accounting form at executor rules.py:222-244; distinguish the dex-default verdict from per-coin shadow rates and subsequently measured execution costs.
- **STRAT status:** DEVIATION/additional eligibility filter beyond canonical pattern geometry. Structural reason: venue costs consume reward and enlarge loss; SKILL:366-393 does not specify this fee threshold.
- **Data motivation:** TAO and the decompositions above, explicitly in-sample. Rate choice and threshold 1 are policy assumptions; the accounting identity is not an expectancy model.
- **Predicted effect / falsifier:** Fewer cost-thin setups should pass. Accounting mismatch against actual charged fees falsifies the implementation; a lack of prospective net whole-book improvement falsifies the claimed performance benefit, not the arithmetic.
- **Receipt:** Gross-floor versus net-floor shadow on the SAME candidate stream; separately report direct rejects, indirect displacement, admissions, common trades and unresolved outcomes.
- **Cost/risk:** Can remove winners; default fees can under- or overcharge particular coins. Per-coin rates are a separate next contrast, not silently part of the already receipted arm.

### R8 - A dead higher-timeframe setup cannot sponsor a continuation

- **Trader:** Higher-timeframe sponsorship must survive its own invalidation.
- **Code:** Reject backing slots with Type 3 invalidation for ordinary reversal signals, preserving the genuine rev3 exception. Current helper: executor rules.py:98-122; candidate-only invalidation: :202-204.
- **STRAT status:** Faithful to SKILL:247-264; no added directional filter.
- **Structural rationale:** Price can remain beyond a trigger after the bar has already invalidated the premise.
- **Data motivation:** Deterministic current-code counterexample; historical frequency was not counted.
- **Predicted effect / falsifier:** Only invalid sponsors disappear. Rejection of clean sponsors or valid 1-3 sponsorship falsifies the repair.
- **Receipt:** Truth table plus source-tagged historical incidence, then full allocation replay.
- **Cost/risk:** Fewer continuations; no new order machinery.

### R9 - Record the market state needed to explain a trade

- **Trader:** Save what was fresh, what crossed, and what it would cost to enter.
- **Code:** Extend decision receipts with per-TF observation/refetch timestamps and opens, first-break time/source, target anchor/source/depth, executable bid/ask/depth, planned versus filled risk, and separate in-trade excursion state. Current boundaries: scanner loop.js:425-459,492-560; executor engine.py:1033-1099.
- **STRAT status:** Observation only; SKILL:268-305 separates bias, scenario and in-force state.
- **Structural rationale:** A poll timestamp cannot identify the age of every signal or the availability of its modeled fill.
- **Data motivation:** Roll approximation, gold residuals, late-fill signs and post-exit-only trackers.
- **Predicted effect / falsifier:** Independently reconstruct decisions and fill bounds without deriving inputs from refusal reasons or future exits. Persistent unexplained disagreement falsifies coverage.
- **Receipt:** Bounded immutable snapshots/shadow fields first; record all-gates masks on predecision portfolio state and stable candidate/poll IDs.
- **Cost/risk:** Storage and feed overhead; keep secrets and account identifiers out of public exports. Missing observations must remain missing.

### R10 - First exit experiment: stop waiting when the trade makes no progress

- **Trader:** Give the setup two of its own bar lengths to start paying.
- **Code:** Add one software exit: elapsed_since_fill >= 2 * signal_timeframe AND favorable excursion observed since fill < 0.5 * original stop distance. Keep entry, size, target, structural stop, invalidation and current flip unchanged. Extension point: executor engine.py:487-507.
- **STRAT status:** DEVIATION from v4's price-bounded validity, SKILL:273-279. Structural reason: a position can remain technically alive while consuming carry and a seat without directional progress.
- **Structural rationale:** Normalize patience to the signal horizon; do not use one fixed number of minutes for hourly and daily trades. The constants 2 and 0.5 are provisional design choices, not natural constants.
- **Data motivation:** Multi-hour occupancy, mostly unvisited runner rungs, and concentrated carry; both ledgers are in-sample.
- **Predicted effect / falsifier:** Shorter stagnant holds and less funding paid. Drop the performance hypothesis if prospective net shared-trade losses exceed avoided carry and net replacement contribution.
- **Receipt:** Shadow deadline/MFE first, then one replay contrast and a frozen forward window. MFE must be known at that instant, not a completed minute's later high.
- **Cost/risk:** Extra market exits and missed slow winners. **This is the ONE new exit I would test first**, because it isolates patience without adding partials, changing the target or weakening current flip protection.

### R11 - Defend half of a meaningful favorable excursion

- **Trader:** After gaining one original risk unit, do not surrender more than half the peak.
- **Code:** Once observed MFE >= 1R, ratchet an additional stop to entry + 0.5*MFE for longs, mirror shorts; never loosen the original stop. R is the frozen entry-to-structural-stop distance. Apply updates after the observation, not retrospectively within its bar.
- **STRAT status:** DEVIATION from structural reversal/target-based exits, SKILL:443-473. Structural reason: protect accumulated favorable travel independently of when a new pattern prints.
- **Data motivation:** DRAM give-back fixture and runner failures; explicitly in-sample, and that research fixture is not a live-executor receipt.
- **Predicted effect / falsifier:** Lower gross give-back with more scratches. Drop if fresh net shared-ticket losses and added costs dominate retained gains.
- **Receipt:** Ordered in-trade mid/quote observations; bounded lower-timeframe replay; no same-bar high-then-stop assumption.
- **Cost/risk:** Stop modifications or software execution; whipsaw and jump-through risk. One-R arming and one-half protection are provisional.

### R12 - Test an ATR cap on adverse travel

- **Trader:** Keep the structural stop, but test a closer volatility-sized loss boundary.
- **Code:** Freeze completed signal-TF ATR(14) at fill; long effective stop = max(original stop, entry - 3*ATR), shorts mirror. Keep original position size fixed to isolate the exit change. Do not resize upward to the tighter test stop.
- **STRAT status:** DEVIATION from structural-stop placement, SKILL:407-414; volatility normalizes distance across instruments. Period 14 and multiplier 3 reuse a declared research convention, not a newly selected winner.
- **Data motivation:** ATR overlay helps the research control whole-book but hurts the package; fresh matched control results are weaker, Appendix C. No direct transfer claim.
- **Predicted effect / falsifier:** Smaller adverse tails, potentially fewer recoveries. Drop if fresh net shared-ticket damage exceeds tail/whole-book benefit under the same feasible fill model.
- **Receipt:** Separate live-control replay arm with frozen ATR/source timestamp. Adequate closed-bar history is a prerequisite: the scanner's 12 retained four-hour bars cannot initialize ATR(14). Acquire a separate ATR history without silently changing the detector's target lookback; report overlay eligibility by timeframe. Missing ATR leaves the original protective stop and labels the overlay unavailable.
- **Cost/risk:** More stops, fees, and recoverable dips cut short. It may rarely bind because the current structural stop is already tighter.

### R13 - Exit a breakout that fails back through its trigger

- **Trader:** Test whether a meaningful recross means the attempted breakout is over.
- **Code:** After entry, add an exit when price crosses adversely beyond trigger by 0.25 * completed signal-TF ATR frozen at fill. Preserve all existing exits and original sizing.
- **STRAT status:** DEVIATION: v4 revokes in-force on a trigger recross but does not universally command a full exit with an ATR buffer; see SKILL:273-279 and the specific 3-2 stay-out rule :198-203.
- **Structural rationale:** Test failure near the thesis boundary before the remote structural stop. The quarter-ATR buffer is provisional noise tolerance.
- **Data motivation:** Frequent flip exits and failed continuations; inspected-sample hypothesis.
- **Predicted effect / falsifier:** Earlier failed-break exits; drop if fresh net false exits on recovered winners exceed saved loss/carry.
- **Receipt:** Trigger-relative ordered path and frozen ATR; one added-exit arm.
- **Cost/risk:** More churn; recross does not necessarily invalidate the larger structure.

### R14 - Exit a reversal at a nearby target zone before the distant target arrives

- **Trader:** A completed reversal at resistance/support can end the trade before T1.
- **Code:** Freeze zones from completed 2U/3 highs for longs and 2D/3 lows for shorts on the trading timeframe and higher, rather than only the k=2 pivot set already defining T1. Require the whole eligible zone to lie strictly between entry and the unchanged T1; no eligible zone means control behavior. Monitor ONE timeframe below the entry. Add a full exit only after a completed opposing reversal combination at a zone. Define zone tolerance as 0.25 * frozen signal-TF ATR for this experimental arm.
- **STRAT status:** Faithful stall/reversal concept, SKILL:468-473; **DEVIATION** from that section's 0.25%-of-price clustering to ATR-scaled tolerance. Structural reason: comparable zones across volatility levels.
- **Data motivation:** Stall versus extension observations; same already-read research sample. An inside bar alone remains caution, not exit.
- **Predicted effect / falsifier:** Fewer stalled give-backs; drop if fresh net avoided losses do not cover premature target exits and fees.
- **Receipt:** Scanner-emitted frozen zones and lower-TF reversal timestamps, replay only after those inputs exist. The executor continues not to analyze bars.
- **Cost/risk:** More detection/state complexity; confirmed-bar latency and scarce valid zones. Do not secretly add confluence weighting as another change.

### R15 - Pay the containing outside wick first

- **Trader:** Do not ignore nearby unfilled structure because the pivot detector cannot yet call it a pivot.
- **Code:** For same-color 3-1-2 continuations only, replace contTarget with the containing 3's directional wick; other patterns and exit rules unchanged. Current scanner strat_core.js:170-180,197,203.
- **STRAT status:** Faithful to SKILL:27-31,388-393 and CORPUS/02 - The 3 Scenarios/10 - 3-1-2/article.md:44-46.
- **Structural rationale:** The obstacle exists without two later bars confirming a swing.
- **Data motivation:** The source/code counterexample in Appendix B and continuation losses; performance premise is in-sample.
- **Predicted effect / falsifier:** Smaller realistic targets and more floor refusals. Drop the performance hypothesis if fresh net opportunity loss outweighs improved target honesty; do not erase the semantic difference.
- **Receipt:** One target-only arm with target-source tags, direct floor effects, matched trades and resulting allocation.
- **Cost/risk:** Fewer entries and earlier profits; cannot attribute changes solely to exits because targets also gate entries.

### R16 - One real structural rung beyond T1, on daily entries only

- **Trader:** Test the daily runner against the next actual higher-timeframe obstacle.
- **Code:** For daily entries with a known, frozen next higher-TF pivot, replace full T1 take-profit with full take-profit at that next pivot; if absent, keep T1. Original T1 continues to govern entry reward:risk, reach and target-unreached eligibility; substitute only the resting exit destination after admission. Keep stop, size and software exits unchanged. Current target/tracker distinction: executor engine.py:1033-1042; scanner strat_core.js:58-82.
- **STRAT status:** Faithful extension/management option, SKILL:372-393; change from the current full-T1 management configuration.
- **Structural rationale:** Daily structure may merit a larger destination; repeated multiples of the initial target distance are not that structure.
- **Data motivation:** Owner's daily-walk-up idea and reviewed ladder receipts; no claim that current all-timeframe walk-up tests it.
- **Predicted effect / falsifier:** Higher matched payouts at the cost of holding time. Drop if a fresh daily cohort has no net shared-trade benefit or net portfolio loss dominates.
- **Receipt:** First establish daily-candidate coverage and immutable pivot availability. Introduce 2h/8h/12h feeds separately if required; never pretend the existing arm contained them.
- **Cost/risk:** Sparse daily samples, deeper history, carry and occupied seats. No partial fills or stepped stop added in this target-only experiment.

### R17 - Compare immediate hourly/daily control with the current entry stack

- **Trader:** Test whether the fast participants agree before requiring every monitored dot.
- **Code:** One entry-only arm replaces 15m/1h/4h/1d unanimity with own hourly and daily price-above/below-open agreement. Leave current flip exit unchanged. Existing gate: executor rules.py:269-270; scanner metrics.js:191-214.
- **STRAT status:** Sourced immediate-control predicate, SKILL:300-305; DEVIATION from the current full-stack entry rule. This is not a rewrite of FTFC's definition.
- **Structural rationale:** Entry timing and swing bias answer different questions; a fifteen-minute open may unnecessarily delay a daily setup.
- **Data motivation:** Weekend confirmation-lag observation does not repeat consistently in round 2; explicitly in-sample.
- **Predicted effect / falsifier:** Earlier/more admissions. Drop if fresh net gains from earlier entrants do not cover extra turnover, false breaks and changed occupancy.
- **Receipt:** Shadow both predicates on every eligible candidate with actual poll IDs; separate this from D/W/M-only continuation licensing and BTC-veto removal.
- **Cost/risk:** More churn and weaker agreement. Do not change the flip clock in the same arm.

### R18 - Name the actual session and carry burden

- **Trader:** A US-share bell is not a universal clock for oil, gold and Asian exposure.
- **Code:** Add shadow instrument-session/oracle state and signed funding budget, without changing the current entry gate. Current clock: executor rules.py:35-45,158-160; scanner underlying_map.js:28-30,52-59,68-71,86.
- **STRAT status:** Venue/risk observation, no pattern change. Any later class-specific trading-hours replacement is a DEVIATION from the present global xyz window, justified by actual reference-market/liquidity structure.
- **Structural rationale:** Reference availability, spread and carry differ by instrument and session.
- **Data motivation:** Extended-hours bottlenecks and ACE's concentrated funding bill; not evidence to turn a particular session on/off.
- **Predicted effect / falsifier:** Session labels should explain measurable quote/depth/oracle differences. Drop a proposed session veto if fresh differences disappear; inaccurate calendars falsify the measurement itself.
- **Receipt:** Shadow actual calendars/holidays, market status, mark-oracle divergence, funding timestamps and paid/received cash. Only then price ONE hours or carry rule.
- **Cost/risk:** Calendar maintenance and stale forecasts. The named weekend, OPEX and Korea windows are a-priori labels, not already justified bans.

### R19 - Make the next comparison capable of disagreeing

- **Trader:** Freeze the question before the next tape; keep every ticket that makes the answer inconvenient.
- **Code:** Extend replay/report manifests and matched-entry reporting, without changing execution. Existing intersection logic: research tier_b_exits.py:627-703; live replay settlement: executor analysis/replay/__main__.py:219-242.
- **STRAT status:** Research process, no methodology deviation.
- **Structural rationale:** A shared closed-trade intersection and a known-exit-pinned replay answer narrower questions than a deployable strategy comparison.
- **Data motivation:** Nine post-dig arms, the A9 narrative and the current fidelity amendments.
- **Predicted effect / falsifier:** Independent readers can reproduce denominators, direct/indirect displacement and unpinned results. Unlogged tuning, future-conditioned candidates or unexplained missing trades invalidate that comparison.
- **Receipt:** Freeze one control and one increment, code/input hashes, window, model assumptions, missing-data handling and success/failure measures. Report pairwise shared trades, full complements, open positions and a common candidate-level exit diagnostic alongside constrained portfolio results.
- **Cost/risk:** More bookkeeping and slower conclusions; no requirement to stop useful exploratory data generation.

### R20 - Repair compound-inside ancestry explicitly

- **Trader:** Another inside bar tightens the setup; it does not move its original mother.
- **Code:** For accepted compound-inside Rev Strat sequences, retain the original mother anchor instead of fixed closed[n-3]; current scanner strat_core.js:215,220.
- **STRAT status:** Faithful to SKILL:168-175. Explicitly excluding the longer setup would be a different, narrower coverage policy.
- **Structural rationale:** Identity of the target-generating structure survives nested inside bars.
- **Data motivation:** Deterministic mother-115 versus served-110 example in Appendix B; ledger frequency unmeasured.
- **Predicted effect / falsifier:** Nested sequences preserve the mother, while simple sequences remain identical. Any unintended simple-pattern change falsifies the repair.
- **Receipt:** Hand-checked ancestry cases and historical incidence before one target-scope replay.
- **Cost/risk:** Wider targets can change reach and fee-floor admissions. Do not simultaneously change the stop or introduce omitted pattern families.

### R21 - Rank executable costs only when real competition exists

- **Trader:** When two valid tickets want the last seat, prefer the one cheaper to execute relative to its planned risk.
- **Code:** After all non-capacity gates, rank same-poll candidates by estimated round-trip execution cost divided by original stop risk; use deterministic existing arrival order for ties. Current arrival scan: executor rules.py:54-65; seat gate :288-289.
- **STRAT status:** DEVIATION/additional portfolio allocation rule; STRAT structure does not itself define a cross-instrument seat auction.
- **Structural rationale:** Spread/depth cost is an executable burden, whereas signal names or heat ranks do not establish opportunity quality. A high reward:risk caused by an invented distant target must not win the seat.
- **Data motivation:** Higher-timeframe-first was inert in round 2; that does not measure this rule. No outcome-derived score or weight is proposed.
- **Predicted effect / falsifier:** Lower cost per booked risk among contested admissions. Drop if prospective cost saving is absent or net opportunity loss exceeds it.
- **Receipt:** Actual poll grouping and executable quotes first; report how often ordering changes a selection and the displaced alternatives.
- **Cost/risk:** Quote estimates can be stale; delayed ranking itself can cost fills. No batching delay or extra seats in this arm.

### The one change, independently reasoned

If only one implementation change were available, I would correct **actual liquidation clearance (R1)**. A half-dollar stop-risk budget is not fulfilled if liquidation arrives first. That choice follows the venue contract and current code, not the return leaderboard.

For the narrower question of one strategy eligibility variable, the net-of-fees floor is my choice over the other eight receipted variants, for its explicit cost arithmetic. I agree with that part of Claude's answer. I disagree with its justification through matched-trade improvement, pure loser removal, or positive results on two already-inspected books. The cutoff and fee schedule remain assumptions to characterize.

The brief disclosed Claude's answer before this review began. It would be inaccurate to claim this was a blinded choice.

### What I would not have done, ranked

1. Used 1/leverage as stop-to-liquidation clearance: R1.
2. Treated malformed absence as a successful flat account or accepted a stop-limit as the specified protection: R2-R3.
3. Interpreted an empty synthetic-entry arm before checking whether its prices could pass its own predicate: R5.
4. Compared research returns as attainable while assigning old trigger fills outside the current bar, or treated known-exit settlement as independent reproduction: R6.
5. Said the fee-floor gain appears in matched trades when those trades are identical: R7/R19.
6. Treated the researched ATR-stop benefit as transferable to every book, or removed current structural protection because a target-exited research arm looks better without it: R1/R12.
7. Read a first-refusal pool as the universe of opportunities that one removed gate would add: R9/R19.
8. Let target fallback, mother ancestry and continuation exits drift behind familiar STRAT names: R15/R20.
9. Described five seats or higher-timeframe sorting as generally irrelevant after one constrained-book experiment: R21.
10. Bundled partial banking, breakeven and trailing into the next attempt to solve give-back. Test patience or one exit first: R10-R14.

## 5. Full live-ledger walkthroughs

All times here are UTC. O/H/L/C describes the recorded trade candle, not necessarily what the scanner's quote-union candle displayed. Fees are stated separately from gross trading proceeds; net means the specifically stated costs have been deducted.

### 5.1 SOL: a coupled-open flip that still avoided a later stop

**Setup and decision.** September 1, 16:00 four-hour candle: 101.98/102.00/98.289/100.03. The 20:00 inside candle: 100.03/100.30/98.873/99.931. On September 2 at 01:47, the minute prints 98.995/98.995/98.820/98.827, breaking the inside low first. At 03:10 price trades 99.963/100.18/99.963/100.13. The 03:11 minute reaches 100.37, completing the far-side reversal above 100.30.

The 03:11:27 decision sees mid 100.345, trigger 100.30, stop 98.873, target 102.00, full upward continuity and gross reward:risk 1.124. Venue fill at 03:11:29.284 is 0.33 SOL at 100.30; fee $0.014298. The entry journal arrives at 03:11:31. This is a late far-side convention compared with reclaim, but the observed fill is not worse than the decision mid.

**During the hold.** The 03:12 minute is 100.29/100.41/100.25/100.38. At 03:26 it is 100.57/100.65/100.55/100.60. The target remains unfilled.

At 04:00, the fifteen-minute, hourly and four-hour opens coincide at 100.24. The daily open is 99.936. Three dots now share one boundary, but the daily boundary is still distinct. The 04:07 minute prints 99.967/99.971/99.920/99.920. The 04:08 minute trades 99.920/99.921/99.860/99.891.

**Exit.** The venue closes at 04:08:01.009 at 99.92, fee $0.014244. Journal reason: ftfc_flip. Gross loss $0.1254, about -0.3789%; net loss about $0.1539 including negligible funding. The daily boundary is only about 0.016% above the exit price. This is a near-boundary, coupled-open exit, not evidence of four independent adverse decisions.

**After exit.** At 08:41 the minute is 99.089/99.111/99.000/99.019; at 08:42 it is 99.019/99.050/98.869/98.953. The original 98.873 stop is touched before the 102 target. At the unchanged stop level, the extra gross price loss relative to the flip would have been about $0.3455 for 0.33 SOL; actual stop slippage is unknown.

| Tracker timestamp | Horizon | Favorable price after exit | Adverse price after exit | Reported rungs |
|---|---:|---:|---:|---|
| Sep 2 05:08:06 | 1h | 100.075 | 99.6775 | None |
| Sep 2 08:08:06 | 4h | 100.375 | 99.6115 | None |
| Sep 3 04:08:06 | 24h | 101.195 | 97.3585 | None |

Sources: hip3-executor/runs/2026-08-31_round2/decisions_r2.jsonl:8008; trades.jsonl:95-96; venue/fills.json:463,481; analysis.json:1579; tracker.jsonl:128,133,149; venue/htf_SOL_4h.json:1 and htf_SOL_15m.json:1, htf_SOL_1h.json:1, htf_SOL_1d.json:1; venue/candles_SOL.json:1, minute timestamps above.

**Reading:** Coupling weakens the interpretation of dot counts; it does not establish that the exit was harmful. Delaying all coupled-open flips would have delayed this useful loss exit. Keep a coupling-distance diagnostic before proposing a grace period.

### 5.2 TAO: the cost floor changes admission, not the exit

The setup, gate and fill are described in Finding 3. Minute detail:

| Sep 1 time | O/H/L/C | Meaning |
|---|---|---|
| 03:32 | 230.33 / 230.67 / 230.33 / 230.67 | Trigger 230.53 has already traded |
| 03:33 | 230.59 / 230.59 / 230.54 / 230.54 | Decision and actual entry minute |
| 03:34 | 230.72 / 230.89 / 230.71 / 230.89 | Initial favorable travel |
| 03:37 | 231.48 / 231.58 / 231.48 / 231.58 | Favorable price remains below target 232.57 |
| 04:13 | 230.33 / 230.33 / 230.33 / 230.33 | Losing most of the move |
| 04:14 | 230.15 / 230.23 / 229.69 / 229.69 | Full opposite stack; exit occurs within minute |
| 04:58 | 229.29 / 229.37 / 229.29 / 229.37 | Approaching original stop |
| 04:59 | 229.21 / 229.21 / 228.97 / 229.17 | First later touch of original stop 228.98 |

Venue entry: 03:33:15.661, 0.311 at 230.59, fee $0.03098. Journal entry: 03:33:18. Venue exit: 04:14:42.225, 229.85, fee $0.03088. Journal exit: 04:14:43, ftfc_flip. Gross trading loss $0.2301; approximately $0.0619 fees and $0.0009 funding produce net loss about $0.2929.

At 04:00, the 15m/1h/4h opens are 230.78 and the day open is 230.11. Price at the exit is below each. Again, a coupled-open exit also precedes the later stop.

Post-exit tracker:

| Timestamp | Horizon | Favorable price | Adverse price | Rungs |
|---|---:|---:|---:|---|
| Sep 1 05:14:43 | 1h | 230.385 | 229.060 | None |
| Sep 1 08:14:44 | 4h | 231.710 | 227.000 | None |
| Sep 2 04:14:47 | 24h | 231.710 | 215.605 | None |

Sources: hip3-executor/runs/2026-08-31_round2/decisions_r2.jsonl:2707; trades.jsonl:77-78; venue/fills.json:148,166; analysis.json:462; tracker.jsonl:108,110,126; venue/htf_TAO_1h.json:1; venue/candles_TAO.json:1.

**Reading:** The new gate would prevent this ticket before knowing the result. But the replay assigns this displaced ticket net -$0.3411, whereas the actual venue net is about -$0.2929. Keep modeled and actual numbers separate. This is cost geometry plus a sample outcome, not a demonstration that all such tickets should lose.

### 5.3 SPX: an invalidation exit after an already-invalid entry

**Setup.** September 2, 16:00 four-hour candle: 0.54312/0.55478/0.53001/0.53131. The 20:00 trap down-candle: 0.53200/0.53632/0.52377/0.53598.

**Order of breaks.** On September 3 at 00:37, a minute prints 0.52469/0.52469/0.51765/0.52218, below the trap low 0.52377. The 01:23 minute prints 0.53602/0.53634/0.53602/0.53634, above the trap high 0.53632. That candle alone cannot timestamp its high before the decision at 01:23:56. The decision mid independently records a quote above the trigger; the venue entry at 01:23:58.513 independently confirms a transaction above it. With the earlier low break established, the entry four-hour bar is Type 3 by the fill.

**Decision and entry.** At 01:23:56 the old-epoch gate nevertheless qualifies a 2D-2U long: mid 0.53645, trigger 0.53632, stop 0.52377, target 0.55478, upward continuity, gross reward:risk 1.446. Venue entry is 01:23:58.513: 39.4 units at 0.53634, fee $0.009128. The journal records entry at 01:24:00.

**Exit about nine seconds after the venue entry.** At 01:24:07.886, venue close fragments are 20.6 at 0.53604 and 18.8 at 0.53590, volume-weighted price 0.535973198. The venue-to-venue hold lasts 9.373 seconds; the journal timestamps are eight seconds apart. Fees total $0.009122. Journal exit at 01:24:08 is invalidation_type3 at rounded 0.53597. Exact venue gross loss is $0.014452; net loss is $0.032702 after $0.018250 fees and no funding. The journal computes gross loss $0.0146 from its rounded exit price, rather than rounding the exact venue gross result.

The full 01:24 minute has a high of 0.53950, whose within-minute timestamp is unknown. It may have occurred after the exit. The analysis reports about +0.589% MFE using the entire endpoint minute; that is an envelope bound, not a demonstrated favorable excursion during this nine-second hold. Source: hip3-executor/analysis/round2.py:185-195; round2/analysis.json:2264.

**After exit.** At 12:55 the minute is 0.55212/0.55330/0.55212/0.55329; 12:56 reaches 0.55489, touching the original target first.

| Timestamp | Horizon | Favorable price | Adverse price | Rungs |
|---|---:|---:|---:|---|
| Sep 3 02:24:11 | 1h | 0.54664 | 0.53496 | None |
| Sep 3 05:24:14 | 4h | 0.55002 | 0.52917 | None |
| Sep 4 01:24:09 | 24h | 0.61463 | 0.52533 | T1-T4 |

Sources: hip3-executor/runs/2026-08-31_round2/decisions_r2.jsonl:13292; trades.jsonl:105-106; venue/fills.json:638,656,673; analysis.json:2264; tracker.jsonl:146,153,172; venue/htf_SPX_4h.json:1; venue/candles_SPX.json:1, timestamps 1788395820000 and 1788398580000 for the two breaks.

**Reading:** The entry and exit rules were inconsistent in that epoch. The entry-invalidated gate was subsequently deployed September 4 at 15:08:14, so this is not evidence that it is still absent. The later target does not make the already-invalid entry coherent. It does show why post-exit favorable travel alone cannot adjudicate an exit: a new valid entry opportunity, its stop and its costs would need separate identification. Sources: executor analysis/replay/gates.py:204-209; tradingview-backtesting/docs/HANDOFF.md:357-370.

## 6. Appendix

### Appendix A - Severity-ranked code and operational findings

| Priority | Finding | Status and evidence |
|---|---|---|
| High | Stop-to-liquidation calculation omits maintenance margin | Current, production-gate and recorded-ticket reproductions; R1 |
| High | Malformed account response can become a flat receipt | Current conditional failure path, no observed live incidence; broker.py:148-160; R2 |
| High for research interpretation | Unattainable research control fills and dead halfway arm | Current model defects; Finding 2 and Appendix C |
| Medium | Invalidated HTF reversal can license a clean lower-TF continuation | Current helper ignores sponsor invalidation; rules.py:98-122,202-204; R8 |
| Medium | Stop-limit accepted as protective stop-market | Current defense gap, normal placement uses stop-market; broker.py:262-274; R3 |
| Medium | Retry after partial close can misstate gross trading proceeds | Current accounting gap while residual protection survives; broker.py:234-260; engine.py:605-635; R4 |
| Medium | Compound-inside Rev Strat shifts mother target | Deterministic source/spec counterexample; scanner strat_core.js:215,220; R20 |
| Low, historical artifact scope | Root Pine indicator leaks final HTF high/low into historical display | Timeframe_Continuity_Pinescript.pine:70-79; not shown to drive current executor or research receipts |

Recorded geometry screen, using cached asset metadata and initial isolated-margin assumptions:

| Round-2 ticket | Fill / stop | Selected and max leverage | Estimated liquidation | Implication |
|---|---|---:|---:|---|
| LITE short | 859.71 / 907.91 | 10 | 900.6486 | Stop beyond estimated liquidation |
| ACE short | 0.1965 / 0.2257 | 3 | 0.2245714 | Stop beyond estimated liquidation |
| NBIS long | 210.15 / 196.68 | 10 | 199.0895 | Stop beyond estimated liquidation |

Source: hip3-executor/runs/2026-08-31_round2/trades.jsonl:81,97,119; venue/meta.json:15-17 (ACE),1173-1175 (LITE),1221-1223 (NBIS). The same concern appears in weekend XMR short, entry 414.3, stop 467.44 at leverage/max 5, estimated liquidation 451.9636; weekend1 trades.jsonl:6. Actual collateral additions, funding and mark history could change exact historical liquidation, which is why the proposed receipt includes venue liquidationPx.

Important repairs already present: live emergency flatten bypasses scanner access; venue checks carry dex identity; residual closes retain tracking/protection; pending entry state directly prevents re-entry; stop checks include side, size, reduce-only and trigger attributes; leverage-confirmation issues are handled explicitly rather than silently ignored. Sources: executor engine.py:148-195,330-333,509-516,518-522,760-766,830-868; broker.py:140-142,250-259,262-280. The 1,144 passing tests and adverse-case review support these particular implemented paths, not unconditional safety. The remaining malformed-flat case attacks the reliability of the proof itself.

The equity change to spot USDC total is consistent with the dedicated account's documented abstraction and flat reconciliation. It should not silently become a universal equity formula for other account modes. Independent mark-to-market, transfers, fees and funding remain necessary when the account model changes. Source: hip3-executor/src/hip3_executor/broker.py:186-224; the round-3 scope is documented at tradingview-backtesting/docs/HANDOFF.md:179-188. The live account mode was not queried in this review.

### Appendix B - STRAT faithfulness, with disagreements left visible

**Classification and action timing.** Strict inequalities and closed setup bars are correctly implemented (scanner strat_core.js:9-14,150-164). A forming extreme remains broken even if current price recrosses; this is appropriate for scenario classification, while executable in-force must be current-price bounded. The executor generally does that latter check (rules.py:187-193). Calling all retained live signals currently in force is loose terminology. Neither a five-second poll nor delayed refetch enters at the exact first market print through a level.

**Continuity is not one universal stack.** Price versus each timeframe's own open is faithful (SKILL:268-285; scanner metrics.js:191-214). Unanimity itself is sourced: CORPUS/03 - Timeframe Continuity/03 - full-timeframe-continuity/article.md:9-12,76-82 describes four-of-four and horizon-specific stacks. The live 15m/1h/4h/1d set is a chosen hybrid, different from the research D/W/M gate and standard swing M/W/D/60. A fifteen-minute dot governing a daily position is a policy choice worth isolating, not a mathematical implementation of the same research strategy.

The skill's majority score is a quality measure, not permission to redefine FTFC (SKILL:308-319). Hour/day immediate control is separately sourced (SKILL:300-305; CORPUS/03 - Timeframe Continuity/05 - override/article.md:9-20). Full four-dot exit is an ATLAS management choice. The school's hourly-flip reduction is one profile, not a universal prohibition on full exits (SKILL:450-466; executor engine.py:502-506).

**Coupling.** Coincident opens are duplicated observations, SKILL:336-341 and CORPUS/03 - Timeframe Continuity/07 - uncoupling/article.md:9-14,185-197. Under an all-of predicate, counting duplicate identical boundaries once does not change the Boolean answer. Weighting dots therefore does not by itself repair near-open flipping. Log distance to the distinct binding opens and test any different exit rule separately. SOL supplies a concrete counterexample to automatically dismissing the coupled subset.

**Signals and time.** The corpus's exhaustion-risk article says a signal expires at its triggering-bar close (CORPUS/05 - Price Discovery & Broadening Formations/05 - exhaustion-risk/article.md:9-15). V4 explicitly chooses price-bounded validity and treats time remaining as quality (SKILL:273-279). The two are not identical. This report treats the local rulings as the mechanized contract and labels time exits as deviations from that contract.

**Stops.** The two min/max formulas should not be conflated:

- For 2U-1-2U, min(previous low, inside low) equals the previous low because the latter bar is inside. No discrepancy: scanner strat_core.js:199,205.
- For 3-2D-2U, the trap down-bar has broken the outside bar's low, so min chooses the trap's new low. Example outside high/low 110/90, then trap 105/85, then reversal: stop 85, whereas the v4 table says the outside low 90. Wider protection behind the failed move is structurally defensible, but it departs from SKILL:411; scanner strat_core.js:209,218.

**Targets can alter entry selection before they alter exits.** The same-color 3-1-2 continuation ignores an unfilled containing outside wick and uses a loaded pivot or 1.5-stop projection. Deterministic example: reference high/low 1007/1000; green outside 1010/995; inside 1008/998; decision 1008.1. Stop 995, served target 1027.5, structural wick target 1010. Gross reward:risk is 1.481 versus 0.145; at the main round-trip fee assumption, net ratios are about 1.33 versus 0.074. The convention can manufacture admission under the ratio filter. It is explicitly user-ruled in scanner comments, not an accusation of unauthorized coding. Sources: scanner strat_core.js:170-180,197,203; SKILL:27-31,388-393; CORPUS/02 - The 3 Scenarios/10 - 3-1-2/article.md:44-46.

The k=2 nearest loaded pivot is a reasonable mechanization, not a universal STRAT constant. Four-hour retention is still 12 bars by default, against hourly 30 and daily 220; increasing depth changes target availability and the admission distribution. Sources: scanner loop.js:33-49,391-403; strat_core.js:58-82. The 1.5-stop fallback is retired to legacy in v4; the specified measured move projects the previous leg (SKILL:377-391; CORPUS/02 - The 3 Scenarios/18 - measured-move/article.md:9-15). T2+ in the post-exit tracker is arithmetic projection, not higher-TF structure (executor engine.py:1033-1042).

**Mother ancestry.** A synthetic nested-inside sequence with original mother 115/95, then 110/100, then 109/101, trap down 108/99, forming reversal 109/101 emits target 110. The v4 retained mother target is 115. Extra inside bars should not silently redefine bar zero. This is an accepted longer ancestry being mislabeled through a shorter lookup, not merely omitted 2-1-1 coverage. Sources: scanner strat_core.js:215,220; SKILL:168-175. These invented bars are an explicitly labeled code counterexample, not fabricated historical market data.

**Coverage.** Ordinary 2-2 continuations are deliberately omitted; 1-1-2 is informational; MoMo is display-only; kicking and first-class 1-3-2 are not fully represented. A qualified 1-3-2 may become generic 3-2 and lose its mother-wick target. Sources: scanner strat_core.js:100-139,200-228; SKILL:186-205,222-245. A bounded rev-first universe is defensible for a mechanics trial. It cannot simultaneously promise participation in uninterrupted daily 2U-2U runners. Opening a new continuation ticket and managing an already-held continuation are different policies.

**The 1-3 convention.** Reclaim with a lower-TF actionable signal is the primary source treatment; far-side completion is a secondary late trigger (CORPUS/02 - The 3 Scenarios/07 - 1-bar-rev-strat/article.md:17-19; SKILL:177-182). Scanner chooses the latter with a first-break latch (strat_core.js:260-264; loop.js:441-459). Halfway by itself is not R19's complete entry prescription. Reclaim, midpoint and far side require separately coherent trigger, stop, target and observation rules. On one-minute OHLC, ambiguous break order must be bounded or excluded, never guessed.

**Invalidation and exit priority.** Entry-bar Type 3 invalidation and rev3 exemption match the stated live mechanism (executor engine.py:487-501; SKILL:443-448). Venue stop/target fills happen asynchronously; the software cannot guarantee an invalidation decision precedes a venue fill in real time. A deterministic replay priority is a convention, not control over event order on the exchange.

### Appendix C - Fidelity, research book and measurement

#### C1. Research control entry containment

I joined each fresh-window entry event by symbol and exact timestamp to its archived five-minute candle, requiring low <= fill <= high with only numerical tolerance. The rollup roster excludes xyz:DRAM, following tier_b_exits.py:422 and :639. No bars were missing.

| Fresh-window policy | Roster entries | Entries outside their candle range |
|---|---:|---:|
| Hourly breakout control (A0b) | 106 | 58 |
| Same control plus frozen ATR stop (A0bS) | 123 | 63 |
| Floored package, full T1 exit (D1) | 39 | 1 |
| Hourly adverse-state exit (S0a) | 492 | 81 |
| State exit plus full flip (S0b) | 492 | 82 |
| State exit plus BF harvest (S0c) | 549 | 115 |

Sources: tradingview-backtesting/analysis/paper/tier_b_exits/events_fresh_A0b.jsonl:1 and the corresponding named event files; analysis/paper/bars/*_5m.json:1. Counts concern recorded entry events, including positions open at the horizon, not just closed trades.

AAPL is concrete. At 10:30/10:35/10:40 on August 3, lows are 309.75/309.89/310.29. At 10:40 the control enters long at 308.591, with that minute's O/H/L/C 310.38/310.54/310.29/310.50. At 12:00 it records a BF exit at 311.9963855, gross +1.103527%. An illustrative entry at the 10:40 open 310.38 would give about gross +0.5208% for the same exit, before execution costs. That arithmetic is not a rerun: a causal gate/fill model can change stop placement, entry eligibility and later occupancy.

Source: tradingview-backtesting/analysis/paper/tier_b_exits/events_fresh_A0b.jsonl:1-2; analysis/paper/bars/xyz_AAPL_5m.json:1, bars at 1785753000,1785753300,1785753600. The entry path checks favorable high/low then assigns the old trigger (engine.py:761-785). It is called with current timestamps/OHLC; this is not a one-bar timestamp mismatch (engine.py:1464-1486).

Even the package is not wholly exempt: a SKHX short at 1060.4 occurs on a candle whose low is 1061.1. Source: events_fresh_D1.jsonl:57; bars/xyz_SKHX_5m.json:1, timestamp 1786040700. Separate this entry defect from the previously repaired target-containment issue.

The gate also uses the current five-minute close while the entry can be an earlier intrabar trigger. Until their ordering is modeled, historical agreement with Pine does not establish that the gate was aligned at the fill instant. Sources: engine.py:1378-1395,752-785. The largest control-family claims need the feasible-fill contrast in R6 before further economic interpretation.

#### C2. What the research receipts do and do not say

The gross research directions described in the dossier largely match the committed rollups: hourly control +104.8/+76.5 combined pp; stopped control +214.9/+111.1; floored full-T1 package +83.8/+28.4; same package plus structural/ATR stop +50.2/+20.0. These are additive position returns, not a constrained $100 account or executable live expectancy.

There are consequential qualifications:

- On the 39 shared closed July control identities, the ATR overlay gives gross +50.4555pp versus +34.2037pp. On the 24 fresh identities it gives gross +22.8695pp versus +25.7064pp, a negative gross difference of 2.8369pp. The matched benefit is not positive in both windows.
- The original full-T1 package still has a worst recorded adverse excursion of 14.9545%, and two structure-break exits sum to gross -21.6014pp. Saying it has no catastrophic-runner class is too categorical. A favorable aggregate comparison is not a reason to remove live protection.
- Bank-half-to-structure beats full-T1 on its shared closed subsets, yet loses whole-book; the more complicated 40/20/20/10-plus-runner profile loses the compared shared subsets. This supports testing components separately, not assuming either profile transfers to the executor.
- The 864-cell earlier sweep really does carry severe adverse tails everywhere: minimum worst-runner MAE 29.7831%, maximum 39.6253%. It is a stress characterization of that old machine, not a leverage instruction for the live structural-stop book.

Sources: tradingview-backtesting/analysis/paper/tier_b_exits/matched_entry_july.json:18-31; matched_entry_fresh.json:18-31; tier_b_t1floor/results_rollup.jsonl:1; tier_b_exits/results_rollup_july.jsonl:4-10; analysis/paper/sweeps/tvb19_tier_a/results_rollup.jsonl:1, field worst_runner.mae_pct across all 864 rows.

The fee-sensitivity prose is wrong. Under the existing linear fee accounting, scaling 0.0125% per-side fees to 0.1% per side multiplies the fee column by eight:

| Policy | July gross combined pp | July fees at 0.1%/side, pp | July net after those fees, pp | Fresh net after those fees, pp |
|---|---:|---:|---:|---:|
| Adverse hourly state exit | 195.2935 | 175.5000 | 19.7935 | -2.1601 |
| State exit plus full flip | 197.7361 | 175.7000 | 22.0361 | -0.9305 |
| State exit plus BF harvest | 291.4173 | 196.5000 | 94.9173 | 22.1242 |

These are net of modeled trading fees ONLY, with the same gross paths; funding, spread, slippage and the entry defects remain unpriced. The entire family does not turn negative. The current July BF/state receipt has 982 closed trades, not the stale 971. Sources: tradingview-backtesting/analysis/paper/tier_b_exits/results_rollup_july.jsonl:1-3; results_rollup_fresh.jsonl:14-16; docs/ARM_LEDGER.md:334-337. The paper 0.0125% per-side assumption is not interchangeable with current live dex-default or per-coin rates.

The matched research diagnostic intersects identities across every family member and then requires all to be closed (tier_b_exits.py:684-685). That is useful bookkeeping but a selected subset dependent on the compared family and window end. A pairwise comparison and an open-inclusive common-candidate exit diagnostic would expose different sensitivities; R19.

#### C3. The DRAM give-back fixture is real arithmetic, not a complete trading replay

The hand-labeled short enters at 65.88 on June 4 at 19:45 UTC. By June 6 at 02:30 the low is 52.788: gross MFE 19.8725%, reached 30.75 hours after the label. The June 14 06:45 exit label is 66.66: gross realized -1.1840%, gross give-back 21.0565pp and MAE 1.2098%. I recomputed these values.

Sources: tradingview-backtesting/analysis/giveback.py:35-73; analysis/reference/tvb13_dram_jun_15m_hl.json:1; tests/test_giveback_fixture.py:1-8,15-37. The test explicitly selects the last downward cross before the known bottom and the first later exit touch. It characterizes the owner's episode; it does not independently identify a strategy's causal entry/exit. Full-bar envelopes can include prices outside a real intrabar hold. The fixture motivates R11 without setting its fractions or forecasting its return.

#### C4. Replay amendments: reasonable explanations, narrower evidence

- **Roll freeze:** there is real scanner staleness after a bar expires. But each coin refreshes when its own response arrives; the served API does not wait to update every coin together. setCandles updates state/revision per response (scanner loop.js:425-438,492-500); expired forming candles freeze (:549-560); the server rebuilds on revision (server.js:289-295).
- **75-second-rank approximation:** fitted to served FTFC agreement on 10,094 near-roll rows, with best agreement 88.8%, and with per-coin sweep placement unmodeled. This is calibration after observing the ledger, targeted at an input agreement measure rather than net return. Source: executor runs/2026-09-04_replay1/PREREG.md:147-172.
- **Drift pin:** infers the BTC sign from the original first-refusal result. A later gate implies earlier gates passed. This is useful reconstruction but not an independently observed BTC tick. Source: PREREG.md:173-188.
- **Settle pin:** reads actual journaled exit time and reason to decide when a matched position releases its seat/cooldown, while keeping modeled prices for return calculations. Actual exit timing is an outcome. Source: PREREG.md:189-206; analysis/replay/__main__.py:219-242.

Thus "not selected to maximize profit" is supported by the declared method and inspected code. "All calibrated on served fields, never outcomes" is literally inaccurate for settlement. Historical author intent and every intermediate calibration choice cannot be certified from current files alone.

All 32 round-2 control positions are settlement-pinned. In the two declared quote/candle residuals, differences can be large: GOLD's modeled September 3 exit is 17:48 while ledger settlement is 18:28:45; PAXG's modeled September 4 exit is 00:08 while ledger settlement is September 3 at 23:37:38. Those create a book occupying a seat after its modeled exit or releasing it before that exit. At September 4 00:07, modeled holding intervals include NBIS, PAXG and VVV simultaneously, although the allocation state has only two seats. This is a dual-timeline model, not an observed live breach of the two-seat limit. Sources: hip3-executor/runs/2026-09-04_replay1/round2.json:25399,26599,26743; analysis/replay/allocator.py:300-311,365-370.

The advertised close timing bound must be read within the same-exit-reason comparison, not as a universal bound for all positions. P4 explicitly filters to matching exit reasons and does not gate the overall verdict (hip3-executor/analysis/replay/parity.py:548-569). The two residual examples therefore do not contradict its qualified worst-2.8-minute statistic.

The retained FAIL receipts and the independent reconstructed-input check are good practice. The pass still means a conditional reconstruction within declared tolerances, not an unpinned generative reproduction of every alternative. Keep the journal-conditioned reconstruction as a forensic tool and add unpinned bounds for strategy comparisons, R6/R19.

#### C5. Pine audit

All five executable request.security sites under pine/ use the confirmed-expression offset idiom: tvb_exp_bf_exit.pine:344; tvb_exp_champion.pine:381; winner_champion_mu15.pine:99; winner_generalizer.pine:101; winner_shortchamp_mu5.pine:107. The active locally aggregated control/package sources have no executable security request.

The separate root Timeframe_Continuity_Pinescript.pine is an indicator (line 2) and requests un-offset [open, high, low] with lookahead_on at lines 70-79. Historical high/low series can see the completed higher-timeframe range early. The open is a different case because it is known at period start. This is a historical display hazard; no evidence ties it to current executor decisions. The official [TradingView repainting guidance](https://www.tradingview.com/pine-script-docs/concepts/repainting/) confirms the offset-plus-lookahead convention. No current TradingView deployment or compiler behavior was checked.

### Appendix D - Selection, exits, regime and sizing

#### D1. Every gate has a different evidential status

| Gate or constraint | Structural reason / discretionary threshold | What the existing evidence supports |
|---|---|---|
| Universes and 1h/4h/1d, rev-first | Scope control; exact roster/horizons are configured | Useful bounded mechanics book, not all STRAT participation |
| Continuation sponsorship | Coherent higher premise; exact licensing is a policy | 0/12 observed wins does not identify whether license, target, entry timing or regime is responsible; R8/R15 |
| $1M daily volume | Liquidity proxy; threshold provisional | 8,612 first refusals in closed round 2. Not a spread/depth guarantee |
| xyz 09:30-16:00 ET | Operational session overlay | 6,358 first refusals; extended-hours replay mostly hits other gates. Not evidence that overnight liquidity is safe or worthless |
| Allow/block/readiness | Operator constraints and minimum data | Missing data should not be treated as negative opportunity evidence |
| Trigger/target geometry | Current price must still have a usable destination | Missed triggers, quote/print differences and actual fills can disagree |
| R:R floor | Gross threshold arbitrary; costs unavoidable | 3,515 first refusals; 69% wins with negative mean refers to an aligned simulated tiny-target pool, not tradable expectancy |
| Reach <= 1.5 daily ATR | Avoid targets far beyond observed travel; multiplier and daily clock provisional | Snapshot 22 refusals, 2 modeled winners, gross summed -60.9pp under bracket-first-touch assumptions. No justification to tune 1.5 from that set |
| Missing ATR | Cannot assess the reach contract | Snapshot gains dominated by a new listing do not justify failing open |
| Liquidation distance | Stop must be executable before liquidation | Current implementation incorrect; R1 |
| Four-dot alignment | Horizon-specific confirmation | Confirmation lag signs differ across ledgers; no stable threshold to select |
| BTC daily drift | Common-market stand-aside hypothesis | Snapshot median refused gross return -0.65%; removing veto changes dollar and pp signs across books. Not an instrument-specific regime detector |
| Kill/block/one position | Execution state and deliberate exposure scope | Operational constraints, not strategy-quality filters |
| Two seats | Portfolio exposure/capital constraint | Often occupied; five seats changes the book and costs. It does not show capacity is irrelevant |
| 60-minute cooldown | Avoid immediate recycle; exact duration configured | Too few first refusals to infer a good duration; applies equally to unlike signal horizons |
| Twelve entries/day | Turnover/exposure budget; threshold configured | Can shape future paths even when not the first observed refusal |
| Transition-only arming | Prevent repeat entries into one live episode | A setup refused once is not necessarily reconsidered when a seat frees or continuity aligns; this defines opportunity, not just deduplication |

Sources: hip3-executor/src/hip3_executor/rules.py:35-65,142-295; round2/ANALYSIS.md and decisions_r2.jsonl; tradingview-backtesting/docs/ARM_LEDGER.md:202-310. Snapshot counterfactual pool returns are GROSS unweighted sums/means at decision-mid bracket assumptions, with no seat competition; they are not net replacement portfolios.

Gate order does not merely distort a chart: it defines each reason's denominator. The closed 22,401-row funnel and the 28-closed-trade snapshot are different slices. Evaluating all gates on the same predecision state is needed to distinguish overlap, direct exclusion and capacity effects. Merely sorting current first reasons cannot recover those populations.

The research prior favoring a slow stand-aside layer is grounds for an a-priori hypothesis, not for copying a daily BTC sign into every coin. Own weekly or D/W/M bias, broad crypto market drift, and a metals/yields regime are different variables. Do not introduce them together. Per-coin weekly/DWM labels and own hour/day control can be shadowed before one future entry-rule contrast; R9/R17/R19.

#### D2. Late entry is not measured by fill-to-trigger distance alone

Signed favorable-direction fill-to-trigger gaps, paired from actual entries/exits:

| Ledger | Trades | Median gap | Largest gap | Exploratory relationship to gross trade return |
|---|---:|---:|---:|---|
| Weekend 1 | 34 | 0.04837% | 1.47256%, PURR | Larger-gap half averages gross -1.10534% versus -0.08477% |
| Round 2 | 32 | 0.04596% | 1.12961%, ATOM | Larger-gap half averages gross +0.97679% versus -0.46987% |

Sources: hip3-executor/runs/2026-08-22_weekend1/trades.jsonl:1; runs/2026-08-31_round2/trades.jsonl:70-134, paired by entry/exit. Median-half splits were computed solely as exploratory summaries, not proposed thresholds.

The signs disagree. Distance combines price travel, spread, timing, pattern geometry and which tickets survive all other gates. It is not a direct measure of scanner latency. Three round-2 and four weekend fills are behind the trigger despite qualifying decision mids. That warrants first-cross, decision, executable-quote and fill timestamps; it does not justify a tuned chase-distance cap.

#### D3. Sizing and correlated seats

For the FULL 32-trade round, 24 tickets have gross structural price risk between $0.45 and $0.56, not 21/32. The earlier 28-trade snapshot has 21. Full range is $0.0990-$1.4863; median $0.49785. Five tickets hit the minimum-notional clamp and three the maximum; 24 are unclamped, but the categories are not identical to the risk-band count. For example, HBAR is unclamped at about $0.568 risk.

Source: hip3-executor/runs/2026-08-31_round2/trades.jsonl:70-134, recorded size times absolute fill-stop distance. These are gross structural risk amounts, excluding fees, funding, stop slippage and liquidation.

Fixed planned risk is appropriate for the mechanics comparison. Scaling by whichever setup/timeframe looked best would add sample selection. If the minimum venue ticket cannot fit the intended risk, declining it is more coherent than silently raising risk; lower leverage changes required margin, not price-loss dollars at fixed size. Maximum-notional clamping legitimately under-risks some tight-stop tickets. R1 and R9 make those distinctions visible.

Two same-direction altcoin seats are not two independent bets. Report simultaneous same-direction exposure, common BTC dependence and aggregate booked stop risk before proposing more seats. The five-seat result is a constrained-book observation, not a general capacity conclusion. A4's unchanged result only says its implemented ordering did not bind in that grouped stream. R21 is deliberately conditional on observing actual competition.

#### D4. Flip protection and denominator corrections

Independent first-touch walks on cached one-minute bars, with original stops/targets and fixed analysis horizons:

| Slice | Flip exits | Later stop first | Later target first | Unresolved |
|---|---:|---:|---:|---:|
| Weekend 1 receipt | 15 | 14 | 0 | 1 |
| Round-2 Sep 4 04:57 snapshot | 18 | 12 | 1 | 5 |
| Round-2 closed Sep 4 17:13 horizon | 19 | 13 | 1 | 5 |

The older snapshots combine to 26/27 resolved, not 26/28. The fully closed-book comparison is 27/28 resolved, with six unresolved among 34 total flips. The dossier mixes the numerator and horizon. The round-2 snapshot gross saved travel versus original stops reproduces at +19.1897 summed pp; at the closed horizon it is +20.0780 gross summed pp. These are unweighted price-distance diagnostics, not net dollar gains from an alternative executed book.

Sources: hip3-executor/runs/2026-08-22_weekend1/analysis.json:1, flip rows and local candles; runs/2026-08-31_round2/trades.jsonl:70-134, analysis.json:1 and venue/candles_*.json:1. VVV resolves to its stop in the longer slice; the newly included NBIS flip remains unresolved. The first-touch convention cannot establish intraminute ordering in an ambiguous bar.

The evidence argues against removing the flip reflexively. The unobserved alternative has different fills, occupancy, funding and future entries. Conversely, it does not establish that every rapid near-open flip is necessary. R10 tests another question, stagnant holding time, while preserving current protection.

#### D5. Runner arms and targets

The walk-up arm (A6) loses on common tickets: round 2 net -$1.3021 across 14 common tickets, with only three changed; weekend net -$1.9437 across 26, with four changed. Its round-2 whole-book result is net -$1.5135 on 35 trades; only ten holds print a rung. Sources: replay1/round2.json:13406-13408,13651,13825-13828; weekend1.json:10018,10466,10633. The sign claim holds under the model.

This is a poor result for that precise all-timeframe combination of destination and walked stop. It does not test the owner's daily-only progression through 1h/2h/4h/8h/12h, and it does not isolate whether the destination or the stop hurts. R16 and R11 separate those ideas.

Bank-half at T1 plus a next-pivot runner and breakeven (A7) has slightly better whole-book round-2 net dollars but worse common-ticket net proceeds. It changes banking, runner destination and protection together. Calling it neutral is a rounded descriptive judgment, not a measured absence of effect. The dollar scale is small; price-model uncertainty and sequence changes matter.

T1 should first be structurally honest and knowable at entry. Timeframe, confluence and time remaining belong in the receipt before they become target-selection rules. A daily pivot that equals a weekly pivot is one obstacle with multiple provenance labels, not two independent targets. Synthetic tracker rungs cannot substitute for that ancestry.

#### D6. Session, carry and the owner's regime ideas

The actual full round-2 venue book sums to gross +$1.258545, minus trading fees $0.777120 and funding paid $0.225945, giving net +$0.255480. That rounds consistently with equity 99.60 to 99.86. The older 28-trade negative-net snapshot is a different endpoint. Sources: round2/venue/fills.json:1; funding.json:1; trades.jsonl:70-134.

ACE accounts for $0.206990 of funding paid, about 91.6% of the round's total. The carry problem is concentrated, not evidence that all multi-hour shorts are expensive. Funding sign depends on the actual rate and side. A per-entry forecast cannot substitute for the subsequently paid hourly cash. R18 keeps forecasts, clocks and cash separate.

The clock gate calls every xyz instrument underlying_closed outside US weekdays 09:30-16:00 and does not implement holidays (executor rules.py:35-45). Scanner bars remain 24/7 UTC. This is neither full equity-RTH STRAT implementation nor a venue requirement. School RTH rules also cover session-specific bar construction and end-of-session management (SKILL:476-482).

The proposed weekend, OPEX and Korea windows deserve explicit predeclared labels. They should not become exclusions because selected historical moves fit the story. Korean ordinary shares, US-listed Korea ETFs, oil, gold and FX have different reference markets. Likewise, high-volatility crypto can compress move duration without having an option's expiry or convex payoff. Volatility and funding may justify a priori horizon hypotheses; VIX or geopolitical narrative should not retroactively label favorable trades. No current macro-market forecast is asserted here.

#### D7. Weekend slippage residual

The two named cases account for most of the failed price reconciliation, but the decomposition is richer than the headline:

- PURR short: August 24 decision mid 0.133675 at 21:52:44; actual entry 0.13248 at 21:52:45.920, 0.89396% adverse. Actual kill close 0.13343 at 21:58:23.528 versus modeled 0.13312. Entry-price difference contributes gross $0.26768 and exit-price difference gross $0.06944 to replay optimism: gross $0.33712 combined.
- STX long: August 22 decision mid 0.20079 at 14:33:54; actual entry 0.20085. Structural stop 0.19518; actual stop fill 0.19313 at 15:04:30.268, 1.05031% through the level. Entry and stop-price differences total gross replay optimism about $0.31523.

Sources: hip3-executor/runs/2026-08-22_weekend1/decisions.jsonl:11905,10; venue/fills.json:41,7,1384,1333; replay1/parity_weekend1.json:546.

Combined gross optimism is about $0.65235, larger than the overall gross residual of approximately $0.6141 because other trades offset about $0.0383. The net residual is +$0.6136, exceeding the $0.50 tolerance by $0.1136; gross summed-price residual +2.0439pp exceeds the 1.5pp tolerance by 0.5439pp.

The attribution to adverse execution/price differences holds. Candles do not establish whether spread, depth, latency or another microstructure event caused each difference. Removing these cases from the test would remove the very failures a thin-book fill model must cover. Retaining the watermark is the honest treatment until a separately declared model is evaluated.

### Appendix E - Where the interpretation is most vulnerable

1. **Fee floor:** common tickets are unchanged. Direct rejection, downstream displacement and replacement gains are different contributions. The strongest structural case is arithmetic; the measured gain remains sample-local.
2. **Halfway arm:** zero entries is partly the output of an impossible predicate combination, not evidence about minute-close recrosses. Its candidate set is additionally conditioned on later far-side emission.
3. **Walk-up:** the negative common-ticket result holds, but only for the implemented horizons, target construction and stop path. It does not settle the daily-only idea.
4. **Flip counts:** preserve unresolved rows and the analysis horizon; 26/28 was a mixed-slice statement. Coupled does not mean useless, as SOL demonstrates.
5. **Weekend price gap:** the two cases explain more than the net residual, with offsets elsewhere. That does not make the remaining model an adequate thin-market fill model.
6. **Parity amendments:** actual exit time is outcome data. No evidence here establishes profit-maximizing calibration, but the blanket no-outcomes wording is inaccurate.
7. **Research ATR overlay:** positive common-ticket July difference becomes negative in the fresh window. The package retains a substantial adverse tail. A one-book result is not a universal stop prescription.
8. **Fee sensitivity:** the state-stop family does not all turn negative at 0.1% per side under the stated fee algebra.
9. **Capacity and ranking:** an unchanged higher-timeframe sort and a disappointing five-seat result do not establish that capacity/ranking are irrelevant.
10. **Near-perfect reproduction:** exact decisions partly reconstructed from original reasons and settlement are useful forensic agreement. Their exactness is not independent evidence that unobserved alternative paths are accurate.

The governing charter's distinction between exploration and selection is the right one. The practical weak point is the transition from "this is the spread we observed" to "this arm is the structural answer." Preregistration after a reject dig but before coding fixes implementation intent; it does not turn the same ledger into untouched data. Retained failed receipts and disclosed amendments are strengths, not reasons to stop interrogating what the pass means.

For the next experiment, separate three records: the historical behavior as actually traded, the corrected current implementation, and the one proposed increment. Freeze each version and never overwrite the earlier receipt. Keep a window-end position in the accounting rather than demanding every arm close the same subset. Do not use nominal trade count as independent sample size when coins share market/session conditions.

**Agreement with the 2026-08-14 assessment:** distinct temporal contracts, gate/fill causality, additive pp versus portfolio dollars, versioned evidence and durable execution state remain the right concerns. Sources: tradingview-backtesting/docs/strategy-implementation-assessment.md:325-491,730-760.

**Where I differ now:** the current scanner/executor separation and subsequent state-machine work reduce the case for a broad rewrite into a new universal kernel before obtaining the next useful measurement. Small, versioned repairs and better event receipts are more proportionate for this solo mechanics program. That older assessment also predates the second live ledger and many repaired failure paths. Its old live-readiness status should not be copied forward as if nothing changed. Conversely, current passing tests do not erase the specific remaining defects found here. Sources: that assessment :1122-1238,1506-1519; current executor paths and tests cited above.

### Appendix F - Reproducibility notes

- Arm decomposition: key positions by the receipt's entry identity; intersect control and arm; sum net differences for common positions; separately sum control-only and arm-only positions. Then distinguish direct net-floor failure from subsequent seat-path displacement using the original candidate and frozen cost assumption.
- Entry containment: join each entry event to exact symbol/timestamp five-minute OHLC; exclude the same parity symbol as the rollup; retain open entries; count low <= fill <= high failures; do not infer a corrected return from the count.
- Flip walk: begin after the real exit, hold the original stop/target fixed, use one named horizon, keep both-unhit cases, and disclose ambiguous same-minute ordering. Gross saved travel is not net executed profit.
- Risk: actual size times absolute entry-fill minus frozen-stop distance; report fees separately, do not replace the denominator with target distance or leverage.
- In-trade MFE/MAE and post-exit excursion are separate series. The live tracker starts at exit and uses sampled mids; it cannot reconstruct pre-exit MFE and does not count executable higher-TF pivot fills.
- Research fee sensitivity: keep the same gross paths and fractional fee sides, then apply the alternative declared rate. No slippage/funding conclusion follows from that subtraction.
- Historical artifacts may retain older diagnostic counters by design. For example, corrected executable collision counts are documented while old rollups await regeneration (tradingview-backtesting/docs/experiments/tvb25_exit_round_report.md:211-240). Do not rewrite them merely to make a review look consistent.

## 7. Suggested next review prompt

"Review the response to this deep dive against the same three pinned repositories. First independently reproduce liquidation clearance, malformed-account flatness, halfway equality/future-conditioned candidate generation, research entry containment, invalid higher-timeframe sponsorship, stop type and partial-close accounting. For each accepted repair, inspect a minimal diff and adversarial receipt; preserve old ledgers and results. Distinguish fixed implementation, changed methodology and unchanged limitations.

Then review ONE preregistered no-progress exit against the corrected, frozen round-3 control: two signal-bar lengths since fill and less than 0.5 original R of observed progress, with original size, target, invalidation, structural stop and flip unchanged. Require contemporaneous excursion observations, feasible fills, signed funding, a fixed non-overlapping window, direct/common/complement trade accounting, and three timestamped real-trade walkthroughs. Report what would falsify the proposal; do not select another arm or make the owner's deployment decision."
