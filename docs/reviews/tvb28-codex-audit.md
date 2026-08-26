<!--
Copy to docs/reviews/tvb{N}-codex-audit.md and fill in.
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-28 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of tradingview-backtesting `4a07107^..9a964e1` and
> hip3-executor `21bd2a9^..e782e57`, captured 2026-08-26 (TVB-28
> post-session). Lightly ASCII-normalized (em-dashes -> --, curly quotes -> straight);
> wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-28 -- Weekend-1 ledger closeout, TVB-26/27 folds, collision receipts, and conviction census
- **Reviewed:** PRIMARY `C:\Strat_Trading_Bot\tradingview-backtesting`, `4a07107^..9a964e1` (6 commits, 13 paths); SIBLING `C:\Strat_Trading_Bot\hip3-executor`, `21bd2a9^..e782e57` (3 commits, 6 paths)
- **Reviewer:** Codex CLI (GPT-5)
- **Overall verdict:** NEEDS-CHANGES

## 2. Verbatim audit

The two audit folds are directionally sound. The D9 text now retracts the
worse-fill claim, records risk-first as a user-ruled convention, carries the
corrected 4/2 and 7/9 sign evidence, and corrects 56 to 58 textual memberships.
The flip analysis now separates 14 observed stop-first cases from one unresolved
case, and the observed +17.34pp result reproduces. The qualitative 32x risk
dispersion also reproduces. No Pine file, canonical result artifact, or committed
event stream changed in the reviewed primary range.

Those corrections are not enough for approval. The new exact-set check makes the
canonical T1-floor runner fail at its real caller boundary; the collision receipt
both counts non-executable protective labels and compares multi-fill races to one
scalar price; the backing-target claim is neither durably receipted nor fully
reproducible; the conviction medians and frozen-rule method are wrong; and the
corrected analysis retains causal/comparative language that its upper-bound census
cannot support. These are analysis and operator-contract defects, not evidence that
the already acknowledged live lifecycle defects were fixed. The binding pre-live
gate remains necessary.

### Scope interpretation and validation

Both work-order pins resolve exactly as described: six commits and 13 paths in the
primary repository, and three commits and six paths in the explicitly named sibling.
I treated the returned TVB-27 audit as the settled baseline and reviewed the fold
quality and post-pin additions rather than re-litigating its venue reconciliation.
Before this audit file was written, the primary worktree contained only the
pre-existing untracked `User_Notes.md`; the sibling was clean.

Validation performed:

- The complete primary suite passed: 270 passed, 2 skipped. The `uv` wrapper could
  not access its host cache in this environment, so I ran the repository virtual
  environment directly with cache writes disabled. The 63 focused changed tests and
  Ruff checks also passed.
- A full `tier_b_exits` replay passed both determinism gates (55 Tier-B rows and 88
  T1-floor rows) and both July/fresh entry-stream gates. Twenty newly generated arm
  event streams were JSON-byte-identical to their committed counterparts. Generation
  used a temporary output directory; canonical artifacts were not modified.
- Both pinned ranges pass `git diff --check`. The Pine tree is identical at both
  primary endpoints, and no `request.security` surface changed.
- Independent current-roster replay reproduced the 58 documented `prot+tgt`
  memberships and the documented D9 sign summaries. Focused synthetic races then
  tested fractional and multi-exit receipt behavior.
- I recomputed the conviction medians and frozen-rule membership from the committed
  census rows. I also replayed the backing-target check from the still-present local
  ignored candle cache. I did not contact the venue, so clean-checkout durability --
  not current local availability -- governs the provenance conclusion.
- No secret, IP, wallet address, or account value is reproduced in this audit.

### Findings, ranked

No CRITICAL or new HIGH finding was verified.

#### MEDIUM-1 -- The hardened exact-set gate breaks the canonical T1-floor runner

`NEW_ARMS` contains the six entry-book depth arms plus `A1F` and `D1ATR`, while
`ENTRY_BOOK_ARMS` contains only the six depth arms
(`analysis/paper/tier_b_t1floor.py:110-129`). The main loop puts every `NEW_ARMS`
result into `arm_streams` and `arm_recs`
(`analysis/paper/tier_b_t1floor.py:639-652`), then passes those eight-arm maps to
`_entry_stream_gate()` with the six-arm expected set
(`analysis/paper/tier_b_t1floor.py:677-685`). The newly correct reverse-set check
therefore reports `A1F` and `D1ATR` as produced outside the expected set
(`analysis/paper/tier_b_t1floor.py:498-505`).

An in-memory probe using the real caller shape reproduced exactly that failure. The
new regression tests only inject a synthetic `ZZ` arm directly into the helper; they
never exercise the main caller's existing eight-arm shape
(`tests/test_t1floor_gates.py:193-211`). This explains why all tests are green while
the canonical CLI path is not. Worse, each arm's event file is written before the
gate aborts (`analysis/paper/tier_b_t1floor.py:659-685`), so a default rerun can
partially overwrite its output directory and then fail.

**Required change:** pass only the family-specific expected-arm maps to this gate (or
explicitly widen the gate contract), add a caller-level canonical/smoke regression,
and stage outputs so no canonical file is promoted until every gate passes.

#### MEDIUM-2 -- Thirteen of the 58 `prot+tgt` memberships have no executable protective exit

The D9 contract calls these bars ones where multiple exit classes are
"simultaneously satisfiable" (`docs/experiments/tvb25_exit_round_prereg.md:302-307`).
In the engine, however, the target loop can consume every remaining middle tranche
before the same-bar arm-and-fire block runs
(`analysis/paper/engine.py:1032-1043`). That block unconditionally adds `prot` and a
T1 candidate, but `fire_retrace()` emits a floor exit only for middle tranches that
still exist (`analysis/paper/engine.py:898-904,1051-1063`). If the runner's
breakeven is not also contained, no protective exit occurs, yet the bar is still
counted and receipted as a collision (`analysis/paper/engine.py:1064-1074,1099-1135`).

Current-roster replay reproduced all 58 textual memberships, but 13 contained no
executed `floor` or `be`: July P2 4/18, July PX 5/21, fresh P2 2/10, and fresh PX
2/9. Only 45/58 therefore include an actual protective exit under the stated class
meaning. The corrected report's 58-member interpretation
(`docs/experiments/tvb25_exit_round_report.md:175-183`) is a faithful count of engine
labels, but not of executable protective-versus-target races.

**Required change:** define the D9 class boundary unambiguously. If `prot` means an
exit class, add it only when a positive remaining fraction can execute and regenerate
the census. If the intended measure is a no-op arming transition, rename and document
it separately from executable collisions.

#### MEDIUM-3 -- Collision receipt deltas do not price fractional multi-exit paths

The receipt starts with only the first contained target level, even though the target
loop can execute several tranches (`analysis/paper/engine.py:942-951,1032-1043`). It
does preserve all actual exit rows, including fractions, but then selects only
`fired[0]["price"]` and compares every one-price class candidate to that scalar
(`analysis/paper/engine.py:1105-1133`). It neither scopes a candidate to the fraction
that class could consume nor simulates the alternative ordered path.

A canonical PX-July receipt demonstrates the category error: the actual path executes
a 40% target and a 60% BF exit, yet the BF candidate is scored as an alternative to
the first target price even though BF is already part of the actual result. A valid
synthetic P2 race reversed the reported sign when its actual and alternative paths
were compared fraction-weightedly. The receipt can support "candidate price minus
first executed price"; it cannot support the report and prereg claim that future runs
"price every collision both ways"
(`docs/experiments/tvb25_exit_round_report.md:202-209`;
`docs/experiments/tvb25_exit_round_prereg.md:412-428`). This finding affects the new
diagnostic only; the event streams remained byte-identical.

**Required change:** persist all class candidate fills with fraction/tranche scope and
compute a path-aware alternative outcome under each named ordering. Otherwise rename
the field as a first-price diagnostic and narrow every "both ways" claim.

#### MEDIUM-4 -- The backing-target counterfactual is not a committed fact, and its 6/7 closeness claim does not reproduce

The new report calls the result a "Supporting committed fact" and says all seven
continuations stop first while six of seven simulated outcomes lie within 0.2pp of
actual (`C:\Strat_Trading_Bot\hip3-executor\runs\2026-08-22_weekend1\ANALYSIS.md:418-427`).
But commit `e782e57` changes prose only: the counterfactual is absent from
`analysis/weekend1.py` and `analysis.json`, and no per-trade receipt was added. The
report header still says the cached candles reproduce after the venue window moves
(`...\ANALYSIS.md:3-8`), while the corrected script says the cache is ignored and a
clean checkout loses exact first-touch reproducibility
(`C:\Strat_Trading_Bot\hip3-executor\analysis\weekend1.py:3-9`;
`C:\Strat_Trading_Bot\hip3-executor\.gitignore:7-9`).

Using the local ignored cache, I reproduced the seven backing targets, their stated
distance range, and stop-before-target for all seven. Under the report's declared
first-touch, stop-first bracket convention, however, only four of seven simulated
outcomes are within 0.2pp at full precision (five of seven only if values are rounded
before comparison), not six. With no implemented method or receipt, the 6/7 claim is
NOT VERIFIED and the exact-touch result cannot survive a clean checkout.

**Required change:** implement the counterfactual in the analysis script; emit compact
per-trade touch receipts with candle hashes, horizon, and collision convention;
regenerate `analysis.json`; correct the report's cache claim; and remove or relabel
the 6/7 sentence until its method reproduces.

#### MEDIUM-5 -- The conviction census uses nonstandard medians and the wrong R:R clock

The helper sorts a sample and returns `vals[len(vals) // 2]`, which is the upper
middle for an even-sized sample rather than the median
(`C:\Strat_Trading_Bot\hip3-executor\analysis\weekend1.py:713-715`). Independent
recalculation with the standard median gives:

- target distance: winners 1.591% and losers 4.4645%, rather than 1.59% and 4.48%;
- R:R at fill: winners 1.086 and losers 1.7445, rather than 1.09 and 1.87;
- alignment age: winners 104.5 minutes and losers 68.4 minutes, rather than 108 and 69.

The report labels the whole section `n=34`, but the target/R:R comparison is 9 winners
versus 18 losers because seven targetless continuations have no value, and the sparse
alignment comparison is 6 versus 20
(`C:\Strat_Trading_Bot\hip3-executor\runs\2026-08-22_weekend1\ANALYSIS.md:356-381`).
Those denominators are not disclosed.

The frozen-rule decomposition also classifies entries using `rr_at_fill`
(`C:\Strat_Trading_Bot\hip3-executor\analysis\weekend1.py:700-722`), whereas the live
gate computes R:R from decision-time mid
(`C:\Strat_Trading_Bot\hip3-executor\src\hip3_executor\rules.py:164-175`). The current
five refused rows happen to match under both clocks, but that is accidental contract
parity, not a correct method. The remaining targetless continuation is exempt from
the R:R gate and accounts for most of the pre-floor loss, so "the process ruled it
away" overstates what the frozen rule did
(`...\ANALYSIS.md:382-386`).

The main descriptive direction survives correction: winners had nearer targets and
lower raw R:R in this sample, alignment age did not support freshness, and stop
distance produced roughly 32x risk dispersion. Those are associations in a tiny
one-regime sample, not predictive tests.

**Required change:** use `statistics.median`, emit each metric's non-null numerator and
denominator, derive frozen-rule membership from decision-time R:R, separate pre- and
post-freeze populations, and retain characterization-only language.

#### MEDIUM-6 -- The corrected mechanics report still makes causal and controlled-comparison claims

The report's new preamble correctly says every P&L statement is only observed in this
ledger under its model (`...\ANALYSIS.md:10-20`), and its operator-regime section is
properly labeled USER, a-priori, and untested (`...\ANALYSIS.md:399-416`). Several
retained passages nevertheless cross that boundary:

- The fee section converts 900 independent census rows into executable round trips
  and says the R:R floor matters twice (`...\ANALYSIS.md:169-179`).
- The blocked-continuation examples become a "lottery-shaped" class whose live sample
  "drew no runner" (`...\ANALYSIS.md:290-297`).
- The alignment refusals "beat" admissions; the directional leg was "spent"; and
  confirmation lag was "made measurable live" (`...\ANALYSIS.md:299-325`).
- The design handoff says "live data now agrees" and that early-long refusals
  "outperformed" admissions (`...\ANALYSIS.md:429-446`).

These statements are stronger than the method. The report itself records that the
blocked pools use decision-mid entries, have no shared allocator or slot competition,
and use a sparse flip proxy with no fixed bias
(`...\ANALYSIS.md:273-277,318-325`). They are opportunity censuses, not executable
books or controlled swaps. Passing the same data through a favorable or unfavorable
proxy does not identify lag, class shape, selection quality, or causal fee volume.

**Required change:** describe these as simulated outcomes in this upper-bound census.
Remove executable-volume fee extrapolation and the words that assert the refusals
beat/outperformed admissions, lag caused the result, or a class is lottery-shaped.
Keep reachability, direction, and early-entry ideas explicitly as preregistration
hypotheses.

#### MEDIUM-7 -- The fold leaves operator guarantees that contradict its own binding gate

The private README still promises that a position is never left without a venue stop,
that `KILL_FLAT` flattens everything, and that current state is crash-safe
(`C:\Strat_Trading_Bot\hip3-executor\README.md:41-50,75-78`). The newly added binding
gate correctly says the existing lifecycle can leave an unrecorded/unprotected venue
position and can announce flatten success while exposure remains
(`C:\Strat_Trading_Bot\hip3-executor\README.md:80-105`). Both descriptions cannot be
true of the current implementation.

This is a fold-quality finding, not a demand that TVB-28 implement the already planned
round-2 executor changes. The gate also shortens two prior audit requirements: its
`KILL_FLAT` item does not require the zero-position/zero-order proof to be durable
(`docs/reviews/tvb27-codex-audit.md:99-108,417-418`), and its provenance item names
source/config/lock hashes but omits immutable candle hashes and per-setup touch
receipts (`docs/reviews/tvb27-codex-audit.md:282-304,425`). The backing-target defect
above demonstrates why that omission matters.

**Required change:** rewrite the Safety Model and journal description as current
limitations until implementation lands; require a durable `KILL_FLAT` terminal
receipt; and carry the immutable candle/touch-receipt task into the binding provenance
gate.

#### LOW-1 -- Round-once fees do not propagate to roster net metrics

Per-symbol rows correctly expose full-precision `fee_sides`, but their net fields have
already subtracted each symbol's four-decimal fee display
(`analysis/paper/tier_b_exits.py:336-376`). `_rollup_arm()` correctly computes one
roster fee from summed side counts, then still builds both roster net fields by
summing the old per-symbol nets (`analysis/paper/tier_b_exits.py:425-455`). It also
does not return roster `fee_sides`.

On the next regeneration, the requested P1 fee corrections will be 0.0002pp, but the
corresponding net fields will retain the old 0.0002pp drift and cease to equal gross
minus roster fees. No test asserts this algebra. The committed canonical artifacts
were correctly left unchanged in TVB-28, so this is a latent next-regeneration defect.

**Required change:** compute roster net fields from roster full-precision gross/open
values minus `roster_fees`, return roster `fee_sides`, and add an invariant test that
net equals gross minus the single rounded roster fee.

### Confirmed corrections and limits

- D9's convention basis, worse-fill retraction, 4/2 and 7/9 sign evidence, and
  56-to-58 textual membership correction are faithfully folded across the report,
  prereg amendment, and ARM ledger. MEDIUM-2 and MEDIUM-3 concern the new instrument's
  semantics, not the historical retraction.
- The flip split now correctly limits the +17.34pp statement to 14 observed
  stop-first cases and leaves one unresolved. The continuation no-target structural
  fact is also properly separated from sample outcome in the corrected prose.
- The user-supplied regime context is clearly marked a-priori design context and says
  the intended regime remains untested. I do not treat that section as a data claim.
- No Pine or canonical result file changed in the pinned range. Green parity does not
  rescue the broken `tier_b_t1floor` caller because that boundary was not exercised by
  the tests, and byte-identical events do not validate newly added receipt semantics.
- The existing ignored candle cache supported local replay today. It is not durable
  evidence for a future clean checkout after the venue window moves.

## 3. Actionable items (reviewer's own list, if provided)

1. Repair the T1-floor caller/gate contract and make artifact promotion atomic -- **MEDIUM** -- `analysis/paper/tier_b_t1floor.py:110-129,639-685`; `tests/test_t1floor_gates.py:193-211` -- filter family maps or widen the contract, then add a caller-boundary regression.
2. Count only executable protective collisions, or relabel no-op arming transitions -- **MEDIUM** -- `analysis/paper/engine.py:898-904,1032-1074,1099-1135` -- regenerate D9 membership under a precise class definition.
3. Make collision alternatives fraction- and path-aware -- **MEDIUM** -- `analysis/paper/engine.py:942-951,1032-1043,1105-1133` -- store scoped candidate fills and simulate each named ordering, or narrow the receipt claim.
4. Implement and receipt the backing-target counterfactual -- **MEDIUM** -- `hip3-executor/analysis/weekend1.py:3-9`; `runs/2026-08-22_weekend1/ANALYSIS.md:3-8,418-427` -- emit durable touch evidence and correct/remove the unreproduced 6/7 claim.
5. Correct conviction statistics and clocks -- **MEDIUM** -- `hip3-executor/analysis/weekend1.py:700-752`; `src/hip3_executor/rules.py:164-175` -- standard medians, explicit denominators, and decision-time R:R membership.
6. Reframe remaining MMQB/conviction prose as an upper-bound opportunity census -- **MEDIUM** -- `runs/2026-08-22_weekend1/ANALYSIS.md:169-179,273-325,429-446` -- remove causal, controlled-swap, and executable-volume language.
7. Reconcile current safety documentation with the binding pre-live gate -- **MEDIUM** -- `hip3-executor/README.md:41-50,75-105` -- state current limitations and restore durable flatten and candle/touch receipt requirements.
8. Finish round-once roster fee algebra -- **LOW** -- `analysis/paper/tier_b_exits.py:336-376,425-455` -- derive net from roster gross minus roster fees, return side count, and test the invariant.

