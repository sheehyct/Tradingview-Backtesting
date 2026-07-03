# TVB-5 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of `tradingview-backtesting` commit range `b99dccb^..d622be1`
> captured 2026-07-03 (TVB-5 post-session). Lightly ASCII-normalized; wording and
> code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate
> control vs variant, or over/under-state a risk. The critical synthesis -- where
> we agree, dispute, and act -- is in `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-5 -- S8 ratified; pre-registered 3x3 TF-set sweep across 4 samples
- **Reviewed:** `b99dccb^..d622be1` on `main` (`6c855cf..d622be1`; 57 changed files)
- **Reviewer:** Codex CLI
- **Overall verdict:** APPROVE-WITH-NITS

## 2. Verbatim audit

I reviewed the active work order in `docs/reviews/REVIEW_REQUEST.md`, the required
read-first packet, and the pinned range `b99dccb^..d622be1`. The range sanity check
returned 57 changed files, matching the request. The range includes the S8
ratification/repro commit, the sweep commit, and the session-end review-pointer
commit.

The main result is sound enough to carry forward: I do not see a blocker in the
window-compounding helper, the committed reference dumps, the no-`request.security`
Pine posture, the S8 fee arithmetic, or the venue-gap caution. The remaining items
are nits around robustness/documentation of the dump parser assumption and the
headline wording of "universal" containment.

### Findings

1. LOW -- `tv_dump` closed-basis marking still relies on an undocumented internal
   `reportData().trades` ordering assumption.

   The script states that `rd.trades` is entry-ordered and that open trade rows sit
   at the end, then marks `open: j >= closedN`, where `closedN` is
   `performance.all.totalTrades` (`scripts/tv_dump.mjs:23-31`). The datasheet
   repeats the same rule as the proof of the closed set (`docs/TVB2_control_AB_rerun.md:643-646`).
   I checked all committed `tvb5_*.json` dumps: `list.Count == trades + openTrades`,
   `open:true` appears only after `trades`, and the closed L/S counts match
   TradingView's exported long/short totals. That supports the current artifacts.
   The gap is that the dumps now encode the assumption; they do not independently
   preserve enough raw exit/open-position evidence to prove that TradingView will
   keep this ordering in future app/server versions. Action: add a dump-time
   assertion and/or preserve raw exit timestamp/status fields so future sessions
   can fail loudly if the open-row convention changes.

2. LOW -- The "universal damage containment" headline is directionally supported
   by the tested matrix, but should be worded as tested-sample universal rather
   than universal in the absolute.

   The data does support the local claim: W1, W2, W3, and the xyz prefix all show
   M/W/D stand_aside reducing damage or improving return versus the relevant
   ungated control (`docs/TVB2_control_AB_rerun.md:824-828`). The same section also
   properly warns that xyz provenance is unverified, slippage realism is still
   unmodeled, short-leg MAE/solvency is deferred, and the system is a regime-local
   edge rather than all-weather (`docs/TVB2_control_AB_rerun.md:833-840`). The nit
   is headline portability: `docs/HANDOFF.md:42-48` and
   `docs/TVB2_control_AB_rerun.md:824-831` are easy to quote without the caveats.
   Action: in the next synthesis, prefer "universal across tested samples/cells"
   or "observed universal damage containment in this sweep" for the headline.

### Checks that passed

- Range pin: `git diff --name-status b99dccb^..d622be1` lists 57 files, so the
  caret rule kept the first TVB-5 commit inside the reviewed range
  (`docs/reviews/REVIEW_REQUEST.md:18-25`, `.claude/commands/session-end.md:70-76`).
- Pine lookahead: no Pine changed in this range. The canonical strategy declares
  local `ta.valuewhen(timeframe.change(tf), open, 0)` reconstruction and explicitly
  says there is no `request.security` (`pine/baseline_continuity.pine:9-11`,
  `pine/baseline_continuity.pine:114-115`).
- Window compounding: `analysis/window_compound.py` implements half-open
  `[start_ms, end_ms)` entry filtering, excludes `open:true` rows, and compounds
  `product(1+pp)-1` over closed trades (`analysis/window_compound.py:23-52`).
  The strategy assumptions behind that method are present: `default_qty_value = 100`
  and `pyramiding = 0` (`pine/baseline_continuity.pine:36-47`). The tests cover
  product compounding, half-open windows, and open/malformed row exclusion
  (`tests/test_window_compound.py:15-39`).
- Venue-gap arithmetic: read-only recomputation from the committed WV dumps matches
  the datasheet's shared-window numbers exactly: ctrlB @0.0125 xyz +80.17% with
  2708 trades, R1E1 @0.0125 xyz +83.07% with 917 trades, and the Dec-Feb prefix
  losses -40.09%/-12.61%. The caution is adequate because the datasheet says the
  xyz feed provenance is unverified and must be cross-validated before trusting any
  xyz number (`docs/TVB2_control_AB_rerun.md:815-823`).
- S8 arithmetic: the fresh committed zero-fee dumps imply `(1 + off_net) /
  (1 + stand_aside_net) = 1.04352` over 1,892 suppressed trades, or about
  0.00225% gross per trade, below the documented 0.025% round-trip commission
  (`docs/TVB2_control_AB_rerun.md:584-590`,
  `analysis/reference/tvb5_R0a_off_0fee.json:1`,
  `analysis/reference/tvb5_R1a_standaside_0fee.json:1`).
- Pre-registration integrity: the SP500 fallback to OKX BTC follows the written
  selection rule, and the W-venue expansion is documented as an in-flight discovery
  after xyz MSTR backfill appeared (`docs/TVB2_control_AB_rerun.md:668-685`,
  `docs/TVB2_control_AB_rerun.md:708-715`). I do not read this as result-driven
  drift.

Validation note: I did not run pytest because this review contract permits only
one write, the audit file. Validation above is from read-only source/dump
inspection and read-only PowerShell calculations over the committed JSON dumps.

## 3. Actionable items (reviewer's own list, if provided)

1. LOW -- `scripts/tv_dump.mjs:23-31` -- Add a fail-loud dump assertion and/or raw
   exit/status fields so the closed-basis parser does not depend solely on the
   observed `reportData().trades` tail-open convention.
2. LOW -- `docs/HANDOFF.md:42-48`, `docs/TVB2_control_AB_rerun.md:824-831` --
   Soften "universal damage containment" to "universal across tested samples/cells"
   in the next synthesis to avoid an all-market/all-regime reading.
