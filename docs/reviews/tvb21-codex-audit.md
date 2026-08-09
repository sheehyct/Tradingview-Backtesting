<!--
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-21 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of `f90d0c9^..1cd6b0c` on `main`, captured 2026-08-09
> (TVB-21 post-session). Lightly ASCII-normalized (em-dashes -> --, curly quotes -> straight);
> wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-21 -- TVB-20 audit fold-in, design session, and Tier B execution
- **Reviewed:** `f90d0c9^..1cd6b0c` on `main` (4 commits, 23 paths)
- **Reviewer:** OpenAI Codex (GPT-5)
- **Overall verdict:** NEEDS-CHANGES

## 2. Verbatim audit

### Verdict

NEEDS-CHANGES. The TVB-20 fold-in is faithful, the ten enabled pattern branches and ladder match
the supplied Pine, the default engine path reproduces both committed Tier A controls exactly, and
the A1-vs-A0b pattern-isolation result independently regenerates. The package result does not
survive the exit-model audit. The pre-registration says a target exit occurs when the 5-minute bar
range reaches the frozen level, but the engine checks only `high >= target` for a long and
`low <= target` for a short. Once an entry is born beyond its target, those predicates can be true
even when the entire exit bar remains on the far side of the target. The engine then records a fill
at a price the bar never traded.

This is the dominant source of the reported A2/A3 loss, not a small accounting difference. On the
10-symbol roster, 188 A2 born-beyond target exits carrying -278.3pp and 97 A3 exits carrying
-146.2pp were outside their exit bars. A read-only sensitivity that required the pre-registered
containment condition changed combined A2/A3 from -222.0/-127.5pp to +24.6/+31.0pp. That sensitivity
is not a replacement experiment -- already-behind targets still need an explicit contract -- but it
proves that the published package verdict, churn mechanism, candidate counts, and tail metrics must
be regenerated. The C1 controls and the A1 pattern-isolation conclusion are not affected by this
target branch.

### Findings

#### 1. HIGH -- Target exits can fill outside the 5-minute bar, invalidating the package verdict

- **Severity:** HIGH
- **Location:** `analysis/paper/engine.py:247-279,482-488`; `tests/test_pattern_engine.py:136-190`; `docs/experiments/tvb21_tier_b_prereg.md:136-142`; `docs/experiments/tvb21_tier_b_report.md:13-22,48-62`
- **Status:** CONFIRMED

The existing BF-touch implementation defines touch as full containment, `low <= line <= high`.
The Tier B target replacement does not reuse that condition. It exits a long whenever the bar high
is at least the target and exits a short whenever the bar low is at most the target. Those one-sided
checks are sufficient while a long target is above the position or a short target is below it. They
are not sufficient for the exact class on which the report is based: a long entered above T1 or a
short entered below T1.

For example, after a short is entered below its frozen target, `low <= target` remains true on a
later bar that is wholly below the target. The engine closes at the higher target price even though
the bar high never reached it. The long-side mirror closes at a lower target even when the bar low
never reached it. This violates the pre-registered statement that the 5-minute range reaches the
level, and it does not model a marketable limit order either: such an order would execute immediately
at the current market or better, not one bar later at a stale adverse level.

An independent replay of the committed runner and bars found:

- A2: 208 of 410 target exits were outside the exit bar. Of the report's 244 strict born-beyond
  trades, 188 out-of-range target exits contributed -278.3pp. The 55 born-beyond target exits whose
  bars actually contained T1 contributed only -29.0pp.
- A3: 102 of 255 target exits were outside the exit bar. Of the report's 159 strict born-beyond
  trades, 97 out-of-range target exits contributed -146.2pp. The 61 contained born-beyond target
  exits contributed -8.7pp.
- Requiring `low <= target <= high` while leaving every other reviewed rule unchanged yielded a
  diagnostic combined result of +24.6pp for A2 and +31.0pp for A3, versus the committed -222.0pp
  and -127.5pp. This is a materiality check, not an adjudicated replacement result.

The current target test only exercises a normal long target that lies inside the next bar. Add
long/short fixtures where the frozen target is already behind entry and where the next bar does and
does not contain it. Then implement the declared containment rule, explicitly decide how a target
that is marketable at entry is handled, and rerun every A2/A3 artifact and narrative derived from it.

#### 2. LOW -- The no-target skip was not added to the pre-registration and distorts veto-rate denominators

- **Severity:** LOW
- **Location:** `docs/experiments/tvb21_tier_b_prereg.md:76-84,136-142`; `analysis/paper/engine.py:549-575`; `docs/experiments/tvb21_tier_b_report.md:70-85`
- **Status:** CONFIRMED

The pre-registration exhaustively says A2 exits all at T1 and A3 falls back from rung 2 to T1, but
does not define a zero-rung signal. The implementation makes a new choice: count the signal as a
candidate, skip the entry, and return before either veto is evaluated. The report discloses 131 such
candidates, and the work order calls this a post-declaration, pre-run clarification, but there is no
dated pre-run amendment in the pre-registration itself.

This also makes the stated veto rates internally ambiguous. `candidates` includes the 131 no-target
signals, while the BF-proximity and chop numerators cannot include them because the function returns
first. Therefore statements such as "share of candidates within 2%" treat unevaluated rows as if
they were outside the band. Before the required rerun, amend the contract to choose skip, fallback,
or another structural behavior and either evaluate diagnostics before the skip or exclude those
signals from the veto-rate denominator.

#### 3. LOW -- The reported plain-3-2 census silently reintroduces the excluded DRAM parity symbol

- **Severity:** LOW
- **Location:** `docs/experiments/tvb21_tier_b_report.md:3-9,88-95`; `analysis/paper/tier_b.py:289-292,326-365`; `analysis/paper/tier_b/results_by_symbol.jsonl:36,47`; `analysis/paper/tier_b/results_rollup.jsonl:4-5`
- **Status:** CONFIRMED

The report frames everything below its introduction as the 10-symbol roster rollup with DRAM
excluded, and `_rollup_arm()` applies that exclusion to the pattern census. The reported plain-3-2
figures -- 182 trades, -163.0pp, 33% wins -- instead reproduce only when the A2/A3 DRAM rows are
added back and the two Boom trades are removed. Under the declared roster scope, the corresponding
plain-3-2 values are 139 trades, -151.2pp, and 29.5% wins. It remains the largest and worst class, so
the qualitative reading survives, but the scope and figures should be corrected or explicitly
labeled as an all-11-symbol diagnostic.

#### 4. LOW -- The run manifest records the pre-code HEAD, not a source receipt for the executed runner

- **Severity:** LOW
- **Location:** `analysis/paper/tier_b.py:397-469`; `analysis/paper/tier_b/manifest.json:1-4,100-114`; `docs/experiments/tvb21_tier_b_report.md:3-6`
- **Status:** CONFIRMED

The manifest records `94090e9` as `git_head`, but `analysis/paper/tier_b.py`, the pattern port, and
the engine extension do not exist in that commit; they first appear together with the outputs in
`163323b`. This is consistent with running from an uncommitted post-prereg worktree, but the manifest
does not record a dirty-state flag, runner blob hash, or diff hash. Its HEAD field therefore proves
the pre-registration was committed, not which source produced the timestamped run.

This did not prevent current verification: the committed `163323b` runner regenerated all 55 symbol
rows and all five rollups exactly in memory, and all 33 bar hashes match. Future manifests should
record the executed runner/engine/pattern blob hashes plus clean/dirty state, or commit code before
the run and record that source commit separately from the pre-registration commit.

### Confirmed checks that are not findings

- **Range and snapshot:** `f90d0c9^..1cd6b0c` contains the named four commits and exactly 23 changed
  paths; `git diff --check` passes. Current HEAD is two documentation-only commits later. None of the
  reviewed implementation or result blobs changed after `1cd6b0c`.
- **TVB-20 parity fold-in:** the hardened gate rejects duplicate keys, invalid directions, unknown
  exit comments, malformed open-row placement, and unequal cardinality. Read-only comparison passes
  GOOGL 89/89/89, TSLA 67/67/67, and DRAM 87/87/87 with zero structural violations and zero maximum
  break/flip price delta (`analysis/paper/port_parity.py:77-115,169-274`; `tests/test_port_parity.py:91-145`).
  The committed parity-result blob is unchanged across the review range.
- **Harvester fold-in:** unknown/empty selectors fail before work begins; run completeness is separate
  from canonical-inventory completeness; every canonical inventory row must carry an error-free
  `history.state == "floor"` receipt (`scripts/tvb19_harvest.mjs:39-61,204-240`). The committed dump
  summary and all dump files are unchanged; only their README changed.
- **Contrast and port wording fold-ins:** charter S3.1 now names C0/C1/C2 and confines any pattern-thesis
  inference to an isolating contrast. The control Pine change is comments only and accurately limits
  the claim to historical close-only decision parity. No executable Pine changed and no
  `request.security` call appears in the range.
- **Enabled pattern fidelity:** for the ten enabled setups, the Python port preserves the Pine's
  `>= mintick` subtraction flags, warm-up guards, branch precedence, color gates, hammer/shooter
  formula, conditional anchor2, strictly monotone ladder walk, six-level cap, and 250-bar history
  (`analysis/paper/patterns.py:94-228,232-377`; `pine/strat_magnitude_targets_plus.pine:135-260,264-587`).
  PMG+ is unreachable for this dictionary as claimed: every enabled long branch requires `u0`, which
  contradicts the first bullish PMG comparison seeded at `curH`; the short mirror is identical.
- **Default-path invariance and committed artifacts:** an independent in-memory run with the committed
  runner and bars reproduced all 55 `results_by_symbol` rows and all five rollups exactly. A0a/A0b
  match all 11 committed Tier A rows on every declared shared field, and all 33 manifest bar hashes
  match (`analysis/paper/tier_b.py:111-139,369-394`; `analysis/paper/tier_b/manifest.json:65-112`).
- **Internally reproducible report arithmetic:** before applying Finding 1, the stored algorithm
  reproduces the 244/413 and 159/263 strict born-beyond splits, -310.1/+88.1pp and -156.0/+72.6pp,
  72.6% one-bar A2 exits, 58.6% next-bar re-entries, the GOOGL chain, 197 rung-2 entries, and the
  54.215pp A1 entry-price drag across 53 late fills. The arithmetic is reproducible; the target-fill
  predicate makes the package interpretation invalid.
- **A1 contrast and research discipline:** A1 regenerates -7.7pp combined versus A0b +104.8pp. Using
  the trigger-level convention adds about 54pp and still leaves A1 materially below A0b. No file or
  commit promotes an arm, pattern, cell, or timeframe, and the S3.1 conclusion is explicitly limited
  to A1-vs-A0b and one in-sample window.
- **Fees and turnover:** all results are explicitly 1x GROSS with zero fees, funding, and slippage.
  No net-performance or deployment claim is made. Any future T1-floor value must be pinned before a
  run rather than selected from this churn record.
- **Validation:** `.venv\Scripts\python.exe -B -m pytest tests/ -q -p no:cacheprovider` passed
  `140 passed, 2 skipped`; Ruff passed for `analysis/` and `tests/`; `node --check` passed for the
  changed harvester. The secret scanner passed over the review range plus the two later routing-doc
  commits (24 files, no findings). The worktree remained clean before writing this audit.

### Validation limits

- I did not run the live CDP harvester, recompile either Pine script in TradingView, or inspect the
  mounted chart. The live selector/floor behavior, source-copy state, and visual behavior remain
  source/prose evidence.
- I did not overwrite any committed result. Artifact reproduction, event reconstruction, and the
  containment sensitivity ran in memory against the pinned implementation and committed bars.
- The containment sensitivity is diagnostic only. It demonstrates that the current verdict depends
  on impossible fills; it does not choose the final semantics for a target already behind entry.
  That choice must be explicit before the package is rerun.
- The result remains one roughly four-week, gross, in-sample window. Passing replay and tests does not
  establish unseen-regime behavior or live intrabar parity.

## 3. Actionable items (reviewer's own list)

1. Enforce the pre-registered target-touch contract and rerun Tier B -- **HIGH** --
   `analysis/paper/engine.py:482-488` -- require target containment, add behind-entry long/short
   fixtures, explicitly define marketable-at-entry target behavior, and regenerate every A2/A3
   artifact and report claim.
2. Record the no-target branch before rerunning and make veto denominators coherent -- **LOW** --
   `docs/experiments/tvb21_tier_b_prereg.md:76-84,136-142`; `analysis/paper/engine.py:549-575` --
   add a dated amendment and either evaluate veto diagnostics first or remove no-target signals from
   the candidate denominator.
3. Recompute the pattern census on the declared roster or label DRAM inclusion -- **LOW** --
   `docs/experiments/tvb21_tier_b_report.md:88-95` -- use the committed roster rollup and report
   139 / -151.2pp / 29.5%, subject to the required package rerun.
4. Source-bind future execution manifests -- **LOW** -- `analysis/paper/tier_b.py:397-469` -- record
   clean/dirty state and runner/engine/pattern blob hashes, or run from a committed source revision.

## Suggested prompt

Add: "For every recorded target exit, assert that the 5-minute bar contains the target under the
declared bf-touch convention. Pre-register the handling of targets already behind the prospective
fill and of zero-rung signals before rerunning. Fail report generation on any out-of-range fill,
compute all roster diagnostics from the same explicit exclusion set, and source-bind the manifest
to the executed code."

Verdict: NEEDS-CHANGES
