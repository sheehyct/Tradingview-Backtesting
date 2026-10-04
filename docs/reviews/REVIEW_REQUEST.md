# CURRENT REVIEW REQUEST -- tradingview-backtesting

> Entry point for external reviewers. If you are Codex (`/session-review`) or any other
> external review agent pointed at this repo: this file is your work order. It
> always describes the LATEST requested session review and is rewritten by
> `/session-end` each session. The permanent per-session record is the
> `### External Review` block in `docs/HANDOFF.md`; for the CURRENT request,
> this file wins if the two disagree. Full contract:
> `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Status

- Status: REQUESTED
  <!-- REQUESTED | RETURNED (audit file written) -->
- Session under review: TVB-36 -- one month of paper-platform data pulled and
  decomposed; the signals the platform never filled replayed through their own
  brackets; a random-walk baseline; two no-human regime labels; a sharp-move
  event study; a stop what-if; a trade review page builder; and the session
  docs, which carry the owner's correction that several "readings" in these
  receipts are the lead's conclusions, not settled findings.
- Requested: 2026-10-04
- Write the audit to: `docs/reviews/tvb36-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: TVB-31, TVB-32, TVB-33, TVB-34 and TVB-35 audits were never returned
  and stay open. The DEEP-DIVE review (docs/reviews/deep-dive-2026-09-05-astra.md)
  was RETURNED and FOLDED in TVB-34; do not re-review it.

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `3f087b0..__HEAD_SHA__` (pre-session sha .. head): fdee294 (September receipt + replay), 9895c61 (regime labels + sharp-move study), a9c55b1 (review page builder), 3dc8cf9 (stop what-if), plus the session-end docs commit(s). Verify with `git diff --name-status 3f087b0..__HEAD_SHA__`. |

No sibling-repo commits this session. The paper platform repo was READ, never
written; the raw account exports and candle caches are owner-local
(`analysis/parallax/exports/`, gitignored), so numbers are checked against the
committed `results/*.json` and by re-running the scripts where the public
candle API still serves the window.

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0. Then the TVB-36 HANDOFF entry, starting
   with "READ FIRST: the owner's correction at close".
2. `analysis/parallax/RECEIPT.md`, then `lostbook.py` and `census.py`.
3. `analysis/regime/REGIME_LABELS_SEPT_RECEIPT.md` with `venue_mrc.py` and
   `index_continuity.py`; `analysis/momentum/SHARP_MOVE_RECEIPT.md` with
   `sharp_move_study.py`.
4. `analysis/parallax/review/build_review.py`, `stop_whatif.py`,
   `trade_review.template.html`.

## Focus areas (scrutinize these)

1. `lostbook.py`: entry at the order's reference price (no slippage),
   bracket-only (the continuity flip is not replayed), a candle touching both
   levels counts as the stop, deduplication by signal key across accounts, and
   the 17-of-17 calibration. Is "bracket-only is pessimistic for the flip
   class" supported by the seven flip-exited trades alone?
2. `census.py`: the random-walk baseline P(target first) = 1 / (1 + R:R) and
   the z-score. The trades cluster in time and by coin; is z = -3.1 overstated
   by treating them as independent? Is "worse than a coin flip" a fair
   sentence for one month?
3. `mfe.py` / `trades.py`: software exits are matched to entries by symbol
   and time, and four of seven have no logged reason. Any mis-match?
4. `venue_mrc.py`: fidelity to `tv_indicators/pine/macro_risk_conditions_v1_2.pine`
   (change horizon, population stdev, EMA holding through gaps, staleness
   multiple, the DXY-weighted basket) and the completed-bar timing. The TLT
   series starts about 09-18; is the pre-09-18 label described honestly?
5. `index_continuity.py`: UTC day / week / month opens against the venue's
   candle boundaries, equality handling, the coupled-day count (56 of 135).
6. `sharp_move_study.py`: ATR(14)[1] by Wilder RMA, the volume confirmation
   on the two lower tiers, per-bar clustering t-stats with overlapping
   horizons, the universe chosen by September volume (survivorship), and
   whether every quoted post-hoc cut is labeled post-hoc.
7. `build_review.py`: the "reached the original target within 72 h after the
   stop" tag (15m candles, the bar containing the exit instant). `stop_whatif.py`:
   the R convention and the "resized" column.
8. The READING paragraphs in all four receipts against the owner's correction
   in the HANDOFF: flag every sentence that states a conclusion the arithmetic
   does not carry.
9. Public-repo hygiene: no hosted platform URL, no review-page link, no
   secret, no personal remark; `analysis/parallax/exports/` ignored.
10. request.security: NO Pine file changed -- verify none did.

## Output contract

- Verbatim audit -> `docs/reviews/tvb36-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value: the VPS
  IP, the master wallet address, the agent address, the paper platform's host
  and the review page's link stay out (this repo is public).
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
