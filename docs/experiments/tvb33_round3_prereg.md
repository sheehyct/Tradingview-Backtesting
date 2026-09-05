# TVB-33 round 3 -- live-executor ruleset v2 + ledger replay -- pre-registration

**LABEL: PRE-COMMITTED SINGLE-CHANGE ABLATION of the live hip3-executor
ruleset (nine arms, each one change against the as-built v1 control),
receipted FIRST on the two CLOSED live ledgers by a replay harness, THEN run
live as round 3 with round 2 as the control. NO deployment claims. NO arm
promotion by sample performance. Kill-first: the job of the replay is to
find where each ruling fails, not to confirm it. Every conclusion attaches
to the contrast that isolates it; the composite never adjudicates its
parts; extreme numbers are questions.**

- Declared: 2026-09-04 (TVB-33 design session, plan mode), BEFORE any
  replay or executor code exists. Git HEAD at declaration: this repo
  4c9e920; hip3-executor 1e79398 (round-2 CLOSE commit); hip3-scanner main
  as of the PR openings (pinned in the PRs).
- Author: the 2026-09-04 design session -- every ruling R1-R12 was made by
  the USER in-session (AskUserQuestion rounds, with the SOL 1-3 minute
  path and the reject dig as the pictures); items D1-D12 are Claude
  declarations flagged in-session and approved with the plan.
- Engine: (a) the ledger replay harness, hip3-executor `analysis/replay/`
  (private repo; local transport for reviewers), over
  `runs/2026-08-22_weekend1/` and `runs/2026-08-31_round2/` (closed
  journals + venue fills/funding committed; 1m/HTF candle caches
  gitignored, sha-pinned); (b) the live executor for round 3.
- Relation to prior rounds: Ruleset v1 (hip3-executor README, five rulings
  2026-08-26 + amendments) is the CONTROL. The full trader/code text of
  every v2 ruling lives in the executor README block "Ruleset v2 (round 3
  -- PREREG, user-ruled 2026-09-04, frozen before code)"; this document is
  the public-repo pre-registration of the same rulings, the arms, the
  contrasts and the named-deferred list, and is the adjudication anchor
  for the external review.

## Where this round comes from (mechanism, not scoreboard)

Round 2 (Mon 2026-08-31 15:37Z -> Fri 2026-09-04 17:13Z, KILL_FLAT on the
user's word): 32 entries / 32 exits, equity 99.60 -> 99.86 spot USDC, net
+$0.26 all-in. Mechanics held; the overnight analysis (TVB-32) and today's
reject dig surfaced MECHANISMS, not a scoreboard: (1) the equity-hours
clock is applied to every xyz coin -- oil, metals, FX and indices included
-- so oil's 04:06 ET 4h reversals and CRCL's 07:03 / 08:33 ET runs were
refused by a bell that does not exist for those underlyings; (2)
candidate selection is arrival order with no ranking, and the two-seat cap
refused CRCL's 4h 3-2U (R:R 1.35, passed every gate) because two probe
tickets held the seats; (3) JUP short #1 reached +4.7% (two thirds of its
target), came all the way back and flipped out at -0.6% with nothing
banked -- the runner lane the research book has carried since TVB-13; (4)
the 1-3 Rev Strat's trigger convention (scanner far side vs skill R22
reclaim) needed a ruling; (5) tickets clamped by the $100 notional cap
paid 69-86% of their risk budget in fees. Continuations are 0 for 12
across both runs under the reversal-backed license. None of these is a
performance claim; each is a design question answered below a-priori.

## User rulings (2026-09-04, all a-priori)

1. **Test venue = ledger replay first.** Each ruling gets a counterfactual
   receipt on BOTH closed ledgers (venue 1m candles, stop checked before
   target, fees from fills, funding) before capital; then live round 3
   with the receipt-passing arms as the arm and round 2 as the control.
2. **1-3 trigger = the halfway line** (skill R19, the 50 percent rule):
   entry the instant price retraces past half of the inside bar after the
   first-side break; stop = the entry bar's first-break extreme; target =
   bar 0's far wick; the later Type-3 completion is not an invalidation.
   Alerts fire, labelled "1-3 (50%SSS)" until the far side prints. The
   as-built far side stays the control.
3. **xyz clock = extended hours**, 04:00-20:00 ET weekdays, ONE window for
   every xyz coin regardless of instrument class. Named future variant: 24
   hours ex-weekend (from the Sunday 8pm ET open) for the top-10 xyz
   tickers by 24h volume meeting the criteria -- definition owed.
4. **BTC drift veto:** one arm = no veto; veto stays the control.
5. **Continuations:** one arm = continuity-backed (the coin's OWN
   daily/weekly/monthly continuity complete and agreeing) on 4h/1d;
   reversal-backed escalate stays the control.
6. **Candidate selection:** one arm = higher timeframe first (1d > 4h >
   1h, then reward-to-risk); arrival order stays the control.
7. **Runner profiles:** two arms vs full exit at T1. WALK-UP: full
   position through T1, take-profit resting at the ladder's LAST rung,
   next target = nearest untaken pivot on the next higher timeframe (1h ->
   4h -> 1d -> 1w), stop walks ONE RUNG BEHIND (T1 -> breakeven; rung 2 ->
   T1), ladder frozen at entry, flip + invalidation exits on. BANK-HALF:
   50% at T1, remainder to the next-timeframe pivot with the stop at
   breakeven; a ticket too small to halve falls back to the control exit,
   journaled. Breakeven = fill plus one tick in the trade's favor.
8. **Pivot ladder source = the scanner** (sorted qualifying k=2 pivots per
   timeframe incl. 1w); the executor never analyzes bars.
9. **Fee-aware floor** (amendment): net reward over net risk after both
   legs' fees >= 1.0. Minimum prior-bar range: named deferred. Funding
   gate: named deferred, with an expected-funding receipt at entry.
10. **Seats:** one arm = five concurrent positions; two stays the control.
11. **Crypto on weekends:** unchanged (no clock on main-dex crypto);
    weekend-protocol arms stay named-deferred.
12. **"Completes"** = the instant the second side breaks, intrabar, never
    the bar close.

## Claude declarations (flagged in-session, approved with the plan)

- D1 1h continuations stay under the escalate license in the continuity
  arm (the ruling names 4h/1d).
- D2 Bank-half remainder targets ONE next-timeframe rung (no further walk).
- D3 Walk-up escalates one timeframe per rung; ladder exhausted = the
  resting terminal take-profit fills.
- D4 Halfway 1-3: payload name `1-3h` (a pure function of bars, so the
  replay can tell conventions apart), display/alert label "1-3 (50%SSS)",
  superseded in display by `1-3` on the same bar once the 3 completes.
  Replay fill at the halfway line; a break and cross inside one 1m candle
  is ambiguous and excluded (counted); zero-range inside bars unusable
  (counted).
- D5 Fee-aware floor formula: (target_dist - fee_rt) / (stop_dist +
  fee_rt) >= 1.0, fee_rt = the venue's observed round-trip rate per dex
  (main ~0.07%, xyz ~0.086% of notional), journaled on the row.
- D6 Expected-funding receipt = current funding rate x notional x the
  signal timeframe's bar length in hours (receipt only, no gate).
- D7 Replay parity gate (control replay vs the taken book): entries 100%
  identical by (coin, tf, signal, dir, decision row); exit-reason
  agreement >= 90% with every mismatch in a closed residual list
  {mid_union_type3, flip_timing_1m, coupled_open_tick, thin_xyz_candles,
  kill_flat_truncation, unknown_exit_row}; |sum pp| <= 1.5pp and |net USD|
  <= $0.50 per ledger; reconstruction validators (rr 100%, ATR >= 95%
  within 5%, BTC drift >= 95%, htf_backing >= 90%). No arm is read until
  PASS; residuals are recorded, never tuned.
- D8 Weekend-1 arm contrasts run against a v1 replay control; its v0
  as-built parity (no drift/reach/xyz/invalidation exit, $30 fixed
  notional, R:R floor from 15:35Z) is the engine-fidelity receipt.
- D9 A replay "poll" = decision rows sharing one journal second.
- D10 Scanner 4h retained depth 12 -> 40 bars in the ladder PR (weight
  math stated in the PR).
- D11 Replay output home: hip3-executor `runs/2026-09-04_replay1/` (both
  ledgers by path + sha; `PREREG.md` written before any number).
- D12 Live round 3 needs three supervised probes before profile autonomy:
  partial reduce on a min ticket; stop place-new-then-cancel-old;
  optional trigger-modify semantics.

## Arms (declared exhaustively; single change each)

| Arm | Control (v1 as built) | Arm value |
|---|---|---|
| A1 clock | xyz 09:30-16:00 ET | 04:00-20:00 ET weekdays, every xyz coin |
| A2 drift | BTC daily-open veto on main-dex crypto | no veto |
| A3 conts | escalate (live higher-TF reversal) | own D/W/M continuity complete + agreeing, 4h/1d |
| A4 selection | arrival order | 1d > 4h > 1h, then R:R desc |
| A5 1-3 | far side | halfway line (`1-3h`) |
| A6 profile | full exit at T1 | walk-up (terminal TP, stop one rung behind) |
| A7 profile | full exit at T1 | bank half at T1, remainder to the next-TF pivot, BE stop |
| A8 seats | 2 | 5 |
| A9 floor | gross R:R >= 1.0 | net-of-fees R:R >= 1.0 |

Config defaults ARE the control; the startup journal row records the arm
set; `assert_single_change` in the replay makes "one change vs control" a
tested property.

## Contrast statements (binding; conclusions attach here and nowhere else)

- Each arm vs CONTROL, on BOTH ledgers, on BOTH axes: whole-book (net USD,
  pp, max drawdown, occupancy, trade count, exit-reason mix) and
  matched-trade (identities common to control and arm; displaced vs
  admitted identities listed). The TVB-25 lesson binds: an occupancy
  effect is not exit quality.
- A1 / A3 / A4 / A8 change WHICH trades exist -> whole-book primary,
  matched secondary. A6 / A7 / A9 change what happens to the same trades
  -> matched primary. A2 both. A5 narrow tier = the scanner-rowed 1-3
  candidates re-timed to the halfway cross; a wide tier (candle-detected
  halfway setups with no scanner row) is a labeled census only.
- An all-arms composite is a labeled reading; it adjudicates nothing.
- Weekend-1 contributes only where its v0 universe overlaps (no xyz, no
  drift rows): A1/A2 on weekend-1 exist only relative to the v1 replay
  control (D8).

## Metrics + pre-committed diagnostics

Per arm and ledger: trade count, wins, gross, fees, funding (provenance
ledger / history / unmodeled), net USD, sum and mean pp, max drawdown,
occupancy, median hold, exit reasons; matched deltas per trade; A6/A7
rung prints and stop-walk exits; A5 ambiguous / zero-range counts; A7
unexecutable partials; A1 xyz-only slice; A4 displaced/admitted list on
the multi-candidate polls; A9 refused-by-fee list. Upper-bound caveats per
arm stated in the report (mid fills, no queue, no slippage, oracle-hours
xyz candles, 1m flip timing vs 5s mids, transition-only candidate stream,
restart baselines unjournaled).

## Execution + provenance

Order: this prereg + the executor README v2 block (docs only) -> replay
`PREREG.md` + arms/rules modules -> caches/fetch/vendored STRAT core ->
reconstructions/gates (differential-tested against the live `evaluate`)
-> control exits + allocator -> PARITY on round 2 then weekend 1 -> arms
A2/A4/A9 (no new data) -> A1/A3 -> pivots + A6/A7 -> A5 -> report + pins.
Scanner PR-B (pivot ladder) and PR-A (`1-3h`) land in parallel; executor
code lands per the commit sequence in the plan, prereg commit first,
control values default. Every replay JSON pins the sha256 of every input
cache, both journals, the prereg, the replay code and the git HEAD. Fees
from `venue/fills.json` (observed 0.0399% of notional per round trip; 61
taker / 4 maker); stops fill at the level; software exits at the 1m close.

## Named deferred (NOT run in v2; on record so they cannot be smuggled in)

Minimum prior-bar range floor; funding-aware entry gate; the 24-hour
top-10-volume xyz clock; per-instrument-class session calendars; weekend
protocol arms; the reclaim (R22) and any other 1-3 convention beyond the
control and A5; 2h / 8h / 12h walk-up rungs; executor-computed pivots;
three or four seats; the walk-up "TP at the next rung" variant; conviction
tiers / size multipliers (position-sizing rule stands).

## Amendments (append-only, dated)

### Amendment 2026-09-04b (orchestrator, before any gate code)

D5's quoted fee rates ("main ~0.07 percent, xyz ~0.086 percent") came from
the overnight analysis prose and are WRONG against the venue's fills.
Observed round 2: main taker 0.0432% per side (round trip 0.0864%), main
maker 0.0144%; xyz taker bimodal per coin (0.00864% on HIMS / LITE /
MINIMAX / MU / NBIS / SP500 / ZHIPU vs 0.0864% on GOLD / MSTR); no builder
fee on any fill. D5 now reads: fee_rt = the observed round-trip rate for
that coin where fills exist, else the dex default (main 0.0864%, xyz
0.0746%), journaled on the row. Formula and floor unchanged. Weekend-1
facts from the files: first decision 14:27:28Z, last exit (kill_flat)
2026-08-24T21:58:24Z = the ledger's close instant.

### Amendments 2026-09-04d/e/f/g/h (hip3-executor runs/2026-09-04_replay1/PREREG.md carries the full text)

Fidelity amendments made between the first round-2 parity FAIL and the
PASS, each calibrated on SERVED fields or journaled facts, never on
outcomes; the pre-amendment receipts are kept in the executor run home
(parity_round2_prefreeze.json, parity_round2_flat.json):

- d/e ROLL FREEZE (sweep model). The scanner stops updating a forming bar
  once its period ends and rolls it only when that timeframe's refetch
  sweep reaches the coin; the sweeps share one queue in TFS order, so a
  timeframe's dot stays pre-roll for SWEEP_RANK[tf] x 75 s (15m x1, 1h x3,
  4h x4, 1d x5) after its own boundary. Fitted on served ftfc vs the store
  (88.8% agreement at 75 s vs 84.2% with no freeze). The first two-bucket
  per-universe constants (10 min perps / 30 min xyz) scored BELOW no
  freeze and were withdrawn. Applied to the flip walk and to the BTC drift
  sign.
- f DRIFT PIN. Where the live reason reveals the drift sign (a
  counter_drift refusal = against; any later-gate reason = not against)
  the control reads that sign; the P6 validator still scores the pure
  reconstruction (98.5%). Both remaining misses were BTC within $10 of its
  daily open inside one minute.
- g SETTLE PIN. A replay position the ledger also held frees its seat and
  starts its cooldown at the JOURNALED exit instant when the exit reason
  agrees or the mismatch is a declared residual class; exit legs, prices,
  P&L and the P3/P4/P5 checks keep the replay's own exits. Reason: a
  one-second seat-timing gap (ACE flip 00:44:29Z live vs 00:45:00Z
  replay; CHIP row 00:44:59Z) cascaded through every later entry.
- h D8 implementation note: weekend-1 arms contrast against a v1 REPLAY
  control (CONTROL_V1 across the window; no settle pin there); REPLAY.md
  marks each ledger block with its own gate status.

Results: round 2 PASS (22,401/22,401 decisions, 32/32 entries, 30/32 exit
reasons with 2 declared residuals, worst timing 2.8 min, net +$0.44 vs
venue); weekend 1 FAIL on P5 only (+$0.61 vs $0.50; +2.04pp vs 1.5pp).
Arm numbers: docs/ARM_LEDGER.md (Live executor family).

OPEN, for the user (not amended by Claude):
- Weekend-1 P5: the delta is fill slippage on two thin weekend trades
  (PURR entry 0.9%, STX stop 1.05%; the other 32 net to ~0). Slippage is a
  stated limitation, not a residual class. Options: accept the watermarked
  weekend-1 readings; amend P5 to score matched trades net of declared
  slippage cases; or declare a fill model a-priori.
- A5: under D4's in-force check at the cross minute's close, zero halfway
  entries survive (875 synthetic candidates: 359 volume, 248 clock, 268
  not beyond the line at the close). Options: re-time the in-force check
  to the cross instant at the crossing price, or leave the halfway tier
  unreceipted on this ledger.

### Amendment 2026-09-05a (USER RULING: the round-3 arm set)

After reading the receipts the user ruled: round 3 = Ruleset v1 + the
fee-aware floor (A9) and nothing else live; every other arm is
shadow-journaled so the round-3 ledger can receipt it again. Rationale
stated to the user and accepted: A9 is the only arm positive on both
ledgers AND on the matched trades, and its gain is the tickets it refuses
(fee-heavy losers), which is a structural accounting argument that would
stand even if the numbers were flat; A6 walk-up is negative on both
ledgers and on matched trades (rungs inside noise on 1h/4h ladders) and is
deferred to a daily-entries-only variant; A4 never bound; A1 admitted one
xyz trade (the R:R floor, not the bell, refuses the oil/CRCL runs); A2, A3,
A7, A8 are reshuffles whose sign does not hold across ledgers. Round 3 is
the next rung of the ladder (v1 -> v1+A9), receipted against round 2 as
the control; it is not a package.

Executor prereg block: hip3-executor README "Round 3 config (user-ruled
2026-09-05)". Live change: `fee_aware_rr: true` with the dex-default
round-trip rates (main 0.0864%, xyz 0.0746%), fail-closed when a dex has
no rate. Shadows journaled per row: net reward-to-risk and the rate used,
the observed per-coin rate, the scanner's D/W/M continuity, the poll
counter, the funding rate; per entry the expected-funding receipt (D6).
Equity display fix (spot USDC total) ships in the same branch as a
non-strategy change.

Amendment 2026-09-04i (found while porting; recorded, not tuned): the
replay's A9 receipt was computed with the dex-default fee table, not the
per-coin observed rates amendment b declared (the per-coin hook was never
wired into the allocator). The live floor matches the receipt; the
per-coin variant is named-deferred (A9c).

Named deferred, added: walk-up scoped to daily entries; A9c; a fill /
slippage model for the weekend-1 P5 question.
