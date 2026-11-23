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
- **No review is requested.** The owner's standing word, 2026-11-21: no external reviews while
  the work is exploratory. A review will be requested when a line of this research is about to
  become a notice field, a watch table or a rule.
- Earlier requests that were never picked up stay set aside: TVB-45 (`a914880..04d8612`) and
  TVB-44. No audit file exists for either, nor for TVB-46.
- Latest session: TVB-47 (2026-11-23). Exploratory: the exit lab (eight simple backup exits
  laid over the monthly reversal patterns of the near-miss study, on the same entries) and its
  Pine strategy mirror. No engine change, no prereg.

## Commits (for the record, not a work order)

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\\Strat_Trading_Bot\\tradingview-backtesting` | `748d83b..65b6f85` plus the docs-only close-out after it (748d83b is the commit the session started from). |

Raw bars and row files are gitignored and re-fetchable; the run command is in the receipt.
`yfinance` is not a project dependency (`uv run --no-project --with yfinance ...`).

## If a review is asked for later

Read first: `analysis/nearmiss/RECEIPT.md` item 11, then `analysis/nearmiss/exits.py` and
`run_exits.py`, then `pine/reversal_exit_lab.pine`.

Focus areas: the fill conventions (a resting level uses the best price as it stood at the
previous close; close rules fill at that close; a day touching both the profit exit and an
adverse level goes to the adverse side); the indicator arithmetic against TradingView's (seeded
averages, population standard deviation); the randomized test that holds the control and the
share-of-the-way mode equal to the near-miss walker; the Pine script's engine block (orders
rest a bar ahead, the calendar test for a period's last bar, the first-bar stop-limit, the gap
fill it closes the same bar); survivorship in the name list; whether every receipt sentence is
carried by the script's printed output and both directions are stated with equal weight.

Write any audit to `docs/reviews/tvb47-codex-audit.md` (copy `docs/reviews/_TEMPLATE.md`).
