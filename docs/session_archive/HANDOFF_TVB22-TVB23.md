# HANDOFF archive -- sessions TVB-22 through TVB-23

> Archived 2026-08-28 from docs/HANDOFF.md (TVB-30 session-end; file exceeded
> 1500 lines). Entries verbatim, newest first. Earlier archives:
> HANDOFF_TVB0-TVB9.md, HANDOFF_TVB10-TVB17.md, HANDOFF_TVB18-TVB21.md.

---

## Session TVB-23: TVB-22 audit folded + T1-floor round designed, prereg'd, built, run, reported (COMPLETE)

**Date:** 2026-08-10/12
**Status:** COMPLETE -- audit fold-in (gate hardened fail-closed, census
receipt-backed), TV header sync, design session (7 user rulings), prereg
BEFORE code with three dated corrections, engine + runner + full 13-arm
run with every gate PASS, censuses, report. One plan step remains open:
the TV mirror + re-gate of the new arms.

### What was accomplished

- TVB-22 AUDIT FOLDED (0023852; RETURNED NEEDS-CHANGES, all three findings
  reproduced BEFORE adjudication): F1 MEDIUM missing/NaN twin trig
  NaN-compared into a silent pattern-layer PASS -- reproduced on committed
  GOOGL/A1 (79 events/40 checked; +inf already failed, missing/NaN were
  the silent paths); pkg_parity now fail-closed at validation AND
  comparison; 12 regression tests (tests/test_pkg_parity.py) incl. the
  committed pin + the audit's delete-one-trig case; all 9 cells
  re-verified PASS in memory; committed artifact NOT regenerated (TVB-20
  precedent). F2 LOW: analysis/paper/ladder_census.py + committed receipt
  reproduces the audit's readings EXACTLY (137 closed, reach: 65.0% >=2,
  37.2% >=4, 39.4% stall; bf 3.41/3.62; with-open n=146 matches too);
  seed corrected (70/40/43 were unpinned mixtures); bimodality survives.
  F3 LOW: pine header names the passed artifact; range count 14 -> 13.
- TV HEADER SYNC: TradingView relaunched with CDP (MSIX Start-Process
  recipe); editor binding verified (TV source byte-equal to pre-edit
  committed base after decode fix -- cp1252 artifact, not real drift);
  full source injected via pine_set_source, byte-verified, compiled
  clean, saved. Local and TV copies identical again.
- DESIGN SESSION (plan mode; strat-methodology loaded; 7 user rulings
  2026-08-10): fixed 0.25% floor (10x worst round-trip taker); depth
  N=1..5 + infinity endpoint (labeled ceiling-map, floor on, no N
  promoted); fallback shallower; Wilder ATR(14) 1H vetoes at 1x/2x with
  fixed comparators; retracement census rides read-only; 1H only;
  per-setup census as declared report reading.
- PREREG BEFORE CODE (58f08d7) + three dated corrections, all before
  results were read: (a) the M+T pine's POTENTIAL-3 comment overstates
  its code -- one-sided flags mean an outside bar whose with-side broke
  first never labels (pine-exact = the code; fixture pins it, 2fcd13b);
  (b) counter reconciliation by equation so new counters stay zero-valued
  on determinism arms; (c) the "identical entry book across depth" gloss
  was WRONG -- caught by the run-time gate on the first full run:
  one-position occupancy funnels entries 137 -> 50 as exits deepen; gate
  corrected to first-divergence-is-exit; the fallback ruling itself
  unaffected. Also declared: DINF/A1F split (the seed's infinity endpoint
  carried two jobs with contradictory veto requirements); empty-ladder =
  uniform structural skip across all floor arms.
- ENGINE (8c5c126, inert defaults): t1_floor_pct entry veto (directional
  fill->T1 distance, strict d < floor, le0/small/only counter split,
  before the extended no-target skip); _Atr Wilder on completed 1H bars
  driving price-unit bf_prox_veto_atr/chop_veto_atr (pct arithmetic
  untouched); read-only retracement layer (health_flags + first-label
  stamps on bar-start position; entry bar excluded, exit bar included;
  stamps ride exit events only under the flag -- golden shape unchanged).
  20 fixtures (tests/test_t1floor_engine.py).
- RUNNER + RUN (8967a07): analysis/paper/tier_b_t1floor.py (tier_b.py
  untouched; determinism arms replay through tier_b._replay_arm itself).
  Gates ALL PASS: 55 determinism rows field-equal (modulo zero-valued new
  keys), entry-stream first-divergence-is-exit, counter reconciliation,
  census determinism per arm. Census tooling analysis/paper/round_census.py
  (roster scope). 88 rows, 8 rollups, 8 event dumps, 8 receipts, manifest
  with dirty PATH LIST.
- FINDINGS (docs/experiments/tvb23_t1floor_report.md; one gross in-sample
  window, no promotion): floor repairs the package (D1 +83.8 vs A2 +24.6)
  but A0b +104.8 still leads -- C2F does NOT earn its place over C1; risk
  shape transforms (maxDD 22.1 vs 122.2, zero open drag, avg MAE 1.47 vs
  2.63); ~40% of ALL candidates arrive at/past their own frozen T1
  (born-beyond real at candidate scale); A1F flips A1 -7.7 -> +23.0 while
  halving the book (S3.1 reinforced: still -81.8pp under A0b); depth
  curve non-monotone shallow-top 83.8/38.5/51.3/60.0/65.4/19.4, MAE tail
  erodes by D3 as predicted; ATR vetoes DISSOLVE the chop symbol filter
  (spread 43-100% -> 58-80%, three shut-outs unlocked; P&L -15.1pp stated
  not adjudicated); retracement census supports the user prior -- first
  POTENTIAL-3 label before 0.02-1.3 rungs of progress, 100% of losers AND
  48-96% of winners labeled (an exit would cut winners early); 98-99% win
  rates flagged as exit-construction artifacts.
- USER CLARIFICATIONS (2026-08-12): entry timing = intrabar of the 1H
  (developing-bar break, 5m-quantized, color-gated as-built; never waits
  for 1H close; Strategy Tester's close-paint is accounting only);
  3-1-2U walk-through incl. the flagged GAP: the canonical intrabar-3
  invalidation exit (entry bar goes 3 against you -> exit at market) is
  ABSENT from the implemented exit set, and the retracement label cannot
  see that case (with-side broke first by construction); 5m mount is the
  parity-covered instrument, a 1H mount is a different uncovered variant.
  Validation-maturity assessment delivered: verification ~90%, design
  ~75% (exits open), evidence ~25% (everything one in-sample window).

### Context for next session

- THE ONE OPEN PLAN STEP: prereg step 7 -- mirror floor/ATR/arm-selector
  into pine/tfc_mt_package_strategy.pine (semantics verbatim; comma-free
  option labels; verify editor binding before save) and re-gate
  GOOGL/TSLA/DRAM x {D1, DINF, D1ATR} via tvb22_pkg_harvest.mjs +
  hardened pkg_parity.py. Until PASS the mounted TV strategy is valid
  ONLY for the TVB-22 arms (declared in the prereg).
- Next research fork per user: exit-design lane (bimodal ladder unsolved;
  census evidence in place; plan mode ON) vs fresh-window replication
  (the biggest evidence gap). The user's stated arc: exits matter most.
- Workbench end state: TV Desktop RUNNING with CDP 9222 (relaunched this
  session), TVB18-parity layout, DRAM 5m chart, package strategy mounted
  (arm A1) + CONTROL + v6.1 watch indicator; Pine editor bound to the
  PACKAGE script; TV-side source byte-identical to committed HEAD.

### Files created/modified

- New: analysis/paper/ladder_census.py + tier_b/ladder_census_receipt.json,
  analysis/paper/tier_b_t1floor.py, analysis/paper/round_census.py,
  analysis/paper/tier_b_t1floor/ (rows, rollups, manifest, 8 event dumps,
  8 census receipts), tests/test_pkg_parity.py, tests/test_ladder_census.py,
  tests/test_t1floor_engine.py, docs/experiments/tvb23_t1floor_prereg.md,
  docs/experiments/tvb23_t1floor_report.md, docs/reviews/tvb22-codex-audit.md.
- Modified: analysis/paper/pkg_parity.py (fail-closed pattern layer),
  analysis/paper/engine.py (floor/ATR/retracement, inert defaults),
  analysis/paper/patterns.py (health_flags, read-only),
  pine/tfc_mt_package_strategy.pine (header parity block; TV synced),
  docs/experiments/tvb22_next_variant_seed.md (census figures corrected),
  HANDOFF + REVIEW_REQUEST flips, .session_startup_prompt.md.
- Suite: 181 passed, 2 skipped; ruff clean.

### Open

- [ ] TV mirror + re-gate of the new arms (prereg step 7): floor + ATR +
      arm selector into the package pine, then 9-cell parity gate; TV
      strategy stays on TVB-22 arms until PASS
- [ ] Exit-design lane (reserved; bimodal ladder unsolved; retracement
      census evidence now in place; canonical intrabar-3 invalidation
      exit absent -- future pre-registered variant if wanted)
- [ ] Fresh-window replication round (own prereg; biggest evidence gap)
- [ ] Greenlit repairs bundle (TVB-18, carried): F2 roster receipts +
      fail-closed, F3 5m-lifecycle warm-up regression, F4 eviction
      telemetry split, freeze-boundary invariant, SKHX tv_symbol/mintick
      backfill
- [ ] Nudge the M+T collaborator: PMG+ prefix structurally unreachable
      (carried from TVB-21)
- [ ] jackson MCP indicator_set_inputs kills Pine user scripts (carried;
      fix in tradingview-mcp-jackson)
- [ ] tvb8/tvb9 external reviews still unreturned (standing)

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb23-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED -- audit at docs/reviews/tvb23-codex-audit.md
  (captured 2026-08-12, verdict NEEDS-CHANGES: 3 MEDIUM + 2 LOW; reviewer
  independently replayed all 13 arms and every committed artifact
  reproduced). Critical synthesis pending TVB-24 fold-in.
- Commits to review: `0023852^..9099bad` on `main` (6 commits; RANGE-PIN
  RULE: the caret keeps 0023852 in the diff; sanity-checked -- `git diff
  --name-status 0023852^..9099bad` lists all 37 files the session
  touched).
- Scope / what changed: TVB-22 audit fold-in (pkg_parity fail-closed +
  tests, ladder-census receipt, metadata fixes); T1-floor round (prereg
  BEFORE code + 3 dated corrections, engine floor/ATR/retracement behind
  inert defaults, runner with determinism/entry-stream/reconciliation
  gates, full 13-arm run, per-arm census receipts, report).
- Focus areas (scrutinize these): (1) F1 fix: validate_events +
  comparison fail-closed paths, the committed parity artifact NOT
  regenerated, the 12 regression tests; (2) receipt integrity: does
  ladder_census reproduce its committed numbers, do the round_census
  conventions match the prereg (entry bar excluded, label bar exclusive,
  roster scope), determinism guards fail-closed; (3) floor veto semantics
  vs the prereg + amendments: strict d < floor, empty-ladder uniform
  skip, DINF/A1F split justification, counter equation; (4) ATR: Wilder
  seed/step math, price-unit predicates, pct-path arithmetic untouched
  (determinism), first-bar TR = h-l convention declared; (5) retracement
  layer truly read-only (no decision path reads it; golden event shape
  unchanged when off) + the as-built one-sided-flag edge fixture vs the
  pine source; (6) runner gates: determinism modulo-zero-new-keys rule,
  entry-stream first-divergence-is-exit logic, occupancy funnel numbers;
  (7) report language discipline (no promotion, constructed win rates
  flagged, contrasts only); (8) request.security: no executable Pine
  change except the package header comment block (TV-synced, byte-equal).
- Reviewed by: OpenAI Codex (GPT-5), captured 2026-08-12; folded by TVB-24
  2026-08-15 with every finding REPRODUCED before adjudication.
- CRITICAL SYNTHESIS (TVB-24, 2026-08-15): verdict NEEDS-CHANGES accepted.
  The strongest part of the audit is its confirmation surface: it
  independently replayed all 5 determinism arms and all 8 new arms and
  every committed row, rollup, event dump, bar hash, and the occupancy
  funnel reproduced exactly -- the findings attack evidence contracts,
  not this round's numbers.
  - F1 (guards fail-open) AGREED, all three false-PASS paths reproduced
    exactly (empty replay, deleted produced field, prefix-vs-entry
    stream, census 85->82 open_mark deletion). Fixed: _determinism_check
    union-of-fields + row cardinality both directions; entry-stream gate
    all 15 depth pairs + equal symbol sets + prefix-next-must-be-exit;
    census guard now checks open count/direction + event linkage.
    17 adversarial regression tests (tests/test_t1floor_gates.py);
    committed artifacts re-verified PASS in memory under the hardened
    gates; committed artifacts NOT regenerated (TVB-20 precedent).
  - F2 (missing prereg-bound diagnostics; retracement prose outruns the
    census) AGREED. Delivered post-hoc via
    analysis/paper/t1floor_diagnostics.py: atr_context_receipt.json
    (mean 1H ATR% of price spans 0.26% GOLD -> 1.98% SKHY, a 7.6x roster
    spread -- the fixed-2% chop band was ~8x GOLD's hourly range, which
    IS the accidental symbol filter, now receipt-grounded) and
    matched_exit_receipt.json (NEW mechanism reading: on the 37 trades
    closed in ALL six depth arms, realized P&L rises strictly with depth
    38.4 -> 66.2pp D1->D5, so the whole-arm shallow-top is an
    occupancy/open-drag effect, not a per-trade exit effect; boundary:
    subset excludes deep-arm open runners by construction). Report
    finding 5 narrowed by dated correction: label-bar-exclusive census
    cannot order rung-vs-label intrabar or price an alternative exit; the
    counterfactual needs a pre-registered exit variant.
  - F3 (correction provenance) AGREED with one argued nuance: the
    occupancy correction is run-time-gate-TRIGGERED, so it cannot precede
    the run by construction -- the honest claim is pre-RESULTS-read,
    which is self-attested. Prereg now carries a dated provenance-status
    note (only 2fcd13b git-verifiable; other two self-attested); the
    runner records prereg_blob_sha256 in the manifest for future runs;
    forward protocol: commit gate-triggered corrections before the clean
    rerun.
  - F4/F5 (stale contract text; realized-P&L monotonicity) AGREED, fixed
    by dated corrections (prereg heading 9->8, superseded entry-book
    language bracketed, runner docstring reconciled; report now states
    the D2 dip 83.8 -> 82.0 -> 89.8 -> 98.5 -> 104.0).
  - DISPUTED: nothing material. Watch item: the audit's "suggested
    prompt" mutations are all now encoded as regression tests.

---

## Session TVB-22: TV package strategy + parity gate 9/9 + audit fold-in with ruled rerun (COMPLETE)

**Date:** 2026-08-09/10
**Status:** COMPLETE -- the user-requested TV package strategy() built and
parity-gated PASS on all nine cells; the TVB-21 Codex audit returned
mid-session, its HIGH finding reproduced to the decimal, semantics ruled by
the user, engine fixed, Tier B rerun regenerated; mechanism decomposition +
next-variant seed written for the T1-floor design session.

### What was accomplished

- TV PACKAGE STRATEGY (056f47b): pine/tfc_mt_package_strategy.pine -- the
  Tier B pattern arms (A1/A2/A3 via one Arm selector) as a strategy();
  M+T detection/ladder layers inserted verbatim (renames + hunks H1-H7
  documented in header) into the control pool/gate/position machinery;
  f_pool gained a pure-read BAR-OPEN alive-set veto scan; entry comments
  carry pattern zipcode + trig for the parity join. Created on TV via the
  Make-a-copy flow (new id USER;b0e937c5...; CONTROL + M+T stamps verified
  unchanged), compiled clean, round-trip byte-identical.
- TVB-21 AUDIT FOLDED (a70339b; returned mid-session, NEEDS-CHANGES): all
  four findings independently reproduced BEFORE adjudication -- F1 HIGH to
  the decimal (A2 208/410 target exits outside their exit bar; born-beyond
  split 188/-278.3pp vs 55/-29.0pp; containment sensitivity +24.6/+31.0pp).
  Package verdict/churn magnitude/tail metrics invalidated; report carries
  a dated notice (original preserved); statuses flipped RETURNED; synthesis
  in the TVB-21 block below.
- USER RULINGS (3, 2026-08-09): containment-touch targets (C1 bf-touch
  convention, gap-past edge included); no-target skip retained with vetoes
  evaluated first (+ no_target_vetoed overlap counter); parity gate only
  after the fix. Prereg amendment committed BEFORE code (2865e5a).
- FIX + RERUN (b54b07b, 40d6e7f, d2418dd): engine containment predicates +
  4 fixtures (born-beyond long/short, favorable gap-past, counter
  reconciliation); manifests source-bound (executed blob hashes + dirty
  state). Full rerun regenerated tier_b/ IN PLACE: A2 -222.0 -> +24.6pp,
  A3 -127.5 -> +31.0pp -- still 80.2/73.8 under A0b (C2 does not earn its
  place over C1); trades 413->186/263->157 (churn loop dissolves under
  containment); 3-2 census REVERSES to +43.4pp/52% (was impossible-fill
  artifact); MAE-tail collapse survives and strengthens. Fix-isolation
  invariants verified (A0a/A0b/A1 rows identical modulo the zero counter
  key; A0 determinism PASS). Report: docs/experiments/tvb22_tier_b_rerun_report.md.
- PINE MIRROR (b990d22): same two semantic hunks applied to the TV
  strategy; recompiled; round-trip identical.
- PARITY GATE PASS 9/9 (870b45d, 9b48a78, 87ca603): GOOGL/TSLA/DRAM x
  A1/A2/A3 vs the twin over TV-harvested feeds, shared cold start,
  pine_gate_warmup: 487 events matched, ZERO mismatches, offset 0s,
  break/flip float-exact, and the NEW pattern layer (name + trig within
  tick/2 on all 246 entries) clean -- the drift-detection payload works.
- THREE TV TRAPS FOUND: (1) setInputValues with the full getInputValues
  array corrupts any Pine user script ("Can't parse pine" sticky kill,
  even value-unchanged -- the array echoes text/pineId/pineVersion/
  pineFeatures; jackson's indicator_set_inputs idiom is broken on this
  build; partial arrays work; memory tv-mcp-setinputs-trap). (2) The M+T
  every-bar PMG/ladder walks blow the strategy execution budget on deep 5m
  charts -- now lazy behind decision-identical guards (H7). (3) Comma in a
  string-input option value adopted as defensively-removed while bisecting.
- MECHANISM DECOMPOSITION (post-hoc reads on the rerun, no artifacts
  modified): package losses ~= the born-beyond class (A2: 75 trades
  -21.3pp, 3% win); hollow wins = the tiny-target class (53 trades +4.4pp,
  100% win, ~0.08% each; 17/53 compressed by late fills) -- both killed by
  the user's own T1-floor rule. A1 ladder census BIMODAL: 43% stall at 1-2
  rungs, 40% run 4+; harvest exits fire after ~3.6 rungs avg. Twin trade
  tables for all 9 parity cells committed
  (analysis/reference/pkg_parity/tvb22_twin_trades.md, 46298d6).
- NEXT-VARIANT SEED (2162780): docs/experiments/tvb22_next_variant_seed.md
  -- T1-floor arm(s), depth sweep N=1..5 as labeled ceiling-map (floor
  on), ATR-scaled vetoes, retracement census as read-only diagnostic
  (pine's own status rules, ported with fixtures); six open rulings
  listed. User prior on record: a retracement-label EXIT would likely hurt
  by exiting early -- census first.

### Context for next session

- The user reviews the seed doc between sessions; next session opens with
  the T1-floor round DESIGN SESSION (plan mode; rulings -> prereg -> code).
  User direction at close: push to limits -- deeper targets, potentially
  other timeframes. Depth = labeled ceiling-map, floor on, no N promoted;
  timeframe changes need structural grounds (15m/30m signal-TF arms are
  named deferred in the Tier B prereg), never sample-picked.
- Any engine change mirrors into pine/tfc_mt_package_strategy.pine and
  RE-GATES before the user runs it live.
- Workbench end state: TVB18-parity layout, DRAM 5m chart; package
  strategy mounted (arm A1, healthy) + CONTROL remounted + v6.1 watch
  indicator; Pine editor bound to the PACKAGE script; TV Desktop running
  with CDP 9222. FLAG: while diagnosing the input-kill I broke the mounted
  CONTROL instance with an unchanged-value round-trip; it was restored as
  a FRESH mount with default settings (the tester recomputes; no
  accumulated strategy state was load-bearing, but it is a new instance).

### Files created/modified

- New: pine/tfc_mt_package_strategy.pine, analysis/paper/pkg_parity.py,
  scripts/tvb22_pkg_harvest.mjs, analysis/reference/pkg_parity/ (9 trade
  dumps + result + twin trade tables),
  docs/experiments/tvb22_tier_b_rerun_report.md,
  docs/experiments/tvb22_next_variant_seed.md,
  docs/reviews/tvb21-codex-audit.md (committed verbatim).
- Modified: analysis/paper/engine.py (containment + veto order +
  no_target_vetoed), analysis/paper/tier_b.py (source-bound manifest +
  rollup counter), tests/test_pattern_engine.py (+4),
  docs/experiments/tvb21_tier_b_prereg.md (dated amendment),
  docs/experiments/tvb21_tier_b_report.md (invalidation notice),
  analysis/paper/tier_b/ (regenerated in place), HANDOFF + REVIEW_REQUEST
  flips, .session_startup_prompt.md.
- Suite: 144 passed, 2 skipped; ruff clean.

### Open

- [ ] T1-floor round: design session (seed = agenda) -> prereg -> build ->
      run -> report; mirror + re-gate the TV strategy after any engine change
- [ ] Greenlit repairs bundle (TVB-18, carried): F2 roster receipts +
      fail-closed, F3 5m-lifecycle warm-up regression, F4 eviction telemetry
      split, freeze-boundary invariant, SKHX tv_symbol/mintick backfill
- [ ] Nudge the M+T collaborator: PMG+ prefix structurally unreachable
      (carried from TVB-21)
- [ ] jackson MCP indicator_set_inputs kills Pine user scripts (full-array
      setInputValues) -- fix in tradingview-mcp-jackson (new this session)
- [ ] BF-harvest-replacement exit ruling revisit after visualization
      (carried; retracement census is the measurement path)
- [ ] tvb8/tvb9 external reviews still unreturned (standing)

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb22-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED (2026-08-10) -- NEEDS-CHANGES; all three findings
  reproduced and ADDRESSED same day (synthesis below).
- Commits to review: `056f47b^..a2ede4e` on `main` (13 commits -- the "14"
  originally recorded here was a miscount, audit F3, `git rev-list --count`
  = 13 and the SHA list was already complete; RANGE-PIN RULE: the caret
  keeps 056f47b in the diff; sanity-checked -- `git diff --name-status
  056f47b^..a2ede4e` lists all 28 files the session touched).
- Scope / what changed: TV package strategy() port + its parity harness/
  gate (9/9 PASS); TVB-21 audit fold-in (F1 reproduced, prereg amendment,
  engine containment fix, full Tier B rerun regenerated in place);
  mechanism decomposition docs + next-variant seed.
- Focus areas (scrutinize these): (1) fold-in fidelity vs
  docs/reviews/tvb21-codex-audit.md (F1 reproduction, amendment wording vs
  the three user rulings, report invalidation notice); (2) the containment
  fix (l <= tgt <= h both sides, gap-past edge) + the four new fixtures --
  do they pin the failure classes; (3) rerun integrity: fix-isolation
  invariants (A0a/A0b/A1 rows unchanged modulo the zero-valued
  no_target_vetoed key), A0 determinism vs committed Tier A cells,
  in-place regeneration provenance (manifest executed-blob hashes,
  git_dirty=true explained as output-only); (4) the Pine merge:
  declared hunks H1-H7 vs verbatim sources, especially H7's
  "decision-identical" claim (lazy PMG/ladder guards) and the f_pool
  veto scan's bar-open-alive-set equivalence to engine._alive_harvest_vals;
  (5) pkg_parity.py gate soundness: injective join, fail-closed
  validation, tgt in the residual layer, the pattern layer's name/trig
  checks, cold-start twin alignment to first_bar_ts; (6) no promotion
  language in the rerun report / seed / trade tables; (7)
  request.security: the new pine has NONE -- confirm across the range.
- Reviewed by: OpenAI Codex (GPT-5), verdict NEEDS-CHANGES
  (docs/reviews/tvb22-codex-audit.md, verbatim).
- CRITICAL SYNTHESIS (folded 2026-08-10, next session; all findings
  reproduced BEFORE adjudication):
  - F1 MEDIUM (missing/NaN twin trig false-passes the pattern layer):
    CONFIRMED -- reproduced pre-fix on the committed GOOGL/A1 cell exactly
    as the audit describes (delete-trig and NaN both false-PASSed at 79
    events / 40 checked / zero violations). One refinement: +inf already
    FAILED via the comparison; the silent paths were missing and NaN
    specifically. FIXED fail-closed at two layers (pkg_parity.py):
    validate_events now requires a non-empty pattern name and a finite
    numeric trig on every enter event on BOTH sides, and the trig
    comparison treats a non-finite twin value as a violation even if
    validation were bypassed. NEW tests/test_pkg_parity.py (12 tests):
    synthetic pattern-stream contract, all malformed-payload paths
    (missing/NaN/inf/string trig, missing/empty pattern), name-mismatch
    and half-tick-drift pins, the committed GOOGL/A1 pin (79/79/79, 40
    checked), and the audit's adversarial delete-one-committed-trig case.
    All nine committed cells re-verified PASS in memory under the hardened
    gate; the committed parity artifact was deliberately NOT regenerated
    (TVB-20 F1 precedent: committed artifacts are a pinned regression
    surface).
  - F2 LOW (ladder census had no pinned denominator/receipt): CONFIRMED --
    the committed rows carry only ladder_depth_at_entry; the seed's
    70/40/43 figures were unpinned post-hoc reads mixing denominators.
    BUILT analysis/paper/ladder_census.py (replays A1 via the tier_b
    warm/seed path, tier_b.py itself untouched -- its blob hash stays
    manifest-pinned) + committed receipt
    analysis/paper/tier_b/ladder_census_receipt.json with every convention
    declared (10-symbol scope, entry-bar excluded, reach AND containment
    touch both reported, zero-rung in denominator, per-trade rows) and a
    fail-closed determinism guard vs the committed A1 rows (PASS). The
    receipt reproduces the AUDIT's readings exactly (reach, 137 closed:
    65.0% >= 2, 37.2% >= 4, 39.4% stall 1-2; bf mean 3.41 / 3.62
    excl-zero) -- independent convergence on conventions. Seed corrected
    in place with receipt-backed figures; bimodality survives with
    corrected numbers (39% stall vs 37% run-4+). 5 unit tests pin the
    counting rules (tests/test_ladder_census.py). The census is now
    prereg-citable for the T1-floor round.
  - F3 LOW (stale parity metadata): CONFIRMED -- pine header updated to
    name the passed nine-cell artifact (487 events, 246 pattern checks)
    with the realtime-cadence caveat preserved and an explicit
    re-gate-on-any-semantic-change rule; comment-only change, zero
    semantic hunks (TV-side copy is one comment block behind until the
    next TV sync; decisions unchanged). Range count corrected 14 -> 13
    here and in REVIEW_REQUEST.md.
  - Audit confirmations worth keeping: rerun arithmetic + class splits
    independently reproduced; fix-isolation invariants verified; Pine
    H1-H7 statement-equality checked against both sources incl. H4
    veto-scan equivalence to engine._alive_harvest_vals and H7's
    guard-only claim; nine-cell parity regenerated in memory 487/487; no
    executable request.security in the range; no promotion language.
    Carried validation limits: parity is historical close-cadence
    decision-level evidence on three symbols; Tier B remains one ~4-week
    gross in-sample window; the manifest records a dirty boolean, not the
    dirty path list (accepted, noted for future manifests).

---
