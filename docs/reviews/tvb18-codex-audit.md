<!--
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-18 External Audit -- Codex (verbatim source, read CRITICALLY)

> External review of `a1a886f^..57417e2` on `main`, captured 2026-08-07
> (TVB-18 post-session). Lightly ASCII-normalized (em-dashes -> --, curly quotes -> straight);
> wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-18 -- week-1 close-out, TVB-15 audit fold-in, and design direction
- **Reviewed:** `a1a886f^..57417e2` on `main` (6 commits)
- **Reviewer:** Codex
- **Overall verdict:** NEEDS-CHANGES

## 2. Verbatim audit

### Scope, guardrails, and reproduction

- The pinned range is well formed. `git rev-list --count a1a886f^..57417e2` returned 6, and `git diff --name-status a1a886f^ 57417e2` returned exactly 46 paths, including all 33 `analysis/paper/bars/*` paths. `57417e2` is an ancestor of current HEAD. All range-era citations below use the `57417e2` snapshot; TVB-19 was not reviewed.
- The close-out artifact mechanics reproduced. The original 38 event lines are a byte-identical prefix of the final log, 43 lines were appended, and the result is 81 sorted, unique event keys (44 entries and 37 exits). An in-memory replay regenerated the reviewed Git blob byte-for-byte and regenerated the scoreboard text exactly. Across the 33 bar files, 4 old arrays remained exact prefixes and 29 replaced only the previously forming final row before appending; no earlier historical row changed. All reviewed arrays were timestamp-sorted, duplicate-free, interval-contiguous, and OHLC-valid.
- The reviewed-era test corpus completed with `97 passed, 2 skipped`; the two post-range TVB-19 test files were excluded. `ruff check --no-cache analysis/ tests/` and `git diff --check a1a886f^ 57417e2` passed.
- The known-open F2/F3/F4 repairs, future freeze invariant, and TVB-14/15 deferred items were treated as recorded decisions, not omissions.

### F1 -- HIGH -- The closed-week open MTM is marked at the August 4 archive tip, not at the July 27 week boundary

- **Severity:** HIGH
- **Location:** `analysis/paper/compare_config.py:74-115`; `docs/experiments/tvb15_paper_week1_protocol.md:230-285,343-355`; `docs/HANDOFF.md:18-30,47-52`
- **Status:** CONFIRMED

`replay_cfg()` correctly returns both the bounded `week_rows` and the full archived `rows_5m` (`analysis/paper/compare_config.py:39-71`). `summarize()` then discards the bounded rows as `_week_rows` and values every position left open at `week_end` with `rows_5m[-1][4]` (`analysis/paper/compare_config.py:81-101`). After TVB-18 advanced the archive through August 4, that is an August 4 close, one week after the declared July 20 through July 27 window. The position lifecycle is still stopped on July 27, so this is neither week-end MTM nor a continued replay through August 4.

I recomputed every open position using the final 5-minute close with `ts < 2026-07-27T00:00:00Z`. The control is -5.58pp open MTM and -33.18pp combined, not -40.65pp and -68.25pp. The variant is -6.94pp open MTM and -22.38pp combined, not -47.69pp and -63.13pp. These are diagnostic corrections only; the user's adjudication still makes neither view an official performance result.

The timestamp error also changes the stated mechanism. At the actual window boundary, GOOGL was -0.97%, AMZN was +0.39%, and SKHY was +1.56%, rather than the later -15.8%, -19.5%, and -12.1% marks described as "window-end" runners (`docs/experiments/tvb15_paper_week1_protocol.md:261-264,350-355`). The later observations may still be useful post-window evidence, and the post-freeze closed adverse-break class remains real, but they do not establish that those three positions were adverse runners at the end of week 1.

The core TVB-15 F1 reproduction remains sound: `freeze_slice.py` reproduced 18/81 pre-freeze events, 12/37 closed trades entered pre-freeze, and +14.37pp realized for the post-freeze-entry sensitivity. All six roster positions open at the week boundary entered post-freeze; DRAM is the seventh open and is correctly tagged parity. What fails is the price timestamp used for their MTM and every combined total derived from it. `freeze_slice.py` only reconstructs and labels the open entries (`analysis/paper/freeze_slice.py:81-91`); it does not calculate the -40.65pp attributed to the fold-in.

### F2 -- MEDIUM -- The parity table substitutes shared chart rungs for the twin's actual nearest rungs

- **Severity:** MEDIUM
- **Location:** `analysis/paper/parity_state.py:75-90`; `analysis/paper/engine.py:241-271`; `docs/experiments/tvb15_paper_week1_protocol.md:300-326`; `docs/HANDOFF.md:31-40`
- **Status:** CONFIRMED

The reviewed script reproduced the documented positions, gates, alive counts, and most quoted line values, and its warm-up, gate seed, arm seed, and last-bar drop match `replay.py`. Its DRAM output does not, however, support the table's "next dn / up" twin values. At the archive tip, the nearest full-history twin line below price is 47.3904 (12h N=3 lo) and the nearest above is 53.3896 (12h N=2 up). Both are alive and position-relevant under the short harvest/adverse-break rules (`analysis/paper/engine.py:241-271`). The protocol instead reports 41.0232 (W N=1 lo) and 71.9622 (D N=4 up), which are farther shared rungs that happen to correspond to the fresh-mount chart (`docs/experiments/tvb15_paper_week1_protocol.md:300-311`).

The later operational paragraph does disclose the missing 47.39 lower line, so the loaded-history risk is not wholly hidden. But it omits the nearer 53.39 upper line and conflicts with both the table label and the claim that every operative rung corresponds (`docs/experiments/tvb15_paper_week1_protocol.md:313-326`). The accurate conclusion is narrower: positions, gate composites after accounting for read time, and selected shared structural rungs matched; the fresh mount lacked nearer operative 12h state on both sides. The table should distinguish "nearest in each state" from "same structural rung found in both states."

There is also a unit error in the same gate explanation: 49.804 minus 49.791 is 0.013 dollars, or 1.3 cents, not 13 cents (`docs/experiments/tvb15_paper_week1_protocol.md:303,313-316`; `docs/HANDOFF.md:34-36`). The direction of the threshold crossing is still correct.

### F3 -- LOW -- The standalone slice output calls a heat-conditioned cohort "clean-entry" without the adjudication warning

- **Severity:** LOW
- **Location:** `analysis/paper/freeze_slice.py:1-8,76-80`; `docs/experiments/tvb15_paper_week1_protocol.md:359-366,403-415`
- **Status:** CONFIRMED

The final protocol, HANDOFF, and next-session prompt consistently say that week 1 has no official number, and the protocol explicitly says the post-freeze cohort remains heat-conditioned by roster selection. I therefore found no session-level attempt to present +14.37pp as the official week-1 result. The standalone CLI output is weaker: it prints realized, win-rate, average, and sum statistics under `POST-FREEZE-ENTRY (clean-entry slice)` without printing either caveat. Because the roster was selected after observing the same day's move, "clean-entry" is easy to read more broadly than intended when the tool is run outside the protocol context. This is a wording risk, not a dispute of the reproduced realized arithmetic.

### Confirmed checks that are not findings

- **Freeze slicing:** Events are counted pre-freeze by event `ts`, closed trades are split by `entry_ts`, exact-boundary entries fall into the post slice through `<` versus `>=`, and DRAM is excluded from closed aggregates (`analysis/paper/freeze_slice.py:50-65`). Empty exit classes avoid division and print `n=0` (`analysis/paper/freeze_slice.py:29-42`). The open-position reconstruction and actual entry-side attribution also reproduced.
- **Parity-state implementation:** Control warm-up uses pre-week 1-hour bars for 12h/D/W, pre-week 1-day bars for M, the same 1-hour gate seed, the last 15 minutes of pre-week 5-minute bars for the arm, and `load_rows()` for the common final-bar drop (`analysis/paper/parity_state.py:35-55`; `analysis/paper/replay.py:37-64`). Empty pools and pools with only one alive side print safely. I found no new replay-convention defect in this utility.
- **TVB-15 fold-in:** F2 is code-grounded: the preserved fixture timestamp differs from the roster's recorded source/freeze times, and the live path performs no HTTP-status, loaded-state, staleness, or candidate-count guard before writing (`analysis/reference/tvb15_apistate_trimmed.json:2-3`; `analysis/paper/roster_week1.json:8,214`; `analysis/paper/roster.py:48-82`). F3 reproduced exactly: TSLA's July 16 N=1 12h lower is consumed at July 17 13:40 in the 5-minute lifecycle path and remains alive in the 1-hour warm path. F4 is also faithful: both implementations increment once per fallback formation eviction before removing both side records, and the prior 14-versus-15 prose is visibly corrected (`pine/tfc_bf_watch.pine:296-325`; `analysis/paper/engine.py:197-212`; `docs/HANDOFF.md:430-436`). The fold-in commit precedes the adjudication commit by about five hours. Deferring the greenlit code repairs until before the next graded run is proportionate to the recorded no-rerun decision.
- **Lookahead rule:** `.claude/commands/pre-commit.md:18-30` and `pine/README.md:27-32` now state the same correct rule: un-offset `lookahead_on` is the trap; `expr[1]` plus `lookahead_on` is an approved confirmed-HTF idiom.
- **New Pine pair:** The reviewed Pine blob and the specified sibling canonical file are exact byte matches (same length and SHA-256). The only `request.security` text in the source is a comment saying none is used; there is no executable `request.*` call (`pine/strat_magnitude_targets_plus.pine:14-25,135-168`). The source bounds developing-bar provisional behavior, local aggregation, and no-backtest use, and the README repeats those limits (`pine/strat_magnitude_targets_plus.README.md:36-43,88-116`).
- **Corpus protection:** `.gitignore` covers `docs/thestrat_ai/` (`.gitignore:82-88`); the path has zero tracked entries at both `57417e2` and HEAD, and `git check-ignore` resolves the local corpus through that rule. Hashing all 417 local corpus files as Git blobs found zero exact matches in either tracked tree. Tracked docs contain only the intentional protective references and short design summary, not a copied corpus artifact.
- **Gross/sample language:** The scoreboard and protocol consistently describe the arithmetic as 1x gross with no fees/funding and do not call it an equity curve (`analysis/paper/scoreboard_week1.md:3-10`; `docs/experiments/tvb15_paper_week1_protocol.md:248-274`). The final adjudication preserves the structural-versus-sample stance and explicitly rejects an official week-1 performance number.

### Validation limits

- I did not have a preserved TradingView fresh-mount artifact, so the chart-side table readings, deployment history, and visual default-render claim remain prose/live-state claims. The code-grounded result is that the reviewed custom Pine is identical to the specified canonical custom file; that comparison alone is not a visual comparison with an unreviewed partner-original file.
- The parity conclusions are replay/code-grounded against the committed Hyperliquid archive. They do not establish tick-live or venue-identical behavior, and the protocol's existing realtime, wick, and loaded-history deltas remain applicable.
- No TVB-19 commit or artifact was reviewed. Post-range files were consulted only to confirm ancestry, unchanged reviewed inputs, and the requested HEAD corpus-tracking check.

## 3. Actionable items

1. [HIGH] Bound open-position valuation to the declared analysis window -- `analysis/paper/compare_config.py:81-101`; `docs/experiments/tvb15_paper_week1_protocol.md:248-285,343-355`; `docs/HANDOFF.md:18-30,47-52` -- Suggested fix: value with `week_rows[-1][4]`, fail clearly when the bounded window is empty, print the mark timestamp, add a regression proving that appending post-window bars cannot change a closed-window report, and regenerate every open/combined/window-end statement while retaining the user's "no official number" adjudication.
2. [MEDIUM] Separate nearest state from shared-rung parity -- `analysis/paper/parity_state.py:75-90`; `docs/experiments/tvb15_paper_week1_protocol.md:300-326`; `docs/HANDOFF.md:31-40` -- Suggested fix: report the nearest twin and chart lines independently, label shared structural matches separately, include the missing DRAM 47.39 lower and 53.39 upper 12h lines, narrow the exact-parity prose, and correct 13 cents to 1.3 cents.
3. [LOW] Make the standalone slice label carry the adjudication -- `analysis/paper/freeze_slice.py:76-80`; `docs/experiments/tvb15_paper_week1_protocol.md:359-366,403-415` -- Suggested fix: rename it to a post-freeze-entry sensitivity and print that the roster remains heat-conditioned and the result is not official performance.

## Suggested prompt

Add: "For every report with an end timestamp T, print the exact mark timestamp for each open-position value and prove the report is invariant when bars after T are appended. In parity reports, distinguish nearest line in each state from a farther structural line shared by both states; never label the latter as the former."

Verdict: NEEDS-CHANGES
