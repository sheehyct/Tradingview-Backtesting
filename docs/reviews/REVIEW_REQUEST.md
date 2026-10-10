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
- Session under review: TVB-37 (IN PROGRESS -- mid-session request by the owner,
  2026-10-10). The work under review is the daily / weekly / monthly domino
  CENSUS: a pre-registered count of how often the venue's perps take out
  yesterday's level together with last week's, last month's or last quarter's
  level for the first time, with the distance between the levels, the setup kind
  (2-2 reversal, 2-2 continuation, 1-2, 3-2), hammer / shooter flags on the
  setup bar, and the quarter state. No entry, stop, target, outcome or P&L exists
  in this range.
- Why it is reviewed now: the next data product (a pattern-matched "chance"
  comparison -- the same pattern with and without the stacked higher-timeframe
  level) will reuse this engine's event definitions and rows. A definitional
  bug here propagates into everything downstream. The owner asked for this
  review explicitly.
- Requested: 2026-10-10
- Write the audit to: `docs/reviews/tvb37-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: the TVB-37 HANDOFF entry does not exist yet (the session is open); the
  prereg and the receipt named below are the session record for this request.
  TVB-31 .. TVB-35 audits were never returned and stay open; TVB-36 was waived
  by the owner (N/A). Do not re-review those ranges.

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `ecc4d6c..8b800a7`. The code is all in 8b800a7 (census prereg, engine, tests, receipt, ledger card, .gitignore). 342b319 and b22d77a are doc moves (HANDOFF archive, TVB-36 waiver) -- skim only. Verify with `git diff --name-status ecc4d6c..8b800a7`. |

No sibling-repo commits. The candle cache (`analysis/domino/data/`) and the
rank 2+ event rows (`analysis/domino/results/events_rank2plus.csv.gz`) are
gitignored; `uv run python analysis/domino/census.py` regenerates both from the
public candle API (about 25 minutes cold; the cache makes re-runs fast).
Committed numbers: `analysis/domino/results/census.json` and `results/tables.md`.

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0 (`docs/ATLAS_Timeframe_Continuity_Charter.md`).
2. `docs/experiments/tvb37_domino_census_prereg.md` -- the definitions, fixed
   before the code. The code must implement THESE, not a reasonable variant.
3. `analysis/domino/RECEIPT.md` -- the numbers and the "What the arithmetic
   says" paragraph.
4. `analysis/domino/census.py`, then `tests/test_domino_census.py`.
5. `docs/ARM_LEDGER.md`, section "Data products (counts, not arms)".

## Focus areas (scrutinize these)

1. **Calendar bars from dailies** (`aggregate`, `week_start`, `month_start`,
   `quarter_start`, `next_start`): week opens Monday 00:00 UTC, month on the 1st,
   quarter on Jan / Apr / Jul / Oct 1; the partial first bucket is dropped; the
   forming day is excluded. Look for off-by-one at bucket edges (a coin listed
   mid-week, a 31-day month, a missing day in the venue history, a duplicate
   candle). Does a GAP in the daily series (no candle for a day) leave the bar's
   high / low honest, or does it shift a day into the wrong bucket?
2. **Levels and first-break-only** (`_context`, `analyze_coin`): the level is
   the previous COMPLETE bar's high / low; a break counts only if the running
   extreme of the current bar BEFORE today had not already exceeded the level.
   On the first day of a new week the running extreme is empty. Is the
   comparison strict everywhere (equality never breaks, ruling R10), including
   the "had not already exceeded" test?
3. **The shared-open EXACT stack**: on a Monday the daily level is Sunday's
   high / low, which can equal the weekly level. Is that distance exactly zero
   (prices parsed consistently so equal prices compare equal as floats), and
   does the daily break then imply the weekly break? The receipt reports 5,003
   of 5,056 exact stacks on shared-open days and 53 on plain days -- what
   produces the 53?
4. **Nesting invariant**: every week / month / quarter first break must also be
   a daily break that day (reported 0 violations). Is the check itself sound,
   or could it pass vacuously?
5. **Distance band** (`distance_band`): largest pairwise gap among the broken
   levels as a percent of the lowest level; bands EXACT / NEAR <= 0.25% /
   WITHIN 1% / SPREAD. Boundary inclusivity as declared in the prereg?
6. **Setup kind** (`classify`, `setup_kind`): the previous bar of each
   timeframe classified against ITS predecessor (2U / 2D / 1 / 3); REVERSAL =
   a 2 against the break, CONTINUATION = a 2 with it, INSIDE BREAK = 1,
   OUTSIDE BREAK = 3. For week / month / quarter, are BOTH bars complete bars?
7. **Hammer / shooter flags** (`shape_flags`): THIRD = open and close both in
   the far third of the setup bar's own range (top third when the break is up,
   so the 2D setup bar is tested as a hammer; bottom third for a down break, a
   shooter); STRICT = THIRD plus the wick beyond the body on the far side at
   most 10% of the bar's range. Zero-range bars. Are the flags reported on
   REVERSAL setups only, as the receipt table says?
8. **Quarter state** (`_quarter_state`): the seven states are exhaustive and
   mutually exclusive? "unknown" iff no complete prior quarter?
9. **Counting and denominators**: one coin-day can carry an up AND a down event
   (an outside day). Is that disclosed and handled consistently in the rates?
   The headline "15.9% of all breaks" uses events as the denominator, "14.7 per
   100 days" uses closed days -- are both computed as stated?
10. **LIQUID** (`liquid`): median over the last 30 closed days of candle volume
    times close. Is the venue's candle `v` base-asset volume, so that `v * c` is
    USD notional? If `v` were already notional the floor is wrong by a factor
    of price.
11. **Data fetch** (`fetch_daily`): the 5000-candle cap and paging, the forming
    day exclusion, cache staleness, delisted names excluded (survivorship --
    is it stated in the receipt?).
12. **Receipt honesty**: does every sentence in "What the arithmetic says (and
    nothing more)" follow from the tables? Flag any sentence that reads as a
    conclusion the count does not carry (owner's standing correction, TVB-36).
13. **Tests**: which of the behaviors above have NO hand vector (quarter state,
    LIQUID, month aggregation, gap days)? Name the missing vectors.
14. **Public-repo hygiene**: only the public candle API URL is added; no secret,
    no host, no personal remark; the data and event-row files are ignored.
15. **request.security**: NO Pine file changed -- verify none did.

## Output contract

- Verbatim audit -> `docs/reviews/tvb37-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value (this
  repo is public).
- The critical synthesis is written by the session into `docs/HANDOFF.md`.
