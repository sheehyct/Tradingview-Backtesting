# TVB-25 exit round -- exit design + ladder bottom + fresh window -- pre-registration

**LABEL: PRE-COMMITTED LAYER ABLATION (thesis exits individually, risk
overlays as with/without contrasts, ONE labeled composite endpoint that
never adjudicates its parts) + the ladder-bottom validation + fresh-window
replication. NO deployment claims. NO arm, profile, depth, or threshold
promotion. Kill-first: the job is to find where each exit design fails,
not to confirm it. Every conclusion attaches to the contrast that isolates
it; package arms NEVER adjudicate charter S3.1.**

- Declared: 2026-08-15 (TVB-24 morning design session), BEFORE any exit
  code exists. Git HEAD at declaration: a0160bd.
- Author: the 2026-08-15 design session -- every ruling below was made by
  the USER in-session (AskUserQuestion rounds); items D1-D8 are Claude
  declarations flagged in-session and approved with the plan.
- Engine: the committed Python twin (analysis/paper/engine.py, TVB-23
  extensions included), extended per this document, over archived
  Hyperliquid bars (analysis/paper/bars/, extended by the fresh harvest
  below). Headless. TV mirroring is ON DEMAND after results (ruling 8) --
  a mirrored arm earns its own parity gate before any live claim.
- Relation to prior rounds: window/universe/units/fill/detection
  conventions inherit tvb21_tier_b_prereg.md (incl. the 2026-08-09
  containment amendment) and tvb23_t1floor_prereg.md verbatim. Committed
  comparators: analysis/paper/tier_b/ (A0a/A0b/A1/A2/A3) and
  analysis/paper/tier_b_t1floor/ (D1..D5/DINF/A1F/D1ATR).

## Where this round comes from (mechanism, not scoreboard)

TVB-23/24 receipts: the whole-arm depth curve's shallow-top is an
OCCUPANCY effect (matched-entry receipt: on the 37 trades closed in all
six depth arms, realized P&L rises strictly with depth 38.4 -> 66.2pp),
while the uncensored book stays BIMODAL (A1F census: 45.7% stall at 1-2
rungs, 33.3% reach 4+, mean 2.81). No single fixed depth serves both
modes. Separately: the canonical STRAT structural stop and the intrabar-3
invalidation exit have never been implemented; the charter's C0 rung
(minimal continuity + state stop) has never been RUN, and the BF exit's
reputation was earned under the old pre-M+T machinery (user provenance
statement, 2026-08-15) -- its value under current machinery has never been
isolated. The retracement-label exit stays named-deferred (census: labels
fire before 0.02-1.3 rungs of progress on 48-100% of trades).

## User rulings (2026-08-15, all a-priori)

1. **Structure:** thesis exits tested individually; risk overlays as
   with/without contrasts; one labeled composite endpoint. All four
   candidates enter.
2. **C0 state stop = 2-against at 1H close:** exit when a completed 1-hour
   bar breaks the PRIOR hour's opposite extreme against the position (a 2D
   against a long; mirror shorts), evaluated at that bar's close (charter
   3.5's own example; strict one-tick break, house operators).
3. **Ladder bottom = TWO arms** on the control's identical 1H-breakout
   entry stream: S0a state-stop-only and S0b state-stop + flip backstop;
   C1 comparator = committed A0b. Isolates the BF layer AND prices the
   flip backstop standalone.
4. **Partial arms = BOTH** P1 and P2 (specs below); "the spread between
   them IS the reading."
5. **P2 floor semantics:** the floor ARMS after the first bank at T2; a
   subsequent T1 containment touch exits ALL remaining unfilled middle
   tranches at T1; the RUNNER survives and exits at BREAKEVEN (entry
   price). The -0.25% small-loss runner-floor variant is NAMED-DEFERRED
   (one declared value runs; never tuned on this sample).
6. **Risk overlay = structural + ATR:** pattern entries carry their
   canonical per-setup STRAT structural stop (table below); setups without
   a defined anchor AND all control entries default to the ATR stop (D2).
7. **Fresh window:** 2026-08-03 00:00 UTC -> the latest complete UTC day
   at run time (labeled SHORT / sign-indeterminate), then EXTENDED through
   2026-08-31 24:00 under this same document when the month completes.
   Design ruled before looking; both looks stay honest.
8. **Mirror policy:** headless first; TV mirroring on demand after
   results, per-arm parity gate before any live use (TVB-22/24 pattern).

## Claude declarations (flagged in-session, approved with the plan)

- **D1** X1 extension threshold: extended = reached rung 3 of the frozen
  entry-snapshot ladder (reach convention, entry bar excluded -- committed
  census conventions). Structural ground: the bimodality boundary
  (stall = 1-2, run = 4+). Never tuned.
- **D2** ATR stop: 3 x Wilder ATR(14) on the 1H aggregation, price units,
  against entry (engine _Atr verbatim; value as of the last completed 1H
  bar; no stop until the window fills). Continues the 1x/2x veto family's
  rung shape; instrument-proportional per the veto-transfer receipt.
- **D3** Stop fill convention: stops exit AT the level on containment
  touch (l <= stop <= h); a bar wholly beyond the stop (gap-through)
  exits at that bar's OPEN. Deliberately the pessimistic mirror of the
  target convention (targets do NOT fill on gap-past; stops MUST).
- **D4** P1 has no retrace floor (the floor is P2's feature).
- **D5** Full-position risk exits (structural/ATR stop, intrabar-3, brk,
  flip) close ALL remaining tranches at their trigger in every tranche
  arm.
- **D6** Intrabar-3 scope: pattern-entry arms only; 5m-quantized -- exit
  at market (the 5m close) on the bar where the entry hour's opposite
  side breaks, entry bar's own completing case declared degenerate.
- **D7** Net-fee reporting columns (taker 0.0125%/side, TVB-2) ride every
  results table. Reporting only.
- **D8** Fresh-window scope: all 13 existing arms rerun on the fresh
  window (replication); the 9 new arms run on BOTH the July window and
  the fresh window.

## Per-setup structural stop table (skill 5.2 anchors; binding)

| Setup | Structural stop anchor |
|---|---|
| 1-2-2 | trap bar's opposite extreme (the 2 that broke the inside bar) |
| 2-2 Reversal | prior 2-bar's opposite extreme |
| 1-3 | the 3 bar's opposite extreme (the trap) |
| 1-3-2 | the 3's opposite extreme |
| 3-2 | outside bar's opposite extreme (wide by nature; declared) |
| 3-2-2 | outside bar's opposite extreme |
| 3-1-2 | bar0 = the 3's opposite extreme (X-1-2: bar0, NOT the inside bar) |
| 2-1-2 Reversal | bar0 = the first 2's opposite extreme |
| 2-1-2 Momentum | bar0 = the first 2's opposite extreme |
| 1-3-1-2 | the 3's opposite extreme (compound bar0; least-canonical, flagged) |
| controls / degenerate anchor | ATR stop (D2) |

Anchors are captured at detection (Signal gains the anchor field);
pine-exact DETECTION is untouched -- stops are a NEW layer sourced from
the skill, since no pine defines them (divergence-from-pine-exact scope
declared here).

## Arms (9 new; declared exhaustively)

Ladder bottom (control 1H-breakout entries; identical stream/costs):

| Arm | Exits |
|-----|-------|
| S0a "C0-pure" | state stop (ruling 2) ONLY |
| S0b "C0+flip" | state stop + flip backstop |

Thesis exits (package base = D1's entry config: pattern entries, floor
0.25%, fixed 1%/2% vetoes -- exit policy the ONLY delta vs D1):

| Arm | Exits |
|-----|-------|
| P1 "two-piece" | 50% at frozen T1; 50% runner to BF harvest-touch; brk/flip on; no floor (D4) |
| P2 "runner profile" | skip T1; 40% T2 / 20% T3 / 20% T4 / 10% T5 (containment touch, frozen rungs); 10% runner to the BF harvest-line touch; floor per ruling 5; brk/flip on |
| X1 "BF overlay at extension" | no target exits; BF harvest-touch ARMED only once rung 3 reached (D1); brk/flip on |

Overlay contrasts:

| Arm | Delta |
|-----|-------|
| D1+i3 | D1 + intrabar-3 invalidation |
| D1+stop | D1 + structural/ATR stop overlay |
| A0b+stop | matched control + ATR stop |

Composite endpoint (reading only, never adjudicates parts):

| Arm | Config |
|-----|--------|
| PX "everything on" | P2 + intrabar-3 + structural/ATR stops |

## Contrast statements (binding; conclusions attach here and nowhere else)

- S0a / S0b vs A0b = does the BF exit layer earn its place over minimal
  continuity (the never-run charter rung); S0b - S0a = the flip
  backstop's standalone price.
- P1 / P2 / X1 each vs D1 = exit policy isolated on the floored package
  book.
- D1+i3 vs D1; D1+stop vs D1; A0b+stop vs A0b = each overlay's price.
- PX = labeled composite reading.
- July window = in-sample comparability; fresh window = the replication
  read for EVERYTHING (existing arms included, D8). The spread is the
  finding; extreme numbers are questions, not verdicts.

## Metrics + pre-committed diagnostics

Tier B row/rollup schema throughout, PLUS: per-tranche P&L attribution in
events and rows (fractions sum to 1.0, reconciliation asserted); gross AND
net (D7) columns; matched-entry (shared-prefix) per-trade exit comparison
across D1/P1/P2/X1/PX (same entry mechanics by construction); ladder +
retracement censuses per arm (committed round_census conventions); stop /
floor / i3 exit-kind splits with counts and P&L per kind; per-symbol ATR%
context carried forward; entry-audit receipts regenerated over the new
arms (containment + close-benchmark).

## Execution + provenance

- Order: (1) THIS document committed before any code; (2) fresh-bar
  harvest (roster 5m/1h/1d, 2026-08-03 -> latest complete day; bar hashes
  recorded); (3) engine extensions behind inert defaults -- existing paths
  bit-identical (full suite + hardened determinism gates field-equal);
  (4) runner analysis/paper/tier_b_exits.py in the tier_b_t1floor.py
  pattern with the TVB-24-hardened fail-closed gate families (row/field
  cardinality both directions, all-pairs entry streams with
  prefix-next-must-be-exit, census open checks) + tranche reconciliation;
  (5) run + censuses + report (docs/experiments/tvb25_exit_round_report.md,
  contrasts only); (6) month-end window extension under this document;
  (7) TV mirror on demand (ruling 8).
- Manifest records prereg_blob_sha256 of THIS file (TVB-24 provenance
  protocol), executed blob hashes, git dirty path list, bar hashes, all
  gate results.
- Gate-triggered corrections follow the TVB-24 forward protocol: commit
  the correction BEFORE the clean rerun.
- Reading rules: findings-first in words, no bare cell codes; every
  discussed difference gets a structural-vs-sample tag; kill-first.

## Named deferred (NOT run in v1; on record so they cannot be smuggled in)

Retracement-label exit variants; the -0.25% runner-floor variant;
vol/instrument-conditioned timeframe sets; the realism layer (position
sizing, dollar P/L, leverage, margin) and the $50-or-less canary wallet;
flip-uncoupling redesign; kernel-vs-Pine charter question; 15m/30m
signal-TF arms; RTH-anchored clock arms; weekend protocol arms; any
promotion of an arm, profile, depth, or threshold.
