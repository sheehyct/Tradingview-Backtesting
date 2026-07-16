# TVB-12 Bounded Replay -- collector-integrity + direction repair (audit F1/F2/F4)

**Status:** PLAN written 2026-07-16 pre-run; results appended below when collected.
**Motivation:** docs/reviews/tvb11-codex-audit.md (NEEDS-CHANGES) + the HANDOFF
TVB-12 critical synthesis. The TVB-11 champion-search RANKINGS are treated as
unverified until this replay passes. This is NOT a rerun of the 1,550-record
experiment and NOT a re-measurement of the BF mechanism (a paired-BF redesign is
queued separately; current-BF cells replayed here become the control arm for
that redesign's future ablation).

## What is being fixed

1. **F1 (collector):** TVB-11's settle gate accepted runs via EITHER a partial
   pine-table echo OR an engine-inputs readback with a stale-report escape
   ("changed OR 20s elapsed"). 736 accepted records carry no window evidence.
   The TVB-12 collector (scripts/tvb12_replay_collect.mjs) is FAIL-CLOSED:
   acceptance requires ALL of (a) full pine-table echo incl. a per-attempt
   NONCE + chart TF + session + BF geometry, (b) entity-bound applied-input
   readback incl. symbol/interval/subsession, and (c) report<->table totals
   equality binding the reportData to the same compute pass that echoed the
   nonce. No time escape; reject -> fresh-nonce retry (max 3) -> recorded
   rejection. Every record persists the window, the applied readback, and the
   nonce. Harness: pine/tvb_exp_champion.pine v2 ("[TVB-12r]"), whose ONLY
   changes are the nonce input (appended last; in_0..in_31 unchanged) and five
   echo rows -- trading logic identical to the TVB-11 artifact plus the
   already-committed conditional 60m BF guard (a trading no-op per the audit's
   own verification).
2. **F4 (anchors):** anchor2 re-run with actual entity readback on the BASE
   study (the TVB-11 version only set inputs and waited). The base has no nonce
   (unchanged E2 artifact); its binding is applied-readback before AND after
   settle + the equality check itself (a stale base report fails toward FALSE
   INEQUALITY, i.e. fail-safe).
3. **F2 (direction roster):** the omitted 5m short champion replays, plus NEW
   direction-repair cells (matched long/short/both and BF-off controls).

## Cell list (71 runs targeted; scripts/tvb12_replay_collect.mjs `cells`)

| Tag | What | Count |
|-----|------|-------|
| R0 | anchor2 C1/C3/C6 cross-script equivalence (hardened) | 3 |
| R1 | per-TF champions: perp tf5 SHORT / tf15 / tf60; mirror tf5/15/60 | 6 |
| R2 | ctrlA-equivalent controls (ctrlA4/state/both/BF-off), both venues x 3 TFs | 6 |
| R3 | all 10 Stage B finalist configs on HOOD/HIMS/RKLB perps + Generalizer config on ORCL/NFLX/MRVL/SILVER perps | 34 |
| R4 | direction repair: 5m short-champ config in long/both; Generalizer config in long/short/both on MU perp and short/both on all 7 roster perps; BF-off matched long/short/both control on MU perp 15m | 22 |

Windows are TODAY'S deepest loadable per (symbol, TF) -- the TV floor slid
since 07-14/15, so exact metric reproduction is NOT the criterion (that is the
same time-perishability that forced the P3 amendment).

## Acceptance criteria (pre-declared)

- **Integrity (per run):** fail-closed gate passes; window recorded. Any cell
  that cannot pass in 3 attempts is recorded as a rejection and investigated
  before the replay is called complete.
- **R0 anchors:** trade-for-trade equality champion-vs-base on the shared
  window (same gate as TVB-11 P3). Any mismatch = STOP. This also proves the
  fresh [TVB-12r] deployment behavior-identical to the E2 lineage.
- **Replay vs original (R1/R2/R3):** compare TRADE LISTS on the OVERLAP window
  (entries at/after max(original loaded_first, replay loaded_first) --
  originals lack loaded_first on engine-path records; for those the overlap
  start is the replay's window start, stated per cell). Expected: identical
  trades on the overlap except edge effects at the window boundary (warmup
  differences from the shifted floor). CONTAMINATION SIGNATURE (what F1 makes
  possible): wholesale trade-list mismatch / numbers matching a DIFFERENT cell.
  Verdict per cell: CLEAN (overlap trades match) / DRIFT (differences confined
  to window-boundary-explainable trades; quantified) / CONTAMINATED-SUSPECT
  (categorical mismatch -> locate which original cell the stale numbers belong
  to). Summary metric: count per verdict; rank order of the 10 finalists per
  symbol (Spearman vs original) reported.
- **R4 (new evidence):** no reproduction target -- results reported with the
  standing confounds (short-window 5m cells; cross-TF windows differ; SILVER
  out-of-family). NO promotion language; the question is only whether the
  all-long Stage B selection distorted the portability claim (does the
  Generalizer config's long-only advantage survive against its own
  short/both/BF-off matches on common windows?).

## What is deliberately NOT rerun

Stage A1's 1,308-cell grid, Stage A2 satellites, mirror-side Stage B, and any
BF-geometry sweep. Rationale: the replay tests the RECORD (collector truth),
not the mechanism; the paired-BF redesign (docs/design/
bf_paired_detector_design.md) owns the mechanism question and will ablate
against these replayed controls on common windows.

## Results (collected 2026-07-16, premarket; artifacts beside this file)

Collection: 3/3 anchors + 68/68 grid cells ACCEPTED through the fail-closed
gate (nonce echo + entity-bound readback + closed-side report<->table binding,
stable x2, no time escape), zero rejections, every cell on attempt 1 (~6s
settle each). Every record carries its loaded window, applied-input readback,
and nonce. Raw: tvb12_replay_anchor2.jsonl, tvb12_replay_run.jsonl; comparator
output: tvb12_replay_compare.json. Two collector defects were found and fixed
fail-loud DURING bring-up (recorded in tvb12_replay_anchor2_gatedebug.jsonl):
the harness tables never drew on live perps (barstate.islast starvation on
realtime bars -- the TVB-11 echo-flakiness ROOT CAUSE, fixed in the v2 Pine),
and the first bindOk compared tick-live open P/L to per-calc table values
(any open-trade cell was unacceptable; binding narrowed to closed-side totals).

### R0 anchors: PASS 3/3

C1/C3/C6 trade-for-trade EQUAL between the fresh [TVB-12r] v2 artifact and the
unchanged E2 engine (nets -1667.29 / +1288.95 / -715.74; counts 6/11/11 on
both), with the base study's applied inputs verified by entity readback before
AND after settle (the audit F4 gap). The redeployed harness is behaviorally
identical to the TVB-11 lineage.

### Collector-integrity verdict (F1): TVB-11 record VERIFIED on this subset

54 replayed cells had TVB-11 originals: 36 CLEAN (every overlap trade
identical), 18 DRIFT, 0 SUSPECT. No cell shows the wrong-config signature the
TVB-11 gate made possible. All 18 DRIFTs carry the window-slide signature, not
the contamination signature: matched fractions 0.89-0.999 with small uniform
deltas sweeping whole symbol blocks alike (e.g. all seven HIMS 15m finalists
shifted ~+2pp together; state-exit control cells differ by boundary trades at
~1pp; the largest, mirror 5m champion +27.7pp, sits on the fastest-sliding
1-year 5m window during a bull run with matched fraction 0.947). Headline
reproductions: perp 15m ceiling +248.70% IDENTICAL to the decimal; the 5m
SHORT champion (engine-path/no-window in TVB-11, the least-evidenced record of
the search) replays +13.7%/19tr vs +12.9%/17tr two days older -- real, not a
stale read. Stage B finalist rank order: Spearman 1.000 (HOOD), 0.988 (HIMS),
1.000 (RKLB); top-1 identical on all three.

### R4 direction repair (F2): NEW evidence, no promotion

The omitted 5m short champion is direction-SPECIFIC on its window: same config
long -8.7%/27tr, both +2.4%/46tr, short +13.7%/19tr -- the short side was the
edge, and its omission from Stage B lost real information. On the 15m
generalizer config (D/W/M gates, flip exit, BF same-side harvest + raised-stop
ratchet re-entry, arm 15m/exit 60m), direction value is SYMBOL-LOCAL in this
window, not uniformly long:

| Symbol (perp, 15m) | Long | Short | Both |
|---|---|---|---|
| MU (fit symbol) | +244.6% /32 | +0.4% /17 | +194.3% /48 |
| MU, BF off (matched control) | +228.3% /11 | -19.6% /10 | +157.9% /20 |
| HOOD | ~+19..25% (Stage B) | -17.5% /28 | +6.2% /47 |
| HIMS | ~+20% (Stage B) | -26.1% /11 | -21.5% /26 |
| MRVL | ~+17..25% (Stage B) | +8.4% /7 | +24.2% /14 |
| RKLB | +3/-2/-3% (Stage B) | +43.0% /7 | +48.0% /8 |
| ORCL | +5/3/-1% (Stage B) | +18.4% /32 | +28.0% /54 |
| NFLX | +6/1/-7% (Stage B) | +12.0% /30 | +17.5% /51 |
| SILVER | -30.0% /36 | -27.5% /34 | -57.0% /64 |

Readings (window confound applies to every line; Stage B longs quoted from the
07-14/15 windows, direction cells from today's):
- On THREE of seven roster perps (RKLB, ORCL, NFLX) the SHORT side of the
  identical config beat the long side -- exactly the symbols where Stage B's
  long-only roster scored the config weakest. The all-long Stage B did not just
  encode launch-regime bias; it flattened a per-symbol axis with real spread.
  "Best generalizer" remains a best-of-10-LONG-candidates claim.
- On MU the BF harvest rescues shorts (+20pp: -19.6 -> +0.4) and helps longs
  (+16pp) -- the harvest's value is not direction-symmetric-negative as the
  chop-loss framing assumed.
- BOTH is not LONG plus SHORT: HIMS both (-21.5) is worse than short alone
  (-26.1 vs long ~+20) because position occupancy and governor state interact.
- SILVER dies in ALL directions -- the out-of-family verdict is
  direction-robust, the cleanest kill of the batch.

### Standing verdicts after this replay

1. The TVB-11 champion-search RANKINGS stand (unverified -> verified on
   anchors, per-TF champions, controls, and Stage B finalists). The absent
   window evidence on 736 engine-path records remains a documentation gap in
   the ORIGINAL record; it no longer taints the conclusions drawn from it.
2. Audit F1/F4 remediations are CLOSED (fail-closed collector operational,
   anchors re-established). F2 is answered with new evidence: direction is a
   live per-symbol axis; any future breadth stage must carry long/short/both.
3. No promotion. Every number above is in-sample on a sliding window; the
   direction map is one window's reading of a regime-shaped quantity (the
   TVB-10/11 lesson applies to it in full).
