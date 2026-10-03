# Parallax PAPER September 2026 receipt -- the paper month, the lost book, and the kill call

Written 2026-10-02 (TVB-36) from the owner's hosted paper platform exports. Characterization of
one month of forward paper on the round-3 package, plus a bracket-only replay of every entry the
strategy qualified but the platform never filled. Scripts in this directory regenerate every
number from the local `exports/` directory (gitignored; populated from the owner's Parallax
export route, host `<PARALLAX_URL>`, never committed) and from Hyperliquid's public candle API.

Standing rules applied: receipt before story; a-priori labels only; nothing here is tuned on the
sample; the charter Section 0 instruction to backtest to KILL the strategy.

## 1. What the platform executed

Three HIP-3 accounts existed on 2026-10-02 22:46Z.

| Account | Created | Config | Entry orders | Filled | Closed trades | Wins | Net R | Net $ |
|---|---|---|---|---|---|---|---|---|
| STRAT (v1 adapter) | 09-14, stopped 09-23 | $1 risk, 10x cap, $200 notional cap | 7 | 6 | 6 | 1 | -3.1 | -3.05 |
| HIP-3 v2 forward pilot | 09-17, running | $1 risk, 10x cap, $200 notional cap | 132 | 17 | 16 (+1 open) | 4 | -3.7 | -3.58 |
| Perp Prop Test | 09-30, running | $100 risk, 20x cap, **$250 notional cap** | 56 | 3 | 2 (+1 open) | 1 | +0.2 | -2.82 |

R = multiples of the planned stop distance at entry. Fees and funding are in the dollar column
only.

Two platform failures explain the fill rates, both outside the strategy:

- **Funding-boundary block (pilot).** The worker missed the 2026-09-28 22:00Z funding boundary
  with XMR, kBONK, RENDER and PYTH open; `quality_flags` carries "missing boundary oracle" for all
  four, and from 09-29 every entry order was rejected with "Funding/data coverage unresolved;
  opening exposure suspended" (71 orders). PYTH is still open and was flagged again 2026-10-01
  19:00Z. This is finding 2 of the 2026-09-09 adversarial review of that repo, observed live.
- **Permission-window latency (both v2 accounts).** Entry orders are created a median 13.3 s
  (Prop) / 13.8 s (pilot, post-v10) after the scanner observation against a 15 s permission
  window; the fills that happened were created at 7.7 s (pre-v10) and 9.7 s (Prop). Rejections:
  "Execution admission/data unavailable" (created median 15.5-16.7 s after observation) and "At
  execution: source transition expired or continuity changed" (12.1 s). Admission itself takes
  5-8 s (context fetch, then book subscription). Latency is worse after the v10 deploy, not
  better: pre-v10 rejected median 10.5 s, post-v10 13.8 s.

Prop Test config note: with a $250 notional cap and a 3.94% stop, the GRASS entry carried about
$10 of risk, not the configured $100; the cap under-risks every ticket by roughly 10x. Settings are
immutable per experiment; a new experiment is needed to test what the name says.

## 2. The 24 closed trades (MFE/MAE from public 1m-15m candles between entry and exit)

- Exits: 11 stops (all full -1R), 6 targets (all wins), 7 continuity flips (all losers, mean
  -0.43R; they exited trades that had been 0.7R in favor on average).
- Losers' median MFE 0.60R; 10 of 18 losers reached 0.5R in favor first; ZEC reached 1.30R of a
  1.64R target and stopped; TAO reached 1.24R of a 1.39R target and was flipped at -0.32R.
  Winners' median MAE 0.75R. Path noise is the size of the stop in both directions.
- 3-2 reversals: 13 of 24 trades, 1 win (weekend 1 in August: 12 trades, 2 wins). Two sightings,
  both direction-confounded and tiny.
- Three flips (BTC, ETH, TAO) fired inside two minutes of each other at 00:30Z on 09-28, half an
  hour after the roll; SOL flipped ten minutes after an hourly open. The TVB-32 coupling
  mechanism: 09-28 was a MONDAY, so at 00:00Z the weekly, daily, 4h, 1h and 15m candles all opened
  together and the whole five-timeframe stack re-read from one fresh open (skill 4.5: coupled
  timeframes are one observation).
- Bar-close exits: none in the v2 adapter. The flip evaluates the forming candles of the
  configured stack (15m, 1h, 4h, 1d and 1w in the v2 package; the scanner's four in v1) for
  close-against-open on every 5 s poll, and fires only when ALL are against the trade; the Type 3
  invalidation is live too. (Corrected 2026-10-03: this line first said "four".)

## 3. The lost book: 116 qualified signals the platform never filled

Method (`lostbook.py`): every rejected or cancelled entry order, deduplicated by signal key across
accounts (116 distinct), entered at the order's reference price at order creation, walked forward
on public Hyperliquid candles (1m where history exists, else 5m, else 15m) until the first touch
of its own stop or target. Bracket-only: the flip exit cannot be replayed (no per-coin stack
history in the journal). A candle touching both levels counts as a stop. Open signals are marked
to the last close.

Calibration first: the same simulator on the 26 filled entries reproduced all 17 actual stop and
target outcomes (17/17 agree). The 7 flip-exited trades all read stop (6) or open (1) under
bracket-only: bracket-only sum -6.07R vs actual -3.04R, so bracket-only is PESSIMISTIC for the
flip class by about 0.4R per flipped trade.

| Lost book | n | target | stop | open | sum R (gross) | net of ~0.0864% RT fee | resolved win rate | median R:R |
|---|---|---|---|---|---|---|---|---|
| All 116 | 116 | 25 | 77 | 14 | -41.1 | -47.3 | 25% | 1.48 |
| 1h | 70 | 18 | 45 | 7 | -19.1 | | | |
| 4h | 43 | 6 | 30 | 7 | -21.1 | | | |
| 1d | 3 | 1 | 2 | 0 | -0.8 | | | |
| longs | 55 | 15 | 37 | 3 | -15.9 | | | |
| shorts | 61 | 10 | 40 | 11 | -25.2 | | | |
| reversals | 90 | 20 | 59 | 11 | -30.8 | | | |
| continuations | 25 | 5 | 17 | 3 | -9.2 | | | |
| before v10 (09-26) | 60 | 14 | 45 | 1 | -25.5 | | | |
| after v10 | 56 | 11 | 32 | 13 | -15.5 | | | |

By pattern (resolved): 3-2D 5 of 26 won, 3-2U 8 of 24, 1-2-2 2 of 11, 2U-1-2U 3 of 10, 2D-1-2D 2
of 10, 1-3 3 of 6, 2D-2U 1 of 5.

**Strategy-chosen book for the month, filled actual plus lost simulated: 140 trades, -47.7R
gross, -0.34R per trade.**

## 4. Worse than a coin flip (`census.py`)

A driftless random walk inside a bracket reaches the target first with probability
stop / (stop + target) = 1 / (1 + R:R). Summing that per trade gives the wins a strategy with NO
directional information would have produced with these exact brackets.

| Set | resolved n | wins | random-walk expectation | z |
|---|---|---|---|---|
| Lost book | 102 | 25 (25%) | 40.4 (40%) | -3.12 |
| Filled, bracket-resolved | 17 | 6 (35%) | 7.3 | -0.65 |
| Pooled | 119 | 31 (26%) | 47.7 (40%) | -3.14 |

Within the lost book: shorts 10 of 50 vs 20.2 expected (z -3.0); 4h 6 of 36 vs 14.4 (z -2.9);
reversals 20 of 79 vs 31.1 (z -2.6); 3-2D 5 of 26 vs 10.6 (z -2.3). Only the 1-3 (3 of 6 vs 2.6)
sat at or above random, n=6.

Not a chase artifact: at decision time the mid sat a median 0.01R beyond the trigger (p75 0.03R);
94 of 101 resolved lost trades were entered within 0.10R of the trigger and still won 26% against
39% expected. The entries are at the break. The break then fails more often than chance.

## 5. The session clock (`census.py` section C)

Both v2 journals, 13 days, distinct signals: 14,490 equity-perp (xyz) signals across 110 coins;
11,846 (82%) were refused because the US underlying was closed; 46 qualified. The NYSE clock is
applied to every xyz name. Refusals by UTC hour peak at 00Z (1,063), 12Z (894) and 20-22Z
(697/732/806). Named clusters, closed-underlying refusals and their peak hours:

| Cluster | Coin | signals | refused closed | peak hours (UTC) |
|---|---|---|---|---|
| Korea | EWY | 133 | 109 | 00, 22, 12, 23 |
| Korea | DRAM | 119 | 95 | 00, 12, 21, 22 |
| Korea | SMSN | 115 | 90 | 00, 20, 12, 05 |
| Korea | SKHX | 114 | 95 | 00, 23, 20, 08 |
| Asia/EU | EWT | 177 | 147 | 00, 12, 20, 10 |
| Asia/EU | EWJ | 161 | 135 | 00, 22, 20, 10 |
| Asia/EU | ASML | 156 | 137 | 00, 22, 21, 20 |
| Asia/EU | TSM | 130 | 108 | 00, 12, 05, 01 |
| Oil | CL | 121 | 104 | 00, 21, 06, 22 |
| Oil | BRENTOIL | 128 | 109 | 00, 12, 21, 02 |
| Metals | GOLD | 124 | 111 | 22, 12, 00, 20 |
| Metals | SILVER | 131 | 107 | 12, 20, 22, 21 |

00Z is the KRX opening cross (09:00 KST). The journal records the FIRST refusal only, so a signal
refused by the clock may also have failed a later gate; this census bounds the clock's reach, not
the qualified pool behind it.

## 6. Lead's assessment, 2026-10-02

The round-3 package as an autonomous mechanical book -- scanner-published pattern breaks on
1h/4h/1d, five-timeframe continuity gate (15m to 1w), structural stop, T1 target, flip exit -- is dead in the
water. Reasoning:

1. Four live ledgers, every one negative or flat: weekend 1 -$6.85 on 34; round 2 -$0.82 net on
   28; round 3 -$3.92 on 18; the paper month -6.6R on 24.
2. The month's full strategy-chosen book, 140 trades, is below a coin flip at z = -3.1 on the
   brackets it chose itself. That is negative edge, not absence of edge.
3. It is not latency (chase 0.01R), not the platform (17/17 calibration), and the one unreplayed
   mechanic (the flip) would narrow the gap by roughly 0.4R per flipped trade, against a 41R
   shortfall.
4. The mechanism is regime: breaks failed in September's whipsaw tape; in August's drift the book
   lost on shorts against the drift. The best it has done across regimes is flat.

What is NOT shown dead: the pattern signals carry information (below random means the sign is
informative); the continuity exit is the only mechanic that has paid in every ledger; the
discretionary layer the owner describes (yields, dollar, oil velocity, session awareness) was never
in the loop. Below random in one regime does not license fading the signals; it licenses a regime
input, pre-registered.

Watermarks: one month, one regime; lost entries at reference price (no slippage, slightly
optimistic); bracket-only (pessimistic on flips); 14 open signals marked to close; fees excluded
from R.

## Files

- `trades.py` -- round-trip reconstruction and order-rejection census from exports.
- `mfe.py` -- MFE/MAE per closed trade from public candles (`results/mfe_mae.json`).
- `lostbook.py` -- the lost-book replay and calibration (`results/lostbook.json`).
- `census.py` -- random-walk baseline, chase diagnostic, session census (`results/census.json`).
- `results/trades_*.json` -- per-account reconstructed trades.
- `exports/` -- local only: the raw account exports (~450 MB) and candle caches.
