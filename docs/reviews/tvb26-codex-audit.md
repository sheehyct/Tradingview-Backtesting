<!--
External review of TVB-26. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-26 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of `53599c4^..7f91c9c` on `main`, captured 2026-08-17
> (TVB-26 post-session). Lightly ASCII-normalized (em-dashes -> --, curly quotes -> straight);
> wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-26 -- TVB-25 audit fold, engine/runner repair, and canonical regeneration
- **Reviewed:** commit range `53599c4^..7f91c9c` on `main` (7 commits, 30 paths)
- **Reviewer:** OpenAI Codex CLI (GPT-5)
- **Overall verdict:** NEEDS-CHANGES

## 2. Verbatim audit

### Verdict

NEEDS-CHANGES.

The fold is mechanically strong. The audit amendment preceded code; the repaired code preceded the
canonical rerun; the manifest binds that exact code and prereg blob; all ten new arms replay exactly
to every committed event, per-symbol row, and rollup in both windows; the D14 stream changes and
stop-source additions reconcile; and the matched aggregates are unchanged. The state-degenerate
runner path now survives end to end. The full suite and static checks pass, no Pine file changed, and
the HANDOFF archive move is verbatim below its new archive header.

Approval is withheld because the corrected D9 instrument supports the collision frequencies but not
the report's stronger statement that the ruled order always books the worse fill. The two fill
classes make that inference false on committed bars: close-filled i3/brk/flip and level/open-filled
stops can rank either way. The same decomposition also undercounts bars containing `prot+tgt` when a
third class is present. These do not corrupt the canonical event stream under the chosen order, and
they do not revoke the user's authority to retain that order, but they do leave the stated rationale
for the user ruling unsupported. Three smaller fail-closed, rounding, and regression-coverage nits
also remain.

### Findings

#### 1. MEDIUM -- D9 does not prove the ruled priority is pessimistic, and the report omits two prot+tgt supersets

**Location:** `docs/experiments/tvb25_exit_round_prereg.md:239-264`,
`docs/experiments/tvb25_exit_round_prereg.md:400-410`, `analysis/paper/engine.py:913-969`,
`analysis/paper/engine.py:1046-1060`,
`analysis/paper/tier_b_exits/results_rollup_july.jsonl:10`,
`analysis/paper/tier_b_exits/results_rollup_fresh.jsonl:23`,
`analysis/paper/tier_b_exits/events_fresh_PX.jsonl:70-71`,
`analysis/paper/tier_b_exits/events_fresh_PX.jsonl:106-107`,
`analysis/paper/bars/xyz_SKHX_5m.json:1`,
`docs/experiments/tvb25_exit_round_report.md:164-189`, `docs/ARM_LEDGER.md:64-76`.

The repaired counter and combination map are internally correct. They answer which exit classes were
satisfiable on a bar under the ordered state transitions. They do not answer which class would have
produced the worse fill. That requires candidate prices because i3, brk, flip, and state fill at the
5-minute close, while stops and protective levels fill at their level or a gap-through open.

The committed PX fresh stream supplies a direct counterexample to the categorical claim. One
`i3+stop` bar enters with both i3 and structural stop at 1172.6 and exits i3-first at the 1156.5 close,
which is worse for the long. Another enters with both at 1184.2 and exits i3-first at the 1184.4
close, which is better for the long than the stop fill. The bar ranges contain the shared levels in
both cases. A focused replay of the 16 roster collision bars the report labels genuinely
order-sensitive found mixed signs: the committed priority was better than the competing class on
seven and worse on nine. Thus "books the worse fill there by design" is not established by D9 and is
false as a per-bar statement. The prereg itself says the named alternatives were not priced.

There is a second, narrower counting error. `collision_pairs` is actually an exact full-combination
map: the key joins every class in the set. PX July contains 19 exact `prot+tgt` combinations plus two
`bf+prot+tgt` combinations. Both supersets contain prot and tgt, so "every prot+tgt bar" totals 58
across the four tranche arm-windows, not the reported 18+19+10+9 = 56. Independent state tracing
still found zero of those 58 with the floor armed at bar start, so the bank-then-floor conclusion
survives; the membership total and decomposition language do not.

Keep the user ruling if it is a priority convention rather than a guarantee of per-bar pessimism,
but relabel it accordingly. If "always worse" was material to the ruling, persist candidate fills or
counterfactual deltas per collision and put the corrected evidence back to the user. Correct the
56-to-58 membership total (or explicitly label 56 as exact two-class keys) in the prereg outcome,
report, ledger, and HANDOFF synthesis.

#### 2. LOW -- The advertised exact-arm gate rejects missing arms but accepts unexpected arms

**Location:** `analysis/paper/tier_b_exits.py:626-636`,
`analysis/paper/tier_b_exits.py:687-710`, `analysis/paper/tier_b_t1floor.py:473-498`,
`tests/test_tier_b_exits.py:136-151`.

The TVB-26 caller repair fixes the audited false-PASS: a removed canonical arm fails, and I also
mutated the smoke expectation (`D1`, `P1`) by removing `P1`; it fails. But the helper's documented
"exact arm set" check is only one-way. It computes `expected - produced` and never checks
`produced - expected`. Supplying an extra produced `P2` stream to that same smoke expectation returns
no failure because subsequent checks iterate only expected arms.

Current canonical construction requests the full family, so this does not shrink or alter the
committed matrices. It does mean a future smoke selector or caller regression can run and write an
unrequested family arm while the scope gate reports PASS. Enforce set equality in both directions
and add unexpected-arm mutations for canonical and smoke paths.

#### 3. LOW -- D10 rounds per symbol before the roster rollup

**Location:** `docs/experiments/tvb25_exit_round_prereg.md:308-312`,
`analysis/paper/tier_b_exits.py:336-340`, `analysis/paper/tier_b_exits.py:424-437`,
`analysis/paper/tier_b_exits/results_rollup_july.jsonl:5`,
`analysis/paper/tier_b_exits/results_rollup_fresh.jsonl:18`.

D10 says to retain full-precision floats and round only at reporting. The runner instead rounds each
symbol's fee to four decimals, then sums those rounded values for the roster rollup. Recomputing from
the committed P1 entry count and fractional exit sides gives 1.0000pp July and 0.6500pp fresh; the
rollups report 1.0002pp and 0.6502pp. Every other checked new-arm rollup reconciles at four decimals.

The difference is immaterial to every conclusion here, but it is avoidable and violates the stated
round-once contract. Carry an unrounded fee accumulator (or fee-side count) into `_rollup_arm`, then
round the final roster value. Keep the displayed per-symbol field separately rounded if required.

#### 4. LOW -- stop_src_ts is implemented and reproduced but not regression-bound

**Location:** `docs/reviews/tvb25-codex-audit.md:183-187`,
`analysis/paper/patterns.py:384-390`, `analysis/paper/engine.py:1195-1212`,
`analysis/paper/engine.py:1305-1318`, `tests/test_tvb25_exits.py:24-38`,
`tests/test_tvb25_exits.py:218-230`.

The accepted audit asked for the absolute source record to be bound in frozen-state/adversarial
tests. The implementation does calculate, freeze, drift-check, and emit it. I checked every one of
the 345 structural-stop entries across D1S/PX and both windows: each timestamp has the declared
offset from the signal hour and names an actual committed 1-hour source bar. Removing only
`stop_src_ts` also makes every regenerated D1S/PX event byte-field-equal to its pre-fix version.

No test mentions `stop_src_ts`; the synthetic Signal helper cannot supply it, and the structural-stop
test asserts only the stop price/kind and fill. A future deletion or off-by-one timestamp can pass the
suite and recreate audit F6 while leaving stop prices unchanged. Add closed[-1], closed[-2], and
developing-source assertions, including repeat-detection freeze behavior and the emitted entry field.

### Confirmed checks (not findings)

- **Range and chronology:** `53599c4^..7f91c9c` resolves to 7 commits and 30 paths. The dated
  amendment (`4631dbd`) precedes engine/runner repair (`cea3372`), which precedes regeneration
  (`0c95a60`) and report/ledger correction (`871ca78`). The amendment was append-only; the later
  risk-first outcome is explicitly dated after the corrected census. The post-range commit is
  docs-only routing. `git diff --check` passes.
- **Provenance:** The manifest's six executed-code hashes match current bytes, its prereg SHA-256
  matches the exact amendment blob at `4631dbd`/`cea3372`, its pre-run head is `cea3372`, all 33 bar
  hashes match, and the recorded run was clean and non-smoke.
- **Canonical replay:** In-memory replay of all ten new arms across all eleven symbols and both
  windows matched every committed event object, per-symbol record, and rollup with zero mismatches.
  Corrected roster collision totals reproduce: P2 18/11, PX 25/12, A0bS 5/4, P1 1/1, S0b 1/1,
  S0c 1/0 (July/fresh).
- **D14:** The existing-position race runs before entry; the new post-entry check is on the
  hour-completing entry bar, after the i3 degenerate check, and uses the one-tick strict-break rule
  (`analysis/paper/engine.py:682-734`). Long, short, and one-tick boundary tests cover it
  (`tests/test_tvb25_exits.py:124-179`). A bar-level join also confirms the mid-hour argument is not
  hypothetical: 104 roster July and 59 roster fresh S0a trades already exit at that entry hour's
  close after an opposite break that occurred before the mid-hour entry. The new all-symbol
  state-degenerate counts are 14/14/15 July and 8/8/8 fresh; roster fresh is 6 per S arm.
- **Regeneration field diff:** Repository blobs for every non-S0/non-stop stream are unchanged.
  D1S/PX preserve line count and every old field exactly, adding only `stop_src_ts` to structural
  entries. The S0 streams contain exactly the ruled state-degenerate counts and their downstream
  occupancy changes. Both families' matched closed aggregates, sums, means, and win rates are
  exactly unchanged at four decimals; only S-family identity census counts increased.
- **Zero-duration episodes:** Closed same-timestamp trades retain P&L and skip excursion metrics;
  a final-bar open position also skips an undefined excursion window
  (`analysis/paper/tier_b_exits.py:248-292`). The runner-level D14 regression retains P&L and reports
  null MFE/MAE (`tests/test_tier_b_exits.py:177-205`). The same guards cover an i3 degenerate event,
  so that known month-end abort path is closed.
- **Gate/modulo scope:** Missing produced arms fail under independently exercised canonical and smoke
  expectations. The `veto_counts` compatibility exception remains new-zero-only and is not applied
  to other fields (`tests/test_tier_b_exits.py:155-174`). Finding 2 is only the reverse-set case.
- **Report and ledger arithmetic:** S-family July/fresh rollups, matched sums and means, the fresh
  S0a-vs-A0b combined gap (+19.4615pp), and the P1-vs-D1 matched values reproduce. The D5 earlier
  receipt is +1.7897pp mean on its distinct 37-trade universe, so the narrowed P1 claim is correct.
  Finding 1 is the collision interpretation; finding 3 is only sub-basis-point rounding drift.
- **Language/archive/Pine:** Finding 5 names its prior error in place, the report makes no promotion,
  and the TVB-18 through TVB-21 session blocks are byte-for-byte verbatim in the archive below its
  new header. No Pine path changed, so this range adds no `request.security` surface.
- **Tests/static checks:** `PYTHONDONTWRITEBYTECODE=1; .venv/Scripts/python.exe -B -m pytest -q -p
  no:cacheprovider` passed 265 tests with 2 skipped. Ruff passed with `--no-cache`; Node syntax check
  passed for `scripts/tvb23_pkg_harvest.mjs`. The worktree was clean before this audit file was
  created.

### Validation limits

- I did not contact TradingView or Hyperliquid, refresh bars, deploy, or regenerate/overwrite any
  canonical artifact. Replays and comparisons were in memory against the pinned committed inputs.
- The collision counterfactual was a focused candidate-fill reconstruction on the committed
  collision bars, sufficient to disprove the categorical worse-fill statement. I did not generate
  full alternative-order canonical arms, so the aggregate P&L price of either named alternative is
  still unknown, as the prereg says.
- Historical replay equality validates the scoped research engine and artifacts, not causal
  intrabar path, shared-cash portfolio behavior, TradingView parity for these arms, or live readiness.

## 3. Actionable items (reviewer's own list)

1. Replace the categorical pessimistic/worse-fill claim with a convention-only label or add a
   per-collision candidate-fill/counterfactual receipt; correct the prot+tgt membership total and
   re-confirm the ruling if the worse-fill premise was material -- **MEDIUM** --
   `docs/experiments/tvb25_exit_round_report.md:164-189`.
2. Make the entry-stream arm-set check two-way and add unexpected-arm mutations for canonical and
   smoke scopes -- **LOW** -- `analysis/paper/tier_b_t1floor.py:473-498`.
3. Preserve unrounded fee sides through the roster aggregation and round only the final reported
   fee -- **LOW** -- `analysis/paper/tier_b_exits.py:336-340`.
4. Add direct freeze/source/event regressions for `stop_src_ts` -- **LOW** --
   `analysis/paper/engine.py:1195-1212`.

## Suggested prompt (optional)

After the D9 wording fix, ask the next reviewer to persist one row per collision bar containing all
satisfiable classes, each candidate fill, the executed class/fill, and pairwise signed P&L deltas.
Require membership-aware aggregation for supersets and adversarially mutate both missing and extra
arms in canonical and smoke gate scopes.
