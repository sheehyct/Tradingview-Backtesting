# TVB-22 Tier B rerun report -- the package under the ruled containment contract

Supersedes the A2/A3 sections of `docs/experiments/tvb21_tier_b_report.md`
(invalidated by external audit F1, `docs/reviews/tvb21-codex-audit.md`; the
original report carries a dated notice and is preserved as the record of
what was claimed). Contract: the pre-registration
`docs/experiments/tvb21_tier_b_prereg.md` INCLUDING its 2026-08-09
user-ruled amendment (containment-touch targets; veto-eval-before-skip;
source-bound manifest), committed BEFORE this rerun. Artifacts:
`analysis/paper/tier_b/` regenerated in place; fix-isolation invariants
verified (A0a/A0b/A1 per-symbol rows identical to the invalidated run's
modulo the zero-valued `no_target_vetoed` counter key; A0 determinism check
vs committed Tier A cells PASS). Same window 2026-07-06 -> 2026-08-03,
10-symbol roster rollup (DRAM excluded), 1x GROSS, one ~4-week window:
in-sample characterization, no arm promoted.

Provenance note: the rerun manifest records the executed blob hashes
(tier_b.py 8714b935..., engine.py 23e8e219..., patterns.py a30f5e2f...) and
`git_dirty: true` -- the dirtiness is the regenerated tier_b/ OUTPUT files
themselves being uncommitted at run time; all three executed code blobs
match the committed fix revision.

## The finding

**Enforcing the pre-registered containment touch removes the impossible
fills, and with them most of the package's reported catastrophe -- but not
its underperformance.** A2 goes -222.0 -> +24.6pp and A3 -127.5 -> +31.0pp,
yet both remain roughly 75-80 points UNDER the matched-cadence control.
What the audit fix killed was the magnitude story (impossible fills booked
at prices the exit bars never traded), not the package's failure to beat
the control below it. The churn loop itself largely dissolves under
containment: a born-beyond trade now stays open until its level actually
trades, and one-position-at-a-time blocks the instant re-candidacy, so A2
shrinks from 413 trades to 186 and one-bar exits fall from 73% to 31%.

Roster totals (combined = realized + open MTM, percentage points):

| Arm | Trades | Combined | Win | Roster maxDD | Exit mix |
|-----|--------|----------|-----|--------------|----------|
| A0a control, deployed 15m trigger | 170 | +47.4 | 67% | 131.5 | bf 111 / brk 26 / flip 33 |
| A0b control, matched 1H trigger | 172 | +104.8 | 68% | 122.2 | bf 113 / brk 27 / flip 32 |
| A1 pattern entries, control exits | 137 | -7.7 | 64% | 116.3 | bf 86 / brk 26 / flip 25 |
| A2 package, T1-always (containment) | 186 | +24.6 | 60% | 67.8 | tgt 182 / brk 4 |
| A3 package, second target (containment) | 157 | +31.0 | 59% | 73.3 | tgt 148 / brk 7 / flip 2 |

Controls and A1 are unchanged from the invalidated run by construction
(fix-isolation verified); they are reprinted for the contrasts.

## Contrast-scoped verdicts (per the pre-registered statements)

- **A2/A3 vs A0b (the C2-vs-C1 package contrast):** +24.6 / +31.0 vs
  +104.8 -- the package still loses to the matched control by 80.2 / 73.8
  points on this window. The C2 layer does not earn its place over C1 here.
- **A2/A3 vs A0a (operational headline, cadence change included):** +24.6 /
  +31.0 vs +47.4 -- still under the deployed control by 22.8 / 16.4.
- **A2/A3 vs A1 (the veto + target-exit increment):** +32.3 / +38.7 points
  ABOVE the pattern-isolation arm. Given pattern entries, the vetoes plus
  frozen-target exits now add rather than destroy -- the increment's sign
  flipped with the fill fix.
- **A1 vs A0b (the only S3.1-relevant contrast): untouched** at -7.7 vs
  +104.8; the target branch never fires in A1. Charter S3.1's verdict
  (patterns added no information beyond the continuity break on this
  window) stands exactly as written.

## The born-beyond class at real prices

The mechanism is real but an order of magnitude smaller than the invalid
run claimed: A2 carries 73 born-beyond trades netting -21.3pp against
+36.5pp from the other 113 (the class still drags, at real fills); A3's 77
born-beyond trades net +0.6pp against +42.3pp from the rest. The
user's T1-floor entry guard remains the mechanism-motivated repair for the
class, as a separately pre-registered variant with an a-priori value --
this rerun neither strengthens nor weakens that case by scoreboard.

## What survives, what reverses (kill-first reading)

- **SURVIVES -- MAE-tail collapse, now on honest fills and stronger:**
  package mean episode MAE 0.92% (A2) / 1.48% (A3) vs 2.6-2.8% controls;
  worst runner 9.0% / 28.7% vs 37.1%; give-back p90 3.3 / 4.5 vs ~8.7pp.
  Roster max drawdown roughly halves (67.8 / 73.3 vs 122.2-131.5). The
  exit-speed-vs-tail trade-off is real and now priced correctly -- and it
  still costs more expectancy than it saves on this window.
- **SURVIVES -- chop-veto dominance and non-transfer:** with coherent
  denominators (amendment: vetoes evaluated for every candidate), A2 flags
  chop on 2,286 + 537 both of 3,104 candidates (91%). The fixed-percent
  transfer failure stands; ATR-scaled variants remain the named deferred
  repair.
- **REVERSES -- the plain 3-2 census:** the invalid run's "largest and
  worst class" (roster-scope 139 trades, -151.2pp, 29.5% win) becomes 67
  trades, +43.4pp, 52.2% win under containment. The class census was
  dominated by the impossible-fill artifact, not by the pattern. Labeled
  ceiling-read only; per-pattern promotion stays forbidden.
- **Candidate counts are flat-time-dependent:** A2 candidates 3,104 (was
  3,763) because longer-lived positions spend fewer bars flat. Veto-rate
  reconciliation is now exact: entries = candidates - (vetoed + no_target -
  no_target_vetoed) = 3104 - (2892 + 79 - 54) = 187 (A2; one open at
  window end) and 2965 - (2753 + 112 - 60) = 160 (A3).

One window, one regime, gross, in-sample. The spread is the finding;
nothing here is a deployment claim.
