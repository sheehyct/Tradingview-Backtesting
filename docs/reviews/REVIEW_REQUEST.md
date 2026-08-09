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
- Session under review: TVB-21 -- TVB-20 audit fold-in (all four findings
  reproduced before adjudication: parity-gate injective-join hardening,
  harvester run/inventory provenance split, C0/C1/C2 contrast ladder,
  port-wording scope block); THE design session (user-ruled: pine-exact
  dictionary, 1H signal TF, contrast set, veto semantics/values, exit
  substitution); Tier B pre-registered BEFORE code, then built
  (analysis/paper/patterns.py pine-exact M+T port, engine extensions
  behind inert defaults, tier_b.py runner) and executed (5 arms x 11
  symbols) with the report's churn-mechanism autopsy.
- SCOPE: standard.
- Requested: 2026-08-09
- Write the audit to: `docs/reviews/tvb21-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: tvb8/tvb9 remain unreturned (standing note).

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `f90d0c9^..1cd6b0c` (4 commits: f90d0c9 TVB-20 audit fold-in; 94090e9 Tier B pre-registration; 163323b Tier B build + run + report; 1cd6b0c session-end docs; sanity-checked -- `git diff --name-status f90d0c9^..1cd6b0c` lists all 23 files the session touched) |

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0, then the S3.1 amendments (both 2026-08-08
   blocks -- the second is this session's audit-F3 fold-in).
2. `docs/HANDOFF.md` -- the TVB-21 entry at top; the TVB-20 entry's External
   Review block (the fold-in synthesis adjudicated there).
3. `docs/experiments/tvb21_tier_b_prereg.md` (declared 94090e9, before code)
   and `docs/experiments/tvb21_tier_b_report.md` (the autopsy).
4. `docs/reviews/tvb20-codex-audit.md` (the audit whose fold-in opens the
   range).
5. `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Focus areas (scrutinize these)

1. Fold-in fidelity: every TVB-20 finding addressed or explicitly deferred
   with reasons; the hardened gate's false-pass fixtures actually pin the
   reproduced failures (tests/test_port_parity.py); the committed parity
   artifact was deliberately NOT regenerated -- verify values unchanged.
2. patterns.py pine-exactness vs pine/strat_magnitude_targets_plus.pine:
   else-if chain order, `>= thr` subtraction-form break flags, warm-up
   guards, hammer/shooter rule, ladder walk (anchor/anchor2 seeding, strict
   monotone, maxLevels, 250-bar cap), the color gates -- and the PMG+
   unreachability claim (streak walk seeded at the developing bar).
3. Engine default-path invariance: entry_mode="arm" must leave every
   pre-existing path bit-identical. Evidence to check: the full suite, the
   committed-GOOGL port-parity pin, and the manifest's A0 determinism check
   (both control arms vs committed Tier A rows, all shared fields).
4. Pre-reg-vs-execution fidelity in analysis/paper/tier_b.py: the five
   arms' configs, veto math vs the prospective FILL price, the bar-open
   alive-set snapshot ordering, frozen-at-entry target semantics (rung-2
   fallback), the conservative fill convention (max(trig+tick, open)), and
   the no-target structural skip (a post-declaration pre-run
   clarification -- flag if you think it needed a prereg amendment).
5. The report's arithmetic: born-beyond-T1 splits (A2 244/413 = -310.1pp vs
   +88.1pp; A3 159/263), one-bar-exit and chain counts, the 54.2pp A1 fill
   drag, veto-rate table -- all from post-hoc deterministic replays;
   reproduce independently.
6. Contrast-language discipline: S3.1 conclusions constrained to A1-vs-A0b;
   package results never adjudicate S3.1; no arm/cell/pattern promoted
   anywhere (report, commits, HANDOFF).
7. request.security lookahead: no executable Pine changed this session
   (tfc_bf_control_strategy.pine header comments only) -- confirm no
   lookahead anywhere in the range.

Standing priorities apply (model fidelity; overfitting language; controls
are research instruments, never deployment claims).

## Output contract

- Verbatim audit -> `docs/reviews/tvb21-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value.
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
