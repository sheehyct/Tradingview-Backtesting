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
- Session under review: TVB-45 (2026-11-18 / 19) -- a re-grounding session after a pause. No
  arm was run, no engine and no Pine was touched. One EXPLORATORY data product was built in
  conversation with the owner and committed: `analysis/sector/`, a count-only look at timeframe
  continuity across the eleven sector SPDRs on week / month / quarter / half-year / year opens
  (cracks out of full agreement, how far they go, what the ten largest holdings and a theme
  fund were doing the day before, high-beta followers). It has no prereg, no tests of its own
  and no audit; `analysis/sector/RECEIPT.md` says so at the top and is the record. The session
  docs were updated (HANDOFF, the arm ledger card, the strategy card row, the startup prompt).
- Requested: 2026-11-19
- Write the audit to: `docs/reviews/tvb45-codex-audit.md` (copy `docs/reviews/_TEMPLATE.md`)
- Note: the first commit's message says TVB-46 by mistake; the session is TVB-45. The
  `docs/reviews/tvb44-codex-audit.md` check was not done in TVB-45 (the session did not run
  `/session-start`); if that audit exists it is still unfolded.

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `{pending push}` |

No sibling-repo commits. Raw daily bars (`analysis/sector/data/`, `analysis/sector/members/`)
and the row files the scripts write (`*.csv`) are gitignored and re-fetchable; the run commands
are in the receipt. `yfinance` is not a project dependency: the scripts run with
`uv run --no-project --with yfinance --with pandas --with numpy ...` (`cushion.py` also needs
`--with scikit-learn`). A re-fetch on a later day extends the series, so counts will differ
slightly from the receipt's (data through 2026-11-19).

## What to read first

1. `analysis/sector/RECEIPT.md`: the definitions, the trap, items 1 to 7, "Read both ways",
   the limitations.
2. `analysis/sector/common.py`: `open_matrix`, `level_state`, `episodes`, `is_deep`. The newer
   scripts (`cushion.py`, `stayed_out.py`) import it; the earlier ones (`levels.py`,
   `inside.py`, `themes.py`, `followers.py`) carry their own copy of the same logic.
3. `analysis/sector/cushion.py` and `stayed_out.py`: the two checks the receipt's conclusions
   lean on most.
4. `docs/HANDOFF.md` TVB-45 entry: the owner's direction and what the look is for.

## Focus areas

- **The level state**: the period keys (ISO week, month, quarter, half-year, year) and the
  first-trading-day open of each; shared opens collapsed by equal price after rounding to four
  decimals (two different periods that happen to open at the same price by coincidence are
  also collapsed: is that what the definition wants?); a close exactly at an open counts as
  below; unadjusted prices for states, adjusted for returns (an ex-dividend drop can flip a
  marginal state on a fund).
- **The crack walker** (`episodes`): the start index, the end on healing or on full agreement
  the other way, `lost_max` when the number of distinct levels changes during an episode (a
  period rolls mid-episode), and the jump `t = last` after an episode.
- **Look-ahead**: every "day before" read uses the member's or theme fund's state at the close
  before the sector's crack (`inside.py`, `cushion.py`, `stayed_out.py`); the cushion's levels
  and the 20-day swing are taken at that same prior close; `followers.py` labels a day by the
  sector's state at the PRIOR close; the forward tables in `stayed_out.py` count a deep crack
  STARTING within the next ten trading days and label depth with hindsight (said in the
  receipt).
- **The cushion test**: whether `d3` (distance to the third level, or the lowest when fewer
  than three are distinct) is the right arithmetic control; the train-before-2019 /
  score-after split; the date-level resampling; whether "mostly arithmetic on breakdowns" is
  what 0.694 against 0.694 and the banded table support.
- **The stayed-out tables**: the run-length counter, the bands, days against separate spells
  (the receipt says the rows are fewer independent observations than their day counts: is
  that said strongly enough?), the two-theme split for technology, the stacking table's merge
  on (sector, date).
- **The follower rule**: candidates pooled from theme funds' top-ten holdings only; the beta
  floor measured on the last two years and then described over each name's whole history
  (selection on the recent window); the 30-worst-day capture as a ratio of sums.
- **The receipt against the scripts**: every number traceable to a script's printed output;
  both directions with equal weight; the two kill tests stated as plainly as the two paths;
  nothing promoted to a rule.
- **Hygiene**: ruff clean; 525 passed, 2 skipped (no test covers `analysis/sector/`); no
  secrets, no private link, no server address; the owner's untracked files left untracked.

## What is NOT in scope

The owner's direction for the workspace (undecided at the close); the ATLAS workspace and its
server (another repo; the session only read it and stopped three unused services on the
owner's word); TheStrat Suite itself (an outside project, read for reference); the STRAT skill's
wording (flagged for the owner, not changed); the carried TVB-44 items (the TradingView port
prereg draft, the pairs and bench receipts awaiting the owner's reading).
