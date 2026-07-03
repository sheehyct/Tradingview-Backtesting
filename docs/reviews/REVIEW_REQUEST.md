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
- Session under review: TVB-3 -- stale gate confirmed + fixed; corrected
  controls; margin-call artifact killed
- Requested: 2026-07-02
- Write the audit to: `docs/reviews/tvb3-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `93f16d7..c9919eb` |
| tradingview-mcp-jackson (sibling, `main`; local transport only -- not in the public push) | `C:\Strat_Trading_Bot\tradingview-mcp-jackson` | `55e93f1` |

## Read first (in this order)

1. `CLAUDE.md` -- epistemic stance + backtest traps (Sections 2, 6).
2. `docs/ATLAS_Timeframe_Continuity_Charter.md` -- Section 0 is mandatory.
3. `docs/HANDOFF.md` -- the TVB-3 entry at the top (what was done and why).
4. `docs/EXTERNAL_REVIEW_PROTOCOL.md` -- the reviewer contract.

## Scope / what changed

Gate staleness empirically confirmed and fixed (`ta.valuewhen(timeframe.change(tf),
open, 0)` local period-open reconstruction, replacing stale `request.security`
period opens); TV margin-call deadlock artifact removed (margin 0/0); corrected-gate
2x4 fee sweep REPLACES all TVB-1/2 numbers; sanitized fee-rate script
(`analysis/fee_rates_by_dex.py`); jackson reader debug/DI hardening.

## Focus areas (scrutinize these)

1. The P2a staleness proof method (single-TF isolation -- is the
   simultaneous-close merge interpretation right?).
2. `ta.valuewhen(timeframe.change)` reconstruction edge cases (partial first
   period, non-aligned chart TFs, warmup-na semantics).
3. Whether margin 0/0 hides anything a 1x cash-margin reality would enforce.
4. The corrected-sweep numbers and the Control-B sign-flip reading.
5. The bundled-delta attribution caveat (gate fix + tick offsets + margin
   removal + window tail are not decomposed).
6. `analysis/fee_rates_by_dex.py` sanitization completeness.

Standing priorities on ANY TVB review: `request.security` lookahead in Pine,
model fidelity (is the backtest measuring what it claims?), overfitting /
sample-vs-structural reasoning, fee/turnover math.

## Output contract

- Verbatim audit -> the audit path named under Status (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line` and Pine docs. Never paste a secret/IP/account
  value into a review file.
- The critical synthesis (agree/dispute/act) is written by the NEXT session
  into `docs/HANDOFF.md` -- your job is the honest external read, not the
  final word.
