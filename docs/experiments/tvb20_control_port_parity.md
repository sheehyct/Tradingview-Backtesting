# TVB-20: v6.1 CONTROL strategy() Port + Parity Gate -- PASS

2026-08-08. The deployed v6.1 watch indicator (`pine/tfc_bf_watch.pine`) was
forked into a TradingView `strategy()` backtest vehicle with zero HISTORICAL
source-logic change (claim qualified same day per external audit F4:
decision-event parity under the close-only convention, NOT realtime cadence
-- see the consequences list below), mounted on the TVB18-parity scratch
layout, and parity-gated against the Python twin over TV-harvested 5m bars. **The gate PASSED on all three
parity symbols: every event matched on (bar, direction, kind) over the full
~20,500-bar feed, and break/flip exit prices are float-exact.** This strategy
is C1 in the contrast ladder (continuity entries + BF exits; charter S3.1
amendments 2026-08-08): the operational control for the exit-design and
Magnitude+Targets ablations. The charter's minimal continuity-only baseline
(C0) is a distinct object. It is a research instrument, not a deployment
claim; the live surface remains the v6.1 indicator, untouched.

## The object

- Repo source of truth: `pine/tfc_bf_control_strategy.pine`. Diff vs v6.1 =
  exactly four hunks: a contract header, the `strategy()` declaration, an
  order-emission block that mirrors the internal position machine, and the
  on-chart table title string. The detection / pool lifecycle / gates /
  position machine are verbatim; decisions never read `strategy.position_size`.
- TV script: "TFC-BF CONTROL [TVB-20]", id `USER;5226f6f46f034f4fbc8ca37af9cdf47a`,
  created via the Make-a-copy UI flow (tab-binding trap). Verified: new id
  appeared; all 31 pre-existing scripts kept byte-identical modified stamps.
- Left MOUNTED with the Strategy Tester open on the TVB18-parity layout
  (last symbol DRAM 5m; the layout autosaves, it is a scratch surface).

## Pinned conventions (user-approved 2026-08-08)

| Convention | Value |
|---|---|
| Fill model | DECISION-EXACT: market orders on the signal bar, filled at that bar's close (`process_orders_on_close=true`) |
| Commission / slippage | 0 / 0 (all profit fields are simultaneously gross AND net here; `strategy.closedtrades.profit()` gross-of-commission caveat is moot at commission 0 but stated for the record) |
| Margin | `margin_long=0, margin_short=0` (TVB-3 margin-call-deadlock lesson) |
| Sizing | 100% of equity, `pyramiding=0`, initial capital 100,000 |
| Bar magnifier | OFF (no intrabar fills are used, so the intrabar-approximation gotcha never binds) |
| Calc flags | `calc_on_every_tick=false`, `calc_on_order_fills=false` |
| Order comments | exits "BF <tf> N<n>" / "Break <tf>" / "Flip"; entry ids L/S |

Consequences of decision-exact, for every later reader:
- The TRADE LIST (bar, direction, kind) is the parity object and matched 100%.
- Break and flip exits fill at the confirming bar's close on BOTH sides:
  float-exact price parity (measured max |delta| = 0 on all three symbols).
- Entries and BF-harvest exits fill at the signal bar's close in TV but at
  the trigger/line level in the twin: a DECLARED residual, reported below,
  NOT hidden. TV-reported P&L therefore differs from twin P&L by these
  residuals. A/B comparisons of exit-design variants against this control
  happen WITHIN TV under one convention, so the residual cancels by design;
  cross-engine P&L claims must use twin prices.
- TV trade times are the SIGNAL bar's open timestamp (offset search chose 0s
  against the twin's bar-open convention on every symbol).
- REALTIME cadence is OUT OF SCOPE (audit F4, 2026-08-08): with
  calc_on_every_tick=false the strategy evaluates the realtime bar once at
  its closing tick, where the v6.1 indicator executes on realtime updates
  intrabar (TradingView declaration-statement semantics). On historical bars
  both sides evaluate completed bars, so historical decision parity is
  unaffected; realtime alert timing is intentionally not parity-tested, and
  the calc flag stays false -- changing it would be a different research
  contract plus a live/historical repaint surface, not a repair.

## Parity method

Twin (`analysis/paper/engine.py`, deployed-default cell: arm 15m, n_max 6,
min_sep 1.0, pool_cap 12) replayed over the committed TV-bar dumps
(`analysis/reference/tv_deep/tvb19_tv_xyz_{coin}_5m.json`, forming tail
dropped), sliced to the strategy chart's actual first loaded bar. All three
charts floored at 2026-05-25 00:00 UTC -- identical to the dump starts, so
the slice is the full dump. Strategy trade lists harvested at the data floor
by `scripts/tvb20_port_harvest.mjs` (deep-load via requestMoreData +
3-stable-rounds floor detection, then `reportData().trades`). Join and price
layers: `analysis/paper/port_parity.py`; artifact:
`analysis/reference/port_parity/tvb20_parity_result.json`.

The join runs over the FULL feed overlap (2026-05-25 -> dump end 2026-08-05),
not just the formal window: a mismatch anywhere before the window would
corrupt position state inside it. TV trades harvested 2026-08-08 whose events
fall after the dump end are counted `beyond_feed`, and an open trade (empty
exit comment, tip-marked) contributes only its entry event.

## Results

| Symbol | Bars replayed | Events matched | Mismatches | In window 07-06..08-03 | beyond_feed | break/flip max abs dp | entry+bf residual median / mean / max abs |
|---|---|---|---|---|---|---|---|
| GOOGL | 20,323 | 89 | 0 | 58 | 2 | 0 | 0.571 / 1.253 / 7.339 |
| TSLA | 20,626 | 67 | 0 | 34 | 0 | 0 | 0.747 / 1.266 / 7.909 |
| DRAM | 20,519 | 87 | 0 | 18 | 6 | 0 | 0.160 / 0.241 / 1.162 |

Residuals are in price units (roughly 0.1-0.35% of price at the median); the
max values are fast bars where the close ran well past the trigger before the
5m bar ended -- the honest cost of close-fills, visible not modeled away.

## The one finding: Pine gate warm-up (the only engine change)

First run FAILED with a fully structured pattern: every mismatch sat between
05-25 and 06-01, TV's first trade was exactly 2026-06-01 00:00 UTC on all
three symbols, and the streams were in lockstep afterward. Mechanism: v6.1's
gate helper is `ta.valuewhen(timeframe.change(tf), open, 0)` and
`timeframe.change` cannot fire until the feed contains a period BOUNDARY --
on a chart whose history starts 05-25, the MONTHLY gate has no value until
June 1, so the Pine side is gate-not-ready and stays flat through May. The
twin's cold bootstrap adopted the first loaded bar as every period's open and
traded from day one. Same first bar, different gate warm-up convention -- the
warm-depth class one level deeper than the slice was designed to neutralize.

Fix: `TwinConfig.pine_gate_warmup` (default **False** -- the paper-grading
path, compare_config, and every committed sweep replay are bit-unchanged;
regression-tested in `tests/test_port_parity.py`). The parity replay sets it
True, reproducing Pine's boundary-armed gates. This is a replay-bootstrap
convention, not a change to any deployed logic; the v6.1 Pine was not touched.

Corollary worth remembering: **a freshly mounted v6.1 chart cannot signal
until the first monthly roll inside its loaded history.** With TV's ~20-21.6k
bar 5m cap that means a 5m chart mounted mid-month starts gate-ready only at
the next month boundary -- relevant to any future live-mount checklist.

## Verification trail

- `uv run python -m analysis.paper.port_parity` -> GATE: PASS (exit 0).
- `uv run pytest tests/ -q` -> 111 passed, 2 skipped.
- `pine_smart_compile` clean (one round-trip: shorttitle length fix).
- Frozen week-1 artifacts untouched; `pine/tfc_bf_watch.pine` untouched.
