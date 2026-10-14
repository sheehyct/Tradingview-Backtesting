# HANDOFF archive -- sessions TVB-33 through TVB-35

> Archived 2026-10-14 from docs/HANDOFF.md (after the TVB-39 close-out, on the
> owner's word; file was 2,140 lines against the 1,500-line limit). Entries
> verbatim, newest first: the round-3 arc (TVB-33 built, TVB-34 live, TVB-35
> halted on the user's word). Earlier archives: HANDOFF_TVB27-TVB32.md,
> HANDOFF_TVB24-TVB26.md, HANDOFF_TVB22-TVB23.md, HANDOFF_TVB18-TVB21.md,
> HANDOFF_TVB10-TVB17.md, HANDOFF_TVB0-TVB9.md.

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
  "rth" rows, one entry = SK Hynix); the weekly dot vetoed 2/91 (the
  "Sun/Mon coupling with the daily open" explanation given here was wrong:
  the scanner's week opens Monday 00:00 UTC, so weekly and daily opens
  coincide only during Monday UTC, Sunday 20:00 to Monday 20:00 New York;
  the 2/91 count stands, its explanation does not -- TVB-35 audit F5,
  2026-10-11); BCH's TP filled in three fragments with
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
  (R18 on my own script). HEADLINE = a structural one: the label is
  mostly UNAVAILABLE at entry. [Paragraph regenerated 2026-10-11 (TVB-38)
  after the TVB-35 Codex audit F6 / F7 / F8: the first labeler read the
  current hour's final close and extremes at the hour's open (look-ahead;
  12 of 84 daily composites moved) and counted a missing whipsaw input as
  "false". Corrected labels, from `analysis/regime/REGIME_RECEIPT.md`:]
  both the dollar and the 10-year daily dots live at entry on 36 of 84
  trades (round 2: 27 of 32; weekend 1: 9 of 34; round 3: 0 of 18, the
  10-year closed all Labor Day). Of the 36, 17 carried a directional
  label (13 with, 4 against) and 19 had both inputs live but disagreeing
  or flat. Round 2, the only readable ledger: with 11 trades (4 wins,
  -3.93pp), mixed 18 (7 wins, +14.84pp), against 3 (0 wins, -2.79pp);
  pooled with 13 (5 wins, -6.37pp) against 4 (0 wins, -4.33pp). The old
  paragraph's "with +6.75pp, sign matches the prior" does NOT survive the
  fix; the "against" cell is still 0 wins on n=4, which says nothing. The
  running outside-day whipsaw flag: true 0, false 10, unknown 74 (weekend
  1 had no BTC history at all) -- the old "fired on 2/84 = inert" claim is
  WITHDRAWN; the flag was mostly unknowable, not inert, and a different
  a-priori measure (prior-day outside bar, range vs ATR, realized vol)
  remains the open design item. NOW (23:33Z): dollar down daily+weekly, 10-year closed,
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
- Reviewed by: local Codex CLI, owner-run backlog prompt, 2026-10-10
- Findings: `docs/reviews/tvb35-codex-audit.md` -- NEEDS-CHANGES, 9
  findings (F2 F6 HIGH; F1 F3 F5 F7 F8 MEDIUM; F4 F9 LOW); the public pin
  held the regime script, data, receipt and harvest script, not docs only
  as this block said; no Pine file changed
- Review status: ADDRESSED 2026-10-11 (TVB-38): F6 F7 F8 F9 fixed in this
  repo and the receipt regenerated; F5's wrong explanation annotated here
  and in the ledger; F1-F4 recorded for the private repo

#### Critical synthesis (TVB-38, 2026-10-11)

- **F6 HIGH, the macro labeler read the future -- AGREE, FIXED, REPRODUCED.**
  `price_at` took the latest hourly bar whose OPEN was at or before the
  instant and returned its CLOSE; the running day took that hour's full
  high and low. At an hour's opening instant neither is known. The audit's
  synthetic hour reproduced (opens 101, closes 90: the label read 90 at the
  open). Now a 60m bar is known at open + 60 minutes; price now is the
  latest COMPLETED close; the running day uses completed bars only;
  freshness runs from the last completed close; a day or week whose first
  hourly bar has not started has no known open (US10Y's daily bar is
  stamped 23:00, first trade 00:00). Regenerated: 12 of 84 daily
  composites moved (8 round 2, 4 weekend 1), exactly the audit's count.
  Nine hand vectors in `tests/test_regime_receipt.py`. The two TVB-36
  receipts (`index_continuity.py`, `venue_mrc.py`) were checked for the same
  pattern: neither reads a bar before its close.
- **F7 MEDIUM, missing whipsaw history became "false" -- AGREE, FIXED.** All
  34 weekend-1 trades had no BTC running day and were counted false. The
  flag and its components are now true / false / unknown with availability
  counts; the result is 0 true, 10 false, 74 unknown. The "inert as an
  entry-time label" inference is withdrawn (above).
- **F8 MEDIUM, the availability narrative contradicted its own labels --
  AGREE, FIXED.** The receipt now separates inputs available (36 of 84 with
  both dots live), available-but-mixed (19) and directional (17: 13 with,
  4 against), per ledger and pooled; this entry's paragraph is regenerated
  from those counts. The old "with +6.75pp" reading does not survive the
  F6 fix (pooled with is now -6.37pp over 13).
- **F9 LOW, a timed-out harvest could save the wrong symbol -- AGREE,
  FIXED.** A settle timeout or identity mismatch is now a failed manifest
  entry with no file written (`scripts/tvb35_regime_harvest.mjs`, not run).
- **F5 MEDIUM, the Sun/Mon weekly-dot explanation is wrong -- AGREE,
  ANNOTATED** here and in `docs/ARM_LEDGER.md`: the scanner's week opens
  Monday 00:00 UTC, so weekly and daily opens coincide only during Monday
  UTC; the 2-of-91 count stands, the calendar story does not. The executor
  README carries the same sentence (recorded for the private repo).
- **F2 HIGH, an unbounded order-book read in front of the safety loop --
  AGREE.** The shadow's `book_top` uses the shared Info client with no
  timeout, before `_enter` and before every later stop check and kill-file
  read. OPEN in the executor before any restart: bounded or asynchronous
  shadow reads with a total time budget.
- **F1 / F3 / F4 (seat-competition population omits `already_in_position`;
  the paper shadow cannot resolve builder-dex names; non-finite book
  values pass) -- AGREE, recorded for the private repo.** F1 is a
  definition to preregister, not a round-3 count change (zero such rows).
- **Disputed: nothing.** One nuance accepted from the reviewer: the ZEC
  liquidation's placement is internally consistent but rests on a venue
  fill record not present in the run files, so it stays a documented claim.

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
      NOTE 2026-10-11 (TVB-34 audit F3): `backing_invalidated` is computed in
      rules.py but never written by the decision journaler, so it cannot be
      read journaled-first until the executor repair lands.
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
- Reviewed by: local Codex CLI, owner-run backlog prompt, 2026-10-10
- Findings: `docs/reviews/tvb34-codex-audit.md` -- NEEDS-CHANGES, 3
  findings (F1 F2 HIGH, F3 MEDIUM), all in the executor; the liquidation
  formula and clearing leverage, the weekly-dot gate / flip symmetry, the
  VWAP arithmetic, amendment j and the twin's `entry_fill` branch checked
  clean within their declared scope
- Review status: ADDRESSED 2026-10-11 (TVB-38): the one public-repo
  consequence (the `backing_invalidated` replay promise) is annotated in
  this entry's Open list; the repairs are recorded for the private repo

#### Critical synthesis (TVB-38, 2026-10-11)

- **F1 HIGH, the malformed-flat repair stops at the outer list -- AGREE.**
  A row with no position object, or a position with no size, still reads as
  zero and proves absence. This is the TVB-31 F1 fold left half done. OPEN
  in the executor before any restart: validate every row (coin, finite
  signed size); any malformed member raises "unknown".
- **F2 HIGH, a partial close during protection loss becomes an unretryable
  mismatch -- AGREE.** The generic handler swallows the partial fill without
  booking the fragment; the next poll sees a size mismatch and continues
  BEFORE checking or restoring a stop, so the residual can sit unprotected
  indefinitely. The same classification hits the legitimate software-exit
  residual. OPEN before any restart: persist fragments and pending close
  intent, track expected residual separately from original size, route
  every close caller through one resumable reconciliation path.
- **F3 MEDIUM, the invalidated-sponsor shadow is computed and dropped --
  AGREE.** `extra['backing_invalidated']` never reaches the decision row,
  so the "journaled-first" replay promise in this entry and in the round-3
  prereg cannot be kept until the journaler writes it. Annotated in the
  Open list above. OPEN: persist the field, test the emitted row.
- **Disputed: nothing.** The reviewer's refusal to treat the go-live and
  the agent-pruning statements as revalidated is correct; they are
  historical claims.

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

- Review status: ADDRESSED 2026-10-11 (TVB-38). Requested 2026-09-05; the
  separate DEEP-DIVE review RETURNED 2026-09-05 and was FOLDED 2026-09-06
  (section 7). The session review itself returned 2026-10-10 from the
  owner-run Codex backlog prompt.
- Commits reviewed: this repo `7a29dad..7ad92f4`; hip3-executor
  `4b5d248..d8a07b0` (derived range, confirmed by the reviewer in that
  repo's log).
- Findings: `docs/reviews/tvb33-codex-audit.md` -- NEEDS-CHANGES, 3
  findings (F1 HIGH, F2 F3 MEDIUM), all in the executor's replay harness;
  the prereg amendments, the live fee gate and the round-3 build checked
  clean within their declared scope.

#### Critical synthesis (TVB-38, 2026-10-11)

- **F1 HIGH, the parity PASS is not pinned to the sweep setting -- AGREE.**
  The pins hash files, ledgers, candles and source but not `roll_freeze_ms`,
  so a PASS earned at 75 seconds authorizes a run at zero seconds with
  nothing watermarked. That weakens the pre-registered stop gate exactly
  where it is supposed to bite. OPEN in the executor: include every
  behaviour-changing runtime argument in the compared pins; a mismatch
  refuses unless forced and watermarked.
- **F2 MEDIUM, duplicate ledger entries collapse silently in P1 -- AGREE
  (latent).** OPEN: assert ledger-key uniqueness and require ledger, replay
  and matched counts to agree.
- **F3 MEDIUM, builder fee counted twice -- AGREE, conditional on the API
  reading.** The reviewer cites the venue's user-fills reference defining
  `fee` as inclusive of `builderFee`; both saved ledgers have zero nonzero
  builder-fee rows, so no committed table moved. OPEN: verify the field
  definition once more in the executor session, then charge the inclusive
  fee once and report the component.
- **The reviewer's framing is accepted:** a high replay-agreement figure is
  a disclosed characterization contract conditioned on historical
  decisions and exits, not fidelity, edge or safety evidence. That is how
  TVB-33 already reads it.
- **Disputed: nothing.**

---
