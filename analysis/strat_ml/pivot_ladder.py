"""The pivot ladder read (owner, 2026-10-20): how far price climbs the Pine's ladder, and what the
Pine's T1 does to the book against the TVB-37 target, on the same rows.

Ladder = the owner's Pine (TheStrat Magnitude + Targets) ported to daily bars in events.py:
anchors first, then prior highs / lows not yet taken out, nearest first, six rungs, 250 bars.
Touch = the TVB-22 ladder census's REACH convention (favourable extreme at or past the rung).
Window = the 10 daily bars after the trigger. Research only.

  uv run python -m analysis.strat_ml.pivot_ladder
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.strat_ml.events import EVENTS_PATH
from analysis.strat_ml.excursion import md

HERE = Path(__file__).parent
REPORTS = HERE / "reports"


def load(path: Path = EVENTS_PATH) -> pd.DataFrame:
    ev = pd.read_parquet(path)
    ev = ev[ev["r_managed_10"].notna() & ~ev["censored"]].copy()
    lo, hi = ev["r_managed_10"].quantile([0.005, 0.995])
    ev["r10"] = ev["r_managed_10"].clip(lo, hi)
    ev["r10_pivot"] = ev["r_managed_pivot_10"].clip(lo, hi)
    ev["win"] = ev["r_managed_10"] > 0
    ev["win_pivot"] = ev["r_managed_pivot_10"] > 0
    ev["year"] = ev["day_ts"].dt.year
    return ev


def rung_table(ev: pd.DataFrame, by: str) -> pd.DataFrame:
    rows = []
    for key, g in ev.groupby(by, observed=True):
        n = len(g)
        row = {by: key, "n": n, "ladder_len_median": float(g["pivot_rungs"].median())}
        row["no_rung_pct"] = 100 * (g["pivot_rungs"] == 0).mean()
        for k in (1, 2, 3, 4):
            row[f"reached_{k}_pct"] = 100 * (g["pivot_reached_10"] >= k).mean()
        row["mean_rungs_reached"] = float(g["pivot_reached_10"].mean())
        for k in (1, 2, 3):
            h = g[f"h_rung{k}"]
            row[f"median_h_rung{k}"] = float(h.median()) if h.notna().any() else np.nan
        row["t1_dist_r_median"] = float(g["pivot_t1_dist_r"].median())
        row["t3_dist_r_median"] = float(g["pivot_t3_dist_r"].median())
        rows.append(row)
    return pd.DataFrame(rows)


def book_table(ev: pd.DataFrame, by: str) -> pd.DataFrame:
    """TVB-37 T1 vs the Pine T1, same rows (both targets exist), same stop, same walk."""
    both = ev[ev["has_target"] & (ev["pivot_rungs"] > 0)]
    rows = []
    for key, g in both.groupby(by, observed=True):
        rows.append(
            {
                by: key,
                "n": len(g),
                "same_t1_pct": 100 * np.isclose(g["t1"], g["pivot_t1"]).mean(),
                "tvb37_rr_median": float(g["t1_dist_r"].median()),
                "pine_rr_median": float(g["pivot_t1_dist_r"].median()),
                "tvb37_tgt_first_pct": 100 * (g["first_touch"] == "target").mean(),
                "pine_tgt_first_pct": 100 * (g["pivot_first_touch"] == "target").mean(),
                "tvb37_win_pct": 100 * g["win"].mean(),
                "pine_win_pct": 100 * g["win_pivot"].mean(),
                "tvb37_mean_r": float(g["r10"].mean()),
                "pine_mean_r": float(g["r10_pivot"].mean()),
                "diff_mean_r": float((g["r10_pivot"] - g["r10"]).mean()),
            }
        )
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> None:
    ev = load()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    no_t = ev[~ev["has_target"]]
    t_all = rung_table(ev.assign(all="all"), "all")
    t_fam = rung_table(ev, "family")
    t_pat = rung_table(ev, "pattern")
    t_cls = rung_table(ev, "asset_class")
    t_year = rung_table(ev, "year")
    b_fam = book_table(ev, "family")
    b_pat = book_table(ev, "pattern")
    b_cls = book_table(ev, "asset_class")
    rung_cols = [
        "n",
        "ladder_len_median",
        "no_rung_pct",
        "reached_1_pct",
        "reached_2_pct",
        "reached_3_pct",
        "reached_4_pct",
        "mean_rungs_reached",
        "median_h_rung1",
        "median_h_rung2",
        "median_h_rung3",
        "t1_dist_r_median",
        "t3_dist_r_median",
    ]
    book_cols = [
        "n",
        "same_t1_pct",
        "tvb37_rr_median",
        "pine_rr_median",
        "tvb37_tgt_first_pct",
        "pine_tgt_first_pct",
        "tvb37_win_pct",
        "pine_win_pct",
        "tvb37_mean_r",
        "pine_mean_r",
        "diff_mean_r",
    ]
    lines = [
        f"# The pivot ladder ({stamp})",
        "",
        f"{len(ev):,} daily trigger rows with a full 10-bar window. The ladder is the owner's Pine ported to daily bars (anchors first, then prior highs / lows not yet taken out, six rungs, 250 bars back). 'reached k' = the favourable extreme touched rung k within 10 bars (reach convention). Hours = hourly bars after the trigger bar.",
        "",
        "## 1. How far price climbs the ladder",
        "",
        md(t_all, ["all"] + rung_cols),
        "",
        "### by family",
        "",
        md(t_fam, ["family"] + rung_cols),
        "",
        "### by pattern",
        "",
        md(t_pat, ["pattern"] + rung_cols),
        "",
        "### majors vs alts",
        "",
        md(t_cls, ["asset_class"] + rung_cols),
        "",
        "### by year",
        "",
        md(t_year, ["year"] + rung_cols),
        "",
        f"## 2. Rows the TVB-37 ladder left without a target: {len(no_t):,}; of those the Pine ladder gives a rung to {int((no_t['pivot_rungs'] > 0).sum()):,}, and {100 * (no_t['pivot_reached_10'] >= 1).mean():.1f}% of them reach rung 1 within 10 bars (median R:R {no_t['pivot_t1_dist_r'].median():.2f})",
        "",
        "## 3. The Pine's T1 against the TVB-37 T1, same rows, same stop, same walk",
        "",
        md(b_fam, ["family"] + book_cols),
        "",
        "### by pattern",
        "",
        md(b_pat, ["pattern"] + book_cols),
        "",
        "### majors vs alts",
        "",
        md(b_cls, ["asset_class"] + book_cols),
        "",
    ]
    text = "\n".join(lines)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"pivot_ladder_{stamp}.md").write_text(text, encoding="utf-8")
    (REPORTS / f"pivot_ladder_{stamp}.json").write_text(
        json.dumps(
            {
                "rows": int(len(ev)),
                "rungs_all": t_all.round(3).to_dict(orient="records"),
                "rungs_family": t_fam.round(3).to_dict(orient="records"),
                "rungs_pattern": t_pat.round(3).to_dict(orient="records"),
                "rungs_class": t_cls.round(3).to_dict(orient="records"),
                "rungs_year": t_year.round(3).to_dict(orient="records"),
                "no_target_rows": int(len(no_t)),
                "no_target_with_rung": int((no_t["pivot_rungs"] > 0).sum()),
                "book_family": b_fam.round(4).to_dict(orient="records"),
                "book_pattern": b_pat.round(4).to_dict(orient="records"),
                "book_class": b_cls.round(4).to_dict(orient="records"),
            },
            indent=1,
            default=str,
        ),
        encoding="utf-8",
    )
    print(text)


if __name__ == "__main__":
    main(sys.argv[1:])
