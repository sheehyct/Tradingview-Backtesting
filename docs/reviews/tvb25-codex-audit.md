<!--
External review of TVB-25. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-25 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of `b31c11d^..6597a68` on `main`, captured 2026-08-16
> (TVB-25 post-session). Lightly ASCII-normalized (em-dashes -> --, curly quotes -> straight);
> wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-25 -- TVB-24 audit fold and preregistered exit round
- **Reviewed:** commit range `b31c11d^..6597a68` on `main` (11 commits, 98 paths)
- **Reviewer:** OpenAI Codex CLI (GPT-5)
- **Overall verdict:** NEEDS-CHANGES

## 2. Verbatim audit

### Verdict

NEEDS-CHANGES.

The round has unusually strong provenance for a research run. The dated amendment was committed
before engine work; the harvest and D13 pin preceded the runner; both runner corrections preceded
the canonical run; the manifest binds the prereg, executed Python blobs, 33 bar files, and the
pre-run git head; all ten new arms are present in both windows; and I reproduced 55 Tier B plus 88
T1-floor incumbent rows field-equal through the extended engine. The committed rollups, matched
receipts, D10 fees, and tranche fractions also reconcile independently. No Pine file changed.

That evidence does not support approval because the declared D9 decision instrument omits the
specific P2 same-bar transitions it says it counts. The resulting report and ledger conclude that
the provisional collision convention is negligible from materially understated values. I also
found an unexecutable declared i3 edge path, an unresolved D14 entry-hour ordering case that occurs
in both committed windows, and a wrapper that reopens the missing-arm false-PASS fixed in the
underlying gate. These are contract and research-validity defects, not cosmetic nits.

### Findings

#### 1. HIGH -- D9 omits P2/PX same-bar arm-and-fire collisions, invalidating Finding 5

**Location:** `docs/experiments/tvb25_exit_round_prereg.md:271-274`,
`docs/experiments/tvb25_exit_round_prereg.md:302-307`, `analysis/paper/engine.py:868-906`,
`analysis/paper/engine.py:935-973`, `tests/test_tvb25_exits.py:259-275`,
`analysis/paper/tier_b_exits/events_july_P2.jsonl:94-95`,
`analysis/paper/tier_b_exits/results_rollup_july.jsonl:6`,
`docs/experiments/tvb25_exit_round_report.md:140-147`, `docs/ARM_LEDGER.md:64-69`.

The amendment is explicit that a bar containing both the first P2 bank and the T1 retrace arms and
fires on that bar, and that D9 counts those bars. The engine instead snapshots all satisfiable
classes at bar start. At that point `floor_armed` is false, so `prot_hit` is false and D9 is already
finished. Only afterward does the target loop set `newly_armed`, execute the target, and execute the
new floor and possible runner breakeven. The dedicated unit test verifies the five resulting exit
events but never asserts `collision_bars`.

This is visible in the committed evidence, not merely a synthetic possibility. GOOGL P2 has a T2
target and a T3 floor at the same timestamp, while the July P2 rollup reports zero collisions. I
grouped committed exit events by roster symbol and timestamp and found a lower bound of 14 such
arm-and-fire bars for P2 July, 16 for PX July, 8 for P2 fresh, and 7 for PX fresh. These are lower
bounds because they count observable multi-class executions, not a full counterfactual
satisfiability census. P2 July has only 55 entries, so this is not a negligible edge case. The
report's claimed maximum of six and its "no revisit" conclusion are false; the ledger repeats both.

This finding does not by itself show that the emitted P&L event stream is wrong: the bank/floor/BE
events follow the implemented amendment order. It shows that the preregistered diagnostic used to
adjudicate that provisional order is wrong. D9 must accumulate eligible classes across the ordered
within-bar state transitions, count each bar once, and gain a regression assertion on the existing
arm-and-fire fixture. Then the canonical artifacts, report, and ledger must be regenerated, and the
user must revisit the convention using the corrected census as promised by the prereg.

#### 2. MEDIUM -- The declared i3 degenerate path aborts the runner if it ever occurs

**Location:** `docs/experiments/tvb25_exit_round_prereg.md:275-281`,
`analysis/paper/engine.py:678-699`, `tests/test_tvb25_exits.py:147-154`,
`analysis/paper/tier_b_exits.py:248-261`, `analysis/giveback.py:43-50`,
`analysis/paper/tier_b_exits/results_rollup_july.jsonl:8`,
`analysis/paper/tier_b_exits/results_rollup_fresh.jsonl:21`.

The amendment declares that an entry 5-minute bar which itself completes Type 3 exits at that same
bar's close. The engine implements exactly that and its unit test requires an enter and exit with the
same timestamp. The round runner then sends every closed episode to `episode_metrics`, which raises
when `exit_time <= entry_time`. A direct end-to-end call through those contracts therefore fails on
the very same-timestamp event the engine declares valid.

Both canonical windows happened to report `i3_degenerate: 0`, so this did not change TVB-25's
numbers. It is nevertheless a latent fail-closed abort in the month-end extension, not a supported
mechanic. Define the metric treatment for a zero-duration episode (or explicitly exclude it from
MFE/MAE while retaining P&L and a counted reason), add a runner-level regression using the existing
engine fixture, and rerun if the repaired path appears in the extended window.

#### 3. MEDIUM -- D14 has an undocumented entry-hour exception on actual sample events

**Location:** `docs/experiments/tvb25_exit_round_prereg.md:47-50`,
`docs/experiments/tvb25_exit_round_prereg.md:321-324`, `analysis/paper/engine.py:621-699`,
`analysis/paper/engine.py:898-903`, `analysis/paper/engine.py:995-997`,
`tests/test_tvb25_exits.py:96-121`,
`analysis/paper/tier_b_exits/events_july_S0a.jsonl:31-32`.

D14 says any completed hour whose range breaks the prior opposite extreme against the position
triggers the state stop at that hour's close, including a Type-3 hour. The engine evaluates the
entire TVB-25 exit race before entry. It has a post-entry degenerate check for i3, but no analogous
post-entry state check. Thus a flat book can enter on the hour-completing 5-minute bar even when that
completed hour also satisfies D14, and it carries the position forward.

This ordering occurs in the archived data. Joining non-parity S0 entry events to the 5-minute bars
found 14 S0a, 14 S0b, and 15 S0c July entries on an hour close whose completed range also broke the
prior opposite extreme; the fresh counts are 6 in each arm. The cited AAPL event is one example: it
enters on the completing bar and does not receive its state exit until a later hour.

There is a legitimate unresolved question about whether an opposite-extreme break that happened
before the entry within the same OHLC hour should count "against the position." The amendment does
not state an entry-hour exception or an intrahour ordering rule, so an independent implementer
cannot derive one exact stream here. Obtain a dated user ruling. If D14 is literal, run a post-entry
hour-close check and rerun the affected arms; if the stop begins only with the next completed hour,
state that exception explicitly and add a boundary test. Do not silently inherit exit-before-entry
ordering as the answer.

#### 4. MEDIUM -- The TVB-25 wrapper defeats the repaired gate's exact-arm-set check

**Location:** `analysis/paper/tier_b_exits.py:657-679`,
`analysis/paper/tier_b_t1floor.py:473-498`, `tests/test_tier_b_exits.py:20-29`,
`tests/test_tier_b_exits.py:57-79`, `analysis/paper/tier_b_exits/manifest.json:189-237`.

The hardened `_entry_stream_gate` correctly accepts a separately declared `expected_arms` set and
reports a missing arm. The TVB-25 caller reconstructs `present` from only the streams that were
produced or supplied as anchors, then passes `present` as `expected_arms`. A missing family arm is
therefore removed from the expectation before the exact-set check runs. The helper is fail-closed;
this wrapper is not.

The canonical manifest currently lists the complete five-arm control and seven-arm package
families in both windows, so this defect does not shrink the committed TVB-25 matrices. It does
reopen the exact false-PASS class that TVB-24 F3 was meant to close for future clean reruns. Pass the
declared `fam`, not `present`, and add a caller-level mutation test that removes one produced arm.
The partial-open final-exit correction has an adversarial regression test. In contrast, the runner
test module's docstring claims coverage of the determinism comparison, but it contains no targeted
test of the 5796da2 zero-key/modulo normalization path; add one before relying on that correction as
a standing gate.

#### 5. MEDIUM -- The report and standing ledger mix axes and overstate P1's rank

**Location:** `docs/experiments/tvb25_exit_round_report.md:37-47`,
`analysis/paper/tier_b_exits/results_rollup_fresh.jsonl:2`,
`analysis/paper/tier_b_exits/results_rollup_fresh.jsonl:14`,
`analysis/paper/tier_b_exits/matched_entry_july.json:81-104`,
`docs/ARM_LEDGER.md:111-118`, `docs/ARM_LEDGER.md:134-138`,
`analysis/paper/tier_b_t1floor/matched_exit_receipt.json:159-168`.

The fresh whole-arm comparison says S0a `+96.1` versus A0b `+55.7`. The first number is combined
P&L, but `+55.7` is A0b realized P&L; A0b combined P&L is `+76.4784`. The comparable occupancy gap
is therefore about `+19.6pp`, not `+40.4pp`. Elsewhere the report calls matched aggregate sums such
as P1 `+18.5` versus D1 `+8.4` "per-trade" values. Because matched cardinality is equal, the ranking
survives, but the actual means are `+0.7118pp` and `+0.3214pp` per trade.

The binding ledger then calls P1 "the best per-trade package exit measured so far." That is false
across the ledger's own measured history: the prior D5 matched receipt reports `+1.7897pp` mean per
trade, and the ledger itself says deeper D2-D5 targets earn more per matched trade. P1 is best only
within a much narrower comparison, such as the two new partial profiles, and even that boundary
must retain its survivor-set warning. Correct the axis, units, and comparator universe. Also avoid
calling S0a the charter's never-run C0 rung (`docs/experiments/tvb25_exit_round_report.md:27-33`):
the amendment expressly retired C0-pure and mechanized the narrower user-ruled 2-against stop
(`docs/experiments/tvb25_exit_round_prereg.md:227-233`).

#### 6. LOW -- Two amendment details are not represented exactly by the implementation record

**Location:** `docs/experiments/tvb25_exit_round_prereg.md:265-270`,
`docs/experiments/tvb25_exit_round_prereg.md:289-296`, `analysis/paper/patterns.py:81-96`,
`analysis/paper/engine.py:1119-1183`, `tests/test_tvb25_exits.py:278-287`,
`analysis/paper/tier_b_exits/events_july_P2.jsonl:91`.

First, the amendment says every missing P2 bank fraction folds into the runner, but then says a
ladder with no bankable rung leaves a 90% runner. The fractions are 40% + 20% + 20% + 10% banks plus
a 10% base runner, so folding all missing banks produces a 100% runner. The engine, unit test, and
committed events use 100%, which is internally coherent. The prereg needs a dated correction from
90% to 100%; an independent implementation based on the current prose has two possible answers.

Second, the amendment requires the structural stop source-bar index to be recorded. `Signal` and
the entry event record only a relative string such as `closed[-1]`, `closed[-2]`, or `developing`.
The anchor value is frozen and its drift assertion is sound, but the promised absolute source index
or timestamp is absent. Record it and bind it in the frozen-state/adversarial tests, or amend the
requirement if the relative token was the intended audit field.

#### 7. LOW -- The D13 merge note overstates the forming-row revision count

**Location:** `docs/experiments/tvb25_exit_round_prereg.md:334-343`,
`analysis/paper/bars/xyz_MRVL_5m.json:1`, `analysis/paper/bars/xyz_MSFT_5m.json:1`.

I compared every bar file in `047d695^..047d695` by timestamp and value. The important integrity
claims pass: no row was removed, no shared row before the July endpoint changed, and none of the 11
5-minute streams gained a continuity hole. The exact note that one post-window row was revised in
every file does not pass. Thirty-one of 33 files revise exactly one shared row; MRVL 5m and MSFT 5m
revise none because their prior files ended before the newly appended sequence. The 31 revisions
occur at two timestamps (22 at 2026-08-04 00:00 UTC and 9 at 00:50 UTC), not one uniform forming-bar
timestamp. Correct the D13 receipt text; the underlying fresh-window pin and hashes remain usable.

### Confirmed checks (not findings)

- **Range and order:** The pinned range resolves to 11 commits and 98 paths. The amendment commit
  `2411821`, harvest `047d695`, engine `007208e`, runner `209d2ef`, corrections `5796da2` and
  `7f3626e`, and canonical run `62ff310` are in the declared order. The amendment was append-only;
  text above its dated section was not silently rewritten. The current post-range commit is docs-only
  routing. `git diff --check` passes.
- **No Pine exposure:** `git diff --name-only b31c11d^..6597a68 -- pine` is empty, so there is no new
  `request.security` or lookahead surface in this session.
- **Inert defaults:** An independent in-memory replay reproduced all 55 Tier B and 88 T1-floor
  committed per-symbol rows with no mismatches. The manifest records the same census at
  `analysis/paper/tier_b_exits/manifest.json:174-179`. Code inspection and the overlay regression
  preserve the incumbent target/BF/break/flip relative order on the default paths.
- **Artifact identity:** The full prereg SHA-256, all 33 bar hashes, and all six executed-code blob
  hashes in `analysis/paper/tier_b_exits/manifest.json:139-186` match the checked-out bytes. The
  recorded pre-run head is `7f3626e`, the run is non-smoke, and the only recorded dirty path was the
  then-untracked canonical output directory (`analysis/paper/tier_b_exits/manifest.json:239-247`).
- **Rollups and receipts:** Independent aggregation reproduced every July and fresh row's trades,
  entries, realized/open/combined P&L, fees, open counts, exit-kind counts, and exit-kind P&L. D10
  matches `0.0125 * (entries + sum(exit fractions))` percentage points. Every closed/open tranche
  reconciles to total fraction 1.0. The matched-entry receipt identities, cardinalities, and
  aggregates reproduce; the report errors in finding 5 are presentation/axis errors, not receipt
  corruption.
- **TVB-24 fold:** The revised F3 helper now checks explicit arm sets, stream-vs-rec counts, roster
  scope, symbols, and both exit directions; F4 protects the exact canonical 3x3 artifact and validates
  the wrapper/read-back count; F5 binds price, ladder, boom, PMG, reversal, and star fields with
  duplicate-identity rejection; F6 makes receipt provenance additive. The new TVB-25 caller defect
  in finding 4 does not undo those helper-level repairs in their original runner.
- **Tests and static checks:** `PYTHONDONTWRITEBYTECODE=1; uv run python -B -m pytest -q -p
  no:cacheprovider` passed 258 tests with 2 skipped. `.venv\Scripts\ruff.exe check --no-cache
  analysis tests scripts` passed, as did `node --check scripts/tvb23_pkg_harvest.mjs`. A separate
  `uv run ruff` invocation did not start because uv encountered a local cache-path `File exists`
  error; the direct project ruff binary supplied the code-quality result. The worktree was clean
  before this audit file was created.

### Validation limits

- I did not contact TradingView or Hyperliquid and did not refresh the archive. Harvest validation
  was against the pinned committed before/after files and their hashes.
- I did not regenerate or overwrite the canonical output directory. Determinism, rollup, receipt,
  fee, collision, and harvest checks ran in memory against committed inputs and artifacts.
- Historical field equality establishes scoped replay stability, not causal market fill, shared-cash
  portfolio behavior, or live readiness. No deployment or strategy promotion is supported here.
- The D14 counterfactual needs the dated user ruling identified in finding 3 before a corrected
  canonical rerun can be specified.

## 3. Actionable items (reviewer's own list)

1. Repair D9 to count within-bar arm-and-fire state transitions, assert the counter in the existing
   P2 fixture, rerun both windows, and revisit the provisional collision order -- **HIGH** --
   `analysis/paper/engine.py:868-973`.
2. Make the runner support or explicitly account for same-timestamp i3-degenerate episodes and add
   an end-to-end regression -- **MEDIUM** -- `analysis/paper/tier_b_exits.py:248-261`.
3. Obtain a dated D14 entry-hour ruling, encode it, add both long and short boundary tests, and rerun
   affected arms if the literal inclusive reading wins -- **MEDIUM** -- `analysis/paper/engine.py:621-699`.
4. Pass the declared family to `_entry_stream_gate`; add a missing-produced-arm mutation and a
   targeted zero-key/modulo determinism regression -- **MEDIUM** -- `analysis/paper/tier_b_exits.py:657-679`.
5. Correct the fresh combined-vs-realized comparison, matched-sum units, P1 comparison universe, and
   C0 label in the report/ledger -- **MEDIUM** -- `docs/experiments/tvb25_exit_round_report.md:27-47`.
6. Add dated prereg clarifications for the 100% no-bank P2 runner and the intended stop-source audit
   field; record an absolute source index/time if the existing requirement stands -- **LOW** --
   `docs/experiments/tvb25_exit_round_prereg.md:265-296`.
7. Correct the D13 merge receipt to 31/33 revised shared rows while retaining the verified no-drop,
   no-July-change, no-hole claims -- **LOW** -- `docs/experiments/tvb25_exit_round_prereg.md:334-343`.

## Suggested prompt (optional)

After the fold, ask the next reviewer to mutate each canonical gate at its caller boundary (remove an
arm, delete a final tranche exit, alter a rec count, reorder a family), then independently reconstruct
D9 from ordered per-bar eligibility rather than trusting the stored counter. Require an explicit
receipt showing whether every D14 entry-hour collision was included or excluded under the dated
ruling.
