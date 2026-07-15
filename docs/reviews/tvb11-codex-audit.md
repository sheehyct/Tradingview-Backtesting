<!--
External review of TVB-11. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-11 External Audit -- Codex CLI / GPT-5 (verbatim source, read CRITICALLY)

> External review of commit range `0561c53^..0a1d26a` and the user-supplied BF reference
> materials captured 2026-07-15 (TVB-11 post-session). Lightly ASCII-normalized
> (em-dashes -> --, curly quotes -> straight); wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-11 -- BF-deviation experiments and champion search
- **Reviewed:** `0561c53^..0a1d26a` on `main` (30 commits, 31 changed files)
- **Reviewer:** Codex CLI / GPT-5
- **Overall verdict:** NEEDS-CHANGES

## 2. Verbatim audit

### Bottom line

NEEDS-CHANGES. I do not recommend rerunning the entire 1,550-record experiment. I do recommend
treating the champion/generalizer claims as unverified until a fail-closed collector replays the
anchors, controls, per-timeframe champions, and a corrected Stage B direction roster. The current
record has three material defects:

1. The collector can accept a report that is not causally bound to the requested configuration.
2. Stage B silently omitted the 5-minute short champion and tested an all-long roster.
3. The BF engine does not require a paired higher-high/lower-low formation before exposing an exit
   boundary, and its one fixed 30m/10 geometry is too narrow to support a full-mechanism claim.

The closed-trade NET calibration, the 60m BF-off trading no-op, and the four Pine
`request.security` expressions themselves check out. Those passes do not repair the selection and
collector defects.

### Scope and method

I sanity-checked `git diff --name-status 0561c53^..0a1d26a`: the range contains 30 commits and 31
changed files. I read the required control documents in the requested order, audited the collector
and every executable `request.security` call at the pinned head, parsed all A1/A2/B JSONL records,
recomputed the P0b per-trade arithmetic, and compared the champion BF engine with both Pine
versions in `temporary/BF PINESCRIPT ORIGINAL PLUS CLAUDE VERSIONS.txt`. I rendered and visually
inspected all seven pages of `temporary/The Broadening Formation Algorithm.pdf`; no private header
or account material from that document is reproduced here. I did not rerun the TradingView grid.

### Finding 1 -- HIGH -- The settle gate does not bind accepted metrics to the requested run

The pre-registration is unambiguous: every run must echo its symbol and all cell inputs, a mismatch
must reject the run, and every accepted run must record its loaded window
(`docs/experiments/tvb11_champion_prereg.md:80-83`, `:269-270`). The implementation has two weaker,
independent acceptance paths:

- `expectedEcho()` omits the chart timeframe, BF timeframe/strength, fixed regime timeframes, and
  chart subsession (`scripts/tvb11_champion_collect.mjs:140-150`). The echo branch checks only that
  partial echo plus symbol, then returns even when the full engine readback is false
  (`scripts/tvb11_champion_collect.mjs:269-285`). A stale table with the same symbol and logical
  cell but the wrong chart timeframe or RTH/24h subsession can therefore pass. That is especially
  consequential because the session already discovered a saved 24h-vs-regular contamination
  vector (`docs/experiments/tvb11_champion_prereg.md:271-284`).
- The engine branch verifies that the requested inputs are currently applied, but the report is
  found separately by the first strategy whose description starts with `TVB-EXP Champion`, not by
  the study entity id (`scripts/tvb11_champion_collect.mjs:160-191`, `:193-210`). It accepts an
  unchanged report after 20 seconds (`scripts/tvb11_champion_collect.mjs:279-285`). Applied inputs
  and an old stable report can therefore coexist long enough to pass; there is no run nonce,
  calculation generation, or full-config echo tying them together.

The committed evidence cannot repair this post hoc. The record schema drops the applied-input,
interval, and subsession snapshot (`scripts/tvb11_champion_collect.mjs:337-346`). I parsed all raw
stage files: 736 accepted records used the engine path, all 736 have `metrics_table: null`, and thus
none contains the promised per-run loaded window. Forty-one engine records were accepted after the
20-second unchanged-report escape. Representative escape records are
`docs/experiments/tvb11_champion_a1.jsonl:9`, `docs/experiments/tvb11_champion_a2.jsonl:3`, and
`docs/experiments/tvb11_champion_b.jsonl:16`; the omitted 5m champion itself is an engine/no-window
record at `docs/experiments/tvb11_champion_a1.jsonl:343`. Section 12 accurately reports the 762/736
path split but incorrectly presents both as satisfying collection integrity
(`docs/experiments/tvb11_champion_prereg.md:356-363`).

This proves an evidence gap, not that all 736 values are wrong. Fix the gate before relying on the
rankings: require both entity-specific engine readback and a full Pine echo containing chart TF,
subsession, BF TF/strength, all fixed axes, and a unique run nonce; remove elapsed-time acceptance;
store the readback and loaded window in every record. A bounded replay of anchors, controls,
per-TF champions, and Stage B finalists is sufficient initially. Expand only if that replay finds
differences.

### Finding 2 -- HIGH -- Stage B discarded the short winner and made generalization all-long

The user's skepticism is justified, with one important correction: the search did produce a short
winner. The 5m perp champion is `slow3/state/short/ss_ratc/a15/x60` at +12.9 percent
(`docs/experiments/tvb11_champion_prereg.md:372-374`; raw record
`docs/experiments/tvb11_champion_a1.jsonl:343`). The pre-registration says per-timeframe champions
"ride along" with the consensus champion into Stage B
(`docs/experiments/tvb11_champion_prereg.md:250-253`). It also promises winner surfaces for the
consensus and per-TF champions (`docs/experiments/tvb11_champion_prereg.md:329-341`).

That did not happen. Machine-parsing the entire Stage B cell list yields 140 rows, 10 unique
configs, and one direction: `long`. The first complete ten-config block shows the selection
directly (`docs/experiments/tvb11_champion_cells_b.json:2-130`). Consequently, "best generalizer"
means best among ten long candidates, not best among the declared champions or across directions.
The delivered Generalizer bakes `LONG ONLY` into its identity
(`pine/winner_generalizer.pine:5-14`), while no 5m short-champion surface was shipped
(`docs/experiments/tvb11_champion_prereg.md:459-468`). This also repeats the exact selection hazard
the independent blind report had already named: choosing long-only in the observed bullish window
encodes launch-regime bias (`docs/experiments/tvb_exp_bf_sweep_gpt.md:281-293`).

There is also an internal pre-registration conflict: Stage B is budgeted as exactly ten configs x
fourteen symbols (`docs/experiments/tvb11_champion_prereg.md:214-218`), yet the scoring contract
requires additional per-TF champions to ride along. Execution silently resolved that conflict by
dropping the short winner rather than amending the plan.

Do not rerun A1. Add a targeted common-window breadth replay containing (a) the exact omitted 5m
short champion, (b) matched `long`, `short`, and `both` direction versions of the same gate/exit/BF
configuration, and (c) a matched BF-off control. Until then, rename "Generalizer" as an all-long
Stage B candidate and do not infer directional portability.

### Finding 3 -- HIGH -- The tested BF exit is not a paired broadening-formation detector

Against the supplied reference algorithm, the model is measuring a looser object than it names.
The article requires both expansion facts -- the new swing high exceeds the prior high and the new
swing low undercuts the prior low -- before a broadening formation is identified
(`temporary/The Broadening Formation Algorithm.pdf`, p. 3), then calls for continuous
re-evaluation/redrawing as new swings arrive (p. 7).

The original TFO Pine evaluates and consumes its lower pair independently from its upper pair
(`temporary/BF PINESCRIPT ORIGINAL PLUS CLAUDE VERSIONS.txt:88-148`). The Claude MTF port preserves
that behavior (`temporary/BF PINESCRIPT ORIGINAL PLUS CLAUDE VERSIONS.txt:353-399`) and explicitly
admits it is a fractal-pivot megaphone approximation, not a STRAT-taxonomy detector
(`temporary/BF PINESCRIPT ORIGINAL PLUS CLAUDE VERSIONS.txt:463-467`). The champion port likewise
creates `lower_tl` when only the lows expand and `upper_tl` when only the highs expand
(`pine/tvb_exp_champion.pine:414-449`). Its orders then use whichever individual line handle exists
(`pine/tvb_exp_champion.pine:482-513`). A long can therefore exit against an orphan upper boundary,
or a short against an orphan lower boundary, without one paired expanding formation ever existing.
Faithfulness to the original Pine is not faithfulness to the supplied BF definition.

The lag concern is also real, though it is not a repaint bug. Champion inputs fix BF geometry at
30m/10 and accurately disclose pivot confirmation lag (`pine/tvb_exp_champion.pine:85-88`). With
the completed-HTF-bar propagation at `pine/tvb_exp_champion.pine:372-377`, an observed turn becomes
usable roughly 5 to 5.5 hours later. The champion preamble calls the exercise a sweep of the "full
mechanism space" (`docs/experiments/tvb11_champion_prereg.md:13-18`), but Stage A1 fixed BF at
30m/10 (`docs/experiments/tvb11_champion_prereg.md:171-203`). The earlier blind sweep had already
shown material BF sensitivity across TFs 15/30/60 and strengths 5/10/20
(`docs/experiments/tvb_exp_bf_sweep_gpt.md:104-125`, `:195-216`).

Specify the detector before another optimization: one formation id must own a compatible pair of
expanding upper/lower pivots; both boundaries should be redrawn/versioned when either confirmed
swing changes the pair. Keep a non-repainting confirmed state for backtests, and if faster live
awareness is desired, expose a separate clearly provisional/developing state that may invalidate.
The article's volatility-adaptive pivot length is worth testing as a pre-registered branch, but the
chosen length must be frozen per candidate so future volatility cannot rewrite old pivots. Validate
paired-vs-independent detection on hand-labeled chart fixtures, then run a small BF ablation across
common windows. The whole champion grid need not be repeated.

### Finding 4 -- MEDIUM -- P3 is a useful replacement, but not "strictly stronger"

The amendment honestly records why the original E2-number reproduction became unevaluable and
retains the first anchor artifact (`docs/experiments/tvb11_champion_prereg.md:84-99`). The three
committed cross-script records are trade-for-trade equal on their shared window
(`docs/experiments/tvb11_champion_anchor2.jsonl:1-3`). That is useful evidence that the clock and
`ratchet_c` changes preserved the old engine on those cells.

It is not strictly stronger than the original requirement. It cannot preserve continuity with the
old E2 numbers/window, cannot detect a bug shared by both scripts (including the BF model above),
and does not test mirror/RTH clock behavior. More directly, the collector comment says the base
engine inputs were already verified, but the code only sets them and waits for a stable base report;
there is no base entity readback at all (`scripts/tvb11_champion_collect.mjs:401-416`). The champion
half also inherits Finding 1's echo-or-engine gate.

Relabel P3 as a narrower current-window cross-script equivalence check. Re-run it with entity-bound
readback and nonces on both studies, and retain a deterministic clock fixture for the behavior the
expired E2 window was meant to anchor.

### Finding 5 -- MEDIUM -- `closedtrades.profit()` is NET, but propagation is incomplete

The calibrated fact is correct. I independently recomputed all 11 C3 trade rows in
`docs/experiments/tvb11_champion_anchor.jsonl:2`. For every row,
`gross == (exit-entry)*signed_size` and `profit == gross-commission`; maximum absolute errors were
1.37e-12 and 2.28e-13 respectively. The harness exposes exactly those fields
(`pine/tvb_exp_champion.pine:626-649`), and the champion governor's `profit() > 0` classification is
therefore NET as claimed (`docs/experiments/tvb11_champion_prereg.md:48-59`).

The claim has not propagated through the repository. The Python simulator still documents and
implements a gross governor (`tfc/simulator.py:12-15`, `:92-99`, `:161-170`). The companion still
labels and calculates gross win/loss from exit vs entry prices (`pine/tfc_companion.pine:99-105`,
`:150-152`, `:365-374`). The VBT port plan still calls `profit()` gross
(`docs/VBT_BREADTH_PORT_PLAN.md:78-87`). Those are now known parity breaks on marginal trades, not
merely stale prose.

Add a dated canonical supersession note rather than rewriting old raw results, update the live
companion and Python port to explicit NET classification where parity is intended, and add a
fixture with `gross > 0` but `gross - commission <= 0`. Do not claim Claude-lineage parity until
that fixture agrees across Pine, companion, and Python.

### Finding 6 -- MEDIUM -- Section 12 says "ruler," but the session-level promotion boundary leaks

Section 12 does prominently state the cross-window confound
(`docs/experiments/tvb11_champion_prereg.md:365-370`), warns that the mirror numbers are dominated by
three bullish years (`:424-426`), and ends with deployment forbidden (`:447-457`). The watch/alert
indicators themselves were pre-authorized (`:329-341`). Those disclosures are good.

However, "single most portable," "Winner: Generalizer," and "intended live system" are promotion
language, especially after an all-long Stage B selection (`docs/experiments/tvb11_champion_prereg.md:447-468`;
`pine/winner_generalizer.pine:5-14`). The handoff then says a live-capital microdeployment is planned
soon (`docs/HANDOFF.md:70-74`). No capital deployment occurred in the reviewed range, but the
cross-artifact message is no longer merely "a ruler, not a strategy." Rename the surfaces as
in-sample candidates and keep capital deployment out of scope until the collector, direction
roster, paired BF model, and an untouched time/regime holdout have passed.

### Finding 7 -- LOW -- The four security calls are safe, but repository policy says the opposite

At `0a1d26a`, there are exactly four executable `request.security` calls in `pine/`:
`pine/tvb_exp_bf_exit.pine:344`, `pine/tvb_exp_champion.pine:373`,
`pine/winner_champion_mu15.pine:92`, and `pine/winner_generalizer.pine:94`. All four request values
offset by at least one completed HTF bar and use `barmerge.lookahead_on`. This is TradingView's
documented non-repainting HTF idiom, not future leakage; the offset and lookahead setting are an
interdependent pair. See TradingView's official "Other timeframes and data" documentation:
https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/.

The repository's hard rules instead say every call must use `lookahead_off`
(`pine/README.md:21-28`; `CLAUDE.md:90-95`). That blanket rule is wrong for this documented idiom and
now contradicts the accepted code. Correct the rule to forbid unoffset `lookahead_on` while
explicitly allowing `expression[1] + lookahead_on` for confirmed HTF values. Also document that
non-repainting safety costs one completed HTF bar of latency; it does not solve Finding 3's
timeliness problem.

### Other focus-area checks

- **60m BF-off neutralization: PASS for trading behavior.** In the original deployed ancestor,
  BF re-entry blocks are set only after BF-commented exits (`pine/tvb_exp_bf_exit.pine:249-261`),
  the only block output feeds entry triggers at `:279-287`, and all BF orders are gated by
  `bf_exit != 'off'` with both orders canceled otherwise (`:463-484`). Setting `bf_tf='60'` while
  BF is off can change internal BF drawings/calculation, but not orders or blocks on the deployed
  60m cell.
- **Window-confound prose: PASS with evidence qualification.** The cross-TF and perp-vs-mirror
  caveats are explicit in Section 12. Finding 1 means the promised window evidence is absent for
  736 accepted runs, so exact per-run comparability is not independently auditable.
- **P3 observed equality: PASS narrowly.** The raw three-cell diffs are equal; Finding 4 limits
  what that proves.
- **NET arithmetic: PASS.** Finding 5 concerns downstream propagation, not the calibration.

## 3. Actionable items (reviewer's own list, if provided)

1. Make collector acceptance fail closed and entity-bound; persist full config/session/window evidence, then replay only anchors, controls, per-TF champions, and Stage B finalists -- **HIGH** -- `scripts/tvb11_champion_collect.mjs:140-210`, `:255-285`, `:337-346`.
2. Restore the omitted 5m short champion and matched long/short/both plus BF-off controls to a bounded common-window breadth replay; relabel Generalizer until it passes -- **HIGH** -- `docs/experiments/tvb11_champion_prereg.md:243-253`, `docs/experiments/tvb11_champion_cells_b.json:2-130`.
3. Define a paired BF formation state, validate it against hand-labeled article examples, and compare paired-vs-independent, TF, and strength branches without rerunning the full grid -- **HIGH** -- `pine/tvb_exp_champion.pine:414-449`, `temporary/The Broadening Formation Algorithm.pdf`, pp. 3 and 7.
4. Downgrade P3's claim to narrow cross-script equivalence and repeat it with verified readback/nonces on both studies -- **MEDIUM** -- `scripts/tvb11_champion_collect.mjs:384-425`.
5. Propagate the NET calibrated fact through companion/Python/VBT parity code and add a marginal-trade fixture -- **MEDIUM** -- `tfc/simulator.py:12-15`, `pine/tfc_companion.pine:365-374`.
6. Keep the artifacts labeled as in-sample rulers/candidates and defer live-capital use until targeted revalidation plus an untouched holdout -- **MEDIUM** -- `docs/experiments/tvb11_champion_prereg.md:447-468`, `docs/HANDOFF.md:70-74`.
7. Correct the repository's `request.security` rule to document the safe offset-plus-lookahead idiom -- **LOW** -- `pine/README.md:21-28`, `CLAUDE.md:90-95`.

## Suggested prompt (optional)

Synthesize TVB-11 without rerunning the full grid. First harden the collector and replay anchors,
controls, all three per-TF champions, and Stage B finalists. Second, repair the Stage B roster with
the omitted 5m short champion and matched direction/BF-off controls on common windows. Third,
ratify a paired BF detector contract from the supplied article and test confirmed vs explicitly
provisional live geometry. Preserve the original raw record, label all changed tests as new
evidence, and do not authorize capital deployment from the in-sample champion search.
