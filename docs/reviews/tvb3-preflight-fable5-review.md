# TVB-3 Preflight Review -- Fable 5 (internal, pre-session)

**Date:** 2026-07-01
**Reviewer:** Claude Fable 5 (this workspace's TVB-1/TVB-2 sessions ran on Opus 4.8 while
Fable 5 was offline; this is the requested fresh-eyes pass before TVB-3 begins).
**Scope:** Current implementation state as of `fbe1138` + uncommitted review artifacts:
`pine/baseline_continuity.pine`, `docs/TVB2_control_AB_rerun.md`, `docs/HANDOFF.md`,
`.session_startup_prompt.md`, `tradingview-mcp-jackson/src/core/data.js` (@ `fb2a788`),
and verification of `docs/reviews/tvb2-codex-audit.md` against the sources it cites.
**Method:** Read-only. strat-methodology skill loaded before assessing Pine trigger/continuity
logic (per CLAUDE.md Section 3). No live TV/CDP session, no backtest runs, no file modified
except this document.
**Not verified here (requires live session or off-repo data):** TV private API shapes
(reader), actual chart-instance property values on entity `35dVw8` (slippage/commission/
bar-magnifier state), the raw HL fills behind the fee ground truth.

---

## Verdict summary

The TVB-2 work is sound where it claims to be sound: no lookahead leak, honest labeling of
model vs actual, the fee ground-truth method (HL `crossed` flag) is the right instrument, and
the reader fix is a real repair of a real bug. All four Codex findings CHECK OUT against the
sources -- none is wrong or overstated; adopt all four.

Two things this review adds beyond Codex:

1. **The HTF-open staleness (P2a) should be treated as near-certain, not merely unverified,
   and it is WORSE than the "fidelity, not a leak" framing: it is also a backtest-vs-live
   asymmetry.** This argues for resequencing TVB-3: verify/fix the gate BEFORE the real-fee
   re-runs, or the re-runs characterize a mis-specified gate and must be repeated. (Finding N1;
   the startup prompt currently orders re-runs first.)
2. **The geometric fee model is internally CONFIRMED**: anchored at the 0% actuals it
   reproduces the 0.1% actuals to ~0.1pp for both controls (A: -12.1% predicted vs -12.0%
   actual; B: -98.1% vs -98.1%). Path-dependence of fees over this window is negligible. The
   +38..+42% / +5..+25% estimates deserve more trust than the datasheet's own hedging implies
   -- the re-run is still correct to do (cheap; removes residual model risk), but it is
   confirmation, not suspense. (Finding N2.)

Recommended TVB-3 order is amended accordingly (Section 4).

---

## 1. Codex TVB-2 audit -- verification (all four findings confirmed)

### Codex 1 (MEDIUM): slippage not controlled/documented -- CONFIRMED, and sharpened

`pine/baseline_continuity.pine:39` declares `slippage = 1` (one tick per fill). The datasheet's
fixed-conditions block (`docs/TVB2_control_AB_rerun.md:10-21`) does not record the effective
slippage, yet the real-fee section (lines 176-190) reasons from "B at +5..+25% on ZERO
slippage." Two mutually exclusive possibilities, both action-affecting:

- If the four runs used the script default, every number already includes 1 tick/fill
  (B: 4,602 fills), the "zero slippage" framing is wrong in the CONSERVATIVE direction, and
  TVB-3 step 2 becomes "incremental/asymmetric slippage on top of 1 tick," not "first slippage."
- If the Strategy Tester properties overrode it to 0, the framing is right but unverifiable
  from the repo.

Sharpening: TV exposes strategy() properties through the same inputs mechanism the session
already used (`in_23` = commission percent per the HANDOFF). The slippage property is readable
the same way. **Concrete fix at TVB-3 start: dump the full inputs/properties of entity `35dVw8`
(re-check id first) and record commission, slippage, AND bar-magnifier state into the datasheet
before any new run.** Also record `syminfo.mintick` for MSTRUSDT.P so 1 tick can be converted
to %/fill -- at $130-540 underlying this decides whether embedded slippage is noise or material.

Note the same recording gap applies to the `leverage` input (datasheet says "effective 1x" but
the input value used is unstated) and bar-magnifier (datasheet caveat admits it is
unconfirmed). Generalize the fix: paste the full decoded inputs dump into the fixed-conditions
block of every run table from now on. (See N3.)

### Codex 2 (MEDIUM): fee reversal evidence not reproducible from repo -- CONFIRMED

`docs/TVB2_control_AB_rerun.md:146-164` asserts n=2,425 fills, xyz 86.5% taker, taker
~0.0086%/0.0125%, validated against HL published 0.0432% crypto taker. Nothing in the repo
backs this: `analysis/` is an empty package; the underlying work lived in Claude Desktop /
`Downloads/TVB2_fee_handling.md` (explicitly superseded and off-repo). The session's single
most consequential conclusion is unauditable from the repository.

Adopt Codex's fix with one addition given the PUBLIC remote: the sanitized artifact should be
counts and rates by `{dex, crossed}` only -- fill counts, modal/median/mean/notional-weighted
RATES, and the 0.0864% tail count. Do NOT include absolute notional totals, timestamps, or
anything account-sizing-revealing; rates and ratios are sufficient for auditability. A small
script under `analysis/` (e.g., `analysis/hl_fee_aggregate.py`) that produces the artifact from
a local fills export (never committed) makes it reproducible on demand and gives the empty
package its first real job.

### Codex 3 (LOW): stale 0.0864% re-run target in the deferred checklist -- CONFIRMED, scope widened

`docs/TVB2_control_AB_rerun.md:221-222` says re-run at "0.0086% and 0.0864%"; the RESOLVED
section (166-172) and the disposition (188) say 0.0086% and 0.0125%. The operative driver --
`.session_startup_prompt.md` step 1 -- already has the CORRECT pair, so no one following the
startup prompt would regress. Still patch the datasheet (it is canonical).

Wider than Codex noted: the whole "Deferred to next session" list (lines 212-228) was written
mid-session, BEFORE the ground-truth resolution, and is partially superseded -- e.g. "Build the
limit-entry (maker) variant ... this is the real test" contradicts the resolved position
(cheap-taker makes the maker variant likely moot; the startup prompt states this correctly).
Fix: annotate the deferred list as pre-resolution, or strike the superseded items, rather than
editing only the fee number.

### Codex 4 (LOW): reader drops `debug_sources` on the no-strategy path -- CONFIRMED in source

Verified in `tradingview-mcp-jackson/src/core/data.js`: the browser-side no-strategy branches
build `debug_sources` (`getStrategyResults` line ~154, `getTrades` line ~195) but the node-side
returns (lines ~174, ~223) field-pick it away. This re-creates the exact failure mode that
burned TVB-1 (diagnostic output silently dropped by the outer return). One-line fixes:
propagate `debug_sources: results?.debug_sources` / `trades?.debug_sources`.

Addition for consistency: `getEquity`'s no-strategy branch (line ~240) builds no debug payload
at all -- give it the same `dbg` block while in there.

Residual reader risk worth one sentence in the code comment: the finder's OR-condition
(`isTVScriptStrategy === true || typeof s.reportData === 'function'`) matches the FIRST source
with `reportData`. If TV ever adds `reportData` to plain studies, the false-positive returns.
The `debug_sources` fix is exactly the instrumentation that will catch it, which is another
reason to land Codex 4.

### Codex overall verdict (NEEDS-CHANGES) -- AGREED

All four findings verified against sources; severities are calibrated correctly; the "what I
would do next" list is right EXCEPT that it, like the startup prompt, sequences the real-fee
re-runs before the gate verification. See N1.

---

## 2. New findings (Fable 5)

### N1 (HIGH for sequencing): the HTF-open gate is near-certainly STALE, and it is a backtest-vs-live asymmetry, not just a fidelity nit

The comment at `pine/baseline_continuity.pine:69-73` asserts that because a period's open is
fixed when the period begins, `request.security(..., open, lookahead_off)` returns the CURRENT
period's open. That justification is a non-sequitur under Pine semantics:

- `lookahead_off` aligns the entire requested HTF series to HTF-bar CONFIRMATION (close). On
  historical bars, during period X the call returns the expression evaluated on period X-1's
  bar -- regardless of whether the requested field ("open") was already knowable during X.
  `request.security` has no notion of per-field knowability; it returns the last CONFIRMED
  bar's value.
- On REALTIME bars, the same call returns the DEVELOPING HTF bar's values (TradingView's
  documented historical/realtime asymmetry -- the classic "repainting" behavior). So live, the
  gate WOULD read the current period's open; in backtest it reads the prior period's open.
  **Backtest and live are two different strategies.** This is stronger than TVB-1's "fidelity
  bug, not a leak" framing (which remains true -- results are honest, just mislabeled): the
  backtest characterizes a gate that cannot be deployed as-is with identical behavior.
- Likely exception: requested TF == chart TF is a pass-through (current bar). So Control B's
  15-on-15m leg and Control A's 60-on-60m leg are probably current; A's M/W/D legs and B's
  60/30 legs are stale by a full period. **Control A -- the promising control -- is the most
  distorted:** for most of a month its "M" check is `close > PRIOR month's open`.

Status of prior knowledge: TVB-1's Codex synthesis flagged this as MUST-VERIFY (P2a) with the
fix already designed (P2b). This review upgrades the prior from "unverified, could go either
way" to "expect stale; verify then fix." The P2a empirical overlay (strategy bar-coloring vs
the TFO indicator, already on-chart) remains the decisive check and should still be run --
if it shows a MATCH, this finding is wrong and should be recorded as such.

The P2b fix is endorsed as designed: `ta.valuewhen(timeframe.change(tf), open, 0)` is exact on
24/7 gapless perps (first chart bar of a new period opens AT the period open), needs the
chart-TF <= enabled-TF guard (already in P2b), uses no `request.security` at all, and -- the
new argument -- is historical/realtime SYMMETRIC, eliminating the backtest-vs-live divergence.

**Sequencing consequence (the actionable point):** the startup prompt runs the real-fee
re-runs FIRST (step 1) and P2a/P2b FOURTH. If the gate is stale, step 1's four runs
characterize the mis-specified gate and must all be repeated after P2b. Cheaper and cleaner:

1. P2a overlay verification first (cheap, decisive).
2. If stale: P2b fix (Pine change -> plan mode, strat-methodology STOP-and-ASK per CLAUDE.md).
3. ONE bridge run (e.g., A @ 0.1%, fixed gate, same window) to quantify the staleness delta
   against TVB-2's A @ 0.1% = -12.0%. That delta is itself a deliverable -- it measures which
   strategy TVB-1/TVB-2 actually characterized, and how far the stale gate is from the
   designed one.
4. THEN the real-fee re-runs (0.0086% / 0.0125%) on the corrected control -- run once, on the
   gate we intend to keep.
5. THEN slippage modeling.

If the overlay shows no staleness, fall back to the startup prompt's original order unchanged.
This is a recommendation, not a unilateral change -- the startup prompt is user-approved
state; user decides. Counter-argument acknowledged: re-running the STALE gate at real fees
preserves strict comparability with TVB-1/TVB-2 tables. The bridge run in step 3 preserves
that comparability at the cost of one run instead of four.

### N2 (POSITIVE): the geometric fee model is internally consistent -- verified

The model `equity_mult = (1 + r_0%) x (1-f)^(2N)` anchored at the 0% actuals REPRODUCES the
0.1% actuals: A: 1.482 x (0.999)^522 = 0.879 -> -12.1% (actual -12.0%); B: 1.858 x
(0.999)^4602 = 0.019 -> -98.1% (actual -98.1%). The fee effect over this window is therefore
almost perfectly geometric with negligible path interaction, so the intermediate estimates
(A +38..+42%, B +5..+25%) are much better grounded than "model, confirm by re-run" hedging
suggests. Keep the re-run (it is cheap and eliminates residual risk) -- but expect
confirmation, and treat a material DEVIATION from the model as itself a red flag (something
other than commission changed between runs).

### N3 (MEDIUM): run-settings recording gap is broader than slippage

Codex 1 covers slippage. The same "not recorded, not reproducible" gap applies to:
bar-magnifier state (datasheet admits unconfirmed; Codex trap #2), the `leverage` input value
(datasheet infers "effective 1x" from first-trade notional), and the full input-id mapping
(`in_23` etc. -- which SHIFTS if P2b adds inputs; never reuse cached ids across Pine edits;
re-derive after every source change). Fix once, structurally: at run time, dump the decoded
inputs/properties of the strategy entity and paste it into the datasheet's fixed-conditions
block. Every future run table inherits reproducibility for free.

### N4 (LOW): trigger touch-vs-break -- carried P2b confirmed against the skill

`strategy.entry(..., stop = high)` arms at exactly the prior extreme, so an entry fires on an
EQUAL-high touch. Strict classification (strat-methodology: 2U requires `H > H[1]`, trigger =
setup high + one tick) says a touch is NOT a break; the skill's Pine equivalent is
`high[1] + syminfo.mintick`. Bias direction: the current form generates strictly MORE (false)
triggers, i.e., results are slightly pessimistic-on-selectivity, optimistic-on-signal-count.
Low severity on a liquid perp; the P2b tick-offset fix is correct as designed. No new action
-- recorded here so the skill-check is on file.

### N5 (LOW): stale fee comment/default in the Pine header

`pine/baseline_continuity.pine:38`: `commission_value = 0.05` with comment "~OKX perp taker;
HIP-3 ~2x -- adjust per venue." Ground truth now: operative HIP-3 xyz taker is ~0.0086-0.0125%
-- roughly 5x BELOW the script default, not 2x above. Anyone loading the script fresh inherits
a wrong fee prior. Bundle the comment/default update with the P2b Pine edit (avoid a separate
compile/save cycle on the shared slot).

### N6 (INFO): uncommitted review artifacts

`docs/HANDOFF.md` (review status REQUESTED -> RETURNED) and `docs/reviews/tvb2-codex-audit.md`
are uncommitted, as is this document. Expected per the external-review protocol (reviews land
after the session commit); commit all three at TVB-3 start so the audit trail is in history
before new work.

### N7 (INFO, no action): mechanics understood and accepted

Two behaviors verified as intended, recorded so they are not re-litigated: (a) after a
state-stop exit there is a one-bar re-arm gap (exit fills at next open; `flat` is only seen at
that bar's close), so the strategy cannot re-enter on the exit bar -- conservative, and means
B's churn is if anything UNDER-counted; (b) `qty` uses the arming bar's close while the fill
occurs at the stop price, so realized notional deviates slightly from `leverage x equity` --
negligible at 1x.

---

## 3. What is sound (explicit, so the review is not only findings)

- **No classic lookahead leak.** Single `request.security` call path, `lookahead_off`,
  unchanged in TVB-2; N1 is a staleness/asymmetry problem, not a future-information problem.
  TVB-1/TVB-2 numbers are honest characterizations -- of the stale gate.
- **The reader fix is a genuine repair**: the old finder false-positive (`s.performance` on
  every study) is correctly diagnosed and the new detection (`isTVScriptStrategy` /
  `reportData`) was live-verified in TVB-2. Codex 4 is a hardening item, not a defect in the fix.
- **The breakout-stop-is-taker reasoning holds** (agree with Codex): a stop-triggered breakout
  crosses the book; a maker fee cannot be assumed for the same fill set. The datasheet's
  treatment of the maker column as an upper bound, and the 97%-maker misclassification
  autopsy, are exemplary charter-S6 discipline.
- **The epistemic hygiene in the datasheet is real**, not performative: models labeled as
  models, single-fee verdicts banned, the "disputed maker read" section preserved with its
  resolution. N2 shows the hedging was, if anything, over-cautious.

---

## 4. Recommended TVB-3 order (amendment for user approval)

0. Commit the review artifacts (N6). Read this document + the Codex audit; fold into HANDOFF.
1. Dump + record entity `35dVw8` inputs/properties: commission, SLIPPAGE, bar-magnifier,
   leverage, mintick (Codex 1 + N3). Patch datasheet lines 176-190 wording to whichever
   slippage reality holds; patch the 0.0864% checklist target (Codex 3) and annotate the
   superseded deferred items (N4-adjacent).
2. P2a overlay verification of HTF-open currency (N1). Decisive either way.
3. If stale: P2b Pine fix (plan mode, STOP-and-ASK) + tick-offset + TF guard + header fee
   comment (N5) in ONE edit; then the A @ 0.1% bridge run to measure the staleness delta.
4. Real-fee re-runs A/B at 0.0086% and 0.0125% on the (possibly corrected) gate -- expect
   agreement with the geometric model (N2); investigate any material deviation.
5. Jackson reader: propagate `debug_sources` (+ getEquity parity) (Codex 4 + N6-adjacent).
6. Sanitized `{dex, crossed}` fee aggregate artifact under `analysis/` (Codex 2).
7. Then, unchanged from the startup prompt: slippage modeling, bar-magnifier fidelity check,
   cherry-picked-window bug test, and only after clean controls: two-layer / second regime.

Items 1, 5, 6 are order-independent of 2-4 and can interleave; the load-bearing change vs the
startup prompt is 2-3 BEFORE 4 (rationale in N1).
