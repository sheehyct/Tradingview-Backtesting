"""The one-instrument bench: run one's management book on the ES tape, and the bench's receipts
and viewer runs (docs/experiments/tvb43_bench_prereg.md, CONFIRMED by the owner 2026-11-01).

    uv run python -m analysis.bench.run_bench --variant globex    # V0: the Globex day -> run two
    uv run python -m analysis.bench.run_bench --variant rth       # V1: the RTH day    -> run three

Per variant: the tape (`es_tape`), the engine on the session calendar (`census.use_calendar`;
`manage.coin_manage_rows` is untouched), every row with the roll flag the prereg declares, the
same tables as run one's receipt (manage's own table functions on the bench's frame), the
prereg's splits (longs / shorts, the roll flag, the continuity ladder C0 / C1 / C2 read off the
recorded context), and the run in the viewer contract (`run_export.card_from_row` with the
session table) imported beside run one. Outputs under `analysis/bench/results/`: the trades CSV
(ignored, regenerable), `bench_<variant>.json` and `bench_<variant>_tables.md` (committed).

CHARACTERIZATION, NO STRATEGY, NO P&L CLAIM. Nothing here ranks, picks or tunes.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
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
    session inside the headline window after the entry), or None. Never a drop."""
    idx = {d: i for i, d in enumerate(dates)}
    roll_idx = np.array(sorted(idx[d] for d in roll_dates if d in idx))
    for r in rows:
        i = idx[r["date"]]
        if r["date"] in roll_dates:
            r["roll"] = "entry"
            continue
        days = r.get("days")
        if days is None or not len(roll_idx):
            r["roll"] = None
            continue
        lo = np.searchsorted(roll_idx, i, side="right")
        hi = np.searchsorted(roll_idx, i + int(days), side="right")
        r["roll"] = "window" if hi > lo else None


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


# ----------------------------------------------------------------------------- the splits


def _mean_ci(s: pd.Series) -> dict:
    return M._ci(s.dropna()) if len(s.dropna()) else {"n": 0}


def _split_block(df: pd.DataFrame, label: str) -> dict:
    out: dict = {"label": label, "n": int(len(df))}
    for b in BOOK_IDS:
        out[b] = _mean_ci(df[RET_COL[b]]) if RET_COL[b] in df else {"n": 0}
    out["reach1"] = (
        M.share(df["reached1"].fillna(False).astype(bool))
        if "reached1" in df and len(df)
        else M.share(pd.Series(dtype=object))
    )
    return out


def splits(df: pd.DataFrame) -> dict:
    """The prereg's declared splits, per unit timeframe, each with its complement beside it:
    direction, the roll flag, the continuity ladder (C0 every unit; C1 the week's side with the
    trade at entry; C2 the week and the month). Readings, never rankings."""
    out: dict = {}
    for tf in ("D", "W", "M"):
        d = df[df["tf"] == tf]
        if not len(d):
            continue
        blocks = []
        blocks.append(_split_block(d, "all"))
        blocks.append(_split_block(d[d["direction"] == "up"], "longs"))
        blocks.append(_split_block(d[d["direction"] == "down"], "shorts"))
        blocks.append(_split_block(d[d["roll"].isna()], "no roll in the window"))
        blocks.append(_split_block(d[d["roll"] == "entry"], "roll on the entry session"))
        blocks.append(_split_block(d[d["roll"] == "window"], "roll inside the window"))
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


# ----------------------------------------------------------------------------- the run


def run_card(variant: str, tape: es_tape.SessionTape, as_of: str, n_units: int) -> dict:
    v = VARIANTS[variant]
    rules = {
        "setup": "2-2 reversal, 2-2 continuation, inside-bar break and outside-bar break on the session, the week and the month (the domino census's units, on the session calendar)",
        "entry": "the instant the setup bar's high (low) breaks, strictly; weekly and monthly units on the session their level breaks",
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
            f"entry session (entry) or a session inside the headline window (window) is the first on a new "
            f"contract; a roll's price jump is a contract switch, not a move. {len(tape.short_sessions)} sessions "
            f"are shorter than the usual (early closes); they count as sessions. Not exported: "
            + "; ".join(NOT_EXPORTED)
            + ". A book absent from a card does not apply to that trade. Characterization, no strategy, no P&L claim."
        ),
    }


def export_run(
    variant: str, tape: es_tape.SessionTape, rows: list[dict], as_of: str, log=print
) -> str:
    v = VARIANTS[variant]
    run = run_card(variant, tape, as_of, len(rows))
    real = Tape(tape.real_daily, tape.real_hourly, tape.opens_by_date)
    cards = []
    for r in rows:
        c = card_from_row(r, INSTRUMENT, META["dex"], real)
        c["extras"]["roll"] = r.get("roll")
        c["extras"]["hours_traded_h"] = r.get("hours_traded_h")
        cards.append(c)
    ids = [c["id"] for c in cards]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate card ids")
    bars = {"1d": tape.real_daily, "1h": tape.real_hourly}
    if tape.real_weekly:
        bars["1w"] = tape.real_weekly
        bars["1M"] = tape.real_monthly
    folder = DATA / "runs" / v["id"]
    folder.mkdir(parents=True, exist_ok=True)
    with open(folder / "run.json", "w", encoding="utf-8") as fh:
        json.dump(run, fh, indent=1)
    with open(folder / K._fname(INSTRUMENT), "w", encoding="utf-8") as fh:
        json.dump(
            {"instrument": INSTRUMENT, "bars": bars, "trades": cards}, fh, separators=(",", ":")
        )
    return K.import_run(folder, DATA, log=log)


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
    log(
        f"{variant}: {len(rows):,} units in {time.time() - t0:.0f}s; "
        + ", ".join(f"{k} {v:,}" for k, v in sorted(counts.items()))
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
        + f"Roll flag: entry {int((df.roll == 'entry').sum()):,}, window {int((df.roll == 'window').sum()):,}. Drops and anchors: "
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
    md += M.table_candidates(cands)
    sp = splits(df)
    md += table_splits(sp)
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
        "splits": sp,
    }
    (RESULTS / f"bench_{variant}.json").write_text(
        json.dumps(
            summary,
            indent=1,
            default=lambda o: None if isinstance(o, float) and math.isnan(o) else str(o),
        ),
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
