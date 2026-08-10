# CURRENT REVIEW REQUEST -- tradingview-backtesting

> Entry point for external reviewers. If you are Codex (`/session-review`) or any other
> external review agent pointed at this repo: this file is your work order. It
> always describes the LATEST requested session review and is rewritten by
> `/session-end` each session. The permanent per-session record is the
> `### External Review` block in `docs/HANDOFF.md`; for the CURRENT request,
> this file wins if the two disagree. Full contract:
> `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Status

- Status: REQUESTED
  <!-- REQUESTED | RETURNED (audit file written) -->
- Session under review: TVB-22 -- TV package strategy() port (M+T
  detection/ladder merged into the control machinery, arm toggles
  A1/A2/A3, Make-a-copy flow, compiled + round-trip-verified) with its own
  parity harness and gate (9/9 cells PASS, 487 events, zero mismatches,
  pattern layer clean); the TVB-21 Codex audit RETURNED mid-session and
  FOLDED (F1 HIGH reproduced to the decimal, three user rulings, dated
  prereg amendment BEFORE code, engine containment fix + 4 fixtures,
  source-bound manifests, full Tier B rerun regenerated in place with
  fix-isolation invariants); mechanism decomposition (born-beyond +
  tiny-target classes; A1 ladder census) + next-variant seed.
- SCOPE: standard.
- Requested: 2026-08-10
- Write the audit to: `docs/reviews/tvb22-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: tvb8/tvb9 remain unreturned (standing note).

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `{pending push -- pinned after session-end push}` |

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0 (S3.1 amendments unchanged this session).
2. `docs/HANDOFF.md` -- the TVB-22 entry at top (incl. the TVB-21 audit
   synthesis inside the TVB-21 entry's External Review block).
3. `docs/reviews/tvb21-codex-audit.md` (the audit folded this session) and
   `docs/experiments/tvb21_tier_b_prereg.md` (its 2026-08-09 amendment).
4. `docs/experiments/tvb22_tier_b_rerun_report.md` (the ruled-contract
   rerun) and `docs/experiments/tvb22_next_variant_seed.md` (nothing in it
   is declared).
5. `pine/tfc_mt_package_strategy.pine` header (hunks H1-H7) and
   `analysis/paper/pkg_parity.py` docstring.
6. `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Focus areas (scrutinize these)

1. Fold-in fidelity: every TVB-21 finding reproduced/fixed or explicitly
   deferred; the amendment wording matches the three user rulings
   (containment touch incl. gap-past; skip-with-vetoes-first +
   no_target_vetoed; gate-after-fix); the invalidation notice preserves
   the original report text.
2. The containment fix (engine.py: `l <= tgt <= h` both directions) and
   the four new fixtures (born-beyond long/short, favorable gap-past,
   counter reconciliation) -- do they pin the audited failure classes.
3. Rerun integrity: fix-isolation invariants (A0a/A0b/A1 per-symbol rows
   byte-equal to the invalidated run modulo the zero-valued
   no_target_vetoed key), A0 determinism vs committed Tier A cells,
   in-place regeneration provenance (manifest executed-blob hashes;
   git_dirty=true explained as output-files-only), and the rerun report's
   arithmetic (reproduce the class splits independently).
4. The Pine merge: declared hunks H1-H7 vs the two verbatim sources --
   especially H7's decision-identical claim (lazy PMG/ladder guards) and
   whether the f_pool veto scan (top-of-function, pre-detection,
   pre-lifecycle) equals engine._alive_harvest_vals' bar-open alive-set
   semantics.
5. pkg_parity.py: injective join + fail-closed contract carried over
   intact; `tgt` correctly in the declared-residual layer; the pattern
   layer (name exact, trig within mintick/2) as a gate-failing check;
   cold-start twin alignment to the harvested first_bar_ts; the harvest
   script's direction-from-e.tp mapping.
6. Language discipline: no arm/depth/pattern promoted anywhere (rerun
   report, twin trade tables, seed); package results never adjudicate
   charter S3.1.
7. request.security: the new pine has NONE and no executable Pine changed
   except the two package-strategy files -- confirm across the range.

Standing priorities apply (model fidelity; overfitting language; controls
are research instruments, never deployment claims).

## Output contract

- Verbatim audit -> `docs/reviews/tvb22-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value.
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
