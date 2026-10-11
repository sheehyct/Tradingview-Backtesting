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
  <!-- REQUESTED | RETURNED (audit file written) | ADDRESSED | N/A -->
- Session under review: TVB-38 (2026-10-11) -- product 3 of the data redirect: the
  STRAT-management book (no price stop, exit at a daily close against the trade with the week
  against it, a ladder of structural targets, four books beside the chance book on the same
  rows, two declared fork variants). The same session also folded the six-audit backlog
  (TVB-31..35 + the TVB-37 close-out) in 5e6c59a; that commit is a fold of returned audits and
  needs no second audit unless a synthesis is disputed.
- Requested: 2026-10-11
- Write the audit to: `docs/reviews/tvb38-codex-audit.md` (copy `docs/reviews/_TEMPLATE.md`)

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `a0c52df..HEAD`: caaba12 (prereg + ledger card, before code) and the product-3 build commit(s) after it. Verify with `git diff --name-status a0c52df..HEAD`. |

No sibling-repo commits. The candle cache, the unit rows (`manage_trades.csv.gz`), the page
output and the run logs are gitignored; the run is reproducible offline with
`uv run python -m analysis.domino.manage --as-of 2026-10-10` (3-4 minutes; needs the cached
`*_1d_20261010.json` files, which the owner's machine has).

## What to read first

1. `docs/experiments/tvb37_management_book_prereg.md` -- the contract: definitions 1-17, the
   two forks, hypotheses H2 / H3, the declared hand vectors and bug tests.
2. `analysis/domino/manage.py` -- the engine (module docstring = the short form).
3. `tests/test_domino_manage.py` -- the vectors; check each against the prereg's definition 16.
4. `analysis/domino/MANAGE_RECEIPT.md` and `results/manage_tables.md` -- every sentence in the
   receipt should trace to a table cell.
5. `analysis/domino/census.py` (`_context`, `day_events`) and `chance.py` -- the extension and
   the moved helpers; the HANDOFF entry records the byte-identical census check.
6. `analysis/domino/chart_page.py` (`management_data`, the four new sections).

## Focus areas

- **Look-ahead.** Every ladder rung is a previous complete weekly / monthly bar's extreme that
  is still unbroken in its current bar BEFORE the entry day, strictly beyond L; the exit tests
  use the day's own open / close and the calendar week's open. Find anything that uses the
  entry day's travel or a later bar's information at decision time.
- **T1 rules.** Reversal = the far wick of the bar before the setup bar; inside break off a 2
  against or a 3 = that bar's far wick; with-trend inside, 2-2 continuation, 3-2, stacked inside
  = the first rung. Check `structural()` and `targets()` against the prereg and the
  strat-methodology skill 5.1 / the resource's reversal anatomy.
- **Intraday order.** Targets are intraday, the exit is at the close; on the entry day the
  break precedes any target touch (perp bars open at the prior close). Check `walk()` and
  `book_fill()`; equality fills on targets (decimals); equality on the exit tests = not
  against.
- **Same rows.** The five books are computed on units with a T1 and a non-null 5-bar reference
  return; book C on every unit is one extra line. Check the paired-difference interval and that
  the reference equals the book view's `ret5` on the same rows.
- **Settlement.** `settle()` at the headline cap and the long cap under both clocks; censoring
  only when the data ends before both the exit and the cap; OPEN marked at the cap's close.
- **Fork 2.** Own-bar clock: weekly = last day of a COMPLETE week bucket, close against the
  week's open AND the month's open; monthly = close against the month's open alone. Check
  `own_close_days()` and the `confirm` dict; units with no month context are n/a, counted.
- **Reach denominators.** T2 after T1 among units that reached T1 and HAVE a T2; T3 likewise;
  the ceiling among units with a cap end; `died` among units with a T1 that exited before it;
  `died_r` among units that exited before one R.
- **Receipt honesty.** The "finding" paragraph and every table against `manage_tables.md`; the
  fee sentence; the tail sentence (shorts beyond -100%); the weekly / monthly sentence.
- **Page.** `management_data()` reads only `manage.json`; cells under 30 faded; the hypothesis
  table's fields exist on every row.
- **Hygiene.** ruff, tests (358 passed, 2 skipped), no secrets, no private link in the repo,
  the `.gitignore` additions, the census `--out` routing.

## What is NOT in scope

The TVB-31..35 executor findings (private repo); the chance / book engines (audited twice in
TVB-37 and folded); the regime receipt fold (folded 2026-10-11 from the TVB-35 audit).
