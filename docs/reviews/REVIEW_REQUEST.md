# CURRENT REVIEW REQUEST -- tradingview-backtesting

> Entry point for external reviewers. If you are Codex (`/session-review`) or any other
> external review agent pointed at this repo: this file is your work order. It
> always describes the LATEST requested session review and is rewritten by
> `/session-end` each session. The permanent per-session record is the
> `### External Review` block in `docs/HANDOFF.md`; for the CURRENT request,
> this file wins if the two disagree. Full contract:
> `docs/EXTERNAL_REVIEW_PROTOCOL.md`.

## Status

- Status: REQUESTED  <!-- REQUESTED | RETURNED (audit file written) -->
- Session under review: TVB-11 -- BF-deviation exit experiments (E0/E1/E2) +
  GPT blind replication; the pre-registered CHAMPION SEARCH executed
  end-to-end (harness, collector, Stages A1/A2/B, results Section 12);
  three minimal winner indicators shipped; closedtrades.profit()
  calibrated-fact correction (NET, superseding TVB-7's GROSS)
- Requested: 2026-07-15
- Write the audit to: `docs/reviews/tvb11-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: the TVB-8 (`b4bab2c^..db203aa`) and TVB-9 (`f192a14^..5edd5b6`)
  requests were never returned; their records live in their HANDOFF blocks.
  Reviewing them alongside this range is welcome but not required.

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | {pending push -- pinned after session-end push; ticket range is `0561c53^..HEAD`, 29+ commits: review fold-in, companion v5, BF E0/E1/E2, GPT reports, champion pre-reg/harness/collector/stages/results, winner indicators, session-end docs} |

No sibling-repo changes this session.

RANGE-PIN RULE (Codex TVB-4 finding 1): git ranges EXCLUDE the left endpoint;
pin `{first}^..{head}` (the caret keeps the first session commit inside the
reviewed diff). Sanity-check with `git diff --name-status <range>`.

## Read first (in this order)

1. `CLAUDE.md` -- epistemic stance + backtest traps (Sections 2, 6).
2. `docs/ATLAS_Timeframe_Continuity_Charter.md` -- Section 0 + Section 5.
3. `docs/HANDOFF.md` -- the TVB-11 entry at the top (what was done and why).
4. `docs/experiments/tvb11_champion_prereg.md` -- the pre-registration, its
   amendment log, and the RESULTS (Section 12). This is the record under
   review. The raw run JSONLs and cell lists sit beside it.
5. `docs/EXTERNAL_REVIEW_PROTOCOL.md` -- the reviewer contract.

## Scope / what changed

(a) BF-exit experiment arc E0/E1/E2 + GPT blind-replication reports
(committed verbatim). (b) `pine/tvb_exp_champion.pine`: champion harness --
ratchet_c/ratchet_g re-entry variants (both adjudicated from source),
session-robust period clocks (time_close == time_close(tf)), machine-readable
collector echo incl. the profit() polarity probe. (c)
`scripts/tvb11_champion_collect.mjs`: direct-CDP batch collector
(echo-first/engine-fallback settle gate, load-to-floor history, RTH-mirror
session forcing, checkpoint/resume). (d) Grid stages A1 (1308 cells, MU
perp + NASDAQ:MU RTH mirror), A2 (60 satellites), B (130/140 roster breadth);
all raw records committed. (e) Results written into the pre-reg Section 12;
scorecard honest (2 expectations refuted). (f) Three minimal winner
indicators (pine/winner_*.pine) deployed. (g) TVB-7 calibrated fact
CORRECTED: closedtrades.profit() is NET of commission.

## Focus areas (scrutinize these)

1. **Collector integrity** (`scripts/tvb11_champion_collect.mjs`): is the
   echo-first/engine-fallback settle gate sufficient against stale reads
   (esp. the engine path's "report changed OR 20s elapsed" acceptance)? Any
   way a wrong-config result could be accepted?
2. **P3 anchor redesign**: original "reproduce E2 numbers" was replaced
   (data floor slid past May 1; monthly-open warmup) with cross-script
   trade-for-trade equivalence on a shared window. Is the replacement
   actually stronger? Is the amendment record honest?
3. **Results discipline** (pre-reg Section 12): window confounds (per-TF and
   perp-vs-mirror loaded depths differ) stated wherever numbers are
   compared? Any sentence promoting the champion beyond ruler status?
4. **profit() NET verdict**: per-trade arithmetic (anchor.jsonl C3 record);
   propagation correctness -- TVB-7 memory correction, "governor classifies
   net everywhere in the Claude lineage" claim, VBT-port parity flag.
5. **60m BF-guard neutralization**: the claim that bf_tf='60' with
   bf_exit='off' is a trading no-op on the ORIGINAL artifact -- verify from
   pine/tvb_exp_bf_exit.pine (the deployed source's ancestor) that no BF
   output feeds orders/blocks when bf_exit=='off'.
6. **request.security audit**: the BF engine's lookahead_on + [1] idiom now
   appears in 4 scripts (champion + 2 winner indicators + E2 base) --
   confirm non-repainting by construction; NO other security calls anywhere.

Standing priorities on ANY TVB review: request.security lookahead in Pine,
model fidelity (is the backtest measuring what it claims?), overfitting /
sample-vs-structural reasoning (the champion search is LICENSED selection --
check the license boundaries held), fee/turnover math.

## Output contract

- Verbatim audit -> `docs/reviews/tvb11-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line` and Pine/TV docs. Never paste a
  secret/IP/account value into a review file.
- The critical synthesis (agree/dispute/act) is written by the NEXT session
  into `docs/HANDOFF.md` -- your job is the honest external read, not the
  final word.
