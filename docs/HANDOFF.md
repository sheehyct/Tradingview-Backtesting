# HANDOFF -- tradingview-backtesting

> Newest session entry at the TOP. Keep under 1500 lines; archive older entries to
> `docs/session_archive/` when it grows past that.

---

## Session TVB-26: TVB-25 audit folded in full, canonical rerun (COMPLETE)

**Date:** 2026-08-16
**Status:** COMPLETE -- the TVB-25 external audit (NEEDS-CHANGES, 1 HIGH +
4 MEDIUM + 2 LOW) folded the same day it returned: all seven findings
reproduced in-repo BEFORE adjudication, zero disputes, two user rulings,
engine/runner repaired, canonical artifacts regenerated under prereg
amendment 2026-08-16b, report + ledger corrected. Seven commits pushed.

### What was accomplished

- ALL SEVEN FINDINGS REPRODUCED FIRST (read-only scripts against
  committed artifacts): F1 executed multi-class bars P2 July 21
  all-symbols / 14 roster vs 0 stored (WORSE than the audit's lower
  bounds; the audit's counts were roster-scoped); F3 D14 entry-hour
  joins 14/14/15 July + 8 (6 roster) fresh, matching the audit; F5
  arithmetic verified to the decimal (A0b fresh combined +76.4784 vs the
  quoted realized +55.65; matched means +0.7118 vs +0.3214; D5 receipt
  +1.7897); F7 D13 git-diff 31/33 files at two timestamps; F2/F4/F6
  confirmed by inspection.
- USER RULING 1 (D14 entry-hour, audit F3): literal-inclusive -- the
  entry hour COUNTS. Key fold fact: mid-hour entries ALREADY counted
  pre-entry same-hour breaks, so only this reading closes the
  evaluation-order gap without rewriting committed behavior. Engine
  post-entry check on the hour-completing entry bar (state_degenerate
  counter, i3-before-state order), long/short/one-tick boundary tests.
- ENGINE/RUNNER REPAIRS (cea3372, committed before the rerun, forward
  protocol): D9 census transition-accumulated (the bar-start snapshot
  could not see the bank->floor and retrace->breakeven armings) +
  collision_pairs per-combination diagnostic + fixture assertion;
  zero-duration episodes guarded on BOTH runner episode paths with an
  end-to-end regression; entry-stream gate expectation DECLARED
  (_expected_family_arms: full family canonical, requested+anchors
  smoke) + caller-boundary mutation test + veto_counts modulo rule
  pinned exact-scope; Signal.stop_src_ts absolute source timestamp
  (frozen, drift-asserted, on stop-arm entry events). 7 new tests
  (suite 265 passed, 2 skipped).
- CANONICAL RERUN (0c95a60): both windows, all gates PASS. Field-diff
  receipt vs the pre-fix snapshot: every non-S0 non-stop event stream
  byte-identical; D1S/PX additive stop_src_ts only; S0a/S0b/S0c changed
  by exactly the ruled D14 scratches (July S0a 866 -> 877 trades,
  +194.8 -> +195.3 combined; fresh 6 roster scratches per arm);
  matched-entry receipts unchanged to the FOURTH DECIMAL in both
  families. Corrected census: P2 18/11 july/fresh, PX 25/12, A0bS 5/4.
- USER RULING 2 (D9 revisit, promised by the prereg): risk-first STANDS
  on the corrected census -- collision_pairs shows EVERY prot+tgt bar
  (18+19+10+9) is the order-FORCED bank->floor arm-and-fire chain (zero
  already-armed collisions); genuinely order-sensitive bars (stop vs
  bf/brk/flip, i3 vs stop) are 3-6 per arm-window and the ruled order
  books the worse fill there by design. Dated in the prereg amendment.
- REPORT + LEDGER CORRECTED (871ca78): Finding 5 rewritten with the
  retraction named in place; C0 label removed from S0a (D12); the fresh
  S0a-vs-A0b comparison fixed to combined-vs-combined (+95.9 vs +76.5,
  ~+19pp -- the axis error is named in-text); matched values stated as
  sums WITH means; P1's per-trade claim scoped to this round's
  shared-trade set vs the D5 receipt on its own universe; S-family
  numbers refreshed.
- Prereg amendment 2026-08-16b (4631dbd, append-only, before code):
  D14 ruling, D9 semantics, P2 90%->100% no-bank correction,
  stop_src_ts, D13 31/33 correction, zero-duration treatment, declared
  gate expectations, and the dated risk-first revisit outcome.

### Context for next session

- TVB-26 review REQUESTED (range covers the census repair vs the prior
  reviewer's suggested reconstruction, the D14 implementation vs the
  ruling, the regeneration field-diff claims, and the corrected
  report/ledger numbers). Fold before new work.
- Month-end extension through Aug 31 under the same prereg (after the
  month completes, ~Sep 1). The F2 abort path is now supported, so the
  extension cannot crash on a degenerate episode.
- No new arm is TV-valid; mirroring per arm on demand with its own gate.
- The P2 per-trade underperformance remains the USER-OWNED design
  question; any refinement is a new a-priori variant.

### Files created/modified

- Modified: analysis/paper/engine.py (D9 rewrite, D14 post-entry check,
  stop_src_ts freeze), analysis/paper/patterns.py (Signal.stop_src_ts),
  analysis/paper/tier_b_exits.py (zero-duration guards, declared gate
  expectations, collision_pairs plumbing), tests/test_tvb25_exits.py
  (+4 tests + census asserts), tests/test_tier_b_exits.py (+4 tests),
  docs/experiments/tvb25_exit_round_prereg.md (amendment 2026-08-16b +
  revisit outcome), docs/experiments/tvb25_exit_round_report.md,
  docs/ARM_LEDGER.md, analysis/paper/tier_b_exits/ (17 regenerated
  artifact files), docs/reviews/REVIEW_REQUEST.md, docs/HANDOFF.md,
  .session_startup_prompt.md.
- New: docs/reviews/tvb25-codex-audit.md (the returned verbatim audit).
- Suite: 265 passed, 2 skipped (7 new tests); ruff clean; secret scan
  clean; pushed.

### Open

- [ ] Fold the TVB-26 external review when returned
      (docs/reviews/tvb26-codex-audit.md)
- [ ] Month-end fresh-window extension through 2026-08-31 24:00 UTC under
      the same prereg incl. 2026-08-16b (harvest -> pin -> rerun, ~Sep 1)
- [ ] P2 T1-retrace per-trade underperformance: user decides whether a
      refined a-priori variant enters a future round
- [ ] TV mirror per arm on demand + per-arm parity gates; package pine
      header "seed-exact" wording fix at the next TV sync
- [ ] Assessment owner decisions: kernel-vs-Pine charter question;
      1m/trade archiving start; spine CLAUDE.md project-map row (outside
      this repo)
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
> below) and write a verbatim assessment to docs/reviews/tvb26-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: REQUESTED
- Commits to review: `53599c4^..7f91c9c` on `main` (7 commits, 30 paths;
  RANGE-PIN RULE: the caret keeps 53599c4 in the diff; sanity-checked
  with `git diff --name-status`; the pin commit after 7f91c9c is
  docs-only routing, out of range).
- Scope / what changed: the TVB-25 audit fold -- reproductions, two user
  rulings (D14 entry-hour; risk-first stands), D9 census repair +
  collision_pairs, zero-duration episode support, declared gate
  expectations, stop_src_ts, canonical regeneration under amendment
  2026-08-16b, report/ledger corrections.
- Focus areas (scrutinize these): (1) reconstruct D9 independently from
  ordered per-bar eligibility (the prior reviewer's suggested check) and
  compare to the stored counters + collision_pairs; (2) the D14
  implementation vs the dated ruling -- post-entry check placement,
  i3-before-state order, boundary behavior, and the mid-hour-consistency
  claim used to justify the recommendation; (3) the regeneration
  field-diff claims (byte-identity of untouched streams, additive-only
  stop_src_ts, matched receipts unchanged); (4) the declared gate
  expectation -- mutate at the caller boundary (remove a produced arm,
  canonical and smoke) and check the modulo rule stayed exact-scope;
  (5) zero-duration episodes: P&L retained, MFE/MAE excluded, both
  runner paths; (6) recompute the corrected report/ledger numbers
  (S-family, matched sums AND means, the ~+19pp fresh gap, the scoped
  P1 claim); (7) amendment 2026-08-16b language: dated, append-only, no
  silent rewrites above it; (8) request.security: NO pine file changed
  -- verify none did.
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb26-codex-audit.md exists)

---

## Session TVB-25: audit folded + exit round built, run, reported (COMPLETE)

**Date:** 2026-08-16
**Status:** COMPLETE -- TVB-24 audit folded (F3-F6 fixed same session with
27 adversarial tests; F1/F2 became a user-ruled prereg amendment via live
walkthrough), then the exit round executed end to end per the amended
prereg: fresh harvest, engine extensions, runner, both windows, all gates
PASS, report + ARM_LEDGER. Ten commits pushed.

### What was accomplished

- TVB-24 AUDIT FOLDED (b31c11d; critical synthesis in the TVB-24 entry's
  External Review block below): every false-PASS path reproduced BEFORE
  adjudication. F3 entry-stream/census gates hardened (both-sides-exit
  divergence; _entry_stream_gate with exact arm set + stream-vs-rec
  reconciliation -- deviation-with-justification: the audit's roster-init
  sketch cannot catch its own mutation because AAPL/AMZN/GOLD are
  legitimate zero-event chop-veto shut-outs; census direction-consistency
  + injective one-outcome-per-entry). F4 canonical parity artifact
  protected (only the exact 3x3 writes it; wrapper metadata inside the
  PASS predicate; harvester arm read-back + strategy_count=1). F5 matched
  identity binds frozen entry state (price/ladder/boom/pmg/rev/star;
  tgt_rung excluded -- the only arm-dependent field across 942 shared
  identities). F6 receipts regenerated ADDITIVELY with provenance hashes
  (field-diff proof: all numbers byte-identical); pkg_parity seed wording
  narrowed; the pine header wording deferred to the next TV sync.
- PREREG AMENDED (2411821, committed before any code; user-ruled in three
  AskUserQuestion rounds): S0c state+BF arm restores the F1 BF isolation,
  A0b relabeled exit-family reference; deterministic exit state machine --
  risk-first pessimistic same-bar race (PROVISIONAL, D9 collision census
  makes its bite observable), two fill classes (protective = D3
  gap-through-at-open; profit = containment-only), P2 short-ladder
  fold-to-runner + same-bar arm-and-fire, i3 = prior-1H opposite extreme
  frozen at entry + entry-hour-only, X1 arming cases, immutable
  Signal.stop_anchor with strict-loss-side degeneracy -> ATR fallback;
  D9-D14 bundle; P2 runner post-retrace = reading A (BF target +
  breakeven floor).
- ROUND EXECUTED per the prereg's binding order: (2) fresh harvest +
  D13 pin Aug 3 -> Aug 16 00:00 UTC (047d695; merge-integrity verified --
  zero July-window rows changed, only the three 2026-08-04 forming-bar
  rows completed); (3) engine extensions behind inert defaults (007208e;
  20 fixtures; 55/55 committed Tier B rows field-equal through the
  extended engine); (4) runner tier_b_exits.py (209d2ef) with two
  gate-caught corrections committed BEFORE the clean rerun (5796da2
  veto-counter modulo rule; 7f3626e partially-banked open entries
  contribute no stream exit); (5) canonical run 62ff310 -- determinism
  55+88 rows field-equal, entry-stream gates PASS both families both
  windows, tranche reconciliation clean; report 40c94ce.
- FINDINGS (gross, contrasts only, no promotion -- full text in
  docs/experiments/tvb25_exit_round_report.md): (1) the bare state stop
  transforms the control through OCCUPANCY, not per-trade exit quality
  (S0a +194.8 July vs A0b +104.8 whole-arm; loses matched 27.4-vs-34.2;
  866 vs 172 trades); (2) the BF layer over the state base = +96.2pp
  (S0c +291.1) but worst-in-family per matched trade -- book
  composition; (3) the ATR stop (A0bS +214.9, dd 55-vs-122) is the FIRST
  overlay winning whole-arm AND matched axes -- it amputates the
  adverse-runner class; (4) every thesis exit loses to plain D1 on July
  (P1 +32.5 but WINS matched 18.5-vs-8.4; P2 +6.1 loses both axes -- the
  T1-retrace dump is the suspect; X1 -37.8/dd 119 = the stall-mode cost
  of extension-only protection; D1S -33.6 vs A0bS +110: STOP VALUE IS
  BOOK-DEPENDENT); (5) D9 collisions near zero -- the ruled convention
  does not distort (user's caveat answered). Fresh window: 13 committed
  arms directionally stable, A1F the lone near-zero negative.
- ARM_LEDGER (b38e0ad + refinement; USER REQUEST, standing): every arm in
  plain trading terms + numbers + What-Claude-notices; binding CLAUDE.md
  Reporting rule -- ledger updated every round, design-session arm
  restatements user-confirmed before prereg, AskUserQuestion options in
  trader language (or dual). User clarified their 50/30/10 phrasing was a
  hypothetical example, not a mis-recall (record corrected).

### Context for next session

- TVB-25 review REQUESTED (range covers amendment coherence, the engine
  race vs the amendment, runner gates incl. the final-exit stream
  convention, the two forward-protocol corrections, report claims vs
  artifacts). Fold before new work.
- Month-end extension through Aug 31 under the same prereg (after the
  month completes).
- No new arm is TV-valid; mirroring per arm on demand with its own gate.
- The P2 per-trade underperformance is a USER-OWNED design question; any
  refinement is a new a-priori variant.

### Files created/modified

- New: analysis/paper/tier_b_exits.py + analysis/paper/tier_b_exits/ (40
  artifacts: events x 33 arm-windows, results, matched-entry receipts,
  manifest), tests/test_tvb25_exits.py (20), tests/test_tier_b_exits.py
  (6), docs/experiments/tvb25_exit_round_report.md, docs/ARM_LEDGER.md,
  docs/reviews/tvb24-codex-audit.md.
- Modified: analysis/paper/{engine,patterns}.py (TVB-25 features, inert
  defaults), analysis/paper/{tier_b_t1floor,round_census,pkg_parity,
  t1floor_diagnostics,entry_audit}.py (audit fold), the three t1floor
  receipts (additive provenance), scripts/tvb23_pkg_harvest.mjs
  (read-back), tests/test_{t1floor_gates,pkg_parity,t1floor_diagnostics}.py,
  docs/experiments/tvb25_exit_round_prereg.md (amendment + pins),
  analysis/paper/bars/ (33 files, fresh harvest), CLAUDE.md (ledger
  rule), HANDOFF + REVIEW_REQUEST + .session_startup_prompt.md.
- Suite: 258 passed, 2 skipped (53 new tests); ruff clean.

### Open

- [x] Fold the TVB-25 external review when returned
      (docs/reviews/tvb25-codex-audit.md) -- DONE TVB-26 2026-08-16
      (all seven findings folded; two user rulings; canonical rerun)
- [ ] Month-end fresh-window extension through 2026-08-31 24:00 UTC under
      the same prereg (harvest -> pin -> rerun)
- [ ] P2 T1-retrace per-trade underperformance: user decides whether a
      refined a-priori variant enters a future round
- [ ] TV mirror per arm on demand + per-arm parity gates; package pine
      header "seed-exact" wording fix at the next TV sync
- [ ] Assessment owner decisions: kernel-vs-Pine charter question;
      1m/trade archiving start; spine CLAUDE.md project-map row (outside
      this repo)
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
> below) and write a verbatim assessment to docs/reviews/tvb25-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED (2026-08-16, docs/reviews/tvb25-codex-audit.md;
  verdict NEEDS-CHANGES, 1 HIGH + 4 MEDIUM + 2 LOW) -- FOLDED by TVB-26
  same day, critical synthesis below.
- CRITICAL SYNTHESIS (TVB-26, 2026-08-16): the audit is accepted IN FULL
  -- all seven findings reproduced in-repo before adjudication, zero
  disputes. The reviewer had independently replayed the entire
  evidentiary base first (55+88 inert-default rows, rollups, receipts,
  hashes, fees, tranche fractions), so the findings attack the
  DIAGNOSTIC/CONTRACT layer, not the P&L: that framing held up exactly.
  - F1 (HIGH, D9 census) reproduced WORSE than the audit's lower bounds
    (executed multi-class bars all-symbols: P2 July 21, PX 24; the
    audit's 14/16 were roster-scoped -- scope note, not a dispute).
    Root cause confirmed at engine bar-start snapshot vs the target
    loop's mid-bar floor arming. Repaired to transition-accumulated
    satisfiability + a collision_pairs decomposition; the arm-and-fire
    fixture now asserts the counter. Corrected census: P2 18/11
    july/fresh, PX 25/12 -- and the decomposition shows every prot+tgt
    bar is the order-FORCED bank->floor chain (zero already-armed
    collisions); order-sensitive bars are 3-6 per arm-window. USER
    RULING on the corrected census: risk-first STANDS (prereg dated
    note). The retracted "max 6 / no revisit" Finding 5 is rewritten
    in place with the retraction named.
  - F3 (D14 entry-hour) reproduced exactly (14/14/15 July; the audit's
    fresh 6 = roster scope of our 8). Key fact surfaced during the fold:
    mid-hour entries ALREADY counted pre-entry same-hour breaks, so only
    the literal-inclusive reading closes the gap without rewriting
    committed behavior. USER RULING: literal-inclusive -- the entry hour
    counts; engine post-entry check + state_degenerate counter +
    long/short/one-tick boundary tests.
  - F2/F4/F6/F7 all confirmed by inspection or replay and fixed:
    zero-duration episodes guarded on both runner episode paths +
    end-to-end regression; gate expectation is now DECLARED (full family
    canonical, requested+anchors smoke) with a caller-boundary mutation
    test + the modulo rule pinned exact-scope; prereg corrected 90%->100%
    no-bank runner + stop_src_ts absolute source timestamp implemented
    (frozen, drift-asserted, on entry events); D13 note corrected to
    31/33 files at two timestamps (git-verified).
  - F5 (report/ledger axes) verified to the decimal (A0b fresh combined
    +76.4784 vs the quoted realized +55.7; matched means +0.71 vs +0.32)
    and corrected: sums labeled as sums with means beside them, the P1
    best-per-trade claim scoped against the D5 receipt's +1.79/trade on
    its own universe, the C0 label removed per D12.
  - Canonical artifacts REGENERATED under amendment 2026-08-16b with a
    field-diff receipt: every non-S0 non-stop event stream byte-identical;
    D1S/PX additive stop_src_ts only; S0 arms changed by exactly the
    ruled D14 scratches (July S0a +194.8 -> +195.3, 866 -> 877 trades);
    matched-entry receipts unchanged to the fourth decimal. No research
    conclusion flipped; the round's contrast readings all survive with
    corrected instruments.
- Commits to review: `b31c11d^..6597a68` on `main` (11 commits, 98 paths;
  RANGE-PIN RULE: the caret keeps b31c11d in the diff; sanity-checked
  with `git diff --name-status`; the pin commit after 6597a68 is
  docs-only routing, out of range).
- Scope / what changed: TVB-24 audit fold (F3-F6 code + tests, receipts
  additive-regenerated); the user-ruled prereg amendment; fresh harvest +
  D13 pin; engine TVB-25 exit features behind inert defaults; runner +
  two forward-protocol gate corrections; canonical run artifacts; report;
  ARM_LEDGER + CLAUDE.md practice rule.
- Focus areas (scrutinize these): (1) amendment vs rulings coherence and
  whether an independent implementer can now derive one event stream;
  (2) engine race vs the amendment (order, two fill classes, i3
  level/scope/degenerate, stop freeze + degeneracy, P2 fold/arm-and-fire/
  reading-A breakeven, X1 arming, D14 inclusive state stop) and the
  inert-defaults claim (55/88-row field equality); (3) runner gates: the
  final-exit stream convention for tranche arms, family anchors (A0b
  in-memory, committed D1), tranche reconciliation, the modulo-rule fix;
  (4) report + ledger claims vs committed artifacts (esp. matched-entry
  numbers and every occupancy reading); (5) D10 fee math; (6) harvest
  merge integrity (the three completed forming bars); (7) request.security:
  no pine changes this session -- verify none slipped in.
- Reviewed by: OpenAI Codex CLI (GPT-5), returned 2026-08-16
- Findings: 1 HIGH (D9 census undercount -- P2/PX arm-and-fire bars
  invisible to the bar-start snapshot) + 4 MEDIUM (i3-degenerate runner
  abort; D14 entry-hour ordering unruled; gate wrapper defeated the
  exact-arm-set check; report/ledger axis + units errors) + 2 LOW (P2
  90%-vs-100% prose + missing stop-source record; D13 merge-note count).
  All folded same day by TVB-26 -- see the synthesis above.

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

- Review status: RETURNED (2026-08-16, docs/reviews/tvb24-codex-audit.md;
  NEEDS-CHANGES -- critical synthesis to be written by TVB-25)
- Commits to review: `674c7f6^..e92e59c` on `main` (6 commits incl. the TVB-25 prereg e92e59c: 674c7f6
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
- Reviewed by: OpenAI Codex (GPT-5), returned 2026-08-15/16
- Findings: NEEDS-CHANGES -- 1 HIGH + 4 MEDIUM + 1 LOW. CRITICAL SYNTHESIS
  (written by TVB-25, 2026-08-16; every finding reproduced BEFORE
  adjudication):
  - The committed TVB-24 evidence is NOT disputed: the reviewer
    independently re-ran the 9-cell parity gate (9/9, same 218 events) and
    recomputed all five diagnostic receipts to the published values. The
    verdict targets forward-looking contracts (the TVB-25 prereg and the
    residual gate false-PASS paths), not the results.
  - F3/F4/F5/F6 AGREED and FIXED by TVB-25 same session, all false-PASS
    paths reproduced first: (F3) exit-vs-entry first divergence, one
    symbol deleted from ALL six arms, a whole arm missing, and a census
    direction flip all passed the old gates -- hardened with a
    both-sides-exit divergence rule, an extracted _entry_stream_gate
    (exact arm set + stream-vs-rec reconciliation + roster scope), and
    census direction-consistency + injective one-outcome-per-entry
    linkage. DEVIATION with justification: the audit's roster-initialized
    stream-map sketch would NOT catch its own mutation -- three roster
    symbols (AAPL/AMZN/GOLD) are legitimately zero-event chop-veto
    shut-outs, so empty-vs-empty streams still compare equal; anchoring
    each arm's stream against its own per-symbol replay rows
    (n_trades/open_dir) does catch it. (F4) a 1-cell smoke run reproduced
    targeting the canonical artifact; now only the exact 3x3 writes
    {gen}_parity_result.json (subsets write scope-named smoke files),
    wrapper metadata is validated inside compare(), and the harvester
    reads the arm input back and rejects strategy_count != 1. (F5) the 41
    all-six identities verified equal on entry price + ladder (the
    committed exits-in-isolation read is supported by the data); the
    matched contract now binds frozen entry state
    (price/ladder/boom/pmg/rev/star), with tgt_rung excluded by declared
    reason (per-arm target config -- the ONLY differing field across the
    942 shared identities); duplicates fail closed. (F6) the three
    receipts regenerated ADDITIVELY with provenance hashes
    (bars/roster/minticks/executed code) -- field diff proves every
    numerical field byte-identical, only provenance/matched_entry_state/
    timestamps/conventions added or changed; the pkg_parity ATR comment
    narrowed to observed-decision-parity language. The package pine's
    header wording (seed-exact, ~line 164) is DEFERRED to the next TV
    sync so a comment edit does not drift the sha-verified mirror.
    27 new adversarial regression tests; suite 232 passed / 2 skipped.
  - F1 (HIGH) + F2 (MEDIUM) target the TVB-25 prereg and are USER-RULING
    territory. Factual basis CONFIRMED: A0b's twin override is arm
    cadence only -- it inherits BF harvest + brk + flip and TwinConfig
    has no state-stop field, so S0a/S0b-vs-A0b is an exit-FAMILY
    replacement, not a BF isolation; and the exit state machine's
    same-bar collision precedence, P2 short-ladder/gap cases, X1 arming
    snapshot, intrabar-3 level freeze, stop_anchor immutability, and
    partial-position fee formula are genuinely underdetermined. Both go
    to a design session before any TVB-25 code (dated prereg amendment).
  - Shading, not dispute: the audit reads S0a's 2-against state stop as
    a charter-3.5 naming mismatch; that form was the user's explicit
    design-session ruling, so the fix is labeling it as the ruled
    variant, not correcting an error.

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
