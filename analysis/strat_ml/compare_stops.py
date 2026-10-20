"""Head-to-head: the setup-bar stop vs the skill's bar-0 stop on the SAME inside-break rows.

Both event files are built by events.py (stop_mode setup / bar0); only inside breaks (setup
bar Type 1) differ between them. R changes with the stop, so the comparison is made in units
that do not: percent of price and ATRs, next to the R view. Research only.

  uv run python -m analysis.strat_ml.compare_stops
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.strat_ml.events import events_path
from analysis.strat_ml.report import HEAD, wilson

HERE = Path(__file__).parent
REPORTS = HERE / "reports"
KEY = ["symbol", "day", "direction"]


def prep(path: Path, label: str) -> pd.DataFrame:
    ev = pd.read_parquet(path)
    ev = ev[ev["r_managed_10"].notna() & (ev["family"] == "inside")].copy()
    ev["mode"] = label
    ev["ret_pct"] = ev["r_managed_10"] * ev["r"] / ev["level"] * 100  # % of price, 10 bars, managed
    ev["ret_atr"] = ev["r_managed_10"] * ev["stop_atr"]  # in ATRs
    ev["win"] = ev["r_managed_10"] > 0
    ev["stopped"] = ev["first_touch"] == "stop"
    ev["tgt"] = ev["first_touch"] == "target"
    ev["year"] = ev["day_ts"].dt.year
    return ev


def cell(g: pd.DataFrame) -> dict:
    n = len(g)
    w = int(g["win"].sum())
    lo, hi = wilson(w, n)
    lo_p, hi_p = np.percentile(g["ret_pct"], [0.5, 99.5]) if n else (0, 0)
    return {
        "n": n,
        "win_pct": 100 * w / n,
        "win_lo": 100 * lo,
        "win_hi": 100 * hi,
        "stop_first_pct": 100 * g["stopped"].mean(),
        "tgt_first_pct": 100 * g["tgt"].mean(),
        "mean_r": g["r_managed_10"].clip(-1, 10).mean(),
        "median_r": g["r_managed_10"].median(),
        "mean_ret_pct": g["ret_pct"].clip(lo_p, hi_p).mean(),
        "median_ret_pct": g["ret_pct"].median(),
        "mean_ret_atr": g["ret_atr"].clip(-5, 20).mean(),
        "median_rr": g["t1_dist_r"].median(),
        "median_stop_atr": g["stop_atr"].median(),
    }


def table(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    rows = []
    for k, g in df.groupby(keys, observed=True):
        k = k if isinstance(k, tuple) else (k,)
        rows.append({**dict(zip(keys, k)), **cell(g)})
    return pd.DataFrame(rows)


def md(df: pd.DataFrame, cols: list[str]) -> str:
    names = {
        "stop_first_pct": "stop first %",
        "tgt_first_pct": "target first %",
        "mean_ret_pct": "mean ret % of price",
        "median_ret_pct": "median ret %",
        "mean_ret_atr": "mean ret (ATR)",
        "median_rr": "median R:R",
        "median_stop_atr": "median stop (ATR)",
        **HEAD,
    }
    out = [
        "| " + " | ".join(names.get(c, c.replace("_", " ")) for c in cols) + " |",
        "|" + "---|" * len(cols),
    ]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (float, np.floating)):
                if c.endswith("_pct") or c in ("win_pct",):
                    cells.append(f"{v:.1f}%")
                elif c.startswith("mean_r") or c.startswith("median_r") and c != "median_rr":
                    cells.append(f"{v:+.3f}")
                else:
                    cells.append(f"{v:.2f}")
            elif isinstance(v, (int, np.integer)):
                cells.append(f"{int(v):,}")
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> None:
    a = prep(events_path("setup"), "setup-bar stop")
    b = prep(events_path("bar0"), "bar-0 stop")
    both = a.merge(b[KEY], on=KEY)  # the same rows on both sides
    a = a.merge(both[KEY], on=KEY)
    b = b.merge(both[KEY], on=KEY)
    df = pd.concat([a, b], ignore_index=True)
    cols_main = [
        "n",
        "win_pct",
        "stop_first_pct",
        "tgt_first_pct",
        "mean_r",
        "median_r",
        "mean_ret_pct",
        "median_ret_pct",
        "mean_ret_atr",
        "median_rr",
        "median_stop_atr",
    ]
    t_all = table(df, ["mode"])
    t_pat = table(df, ["pattern", "mode"]).sort_values(["pattern", "mode"])
    t_cls = table(df, ["asset_class", "mode"]).sort_values(["asset_class", "mode"])
    t_year = table(df, ["year", "mode"]).sort_values(["year", "mode"])
    t_dir = table(df, ["direction", "mode"]).sort_values(["direction", "mode"])
    # whole-book effect: all rows (inside rows swapped, others identical)
    full_a = pd.read_parquet(events_path("setup"))
    full_b = pd.read_parquet(events_path("bar0"))
    for f in (full_a, full_b):
        f["ret_pct"] = f["r_managed_10"] * f["r"] / f["level"] * 100
    book = pd.DataFrame(
        [
            {
                "mode": m,
                "n": int(f["r_managed_10"].notna().sum()),
                "mean_ret_pct": f["ret_pct"].clip(-50, 50).mean(),
                "median_ret_pct": f["ret_pct"].median(),
                "win_pct": 100 * (f["r_managed_10"] > 0).mean(),
                "stop_first_pct": 100 * (f["first_touch"] == "stop").mean(),
            }
            for m, f in (("setup-bar stop", full_a), ("bar-0 stop", full_b))
        ]
    )
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        f"# Stop placement head-to-head on inside breaks ({stamp})",
        "",
        f"Same {len(both):,} inside-break rows (setup bar Type 1), two stops: the far side of the setup bar (TVB-37 R) vs the far side of bar 0 (the skill's structural stop). Everything else identical: entry at the level, the same target, 10 daily bars, stop-first on ties. 'ret % of price' and 'ret (ATR)' are the units that do not move with the stop; R moves with it by construction.",
        "",
        "## Inside breaks, all rows",
        "",
        md(t_all, ["mode"] + cols_main),
        "",
        "## By pattern",
        "",
        md(t_pat, ["pattern", "mode"] + cols_main),
        "",
        "## By direction",
        "",
        md(t_dir, ["direction", "mode"] + cols_main),
        "",
        "## Majors vs alts",
        "",
        md(t_cls, ["asset_class", "mode"] + cols_main),
        "",
        "## By year",
        "",
        md(
            t_year,
            [
                "year",
                "mode",
                "n",
                "win_pct",
                "stop_first_pct",
                "mean_ret_pct",
                "median_ret_pct",
                "mean_ret_atr",
            ],
        ),
        "",
        "## The whole book (all patterns; only the inside rows changed)",
        "",
        md(book, ["mode", "n", "win_pct", "stop_first_pct", "mean_ret_pct", "median_ret_pct"]),
        "",
    ]
    text = "\n".join(lines)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"stop_compare_{stamp}.md").write_text(text, encoding="utf-8")
    (REPORTS / f"stop_compare_{stamp}.json").write_text(
        json.dumps(
            {
                "rows": int(len(both)),
                "all": t_all.round(4).to_dict(orient="records"),
                "pattern": t_pat.round(4).to_dict(orient="records"),
                "year": t_year.round(4).to_dict(orient="records"),
                "book": book.round(4).to_dict(orient="records"),
            },
            indent=1,
            default=str,
        ),
        encoding="utf-8",
    )
    print(text)


if __name__ == "__main__":
    main(sys.argv[1:])
