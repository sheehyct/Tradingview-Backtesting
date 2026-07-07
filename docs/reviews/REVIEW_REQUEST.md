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
- Session under review: TVB-8 -- VBT breadth port Phases 0-4; the Phase-3
  trade-for-trade equivalence gate GREEN on all 8 cells; pp cost-basis
  correction; Q_FLOOR_EPS adjudication; VBT Pro in-workspace install (DMCA
  gitignore guard); Codex TVB-7 fold-in
- Requested: 2026-07-07
- Write the audit to: `docs/reviews/tvb8-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | {pending push -- pinned by the session-end follow-up commit} |

No sibling-repo changes this session.

RANGE-PIN RULE (Codex TVB-4 finding 1): git ranges EXCLUDE the left endpoint;
pin `{first}^..{head}` (the caret keeps the first session commit inside the
reviewed diff). Sanity-check with `git diff --name-status <range>`.

## Read first (in this order)

1. `CLAUDE.md` -- epistemic stance + backtest traps (Sections 2, 6).
2. `docs/ATLAS_Timeframe_Continuity_Charter.md` -- Section 0 + Section 5.
3. `docs/HANDOFF.md` -- the TVB-8 entry at the top (what was done and why).
4. `docs/VBT_BREADTH_PORT_PLAN.md` -- the design of record, including the
   TVB-8 venue amendment and the corrected calibrated facts (pp formula).
5. `docs/TVB2_control_AB_rerun.md` -- the TVB-8 section at the end (gate
   record, pp correction, epsilon-floor adjudication, Phase-4 verification).
6. `pine/baseline_continuity.pine` -- the ported source (pineVersion 20,
   UNCHANGED this session; the simulator claims exact semantic equivalence).
7. `docs/EXTERNAL_REVIEW_PROTOCOL.md` -- the reviewer contract.

## Scope / what changed

The TFC baseline was ported to a Python bar-loop simulator in this repo
(`tfc/` package; user decision moved the port here from vectorbt-workspace,
with VectorBT Pro installed in the untracked venv and ALL VBT Pro material
hard-gitignored -- the remote is PUBLIC). Phase 0 calibrated fill/qty/pnl
conventions dump-driven (zero fill-convention violations on ~20,300 trades;
pp discovered to be COST-BASIS return, not equity return). Phases 2-3 built
the simulator (integer tick-space trigger arithmetic) and the equivalence
comparator; THE GATE IS GREEN: all 8 reference cells reproduce trade-for-trade
(20,429 closed trades, et/xt/dir exact, fills 2.8e-14, both open-position
boundaries). One adjudication: Q_FLOOR_EPS=1e-5 for a single knife-edge qty
floor (scan shows no other trade within 2e-5 of a boundary). Phase 4:
UTC resampler (verified against TV's own 60m/1D files) + HL/OKX providers
(live HL fetch reproduces committed candles exactly on overlap; network tests
opt-in). Codex TVB-7 review folded in (1 LOW actioned). Suite 25 -> 72 tests.

## Focus areas (scrutinize these)

1. **Does the equivalence comparator PROVE trade-for-trade equivalence?**
   (`tfc/equivalence.py`) The prefix rule (xt <= last bar), the tolerances
   (ep/xp 1e-9, q step/2, pv 1e-4, pp 2e-8), and the open-position boundary
   check -- is there an escape hatch where a systematically wrong simulator
   could still pass? Is comparing sim full-precision pv against SERIALIZED
   dump pv at 1e-4 too loose to catch a fee-formula error?
2. **Q_FLOOR_EPS=1e-5** (`tfc/simulator.py`): adjudicated float artifact or
   tuned parameter in disguise? The knife-zone scan (exactly one trade within
   2e-5 of an integer boundary across ~20,300) is the justification -- is the
   scan itself sound (it used sim-chained equity)?
3. **pp cost-basis correction** (`scripts/tfc_qty_calibration.py`, plan +
   datasheet): is pv/(q*ep*(1+comm)) proven by the zero-fee control, and is
   the window_compound.py "~5bp approximation, window comparisons unaffected"
   scoping honest?
4. **Simulator Pine-order fidelity** vs `pine/baseline_continuity.pine`:
   Phase A/B ordering, exits-before-entries, governor capture -> GROSS
   loss-arm -> alignment reset on the same bar, flat-only arming, one-bar stop
   life, gap-through fill at open with qty basis at the slipped stop,
   integer tick-space trigger arithmetic. Any semantic divergence the 8 cells
   would NOT catch?
5. **Providers** (`tfc/providers.py`): HL floor_hit semantics (listing vs cap
   indistinguishable), OKX UTC+8 intraday-only guard, and whether a 2-day
   overlap slice is enough for the "live HL fetch exact" claim.
6. **Resampler** (`tfc/resample.py`): period-start stamping; is "both
   mismatches are the live last bar at capture time" verified or asserted?

Standing priorities on ANY TVB review: `request.security` lookahead in Pine
(note: NO Pine changes this session; slot stays pineVersion 20.0), model
fidelity (is the backtest measuring what it claims?), overfitting /
sample-vs-structural reasoning (the TVB-9 breadth pass is pre-registered,
regime-mapping only, no verdicts off young listings -- user directive),
fee/turnover math.

## Output contract

- Verbatim audit -> `docs/reviews/tvb8-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line` and Pine/TV docs. Never paste a
  secret/IP/account value into a review file.
- The critical synthesis (agree/dispute/act) is written by the NEXT session
  into `docs/HANDOFF.md` -- your job is the honest external read, not the
  final word.
