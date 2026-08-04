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

## Fix-forward record (pre-declared policy exercised)

- 2026-07-20 (day 1): the TVB-14 external audit RETURNED (NEEDS-CHANGES,
  docs/reviews/tvb14-codex-audit.md). Both HIGH findings were confirmed and
  independently reproduced by TVB-15 before acting: F1 supersede-before-
  ghost silently deleted an unchanged still-valid side (committed DRAM
  cases D F17/F18 + 12h F23/F24; live AAPL twin lost a D lower at -13.9%);
  F2 pool_cap evicted alive lines (census reproduced to the digit: 12h
  54 births / 42 evictions / 22 alive-at-eviction, D 27/15/6) and the
  acceptance fixture omitted the cap entirely -- roster sweep found
  evicted-alive rungs at 4-8% on AAPL/MSFT/GOOGL/GOLD/TSLA including the
  standing TSLA short's -7.4% harvest rung.
- v6.1 deployed same day (user-ratified: retired-first eviction + full
  bundle): per-side supersede, retired-first eviction with a visible
  evict-alive counter, non-tiling chart-TF warning, min_sep relabeled
  provisional. Saved 16:04Z (script version 6.0 -> 7.0 on USER;7c28fa0b),
  on the DRAM 5m chart ~16:08Z. Twin engine updated in lockstep (v6.0
  mode retained behind flags for the fixture-parity goldens; regression
  pins: v6.0 evict-alive 22/6 -> v6.1 13/1; DRAM alive sides restored
  10 (12h) + 6 (D)).
- Week-log impact: NONE -- the re-replay under v6.1 produced the identical
  18 events (no affected line had been touched before the fix), so the
  event log is continuous with no retroactive mutation. The live chart ran
  v6.0 from Mon 00:00Z to ~16:08Z; chart-vs-twin label differences in that
  window attribute to the fixed defects.
- Post-fix parity (DRAM, first read after deploy): alive counts EXACT on
  all four pools (chart 13/11/2/0 = twin 13/11/2/0); on-chart evict-alive
  14 vs twin 15 (history-depth class); next-line values agree once each
  line's slope is projected across the 1.6h evaluation-time gap
  (48.349/57.041 chart vs 48.358/56.955 twin at 14:30Z data). Delta note
  2 (TVB15-D1) is therefore substantially RESOLVED: the day-1 stale-line
  divergence was mostly audit-F1/F2 behavior, not warm-history resolution.
- Still open from the audit, deliberately deferred to week end: the
  last-only supersede search (duplicate-line class, audit F1 second half),
  fixture assertion/interleave remediation (F3; the twin engine + goldens
  already serve as the parity oracle), and the min_sep holdout-freeze
  protocol (F5).

## TVB-16 mid-week check-in (2026-07-22)

Recorded during the ride-along refresh. NONE of it changes the frozen
a-priori config or the week-1 record; design work is deferred to week end
per the mid-week policy.

### Ride-along refresh

Archive + replay advanced the record from the day-1 freeze (07-20 14:30Z) to
07-22 02:05Z. Deterministic and additive: the 18 day-1 events reproduced
byte-identically, 20 day-2 events appended (18 -> 38); 24 paper goldens
green. 15 closed trades, 8 open. Closed exit classes: BF harvest 8/8 green
(+1.82% avg, 0.14pp give-back), BF adverse-break 2 (-0.75%), flip backstop 5
(-2.10%, 4.18pp give-back). Realized sum +2.59pp; open mark-to-market ~-49pp
across all 8 open positions (incl. DRAM), three shorts dominating.

### Headline finding -- config-invariant adverse-runner exit gap

Three shorts (NBIS -22%, DRAM -13%, MRVL -11%) entered within the first
~2.5h of the week from the flat seed and rode a rally ~49h with NO exit.
Mechanism confirmed by dumping gate + alive-line state (not inferred): all
three read D=down / W=up / M=down, so the flip backstop (needs full D/W/M up)
never arms; the nearest alive adverse (upper) BF line sits 3-17% above price,
so no break exit fires; price rose in open air with no line in the path. The
flat-seed entry timing (a declared delta) placed the entries right before the
rally and materially inflates the severity. This is the week's headline
finding; the fix (flip full-vs-partial D/W/M granularity, or a structural
stop for open-air adverse runs) is a STOP-and-ASK methodology question to
design WITH the user at week end -- carried from the TVB-14 open
"flip-backstop granularity" item.

### Ablation -- frozen control vs the user's live variant (measurement, not a change)

`analysis/paper/compare_config.py` runs the same committed week-1 bars
through two configs: control = 15m arm + 12h/D/W/M pools (shipped defaults);
variant = 1H arm + D/W/M pools (12h off, the user's manual live settings).

| metric | control (15m, 12h on) | variant (1H, 12h off) |
|---|---|---|
| closed trades | 15 | 9 |
| BF harvest | 8 @ +1.82%, gb 0.14 | 3 @ +3.94%, gb 0.07 |
| flip backstop | 5 @ -2.10%, gb 4.18 | 5 @ -2.12%, gb 4.15 |
| realized sum | +2.59pp | +0.76pp |
| open MTM sum (roster, DRAM excl) | -35.95pp | -35.44pp |
| combined | -33.36pp | -34.68pp |

Reading: 12h-off had LOWER realized on this sample (the 12h pool was
harvesting winners, not noise), but its harvests were fewer/bigger/cleaner
(+3.94 vs +1.82, gb 0.07 vs 0.14) -- the "12h harvests too eagerly"
intuition, measured. Combined P&L is ~equal (both ~-34pp): the two knobs
mostly RE-TIME the same book (give-back/timing), not change its edge. The
three stuck shorts are IDENTICAL across configs (NBIS -22.1/-22.4, MRVL
-11.0/-11.1, DRAM -13.2/-13.4) -- the adverse-runner gap is invariant to both
knobs. Caveat: 2 days, one rally regime, 9-15 trades -- a measurement to
populate over more regimes, not a verdict. The frozen control remains the
week-1 record.

## TVB-18 week-end pass (2026-08-03)

The window closed 2026-07-27 00:00 UTC; this pass closed out the record six
days later (archive floor allowed it -- the 07-20 window start survived).

### Close-out mechanics

Archive advanced all 11 symbols through 08-04 00:45Z (5m/1h/1d; merged
series span 07-03 -> 08-04). Replay regenerated the week window
deterministically: the 38 committed events reproduced BYTE-IDENTICALLY and
43 appended (38 -> 81; 44 entries / 37 exits). Full suite green (97 passed,
2 skipped) including the 24 paper goldens.

### Week-1 final (frozen control, gross, 1x; roster aggregates excl DRAM)

- Realized: 37 closed trades, -27.61pp. Open MTM at window end: -40.65pp
  across 7 opens. Combined: -68.25pp.
- Exit classes: BF harvest 24 @ +1.86% avg, gb 0.24pp (100% win BY
  CONSTRUCTION -- the exit IS a profitable line touch); BF adverse-break 7
  @ -8.15% avg, gb 9.19pp (worst NBIS -26.82%, MRVL -14.32%); flip
  backstop 6 @ -2.54% avg, gb 4.38pp.
- The mid-week stuck shorts REALIZED their damage: NBIS -26.82% and MRVL
  -14.32% finally exited via adverse-break (give-back 28.10pp and 15.63pp
  from positive MFE). DRAM's parity short (07-20 02:25) never exited all
  week: -13% trough, +4.7% at the window end -- a full adverse round-trip
  ridden with no line in the path, in both directions.
- NEW adverse runners formed from genuine MID-WEEK signals: GOOGL short
  (07-23 13:30) -15.8% and AMZN short (07-23 14:00) -19.5% open at window
  end. The exit gap is therefore NOT a flat-seed artifact; the flat-seed
  delta only inflated the first-2.5h cohort's severity.
- Counterexample: TSLA 8/8 harvests, +18.99pp, gb 0.39pp -- the harvest
  engine performs when rungs keep appearing in the price path. One
  adverse-break erases roughly 4-14 average harvests; that asymmetry is
  the week's design question (carried to the adverse-runner design
  session).

Heat-conditioning (stated per contract): the roster is scanner-score
extreme-selected at freeze, graded across ONE regime (a broad rally against
the short tail). This characterizes EXIT CLASSES on heat-selected names;
it is not a strategy-edge estimate.

### Full-week ablation (control vs user live variant)

compare_config over the closed week: control -27.60 realized / -40.65 open
/ -68.25 combined; variant (1H arm, 12h off) -15.44 / -47.69 / -63.13.
Confirms the TVB-16 mid-week reading at full-week scale: the two knobs
RE-TIME the same book rather than change its edge -- the variant converts
realized damage into still-open damage (MRVL realized -14.32 vs still-short
-2.8; AAPL realized -1.06 vs open long -9.0), harvests get fewer but bigger
(24 @ +1.86 -> 14 @ +3.23), and the adverse-runner class is config-invariant
in scale and membership.

### Parity pass (DRAM + TSLA + GOOGL, read 2026-08-04 ~01:00Z)

Context that changed the instrument: the deployed accumulated-history v6.1
chart instances were REMOVED from all saved layouts during the user's
post-week pivot (the "DRAM" front layout now shows NASDAQ:SNDK with a
community "Strat Assistant" study; layout "5x" holds bare DRAMUSDC.P).
Strong-form census parity (TVB-15's exact 13/11/2/0) is no longer
reproducible by anyone. These reads are FRESH MOUNTS of USER;7c28fa0b v7.0
(table title v6.1) at source defaults on a scratch layout (TVB18-parity),
which compute only over TV's initial ~3-week 5m load. Twin side:
`analysis/paper/parity_state.py` (control config), replayed week-start ->
archive tip 08-04 00:45Z.

| surface | twin @ tip | chart (fresh mount) | verdict |
|---|---|---|---|
| DRAM position | SHORT @48.231 since 07-28 13:40 | SHORT | MATCH |
| DRAM gate | D dn, W dn, M up (tip close 50.08 > M open 49.804) | DOWN | MATCH -- read-gap: last 49.791 < 49.804 at read time; M is knife-edge on the monthly open, verified numerically |
| DRAM next dn / up | 41.0232 (W N1 lo) / 71.9622 (D N4 up) | 41.03705 / 71.99174 | same rungs, 0.03-0.04% |
| TSLA position | LONG @314.891 since 08-03 04:00 | LONG | MATCH |
| TSLA gate | D dn, W up, M up | grey | MATCH exact |
| TSLA next dn / up | 265.948 (D N1 lo) / 326.515 (D N3 up) | 265.876 / 326.529 | same rungs, 0.004-0.03% |
| GOOGL position | LONG @365.571 since 08-03 13:35 | LONG | MATCH |
| GOOGL gate | D up, W up, M up | UP | MATCH exact |
| GOOGL next dn / up | 306.89 (W N3 lo) / 393.687 (W N1 up) | 306.869 / 393.717 | same rungs, 0.007-0.008% |
| alive census | DRAM 14/11/2/0, TSLA 13/11/3/2, GOOGL 11/8/7/4 | DRAM 0/8/1/0, TSLA 0/10/1/0, GOOGL 0/6/3/0 | NOT comparable -- fresh-mount loaded depth (delta class 1, amplified): deep pools, esp. 12h formations with May-era preserved-alive sides, cannot rebuild from the initial window |

No divergence escalates outside the declared delta classes: positions and
gate composites match exactly (the one gate difference resolves numerically
to 13 cents of price movement through the monthly open across the 15-minute
read gap), and every operative rung corresponds at 0.004-0.04% (anchor
resolution + line slope over the read gap).

OPERATIONAL FINDING (new, live-relevant): remounting the indicator -- or any
chart reload that shrinks the loaded window -- silently thins the harvest
ladder. v6.1's retired-first eviction deliberately preserves old alive
lines (DRAM's May-era 12h uppers at 74.78/87.27), but a fresh mount can
never rebuild them: the fresh DRAM mount's nearest lower exit sits at 41.04
where the full-history twin holds a 12h rung at 47.39. For the standing
short that is the difference between harvesting at -5% adverse and riding
to -18%. Loaded chart history is load-bearing state for this design; any
live deployment needs either persistent chart sessions or server-side line
state.

## Out of scope this week

Tier-2 STRAT targets (present in `/api/state` per-TF blocks incl. 1w/1M;
seed for later), TV alert webhooks, cross-pool dedup, roster refresh
cadence, any v6 Pine change.
