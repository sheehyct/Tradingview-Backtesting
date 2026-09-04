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
- Session under review: TVB-32 -- round-2 GO-LIVE (Mon 2026-08-31: LF
  deploy fix, KILL_FLAT drill, supervised probes closing README items e/f)
  and the OVERNIGHT ANALYSIS of the still-live ledger (2026-09-04:
  28 closed trades reconciled to the venue; three findings -- entry gate
  admits already-Type-3 bars, flip exit vindicated with the coupling
  mechanism quantified, equity formula pinned; accuracy census; gates
  census; a fix STAGED on a branch, not deployed).
- Requested: 2026-09-04
- Write the audit to: `docs/reviews/tvb32-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: the TVB-31 request (docs/reviews/tvb31-codex-audit.md) was never
  returned and stays open; tvb8/tvb9 remain unreturned (standing note).

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `5b194a2..<TVB-32 session-end commit>` (docs only: HANDOFF TVB-32 entry, startup prompt TVB-33, this file; the pin commit after it names the sha). No Pine, no code. |
| hip3-executor (PRIVATE github.com/sheehyct/hip3-executor; local transport only) | `C:\Strat_Trading_Bot\hip3-executor` | main: `fd4db97` (.gitattributes LF fix -- the deploy defect) and `35a73a4` (analysis/fetch_round2.py, analysis/round2.py, runs/2026-08-31_round2/ incl. ANALYSIS.md + analysis.json + venue fills/funding). Branch `fix/entry-invalidated-bar` @ `cbea184` (rules.py entry gate + 5 tests; NOT merged). |

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0. Then the TVB-32 HANDOFF entry.
2. hip3-executor `runs/2026-08-31_round2/ANALYSIS.md` (the claims) and
   `analysis/round2.py` (how every number is computed; module docstring
   states the conventions). `analysis.json` pins every derived number.
3. hip3-executor `src/hip3_executor/rules.py` on the fix branch (the
   `entry_bar_invalidated` gate) vs `engine._exit_reason`; hip3-scanner
   `parity/strat_core_extracted.js` analyzeTF (`live` + `invalidated`) and
   `src/loop.js` setCandles (mid-union forming bar) -- the two scanner
   facts the findings rest on.

## Focus areas (scrutinize these)

1. Finding 1 (entry gate): is the mechanism as stated -- does the scanner
   really serve a live signal on an already-Type-3 forming bar, and does
   `evaluate` really have no forming-bar check? Is the staged fix placed
   correctly (before R:R, after in-force) and is `sig.rev3` the right
   exemption key? Does the 1m-candle "wrong_side_first" re-classification
   prove what ANALYSIS.md says for MORPHO / SPX / MINIMAX / GOLD?
2. Finding 3 (equity): the chain 99.601466 + closedPnl - fees - funding =
   98.7655 vs spot_total - open uPnL = 98.7685. Is "HL spot hold =
   isolated marginUsed incl. uPnL" a correct reading of the venue, or an
   artifact of these two positions? Is the proposed formula (spot USDC
   total) right for an all-isolated account and what breaks it?
3. Flip analysis: the per-TF reconstruction is a PROXY for the served
   ftfc (14/18 agree). Does the coupled/mature split, the base-rate claim
   (25%), and the decoupled-60 counterfactual hold up? Any sign error in
   `margin_pct` for shorts? Is "12 of 13 resolved flips stop-first"
   computed with the stated stop-before-target convention?
4. Fill matching: entries by `cloid`, exits by coin/time window bounded by
   the next same-coin entry -- can a fill be mis-assigned on TAO (3 closed
   + none open), MORPHO (2), GRAM (2), SPX (2), JUP (1 closed + 1 open)?
   Is the size assertion reachable?
5. Pools census: same upper-bound model as weekend-1 -- are the new pools
   (counter_drift, target_beyond_reach, reach_unavailable,
   underlying_closed aligned subset) filtered and summarized without
   double counting; does `top8_share_of_sum` mean what the prose says?
6. Accuracy census: strict-break classification, `htf_before` picking the
   bars immediately before the entry bar, the `PATTERN_TOKENS` map vs the
   signal names present, the 1-3 trigger convention statement (scanner
   `entry: L.h` for bullish) -- verify against the scanner source.
7. Prose discipline: every P&L statement must read as characterization;
   "second sighting" claims (flip exit, R:R floor class) must not become
   validation language; the run was LIVE at snapshot -- is that stated
   everywhere a reader would need it?
8. request.security: NO Pine file changed -- verify none did.

Standing priorities apply (model fidelity; overfitting language; every
census claim stays characterization; nothing here is a promotion).

## Output contract

- Verbatim audit -> `docs/reviews/tvb32-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value:
  the VPS IP and the master wallet ADDRESS must both stay out of the
  audit (this repo is public -- the address lives only in the private
  hip3-executor repo).
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
