"""High-beta followers against their parent sector fund. Description only: no trades, no rule.

Owner's rule, 2026-11-19: a follower is a liquid name that is NOT one of the parent sector
fund's ten largest holdings and whose beta to that sector fund is 1.5 or higher. Candidates are
pooled from the top holdings of narrower theme funds (TODAY'S lists: hindsight, and the beta
floor uses the last two years, so every name here is one that has recently been high-beta).

Questions:
  1. Is the down-day lean general: do these names fall harder on sector down days than they
     rise on sector up days?
  2. When the sector is weak (it had lost two or more distinct levels at the PRIOR close, so the
     label is known before the day starts), is the follower's beta higher than on calm days?

Shared opens count as one level (week / month / quarter / half-year / year), as in levels.py.

Run:  uv run --no-project --with yfinance --with pandas --with numpy \
          python analysis/sector/followers.py analysis/sector
"""

from __future__ import annotations

import json
import sys
import warnings

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

BETA_FLOOR = 1.5
DOLLAR_FLOOR_M = 50.0  # median dollars traded per day, last 60 days, in millions
BETA_WINDOW = 504  # trading days, about two years
MIN_DAYS = 300

# parent sector fund -> theme funds whose top holdings are pooled for candidates
POOLS = {
    "XLK": ["SMH", "SOXX", "XSD", "PSI", "NCLD", "IGV", "WCLD", "CIBR", "XSW", "ARKW", "ARKK"],
    "XLF": ["KRE", "KBE", "IAT", "KBWB", "KCE", "IAI", "FINX", "ARKF"],
    "XLY": ["ITB", "XHB", "XRT", "PEJ", "ONLN"],
}


def fetch(ticker: str) -> pd.DataFrame:
    df = yf.download(ticker, start="1998-01-01", auto_adjust=False, progress=False, threads=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]].dropna()


def level_state(df: pd.DataFrame) -> pd.DataFrame:
    """Distinct period opens (L) and how many of them the close is above (A)."""
    i = df.index
    iso = i.isocalendar()
    keys = {
        "W": iso["year"].astype(int).values * 100 + iso["week"].astype(int).values,
        "M": i.year * 100 + i.month,
        "Q": i.year * 10 + i.quarter,
        "H": i.year * 10 + ((i.month - 1) // 6),
        "Y": i.year,
    }
    opens = np.column_stack(
        [
            df.groupby(pd.Series(np.asarray(k), index=i))["Open"].transform("first").round(4).values
            for k in keys.values()
        ]
    )
    close = df["Close"].values
    n_levels = np.array([len(set(row)) for row in opens])
    n_above = np.array([len({x for x in row if c > x}) for row, c in zip(opens, close)])
    return pd.DataFrame({"L": n_levels, "A": n_above}, index=i)


def slope(y: pd.Series, x: pd.Series) -> float:
    d = pd.concat([y, x], axis=1).dropna()
    if len(d) < 40:
        return float("nan")
    return float(np.cov(d.iloc[:, 0], d.iloc[:, 1])[0, 1] / d.iloc[:, 1].var())


def main(root: str) -> None:
    parent_top = json.load(open(f"{root}/holdings.json"))
    out: dict[str, list[dict]] = {}
    for parent, funds in POOLS.items():
        p = fetch(parent)
        rp = p["Adj Close"].pct_change()
        st = level_state(p)
        weak_prev = ((st.L - st.A) >= 2).shift(1, fill_value=False)
        calm_prev = (st.A == st.L).shift(1, fill_value=False)
        top_ten = {t for t, _ in parent_top[parent]}

        source: dict[str, list[str]] = {}
        for fund in funds:
            try:
                holdings = yf.Ticker(fund).funds_data.top_holdings
            except Exception:  # a fund without holdings data is skipped, and said so
                print(f"  ({fund}: no holdings data)")
                continue
            for ticker in holdings.index:
                ticker = str(ticker)
                if ticker.replace("-", "").isalpha() and ticker not in top_ten:
                    source.setdefault(ticker, []).append(fund)

        rows = []
        for ticker, came_from in sorted(source.items()):
            try:
                d = fetch(ticker)
            except Exception:
                continue
            if len(d) < MIN_DAYS:
                continue
            rf = d["Adj Close"].pct_change()
            dollars = float((d["Close"] * d["Volume"]).tail(60).median()) / 1e6
            beta_recent = slope(rf.tail(BETA_WINDOW), rp.tail(BETA_WINDOW))
            if not (beta_recent >= BETA_FLOOR and dollars >= DOLLAR_FLOOR_M):
                continue
            j = pd.concat([rf.rename("f"), rp.rename("p")], axis=1).dropna()
            worst = j.nsmallest(30, "p")
            best = j.nlargest(30, "p")
            weak = j[weak_prev.reindex(j.index, fill_value=False)]
            calm = j[calm_prev.reindex(j.index, fill_value=False)]
            beta_calm = slope(calm.f, calm.p)
            rows.append(
                {
                    "ticker": ticker,
                    "from": "+".join(came_from),
                    "since": str(j.index[0].date()),
                    "days": len(j),
                    "dollars_m": round(dollars),
                    "beta_recent": round(beta_recent, 2),
                    "beta_all": round(slope(j.f, j.p), 2),
                    "beta_down": round(slope(j.f[j.p < 0], j.p[j.p < 0]), 2),
                    "beta_up": round(slope(j.f[j.p > 0], j.p[j.p > 0]), 2),
                    "beta_calm": round(beta_calm, 2),
                    "beta_weak": round(slope(weak.f, weak.p), 2),
                    "worst30": round(float(worst.f.sum() / worst.p.sum()), 2),
                    "best30": round(float(best.f.sum() / best.p.sum()), 2),
                    "opposite_on_worst30": int((worst.f > 0).sum()),
                    "weak_days": len(weak),
                    "weak_gap_bp": round(float((weak.f - beta_calm * weak.p).mean() * 1e4), 1),
                    "corr": round(float(j.f.corr(j.p)), 2),
                }
            )
        rows.sort(key=lambda r: -r["beta_recent"])
        out[parent] = rows

        print(f"\n=== followers against {parent}: {len(source)} candidates, {len(rows)} pass ===")
        if not rows:
            print("    none pass the beta and liquidity floors")
            continue
        head = "ticker from                 since       beta2y  all  down   up | calm weak |"
        print("   ", head, "worst30 best30 opp | corr  $M/day")
        for r in rows:
            print(
                f"    {r['ticker']:6s} {r['from'][:20]:20s} {r['since']}  {r['beta_recent']:5.2f} "
                f"{r['beta_all']:5.2f} {r['beta_down']:5.2f} {r['beta_up']:5.2f} | "
                f"{r['beta_calm']:4.2f} {r['beta_weak']:4.2f} | {r['worst30']:6.2f} "
                f"{r['best30']:6.2f} {r['opposite_on_worst30']:3d} | {r['corr']:4.2f} "
                f"{r['dollars_m']:6d}"
            )
        f = pd.DataFrame(rows)
        lean = (f.beta_down > f.beta_up).sum()
        print(
            f"    down-day beta above up-day beta: {lean} of {len(f)} names | medians: down "
            f"{f.beta_down.median():.2f}, up {f.beta_up.median():.2f}, calm "
            f"{f.beta_calm.median():.2f}, weak {f.beta_weak.median():.2f}, worst-30 capture "
            f"{f.worst30.median():.2f}, best-30 capture {f.best30.median():.2f}"
        )
        print(
            f"    sector-weak days, follower move beyond what calm beta predicts: median "
            f"{f.weak_gap_bp.median():+.1f} bp/day; negative for "
            f"{(f.weak_gap_bp < 0).sum()} of {len(f)} names"
        )
    json.dump(out, open(f"{root}/followers.json", "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
