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
- Session under review: TVB-9 -- Phase 5 complete: venue-bar drift pilot
  (band -0.5..-1.3pp); user-approved pre-registration + 144-run breadth
  sweep (regime map); CRCL-governor + MU-short-whipsaw digs; pre-registered
  HTF-index cells (108 runs; H2 refuted -- dead zone is SIGNAL-structural);
  leverage-extreme overlay ($500 account, MAE-clearance)
- Requested: 2026-07-07
- Write the audit to: `docs/reviews/tvb9-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: the TVB-8 request (range `b4bab2c^..db203aa`) was never returned;
  its record lives in the TVB-8 HANDOFF block. Reviewing it alongside this
  range is welcome but not required.

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `f192a14^..5edd5b6` (12 commits; incl. the post-session-end TFC Companion indicator, `pine/tfc_companion.pine`, and its v2 logic-TF-decoupled rewrite) |

No sibling-repo changes this session.

RANGE-PIN RULE (Codex TVB-4 finding 1): git ranges EXCLUDE the left endpoint;
pin `{first}^..{head}` (the caret keeps the first session commit inside the
reviewed diff). Sanity-check with `git diff --name-status <range>`.

## Read first (in this order)

1. `CLAUDE.md` -- epistemic stance + backtest traps (Sections 2, 6).
2. `docs/ATLAS_Timeframe_Continuity_Charter.md` -- Section 0 + Section 5.
3. `docs/HANDOFF.md` -- the TVB-9 entry at the top (what was done and why).
4. `docs/TVB2_control_AB_rerun.md` -- the six TVB-9 sections at the end
   (pilot, pre-registration, breadth results, digs, HTF pre-reg + results,
   leverage overlay). These are the record under review.
5. `docs/VBT_BREADTH_PORT_PLAN.md` -- the design of record (Phases 0-5 now
   complete).
6. `docs/EXTERNAL_REVIEW_PROTOCOL.md` -- the reviewer contract.

## Scope / what changed

Phase 5 of the VBT breadth port executed end-to-end, all runs pre-registered
or explicitly diagnostic: (a) `analysis/tfc_hl_pilot.py` -- MSTR on TV bars
vs HL bars, identical window/config; drift band -0.5..-1.3pp, trade identity
>= 99.2%; binding rule |net| < 1.5pp (gov 2.5pp) = sign-indeterminate.
(b) user-approved pre-registration (universe, cells incl. the E3only
containment control, per-symbol mintick/qty_step conventions, expectations
1-9) committed BEFORE `scripts/tfc_breadth_sweep.py` ran 144 cells over 9
symbols on committed HL 1h pulls. (c) trade-list digs: CRCL governor delta
attribution; MU short-whipsaw mechanism (+ long-only/short-only diagnostic).
(d) pre-registered HTF cells (`scripts/tfc_htf_sweep.py`, MWD_on240/MWD_onD,
matched + native-1d windows): H2 refuted. (e) `analysis/tfc_leverage_overlay.py`:
survival-max isolated leverage by MAE-clearance + $500 account paths.
NO Pine changes (pineVersion 20 anchor untouched); NO simulator changes
(equivalence gate 8/8 green throughout; overlay post-processes trade lists).

## Focus areas (scrutinize these)

1. **Drift-band inference** (`analysis/tfc_hl_pilot.py`, datasheet pilot
   section): 12 cells sharing ~99% of trades are ONE sample, not twelve --
   is the +/-1.5pp (gov 2.5pp) sign-indeterminate rule honest, too tight,
   or too loose? Is anchoring the HL source to the committed TVB-6 pull
   (instead of a fresh fetch) sound?
2. **Pre-registration integrity** (datasheet pre-reg + results sections):
   any cell, symbol, or interpretation that exceeded the declared
   expectations? Is the containment test (R1E3 vs E3only) fair, and are
   the flagged surprises (BTC ctrlA +3.55, TSLA E3only +9.4) handled
   without promotion?
3. **HTF sweep correctness** (`scripts/tfc_htf_sweep.py`, `tfc/resample.py`
   reuse): 240m/1D resampling from 1h (period-start stamping, partial
   first/last days), the native-1d crosscheck (5 mismatched days on MU --
   placeholder explanation asserted, not proven), same-TF D leg semantics
   on a D chart, and whether "SIGNAL-structural" is over-claimed from
   20-37-trade windows.
4. **Leverage overlay math** (`analysis/tfc_leverage_overlay.py`):
   x_liq = 1/L - mm with mm = 1/(2*maxLeverage) -- is that the right HL
   isolated-margin model? MAE window includes the FULL entry bar
   (conservatism direction?); equity compounding as (1 + L*pp) (fees scale
   with notional -- correct?); min-notional death; sample-Kelly grid. Are
   the in-sample caveats sufficient given the "survival" framing?
5. **Short-side weakness claim**: three observations (MU 60m, BTC daily,
   CRCL daily) across overlapping windows and correlated instruments -- is
   "3x repeated" a fair characterization or double-counting one regime?
6. **Evidence hygiene**: ~7MB of raw HL pulls committed to a PUBLIC repo --
   any licensing/ToS concern with redistributing venue candle data?

Standing priorities on ANY TVB review: `request.security` lookahead in Pine
(N/A this session -- no Pine changes; slot stays pineVersion 20.0), model
fidelity (is the backtest measuring what it claims?), overfitting /
sample-vs-structural reasoning (the overfit guards in the HTF and leverage
sections; no keep/kill verdicts off young listings -- user directive),
fee/turnover math.

## Output contract

- Verbatim audit -> `docs/reviews/tvb9-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line` and Pine/TV docs. Never paste a
  secret/IP/account value into a review file.
- The critical synthesis (agree/dispute/act) is written by the NEXT session
  into `docs/HANDOFF.md` -- your job is the honest external read, not the
  final word.
