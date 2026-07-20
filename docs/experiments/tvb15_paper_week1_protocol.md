# TVB-15 Paper-Trading Week 1 -- Protocol (a-priori declarations)

Declared 2026-07-20, BEFORE the week's grades. The week grades TFC-BF v6.0
defaults (TV `USER;7c28fa0b`, live on the DRAM 5m front chart). Nothing here
is tuned mid-week.

## Window

2026-07-20 00:00 UTC -> 2026-07-27 00:00 UTC.

## What gets recorded, by what

The **Python twin** (`analysis/paper/engine.py`, replay via
`analysis/paper/replay.py`) is the recording instrument: a line-referenced
port of the v6 Pine replayed over archived Hyperliquid 5m bars (the deployed
chart TF). The TradingView instances remain the human surface and the
parity reference. Chosen over TV-alert webhooks 2026-07-20 (no new
infrastructure; the bar archive doubles as the standing HL-archiving
priority; the port risk is owned by parity grading below).

- Events log: `analysis/paper/events_week1.jsonl` (regenerated
  deterministically from the committed bars on every run).
- Scoreboard: `analysis/paper/scoreboard_week1.md` (per symbol and per exit
  class, give-back via `analysis/giveback.py`).
- Cadence: archive + replay at session touchpoints, at most 3 days apart
  (the HL 5m floor is ~17 days):

      uv run python -m analysis.paper.archive --roster analysis/paper/roster_week1.json
      uv run python -m analysis.paper.replay  --roster analysis/paper/roster_week1.json

## Roster (frozen 2026-07-20T14:31Z)

Rule: `uni == xyz`, vol24 >= $5M, OI >= $3M, then up to 5 most-positive and
5 most-negative scanner scores (hip3-alerts `/api/state`). Both directions
enabled on every symbol; the score only selects. Frozen for the week.

| symbol | tail | score | vol24 | OI | tv_mintick (source) |
|---|---|---|---|---|---|
| xyz:MRVL | long | +34 | $15.4M | $30.8M | 0.0001 (tv_symbolinfo) |
| xyz:GOOGL | long | +29 | $19.3M | $65.3M | 0.001 (tv_symbolinfo) |
| xyz:AMZN | long | +25 | $5.3M | $17.7M | 0.001 (tv_symbolinfo) |
| xyz:MSFT | long | +24 | $10.9M | $63.7M | 0.001 (tv_symbolinfo) |
| xyz:GOLD | long | +20 | $21.6M | $148.4M | 0.01 (tv_symbolinfo) |
| xyz:AAPL | short | -93 | $16.7M | $52.6M | 0.001 (tv_symbolinfo) |
| xyz:SKHX | short | -46 | $723.4M | $447.8M | 0.1 (hl_inferred; NO TV listing -- twin-only) |
| xyz:SKHY | short | -42 | $121.6M | $128.8M | 0.0001 (tv_symbolinfo) |
| xyz:NBIS | short | -40 | $15.0M | $38.7M | 0.0001 (tv_symbolinfo) |
| xyz:TSLA | short | -39 | $12.6M | $20.9M | 0.001 (tv_symbolinfo) |
| xyz:DRAM | parity | n/a | n/a | n/a | 0.00001 (tv_symbolinfo) |

Notes recorded at freeze:

- **Score rotation is fast.** Between a 12:06Z snapshot and the 14:31Z
  freeze, NBIS went +75 -> -40, SKHY +61 -> -42, AAPL fell to -93. The
  momentum-heavy score (35% r60, rvol-scaled) rotates intraday; the rule
  was frozen a-priori and the freeze time is part of the record, not a knob.
- **Scanner score != entry gate.** The score's alignment runs over
  {15m, 1h, 4h, 1d}; the v6 gate is close-vs-period-open over {D, W, M}.
  A zero-entry roster symbol is the gate doing its job.
- **xyz:SKHX has no TradingView HIP3XYZ listing** at freeze
  (symbol_search 2026-07-20): twin-only symbol; no TV parity possible.
- **xyz:DRAM** is the parity instrument (the live v6 front chart), NOT
  rule-selected; excluded from tail aggregates.

## Twin conventions (all a-priori)

- Fills: entry at the trigger (prev completed 15m arm extreme +/- 1 TV
  tick); "BF S/L Exit" at the touched line's value that bar; "BF Break" and
  "Flip" exits at the 5m close. 1x, gross, no fees/funding (matches the
  indicator's declared scope; real xyz taker ~0.01% per TVB-2).
- The twin replays CLOSED 5m bars only (every bar confirmed -- TV
  historical-recompute semantics). The last archived bar of every series is
  dropped as potentially forming.
- Warm-up: pools 12h/D/W from the 1h archive, M from the 1d archive, up to
  the week boundary; gates seeded from the same stream; positions start
  FLAT at 2026-07-20 00:00 UTC (the live chart may carry pre-week state --
  declared difference).
- v6 defaults frozen: n_max 6, min_sep 1.0, pool_cap 12, flip backstop on,
  break exit on, both directions, arm TF 15m, gates D/W/M.

## Known fidelity deltas (declared, measured where possible)

1. **Warm-history anchor resolution.** Pool anchors warmed at 1h/1d
   resolution vs the chart's 5m stamps; line values differ at the cents
   level on operative rungs and can flip touch outcomes on old lines over
   weeks.
2. **TVB15-D1 (day-1 parity snapshot, DRAM 14:30Z):** twin vs live table --
   position SHORT = SHORT; gate grey = grey; next line down 48.358 vs
   48.360 (the weekly N=4 rung, delta 0.002); D-pool structural upper
   69.61 vs 69.62; W alive 2 = 2; M 0 = 0. DIVERGENT: twin holds 4 stale
   12h lines alive (incl. an upper at 56.96) that the chart has retired --
   deep-history lifecycle drift, mechanism = delta 1. Operative rungs for
   the standing short MATCH. Watch whether a stale-line exit fires in the
   twin that the chart would not print.
3. **Tick-live vs 5m bars.** The live chart evaluates intrabar; the twin at
   5m-close resolution. Same-bar label timing/pricing can differ within a
   bar; TV's own reload-recompute is the twin's semantics.
4. **TV-vs-HL wick variance** (TVB-6 class): cents on some anchors.
5. **M pool is shallow** everywhere (and empty on young listings) -- mirrors
   the deployed 5m chart where loaded history bounds the M pool anyway.
6. **Fixture supersede-shadow (TVB-15 finding, engine side settled):** the
   TVB-14 acceptance fixture applies supersede in a second pass, so two 12h
   DRAM sides it labels "superseded" were actually TOUCHED before the
   superseding birth; Pine (and the engine) consume first
   (pine/tfc_bf_watch.pine:234 relabels only still-alive sides). Pinned in
   tests/test_paper_engine.py (FIXTURE_SUPERSEDE_SHADOWS + invariant test).
   States are retired either way; no exit impact. Carry into the TVB-14
   review synthesis.

## Grading contract

- The user's ride-along grades (screenshots, notes) are collected against
  the twin log; every user-vs-twin or chart-vs-twin disagreement becomes a
  numbered divergence **TVB15-Dn** in this file with its mechanism.
- Week-end parity pass: DRAM plus two roster symbols, TV labels vs twin
  events, differences attributed to the declared delta classes or escalated.
- Alerts on the live instances are the user's phone layer only (re-create
  after any script update; none planned this week).

## Mid-week policy (pre-declared, TVB-13 precedent)

A CONFIRMED correctness bug in v6 or the twin: fix forward, annotate the
event log with the fix commit, keep grading. Anything less than a confirmed
bug -- including ugly results -- waits for week end. No roster changes, no
default changes, no min_sep dialing on backtests.

## Out of scope this week

Tier-2 STRAT targets (present in `/api/state` per-TF blocks incl. 1w/1M;
seed for later), TV alert webhooks, cross-pool dedup, roster refresh
cadence, any v6 Pine change.
