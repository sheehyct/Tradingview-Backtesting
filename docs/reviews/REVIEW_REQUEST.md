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
- Session under review: TVB-6 -- xyz backfill verified vs HL venue candles + adopted
  as primary; venue gap decomposed (tick-size artifact ~half); MAE/solvency cleared;
  slippage band; re-entry governor v1->v2 built + KEPT by pre-registered rule
- Requested: 2026-07-03
- Write the audit to: `docs/reviews/tvb6-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `43fb973^..9a00d40` (= `1f7815f..9a00d40`; verified: 51 files) |
| tradingview-mcp-jackson (sibling, LOCAL transport only) | `C:\Strat_Trading_Bot\tradingview-mcp-jackson` | `27757bc` (Monaco finder multi-candidate fix) |

RANGE-PIN RULE (Codex TVB-4 finding 1): git ranges EXCLUDE the left endpoint;
pin `{first}^..{head}` (the caret keeps the first session commit -- the TVB-5
review-return flip `43fb973` -- inside the reviewed diff). Sanity-check with
`git diff --name-status <range>`.

## Read first (in this order)

1. `CLAUDE.md` -- epistemic stance + backtest traps (Sections 2, 6).
2. `docs/ATLAS_Timeframe_Continuity_Charter.md` -- Section 0 + Section 5
   (exploration protocol) + Section 8 (the re-entry governor open question this
   session answers provisionally).
3. `docs/HANDOFF.md` -- the TVB-6 entry at the top (what was done and why).
4. `docs/TVB2_control_AB_rerun.md` -- the six TVB-6 sections at the end: backfill
   verification, mechanism peek + tick-size decomposition, xyz-native rows,
   MAE/solvency, slippage band, governor v1/v2 pre-registrations + results.
5. `docs/EXTERNAL_REVIEW_PROTOCOL.md` -- the reviewer contract.

## Scope / what changed

xyz TV backfill cross-validated against Hyperliquid venue candles (97-99%
float-exact OHLCV incl. volume; 7 TIME-PERISHABLE evidence files committed --
HL serves only ~5000 recent candles/interval, these pulls cannot be re-fetched).
Venue gap decomposed: OKX mintick 0.01 vs xyz 0.001 made the "1 tick/fill"
slippage convention charge OKX ~10x more per fill; equal-$ comparison closes
~half the gap. xyz MSTRUSDC.P adopted as primary MSTR chart (user decision).
Short-leg MAE/1x-cash solvency cleared (worst short MAE 8.11% vs +90.5% HL liq
threshold; `analysis/trade_mae.py`). Slippage band {1,10,25,50} ticks. Re-entry
governor: zero-parameter level ratchet (Pine, gov_mode input default off); v1
exposed reset starvation under stand_aside (recorded as a finding); v2
(exec-gate full-opposite-alignment reset) KEPT by the pre-registered keep-rule
(R1E1+gov2 +71.80/+45.71 vs ungoverned +59.96/+34.76 @0.0125 s1/s10).
`scripts/tv_dump.mjs` fail-loud assertions + enriched trade rows (et/xt/ep/xp/
ddp/rnp). NEW `scripts/tv_bars.mjs`, `analysis/verify_xyz_backfill.py`,
`analysis/trade_mae.py` (+8 tests; suite 17/17).

## Focus areas (scrutinize these)

1. `analysis/verify_xyz_backfill.py` method: is 97-99% float-exact on the
   timestamp intersection + 4h closure + internal 15m->60m aggregation
   SUFFICIENT for "genuine venue data"? Is the pre-May-12 15m residual (native
   HL 15m capped) honestly bounded? Are the wick-diff residuals (TV more
   extreme, worst 2.7% one bar) correctly judged immaterial?
2. The tick-size decomposition: is "xyz 10 ticks == OKX 1 tick in $/fill" a
   sound equalizer given near-unity price ratio? Is "roughly half artifact,
   half texture" over-claimed from two configs?
3. `analysis/trade_mae.py`: MAE vs ENTRY off bar extremes (entry-bar extreme may
   precede the intrabar entry -- is "conservative" correct in BOTH directions?);
   HL liquidation model r* = (1+L)/(L*(1+mm)), mm = 1/(2*maxLev); the
   max-survivable-leverage inverse; the cross-check vs TV's per-trade ddp.
4. The governor Pine (`pine/baseline_continuity.pine`): trigger capture as
   high[1]/low[1] +/- tick on the fill bar (is that ALWAYS the live stop's
   level?); same-bar ordering (loss-detection then alignment reset); does
   `strategy.closedtrades.profit` include commission (the "scratch = losing"
   boundary); any repaint/lookahead path introduced.
5. v1 -> v2 amendment epistemics: mechanism-driven interaction fix (reset
   starvation under stand_aside) or post-hoc tuning? Was the v2 keep-rule
   applied exactly as pre-registered (beat ungoverned at BOTH s1 and s10)?
   Are the v1 results honestly retained?
6. Byte-identity regression method: is the 4,308-trade prefix match (et/dir/pp)
   strong evidence the governor-off path is unchanged across pineVersion
   18 -> 19 -> 20?

Standing priorities on ANY TVB review: `request.security` lookahead in Pine
(note: still NONE -- local `ta.valuewhen` reconstruction only), model fidelity
(is the backtest measuring what it claims?), overfitting / sample-vs-structural
reasoning, fee/turnover math.

## Output contract

- Verbatim audit -> `docs/reviews/tvb6-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line` and Pine/TV docs. Never paste a
  secret/IP/account value into a review file.
- The critical synthesis (agree/dispute/act) is written by the NEXT session
  into `docs/HANDOFF.md` -- your job is the honest external read, not the
  final word.
