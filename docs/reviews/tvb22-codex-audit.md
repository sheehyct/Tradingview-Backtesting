<!--
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-22 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of `056f47b^..a2ede4e` on `main`, captured 2026-08-10
> (TVB-22 post-session). Lightly ASCII-normalized (em-dashes -> --, curly quotes -> straight);
> wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-22 -- TV package strategy, TVB-21 audit fold-in, ruled rerun, and package parity gate
- **Reviewed:** `056f47b^..a2ede4e` on `main` (13 commits, 28 paths)
- **Reviewer:** OpenAI Codex (GPT-5)
- **Overall verdict:** NEEDS-CHANGES

## 2. Verbatim audit

### Verdict

NEEDS-CHANGES. The TVB-21 audit fold-in is faithful: the user-ruled amendment precedes code, the
engine and Pine now require target containment, the four fixtures pin the audited classes, the
no-target/veto counters reconcile, and the regenerated artifacts preserve A0a/A0b/A1 byte-for-byte
apart from the declared zero counter. The rerun totals and mechanism splits reproduce. The package
Pine is a faithful merge of the two named sources under H1-H7, and the committed nine-cell parity
result independently regenerates at 487 matched events with 246 pattern/trigger checks.

The new pattern layer is not fully fail-closed, however. If a Python entry loses its `trig` field,
the comparison substitutes NaN; the tolerance comparison against NaN is false, so the gate still
passes. I reproduced that against the committed GOOGL/A1 cell: after deleting the first twin
entry's trigger in memory, the gate still returned PASS with 79 matched events, 40 pattern checks,
zero pattern violations, and zero structural violations. All 246 committed twin triggers are
present, finite, and equal to the harvested values, so this does not falsify the current 9/9
artifact. It does break the advertised future drift-detector contract and needs a regression before
the gate can be called fail-closed.

### Findings

#### 1. MEDIUM -- A missing twin trigger silently passes the pattern parity layer

- **Severity:** MEDIUM
- **Location:** `analysis/paper/pkg_parity.py:120-132,239-246`
- **Status:** CONFIRMED

`validate_events()` checks action, direction, exit kind, and duplicate keys, but it does not require
an entry to carry a finite numeric trigger. The later trigger check uses
`te.get("trig", float("nan"))`; when the key is absent, `abs(tv - nan) > mintick / 2` evaluates false.
The entry is counted as checked and contributes no violation. A future engine refactor that drops
the field can therefore make the specific drift payload disappear while leaving `pass=True`.

This is not merely an untested edge: deleting `trig` from one real committed twin event reproduced
the false PASS. A normal numeric change of more than half a tick does fail as intended; the defect is
the missing/non-finite schema path. Validate required entry fields before the join, require both
triggers to be real and finite, and add missing/NaN/non-finite regression cases that assert
`pass=False`.

#### 2. LOW -- The A1 ladder census has no pinned denominator or reproducible receipt

- **Severity:** LOW
- **Location:** `docs/experiments/tvb22_next_variant_seed.md:10-25`; `analysis/paper/tier_b.py:217-285`
- **Status:** CONFIRMED

The seed reports 70% reaching at least two rungs, 40% reaching at least four, 43% stalling at one or
two, and about 3.6 rungs before a harvest exit, under an introductory 10-symbol-roster scope. It does
not say whether the denominator is all entries, closed trades, BF-harvest exits, or only trades that
reach at least one rung. The committed result rows retain only coarse ladder depth *at entry*; they
do not retain this traversal census or its denominator.

Using the direct reading of "rungs reached before exit" on a deterministic replay of the declared
10-symbol roster gives, for all 137 closed A1 trades, 89/137 = 65.0% at two or more, 51/137 = 37.2%
at four or more, and 54/137 = 39.4% at one or two. Including the nine open trades marked through the
window end gives 64.4%, 35.6%, and 41.1%. Restricting to the 86 BF exits gives 74.4%, 44.2%, and
41.9%; their mean is 3.41 rungs, or 3.62 only after excluding the five zero-rung BF exits. These
views support the qualitative bimodality, but none reproduces all four published numbers under one
stated denominator.

Nothing in the seed is declared and no depth is promoted, so the consequence is limited. Before
these figures become preregistration evidence, commit the census calculation or a compact receipt
that pins roster inclusion, open-trade treatment, touch convention, exit subset, zero-rung handling,
and exact counts.

#### 3. LOW -- Final review metadata contradicts the completed parity state

- **Severity:** LOW
- **Location:** `pine/tfc_mt_package_strategy.pine:100-105`; `analysis/reference/pkg_parity/tvb22_parity_result.json:3-5`; `docs/reviews/REVIEW_REQUEST.md:31-35`
- **Status:** CONFIRMED

The final Pine header still says `SCOPE OF THE PARITY CLAIM: NONE YET` and requires its own gate to
pass, while the committed result says `all_pass: true` and the session claims the completed 9/9
gate. The conservative stale warning does not overstate safety, but it leaves the script's binding
contract inconsistent with the artifact that authorizes its use as a drift detector. Update the
header to name the passed artifact, nine-cell scope, event/pattern counts, and unchanged realtime
exclusion.

The work order also labels the pinned range as 14 commits while listing 13 SHAs; `git rev-list
--count 056f47b^..a2ede4e` returns 13. The SHA range and 28-path scope are unambiguous, so this is a
bookkeeping nit rather than a scope failure.

### Confirmed checks that are not findings

- **Range and snapshot:** The pinned range contains 13 commits and exactly 28 changed paths;
  `git diff --check` passes. Current HEAD is two documentation-only commits later, with no reviewed
  implementation or result blob changed after `a2ede4e`.
- **TVB-21 fold-in fidelity:** The dated amendment is the only change in `2865e5a`; implementation
  begins in `b54b07b`. It records containment including gap-past, born-beyond handling, vetoes before
  the no-target skip, the overlap counter equation, source hashes, in-place regeneration, and the
  A0a/A0b/A1 isolation invariant (`docs/experiments/tvb21_tier_b_prereg.md:181-217`). The original
  report change is an inserted invalidation notice; its prior text remains intact
  (`docs/experiments/tvb21_tier_b_report.md:3-22`).
- **Containment implementation and fixtures:** Both directions use `low <= target <= high`, and
  exit-at-level plus target-first race remain intact (`analysis/paper/engine.py:483-496`). The new
  tests cover born-beyond long and short non-containment followed by containment, favorable
  gap-past, and no-target/veto overlap reconciliation (`tests/test_pattern_engine.py:206-323`).
- **Fix isolation and determinism:** All 33 A0a/A0b/A1 per-symbol JSONL rows are byte-equal to the
  invalidated run after removing only the zero `no_target_vetoed` member. An independent field
  comparison of both A0 arms against the committed Tier A cells found no mismatch. The manifest's
  three executed hashes equal both the current files and the files at recorded HEAD `40d6e7f`; all
  33 bar hashes match (`analysis/paper/tier_b/manifest.json:4-10,71-118`).
- **Rerun arithmetic:** The five rollups regenerate the report totals. A2/A3 move from
  -221.9622/-127.5018pp to +24.5653/+30.9582pp, with 186/157 closed trades and the stated exit mix.
  The candidate equations reconcile exactly. The current combined plain-3-2 census is 67 trades,
  +43.3538pp, 35 wins (52.2%). A2 has 73 strict born-beyond closed trades at -21.3098pp; including
  two exactly-at-target zero-P&L trades gives the seed's 75 at-or-past count with the same rounded
  P&L. The 53 positive-but-under-0.25% T1 trades return +4.3862pp with 53 wins, and 17 were compressed
  below the floor by late fills. Tail, drawdown, one-bar-exit, veto-share, and nine-backstop-exit
  claims also reproduce (`docs/experiments/tvb22_tier_b_rerun_report.md:23-97`).
- **Pine source fidelity:** After the declared identifier renames, the aggregation/classification,
  16-branch signal chain, PMG loop bodies, prefix logic, and ladder loop bodies are statement-equal
  to `pine/strat_magnitude_targets_plus.pine`. Removing only H4 and its extra arguments/return leaves
  `f_pool` statement-equal to the control source. H7 merely guards PMG work by the conditions under
  which its values are read and guards the non-persistent ladder arrays by `sigDir != 0`; no later
  signal-less path reads those outputs (`pine/tfc_mt_package_strategy.pine:587-669`).
- **Veto and target mirror:** The Pine H4 scan reads state-zero harvest sides before detection or
  lifecycle mutation, values them at the current bar open timestamp, and chooses the nearest strict
  beyond-fill line, matching `_alive_harvest_vals` plus `_pattern_entry` filtering
  (`pine/tfc_mt_package_strategy.pine:695-736,1013-1023`; `analysis/paper/engine.py:414-429,566-589`).
  The target containment and veto-before-skip branches mirror the amended engine
  (`pine/tfc_mt_package_strategy.pine:1052-1123`).
- **Parity evidence:** Every harvest receipt names the requested arm and package strategy, has one
  matching strategy, 5-minute resolution, floor history, matching chart symbol, and only `le`/`se`
  entry types. Recomputing all nine cells in memory reproduced the committed JSON result after JSON
  key normalization: 487/487 events, offset 0, zero structural or exact-price violations, and 246
  current pattern/trigger matches (`analysis/paper/pkg_parity.py:189-310`). Finding 1 is a future
  malformed-schema false PASS, not a mismatch in those committed values.
- **Lookahead:** The only Pine path in the range is the new package strategy, and it adds no
  executable `request.security` call. Its higher-timeframe state is locally aggregated.
- **Research and fee discipline:** The rerun and seed keep contrasts scoped, call the depth sweep a
  ceiling map, forbid promotion, and label the window gross and in-sample. The Pine strategy uses
  zero commission/slippage and the report makes no net-performance or deployment claim
  (`pine/tfc_mt_package_strategy.pine:118`; `docs/experiments/tvb22_tier_b_rerun_report.md:13-15,49-63,99-100`).
- **Validation:** `.venv\Scripts\python.exe -B -m pytest tests/ -q -p no:cacheprovider` passed
  `144 passed, 2 skipped`; Ruff passed for `analysis/` and `tests/`; `node --check` passed for the
  harvester. The secret scanner passed the reviewed range/current routing-doc snapshot (28 files,
  no findings).

### Validation limits

- I did not run the live CDP harvester, recompile the Pine strategy in TradingView, inspect the
  mounted chart, or repeat the Make-a-copy/round-trip operation. The nine committed floor receipts
  and exact event replay are strong evidence, but live UI and compiler state remain source/artifact
  evidence.
- I did not overwrite committed outputs. Artifact comparison, Tier B replay, class decomposition,
  adversarial gate checks, and parity regeneration ran in memory against the pinned implementation
  and committed bars.
- The manifest records only a dirty boolean, not the dirty path list. Its executed blobs and bar
  hashes verify, and the next commit contains only regenerated outputs plus the rerun report, but the
  exact runtime dirty-path set cannot be reconstructed from the receipt.
- The parity gate is historical, close-cadence, decision-level evidence on three symbols. It does
  not establish realtime tick cadence, cash-fill price parity for declared-residual events, unseen
  pattern branches, or unseen regimes. The Tier B result remains one roughly four-week, gross,
  in-sample window.

## 3. Actionable items (reviewer's own list)

1. Make the pattern trigger layer fail closed -- **MEDIUM** --
   `analysis/paper/pkg_parity.py:120-132,239-246` -- require finite numeric triggers on every entry
   before joining, reject missing/NaN/non-finite values, and add adversarial regression tests.
2. Commit a reproducible A1 ladder-traversal receipt before using it in the next preregistration --
   **LOW** -- `docs/experiments/tvb22_next_variant_seed.md:10-25` -- pin scope, denominator, open
   handling, touch rule, zero-rung treatment, counts, and the script/query that produces them.
3. Reconcile final parity metadata -- **LOW** -- `pine/tfc_mt_package_strategy.pine:100-105`;
   `docs/reviews/REVIEW_REQUEST.md:31-35` -- record the passed nine-cell artifact in the Pine header
   while preserving the realtime caveat, and correct the range count from 14 to 13.

## Suggested prompt

Add: "Before accepting the TVB-22 gate, delete and NaN one twin entry trigger and require both cases
to fail structurally. Then regenerate a committed A1 ladder-census receipt with an explicit
10-symbol exclusion set and one denominator per percentage; do not carry approximate unlabeled
percentages into the T1-floor preregistration."

Verdict: NEEDS-CHANGES
