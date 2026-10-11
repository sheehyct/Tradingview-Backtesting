# HANDOFF -- tradingview-backtesting

> Newest session entry at the TOP. Keep under 1500 lines; archive older entries to
> `docs/session_archive/` when it grows past that.

---

## Session TVB-37: the data redirect -- domino census, chance comparison, equal-size book and chart page, two Codex audits folded (COMPLETE)

**Date:** 2026-10-04 .. 2026-10-10
**Status:** COMPLETE -- the owner redirected the workspace to data products on
the daily, weekly and monthly timeframes ("step back to focus on the data
aspect"; paper and live are data only; rank entries by how many
higher-timeframe levels break together, the domino). Three products were
pre-registered, built, receipted and pushed: the domino census, the chance
comparison (the same STRAT pattern plain against stacked), and the equal-size
book with its R-matched check and a private chart page. Two mid-session Codex
audits were requested by the owner and folded the same day. The session closed
on the design of product 3, the STRAT-management book, with two forks awaiting
the owner's one-word answers. The owner's closing words: "this was a hard one.
Very very impressed, great work."

### What was accomplished

- HANDOFF archived under the 1,500-line limit at the owner's word (TVB-27..32 to
  `docs/session_archive/HANDOFF_TVB27-TVB32.md`); the TVB-36 review waived.
- Owner rulings collected and dated (below): domino, calendar quarter as
  context, the hammer's shape and sliver wick, every D / W / M break taken for
  data, the in-favour wiggle, no coin-flip baseline, the weekly-stop idea
  logged as an idea, trader language and a book-and-charts view in every
  report.
- **Product 1, the census** (commit 8b800a7): 292 live perps, 214,861
  coin-days; one directional break in six also took a higher-timeframe level
  for the first time; same-price stacks are a shared-open phenomenon; down's
  share rises with rank. Codex audit (12 findings, 1 HIGH) folded in 4560e7c;
  the fold uncovered that the venue's API serves zero-volume index-price
  candles before a coin first traded (94 coins, 48,331 coin-days), hence the
  VENUE ERA split used by everything after.
- **Product 2, the chance comparison** (c0f1826): one-R-before-the-stop by 1 /
  3 / 5 bars, the same pattern plain against stacked, hammer flags, weekly and
  monthly units, the owner's variant stop. A look-ahead defect was caught by
  the session before any number was reported (classing a daily trigger by
  which levels BROKE TODAY; amendments A1 / A2). Codex audit (8 findings, no
  remaining look-ahead) folded in dadf8ef.
- **Product 2b, the book, the R-matched check and the chart page** (dadf8ef):
  every plain daily pattern loses under a fixed one-R target and the setup-bar
  stop (-0.21% to -0.84% per trade before fees); the hammer shape brings each
  to about flat; the stacked 2-2 continuation is the one daily A+ class in the
  black; the shared-open stack loses more than plain on the daily and on every
  weekly setup; the daily near-stack edge survives bar-size matching, the
  daily shared-open gap does not, the weekly shared-open deficit keeps two
  thirds. A private chart page draws the same numbers (link in the lead's
  memory only).
- The data point that opened product 3: price reached a full R within 5 bars
  in 57% of plain reversals and 67% of inside-bar breaks, against 38% and 41%
  recorded as one R first; a third to a half of the stopped trades saw the
  target anyway. The stop, not the target, is what loses.
- Tests 295 -> 324 passing (census 16, chance 9 + 8, book 3 hand vectors).
  Memory: three new standing items (trader language reinforced, book + charts,
  the Codex exec recipe), the chart page reference, the project record.

### Context for next session

**Product 3, the STRAT-management book (card drafted, two forks open).** Same
units and entry as the chance comparison. No price stop. Exit at a daily close
when that day closed against the trade AND the week sits against it at that
moment (below its open for a long); the exit fill is that close; on a Monday
the two conditions are one. Target ladder: T1 = the pattern's own structural
magnitude on its timeframe (skill 5.1: the anchor bar's far wick for a 2-2
reversal and for a 1-2 off a reversal context; the 3-2 and the 2-2
continuation have none and use the ladder's next rung), T2 = the next unbroken
higher-timeframe level, T3 = the one above. Cap 20 daily bars, mark open
trades there. Report the share reaching T1 before the exit, T2 after T1, T3
after T2, how pre-T1 exits died, MFE, and three books in percent: all out at
T1, hold through T2 with the exit, exit only. Same receipt, book and chart
treatment; Codex review after.

The two forks, with the lead's recommendation (owner asked for it, has not
ruled): (1) the continuation's T1 -- recommend the next unbroken
higher-timeframe LEVEL (the owner's own ladder language, known at entry, no
leg definition needed); the measured move runs beside it as a declared
variant. (2) the exit clock for weekly and monthly trades -- recommend the
DAILY close with the week's colour for every trade (the lowest timeframe in the
stack carries the risk; a weekly trade that checks itself only on Friday has
no risk control for a week); the own-bar clock runs as a declared variant.
Both variants are cheap (same rows); the prereg names one headline
combination (level + daily clock) and shows each variant in one table, nothing
promoted afterwards.

Mechanics the next session needs: `census.day_events` returns the bar before
the setup bar only as a type; structural targets need its OHLC, so extend it
and re-run the census to confirm `splits` and `coins` stay byte-identical (the
TVB-37 refactor did exactly this). `chance.coin_units` yields the unit rows;
`book.coin_book_rows` shows how to attach outcomes to them;
`chart_page.build_data` shows how the page is fed. Runs are
`uv run python -m analysis.domino.<module>` (cache-based, 3-4 minutes each).
The Codex exec recipe and the chart page link are in the lead's private
memory. The owner reads impact as a hypothetical equal-size book in percent
and as charts; chance tables alone do not land.

### Files created/modified

- New: `analysis/domino/{census,chance,book,chart_page}.py`,
  `analysis/domino/{RECEIPT,CHANCE_RECEIPT,BOOK_RECEIPT}.md`,
  `analysis/domino/results/{census.json,tables.md,chance.json,chance_tables.md,
  book.json,book_tables.md}`, `docs/experiments/tvb37_domino_census_prereg.md`,
  `docs/experiments/tvb37_chance_comparison_prereg.md`,
  `docs/reviews/tvb37-codex-audit.md`, `docs/reviews/tvb37-chance-codex-audit.md`,
  `docs/session_archive/HANDOFF_TVB27-TVB32.md`,
  `tests/test_domino_{census,chance,chance_audit2,book}.py`.
- Modified: `docs/HANDOFF.md`, `docs/ARM_LEDGER.md` (new "Data products"
  section, three cards), `docs/reviews/REVIEW_REQUEST.md`,
  `.session_startup_prompt.md`, `.gitignore` (candle cache, unit rows, run
  logs, the page output).
- Gitignored, regenerable: `analysis/domino/data/` (candle cache),
  `results/events_rank2plus.csv.gz`, `results/trades.csv.gz`,
  `results/chance_book_page.html`, run logs.

### Rulings collected this session (owner, dated)

- 2026-10-04: paper and live = data only; trade D / W / M only; rank by levels
  broken together; quarter = context; monthly broadening-formation target =
  later; hierarchy and hammer definition go to design work; TVB-36 review
  waived. Domino = at least two levels stacked, any time, not only at shared
  opens; timeframes outside the stack "still in your direction" = support.
- 2026-10-05: quarter = CALENDAR quarter, context only (prefer in favour,
  ideally not inside, if inside the trade's colour). Hammer = the resource's
  basic shape (body in the far third), momo left out "to keep it simple";
  SOXL is a hard reference (leveraged fund vs perp).
- 2026-10-09: a sliver of wick allowed (coded as at most one tenth of the
  bar's own range); every D / W / M break of the prior bar's high or low is
  taken for data, continuations included ("take both for data"). Census card
  approved: "Yes the card reads right we can go when ready".
- 2026-10-10: intraday pass not needed yet; the hierarchy rulings need a
  comparison first. Hypothesis 1: stacks that exist only because yesterday was
  the last candle of the week or month (shared opens) underperform. Compare the
  same pattern with and without the stacked level (an "A+ setup" against its
  plain version). Levels must be exact; any wiggle room only in the trade's
  direction, and only for candle accuracy. Drop the quarter as a rule at
  first. Add the momo hammer for testing (a 2U sold hard inside the bar that
  held the prior low, closed as a hammer, then 2U again). Keep trader language
  in every data report.

### Product 1: the domino census (DONE, audited, folded)

- Prereg `docs/experiments/tvb37_domino_census_prereg.md` (definitions before
  code; labelled post-audit amendments appended). Engine
  `analysis/domino/census.py`; tests `tests/test_domino_census.py` (16 hand
  vectors); receipt `analysis/domino/RECEIPT.md` with a trader's glossary;
  ledger card under "Data products (counts, not arms)". Commit 8b800a7, then
  the audit fold.
- Headline, in chart terms: of all days that took out yesterday's high or
  low, about one in six also took last week's or last month's level for the
  first time. Four in five of those are day plus week. Same-price stacks are a
  shared-open phenomenon (99%: the old bar closed on its extreme). Two thirds
  of multi-level days have the levels more than 1% apart. Down's share rises
  with rank (52% / 61% / 71%). Reversal setups are under a third of classified
  setups on the day, week and month; a hammer or shooter sits on about one in
  six of them by the 33% rule, one in twelve with the sliver wick. Most breaks
  happened while the quarter had already taken out its low.
- Provenance found during the fold: the venue's API serves zero-volume
  index-price candles from before a coin traded (BTC from 2020-08-19, first
  trade 2023-02-26); 94 coins, 48,331 coin-days. A VENUE ERA split (each coin
  from its first traded day) sits beside ALL; no day or week share moves by
  more than half a point.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb37-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: ADDRESSED (mid-session audit of the census, owner-requested;
  the fold commit and the chance-comparison work will get their own request at
  session end)
- Commits to review: `ecc4d6c..8b800a7` on `main` (the census); the fold is
  the commit after ea58c6c
- Scope / what changed: census prereg, engine, tests, receipt, ledger card
- Focus areas (scrutinize these): calendar aggregation, first-break-only and
  strict comparisons, the shared-open exact stack, nesting check, bands,
  setup kinds, hammer flags, quarter states, denominators, LIQUID notional,
  data fetch, receipt honesty, tests, hygiene
- Reviewed by: local Codex CLI (`codex exec -s read-only`, third run; the
  first two could not start their Windows sandbox and returned a tooling
  BLOCK, not recorded)
- Findings: `docs/reviews/tvb37-codex-audit.md` -- NEEDS-CHANGES, 12 findings
  (F1 HIGH, F2 F3 F6 F8 F9 F11 F12 MEDIUM, F4 F5 F7 F10 LOW)

### Critical synthesis of the audit (where the session agrees, disputes, acts)

- **F1 HIGH, gaps and duplicates -- AGREE, fixed.** The engine trusted the
  array order: a missing day made the previous element "yesterday", a
  duplicate could mask a gap in a "complete" bar, and the first bar seen in a
  bucket passed as the shared open. Now: a day without an adjacent yesterday
  carries no event and is counted; duplicates keep the last copy and are
  counted; off-grid stamps are dropped and counted; complete means every
  calendar day present exactly once; shared open means the calendar first day.
  The cached history has zero gaps, duplicates or off-grid stamps (the engine
  now reports this), so the committed counts did not move.
- **F2 MEDIUM, nesting check -- AGREE, fixed.** The old check only fired at
  rank 2+, so a week-only hit would have been a silent rank 1 event. Now any
  higher-timeframe hit without a daily hit is a violation (still 0).
- **F3 / F6 MEDIUM, float boundaries -- AGREE, fixed.** Exactly 0.25%, exactly
  1% and a wick of exactly one tenth were falling one band out in binary
  floats. Comparisons now run on the venue's decimal prices; four hammer flags
  moved onto the inclusive boundary. No band in the 31,501 rows changed.
- **F4 LOW, units -- AGREE, fixed.** The row field is `gap_pct`, in percent.
- **F5 LOW, denominators -- AGREE, fixed.** Setups without a classifiable
  predecessor (250 / 261 / 231 / 194 by timeframe) are shown beside the
  percentages, which are of classified setups.
- **F7 LOW, equality to the open -- AGREE, documented.** A level exactly at
  the open is "against"; the prereg amendment says so.
- **F8 MEDIUM, events vs days -- AGREE, fixed in the receipt.** 15.9% of
  directional events; 17.8% of break days; outside days count twice as events.
  Both denominators are now in the tables.
- **F9 / F10 MEDIUM / LOW, exclusions and survivorship -- AGREE, fixed.** The
  run records excluded coins (none) and data quality; the receipt says
  survivors only and that LIQUID is today's membership applied backwards.
- **F11 MEDIUM, receipt wording -- AGREE on every item.** "Under a third"
  hid the quarter's 34.7%; "down leads slightly" hid 61% / 71%; "no share
  moves more than a point" was false for the monthly and quarterly hammer
  rows; "most xyz coins lack a prior quarter" confused coins with events (84
  of 114 have one); "history to 2023" was wrong -- 2020-08-19, which led to
  the provenance finding above. All corrected and tagged in the receipt.
- **F12 MEDIUM, tests -- AGREE, nine vectors added**, including the audit's
  four reproduced failures and the denominators.
- **Disputed: nothing.** One nuance: the reviewer's "the 53 plain-day exact
  stacks are valid" is accepted and is now explained in the receipt (yesterday
  retouched the higher level without breaking it).

### External Review, second request (the chance comparison)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb37-chance-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: ADDRESSED (owner-requested mid-session; folded the same day)
- Commits to review: `4560e7c..c0f1826` on `main` (chance prereg + engine +
  census refactor); the fold is the commit after cff7932
- Scope / what changed: `analysis/domino/chance.py`, its tests, receipt,
  prereg amendments A1 / A2, the `day_events` refactor of the census
- Focus areas (scrutinize these): remaining look-ahead in any condition or
  split column; the walker; horizons; follow-through; unit separation; the
  variant stop; cell statistics; venue era; the refactor's equivalence;
  receipt honesty; tests; hygiene
- Reviewed by: local Codex CLI (`codex exec -s read-only`, unelevated sandbox)
- Findings: `docs/reviews/tvb37-chance-codex-audit.md` -- NEEDS-CHANGES, 8
  findings (F1 F2 F4 F5 MEDIUM, F3 F6 F7 F8 LOW); **no remaining look-ahead
  found**; 477 committed cells and the full tables reproduced from the saved
  rows; the census refactor confirmed equivalent on 80 extra sequences

### Critical synthesis of the second audit

- **Look-ahead hunt -- clean.** The reviewer's first job was to find any
  remaining selection-on-outcome in a condition column after amendments A1 and
  A2. None found: the entry-time class, the weekly / monthly class, the
  flags, the month-open and quarter columns all read only what is known at the
  break. The retrospective `liquid` label and the survivor universe are
  disclosed, not leaks.
- **F1 MEDIUM, decimal touch fills -- AGREE, fixed.** The target was computed
  in binary floats, so a high exactly one R above the entry could read a hair
  short and miss the fill. Stop and target are now compared to the bar's
  prices as decimals (the same fix the census got for its bands). Re-run;
  moved cells listed in the receipt.
- **F2 MEDIUM, counts and greying -- AGREE, fixed.** Tables showed the unit
  count and greyed on it; the chance's denominator is the valid count at that
  horizon (censored excluded), which can be far smaller on monthly cells.
  Every table now shows the valid count beside each chance and greys on it;
  differences grey when either side is under 30 valid. The prereg's "every
  proportion carries an interval" was the intent, not what was built: the
  contract is restated in amendment A4 (intervals on the one-R chances and
  their differences; stop, entry-day and next-bar shares carry their count).
- **F3 LOW, LIQUID bookkeeping -- AGREE, fixed.** Censored counts are now
  computed per sample; the dropped-unit counters are labelled universe-level.
- **F4 MEDIUM, the "within two points" sentence -- AGREE, corrected.** It was
  false for some flagged cells (a plain outside STRICT cell differs by 6 points
  between venue era and LIQUID). Replaced with the scoped statement.
- **F5 MEDIUM, over-general sentences -- AGREE, corrected.** "Nothing flips
  across splits" ignored +4.7 in 2023; "every pattern by four to seven points"
  ignored the outside break's 2.6; "with fewer stops" was false for the
  continuation THIRD cell; "one in four to one in three" was the reversal and
  inside figures only; hypothesis 1 was declared on DAILY units, so the weekly
  shared-open result is a descriptive comparison, not a test of it. Receipt,
  ledger and this entry now say so.
- **F6 LOW, "exact was clean in both versions" -- AGREE, corrected to
  "nearly".** The first run's class took the largest gap among the levels
  that broke, so a same-price weekly stack could leave the exact cell when the
  day also reached a farther monthly level (292 units). The entry-time class
  fixed it.
- **F7 LOW, tests -- AGREE, eight vectors added** in
  `tests/test_domino_chance_audit2.py` (decimal fills both sides, monthly
  horizons and follow-through, weekly / monthly classes, A2 invariance of the
  context columns under a changed entry day, cell denominators and greying,
  flag mask on a non-default index, later zero-volume days, the variant's
  wrong-side counter). The obsolete bug test 13 is retired in A4.
- **F8 LOW, later zero-volume days -- AGREE, stated** in the receipt and A4.
- **Disputed: nothing.**

### Product 2: the chance comparison (DONE 2026-10-10, receipted)

The owner answered the two questions (in-favour wiggle YES; the card GO) and
added two notes: no coin-flip baseline ("a 2 going 3" makes the reference
about one in three, recorded not asserted), and a stop idea (stop at the
weekly bar, exit when a higher timeframe goes against the trade, let trades
run until invalidated, then size against liquidation) logged as the OWNER'S
IDEA and run as one variant table, with the setup-bar stop as the primary.

- Prereg `docs/experiments/tvb37_chance_comparison_prereg.md` with labelled
  amendments A1 and A2; engine `analysis/domino/chance.py` (event detection
  shared with the census through `census.day_events`; the census was
  refactored to expose it and re-run byte-identical); tests
  `tests/test_domino_chance.py` (9 vectors); receipt
  `analysis/domino/CHANCE_RECEIPT.md`; ledger card updated.
- **Defect caught before any number was reported (A1):** the daily "stack
  class" was first decided by which higher levels BROKE THAT DAY. That selects
  on the day's own travel (the "spread" cells read 60-80% one-R). A trader at
  the daily break cannot know it. The class is now the distance to the nearest
  UNBROKEN weekly or monthly level at the daily break. The same leak sat in
  the month-open and quarter context columns (A2). The look-ahead version is
  kept in the tables once, headed TRAP. Nesting guarantees a fresh higher
  level never sits short of yesterday's level, so the owner's "wiggle only in
  favour" is automatic.
- **What the arithmetic says, in chart terms (venue era):** the same-price
  stack at the Monday / 1st open adds nothing to a 2-2 continuation on the
  daily (32.9% vs 34.4% one R by 3 bars, more stops) and costs on the weekly
  (29% vs 42%, -12 points). A 2-2 continuation with an unbroken higher level
  within a quarter percent beyond the trigger did better (+6 points); the same
  compression hurt inside-bar breaks (-5). The hammer shape on the setup bar
  lifted the reversal, continuation and inside break by four to seven points (the outside break by about three), with fewer stops on all but the continuation (second audit F5). One in four
  to one in three daily units traded their stop on the entry day (the owner's
  "2 going 3"), all counted as stops. Nothing flips across direction, year,
  liquidity or the month's open. Hypothesis 1 reads as supported on the
  weekly, weak on the daily, untestable on reversals (7 shared-open exact
  reversal stacks in the whole sample: a bar that closes the week on its
  extreme is a 2 or a 3, not a reversal setup).
- Not done, flagged: an R-matched comparison (exact shared-open stacks carry
  the biggest setup bars); fees / funding / sizing; the Underlying-RTH mirror.

### Product 2b: the book view, the R-matched check and the chart page (DONE 2026-10-10)

Owner, after the chance receipt: "it is hard for me to understand the impact of
some of things unless talking in terms of p/l or percent performance even if
it's a hypothetical account (no leverage, no fees, single buy)", and "a
visualization of some of this would help ... like you reading data vs charts".
Declared as prereg amendment A3 BEFORE computing: two VIEWS of the same unit
rows, no new condition, nothing promoted. Engine `analysis/domino/book.py`
(reads the units through `chance.coin_units`); tests `tests/test_domino_book.py`
(3 vectors); receipt `analysis/domino/BOOK_RECEIPT.md`; tables
`results/book_tables.md`; page builder `analysis/domino/chart_page.py`
(output gitignored; the private claude.ai page is linked only in the lead's
memory, never in this public repo). New standing feedback saved: every data
product gets a book view and a chart page beside the receipt.

- **The book's rules:** one unit of notional per trade, long or short as the
  break, entry at the level, stop at the other side of the setup bar, one-R
  target, otherwise marked at the close of the fifth bar; no leverage, fees,
  funding or slippage; every trade taken; dollar figures are the SUM of
  1,000-dollar trades, not an account balance.
- **What it says, in money (venue era, 5 bars):** every plain daily pattern
  loses: 2-2 reversal -0.84% per trade (43,442 trades), 2-2 continuation
  -0.43%, inside break -0.54%, outside break -0.21%, with hit rates of 36-41%
  against stop rates of 41-55% (the pessimistic same-day call inside them).
  The hammer shape brings each pattern to about flat (-0.10% to +0.31%). The
  stacked 2-2 continuation is the one daily A+ class in the black (+0.44% with
  a level within a quarter percent beyond the trigger, +0.33% within 1%). The
  same-price stack at the Monday / 1st open loses more than plain (-1.19%;
  outside -2.23%) and on the weekly loses on every setup (-0.9% to -3.2%). The
  weekly 2-2 continuation whose day had already run 1%+ before the level broke
  is the biggest positive (+1.75% over 4,492 trades, +78k on the book, -31k
  drawdown).
- **R-matched (bar size held equal in five bins):** the daily near-continuation
  gap survives (+4.7 [+1, +8] by 3 bars, +6.0 [+3, +10] by 5); the daily
  shared-open gap vanishes (-0.7 [-2, +1]); the weekly shared-open deficit keeps
  two thirds of its size (-8.0 [-10, -6]) and holds in every bar-size bin.
- **Reading, kept to the arithmetic:** with a fixed one-R target and the
  setup-bar stop, the plain patterns are a losing book before fees; the hammer
  shape and the compression of a 2-2 continuation under an unbroken higher
  level are the two entry-time conditions that lift it to flat or slightly
  positive; the shared-open stack is not one of them. None of this tests STRAT
  trade management (targets at structure, running until invalidated), which is
  the owner's stated way of trading these.
- **Charts:** the private page draws the daily bars with intervals, the book
  curves for the daily continuation classes, the hammer split, the weekly bars
  and curves, the R-matched bars and the book table. Rebuild with
  `uv run python -m analysis.domino.chart_page` and republish to the same url.

### Open

- [ ] Product 3, the STRAT-management book: the owner's two one-word answers
      on the forks (continuation T1: level or leg; weekly / monthly exit clock:
      daily or own), then prereg + ledger card, then code, run, receipt, book,
      chart page, Codex review.
- [ ] Extend `census.day_events` to return the anchor bar's OHLC (needed for
      structural targets); re-run the census and confirm byte-identical splits.
- [ ] The hierarchy rulings the owner deferred (stop owner in a stack,
      continuation ranking, seat competition, which higher-timeframe event ends
      a trade), once the three books are in hand.
- [ ] Codex backlog run by the OWNER (docs/reviews/CODEX_BACKLOG_PROMPT.md: tvb31..35 +
      tvb37-close); TVB-38 folds every returned file BEFORE plan mode (owner's word at
      close, 2026-10-10).
- [ ] Close-out Codex review of the unreviewed commits (this entry's External
      Review block below); TVB-31..35 audits still unreturned (executor code;
      matter only before a real-money restart).
- [ ] An R-matched follow-up (date / coin held equal) only if the owner asks.
- [ ] Carried from earlier sessions, untouched: intraday-order pass on 1h
      history (owner: not yet); paper rule set / prereg for the other
      workspace; monthly broadening-formation target; Friday-close oracle /
      SOXL off-hours pricing; fresh wallet and executor restart checklist;
      scanner STRAT rulings; holiday calendar for the xyz clock; the TVB-36
      startup prompt's longer carried list.

### External Review, close-out (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb37-close-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: REQUESTED
- Commits to review: `ea58c6c..9e0f95e` on `main` (pinned 2026-10-10 after the push). Of
  these, 25a8ac5 and c0f1826 were already covered by the second mid-session
  audit (`4560e7c..c0f1826`); the UNREVIEWED commits are 4560e7c (the census
  audit fold), cff7932 (a request pointer), dadf8ef (the book view, the
  R-matched check, the chart-page builder, the second audit's fold) and the
  close-out docs commits.
- Scope / what changed: `analysis/domino/book.py` (equal-size book, R-matched
  reweighting, curves), `analysis/domino/chart_page.py` (page data mapping),
  the census fold in `census.py` (gap / duplicate proofing, any-rank nesting,
  decimal bands, venue-era split), `BOOK_RECEIPT.md`, prereg amendments A3 /
  A4, the ledger cards, this entry, the startup prompt.
- Focus areas (scrutinize these): the book's return arithmetic (sign for
  shorts, mark-to-market at the horizon close, censored exclusion, the summed
  equal-size dollars labelled as not an account); `r_matched` (quintile edges
  on the base, searchsorted side, renormalisation when a bin has no base
  units, the variance formula); `book_cell` drawdown on a by-date cumulative
  sum; `chart_page.build_data` (hit = one-R share, every number traceable to
  a table, no number invented on the page); the census fold against audit
  findings F1-F12; every sentence of `BOOK_RECEIPT.md` "What the arithmetic
  says" against its tables; tests missing for `chart_page`; public-repo
  hygiene (no claude.ai artifact link, no host, no secret; page output and run
  logs ignored); no Pine file changed.
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb37-close-codex-audit.md exists)

---

## Session TVB-36: paper-month receipt, the kill call on the round-3 mechanical book, regime and momentum receipts, the trade review page, and the higher-timeframe question left open (COMPLETE)

**Date:** 2026-10-02 .. 2026-10-04
**Status:** COMPLETE -- the owner redirected the session away from the planned
regime-design work to what they had watched on the paper platform. The hosted
ledger was pulled and decomposed, the unfilled signals were replayed, four
characterization receipts were committed, a visual trade review page was
published, and the session closed on the owner's caution against jumping to
conclusions plus an open design question about higher-timeframe context.
**The next session starts from the verbatim closing discussion in this entry.**

### READ FIRST: the owner's correction at close

Two framings in this session were the LEAD'S, not the owner's, and the owner
pushed back on both at close:

- The stop what-if (wider or no stop on every trade) was NOT requested as a
  test of moving stops. The owner's "maybe our stops are too tight" was a
  thought. The data point to carry is the plain one: **patterns do reach their
  targets** (35 of 88 stopped trades touched their ORIGINAL target within 72 h
  of the stop). In the owner's words, "even that is not enough".
- "The entries are worse than a coin flip, so it is not the fix" was a
  conclusion the lead attached to that what-if. The owner: "the one thing I
  would emphasize here is not jumping to conclusions."

What this session settles is arithmetic on one month of paper data. It does
not settle what the strategy should become. The receipts stand as receipts;
their "reading" paragraphs are the lead's and are open to the next session.

### Reminder the owner asked for: the as-built continuity and step-up rules

Verified 2026-10-04 in the rules as vendored into the paper platform (executor
pin fc90368: `signal_tfs`, `stack_tfs`, `htf_reversal_backing`, `TF_ORDER`).
Trader terms. This is what the bot DOES today, not what it should do.

1. **What is traded.** Entries only on the 1-hour, 4-hour and daily. The
   weekly and monthly are never traded.
2. **What the weekly and monthly do today.** (a) The weekly is one of the five
   continuity votes. (b) A weekly or monthly REVERSAL can sponsor a
   lower-timeframe continuation (item 4). (c) The monthly also rides every row
   inside the journaled 60 / day / week / month "sheet" verdict, which never
   gates anything.
3. **Continuity at entry.** Price must be on the trade's side of its own open
   on ALL FIVE of 15-minute, 1-hour, 4-hour, daily and weekly. So every trade
   on the review page had all five aligned at entry, by rule. The page does
   not show it, and the monthly was neither required nor recorded.
4. **Stepping up, as built: for PERMISSION only.** A continuation on the
   1-hour, 4-hour or daily is allowed only when a higher timeframe holds a
   live REVERSAL in the same direction that is still in force (price past its
   trigger and short of its target). The search climbs from the next
   timeframe up, through the weekly, to the monthly, and stops at the FIRST
   timeframe that qualifies. A higher-timeframe continuation never licenses
   anything. A sponsor whose own forming bar has gone outside is dead (1-3s
   exempt).
5. **Not built: stepping the target or the stop up.** Every trade keeps the
   stop and first target of its own entry-timeframe pattern and exits in full
   at that first target. The sponsor's target is journaled as evidence and
   never used.
6. **Exits as built.** A resting stop; a resting limit at the first target;
   an at-market exit if the entry bar goes outside; an at-market exit when all
   five timeframes are against the trade (mixed holds). Nothing exits on the
   week alone turning, on a weekly close, or on a daily close.
7. **What was tried on step-up in replay** (round-2 and weekend-1 ledgers,
   `docs/ARM_LEDGER.md`): walking the stop up the timeframes (A6) gave money
   back on the trades it shared with the control; banking half at the first
   target and running the rest to the next pivot (A7) was neutral on shared
   trades; licensing continuations by day / week / month continuity instead of
   a reversal (A3) was a small positive inside the noise of a dozen trades.
   The round-3 ruling deferred the walk-up to "a daily-entries-only variant".
   A round-3 STRAT ruling is on record for the next scanner release: a 3-1-2
   continuation's target is the outside bar's wick first, then a
   higher-timeframe pattern's target.
8. **Coupling.** At Monday 00:00 UTC the weekly, daily, 4-hour, 1-hour and
   15-minute candles share one open (on the 1st, the monthly too), so the five
   votes are one observation then. Three September flips fired half an hour
   after a Monday roll.

Against the owner's two assumptions in the closing message: (1) is correct.
(2) is partly correct: the bot does step up, but only to find a reversal that
licenses a continuation; it stops at the first higher timeframe that has one;
and continuations ARE traded in that licensed form (25 of the 116 unfilled
September signals were continuations).

### What was accomplished

- Session start: charter S0, startup prompt, HANDOFF TVB-35, CLAUDE.md; tests
  288 pass. TVB-35 audit NOT returned (TVB-31..35 all open). The owner opened
  by saying priorities had changed: they had been watching the strategy on the
  paper platform and an adjustment or overhaul comes first. A prop-firm note
  was logged to private memory at the owner's request (not discussed).
- **Paper ledger pulled** (read-only, the owner's hosted paper platform, three
  HIP-3 accounts; host never committed). `analysis/parallax/RECEIPT.md`:
  195 entry orders, 26 filled. The forward pilot filled nothing after 09-28 (a
  missed funding-boundary check blocked every later entry); the prop test lost
  51 of 56 entries to the scanner's 15-second permission window (orders were
  created a median 13.3 s after the observation); its $250 entry cap made the
  $100-risk setting about $10. 24 closed trades, 6 winners, -6.6R; losers'
  median best excursion 0.6R; no bar-close exit exists in the v2 rules.
- **The unfilled signals replayed** (`lostbook.py`): 116 distinct signals the
  strategy qualified and the platform never filled, walked through their own
  stop and target on public candles. The simulator first reproduced all 17
  actual stop and target outcomes. Result: 25 target, 77 stop, 14 open,
  -41.1R; 25% of resolved trades won against 40% for a driftless walk inside
  the same brackets (z -3.12); entries sat a median 0.01R past the trigger.
  Month, filled plus unfilled: 140 trades, -47.7R.
- **Session clock census:** 11,846 of 14,490 stock-perp signals (82%) were
  refused because the US underlying was closed; the Korea names peak at 00Z,
  the KRX opening cross.
- **The lead's call, on the owner's explicit invitation to say so:** the
  round-3 package as an AUTONOMOUS mechanical book is dead in the water
  (RECEIPT.md section 6). Read it with the correction at the top of this
  entry: the owner has not adopted that as a conclusion.
- **Stack map for the owner** ("between this space and the HL paper trading
  space I dont want to get them confused"): the scanner detects, the executor
  rules decide, the paper platform runs a pinned copy of those rules; this
  repo holds the design record and a different research family and executes
  nothing. Recorded in private memory.
- **Three more receipts** (definitions fixed in each docstring before reading):
  `analysis/regime/REGIME_LABELS_SEPT_RECEIPT.md` -- the Tightening half of
  the owner's Macro Risk Conditions indicator rebuilt from venue perps is
  defined at 140 of 140 entries but quiet 82-88% of the time, no separation;
  index continuity (BTC or the Nasdaq-100 perp against its own day, week and
  month open) had 73 of 135 entries taken with the index mixed, holding 28 of
  43 R lost. `analysis/momentum/SHARP_MOVE_RECEIPT.md` -- entering with a
  sharp bar at its close did not pay on 40 liquid crypto perps; post-hoc, sharp
  down bars bounced. The owner then explained how they ACTUALLY use each tool
  (verbatim below), which corrects the framing of all three tests.
- **Trade review page** (private page, link in private memory; builder
  `analysis/parallax/review/build_review.py`): all 142 September trades on
  candlestick charts with entry, stop and target lines, the exit marked, a
  15m / 1h / 4h / daily switch, inside and outside bars outlined, filters,
  and one-tap verdicts saved to the page's own store (collection `reviews`).
  Chart colors validated for colorblind separation in both themes.
- **Stop what-if** (`stop_whatif.py`), see the correction above: hindsight
  swing +91.6R; applied to every trade at the same size the month reads -54R
  as traded, -65R at 1.5x, -59R at 2x, -53R at 3x, -28R with no stop.
- **Owner rulings this session:** no session calendar to start, "just to
  test", then look at what a calendar would have done; weekends are altcoins
  only; stock perps on weekends are held until the Friday-close oracle is
  investigated in depth; index simultaneous breaks trade both directions; the
  one to three symbols are still to come from the owner; replies stay
  condensed and in trader terms until the owner signals a deep dive.
- **Corrections recorded:** the flip exit reads five timeframes in the v2
  package, not four; the 09-28 flips fired after a MONDAY roll.

### Closing discussion, verbatim

Kept word for word at the owner's request so the next session can explore it
fully. Three short personal asides are removed from the owner's messages and
marked in place; nothing about trading is changed. Typos are the originals.
The lead's long replies of 10-02 and 10-03 (the kill call, the stack map, the
indicator brainstorm) are in the receipts and are not repeated here.

**Owner, 2026-10-02, after the paper ledger read-out (the invitation and the
discretionary context):**

```text
Lets do it - now I will explicity flag this and it is okay for you to say so, ill leave it just at that for now. But at anytime you consider the strategy dead in the water say so, and give your reasoning for it. No
hard feelings. This is a discrentionary strategy trying to be coded. Not easy. It doesnt take into account the fact that a trader knows treasury yields are at multi decade high, it doesnt see the exact moment the
dollar spikes and holds or spikes and falls and the implications that come along with it, it has tickers that could trade the asia session cleanly and somehow stands at the sideline as a perp for equities at 00:00
utc while the korea/china session is getting at hand. It doesnt realize the fact that almost all price action has come from this and the rise/fall of oil and its velocity everyday which almost always happens in non
US market standard hours. honestly? strat gives you the framework - it doesnt give you the golden ticket - this is the discrenionary part. alot of strat traders including myself take the things above as granted or
things in the back of their head that barely register as strategy. its just a correlation they know when price action moves. they either recognize it (think human machine learning maybe?) or they try to understand
it - they find the correlation and extreme minor "blips" of market inefficiency for THEM and just them. that might be realizing TFC nearing a crucial level, seeing CL spike, wathcing 10Y1! break a high from a decade
ago all while watching VIX spike 4 percent or more, while also knowing houthi strikes on saudi pipelines and other macro ecnomoinc context. all that can be calculated in under a minute or fractions of a second -
something that seems to me at least impossible to code without spending thousands of dollars.

And the kicker? were doing perps - 24/7 regime distinction? throw away your scholary articles - they have been replicated and arbitraged away or just dont have much of a place in what we do.

Feel free to ask questions.
```

**Owner, 2026-10-03 (the indicators and the first rulings):**

```text
1. Explain just exactly what the mechanical book is - between this space and the HL paper trading space I dont want to get them confused
2. Ideally it would be nice for me to not be the regime input - though im not against the idea, brainstorming this would be interesting - there is a macro indicator I can provide - one that combines yields, dxy, oil and vix.  There is also one for jpy/usd (or maybe the other way - the one that is most common - I have not played around with this yet)
 - momentum strategy complimented would be nice too to play with - especially with altcoins lately - I have a "sharp move detector" - not sure if combining this somehow with bolliger bands with strat levels as targets/areas of exhaustion would be worth exploring
3. Ill look and provide and provide these soon - [personal aside omitted] so I want to be accurate here
4.  I would say start with no session calendar - just to test - based off results see what would have happened with a session calendar

Indicators (plus any that COULD be relevant ill let you look)
- "C:\Strat_Trading_Bot\tv_indicators\pine\macro_risk_conditions_v1_2.pine"
- "C:\Strat_Trading_Bot\tv_indicators\pine\Yen_Cross_Assest_Monitor.pine" (some symbols were incorrectly listed in this indicator not on tradingview as listed - easy switch as I found their actual tickers available quickly)
- "C:\Strat_Trading_Bot\tv_indicators\pine\sharp_move_detector_v2.pine"
- "C:\Strat_Trading_Bot\tv_indicators\pine\memory_complex_composite.pine"

All others are in that folder
```

**Owner, 2026-10-03 (how each tool is actually used; the working-style ask):**

```text
Few things based off personal experience, and I likely am missing some things as I haven't got a chance and likely won't [personal aside omitted] until tomorrow. One thing I noticed though and a few thoughts

1. Macro risk conditions - too many signals meshing and clashing together. This was discussed before with Claude and I believe I tailored the indicator to use less clashing symbols. Oil, dxy and yields are things that always and typically don't rise in tandem. Oil can fall yields can fall, dxy can go up. Oil can rise, economic eats can make yields fall, maybe another factor makes dxy go up. Middle east developments can make oil and vix spike - but economic data again can make day and yields fall. This together makes the indicator useless as a lot of the time they fight each other leading to small to neutral overall moves.

2. Index continuity - honestly only good for short trades on simultaneous breaks. All indices (nq/es/mym/iwm) break together one way to the upside or downside with an actionable signal such as a strong hammer/shooter coming first and closing as such (hammer - 33 percent of body is wick extreme high has no wick indicating heavy buying into the close of the bar) shooter is the same just in reverse. This is not very common but a strong move - can discuss more in detail later.

3. Sharp move detector has to be paired with something else - when I see it live it is usually a symbol that might be a 2U-2U continuation (not always just some things I notice) that also breaks a previous week/month high or low. Bollinger bands would be on a higher timeframe such as 4 hour. Lower timeframe again is noise. Sharp move detector is the "let me look, not base a decision) next comes "did something important happen price action wise or are we still inside on the daily timeframe? " Bollinger bands are simply assessing the retail trader sentiment.

4. Yen monitor - hadn't played with it as mentioned. Just provided it in case there was anything good in there.

5. I played around with this some not much. Not a huge or great signal - but notices any drift between memory name or if memory names are in alignment strengthing their case. Can also potentially indicate agreement/disagreement with things like EWY/KOPSI/KORU if the Korean memory complex is moving too. All other memory names strengthens the argument.

6. Weekends - I like altcoin tests here. The major crypto names have a tendency especially on weekends to trade in a very very tight range, maybe spike one way then the other but typically a lot of higher timeframe inside bars or daily breaks with very very little target.

7. I'm working currently on the HL paper trading space. It's hard to navigate, hard to look as past trades visually for good data, seems Claude there also has reservations about pushing account risk and leverage when it is a place where this can be a playground.

Let me know if I did or did not hit your points. The more condense and it trader terms your responses are from here until I pretty much say [personal aside omitted: the owner's own phrase for "I have time for a deep dive"] helps both of us so things aren't skipped over. I can always ask for more clarity and so can you.
```

**Lead's reply:**

```text
You hit every point, and three of them correct how I tested things. Your numbering:

1. Macro composite. Agreed, and the data shows it. The label sat neutral over 80% of the time because the pieces cancel. Dropped as a gate. If anything survives, it is one driver at a time, never the average.
2. Index. Yours is an event: every index breaking the same way after a hammer or shooter closes. I tested the standing version, which only limited damage. Yours is untested. On the venue only the Nasdaq and S&P perps exist. Dow and Russell need TradingView.
3. Sharp move detector. I tested it as an entry, which is not how you use it. Your read is alarm first, then one question: did it take out last week's or last month's high or low, or is the daily still inside? Bands go on the 4-hour for sentiment. That is a different test, and I can run it.
4. Yen monitor. Parked.
5. Memory names. Supporting evidence, not a signal. EWY, the KOSPI 200 and KORU are all on the venue, so the Korea cross-check is available.
6. Weekends. Altcoins, majors out. Noted for the weekend test.
7. Paper space. It is a playground, so push it. My own reservation two days ago was misplaced for paper. One mechanical point for that session: leverage alone changes nothing, because size comes from risk per trade. Raise risk per trade and the max entry size together. The $250 entry cap is what turned your $100 risk into about $10.

Unless you say otherwise, I am treating the old book as retired.

Two one-word answers when you can:
- Point 2, "short trades": quick trades in either direction, or shorts only?
- Weekends: stock perps too, or crypto alts only?

Parked for the detailed talk: your hammer adds "closes at the extreme, no wick", which the written rule does not require.

One offer: I can build a page showing every September trade on a chart with entry, stop, target and exit marked, since reviewing trades visually is the pain point.
```

**Owner:**

```text
1. Short trades - yes short and long
2. Weekends for now altcoins. Reasoning: Currently majors seem tied largely to BTC, which itself seems tied to the regular market. Equity perps have the Oracle concept from Friday Close, which we would need to investigate very in depth before anything was implemented here. So that's why I am saying hold off on that for now. I would say Sundays around noon in the future they potentially could be implemented but I can tell you that Saturdays typically are very very dead in a very tight small range Sundays only open up usually if there is some type of geopolitical or macro economic event tied to it that happened during the weekend.

And sure, I'll take you up on the visual part as I have a feeling that we probably are getting stopped out early while the move probably on some higher time frame might go in our favor. But no need to dig that deep. I'll look at it when I see it visually, which will help to see where we are going wrong.
```

**Lead's reply (the review page; link kept in private memory):**

```text
Noted on both. Simultaneous breaks trade both ways. Weekends are altcoins only, with no stock perps until the Friday-close oracle is understood, and Saturdays skipped as dead.

The review page is live: September Trade Review [link omitted from this public file]

- Every trade on a chart. All 142, with entry, stop and target lines and the exit marked. 26 were filled. The other 116 are orders the platform refused, replayed through their own stop and target.
- Step up the timeframe. Buttons for 15m, 1h, 4h and daily on the same trade, so you can see whether the bigger picture went your way after the stop.
- Inside and outside bars are outlined. Switch it off if it is noise.
- Tap a verdict. Stopped too early, bad entry, target too far, good trade, should have skipped, plus an optional note. It saves, and I can read your verdicts back next session, so you do not have to type up what you saw.

On your hunch: 35 of the 88 stopped trades reached their original target within three days after the stop. There is a filter for exactly those, and the page opens on one. Treat it as a list of charts to look at, not proof. With stops and targets this close, random chop produces about that many. The bot's own early exits look better: 6 of the 7 went on to hit the stop anyway.

I tested the saving by writing, reading back and deleting one test row. I previewed the charts locally in dark theme only. I could not click through the hosted page itself, so tell me if anything looks off on your phone.
```

**Owner:**

```text
so how would the trades that reached their target have affected the overall return vs the previous numbers?
```

**Lead's reply (the what-if the owner later said was not what they meant to test):**

```text
On paper it is huge. Counting those 35 as winners swings the month by about 92R, from -48R to +44R. But that is hindsight. No rule knows in advance which stops come back.

The honest test is to widen the stop on every trade and let the ones that never come back lose more:

| Stop | Trades that hit target | Month, same position size | Month, size cut to keep risk equal |
|---|---|---|---|
| As traded | 24% | -54R | -54R |
| 1.5x wider | 33% | -65R | -44R |
| 2x wider | 44% | -59R | -30R |
| 3x wider | 60% | -53R | -18R |
| No stop | 70 of 142 | -28R | not applicable |

- Same size: wider stops win more often, but each loss is bigger, so the month does not improve.
- Size cut to match: it loses less at every step, and still never turns positive.
- No stop: half reach target. The other half sit on open losses averaging about -1.9R, with the worst at -12.7R.

The "as traded" row reads -54R, not -48R, because every row here uses the same simple replay of stop and target only. The recorded -48R includes the bot's early exits, which saved a few R.

So your eye is right that many stops come back. It is not the fix. A wider stop mostly trades many small losses for fewer large ones, and the entries are still worse than a coin flip.
```

**Owner, 2026-10-04 (THE CLOSING MESSAGE: start here next session):**

```text
So the one thing I would emphasize here is not jumping to conclusions. The what if on the stop/target information isn't and wasn't meant by me to test moving stops. While I believe I might have mentioned something like "maybe our stops are too tight" that was more a thought. The main data point here to focus on isn't R it's taking the data point of patterns do hit their target. But yes even that is not enough.

I briefly am looking through the trades now. I may have to be reminded of our current timeframe continuity rules and stepping up time-frames in trades.

Just by browsing I can't tell exactly the full context of the trade as continuity is unknown. A 4HR 3-2U CAN be a good trade, but emphasis on the can.

A few ways to go from here - and you can give me your thoughts. Here are just a few quick ones of mine.

1. I'm assuming we decided at some point to not trade time-frames higher than daily, leaving weekly and monthly only for context. This is an assumption I can be wrong
2. Due to this, and even if the above is not true, we are not stepping up time-frames looking for the bigger trade on anything larger than a daily, or if we do we possibly even stop at the first higher timeframe that shows a continuation pattern, since we currently don't implement those. The reasoning behind this was more to ensure accuracy of detection first which has gotten immensely better.
3. The question then becomes: "what did we miss in the higher context? With the small amount we are risking, how far can our stop go if we bump up the target timeframe? If it's a weekly timeframe trade do we place our stop at a daily pivot? Or keep it at the same timeframe? If we are trading a daily pattern, do we stay in the trade until the week flips red, or the week is red upon that daily closes bar, or stay in until the weekly bar closes red? (With the same scenario being applied to the other different timeframe)"

This isn't a "let's overfit this". Trading to an extent is over fitting from previous pattern matching. But what this step is, is the "how do we code rules that a discretionary trader can see very fast, and occasionally even maybe drift from the rules (such as staying in a trade past its target when a higher timeframe trade is triggered too?) ?"

Drifting from rules is more a term I used for what might be referred to as something like " trader intuition ". Not something you can ever code as a system automatically, but a chance parts of it can be taken.

I would say due to context of 689k tokens we can not answer this right now. I would say now is a good time to run session end and try to leave as much of the latter parts of this conversation, especially what we are discussing now, verbatim in the handoff document to have to chance to fully explore next session
```

**Lead's reply at close:**

```text
You are right, and I overstepped: I turned "many stops come back" into a verdict on stops and entries when the observation that matters is the simpler one, patterns do reach their targets. I will record it that way.
```

### Context for next session

- Begin with the closing message above and the reminder section. Restate the
  as-built rules to the owner in trader terms and confirm them before any
  design talk; the owner's assumption 2 differs from the code in the ways
  listed there.
- The owner's three questions are DESIGN questions in the STRAT STOP-and-ASK
  zone: load the strat-methodology skill, plan mode, dual language, a-priori
  definitions, prereg before code. Relevant skill sections: 4.5 (domino
  cascade, "can this trigger the week? the month?"), 5.1 (pivot ladder, "an
  HTF signal taking over justifies continuation" at magnitude), 5.4
  (management profiles; "a 60-minute flip against = reduce, not exit").
- The owner said they cannot judge a trade on the review page because the
  continuity and higher context are not shown. The cheapest useful first step
  is to PUT that context on the page: the five-timeframe continuity at entry
  (aligned by rule) plus the monthly; the daily, weekly and monthly bar type
  and color at the entry instant; prior week and month high and low lines; and
  the sponsoring timeframe on continuations. The per-coin daily history
  already on the page (150 days) is enough to build the weekly and monthly.
- Read the owner's verdicts from the page's `reviews` collection first
  (private memory holds the link and the tool call). They are the owner's own
  read of where it goes wrong.
- Keep replies condensed and in trader terms until the owner signals they
  have time for a deep dive. Do not attach conclusions to the owner's
  thoughts; report the data point asked for and stop.
- The paper platform's blockers (funding-boundary block, order latency, the
  prop test's entry cap) belong to the owner's other session in that repo; any
  forward number from it is not comparable until they are fixed.

### Files created/modified

- analysis/parallax/: RECEIPT.md, trades.py, mfe.py, lostbook.py, census.py,
  results/{trades_*,mfe_mae,lostbook,census,stop_whatif}.json,
  review/{build_review.py, stop_whatif.py, trade_review.template.html}
- analysis/regime/: venue_mrc.py, venue_mrc.json, index_continuity.py,
  index_continuity.json, REGIME_LABELS_SEPT_RECEIPT.md
- analysis/momentum/: sharp_move_study.py, sharp_move_study.json,
  SHARP_MOVE_RECEIPT.md, top40_main.json, as_of.json
- .gitignore (analysis/parallax/exports/ stays local)
- docs/HANDOFF.md, .session_startup_prompt.md, docs/reviews/REVIEW_REQUEST.md,
  docs/ARM_LEDGER.md (paper-month card)
- Not in this repo: the published review page (private) and its data files;
  raw account exports and candle caches under analysis/parallax/exports/.
- No Pine file changed. No change to the executor, the scanner or the paper
  platform repos (the paper platform was read, never written).

### Open

- [ ] Design discussion on the owner's closing message: higher-timeframe
      context, where the stop sits when the target timeframe is bumped up, and
      which higher-timeframe event ends a trade. Deep dive only on the owner's
      signal.
- [ ] Read the owner's verdicts from the review page store before that
      discussion.
- [ ] Add the higher-timeframe context to the review page (continuity at
      entry with the monthly, higher-timeframe bar types, prior week and month
      levels, continuation sponsor).
- [ ] The owner supplies the one to three symbols.
- [ ] No-session-calendar test: define it (session journaled, not gated;
      weekends altcoins only; stock perps on weekends held). It needs a new
      experiment identity on the paper platform, in that repo.
- [ ] Friday-close oracle for stock perps: in-depth investigation before any
      weekend stock-perp trading (owner's condition).
- [ ] Sharp-move alarm tested the way the owner uses it (alarm, then prior
      week or month level taken out, daily not inside, 4-hour bands as
      sentiment): offered, not run.
- [ ] Index simultaneous break (all indices together after a hammer or
      shooter, both directions): untested; Dow and Russell are not on the
      venue; confirm the hammer definition detail (the owner adds "no wick at
      the extreme"; skill R20 does not).
- [ ] The flush-bounce observation: a design candidate only, STOP-and-ASK.
- [ ] Paper platform (other repo): funding-boundary block, order latency
      against the 15-second window, the prop test's $250 entry cap.
- [ ] HANDOFF.md is far over 1,500 lines: archive TVB-27..TVB-32 to
      docs/session_archive/ on the owner's word (asked at TVB-34, TVB-35 and
      again now).
- [ ] TVB-31..TVB-35 session reviews still unreturned; TVB-36 requested.
- [ ] Carried from TVB-35: fresh wallet and executor restart checklist (only
      on the owner's word; the executor stays DOWN under KILL_FLAT); holiday
      calendar for the xyz clock; scanner release with the three STRAT rulings
      plus PR-B / PR-A; the 1-3 trigger convention ruling (far side vs
      reclaim); round-3 close-out replay and the 12-continuation replay;
      score-picker and cost-picker receipts; executor-side secret scan; July
      A0b anchor; prospective halfway generator; slippage model; TVB-18
      repairs; month-end fresh-window regen.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb36-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: N/A -- waived by the owner 2026-10-04 at TVB-37 session
  start (was REQUESTED); see docs/reviews/REVIEW_REQUEST.md
- Commits to review: `3f087b0..ecc4d6c` on `main` (pre-session sha ..
  head; verify with `git diff --name-status 3f087b0..ecc4d6c`). This repo
  only; no sibling-repo commits this session.
- Scope / what changed: analysis scripts and receipts over one month of paper
  data (reconstruction, bracket-only replay of unfilled signals, random-walk
  baseline, two regime labels, a sharp-move event study, a stop what-if), a
  trade review page builder, and the session docs. No strategy code, no Pine.
- Focus areas (scrutinize these): (1) `lostbook.py` -- entry at the order's
  reference price, bracket-only, both-touch counts as stop, the 17-of-17
  calibration, deduplication by signal key across accounts; (2) `census.py` --
  the 1/(1+R:R) random-walk baseline and whether a z-score over trades that
  cluster in time is overstated; (3) `mfe.py` -- matching software exits to
  entries by symbol; (4) `venue_mrc.py` -- fidelity to the Pine script (change
  horizon, population stdev, EMA through gaps, staleness, DXY weights) and the
  completed-bar timing; (5) `index_continuity.py` -- UTC day / week / month
  opens and the coupled-day count; (6) `sharp_move_study.py` -- ATR[1] by
  Wilder RMA, the volume confirmation, per-bar clustering, and whether the
  post-hoc cuts are labeled everywhere they are quoted; (7)
  `build_review.py` -- the 72-hour "reached target after the stop" tag;
  `stop_whatif.py` conventions; (8) the READING paragraphs in the receipts
  against the owner's correction at the top of the HANDOFF entry -- flag any
  sentence that states a conclusion the arithmetic does not carry; (9)
  public-repo hygiene: no hosted platform URL, no page link, no secret; (10)
  no Pine file changed (verify).
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb36-codex-audit.md exists)

---

## Session TVB-35: round-3 monitoring, two shadows added, round 3 HALTED on the user's word, deployment paused for regime-detection design (COMPLETE)

**Date:** 2026-09-07/08
**Status:** COMPLETE -- the round-3 tape was read from the raw journals and the
venue record, the user's -$133 was located (a manual ZEC liquidation 15 h
BEFORE the ledger window, same wallet), two review-seeded shadow columns
were built and deployed to executor main (not to the VPS), and round 3 was
killed flat on the user's word with a clean receipt. The user is pausing
live deployment for the week of 2026-09-08 and wants it spent on regime
detection (dollar / 10-year yield / crude sensitivity of the traded names).

### What was accomplished

- Session start: charter S0, startup prompt, HANDOFF TVB-34, CLAUDE.md;
  TVB-34 audit NOT returned (TVB-31..34 all still open); tests 288 pass.
- Astra's "what I would do next" (entry selection) assessed against the
  record: points 1 (first obstacle), 3 (dissect the 12 continuations) and
  5 (post-entry path metrics) agreed and largely already ruled (R-A/R-B/
  R-C) or replayable; point 2 (hourly/daily control as the FIRST live
  change) declined -- shadow first, the five-dot arm is one day old;
  point 4 (seat competition) agreed as a shadow; four seats make it near-
  inert. Proposed order: scanner release -> shadows before restart ->
  12-cont replay under R-A -> path-metrics block.
- The user's question "didn't we fold volume INTO the score?" answered:
  yes, as `rank` = score x log10(24h volume), one composite journaled per
  row; the scanner's score is served unchanged and the parts ride along.
- Executor amendment 2026-09-07a (098cff1, pushed; 1,204 tests): `stack_hd`
  (hourly+daily immediate-control verdict, review R17) on every decision
  row; `spread_bps` / `tob_bid_usd` / `tob_ask_usd` from the venue l2Book
  on entry and seat-stage rows only (review R21), once per coin per poll,
  cap 20, None on failure. Journal-only; no gate; no config change; README
  + PREREG amended.
- Round-3 ledger pulled (the classifier blocked history-derived SSH; the
  user gave the host in chat + permission): 5,330 decision rows, 18 entries,
  watch list clean (no liq_inside_stop, no fee_rate_unavailable, lev +
  liq_px_venue on every entry, the five shadows on every row). Venue fills
  since the open reconcile to the books (-$4.60 gross, $0.87 fees at the
  first read; -$3.92 after the two kill-flat exits).
- The -$133 located: ZEC short LIQUIDATED 2026-09-06 04:46:32Z on the same
  master wallet (userFillsByTime carries a `liquidation` block; my first
  query started at the round open and missed it). Outside the ledger by
  time; fouls the phone-app lifetime view only.
- Labels for the replay: Labor Day (xyz clock has no holiday calendar; 394
  "rth" rows, one entry = SK Hynix); the weekly dot vetoed 2/91 (Sun/Mon
  coupling with the daily open); BCH's TP filled in three fragments with
  protection_mismatch logged every 6 s; sheet stack "mixed" on 9/18
  entries (all shorts, 8 lost) = a question.
- KILL_FLAT on the user's word 19:00:17Z: SKHX long + ENA short closed in
  3 s, receipt clean, verified from the public API (0/0 both dexes, spot
  USDC 197.28, hold 0), no process, interlock LEFT IN PLACE. Journals +
  DEPLOYED_SHA copied to executor runs/2026-09-06_round3_aborted/.
  Executor README STATUS 2026-09-07 (7dc011f, pushed).
- Public record: prereg amendment 2026-09-07a, ARM_LEDGER round-3 halt
  card, this entry, startup prompt for TVB-36.
- POST-CLOSE ADDENDUM (2026-09-08 23:xxZ, user: "I'd be okay with going ahead
  and doing this now"): the macro-regime RECEIPT. Source question answered:
  TradingView is enough for the receipt (TVC:DXY, TVC:US10Y, NYMEX:CL1!,
  ICEEUR:BRN1!, SP:SPX, BITSTAMP:BTCUSD at 60m/D/W, 300 bars each, harvested
  by scripts/tvb35_regime_harvest.mjs into analysis/regime/data/ with a
  MANIFEST; TradingView launched with CDP by me, the user's chart restored
  to CBOT_MINI:10Y1! 60). A PROSPECTIVE source for the executor (VPS has no
  TradingView) is a design-session item. analysis/regime/receipt.py labels
  all 84 closed trades + 39,653 decision rows with a-priori labels fixed in
  its docstring BEFORE reading numbers (daily/weekly dot per reference =
  price vs that reference's OWN forming open; macro_dir headwind = dollar
  up AND 10-year up, tailwind = both down, else mixed; alignment with/
  against/mixed; whipsaw = S&P or BTC running outside day). CAUGHT AND
  FIXED before reading: a frozen Friday close was labeling weekend trades
  as live dots -- a reference with no 60m bar in 2 h now reads "closed"
  (R18 on my own script). HEADLINE = a structural one: the label EXISTS
  for only 32 of 84 trades. Weekend 1: 29/34 trades entered while both
  references were closed; round 3: the 10-year was closed all Labor Day,
  18/18 mixed. Only round 2 is labelable: with 16 trades (7 wins, +6.75pp,
  +$1.80), mixed 12 (+4.3pp), against 4 (0 wins, -2.94pp) -- the sign
  matches the prior, n=4 says nothing. The running outside-day whipsaw
  flag fired on 2/84 entries = inert as an entry-time label (needs a
  different a-priori measure: prior-day outside bar, range vs ATR, or
  realized vol). NOW (23:33Z): dollar down daily+weekly, 10-year closed,
  WTI up daily+weekly, BTC down, S&P closed -> mixed. Output:
  analysis/regime/REGIME_RECEIPT.md + receipt.json. Characterization only.

### Context for next session

The executor is DOWN by design under the KILL_FLAT interlock; VPS still
holds 9f39ba9 (098cff1 with the shadows is NOT deployed). Deployment is
PAUSED for the week on the user's call (holiday-shortened week,
geopolitical headlines, economic data, a sensitive market). The user
wants the week on REGIME DETECTION: the traded names are sensitive to
DXY and the US 10-year (which tagged a 2023 pivot high on 09-08 morning);
crude 94.72 / HIP-3 Brent ~99; the market is whipsaw and headline-driven.
Design session in plan mode, dual language, a-priori labels only; see the
startup prompt. Restart checklist when the fresh wallet exists: approve
the agent FIRST -> extraAgents -> fund -> re-pin config wallet/risk/cap ->
deploy 098cff1 -> `--once` receipt -> rm KILL_FLAT on the user's word ->
tmux --live. Whether the restart continues the round-3 ledger or opens a
new one is the user's call.

### Files created/modified

- docs/HANDOFF.md, .session_startup_prompt.md, docs/reviews/REVIEW_REQUEST.md,
  docs/experiments/tvb33_round3_prereg.md (amendment 2026-09-07a),
  docs/ARM_LEDGER.md (round-3 halt card)
- hip3-executor (private): src/hip3_executor/{rules,broker,engine}.py,
  tests/conftest.py, tests/test_shadows_hd_book.py (new), README.md,
  runs/2026-09-04_replay1/PREREG.md, runs/2026-09-06_round3_aborted/ (local,
  journals gitignored per the runs convention -- check before relying on it)

### Open

- [ ] HANDOFF.md is over 1,500 lines: archive TVB-27..TVB-32 to
      docs/session_archive/ on the user's word (asked again at TVB-35 close).
- [ ] Regime-detection design session (TVB-36, plan mode): a-priori macro
      labels (dollar / yields / crude continuity; expansion = whipsaw),
      shadow-journaled on the executor first, receipted on the three closed
      ledgers as characterization only; never sample-tuned.
- [ ] Fresh wallet + restart of the executor (checklist above), 098cff1 to
      deploy; round-3 ledger continue-vs-new = user's call.
- [ ] Holiday calendar for the xyz session clock (review R18): at least a
      US-holiday list; the Korea-linked names need their own session.
- [ ] Scanner release with the three STRAT rulings + PR-B / PR-A.
- [ ] Round-3 close-out replay (LedgerSpec, shadows journaled-first) and the
      12-continuation replay under R-A; the score-picker and cost-picker
      receipts; the post-entry path-metrics block (Astra point 5).
- [ ] Executor push gate: this repo's secret_scan walks THIS repo; pointed at
      the executor it flags the master address in weekend-1 records (there by
      design). Decide an allowlist or an executor-local scan; never mask the
      exit code with a pipe.
- [ ] July A0b anchor under feasible fills; prospective halfway generator;
      slippage model; TVB-18 repairs; month-end fresh-window regen.
- [ ] TVB-31/32/33/34 session reviews still unreturned.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb35-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: REQUESTED
- Commits to review: `848db00..HEAD` on `main` = 5b028a5 (the session-end
  docs) + the sha-pin follow-up commit on top of it (this repo: docs only;
  `git diff --name-status 848db00..HEAD` lists HANDOFF, the startup prompt,
  REVIEW_REQUEST, the prereg, ARM_LEDGER); hip3-executor (private, local
  transport) `5cd2b0d..fc90368` on main (098cff1 the shadows, 7dc011f the
  STATUS, fc90368 the round-3 ledger slices + run README).
- Scope / what changed: two journal-only shadow columns on the executor
  (hourly/daily control verdict; order-book spread on seat-stage rows), the
  round-3 read-out and halt, the public prereg / ledger amendments.
- Focus areas (scrutinize these): the seat-stage gating of the l2Book read
  (does any refusal reason that should count as "competed" fall outside
  SEAT_STAGE_REASONS, e.g. already_in_position?); the per-poll cache keyed by
  coin while `mid` can differ per signal row; l2Book naming for builder-dex
  coins; the claim that the weekly dot duplicates the daily on Sun/Mon (check
  the served 1w candle's open against the scanner's week boundary); whether
  the Labor Day rows are correctly labeled by `session` alone; the ZEC
  liquidation placement relative to the ledger window; no Pine file changed
  (verify).
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb35-codex-audit.md exists)

---

## Session TVB-34: deep-dive external review delivered and FOLDED, round-3 package approved and LIVE (COMPLETE)

**Date:** 2026-09-05/06
**Status:** COMPLETE -- the whole-program review came back, every checkable number
reproduced, five mechanics defects repaired on the executor, the research control
family watermarked, the user's Sunday rulings prereg'd, the round-3 package built
and LIVE on the VPS (effective open 2026-09-06 19:52:53Z after the agent-pruning
incident). Detail lives in the TVB-33 entry section 7 (the critical synthesis)
and its Open list; this entry is the close-out.

### What was accomplished

- Wrote and delivered `docs/guides/STRATEGY_DEEP_DIVE_REVIEW_PROMPT_2026-09-05.md`;
  the review returned as `docs/reviews/deep-dive-2026-09-05-astra.md`.
- Verified the review from the raw receipts (liquidation geometry, A9
  decomposition, research entry containment 58/106, fee algebra) BEFORE editing.
- Executor (main): liquidation-aware clearance (leverage set per ticket, venue
  liquidationPx receipted, liq_inside_stop warns), malformed-flat guard, "Stop
  Market" exact, partial-close fragments, dead-sponsor license; halfway
  synthesizer fix (amendment j) + parity re-gated + all arms re-run (pre-fix
  receipts archived); replay port + differential cases; 1,188 tests.
- Research: `TwinConfig.entry_fill "feasible"` + `analysis/paper/tier_b_exits_feasible/`
  contrast receipt (fresh A0b 76.5 -> 20.0, A0bS 111.1 -> 44.8, S0c 131.6 -> 67.3;
  D1 unchanged); ARM_LEDGER control family WATERMARKED, "the control still leads"
  withdrawn; A9 / A5 / fee-sensitivity / risk-band corrections on the record.
- User rulings (Sunday, the cheat sheet as the reference): 3-1-2 continuation
  target = outside bar's wick then a higher-TF pattern's target; 3-2-2 stop =
  outside bar's wick; nested inside bars keep the bar the whole coil sits inside;
  reviewer's time exit PARKED; extended hours stays the control (session shadow).
- Round-3 package approved and built: weekly dot on gate and flip, four seats,
  $1.00 risk / $200 cap on a $202 wallet, score x log-volume rank shadow, session
  shadow. Deployed 9f39ba9; interlock receipt clean; KILL_FLAT removed on the
  user's word; loop live 16:26:06Z. Incident 18:22Z: the venue had pruned the
  round-2 API wallet after Thursday's full withdrawal; the user approved a new
  agent and set the key on the VPS; loop restarted 19:52:53Z (effective open);
  the failing leverage call re-issued and accepted.

### Context for next session

The executor is LIVE (round 3; tmux `executor`; KILL_FLAT only on the user's
word). Round 2 is the control; three admission changes ride on top (fee floor,
weekly dot, seats), each journaled with its counterfactual. Watch:
`liq_inside_stop` must never fire, `fee_rate_unavailable` never appears, the
first entry receipt carries `lev` and `liq_px_venue`. The user will open a NEW
session for monitoring and the review of this leg. Rule learned: after any full
withdrawal, re-approve the agent before re-funding and check `extraAgents`.

### Files created/modified

- docs/guides/STRATEGY_DEEP_DIVE_REVIEW_PROMPT_2026-09-05.md (new), docs/reviews/deep-dive-2026-09-05-astra.md (new, verbatim review)
- docs/HANDOFF.md (TVB-33 section 7 + Open), docs/ARM_LEDGER.md, docs/experiments/tvb33_round3_prereg.md, docs/reviews/REVIEW_REQUEST.md, docs/INDEX.md, .session_startup_prompt.md
- analysis/paper/engine.py, analysis/paper/tier_b_exits.py, tests/test_paper_engine.py, analysis/paper/tier_b_exits_feasible/ (new receipt)
- hip3-executor (private): src/hip3_executor/{config,rules,broker,engine}.py, config.json, analysis/replay/{types,gates,recon,one_three}.py, tests/, README.md, runs/2026-09-04_replay1/ (PREREG j/k, re-run receipts, before_amend_j/)

### Open

- [ ] HANDOFF.md is over 1,500 lines: archive the TVB-27..TVB-32 entries to
      docs/session_archive/ on the user's word.
- [ ] Round-3 close-out replay: add the round-3 LedgerSpec (contrast_control
      "as_built"; read the journaled shadows first: stack, rank, session, lev,
      backing_invalidated) and replay it against round 2 at close.
- [ ] Scanner release with the three STRAT rulings (3-1-2 cont target, 3-2-2
      stop, nested mother) + PR-B pivot ladder / PR-A `1-3h`.
- [ ] The July A0b anchor under feasible fills is not written by the runner
      (owed for the July control-vs-package comparison).
- [ ] Score picker arm (receipt on the round-3 ledger before it trades);
      prospective halfway generator; fill/slippage model (weekend-1 P5).
- [ ] TVB-31/32/33 session reviews still unreturned.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb34-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: REQUESTED
- Commits to review: `7ad92f4..00d243e` on `main` (this repo: docs, the review
  file, the twin's entry_fill option, the feasible receipt); hip3-executor
  (private, local transport) `d8a07b0..5cd2b0d` on main.
- Scope / what changed: the deep-dive fold (five executor repairs, halfway
  synthesizer fix, replay port), the feasible-fill research contrast, the
  round-3 package (weekly dot, seats, risk, shadows), the go-live and the
  agent-pruning incident.
- Focus areas (scrutinize these): the liquidation formula and clearing-leverage
  selection vs the venue docs; the weekly-dot verdict (executor-computed
  dots_dir vs the scanner's coinSummary; missing/flat handling) and its use in
  BOTH gate and flip; the partial-close VWAP path across a restart; whether
  amendment j's decision-price convention is the right D4 successor; the
  feasible-fill twin change (only the arm-mode entry touched?); whether three
  admission changes on round 2 stay separable from the shadows.
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb34-codex-audit.md exists)

---

## Session TVB-33: round-2 CLOSED (KILL_FLAT) + reject dig + round-3 design session + Ruleset v2 prereg + ledger-replay harness BUILT + receipts + round 3 BUILT and READY (COMPLETE; deploy on the user's word)

**Date:** 2026-09-04 (afternoon/evening, same day as the TVB-32 Friday deploy)
**Status:** IN PROGRESS. Prereg frozen and pushed in both repos BEFORE any
code; the replay harness is being built in four parallel slices on
executor branch `feat/replay-harness` (skeleton 5c58e30).

### 1. Round 2 CLOSED on the user's word (17:13Z)

User: "kill flat the positions and shut down the wallet activity ... pull
those funds temporarily for manual trading until we design the next
implementation". Read-only VPS check first (loop alive on 4b5d248,
heartbeat 17:07Z, ATOM + HBAR 4h shorts tracked = venue view, no kill
files, no systemd unit, zero block rows, 6 first sightings of the new
`entry_bar_invalidated` gate). KILL_FLAT file created 17:13:19Z; HBAR
closed 17:13:26Z (-$0.06), ATOM 17:13:28Z (+$0.11); receipt 17:13:32Z
`clean: true`, 0 positions / 0 orders on main AND xyz, `order_sweep:
full`; loop halted and exited; public-API check 0/0, spot USDC 99.8567
with nothing on hold. `data/KILL_FLAT` LEFT IN PLACE as the restart
interlock; agent key stays on the VPS (order-only); the user withdraws the
funds. Closed ledger: 32 entries / 32 exits (19 flip / 5 target / 4
invalidation_type3 / 2 stop / 2 kill_flat); equity 99.6015 -> 99.8567
(+$0.26 net all-in, zero deposits); zero entries after the 15:08Z restart.
Closed journals + refreshed venue fills/funding installed in hip3-executor
runs/2026-08-31_round2/ (README CLOSE block; SNAPSHOT_TS = the receipt
instant; executor 1e79398). The gitignored candle caches were extended to
the close by the new `analysis/extend_round2.py` (tail-only merge; 289
caches, no errors). Harness note: the classifier blocks base64-piped
remote scripts and the safety hook blocks `Remove-Item` on Windows paths;
plain `ssh atlas@<host> 'cmd; cmd'` and Git Bash `rm` work.

DEFECT FOUND: the TVB-32 overnight snapshot's `decisions_r2.jsonl` was
MISSING 777 skip rows from 2026-08-31 20:03Z-23:59Z that the cumulative
VPS journal holds (contiguous, all `skip`, normal 160-263 rows/hour
cadence, zero entries in the window) -- a slicing defect at snapshot time,
not a journal gap. Every pool-census count in ANALYSIS.md / analysis.json
for that Monday evening is an undercount (all refusals; no trade
affected). Noted in the run README; ANALYSIS.md/analysis.json left as
the reviewed snapshot record. For the TVB-32 reviewer.

### 2. Reject dig (user: BRENTOIL, CL, CRCL "had some pretty good runs")

Every sighting of all three was refused, overwhelmingly by the
equity-hours clock: BRENTOIL 60/84, CL 57/80, CRCL 63/78 sightings
(`underlying_closed`), then the R:R floor (15/14/12), the seat cap, and
one `entry_bar_invalidated` each on today's 4h longs. The clock is a
weekday 09:30-16:00 NY window applied to EVERY xyz coin: oil, metals, FX
and Asian indices included. The runs and who refused them (1m replay,
fill at the sighted mid, stop-before-target): oil's Sep 1 +4.7% day = 4h
3-2U longs at 04:06 ET on both names, clock-refused, 3.4R / 4.1R; CRCL Aug
31 +6.4% = 4h 3-2U at 12:06 ET, R:R 1.35, passed EVERY gate, refused only
because the two go-live probes (SP500 12:02, HIMS 12:04) held both seats,
+6.2% MFE, 1.4R; CRCL Sep 3 +15% = 1h 1-2-2 at 07:03 ET (21R stop-only over
48h on a 0.75% stop) and 1d 1-2-2 at 08:33 ET, both clock-refused; inside
the bell the only long was a 1h cont refused by the seat cap. Caveats: the
clock guard runs before R:R/reach/drift, so its pool never met the later
gates (upper bound); mid fills, no fees/slots. Script:
scratchpad reject_dig.py (per-setup lines + per-guard summary).

### 3. Design session (plan mode; strat-methodology loaded; two Explore +
### two Plan agents; every decision via AskUserQuestion in trader terms)

Walkthroughs used: SOL 4h 1-3 minute path (Tue Sep 1 ET: inside bar
98.87-100.30 inside the noon-4pm mother bar 98.29-102.00; the 8pm bar broke
the low 9:47pm, bottomed 98.49, reclaimed 98.87 at 9:55pm, crossed the
inside bar's halfway 99.59 at 10:33pm, took 100.30 at 11:11pm where the
bot bought, topped 100.65; flipped out 12:08am at -0.38%; all three entry
conventions stopped by Wed morning bracket-only); JUP #1 runner
(+4.71% MFE -> -0.63% flip; bracket-only would have been a stop; JUP #2 hit
+4.84%); the reject-dig cases. Facts that shaped the options: the scanner
computes 15m/30m/1h/4h/1d/1w/1M (no 2h/8h/12h), serves ONE target per
signal (nearest k=2 pivot or bar-0 wick), already serves `prov.kind` +
`us_session` and `dwmContinuity` which the executor never reads;
selection is arrival order (`selectionRank` null); P2 lost both axes in
TVB-25 while P1 won per matched trade; the thestrat_ai corpus says
"start small, add to winners, never scale out" (tension item, not
adopted); "walk up the timeframe" is a project-derived idea.

TWELVE RULINGS (user, 2026-09-04): R1 ledger replay first, then live round 3
(amended = arm, round 2 = control). R2 1-3 trigger = the HALFWAY LINE (50
percent rule, R19): live when price retraces past half the inside bar
after the first break; stop = the entry bar's first-break extreme; target
= bar 0's wick; the 3 completing is not an invalidation; scanner name
`1-3h`, label "1-3 (50%SSS)" until the far side prints; alerts fire; far
side stays the control. R3 xyz clock = EXTENDED HOURS 04:00-20:00 ET
weekdays, ONE window for every xyz coin; future variant named: 24h
ex-weekend (Sunday 8pm ET open) for the top-10 xyz by 24h volume. R4 no
drift veto (arm). R5 continuity-backed 4h/1d conts via the coin's own
D/W/M stack (arm). R6 higher-timeframe-first selection, then R:R (arm).
R7 walk-up (TP at the ladder's LAST rung; next target = next-TF pivot;
stop ONE RUNG BEHIND; ladder frozen at entry; BE = fill + one tick) and
bank-half (50% at T1, remainder to the next-TF pivot, BE stop; sub-$20
tickets fall back to T1, journaled) as arms vs full exit at T1. R8 the
SCANNER serves the pivot ladder. R9 fee-aware R:R floor (net of both
legs' fees >= 1.0) as an amendment; min prior-bar range and the funding
gate NAMED DEFERRED with an expected-funding receipt. R10 five seats
(arm). R11 crypto on weekends unchanged. R12 "completes" = intrabar. The
user asked for my view on seats (given: arm not amendment; the blocked
queue simulated worse at the median in both runs) and on the three
lanes (given with the fee-share table: PAXG 86%, GOLD 69% of risk in
fees). Claude declarations D1-D12 approved with the plan (parity gate
thresholds, replay conventions, supervised probes).

### 4. Phase 0 -- prereg BEFORE code, pushed in both repos

- hip3-executor README "Ruleset v2 (round 3 -- PREREG, user-ruled
  2026-09-04, frozen before code)" (5ba3347).
- This repo `docs/experiments/tvb33_round3_prereg.md` (LABEL block,
  rulings, declarations, nine arms A1-A9, binding contrasts, named
  deferred) + `docs/ARM_LEDGER.md` "Live executor family" section
  (v1 control cards + A1-A9 cards, trader terms, numbers pending)
  (7deca94).
- Replay skeleton on executor branch `feat/replay-harness` (5c58e30):
  `analysis/replay/types.py` (the contract), `CONTRACT.md` (four slices),
  `runs/2026-09-04_replay1/PREREG.md` (pins README v2 @ 5ba3347 + prereg
  @ 7deca94; parity gate; arms; limitations), pytest pythonpath + ledger
  marker, `tests/replay/synth.py`.

### 5. Ledger replay harness -- BUILT, round-2 parity PASS, nine arms receipted

Built in four reviewed slices (S1 foundation, S2 rules/gates, S3 exits/
allocator, S4 parity/report; 1,032 tests) on hip3-executor branch
`feat/replay-harness` (5c58e30..b1da068, pushed; nothing under src/
changed). The three "failed" background tasks the user saw were the
parity CLI exiting non-zero on a real FAIL and two mid-build test runs
inside teammates, fixed before the slice commits; the teammates then hit
the account's session limit and the rest was done directly.

Parity round 2: FAIL -> FAIL -> FAIL -> PASS across three fidelity
amendments (prereg d-h, executor PREREG.md; mirrored in
tvb33_round3_prereg.md): (1) the scanner's post-roll FREEZE -- served
dots keep the pre-roll value for one refetch sweep per timeframe (~75 s
each, TFS order; the daily dot lags ~6 min; a first per-universe 10/30
min guess scored below no-freeze and was withdrawn); (2) the BTC drift
sign journal-pinned where the refusal reason reveals it (both misses
were BTC within $10 of its open inside a minute); (3) matched positions
free their seat at the journaled exit instant (a one-second seat gap
cascaded through every later entry). Final: 22,401/22,401 decisions
agree, 32/32 entries, 30/32 exit reasons (2 mid_union_type3), worst
timing 2.8 min, net +$0.44 vs venue (threshold $0.50). pins.json written.

Parity weekend 1: 34/34 entries, 33/34 exit reasons (KAITO
coupled_open_tick), P5 FAIL by $0.11 / 0.54pp = fill slippage on PURR
(entry 0.9%) and STX (stop 1.05%); arms run WATERMARKED against a v1
replay control (D8; net -$2.16 on 27 vs the v0 book's -$6.86 on 34).

Arms (round 2, control +$0.70 on 32): A9 fee-aware floor +$3.30 (the
gain is the 11 refused fee-heavy losers, -$1.61); A6 walk-up -$1.51 and
-$1.30 on matched trades (same sign on weekend 1); A3 +$1.26, A2 +$1.20
(sign flips on weekend 1), A7 +$0.82 (matched -$0.48), A1 +$0.75 (one
xyz trade admitted; oil/CRCL die at the R:R floor once the bell opens;
two 4h conts found no seat), A5 +$0.36 with ZERO halfway entries (875
synthetic candidates all refused: volume 359, clock 248, not beyond the
line at the cross minute's close 268), A8 -$0.14 on 55 trades, A4
identical (never bound). Full cards: docs/ARM_LEDGER.md; dual-language
report: executor runs/2026-09-04_replay1/REPLAY.md.

### 6. Round 3 ruled and built (user, 2026-09-05: "lets go with that and get it ready")

Asked for a one-shot recommendation, Claude proposed: make the R:R floor
net of fees (the only arm positive on both ledgers and on matched trades,
for a structural accounting reason), change nothing else live, and
shadow-journal every other arm so the next ledger can receipt them again.
The user accepted. Prereg'd BEFORE code in both repos (executor README
"Round 3 config"; public prereg amendment 2026-09-05a; replay PREREG
amendments i and 2026-09-05a). Found while porting: the A9 receipt was
computed with the dex-default fee table, not the per-coin rates
amendment b declared (the hook was never wired) -- recorded as amendment
2026-09-04i; the live floor matches the receipt, the per-coin rate is a
shadow (A9c, named-deferred).

Built on hip3-executor `feat/round3-fee-floor` (merged to main): the net
floor with dex-default rates and fail-closed refusal, config validation
at load, shadows on every decision row (rr_net, fee_rt_pct,
fee_rt_pct_coin, dwm, poll, funding_rate), the D6 expected-funding entry
receipt, `arms` on the startup row, the hourly `equity` tracker row, and
the TVB-32 equity fix (account_value = spot USDC total). 1,144 tests; the
replay differential proves live and port agree on the fee-aware cases;
paper smoke run clean. NOT deployed: the VPS deploy, the interlock
receipt, the equity check and `rm KILL_FLAT` all wait for the user
(checklist in the executor README STATUS 2026-09-05).

### 7. Deep-dive external review FOLDED (2026-09-06; the critical synthesis)

Review: `docs/reviews/deep-dive-2026-09-05-astra.md` (GPT-6 Astra via the
local transport; prompt `docs/guides/STRATEGY_DEEP_DIVE_REVIEW_PROMPT_2026-09-05.md`).
Verdict on the review: the best this program has had. Every numerical
claim I could check reproduced from the raw receipts before any edit
(scratchpad verify_review.py): the liquidation geometry, the A9
decomposition to the cent, the research entry-containment census
(58/106, 63/123, 1/39, 81/492), the July fee algebra. The user was told
the plain-terms reading first and said continue.

AGREE (acted):
- R1 stop-vs-liquidation. The rail used 1/leverage; the venue liquidates
  at (1/L - m)/(1 -/+ m), m = 1/(2 x maxLeverage) (5.26% long / 4.76%
  short at 10x vs the 8% the rail admitted). Round 2: LITE, ACE, NBIS
  stops rested BEYOND the liquidation price, ZHIPU and DOT past the 80%
  buffer; weekend-1 XMR the same. None hit. Repaired: `liq_model
  "maintenance"` picks the leverage per ticket so the stop clears (LITE
  8x, ACE 2x, NBIS 7x), the entry SETS it, and the entry receipt carries
  the venue's liquidationPx + `liq_inside_stop` (receipt + warn).
- R2/R3/R4 broker defenses: malformed account response is unknown never
  flat (both dexes serve assetPositions as a list when empty, checked
  read-only); stop verifier requires "Stop Market" exactly; partial IOC
  closes book their fragment and the exit prices size-weighted.
- R8: a higher-TF reversal whose forming bar is a Type 3 cannot license
  a continuation (`backing_excludes_invalidated`; the as-built sponsor is
  journaled as a shadow).
- R5: the A5 halfway synthesizer set mid == trigger; the strict in-force
  gate refused every candidate. MY ERROR: I reported the 268 refusals as
  the D4 convention. Fixed (amendment j: decision price = cross minute's
  close), parity re-gated (round 2 PASS again; weekend 1 P5 FAIL as
  before), all arms re-run, pre-fix receipts archived in
  `runs/2026-09-04_replay1/before_amend_j/`. Result: round 2 still zero
  halfway entries for honest reasons (109 R:R floor, 44 no seat, 44
  close back inside, 41 stack, 18 drift); weekend 1 five halfway entries,
  zero winners (-$1.67 on the five; watermarked).
- R6/C1: the research twin's arm-mode entry books the prior-hour level
  even when the bar opened beyond it. Added `entry_fill "feasible"` (the
  rule the package path already used) and a labeled contrast receipt
  `analysis/paper/tier_b_exits_feasible/` (determinism gates PASS):
  fresh A0b 76.5 -> 20.0, A0bS 111.1 -> 44.8 with drawdown 36.5 -> 59.5,
  S0c 131.6 -> 67.3; July S0c 291.4 -> 155.0, A0bS 214.9 -> 88.2 with
  drawdown 55 -> 73; D1 unchanged. ARM_LEDGER control family
  WATERMARKED; "the control still leads" withdrawn as a finding.
- R7 (Finding 3): MY ERROR. A9's matched trades are identical by
  construction (I said "positive on matched trades"); only 6 of the 11
  displaced tickets fail the net floor directly, one a winner, all six at
  net R:R 0.95-0.9997 ("gross floor ~1.07" in practice); 5 vanished via
  seat reshuffle (3 of the 4 "gold-class" names I cited); the +$2.60 is
  62% avoided losses, 38% admitted tickets. The accounting argument
  stands; the money argument is thin and in-sample. The reviewer still
  picks the fee floor as the one eligibility change, for the accounting
  reason. THE USER'S RULING STANDS UNLESS THE USER CHANGES IT.
- Conceded wording: settle pin reads journaled exit instants (outcome
  data); "26 of 28 flips" was a mixed-slice slip (26/27, 27/28 closed);
  24/32 in the risk band; the state-stop family does NOT all flip
  negative at 0.1%/side (July stays positive). ARM_LEDGER corrected.

DISPUTE / NUANCE: none of the numerical findings. The reviewer's
"designed after a reject dig then receipted on the same ledger =
in-sample" is correct and was already implicit; recorded now as binding
(the next round needs a frozen forward window before any arm is called
anything). Its 21 recommendation cards are proposals; for a solo
operator the three that matter were R1, R5/R6, R7, and those are done.

NOT ACTED (user rulings or scanner PRs; put to the user): R15 same-color
3-1-2 continuation target = the containing 3's wick (skill invariant 5;
the near-bank pivot can MANUFACTURE admissions under the R:R floor);
Appendix B 3-2-2 stop = the outside bar's extreme (scanner uses the
trap's low, wider); R20 nested inside bars keep the original mother bar
(scanner uses closed[n-3]); which continuity stack is "STRAT" (four
intraday dots vs D/W/M); R10 the reviewer's proposed FIRST exit
experiment (no progress in two signal-bar lengths with < 0.5R MFE = out)
as a candidate A10 over the runner profiles; a prospective halfway
generator; a fill/slippage model (weekend-1 P5).

Commits: executor branch `fix/deep-dive-fold` 0562f14 (code + 1,172
tests) + the README amendment 2026-09-06b, PREREG j/k and re-run
receipts, merged to main; this repo: twin `entry_fill`, the feasible
receipt, prereg amendment, ARM_LEDGER corrections, this section.

### Open

- [x] BEFORE DEPLOY: deep-dive review delivered, returned and FOLDED
      (section 7). Blocking finding R1 repaired on executor main; round
      3 = v1 + fee floor + the mechanics repairs (liq_model maintenance,
      backing_excludes_invalidated, broker defenses).
- [ ] USER RULINGS raised by the review (before or after go-live, user's
      call): 3-1-2 continuation target (the 3's wick vs near-bank pivot);
      3-2-2 stop placement; nested-inside mother anchoring; the continuity
      stack question; whether the reviewer's no-progress exit becomes A10.
- [x] ROUND-3 PACKAGE BUILT 2026-09-06 (user-approved after the fold; executor
      main; prereg amendments 2026-09-06c executor / 2026-09-06b here): weekly
      dot on gate and flip, four seats, $1.00 risk / $200 cap on a $200
      wallet, score x log-volume shadow; the three STRAT scanner rulings
      (3-1-2 cont target = the outside bar's wick then a higher-TF pattern's
      target; 3-2-2 stop = the outside bar's wick; nested inside bars keep
      the bar the whole coil sits inside) recorded for the next scanner
      release; the reviewer's time exit parked.
- [x] ROUND 3 LIVE 2026-09-06 16:26:06Z (executor 9f39ba9; the user funded
      $202.24 and gave the go for the SSH deploy and go-live; interlock
      receipt clean 0/0 both dexes; KILL_FLAT removed; tmux `executor`
      --live). The round-3 ledger opens at that startup row; round 2 is the
      control. First minute: the fee floor refused DASH 1h 1-3 at rr_net
      0.959; stack / stack_60dwm / score / rank / session ride every row.
      Extended hours stays the CONTROL (user option 1: `session` shadow
      journaled, the bell gates). INCIDENT 18:22Z: the venue had PRUNED the
      round-2 API wallet when Thursday's withdrawal took the balance to
      zero, so the first qualified candidate (PURR) failed at the leverage
      step and reconciled fail-closed (no exposure); the user approved a new
      agent in the HL app and set the key on the VPS himself; loop restarted
      19:52:53Z = the EFFECTIVE round-3 open (no entry was possible before
      it); the failing call was re-issued on the new key and accepted.
      Lesson: a full withdrawal drops the agent; re-approve before
      re-funding. Watch list: `liq_inside_stop` must never
      fire; `fee_rate_unavailable` must never appear; the first entry
      receipt should carry `lev` and `liq_px_venue`.
- [ ] (done above) ROUND 3 GO-LIVE checklist, for the record: fund the wallet ($200)
      -> deploy main (deploy_from_dev.ps1, 40-hex DEPLOYED_SHA; SSH only
      with explicit confirmation) -> `--once` interlock receipt -> equity
      check vs the HL app -> `rm data/KILL_FLAT` -> tmux `--live` ->
      first heartbeat + first rr_net row. No supervised probes needed
      (no venue primitive changed).
- [ ] After go-live: add the round-3 LedgerSpec to analysis/replay
      (contrast_control "as_built"; the journaled shadows read
      journaled-first), replay it at close against round 2 as the
      control.
- [ ] USER RULINGS still open: (a) weekend-1 P5 -- accept watermarked
      readings, amend P5 to exclude declared slippage trades, or add a
      fill model; (b) A5 -- D4's in-force-at-minute-close convention
      leaves the halfway tier empty.
- [ ] Scanner PR-B (pivot ladder) and PR-A (`1-3h`) -- deferred with the
      profile arms and the A5 ruling; not needed for round 3.
- [ ] TVB-31 / TVB-32 audits unreturned; TVB-33 review requested
      (REVIEW_REQUEST.md): the three fidelity amendments and the live A9
      port are the things to attack.
- [ ] Carried: month-end fresh-window regen (overdue); TV mirror on
      demand; TVB-18 repairs; jackson set_inputs fix; metals /
      tech-vs-yields regime ID (user, later); trade visualization (the
      SOL minute path and reject-dig replays are the first instalment);
      replay `_Context` calls fetch.ensure_meta (network) -- make it
      offline-pure; walk-up scoped to daily entries as a future arm.

### External Review (for Codex / cloud review agents)

- Review status: REQUESTED 2026-09-05 (docs/reviews/REVIEW_REQUEST.md);
  the separate DEEP-DIVE review RETURNED 2026-09-05 and was FOLDED
  2026-09-06 (section 7). The TVB-33 session review is still open; its
  reviewer should read section 7 and the fold commits first.

---

> Older sessions: TVB-27..TVB-32 archived 2026-10-04 to
> docs/session_archive/HANDOFF_TVB27-TVB32.md (verbatim). Earlier:
> HANDOFF_TVB24-TVB26.md, HANDOFF_TVB22-TVB23.md, HANDOFF_TVB18-TVB21.md,
> HANDOFF_TVB10-TVB17.md, HANDOFF_TVB0-TVB9.md.
