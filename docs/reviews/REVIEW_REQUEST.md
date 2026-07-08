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
- Session under review: TVB-10 -- exit-symmetry ablation (state-stop vs
  flip-stop; `TFCConfig.exit_mode`; pre-registered 288-run sweep + D1
  flip-line diagnostic); TFC Companion indicator v3 -> v4.1 (exit_mode
  toggle, Desktop UX rework, mobile table compaction); end-of-session live
  finding (entry-arming fork) recorded for TVB-11
- Requested: 2026-07-08
- Write the audit to: `docs/reviews/tvb10-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: the TVB-8 (`b4bab2c^..db203aa`) and TVB-9 (`f192a14^..5edd5b6`)
  requests were never returned; their records live in their HANDOFF blocks.
  Reviewing them alongside this range is welcome but not required.

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `{pending push}` |

No sibling-repo changes this session.

RANGE-PIN RULE (Codex TVB-4 finding 1): git ranges EXCLUDE the left endpoint;
pin `{first}^..{head}` (the caret keeps the first session commit inside the
reviewed diff). Sanity-check with `git diff --name-status <range>`.

## Read first (in this order)

1. `CLAUDE.md` -- epistemic stance + backtest traps (Sections 2, 6).
2. `docs/ATLAS_Timeframe_Continuity_Charter.md` -- Section 0 + Section 5.
3. `docs/HANDOFF.md` -- the TVB-10 entry at the top (what was done and why).
4. `docs/TVB2_control_AB_rerun.md` -- the TVB-10 sections at the end
   (pre-registration, C2 pre-run amendment, results scorecard, companion
   deployment records). These are the record under review.
5. `docs/EXTERNAL_REVIEW_PROTOCOL.md` -- the reviewer contract.

## Scope / what changed

(a) `tfc/config.py` + `tfc/simulator.py`: `exit_mode` state|flip -- state-stop
exits on FIRST loss of full alignment, flip-stop only on full OPPOSITE
alignment; equivalence gate stayed 8/8 and the state arm reproduced TVB-9
bit-exactly. (b) `scripts/tfc_exit_sweep.py`: pre-registered 288-run sweep
(60m grid x exit_mode x fees x slippage) on committed HL pulls, with a
state-arm regression check, governor-delta check C1, one-per-regime check
C2, and dual closed+MTM accounting (`mtm_net_pct`). (c)
`analysis/flipline_distance.py`: D1 flip-line clustering diagnostic
(pre-registered; result WEAK 22/36 -> dead-band candidate parked). (d)
`pine/tfc_companion.pine` v2 -> v4.1 (INDICATOR slot only; the STRATEGY slot
stays pineVersion 20, untouched). Headline reading recorded, NO promotion:
exit symmetry is a regime-shape bet (flip rides bursts, state harvests
swings); cadence collapse is gate-set-speed-dependent (ctrlA ratio 0.068 vs
E3 ~0.7); governor structurally inert under flip.

## Focus areas (scrutinize these)

1. **exit_mode branch correctness** (`tfc/simulator.py`): the one-token spec
   difference (`not up[i]` vs `dn[i]`), exit-fill timing (exit fills at the
   open AFTER the qualifying close -- is the lag modeled consistently with
   the state arm?), and interaction with the regime layer (regime must
   never gate exits).
2. **The C2 PRE-RUN amendment** (datasheet): the draft check was mis-derived
   (entry-subset invariant); it was amended BEFORE any execution to a
   one-per-regime invariant and the error recorded. Is the amended
   invariant actually correct, and is the record honest?
3. **Interpretation discipline**: flip cells are n=8-42, in-sample, young
   listings. Does the "regime-shape bet" reading stay descriptive, or does
   any sentence promote flip (or state) beyond the evidence? Is the
   gate-set-speed cadence claim (0.068 vs ~0.7) supported?
4. **D1 diagnostic validity** (`analysis/flipline_distance.py`): nan
   filtering before the first M/W/D boundary, within-cell winner-vs-loser
   comparison (absolute distances confounded by open-coupling), >=30-trade
   cell floor -- any way the WEAK verdict is an artifact?
5. **Companion fidelity** (`pine/tfc_companion.pine` v4.1): claims NO
   `request.security`, [1]-committed gate reads at strategy-TF boundaries,
   `ta.valuewhen(timeframe.change(tf), open, 0)` period opens, const-string
   alertcondition names. Does the indicator's state machine actually match
   the simulator's arming/exit semantics for BOTH exit modes?
6. **MTM accounting** (`mtm_net_pct`): open trade marked at last close with
   exit-side slip+commission -- fair, or does it flatter either arm?

Standing priorities on ANY TVB review: `request.security` lookahead in Pine
(Pine changed this session -- INDICATOR slot; verify the no-security claim),
model fidelity (is the backtest measuring what it claims?), overfitting /
sample-vs-structural reasoning (no keep/kill verdicts off young listings --
user directive), fee/turnover math.

## Output contract

- Verbatim audit -> `docs/reviews/tvb10-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line` and Pine/TV docs. Never paste a
  secret/IP/account value into a review file.
- The critical synthesis (agree/dispute/act) is written by the NEXT session
  into `docs/HANDOFF.md` -- your job is the honest external read, not the
  final word.
