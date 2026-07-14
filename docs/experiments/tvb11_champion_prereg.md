# TVB-11 Champion Search -- Pre-Registration (DRAFT v1, PENDING USER APPROVAL)

Date drafted: 2026-07-14
Status: DRAFT. No runs may execute until the user explicitly approves this
document. Amendments after approval follow the TVB-10 C2 precedent: allowed
only PRE-RUN, recorded verbatim with the reason.

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

- P0a. Ratchet-fork source adjudication: pull the GPT script source
  ("TVB-EXP BF Exit [GPT]") via TV MCP, diff its re-entry logic against
  pine/tvb_exp_bf_exit.pine, and record both semantics precisely in this
  file (Section 3). Requires TV relaunch with CDP (user go-ahead required;
  heads-up rule applies while GPT shares the instance). Claude side is
  already characterized from committed source: resting stop RAISED to
  max(arm trigger, post-exit extreme + 1 tick); block clears on re-entry
  fill or full opposite alignment at an exit-TF close.
- P0b. profit() polarity check: settle the TVB-7 (gross) vs GPT audit (net)
  contradiction on closedtrades.profit() with a targeted 3-trade read on a
  live chart. Governor arming depends on it; both prior datasets are
  near-inert under flip so economic impact is low, but the calibrated fact
  must be right before it is baked into more scripts.
- P1. Harness: extend pine/tvb_exp_bf_exit.pine with the third re-entry
  option (bf_reentry = recycle | ratchet_c | ratchet_g) implementing GPT's
  semantics verbatim from P0a. MANDATORY: invoke the strat-methodology
  skill before writing this Pine (trigger mechanics). Deploy via the
  Make-a-copy flow to a NEW script slot ("TVB-EXP Champion [TVB-11]");
  verify by new script id + unchanged modified stamps on all other scripts
  (tab-binding trap). STRATEGY slot pv20 anchor stays untouched.
- P2. Collector: batch runner over the TV MCP with the GPT-proven integrity
  method -- the script echoes symbol + all cell inputs into machine-readable
  output; a run is REJECTED unless the echo matches the requested cell.
  Record the loaded window (first/last bar, bar count) with every run.
- P3. Regression anchor: before the grid, re-run E2 cells C1/C3/C6 on MU
  perp with the new script at live config; they must reproduce the
  committed E1/E2 results within window drift. Discrepancy = STOP, no grid.

## 3. Ratchet variant definitions (to be completed at P0a)

- ratchet_c (Claude, from committed source): after a BF exit, the working
  re-entry stop is raised to strictly beyond the running post-exit extreme:
  eff_trig = max(natural arm trigger, extreme + 1 tick). Order always
  resting while gate-aligned; fires the instant price exceeds the extreme.
  Observed E2 behavior: trade counts ~unchanged vs recycle, better prices.
- ratchet_g (GPT, PENDING P0a source read -- hypothesis from observed
  behavior): arming is GATED rather than the stop being raised -- no order
  rests until the natural arm-TF trigger structure itself exceeds the
  post-exit extreme. Observed behavior: fewer/later re-entries (median wait
  280-5160 min vs 5 min), ~4% price extension. Exact clearing rules TBD
  from source; this section MUST be completed before approval of any
  ratchet-cell result.

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

Estimated total: ~1830 runs incl. anchors/canaries. At the GPT-demonstrated
collection rate (~7-9s/run) this is a 4-7 hour automated collection; the
collector must checkpoint so partial progress commits.

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

- C1 (anchor): E2 cells C1/C3/C6 on MU perp reproduce committed values
  within window drift BEFORE the grid (prep P3). Fail = STOP.
- C2 (echo integrity): every accepted run's echoed symbol+inputs match the
  requested cell; mismatches are rejected and logged with counts.
- C3 (mirror sanity): one hand-verified NASDAQ:MU run (trade list inspected
  on the chart) before the mirror batch; confirms session handling (RTH
  bars, gaps) behaves as the script assumes.
- C4 (ratchet variant separation): on one burst window (MU perp, 5m), the
  ratchet_c and ratchet_g cells must show the E2/GPT signature difference
  (re-entry wait distributions); if they do not separate, the P1 port is
  wrong. Fail = STOP.

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

## 10. What this pre-reg does NOT license

- No deployment, promotion, or "keep" verdicts. The output is a ruler.
- No charter amendment to Section 7 (the no-tuning rule stays in force
  everywhere outside this document).
- No BF verdict without naming the ratchet variant.
- No reading of mirror deltas as liquidity-only effects (they are joint
  session-structure + gap + liquidity effects; say so each time).
- Weekend-window cells are OUT of scope (separate pre-reg,
  project-weekend-liquidity-protocol).
