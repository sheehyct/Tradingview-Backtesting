<!--
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-24 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of 674c7f6^..e92e59c on main, captured 2026-08-15
> (TVB-24 post-session, including the pre-code TVB-25 preregistration).
> Lightly ASCII-normalized (em-dashes -> --, curly quotes -> straight);
> wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> docs/HANDOFF.md. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-24 -- audit/assessment fold, H8 TV mirror, parity gate, and TVB-25 exit prereg
- **Reviewed:** 674c7f6^..e92e59c on main (6 commits, 34 paths)
- **Reviewer:** OpenAI Codex (GPT-5)
- **Overall verdict:** NEEDS-CHANGES

## 2. Verbatim audit

### Verdict

NEEDS-CHANGES. This is not an objection to the experimental program, the large arm set, or
deliberate overfit ceiling-mapping. Those are explicitly allowed research instruments here, and
the new preregistration continues to label the composite, the short window, and the no-promotion
boundary honestly.

The committed TVB-24 numerical evidence is stronger than the verdict may suggest. I independently
re-ran the 9-cell parity comparison from the committed dumps and local feeds: all nine cells pass,
with 218 in-feed events matched, 111 pattern entries checked, zero twin-only or TV-only events, and
41 later TradingView events honestly excluded beyond the local feed. I also recomputed the
matched-exit, ATR-context, entry-containment, decision-close, and D1 identity-funnel diagnostics.
Their published values reproduce. The H8 Pine arm routing, floor ordering, and Wilder ATR update
match the Python engine on inspection, and no request.security call was added.

The changes requested below address three different contracts. First, the TVB-25 comparison named
as isolating the BF layer does not hold the state stop fixed and therefore cannot answer that named
question. Second, several tranche/stop collisions are not specified well enough for two independent
implementers to produce the same event stream. Third, the hardened TVB-24 evidence gates still have
adversarial false-PASS paths, including a partial run that can overwrite the canonical 9-cell parity
artifact. None of those findings demonstrates that the currently committed result numbers are
wrong; they do require correction before those guards or the TVB-25 preregistration are treated as
binding evidence.

### Findings

#### 1. HIGH -- The declared C0/C1 comparison does not isolate the BF layer

- **Severity:** HIGH
- **Location:** docs/experiments/tvb25_exit_round_prereg.md:47-54,120-159;
  docs/ATLAS_Timeframe_Continuity_Charter.md:75-87,118-127;
  analysis/paper/tier_b.py:64-76; analysis/paper/engine.py:294-331
- **Status:** CONFIRMED

The charter defines C0 as trigger + TFO gate + state stop and C1 as C0 plus the BF-exit layer
(docs/ATLAS_Timeframe_Continuity_Charter.md:75-82). The preregistration instead compares S0a
(state stop only) and S0b (state stop + flip) with committed A0b and says this isolates BF
(docs/experiments/tvb25_exit_round_prereg.md:47-54,122-159). A0b only overrides the arm cadence;
its inherited engine defaults are BF harvest + brk + flip, with no state-stop field
(analysis/paper/tier_b.py:64-76; analysis/paper/engine.py:294-331). S0a versus A0b therefore
replaces the state stop with an entire different exit family. S0b versus A0b replaces
state-stop-plus-flip with BF-plus-brk-plus-flip. Neither is a BF-only delta.

There is a second naming mismatch inside S0a itself. Charter Section 3.5 exits when the lowest
execution timeframe closes neutral or opposite. The preregistration uses only a strict break of
the prior hour's opposite extreme and calls that C0-pure
(docs/ATLAS_Timeframe_Continuity_Charter.md:118-127;
docs/experiments/tvb25_exit_round_prereg.md:47-50,126-127). That may be a useful, user-ruled
2-against variant, but it is narrower than the charter state and should be named as such unless
neutral closes are intentionally restored.

Finally, "identical stream/costs" repeats the occupancy error already corrected in TVB-23.
Different exits change when a one-position engine becomes flat and therefore which later trigger
opportunities can become realized entries. The shared trigger/candidate rule can be identical;
the realized entry streams need not be. The preregistered matched-entry diagnostic covers
D1/P1/P2/X1/PX, not S0a/S0b/A0b
(docs/experiments/tvb25_exit_round_prereg.md:122-170).

Before implementation, either add matched C1 arms that retain the chosen state stop while toggling
only the BF layer (and separately flip), or relabel A0b as an exit-family replacement/reference
rather than a BF isolation. Include S0a/S0b/the matched C1 arm/A0b in the shared-prefix and
matched-entry diagnostics. This preserves the exploratory comparison while preventing a family
replacement from being interpreted as component attribution.

#### 2. MEDIUM -- The TVB-25 exit state machine is not yet deterministic enough to build

- **Severity:** MEDIUM
- **Location:** docs/experiments/tvb25_exit_round_prereg.md:57-118,129-190;
  analysis/paper/patterns.py:80-91,257-267,349-383
- **Status:** CONFIRMED

The nine arms are exhaustively named and the headline fractions reconcile, but order-sensitive
mechanics remain unspecified:

- There is no global precedence table when a 5-minute bar contains more than one of: a tranche
  target, the P2 T1 floor, breakeven, BF touch, brk, flip, intrabar-3, structural stop, or ATR stop.
  D5 says risk exits close all remaining tranches, but does not say which event wins or at what
  price when multiple conditions occur on the same OHLC bar
  (docs/experiments/tvb25_exit_round_prereg.md:82-94).
- P2 assigns T2 through T5 but does not say what happens when the frozen ladder has fewer than five
  rungs. It also does not say whether all contained target rungs fill on one bar, how a gap past one
  or more targets affects later tranches, or whether the T1 floor/breakeven state can arm and fire
  on the same bar that first contains T2
  (docs/experiments/tvb25_exit_round_prereg.md:57-61,129-136).
- X1 does not define the fewer-than-three-rungs case, whether arming begins on the rung-3 bar or the
  next bar, or whether "the BF line" is the currently alive line, the entry snapshot, or an arming
  snapshot. A same-bar rung-3/BF touch and a line retired before arming are therefore undecidable
  from the document (docs/experiments/tvb25_exit_round_prereg.md:74-77,136).
- Intrabar-3 names the "entry hour's opposite side" but does not freeze the exact source bar and
  level, or state what the declared entry-bar degenerate case actually does
  (docs/experiments/tvb25_exit_round_prereg.md:87-92).
- Structural-stop anchors are said to be captured "at detection," although the developing 1H
  signal can be detected again on successive 5-minute bars. The current detector also already
  uses local variables named anchor/anchor2 for magnitude-ladder construction, while Signal has
  no stop field (analysis/paper/patterns.py:80-91,257-267,349-383). Use a distinct immutable
  stop_anchor with a declared source-bar index and snapshot clock. Define "degenerate" and the
  action when an anchor is non-finite, equal to entry, or already on the wrong side.
- "No floor" in P1 should explicitly mean no post-bank retrace floor; the arm still inherits D1's
  0.25% entry-distance floor. The fee rule also needs an exact partial-position formula: entry-fee
  allocation, per-tranche exit fees, treatment of the surviving open fraction, and rounding
  (docs/experiments/tvb25_exit_round_prereg.md:86,93-94,129-135,167-174).

The structural-stop table is broadly consistent with the canonical shapes: the X-1-2 rows use
bar0, 2-2 uses the prior directional bar, and 3-2/3-2-2 use the outside bar. The reversal guidance
permits a trap/inside extreme, however, while the table fixes the 1-3 and compound 1-3-1-2 families
to the 3. The latter is already flagged least-canonical; the former should also be labeled as the
chosen experimental anchor rather than presented as uniquely canonical
(docs/experiments/tvb25_exit_round_prereg.md:99-118).

This finding does not argue for fewer combinations. It asks for one deterministic state-transition
table, applied to all of them, before code. The predeclared rung-3 and 3x-ATR thresholds do not show
evidence of post-result tuning in this range; treat them as exploratory fixed values and report
neighborhood sensitivity later without selecting a winner.

#### 3. MEDIUM -- The three hardened guard families still accept missing or substituted evidence

- **Severity:** MEDIUM
- **Location:** analysis/paper/tier_b_t1floor.py:393-464,573-604;
  analysis/paper/round_census.py:46-91,147-183;
  tests/test_t1floor_gates.py:100-189
- **Status:** CONFIRMED

The row/field determinism guard is now genuinely bidirectional and duplicate-aware. The remaining
entry-stream and census guards are not:

- _first_divergence_is_exit([enter, exit], [enter, different_enter]) returns true because line
  460 accepts an exit on either side. At the first divergence, the second arm's entry is not yet
  downstream of a shared exit divergence; this mutation can represent a deleted/substituted exit.
- Symbol sets are checked only relative to the other present depth arms. Removing xyz:DRAM from
  all six in-memory maps leaves every set equal and all 15 pair checks passing.
- checked is the intersection of expected depth arms and produced arms. A missing whole arm reduces
  the pair matrix instead of failing exact-arm cardinality
  (analysis/paper/tier_b_t1floor.py:577-604).
- The census links an outcome to any entry with the same symbol/entry_ts, then checks only
  per-symbol closed count plus open count/direction. Flipping the direction of a real D2 roster
  exit still produces linked rows and an empty determinism mismatch list
  (analysis/paper/round_census.py:46-91,147-183).

The committed streams pass stronger checks: all expected arms are present, all 15 pairs have equal
observed symbol sets, and the current closed outcomes are linked. These adversarial cases expose
future certification gaps, not a demonstrated mutation in the committed artifacts. Add tests for
exit-versus-entry substitution, one symbol removed from every arm, one whole arm missing, a
flipped closed direction, a duplicated outcome, and a different closed event with the same
aggregate count. Require the exact expected arm set and initialize stream maps from the canonical
roster. When both streams have a next event at their first difference, both next events should be
exits; a strict prefix may pass only when the longer next event is an exit. Census an injective
Counter of authoritative event identities, not just totals.

#### 4. MEDIUM -- A partial parity run can overwrite the canonical 9-cell PASS

- **Severity:** MEDIUM
- **Location:** analysis/paper/pkg_parity.py:187-197,241-266,361-427;
  scripts/tvb23_pkg_harvest.mjs:125-150,153-213,215-279;
  tests/test_pkg_parity.py:60-145
- **Status:** CONFIRMED

Generation scoping correctly prevents a TVB-23 run from overwriting the TVB-22 artifact. It does
not protect completeness within TVB-23. main() accepts any arm tuple and any coin subset, and every
non-all-A invocation writes analysis/reference/pkg_parity/tvb23_parity_result.json
(analysis/paper/pkg_parity.py:369-427). With Path.write_text intercepted so no file changed,
main(["--arms", "D1", "GOOGL"]) returned zero and targeted that canonical path with all_pass=true
and one result. A successful smoke cell can therefore replace the committed 3x3 certificate.

The Python gate also does not validate the wrapper metadata that identifies the harvested cell.
The harvester records coin, requested arm, symbol, interval, history-floor state, strategy_count,
and total_trades, but setArmExpr does not read the arm value back, the dump selects the first
matching computed strategy when multiple copies exist, and parity ignores those metadata fields
(scripts/tvb23_pkg_harvest.mjs:125-194,215-275;
analysis/paper/pkg_parity.py:241-266,361-366). The committed nine dumps are healthy -- I checked
the exact matrix, interval 5, history floor, one strategy, correct symbol/arm labels, and
total_trades == len(trades) -- but those facts are outside the executable PASS predicate.

Require the exact three coins and exact three TVB-23 arms before writing the canonical result.
Subset runs should write a scope-named smoke artifact or no artifact. Validate the dump's coin,
arm, arm_input, tv_symbol, interval, floor state, finite mintick, strategy_count == 1, and trade
cardinality before joining events; read the arm input back after setting it. Add a main-level
regression test proving a 1-cell PASS cannot replace the 9-cell pin.

#### 5. MEDIUM -- "Exits in isolation" does not yet bind the full entry contract

- **Severity:** MEDIUM
- **Location:** analysis/paper/t1floor_diagnostics.py:137-225,229-271;
  tests/test_t1floor_diagnostics.py:73-108
- **Status:** CONFIRMED

The matched-exit receipt keys an entry by symbol, entry timestamp, direction, pattern, and trigger.
It does not compare entry price or the frozen ladder, even though either difference can change P&L
or the later exit mechanics and invalidate an exits-only attribution. Entries and outcomes are
also accumulated in dictionaries, so a duplicate identity can overwrite rather than fail before
the final dictionary cardinality check
(analysis/paper/t1floor_diagnostics.py:137-176).

I independently checked the current 41 all-six identities: entry prices and frozen ladders are
equal across all six arms, and 37 are closed everywhere. Thus the committed exits-in-isolation
reading is supported by the actual data. The test and receipt simply do not enforce the property
their interpretation needs. Make the matched key or an explicit equality assertion include price,
ladder, and any frozen entry-time state; compare raw Counter cardinality before converting to
dictionaries; and add price/ladder/duplicate mutations. Reuse that stronger contract for the
TVB-25 D1/P1/P2/X1/PX diagnostic.

#### 6. LOW -- Receipt provenance and "seed-exact" wording exceed the persisted inputs

- **Severity:** LOW
- **Location:** analysis/paper/t1floor_diagnostics.py:229-271;
  analysis/paper/entry_audit.py:189-219;
  analysis/paper/pkg_parity.py:187-197,361-366;
  scripts/tvb23_pkg_harvest.mjs:253-275;
  pine/tfc_mt_package_strategy.pine:154-167
- **Status:** CONFIRMED

The diagnostic receipts hash event/result artifacts, but not every derived input. ATR context and
entry containment depend on archived bars; entry audit also depends on roster minticks and the
executed code. The tests recompute correctly from the current checkout, but the receipt alone
cannot prove which bars, roster, or implementation produced it
(analysis/paper/t1floor_diagnostics.py:229-271;
analysis/paper/entry_audit.py:189-219).

Similarly, twin_events reads archived tv_deep bars and aligns their starting timestamp to chart
metadata. The TradingView dump persists chart edges and strategy trades, not the loaded bar values
or an ATR trace. The 9/9 decision parity is strong evidence that the implementations behaved the
same, but it cannot prove literal byte-identical bar inputs or ATR seeds. Narrow "seed-exact" to
"same nominal cold-start span with observed decision parity," or persist/hash the exact TV bars
or a per-completed-hour ATR trace. Add bar, roster, mintick, and executed-code hashes to the
diagnostic receipts.

### Confirmed checks that are not findings

- **Range and snapshot:** The pinned range is linear and contains six commits and 34 paths;
  git diff --check 674c7f6^..e92e59c passes. Current HEAD is 128668a, one later docs-only review
  routing commit that changes docs/HANDOFF.md and docs/reviews/REVIEW_REQUEST.md; no reviewed code
  or evidence artifact changed after e92e59c. The informal "7 commits" count includes that
  out-of-range routing commit; the pinned audit range itself contains six.
- **9-cell parity replay:** Re-running the committed gate produced:

  | Coin | Arm | In-feed matched | In declared window | TV events beyond feed |
  |---|---:|---:|---:|---:|
  | GOOGL | D1 | 8 | 4 | 0 |
  | GOOGL | DINF | 5 | 4 | 1 |
  | GOOGL | D1ATR | 8 | 4 | 2 |
  | TSLA | D1 | 12 | 10 | 4 |
  | TSLA | DINF | 8 | 6 | 4 |
  | TSLA | D1ATR | 28 | 22 | 4 |
  | DRAM | D1 | 81 | 72 | 9 |
  | DRAM | DINF | 27 | 19 | 6 |
  | DRAM | D1ATR | 41 | 34 | 11 |

  Total: 218 matched, 175 in the declared July window, 41 beyond feed, 111 pattern checks, 9/9
  PASS. The local twin feeds end around 2026-08-05 while the declared window ends 2026-08-03;
  all 41 exclusions are later than the feed end and therefore outside the declared window. The
  committed result records the exact 3x3 matrix and all nine pass
  (analysis/reference/pkg_parity/tvb23_parity_result.json:1-486).
- **Harvest shape:** All nine raw dumps declare the expected coin/arm/symbol, interval 5, history
  termination at floor, one matching strategy, finite mintick, and exact list/count
  reconciliation. Their chart histories begin 2026-06-01 and extend beyond the local twin feed.
- **H8 semantics:** D1ATR is tested before the shared D1 prefix; fixed-percent and ATR veto forms
  are mutually exclusive; floor distance is directional and strict; the floor runs before the
  extended no-target skip; and the counter split matches the engine
  (pine/tfc_mt_package_strategy.pine:255-268,1191-1242;
  analysis/paper/engine.py:636-723). Pine ATR uses the same first-bar TR, first-window SMA seed,
  Wilder recursion, and completed-1H update order as _Atr
  (pine/tfc_mt_package_strategy.pine:301-338;
  analysis/paper/engine.py:347-397). No executable request.security call was added in the range.
- **Diagnostics:** The matched receipt recomputes 41 identities shared by all six arms and 37
  closed everywhere; D1 and D5 matched sums are 38.3996pp and 66.2171pp. ATR context recomputes for
  11 symbols. Entry audit recomputes 765 entries with 11 outside their entry bar, all on the
  pessimistic side of the trade. D1's roster decision-close benchmark is 61 favorable / 41
  adverse with +8.2503pp summed signed difference. The instrumented D1 funnel recomputes 4,111
  candidate evaluations -> 682 identities, 569 repeated identities, max 12 evaluations per
  identity (analysis/paper/t1floor_diagnostics.py:137-225;
  analysis/paper/entry_audit.py:70-186).
- **Research language:** The charter permits labeled deliberate-overfit censuses as ceiling maps,
  never promotion (docs/ATLAS_Timeframe_Continuity_Charter.md:69-73). The TVB-25 document calls the
  composite a reading, labels the short window sign-indeterminate, binds conclusions to named
  contrasts, and explicitly defers promotion/live mechanics
  (docs/experiments/tvb25_exit_round_prereg.md:65-70,146-163,194-204). The arm count and exploratory
  breadth are not findings.
- **Validation suite:** Full pytest passed 205 tests with 2 skipped under python -B with the pytest
  cache disabled. Ruff passed for analysis/ and tests/. node --check passed for
  scripts/tvb23_pkg_harvest.mjs. The worktree was clean before this audit file was created.

### Validation limits

- I did not launch TradingView, compile Pine in the editor, inspect the mounted study, or repeat the
  browser-side harvest. TV-side conclusions rely on the committed dumps plus inspection of the
  harvesting code.
- I did not regenerate or overwrite committed research artifacts. Replays, receipt
  recomputations, metadata checks, and adversarial mutations were read-only or in memory.
- No TVB-25 implementation exists in the reviewed range, so the preregistration review assesses
  whether its contract is buildable; it cannot validate future event streams or results.
- Historical decision parity does not establish realtime cadence, execution, funding, slippage,
  portfolio accounting, or live readiness. Those are declared outside this experimental round and
  are not the basis for the NEEDS-CHANGES verdict.

## 3. Actionable items (reviewer's own list)

1. Repair or relabel the C0/C1 identification -- **HIGH** --
   docs/experiments/tvb25_exit_round_prereg.md:47-54,122-170 -- retain the chosen state stop in the
   BF comparator if the claim is BF isolation; otherwise call A0b a family-replacement reference.
   Distinguish the 2-against state variant from charter C0 and extend matched-entry diagnostics to
   the ladder-bottom arms.
2. Commit a dated deterministic exit-state amendment before code -- **MEDIUM** --
   docs/experiments/tvb25_exit_round_prereg.md:57-118,129-190 -- define collision priority, fill
   prices, P2 short-ladder fallbacks and same-bar arming, X1 BF snapshot/arming, intrabar-3 level,
   immutable stop_anchor semantics, fee allocation, and exact window endpoints.
3. Close the remaining stream/census mutations -- **MEDIUM** --
   analysis/paper/tier_b_t1floor.py:449-464,573-604;
   analysis/paper/round_census.py:46-91,147-183 -- require exact arms and canonical symbol scope,
   reject exit-versus-entry first differences, and compare injective closed/open event identities;
   add the six adversarial regressions described in Finding 3.
4. Protect the canonical parity artifact -- **MEDIUM** --
   analysis/paper/pkg_parity.py:361-427; scripts/tvb23_pkg_harvest.mjs:125-279 -- only a validated
   exact 3x3 run may write tvb23_parity_result.json; scope smoke outputs separately, validate all
   wrapper metadata, and read the selected arm back before harvesting.
5. Strengthen matched-entry identity -- **MEDIUM** --
   analysis/paper/t1floor_diagnostics.py:137-225 -- assert equal entry price, ladder, and frozen
   state; reject duplicate raw identities/outcomes; carry that contract into TVB-25.
6. Bind provenance and narrow the seed claim -- **LOW** --
   analysis/paper/t1floor_diagnostics.py:229-271;
   analysis/paper/entry_audit.py:189-219; pine/tfc_mt_package_strategy.pine:154-167 -- hash bars,
   roster/minticks, and executed code, and either persist exact TV bar/ATR evidence or describe the
   observed parity without claiming literal seed identity.

## Suggested prompt

Before TVB-25 code, amend the preregistration so an independent implementer can derive one exact
event stream: define a matched state-stop-on/state-stop-plus-BF contrast, occupancy-aware entry
diagnostics, and a single per-bar priority/fill table for tranche targets, floors, BF, state,
intrabar-3, and structural/ATR stops. Then adversarially prove that removing any expected arm,
symbol, exit, open mark, parity cell, or dump identity makes the relevant gate fail.

Verdict: NEEDS-CHANGES
