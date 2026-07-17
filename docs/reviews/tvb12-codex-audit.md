<!--
External review of TVB-12. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-12 External Audit -- Codex CLI / GPT-5.6 Sol Max (verbatim source, read CRITICALLY)

> External review of commit range `f97646e^..65d9cba` captured 2026-07-17
> (TVB-12 post-session). Lightly ASCII-normalized (em-dashes -> --, curly quotes -> straight);
> wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-12 -- audit fold-in, bounded replay, and ShortChamp MU5
- **Reviewed:** `f97646e^..65d9cba` on `main` (7 commits, 14 changed files)
- **Reviewer:** Codex CLI / GPT-5.6 Sol Max
- **Overall verdict:** NEEDS-CHANGES

## 2. Verbatim audit

### Bottom line

NEEDS-CHANGES. The fail-closed collector is a material improvement, and the committed raw rows
reproduce the reported acceptance counts, anchors, +248.70 percent perp ceiling, 5m short result,
and three reported Spearman coefficients. Those passes do not support the session's stronger
closure language for two reasons:

1. The shipped ShortChamp indicator does not implement its live clock contract. Its trigger
   snapshot is updated before the trigger is tested on the final child bar, and its 60m state exit
   is not gated to a confirmed chart-bar close.
2. The comparator mechanically calls every 80 percent match DRIFT without testing whether the
   unmatched trades are boundary-explainable. It also does not cap the comparison at the common
   window end. Thus `0 SUSPECT` does not exclude the stale-nearby-config case the replay was meant
   to test.

The new collector has no elapsed-time acceptance path and all 68 committed grid rows satisfy its
recorded nonce/input/totals checks. However, its report-to-table join is still a non-unique
fingerprint, so "fully causal" is stronger than the implementation. Finally, 54 compared IDs out
of 1,438 eligible original IDs are a targeted consistency check, not verification of the whole
TVB-11 record or the full 10-config x 7-perp generalizer ranking.

### Scope and range sanity

The user-pinned range is correct:

Command:

```powershell
git log --oneline f97646e~1..65d9cba
```

Output:

```text
65d9cba docs(tvb): TVB-13 seed addendum -- BF comprehension guard, fractality note, fixture not-cherry-picked correction
ceb9640 docs(tvb): TVB-12 session end -- exit-arc redirect recorded, TVB-13 seeded, light-scope review requested
b301e77 feat(tvb): Winner: ShortChamp MU5 [TVB-12] -- live watch indicator for the replay-verified 5m short champion
a3a6c74 feat(tvb): bounded replay COMPLETE -- TVB-11 record verified (36 CLEAN/18 DRIFT/0 SUSPECT), direction repair mapped
d3e01e6 feat(tvb): anchors PASS on hardened gate -- C1/C3/C6 trade-for-trade equal, bindOk fixed to closed-side totals
00c4cb8 feat(tvb): fail-closed replay collector + champion v2 nonce echo (audit F1/F2/F4 remediation)
f97646e docs(tvb): TVB-11 review RETURNED -- audit committed, critical synthesis + remediation queue in HANDOFF
```

Command:

```powershell
git diff --name-status f97646e~1 65d9cba
```

Output:

```text
M .session_startup_prompt.md
M docs/HANDOFF.md
A docs/experiments/tvb12_replay_anchor2.jsonl
A docs/experiments/tvb12_replay_anchor2_gatedebug.jsonl
A docs/experiments/tvb12_replay_cells.json
A docs/experiments/tvb12_replay_compare.json
A docs/experiments/tvb12_replay_plan.md
A docs/experiments/tvb12_replay_run.jsonl
M docs/reviews/REVIEW_REQUEST.md
A docs/reviews/tvb11-codex-audit.md
M pine/tvb_exp_champion.pine
A pine/winner_shortchamp_mu5.pine
A scripts/tvb12_replay_collect.mjs
A scripts/tvb12_replay_compare.mjs
```

### Finding 1 -- HIGH -- ShortChamp's live clock ordering violates both the entry and state-exit contracts

The short-side comparisons themselves are mostly mirrored correctly. The natural trigger is one
tick below `prev_al`; `ratchet_c` uses `math.min`, requires a tick below the running low, and clears
on fill or full `gate_up`; only `lower_test` harvests
(`pine/winner_shortchamp_mu5.pine:164-186`, `:188-215`). The
`request.security` tuple is also the accepted completed-value idiom: every requested value is
offset and the call uses `lookahead_on` (`pine/winner_shortchamp_mu5.pine:97-102`). There is no
unoffset lookahead leak.

The only explicit post-harvest clear sites are full `gate_up` on `exit_last` and a re-entry fill
(`pine/winner_shortchamp_mu5.pine:207-215`), so no residual long-side `gate_dn` clear survived.
The `exit_last` expression is still evaluated intrabar as discussed below; rollback means only the
closing execution commits that persistent clear, but the code does not keep the live surface
strictly close-only.

The entry clock is nevertheless wrong for the advertised live indicator:

- `arm_last` identifies the final chart bar inside the 15m period
  (`pine/winner_shortchamp_mu5.pine:49-51`).
- On that bar, the script first folds the current bar's low into `a_low`, then assigns that
  current-period value to `prev_al` (`pine/winner_shortchamp_mu5.pine:53-61`).
- Only afterward does it calculate `prev_al - mintick` and test the current low
  (`pine/winner_shortchamp_mu5.pine:210-215`).

Therefore, on every final child bar, `prev_al <= low` by construction and
`low <= prev_al - mintick` cannot be true. On a 5m chart this suppresses breaks occurring in the
third child bar. On the explicitly supported 15m chart, every bar is both `arm_new` and
`arm_last`, so the indicator cannot issue any entry at all. The same ordering was inherited from
the long watch surface, but mirroring an existing defect does not satisfy the stated "prior
COMPLETED 15m bar" contract.

The state-exit predicate is directionally correct (`not gate_dn`), but its live timing is not.
`exit_last = time_close == time_close(EXIT_TF)` is true for the whole final child bar, not only its
closing update, and the exit condition has no `barstate.isconfirmed` guard
(`pine/winner_shortchamp_mu5.pine:49-51`, `:202-208`). An indicator executes on every realtime
update. It can therefore emit a state-exit condition when D/W/M alignment goes grey intrabar even
if DOWN alignment is restored by the actual 60m close. TradingView documents both the per-tick
indicator execution/rollback model and that only the closing update is confirmed:
https://www.tradingview.com/pine-script-docs/language/execution-model/. Its alert documentation
also identifies this exact intrabar-true/close-false pattern as repainting:
https://www.tradingview.com/pine-script-docs/concepts/alerts/.

Command:

```powershell
Select-String -Path 'pine/winner_shortchamp_mu5.pine' -Pattern 'arm_last\s*=|exit_last\s*=|prev_al :=|not gate_dn|low <= eff_trig' | ForEach-Object { '{0}: {1}' -f $_.LineNumber, $_.Line.Trim() }
```

Output:

```text
50: arm_last  = time_close == time_close(ARM_TF)
51: exit_last = time_close == time_close(EXIT_TF)
61: prev_al := a_low
204: if pos == -1 and exit_last and not gate_dn
212: if pos == 0 and gate_dn and not na(prev_al) and low <= eff_trig
```

Fix the snapshot ordering so the completed 15m low is preserved before the new period starts, and
gate the state exit to the confirmed final child bar. Add deterministic 5m and 15m fixtures that
exercise breaks in each child-bar position plus a grey-then-DOWN realtime recovery on the final
60m child bar. Until that passes, this should not be treated as a reliable live alert surface.

### Finding 2 -- HIGH -- The comparator does not implement the plan's semantic DRIFT test and can mask contamination

The plan defines CLEAN as equal overlap trades, DRIFT as differences confined to
window-boundary-explainable trades, and SUSPECT as a categorical mismatch
(`docs/experiments/tvb12_replay_plan.md:58-69`). The comparator implements something materially
weaker:

- It applies only a lower bound, `entry >= max(loaded_first)`, and never applies the common window
  end (`scripts/tvb12_replay_compare.mjs:42-47`).
- It maps originals by entry time/direction, does not consume matches one-to-one, and does not
  compare quantity, profit, commission, or exit reason (`scripts/tvb12_replay_compare.mjs:48-57`).
- Most importantly, it assigns DRIFT solely when `matched / max(lengths) >= 0.8`
  (`scripts/tvb12_replay_compare.mjs:58-60`). It never checks where the unmatched trades occur or
  whether a boundary/state explanation exists.

A wrong or stale nearby configuration that shares 80 of 100 trades is therefore called DRIFT, not
SUSPECT. That is a plausible contamination shape for adjacent BF/gate variants; the threat need
not be a wholesale unrelated list. The 0.8 cutoff was not stated in the pre-run acceptance
criteria, which declared the semantic boundary test instead.

The stored 36/18/0 output is mechanically reproducible:

Command:

```powershell
node scripts/tvb12_replay_compare.mjs docs/experiments/tvb12_replay_run.jsonl
```

Output:

```text
{
 "compared_cells": 54,
 "verdict_counts": {
  "DRIFT": 18,
  "CLEAN": 36
 },
 "new_evidence_cells": 14
}
DRIFT HIP3XYZ:MUUSDC.P_tf5_slow3_state_short_ss_ratc_a15_x60 matched=0.8947 netDelta=0.795pp
DRIFT HIP3XYZ:MUUSDC.P_tf5_ctrlA4_state_both_off_a15_x15 matched=0.9643 netDelta=-1.129pp
DRIFT HIP3XYZ:MUUSDC.P_tf5_slow3_state_both_ss_ratc_a15_x60 matched=0.9565 netDelta=0.716pp
DRIFT HIP3XYZ:MUUSDC.P_tf15_ctrlA4_state_both_off_a15_x15 matched=0.9891 netDelta=-1.318pp
DRIFT HIP3XYZ:MUUSDC.P_tf15_slow3_flip_both_ss_ratc_a15_x60 matched=0.9792 netDelta=0.324pp
DRIFT HIP3XYZ:MUUSDC.P_tf15_slow3_flip_both_off_a15_x60 matched=0.95 netDelta=0.301pp
DRIFT NASDAQ:MU_tf5_slow3_flip_long_off_a5_x30 matched=0.9474 netDelta=27.724pp
DRIFT NASDAQ:MU_tf5_ctrlA4_state_both_off_a15_x15 matched=0.9503 netDelta=4.605pp
DRIFT NASDAQ:MU_tf15_ctrlA4_state_both_off_a15_x15 matched=0.9976 netDelta=1.093pp
DRIFT NASDAQ:MU_tf60_ctrlA4_state_both_off_a60_x60 matched=0.9994 netDelta=0.975pp
DRIFT HIP3XYZ:HIMSUSDC.P_tf15_slow3_flip_long_ss_recycle_a15_x60 matched=0.9375 netDelta=2.017pp
DRIFT HIP3XYZ:HIMSUSDC.P_tf15_full6_flip_long_ss_recycle_a15_x60 matched=0.9375 netDelta=1.984pp
DRIFT HIP3XYZ:HIMSUSDC.P_tf15_ctrlA4_flip_long_ss_recycle_a15_x60 matched=0.9375 netDelta=1.984pp
DRIFT HIP3XYZ:HIMSUSDC.P_tf15_slow3_flip_long_ss_ratc_a15_x60 matched=0.9375 netDelta=1.88pp
DRIFT HIP3XYZ:HIMSUSDC.P_tf15_full6_flip_long_ss_ratc_a15_x60 matched=0.9333 netDelta=1.892pp
DRIFT HIP3XYZ:HIMSUSDC.P_tf15_ctrlA4_flip_long_ss_ratc_a15_x60 matched=0.9333 netDelta=1.913pp
DRIFT HIP3XYZ:HIMSUSDC.P_tf15_slow3_flip_long_ss_recycle_a15_x15 matched=0.9412 netDelta=2.1pp
DRIFT HIP3XYZ:SILVERUSDC.P_tf15_slow3_flip_long_ss_ratc_a15_x60 matched=0.9722 netDelta=-0.986pp
```

But a read-only recomputation that also requires each closed trade to exit by the common available
end changes 13 of the 18 DRIFT labels to CLEAN. The 54-cell counts become 49 CLEAN / 5 DRIFT, with
25 replay-only right-tail trades removed:

Recomputation: the exact combined read-only Node command is reproduced under
"Exact JSONL recomputation command" below.

Output:

```text
rows=54
shipped: CLEAN=36 DRIFT=18 SUSPECT=0
bounded_to_common_end: CLEAN=49 DRIFT=5 SUSPECT=0
verdict_changes=13
removed_replay_right_tail_trades=25
```

The five residual DRIFTs may be genuine path-dependent boundary drift, but the artifact does not
prove that. Three contain a `price_or_exit_mismatch` on a trade with the same entry time and
direction and are still labeled DRIFT (`docs/experiments/tvb12_replay_compare.json:120-139`,
`:186-205`, `:252-271`; corresponding raw replay rows
`docs/experiments/tvb12_replay_run.jsonl:6`, `:9`, `:12`). Independent raw parsing found entry-price
differences of 1.349, 0.479, and 0.479 on those three matched-time trades. A shifted-floor governor
state could be the cause, but no committed trace establishes it; the comparator simply assumes
the conclusion from the 0.8 fraction.

There is also a pre-declaration scope mismatch. The plan says R4 has no reproduction target
(`docs/experiments/tvb12_replay_plan.md:70-72`), while the script compares every replay ID that
happens to exist in the original map (`scripts/tvb12_replay_compare.mjs:74-80`). Eight R4 rows
enter the headline counts: 5 CLEAN and 3 DRIFT. R1-R3 alone are 31 CLEAN / 15 DRIFT.

Replace the scalar threshold with a true common-window, one-to-one diff that emits the unmatched
trade timestamps and fields. Compare quantity and exit semantics as well as time/prices. A DRIFT
label should require an explicit boundary/path attribution; an unexplained interior mismatch must
remain SUSPECT. Keep R4 out of the predeclared reproduction tally. Regenerate the comparison JSON
and the affected prose before accepting F1 closure.

### Finding 3 -- MEDIUM -- The collector is improved and the committed rows pass, but the report join is not fully causal

The important pass comes first. `settleAndRead()` has one acceptance branch, requires the fresh
nonce/table echo plus entity input readback plus report/table totals on consecutive stable polls,
and returns failure at timeout (`scripts/tvb12_replay_collect.mjs:293-343`). There is no
engine-only branch and no time-based success escape. All 68 committed grid records are accepted on
attempt 1, carry 68 unique nonces and windows, and their stored nonce/input/symbol/TF/BF/totals
fields pass an independent recheck. All report sources in those rows say they bound by entity ID.
The three anchor rows also have `champion_ok`, base readback, entity binding, and full trade-list
equality (`docs/experiments/tvb12_replay_anchor2.jsonl:1-3`).

Recomputation: the exact combined read-only Node command is reproduced under
"Exact JSONL recomputation command" below.

Output:

```text
grid_rows=68
failures: accepted=0 attempt1=0 via=0 nonce_table=0 nonce_applied=0
          cell_echo=0 symbol_table=0 symbol_applied=0 tf_table=0
          tf_applied=0 bf=0 closed_bind=0 open_bind=0 net_bind=0
          list_len=0 report_id_bound=0 window=0
unique_nonces=68 elapsed_ms_min=6021 elapsed_ms_max=8050
anchors=3 champion_ok=3 base_applied_ok=3 base_id_bound=3 diff_equal=3
```

The remaining gap is the report-to-table link. The nonce exists only in the Pine table, not in
`reportData`. `bindOk` joins them using only closed-trade count, open-trade count, and closed net
to one cent (`scripts/tvb12_replay_collect.mjs:324-332`). The stability key adds only list length
and table total net, not any trade content (`scripts/tvb12_replay_collect.mjs:338-341`). The report
lookup also falls back from entity ID to exact description (`scripts/tvb12_replay_collect.mjs:197-235`).
A stale or wrong report with the same coarse totals can therefore pass while carrying a different
trade list.

This is not merely a theoretical hash collision. Applying the collector's three-field fingerprint
to the 1,438 accepted non-variant TVB-11 reports yields 241 multi-ID collision groups; 35 groups
contain different trade lists:

Recomputation: the exact combined read-only Node command is reproduced under
"Exact JSONL recomputation command" below.

Output:

```text
accepted_nonvariant_reports=1438
fingerprint_collision_groups=241
groups_with_different_trade_lists=35
```

The actual 68-row replay shows no evidence that this happened: every stored report used ID
binding, and its fresh table/report values agree. The finding is that the advertised causal proof
is non-injective, so an adversarial stale-report path remains. Add a report-side generation token
if TradingView exposes one; otherwise echo and bind a deterministic digest over the complete
closed trade list (not merely the first 60 table rows). Fail instead of falling back by name when
entity binding is unavailable.

One smaller contract mismatch should be fixed at the same time. The plan promises session and
subsession verification for every run (`docs/experiments/tvb12_replay_plan.md:16-22`), but both
checks are conditional on `isRthMirror()` (`scripts/tvb12_replay_collect.mjs:309-323`). All
committed rows happen to report `regular`, so this did not alter this batch; the code should still
verify the expected session for every supported symbol rather than silently exempting perps.

### Finding 4 -- MEDIUM -- "Record VERIFIED" and "rankings stand" exceed the replay's targeted coverage

The plan's local heading is appropriately narrow: "TVB-11 record VERIFIED on this subset"
(`docs/experiments/tvb12_replay_plan.md:107-121`). The session summary drops or outruns that
qualification: the top status says "TVB-11 record VERIFIED, F1/F4 closed"
(`docs/HANDOFF.md:11-14`), and the standing verdict says the champion-search rankings changed from
unverified to verified (`docs/experiments/tvb12_replay_plan.md:159-166`).

The raw coverage is much narrower:

Recomputation: the exact combined read-only Node command is reproduced under
"Exact JSONL recomputation command" below.

Output:

```text
accepted_original_rows=1498
eligible_nonvariant_ids=1438
compared_ids=54
coverage_pct=3.76
compared_engine_path=40
compared_echo_path=14
```

The subset is deliberately targeted, not random. That is useful for checking named conclusions,
but it cannot retroactively validate the unobserved original rows against a per-record stale-read
threat. The same limit applies to the generalizer ranking. Stage B selected the best median among
10 configs across 7 perps (`docs/experiments/tvb11_champion_prereg.md:401-421`). TVB-12 reruns all
10 configs on only HOOD/HIMS/RKLB and reruns only the already-selected Generalizer on the other
four perps (`scripts/tvb12_replay_collect.mjs:115-132`, `:157-165`). The reported Spearman values
for those three full blocks reproduce exactly, but the replay cannot recompute the 10-config
seven-perp median ranking. The original top median is 5.807 percent versus 3.758 percent for rank
2; the four unrerun competitor values remain part of that ordering.

Use precise closure language: the new collector remediation is operational for future runs; the
three anchors and targeted 54-cell subset are consistent with the original; the 5m short and
+248.70 percent named cells reproduce; and no tested cell showed wholesale contamination. Keep
the original 736-row provenance gap open. If the session wants to call the Stage B ranking
verified, replay the complete 10-config x 7-perp matrix on common windows; otherwise retain
"targeted subset consistency check" and the three-symbol rank-stability result.

### Recomputed claims and passing checks

The following claims do reproduce from the committed artifacts:

- Range: 7 commits and 14 changed files.
- Collection: 68/68 grid rows accepted, zero recorded rejections, all attempt 1, all via
  `nonce+engine+bind`; 3/3 anchors have equal closed trade lists.
- Stored comparator output: 36 CLEAN / 18 DRIFT / 0 SUSPECT across 54 compared IDs. Finding 2
  limits the meaning of those labels; it does not dispute that the script emitted them.
- Perp 15m ceiling: replay 248.7007 percent vs original 248.7007 percent, equal to two decimals
  (`docs/experiments/tvb12_replay_run.jsonl:5`;
  `docs/experiments/tvb11_champion_a1.jsonl:622`).
- 5m short champion: replay 13.7061 percent / 19 trades vs original 12.9115 percent / 17 trades
  (`docs/experiments/tvb12_replay_run.jsonl:1`;
  `docs/experiments/tvb11_champion_a1.jsonl:343`). With a proper common end, the original 17
  trades match and the two extra replay trades are right-tail additions.
- Stage B full-block ranks on the three rerun symbols: Spearman 1.000, 0.988, and 1.000; top-1
  is unchanged on all three.
- Syntax: both new MJS files pass `node --check`.

Command:

```powershell
node --check scripts/tvb12_replay_collect.mjs
if ($LASTEXITCODE -eq 0) { 'collector syntax: OK' }
node --check scripts/tvb12_replay_compare.mjs
if ($LASTEXITCODE -eq 0) { 'comparator syntax: OK' }
```

Output:

```text
collector syntax: OK
comparator syntax: OK
```

#### Exact JSONL recomputation command

This is the read-only inline command used for the aggregate collector, comparator, collision,
coverage, ceiling, short-champion, and rank checks quoted above. It writes no file.

```powershell
@'
const fs = require('fs');
const load = p => fs.readFileSync(p, 'utf8').trim().split(/\r?\n/).filter(Boolean).map(JSON.parse);
const origFiles = [
  'docs/experiments/tvb11_champion_a1.jsonl',
  'docs/experiments/tvb11_champion_a2.jsonl',
  'docs/experiments/tvb11_champion_b.jsonl',
];
const allOrig = origFiles.flatMap(load).filter(r => r.accepted);
const eligible = allOrig.filter(r => !r.variant);
const originals = new Map(eligible.map(r => [r.id, r]));
const replay = load('docs/experiments/tvb12_replay_run.jsonl');
const anchors = load('docs/experiments/tvb12_replay_anchor2.jsonl');
const comparedArtifact = require('./docs/experiments/tvb12_replay_compare.json');
const rawChecks = {
  accepted: r => r.accepted === true,
  attempt1: r => r.attempts === 1,
  via: r => r.via === 'nonce+engine+bind',
  nonceTable: r => r.nonce === r.metrics_table?.nonce,
  nonceApplied: r => String(r.nonce) === String(r.applied?.inputs?.in_32),
  echo: r => r.echo === r.expected_echo,
  symbol: r => r.metrics_table?.symbol === r.symbol && r.applied?.symbol === r.symbol,
  tf: r => String(r.metrics_table?.chart_tf) === String(r.chart_tf)
    && String(r.applied?.interval) === String(r.chart_tf),
  bf: r => String(r.metrics_table?.bf_strength) === '10'
    && String(r.metrics_table?.bf_tf) === String(
      r.chart_tf === '60' && r.bf_exit === 'off' ? '60' : '30'
    ),
  closedBind: r => r.report?.trades === Number(r.metrics_table?.closed_trades),
  openBind: r => r.report?.openTrades === Number(r.metrics_table?.open_trades),
  netBind: r => Math.abs(r.report?.netAbs - Number(r.metrics_table?.net_abs)) < 0.01,
  listLen: r => r.report?.assert?.lenOk === true,
  idBound: r => r.report?.bound === 'id',
  window: r => Number.isFinite(Number(r.metrics_table?.loaded_first_ms))
    && Number.isFinite(Number(r.metrics_table?.loaded_last_ms)),
};
const closed = list => (list || []).filter(t => !t.open && t.et != null && t.xt != null);
function match(rt, ot) {
  const by = new Map();
  for (const t of ot) {
    const k = `${t.et}|${t.dir}`;
    if (!by.has(k)) by.set(k, []);
    by.get(k).push(t);
  }
  let n = 0;
  for (const t of rt) {
    const a = by.get(`${t.et}|${t.dir}`) || [];
    const i = a.findIndex(o => t.xt === o.xt
      && Math.abs(t.ep-o.ep) <= Math.abs(o.ep)*1e-6
      && Math.abs(t.xp-o.xp) <= Math.abs(o.xp)*1e-6);
    if (i >= 0) {
      n++;
      a.splice(i, 1);
    }
  }
  const d = Math.max(rt.length, ot.length);
  return d === 0 ? 1 : n / d;
}
const verdict = f => f === 1 ? 'CLEAN' : f >= 0.8 ? 'DRIFT' : 'SUSPECT';
const boundedRows = [];
for (const rep of replay) {
  const orig = originals.get(rep.id);
  if (!orig) continue;
  const start = Math.max(
    Number(rep.metrics_table.loaded_first_ms) || 0,
    orig.metrics_table ? Number(orig.metrics_table.loaded_first_ms) : 0
  );
  const end = Math.min(
    Number(rep.metrics_table.loaded_last_ms),
    orig.metrics_table ? Number(orig.metrics_table.loaded_last_ms) : Date.parse(orig.collected_utc)
  );
  const r0 = closed(rep.report.list).filter(t => t.et >= start);
  const o0 = closed(orig.report.list).filter(t => t.et >= start);
  const r1 = r0.filter(t => t.xt <= end);
  const o1 = o0.filter(t => t.xt <= end);
  boundedRows.push({
    shipped: verdict(match(r0,o0)),
    bounded: verdict(match(r1,o1)),
    tail: r0.length-r1.length,
  });
}
const countVerdicts = k => Object.fromEntries(
  ['CLEAN','DRIFT','SUSPECT'].map(v => [v, boundedRows.filter(r => r[k] === v).length])
);
const fpGroups = new Map();
for (const r of eligible) {
  const k = `${r.report.trades}|${r.report.openTrades}|${Math.round(r.report.netAbs*100)}`;
  if (!fpGroups.has(k)) fpGroups.set(k, []);
  fpGroups.get(k).push(r);
}
const collisions = [...fpGroups.values()].filter(v => new Set(v.map(r => r.id)).size > 1);
const tradeSig = r => JSON.stringify(
  (r.report.list || []).map(t => [t.et,t.xt,t.dir,t.ep,t.xp,t.q])
);
const byTag = {};
for (const c of comparedArtifact.compared) {
  byTag[c.tag] ||= {};
  byTag[c.tag][c.verdict] = (byTag[c.tag][c.verdict] || 0) + 1;
}
const pairs = replay.filter(r => originals.has(r.id));
const ceiling = pairs
  .filter(r => r.symbol.startsWith('HIP3XYZ:') && r.chart_tf === '15')
  .sort((a,b) => originals.get(b.id).report.net - originals.get(a.id).report.net)[0];
const short = pairs.find(r => r.id.includes('tf5_slow3_state_short_ss_ratc'));
const bOrig = new Map(
  load('docs/experiments/tvb11_champion_b.jsonl')
    .filter(r => r.accepted && !r.variant)
    .map(r => [r.id,r])
);
const rank = a => new Map([...a].sort((x,y) => y.v-x.v).map((x,i) => [x.id,i+1]));
const ranks = [];
for (const symbol of [...new Set(replay.filter(r => r.tag === 'R3').map(r => r.symbol))]) {
  const rr = replay.filter(r => r.tag === 'R3' && r.symbol === symbol);
  if (rr.length !== 10) continue;
  const a = rank(rr.map(r => ({id:r.id,v:r.report.net})));
  const b = rank(rr.map(r => ({id:r.id,v:bOrig.get(r.id).report.net})));
  let d2 = 0;
  for (const r of rr) d2 += (a.get(r.id)-b.get(r.id))**2;
  ranks.push({
    symbol,
    rho: Number((1-6*d2/(10*99)).toFixed(3)),
    top1Same: [...a].sort((x,y)=>x[1]-y[1])[0][0]
      === [...b].sort((x,y)=>x[1]-y[1])[0][0],
  });
}
console.log(JSON.stringify({
  raw: {
    rows: replay.length,
    failures: Object.fromEntries(
      Object.entries(rawChecks).map(([k,f]) => [k,replay.filter(r => !f(r)).length])
    ),
    uniqueNonces: new Set(replay.map(r => r.nonce)).size,
    elapsedMs: [
      Math.min(...replay.map(r => r.elapsed_ms)),
      Math.max(...replay.map(r => r.elapsed_ms)),
    ],
  },
  anchors: {
    rows: anchors.length,
    championOk: anchors.filter(r => r.champion_ok).length,
    baseAppliedOk: anchors.filter(r => r.base_applied_ok).length,
    baseIdBound: anchors.filter(r => r.base_bound === 'id').length,
    diffEqual: anchors.filter(r => r.diff?.equal).length,
  },
  comparator: {
    stored: comparedArtifact.verdict_counts,
    byTag,
    trueCommonEnd: countVerdicts('bounded'),
    changed: boundedRows.filter(r => r.shipped !== r.bounded).length,
    removedReplayTailTrades: boundedRows.reduce((s,r) => s+r.tail,0),
  },
  fingerprint: {
    eligible: eligible.length,
    collisionGroups: collisions.length,
    differentTradeLists: collisions.filter(v => new Set(v.map(tradeSig)).size > 1).length,
  },
  coverage: {
    acceptedOriginalRows: allOrig.length,
    eligibleIds: new Set(eligible.map(r => r.id)).size,
    comparedIds: comparedArtifact.compared.length,
    pct: Number((
      100*comparedArtifact.compared.length/new Set(eligible.map(r => r.id)).size
    ).toFixed(2)),
    engine: comparedArtifact.compared.filter(c => !originals.get(c.id).metrics_table).length,
    echo: comparedArtifact.compared.filter(c => originals.get(c.id).metrics_table).length,
  },
  named: {
    ceiling: [
      Number((ceiling.report.net*100).toFixed(4)),
      Number((originals.get(ceiling.id).report.net*100).toFixed(4)),
    ],
    short: [
      Number((short.report.net*100).toFixed(4)),
      short.report.trades,
      Number((originals.get(short.id).report.net*100).toFixed(4)),
      originals.get(short.id).report.trades,
    ],
    ranks,
  },
}, null, 2));
'@ | node -
```

Output:

```text
raw: rows=68; every listed failure count=0; uniqueNonces=68; elapsedMs=6021..8050
anchors: rows=3; championOk=3; baseAppliedOk=3; baseIdBound=3; diffEqual=3
comparator stored: DRIFT=18 CLEAN=36
comparator byTag: R1 D2/C4; R2 D5/C1; R3 C26/D8; R4 C5/D3
trueCommonEnd: CLEAN=49 DRIFT=5 SUSPECT=0; changed=13; removedReplayTailTrades=25
fingerprint: eligible=1438; collisionGroups=241; differentTradeLists=35
coverage: acceptedOriginalRows=1498; eligibleIds=1438; comparedIds=54; pct=3.76;
          engine=40; echo=14
named ceiling: replay=248.7007 original=248.7007
named short: replay=13.7061/19 original=12.9115/17
ranks: HOOD=1.000/top1 true; HIMS=0.988/top1 true; RKLB=1.000/top1 true
```

The ShortChamp min/max/direction mirror passes for the requested harvest and ratchet mechanics,
and its sole executable HTF request uses the confirmed-offset idiom. Finding 1 is specifically
about the live snapshot/close clocks, not a residual long-side comparison or an unoffset
`lookahead_on` call.

## 3. Actionable items (reviewer's own list, if provided)

1. Fix ShortChamp's completed-15m snapshot ordering and require a confirmed final child bar for
   the 60m state exit; validate 5m and 15m live-alert fixtures -- **HIGH** --
   `pine/winner_shortchamp_mu5.pine:49-61`, `:202-215`.
2. Replace the 0.8-only comparator with a true common-window, one-to-one, field-complete trade
   diff; keep unexplained interior mismatches SUSPECT and regenerate the JSON/prose -- **HIGH** --
   `scripts/tvb12_replay_compare.mjs:42-70`.
3. Make the report/table join injective with a report generation token or complete trade digest,
   remove name fallback, and enforce session readback on every symbol -- **MEDIUM** --
   `scripts/tvb12_replay_collect.mjs:197-235`, `:293-343`.
4. Relabel the replay as a targeted subset consistency check, keep the original provenance gap
   open, and either narrow the ranking claim or replay the complete 10-config x 7-perp matrix --
   **MEDIUM** -- `docs/HANDOFF.md:11-14`,
   `docs/experiments/tvb12_replay_plan.md:107-121`, `:159-166`.

## Suggested prompt (optional)

Re-review only the TVB-12 repairs. Require fixture evidence that ShortChamp signals entries in
each 5m child position and never exits before a confirmed 60m close. Feed the comparator synthetic
lists covering right-tail additions, boundary cascades, 80-percent nearby-config contamination,
duplicate entry keys, quantity-only differences, and unexplained interior price differences.
Then rerun the committed raw JSONLs through the corrected comparator and reconcile every
VERIFIED/CLOSED claim without expanding into TVB-13.
