# TVB-21 Tier B report -- the Magnitude+Targets layer ablation

> **INVALIDATION NOTICE (2026-08-09, TVB-22 audit fold-in -- external audit
> `docs/reviews/tvb21-codex-audit.md` F1 HIGH, independently reproduced to
> the decimal before adjudication).** The A2/A3 target exit implemented
> one-sided predicates (long `h >= tgt` / short `l <= tgt`) instead of the
> pre-registered range-containment touch. Trades born beyond their frozen
> target were therefore closed AT the target on bars that never traded that
> price: A2 208/410 target exits filled outside their exit bar (188 of them
> in the born-beyond class, -278.3pp of the reported -310.1pp); A3 102/255
> (97, -146.2pp). Requiring containment flips A2/A3 combined from
> -222.0/-127.5pp to +24.6/+31.0pp (diagnostic only). CONSEQUENTLY the
> package verdict, the churn-loss MAGNITUDE, candidate counts, and the
> package-arm MAE-tail claims below are INVALID pending a pre-registered
> semantics amendment (marketable-at-entry targets + the no-target skip)
> and a full A2/A3 rerun. The born-beyond re-entry MECHANISM itself, both
> A0 controls, and the A1-vs-A0b S3.1 contrast are unaffected. Also
> corrected (audit F3): the plain 3-2 census quoted below (182 trades,
> -163.0pp, 33% win) is the ALL-11-symbol scope with Boom removed; under
> the declared 10-symbol roster it is 139 trades, -151.2pp, 29.5% win --
> still the largest and worst class. Original text below is preserved
> unchanged as the record of what was claimed.

Pre-registration: `docs/experiments/tvb21_tier_b_prereg.md` (94090e9, declared
before any pattern/veto/target code). Artifacts: `analysis/paper/tier_b/`
(manifest carries git head, bar hashes, and the PASSING A0 determinism check:
both control arms reproduced the committed Tier A cells field-exact on all 11
symbols). Window 2026-07-06 -> 2026-08-03, 10-symbol roster rollup (DRAM
excluded, parity convention), 1x GROSS, one ~4-week window: everything below
is in-sample characterization. No arm is promoted.

## The finding

**The pattern package died on this window, and the autopsy is unusually
clean: the loss is almost entirely one identified mechanical class -- trades
BORN BEYOND their own first target -- created by the strategy-ization, not
by the patterns.** The reclaim ladder freezes at entry; the 1H signal
persists after a target exit; the next 5m bar re-enters at a price already
past the spent reclaim level; the touch rule then force-exits at that level
for a structural loss; repeat. The Magnitude+Targets DISPLAY tool never does
this -- it never enters. The defect lives in the entry/re-entry semantics of
the backtest strategy-ization, exactly the layer the pre-registration said
it was testing.

Roster totals (combined = realized + open MTM, percentage points):

| Arm | Trades | Combined | Win | Roster maxDD | Exit mix |
|-----|--------|----------|-----|--------------|----------|
| A0a control, deployed 15m trigger | 170 | +47.4 | 67% | 131.5 | bf 111 / brk 26 / flip 33 |
| A0b control, matched 1H trigger | 172 | +104.8 | 68% | 122.2 | bf 113 / brk 27 / flip 32 |
| A1 pattern entries, control exits | 137 | -7.7 | 64% | 116.3 | bf 86 / brk 26 / flip 25 |
| A2 package, always exit at Target 1 | 413 | -222.0 | 40% | 230.4 | tgt 410 / brk 3 |
| A3 package, exit at second target | 263 | -127.5 | 43% | 151.7 | tgt 255 / brk 6 / flip 2 |

## Contrast-scoped verdicts (per the pre-registered statements)

**A1 vs A0b (the only S3.1-relevant contrast -- pattern entries, exits held
fixed):** pattern-gated entries took the matched-cadence control from +104.8
to -7.7 (137 trades vs 172; the dictionary traded LESS and worse). Honest
decomposition: A1 carries the declared conservative fill bias (late entries
fill at bar open, controls fill at the level); the measured total drag is
54.2pp across 53 late fills. Crediting ALL of it back puts A1 near +46 --
still ~58pp under the control, whose own level fills are themselves the
optimistic convention. **On this window, the pattern dictionary added no
information beyond the continuity break under either fill convention.
Charter S3.1's thesis survives its first identified test.** One window, one
regime; the result characterizes, it does not generalize.

**A2/A3 vs A0b (the package):** -222.0 and -127.5 vs +104.8. But the
born-beyond-target class explains MORE than the whole loss: in A2, 244 of
413 trades (59%) entered beyond their own frozen T1 and netted -310.1pp,
while the remaining 169 legitimate trades netted +88.1pp. A3 mirrors it
(159/263 beyond, -156.0pp vs +72.6pp). 73% of A2 trades exited within one
5m bar; 59% re-entered within one bar of the prior exit. The package
verdict is therefore: **killed by an identified structural defect in the
always-exit-at-target + persistent-signal re-entry combination**, with the
patterns' own contribution already adjudicated (negative) by A1.

**A2/A3 vs A1 (the veto + target-exit increment):** swapping the control's
BF-harvest exits for target exits turned -7.7 into -222.0 / -127.5. The
increment is the churn loop above, partially damped by the deeper target
in A3 (its 255 target exits net only -22.5pp; rung 2 existed for 197 of
266 entries, 69 fell back to T1).

**A0b vs A0a:** the 1H arm trigger control (+104.8) more than doubles the
deployed 15m control (+47.4) -- consistent with Tier A's arm-TF gradient;
recorded as context, not promoted.

## The vetoes (the user's excessive-suppression flag, measured)

- **The chop veto is the dominant force in the package arms and it does not
  transfer across symbols** -- exactly the concern that motivated flagging
  fixed percentages. Share of candidates within 2% of a D/W/M open: GOLD
  100% (zero trades survived), AAPL 96% (one trade), AMZN 94%, GOOGL 90%,
  MSFT 90%, TSLA 81% -- versus SKHX 47%, DRAM 58%, NBIS 64%, MRVL 65%. The
  fixed 2% band acts as an accidental symbol filter: it nearly delists the
  slow movers and lets the fast ones through. The deferred ATR-scaled
  variant is now motivated by mechanism, not by performance.
- The BF-proximity veto (the user's flagged worry) was the MILD one: 1-45%
  of candidates per symbol (highest on the quiet symbols where lines sit
  near price). 131 candidates were skipped for having no target at all.
- Candidate counts themselves are inflated by the churn loop (a persisting
  1H signal re-candidates every 5m bar while flat): A2 saw 3,763 candidates
  vs A1's 146. Entry-count deltas per symbol ran both directions: GOLD
  14 -> 0 and AAPL 11 -> 1 (veto-starved) vs SKHX 9 -> 99 and MRVL 7 -> 86
  (churn-inflated). The package arms trade a structurally different book,
  not a filtered version of the same book.

## Pre-committed diagnostic reads

- **Pattern census** (labeled ceiling-read, no promotion): across package
  arms the plain 3-2 was the largest and worst class -- 182 closed trades,
  -163.0pp, 33% win. Only 2 trades carried the Boom (hammer/shooter) flag,
  both winners (+1.0pp): far too few to read, recorded because it was
  pre-committed. The 2-2 family was the healthiest large class in the DRAM
  smoke and mixed at roster scale.
- **PMG+ flag: structurally dead for this dictionary** (as-built quirk,
  found during the port): the pine seeds the streak walk at the developing
  bar's own high/low, and every enabled setup requires that bar to have
  broken the level, so the first streak comparison always fails. The flag
  can only fire for the gap / going-3 families, which are toggled off. Zero
  PMG-prefixed trades, as predicted. Worth a nudge to the M+T collaborator.
- **What survived (kill-first honesty):** the package arms crush the
  adverse-excursion tail -- mean episode MAE 0.78% (A2) / 1.32% (A3) vs
  2.6-2.8% in the controls, worst runner 15.0% / 29.7% vs 37.1%, give-back
  p90 3.2 / 4.0pp vs ~8.7pp. Fast target exits cap the adverse-runner class
  that has haunted every control since TVB-16 -- at the cost, in this
  build, of the churn loss engine. The exit-speed/tail trade-off is real
  and now has numbers on both sides.

## Named next variants (pre-registered before running, per protocol)

Both are single-mechanism repairs motivated by the autopsy, not by the
scoreboard, and both remain ablations against C1:

1. **T1-floor entry guard** -- the user's own rule-base component ("Target 1
   must be far enough away to cover fees and ensure real profit"), deferred
   out of v1 and now shown to be the missing structural guard: it vetoes
   every born-beyond-target re-entry by construction. A value must be
   pinned a-priori before any run.
2. **ATR-scaled vetoes** -- already a named deferred arm; the chop veto's
   47-100% per-symbol spread is the transfer failure the scaling exists to
   fix.

Nothing else changes without a new pre-registration; in particular the
"revisit the BF-harvest replacement after visualization" note from the
design session stays a future variant decision.
