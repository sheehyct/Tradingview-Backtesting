# TVB-19 overnight report -- 2026-08-05 (for the morning read)

Everything below is committed. Nothing tonight touched engine code, Pine
code, flip semantics, or the target ladder (your order); the design
session and Tier B remain fully open. Week-1 frozen artifacts untouched.

**Label on all sweep numbers: DELIBERATE OVERFIT / in-sample ceiling /
secondary control. One ~4-week window, gross, 1x, no fees. No deployment
claims anywhere in this report.**

## What ran tonight (in order, each committed before the next used it)

1. Pre-registration for the Tier A sweep (docs/experiments/
   tvb19_tier_a_prereg.md, commit 2a78ec2) -- grid, window, metrics
   declared BEFORE the runner existed. The F1 lesson, applied.
2. The sweep itself (analysis/paper/sweep_tier_a.py): 864 cells x 11
   symbols over 2026-07-06 -> 2026-08-03, ~4 minutes wall. Results in
   analysis/paper/sweeps/tvb19_tier_a/ (manifest has timestamps + bar
   hashes; the run log is local-only, gitignored).
3. The RTH-vs-UTC clock census (analysis/clock_census.py ->
   analysis/reference/tvb19_clock_census.json).
4. The deep-window TV-bar harvest (scripts/tvb19_harvest.mjs ->
   analysis/reference/tv_deep/), TV launched fresh on CDP, run on the
   TVB18-parity scratch layout only -- your live layouts untouched.

## Finding 1 -- the clock census answers its own question: MATERIAL

On the same bars, the same deployed D/W/M gate disagrees with itself
across the two clocks on **30.8% of all 5m bars** (per symbol 23.6% to
40.6%). This is not a rounding question; the seeded decision rule said
"if often, pre-registered arms become an experiment" -- it is often.

The mechanism is structural, not statistical: from 00:00 UTC to 9:30 ET
(~13.5 hours of every weekday, plus the entire weekend) the venue "day"
and the RTH "day" are literally different periods with different opens.
The day leg alone disagrees on 31-42% of bars for every symbol.
Disagreements cluster exactly where the mechanism says they should: ET
hours 20-22 (right after the 00:00 UTC roll re-anchors the venue day
while the RTH day still points at yesterday 9:30) and 05-07 (pre-market
drift before RTH re-anchors). Your live observation of ~19:00-20:00 ET
character changes sits on this boundary.

Two texture points worth carrying into the design session:

- The clocks do not just shade the gate differently -- they generate
  mostly DIFFERENT flip events: 2,519 composite-state changes under the
  venue clock vs 1,710 under the RTH clock in the window, and only ~220
  of them coincide. Hard up-to-down (or reverse) flips are rare under
  both (6 vs 7); almost all flip traffic is into/out of neutral.
- GOLD shows the monthly version of the mechanism in isolation: July's
  venue-clock monthly open printed 4007.7 at 00:00 UTC July 1; by the
  RTH monthly open that morning the price was 4092.6 (+2.1%). Price
  then spent 65% of the window BETWEEN those two opens, so the monthly
  bias leg disagreed for two-thirds of the month off one overnight gap.

Consequence (not acted on tonight): the anchor clock is now a
demonstrated live variable for the design session, and any future
graded run should state which clock it stands on. Declared census
caveats: NYSE holiday table hardcoded (2026-07-03 in-window), weekend
bars belong to Friday's RTH session, pre-archive RTH opens sampled from
1h bars (up to 30 minutes late -- the GOLD RTH monthly open above
carries that delta; the mechanism conclusion survives it).

## Finding 2 -- the sweep spread is wide and the top of it is one shape

Across all 864 cells: combined (realized + open mark-to-market) runs
from **-13.8pp to +171.3pp**, median +82pp. The spread is the finding;
the ceiling is a ruler, not a target.

The single most important read: **the entire top of the table is the
no-backstop corner** -- cells with the adverse-break exit AND the flip
backstop both OFF, i.e. harvest-touch as the only exit. Those 216 cells
have median +132.4pp [corrected 2026-08-07, audit F1 estimator] vs +82
overall, and the five best cells (+166 to
+171pp) are all that shape, slow-armed (four 1H, one 30m [corrected
2026-08-07, audit F4]), riding ~10 open positions
into the window end. Treat this as a question, per the charter, and the
question has a sharp form: this window PAID you for never realizing a
loss (unrealized holes recovered or ended as open marks), while
absorbing episodes as deep as -39.6% adverse excursion (NBIS) that
simply happened not to die. It is exactly the shape that week 1's
adverse-runner gap punishes on a less kind window. In other words: the
in-sample ceiling and the known failure mode are the same object seen
from two windows. That is the cleanest possible framing for the
open-air-stop question on the design docket, and it was obtained
without writing a line of exit code.

At the deployed defaults themselves (15m arm, all four pools, both
backstops on -- the shipped config): **+47.4pp combined** on the four
weeks, roster drawdown 131.5pp, with -73.5pp of that dragged by open
runners at the window end -- three deep-underwater shorts (SK Hynix
perp -26.6, Marvell perp -22.2, SKHX -25.7) plus DRAM -8.5. Weekly
slices: +44.1 / -6.8 / -4.8 / +88.3 -- two of four weeks carried
everything, and the profitable weeks bracket the flat middle that
contains your live week-1 window. Same book, kinder sample.

Knob-by-knob (marginal medians across the half-grids), in words:

- **Arm timeframe is the lever**: 5m arm +23pp median, 15m +70.6, 30m
  +100.7, 1H +111.9 -- monotone. Slower arming = fewer, later, better
  entries in this window. This is the TVB-1 turnover lever wearing a
  new costume, and four of the worst five cells in the whole grid are
  5m-armed churn with full backstops on (the second-worst is 15m-armed
  with brk on / flip off [corrected 2026-08-07, audit F4]).
- **The backstops cost money in this window**: turning the adverse-break
  exit on costs ~47pp median; the flip backstop on costs ~35pp. That is
  the measured price of insurance in a window where the insured event
  mostly did not finish happening. The design question is not "drop
  them" (that is the overfit read) but "what cheaper insurance buys the
  same tail coverage" -- which is precisely the ladder + flip-redesign
  agenda.
- **The 12h pool helps at the margin** (+32pp median ON vs OFF),
  consistent with the TVB-16 "12h harvests winners" ablation -- BUT at
  the exact deployed point, dropping it gained +9.7pp. Marginals and
  point-contrasts disagree at that point: the knobs interact; nothing
  here is a clean monotone dial.
- **Two shape knobs are near-inert, one is not** [corrected
  2026-08-07, audit F4: "all 2-7pp" was wrong for min_sep]: compound
  width (n_max 3/6/9) moves marginal medians 7.4pp and pool cap
  (6/12/uncapped) 4.5pp; anchor separation is a real axis -- min_sep
  0.5 -> 2.0 moves the median 14.5pp (tighter spacing better IN THIS
  WINDOW). The BF ladder mechanism is knob-tolerant rather than
  knob-inert -- a hypothesis from this one in-sample window, not a
  demonstrated generalization. What moves outcomes most is still WHEN
  you enter (arm) and HOW you are allowed to lose (backstops). Both of
  those are the design session's subjects.

- **Every cell keeps a severe adverse-runner tail** [corrected
  2026-08-07, audit F4: previously "37-40% config-invariant at grid
  scale"]: worst-runner MAE spans 29.8-39.6% across the 864 cells (372
  cells sit below 37%), with the 37-40% depths (NBIS, SKHY) in broad
  regions including the deployed cell. TVB-16 showed the class on two
  configs; tonight bounds it on 864: no existing knob removes the
  roughly 30-40% tail; only exit design can.

Reading rules honored: no cell is promoted; the per-cell artifacts
carry config codes, this report carries words; single window, gross,
1x, no fees; the W3 slice of this window does NOT reproduce the frozen
week-1 record (different warm boundary, carried positions -- declared
in the pre-reg) and week 1 keeps NO official number.

## Finding 3 -- the deep TV harvest reaches venue listing (33/33 datasets)

TradingView was not running when the session started; it was launched
fresh with CDP via the documented Store-app incantation and left
running. All work happened on the TVB18-parity scratch layout; your
live layouts were never touched.

All 11 symbols x {5m, 15m, 60m} harvested and committed
(analysis/reference/tv_deep/, ~19 MB, per-dump provenance inside each
file, inventory in tvb19_harvest_summary.json). What the floors turned
out to be:

- **5m is a ~20.2-21.6k-bar TV-side cap, not a uniform calendar
  floor** [corrected 2026-08-07, audit F3: "2026-05-25 for every
  symbol, boundary identical" was false]: starts are 2026-05-18
  (AMZN/MSFT/AAPL), 2026-05-25 (six symbols), and venue listing for
  the young ones (NBIS 2026-06-09, SKHY 2026-07-09). Still about 4x
  the Hyperliquid API's ~17-day 5m floor for the cap-bound symbols.
  Practical consequence: future pre-registered 5m replay windows can
  start ~May 18-25 for the nine older symbols (NBIS/SKHY are
  listing-bound) -- with the venue-feed mix declared (TV bars vs HL
  bars differ at the wick level; TVB-6: 97-99% float-exact). Every
  committed dump ends on TV's active bar (drop the final row on
  consume) and the run predates fail-closed floor detection -- see
  analysis/reference/tv_deep/README.md caveats.
- **15m reaches venue listing for young symbols** (Marvell perp
  2026-05-04, SK hynix perp 2026-02-19) and a ~20k-bar cap (~7 months,
  back to Jan 1) for the older majors.
- **60m reaches venue listing everywhere** (deepest: GOOGL perp
  2025-11-18).

One trap found and resolved: HL's `xyz:SKHX` is listed on TV as
`HIP3XYZ:SKHYNIXUSDC.P` -- and TV's symbol search does not index
HIP3XYZ at all, so the name was only findable by direct chart load.
Identity is verified, not assumed: 9,183 of 9,187 overlapping 5m
closes are float-exact against the HL SKHX archive, and the TV series
starts on the HL listing date. A side-catch with a real consequence:
the frozen week-1 roster carries SKHX with an HL-inferred mintick of
0.1 (its TV symbol was null at freeze time -- same discovery failure);
TV metadata says the true tick is 0.001. The frozen roster stays
frozen per the adjudication; future rosters should backfill tv_symbol
and re-pull ticks from TV metadata. Tonight's sweep used the frozen
roster tick for SKHX, consistent with the week-1 twin convention (at
SKHX prices ~1216 the trigger-offset difference is under one basis
point per trade).

## Where everything lives

- Pre-reg + results: docs/experiments/tvb19_tier_a_prereg.md,
  analysis/paper/sweeps/tvb19_tier_a/ (manifest.json,
  results_by_symbol.jsonl, results_rollup.jsonl)
- Census: analysis/clock_census.py, analysis/reference/
  tvb19_clock_census.json (per-symbol rates, per-leg attribution,
  hour histograms, flip counts)
- Harvest: scripts/tvb19_harvest.mjs, analysis/reference/tv_deep/
- Tests: tests/test_sweep_tier_a.py, tests/test_clock_census.py
  (suite green: 103 passed, 2 skipped)

## What tonight deliberately did NOT do

No flip-semantics or ladder code; no Tier B; no design decisions; no
week-2 definition; no promotion of any sweep cell; no /session-end
(HANDOFF untouched for you to close out with the design session's
plan). The TVB-18 external review was still unreturned at run time.
