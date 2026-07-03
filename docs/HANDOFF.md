# HANDOFF -- tradingview-backtesting

> Newest session entry at the TOP. Keep under 1500 lines; archive older entries to
> `docs/session_archive/` when it grows past that.

---

## Session TVB-5: S8 ratified; TF-set sweep across 4 samples; regime layer = containment; venue gap flagged (COMPLETE)

**Date:** 2026-07-03
**Status:** COMPLETE -- all four startup priorities done: S8 ratified + default-vs-input
decided; TVB-4 Codex review folded in (all 3 findings actioned); headline rows re-run +
committed; the pre-registered 3x3 timeframe-set sweep ran across FOUR samples (35 runs,
all sanity gates green).

### What was accomplished
- **S8 RATIFIED (Fable judgment, datasheet TVB-5 section):** stand_aside confirmed as the
  two-layer grey rule. Independent check: the suppressed stream is ~zero-expectancy GROSS
  (~+0.002%/trade vs 0.025% round-trip cost) -- skipping beats half-sizing mechanically;
  stand_aside also dominates risk-adjusted at ZERO fee, so it is not purely a fee story.
  P5 late-entry tax ratified as structural. DECIDED: `reg_mode` stays an INPUT, default
  `off` (defaults == regression anchor; baking a one-window data decision into code would
  fossilize it); the TVB-5+ baseline configuration = stand_aside set explicitly per run.
- **Codex TVB-4 review synthesis (RETURNED, APPROVE-WITH-NITS -- all 3 AGREED + actioned):**
  (1) MEDIUM range-pin (git left-endpoint exclusion dropped the Pine commit from the
  pinned range) -- verified correct; session-end command now mandates `{first}^..{head}`
  + a `git diff --name-status` sanity check. (2) LOW L/S open-trade basis -- verified
  against the committed dumps; `tv_dump.mjs` now reports CLOSED-basis splits (the open
  position is a pseudo-closed trade row whose exit is a mark-to-market at a WALL-CLOCK ms
  timestamp; closed set = first `performance.all.totalTrades` entries). (3) LOW missing
  real-fee dumps -- all six TVB-4 ablation rows re-run fresh and committed
  (`tvb5_R*.json`); every row reproduced within tail drift, DD/Sharpe exact. Also
  committed the tvb3/tvb4 audit files themselves (were untracked -- TVB-4 oversight).
- **Sweep design (with user, then locked):** 3 regime sets {M/W/D, W/D/12h, D/12h/4h} x
  3 exec sets {60/30/15@15m, 240/60/15@15m, 240/120/60@60m}, all stand_aside, fees
  {0, 0.0125}, PRE-REGISTERED in the datasheet (design + SP1-SP6 predictions) before any
  run. Amendments in-flight (justified, documented): SP500USDC.P has no TV backfill ->
  W2 fell back to OKX:BTCUSDT.P per the pre-registered rule; xyz MSTRUSDC.P turned out to
  HAVE backfill to 2025-12-02 -> W-venue upgraded to full runs + analytical
  window-slicing.
- **Sweep results (datasheet TVB-5 RESULTS section; the headline findings):**
  1. **The regime layer is universal damage containment, not return enhancement.** Every
     pairing in every sample improved: BTC 15m -73.67 -> -17.23; BTC 60m 2.5y -90.43 ->
     -36.71; xyz prefix -40.09 -> -12.61; OKX MSTR -9.06 -> +39.86 (@0.0125).
  2. **Regime speed is monotone-destructive** -- M/W/D > W/D/12h > D/12h/4h in every
     column of every window; the fast regime lands BELOW B-alone even at zero fee
     (anti-selective; the charter-S6 "correlated follower" failure mode observed
     empirically). Exec-span widening (240/60/15) is NOT a substitute regime layer.
  3. **The edge is instrument-specific and regime-local.** BTC: dead everywhere (B-alone
     -11.8% at ZERO fee over 7 months; ~0% gross over 2.5y at E3). Kill-regime LOCATED on
     the target instrument itself: xyz MSTR Dec-Feb chop is negative GROSS (-10.7%) while
     Feb-Jul is +254% gross.
  4. **S8 robustness:** off -90.43 < size_down -68.10 < stand_aside -36.71 in the 2.5y
     BTC spot-check -- the TVB-4 ordering generalizes.
  5. **SURPRISE (biggest open question): the venue gap REVERSES the assumed direction.**
     Same underlying, shared window, near-identical trade counts: xyz MSTRUSDC.P ctrlB
     @0.0125 = **+80.17%** vs OKX MSTRUSDT.P **-9.05%** (R1E1: +83.07 vs +39.88). The xyz
     TV backfill's provenance is UNVERIFIED -- flagged as a question per charter S0.
     TVB-6 job 1: cross-validate xyz TV bars against HL SDK candles before ANYTHING
     builds on xyz numbers.
- **Scorecard:** SP3 (E3 most fee-robust), SP5 (orderings replicate cross-instrument),
  SP6 (kill-regime exists + located) CONFIRMED; SP1, SP2, SP4 REFUTED with mechanisms
  (the useful kind -- documented in the datasheet).
- **New tooling:** `analysis/window_compound.py` (+3 tests; suite 9/9) -- window-sliced
  product(1+pp) compounding over dump trade lists (validated kind-window method), enabling
  shared-window venue comparisons without constrained re-runs. `tv_dump.mjs` closed-basis
  fix verified live (closed L/S sums exactly to totalTrades).

### Context for next session
- TVB-6 = xyz backfill verification FIRST (see `.session_startup_prompt.md`); everything
  else (venue adoption decision, MAE/solvency, slippage realism) sequences behind it.
- NO deployability language is warranted anywhere: the characterized system is a
  regime-local edge (MSTR-class, trending stretches) + a universal containment layer.
- OPERATIONAL: TradingView is now a Microsoft Store app -- `tv_launch` auto-detect fails;
  direct exe launch flow + full re-stage notes in `.session_startup_prompt.md`. Chart
  left at the control resting state (OKX:MSTRUSDT.P 15m, reg off, fee 0.0125); end-state
  regression green.

### Files created/modified
- MOD `docs/TVB2_control_AB_rerun.md` (TVB-5: ratification, repro re-run, sweep
  pre-registration, sweep results -- the session's core record).
- NEW `analysis/window_compound.py`, `tests/test_window_compound.py` (9/9 pass).
- MOD `scripts/tv_dump.mjs` (closed-basis L/S; header). MOD
  `.claude/commands/session-end.md` (range-pin rule).
- NEW `analysis/reference/tvb5_R*.json` (6 repro dumps) + `tvb5_{W1,W2,W3,WV}_*.json`
  (29 sweep dumps). NEW-to-git `docs/reviews/tvb{3,4}-codex-audit.md`.
- MOD `docs/HANDOFF.md` (TVB-4 review block flipped RETURNED + this entry),
  `docs/reviews/REVIEW_REQUEST.md`, `.session_startup_prompt.md`.
- Commits: `b99dccb` (ratification + review fold-in + repro), `124ef0c` (sweep), plus the
  session-end doc commit.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range below) and
> write a verbatim assessment to docs/reviews/tvb5-codex-audit.md. See
> docs/reviews/REVIEW_REQUEST.md (the pointer) and docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED (2026-07-03, local Codex CLI -- APPROVE-WITH-NITS, 2 LOW; audit
  at `docs/reviews/tvb5-codex-audit.md`; critical synthesis in the TVB-6 entry)
- Commits to review: `b99dccb^..d622be1` on `main` (= `6c855cf..d622be1`; sanity-checked:
  `git diff --name-status` lists all 57 session files). RANGE-PIN RULE applied: the caret
  keeps `b99dccb` (ratification + review fold-in) inside the reviewed diff.
- Scope / what changed: S8 ratification write-up; Codex TVB-4 fold-in (tv_dump
  closed-basis fix, range-pin rule, repro dumps); pre-registered 3x3 TF-set sweep across
  4 samples (35 runs) + results reading; window_compound analysis tool + tests.
- Focus areas (scrutinize these): (1) `analysis/window_compound.py` method validity --
  product(1+pp) over closed in-window entries under 100%-equity sizing, open-trade
  exclusion, half-open window semantics; (2) the tv_dump closed-basis assumption (is the
  trade list guaranteed entry-ordered with open trades last?); (3) the sweep READING --
  are "universal containment" and "monotone regime-speed destruction" over-claimed from
  9 cells x 4 samples? (4) the venue-gap flag -- is the shared-window comparison sound,
  and is the unverified-provenance caution adequate? (5) pre-registration integrity --
  were the in-flight amendments (BTC fallback, W-venue upgrade) justified or
  result-driven? (6) the S8 ratification arithmetic (~zero-expectancy suppressed stream).
- Reviewed by: Codex CLI (2026-07-03)
- Findings: 2 LOW, no blockers. (1) tv_dump closed-basis parser relies on the observed
  `reportData().trades` tail-open ordering with no fail-loud assertion -- add one. (2)
  "universal damage containment" should be worded "universal across tested samples/cells"
  in the next synthesis. Checks passed: range pin, no-request.security posture,
  window_compound method + tests, venue-gap arithmetic re-derived from dumps, S8
  arithmetic (~0.00225%/trade gross), pre-registration amendments read as justified.

---

## Session TVB-4: Two-layer regime built + ablated; stand_aside flips B positive; review pointer + guide (COMPLETE)

**Date:** 2026-07-03
**Status:** COMPLETE -- built the two-layer regime architecture (charter 3.3), ran the
ablation, and answered the charter S8 grey-handling question with data. Dual-model session:
Fable 5 designed + built + regression-gated; Opus 4.8 ran the matrix + recorded.

### What was accomplished
- **Review workflow upgrade:** new `docs/reviews/REVIEW_REQUEST.md` -- a stable pointer file
  external reviewers (Codex `/review`, cloud) are aimed at; `/session-end` rewrites it each
  session, `/session-start` flips it to RETURNED. Wired through EXTERNAL_REVIEW_PROTOCOL,
  reviews README, both slash commands. Retired the per-commit-approval rule in session-end
  (predated auto mode; commits/pushes now autonomous, secret-scan gate is the sole blocker).
- **TVB-3 Codex review RETURNED (APPROVE-WITH-NITS, 3 LOW), all agreed + triaged:**
  finding 3 (crossed-flag `bool()` coercion) FIXED -- `to_bool()` validates a real JSON
  boolean, malformed rows skip, +1 test (6/6 pass). Finding 1 (alignment guard) folded into
  the TVB-4 Pine. Finding 2 (short-leg MAE/solvency) deferred to the deployability stage.
- **Preflight 1 -- bar-magnifier fidelity: no material distortion.** B @0.0125 OFF -10.06%
  vs ON -11.13% (1 fewer trade); A bit-identical (verified via live-recompute control). The
  state-stop architecture is path-independent intrabar; magnifier stays OFF for the sweep.
  CARVE-OUT: any future price-stop variant is magnifier-sensitive, re-check then.
- **Preflight 2 -- kind-window bug-test: PASS.** A-priori windows from a price scan (KIND-UP
  Apr12-22 +43.8% B&H; KIND-DOWN Jun16-26 -36.5%). Zero-fee in-window compounding is
  unmissably positive and direction-coherent (A: 0 longs in the crash, 34/35 longs in the
  rally). Findings: A's down-capture is structurally weak at zero fee (25% vs 69% up); B
  fights the trend with ~half its trades -- the data-generated motivation for the regime layer.
- **Two-layer regime Pine (charter 3.3), regression GREEN.** Added an HTF M/W/D FTFC gate
  over the Control-B execution layer; `reg_mode` = off | stand_aside | size_down (grey at
  fixed a-priori 50%); no regime exit in v1 (reg_exit knob off). Plus the alignment guard
  (chart TF must TILE every enabled gate TF -- Codex finding 1; both guard paths verified
  firing live). Defaults = the TVB-3 control; regression PROVEN twice (pre- and post-restart:
  all 2811 reference trades byte-identical with reg_mode off).
- **Two-layer ablation (the headline).** OKX:MSTRUSDT.P, Control-B exec, window Feb25-Jul3:
  - @0.0125 real fee: control **-8.60%** (PF 0.981, DD 37.3%, Sharpe -0.10) -> stand_aside
    **+40.26%** (PF 1.195, DD 14.3%, Sharpe 0.75) -> size_down **+12.84%**. A ~49pp swing +
    sign flip from a regime filter alone.
  - stand_aside cuts trades 2814 -> 922 (67%) but keeps 90% of zero-fee P&L (+76.6 vs +84.7)
    -- the suppressed trades were disproportionately fee-burners (P4 confirmed dramatically).
  - **S8 DECISION (data-driven): stand_aside > size_down** on every axis at real fees.
    "Stand aside when the playbook stops" beats "trade smaller." Fable to ratify.
  - Predictions P1/P2/P4/P6 confirmed; P3 partial (small honest cost); P5 confirmed + LOCATED
    (regime late-entry tax at the V-bottom: core-rally +16.7% vs control +23.7%). SURPRISE:
    size_down wins the KIND-DOWN window (+20.1%) but loses the full-fee sample -- grey rule is
    regime-dependent (parked vol-conditional avenue, do not tune).
- **Manual backtesting guide:** `docs/guides/MANUAL_CONTROL_AB_GUIDE.md` -- step-by-step for
  the user's own cross-ticker control runs (fee ladder, history loading, sanity gates, refs).

### Context for next session
- TVB-5 = the priority-4 timeframe-set SWEEP with the two-layer as the ablation baseline.
  Ratify the stand_aside S8 decision first (Fable judgment); fold in the TVB-4 Codex review.
- The two-layer Pine is the go-forward baseline. Regime late-entry tax (P5) will bite harder
  in a sample with more sharp reversals -- the second regime window (regime-flattery guard)
  matters. Results still concentrate long (+29.80 vs short +10.46 @0.0125).
- OPERATIONAL: TV restart drops the strategy study (in-memory, not saved to layout) AND a
  bare relaunch over a running instance does NOT attach the debug port -- must Stop-Process
  the existing TradingView first, then relaunch with the CDP flag. Re-add the study, re-derive
  the entity id (changes every add) + id map. Full re-stage flow in `.session_startup_prompt.md`.

### Files created/modified
- MOD `pine/baseline_continuity.pine` (two-layer regime; Pine v6; slot "TFC Baseline"
  `USER;e7c8...` byte-identical, pineVersion 18).
- MOD `analysis/fee_rates_by_dex.py` + `tests/test_fee_rates.py` (crossed-flag fix; 6/6 pass).
- MOD `docs/TVB2_control_AB_rerun.md` (preflight 1, preflight 2, two-layer ablation sections).
- NEW `docs/reviews/REVIEW_REQUEST.md` (reviewer pointer); MOD EXTERNAL_REVIEW_PROTOCOL,
  reviews README, `.claude/commands/session-{start,end}.md`.
- NEW `docs/guides/MANUAL_CONTROL_AB_GUIDE.md`.
- NEW `scripts/tv_probe.mjs`, `scripts/tv_dump.mjs`, `analysis/reference/tvb4_*.json`
  (CDP probe + dump helpers + reference/run dumps).
- MOD `docs/HANDOFF.md`, `.session_startup_prompt.md`, `docs/reviews/REVIEW_REQUEST.md`.
- Memory: NEW TVB-4 (OpenMemory + auto-memory); auto-memory `feedback-autonomous-commit-push`.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range below) and
> write a verbatim assessment to docs/reviews/tvb4-codex-audit.md. See
> docs/reviews/REVIEW_REQUEST.md (the pointer) and docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED (2026-07-03, local Codex CLI -- APPROVE-WITH-NITS; audit at
  `docs/reviews/tvb4-codex-audit.md`; critical synthesis in the TVB-5 entry)
- Commits to review: `58c3ca9..bc9941f` on `main` (the two-layer Pine, ablation, docs; the
  review-workflow + fee-fix commits `5359756`/`9331d89` are pre-58c3ca9 if a wider range helps)
  -- NOTE (Codex finding 1, MEDIUM): this range EXCLUDES `58c3ca9` itself (the Pine commit);
  the reviewer compensated by reading the wider session context. Future pins: `58c3ca9^..`.
- Scope / what changed: two-layer regime Pine (M/W/D over Control-B, reg_mode modes,
  alignment guard); regression-proven; ablation run matrix; datasheet + review-pointer + guide.
- Focus areas (scrutinize these): (1) the `f_agg`/`long_permit`/`short_permit`/`size_scale`
  regime logic -- does stand_aside/size_down/off do exactly what's claimed? (2) the
  size_down `qty = strategy.equity * size_scale / close` arm-time approximation -- is it a
  fair half-size, any leak? (3) the alignment guard (tiling math for D/W/M vs intraday);
  (4) the regression-equivalence claim (reg_mode off == control); (5) the ablation reading,
  especially P4/P5 and whether the S8 stand_aside conclusion is over-claimed on one window;
  (6) kind-window compounding method (product(1+pp), in-window entry filter).
- Reviewed by: local Codex CLI (2026-07-03)
- Findings: APPROVE-WITH-NITS, no Pine logic blocker. 1 MEDIUM: the pinned range
  `58c3ca9..bc9941f` excludes the Pine commit itself (git left-endpoint exclusion).
  2 LOW: (a) tv_dump L/S counts include the open trade so the split sums to
  totalTrades+1 in the datasheet; (b) the real-fee headline rows (+40.26/-8.60/+12.84
  @0.0125) have no committed reference dumps -- only the zero-fee runs are preserved.
  Regime logic, off-mode inertness, alignment guard, size_down arm-time sizing all
  verified clean by the reviewer. Synthesis (agree/dispute/act): TVB-5 entry.

---

## Session TVB-3: Stale gate confirmed + fixed; corrected controls; margin artifact killed (COMPLETE)

**Date:** 2026-07-02
**Status:** COMPLETE -- all 6 amended-order priorities done. The FTFC gate WAS stale (preflight
N1 confirmed empirically), fixed via local period-open reconstruction; a TV margin-call deadlock
artifact was discovered and removed; the corrected-gate fee sweep REPLACES all TVB-1/2 numbers.

### What was accomplished
- **Settings dump (Codex 1 + N3):** full CDP decode of the strategy instance's inputs +
  properties (metaInfo().inputs id->internalID map). Answers: TVB-2 runs INCLUDED slippage=1
  tick/fill (in_24); bar magnifier OFF (in_32); sizing structurally 1x. Found the TV slot had
  drifted to the TVB-1 fee-test variant (v6, no leverage input). Datasheet patched: slippage
  wording corrected (runs were never slippage-free), checklist fee 0.0864%->0.0125% (Codex 3),
  superseded items annotated (N4).
- **P2a -- gate staleness CONFIRMED (N1 right).** Method deviation (justified): single-TF
  isolation of the strategy's own plotted gate values vs raw period opens, NOT the visual TFO
  overlay (the TFO indicator is itself lookahead-on). D-only: every bar of day N shows
  open(N-1); 60m-only: 43/43 non-boundary bars show the prior hour's open; the current open
  appears only on each period's LAST chart bar (simultaneous-close merge). All TVB-1/2 numbers
  characterized a "close vs prior-period opens" gate. Also verified: TV's OKX daily bars roll
  at 00:00 UTC. LESSON: an interim "gate looks current" read from the old 4-TF composite was
  WRONG (dead-session-polluted data + max/min masking) -- only single-TF isolation is decisive.
- **P2b -- ONE canonical Pine edit (plan approved):** gate -> `ta.valuewhen(timeframe.change(tf),
  open, 0)` (chart-local; backtest==live; same-TF = current bar open); trigger tick-offsets
  (high+mintick / low-mintick, strat-methodology strict-break); chart-TF<=gate-TF guard
  (runtime.error, verified firing); header fee note fixed (N5). Repo file and slot now
  byte-identical (Pine v6). Regression: 60m-only probe reads CURRENT 57/57.
- **DISCOVERY: TV margin-call deadlock.** 100%-equity sizing + default margin 100/100 =>
  every short margin-calls on its first adverse tick (equity==required at entry); on Apr 2 a
  margin-call/close race left an orphan +1.112-contract long that no strategy.close(id) could
  target => the first bridge run silently traded NOTHING for 3 months (order log + orphan
  arithmetic verified to the cent). FIX: margin_long=0, margin_short=0 (state-stop is the only
  exit, as designed). NOTE: TVB-1/2 short legs were margin-contaminated too.
- **Corrected-gate fee sweep (ACTUALS, replacing the geometric model).** Window Feb 25 10:00Z
  (data floor) -> Jul 3; buyHold -22.5% (the +3 tail days added a +19% rally):
  - A (M/W/D/60, 60m): 317 trades; 0% +50.0% PF 1.316; 0.0086% +42.0%; 0.0125% +38.6%
    (PF 1.245, DD 16.4%, Sharpe 0.87); 0.1% -20.4% PF 0.864.
  - B (60/30/15, 15m): 2801 trades; 0% +86.5% PF 1.143; 0.0086% +15.2%; 0.0125% **-7.4%**;
    0.1% -99.3%.
  - A's real-fee band matches the geometric prediction almost exactly; **B's sign FLIPS inside
    the real-fee band** (PF 0.98-1.03; corrected gate churns ~22% more) -- flagged as the
    session's surprise. A's edge is long-heavy (long +34.7% / short +3.9% @ 0.0125%).
  - Old-vs-new deltas bundle {gate fix + tick offsets + margin removal + 3-day window tail};
    decomposition deliberately not spent.
- **Jackson reader hardening (Codex 4; separate repo, commit `55e93f1`):** debug_sources
  propagated through getStrategyResults/getTrades/getEquity public returns; getEquity got the
  no-strategy debug branch; MAX_TRADES 20->500 cap (default stays 20); fixed three latent
  "evaluate is not defined" DI bugs in chart core (getVisibleRange/scrollToDate/symbolInfo --
  scrollToDate bit live this session). 123/123 non-e2e tests pass; 2 pre-existing live-TV
  compile failures verified identical on the pre-edit tree. Deploys at next MCP restart.
- **Sanitized fee artifact (Codex 2):** `analysis/fee_rates_by_dex.py` -- counts + RATES by
  {dex, crossed} from a LOCAL fills export; sanitization contract enforced and unit-tested
  (no absolute notionals in output). 4 new tests; suite 5/5.

### Context for next session
- TVB-4 = EXPERIMENTATION PHASE (charter S5) after two cheap preflights: bar-magnifier check
  (B knife-edge most exposed) and the kind-window bug-test. Then two-layer design (plan mode).
  See `.session_startup_prompt.md` for the full order + operational notes.
- Input id map SHIFTED this session when margin args were added (margins now in_25/26; a
  stale-id write set currency=0 => "Can't parse pine"; fixed by remove+re-add). Re-derive ids
  after ANY source change -- the rule has now bitten twice.
- Strategy on chart: `dILiiy` (re-check), OKX:MSTRUSDT.P 15m, Control-B enables, in_23=0.1.
  User's personal chart was displaced from CBOE:DRAM 1m -- restore or leave per user.
- TV session-disconnect gotcha: our own kill+relaunch triggers "accessed from another device";
  while disconnected, layout/tab ops and restudies silently no-op. Click Connect.

### Files created/modified
- MOD `pine/baseline_continuity.pine` (Pine v6 canonical: gate fix + tick offsets + guard +
  margin 0/0 + corrected header; byte-identical to slot "TFC Baseline" `USER;e7c8...`).
- MOD `docs/TVB2_control_AB_rerun.md` (TVB-3 sections: settings dump, P2a proof, P2b +
  artifacts, corrected-gate sweep + reading).
- NEW `analysis/fee_rates_by_dex.py`, `tests/test_fee_rates.py`.
- MOD `.session_startup_prompt.md`, `docs/HANDOFF.md`.
- SEPARATE repo: `tradingview-mcp-jackson` commit `55e93f1` (reader hardening + DI fixes).
- Memory: NEW `tvb3-stale-gate-margin-artifacts`; updated `tvb2-fee-resolved-real-taker`,
  `tvb1-controlB-fee-churn-finding` (supersession notes), MEMORY.md index.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range below) and
> write a verbatim assessment to docs/reviews/tvb3-codex-audit.md. See
> docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED 2026-07-03 (via the new Codex /review command reading
  docs/reviews/REVIEW_REQUEST.md) -- APPROVE-WITH-NITS; synthesis below.
- Commits to review: `93f16d7..HEAD` on `main` (workspace) + `55e93f1` in
  `tradingview-mcp-jackson` (reader hardening)
- Scope / what changed: gate staleness empirically confirmed + fixed (ta.valuewhen local
  period-open recon); margin-call deadlock artifact removed (margin 0/0); corrected-gate
  2x4 fee sweep replaces TVB-1/2 numbers; sanitized fee-rate script; jackson DI/debug fixes.
- Focus areas (scrutinize these): (1) the P2a staleness proof method (single-TF isolation --
  is the simultaneous-close merge interpretation right?); (2) ta.valuewhen(timeframe.change)
  reconstruction edge cases (partial first period, non-aligned chart TFs, warmup-na semantics);
  (3) whether margin 0/0 hides anything a 1x cash-margin reality would enforce; (4) the
  corrected-sweep numbers and the B sign-flip reading; (5) the bundled-delta attribution caveat;
  (6) fee_rates_by_dex.py sanitization completeness.
- Reviewed by: local Codex CLI (docs/reviews/tvb3-codex-audit.md)
- Findings: 3 LOW -- (1) ta.valuewhen recon is only exact when every enabled gate TF
  aligns with the chart TF; guard only enforces chart<=gate; (2) margin 0/0 removes any
  solvency/liquidation constraint a real 1x short book would enforce -- add an MAE/
  liquidation-distance check before deployability language; (3) fee_rates_by_dex.py
  coerces `crossed` with bool() -- a stringified "false" would misclassify as taker.

**Critical synthesis (TVB-4, 2026-07-03):** all three findings AGREED on inspection.
(1) is real and matters for the S5 sweep specifically: for a non-dividing chart TF the
first chart bar of a new period can OPEN before/after the true boundary, so the
"period open" silently becomes an approximation -- the alignment guard (every enabled
gate TF an integer multiple of chart TF; D/W/M require chart TF to divide 1D) must land
in the Pine BEFORE the timeframe-set sweep runs arbitrary combos (plan-mode item,
folded into sweep prep). (2) agreed and already on the deferred list as slippage/
deployability realism -- shorts' MAE vs 1x cash margin gets checked before any
deployability verdict, not for control characterization. (3) FIXED this session
(isinstance bool check + malformed-row skip + test). Also validated: the reviewer's
approval notes match our own P2a/P2b reading (single-TF isolation as ground truth,
lookahead-free strategy source).

---

## Interim 2026-07-01: Fable 5 preflight review (one-off; review only, no session work)

Pre-TVB-3 fresh-eyes review by Fable 5 (TVB-1/2 ran on Opus 4.8 while Fable 5 was offline).
Full findings: `docs/reviews/tvb3-preflight-fable5-review.md`. Summary:
- All 4 Codex TVB-2 findings CONFIRMED against sources -- adopt all (slippage recording,
  sanitized fee artifact, 0.0864% checklist patch, reader `debug_sources` propagation).
- NEW N1: the HTF-open gate is near-certainly STALE (`request.security` + `lookahead_off`
  returns the PRIOR period's open on historical bars) AND backtest-vs-live asymmetric
  (realtime returns the developing bar) -- a repaint-class divergence, stronger than the
  TVB-1 "fidelity, not a leak" framing. P2a/P2b therefore RESEQUENCED BEFORE the real-fee
  re-runs (else the four runs characterize the wrong gate and get redone).
- NEW N2: the geometric fee model was VERIFIED -- anchored at the 0% actuals it reproduces
  both 0.1% actuals to ~0.1pp; the A +38..42% / B +5..25% real-fee estimates are well
  grounded; the re-run is confirmation, and a material deviation would itself be a finding.
- `.session_startup_prompt.md` NEXT order amended accordingly (user-approved 2026-07-01).
  No implementation files were changed by the review.

---

## Session TVB-2: TV MCP reader fix + clean controls + fee saga resolved (COMPLETE)

**Date:** 2026-06-30
**Status:** COMPLETE -- TV MCP Strategy Tester readers FIXED + deployed + verified live; controls A/B
re-characterized cleanly; fee model resolved to GROUND TRUTH (real xyz taker ~10x cheaper than
assumed), REVERSING the "B dead by fees" verdict; binding constraint re-identified as slippage.

### What was accomplished
- **TV MCP reader FIXED + deployed + verified (P1, the session's main effort).** The new TV Strategy
  Tester UI broke the `tradingview-mcp-jackson` readers. Root cause was NOT what TVB-1 assumed:
  (a) finder false-positive -- matched `s.performance`, a profiling method on EVERY study, so it
  grabbed the first indicator; and `metaInfo().isStrategy` does not exist in the new UI. (b) data
  shape -- `reportData()`/`ordersData()` are methods; metrics in `reportData().performance.{all,long,
  short}`; trades in `reportData().trades`. Fixed all three readers (getStrategyResults/getTrades/
  getEquity) to detect via `isTVScriptStrategy` and pull the new shapes. Verified live on
  OKX:MSTRUSDT.P. Committed to jackson `main` (commit `fb2a788`).
  - The TVB-1 "relaunch to load the diagnostic" premise was a red herring: the diagnostic ran but its
    output was dropped by the reader's node-side outer return (field-pick). The right instrument was
    a standalone CDP probe reusing jackson's `connection.js` evaluate() -- iterate freely vs live TV,
    restart the MCP only to DEPLOY.
- **Controls A/B re-characterized cleanly** (clean JSON, no screenshots). 2x2 (A/B x fee 0%/0.1%),
  same window (Feb 25 - Jun 30, ~-30% downtrend), 1x, bidirectional:
  - B (60/30/15, 15m): 2301 trades; @0% +85.8% PF 1.186; @0.1% -98.1% PF 0.400 (commission 10545 > capital).
  - A (M/W/D/60, 60m): 261 trades; @0% +48.2% PF 1.373 Sharpe 1.84; @0.1% -12.0% PF 0.906.
  - Replicates + extends TVB-1; A dominates B risk-adjusted at ~9x fewer trades.
  - NOTE: the on-chart strategy was found as a HYBRID (M/W/D/60 on a 15m chart) -- neither control;
    inputs decoded to pin config. A vanished template-added instance was long-only (the "all-long"
    389-trade run); the bidirectional instance is the real one.
- **Fee saga RESOLVED to ground truth (the session's biggest finding).** User supplied real HL fills.
  An initial fee/notional inference gave a wrong "97% maker" read; the user's "I trade market orders"
  testimony flagged it; re-classified by HL's authoritative `crossed` flag (validated: native-crypto
  taker = HL published 0.0432% exactly). Result: xyz is 86.5% TAKER, and the real xyz TAKER rate is
  CHEAP -- ~0.0086% modal / 0.0125% notional-weighted, ~8-12x BELOW the 0.1% the backtest used.
  - REVERSES the fee verdict: at real cost A ~= +38-42% (clear winner), B ~= +5-25% (near breakeven),
    NOT dead. "Turnover fatal for B" was largely a fee artifact (~10x too high). These are GEOMETRIC-
    MODEL estimates -- must be CONFIRMED by actual re-run.
  - BUT the binding constraint MOVED to SLIPPAGE: user fills market/taker both legs; B = 2301
    round-trips = 2301x slippage; B near-breakeven at zero slippage is exactly where realistic
    slippage decides the sign. Charter S6 flag: a real mechanism (cheap fees) must not launder an
    optimistic "deployable" verdict.

### Context for next session
- Reader WORKS -- clean JSON via data_get_strategy_results/data_get_trades/data_get_equity. TV must
  run on CDP (MSIX: `Get-AppxPackage *TradingView*` + Start-Process `--remote-debugging-port=9222`).
  Each Claude relaunch kills the Claude-launched TV -> relaunch it.
- The A/B-at-real-fee numbers are MODEL estimates, NOT fresh backtests -- re-run at 0.0086% and 0.0125%.
- SLIPPAGE is the new binding constraint (deferred so far) -- model before any deployability call.
- Strategy `35dVw8` (`Baseline TFC [TVB-1]` / slot "VIX Spike Alert" / id `USER;e7c8...`) left at
  M/W/D/60, 0.1% fee, 15m chart (as-found hybrid). Input ids: in_2=M, in_4=W, in_6=D, in_8=60,
  in_10=30, in_12=15 (bool enables); in_23 = commission percent.
- P2a (HTF-open currency) + P2b (period-open recon + tick-offset + TF guard) still pending; the
  `Timeframe Continuity [TFO]` indicator is now on the chart for the overlay.

### Files created/modified
- NEW `docs/TVB2_control_AB_rerun.md` (control 2x2 + fee model + ground-truth resolution; canonical).
- MOD `docs/HANDOFF.md`, `.session_startup_prompt.md`.
- SEPARATE repo (committed): `tradingview-mcp-jackson/src/core/data.js` reader fix (`fb2a788`, main).
- Memory: updated `tvb1-tv-mcp-reader-newui` (FIXED + new-API ref); new `feedback-relaunch-is-cheap`;
  new `tvb2-fee-resolved-real-taker`.
- User-side: `Downloads/TVB2_fee_handling.md` (Claude Desktop fee analysis -- superseded by the repo datasheet).

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range below) and write a
> verbatim assessment to docs/reviews/tvb2-codex-audit.md. See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED
- Commits to review: `bd2c760..HEAD` on `main` (workspace) + `fb2a788` in `tradingview-mcp-jackson` (reader fix)
- Scope / what changed: TV MCP reader fix (jackson); clean A/B control re-characterization; fee model
  resolved to ground truth (real taker ~10x cheaper -> verdict reversed; slippage now binding).
- Focus areas (scrutinize these): (1) fee ground-truth method (HL `crossed` flag + validation);
  (2) the geometric-model A/B-at-real-fee estimates -- should be confirmed by actual re-run, not trusted;
  (3) the "slippage is now binding, esp. for B" claim and the churn math; (4) whether the
  "breakout entry is intrinsically taker -> maker is not a free fee swap" reasoning holds;
  (5) reader-fix correctness in `jackson/src/core/data.js`.
- Reviewed by: local Codex CLI
- Findings: see `docs/reviews/tvb2-codex-audit.md` (overall NEEDS-CHANGES; 2 medium, 2 low)

---

## Session TVB-1: Baseline continuity strategy + A/B fee characterization (COMPLETE)

**Date:** 2026-06-28
**Status:** COMPLETE -- baseline control built + characterized; naive baseline KILLED at real
HIP-3 fees; turnover identified as the dominant lever.

### What was accomplished
- Built `pine/baseline_continuity.pine`: ONE parameterized `strategy()` =
  `{2-trigger (raw level cross via breakout STOP orders -> intrabar fill) + FTFC gate
  (chart close vs each enabled TF period-open, lookahead_off) + close-based state-stop}`,
  both directions, `leverage` input. Compiles clean; lookahead audit PASS (single
  `request.security`, `lookahead_off`; gate uses only period-open = non-leaking).
- Designed WITH user (plan approved): two a-priori controls, single-layer, state-stop only,
  fixed-size, `OKX:MSTRUSDT.P`. FTFC gate reconciled to the TFO indicator's `close > period-open`
  (NOT the skill's bar-type TFC) -- flagged per ambiguity policy; charter governs.
- Results on `OKX:MSTRUSDT.P`, Feb 25 - Jun 28 2026, 1x:
  - **Control B** (60/30/15, 15m): 2263 trades, 27.04% win, **PF 0.645**, MaxDD 81.79%, ~ -81%.
  - Fee-isolation (B, zero fees): **PF 1.284**, 37.65% win, MaxDD 14.66% -> raw edge POSITIVE;
    fees/churn (2263 round-trips) are the killer, not the signal.
  - **Control A** (M/W/D/60, 60m): 258 trades (~9x fewer), 34.11% win, **PF 1.131 (net +)**,
    MaxDD 14.79% -- clears OKX fees.
  - **Control A @ HIP-3 fees** (commission 0.10%): **PF 0.921 (net LOSER)**, 30.62% win,
    MaxDD 22.37% -- does NOT clear real venue costs.
- **VERDICT:** continuity gate has a faint real edge; turnover reduction (B->A) was necessary
  but NOT sufficient at real HIP-3 fees. A deployable version needs per-trade edge clearing
  ~0.2% round-trip -> MORE selectivity (two-layer regime filter, compression filter, re-entry
  governor), not just a slower gate. The exploration did its job: killed the naive baseline and
  located the bar.
- Fixed the `tradingview-mcp-jackson` reader FINDER (overlay strategies now matched; was
  wrongly `is_price_study`-gated) in `src/core/data.js` (SEPARATE repo, uncommitted). The new
  TV Strategy Tester UI ALSO changed the data-access API (`ordersData`/`reportData` reshaped);
  a diagnostic is staged but needs a full Claude Code relaunch to load + finish.

### Incident (resolved)
- Overwrote the user's saved "VIX Spike Alert" TV script with the baseline (`pine_new` did not
  create a separate slot; `smart_compile` auto-saved over it). User has a backup; baseline source
  is safe in the repo. LESSON: `pine_get_source` to verify the slot BEFORE `pine_set_source`.

### Context for next session
- Reader: a full Claude Code relaunch loads the staged `data.js` diagnostic -> read its dump
  (new TV data API) -> apply data-access fix -> relaunch -> clean JSON reads. Until then,
  screenshots (close editor via its X ~1884,33; dismiss CLUSDT.P alert popups).
- Canonical strategy = `pine/baseline_continuity.pine` (leverage 2x default, Control B 60/30/15
  defaults). Set `leverage=1` for sizing-agnostic edge reads. Control A = enable M/W/D/60 + chart 60m.
- Leverage is NOT an edge lever (per-trade metrics invariant; compounded curve concave +
  liquidation cap). Characterize at 1x; size via vol-targeting on a ROBUST edge later.

### Codex external audit + Claude critical review (post-TVB-1)
Codex audited `baseline_continuity.pine` + the TFO indicator (full verbatim text in
`docs/reviews/tvb1-codex-audit.md` -- read it against this synthesis, don't trust either blindly).
My critical synthesis -- do NOT assume Codex right; the starred item cuts both ways:

- **No classic lookahead LEAK in the baseline** (HTF `open` + `lookahead_off`). The TFO indicator
  IS unsafe as a backtest source (HTF `high/low` under `lookahead_on`) but we never used it as one.
  => TVB-1 results are NOT leak-inflated fiction. CONFIRMED.
- ***MUST VERIFY -- HTF-open currency.** My code comment asserts `lookahead_off` returns the
  CURRENT period's open. That was OVERCONFIDENT and may be WRONG: `lookahead_off` reveals an HTF
  bar aligned to its CLOSE and applies to the whole `[o,h,l]` tuple, so for true HTFs (D/W/M on a
  60m chart) it may return the PRIOR period's open => a stale/lagged gate. This is a FIDELITY bug,
  NOT a leak (prior open is fully known; results stay honest). VERIFY empirically: overlay the
  strategy's FTFC bar-coloring vs the TFO indicator (lookahead_on = current period). Match => fine;
  differ => stale opens. Either way ADOPT the unambiguous local reconstruction:
  `f_period_open(tf) => ta.valuewhen(timeframe.change(tf), open, 0)` (no `request.security`).
- **Model fidelity (valid):** the baseline is a "prior-close TFC-gate + resting breakout stop",
  NOT "check TFC at the exact intrabar break". Both legitimate; ours is the conservative, safe one.
- **The 1m reframe (the gem -- resolves the parked 1m idea):** for "TFC-at-the-break", run on a
  LOWER chart TF (1m/2m/5m) for intrabar fidelity but reconstruct the EXECUTION-TF (15/30/60) prior
  highs/lows for the TRIGGER and check the gate intrabar -- do NOT trigger off 1m bars (the naive
  version's flaw). A distinct VARIANT to build/compare, not a fix.
- **Adopt (low-risk fidelity):** trigger tick-offset (`stop = high + syminfo.mintick` /
  `low - syminfo.mintick`) to force a strict break vs equal-high touch (matches strat-methodology
  `H[1]+tick`); enforce chart-TF <= enabled-TF via `runtime.error`.
- **Variant, NOT control (charter ablation discipline):** catastrophic price fail-safe stop and the
  re-entry governor are charter Section 8 open questions -- test as ablations, do NOT bake into the
  minimal control (fail-safe matters more once leverage > 1; state-stop is close-based).
- **`close == open`:** TFO treats equality as down; ours as neutral (intentional). Negligible on
  liquid perps; only matters for exact TFO replication.
- **Proposed next-session order:** VERIFY HTF-open currency -> adopt local period-open recon +
  tick-offset + TF guard -> RERUN A/B fee characterization (confirm findings hold) -> THEN
  two-layer / TFC-at-break variant / governor as ablations.

### Files created/modified
- NEW `pine/baseline_continuity.pine`; MOD `pine/README.md` (control presets), `docs/HANDOFF.md`,
  `.session_startup_prompt.md`.
- Reference (user-added at root): `Timeframe_Continuity_Claude_Discussion.md`,
  `Timeframe_Continuity_Pinescript.pine` (the source discussion + the TFO indicator).
- SEPARATE repo, uncommitted: `tradingview-mcp-jackson/src/core/data.js` (reader finder fix + diagnostic).
- Memory: `tvb1-controlB-fee-churn-finding.md`, `tvb1-tv-mcp-reader-newui.md`.

---

## Session TVB-0: Workspace Bootstrap (COMPLETE)

**Date:** 2026-06-27
**Status:** COMPLETE -- standalone workspace scaffolded, MCP wired, conventions mirrored.

### What was accomplished

- Created standalone git repo `C:\Strat_Trading_Bot\tradingview-backtesting` (branch `main`).
- Wrote `CLAUDE.md` adapted for this domain: Pine-first vehicle, crypto-perp data rules (NOT
  the ATLAS equity/RTH orthodoxy), and the charter's epistemic stance encoded as binding rules.
- Moved the governing design doc out of vbt-workspace `Temporary/` to
  `docs/ATLAS_Timeframe_Continuity_Charter.md`.
- Wired the `tradingview` + `openmemory` MCP servers in `.mcp.json` (TRACKED here on purpose --
  no secrets -- so the wiring travels with the repo, fixing the vbt-workspace gitignore gotcha).
- `.claude/settings.json`: `ui_evaluate` denied (Tier 1), MCP servers enabled, and only the
  domain-agnostic global hooks kept (trading safety guard, ruff lint, test gate). The
  VBT/STRAT-Python guardians from vbt-workspace were intentionally NOT ported (Pine-first repo).
- Light `uv` Python project (`pyproject.toml`) for the analysis layer; smoke test added.
- Ported + adapted slash commands: `/session-start`, `/session-end`, `/pre-commit`.
- Seeded `.session_startup_prompt.md` with the TVB-1 plan.

### Context for next session

- Nothing strategic is built yet -- only the scaffold. The first real task (TVB-1) is to design
  and write the **baseline strategy()** WITH the user (charter Sections 3-4). This touches STRAT
  detection logic, so it is a strat-methodology STOP-and-ASK zone -- design before coding.
- The TradingView MCP install/gotchas are documented in the master guide at
  `vectorbt-workspace/docs/guides/TRADINGVIEW_MCP_INSTALL.md`; this workspace's
  `docs/guides/TRADINGVIEW_MCP_SETUP.md` is the local pointer + delta.

### Files created

Scaffold only -- see `git log` for the bootstrap commit. No strategy or analysis logic yet.

---
