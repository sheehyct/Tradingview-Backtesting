# TVB-7 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of `a4e1de8^..557e00d` captured 2026-07-04
> (TVB-7 post-session). Lightly ASCII-normalized;
> wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-7 -- governor v2 cross-venue verification, VBT breadth-port design, cost realism, TVB-6 fold-in
- **Reviewed:** `a4e1de8^..557e00d` on `main` (5 commits, 33 changed files by `git diff --name-status`)
- **Reviewer:** Codex CLI
- **Overall verdict:** APPROVE-WITH-NITS

## 2. Verbatim audit

I reviewed the request packet, the pinned range, the changed docs/code/tests, and the committed JSON evidence. I also performed read-only recomputations over the committed dumps for the cross-venue table, the governor gross-arming prefix checks, the L2 aggregate, and the funding-adjusted returns.

### Findings

#### LOW -- VBT port plan still has one stale net-PnL governor sentence

`docs/VBT_BREADTH_PORT_PLAN.md` is implementation-facing and says in the user-approved fork summary that "the governor reads net closed-trade PnL" at `docs/VBT_BREADTH_PORT_PLAN.md:20`. That conflicts with the corrected calibrated-facts block in the same file, which says the port must arm on `GROSS profit <= 0` and explicitly notes that a net interpretation would fail the gate cells at `docs/VBT_BREADTH_PORT_PLAN.md:57` and `docs/VBT_BREADTH_PORT_PLAN.md:60`.

The rest of the TVB-7 record correctly adjudicates gross semantics: the datasheet documents a real boundary population, fee-independent sequence evidence, the 575-trade high-fee prefix, and the conclusion that `strategy.closedtrades.profit()` is gross of commission in this TV build at `docs/TVB2_control_AB_rerun.md:1454`, `docs/TVB2_control_AB_rerun.md:1458`, `docs/TVB2_control_AB_rerun.md:1464`, and `docs/TVB2_control_AB_rerun.md:1468`. `docs/HANDOFF.md` also tells the next session that the calibrated facts are spec and the governor arms on gross at `docs/HANDOFF.md:62`.

This is not a results blocker because the canonical calibrated-facts section and the Phase-3 trade-for-trade gate point the implementation in the right direction. It is still worth fixing before the vectorbt-workspace port begins, because following the stale sentence would send the implementer down a path the document itself says would fail the gate.

The Pine comment is also still stale by design: it says "net of fees" at `pine/baseline_continuity.pine:212`, while the datasheet explicitly queues that comment correction for the next Pine-touching deployment at `docs/TVB2_control_AB_rerun.md:1473`. I agree with not touching Pine solely for a comment while preserving the pineVersion-20 anchor, but the queued fix should remain attached to the next Pine change.

### Passed checks

- **Range and scope:** The pinned diff is `a4e1de8^..557e00d` and lists 33 changed files, matching the current request. No Pine file is in the diff. The only Pine lookup path remains local `ta.valuewhen(timeframe.change(tf), open, 0)` reconstruction, not `request.security`, at `pine/baseline_continuity.pine:124` and `pine/baseline_continuity.pine:126`.

- **Gross-arming adjudication:** The inference chain is strong. The datasheet documents that boundary trades exist, that fee changes should affect the sequence only through the profit test, that the zero-fee and fee'd governed sequences match across all closed trades, and that the 1% stress matches for the first 575 trades before the qty-floor break at `docs/TVB2_control_AB_rerun.md:1454`, `docs/TVB2_control_AB_rerun.md:1456`, `docs/TVB2_control_AB_rerun.md:1458`, and `docs/TVB2_control_AB_rerun.md:1464`. My read-only recomputation matched those sequence-prefix claims from `analysis/reference/tvb7_diag_gov2_0125.json:1`, `analysis/reference/tvb7_diag_gov2_100bp.json:1`, and the TVB-6 gov2 dumps.

- **CV pre-registration integrity:** CV1-CV4 were written before the result section and the pass/fail language was scoped correctly: CV2 upgrades only to cross-venue-verified on the MSTR underlying, not universal structural, at `docs/TVB2_control_AB_rerun.md:1265`, `docs/TVB2_control_AB_rerun.md:1269`, and `docs/TVB2_control_AB_rerun.md:1271`. The results table supports the keep-rule mirror on OKX MSTR R1E1 at both cost points at `docs/TVB2_control_AB_rerun.md:1303` through `docs/TVB2_control_AB_rerun.md:1305`, and the caveat that magnitude is path-local is stated at `docs/TVB2_control_AB_rerun.md:1336` through `docs/TVB2_control_AB_rerun.md:1344`.

- **L2 impact method:** `analysis/l2_book_impact.py` prices taker fills against visible book depth, reports impact vs mid, tracks exhausted sides, and converts to TV-tick equivalents at `analysis/l2_book_impact.py:71`, `analysis/l2_book_impact.py:88`, `analysis/l2_book_impact.py:97`, and `analysis/l2_book_impact.py:147`. The tests cover multi-level VWAP, buy/sell signs, and TV-tick conversion at `tests/test_l2_book_impact.py:24`, `tests/test_l2_book_impact.py:45`, and `tests/test_l2_book_impact.py:59`. The 20-snapshot evidence supports the "not near s10" conclusion, and the weekend-night caveat is explicit enough at `docs/TVB2_control_AB_rerun.md:1376` and `docs/TVB2_control_AB_rerun.md:1384`.

- **Funding model:** The join semantics are exactly `(et, xt]`, long-pays-positive and short-receives-positive are implemented at `analysis/funding_model.py:77`, `analysis/funding_model.py:93`, and `analysis/funding_model.py:96`. The compounded adjustment is `product(1 + pp - f)` at `analysis/funding_model.py:101` and `analysis/funding_model.py:109`, and tests cover the event window, sign convention, malformed row skipping, and compounding at `tests/test_funding_model.py:12`, `tests/test_funding_model.py:21`, `tests/test_funding_model.py:33`, and `tests/test_funding_model.py:45`. My recomputation matched the datasheet table at `docs/TVB2_control_AB_rerun.md:1404` through `docs/TVB2_control_AB_rerun.md:1410`; the "funding inverts the fee gradient" statement is supported at these magnitudes.

- **MAE correction:** The root-cause explanation is framed as "most plausible," not as proven fact, and the deterministic replay over committed files is clearly made canonical at `docs/TVB2_control_AB_rerun.md:1001` through `docs/TVB2_control_AB_rerun.md:1009` and `docs/TVB2_control_AB_rerun.md:1434` through `docs/TVB2_control_AB_rerun.md:1442`. That is honest enough for the evidence available.

- **VBT calibrated facts:** The qty rule, PnL formula, fill conventions, Pine order, and Phase-3 gate are specific enough to make the Python port falsifiable at `docs/VBT_BREADTH_PORT_PLAN.md:44`, `docs/VBT_BREADTH_PORT_PLAN.md:46`, `docs/VBT_BREADTH_PORT_PLAN.md:51`, `docs/VBT_BREADTH_PORT_PLAN.md:53`, and `docs/VBT_BREADTH_PORT_PLAN.md:107`. Aside from the stale net-PnL sentence above, I did not find a gate-breaking spec mismatch.

## 3. Actionable items (reviewer's own list, if provided)

1. Replace the stale "governor reads net closed-trade PnL" sentence with gross/profit()-semantics wording -- LOW -- `docs/VBT_BREADTH_PORT_PLAN.md:20` -- make it agree with `docs/VBT_BREADTH_PORT_PLAN.md:57` so the vectorbt-workspace implementation starts from the gate-passable spec.
2. Keep the queued Pine comment correction attached to the next Pine-touching deployment -- LOW -- `pine/baseline_continuity.pine:212` -- change the comment from net-fee arming to the empirically adjudicated gross-profit arming, then rerun the prefix regression as planned.

## Suggested prompt

For the next implementation review, add this explicit check to the existing prompt: "Search implementation-facing docs, comments, and tests for stale net-vs-gross governor wording; verify every port spec, fixture name, and expected cell uses the adjudicated gross `strategy.closedtrades.profit()` semantics before reviewing simulator mismatches."
