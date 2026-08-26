<!--
Copy to docs/reviews/tvb{N}-codex-audit.md and fill in.
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-27 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of the hip3-executor live micro-capital build, Weekend-1 ledger,
> TVB-28 analysis, and the tradingview-backtesting session record, captured 2026-08-25
> (TVB-27 post-session). Lightly ASCII-normalized (em-dashes -> --, curly quotes -> straight);
> wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-27 -- live executor and Weekend-1 / TVB-28 analysis
- **Reviewed:** PRIMARY `C:\Strat_Trading_Bot\hip3-executor`, root-inclusive `e93d748..2daf6a4` (17 commits); SECONDARY `C:\Strat_Trading_Bot\tradingview-backtesting`, `59cda10^..59cda10`
- **Reviewer:** Codex CLI (GPT-5)
- **Overall verdict:** NEEDS-CHANGES

## 2. Verbatim audit

The Weekend-1 books reconcile to the venue, the 34 recorded entries satisfy the
recorded rules, the ordinary entry/exit path completed, and the run ended with no
journaled position. Those are real mechanics accomplishments. They do not establish
that the live executor is safe on failure paths. Two high-severity lifecycle defects
can leave exposure while the executor has no durable position record or while it says
that `KILL_FLAT` succeeded. The TVB-28 calculations mostly reproduce as implemented,
but several conclusions turn modeled or partly unobserved P&L into causal strategy
claims. Those defects require correction before another unattended live run or any
promotion decision.

### Scope interpretation and validation

The literal primary range in the request, `e93d748^..2daf6a4`, cannot resolve because
`e93d748` is the repository's root commit. I reviewed the empty-tree diff plus the
complete ancestry from `e93d748` through `2daf6a4`, inclusive. The on-disk work order
has since been extended through `21bd2a9`; the user's more specific invocation pinned
this review at `2daf6a4`, so `21bd2a9` is explicitly out of scope. The secondary pin is
valid and contains exactly four documentation paths; no Pine file or
`request.security` implementation changed (`docs/reviews/REVIEW_REQUEST.md:30-35 @
59cda10`).

I parsed all 12 pinned Python files, replayed the analysis in memory using the existing
local candle cache, independently recomputed the ledger and requested censuses from
the committed JSON/JSONL, ran targeted in-memory broker/engine failure probes, scanned
both reviewed histories for secrets, and ran `git diff --check` on both ranges. The
private repository contains no test suite, and `pytest` is not installed there, so
there is no independent automated regression gate to report. I did not contact the
venue. No VPS IP or wallet address is reproduced here.

### Findings, ranked

No CRITICAL finding was verified.

#### HIGH-1 -- The post-fill safety invariant is neither fail-closed nor crash-consistent

`LiveBroker.place_bracket()` treats any parsed successful stop response as sufficient
and can return `sl_oid=None`; it never requires a venue-resting stop OID before moving
on (`src/hip3_executor/broker.py:130-159 @ e93d748`, still present at `2daf6a4`).
`Engine._enter()` obtains the market fill before placing the bracket, catches only
`BrokerError`, makes one unguarded close attempt on a caught bracket error, and does
not create the position record until after both operations
(`src/hip3_executor/engine.py:371-446 @ e93d748`). Durable state is written only at the
end of the cycle (`src/hip3_executor/engine.py:182-188 @ e93d748`). On restart, a real
position missing from that state is merely warned about and deliberately left alone
(`src/hip3_executor/engine.py:206-219 @ e93d748`).

Targeted probes reproduced three unsafe states: an accepted stop response produced
`sl_oid=None`; a non-`BrokerError` after a venue fill escaped with no close, journal
row, or persisted record; and a TP-leg `BrokerError` after the stop rested caused a
market close without cancelling the now-orphaned stop. No such abort appears in the
Weekend-1 ledger, so the live run exercised only the happy path. This contradicts the
documented invariant that a position is never held without a venue stop
(`README.md:41-50 @ e93d748`).

**Required change:** persist a pending entry intent before the market order; journal
client/order IDs and every transition; require and re-query a resting stop; treat all
exception and partial/ambiguous responses as reconciliation states; cancel orphaned
orders; and block new entries until venue positions and orders are adopted or flattened.

#### HIGH-2 -- `KILL_FLAT` can halt and announce success while exposure remains

The flatten loop visits only `state["positions"]`, swallows each close error, and
returns without checking the venue. The caller then unconditionally announces
`KILL_FLAT: flattened everything; halting`, sets `halt=True`, and saves state
(`src/hip3_executor/engine.py:175-180,257-265 @ e93d748`; notifier text at `0f3cf3d`).
Untracked venue positions are outside that loop because reconciliation explicitly
leaves them alone (`src/hip3_executor/engine.py:214-219 @ e93d748`). A probe with a
rejected close reproduced the false-success state: the engine halted while its tracked
position remained open.

The two Weekend-1 kill orders did fill and the committed journal/state finish flat
(`runs/2026-08-22_weekend1/trades.jsonl:65-68` and `state.json:1-12586 @ f4011b6`).
That observed outcome does not test rejection, partial fill, stale state, or orphaned
orders, and the committed venue bundle has no final open-orders receipt. Therefore the
specific weekend close is supported, but the reusable safety claim is not.

**Required change:** flatten from venue-authoritative positions, cancel all relevant
orders, retry/reconcile partial or rejected closes, verify zero positions and zero open
orders, and announce/halt only after that receipt is durable. Otherwise remain in an
error-halt loop that continues flattening and alerts the operator truthfully.

#### MEDIUM-1 -- Isolated leverage is requested but never verified

`set_isolated_leverage()` discards the exchange response
(`src/hip3_executor/broker.py:115-116 @ e93d748`), and `_enter()` immediately submits
the market order (`src/hip3_executor/engine.py:365-373 @ e93d748`). The recorded `lev`
is the requested value, not a venue-confirmed margin-mode/leverage receipt. All 34
entries pass the MAE-clearance equation when evaluated with the recorded leverage, but
the committed artifacts do not prove that the venue accepted isolated mode before
each order. The liquidation-distance safety premise in `README.md:25-28 @ e93d748` is
therefore NOT VERIFIED at the venue boundary.

**Required change:** parse and validate the leverage update response, re-read the
position/margin configuration before entry, and persist the confirmed mode and
effective leverage with the order intent.

#### MEDIUM-2 -- Exit identity and fill validation are too weak for ground-truth attribution

The live classifier selects the first same-coin user fill without constraining close
direction, entry time, or complete OID fragments (`src/hip3_executor/broker.py:173-204
@ a4e7e26`). Its survivor fallback also classifies a targetless record whose stop is
still alive as `target`, because a missing `tp_oid` is treated as a vanished TP
(`src/hip3_executor/broker.py:180-203 @ a4e7e26`). Entry journal rows omit the stored
SL/TP OIDs (`src/hip3_executor/engine.py:386-427 @ e93d748`), and final state is flat,
so the historical OID matches cannot be independently reconstructed from the commit.

Seven of 34 venue close orders have two or three fill fragments. Five journal exit
prices differ from OID-level VWAP; the largest return difference is 0.02511391pp and
the aggregate journal-gross difference is -$0.009165. This does not disturb venue net
P&L, which remains authoritative (`venue/fills.json:1-1464` and `trades.jsonl:1-68 @
f4011b6`). Separately, the TVB-28 validator says it retains fills only when their sizes
sum to the journal size, but both branches return the same list
(`analysis/weekend1.py:169-177 @ c8e65f4`). I independently found exact size and
one-close-OID matches in this dataset, so that bug did not alter this ledger; it can
silently accept a future mismatch.

**Required change:** persist all order/client IDs, restrict reconciliation to closing
fills after the entry, aggregate every fragment by OID, guard `tp_oid is not None`,
defer ambiguous classifications, and make analysis mismatch checks raise or record a
hard failure.

#### MEDIUM-3 -- The +29.71pp flip headline includes a stop that never occurred

The committed result reproduces under the code's convention: 15 flip exits total
-18.45pp; pricing every one at its stop totals -48.16pp; the per-trade-rounded
difference is +29.71pp, or +$8.91 on $30 tickets
(`analysis.json:19825-19839 @ 2daf6a4`; method at
`analysis/weekend1.py:657-685 @ c8e65f4`). But the method aggregates the hypothetical
stop price whether or not `stop_hit_after` is true. Only 14 later touched their stop
first, zero touched target first, and the unresolved fifteenth trade alone contributes
+12.377pp -- 41.7% of the headline (`analysis.json:19825-19839 @ 2daf6a4`). Restricting
the claim to observed stop touches yields +17.338pp, about +$5.20, not +29.71pp.

The exact unrounded all-stop delta is +29.715509pp, which ordinarily rounds to
+29.72pp; +29.71pp results because individual stop/savings values are rounded to three
decimals before aggregation (`analysis/weekend1.py:663-684 @ c8e65f4`). The directional
observation survives: the 14 resolved flips avoided meaningful further loss. The
sentence that every flipped trade later hit its stop, and the comparison that flips
saved more than the whole weekend lost, do not
(`runs/2026-08-22_weekend1/ANALYSIS.md:23-35 @ c8e65f4`).

**Required change:** split observed first-touch savings from unresolved terminal-price
scenarios, aggregate full-precision values before display rounding, and label any
endpoint mark with the exact shared horizon.

#### MEDIUM-4 -- The MMQB pools reproduce as simulations, not as fair swaps or population evidence

The requested pool arithmetic reproduces. Rails-blocked is 176 no-slot + 25 day-cap +
9 already-positioned + 1 cooldown = 211 setups, total -177.951pp, mean -0.843370% per
setup, median -1.13595%; the actual taken book is -0.595% per trade
(`analysis.json:13096-13235 @ 2daf6a4`). The `ftfc_not_aligned` pool is 256 setups,
+60.984pp, mean +0.238219%, median -0.282446%; longs average +0.524720%, shorts
-0.358977%, and the top eight contribute +56.592pp, 92.8% of pool profit
(`analysis.json:16196-16278 @ 2daf6a4`). These are valid descriptions of this
implemented model.

They are not measurement-equivalent to the starters. Taken trades use venue fills and
actual live exits; blocked setups enter at the decision mid and use 1m first-touch plus
the first later opposite row in a signal-sparse decisions journal
(`analysis/weekend1.py:361-439,503-617 @ ddbd9d0`). Portfolio rails are not applied, so
blocked trades that would compete for the same slots are all counted independently.
The rails pool is also endogenous to the actual positions and day budget, not a
randomized bench.

The decision-mid assumption is favorable relative to this run's actual fills. Matching
the 34 entry decisions to venue fills worsens return from decision mid to fill by a mean
0.041pp and median 0.012pp; 21 of 34 fills are worse, with a worst difference of
0.894pp (`decisions.jsonl:1-11909`, `trades.jsonl:1-68`, and
`venue/fills.json:1-1464 @ f4011b6`). The blocked simulations include none of that
observed entry lag.

Calibration on the 15 real flip exits found that the sparse-row proxy saw every flip
late: median 2.36h, mean 4.65h, maximum 17.97h. In that observed set the proxy return
was 27.15pp worse in aggregate than the actual exit, so lateness does not have a fixed
"flattering" sign. In the stack pool, 39 of 256 bracket outcomes occur inside the last
logged non-opposite to first logged opposite interval; conditional gaps have median
1.176h, p90 2.506h, and maximum 5.239h, while an earlier unlogged flip-and-revert is not
bounded at all by this journal. On the 255 common stack simulations, removing the
sparse flip and using brackets only changes +0.231% per setup to +0.435%. Thus +0.238%
is VERIFIED as coded, while a faithful live-exit FTFC ablation is NOT VERIFIED.

The sign of a shared-endpoint sensitivity remains unfavorable for rails (about -0.875%
instead of -0.843%), but that does not make it a controlled swap. The prose calling
the starters a "fair draw," saying a swap loses more, and declaring the result
population-level is unsupported (`ANALYSIS.md:222-268 @ ddbd9d0`). Feed iteration is
ordered by snapshot coin, configured timeframe, and live-list order
(`src/hip3_executor/rules.py:38-55 @ e93d748`), so "arrival luck, full stop" is also
stronger than the evidence; simultaneous candidates may reflect serialization order,
not chronological arrival.

**Required change:** call these pools upper-bound opportunity censuses; do not state a
causal swap result. For a future audit, record poll ID, candidate ordinal, component
FTFC state and transition time; apply a shared run endpoint; and replay both admitted
and refused setups with the same entry and software-exit clock plus an explicit
portfolio allocator.

#### MEDIUM-5 -- A mechanics report repeatedly turns post-hoc P&L into performance and causal claims

The governing product statement says the test is mechanics, never P&L
(`README.md:3-7 @ e93d748`), and the analysis repeats that boundary
(`ANALYSIS.md:10-14 @ c8e65f4`). The following passages cross it and must be read only
as labeled post-hoc observations, not validation, attribution, or promotion evidence:

- flip as the "single best-performing mechanic" (`ANALYSIS.md:23-35 @ c8e65f4`);
- continuations "lost by construction, not by luck" (`ANALYSIS.md:37-52 @ c8e65f4`);
- the R:R floor "validated" and doing exactly the right thing (`ANALYSIS.md:72-95 @ c8e65f4`);
- continuation/reversal "performance," money left on the table, flips being not too twitchy, and "the exits are not the problem" (`ANALYSIS.md:97-145 @ c8e65f4`);
- the fee extrapolation that the floor matters twice and the assertion that caps were protective or likely helped (`ANALYSIS.md:147-172 @ c8e65f4`);
- the fair-draw, bench-swap, confirmation-gate, and direction claims (`ANALYSIS.md:230-288 @ ddbd9d0` and `2daf6a4`);
- the per-signal census and statement that the live book behaved as the earlier map predicted (`ANALYSIS.md:290-307 @ ddbd9d0`);
- round-2 prompts saying live data now agrees with a hit-rate diagnosis and early longs outperformed admissions (`ANALYSIS.md:309-326 @ ddbd9d0`).

The continuation mechanism sentence is also factually incomplete. All seven
continuations did have `target=null`, went 0/7, and exited as five stops plus two flips;
their aggregate venue net is -$4.674291. The broker therefore placed no ordinary TP
(`src/hip3_executor/broker.py:130-159 @ e93d748`). But Type-3 invalidation is another
software exit, and kill can close at a gain (`src/hip3_executor/engine.py:238-265 @
e93d748`). No-TP is structural; 0/7 and loss are sample outcomes, not construction.

The secondary session record also labels detailed hit rate, gross loss, day splits and
exit mix as a live "result" (`docs/HANDOFF.md:57-62 @ 59cda10`). Raw ledger facts may
remain as characterization, but the only pre-registered adjudication is: mechanics
happy path passed and the account moved from 52.60 to 45.75. No P&L sentence in either
document establishes strategy performance.

**Required change:** replace "validates," "best-performing," "protective," "fair
draw," "beat," and causal failure diagnoses with "observed in this ledger under this
model." Keep hypotheses and round-2 ideas in the non-binding design discussion until
pre-registered forward evidence exists.

#### MEDIUM-6 -- Operator reporting contains two independent accounting errors

First, `account_value()` adds perpetual `marginSummary.accountValue` to spot USDC
`total` (`src/hip3_executor/broker.py:94-113 @ b52509f`). The independent ledger chain
reproduces the isolated-margin double-count: all 25 non-flat account-bearing exit rows
are inflated by $2.57 to $11.64 while five flat rows match true realized equity within
$0.01 (`analysis/weekend1.py:688-718 @ c8e65f4`;
`analysis.json:19941-20035 @ 2daf6a4`). The inflation closely tracks remaining open
margin. This method feeds alerts/journal reporting, not sizing or entry rules
(`src/hip3_executor/engine.py:109-115,267-304 @ 8a56ace`), so it did not change trades.

Second, when P&L state is absent, `_close_record()` writes the current exit, then
`_pnl_state()` rebuilds from a journal that already contains it, then adds it again
(`src/hip3_executor/engine.py:67-107,282-304 @ 8a56ace`). That deterministically doubles
the first exit in day/since-start alerts after a fresh or migrated state. It did not
manifest in Weekend-1 because an hourly report initialized P&L state before the next
exit; final state differed from an independent journal rebuild only by rounding.

**Required change:** define one venue-grounded equity field and test it while exactly
one isolated position is open; do not guess at a spot `hold` subtraction without a
captured API contract. Rebuild P&L before appending the current exit, or do not add the
current exit again after a rebuild.

#### MEDIUM-7 -- Neither the live build nor the candle counterfactual has a durable input receipt

The deploy script archives the working directory rather than a clean Git tree, excludes
`.git`, and records no deployed SHA or config digest (`deploy/deploy_from_dev.ps1:18-25
@ 4dec092`). Dependencies have open-ended lower bounds (`pyproject.toml:6-9 @ e93d748`),
`uv.lock` is ignored (`.gitignore:6 @ e93d748`), and the VPS runs `uv sync`
(`deploy/remote_setup.sh:10-13 @ 4dec092`). Journal schema timing corroborates the
documented order of mid-run rulings, and no row was found to which a later gate was
retro-applied. It does not prove the exact source/dependency tree deployed for every
poll. Exact live-build provenance is NOT VERIFIED.

The analysis docstring says the 1m candle snapshot is committed and remains
reproducible after the venue window moves (`analysis/weekend1.py:1-7 @ c8e65f4`), and
`ANALYSIS.md:3-8 @ c8e65f4` repeats that claim. The actual candle files are excluded
(`.gitignore:7-9 @ c8e65f4`); only fills, funding and ledger updates are in Git. I
regenerated `analysis.json` exactly except for its timestamp only because this machine
still has the roughly 53MB ignored cache. A clean checkout cannot reproduce exact
first touches once the venue no longer serves this window.

**Required change:** deploy a clean committed archive and journal source SHA, config
hash and dependency-lock hash at startup. For counterfactuals, commit permitted compact
per-setup touch receipts plus candle hashes and horizon metadata, or archive the exact
inputs in an access-controlled immutable store.

#### LOW-1 -- Secret handling passed the public-leak check, but the inventory and webhook prompt are inaccurate

No tracked `.env`, agent key, webhook URL, known token, VPS IP, or master-wallet value
was found in the reviewed public commit or current public tree. The master wallet is
private-only, but contrary to the work-order wording it also appears in the private
analysis source and venue ledger record, not solely in the private run README
(`analysis/weekend1.py:34` and `venue/ledger_updates.json:7-8 @ c8e65f4`). This is not a
public leak, but the inventory should be truthful. Also, the webhook is described as a
secret (`.env.template:15-16 @ 0f3cf3d`) while `set_webhook.sh` uses an echoing prompt
(`deploy/set_webhook.sh:8 @ 0f3cf3d`).

**Required change:** retain the private-only boundary, update the inventory, and use a
silent prompt for the webhook value.

#### LOW-2 -- The run's weekday labels are off by one day

The dated interval 2026-08-22 through 2026-08-24 was Saturday through Monday, not
Friday through Sunday. The public handoff says Fri-Sun and labels day P&L accordingly
(`docs/HANDOFF.md:10-15,57-60 @ 59cda10`); the private run README calls the legacy exits
Friday rows (`runs/2026-08-22_weekend1/README.md:1,13-16 @ 39255a9`). The timestamps and
UTC date buckets themselves are intact.

**Required change:** correct prose labels to Sat/Sun/Mon without changing any ledger
row or numeric bucket.

### Numerical adjudication

Every requested headline was recomputed rather than accepted from prose:

1. **Venue reconciliation -- VERIFIED.** There are 86 venue fill fragments belonging
   to 68 unique order IDs and 34 complete entry/exit pairs. Raw sums are deposit
   52.600000, `closedPnl=-6.032702`, fees 0.808169 (0.772902 taker + 0.035267 maker),
   and funding cost 0.008401. Therefore
   `52.60 - 6.032702 - 0.808169 - 0.008401 = 45.750728`, which rounds to 45.75.
   Every journal event matched one unique venue OID within 90 seconds and exact
   aggregate size. Sources: `venue/fills.json:1-1464`, `venue/funding.json:1-1094`,
   `venue/ledger_updates.json:1-20`, and `trades.jsonl:1-68 @ f4011b6`; pinned summary
   `analysis.json:3-14 @ c8e65f4`.

2. **Flip savings -- VERIFIED AS CODED, headline interpretation NOT VERIFIED.** The
   reported -18.45pp versus -48.16pp and +29.71pp reproduce under rounded, all-stop
   pricing. Fourteen resolved stop-first observations support +17.338pp; one unresolved
   trade supplies +12.377pp. See MEDIUM-3 and `analysis.json:19825-19839 @ 2daf6a4`.

3. **Continuation 0/7 and no ordinary TP -- VERIFIED; causal wording rejected.** All
   seven have `target=null`; realized exits are five stops and two flips; gross is
   -15.0973pp and venue net is -$4.674291. The absence of a venue TP is structural, but
   the loss is not. Sources: continuation entries in `trades.jsonl:4,12,36,40,52,56,60
   @ f4011b6`, `analysis.json:1166-1179 @ c8e65f4`, and the code cited in MEDIUM-5.

4. **R:R-floor counterfactual -- VERIFIED AS CODED.** From 904 unique FTFC-aligned
   refusals: 614 target, 130 stop, 126 sparse-row flip, 34 open; 623 positive marks are
   68.916%; the sum of the pinned three-decimal detail rows is -139.400pp and its mean
   is -0.154204% per setup,
   matching the displayed -0.154% (`analysis.json:1238-1265 @ c8e65f4`). Nine positives
   are unresolved endpoint marks, not target wins. Removing the sparse flip and using
   brackets only remains negative at -0.116526% per setup. The first-touch function
   skips the containing minute because the candle's minute-open timestamp precedes the
   second-level decision (`analysis/weekend1.py:71-86 @ c8e65f4`); allowing favorable
   full-minute ambiguity changes the mean to about -0.131%, so the negative sign
   survives. An independent scan found no resolving 1m candle in the R:R, rails, or
   stack pools that touched both stop and target, so the stop-before-target tie-break
   did not change these reported outcomes. This is an unconstrained, gross opportunity
   census, not a deployable book.

5. **MMQB pools -- VERIFIED AS CODED; causal claims rejected.** Rails-blocked is 211
   and -0.843370% per setup. `ftfc_not_aligned` is 256 and +0.238219%, with median
   -0.282446%; its top eight are 92.8% of pool profit. The method and timing defects in
   MEDIUM-4 prevent a fair-swap or population inference. Sources:
   `analysis.json:13096-13235,16196-16278 @ 2daf6a4`.

6. **Kind x direction -- VERIFIED, hindsight only.** Independent journal/OID grouping
   gives reversal-long 13 trades, 6 positive, +4.8301pp and +$1.107139 net;
   reversal-short 14/3, -9.9647pp and -$3.282120; continuation-long 5/0,
   -10.8072pp and -$3.352185; continuation-short 2/0, -4.2901pp and -$1.322106.
   This matches `ANALYSIS.md:278-288 @ 2daf6a4`; it does not license a long-only or
   pattern promotion.

7. **`account_value()` isolated-margin double-count -- VERIFIED and isolated to
   reporting.** Twenty-five of 25 non-flat rows are inflated, while five flat rows
   reconcile within one cent. Source and artifact evidence are in MEDIUM-6.

### Confirmed mechanics and scope checks

- All 34 entered decisions had `ftfc == dir`, were beyond trigger and short of any
  target, had a losing-side stop, passed universe/volume, and passed MAE clearance at
  the recorded leverage. The gate implementation is
  `src/hip3_executor/rules.py:110-199 @ 6c68f3b`; the replay source is
  `decisions.jsonl:1-11909 @ f4011b6`.
- All seven continuation entries carry an in-force higher-timeframe reversal backing:
  four 4h, one 1d, two 1M. The rule is
  `src/hip3_executor/rules.py:82-107,128-138 @ 7f784c0`.
- All 28 targeted entries after the frozen schema have recorded R:R >= 1. Maximum
  concurrency is two; there is no same-coin overlap or orphan exit; the shortest
  re-entry is 134.783 minutes; UTC entry counts are 10/12/12; all 34 entries map to
  distinct persisted per-signal-per-bar keys; final recorded positions are empty.
  Sources: `trades.jsonl:1-68`, `decisions.jsonl:1-11909`, and `state.json:1-12586 @
  f4011b6`; dedup definition `rules.py:32-55 @ e93d748`.
- Mid-run entry-rule changes precede the rows to which their schemas apply; the last
  in-scope rule commit is `6c68f3b`, and `8a56ace` is reporting-only. Four legacy
  `unknown_exit` rows reclassify from venue data as three targets and one stop. The run
  docs represent them as predating the deployed classifier, but the journal carries no
  deployed SHA and the new classifier can itself return `unknown_exit`; that deployment
  ordering is NOT VERIFIED. They do not all precede the `a4e7e26` commit timestamp,
  which is why the missing deploy receipt in MEDIUM-7 matters.
- The secondary diff is exactly `.session_startup_prompt.md`, `docs/HANDOFF.md`,
  `docs/reviews/REVIEW_REQUEST.md`, and `docs/reviews/tvb26-codex-audit.md @ 59cda10`.
  It contains no Pine or `request.security` change. Both range diff checks pass.

## 3. Actionable items (reviewer's own list, if provided)

1. Make entry, bracket and restart handling venue-authoritative and crash-consistent -- **HIGH** -- `broker.py:130-159; engine.py:182-219,371-446 @ e93d748` -- persist intent/OIDs, verify a resting stop, reconcile every ambiguous outcome, and halt new entries until safe.
2. Make `KILL_FLAT` prove zero positions and zero orders before announcing or halting -- **HIGH** -- `engine.py:175-180,257-265 @ e93d748` -- flatten venue state with retries and a durable receipt.
3. Verify isolated mode/effective leverage before order entry -- **MEDIUM** -- `broker.py:115-116; engine.py:365-373 @ e93d748` -- parse, re-read and persist venue confirmation.
4. Harden exit/fill identity and journal all OIDs/VWAP fragments -- **MEDIUM** -- `broker.py:173-204 @ a4e7e26; analysis/weekend1.py:169-177 @ c8e65f4` -- reject ambiguity and failed size checks.
5. Correct the flip headline to distinguish 14 observed stops from one unresolved scenario -- **MEDIUM** -- `analysis/weekend1.py:657-685; ANALYSIS.md:23-35 @ c8e65f4`.
6. Reframe MMQB as an upper-bound census and equalize clocks/portfolio constraints before causal comparison -- **MEDIUM** -- `analysis/weekend1.py:361-439,503-617; ANALYSIS.md:222-268 @ ddbd9d0`.
7. Remove performance/validation language from the mechanics report, including the deterministic continuation-loss claim -- **MEDIUM** -- `ANALYSIS.md:23-172,230-326 @ c8e65f4/ddbd9d0/2daf6a4`.
8. Fix both operator accounting paths -- **MEDIUM** -- `broker.py:94-113 @ b52509f; engine.py:67-107,282-304 @ 8a56ace` -- venue-ground equity plus single-count P&L bootstrap.
9. Pin live-build and candle-input provenance -- **MEDIUM** -- `deploy/deploy_from_dev.ps1:18-25 @ 4dec092; analysis/weekend1.py:1-7 @ c8e65f4` -- SHA/config/lock and immutable candle/touch receipts.
10. Make the webhook prompt silent and correct the private wallet inventory -- **LOW** -- `deploy/set_webhook.sh:8 @ 0f3cf3d; analysis/weekend1.py:34 @ c8e65f4`.
11. Correct Fri/Sun labels to Sat/Mon -- **LOW** -- `docs/HANDOFF.md:10-15,57-60 @ 59cda10; runs/2026-08-22_weekend1/README.md:1,13-16 @ 39255a9`.

## ADVISORY (non-binding, requested by the user)

The opinions below are deliberately separated from the defects above. They are design
input, not findings or promotion rulings.

### 1. Honest strategy status

In trader English: the machine proved it can take real small orders, get most of its
protective orders and exits onto the venue, keep a usable ledger, and close a weekend
book. It did not yet prove that it always knows what it owns when something fails. Fix
that before asking the strategy to answer anything else with live money.

The strategy itself has not shown an edge. Thirty-four trades during one changing-rule
weekend cannot do that. The account decline is not proof that the strategy is dead,
and the attractive hindsight pockets are not proof of where its edge lives.

What I would change before another micro-capital round:

1. Fix the lifecycle, `KILL_FLAT`, leverage receipt and accounting defects first.
2. Keep the flip exit for the next like-for-like mechanics round. The 14 resolved cases
   show credible loss reduction, just not the advertised +29.71pp result.
3. Do not loosen the R:R floor from this census. Even generous timing sensitivities
   leave the 904 refused setups negative on average before portfolio constraints and
   costs.
4. Do not loosen the two-slot, cooldown or day rails because of MMQB. That comparison is
   not a replacement portfolio, and its coded result gives no affirmative safety case
   for relaxing them anyway.
5. Either park continuations or give them a pre-registered profit-taking contract. The
   useful finding is not "continuations went 0/7, ban them." It is that targetless
   continuations have no ordinary way to bank a normal advance. A fixed structural
   partial/T1 proxy or a separately licensed trailing rule can be tested without
   pretending this sample chose the winner.
6. Treat reversal-long, direction/regime, and earlier-confirmation ideas as shadow arms.
   Do not turn +4.83pp in 13 reversal-long trades into a long-only rule.

Was it too restrictive? Not generally, on this evidence. The system looks more
under-specified on continuation exits than over-restricted at entry. There may be a
narrow confirmation-lag question in 4h longs during the positive middle day, but the
stack pool is concentrated: the top eight create 92.8% of its profit. My independent
date/timeframe split is equally cautionary -- Aug 22 is -21.74pp, Aug 23 +107.21pp,
Aug 24 -24.48pp; 1h is -24.78pp while 4h is +85.76pp. Removing the top eight leaves
about +4.39pp, and removing the top nine turns the pool negative. That is a useful
hypothesis about one regime/timeframe/direction cluster, not evidence that FTFC is
generally too strict.

### 2. Relation to the prior TVB-21 through TVB-25 record

The executor is closest to the M+T/package world, especially D1: pattern-triggered
entry, an entry floor, and full exit at first structural target. It is not a live
version of the continuity-only A0b control. `docs/ARM_LEDGER.md:11-14` correctly says
those historical gross readings are characterization, not rankings; its package
definitions are at `:21-35,112-143`.

The resemblance is not identity. The research package used 1h patterns, D/W/M
alignment, fixed target-distance/chop/BF filters and a one-position-per-symbol
simulation. This executor uses 1h/4h/1d signals, a 15m/1h/4h/1d FTFC gate, R:R >= 1,
live fills, shared two-slot capital, isolated leverage, structural stops, and a separate
targetless continuation license. Direct expectancy comparison would be false precision.

The prior arcs still give useful cautions:

- D1 full-T1 was the plain low-drawdown package comparator
  (`docs/ARM_LEDGER.md:121-137`). That supports retaining simple full-T1 as the baseline,
  not declaring it optimal live.
- The same structural-stop overlay helped the continuity control and hurt the package
  sample (`:88-93,138-143`). Stop value is book-dependent. Live safety still requires a
  stop even if a backtest says the overlay costs gross P&L.
- Simple P1 beat the more elaborate P2 on the matched subset, and the no-target X1
  stalled badly (`:144-169`). Four post-target runners in this weekend are a question,
  not a license to bolt on a runner profile.
- Flip was nearly inert only when a faster hourly state stop already existed
  (`:101-103,193-195`). The executor has no equivalent completed-hour state stop, so
  active live flips do not contradict that earlier result.

The right comparison for round two is therefore an ablation inside the executor's own
book: unchanged full-T1 reversal baseline, then one pre-registered change at a time.
Do not compare its $52.60 live account path to the ARM_LEDGER's additive gross pp as if
they were the same unit, capital allocator, venue, or observation clock.

### 3. Monday-morning-quarterback survivorship audit

Why did the traded tickers get seats? Mechanically, the executor walks the feed's coin
order, configured timeframe order and each live-signal list. The first newly seen setup
that passes all gates while its coin, slot, cooldown and daily budget permit gets the
seat. There is no quality score. Calling this "arrival ordered" is shorthand; for
same-poll candidates it is serialization order, not necessarily which market event
happened first.

Were skipped setups better? Some individual simulated misses were much better and some
were much worse. The committed census is useful for finding those tails. It does not
show that the 34 starters were a fair random sample or that swapping in all 211 blocked
setups would produce -0.843% per trade. Those candidates were blocked precisely because
the real portfolio was occupied, and the simulation then lets all of them coexist
without those constraints. The `ftfc_not_aligned` pool is even more clearly a gate
ablation: its positive mean comes from a small long/4h/date cluster and a sparse flip
clock whose live timing is unknown.

The most useful extension is instrumentation, not another sort by P&L. For every poll,
write a poll ID, candidate ordinal, source snapshot timestamp, each 15m/1h/4h/1d FTFC
component, the aggregate transition timestamp, gate vector, hypothetical order price,
and the seat-holder that displaced it. Then replay a pre-registered allocator with the
same two slots, day/cooldown rules, entry slippage, fee model, software-exit clock and
shared end time. That would answer "which candidate would actually have replaced which
starter?" rather than "what if every person outside the club got a private table?"

### 4. Pattern-by-pattern books: characterization or tournament trap?

Separate pattern books are informative if they are ceiling maps and diagnostic
ablations. They become a tournament trap the moment the best row earns capital because
it won this census. The governing rule is explicit: pre-committed blocks must beat the
control directly below them, while sample-ranked pattern promotion is forbidden
(`CLAUDE.md:67-75`; charter Section 0 at
`docs/ATLAS_Timeframe_Continuity_Charter.md:7-23` and the ablation contract at
`:52-88,143-168`).

A charter-clean design would be:

1. Pre-register the complete pattern-family map, grouping rules, directions, universe,
   timeframes, windows, costs, entry/exit clock and shared endpoint before opening
   outcome data.
2. Keep one unchanged composite executor baseline.
3. Run broad structural blocks first: reversal versus continuation; compression-bearing
   versus bare reversal; then at most one pre-stated direction/regime interaction.
4. Add leave-one-family-out arms to measure marginal contribution while preserving the
   shared two-slot occupancy and displacement effects.
5. Run one-pattern-only books only as labeled equal-risk ceiling maps. Report both an
   independent-capital view and a shared-account portfolio view; never compare an
   unlimited set of private books directly with the two-slot baseline.
6. Record overlap, opportunity count, rail displacement, turnover, MFE/MAE and net
   costs, not just win rate or P&L.
7. Freeze the ladder, run untouched forward windows across more than one regime, and
   require a repeated mechanism-consistent improvement over the immediately lower rung.
8. Promote nothing because it topped the census. Any idea suggested by Weekend-1 --
   long reversals, 4h early confirmation, or a continuation profit-taking rule -- starts
   as a newly pre-registered shadow hypothesis.

That design lets pattern-by-pattern books teach you where the composite is fragile
without quietly turning 34 live trades into a selection tournament.
