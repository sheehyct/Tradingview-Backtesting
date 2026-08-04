<!--
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-15 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of `75eba90^..b9b93cb` on `main`, captured 2026-08-04
> (TVB-15 post-session). Lightly ASCII-normalized (em-dashes -> --, curly quotes -> straight);
> wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-15 -- paper twin, week-1 freeze, and same-day v6.1 fix-forward
- **Reviewed:** `75eba90^..b9b93cb` on `main` (5 commits)
- **Reviewer:** Codex CLI
- **Overall verdict:** NEEDS-CHANGES

## 2. Verbatim audit

### Scope, guardrails, and reproduction

- `git rev-list --count 75eba90^..b9b93cb` returned 5. `git diff --name-status 75eba90^ b9b93cb` returned the expected 57 changed files. `b9b93cb` is an ancestor of the current `HEAD`; all citations below refer to file snapshots at `b9b93cb` unless explicitly stated otherwise.
- The post-range guardrails were honored. I did not re-raise the deliberately deferred last-only supersede search, fixture assertion/interleave work, `min_sep` holdout protocol, or the later adverse-runner design gap.
- `uv run pytest tests/ -q -p no:cacheprovider` completed with **97 passed, 2 skipped**. The 24 paper-specific tests passed separately. `uv run ruff check analysis/paper tests/test_paper_engine.py tests/test_paper_archive.py tests/test_paper_roster.py` also passed.
- I replayed the `b9b93cb` roster and all 33 historical bar blobs in memory through the unchanged engine. The result reproduced `analysis/paper/events_week1.jsonl` byte-for-byte (18 events) and `analysis/paper/scoreboard_week1.md` byte-for-byte. The 33 series were timestamp-sorted, duplicate-free, internally gap-free at their stated intervals, and had valid OHLC envelopes.
- I independently reproduced the v6.0/v6.1 event-continuity claim: both modes emitted the same 18 events. The v6.1 DRAM twin ended at 13/11/2/0 alive sides. The residual eviction counter did **not** reproduce the HANDOFF/request claim; that is F4 below.

### F1 -- HIGH -- The entire committed day-one record is selected with a future roster

- **Severity:** HIGH
- **Location:** `docs/experiments/tvb15_paper_week1_protocol.md:7-9,31-35`; `analysis/paper/replay.py:33,53-64`; `analysis/paper/roster_week1.json:8-22,214`; `analysis/paper/events_week1.jsonl:1-18`
- **Status:** CONFIRMED

The grading window starts at 2026-07-20 00:00 UTC, but the scanner roster was frozen at 2026-07-20 14:31:21 UTC. `replay_symbol()` selects bars from `week_start` and never clamps the replay to `frozen_at_utc` (`analysis/paper/replay.py:53-64`). The committed output therefore grades instruments chosen with information that did not exist when the simulated events occurred.

This is not a small bootstrap overlap. Decoding the committed timestamps shows **18/18 events predate the freeze**: 13 entries and 5 exits, from 00:00 through 14:00 UTC (`analysis/paper/events_week1.jsonl:1-18`). The scoreboard displays the contradiction directly: the window begins at 00:00, the roster was frozen at 14:31, and every row contains data only through 14:30 or 14:35 (`analysis/paper/scoreboard_week1.md:3-22`).

The selection variable is especially non-neutral here. The roster is ranked by a rapidly rotating score that includes short-horizon momentum and live-pattern state (`analysis/paper/roster.py:3-10`), and the protocol itself records large same-day score rotations before the freeze (`docs/experiments/tvb15_paper_week1_protocol.md:51-59`). Selecting at 14:31 and replaying that roster from 00:00 leaks the first 14.5 hours of the evaluation window into instrument selection. The 18 events reproduce deterministically, but none is prospective paper-trading evidence.

Start graded events at the first closed 5m bar after the roster freeze, or label the pre-freeze segment as retrospective bootstrap and exclude it from all week-1 grades. Add an invariant that no graded event timestamp can precede the roster's effective freeze boundary.

### F2 -- MEDIUM -- The actual 14:31 roster selection is not reproducible or fail-closed

- **Severity:** MEDIUM
- **Location:** `analysis/paper/roster.py:48-82`; `analysis/reference/tvb15_apistate_trimmed.json:2-14`; `tests/test_paper_roster.py:10-23`; `analysis/paper/roster_week1.json:8-22,214`
- **Status:** CONFIRMED

The repository does not contain the `/api/state` document used for the 14:31 freeze. The committed reference snapshot has an earlier source timestamp (13:26:36 UTC when decoded), and its tested tails are materially different from the frozen roster: the test expects NBIS/GOOGL/SKHY/AMD/GOLD and ORCL/CRCL/TSLA/MSTR/ZHIPU (`tests/test_paper_roster.py:13-23`), while the week roster stores MRVL/GOOGL/AMZN/MSFT/GOLD and AAPL/SKHX/SKHY/NBIS/TSLA (`analysis/paper/roster_week1.json:9-22`). That earlier fixture proves the selector on one real document; it cannot prove that the committed week roster was the top-five result at the claimed freeze.

The live path also calls `.json()` and immediately selects/writes without `raise_for_status()`, a `loaded` check, a source-age bound, a candidate-count check, or preservation of the source document (`analysis/paper/roster.py:75-82`). The output keeps only `source_ts` and the selected rows (`analysis/paper/roster.py:66-72`). A stale or partial but syntactically valid state can therefore become an apparently valid frozen roster, and the exact selection cannot be audited later.

Freeze the normalized source state (or a complete eligible-candidate census plus a content hash) transactionally with the roster. Fail closed on HTTP status, `loaded != true`, stale timestamps, and implausible candidate counts. Add a test that selecting the exact frozen source reproduces `long_names` and `short_names` byte-for-byte.

### F3 -- MEDIUM -- Coarse warm-up changes lifecycle state, not only anchor precision

- **Severity:** MEDIUM
- **Location:** `analysis/paper/replay.py:9-14,53-60`; `analysis/paper/engine.py:215-272,336-350`; `docs/experiments/tvb15_paper_week1_protocol.md:81-100`
- **Status:** CONFIRMED

The disclosure describes warm history primarily as an anchor-resolution delta: 12h/D/W use 1h bars and M uses 1d bars, so wick timestamps and projected values can differ. The implementation does more than form coarse anchors. `warm_pool()` sends each coarse row through the full `process_bar()` path (`analysis/paper/engine.py:336-341`), including containment touch, confirmed cross, and lifecycle mutation (`analysis/paper/engine.py:237-271`). One hourly range is compared with one line value at the hour-open timestamp; Pine on the deployed 5m chart compares twelve ranges with twelve contemporaneous line values. The 1d M warm-up collapses an entire day the same way.

The distinction is observable in the committed data. Over the common pre-week TSLA window, I fed the stored 5m bars and stored 1h bars separately through the same 12h `Pool`. The complete-hour high/low/close values matched; the one interval discrepancy was an unrelated open, which `Pool` does not consume. A shared N=1 formation born 2026-07-16 had its lower side consumed at 2026-07-17 13:40 in the 5m path but remained alive in the production 1h warm path (`analysis/paper/bars/xyz_TSLA_5m.json:1`; `analysis/paper/bars/xyz_TSLA_1h.json:1`). That stale alive side can later become a harvest or break candidate.

The protocol records stale-line drift, but attributing this only to cents-level anchor resolution understates the mechanism and its consequence. Either run lifecycle warming on 5m bars while using coarse bars only to construct base candles, or explicitly classify coarse lifecycle evaluation as a separate fidelity delta and test the common-window state diff per symbol.

### F4 -- MEDIUM -- `evict-alive` counts formations, undercounts lines, and is used in a false parity claim

- **Severity:** MEDIUM
- **Location:** `pine/tfc_bf_watch.pine:296-325`; `analysis/paper/engine.py:197-212`; `tests/test_paper_engine.py:143-164`; `docs/HANDOFF.md:60-67`; `docs/experiments/tvb15_paper_week1_protocol.md:143-155`; `docs/reviews/REVIEW_REQUEST.md:68-70`
- **Status:** CONFIRMED

When no fully retired formation exists, Pine increments `ev_alive` once and then removes both the lower and upper records (`pine/tfc_bf_watch.pine:296-325`). Python mirrors that event counter (`analysis/paper/engine.py:197-212`). The tests call it alive-at-eviction and assert only event totals (`tests/test_paper_engine.py:143-159`), even though one fallback eviction can discard two alive side lines.

An independent trace on the committed DRAM reference found:

- v6.0 12h: counter 22, but 25 alive sides removed (19 one-side and 3 two-side evictions).
- v6.1 12h: counter 13, but 14 alive sides removed (12 one-side and 1 two-side eviction).
- The `b9b93cb` day-one v6.1 twin: counter 15 total (14 for 12h plus 1 for D), but 16 alive sides removed.

This also exposes an internal claim conflict. The protocol correctly records on-chart counter 14 versus twin counter 15 (`docs/experiments/tvb15_paper_week1_protocol.md:152-155`), while HANDOFF and the review request claim chart 14 equals twin `13+1=14` (`docs/HANDOFF.md:65-67`; `docs/reviews/REVIEW_REQUEST.md:68-70`). The latter reused the fixed 1h regression census instead of the actual day-one twin state. Neither counter is an alive-side count, despite the Pine header describing the old 22/6 values as alive sides (`pine/tfc_bf_watch.pine:12-17`).

Track and label fallback formation evictions and alive side lines separately, increment the side counter from the two states immediately before removal, and add a two-alive-side regression. Correct the deploy-parity prose to preserve the real chart 14 versus twin 15 history-depth delta.

### Confirmed checks that are not findings

- **Engine/Pine processing order:** The twin performs boundary sweep, accumulation, collect-before-transition lifecycle scan, BF -> break -> flip exit race, entry, and arm roll last in the same order as the scoped Pine (`analysis/paper/engine.py:215-272,356-443,445-496`; `pine/tfc_bf_watch.pine:213-392,480-526`). Direction-relative harvest eligibility and strict trigger arithmetic also match.
- **Immediate v6.1 supersede fix:** Per-side retirement preserves the unchanged predecessor and ghosts its duplicate replacement in both implementations (`analysis/paper/engine.py:168-195`; `pine/tfc_bf_watch.pine:253-295`). The known last-only/older-duplicate search remains deliberately deferred and is not relabeled as a new finding here.
- **Retired-first selection and lockstep:** The oldest fully retired formation is selected before fallback eviction, and all 13 Pine arrays remove the same index (`pine/tfc_bf_watch.pine:296-325`). F4 concerns telemetry semantics and the parity claim, not array desynchronization.
- **Golden behavior:** The three uncapped v6.0 fixture goldens reproduce byte-for-byte after the two declared supersede-shadow substitutions, and the exception invariant test passes (`tests/test_paper_engine.py:69-115`). This is a useful regression pin, not independent deployment proof; the known assertion/interleave remediation was explicitly excluded from fresh findings.
- **No scoped `request.security`:** The only occurrence in `pine/tfc_bf_watch.pine` is the header's statement that none is used (`pine/tfc_bf_watch.pine:93-97`). There is no executable call in the reviewed indicator.
- **Archive mechanics:** `merge_rows()` is a timestamp union with the new fetch winning overlap, and its real-bar tests pass (`analysis/paper/archive.py:41-46`; `tests/test_paper_archive.py:12-29`). The SKHX tick remains visibly marked `hl_inferred` rather than TV-sourced (`analysis/paper/roster_week1.json:127-142`); I do not treat that provisional value as TV parity evidence.
- **Fees and turnover:** The artifacts consistently label fills as 1x gross with no fees/funding, and the scoreboard calls the arithmetic `sum pnl%`, not an equity curve (`docs/experiments/tvb15_paper_week1_protocol.md:65-79`; `analysis/paper/scoreboard_week1.md:3-10`). I found no hidden net-performance claim.
- **`min_sep` wording:** The reviewed Pine relabels the default as provisional/example-derived in both the header and input tooltip (`pine/tfc_bf_watch.pine:84-89,117-119`). The holdout protocol remains a known deferred decision.

### Validation limits

- The source proves that the committed indicator identifies itself as v6.1 and contains the restored header language. The historical live save, binding, version bump, and on-chart table readings are prose-only in this range; current live state cannot independently prove what was deployed on 2026-07-20. I therefore leave those claims UNVERIFIED rather than converting them into a code finding (`docs/HANDOFF.md:62-67`; `pine/tfc_bf_watch.pine:1-21,575-580`).
- The engine/Pine conclusions are code-grounded plus committed-data replay. I did not claim tick-for-tick live equivalence; the protocol's TV-vs-HL wick and realtime-vs-closed-5m deltas remain real.

## 3. Actionable items

1. Exclude all pre-roster-freeze events from week-1 grading (or relabel them retrospective) and enforce `event.ts >= effective_roster_freeze` -- **HIGH** -- `analysis/paper/replay.py:33,53-64`; `analysis/paper/roster_week1.json:214`.
2. Preserve and validate the exact freeze source, then prove that it regenerates the committed tails -- **MEDIUM** -- `analysis/paper/roster.py:48-82`; `tests/test_paper_roster.py:10-23`.
3. Separate coarse base-candle construction from 5m lifecycle warming, or explicitly disclose and regression-test coarse lifecycle drift -- **MEDIUM** -- `analysis/paper/engine.py:215-272,336-341`; `analysis/paper/replay.py:53-56`.
4. Split eviction-event and alive-side telemetry, add a two-live-side test, and correct the 14-versus-15 deploy narrative -- **MEDIUM** -- `pine/tfc_bf_watch.pine:296-325`; `tests/test_paper_engine.py:143-164`; `docs/HANDOFF.md:65-67`.

## Suggested prompt

Add: "Before grading any paper/replay artifact, compare every selection/config freeze timestamp with the first eligible bar and every emitted event. Fail if a graded event predates the information that selected its instrument. Require the exact selection-source snapshot to reproduce the frozen roster. For pool-cap telemetry, report both fallback formation evictions and the number of alive side lines removed."

Verdict: NEEDS-CHANGES
