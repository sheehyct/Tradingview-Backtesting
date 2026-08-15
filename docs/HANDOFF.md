# HANDOFF -- tradingview-backtesting

> Newest session entry at the TOP. Keep under 1500 lines; archive older entries to
> `docs/session_archive/` when it grows past that.

---

## Session TVB-24: both reviews folded + TV mirror parity-gated PASS (COMPLETE)

**Date:** 2026-08-15 (autonomous overnight; user in and out)
**Status:** COMPLETE -- TVB-23 Codex audit folded (every finding reproduced
before adjudication), the 2026-08-14 strategy-implementation assessment
folded (both diagnostics reproduced exactly), and prereg step 7 closed:
TV mirror built, saved, and 9-cell parity gate PASS. Three commits pushed.

### What was accomplished

- TVB-23 AUDIT FOLDED (674c7f6; NEEDS-CHANGES, 3 MEDIUM + 2 LOW, all
  reproduced BEFORE adjudication -- critical synthesis in the TVB-23
  entry's External Review block below): F1 guards hardened fail-closed
  (determinism union-of-fields + row cardinality both directions;
  entry-stream all 15 depth pairs + equal symbol sets +
  prefix-next-must-be-exit; census open count/direction + event linkage)
  with 17 adversarial regression tests (tests/test_t1floor_gates.py);
  committed artifacts re-verified PASS in memory, NOT regenerated. F2 the
  two prereg-bound diagnostics delivered post-hoc
  (analysis/paper/t1floor_diagnostics.py): atr_context_receipt.json
  (roster ATR% spread 0.26-1.98%, grounds the accidental-symbol-filter
  mechanism) + matched_exit_receipt.json (NEW mechanism reading: on the
  37 trades closed in ALL six depth arms realized P&L rises strictly with
  depth 38.4 -> 66.2pp, so the whole-arm shallow-top is an occupancy
  effect; survivor boundary declared); report finding 5 narrowed by dated
  correction (label-bar-exclusive census cannot support the exit
  counterfactual). F3 provenance downgraded to self-attested for the two
  same-commit corrections (dated prereg note); runner now records
  prereg_blob_sha256. F4/F5 dated text corrections (arm count 9 -> 8,
  superseded entry-book language, the realized-P&L D2 dip).
- ASSESSMENT FOLDED (33c7138): docs/strategy-implementation-assessment.md
  committed as source; BOTH its diagnostics reproduced exactly before
  adoption (D1 entry-vs-close 61/41 mean +0.0809pp sum +8.25pp; identity
  funnel 4111 evals -> 682 identities, 102 entries / 86 / 16 re-entered)
  and folded into committed tooling analysis/paper/entry_audit.py +
  entry_audit_receipt.json with pinned tests. NEW finding beyond the
  assessment: 11/765 committed entries (4 distinct events) booked level
  fills OUTSIDE the entry bar's range -- entry-side born-beyond analogue,
  but structurally PESSIMISTIC-direction (far side of the max/min fill
  rule) and immaterial (~0.7pp against the arms). Three-benchmark fill
  framing pinned (vs level/open = conservative-by-construction; vs
  decision close = favorable-majority; vs live intrabar = unresolved at
  5m). Constitution sync: CLAUDE.md + README no longer deny the Python
  engine exists (stale since TVB-21); engine comment disambiguates the
  gate-open-proximity veto from M+T's reversal-streak chop (P1-3).
  Adjudication delivered to the user in-session: adopt the
  research-integrity spine now, park the G0-G7 execution architecture
  until the live arc opens (tension with the loss-tolerable micro-canary
  philosophy surfaced, user's call).
- TV MIRROR + RE-GATE (b58688e; prereg step 7 CLOSED): floor/ATR/
  arm-selector into pine/tfc_mt_package_strategy.pine, semantics verbatim
  from engine.py (H8 header hunk; ATR update-order verified against
  replay_bar; comma-free labels; D1ATR tested before D1 in the startswith
  chain). Editor binding verified BEFORE save (byte-equal to committed
  base modulo the known cp1252 dump artifact); injection disk -> Monaco
  via node CDP with SHA-256 round-trip verification (70,537 chars
  byte-equal); compiled clean; saved (same script evolves, v10+). GATE
  PASS 9/9 (GOOGL/TSLA/DRAM x D1/DINF/D1ATR): 218/218 events matched,
  zero twin-only/tv-only, offset 0s every cell, break/flip float-exact,
  pattern layer clean on all 111 checked entries. The TV strategy is now
  parity-valid for ALL SIX arms. New tooling:
  scripts/tvb23_pkg_harvest.mjs (TVB_TARGET target pinning),
  pkg_parity.py --arms with generation-scoped artifacts (committed TVB-22
  pin never overwritten; gate twin's ATR seed-exact vs the pine).
- OPERATIONAL (memory tv-mcp-tvb24-ops): layout_switch false-success
  (create-new-layout UI flow works); Add-to-chart is icon-only, findable
  by title attribute; screenshots hang when the session is locked (drove
  the whole TV phase blind via DOM probes); worked in a NEW
  "TVB24-mirror" layout so the user's layouts/live tab were never driven.
- MORNING DESIGN SESSION (user present, plan mode; the research fork
  RESOLVED): the TVB-25 exit round designed and PRE-REGISTERED
  (docs/experiments/tvb25_exit_round_prereg.md, committed BEFORE any
  code). User rulings: all four exit candidates enter (thesis exits
  individual, overlays as with/without, one composite endpoint); C0 state
  stop = 2-against at 1H close; ladder bottom = TWO arms (S0a pure /
  S0b +flip) vs A0b; BOTH partial profiles (P1 two-piece 50@T1+runner;
  P2 the user's runner profile: skip T1, 40/20/20/10 at T2-T5, 10%
  runner to the BF touch, floor arms after the T2 bank, T1 retrace exits
  the middles, runner exits at breakeven, -0.25% variant named-deferred);
  risk overlay = per-setup STRUCTURAL stops (skill 5.2 table in the
  prereg) with ATR(14,1H)x3 default for controls/undefined anchors;
  intrabar-3 invalidation as an overlay contrast; fresh window = Aug 3 ->
  latest complete day now, extended through Aug 31 under the same prereg;
  headless first, TV mirror on demand per arm. Also logged to memory:
  the $50-or-less separate-wallet live canary + realism layer
  (sizing/dollar P&L/leverage/margin) as a named future lane; the user's
  vol/time-compression observation (instrument/regime-dependent minimal
  continuity, a-priori-only future variant).

### Context for next session

- Prereg step 7 CLOSED -- nothing blocks the research fork; it needs the
  USER's direction (exit-design [plan mode ON] vs fresh-window vs the
  assessment-motivated C0-current/C1-current isolated pair).
- The assessment's owner-level items stay parked: kernel-vs-Pine charter
  question, 1m/trade archiving start, spine CLAUDE.md project-map row
  (outside this repo, still says Pine-first).
- Workbench: TV Desktop on CDP 9222, TVB24-mirror layout, package
  strategy mounted (DRAM 5m, arm D1ATR), editor bound to the package
  script, TV source byte-equal to committed HEAD.

### Files created/modified

- New: analysis/paper/t1floor_diagnostics.py, analysis/paper/entry_audit.py,
  scripts/tvb23_pkg_harvest.mjs, tests/test_t1floor_gates.py,
  tests/test_t1floor_diagnostics.py, tests/test_entry_audit.py,
  docs/reviews/tvb23-codex-audit.md, docs/strategy-implementation-assessment.md,
  tier_b_t1floor/{atr_context,matched_exit,entry_audit}_receipt.json,
  analysis/reference/pkg_parity/tvb23_*_trades.json (9) + tvb23_parity_result.json.
- Modified: analysis/paper/tier_b_t1floor.py + round_census.py (fail-closed
  gates), analysis/paper/pkg_parity.py (TVB-23 arms), analysis/paper/engine.py
  (comment only), pine/tfc_mt_package_strategy.pine (H8 + gate-pass header;
  TV-synced sha-verified), docs/experiments/tvb23_t1floor_{prereg,report}.md
  (dated corrections), CLAUDE.md, README.md, HANDOFF + REVIEW_REQUEST flips,
  .session_startup_prompt.md.
- Suite: 205 passed, 2 skipped (24 new tests); ruff clean.

### Open

- [x] Research fork (user direction) -- CLOSED same session by the morning
      design session: all three lanes merged into ONE pre-registered round
      (docs/experiments/tvb25_exit_round_prereg.md); TVB-25 builds + runs it
- [ ] TVB-25 round: build + run per the committed prereg (engine tranche
      machinery, structural/ATR stops, state stop, intrabar-3, X1 arming;
      fresh-bar harvest FIRST; hardened gates); month-end window extension
- [ ] Assessment owner decisions: kernel-vs-Pine charter question; start
      1m/trade archiving for causal-fill work; spine CLAUDE.md
      project-map row stale (outside this repo)
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
> below) and write a verbatim assessment to docs/reviews/tvb24-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: REQUESTED
- Commits to review: `674c7f6^..130013e` on `main` (4 commits: 674c7f6
  audit fold; 33c7138 assessment fold; b58688e TV mirror + gate PASS;
  130013e session-end docs. RANGE-PIN RULE: the caret keeps 674c7f6 in
  the diff; sanity-checked with `git diff --name-status`).
- Scope / what changed: TVB-23 audit fold (fail-closed gate hardening +
  adversarial tests; prereg-bound diagnostics as receipts; dated
  corrections; provenance hashing); assessment fold (entry_audit receipts,
  constitution sync, chop-naming disambiguation); TV mirror of the TVB-23
  arms + 9-cell parity gate PASS (harvest variant, pkg_parity --arms).
- Focus areas (scrutinize these): (1) hardened gates genuinely fail-closed
  (union-of-fields, all-pairs, prefix rule, census open checks) and the
  adversarial tests actually bite; (2) t1floor_diagnostics + entry_audit
  receipts reproduce from committed artifacts (conventions honest,
  survivor-shape boundary on the matched-exit read); (3) pine H8 hunk
  semantics verbatim vs engine.py (floor order before no-target skip; ATR
  Wilder math + update order; pct/ATR mutual exclusion; arm derivation
  startswith chain D1ATR-before-D1); (4) parity gate extension (prefix
  routing, generation-scoped artifact never overwrites the TVB-22 pin;
  ATR seed-exactness claim for the gate twin); (5) dated corrections
  never silently rewrite (prereg/report); (6) request.security: no new
  calls; pine change is the H8 logic + header (TV-synced, sha-verified).
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb24-codex-audit.md exists)

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

## Session TVB-21: TVB-20 audit fold-in + design session + Tier B built and executed (COMPLETE)

**Date:** 2026-08-08/09
**Status:** COMPLETE -- all four TVB-20 audit findings reproduced-then-fixed,
THE design session held in plan mode (every variable user-ruled), Tier B
pre-registered BEFORE code, built, executed, and autopsied same session.

### What was accomplished

- TVB-20 AUDIT FOLD-IN (f90d0c9, all four findings reproduced before
  adjudication): F1 parity gate hardened (injective join, fail-closed
  stream validation, cardinality equality; false-pass reproduced on the
  committed GOOGL artifact pre-fix -- dup trade PASSed 91v89, direction 's'
  aliased to short; 8 regression tests incl. the committed-GOOGL 89/89/89
  pin; committed parity artifact NOT regenerated). F2 harvester provenance
  (bogus selector reproduced writing complete:true over 33 zero-receipt
  legacy rows at exit 0; now unknown/empty selectors exit 1 and the summary
  splits run_complete from inventory_complete requiring history.state ==
  'floor' receipts on all 33 canonical rows). F3 contrast identification
  (C0/C1/C2 ladder named in charter S3.1 second amendment + S5 + CLAUDE.md
  + seed + parity doc; package results never adjudicate S3.1). F4 wording
  (ZERO HISTORICAL SOURCE-LOGIC CHANGE + realtime-cadence scope block in
  the .pine contract header, 4-hunk diff re-verified after the edit;
  calc_on_every_tick untouched). Synthesis in the TVB-20 block below.
- DESIGN SESSION (plan mode, strat-methodology loaded, user supplied the
  10-setup live dictionary): rulings -- pine-exact detection (divergences
  vs skill R22/R17/color-gate documented, not re-designed); all 3-2s with
  Boom as a logged flag; 1H signal TF only (structural: the user's live
  TF); contrasts = C2-vs-C1 + a pattern-isolation arm; BF-prox veto =
  nearest alive harvest line across ALL pools (user flagged possible
  over-suppression -> pre-committed diagnostic); target exits REPLACE
  bf-harvest (brk/flip stay); fixed 1%/2% veto values.
- TIER B PRE-REGISTERED (94090e9, declared before any pattern/veto/target
  code): 5 arms (A0a deployed control 15m / A0b matched control 1H / A1
  isolation / A2 package-T1 / A3 package-T2), binding contrast statements,
  mechanics, diagnostics, named deferred arms.
- BUILT (163323b): analysis/paper/patterns.py (pine-exact M+T port, 12
  fixture tests; found the as-built PMG+ quirk -- streak walk seeded at the
  developing bar's own extreme makes the prefix unreachable for all 10
  enabled setups); engine extensions behind inert defaults (pattern entry
  mode, vetoes with bar-open alive-line snapshot, frozen target exits;
  entry events now carry trig; 9 tests; suite 140 passed); tier_b.py
  runner with the A0 determinism cross-check.
- EXECUTED + AUTOPSIED (163323b, report
  docs/experiments/tvb21_tier_b_report.md): headline = the package died to
  ONE identified mechanism -- trades BORN BEYOND their frozen reclaim
  target via re-entry-while-signal-persists (A2: 244/413 trades = -310.1pp
  vs +88.1pp on the rest; 73% one-bar exits; GOOGL chain reproduced on raw
  events). S3.1 contrast (A1 -7.7pp vs A0b +104.8pp) negative for patterns
  under BOTH fill conventions (measured drag 54.2pp declared). Chop veto
  does not transfer (47-100% per-symbol suppression; GOLD zero trades) --
  the user's fixed-percent concern confirmed with mechanism. Package arms
  DO collapse the MAE tail (0.78-1.32% avg vs 2.6-2.8% controls, worst 15%
  vs 37%). Boom split n=2 (unreadable, recorded). Both A0 controls
  reproduced committed Tier A cells field-exact (manifest check PASS).

### Context for next session

- USER REQUEST at close: build the TV-side PACKAGE strategy() so the user
  can run it live as the drift/bug detector. Assessed build shape: insert
  the M+T detection/ladder block INTO the tfc_bf_control_strategy.pine
  machinery (the pool engine is required by the BF-prox veto and C1-style
  exits) as a NEW script (Make-a-copy flow), arm toggles for A1/A2/A3, MCP
  compile, then its OWN parity gate vs the twin arms (twin entry events
  carry trig for the join). Deferred from TVB-21 deliberately -- a blind
  ~400-line Pine merge at session end creates drift instead of catching it.
- T1-floor entry guard (the user's own rule-base component) is the
  mechanism-motivated repair for the churn class; ATR-scaled vetoes for the
  chop transfer failure. Both need a-priori values pinned with the user
  before any run; both stay ablations vs C1.
- The BF-harvest-replacement exit ruling is revisitable AFTER visualization
  per the user -- as a NEW pre-registered variant, never a mid-run change.
- Tier B artifacts are deterministic from committed runner + bars + prereg;
  the fill-drag/churn/ladder diagnostics were post-hoc reads on
  deterministic replays (no artifacts modified).

### Files created/modified

- Fold-in (f90d0c9): analysis/paper/port_parity.py (hardened),
  tests/test_port_parity.py (+8), scripts/tvb19_harvest.mjs,
  analysis/reference/tv_deep/README.md, charter S3.1/S5, CLAUDE.md,
  tvb20 seed + parity docs, pine/tfc_bf_control_strategy.pine (header),
  HANDOFF + REVIEW_REQUEST flips, docs/reviews/tvb20-codex-audit.md
  (committed).
- Pre-reg (94090e9): docs/experiments/tvb21_tier_b_prereg.md.
- Build+run (163323b): analysis/paper/patterns.py (NEW),
  analysis/paper/tier_b.py (NEW), analysis/paper/engine.py (extensions),
  tests/test_patterns.py + tests/test_pattern_engine.py (NEW),
  analysis/paper/tier_b/ (manifest + 2 JSONL),
  docs/experiments/tvb21_tier_b_report.md (NEW).
- Suite: 140 passed, 2 skipped.

### Open

- [ ] TV-side package strategy() port + parity gate (TVB-22 headline; user
      request 2026-08-09)
- [ ] T1-floor guard + ATR-scaled veto variant pre-registration (values
      a-priori with user)
- [ ] Greenlit repairs bundle (TVB-18): F2 roster receipts + fail-closed,
      F3 5m-lifecycle warm-up regression, F4 eviction telemetry split,
      freeze-boundary invariant, SKHX tv_symbol/mintick backfill
- [ ] Nudge the M+T collaborator: PMG+ prefix structurally unreachable for
      break-directional setups (as-built streak-walk seeding)
- [ ] BF-harvest-replacement exit ruling revisit after visualization (user
      note, new pre-registered variant only)
- [x] HANDOFF.md over the 1500-line budget -- archived TVB-10..TVB-17 to
      docs/session_archive/HANDOFF_TVB10-TVB17.md (closed same session,
      TVB-21, user-approved)
- [ ] tvb8/tvb9 external reviews still unreturned (standing)

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb21-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED (2026-08-09; NEEDS-CHANGES; folded in by TVB-22
  same day -- all four findings independently reproduced before
  adjudication; synthesis below)
- Commits to review: `f90d0c9^..1cd6b0c` on `main` (4 commits: f90d0c9
  TVB-20 audit fold-in; 94090e9 Tier B pre-registration; 163323b Tier B
  build + run + report; 1cd6b0c session-end docs. RANGE-PIN RULE: the
  caret keeps f90d0c9 in the diff; sanity-checked -- `git diff
  --name-status f90d0c9^..1cd6b0c` lists all 23 files the session
  touched).
- Scope / what changed: TVB-20 audit fold-in (4 findings); Tier B
  pre-registration; pine-exact pattern layer + engine extensions + runner;
  Tier B execution + report.
- Focus areas (scrutinize these): (1) fold-in fidelity vs
  docs/reviews/tvb20-codex-audit.md (every finding reproduced/fixed or
  explicitly deferred); (2) patterns.py pine-exactness vs
  pine/strat_magnitude_targets_plus.pine (chain order, >= thr break forms,
  warm-up guards, ladder walk, hammer rule, the PMG quirk claim); (3)
  engine default-path invariance (entry_mode="arm" bit-exactness; the A0
  determinism check + committed-GOOGL parity pin as evidence); (4)
  pre-reg-vs-execution fidelity in tier_b.py (arms, vetoes vs fill price,
  bar-open alive-set snapshot, frozen-ladder exits, fill convention); (5)
  the report's churn-mechanism attribution and fill-drag decomposition
  arithmetic (born-beyond-T1 splits, 54.2pp drag) -- these came from
  post-hoc deterministic reads, verify they reproduce; (6)
  contrast-language discipline (S3.1 wording constrained to A1-vs-A0b, no
  promotion anywhere); (7) request.security: no executable Pine changed
  (control header comments only) -- confirm.
- Reviewed by: OpenAI Codex (GPT-5), verdict NEEDS-CHANGES
- Findings + CRITICAL SYNTHESIS (TVB-22 fold-in, 2026-08-09; every number
  below independently reproduced from committed runner + bars before
  adjudication):
  - F1 HIGH -- AGREE, CONFIRMED TO THE DECIMAL. The Tier B target exit
    uses one-sided predicates (long `h >= tgt` / short `l <= tgt`,
    engine.py:485-488) instead of the pre-registered "5m bar range reaches
    the level" containment. For trades BORN BEYOND their frozen target the
    predicate is true on bars wholly past the level, so the engine books a
    fill AT a price the exit bar never traded. Reproduced: A2 208/410
    target exits outside their exit bar; the 244 born-beyond trades split
    188 impossible-fill exits = -278.3pp vs 55 contained exits = -29.0pp.
    A3: 102/255 outside; 97 = -146.2pp vs 61 = -8.7pp. Requiring
    containment (all else unchanged) flips A2/A3 combined from
    -222.0/-127.5pp to +24.6/+31.0pp. CONSEQUENCE: the TVB-21 package
    verdict, the churn-loss MAGNITUDE attribution, candidate counts, and
    the package-arm MAE-tail metrics are INVALID pending a semantics
    ruling + rerun. What survives: the born-beyond re-entry MECHANISM is
    real (contained born-beyond exits are still structural losses, just
    small); both A0 controls; the A1-vs-A0b S3.1 contrast (negative for
    patterns) -- none touch the target branch. The audit's containment
    sensitivity is a DIAGNOSTIC, not a result: the contract for a target
    already marketable at entry (and the no-target skip, F2) must be
    pre-registered as a dated amendment BEFORE the A2/A3 rerun -- that is
    a user ruling, queued in TVB-22. The TVB-22 TV port (056f47b) mirrors
    the as-built predicates verbatim by design; it inherits the same fix
    once ruled, before its parity gate is meaningful.
  - F2 LOW -- AGREE. The no-target structural skip was a post-declaration
    choice never written into the prereg as a dated amendment, and it
    makes veto-rate denominators ambiguous (131 skipped signals counted
    as candidates but never veto-evaluated). Fold into the same amendment.
  - F3 LOW -- AGREE, REPRODUCED from committed rows: the report's plain
    3-2 census (182 / -163.0pp / 33%) is the ALL-11 scope (DRAM included,
    Boom removed); the declared 10-symbol roster gives 139 / -151.2pp /
    29.5%. Qualitative reading (largest, worst class) unchanged. Report
    annotated rather than silently rewritten.
  - F4 LOW -- AGREE. manifest git_head = 94090e9 (prereg-only commit; the
    runner first exists in 163323b): it proves prereg-before-code, not
    which source ran. The audit's own re-run reproduced all 55 rows + 5
    rollups exactly, so provenance is intact in practice. Future
    manifests get executed-blob hashes + clean/dirty state -- lands with
    the F1 rerun.
  - DISPUTED: nothing. The audit's positive checks (fold-in fidelity,
    pattern-port pine-exactness incl. the PMG+ unreachability proof,
    default-path invariance, A1 regeneration, no promotion) match our
    records.

---

## Session TVB-20: Audit fold-ins + layering-arc alignment + v6.1 CONTROL strategy() port (COMPLETE)

**Date:** 2026-08-07/08
**Status:** COMPLETE -- both returned audits folded in (every finding
reproduced before adjudication), the layering-arc research direction pinned
with the user in writing, and the v6.1 CONTROL strategy() port built,
mounted, and parity-gated PASS (full-span, three symbols, zero mismatches).

### What was accomplished

- AUDIT FOLD-INS (start of session): TVB-18 (`bef6dae`, 3 findings: window-end
  MTM tip-marking, freeze-slice labeling, empty-window fail-loud + the
  append-invariance regression test) and TVB-19 (`9f11a74`, 4 findings:
  nearest-rank medians fixed + artifacts regenerated diff-verified, SKHX
  identity made executable, harvester fail-closed rework, report wording).
  Both HANDOFF blocks below flipped to ADDRESSED with synthesis in place.
- LAYERING-ARC ALIGNMENT (user discussion, the session's pivot): the research
  program is a LAYER STACK tested as ablations -- TFC-only entries (layer 1)
  -> BF exits (layer 2, v6.1) -> TheStrat Magnitude+Targets (layer 3, the
  pattern dictionary + target ladder built with the user's collaborator).
  Sequencing confirmed: control port FIRST, then ONE design session (exit
  redesign + M+T layering together), then Tier B pre-registration. Captured
  verbatim-in-substance in `docs/experiments/tvb20_design_session_seed.md`
  (`bbdb10b`): the pattern-aliasing nuance (a lower-TF 3-1-2 aggregates to a
  3-2), the pattern frequency-x-performance census (deliberate-overfit
  ceiling frame), the BF-proximity entry rule confirmed as an EXHAUSTION VETO
  (~1% placeholder, possibly ATR-scaled; equivalently a minimum-magnitude
  requirement -- layers 2 and 3 meet in the same object), and the user's
  preset rule-base ("how complex do we have to make this?": 1H-or-less
  pattern + TFC + not near exhaustion; T1-always vs 2-3-target arms; ~2%
  ATR-scaled continuity-flip chop veto; 1D governing BF).
- CHARTER/CLAUDE.md RECONCILIATION (`bbdb10b`): the "No pattern tournament"
  invariant reworded to "Ablation, not tournament" (pre-committed blocks
  chosen a-priori by the user; per-pattern winner promotion stays forbidden;
  labeled overfit censuses = ceiling-mapping); charter S3.1 thesis promoted
  from baked-in assumption to HYPOTHESIS UNDER ABLATION via dated annotations
  at S3.1 and S5 (the S5 ablation frame already anticipated this).
- v6.1 CONTROL strategy() PORT (`2d1f25b`): `pine/tfc_bf_control_strategy.pine`
  -- diff vs v6.1 is exactly 4 hunks (contract header, strategy() declaration,
  order-emission block mirroring the internal position machine, table title).
  Decision-exact fill model (market orders on the signal bar, close fills via
  process_orders_on_close), commission 0, slippage 0, margin 0/0, pyramiding
  0, 100% equity, bar magnifier OFF. TV script "TFC-BF CONTROL [TVB-20]"
  (id USER;5226f6f46f034f4fbc8ca37af9cdf47a) created via the Make-a-copy UI
  flow with the full tab-binding verification (new id; all 31 pre-existing
  scripts' modified stamps byte-identical). Compile clean (one shorttitle
  length fix). Left MOUNTED with the Strategy Tester open on the
  TVB18-parity scratch layout.
- PARITY GATE PASS (docs/experiments/tvb20_control_port_parity.md): twin
  replayed over the committed TV-bar dumps sliced to each chart's actual
  first loaded bar (all three floored at 2026-05-25 00:00Z = dump starts);
  89/67/87 events matched on GOOGL/TSLA/DRAM over the FULL feed span, zero
  mismatches, break/flip exit prices float-exact (max |dp| = 0), entry/BF
  residuals declared (median 0.16-0.75 price units, the honest cost of
  close-fills). Tooling: `scripts/tvb20_deepload.mjs`,
  `scripts/tvb20_port_harvest.mjs`, `analysis/paper/port_parity.py`;
  artifacts under `analysis/reference/port_parity/`.
- THE FINDING -- PINE GATE WARM-UP: v6.1's gate helper
  (`ta.valuewhen(timeframe.change(tf), open, 0)`) has no value until the feed
  contains a period BOUNDARY, so a cold-started chart is gate-not-ready until
  its first MONTHLY roll (TV's first trade was 06-01 00:00Z on all three
  symbols; the twin's original bootstrap traded from day one). Fixed as
  `TwinConfig.pine_gate_warmup` (default False -- paper grading and every
  committed sweep replay bit-unchanged; both behaviors regression-tested in
  `tests/test_port_parity.py`). LIVE COROLLARY: a freshly mounted v6.1 chart
  cannot signal until the first month roll inside its loaded history.
- OPS NOTES: TradingView was running WITHOUT the CDP flag (user-opened) --
  full kill-first restart with `--remote-debugging-port=9222` required (the
  TVB-4 re-stage flow; single-instance Electron ignores the flag on join).
  `layout_switch` via internal API reported success but never landed; the
  working route is Manage layouts -> Open layout... UI dialog, which opens a
  NEW in-app tab -- `tab_list` + `tab_switch` to rebind the MCP target.

### Context for next session

- NEXT = the design session, PLAN MODE ON, strat-methodology skill loaded.
  Inputs: `docs/experiments/tvb20_design_session_seed.md` (the user's
  rule-base + point-by-point capture), the TVB-18/19 exit-design scope
  (flip coupling/UNCOUPLING, gate-vs-scenario flip, targets+BF overlay),
  Tier A's exit-cost findings (brk ~47pp / flip ~35pp median in-window vs
  the 30-40% MAE tail everywhere), and the week-1 adverse-runner gap.
- The user will supply the a-priori list of M+T setups they actually trade
  live (a design-session input, not a blocker).
- A/B mechanics: variants compare against the mounted CONTROL within TV
  under the one decision-exact convention, so the entry/bf close-fill
  residual cancels; cross-engine P&L claims must use twin prices.
- The tv_deep dumps end 2026-08-05; TV trades harvested past that are
  beyond_feed by construction. Re-harvest extends the feed if the design
  session wants fresher parity spans.

### Files created/modified

- `pine/tfc_bf_control_strategy.pine` (NEW -- the port; v6.1 untouched)
- `scripts/tvb20_deepload.mjs`, `scripts/tvb20_port_harvest.mjs` (NEW)
- `analysis/paper/port_parity.py` (NEW gate), `analysis/paper/engine.py`
  (pine_gate_warmup flag), `tests/test_port_parity.py` (NEW, 3 tests)
- `analysis/reference/port_parity/` (3 trade dumps + parity result)
- `docs/experiments/tvb20_control_port_parity.md`,
  `docs/experiments/tvb20_design_session_seed.md` (NEW)
- `docs/ATLAS_Timeframe_Continuity_Charter.md` (S3.1/S5 amendments),
  `CLAUDE.md` (invariant reword)
- Fold-in files per the TVB-18/19 blocks below (`bef6dae`, `9f11a74`)
- `.claude/commands/session-end.md` (Open-block convention, cross-repo)

### Open

- [ ] Design session (plan mode): exit redesign + Magnitude+Targets layering
      -- seed is docs/experiments/tvb20_design_session_seed.md
- [ ] User to supply the a-priori list of live-traded M+T setups
- [ ] Greenlit repairs bundle (TVB-18): F2 roster receipts + fail-closed, F3
      5m-lifecycle warm-up regression, F4 eviction telemetry split,
      freeze-boundary invariant, SKHX tv_symbol/mintick backfill (future
      rosters only)
- [ ] Tier B (design-gated, pre-registered)
- [ ] tvb8/tvb9 external reviews still unreturned (standing)
- [ ] Optional /session-end protocol fix: carry unreturned review requests
      forward instead of single-writer overwrite (offered TVB-20, not
      requested)

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb20-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: ADDRESSED (returned 2026-08-08, NEEDS-CHANGES, 3 MEDIUM +
  1 LOW; all four findings independently REPRODUCED by TVB-21 before
  adjudication, fixes landed same day). Synthesis: the audit VALIDATED the
  headline before critiquing the tooling -- it independently reconstructed
  the 89/67/87 parity result, regenerated all 9,504 sweep rows + 864 rollups
  bit-exact under the default-off warm-up flag, reproduced both fold-ins,
  and confirmed frozen week-1 artifacts, the 4-hunk Pine diff, and zero
  lookahead. The PASS stands; the findings future-proof the instruments.
  Nothing disputed materially.
- Commits to review: `bef6dae^..fffbacb` on `main` (5 commits: bef6dae,
  9f11a74, bbdb10b, 2d1f25b, fffbacb; RANGE-PIN RULE: the caret keeps
  bef6dae itself in the diff; sanity-checked -- `git diff --name-status
  bef6dae^..fffbacb` lists all 34 files the session touched).
- Scope / what changed: TVB-18/19 audit fold-ins; layering-arc seed +
  charter/CLAUDE.md amendments; the v6.1 CONTROL strategy() port + full-span
  parity gate (PASS) + the pine_gate_warmup engine flag.
- Focus areas (scrutinize these): (1) the fork's ZERO-SEMANTIC-CHANGE claim
  -- diff pine/tfc_bf_control_strategy.pine vs pine/tfc_bf_watch.pine and
  verify the 4-hunk claim and that the emission block cannot feed back into
  decisions; (2) parity method validity in analysis/paper/port_parity.py --
  the ts-offset selection, beyond_feed and open-trade handling, the
  close-fill cross-check, full-span-vs-window claim; (3) pine_gate_warmup
  isolation -- default False must leave compare_config/sweep replays
  bit-identical (the committed sweep artifacts must NOT change); (4)
  decision-exact residual accounting -- no hidden P&L claim anywhere; (5)
  no frozen week-1 artifact modified in the range; (6) request.security:
  the new .pine must add none (it forks v6.1 verbatim -- verify).
- Reviewed by: local Codex CLI (GPT-5), returned 2026-08-08, via
  /session-review
- Findings (all CONFIRMED by TVB-21 reproduction; verbatim in
  docs/reviews/tvb20-codex-audit.md):
  - F1 MEDIUM, parity gate not multiplicity-safe: REPRODUCED on the committed
    GOOGL artifact -- a duplicated closed-trade row false-PASSed with
    tv_events_in_feed 91 vs matched 89 (dict-comprehension collapse), and a
    corrupted direction 's' silently aliased to short and PASSed. FIXED:
    injective join enforced in analysis/paper/port_parity.py -- fail-closed
    validate_trades (direction enum, exit-comment parse, at-most-one FINAL
    open row) runs before parsing; validate_events rejects duplicate
    (ts,action,dir,kind) keys + bad enums on BOTH streams; PASS now also
    requires twin == tv_in_feed == matched cardinality; gate() extracted
    artifact-free so the false-pass fixtures are permanent (8 new tests,
    including the committed-GOOGL 89/89/89 pin). The committed
    tvb20_parity_result.json is NOT regenerated -- its values are unchanged
    and the hardened gate is test-pinned against it. Matters forward: M+T
    multi-target variants are exactly the streams that can emit same-key
    events legitimately, so the key schema must widen when they arrive.
  - F2 MEDIUM, harvester can stamp complete over legacy inventory:
    REPRODUCED in scratch on a copy of the committed summary --
    TVB19_COINS=BOGUS gave zero targets, zero failures, exit 0, and REWROTE
    the summary with complete:true over 33 legacy rows carrying ZERO floor
    receipts (the committed 2026-08-05 file has no complete field at all; a
    rerun would ADD the false receipt). FIXED in scripts/tvb19_harvest.mjs:
    unknown/empty selectors exit 1 before anything runs; summary now splits
    run_complete (this run's subset) from inventory_complete (all 33
    canonical rows error-free with history.state=='floor'). Verified: bogus
    selector exits 1 leaving the file byte-untouched; a simulated successful
    GOOGL-only rerun yields run_complete true / inventory_complete false
    (1/33 receipted). tv_deep README documents the split; committed
    dumps/summary untouched.
  - F3 MEDIUM, layering contrast not identified: CONFIRMED by reading the
    three records side by side (charter amendment said "continuity-only
    control"; seed + parity record named v6.1 = layers 1+2). FIXED in docs
    BEFORE the design session: charter S3.1 second amendment names the
    ladder C0 (S5 minimal continuity-only, whole-strategy sense) / C1
    (C0 + BF exits = v6.1 = the mounted CONTROL) / C2 (C1 + M+T package) and
    qualifies the "if it wins, 3.1 is revised" inference -- a C2-vs-C1
    result adjudicates the PACKAGE; revising 3.1 itself requires a
    pattern-isolating contrast (non-pattern mechanics held fixed) or the
    conclusion stays composite-constrained. S5 amendment, CLAUDE.md bullet,
    seed doc, and parity doc now name the same ladder. Which contrasts run
    (incl. any held-exit pattern-only arm) is deliberately left to the
    design-session pre-registration.
  - F4 LOW, ZERO-SEMANTIC-CHANGE overstated: CONFIRMED (with
    calc_on_every_tick=false a strategy evaluates the realtime bar at its
    closing tick; the indicator ticks intrabar; historical bars identical).
    FIXED as wording only: .pine contract header now claims ZERO HISTORICAL
    SOURCE-LOGIC CHANGE with an explicit SCOPE block (realtime cadence out
    of scope, intentionally not parity-tested, calc flag stays false);
    parity doc intro + a consequences bullet mirror it; CLAUDE.md 2U-timing
    bullet carries the declared-exception parenthetical. The 4-hunk diff
    claim re-verified AFTER the edit (the qualification lives inside the
    inserted header hunk). The TV-side script now trails the local source by
    this comment block only -- sync at the next TV session; comments do not
    change compiled behavior.

---

## Session TVB-19: Overnight Tier A sweep + clock census + deep TV harvest (COMPLETE)

**Date:** 2026-08-04/05
**Status:** COMPLETE -- overnight autonomous run under explicit user
direction (pre-reg -> sweep -> census -> harvest -> morning report; no
design/flip/ladder code), then a morning visualization discussion that
set the next build: a v6.1 CONTROL strategy() port with a parity gate.

### What was accomplished

- TIER A PRE-REGISTRATION FIRST (the F1 lesson applied literally):
  docs/experiments/tvb19_tier_a_prereg.md committed at 2a78ec2 BEFORE
  the runner existed or any cell ran. Grid = existing TwinConfig knobs
  only (864 cells), window 07-06 -> 08-03 Monday-to-Monday, metrics,
  exclusions, DELIBERATE OVERFIT / in-sample-ceiling label.
- TIER A SWEEP EXECUTED (analysis/paper/sweep_tier_a.py, ~4 min wall,
  warm-key task grouping 594 warm-ups instead of 9504): 9504
  per-symbol rows + 864 rollups + manifest (timestamps, bar hashes)
  committed under analysis/paper/sweeps/tvb19_tier_a/. Reading (full
  plain-language version: docs/experiments/tvb19_overnight_report.md):
  spread -13.8..+171.3pp combined, median +82; the ENTIRE top = the
  no-backstop corner (brk+flip OFF, median +132.5) = "never realize a
  loss in a kind window" -- the adverse-runner question inverted, a
  question not a verdict; arm TF monotone (5m +23 -> 1H +112 median);
  brk costs ~47pp / flip ~35pp median IN-WINDOW; shape knobs
  (n_max/min_sep/pool_cap) near-inert = the BF ladder mechanism is
  knob-robust; adverse-runner MAE 37-40% config-invariant at grid
  scale (extends TVB-16's 2-cell finding to 864); deployed cell
  +47.4pp with -73.5pp open-runner drag (3 deep shorts at window end,
  week-1 class again). Nothing promoted. Tests added (grid shape,
  determinism, accounting identities, parity-symbol exclusion).
  [TVB-19 audit fold-in 2026-08-07: "med" fields were nearest-rank
  picks, not true medians (worst two-trade error 9.77pp) and the
  rollup omitted preregistered metrics -- runner fixed
  (statistics.median + full roster schema), artifacts REGENERATED with
  combined/dd/counts verified unchanged; no-backstop median +132.4;
  min_sep is a real 14.5pp axis (knob-inert wrong for it); worst-MAE
  spans 29.8-39.6% (372/864 below 37) = severe tail EVERYWHERE, not
  "37-40 invariant"; top-5 includes one 30m cell. Report corrected in
  place; headline findings (54-cell no-backstop top, arm monotone,
  brk/flip costs) all survived independent reproduction.]
- RTH-vs-UTC CLOCK CENSUS: MATERIAL. analysis/clock_census.py +
  analysis/reference/tvb19_clock_census.json: the deployed D/W/M gate
  disagrees with itself across venue-clock vs RTH-anchored opens on
  30.84% of 87,683 scored 5m bars (23.6-40.6% per symbol); the day leg
  drives it (structural: different "days" ~13.5h/weekday + all
  weekend); disagreements cluster 20-22 ET and 05-07 ET; the clocks
  generate mostly DIFFERENT flip events (2519 UTC vs 1710 RTH, ~220
  shared; hard up<->down flips rare, 6 vs 7); GOLD demonstrates the
  monthly-leg mechanism (opens 2.1% apart on Jul 1, price between
  them 65% of the window). Per the seeded decision rule the
  pre-registered anchor-clock arms are now justified -- a design
  input, deliberately NOT run. Calendar tests committed.
- DEEP TV HARVEST 33/33 (scripts/tvb19_harvest.mjs -> analysis/
  reference/tv_deep/ + README, ~19MB committed): TV launched fresh on
  CDP (Store-app incantation), TVB18-parity scratch layout only. TV 5m
  depth = uniform floor 2026-05-25 (~10 weeks, ~4x the HL floor,
  TV-side window); 15m to listing or ~20k-bar cap; 60m to listing
  (deepest GOOGL 2025-11-18). [TVB-19 audit F2/F3 2026-08-07: the 5m
  "uniform floor" claim was FALSE -- it is a ~20.2-21.6k-bar cap
  (AMZN/MSFT/AAPL reach 05-18; NBIS/SKHY listing-bound); every dump
  ends on a possibly-forming bar (drop on consume); the harvester was
  fail-open and its default coin list could never regenerate the
  committed 33/33 (SKHX vs SKHYNIX) -- now fail-closed with an
  explicit roster->TV mapping and merge-by-key summary; the identity
  claim is now executable (analysis/verify_skhx_identity.py, 9187
  overlap / 9183 float-exact reproduced). Committed dumps unchanged.] Trap resolved: HL xyz:SKHX = TV
  HIP3XYZ:SKHYNIXUSDC.P -- TV symbol search does NOT index HIP3XYZ
  (direct chart load only); identity PROVEN (9183/9187 overlapping 5m
  closes float-exact + listing-date match). Side-catch: week-1 roster
  SKHX mintick was hl_inferred 0.1 (tv_symbol null at freeze); TV
  true tick 0.001. Frozen roster untouched; future-roster backfill
  item.
- MORNING DECISION (user, 2026-08-05): the overnight sweep did NOT use
  the Magnitude+Targets indicator anywhere (confirmed to user --
  entries/exits = the v6.1 twin only; ladder is Tier B/design-gated).
  Visualization direction chosen: TradingView-NATIVE, not a custom
  explorer -- fork the deployed v6.1 watch indicator into a CONTROL
  strategy(), parity-gate against the twin (declared TV-vs-HL feed
  deltas), leave the Strategy Tester mounted for browsing; it then
  becomes the A/B baseline for exit-design variants. Custom HTML
  explorer dropped; trace-mode twin instrumentation deferred until
  the design session needs forensics.

### Context for next session

- Priority 1 = the v6.1 control strategy() port + parity gate (see
  .session_startup_prompt.md for pinned conventions: commission 0,
  margin 0/0, fill model, deep-load-first, tab-binding trap). Zero
  semantic change; parity is the proof; STOP-and-ASK on any semantic
  question (skill still mid-rebuild).
- The exit-design session follows with sweep-quantified stakes and
  the anchor clock as a new tested variable. Repairs bundle
  F2/F3/F4 + invariant still greenlit and pending.
- TradingView was left RUNNING with CDP on the TVB18-parity scratch
  layout (user's live layouts untouched all session).
- Week-1 frozen artifacts untouched; week 1 still has NO official
  number (adjudication stands).

### Files created/modified

- Created: docs/experiments/tvb19_tier_a_prereg.md,
  analysis/paper/sweep_tier_a.py, tests/test_sweep_tier_a.py,
  analysis/paper/sweeps/tvb19_tier_a/ (manifest + 2 JSONL),
  analysis/clock_census.py, tests/test_clock_census.py,
  analysis/reference/tvb19_clock_census.json,
  scripts/tvb19_harvest.mjs, analysis/reference/tv_deep/ (33 dumps +
  summary + README), docs/experiments/tvb19_overnight_report.md
- Modified: .session_startup_prompt.md, docs/HANDOFF.md,
  docs/reviews/REVIEW_REQUEST.md (session-end)
- Suite: 103 passed, 2 skipped (6 new tests)

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work
> (range below) and write a verbatim assessment to
> docs/reviews/tvb19-codex-audit.md. See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: ADDRESSED (returned 2026-08-07, NEEDS-CHANGES; all
  four findings independently reproduced by TVB-20 before adjudication;
  fixes + artifact regeneration landed same day)
- Commits to review: `2a78ec2^..5289f9b` on `main` (6 commits: 2a78ec2
  pre-registration; 48d3aef sweep runner + tests; 4eb5eea clock census;
  72526c9 sweep results; 2fa892a TV harvest + overnight report; 5289f9b
  session-end docs; the pin commit follows outside the range, per
  precedent). RANGE-PIN RULE: caret included; sanity-checked --
  `git diff --name-status 2a78ec2^ 5289f9b` lists all 49 files the
  session touched.
- Scope / what changed: pre-registered 864-cell deliberate-overfit
  sweep (runner + committed results), RTH-vs-UTC clock census (code +
  committed results), deep TV-bar harvest (33 datasets + provenance),
  overnight report, session-end docs.
- Focus areas (scrutinize these): (1) pre-reg-vs-execution fidelity --
  does sweep_tier_a.py implement EXACTLY the declared grid/window/
  metrics (warm-key grouping correctness, roster equity-curve
  alignment/forward-fill in _rollup, weekly entry-ts slicing,
  parity-symbol exclusion); (2) clock_census.py correctness -- RTH
  roll calendar (holiday table, weekend-to-Friday attribution,
  first-trading-day week/month), 1h-seeding deltas (declared 30-min
  RTH lateness), whether the 30.84% headline and per-leg attribution
  survive scrutiny; (3) overfit-language discipline -- the report and
  commit messages must nowhere promote a cell or morph the ceiling
  into a performance claim (week-1 adjudication language intact);
  (4) harvest identity claims -- SKHYNIX=SKHX float-exact
  verification, the mintick 0.1-vs-0.001 catch, and that no frozen
  week-1 artifact changed; (5) request.security N/A (no Pine changed)
  but confirm.
- Reviewed by: local Codex CLI (GPT-5), 2026-08-07, via /session-review
  (this file's pointer described TVB-19 correctly)
- Findings (all CONFIRMED by TVB-20 reproduction; docs/reviews/
  tvb19-codex-audit.md):
  - F1 MEDIUM: sweep "med" fields were nearest-rank picks (round(q*(n-1))
    with banker's rounding = the LOWER of a pair on n=2; all 398
    two-trade rows wrong, worst 9.77pp) and _rollup omitted the
    preregistered roster trade-median/win-rate/MFE/gb-median. FIXED:
    statistics.median + full schema + even-sample/schema tests;
    artifacts REGENERATED -- diff-verified: only the 3 med fields
    changed in by_symbol, only the 5 new fields appear in rollup,
    every accounting/dd/count field byte-stable. Report medians
    re-derived: only the no-backstop corner moved (+132.5 -> +132.4).
  - F2 MEDIUM: the committed 33/33 harvest is not regenerable by the
    default runner (coin list said SKHX, TV needs SKHYNIX; summary
    whole-file rewrite on partial reruns). FIXED forward: explicit
    roster->TV SYMBOL_MAP, merge-by-key summary, run fails unless all
    datasets land. Identity claim made executable:
    analysis/verify_skhx_identity.py + skhx_identity_check.json
    (9187 overlap / 9183 float-exact / 4 mismatches max delta 1.7 --
    reproduced from committed bars).
  - F3 MEDIUM: loadHistory declared the floor after ONE unchanged
    700ms sample and the caller ignored err/capped; every dump ends on
    a possibly-forming bar; the "uniform 5m floor 2026-05-25" claim is
    false (05-18 for AMZN/MSFT/AAPL, listing for NBIS/SKHY -- it is a
    ~20.2-21.6k-bar cap). FIXED forward: 3-stable-round fail-closed
    detection with recorded termination state; forming-tail + floor
    caveats declared in README/report; committed dumps unchanged.
  - F4 LOW: report prose corrected in place -- min_sep is a real
    14.5pp axis (not "all shape knobs 2-7pp"); worst-MAE spans
    29.8-39.6% with 372/864 below 37 (severe-tail-everywhere, not
    "37-40 invariant"); top-5 includes one 30m cell; second-worst
    cell is 15m/flip-off.
  - Reviewer independently CONFIRMED: P/L accounting + roster
    drawdown (131.4984 exact), warm-key soundness (16-variant
    refutation attempt failed), census headline (30.8418% + all
    sub-counts), overfit language, frozen artifacts untouched,
    prereg-before-code. Headline findings all stand.

---

## Session TVB-18: Week-1 close-out + TVB-15 audit fold-in + design direction (COMPLETE)

**Date:** 2026-08-03/04
**Status:** COMPLETE -- the overdue paper close-out plus a same-session
external-review round trip. First session run over remote control. Every
mechanical standing item cleared; the one remaining open arc is the
exit-design session, now fully staged with user decisions recorded.

### What was accomplished

- ARCHIVE CATCH-UP + WEEK CLOSE-OUT: all 11 roster symbols pulled through
  08-04 00:45Z (5m/1h/1d; merged spans 07-03 -> 08-04) -- the 07-20 window
  start secured ~3 days before the HL floor slide-off. Replay closed the
  07-20..07-27 window deterministically: 38 committed events reproduced
  BYTE-IDENTICALLY, 43 appended (81 total; 44 entries / 37 exits). Suite
  green (97 passed, 2 skipped) incl. 24 paper goldens. Commit a1a886f.
- WEEK-END PASS (protocol doc): full-record realized -27.61pp over 37
  closed / open MTM -40.65pp / combined -68.25pp (gross, 1x, roster excl
  DRAM). [TVB-18 audit F1, 2026-08-07: open/combined were ARCHIVE-TIP
  (08-04) marks, not window-end; corrected window-end control -5.58pp
  open / -33.18pp combined, variant -6.94 / -22.38. Realized and exit
  classes unaffected. See protocol doc.] Exit classes: 24 BF harvests
  +1.86% avg (win-by-construction), 7 adverse-breaks -8.15% avg (worst
  NBIS -26.82, MRVL -14.32), 6 flips -2.54% avg. TSLA the
  counterexample: 8/8 harvests +18.99pp. Full-week ablation (control vs
  user live variant): knobs RE-TIME the same book (combined -68.25 vs
  -63.13 tip-marked; -33.18 vs -22.38 window-end), adverse-runner class
  config-invariant.
- PARITY PASS (DRAM/TSLA/GOOGL, fresh mounts on scratch layout
  TVB18-parity; the deployed accumulated-history instances were removed
  from all layouts during the user's SNDK-focus period): positions and
  gate composites match EXACTLY (DRAM's one apparent gate mismatch
  resolved numerically -- 1.3 cents [audit F2 correction; was "13
  cents"] through the monthly open across a 15-min read gap); every
  SHARED rung is the same structural line within 0.004-0.04% [audit F2,
  2026-08-07: the "next" cells quoted shared rungs, NOT the twin's
  nearest operative lines -- nearest-line parity was not established;
  see protocol doc]. Census NOT comparable from fresh mounts.
  NEW OPERATIONAL FINDING: loaded chart history is load-bearing state --
  a remount silently thins the harvest ladder (fresh DRAM nearest exit
  41.04 vs full-history twin 12h rung 47.39; -5% harvest vs -18% ride).
  Twin side: analysis/paper/parity_state.py (committed).
- TVB-15 EXTERNAL REVIEW ROUND TRIP, same session: paste-ready prompt
  delivered (range-pinned, post-range guardrails, known-open list); user
  ran Codex CLI; audit RETURNED NEEDS-CHANGES (1 HIGH + 3 MEDIUM) and was
  folded in the same day -- ALL FOUR findings independently reproduced
  before adjudication (TVB-14 precedent). Commit 0789d2c.
  - F1 HIGH: window opens 00:00, roster froze 14:31:21 -- 18/81 events and
    12/37 closed trades (incl. BOTH catastrophic adverse-breaks) entered
    pre-freeze. Realized flips -27.60 -> +14.37pp in the post-freeze-entry
    slice (analysis/paper/freeze_slice.py, committed). The adverse-runner
    gap SURVIVES: the open runners (GOOGL / AMZN / SKHY) all entered
    post-freeze [TVB-18 audit F1: their -15.8 / -19.5 / -12.1 depths
    are archive-tip marks accrued post-window; window-end -0.97 /
    +0.39 / +1.56].
  - F2: committed snapshot = 13:26:36Z (65 min early); freeze source
    unrecoverable; roster.py fails open.
  - F3: coarse 1h/1d warm-up changes LIFECYCLE state, not just anchors --
    reviewer's TSLA instance reproduced exactly; delta 1 amended.
  - F4: evict-alive counts fallback formation evictions, not alive sides;
    the TVB-15 "14 vs 13+1=14" parity line was WRONG (annotated in place;
    actual day-one twin counter 15, as the protocol doc recorded).
- WEEK-1 ADJUDICATED BY THE USER (recorded in the protocol doc, c93dcaf):
  NO official number -- performed wrong, stands as a process test run
  (gotchas + why-trades-went-good/bad); both views stay as documentation.
  REPAIRS ALL GREENLIT (F2 + F3 + F4 + freeze-boundary invariant for
  future rosters; week-1 files stay frozen). NO week-2 rerun now; next
  build focus = the exit-design step.
- DESIGN DIRECTION RECORDED (user, verbatim intent): the Magnitude+Targets
  [Custom] indicator (committed as pine/strat_magnitude_targets_plus.pine
  + README, c954c22 -- logic-identical fork of the partner original,
  display/UX layer only, zero request.security) is the where-to-take-
  profit half; target ladder = harvest path (5-6 rungs, count TBD); BF =
  exhaustion overlay at extended rungs; kill-signal there = continuity
  turning against the position while extended. Drop-the-month agreed AS A
  START with the COUPLING caveat -- at period boundaries flips are not
  independent votes (new week = D+W open on the same print; month couples
  with day always, with week only on Monday month-starts; stacked levels
  can break on one tick = domino). Design must resolve gate-flip
  (close-vs-open, deployed) vs scenario-flip (prior-extreme break, STRAT)
  semantics. NO flip code before the design session (skill mid-rebuild,
  Ambiguity Policy strict).
- THESTRAT.AI CORPUS LANDED + ASSESSED + PROTECTED: docs/thestrat_ai/
  (417 files, 48.7 MB; 70 articles, 121 SVG figures with OBSERVED/DERIVED
  separation and a 164:2 label-agreement ledger; grep-first discipline by
  its own README; term-index.csv). It answered the coupling question BY
  NAME: UNCOUPLING (03/07) -- "until the opens separate, some of your
  four facts are the same fact" + separation schedule + month-start
  rules (RTH arithmetic; translate to 24/7 UTC rolls per charter S2).
  Vocabulary trap: corpus "flip" = new 60-minute open (03/06). GITIGNORED
  (3200e3b): public remote, scraped curriculum mirror, not ours to
  republish (VBT protective class); stays fully greppable locally.
- NEW QUESTION SEEDED (user, from live-trading experience): the RTH-clock
  test -- what changes in backtest numbers for the SAME perp when
  uncoupling/flip rules apply only during RTH? These are oracle-priced
  equity perps under TWO clocks (venue 00:00 UTC vs underlying 9:30 ET).
  Cheap first step = read-only census of UTC-clock vs RTH-clock signal
  disagreement per symbol per hour; full pre-registered arms only if
  disagreement is material. The anchor clock is a tested variable, not an
  assumption.
- HOUSEKEEPING: /pre-commit Check 2 amended to the corrected lookahead
  rule (TVB-17 blocker cleared -- the permission classifier allowed the
  edit this time); TVB-15 statuses flipped RETURNED in REVIEW_REQUEST.md
  + the TVB-15 HANDOFF block (wrong parity line annotated in place).

### Context for next session

- The design session is THE next move (plan mode ON, STOP-and-ASK
  throughout). Its brief, inputs, and the user's recorded decisions are
  consolidated in the protocol doc ("Week-1 adjudication" + design bullet)
  and .session_startup_prompt.md.
- The greenlit repairs (F2/F3/F4 + invariant) land before any future
  graded run; F4's Pine side deploys with the design bundle (no live chart
  mounts the indicator -- zero drift meanwhile).
- TradingView state: scratch layout TVB18-parity exists (fresh-mount
  TFC-BF for parity reads; harmless, delete or keep); the user's live
  layouts are SNDK-focused with a community "Strat Assistant" study; new
  user scripts since TVB-17: the Magnitude+Targets pair (07-30) and
  "Memory/Storage Complex Composite (HIP-3)" (08-03).
- The HL 5m floor keeps rolling: post-week bars through 08-04 are
  archived; nothing time-critical is pending.

### Files created/modified

- Created: analysis/paper/parity_state.py, analysis/paper/freeze_slice.py,
  pine/strat_magnitude_targets_plus.pine + .README.md,
  docs/reviews/tvb15-codex-audit.md (reviewer-written, committed here)
- Modified: analysis/paper/bars/* (33 files), events_week1.jsonl,
  scoreboard_week1.md, docs/experiments/tvb15_paper_week1_protocol.md
  (week-end pass + audit fold-in + adjudication + corpus pointer),
  docs/HANDOFF.md (TVB-15 annotation + this entry), REVIEW_REQUEST.md,
  .claude/commands/pre-commit.md, .gitignore, .session_startup_prompt.md
- Local-only: docs/thestrat_ai/ (gitignored corpus)

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work
> (range below) and write a verbatim assessment to
> docs/reviews/tvb18-codex-audit.md. See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: ADDRESSED (returned 2026-08-07, NEEDS-CHANGES; all
  three findings independently reproduced by TVB-20 before adjudication;
  fixes landed same day)
- Commits to review: `a1a886f^..57417e2` on `main` (6 commits: a1a886f
  week-1 close-out; c954c22 indicator pair; 0789d2c audit fold-in;
  c93dcaf adjudication; 3200e3b corpus gitignore; 57417e2 session-end
  docs; the pin commit follows outside the range, per precedent).
  RANGE-PIN RULE: caret included; sanity-check
  `git diff --name-status a1a886f^ 57417e2` lists every file the session
  touched.
- Scope / what changed: week-1 archive/replay close-out + week-end pass +
  fresh-mount parity; TVB-15 audit fold-in (freeze_slice + doc
  corrections + status flips); the Magnitude+Targets [Custom] indicator
  pair; week-1 adjudication + design-direction records; corpus gitignore.
- Focus areas (scrutinize these): (1) freeze_slice.py correctness (slice
  boundary semantics: entry_ts vs event ts, parity exclusion, open-MTM
  attribution) and whether the +14.37pp clean-slice framing carries any
  hidden performance claim the adjudication forbids; (2) parity_state.py
  fidelity to replay.py conventions (warm-up, seed windows, last-bar
  drop) and the parity pass's honesty about fresh-mount limits; (3) the
  fold-in adjudications vs the audit text -- did TVB-18 reproduce F1-F4
  faithfully and act proportionately; (4) the amended pre-commit Check 2
  wording vs pine/README.md rule 3; (5) the new pine pair: zero
  request.security claim, defaults-render-identical claim vs the
  tv_indicators canonical copy (byte-identical check); (6) gitignore
  protection completeness for docs/thestrat_ai/ on the PUBLIC remote.
- Reviewed by: local Codex CLI (GPT-5.4), 2026-08-07, via standalone
  paste prompt (REVIEW_REQUEST.md had been rewritten to TVB-19 -- the
  request survived only in this block)
- Findings (all CONFIRMED by TVB-20 reproduction before adjudication):
  - F1 HIGH: compare_config.py marked open positions at rows_5m[-1]
    (archive tip, 08-04) instead of the last in-window close (07-26
    23:55Z) -- every open-MTM/combined figure in the week-end pass was
    tip-marked. Reproduced to the digit (control -5.58 open / -33.18
    combined window-end vs -40.65 / -68.25 tip; variant -6.94 / -22.38
    vs -47.69 / -63.13; GOOGL/AMZN/SKHY window-end -0.97 / +0.39 /
    +1.56 vs tip -15.8 / -19.5 / -12.1). FIXED: mark from week_rows +
    empty-window guard + mark-ts printed; regression
    tests/test_compare_config.py pins append-invariance. Docs annotated
    in place. REFRAME: the deep runner marks are post-window
    continuation evidence (the no-exit ride is real and still open
    8-12 days after entry) -- stronger for the exit-design question,
    but not week-1 window-end MTM. sweep_tier_a.py checked: marks at
    rows_5m[wj-1] INSIDE its window -- TVB-19 sweep numbers unaffected.
  - F2 MEDIUM (and WIDER than flagged): the parity table's "next dn/up"
    cells quoted rungs shared with the fresh mount, not the twin's
    nearest operative lines. Audit flagged DRAM (nearest 47.3904 12h lo
    / 53.3896 12h up vs quoted 41.0232 W / 71.9622 D); reproduction
    found the same substitution on TSLA dn (nearest 291.418 M N3 vs
    quoted 265.948 D N1) and GOOGL dn (nearest 316.766 12h N1 vs quoted
    306.89 W N3) -- engine.py exit scan treats ALL alive pool lines as
    operative. Also "13 cents" -> 1.3 cents. Docs corrected/narrowed:
    shared-rung parity established, nearest-line parity NOT.
  - F3 LOW: freeze_slice.py CLI printed "clean-entry slice" with no
    caveat. FIXED: relabeled "sensitivity slice" + prints
    heat-conditioning / not-official-number lines.
  - Adjudication unchanged: week 1 still has NO official number; frozen
    artifacts untouched (code + docs only).

---

Older sessions are archived VERBATIM: TVB-10 .. TVB-17 (exit-symmetry
ablation; champion search; exit-arc redirect; BF comprehension; rolling
compound-3 pools v4->v6; paper twin + week-1 freeze; ride-along + config
ablation; context-engineering audit) in
docs/session_archive/HANDOFF_TVB10-TVB17.md, and TVB-0 .. TVB-9 in
docs/session_archive/HANDOFF_TVB0-TVB9.md.
