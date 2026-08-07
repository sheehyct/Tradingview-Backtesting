# CURRENT REVIEW REQUEST -- tradingview-backtesting

> Entry point for external reviewers. If you are Codex (`/session-review`) or any other
> external review agent pointed at this repo: this file is your work order. It
> always describes the LATEST requested session review and is rewritten by
> `/session-end` each session. The permanent per-session record is the
> `### External Review` block in `docs/HANDOFF.md`; for the CURRENT request,
> this file wins if the two disagree. Full contract:
> `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Status

- Status: REQUESTED  <!-- REQUESTED | RETURNED (audit file written) -->
- Session under review: TVB-19 -- overnight autonomous run: the
  pre-registered 864-cell Tier A deliberate-overfit sweep (runner +
  committed results), the RTH-vs-UTC clock census (MATERIAL: 30.84%
  gate disagreement), the deep TV-bar harvest (33/33 datasets incl.
  the SKHX/SKHYNIX identity resolution), the overnight report, and
  session-end docs seeding the v6.1 control strategy() port.
- SCOPE: standard.
- Requested: 2026-08-05
- Write the audit to: `docs/reviews/tvb19-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: TVB-18 (`docs/reviews/tvb18-codex-audit.md`) was still
  UNRETURNED when TVB-19 closed -- that request remains open alongside
  this one (its range is pinned in the TVB-18 HANDOFF block).
  tvb8/tvb9 also remain unreturned (standing note).

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | {pending push -- pinned by the follow-up commit after session-end; will be `2a78ec2^..{session-end sha}`; sanity-check with `git diff --name-status`} |

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0.
2. `docs/HANDOFF.md` -- the TVB-19 entry at top (its External Review
   block mirrors this request).
3. `docs/experiments/tvb19_tier_a_prereg.md` -- the pre-registration
   (committed BEFORE the runner existed; part of the reviewed claim
   set) -- then `docs/experiments/tvb19_overnight_report.md` (the
   plain-language findings).
4. `docs/experiments/tvb15_paper_week1_protocol.md` week-1
   adjudication section (the language discipline the report must not
   violate).
5. `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Focus areas (scrutinize these)

1. Pre-reg-vs-execution fidelity: does `analysis/paper/sweep_tier_a.py`
   implement EXACTLY the declared grid (864 cells, axis levels),
   window (2026-07-06 -> 2026-08-03), warm-up conventions, and
   metrics? Scrutinize the warm-key task grouping (warm state depends
   only on pool-shape knobs -- true?), the roster equity-curve
   alignment/forward-fill in `_rollup` (drawdown correctness), the
   weekly entry-ts slicing, and the parity-symbol (DRAM) exclusion.
2. `analysis/clock_census.py` correctness: the RTH roll calendar
   (declared NYSE holiday table, weekend-bars-belong-to-Friday,
   first-trading-day week/month rules), the twin-convention open
   sampling (first bar at/after roll), the declared 1h-seeding delta
   (RTH opens up to 30 min late pre-archive), and whether the 30.84%
   pooled disagreement + day-leg attribution + flip-event asymmetry
   (2519 vs 1710, ~220 shared) survive scrutiny.
3. Overfit-language discipline: the DELIBERATE OVERFIT / in-sample
   ceiling label must hold everywhere (report, commit messages,
   HANDOFF); no cell promoted; the week-1 "NO official number"
   adjudication language intact; the no-backstop-corner finding framed
   as a question, not a strategy recommendation.
4. Harvest identity claims: xyz:SKHX = HIP3XYZ:SKHYNIXUSDC.P proven
   (9183/9187 float-exact overlapping 5m closes + listing-date match);
   the roster mintick catch (hl_inferred 0.1 vs TV 0.001) correctly
   left as a future-roster item with the frozen week-1 roster
   untouched; provenance (TV-vs-HL feed mix) declared in
   `analysis/reference/tv_deep/README.md`.
5. No frozen week-1 artifact modified anywhere in the range
   (events_week1.jsonl, scoreboard_week1.md, roster_week1.json).
6. request.security lookahead: N/A this session (no .pine changed) --
   confirm the range contains no Pine edits.

Standing priorities apply (model fidelity; overfitting language; the
sweep is a labeled ceiling, never a deployment claim).

## Output contract

- Verbatim audit -> `docs/reviews/tvb19-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value.
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
