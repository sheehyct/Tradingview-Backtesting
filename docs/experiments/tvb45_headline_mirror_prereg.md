# TVB-45 -- the management book's headline as a TradingView strategy(): the mirror and its parity gate -- pre-registration (DRAFT, awaiting the owner's word)

**LABEL: A MIRROR, NOT A STRATEGY CLAIM.** The owner chose the TradingView route as the viewing
surface for strategies (2026-11-02, "a good quick intermediary option") and ruled the first port:
the management book's headline (exit only C). The Python engine (`analysis/domino/manage.py`)
stays the authority; the TradingView script is valid only for the cells its parity gate passes
(CLAUDE.md). Nothing here changes the engine, the book or its receipts. The recipe is TVB-20's
(`docs/experiments/tvb20_control_port_parity.md`): a decision-exact mirror, a harvested trade
list joined to the twin's rows, every residual declared.

## Glossary (trader terms first)

- **The headline (C, exit only)**: every first break of yesterday's high (a long) or low (a
  short), no stop, no target; out at the close of the first session that closes against the
  trade with the week also against it at that close; 20 sessions and out.
- **A unit**: one such break, one position of equal size, independent of every other unit (a
  new break each day while an earlier one is still open is a second position).
- **Against**: a close below its own open for a long (above, for a short); equality is not
  against. **The week against**: that same close below the week's open for a long (above, for a
  short). The week's open is the open of the week's first session (crypto: the Monday 00:00
  UTC week; ES: the Sunday-evening-to-Friday Globex week).
- **The twin**: the engine's rows (run one for BTC, `analysis/domino/results/manage_trades.csv.gz`;
  the ES bench's Globex rows, `analysis/bench/results/bench_globex_trades.csv.gz`), with
  `ret_C` the headline's return per unit.
- **Decision-exact**: the TradingView trade list (entry session, direction, exit session) must
  match the twin's rows event for event; prices are compared where the fill model is the same
  and declared where it is not.

## 1. The object

- `pine/domino_headline_strategy.pine`, "Domino Headline C [TVB-45]", a `strategy()` on the
  DAILY chart. The local file is the source of truth; created on TradingView through the
  Make-a-copy flow with a NEW script id verified (the tab-binding trap in CLAUDE.md).
- Two charts: BTC on Hyperliquid, daily (run one's coin BTC: 1,407 units, two venue years);
  ES continuous front month, daily on the Globex session (the bench's V0: 3,824 session units,
  2011-2025). Session (daily) units only; weekly and monthly units are not in this port.

## 2. The rules, verbatim from the engine (both directions)

1. **The unit.** A session whose high trades strictly above the previous session's high is a
   long unit; whose low trades strictly below the previous session's low is a short unit; an
   outside session is both. One unit per direction per session. (`census.day_events`, strict.)
2. **The entry.** At the previous session's high (low) the instant it breaks. In Pine: a stop
   order at `high[1]` (`low[1]`) placed for the next session, each session. The broker emulator
   fills it at the level when the session trades through it, and at the session's OPEN when the
   session opens past it: on a gapped session the mirror fills at the open by construction (the
   bench's F1 convention), where the engine's control fills at the level. On the 24/7 crypto
   tape no session opens past the trigger, so the fill is the level on every unit; on ES the
   gap units (204 of 3,824 on the Globex day) are a DECLARED residual, counted and excluded from
   the price cells, never hidden.
3. **The exit.** At the close of the first session, the entry session included, whose close is
   against the trade (below its own open for a long, above for a short; equality not against)
   AND against the week's open (below it for a long, above for a short). If no such close by the
   20th session after the entry session, out at that session's close (the cap). No stop, no
   target. (`manage.walk` `exit_d`; `manage.settle` with `CAP`.)
4. **The week's open on the chart.** The non-repainting on-chart idiom (the open of the bar
   that starts a new `time("W")` period, carried forward), never `request.security` with an
   un-offset lookahead. The chart's weekly boundary must equal the engine's week for the symbol
   (crypto Monday 00:00 UTC; ES the Globex week): a gate cell, not an assumption.
5. **Every unit is its own position.** Equal size (1,000 USD notional a unit, the receipts'
   book view); `pyramiding` above the most units that can be open at once (two directions, 21
   sessions each: 42); each entry carries its own id (direction and session) so its cap closes
   it alone, while the against-close closes every open unit on that side at once (the engine's
   condition is identical for them).
6. **Pinned conventions (TVB-20's, adapted):** commission 0, slippage 0, margin 0, bar
   magnifier OFF (daily bars; the stop fill sits at a prior extreme inside the bar's range),
   `calc_on_every_tick=false`, exits filled at the exit session's close, initial capital large
   enough never to refuse a unit.

## 3. The parity gate (cells; PASS is all of them on the matching bars)

On each symbol the TradingView trade list is harvested at the data floor (the TVB-20 harvest
script adapted: deep-load, floor detection, `reportData().trades`) and joined to the twin's
rows on (entry session, direction):

- **P1 units**: every twin unit has a TradingView trade on the same entry session and side, and
  every TradingView trade has a twin unit; 100% on the overlapping feed, every difference
  listed with its bar.
- **P2 exit session**: identical, the cap included.
- **P3 entry price**: the level, float-exact (within one tick) on units whose session did not
  open past the trigger; the gap units counted as the F1 fill and reported beside.
- **P4 exit price**: the exit session's close, float-exact.
- **P5 return**: the TradingView per-unit return equals `ret_C` within rounding on the P3 units.
- **P6 the week boundary**: the script's week-open series (exported through a plot) equals the
  engine's week open on every session of the overlap.
- **P7 the bars**: the chart's daily OHLC equals the engine's bars on the overlap (run one's
  venue cache; the Databento Globex session bars); every mismatch listed. The cells above are
  read on the matching bars only; a feed difference is a finding about the feeds, not the mirror.

The gate result is written to `docs/experiments/tvb45_headline_mirror_parity.md` with every
residual named; the card's row 9 reads "on TradingView: the headline, gate PASS" only then.

## 4. Declared scope and what is not here

Session units only; the headline book only. The hourly clock (C_h) is the second port and the
chance book (one R or the setup-bar stop) the third, each with its own gate, on the owner's
word. No pattern filter (the headline takes every unit), no size rule, no cost model, no tuning
of anything. The other books (A, B, D, D5, under water, the own clock, the long cap) are not
mirrored here.

## 5. Kill tests and confounds (declared, equal weight)

1. **The feed.** TradingView's Hyperliquid daily bars against the venue's API cache (the
   session boundary 00:00 UTC; volume absent or different); ES continuous on TradingView
   against the Databento cache (the contract roll: the chart's continuous contract must be
   UNADJUSTED and its roll sessions listed against the bench's 60; a roll inside a unit is a
   feed difference, counted). P7 reads it; a feed that does not match on most bars fails the
   port, not the book.
2. **The week boundary** (P6): a Sunday-evening open that TradingView files under Monday for
   ES, a crypto week that starts in the exchange's timezone rather than UTC: either breaks the
   exit rule silently.
3. **The gap fill** (ES, P3): the mirror is the F1 convention on gapped sessions by
   construction; the bench's section 1b says what that changes (the Globex day barely moves).
4. **Pyramiding and capital**: a unit refused by the emulator for a position limit or capital
   is a parity failure, so both are set beyond the maximum.
5. **The entry session can be the exit session**: an against-close on the entry day closes the
   unit the day it opened (the engine does the same); the emulator must allow an entry and an
   exit on one bar.
6. **Out-of-scope cadence**: the daily chart evaluates completed sessions; the live realtime
   bar is not a parity object (TVB-20 audit F4 applies).

## 6. Build order (each lands tested before the next)

1. This file confirmed by the owner (section 7).
2. The `strat-methodology` skill invoked for the Pine translation of the unit, the trigger and
   the against-close (the rules are the engine's; the idiom is reviewed with the owner where
   the skill and the engine could read a bar differently: STOP-and-ASK).
3. The script written locally; `node --check`-style sanity is not available for Pine, so the
   TradingView compile is the first gate (the MCP's `pine_save` after Make-a-copy, a NEW id).
4. The harvest and the join (adapt `scripts/tvb20_port_harvest.mjs` and
   `analysis/paper/port_parity.py` to the domino rows), the gate result document.
5. `docs/STRATEGY_CARD.md` row 9 updated; the ledger card gets a line.

## 7. What the owner is asked to rule on

- The fill model on gapped sessions: the mirror fills at the open (TradingView's emulator), the
  engine at the level; declared residual, counted, excluded from the price cells. Confirm.
- Equal size per unit (1,000 USD notional) with pyramiding above the maximum open units.
  Confirm, or name another size.
- The two charts: BTC on Hyperliquid daily, ES continuous front month daily on the Globex
  session, unadjusted. Confirm, or name another pair (BTC on another venue's feed; MES).
- Session units only for the first port; the hourly clock second, the chance book third.
  Confirm.
