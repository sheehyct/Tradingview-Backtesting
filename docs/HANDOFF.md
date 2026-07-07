# HANDOFF -- tradingview-backtesting

> Newest session entry at the TOP. Keep under 1500 lines; archive older entries to
> `docs/session_archive/` when it grows past that.

---

## Session TVB-8: VBT breadth port Phases 0-4 -- THE EQUIVALENCE GATE IS GREEN (COMPLETE)

**Date:** 2026-07-06/07
**Status:** COMPLETE -- the port plan's Phases 0-4 built, verified, and pushed in
one session; the Phase-3 trade-for-trade gate is GREEN on all 8 cells. Last
Fable 5 session (judgment-heavy Pine-semantics port front-loaded per plan);
Opus 4.8 takes over from TVB-9.

### What was accomplished
1. **Codex TVB-7 review folded in** (session start, 2026-07-05): the 1 LOW
   verified real and fixed (`VBT_BREADTH_PORT_PLAN.md:20` net->GROSS wording);
   verbatim audit committed; statuses flipped. All reviewer recomputations had
   matched our record; nothing disputed. (This entry IS the critical synthesis:
   AGREE on the LOW -- the fix mattered because the plan is implementation-
   facing spec; the queued Pine comment correction stays attached to the next
   Pine-touching deployment.)
2. **VectorBT Pro v2026.6.27 installed IN THIS WORKSPACE** (user decision;
   workspaces stay separate). Kept OUT of git entirely: install guide
   (`vectorbt_pro_install.md`) gitignored -- remote is PUBLIC (verified via gh),
   DMCA exposure; package in .venv only, NOT pyproject/uv.lock (public clones
   still sync/test). numpy capped <2.5 + relock (numba import ceiling; `uv run`
   resyncs lock pins every invocation). Port plan AMENDED: implementation runs
   HERE; module home `tfc/`; fixture-copy step dropped (gate reads committed
   `analysis/reference/` directly).
3. **Codex-skill cross-workspace confusion DIAGNOSED + fix prompt delivered**
   (user ran it): single global `~/.codex/skills/session-review/SKILL.md`
   hardcodes this repo's absolute REVIEW_REQUEST path while vectorbt-workspace
   uses a different contract (HANDOFF block + EQUITY-<N>_review.md, no
   REVIEW_REQUEST.md) -> invoked there, it reviews the wrong repo. Prescribed
   fix: workspace-RESOLVING skill (git rev-parse from cwd; REVIEW_REQUEST.md
   else HANDOFF block; STOP if neither), delete the stale deprecated
   `~/.codex/prompts/session-review.md`.
4. **Phase 0-1 (calibration + periods).** Dump-driven calibration GREEN on all
   8 cells: fill conventions EXACT on ~20,300 closed trades (intrabar stop
   fill, gap-through at open -- 29% of 15m entries, exits next-open, adverse
   slip both sides); qty rule exact minus 2-3 floor-boundary cases (plan risk 1
   predicted 1-3). **CALIBRATED-FACT CORRECTION: dump `pp` =
   pv/(q*ep*(1+comm)) -- return on entry COST BASIS incl. entry commission
   (<= 8.3e-9 on all cells), NOT return on equity (~1.4e-4 err)** --
   indistinguishable at 100% sizing except on gap-through fills; zero-fee cell
   isolates the commission term. Corollary recorded: `window_compound.py`
   product(1+pp) is a ~5bp/4,308-trade approximation (fine for the recorded
   window COMPARISONS; equity must chain pv). `tfc/periods.py` pins the
   valuewhen seed semantics by test (M Jan-1, W Monday Dec-8, D Dec-3;
   change[0]=False). PREFIX RULE established: gov2 dumps carry live tail-drift
   trades past the committed bar files (contiguous, asserted).
5. **Phase 2-3 (simulator + THE GATE).** `tfc/simulator.py` = two-phase bar
   loop in Pine execution order; all trigger/stop arithmetic in INTEGER TICK
   SPACE (float high+mintick can exceed the true sum and miss fills TV takes).
   **GATE GREEN, first run for 7/8 cells: all 8 reference cells PASS
   trade-for-trade -- 20,429 closed trades, et/xt/dir exact, fills 2.8e-14,
   pv at serialization floor, pp <= 5e-9, both open-position boundaries match;
   ctrlB headline net to 1.3e-8; ~0.4s total.** One adjudication (plan risk
   1's own fallback): ctrlB_0125_s10 trade 686 sits 6.4e-6 below an integer
   qty boundary (TV's internal float path holds ~1e-6 USD more equity); a full
   scan shows NO other trade within 2e-5 of a boundary across ~20,300, so
   Q_FLOOR_EPS=1e-5 resolves it and provably cannot false-flip anything else.
   Micro-behavior tests pin re-arm gap, gap-through basis, one-bar stop life,
   equality-grey, governor block/win/reset. POLICY now enforced by
   `tests/test_tfc_equivalence_gate.py`.
6. **Phase 4 (resampler + providers, live-verified).** `tfc/resample.py`:
   15m->60m reproduces TV's own 60m file 5,102/5,103 exact OHLCV, 15m->1D
   213/214 -- both mismatches are the live LAST bar at capture time (pull
   skew), not aggregation error; period-start stamping matches TV (partial
   listing day stamps 00:00). `tfc/providers.py`: HL candleSnapshot + OKX
   history-candles (paginated, INTRADAY-ONLY guard -- OKX HTF anchors UTC+8;
   meta records served-vs-requested + floor_hit). LIVE: HL fetch reproduces
   the committed tvb6 HL candles EXACTLY on overlap; OKX pagination sane.
   Network tests opt-in via TFC_NETWORK=1; suite 70 passed + 2 skipped.
7. **Breadth universe scoped with user (directives binding for TVB-9):**
   probe: XYZ100 since 2025-10-13, SP500 since 2026-03-18, DRAM since
   2026-05-04 (1h capped ~5,000; 15m ~52d). User: NO keep/kill verdicts off
   young listings -- regime-mapping only; DRAM SKIPPED (too thin); widening to
   other a-priori xyz equity perps welcome if runway allows.

### Context for next session
- PRIMARY: Phase 5 -- MSTR-on-HL-bars pilot FIRST (venue-bar drift calibration),
  then pre-register (user approves) and run the regime-mapping breadth pass.
  See .session_startup_prompt.md for the full directive block.
- The gate is the contract: any simulator change must keep 8/8 green.
- `uv sync` strips vectorbtpro; reinstall via the gitignored guide (cached).
- No TV/chart work happened this session; resting state untouched from TVB-7.

### Files created/modified
- NEW `tfc/` package: `__init__.py`, `config.py` (f_guard port), `periods.py`,
  `tv_reference.py` (loaders + 8-cell registry), `simulator.py`,
  `equivalence.py`, `resample.py`, `providers.py`.
- NEW `scripts/tfc_qty_calibration.py`, `scripts/tfc_gate_report.py`.
- NEW tests: `test_tfc_periods.py`, `test_tfc_reference.py`,
  `test_tfc_simulator.py`, `test_tfc_equivalence_gate.py`,
  `test_tfc_resample.py`, `test_tfc_providers.py` (suite 25 -> 72).
- MOD `docs/VBT_BREADTH_PORT_PLAN.md` (venue amendment; gross-arming LOW fix;
  pp calibrated-fact correction), `docs/TVB2_control_AB_rerun.md` (TVB-8
  section), `.gitignore` (VBT Pro DMCA guard), `pyproject.toml` (numpy <2.5,
  network marker), `uv.lock`, `docs/HANDOFF.md`, `docs/reviews/REVIEW_REQUEST.md`,
  NEW `docs/reviews/tvb7-codex-audit.md` (verbatim, committed).

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb8-codex-audit.md.
> See docs/reviews/REVIEW_REQUEST.md (the pointer) and docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: REQUESTED
- Commits to review: {pending push -- pinned after session-end push}
- Scope / what changed: VBT breadth port Phases 0-4 (tfc/ package, calibration,
  simulator, equivalence gate, resampler, providers); gate GREEN 8/8; pp
  cost-basis correction; Q_FLOOR_EPS adjudication; VBT Pro in-workspace install
  with DMCA gitignore guard; Codex TVB-7 fold-in.
- Focus areas (scrutinize these): (1) does the equivalence comparator PROVE
  trade-for-trade equivalence, or do the tolerances/prefix rule leave an escape
  hatch for systematic bias? (2) is Q_FLOOR_EPS=1e-5 an adjudicated float
  artifact or a tuned parameter in disguise (knife-zone scan logic)? (3) the pp
  cost-basis correction inference (zero-fee control) + the window_compound
  approximation scoping; (4) simulator Pine-order fidelity vs
  pine/baseline_continuity.pine (loss-arm before alignment reset; flat-only
  arming; one-bar stop life; tick-space arithmetic); (5) providers: HL
  floor_hit semantics, OKX UTC+8 guard, the 2-day overlap cross-check breadth;
  (6) resampler last-bar mismatch explanation. Standing: request.security
  lookahead (NO Pine changes this session), model fidelity, fee/turnover math,
  sample-vs-structural reasoning (breadth pre-registration plan).
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb8-codex-audit.md exists)

---

## Session TVB-7: governor cross-venue VERIFIED; VBT port plan APPROVED; cost realism closed; Codex fold-in -> gross-arming discovery (COMPLETE)

**Date:** 2026-07-04
**Status:** COMPLETE -- all three startup priorities done PLUS the Codex TVB-6
review folded in same-session. Fable 5 session (mechanical re-verification, plan-
mode design with user, analysis tooling, review adjudication).

### What was accomplished
1. **Governor v2 cross-instrument re-verification -- KEEP-VERDICT UPGRADED
   (provisional -> cross-venue-verified on the MSTR underlying).** Pre-registered
   CV1-CV4 (datasheet) then 16 paired fresh runs: OKX:MSTRUSDT.P 15m ctrlB/R1E1
   x {0, 0.0125} x {s1, s10}; OKX MSTR 60m R1E3 (floor ALSO Feb-25 -- "60m
   deeper" refuted for OKX, listing-driven); BTC 60m R1E3 2.5y. CV2 keep-rule
   mirror PASS: R1E1+gov2 beats ungoverned at BOTH cost points (+42.44 vs +40.08
   s1; -56.62 vs -59.58 s10), gross higher (+78.16 vs +76.61), cut -3.5% (no
   starvation, CV1). Direction non-negative 8/8 pairs; MAGNITUDE PATH-LOCAL
   (+12pp xyz -> +2-3pp OKX; ctrlB gross flat on OKX vs +40pp on xyz). BTC
   stays negative governed (CV4 -- no manufactured edge). NOT universal-
   structural (no non-MSTR positive-edge instrument exists). Repro gates green
   (fresh ungoverned matched TVB-5 rows within tail drift). 16 dumps committed.
2. **VBT breadth-engine port DESIGNED with user (plan mode) and APPROVED** --
   `docs/VBT_BREADTH_PORT_PLAN.md` is the design of record. User forks decided:
   custom bar-loop simulator (not VBT callbacks); hard gate = 4-cell mechanism
   cover + 4 secondary regression cells; crypto perps first (equities = later
   phase, seam only). Planning VERIFIED calibrated facts against committed
   dumps: TV qty rule = floor(equity/(slipped_stop*(1+comm))/step)*step; pv
   formula (worst err 4.9e-5); gap-through fills at open. Implementation runs
   in a vectorbt-workspace session; Phase 3 (8 gate cells green) is a hard
   policy gate before ANY Python number enters the record.
3. **Cost realism closed (both TVB-6 carries).** (a) Live L2 sampling
   (`analysis/l2_book_impact.py`, 20 snapshots): at ~90 contracts per-fill cost
   vs mid = ~20-40 TV-ticks median, p90 ~30-50 -- BETWEEN s25 and s50, not near
   s10; caveat WEEKEND-NIGHT book (conservative); weekday-RTH re-sample queued.
   (b) Funding model (`analysis/funding_model.py`, 5,124 hourly events since
   listing): drag modest at 1x (-2.5 to -4.9pp, no sign flips) but INVERTS the
   fee gradient -- scales with time-in-market, so slow cells pay ~2x churn
   cells (R1E3 -4.77 / ctrlA -4.93 vs ctrlB -2.78); linear in leverage. +8
   tests (suite 25/25); evidence committed (L2 samples time-perishable).
4. **Codex TVB-6 review RETURNED + folded in (APPROVE-WITH-NITS, 3 LOW, all
   AGREED + actioned).** (1) 60m MAE rows corrected to committed replay (worst
   short 8.42%/7.22x, long 5.54%; 15m rows replay exactly; solvency
   unaffected). (2) tv_bars.mjs now persists tick metadata; equalizer evidence
   committed (tvb7_symbolinfo.json). (3) **THE DISCOVERY: the governor arming
   test `strategy.closedtrades.profit() > 0` reads GROSS of commission** --
   adjudicated without touching the Pine: boundary trades real (137/4,191);
   zero-fee vs fee'd governed sequences identical over 4,191 trades; at 1%
   commission the first 575 trades still match exactly, diverging only at the
   qty=0.001 equity floor (sizing artifact). All governed RESULTS stand (as-
   deployed behavior; keep-rule applied to what ran); the "net of fees"
   description corrected in datasheet + VBT plan (which would have failed its
   own gate); Pine comment fix queued for next deployment; net-arming variant
   = future pre-registered ablation candidate.

### Context for next session
- PRIMARY: execute the VBT port Phases 0-3 in a VECTORBT-WORKSPACE session per
  the approved plan (calibrated facts are spec; governor arms on GROSS).
- Weekday-RTH L2 re-sample = the operative slippage point estimate.
- Pine comment correction bundles with the next Pine deployment (+ prefix
  regression); do not do it standalone.
- Chart resting state verified after every excursion this session (anchor
  ~+8.0-8.2%/4,310-4,312, tail drift only). Entity SCn1V9 survived throughout.

### Files created/modified
- NEW `analysis/l2_book_impact.py`, `analysis/funding_model.py` + 2 test files
  (suite 25/25); MOD `analysis/fee_rates_by_dex.py` (ruff E731).
- MOD `scripts/tv_bars.mjs` (persists exchange/minmov/pricescale/mintick).
- NEW `analysis/reference/`: 16 cross-venue dumps (tvb7_OKXMSTR_*, tvb7_BTC_*),
  tvb7_l2_xyzMSTR.json, tvb7_funding_xyzMSTR.json, tvb7_symbolinfo.json,
  tvb7_diag_gov2_{0125,100bp}.json.
- NEW `docs/VBT_BREADTH_PORT_PLAN.md` (approved design of record, spec corrected).
- MOD `docs/TVB2_control_AB_rerun.md` (TVB-7 sections: cross-venue pre-reg +
  results, cost realism, Codex synthesis + adjudication; MAE table corrected).
- MOD `docs/HANDOFF.md`, `docs/reviews/REVIEW_REQUEST.md` (TVB-6 flip +
  TVB-7 request), NEW `docs/reviews/tvb6-codex-audit.md` (verbatim, committed).

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb7-codex-audit.md.
> See docs/reviews/REVIEW_REQUEST.md (the pointer) and docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED (2026-07-04, Codex CLI) -- APPROVE-WITH-NITS; verbatim
  audit in `docs/reviews/tvb7-codex-audit.md`; critical synthesis to be written
  by TVB-8.
- Commits to review: `a4e1de8^..557e00d` on `main` (= `d9504ba's ancestors
  back through a4e1de8` plus the session-end commit; 5 commits, sanity-checked:
  `git diff --name-status` lists all 33 session files). RANGE-PIN RULE applied:
  the caret keeps `a4e1de8` (cross-venue verification) inside the reviewed diff.
- Scope / what changed: governor v2 cross-venue verification (16 paired OKX/BTC
  runs, pre-registered CV1-CV4, keep-verdict upgrade); VBT breadth-port design
  doc; cost realism (L2 impact sampler + funding model + datasheet section);
  Codex TVB-6 fold-in (MAE correction, tick-metadata evidence, gross-arming
  adjudication with diagnostic dumps).
- Focus areas (scrutinize these): (1) the gross-arming adjudication logic --
  is the 575-trade identical prefix at 1% fee DECISIVE for gross semantics, and
  is the qty-floor explanation of the divergence sound (tvb7_diag_gov2_*)?
  (2) CV pre-registration integrity -- were CV1-CV4 applied as written; is
  "cross-venue-verified but not universal-structural" honestly scoped?
  (3) l2_book_impact method -- impact vs mid as the s-band comparable; the
  TV-tick mapping under HL 5-sig-fig pricing; weekend-regime caveat adequacy;
  (4) funding_model join semantics (et,xt] and the notional~=equity 1x
  approximation; (5) the MAE-correction root-cause claim (pre-final bar export)
  -- plausible or overclaimed? Standing: request.security lookahead (none;
  no Pine changes this session), model fidelity, fee/turnover math.
- Reviewed by: Codex CLI, 2026-07-04
- Findings: 1 LOW -- stale "governor reads net closed-trade PnL" sentence at
  `docs/VBT_BREADTH_PORT_PLAN.md:20` conflicts with the corrected GROSS-arming
  calibrated-facts block in the same file (fix before the port starts). Second
  actionable = a reminder, not a new finding: keep the queued Pine comment
  correction (`pine/baseline_continuity.pine:212`) attached to the next
  Pine-touching deployment. All focus-area checks PASSED (gross-arming
  adjudication chain, CV pre-registration, L2 method, funding model, MAE
  framing, VBT calibrated facts) with reviewer recomputation matching ours.

---

## Session TVB-6: xyz backfill VERIFIED + adopted; venue gap decomposed; solvency + slippage gates; governor v1->v2 KEPT (COMPLETE)

**Date:** 2026-07-03
**Status:** COMPLETE -- every startup priority done plus the full governor arc.
Fable 5 solo session (verification, analysis, design-with-user, Pine build, ablation).

### Codex TVB-5 review -- critical synthesis (RETURNED, APPROVE-WITH-NITS, 2 LOW)
Both findings AGREED and actioned same-session: (1) tv_dump ordering assumption ->
fail-loud assertions (list length == closed+open, entry-time ordering) + raw exit
timestamp (`xt`) preserved per row; verified passing on every live dump. (2)
"universal damage containment" -> sample-scoped wording used in all new datasheet
sections and this synthesis. The audit's independent re-derivations (venue-gap
arithmetic, S8 ~0.00225%/trade, pre-registration integrity) all matched our record;
nothing disputed.

### What was accomplished
1. **xyz TV backfill VERIFIED = genuine HL venue data** (priority 1, the gate).
   HL candles pulled for `xyz:MSTR` (API floors: 15m 2026-05-12, 1h 2025-12-07
   capped at ~5000; 4h/1d UNCAPPED from the 2025-12-02 listing = TV backfill start).
   Bar-by-bar: 97-99% float-exact OHLCV INCLUDING VOLUME at 15m/60m/1D; Dec2-Dec7
   hole closed via 4h aggregation (29/30 exact, 30/30 volume); pre-May 15m pinned by
   exact internal 15m->60m aggregation (5102/5103). Residuals characterized (wick
   scrub pattern TV-more-extreme, one missing traded bar Jun-28 reconciling to the
   decimal, placeholder asymmetry). Evidence TIME-PERISHABLE -> 7 raw files committed
   (`tvb6_{tv,hl}_xyzMSTR_*.json`); reproduce via
   `uv run python analysis/verify_xyz_backfill.py` (NEW, +4 tests).
2. **Venue gap DECOMPOSED -- the TVB-5 surprise is ~half modeling artifact.**
   Mechanism peek: venues near-identical (close corr 0.9923; cum close path -18.00
   vs -18.09) -> the 89pp ctrlB gap needs only ~2.5bp/trade. Then the tick-size
   discovery: OKX mintick 0.01 vs xyz 0.001 -- the "slippage = 1 tick/fill"
   convention charged OKX ~10x more per fill. Equal-$ comparison (xyz s10): closes
   ~49% of the R1E1 gap (+83.07 -> +61.78 vs OKX +39.88) and ~61% of ctrlB's.
   Remaining gap = real venue texture; knife-edge conclusion REINFORCED (churn-config
   sign = venue-texture noise). NEW xyz CONVENTION: report s1 AND s10, never s1 alone.
3. **xyz MSTRUSDC.P ADOPTED as primary MSTR chart** (DECIDED with user; target venue
   + deeper 15m history; OKX = standing sign check). Re-stage regression GREEN
   (ctrlB/R1E1 reproduce TVB-5 WV within tail drift); NEW xyz-native 60m rows:
   ctrlA 474tr +65.62 @0 / +47.10 @0.0125; R1E3 408tr +61.92 / +46.21. Slices:
   modest same-sign venue lift on slow cells; **kill-regime is TURNOVER-DEPENDENT**
   (Dec-Feb: ctrlA +2.12 / R1E3 +4.63 NET through the window that took ctrlB to
   -40.09 and R1E1 to -12.61) -- refines TVB-5 SP6.
4. **Short-leg MAE / 1x-cash solvency CLEARED** (Codex TVB-3 finding 2; skill
   position-sizing-risk invoked). HL margin model (maxLev 10 -> mm 5%): 1x short liq
   at +90.5%; worst observed short MAE across 3,225 shorts = 8.11%; zero breaches
   even at the 5x threshold; max survivable short lev at sample-worst ~7.4x (long
   ~9.8x). TV margin-0/0 = fair model of 1x cash. NEW `analysis/trade_mae.py`
   (+4 tests); tv_dump upgraded to TVB-6 trade format (ep/xp/ddp/rnp). Leverage
   discussion with user recorded: isolated leverage = knock-out option; below
   clearance it is risk-REDUCING vs 1x-all-in cross; above clearance the backtest no
   longer describes the strategy. All %s in the record are 1x.
5. **Slippage sensitivity band** {1,10,25,50} ticks pre-registered (SB1-SB4) then
   run: ctrlB +7.94/-37.56/-74.92/-94.52; R1E1 +59.96/+34.76/+1.29/-37.07; ctrlA
   +47.10/.../+4.79; R1E3 +46.21/.../+9.19. SB2 refuted on magnitude (100%-equity
   compounding amplifies linear cost); 60m cells positive even at 50t.
6. **Re-entry governor (charter S8) -- designed WITH user, v1 -> v2, KEPT.**
   Zero-parameter LEVEL RATCHET (losing exit -> same-direction re-entry only beyond
   the failed trigger). v1 reset (winning exit OR completed opposite trade) exposed
   **reset starvation under stand_aside** (opposite fills blocked -> one failed long
   ratchets out a whole regime episode; R1E1 1302->488 trades, gross +121->+27) --
   the two-layer baseline caught what the single-layer control hid. v2 reset =
   continuity event (exec-gate FULL OPPOSITE alignment), fresh pre-registration
   (V1-V4), re-run: R1E1+gov2 **+71.80 @0.0125 s1 / +45.71 s10** vs ungoverned
   +59.96/+34.76, higher gross (+134.8 vs +121.5 @0), better PF/DD; R1E3 inert
   (+0.84pp). **Pre-registered keep-rule MET -> v2 ratchet KEPT for the two-layer
   baseline** (input default stays off = regression anchor). Both regressions
   byte-identical (4,308-trade prefix match) at pineVersion 19 and 20.
7. **Underwater reality check (user flag, quantified):** ctrlB @0.0125 spent 204/213
   days below HWM (recrossed Jul-1 -- the +8% headline IS the final surge); R1E1
   149d; R1E1+gov2 124d; slow cells ~70d. Standing caveat in the datasheet: the
   underwater profile, not the endpoint, is the honest risk picture; everything
   remains one instrument, one 7-month path.
8. **Tooling/ops:** NEW `scripts/tv_bars.mjs` (CDP OHLCV export). tv_dump TVB-6
   format + assertions. Codex nit 1 done; nit 2 wording applied throughout. Jackson
   MCP Monaco finder FIXED (`27757bc` in tradingview-mcp-jackson): TV 2026-07 ships a
   fiber-less DECOY `.monaco-editor.pine-editor-monaco` node that dead-ended the
   first-match finder; multi-candidate fiber walk now; MCP picks it up on restart
   (this session used a direct-CDP bridge; the header "Add to chart" text button is
   gone -- use the circular-arrows update icon).

### Context for next session
- TVB-7 job 1 = governor v2 cross-instrument re-verification (OKX MSTR + BTC
  spot-check): is the lift structural or xyz-path-local? Keep-verdict is provisional.
- USER DIRECTION: port to VectorBT Pro as a BREADTH engine (many symbols, longer
  history, incl. regular equities as a DIFFERENT regime family). TV = fidelity
  anchor. HARD GATE: VBT must reproduce TV xyz cells trade-for-trade on the committed
  venue-verified bars before any VBT number enters the record. Plan mode for the
  design. See memory `project-vbt-breadth-engine`.
- Cost realism still open: venue-absolute slippage (live L2 sampling) + perp funding.
- NO deployability language anywhere: regime-local edge + containment + governor,
  single-sample; the system is one layer of a larger picture (HIP-3 screener attach
  path -- memory `project-one-layer-screener-attach`).

### Files created/modified
- NEW `analysis/verify_xyz_backfill.py`, `analysis/trade_mae.py` + tests (suite 17/17).
- NEW `scripts/tv_bars.mjs`; MOD `scripts/tv_dump.mjs` (TVB-6 format + assertions).
- MOD `pine/baseline_continuity.pine` (governor v2; slot pineVersion 20.0; id map +1
  shift: in_25 gov_mode, in_33 comm, in_34 slip, in_35/36 margins, in_42 magnifier).
- NEW `analysis/reference/`: 7 backfill-evidence files (tvb6_{tv,hl}_*), 6 xyz-native
  dumps (tvb6_WV_*), 12 slippage-band dumps (*_s{10,25,50}), 14 governor dumps
  (*gov_*, *gov2_*).
- MOD `docs/TVB2_control_AB_rerun.md` (six TVB-6 sections -- the session's core record).
- MOD `docs/HANDOFF.md`, `docs/reviews/REVIEW_REQUEST.md`, `.session_startup_prompt.md`.
- Sibling repo tradingview-mcp-jackson: `27757bc` (Monaco finder fix; local only).

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range below)
> and write a verbatim assessment to docs/reviews/tvb6-codex-audit.md. See
> docs/reviews/REVIEW_REQUEST.md (the pointer) and docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED (2026-07-04, APPROVE-WITH-NITS, 3 LOW -- synthesis in
  the TVB-7 sections of docs/TVB2_control_AB_rerun.md and the TVB-7 HANDOFF entry)
- Commits to review: `43fb973^..9a00d40` on `main` (= `1f7815f..9a00d40`;
  sanity-checked: `git diff --name-status` lists all 51 session files). RANGE-PIN
  RULE applied: the caret keeps `43fb973` (the review-return flip) inside the
  reviewed diff. Sibling repo tradingview-mcp-jackson `27757bc` at
  `C:\Strat_Trading_Bot\tradingview-mcp-jackson` -- local transport only.
- Scope / what changed: xyz backfill verification vs HL venue candles (+evidence);
  venue-gap decomposition (tick-size artifact); xyz adoption + native rows; MAE/
  solvency gate; slippage band; re-entry governor v1->v2 (Pine) + ablations; tv_dump
  assertions; Monaco finder fix.
- Focus areas (scrutinize these): (1) verify_xyz_backfill method -- is 97-99%
  float-exact + aggregation closure SUFFICIENT for "genuine venue data", and is the
  pre-May-12 15m residual honestly bounded? (2) the tick-size decomposition -- is
  "xyz s10 == OKX s1 in $/fill" a sound equalizer, and is "half artifact / half
  texture" over-claimed? (3) trade_mae.py -- MAE-vs-entry off bar extremes
  (conservative on the entry bar?), HL liquidation model (mm = 1/(2*maxLev)),
  max-survivable-leverage inverse; (4) the governor Pine -- trigger capture
  (high[1]+tick on the fill bar), same-bar ordering of loss-detection vs alignment
  reset, closedtrades.profit semantics (net of fees?), any repaint path; (5) the
  v1->v2 amendment epistemics -- mechanism-driven fix or post-hoc tuning? was the
  keep-rule applied as pre-registered? (6) byte-identity regressions as evidence
  (prefix match method). Standing: request.security lookahead (still none -- local
  ta.valuewhen only), model fidelity, fee/turnover math.
- Reviewed by: Codex CLI (docs/reviews/tvb6-codex-audit.md)
- Findings: 3 LOW, all AGREED + actioned in TVB-7: (1) 60m MAE table understated
  the committed replay (8.42%/7.22x, long 5.54%) -- corrected; (2) tick metadata
  not committed -- tv_bars.mjs now persists it + tvb7_symbolinfo.json committed;
  (3) governor profit-boundary diagnostic requested -- adjudicated WITHOUT a Pine
  change: strategy.closedtrades.profit() is GROSS of commission in this TV build
  (575-trade identical prefix at 1% fee is impossible under net-arming), so the
  "net of fees" mechanism description was wrong while every governed RESULT
  (as-deployed behavior) stands; VBT port spec corrected accordingly.

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
