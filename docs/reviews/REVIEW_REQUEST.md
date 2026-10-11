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
  <!-- REQUESTED | RETURNED (audit file written) | N/A -->
- Session under review: TVB-37 close-out (2026-10-04 .. 2026-10-10) -- the data
  redirect: a domino census, a chance comparison and an equal-size book view
  on every daily / weekly / monthly level break across 292 live perps, plus a
  private chart page builder. Two mid-session audits already covered the
  census engine (`docs/reviews/tvb37-codex-audit.md`, folded in 4560e7c) and
  the chance engine (`docs/reviews/tvb37-chance-codex-audit.md`, folded in
  dadf8ef). THIS request covers what those two did not: the census fold
  itself, the book view, the R-matched check, the chart-page builder, the
  second fold, and the close-out docs.
- Requested: 2026-10-10
- Write the audit to: `docs/reviews/tvb37-close-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: TVB-31 .. TVB-35 audits were never returned and stay open; TVB-36 was
  waived by the owner (N/A). Do not re-review the two folded TVB-37 ranges
  except to check that their findings were folded as the HANDOFF syntheses say.

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `ea58c6c..9e0f95e`. Unreviewed inside it: 4560e7c (census audit fold), cff7932 (request pointer), dadf8ef (book view + R-matched + chart-page builder + second audit fold), and the close-out docs commits. Already reviewed inside it: 25a8ac5, c0f1826. Verify with `git diff --name-status ea58c6c..9e0f95e`. |

No sibling-repo commits. The candle cache, the unit rows (`trades.csv.gz`), the
page output (`chance_book_page.html`) and the run logs are gitignored;
`uv run python -m analysis.domino.chance`, then `-m analysis.domino.book`, then
`-m analysis.domino.chart_page` regenerate them from the cache (about ten
minutes in all). Committed numbers: `analysis/domino/results/*.json` and
`results/*_tables.md`.

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0. Then the TVB-37 HANDOFF entry: rulings,
   products 1 / 2 / 2b, both audit syntheses, "Context for next session".
2. `docs/experiments/tvb37_chance_comparison_prereg.md`, amendments A3 and A4.
3. `analysis/domino/BOOK_RECEIPT.md`, then `analysis/domino/book.py` and
   `tests/test_domino_book.py`.
4. `analysis/domino/chart_page.py` (no tests; the page is a view).
5. `analysis/domino/RECEIPT.md` and the census fold in `analysis/domino/census.py`
   against `docs/reviews/tvb37-codex-audit.md` F1-F12.

## Focus areas (scrutinize these)

1. **Book arithmetic** (`book.coin_book_rows`, `book_cell`): +R% on one R, -R%
   on the stop, the signed move to the horizon's last close when neither
   (sign for shorts), censored units excluded, the by-entry-date cumulative sum
   and its drawdown, the dollar figures labelled as sums of equal-size trades
   and not an account balance.
2. **R-matched check** (`r_matched`): quintile edges on the BASE, `searchsorted`
   with `side="right"`, the weighting by the stacked group's bin shares, the
   renormalisation when a bin has no base units, the variance formula and the
   95% interval, `covered`. Is "reweight the base to the stacked group's bar
   sizes" what the code does?
3. **Curves** (`_curve_points`): downsampling keeps the last point; dates are
   entry dates; many trades open at once.
4. **Chart page** (`chart_page.build_data`): every number on the page comes
   from `chance.json` or `book.json`; `hit` is the one-R share; the matched
   rows filter (`flag == all`, `n_stacked >= 30`); labels match the receipts'
   vocabulary; nothing invented. No test covers it -- say so.
5. **The census fold** (4560e7c) against audit findings F1-F12: gap / duplicate
   proofing, the any-rank nesting check, decimal bands, the events-vs-days
   denominators, exclusions recorded, the venue-era split. Re-run claims
   (byte-identical splits after the `day_events` refactor) -- plausible from
   the diff?
6. **Receipt honesty** (`BOOK_RECEIPT.md`): each sentence of "What the
   arithmetic says" against the tables; the pessimistic same-day caveat; the
   R-size and clustering caveats; "the one daily A+ class in the black" --
   does the table support it; the weekly "biggest positive" sentence.
7. **Prereg A3 / A4**: do the engines implement A3 as written (bins, book
   rules, horizons 3 and 5) and does A4 describe the tables as built?
8. **Tests**: `tests/test_domino_book.py` (3 vectors) -- which book behaviours
   have no vector (short-side mark-to-market, censored exclusion in
   `book_cell`, `r_matched` renormalisation, `_curve_points`)?
9. **Public-repo hygiene**: no claude.ai artifact link anywhere in the range
   (it lives only in the lead's private memory), no host, no secret, no
   personal remark; `chance_book_page.html`, `trades.csv.gz`, run logs ignored.
10. **request.security**: NO Pine file changed -- verify none did.

## Backlog (also open, never returned; one audit file each)

The owner runs these with `docs/reviews/CODEX_BACKLOG_PROMPT.md`. Ranges are
pinned in each session's HANDOFF External Review block (TVB-31 / 32 in
`docs/session_archive/HANDOFF_TVB27-TVB32.md`); sibling-repo ranges are local
transport only.

| session | this repo | hip3-executor (private, local) | audit file |
|---|---|---|---|
| TVB-31 | `0d7437c^..7bfde0f` | `4e384bb^..4e384bb` (+ scanner d0fe9e7 / 7723462) | `tvb31-codex-audit.md` |
| TVB-32 | `5b194a2..7a29dad` | fd4db97, 35a73a4, 2dc9490, 68dca79, cbea184 -> e2a91ad, 4b5d248 | `tvb32-codex-audit.md` |
| TVB-33 | `7a29dad..7ad92f4` (first commit = TVB-32's pin) | `4b5d248..d8a07b0` (derived; confirm) | `tvb33-codex-audit.md` |
| TVB-34 | `7ad92f4..00d243e` | `d8a07b0..5cd2b0d` | `tvb34-codex-audit.md` |
| TVB-35 | `848db00..3f087b0` | `5cd2b0d..fc90368` | `tvb35-codex-audit.md` |
| TVB-36 | waived (N/A) | -- | -- |

## Output contract

- Verbatim audit -> `docs/reviews/tvb37-close-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value or the
  chart page's link (this repo is public).
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
