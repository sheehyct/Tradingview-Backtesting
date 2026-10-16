# HANDOFF -- tradingview-backtesting

> Newest session entry at the TOP. Keep under 1500 lines; archive older entries to
> `docs/session_archive/` when it grows past that.

---

## Maintenance 2026-10-16 (not a TVB session): Claude Code hooks for cloud sessions (COMPLETE)

**Date:** 2026-10-16
**Status:** COMPLETE on branch chore/cloud-hooks-2026-10-16 (owner-approved). Takes
effect for cloud sessions once merged to main, since cloud sessions clone main. No
research, analysis, Pine or test code changed; TVB numbering is untouched.

### Why

The owner wants the non-backtest TVB work (Python analysis, tests, docs, reviews)
to be able to run as Claude Code CLOUD sessions (claude.ai/code, phone Code tab,
`claude --cloud`), with backtests staying on the workstation. Locally this
workspace's hooks live in the UNTRACKED `.claude/settings.local.json` with `C:/`
paths, which cloud sessions never read, so a cloud clone ran with no safety
guard, no lint and no test gate.

### What changed

- `.claude/settings.json`: hooks added that run ONLY when `CLAUDE_CODE_REMOTE=true`
  (cloud): SessionStart prints `.claude/cloud-context.md`; PreToolUse safety
  guard, trading and global scopes (two separate entries, each needs its own
  stdin); PostToolUse ruff lint; Stop test gate. Existing keys (MCP servers,
  the ui_evaluate deny rule, additionalDirectories) are unchanged.
- NEW `.claude/hooks/safety_guard.py` and `.claude/hooks/post_edit_lint.py`:
  byte-identical copies of the spine's scripts in `C:\Strat_Trading_Bot\.claude\hooks\`
  as of 2026-10-16. If the spine's copies change, copy them here again.
- NEW `.claude/hooks/stop_test_gate_cloud.sh`: the tvb branch of the spine's
  stop_test_gate.sh (`uv run pytest tests/ -q`, exit 2 on failure,
  SKIP_TEST_GATE=1 bypass) without its directory-name detection, because a cloud
  clone is named `Tradingview-Backtesting` and the spine script's lowercase
  case-match would skip it silently. Skips with a message if uv is missing.
- NEW `.claude/cloud-context.md`: the spine's safety rules and communication
  standards, this repo's session-start order, the PUBLIC-repo warning, and what
  a cloud session cannot do (no TradingView Desktop or tradingview MCP: no
  strategy() runs, chart reads or Pine compile checks; no .env or keys; no live
  accounts).

### Workstation behavior: unchanged

Every new hook is a no-op when `CLAUDE_CODE_REMOTE` is unset. The workstation
still gets the guard, lint and test gate from the untracked
`.claude/settings.local.json` (pointing at `C:\Strat_Trading_Bot\.claude\hooks\`),
exactly as before. If those local hooks are ever moved into settings.json, delete
them from settings.local.json in the same step or they will run twice.

### Verified (2026-10-16)

- Workstation, Git Bash: 5/5 harness checks, every new hook silent and exit 0.
- Linux (`sh`): guard blocks prod Tradier and `rm -rf /` and allows pytest; lint
  silent without ruff; test gate exits 2 on a failing run, 0 on a passing run,
  0 with SKIP_TEST_GATE=1, and skips with a message without uv; SessionStart
  prints the context (10/10 across runs).
- The real suite on Linux (Ubuntu 24.04, fresh clone of main da7f4c2,
  `uv run pytest tests/ -q`): 372 passed, 2 skipped in 9.2 s, so the cloud gate
  does not trap sessions on a Windows-only test.

---

## Session TVB-39: the trade viewer (every row on its own candles, locally) and the lead's five candidates run as prereg amendment A2 (COMPLETE)

**Date:** 2026-10-12
**Status:** COMPLETE -- two pieces on the owner's word of 2026-10-12: "You may run your 'would
test next'", and a request to start implementing a local chart tool so the rows can be checked
visually without TradingView ("visually verifying via TradingView is one of the most time
consuming tasks, almost impossible to accurately do ... the numbers were there and seemed right
until visually verified, which showed inaccuracies"), styled like the owner's screenshot (grey
context candles, the trade's candles coloured, opened / closed lines, a strip of trade cards,
1H / 1D / 1W / 1M toggles). Both delivered, pushed. The owner began their own pass the same
evening on the viewer (two BTC trades walked, section below): three viewer additions and one
viewer bug fix came out of it, plus one STRAT STOP-and-ASK question (the with-trend inside
break's T1) that is OPEN, and two direction signals from the owner recorded below (the
daily-close exit is likely to be retired; higher-timeframe inside bars are the hazard the domino
test was meant to answer). Nothing is promoted; nothing is read into the hierarchy rulings.

### What was accomplished

- **The trade viewer** (`analysis/domino/trade_viewer.py` + `analysis/domino/viewer/`): a local
  page served on localhost that draws the management book's recorded rows on the census's raw
  candles. It re-runs NO trade logic: the entry day, targets, touch days, exit day and every
  book's fill come off `manage_trades.csv.gz` as the engine wrote them, so a chart that
  disagrees with a row is evidence against the engine. One coin at a time or every trade
  entered on one day across coins; 1H / 1D / 1W / 1M (weeks and months bucketed by the census's
  calendar rules, tested against `census.week_start` / `month_start` through node); candles not
  in a trade grey, the setup bar amber, the bar before it dark amber, the trade's candles green /
  red by close; lines for the entry level, the exit close, T1 / T2 / T3 with sources, one R, the
  setup-bar stop, the measured move; markers on the first bar (hour, on the hourly view) that
  touched each price; the exit day's test spelled out (close against the day's open and the
  week's open, with colours); every book's fill; the two A2 exits (under water on the daily,
  the hourly clock on the hourly view); filters (unit timeframe, kind, side, liquid, has T1),
  book and equal-size selectors for the printed P/L; arrow keys; bookmarkable addresses
  (`#coin=BTC&date=2025-06-17&tf=D&dir=down&view=1D`, the receipt's worked example). On the
  owner's first pass (BTC 2026-03-27 weekly short: "we hit T1, no exit") three additions and
  one fix, same day: the book box now drives the chart (candles, closed line and out arrow at
  the selected book's own settle day and fill, read off the row; the headline clock kept as a
  small square); every timeframe that broke the same day is drawn with the gap band and a
  "domino" label on a converged stack (the chart's calendar level checked equal to every row's
  recorded level, all 179,498 units); a magnet ray tool (Draw / R, snaps to the bar's OHLC on
  the active view, persists across timeframes per coin); and the misplaced "data ends" marker
  (the A2 markers had split the exit arrow's `if` from its `else`) fixed. `serve` takes
  `--host` and `--no-open` for the owner's laptop over SSH / Tailscale. Hourly
  candles fetched for all 292 coins (the venue serves ~208 days) into the census cache, stamped.
  Recipe in the receipt's viewer section: `hourly --as-of ... all` (once), `build --as-of ...`,
  `serve`. The data folder and the vendored chart library are gitignored and regenerable.
- **Prereg amendment A2, declared before code (f505f9d):** the five candidates restated in
  trader terms, each one change on the same trades, with readings R1-R5 and vectors v16-v19
  written first. One sentence was corrected while writing v17, labelled in the prereg: a target
  on the trade's side cannot be touched before the level, so the hourly ordering difference is
  on the EXIT day (the daily bar fills any touch that day, the hourly clock only up to the exit
  hour).
- **Engine (`manage.py`):** the under-water exit recorded on the same walk (`exit_u`, books
  C_u / A_u / D_u); the hourly clock (`walk_hourly`: entry hour = first hour reaching L; exit =
  first hour closing against its own open AND the day's open; cap = the last hour of day 20;
  censored when the hours end; books C_h / A_h / D_h) on the hourly-window subset; book E and
  the fees as arithmetic on the recorded columns; the week's side as a split of every book.
  Hourly helpers (`fetch_hourly`, `cached_hourly`, `normalize_hourly`, `HOUR`) live in
  `census.py`. `candidates()` + `table_candidates()`; `manage.json` carries a `candidates`
  block; the CSV carries the new columns. Offline rerun as before (`--as-of 2026-10-10`, ~10
  min with the hourly). Headline numbers did not move (same rows, same walk; the hourly and
  under-water columns are additions).
- **Receipt** (`MANAGE_RECEIPT.md`): a viewer section and an A2 section (what each candidate
  did, in trader terms, against its declared reading). **Ledger** card extended. **Page**
  republished (version 5) with a candidates section. 23 manage vectors + 7 A2 vectors + 4
  viewer tests; full suite green.

### The five, against their declared readings (plain daily, the book cohort)

- **R1 the week's side at entry: NOT a general condition.** With beats against on the reversal,
  the continuation and the outside break (reversal C +0.28 with / +0.13 against; continuation
  C -0.20 / -0.53), but the inside break pays MORE against the week (A +0.18 / C +0.16 / D +0.38
  against; -0.07 / -0.13 / +0.16 with) and reaches T1 nearly as often. The declared rule said
  one reversal of the split means it is not a condition. An inside-bar break against the week is
  a counter-trend break with the week's open ahead as a level: a pattern-specific read.
- **R2 the hourly clock: a different trade, not a better one.** On ~38k trades inside the
  hourly window: held 9-11 hours against 48-72; every trade exits inside the cap; losers shrink
  to less than half (-1.5..-1.9 against -3.8..-4.9); T1 before the exit falls by a third to a
  half. Net paired: C_h - C reversal -0.14 [-0.28, +0.01], continuation 0.00, inside +0.21
  [+0.04, +0.37], outside -0.27 [-0.59, +0.05]; A and D within a tenth. The declared
  expectations (sooner, smaller losers, fewer targets) all held; no sign was predicted.
- **R3 half at T1: holds.** E between A and C on every kind (reversal -0.05 / +0.09 / +0.22).
- **R4 fees: three lines survive.** Two taker fills cost 0.077-0.082 per trade; net of that,
  intervals clear of zero: reversal C +0.14 [+0.02, +0.27]; inside D +0.16 [+0.08, +0.23] and
  D5 +0.16 [+0.09, +0.24]. Everything else flat net; the reference -0.35..-0.92 net.
- **R5 under water: the lead was wrong.** The lead called C_u < C (holds longer, loses more).
  Holding time is the same (median 2-4 days), the tail a little fatter (44-57% past one R
  against 42-54%), and the exit-only book loses LESS or the same: C_u - C +0.20 [+0.09, +0.32]
  on the continuation, +0.04 / +0.04 / +0.23 elsewhere; A slips a few hundredths; D unchanged.
  On the continuation a red candle above the entry is not evidence against the trade.

### The owner's first pass on the viewer (same evening; two BTC trades)

**Trade 1, BTC 2026-03-27 weekly reversal short, "we hit T1, no exit; a second trip through
T1, no exit; hard to tell which level is the domino level".** The row was right; the viewer was
the problem. The book box was on C (exit only, no target by rule) and the "Position closed"
line was hard-wired to the headline exit whatever the box said; the trade's only level drawn
was its own weekly trigger, and "spread D+W" (the daily trigger broke the same day more than 1%
away) was printed as a chip, not drawn. Fixed the same evening (7f3fc88): the book box now
drives the chart (candles to the selected book's own settle day, the closed line at that
book's fill read off the row's return, the out arrow on the bar that touched the target when
the book took one, the headline clock kept as a small square); every timeframe the row says
broke that day is drawn, with a stack line in the details (each trigger's price, the gap, the
census band) and a "domino" label on a converged stack; the chart's previous-complete-bar
level was checked equal to the recorded entry level on all 179,498 rows (no mismatch); a magnet
ray tool (the owner's TradingView habit: a one-pixel blue line at 70% opacity snapped to the
bar's open / high / low / close, kept across the timeframe toggles per coin, moved by clicking
near it on a faster view); `&book=` in the address. One viewer bug found on the owner's
screenshot: the A2 markers had been spliced between the exit arrow's `if` and its `else`, so a
"data ends" square printed on every exited trade. Also `serve --host / --no-open` (ed08ae5) so
the owner can browse the viewer from their laptop over an SSH port forward or the tailnet.

**Trade 2, BTC 2026-03-25 daily inside break long, -6.99% in two days, "a 2D week and an
inside month, a recipe for disaster, yet it hit its daily target, and a weekly target on the
upside on a 2D week?"** Checked against the candles:

- The week was NOT 2D at entry: through 03-24 the week of 03-23 ran 67,404-71,785 inside the
  prior week's 67,313-75,972, with price above the week's open at 67,831 (the row's "week
  with"). It went 2D on 03-27, the exit day. The 2D week is hindsight.
- The month was inside (March 65,000-75,972 inside February's 60,000-79,417). The engine reads
  neither the month nor the week's bar type; it takes every daily break by design, and the
  only week read is its colour at entry (A2.1).
- T1 75,972 [W] is last week's high, the first unbroken weekly level above the entry: a level
  from the ladder, not the week's direction.
- The owner's "daily target" at 71,785 is the mother bar's high (03-23, a 2U). It was hit on
  the entry day (high 72,034); book A would have left at +0.56%. **Code-versus-skill drift,
  STOP-and-ASK raised, OPEN:** the prereg's definition says a with-trend inside break has no
  magnitude of its own and takes the first weekly / monthly rung (`anchor = ladder`); the
  strat-methodology skill's rulings R14 / R18 say unfilled structure containing the trigger is
  a real structural magnitude, and the 2U mother bar's far side contains this trigger. The
  owner's ruling decides; any change is prereg amendment A3 BEFORE code (rerun ~10 min). The
  question put to the owner: "Mother bar's far side as T1 for the with-trend inside break:
  amend?" Not answered this session.
- Why -6.99%: 03-26 closed red on the day but above the week's open, so the two-test exit did
  not fire; 03-27 closed below both, out at 66,396. The week-colour test let it ride through a
  3.6% red day; the setup-bar stop (68,904, the inside bar's low) would have cost 3.48%.
- Feed note: the venue API prints the inside bar's high at 71,385, TradingView at 71,387.

**The owner's closing words, as direction (not rulings):** the trade is "the danger of trading
lower timeframes when you have higher timeframes as inside bars", which is "why we tried to go
with the domino test" (the coincident-level event, TVB-37); "I think the daily exit close also
is going to be thrown out, the amount of trades this affects is pretty ridiculous"; more trade
reviews to come ("it does take time"); "we are making progress ... still some bugs to work
out". The owner's first pass is BEGUN, not finished.

### What the lead would say next (not done; the owner decides)

- The with-trend inside break's T1 is the first amendment candidate (A3): the mother bar's far
  side per the skill, against the prereg's ladder. The viewer should draw the mother bar's far
  side on every inside break so the owner can see the skill's reading trade by trade before
  ruling.
- If the daily-close exit is retired, the replacements are already measured on the same rows:
  under water (A2.5, loses less or the same), the hourly clock (A2.2, a different trade, flat
  net), the own-bar clock (fork 2, holds longer and loses more), the chance book's setup-bar
  stop (the reference). The owner picks; prereg before any rerun; no pick-the-winner.
- The owner's hazard (higher-timeframe inside bars around a lower-timeframe entry) is a
  context split the rows can already carry: the week's and month's bar type at entry (inside /
  2 with / 2 against / 3) as a declared split of every book, like A2.1 did for the week's
  colour. A one-line amendment if the owner wants it.
- The headline's "against" is the weaker reading on the continuation (A2.5); the week's side
  belongs to the reversal and the continuation (A2.1).

### Files created/modified

- New: `analysis/domino/trade_viewer.py`, `analysis/domino/viewer/{index.html,app.js}`,
  `tests/test_domino_viewer.py`, `tests/test_domino_manage_a2.py`.
- Modified: `analysis/domino/{manage.py,census.py,chart_page.py,MANAGE_RECEIPT.md}`,
  `results/{manage.json,manage_tables.md}` (+ the gitignored CSV / log / viewer data),
  `docs/experiments/tvb37_management_book_prereg.md` (A2), `docs/ARM_LEDGER.md`, `.gitignore`,
  `docs/reviews/REVIEW_REQUEST.md`, `.session_startup_prompt.md`, this file.
- Commits: dbeaffe (viewer), f505f9d (A2 prereg), 340c86e (A2 build), ed08ae5 (serve flags),
  7f3fc88 (viewer: book box, same-day triggers, ray tool, marker fix), then the close-out.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb39-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: REQUESTED
- Commits to review: `4dc5f6b..30391fb` on `main` (4dc5f6b is the pre-session sha; the range
  is dbeaffe, f505f9d, 340c86e, ed08ae5, 7f3fc88, 30391fb close-out; the sha-pin commit after
  it is docs only). Sanity-check: `git diff --name-status 4dc5f6b..30391fb` lists every file
  above (verified at pin time: 16 source / doc files plus the gitignore).
- Scope / what changed: the trade viewer (a static page + a build / hourly / serve CLI that
  draws recorded rows on cached candles and claims to re-run no trade logic) and prereg
  amendment A2 in `manage.py` / `census.py` (the under-water exit on the shared walk, the
  hourly clock on the hourly window, book E and fees as arithmetic, the week's side as a
  split, `candidates()` and its tables / page section).
- Focus areas (scrutinize these): `walk_hourly` (entry hour = first hour reaching L, exit =
  first hour closing against its own open AND the day's open, cap = the last hour of day 20,
  censoring when the hours end; the ordering claim that a target cannot be touched before
  the entry hour and the exit-day difference); `exit_u` sharing the headline `walk()` without
  changing it (headline numbers byte-identical: 179,498 units, same tables); book E and the fee
  arithmetic against the prereg's A2.3 / A2.4 definitions; the viewer's calendar bucketing
  (`weekStart` / `monthStart` against `census.week_start` / `month_start`), its `settle()`
  (the fill = level moved by the recorded return; is that always the engine's own price?),
  `stackLevels()` (previous complete bar's extreme per stack timeframe; checked equal to every
  row's `level` for its own timeframe) and the claim of re-running no trade logic; the "data
  ends" marker fix.
- Reviewed by: pending
- Findings: {blank until docs/reviews/tvb39-codex-audit.md exists}

### Open

- [ ] The owner's own pass over the management book on the viewer (BEGUN 2026-10-12 evening,
      two BTC trades; continues) before anything is read into the hierarchy rulings.
- [ ] STOP-and-ASK, open: the with-trend inside break's T1 (the mother bar's far side per
      skill R14 / R18, against the prereg's weekly / monthly ladder). The owner rules; prereg
      amendment A3 BEFORE code; rerun ~10 min.
- [ ] The owner's signal that the daily-close exit "is going to be thrown out": a declared
      replacement (prereg) before any rerun. Already measured on the same rows: under water
      (A2.5), the hourly clock (A2.2), the own-bar clock (fork 2), the setup-bar stop
      (reference).
- [ ] Viewer: draw the mother bar's far side on every inside break; optionally the week's and
      month's bar type at entry as chips (the owner's hazard).
- [ ] Codex review of `4dc5f6b..HEAD` (block above): REQUESTED at session end.
- [ ] The hierarchy rulings the owner deferred (stop owner in a stack, continuation ranking,
      seat competition, which higher-timeframe event ends a trade).
- [x] HANDOFF is over the 1,500-line limit (2,100+; TVB-33..34 are the next archive
      candidates): archiving asks the owner. CLOSED 2026-10-14 (after the TVB-39
      close-out, on the owner's word): TVB-33..35 archived verbatim to
      docs/session_archive/HANDOFF_TVB33-TVB35.md (TVB-33..34 alone left ~1,640
      lines; the three make the round-3 arc); HANDOFF now ~1,420 lines.
- [ ] Executor repairs owed before any real-money restart (TVB-31..35 syntheses); fresh
      wallet; scanner STRAT rulings; the carried list in the TVB-37 entry.

---

## Session TVB-38: the Codex backlog folded, then product 3 -- the STRAT-management book (no stop, a close exit, a ladder of targets) built and receipted (COMPLETE)

**Date:** 2026-10-11
**Status:** COMPLETE -- two pieces of work. First, the six-audit Codex backlog the owner ran
overnight (TVB-31..35 and the TVB-37 close-out) was folded in one commit (5e6c59a: syntheses in
each entry, the book's drawdown column and the regime labeler's look-ahead fixed here, the
executor findings recorded for the private repo; see the TVB-37 close-out synthesis and the
archived entries). Second, product 3 of the TVB-37 data redirect: the owner ruled both forks
run for the data, agreed the headline combination, said "run it as is" and that the numbers
will be taken with a grain of salt until they can sit down with the charts; the prereg and the
ledger card went in before code (caaba12), the engine was built on the chance units with 14 hand
vectors first, run offline on the 2026-10-10 snapshot, receipted, drawn on the private page and
sent to Codex. Nothing is promoted.

### What was accomplished

- **Backlog fold (item 0, morning):** `docs/reviews/tvb31..35-codex-audit.md` and
  `tvb37-close-codex-audit.md` read, synthesised (agree / dispute / act) into their HANDOFF
  entries, fixed where the code lives here (book drawdown from zero, 110 cells; regime receipt
  labelled on completed 60m bars only, 12 of 84 composites moved, the old positive macro cell
  now negative; receipt sentences corrected; strict JSON; `--as-of` offline reruns), statuses
  flipped, pushed. The executor repairs owed before any real-money restart are listed in the
  TVB-31..35 syntheses (headline: malformed inner position rows prove flat; partial close during
  protection loss unretryable; unbounded book_top read before the safety loop; replay parity
  not pinned to roll_freeze_ms; builder fee double-counted; decoupled flip counterfactual
  unreachable; backing_invalidated never journaled; NaN size passes stop coverage).
- **Owner rulings, 2026-10-11:** both forks of product 3 run as declared variants ("I believe it
  involved both forks for the data"; "try both and see the results"); headline = the
  continuation's T1 at the next unbroken higher level + the daily close with the week's colour
  as the exit clock for every trade ("Yes we may proceed with this"); the lead's seven declared
  calls stood (against = the candle's colour; equality not against; the entry day can exit; the
  ladder is week and month levels only, fixed at entry; a zero-magnitude reversal has no T1; the
  monthly own-bar clock has no higher confirmation; cap 20 daily bars); book D (one R or the
  exit, the lead's addition) kept. "We can run it as is ... we'll take them with a grain of salt
  for now until I can kind of sit down and visualize some of it and break down the numbers
  myself."
- **Prereg before code:** `docs/experiments/tvb37_management_book_prereg.md` (17 definitions,
  hypotheses H2 / H3 with direction, 15 hand vectors, bug tests) and the ARM_LEDGER card
  (trader restatement, the owner's go), commit caaba12.
- **`census.day_events` extended** to return the bar before the setup bar with its prices (the
  fourth element of each setups tuple); `_context` carries `ref`; the census gained `--as-of`
  and `--out` for offline reruns (the cache helpers moved into census, re-exported by chance).
  The census was rerun offline before and after the extension: `census.json` byte-identical,
  and the offline baseline's `splits` equal the committed live run's.
- **`analysis/domino/manage.py`** (the engine): ladder, structural T1 per the resource's
  reversal anatomy (confirmed in the corpus: "the target is always the high or low of the bar
  prior to the trigger bar"; the 3-2 and the with-trend 2-2 "take their target from the higher
  timeframe"), the measured move as the two-bar range, one walk per unit recording target
  touches, travel and both exit clocks, settlement at either cap, five books on the same rows,
  paired differences, reach / death / tail tables, both fork tables, hypothesis read-out,
  splits. `tests/test_domino_manage.py`: 14 vectors before the data run (the 15 declared;
  v13 and v14 shared a vector with v2 / v3), 18 after the audit fold (decimal touches long and
  short, the month veto alone, each equality test alone, the counters). Suite 361 passed, 2
  skipped after the fold.
- **Run and reconciliation:** 179,498 units (product 2's 179,913 less 415 daily units with no
  week open to test against); one BTC short reconciled by hand against the raw candles; the
  rerun that added two columns moved no number. Receipt `analysis/domino/MANAGE_RECEIPT.md`;
  tables `results/manage_tables.md`; `results/manage.json`.
- **The private chart page** gained four sections (reach bars, five-book curves for the three
  plain daily patterns, the hypothesis table, the management book table) and was republished
  to the same link (version 3; the link stays in the lead's memory only).

### The finding (trader terms; the receipt has every table)

Taking the stop away turns every plain daily pattern from a loser into roughly flat: the chance
book lost -0.27 to -0.84 per trade, the management books sit between -0.24 and +0.24, and on the
same trades the stop swap alone (book D minus the chance book, paired) is worth +0.45 to +0.93
with intervals clear of zero. H2 (the owner's suspect) holds in sign on all four patterns. It
is not a money machine: the median trade still loses in every book that holds past T1, two
trades in three close red on the exit-only book, and the averages are of the same order as a
round-trip taker fee. The close exit fires inside a median two to three days and is itself an
early exit: of the trades it closes before one R, 45-61% touch one R later inside the cap,
against the stop's 24-48% on a 20-day follow-up; on the like-for-like read the audit forced
(book D5, the same one-R target and the same five-bar window, T1 units only) the close exit
throws away FEWER target-bound trades than the stop did (16-32% against 24-48%), so H3, the
lead's counter, does not hold; the stop swap's lift is the same on the five-bar horizon (D5
minus reference +0.48 to +0.92). The tail is the price: 32-55%
of trades travel more than one R against before the exit, 6-20% more than two R, worst single
trades -88% to -143% (shorts on doublings), unsized. T1 before the exit: reversal 63.8% (its T1
is the bar before the pattern, a median 2.6% away), inside 53.6%, outside 38.7%, continuation
36.2% (T1 a median 9.8% away, beyond its own R: the one pattern management does not get into the
black). The hammer flag adds little on top of its already-flat cells; the stacked continuation
stays the one A+ in the black under every rule; shared-open stacks lose under every book. Weekly
and monthly units traded on the daily clock close in 1-5 days and lose to the chance book's
five-bar hold where that hold won; the own-bar clock holds 13-27 days and loses more on ten of
sixteen weekly cells. Fork 1: the measured move and the level sit at the same distance on plain
continuations (A +0.02 against -0.23); on stacked cells the level is next door and the measured
move is the real target. An entry-time split worth the owner's eye: a continuation entered
against the week reaches T1 14.7% of the time against 39.4% with it (reversal 50.4% against
72.3%).

### What the lead would test next (not done; the owner decides)

- The week's side at entry as a declared entry-time condition (the one split with a large gap
  that a trader can see at the break); the hourly as the exit clock (the daily close is blunt);
  half at T1 and the rest on the exit (the ATLAS ladder shape); fees at the venue's taker rate
  on every book; the exit test on the close against the ENTRY price (under water) as the
  declared alternative reading of "against".
- The owner's own pass over the charts and the per-trade rows (`manage_trades.csv.gz` has every
  target, touch day, exit day and fill) before any of the hierarchy rulings are read from these
  tables.

### Files created/modified

- New: `analysis/domino/manage.py`, `analysis/domino/MANAGE_RECEIPT.md`,
  `analysis/domino/results/{manage.json,manage_tables.md}`,
  `docs/experiments/tvb37_management_book_prereg.md`, `tests/test_domino_manage.py`,
  `docs/reviews/tvb31..35-codex-audit.md`, `docs/reviews/tvb37-close-codex-audit.md`.
- Modified: `analysis/domino/census.py` (ref bar, `--as-of`, `--out`, cache helpers),
  `analysis/domino/chance.py` (imports; `_refbar` unpacking), `analysis/domino/chart_page.py`
  (management sections), `analysis/domino/book.py` (drawdown, strict JSON, `--as-of`, fold),
  `analysis/regime/receipt.py` and `scripts/tvb35_regime_harvest.mjs` (fold),
  `tests/test_domino_book_audit.py`, `docs/ARM_LEDGER.md` (product 3 card with numbers),
  `docs/HANDOFF.md`, `docs/reviews/REVIEW_REQUEST.md`, `.session_startup_prompt.md`,
  `.gitignore`, `CLAUDE.md` (owner's notes section, a0c52df).
- Gitignored, regenerable: `results/manage_trades.csv.gz`, `results/manage_run.log`, the page.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb38-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: ADDRESSED (returned the same session via `codex exec`, folded the same day;
  the fold commit itself is unreviewed and carries into the next request)
- Commits to review: `a0c52df..058395f` on `main` (the prereg commit caaba12 and the product-3
  build; the backlog fold 5e6c59a is the fold of six returned audits and needs no second audit
  unless the reviewer disputes a synthesis)
- Scope / what changed: the management-book prereg, the `day_events` extension, the engine,
  its tests, the receipt, the ledger card, the chart-page sections
- Focus areas (scrutinize these): look-ahead in the ladder and the exit (every level and both
  exit tests must be knowable at the instant they are used); the T1 rules against the skill
  and the resource; target-before-close ordering inside a day and on the entry day; the
  same-rows claim for the five books; the paired-difference interval; the fork-2 settlement
  at the long cap; censoring; the receipt's sentences against the tables; the page's data
  against manage.json; hygiene
- Reviewed by: local Codex CLI 0.162.1 (`codex exec -s read-only`, unelevated sandbox), same
  session, before the fold
- Findings: `docs/reviews/tvb38-codex-audit.md` -- NEEDS-CHANGES, 8 findings (F1 F2 HIGH,
  F3-F7 MEDIUM, F8 LOW); "what I checked and found sound" covers the T1 rules, the ladder
  look-ahead, the intraday ordering, the same-rows join (179,498 matches, no mismatches), the
  aggregation invariants, settlement and clocks, the tail arithmetic, the page and hygiene

### Critical synthesis of the audit (where the session agrees, disputes, acts)

All eight accepted; none disputed. Folded the same afternoon (prereg amendment A1, the fold
commit after 058395f); the engine rerun and every moved number listed in the receipt.

- **F1 HIGH, decimal targets -- AGREE, fixed.** One R and the measured move were built as
  binary floats (`level + r`), so a target at a printed price could sit a hair beyond it and
  an exact touch could miss; the reviewer reproduced it (L 0.1, stop 0.09, high 0.11: the
  chance book filled, book D did not). Both projections are now decimals, as the chance walker
  builds its own; exact-touch vectors long and short added. The anchor and ladder targets were
  raw printed prices and were never affected.
- **What moved in the rerun:** book D's averages by less than a hundredth of a point and its
  target-hit shares by less than 0.01 pp (F1: the exact-touch misses were rare); the "median
  days" column (F4: A 0-1 days, D 1, the reference 0-2, not the 2-3 shown before); the 20-day
  follow-up denominators (F3); and the H3 read, which REVERSED on the matched five-bar window
  (D5's early exits 16-32% against the stop's 24-48%). Nothing else moved.
- **F2 HIGH, D does not isolate the stop -- AGREE, fixed by addition.** D keeps the one-R
  target but runs to the 20-day cap while the reference marks at five bars, so "only the loss
  side changes" was overstated (1,330 plain daily rows where the reference marked `neither` and
  D filled one R after day five). Book D5 (one R or the exit, settled at the reference's own
  five-bar horizon) is added on the same rows and is the stop-isolating read; D stays as the
  20-day variant. H3's cohorts and windows are matched the same way (D5's early exits inside
  the five bars, T1 units only, against the chance book's stopped-then-saw share). The fee
  sentence is corrected: fees are per fill, not per day held.
- **F3 MEDIUM, incomplete follow-up recorded as false -- AGREE, fixed.** A unit that exited
  but whose 20-day window ran past the data end had `later1 = False` even when the touch was
  observed (733 observed T1 touches among plain daily units). The 20-day flags are now UNKNOWN
  (null, excluded from the denominator) when the cap is not reachable; the five-bar flag is
  the matched read.
- **F4 MEDIUM, holding periods -- AGREE, fixed.** A, B and D showed the exit-only duration and
  the reference a constant five; each book now records its own fill day (target, else exit or
  mark), the reference its stop / one-R / fifth-bar day. The reviewer's recomputed medians (A
  0-1 day, D 1 day) were right.
- **F5 MEDIUM, exit-only cells dropped from the book tables -- AGREE, fixed.** The loop skipped
  a cell with no five-book cohort before printing "C on every unit"; every monthly continuation
  and outside-break cell was missing (monthly continuation spread: 1,434 trades, +0.94%). The
  line is now printed regardless.
- **F6 MEDIUM, LIQUID is retrospective -- AGREE, labelled.** The census label is the median
  notional over the LAST 30 days of the snapshot, inherited for parity; the split footnote
  says so and the table title no longer calls it entry-time.
- **F7 MEDIUM, receipt sentences -- AGREE, corrected.** The weekly / monthly sentence was too
  broad (the weekly continuation within 1% beat the reference under B and C); the own-clock
  count was wrong (14 of 16 by the mean; the receipt now states both the mean count and the
  interval count); the direction and year bullets quoted book C as B and missed two cells
  (the split table has no B column); the entry-day-outside ranges omitted the inside break;
  "the median trade loses in every book that holds past T1" narrowed to B and C. The ledger
  card and this entry were resynchronised.
- **F8 LOW, hypothesis-table fading -- AGREE, fixed.** Rows and share cells fade on their own
  denominators.
- **Open questions:** the vector weaknesses (v7's invalid OHLC, v10 and v11 not isolating
  their tests, v5 / v9 / v13 not asserting counters, no decimal or short-side vectors) are all
  fixed in `tests/test_domino_manage.py` (18 vectors now). The MAE caveat (the entry day's
  adverse extreme may predate the break) is added to the receipt's limitations. The claims the
  reviewer could not verify (vectors before the data run, the byte-identical census, numbers
  unchanged between runs) stand as recorded in this entry.

### Open

- [ ] The owner's own pass over the management book (charts and rows) before anything is read
      into the hierarchy rulings (the TVB-39 trade viewer is the instrument for it).
- [x] The lead's "would test next" list: run in TVB-39 as prereg amendment A2 (owner's word
      2026-10-12).
- [ ] The hierarchy rulings the owner deferred (stop owner in a stack, continuation ranking,
      seat competition, which higher-timeframe event ends a trade).
- [ ] Codex review of this session's range (block above); fold next session.
- [ ] HANDOFF is over the 1,500-line limit (TVB-33..34 are the next archive candidates):
      archiving asks the owner.
- [ ] Executor repairs owed before any real-money restart (TVB-31..35 syntheses); fresh
      wallet; scanner STRAT rulings; the carried list in the TVB-37 entry.

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
the owner's one-word answers. (A personal remark recorded here on 2026-10-10
was removed 2026-10-11 per the close-out audit F9: this is a public record.)

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
  target anyway. That makes the setup-bar stop the suspect, not the verdict:
  reaching a target after a pessimistically assigned stop does not show that
  a book without the stop does better (timing, adverse travel, holding cost
  and the alternate exit are unspecified); product 3 is the declared
  comparison that tests it (reworded 2026-10-11, close-out audit F7).
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
- Headline, in chart terms: of all directional breaks of yesterday's high or
  low, about one in six (15.9% of events; 17.8% of break days, an outside day
  being two events) also took last week's or last month's level for the
  first time. Four in five of those are day plus week. Same-price stacks are a
  shared-open phenomenon (99%: the old week or month made its extreme on its
  last day, which is not the same as closing there; wording corrected
  2026-10-11, close-out audit F4). Two thirds
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
  lifted the reversal, continuation and inside break by four to seven points (the outside break by about three), with fewer stops on all but the continuation (second audit F5). Between one in
  seven and one in three daily units traded their stop on the entry day
  (13.9% outside to 32.2% inside; the owner's "2 going 3"), all counted as
  stops. The continuation stack stays within two points of plain by
  direction, liquidity and the month's open, and by year except 2023 (+4.7).
  Hypothesis 1 was declared on DAILY units: there it reads weak (no gain,
  more stops) and is untestable on reversals (7 shared-open exact reversal
  stacks in the whole sample: a bar that makes the week's extreme on its last
  day is a 2 or a 3, not a reversal setup); the weekly shared-open result is a
  separate descriptive comparison, not a test of it. (This paragraph was the
  stale copy the close-out audit F6 caught; corrected 2026-10-11 to match the
  second-audit synthesis above.)
- Flagged here, then run as product 2b under amendment A3: the R-matched
  check (bar size held equal within five bins, nothing else). Still not done:
  fees / funding / sizing; the Underlying-RTH mirror.

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

- [x] Product 3, the STRAT-management book: DONE in TVB-38 (owner ruled both forks run;
      prereg, card, engine, receipt, page; see the TVB-38 entry).
- [x] Extend `census.day_events` to return the anchor bar's OHLC: DONE in TVB-38, census
      byte-identical before and after.
- [ ] The hierarchy rulings the owner deferred (stop owner in a stack,
      continuation ranking, seat competition, which higher-timeframe event ends
      a trade), now that the books are in hand (carried to TVB-38's Open block).
- [x] Codex backlog run by the OWNER: returned 2026-10-10 / 11, folded by TVB-38 (5e6c59a).
- [x] Close-out Codex review: returned and folded by TVB-38 (5e6c59a); TVB-31..35 folded
      the same day (executor findings recorded for the private repo).
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
- Reviewed by: local Codex CLI, owner-run backlog prompt
  (`docs/reviews/CODEX_BACKLOG_PROMPT.md`), written 2026-10-11 05:39
- Findings: `docs/reviews/tvb37-close-codex-audit.md` -- NEEDS-CHANGES, 9
  findings (F1-F7 MEDIUM, F8 F9 LOW, no HIGH); all 233 book cells, both
  horizons, 12 curves and the R-matched statistics reproduced by the
  reviewer from the saved rows; the census fold F1-F12 confirmed folded;
  no artifact link, host or secret in the range; no Pine file changed
- Review status: ADDRESSED 2026-10-11 (TVB-38): every finding acted on in
  this repo (code by two delegated agents, each finding reproduced before
  the change and the regenerated artifacts checked leaf by leaf by the
  lead; prose by the lead)

### Critical synthesis of the close-out audit (TVB-38, 2026-10-11)

- **F1 MEDIUM, drawdown ignored the starting zero -- AGREE, FIXED,
  REPRODUCED** (one -2% trade read drawdown 0). The high-water mark now
  starts at zero. Regenerated offline on the 2026-10-10 cache (a new
  `--as-of` flag on `book` and `chance` builds the universe from the cached
  files, no venue call, so the window cannot move): exactly 110 drawdown
  values moved across 62 of 233 cells, the audit's count; every other leaf
  of `book.json` is bit-identical (checked independently). The headline
  daily plain reversal cell did not move (its curve was above zero before
  its trough); the two receipt rows that moved are the daily outside
  shared-open stack (-15,053 to -15,121) and the weekly inside shared-open
  stack (-13,221 to -13,316). Three vectors added.
- **F2 MEDIUM, zero shared bar-size bin divides by zero; partial cover
  hidden -- AGREE, FIXED, REPRODUCED.** `r_matched` now returns unavailable
  on no overlap and publishes `covered`, the effective count and a
  conditional flag; the tables and the page print them. Every saved row has
  full cover, so no number changed. Three vectors.
- **F3 MEDIUM, per-horizon counts and greying not carried through -- AGREE,
  FIXED, REPRODUCED** (monthly reversal shared-open 33 valid by 3, 27 by 5,
  ungreyed at 5). Each horizon now greys on its own valid count in the
  R-matched table; the chance difference rows print valid counts at every
  horizon; the hypothesis-1 and variant one-R chances carry Wilson
  intervals (so prereg A4's promise is now met rather than narrowed); the
  chart's bar n is the valid count by 3 (daily plain reversal 43,629, not
  43,809) with faded small cells. `chance_tables.md` regenerated: every old
  number in place, only counts and intervals added; `chance.json`
  byte-identical.
- **F4 MEDIUM, chart labels -- AGREE, FIXED.** Weekly and monthly matched
  rows now name their base (the rest: within 1% plus spread); the
  shared-open mechanism no longer says the old week "closed" on its extreme
  (it made the extreme on its last day); the same wording is corrected in
  the chance glossary, the census headline above and the ledger;
  entry-date attribution of the curves is stated on the page.
- **F5 MEDIUM, book receipt sentences outran the tables -- AGREE on every
  item, CORRECTED and tagged [F5]:** the near 2-2 continuation has a
  positive median; the near outside break (+0.28%, 218 trades) is a second
  daily cell in the black (no chance uplift, negative R expectancy: bigger
  moves, not more hits); hammer stop rates are 8 points lower on the
  reversal, 5 to 6 on the inside and outside breaks and 2 points HIGHER on
  the continuation; entry-day stops are 13.9% to 32.2%, not one in four to
  one in three; the weekly "biggest positive" is by total dollars (near is
  larger per trade); the weekly shared-open floor is -0.8%; hypothesis 1
  is daily-only and the daily matched gap "vanishes" only for the
  continuation (the outside break's stays below zero by 5 bars).
- **F6 MEDIUM, the second fold left wrong numbers and stale copies --
  AGREE, FIXED.** The chance receipt's outside-break hammer figures were
  wrong in sign (34.3% vs 31.7% by 3, 38.8% vs 36.5% by 5, stops 35.3%,
  not 28.9% / 33.2% / 39.3%); this entry's product-2 paragraph still
  carried "nothing flips" and "supported on the weekly" (corrected to the
  second-audit synthesis); the census headline now gives both
  denominators; the chance limitations no longer deny the R-matched check.
- **F7 MEDIUM, descriptive findings stated as causes -- AGREE, REWORDED.**
  "The stop, not the target, is what loses" is now "the setup-bar stop is
  the suspect; product 3 is the declared comparison that tests it" (this
  entry and the startup prompt); the page's "the raw gap WAS bar size" is
  now attenuation after reweighting. The owner's product-3 design is
  unchanged; only what this receipt is allowed to claim changed.
- **F8 LOW, non-strict JSON -- AGREE, FIXED.** `allow_nan=False`, non-finite
  to null, the open top bin as `r_to` null plus `r_to_unbounded`; strict
  parse verified.
- **F9 LOW, a personal remark in the public record -- AGREE, REMOVED.**
- **Disputed: nothing.** Tests 324 -> 344 (11 book / chart-page vectors, 9
  regime vectors from the TVB-35 fold). The private chart page is NOT
  republished yet: the rebuilt page reflects these fixes locally and goes
  up with the next product-3 page build.

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
- [x] HANDOFF.md is far over 1,500 lines: archive TVB-27..TVB-32 to
      docs/session_archive/ on the owner's word (asked at TVB-34, TVB-35 and
      again now). CLOSED at the TVB-37 session start (2026-10-04):
      HANDOFF_TVB27-TVB32.md; the tick was missed then and added 2026-10-14.
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

> Older sessions: TVB-33..TVB-35 archived 2026-10-14 to
> docs/session_archive/HANDOFF_TVB33-TVB35.md (verbatim); TVB-27..TVB-32 archived
> 2026-10-04 to HANDOFF_TVB27-TVB32.md. Earlier: HANDOFF_TVB24-TVB26.md,
> HANDOFF_TVB22-TVB23.md, HANDOFF_TVB18-TVB21.md, HANDOFF_TVB10-TVB17.md,
> HANDOFF_TVB0-TVB9.md.
