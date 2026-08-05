# HANDOFF -- tradingview-backtesting

> Newest session entry at the TOP. Keep under 1500 lines; archive older entries to
> `docs/session_archive/` when it grows past that.

---

## Session TVB-18: Week-1 close-out + TVB-15 audit fold-in + design direction (COMPLETE)

**Date:** 2026-08-03/04
**Status:** COMPLETE -- the overdue paper close-out plus a same-session
external-review round trip. First session run over remote control. Every
mechanical standing item cleared; the one remaining open arc is the
exit-design session, now fully staged with user decisions recorded.

### What was accomplished

- ARCHIVE CATCH-UP + WEEK CLOSE-OUT: all 11 roster symbols pulled through
  08-04 00:45Z (5m/1h/1d; merged spans 07-03 -> 08-04) -- the 07-20 window
  start secured ~3 days before the HL floor slide-off. Replay closed the
  07-20..07-27 window deterministically: 38 committed events reproduced
  BYTE-IDENTICALLY, 43 appended (81 total; 44 entries / 37 exits). Suite
  green (97 passed, 2 skipped) incl. 24 paper goldens. Commit a1a886f.
- WEEK-END PASS (protocol doc): full-record realized -27.61pp over 37
  closed / open MTM -40.65pp / combined -68.25pp (gross, 1x, roster excl
  DRAM). Exit classes: 24 BF harvests +1.86% avg (win-by-construction),
  7 adverse-breaks -8.15% avg (worst NBIS -26.82, MRVL -14.32), 6 flips
  -2.54% avg. TSLA the counterexample: 8/8 harvests +18.99pp. Full-week
  ablation (control vs user live variant): knobs RE-TIME the same book
  (combined -68.25 vs -63.13), adverse-runner class config-invariant.
- PARITY PASS (DRAM/TSLA/GOOGL, fresh mounts on scratch layout
  TVB18-parity; the deployed accumulated-history instances were removed
  from all layouts during the user's SNDK-focus period): positions and
  gate composites match EXACTLY (DRAM's one apparent gate mismatch
  resolved numerically -- 13 cents through the monthly open across a
  15-min read gap); every operative rung is the same structural line
  within 0.004-0.04%. Census NOT comparable from fresh mounts.
  NEW OPERATIONAL FINDING: loaded chart history is load-bearing state --
  a remount silently thins the harvest ladder (fresh DRAM nearest exit
  41.04 vs full-history twin 12h rung 47.39; -5% harvest vs -18% ride).
  Twin side: analysis/paper/parity_state.py (committed).
- TVB-15 EXTERNAL REVIEW ROUND TRIP, same session: paste-ready prompt
  delivered (range-pinned, post-range guardrails, known-open list); user
  ran Codex CLI; audit RETURNED NEEDS-CHANGES (1 HIGH + 3 MEDIUM) and was
  folded in the same day -- ALL FOUR findings independently reproduced
  before adjudication (TVB-14 precedent). Commit 0789d2c.
  - F1 HIGH: window opens 00:00, roster froze 14:31:21 -- 18/81 events and
    12/37 closed trades (incl. BOTH catastrophic adverse-breaks) entered
    pre-freeze. Realized flips -27.60 -> +14.37pp in the post-freeze-entry
    slice (analysis/paper/freeze_slice.py, committed). The adverse-runner
    gap SURVIVES: window-end open runners (GOOGL -15.8 / AMZN -19.5 /
    SKHY -12.1) all entered post-freeze.
  - F2: committed snapshot = 13:26:36Z (65 min early); freeze source
    unrecoverable; roster.py fails open.
  - F3: coarse 1h/1d warm-up changes LIFECYCLE state, not just anchors --
    reviewer's TSLA instance reproduced exactly; delta 1 amended.
  - F4: evict-alive counts fallback formation evictions, not alive sides;
    the TVB-15 "14 vs 13+1=14" parity line was WRONG (annotated in place;
    actual day-one twin counter 15, as the protocol doc recorded).
- WEEK-1 ADJUDICATED BY THE USER (recorded in the protocol doc, c93dcaf):
  NO official number -- performed wrong, stands as a process test run
  (gotchas + why-trades-went-good/bad); both views stay as documentation.
  REPAIRS ALL GREENLIT (F2 + F3 + F4 + freeze-boundary invariant for
  future rosters; week-1 files stay frozen). NO week-2 rerun now; next
  build focus = the exit-design step.
- DESIGN DIRECTION RECORDED (user, verbatim intent): the Magnitude+Targets
  [Custom] indicator (committed as pine/strat_magnitude_targets_plus.pine
  + README, c954c22 -- logic-identical fork of the partner original,
  display/UX layer only, zero request.security) is the where-to-take-
  profit half; target ladder = harvest path (5-6 rungs, count TBD); BF =
  exhaustion overlay at extended rungs; kill-signal there = continuity
  turning against the position while extended. Drop-the-month agreed AS A
  START with the COUPLING caveat -- at period boundaries flips are not
  independent votes (new week = D+W open on the same print; month couples
  with day always, with week only on Monday month-starts; stacked levels
  can break on one tick = domino). Design must resolve gate-flip
  (close-vs-open, deployed) vs scenario-flip (prior-extreme break, STRAT)
  semantics. NO flip code before the design session (skill mid-rebuild,
  Ambiguity Policy strict).
- THESTRAT.AI CORPUS LANDED + ASSESSED + PROTECTED: docs/thestrat_ai/
  (417 files, 48.7 MB; 70 articles, 121 SVG figures with OBSERVED/DERIVED
  separation and a 164:2 label-agreement ledger; grep-first discipline by
  its own README; term-index.csv). It answered the coupling question BY
  NAME: UNCOUPLING (03/07) -- "until the opens separate, some of your
  four facts are the same fact" + separation schedule + month-start
  rules (RTH arithmetic; translate to 24/7 UTC rolls per charter S2).
  Vocabulary trap: corpus "flip" = new 60-minute open (03/06). GITIGNORED
  (3200e3b): public remote, scraped curriculum mirror, not ours to
  republish (VBT protective class); stays fully greppable locally.
- NEW QUESTION SEEDED (user, from live-trading experience): the RTH-clock
  test -- what changes in backtest numbers for the SAME perp when
  uncoupling/flip rules apply only during RTH? These are oracle-priced
  equity perps under TWO clocks (venue 00:00 UTC vs underlying 9:30 ET).
  Cheap first step = read-only census of UTC-clock vs RTH-clock signal
  disagreement per symbol per hour; full pre-registered arms only if
  disagreement is material. The anchor clock is a tested variable, not an
  assumption.
- HOUSEKEEPING: /pre-commit Check 2 amended to the corrected lookahead
  rule (TVB-17 blocker cleared -- the permission classifier allowed the
  edit this time); TVB-15 statuses flipped RETURNED in REVIEW_REQUEST.md
  + the TVB-15 HANDOFF block (wrong parity line annotated in place).

### Context for next session

- The design session is THE next move (plan mode ON, STOP-and-ASK
  throughout). Its brief, inputs, and the user's recorded decisions are
  consolidated in the protocol doc ("Week-1 adjudication" + design bullet)
  and .session_startup_prompt.md.
- The greenlit repairs (F2/F3/F4 + invariant) land before any future
  graded run; F4's Pine side deploys with the design bundle (no live chart
  mounts the indicator -- zero drift meanwhile).
- TradingView state: scratch layout TVB18-parity exists (fresh-mount
  TFC-BF for parity reads; harmless, delete or keep); the user's live
  layouts are SNDK-focused with a community "Strat Assistant" study; new
  user scripts since TVB-17: the Magnitude+Targets pair (07-30) and
  "Memory/Storage Complex Composite (HIP-3)" (08-03).
- The HL 5m floor keeps rolling: post-week bars through 08-04 are
  archived; nothing time-critical is pending.

### Files created/modified

- Created: analysis/paper/parity_state.py, analysis/paper/freeze_slice.py,
  pine/strat_magnitude_targets_plus.pine + .README.md,
  docs/reviews/tvb15-codex-audit.md (reviewer-written, committed here)
- Modified: analysis/paper/bars/* (33 files), events_week1.jsonl,
  scoreboard_week1.md, docs/experiments/tvb15_paper_week1_protocol.md
  (week-end pass + audit fold-in + adjudication + corpus pointer),
  docs/HANDOFF.md (TVB-15 annotation + this entry), REVIEW_REQUEST.md,
  .claude/commands/pre-commit.md, .gitignore, .session_startup_prompt.md
- Local-only: docs/thestrat_ai/ (gitignored corpus)

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work
> (range below) and write a verbatim assessment to
> docs/reviews/tvb18-codex-audit.md. See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: REQUESTED
- Commits to review: `a1a886f^..57417e2` on `main` (6 commits: a1a886f
  week-1 close-out; c954c22 indicator pair; 0789d2c audit fold-in;
  c93dcaf adjudication; 3200e3b corpus gitignore; 57417e2 session-end
  docs; the pin commit follows outside the range, per precedent).
  RANGE-PIN RULE: caret included; sanity-check
  `git diff --name-status a1a886f^ 57417e2` lists every file the session
  touched.
- Scope / what changed: week-1 archive/replay close-out + week-end pass +
  fresh-mount parity; TVB-15 audit fold-in (freeze_slice + doc
  corrections + status flips); the Magnitude+Targets [Custom] indicator
  pair; week-1 adjudication + design-direction records; corpus gitignore.
- Focus areas (scrutinize these): (1) freeze_slice.py correctness (slice
  boundary semantics: entry_ts vs event ts, parity exclusion, open-MTM
  attribution) and whether the +14.37pp clean-slice framing carries any
  hidden performance claim the adjudication forbids; (2) parity_state.py
  fidelity to replay.py conventions (warm-up, seed windows, last-bar
  drop) and the parity pass's honesty about fresh-mount limits; (3) the
  fold-in adjudications vs the audit text -- did TVB-18 reproduce F1-F4
  faithfully and act proportionately; (4) the amended pre-commit Check 2
  wording vs pine/README.md rule 3; (5) the new pine pair: zero
  request.security claim, defaults-render-identical claim vs the
  tv_indicators canonical copy (byte-identical check); (6) gitignore
  protection completeness for docs/thestrat_ai/ on the PUBLIC remote.
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb18-codex-audit.md exists)

---

## Session TVB-17: Context-engineering audit of standing context (COMPLETE)

**Date:** 2026-07-27
**Status:** COMPLETE -- a workspace/context session, NOT the seeded TVB-17 paper
work. The seeded priorities (ride-along refresh, week-end pass) were NOT
executed and carry forward to TVB-18 unchanged. The user ran this audit across
three repos simultaneously and stalled on the volume of findings; scope was
deliberately cut to the lighter set on their instruction.

### What was accomplished

- AUDITED all standing context: spine CLAUDE.md, repo CLAUDE.md, `.claude/`
  settings + commands, `.mcp.json`, user-global settings, and the auto-memory
  index. Always-on repo-controlled load measured at 28,323 bytes (~7.5K tokens)
  across three files; everything else is load-on-demand.
- **CLAUDE.md 9252 -> 5203 bytes (-43.8%).** Deleted Section 10 (a verbatim
  restatement of Sections 2-9), the spine duplications (ASCII / conventional-
  commits / ambiguity-policy), and session-protocol prose that `/session-start`
  already performs. Every epistemic-stance and mechanics rule was KEPT --
  classified as domain invariants a capable model would get wrong by default.
  Landed above the 3-4KB target on purpose: further cuts would have removed
  invariants, not redundancy.
- **PROMOTED six gotchas out of auto-memory into the always-on file:** the
  `pine_new`/`pine_open` tab-binding overwrite trap (destroyed BF-1 2026-07-10),
  `uv sync` strips VBT Pro, `closedtrades.profit()` is gross of commission,
  `tv_launch` fails on the Store app, autonomous commit/push overriding the
  harness default, and the plain-language results rule. The audit's framing:
  obvious structure was in CLAUDE.md while the real traps were buried in memory.
- **EXECUTED the TVB-11 audit finding F7** (agreed, queued as remediation item
  3, never done). The `request.security` trap is UN-OFFSET `lookahead_on`, not
  `lookahead_on` as such; the documented `expr[1]` + `lookahead_on` non-
  repainting idiom is used deliberately in 5 scripts (count has grown from the
  4 F7 recorded). The blanket `lookahead_off` rule contradicted accepted code
  and would have flagged all 5 as failures -- or pushed a future session to
  "fix" correct non-repainting code into repainting code. Amended in CLAUDE.md
  and `pine/README.md` rule 3. **`.claude/commands/pre-commit.md` Check 2 still
  carries the OLD rule** -- the permission classifier blocked that edit; until
  it is fixed `/pre-commit` will report a false FAIL on the 5 files.
- **FIXED the dead Stop test gate (the audit's highest-value finding).**
  `stop_test_gate.sh` had no `tradingview-backtesting` case: the hook was
  registered with a 300s timeout, printed "unknown project directory, skipping",
  and returned 0. **No test has ever been gated in this workspace.** Added the
  case; verified it now runs (97 passed, 2 skipped, ~2.3s) and that all five
  existing projects still route unchanged. The suite was healthy the whole time
   -- the gate was the only thing broken.
- README: warned that `uv sync` strips VBT Pro, directly contradicting the
  getting-started block above it.
- Spine `CLAUDE.md`: removed the "Schwab Level 1 Options" account constraint --
  user confirmed no such account exists and could not place its origin.

### Drift found and NOT fixed (deliberate, lighter-scope call)

- `safety_guard.py`: `RE_DOCKER_PROD` is compiled and never called (dead code),
  so "NEVER docker compose prod" is unenforced prose. Same for the SSH/SCP and
  VPS-IP rules -- no patterns exist, and global settings explicitly allow
  `Bash(ssh:*)` / `Bash(scp:*)`. NOT fixed: adding a new hard block to a shared
  safety file was judged too risky to do unsupervised.
- `PROJECT_ROOTS` in `safety_guard.py` omits `tradingview-backtesting` and all
  `hip3-*` repos, so `rm -rf` protection does not cover them.
- `checkpoint_review_prompt.py` exists (with a compiled `.pyc`) but is wired in
  no settings file -- orphaned.
- `post_edit_lint.py` returns early on any non-`.py` path, so the repo's primary
  artifact (`.pine`) has no automated check of any kind.
- Spine hook table omits `session_orchestration_prompt.py`.
- Dead references: `mcp__tradingview__ui_evaluate` (tool no longer exists in the
  jackson server; deny rule harmless, but `README.md:38` documents it as live),
  seven `mcp__playwright__*` permissions (server not enabled in this project),
  and `Read(//c/Users/sheeh/Downloads/**)` (wrong user profile).
- OUT OF BAND: a live `OPENAI_API_KEY` sits in plaintext in
  `~/.claude/settings.json`. Not in this repo, not exposed by the public push;
  flagged to the user for rotation.

### Proposed gates NOT built

G2 (a pytest asserting every `request.security` either uses `lookahead_off` or
pairs `lookahead_on` with an explicit offset) and G3 (an ASCII/emoji check --
the rule is stated in two files, enforced nowhere, and already violated by 266
non-ASCII chars in the charter and 4 in `tfc_companion.pine`). Both were judged
new maintenance surface the user did not have capacity for. G1 (the test gate)
was built.

### Context for next session

- **The seeded TVB-17 paper priorities did not happen and are now TVB-18's.**
  Paper week 1 CLOSED 2026-07-27 00:00 UTC. The record is still current only
  through 07-22 02:05Z (~5 days stale). **No data has been lost:** the HL
  candleSnapshot floor is ~5000 candles (~17 days at 5m), so the 07-20 window
  start does not slide off until roughly 2026-08-06. There is headroom, but it
  is finite -- archive before then.
- The week's HEADLINE finding is unchanged and still awaits a design session:
  the config-invariant adverse-runner exit gap (three shorts rode ~49h with no
  exit; identical across the 12h/arm ablation).
- TVB-15 external review is STILL PENDING; `docs/reviews/REVIEW_REQUEST.md` was
  deliberately NOT rewritten this session so that request stays live.
- CLAUDE.md is now materially shorter. If something feels missing, the deleted
  material was either restating the spine, restating itself, or describing what
  `/session-start` already does -- check git history at `7ebc955` before
  re-adding.

### Files created/modified

- `CLAUDE.md` (rewritten), `README.md`, `pine/README.md`, `docs/HANDOFF.md`,
  `.session_startup_prompt.md`
- Outside git (spine is not a repo -- no revert point): 
  `C:\Strat_Trading_Bot\.claude\hooks\stop_test_gate.sh`,
  `C:\Strat_Trading_Bot\CLAUDE.md`

### External Review (for Codex / cloud review agents)

- Review status: SKIPPED -- context/docs session, no strategy or engine change.
  The one item a reviewer might want to confirm is the F7 execution (that
  `expr[1]` + `lookahead_on` is genuinely the non-repainting idiom and the
  amended rule is correct); that finding was itself externally reviewed and
  agreed in TVB-11.
- Commits to review: `7ebc955^..HEAD` on `main` if reviewed later.
- Focus areas: the amended `request.security` rule; whether anything cut from
  CLAUDE.md was load-bearing.

---

## Session TVB-16: Ride-along refresh + config ablation + mid-week check-in (COMPLETE)

**Date:** 2026-07-22
**Status:** COMPLETE -- a check-in session (not a build): the week-1 paper
record was refreshed from the day-1 freeze to current, the recording accuracy
was verified, the entry model and the live-config framing were clarified WITH
the user, a read-only ablation harness was built to measure the user's live
settings against the frozen control, and the week's headline finding (a
config-invariant adverse-runner exit gap) was logged for a week-end design
session. No strategy or frozen-record change; mid-week no-tune held.

### What was accomplished

- RIDE-ALONG REFRESH: archive + replay advanced the week-1 record from the
  day-1 freeze (07-20 14:30Z) to 07-22 02:05Z. Deterministic and additive --
  the 18 day-1 events reproduced BYTE-IDENTICALLY on re-replay (verified by
  set comparison; the CRLF `diff` mismatch was an artifact), 20 day-2 events
  appended (18 -> 38); 24 paper goldens green. 15 closed trades, 8 open.
  Closed exit classes: BF harvest 8/8 green (+1.82% avg, 0.14pp give-back),
  BF adverse-break 2 (-0.75%), flip backstop 5 (-2.10%, 4.18pp give-back);
  realized sum +2.59pp. Open mark-to-market ~-49pp across all 8 opens (three
  shorts dominate). Committed 89e2fb5, pushed.
- ENTRY MODEL CLARIFIED (corrected a user assumption): the twin is
  ALWAYS-IN-market, seeded FLAT at the week boundary (07-20 00:00 UTC), and
  re-enters on the very next qualifying 5m bar after any exit. 6/10 symbols
  opened within an hour of 00:00 from the flat seed (NOT fresh mid-week
  triggers); MSFT (+915min) was the only genuine mid-week-signal entry. The
  user's "last active enter" read was right, not "enter once on first
  signal." The flat-seed timing (a declared delta) placed the bleeding
  shorts right before the rally and materially inflates their severity.
- CONFIG FRAMING RESOLVED (with user): the frozen twin (15m arm, 12h/D/W/M,
  all v6.1 defaults) IS the shipped/established strategy = the legitimate
  a-priori CONTROL; the user's live manual settings (1H arm, 12h pool OFF)
  are a post-ship drift the user owns = the VARIANT. The week-1 record keeps
  its integrity; the live chart is NOT a mirror of the twin (divergence by
  config is expected). NOTE: the shipped Pine `en_12h` is all-or-nothing
  (lines + exits together, pine :113); there is NO "12h lines on, harvest
  off" toggle -- if wanted, that is a feature, not a checkbox.
- ABLATION HARNESS + RESULT (analysis/paper/compare_config.py, read-only,
  never writes the frozen record; no engine change -- drop the 12h pool
  post-construction, set arm_tf_s): control (15m, 12h/D/W/M) vs variant (1H,
  D/W/M) on the SAME committed bars. 12h-off had LOWER realized (+0.76 vs
  +2.59pp -- the 12h pool harvests winners, not noise) but fewer/bigger/
  cleaner harvests (+3.94 vs +1.82, gb 0.07 vs 0.14 = the "12h harvests too
  eagerly" intuition, measured). Combined ~equal (both ~-34pp): the two knobs
  RE-TIME the same book, not re-edge it. The three stuck shorts are IDENTICAL
  across configs -- the adverse-runner gap is invariant to both knobs.
  Committed 39fd165, pushed.
- HEADLINE FINDING (user chose "log it, design at week-end"): config-
  invariant adverse-runner exit gap. NBIS -22% / DRAM -13% / MRVL -11% rode
  ~49h with NO exit. Mechanism confirmed by dumping gate + alive-line state
  (not inferred): all three read D=down / W=up / M=down, so the flip backstop
  (needs FULL D/W/M) never arms; the nearest alive adverse (upper) BF line
  sits 3-17% above price, so no break exit; open-air run with no line in the
  path. Ties to the TVB-14 open "flip-backstop granularity (full vs partial
  D+W)". Fix is a STOP-and-ASK design question for week end.
- ACCURACY VERDICT: the RECORD is sound (deterministic, additive, goldens
  green, day-1 DRAM parity was exact). The one real gap was STALENESS (the
  record sat at day-1 until refreshed); the ~3-day archive cadence (5m floor
  ~17d) is the standing operational risk -- worth automating. Live-chart
  parity spot-check still pending (TV was not on CDP this session).

### Context for next session

TVB-17 = keep the cadence (archive+replay+compare by ~07-25), collect grades;
at week end (>= 07-27) run the parity/give-back pass THEN design the headline
adverse-runner fix WITH the user (flip full-vs-partial, or open-air stop --
design before code). TVB-15 external review is still PENDING. The scanner
score work stays in the hip3-scanner workspace.

### Files created/modified

analysis/paper/compare_config.py (new, read-only ablation tool);
analysis/paper/bars/ (33 refreshed), events_week1.jsonl, scoreboard_week1.md
(refreshed via replay); docs/experiments/tvb15_paper_week1_protocol.md
(+ TVB-16 mid-week check-in section); .session_startup_prompt.md,
docs/HANDOFF.md, docs/reviews/REVIEW_REQUEST.md.

### External Review (for Codex / cloud review agents)

- Review status: N/A -- SKIPPED (user decision). TVB-16 was a light session:
  a data refresh, a read-only ablation tool, and docs notes; no strategy or
  engine change. The standing external-review request remains TVB-15
  (docs/reviews/tvb15-codex-audit.md, still pending).
- Commits (context, not a review request): `89e2fb5` (ride-along refresh),
  `39fd165` (ablation tool + mid-week note), plus the session-end docs commit
  on `main`.

---

## Session TVB-15: Paper twin + week-1 freeze; TVB-14 audit folded same day; v6.1 (COMPLETE)

**Date:** 2026-07-20
**Status:** COMPLETE -- four arcs in one session: (1) the week-1
paper-trading system designed WITH the user and built (Python twin recorder,
scanner-fed frozen roster, HL archive, deterministic replay + scoreboard);
(2) the TVB-14 external audit RETURNED, every count independently
reproduced, and its two HIGH findings fixed forward as v6.1 SAME DAY under
the pre-declared policy, deployed and parity-verified live; (3) the
heat-score dual review (Claude + GPT blind, then compared) delivered to the
hip3-scanner workspace; (4) day-1 replay produced 18 events and the first
exit-class numbers.

### What was accomplished

- PAPER-TRADING WEEK 1 (decide-WITH-user; forks ratified via dialog):
  recorder = PYTHON TWIN over archived HL bars (not TV-alert webhooks);
  roster rule = xyz, vol>=5M, OI>=3M, top-5 |score| per direction, FROZEN
  for the week; both directions enabled everywhere (score selects, the
  D/W/M gate decides). Built analysis/paper/{engine,roster,archive,replay}
  .py + 24 tests + byte-for-byte fixture-parity goldens (tests/golden/).
  Roster frozen 14:31Z: long MRVL/GOOGL/AMZN/MSFT/GOLD, short AAPL/SKHX/
  SKHY/NBIS/TSLA, + DRAM as labeled parity entry. TV minticks captured via
  scripts/tvb15_symbolinfo.mjs (SKHX has NO TV listing -- twin-only,
  hl_inferred tick). Score rotation observed live at freeze (NBIS +75 ->
  -40 in 2.5h) -- recorded, not re-litigated. Archive: 33 files, 11
  symbols x 5m/1h/1d (~5MB committed; 5m floor ~17d -> refresh <= 3 days).
  Day-1 replay: 18 events; TSLA harvested 2 BF exits (both green), AAPL
  took the first adverse-break exit, GOOGL/GOLD flip backstops; 7 open.
  Protocol doc: docs/experiments/tvb15_paper_week1_protocol.md (a-priori
  conventions, declared deltas, grading contract, mid-week policy).
- TVB-15 FINDING (pre-audit, morning): the committed TVB-14 fixture's
  two-pass ordering shadows supersede over two real touches (12h F23/F39
  lowers print "superseded", Pine consumes first) -- engine matches Pine;
  pinned as FIXTURE_SUPERSEDE_SHADOWS + invariant test. The afternoon
  audit independently found the same two lines (its F3): convergent.
- TVB-14 AUDIT FOLD-IN (returned NEEDS-CHANGES, Codex CLI user-run):
  every quantitative claim reproduced before acting. F1 HIGH
  supersede-before-ghost deletes an unchanged still-valid side --
  CONFIRMED (D F17/F18 + 12h F23/F24 in committed data; live roster: AAPL
  twin lost a D lower at -13.9%). F2 HIGH pool_cap evicts alive lines --
  census reproduced TO THE DIGIT (12h 54 births/42 evictions/22
  alive-at-eviction; D 27/15/6); roster sweep found evicted-alive rungs at
  4-8% on AAPL/MSFT/GOOGL/GOLD/TSLA incl. the standing TSLA short's -7.4%
  harvest rung. F4/F5/F6 agreed (tiling overstatement; min_sep relabel
  "provisional example-derived"; commit count 4 not 5). One partial
  dispute: the v5-header "57 -> handful" sentence referred to structural
  alive lines, not kept-formation count.
- v6.1 FIX-FORWARD (user ratified: retired-first eviction + full bundle,
  same day; pre-declared mid-week policy exercised): per-side supersede,
  retired-first eviction with visible evict-alive counter, non-tiling
  chart-TF warning, min_sep relabel. Engine in lockstep behind flags
  (v6.0 mode kept for goldens); regression pins: v6.0 alive-at-eviction
  22/6 reproduces the audit, v6.1 cuts to 13/1, DRAM restores 10+6 alive
  sides. Deployed to the live DRAM 5m (USER;7c28fa0b version 6.0 -> 7.0,
  saved 16:04Z, on-chart ~16:08Z; binding verified, version bump
  verified; deploy restored two v6-only header bullets the repo had
  dropped). POST-FIX PARITY: chart and twin alive counts EXACT
  (13/11/2/0); on-chart evict-alive 14 vs twin census 13+1=14 [WRONG --
  TVB-15 audit F4, annotated by the TVB-18 fold-in 2026-08-04: this line
  reused the fixed-regression census; the actual day-one twin counter was
  15 (14 12h + 1 D), as the protocol doc correctly recorded ("14 vs 15,
  history-depth class"). The counter counts fallback formation evictions,
  not alive sides removed]; next-line
  values agree once slopes are projected across the 1.6h read gap.
  WEEK-LOG CONTINUITY: v6.1 re-replay = the IDENTICAL 18 events (no
  affected line had been touched); TVB15-D1 (day-1 stale-line divergence)
  substantially RESOLVED -- it was mostly F1/F2 behavior, not
  warm-history resolution.
- SCORE DUAL REVIEW (user request; scanner moved to its own workspace):
  my six proposals formed from two live /api/state snapshots 3.5h apart
  (median |dScore| 30, p90 74, 72/262 sign flips, tails 1/10 + 0/10, the
  dot term -- not momentum -- drives rotation, corr(dot,mom)=0.703
  double-count); independent GPT review returned and ALL its code claims
  verified against source (stale live-signal counting vs skill 4.1
  in-force; RVOL median 0.56 makes |score|>=60 unreachable + missing-RVOL
  outranks median; r60 anchor jump from the 7-min mid-history prune;
  dashboard UI-TF recompute parity gap; score_cross DISABLED in config).
  Blind convergence on: consumer-contract split, selection reads
  D/W/M formingDir (ALREADY served by /api/state), ATR-normalized
  exact-horizon momentum, direction/activity separation, instrument
  before retuning. Key system fact: the alert config already runs
  {1d,1w,1M} rev-only -- the score is the timescale outlier. Deliverable
  written to hip3-scanner/docs/SCORE_METHODOLOGY_DUAL_REVIEW_2026-07-20.md
  (UNCOMMITTED there; that repo's session commits it). GPT's roster-
  contamination framing adopted: week 1 = exit-class grading on
  heat-selected names (state it at week end); week-2 candidate =
  full-universe twin.
- Repo hygiene: pyproject ruff config now explicitly ignores E741 (`l` =
  OHLC low, the codebase-wide bar-row idiom; the committed fixture already
  used it).

### Decisions recorded (user-ratified)

Twin as recorder (TV = eyes + parity reference); roster rule + freeze +
xyz-only; retired-first eviction; v6.1 full bundle deployed same day;
filter-by-gate-yes/rank-no until validated (score compare adjudication).

### Known deltas / open questions

Deferred audit items: last-only supersede search (duplicate-line class,
design question); fixture assertions/interleave (twin engine + goldens are
the parity oracle meanwhile); min_sep holdout-freeze protocol. Carried:
flip-backstop granularity; cross-pool dedup; consumption-while-flat review;
same-bar entry+touch edge. Twin deltas declared in the protocol doc
(anchor resolution, tick-live vs 5m, TV-vs-HL wicks, flat start). v6.1
evict-alive residual is counted and visible (chart 14 at deploy).

### Files created/modified

analysis/paper/{__init__,engine,roster,archive,replay}.py (new);
tests/test_paper_{engine,roster,archive}.py + tests/golden/ (new);
analysis/reference/tvb15_apistate_trimmed.json (new);
analysis/paper/{roster_week1.json,bars/ (33),tvb15_symbolinfo.json,
events_week1.jsonl,scoreboard_week1.md} (new);
scripts/tvb15_symbolinfo.mjs (new);
docs/experiments/tvb15_paper_week1_protocol.md (new);
pine/tfc_bf_watch.pine (v6 -> v6.1, deployed);
docs/reviews/tvb14-codex-audit.md (returned, committed);
docs/reviews/REVIEW_REQUEST.md, docs/HANDOFF.md, pyproject.toml,
.session_startup_prompt.md; sibling workspace:
hip3-scanner/docs/SCORE_METHODOLOGY_DUAL_REVIEW_2026-07-20.md (delivered,
uncommitted there).

### Context for next session

TVB-16 = ride-along refresh (archive+replay MUST run by 2026-07-23; 5m
floor), collect exit-class grades, fold in the TVB-15 review, and -- at
week end -- the parity pass + exit-class report + deferred design
questions + week-2 protocol. The scanner score work happens in the
hip3-scanner workspace; TVB may consume tf.{1d,1w,1M}.formingDir any time.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work
> (range below) and write a verbatim assessment to
> docs/reviews/tvb15-codex-audit.md. See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED 2026-08-04 (NEEDS-CHANGES) -- folded in same day
  by TVB-18; all four findings independently reproduced before adjudication.
  Synthesis: TVB-18 HANDOFF entry + the fold-in section of
  docs/experiments/tvb15_paper_week1_protocol.md.
- Commits to review: `75eba90^..b9b93cb` on `main` (5 commits; the pin
  commit follows outside the range, per precedent). RANGE-PIN RULE: caret
  included; sanity-check `git diff --name-status 75eba90^ b9b93cb`.
- Scope / what changed: the paper-trading twin layer (engine port of the
  live v6/v6.1 Pine + roster/archive/replay + goldens), the week-1 frozen
  artifacts, the TVB-14 audit fold-in with same-day v6.1 fix-forward
  (Pine + engine + regression pins), and the protocol doc.
- Focus areas (scrutinize these): (1) engine-vs-Pine port fidelity
  (per-bar order, collect-before-transition, exit race, corrected arm
  clock, float trigger arithmetic) and the v6.0/v6.1 flag split; (2) the
  golden methodology (fixture goldens + FIXTURE_SUPERSEDE_SHADOWS
  exceptions -- is pinning the engine's own formatter against
  fixture-generated text sound?); (3) v6.1 fix edges: per-side supersede
  interaction with the dup-ghost scan, retired-first eviction under
  sustained alive pressure, Pine array.remove lockstep x13; (4) replay
  conventions honesty (fill prices, last-bar drop, warm-up boundary,
  flat start, 5m confirmed semantics); (5) roster selector rule vs its
  stated a-priori claims; archive merge newest-wins; (6) the audit
  fold-in's own verification claims (census reproductions, roster
  live-impact sweep method -- uncapped-as-truth caveat); (7) deploy
  verification claims (version bump, table parity numbers).
- Reviewed by: Codex CLI (user-run), 2026-08-04
- Findings: NEEDS-CHANGES, 1 HIGH + 3 MEDIUM, all four CONFIRMED by
  TVB-18 reproduction. F1 HIGH: all 18 day-one events predate the 14:31
  roster freeze (selection lookahead); on the final 81-event record, 12/37
  closed trades entered pre-freeze incl. both catastrophic adverse-breaks;
  realized flips -27.60pp -> +14.37pp in the post-freeze-entry slice
  (analysis/paper/freeze_slice.py); the adverse-runner gap SURVIVES (the
  window-end open runners all entered post-freeze). F2: the actual freeze
  source was never preserved (committed snapshot = 13:26:36Z, 65 min
  early); roster.py fails open. F3: coarse 1h/1d warm-up changes lifecycle
  state, not just anchor precision (TSLA 07-16 N=1 lower alive-vs-consumed
  reproduced); delta 1 amended. F4: evict-alive counts fallback formation
  evictions, not alive sides; the "14 vs 13+1=14" parity line above was
  wrong (annotated in place; true day-one twin counter 15).

---

## Session TVB-14: TFC-BF v4->v6 -- rolling compound-3 pools, field-graded same day (COMPLETE)

**Date:** 2026-07-19..20
**Status:** COMPLETE -- the tier-1 exit engine was redesigned with the user,
built, deployed BEFORE the new weekly candle, and then twice field-fixed the
same day from the user's live observations. Three ships: v4 (rolling
compound-3 pool, weekly base), v5 (multi-TF pools 12h/D/W/M + junk filter,
after the user's zero-BF-exit report), v6 (adverse-line break exit, after
the user's CL/WTIOIL case). TV USER;7c28fa0b at v6.0, live on DRAM 5m.

### What was accomplished

- DESIGN (with the user, MU + DRAM screenshots): the BF detection rule is
  the user's sentence mechanized -- at each base-TF close, the envelope of
  the last N closed candles strictly takes out BOTH sides of the prior N's
  envelope (N=1..6 ascending, smallest wins; N=1 = plain scenario 3, N>1 =
  compound 3; R10 strict). No calendars -- month-straddling "atypical
  timeframe" structures found natively. Wick-time anchors ratified (the MU
  "same lines, just switching timeframes" argument; the weekly-column
  hand-draw fork is material: BF2 44.02 wick vs 37.30 column at Jul-20).
  BF2 pinned = the previous weekly 3 (May-25 55.000 -> crash-week 52.788).
- VERIFICATION-FIRST BUILD: xyz:DRAM 1d+1h archived from HL
  (analysis/reference/tvb14_dram_{1d,1h}_hl.json), fixture
  analysis/tvb14_bf_pool_fixture.py replays the pool per base TF; v4's
  drawn lines matched the fixture to the penny (weekly trio incl. the N=4
  compound BORN AT THE JUL-20 ROLL at 48.42, observed 48.414 live).
- v5 (field fix 1): user report "zero BF exits, any ticker" -- structural:
  weekly-only lines sit 15-35% away (SKHYNIX next rung -36%), flip fires in
  days, flips win every race; the June DRAM harvests were 12h/D rungs. Fix:
  four parallel pools (12h/D/W/M toggles, per-pool colors) + the
  min-anchor-separation validity filter (1.0 base periods, a-priori from
  the user's own good-vs-junk examples; naive 12h pool 57 formations ->
  the structural handful matching the hand-drawn ladder 48.4/44.1/41.4/
  39.7/38.8).
- v6 (field fix 2): user CL/WTIOIL case -- sim long rode a crash through a
  lower line with no exit (correct under v5: adverse side never exits on
  touch; flip blocked by monthly-still-up; line consumed silently). Fix:
  ASYMMETRIC EXIT SEMANTICS (canon): harvest side touch = exit (sharp
  bounce takes profit); adverse side exits on the bounce FAILING = a
  confirmed chart-bar close through an alive line ("BF Break L/S Exit",
  toggleable). The user's close-confirmation sketch landed on the side it
  belongs.
- Memory hygiene: retracted day-one churn diagnosis corrected; the
  touch-confirmation supersede honored; roadmap memory tracks v6 state.

### Decisions recorded (user-ratified)

Wick-time anchors; smallest-N; lifecycle alive/consumed(any touch)/crossed/
superseded/ghost; direction-relative exits; asymmetric harvest-touch vs
adverse-break; min_sep 1.0 a-priori (dial live, never tune on backtests);
naming "BF S/L Exit", "BF Break L/S Exit", "Flip S/L Exit".

### Known deltas / open questions

Cross-pool duplicate lines (no dedup yet); weekly UPPER pairs often ghost
under min_sep on young instruments (faster pools supply long rungs);
deep-decayed lines linger alive but unreachable; same-bar entry+touch
consumes without exit (one-bar edge); stranded-line birth can fire one
break exit (one-bar window); flip-backstop granularity (full vs partial
alignment -- the CL monthly-held-it-open case) OPEN; TV-vs-HL wick variance
cents-level on some anchors (TVB-6 class).

### Files created/modified

pine/tfc_bf_watch.pine (v3->v6); analysis/tvb14_bf_pool_fixture.py (new);
analysis/reference/tvb14_dram_1d_hl.json + tvb14_dram_1h_hl.json (new);
.session_startup_prompt.md; docs/reviews/REVIEW_REQUEST.md; this entry.

### Context for next session

TVB-15 = paper-trading protocol for the week (designed with user) + what-
gets-traded via the scanner (https://hip3-alerts-production.up.railway.app/,
/api/state). Alerts must be RE-CREATED on the v6 instance; other layouts
hold older versions until updated. The week grades the three exit classes;
no mid-week tuning.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work
> (range below) and write a verbatim assessment to
> docs/reviews/tvb14-codex-audit.md. See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: ADDRESSED (returned + acted on same day 2026-07-20:
  v6.1 fix-forward for F1/F2/F4/F5, F6 corrected; F3 remediation deferred
  with the twin engine + goldens as the interim parity oracle; synthesis
  in the TVB-15 entry above)
- Commits to review: `b324f80^..bd09895` on `main` (v4/v5/v6 + fixture +
  reference bars; session-end docs commit follows and may extend the head
  -- REVIEW_REQUEST.md pins the final range). RANGE-PIN RULE: caret
  included; sanity-check `git diff --name-status b324f80^..bd09895`.
- Scope / what changed: the tier-1 watch indicator's BF exit engine
  rebuilt (rolling compound-3 pools, multi-TF, lifecycle, three exit
  classes) + the Python acceptance fixture + committed venue bars.
- Focus areas (scrutinize these): (1) the rolling sweep in
  pine/tfc_bf_watch.pine f_pool -- window indexing, smallest-N, novelty/
  supersede/per-side-ghost rules, pool-cap eviction of 13 parallel
  arrays; (2) per-call-site var instantiation of f_pool x4 (Pine
  semantics) and the pos/entry_px prior-bar-state pass; (3) exit
  correctness: direction-relative eligibility (v < entry_px), break-exit
  ordering vs harvest vs flip, same-bar edges, barstate.isconfirmed use
  on historical vs realtime bars; (4) lifecycle consumption-on-ANY-touch
  implications; (5) min_sep filter honesty (a-priori claim vs the
  fixture-derived good/junk boundary -- is it selection-on-sample?);
  (6) zero request.security claim; chart-TF-tiling honesty notes;
  (7) fixture parity method (1h-resolution lifecycle vs 5m chart; TV-vs-
  HL wick variance attribution); (8) the deploy-verification claims
  (version bumps, drawn-line cross-checks).
- Reviewed by: Codex CLI (user-run, 2026-07-20)
- Findings: NEEDS-CHANGES. F1 HIGH supersede-before-ghost silently deletes
  an unchanged still-valid side (TVB-15 reproduced: D F17->F18 upper + 12h
  F23->F24 upper in committed data; live AAPL twin shows a lost D lower at
  -13.9%). F2 HIGH pool_cap evicts alive lines and the fixture omits the
  cap (TVB-15 reproduced the census exactly: 12h 54/42/22, D 27/15/6;
  roster sweep finds evicted-alive rungs at 4-8% on AAPL/MSFT/GOOGL/GOLD/
  TSLA incl. the standing TSLA short's -7.4% harvest rung). F3 MED fixture
  two-pass supersede masks consumed (independently found by TVB-15 the
  same morning; pinned in tests/test_paper_engine.py). F4 MED tiling
  overstatement + silent non-tiling TFs. F5 MED min_sep=1.0 relabel:
  form structural, threshold sample-derived. F6 LOW commit count 5->4
  (corrected). Critical synthesis + fix-forward record in the TVB-15
  session entry.

---

## Session TVB-13: BF comprehension surface + TVB-12 fold-in + give-back v1 (COMPLETE)

**Date:** 2026-07-17
**Status:** COMPLETE -- three arcs: (1) TVB-12 external review RETURNED
(NEEDS-CHANGES) and folded in with every recomputation independently re-run
(synthesis below); the audit's HIGH finding was EXTENDED to all four live
winner watch surfaces and the champion STRATEGY was exonerated (resting stop
orders); user decision: fix-forward, four surfaces FROZEN with header notes,
no redeploys. (2) BF Comprehension [TVB-13] designed WITH the user (two
corrections folded live), BUILT, and DEPLOYED to the DRAM 15m pane (v3.0,
USER;84bb0f1e...) incl. a freeze-as-of fixture tool; the frozen June
screenshots were delivered and the user ACCEPTED ship-as-is (will grade it
live via written-down paper trades; clutter noted, layer toggles are the
mitigation). (3) Give-back instrumentation v1: the DRAM June episode
archived from the Hyperliquid API (floor had already slid to May 26) and
hand-labeled as acceptance tests that reproduce the user's live account to
the decimal (MFE 19.87% at 30.8h, bottom 52.788, realized -1.18%, give-back
21.06pp -- more than the whole peak surrendered); suite 73 passed.
Companion-Pine MFE/MAE surface deferred to TVB-14.

### TVB-12 review fold-in (critical synthesis)

Reviewer: Codex CLI / GPT-5.6 Sol Max (run by the user), LIGHT scope, verdict
NEEDS-CHANGES; audit verbatim in docs/reviews/tvb12-codex-audit.md. Every
recomputation was re-run independently this session before synthesis and all
counts reproduce exactly (raw gate failures all zero, 68 unique nonces,
anchors 3/3, stored verdicts 36 CLEAN / 18 DRIFT / 0 SUSPECT, bounded recount
49/5/0 with 25 right-tail trades removed, fingerprint 1438/241/35, coverage
3.76%, ceiling 248.7007 on both sides, short champion 13.7061%/19tr vs
12.9115%/17tr, Spearman 1.000/0.988/1.000) -- the second consecutive external
audit whose every asserted count reproduced. Agreement/dispute below is ours.

- **C1 winner-surface clocks (HIGH) -- AGREE + EXTEND, with one adjudication
  the audit lacked.** Verified: ShortChamp folds the current bar's low into
  a_low BEFORE assigning prev_al on arm_last bars and tests the trigger
  afterward (winner_shortchamp_mu5.pine:56-61 vs :210-215), so on every final
  child bar the in-bar test `low <= prev_al - tick` is unsatisfiable -- on
  the 5m chart, breaks first occurring in the third 5m child are never
  signaled. The state exit (:204) has no barstate.isconfirmed guard, so
  intrabar grey can flash an exit that the actual 60m close would not
  confirm. ADJUDICATION (the audit did not check the strategy): the champion
  STRATEGY shares the identical snapshot ordering
  (tvb_exp_champion.pine:213-231) but enters via RESTING STOP ORDERS
  (:329/:334) -- an order placed during the final child bar activates on the
  NEXT bar, by which time the period has genuinely completed, and breaks
  during the final child fill from the order rested on the prior bar. The
  backtest therefore implements the advertised contract correctly at every
  child position; the TVB-11/12 measured record is NOT touched by this
  finding. The defect is specific to the in-bar signal replication in the
  watch indicators. EXTENSION (ours, beyond the audit's light scope): all
  three LONG winner surfaces run with chart TF == ARM_TF (generalizer
  a15/15m chart, champion_mu15 a15/15m, slow60 a60/60m), where EVERY bar is
  arm_last -- their entry signal can NEVER fire at all. Three of the four
  deployed live watch surfaces are entry-dead; the fourth (ShortChamp, 5m
  chart) misses ~1/3 of arming windows. ACT: reorder the arm_last roll to
  AFTER the entry evaluation (Pine rollback semantics then give the
  completed-period reference on every child bar including chart == ARM_TF),
  add barstate.isconfirmed to the state exit, add per-child-position
  fixtures, redeploy all four surfaces.
- **C2 comparator (HIGH) -- AGREE, one precision note.** Verified: the code
  implements a start-bound-only overlap plus a scalar 0.8 verdict
  (tvb12_replay_compare.mjs:42-60) while its own header comment and the plan
  describe the semantic boundary test; R4 rows enter the headline counts
  (byTag: R4 = 5 CLEAN / 3 DRIFT) though the plan pre-declared R4 as having
  no reproduction target. PRECISION: the missing common-window END was also
  missing from the pre-registered acceptance text (plan lines 58-69 declare
  only the start bound), so the comparator faithfully implemented an
  under-specified pre-reg; the 0.8 threshold, however, was never
  pre-declared anywhere. The auditor's own bounded recount (49 CLEAN /
  5 DRIFT / 0 SUSPECT; 13 DRIFT->CLEAN; all 25 removed trades are
  replay-side right-tail additions) STRENGTHENS the window-slide reading of
  the drift -- but the audit's point stands: the shipped artifact asserts
  what it should demonstrate. The 3 interior price mismatches are all
  direction=BOTH cells on MU 15m (one R2 control, two R4); path-dependent
  position occupancy (a boundary-shifted exit re-arms the resting stop on a
  different bar -> same entry bar, different level) is the plausible
  mechanism, unproven. ACT: comparator v2 -- common window bounded at BOTH
  ends, one-to-one match consumption, field-complete comparison (quantity,
  exit semantics), DRIFT requires explicit boundary/path attribution else
  SUSPECT, R4 excluded from the headline tally; regenerate compare.json and
  reconcile prose.
- **C3 collector join (MEDIUM) -- AGREE.** Verified: the nonce lives only in
  the Pine table; report<->table binding is the coarse 3-field fingerprint
  (closed count + open count + closed net to a cent,
  tvb12_replay_collect.mjs:329-332); the stability key adds no trade content
  (:338); the report lookup falls back from entity id to exact description
  (:199-211); session/subsession are asserted only for RTH-mirror symbols
  (:316, :322). Collision recount reproduced: 241 multi-id groups / 35 with
  different trade lists across the 1,438 eligible TVB-11 reports. All 68
  committed rows bound by id and pass every recorded check -- the finding is
  the remaining adversarial path, not this batch. ACT (gates the NEXT
  collection run): Pine-side digest over the COMPLETE closed trade list
  echoed in the METRICS table, remove the name fallback (fail loud), assert
  the expected session per symbol class.
- **C4 closure language (MEDIUM) -- AGREE; relabels applied this session.**
  54 compared ids / 1,438 eligible = 3.76%, deliberately targeted, not
  random; the unqualified top-line "record VERIFIED" (TVB-12 status) and
  "no longer taints the conclusions drawn from it" (plan standing verdict 1)
  overreach a targeted subset; Stage B rank stability is proven on the
  HOOD/HIMS/RKLB full blocks only -- the 10-config x 7-perp median ranking
  was not recomputed and the four unrerun competitor medians remain part of
  the original ordering. ACT (DONE 2026-07-17, dated + additive): TVB-12
  status line qualified below; plan standing-verdict correction note added.
  The 736-row provenance gap REMAINS OPEN.

Audit checks co-signed: the short mirror's comparisons/ratchet/harvest are
faithful; the sole executable request.security call uses the accepted
offset idiom; no long-side residue; the collector has no time-based escape;
all four named reproductions (ceiling, short champion, anchors, Spearman)
are real.

### Remediation queue (TVB-13, execution order decided with user)

1. Winner-surface clock fix (C1) -- HIGH, LIVE-RELEVANT: three surfaces
   entry-dead on their nominal charts, one missing final-child entries;
   state exits can flash intrabar. Mechanical and well-specified; needs a
   TV redeploy per surface (tab-binding recipe applies).
2. Comparator v2 + regenerated compare.json + prose reconciliation (C2).
3. Collector digest + no-name-fallback + session assertion (C3) -- required
   before any future collection run; no urgency until one is scheduled.
4. Prose relabels (C4) -- DONE 2026-07-17.
5. Standing from the TVB-11 audit, still pending: Section 12 qualifiers, P3
   relabel, security-rule amendment (F4/F6/F7), NET propagation + fixture
   (F5).

### BF comprehension arc (what was built and why)

- Design doc docs/design/bf_comprehension_indicator_design.md, corrected
  twice with the user in-session: (a) the line is NEVER 3-to-previous-3 --
  TWO modes: adjacent (3's extreme to the immediately previous candle's) and
  compound take-out, which the user then sharpened to the Rob-canonical
  PRICE-PROXIMITY rule (lower line anchors at the nearest prior low slightly
  HIGHER than the 3's low, upper at the nearest prior high slightly LOWER
  than its high; months-back reach = the huge compound 3); (b) fractality
  confirmed as the architecture -- a compound 3 IS a plain scenario 3 on the
  higher timeframe (user's example: 2U-1-2D-2U rev strat-2U daily week = one
  weekly 3), so aggregate detection is just strict classification of real
  HTF candles, firing the instant the second side breaks. Behavioral
  semantics recorded for the exit arc: bounce != reversal; outside a line
  the position is never against us until price re-enters the formation; a
  full line-to-line traversal IS a compound 3 that EXTENDS the formation
  (user quizzed this; the answer is canon).
- pine/bf_comprehension.pine: order-free indicator(); L1 strict-ops chars,
  L2 HTF-3 span shading, L3 compound-3 fire markers + line pairs (both
  anchor modes; aggregate + rolling detection; ladder 60m/4h/12h/D/W/M,
  defaults 12h+D, HTF precedence by width), L4 restart + reclaim levels,
  freeze-as-of input (grade historical episodes with period-true lines).
  Chart-side aggregation, ZERO request.security calls; reference rolls at
  period START then tests (the corrected C1 clock by construction).
- Deployed v3.0 via the first-dialog recipe (a second-session save silently
  failed exactly per the trap memory; one extra TV restart). Frozen June
  fixture screenshots (proximity + adjacent) delivered; copies in
  temporary/tvb13_fixture_screens/. NEW TRAP found and memory'd: jackson's
  indicator_set_inputs CORRUPTS indicator() studies ("Can't parse pine";
  getInputValues returns null on indicators, unlike strategies) -- use the
  study settings dialog UI; recovery = remove + re-add the study.

### Give-back instrumentation (the leak, quantified on the fixture)

analysis/giveback.py (episode MFE/MAE/realized/give-back pp+frac,
distribution summary, CLI) + analysis/reference/tvb13_dram_jun_15m_hl.json
(xyz:DRAM 15m, 2026-05-30..06-15, Hyperliquid public candleSnapshot) +
tests/test_giveback_fixture.py. The mechanical episode definition (entry =
LAST downward cross of 65.88 before the bottom -> 2026-06-04T19:45Z; exit =
first touch of 66.66 after -> 2026-06-14T06:45Z) reproduces the user's live
account exactly: MFE 19.87% (their figure to the second decimal), 30.8h to
the 52.788 bottom ("1d6h"), MAE 1.21%, realized -1.18% ("-1.2% loss"),
give-back 21.06pp with give_back_frac > 1.0. The distribution over champion
trade lists needs a bars archive per symbol -- which is the standing HL
archiving thread (HL's 15m floor was ALREADY at May 26 when captured; the
June episode was days from unfetchable).

### Context for next session

- The user tests BF-COMP live by writing down mental entries/exits; their
  grade + divergences feed the exit-ablation design session. Freeze is ON
  (June 4) on the deployed instance; they can uncheck it in settings.
- The DRAM 15m surface lives in the pane that previously held NQ.
- Companion MFE/MAE Pine surface: deferred, first build item of TVB-14.
- Remediation queue above: comparator v2 (C2) before leaning on DRIFT
  labels again; collector digest (C3) before the next collection run.

### Files created/modified

- docs/design/bf_comprehension_indicator_design.md (new)
- pine/bf_comprehension.pine (new); pine/winner_*.pine x4 (frozen headers)
- analysis/giveback.py, analysis/reference/tvb13_dram_jun_15m_hl.json,
  tests/test_giveback_fixture.py (new)
- docs/reviews/tvb12-codex-audit.md (new, committed), REVIEW_REQUEST.md,
  docs/experiments/tvb12_replay_plan.md (dated correction), this file

### TVB-13 review fold-in (critical synthesis -- post-session addendum, 2026-07-18)

Reviewer: Codex CLI / GPT-5 (run by the user), FULL scope, verdict
NEEDS-CHANGES; audit verbatim in docs/reviews/tvb13-codex-audit.md. The
load-bearing replay (proximity-anchor staleness) was independently re-run
this addendum and reproduced exactly; the audit also re-executed the TVB-12
recomputation block and matched. Agreement/dispute is ours.

- **A1 proximity anchor staleness (HIGH) -- AGREE, defect by construction.**
  The anchor scan runs only on the FIRE bar; later extension of the open HTF
  candle's extremes updates only the line's second endpoint, and the line
  solidifies at the boundary without re-scanning -- so "nearest prior low
  strictly above the 3's low" is evaluated against the fire-time low, not
  the candle's final low. Replay on the committed DRAM bars: 2 of 4 12h
  fires solidify with stale anchors, INCLUDING the June-3 13:30Z fire at
  the fixture entry (fire anchor 68.624 vs rule-correct 67.15) -- the frozen
  proximity screenshot delivered to the user carries this defect. ADJACENT
  mode is unaffected (its anchor never depends on the open candle's final
  extremes) -- the user's live grading should prefer adjacent mode until
  fixed. ACT (TVB-14 fix 1): recompute the affected side's anchor whenever
  its extreme extends + final scan before solidify; fixture asserting both
  fire-time and close-time geometry.
- **A2 C1 narrowing (MEDIUM) -- AGREE; the exoneration itself SURVIVED
  hostile review.** The audit found NO path where an entry stop references
  an uncompleted arm period ("resting stops do cure that specific
  early-snapshot problem at every child position, including chart_tf ==
  arm_tf") and its child-position fill counts disprove any entry-dead
  strategy. The narrowing: a default close-calculated strategy cannot
  cancel/create the pending order intrabar, so the record proves the
  COMPLETED-ARM-LEVEL contract but not a continuously-synchronized live
  gate (pending order can fill after the gate turned neutral at a new
  D/W/M open; a mid-bar gate flip + break yields a delayed next-bar entry).
  This is precisely the ENTRY-ARMING FORK the user already found live on
  EWY (memory project-entry-arming-fork) -- independently re-derived by the
  audit; converged evidence elevates that standing thread. ACT: dated
  narrowing note below (the clock claim stands; the live-gate fidelity
  claim was never established and is now explicitly open).
- **A3 freeze boundary + L1 (MEDIUM) -- AGREE.** `time <= asof_t` admits the
  freeze bar's full OHLC (open-time compare); L1 chars ignore the freeze
  entirely while the table says FROZEN. ACT: time_close-based predicate +
  gate L1.
- **A4 L4 same-bar restart + supersede retraction (MEDIUM) -- AGREE.** The
  `not fired_now` guard makes the cheat sheet's CANONICAL case (outside bar
  closing back inside) one bar late (3 of 8 committed fires); superseded
  lines drop extension without pinning x2, so faded history retracts. ACT:
  same-bar restart eval + pin x2 at supersede.
- **A5 give-back fidelity wording (MEDIUM) -- AGREE.** Arithmetic, long
  mirror, and selector reproducibility all verified by the audit (and the
  committed bars live-matched the HL API, 0 mismatches); the findings are
  labels: MFE/MAE are full-bar-envelope metrics on 15m OHLC (capping the
  exit bar gives MAE 1.184% vs 1.210%), `realized` is GROSS price return
  (no fees/funding -- consistent with the standing F5 NET thread), and the
  retrospectively pinned episode is an acceptance fixture, never validation
  of a candidate rule. ACT: docstring/HANDOFF relabels; keep hand-labeled
  framing.
- **A6 summarize() median (LOW) -- AGREE, real future bug.** Nearest-rank
  with ties-to-even makes median([0,10]) = 0. ACT: statistics.median +
  declared p90 method + even/odd tests before any distribution is read.
- **A7 disclosure bounds (LOW) -- AGREE.** "Exact on 24/7 perps" needs a
  tiling qualifier (a 45m chart straddles 60m boundaries); box/label lack a
  visible provisional->confirmed transition; design doc drift (4900 vs the
  shipped 2000-candle archive; stale "no Pine exists" footer). ACT: header
  qualifier + doc reconciliation.

Co-signed passes (audit verified, we accept): strict R10 everywhere with
equality never breaking; the corrected period-start aggregation clock with
no ordering defect; zero request.security calls; the rolling buffer guard
safe; C4 relabels "pass without a finding"; all four frozen winner-surface
header diagnoses accurate from code; the archive move byte-exact; suite
73 passed under no-cache.

DATED NARROWING (2026-07-18, applies to the C1 adjudication above): "the
TVB-11/12 measured record is NOT touched by this finding" holds for the
ARM-SNAPSHOT CLOCK question the audit raised -- no uncompleted arm level can
reach a fill. It does NOT establish that fills always occur under a
still-aligned gate, nor same-bar entries after mid-bar gate flips; that
live-gate fidelity question is open, pre-existing, and identical to the
entry-arming fork (project-entry-arming-fork). Any future claim leaning on
gate-synchronized entries needs per-fill gate/order-state traces or an
explicit intrabar strategy contract.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb13-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED 2026-07-18 (Codex CLI / GPT-5, run by the user;
  verdict NEEDS-CHANGES; audit in docs/reviews/tvb13-codex-audit.md;
  critical synthesis in the addendum above). Originally REQUESTED at FULL
  scope -- the deep review the user reserved when scoping TVB-12 light.
- Commits to review: `1f53463^..32efec6` on `main` (8 commits incl. the
  session-end docs; sanity-check with
  `git diff --name-status 1f53463^ 32efec6`)
- Scope / what changed: TVB-12 audit fold-in + synthesis; BF comprehension
  design doc + order-free indicator + freeze tool; winner surfaces frozen;
  give-back calculator + archived fixture bars + acceptance tests.
- Focus areas (scrutinize these): (1) pine/bf_comprehension.pine -- strict
  R10 operators everywhere, chart-side aggregation correctness on 24/7
  perps, the proximity anchor scan, freeze semantics, repaint honesty of
  provisional drawings; (2) the TVB-12 synthesis C1 ADJUDICATION -- does the
  resting-stop-order argument really exonerate the champion strategy's
  early arm_last roll at every child position (tvb_exp_champion.pine:
  213-231 vs :327-345)?; (3) analysis/giveback.py + the fixture derivation
  (is the entry/exit pinning method sound; tolerance choices); (4) the C4
  relabels -- do the dated corrections fully cure the overreach the audit
  named.
- Reviewed by: Codex CLI / GPT-5 (user-run), 2026-07-18
- Findings: NEEDS-CHANGES -- 1 HIGH (proximity anchors stale at HTF close;
  verified on committed bars incl. the fixture's June-3 12h fire), 4 MEDIUM
  (C1 narrowed to the completed-arm snapshot -- the exoneration itself
  survived; freeze not boundary-exact + L1 ungated; L4 restart one bar late
  + supersede retraction; give-back = gross full-bar-envelope labels),
  2 LOW (summarize median; disclosure bounds). Synthesis above; fix list
  seeded as TVB-14 priority 1.

---

## Session TVB-12: audit fold-in + fail-closed replay + ShortChamp + EXIT-ARC redirect (COMPLETE)

**Date:** 2026-07-15..16
**Status:** COMPLETE. Four arcs: (1) TVB-11 audit folded in (synthesis below);
(2) bounded replay EXECUTED -- TVB-11 record VERIFIED [2026-07-17 qualifier,
per TVB-12 audit C4: verified on the 54-cell TARGETED subset (3.76% of
eligible ids) -- anchors, named champions, controls, three Stage B full
blocks; the 736-row provenance gap remains open; see the TVB-13 synthesis
above], F1/F4 closed, F2 answered with new direction evidence; (3) "Winner: ShortChamp MU5 [TVB-12]"
live watch indicator shipped premarket (the replay-verified 5m short champion,
the one performer without a live surface); (4) USER REDIRECT at session end:
the TVB-13 mission is EXITS ON WINNERS -- combined-indicator/regime-label arc
PARKED. See "Session-end redirect" below and memory project-exit-arc-tvb13.

### Session-end redirect: the exit arc (user-set, 2026-07-16)

User evidence (10 screenshots on file): DRAM perp June SHORT entered ~65.88
(FTFC-down), ran -19.87% in favor in 1d6h, retraced +25.9% off the ~52.7
bottom, and the strategy exited at 66.66 = a -1.2% LOSS on a +20% open winner,
through ~7 daily pivots + monthly levels taking nothing. A LIVE July short
(+27% open) poses the same question with real capital. User demonstrated the
compound-3 BF exit hand-drawn: line = most recent old scenario-3 candle's low
attached to the PREVIOUS candle's low, extended forward (causal, zero lag,
known in advance) -- the DAILY line harvested ~half the fixture move; the 12H
line (52.79) caught the bottom wick almost to the tick. This is TVB-11's
winning same_side-harvest concept with the causal line replacing the lagged
fractal line. TVB-13: companion MFE/MAE/give-back upgrade, then ONE
exit-ablation pre-reg (controls: flip/state/swing-line BF; candidates:
compound-3 BF ladder, pivot-ladder trim/caution, ATR/% trails). Decisions
reserved for the user listed in .session_startup_prompt.md.

### TVB-11 review fold-in (critical synthesis)

The TVB-11 external review RETURNED (GPT 5.6 Sol Ultra,
run by the user; audit verbatim in docs/reviews/tvb11-codex-audit.md; verdict
NEEDS-CHANGES). Every factual claim below was re-verified against the repo this
session before synthesis; agreement/dispute is ours, not the reviewer's.

### Critical synthesis of the TVB-11 audit (agree / dispute / act)

Reviewer inputs beyond the repo: the user supplied two reference files
(temporary/BF PINESCRIPT ORIGINAL PLUS CLAUDE VERSIONS.txt and temporary/The
Broadening Formation Algorithm.pdf -- a theStrat Lab article defining the BF as
paired HH+LL with continuous redraw). Both are gitignored (verified; the PDF
carries the user's email header and must stay untracked).

- **F1 collector integrity (HIGH) -- AGREE, with two precision notes.**
  Verified: 736/1498 accepted records took the engine path and ALL 736 have
  metrics_table null, so the P2-promised per-run loaded window (prereg line 83)
  is absent for them; echo-path records DO carry loaded_first/last_ms +
  loaded_bars. The engine path's true hole is report-to-config binding: the
  report is located by description prefix (not entity id) and accepted on
  stable + (changed OR >20s) -- no nonce ties the report to the just-applied
  inputs. Precision notes: (a) the audit's "wrong chart TF or subsession can
  pass" sentence applies to the ECHO path (echo string omits chart TF /
  subsession / BF geometry); the engine path DOES verify symbol + interval +
  subsession + all mapped inputs incl. bf_tf. The two paths have complementary
  holes, which is exactly why neither alone suffices. (b) "41 used the timeout
  escape" is an UPPER BOUND: elapsed>20s cannot be distinguished from
  slow-but-changed acceptance because the `changed` flag is not recorded --
  itself part of the evidence gap. Also verified NON-issue: bf_tf cannot stick
  at '60' across cells (A1_FIXED sets bf_tf='30' in every cellInputs). ACT:
  harden collector (nonce echoed through the pine table, full echo incl. chart
  TF/subsession/BF geometry, entity-bound report read, drop the time escape,
  persist applied readback + window + changed flag), then a BOUNDED replay:
  anchors, controls, the three per-TF champions, Stage B finalists. No full
  rerun unless the replay diverges.
- **F2 Stage B all-long (HIGH) -- AGREE, fully verified.** cells_b.json = 140
  rows, 10 unique configs, every one dir=long. The 5m SHORT champion
  (slow3/state/short/ss_ratchet_c a15/x60, +12.9%, 17 trades) is at
  a1.jsonl:343 -- an engine-path/no-window record -- and never rode along,
  despite prereg line 252 ("per-TF champions ride along"). The prereg's own
  Stage B budget (10 configs x 14 symbols = 140, lines 216-217) conflicted
  with that clause and execution silently resolved it by dropping the short.
  Our Section 12 sentence "Stage B carried configs unmodified" is therefore
  misleading as written. ACT: add the omitted short champion + matched
  long/short/both variants of the generalizer config + BF-off control to the
  bounded replay; qualify "Generalizer" as best-of-10-long-candidates until
  it passes.
- **F3 BF not a paired detector (HIGH) -- AGREE on code, PARTIAL on framing.**
  Verified in all three sources (original TFO, BF-1 port, champion port
  414-449/497-513): upper/lower boundaries are created and consumed
  independently; exits fire off whichever single line exists; no paired
  formation is required. The article (user's operative definition) requires
  BOTH expansion facts simultaneously (p.3) + continuous redraw (p.7).
  DISPUTE on framing only: the repo never claimed article fidelity -- the
  BF-1 honest-deltas footer explicitly disclaims STRAT-taxonomy detection,
  and BF geometry (30m/10) was a FIXED a-priori axis, so "full mechanism
  space" (prereg preamble) overreaches on the BF axis but the sweep itself
  was honest about what it toggled. The finding's real force: what we measure
  as "BF" diverges from what the user MEANS by BF, and the ~5-5.5h pivot
  confirmation lag is disclosed but material. CONVERGENCE: the audit's
  "specify the detector" prescription lands on the already-planned compound-3
  BF redesign (memory: project-compound3-bf-redesign -- causal BF drawn the
  moment the compound 3 fires, killing the pivot lag). ACT: fold F3 into that
  design-WITH-user session (strat-methodology gate applies); the article's
  ROC-of-ATR adaptive pivot length is a pre-registrable branch, frozen per
  candidate; hand-labeled fixtures for paired-vs-independent validation.
- **F4 P3 "strictly stronger" (MEDIUM) -- AGREE.** Cross-script equivalence
  cannot detect a bug shared by both scripts and does not anchor the expired
  E2 window; the prereg's "STRICTLY STRONGER" is an overclaim (the amendment
  is otherwise honest and the 3 records ARE trade-for-trade equal). Verified:
  runAnchor2 comment says base inputs "already verified applied" but no
  appliedExpr readback runs against the base entity. ACT: dated relabel to
  "narrower current-window cross-script equivalence"; re-run under the
  hardened collector with entity-bound readback on BOTH studies.
- **F5 NET propagation (MEDIUM) -- AGREE, verified.** tfc/simulator.py arms
  the governor on gross (lines 12-13, 168-170) and documents the superseded
  TVB-7 GROSS fact; tfc_companion.pine computes gross_win from prices only
  (369-374) and cites TVB-7 (101-102); docs/VBT_BREADTH_PORT_PLAN.md still
  says gross. TVB-11 flagged the parity risk but flag != fix. ACT: dated
  supersession notes + NET propagation where parity is intended + a
  marginal-trade fixture (gross>0, net<=0) that must agree across Pine /
  companion / Python before any Claude-lineage parity claim.
- **F6 promotion leak (MEDIUM) -- PARTIAL AGREE.** The Section 12 verdict
  paragraph is heavily hedged ("worth exactly nothing more than that",
  deployment forbidden) and the audit acknowledges the indicators were
  pre-authorized. But "Winner:" naming + "single most portable" now rest on
  an all-long roster with unproven collector binding, so the labels outrun
  the evidence. Section 12's integrity sentence also presents both acceptance
  paths as equivalent, which F1 disproves. ACT: qualifier edits in Section 12
  (dated, additive -- raw results untouched); keep the no-deployment rule
  explicit. The user's planned $100-200 micro-deployment is their own
  loss-tolerable live test (memory: project-live-micro-deployment-plan) and
  is NOT licensed by the champion search -- restate, not renamed away.
- **F7 request.security rule (LOW) -- AGREE.** Verified: exactly 4 executable
  calls, all `expr[1] + lookahead_on` -- TradingView's documented
  non-repainting HTF idiom (confirmed values, one-HTF-bar latency). The
  blanket "every call uses lookahead_off" rule (pine/README.md rule 3;
  project CLAUDE.md Section 6) contradicts accepted code. The TRAP remains
  un-offset lookahead_on (TVB-1's original TFO finding). ACT: amend both
  rules to forbid un-offset lookahead_on and explicitly allow the offset
  idiom, noting the latency cost.

Audit checks that PASSED and we co-sign: 60m BF-off trading no-op, P0b NET
arithmetic (reviewer recomputed all 11 C3 rows to 1e-12), window-confound
prose, P3 observed equality (narrow). Overall: the audit is high quality;
every count it asserted reproduced exactly. NEEDS-CHANGES accepted. The
champion-search RANKINGS are treated as unverified-pending-replay; the
process catches (session forcing, checkpoint design) stand.

### Remediation queue (decide-with-user before execution)

1. Collector hardening + bounded replay (F1/F4; enables F2's replay cells).
   -- EXECUTED 2026-07-16 (user-approved): see below.
2. Stage B direction repair cells + Generalizer relabel (F2). -- direction
   cells EXECUTED 2026-07-16; relabel/doc edits still pending.
3. Doc/label edits: Section 12 qualifiers + P3 relabel + security-rule
   amendment (F4/F6/F7) -- cheap, no reruns. PENDING.
4. NET propagation + fixture (F5). PENDING.
5. BF paired-detector design session == the compound-3 redesign (F3).
   -- design DOC drafted 2026-07-16 on worktree branch
   worktree-agent-aba898ce6f7f356c9 (docs/design/bf_paired_detector_design.md,
   11 open questions); design session with user pending; merge after review.

### Bounded replay EXECUTED 2026-07-16 (audit F1/F2/F4 closure)

Full record: docs/experiments/tvb12_replay_plan.md (plan + results) with raw
JSONLs and comparator output beside it. Headlines:

- 3/3 anchors + 68/68 cells accepted through a FAIL-CLOSED gate (per-run nonce
  echoed by the Pine table + entity-bound applied readback + closed-side
  report<->table binding; no time escape); zero rejections, all first-attempt.
- TVB-11 record VERIFIED on the replayed subset: 36 CLEAN / 18 DRIFT /
  0 SUSPECT vs originals; all drift is window-slide shaped; ceiling +248.70%
  reproduces to the decimal; 5m SHORT champion (+13.7%) is real; Stage B
  finalist rank order Spearman 0.988-1.000. The champion-search rankings
  stand.
- ROOT CAUSE of TVB-11 echo flakiness found and fixed: strategy tables gated
  on barstate.islast never draw on 24/7 perps (a realtime bar always exists;
  no-tick strategies never calculate it). v2 harness draws on
  islastconfirmedhistory + last-bar fallback -- display-only.
- Direction repair (new evidence, no promotion): the 5m short champion is
  direction-specific (long -8.7% on the same config); on the 15m generalizer
  config, SHORT beats LONG on 3/7 roster perps (RKLB +43 / ORCL +18 / NFLX
  +12) -- precisely the symbols where the all-long Stage B scored weakest;
  BOTH is not LONG+SHORT (HIMS interaction); SILVER negative in all
  directions (out-of-family confirmed direction-robust). Direction is a live
  per-symbol axis; future breadth stages must carry long/short/both.
- New artifact: "TVB-EXP Champion [TVB-12r]" study (script TVB-12r4,
  USER;e9873a6d...); anchors prove it behavior-identical to the E2 lineage.
  Pine tab-binding trap SHARPENED (memory updated): saves persist only in the
  FIRST Pine-dialog session per TV launch; "Add to chart" compiles the SAVED
  version, not the buffer; verify saves by the version bump.
- User chart state restored: NASDAQ:MU session preference back to '24h',
  chart back to DRAM 15m.

### Files created/modified (TVB-12)

- docs/reviews/: tvb11-codex-audit.md (committed), REVIEW_REQUEST.md
- docs/experiments/: tvb12_replay_plan.md (plan + RESULTS), tvb12_replay_
  {run,anchor2,anchor2_gatedebug}.jsonl, tvb12_replay_cells.json,
  tvb12_replay_compare.json
- pine/: tvb_exp_champion.pine v2 (nonce echo + realtime-bar table fix),
  winner_shortchamp_mu5.pine (NEW, deployed USER;b70672d9...)
- scripts/: tvb12_replay_collect.mjs (fail-closed), tvb12_replay_compare.mjs
- Unmerged branch worktree-agent-aba898ce6f7f356c9: docs/design/
  bf_paired_detector_design.md (BF design doc, 11 open questions -- merge
  after user review; fold in the answered compound-3 geometry)
- docs/HANDOFF.md, .session_startup_prompt.md

### External Review (for Codex / cloud review agents)

> Review THIS session's work and write a verbatim assessment to
> docs/reviews/tvb12-codex-audit.md. See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED 2026-07-17 (Codex CLI / GPT-5.6 Sol Max, run by the
  user; verdict NEEDS-CHANGES; audit in docs/reviews/tvb12-codex-audit.md;
  critical synthesis in the TVB-13 entry above). Original request: LIGHT
  SCOPE by user decision -- this session was mostly verification; the TVB-13
  exit implementation gets the full review.
- Commits to review: `f97646e^..` HEAD-at-session-end on `main` (f97646e =
  review fold-in, first TVB-12 commit; head = the session-end docs commit;
  verify with `git diff --name-status`). RANGE-PIN RULE: the caret keeps
  f97646e inside the diff.
- Focus areas: (1) winner_shortchamp_mu5.pine -- is the long->short mirror
  faithful (state exit on NOT gate_dn, ratchet_c lowered via math.min, strict
  break of prev completed 15m low, block cleared only on full OPPOSITE
  alignment)? (2) tvb12_replay_collect.mjs fail-closed gate -- any acceptance
  path left that is not causally bound? (3) tvb12_replay_compare.mjs method --
  is CLEAN/DRIFT/SUSPECT sound, esp. matched-fraction thresholds? (4) the
  HANDOFF/plan-doc claims vs the raw JSONLs (does "record VERIFIED" overreach?).
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb12-codex-audit.md exists)

---

## Session TVB-11: BF-exit experiments, GPT blind replication, CHAMPION SEARCH executed end-to-end (COMPLETE)

**Date:** 2026-07-10..15 (champion search 07-14/15)
**Status:** COMPLETE -- the deliberate-overfit champion search (pre-registered,
user-approved) ran all three stages on one anchored artifact; the in-sample
ceiling and its generalization gap are now measured controls; three minimal
winner indicators shipped for the user's live watch.

### What was accomplished

Early ticket (07-10..12, recorded here for completeness): TVB-10 review folded
in (RETURNED, APPROVE-WITH-NITS, 3 LOW -- all resolved); Companion v5
(intrabar entry-arming watch); BF-deviation exit experiment arc E0/E1/E2
(`docs/experiments/tvb_exp_bf_exit_2026-07-10.md`); GPT blind replication +
448-run sweep (reports committed 07-14); ratchet-semantics fork discovered.

Champion search (07-14/15), `docs/experiments/tvb11_champion_prereg.md`:
- Pre-reg drafted, user-APPROVED v1.1 (Stage C scalp satellite optional,
  winner-indicator deliverables added at approval). New standing rules
  ratified: underlying-RTH mirror rule (every perp symbol gets a paired
  regular-hours equity run; silver exempted to a SIL1! venue-fidelity
  mirror), weekend-ablation directive (own future pre-reg), plain-language
  results rule.
- Prep gates, all green and evidenced: P0a ratchet fork adjudicated FROM
  SOURCE (ratchet_c = raised stop, ratchet_g = arming gate; both swept as
  named toggles); P0b `closedtrades.profit()` proven NET of commission
  (direct per-trade arithmetic; TVB-7 "GROSS" calibrated fact CORRECTED,
  VBT-port marginal-trade parity flagged); P1 harness (ratchet_g port +
  session-robust clocks + collector echo); P2 collector (echo-first/
  engine-fallback integrity gate, load-to-floor, checkpoint/resume); P3
  anchor REDESIGNED (data floor slid past May 1; E2 numbers unreachable) to
  cross-script trade-for-trade equivalence -- PASS on C1/C3/C6, which also
  proved the clock swap behavior-identical on perps; C4 ratchet separation
  PASS (timing-level, counts below data floor).
- Bugs found BY the process (all pre-run or fail-loud, none contaminating):
  wall-clock modulo period closes never fire on RTH charts (mirror rule's
  first catch, before any run); unconditional BF guard killed all 60m cells
  (BF axis collapses to off on 60m -- structural; neutralized via bf_tf
  input, artifact unchanged); x240 exit clock infeasible with 60m-containing
  gates; NASDAQ:MU chart carried a 24/5 OVERNIGHT session preference
  (Sunday-8pm entries -- C3 mirror gate caught it; collector now forces +
  verifies 'regular' subsession; contaminated probe purged).
- Stage A1: 1308/1308 cells (654 MU perp + 654 NASDAQ:MU RTH mirror), zero
  unexplained rejects; survived a mid-run PC restart with zero accepted-run
  loss (checkpoint design). Stage A2: 60/60 -- regime layer inert TO THE
  DECIMAL on champion configs; governor value VENUE-SIGNED (helps perp chop
  9/10, taxes mirror trend 8/10); ranking stable. Stage B: 130/140 across
  the ratified roster (SIL1! unresolvable on this TV instance, 10 cells
  deferred).
- RESULTS (pre-reg Section 12): ceiling +248.7% perp 15m (slow3/flip/long/
  BF-harvest-recycle, plateau) and +766% mirror 60m (3yr window, knife-edge);
  generalization gap ceiling -> +3..6% median across 7 roster perps; best
  generalizer = slow3/flip/long + BF harvest + ratchet_c (+5.8% median, 6/7
  positive) = the E2 intended-live-system shape; exit-mode verdict INVERTS
  by venue (perp medians state>flip; mirror flip +101% vs state -12%);
  SILVER perp uniformly negative (out-of-family). Scorecard: E1/E3/E4
  confirmed, E5/E6 REFUTED (surprises flagged), E2 partial. NO promotion --
  the ceiling is a ruler.
- Deliverables shipped: three minimal winner indicators (Champion MU15,
  Generalizer, Slow60) deployed via Make-a-copy, stamp-audited, live on the
  chart with const-name alertconditions; sources in pine/.

### Context for next session
- User is reading results and watching the winner indicators live (their
  stated preference: live conditions after backtesting). Live micro-
  deployment ($100-200) planned soon -- live-relevant fidelity items stay
  elevated.
- The champion artifact in TV is the ORIGINAL deployment; the conditional-
  guard fix lives only in the repo (TV re-saves after editor reopen silently
  no-op -- new tab-binding-trap facet in memory; redeploys need fresh
  Make-a-copy).
- Deferred: weekend ablation pre-reg, Stage C scalp satellite (own PRE-RUN
  amendment), SIL1! entitlement question, VBT governor parity re-check,
  Korea-cluster tests.

### Files created/modified
- docs/experiments/: tvb11_champion_prereg.md (pre-reg + amendments +
  results), tvb_exp_bf_exit_gpt.md + tvb_exp_bf_sweep_gpt.md (committed),
  tvb11_champion_{anchor,anchor2,ratchetsep,a1,a2,b}.jsonl,
  tvb11_champion_cells_{a1,a2,b}.json
- pine/: tvb_exp_champion.pine, winner_champion_mu15.pine,
  winner_generalizer.pine, winner_slow60.pine
- scripts/: tvb11_champion_collect.mjs
- docs/HANDOFF.md, .session_startup_prompt.md, docs/reviews/REVIEW_REQUEST.md

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb11-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED 2026-07-15 (GPT 5.6 Sol Ultra; verdict
  NEEDS-CHANGES; audit in docs/reviews/tvb11-codex-audit.md; critical
  synthesis in the TVB-12 entry above)
- Commits to review: `0561c53^..0a1d26a` on `main` (30 commits, 31 files;
  verified via `git diff --name-status`). RANGE-PIN RULE (Codex TVB-4
  finding 1): git ranges EXCLUDE the left endpoint, so the caret keeps
  0561c53 (first ticket commit) inside the diff.
- Scope / what changed: BF-exit experiment arc + GPT replication reports;
  champion-search pre-reg, harness (Pine), collector (CDP batch runner),
  three grid stages + results; three winner indicators; TVB-7 profit()
  calibrated-fact correction.
- Focus areas (scrutinize these): (1) collector integrity gates -- is the
  echo-first/engine-fallback settle gate actually sufficient against stale
  reads? (2) the P3 anchor REDESIGN (cross-script equivalence replacing E2
  reproduction) -- is it truly stronger, and is the record honest? (3)
  results Section 12 -- does any sentence promote beyond the evidence?
  window confounds stated everywhere? (4) profit() NET verdict -- arithmetic
  and its propagation (TVB-7 memory correction, VBT-port flag); (5) the 60m
  BF-guard input-neutralization no-op claim; (6) request.security audit on
  the new Pine (BF engine lookahead_on [1] idiom in 4 scripts).
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb11-codex-audit.md exists)

---

## Session TVB-10: Exit-symmetry ablation + companion v3-v4.1 + entry-arming fork found live (COMPLETE)

**Date:** 2026-07-08
**Status:** COMPLETE -- pre-registered exit-mode sweep run and recorded;
companion upgraded three times; session ends with a USER LIVE FINDING that
sets TVB-11's agenda (entry-arming fork). Fable 5 session, ended at ~4%
weekly budget.

### What was accomplished
1. **Motivating observation (user, 16 CL screenshots)**: Jun-11 -> Jul-6 was
   ONE FTFC-Down regime on the TFO indicator but the strategy logic produced
   58 short entries (zero longs); April chop = 8 entries vs 4 FTFC flips,
   clustered at the monthly open ("flip line").
2. **TVB-10 exit-symmetry pre-registration** (drafted, amended, APPROVED;
   datasheet): `TFCConfig.exit_mode` state|flip -- state-stop exits on FIRST
   loss of full alignment, flip-stop only on full OPPOSITE alignment. 60m
   grid only; gov cells kept; dual closed+MTM accounting; CLUSDC.P deferred.
   Check C2 was mis-derived in the draft (entry-subset invariant) and
   amended PRE-RUN to the one-per-regime invariant, with the error recorded
   honestly (flip exits fill at the open AFTER the first opposite-aligned
   close, so flip entries LAG the state arm's).
3. **288-run sweep executed** (`scripts/tfc_exit_sweep.py`, artifact
   `tvb10_exit_results.json`; committed pulls only; state arm reproduced
   TVB-9 EXACTLY; C1/C2 clean). Headline: **exit symmetry is a regime-shape
   bet, not a churn fix.** Flip rides bursts (MU ctrlA +15.2 -> +136.7 at
   0.0125/s1, n=19; BTC +3.6 -> +26); state harvests swings (MSTR ctrlA
   +45.9 vs flip -22.1 -- even at ZERO fee +64.4 vs -21.4: state's churn
   dodges real damage); whipsaw punishes flip (CRCL E3only -9.6 -> -42.2).
   Cadence collapse is GATE-SET-SPEED-dependent: ctrlA flip/state ratio
   median 0.068 (~15:1, matches the CL observation); E3 ~0.7. Governor is
   structurally INERT under flip (ratchet resets on its own exit event;
   CRCL +11.75pp -> -0.70pp). MU shorts WORSE under flip (-49.3 -> -60.4
   E3only short-only) -> long-only motivation now EXIT-MODE-ROBUST. Median
   MAE inflates 7-8x under flip on slow gates (MU L_surv 7.3 -> 5.4). NO
   promotion (flip cells n=8-42, in-sample, young listings).
4. **Diagnostic D1** (`analysis/flipline_distance.py`, artifact
   `tvb10_flipline_distance.json`): flip-line clustering of losers WEAK
   (22/36 cells, symbol-local, <20bp effects) -> dead-band candidate PARKED.
5. **Companion v3 -> v4 -> v4.1** (`pine/tfc_companion.pine`, deployed to TV
   script "TFC Companion [TVB-10]"): v3 = exit_mode toggle for the user's
   two-instance state-vs-flip live watch; v4 = user's Claude-Desktop UX
   rework merged (quick-start header, tooltips on every input, signal
   boxes, A+ grading, color/table customization) -- now the STANDING STYLE
   for all Pine scripts (memory: feedback-pine-script-ux-style); v4.1 =
   mobile table compaction (disabled TFs dropped, per-section toggles,
   ratchet row auto-hides). STRATEGY slot untouched (pv20 anchor intact).
   Standing rule adopted: companion syncs with every strategy-logic change.
6. **END-OF-SESSION USER FINDING (sets TVB-11)**: tracked a would-be bad
   losing position on EWY with the latest logic + a full day of watching:
   the strategy still churns far more than the original TFO indicator. The
   user's CL reference was 1M/1W/1D/4H/1H stacked, NO regime layer,
   entering the INSTANT of alignment (intrabar) -- our engine arms only at
   strategy-TF CLOSE. This contradicts the original indicator AND the
   charter's own 2U-timing doctrine. Decomposition: exit mode (tested,
   TVB-10), entry arming close-vs-intrabar (UNTESTED -- promoted from the
   parked net-arming carry to next pre-reg), stack depth/composition
   (UNSWEPT -- 5-TF no-regime mirror cell belongs in the same pre-reg).
   Fidelity warning for the ablation: the gate is a reversible threshold;
   intrabar arming cannot be simulated faithfully from 1h bars alone
   (needs committed LTF pulls or explicit best/worst-case bracketing).

### Context for next session
- `.session_startup_prompt.md` carries the full TVB-11 plan (entry-arming +
  stack-depth pre-reg is priority after review fold-in).
- Housekeeping for user: TV library script "Price Level Alerts (Interval
  Bands)" contains companion v2 source (pre-existing; original likely lost).
- Codex reviews tvb8 AND tvb9 still unreturned; tvb10 now also REQUESTED.

### Files created/modified
- `tfc/config.py` (exit_mode field + guard), `tfc/simulator.py` (Phase-B
  exit branch; equivalence gate stayed 8/8, state arm == TVB-9)
- `scripts/tfc_exit_sweep.py` (NEW), `analysis/flipline_distance.py` (NEW)
- `analysis/reference/tvb10_exit_results.json`,
  `analysis/reference/tvb10_flipline_distance.json` (NEW artifacts)
- `pine/tfc_companion.pine` (v2 -> v4.1)
- `docs/TVB2_control_AB_rerun.md` (TVB-10 pre-reg, C2 amendment, results,
  companion deployment records)
- `.session_startup_prompt.md`, `docs/HANDOFF.md`,
  `docs/reviews/REVIEW_REQUEST.md` (session end)

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb10-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED (2026-07-08, `docs/reviews/tvb10-codex-audit.md`)
- Commits to review: `af27900^..258dfb3` on `main` (9 commits, incl. the
  session-end docs commit 258dfb3). RANGE-PIN RULE (Codex TVB-4
  finding 1): git ranges EXCLUDE the left endpoint, so pin `{first}^..{head}`
  (note the caret). Sanity-check: `git diff --name-status <range>` must list
  every file the session touched.
- Scope / what changed: exit_mode (state|flip) added to config+simulator;
  288-run pre-registered exit-symmetry sweep + D1 flip-line diagnostic;
  companion indicator v3-v4.1 (Pine, INDICATOR slot only -- strategy slot
  pv20 untouched).
- Focus areas (scrutinize these): exit_mode branch correctness + exit-fill
  lag; the PRE-RUN C2 amendment (honest? is the one-per-regime invariant
  right?); regime-shape interpretation vs promotion on n=8-42 cells; D1
  nan-filtering and within-cell comparison validity; companion v4.1 gate
  parity with the simulator (no request.security claim, [1]-committed
  reads, alertcondition const strings); mtm_net_pct open-trade marking.
- Reviewed by: Codex CLI / GPT-5 -- APPROVE-WITH-NITS (3 LOW; no BLOCK/NEEDS-CHANGES)
- Findings: (1) C1 governor-inertness wording too strong for AMD flip rows
  (real-fee +2.82pp slightly exceeds the 2.5pp gov drift band); (2) companion
  header/tooltip still says strategy is net-of-fees while it now classifies
  governor wins/losses GROSS -- stale user-facing guidance, not a behavior bug;
  (3) TVB-10 MAE/L_surv flip overlay lacks a committed TVB-10-specific
  artifact (leverage overlay defaults to exit_mode=state).

**Critical synthesis (TVB-11, agree/dispute/act):** All three findings ACCEPTED;
none is a code bug and none blocks TVB-11 work.
- **F1 (C1 wording) -- AGREE, act now (wording).** The numbers are right: AMD
  real-fee flip gov deltas (+2.82pp) do exceed the carried 2.5pp gov drift band,
  so "structurally inert under flip" was too absolute. Corrected reading:
  governor is *mostly inert / no longer a major lever* under flip, with small
  AMD residuals from exit-fill-bar close state. Future sweeps that keep C1 as a
  formal check must report pass/fail against the declared 2.5pp band, not prose.
  APPLIED to datasheet point 6 (TVB-11).
- **F2 (companion tooltip) -- AGREE, DONE THIS SESSION (companion v5).** Code
  classifies gross correctly; only the header/tooltip still described net-of-fees
  ratchet divergence that cannot occur at the gross-profit boundary. Fixed in the
  same companion arming-mode touch (INDICATOR slot: header Fidelity note + gov
  tooltip now say BOTH display and strategy classify GROSS); strategy-slot pv20
  comment fix stays queued separately.
- **F3 (MAE/L_surv evidence gap) -- AGREE, sharpest nit -- RESOLVED THIS SESSION.**
  The leverage overlay built `TFCConfig(...)` with no `exit_mode` -> defaulted to
  state, so the datasheet's "MU L_surv 7.3 -> 5.4 under flip" line was NOT a
  committed flip-mode artifact the way net/MTM and D1 are. FIX: added
  `--exit-mode {state,flip,compare}` to `analysis/tfc_leverage_overlay.py` (state
  default reproduces TVB-9 exactly; +median_mae_pct) and committed
  `analysis/reference/tvb10_exit_leverage_overlay.json` (compare, 36 rows). It
  reproduces every datasheet number to the decimal: MU ctrlA L_surv 7.30->5.36,
  worst-MAE 8.69->13.67, median 0.53->4.44; MSTR ctrlA median 0.51->3.70; AMD
  E3only worst-MAE 7.65->6.55. The claim was HONEST, just un-pinned; now pinned.
  Bonus: the L_surv collapse is concentrated in the slow ctrlA gate (fast
  E3only/R1E3 cells barely move under flip).
- **Process (reviewer meta-suggestion) -- ADOPT.** Add an explicit "evidence
  inventory" line to REVIEW_REQUEST.md next session-end: each pre-registered
  check paired with the exact committed artifact/script that proves it. Would
  have surfaced the F3 gap before review.

---

## Archived sessions

TVB-0 .. TVB-9 (bootstrap; baseline + A/B fee characterization; TV MCP
reader fix + fee saga; stale-gate fix + corrected controls; two-layer
regime + stand_aside; TF-set sweep; xyz backfill + governor v2; governor
cross-venue + VBT port plan; VBT breadth port equivalence gate; breadth
regime map + leverage overlay) are archived VERBATIM in
docs/session_archive/HANDOFF_TVB0-TVB9.md.
