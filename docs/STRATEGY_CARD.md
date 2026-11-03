# Strategy reference card (one screen)

> Every strategy family this workspace has run, one line each, in trader terms: the plain name
> (rename at will; the artifact code stays in brackets so the receipts still match), what it
> does, where it lives, whether it opens on TradingView today, the latest number read both ways.
> Numbers are GROSS; the control family's are FEASIBLE-FILL (the level fill was an upper bound).
> The long form is `docs/ARM_LEDGER.md`; this card is the index. Kept current every round.
> Owner's decision 2026-11-02: TradingView is the viewing surface for strategies (the quick
> intermediary); the viewer stays the research page for rows.

| # | Plain name [code] | What it does, one line | Lives in | On TradingView | Latest number, both ways |
|---|---|---|---|---|---|
| 1 | **The hourly control** [A0b] | Buy the break of the prior completed hour's high (short the mirror) when price is on the same side of the day's, week's and month's opens; out on a BF touch, a close through a structure line, or the continuity flipping | `pine/tfc_bf_control_strategy.pine` (TVB-20, parity PASS at bar close); Python `analysis/paper/` | YES, strategy | Fresh window +20.0 pp feasible (was +76.5 at the level fill; 58 of 106 entries were at a price never traded); July +104.8 level. Sits in losers for days. |
| 2 | **The control with a hard stop** [A0bS] | Row 1 plus a stop 3x the hourly ATR from entry, frozen at fill | Python only | no | Fresh +44.8 feasible (+111.1 level); under feasible fills the stop DEEPENS drawdown (36.5 to 59.5) instead of halving it. |
| 3 | **The state-stop exits** [S0a / S0b / S0c] | Row 1's entries; out at the close of the first hour that breaks the prior hour's opposite extreme (S0a); plus the flip backstop (S0b); plus BF touches (S0c) | Python only | no | Fresh +69.5 / +69.6 / +67.3 feasible (95.9 / 97.2 / 131.6 level). S0c's lead is gone under feasible fills; the whole-arm wins are reload speed, per shared trade they exit worse than row 1. |
| 4 | **The first-target package** [D1, D1ATR, D1i3, D1S] | The ten pre-committed STRAT setups' trigger break, only with room to the first target (the floor) and the filters; all out at T1 | `pine/tfc_mt_package_strategy.pine` (TVB-22, 9-cell mirror gate PASS); Python `analysis/paper/tier_b_exits*` | YES, strategy (the A1 / A2 / A3 arms) | D1 July +83.8 / fresh +28.4 (fills unchanged under the feasible rule); D1ATR +68.7 / +21.6 with the smallest drawdowns (10.6 / 5.6); the invalidation exit costs a tenth; the structural stop costs a third. The Codex assessment's preferred family; 37 fresh trades. |
| 5 | **Deeper targets and runners** [D2-D5, P1, P2, X1, PX] | Row 4's entries held for rung 2 to 5; half out at T1 and run half (P1); the owner's runner profile 40/20/20/10 + a 10% runner (P2); harvest only after rung 3 (X1) | Python only | no | P1 beats D1 per shared trade (+0.71 vs +0.32) and loses whole-arm (its runners hold the bullet); P2 July +6.1 / fresh +3.4 and loses to D1 matched; X1 July -37.8, the worst cell. |
| 6 | **The TFC baseline** [Control A / B, TVB-1 / TVB-4] | The first strategy: breakout stop at the prior bar's high, a per-timeframe open gate, a close-based state stop; two a-priori gate sets (M/W/D/60 and 60/30/15) | `pine/baseline_continuity.pine` | YES, strategy | Control B PF 0.645 (2,263 trades, churn); Control A PF 1.13 at OKX fees, 0.92 at HIP-3 fees. Retired reference: turnover is the lever. |
| 7 | **The overfit winners** [Champion MU15, Generalizer, ShortChamp MU5, Slow60; TVB-EXP] | Four deliberately overfit configurations kept as the labeled in-sample ceiling (the owner's request), plus two experimental strategies | `pine/winner_*.pine` (indicators), `pine/tvb_exp_champion.pine`, `pine/tvb_exp_bf_exit.pine` (strategies) | YES | Ceiling readings only; never arms, never deployed. |
| 8 | **The watch surfaces** [TFC Companion, TFC-BF watch, BF Comprehension, Magnitude + Targets] | Live discretionary displays: the continuity dots, the BF lines, the structural targets and magnitude | `pine/tfc_companion.pine`, `tfc_bf_watch.pine`, `bf_comprehension.pine`, `strat_magnitude_targets_plus.pine` | YES, indicators | Not backtested; the companion is the primary live validation route. |
| 9 | **The management book** [run one, C / A / B / D / D5 / chance / C_h / C_u] | Every first break of a day's, week's or month's level on 292 perps, no stop; out on a daily close against the trade with the week against it (20-day cap); the books take T1, T2, one R, five bars; the chance book keeps the setup-bar stop; an hourly clock and an under-water clock | Python `analysis/domino/` (the viewer's run one) | NO | Targets get reached, the setup-bar stop is what loses: the stop swap +0.48 to +0.92 per trade; the books near flat gross; the hourly clock halves the losers. Receipt `analysis/domino/MANAGE_RECEIPT.md`. |
| 10 | **The ES bench** [V0 Globex day, V1 RTH day, F0 / F1 / F2 fills] | Row 9's book on the E-mini, fifteen years, two day definitions, with the entry filled at the trigger, at the open, or not at all when the session gaps past it | Python `analysis/bench/` (viewer runs two and three) | NO | At the trigger Globex -0.05 / RTH +0.08 per trade; from the open -0.07 / -0.08 (the RTH sign was the fill); a gap that never fills back +0.42, a gap that fills -0.36 (RTH); the stop swap replicates daily and reverses monthly. Receipt `analysis/bench/BENCH_RECEIPT.md`. |
| 11 | **The live executor rule set** [Ruleset v1 / v2, round 3] | Scanner-fed STRAT entries on Hyperliquid, half a dollar of risk a ticket, venue stop and take-profit, refusals for BTC's day, reach and the bell | `hip3-executor` (another repo) | no | DOWN by design since 2026-09-07 (KILL_FLAT). September: 116 signals -41R, 25% wins against 40% random. Dead in the water. |
| 12 | **Studies, not strategies** | The domino census and chance comparison (TVB-37); the STRAT ML vessel; the regime labels (TVB-36); the matched-pair study (TVB-44) | Python `analysis/domino/`, `analysis/strat_ml/`, `analysis/regime/`, `analysis/pairs/` | no | No daily pattern family pays after costs across 898 coins; regime labels do not separate (stand-aside contains losses only); late entry is open air; candle sizes before the move matter on crypto, not on ES. |

## The TradingView route (owner's decision 2026-11-02)

Rows 1, 4, 6, 7 and 8 open on TradingView today. Rows 9 and 10 are the book everything since
TVB-37 is measured on and have no Pine mirror. The port order proposed for the owner's word,
one script at a time, each a parity-gated mirror of its Python twin (CLAUDE.md: a TV strategy is
valid only for the arms its gate has passed; the STRAT skill's STOP-and-ASK zones apply to the
bar logic):

1. **The management book's headline** (row 9, exit only C): enter the break of yesterday's high
   or low, no stop, out on a daily close against with the week against it, 20-day cap. On BTC
   and on ES (the Globex day). The reading the owner can see on a chart.
2. **Its hourly clock** (C_h): the same entry, out at the first hour closing against its open
   with the day against it.
3. **The chance book** (one R or the setup-bar stop, marked at bar five): the reference the stop
   swap is measured against.

Not on the route: the executor rule set (row 11, another machine) and the studies (row 12).
