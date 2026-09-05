# Strategy deep-dive review prompt (2026-09-05, before round 3 goes live)

Delivery note (for the owner; not part of the prompt):

- Written for an external frontier-model reviewer (Codex / GPT-6 Astra) run
  through the LOCAL transport, i.e. with read access to all three repos on
  this machine. If it is pasted into a web UI without file access, the
  dossier in section 2 is self-contained enough to review from, and the
  reviewer is told to say what it could not verify.
- Copy everything between BEGIN PROMPT and END PROMPT. Nothing in it names
  a secret; keep it that way if you edit it (public repo).
- The reviewer's output lands at `docs/reviews/deep-dive-2026-09-05-astra.md`
  (a new review kind, not tied to a TVB session number). The next session
  writes the critical synthesis into HANDOFF, per the review protocol.
- Nothing is modified by this review. Round 3 stays built-not-deployed until
  you say go, whatever the review says.

---------------------------------------------------------------- BEGIN PROMPT

# Deep-dive review: the STRAT / timeframe-continuity trading program

You are an independent frontier-model reviewer. You have READ access to
three sibling repositories on this machine and to one methodology file.
Your job is a complete, adversarial, constructive review of a trading
strategy research program that is about to start its third live
micro-capital round. The owner asked, verbatim:

> go over every aspect of the strategy, how it compares to the data, how
> faithful it is to strat, and any recommendations and modifications it
> would make itself to improve the strategy -- even if a slight deviation
> from strat. This would include but not limited to candidate selection,
> target criteria, MFE/MAE/ATR based exit mechanics, literally anything
> else you can think of. Obviously nothing would be modified, this is a
> deep dive of everything we have done so far.

Take that literally. Nothing you write changes anything; the owner
decides. But the owner is a solo operator who reads every word, so rank
what matters, lead with it, and keep the rest as an appendix.

## 1. Ground rules (binding)

1. READ-ONLY. Do not edit, create, commit, push, deploy, or delete anything
   inside the repositories. Do not touch `data/KILL_FLAT` anywhere; do not
   start, stop, or restart any process; do not SSH anywhere. You may run
   read-only commands (`git log`, `git show`, tests) and your own analysis
   scripts, provided they write only to a scratch directory OUTSIDE the
   repositories. The replay harness subcommands `parity`, `run`, `report`
   overwrite committed receipts: do not run them; read the committed JSON
   and Markdown receipts instead, or import the harness modules from a
   scratch script. (`fetch` writes only gitignored candle caches and may
   be run if a cache is missing, but prefer the committed receipts.)
2. SECRETS. Your output will be committed to a PUBLIC repository. Never
   paste the VPS IP, the master wallet address (it appears in the private
   executor repo's ledger READMEs), API keys, or the scanner URL. Cite
   `file:line` instead.
3. EPISTEMIC CONTRACT (from the governing charter; it binds you too):
   - Generating data is not selecting on it. Reading the spread across
     arms is exploration; picking the top arm and calling it the answer is
     the overfit.
   - Ablation, never a tournament. A change earns a place by beating the
     control directly below it in a named ladder, one change at a time.
   - Navigate by the structural-vs-sample gradient. A parameter set for a
     structural reason generalizes; the same form tuned because it scored
     best on the sample does not. Say which kind each of your
     recommendations is.
   - Extreme metrics are questions, not verdicts.
   - The two live ledgers are 34 and 32 trades. Every P&L number is
     characterization. Do not write "validated", "proven", or "edge".
   - You MAY recommend deviations from STRAT. Label every one of them as
     a deviation, name the rule it deviates from, and give the structural
     reason.
4. OUTPUT DISCIPLINE (owner's standing requests): plain ASCII, no emojis;
   trader language first, code terms second; no bare arm codes without the
   plain-words meaning; state gross vs net on every fee or P&L claim; for
   every key claim give at least one concrete bar-by-bar walkthrough from
   the ledgers (the owner cannot visualize a trade from an abstraction);
   cite `file:line` for every code claim.

## 2. The dossier (what the system is; verify against the files)

### 2.1 Architecture, one paragraph

Detection lives in the scanner (`hip3-scanner`, Node, deployed on
Railway): it classifies bars and emits STRAT setups per coin per
timeframe and serves them as JSON (`/api/state`). The live executor
(`hip3-executor`, Python, runs on a VPS from a dedicated wallet, ~$100)
polls that state every 5 s, runs a fixed gate order over each live signal,
enters at market, rests a venue stop and take-profit, and manages exits in
software. It NEVER analyzes bars. The research repo
(`tradingview-backtesting`) holds the charter, the ledger of every arm in
plain terms, the research-book results (a TradingView `strategy()` family
and its Python replay twin, July 2026 window plus a fresh Aug 3-16
window), the session log (TVB-1 .. TVB-33), and every external audit so
far. The methodology spec is the strat-methodology skill file (v4,
rulings R1-R24), plus a local corpus of the STRAT source material.

Venue: Hyperliquid perps. Two universes: main-dex crypto perps ("perps")
and the xyz HIP-3 equity/commodity/index perps ("xyz", oracle-priced off
an underlying that closes). 24/7, day rolls 00:00 UTC.

### 2.2 Detection (scanner STRAT-CORE, `src/strat_core.js`)

- Bar classification (`classify`, line 9): strict inequalities, Type 1 /
  2U / 2D / 3 from the prior bar's high/low. Setups are built from CLOSED
  bars; the FORMING bar is classified live (`analyzeTF`, line 150).
- Retained depth per timeframe (`src/loop.js` line 33 ff.): 15m 40 bars,
  1h 30, 4h shallow (12 at the design session; a bump to 40 is a deferred
  PR), 1d 220. Weekly and monthly bars are aggregated from dailies on the
  calendar (`aggregateBars`, line 294) because the venue's native weekly
  is Thursday-aligned.
- Setups emitted (line 150-245), with trigger / stop / target:
  - After an inside bar: 3-1-2U/D (reversal, or CONTINUATION when the 3's
    close color matches the break), 2D-1-2U and 2U-1-2D (reversal;
    target = bar 0's wick; stop = bar 0's opposite extreme), 2U-1-2U and
    2D-1-2D (continuation; stop = the lower of both bars' lows; target =
    near-bank pivot), 1-1-2 and ?-1-2 as info only.
  - After a 2: 2D-2U and 2U-2D reversals (stop = the trap 2's extreme,
    target = the prior 2's wick), 3-2D-2U / 3-2U-2D (stop = min/max of
    both bars, target = the 3's wick), 1-2-2 Rev Strat (target = bar 0's
    wick). 2-2 continuations are omitted BY DESIGN (position management).
  - After a 3: 3-2U and 3-2D with the pivot-ladder T1 (`pivotTarget`,
    line 64: nearest k=2 swing pivot beyond the trigger on the loaded
    bars) else a 1.5x-stop-distance measured move.
  - PMG at a run of >= 5 (target = the previous chain rung).
  - MoMo hammer/shooter is display-only; kicking patterns and 2-1-1 and
    1-3-2 are not emitted.
- LIVE = the forming bar's extreme is strictly past a setup's trigger
  (line 245-249), monotonic. `invalidated` = the forming bar is Type 3
  while something is live (line 251).
- 1-3 Rev Strat (line 258-265): path-dependent via the tracker's
  first-break latch; entry = the inside bar's OTHER side (the far side,
  where the 3 completes), stop = the inside bar's first-broken extreme,
  target = bar 0's wick, `rev3: true` exempts it from invalidation. The
  skill's pattern table says "reclaim of broken side" (R22) and its 50%
  rule (R19) describes the halfway line; three conventions exist and
  none has a receipt with entries in it (see A5 below).
- Continuity (`src/metrics.js` `coinSummary` line 191): `ftfc` = "up" or
  "down" only when the FORMING bar's close-vs-open direction agrees on
  ALL of 15m, 1h, 4h, 1d; else "mixed". `dwmContinuity` (line 232):
  the same predicate on 1d / 1w / 1M, served but not used by the live
  executor (arm A3 would use it).
- Serving artifact that matters: after a bar rolls, the scanner FREEZES
  that timeframe's served values until one full-universe refetch sweep
  completes (~75 s per timeframe rank; `src/loop.js` lines 548-560 and
  617-655). The replay had to model this to reproduce the live book.

### 2.3 Execution (hip3-executor, Ruleset v1 as it traded round 2, plus the round-3 delta)

Read `README.md` sections "Ruleset v0", "Ruleset v1", "Ruleset v2
(PREREG)", "Round 3 config", and the "Round-2 pre-live gate". Config as
of round 3: `config.json` (no secrets in it).

- Consumes signal timeframes 1h / 4h / 1d; signal kinds `rev` only;
  continuations are admitted only under the ESCALATE license: a higher
  timeframe (up through 1w / 1M) holds a live, in-force reversal in the
  same direction (`rules.htf_reversal_backing`, line 98). Cumulative
  record of that license: 0 wins in 12 continuation trades.
- Entry is TRANSITION-based: only on the poll where the signal became
  live, one entry per signal per bar; at market at the decision mid.
- Gate order (`rules.evaluate`, line 142-293; the journal reason is the
  first gate that refuses): universe_excluded, underlying_closed (xyz
  outside 09:30-16:00 ET weekdays), bad_direction, no_htf_reversal /
  kind_not_tradeable, coin_not_ready, not_on_allow_list, blocked,
  below_volume_floor ($1M 24h notional), missing_price,
  no_structural_stop, not_beyond_trigger, target_already_reached,
  entry_bar_invalidated (the entry bar is already Type 3; 1-3 exempt),
  stop_wrong_side, fee_rate_unavailable / reward_risk_below_floor
  (round 3: NET of round-trip fees, dex-default rates main 0.0864% /
  xyz 0.0746% of notional; round 2 was gross), reach_unavailable /
  target_beyond_reach (target farther than 1.5x the coin's daily ATR,
  fail-closed on missing ATR), stop_outside_liq_distance (stop must sit
  inside 80% of the isolated liquidation distance), ftfc_not_aligned
  (the four-timeframe stack must agree with the direction),
  counter_drift (crypto only: no longs while BTC is below its 00:00 UTC
  open, no shorts while above), kill_switch, entry_blocked,
  already_in_position, no_slot_free (2 seats), cooldown (60 min per
  coin), day_cap_reached (12 per UTC day).
- Sizing: risk-normalized, $0.50 per ticket = $0.50 / stop distance,
  clamped to $10-$100 notional, 10x isolated (venue max if lower);
  booked risk receipted per entry, risk drift above 1.5x warns, never
  auto-closes.
- Exits, in priority (`engine._exit_reason`, line 487; `_software_exits`):
  (1) invalidation_type3: the entry bar itself becomes Type 3 while still
  forming -> market out before the stop (1-3 exempt); (2) the venue
  stop-market at the structural stop; (3) ftfc_flip: all four of
  15m/1h/4h/1d turn against the position -> market out (holds through
  "mixed"); (4) reduce-only limit at the target, full exit. Plus
  KILL_FLAT (owner interlock file). No time stop, no trailing stop, no
  breakeven, no partials.
- Post-exit tracker (`engine._start_tracker` / `_update_trackers`, line
  1033-1102): 24 h after every exit, peak favorable / adverse excursion
  from mids and which rungs T1..T4 (target + k x |target - trigger|)
  printed, journaled at 1 h / 4 h / 24 h. Diagnostic only.
- Round 3 delta (built, tested, NOT deployed): the fee-aware floor above;
  shadows on every decision row (`rr_net`, `fee_rt_pct`, per-coin rate,
  `dwm`, `poll`, `funding_rate`) and an expected-funding receipt per
  entry; equity display = spot USDC total; startup row journals `arms`.

### 2.4 The two closed live ledgers (private repo, `runs/`)

| Ledger | Rules | Window (UTC) | Trades | Result | Exits |
|---|---|---|---|---|---|
| Weekend 1 `runs/2026-08-22_weekend1/` | v0: fixed $30 notional, no drift veto, no reach gate, no xyz, R:R floor only from 15:35Z | Sat 08-22 14:26 -> Mon 08-24 21:58 | 34 (9 wins) | gross -$6.04; account 52.60 -> 45.75 USDC | 15 ftfc_flip / 8 stop / 5 target / 4 unknown (venue says 3 target + 1 stop) / 2 kill_flat |
| Round 2 `runs/2026-08-31_round2/` | v1 (section 2.3, gross floor) | Mon 08-31 15:37 -> Fri 09-04 17:13 | 32 (11 wins) | journal gross +$1.26; equity 99.60 -> 99.86 (+$0.26 net all-in); at the 04:57Z snapshot 28 closed: gross +$0.13, fees $0.73, funding $0.23, net -$0.82 | 19 ftfc_flip / 5 target / 4 invalidation_type3 / 2 stop / 2 kill_flat |

Each ledger directory holds `decisions*.jsonl` (every candidate and its
verdict; round 2 = 22,401 rows), `trades.jsonl`, `tracker.jsonl`,
`state.json`, `venue/` (fills, funding, ledger updates = ground truth;
1m candle caches gitignored), and an `ANALYSIS.md` + `analysis.json`
(dual-language findings, census tables, defects, open questions). Books
reconcile to the venue to the cent on both.

Round-2 funnel (closed slice, journal reasons): below_volume_floor 8,612;
underlying_closed 6,358; reward_risk_below_floor 3,515; no_htf_reversal
1,615; not_beyond_trigger 813; ftfc_not_aligned 508; no_slot_free 391;
target_already_reached 341; counter_drift 87; coin_not_ready 54;
qualified 32; reach_unavailable 26; target_beyond_reach 26;
already_in_position 11; entry_bar_invalidated 6; stop_outside_liq 4;
cooldown 2. Note the ORDER: a row's reason is the first refusing gate, so
every "pool" census is conditional on the gates above it.

Round-2 gate census (from the 04:57Z live snapshot in `ANALYSIS.md`, 28
closed trades; the closed slice above is slightly larger; refused setups
simulated at decision mid, bracket first-touch on 1m candles, stop-first,
no seat competition; upper-bound counterfactuals): reach gate refused 22, 2 winners, sum -60.9pp; missing
ATR refused 24 (new listings), +94pp driven by one coin; drift veto
refused 72, mean +0.15%, median -0.65%, positive only through eight
trades; bell refused 2,491 aligned xyz rows, zero-mean; R:R floor refused
1,524 aligned rows, 69% sim winners with a negative mean (the tiny-target
class). Weekend-1's headline: the continuity-flip exit avoided further
loss on 14 of 15; round 2: 12 of the 13 resolved flips hit the stop first
(+19.2pp saved vs riding to the stop), but 9 of 18 flips fired within
60 min of a 4h/1d open, where every timeframe re-opens at one price and a
single tick flips the whole stack (the "coupled opens" quirk).

### 2.5 The ledger replay and the nine receipted arms (private repo, `runs/2026-09-04_replay1/`)

`analysis/replay/` re-runs the executor's rules over venue 1m candles and
the served scanner state; a parity gate (P0-P6) must PASS before any arm
is read. Round 2: PASS -- 22,401/22,401 decision rows agree, 32/32
entries, 30/32 exit reasons (2 in a declared residual class), timing
median 0.4 min, P&L within +$0.44 / +0.42pp. It took THREE fidelity
amendments after FAILs, each calibrated on served fields or journaled
facts, never on outcomes (the roll freeze, a drift-sign pin read from the
live refusal, and matched trades settling at the journaled instant); the
FAIL receipts are kept. Weekend 1: entries 34/34, exit reasons 33/34,
but P5 FAILS by $0.11 (two thin weekend fills: PURR entry 0.9% worse than
the decision mid, STX stop 1.05% through the level) -- its arm numbers
are WATERMARKED and contrasted against a v1 replay control (-$2.16 on
27), not the v0 book that traded.

Replay control card, round 2: 32 trades, net +$0.70, +8.5pp, 44%
winners, max drawdown $1.43, both seats busy 95% of the window, median
hold 3.7 h.

| Arm (one change each) | Round 2 (PASS) | Weekend 1 (watermarked) | Reading given to the owner |
|---|---|---|---|
| A1 xyz extended hours 04:00-20:00 ET | 36 trades, +$0.75 vs +$0.70; only ONE bell-refused row ever became a trade | identical | oil/CRCL die at the R:R floor, not the bell |
| A2 no BTC drift veto | 41 trades, +$1.20 but -4.1pp | -$3.10 vs -$2.16 | sign flips between ledgers |
| A3 continuations licensed by own D/W/M continuity | +$1.26, 36 trades | -$2.01 vs -$2.16 | small positive both, inside noise |
| A4 higher timeframe first within a poll | IDENTICAL (never bound) | 2 swaps, -$2.73 | inert |
| A5 1-3 at the halfway line | +$0.36 with ZERO halfway entries (875 candidates: 359 volume, 248 bell, 268 no longer beyond the line at the cross minute's close) | identical | "far-side 1-3 removed", not "halfway added" |
| A6 walk-up runner (TP at the ladder's last rung, stop walks one rung behind) | -$1.51; matched trades gave back $1.30; 10 of 35 holds printed a rung | -$3.83; matched -$1.94 | negative on both axes, both ledgers |
| A7 bank half at T1, rest to next pivot, BE stop | +$0.82; matched -$0.48; best drawdown $1.10 | -$2.21; matched -$0.33 | neutral on shared trades |
| A8 five seats | 55 trades, -$0.14, +15.2pp; seats 46% busy | -$1.83 | seats are not the constraint |
| A9 net-of-fees R:R floor | +$3.30, drawdown $0.94; 21 matched identical; 11 displaced had netted -$1.61; 11 admitted +$0.99 | -$0.36 vs -$2.16; 7 displaced -$1.64 | a filter that removes fee-dominated losers |

Owner ruling (2026-09-05): round 3 = v1 + A9 live, nothing else; all
other arms shadow-journaled. Claude's stated reasoning: A9 is the only
arm positive on both ledgers AND on matched trades, and its gain is what
it refuses (a cost-accounting identity that would hold even if the
numbers were flat), so it is the most structural of the nine. Judge that
reasoning yourself (section 4.9) -- and note that the arms were DESIGNED
after a reject dig on round 2 and then receipted on round 2.

### 2.6 The research book (public repo; a different machine, different units)

A TradingView `strategy()` family and its Python replay twin
(`analysis/paper/engine.py`) on 5m Hyperliquid bars, one position per
symbol, gate = price on the same side of the Daily, Weekly AND Monthly
opens. Numbers are gross combined percentage points, July window / fresh
Aug 3-16 window. Read `docs/ARM_LEDGER.md` first; it is the plain-terms
card of every arm. Headlines you should know before you start:

- Control A0b (break of the prior hour's extreme, exits = broadening-
  formation harvest touch + level break + D/W/M flip): +104.8 / +76.5;
  can sit in a loser for days (July max drawdown 122pp).
- A0bS (A0b + a stop 3x hourly ATR frozen at fill): +214.9 / +111.1,
  drawdown roughly halved; the stops themselves LOSE -180pp over 60
  stop-outs; the win is amputating catastrophic runners and handing the
  bullet back. The only overlay so far that also wins per matched trade.
- State-stop family S0a/S0b/S0c: +195 to +291 whole-arm on 870-970
  trades, WORSE per shared trade than A0b; the gain is reload speed.
  Fees at the real taker tier (~1.25 bp/side) cost ~24pp; at the 0.1%
  assumption from early rounds the whole family flips negative.
- Package family (ten pre-committed STRAT setups on the 1h, with a
  minimum-target floor, a harvest-proximity veto and a chop veto): raw
  patterns A1 -7.7 / +11.2; the floor alone flips it positive (A1F);
  D1 (floored, full exit at T1) +83.8 / +28.4 is the package comparator;
  deeper rungs D2-D5 earn more per matched trade but hold the bullet
  longer; D1S (D1 + the same ATR/structural stop) +50.2 / +20.0 -- the
  stop that was medicine on the control book is a tax on the floored
  book; P1 (bank half at T1) beats D1 per matched trade and loses
  whole-arm through occupancy; P2 (the owner's own 40/20/20/10 + runner
  profile) loses both ways; X1 (harvest only after rung 3) -37.8 with the
  worst drawdown.
- Earlier arcs (archived HANDOFF, `docs/session_archive/`): TVB-1 churn
  finding (a 60/30/15 stack at 15m lost 81% via churn, PF 0.645 with a
  0.1% fee vs 1.28 without; the M/W/D/60 stack ~9x fewer trades, PF
  1.13 net); TVB-2/3 real xyz taker fee ~0.01% (10x below the assumed
  0.1%); TVB-4/5 a slow M/W/D regime layer as stand-aside flipped a
  losing control from -8.6% to +40.3% and contained damage everywhere
  tested, and faster regime clocks were monotone-destructive; TVB-9
  144-run breadth sweep: edge only in high-vol trend regimes, a dead
  zone that is signal-structural, short whipsaw as the damage signature;
  TVB-10 flip-stop rides regimes while a state-stop harvests slices;
  TVB-13 exits on winners = THE problem (a DRAM short +20% round-tripped
  to -1.2% through seven daily rungs); TVB-16/18 paper week: a
  config-invariant adverse-runner exit gap (three shorts rode ~49 h);
  TVB-19 clock census (31% gate disagreement UTC vs RTH) and an 864-cell
  Tier A sweep with a 29.8-39.6% MAE tail in EVERY cell; TVB-21/22 the
  born-beyond mechanism (one-sided target predicates booked impossible
  fills; fixed by containment); TVB-23 the T1 floor repairs the package
  but the control still leads; TVB-25 the exit round (ladder bottom,
  ATR stop, thesis exits all lose to D1, collision census).
- `docs/strategy-implementation-assessment.md` (2026-08-14) is a prior
  independent assessment; do not anchor on it, but do say where you
  agree and disagree.

### 2.7 The owner's own open ideas and standing beliefs (respond to them)

- Timeframe walk-up for daily-pattern targets (1h -> 2h -> 4h -> 8h ->
  12h); daily 2U-2U-2U runners are invisible to the rev-only universe;
  second-guessing the BTC veto and the RTH-only xyz clock in the current
  overnight / geopolitical regime; metals / yields regime identification
  later; trade visualization is still owed.
- Leverage philosophy: isolated margin is a defined-risk premium; the
  loss limit comes before the liquidation; argue from MAE clearance, not
  from drawdown x leverage. Live capital is deliberately tiny; the
  product under test is MECHANICS, not P&L.
- High-vol crypto perps may behave like options under high VIX (time
  compression) -> minimal continuity may be instrument- or regime-
  dependent; a-priori variant only.
- Named dead zones (a-priori): Fri 6pm -> Sun 6pm ET on HIP-3 perps;
  Friday late-day OPEX pinning; the Korea session cluster (18:00-20:00
  ET) for DRAM / EWY / SMSN / SKHYNIX.
- Open rulings right now: the weekend-1 P5 slippage question; the halfway
  1-3 in-force convention (D4); the 1-3 trigger convention itself.

## 3. Where everything lives (read in this order)

Repos (all on this machine; the first is PUBLIC on GitHub, the other two
PRIVATE):

1. `C:\Strat_Trading_Bot\tradingview-backtesting` (HEAD 7ad92f4):
   `CLAUDE.md`; `docs/ATLAS_Timeframe_Continuity_Charter.md` (Section 0
   first); `docs/ARM_LEDGER.md`; `docs/HANDOFF.md` (TVB-27 .. TVB-33 =
   the live arc; older sessions in `docs/session_archive/`);
   `docs/experiments/` (every prereg and report; `tvb33_round3_prereg.md`
   is the current one); `docs/reviews/` (every prior external audit,
   `tvb1` .. `tvb30`); `analysis/paper/engine.py` and the tier runners
   (the Python twin); `pine/` (the strategy() mirrors and indicators;
   audit `request.security` usage: the approved idiom is `expr[1]` +
   `lookahead_on`, un-offset `lookahead_on` is the trap);
   `analysis/giveback.py`, `analysis/trade_mae.py`,
   `analysis/paper/round_census.py`, `analysis/paper/ladder_census.py`
   (MFE / MAE / give-back / ladder receipts); `docs/thestrat_ai/` (LOCAL
   ONLY, gitignored: the STRAT source corpus, eight chapters).
2. `C:\Strat_Trading_Bot\hip3-executor` (HEAD d8a07b0 on main):
   `README.md`; `config.json`; `src/hip3_executor/{rules,engine,broker,
   config}.py`; `runs/2026-08-22_weekend1/` and `runs/2026-08-31_round2/`
   (ledgers + `ANALYSIS.md`); `analysis/replay/` (harness; `CONTRACT.md`
   is the build contract); `runs/2026-09-04_replay1/` (`PREREG.md` with
   dated amendments b-i, `REPLAY.md`, `parity_*.json` including the kept
   FAIL receipts, `round2.json`, `weekend1.json`); `tests/` (1,144).
3. `C:\Strat_Trading_Bot\hip3-scanner` (HEAD 62adc75): `src/strat_core.js`
   (extracted verbatim from the dashboard's STRAT-CORE block; `npm run
   extract:check` is the drift gate), `src/loop.js`, `src/metrics.js`,
   `src/apistate.js`, `src/rules.js` (the alert rule engine),
   `parity/reference.py` (an independent Python port used for parity).
4. Methodology: `C:\Users\Chris\.claude\skills\strat-methodology\SKILL.md`
   (v4; section 1 invariants, section 3 patterns, section 4 continuity,
   section 5 targets / stops / exits, section 7 test vectors). It is the
   project's MECHANIZED spec and is itself under refinement; where it and
   the STRAT corpus (or your own knowledge of Rob Smith's method)
   disagree, say so explicitly rather than picking one silently.

Read-only verification commands:

```
cd C:\Strat_Trading_Bot\hip3-executor          && uv run pytest -q -p no:cacheprovider
cd C:\Strat_Trading_Bot\tradingview-backtesting && uv run pytest tests/ -q
cd C:\Strat_Trading_Bot\hip3-scanner            && node --test && npm run extract:check
```

## 4. Review dimensions (cover every one; add your own)

For each dimension: what the system does (cite), what the data says
about it (cite the ledger, census or research receipt), how faithful it
is to STRAT (skill section and corpus chapter), and what you would
change. Seeds below are things a first read turned up; go beyond them.

### 4.1 STRAT faithfulness of the detection and gating layer

- Classification and triggers: strict breaks, monotonic live state,
  setup bars closed, forming bar live (skill invariants 1-3, 6). Does the
  executor's entry instant honor "a bar is a 2U the instant price trades
  through the prior high"? It enters at the decision MID on a 5 s poll
  after a scanner sweep that can take ~75 s per timeframe; there is no
  cap on how far past the trigger price may already be (only
  `not_beyond_trigger`, `target_already_reached`, and the R:R floor,
  which shrinks as price runs). Is a late-entry tax visible in the
  ledgers (entry vs trigger distance vs outcome)?
- Which continuity? The executor gates AND exits on the four INTRADAY
  forming-bar directions (15m/1h/4h/1d, all required), while the
  charter, the research book and the skill's bias predicate speak of the
  Daily / Weekly / Monthly opens, and the skill (4.1) insists bias, live
  scenario and signal-in-force are three predicates never merged. Is a
  15m dot a legitimate gate or exit input for a daily signal? Is
  requiring all four "full timeframe continuity" in Rob Smith's sense?
  Is the full-stack flip exit (skill 4.5: a 60-minute flip against =
  reduce, not exit) faithful, and how much of its observed value is the
  coupled-open artifact?
- Setup coverage: which canonical setups are emitted, which are omitted
  (2-2 continuation by design, 2-1-1, 1-3-2, kicking, MoMo as display
  only), and whether the omissions are defensible for a universe that is
  traded rev-only with an escalate license for continuations.
- Stops: the scanner's structural table vs skill 5.2 (X-1-2 stop = bar
  0's extreme, not the inside bar; 2-2 = the trap bar; 3-2 = the outside
  bar). Check the 2U-1-2U continuation stop (`min(P.l, L.l)`).
- Targets: structural wick targets vs the pivot ladder (k=2, nearest
  beyond the trigger on that timeframe's loaded bars, shallow 4h depth)
  vs the 1.5x-stop measured-move fallback that the skill RETIRED to
  ATLAS-legacy (R18 says measured move = the prior leg projected from
  the trigger). No higher-timeframe extension for T2+ (skill 5.1).
- The 1-3: far side (scanner) vs reclaim (skill R22) vs halfway (R19).
  Which is canon, which is tradeable on 1m data, and what does the A5
  receipt (875 halfway candidates, all refused, 268 by the in-force
  check at the cross minute's close) actually tell you?
- Invalidation: entry bar turns Type 3 -> out at market before the stop
  (skill 5.4 order). Faithful? The scanner builds its forming bar from a
  "mid-union" of mids, which produced both parity residuals.
- Continuations: canon says ride until a reversal combo prints; the
  executor rests a near-bank pivot TP (0 wins in 12) and the escalate
  license. Which deviation is doing the damage, if any?
- The xyz bell: STRAT's intraday rules (skill 5.5) are RTH-equity rules;
  the bell here is a liquidity / oracle-regime gate on a 24/7 perp. Is it
  a STRAT rule, a venue rule, or neither?

### 4.2 Candidate selection

Universe (perps + xyz; rev-only; 1h/4h/1d), the $1M volume floor, the
bell, the drift veto (crypto only), the escalate license, the R:R floor
(gross -> net in round 3), the reach gate, arrival order (A4 inert), two
seats, cooldown, day cap, transition-only arming. For each gate: is it
structural or sample-motivated, what did its refused pool simulate, is
it redundant with another gate, and is the census reading distorted by
gate ORDER? Then the missing layers: setup quality (bar range vs ATR,
the 50% / DCR line as a quality filter per R19, volume at the trigger,
higher-timeframe confluence, time left in the bar, book depth / spread,
funding sign and magnitude, session), per-coin or weekly-bias
alternatives to the BTC veto, and the weekend-1 "confirmation lag"
finding (early longs the stack gate refused simulated better than its
admissions). Say what you would rank candidates by and why A4 never
bound.

### 4.3 Entry mechanics and sizing

Market at mid on the transition poll, slippage on thin books (weekend-1
P5), the entry_bar_invalidated gate, $0.50 risk with $10/$100 clamps
(21 of 32 round-2 tickets landed $0.45-0.56; the tails were under- and
over-risked), 10x isolated, the 80% liquidation-distance rail, MAE
clearance. Should size respond to anything (setup class, timeframe,
ATR, book), or is fixed-risk the right control for a mechanics test?

### 4.4 Target criteria

Structural wick targets, nearest-pivot T1, the 1.5x fallback, the reach
gate (22 refused, 2 winners), the R:R floor's interaction with tiny
targets (3,515 refusals; 69% simulated winners with a negative mean),
the post-exit rung tracker (T2..T4 as magnitude multiples, not
higher-timeframe structure), and the research book's ladder results
(D1 vs D2-D5; P1 vs P2; X1; the "magnitude is a decision point, not an
exit" reading in skill 5.1). Should T1 be timeframe-aware, confluence-
aware (a daily pivot that IS the weekly pivot), or time-aware? What
target rule would you run against full-exit-at-T1 as the next rung of
the ladder, and what would falsify it?

### 4.5 Exit mechanics, including MFE / MAE / ATR-based designs

What exists: invalidation, the structural stop, the four-timeframe flip,
the target, KILL_FLAT; no time stop, trailing, breakeven or partial in
the live control. What the data says: 26 of 28 resolved flips across the
two ledgers hit the stop first afterwards, but the coupled-open subset
exited near flat; the research ATR stop (3x hourly ATR frozen at fill)
is the only overlay winning on both axes on the control book and a tax
on the floored book; every Tier A cell carried a 30-40% MAE tail; the
TVB-13 give-back fixture; the walk-up and bank-half replay receipts;
`tracker.jsonl` (peak favorable / adverse at 1 h / 4 h / 24 h after
every exit). Design at least five exit mechanisms that use MFE, MAE, ATR
or time explicitly (for example an ATR-scaled stop, an MFE-fraction
give-back stop, a time-in-trade stop, a partial at 1R with a structural
trail by 2U lows / 2D highs, a pivot-zone stall exit per skill 5.4, a
DCR / 50%-line stop per R19), each as a single-change arm card (section
5), and say which ONE you would run first against the control and why.
Be explicit about which of these are STRAT and which are deviations.

### 4.6 Regime, clock and session

The BTC drift veto (TVB-4/5/9 research prior: stand-aside contains
damage, faster regime clocks destroy), the 00:00 UTC coupled opens, the
xyz bell vs extended hours (A1), the Korea cluster, the weekend and OPEX
dead zones, funding (round 2 had paid $0.23 of funding against $0.73 of
fees by the 28-trade snapshot; multi-hour shorts on high-rate coins), the "overnight / geopolitical regime" the owner is
watching. What regime input, if any, would you pre-register, and what is
its structural reason?

### 4.7 Fidelity and measurement

The parity gate and its three amendments (are they legitimate fidelity
fixes or tuning-until-it-matched?), decision mid vs trade candles, the
scanner's mid-union forming bar, the roll freeze, the research twin's
declared fidelity deltas, TradingView's intrabar approximation, and what
is still unmeasured (a slippage / book-depth model, oracle-hours fills,
funding on longer holds). What measurement would you add BEFORE the next
design round?

### 4.8 Code and operations

Silent failures, fail-open paths, gate-order bugs, the state machine
around pending intents and reconciliation, the KILL_FLAT path, the
equity formula, the round-3 port (net_reward_risk vs the replay's
gates.py, the fail-closed fee branch), test coverage of the exit
predicates, Pine `request.security` usage, anything a careful engineer
would not ship. Severity-ranked.

### 4.9 Research process

Prereg-before-code, single-change arms, the ladder, the matched-trade
axis, small n, nine arms read on one 32-trade ledger (best-of-nine
selection), arms designed from a reject dig on the same ledger they were
receipted on, the parity amendments after FAILs, the watermark practice,
the "characterization not validation" language. Is the process honest
with itself? Where is it most likely fooling the owner, and what would
you change about HOW the program decides, independent of WHAT it trades?

### 4.10 Anything else

Anything the sections above do not name. The owner explicitly asked for
this; do not skip it.

## 5. What a recommendation must look like

Every recommendation is a card:

- NAME and one-line trader statement ("a setup must pay for the stop
  and both legs' fees before it is worth a ticket").
- CODE statement (which module, which gate or exit, the predicate).
- STRAT STATUS: faithful (cite the skill section / corpus chapter) or
  DEVIATION (name the rule it departs from and the structural reason).
- STRUCTURAL RATIONALE, separate from any number.
- WHAT IN THE DATA MOTIVATES IT, and whether that makes it in-sample for
  the two ledgers (be honest; most things will be).
- PREDICTED EFFECT and FALSIFIER (what result on which ledger or window
  would make you drop it).
- HOW TO RECEIPT IT: replay arm on the closed ledgers, research-book arm
  in the Python twin / TradingView mirror, live shadow field, or a new
  measurement first.
- COST / RISK (fees, occupancy, complexity, venue primitives it needs).
- RANK among your recommendations.

Then three more things:

1. THE ONE CHANGE. The owner asked Claude "if you could change the
   variables in one shot, what would it be and why"; Claude answered the
   net-of-fees floor (reasoning in section 2.5). Answer the same question
   YOURSELF FIRST, before re-reading Claude's answer, then state where
   you agree or disagree and why.
2. WHAT YOU WOULD NOT HAVE DONE that this program did (rules, gates,
   exits, process), ranked by how much it matters.
3. WHERE CLAUDE IS MOST LIKELY WRONG. Claude wrote most of the code, the
   receipts and the readings in section 2. Re-derive at least these from
   the raw ledgers and say if they hold: the A9 mechanism (the gain is in
   the displaced set, not admitted winners); A6 negative on matched
   trades; A5 empty under D4; the flip exit's stop-first count; the
   weekend-1 P5 slippage attribution; the claim that the three parity
   amendments were calibrated on served fields, not outcomes.

## 6. Output contract

Write ONE file: `docs/reviews/deep-dive-2026-09-05-astra.md` in the
public repo (plain ASCII; no secrets; `file:line` citations). Shape:

1. Metadata: what you read, what you ran, what you could NOT verify.
2. THE THREE FINDINGS THAT MATTER (each with a trader sentence, a code
   sentence, the evidence, and a bar-by-bar walkthrough of one real trade
   or refusal from the ledgers that shows it).
3. A verdict table, one row per dimension in section 4: faithful /
   divergent / defect / open question, with the pointer.
4. Recommendation cards (section 5), ranked; the one change; the
   would-not-have-done list; where Claude is most likely wrong.
5. At least three full walkthroughs from the ledgers: one continuity-flip
   exit, one ticket the fee-aware floor displaces, one invalidation exit
   (decision row -> fill -> exit -> post-exit tracker, with timestamps).
6. Appendix: everything else, in any order, clearly marked as appendix.
7. A "Suggested next review prompt" section if you think a better one
   exists.

Length: as long as the content needs, but the first two sections must
stand alone for a reader with ten minutes. Rank, do not dump. Do not
propose a promotion decision; the owner makes those.

------------------------------------------------------------------ END PROMPT
