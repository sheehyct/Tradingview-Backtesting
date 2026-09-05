# CURRENT REVIEW REQUEST -- tradingview-backtesting

> Entry point for external reviewers. If you are Codex (`/session-review`) or any other
> external review agent pointed at this repo: this file is your work order. It
> always describes the LATEST requested session review and is rewritten by
> `/session-end` each session. The permanent per-session record is the
> `### External Review` block in `docs/HANDOFF.md`; for the CURRENT request,
> this file wins if the two disagree. Full contract:
> `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Status

- Status: REQUESTED
  <!-- REQUESTED | RETURNED (audit file written) -->
- Session under review: TVB-33 -- round-2 CLOSE (KILL_FLAT), reject dig,
  round-3 design session (twelve rulings + D1-D12, prereg BEFORE code),
  and the LEDGER REPLAY HARNESS: built in four reviewed slices, round-2
  parity taken from FAIL to PASS through three fidelity amendments, nine
  single-change arms receipted on both closed ledgers.
- Requested: 2026-09-05
- Write the audit to: `docs/reviews/tvb33-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: TVB-31 and TVB-32 (docs/reviews/tvb31-codex-audit.md,
  tvb32-codex-audit.md) were never returned and stay open. For the TVB-32
  reviewer: the 777-row snapshot-slice defect in the overnight analysis
  is documented in the TVB-33 HANDOFF entry (section 1), not silently
  fixed.

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `7a29dad..HEAD` (docs only: 4c9e920 close-out, 7deca94 prereg + ARM_LEDGER family, 6a44e36 HANDOFF, 48bc604 amendment b, then the session-end commit: amendments d-h mirrored, ARM_LEDGER numbers, HANDOFF, this file). No Pine, no code. |
| hip3-executor (PRIVATE github.com/sheehyct/hip3-executor; local transport only) | `C:\Strat_Trading_Bot\hip3-executor` | main `5ba3347` (Ruleset v2 prereg block) and `99620ff` (amendment b). Branch `feat/replay-harness` `5c58e30..b1da068` (NOT merged): analysis/replay/ (16 modules + CONTRACT.md), tests/replay/ (18 files, 1,032 tests, pins.json), runs/2026-09-04_replay1/ (PREREG.md with amendments b-h, parity_round2.json PASS, parity_round2_prefreeze.json and _flat.json = the kept FAIL receipts, parity_weekend1.json FAIL on P5, round2.json, weekend1.json, REPLAY.md), runs/2026-08-31_round2/ closed ledger + venue records, runs/2026-08-22_weekend1/venue/FETCH_RECEIPT.json. Nothing under src/ changed there. Branch `feat/round3-fee-floor` (merged to main): 1ddc19e README "Round 3 config" prereg, 2e877a3 rules/config (the live fee-aware floor + tests + differential cases), 64d8d19 engine shadows / funding receipt / arms row / equity receipt, 4dad7f3 broker equity fix, 38179e3 config.json. |

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0. Then the TVB-33 HANDOFF entry.
2. hip3-executor `runs/2026-09-04_replay1/PREREG.md` (what was declared
   before any number, and the dated amendments b-h) and
   `analysis/replay/CONTRACT.md` (the slice contract + build rulings).
3. `analysis/replay/exits.py` (dot_with_freeze / simulate),
   `analysis/replay/recon.py` (ref_drift + the drift pin in build_view),
   `analysis/replay/allocator.py` (settle_pin), `analysis/replay/parity.py`
   (P0-P6, residual classes), `analysis/replay/__main__.py` (_Context:
   how the pins and the v1 contrast control are wired). hip3-scanner
   `src/loop.js` lines 57-69, 492-501, 548-560, 617-655 (the freeze
   mechanism the sweep model claims to reproduce).
4. `runs/2026-09-04_replay1/REPLAY.md` and this repo's
   `docs/ARM_LEDGER.md` (Live executor family) -- the numbers as stated
   to the user.

## Focus areas (scrutinize these)

1. THE THREE FIDELITY AMENDMENTS are the thing to attack. Each was made
   AFTER a parity FAIL. The claim is that each is calibrated on a served
   field or a journaled fact and never on outcomes; the alternative
   reading is that the control was tuned until it matched. For each:
   (a) roll freeze / sweep model (amendments d, e): is SWEEP_RANK x 75 s
   what loop.js actually does (one queue, TFS order, concurrency 6, 4 s
   "beat", 5 s timer, 30 s retryAfter on failures)? Is fitting SWEEP_MS
   by argmax of served-ftfc agreement legitimate, and does the per-minute
   curve in amendment e support 75 s over 60 s? The withdrawn 10/30 min
   constants scored BELOW no freeze -- was the first calibration wrong or
   the second?
   (b) drift pin (f): does reading the sign from the refusal reason leak
   the live decision into the control in a way that also helps the ARMS
   (A2 excepted)? Is `reached(reason, "kill_switch")` the right boundary
   in the gate order?
   (c) settle pin (g): matched positions free their seat at the journaled
   exit instant when reasons agree OR the mismatch is a declared residual.
   Does this make P1 (entries 100% identical) trivially satisfiable? What
   would P1 look like with the pin off (the third receipt in the HANDOFF
   narrative: 25/32)? Is applying the pin to the ARMS (over as-built
   epochs) defensible, and is switching it off under the weekend-1 v1
   control (h) consistent?
2. Weekend-1 P5: the $0.61 delta is attributed to slippage on PURR and
   STX. Verify the per-trade attribution (parity_weekend1.json
   control_positions vs the trades.jsonl exit rows; `ledger_gross_usd`
   for the reclassified unknown_exit rows). Is "the other 32 net to ~0"
   true, and is leaving P5 as FAIL (watermarked arms) the right reading
   of the prereg?
3. A5: 875 synthetic halfway candidates, all refused, 268 by the in-force
   check at the cross minute's close. Is `one_three.synthesize` timing
   the cross as D4 declares (last second of the cross minute; stop =
   running extreme incl. the cross candle)? Is the "not_beyond_trigger"
   outcome a convention artifact or a real property of the halfway line?
4. A9: net +$3.30 on 32 trades with 11 displaced / 11 admitted. Check the
   fee-aware floor formula (D5 + amendment b rates), that the displaced
   set really is the fee-heavy gold class, and that the whole-book gain
   is the displaced set (-$1.61) rather than admitted winners.
5. A6 walk-up: 10 of 35 holds printed a rung; the walked stop ends them.
   Check pivots.next_rung / build_ladder (40 retained 4h bars, 1w derived
   from dailies) and the stop-first convention on rung candles (c(3)).
6. The parity checks themselves: P0 100% agreement on 22,401 decision
   rows is the strongest claim in the session -- is the gate port in
   gates.py truly line-for-line with rules.evaluate (the differential
   test in tests/replay/test_gates_port.py), and are the journaled-first
   pins (forming_type not_3, htf_backing, drift) hiding gate differences?
7. Prose discipline: every P&L statement in ARM_LEDGER.md and REPLAY.md
   must read as characterization; "receipt" must not become
   "validation"; watermarked weekend-1 numbers must be visibly marked
   wherever quoted.
8. request.security: NO Pine file changed -- verify none did.
9. THE LIVE PORT OF A9 (round 3 goes live on it): rules.net_reward_risk
   vs analysis/replay/gates.py line for line; the dex mapping
   (config.dex_of_uni) vs replay costs.dex_of; the fail-closed
   `fee_rate_unavailable` branch vs Config.__post_init__ (is it really
   unreachable?); the shadows (rr_net in gross mode, fee_rt_pct_coin,
   dwm, poll, funding_rate) and the D6 funding sign convention
   (engine.expected_funding_usd: positive = this side pays); the equity
   fix (broker.account_parts / account_value = spot USDC total) against
   the TVB-32 chain. Amendment 2026-09-04i: is "the receipt used
   dex-default rates" correct, and does it change the A9 reading?

Standing priorities apply (model fidelity; overfitting language; every
census claim stays characterization; nothing here is a promotion).

## Output contract

- Verbatim audit -> `docs/reviews/tvb33-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value:
  the VPS IP and the master wallet ADDRESS must both stay out of the
  audit (this repo is public -- the address lives only in the private
  hip3-executor repo).
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
