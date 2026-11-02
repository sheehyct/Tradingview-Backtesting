"""The one-instrument bench: run one's management book on the ES tape, and the bench's receipts
and viewer runs (docs/experiments/tvb43_bench_prereg.md, CONFIRMED by the owner 2026-11-01;
section 9, the entry fill, owner-ruled 2026-11-02).

    uv run python -m analysis.bench.run_bench --variant globex    # V0: the Globex day -> run two
    uv run python -m analysis.bench.run_bench --variant rth       # V1: the RTH day    -> run three

Per variant: the tape (`es_tape`), the engine on the session calendar (`census.use_calendar`;
`manage.coin_manage_rows` is untouched), every row with the roll flag the prereg declares (the
HEADLINE window; `roll_ref` the chance book's own window beside it as a diagnostic), the gap flag
and the open-fill re-measurement of amendment 2026-11-02 (the control's rows never change: the
open-fill is a second column set on the same exits, the missed-entry a subset), the same tables
as run one's receipt (manage's own table functions on the bench's frame), the prereg's splits
(longs / shorts, the roll flag, the continuity ladder C0 / C1 / C2 read off the recorded
context), the entry-fill pair, and the run in the viewer contract (`run_export.card_from_row`
with the session table) imported beside run one. Outputs under `analysis/bench/results/`: the
trades CSV (ignored, regenerable), `bench_<variant>.json` and `bench_<variant>_tables.md`
(committed).

CHARACTERIZATION, NO STRATEGY, NO P&L CLAIM. Nothing here ranks, picks or tunes.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.bench import es_tape
from analysis.domino import contract as K
from analysis.domino import manage as M
from analysis.domino.census import HOUR as HOUR_MS
from analysis.domino.census import use_calendar
from analysis.domino.run_export import BOOKS, NOT_EXPORTED, Tape, card_from_row, git_commit
from analysis.domino.trade_viewer import DATA

HERE = Path(__file__).parent
RESULTS = HERE / "results"
INSTRUMENT = "ES"
META = {"coin": INSTRUMENT, "dex": "cme", "liquid": True}
BOOK_IDS = ("C", "A", "B", "D", "D5", "ref")
RET_COL = {"C": "ret_C", "A": "ret_A", "B": "ret_B", "D": "ret_D", "D5": "ret_D5", "ref": "ret5"}

# amendment 2026-11-02: the books the entry-fill pair re-measures (id, the control's return column,
# the column that says the book filled its target; "out5" is the chance book's outcome word)
GAP_BOOKS = (
    ("C", "ret_C", None),
    ("A", "ret_A", "hit_A"),
    ("B", "ret_B", "hit_B"),
    ("D", "ret_D", "hit_D"),
    ("D5", "ret_D5", "hit_D5"),
    ("ref", "ret_ref", "out5"),
    ("C_h", "ret_C_h", None),
    ("A_h", "ret_A_h", "hit_A_h"),
    ("D_h", "ret_D_h", "hit_D_h"),
)
FILL_IDS = tuple(b for b, _, _ in GAP_BOOKS)
FILL_RET = {b: rc for b, rc, _ in GAP_BOOKS}
FILL_HIT = {b: hc for b, _, hc in GAP_BOOKS}
OF_RET = {b: "of_" + rc for b, rc, _ in GAP_BOOKS}
FILL_HEAD = (
    "| rows | n | C exit only | A all out at T1 | B through T2 | D one R or exit | D5 five bars | "
    "chance book | C_h hourly clock | A_h hourly T1 | D_h hourly one R |"
)

BENCH_FOOTER = (
    "Each candidate is one change to the headline on the same rows (run one's prereg amendment A2, "
    "read here on the ES tape); the paired differences are mean and normal 95% interval of the "
    "per-trade difference. The hourly arm is the subset of rows whose entry session had an hour "
    "through the level (the whole tape: the hourly clock reads the cache's 60-minute bars by "
    "session); its targets fill only from the entry hour on, so it differs from the session books "
    "by the clock AND by that ordering. Gross of every cost: no fees, no commission, no financing "
    "or margin arithmetic are modelled on the futures tape; the stop-swap difference is "
    "cost-neutral either way."
)

VARIANTS = {
    "globex": {
        "id": "es-globex-2011-2025",
        "name": "The management book on ES, the Globex day (V0), 2011-2025",
        "clock": {
            "day_roll": "18:00 ET",
            "resolution": "day",
            "weeks": "Sunday 18:00 ET through Friday 17:00 ET (the Monday to Friday trade dates)",
            "months": "calendar, by trade date",
            "label_shift_hours": es_tape.GLOBEX_LABEL_SHIFT_H,
            "calendar": "session",
        },
        "day_word": "the Globex session (18:00 ET open, 17:00 ET close the next afternoon)",
    },
    "rth": {
        "id": "es-rth-2011-2025",
        "name": "The management book on ES, the regular-hours day (V1), 2011-2025",
        "clock": {
            "day_roll": "09:30 ET",
            "resolution": "day",
            "weeks": "Monday to Friday regular sessions",
            "months": "calendar, by trade date",
            "label_shift_hours": 0,
            "calendar": "session",
        },
        "day_word": "the regular session (09:30 to 16:00 ET)",
    },
}


# ----------------------------------------------------------------------------- the rows


def roll_flags(rows: list[dict], dates: list[str], roll_dates: set[str]) -> None:
    """Prereg section 2.5: `roll` = entry (the entry session is a roll session), window (a roll
    session inside the HEADLINE window, the entry through C's exit or cap), or None. Never a
    drop. `roll_ref` reads the same way over the chance book's own window (the entry through its
    stop, one R or fifth-bar mark): a diagnostic beside the declared flag (audit F4), because a
    null `roll` says nothing about a book whose window is longer than C's."""
    idx = {d: i for i, d in enumerate(dates)}
    roll_idx = np.array(sorted(idx[d] for d in roll_dates if d in idx))

    def flag(i: int, days) -> str | None:
        if days is None or not len(roll_idx):
            return None
        lo = np.searchsorted(roll_idx, i, side="right")
        hi = np.searchsorted(roll_idx, i + int(days), side="right")
        return "window" if hi > lo else None

    for r in rows:
        i = idx[r["date"]]
        if r["date"] in roll_dates:
            r["roll"] = r["roll_ref"] = "entry"
            continue
        r["roll"] = flag(i, r.get("days"))
        r["roll_ref"] = flag(i, r.get("days_ref"))


def traded_hours(rows: list[dict], hourly: list[dict]) -> None:
    """The hourly clock's hold in TRADED hours (`hours_h` is session time, with the weekend's empty
    hours in it): the count of the tape's hours after the entry hour through the exit hour."""
    ts = np.array([b["t"] for b in hourly], dtype=np.int64)
    for r in rows:
        if r.get("entry_h") is None or r.get("hours_h") is None:
            r["hours_traded_h"] = None
            continue
        t0 = es_tape.session_ms(r["date"]) + int(r["entry_h"]) * HOUR_MS
        t1 = t0 + int(r["hours_h"]) * HOUR_MS
        r["hours_traded_h"] = int(
            np.searchsorted(ts, t1, side="right") - np.searchsorted(ts, t0, side="right")
        )


def gap_flags(rows: list[dict], sessions: dict[str, dict]) -> None:
    """Amendment 2026-11-02 (audit F1): `gap` = "open" when the entry session OPENS strictly beyond
    the trigger in the trade direction (the trigger was not a fill the session offered at the
    open; the engine's books measure from it anyway), "untraded" when the whole session's range
    is beyond it (the trigger never printed), else None. `session_open` = the entry session's
    open, the open-fill's price. `sessions` maps a trade date to its engine bar (o, h, l)."""
    for r in rows:
        b = sessions[r["date"]]
        o, lv, up = b["o"], r["level"], r["direction"] == "up"
        r["session_open"] = o
        if (o > lv) if up else (o < lv):
            r["gap"] = "untraded" if ((b["l"] > lv) if up else (b["h"] < lv)) else "open"
        else:
            r["gap"] = None


def _missing(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))


def _hit(r: dict, key: str | None) -> bool:
    if key is None:
        return False
    if key == "out5":
        return r.get("out5") == "one_r"
    v = r.get(key)
    return bool(v) if isinstance(v, (bool, int, np.bool_, np.integer)) else False


def open_fill(rows: list[dict]) -> None:
    """Amendment 2026-11-02, F1: for every book in GAP_BOOKS an `of_<ret>` column. On a unit that
    does not gap it is the control's value, untouched. On a gap unit each book's recorded exit
    price is recovered from the control's return (percent of the trigger, exact) and the book is
    re-measured from the session's open; a target fill at or behind the open is reached at the
    entry: the trade opens and closes at the open, zero. Every price and every exit path stays
    the control's: the fill is the one change."""
    for r in rows:
        gap, up = r.get("gap"), r["direction"] == "up"
        sign, lv, e = (1.0 if up else -1.0), float(r["level"]), r.get("session_open")
        for b in FILL_IDS:
            rc = FILL_RET[b]
            ret = r.get(rc)
            if gap is None or _missing(ret):
                r[OF_RET[b]] = ret
                continue
            exit_p = lv * (1.0 + sign * float(ret) / 100.0)
            if _hit(r, FILL_HIT[b]) and ((exit_p <= e) if up else (exit_p >= e)):
                r[OF_RET[b]] = 0.0
            else:
                r[OF_RET[b]] = sign * (exit_p - e) / e * 100.0


# ----------------------------------------------------------------------------- the splits


def _mean_ci(s: pd.Series) -> dict:
    return M._ci(s.dropna()) if len(s.dropna()) else {"n": 0}


def _split_block(
    df: pd.DataFrame, label: str, cols: dict | None = None, books: tuple = BOOK_IDS
) -> dict:
    cols = cols or RET_COL
    out: dict = {"label": label, "n": int(len(df))}
    for b in books:
        out[b] = _mean_ci(df[cols[b]]) if cols[b] in df else {"n": 0}
    if cols is RET_COL:
        out["reach1"] = (
            M.share(df["reached1"].fillna(False).astype(bool))
            if "reached1" in df and len(df)
            else M.share(pd.Series(dtype=object))
        )
    return out


def splits(df: pd.DataFrame) -> dict:
    """The prereg's declared splits, per unit timeframe, each with its complement beside it:
    direction, the roll flag (the headline window; the chance book's own window as a diagnostic),
    the continuity ladder (C0 every unit; C1 the week's side with the trade at entry; C2 the week
    and the month). Readings, never rankings."""
    out: dict = {}
    for tf in ("D", "W", "M"):
        d = df[df["tf"] == tf]
        if not len(d):
            continue
        blocks = []
        blocks.append(_split_block(d, "all"))
        blocks.append(_split_block(d[d["direction"] == "up"], "longs"))
        blocks.append(_split_block(d[d["direction"] == "down"], "shorts"))
        blocks.append(_split_block(d[d["roll"].isna()], "no roll through C's window (headline)"))
        blocks.append(_split_block(d[d["roll"] == "entry"], "roll on the entry session"))
        blocks.append(_split_block(d[d["roll"] == "window"], "roll inside C's window"))
        blocks.append(
            _split_block(
                d[d["roll"].isna() & d["roll_ref"].isna()],
                "no roll through C's window nor the chance book's own (diagnostic)",
            )
        )
        c1 = d["w_support"] == "with"
        c2 = c1 & (d["m_support"] == "with")
        blocks.append(_split_block(d, "C0: every unit"))
        blocks.append(_split_block(d[c1], "C1: the week with the trade at entry"))
        blocks.append(_split_block(d[~c1], "C1 complement: the week against or unknown"))
        blocks.append(_split_block(d[c2], "C2: the week and the month with the trade"))
        blocks.append(_split_block(d[~c2], "C2 complement"))
        out[tf] = blocks
    return out


def table_splits(sp: dict) -> list[str]:
    md = []
    for tf, blocks in sp.items():
        md += [
            f"## Declared splits, {M.PATTERN_TFS and tf} units: percent per trade, every book, each split with its complement",
            "",
            "| split | n | C exit only | A all out at T1 | B through T2 | D one R or exit | D5 five bars | chance book | T1 reached |",
            "|---|---:|---|---|---|---|---|---|---|",
        ]
        for b in blocks:
            md.append(
                f"| {b['label']} | {b['n']:,} | "
                + " | ".join(M._ci_s(b[k]) for k in BOOK_IDS)
                + f" | {M._sh(b['reach1'])} |"
            )
        md.append("")
    return md


def _at_entry(g: pd.DataFrame, b: str) -> int:
    """How many gap units the book filled at a target the open had already passed (zero under
    the open-fill): the same test `open_fill` applies, over the frame."""
    rc, hc = FILL_RET[b], FILL_HIT[b]
    if hc is None or rc not in g or (hc != "out5" and hc not in g) or not len(g):
        return 0
    hit = (g["out5"] == "one_r") if hc == "out5" else g[hc].fillna(False).astype(bool)
    up = (g["direction"] == "up").to_numpy()
    sign = np.where(up, 1.0, -1.0)
    ret = g[rc].astype(float)
    exit_p = g["level"].astype(float) * (1.0 + sign * ret / 100.0)
    o = g["session_open"].astype(float)
    behind = pd.Series(np.where(up, exit_p <= o, exit_p >= o), index=g.index)
    return int((hit & behind & ret.notna()).sum())


def fill_blocks(df: pd.DataFrame) -> dict:
    """Amendment 2026-11-02: per unit timeframe, every book under the control (F0, the trigger),
    the open-fill (F1) and the missed-entry (F2, the control on the units that do not gap); the
    gap units alone under both, with the paired difference control minus open-fill on the same
    rows; the never-printed units; longs and shorts under the open-fill. Readings, never rankings."""
    out: dict = {}
    for tf in ("D", "W", "M"):
        d = df[df["tf"] == tf]
        if not len(d):
            continue
        gap = d[d["gap"].notna()]
        unt = d[d["gap"] == "untraded"]
        nog = d[d["gap"].isna()]
        blocks = [
            _split_block(d, "all units, at the trigger (F0, the control)", FILL_RET, FILL_IDS),
            _split_block(d, "all units, open-fill (F1)", OF_RET, FILL_IDS),
            _split_block(
                nog,
                "missed-entry (F2): the units that do not gap, at the trigger",
                FILL_RET,
                FILL_IDS,
            ),
            _split_block(
                gap,
                "gap at the open: at the trigger (a price the session did not offer at the open)",
                FILL_RET,
                FILL_IDS,
            ),
            _split_block(gap, "gap at the open: open-fill", OF_RET, FILL_IDS),
            _split_block(unt, "trigger never printed: at the trigger", FILL_RET, FILL_IDS),
            _split_block(unt, "trigger never printed: open-fill", OF_RET, FILL_IDS),
            _split_block(d[d["direction"] == "up"], "longs, open-fill", OF_RET, FILL_IDS),
            _split_block(d[d["direction"] == "down"], "shorts, open-fill", OF_RET, FILL_IDS),
            _split_block(nog[nog["direction"] == "up"], "longs, missed-entry", FILL_RET, FILL_IDS),
            _split_block(
                nog[nog["direction"] == "down"], "shorts, missed-entry", FILL_RET, FILL_IDS
            ),
        ]
        paired = {
            b: (
                M.paired(gap[FILL_RET[b]], gap[OF_RET[b]])
                if FILL_RET[b] in gap and OF_RET[b] in gap
                else {"n": 0}
            )
            for b in FILL_IDS
        }
        out[tf] = {
            "n": int(len(d)),
            "gap": int(len(gap)),
            "untraded": int(len(unt)),
            "blocks": blocks,
            "control_minus_open_fill_on_gap_units": paired,
            "reached_at_entry": {b: _at_entry(gap, b) for b in FILL_IDS},
        }
    return out


def _pd(p: dict) -> str:
    if not p or not p.get("n") or p["n"] < 2:
        return "-"
    return f"{p['diff']:+.2f} [{p['lo']:+.2f}, {p['hi']:+.2f}] n={p['n']:,}"


def table_fill(fb: dict) -> list[str]:
    md = []
    for tf, f in fb.items():
        md += [
            f"## Amendment 2026-11-02: the entry fill, {tf} units: the trigger (F0, control), the open (F1), no trade (F2); percent per trade",
            "",
            f"{f['n']:,} units; {f['gap']:,} open past the trigger in the trade direction, of which "
            f"{f['untraded']:,} never print the trigger inside the session. The control's rows are "
            "untouched: the open-fill is a second measurement of the same exits from the session's open, "
            "the missed-entry the control on the units that do not gap. Both directions; nothing picked.",
            "",
            FILL_HEAD,
            "|---|---:|---|---|---|---|---|---|---|---|---|",
        ]
        for b in f["blocks"]:
            md.append(
                f"| {b['label']} | {b['n']:,} | "
                + " | ".join(M._ci_s(b[k]) for k in FILL_IDS)
                + " |"
            )
        p, z = f["control_minus_open_fill_on_gap_units"], f["reached_at_entry"]
        md.append(
            f"| control minus open-fill on the gap units, paired | {f['gap']:,} | "
            + " | ".join(_pd(p[k]) for k in FILL_IDS)
            + " |"
        )
        md.append(
            f"| target behind the open, counted as reached at the entry (zero) | {f['gap']:,} | "
            + " | ".join("-" if FILL_HIT[k] is None else f"{z[k]:,}" for k in FILL_IDS)
            + " |"
        )
        md.append("")
    return md


# ----------------------------------------------------------------------------- the run


def run_card(
    variant: str,
    tape: es_tape.SessionTape,
    as_of: str,
    n_units: int,
    n_gap: int = 0,
    n_untraded: int = 0,
) -> dict:
    v = VARIANTS[variant]
    rules = {
        "setup": "2-2 reversal, 2-2 continuation, inside-bar break and outside-bar break on the session, the week and the month (the domino census's units, on the session calendar)",
        "entry": (
            "the instant the setup bar's high (low) breaks, strictly; weekly and monthly units on the "
            "session their level breaks. Where the entry session OPENS past the trigger (extras.gap: "
            "open; untraded when the trigger never printed in the session) the books still measure "
            "from the trigger, a price the session did not offer at the open: the receipt's amendment "
            "2026-11-02 shows the open-fill and the missed-entry readings beside them."
        ),
        "stop": "none for the management books; the setup bar's far side for the chance book (and the one-R yardstick for every book)",
        "targets": "T1 the pattern's own magnitude or the first unbroken weekly / monthly level beyond the entry, T2 / T3 the next unbroken levels, fixed at entry; the measured move beside them",
        "exit": f"a session close against the trade with the week also against it at that close; 20-session cap (other clocks as grouped books). The day is {v['day_word']}.",
        "continuity": "none gated; the week's and month's side at entry are recorded on the card (the prereg's C1 / C2 split reads them)",
    }
    return {
        "contract": K.CONTRACT,
        "id": v["id"],
        "name": v["name"],
        "as_of": as_of,
        "source": {
            "repo": "tradingview-backtesting",
            "commit": git_commit(),
            "command": f"uv run python -m analysis.bench.run_bench --variant {variant}",
            "data": f"Databento GLBX MDP3 {tape.symbol}, 1-minute source resampled in vectorbt-workspace/data/databento_cache",
        },
        "clock": dict(v["clock"]),
        "units": ["D", "W", "M"],
        "bars": ["1h", "1d"] + (["1w", "1M"] if tape.real_weekly else []),
        "returns": "percent of price, equal size, no fees, no leverage, no margin arithmetic",
        "rules": rules,
        "books": [dict(b) for b in BOOKS],
        "notes": (
            f"The one-instrument bench (docs/experiments/tvb43_bench_prereg.md): run one's seventeen books, "
            f"unchanged, on {INSTRUMENT} ({tape.symbol}, continuous front month by open interest, unadjusted) "
            f"where the day is {v['day_word']}. {n_units:,} units. The card's `extras.roll` says whether the "
            f"entry session (entry) or a session inside the headline window, the entry through C's exit or "
            f"cap (window), is the first on a new contract; `extras.roll_ref` reads the chance book's own "
            f"window the same way; a roll's price jump is a contract switch, not a move. {n_gap:,} units "
            f"open past the trigger ({n_untraded:,} never print it inside the session): their books are "
            f"level-to-exit measurements, flagged on the card (`extras.gap`, `extras.session_open`) and "
            f"re-measured from the open in the receipt's amendment 2026-11-02 pair. "
            f"{len(tape.short_sessions)} sessions are shorter than the usual (early closes); they count as "
            f"sessions. Not exported: "
            + "; ".join(NOT_EXPORTED)
            + ". A book absent from a card does not "
            "apply to that trade. Characterization, no strategy, no P&L claim."
        ),
    }


def export_run(
    variant: str,
    tape: es_tape.SessionTape,
    rows: list[dict],
    as_of: str,
    log=print,
    data: Path = DATA,
) -> str:
    """The run in the viewer contract. The source is serialized into a temporary folder beside
    the runs and handed to the staged importer, so a failed write or a refused run leaves a
    registered run of the same id byte-identical (audit F2: the exporter used to open the live
    run's files for writing before the importer could protect them)."""
    n_gap = sum(1 for r in rows if r.get("gap"))
    n_unt = sum(1 for r in rows if r.get("gap") == "untraded")
    run = run_card(variant, tape, as_of, len(rows), n_gap, n_unt)
    real = Tape(tape.real_daily, tape.real_hourly, tape.opens_by_date)
    cards = []
    for r in rows:
        c = card_from_row(r, INSTRUMENT, META["dex"], real)
        for k in ("roll", "roll_ref", "hours_traded_h", "gap", "session_open"):
            c["extras"][k] = r.get(k)
        cards.append(c)
    ids = [c["id"] for c in cards]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate card ids")
    bars = {"1d": tape.real_daily, "1h": tape.real_hourly}
    if tape.real_weekly:
        bars["1w"] = tape.real_weekly
        bars["1M"] = tape.real_monthly
    data.mkdir(parents=True, exist_ok=True)
    src = Path(tempfile.mkdtemp(prefix=".export-", dir=data))
    try:
        with open(src / "run.json", "w", encoding="utf-8") as fh:
            json.dump(run, fh, indent=1)
        with open(src / K._fname(INSTRUMENT), "w", encoding="utf-8") as fh:
            json.dump(
                {"instrument": INSTRUMENT, "bars": bars, "trades": cards},
                fh,
                separators=(",", ":"),
            )
        return K.import_run(src, data, log=log)
    finally:
        shutil.rmtree(src, ignore_errors=True)


def _finite(o):
    """Strict JSON: NaN and infinities become null, numpy scalars plain Python."""
    if isinstance(o, dict):
        return {k: _finite(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_finite(v) for v in o]
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, (float, np.floating)):
        return None if (math.isnan(o) or math.isinf(o)) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    return o


# ----------------------------------------------------------------------------- main


def run(variant: str, do_export: bool = True, log=print) -> dict:
    t0 = time.time()
    tape = es_tape.load(variant)
    as_of = tape.dates[-1]
    log(
        f"{variant}: {len(tape.daily):,} sessions {tape.dates[0]} to {as_of}, {len(tape.hourly):,} hours, "
        f"{len(tape.roll_dates)} roll sessions, {len(tape.short_sessions)} short sessions ({time.time() - t0:.0f}s)"
    )
    with use_calendar("session"):
        rows, counts = M.coin_manage_rows(META, tape.daily, tape.hourly)
    roll_flags(rows, tape.dates, tape.roll_dates)
    traded_hours(rows, tape.hourly)
    gap_flags(rows, dict(zip(tape.dates, tape.daily)))
    open_fill(rows)
    n_gap = sum(1 for r in rows if r.get("gap"))
    n_unt = sum(1 for r in rows if r.get("gap") == "untraded")
    log(
        f"{variant}: {len(rows):,} units in {time.time() - t0:.0f}s; "
        + ", ".join(f"{k} {v:,}" for k, v in sorted(counts.items()))
        + f"; {n_gap:,} open past the trigger ({n_unt:,} never print it)"
    )
    RESULTS.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    with gzip.open(
        RESULTS / f"bench_{variant}_trades.csv.gz", "wt", newline="", encoding="utf-8"
    ) as fh:
        df.to_csv(fh, index=False)
    # the tables, exactly run one's (the hourly hold shown in traded hours, not session time)
    tdf = df.copy()
    if "hours_traded_h" in tdf:
        tdf["hours_h"] = tdf["hours_traded_h"]
    cells, clocks = M.compute(tdf)
    cands = M.candidates(tdf)
    md = [
        f"# The management book on {INSTRUMENT}, {VARIANTS[variant]['name']} (generated by analysis/bench/run_bench.py; the session calendar)",
        "",
        f"{len(df):,} units ("
        + ", ".join(f"{tf} {int((df.tf == tf).sum()):,}" for tf in M.PATTERN_TFS)
        + f") on {len(tape.daily):,} sessions {tape.dates[0]} to {as_of}. Headline: the session clock, cap {M.CAP} sessions. "
        + f"Roll flag (C's window): entry {int((df.roll == 'entry').sum()):,}, window {int((df.roll == 'window').sum()):,}. "
        + f"Gap flag: {n_gap:,} units open past the trigger, {n_unt:,} never print it (the books below "
        + "measure from the trigger on those; the amendment 2026-11-02 block at the end re-measures them). Drops and anchors: "
        + ", ".join(f"{k} {v:,}" for k, v in sorted(counts.items()))
        + ". The hourly clock's hold is in TRADED hours. Characterization, no strategy, no P&L claim; every split shown with its complement.",
        "",
    ]
    for tf, name in (("D", "session"), ("W", "weekly"), ("M", "monthly")):
        if not int((df.tf == tf).sum()):
            continue
        md += M.table_reach(tdf, tf, f"Reach rates, {name} units", cells)
        md += M.table_deaths(tdf, tf, f"How the pre-T1 exits died, {name} units", cells)
        md += M.table_tail(tdf, tf, f"The tail, {name} units", cells)
        md += M.table_books(tdf, tf, f"The books, {name} units", cells)
    md += M.table_books(
        tdf,
        "D",
        "The books, session units, hammer / shooter flag",
        cells,
        levels=("third", "strict"),
    )
    md += M.table_mm(tdf, "D", "Fork 1: the measured move beside the level, session units", cells)
    md += M.table_mm(tdf, "W", "Fork 1: the measured move beside the level, weekly units", cells)
    md += M.table_clocks(tdf, "W", "Fork 2: the exit clock, weekly units", clocks)
    md += M.table_clocks(tdf, "M", "Fork 2: the exit clock, monthly units", clocks)
    md += M.table_hypotheses(cells)
    md += M.table_candidates(cands, footer=BENCH_FOOTER)
    sp = splits(df)
    md += table_splits(sp)
    fb = fill_blocks(df)
    md += table_fill(fb)
    (RESULTS / f"bench_{variant}_tables.md").write_text("\n".join(md), encoding="utf-8")
    summary = {
        "variant": variant,
        "run_id": VARIANTS[variant]["id"],
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "sessions": len(tape.daily),
        "first": tape.dates[0],
        "last": as_of,
        "hours": len(tape.hourly),
        "roll_sessions": sorted(tape.roll_dates),
        "short_sessions": dict(sorted(tape.short_sessions.items())),
        "units": int(len(df)),
        "units_by_tf": {tf: int((df.tf == tf).sum()) for tf in M.PATTERN_TFS},
        "counts": dict(sorted(counts.items())),
        "roll": {k: int((df.roll == k).sum()) for k in ("entry", "window")},
        "roll_ref": {k: int((df.roll_ref == k).sum()) for k in ("entry", "window")},
        "gap": {
            "open_or_untraded": n_gap,
            "untraded": n_unt,
            "by_tf": {
                tf: {
                    "gap": int(((df.tf == tf) & df.gap.notna()).sum()),
                    "untraded": int(((df.tf == tf) & (df.gap == "untraded")).sum()),
                }
                for tf in M.PATTERN_TFS
            },
        },
        "splits": sp,
        "fill": fb,
    }
    (RESULTS / f"bench_{variant}.json").write_text(
        json.dumps(_finite(summary), indent=1, allow_nan=False, default=str),
        encoding="utf-8",
    )
    log(f"{variant}: tables and summary -> {RESULTS}")
    if do_export:
        rid = export_run(variant, tape, rows, as_of, log)
        log(f"{variant}: imported as run {rid} ({time.time() - t0:.0f}s)")
        summary["imported"] = rid
    return summary


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--variant", choices=sorted(VARIANTS), required=True)
    ap.add_argument(
        "--no-export", action="store_true", help="tables and summary only; no viewer run"
    )
    args = ap.parse_args(argv)
    run(args.variant, not args.no_export)


if __name__ == "__main__":
    main()
