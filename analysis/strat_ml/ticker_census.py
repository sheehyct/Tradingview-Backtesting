"""The overfit and underfit ticker census (owner, 2026-10-20): which coins carried the most
patterns and did best, which did worst. A LABELLED OVERFIT CENSUS: ceiling-mapping, never a
promotion (CLAUDE.md "Ablation, not tournament"). Every number is per coin on the daily trigger
rows with the setup-bar stop and the TVB-37 target, 10 bars, no fees.

  uv run python -m analysis.strat_ml.ticker_census
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
MIN_ROWS = 500
STABLES = ("USDCUSDT", "FDUSDUSDT", "BUSDUSDT", "TUSDUSDT", "USDPUSDT", "DAIUSDT", "USD1USDT")


def effective_patterns(s: pd.Series) -> float:
    """exp(entropy) of the pattern mix: 1 = one pattern only, 11 = all equally."""
    p = s.value_counts(normalize=True)
    return float(np.exp(-(p * np.log(p)).sum()))


def census(path: Path = EVENTS_PATH) -> pd.DataFrame:
    ev = pd.read_parquet(path)
    ev = ev[ev["r_managed_10"].notna() & ~ev["censored"]].copy()
    lo, hi = ev["r_managed_10"].quantile([0.005, 0.995])
    ev["r10"] = ev["r_managed_10"].clip(lo, hi)
    ev["win"] = ev["r_managed_10"] > 0
    ev["rc"] = ev["r_close_10"].clip(-5, 10)
    ev["ret_pct"] = (ev["r_managed_10"] * ev["r"] / ev["level"] * 100).clip(-50, 50)
    ev["stable"] = ev["symbol"].isin(STABLES)
    g = (
        ev.groupby("symbol")
        .agg(
            n=("r10", "size"),
            years=("day_ts", lambda s: (s.max() - s.min()).days / 365.25),
            eff_patterns=("pattern", effective_patterns),
            continuation_share=("family", lambda s: (s == "continuation").mean()),
            reversal_share=("family", lambda s: (s == "reversal").mean()),
            win_pct=("win", lambda s: 100 * s.mean()),
            mean_r=("r10", "mean"),
            sum_r=("r10", "sum"),
            mean_ret_pct=("ret_pct", "mean"),
            mean_r_no_stop=("rc", "mean"),
            liq_rank_median=("liq_rank", "median"),
            age_days=("symbol_age_days", "max"),
            stable=("stable", "first"),
        )
        .reset_index()
    )
    g = g[g["n"] >= MIN_ROWS].copy()
    # how far a coin's mean is from zero in its own noise: sd of r / sqrt(n)
    sd = ev.groupby("symbol")["r10"].std()
    g["noise_sd"] = g["symbol"].map(sd) / np.sqrt(g["n"])
    g["z"] = g["mean_r"] / g["noise_sd"]
    g["rank"] = g["mean_r"].rank(ascending=False).astype(int)
    return g.sort_values("mean_r", ascending=False).reset_index(drop=True)


def md(df: pd.DataFrame, cols: list[str]) -> str:
    out = ["| " + " | ".join(c.replace("_", " ") for c in cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (float, np.floating)):
                if c.endswith("pct") or c.endswith("share"):
                    cells.append(f"{v * 100:.0f}%" if c.endswith("share") else f"{v:.1f}%")
                elif c in ("mean_r", "sum_r", "mean_r_no_stop"):
                    cells.append(f"{v:+.3f}")
                else:
                    cells.append(f"{v:.2f}")
            elif isinstance(v, (bool, np.bool_)):
                cells.append("yes" if v else "")
            elif isinstance(v, (int, np.integer)):
                cells.append(f"{int(v):,}")
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> None:
    g = census()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cols = [
        "rank",
        "symbol",
        "n",
        "years",
        "eff_patterns",
        "continuation_share",
        "win_pct",
        "mean_r",
        "sum_r",
        "mean_ret_pct",
        "mean_r_no_stop",
        "z",
        "liq_rank_median",
        "stable",
    ]
    live = g[~g["stable"]]
    corr = {
        "mean_r_vs_eff_patterns": float(live["mean_r"].corr(live["eff_patterns"])),
        "mean_r_vs_continuation_share": float(live["mean_r"].corr(live["continuation_share"])),
        "mean_r_vs_liq_rank": float(live["mean_r"].corr(live["liq_rank_median"])),
        "mean_r_vs_years": float(live["mean_r"].corr(live["years"])),
    }
    noise = float(live["noise_sd"].median())
    lines = [
        f"# The overfit and underfit ticker census ({stamp})",
        "",
        f"{len(g)} coins with at least {MIN_ROWS} daily trigger rows (of 900). Per coin: rows, years of history, the effective number of patterns (1 = one pattern, 11 = all equally), the share of rows that were 2-2 continuations, win %, mean R (winsorized) with the setup-bar stop, the sum of R, mean return in % of price, mean R with no stop, and z = mean R divided by the coin's own noise (sd / sqrt n). A labelled overfit census: ceiling-mapping, never a promotion.",
        "",
        f"The honest yardstick first: a coin with 1,000 rows and no edge would show a mean R anywhere within about +-{2 * noise:.3f} by chance (two noise sd). The top of the table should be read against that.",
        "",
        "## The overfit end: top 15 by mean R",
        "",
        md(g.head(15), cols),
        "",
        "## The underfit end: bottom 15 by mean R",
        "",
        md(g.tail(15).iloc[::-1], cols),
        "",
        "## Most pattern-diverse coins (top 10 by effective patterns), with their results",
        "",
        md(g.sort_values("eff_patterns", ascending=False).head(10), cols),
        "",
        "## Across coins (stables excluded)",
        "",
        f"- mean R vs pattern diversity: r = {corr['mean_r_vs_eff_patterns']:+.2f} (more variety, slightly worse)",
        f"- mean R vs continuation share: r = {corr['mean_r_vs_continuation_share']:+.2f} (the coins that did best were the ones that trended: more 2-2 continuations)",
        f"- mean R vs liquidity rank: r = {corr['mean_r_vs_liq_rank']:+.2f}; vs years of history: r = {corr['mean_r_vs_years']:+.2f}",
        f"- spread of per-coin mean R: 5th pct {live['mean_r'].quantile(0.05):+.3f}, median {live['mean_r'].median():+.3f}, 95th pct {live['mean_r'].quantile(0.95):+.3f}",
        "",
    ]
    text = "\n".join(lines)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"ticker_census_{stamp}.md").write_text(text, encoding="utf-8")
    (REPORTS / f"ticker_census_{stamp}.json").write_text(
        json.dumps(
            {
                "coins": int(len(g)),
                "min_rows": MIN_ROWS,
                "noise_sd_median": noise,
                "correlations": corr,
                "top": g.head(15).round(4).to_dict(orient="records"),
                "bottom": g.tail(15).iloc[::-1].round(4).to_dict(orient="records"),
                "diverse": g.sort_values("eff_patterns", ascending=False)
                .head(10)
                .round(4)
                .to_dict(orient="records"),
                "all": g.round(4).to_dict(orient="records"),
            },
            indent=1,
            default=str,
        ),
        encoding="utf-8",
    )
    print(text)


if __name__ == "__main__":
    main(sys.argv[1:])
