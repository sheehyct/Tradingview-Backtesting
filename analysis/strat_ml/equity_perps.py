"""Equity perps (Hyperliquid xyz dex, HIP-3) two ways: the 24/7 calendar day, and the New York
regular session as the STRAT bar (owner, 2026-10-20: "the one thing we did not test").

Inputs: events_xyz.parquet (calendar build of the xyz roster) and events_xyz_rth.parquet (the
regular-hours build), plus the Binance table restricted to the same window as the control
cell. The venue serves ~208 days of hourly bars, so every number here is a short window
(2026-03-26 to the build date) and the samples are small; counts on every cell. Research only.

  uv run python -m analysis.strat_ml.equity_perps
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.strat_ml.events import EVENTS_PATH, events_path
from analysis.strat_ml.excursion import md

HERE = Path(__file__).parent
REPORTS = HERE / "reports"


def prep(path: Path, label: str) -> pd.DataFrame:
    ev = pd.read_parquet(path)
    ev = ev[ev["r_managed_10"].notna() & ~ev["censored"]].copy()
    ev["build"] = label
    ev["r10"] = ev["r_managed_10"].clip(-1, 10)
    ev["rc"] = ev["r_close_10"].clip(-5, 10)
    ev["win"] = ev["r_managed_10"] > 0
    ev["tgt"] = ev["first_touch"] == "target"
    ev["stopped"] = ev["first_touch"] == "stop"
    ev["ret_pct"] = (ev["r_managed_10"] * ev["r"] / ev["level"] * 100).clip(-50, 50)
    if "session_class" not in ev.columns:
        ev["session_class"] = "crypto"
    ev["session_class"] = ev["session_class"].fillna("crypto")
    return ev


def cell(g: pd.DataFrame) -> dict:
    n = len(g)
    return {
        "n": n,
        "coins": int(g["symbol"].nunique()),
        "win_pct": 100 * g["win"].mean() if n else np.nan,
        "tgt_first_pct": 100 * g["tgt"].mean() if n else np.nan,
        "stop_first_pct": 100 * g["stopped"].mean() if n else np.nan,
        "mean_r": float(g["r10"].mean()) if n else np.nan,
        "median_r": float(g["r_managed_10"].median()) if n else np.nan,
        "mean_ret_pct": float(g["ret_pct"].mean()) if n else np.nan,
        "mean_r_no_stop": float(g["rc"].mean()) if n else np.nan,
        "mfe_med": float(g["mfe_r_10"].median()) if n else np.nan,
        "mae_med": float(g["mae_r_10"].median()) if n else np.nan,
        "rungs_mean": float(g["pivot_reached_10"].mean())
        if n and "pivot_reached_10" in g
        else np.nan,
        "stop_atr_med": float(g["stop_atr"].median()) if n else np.nan,
    }


def table(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    rows = []
    for k, g in df.groupby(keys, observed=True):
        k = k if isinstance(k, tuple) else (k,)
        rows.append({**dict(zip(keys, k)), **cell(g)})
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> None:
    cal = prep(events_path("setup", "calendar", "xyz"), "24/7 calendar day")
    rth = prep(events_path("setup", "rth", "xyz"), "NY regular session")
    t0, t1 = cal["day_ts"].min(), cal["day_ts"].max()
    crypto = prep(EVENTS_PATH, "crypto alts, same window")
    crypto = crypto[
        (crypto["day_ts"] >= t0) & (crypto["day_ts"] <= t1) & (crypto["asset_class"] == "alt")
    ]
    crypto["session_class"] = "crypto_alt"
    cols = [
        "n",
        "coins",
        "win_pct",
        "tgt_first_pct",
        "stop_first_pct",
        "mean_r",
        "median_r",
        "mean_ret_pct",
        "mean_r_no_stop",
        "mfe_med",
        "mae_med",
        "rungs_mean",
        "stop_atr_med",
    ]
    us_cal = cal[cal["session_class"] == "us_listed"]
    us_rth = rth[rth["session_class"] == "us_listed"]
    t_class = table(pd.concat([cal, crypto]), ["session_class"])
    t_sess = table(cal, ["session_class", "trigger_session"])
    t_two = table(pd.concat([us_cal, us_rth, crypto]), ["build"])
    t_fam = table(pd.concat([us_cal, us_rth]), ["family", "build"]).sort_values(["family", "build"])
    t_dir = table(pd.concat([us_cal, us_rth]), ["direction", "build"]).sort_values(
        ["direction", "build"]
    )
    t_hour = table(us_cal, ["local_hour"])
    t_pat = table(pd.concat([us_cal, us_rth]), ["pattern", "build"]).sort_values(
        ["pattern", "build"]
    )
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        f"# Equity perps two ways ({stamp})",
        "",
        f"Hyperliquid xyz dex, hourly bars {t0:%Y-%m-%d} to {t1:%Y-%m-%d} (the venue serves ~208 days). Calendar build: {len(cal):,} rows on {cal['symbol'].nunique()} perps; regular-session build: {len(rth):,} rows on {rth['symbol'].nunique()}. Control: Binance crypto alts in the same window, {len(crypto):,} rows. "
        "Same stop (setup bar), same target ladder, same 10-day walk over all hours. 'NY regular session' = the STRAT daily bar is the weekday 9:00-15:59 New York hours only (the 9:00 hourly bar holds the 9:30 open: an approximation), triggers scanned inside the session, weeks and months by the local calendar.",
        "",
        "## 1. By what the perp tracks (calendar build) against crypto alts in the same months",
        "",
        md(t_class, ["session_class"] + cols),
        "",
        "## 2. US-listed perps: 24/7 calendar day vs the regular session as the bar vs crypto",
        "",
        md(t_two, ["build"] + cols),
        "",
        "### by family",
        "",
        md(t_fam, ["family", "build"] + cols),
        "",
        "### by direction",
        "",
        md(t_dir, ["direction", "build"] + cols),
        "",
        "### by pattern",
        "",
        md(t_pat, ["pattern", "build"] + cols),
        "",
        "## 3. Calendar build: what session the break happened in",
        "",
        md(t_sess, ["session_class", "trigger_session"] + cols),
        "",
        "## 4. US-listed, calendar build: by New York hour of the break",
        "",
        md(t_hour, ["local_hour"] + cols),
        "",
    ]
    text = "\n".join(lines)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"equity_perps_{stamp}.md").write_text(text, encoding="utf-8")
    (REPORTS / f"equity_perps_{stamp}.json").write_text(
        json.dumps(
            {
                "window": [str(t0.date()), str(t1.date())],
                "rows_calendar": int(len(cal)),
                "rows_rth": int(len(rth)),
                "rows_crypto_control": int(len(crypto)),
                "by_class": t_class.round(4).to_dict(orient="records"),
                "two_ways": t_two.round(4).to_dict(orient="records"),
                "family": t_fam.round(4).to_dict(orient="records"),
                "direction": t_dir.round(4).to_dict(orient="records"),
                "pattern": t_pat.round(4).to_dict(orient="records"),
                "session": t_sess.round(4).to_dict(orient="records"),
                "hour": t_hour.round(4).to_dict(orient="records"),
            },
            indent=1,
            default=str,
        ),
        encoding="utf-8",
    )
    print(text)


if __name__ == "__main__":
    main(sys.argv[1:])
