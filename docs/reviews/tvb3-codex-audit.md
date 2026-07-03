<!--
External review of TVB-3. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-3 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of `tradingview-backtesting` range `93f16d7..c9919eb` plus
> sibling `tradingview-mcp-jackson` commit `55e93f1`, captured 2026-07-03
> (TVB-3 post-session). Lightly ASCII-normalized; wording and code otherwise
> unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate
> control vs variant, or over/under-state a risk. The critical synthesis --
> where we agree, dispute, and act -- is in `docs/HANDOFF.md`. Read that
> alongside this.

---

## 1. Metadata

- **Session:** TVB-3 -- stale gate confirmed + fixed; corrected controls; margin artifact killed
- **Reviewed:** `tradingview-backtesting` `93f16d7..c9919eb`; `tradingview-mcp-jackson` `55e93f1`
- **Reviewer:** local Codex CLI
- **Overall verdict:** APPROVE-WITH-NITS

## 2. Verbatim audit

I reviewed the requested work order in `docs/reviews/REVIEW_REQUEST.md`, then read
`CLAUDE.md`, `docs/ATLAS_Timeframe_Continuity_Charter.md`,
`docs/HANDOFF.md`, and `docs/EXTERNAL_REVIEW_PROTOCOL.md` in the requested order.
I inspected the pinned workspace commit and the sibling Jackson commit. I did not
run tests because this review command's hard constraint permits only one write:
this audit file.

Pine docs consulted:

- TradingView Pine concepts, Other timeframes and data:
  https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/
- TradingView Pine concepts, Timeframes:
  https://www.tradingview.com/pine-script-docs/concepts/timeframes/
- TradingView Pine concepts, Strategies:
  https://www.tradingview.com/pine-script-docs/concepts/strategies/

### Findings

1. LOW -- The new local period-open reconstruction is correct for the reviewed
   A/B controls, but it is not guarded against non-aligned chart/gate timeframe
   combinations. The code only enforces `chart TF <= enabled gate TF`
   (`pine/baseline_continuity.pine:88`) while the header merely says the chart
   TF "should equal" the lowest enabled TF (`pine/baseline_continuity.pine:30`).
   The actual open reconstruction uses the local chart bar open at
   `timeframe.change(tf)` (`pine/baseline_continuity.pine:102`). That is the
   true HTF period open when the chart bars align with the higher timeframe
   boundary, as in Control A and Control B. It can silently become "first chart
   bar inside the new HTF period" for odd combinations such as a chart timeframe
   that is below but does not divide the enabled gate timeframe. TVB-3 explicitly
   lists non-aligned chart TFs as a focus area (`docs/HANDOFF.md:98`), so future
   sweeps should either enforce chart TF == lowest enabled TF or enforce integer
   divisibility/alignment for every enabled gate TF before reporting numbers.

2. LOW -- `margin_long = 0, margin_short = 0` is a defensible signal-isolation
   fix for the TradingView emulator deadlock, but it also removes any liquidation
   or solvency constraint that a real 1x short book would eventually enforce.
   The Pine change is explicit (`pine/baseline_continuity.pine:54`), and the
   datasheet honestly reports that the corrected sweep ran with margin off
   (`docs/TVB2_control_AB_rerun.md:365`). I do not think this invalidates the
   corrected A/B characterization because the session positions the sweep as a
   control baseline, not a deployability claim. Before any live-read or
   deployability language, add a max-adverse-excursion or liquidation-distance
   check for the short legs, especially because the session itself asks whether
   margin 0/0 hides a cash-margin reality (`docs/HANDOFF.md:100`).

3. LOW -- The sanitized fee artifact should validate the `crossed` field as a
   JSON boolean instead of coercing it with `bool(...)`. The script documents
   `crossed` as the authoritative liquidity flag (`analysis/fee_rates_by_dex.py:4`)
   but currently does `crossed = bool(f["crossed"])`
   (`analysis/fee_rates_by_dex.py:58`). That is fine for raw Hyperliquid JSON
   booleans, but a local export that serializes false as a string would be
   silently classified as taker. The tests cover true/false boolean fixtures
   (`tests/test_fee_rates.py:21`) but not stringified booleans. Treat this as
   a parser-hardening nit: require `isinstance(crossed_raw, bool)` or skip the
   row as malformed.

### Notes supporting approval

- I do not see a classic `request.security` lookahead leak in the reviewed
  canonical strategy. The new strategy source reconstructs the gate via
  `ta.valuewhen(timeframe.change(tf), open, 0)` and has no active
  `request.security` call in the strategy logic (`pine/baseline_continuity.pine:98`).
- The unsafe visual TFO indicator still uses `barmerge.lookahead_on`
  (`Timeframe_Continuity_Pinescript.pine:70`), but the TVB-3 proof correctly
  avoids treating that overlay as ground truth and instead uses single-TF
  isolation of the strategy's own plotted values
  (`docs/TVB2_control_AB_rerun.md:312`). That is the right separation.
- The P2a interpretation is plausible. TradingView's own docs describe different
  historical vs realtime behavior for `request.security`, and the TVB-3 evidence
  says the prior gate showed the previous period open on historical bars and
  only merged the current open on the closing chart bar
  (`docs/TVB2_control_AB_rerun.md:318`). The replacement removes that class of
  divergence from the strategy.
- The corrected fee sweep is appropriately framed as a replacement for TVB-1/2,
  with the B sign flip and bundled attribution caveat called out rather than
  hidden (`docs/TVB2_control_AB_rerun.md:396`,
  `docs/TVB2_control_AB_rerun.md:407`). I did not find an arithmetic or
  interpretation issue in the table-level claims.
- The Jackson hardening is directionally correct: public returns now propagate
  `debug_sources` for strategy results, trades, and equity
  (`C:\Strat_Trading_Bot\tradingview-mcp-jackson\src\core\data.js:174`,
  `C:\Strat_Trading_Bot\tradingview-mcp-jackson\src\core\data.js:223`,
  `C:\Strat_Trading_Bot\tradingview-mcp-jackson\src\core\data.js:262`), the trade
  cap now honors requests above 20 up to 500
  (`C:\Strat_Trading_Bot\tradingview-mcp-jackson\src\core\data.js:7`), and the
  chart helpers now resolve injected dependencies before calling `evaluate`
  (`C:\Strat_Trading_Bot\tradingview-mcp-jackson\src\core\chart.js:118`).

## 3. Actionable items (reviewer's own list, if provided)

1. Add an explicit alignment guard for local HTF-open reconstruction -- LOW --
   `pine/baseline_continuity.pine:88` -- require chart TF to equal the lowest
   enabled TF or require every enabled gate TF to be an integer multiple of the
   chart TF before running/reporting arbitrary sweeps.
2. Add a short-leg solvency/MAE check before deployability language -- LOW --
   `pine/baseline_continuity.pine:54` -- keep margin 0/0 for the signal baseline,
   but report whether any corrected-control short would breach a realistic 1x
   cash-margin/liquidation constraint.
3. Validate `crossed` as a real boolean in the sanitized fee script -- LOW --
   `analysis/fee_rates_by_dex.py:58` -- reject or skip malformed rows instead of
   coercing truthiness.

## Suggested prompt (optional)

No replacement prompt suggested. The current `/review` prompt is specific enough
for this workspace and correctly forces the latest `REVIEW_REQUEST.md` to be the
work order.
