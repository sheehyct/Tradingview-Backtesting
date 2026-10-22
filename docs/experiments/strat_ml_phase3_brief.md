# STRAT Trigger Research: Phase 3 Brief

Oct 21, 2026 · @Christopher Sheehy

## Purpose and how to use this

This brief is the complete instruction set for phase 3 of the STRAT trigger research. It exists so the Claude Code cloud session that runs it needs no context from any chat: everything decided is written here.

**Opening prompt for the Claude Code session** (paste exactly this, nothing else):

```markdown
Read docs/experiments/strat_ml_phase3_brief.md in full before doing anything. It is the spec. Execute it in the order it gives, stop at the gate it names, and follow its reporting rules for every table. Do not re-derive anything it lists as already known.
```

Save this document as `docs/experiments/strat_ml_phase3_brief.md` in the repo (export to Markdown from the doc menu) so the session reads it from disk rather than from a paste.

**The question phase 3 answers.** Phase 1 showed a mechanical daily STRAT book on Binance perps is flat before fees (mean R −0.032, 556,092 triggers). The hit rate of every reversal pattern sits on the fair-game line for its stop and target geometry, so the exits are measuring geometry, not drift. Phase 3 tests one hypothesis: *there is forward drift after a STRAT trigger, and the phase-1 exits threw it away.* If the drift is zero, the alt-coin line of research closes and the work moves to the HIP-3 equity perps.

**Scope guardrails for the session**

- Extend `analysis/strat_ml/report.py`; do not rewrite it. New tests are new sections in a `report_v3.py` that imports the phase-1 event table unchanged.
- Keep the phase-1 trigger definition, stop convention, and target ladder exactly as they are. New exit rules are *added* as variants on the same rows, never substituted.
- Nothing is tuned on 2025–26 data. Every threshold is chosen on 2020–24 or taken from this brief.
- If a test needs data the archive does not hold, write one line saying so and skip it. Never synthesize or proxy.
- Build in stages: fixes, then test 1, then stop and report the gate result before tests 2–5.

## What already exists and what phase 1 established

Phase 1 is done and its numbers are settled. Do not re-run the baseline tables; cite them.

**In the repo**

- `analysis/strat_ml/report.py` — builds the phase-1 event table and report (HTML + MD). Run time \~121 s.
- `docs/experiments/strat_ml_phase2_events_design.md` — definitions of every column in the event table (trigger, stop, target ladder, HTF partial-bar features, excursion clock).
- The data archive: Binance USDT-M perps, 899 coins, hourly and 15-minute bars, 2020-01-03 to 2026-10-06, plus funding-rate series. Hyperliquid HIP-3 equity perps, hourly, 2026-03-29 to 2026-10-09.
- The `strat-methodology` skill (load it; section 12 of this brief inlines the rules that matter here).

**Phase-1 event table, in one line.** One row per daily 2U/2D break. Entry at the broken level. Stop at the far side of the setup bar. T1 = bar-0 wick for reversals, week/month ladder level for continuations and 3-2s (a Pine pivot ladder was added in section 8). Outcome walked hour by hour for 10 daily bars. HTF features use the *partial* week and month as of the trigger hour (no lookahead). Train = triggers before 2025-01-01; test = 2025–26.

**What phase 1 found, with the numbers to cite**

| finding | number | where |
| --- | --- | --- |
| Whole book is flat before fees | mean R −0.032, median +0.056, −0.3% of price per trade, 556,092 rows | §0 |
| Every reversal pattern sits on the fair line 1/(1+R:R) | 2-1-2 rev: R:R 0.40, fair 71.4%, observed 69.4%; 3-2-2: 0.65, fair 60.6%, observed 60.6% | §8a |
| Mean R is flat across every reward-to-risk bucket | <0.5R: 82% hit, +0.01R; >3R: 24% hit, −0.13R | §1l |
| The median trade swings 1.6R both ways in 10 bars | median MFE 1.60R, median MAE 1.58R | §0, §1a |
| Removing the stop flips the sign where shown | alts same window −0.059 → +0.066; HIP-3 24/7 −0.096 → +0.250 | §9, §10a |
| Context can rank trades but only finds losers | model A test deciles −0.245R (decile 1) to +0.046R (decile 10); train R² 0.17, test −0.01 | §3a |
| Regime beats pattern | BTC 30-day realized-vol percentile is top SHAP feature at 0.07; pattern name 0.03 | §3d |
| Full type-and-colour continuity is the worst cell | tfc\_score = 1: 38.3% win, −0.085R; tfc = 0: 57.2% win, −0.021R | §1e |
| Hour of day does nothing to 10-bar outcomes | all hour buckets 53–55% win; SHAP 0.01 | §1f, §3d |
| Sunday triggers are bad | 45.5% win, −0.082R | §1h |
| Wider stop changes how the book loses, not whether | inside breaks: bar-0 stop 61.7% win vs setup-bar 54.3%; return per trade −0.2% of price either way | §6 |
| HIP-3 US-listed perps on the NY session bar is the only positive cell | +0.117R, 55.6% win, 7,246 rows, 76 names, 7 months | §10a |

**Known bugs in phase 1 (fix before anything runs, section 5)**: §3f interaction table crashed on an unencoded categorical; USDCUSDT (a stablecoin perp) is in the universe; section numbering puts §5 after §10.

## Glossary in trader terms

Every term below must be used with this meaning in the report, and the report's own glossary block (top of the page) reproduces these definitions verbatim. The running convention: **size every trade so the stop costs $100.** Then every number in R reads as dollars per $100 risked.

| term | what it means | example |
| --- | --- | --- |
| R | Your risk per trade, in dollars. 1R = what the stop costs. | Stop costs $100, so 1R = $100. |
| +0.5R | The trade is up half your risk. | Up $50 on a $100 risk. "Move stop to breakeven at +0.5R" = once up $50, stop goes to entry so the trade can't lose. |
| −1R | Stopped out. | Lost $100. |
| Mean R | Average result per trade. What the account does over many trades. | Mean R −0.032 = lost $3.20 per $100 risked, on average, before fees. |
| Median R | The middle trade. What a typical trade feels like. | Median +0.056 = typical trade made $5.60. Mean −0.032 at the same time = losers big enough to drag the average under zero. |
| Target at 0.4R | Aiming to make 40% of what you're risking. | Make $40, risk $100. |
| Reward-to-risk (R:R) | Target distance divided by stop distance. | T1 0.4R away, stop 1R away: R:R 0.4. |
| Fair hit rate | The win rate a coin-flip market gives for that stop and target. Nearer target = hit more often, with no edge involved. Formula: 1 ÷ (1 + R:R). | R:R 0.4 → fair = 71%. You need to hit the target more than 71 times in 100 to make money. |
| Excess over fair | Observed target-first % minus fair hit rate. The only hit-rate number that isn't geometry. | Reversals: 69% observed vs 71% fair = −2 points. No edge. |
| Target-first % | Share of trades that touched the target before the stop. Not the same as win %. |  |
| Win % | Share of trades that closed above zero after 10 bars, however they got there. |  |
| MFE / MAE | Best and worst the trade got during the window if you had never exited. | Median MFE 1.6R = half the trades were up at least $160 at some point. Median MAE 1.58R = half were also down at least $158 at some point. Exits at +$40 and −$100 sit inside that swing. |
| Drift | Whether price keeps going the break's way, on average, if you just hold. The only thing any exit rule can harvest. | No drift = no stop or target or trail can help; the trade is a coin flip whatever you do with it. |
| Expectancy | Mean R after fees, funding and slippage. The number that decides whether to trade it. |  |
| Walk-forward / train–test | Rules found on 2020–24, judged on 2025–26 which the rules never saw. | A rule that holds on both is real. One that only holds on 2020–24 was fitted to noise: that is what "overfit" means. |
| Decile | Sort trades by a model's score, cut into 10 equal buckets. | Decile 1 = the model's least-favourite 10%. If decile 1 loses and decile 10 wins, the model can rank. |
| ATR | Average true range: the coin's normal daily swing. Used to compare moves across coins that move at different speeds. | Stop at 0.6 ATR = stop set at 60% of a normal day's range. |
| z vs own noise | Mean R divided by how much that cell's results bounce around. Below 2 = could be luck. | A coin with +0.08R and z 1.8 is at the edge of noise. |

## Reporting rules

The reader is a trader who sizes by dollars at risk, not a quant. Every table in the phase-3 report follows these rules, enforced in code (the table-writing helper takes the explanation text as a required argument and refuses to render without it).

1. **A "What this means" paragraph sits directly above every table**, 2–4 sentences. It says, in plain words: what one row is, what the key column is, and what the reader should look for. It uses the $100-risked convention on first mention of any R value in that section.
2. **A one-line verdict sits directly below every table**, in the form `Verdict: supports / contradicts / inconclusive — <hypothesis this table was built to test>, because <one number>.` Every table in phase 3 exists to test something; the verdict names it.
3. **No quant term without its trader translation** on first use in each section. Fine: "mean R −0.08 (lost $8 per $100 risked)". Not fine: "expectancy −0.08" on its own.
4. **Fees are in every R number** from test 1 onward, with a `fees` column (R per trade) so the reader can see what they cost. Phase-1 numbers cited for comparison are labelled "before fees".
5. **Counts and the 95% band on every win % and hit %**, as phase 1 did. Cells under 300 rows are greyed and not quoted in verdicts.
6. **Train and test side by side** in any table where a rule or threshold was involved, as in phase-1 §4. A finding exists only if it holds on both.
7. **Charts keep the phase-1 style** (inline PNG, 95% bands). Tables keep the phase-1 columns where they overlap so the two reports read alike.
8. **The glossary block from section 3 of this brief is the first thing on the page**, verbatim, after the one-paragraph "how to read this page" note.

**Worked example of rule 1 and 2**, for a hypothetical test-1 table of forward return by family:

> **What this means.** One row = every trigger of that family, held for 5 days with no stop and no target. "Mean ret (ATR)" is the average move in the break's direction, measured in the coin's normal daily range; 0.10 means price was on average a tenth of a normal day further along after 5 days. Fees are already subtracted. Look at whether the number is above zero and whether z is above 2; if both, there is drift to harvest.
>
> *\[table\]*
>
> Verdict: supports — drift exists for reversals, because mean ret +0.14 ATR with z 4.1 after fees; contradicts for continuations, because −0.03 ATR, z −1.2.

**Worked example of rule 3**, translating a phase-1 sentence: "Median MFE 1.60R" becomes "half the trades were up at least 1.6R at some point in the 10 days, which is $160 on a $100 risk."

## Fixes and parameters before any test runs

Three phase-1 bugs get fixed first, then the cost model is added as a column on the event table. Nothing else in the event table changes.

**Fixes**

- [ ] §3f interaction table: encode categoricals (asset class, pattern, direction, bar types) before the SHAP interaction call. Re-render §3f.
- [ ] Drop stablecoin perps from the universe: any symbol whose base is USDC, BUSD, TUSD, FDUSD, USDP, DAI, USDD, or any pair that trades inside ±1% of 1.00 for 90% of its history. Log the dropped list. Phase-1 headline numbers shift slightly; report the new ones alongside the old in one table.
- [ ] Renumber sections so caveats are last and the order on the page is the order in the HTML.

**Cost model** (added as `fees_r`, `funding_r`, `slip_r`, `cost_r` columns on every event row; all in R using that row's actual stop distance in % of price)

| component | Binance USDT-M | HIP-3 (Hyperliquid) | how it enters |
| --- | --- | --- | --- |
| Taker fee, each side | 0.05% | 0.045% | Entry is a stop-market at the break (taker). Target exit is a resting limit (maker, 0.02% / 0.015%). Stop exit is taker. Trail exit (test 2) is taker. |
| Slippage, each side | tier 1: 0.02%; tier 2: 0.03%; tier 3: 0.05% | 0.05% | Liquidity tier from phase 1. On the taker legs only. |
| Funding | actual rate series from the archive, charged per 8h funding mark the trade is open across | actual series | Signed by direction (longs pay positive funding). |
| Parameters | all four as a config block at the top of `report_v3.py`, so a reader can change them |  |  |

**What this means for the phase-1 numbers.** The whole book is −0.3% of price per trade before costs; round-trip taker plus slippage is roughly 0.15–0.20% for a tier-3 alt. Costs are on the order of half the existing loss. Any cell that reads +0.05R before fees is at or under zero after them. That is why no phase-3 verdict is allowed on a before-fees number.

**One check to run and report, not fix.** The phase-1 excursion clock counts the trigger hour's own low against the trade. Using the 15-minute bars, recompute `first_025r_move` (favourable vs adverse first) for a random 20,000-row sample. Report the before/after split in one table. If the adverse-first share drops from 68% toward the 27% the report estimated, say so and note that §7b–7c of phase 1 should be read with the 15m version. Do not rebuild the clock for the whole table in this phase.

## Test 1: raw forward drift, no exits (the gate)

This test decides whether tests 2–5 run on crypto alts at all. It asks the simplest question in the brief: after a STRAT trigger, does price keep going the break's way if you do nothing?

**Hypothesis.** Conditional on a daily 2U/2D trigger, the forward move in the break's direction is positive on average, and phase-1's exits (stop inside the noise, T1 at 0.3–0.5R) resolved on noise before that drift could show.

**Measurement**, one row per phase-1 trigger, no stop, no target:

- Forward return from the entry level to the close at +1, +3, +5, +10 daily bars, signed in the trade direction, in two units: % of price and ATR (the coin's 20-day ATR at the trigger).
- Costs subtracted once (entry taker + exit taker + funding over the hold), so the ATR and % numbers are net.
- Also the +10-bar `mean R no stop` phase 1 already computes for some cells, now for every cell, so the two reports line up.

**Tables** (each with its What-this-means and verdict):

1. By family (continuation, inside, outside, reversal) × horizon (1/3/5/10). The headline table.
2. By pattern × direction, 10-bar horizon.
3. By BTC 30-day realized-vol tercile (low/mid/high, cut on 2020–24) × family, 5-bar horizon.
4. By year × family, 5-bar horizon. Regime drift check.
5. By liquidity tier, 5-bar horizon.
6. Train vs test for tables 1 and 3.

**Chart.** For the whole book and for each family: mean net forward return in ATR against horizon (1/3/5/10), with 95% bands, train and test as two lines. A line rising from zero is drift; a flat line at zero is no drift; a line that rises in train and sits at zero in test is a regime story.

**Statistic.** Mean, median, and z vs own noise, where the noise is the standard error clustered by trigger date (triggers on the same day across 899 coins are one observation of the market, not 899). Without clustering the z will be inflated several-fold and the gate will pass on nothing.

**Gate.** The alt-coin line continues to tests 2–5 only if, on the test period (2025–26), net 5-bar forward return is above zero with clustered z ≥ 2 in at least one family, after fees. If no family clears it: write that table and its verdict, stop, and go to section 11 (HIP-3 branch). Do not run tests 2–5 on alts "anyway".

**What this means for the reader** (write a version of this above table 1): this is what you'd make per $100 risked if you took every break and just held for N days, no stop, no target, fees paid. If it's zero, STRAT triggers on daily alts don't predict direction and no exit rule can fix that. If it's positive, the phase-1 exits were the problem and tests 2–3 go looking for the exit that keeps it.

## Test 2: continuations with the STRAT exit

Half the phase-1 book (2-2, 2-1-2 and 3-1-2 continuations, about 270,000 rows) was traded with an exit STRAT does not use: a far week/month target or none, a setup-bar stop, and a 10-bar hold. The skill says continuations have no structural magnitude and are ridden until a reversal combo prints. This test runs those rows the skill's way and compares.

**Hypothesis.** The worst phase-1 cells (continuation >3R: 24.6% win, −0.13R; no\_rung: 30% win, −0.11R) are artifacts of the bolted-on exit. With the trailing exit, continuation expectancy is materially higher than phase 1 measured.

**Rows.** Every phase-1 row where pattern ∈ {2-2 continuation, 2-1-2 continuation, 3-1-2 continuation}. Same entry, same initial stop (setup-bar far side; keep it so R is comparable to phase 1).

**Exit rule A: pivot trail (the skill's STRAT-level trailing).**

1. Initial stop = setup-bar far side, as phase 1.
2. Each time a daily bar *closes* as 2U (long) / 2D (short), move the stop to that bar's low (long) / high (short), never backward.
3. Inside bars (Type 1) do not move the stop. Outside bars (Type 3) that close in the trade's colour move it; in the opposite colour, exit at that bar's close.
4. Exit at market when price trades through the current stop, walked hour by hour as phase 1 did.
5. No target. Hold cap 30 daily bars; if still open, mark at the bar-30 close and flag the row as `capped`.

**Exit rule B: breakeven at +0.5R, then rule A.** Same as A, plus: once the trade shows +0.5R intrabar, stop moves to entry if entry is above the current trail (long) / below (short). This is the ATLAS-CONFIG default from the skill.

**Exit rule C: invalidation before the stop** (applies to all rows, run here and reused in test 3). Walking hour by hour, if the entry bar's running classification reaches Type 3 (it took out the setup bar's other side), exit at that hour's close, ahead of any stop or target check. Report how many rows this fires on and what it costs or saves versus phase 1. For inside breaks the level coincides with the setup-bar stop, so the difference should be near zero; for 2-2 continuations it will differ.

**Tables** (What-this-means and verdict on each):

1. Phase-1 exit vs rule A vs rule B, same rows: n, win %, mean R, median R, mean % of price, mean hold (bars), share capped, fees R. By pattern and overall. The headline.
2. Same, train vs test.
3. Same, by BTC-vol tercile.
4. Rule C alone: rows fired, mean R with vs without, by family.
5. Distribution of exit R under rule A, as a histogram in the phase-1 style, overlaid on the phase-1 histogram for the same rows.

**What a pass looks like.** Rule A or B has mean R after fees above zero on both train and test for at least one continuation pattern with n ≥ 2,000 per period. A pass here is the strongest possible evidence for the brief's hypothesis, because it is the same entries with only the exit changed.

**What a fail looks like.** Rule A and B land at or under phase 1 after fees. Then the continuation exit is not where the money was, and the trail just converts many small stop-outs into fewer larger ones, the way the wider stop did in phase-1 §6.

**Do not** add a target to rules A or B, tune the hold cap, or try a 3-bar trail: one exit per rule, as specified.

## Test 3: the fair-line sweep

This is the "overfit on purpose" run, built so geometry cannot win it. Phase 1 showed that hit rate, speed and drawdown are all set by how close the target is and how tight the stop is; a naive search for "highest hit rate, fastest, least drawdown" returns the smallest-target cell and it has zero expectancy. The sweep therefore scores every cell by its distance above the fair line, and by net expectancy, never by raw hit rate.

**Hypothesis.** Somewhere in pattern × timeframe × continuity × regime there is a cell whose target-first rate sits above the fair line on both train and test and whose expectancy clears costs.

**Cells.** The cross of:

- pattern: the 10 phase-1 patterns
- direction: long, short
- timeframe of the trigger: daily (phase-1 table), 4-hour (new; build from the hourly archive with the same event logic, HTF partials = daily and weekly as of the trigger hour), 1-hour only if 4H is finished and time allows
- continuity: the gated score from test 4 (`tfc_gated` ∈ {0, 0.5, 1}); until test 4 runs, use the phase-1 `tfc_score`
- regime: BTC 30-day realized-vol tercile, cut on 2020–24

That is up to 10 × 2 × 2 × 3 × 3 = 360 cells per timeframe. With this many cells, roughly 18 will look good at p < 0.05 by chance alone; the walk-forward rule below is what deals with that, and the report says so in the What-this-means.

**Per cell, compute** (phase-1 exits for reversals; rule A from test 2 for continuations, since the fair line does not apply to a trailed exit — those cells report expectancy only):

- n (train, test separately)
- median R:R, fair hit rate 1/(1+R:R), observed target-first %, excess = observed − fair, with 95% band on the observed
- mean R after costs, z clustered by trigger date
- median hours to T1, median MAE

Cap R:R at 2.0 for the fair-line columns: a 4R target rarely resolves inside the 10-bar window, so far-target cells sit under the line for a censoring reason, not an edge reason. Rows with R:R > 2 stay in the expectancy columns.

**Survival rule.** A cell survives if all of: excess > 0 on train AND on test; mean R after costs > 0 on train AND on test; n ≥ 300 in each period; clustered z ≥ 2 on test. List survivors in one table sorted by test mean R. If none survive, the table says so.

**Charts.**

1. The fair-line scatter: x = fair hit rate, y = observed target-first %, one dot per cell, dot size = n, colour = family, test period only. The diagonal is drawn. Dots above it are edge; on or below are geometry. A second panel shows the same cells on train, so the reader can see whether the above-the-line dots are the same ones.
2. Train vs test scatter of mean R after costs: x = train, y = test, one dot per cell. Dots on the diagonal are real; a horizontal cloud at y = 0 is noise that fit the past.

**What this means for the reader** (above the survivor table): each row is one specific trade: this pattern, this timeframe, this continuity, this BTC regime, this direction. "Excess" is how many more times in 100 the target was hit than a coin-flip market would give for that stop and target; that is the only hit-rate column that is not geometry. A cell is listed only if it worked on 2020–24 and again on 2025–26, which it never saw. The scatter shows the whole field at once: the diagonal is "no edge", and the question is whether anything sits above it twice.

**Do not** add features, change the cut points, or re-slice after seeing test results. One pass.

## Test 4: continuity gated on structure beyond

Phase 1 found that full continuity (week and month both Type 2 in the trade's direction and coloured the same way, `tfc_score` = 1) is the worst cell in every family, which contradicts the skill's Tier A rule (score ≥ 0.67 = take it). The skill also says, in its targets section, that clearing one timeframe's level with no larger level beyond is exhaustion risk. The two rules pull against each other and phase 1 says exhaustion wins. This test splits them.

**Hypothesis.** `tfc_score` = 1 is bad because, by construction, both higher-timeframe levels are already broken and nothing structural sits beyond the entry. Among tfc = 1 triggers that *do* still have a higher-timeframe level beyond entry, results are as good as or better than tfc = 0.

**Definition.** `structure_beyond` = true when at least one of the following sits beyond the entry in the trade direction and has not been taken out as of the trigger hour: prior week's high/low, prior month's high/low, or the nearest Pine pivot-ladder rung from phase-1 §8. Compute `tfc_gated` = `tfc_score` if `structure_beyond` else 0, and keep `structure_beyond` as its own column.

**Tables**

1. `tfc_score` × `structure_beyond` × family: n, win %, mean R after costs, median R:R. The headline. Six cells per family.
2. The same with `bias_score` (colour only) in place of `tfc_score`, since phase 1 found colour alone goes the expected way.
3. Train vs test for table 1.
4. Rev Strat tiers from the skill (A: aligned ≥ 0.67; B: the Rev Strat is itself on the higher timeframe; C: against the majority) applied to the 1-2-2 and 3-1-2 reversal rows only, with and without the gate.

**What this means for the reader** (above table 1): "continuity" in phase 1 meant the week and month had already broken in your direction. That sounds like confirmation, but it also means the obvious targets above you are already gone. This table separates the two: same continuity score, split by whether there is still a level to aim at. If the tfc = 1 rows with a level beyond do fine and the ones without a level do badly, the skill's Tier A rule needs a second condition, not a different threshold.

**Pass.** tfc = 1 with structure beyond beats tfc = 1 without it by more than the 95% band on both train and test. **Fail.** The split does not separate them; then exhaustion is not the explanation and the tfc = 1 result stands unexplained.

## Test 5: time exhaustion as the skill states it

The skill says a signal that triggers with little time left in its bar rarely reaches its timeframe target, and scores signal quality as time remaining ÷ bar length. Phase 1 found the hour of the day does nothing to 10-bar outcomes (all buckets 53–55% win). But the skill's claim is about reaching the target *before the bar closes*, and phase 1 never measured that. The hourly walk already has what is needed.

**Hypothesis (the skill's).** P(T1 touched before the daily bar closes) falls as hours remaining at the trigger falls.

**Measurement**, per phase-1 row with a target: `hours_remaining` = 24 − `hours_since_daily_open`; `t1_within_bar` = T1 touched at or before the daily close of the trigger bar; `t1_within_10` = phase-1 target-first flag.

**Tables**

1. `hours_remaining` bucket (0–3, 3–6, 6–12, 12–18, 18–24) × family: n, P(t1\_within\_bar), P(t1\_within\_10), mean R after costs. Reversals and continuations separately, since only reversals have a structural T1.
2. The same restricted to R:R ≤ 1, so the within-bar rate is not just a far-target effect.
3. Train vs test for table 1.

**Chart.** P(t1\_within\_bar) against hours remaining, one line per family, 95% bands.

**What this means for the reader** (above table 1): a break that happens at 22:00 UTC has two hours of its daily bar left; one at 02:00 has twenty-two. The skill says the late one rarely gets to its target the same day. This table checks that directly, then checks whether it matters at all over 10 days (phase 1 says it does not). If the first column slopes and the second is flat, the skill's rule is about timing, not quality, and it should not be used as a filter.

**Pass.** Within-bar rate rises monotonically with hours remaining on both periods. **Fail.** Flat. Either way, record the result against the skill's claim in the verdict line.

## HIP-3 session branch

The HIP-3 US-listed perps on the New York session bar were the only positive cell in phase 1 (+0.117R, 7,246 rows, 76 names, 2026-03-29 to 2026-10-09). This branch runs either after tests 2–5 on alts or instead of them if test 1 fails the gate.

**What phase 1 got right and wrong here.** The 24/7 UTC-day build was measuring a daily bar that rolls at 20:00 New York while the underlying is closed; that is where most of the damage sat, so the session build is the defensible bar definition, not a cherry-pick. But the control phase 1 used (crypto alts in the same months) answers "was crypto trending" and not "is this a perp artifact". The right control is the underlying stock.

**Hypothesis.** The session-bar result is a property of the equity market in those months, not of the perp. If so, the same rules on the underlying's session bars give a similar number.

**Runs**

1. Test 1 (raw drift) on the HIP-3 session build, clustered by trigger date. The 76 names move together; without clustering, z is meaningless here.
2. The same test 1 on the *underlying* stocks' regular-session bars, same dates, same tickers, same rules. Needs an equity daily/hourly feed for the 76 names; if none is wired into the environment, write one line saying so and skip this run.
3. Leave-one-ticker-out on the session build: drop each name, recompute mean R; report the spread. If one or two names carry the result, say which.
4. The skill's gap rule, which phase 1 may not have applied: an open beyond the trigger level invalidates the entry. Count how many session-build rows are gap entries and report the result with and without them.
5. Test 3 (fair-line sweep) on the session build, daily and 1-hour (RTH-aligned, 09:30 start, per the skill's hourly-alignment note), with the same survival rule. Expect few survivors at n ≥ 300 in a 7-month sample; say so.

**Tables and chart** follow the test-1 and test-3 formats. One extra table: perp vs underlying vs crypto-alt control, side by side, 5-bar net forward return.

**What this means for the reader** (above the side-by-side): the perp result is only interesting if the stock does not show the same thing. If both show it, you are measuring the equity market in spring and summer 2026 through two instruments. If only the perp shows it, something about the perp (funding, a thin overnight book, basis) is doing it, and that can go away as fast as it came.

**Verdict rule.** "Lead confirmed" only if the session build clears the test-1 gate with clustered z ≥ 2, survives leave-one-out, and the underlying control is either unavailable or tells the same story. Otherwise "lead, not finding" stands.

## STRAT rules that govern this run

The `strat-methodology` skill is the authority; load it. The rules below are the ones phase 3 depends on, inlined so the session does not have to find them, in the skill's own terms.

**Bar classification** (strict breaks, equality never breaks): Type 1 = H ≤ pH and L ≥ pL; 2U = H > pH and L ≥ pL; 2D = L < pL and H ≤ pH; 3 = both. Classify live, intrabar, monotonic 1 → 2 → 3. Setup bars must be closed; the entry bar is classified live.

**Continuation exit** (critical invariant 5): continuations have no hard structural magnitude. Their exit is a reversal combo firing on the trading timeframe, implemented as the STRAT-level trail: most recent 2U low for longs, 2D high for shorts. Inside bars are a pause, stay in. This is test 2, rule A.

**Exit priority** (skill §5.4): 1 target hit; 2 pattern invalidated (entry bar went Type 3) → exit at market now; 3 stop hit. Backtests must evaluate invalidation before the stop. This is test 2, rule C.

**Structural stop** (skill §5.2, default): anchor or first directional bar's opposite extreme. For X-1-2, bar 0, not the inside bar. Phase 1 used the setup bar; phase 3 keeps that for comparability and does not re-open the question (phase-1 §6 already measured the difference).

**Break-even** (ATLAS-CONFIG, not STRAT-native, label it so): move stop to entry at +0.5R with a 1-tick buffer. Test 2, rule B.

**Timeframe continuity** (skill §4.3): tfc\_score = aligned higher timeframes ÷ total higher timeframes at signal time; Tier A ≥ 0.67; bar type primary, colour secondary; Type 1 counts as not aligned. **Exhaustion risk** (skill §5.1): clearing one timeframe's magnitude without a larger-timeframe magnitude beyond = exhaustion risk; defend or exit. Test 4 is built on the gap between these two.

**Time exhaustion** (skill §4.5): a signal triggering with little time left in its bar rarely reaches its timeframe target; quality ≈ time remaining ÷ bar duration. Test 5.

**Gaps** (skill §5.3): an open beyond the trigger invalidates the setup for new entries. Relevant only to the HIP-3 session build.

**Hourly alignment for equities** (skill §8): clock-aligned hours are wrong; resample from 1-minute with a 30-minute offset so bars start 09:30, and filter to RTH. HIP-3 branch, run 5.

**Three predicates, never merged** (ruling R1): bias (price vs the timeframe's own open), live scenario (1/2U/2D/3), signal in force (beyond the level and the bar still open). Phase 1's `bias_score` is the first, its `tfc_score` combines the first two. Keep the names.

## Order of operations and deliverable

Run in this order and stop where it says stop. Each numbered step ends with the report re-rendered so progress is visible if the session is interrupted.

1. Load the `strat-methodology` skill. Read `docs/experiments/strat_ml_phase2_events_design.md` and `analysis/strat_ml/report.py`. Do not modify either.
2. Create `analysis/strat_ml/report_v3.py` importing the phase-1 event builder. Add the glossary block and the table helper that requires a What-this-means argument and emits a verdict line (section 4).
3. Section 5 fixes: §3f encoding, stablecoin drop, renumbering. Add the cost columns. Render a short "phase 1, corrected" table: old vs new headline numbers.
4. Section 5 check: the 15-minute trigger-hour recomputation on a 20,000-row sample. One table.
5. **Test 1.** Render. Apply the gate. Write the gate result as the first line under the report title, in the form `Gate: PASSED for <families> / FAILED` with the numbers.
6. **If the gate failed:** skip to step 10.
7. **Test 2** (rules A, B, C). Render.
8. **Test 4** before **Test 3**, because test 3's continuity axis uses test 4's gated score. Render each.
9. **Test 5.** Render.
10. **HIP-3 branch** (section 11), runs 1–5. Render.
11. Write the one-page summary at the top of the report, under the gate line: each test's verdict line copied verbatim, then two sentences on what the next phase should be.
12. Commit `report_v3.py`, the rendered `STRAT Trigger Research v3.html` and `.md`, and `docs/experiments/strat_ml_phase3_results.md` holding the summary from step 11. Leave phase-1 outputs untouched.

**Deliverable checklist**

- [ ] Glossary block is the first thing on the page, verbatim from section 3
- [ ] Every table has a What-this-means paragraph above and a verdict line below
- [ ] Every R number after step 3 is after costs, with a fees column
- [ ] Every statistical claim uses z clustered by trigger date
- [ ] Train and test shown side by side wherever a rule or cut point was involved
- [ ] Gate line at the top of the report
- [ ] No threshold, cut point or feature was chosen on 2025–26 data
- [ ] Anything skipped for missing data is named in one line where it would have been
- [ ] Phase-1 report and code untouched

**If the session runs out of time**, the order above is the priority order. Test 1 with the gate line is worth more than everything after it together.

---

## Appendix: environment bootstrap for the cloud session (added 2026-10-22 by the phase-1 session, not part of the owner's spec)

The brief assumes the data is on disk. In a cloud session it is not: the parquet cache is per
container and dies with it (gitignored `analysis/strat_ml/data/`). Run these first, in this
order, before step 1 of "Order of operations". Total about 2.7 hours wall clock; every command
is re-runnable and skips what is already cached.

```
uv sync                                                               # pyarrow, lightgbm, shap, scikit-learn, httpx are in pyproject
uv run python -m analysis.strat_ml.binance_vision universe            # ~4 min: the archive listing -> data/universe.parquet
uv run python -m analysis.strat_ml.binance_vision fetch --universe --workers 8   # ~2.5 h: 1h klines + funding, 900 USDT perps
uv run python -m analysis.strat_ml.hl_fetch                           # ~2 min: the 115 HIP-3 perps' hourly bars (the venue's ~208-day window ROLLS: dates will differ from the brief's)
uv run python -m analysis.strat_ml.events build --workers 4           # 77 s: the phase-1 event table (events.py builds it; report.py only reads it)
uv run python -m analysis.strat_ml.events build --workers 4 --stop-mode bar0
uv run python -m analysis.strat_ml.events build --roster analysis/strat_ml/xyz_summary.json --roster-tag xyz --workers 4
uv run python -m analysis.strat_ml.events build --roster analysis/strat_ml/xyz_summary.json --roster-tag xyz --session rth --workers 4
```

Corrections to "What already exists" the session should know rather than re-derive:

- The event table is built by `analysis/strat_ml/events.py` (`events build`), not by `report.py`;
  `report.py` reads `analysis/strat_ml/data/events.parquet`. Run time: build 77 s, report 72 s.
- **15-minute bars are NOT in the archive cache.** Only 1h klines, funding and a one-week metrics
  smoke test were pulled. Binance Vision serves 15m klines in the same file layout (one zip per
  symbol-month, 4x the rows); `binance_vision.py` has no interval flag yet (it is hard-wired to
  1h in `fetch --interval`, which exists, but `fetch_symbol` writes into the same klines folder,
  so a 15m pull needs its own dataset folder first). For the section-5 20,000-row check, pull 15m
  only for the symbol-months the sample touches, or restrict the sample to a subset of coins; a
  full 15m pull is another ~2.5 h.
- The universe is 900 USDT perp folders (899 after the stablecoin drop the brief orders; USDCUSDT
  is the one with 500+ rows). The brief's 556,092 rows = the rows with a full 10-bar outcome after
  the Codex gap-censoring fix (565,687 built, 9,595 censored).
- The §3f crash is real: the SHAP interaction call fails with "could not convert string to float:
  'alt'" and the report prints an n/a row. Fix in `report_v3.py` as the brief says; `report.py`
  stays untouched.
- Equity perps: `hl_fetch.py` classifies the 115 names by hand (`US_LISTED`, `NON_US_LISTED`,
  `COMMODITY_FX`; 11 unknown). No underlying-stock feed is wired into this environment; the
  brief's HIP-3 run 2 will be the "one line saying so and skip" case unless one is added.
- The repo's cloud hooks run the test suite on Stop; keep `uv run pytest tests/ -q` green.
- Everything phase 1 wrote is on branch `ccr-84c65430-bqc01u` (PR #3). A new cloud session clones
  `main`; merge the PR first or the session will not see `analysis/strat_ml/` at all.
