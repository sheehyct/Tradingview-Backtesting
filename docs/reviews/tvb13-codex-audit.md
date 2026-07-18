<!--
Copy to docs/reviews/tvb{N}-codex-audit.md and fill in.
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-13 External Audit -- Codex CLI / GPT-5 (verbatim source, read CRITICALLY)

> External review of commit range `1f53463^..32efec6` on `main`, including the
> TVB-12 fold-in, BF comprehension indicator, give-back fixture, C4 relabels,
> and frozen winner-surface notes, captured 2026-07-18 (TVB-13 post-session).
> Lightly ASCII-normalized (em-dashes -> --, curly quotes -> straight);
> wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-13 -- BF comprehension surface, TVB-12 fold-in, and give-back v1
- **Reviewed:** commit range `1f53463^..32efec6` on `main`
- **Reviewer:** Codex CLI / GPT-5
- **Overall verdict:** NEEDS-CHANGES

## 2. Verbatim audit

### Overall assessment

NEEDS-CHANGES.

The strict R10 classifier, corrected period-start aggregation clock, zero-
`request.security` BF implementation, rolling history guard, C4 relabels,
winner-header diagnoses, raw DRAM candles, and published give-back arithmetic
all pass the checks described below.

The central failure is in the defining Rob-canonical proximity geometry. The
indicator chooses the anchor when the open HTF candle first becomes a 3, moves
only the line's current-candle endpoint as that candle extends, and then
solidifies the line without re-running the price-nearest anchor scan. A
deterministic replay of the committed DRAM bars finds stale final anchors on
two of four 12h fires. This is not cosmetic: a provisional line can become a
solid line that does not satisfy the locked anchor rule.

The C1 strategy adjudication needs a narrower statement, not a wholesale
reversal. I found no path where the active entry stop references an
uncompleted arm period. Resting stops do cure that specific early-snapshot
problem at every child position, including `chart_tf == arm_tf`. However, a
default close-calculated strategy cannot revoke or create that pending order
when the "live" gate changes intrabar. The measured record therefore supports
the completed-arm-level contract, but it does not by itself prove the broader
"revocable while the live gate is aligned" contract.

### Findings, ranked by severity

#### HIGH -- The proximity anchor can be wrong when a provisional HTF 3 solidifies

The locked rule is the minimum prior low strictly above the 3 candle's final
low and the maximum prior high strictly below its final high, with the two
sides independent (`docs/design/bf_comprehension_indicator_design.md:83-98`).
The implementation runs that scan only on the fire bar
(`pine/bf_comprehension.pine:181-206`). Later bars can extend `curLo` or
`curHi`, but only `xy2` is updated (`pine/bf_comprehension.pine:207-215`).
At the next period boundary, the now-stale line is made solid
(`pine/bf_comprehension.pine:129-135`).

The scan is correct at the instant of fire: it uses strict operators, searches
all retained prior aggregate candles, anchors each side independently, and
falls back to the adjacent reference when no candidate exists. The defect is
that "nearest in price" is a function of the final current extreme. If the
open HTF candle extends, a different prior candle can become the nearest valid
anchor.

Command (read-only replay of the Pine boundary, latch, and anchor rules):

```powershell
$src = @'
const fs=require("fs");
const bars=JSON.parse(fs.readFileSync("analysis/reference/tvb13_dram_jun_15m_hl.json","utf8")).bars;
const iso=t=>new Date(t*1000).toISOString().replace(".000Z","Z");
for (const [name,span] of [["12h",43200],["D",86400]]) {
  const hist=[]; let cur=null,fired=false,bHi=false,bLo=false,events=[];
  for (const b of bars) {
    const [t,o,h,l,c]=b, k=Math.floor(t/span)*span;
    if (!cur || cur.k!==k) {
      if (cur) hist.push(cur);
      cur={k,hi:h,lo:l,hiT:t,loT:t}; fired=false;bHi=false;bLo=false;
    } else {
      if (h>cur.hi) {cur.hi=h;cur.hiT=t}
      if (l<cur.lo) {cur.lo=l;cur.loT=t}
    }
    if (!fired && hist.length) {
      const p=hist.at(-1); bHi=bHi||h>p.hi; bLo=bLo||l<p.lo;
      if (bHi&&bLo) {
        const choose=(lo,hi)=>{let lower=null,upper=null;for(const x of hist){if(x.lo>lo&&(lower===null||x.lo<lower))lower=x.lo;if(x.hi<hi&&(upper===null||x.hi>upper))upper=x.hi}return [lower??p.lo,upper??p.hi]};
        events.push({k,t,ref:p,fireAnchor:choose(cur.lo,cur.hi),fireExt:[cur.lo,cur.hi],closeInside:c<p.hi&&c>p.lo}); fired=true;
      }
    }
  }
  if(cur) hist.push(cur);
  let changed=0,inside=0,late=0;
  for(const e of events){
    const final=hist.find(x=>x.k===e.k);let lower=null,upper=null;
    for(const x of hist.filter(x=>x.k<e.k)){if(x.lo>final.lo&&(lower===null||x.lo<lower))lower=x.lo;if(x.hi<final.hi&&(upper===null||x.hi>upper))upper=x.hi}
    const finalAnchor=[lower??e.ref.lo,upper??e.ref.hi];
    if(JSON.stringify(finalAnchor)!==JSON.stringify(e.fireAnchor)){changed++;console.log(`${name} anchor_change fire=${iso(e.t)} fire_anchor=${e.fireAnchor.join(",")} final_anchor=${finalAnchor.join(",")} fire_ext=${e.fireExt.join(",")} final_ext=${final.lo},${final.hi}`)}
    if(e.closeInside){inside++;const next=bars.find(b=>b[0]===e.t+900);if(next&&next[4]<e.ref.hi&&next[4]>e.ref.lo)late++;}
  }
  console.log(`${name} fires=${events.length} anchor_changed_by_close=${changed} fire_bar_close_inside=${inside} late_if_next_inside=${late}`);
}
'@; $src | node -
```

Output:

```text
12h anchor_change fire=2026-05-27T13:45:00Z fire_anchor=60.093,63.374 final_anchor=59.563,63.374 fire_ext=59.624,63.572 final_ext=58.564,63.572
12h anchor_change fire=2026-06-03T13:30:00Z fire_anchor=68.624,69.947 final_anchor=67.15,69.947 fire_ext=68.55,69.98 final_ext=66.385,69.98
12h fires=4 anchor_changed_by_close=2 fire_bar_close_inside=2 late_if_next_inside=2
D fires=4 anchor_changed_by_close=0 fire_bar_close_inside=1 late_if_next_inside=1
```

Required change: while the current HTF candle is provisional, recompute the
affected side's anchor whenever its extreme extends, or perform a final scan
before pushing the completed candle into history and making the line solid.
Add a fixture that asserts both the fire-time and close-time geometry.

#### MEDIUM -- C1 exonerates the arm snapshot, but not the broader live-gate entry contract

The HANDOFF says the strategy implements the advertised contract at every
child position and therefore leaves the TVB-11/12 record untouched
(`docs/HANDOFF.md:48-56`). The first half is correct when "contract" means the
arm level:

- The strategy uses default close-only calculation: its declaration enables
  Bar Magnifier but does not enable `calc_on_every_tick`,
  `calc_on_order_fills`, or `process_orders_on_close`
  (`pine/tvb_exp_champion.pine:46-51`).
- During a non-final child, the active order was created at the prior chart
  close from the last completed arm period. During the final child, that same
  order is already active. Only at the final-child close does the code roll
  `prev_ah`/`prev_al` (`pine/tvb_exp_champion.pine:213-231`) and reissue the
  pending stop (`pine/tvb_exp_champion.pine:313-345`) for the next tick.
- With `chart_tf == arm_tf`, the order active during bar N was created after
  bar N-1 closed from bar N-1's final extreme. The snapshot of bar N cannot
  affect a fill until bar N+1.
- A gap through the stop fills at the new bar's open, but the level still came
  from a completed arm bar. Disabling Bar Magnifier changes intrabar fill
  resolution, not when the strategy calculates or creates the order.

TradingView documents default strategy calculation after bar close and
next-tick order activation, gap-through fills at the current open, and Bar
Magnifier as a lower-timeframe fill model rather than a recalculation mode:
[execution model](https://www.tradingview.com/pine-script-docs/language/execution-model/),
[strategy order semantics](https://www.tradingview.com/pine-script-docs/concepts/strategies/).
I found no uncompleted-arm-level leak.

The replay trade lists are consistent with that conclusion. They contain
fills in every 5m child position and thousands of fills in `chart_tf ==
arm_tf` cells:

```powershell
$src=@'
const fs=require("fs"),rows=fs.readFileSync("docs/experiments/tvb12_replay_run.jsonl","utf8").trim().split(/\r?\n/).map(JSON.parse);
for(const tf of ["5","15","60"]){const a=rows.filter(r=>r.chart_tf===tf&&r.arm_tf===tf);console.log(`chart_eq_arm=${tf} cells=${a.length} closed_entries=${a.reduce((s,r)=>s+r.report.trades,0)}`)}
const p=[0,0,0];for(const r of rows.filter(r=>r.chart_tf==="5"&&r.arm_tf==="15"))for(const t of r.report.list||[])if(!t.open&&t.et!=null)p[Math.floor(t.et/300000)%3]++;console.log(`chart5_arm15_closed_entry_bar_positions first=${p[0]} middle=${p[1]} final=${p[2]}`);
'@;$src|node -
```

```text
chart_eq_arm=5 cells=1 closed_entries=18
chart_eq_arm=15 cells=49 closed_entries=2346
chart_eq_arm=60 cells=13 closed_entries=2250
chart5_arm15_closed_entry_bar_positions first=208 middle=222 final=142
```

Those counts disprove an entry-dead strategy, but they do not prove the
broader "revocable stop while the live gate is aligned" comment
(`pine/tvb_exp_champion.pine:313`) or the pre-registered statement that the
order is always resting while gate-aligned
(`docs/experiments/tvb11_champion_prereg.md:103-106`). The gate is derived
from the current `close` (`pine/tvb_exp_champion.pine:147-177`), yet the
strategy does not recalculate it between chart-bar closes:

- An order left pending from the previous close can fill at the next open or
  intrabar before a now-neutral/opposite gate is calculated and canceled.
  The first child of a new D/W/M period is a concrete edge: the new period
  open makes that component neutral at the opening tick, but the old pending
  order is processed before the close-only script can cancel it.
- Conversely, if the gate becomes aligned and price breaks the stop during a
  bar that began without an order, the strategy cannot create the order until
  the close. A stop already behind the market then activates on the next tick,
  producing a delayed entry rather than the advertised same-bar break.
- Reissuing a pending order with the same ID modifies it only when that
  bar-close calculation occurs. Bar Magnifier supplies lower-timeframe prices
  to the emulator; it does not make the gate or cancellation intrabar-live.

No committed artifact contains a per-fill gate/order-state trace, so I cannot
quantify whether any recorded trade uses one of those paths. The defensible
statement is: "C1 does not invalidate the completed-arm snapshot or require a
clock correction to the record." The stronger assertion that the whole live
entry contract is implemented at every child position is not established.

Required change: narrow the HANDOFF/header wording, or add a lower-timeframe
fixture that records gate state at order creation, activation, cancellation,
and fill. If contemporaneous live-gate validity is intended, the strategy
model itself needs an explicit intrabar contract; it cannot be inferred from
Bar Magnifier.

#### MEDIUM -- Freeze-as-of is not exact at the requested instant, and L1 ignores it

The input promises to ignore all bars after the freeze moment and show the
formation exactly as it stood then (`pine/bf_comprehension.pine:48-52`).
There are two violations:

1. `time <= asof_t` compares the freeze timestamp to the bar's opening time.
   TradingView defines `time` as the opening timestamp and `time_close` as the
   closing timestamp
   ([time documentation](https://www.tradingview.com/pine-script-docs/concepts/time/)).
   On a 15m chart, a freeze at 00:00 includes the final OHLC of the entire
   00:00-00:15 bar. Events after the requested instant can therefore alter
   aggregate extremes, fire a 3, choose anchors, and create drawings.
2. The L1 plot calls are outside `proc_ok` entirely
   (`pine/bf_comprehension.pine:75-86`). Every later chart bar can continue to
   add 1/2U/2D/3 marks even while the status table says `FROZEN`
   (`pine/bf_comprehension.pine:275-283`).

The aggregate engine itself is gated at `pine/bf_comprehension.pine:117`, and
rolling fire labels are gated at `pine/bf_comprehension.pine:245`, so later
bars do not otherwise mutate those state machines. Extending frozen lines
rightward is an explicitly disclosed grading feature, not this finding.

The operator/security scan also confirms that the only `<=` in state
processing is this freeze boundary:

```powershell
$src = Get-Content pine\bf_comprehension.pine; $exec = for ($n=0; $n -lt $src.Count; $n++) { if ($src[$n] -notmatch '^\s*//') { [pscustomobject]@{Line=$n+1; Text=$src[$n]} } }; 'executable_request.security_calls=' + (($exec | Where-Object Text -Match 'request\.security\s*\(').Count); 'all_non_strict_operator_lines:'; $exec | Where-Object Text -Match '>=|<=' | ForEach-Object { '{0}: {1}' -f $_.Line,$_.Text.Trim() }
```

```text
executable_request.security_calls=0
all_non_strict_operator_lines:
52: bool proc_ok = not use_asof or time <= asof_t
85: plotchar(show_l1 and cls3 and close >= open ? true : false, 'Type 3 (green close)', '3', location.belowbar, color.new(color.purple, 0), size = size.small)
238: bool ok = en and nRaw > 1 and nRaw * 2 <= 2000
```

Line 85 is a color choice, not an R10 level break; line 238 is the history
guard. Structural classification remains strict.

Required change: define whether the timestamp means "last fully closed chart
bar" or an intrabar instant. For the former, admit OHLC only when
`time_close <= asof_t`; separately finalize the previous HTF period at a
boundary without ingesting the next bar's OHLC. Gate L1 with the same
effective freeze predicate.

#### MEDIUM -- L4 skips the canonical same-bar restart, and superseded lines retract

The design says a formation restarts when price trades back inside the prior
range and explicitly treats re-entry as the event that changes the trade's
footing (`docs/design/bf_comprehension_indicator_design.md:103-119`,
`:147-150`). The Pine comment goes further: an outside bar closing back inside
the prior range is the canonical restart illustration
(`pine/bf_comprehension.pine:216-218`).

The code nevertheless requires `not fired_now`
(`pine/bf_comprehension.pine:219`). Therefore, if the aggregate 3 fires and
the same confirmed chart bar closes inside the taken-out reference range, L4
cannot mark the restart until a later bar. The HIGH finding's deterministic
replay found this on two of four 12h fires and one of four daily fires; in all
three committed cases the next bar also closed inside, so the shipped marker
is exactly one chart bar late:

```text
12h fires=4 anchor_changed_by_close=2 fire_bar_close_inside=2 late_if_next_inside=2
D fires=4 anchor_changed_by_close=0 fire_bar_close_inside=1 late_if_next_inside=1
```

There is a second lifecycle mismatch. When a new 3 supersedes the old line,
the code switches the old line from `extend.right` to `extend.none` and fades
it (`pine/bf_comprehension.pine:169-174`), but it does not first move `x2` to
the supersede time. The visible extension retracts to the originating HTF
extreme rather than remaining as faded historical structure through the
supersede event. That is inconsistent with the recorded self-extending
formation semantics
(`docs/design/bf_comprehension_indicator_design.md:114-119`).

Required change: evaluate the confirmed fire bar for restart after creating
the formation, and pin an old line's second endpoint at the supersede bar
before disabling extension.

#### MEDIUM -- Give-back arithmetic is correct, but boundary-bar MAE and "live account" wording overstate fidelity

The short definitions, signed realized return, percentage-point give-back,
fractional give-back, and long mirror are algebraically correct
(`analysis/giveback.py:9-17`, `:43-76`). The published fixture recomputes
exactly:

```powershell
uv run --no-cache python analysis\giveback.py --bars analysis\reference\tvb13_dram_jun_15m_hl.json --dir short --entry-time 2026-06-04T19:45:00Z --entry-price 65.88 --exit-time 2026-06-14T06:45:00Z --exit-price 66.66
```

```text
{
 "direction": "short",
 "entry_time_s": 1780602300,
 "exit_time_s": 1781419500,
 "bars": 909,
 "mfe": 0.19872495446265936,
 "mae": 0.012097753491196286,
 "realized": -0.011839708561020054,
 "give_back_pp": 21.056466302367944,
 "give_back_frac": 1.0595783684692943,
 "mfe_time_s": 1780713000,
 "hours_to_mfe": 30.75
}
```

An independent synthetic long episode also mirrors correctly:

```powershell
uv run --no-cache python -c "from analysis.giveback import episode_metrics; b=[[0,100,100,100,100,0],[60,100,120,80,110,0],[120,110,115,90,110,0]]; print(episode_metrics(b,'long',0,100,120,110))"
```

```text
{'direction': 'long', 'entry_time_s': 0, 'exit_time_s': 120, 'bars': 3, 'mfe': 0.2, 'mae': 0.2, 'realized': 0.1, 'give_back_pp': 10.0, 'give_back_frac': 0.5, 'mfe_time_s': 60, 'hours_to_mfe': 0.016666666666666666}
```

The episode selector is reproducible once the account-derived levels and
known bottom are supplied. Three reasonable 15m downward-cross definitions
all choose the committed entry timestamp, and the first later high touch
chooses the committed exit:

```powershell
$src = @'
const fs=require("fs"),b=JSON.parse(fs.readFileSync("analysis/reference/tvb13_dram_jun_15m_hl.json","utf8")).bars,L=65.88,X=66.66,iso=t=>new Date(t*1000).toISOString().replace(".000Z","Z");
const bottom=b.reduce((a,x)=>x[3]<a[3]?x:a,b[0]),bi=b.indexOf(bottom);
const rules={"prev_close_to_low":(p,x)=>p[4]>L&&x[3]<=L,"close_to_close":(p,x)=>p[4]>L&&x[4]<=L,"open_to_low":(p,x)=>x[1]>L&&x[3]<=L};
for(const [n,f] of Object.entries(rules)){let hit;for(let i=1;i<=bi;i++)if(f(b[i-1],b[i]))hit=b[i];console.log(`${n} last=${iso(hit[0])}`)}
const exit=b.slice(bi+1).find(x=>x[2]>=X),ei=b.indexOf(exit),entry=b.find(x=>x[0]===1780602300),interior=b.slice(b.indexOf(entry)+1,ei);
console.log(`bottom=${bottom[3]}@${iso(bottom[0])} first_exit_touch=${iso(exit[0])} high=${exit[2]}`);
console.log(`entry_bar_high=${entry[2]} interior_max_high=${Math.max(...interior.map(x=>x[2]))} exit_bar_high=${exit[2]}`);
console.log(`full_bar_mae_pct=${((Math.max(entry[2],...interior.map(x=>x[2]),exit[2])-L)/L*100).toFixed(6)} capped_at_exit_pct=${((X-L)/L*100).toFixed(6)}`);
'@; $src | node -
```

```text
prev_close_to_low last=2026-06-04T19:45:00Z
close_to_close last=2026-06-04T19:45:00Z
open_to_low last=2026-06-04T19:45:00Z
bottom=52.788@2026-06-06T02:30:00Z first_exit_touch=2026-06-14T06:45:00Z high=66.677
entry_bar_high=66.487 interior_max_high=66.657 exit_bar_high=66.677
full_bar_mae_pct=1.209775 capped_at_exit_pct=1.183971
```

That output also exposes the fidelity problem. `episode_metrics()` includes
the full entry and exit bars (`analysis/giveback.py:48`). With only 15m OHLC,
the entry bar's high can precede the downward-cross fill and the exit bar's
high can follow the first-touch exit. The reported 1.21% is therefore a
conservative full-bar envelope, not a uniquely knowable in-trade MAE. Merely
capping the exit bar at the known exit price gives 1.183971%; the entry-bar
path remains unknown.

Also, `realized` is a gross price return. It contains no commission, slippage,
or funding, so the claims that the metrics reproduce the "live account
exactly" (`analysis/giveback.py:19-23`, `docs/HANDOFF.md:170-175`) are too
strong. They reproduce the reported gross price move to the displayed
precision.

Finally, "last cross before the known bottom" is retrospective selection using
future knowledge. The repository does label the fixture "hand-labeled"
(`tests/test_giveback_fixture.py:1-8`), which is honest, but the test hardcodes
the selected timestamps (`tests/test_giveback_fixture.py:16-35`) rather than
testing the derivation. This is a valid account reconstruction and acceptance
fixture, not independent evidence for an entry or exit rule.

The committed venue data itself passed a live public-API comparison over the
declared May 30-June 15 interval:

```powershell
$src = @'
const fs=require("fs");
(async()=>{const start=Date.parse("2026-05-30T00:00:00Z"),end=Date.parse("2026-06-15T00:00:00Z");const r=await fetch("https://api.hyperliquid.xyz/info",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({type:"candleSnapshot",req:{coin:"xyz:DRAM",interval:"15m",startTime:start,endTime:end}})});if(!r.ok)throw Error(`${r.status} ${await r.text()}`);const live=await r.json(),bars=JSON.parse(fs.readFileSync("analysis/reference/tvb13_dram_jun_15m_hl.json","utf8")).bars.filter(b=>b[0]*1000>=start&&b[0]*1000<=end),m=new Map(live.map(x=>[x.t,x]));let missing=0,mismatch=0;for(const b of bars){const x=m.get(b[0]*1000);if(!x){missing++;continue}const v=[x.o,x.h,x.l,x.c,x.v].map(Number);if(v.some((z,i)=>Math.abs(z-b[i+1])>1e-9))mismatch++}console.log(`live_bars=${live.length} first=${new Date(live[0].t).toISOString().replace(".000Z","Z")} last=${new Date(live.at(-1).t).toISOString().replace(".000Z","Z")} missing_from_commit=${missing} ohlcv_mismatches=${mismatch}`)})().catch(e=>{console.error(e);process.exit(1)});
'@; $src | node -
```

```text
live_bars=1537 first=2026-05-30T00:00:00Z last=2026-06-15T00:00:00Z missing_from_commit=0 ohlcv_mismatches=0
```

Required change: label MFE/MAE as inclusive bar-envelope metrics unless
lower-timeframe boundary paths are available; rename `realized` to
`gross_price_return` or add explicit net inputs; and either implement the
cross/touch selector in a tested helper or keep calling the timestamps
hand-labeled. Do not use this retrospectively pinned episode as validation of
a candidate rule.

#### LOW -- `summarize()` does not calculate the conventional median for even samples

The percentile helper selects one nearest-rank observation using
`round(q * (n - 1))` (`analysis/giveback.py:80-98`). Python's ties-to-even
rounding makes the "median" of `[0, 10]` equal 0 rather than 5:

```powershell
uv run --no-cache python -c "from analysis.giveback import summarize; r=lambda x:{'give_back_pp':x,'mfe':0.03,'realized':0.01}; print(summarize([r(0.0),r(10.0)]))"
```

```text
{'episodes': 2, 'mfe_pct': {'median': 3.0, 'p90': 3.0}, 'give_back_pp': {'median': 0.0, 'p90': 10.0}, 'winners_2pct_plus': 2, 'full_round_trips': 0}
```

This does not affect the one-episode acceptance number, but it will bias the
distribution surface the module is intended to produce. Use
`statistics.median` for median and declare a standard quantile interpolation
method for p90; test even and odd sample counts.

#### LOW -- BF "exact" and provisional-state disclosures need tighter bounds

The header says chart-side HTF aggregation is exact on 24/7 perps
(`pine/bf_comprehension.pine:29-37`). The implementation checks only that a
rung is higher than the chart timeframe
(`pine/bf_comprehension.pine:115`). It does not require the chart timeframe to
tile the rung. For example, a 45m chart bar can straddle a native 60m
boundary; no chart-side max/min can split that OHLC into the two native
periods. The default DRAM 15m surface tiles all default rungs and is not
affected, but the unconditional "Exact on 24/7 perps" claim is false off that
surface. Add the same divisibility guard used by the champion strategy or
qualify the header.

The lines do change from dashed to solid at the HTF close
(`pine/bf_comprehension.pine:129-135`), but the shaded box has no provisional
versus confirmed style transition and the fire label's tooltip remains
"Provisional until the period closes" forever
(`pine/bf_comprehension.pine:165-168`). Thus the quick-start claim that
"hollow shading" solidifies (`pine/bf_comprehension.pine:23-24`) is not
implemented as a visible state change.

The rolling guard is safe: `nRaw * 2 <= 2000` is checked before assigning the
history length, and an oversized rung falls back to `n=1` without a large
history reference (`pine/bf_comprehension.pine:236-249`). It silently skips
the rung, as disclosed. There is no 5,000-bar buffer blow-up. The documentation
does drift, however: the design promises about 4,900 loaded bars
(`docs/design/bf_comprehension_indicator_design.md:95-98`) while the shipped
per-rung archive is 2,000 candles, and the footer still says no Pine exists
(`docs/design/bf_comprehension_indicator_design.md:194-195`).

### Focus-area passes and negative checks

#### Range and out-of-scope documentation moves

The requested range is exactly eight commits and fourteen changed paths:

```powershell
git log --oneline 1f53463~1..32efec6
git diff --name-status 1f53463~1 32efec6
```

```text
32efec6 docs(tvb): TVB-13 session end -- BF comprehension shipped, give-back v1 landed, TVB-14 seeded, full-scope review requested
e590365 feat(tvb): give-back instrumentation v1 -- MFE/MAE calculator + DRAM June fixture archived and hand-labeled
37a3a9c feat(tvb): BF Comprehension freeze-as-of input -- grade historical episodes with period-true lines
ab7d8b8 feat(tvb): BF Comprehension [TVB-13] v1 -- order-free scenario-3/BF comprehension surface
23d0536 docs(tvb): Rob-canonical BF anchor rule + behavioral semantics; winner surfaces frozen with C1 header notes
7e6995a docs(tvb): TVB-12 review RETURNED -- audit committed, critical synthesis + remediation queue, C4 relabels applied
b6c4a3a docs(tvb): BF design correction -- two line modes (adjacent vs compound take-out), never 3-to-previous-3
1f53463 docs(tvb): BF comprehension indicator design draft -- both compound-3 window modes as toggles, 60m TF floor, fixture-graded acceptance
M  .session_startup_prompt.md
A  analysis/giveback.py
A  analysis/reference/tvb13_dram_jun_15m_hl.json
M  docs/HANDOFF.md
A  docs/design/bf_comprehension_indicator_design.md
M  docs/experiments/tvb12_replay_plan.md
M  docs/reviews/REVIEW_REQUEST.md
A  docs/reviews/tvb12-codex-audit.md
A  pine/bf_comprehension.pine
M  pine/winner_champion_mu15.pine
M  pine/winner_generalizer.pine
M  pine/winner_shortchamp_mu5.pine
M  pine/winner_slow60.pine
A  tests/test_giveback_fixture.py
```

`git diff --check 1f53463~1 32efec6` produced no output.

The two later commits are content-neutral with respect to the reviewed
implementation and data. The TVB-0..9 archive payload exactly equals the
removed HANDOFF block:

```powershell
$old=@(git show '57b9c66^:docs/HANDOFF.md');$arch=Get-Content docs\session_archive\HANDOFF_TVB0-TVB9.md;$oi=[array]::FindIndex($old,[Predicate[string]]{param($x)$x -match '^## Session TVB-9:'});$ai=[array]::FindIndex($arch,[Predicate[string]]{param($x)$x -match '^## Session TVB-9:'});$removed=$old[$oi..($old.Count-1)];$payload=$arch[$ai..($arch.Count-1)];"removed_lines=$($removed.Count) archive_payload_lines=$($payload.Count) exact_equal=$([string]::Join("`n",$removed) -ceq [string]::Join("`n",$payload))"; "implementation_or_reference_changes_after_pinned_head=$((git diff --name-only 32efec6 HEAD -- pine analysis/reference analysis tests | Measure-Object).Count)"
```

```text
removed_lines=1128 archive_payload_lines=1128 exact_equal=True
implementation_or_reference_changes_after_pinned_head=0
```

#### BF R10, aggregation clock, security discipline, and rolling guard

- All structural high/low comparisons use strict `>`/`<`: L1 at
  `pine/bf_comprehension.pine:76-81`, running extremes at `:147-152`,
  aggregate latches at `:157-159`, proximity candidates at `:190-204`, and
  rolling comparison at `:240-245`. Equality never breaks a level.
- At `timeframe.change(tf)`, the completed current aggregate is pushed to
  history, then the new aggregate is initialized, then the latch reads the
  last history element (`pine/bf_comprehension.pine:118-159`). This is the
  corrected period-start C1 clock. I found no ordering defect on tiled 24/7
  charts.
- The BF script has zero executable `request.security` calls, as its header
  claims. The earlier static-scan output confirms this.
- The 2,000-window rolling guard is safe, as discussed in the LOW finding.

#### C4 relabels fully cure the named closure-language overreach

The dated HANDOFF qualifier now says 54 targeted cells, 3.76%, three complete
Stage B symbol blocks, and an open 736-record provenance gap
(`docs/HANDOFF.md:102-111`, `:232-236`). The dated additive correction in the
plan says the unobserved rows were not validated, the 10-config x 7-perp
median ranking was not recomputed, four competitor medians were not rerun,
and the old verdict is superseded
(`docs/experiments/tvb12_replay_plan.md:161-182`). It does not rewrite the raw
results.

Commit `7e6995a` changed only documentation and added the prior audit:

```powershell
git show --name-status --format='%h %s' 7e6995a
```

```text
7e6995a docs(tvb): TVB-12 review RETURNED -- audit committed, critical synthesis + remediation queue, C4 relabels applied
M  docs/HANDOFF.md
M  docs/experiments/tvb12_replay_plan.md
M  docs/reviews/REVIEW_REQUEST.md
A  docs/reviews/tvb12-codex-audit.md
```

I re-executed the prior audit's committed read-only recomputation block:

```powershell
$lines=Get-Content docs\reviews\tvb12-codex-audit.md; $code=$lines[400..578] -join "`n"; $j=($code | node -) | ConvertFrom-Json; "raw=$($j.raw.rows) failures=$((($j.raw.failures.PSObject.Properties.Value | Measure-Object -Sum).Sum)) nonces=$($j.raw.uniqueNonces) anchors=$($j.anchors.rows)/$($j.anchors.diffEqual) stored=CLEAN:$($j.comparator.stored.CLEAN),DRIFT:$($j.comparator.stored.DRIFT) bounded=CLEAN:$($j.comparator.trueCommonEnd.CLEAN),DRIFT:$($j.comparator.trueCommonEnd.DRIFT),SUSPECT:$($j.comparator.trueCommonEnd.SUSPECT) tail=$($j.comparator.removedReplayTailTrades) fingerprint=$($j.fingerprint.eligible)/$($j.fingerprint.collisionGroups)/$($j.fingerprint.differentTradeLists) coverage=$($j.coverage.comparedIds)/$($j.coverage.eligibleIds)=$($j.coverage.pct)% ceiling=$($j.named.ceiling -join '/') short=$($j.named.short -join '/') ranks=$(($j.named.ranks | ForEach-Object { $_.symbol + ':' + $_.rho }) -join ',')"
```

```text
raw=68 failures=0 nonces=68 anchors=3/3 stored=CLEAN:36,DRIFT:18 bounded=CLEAN:49,DRIFT:5,SUSPECT:0 tail=25 fingerprint=1438/241/35 coverage=54/1438=3.76% ceiling=248.7007/248.7007 short=13.7061/19/12.9115/17 ranks=HIP3XYZ:HOODUSDC.P:1,HIP3XYZ:HIMSUSDC.P:0.988,HIP3XYZ:RKLBUSDC.P:1
```

The provenance counts also reproduce:

```powershell
$files='docs\experiments\tvb11_champion_a1.jsonl','docs\experiments\tvb11_champion_a2.jsonl','docs\experiments\tvb11_champion_b.jsonl'; $all=$files | ForEach-Object { Get-Content $_ } | ForEach-Object { $_ | ConvertFrom-Json } | Where-Object accepted; $eligible=$all | Where-Object { -not $_.variant }; "accepted=$($all.Count) metrics_table_null=$(($all | Where-Object { $null -eq $_.metrics_table }).Count) eligible=$($eligible.Count) eligible_metrics_table_null=$(($eligible | Where-Object { $null -eq $_.metrics_table }).Count)"
```

```text
accepted=1498 metrics_table_null=736 eligible=1438 eligible_metrics_table_null=706
```

C4 passes without a finding.

#### Frozen winner-surface notes are accurate as diagnoses

The range adds comments only: 7/7/7/8 lines and no executable changes across
the four winner files.

- Generalizer and Champion MU15 assign the current 15m bar's high to
  `prev_ah` before testing `high >= prev_ah + tick`; on a 15m chart the test
  is impossible (`pine/winner_generalizer.pine:52-63`, `:209-211`;
  `pine/winner_champion_mu15.pine:50-61`, `:200-201`).
- Slow60 has the identical impossibility on a 60m chart
  (`pine/winner_slow60.pine:46-57`, `:68-69`).
- ShortChamp includes the final 5m child's low in `prev_al` before testing
  `low <= prev_al - tick`, so a break first occurring in that final child is
  missed (`pine/winner_shortchamp_mu5.pine:57-69`, `:218-220`).
- Each close-based indicator exit tests a live `close` throughout the final
  exit child with no `barstate.isconfirmed` guard
  (`pine/winner_generalizer.pine:203-205`;
  `pine/winner_champion_mu15.pine:196-198`;
  `pine/winner_slow60.pine:64-66`;
  `pine/winner_shortchamp_mu5.pine:210-214`). Intrabar flashes are therefore
  possible.

The header claim that the strategy record is unaffected is correct for the
arm-snapshot defect, subject to the live-gate qualification in the MEDIUM C1
finding.

The executable HTF requests on Generalizer, Champion MU15, and ShortChamp all
use the accepted confirmed offset expression plus `lookahead_on`; Slow60 has
no request:

```text
winner_generalizer.pine: [f_fractal_hi(...)[1], f_fractal_lo(...)[1], time[strength + 1]], lookahead_on
winner_champion_mu15.pine: same accepted offset pattern
winner_slow60.pine: zero executable request.security calls
winner_shortchamp_mu5.pine: same accepted offset pattern
```

I found no unoffset `lookahead_on` request in the reviewed Pine.

#### Tests and epistemic stance

The full repository suite passes with cache and bytecode writes disabled:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; uv run --no-cache pytest tests/ -q -p no:cacheprovider
```

```text
......................................ss................................ [ 96%]
...                                                                      [100%]
73 passed, 2 skipped in 1.03s
```

The session generally preserves the charter's distribution-not-winner stance
(`docs/ATLAS_Timeframe_Continuity_Charter.md:7-23`): the BF artifact is
order-free, C4 narrows rather than promotes the replay, and the give-back row
is called an acceptance fixture. The remaining epistemic risk is the
retrospective episode pinning; it must not migrate from reconstruction into
candidate validation without a pre-registered selector and broader
distribution.

### Verification limits

- I reviewed and replayed the committed source/data. I did not alter a live
  TradingView tab or independently compile the deployed Pine instance, because
  this was a read-only external review and live source injection would mutate
  external state.
- The DRAM public candles were live-verified for the declared May 30-June 15
  interval. I cannot verify private account fills, fees, funding, or the
  account narrative from public artifacts.
- The TVB-12 replay artifacts contain trades and aggregate metadata, not the
  per-bar gate/order-state trace needed to quantify the C1 live-gate edge.

## 3. Actionable items (reviewer's own list, if provided)

1. Recompute proximity anchors through HTF close and add fire-time/final-time
   geometry fixtures -- **HIGH** --
   `pine/bf_comprehension.pine:181-215`,
   `docs/design/bf_comprehension_indicator_design.md:83-98`.
2. Narrow the C1 adjudication to the completed-arm snapshot, or prove the
   broader live-gate contract with per-fill gate/order traces -- **MEDIUM** --
   `docs/HANDOFF.md:48-56`, `pine/tvb_exp_champion.pine:147-177`,
   `:313-345`.
3. Make freeze-as-of boundary-exact and apply it to L1 -- **MEDIUM** --
   `pine/bf_comprehension.pine:48-52`, `:75-86`, `:117`.
4. Permit the confirmed fire bar to create the canonical L4 restart, and pin
   faded line endpoints at supersede time -- **MEDIUM** --
   `pine/bf_comprehension.pine:169-174`, `:216-229`.
5. Label give-back outputs as gross, inclusive bar-envelope metrics; test or
   explicitly hand-label the retrospective selector -- **MEDIUM** --
   `analysis/giveback.py:9-23`, `:43-76`,
   `tests/test_giveback_fixture.py:1-35`.
6. Replace nearest-rank "median" with a conventional median and declared p90
   method -- **LOW** -- `analysis/giveback.py:80-98`.
7. Guard HTF tiling, make provisional box/label status visible, and reconcile
   the design's 4,900/no-Pine text with the shipped 2,000-candle
   implementation -- **LOW** -- `pine/bf_comprehension.pine:23-37`,
   `:115`, `docs/design/bf_comprehension_indicator_design.md:95-98`,
   `:194-195`.

## Suggested prompt (optional)

No replacement prompt proposed. The binding work order was specific enough to
separate source correctness, broker-emulator semantics, raw-data
recomputation, and claim-language review.
