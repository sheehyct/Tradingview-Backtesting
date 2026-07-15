# TVB-11 Champion Search -- Pre-Registration (DRAFT v1, PENDING USER APPROVAL)

Date drafted: 2026-07-14
Status: APPROVED v1.1 (user, 2026-07-14). Amendment record: v1.0 -> v1.1
changes were made AT approval, PRE-RUN, on user request (TVB-10 C2
precedent): added the OPTIONAL Stage C scalp-profile satellite (Section 5,
deferred by default) and the post-run winner-indicator deliverables
(Section 11). No run had executed when these were added. Any further
amendment must be PRE-RUN and recorded here with its reason.

---

## 1. Purpose and epistemic license (read first)

This is a DELIBERATE, LABELED overfit exercise (user directive 2026-07-13,
confirmed 2026-07-14): sweep the full mechanism space of the TFC+BF strategy
-- "all the toggles, options, ways to enter/exit" -- and find what performs
best across the most time and symbols available. The product is a SECOND
CONTROL: the in-sample CEILING, complementing the crude a-priori control
(the floor). Every future complexity addition is judged by where it lands
between floor and ceiling and whether that position survives widening.

Charter positioning (Section 0/1): selection on the sample is ALLOWED here BY
DESIGN because deployment is FORBIDDEN here BY DESIGN. The charter Section 7
rule "timeframe sets are chosen a-priori and then NOT tuned" is deliberately
SUSPENDED inside this pre-reg only -- tuning gate sets on the sample is the
point of a ceiling measurement. Nothing in this document licenses deploying,
promoting, or preferring any configuration found. The champion is a ruler,
not a strategy. Charter S1's "over-specification as instrument" is the
operating clause: the champion's out-of-window/off-symbol decay measures the
generalization gap directly.

Reporting rules:
- Report the champion AND the plateau around it. A knife-edge champion
  (neighbors much worse) is noise; a plateau is information.
- Any statement about ratchet cells must NAME the ratchet variant used
  (ratchet_c vs ratchet_g) -- the E2/GPT fork showed the verdict flips.
- No keep/kill or deployability language anywhere in the results writeup.

## 2. Prep items (complete BEFORE any pre-registered run)

- P0a. DONE 2026-07-14 (TV relaunched on CDP, user go-ahead; GPT inactive).
  GPT source read read-only from script id USER;a5a6fd4be3b1457ea1f6f81a3a
  071c97 v5, title verified. Semantics recorded in Section 3. Both scripts
  otherwise agree: identical BF-1 engine (30m/10, [1]+lookahead_on idiom),
  identical local period-open gate reconstruction; the GPT script is
  flip-exit-only with gate fixed full6 and regime fixed W+D.
- P0b. VERDICT 2026-07-14: **closedtrades.profit() is NET of commission.**
  Direct per-trade arithmetic from the harness trade table (anchor C3
  record, docs/experiments/tvb11_champion_anchor.jsonl): profit ==
  (exit-entry)*size - commission exactly (1e-6) on independent trades;
  matches GPT's 2026-07-11 audit; SUPERSEDES the TVB-7 "GROSS" calibrated
  fact (corrected in memory, with the flag that the VBT port's governor
  parity should be re-verified on marginal trades). HARNESS DECISION: the
  champion governor KEEPS profit()>0 classification (i.e., net) -- it
  matches every prior Claude-lineage dataset (TVB-6/9/10, E2) and the
  cross-script anchor requires bit-parity with the E2 engine. The known
  GPT-vs-Claude governor delta (GPT classifies explicit gross) stays a
  disclosed dataset difference, marginal-trade-only.
- P1. DONE 2026-07-14. Harness built (pine/tvb_exp_champion.pine, committed)
  with bf_reentry = recycle | ratchet_c | ratchet_g per Section 3;
  strat-methodology skill invoked before writing. Deployed via the
  Make-a-copy flow to NEW script id USER;1a68d411fe694ccda089602f41c2bf69
  ("TVB-EXP Champion [TVB-11]"); compiled 0 errors; verified new id +
  unchanged modified stamps on ALL other scripts (incl. both GPT scripts
  and the pv20 STRATEGY anchor). Trap note: the fresh editor tab was bound
  to "TVB-EXP BF Sweep [GPT]" when pine_open loaded the Claude base --
  the Make-a-copy flow is what made the save safe; never Ctrl+S before
  the copy. P0b polarity probe and session-robust clocks are in the
  deployed source; their VERDICTS land with P3.
  CRITICAL (found at P0a): the Claude-base harness marks arm/exit period
  closes by wall-clock modulo (time_close % period == 0). Correct on 24/7
  UTC perps; on RTH mirror charts intraday periods end OFF the wall-clock
  hour (NYSE 60m periods end 10:30, 11:30, ...), so the modulo clock never
  fires except at session close -- exits would silently never arm. The
  harness MUST replace modulo clocks with session-robust equivalents (GPT
  idiom: time_close == time_close(tf)) BEFORE any mirror run, and the two
  clock idioms must be shown equivalent on one perp cell (part of P3).
  Check C3 exists to catch exactly this class on the mirror side.
- P2. Collector: batch runner over the TV MCP with the GPT-proven integrity
  method -- the script echoes symbol + all cell inputs into machine-readable
  output; a run is REJECTED unless the echo matches the requested cell.
  Record the loaded window (first/last bar, bar count) with every run.
- P3. Regression anchor -- AMENDED PRE-GRID 2026-07-14 (recorded honestly):
  the original form ("reproduce committed E2 results within window drift")
  is NOT EVALUABLE anymore -- TV's 5m data floor slid past May 1 (now
  ~20.7k bars from ~May 3) and the gate's monthly-open warmup then pushes
  the first tradeable bar to Jun 1, so E2's May trades are unreachable
  (evidence is time-perishable; the TVB-6 lesson). REPLACED with a STRICTLY
  STRONGER check: cross-SCRIPT equivalence -- the unchanged E2 engine
  ("TVB-EXP BF Exit [Claude]", old modulo clocks, 'ratchet') and the
  Champion ('ratchet_c', session-robust clocks) run the SAME cells
  (C1/C3/C6) on the SAME loaded bars and must agree TRADE-FOR-TRADE
  (times, prices, qty). This isolates exactly the P1 changes and IS the
  pre-registered clock-equivalence proof on a perp. Any trade mismatch =
  STOP. Collector command: anchor2; artifact
  docs/experiments/tvb11_champion_anchor2.jsonl. (The first anchor pass,
  tvb11_champion_anchor.jsonl, is retained as the P0b evidence carrier and
  as the record of the data-floor discovery.)

## 3. Ratchet variant definitions (to be completed at P0a)

- ratchet_c (Claude, from committed source): after a BF exit, the working
  re-entry stop is raised to strictly beyond the running post-exit extreme:
  eff_trig = max(natural arm trigger, extreme + 1 tick). Order always
  resting while gate-aligned; fires the instant price exceeds the extreme.
  Observed E2 behavior: trade counts ~unchanged vs recycle, better prices.
- ratchet_g (GPT, CONFIRMED from source 2026-07-14): an ARMING GATE -- the
  stop is never moved. After a BF exit, a block direction is set (+1 long /
  -1 short; a SINGLE shared slot, so a BF exit in the other direction
  OVERWRITES the block -- unlike ratchet_c's independent per-side blocks)
  and the extreme initializes at the exit bar's high/low, advancing on
  every later chart bar. The entry order is placed ONLY when the NATURAL
  trigger (prior completed arm-TF bar extreme +/- 1 tick) stands strictly
  beyond the running extreme; the stop rests at that natural trigger.
  Consequence: in a monotone burst the natural trigger always lags the
  running extreme, so re-entry is impossible until price pauses for at
  least one full arm period (a completed arm bar whose extreme holds as the
  running max) and then breaks it. Block clears on the blocked-direction
  fill or on full opposite alignment at an exit-clock close (same clocks as
  ratchet_c). This explains the observed 280-5160 min waits and ~4% price
  extension.

One-line summary: ratchet_c = momentum-continuation reading (enter the
instant price makes a new post-exit extreme); ratchet_g = structure-
confirmation reading (enter only after a completed arm bar stands beyond
the extreme and breaks). Both are defensible readings of the same E2 spec
sentence; the champion grid carries both, and no result sentence may say
"ratchet" without the suffix.

## 4. Frozen roster (a-priori; ratified by user 2026-07-14)

| # | Perp | Mirror | Mirror type |
|---|------|--------|-------------|
| 1 | HIP3XYZ:MUUSDC.P | NASDAQ:MU | RTH session mirror (Stage A pair) |
| 2 | HIP3XYZ:SILVERUSDC.P | COMEX:SIL1! | VENUE-FIDELITY mirror (exemption: underlying is not an RTH equity; perp pegs to futures per user obs.) |
| 3 | HIP3XYZ:HOODUSDC.P | NASDAQ:HOOD | RTH session mirror |
| 4 | HIP3XYZ:ORCLUSDC.P | NYSE:ORCL | RTH session mirror |
| 5 | HIP3XYZ:NFLXUSDC.P | NASDAQ:NFLX | RTH session mirror |
| 6 | HIP3XYZ:HIMSUSDC.P | NYSE:HIMS | RTH session mirror |
| 7 | HIP3XYZ:MRVLUSDC.P | NASDAQ:MRVL | RTH session mirror |
| 8 | HIP3XYZ:RKLBUSDC.P | NASDAQ:RKLB | RTH session mirror |

Excluded by design: the Korea-linked cluster (DRAM, EWY, SMSN, SKHYNIX) --
session-structure confound, reserved for the weekend/Korea pre-reg family.
Exchange prefixes to be verified against TV symbol search before runs;
corrections are clerical, not amendments.

## 5. Design

### Stage A1 -- core factorial on the MU pair

Swept axes (full factorial within each chart TF):

| Axis | Values | n |
|------|--------|---|
| Gate set G | full6 {60,120,240,D,W,M}; ctrlA4 {60,D,W,M}; slow3 {D,W,M} | 3 |
| Exit mode X | state; flip | 2 |
| Direction D | both; long-only; short-only | 3 |
| BF config B | off; same_side x {recycle, ratchet_c, ratchet_g}; any_side x recycle | 5 |
| Arm/exit TF pair T | per chart TF, below | 2-4 |

Chart TFs and their valid arm/exit pairs (arm >= chart, arm tiles exit,
exit tiles all gate TFs; deepest loadable window per TF, recorded per run):
- 5m: 15/15, 5/15, 5/30, 15/60 (4)
- 15m: 15/15, 15/30, 15/60 (3)
- 60m: 60/60, 60/240 (2)

Cells per venue: (3x2x3x5) x (4+3+2) = 90 x 9 = 810. Both venues: 1620.

Fixed in A1 at the user's live config (structural declaration, not tuned):
regime = stand_aside on W+D; governor = ratchet; commission 0.0125%/side;
slippage 1 tick; margin 0/0; bar magnifier ON; 100% equity, no pyramiding;
initial capital 10,000. Costs are held IDENTICAL on mirrors deliberately:
the mirror delta must isolate session structure, not cost model. any_side
is limited to recycle (E0 measured it negative; kept for completeness only).

### Stage A2 -- fixed-axis interaction satellites

Take the top-10 A1 configs on the MU perp (by the primary metric) and re-run
each under {regime off}, {governor off}, {both off}: 30 runs per venue, 60
total. Purpose: verify the fixed axes did not distort the ranking. If any
satellite re-orders the top-10 materially (rank-1 leaves the top-5), that is
a finding to report, and Stage B carries BOTH variants of the affected
config.

### Stage B -- breadth over the frozen roster

Champion + plateau top-10 (as configs, including chart TF) re-run verbatim
on roster rows 2-8, both columns (7 perps + 7 mirrors): 140 runs. No
re-tuning per symbol. The deliverable is the generalization map: where the
ceiling config lands on names it was not fit to, perp vs mirror.

Estimated total (Stages A1/A2/B): ~1830 runs incl. anchors/canaries. At the
GPT-demonstrated collection rate (~7-9s/run) this is a 4-7 hour automated
collection; the collector must checkpoint so partial progress commits.

### Stage C -- OPTIONAL scalp-profile satellite (deferred by default)

Added at approval on user request; explicitly NOT the main goal. Motivation:
the main grid finds the swing-horizon ceiling; the user's second scenario is
a momentum-scalp profile, and charter 3.5 already maps price stops (not
state stops) to scalp horizons -- so this is a second scenario-champion, not
scope creep. What the main grid does NOT cover: (a) a fast regime layer
(D + 4H stand_aside; size_down variant deferred -- not implemented in the
harness), (b) pure-intraday gate sets with no D/W/M member ({5,15,30} and
{10,30,60}), (c) a fixed %TP/%SL exit family (entry unchanged: trigger +
gate; exits = take-profit % and stop % from entry; at 1x/100% equity, ROE%
== price-move % -- leverage scales both sides, state this wherever ROE is
quoted). Sketch grid: chart TF 1-5m; gates x 2; TP {0.5, 1, 2}% x SL
{0.25, 0.5, 1}%; state-exit control cell per gate. Runs ONLY after Stage B,
time permitting, and ONLY after its own short PRE-RUN amendment fixing the
final cells and the Pine changes (percent exits are new strategy code ->
strat-methodology skill gate applies).

## 6. Scoring and champion definition (pre-declared)

- Primary metric: Total % = (closed net + open P/L) / initial capital
  (TVB-10 dual-accounting convention; open trade marked with exit-side
  slip+commission where the engine reports it, else TV convention noted).
- Secondary (reported, never used for selection): closed %, PF, trade
  count, win %, max DD %, commission paid, long/short split.
- Champion per (venue, chart TF): argmax Total %.
- CONSENSUS champion: best mean rank across the three chart TFs on the MU
  perp. This is THE champion for Stage B; per-TF champions ride along.
- Plateau: top-10 by the same metric per (venue, chart TF). Report the
  spread between rank 1 and rank 10; a >2x Total% cliff inside the top-10
  is flagged as knife-edge.
- Controls reported alongside every table: ctrlA-equivalent (gate ctrlA4,
  state, both dirs, BF off, live regime/gov) and the E2 C1 cell, as floor
  references.

## 7. Pre-registered checks

- C1 (anchor): amended to cross-script equivalence (see P3 amendment).
  **PASS 2026-07-14**: all three cells (C1/C3/C6 configs) trade-for-trade
  EQUAL between the unchanged E2 engine and the Champion on the shared
  20,731-bar MU-perp 5m window (C1 -1667.29/6tr, C3 +1288.95/11tr,
  C6 -715.74/11tr; times/prices/qty exact). Clock-equivalence on perps
  PROVEN; ratchet_c bit-faithful to E2 'ratchet'. Artifact:
  docs/experiments/tvb11_champion_anchor2.jsonl.
- C2 (echo integrity): every accepted run's echoed symbol+inputs match the
  requested cell; mismatches are rejected and logged with counts.
- C3 (mirror sanity): one hand-verified NASDAQ:MU run (trade list inspected
  on the chart) before the mirror batch; confirms session handling (RTH
  bars, gaps) behaves as the script assumes.
- C4 (ratchet variant separation): **PASS 2026-07-14** -- on the current MU
  perp 5m window (20,732 bars) the variants diverge at EXACTLY the two
  post-BF-exit re-entries, ratchet_g entering one-two completed arm bars
  LATER (18:15 -> 18:30; 14:25 -> 15:00) = the arming-gate mechanism;
  identical everywhere else (net 1288.95 vs 1190.50, both 11 trades).
  Caveat recorded honestly: this window separates on TIMING only, not
  counts -- the E2/GPT count-level separation lived in the May bursts,
  which are below the current data floor. Artifact:
  docs/experiments/tvb11_champion_ratchetsep.jsonl (compare vs the C3
  record in tvb11_champion_anchor2.jsonl).

## 8. Pre-registered expectations (score these honestly afterward)

- E1: Champions are venue- and chart-TF-local; the consensus champion is
  the argmax of no single TF. The spread is the finding.
- E2: Mirror (RTH) top-10s are more knife-edged and shifted toward slower
  gates/exits than perp top-10s; fast-gate configs degrade hardest on
  mirrors (session gaps break intraday continuity reconstruction).
- E3: ratchet_c outranks ratchet_g on burst-heavy MU; ratchet_g closes the
  gap (or wins) wherever chop dominates the window.
- E4: The consensus champion beats the ctrlA floor by a large margin
  in-sample (that is what a ceiling is) and decays toward or below the
  plateau median on Stage B names. If it does NOT decay, flag loudly --
  that would be the surprising (structural-candidate) outcome.
- E5: full6 ~ ctrlA4 on 5m (GPT's slow4 finding restated); they diverge at
  60m where the 120/240 gates bind for a larger share of bars.
- E6: BF-off cells dominate the top-10 more often than not (GPT sweep
  precedent), but at least one BF ratchet_c cell reaches a top-10 (E2 C6
  precedent on AMZN).

## 9. Evidence inventory (commit list; TVB-10 review process adoption)

| Item | Artifact |
|------|----------|
| Full run table (all stages) | docs/experiments/tvb11_champion_results.json |
| Per-run loaded windows + echo log | docs/experiments/tvb11_champion_runlog.json |
| Anchor check C1 diff | docs/experiments/tvb11_champion_anchor.json |
| Ratchet separation check C4 | docs/experiments/tvb11_champion_ratchetsep.json |
| Harness Pine source | pine/tvb_exp_champion.pine (new file, committed) |
| Collector script | scripts/tvb11_champion_collect.mjs (or .py) |
| Results narrative | this file, appended sections |

## 11. Post-run deliverables (user directive at approval)

For the top combinations after Stage B: one MINIMAL indicator() script per
winner (separate script per winner -- consensus champion, per-TF champions,
and any plateau member the user picks). Contents: entry/exit signals and
alertconditions ONLY -- enter long, enter short, exit long, exit short,
exit-stop long, exit-stop short (const-string alertcondition names; the
stop-exit pair applies where the winner's exit family distinguishes harvest
vs stop, e.g. BF or Stage C cells). NO info/alignment table, NO timeframe
auto-switching. Inputs limited to UI cosmetics: background color on/off,
bar color on/off, shape colors. This is a deliberate exception to the
standing Desktop-UX Pine style (recorded in memory). These are watch/alert
surfaces; the standing no-deployment rule is unchanged.

## 10. What this pre-reg does NOT license

- No deployment, promotion, or "keep" verdicts. The output is a ruler.
- No charter amendment to Section 7 (the no-tuning rule stays in force
  everywhere outside this document).
- No BF verdict without naming the ratchet variant.
- No reading of mirror deltas as liquidity-only effects (they are joint
  session-structure + gap + liquidity effects; say so each time).
- Weekend-window cells are OUT of scope (separate pre-reg,
  project-weekend-liquidity-protocol).
