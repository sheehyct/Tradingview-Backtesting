# TVB-4 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of `58c3ca9..bc9941f` on `main`, with wider same-session context
> (`5359756..bc9941f`) used where the work order required Pine review, captured
> 2026-07-03 (TVB-4 post-session). Lightly ASCII-normalized; wording and code
> otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control
> vs variant, or over/under-state a risk. The critical synthesis -- where we agree,
> dispute, and act -- is in `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-4 -- two-layer regime layer built + ablated
- **Reviewed:** requested range `58c3ca9..bc9941f` on `main`; wider same-session
  context inspected where required by `docs/reviews/REVIEW_REQUEST.md`
- **Reviewer:** local Codex CLI
- **Overall verdict:** APPROVE-WITH-NITS

## 2. Verbatim audit

### Findings

1. **MEDIUM -- The pinned review range excludes the central Pine commit.**

   `docs/reviews/REVIEW_REQUEST.md:24` and `docs/HANDOFF.md:85-89` tell reviewers to
   review `58c3ca9..bc9941f` and describe that range as containing the two-layer Pine
   plus ablation/docs. In Git range syntax the left endpoint is excluded, and
   `58c3ca9` itself is the Pine-only commit (`git show --stat 58c3ca9` shows only
   `pine/baseline_continuity.pine`). A literal `git diff --name-status 58c3ca9..bc9941f`
   contains only `.session_startup_prompt.md`, `analysis/reference/tvb4_R*.json`,
   `docs/HANDOFF.md`, `docs/TVB2_control_AB_rerun.md`,
   `docs/reviews/REVIEW_REQUEST.md`, and `scripts/tv_dump.mjs`; it does not include
   `pine/baseline_continuity.pine`.

   I worked around this by reviewing the wider same-session context, but a cloud or
   future reviewer following the range exactly can miss the primary implementation.
   Pin the request to `58c3ca9^..bc9941f`, `9331d89..bc9941f`, or another range whose
   diff actually contains the Pine commit.

2. **LOW -- The ablation table mixes closed-trade totals with direction counts that
   include the open trade.**

   `scripts/tv_dump.mjs:20-27` exports `rd.trades` into `list` while also reporting
   `performance.all.totalTrades`; `scripts/tv_dump.mjs:37-39` then counts L/S from
   `out.list`. The committed TVB-4 reference dumps show the mismatch:
   `tvb4_R1a_standaside_0fee.json` has `totalTrades=922`, `openTrades=1`,
   `listCount=923`, `le=488`, `se=435`; `tvb4_R2a_sizedown_0fee.json` has
   `totalTrades=2390`, `openTrades=1`, `listCount=2391`, `le=1212`, `se=1179`.
   The datasheet copies that shape: `docs/TVB2_control_AB_rerun.md:521` reports
   `922 (488/435)` and `docs/TVB2_control_AB_rerun.md:524` reports `2390
   (1212/1179)`, so the L/S split sums to one more than the displayed trade total.

   This does not invalidate the net/PF headline, but it makes trade-count and churn
   comparisons slightly ambiguous. Either filter the dump's L/S counts to closed trades
   only, or label the split as closed plus current open trade whenever `openTrades > 0`.

3. **LOW -- The tracked reference artifacts do not preserve the real-fee headline runs.**

   The central TVB-4 claim is the real-fee ablation in
   `docs/TVB2_control_AB_rerun.md:517-525`, especially stand_aside `+40.26%` vs control
   `-8.60%` and size_down `+12.84%` at `0.0125%`. The tracked `analysis/reference`
   files at HEAD are `tvb4_bars_60m.json`, `tvb4_trades_A_0fee.json`,
   `tvb4_trades_B_0fee.json`, `tvb4_R1a_standaside_0fee.json`, and
   `tvb4_R2a_sizedown_0fee.json`. The zero-fee stand_aside and size_down dumps match
   the table, but the `0.0125%` headline rows and the same-window off-control rows are
   not reproducible from committed artifacts alone.

   The numbers may be correct, but the evidence chain is weaker than the docs imply
   when they say reference/run dumps were preserved (`docs/HANDOFF.md:74-75`). Commit
   JSON dumps or a manifest for every headline matrix row before treating the TVB-4
   real-fee result as a stable reference point for TVB-5.

### Pine and methodology read

I do not see a Pine logic blocker in the two-layer regime implementation.

- `pine/baseline_continuity.pine:114-115` reconstructs period opens locally with
  `ta.valuewhen(timeframe.change(tf), open, 0)` and does not use `request.security`,
  which avoids the standing lookahead trap for this strategy.
- The alignment guard in `pine/baseline_continuity.pine:91-111` enforces chart TF
  no finer than enabled gate TFs, intraday integer tiling, and D/W/M chart-TF division
  of one day. That matches the TVB-3 finding it was meant to close.
- `f_agg` and the permission logic in `pine/baseline_continuity.pine:154-184` implement
  the claimed modes: off permits both directions at full size, stand_aside requires
  regime alignment, and size_down allows grey in both directions at `grey_size_pct`
  while blocking the opposite regime.
- The off branch is behaviorally inert: `long_permit` and `short_permit` become `true`,
  `size_scale` becomes `1.0`, and `reg_exit` is also gated behind
  `reg_mode != 'off'` at `pine/baseline_continuity.pine:194`.
- The size_down explicit `qty = strategy.equity * size_scale / close` in
  `pine/baseline_continuity.pine:207-218` is an arm-time approximation, not an exact
  fill-price half-size. I do not see lookahead or equity timing leakage because the
  strategy is flat when it arms the order, but the docs should continue to call it an
  approximation rather than exact parity with `percent_of_equity`.

The S8 interpretation is acceptable as a go-forward ablation baseline, not as a
deployability verdict. The datasheet does include the right caveats at
`docs/TVB2_control_AB_rerun.md:572-576`: single instrument, single window, long
concentration, late-entry tax, slippage realism, and OKX-to-HL venue gap. Keep those
caveats attached to any short-form "stand_aside is decided" language during TVB-5.

### Validation performed

- `git diff --name-status 58c3ca9..bc9941f`
- `git diff --name-status 9331d89..bc9941f`
- `git show --stat 58c3ca9`
- Parsed committed TVB-4 JSON dumps with PowerShell `ConvertFrom-Json`
- `uv --cache-dir .uv-cache run pytest tests/test_fee_rates.py -q` -> `5 passed in 0.01s`

I did not live-recompute TradingView/CDP results in this review. The audit is based on
tracked source, docs, and committed reference dumps.

## 3. Actionable items (reviewer's own list, if provided)

1. **Range pin** -- MEDIUM -- `docs/reviews/REVIEW_REQUEST.md:24`,
   `docs/HANDOFF.md:85-89` -- change the review range so it includes `58c3ca9`
   rather than excluding it.
2. **Trade-count split** -- LOW -- `scripts/tv_dump.mjs:20-27`,
   `scripts/tv_dump.mjs:37-39`, `docs/TVB2_control_AB_rerun.md:521`,
   `docs/TVB2_control_AB_rerun.md:524` -- make L/S counts use the same closed/open
   trade basis as the displayed total, or label the mismatch explicitly.
3. **Reference coverage** -- LOW -- `docs/TVB2_control_AB_rerun.md:517-525`,
   `docs/HANDOFF.md:74-75` -- preserve real-fee headline dumps or a manifest for
   every ablation row that TVB-5 will use as a baseline.

## Suggested prompt

For the next external review, pin a range that includes the implementation commit:

> Review `58c3ca9^..bc9941f` (or the current corrected TVB-4 range) with focus on
> Pine regime semantics, closed-vs-open trade accounting in dump artifacts, and whether
> every headline ablation row has a committed reproducibility artifact.
