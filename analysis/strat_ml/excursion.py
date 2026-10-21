"""The excursion clock: does the setup show a favourable move SOON, and what is a trade worth
when it has not? (owner's question 2026-10-20, the discretionary "it turned against me" exit)

Declared grid, read as a spread, never a pick: favourable thresholds x in {0.25R, 0.5R, 1R};
clock hours H in {6, 12, 24, 48, 72} after the trigger hour. Rows with a full 10-bar window
only. Every table carries n. Research only.

  uv run python -m analysis.strat_ml.excursion
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.strat_ml.events import EVENTS_PATH

HERE = Path(__file__).parent
REPORTS = HERE / "reports"
THRESH = (("025", 0.25), ("05", 0.5), ("1", 1.0))
CLOCKS = (6, 12, 24, 48, 72)


def load(path: Path = EVENTS_PATH) -> pd.DataFrame:
    ev = pd.read_parquet(path)
    ev = ev[ev["r_managed_10"].notna() & ~ev["censored"]].copy()
    lo, hi = ev["r_managed_10"].quantile([0.005, 0.995])
    ev["r10"] = ev["r_managed_10"].clip(lo, hi)
    ev["win"] = ev["r_managed_10"] > 0
    ev["stopped"] = ev["first_touch"] == "stop"
    ev["tgt"] = ev["first_touch"] == "target"
    ev["hour_bucket"] = pd.cut(
        ev["hours_since_daily_open"],
        [-1, 0, 5, 11, 17, 23],
        labels=["00", "01-05", "06-11", "12-17", "18-23"],
    )
    return ev


# ----------------------------------------------------------------------------- tables


def reach_curve(ev: pd.DataFrame, by: str | None = None) -> pd.DataFrame:
    """Share of rows whose favourable / adverse excursion reached x R within H bars."""
    rows = []
    groups = ev.groupby(by, observed=True) if by else [("all", ev)]
    for key, g in groups:
        for side in ("fav", "adv"):
            for tag, x in THRESH:
                col = g[f"h_{side}_{tag}"]
                row = {by or "group": key, "side": side, "threshold_r": x, "n": len(g)}
                for H in CLOCKS + (240,):
                    row[f"by_{H}h"] = 100 * (col <= H - 1).mean()
                row["median_hours_when_reached"] = (
                    float(col.median()) if col.notna().any() else np.nan
                )
                rows.append(row)
    return pd.DataFrame(rows)


def first_excursion(ev: pd.DataFrame, by: str | None = None) -> pd.DataFrame:
    keys = ([by] if by else []) + ["first_excursion"]
    g = ev.groupby(keys, observed=True)
    out = g.agg(
        n=("r10", "size"),
        win_pct=("win", lambda s: 100 * s.mean()),
        tgt_first_pct=("tgt", lambda s: 100 * s.mean()),
        stop_first_pct=("stopped", lambda s: 100 * s.mean()),
        mean_r=("r10", "mean"),
        median_r=("r_managed_10", "median"),
    ).reset_index()
    tot = out.groupby(by, observed=True)["n"].transform("sum") if by else out["n"].sum()
    out.insert(len(keys) + 1, "share_pct", 100 * out["n"] / tot)
    return out


def time_stop(ev: pd.DataFrame, by: str | None = None) -> pd.DataFrame:
    """The rule 'at hour H, if the trade has not shown +x R yet and is still open, exit at that
    hour's close; otherwise manage as before' against plain holding, on the same rows."""
    rows = []
    groups = ev.groupby(by, observed=True) if by else [("all", ev)]
    for key, g in groups:
        for tag, x in THRESH[:2]:
            for H in CLOCKS[:4]:
                mark = g[f"r_close_{H}h"]
                ok = mark.notna()
                gg = g[ok]
                reached = gg[f"h_fav_{tag}"] <= H - 1
                resolved = gg["touch_hours"].notna() & (gg["touch_hours"] <= H - 1)
                exit_now = ~reached & ~resolved
                rule = np.where(exit_now, gg[f"r_close_{H}h"], gg["r10"])
                rows.append(
                    {
                        by or "group": key,
                        "threshold_r": x,
                        "clock_h": H,
                        "n": int(len(gg)),
                        "reached_pct": 100 * reached.mean(),
                        "resolved_pct": 100 * resolved.mean(),
                        "exit_now_pct": 100 * exit_now.mean(),
                        "hold_mean_r": float(gg["r10"].mean()),
                        "rule_mean_r": float(np.mean(rule)),
                        "reached_mean_r": float(gg.loc[reached, "r10"].mean())
                        if reached.any()
                        else np.nan,
                        "not_reached_open_mean_r": float(gg.loc[exit_now, "r10"].mean())
                        if exit_now.any()
                        else np.nan,
                        "not_reached_open_win_pct": 100 * float(gg.loc[exit_now, "win"].mean())
                        if exit_now.any()
                        else np.nan,
                        "exit_mark_mean_r": float(gg.loc[exit_now, f"r_close_{H}h"].mean())
                        if exit_now.any()
                        else np.nan,
                    }
                )
    return pd.DataFrame(rows)


def context_slices(ev: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for by in (
        "family",
        "asset_class",
        "direction",
        "tfc_score",
        "hour_bucket",
        "liq_tier",
        "h4_broke_before",
    ):
        for key, g in ev.groupby(by, observed=True):
            rows.append(
                {
                    "slice": by,
                    "value": str(key),
                    "n": len(g),
                    "fav_05_by_24h_pct": 100 * (g["h_fav_05"] <= 23).mean(),
                    "adv_05_by_24h_pct": 100 * (g["h_adv_05"] <= 23).mean(),
                    "fav_first_pct": 100 * (g["first_excursion"] == "fav").mean(),
                    "median_h_fav_05": float(g["h_fav_05"].median())
                    if g["h_fav_05"].notna().any()
                    else np.nan,
                    "mean_r": float(g["r10"].mean()),
                    "win_pct": 100 * g["win"].mean(),
                }
            )
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- output


def md(df: pd.DataFrame, cols: list[str] | None = None) -> str:
    cols = cols or list(df.columns)
    out = ["| " + " | ".join(c.replace("_", " ") for c in cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (float, np.floating)):
                if np.isnan(v):
                    cells.append("")
                elif c.endswith("pct") or c.startswith("by_"):
                    cells.append(f"{v:.1f}%")
                elif "mean_r" in c or "median_r" in c:
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
    ev = load()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    t_reach = reach_curve(ev)
    t_reach_fam = reach_curve(ev, "family")
    t_first = first_excursion(ev)
    t_first_fam = first_excursion(ev, "family")
    t_stop = time_stop(ev)
    t_stop_fam = time_stop(ev, "family")
    t_stop_cls = time_stop(ev, "asset_class")
    t_ctx = context_slices(ev)
    reach_cols = (
        ["side", "threshold_r", "n"]
        + [f"by_{H}h" for H in CLOCKS + (240,)]
        + ["median_hours_when_reached"]
    )
    stop_cols = [
        "threshold_r",
        "clock_h",
        "n",
        "reached_pct",
        "resolved_pct",
        "exit_now_pct",
        "hold_mean_r",
        "rule_mean_r",
        "reached_mean_r",
        "not_reached_open_mean_r",
        "not_reached_open_win_pct",
        "exit_mark_mean_r",
    ]
    lines = [
        f"# The excursion clock ({stamp})",
        "",
        f"{len(ev):,} trigger rows with a full 10-bar window. Hours = hourly bars after the trigger bar (the trigger bar is hour 0). "
        "'reached' = the favourable excursion touched +x R within the clock; 'resolved' = stop or target already hit; 'exit now' = neither, the rule exits at that hour's close. "
        "'hold' = the normal 10-bar management on the same rows.",
        "",
        "## 1. How soon the move shows: share of rows reaching +x R (fav) or x R against (adv) within H hours",
        "",
        md(t_reach, reach_cols),
        "",
        "### by family",
        "",
        md(t_reach_fam, ["family"] + reach_cols),
        "",
        "## 2. Which 0.25R came first, and how those trades ended",
        "",
        md(t_first),
        "",
        "### by family",
        "",
        md(t_first_fam),
        "",
        "## 3. The time-stop rule vs holding (same rows)",
        "",
        md(t_stop, stop_cols),
        "",
        "### by family",
        "",
        md(t_stop_fam, ["family"] + stop_cols),
        "",
        "### majors vs alts",
        "",
        md(t_stop_cls, ["asset_class"] + stop_cols),
        "",
        "## 4. Context slices: who shows +0.5R within 24 hours",
        "",
        md(t_ctx),
        "",
    ]
    text = "\n".join(lines)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"excursion_{stamp}.md").write_text(text, encoding="utf-8")
    (REPORTS / f"excursion_{stamp}.json").write_text(
        json.dumps(
            {
                "rows": int(len(ev)),
                "reach": t_reach.round(3).to_dict(orient="records"),
                "reach_family": t_reach_fam.round(3).to_dict(orient="records"),
                "first": t_first.round(3).to_dict(orient="records"),
                "first_family": t_first_fam.round(3).to_dict(orient="records"),
                "time_stop": t_stop.round(4).to_dict(orient="records"),
                "time_stop_family": t_stop_fam.round(4).to_dict(orient="records"),
                "time_stop_class": t_stop_cls.round(4).to_dict(orient="records"),
                "context": t_ctx.round(3).to_dict(orient="records"),
            },
            indent=1,
            default=str,
        ),
        encoding="utf-8",
    )
    print(text)


if __name__ == "__main__":
    main(sys.argv[1:])
