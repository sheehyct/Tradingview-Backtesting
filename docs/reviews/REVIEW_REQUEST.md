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
- Session under review: TVB-35 -- round-3 monitoring from the raw journals
  and the venue record, two journal-only shadow columns on the executor
  (hourly/daily immediate-control verdict; order-book spread on seat-stage
  rows), the round-3 halt (KILL_FLAT on the user's word), the public
  prereg / ledger amendments, and the week's pause for regime-detection
  design.
- Requested: 2026-09-08
- Write the audit to: `docs/reviews/tvb35-codex-audit.md` (copy
  `docs/reviews/_TEMPLATE.md`)
- NOTE: TVB-31, TVB-32, TVB-33 and TVB-34 audits were never returned and stay
  open. The DEEP-DIVE review (docs/reviews/deep-dive-2026-09-05-astra.md) was
  RETURNED and FOLDED in TVB-34; do not re-review it.

## Commits to review

| Repo | Local path | Range / commits |
|------|------------|-----------------|
| tradingview-backtesting (this repo, `main`) | `C:\Strat_Trading_Bot\tradingview-backtesting` | `848db00..HEAD` = 5b028a5 + the sha-pin follow-up on top -- docs only: HANDOFF TVB-35, startup prompt, this file, prereg amendment 2026-09-07a, ARM_LEDGER round-3 halt card (verify with `git diff --name-status 848db00..HEAD`) |
| hip3-executor (PRIVATE; local transport only) | `C:\Strat_Trading_Bot\hip3-executor` | main `5cd2b0d..fc90368`: 098cff1 (amendment 2026-09-07a: `HD_STACK`, `SEAT_STAGE_REASONS`, `book_summary`, `book_top` on both brokers, `_book_shadow` in the engine, 16 tests), 7dc011f (README STATUS 2026-09-07: the halt, labels, restart checklist), fc90368 (runs/2026-09-06_round3_aborted/ slices + README) |

## Read first (in this order)

1. `CLAUDE.md`; charter Section 0. Then the TVB-35 HANDOFF entry.
2. Executor README amendment 2026-09-07a and STATUS 2026-09-07; PREREG.md
   amendment 2026-09-07a (runs/2026-09-04_replay1/PREREG.md).
3. Executor `src/hip3_executor/rules.py` (HD_STACK, SEAT_STAGE_REASONS,
   book_summary), `engine.py` (`_scan_candidates`, `_book_shadow`,
   BOOK_CALLS_PER_POLL), `broker.py` (`book_top` x2),
   `tests/test_shadows_hd_book.py`, `tests/conftest.py` (FakeBroker.book_top).
4. The aborted-run copy `runs/2026-09-06_round3_aborted/live/` (local; may be
   gitignored) for the numbers quoted in the HANDOFF and ARM_LEDGER.

## Focus areas (scrutinize these)

1. Seat-stage gating of the order-book read: `SEAT_STAGE_REASONS` =
   {no_slot_free, cooldown, day_cap_reached}. Should `already_in_position`
   or `counter_drift` count as "competed"? Is anything journaled on a row
   that did NOT reach the seat stage?
2. The per-poll cache is keyed by coin while `mid` is read per row: two
   signals on one coin in one poll share one book read but could carry
   different mids -- is spread_bps then consistent? (Same poll, same served
   coin dict, so mid should be identical; verify.)
3. `l2_snapshot(name)` for builder-dex coins (`xyz:AAPL` naming) -- does the
   SDK call accept the dex-qualified name? No live check was made; every
   failure path returns None by design, so a silent None on every xyz row
   would be the failure mode.
4. The rate-budget claim: at most 20 l2Book reads per 5 s poll; is that
   within the venue's per-IP budget alongside the loop's own calls?
5. The claim that the weekly dot duplicates the daily on Sunday/Monday: the
   served 1w candle's open vs the scanner's week boundary (UTC Monday? the
   user's "Sunday 20:00 ET new week"?). Only 2/91 continuity refusals were
   the weekly's; is the coupling explanation right or was the week simply
   aligned?
6. Labor Day labeling: `session` = "rth" on 09-07 for 394 xyz rows; the
   README states the missing holiday calendar as an accepted limitation.
   Is the SK Hynix entry correctly described (Korean session also closed at
   09:31 ET)?
7. The ZEC liquidation (2026-09-06 04:46:32Z) sits before the ledger window
   (open 19:52:53Z); confirm the window definition excludes it and that the
   phone-app framing is right.
8. request.security: NO Pine file changed -- verify none did.

## Output contract

- Verbatim audit -> `docs/reviews/tvb35-codex-audit.md` (template:
  `docs/reviews/_TEMPLATE.md`, skeptic preamble included).
- Be concrete; cite `file:line`. Never paste a secret/IP/account value: the VPS
  IP, the master wallet address and the agent address stay out (this repo is
  public).
- The critical synthesis is written by the NEXT session into `docs/HANDOFF.md`.
