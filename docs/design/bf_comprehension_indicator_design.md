# BF Comprehension Indicator -- Design (TVB-13)

> Status: DESIGN for user review. The artifact is an order-free `indicator()`
> ONLY -- no strategy logic, no exits, nothing feeds orders. Purpose: prove
> the scenario-3 / broadening-formation / compound-3 principle is understood
> BEFORE the exit detector is designed, by reproducing the user's hand-drawn
> fixture lines on the chart. This precedes and feeds the exit-ablation
> design session; it decides nothing about the ablation itself.
>
> Companion doc: docs/design/bf_paired_detector_design.md (worktree branch
> worktree-agent-aba898ce6f7f356c9, UNMERGED) -- its D/OQ numbering is
> referenced below where relevant. This doc narrows scope; it does not
> supersede that one.
>
> Skill basis: strat-methodology v3 invoked 2026-07-17 (Sections 1, 2, 3.2,
> 5.1). Sources re-read same day: the cheat sheet
> (temporary/tvb13_fixture_screens/a41883e8-9767.jpg) and "The Broadening
> Formation Algorithm" (theStrat Lab, temporary/, gitignored).

---

## 1. Decisions locked with the user (2026-07-17)

- **D-A Compound-3 window semantics: build BOTH as toggles.** The user cannot
  pre-decide from description ("this is something I have learned to see, not
  quite code yet ... we might have to just try both"). Modes:
  - `aggregate`: real scenario 3s detected on actual HTF bars (the anchored
    aggregate-candle reading of a compound 3);
  - `rolling`: a chart-TF bar/cluster strictly outside ALL bars of a rolling
    N-bar window (fires the instant the second side strictly breaks).
  The fixture decides which mode matches the hand-drawn lines. This resolves
  the paired-doc's OQ-1 for the comprehension artifact by refusing to choose.
- **D-B Timeframe floor and precedence.** No BF line is drawn from any
  timeframe below 60m. The ladder above the floor carries HTF PRECEDENCE:
  higher-TF lines have more weight / higher reversal likelihood when price
  touches them. Comprehension-surface encoding: visual only (line thickness /
  opacity increase with TF). Any order-logic meaning of precedence (rung
  policy) stays reserved for the exit-ablation pre-reg.
- **D-C Parallelism.** The MFE/MAE/give-back leak quantification is a
  separate thread and proceeds in parallel; nothing here blocks on it.
- **D-D Acceptance = the user's own hand.** On the DRAM June fixture the
  DAILY line and the 12H line (the 52.79 bottom-wick catch) must be
  reproduced essentially to the tick. The 11 screenshots in
  temporary/tvb13_fixture_screens/ are the grading set. The LIVE July short
  window is the second surface.

Proposed defaults (user veto at review; a-priori, never tuned on results):

- TF ladder: {60m, 4h, 12h, D, W}; default-visible {12h, D} (the two rungs
  the user demonstrated), the rest toggleable.
- Build/verify surface: the DRAM 15m live-watch layout.
- Rolling-mode default windows: N chosen to SPAN the same wall-clock as each
  aggregate rung (e.g. 48 x 15m = 12h) so the two modes are directly
  comparable rung-for-rung.

## 2. Geometry under test (CORRECTED by the user, 2026-07-17)

The user corrected the draft-1 single-geometry read-back. The line is NEVER
drawn 3-to-previous-3. There are TWO valid drawing modes, demonstrated on an
ES 12h example (12h is illustrative, NOT a definitive timeframe; screenshots
preserved as temporary/tvb13_fixture_screens/es12h_line_mode1_adjacent.png
and es12h_line_mode2_compound.png). Both modes are per-rung toggles -- the
same try-both stance as D-A. All described for the SHORT (lows) side; mirror
with HIGHS for longs.

- **LINE MODE 1 -- adjacent (the easy way).** Connect the LOW of the bar
  immediately preceding the scenario 3 to the 3's own LOW; extend forward.
  ES example: inside bar's low (~7590) -> the 3's low (7578); the steeper
  line.
- **LINE MODE 2 -- compound take-out ("take out the highs, take out the
  lows").** The 3 completes a COMPOUND scenario 3: it strictly took out not
  only the previous bar's low but a slightly LOWER low one bar further back.
  The line anchors at that deeper taken-out low instead. ES example: the
  low-side run is two bars deep (inside bar ~7590, prior green bar ~7585),
  so the lower line runs ~7585 -> 7578 -- the shallower line -- while the
  upper line is UNCHANGED from mode 1 because the high-side run is only one
  bar deep. Conceptually the taken-out run plus the 3 aggregate into a
  single scenario-3 candle (the cheat sheet's fractality premise: "3 12-hour
  bars that together would form a single scenario 3 candle").

Proposed mechanization of mode 2 (Claude's formalization of the drawings --
CONFIRM WITH USER before code): per side, walk back from the 3 through the
maximal consecutive run of bars whose side-extreme the 3 strictly took out;
the anchor = that run's most extreme value. The two sides are anchored
INDEPENDENTLY (their run depths differ, as in the ES example). Mode 2
degenerates to mode 1 on any side where the immediately-previous bar is the
local extreme. Open sub-question: is the walk-back uncapped or bounded by an
a-priori lookback?

Classification is strict throughout (R10): H > pH AND L < pL; equality never
breaks anything, including window extremes in rolling mode.

A BF is two structural lines through ACTUAL bar extremes -- lower lows
connected and higher highs connected. It is never an envelope or band; no
smoothing, no derived series, only real wicks.

## 3. Layers

- **L1 Bar grounding.** Chart-TF 1/2U/2D/3 marks via the canonical strict
  operators, with 3s distinguished by fire timing: which side broke first
  and where the second side's break (the instant the bar became a 3)
  occurred. Live intrabar classification, monotonic, never close-painted.
- **L2 Fractality view.** For each ladder TF, shade the chart-TF span of
  every HTF bar that classifies as a 3. This is the cheat sheet's universal
  truth made visible: an HTF outside bar IS an LTF broadening structure.
  Decision-free demonstration layer.
- **L3 Compound-3 birth + the exit line.** Per detection mode (D-A), per
  line mode (Section 2), and per ladder rung: fire a marker the instant the
  second side of the reference range strictly breaks, and at that instant
  draw the Section 2 geometry. Both sides drawn whenever both exist (lows
  line and highs line), each side anchored independently per its own
  take-out depth. HTF precedence via visual weight (D-B).
- **L4 Restart and reclaims.** When price trades back inside a previous
  range, the formation RE-STARTS; mark reclaim levels at the prior range
  extremes. Semantics from the cheat sheet: "if we fail the highs we target
  the lows" -- the magnitude gauge; shown as levels only, no order meaning.

## 4. Live-draw semantics and repaint honesty

Because nothing feeds orders, live provisional drawing is allowed and
LABELED: any element derived from a not-yet-closed bar is marked PROVISIONAL
until its bar closes. This dissolves the paired-doc's OQ-6 (closed-only vs
live) for the comprehension artifact ONLY; the backtest detector's contract
remains a design-session question.

`request.security` discipline: closed HTF series use the accepted
confirmed-bar idiom (`expr[1]` + lookahead_on, per the pending F7 rule
amendment); the CURRENT HTF bar's running extremes are computed from chart-TF
running max/min inside the current HTF period, never from a lookahead call.

## 5. Acceptance protocol

1. Deploy on the DRAM 15m layout (Make-a-copy flow; verify the version bump;
   memory tv-mcp-pine-tab-binding-trap applies).
2. Scroll to the June fixture window; enable the 12h + D rungs.
3. Screenshot per mode (aggregate vs rolling), side-by-side against the
   hand-drawn screenshots; the user grades each rung.
4. Every divergence is recorded as a numbered design-session question --
   divergences are the deliverable, not a failure.
5. Repeat on the LIVE July short window.

## 6. Out of scope

Exit logic, ablation arms, zones-as-order-logic, adaptive (ROC-of-ATR) pivot
length, reclaim-break exits, any strategy() port, any change to deployed
winner indicators. The article's fractal-pivot variant MAY be added later as
a comparison layer on the same surface -- second iteration, only if the user
wants it.

---

Version: draft 1 (TVB-13, 2026-07-17). No Pine exists for this design yet;
build starts after user sign-off on Sections 1-2.
