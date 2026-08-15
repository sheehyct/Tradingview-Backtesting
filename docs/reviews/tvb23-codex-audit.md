<!--
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-23 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of `0023852^..9099bad` on `main`, captured 2026-08-12
> (TVB-23 post-session). Lightly ASCII-normalized (em-dashes -> --, curly quotes -> straight);
> wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-23 -- TVB-22 audit fold-in and T1-floor round
- **Reviewed:** `0023852^..9099bad` on `main` (6 commits, 37 paths)
- **Reviewer:** OpenAI Codex (GPT-5)
- **Overall verdict:** NEEDS-CHANGES

## 2. Verbatim audit

### Verdict

NEEDS-CHANGES. The current numerical artifacts are substantially stronger than the verdict may
suggest. I independently replayed all five Tier B determinism arms and all eight TVB-23 arms in
memory from the committed bars. The 55 comparator rows match modulo only the four declared
zero-valued floor-counter keys; all 88 new rows, eight rollups, and eight event dumps match exactly.
All 33 bar hashes and four executed-source hashes match the manifest. A stronger all-pairs audit of
the committed depth streams found every observed first divergence was an exit, and the reported
137/108/93/89/85/50 funnel reproduces. The floor, ATR, retracement, parity-hardening, and census
mechanics also reproduce.

The executable safeguards do not, however, satisfy their advertised fail-closed contracts. Missing
rows, missing fields, missing open marks, whole missing streams, and untested non-reference arm
pairs can false-PASS. The round also omits two binding diagnostics, overstates what its read-only
retracement census establishes, and cannot substantiate the claimed pre-code/pre-results ordering
for two of its three preregistration corrections. Those are evidence-contract defects even though a
stronger independent reconstruction supports the committed run itself.

### Findings

#### 1. MEDIUM -- The advertised fail-closed gates accept missing evidence

- **Severity:** MEDIUM
- **Location:** `analysis/paper/tier_b_t1floor.py:384-411,423-431,544-551`;
  `analysis/paper/round_census.py:137-149`
- **Status:** CONFIRMED

The Tier B determinism comparison iterates only the rows and fields produced by the new replay. It
never asserts that the produced key set equals the 55 committed keys, and it never checks committed
fields that are absent from a produced row. Adversarially, `_determinism_check([])` returns 55
committed rows, zero compared rows, and no mismatches. Removing `sum_pnl_pp` from one otherwise
real committed row also returns no mismatches. This is not field equality modulo zero-valued new
keys (`analysis/paper/tier_b_t1floor.py:384-411`).

The entry-stream helper returns true whenever either stream is a prefix, without requiring the next
event in the longer stream to be an exit. An empty/missing stream therefore passes against a stream
whose first event is an entry. The caller also compares only D1 against each other arm and iterates
only symbols present in D1; it does not compare all 15 depth-arm pairs or assert equal symbol key
sets (`analysis/paper/tier_b_t1floor.py:423-431,544-551`). A constructed D1 reference can pass
against D2 and D3 while D2 versus D3 first-diverges on two different entries.

The census guard is weaker again: it compares only per-symbol closed-trade counts. Deleting all
three D2 `open_mark` events changes its receipt from 85 rows with three open trades to 82 rows with
none, yet `_determinism()` still reports no mismatch (`analysis/paper/round_census.py:137-149`).

These weaknesses did not corrupt the committed TVB-23 package: independent bidirectional row
comparison, event linkage, all-pairs stream comparison, and receipt regeneration all passed. They
do make the manifest/report claim that every guard is fail-closed materially false and leave the
next regression able to certify incomplete evidence.

#### 2. MEDIUM -- Two binding diagnostics are absent, and the retracement prose outruns the receipt

- **Severity:** MEDIUM
- **Location:** `docs/experiments/tvb23_t1floor_prereg.md:228-243`;
  `analysis/paper/tier_b_t1floor.py:505-535,575-585`;
  `docs/experiments/tvb23_t1floor_report.md:46-65,133-139`
- **Status:** CONFIRMED

The preregistration requires per-symbol ATR as a percentage of price alongside the veto-suppression
comparison, and a matched-entry/shared-prefix per-trade exit comparison as the exits-in-isolation
diagnostic (`docs/experiments/tvb23_t1floor_prereg.md:228-243`). Neither exists in the runner,
manifest, rows, event dumps, census receipts, report, or receipt index. The runner retains only the
whole-arm entry counts and first-divergence gate (`analysis/paper/tier_b_t1floor.py:505-535,575-585`).

The missing matched-entry diagnostic matters because the report then moves from a descriptive label
census to the counterfactual claim that a POTENTIAL-3 exit "would fire far too early" and "would
have cut winners before their first rung" (`docs/experiments/tvb23_t1floor_report.md:55-65`). The
census deliberately excludes the label bar when counting prior rungs
(`analysis/paper/round_census.py:70-79`), so it cannot resolve whether a rung and label occurred in
which order inside that 5-minute bar. It also records no alternative exit price or P&L. The later
statement that the census "does not decide" the exit is the defensible boundary
(`docs/experiments/tvb23_t1floor_report.md:122-131`).

Commit the two promised diagnostics and either run an explicitly preregistered exit variant or
soften the counterfactual to the supported observation: labels are frequent and often appear before
any progress recorded on an earlier 5-minute bar.

#### 3. MEDIUM -- Only one of the three claimed correction orderings is Git-verifiable

- **Severity:** MEDIUM
- **Location:** `docs/experiments/tvb23_t1floor_prereg.md:59-76,88-95,170-177`;
  `analysis/paper/tier_b_t1floor/manifest.json:2-16`
- **Status:** CONFIRMED

The outside-bar correction is a distinct commit (`2fcd13b`) before the engine commit. The other two
do not have that evidence. The counter-equation correction and the engine implementation share
`8c5c126`; the occupancy/entry-stream correction shares `8967a07` with the new runner, all result
artifacts, all census receipts, and the report. The latter correction also embeds observed funnel
counts (`docs/experiments/tvb23_t1floor_prereg.md:59-76`).

The run manifest proves only that the preregistration path was dirty at run time. It hashes the
runner, Tier B runner, engine, and patterns, but not the dirty preregistration content
(`analysis/paper/tier_b_t1floor/manifest.json:2-16`). It therefore cannot establish which correction
text existed at run start or that results had not been inspected before the correction. The
chronology may be true, but it is self-attested rather than independently reproducible from the
committed evidence.

For this round, downgrade the chronology wording to that limit instead of calling all three
corrections verified pre-code/pre-results. For future gate-triggered corrections, commit the
correction before the clean rerun and record the preregistration blob hash in the run manifest.

#### 4. LOW -- Binding documentation still states the superseded entry-book contract

- **Severity:** LOW
- **Location:** `docs/experiments/tvb23_t1floor_prereg.md:59-76,108-135`;
  `analysis/paper/tier_b_t1floor.py:1-27`
- **Status:** CONFIRMED

The dated correction correctly says realized entry books differ through one-position occupancy and
changes the gate to first-divergence-is-exit. Later binding text still says DINF "holds entries
fixed," that D1 through DINF "share ONE entry book exactly," and that the curve varies only exit
depth (`docs/experiments/tvb23_t1floor_prereg.md:123-135`). The runner docstring repeats the old
identical-entry-stream gate (`analysis/paper/tier_b_t1floor.py:23-27`). The preregistration heading
also says "9 new" arms although its table and runner define eight
(`docs/experiments/tvb23_t1floor_prereg.md:108-121`). The executable gate and report use the corrected
interpretation, so this is documentation debt rather than a result defect.

#### 5. LOW -- Realized P&L is not monotone from D1 through D5

- **Severity:** LOW
- **Location:** `docs/experiments/tvb23_t1floor_report.md:36-45`;
  `analysis/paper/tier_b_t1floor/results_rollup.jsonl:1-5`
- **Status:** CONFIRMED

The report says realized P&L rises monotonically with depth from 83.8pp at D1 to 104.0pp at D5.
The committed rollups are D1 83.8153, D2 82.0468, D3 89.8239, D4 98.5428, and D5 103.9727pp.
There is a 1.7685pp dip at D2 before the D3-D5 rise. The report's larger conclusion that combined
P&L is non-monotone remains correct; fix this one mechanism sentence.

### Confirmed checks that are not findings

- **Range and snapshot:** The pinned range contains six commits and 37 changed paths; `git
  diff --check 0023852^..9099bad` passes. Current HEAD is one later routing-doc commit; no reviewed
  implementation or result artifact changed after `9099bad`.
- **TVB-22 audit F1 fold-in:** Event validation now requires non-empty pattern names and finite
  numeric triggers on both sides, and the comparison independently rejects a non-finite twin
  trigger (`analysis/paper/pkg_parity.py:121-146,253-264`). The 12 focused tests include the real
  GOOGL/A1 delete-trigger reproduction (`tests/test_pkg_parity.py:59-145`). In-memory comparison of
  all nine committed cells returns 487 matched events, 246 checked entries, and 9/9 PASS. The
  committed parity result was not regenerated in this range.
- **TVB-22 audit F2 receipt:** Replaying A1 regenerates the committed per-trade rows and aggregates:
  137 closed / 146 including open, reach 65.0% at two or more rungs, 37.2% at four or more, 39.4%
  stalled at one or two, and BF means 3.407 / 3.6173 excluding zero. Roster scope excludes
  `xyz:DRAM`; entry bars are excluded and exit bars included
  (`analysis/paper/ladder_census.py:67-86,114-143,174-208`).
- **Floor mechanics:** The engine uses prospective fill, directional distance to frozen ladder[0],
  strict `d < floor`, the `d <= 0` versus `0 < d < floor` split, the marginal-only counter, and the
  uniform empty-ladder skip under C1 exits (`analysis/paper/engine.py:632-720`). Every committed
  arm/symbol counter equation reconciles.
- **ATR mechanics:** `_Atr` uses first-bar `h-l`, the first-window SMA seed, Wilder recursion, and
  only completed signal-timeframe bars. Proximity and chop predicates use price-unit ATR distances;
  the existing percentage arithmetic is unchanged (`analysis/paper/engine.py:343-393,650-684`).
- **Retracement implementation:** `health_flags()` mirrors the one-sided Pine flags and live color;
  the census reads the bar-start position before the exit step, so entry bars are excluded and exit
  bars included. With the flag off, the old event shape is unchanged
  (`analysis/paper/patterns.py:157-180`; `analysis/paper/engine.py:739-781`).
- **Round artifacts:** In-memory replay regenerates all 88 new symbol rows, all eight rollups, and
  all eight event dumps exactly. The eight census receipts also regenerate exactly apart from their
  timestamps. A stronger all-pairs audit found no non-exit first divergence in the committed depth
  streams, and the manifest funnel reproduces exactly
  (`analysis/paper/tier_b_t1floor/manifest.json:176-209`).
- **Research discipline:** The report labels the window gross and in-sample, calls the depth sweep a
  ceiling-map, flags the constructed win rates, and makes no arm/depth/setup promotion or fee/live
  claim (`docs/experiments/tvb23_t1floor_report.md:3-8,66-71,122-131`).
- **Pine/lookahead:** The only Pine change is the package header comment that records the passed
  TVB-22 artifact and keeps the realtime exclusion. No executable Pine or `request.security` call
  changed in the range (`pine/tfc_mt_package_strategy.pine:92-121`).
- **Validation:** The focused TVB-23 tests passed `37 passed`; the full suite passed `181 passed, 2
  skipped` under `python -B` with the pytest cache disabled. Ruff passed for `analysis/` and `tests/`.

### Validation limits

- I did not launch TradingView, recompile either Pine script, inspect the mounted chart, or repeat
  the claimed TV-side byte comparison. The Pine edit is locally comment-only; live editor state
  remains session evidence.
- I did not overwrite or regenerate committed artifacts. Replays, parity comparisons, census
  reconstruction, hash verification, and adversarial guard checks ran in memory against the pinned
  sources and committed bars.
- This remains one roughly four-week, gross, in-sample window. None of the successful arithmetic or
  deterministic reconstruction supplies fresh-window, fee, funding, slippage, or realtime-cadence
  evidence.

## 3. Actionable items (reviewer's own list)

1. Make all three guard families genuinely fail-closed -- **MEDIUM** --
   `analysis/paper/tier_b_t1floor.py:384-411,423-431,544-551`;
   `analysis/paper/round_census.py:137-149` -- assert exact row/field/symbol cardinality, compare all
   depth-arm pairs, require a prefix's next event to be an exit, validate open state and event
   identity, and add missing-row/field/stream/open-mark adversarial tests.
2. Deliver the two binding diagnostics and narrow the retracement conclusion -- **MEDIUM** --
   `docs/experiments/tvb23_t1floor_prereg.md:228-243`;
   `docs/experiments/tvb23_t1floor_report.md:46-65` -- commit per-symbol ATR-percent context and the
   matched-entry/shared-prefix exit comparison; do not infer alternative-exit P&L or intrabar order
   from the label-exclusive census.
3. Correct the correction-provenance claim -- **MEDIUM** --
   `docs/experiments/tvb23_t1floor_prereg.md:59-76,170-177`;
   `analysis/paper/tier_b_t1floor/manifest.json:2-16` -- label the two same-commit orderings
   self-attested for TVB-23; in future, commit each correction before its rerun and hash the binding
   preregistration in the manifest.
4. Reconcile the superseded contract text and arm count -- **LOW** --
   `docs/experiments/tvb23_t1floor_prereg.md:108-135`;
   `analysis/paper/tier_b_t1floor.py:1-27` -- remove identical-entry-book language, describe the
   occupancy-aware pairwise gate consistently, and change nine new arms to eight.
5. Fix the realized-P&L sentence -- **LOW** --
   `docs/experiments/tvb23_t1floor_report.md:36-45` -- state that realized P&L dips at D2 and then
   rises from D3 through D5.

## Suggested prompt

Before accepting TVB-23, adversarially remove one comparator row, one comparator field, one depth
stream, and every open_mark from one census arm; every mutation must fail. Compare all 15 depth-arm
pairs with exact symbol sets and prefix handling. Then produce the preregistered per-symbol ATR%
context and matched-entry exit diagnostic, and separate descriptive label timing from an unrun exit
counterfactual.

Verdict: NEEDS-CHANGES
