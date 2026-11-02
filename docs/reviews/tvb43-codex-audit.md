# TVB-43 External Audit -- Codex (verbatim source, read CRITICALLY)

> External review of `8a5806c..f3bb795`, captured 2026-11-02
> (TVB-43 post-session). ASCII text; code and findings are the reviewer's own.
>
> **Do NOT assume this is correct.** External reviewers can be wrong, conflate control vs variant,
> or over/under-state a risk. The critical synthesis -- where we agree, dispute, and act -- is in
> `docs/HANDOFF.md`. Read that alongside this.

---

## 1. Metadata

- **Session:** TVB-43 -- audit repairs, contract stage 3, session calendar, ES bench.
- **Reviewed:** `8a5806c..f3bb795`; workspace HEAD `5ee9b84` adds the docs-only review-range pin.
- **Reviewer:** Codex, local Windows workspace, read-only implementation review.
- **Overall verdict:** NEEDS-CHANGES.
- **Work order:** `docs/reviews/REVIEW_REQUEST.md`, status REQUESTED when opened.
- **Write scope:** this audit only. The owner's separately requested strategy assessment belongs
  in the conversational response, not in this session's formal findings.

## 2. Verbatim audit

The calendar implementation and default crypto regression held up. Both ES tapes reproduce
their saved rows and tables, the exported session/hour/target times map correctly to the real
tape, and the earlier named narration repairs remain intact. Those are useful, bounded checks.

The new regular-hours reading has an undeclared gap-entry accounting problem large enough to
change its sign. Separately, the bench exporter can overwrite an existing run before reaching
the repaired importer. The remaining findings concern a new asynchronous comparison path and
two metadata/reporting mismatches. None requires silently changing the frozen crypto book or
retroactively promoting a new strategy variant.

### F1 -- HIGH -- The ES session adaptation books gap-through entries at an unavailable trigger price

**Locations:** `analysis/bench/run_bench.py:262`, `analysis/bench/es_tape.py:186`,
`analysis/domino/manage.py:534`, `analysis/domino/manage.py:591`,
`analysis/domino/run_export.py:169`, `analysis/bench/BENCH_RECEIPT.md:78`,
`analysis/bench/BENCH_RECEIPT.md:167`.

The runner feeds disconnected sessions into the existing level-return accounting. A first
hour whose entire range is already beyond the trigger passes the strict high/low predicate.
The return is then measured from `level`, without a missed-entry state or an opening-price
fill convention. The daily books use the same level denominator. This is consequential for
RTH, where the overnight movement is absent from the tape but can be credited between the
prior-session trigger and the next session's open. The exported entry rule still describes
entry at the instant of the strict break.

**Confirmed from the saved rows and independently loaded session bars:**

| Daily units | Globex | RTH |
|---|---:|---:|
| Total | 3,824 | 3,797 |
| Session opens strictly beyond the trigger in the trade direction | 204 | 1,610 |
| Trigger is outside the entire entry-session range | 39 | 581 |

For example, the RTH 2011-01-12 long continuation uses 1273.75 while the session opens at
1278.50 and never trades down to the trigger. Its hourly exit-only return is +0.451423% from
the trigger, versus +0.078217% from the opening price. There was no 1273.75 entry available
in this RTH session. An order entered in a different session would require a different,
explicitly modelled trading rule.

I ran a deliberately limited sensitivity: preserve each recorded exit price and every row;
replace only a gap-through entry by the session open. For a long use `max(level, open)`;
for a short use `min(level, open)`. Recover the recorded exit price as
`level * (1 + sign * ret / 100)`, then calculate the return from the alternative fill.

| Daily book | Filled rows | Published level return, mean % | Same exits, opening-price sensitivity, mean % |
|---|---:|---:|---:|
| Globex C | 3,822 | -0.053285 | -0.066007 |
| Globex C_h | 3,801 | +0.009346 | -0.002267 |
| RTH C | 3,796 | +0.080659 | -0.080249 |
| RTH C_h | 3,796 | +0.158827 | -0.001728 |

This is **not** a causal strategy rerun, a proposed replacement result, or a fee/slippage
model. It holds exits fixed and does not re-evaluate targets, eligibility, or same-bar
ordering. It demonstrates that the apparent RTH sign advantage is sensitive to an
unavailable entry price, before costs. Arithmetic reproducibility does not resolve that.

**Requested disposition:** preserve the preregistered characterization, but prominently label
its gap-through units as theoretical level-to-exit measurements in the receipt, ledger and
run card. State the gap convention and counts. Before interpreting a session advantage as
an actionable path, add a separately declared comparison with missed-gap entries or causal
available-price fills, including targets already passed at the open. Add a vector where the
whole first session is above a long trigger and the mirrored short case. Do not alter the
default crypto path to make this benchmark look better.

### F2 -- MEDIUM -- The new bench exporter bypasses the staged replacement protection

**Locations:** `analysis/bench/run_bench.py:241` through `analysis/bench/run_bench.py:248`;
contrast `analysis/domino/contract.py:800` and `analysis/domino/contract.py:840`.

`export_run()` opens `data/runs/<id>/run.json` and the instrument JSON in write mode BEFORE
calling `K.import_run(folder, DATA)`. On a rerun, those are the registered run's live files.
The importer cannot protect their previous contents once the exporter has truncated them.
An interrupted or failed serialization leaves the old derived index/listing advertising a
partially replaced run. A reader can also observe the intermediate mixed set.

**Reproduction:** in an isolated temporary data root, exported a valid Globex tape with an
empty trade list; reran the actual exporter with `json.dump` raising `OSError` on its second
call, after the instrument file had been opened. The instrument file changed from 4,736,958
bytes to zero bytes. `runs.json` remained unchanged and still advertised the run. Reading
the instrument JSON failed. No real viewer data was modified by this probe.

This is a new producer-side path, not a claim that the repaired `import_run()` still destroys
the old run when it rejects an untouched external source.

**Requested fix:** serialize the entire source into a separate temporary folder first, then
pass that source to the staged importer. On exporter write/validation failure the old run
and listing must remain byte-identical. Test failure during the instrument write, not only
the importer's two renames.

### F3 -- MEDIUM -- Switching the current run can strand an in-flight comparison in loading state

**Locations:** `analysis/domino/viewer/app.js:658`, `analysis/domino/viewer/app.js:668`,
`analysis/domino/viewer/app.js:713`, `analysis/domino/viewer/app.js:916`.

`loadOther()` captures the current run generation and sets `state.other = {id, loading:true}`.
If the user changes the current run while that request is pending, `loadRun()` increments the
generation. `fillRunCompare()` retains the other run unless it has become the current run.
The old response is correctly discarded, but nobody clears or restarts its loading state.

**Reproduction using the actual app module under Node with a stub DOM and deferred fetch:**

1. Current run A; begin loading comparison B and hold B's `run.json` response.
2. Complete `loadRun(C)`.
3. Resolve B's response and await the original `loadOther(B)`.
4. `state.other` remains `{"id":"B","loading":true}`. The comparison renders "loading run B..."
   indefinitely, until the user changes/reselects the comparison.

This concerns the newly added cross-run comparison, not the repaired main-universe loader.

**Requested fix:** on a current-run switch, cancel and clear a pending other-run load or
restart it under the new generation. Add an asynchronous test for A/B pending -> C -> B
completion, alongside the already-loaded comparison and other-becomes-current cases.

### F4 -- MEDIUM -- The roll split is defined by C but presented as clean for other books, and its mean difference is given a causal reading

**Locations:** `analysis/bench/run_bench.py:79`, `analysis/bench/run_bench.py:89`,
`analysis/bench/run_bench.py:122`, `analysis/bench/run_bench.py:145`,
`analysis/bench/BENCH_RECEIPT.md:117`, `analysis/bench/BENCH_RECEIPT.md:124`,
`docs/ARM_LEDGER.md:727`.

The implementation faithfully follows the preregistered HEADLINE-window definition of
`extras.roll`: it looks through `row.days`, the C exit/cap. The split then reports all books
under "no roll in the window". Other books, especially the reference, have different fill
dates. A null flag is not a claim that those trades avoided a roll.

**Confirmed:** among null-roll rows, the reference's actual `days_ref` holding interval
crosses a flagged roll session on 235 Globex rows (36 D, 107 W, 92 M) and 202 RTH rows
(23 D, 89 W, 90 M). For example, Globex monthly long reversal 2011-04-21 exits C at day 6,
but the reference settles at day 72 and crosses the 2011-06-16 roll. Its roll flag is null.
Thus even the receipt's daily "no roll" reference column contains roll-crossing trades.

Also, the higher average of the roll-window cohort does not measure the amount the contract
jump "adds". Membership depends on how long C stays open. Longer-lived survivors and other
market differences are mixed with the real price discontinuity. The unadjusted switch is
a genuine confound, but these subgroup means do not isolate its causal contribution.

**Requested disposition:** retain the declared split and label it "no roll through headline
C's exit/cap" everywhere it is used. Explain that other books can cross a roll. Remove the
claim that the split establishes a roughly one-point roll contribution. Any book-specific
holding-window flags or same-contract/roll-adjusted comparisons should be an explicit
additional diagnostic, not an unannounced change to the preregistration.

### F5 -- LOW -- Unicode casefold merges listings for names that are distinct on this Windows filesystem

**Locations:** `analysis/domino/contract.py:75`, `analysis/domino/contract.py:82`,
`analysis/domino/contract.py:712` through `analysis/domino/contract.py:718`.

`_slug()` accepts Unicode alphanumeric characters, directories retain that spelling, and
`register()` merges ids using Python `casefold()`. That equivalence is broader than the
filesystem's equivalence on the Windows workspace used for this review.

**Reproduction through public `import_run()`, isolated root:** import two otherwise valid
inline runs with ids `"K"` and `"\u212a"` (KELVIN SIGN). Both are accepted. There are two
physical folders, but `runs.json` contains only the latter id because both casefold to `k`.
The first valid run becomes unlisted. I did not observe a directory overwrite or traversal
in this example; its bytes remain on disk.

**Requested fix:** use one explicit identity convention for both storage and registration.
For example, constrain ids to an ASCII alphabet, or canonicalize the storage id as well as
the listing key and reject ambiguous replacements. Add the K/KELVIN example to the existing
ASCII case-collision tests. Do not equate all Unicode casefold matches with one NTFS path.

### Smaller reporting issues

- `analysis/bench/BENCH_RECEIPT.md:47` gives 26,900 RTH hourly bins. The raw replay and
  `analysis/bench/results/bench_rth.json:8` both give **26,570** (120 short RTH sessions).
- `analysis/bench/BENCH_RECEIPT.md:113` says twelve positive RTH years but names only two
  negative years. Grouping daily `ret_C` by entry year gives **13 positive, 2 negative**.
- The reused candidate-table footer, e.g. `analysis/bench/results/bench_rth_tables.md:860`,
  still describes a roughly 208-day crypto hourly window and Hyperliquid main/xyz taker fees.
  Those are not the ES window or an ES cost model. The receipt's gross-only label is correct;
  the copied footer should agree with it.
- `analysis/bench/run_bench.py:334` uses a `json.dumps(default=...)` handler that does not
  replace native float NaN. `bench_rth.json:1468` and nearby single-row intervals contain
  literal `NaN`, which is not strict JSON. Normalize non-finite floats to null before dumping
  and use `allow_nan=False`. No current viewer failure was attributed to this summary file.
- The normal per-row confidence intervals are descriptive calculations; overlapping trades
  and shared market episodes are not independent observations. The wording "intervals are
  honest for this tape" at receipt line 189 should not imply calibrated uncertainty or a
  successful out-of-sample strategy test. A clustered/block-based assessment is additional
  research, not a reason to alter the frozen arithmetic in this patch.

### Confirmed repairs and validation

**Default crypto path: CLEAN for the requested gate.** Ran the actual `manage.main()` for
`--as-of 2026-10-10` against the local cache, intercepting output writes into memory and
disallowing a network fetch. It processed 292 perps / 179,498 rows. Both saved artifacts
reproduced byte-for-byte using their Windows newline encoding:

- `manage_tables.md`: SHA-256 `2a2b0965fbe4a93ace17307d898431b19e1adb61c5478855dbdde05cbdf3b021`.
- `manage.json`: SHA-256 `da66df6d4fa0da7a4c4387e1418ac5d9d6e5af159f7fde69159987b1bf859b7f`.

**ES arithmetic: CLEAN within the declared level-fill model, subject to F1/F4.** Regenerated
all 4,823 Globex and 4,788 RTH rows from the source cache. All saved CSV columns compared
within `rtol=atol=1e-12`; counters matched. Actual runner tables reproduced exactly in memory.
Summary values matched after excluding generation timestamps and treating NaN as missing
(plain Python NaN equality initially made the RTH summary probe read false).

**Calendar and tape: CLEAN for the exercised definitions.** The eight dedicated calendar
tests pass: default restoration, holiday week completion/first session, prior-session level,
overnight/weekend stepping, cap, missing hour and session-clock export. Globex cache weekly
and monthly OHLC matches engine aggregation. Independently aggregating the one-minute source
under the declared fixed 18:00-17:00 ET cutoff matches all cached daily OHLCV. Historical
minutes outside that declared cutoff are not a cache mismatch and were not silently added.
RTH opens are 09:30 ET; its final ordinary bin is 15:30-16:00.

**Export times: CLEAN.** Independently mapped saved card entry times, C_h settlement times
and hit A_h target times to the corresponding raw real-time bars: 10,747 checks on Globex,
11,091 on RTH, zero mismatches. The real 2025-10-31 session opens at 22:00 UTC on the prior
date; the 2025-11-03 session opens at 23:00 UTC on the prior date. Friday-to-Monday hour-one
mapping absorbs that November clock change. Both ES runs pass `contract.check()` with zero
problems; each has two generic bar-gap warnings from expected session spacing, not proof
that every gap is scheduled.

**Earlier importer repairs: CLEAN for the exercised serial-import cases.** The suite covers
invalid replacement preserving bytes/listing, direct/zip/folder inline parity, generated
names/device names, sparse extras, recovery with dashed ids, and rollback on second-rename
failure. A real Windows open handle on the destination `run.json` made replacement fail
with PermissionError, left every old file and the listing unchanged, and left no staging
debris. After closing it, in-place import from `<dest>/run.json` succeeded with all six
example cards. This directly exercises an open destination handle; it is not a concurrent
HTTP/browser stress test. The new bench producer remains subject to F2.

**Earlier viewer repairs: CLEAN for the named cards and exercised module behavior.** Ran
the actual complete `story.narrate()` against saved cards, not only helper predicates:

- ATOM 2026-05-09 daily long: D one R on day 2, May 11, +5.28%.
- ACE 2026-04-29 daily long continuation: hourly entry 02:00, exit 03:00, one hour later.
- BTC 2026-03-16 weekly long inside: reference stop on day 11, March 27.
- BLUR 2026-07-24 weekly short inside: D5 close exit on day 24, August 17, distinct from C's cap.
- 0G 2025-10-01 C_u and 0G 2026-03-19 C_h: compared-price language and the day's color at
  the exit hour use the correct prices, rather than trade direction or the final daily close.

Run one's rebuilt universe equals its saved universe. None of its 292 exported daily tapes
has an internal daily gap: no run-one `:days` value changes when calendar-day distances are
replaced by bar offsets. The actual median holds therefore do not move. The changed rule
matters for sparse/session tapes. Mapping a timestamp inside an absent calendar day to the
previous observed bar is a coherent chart-bucket convention; it is not evidence of trading
or observation on the missing day. Role pairing and disjoint-unit filtering are consistent
with the declared comparison contract; the shared axis remains a readability limitation.

**Repository checks:**

- `.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider`: **508 passed, 2 skipped**.
- `.venv\Scripts\ruff.exe check --no-cache .`: passed.
- `node --check` for every top-level viewer JavaScript module: passed.
- `.venv\Scripts\python.exe scripts/secret_scan.py --range 8a5806c`: passed, 35 files.
  This scanner takes a base, so the scan includes HEAD's docs-only range pin as well.
- `git diff --check 8a5806c..f3bb795`: one whitespace warning, an extra blank line at EOF in
  the newly committed prior audit `docs/reviews/tvb42-codex-audit.md:331`; no code warning.
- Viewer data and vendor paths remain gitignored. Pre-existing untracked `User_Notes.md`
  and `analysis/domino/viewer/proto_codex/` were preserved.

### Explicit limits

- The browser host returned "The browser access host is unavailable". No rendered/browser
  interaction result is claimed. Viewer evidence is from the actual modules under Node,
  the suite and real saved cards; chart rendering and an HTTP open-handle stress run remain
  unverified in this review.
- Concurrent imports are **not handled**: recovery sweeps staging folders without an active
  import lock. Same-id simultaneous imports were explicitly excluded by the work order;
  this review does not redesign that protocol or certify concurrent use.
- Unicode listing loss is demonstrated in F5. No public-loader ADS/traversal overwrite was
  demonstrated. This is not a blanket proof of every NTFS naming/length equivalence.
- A missing interior hourly bin censors; recognizing a missing terminal bin as missing rather
  than an early close would require an expected-session schedule. The declared fixed session
  definitions were checked; a complete historical exchange-calendar certification was not.
- Reproducible gross, equal-notional overlapping trades do not establish executable fills,
  account returns, margin survivability, costs, or future edge. The owner's separate strategy
  question does not promote these benchmark measurements into a deployable strategy.

## 3. Actionable items (reviewer's own list)

1. **F1 -- HIGH:** qualify gap-through level accounting and run a declared executable-entry
   comparison before interpreting the RTH advantage -- `analysis/domino/manage.py:534`.
2. **F2 -- MEDIUM:** build the benchmark export source away from the registered destination,
   then use the staged importer -- `analysis/bench/run_bench.py:241`.
3. **F3 -- MEDIUM:** clear or restart pending comparisons after the current-run generation
   changes -- `analysis/domino/viewer/app.js:668`.
4. **F4 -- MEDIUM:** name the headline holding window in roll splits, and remove the causal
   roll-contribution inference -- `analysis/bench/run_bench.py:145`.
5. **F5 -- LOW:** align accepted run-name identity with storage and listing identity --
   `analysis/domino/contract.py:717`.
6. **LOW reporting follow-up:** correct RTH hours/year counts, remove crypto-only table
   footer text, emit strict JSON, and qualify interval interpretation.

## Suggested prompt

Review the repair against F1-F5 without changing the preregistered control. Demonstrate a
gapped session whose trigger never trades; preserve the old registered run through an
exporter write failure; switch the current run during a pending comparison fetch; reconcile
each displayed roll label with the book it describes; and import K plus U+212A on Windows.
Retain the crypto byte-identity gate. Report repaired, disputed, and still-unverified items
separately, with browser evidence clearly distinguished from Node/module checks.
