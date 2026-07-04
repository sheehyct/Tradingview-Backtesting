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
- Session under review: TVB-7 -- governor v2 cross-venue verification (keep-verdict
  upgraded); VBT breadth-port design of record; cost realism (live L2 impact +
  funding model); Codex TVB-6 fold-in incl. the GROSS-arming adjudication
- Requested: 2026-07-04
- Write the audit to: `docs/reviews/tvb7-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `a4e1de8^..557e00d` (5 commits; verified: 33 files) |

No sibling-repo changes this session (jackson `27757bc` from TVB-6 remains
local-transport-only).

RANGE-PIN RULE (Codex TVB-4 finding 1): git ranges EXCLUDE the left endpoint;
pin `{first}^..{head}` (the caret keeps the first session commit -- the TVB-7
cross-venue verification `a4e1de8` -- inside the reviewed diff). Sanity-check
with `git diff --name-status <range>`.

## Read first (in this order)

1. `CLAUDE.md` -- epistemic stance + backtest traps (Sections 2, 6).
2. `docs/ATLAS_Timeframe_Continuity_Charter.md` -- Section 0 + Section 5.
3. `docs/HANDOFF.md` -- the TVB-7 entry at the top (what was done and why).
4. `docs/TVB2_control_AB_rerun.md` -- the four TVB-7 sections at the end:
   cross-venue pre-registration + results, cost realism (L2 + funding), Codex
   TVB-6 synthesis + gross-arming adjudication; plus the CORRECTED MAE table.
5. `docs/VBT_BREADTH_PORT_PLAN.md` -- the approved port design (its "calibrated
   facts" section is spec for the next implementation session).
6. `docs/EXTERNAL_REVIEW_PROTOCOL.md` -- the reviewer contract.

## Scope / what changed

Governor v2 cross-instrument re-verification: pre-registered CV1-CV4, then 16
paired fresh runs (OKX MSTR 15m ctrlB/R1E1 x {0,0.0125} x {s1,s10}; OKX MSTR
60m R1E3 -- floor also Feb-25; BTC 60m R1E3 2.5y). CV2 keep-rule mirror PASS
at both cost points; keep-verdict upgraded provisional -> cross-venue-verified
(MSTR underlying), magnitude path-local. VBT breadth-engine port designed with
user in plan mode and committed as design of record. Cost realism: NEW
analysis/l2_book_impact.py (live xyz L2 sampling; ~90-contract per-fill cost
lands between s25 and s50, weekend-night caveat) and analysis/funding_model.py
(5,124 hourly events; funding inverts the fee gradient, slow cells pay ~2x
churn cells). Codex TVB-6 review folded in (3 LOW all actioned): MAE table
corrected to committed replay; tv_bars.mjs persists tick metadata +
tvb7_symbolinfo.json; governor profit-boundary ADJUDICATED -- profit() is
GROSS of commission (evidence tvb7_diag_gov2_*), all governed results stand
as-deployed, descriptions + port spec corrected.

## Focus areas (scrutinize these)

1. **The gross-arming adjudication** (datasheet TVB-7 synthesis; evidence
   `analysis/reference/tvb7_diag_gov2_{0125,100bp}.json`): is the inference
   chain decisive? (a) trade sequence fee-independent except through profit();
   (b) zero-fee vs fee'd governed sequences identical over 4,191 trades;
   (c) at 1% commission the first 575 trades match exactly, diverging only at
   the qty=0.001 equity floor. Is the qty-floor explanation of the divergence
   sound? Any alternative fee-coupled path into the sequence we missed?
2. **CV pre-registration integrity**: were CV1-CV4 applied exactly as written
   BEFORE the runs; is the upgrade language ("cross-venue-verified on the MSTR
   underlying, NOT universal-structural") honestly scoped; are the paired-run
   tail-matching and one-input-per-step staging sound?
3. **l2_book_impact.py method**: impact-vs-mid as the honest comparable to the
   backtest's fill-at-trigger + s-ticks model; the TV-tick mapping given HL
   5-sig-fig price granularity; is the weekend-night caveat weighted enough,
   or is the "between s25 and s50" headline over-claimed from 20 snapshots?
4. **funding_model.py**: the (et, xt] event join; long-pays-positive sign
   convention; the notional~=equity 1x approximation and product(1+pp-f)
   compounding; is "funding inverts the fee gradient" supported at these
   magnitudes?
5. **The MAE-correction root cause** (pre-final 60m bar export, wick scrub):
   plausible or overclaimed? The committed replay is canonical either way --
   is that framed honestly?
6. **VBT_BREADTH_PORT_PLAN.md calibrated facts**: qty rule, pv formula, fill
   conventions -- spot-check any against the committed dumps; flag anything
   that would make the Phase-3 gate unpassable as specified.

Standing priorities on ANY TVB review: `request.security` lookahead in Pine
(note: NO Pine changes this session; slot stays pineVersion 20.0), model
fidelity (is the backtest measuring what it claims?), overfitting /
sample-vs-structural reasoning, fee/turnover math.

## Output contract

- Verbatim audit -> `docs/reviews/tvb7-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line` and Pine/TV docs. Never paste a
  secret/IP/account value into a review file.
- The critical synthesis (agree/dispute/act) is written by the NEXT session
  into `docs/HANDOFF.md` -- your job is the honest external read, not the
  final word.
