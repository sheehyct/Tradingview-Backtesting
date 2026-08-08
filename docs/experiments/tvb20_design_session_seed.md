# TVB-20 Design-Session Seed -- Layering Arc + User Rule-Base

> Captured 2026-08-08 (TVB-20) from a direction-alignment discussion with the user,
> BEFORE the control strategy() port. Status: INPUT to the upcoming exit/entry design
> session (plan mode). Nothing in this file is pre-registered; it is the raw material
> the design session turns into pre-registered arms. Companion amendments landed the
> same day: charter S3.1/S5 annotations + the CLAUDE.md "Ablation, not tournament"
> reword (same commit as this file).

## Confirmed direction (user, 2026-08-08)

The research program is a LAYER STACK, tested as a sequence of ablations -- each
layer is one pre-committed block that must beat the control without it:

1. Layer 1 -- TFC-only entries. The original "what if" test (continuity alone, no
   patterns); worked better than expected, crude implementation.
2. Layer 2 -- Broadening-formation exits (`pine/tfc_bf_watch.pine` v6.1). Born from
   the give-back problem: winners reaching the move in a day, then spending a week
   handing it back. Deployed live surface, paper-week-1 graded.
3. Layer 3 -- TheStrat Magnitude + Targets (`pine/strat_magnitude_targets_plus.pine`):
   setup dictionary + trigger level + target ladder (T1 = reclaim level, T2+ = prior
   signal-TF extremes not yet taken out) + position health (IN-FORCE / RETRACEMENT /
   POTENTIAL 3) + chop counter. Built with the user's STRAT collaborator. NOT yet
   backtested in any form; Tier A was twin-only by design.

Sequencing confirmed by the user: control strategy() port + parity gate FIRST (the
measuring stick), then ONE design session covering exit redesign + Magnitude+Targets
layering together, then Tier B pre-registration.

## Point 1 -- Pattern dictionary (a-priori, not swept)

- The user will supply the list of setups they actually trade live; that fixed list
  is the layer-3 dictionary. No per-pattern selection on sample performance.
- NUANCE (user): patterns alias across timeframes -- e.g. a 3-1-2 Chicago on a lower
  TF can be a 3-2 one aggregation up (the 3 and the 1 merge into a single outside
  bar). Any per-TF pattern census must expect the same event to carry different
  names at different resolutions. 2-2 reversals are the most common pattern.
- Candidate labeled-overfit test (user proposal): on ONE timeframe, census which
  patterns are most COMMON, then among the common ones which perform best --
  explicitly framed as balancing "not too many or too few trades" against "trades
  that are actually worthwhile". Runs under the DELIBERATE-OVERFIT ceiling label:
  frequency census = exploration, performance ranking = ceiling-mapping, promoting
  a winner = forbidden.

## Point 2 -- BF-proximity entry veto (exhaustion filter)

- Confirmed mechanical reading: it is a VETO, not an attraction. A long that
  triggers within X of the TOP of the governing BF (mirror for shorts at the
  BOTTOM) is "late to the game" -- short-term exhaustion risk (profit-taking or
  reversal); the move has largely already occurred. Analogy given: shorting a stock
  already down big, or buying at recent/all-time highs.
- Placeholder X = 1 percent. Exact value is a design-session variable, possibly
  ATR-scaled.
- Unification note: v6.1's BF lines already ARE the harvest targets, so this veto
  is equivalently a MINIMUM-MAGNITUDE requirement -- do not enter when the first
  harvest target is already at hand. Layers 2 and 3 meet in the same object.

## Point 3 -- User preset rule-base ("how complex do we have to make this?")

A deliberately simple candidate ruleset, supplied as a hypothesis (user: "I have no
idea if it will fail or do well"). Likely the spine of the design session; the
components below are the parameters to test, not commitments:

- Signal TF: 1 hour or less (pattern from the layer-3 dictionary).
- Target floor: Target 1 must be far enough away to cover fees and ensure real
  profit if hit; distance floor possibly ATR-derived (fixed percent floors do not
  transfer across indices / slow movers vs fast tickers).
- Exit arms: (a) always exit at Target 1; (b) allow up to 2-3 targets before exit
  (user leans 2).
- TFC chop veto: no entry within +/- ~2 percent (ATR-scaled candidate) of the
  continuity FLIP level. Purpose: stay out of the region where continuity is being
  won and lost repeatedly. Mechanically computable today: the flip levels are the
  D/W/M period-open gate levels the twin already tracks.
- BF context: the 1-DAY broadening formation as the governing structure; expand to
  a higher TF if too tight.

The framing question the design session must answer: "If we have a pattern on a
1-hour timeframe, continuity, and are not close to a known exhaustion area, is that
all we need?" -- minimal sufficient complexity, tested against the layer-1+2
control, not assumed in either direction.

## Standing constraints that bind the design session

- Ablation vs continuity-only control per layer; the charter S5 shape.
- Timeframe sets and dictionaries chosen a-priori, never tuned on the sample.
- Deliberate-overfit sweeps stay labeled in-sample ceilings; the spread is the
  finding; no cell promoted.
- strat-methodology skill mandatory for any trigger/stop/target mechanics; any
  ambiguity = STOP and ASK.
