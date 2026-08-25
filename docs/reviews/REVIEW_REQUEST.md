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
- Session under review: TVB-27 -- the USER-DIRECTED live pivot. A new
  PRIVATE sibling repo (hip3-executor) was built from scratch, deployed
  to the user's VPS, and traded a dedicated $52.60 Hyperliquid
  agent-wallet account live and unattended 2026-08-22 14:26 -> 08-24
  21:58 UTC (34 round trips, account closed FLAT at $45.75 by
  user-decided KILL_FLAT; success metric was MECHANICS, which passed).
  THIS repo carries only docs (TVB-26 status flips + session-end docs +
  the committed TVB-26 audit). The TVB-26 FOLD IS STILL OWED and is NOT
  part of this request.
- SCOPE: the sibling repo is the primary target (see table).
- Requested: 2026-08-24
- Write the audit to: `docs/reviews/tvb27-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: tvb8/tvb9 remain unreturned (standing note).

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| hip3-executor (PRIMARY; private github.com/sheehyct/hip3-executor) | `C:\Strat_Trading_Bot\hip3-executor` | `e93d748^..ddbd9d0` (13 commits: executor build, paper/live brokers, rules gates, VPS deploy kit, dated mid-weekend rulings -- continuation escalation, min_reward_risk 1.0, operator alerts, hourly P/L -- fixes learned live, the committed weekend-1 ledger under `runs/2026-08-22_weekend1/`, the private ledger README 39255a9, and the TVB-28 ledger ANALYSIS c8e65f4 + MMQB addendum ddbd9d0 -- `analysis/weekend1.py` + `ANALYSIS.md` + `analysis.json` + committed venue ground truth. Range EXTENDED 2026-08-24 by TVB-28: the analysis is IN scope and its findings are provisional until this review returns) |
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `59cda10^..59cda10` (1 commit, 4 paths, docs only: TVB-26 audit recorded + status flips + TVB-27 session-end docs. RANGE-PIN RULE: the caret keeps 59cda10 in the diff; sanity-checked with `git diff --name-status`. The pin commit after 59cda10 is docs-only routing, out of range. Sibling hip3-executor gained one post-range docs commit 39255a9 -- the private ledger README the focus areas reference.) |

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0. Then hip3-executor `README.md` -- the
   ruleset v0 in trader terms, with every dated ruling.
2. hip3-executor `src/hip3_executor/rules.py` (gates), `broker.py`
   (order lifecycle, exit classification), `engine.py` (loop, software
   exits, P/L reporting), `deploy/` (VPS kit incl. the hidden-prompt
   secret handling).
3. `runs/2026-08-22_weekend1/` -- the canonical ledger (decisions /
   trades / tracker JSONL + state.json) plus the TVB-28 analysis layer
   (`ANALYSIS.md`, `analysis.json`, `venue/` ground truth,
   `analysis/weekend1.py`).
4. This repo's `docs/HANDOFF.md` TVB-27 entry (the session record).

## Focus areas (scrutinize these)

1. Order lifecycle correctness: bracket placement after fill, the
   never-hold-without-a-stop abort path, reconcile-on-vanish, the
   oid-match exit classification (venue auto-cancels the reduce-only
   sibling -- verified live 08-22; 4 `unknown_exit` rows predate the fix
   and are dated).
2. rules.py gates vs the dated rulings: continuation escalation
   (higher-TF in-force reversal backing), min_reward_risk floor, MAE
   clearance vs isolated liquidation distance, in-force (R11), ftfc
   alignment, dedup keys (per-signal-per-bar).
3. Ledger integrity: journals vs venue fills for the master wallet (the
   address is recorded in the PRIVATE hip3-executor repo at
   `runs/2026-08-22_weekend1/README.md` -- this repo is public, so the
   address never appears here); do the 34 round trips, exit reasons, and
   P/L totals reconcile?
4. Secrets: verify NOTHING sensitive is committed in either repo (.env
   excluded everywhere; the agent key never appears; the master ADDRESS
   is public by design).
5. Change discipline: every mid-weekend change is reporting-side or
   entry-side, dated, none retro-applied to open positions or past rows.
6. request.security: NO pine file changed this session -- verify none did.
7. TVB-28 ANALYSIS (added 2026-08-24, `analysis/weekend1.py` +
   `runs/2026-08-22_weekend1/ANALYSIS.md` + `analysis.json`): reproduce the
   to-the-cent reconciliation (deposit 52.60 - closedPnl 6.0327 - fees
   0.8082 - funding 0.0084 = 45.7507 vs 45.75); scrutinize the
   counterfactual method (1m-candle first-touch with stop-before-target
   pessimism; the ftfc-flip approximation from sparse decisions rows is
   bracket-biased; slots/cooldown/day-cap NOT applied to refused-setup sims
   -- upper bound framing must survive); check the headline claims (flip
   exits +29.71pp vs riding to stops; cont 0/7 structural no-TP argument;
   rr-floor refusals mean -0.154%/trade gross; account_value() isolated-
   margin double-count) against the journals and venue files. The analysis
   findings are PROVISIONAL until this review returns.
8. MMQB addendum (ddbd9d0, user-requested survivorship audit): verify the
   pool constructions (rails-blocked 211 / stack-blocked 256 unique
   setups from decisions.jsonl skip reasons; selection is arrival-ordered
   in `engine._scan_candidates`); adversarially probe the two census
   headlines -- (a) bench-worse-than-starters (-0.843%/trade vs -0.595%),
   (b) the confirmation-lag census (unconfirmed longs +0.525%/trade vs
   confirmed-queued longs -0.442%, median -0.28%, top-8 sims = 93% of
   pool profit). The flip-approximation lag plausibly FLATTERS unconfirmed
   entries -- quantify or bound that bias if you can.

## Advisory section requested (NON-BINDING, separate from findings)

Beyond the defect audit, the user asks for the reviewer's independent
strategy-level judgment, to be written as a clearly-labeled ADVISORY
section at the end of the audit (opinions, not findings; the user will
reconvene on these before any round-2 build/live test/strategy
brainstorm). The user's questions, near-verbatim:

- Honest thoughts on the current status of the strategy. Would anything
  have changed the outcome for the better? Was it too over-restrictive in
  some parts?
- Any other considerations vs previous backtest results (this repo's
  ARM_LEDGER / TVB-21..25 arcs are the reference; the executor is a
  pattern-entry, T1-target, ftfc-gated book -- closer to the M+T package
  world than to the continuity-only control).
- The "Monday morning quarterback" survivorship audit: why did the
  tickers that traded make the selection, and were any skipped ones
  better trades? (TVB-28's MMQB addendum is our attempt -- critique it
  and extend it if the data supports more.)
- The user is considering running the system pattern-by-pattern
  (separate books per signal name) in a future round -- thoughts on
  whether that is informative characterization or a tournament trap,
  and if informative, what design keeps it charter-clean (ablation
  ladder, pre-registration, no promotion by census).

Standing priorities apply (model fidelity; overfitting language; this
was a MECHANICS test -- any P&L claim beyond "mechanics passed, account
went 52.60 -> 45.75" should be flagged as over-claim).

## Output contract

- Verbatim audit -> `docs/reviews/tvb27-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value:
  the VPS IP and the master wallet ADDRESS must both stay out of the
  audit (this repo is public -- read the address from the private
  hip3-executor repo, reference it as "the master wallet").
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
