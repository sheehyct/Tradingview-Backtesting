# HANDOFF -- tradingview-backtesting

> Newest session entry at the TOP. Keep under 1500 lines; archive older entries to
> `docs/session_archive/` when it grows past that.

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

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb13-codex-audit.md.
> See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: REQUESTED (FULL scope -- the user reserved the deep review
  for the TVB-13 implementation when scoping TVB-12 light)
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
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb13-codex-audit.md exists)

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

## Session TVB-9: Phase 5 complete -- drift pilot, breadth regime map, digs, HTF cells, leverage overlay (COMPLETE)

**Date:** 2026-07-07
**Status:** COMPLETE -- the entire Phase-5 arc plus three user-directed
extensions ran in one session, every run pre-registered or diagnostic,
everything pushed. Fable 5 session (the startup prompt expected Opus 4.8;
flagged and proceeded).

### What was accomplished
1. **Phase 5a -- venue-bar drift pilot** (`analysis/tfc_hl_pilot.py`,
   artifact `tvb9_hl_pilot_MSTR.json`): same simulator/configs/window on TV
   chart bars vs HL venue candles (committed TVB-6 1h pull = the HL source;
   a fresh fetch floors at Dec-10, so the committed evidence is
   irreproducible -- verified live, 0 mismatches on 4,922 interior overlap
   bars). **Drift band: -0.5..-1.3pp of net, trade identity >= 99.2%**;
   mechanism = a handful of substituted trades at zero-volume-placeholder
   boundaries (HL emits flat v=0 candles, TV omits them). BINDING reading
   rule: |net| < 1.5pp (gov 2.5pp) is sign-indeterminate at bar-source
   resolution. Gate anchors re-asserted before any pilot read.
2. **Breadth pre-registration APPROVED by user** (4 decision points, all as
   recommended) and committed BEFORE runs: universe {MSTR anchor, XYZ100,
   SP500 null, BTC dead control + a-priori adds MU/AMD/NVDA/TSLA/CRCL;
   DRAM skipped}, cells {ctrlA, E3only (approved add -- makes containment
   falsifiable), R1E3, R1E3gov2} x {0, 0.0125} x {s1, s10}; mintick = TV
   symbolInfo via CDP (primary), qty_step = 10^-szDecimals (HL meta); raw
   candles committed (~7MB, sliding-cap rationale); expectations 1-9 first.
3. **Phase 5b -- runner + 144-run sweep executed**
   (`scripts/tfc_breadth_sweep.py`, `scripts/tvb9_symbolinfo.mjs`, artifacts
   `tvb9_breadth_results.json` + 9 committed 1h pulls + `tvb9_symbolinfo.json`).
   MSTR anchor inside the drift band (runner verified). **Regime map:** edge
   at real fees only in high-vol trend regimes (MSTR +45.9 ctrlA, AMD +31.6);
   <40% realized vol = dead zone (SP500/XYZ100 gross ~0); containment
   CONFIRMED 6/6 where E3only negative AND costs upside 3/3 where positive
   (insurance, not alpha); CRCL gov2 +11.75pp = the only non-inert governor
   delta. Surprises flagged: BTC ctrlA +3.55 (small positive, bear window);
   TSLA E3only +9.4 lone inversion; XYZ100 "between BTC and MSTR" prior
   REFUTED on ordering (mechanism intact).
4. **Mechanism digs** (diagnostics, recorded in the datasheet): CRCL
   governor delta = 17 blocked re-entry losers (-12.4 log-pp, 29% win)
   spread EVENLY across months (continuous whipsaw, vs xyz's episodes);
   MU-vs-AMD E3only divergence = SHORT-side asymmetry (MU shorts -71.2
   log-pp vs longs -9.0; long-only +1.3 vs short-only -49.3; AMD positive
   both sides) + burst concentration (MU top-10 HOURS = 49% of +260% b&h).
5. **HTF-index exploration (user hypothesis), pre-registered H1-H5 then
   108 runs** (`scripts/tfc_htf_sweep.py`, `tvb9_htf_results.json` + 9
   committed native-1d pulls): M/W/D as the entry/exit layer on 240m/1D
   charts. H1 confirmed (median |pp| 20-160x the fee floor at D); **H2
   REFUTED -- the dead zone is SIGNAL-structural, not resolution-structural**
   (XYZ100 worsens as horizon stretches, gross negative at D with fees
   immaterial; SP500 stays noise). H3 confirmed (MU MWD_onD +69.8 -- daily
   bars cannot see the intraday short whipsaw). H4 refined: BTC native-1d
   5.9y +73.7% = lumpy regime harvest (2025 -36.8 log-pp; shorts -48.4 vs
   longs +103.6). SHORT-SIDE WEAKNESS now observed 3x -> long-only ablation
   = best-motivated future pre-registered candidate. State-stop give-back
   scales with bar size (charter S3.5 tradeoff made visible).
6. **Leverage-extreme overlay + $500 account** (user request;
   `analysis/tfc_leverage_overlay.py`, `tvb9_leverage_overlay.json`):
   MAE-clearance vs HL isolated liquidation (x_liq = 1/L - mm, live maxLev
   per symbol), post-processing on trade lists -- gated simulator untouched.
   Findings: survival-edge L destroys wealth even without liquidation (vol
   drag; MSTR ctrlA $729@1x vs $535@8.4x); **sample-Kelly ~ HALF of L_surv**
   on real-edge cells (MSTR ~4.4, AMD ~5-5.8), ZERO elsewhere; $500 at venue
   max dies fast (SP500@50x = $25k notional, liquidated at trade ~26-33;
   30/36 cells -> $0); L_surv anti-correlates with vol (max safe leverage is
   highest where nothing is worth levering). All in-sample by construction;
   funding (linear in L) un-modeled and flagged.
7. TVB-8 external review: still REQUESTED, no audit returned; proceeded per
   user decision (fold in whenever it lands).
8. **ADDENDUM (post-session-end, user request): TFC Companion indicator**
   (`pine/tfc_companion.pine`, Pine v6 `indicator()`): manual-trading port
   of the baseline -- verbatim gate/guard/regime code, plus a position-state
   machine replicating the strategy's fills/exits/governor with NO equity
   model (valid because the trade sequence is fee-independent and the
   governor arms on gross, TVB-7). Shows armed trigger, sim entry/exit
   markers, ratchet levels, per-TF status table; alertcondition()s (entry
   fills "Once Per Bar", close decisions "Once Per Bar Close"). Defaults =
   R1E3 two-layer (user choice). strat-methodology skill invoked; TVB-1
   close-vs-period-open reconciliation governs. Compiled CLEAN via MCP in a
   NEW editor slot (slot verified blank before injection -- TVB-1 lesson;
   the pv20 baseline strategy slot untouched; saved in TV as "TFC Companion
   [TVB-9]"). Known port deltas vs the strategy, both deliberate: ratchet
   captured from the armed stop_price (identical value, simpler plumbing);
   fills use float high+mintick exactly like the Pine strategy (the Python
   tick-space lesson does not apply -- this mirrors Pine, not the dumps).
   NOTE: TV had been relaunched by the user WITHOUT CDP (chart NYMEX:MCL1!
   5m, their manual layout) -- kill-first relaunch flow used; their chart
   symbol/layout untouched; TV left RUNNING with CDP.
   **v2 (same session, user-approved): logic-TF decoupling.** New 'Strategy
   TF' input (default 60): decisions (gate read at [1]-committed values,
   state-stop, arming, governor) commit only at Strategy-TF boundaries;
   fills checked on every chart bar (earlier visibility, identical state --
   a logic high is the max of its chart highs; intra-logic-bar gaps fill AT
   the stop per the Strategy Tester's bar model). With chart TF == Strategy
   TF, v2 reduces exactly to the v1 per-bar machine (Phase-B-at-[1] ==
   v1's close-committed Phase B). The state machine is now fully
   non-repainting (no close flicker); a separate PROVISIONAL
   'gate-against-position' alert covers the live warning. request.security
   deliberately still absent: user asked whether live use permits it --
   adjudicated NO (lookahead_off is stale on historical bars = the TVB-3
   bug, and the path-dependent machine needs correct history for a correct
   current state; the lookahead_on-for-open idiom violates the workspace
   bright line). Guard now: chart tiles Strategy TF; Strategy TF tiles
   every gate TF (chart-tiles-gate transitive). Compiled CLEAN, saved over
   the same verified "TFC Companion [TVB-9]" slot; user's HOOD chart
   untouched.

### Context for next session
- PRIMARY: fold in returned Codex audits (tvb9 AND the still-pending tvb8),
  then draft the LONG-ONLY ablation pre-registration WITH the user.
- TV Desktop left RUNNING (CDP 9222), chart at resting state
  HIP3XYZ:MSTRUSDC.P 15m; no Pine/slot changes this session.
- Sweep runners are idempotent: they read the committed tvb9 bar pulls
  (irreproducible -- cap slides daily); fresh symbols need fetch + commit.
- The gate stayed 8/8 green through everything; suite 70 passed + 2 skipped.

### Files created/modified
- NEW `analysis/tfc_hl_pilot.py`, `analysis/tfc_leverage_overlay.py`,
  `scripts/tfc_breadth_sweep.py`, `scripts/tfc_htf_sweep.py`,
  `scripts/tvb9_symbolinfo.mjs`.
- NEW evidence (all committed): `analysis/reference/tvb9_hl_pilot_MSTR.json`,
  `tvb9_symbolinfo.json`, `tvb9_breadth_results.json`, `tvb9_htf_results.json`,
  `tvb9_leverage_overlay.json`, 9x `tvb9_hl_{slug}_1h.json`,
  9x `tvb9_hl_{slug}_1d.json`.
- MOD `docs/TVB2_control_AB_rerun.md` (six TVB-9 sections: pilot,
  pre-registration, breadth results, digs, HTF pre-reg+results, leverage
  overlay), `docs/HANDOFF.md`, `.session_startup_prompt.md`,
  `docs/reviews/REVIEW_REQUEST.md`.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb9-codex-audit.md.
> See docs/reviews/REVIEW_REQUEST.md (the pointer) and docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: REQUESTED
- Commits to review: `f192a14^..5edd5b6` on `main` (12 commits: pilot,
  pre-registration, sweep + evidence, interpretation, digs + HTF pre-reg,
  HTF sweep + evidence, leverage overlay, session-end, range pin, the
  post-session-end TFC Companion indicator addendum, its range pin, and
  the Companion v2 logic-TF-decoupled rewrite). RANGE-PIN RULE applied:
  the caret keeps `f192a14` (the pilot) inside the reviewed diff.
  Companion-specific focus: does the v2 state machine
  (`pine/tfc_companion.pine`: boundary-clocked Phase B at [1]-committed
  values, per-chart-bar fill checks) faithfully replicate the strategy's
  fill/exit/governor semantics; is the chart==Strategy-TF reduction to v1
  exact; is the no-equity-model claim sound; and is the
  no-request.security adjudication (stale-history vs lookahead_on idiom)
  correctly reasoned?
- Scope / what changed: Phase 5 complete -- venue-bar drift pilot;
  user-approved breadth pre-registration + 144-run sweep (regime map);
  CRCL-governor and MU-short-whipsaw digs; pre-registered HTF-index cells
  (108 runs, H2 refuted); leverage-extreme overlay ($500 account,
  MAE-clearance). NO Pine changes; NO simulator changes (gate 8/8
  throughout).
- Focus areas (scrutinize these): (1) drift-band logic -- is the
  sign-indeterminate rule (1.5/2.5pp) justified by the pilot's 12
  correlated cells, and is using the committed TVB-6 HL pull as the HL
  source sound? (2) pre-registration integrity -- were any cells/symbols
  added or interpreted beyond the declared expectations; is the E3only
  containment test fair? (3) HTF sweep -- resample correctness at 240m/1D
  (period-start stamping, partial first day), native-1d crosscheck
  handling (5 mismatched days on MU), and the H2-refuted inference;
  (4) leverage overlay math -- x_liq = 1/L - mm with mm = 1/(2*maxLev),
  MAE window (full entry bar conservatism), L*pp compounding approximation,
  min-notional death rule; (5) short-side weakness claim -- 3 observations,
  is the pattern real or window-driven? Standing: request.security lookahead
  (N/A -- no Pine), model fidelity, fee/turnover math, sample-vs-structural
  reasoning (the overfit guards in the HTF and leverage sections).
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb9-codex-audit.md exists)

---

## Session TVB-8: VBT breadth port Phases 0-4 -- THE EQUIVALENCE GATE IS GREEN (COMPLETE)

**Date:** 2026-07-06/07
**Status:** COMPLETE -- the port plan's Phases 0-4 built, verified, and pushed in
one session; the Phase-3 trade-for-trade gate is GREEN on all 8 cells. Last
Fable 5 session (judgment-heavy Pine-semantics port front-loaded per plan);
Opus 4.8 takes over from TVB-9.

### What was accomplished
1. **Codex TVB-7 review folded in** (session start, 2026-07-05): the 1 LOW
   verified real and fixed (`VBT_BREADTH_PORT_PLAN.md:20` net->GROSS wording);
   verbatim audit committed; statuses flipped. All reviewer recomputations had
   matched our record; nothing disputed. (This entry IS the critical synthesis:
   AGREE on the LOW -- the fix mattered because the plan is implementation-
   facing spec; the queued Pine comment correction stays attached to the next
   Pine-touching deployment.)
2. **VectorBT Pro v2026.6.27 installed IN THIS WORKSPACE** (user decision;
   workspaces stay separate). Kept OUT of git entirely: install guide
   (`vectorbt_pro_install.md`) gitignored -- remote is PUBLIC (verified via gh),
   DMCA exposure; package in .venv only, NOT pyproject/uv.lock (public clones
   still sync/test). numpy capped <2.5 + relock (numba import ceiling; `uv run`
   resyncs lock pins every invocation). Port plan AMENDED: implementation runs
   HERE; module home `tfc/`; fixture-copy step dropped (gate reads committed
   `analysis/reference/` directly).
3. **Codex-skill cross-workspace confusion DIAGNOSED + fix prompt delivered**
   (user ran it): single global `~/.codex/skills/session-review/SKILL.md`
   hardcodes this repo's absolute REVIEW_REQUEST path while vectorbt-workspace
   uses a different contract (HANDOFF block + EQUITY-<N>_review.md, no
   REVIEW_REQUEST.md) -> invoked there, it reviews the wrong repo. Prescribed
   fix: workspace-RESOLVING skill (git rev-parse from cwd; REVIEW_REQUEST.md
   else HANDOFF block; STOP if neither), delete the stale deprecated
   `~/.codex/prompts/session-review.md`.
4. **Phase 0-1 (calibration + periods).** Dump-driven calibration GREEN on all
   8 cells: fill conventions EXACT on ~20,300 closed trades (intrabar stop
   fill, gap-through at open -- 29% of 15m entries, exits next-open, adverse
   slip both sides); qty rule exact minus 2-3 floor-boundary cases (plan risk 1
   predicted 1-3). **CALIBRATED-FACT CORRECTION: dump `pp` =
   pv/(q*ep*(1+comm)) -- return on entry COST BASIS incl. entry commission
   (<= 8.3e-9 on all cells), NOT return on equity (~1.4e-4 err)** --
   indistinguishable at 100% sizing except on gap-through fills; zero-fee cell
   isolates the commission term. Corollary recorded: `window_compound.py`
   product(1+pp) is a ~5bp/4,308-trade approximation (fine for the recorded
   window COMPARISONS; equity must chain pv). `tfc/periods.py` pins the
   valuewhen seed semantics by test (M Jan-1, W Monday Dec-8, D Dec-3;
   change[0]=False). PREFIX RULE established: gov2 dumps carry live tail-drift
   trades past the committed bar files (contiguous, asserted).
5. **Phase 2-3 (simulator + THE GATE).** `tfc/simulator.py` = two-phase bar
   loop in Pine execution order; all trigger/stop arithmetic in INTEGER TICK
   SPACE (float high+mintick can exceed the true sum and miss fills TV takes).
   **GATE GREEN, first run for 7/8 cells: all 8 reference cells PASS
   trade-for-trade -- 20,429 closed trades, et/xt/dir exact, fills 2.8e-14,
   pv at serialization floor, pp <= 5e-9, both open-position boundaries match;
   ctrlB headline net to 1.3e-8; ~0.4s total.** One adjudication (plan risk
   1's own fallback): ctrlB_0125_s10 trade 686 sits 6.4e-6 below an integer
   qty boundary (TV's internal float path holds ~1e-6 USD more equity); a full
   scan shows NO other trade within 2e-5 of a boundary across ~20,300, so
   Q_FLOOR_EPS=1e-5 resolves it and provably cannot false-flip anything else.
   Micro-behavior tests pin re-arm gap, gap-through basis, one-bar stop life,
   equality-grey, governor block/win/reset. POLICY now enforced by
   `tests/test_tfc_equivalence_gate.py`.
6. **Phase 4 (resampler + providers, live-verified).** `tfc/resample.py`:
   15m->60m reproduces TV's own 60m file 5,102/5,103 exact OHLCV, 15m->1D
   213/214 -- both mismatches are the live LAST bar at capture time (pull
   skew), not aggregation error; period-start stamping matches TV (partial
   listing day stamps 00:00). `tfc/providers.py`: HL candleSnapshot + OKX
   history-candles (paginated, INTRADAY-ONLY guard -- OKX HTF anchors UTC+8;
   meta records served-vs-requested + floor_hit). LIVE: HL fetch reproduces
   the committed tvb6 HL candles EXACTLY on overlap; OKX pagination sane.
   Network tests opt-in via TFC_NETWORK=1; suite 70 passed + 2 skipped.
7. **Breadth universe scoped with user (directives binding for TVB-9):**
   probe: XYZ100 since 2025-10-13, SP500 since 2026-03-18, DRAM since
   2026-05-04 (1h capped ~5,000; 15m ~52d). User: NO keep/kill verdicts off
   young listings -- regime-mapping only; DRAM SKIPPED (too thin); widening to
   other a-priori xyz equity perps welcome if runway allows.

### Context for next session
- PRIMARY: Phase 5 -- MSTR-on-HL-bars pilot FIRST (venue-bar drift calibration),
  then pre-register (user approves) and run the regime-mapping breadth pass.
  See .session_startup_prompt.md for the full directive block.
- The gate is the contract: any simulator change must keep 8/8 green.
- `uv sync` strips vectorbtpro; reinstall via the gitignored guide (cached).
- No TV/chart work happened this session; resting state untouched from TVB-7.

### Files created/modified
- NEW `tfc/` package: `__init__.py`, `config.py` (f_guard port), `periods.py`,
  `tv_reference.py` (loaders + 8-cell registry), `simulator.py`,
  `equivalence.py`, `resample.py`, `providers.py`.
- NEW `scripts/tfc_qty_calibration.py`, `scripts/tfc_gate_report.py`.
- NEW tests: `test_tfc_periods.py`, `test_tfc_reference.py`,
  `test_tfc_simulator.py`, `test_tfc_equivalence_gate.py`,
  `test_tfc_resample.py`, `test_tfc_providers.py` (suite 25 -> 72).
- MOD `docs/VBT_BREADTH_PORT_PLAN.md` (venue amendment; gross-arming LOW fix;
  pp calibrated-fact correction), `docs/TVB2_control_AB_rerun.md` (TVB-8
  section), `.gitignore` (VBT Pro DMCA guard), `pyproject.toml` (numpy <2.5,
  network marker), `uv.lock`, `docs/HANDOFF.md`, `docs/reviews/REVIEW_REQUEST.md`,
  NEW `docs/reviews/tvb7-codex-audit.md` (verbatim, committed).

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb8-codex-audit.md.
> See docs/reviews/REVIEW_REQUEST.md (the pointer) and docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: REQUESTED
- Commits to review: `b4bab2c^..db203aa` on `main` (9 commits: TVB-7 fold-in +
  gitignore guard + numpy cap + port Phases 0-1, 2-3, 4a, 4b + datasheet +
  session-end; sanity-checked: `git diff --name-status` lists all 25 session
  files). RANGE-PIN RULE applied: the caret keeps `b4bab2c` (the fold-in)
  inside the reviewed diff.
- Scope / what changed: VBT breadth port Phases 0-4 (tfc/ package, calibration,
  simulator, equivalence gate, resampler, providers); gate GREEN 8/8; pp
  cost-basis correction; Q_FLOOR_EPS adjudication; VBT Pro in-workspace install
  with DMCA gitignore guard; Codex TVB-7 fold-in.
- Focus areas (scrutinize these): (1) does the equivalence comparator PROVE
  trade-for-trade equivalence, or do the tolerances/prefix rule leave an escape
  hatch for systematic bias? (2) is Q_FLOOR_EPS=1e-5 an adjudicated float
  artifact or a tuned parameter in disguise (knife-zone scan logic)? (3) the pp
  cost-basis correction inference (zero-fee control) + the window_compound
  approximation scoping; (4) simulator Pine-order fidelity vs
  pine/baseline_continuity.pine (loss-arm before alignment reset; flat-only
  arming; one-bar stop life; tick-space arithmetic); (5) providers: HL
  floor_hit semantics, OKX UTC+8 guard, the 2-day overlap cross-check breadth;
  (6) resampler last-bar mismatch explanation. Standing: request.security
  lookahead (NO Pine changes this session), model fidelity, fee/turnover math,
  sample-vs-structural reasoning (breadth pre-registration plan).
- Reviewed by: pending
- Findings: (blank until docs/reviews/tvb8-codex-audit.md exists)

---

## Session TVB-7: governor cross-venue VERIFIED; VBT port plan APPROVED; cost realism closed; Codex fold-in -> gross-arming discovery (COMPLETE)

**Date:** 2026-07-04
**Status:** COMPLETE -- all three startup priorities done PLUS the Codex TVB-6
review folded in same-session. Fable 5 session (mechanical re-verification, plan-
mode design with user, analysis tooling, review adjudication).

### What was accomplished
1. **Governor v2 cross-instrument re-verification -- KEEP-VERDICT UPGRADED
   (provisional -> cross-venue-verified on the MSTR underlying).** Pre-registered
   CV1-CV4 (datasheet) then 16 paired fresh runs: OKX:MSTRUSDT.P 15m ctrlB/R1E1
   x {0, 0.0125} x {s1, s10}; OKX MSTR 60m R1E3 (floor ALSO Feb-25 -- "60m
   deeper" refuted for OKX, listing-driven); BTC 60m R1E3 2.5y. CV2 keep-rule
   mirror PASS: R1E1+gov2 beats ungoverned at BOTH cost points (+42.44 vs +40.08
   s1; -56.62 vs -59.58 s10), gross higher (+78.16 vs +76.61), cut -3.5% (no
   starvation, CV1). Direction non-negative 8/8 pairs; MAGNITUDE PATH-LOCAL
   (+12pp xyz -> +2-3pp OKX; ctrlB gross flat on OKX vs +40pp on xyz). BTC
   stays negative governed (CV4 -- no manufactured edge). NOT universal-
   structural (no non-MSTR positive-edge instrument exists). Repro gates green
   (fresh ungoverned matched TVB-5 rows within tail drift). 16 dumps committed.
2. **VBT breadth-engine port DESIGNED with user (plan mode) and APPROVED** --
   `docs/VBT_BREADTH_PORT_PLAN.md` is the design of record. User forks decided:
   custom bar-loop simulator (not VBT callbacks); hard gate = 4-cell mechanism
   cover + 4 secondary regression cells; crypto perps first (equities = later
   phase, seam only). Planning VERIFIED calibrated facts against committed
   dumps: TV qty rule = floor(equity/(slipped_stop*(1+comm))/step)*step; pv
   formula (worst err 4.9e-5); gap-through fills at open. Implementation runs
   in a vectorbt-workspace session; Phase 3 (8 gate cells green) is a hard
   policy gate before ANY Python number enters the record.
3. **Cost realism closed (both TVB-6 carries).** (a) Live L2 sampling
   (`analysis/l2_book_impact.py`, 20 snapshots): at ~90 contracts per-fill cost
   vs mid = ~20-40 TV-ticks median, p90 ~30-50 -- BETWEEN s25 and s50, not near
   s10; caveat WEEKEND-NIGHT book (conservative); weekday-RTH re-sample queued.
   (b) Funding model (`analysis/funding_model.py`, 5,124 hourly events since
   listing): drag modest at 1x (-2.5 to -4.9pp, no sign flips) but INVERTS the
   fee gradient -- scales with time-in-market, so slow cells pay ~2x churn
   cells (R1E3 -4.77 / ctrlA -4.93 vs ctrlB -2.78); linear in leverage. +8
   tests (suite 25/25); evidence committed (L2 samples time-perishable).
4. **Codex TVB-6 review RETURNED + folded in (APPROVE-WITH-NITS, 3 LOW, all
   AGREED + actioned).** (1) 60m MAE rows corrected to committed replay (worst
   short 8.42%/7.22x, long 5.54%; 15m rows replay exactly; solvency
   unaffected). (2) tv_bars.mjs now persists tick metadata; equalizer evidence
   committed (tvb7_symbolinfo.json). (3) **THE DISCOVERY: the governor arming
   test `strategy.closedtrades.profit() > 0` reads GROSS of commission** --
   adjudicated without touching the Pine: boundary trades real (137/4,191);
   zero-fee vs fee'd governed sequences identical over 4,191 trades; at 1%
   commission the first 575 trades still match exactly, diverging only at the
   qty=0.001 equity floor (sizing artifact). All governed RESULTS stand (as-
   deployed behavior; keep-rule applied to what ran); the "net of fees"
   description corrected in datasheet + VBT plan (which would have failed its
   own gate); Pine comment fix queued for next deployment; net-arming variant
   = future pre-registered ablation candidate.

### Context for next session
- PRIMARY: execute the VBT port Phases 0-3 in a VECTORBT-WORKSPACE session per
  the approved plan (calibrated facts are spec; governor arms on GROSS).
- Weekday-RTH L2 re-sample = the operative slippage point estimate.
- Pine comment correction bundles with the next Pine deployment (+ prefix
  regression); do not do it standalone.
- Chart resting state verified after every excursion this session (anchor
  ~+8.0-8.2%/4,310-4,312, tail drift only). Entity SCn1V9 survived throughout.

### Files created/modified
- NEW `analysis/l2_book_impact.py`, `analysis/funding_model.py` + 2 test files
  (suite 25/25); MOD `analysis/fee_rates_by_dex.py` (ruff E731).
- MOD `scripts/tv_bars.mjs` (persists exchange/minmov/pricescale/mintick).
- NEW `analysis/reference/`: 16 cross-venue dumps (tvb7_OKXMSTR_*, tvb7_BTC_*),
  tvb7_l2_xyzMSTR.json, tvb7_funding_xyzMSTR.json, tvb7_symbolinfo.json,
  tvb7_diag_gov2_{0125,100bp}.json.
- NEW `docs/VBT_BREADTH_PORT_PLAN.md` (approved design of record, spec corrected).
- MOD `docs/TVB2_control_AB_rerun.md` (TVB-7 sections: cross-venue pre-reg +
  results, cost realism, Codex synthesis + adjudication; MAE table corrected).
- MOD `docs/HANDOFF.md`, `docs/reviews/REVIEW_REQUEST.md` (TVB-6 flip +
  TVB-7 request), NEW `docs/reviews/tvb6-codex-audit.md` (verbatim, committed).

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range
> below) and write a verbatim assessment to docs/reviews/tvb7-codex-audit.md.
> See docs/reviews/REVIEW_REQUEST.md (the pointer) and docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED (2026-07-04, Codex CLI) -- APPROVE-WITH-NITS; verbatim
  audit in `docs/reviews/tvb7-codex-audit.md`; critical synthesis to be written
  by TVB-8.
- Commits to review: `a4e1de8^..557e00d` on `main` (= `d9504ba's ancestors
  back through a4e1de8` plus the session-end commit; 5 commits, sanity-checked:
  `git diff --name-status` lists all 33 session files). RANGE-PIN RULE applied:
  the caret keeps `a4e1de8` (cross-venue verification) inside the reviewed diff.
- Scope / what changed: governor v2 cross-venue verification (16 paired OKX/BTC
  runs, pre-registered CV1-CV4, keep-verdict upgrade); VBT breadth-port design
  doc; cost realism (L2 impact sampler + funding model + datasheet section);
  Codex TVB-6 fold-in (MAE correction, tick-metadata evidence, gross-arming
  adjudication with diagnostic dumps).
- Focus areas (scrutinize these): (1) the gross-arming adjudication logic --
  is the 575-trade identical prefix at 1% fee DECISIVE for gross semantics, and
  is the qty-floor explanation of the divergence sound (tvb7_diag_gov2_*)?
  (2) CV pre-registration integrity -- were CV1-CV4 applied as written; is
  "cross-venue-verified but not universal-structural" honestly scoped?
  (3) l2_book_impact method -- impact vs mid as the s-band comparable; the
  TV-tick mapping under HL 5-sig-fig pricing; weekend-regime caveat adequacy;
  (4) funding_model join semantics (et,xt] and the notional~=equity 1x
  approximation; (5) the MAE-correction root-cause claim (pre-final bar export)
  -- plausible or overclaimed? Standing: request.security lookahead (none;
  no Pine changes this session), model fidelity, fee/turnover math.
- Reviewed by: Codex CLI, 2026-07-04
- Findings: 1 LOW -- stale "governor reads net closed-trade PnL" sentence at
  `docs/VBT_BREADTH_PORT_PLAN.md:20` conflicts with the corrected GROSS-arming
  calibrated-facts block in the same file (fix before the port starts). Second
  actionable = a reminder, not a new finding: keep the queued Pine comment
  correction (`pine/baseline_continuity.pine:212`) attached to the next
  Pine-touching deployment. All focus-area checks PASSED (gross-arming
  adjudication chain, CV pre-registration, L2 method, funding model, MAE
  framing, VBT calibrated facts) with reviewer recomputation matching ours.

---

## Session TVB-6: xyz backfill VERIFIED + adopted; venue gap decomposed; solvency + slippage gates; governor v1->v2 KEPT (COMPLETE)

**Date:** 2026-07-03
**Status:** COMPLETE -- every startup priority done plus the full governor arc.
Fable 5 solo session (verification, analysis, design-with-user, Pine build, ablation).

### Codex TVB-5 review -- critical synthesis (RETURNED, APPROVE-WITH-NITS, 2 LOW)
Both findings AGREED and actioned same-session: (1) tv_dump ordering assumption ->
fail-loud assertions (list length == closed+open, entry-time ordering) + raw exit
timestamp (`xt`) preserved per row; verified passing on every live dump. (2)
"universal damage containment" -> sample-scoped wording used in all new datasheet
sections and this synthesis. The audit's independent re-derivations (venue-gap
arithmetic, S8 ~0.00225%/trade, pre-registration integrity) all matched our record;
nothing disputed.

### What was accomplished
1. **xyz TV backfill VERIFIED = genuine HL venue data** (priority 1, the gate).
   HL candles pulled for `xyz:MSTR` (API floors: 15m 2026-05-12, 1h 2025-12-07
   capped at ~5000; 4h/1d UNCAPPED from the 2025-12-02 listing = TV backfill start).
   Bar-by-bar: 97-99% float-exact OHLCV INCLUDING VOLUME at 15m/60m/1D; Dec2-Dec7
   hole closed via 4h aggregation (29/30 exact, 30/30 volume); pre-May 15m pinned by
   exact internal 15m->60m aggregation (5102/5103). Residuals characterized (wick
   scrub pattern TV-more-extreme, one missing traded bar Jun-28 reconciling to the
   decimal, placeholder asymmetry). Evidence TIME-PERISHABLE -> 7 raw files committed
   (`tvb6_{tv,hl}_xyzMSTR_*.json`); reproduce via
   `uv run python analysis/verify_xyz_backfill.py` (NEW, +4 tests).
2. **Venue gap DECOMPOSED -- the TVB-5 surprise is ~half modeling artifact.**
   Mechanism peek: venues near-identical (close corr 0.9923; cum close path -18.00
   vs -18.09) -> the 89pp ctrlB gap needs only ~2.5bp/trade. Then the tick-size
   discovery: OKX mintick 0.01 vs xyz 0.001 -- the "slippage = 1 tick/fill"
   convention charged OKX ~10x more per fill. Equal-$ comparison (xyz s10): closes
   ~49% of the R1E1 gap (+83.07 -> +61.78 vs OKX +39.88) and ~61% of ctrlB's.
   Remaining gap = real venue texture; knife-edge conclusion REINFORCED (churn-config
   sign = venue-texture noise). NEW xyz CONVENTION: report s1 AND s10, never s1 alone.
3. **xyz MSTRUSDC.P ADOPTED as primary MSTR chart** (DECIDED with user; target venue
   + deeper 15m history; OKX = standing sign check). Re-stage regression GREEN
   (ctrlB/R1E1 reproduce TVB-5 WV within tail drift); NEW xyz-native 60m rows:
   ctrlA 474tr +65.62 @0 / +47.10 @0.0125; R1E3 408tr +61.92 / +46.21. Slices:
   modest same-sign venue lift on slow cells; **kill-regime is TURNOVER-DEPENDENT**
   (Dec-Feb: ctrlA +2.12 / R1E3 +4.63 NET through the window that took ctrlB to
   -40.09 and R1E1 to -12.61) -- refines TVB-5 SP6.
4. **Short-leg MAE / 1x-cash solvency CLEARED** (Codex TVB-3 finding 2; skill
   position-sizing-risk invoked). HL margin model (maxLev 10 -> mm 5%): 1x short liq
   at +90.5%; worst observed short MAE across 3,225 shorts = 8.11%; zero breaches
   even at the 5x threshold; max survivable short lev at sample-worst ~7.4x (long
   ~9.8x). TV margin-0/0 = fair model of 1x cash. NEW `analysis/trade_mae.py`
   (+4 tests); tv_dump upgraded to TVB-6 trade format (ep/xp/ddp/rnp). Leverage
   discussion with user recorded: isolated leverage = knock-out option; below
   clearance it is risk-REDUCING vs 1x-all-in cross; above clearance the backtest no
   longer describes the strategy. All %s in the record are 1x.
5. **Slippage sensitivity band** {1,10,25,50} ticks pre-registered (SB1-SB4) then
   run: ctrlB +7.94/-37.56/-74.92/-94.52; R1E1 +59.96/+34.76/+1.29/-37.07; ctrlA
   +47.10/.../+4.79; R1E3 +46.21/.../+9.19. SB2 refuted on magnitude (100%-equity
   compounding amplifies linear cost); 60m cells positive even at 50t.
6. **Re-entry governor (charter S8) -- designed WITH user, v1 -> v2, KEPT.**
   Zero-parameter LEVEL RATCHET (losing exit -> same-direction re-entry only beyond
   the failed trigger). v1 reset (winning exit OR completed opposite trade) exposed
   **reset starvation under stand_aside** (opposite fills blocked -> one failed long
   ratchets out a whole regime episode; R1E1 1302->488 trades, gross +121->+27) --
   the two-layer baseline caught what the single-layer control hid. v2 reset =
   continuity event (exec-gate FULL OPPOSITE alignment), fresh pre-registration
   (V1-V4), re-run: R1E1+gov2 **+71.80 @0.0125 s1 / +45.71 s10** vs ungoverned
   +59.96/+34.76, higher gross (+134.8 vs +121.5 @0), better PF/DD; R1E3 inert
   (+0.84pp). **Pre-registered keep-rule MET -> v2 ratchet KEPT for the two-layer
   baseline** (input default stays off = regression anchor). Both regressions
   byte-identical (4,308-trade prefix match) at pineVersion 19 and 20.
7. **Underwater reality check (user flag, quantified):** ctrlB @0.0125 spent 204/213
   days below HWM (recrossed Jul-1 -- the +8% headline IS the final surge); R1E1
   149d; R1E1+gov2 124d; slow cells ~70d. Standing caveat in the datasheet: the
   underwater profile, not the endpoint, is the honest risk picture; everything
   remains one instrument, one 7-month path.
8. **Tooling/ops:** NEW `scripts/tv_bars.mjs` (CDP OHLCV export). tv_dump TVB-6
   format + assertions. Codex nit 1 done; nit 2 wording applied throughout. Jackson
   MCP Monaco finder FIXED (`27757bc` in tradingview-mcp-jackson): TV 2026-07 ships a
   fiber-less DECOY `.monaco-editor.pine-editor-monaco` node that dead-ended the
   first-match finder; multi-candidate fiber walk now; MCP picks it up on restart
   (this session used a direct-CDP bridge; the header "Add to chart" text button is
   gone -- use the circular-arrows update icon).

### Context for next session
- TVB-7 job 1 = governor v2 cross-instrument re-verification (OKX MSTR + BTC
  spot-check): is the lift structural or xyz-path-local? Keep-verdict is provisional.
- USER DIRECTION: port to VectorBT Pro as a BREADTH engine (many symbols, longer
  history, incl. regular equities as a DIFFERENT regime family). TV = fidelity
  anchor. HARD GATE: VBT must reproduce TV xyz cells trade-for-trade on the committed
  venue-verified bars before any VBT number enters the record. Plan mode for the
  design. See memory `project-vbt-breadth-engine`.
- Cost realism still open: venue-absolute slippage (live L2 sampling) + perp funding.
- NO deployability language anywhere: regime-local edge + containment + governor,
  single-sample; the system is one layer of a larger picture (HIP-3 screener attach
  path -- memory `project-one-layer-screener-attach`).

### Files created/modified
- NEW `analysis/verify_xyz_backfill.py`, `analysis/trade_mae.py` + tests (suite 17/17).
- NEW `scripts/tv_bars.mjs`; MOD `scripts/tv_dump.mjs` (TVB-6 format + assertions).
- MOD `pine/baseline_continuity.pine` (governor v2; slot pineVersion 20.0; id map +1
  shift: in_25 gov_mode, in_33 comm, in_34 slip, in_35/36 margins, in_42 magnifier).
- NEW `analysis/reference/`: 7 backfill-evidence files (tvb6_{tv,hl}_*), 6 xyz-native
  dumps (tvb6_WV_*), 12 slippage-band dumps (*_s{10,25,50}), 14 governor dumps
  (*gov_*, *gov2_*).
- MOD `docs/TVB2_control_AB_rerun.md` (six TVB-6 sections -- the session's core record).
- MOD `docs/HANDOFF.md`, `docs/reviews/REVIEW_REQUEST.md`, `.session_startup_prompt.md`.
- Sibling repo tradingview-mcp-jackson: `27757bc` (Monaco finder fix; local only).

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range below)
> and write a verbatim assessment to docs/reviews/tvb6-codex-audit.md. See
> docs/reviews/REVIEW_REQUEST.md (the pointer) and docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED (2026-07-04, APPROVE-WITH-NITS, 3 LOW -- synthesis in
  the TVB-7 sections of docs/TVB2_control_AB_rerun.md and the TVB-7 HANDOFF entry)
- Commits to review: `43fb973^..9a00d40` on `main` (= `1f7815f..9a00d40`;
  sanity-checked: `git diff --name-status` lists all 51 session files). RANGE-PIN
  RULE applied: the caret keeps `43fb973` (the review-return flip) inside the
  reviewed diff. Sibling repo tradingview-mcp-jackson `27757bc` at
  `C:\Strat_Trading_Bot\tradingview-mcp-jackson` -- local transport only.
- Scope / what changed: xyz backfill verification vs HL venue candles (+evidence);
  venue-gap decomposition (tick-size artifact); xyz adoption + native rows; MAE/
  solvency gate; slippage band; re-entry governor v1->v2 (Pine) + ablations; tv_dump
  assertions; Monaco finder fix.
- Focus areas (scrutinize these): (1) verify_xyz_backfill method -- is 97-99%
  float-exact + aggregation closure SUFFICIENT for "genuine venue data", and is the
  pre-May-12 15m residual honestly bounded? (2) the tick-size decomposition -- is
  "xyz s10 == OKX s1 in $/fill" a sound equalizer, and is "half artifact / half
  texture" over-claimed? (3) trade_mae.py -- MAE-vs-entry off bar extremes
  (conservative on the entry bar?), HL liquidation model (mm = 1/(2*maxLev)),
  max-survivable-leverage inverse; (4) the governor Pine -- trigger capture
  (high[1]+tick on the fill bar), same-bar ordering of loss-detection vs alignment
  reset, closedtrades.profit semantics (net of fees?), any repaint path; (5) the
  v1->v2 amendment epistemics -- mechanism-driven fix or post-hoc tuning? was the
  keep-rule applied as pre-registered? (6) byte-identity regressions as evidence
  (prefix match method). Standing: request.security lookahead (still none -- local
  ta.valuewhen only), model fidelity, fee/turnover math.
- Reviewed by: Codex CLI (docs/reviews/tvb6-codex-audit.md)
- Findings: 3 LOW, all AGREED + actioned in TVB-7: (1) 60m MAE table understated
  the committed replay (8.42%/7.22x, long 5.54%) -- corrected; (2) tick metadata
  not committed -- tv_bars.mjs now persists it + tvb7_symbolinfo.json committed;
  (3) governor profit-boundary diagnostic requested -- adjudicated WITHOUT a Pine
  change: strategy.closedtrades.profit() is GROSS of commission in this TV build
  (575-trade identical prefix at 1% fee is impossible under net-arming), so the
  "net of fees" mechanism description was wrong while every governed RESULT
  (as-deployed behavior) stands; VBT port spec corrected accordingly.

---

## Session TVB-5: S8 ratified; TF-set sweep across 4 samples; regime layer = containment; venue gap flagged (COMPLETE)

**Date:** 2026-07-03
**Status:** COMPLETE -- all four startup priorities done: S8 ratified + default-vs-input
decided; TVB-4 Codex review folded in (all 3 findings actioned); headline rows re-run +
committed; the pre-registered 3x3 timeframe-set sweep ran across FOUR samples (35 runs,
all sanity gates green).

### What was accomplished
- **S8 RATIFIED (Fable judgment, datasheet TVB-5 section):** stand_aside confirmed as the
  two-layer grey rule. Independent check: the suppressed stream is ~zero-expectancy GROSS
  (~+0.002%/trade vs 0.025% round-trip cost) -- skipping beats half-sizing mechanically;
  stand_aside also dominates risk-adjusted at ZERO fee, so it is not purely a fee story.
  P5 late-entry tax ratified as structural. DECIDED: `reg_mode` stays an INPUT, default
  `off` (defaults == regression anchor; baking a one-window data decision into code would
  fossilize it); the TVB-5+ baseline configuration = stand_aside set explicitly per run.
- **Codex TVB-4 review synthesis (RETURNED, APPROVE-WITH-NITS -- all 3 AGREED + actioned):**
  (1) MEDIUM range-pin (git left-endpoint exclusion dropped the Pine commit from the
  pinned range) -- verified correct; session-end command now mandates `{first}^..{head}`
  + a `git diff --name-status` sanity check. (2) LOW L/S open-trade basis -- verified
  against the committed dumps; `tv_dump.mjs` now reports CLOSED-basis splits (the open
  position is a pseudo-closed trade row whose exit is a mark-to-market at a WALL-CLOCK ms
  timestamp; closed set = first `performance.all.totalTrades` entries). (3) LOW missing
  real-fee dumps -- all six TVB-4 ablation rows re-run fresh and committed
  (`tvb5_R*.json`); every row reproduced within tail drift, DD/Sharpe exact. Also
  committed the tvb3/tvb4 audit files themselves (were untracked -- TVB-4 oversight).
- **Sweep design (with user, then locked):** 3 regime sets {M/W/D, W/D/12h, D/12h/4h} x
  3 exec sets {60/30/15@15m, 240/60/15@15m, 240/120/60@60m}, all stand_aside, fees
  {0, 0.0125}, PRE-REGISTERED in the datasheet (design + SP1-SP6 predictions) before any
  run. Amendments in-flight (justified, documented): SP500USDC.P has no TV backfill ->
  W2 fell back to OKX:BTCUSDT.P per the pre-registered rule; xyz MSTRUSDC.P turned out to
  HAVE backfill to 2025-12-02 -> W-venue upgraded to full runs + analytical
  window-slicing.
- **Sweep results (datasheet TVB-5 RESULTS section; the headline findings):**
  1. **The regime layer is universal damage containment, not return enhancement.** Every
     pairing in every sample improved: BTC 15m -73.67 -> -17.23; BTC 60m 2.5y -90.43 ->
     -36.71; xyz prefix -40.09 -> -12.61; OKX MSTR -9.06 -> +39.86 (@0.0125).
  2. **Regime speed is monotone-destructive** -- M/W/D > W/D/12h > D/12h/4h in every
     column of every window; the fast regime lands BELOW B-alone even at zero fee
     (anti-selective; the charter-S6 "correlated follower" failure mode observed
     empirically). Exec-span widening (240/60/15) is NOT a substitute regime layer.
  3. **The edge is instrument-specific and regime-local.** BTC: dead everywhere (B-alone
     -11.8% at ZERO fee over 7 months; ~0% gross over 2.5y at E3). Kill-regime LOCATED on
     the target instrument itself: xyz MSTR Dec-Feb chop is negative GROSS (-10.7%) while
     Feb-Jul is +254% gross.
  4. **S8 robustness:** off -90.43 < size_down -68.10 < stand_aside -36.71 in the 2.5y
     BTC spot-check -- the TVB-4 ordering generalizes.
  5. **SURPRISE (biggest open question): the venue gap REVERSES the assumed direction.**
     Same underlying, shared window, near-identical trade counts: xyz MSTRUSDC.P ctrlB
     @0.0125 = **+80.17%** vs OKX MSTRUSDT.P **-9.05%** (R1E1: +83.07 vs +39.88). The xyz
     TV backfill's provenance is UNVERIFIED -- flagged as a question per charter S0.
     TVB-6 job 1: cross-validate xyz TV bars against HL SDK candles before ANYTHING
     builds on xyz numbers.
- **Scorecard:** SP3 (E3 most fee-robust), SP5 (orderings replicate cross-instrument),
  SP6 (kill-regime exists + located) CONFIRMED; SP1, SP2, SP4 REFUTED with mechanisms
  (the useful kind -- documented in the datasheet).
- **New tooling:** `analysis/window_compound.py` (+3 tests; suite 9/9) -- window-sliced
  product(1+pp) compounding over dump trade lists (validated kind-window method), enabling
  shared-window venue comparisons without constrained re-runs. `tv_dump.mjs` closed-basis
  fix verified live (closed L/S sums exactly to totalTrades).

### Context for next session
- TVB-6 = xyz backfill verification FIRST (see `.session_startup_prompt.md`); everything
  else (venue adoption decision, MAE/solvency, slippage realism) sequences behind it.
- NO deployability language is warranted anywhere: the characterized system is a
  regime-local edge (MSTR-class, trending stretches) + a universal containment layer.
- OPERATIONAL: TradingView is now a Microsoft Store app -- `tv_launch` auto-detect fails;
  direct exe launch flow + full re-stage notes in `.session_startup_prompt.md`. Chart
  left at the control resting state (OKX:MSTRUSDT.P 15m, reg off, fee 0.0125); end-state
  regression green.

### Files created/modified
- MOD `docs/TVB2_control_AB_rerun.md` (TVB-5: ratification, repro re-run, sweep
  pre-registration, sweep results -- the session's core record).
- NEW `analysis/window_compound.py`, `tests/test_window_compound.py` (9/9 pass).
- MOD `scripts/tv_dump.mjs` (closed-basis L/S; header). MOD
  `.claude/commands/session-end.md` (range-pin rule).
- NEW `analysis/reference/tvb5_R*.json` (6 repro dumps) + `tvb5_{W1,W2,W3,WV}_*.json`
  (29 sweep dumps). NEW-to-git `docs/reviews/tvb{3,4}-codex-audit.md`.
- MOD `docs/HANDOFF.md` (TVB-4 review block flipped RETURNED + this entry),
  `docs/reviews/REVIEW_REQUEST.md`, `.session_startup_prompt.md`.
- Commits: `b99dccb` (ratification + review fold-in + repro), `124ef0c` (sweep), plus the
  session-end doc commit.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range below) and
> write a verbatim assessment to docs/reviews/tvb5-codex-audit.md. See
> docs/reviews/REVIEW_REQUEST.md (the pointer) and docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED (2026-07-03, local Codex CLI -- APPROVE-WITH-NITS, 2 LOW; audit
  at `docs/reviews/tvb5-codex-audit.md`; critical synthesis in the TVB-6 entry)
- Commits to review: `b99dccb^..d622be1` on `main` (= `6c855cf..d622be1`; sanity-checked:
  `git diff --name-status` lists all 57 session files). RANGE-PIN RULE applied: the caret
  keeps `b99dccb` (ratification + review fold-in) inside the reviewed diff.
- Scope / what changed: S8 ratification write-up; Codex TVB-4 fold-in (tv_dump
  closed-basis fix, range-pin rule, repro dumps); pre-registered 3x3 TF-set sweep across
  4 samples (35 runs) + results reading; window_compound analysis tool + tests.
- Focus areas (scrutinize these): (1) `analysis/window_compound.py` method validity --
  product(1+pp) over closed in-window entries under 100%-equity sizing, open-trade
  exclusion, half-open window semantics; (2) the tv_dump closed-basis assumption (is the
  trade list guaranteed entry-ordered with open trades last?); (3) the sweep READING --
  are "universal containment" and "monotone regime-speed destruction" over-claimed from
  9 cells x 4 samples? (4) the venue-gap flag -- is the shared-window comparison sound,
  and is the unverified-provenance caution adequate? (5) pre-registration integrity --
  were the in-flight amendments (BTC fallback, W-venue upgrade) justified or
  result-driven? (6) the S8 ratification arithmetic (~zero-expectancy suppressed stream).
- Reviewed by: Codex CLI (2026-07-03)
- Findings: 2 LOW, no blockers. (1) tv_dump closed-basis parser relies on the observed
  `reportData().trades` tail-open ordering with no fail-loud assertion -- add one. (2)
  "universal damage containment" should be worded "universal across tested samples/cells"
  in the next synthesis. Checks passed: range pin, no-request.security posture,
  window_compound method + tests, venue-gap arithmetic re-derived from dumps, S8
  arithmetic (~0.00225%/trade gross), pre-registration amendments read as justified.

---

## Session TVB-4: Two-layer regime built + ablated; stand_aside flips B positive; review pointer + guide (COMPLETE)

**Date:** 2026-07-03
**Status:** COMPLETE -- built the two-layer regime architecture (charter 3.3), ran the
ablation, and answered the charter S8 grey-handling question with data. Dual-model session:
Fable 5 designed + built + regression-gated; Opus 4.8 ran the matrix + recorded.

### What was accomplished
- **Review workflow upgrade:** new `docs/reviews/REVIEW_REQUEST.md` -- a stable pointer file
  external reviewers (Codex `/review`, cloud) are aimed at; `/session-end` rewrites it each
  session, `/session-start` flips it to RETURNED. Wired through EXTERNAL_REVIEW_PROTOCOL,
  reviews README, both slash commands. Retired the per-commit-approval rule in session-end
  (predated auto mode; commits/pushes now autonomous, secret-scan gate is the sole blocker).
- **TVB-3 Codex review RETURNED (APPROVE-WITH-NITS, 3 LOW), all agreed + triaged:**
  finding 3 (crossed-flag `bool()` coercion) FIXED -- `to_bool()` validates a real JSON
  boolean, malformed rows skip, +1 test (6/6 pass). Finding 1 (alignment guard) folded into
  the TVB-4 Pine. Finding 2 (short-leg MAE/solvency) deferred to the deployability stage.
- **Preflight 1 -- bar-magnifier fidelity: no material distortion.** B @0.0125 OFF -10.06%
  vs ON -11.13% (1 fewer trade); A bit-identical (verified via live-recompute control). The
  state-stop architecture is path-independent intrabar; magnifier stays OFF for the sweep.
  CARVE-OUT: any future price-stop variant is magnifier-sensitive, re-check then.
- **Preflight 2 -- kind-window bug-test: PASS.** A-priori windows from a price scan (KIND-UP
  Apr12-22 +43.8% B&H; KIND-DOWN Jun16-26 -36.5%). Zero-fee in-window compounding is
  unmissably positive and direction-coherent (A: 0 longs in the crash, 34/35 longs in the
  rally). Findings: A's down-capture is structurally weak at zero fee (25% vs 69% up); B
  fights the trend with ~half its trades -- the data-generated motivation for the regime layer.
- **Two-layer regime Pine (charter 3.3), regression GREEN.** Added an HTF M/W/D FTFC gate
  over the Control-B execution layer; `reg_mode` = off | stand_aside | size_down (grey at
  fixed a-priori 50%); no regime exit in v1 (reg_exit knob off). Plus the alignment guard
  (chart TF must TILE every enabled gate TF -- Codex finding 1; both guard paths verified
  firing live). Defaults = the TVB-3 control; regression PROVEN twice (pre- and post-restart:
  all 2811 reference trades byte-identical with reg_mode off).
- **Two-layer ablation (the headline).** OKX:MSTRUSDT.P, Control-B exec, window Feb25-Jul3:
  - @0.0125 real fee: control **-8.60%** (PF 0.981, DD 37.3%, Sharpe -0.10) -> stand_aside
    **+40.26%** (PF 1.195, DD 14.3%, Sharpe 0.75) -> size_down **+12.84%**. A ~49pp swing +
    sign flip from a regime filter alone.
  - stand_aside cuts trades 2814 -> 922 (67%) but keeps 90% of zero-fee P&L (+76.6 vs +84.7)
    -- the suppressed trades were disproportionately fee-burners (P4 confirmed dramatically).
  - **S8 DECISION (data-driven): stand_aside > size_down** on every axis at real fees.
    "Stand aside when the playbook stops" beats "trade smaller." Fable to ratify.
  - Predictions P1/P2/P4/P6 confirmed; P3 partial (small honest cost); P5 confirmed + LOCATED
    (regime late-entry tax at the V-bottom: core-rally +16.7% vs control +23.7%). SURPRISE:
    size_down wins the KIND-DOWN window (+20.1%) but loses the full-fee sample -- grey rule is
    regime-dependent (parked vol-conditional avenue, do not tune).
- **Manual backtesting guide:** `docs/guides/MANUAL_CONTROL_AB_GUIDE.md` -- step-by-step for
  the user's own cross-ticker control runs (fee ladder, history loading, sanity gates, refs).

### Context for next session
- TVB-5 = the priority-4 timeframe-set SWEEP with the two-layer as the ablation baseline.
  Ratify the stand_aside S8 decision first (Fable judgment); fold in the TVB-4 Codex review.
- The two-layer Pine is the go-forward baseline. Regime late-entry tax (P5) will bite harder
  in a sample with more sharp reversals -- the second regime window (regime-flattery guard)
  matters. Results still concentrate long (+29.80 vs short +10.46 @0.0125).
- OPERATIONAL: TV restart drops the strategy study (in-memory, not saved to layout) AND a
  bare relaunch over a running instance does NOT attach the debug port -- must Stop-Process
  the existing TradingView first, then relaunch with the CDP flag. Re-add the study, re-derive
  the entity id (changes every add) + id map. Full re-stage flow in `.session_startup_prompt.md`.

### Files created/modified
- MOD `pine/baseline_continuity.pine` (two-layer regime; Pine v6; slot "TFC Baseline"
  `USER;e7c8...` byte-identical, pineVersion 18).
- MOD `analysis/fee_rates_by_dex.py` + `tests/test_fee_rates.py` (crossed-flag fix; 6/6 pass).
- MOD `docs/TVB2_control_AB_rerun.md` (preflight 1, preflight 2, two-layer ablation sections).
- NEW `docs/reviews/REVIEW_REQUEST.md` (reviewer pointer); MOD EXTERNAL_REVIEW_PROTOCOL,
  reviews README, `.claude/commands/session-{start,end}.md`.
- NEW `docs/guides/MANUAL_CONTROL_AB_GUIDE.md`.
- NEW `scripts/tv_probe.mjs`, `scripts/tv_dump.mjs`, `analysis/reference/tvb4_*.json`
  (CDP probe + dump helpers + reference/run dumps).
- MOD `docs/HANDOFF.md`, `.session_startup_prompt.md`, `docs/reviews/REVIEW_REQUEST.md`.
- Memory: NEW TVB-4 (OpenMemory + auto-memory); auto-memory `feedback-autonomous-commit-push`.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range below) and
> write a verbatim assessment to docs/reviews/tvb4-codex-audit.md. See
> docs/reviews/REVIEW_REQUEST.md (the pointer) and docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED (2026-07-03, local Codex CLI -- APPROVE-WITH-NITS; audit at
  `docs/reviews/tvb4-codex-audit.md`; critical synthesis in the TVB-5 entry)
- Commits to review: `58c3ca9..bc9941f` on `main` (the two-layer Pine, ablation, docs; the
  review-workflow + fee-fix commits `5359756`/`9331d89` are pre-58c3ca9 if a wider range helps)
  -- NOTE (Codex finding 1, MEDIUM): this range EXCLUDES `58c3ca9` itself (the Pine commit);
  the reviewer compensated by reading the wider session context. Future pins: `58c3ca9^..`.
- Scope / what changed: two-layer regime Pine (M/W/D over Control-B, reg_mode modes,
  alignment guard); regression-proven; ablation run matrix; datasheet + review-pointer + guide.
- Focus areas (scrutinize these): (1) the `f_agg`/`long_permit`/`short_permit`/`size_scale`
  regime logic -- does stand_aside/size_down/off do exactly what's claimed? (2) the
  size_down `qty = strategy.equity * size_scale / close` arm-time approximation -- is it a
  fair half-size, any leak? (3) the alignment guard (tiling math for D/W/M vs intraday);
  (4) the regression-equivalence claim (reg_mode off == control); (5) the ablation reading,
  especially P4/P5 and whether the S8 stand_aside conclusion is over-claimed on one window;
  (6) kind-window compounding method (product(1+pp), in-window entry filter).
- Reviewed by: local Codex CLI (2026-07-03)
- Findings: APPROVE-WITH-NITS, no Pine logic blocker. 1 MEDIUM: the pinned range
  `58c3ca9..bc9941f` excludes the Pine commit itself (git left-endpoint exclusion).
  2 LOW: (a) tv_dump L/S counts include the open trade so the split sums to
  totalTrades+1 in the datasheet; (b) the real-fee headline rows (+40.26/-8.60/+12.84
  @0.0125) have no committed reference dumps -- only the zero-fee runs are preserved.
  Regime logic, off-mode inertness, alignment guard, size_down arm-time sizing all
  verified clean by the reviewer. Synthesis (agree/dispute/act): TVB-5 entry.

---

## Session TVB-3: Stale gate confirmed + fixed; corrected controls; margin artifact killed (COMPLETE)

**Date:** 2026-07-02
**Status:** COMPLETE -- all 6 amended-order priorities done. The FTFC gate WAS stale (preflight
N1 confirmed empirically), fixed via local period-open reconstruction; a TV margin-call deadlock
artifact was discovered and removed; the corrected-gate fee sweep REPLACES all TVB-1/2 numbers.

### What was accomplished
- **Settings dump (Codex 1 + N3):** full CDP decode of the strategy instance's inputs +
  properties (metaInfo().inputs id->internalID map). Answers: TVB-2 runs INCLUDED slippage=1
  tick/fill (in_24); bar magnifier OFF (in_32); sizing structurally 1x. Found the TV slot had
  drifted to the TVB-1 fee-test variant (v6, no leverage input). Datasheet patched: slippage
  wording corrected (runs were never slippage-free), checklist fee 0.0864%->0.0125% (Codex 3),
  superseded items annotated (N4).
- **P2a -- gate staleness CONFIRMED (N1 right).** Method deviation (justified): single-TF
  isolation of the strategy's own plotted gate values vs raw period opens, NOT the visual TFO
  overlay (the TFO indicator is itself lookahead-on). D-only: every bar of day N shows
  open(N-1); 60m-only: 43/43 non-boundary bars show the prior hour's open; the current open
  appears only on each period's LAST chart bar (simultaneous-close merge). All TVB-1/2 numbers
  characterized a "close vs prior-period opens" gate. Also verified: TV's OKX daily bars roll
  at 00:00 UTC. LESSON: an interim "gate looks current" read from the old 4-TF composite was
  WRONG (dead-session-polluted data + max/min masking) -- only single-TF isolation is decisive.
- **P2b -- ONE canonical Pine edit (plan approved):** gate -> `ta.valuewhen(timeframe.change(tf),
  open, 0)` (chart-local; backtest==live; same-TF = current bar open); trigger tick-offsets
  (high+mintick / low-mintick, strat-methodology strict-break); chart-TF<=gate-TF guard
  (runtime.error, verified firing); header fee note fixed (N5). Repo file and slot now
  byte-identical (Pine v6). Regression: 60m-only probe reads CURRENT 57/57.
- **DISCOVERY: TV margin-call deadlock.** 100%-equity sizing + default margin 100/100 =>
  every short margin-calls on its first adverse tick (equity==required at entry); on Apr 2 a
  margin-call/close race left an orphan +1.112-contract long that no strategy.close(id) could
  target => the first bridge run silently traded NOTHING for 3 months (order log + orphan
  arithmetic verified to the cent). FIX: margin_long=0, margin_short=0 (state-stop is the only
  exit, as designed). NOTE: TVB-1/2 short legs were margin-contaminated too.
- **Corrected-gate fee sweep (ACTUALS, replacing the geometric model).** Window Feb 25 10:00Z
  (data floor) -> Jul 3; buyHold -22.5% (the +3 tail days added a +19% rally):
  - A (M/W/D/60, 60m): 317 trades; 0% +50.0% PF 1.316; 0.0086% +42.0%; 0.0125% +38.6%
    (PF 1.245, DD 16.4%, Sharpe 0.87); 0.1% -20.4% PF 0.864.
  - B (60/30/15, 15m): 2801 trades; 0% +86.5% PF 1.143; 0.0086% +15.2%; 0.0125% **-7.4%**;
    0.1% -99.3%.
  - A's real-fee band matches the geometric prediction almost exactly; **B's sign FLIPS inside
    the real-fee band** (PF 0.98-1.03; corrected gate churns ~22% more) -- flagged as the
    session's surprise. A's edge is long-heavy (long +34.7% / short +3.9% @ 0.0125%).
  - Old-vs-new deltas bundle {gate fix + tick offsets + margin removal + 3-day window tail};
    decomposition deliberately not spent.
- **Jackson reader hardening (Codex 4; separate repo, commit `55e93f1`):** debug_sources
  propagated through getStrategyResults/getTrades/getEquity public returns; getEquity got the
  no-strategy debug branch; MAX_TRADES 20->500 cap (default stays 20); fixed three latent
  "evaluate is not defined" DI bugs in chart core (getVisibleRange/scrollToDate/symbolInfo --
  scrollToDate bit live this session). 123/123 non-e2e tests pass; 2 pre-existing live-TV
  compile failures verified identical on the pre-edit tree. Deploys at next MCP restart.
- **Sanitized fee artifact (Codex 2):** `analysis/fee_rates_by_dex.py` -- counts + RATES by
  {dex, crossed} from a LOCAL fills export; sanitization contract enforced and unit-tested
  (no absolute notionals in output). 4 new tests; suite 5/5.

### Context for next session
- TVB-4 = EXPERIMENTATION PHASE (charter S5) after two cheap preflights: bar-magnifier check
  (B knife-edge most exposed) and the kind-window bug-test. Then two-layer design (plan mode).
  See `.session_startup_prompt.md` for the full order + operational notes.
- Input id map SHIFTED this session when margin args were added (margins now in_25/26; a
  stale-id write set currency=0 => "Can't parse pine"; fixed by remove+re-add). Re-derive ids
  after ANY source change -- the rule has now bitten twice.
- Strategy on chart: `dILiiy` (re-check), OKX:MSTRUSDT.P 15m, Control-B enables, in_23=0.1.
  User's personal chart was displaced from CBOE:DRAM 1m -- restore or leave per user.
- TV session-disconnect gotcha: our own kill+relaunch triggers "accessed from another device";
  while disconnected, layout/tab ops and restudies silently no-op. Click Connect.

### Files created/modified
- MOD `pine/baseline_continuity.pine` (Pine v6 canonical: gate fix + tick offsets + guard +
  margin 0/0 + corrected header; byte-identical to slot "TFC Baseline" `USER;e7c8...`).
- MOD `docs/TVB2_control_AB_rerun.md` (TVB-3 sections: settings dump, P2a proof, P2b +
  artifacts, corrected-gate sweep + reading).
- NEW `analysis/fee_rates_by_dex.py`, `tests/test_fee_rates.py`.
- MOD `.session_startup_prompt.md`, `docs/HANDOFF.md`.
- SEPARATE repo: `tradingview-mcp-jackson` commit `55e93f1` (reader hardening + DI fixes).
- Memory: NEW `tvb3-stale-gate-margin-artifacts`; updated `tvb2-fee-resolved-real-taker`,
  `tvb1-controlB-fee-churn-finding` (supersession notes), MEMORY.md index.

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range below) and
> write a verbatim assessment to docs/reviews/tvb3-codex-audit.md. See
> docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED 2026-07-03 (via the new Codex /review command reading
  docs/reviews/REVIEW_REQUEST.md) -- APPROVE-WITH-NITS; synthesis below.
- Commits to review: `93f16d7..HEAD` on `main` (workspace) + `55e93f1` in
  `tradingview-mcp-jackson` (reader hardening)
- Scope / what changed: gate staleness empirically confirmed + fixed (ta.valuewhen local
  period-open recon); margin-call deadlock artifact removed (margin 0/0); corrected-gate
  2x4 fee sweep replaces TVB-1/2 numbers; sanitized fee-rate script; jackson DI/debug fixes.
- Focus areas (scrutinize these): (1) the P2a staleness proof method (single-TF isolation --
  is the simultaneous-close merge interpretation right?); (2) ta.valuewhen(timeframe.change)
  reconstruction edge cases (partial first period, non-aligned chart TFs, warmup-na semantics);
  (3) whether margin 0/0 hides anything a 1x cash-margin reality would enforce; (4) the
  corrected-sweep numbers and the B sign-flip reading; (5) the bundled-delta attribution caveat;
  (6) fee_rates_by_dex.py sanitization completeness.
- Reviewed by: local Codex CLI (docs/reviews/tvb3-codex-audit.md)
- Findings: 3 LOW -- (1) ta.valuewhen recon is only exact when every enabled gate TF
  aligns with the chart TF; guard only enforces chart<=gate; (2) margin 0/0 removes any
  solvency/liquidation constraint a real 1x short book would enforce -- add an MAE/
  liquidation-distance check before deployability language; (3) fee_rates_by_dex.py
  coerces `crossed` with bool() -- a stringified "false" would misclassify as taker.

**Critical synthesis (TVB-4, 2026-07-03):** all three findings AGREED on inspection.
(1) is real and matters for the S5 sweep specifically: for a non-dividing chart TF the
first chart bar of a new period can OPEN before/after the true boundary, so the
"period open" silently becomes an approximation -- the alignment guard (every enabled
gate TF an integer multiple of chart TF; D/W/M require chart TF to divide 1D) must land
in the Pine BEFORE the timeframe-set sweep runs arbitrary combos (plan-mode item,
folded into sweep prep). (2) agreed and already on the deferred list as slippage/
deployability realism -- shorts' MAE vs 1x cash margin gets checked before any
deployability verdict, not for control characterization. (3) FIXED this session
(isinstance bool check + malformed-row skip + test). Also validated: the reviewer's
approval notes match our own P2a/P2b reading (single-TF isolation as ground truth,
lookahead-free strategy source).

---

## Interim 2026-07-01: Fable 5 preflight review (one-off; review only, no session work)

Pre-TVB-3 fresh-eyes review by Fable 5 (TVB-1/2 ran on Opus 4.8 while Fable 5 was offline).
Full findings: `docs/reviews/tvb3-preflight-fable5-review.md`. Summary:
- All 4 Codex TVB-2 findings CONFIRMED against sources -- adopt all (slippage recording,
  sanitized fee artifact, 0.0864% checklist patch, reader `debug_sources` propagation).
- NEW N1: the HTF-open gate is near-certainly STALE (`request.security` + `lookahead_off`
  returns the PRIOR period's open on historical bars) AND backtest-vs-live asymmetric
  (realtime returns the developing bar) -- a repaint-class divergence, stronger than the
  TVB-1 "fidelity, not a leak" framing. P2a/P2b therefore RESEQUENCED BEFORE the real-fee
  re-runs (else the four runs characterize the wrong gate and get redone).
- NEW N2: the geometric fee model was VERIFIED -- anchored at the 0% actuals it reproduces
  both 0.1% actuals to ~0.1pp; the A +38..42% / B +5..25% real-fee estimates are well
  grounded; the re-run is confirmation, and a material deviation would itself be a finding.
- `.session_startup_prompt.md` NEXT order amended accordingly (user-approved 2026-07-01).
  No implementation files were changed by the review.

---

## Session TVB-2: TV MCP reader fix + clean controls + fee saga resolved (COMPLETE)

**Date:** 2026-06-30
**Status:** COMPLETE -- TV MCP Strategy Tester readers FIXED + deployed + verified live; controls A/B
re-characterized cleanly; fee model resolved to GROUND TRUTH (real xyz taker ~10x cheaper than
assumed), REVERSING the "B dead by fees" verdict; binding constraint re-identified as slippage.

### What was accomplished
- **TV MCP reader FIXED + deployed + verified (P1, the session's main effort).** The new TV Strategy
  Tester UI broke the `tradingview-mcp-jackson` readers. Root cause was NOT what TVB-1 assumed:
  (a) finder false-positive -- matched `s.performance`, a profiling method on EVERY study, so it
  grabbed the first indicator; and `metaInfo().isStrategy` does not exist in the new UI. (b) data
  shape -- `reportData()`/`ordersData()` are methods; metrics in `reportData().performance.{all,long,
  short}`; trades in `reportData().trades`. Fixed all three readers (getStrategyResults/getTrades/
  getEquity) to detect via `isTVScriptStrategy` and pull the new shapes. Verified live on
  OKX:MSTRUSDT.P. Committed to jackson `main` (commit `fb2a788`).
  - The TVB-1 "relaunch to load the diagnostic" premise was a red herring: the diagnostic ran but its
    output was dropped by the reader's node-side outer return (field-pick). The right instrument was
    a standalone CDP probe reusing jackson's `connection.js` evaluate() -- iterate freely vs live TV,
    restart the MCP only to DEPLOY.
- **Controls A/B re-characterized cleanly** (clean JSON, no screenshots). 2x2 (A/B x fee 0%/0.1%),
  same window (Feb 25 - Jun 30, ~-30% downtrend), 1x, bidirectional:
  - B (60/30/15, 15m): 2301 trades; @0% +85.8% PF 1.186; @0.1% -98.1% PF 0.400 (commission 10545 > capital).
  - A (M/W/D/60, 60m): 261 trades; @0% +48.2% PF 1.373 Sharpe 1.84; @0.1% -12.0% PF 0.906.
  - Replicates + extends TVB-1; A dominates B risk-adjusted at ~9x fewer trades.
  - NOTE: the on-chart strategy was found as a HYBRID (M/W/D/60 on a 15m chart) -- neither control;
    inputs decoded to pin config. A vanished template-added instance was long-only (the "all-long"
    389-trade run); the bidirectional instance is the real one.
- **Fee saga RESOLVED to ground truth (the session's biggest finding).** User supplied real HL fills.
  An initial fee/notional inference gave a wrong "97% maker" read; the user's "I trade market orders"
  testimony flagged it; re-classified by HL's authoritative `crossed` flag (validated: native-crypto
  taker = HL published 0.0432% exactly). Result: xyz is 86.5% TAKER, and the real xyz TAKER rate is
  CHEAP -- ~0.0086% modal / 0.0125% notional-weighted, ~8-12x BELOW the 0.1% the backtest used.
  - REVERSES the fee verdict: at real cost A ~= +38-42% (clear winner), B ~= +5-25% (near breakeven),
    NOT dead. "Turnover fatal for B" was largely a fee artifact (~10x too high). These are GEOMETRIC-
    MODEL estimates -- must be CONFIRMED by actual re-run.
  - BUT the binding constraint MOVED to SLIPPAGE: user fills market/taker both legs; B = 2301
    round-trips = 2301x slippage; B near-breakeven at zero slippage is exactly where realistic
    slippage decides the sign. Charter S6 flag: a real mechanism (cheap fees) must not launder an
    optimistic "deployable" verdict.

### Context for next session
- Reader WORKS -- clean JSON via data_get_strategy_results/data_get_trades/data_get_equity. TV must
  run on CDP (MSIX: `Get-AppxPackage *TradingView*` + Start-Process `--remote-debugging-port=9222`).
  Each Claude relaunch kills the Claude-launched TV -> relaunch it.
- The A/B-at-real-fee numbers are MODEL estimates, NOT fresh backtests -- re-run at 0.0086% and 0.0125%.
- SLIPPAGE is the new binding constraint (deferred so far) -- model before any deployability call.
- Strategy `35dVw8` (`Baseline TFC [TVB-1]` / slot "VIX Spike Alert" / id `USER;e7c8...`) left at
  M/W/D/60, 0.1% fee, 15m chart (as-found hybrid). Input ids: in_2=M, in_4=W, in_6=D, in_8=60,
  in_10=30, in_12=15 (bool enables); in_23 = commission percent.
- P2a (HTF-open currency) + P2b (period-open recon + tick-offset + TF guard) still pending; the
  `Timeframe Continuity [TFO]` indicator is now on the chart for the overlay.

### Files created/modified
- NEW `docs/TVB2_control_AB_rerun.md` (control 2x2 + fee model + ground-truth resolution; canonical).
- MOD `docs/HANDOFF.md`, `.session_startup_prompt.md`.
- SEPARATE repo (committed): `tradingview-mcp-jackson/src/core/data.js` reader fix (`fb2a788`, main).
- Memory: updated `tvb1-tv-mcp-reader-newui` (FIXED + new-API ref); new `feedback-relaunch-is-cheap`;
  new `tvb2-fee-resolved-real-taker`.
- User-side: `Downloads/TVB2_fee_handling.md` (Claude Desktop fee analysis -- superseded by the repo datasheet).

### External Review (for Codex / cloud review agents)

> For Codex / other external review agents: review THIS session's work (range below) and write a
> verbatim assessment to docs/reviews/tvb2-codex-audit.md. See docs/EXTERNAL_REVIEW_PROTOCOL.md.

- Review status: RETURNED
- Commits to review: `bd2c760..HEAD` on `main` (workspace) + `fb2a788` in `tradingview-mcp-jackson` (reader fix)
- Scope / what changed: TV MCP reader fix (jackson); clean A/B control re-characterization; fee model
  resolved to ground truth (real taker ~10x cheaper -> verdict reversed; slippage now binding).
- Focus areas (scrutinize these): (1) fee ground-truth method (HL `crossed` flag + validation);
  (2) the geometric-model A/B-at-real-fee estimates -- should be confirmed by actual re-run, not trusted;
  (3) the "slippage is now binding, esp. for B" claim and the churn math; (4) whether the
  "breakout entry is intrinsically taker -> maker is not a free fee swap" reasoning holds;
  (5) reader-fix correctness in `jackson/src/core/data.js`.
- Reviewed by: local Codex CLI
- Findings: see `docs/reviews/tvb2-codex-audit.md` (overall NEEDS-CHANGES; 2 medium, 2 low)

---

## Session TVB-1: Baseline continuity strategy + A/B fee characterization (COMPLETE)

**Date:** 2026-06-28
**Status:** COMPLETE -- baseline control built + characterized; naive baseline KILLED at real
HIP-3 fees; turnover identified as the dominant lever.

### What was accomplished
- Built `pine/baseline_continuity.pine`: ONE parameterized `strategy()` =
  `{2-trigger (raw level cross via breakout STOP orders -> intrabar fill) + FTFC gate
  (chart close vs each enabled TF period-open, lookahead_off) + close-based state-stop}`,
  both directions, `leverage` input. Compiles clean; lookahead audit PASS (single
  `request.security`, `lookahead_off`; gate uses only period-open = non-leaking).
- Designed WITH user (plan approved): two a-priori controls, single-layer, state-stop only,
  fixed-size, `OKX:MSTRUSDT.P`. FTFC gate reconciled to the TFO indicator's `close > period-open`
  (NOT the skill's bar-type TFC) -- flagged per ambiguity policy; charter governs.
- Results on `OKX:MSTRUSDT.P`, Feb 25 - Jun 28 2026, 1x:
  - **Control B** (60/30/15, 15m): 2263 trades, 27.04% win, **PF 0.645**, MaxDD 81.79%, ~ -81%.
  - Fee-isolation (B, zero fees): **PF 1.284**, 37.65% win, MaxDD 14.66% -> raw edge POSITIVE;
    fees/churn (2263 round-trips) are the killer, not the signal.
  - **Control A** (M/W/D/60, 60m): 258 trades (~9x fewer), 34.11% win, **PF 1.131 (net +)**,
    MaxDD 14.79% -- clears OKX fees.
  - **Control A @ HIP-3 fees** (commission 0.10%): **PF 0.921 (net LOSER)**, 30.62% win,
    MaxDD 22.37% -- does NOT clear real venue costs.
- **VERDICT:** continuity gate has a faint real edge; turnover reduction (B->A) was necessary
  but NOT sufficient at real HIP-3 fees. A deployable version needs per-trade edge clearing
  ~0.2% round-trip -> MORE selectivity (two-layer regime filter, compression filter, re-entry
  governor), not just a slower gate. The exploration did its job: killed the naive baseline and
  located the bar.
- Fixed the `tradingview-mcp-jackson` reader FINDER (overlay strategies now matched; was
  wrongly `is_price_study`-gated) in `src/core/data.js` (SEPARATE repo, uncommitted). The new
  TV Strategy Tester UI ALSO changed the data-access API (`ordersData`/`reportData` reshaped);
  a diagnostic is staged but needs a full Claude Code relaunch to load + finish.

### Incident (resolved)
- Overwrote the user's saved "VIX Spike Alert" TV script with the baseline (`pine_new` did not
  create a separate slot; `smart_compile` auto-saved over it). User has a backup; baseline source
  is safe in the repo. LESSON: `pine_get_source` to verify the slot BEFORE `pine_set_source`.

### Context for next session
- Reader: a full Claude Code relaunch loads the staged `data.js` diagnostic -> read its dump
  (new TV data API) -> apply data-access fix -> relaunch -> clean JSON reads. Until then,
  screenshots (close editor via its X ~1884,33; dismiss CLUSDT.P alert popups).
- Canonical strategy = `pine/baseline_continuity.pine` (leverage 2x default, Control B 60/30/15
  defaults). Set `leverage=1` for sizing-agnostic edge reads. Control A = enable M/W/D/60 + chart 60m.
- Leverage is NOT an edge lever (per-trade metrics invariant; compounded curve concave +
  liquidation cap). Characterize at 1x; size via vol-targeting on a ROBUST edge later.

### Codex external audit + Claude critical review (post-TVB-1)
Codex audited `baseline_continuity.pine` + the TFO indicator (full verbatim text in
`docs/reviews/tvb1-codex-audit.md` -- read it against this synthesis, don't trust either blindly).
My critical synthesis -- do NOT assume Codex right; the starred item cuts both ways:

- **No classic lookahead LEAK in the baseline** (HTF `open` + `lookahead_off`). The TFO indicator
  IS unsafe as a backtest source (HTF `high/low` under `lookahead_on`) but we never used it as one.
  => TVB-1 results are NOT leak-inflated fiction. CONFIRMED.
- ***MUST VERIFY -- HTF-open currency.** My code comment asserts `lookahead_off` returns the
  CURRENT period's open. That was OVERCONFIDENT and may be WRONG: `lookahead_off` reveals an HTF
  bar aligned to its CLOSE and applies to the whole `[o,h,l]` tuple, so for true HTFs (D/W/M on a
  60m chart) it may return the PRIOR period's open => a stale/lagged gate. This is a FIDELITY bug,
  NOT a leak (prior open is fully known; results stay honest). VERIFY empirically: overlay the
  strategy's FTFC bar-coloring vs the TFO indicator (lookahead_on = current period). Match => fine;
  differ => stale opens. Either way ADOPT the unambiguous local reconstruction:
  `f_period_open(tf) => ta.valuewhen(timeframe.change(tf), open, 0)` (no `request.security`).
- **Model fidelity (valid):** the baseline is a "prior-close TFC-gate + resting breakout stop",
  NOT "check TFC at the exact intrabar break". Both legitimate; ours is the conservative, safe one.
- **The 1m reframe (the gem -- resolves the parked 1m idea):** for "TFC-at-the-break", run on a
  LOWER chart TF (1m/2m/5m) for intrabar fidelity but reconstruct the EXECUTION-TF (15/30/60) prior
  highs/lows for the TRIGGER and check the gate intrabar -- do NOT trigger off 1m bars (the naive
  version's flaw). A distinct VARIANT to build/compare, not a fix.
- **Adopt (low-risk fidelity):** trigger tick-offset (`stop = high + syminfo.mintick` /
  `low - syminfo.mintick`) to force a strict break vs equal-high touch (matches strat-methodology
  `H[1]+tick`); enforce chart-TF <= enabled-TF via `runtime.error`.
- **Variant, NOT control (charter ablation discipline):** catastrophic price fail-safe stop and the
  re-entry governor are charter Section 8 open questions -- test as ablations, do NOT bake into the
  minimal control (fail-safe matters more once leverage > 1; state-stop is close-based).
- **`close == open`:** TFO treats equality as down; ours as neutral (intentional). Negligible on
  liquid perps; only matters for exact TFO replication.
- **Proposed next-session order:** VERIFY HTF-open currency -> adopt local period-open recon +
  tick-offset + TF guard -> RERUN A/B fee characterization (confirm findings hold) -> THEN
  two-layer / TFC-at-break variant / governor as ablations.

### Files created/modified
- NEW `pine/baseline_continuity.pine`; MOD `pine/README.md` (control presets), `docs/HANDOFF.md`,
  `.session_startup_prompt.md`.
- Reference (user-added at root): `Timeframe_Continuity_Claude_Discussion.md`,
  `Timeframe_Continuity_Pinescript.pine` (the source discussion + the TFO indicator).
- SEPARATE repo, uncommitted: `tradingview-mcp-jackson/src/core/data.js` (reader finder fix + diagnostic).
- Memory: `tvb1-controlB-fee-churn-finding.md`, `tvb1-tv-mcp-reader-newui.md`.

---

## Session TVB-0: Workspace Bootstrap (COMPLETE)

**Date:** 2026-06-27
**Status:** COMPLETE -- standalone workspace scaffolded, MCP wired, conventions mirrored.

### What was accomplished

- Created standalone git repo `C:\Strat_Trading_Bot\tradingview-backtesting` (branch `main`).
- Wrote `CLAUDE.md` adapted for this domain: Pine-first vehicle, crypto-perp data rules (NOT
  the ATLAS equity/RTH orthodoxy), and the charter's epistemic stance encoded as binding rules.
- Moved the governing design doc out of vbt-workspace `Temporary/` to
  `docs/ATLAS_Timeframe_Continuity_Charter.md`.
- Wired the `tradingview` + `openmemory` MCP servers in `.mcp.json` (TRACKED here on purpose --
  no secrets -- so the wiring travels with the repo, fixing the vbt-workspace gitignore gotcha).
- `.claude/settings.json`: `ui_evaluate` denied (Tier 1), MCP servers enabled, and only the
  domain-agnostic global hooks kept (trading safety guard, ruff lint, test gate). The
  VBT/STRAT-Python guardians from vbt-workspace were intentionally NOT ported (Pine-first repo).
- Light `uv` Python project (`pyproject.toml`) for the analysis layer; smoke test added.
- Ported + adapted slash commands: `/session-start`, `/session-end`, `/pre-commit`.
- Seeded `.session_startup_prompt.md` with the TVB-1 plan.

### Context for next session

- Nothing strategic is built yet -- only the scaffold. The first real task (TVB-1) is to design
  and write the **baseline strategy()** WITH the user (charter Sections 3-4). This touches STRAT
  detection logic, so it is a strat-methodology STOP-and-ASK zone -- design before coding.
- The TradingView MCP install/gotchas are documented in the master guide at
  `vectorbt-workspace/docs/guides/TRADINGVIEW_MCP_INSTALL.md`; this workspace's
  `docs/guides/TRADINGVIEW_MCP_SETUP.md` is the local pointer + delta.

### Files created

Scaffold only -- see `git log` for the bootstrap commit. No strategy or analysis logic yet.

---
