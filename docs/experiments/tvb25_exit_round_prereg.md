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

## Amendment 2026-08-16 (TVB-24 audit F1/F2 fold; user-ruled, before code)

The TVB-24 Codex audit (docs/reviews/tvb24-codex-audit.md, RETURNED
2026-08-16) confirmed two defects in THIS document: F1 HIGH -- the
S0a/S0b-vs-A0b contrast replaces the whole exit family (A0b inherits
BF+brk+flip; the engine has no state-stop field), so it cannot isolate the
BF layer; F2 MEDIUM -- the exit state machine underdetermines same-bar
collisions and several arm mechanics. Every ruling below was made by the
USER in a live walkthrough (2026-08-16, three AskUserQuestion rounds);
items D9-D14 are Claude declarations approved as a bundle. Nothing above
this line is rewritten. No code existed when this amendment was committed.

### A. F1 repair -- BF isolation restored, reference relabeled

- NEW ARM **S0c "state+BF"** = state stop + BF harvest touch (no flip, no
  brk), on the same control 1H-breakout entry family. The round is now
  **10 new arms**.
- Contrast statements REPLACE the first ladder-bottom bullet: S0c - S0a =
  the BF exit layer's standalone price on the state-stop base; S0b - S0a =
  the flip backstop's standalone price; **A0b is an exit-family REFERENCE**
  -- S-family vs A0b is a family contrast and never component attribution.
- **D12** (naming + occupancy): S0a's "C0-pure" label is RETIRED -- S0a
  implements the USER-RULED 2-against variant of charter 3.5 (a completed
  1H bar breaking the prior hour's opposite extreme; a NEUTRAL 1H close
  does NOT exit -- deliberately narrower than the charter's
  neutral-or-opposite example). "Identical stream/costs" in the arms table
  is corrected to: identical candidate/trigger rule; realized entry
  streams may diverge through one-position occupancy (the TVB-23 lesson).
  The matched-entry diagnostic and the entry-stream gates EXTEND to
  S0a/S0b/S0c/A0b.

### B. F2 repair -- the deterministic exit state machine

- **Same-bar collision precedence** (NEW arms only; TVB-22/23 arms keep
  their parity-pinned incumbent race): within one 5m bar, exits are
  evaluated in this order, first hit wins, and any risk exit closes ALL
  remaining tranches at its trigger (D5):
  1. intrabar-3 (invalidation before stop, skill 5.4)
  2. structural/ATR stop
  3. protective retrace levels (P2 T1-retrace middle exit, runner
     breakeven, armed floor)
  4. tranche profit targets, in ladder order (T2 before T3 ...)
  5. BF harvest touch
  6. brk
  7. flip
  8. state stop (close-evaluated, hour-completing bar)
  PROVISIONAL by user ruling: this is the pessimistic (risk-first)
  convention; if the D9 collision census shows it biting materially, the
  named alternatives (skill-5.4 target-first order; incumbent
  profit-first order) are revisited by a further dated amendment -- never
  silently.
- **Two fill classes.** PROTECTIVE levels (structural/ATR stop, P2
  retrace floor, T1-retrace middle exit, runner breakeven) follow D3:
  fill AT the level on containment touch (l <= level <= h); a bar wholly
  beyond fills at that bar's OPEN (gap-through MUST fill). PROFIT levels
  (tranche banks T2-T5, P1's T1, BF touch) fill on containment touch
  ONLY and are never gap-credited -- a gapped-past target stays unfilled
  and waits. Close-evaluated exits (i3, brk, flip, state stop) fill at
  the evaluating 5m close.
- **P2 short ladder** (fewer than 5 frozen rungs): each missing rung's
  fraction FOLDS INTO THE RUNNER (less mapped structure = more runner --
  the profile's own spirit). The floor arms after the FIRST executed
  bank; a ladder with no bankable rung leaves 90% runner and the floor
  never arms. There is NO skip rule -- a P2-specific skip would desync
  its entry book from D1 and break the matched-entry design.
- **P2 same-bar arm chain:** arm-and-fire. A single 5m bar containing
  both the T2 bank and a T1 containment touch banks T2 AND exits the
  middles at T1 on that bar (one pessimism rule everywhere; D9 counts
  these bars).
- **Intrabar-3 pinned (D6):** the level is the PRIOR 1H bar's opposite
  extreme -- the price whose strict break makes the entry hour a Type 3
  -- captured immutably at entry. ACTIVE ONLY until the entry hour
  completes (a later break is ordinary 2-against territory, the state
  stop's job). Exit at the 5m close of the breaking bar. Degenerate case:
  the entry 5m bar itself completes the 3 -> exit at that same bar's
  close.
- **X1 pinned:** (a) a frozen ladder with fewer than 3 rungs NEVER arms
  -- exits are brk/flip only (declared structural consequence: the short
  ladder is the stall mode where the harvest was not earned); (b)
  rung-3 reach and a BF touch on the SAME 5m bar arm-and-fire, evaluated
  in the ruled race order; (c) "the BF line" is the engine's live v6.1
  alive-line set at touch time -- never an entry snapshot; a line retired
  before arming simply means no BF exit until another qualifies.
- **Structural stop discipline:** the anchor is captured ONCE, at the
  FIRST detection of the signal identity, into a new immutable
  `Signal.stop_anchor` field with its source-bar index recorded (distinct
  from the detector's ladder `anchor`/`anchor2` locals). Setup bars are
  closed, so re-detections of a persisting signal must never drift the
  anchor -- asserted in code. DEGENERATE = non-finite, equal to the entry
  fill, or on the profit side of it (for a long the stop must sit
  STRICTLY BELOW the fill; mirror shorts) -> ATR fallback (D2), counted
  per arm. The 1-3 and compound 1-3-1-2 rows of the stop table are
  relabeled **"chosen experimental anchor"** (the skill permits
  trap/inside-extreme alternatives there; the table's choice is declared,
  not uniquely canonical).

### C. Declarations D9-D14 (Claude-flagged, user-approved as a bundle)

- **D9** Collision census: per arm, the count of exit bars on which more
  than one exit class was simultaneously satisfiable, reported beside the
  exit-kind splits -- operationalizes the "flag it if it does not work as
  intended" caveat on the risk-first convention.
- **D10** Partial-fee formula (reporting-only, rides D7): entry fee
  (taker 0.0125%) on the FULL position at entry; each tranche exit
  charged on its exited fraction; a window-end open fraction carries its
  entry-fee share only (flagged); per-tranche P&L position-fraction-
  weighted; full-precision floats, rounding only at reporting (4dp).
- **D11** Floor vocabulary: P1's "no floor" (D4) means no post-bank
  RETRACE floor. P1, P2, and X1 all inherit D1's 0.25% entry-distance
  floor VETO as part of the shared package entry config (it is an entry
  filter, not an exit).
- **D12** In section A above.
- **D13** The fresh window's "latest complete UTC day" endpoint is
  resolved at harvest time and PINNED (exact end timestamp + bar hashes
  recorded) before any run.
- **D14** State stop inclusive reading: ANY completed hour whose range
  broke the prior hour's opposite extreme against the position triggers
  it -- a Type-3 hour included, since it did break that extreme -- and
  fills at that hour's close (the completing 5m bar's close print).

### Ruling clarification 2026-08-16 (user-ruled, before engine code)

P2 runner after the T1-retrace event = reading A: the runner KEEPS riding
toward the BF harvest touch with a breakeven floor at the entry price --
both levels live, protective-first on collision (the classic runner with
breakeven protection). The literal exits-at-breakeven-only reading was
rejected.

### D13 pin (2026-08-16 harvest, before any run)

Fresh window = **2026-08-03 00:00:00 UTC -> 2026-08-16 00:00:00 UTC**
(latest complete UTC day at harvest time = 2026-08-15). Harvested via
analysis.paper.archive, full roster x 5m/1h/1d, all 33 fetches hit the
HL floor; bar hashes = the harvest commit itself (files tracked).
Merge-integrity check run before commit: zero July-window rows changed,
zero rows dropped, zero 5m continuity holes; exactly one post-window row
revised per file (the 2026-08-04 00:00-00:50 UTC bars captured while
FORMING by the 2026-08-04 00:45Z archive run, now completed values).
[Superseded on the per-file count by the 2026-08-16b amendment below:
31 of 33 files, two timestamps.]

### Amendment 2026-08-16b (TVB-26, external-audit fold; user-ruled where noted)

Repairs and clarifications from the returned TVB-25 audit
(docs/reviews/tvb25-codex-audit.md). Nothing above this section is
rewritten; the canonical artifacts are regenerated under this text.

- **D14 entry-hour ruling (audit F3; USER-RULED, literal-inclusive):**
  the entry hour COUNTS. An entry on the hour-completing 5m bar of an
  hour whose range broke the prior hour's opposite extreme against the
  new position exits at that same bar's close (state stop, counted
  `state_degenerate`) -- exactly as a mid-hour entry in that same hour
  already would at the hour close, and mirroring the i3 degenerate
  convention on the entry bar. On a shared entry bar i3 precedes state
  (race steps 1 vs 8). The intrahour position of the break is NOT
  consulted (pessimistic, order-free within the hour, consistent with
  D14's Type-3-hour-included text). The alternatives (entry hour never
  counts; post-entry-breaks-only) were declined -- both would also
  rewrite the already-ruled mid-hour behavior.
- **D9 census repair (audit F1):** the collision census accumulates
  class satisfiability across the ordered within-bar state transitions
  (the bank->floor and retrace->breakeven armings add the protective
  class mid-bar); each bar counts once. The TVB-25 canonical counters
  understated the P2/PX arm-and-fire collisions (report Finding 5 and
  the ledger line are superseded by the regenerated artifacts).
  ADDITIVE diagnostic: `collision_pairs` (counts per colliding class
  combination) rides beside the pinned counter so the promised revisit
  of the provisional risk-first order can see WHICH combinations
  collide -- reporting-only, no behavior change.
- **P2 no-bank ladder (audit F6a):** "leaves 90% runner" above is
  corrected to **100% runner** -- folding all four missing banks
  (40+20+20+10) into the 10% base runner leaves the full position
  riding. The engine, fixtures, and committed events already implement
  100%; the prose was arithmetically wrong.
- **Stop-anchor source record (audit F6b):** the promised source-bar
  record is implemented as `stop_src_ts` -- the absolute signal-TF
  bar-start timestamp of the anchor source, derived from the relative
  token at detection -- frozen with the anchor, drift-asserted, and
  emitted on entry events beside `stop_src`.
- **D13 merge note correction (audit F7):** the harvest revised one
  shared post-window row in 31 of 33 files (22 rows at 2026-08-04
  00:00 UTC, 9 at 00:50 UTC); MRVL 5m and MSFT 5m revised none (their
  prior files ended before the appended sequence). The verified claims
  stand unchanged: zero rows dropped, zero July-window rows changed,
  zero 5m continuity holes.
- **Zero-duration episodes (audit F2):** i3/state degenerate episodes
  (exit ts == entry ts) keep their P&L and counted reason; they are
  excluded from MFE/MAE/give-back (no excursion window exists). The
  runner supports them end-to-end (regression-tested).
- **Gate expectation (audit F4):** the entry-stream gate's expected arm
  set is DECLARED -- the full family on canonical runs, the requested
  subset plus anchors on smoke runs -- never derived from produced
  streams.

**Revisit outcome (2026-08-16, USER-RULED after the corrected census):
the risk-first convention STANDS.** Corrected collision counts (roster
scope): P2 18/11 (july/fresh), PX 25/12, A0bS 5/4, P1 1/1, S0b 1/1, S0c
1/0. Decomposition: every prot+tgt bar (18+19+10+9 across the tranche
arm-windows) is the bank->floor ARM-AND-FIRE chain, where the order is
structurally forced (the floor does not exist until the bank arms it) --
zero already-armed-floor collisions; the genuinely order-sensitive bars
(stop vs bf/brk/flip on A0bS, i3 vs stop and prot vs stop on PX, bf vs
state on S0c) are 3-6 per arm-window, and the ruled order books the
worse fill there by design. The named alternatives are NOT priced; the
census + collision_pairs ride every future run as the watchdog.
