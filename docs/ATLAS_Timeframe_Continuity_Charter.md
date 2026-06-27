# ATLAS — Timeframe-Continuity Exploration Charter

> **This is a charter, not a spec.** Read the next section before doing anything else. It governs how you (Claude Code) are expected to behave on this work, and it overrides the default instinct to treat a planning document as a fixed contract.

---

## 0. How to read this document (read this first)

This document hands off a long design conversation. It encodes **reasoning and guardrails**, not a frozen list of requirements. The distinction is load-bearing, because the failure mode this project is most exposed to is *the tool behaving wrongly around data*, in two opposite directions that have both happened before:

1. **Overfit-gravitation** — running combinations, finding the best-looking one, and defending it as "the answer." Picking the top Sharpe and shipping it.
2. **Exploration-freezing** — concluding "the data says X is optimal; trying anything else is overfitting," and refusing to run the analysis at all.

Both are the same underlying error: **treating every interaction with data as a selection decision.** It is not. There is a difference between *generating* data and *selecting on* it, and this whole project lives in the first activity.

What this means for how you work here:

- **Deviation-with-justification is the expected mode, not a violation.** If, mid-build, you notice something that contradicts or wasn't anticipated by this document, **surface it.** That instinct to push back when reality diverges from the plan is the *desired* behavior on this project — not something to suppress in the name of "following the spec." The author has had agents refuse to engage with a mid-development discovery because "that's not what the spec says." Do the opposite.
- **The goal of backtesting here is to break the strategy and find bugs, not to produce a favorable curve.** A backtest run to confirm is worthless — with enough free parameters it always confirms. A backtest run to *kill* the thing — to find the regime where it dies and the bar where the logic breaks — is the only version that carries information. Optimize for finding where it fails.
- **There is no best combination, and that is the premise, not a problem to solve.** Every day is a new micro-regime; every instrument differs; the inherited orthodoxy may not transfer (see §2). We explore *because* no universal optimum exists — to map the terrain and find the surprises, not to crown a winner.
- **Treat extreme metrics as questions, not verdicts.** A Sharpe of 3–4 is a flag that the period was kind, not a target hit. 95/100 winning trades is a prompt to dig (sizing? exit bug? a genuinely good but fragile edge?), not proof of edge. The number is where the investigation *starts*.

If you ever find yourself about to say "the data shows this is optimal, so we shouldn't try alternatives" — stop. That's the category error. Generate the alternatives anyway; the spread *is* the finding.

---

## 1. The epistemic stance

A few principles that the rest of the design serves. These are the author's stated operating beliefs and should be treated as binding context, not re-litigated:

- **Generating data ≠ selecting on it.** Running thirty timeframe combinations and reading the distribution is exploratory analysis — characterizing what's robust vs. fragile, finding what's surprising. Picking the top performer and deploying it is the overfit. Same data, different act. This project does a lot of the first and is deliberately cautious about the second.
- **All trading systems are rules fit to a regime** — there is no assumption-free position. Accepted. But this does *not* erase the gradient that matters: whether each parameter is set by a **structural reason** or by the **sample**. Two parameters justified by a structural claim generalize; the same form with parameters chosen because they backtested best does not. The signature of the bad kind is a **generalization gap** (great in-sample, dead out-of-sample), driven by free-parameter count and search intensity — not by whether rules exist at all. Navigate by that gradient.
- **No system profits across all regimes with zero tweaks.** This is why strategies are held loosely and why "always be thinking about strategies" (even unused ones) is the stance. Regime-specific by nature; survival comes from not over-fitting to what just worked and from standing aside when the playbook stops.
- **Over-specification can be an instrument, not only a sin.** Deliberately fitting tight to make the expectation *brittle on purpose* makes reality's deviations visible — which is how pattern-detection bugs were historically found in ATLAS. Pejorative overfitting fits noise to make a loser print. The legitimate use fits tightly to make deviations *legible*. Same mechanic, opposite goal. When the author asks to fit something tight to expose a bug, that is not the bad kind.

---

## 2. What we're trading, and why inherited assumptions may not transfer

The target instruments are **HIP-3 builder-deployed perpetuals on Hyperliquid** (e.g. trade.xyz equity perps, `{dex}:{coin}` naming), plus closely-related crypto/equity perps. Key structural facts:

- **24/7, no close, no overnight gap, no closing auction.** The "day" rolls at **00:00 UTC** (visible as the ~8pm ET volume spike during EDT, 7pm during EST), not at a market bell.
- HIP-3 equity perps are **oracle-priced off an underlying equity that *does* close.** During RTH the reference is the underlying equity/ETF; outside RTH (where most meaningful action happens lately) the cleanest proxy is the most-liquid equity perp on a crypto venue — empirically ~98% OKX (e.g. `MSTRUSDT` perpetual swap), **same instrument class**, also 24/7, also UTC-rolled.
- Level-break correlation between the OKX proxy perp and the Hyperliquid perp is **mechanically sound, not luck** — both are arbitraged/oracle-pulled toward the same underlying, so levels break together. This is tighter than tick-by-tick basis. Edge cases where they could diverge: a level sitting inside the typical basis band, or a venue-local liquidity event (squeeze/wick on the thinner book).

**The implication for this project:** fifty years of quant best-practice was built on RTH equity data — overnight gaps, a closing auction, a daily bell. Our instruments have none of that. Assuming the inherited orthodoxy transfers is *itself an unexamined prior.* This is a substantive reason to **regenerate the data and re-derive what works here**, rather than inheriting conclusions — and it is *not* a license to fish. The distinction in §0 still applies.

---

## 3. The system design

### 3.1 Core thesis: continuity-first, patterns-minimal

The central design decision, reasoned out at length:

**STRAT patterns built from "2" bars (2-2, the spine of 2-1-2, 3-1-2) are lower-resolution re-descriptions of timeframe continuity** — which a Timeframe Continuity (TFO/TFC) indicator measures **directly and continuously, at higher resolution.** A "2" is just a directional break; a sequence of 2s is a continuity transition the TFO already tracks. Therefore:

- **Menu-selecting among 2-based patterns is almost pure overfit.** "A 2-1-2 on the daily" privileges one scale's directional pattern; the directional content is scale-relative ("a 2-1-2 daily ≈ a 2U monthly" in spirit), so picking one is fitting the sample, not the market. **Do not build a pattern tournament.**
- **What the TFO cannot see** is the **range regime**: the **1** (compression — broke neither side) and the **3** (expansion — took both sides). Continuity is a *directional-agreement* measure; these are an orthogonal axis. **These are the only pattern-elements worth keeping**, and they are kept as **binary features with a prior** ("compression preceded this break"; "this was an expansion bar"), *not* as a named menu.
- Note on the "1": do **not** label it "coil vs. profit-taking" in real time — that's only knowable by resolution, so as a live feature it's post-hoc and worthless. What survives is the **compression** itself, measurable the instant the bar forms.

The one structural hypothesis worth ablation-testing (see §5): **compression-then-expansion** (a documented volatility-breakout effect generally) — i.e. does a break *preceded by a 1* outperform a bare break, in *our* instruments and timeframes? That's an empirical question, not an assumption to bake in.

### 3.2 The TFO is the gate; the timeframe set is the most important knob

The TFO indicator **collapses whatever timeframe set you feed it into a single up / down / neutral state.** Consequences:

- The signal logic is only **two conditions**: (1) the **trigger** (a level break) and (2) **the TFO is FTC-aligned** in the trade direction. This is *not* three separate per-timeframe FTC flags — the TFO already aggregates them. (The TradingView native multi-condition alert cap of 5 never binds here.)
- **The timeframe set you feed the TFO *is* your operational definition of continuity** — the single highest-leverage parameter in the system. More timeframes = stricter gate = fewer, cleaner signals. Fewer = looser. Demonstrated concretely: on a 2h chart with M/W/D/60, a bar paints neutral (grey) because the 60m flipped; **remove the 60** and the same bar goes bright-red because now "aligned" only requires M/W/D and the day is still down. Changing the set *is* changing what "aligned" means.
- This selection is **regime-dependent, not universal** — which is exactly why it gets **explored** (§5), and exactly why the explored result must **not** be hard-selected by backtest and called physics.

Indicator reading reference (verified against the live charts): grey-with-green-outline = inside bar that closed up within prior range; grey-with-red-outline = inside bar that closed down within range; **neutral/grey = the timeframes in the set are not all in agreement** (covers both a flip and a non-resolving bar); solid red/green = full FTC down/up.

### 3.3 Two-layer architecture

Two instances of the continuity measurement at different scales — the same concept at two resolutions, which is the elegant part:

- **Regime layer** (slow): e.g. `M/W/D`, or — since these are 24/7 perps — something more exploratory like `W/D/12h`. **Governs position size.** Regime grey (higher timeframes not in agreement) → **size down** (or stand aside — see open question §6). Regime red/green → execution layer is permitted to trade that direction.
- **Execution layer** (fast): e.g. `60/30/15`. **Generates the signal.** Enter when continuity aligns; exit when the lowest execution-TF bar closes neutral/opposite (see §3.5).

Graceful degradation (size scaling with regime agreement, rather than binary in/out) is intentionally good risk design.

### 3.4 The 2U timing — get this right (it was wrong in an earlier draft)

**A bar becomes a 2U the instant price trades through the prior bar's high — the same instant as the trigger and the entry — NOT only at bar close.** The running high only ratchets up and is never revocable, so the break is real intrabar. The bar's *final* label can still upgrade 2U→3 if the low also breaks later, but it never downgrades, and that upgrade risk is what the stop handles, not a reason to wait.

Implementation consequence:

- **Trigger off the raw level cross — `high > high[1]` (or `close`/`high` crossing the stored prior-bar high) — NOT the indicator's painted "bar shape" series.** Reason: some indicators only *plot* the 2U label at bar close to avoid intrabar flicker, even though the break itself is intrabar-real. Triggering off the raw level gives true intrabar timing regardless of how any indicator chose to paint.
- `high > high[1]` **does not repaint** — once true on the bar it stays true — so it's a clean fire. Set alert/strategy evaluation to **once-per-bar**, not once-per-bar-**close**, or the lag is reintroduced.

### 3.5 Stop-as-state

Rather than a fixed price stop off a rules sheet (which is an arbitrary line), the preferred invalidation is **stateful: exit when the lowest execution-TF bar on the TFO closes neutral (grey) or opposite (e.g. a 2D against a long).** This makes the **exit the same measurement as the entry** — you leave when the thing that got you in breaks. Internally consistent in a way a price stop is not.

Tradeoff to encode honestly: a state stop is **close-based**, therefore **wider and laggier** than an intrabar price stop — you give back level-to-close. This maps directly onto the discretionary "it depends on duration" reality:

- Tight scalp / 0DTE-equivalent on a low TF → a price stop (intrabar) is appropriate; an inside-close eats you, "you can be right and go to zero."
- Longer-dated thesis with room (the "daily closed inside but up, in a call" case) → a state stop is appropriate; there's room to let it resolve.

**Both can be implemented and selected by holding horizon** (price stop on execution-scalps, state stop on swings). This is the discretionary "it depends" rendered mechanical.

---

## 4. Implementation vehicle

**Use TradingView's `strategy()` script type, not `indicator()`.** Rationale:

- `strategy()` simulates entries/exits (`strategy.entry`, `strategy.exit`), produces a full backtest in the Strategy Tester (net P&L, win rate, drawdown, per-trade list), **and** fires webhook alerts on simulated fills with placeholders (`{{strategy.order.action}}`, etc.).
- It bakes the **entire compound logic — trigger + TFO gate + stop + target — into one script.** You put **one alert** on it ("order fills only"); the compound condition lives in code, not in the multi-condition alert UI. This is the "pre-compiled condition into one alert" the author was reaching for, *plus* the test harness in the same object.
- **Gotcha:** TradingView's native multi-condition alerts **reject scripts that use the `alert()` function.** If (and only if) you ever want to combine a script signal with UI conditions, expose it via `alertcondition()` instead. Cleanest path: bake everything into the strategy and fire one signal — don't split logic across code and UI.

Distinguish from **"Add indicator/strategy to [X]"** — that is *source-chaining* (feeding one script's plot as the *input* to another, e.g. an RSI computed on another indicator's output). It is **not** the mechanism here and should not be conflated with `strategy()`.

---

## 5. The exploration protocol (the actual work)

This is the procedure. Its purpose is **characterization and bug-finding**, per §0.

1. **Run many timeframe-set combinations** (both layers) **across multiple distinct regimes**, **against a control/baseline.** The baseline is the minimal system: `{2-trigger + TFO-gate + state-stop}` with a fixed, a-priori-chosen timeframe set.
2. **Expect — and want — numbers all over the place, good and bad.** The **spread is the signal.** A tight cluster of great results is suspicious; a wide distribution is informative. Always compare to the control.
3. **For combinations that did poorly: ask *why*.** Do not assume poor performance means a different timeframe set should be adopted — and do not assume the inherited choice is correct either. Investigate the mechanism of the failure.
4. **For surprising results — something that doesn't move what you'd expect, or raises an interesting point — flag it explicitly.** Unexpected findings are a primary deliverable of this exercise, not noise to smooth over.
5. **Then decide, then paper-trade the chosen parameters against the control.** If it underperforms live: **find out why before concluding "bad strategy."** Candidate causes, in order of "check first": a **position-sizing** problem; an **exit bug on an otherwise-good strategy**; *then* a genuinely bad edge. "Can't find out why" is itself a valid (if unsatisfying) terminal state — but only after digging.

**Ablation, not tournament.** The one structural question worth testing is whether **patterns add edge over the continuity-only baseline:**

- Baseline: every 2U-trigger that fires while FTC-aligned.
- Variant A: only triggers **preceded by a 1** (compression filter).
- Variant B: **reversal context** (e.g. 2D→2U) vs. **continuation** (2U→2U).
- Compare expectancy / win rate / drawdown to baseline.

If A/B don't beat baseline → the hypothesis is confirmed, patterns were redundant once continuity is measured directly, **drop them.** If they do → the structure carries real information, **keep that one filter.** Either way the question is answered with **data against a control**, not argument — and it's the "hold strategies loosely" principle applied to the strategy's own components. **Keep at most one thing from the pattern world (compression, possibly the 3); do not reintroduce the menu.**

---

## 6. The volatility-conditional question (parked, but specified)

Whether to make the timeframe sets **volatility-conditional** is an open avenue, deliberately not built yet. It is specified here with full nuance because it is the canonical place where a *real mechanism becomes cover for overfitting.*

- **The form clears the bar.** "Compress timeframes when volatility is high" is mechanism-first and predicts a direction *a priori*: range scales with `vol × √time`, so to hold range constant `time ∝ 1/vol²` — **doubling implied vol compresses the clock ~4×** (a 60-minute bar at VIX 30 carries roughly the range a 4-hour bar does at VIX 15). "A month in an hour" is the same law at a bigger multiple. This is categorically better epistemics than grid-searching frames.
- **The parameters do *not* clear the bar just because the mechanism is real.** The mechanism authorizes the *direction* of the adjustment and says **nothing** about the **threshold** (why 25 and not 22 or 28) or the **exact mapping** (which frames shift, by how much). Those stay free and sample-tunable — and now there's a respectable story to launder them through. **A real mechanism is the most effective cover overfitting has.** Bar to clear: **fix the threshold *and* the mapping a priori too**, or it's laundered overfit wearing physics.
- **The switch is a second strategy with its own error, correlated with what it chases.** A vol regime is only knowable once underway, so you classify "high vol" *after* the expansion has started — the adaptation **systematically arrives late** relative to the exact fast move it exists to handle. The switched system must beat a fixed set *including* this lag and the threshold false-positives — a far higher bar than "per-regime, the optimal frames win in-sample."
- **Match the vol measure to the instrument.** VIX is SPX implied vol — correct for ES, a **risk-off proxy that can decouple** for COIN/MSTR/HIP-3 perps, which have their own vol surface. "VIX > 25" as a literal switch on a crypto book is **borrowing equity vol for a different instrument** and must be checked, not assumed. (Prior VIX research exists; condition on the **native** measure where possible.)
- **On the May–June ES example** (≈28 days to build +3.05%; 2.76% gone in 8 hours; the whole month erased in 22.5 hours): it cleanly proves **compression happens**, not that it's **tradeable in advance.** The deciding question the chart does *not* answer: **was vol already elevated *before* the break** (so a conditional system would have switched in time), or did it **spike *with* the move** (so the switch lags exactly as above)? Descriptively undeniable; tradeably it lives or dies on **lead vs. coincidence.** Interrogate that specifically from the data before trusting the switch — it's precisely where a confirming read feels like proof.

**Disposition:** legitimate to build *if and only if* threshold + mapping are fixed a priori and the lead/lag is verified empirically. Until then, parked.

---

## 7. Backtest traps specific to this system (must respect)

A continuity-gated trend system is maximally exposed to these. Violating the first one makes the entire backtest fiction.

1. **`request.security` lookahead — the critical one.** Pulling higher-timeframe continuity with lookahead **on** lets the script "see" the HTF bar's outcome before it would be known live, massively inflating results. This is *the* classic STRAT-backtest trap and this system is the most exposed kind. **Use `lookahead_off` and confirm-on-close offsets.** Audit every `request.security` call for this.
2. **Intrabar fill approximation.** The Strategy Tester approximates intrabar fills from OHLC unless the **bar-magnifier / lower-timeframe data** is enabled. The intrabar level-break entry (§3.4) will read **optimistic** without it.
3. **Venue mismatch.** Backtesting on the **OKX proxy perp's** history while executing on **Hyperliquid** — basis and the RTH/after-hours structure differ. Don't treat the proxy backtest as identical to live HL behavior.
4. **Regime flattery.** A continuity-gated trend system **looks gorgeous in a trending sample and bleeds in chop.** Hold every headline number loosely; weight performance *by regime*, and per §0, hunt for the regime where it dies.

---

## 8. Open questions — explicitly NOT decided

Do not treat any of these as settled; flag your reasoning if you touch them:

- **Chop handling conflicts with the stated meta-principle.** When the regime layer is grey (HTF = scenario-1 = "chop"), the current design **sizes down but keeps trading** — yet the execution layer in chop thrashes grey→red→grey, churning small losses + spread/fees each cycle, and size-down caps *per-trade* damage, not *churn*. The author's stated philosophy is "standing aside when the playbook stops beats finding better entries." These conflict. **Open decision:** should grey regime **widen the gate / stand aside** rather than "trade smaller"? This is a load-bearing choice; decide it deliberately.
- **Re-entry governor.** "Enter every time continuity is re-introduced" needs a **cooldown or a required new extreme**, or one choppy-but-trending move yields ten entries. Unspecified.
- **Timeframe sets must be chosen a-priori and then *not* tuned on the sample.** The defense against relocating overfit (from "which pattern" to "which timeframes") is that the sets carry structural priors (M/W/D, 60/30/15 are not arbitrary) — but only *if fixed by reasoning and not optimized on the backtest.* The moment "W/D/12h or M/W/D?" is chosen by performance, it's fitting again with fewer knobs. Choose, accept the result, don't tune.
- **Price-stop vs. state-stop selection rule** (§3.5) by holding horizon — sketched, not formalized.

---

*This document captures a design discussion and is meant to be argued with. If implementation reveals something it didn't anticipate, that discovery is the point — raise it.*
