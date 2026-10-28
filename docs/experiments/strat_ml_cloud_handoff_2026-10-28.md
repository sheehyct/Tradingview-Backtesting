# Cloud-to-local handoff: the STRAT ML vessel after two cloud sessions

Written 2026-10-28 for the next Claude Code session on the owner's PC. The cloud credits are
spent; everything below moves local. Read this file first, then the top HANDOFF entry's
`### Open` list, then `docs/experiments/strat_ml_phase3_brief.md`. Do not re-derive anything
cited here: open the file it points at. The cloud sessions could not reach OpenMemory, so
nothing from them is in memory yet (checklist item 7).

The two cloud sessions: (1) 2026-10-17 to 10-20, phases 1-2 and the follow-ups (data layer,
the 565k-row daily trigger table, the phase-1 report, stop head-to-head, excursion clock, pivot
ladder, ticker census, equity perps two ways), branch merged as PRs #3 and #4; (2) 2026-10-22 to
10-28, phase 3 to the test-1 gate plus the close-out work, branch `claude/jolly-babbage-vlk7yz`,
seven commits, NOT merged at the time of writing.

## 0. First-session checklist, in order, before any new work

1. Bring the branch in: merge the PR if the owner opened one, else
   `git fetch origin && git checkout claude/jolly-babbage-vlk7yz`. `git log --oneline -8` must
   show `2faa2ad` (close-out) at the top of the branch's commits.
2. `uv sync`, then `uv run pytest tests/ -q`: 414 passed, 2 skipped is the expected line
   (11 of those are `tests/test_strat_ml_report_v3.py`).
3. Rebuild the data cache (gitignored, never on the PC before; about 3 hours unattended), the
   brief's appendix verbatim:
   ```
   uv run python -m analysis.strat_ml.binance_vision universe
   uv run python -m analysis.strat_ml.binance_vision fetch --universe --workers 8 --until 2026-10-16
   uv run python -m analysis.strat_ml.hl_fetch --from-snapshot analysis/strat_ml/snapshots/xyz_2026-10-20
   uv run python -m analysis.strat_ml.events build --workers 4
   uv run python -m analysis.strat_ml.events build --workers 4 --stop-mode bar0
   uv run python -m analysis.strat_ml.events build --roster analysis/strat_ml/xyz_summary.json --roster-tag xyz --workers 4
   uv run python -m analysis.strat_ml.events build --roster analysis/strat_ml/xyz_summary.json --roster-tag xyz --session rth --workers 4
   ```
   From the workstation the CDN host `data.binance.vision` works; the cloud used the S3 bucket
   fallback (the fetcher tries both). Check: `events_summary.json` rows 565,687, censored 9,595
   (= 556,092 with a 10-bar outcome); the xyz builds 15,844 and 11,324 rows. If the numbers
   differ, stop: the pin (`--until 2026-10-16`, the frozen HIP-3 snapshot) was meant to make
   them identical, and a difference is a finding before it is anything else.
4. Reproduce the gate: `uv run python -m analysis.strat_ml.report_v3 --skip-15m` (about 3 min).
   The first line under the title must read `Gate: FAILED` with continuation -0.085 ATR,
   z -2.3, n 118,267 on the test period. With `--m15-rows 20000` (pulls 15-minute bars for the
   sampled months, about 4 min) the 15-minute table must read 67.8% / 55.7% / 47.5%
   against-first. Outputs land in `analysis/strat_ml/reports/` under the names already
   committed; a re-render changes only the build stamp.
5. The phone review page, if the owner wants it local: `uv run python -m
   analysis.strat_ml.phone_review.build_pack --out analysis/strat_ml/phone_review/data`, then
   serve the folder (`python -m http.server 8788` inside `analysis/strat_ml/phone_review/`, open
   `http://127.0.0.1:8788/page.html`). The page fetches `data/index.json` relatively, so it
   needs a server, not file://. It loads lightweight-charts 4.2.0 from unpkg with a jsdelivr
   fallback. The published private page (the owner has the link; links never go in the repo)
   is refreshed by publishing `page.html` with the six data files from a cloud session.
6. Open `analysis/strat_ml/reports/STRAT Trigger Research v3.md` and read the gate line, the
   summary and section 3f. That is the whole phase-3 result in one screen.
7. Store a summary of this file in OpenMemory (tags: strat_ml, phase-3, cloud-handoff).
8. STOP. Put the section 5 questions to the owner before building anything.

## 1. Situation

Phase 1 said a mechanical daily STRAT break book on Binance alts is flat before fees. The
owner's phase-3 brief asked one question: is there forward drift after a trigger that the
phase-1 exits threw away? The brief's order: fix three phase-1 bugs, add a cost model, re-read
the trigger hour on 15-minute bars, run test 1 (hold N days with no stop and no target, costs
paid), apply the gate, and stop there before tests 2-5. That was done. The gate FAILED: on
2025-26 no family shows positive net drift, continuations are significantly against the break
(-0.085 of a daily range at 5 days, z -2.3 clustered by trigger date), reversals are flat.
After the gate, at the owner's prompting, exploratory cuts showed every higher-timeframe context
effect flips sign between 2020-24 and 2025-26, and a phone review page was built so the owner
can judge trades blind with the week and month drawn as they stood at the trigger hour.

## 2. Done, with where it lives

- `analysis/strat_ml/report_v3.py`: extends `report.py` (untouched). Cost-model config block
  at the top. `Doc.table` refuses to render without a What-this-means paragraph and a
  `Verdict:` line. `clustered_mean` is the z. `add_costs` and `funding_sums` are the cost
  model. `drift_cell` / `drift_table` / `drift_train_test` / `gate_result` are test 1.
  `interactions_fixed` is the 3f repair. `stablecoin_table` logs the drop
  (`analysis/strat_ml/stablecoins_dropped.json`: only USDCUSDT).
- `analysis/strat_ml/m15_check.py`: the 15-minute re-read, own raw folder
  (`data/raw15m/`), block-random sample, `first_excursion` is the walk.
- `tests/test_strat_ml_report_v3.py`: 11 hand vectors (glossary verbatim against the brief,
  clustered z, cost arithmetic and funding marks, the 15-minute walk, the gate rule).
- Rendered: `analysis/strat_ml/reports/STRAT Trigger Research v3.html` and `.md`,
  `report_v3_numbers.json`, `v3_charts/`; `docs/experiments/strat_ml_phase3_results.md` (the
  gate line and every verdict verbatim; written by the script).
- `analysis/strat_ml/reports/v3_visual_review_list.md` / `.csv`: six coins on 20 anchor days.
- `analysis/strat_ml/phone_review/`: `page.html` (the published page's source) and
  `build_pack.py`.
- `.claude/skills/adhd/SKILL.md`: the owner's mid-session recap skill, verbatim.
- HANDOFF top entry (dated 2026-10-22, addendum to 10-27) and `RESEARCH_LOG.md` lines.

## 3. Right now

Branch pushed, tree clean, nothing mid-edit, no failing test. Tests 2-5 of the brief were not
run (the brief forbids running them on alts after a failed gate). The HIP-3 session branch
(brief section 11) is next in the brief and waits on the owner's word. The owner's stated
direction at close: move the research off alts to a multi-regime instrument class (index
futures or their ETFs, session bars, 15-plus years), with the continuity arms declared as an
ablation ladder before any run; and a $100 live data run on Hyperliquid.

## 4. Decisions made WITHOUT the owner's explicit sign-off (question each)

Report and statistics:
- Page order: title, gate line, summary, how-to-read, glossary (the brief puts gate and glossary
  both "first"). The "renumbering" fix was applied to the new page only; the phase-1 page was
  not regenerated.
- The gate is judged in ATR units; the brief names no unit. The R unit and the ATR unit
  disagree in sign at 10 bars (+0.05R against -0.03 ATR); the page says the R column is the
  distorted one (one-sided clip at -5R/+10R copied from phase 1; tiny setup bars).
- Percent and ATR units winsorized at the 2020-24 0.5/99.5 percentiles.
- Clustered standard error: residuals summed per trigger day, no small-sample correction;
  overlap between consecutive days (a 10-day hold spans ten trigger days) is not corrected.
- Verdict thresholds: supports = mean > 0 and z >= 2; contradicts = mean <= 0 and z <= -2;
  cells under 300 rows never quoted; "material" stablecoin shift = 0.005R; the brief's "about
  half" claim accepted between 30% and 80%.
Cost model:
- Slippage charged on BOTH legs of the hold-N-days exit (the brief's test-1 sentence names only
  fees and funding; its cost-model table says slippage on taker legs, which both are).
- Timeout exits priced as taker; rows with no liquidity tier pay tier-3 slippage; funding on
  the entry notional at marks in (trigger hour open, exit hour open]; the HIP-3 snapshot has no
  funding series (charged 0, flagged).
Section 5 fixes:
- 3f: model A was REFIT on integer-coded categoricals as plain numbers, not merely encoded
  before the SHAP call, because SHAP's interaction walker cannot handle LightGBM categorical
  splits. The published pair ranking is from that refit.
15-minute check:
- A two-stage block sample (random coin-months until 20,000 rows, then 20,000 rows at random
  from them) instead of a simple random sample, to keep the pull small. Trigger bar = the first
  15-minute bar in the trigger hour that trades strictly through the level; a tie inside one
  bar reads as against (phase 1's rule); a second variant ignores the trigger bar's own adverse
  print.
Process:
- A second parallel fetcher and a waiter script that sent SIGTERM to the fetchers once every
  roster symbol was cached (only when a fetcher's last log line showed it between symbols).
- `m15_check.py` is a separate module (the brief said new tests are sections of report_v3.py).
- Output file names with spaces, exactly as the brief wrote them.
- Two commits (9155973, f354eff) carry an AI attribution trailer against the spine's rule; later
  commits omit it; history was not rewritten.
- ARM_LEDGER not updated (earlier side-thread sessions did not either).
- The phone page uses lightweight-charts, not the owner's preferred amCharts (format test);
  before 2024-10-01 its "as of the trigger hour" bars are built from completed days only.
- `v3_visual_review_list.csv` was force-added past the repo's `*.csv` ignore rule (117 rows).

## 5. Questions to put to the owner before continuing

1. Alt line: closed, or re-opened for tests 2-5 despite the gate? (The brief says closed.)
2. HIP-3 session branch (brief section 11): run it, and at daily resolution for the underlying
   control via the market-data server? If yes, freeze the 76 names' daily bars as a snapshot
   first; the server's 200-bar window rolls past the HIP-3 start in late December.
3. The next instrument set: SPY and QQQ hourly from Alpaca on the workstation, or ES/NQ from a
   vendor? Session bars? How many years?
4. The continuity ablation ladder, in trader terms, confirmed before the prereg: control (every
   daily break); "week or month inside but coloured our way" kept AND skipped as separate arms
   (its sign flipped between regimes); "week and month both 2 our way"; the domino break traded
   on the WEEK's geometry (week stop, week target), not the day's.
5. The $100 Hyperliquid data run: which book (the lead's ranking is in the session transcript
   and summarised in HANDOFF); equity perps on the New York session bar or the UTC day (the data
   says session: +0.12R against -0.10R); risk per ticket (the lead suggested about $5, two
   seats, leverage set so the stop clears liquidation).
6. The phone page: keep lightweight-charts or port to amCharts; keep the source in the repo or
   move it out; and the owner's blind calls, pasted back, to be scored.
7. XAUUSDT / XAGUSDT (Binance gold and silver perps) sit in the "alt" universe. Drop them like
   the stablecoin, or keep?
8. HANDOFF.md is 1,910 lines, past the archive threshold. Archive TVB-36..38 to
   `docs/session_archive/`?

## 6. Review brief: what the local session should verify or challenge on its own

- Reproduce the gate numbers (checklist item 4) before trusting anything else here.
- Read `add_costs` against the brief's cost table and decide whether slippage on the test-1
  exit leg was intended.
- Check `clustered_mean` by hand on one day with many coins; consider whether a cluster-robust
  correction for the 10-day overlap would change the z on the 10-bar horizon (it will not
  change the 5-bar gate's sign; the continuation z is -2.3 at 5 bars).
- Check `first_excursion` in `m15_check.py` against the phase-1 hourly convention in
  `events.py` (the trigger hour's own low counts) and decide whether the 15-minute "counted"
  variant is the faithful comparison.
- Confirm `interactions_fixed` is an acceptable reading of the brief's "encode categoricals
  before the SHAP interaction call", or re-render 3f another way.
- The phone page's partial-bar logic (`seriesFor` in `page.html`) is only tested by a mocked
  run; the context pane's last candle for a trade at 01:00 UTC on a Monday is the empty case.
- Nothing in phase 3 touched `events.py`, `report.py` or the phase-1 outputs; `git diff
  f356f0e..2faa2ad --stat` should show that.

## 7. Parking lot (not current scope)

Rebuilding the whole excursion clock on 15-minute bars; the underlying-stock control for HIP-3
at hourly resolution (no feed); a symmetric R clip; tests 2-5 on alts; the HIP-3 funding series;
the 15-minute sample's block design; the two commits with attribution trailers; TradesViz or a
journal app as a review surface (feasible via a CSV export of the row table, judged marginal);
a neutral trade-row contract so every run exports rows the TVB-40 viewer and the phone page can
draw (the owner asked to test the phone format first; it was tested; the contract is next if
the format sticks).

## 8. Rules as implemented, in plain words

A long row exists on a day when some hourly bar's high goes strictly above the previous day's
high; entry is that previous high; a short mirrors it on the low (phase-1 `events.py`,
unchanged). Test 1 holds from that hour to the close of the last hour of day D+N and sells
there. Costs: 0.05% in and out, slippage in and out by liquidity tier, and the coin's actual
funding rate at every mark whose time is after the entry hour's open and at or before the exit
hour's open, longs paying positive rates and shorts receiving them. The move is measured in
percent of price, in the coin's 14-day ATR, and in multiples of the stop distance. The noise
sums each day's residuals across coins before squaring, so 899 coins on one day are one draw.
The gate passes only if a family's 2025-26 mean in ATR units is above zero with z of 2 or more
and 300-plus rows. The phone page's context pane builds the week or month bar from hourly bars
in [bucket start, trigger hour open), exactly the table's partial-bar rule.

## 9. Numbers to cite, not re-derive

| what | number |
|---|---|
| corrected table | 554,939 rows, 898 coins, USDCUSDT dropped (1,153 rows, -0.233R) |
| phase-1 headline, as published / corrected / after costs | mean R -0.0315 / -0.0311 / -0.0541; % of price -0.331 / -0.331 / -0.506 |
| cost per trade | 0.176% of price, 53% of the loss; 0.02-0.04R by tier |
| 15-minute check, against-first | 67.8% hourly, 55.7% 15m counted, 47.5% 15m ignoring the trigger bar |
| gate, test period, 5-bar net ATR (z) | continuation -0.085 (-2.3); inside -0.046 (-1.8); outside -0.035 (-1.0); reversal +0.010 (+0.3) |
| context flips, 10-bar net ATR, train -> test | inside-but-our-colour +0.13 -> -0.11; full continuity +0.19 -> -0.14; week-only domino -0.04 -> -0.25 |
| HIP-3 (phase 1, before fees) | UTC day -0.096R; NY session bar +0.117R, 7,246 rows |
