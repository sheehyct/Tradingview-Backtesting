<!--
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-20 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of `bef6dae^..fffbacb` on `main`, captured 2026-08-08
> (TVB-20 post-session). Lightly ASCII-normalized (em-dashes -> --, curly quotes -> straight);
> wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-20 -- audit fold-ins, layering-arc alignment, and v6.1 CONTROL strategy port
- **Reviewed:** `bef6dae^..fffbacb` on `main` (5 commits, 34 paths)
- **Reviewer:** OpenAI Codex (GPT-5)
- **Overall verdict:** NEEDS-CHANGES

## 2. Verbatim audit

### Verdict

NEEDS-CHANGES. The current control-port evidence is substantially sound: the Pine fork has exactly
the four declared diff hunks, its internal decisions do not read strategy state, all three committed
TV trade streams independently match the twin over the full common feed, the gate-warm-up mechanism
reproduces, and the default-false engine path regenerates every committed TVB-19 sweep row exactly.
The TVB-18/19 numerical fold-ins also reproduce. The remaining issues are proof and experiment-contract
defects: the reusable parity gate is not multiplicity-safe, the repaired TVB-19 harvester can certify a
partially legacy inventory as complete, and the layering records do not identify which control or which
component can support a revision of the pattern thesis. A smaller wording defect overstates the Pine
fork's realtime semantic equivalence. None of these findings erases the present 89/67/87 unique-event
match, but they should be corrected before this gate or the layering pre-registration becomes the next
research record.

### Findings

#### 1. MEDIUM -- The parity gate converts event streams to dictionaries, so duplicate events can disappear before PASS

- **Severity:** MEDIUM
- **Location:** `analysis/paper/port_parity.py:103-133,164-200`; `tests/test_port_parity.py:24-48`
- **Status:** CONFIRMED

`pick_offset()` scores every TV entry against a set of twin timestamps, and `compare()` then constructs
`twin_by_key` and `tv_by_key` with dictionary comprehensions. The subsequent set differences compare
only the surviving unique keys. `pass` checks those set differences plus price violations, but never
checks key multiplicity, stream cardinality, valid direction values, or the open-row convention.
Consequently, adding a second TV event with the same `(ts, action, dir, kind)` overwrites the first;
`tv_events_in_feed` can exceed `matched` while the gate still returns PASS. A duplicate twin event has
the mirror failure. The offset score has the same many-to-one property.

This is a structural false-pass path in the reusable gate, not evidence that the committed TVB-20 result
is currently wrong. I inspected all three raw trade artifacts: their in-feed event keys are unique, their
directions are only L/S, each has one final open row, and their in-feed cardinalities equal both the twin
and matched counts. The committed 89/67/87 result therefore survives an independent multiplicity check;
the code simply does not enforce the condition that made this run trustworthy.

Use `Counter` or an explicit one-to-one join, reject duplicate keys on either side, validate the direction
enum and open-row shape, and require `twin_events == tv_events_in_feed == matched` for PASS. Add synthetic
duplicate, invalid-direction, and multiple-open-row tests; the existing tests cover only warm-up behavior
and exit-comment parsing.

#### 2. MEDIUM -- A partial or empty TVB-19 rerun can mark a legacy merged inventory `complete: true`

- **Severity:** MEDIUM
- **Location:** `scripts/tvb19_harvest.mjs:16-35,183-198`; `analysis/reference/tv_deep/README.md:34-42`
- **Status:** CONFIRMED

The explicit roster-to-TV mapping fixes the SKHX naming defect, and a failed requested dataset now makes
the process exit nonzero. However, `TVB19_COINS` deliberately reduces `TARGETS` to a subset, the summary
merge retains all untouched prior rows, and the top-level `complete` flag is only `failures === 0` for
the current subset. The committed prior rows are explicitly documented as coming from the old fail-open
harvest with no recorded clean-floor state. A successful three-dataset partial rerun can therefore merge
30 legacy rows and write `complete: true`. An unknown selector yields zero targets, zero failures, a
rewritten prior summary, exit 0, and the same false complete flag.

That falls short of the returned audit's requested 33-dataset completeness guarantee and of commit
`9f11a74`'s "fail unless all datasets land" claim. It does not rewrite or invalidate the preserved 2026-08-05
dumps, whose limitation is now honestly documented, and it does not affect the TVB-20 parity arithmetic.
It does mean the forward repair can create a misleading provenance receipt.

Reject unknown or empty selectors. Distinguish `run_complete` from `inventory_complete`, and compute the
latter over the canonical 11 x 3 key set only when every merged row has no error and records
`history.state == "floor"`. A partial rerun over legacy rows should remain inventory-incomplete until the
other rows are re-harvested under the fail-closed path.

#### 3. MEDIUM -- The amended pattern hypothesis is not identified by the recorded control and composite layer

- **Severity:** MEDIUM
- **Location:** `docs/ATLAS_Timeframe_Continuity_Charter.md:64-73,132-150`; `CLAUDE.md:61-68`; `docs/experiments/tvb20_design_session_seed.md:10-33,45-80,82-89`; `docs/experiments/tvb20_control_port_parity.md:3-11`
- **Status:** CONFIRMED

The anti-tournament invariant itself remains explicit everywhere: dictionaries and timeframe sets are
chosen a priori, labeled censuses are ceiling maps, and per-pattern winner promotion is forbidden. The
problem is the causal contrast. Charter Section 5 defines the continuity-only baseline as the minimal
trigger/gate/state-stop system, and the new amendment says the Magnitude+Targets block is tested against
that baseline. The seed instead calls the v6.1 BF-exit system the layer-1+2 control, and the parity record
names that same v6.1 system as the control for both exit-design and Magnitude+Targets ablations.

The proposed layer-3 block also changes several things together: setup dictionary, trigger semantics,
target ladder, position-health/chop logic, and BF-proximity veto. A win by that package can establish that
the pre-committed package helped under its tested control. It cannot establish that patterns add
information beyond continuity, nor support the charter's stated "if it wins, revise 3.1" inference,
because exit and exhaustion changes are co-mingled. Conversely, a loss cannot isolate which component
failed. This matters even without any per-pattern selection.

The design seed says it is input rather than a completed pre-registration, so this is still cheap to fix.
Name the contrasts before Tier B: for example, C0 = the charter's minimal continuity-only system, C1 =
C0 plus the BF layer, and C2 = C1 plus the full M+T package. If Section 3.1 itself is to be adjudicated,
hold exit mechanics fixed in a pattern-only contrast or constrain the conclusion to the composite package;
do not infer pattern edge from the package result. Also state whether "continuity-only control" refers to
entry features only or to the whole strategy.

#### 4. LOW -- `ZERO SEMANTIC CHANGE` is true for historical decision logic, not realtime execution cadence

- **Severity:** LOW
- **Location:** `pine/tfc_bf_control_strategy.pine:3-20,92-122`; `docs/experiments/tvb20_control_port_parity.md:3-19,26-49`; `CLAUDE.md:51-55`
- **Status:** CONFIRMED

The four-hunk source claim is exact, and the order calls do not feed back into the internal machine. But
changing `indicator()` to a strategy with `calc_on_every_tick=false` intentionally changes realtime
execution: TradingView documents that such a strategy waits for the realtime bar's closing tick, whereas
an indicator executes on realtime updates. The inherited source header still describes entries and BF
touches as intrabar, while this research strategy observes the completed bar and fills at its close.
TradingView reference: https://www.tradingview.com/pine-script-docs/language/declaration-statements/

The parity report declares the close-fill residual, the live indicator is untouched, and the fork is
explicitly not a deployment claim, so this does not invalidate the historical control. Qualify the wording
as "zero historical source-logic change / full decision-event parity under the close-only convention" and
state that realtime alert timing is intentionally not parity-tested. Do not silently change the calc flag;
that would create a different research contract and historical/realtime repaint questions.

### Confirmed checks that are not findings

- **Range and snapshot:** `bef6dae^..fffbacb` contains the named five commits and exactly 34 changed paths;
  `git diff --check` passes. The only post-range commit changes HANDOFF and REVIEW_REQUEST pinning, so the
  reviewed code and artifacts at current HEAD are the `fffbacb` blobs.
- **Pine fork:** A direct watch-versus-control diff has exactly four hunks: header, declaration, order
  emission, and table title. The internal position machine permits at most one exit or entry action per
  bar, blocks same-bar re-entry, and never reads `strategy.position_size`
  (`pine/tfc_bf_control_strategy.pine:501-563`). `pine/tfc_bf_watch.pine` has the same Git blob before and
  after the range.
- **Current parity evidence:** Independent read-only reconstruction matches the committed result object for
  every symbol. Offset 0 scores 45/34/44 entries while both +/-300 scores are zero; matched counts are
  89/67/87, window counts are 58/34/18, beyond-feed counts are 2/0/6, and every twin-only/TV-only list is
  empty (`analysis/reference/port_parity/tvb20_parity_result.json:7-50,53-96,99-142`). All in-feed TV entry
  and exit prices equal their source bar close. Break/flip maximum absolute price delta is zero; the
  entry/BF residual medians and maxima reproduce. The beyond-feed events form coherent exit/next-entry
  continuations, and each empty-exit open trade contributes entry only.
- **Warm-up:** With `pine_gate_warmup=True`, all three reconstructed event streams begin at the first monthly
  boundary and match TV. With the default False behavior, the same feeds add 21 GOOGL, 27 TSLA, and 9 DRAM
  events before TV's first event. The implementation leaves first-bar opens unset only on the True path
  (`analysis/paper/engine.py:285-305,453-466`). A full in-memory rerun of all 864 Tier A cells regenerated
  all 9,504 symbol rows and all 864 rollups exactly, proving default-False isolation at artifact scale.
- **TVB-18 fold-in:** The corrected tool marks open positions at the last in-window 5-minute close, fails on
  an empty window, and passes its append-invariance test (`analysis/paper/compare_config.py:52-119`;
  `tests/test_compare_config.py:30-58`). The independent totals are control -5.58pp open / -33.18pp combined
  and variant -6.94pp / -22.38pp. The sensitivity CLI now prints both heat-conditioning and not-official
  caveats (`analysis/paper/freeze_slice.py:76-84`).
- **TVB-19 fold-in:** Comparing the pre-fix and regenerated JSONL files shows that only `med_pnl_pct`,
  `mfe_med_pct`, and `gb_med_pp` change in the 9,504 per-symbol rows; no other existing field changes. The
  864 rollups preserve every old field value and add exactly the five declared metrics. Manifest changes
  are limited to rerun timestamps and Git head. The executable SKHX identity check reproduces the committed
  aggregate artifact exactly after excluding its generation timestamp.
- **Frozen record and lookahead:** `events_week1.jsonl`, `scoreboard_week1.md`, and `roster_week1.json` have
  identical Git blobs at both range endpoints. The only changed Pine path is the new control fork; it adds
  no executable `request.security` call and contains no `lookahead_on`.
- **P/L and fees:** The report explicitly separates TV close fills from twin trigger/line prices and requires
  twin prices for cross-engine P/L (`docs/experiments/tvb20_control_port_parity.md:38-49`). Commission and
  slippage are both zero, no turnover claim is made, and no narrative treats raw TV performance fields as
  twin P/L.
- **Overfit discipline:** Apart from Finding 3's contrast ambiguity, no file or commit promotes a cell,
  pattern, or timeframe winner. The design seed is labeled pre-registration input, and the per-pattern
  promotion ban survives the charter and CLAUDE.md amendments verbatim in substance.
- **Validation:** `uv run pytest tests/ -q -p no:cacheprovider` passed 111 tests with 2 skipped; full Ruff
  passed for `analysis/` and `tests/`; Node syntax checks passed for the three changed harvest/deep-load
  scripts. Targeted fold-in/parity tests passed 10/10. The worktree remained clean before this audit file.

### Validation limits

- I did not run the live CDP harvester, recompile Pine in TradingView, or inspect the mounted chart. The
  script-copy identity, tab modified-stamp claim, compile result, mounted-state claim, and visual behavior
  remain live-state/prose evidence. The committed trade streams plus source diff strongly support historical
  behavior, but do not preserve a source hash/input receipt from the mounted TV instance.
- I did not regenerate live TV data or overwrite any committed result. The full sweep verification ran
  entirely in memory, and parity was invoked through `compare()` rather than its artifact-writing CLI.
- The parity result is feed- and sample-scoped: three symbols, one roughly 20.5k-bar 5-minute history per
  symbol, cold-started at the recorded chart floor. It is not proof of tick-live equivalence, accumulated
  live-chart state, non-tiling chart resolutions, or unseen regimes.

## 3. Actionable items (reviewer's own list)

1. Make the parity gate multiplicity-safe and fail closed on malformed trade streams -- **MEDIUM** --
   `analysis/paper/port_parity.py:103-133,164-200` -- compare key Counters or use an injective join, validate
   direction/open-row contracts, require cardinality equality, and add false-pass regression fixtures.
2. Separate per-run success from complete-inventory provenance in the TVB-19 harvester -- **MEDIUM** --
   `scripts/tvb19_harvest.mjs:16-35,183-198` -- reject empty/unknown subsets and require all canonical rows
   to carry clean-floor receipts before setting inventory complete.
3. Pre-register an identified control/variant matrix and limit conclusions to what each contrast isolates --
   **MEDIUM** -- `docs/ATLAS_Timeframe_Continuity_Charter.md:64-73,132-150`;
   `docs/experiments/tvb20_design_session_seed.md:10-33,77-89` -- distinguish minimal continuity, BF-layer,
   and full M+T-package controls; add a held-exit pattern contrast if Section 3.1 itself will be revised.
4. Qualify the port's zero-change language as historical decision parity, not realtime cadence parity --
   **LOW** -- `pine/tfc_bf_control_strategy.pine:3-20,92-122` -- retain the declared close-only contract and
   explicitly exclude live intrabar timing from the claim.

## Suggested prompt

Add: "Treat parity as a multiset/injective join: fail on duplicate event keys, malformed directions, or more
than one non-final open row, and require raw cardinality equality before PASS. For the layering pre-registration,
name C0/C1/C2 explicitly, hold non-pattern mechanics fixed for any claim about pattern information, and constrain
every conclusion to the component contrast that actually identified it. Distinguish historical source-logic
parity from realtime indicator cadence."

Verdict: NEEDS-CHANGES
