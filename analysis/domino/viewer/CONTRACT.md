# The run and trade-card contract (the viewer's row contract)

> Status: CONFIRMED by the owner 2026-10-31 (TVB-42), stage 1 built the same day: the validator
> and importer (`analysis/domino/contract.py`), the management book's exporter and the row-for-row
> check (`analysis/domino/run_export.py`), the CLI (`trade_viewer export-run / import / validate /
> check-run`), tests in `tests/test_domino_contract.py`. Stage 2 built 2026-11-01 on the owner's
> word: the page reads runs (`data/runs.json`, a run picker; `core.js` holds the run's books with
> roles and colours; `prep` derives day offsets from the card's times against the run's bars; the
> ladder, the story, the markers and Compare read the card's book entries; no engine column name
> survives in the page). Stage 3 built 2026-11-01 (TVB-43): the flat layout, `build` and
> `check-run` retired; Compare across runs by role; the example single-file run imported and
> viewed end to end. Confirmed choices are in section 11; section 12 lists what the stages settled.

One card shape that every run exports and the trade viewer draws. The page reads cards, it
never computes a trade: every price, time, fill and return on screen is what the producing
engine recorded. A run produced anywhere (this workspace's management book, the STRAT ML
vessel, a futures bench, a backtest written on a phone) is importable for viewing if it writes
this shape.

## 1. Glossary (trader terms first)

- **Run**: one labelled result set. A name, the day it is good through, the instruments, the
  bar clock, the rule card in words, and the books it scored. The page shows one run at a time.
- **Card**: one trade. The setup, the levels fixed at entry, how each book left, the travel,
  and the context at entry.
- **Book**: one way of managing the same trade (exit only; all out at T1; hold through T2; one R
  or the exit; the hourly clock; the chance book with its setup-bar stop). A run names its own
  books. One of them is the **headline**: the book the run's receipt leads with.
- **How it left**: the fixed vocabulary for a book's exit: `target`, `one_r`, `stop`, `clock`,
  `cap`, `censored`, `none`. Words for the page to colour and narrate; the book's own rule text
  says what they mean for that book.
- **Bar clock**: when the day rolls for the run (00:00 UTC for a 24/7 perp, 18:00 ET for the
  Globex day, a session open for a session bar) and the finest resolution the engine saw fills
  at (day, hour, minute).
- **Role**: what a book is for, so the page can line runs up without matching names:
  `headline`, `target`, `stop`, `clock`, `reference`.
- **Level, far side, one R**: the entry price (the level that broke), the setup bar's far side
  (the chance book's stop and the yardstick for the management books), and one R beyond entry.

## 2. The run card (`run.json`)

```json
{
  "contract": 1,
  "id": "management-book-2026-10-10",
  "name": "STRAT management book, Hyperliquid perps, as of 2026-10-10",
  "as_of": "2026-10-10",
  "built": "2026-10-31T14:00:00Z",
  "source": { "repo": "tradingview-backtesting", "commit": "75626b7",
              "command": "uv run python -m analysis.domino.trade_viewer export-run --as-of 2026-10-10" },
  "clock": { "day_roll": "00:00 UTC", "resolution": "day", "weeks": "Monday 00:00 UTC", "months": "calendar",
             "label_shift_hours": 0, "calendar": "utc_day" },
  "units": ["D", "W", "M"],
  "bars": ["1h", "1d"],
  "returns": "percent of price, equal size, no fees, no leverage",
  "rules": {
    "setup": "2-2 reversal, 2-2 continuation, inside-bar break, outside-bar break on the daily, weekly and monthly bar",
    "entry": "the instant the setup bar's high (low) breaks, strictly",
    "stop": "none for the management books; the setup bar's far side for the chance book",
    "targets": "T1 the pattern's own magnitude or the first unbroken weekly / monthly level, T2 / T3 the next unbroken levels, fixed at entry",
    "exit": "a daily close against the trade with the week also against it at that close; 20-day cap",
    "continuity": "none (the week's side at entry is recorded, not gated)"
  },
  "books": [
    { "id": "C",   "name": "exit only",                 "role": "headline",  "rule": "No target. Hold until a daily close goes against the trade with the week against it at that close." },
    { "id": "A",   "name": "all out at T1",             "role": "target",    "rule": "Everything out at T1, the pattern's own magnitude. Otherwise the exit." },
    { "id": "B",   "name": "hold through T2",           "role": "target",    "rule": "Hold through T2 with the exit live. T1 is not a decision." },
    { "id": "D",   "name": "one R or the exit",         "role": "target",    "rule": "One R or the exit, whichever comes first, inside the 20-day cap." },
    { "id": "D5",  "name": "one R or the exit, 5 bars", "role": "target",    "rule": "One R or the exit inside five bars of the unit, the chance book's own horizon." },
    { "id": "ref", "name": "chance book",               "role": "reference", "rule": "One R or the setup-bar stop, marked at bar five." },
    { "id": "C_h", "name": "hourly clock",              "role": "clock",     "resolution": "hour",
      "rule": "Exit only, on the first hour closing against the trade while the day is against it; the entry is the same level at the first hour strictly through it." },
    { "id": "C_u", "name": "under water",               "role": "clock",     "rule": "Exit only, reading against as a close through the entry price with the week against it." },
    { "id": "C_own", "name": "own clock",               "role": "clock",     "rule": "Weekly and monthly units only: the unit's own close against its open with the next bar up also against it; 20 bars of the unit." }
  ],
  "instruments": [ { "instrument": "BTC", "file": "BTC.json", "n": 1407, "first": 1758067200, "last": 1791504000, "bars": ["1h", "1d"] } ],
  "notes": "free words: what this run is for, what it is not"
}
```

`units` names the setup bar sizes the cards use (`bar` on a card must be one of them); `bars`
names the candle sizes shipped. A book may carry `resolution` (overriding the run's), an
optional `group` (words, e.g. "hourly clock", "under water": grouped books are the same book on
another clock or target, which the page folds under their group and Compare leaves off its
table) and, for a book that takes a target, `target`: the name of the target it takes (`T1`,
`T2`, `mm`, or `one_r` for one R), so the page can say "its target was only touched after the
exit" by reading the card, never by guessing from the book's id. `instruments` is filled by the importer from the instrument files; a producer may leave
it out. A run with one instrument may put everything in `run.json` (section 7, the single-file
flavour).

## 3. The trade card

One card per trade; the books are a list on it (the owner's choice, section 11). Every time is
a UTC timestamp in seconds, the open time of the finest bar the engine looked at, so a touch
known only to the day sits on that day's bar and a fill known to the hour sits on that hour's.

```json
{
  "id": "BTC-2026-03-16-W-up",
  "instrument": "BTC",
  "bar": "W",
  "pattern": "2-2 reversal",
  "kind": "reversal",
  "direction": "up",
  "class": "plain",
  "stack": [ { "bar": "D", "price": 84120.0 } ],
  "entry": { "t": 1773619200, "price": 84120.0 },
  "far": 81900.0,
  "one_r": 86340.0,
  "r_pct": 2.64,
  "targets": [
    { "name": "T1", "price": 88450.0, "source": "anchor", "touched": 1774051200 },
    { "name": "T2", "price": 91200.0, "source": "M",      "touched": null },
    { "name": "mm", "price": 86340.0, "source": "measured move", "touched": 1773964800 }
  ],
  "touches": { "one_r": 1773964800, "far": null },
  "books": [
    { "id": "C",   "how": "clock",  "at": 1774569600, "price": 87010.0, "ret": 3.44, "hit": null },
    { "id": "A",   "how": "target", "at": 1774051200, "price": 88450.0, "ret": 5.15, "hit": true },
    { "id": "B",   "how": "clock",  "at": 1774569600, "price": 87010.0, "ret": 3.44, "hit": false },
    { "id": "D",   "how": "one_r",  "at": 1773964800, "price": 86340.0, "ret": 2.64, "hit": true },
    { "id": "D5",  "how": "one_r",  "at": 1773964800, "price": 86340.0, "ret": 2.64, "hit": true },
    { "id": "ref", "how": "one_r",  "at": 1773964800, "price": 86340.0, "ret": 2.64, "hit": true },
    { "id": "C_h", "how": "none",   "at": null, "price": null, "ret": null, "hit": null, "note": "outside the venue's hourly window" }
  ],
  "travel": { "mfe": 6.10, "mae": 0.90, "window": "C", "next_bar": "with" },
  "context": { "week_side": "with", "month_side": "against" },
  "extras": { "liquid": true, "dex": "hl" }
}
```

Field rules:

- `bar` is one of the run's declared bar names (`D`, `W`, `M`, or a session / intraday bar the
  run names). `kind` is one of `reversal`, `continuation`, `inside`, `outside` for the filters;
  `pattern` is the words (any STRAT name). `class` and `stack` are optional (the domino census's
  stack class and the other levels broken on the same bar).
- `far` is the setup bar's far side; `one_r` and `r_pct` follow from it. All optional: a run with
  no setup-bar concept leaves them null and the one-R books absent.
- `targets` is a list; names are free (`T1`, `T2`, `T3`, `mm`); `source` is words; `touched` is
  the first touch time or null (never inside the window).
- `touches.one_r` and `touches.far` are the first touch of one R and of the far side.
- Every `books[]` entry's `id` must be declared in the run. `how` is the vocabulary of section
  1. `at` and `price` are required when `how` is `target`, `one_r`, `stop` or `clock`; `at` is
  the cap time when `how` is `cap` (`price` optional there); all three null when `censored` or
  `none`. `ret` is a number except for `none` and `censored`. `hit` says whether the book's own
  target or one R was touched (null for books without one). `note` is optional words (why
  `none`, a tie the bar cannot order). A declared book ABSENT from a card does not apply to that
  trade (a daily unit has no own clock); `none` means it applied and was not scored. A book on
  its own clock may carry `entry`, its own entry time (the hourly clock enters at the first hour
  strictly through the level), at or after the card's entry and at or before its `at`. A book
  entry may carry its own `resolution` when one fill is known less finely than the book's
  (the hourly one-R book's fill is known to the day; its `at` is then the latest time known to
  be at or before the fill: the touch day's open, or the entry hour on the entry day).
- `stack` entries may carry only `bar` when the producer did not record the other levels'
  prices; the page reads the prices off the bars in that case.
- `travel` is recorded once, in the window the run names (`window` is a book id).
- `context` holds the sides at entry; `extras` is a free bag shown as chips (fees in R, ATR,
  volume tier, anything a run wants on the card) and never computed on.

## 4. Times and resolution

The run's `clock.resolution` is the resolution of every time on a card unless a book overrides
it (`resolution` on the book, e.g. the hourly clock). The page derives "day 3" or "hour 14" from
the entry time and the run's day roll; cards never carry offsets. A fill known to the day is a
timestamp at that day's open under the run's day roll (00:00 UTC for a perp day; the 18:00 ET
open for a Globex day). The exit of a clock exit is the time of the bar whose close fired it.

A time belongs to the SESSION whose daily bar opens latest at or before it (an hour of a Globex
session that crosses midnight UTC stays with its session). A session is NAMED by the calendar
date of its open plus `clock.label_shift_hours` (0 for a 00:00 UTC day; 6 for the Globex day,
whose Sunday 22:00 or 23:00 UTC open is Monday's session): that label is the date the page
prints, the key of `dates.json` and the universe table's `date`. `clock.calendar` is `utc_day`
(the default: every calendar day is a bar, a missing day is a gap) or `session` (sparse: no
weekend, holidays; a week or month is complete once the data runs past it). Day offsets are
counted in bars (sessions), not calendar days: a Friday-to-Monday hold is one bar.

## 5. How it left

| `how`      | meaning                                                      | needs `at` / `price` |
|------------|--------------------------------------------------------------|----------------------|
| `target`   | the book's target filled (which one: `note` or `hit`)        | yes                  |
| `one_r`    | one R filled                                                 | yes                  |
| `stop`     | the book's stop filled                                       | yes                  |
| `clock`    | the book's exit clock fired (a close against, an hour, ...)  | yes                  |
| `cap`      | marked at the book's horizon, nothing fired                  | `at` = the cap time  |
| `censored` | the data ends inside the book's window; no result            | no                   |
| `none`     | the book was not scored on this row (reason in `note`)       | no                   |

A touch that the bar cannot order (the stop and one R on the same daily bar) is whatever the
engine recorded, with the engine's rule in `note` ("the engine takes the stop first").

## 6. Bars

Per instrument, per bar size the run declares, as arrays `[t, open, high, low, close, volume]`
with `t` the bar's open in UTC seconds, sorted, as the engine normalised them. Bars are optional:
a run that ships none still imports; the importer can fill a Hyperliquid coin's bars from the
census cache (`--bars-from-cache`), otherwise the card shows the story and the ladder with a
"no bars for this run" chart. The page aggregates weekly and monthly candles from the daily
bars, bucketed by each bar's LABEL date (Monday 00:00 weeks, calendar months of the label); a run
on another day roll ships its own daily bars already rolled and may ship `1w` and `1M` bars too,
whose open / high / low / close then replace the aggregate for the matching week or month (the
exchange's bar, not a re-aggregation); the daily bars still say which days a week holds.

## 7. Files, folders, import

```
viewer/data/runs.json                    the list of imported runs (importer-maintained)
viewer/data/runs/<id>/run.json           the run card
viewer/data/runs/<id>/<INSTRUMENT>.json  { "instrument", "bars": { "1d": [...], "1h": [...] }, "trades": [cards] }
viewer/data/runs/<id>/index.json         derived by the importer: instruments, counts, first / last
viewer/data/runs/<id>/dates.json         derived: every entry day's trades across instruments
viewer/data/runs/<id>/universe.json      derived: the columnar table the Compare tab reads
```

Single-file flavour: one `run.json` with `"instruments": [{ "instrument", "bars", "trades" }]`
inline; the importer splits it. A zip of either is accepted. CSV is not a first-cut input: a card
holds a list of books, which needs two tables in CSV; it can be added as an input flavour if a
producer needs it, converting to the same JSON.

```
uv run python -m analysis.domino.trade_viewer export-run --as-of 2026-10-10    the management book -> a run folder, then import
uv run python -m analysis.domino.trade_viewer import <folder | run.json | zip> [--id x] [--bars-from-cache]
uv run python -m analysis.domino.trade_viewer validate <folder | run.json | zip>
uv run python -m analysis.domino.trade_viewer serve [--port 8765] [--no-open]
```

`validate` says what is wrong in plain words with the card named ("BTC card
BTC-2026-03-16-W-reversal-up: book A left by target but has no price"); `import` refuses a run
that does not validate, builds the run in a staging folder and swaps it in only when every card
has passed (a refused replacement leaves the run it would have replaced, and the listing,
untouched); the source may be the destination folder or its `run.json`. Run ids start with a
letter or a digit; instrument names become plain file names (a colon, slash or backslash turns
into an underscore), so nothing a run writes can land outside its folder. `check-run <id>`
compared an imported run with the flat viewer data row for row and was the stage-1 regression
guard; its exact coverage was the level, the six ladder books' returns, the A / B / D / D5 hit
flags, the headline's / D5's / chance book's reason and day, T1's price and touch day, one R's
touch day, and the hourly clock's reason and return. It did NOT compare the A / B / D books'
reasons or days, the hourly books' entry and exit hours, or the clock variants (`C_u`, `C_own`,
`C_long` and their A / D books), and it walked only the instruments in the imported index
(TVB-42 audit F8). Retired with the flat layout in stage 3.
Checks: the contract version; one headline book; every book id on a card declared in the run;
`how` in the vocabulary and the `at` / `price` / `ret` rules of section 3; prices positive;
times at or after the entry; a touched target's time at or before the book that filled on it;
bars sorted (gaps are a warning, not a refusal); instruments on cards present in the bars or
flagged "no bars".

## 8. What the page does with it

- A run picker (the list from `runs.json`; the last chosen run remembered); the instrument
  list, the calendar, the table rail and Compare all belong to the chosen run.
- The ladder iterates the run's `books`, in the run's order, coloured by role; a book with
  `how: none` keeps its name and prints its note (the TVB-39 F6 rule, now a contract rule).
- The story reads the card: the setup from `pattern` and the levels, each book's paragraph from
  the book's `rule` plus its `how` / `at` / `price` / `ret`, the clock sentences (the day's
  close against its open, a Monday) as readings of the bars at the recorded exit time, labelled
  as readings. Nothing in the story infers which clock a book used (the TVB-41 audit F1 class of
  bug ends here).
- Compare lines runs up by role (headline against headline) and by book id within a run; the
  universe table is derived at import, so an imported phone run gets Compare for free.
- Markers: the entry at `entry.t`; each target at its `touched` time; each book's exit at its
  `at` on the pane whose resolution matches.

## 9. The management book's mapping (the exporter is mechanical)

| card field | engine column(s) (`manage_trades.csv.gz`) |
|---|---|
| `entry.t`, `entry.price` | `date` at 00:00 UTC (resolution day); `level` |
| `bar`, `kind`, `direction`, `class`, `stack` | `tf`, `kind`, `direction`, `cls`, `stack` + `near_tf` with the levels from the census |
| `far`, `one_r`, `r_pct` | `stop`, `level` +/- `r_pct`, `r_pct` |
| `targets` | `t1` / `t1_src` / `t1_k`, `t2` ..., `t3` ..., `mm_t1` / `mm1_k` (touch = `date` + k days) |
| `touches` | `one_r_k`, `stop_k` |
| book C | `status` (exit -> clock, open -> cap, censored), `exit_k`, `ret_C` |
| book A / B | `hit_A` -> target at `t1_k`, else as C; `hit_B` -> target at `t2_k`, else as C; `ret_A`, `ret_B` |
| book D | `hit_D` -> one_r at `one_r_k`, else as C; `ret_D` |
| book D5 | `hit_D5` -> one_r; `status5` exit -> clock at `days_D5`, open -> cap, censored; `ret_D5` |
| book ref | `out5` stop -> stop at `stop_k`, one_r -> one_r at `one_r_k`, neither -> cap at bar five, censored; `ret5` |
| book C_h | `status_h` (exit -> clock at the hour, else none with the reason), `entry_h`, `exit_h`, `hours_h`, `ret_C_h` (resolution hour; the A / D variants `ret_A_h`, `ret_D_h` as two more clock books if wanted) |
| book C_u | `status_u`, `exit_k_u`, `ret_C_u` (and `ret_A_u`, `ret_D_u`) |
| books C_own, C_long | `status_own` / `days_own` / `ret_C_own`; `status_long` / `days_long` / `ret_C_long` (weekly / monthly units) |
| `travel` | `mfe_x`, `mae_x` (window C), `next_bar` |
| `context` | `w_support`, `m_support` |
| `extras` | `liquid`, `dex`, `flag`, `anchor`, `reached1..3`, `stop_saw`, `stop0` |

Two honest limits of the row, stated on the run card: `B_mm` (hold through the second
measured-move rung) is not exported because the row holds neither that rung's price nor its
touch day; `D_h`'s one-R fill carries the touch DAY (the row has no touch hour for one R) with
a note saying so. Prices of clock exits and cap marks are recovered from the recorded return
(`level * (1 + sign * ret / 100)`), which is the engine's own definition of the return. The
`A_h`, `D_h`, `A_u`, `D_u`, `A_own`, `A_long` and `A_mm` variants are exported as grouped books.
`check-run` compared the imported run with the page's flat data row for row before the flat
`viewer/data/*.json` layout was retired (stage 3); section 7 states exactly what it covered.
The TVB-42 audit's independent probe (the typed CSV rows against every card: 4,314,995 field
checks, zero differences, including the clock variants' returns and times that `check-run` did
not cover) is the broader receipt for run one.

## 10. Build stages (each lands on its own, tested, before the next)

1. This document confirmed; the exporter (`export-run`) and the importer / validator with
   tests on hand vectors (a valid run, each refusal); the management book exported and imported
   as run one; the derived files agree with today's `build` output.
2. The page reads runs: the picker; `core.js` iterates `run.books`; the story and the ladder
   read the card; markers from timestamps; the node tests moved to the card shape; the audits'
   named rows (ATOM 2026-05-09, ACE 2026-06-14, BTC 2026-03-16 W, BLUR 2026-07-24 W) re-checked.
3. Compare per run and by role; the flat layout retired; NOTES.md updated; the importer tried on
   a hand-written single-file run (the phone case) end to end. DONE 2026-11-01.

Later, on the owner's word: a CSV input flavour; the vessel's event table as a run; the ES bench
as a run (`docs/experiments/tvb43_bench_prereg.md`, draft).

## 11. Decisions recorded (2026-10-31, the owner)

- One card per trade with the books as a list on it (not one card per book).
- Every time is an exact timestamp with a declared resolution (not day offsets).
- Each run declares its own books with a role; no fixed house names across runs.
- Runs made outside this workspace (a phone backtest included) must be importable by writing
  this shape: JSON, one file or a folder, validated on import; bars optional. CSV deferred.

## 12. What stage 1 settled (2026-10-31)

- The universe table (Compare) carries the ladder books only: roles headline / target / stop /
  reference without a `group`. Grouped books (the other clocks, the measured-move variant) stay
  on the cards. Flags and short categorical strings in `extras` become coded columns (`x:<key>`);
  anything else stays on the card.
- Day offsets on the universe table are whole days from the entry time; the page derives words
  from them, cards never carry them.
- `runs.json` lists runs newest-built first; importing under an existing id replaces that run.
- An export in place (the source folder is the destination) is allowed: the files are read
  before they are rewritten.
- The importer streams a folder file by file (the management book is 300 MB of JSON); a
  single-file run or a zip is read whole.
- Stage 2 (2026-11-01): a book definition may declare `target` (T1 / T2 / mm / one_r); a book
  entry may carry `entry` (its own entry time) and `resolution` (a fill known less finely than
  its book). The page's only derived layer is `prep` in `core.js`: flat aliases and day offsets
  from the card's times against the run's daily bars (bars, not calendar days). The page chooses
  the run from `runs.json` (the address carries `run=`; the last choice is remembered in the
  browser). The ladder lists ladder books then groups; Compare lines up the ladder books of ONE
  run; Compare across runs is stage 3.
- Stage 3 (2026-11-01): Compare across runs lines two runs up BY ROLE, never by id: the k-th book
  of each role on each side (headline, target books in order, stop books, reference), each over
  its own universe table with the page's filters; a run with fewer books of a role leaves a gap.
  Run ids start and end with a letter or digit and are not Windows device names; ids differing
  only by case are one run. Instrument names become plain file names (anything outside letters,
  digits, dot, dash, underscore turns into an underscore; collisions and reserved files compared
  without case). An import is staged and swapped in; a refused replacement leaves the old run;
  `recover` restores a run an interrupted import left stepped aside. The single-file flavour is
  recognised inside a zip or a folder too, and a folder mixing the two flavours is refused. The
  flat layout, `build` and `check-run` are gone; `viewer/examples/single_file_run.json` is the
  shipped example of the shape (real bars, the engine's own cards, not a result).
