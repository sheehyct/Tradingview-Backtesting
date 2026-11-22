# CURRENT REVIEW REQUEST -- tradingview-backtesting

> Entry point for external reviewers. If you are Codex (`/session-review`) or any other
> external review agent pointed at this repo: this file is your work order. It
> always describes the LATEST requested session review and is rewritten by
> `/session-end` each session. The permanent per-session record is the
> `### External Review` block in `docs/HANDOFF.md`; for the CURRENT request,
> this file wins if the two disagree. Full contract:
> `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Status

- Status: N/A
  <!-- REQUESTED | RETURNED (audit file written) | ADDRESSED | N/A -->
- **No review is requested.** The owner's word, 2026-11-21 (TVB-46): no external reviews while
  the work is exploratory. A review will be requested when a line of this research is about to
  become a notice field, a watch table or a rule.
- This also sets aside the two earlier requests that were never picked up: TVB-45
  (`a914880..04d8612`) and TVB-44. No audit file exists for either.
- Latest session: TVB-46 (2026-11-21). Exploratory counts only: the November 2026 index drop
  read through the sector continuity look (`analysis/sector/`, receipt items 8 to 11); the
  near-miss study (`analysis/nearmiss/`: how close failed daily, weekly, monthly and quarterly
  reversal patterns came to their target); the owner's what-if exit. No engine, no Pine, no
  prereg.

## Commits (for the record, not a work order)

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `3594558..dd70032` plus the docs-only close-out after it (3594558 is the commit the session started from). |

Raw bars and row files are gitignored and re-fetchable; the run commands are in the two
receipts. `yfinance` is not a project dependency (`uv run --no-project --with yfinance ...`).

## If a review is asked for later

Read first: `analysis/nearmiss/RECEIPT.md`, then `analysis/nearmiss/core.py` and `htf.py`, then
`analysis/sector/RECEIPT.md` items 8 to 11.

Focus areas: the pattern levels and the walk (strict breaks, the gap rule, the order of events
inside the entry bar, the 3-2-2's stop at the 3 bar's extreme by the owner's ruling, the
went-3 exit while the entry bar is open); the randomized test that holds the daily and
higher-timeframe walkers equal; survivorship in the name list; whether every receipt sentence
is carried by a script's printed output and both directions are stated with equal weight.

Write any audit to `docs/reviews/tvb46-codex-audit.md` (copy `docs/reviews/_TEMPLATE.md`).
