<!--
External review of a TVB session. See docs/EXTERNAL_REVIEW_PROTOCOL.md.
The verbatim audit goes in section 2; the CRITICAL SYNTHESIS goes in docs/HANDOFF.md, not here.
-->

# TVB-14 External Audit -- Codex CLI (verbatim source, read CRITICALLY)

> External review of `b324f80^..129336a` on `main`, captured 2026-07-20
> (TVB-14 post-session). Lightly ASCII-normalized (em-dashes -> --, curly quotes -> straight);
> wording and code otherwise unchanged.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-14 -- TFC-BF v4->v6 rolling compound-3 pools and three exit classes
- **Reviewed:** `b324f80^..129336a` on `main`
- **Reviewer:** Codex CLI
- **Overall verdict:** NEEDS-CHANGES

## 2. Verbatim audit

### Scope and reproduction

- `git diff --name-status b324f80^ 129336a` returned the seven expected session files. The tree was clean before review.
- `uv run pytest tests/ -q` initially hit a host uv-cache initialization collision before pytest started. With `UV_CACHE_DIR` redirected to temporary storage, the same command completed: **95 passed, 2 skipped**.
- The required fixture runs completed:
  - `12h`: 54 formations
  - `D`: 27 formations
  - `W`: 2 formations
- The committed 1h reference has 1,826 contiguous hourly bars and valid OHLC. Its 75 complete UTC days reproduce the committed 1d OHLC exactly. The fixture reads only the 1h file (`analysis/tvb14_bf_pool_fixture.py:38-39`); the 1d file is an independent provenance cross-check, not a fixture input.
- A read-only live-chart check found the DRAM 5m v6 instance. Its table identified v6, and its drawn weekly anchors rounded to `55.00->52.79`, `67.42->67.18`, and `52.79->48.66`. Independently closing the partial final reference week conditionally at the Jul-20 roll yields smallest `N=4` and a lower-line birth value of `48.4184`; that is within one cent of the HANDOFF's claimed live `48.414` (`docs/HANDOFF.md:29-33`). The live drawing therefore supports the specific weekly penny-level claim.

### F1 -- HIGH -- Supersede-before-ghost ordering deletes an unchanged, still-valid side

- **Severity:** HIGH
- **Location:** `pine/tfc_bf_watch.pine:227-264`; mirrored by `analysis/tvb14_bf_pool_fixture.py:95-105`
- **Status:** CONFIRMED

**Concrete failure scenario:** Formation A has an alive lower and upper side. The next qualifying formation has the same left anchors, a re-anchored lower side, and an upper side identical to A. A long entered below that upper line should still harvest when price later touches it. Instead, the old upper is marked superseded and the replacement upper is marked ghost, so neither side has state `0`; the touch scan at `pine/tfc_bf_watch.pine:332-347` cannot emit `xl_v`, and the BF long exit is missed.

**Evidence:** The implementation retires both old sides before it decides whether either replacement side is an exact duplicate:

```pine
if not identical and array.get(p_lo_t1, li) == bLt and array.get(p_lo_v1, li) == bLm and array.get(p_up_t1, li) == bHt and array.get(p_up_v1, li) == bHm
    if array.get(p_lo_st, li) == 0
        array.set(p_lo_st, li, 3)
    if array.get(p_up_st, li) == 0
        array.set(p_up_st, li, 3)
...
if array.get(p_up_t1, i) == bHt and array.get(p_up_v1, i) == bHm and array.get(p_up_t2, i) == aHt and array.get(p_up_v2, i) == aHm
    up_ghost := true
...
array.push(p_up_st, up_ghost ? 4 : 0)
```

That exact case occurs in the committed daily replay: the formation born Jun-23 has an alive upper side; the Jun-24 formation changes the lower right anchor but preserves the upper line exactly. The first upper becomes `superseded`; the second becomes `ghost`. The live drawing read also showed that anchor pair only as a faded dashed line, with no solid replacement. This is not merely a fixture artifact.

The same block checks only `li = sz - 1` (`pine/tfc_bf_watch.pine:227-233`). If a smaller-N formation intervenes before an older same-left structure re-anchors, the older structure is not superseded at all. The immediate committed case above is sufficient to prove the HIGH failure; the last-only search is a second structural weakness in the same rule.

### F2 -- HIGH -- The default cap silently evicts alive lines, while the acceptance fixture omits the cap

- **Severity:** HIGH
- **Location:** `pine/tfc_bf_watch.pine:94,265-284`; `analysis/tvb14_bf_pool_fixture.py:59-113`; claim at `pine/tfc_bf_watch.pine:28-35`
- **Status:** CONFIRMED

**Concrete failure scenario:** An old structural line remains alive, then the thirteenth newer formation is born in that pool. The cap deletes the oldest line and shifts its record regardless of state. A later eligible position touches the deleted line, but the pool no longer contains it, so no BF exit occurs.

**Evidence:** The 13 parallel arrays are shifted in lockstep; that mechanical part is correct. The selection policy is not lifecycle-aware:

```pine
pool_cap = input.int(12, 'Max formations kept per pool', minval = 3, maxval = 30, group = grp_x)
...
if array.size(p_N) > pool_cap
    line d1 = array.get(p_lo_ln, 0)
    line d2 = array.get(p_up_ln, 0)
    if not na(d1)
        line.delete(d1)
    if not na(d2)
        line.delete(d2)
    array.shift(p_N)
    ...
    array.shift(p_up_ln)
```

The fixture has no `pool_cap` equivalent; it returns every formation:

```python
def run_pool(key_fn, period_s):
    ...
    formations = []
    ...
    return formations
```

A chronological replay of the Pine policy over the committed bars produced:

- 12h: 54 births, 42 evictions; 22 evicted records still had at least one alive side at eviction.
- D: 27 births, 15 evictions; 6 evicted records still had at least one alive side at eviction.

This directly contradicts the header's wording that the filter "collapses the naive 12h pool from 57 formations to the handful" (`pine/tfc_bf_watch.pine:32-35`): the required fixture prints 54 formations. It also breaks fixture-to-deployment parity. For example, the fixture keeps the daily lines projected near `41.45` and `38.78` alive at the final committed hour; those are the claimed `41.4` and `38.8` ladder rungs, but they are older than the final 12 daily formations and are therefore absent under the Pine cap on the same reference sequence.

Eviction needs either an explicit lifecycle state or a policy that removes retired records before alive ones. As written, "alive" does not mean the engine will retain the line until consumed, crossed, or superseded, despite the lifecycle claim at `pine/tfc_bf_watch.pine:45-48`.

### F3 -- MEDIUM -- The "acceptance fixture" is a print-only, two-phase approximation, not a parity oracle

- **Severity:** MEDIUM
- **Location:** `analysis/tvb14_bf_pool_fixture.py:14-25,59-113,121-151`
- **Status:** CONFIRMED

**Concrete failure scenario:** A line is consumed between its birth and a later same-left re-anchor. Pine processes the touch before the later formation, so its state remains consumed because supersession only changes state `0`. The fixture detects and supersedes all formations first, while every line still appears alive, and only afterward replays touches. It reports the line as superseded and masks the real transition.

**Evidence:** Formation generation finishes before lifecycle replay:

```python
formations = run_pool(KEYS[tf], PERIOD_S[tf])

for f in formations:
    for ts, o, h, l, c in bars:
        ...
        if f["lo_state"] == "alive":
            if l <= lv <= h:
                f["lo_state"] = f"consumed {ds(ts)}"
```

On the committed 12h data, a chronological replay disagrees on two concrete lower sides: fixture F23 and F39 print `superseded`, while both had already been consumed before the later re-anchor and Pine leaves them consumed. The runner also contains no assertions; the expected values live only in the docstring and every result is printed (`analysis/tvb14_bf_pool_fixture.py:14-25,142-151`). A wrong window, state, or anchor can therefore still exit zero.

The weekly command does not print the documented F3 because the 1h reference ends before the next weekly key and `run_pool()` does not flush the final partial period. The F3 value can be recomputed conditionally, as done above, but the committed "acceptance fixture" does not itself accept or reject that claim.

### F4 -- MEDIUM -- "Exact when the chart TF tiles" overstates geometry, and non-tiling lower TFs run silently

- **Severity:** MEDIUM
- **Location:** `pine/tfc_bf_watch.pine:51-53,70-72,184-185,285-296`; `analysis/tvb14_bf_pool_fixture.py:23-25,38-39,107-112`
- **Status:** CONFIRMED

**Concrete failure scenario A:** Put the indicator on a 7m chart. Seven minutes is below 12h, so the pool is active, but 7m does not tile 12h. A chart bar that straddles a 12h boundary is assigned wholly to one base period; its high/low can move the wrong envelope, producing a wrong formation and exit line.

**Concrete failure scenario B:** The same true wick occurs at 10:35. A 5m chart stores anchor time 10:35; the 1h fixture stores 10:00. Both chart TFs tile D/W/M, and the base OHLC extrema can be exact, but projected line value and a near-boundary `min_sep` decision can differ because the slope uses those timestamps.

**Evidence:** The only runtime gate is "lower than," not divisibility:

```pine
bool active = en and timeframe.in_seconds(tf) > timeframe.in_seconds()
...
cur_hiT := time
...
cur_loT := time
```

The header says:

```pine
//   - Chart-side aggregation: exact when the chart TF tiles the base TF
```

That is defensible only for base-period OHLC aggregation. Wick-time line geometry is chart-resolution-quantized by `time`, and the fixture explicitly supplies 1h timestamps. Its caveat mentions only touch/cross timing differences, not changed anchor geometry (`analysis/tvb14_bf_pool_fixture.py:23-25`). The live weekly pairs happened to match to the cent; that successful sample does not make the general exactness claim true.

The script should reject or visibly warn on non-tiling TFs, and the docs should distinguish exact envelope values from resolution-dependent wick timestamps and projections.

### F5 -- MEDIUM -- The `min_sep=1.0` form has a structural rationale; the numeric default is sample-side

- **Severity:** MEDIUM
- **Location:** `pine/tfc_bf_watch.pine:28-35,67-69,93,185,243-244`; `analysis/tvb14_bf_pool_fixture.py:36-38`; `docs/HANDOFF.md:34-41,53-58`; charter rule at `docs/ATLAS_Timeframe_Continuity_Charter.md:31-34,142-143`
- **Status:** CONFIRMED

**Concrete failure scenario:** A future instrument has a user-valid structural pair whose wick anchors are 0.75 base periods apart. The fixed 1.0 cutoff ghosts it, not because a structural derivation says 0.75 is invalid, but because the observed labeled examples used to select the default had junk below 0.5 and good pairs beginning at 1.25. The exit rung disappears out of sample.

**Evidence:** The script states the empirical separator and then calls the chosen value a priori:

```pine
//   - min_sep is the one new a-priori parameter (default 1.0 periods,
//     from the user's validated examples: good pairs 1.25-54 periods
//     apart, junk pairs < 0.5). Dial, do not tune on backtests.
min_sep = input.float(1.0, 'Min anchor separation (periods)', ...)
```

The same DRAM reference is then graded with `MIN_SEP = 1.0` (`analysis/tvb14_bf_pool_fixture.py:36-38`), and HANDOFF judges success by reproduction of the DRAM ladder (`docs/HANDOFF.md:34-41`). There is no pre-selection artifact or out-of-sample instrument set in the reviewed range.

Under the charter's own gradient, the **filter form and direction** are structural: near-coincident anchors create extreme slopes. The **1.0 threshold** is sample-derived: it was chosen inside an observed `0.5..1.25` separation gap and graded on the same example family. The charter explicitly distinguishes a mechanism from its still-free threshold (`docs/ATLAS_Timeframe_Continuity_Charter.md:142-143`). "Dial from live watching" is still sample selection unless the dialing rule and evaluation window are fixed in advance.

The honest label is "provisional example-derived default," not "a-priori parameter," until it is frozen before a separate holdout.

### F6 -- LOW -- The pinned range contains four commits, not five

- **Severity:** LOW
- **Location:** `docs/reviews/REVIEW_REQUEST.md:26-30`
- **Status:** CONFIRMED

**Concrete failure scenario:** A reviewer treats the declared count as a completeness invariant, cannot reconcile the fifth commit, and either expands scope or assumes a commit is missing even though the SHA endpoints are correct.

**Evidence:** The work order says:

```markdown
`b324f80^..129336a` (5 commits: b324f80 = v4; 915e678 = v5; bd09895 = v6; 129336a = session-end docs)
```

`git rev-list --count b324f80^..129336a` returns `4`, and the text itself names four commits. The range and seven-file diff are otherwise coherent.

### Confirmed checks that are not findings

- **Rolling windows / smallest-N:** `cnt-n..cnt-1` is the current envelope and `cnt-2n..cnt-n-1` is the prior envelope (`pine/tfc_bf_watch.pine:198-226`). `found` makes the first qualifying N win.
- **Parallel-array lockstep:** `p_N` plus six lower-side and six upper-side arrays are pushed and shifted together (`pine/tfc_bf_watch.pine:171-183,252-284`). F2 concerns which record is evicted, not array desynchronization.
- **Four call-site states:** The four written `f_pool()` calls are separate scopes (`pine/tfc_bf_watch.pine:357-360`). TradingView's current documentation says each written user-function call creates unique variables with independent history: [User-defined function call scopes](https://www.tradingview.com/pine-script-docs/language/user-defined-functions/#scope-of-a-function-call). The cross-instance leakage claim is therefore grounded as **CONFIRMED absent**.
- **Prior-bar position inputs:** All four pool calls occur before the position machine (`pine/tfc_bf_watch.pine:353-360,432-473`), so `_pos` and `_entry` see the standing state entering the bar. The documented entry+touch non-exit follows from that order.
- **Exit race:** Harvest clears `pos` before break; break clears it before flip (`pine/tfc_bf_watch.pine:438-461`). The stated harvest -> break -> flip priority is implemented. Direction-relative harvest eligibility is also correct at `pine/tfc_bf_watch.pine:317-319,336-338`.
- **Historical confirmation:** TradingView documents `barstate.isconfirmed` as true on all historical bars and on the closing realtime update: [Bar states](https://www.tradingview.com/pine-script-docs/concepts/bar-states/#barstateisconfirmed). The source's confirmed-close checks at `pine/tfc_bf_watch.pine:324-350,454-461` match that behavior.
- **Any-touch lifecycle:** `if touched` changes state without checking position (`pine/tfc_bf_watch.pine:313-350`), so flat and wrong-side touches consume lines exactly as disclosed. This is consequential for rung availability but not hidden.
- **No `request.security`:** A literal search found only the header sentence at `pine/tfc_bf_watch.pine:71`; there is no executable `request.security` call.
- **Drawing resources:** At the maximum input cap, four pools retain at most 240 side records, below the declared 500-line ceiling (`pine/tfc_bf_watch.pine:76,94`). TradingView documents a maximum of 500 line/label IDs and automatic drawing limits: [Pine limits](https://www.tradingview.com/pine-script-docs/writing/limitations/#line-box-polyline-and-label-limits). No resource-cap failure was found.
- **UNVERIFIED:** Monthly fixture parity. The acceptance runner exposes only `12h`, `D`, and `W` (`analysis/tvb14_bf_pool_fixture.py:23,48-52,121-123`), and the live table had no alive M side to compare. I do not assert monthly alignment or anchor parity from the available evidence.

## 3. Actionable items

1. Preserve an unchanged side across a same-left re-anchor; determine duplicate/ghost state per side before retiring its predecessor, and test one-side-unchanged cases -- **HIGH** -- `pine/tfc_bf_watch.pine:227-264`.
2. Make cap eviction lifecycle-aware (retired first, or explicit user-ratified alive eviction), then apply the identical cap chronologically in the fixture -- **HIGH** -- `pine/tfc_bf_watch.pine:265-284`; `analysis/tvb14_bf_pool_fixture.py:59-113`.
3. Interleave formation, lifecycle, and cap operations in the fixture and add executable assertions for states and penny-level anchors, including conditional/final-period handling -- **MEDIUM** -- `analysis/tvb14_bf_pool_fixture.py:59-151`.
4. Enforce chart-TF tiling or issue a visible warning; narrow "exact" to base OHLC and document chart-resolution-dependent anchor geometry -- **MEDIUM** -- `pine/tfc_bf_watch.pine:51-53,70-72,184-185,285-296`.
5. Relabel `min_sep=1.0` as provisional/sample-derived and freeze it before a separate holdout if it is to earn an a-priori claim -- **MEDIUM** -- `pine/tfc_bf_watch.pine:67-69,93`; `docs/HANDOFF.md:34-41`.
6. Correct the commit count from five to four when the request is returned -- **LOW** -- `docs/reviews/REVIEW_REQUEST.md:30`.

## Suggested prompt

Add: "Replay birth, lifecycle, and deployed `pool_cap` in one chronological trace. List every alive-side eviction. Force same-left re-anchors where exactly one side is unchanged, both consecutively and with an intervening smaller-N formation; fail the review if a valid side has neither an alive predecessor nor an alive replacement."

Verdict: NEEDS-CHANGES
