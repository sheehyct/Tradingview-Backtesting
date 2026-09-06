# HANDOFF -- tradingview-backtesting

> Newest session entry at the TOP. Keep under 1500 lines; archive older entries to
> `docs/session_archive/` when it grows past that.

---

## Session TVB-34: deep-dive external review delivered and FOLDED, round-3 package approved and LIVE (COMPLETE)

**Date:** 2026-09-05/06
**Status:** COMPLETE -- the whole-program review came back, every checkable number
reproduced, five mechanics defects repaired on the executor, the research control
family watermarked, the user's Sunday rulings prereg'd, the round-3 package built
and LIVE on the VPS (effective open 2026-09-06 19:52:53Z after the agent-pruning
incident). Detail lives in the TVB-33 entry section 7 (the critical synthesis)
and its Open list; this entry is the close-out.

### What was accomplished

- Wrote and delivered `docs/guides/STRATEGY_DEEP_DIVE_REVIEW_PROMPT_2026-09-05.md`;
  the review returned as `docs/reviews/deep-dive-2026-09-05-astra.md`.
- Verified the review from the raw receipts (liquidation geometry, A9
  decomposition, research entry containment 58/106, fee algebra) BEFORE editing.
- Executor (main): liquidation-aware clearance (leverage set per ticket, venue
  liquidationPx receipted, liq_inside_stop warns), malformed-flat guard, "Stop
  Market" exact, partial-close fragments, dead-sponsor license; halfway
  synthesizer fix (amendment j) + parity re-gated + all arms re-run (pre-fix
  receipts archived); replay port + differential cases; 1,188 tests.
- Research: `TwinConfig.entry_fill "feasible"` + `analysis/paper/tier_b_exits_feasible/`
  contrast receipt (fresh A0b 76.5 -> 20.0, A0bS 111.1 -> 44.8, S0c 131.6 -> 67.3;
  D1 unchanged); ARM_LEDGER control family WATERMARKED, "the control still leads"
  withdrawn; A9 / A5 / fee-sensitivity / risk-band corrections on the record.
- User rulings (Sunday, the cheat sheet as the reference): 3-1-2 continuation
  target = outside bar's wick then a higher-TF pattern's target; 3-2-2 stop =
  outside bar's wick; nested inside bars keep the bar the whole coil sits inside;
  reviewer's time exit PARKED; extended hours stays the control (session shadow).
- Round-3 package approved and built: weekly dot on gate and flip, four seats,
  $1.00 risk / $200 cap on a $202 wallet, score x log-volume rank shadow, session
  shadow. Deployed 9f39ba9; interlock receipt clean; KILL_FLAT removed on the
  user's word; loop live 16:26:06Z. Incident 18:22Z: the venue had pruned the
  round-2 API wallet after Thursday's full withdrawal; the user approved a new
  agent and set the key on the VPS; loop restarted 19:52:53Z (effective open);
  the failing leverage call re-issued and accepted.

### Context for next session

The executor is LIVE (round 3; tmux `executor`; KILL_FLAT only on the user's
word). Round 2 is the control; three admission changes ride on top (fee floor,
weekly dot, seats), each journaled with its counterfactual. Watch:
`liq_inside_stop` must never fire, `fee_rate_unavailable` never appears, the
first entry receipt carries `lev` and `liq_px_venue`. The user will open a NEW
session for monitoring and the review of this leg. Rule learned: after any full
withdrawal, re-approve the agent before re-funding and check `extraAgents`.

### Files created/modified

- docs/guides/STRATEGY_DEEP_DIVE_REVIEW_PROMPT_2026-09-05.md (new), docs/reviews/deep-dive-2026-09-05-astra.md (new, verbatim review)
- docs/HANDOFF.md (TVB-33 section 7 + Open), docs/ARM_LEDGER.md, docs/experiments/tvb33_round3_prereg.md, docs/reviews/REVIEW_REQUEST.md, docs/INDEX.md, .session_startup_prompt.md
- analysis/paper/engine.py, analysis/paper/tier_b_exits.py, tests/test_paper_engine.py, analysis/paper/tier_b_exits_feasible/ (new receipt)
- hip3-executor (private): src/hip3_executor/{config,rules,broker,engine}.py, config.json, analysis/replay/{types,gates,recon,one_three}.py, tests/, README.md, runs/2026-09-04_replay1/ (PREREG j/k, re-run receipts, before_amend_j/)

### Open

- [ ] HANDOFF.md is over 1,500 lines: archive the TVB-27..TVB-32 entries to
      docs/session_archive/ on the user's word.
- [ ] Round-3 close-out replay: add the round-3 LedgerSpec (contrast_control
      "as_built"; read the journaled shadows first: stack, rank, session, lev,
      backing_invalidated) and replay it against round 2 at close.
- [ ] Scanner release with the three STRAT rulings (3-1-2 cont target, 3-2-2
      stop, nested mother) + PR-B pivot ladder / PR-A `1-3h`.
- [ ] The July A0b anchor under feasible fills is not written by the runner
      (owed for the July control-vs-package comparison).
- [ ] Score picker arm (receipt on the round-3 ledger before it trades);
      prospective halfway generator; fill/slippage model (weekend-1 P5).
- [ ] TVB-31/32/33 session reviews still unreturned.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb34-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: REQUESTED
- Commits to review: `7ad92f4..00d243e` on `main` (this repo: docs, the review
  file, the twin's entry_fill option, the feasible receipt); hip3-executor
  (private, local transport) `d8a07b0..5cd2b0d` on main.
- Scope / what changed: the deep-dive fold (five executor repairs, halfway
  synthesizer fix, replay port), the feasible-fill research contrast, the
  round-3 package (weekly dot, seats, risk, shadows), the go-live and the
  agent-pruning incident.
- Focus areas (scrutinize these): the liquidation formula and clearing-leverage
  selection vs the venue docs; the weekly-dot verdict (executor-computed
  dots_dir vs the scanner's coinSummary; missing/flat handling) and its use in
  BOTH gate and flip; the partial-close VWAP path across a restart; whether
  amendment j's decision-price convention is the right D4 successor; the
  feasible-fill twin change (only the arm-mode entry touched?); whether three
  admission changes on round 2 stay separable from the shadows.
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb34-codex-audit.md exists)

---

## Session TVB-33: round-2 CLOSED (KILL_FLAT) + reject dig + round-3 design session + Ruleset v2 prereg + ledger-replay harness BUILT + receipts + round 3 BUILT and READY (COMPLETE; deploy on the user's word)

**Date:** 2026-09-04 (afternoon/evening, same day as the TVB-32 Friday deploy)
**Status:** IN PROGRESS. Prereg frozen and pushed in both repos BEFORE any
code; the replay harness is being built in four parallel slices on
executor branch `feat/replay-harness` (skeleton 5c58e30).

### 1. Round 2 CLOSED on the user's word (17:13Z)

User: "kill flat the positions and shut down the wallet activity ... pull
those funds temporarily for manual trading until we design the next
implementation". Read-only VPS check first (loop alive on 4b5d248,
heartbeat 17:07Z, ATOM + HBAR 4h shorts tracked = venue view, no kill
files, no systemd unit, zero block rows, 6 first sightings of the new
`entry_bar_invalidated` gate). KILL_FLAT file created 17:13:19Z; HBAR
closed 17:13:26Z (-$0.06), ATOM 17:13:28Z (+$0.11); receipt 17:13:32Z
`clean: true`, 0 positions / 0 orders on main AND xyz, `order_sweep:
full`; loop halted and exited; public-API check 0/0, spot USDC 99.8567
with nothing on hold. `data/KILL_FLAT` LEFT IN PLACE as the restart
interlock; agent key stays on the VPS (order-only); the user withdraws the
funds. Closed ledger: 32 entries / 32 exits (19 flip / 5 target / 4
invalidation_type3 / 2 stop / 2 kill_flat); equity 99.6015 -> 99.8567
(+$0.26 net all-in, zero deposits); zero entries after the 15:08Z restart.
Closed journals + refreshed venue fills/funding installed in hip3-executor
runs/2026-08-31_round2/ (README CLOSE block; SNAPSHOT_TS = the receipt
instant; executor 1e79398). The gitignored candle caches were extended to
the close by the new `analysis/extend_round2.py` (tail-only merge; 289
caches, no errors). Harness note: the classifier blocks base64-piped
remote scripts and the safety hook blocks `Remove-Item` on Windows paths;
plain `ssh atlas@<host> 'cmd; cmd'` and Git Bash `rm` work.

DEFECT FOUND: the TVB-32 overnight snapshot's `decisions_r2.jsonl` was
MISSING 777 skip rows from 2026-08-31 20:03Z-23:59Z that the cumulative
VPS journal holds (contiguous, all `skip`, normal 160-263 rows/hour
cadence, zero entries in the window) -- a slicing defect at snapshot time,
not a journal gap. Every pool-census count in ANALYSIS.md / analysis.json
for that Monday evening is an undercount (all refusals; no trade
affected). Noted in the run README; ANALYSIS.md/analysis.json left as
the reviewed snapshot record. For the TVB-32 reviewer.

### 2. Reject dig (user: BRENTOIL, CL, CRCL "had some pretty good runs")

Every sighting of all three was refused, overwhelmingly by the
equity-hours clock: BRENTOIL 60/84, CL 57/80, CRCL 63/78 sightings
(`underlying_closed`), then the R:R floor (15/14/12), the seat cap, and
one `entry_bar_invalidated` each on today's 4h longs. The clock is a
weekday 09:30-16:00 NY window applied to EVERY xyz coin: oil, metals, FX
and Asian indices included. The runs and who refused them (1m replay,
fill at the sighted mid, stop-before-target): oil's Sep 1 +4.7% day = 4h
3-2U longs at 04:06 ET on both names, clock-refused, 3.4R / 4.1R; CRCL Aug
31 +6.4% = 4h 3-2U at 12:06 ET, R:R 1.35, passed EVERY gate, refused only
because the two go-live probes (SP500 12:02, HIMS 12:04) held both seats,
+6.2% MFE, 1.4R; CRCL Sep 3 +15% = 1h 1-2-2 at 07:03 ET (21R stop-only over
48h on a 0.75% stop) and 1d 1-2-2 at 08:33 ET, both clock-refused; inside
the bell the only long was a 1h cont refused by the seat cap. Caveats: the
clock guard runs before R:R/reach/drift, so its pool never met the later
gates (upper bound); mid fills, no fees/slots. Script:
scratchpad reject_dig.py (per-setup lines + per-guard summary).

### 3. Design session (plan mode; strat-methodology loaded; two Explore +
### two Plan agents; every decision via AskUserQuestion in trader terms)

Walkthroughs used: SOL 4h 1-3 minute path (Tue Sep 1 ET: inside bar
98.87-100.30 inside the noon-4pm mother bar 98.29-102.00; the 8pm bar broke
the low 9:47pm, bottomed 98.49, reclaimed 98.87 at 9:55pm, crossed the
inside bar's halfway 99.59 at 10:33pm, took 100.30 at 11:11pm where the
bot bought, topped 100.65; flipped out 12:08am at -0.38%; all three entry
conventions stopped by Wed morning bracket-only); JUP #1 runner
(+4.71% MFE -> -0.63% flip; bracket-only would have been a stop; JUP #2 hit
+4.84%); the reject-dig cases. Facts that shaped the options: the scanner
computes 15m/30m/1h/4h/1d/1w/1M (no 2h/8h/12h), serves ONE target per
signal (nearest k=2 pivot or bar-0 wick), already serves `prov.kind` +
`us_session` and `dwmContinuity` which the executor never reads;
selection is arrival order (`selectionRank` null); P2 lost both axes in
TVB-25 while P1 won per matched trade; the thestrat_ai corpus says
"start small, add to winners, never scale out" (tension item, not
adopted); "walk up the timeframe" is a project-derived idea.

TWELVE RULINGS (user, 2026-09-04): R1 ledger replay first, then live round 3
(amended = arm, round 2 = control). R2 1-3 trigger = the HALFWAY LINE (50
percent rule, R19): live when price retraces past half the inside bar
after the first break; stop = the entry bar's first-break extreme; target
= bar 0's wick; the 3 completing is not an invalidation; scanner name
`1-3h`, label "1-3 (50%SSS)" until the far side prints; alerts fire; far
side stays the control. R3 xyz clock = EXTENDED HOURS 04:00-20:00 ET
weekdays, ONE window for every xyz coin; future variant named: 24h
ex-weekend (Sunday 8pm ET open) for the top-10 xyz by 24h volume. R4 no
drift veto (arm). R5 continuity-backed 4h/1d conts via the coin's own
D/W/M stack (arm). R6 higher-timeframe-first selection, then R:R (arm).
R7 walk-up (TP at the ladder's LAST rung; next target = next-TF pivot;
stop ONE RUNG BEHIND; ladder frozen at entry; BE = fill + one tick) and
bank-half (50% at T1, remainder to the next-TF pivot, BE stop; sub-$20
tickets fall back to T1, journaled) as arms vs full exit at T1. R8 the
SCANNER serves the pivot ladder. R9 fee-aware R:R floor (net of both
legs' fees >= 1.0) as an amendment; min prior-bar range and the funding
gate NAMED DEFERRED with an expected-funding receipt. R10 five seats
(arm). R11 crypto on weekends unchanged. R12 "completes" = intrabar. The
user asked for my view on seats (given: arm not amendment; the blocked
queue simulated worse at the median in both runs) and on the three
lanes (given with the fee-share table: PAXG 86%, GOLD 69% of risk in
fees). Claude declarations D1-D12 approved with the plan (parity gate
thresholds, replay conventions, supervised probes).

### 4. Phase 0 -- prereg BEFORE code, pushed in both repos

- hip3-executor README "Ruleset v2 (round 3 -- PREREG, user-ruled
  2026-09-04, frozen before code)" (5ba3347).
- This repo `docs/experiments/tvb33_round3_prereg.md` (LABEL block,
  rulings, declarations, nine arms A1-A9, binding contrasts, named
  deferred) + `docs/ARM_LEDGER.md` "Live executor family" section
  (v1 control cards + A1-A9 cards, trader terms, numbers pending)
  (7deca94).
- Replay skeleton on executor branch `feat/replay-harness` (5c58e30):
  `analysis/replay/types.py` (the contract), `CONTRACT.md` (four slices),
  `runs/2026-09-04_replay1/PREREG.md` (pins README v2 @ 5ba3347 + prereg
  @ 7deca94; parity gate; arms; limitations), pytest pythonpath + ledger
  marker, `tests/replay/synth.py`.

### 5. Ledger replay harness -- BUILT, round-2 parity PASS, nine arms receipted

Built in four reviewed slices (S1 foundation, S2 rules/gates, S3 exits/
allocator, S4 parity/report; 1,032 tests) on hip3-executor branch
`feat/replay-harness` (5c58e30..b1da068, pushed; nothing under src/
changed). The three "failed" background tasks the user saw were the
parity CLI exiting non-zero on a real FAIL and two mid-build test runs
inside teammates, fixed before the slice commits; the teammates then hit
the account's session limit and the rest was done directly.

Parity round 2: FAIL -> FAIL -> FAIL -> PASS across three fidelity
amendments (prereg d-h, executor PREREG.md; mirrored in
tvb33_round3_prereg.md): (1) the scanner's post-roll FREEZE -- served
dots keep the pre-roll value for one refetch sweep per timeframe (~75 s
each, TFS order; the daily dot lags ~6 min; a first per-universe 10/30
min guess scored below no-freeze and was withdrawn); (2) the BTC drift
sign journal-pinned where the refusal reason reveals it (both misses
were BTC within $10 of its open inside a minute); (3) matched positions
free their seat at the journaled exit instant (a one-second seat gap
cascaded through every later entry). Final: 22,401/22,401 decisions
agree, 32/32 entries, 30/32 exit reasons (2 mid_union_type3), worst
timing 2.8 min, net +$0.44 vs venue (threshold $0.50). pins.json written.

Parity weekend 1: 34/34 entries, 33/34 exit reasons (KAITO
coupled_open_tick), P5 FAIL by $0.11 / 0.54pp = fill slippage on PURR
(entry 0.9%) and STX (stop 1.05%); arms run WATERMARKED against a v1
replay control (D8; net -$2.16 on 27 vs the v0 book's -$6.86 on 34).

Arms (round 2, control +$0.70 on 32): A9 fee-aware floor +$3.30 (the
gain is the 11 refused fee-heavy losers, -$1.61); A6 walk-up -$1.51 and
-$1.30 on matched trades (same sign on weekend 1); A3 +$1.26, A2 +$1.20
(sign flips on weekend 1), A7 +$0.82 (matched -$0.48), A1 +$0.75 (one
xyz trade admitted; oil/CRCL die at the R:R floor once the bell opens;
two 4h conts found no seat), A5 +$0.36 with ZERO halfway entries (875
synthetic candidates all refused: volume 359, clock 248, not beyond the
line at the cross minute's close 268), A8 -$0.14 on 55 trades, A4
identical (never bound). Full cards: docs/ARM_LEDGER.md; dual-language
report: executor runs/2026-09-04_replay1/REPLAY.md.

### 6. Round 3 ruled and built (user, 2026-09-05: "lets go with that and get it ready")

Asked for a one-shot recommendation, Claude proposed: make the R:R floor
net of fees (the only arm positive on both ledgers and on matched trades,
for a structural accounting reason), change nothing else live, and
shadow-journal every other arm so the next ledger can receipt them again.
The user accepted. Prereg'd BEFORE code in both repos (executor README
"Round 3 config"; public prereg amendment 2026-09-05a; replay PREREG
amendments i and 2026-09-05a). Found while porting: the A9 receipt was
computed with the dex-default fee table, not the per-coin rates
amendment b declared (the hook was never wired) -- recorded as amendment
2026-09-04i; the live floor matches the receipt, the per-coin rate is a
shadow (A9c, named-deferred).

Built on hip3-executor `feat/round3-fee-floor` (merged to main): the net
floor with dex-default rates and fail-closed refusal, config validation
at load, shadows on every decision row (rr_net, fee_rt_pct,
fee_rt_pct_coin, dwm, poll, funding_rate), the D6 expected-funding entry
receipt, `arms` on the startup row, the hourly `equity` tracker row, and
the TVB-32 equity fix (account_value = spot USDC total). 1,144 tests; the
replay differential proves live and port agree on the fee-aware cases;
paper smoke run clean. NOT deployed: the VPS deploy, the interlock
receipt, the equity check and `rm KILL_FLAT` all wait for the user
(checklist in the executor README STATUS 2026-09-05).

### 7. Deep-dive external review FOLDED (2026-09-06; the critical synthesis)

Review: `docs/reviews/deep-dive-2026-09-05-astra.md` (GPT-6 Astra via the
local transport; prompt `docs/guides/STRATEGY_DEEP_DIVE_REVIEW_PROMPT_2026-09-05.md`).
Verdict on the review: the best this program has had. Every numerical
claim I could check reproduced from the raw receipts before any edit
(scratchpad verify_review.py): the liquidation geometry, the A9
decomposition to the cent, the research entry-containment census
(58/106, 63/123, 1/39, 81/492), the July fee algebra. The user was told
the plain-terms reading first and said continue.

AGREE (acted):
- R1 stop-vs-liquidation. The rail used 1/leverage; the venue liquidates
  at (1/L - m)/(1 -/+ m), m = 1/(2 x maxLeverage) (5.26% long / 4.76%
  short at 10x vs the 8% the rail admitted). Round 2: LITE, ACE, NBIS
  stops rested BEYOND the liquidation price, ZHIPU and DOT past the 80%
  buffer; weekend-1 XMR the same. None hit. Repaired: `liq_model
  "maintenance"` picks the leverage per ticket so the stop clears (LITE
  8x, ACE 2x, NBIS 7x), the entry SETS it, and the entry receipt carries
  the venue's liquidationPx + `liq_inside_stop` (receipt + warn).
- R2/R3/R4 broker defenses: malformed account response is unknown never
  flat (both dexes serve assetPositions as a list when empty, checked
  read-only); stop verifier requires "Stop Market" exactly; partial IOC
  closes book their fragment and the exit prices size-weighted.
- R8: a higher-TF reversal whose forming bar is a Type 3 cannot license
  a continuation (`backing_excludes_invalidated`; the as-built sponsor is
  journaled as a shadow).
- R5: the A5 halfway synthesizer set mid == trigger; the strict in-force
  gate refused every candidate. MY ERROR: I reported the 268 refusals as
  the D4 convention. Fixed (amendment j: decision price = cross minute's
  close), parity re-gated (round 2 PASS again; weekend 1 P5 FAIL as
  before), all arms re-run, pre-fix receipts archived in
  `runs/2026-09-04_replay1/before_amend_j/`. Result: round 2 still zero
  halfway entries for honest reasons (109 R:R floor, 44 no seat, 44
  close back inside, 41 stack, 18 drift); weekend 1 five halfway entries,
  zero winners (-$1.67 on the five; watermarked).
- R6/C1: the research twin's arm-mode entry books the prior-hour level
  even when the bar opened beyond it. Added `entry_fill "feasible"` (the
  rule the package path already used) and a labeled contrast receipt
  `analysis/paper/tier_b_exits_feasible/` (determinism gates PASS):
  fresh A0b 76.5 -> 20.0, A0bS 111.1 -> 44.8 with drawdown 36.5 -> 59.5,
  S0c 131.6 -> 67.3; July S0c 291.4 -> 155.0, A0bS 214.9 -> 88.2 with
  drawdown 55 -> 73; D1 unchanged. ARM_LEDGER control family
  WATERMARKED; "the control still leads" withdrawn as a finding.
- R7 (Finding 3): MY ERROR. A9's matched trades are identical by
  construction (I said "positive on matched trades"); only 6 of the 11
  displaced tickets fail the net floor directly, one a winner, all six at
  net R:R 0.95-0.9997 ("gross floor ~1.07" in practice); 5 vanished via
  seat reshuffle (3 of the 4 "gold-class" names I cited); the +$2.60 is
  62% avoided losses, 38% admitted tickets. The accounting argument
  stands; the money argument is thin and in-sample. The reviewer still
  picks the fee floor as the one eligibility change, for the accounting
  reason. THE USER'S RULING STANDS UNLESS THE USER CHANGES IT.
- Conceded wording: settle pin reads journaled exit instants (outcome
  data); "26 of 28 flips" was a mixed-slice slip (26/27, 27/28 closed);
  24/32 in the risk band; the state-stop family does NOT all flip
  negative at 0.1%/side (July stays positive). ARM_LEDGER corrected.

DISPUTE / NUANCE: none of the numerical findings. The reviewer's
"designed after a reject dig then receipted on the same ledger =
in-sample" is correct and was already implicit; recorded now as binding
(the next round needs a frozen forward window before any arm is called
anything). Its 21 recommendation cards are proposals; for a solo
operator the three that matter were R1, R5/R6, R7, and those are done.

NOT ACTED (user rulings or scanner PRs; put to the user): R15 same-color
3-1-2 continuation target = the containing 3's wick (skill invariant 5;
the near-bank pivot can MANUFACTURE admissions under the R:R floor);
Appendix B 3-2-2 stop = the outside bar's extreme (scanner uses the
trap's low, wider); R20 nested inside bars keep the original mother bar
(scanner uses closed[n-3]); which continuity stack is "STRAT" (four
intraday dots vs D/W/M); R10 the reviewer's proposed FIRST exit
experiment (no progress in two signal-bar lengths with < 0.5R MFE = out)
as a candidate A10 over the runner profiles; a prospective halfway
generator; a fill/slippage model (weekend-1 P5).

Commits: executor branch `fix/deep-dive-fold` 0562f14 (code + 1,172
tests) + the README amendment 2026-09-06b, PREREG j/k and re-run
receipts, merged to main; this repo: twin `entry_fill`, the feasible
receipt, prereg amendment, ARM_LEDGER corrections, this section.

### Open

- [x] BEFORE DEPLOY: deep-dive review delivered, returned and FOLDED
      (section 7). Blocking finding R1 repaired on executor main; round
      3 = v1 + fee floor + the mechanics repairs (liq_model maintenance,
      backing_excludes_invalidated, broker defenses).
- [ ] USER RULINGS raised by the review (before or after go-live, user's
      call): 3-1-2 continuation target (the 3's wick vs near-bank pivot);
      3-2-2 stop placement; nested-inside mother anchoring; the continuity
      stack question; whether the reviewer's no-progress exit becomes A10.
- [x] ROUND-3 PACKAGE BUILT 2026-09-06 (user-approved after the fold; executor
      main; prereg amendments 2026-09-06c executor / 2026-09-06b here): weekly
      dot on gate and flip, four seats, $1.00 risk / $200 cap on a $200
      wallet, score x log-volume shadow; the three STRAT scanner rulings
      (3-1-2 cont target = the outside bar's wick then a higher-TF pattern's
      target; 3-2-2 stop = the outside bar's wick; nested inside bars keep
      the bar the whole coil sits inside) recorded for the next scanner
      release; the reviewer's time exit parked.
- [x] ROUND 3 LIVE 2026-09-06 16:26:06Z (executor 9f39ba9; the user funded
      $202.24 and gave the go for the SSH deploy and go-live; interlock
      receipt clean 0/0 both dexes; KILL_FLAT removed; tmux `executor`
      --live). The round-3 ledger opens at that startup row; round 2 is the
      control. First minute: the fee floor refused DASH 1h 1-3 at rr_net
      0.959; stack / stack_60dwm / score / rank / session ride every row.
      Extended hours stays the CONTROL (user option 1: `session` shadow
      journaled, the bell gates). INCIDENT 18:22Z: the venue had PRUNED the
      round-2 API wallet when Thursday's withdrawal took the balance to
      zero, so the first qualified candidate (PURR) failed at the leverage
      step and reconciled fail-closed (no exposure); the user approved a new
      agent in the HL app and set the key on the VPS himself; loop restarted
      19:52:53Z = the EFFECTIVE round-3 open (no entry was possible before
      it); the failing call was re-issued on the new key and accepted.
      Lesson: a full withdrawal drops the agent; re-approve before
      re-funding. Watch list: `liq_inside_stop` must never
      fire; `fee_rate_unavailable` must never appear; the first entry
      receipt should carry `lev` and `liq_px_venue`.
- [ ] (done above) ROUND 3 GO-LIVE checklist, for the record: fund the wallet ($200)
      -> deploy main (deploy_from_dev.ps1, 40-hex DEPLOYED_SHA; SSH only
      with explicit confirmation) -> `--once` interlock receipt -> equity
      check vs the HL app -> `rm data/KILL_FLAT` -> tmux `--live` ->
      first heartbeat + first rr_net row. No supervised probes needed
      (no venue primitive changed).
- [ ] After go-live: add the round-3 LedgerSpec to analysis/replay
      (contrast_control "as_built"; the journaled shadows read
      journaled-first), replay it at close against round 2 as the
      control.
- [ ] USER RULINGS still open: (a) weekend-1 P5 -- accept watermarked
      readings, amend P5 to exclude declared slippage trades, or add a
      fill model; (b) A5 -- D4's in-force-at-minute-close convention
      leaves the halfway tier empty.
- [ ] Scanner PR-B (pivot ladder) and PR-A (`1-3h`) -- deferred with the
      profile arms and the A5 ruling; not needed for round 3.
- [ ] TVB-31 / TVB-32 audits unreturned; TVB-33 review requested
      (REVIEW_REQUEST.md): the three fidelity amendments and the live A9
      port are the things to attack.
- [ ] Carried: month-end fresh-window regen (overdue); TV mirror on
      demand; TVB-18 repairs; jackson set_inputs fix; metals /
      tech-vs-yields regime ID (user, later); trade visualization (the
      SOL minute path and reject-dig replays are the first instalment);
      replay `_Context` calls fetch.ensure_meta (network) -- make it
      offline-pure; walk-up scoped to daily entries as a future arm.

### External Review (for Codex / cloud review agents)

- Review status: REQUESTED 2026-09-05 (docs/reviews/REVIEW_REQUEST.md);
  the separate DEEP-DIVE review RETURNED 2026-09-05 and was FOLDED
  2026-09-06 (section 7). The TVB-33 session review is still open; its
  reviewer should read section 7 and the fold commits first.

---

## Session TVB-32: round-2 GO-LIVE (Mon 2026-08-31) + overnight ledger analysis (Thu/Fri 09-03/04) (COMPLETE, run STILL LIVE)

**Date:** 2026-08-31 (go-live) and 2026-09-04 (overnight analysis; session
resumed after the Monday process exited)
**Status:** COMPLETE. The executor has been trading autonomously since Mon
11:37 ET and was deliberately LEFT RUNNING (user, Thu night: "keep it
running"). Analysis delivered for the Friday-morning review; the
entry-gate fix was then MERGED AND DEPLOYED on the user's go (executor
4b5d248, restarted 15:08Z); the equity-display fix is not coded.

### Monday go-live (checklist items 1-4 done; 5 superseded)

- HyPaper: PARKED (user). Crypto-only + not drop-in; xyz support = a real
  fork (dex-aware meta/mids seeding, offset asset ids, dex-scoped reads,
  keyed positions/fills, per-dex funding) plus the mid-not-mark caveat
  bites hardest on equity perps. Revisit only after the live arc.
- Deploy: `deploy_from_dev.ps1` FAILED on first real use -- `git archive`
  on Windows (core.autocrlf=true, no .gitattributes) exported CRLF and
  remote_setup.sh died on `set -o pipefail`. Fixed with
  `* text=auto eol=lf` (executor fd4db97; archive verified byte-level
  zero CRLF). Deployed sha fd4db979 (= 4e384bb fold + that one line);
  90/90 tests on the VPS; KILL_FLAT drill clean (receipt `order_sweep:
  full`, 0/0); interlock removed on the user's explicit word; preflight
  PASS (agent approved; $99.60 spot USDC, unified account so perp
  accountValue reads 0.0 while flat).
- Live 15:37:45Z in the existing tmux session. Supervised probes = the
  first two live trades (xyz:SP500 1h cont short, xyz:HIMS 4h rev long),
  both xyz: README STATUS items closed with venue data -- (f) stop-row
  field VALUES confirmed on a real bracket (`orderType "Stop Market"`,
  `isTrigger true`, `reduceOnly true`, close side, remaining sz = position,
  venue-rounded triggerPx; the TP leg correctly FAILS the stop predicate);
  (e) `userFills` DOES carry builder-dex fills, dex-prefixed. Discord
  webhook verified (HTTP 204). All three sizing branches witnessed
  (max_notional clamp on SP500, plain on HIMS, min_notional on ZEC).
- Item 5 (KILL_FLAT at day end) never happened: the Monday process exited
  with the watcher running and the run continued. Fact, not a defect.

### Overnight analysis (user directive Thu 00:43 ET: pull and analyze
### everything tonight, present in the morning)

Ledger snapshot 2026-09-04T04:57:13Z, run still live: 30 entries / 28
closed / 2 open. Everything in hip3-executor `runs/2026-08-31_round2/`
(ANALYSIS.md dual-language + analysis.json every number pinned;
`analysis/round2.py`, `analysis/fetch_round2.py`; venue fills/funding
committed, candle caches gitignored with hashes). Morning-review page
published as an Artifact (see the session-end message). Headlines:

1. ENTRY GATE ADMITS DEAD PATTERNS (mechanics): `rules.evaluate` has no
   forming-bar check; the scanner marks a setup live the instant the
   forming bar's extreme passes the trigger even when that bar already
   broke the prior bar's OTHER side (Type 3 -- skill 3.6; the scanner
   itself sets `invalidated`). The exit side honors `formingType "3"`, so
   the bot enters and exits `invalidation_type3` ~8 s later: MORPHO 1h,
   SPX 4h, xyz:MINIMAX 4h (+ xyz:GOLD, entered wrong-side-first, never
   invalidated, stopped). Re-classified live from venue 1m candles: 4 of
   27 non-1-3 entries. FIX STAGED on executor branch
   `fix/entry-invalidated-bar` (cbea184: `entry_bar_invalidated` journal
   reason mirroring the exit predicate, rev3 exempt, 5 regressions,
   95/95) -- NOT merged, NOT deployed.
2. FLIP EXIT EARNS ITS KEEP, second sighting: 18 flips, 12 stop-first
   after exit (+19.2pp observed savings), 1 target-first (GRAM 4h,
   -2.5pp), 5 unresolved. The 00:00-UTC coupling is REAL BY CONSTRUCTION
   (scanner ftfc = forming close-vs-open on 15m/1h/4h/1d, all four; at
   the roll they share one open, one tick flips all four -- skill 4.5):
   9/18 flips inside the first hour after a 4h/1d open vs 25% base, but
   those nine exited near flat and the "young bars can't vote" variant
   sums -0.19pp vs +0.66pp actual. Mature-bar flips: 8/9 stop-first,
   -7.5pp actual vs -17.0pp bracket-only.
3. BOOKS TIE TO THE VENUE within $0.003 and PIN THE EQUITY FORMULA (README
   item b closed): HL spot `hold` = every isolated position's `marginUsed`
   which already carries uPnL -> true equity = spot USDC total (all-
   isolated). `account_value()` adds main-dex perp `accountValue` on top:
   $101.83 shown vs $99.20 real; journal `account` ran $1-7 high with a
   main-dex position open. One-line reporting fix, not coded yet.
4. ACCURACY: 28/28 pattern sequences and triggers re-derive exactly from
   venue candles. Two scanner-vs-tape disagreements on the two thinnest
   prior bars (PAXG 0.094%: scanner-only Type 3, the forming bar unions
   MID ticks with candles per loop.js setCandles; xyz:GOLD 0.25%: the
   mirror) -> a-priori design question: minimum prior-bar range.
5. CUT TOO SOON / HELD TOO LONG: no evidence of early bailing; 9 trades
   reached >= 0.5% MFE and closed <= 0 (JUP +4.71% = 65% of target ->
   -0.63% flip after 13.3h) = the runner/partial lane (TVB-13), prereg
   territory. 2 of 4 target exits had a T2 within 24h.
6. TFC: the 440 `ftfc_not_aligned` refusals simulate WORSE than the taken
   book (-0.025 vs +0.136%/trade) -- weekend-1's confirmation-lag pattern
   did NOT recur (one sighting for, one against).
7. LEDGER: 9 wins (32%), 5 material; gross +$0.13, fees $0.73, funding
   $0.23 (ACE alone $0.21 = 2.1% of notional over 20.6h), NET -$0.82;
   payoff 2.62 -> breakeven 27.6%. Conts 0/5 with near-bank targets
   (0/12 cumulative). rev-short 5/11 +$0.39 the only paying quadrant.
   Sizing: max_notional clamp under-risks tight-stop gold-class tickets
   (fees 12-86% of the $0.10-0.25 budgets); min_notional over-risks wide
   stops (ACE $1.49). Gates census: reach gate refused 2-for-22 (-60.9pp
   sim); missing-ATR refused the PONS lottery; drift veto's pool positive
   only via 8 trades; RTH clock refusals zero-mean; R:R floor class as
   weekend-1 (69% winners, negative mean).
8. RULING NEEDED: scanner 1-3 Rev Strat trigger = inside bar far side
   (where the 3 completes) vs skill R22 reclaim of the broken side (SOL
   4h this week). Surfaced, not decided.

Analysis-script review (fresh-context feature-dev code-reviewer agent,
adversarial brief, ran the script and recomputed against raw fills):
2 CONFIRMED + 1 minor, ALL FIXED before the final commit, zero disputes.
(1) `excursions`/`first_touch` skipped the 1m candle CONTAINING the start
instant (`c.t < start_ms` vs a minute-aligned `t`), so the two
same-minute 8-second trades (MORPHO, PAXG) had null MFE/MAE and every
trade lost a boundary minute -- fixed to skip only candles fully closed
before the start; (2) the 1-2-2 token accepted either 2U/2D for the trap
bar instead of the direction-opposite one skill 3.2 requires -- fixed
(`2opp`); all three 1-2-2 trades still match; (3) sparse-candle entries
read `wrong_side_first` False instead of unknown -- now None. Re-run:
EVERY headline number unchanged (flip 12/1/5, +19.19pp, coupled 9/18,
decoupled -0.19 vs +0.66, accuracy 28/28, net -$0.82); the give-back
medians moved and were corrected in ANALYSIS.md and the Artifact
(material winners' MFE median 102% of target distance, losers 19%; the
draft's "winners 80%" had mixed scratch exits into the winner set). The
reviewer also verified fill matching (TAO 3 / MORPHO 2 / GRAM 2 / SPX 2 /
JUP 1+open, no cross-trade leakage), sign conventions both directions,
the decoupled loop, pool dedup on a chronologically sorted journal,
reconciliation scope (no prior-run fills), and the tracker join (28/28,
12 orphan keys are weekend-1 trackers).

### Friday morning (user, 2026-09-04 ~11:00 ET): fix DEPLOYED, run continues

User: "go ahead and implement the fix". Merged `fix/entry-invalidated-bar`
into executor main (e2a91ad, 95/95), README STATUS rewritten (4b5d248 --
probes/e/f closed with venue data, equity formula pinned but fix NOT
coded, new gate documented). Live loop stopped with Ctrl-C in tmux
(KeyboardInterrupt during poll sleep; brackets venue-resident),
deploy_from_dev.ps1 run (PS 5.1 `2>&1` trap fired on uv's stderr again --
the remote side had completed; remote_setup.sh re-run idempotently, VPS
suite 95/95), restarted `--live` 15:08:14Z with `source_sha 4b5d248`
from DEPLOYED_SHA, zero protection/entry-block rows after restart. The
equity-display fix and the 1-3 trigger ruling remain open (user chose to
discuss next session). User's verdict on round 2 so far: "pleasantly
surprised with the performance".

### Design seeds the user raised for TVB-33 (their words, paraphrased --
### discuss, do not pre-decide)

1. Entry/exit mechanics across timeframes: for a DAILY pattern, enter on
   the daily with T1/T2 as the only exits -- or enter on the daily, drop
   to the 1h targets first, and once those are taken (targets overlap
   across timeframes) step up 2h -> 4h -> 8h -> 12h, "bumping up our
   timeframe with how the trade is trending"? Maps to the skill's pivot
   ladder / DP1-WP1 confluence language; the walk-up is a management
   profile question (R15), prereg territory.
2. Candidate selection in big trends: massive crypto runners print
   2U-2U-2U-2U even on the daily; the rev-only + escalate-cont universe
   never sees a pure continuation chain. "Could have been improved."
3. Visualize the trades (still owed -- the standing
   trader-visualization gap) before trusting "true performance".
4. Second-guessing two round-2 rulings given the CURRENT REGIME (much of
   the move is overnight, geopolitics-driven): (a) crypto only when BTC
   is "green" (the daily-open drift veto), (b) equities only in RTH.
5. Later, not now: basic regime identification for metals (silver/gold)
   and for tech vs the 2y/10y yield levels.

### Files (this repo)

- `docs/HANDOFF.md` (this entry), `.session_startup_prompt.md` (TVB-33),
  `docs/reviews/REVIEW_REQUEST.md` (TVB-32 request). No Pine changed;
  no request.security touched.

### Open

- [x] Merge + deploy `fix/entry-invalidated-bar` (closed TVB-32 Friday:
      e2a91ad merged, 4b5d248 deployed, restarted 15:08Z).
- [ ] Equity-display fix: `account_value()` = spot USDC total while
      all-isolated; verify once vs the HL app.
- [ ] 1-3 Rev Strat trigger ruling (scanner far side vs skill R22 reclaim).
- [ ] TVB-33 design discussion: timeframe walk-up for daily-pattern
      targets; continuation-chain runners; the BTC drift veto and RTH-only
      xyz under the overnight regime; pattern breakdown.
- [ ] Visualize the round-2 trades (user: still owed before trusting
      "true performance").
- [ ] Design-lane preregs (a-priori only): minimum prior-bar range;
      min stop distance / fee-aware R:R for clamped tickets;
      runner/partial-harvest profile; funding-aware holding cost.
- [ ] Weekend decision: run continues (crypto 24/7, xyz RTH-gated) unless
      the user says KILL_FLAT; refresh the ledger snapshot when the run
      closes so the analysis is on a CLOSED ledger.
- [ ] Month-end fresh-window regen (overdue since ~Sep 1).
- [ ] TVB-31 audit unreturned (docs/reviews/tvb31-codex-audit.md absent);
      TVB-32 requested; tvb8/tvb9 unreturned.
- [ ] Carried: TV mirror on demand; TVB-18 repairs; jackson set_inputs fix;
      metals (silver/gold) + tech-vs-yields regime identification (user,
      later).

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb32-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: REQUESTED (2026-09-04)
- Commits to review: this repo `5b194a2..7a29dad` on `main` (docs only:
  9507928, d2f2a24, 7a29dad; the pin commit after 7a29dad is outside the
  range by construction -- RANGE-PIN RULE: `5b194a2..X` keeps every
  session commit since 5b194a2 was the TVB-31 pin; sanity-checked with
  `git diff --name-status` = 3 paths). hip3-executor (PRIVATE, local transport
  only, `C:\Strat_Trading_Bot\hip3-executor`): `fd4db97` (LF deploy fix),
  `35a73a4` + `2dc9490` + `68dca79` (round-2 analysis + review fold),
  `cbea184` (fix branch) merged as `e2a91ad`, `4b5d248` (README STATUS);
  deployed sha 4b5d248.
- Scope / what changed: round-2 go-live ops (deploy defect + fix,
  probes), the overnight ledger analysis (analysis/round2.py, ANALYSIS.md,
  analysis.json), the entry-gate fix (rules.py + 5 tests), README STATUS.
- Focus areas (scrutinize these): finding 1's mechanism and the fix
  placement; the equity-formula reading of HL spot hold; the flip
  proxy / coupling split / decoupled counterfactual; fill matching; the
  pools census; the accuracy census; prose discipline (characterization
  only; run LIVE at snapshot); no Pine changed.
- Reviewed by: pending (in-session: analysis/round2.py reviewed by a
  fresh-context code-reviewer agent, 2 confirmed + 1 minor, all fixed)
- Findings: {blank until docs/reviews/tvb32-codex-audit.md exists}
- NOTE: the TVB-31 request was never returned; both remain open.

---

## Session TVB-31: scanner deploy verified w/o redeploy; HyPaper spike; TVB-30 audit (BLOCK) folded (COMPLETE)

**Date:** 2026-08-30
**Status:** COMPLETE -- three work blocks: (1) the scanner Railway item
resolved by VERIFICATION, not deploy; (2) the HyPaper adoption spike
(docs/experiments/tvb31_hypaper_spike.md, 0d7437c); (3) the TVB-30 audit
returned BLOCK and was folded same-day across all three repos (all
merges done: executor 4e384bb, this repo 371c37d, scanner PR #10 merged
@ 7723462). Two new dated user rulings 2026-08-30. Monday go-live
checklist unchanged and now unblocked through the VPS-deploy step.

### Scanner Railway item (startup checklist item 2) -- resolved, no deploy

Cont targets are ALREADY LIVE: the live payload serves cont signals with
targets (xyz:XYZ100 live 2D-1-2D, entry 29580 / stop 29595 / target
29544), live display_v d9cb6247159c52f8 matches local main exactly, and
everything merged since PR #1 (PRs #5/#6) is docs/parity/tests/npm-alias
only. `railway up` deliberately SKIPPED: a no-op redeploy restarts the
worker and resets in-memory alert state the day before go-live.
Verification ticks all green: /health ok (279 coins), payload probe,
SMOKE GREEN vs the live URL, local extract:check + 354/354.

### HyPaper spike (docs/experiments/tvb31_hypaper_spike.md)

Verdict: adoptable for continuous multi-strategy paper on MAIN-DEX
CRYPTO ONLY, not drop-in. (a) zero builder-dex support end to end (meta/
mids/asset-map are main-dex only); (b) three SDK blockers, all small --
/exchange demands a `wallet` field the SDK never sends (400 on every
action; ~30-line shim), trigger orders are DEAD via the API (route
validation rejects non-limit wires while the engine's own trigger path
sits unreachable; ~2-line upstream patch), HTTP-400-on-err reads as
ambiguous BrokerError not OrderRejected; broker.py needs a base_url
config and HyPaper mode must run perp_dexs=[""] (it ignores the dex
param on reads -- our re-prefixing would mint phantom xyz positions);
(c) fills are mid-cross detected but priced by REAL L2-book VWAP with
maker/taker split + 8h live funding -- more realistic than PaperBroker
-- with named optimisms: triggers fire on MID not MARK, maker fills on
touch (no queue), no partials, no liquidation engine. Key value
unchanged: it runs the REAL LiveBroker code path (where HIGH-1 hid) and
per-wallet auto-created accounts = the user's parallel-strategies goal.
Orthogonal to Monday's live run.

### External review fold -- critical synthesis (TVB-30 audit, verdict BLOCK)

The audit returned 2026-08-30: BLOCK, 0 CRITICAL / 4 HIGH / 4 MEDIUM /
4 LOW. All four HIGHs were again executor live-safety defects inside the
boundary TVB-30 claimed folded; the auditor's summary -- "the TVB-29
fold is not ready for a supervised live run" -- was CORRECT. Every
finding REPRODUCED before adjudication: 10 executor no-network probes
10/10 -> 0/10 after the fold, M4a/M4b/L1/L2 primary probes all
reproduced (L1 via the exact formula mechanism on P1-shaped
half-fraction fee_sides; committed rows predate the fp fields), L4
confirmed statically (the mutation test never spawned the runner). ZERO
disputes. Fold commits: executor 4e384bb (pushed, 90 tests, was 64),
this repo 371c37d (287 tests, was 280), scanner PR #10 (d0fe9e7, 356
tests; MERGED by user same day @ 7723462).

Where we agree (everything, with receipts):

- HIGH-1 (partial IOC close read as complete): market_close discarded
  totalSz; every caller deleted the record and cancelled the stop on ANY
  nonzero fill -- a partial left a NAKED UNTRACKED residual (probe: 0.3
  residual, failed_closes=[], stop stripped). Fixed: market_close proves
  flat with a fresh dex-scoped query INSIDE the broker or raises
  (underfilled = unresolved); every caller already handles the raise --
  record kept, stop kept, KILL_FLAT books it failed and retries.
- HIGH-2 (failed poll + cancel-all): with pre_poll down, KILL_FLAT
  flattened tracked names then ran the GLOBAL cancel sweep anyway -- an
  unseen survivor's stop was stripped (probe: GHOST's stop gone). Fixed:
  scope-unknown skips the sweep entirely (receipt order_sweep:
  skipped_scope_unknown); only proved closes lose their orders.
- HIGH-3 (scalar entry_block): the untracked writer's clear erased the
  pending-intent block while state["pending_entry"] persisted (probe:
  block None, intent retained), and _enter could overwrite the only
  durable handle. Fixed: independent keyed blocks (intent / untracked /
  protection), each writer owns exactly its key, the intent block
  re-derives from persisted state EVERY cycle with reconciliation
  retried (announce-throttled), and _enter refuses while an intent
  exists (pending_intent_unresolved).
- HIGH-4 (coin/oid-only stop proof): a same-coin/oid row with wrong
  side, size, price, type, and reduceOnly=False verified as protection
  (probe: True); 1000.0-vs-1000.9 passed the 0.1% size tolerance. Fixed:
  _orders_state moved to frontendOpenOrders (rich rows, dex param
  intact) and the predicate proves the FULL contract -- reduce-only,
  isTrigger, "Stop" orderType, close side, remaining-size coverage to
  half a size step, venue-rounded trigger price; missing fields read
  UNPROTECTED; mutation-tested per attribute; the engine size compare is
  half a step (was 0.1% relative); restore updates stop_venue and
  re-proves the contract fresh. Venue field VALUES asserted from SDK
  docs -- confirm against a real resting bracket in the supervised probe
  (added to README STATUS open list).
- M1 (boundary sizing): exactly-$10.00 and $10.40 tickets floored to
  $9.45 and self-rejected (probe digit-for-digit). Fixed: quantize
  first, ceil-repair ANY under-minimum result, cap guard unchanged.
- M2 (kill-flat scanner touch): live KILL_FLAT fetched scanner state
  (15s timeout exposure) before the broker. Fixed: LIVE never touches
  the scanner (the live broker ignores mids); the paper twin keeps the
  best-effort fetch for its fills.
- M3 + USER RULING 2026-08-30 (warn-only): a failed/incomplete leverage
  confirmation was swallowed silently. Fixed: leverage_unverified
  journal + announce with the reason (query_failed /
  position_not_visible / leverage_fields_missing); entries NEVER block
  on it (risk is set by the stop; matches the risk-drift ruling shape).
- NEW USER RULING 2026-08-30 (the audit's unstated question): the
  max-notional cap binds the PRE-TRADE estimate; the ACTUAL fill
  notional rides every entry receipt (notional_usd_filled) and warns
  past 5% over the cap -- never auto-closed.
- M4 (this repo, t1floor): blank/commas-only --arms resolved to ZERO
  arms with every gate passing vacuously; the default expectation
  tracked a mutated NEW_ARMS; dict-keying erased production
  multiplicity. Fixed: CANONICAL_ARM_IDS literal + NEW_ARMS assertion,
  absent-vs-explicit-empty distinction (empty components hard-error),
  produced-sequence multiset gate before any dict collapse; tests pin
  the eight ids literally.
- L1 (this repo): per-symbol nets subtracted the ROUNDED display fee
  from full-precision P&L (0.0001pp drift on P1 half-fraction rows).
  Fixed: _net_fields helper -- every net derives from the unrounded fee,
  rounds once; regression distinguishes the two formulas exactly.
  EXPECTED DELTA: committed results_by_symbol rows keep the staged
  values until the month-end regen re-pins them (same treatment as the
  TVB-30 LOW-1 rollup delta).
- L2 (this repo): rollup fallback silently zeroed an open row's missing
  MTM, propagated NaN into JSON, and one old row flipped EVERY row to
  rounded display fees. Fixed: fail-closed finiteness validation, open
  rows REQUIRE an MTM value, row-wise fee fallback.
- L3 (executor): any nonempty DEPLOYED_SHA text became provenance.
  Fixed: 40-hex or journaled deployed_sha_invalid; four vectors pinned.
- L4 (scanner): the parity mutation test re-implemented the comparison
  inline and never executed run_parity.js -- deleting the preflight left
  every test green. Fixed (PR #10): the new test spawns the ACTUAL
  runner against a poisoned tmp replica, asserts exit 1 + STALE message
  + the poison never executed; META-CHECKED (deleting the preflight
  fails exactly this test).

New dated user rulings this session (2026-08-30): (1) leverage
unverified = journal + announce, warn-only, never blocks entries;
(2) actual-fill notional = receipt every entry + warn past 5% over the
cap, never auto-close.

Suites after the fold: executor 90 (was 64), this repo 287 (was 280),
scanner 356 (PR #10). request.security untouched (no Pine changed --
audit confirmed independently).

### Context for next session

- Go-live checklist unchanged for Monday: executor VPS deploy now at
  4e384bb+ (SSH needs explicit user go), VPS dry-run + KILL_FLAT drill,
  supervised probes (bracket receipt + STOP-CONTRACT field confirmation
  vs a real resting bracket / equity formula with ONE isolated position
  -- STILL UNVERIFIED / first xyz fill + user_fills dex question).
- Scanner PR #10 MERGED (user, 2026-08-30 @ 7723462; test-only, runtime
  untouched -- no Railway deploy needed). The whole TVB-30 fold is now
  on main in all three repos.
- Month-end regen ~Sep 1 now ALSO re-pins the per-symbol L1 net fields
  (net_realized_pp/net_combined_pp staged-vs-round-once, 0.0001pp class)
  alongside the TVB-28/TVB-30 deltas already documented.
- HyPaper adoption decision pending the Monday discussion; the spike doc
  is the input.

### Files created/modified

- This repo: docs/experiments/tvb31_hypaper_spike.md (NEW),
  analysis/paper/tier_b_t1floor.py (M4), analysis/paper/tier_b_exits.py
  (L1 _net_fields + L2 fail-closed rollup), tests/test_t1floor_gates.py
  + tests/test_tier_b_exits.py (new regressions),
  docs/reviews/tvb30-codex-audit.md (NEW, verbatim),
  docs/reviews/REVIEW_REQUEST.md, docs/HANDOFF.md (this entry +
  TVB-24..26 archived to session_archive/HANDOFF_TVB24-TVB26.md),
  .session_startup_prompt.md.
- hip3-executor @ 4e384bb: src/hip3_executor/broker.py + engine.py (the
  whole fold), tests/conftest.py + tests/test_gate_hardening.py (90
  tests), README.md (amendments + rewritten STATUS).
- hip3-scanner PR #10 @ d0fe9e7 (merged 7723462):
  test/parity_extract_check.test.js (runner-mutation test).

### Open

- [ ] Executor VPS deploy at 4e384bb+ via deploy_from_dev.ps1 (SSH needs
      explicit user go), then VPS dry-run + KILL_FLAT drill, deliberate
      rm data/KILL_FLAT, live start (Monday 2026-08-31).
- [ ] Supervised probes = first live trades: bracket receipt + confirm
      the frontendOpenOrders stop-row field VALUES vs a real resting
      bracket (new README STATUS item f); equity formula vs venue UI
      with exactly ONE isolated position (still unverified); first xyz
      fill (dex coin naming + whether user_fills carries builder-dex
      fills).
- [ ] HyPaper adoption decision (Monday discussion; spike doc = input;
      if adopted: trigger-order upstream patch/fork, wallet shim,
      broker.py base_url config, perp_dexs=[""] pin, then one live probe
      bracket).
- [ ] Month-end regen ~Sep 1: re-pins TVB-28 deltas + TVB-30 LOW-1
      rollup fields + NEW TVB-31 per-symbol L1 net fields (0.0001pp
      staged-vs-round-once class).
- [ ] TVB-31 review fold when returned; tvb8/tvb9 unreturned (standing).
- [ ] Carried: TV mirror on demand; TVB-18 repairs; jackson set_inputs
      fix.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work
> (range below) and write a verbatim assessment to
> docs/reviews/tvb31-codex-audit.md. See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: REQUESTED
- Commits to review: `0d7437c^..7bfde0f` on `main` (4 commits, 10 paths:
  HyPaper spike 0d7437c, fold 371c37d, PR-10 docs f8921f4, session-end
  7bfde0f; sanity-checked via `git diff --name-status`). Sibling repos:
  hip3-executor `4e384bb^..4e384bb` (local transport only); hip3-scanner
  PR #10 branch commit `d0fe9e7`, merged unchanged at `7723462`.
- Scope / what changed: TVB-30 BLOCK audit folded across three repos
  (executor safety boundary rework: proved closes, sweep-scope guard,
  keyed entry blocks, full stop-contract verification; this repo arm
  contract + D10 net/rollup; scanner runner-mutation test); HyPaper
  spike doc (claims checkable against the public repo); scanner deploy
  VERIFIED not redeployed.
- Focus areas (scrutinize these): (1) market_close proved-close -- any
  caller where the fresh position query can mislead (same-coin refill
  race, PaperBroker mirror); (2) the scope-unknown sweep skip -- any
  path that still cancels against an unknown position set; (3) keyed
  entry blocks -- any writer that can still clear another owner's block,
  the per-cycle retry throttling, the _enter guard; (4) _stop_row_ok
  semantics: "Stop" substring on orderType, remaining-sz (not origSz)
  coverage choice, triggerPx tolerance, FakeMeta-vs-LiveMeta fidelity,
  frontendOpenOrders-vs-openOrders count parity in requery_flat;
  (5) _sized restructure: fixed-notional path now also min-repairs
  (behavior change, journaled) -- boundary vectors; (6) M4 multiset gate
  placement and CANONICAL literal; (7) _net_fields + row-wise fallback +
  the documented committed-artifact delta; (8) the scanner test's tmp
  replica fidelity; (9) HyPaper spike factual claims; (10) no Pine
  changed -- verify request.security surface untouched.
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb31-codex-audit.md exists)

---

## Session TVB-30: TVB-29 audit (BLOCK) folded before go-live; run deferred to Monday (COMPLETE)

**Date:** 2026-08-28
**Status:** COMPLETE -- the TVB-29 audit (verdict BLOCK, 4 HIGH executor
live-safety) folded same-day across all three repos, every finding
reproduced first, zero disputes, three new dated rulings; the round-2
live run was then USER-DEFERRED to Monday 2026-08-31 (scheduling +
Friday late-day OPEX pinning); HyPaper assessed for the Monday
discussion.

### External review fold -- critical synthesis (TVB-29 audit, verdict BLOCK)

The audit returned 2026-08-28: BLOCK, 0 CRITICAL / 4 HIGH / 6 MEDIUM /
2 LOW. All four HIGHs were hip3-executor live-safety defects inside the
exact round-2 scope; the auditor's own summary -- "the executor pre-live
gate does not hold" -- was CORRECT, and the 2026-08-26 "items 1-7
IMPLEMENTED" claim was over-stated. Every finding was REPRODUCED before
adjudication (16/16 no-network probes against the old code; 0/16
reproduce after the fold). ZERO disputes. Fold commits: executor
a23ac43 (pushed), this repo (this commit), scanner PR #6 (branch
tvb30-parity-gate @ fb1ec84).

Where we agree (everything, with receipts):

- HIGH-1 (dex-blind safety reads): SDK 0.24.0's user_state/open_orders
  take dex="" = MAIN dex only, while the order path was perp_dexs-aware
  -- writes succeeded into a universe the reads could not see. Probe:
  a fake venue holding an xyz:TSLA position + resting order yielded a
  clean {positions:0, open_orders:0} KILL_FLAT proof. Fixed: every
  venue read sweeps every configured dex (coin-name prefix = dex
  identity), requery_flat proves zero/zero ACROSS dexs with a by_dex
  breakdown, and a builder-dex-only exposure fixture pins that a clean
  receipt is impossible.
- HIGH-2 (unknown read as flat): position_for mapped ANY query
  exception to None = "confirmed absent"; startup then cleared the
  intent while a real position sat live (probe H2b); a BrokerError
  after a sent order cleared the intent with the position live (H2c);
  market_close accepted an unfilled close (H2d/H2e). Fixed: tri-state
  lookup (present / absent / raises), OrderRejected = the ONLY
  definite-rejection class that skips reconciliation, unfilled closes
  raise, and intents clear only after a fresh zero-position zero-order
  proof. Live cloid downgrade is journaled.
- HIGH-3 (no post-entry stop verification): verify_resting was called
  exactly once, in the entry sequence; a stop canceled/rejected later
  left the position naked indefinitely (probe H3b: no reaction). Fixed
  + USER-RULED 2026-08-28 (restore, else flatten): every poll rechecks
  venue side/size vs the record and the stop's presence in the cached
  cross-dex order set; a missing stop is re-placed once and verified
  fresh, else the position is closed (protection_lost); mismatch or an
  unclosable naked position blocks entries.
- HIGH-4 (KILL_FLAT gaps): the kill file was checked AFTER feed.state()
  -- a scanner outage aborted the cycle before flattening (probe H4a);
  a failed close was followed by an unconditional cancel-all that
  stripped the survivor's stop (H4b). Fixed: kill honored before any
  feed dependency (mids best-effort), failed closes KEEP their coin's
  protective orders (cancel_all skip set + failed_closes in the
  receipt), clean requires no failed closes.
- M1 (sizing): the $10 min-clamp floored its own size back under $10
  (probe: $9.45 at mid 105 -> self-reject below_min_notional) -- a
  systematic skip, exactly as the audit said. Fixed + USER-RULED
  2026-08-28 (receipt + warn): min tickets ceil to a valid size step,
  one-step-over-cap refused min_ticket_exceeds_max_notional, entries
  receipt stop_venue + risk_usd_booked (actual fill x actual size x
  venue-rounded stop), RISK DRIFT alert past 1.5x budget, never
  auto-close.
- M2 (exit identity): an unmatched closing-fill OID was relabeled
  "stop" by the survivor heuristic (probe reproduced). Fixed: an
  explicit closing fill classifies by OID alone; unmatched, partial
  (size-unreconciled), or wrong-direction fills defer to unknown_exit;
  survivor heuristics only when no fill is visible. The audit also
  caught our test fixture: ENTRY_MS sat TWO DAYS after ENTRY_TS, so the
  pre-entry exclusion test never tested the exclusion -- now derived
  from ENTRY_TS, and the pre-entry fill carries the sl_oid so a filter
  regression would visibly misclassify.
- M3 (reach fail-open): missing ATR silently passed the reachability
  gate; the exception lived in code comments, never a dated ruling.
  USER-RULED 2026-08-28: fail closed, reason reach_unavailable
  (targetless entries untouched). Prereg amendment recorded in the
  executor README.
- M4 (gate status over-claim): leverage was "verified" by a bare
  status:ok; account_value keeps the TVB-27-flagged sum; source_sha
  came only from rev-parse (an archive deploy journals a PARENT repo's
  HEAD). Fixed: post-fill venue leverage confirmation (mismatch
  journaled + announced, venue values persisted), rev-parse trusted
  only when ROOT/.git exists with DEPLOYED_SHA consumed otherwise, and
  the README STATUS rewritten to say what is STILL OPEN -- the equity
  formula is UNCHANGED and UNVERIFIED until the supervised
  one-isolated-position probe.
- M5 (this repo, t1floor): the produced-vs-requested check was
  CIRCULAR -- `requested` was re-derived from the already-filtered arm
  list, so "--arms D1,ZZ" silently selected D1 and passed. Fixed:
  _resolve_requested_arms validates the RAW CLI request (unknown /
  duplicate ids are hard errors) and the scope gate compares against
  that independent expectation; selector-mutation regressions added
  both directions; the smoke redirect now compares resolved paths.
- M6 (scanner): the parity harness require()d its committed extraction
  blind -- the exact stale-copy failure TVB-29 said to exclude.
  Fixed: run_parity.js derives the expected module from the HTML in
  memory and byte-compares BEFORE loading (proved end-to-end: a
  mutated copy exits 1 before any network call); extract_core.js gains
  build() + --check; npm run parity:check; HTML-mutation test pinned.
- LOW-1 (this repo): roster rollups summed 4dp-rounded per-symbol
  display fields. Fixed: full-precision realized_fp/open_mtm_fp ride
  every rec, the rollup aggregates those and rounds ONCE (D10 holds
  end to end), with a fallback for pre-amendment recs; a fractional
  three-symbol vector (0.12344 x3 -> 0.3703 not 0.3702) pins it. The
  committed round artifacts keep their last-digit drift until the
  month-end regen re-pins them (documented expected delta).
- LOW-2 (scanner): the single-pivot cont vector could not catch a
  first-qualifying scan-order mutation; two-pivot vectors both
  directions now assert the price-NEAREST pivot wins.

New dated user rulings this session (2026-08-28, recorded in the
executor README prereg amendments): (1) reach fail-closed
(reach_unavailable); (2) risk drift = receipt + warn at 1.5x budget,
never auto-close; (3) naked stop = restore once verified, else flatten,
entries blocked while unprotected.

Suites after the fold: executor 64 (was 35), this repo 280 (was 275),
scanner 354 (was 349). request.security untouched (no Pine changed --
audit confirmed independently).

### Context for next session

- The go-live checklist (.session_startup_prompt.md) remains the
  contract, now unblocked by the fold: scanner PR #6 merge + railway
  deploy, executor VPS deploy (a23ac43+), VPS dry-run + KILL_FLAT
  drill, supervised probes (bracket / equity formula with ONE isolated
  position -- still the open half of gate item 6 / first xyz fill),
  manual KILL_FLAT at 18:00 ET.
- Builder-dex coin naming in dex-scoped venue responses is normalized
  defensively (re-prefixed if bare) but the first xyz probe should
  confirm the venue's actual naming.
- Month-end regen ~Sep 1 now ALSO re-pins the LOW-1 full-precision
  rollup fields alongside the TVB-28 deltas already documented.

### HyPaper assessment (user-raised 2026-08-28, for the Monday discussion)

github.com/GigabrainGG/HyPaper (MIT, Node/TS + Redis, ~29 stars /
17 commits -- young): a drop-in paper-trading twin of the HL API --
swap the base URL, add a wallet field, no signing; a worker fills paper
orders on every live WS mid tick with maker/taker fees at live rates,
8h funding from live rates, GTC/IOC/ALO, cancel-by-cloid,
updateLeverage; /info mirrors HL (paper user-state + proxied live
market data). Why it is interesting HERE: our dry-run exercises
PaperBroker, a parallel twin -- the TVB-29 audit itself noted the
dry-run can never reveal LiveBroker defects (HIGH-1 hid exactly there).
Pointing LiveBroker at HyPaper would run the REAL, just-hardened code
path (dex-scoped reads, tri-state reconcile, resting-stop verify,
KILL_FLAT proofs) continuously against a simulated venue; multiple
wallets = multiple strategies on one ticker. Open questions before any
adoption (a spike, not a rewrite): (1) builder-dex support -- does it
serve xyz:* assets and dex-scoped user_state/open_orders/meta, the
exact seam we just fixed; (2) SDK compatibility -- the Python SDK signs
actions, HyPaper wants unsigned JSON + wallet field; (3) fill realism
is mid-cross (optimistic vs spread/queue) -- still better than our
poll-cadence mid fills with no fees/funding; (4) new infra (Redis +
Node service). Neighbors seen: chainstacklabs/hyperliquid-trading-bot
(grid bot + SDK examples, not a paper venue), horn111/hip4-mm-simulator
(HIP-4 MM queue modeling, different problem).

### Files created/modified

- hip3-executor (a23ac43, pushed): broker.py (dex_of/_dex_name, dex-swept
  pre_poll/verify_resting/position_for/open_orders_for/cancel sweeps/
  requery_flat by_dex, OrderRejected + _parse_status classification,
  market_close raises on unfilled, stop_resting_cached, place_bracket
  sl_px, OID-only explain_exit), engine.py (_kill_flat_cycle,
  _flatten_all failed-set, _verify_protection, tri-state intent
  reconciliations, OrderRejected split, ceil-step _sized, risk receipt +
  warn, post-fill leverage confirm, DEPLOYED_SHA provenance), rules.py
  (reach_unavailable), config.py comment, README (amendments + honest
  STATUS), tests/ (conftest, test_broker, test_rules,
  test_gate_hardening NEW; 64 total).
- hip3-scanner (PR #6, branch tvb30-parity-gate @ fb1ec84): parity/
  extract_core.js (build() + --check), parity/run_parity.js (in-memory
  byte-compare preflight), package.json (parity:extract/parity:check),
  test/parity_extract_check.test.js NEW, test/core_v3.test.js
  (two-pivot nearest-wins vectors); 354 tests.
- This repo (aa1c795, c2bf6ea, 41a542d + session-end): tier_b_t1floor.py
  (_resolve_requested_arms + independent requested set + resolved-path
  smoke redirect), tier_b_exits.py (realized_fp/open_mtm_fp +
  aggregate-then-round rollup), tests (t1floor M5 regressions, exits
  fractional-precision vectors; 280 total), audit recorded, HANDOFF
  synthesis + HyPaper assessment, startup prompt, archive
  HANDOFF_TVB22-TVB23.md.

### Open

- [ ] MONDAY 2026-08-31: discussion (HyPaper adoption + parallel
      strategy comparison shape), then the go-live checklist
      (.session_startup_prompt.md) -- scanner PR #6 merge + railway
      deploy first
- [ ] HyPaper spike decision (xyz-dex + SDK-compat probe before any
      adoption; assessment above; user goal: multiple parallel
      strategies on the same tickers, results compared)
- [ ] user_fills has NO dex parameter in SDK 0.24.0 -- whether
      builder-dex fills appear in it is UNVERIFIED; exit classification
      falls back to unknown_exit if not, but confirm on the first xyz
      fill
- [ ] Month-end fresh-window regen ~Sep 1 (adds LOW-1 fp re-pin)
- [ ] Carried: TV mirror on demand; TVB-18 repairs; jackson set_inputs
      fix; tvb8/tvb9 unreturned

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb30-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: REQUESTED
- Commits to review: this repo `aa1c795^..60bc7de` on `main` (4 commits,
  9 paths: audit recorded aa1c795, fold c2bf6ea, Monday-deferral docs
  41a542d, session-end 60bc7de; caret keeps aa1c795 in the diff,
  sanity-checked via `git diff --name-status`). Sibling hip3-executor
  (PRIVATE, local path C:\Strat_Trading_Bot\hip3-executor):
  `a23ac43^..a23ac43` (one commit, the whole executor fold). Sibling
  hip3-scanner (PRIVATE, HIP-3-Solutions org): branch `tvb30-parity-gate`
  @ `fb1ec84` (PR #6; merged to main 2026-08-30 @ 6a7a53c, scoped files
  identical).
- Scope / what changed: the TVB-29 BLOCK audit folded in full (4 HIGH +
  6 MEDIUM + 2 LOW, all reproduced first via 16 no-network probes);
  three new dated user rulings 2026-08-28 (reach fail-closed, risk
  receipt+warn 1.5x, stop restore-else-flatten); live run deferred to
  Monday; HyPaper assessed.
- Focus areas (scrutinize these): (1) dex-scoping COMPLETENESS -- did
  any venue read escape the sweep? user_fills notably has NO dex param
  in SDK 0.24.0 (explain_exit depends on it; flagged Open); (2) the
  OrderRejected definite-vs-ambiguous split in _parse_status -- is
  status:"err" truly always nothing-placed on this venue?; (3)
  _verify_protection: restore path re-places at rec["stop"] for
  abs(venue szi) -- any wrong-size/wrong-price hole, and the
  entry_block interplay between the untracked/protection writers; (4)
  _kill_flat_cycle ordering incl the venue_ok fallback to tracked
  records and the clean = zero/zero AND no-failed-closes rule; (5)
  ceil-step sizing math and the risk receipt/warn (min-clamp
  interaction); (6) t1floor _resolve_requested_arms + the independent
  requested set -- truly non-circular now?; LOW-1 fp rollup incl the
  pre-amendment fallback; (7) scanner parity preflight -- any path that
  still loads the committed copy without the byte-compare; the
  two-pivot vectors' correctness; (8) request.security: NO Pine changed
  -- verify.
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb30-codex-audit.md exists)

---

## Session TVB-29: TVB-28 audit folded + round-2 design session + pre-live gate LANDED (COMPLETE)

**Date:** 2026-08-26..28
**Status:** COMPLETE -- the TVB-28 audit folded same-day (all 8 findings
reproduced first, zero disputes), the round-2 design session produced five
dated user rulings + a prereg BEFORE code, and the entire executor
pre-live gate + rule changes landed with a new 35-test suite. Round-2
live test (Fri 08-28, ~$100, crypto + xyz equity perps to 18:00 ET) is
staged for TVB-30.

### What was accomplished

- TVB-28 AUDIT FOLD (this repo ddca002/7b4ae6a/3fb0631; executor
  7d4fd86): critical synthesis in the TVB-28 External Review block below.
  Highlights: D9 executable-only USER RULING (membership 58 -> 45, the 13
  inert armings ride floor_armed_inert; events byte-identical); receipt
  relabeled FIRST-FILL diagnostic (delta_vs_first_fill_pct); t1floor
  _gate_scope caller contract + staged event promotion + smoke redirect
  (the canonical 8-arm CLI had been failing its own hardened gate);
  round-once roster net algebra + invariant test; executor census medians
  corrected (statistics.median, 9v18/6v20 denominators, decision-clock
  membership, STX exemption), backing-target counterfactual IMPLEMENTED
  + receipted (7/7 stop-first stands; 6/7-within-0.2pp corrected to 4/7),
  MMQB language pass, README INTENDED-vs-CURRENT + gate items restored.
- ROUND-2 DESIGN SESSION (plan mode, trader-terms questions anchored on
  real weekend trades -- STX cont walkthrough, MOVE/CHIP vs kFLOKI):
  five dated USER RULINGS 2026-08-26 prereg'd BEFORE code (executor
  f986716 "Ruleset v1"): (1) cont targets = pivot-ladder near bank,
  scanner-side; (2) symmetric stand-aside vs BTC daily-open sign; (3)
  risk-normalized $0.50/trade (min $10 / max $100 notional clamps); (4)
  reachability 1.5x daily ATR, all targeted entries (stated consequence:
  conts fall under the rr floor once targeted); (5) universe = crypto +
  xyz during underlying RTH. AMENDMENT 2026-08-28 (user-ruled): drift
  veto scoped to main-dex crypto -- BTC's color never vetoes an equity
  perp (36d5541). User flags recorded in the prereg: short window = weak
  evidence; -6.85 vs $50 budget = refinements not repairs; STRAT-vs-algo
  boundary answered in writing.
- SCANNER CONT TARGETS (hip3-scanner PR #1, branch tvb29-cont-targets @
  dccfd06 -- the repo moved to the HIP-3-Solutions org, main is PR-only
  now): contTarget() in the HTML STRAT-CORE block wires the existing
  pivotTarget() into the cont branches (3-2 measured-move fallback);
  extract:check OK, 346/346 node tests, Python parity mirror updated,
  parity harness 125 live pairs + 12 aggregations ZERO mismatches
  (NOTE: the parity harness keeps its OWN extraction -- regenerate
  parity/extract_core.js too or parity lies), bar-level hand checks
  (TSLA 352.02 pivot / MSFT 487.19 / NVDA fallback).
- PRE-LIVE GATE LANDED (executor 60d57a7, all 7 items + tests): entry
  fail-closed (persisted intent + cloid before any order, resting-stop
  re-query, ANY-exception reconciliation, entry_block on untracked
  positions/failed reconcile, startup intent reconciliation); KILL_FLAT
  venue-authoritative union flatten + cancel-all + durable zero/zero
  kill_flat_receipt (dirty result never announces success); NEW HIGH
  found in design exploration: the Type-3 invalidation exit was DEAD
  CODE all weekend-1 (engine compared formingType == 3 int vs the
  scanner's string "3") -- fixed + pinned; leverage response verified;
  exit identity (closing-fills-after-entry, VWAP by oid, tp_oid-None
  guard); P/L rebuild-then-append double-count fixed; provenance
  (startup journals source SHA + config + uv.lock hashes; lock now
  committed; deploy script archives git HEAD only, refuses dirty trees).
  Rule changes wired: risk sizing, drift gate, reachability gate, xyz
  RTH clock gate + SDK perp_dexs routing (incl "" main dex -- verified
  live that meta(dex="xyz") serves prefixed names). 35-test pytest suite
  (fake broker, payload fixtures, no network); local dry-run poll
  verified against the live scanner (880 keys baselined, provenance row).
- Memory: new standing feedback memory (trader-visualization gap: design
  questions in trader terms + bar-by-bar walkthroughs are the
  verification tool).

### Context for next session

- TVB-30 = the Friday live run. Go-live checklist is in
  .session_startup_prompt.md: scanner PR merge + railway deploy FIRST
  (cont targets don't exist live until then), executor VPS deploy (new
  git-archive script; SSH needs explicit user go), VPS dry-run + KILL_FLAT
  drill, deliberate rm data/KILL_FLAT, supervised probes (bracket /
  equity formula with one isolated position / first xyz fill), manual
  KILL_FLAT ~18:00 ET. Agent wallet ACTIVE (user confirmed 08-28).
- Month-end regen ~Sep 1 re-pins rollups with MORE than fee fields:
  corrected collision census (P2 14/9, PX 21/10, prot+tgt 45) +
  collision_receipts + fee_sides + net-from-roster-fee algebra. All
  deltas documented in the report amendments.
- User_Notes.md stays untracked.

### Files created/modified

- This repo: analysis/paper/engine.py (executable-only D9 +
  floor_armed_inert + first-fill receipt), tier_b_t1floor.py
  (_gate_scope + staged promotion + smoke redirect), tier_b_exits.py
  (roster net algebra + fee_sides), tests (+5 = 275), report/prereg/
  ARM_LEDGER amendments, .gitignore (smoke dirs), audit committed,
  HANDOFF synthesis, session docs.
- hip3-executor: README (Ruleset v1 prereg + amendment + gate STATUS +
  safety model), config.json/config.py (5 new fields), engine.py,
  broker.py, rules.py, deploy/deploy_from_dev.ps1, tests/ (NEW, 35),
  uv.lock committed, analysis/weekend1.py + ANALYSIS.md + analysis.json
  (audit fold regen).
- hip3-scanner: hip3_strat_screener.html STRAT-CORE + regenerated
  src/strat_core.js + parity/strat_core_extracted.js +
  parity/reference.py + test/core_v3.test.js (branch tvb29-cont-targets,
  PR #1).

### Open

- [ ] TVB-30: run the Friday round-2 live test per the go-live checklist
      (scanner PR merge + deploy, executor VPS deploy, dry-run + drill,
      probes, 18:00 ET KILL_FLAT)
- [ ] Month-end fresh-window regen ~Sep 1 (re-pins collision census +
      receipts + fee algebra; expected deltas documented)
- [ ] TVB-29 review fold when returned (incl the drift-scope amendment
      and the gate implementation)
- [ ] Equity-side drift reference: deliberately unchosen (future a-priori
      design decision)
- [ ] Runner profiles past T1: future prereg lane
- [ ] Carried: TV mirror per arm on demand; TVB-18 repairs bundle; M+T
      PMG+ nudge; jackson set_inputs fix; tvb8/tvb9 unreturned

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb29-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED (2026-08-28, verdict BLOCK: 0C/4H/6M/2L; folded in
  TVB-30 -- critical synthesis in the TVB-30 entry)
- Commits to review: this repo `ddca002^..7531a12` on `main` (4 commits,
  14 paths; caret keeps ddca002 in the diff; sanity-checked via
  `git diff --name-status`; the pin commit after 7531a12 is routing,
  out of range). Sibling hip3-executor (PRIVATE, local path
  C:\Strat_Trading_Bot\hip3-executor): `7d4fd86^..36d5541` (audit fold,
  Ruleset v1 prereg, gate + rules, drift amendment). Sibling
  hip3-scanner (PRIVATE, HIP-3-Solutions org): branch
  `tvb29-cont-targets` @ `dccfd06` (PR #1).
- Scope / what changed: TVB-28 audit fold (both repos), Ruleset v1 prereg
  + five rulings + drift amendment, scanner cont targets (PR #1), the
  full pre-live gate implementation + 35-test suite.
- Focus areas (scrutinize these): (1) executable-only D9 semantics vs the
  ruled definition (satisfiable = could fire; the 45/13/17 split); (2)
  the t1floor _gate_scope contract -- does the caller-level exact-set
  check truly preserve LOW-2's protection; (3) entry fail-closed paths
  (any exception class that still escapes?); (4) KILL_FLAT receipt --
  can any path announce success without the fresh zero/zero proof; (5)
  scanner contTarget correctness vs pivotTarget semantics + the parity
  harness's own extraction; (6) sizing clamp math (min/max notional,
  risk actually booked); (7) request.security: no Pine changed -- verify.
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb29-codex-audit.md exists)

---

## Session TVB-28: Weekend-1 analysis + BOTH audits folded + D9 re-ruling (COMPLETE)

**Date:** 2026-08-24..26 (spans the /clear on 08-24; audit returned 08-25)
**Status:** COMPLETE -- the weekend-1 ledger analyzed in the binding
dual-language form, the TVB-27 external audit returned and folded same
session, the twice-deferred TVB-26 fold executed with a user re-ruling,
and the collision-receipt instrument landed. All work pushed both repos.

### What was accomplished

- WEEKEND-1 LEDGER ANALYSIS (hip3-executor commits c8e65f4..2daf6a4 +
  corrections dd1a591, e782e57; report runs/2026-08-22_weekend1/
  ANALYSIS.md + analysis.json + analysis/weekend1.py): books reconcile
  against the venue TO THE CENT (52.60 - 6.0327 closedPnl - 0.8082 fees
  - 0.0084 funding = 45.7507 vs 45.75); 4 unknown_exit rows reclassified
  from venue fills (3 target / 1 stop -> true mix 15 flip / 9 stop /
  8 target / 2 kill_flat); flip exits: 14/15 observed stop-first after
  exit, 0 target-first, observed savings +17.34pp = +$5.20 (XMR
  +12.38pp quarantined as unresolved scenario); conts 0/7 with the
  structural no-TP fact scoped from the sample outcome; rr-floor census
  (904 aligned refusals, 68.9% winners, mean -0.154%/trade gross =
  tiny-target/reclaim class as named by TVB-22); fees $0.81 = 0.040% of
  notional (not the TVB-1 churn regime); account-field double-count
  found + verified (exact when flat, +~1 margin lot per open position).
- MMQB + CONVICTION CENSUSES (user-requested; ddbd9d0, 21bd2a9): rails-
  blocked pool (211) sims WORSE than the taken book (-0.843 vs
  -0.595%/trade) -- no flattering survivorship; stack-blocked pool (256)
  +0.238%/trade BUT median -0.28% and top-8 = 93% of profit
  (confirmation-lag question, one regime, upper-bound census); kind x
  direction decomposition: rev-long +$1.11 NET (6/13) vs all other
  quadrants negative (third sighting of the short-whipsaw signature);
  conviction census REFUTED the intuitive tier -- winners had NEAR
  targets (median 1.59% vs losers 4.48%) and LOWER R:R at fill (1.09 vs
  1.87); per-trade risk was a 32x accident of stop distance
  ($0.12-$3.83) -> risk-normalize before any tier.
- TVB-27 AUDIT RETURNED 2026-08-25 (NEEDS-CHANGES: no CRITICAL, 2 HIGH /
  7 MEDIUM / 2 LOW) and FOLDED same session. Critical synthesis: the
  audit reproduced EVERY published number, then correctly flagged (and
  we accepted): the flip headline mixed observed savings with an
  unresolved scenario (MEDIUM-3, corrected + full-precision aggregation);
  my match_fills size check was a no-op bug (MEDIUM-2, now a hard
  assert, passes on real data); MMQB language over-claimed fair-swap/
  population inference (MEDIUM-4, reframed as upper-bound census with
  the auditor's flip-proxy calibration recorded -- median 2.36h late, no
  fixed sign, brackets-only +0.435%); mechanics-boundary language pass
  (MEDIUM-5); candle-cache "committed" docstring corrected (MEDIUM-7);
  wallet-inventory + webhook echo fixed (LOW-1); weekday erratum -- the
  run was SAT 08-22 -> MON 08-24 UTC (LOW-2, annotated in place here).
  The 2 HIGH executor lifecycle defects (bracket not fail-closed;
  KILL_FLAT can announce success unverified) + 4 MEDIUMs are now the
  BINDING round-2 pre-live gate in hip3-executor README. DISPUTED:
  nothing material. Scope note: the review was pinned at 2daf6a4, so
  the conviction census (21bd2a9) is UNREVIEWED -> in the TVB-28 range.
- TVB-26 FOLD (owed since 08-17, df291ef; all four findings REPRODUCED
  first): MEDIUM D9 -- the "books the worse fill by design" claim is
  FALSE per-bar (PX-fresh counterexample verified to the tick: shared
  level 1184.2, i3 close-fill 1184.4 BETTER; own sign census 4 worse /
  2 better of 6; auditor 16-bar replay 7/9); USER RE-RULING 2026-08-24:
  risk-first STANDS as a priority CONVENTION, not a pessimism guarantee
  -- relabeled in report Finding 5, prereg (append-only dated
  amendment), ARM_LEDGER; prot+tgt membership corrected 56 -> 58. NEW
  INSTRUMENT: the engine emits per-collision candidate-fill RECEIPTS
  (classes, candidate fills incl gap rules, executed fills, signed
  deltas) into recs + rollups; tests pin the audit counterexample class.
  LOW-2 two-way arm-set gate + mutations; LOW-3 round-once roster fee
  from fee_sides; LOW-4 stop_src_ts regression-bound. 270 tests pass.
- DESIGN SEEDS for round 2 (user questions answered in-session):
  strat-methodology loaded -- the cont-target idea (walk UP timeframes
  incl atypical aggregations to find the containing structure) maps to
  the skill's R14/R18 continuation-magnitude rule; committed
  counterfactual: inheriting the escalation-backing target changes
  NOTHING (all 7 conts still stop first; backing structures +1.4% to
  +27.6% away) -> the design question is a NEAR bank + reachability.
  position-sizing-risk loaded -- sizing amplifies edge, never creates
  it; notional-vs-leverage distinction recorded.
- USER REGIME FRAMING recorded (ANALYSIS.md operator context): the
  window was post-ignition digestion after the best 1-2 days in crypto
  in years -- a mild edge case; the DESIGN regime (in position when
  momentum ignites; shorts exit via stop/invalidation/flip and reverse)
  went untested by this window.

### Context for next session

- FIRST TASK: the round-2 design session (plan mode ON) -- cont-target
  contract, regime/direction input, risk-normalized sizing, pre-live
  gate implementation plan. All rule changes are dated USER rulings.
- The pre-live gate is BINDING: no live run until the 2 HIGH + 4 MEDIUM
  executor fixes land. Agent approval expired ~08-29; rm data/KILL_FLAT
  deliberately before any future run.
- Next canonical regen re-pins rollups with collision_receipts +
  fee_sides + round-once fee (expected deltas: P1 fee 1.0002->1.0000
  July, 0.6502->0.6500 fresh).
- User_Notes.md at repo root is the user's personal untracked scratch --
  leave untracked, never sweep into a commit.

### Files created/modified

- This repo: analysis/paper/engine.py (+receipts), tier_b_exits.py,
  tier_b_t1floor.py, tests (+5), docs/experiments/tvb25_exit_round_
  report.md + prereg (D9 corrections), docs/ARM_LEDGER.md,
  docs/reviews/tvb27-codex-audit.md (committed), REVIEW_REQUEST.md,
  HANDOFF annotations, .session_startup_prompt.md.
- hip3-executor (PRIVATE): analysis/weekend1.py + analysis.json +
  ANALYSIS.md (analysis, censuses, audit corrections, operator context),
  runs README, repo README (pre-live gate), deploy/set_webhook.sh,
  venue/ ground truth (fills/funding/ledger committed; candle cache
  gitignored).

### Open

- [ ] Round-2 design session -> dated rulings + prereg (cont targets,
      regime input, sizing, pre-live gate plan)
- [ ] Pre-live gate implementation in hip3-executor (2 HIGH + 4 MEDIUM;
      BINDING before any live run)
- [ ] Month-end fresh-window extension through 2026-08-31 24:00 UTC
      (~Sep 1; regen re-pins rollups with receipts/fee_sides)
- [ ] TVB-28 review fold when returned (incl the conviction census,
      unreviewed by the TVB-27 audit)
- [ ] Agent re-approval + deliberate KILL_FLAT removal before round 2
- [ ] Carried: TV mirror per arm on demand; assessment owner decisions;
      TVB-18 repairs bundle; M+T PMG+ nudge; jackson set_inputs fix;
      tvb8/tvb9 unreturned

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb28-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED 2026-08-26 (docs/reviews/tvb28-codex-audit.md;
  NEEDS-CHANGES, 0 CRITICAL / 0 new HIGH / 7 MEDIUM / 1 LOW; flipped at
  TVB-29 session start; critical synthesis owed by the folding session)
- Commits to review: this repo `4a07107^..9a964e1` on `main` (6 commits,
  13 paths: the TVB-27 scope-extension docs commits + the fold commit
  df291ef + session-end docs 9a964e1; sanity-checked via
  `git diff --name-status`; the pin commit after 9a964e1 is routing,
  out of range). Sibling hip3-executor (PRIVATE, local path
  C:\Strat_Trading_Bot\hip3-executor): `21bd2a9^..e782e57` -- the
  conviction census (EXPLICITLY unreviewed by the TVB-27 audit, which
  was pinned at 2daf6a4), the audit-fold corrections dd1a591, and the
  operator-context addendum e782e57.
- Scope / what changed: TVB-26 fold (D9 relabel + user re-ruling +
  collision receipts + 3 LOW fixes + 5 tests); TVB-27 fold (analysis
  corrections, pre-live gate); conviction census; session docs.
- Focus areas (scrutinize these): (1) the collision-receipt emitter --
  candidate fills incl gap rules and mid-race prot arming, executed-row
  capture, no behavior change to the race itself (all committed streams
  must replay byte-identically; only NEW fields appear in recs/rollups
  on the next regen); (2) D9 relabel fidelity across report/prereg/
  ledger vs the audit's finding and the 2026-08-24 re-ruling; (3) the
  round-once fee change (P1 1.0002->1.0000 expected on regen -- verify
  no committed artifact was modified THIS session); (4) the conviction
  census method + claims (near-target/anti-R:R finding, 32x risk
  dispersion) under the same upper-bound caveats the TVB-27 audit
  enforced; (5) the corrected ANALYSIS.md staying inside the
  mechanics-test boundary; (6) request.security: no Pine changed --
  verify.
- Reviewed by: Codex CLI (GPT-5), returned 2026-08-26; FOLDED by TVB-29
  same day (this repo ddca002 + 7b4ae6a; hip3-executor 7d4fd86)
- Findings / critical synthesis (TVB-29): ALL EIGHT findings reproduced
  or confirmed BEFORE adjudication -- several digit-for-digit -- and
  accepted with ZERO material disputes. The auditor first revalidated
  our evidence base (suite 270 green, full tier_b_exits replay, 20
  event streams byte-identical, the 58 memberships, the D9 signs), so
  every finding attacks the instrument/contract layer, not the P&L.
  - M1 REPRODUCED live: the canonical 8-arm t1floor caller fails its
    own hardened 6-arm gate on A1F/D1ATR (probe confirmed), with event
    files written pre-abort into the canonical dir; smoke runs also
    wrote there unsuffixed (our finding, same class). FIX: _gate_scope
    caller contract (produced==requested both ways + family-scoped gate
    maps), staged event promotion after all gates, smoke out-dir
    redirect, 3 real-shape caller regressions.
  - M2 REPRODUCED exactly (58 members; 13 with no executable protective
    exit: July P2 4/18, July PX 5/21, fresh P2 2/10, fresh PX 2/9).
    USER RULED 2026-08-26: EXECUTABLE-ONLY -- corrected membership 45
    (14/16/8/7), the arming-only transitions ride the new
    floor_armed_inert counter (17 roster-wide: the 13 + 4 on bars never
    collision-labeled). Event streams verified byte-identical under the
    fix; report/prereg/ledger amended (dated); canonical rollups re-pin
    at the month-end regen. Also explains the earlier 56-vs-58 split
    (exact-pair vs superset counting).
  - M3 REPRODUCED (the PX-July NBIS receipt scores BF +0.9pp "vs
    executed" when BF was 60% of the actual path). USER RULED: honest
    FIRST-FILL diagnostic -- field renamed delta_vs_first_fill_pct,
    every both-ways claim narrowed; path-aware pricing deferred behind
    a prereg.
  - M4 CONFIRMED (e782e57 was prose-only) and the counterfactual is now
    IMPLEMENTED with per-trade touch receipts + candle-cache sha256 in
    analysis.json: 7/7 stop-first STANDS; the 6/7-within-0.2pp claim
    did NOT reproduce -- corrected to 4/7 full precision (STX's venue
    stop filled 1.0pp past its level; KAITO-down flipped 0.9pp before
    its stop). ANALYSIS.md header cache claim corrected.
  - M5 REPRODUCED exactly: med() picked the upper middle on even
    samples (losers 4.48->4.465, R:R 1.87->1.745, align 108->104.5 /
    69->68.4); denominators 9v18 + 6v20 now disclosed; frozen-rule
    membership recomputed on the DECISION-time clock (same five coins
    -- accidental parity, now stated); pre/post-freeze separated; the
    STX targetless cont is exempt from the R:R gate and carries -3.84
    of the -5.45 pre-freeze pp ("the process ruled it away" corrected).
    Every census DIRECTION survives correction.
  - M6/M7 ACCEPTED: causal/controlled-swap language rewritten to
    upper-bound-census framing; README safety model states INTENDED vs
    CURRENT per line until the gate lands; the two silently-shortened
    gate requirements (durable KILL_FLAT zero/zero receipt;
    candle/touch-receipt provenance) restored from the TVB-27 audit's
    original wording.
  - LOW-1 CONFIRMED: roster net now = roster gross minus the single
    round-once roster fee, rollup returns fee_sides, invariant test
    pins the algebra (drift case 2.9988 vs 2.9989 constructed).
  - DISPUTED: nothing material.
  - Regen note for the month-end extension: the canonical rollups now
    re-pin with MORE deltas than previously listed -- receipts +
    fee_sides + round-once fee (P1 1.0002->1.0000 July etc.), PLUS
    net fields becoming gross-minus-roster-fee, PLUS the corrected
    collision census (P2 14/9, PX 21/10, prot+tgt 45) and
    floor_armed_inert. All expected, all documented in the report
    amendments.

---

## Session TVB-27: Live pivot -- hip3-executor built, VPS-deployed, weekend-1 live test run and closed (COMPLETE)

**Date:** 2026-08-21..24 (multi-day session; user on remote control)
**Status:** COMPLETE -- USER-DIRECTED pivot away from the planned TVB-26
fold: a new PRIVATE repo (hip3-executor) was built from scratch, deployed
to the ATLAS VPS, and traded a dedicated $52.60 Hyperliquid agent-wallet
account live and unattended Fri 14:26 -> Sun 21:58 UTC [erratum
2026-08-26, TVB-27 audit LOW-2: the run days were SAT 08-22 14:26 -> MON
08-24 21:58 UTC; every date/timestamp is correct, the weekday names in
this entry are off by one]. Killed FLAT by
user decision (momentum stalled). Mechanics verdict: PASS on the
pre-registered success metric (enters/sizes/brackets/exits as designed).
The TVB-26 fold was flipped RETURNED at session start and DEFERRED (user
ruling) -- it remains owed.

### What was accomplished

- TVB-26 review flipped RETURNED (audit committed this session-end:
  NEEDS-CHANGES, 1 MEDIUM + 3 LOW; the MEDIUM carries a user checkpoint
  on the D9 risk-first ruling's worse-fill premise). Fold deferred by
  user direction; owed to TVB-28.
- hip3-executor BUILT (github.com/sheehyct/hip3-executor, PRIVATE; local
  C:\Strat_Trading_Bot\hip3-executor; commits e93d748..f4011b6): Python
  3.12/uv + hyperliquid-python-sdk; consumes hip3-scanner /api/state
  (single detection source -- the executor never analyzes bars); paper
  and live brokers behind one interface; venue-resident stop+target
  brackets; software exits (Type-3 invalidation with rev3 exemption,
  ftfc opposite-flip, hold-through-mixed); decision/trade/tracker JSONL
  journals; KILL / KILL_FLAT kill switches; agent wallet signs orders
  only (cannot withdraw -- blast radius = wallet balance); key entered
  only via hidden-prompt scripts in the user's own SSH session, never
  through chat (a mid-session user offer to relax this was declined).
- RULESET v0, all dated user rulings: rev signals on 1h/4h/1d + full
  15m/1h/4h/1d ftfc alignment; transition-based entries with
  per-signal-per-bar dedup + restart baseline; $30 fixed notional,
  isolated 10x (venue max clamp); MAE-clearance (stop inside 0.8/lev or
  skip); full exit at structural T1 + 24h post-exit rung tracking; main
  dex crypto only (xyz excluded -- weekend oracle dynamics), $1M 24h
  volume floor; max 2 concurrent, 60min cooldown, 12 entries/UTC day.
- MID-WEEKEND RULINGS (all dated, all before the Saturday freeze):
  continuation ESCALATE mode (a cont qualifies only with a live in-force
  higher-TF reversal behind it -- the user's "go up in timeframes until
  you find it", mechanized); min_reward_risk 1.0 entry floor (refuses
  the tiny-target/reclaim class the TVB-22 research named; fired on 22
  candidates at first snapshot); operator-grade alerts (dollar
  notional/margin/risk on entry; dollar P/L + unified-account balance on
  exit); hourly Discord P/L report (day resets 00:00 UTC + since-start).
- VPS DEPLOY (ATLAS VPS, atlas@, IP in session chat only -- never
  committed): tar-over-scp deploy kit, remote setup, phone runbook,
  hidden-prompt env + webhook scripts, preflight (derives agent address
  from the key WITHOUT exposing it, checks venue approval + balance --
  caught the user pasting the agent ADDRESS instead of the private key).
- WEEKEND-1 LIVE LEDGER (characterization only -- the pre-registered
  adjudication is mechanics-pass + 52.60 -> 45.75; qualifier added
  2026-08-26 per audit MEDIUM-5): 34 round trips, 9/34 winners, gross
  -6.04 USD; account 52.60 -> 45.75 (-6.85 net incl fees; day P/L by UTC
  date 08-22 -2.01 / 08-23 -0.33 / 08-24 -3.70 [weekdays Sat/Sun/Mon,
  erratum 2026-08-26]); exits 15 ftfc_flip / 8 stop / 5 target / 4
  unknown_exit (all pre-fix first hours) / 2 kill_flat; 11,909 decisions
  journaled. First trades: PENDLE long (bracketed on venue, verified via
  public API) and PYTH long booked AT target to the tick 17s after entry.
- LIVE LESSONS FIXED SAME DAY: Hyperliquid AUTO-CANCELS the reduce-only
  sibling when a position closes (exit classification now matches the
  closing fill's oid); paper positions rehydrate across restarts; a lint
  hook stripped a briefly-unused import between edits (verify against
  the source tree, not the cached build).
- CLOSED FLAT 2026-08-24 21:58 UTC via KILL_FLAT (user decision):
  0 positions, 0 orders verified via public API; canonical ledger
  committed at hip3-executor/runs/2026-08-22_weekend1/ (f4011b6);
  data/KILL_FLAT left on the VPS as a restart interlock.

### Context for next session

- FIRST TASK (user directive): heavy analysis of the weekend ledger,
  BINDING FORM = every finding in both code/automation vocabulary AND
  plain trader English. Seeded questions in .session_startup_prompt.md.
- TVB-26 fold still owed (deferred twice); the MEDIUM needs the user.
- Month-end fresh-window extension ~Sep 1.
- Agent approval expires ~2026-08-29; rm data/KILL_FLAT deliberately
  before any future live run.

### Files created/modified

- This repo: docs/reviews/REVIEW_REQUEST.md + docs/HANDOFF.md (TVB-26
  status flips at session start; this entry + rewritten request at
  close), .session_startup_prompt.md, docs/reviews/tvb26-codex-audit.md
  (returned audit, committed).
- Sibling repo hip3-executor (PRIVATE, all work): full build -- see
  commits e93d748..f4011b6 there.

### Open

- [ ] Weekend-1 ledger analysis, dual-language form (TVB-28 first task)
- [ ] Fold the TVB-26 external review (owed since 2026-08-17; MEDIUM has
      a user checkpoint on the D9 risk-first worse-fill premise)
- [ ] Month-end fresh-window extension through 2026-08-31 24:00 UTC (~Sep 1)
- [ ] Executor round-2 decisions after the analysis (user-owned; agent
      re-approval needed ~08-29; KILL_FLAT interlock on the VPS)
- [ ] Carried from TVB-26: TV mirror per arm on demand + pine header
      wording; assessment owner decisions; TVB-18 repairs bundle; M+T
      PMG+ nudge; jackson set_inputs fix; tvb8/tvb9 unreturned

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb27-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: REQUESTED
- Commits to review: this repo `59cda10^..59cda10` (docs only; the pin
  commit after it is routing, out of range). PRIMARY REVIEW TARGET is
  the sibling repo hip3-executor at C:\Strat_Trading_Bot\hip3-executor
  (PRIVATE remote; local access), range `e93d748^..f4011b6` -- the
  entire executor build, the weekend rulings, and the committed ledger
  (+ post-range docs commit 39255a9, the private ledger README).
- Scope / what changed: live micro-capital executor built + deployed +
  run + closed; this repo carries only status flips and session docs.
- Focus areas (scrutinize these): (1) order lifecycle correctness in
  broker.py (bracket placement, reconcile-on-vanish, oid-match exit
  classification, the never-hold-without-a-stop abort); (2) rules.py
  gates vs the dated rulings (escalation, R:R floor, MAE clearance,
  in-force); (3) ledger integrity -- journals vs venue fills (the
  runs/2026-08-22_weekend1 artifacts; 4 unknown_exit rows predate the
  oid fix, dated); (4) no secrets anywhere in the committed tree; (5)
  the mid-weekend change discipline (every change reporting-side or
  entry-side, dated, none retro-applied).
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb27-codex-audit.md exists)

---

