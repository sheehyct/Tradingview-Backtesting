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

## Results

(appended after collection)
