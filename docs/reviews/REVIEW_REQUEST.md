# CURRENT REVIEW REQUEST -- tradingview-backtesting

> Entry point for external reviewers. If you are Codex (`/session-review`) or any other
> external review agent pointed at this repo: this file is your work order. It
> always describes the LATEST requested session review and is rewritten by
> `/session-end` each session. The permanent per-session record is the
> `### External Review` block in `docs/HANDOFF.md`; for the CURRENT request,
> this file wins if the two disagree. Full contract:
> `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Status

- Status: RETURNED -- audit written 2026-10-10 to `docs/reviews/tvb37-chance-codex-audit.md`
  (verdict NEEDS-CHANGES, 8 findings, no remaining look-ahead found); synthesis in the TVB-37 HANDOFF entry.
  <!-- REQUESTED | RETURNED (audit file written) | N/A -->
- Session under review: TVB-37 (IN PROGRESS -- second mid-session request by the
  owner, 2026-10-10). The work under review is the CHANCE COMPARISON: for every
  daily, weekly and monthly level break on every live perp (venue era), the
  chance of one R before the stop within 1 / 3 / 5 bars, with the same STRAT
  pattern put side by side plain (yesterday's level alone) and stacked (an
  unbroken weekly or monthly level at or just beyond the trigger). Gross, no
  fees, no sizing, no P&L. The census audit (first request) is folded and
  ADDRESSED; do not re-review it.
- Why it is reviewed now: the owner will read the receipt's comparisons and a
  hypothetical-book view is being built on the same unit rows. A look-ahead
  defect was already caught and fixed by the session (prereg amendments A1 and
  A2): the first version classed a daily trigger by which higher levels BROKE
  THAT DAY. The reviewer's first job is to hunt for any REMAINING look-ahead or
  selection-on-outcome in a condition column.
- Requested: 2026-10-10
- Write the audit to: `docs/reviews/tvb37-chance-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: the first TVB-37 audit is `docs/reviews/tvb37-codex-audit.md`
  (census, folded in commit 4560e7c). Files in the working tree that are NOT in
  the range below (for example `analysis/domino/book.py`, `BOOK_RECEIPT.md`)
  are being written while you review; ignore them.

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `4560e7c..c0f1826`: 25a8ac5 (chance prereg + ledger card, before code), c0f1826 (engine `analysis/domino/chance.py`, tests, receipt, prereg amendments A1 / A2, HANDOFF, ledger numbers, and a refactor of `analysis/domino/census.py` that exposes `day_events` / `shared_opens` for reuse). Verify with `git diff --name-status 4560e7c..c0f1826`. |

The unit rows (`analysis/domino/results/trades.csv.gz`, 29 MB) and the candle
cache are gitignored; `uv run python -m analysis.domino.chance` regenerates them
from the cache in about three minutes (no API call beyond the universe list).
Committed numbers: `analysis/domino/results/chance.json` (headline cells) and
`results/chance_tables.md` (every table, every split, every sample).

## Read first (in this order)

1. `docs/experiments/tvb37_chance_comparison_prereg.md` -- definitions, then
   amendments A1 and A2 at the end. The code must implement the amended
   definitions exactly.
2. `analysis/domino/CHANCE_RECEIPT.md`.
3. `analysis/domino/chance.py`; `analysis/domino/census.py` for `day_events`,
   `shared_opens`, `_context`, `aggregate`, `shape_flags`, `setup_kind`.
4. `tests/test_domino_chance.py`.
5. `docs/ARM_LEDGER.md` (the chance card) and the TVB-37 entry in
   `docs/HANDOFF.md` (section "Product 2").

## Focus areas (scrutinize these)

1. **Remaining look-ahead.** Every column used as a CONDITION or a SPLIT must
   be knowable at the entry instant (the strict break of the unit's level):
   `kind`, `flag` (shape of the setup bar, the PREVIOUS bar), `cls` via
   `entry_class` (daily) and `stack_class` (weekly / monthly), `near_tf`,
   `m_support`, `quarter`, `year`, `liquid` (today's membership applied
   backwards, disclosed), `direction`. Is `cls` for a WEEKLY unit truly
   entry-time (yesterday's level vs the weekly level at the weekly break)? Is
   the "spread" class of a weekly unit a momentum condition (the day already
   ran 1%+) rather than a look-ahead? Is `stack` used anywhere as a condition?
2. **The nesting assertion** (`stack_class`, `entry_class`): the claim that an
   unbroken higher level is never short of yesterday's level on the same bar.
   Is the argument in the prereg correct on the first day of a new bar (Monday
   / the 1st) and on a plain day? Could a gap day or an off-grid stamp break it
   (the census engine now rejects both)?
3. **The walker** (`walk`): pessimistic same-day rule (stop and target the same
   day = stop), orders fill on touch (equality fills; R10 is about breaks, not
   fills), the entry bar included in every horizon, `res_j <= end`, censoring
   when `end is None`, MFE / MAE as price travel from the level, `stop0`. Is the
   entry-day stop touch counted even when the day's low came BEFORE the break
   (declared pessimistic) and is that disclosed?
4. **Horizons** (`horizon_ends`): daily = i + N; weekly / monthly = the last day
   of bucket b + N only if that bucket is complete. Is bucket adjacency
   guaranteed (the census engine excludes coins with gaps)? What happens when
   the entry bar itself is the incomplete last bucket?
5. **Follow-through** (`next_bar`): daily next bar vs the entry day; weekly /
   monthly next bucket vs the entry bucket, both complete. Correct mapping to
   with / against for shorts?
6. **Units are not pooled across timeframes**: a D + W day is one daily unit
   and one weekly unit; every table filters on `tf`. Any place they mix?
7. **Variant stop**: `vstop` = last week's low (long) / high (short); wrong-side
   units counted and excluded; R for the variant is a different distance and
   the receipt says the two are not compared. Anything misleading?
8. **Cell statistics** (`cell`, `wilson`, `diff_interval`): denominators
   exclude censored and n/a; nested flag levels (THIRD includes STRICT)
   disclosed; the MIN_CELL greying; `flag_mask`. The difference table's base:
   plain for daily, within1 + spread for weekly / monthly. The hypothesis-1
   table. Any sign error for shorts?
9. **venue_era**: first day with volume > 0; a coin with zero-volume days AFTER
   its first trade keeps them; is that stated? ALL vs VENUE ERA as a check line.
10. **The census refactor**: `day_events` + `shared_opens` extracted from
    `analyze_coin`; the session re-ran the census and reports byte-identical
    `splits` and `coins`. Read the diff and confirm the extraction preserves
    every branch (the skipped-day count, the violation check, the unknown-kind
    counters).
11. **Receipt honesty** (`CHANCE_RECEIPT.md`, "What the arithmetic says"): does
    every sentence follow from the tables? Are the R-size confound, the
    clustering caveat and the pessimistic rule stated where they bite? Is the
    TRAP table labelled so that it cannot be read as a result? Is "hypothesis 1
    reads as supported on the weekly" a fair sentence given the R-size
    difference (24% vs 14-20%)?
12. **Tests** (`tests/test_domino_chance.py`): which behaviours have NO vector
    (weekly / monthly `stack_class` classes, a short-side walker with equality
    fills, censoring on the daily side, `cell` denominators, `flag_mask`,
    `venue_era` with later zero days, the variant stop wrong-side count)?
13. **Public-repo hygiene**: no secret, host or personal remark in the range;
    `trades.csv.gz` and `chance_run.log` ignored.
14. **request.security**: NO Pine file changed -- verify none did.

## Output contract

- Verbatim audit -> `docs/reviews/tvb37-chance-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value (this
  repo is public).
- The critical synthesis is written by the session into `docs/HANDOFF.md`.
