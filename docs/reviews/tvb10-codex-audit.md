# TVB-10 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of TVB-8 `b4bab2c^..db203aa`, TVB-9 `f192a14^..5edd5b6`, and TVB-10 `af27900^..258dfb3` captured 2026-07-08
> (TVB-10 post-session, with TVB-8/TVB-9 included because their review requests were still unreturned).
> Lightly ASCII-normalized; wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-8 / TVB-9 / TVB-10 combined pending external review
- **Reviewed:** `b4bab2c^..db203aa`, `f192a14^..5edd5b6`, `af27900^..258dfb3` on `main`
- **Reviewer:** Codex CLI / GPT-5
- **Overall verdict:** APPROVE-WITH-NITS

## 2. Verbatim audit

I reviewed the repo-local work order first (`docs/reviews/REVIEW_REQUEST.md`), then the protocol, template, current HANDOFF blocks, datasheet sections, scoped diffs, simulator/config code, sweep/diagnostic scripts, committed JSON artifacts, and the TVB-10 companion Pine. The current request file is valid, status is REQUESTED, and `docs/reviews/tvb10-codex-audit.md` did not already exist. The TVB-8 and TVB-9 audit files also did not exist, so including those ranges is consistent with the user's request and the TVB-10 pointer note.

No BLOCK or NEEDS-CHANGES finding came out of the core port/sweep path. TVB-8's simulator port preserves the Pine bar-loop shape: Phase A fills at open, Phase B logic at close, integer tick-space trigger arithmetic, gross-profit governor arming, and the equivalence comparator checks exact entry/exit times/direction plus fill/economic tolerances and the open-position boundary. TVB-9's breadth and HTF artifacts are consistent with the declared grids: 144 breadth rows and 108 HTF rows, with the HTF native-1d crosscheck explicitly recording the small MU/AMD/CRCL mismatches rather than hiding them. TVB-10's `exit_mode` implementation is the intended branch: `state` exits on first loss of full alignment, while `flip` exits only on full opposite alignment; exit fill timing stays next-open and regime permits are entry-only. The TVB-10 artifact records state regression PASS, C2 total violations = 0, and the cadence-refutation numbers used in the write-up.

The main nits are evidence and wording issues around claims that were otherwise mostly handled honestly: the C1 governor-inertness language is slightly too strong for AMD, the companion still exposes stale net-vs-gross governor wording, and the TVB-10 MAE/L_surv overlay claim is not backed by a committed TVB-10-specific runner/artifact the way the net/MTM and D1 claims are.

### Finding 1 -- C1 "governor inertness" is overstated for AMD flip rows -- LOW

The pre-registration says the governor deltas should be approximately zero under `flip`, and the carried drift rule says gov-cell differences below 2.5pp are sign-indeterminate (`docs/TVB2_control_AB_rerun.md:2127`). The result text calls C1 "CONFIRMED operatively" and says the residual worst is 2.88pp at AMD 0-fee, "small at real fees" (`docs/TVB2_control_AB_rerun.md:2259`). But the committed artifact shows AMD real-fee flip governor deltas of +2.8178pp at s1 and +2.8135pp at s10 (`analysis/reference/tvb10_exit_results.json:4477`, `analysis/reference/tvb10_exit_results.json:4484`), while `c1_worst` is +2.8787pp (`analysis/reference/tvb10_exit_results.json:4576`). Those are much smaller than the CRCL state-arm +11.75pp case and do not overturn the headline, but they are not literally "~0 everywhere" and the real-fee AMD deltas slightly exceed the stated 2.5pp gov-cell drift band.

Suggested action: soften "governor structurally inert under flip" to "mostly inert / no longer a major lever under flip, with small AMD residuals from exit-fill-bar close state." If C1 remains a formal check in future sweeps, report pass/fail against the declared 2.5pp band.

### Finding 2 -- Companion governor tooltip still says strategy is net-of-fees -- LOW

The TVB-10 companion behavior uses gross win/loss (`gross_win = pos > 0 ? xp > ep : xp < ep`) and therefore matches the corrected simulator model (`pine/tfc_companion.pine:331`, `tfc/simulator.py:12`). However, the companion's header comment and live input tooltip still tell users the companion is gross while "the strategy" is net-of-fees (`pine/tfc_companion.pine:77`, `pine/tfc_companion.pine:123`). That contradicts the TVB-7 adjudication recorded in the datasheet: `strategy.closedtrades.profit()` is gross of commission in this TV build, and the port must arm on gross profit <= 0 (`docs/TVB2_control_AB_rerun.md:1468`, `docs/TVB2_control_AB_rerun.md:1476`).

This is not a behavior bug in the companion or simulator; it is stale user-facing guidance. It matters because the companion is now a manual-trading tool, and the tooltip currently tells users to expect ratchet divergence that should not exist for the gross-profit boundary.

Suggested action: update the companion header/tooltip to say both the deployed strategy and companion classify governor wins/losses gross of commission, with slippage still controlling scratch behavior. Leave the strategy-slot comment fix queued if preserving the pv20 anchor is still the priority.

### Finding 3 -- TVB-10 MAE/L_surv overlay lacks a committed TVB-10-specific evidence path -- LOW

The TVB-10 pre-registration requires a leverage-overlay re-run on the flip arm for MAE/L_surv comparison (`docs/TVB2_control_AB_rerun.md:2130`) and expectation 5 explicitly binds MAE, L_surv, and sample-Kelly (`docs/TVB2_control_AB_rerun.md:2160`). The results report median MAE inflation and MU L_surv falling from 7.30 to 5.36 (`docs/TVB2_control_AB_rerun.md:2253`). I do not see a committed TVB-10 leverage artifact or runner path corresponding to that result: the TVB-10 exit runner writes economics plus `mtm_net_pct` only (`scripts/tfc_exit_sweep.py:151`), and the committed leverage overlay script constructs `TFCConfig(...)` without an `exit_mode`, so it defaults to state mode (`analysis/tfc_leverage_overlay.py:141`).

The numbers may be reproducible from the committed bars by adapting the TVB-9 overlay to `exit_mode='flip'`, and the qualitative warning is directionally plausible. The issue is evidentiary: unlike `tvb10_exit_results.json` and `tvb10_flipline_distance.json`, this check cannot be audited as a committed TVB-10 artifact.

Suggested action: either commit a small TVB-10 flip-overlay postprocessor/artifact, or mark the MAE/L_surv statement as a manually recomputed diagnostic until it is pinned. Do not let this block the net/MTM exit-symmetry read.

### Notes on scope areas that passed

- The `exit_mode` branch itself is correct in the Python engine: `flip` uses `dn[i]` for long exits and `up[i]` for short exits, while `state` uses `not up[i]` / `not dn[i]`; both schedule the same next-open exit fill path (`tfc/simulator.py:146`).
- Regime layer does not gate exits in the simulator; it only supplies `long_permit`/`short_permit` for entries (`tfc/simulator.py:48`, `tfc/simulator.py:176`).
- C2 is implemented against recomputed gate series and includes open trades in the entry list; the artifact reports zero violations (`scripts/tfc_exit_sweep.py:86`, `analysis/reference/tvb10_exit_results.json:4583`).
- The companion Pine contains no `request.security` call; it uses local `ta.valuewhen(timeframe.change(tf), open, 0)` period opens and [1]-committed gate reads at Strategy-TF boundaries (`pine/tfc_companion.pine:181`, `pine/tfc_companion.pine:289`).
- D1's nan filtering is real: entries before any active M/W/D boundary are skipped before distance comparison (`analysis/flipline_distance.py:64`). The weak 22/36 result is correctly treated as insufficient for a dead-band parameter.
- TVB-8/TVB-9 interpretation discipline is mostly good: young-listing and in-sample caveats are repeated, drift bands are carried forward, and no keep/kill verdict is made off the breadth pass.

## 3. Actionable items (reviewer's own list, if provided)

1. Soften C1 governor-inertness wording and explicitly report AMD real-fee residuals against the 2.5pp gov drift band -- LOW -- `analysis/reference/tvb10_exit_results.json:4477` -- update the TVB-10 result text/HANDOFF synthesis.
2. Correct the companion governor tooltip/comment from net-of-fees divergence to gross-profit parity -- LOW -- `pine/tfc_companion.pine:123` -- comment/tooltip-only Pine update at next companion touch.
3. Pin the TVB-10 flip MAE/L_surv overlay as committed code/artifact, or downgrade that result to a manually recomputed diagnostic -- LOW -- `docs/TVB2_control_AB_rerun.md:2130` -- add a tiny `exit_mode='flip'` overlay path if the claim remains part of the record.

## Suggested prompt (optional)

For the next review, include an explicit "evidence inventory" line in `REVIEW_REQUEST.md`: list each pre-registered check and the exact committed artifact or script that proves it. This would have made the MAE/L_surv overlay gap obvious before the review.
