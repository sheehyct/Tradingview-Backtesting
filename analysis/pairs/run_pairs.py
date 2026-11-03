"""The matched-pair study, run (prereg docs/experiments/tvb44_matched_pairs_prereg.md, confirmed
by the owner 2026-11-02; section 12, the in-session Codex pass folded): the pre-entry variables
on run one's rows (292 perps), bitcoin alone, and the ES bench's two days (the clean-fill units
first, every unit beside them), the readings per cell and pooled, the owner's theme rule, the
book view, the tables and the JSON.

    uv run python -m analysis.pairs.run_pairs            # about ninety seconds

Outputs under `analysis/pairs/results/`: the rows with the variables (`pairs_rows_*.csv.gz`) and
the per-cell readings (`pairs_cells.json`), both ignored and regenerable; `pairs.json` and
`pairs_tables.md` (committed). The receipt (`analysis/pairs/PAIRS_RECEIPT.md`) is written by
hand from them.

CHARACTERIZATION, NO SELECTOR, NO ENGINE CHANGE. Every variable is reported whether it separates
or not; nothing here ranks, picks or tunes."""

from __future__ import annotations

import gzip
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.bench import es_tape
from analysis.domino.census import cached_universe, normalize, use_calendar
from analysis.domino.chance import venue_era
from analysis.domino.trade_viewer import cache_path
from analysis.pairs import cells as X
from analysis.pairs.features import (
    BAR_VARS,
    CATEGORY,
    NUMERIC,
    VARS,
    IndexState,
    TapeVars,
    card_vars,
    date_of,
    month_side,
    week_position,
    weekday_of,
)

HERE = Path(__file__).parent
RESULTS = HERE / "results"
RUN_ONE = HERE.parent / "domino" / "results" / "manage_trades.csv.gz"
BENCH = HERE.parent / "bench" / "results"
AS_OF = "2026-10-10"
AS_OF_MS = int(datetime(2026, 10, 10, tzinfo=timezone.utc).timestamp() * 1000)
MIN_N = {"crypto": 200, "btc": 50, "es": 50}
UNIT_USD = 1000.0
ROW_COLS = [
    "coin",
    "dex",
    "liquid",
    "date",
    "direction",
    "tf",
    "kind",
    "flag",
    "cls",
    "near_tf",
    "stack",
    "level",
    "stop",
    "r_pct",
    "t1",
    "anchor",
    "ladder_len",
    "w_support",
    "m_support",
    "reached1",
    "ret_C",
    "ret_D",
    "status",
]
ORDER = ["crypto", "btc", "es_globex_clean", "es_rth_clean", "es_globex_all", "es_rth_all"]
BOOK_TAPES = ["crypto", "btc", "es_globex_clean", "es_rth_clean"]


def _bars_crypto(coin: str) -> list[dict]:
    """The coin's closed daily bars as the engine saw them: the census cache as of the run,
    trimmed to the venue era (the venue's earlier candles are index prices; the engine drops
    them before it makes any unit, so the variables read the same history)."""
    p = cache_path(coin, "1d", AS_OF_MS)
    return venue_era(normalize(json.load(open(p, encoding="utf-8")), AS_OF_MS))


def build_vars(
    rows: pd.DataFrame, bars_of, index: IndexState | None, session: bool, log=print
) -> pd.DataFrame:
    """The variables appended to the rows, instrument by instrument: the bar-based ones from
    `TapeVars` on the unit's own timeframe, the week position (session tape) or the weekday
    (24/7 tape), the index state (crypto), the card's own fields; the month side of weekly and
    monthly units rebuilt from the unit's own trigger (the engine's label is kept as
    `m_support_engine`)."""
    out = []
    t0 = time.time()
    for n, (coin, g) in enumerate(rows.groupby("coin", sort=True)):
        daily = bars_of(coin)
        idx = {date_of(b["t"]): i for i, b in enumerate(daily)}
        tapes = {tf: TapeVars(daily, tf) for tf in ("D", "W", "M")}
        wk: dict = {}
        for _, r in g.iterrows():
            rec = r.to_dict()
            i = idx.get(r["date"])
            rec.update(card_vars(rec))
            rec["m_support_engine"] = rec.get("m_support")
            if i is None:
                rec.update({k: None for k in BAR_VARS})
                rec["v_week"] = None
            else:
                rec.update(tapes[r["tf"]].at(i, r["direction"], float(r["level"]), r.get("r_pct")))
                if r["tf"] in ("W", "M"):
                    rec["m_support"] = month_side(daily, i, float(r["level"]), r["direction"])
                if session:
                    if i not in wk:
                        wk[i] = week_position(daily, i)
                    rec["v_week"] = wk[i]
                else:
                    rec["v_week"] = weekday_of(r["date"])
            rec["v_index"] = index.at(r["date"]) if index is not None else None
            out.append(rec)
        if (n + 1) % 50 == 0:
            log(f"  {n + 1} instruments, {len(out):,} units ({time.time() - t0:.0f}s)")
    return pd.DataFrame(out)


def load_run_one() -> pd.DataFrame:
    return pd.read_csv(gzip.open(RUN_ONE, "rt"), usecols=ROW_COLS, low_memory=False)


def load_bench(variant: str) -> pd.DataFrame:
    return pd.read_csv(
        gzip.open(BENCH / f"bench_{variant}_trades.csv.gz", "rt"),
        usecols=ROW_COLS + ["gap"],
        low_memory=False,
    )


# ----------------------------------------------------------------------------- tables


def _p(x, fmt="+.2f") -> str:
    return "-" if x is None or (isinstance(x, float) and not math.isfinite(x)) else format(x, fmt)


def _pct(x) -> str:
    return (
        "-" if x is None or (isinstance(x, float) and not math.isfinite(x)) else f"{100 * x:.1f}%"
    )


def _pool(p: dict | None, pct=True) -> str:
    if not p or not math.isfinite(p.get("diff", math.nan)):
        return "-"
    if pct:
        return f"{100 * p['diff']:+.1f} pp [{100 * p['lo']:+.1f}, {100 * p['hi']:+.1f}] ({p['cells']} cells)"
    return f"{p['diff']:+.2f} [{p['lo']:+.2f}, {p['hi']:+.2f}] ({p['cells']} cells)"


def _lv_row(tape: str, lv, s: dict) -> str:
    return (
        f"| {tape} | {lv} | {s['n']:,} | {_pct(s['has_t1'])} | {_pct(s['reach'])} | {_p(s['C'])} |"
    )


def table_variable(var: str, by_tape: dict[str, dict], order: list[str]) -> list[str]:
    _, label = VARS[var]
    md = [
        f"### {label} (`{var}`)",
        "",
        "| tape | level | n | has a T1 | T1 reached (of those) | C exit only |",
        "|---|---|---:|---|---|---|",
    ]
    for tape in order:
        r = by_tape[tape].get(var)
        if not r:
            continue
        first = f"{tape} ({r['units']:,} units, {r['absent']:,} absent)"
        for lv in r["levels"]:
            s = r["standardized"].get(lv)
            if not s:
                continue
            md.append(_lv_row(first, lv, s))
            first = ""
        if r["pooled"]:
            p = r["pooled"]
            md.append(
                f"| {first} | high minus low, pooled by cell | | {_pool(p['has_t1'])} | {_pool(p['reach'])} | "
                f"{_pool(p['C'], pct=False)}; one R {_pool(p['D'], pct=False)} |"
            )
            first = ""
        if r["other"]:
            o = r["other"]
            for lv, s in o["levels"].items():
                md.append(
                    f"| {first} | other ({o['cells']} cells below the minimum, {o['n']:,} units): {lv} | {s['n']:,} | "
                    f"{_pct(s['has_t1']['p'])} | {_pct(s['reach']['p'])} | {_p(s['C']['avg'])} |"
                )
                first = ""
    md.append("")
    return md


def _sign_cell(s: dict | None) -> str:
    if not s:
        return "-"
    return f"{100 * s['diff']:+.1f} [{100 * s['lo']:+.1f}, {100 * s['hi']:+.1f}]{' *' if s['clear'] else ''}"


def table_themes(th: dict, order: list[str]) -> list[str]:
    md = [
        "## The owner's theme rule: same direction on the crypto run AND an ES clean-fill day, both intervals clear",
        "",
        "Per variable, the pooled high-minus-low difference in T1 reach (percentage points, over the units that have a first target) on every tape; `theme` when the rule holds. A variable that separates on one tape only is a reading there, not a theme.",
        "",
        "| variable | theme | with | " + " | ".join(order) + " |",
        "|---|---|---|" + "---|" * len(order),
    ]
    for var, t in th.items():
        md.append(
            f"| `{var}` | {'THEME' if t['theme'] else 'no'} | {t['with'] or '-'} | "
            + " | ".join(_sign_cell(t["signs"].get(tape)) for tape in order)
            + " |"
        )
    md += [
        "",
        "The same reading for the share of units that HAVE a first target at all (high minus low, percentage points; not part of the rule, the fact the reach outcome is conditioned on):",
        "",
        "| variable | " + " | ".join(order) + " |",
        "|---|" + "---|" * len(order),
    ]
    for var, t in th.items():
        md.append(
            f"| `{var}` | " + " | ".join(_sign_cell(t["has_t1"].get(tape)) for tape in order) + " |"
        )
    md += [
        "",
        "`*` = the interval is clear of zero. Categories with more than two levels have no high-minus-low and read per level in their own table.",
        "",
    ]
    return md


def book_view(d: pd.DataFrame, var: str) -> dict:
    """The equal-size exit-only book per level of a variable (the owner's standing preference):
    units, average percent per trade, total USD at 1,000 per unit, the share of green trades."""
    col = X.tercile(d, var) if var in NUMERIC else d[var]
    out = {}
    for lv in X.levels_of(var, d, col):
        sub = d[(col == lv) & d["ret_C"].notna()]
        if not len(sub):
            continue
        r = sub["ret_C"].astype(float)
        out[str(lv)] = {
            "n": int(len(sub)),
            "avg": float(r.mean()),
            "total_usd": float(r.sum() * UNIT_USD / 100.0),
            "green": float((r > 0).mean()),
        }
    return out


def table_books(books: dict, order: list[str]) -> list[str]:
    md = [
        "## The book view: the equal-size exit-only book per level, 1,000 USD a unit, no fees",
        "",
    ]
    for var, per_tape in books.items():
        md += [
            f"### `{var}`: {VARS[var][1]}",
            "",
            "| tape | level | units | avg % | total USD | green |",
            "|---|---|---:|---|---:|---|",
        ]
        for tape in order:
            for lv, s in (per_tape.get(tape) or {}).items():
                md.append(
                    f"| {tape} | {lv} | {s['n']:,} | {s['avg']:+.2f} | {s['total_usd']:+,.0f} | {100 * s['green']:.0f}% |"
                )
        md.append("")
    return md


# ----------------------------------------------------------------------------- main


def run(log=print) -> dict:
    t0 = time.time()
    RESULTS.mkdir(parents=True, exist_ok=True)
    frames: dict[str, pd.DataFrame] = {}
    rows = load_run_one()
    log(f"run one: {len(rows):,} rows, {rows.coin.nunique()} instruments")
    universe = {m["coin"]: m for m in cached_universe(AS_OF_MS)}
    missing = sorted(set(rows.coin) - set(universe))
    if missing:
        log(f"  {len(missing)} coins without cached bars, left out: {missing}")
        rows = rows[rows.coin.isin(universe)]
    index = IndexState(_bars_crypto("BTC"))
    crypto = build_vars(rows, _bars_crypto, index, session=False, log=log)
    frames["crypto"] = crypto
    frames["btc"] = crypto[crypto.coin == "BTC"].copy()
    log(
        f"run one: variables built ({time.time() - t0:.0f}s); bitcoin alone {len(frames['btc']):,} units"
    )
    for variant in ("globex", "rth"):
        tape = es_tape.load(variant)
        rows_es = load_bench(variant)
        with use_calendar("session"):
            es = build_vars(rows_es, lambda coin, t=tape: t.daily, None, session=True, log=log)
        frames[f"es_{variant}_clean"] = es[es["gap"].isna()].copy()
        frames[f"es_{variant}_all"] = es
        log(
            f"ES {variant}: {len(es):,} units, {len(frames[f'es_{variant}_clean']):,} clean-fill ({time.time() - t0:.0f}s)"
        )
    for name in ("crypto", "es_globex_all", "es_rth_all"):
        with gzip.open(
            RESULTS / f"pairs_rows_{name}.csv.gz", "wt", newline="", encoding="utf-8"
        ) as fh:
            frames[name].to_csv(fh, index=False)
    prepared = {name: X.prepare(frames[name]) for name in ORDER}
    relabelled = {
        name: int(
            (
                prepared[name]["m_support"] != prepared[name]["m_support_engine"].fillna("unknown")
            ).sum()
        )
        for name in ORDER
    }
    by_tape = {}
    for name in ORDER:
        key = "btc" if name == "btc" else "es" if name.startswith("es_") else "crypto"
        by_tape[name] = X.readings(prepared[name], MIN_N[key])
        log(f"  readings on {name}: {len(prepared[name]):,} units ({time.time() - t0:.0f}s)")
    th = X.themes(by_tape, "crypto", ("es_globex_clean", "es_rth_clean"))
    theme_vars = [v for v, t in th.items() if t["theme"]]
    books = {
        var: {name: book_view(prepared[name], var) for name in BOOK_TAPES} for var in theme_vars
    }
    has = {name: int(prepared[name]["has_t1"].sum()) for name in ORDER}
    md = [
        "# The matched-pair study: same trigger, different outcome, what else was on the card (generated by analysis/pairs/run_pairs.py)",
        "",
        "Prereg docs/experiments/tvb44_matched_pairs_prereg.md (confirmed 2026-11-02; section 12 folded). Units with an exit-only outcome: "
        + ", ".join(f"{name} {len(prepared[name]):,} (with a T1 {has[name]:,})" for name in ORDER)
        + f". A cell is read at {MIN_N['crypto']} units (crypto), {MIN_N['btc']} (bitcoin alone), {MIN_N['es']} (ES); smaller cells are "
        "pooled as 'other' and shown. The month side of weekly and monthly units is the unit's own trigger against the month's open "
        "(relabelled against the engine's daily-trigger label: "
        + ", ".join(f"{name} {relabelled[name]:,}" for name in ORDER)
        + "). Per level: the share with a first target, the T1-reach rate OVER THE UNITS WITH ONE, the exit-only mean, each standardized "
        "to the cell sizes; the pooled high-minus-low difference is stratified by cell with a normal 95% interval. Characterization, no "
        "selector; every variable shown whether it separates or not.",
        "",
    ]
    md += table_themes(th, ORDER)
    md += ["## Every variable, every tape", ""]
    for var in (*NUMERIC, *CATEGORY):
        md += table_variable(var, by_tape, ORDER)
    if books:
        md += table_books(books, BOOK_TAPES)
    else:
        md += [
            "## The book view",
            "",
            "No variable met the theme rule; no book view is drawn (the per-level exit-only means are in the tables above).",
            "",
        ]
    (RESULTS / "pairs_tables.md").write_text("\n".join(md), encoding="utf-8")
    summary = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "as_of": AS_OF,
        "units": {name: int(len(prepared[name])) for name in ORDER},
        "with_t1": has,
        "rows": {name: int(len(frames[name])) for name in ORDER},
        "month_side_relabelled": relabelled,
        "coins_without_bars": missing,
        "min_n": MIN_N,
        "themes": th,
        "readings": {
            name: {var: {k: v for k, v in r.items() if k != "cells"} for var, r in rd.items()}
            for name, rd in by_tape.items()
        },
        "cells": {name: {var: r["cells"] for var, r in rd.items()} for name, rd in by_tape.items()},
        "books": books,
    }
    # the per-cell readings are large (every cell, every variable, every level) and regenerable:
    # they go beside the summary, ignored by git; the summary stays committed
    cells_doc = summary.pop("cells")
    (RESULTS / "pairs_cells.json").write_text(
        json.dumps(_finite(cells_doc), indent=1, allow_nan=False, default=str), encoding="utf-8"
    )
    (RESULTS / "pairs.json").write_text(
        json.dumps(_finite(summary), indent=1, allow_nan=False, default=str), encoding="utf-8"
    )
    log(
        f"tables and summary -> {RESULTS} ({time.time() - t0:.0f}s); themes: {theme_vars or 'none'}"
    )
    return summary


def _finite(o):
    if isinstance(o, dict):
        return {str(k): _finite(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_finite(v) for v in o]
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, (float, np.floating)):
        return None if not math.isfinite(float(o)) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    return o


if __name__ == "__main__":
    run()
