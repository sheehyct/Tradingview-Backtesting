# TVB-1 External Audit -- Codex (verbatim source, read CRITICALLY)

> External review of `pine/baseline_continuity.pine` + the TFO indicator (`Timeframe_Continuity_Pinescript.pine`)
> by Codex, captured 2026-06-28 (TVB-1 post-session). Lightly ASCII-normalized from the original
> (em-dashes -> --, curly quotes -> straight); wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** The starred HTF-open claim cuts both ways and must be verified
> empirically (overlay the strategy FTFC coloring vs the TFO indicator). Claude's point-by-point
> critical synthesis -- including where Codex corrects Claude and where it conflates control-vs-variant
> -- is in `docs/HANDOFF.md` under "Codex external audit + Claude critical review". Read that alongside this.

---

Cuz -- my verdict:

**The original TFO indicator would be unsafe as a backtest source if you used its higher-timeframe `high/low` or inside/mother-bar state. The baseline strategy is mostly protected from classic lookahead bias, but I would still change how the HTF opens are computed and tighten the trigger mechanics.**

The bigger issue in `baseline_continuity.pine` is **not obvious future leak**. It is **model fidelity**: the strategy is really a "prior-close TFC gate + resting breakout stop" system, not a "check TFC at the exact intrabar break" system. That may be acceptable, but it should be named honestly.

## What the documents say the experiment actually tested

The experiment was intentionally a **minimal control**, not a deployable system: `{raw 2-trigger + TFO/FTFC gate + state-stop}`, with everything else tested later by ablation rather than mixed in by default. The README explicitly requires a `strategy()` backtest vehicle, one script containing the whole compound condition, raw level-cross triggers, once-per-bar behavior, `request.security` with `lookahead_off`, and Bar Magnifier/lower-TF data for intrabar fills.

The actual TVB-1 results are useful but not deployable: Control B `60/30/15` on 15m produced **2263 trades, PF 0.645 net**, while zero-fee PF was **1.284**, which says the raw signal had something but churn/fees killed it. Control A `M/W/D/60` on 60m reduced turnover to **258 trades** and cleared OKX fees with PF **1.131**, but failed at HIP-3-style 0.10% fees with PF **0.921**. The handoff's conclusion is right: the lever is **turnover / per-trade edge**, not leverage or a magic timeframe set.

The design discussion also correctly lands on "continuity-first, patterns-minimal": 2-sequences are mostly directional-break/continuity information the TFO already measures, while **1s and 3s** are the parts continuity cannot see well because they represent compression/expansion, not just directional agreement.

## Pine audit: `Timeframe_Continuity_Pinescript.pine`

The TFO indicator has the obvious red flag:

```pine
[o1, h1, l1] = request.security(..., [open, high, low], ..., barmerge.lookahead_on)
...
[o10, h10, l10] = request.security(..., [open, high, low], ..., barmerge.lookahead_on)
```

That is lines **70-79** in the TFO file.

TradingView's own Pine docs are blunt here: when requesting higher-timeframe data, `lookahead` determines whether the request can return values from times beyond the historical bar being evaluated, and `lookahead_on` without an offset can leak future data into historical bars. They specifically show HTF `high` with `lookahead_on` displaying final higher-timeframe highs before those highs were actually knowable. ([TradingView][1])

So:

**Using `open` with `lookahead_on` is not the same kind of sin as using `high`, `low`, or `close`.** The HTF period open is known as soon as that HTF period begins. Substantively, "current day open" or "current 60m open" is not future information after the first bar of that period.

**But this TFO does not only request `open`.** It requests `high` and `low` too. Those are future-leaking on historical lower-timeframe bars unless offset. Then the script uses those values in functions like `check_tfc()` and `draw_lines()` to determine inside/mother-bar behavior. That means the indicator's table / mother-bar / inside-high-low logic can absolutely know the final HTF high/low before a live trader would have known it.

The FTFC candle color specifically is less bad than the raw `lookahead_on` line suggests, because the core FTFC state is built at lines **220-249** as:

```pine
tfc1 = close > o1
...
if tfc_arr.get(i)
    ftfc_dn := false
else
    ftfc_up := false
```

So the main red/green/grey FTFC color depends on **chart close vs HTF open**, not HTF high/low. That part is not obviously future-leaking if the only requested value used is the HTF open. But the file as a whole is not a clean backtest source because it bundles safe-ish `open` data with unsafe `high/low` data under `lookahead_on`.

One more subtle mismatch: the TFO treats `close == open` as **down**, because `close > open` is false and the `else` kills only `ftfc_up`. Your baseline strategy treats equality as neutral. That is probably rare on liquid perps, but if the goal is exact indicator replication, this is a real semantic difference.

## Pine audit: `baseline_continuity.pine`

The baseline strategy does the right big things:

At lines **30-39**, it uses `strategy()`, not `indicator()`, with `process_orders_on_close=false`, `calc_on_every_tick=false`, commission and slippage configured.

At lines **72-73**, it requests only HTF `open` and uses `barmerge.lookahead_off`:

```pine
f_open(simple string tf) =>
    request.security(syminfo.tickerid, tf, open, barmerge.gaps_off, barmerge.lookahead_off)
```

At lines **85-105**, it builds `ftfc_up` / `ftfc_dn` only from chart `close > requested period open`.

At lines **113-116**, it exits via state-stop when the gate de-aligns.

At lines **124-132**, it arms stop entries while flat:

```pine
if allow_long and ftfc_up
    strategy.entry("Long", strategy.long, qty = qty, stop = high)
...
if allow_short and ftfc_dn
    strategy.entry("Short", strategy.short, qty = qty, stop = low)
```

Because Pine strategies normally create orders after the bar calculation and the earliest fill is the next available tick, a stop set to the just-closed bar's high is functioning as "next bar breaks prior bar high." TradingView documents that default strategy orders fill no earlier than the next tick, and because strategies recalculate after bar close by default, market orders usually fill at the next bar open; stop orders can then fill on the next bar when price reaches the stop. ([TradingView][2])

So I **do not see classic lookahead bias** in the baseline from `request.security` the way I do in the original TFO indicator's `high/low` requests.

But I would still change several things.

## The biggest concern: HTF open retrieval ambiguity

The baseline comment says `lookahead_off` returns the current period's open safely. I would not rely on that as written.

TradingView's docs say default `request.security` behavior on historical bars returns confirmed values from the requested context, while realtime bars can contain unconfirmed values; they recommend offsetting HTF expressions and using `lookahead_on` when you want consistent non-repainting confirmed HTF values. ([TradingView][3])

For an HTF **open**, the value is economically known at the start of the HTF bar, so there is a good argument that using the current HTF open is not "future leak." But Pine's historical/realtime merge behavior can still be unintuitive. I would avoid the argument entirely.

For this specific same-symbol, 24/7 perp use case, I would compute period opens locally from the chart bars and remove `request.security` from the FTFC open gate altogether:

```pine
f_period_open(string tf) =>
    if timeframe.in_seconds(tf) < timeframe.in_seconds(timeframe.period)
        runtime.error("Selected TFC timeframe is lower than chart timeframe.")
    ta.valuewhen(timeframe.change(tf), open, 0)
```

Then:

```pine
o1 = f_period_open(tf1)
o2 = f_period_open(tf2)
...
```

That gives you the current M/W/D/60/30/15 period open at the first chart bar of the new period without asking Pine to merge HTF data. It also makes the logic easier to audit: the period open is literally the first chart-bar open inside that period.

For 24/7 perps with UTC session boundaries, this is cleaner than `request.security`. For RTH equities or session-mismatched symbols, you would need to be more careful.

## The trigger is close, but I would offset by one tick

The baseline currently uses:

```pine
strategy.entry("Long", strategy.long, stop = high)
strategy.entry("Short", strategy.short, stop = low)
```

Because the order is created after the bar closes, `high` is the prior bar's high for the next bar's stop. Mechanically, that is okay.

But STRAT logic is strict:

```pine
high > high[1]
low < low[1]
```

A stop order at the exact prior high can fill on a touch, not necessarily a true break. I would use:

```pine
longStop  = high + syminfo.mintick
shortStop = low  - syminfo.mintick
```

Then:

```pine
strategy.entry("Long", strategy.long, qty = qty, stop = longStop)
strategy.entry("Short", strategy.short, qty = qty, stop = shortStop)
```

That forces a real 2U/2D break instead of an equal-high/equal-low touch.

## The backtest is not exactly "TFC at the moment of break"

This is important.

With `calc_on_every_tick=false`, the strategy evaluates the TFC gate at bar close, places a resting breakout stop, and that stop can fill intrabar on the next bar. That is a valid model if the intended live behavior is:

> "At the close of a bar, if TFC is aligned, place a stop order above/below the just-closed bar and let it work during the next bar."

That is **not** the same as:

> "When price breaks the prior high intrabar, check whether TFC is still aligned at that exact moment, then enter."

The latter is harder to backtest on the same chart timeframe because the strategy logic is not recalculating inside the bar. Bar Magnifier improves fill sequencing, but it does not magically turn your strategy logic into a lower-timeframe decision engine. TradingView's Bar Magnifier uses lower-timeframe data for more realistic historical order fills instead of relying only on chart-bar OHLC assumptions. ([TradingView][4])

So I would rename the current baseline mentally:

**Current baseline = prior-close TFC-gated resting breakout.**

That is not a lookahead bug. It is a model definition. But it matters.

If you want "TFC at the break," I would run the strategy on a lower chart timeframe, such as 1m/2m/5m, and explicitly compute the 15m/30m/60m prior highs/lows and period opens from that lower timeframe. That is more work, but it's the honest way to backtest intrabar decision logic.

## What I would do differently

First, I would keep the experiment's philosophy exactly: start with the dumb-simple control and kill it if it deserves to die. The docs are right that the baseline should be tested first, then compression / reversal-vs-continuation / vol-conditional timeframe sets should be ablated against it rather than thrown in by default.

Second, I would revise the baseline engine like this:

```pine
//@version=5
strategy("Baseline TFC [No-security-open version]", overlay = true,
     pyramiding = 0,
     process_orders_on_close = false,
     calc_on_every_tick = false,
     commission_type = strategy.commission.percent,
     commission_value = 0.10,
     slippage = 1,
     use_bar_magnifier = true)

f_period_open(string tf) =>
    if timeframe.in_seconds(tf) < timeframe.in_seconds(timeframe.period)
        runtime.error("Enabled TFC timeframe is lower than chart timeframe.")
    ta.valuewhen(timeframe.change(tf), open, 0)

f_apply_gate(bool useTf, float op, bool up, bool dn) =>
    bool outUp = up
    bool outDn = dn
    if useTf
        if close > op
            outDn := false
        else if close < op
            outUp := false
        else
            outUp := false
            outDn := false
    [outUp, outDn]
```

Then I would build the enabled-timeframe gate from locally reconstructed opens, not `request.security`.

Third, I would enforce the chart/timeframe relationship in code. The README says chart TF must equal the lowest enabled TF, but the code does not enforce it. Pine docs specifically warn that if a script is designed for HTF requests, it should prevent users from selecting timeframes lower than the chart timeframe, because lower-timeframe `request.security` behavior is a different animal. ([TradingView][1])

Fourth, I would add a catastrophic fail-safe stop in addition to the state-stop. The state-stop is conceptually elegant because it exits when the same thing that got you in breaks, but it is close-based and can give back a lot inside a fast perp bar. The discussion already captures that tradeoff: state stops are wider/laggier and fit swing-style logic better than tight scalps.

Something like this for long:

```pine
failStopLong = strategy.position_avg_price * (1 - maxLossPct / 100)
strategy.exit("Long catastrophic", "Long", stop = failStopLong)
```

Not as the "STRAT invalidation," but as a market-structure-independent disaster guard.

Fifth, I would add a re-entry governor before taking "TFC reintroduced" over and over. The handoff explicitly flags this: entering every reintroduction needs cooldown or a required new extreme, otherwise chop can hand you repeated churn entries.

## Final answer on lookahead bias

**Original TFO indicator:** yes, if used as a backtest/strategy source beyond simple `close > HTF open`, it can introduce lookahead bias. The `high/low` requests with `lookahead_on` are the dangerous part.

**Baseline strategy:** I do **not** think it has classic future-looking `request.security` lookahead bias. It intentionally uses `lookahead_off` and only requests HTF opens. But I would not leave it as-is because the HTF-open retrieval is ambiguous enough that I'd remove `request.security` completely and reconstruct period opens locally.

**Bigger than lookahead:** the current strategy is a **prior-close gated resting-stop model**. That is a legitimate model, but it is not the same as checking TFC alignment at the exact intrabar break. If that distinction matters, run the strategy on a lower execution timeframe and build the 15/30/60 or M/W/D/60 state from there.

My next build would be: **No-security-open baseline + strict tick break + catastrophic fail-safe + optional re-entry governor**, then rerun Control A/B fee characterization before adding any compression or regime layer.

[1]: https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/ "Concepts / Other timeframes and data"
[2]: https://www.tradingview.com/pine-script-docs/concepts/strategies/ "Concepts / Strategies"
[3]: https://www.tradingview.com/pine-script-docs/concepts/repainting/ "Concepts / Repainting"
[4]: https://www.tradingview.com/support/solutions/43000669285-what-is-bar-magnifier-backtesting-mode/ "What is bar magnifier backtesting mode -- TradingView"
