# TVB-2 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of `bd2c760..fbe1138` on `main` plus sibling reader commit
> `tradingview-mcp-jackson@fb2a788`, captured 2026-07-01 (TVB-2 post-session).
> Lightly ASCII-normalized; wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate
> control vs variant, or over/under-state a risk. The critical synthesis -- where
> we agree, dispute, and act -- is in `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-2 -- TV MCP reader fix, clean A/B controls, fee model resolution
- **Reviewed:** `bd2c760..fbe1138` on `main` plus `tradingview-mcp-jackson@fb2a788`
- **Reviewer:** Codex CLI
- **Overall verdict:** NEEDS-CHANGES

## 2. Verbatim audit

### Verdict

NEEDS-CHANGES on the review artifact before the next session relies on it as canonical.
The main reader fix looks directionally correct, and the fee/slippage conclusion is
plausible. The problems are narrower but action-affecting: the real-fee evidence is not
reproducible from the repo, slippage is described inconsistently with the Pine source,
one next-step fee target regresses to the superseded 0.0864% rate, and the reader fix
still drops the debug payload on the no-strategy path.

### Findings

1. **MEDIUM -- Slippage is not actually controlled or documented in the TVB-2 runs.**

   `docs/TVB2_control_AB_rerun.md` says slippage was deferred and calls the real-fee
   model "ZERO slippage" at lines 176-184. But the reviewed Pine strategy has a fixed
   `slippage = 1` in the `strategy()` declaration at `pine/baseline_continuity.pine:30-39`.
   The TVB-2 fixed conditions list instrument, window, sizing, fee, etc. at
   `docs/TVB2_control_AB_rerun.md:10-21`, but it does not say whether TradingView used
   the script's one-tick slippage, a Strategy Tester override, or zero.

   This matters because the current conclusion is "B is alive but fragile pending slippage."
   If the four actual runs already include one tick per fill, then the model is not zero
   slippage and the next step is incremental/asymmetric slippage, not first slippage. If
   TradingView overrode the script to zero, the document needs to state that explicitly.

   Suggested fix: add the exact Strategy Tester slippage setting to the fixed conditions.
   Rename the conclusion to either "1 tick/fill baseline, additional slippage pending" or
   "0 tick override, slippage entirely pending" before using the fee-adjusted estimates.

2. **MEDIUM -- The central fee reversal depends on off-repo evidence that future reviewers cannot reproduce.**

   The datasheet asserts the resolved Hyperliquid `crossed`-flag classification, including
   `n=2,425`, xyz `86.5%` taker, xyz taker `~0.0086% modal / 0.0125% notional-wtd`, and
   validation against native crypto taker `0.0432%` at
   `docs/TVB2_control_AB_rerun.md:146-164`. Those claims are coherent and the method is the
   right one: use the exchange liquidity flag, not inferred fee/notional labels. But no
   sanitized aggregate, script, checksum, or redacted output is tracked in the reviewed
   commit. The most important session conclusion at `docs/TVB2_control_AB_rerun.md:166-174`
   is therefore an external assertion from the repository's perspective.

   Suggested fix: do not commit raw fills or account identifiers. Add a sanitized artifact
   with only aggregate counts and rates by `{dex, crossed}`: fill count, notional-weighted
   fee rate, modal/median/mean rate, and count of the 0.0864% tail. That is enough to make
   the fee reversal auditable without exposing private trade data.

3. **LOW -- The deferred rerun target contradicts the resolved fee range.**

   The resolved section says the operative taker range is `0.0086-0.0125%` at
   `docs/TVB2_control_AB_rerun.md:166-172`, and the immediate next step correctly says to
   rerun at `0.0086% and 0.0125%` at `docs/TVB2_control_AB_rerun.md:186-190`. But the
   deferred checklist later says to set `in_23` to `0.0086% and 0.0864%` at
   `docs/TVB2_control_AB_rerun.md:221-222`. That second number is the superseded old taker
   assumption/tail rate, not the resolved notional-weighted rate.

   Suggested fix: change the deferred checklist to `0.0086% and 0.0125%`. If the 0.0864%
   tail is still worth testing, label it as a stress/tail-fee run, not the real-fee rerun.

4. **LOW -- The reader fix reintroduces the "debug payload dropped by outer return" failure mode on errors.**

   In `tradingview-mcp-jackson/src/core/data.js`, the browser-side no-strategy branch now
   builds `debug_sources` for `getStrategyResults` at lines 151-154 and for `getTrades` at
   lines 192-195. The outer Node return drops that payload: `getStrategyResults` returns
   only `success`, `metric_count`, `source`, `metrics`, and `error` at line 174, and
   `getTrades` returns only `success`, counts, `source`, `trades`, and `error` at line 223.
   The handoff specifically says a previous diagnostic was misleading because output was
   dropped by the node-side field-pick, so this is worth fixing now.

   Suggested fix: propagate `debug_sources` in the public return objects. It will not affect
   successful reads, but it preserves the diagnostic when the finder breaks again.

### Reader-fix review

The substantive reader patch is a real improvement over TVB-1. The old finder matched generic
`s.performance`; the new code searches `metaInfo().isTVScriptStrategy === true` or a
`reportData` method at `tradingview-mcp-jackson/src/core/data.js:142-150`, then reads
`reportData().performance` and copies scalar headline/risk fields at lines 156-168. `getTrades`
reads `reportData().trades` and maps entry/exit trade pairs at lines 197-208. `getEquity` derives
per-trade equity points from the same report data at lines 241-254.

I cannot independently verify the TradingView private object shape without a live CDP session,
but the patch matches the TVB-2 handoff's described standalone probe, and the no-longer-match
on generic `performance()` addresses the stated false positive.

Remaining reader caveat: no local unit tests cover `getStrategyResults`, `getTrades`, or
`getEquity`; the existing e2e test requires TradingView Desktop on CDP. That is acceptable for
this brittle private API, but the live verification evidence should stay in the handoff/datasheet.

### Fee and execution review

The "breakout stop entry is taker" reasoning holds for the control as written. The baseline uses
stop entries at `pine/baseline_continuity.pine:124-130`, and the state-stop exits use
`strategy.close` at `pine/baseline_continuity.pine:113-116`. A maker fee cannot be assumed for
the same stop-breakout fill set. The datasheet correctly flags the earlier maker-fee swap as a
different strategy unless the resolved point is that xyz taker itself is cheap.

The geometric model is appropriately labeled as a model, not a fresh backtest, at
`docs/TVB2_control_AB_rerun.md:169-172` and again at `docs/HANDOFF.md:41-43`. The next session
should still replace it with actual TradingView reruns before making any deployability call.

### Pine/model-fidelity review

No Pine code changed in the reviewed workspace range. The existing baseline still uses a single
`request.security(..., open, ..., lookahead_off)` call path at `pine/baseline_continuity.pine:68-80`,
so no new classic lookahead issue was introduced in TVB-2.

The two carried TVB-1 fidelity risks remain real and correctly documented: HTF-open currency is
unverified, and bar-magnifier/lower-timeframe fill fidelity is unverified. Those are not new TVB-2
regressions, but they still limit how strongly the control results can be interpreted.

### What I would do next

1. Patch the docs inconsistency: real-fee reruns are `0.0086%` and `0.0125%`; reserve `0.0864%`
   for a tail/stress run if desired.
2. Record the actual slippage setting used for the four TVB-2 runs before interpreting "B near
   breakeven on zero slippage."
3. Add a sanitized `crossed`-flag aggregate artifact for the fee reversal.
4. Propagate `debug_sources` through the jackson reader return objects.
5. Then rerun A/B at `0.0086%` and `0.0125%` with the reader, same window, same chart settings,
   and explicit slippage setting.

## 3. Actionable items (reviewer's own list, if provided)

1. Slippage setting missing/contradictory -- MEDIUM -- `pine/baseline_continuity.pine:30-39`,
   `docs/TVB2_control_AB_rerun.md:176-184` -- document whether TVB-2 used script slippage,
   UI override, or zero.
2. Fee reversal evidence not reproducible from repo -- MEDIUM --
   `docs/TVB2_control_AB_rerun.md:146-164` -- add a sanitized aggregate `{dex, crossed}` fee
   artifact.
3. Wrong deferred real-fee target -- LOW -- `docs/TVB2_control_AB_rerun.md:221-222` -- replace
   `0.0864%` with `0.0125%` or label `0.0864%` as stress/tail.
4. Reader debug payload dropped -- LOW --
   `tradingview-mcp-jackson/src/core/data.js:151-154`,
   `tradingview-mcp-jackson/src/core/data.js:174`,
   `tradingview-mcp-jackson/src/core/data.js:192-195`,
   `tradingview-mcp-jackson/src/core/data.js:223` -- include `debug_sources` in public returns.

## Suggested prompt (optional)

Review the TVB-3 real-fee reruns after A/B have been rerun at `0.0086%` and `0.0125%` with the
slippage setting explicitly recorded. Prioritize: whether the TradingView settings truly match the
control definitions, whether the fee/slippage decomposition is internally consistent, and whether
B's apparent survival is robust after realistic fill costs.
