# CURRENT REVIEW REQUEST -- tradingview-backtesting

> Entry point for external reviewers. If you are Codex (`/review`) or any other
> external review agent pointed at this repo: this file is your work order. It
> always describes the LATEST requested session review and is rewritten by
> `/session-end` each session. The permanent per-session record is the
> `### External Review` block in `docs/HANDOFF.md`; for the CURRENT request,
> this file wins if the two disagree. Full contract:
> `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Status

- Status: REQUESTED  <!-- REQUESTED | RETURNED (audit file written) -->
- Session under review: TVB-4 -- two-layer regime layer built + ablated;
  stand_aside flips Control-B positive at real fees; S8 grey decision
- Requested: 2026-07-03
- Write the audit to: `docs/reviews/tvb4-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `58c3ca9..{pending session-end push}` |

Wider context if useful (pre-58c3ca9, same session): `5359756` (review-workflow
pointer + retire per-commit approval), `9331d89` (TVB-3 review synthesis +
crossed-flag fix + manual guide), `31230fb` (artifact preservation).

## Read first (in this order)

1. `CLAUDE.md` -- epistemic stance + backtest traps (Sections 2, 6).
2. `docs/ATLAS_Timeframe_Continuity_Charter.md` -- Section 0 + Section 3.3
   (two-layer) + Section 8 (grey open question) are the load-bearing parts.
3. `docs/HANDOFF.md` -- the TVB-4 entry at the top (what was done and why).
4. `docs/TVB2_control_AB_rerun.md` -- the "TVB-4 two-layer regime ablation"
   section at the very end (the numbers + predictions scorecard).
5. `docs/EXTERNAL_REVIEW_PROTOCOL.md` -- the reviewer contract.

## Scope / what changed

Two-layer regime Pine (charter 3.3): an HTF M/W/D FTFC gate over the Control-B
execution layer (`pine/baseline_continuity.pine`, TVB-4 rev). `reg_mode` =
off | stand_aside | size_down (grey at fixed a-priori 50%); no regime exit in v1.
Plus the alignment guard (chart TF must tile every enabled gate TF -- Codex TVB-3
finding 1). Regression proven (reg_mode off == the TVB-3 control, all 2811 ref
trades identical). Ablation run matrix + datasheet section; crossed-flag fix in
`analysis/fee_rates_by_dex.py`; new `scripts/tv_{probe,dump}.mjs`; manual
backtesting guide.

## Focus areas (scrutinize these)

1. The regime logic: `f_agg` and `long_permit`/`short_permit`/`size_scale`
   (`pine/baseline_continuity.pine`) -- do off/stand_aside/size_down do EXACTLY
   what the header + datasheet claim (aligned-only permit, grey per mode,
   opposite blocks)?
2. The size_down grey sizing: `qty = strategy.equity * size_scale / close` at
   arm-time -- is it a fair 50%, any look-ahead or equity-timing leak vs the
   percent_of_equity full-size path?
3. The alignment guard tiling math (D/W/M require chart TF to divide 1D;
   intraday gate TFs integer-multiple of chart TF) -- correct and complete?
4. The regression-equivalence claim (reg_mode off reproduces the control
   byte-for-byte) -- is the branch truly inert when off?
5. The ablation READING -- especially P4 (the -8.60% -> +40.26% flip) and the
   S8 stand_aside-beats-size_down conclusion: is it over-claimed on a single
   instrument / single window? Is the P5 late-entry-tax characterization fair?
6. Kind-window compounding method (product(1+pp) over in-window entries, split
   by `e.tp`) -- valid aggregate under 100%-equity sizing?

Standing priorities on ANY TVB review: `request.security` lookahead in Pine
(note: this strategy uses NO request.security -- local `ta.valuewhen` recon),
model fidelity (is the backtest measuring what it claims?), overfitting /
sample-vs-structural reasoning, fee/turnover math.

## Output contract

- Verbatim audit -> `docs/reviews/tvb4-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line` and Pine docs. Never paste a secret/IP/account
  value into a review file.
- The critical synthesis (agree/dispute/act) is written by the NEXT session
  into `docs/HANDOFF.md` -- your job is the honest external read, not the
  final word.
