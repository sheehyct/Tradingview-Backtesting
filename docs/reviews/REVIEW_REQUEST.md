# CURRENT REVIEW REQUEST -- tradingview-backtesting

> Entry point for external reviewers. If you are Codex (`/session-review`) or any other
> external review agent pointed at this repo: this file is your work order. It
> always describes the LATEST requested session review and is rewritten by
> `/session-end` each session. The permanent per-session record is the
> `### External Review` block in `docs/HANDOFF.md`; for the CURRENT request,
> this file wins if the two disagree. Full contract:
> `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Status

- Status: REQUESTED  <!-- REQUESTED | RETURNED (audit file written) -->
- Session under review: TVB-5 -- S8 ratified; pre-registered 3x3 TF-set sweep
  across 4 samples (35 runs); regime layer characterized as universal damage
  containment; xyz-vs-OKX venue gap flagged (unverified)
- Requested: 2026-07-03
- Write the audit to: `docs/reviews/tvb5-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `b99dccb^..d622be1` (= `6c855cf..d622be1`; verified: 57 files) |

RANGE-PIN RULE (Codex TVB-4 finding 1): git ranges EXCLUDE the left endpoint;
the caret in `b99dccb^..` keeps the first session commit (ratification +
review fold-in) inside the reviewed diff. Sanity-check with
`git diff --name-status <range>`.

## Read first (in this order)

1. `CLAUDE.md` -- epistemic stance + backtest traps (Sections 2, 6).
2. `docs/ATLAS_Timeframe_Continuity_Charter.md` -- Section 0 + Section 5
   (exploration protocol) + Section 6 (the "correlated follower" failure mode,
   observed empirically this session).
3. `docs/HANDOFF.md` -- the TVB-5 entry at the top (what was done and why).
4. `docs/TVB2_control_AB_rerun.md` -- the TVB-5 sections at the end:
   ratification, reproducibility re-run, sweep PRE-REGISTRATION, sweep RESULTS
   (tables, scorecard, surprises).
5. `docs/EXTERNAL_REVIEW_PROTOCOL.md` -- the reviewer contract.

## Scope / what changed

S8 ratification (stand_aside; reg_mode stays input, default off). Codex TVB-4
fold-in: `scripts/tv_dump.mjs` closed-basis L/S fix; range-pin rule in
session-end; all six TVB-4 ablation rows re-run + committed (`tvb5_R*.json`).
Pre-registered 3x3 timeframe-set sweep (regime {M/W/D, W/D/12h, D/12h/4h} x
exec {60/30/15, 240/60/15, 240/120/60}, all stand_aside) across four samples:
OKX MSTR Feb-Jul grid; OKX BTC 15m Dec-Jul; OKX BTC 60m 2024-2026; xyz
MSTRUSDC.P Dec-Jul (venue comparison). NEW `analysis/window_compound.py`
(+tests): window-sliced product(1+pp) compounding over dump trade lists.
29 sweep dumps committed under `analysis/reference/tvb5_*`.

## Focus areas (scrutinize these)

1. `analysis/window_compound.py` method validity: is product(1+pp) over CLOSED
   trades ENTERED in-window the right aggregate under 100%-equity sizing? Open
   -trade exclusion, half-open window semantics, ms timestamps.
2. The tv_dump closed-basis assumption (`scripts/tv_dump.mjs`): is
   `reportData().trades` guaranteed entry-ordered with open positions at the
   END, so `first totalTrades entries == closed set`?
3. The sweep READING (datasheet TVB-5 RESULTS): are "universal damage
   containment" and "regime speed is monotone-destructive" over-claimed from
   9 cells x 4 samples? Is the anti-selective fast-regime mechanism read sound?
4. The venue-gap surprise: is the shared-window xyz-vs-OKX comparison
   methodologically sound (same fee model, method-matched compounding, trade
   counts 2708 vs 2815)? Is the unverified-provenance caution adequate, or is
   any language already over-trusting the xyz backfill?
5. Pre-registration integrity: the in-flight amendments (SP500USDC.P no-backfill
   -> BTC fallback per the pre-registered rule; W-venue upgrade to full-window
   runs + analytical slicing) -- justified deviations or result-driven drift?
6. The S8 ratification arithmetic (~zero-expectancy suppressed stream:
   1.8470/1.7663 over ~1,892 trades vs 0.025% round-trip cost).

Standing priorities on ANY TVB review: `request.security` lookahead in Pine
(note: this strategy uses NO request.security -- local `ta.valuewhen` recon;
Pine unchanged this session), model fidelity (is the backtest measuring what it
claims?), overfitting / sample-vs-structural reasoning, fee/turnover math.

## Output contract

- Verbatim audit -> `docs/reviews/tvb5-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line` and Pine/TV docs. Never paste a
  secret/IP/account value into a review file.
- The critical synthesis (agree/dispute/act) is written by the NEXT session
  into `docs/HANDOFF.md` -- your job is the honest external read, not the
  final word.
