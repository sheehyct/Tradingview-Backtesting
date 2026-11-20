"""Feasibility probe, descriptive only: are thematic funds + holdings available, and how has a
follower (NBIS and peers) moved against a leader (NVDA) on daily closes. No trades, no rule."""

import yfinance as yf
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings("ignore")
themes = [
    "SMH",
    "SOXX",
    "IGV",
    "NCLD",
    "DRAM",
    "XBI",
    "KRE",
    "XOP",
    "ITB",
    "TAN",
    "ARKK",
    "WCLD",
    "CIBR",
    "BOTZ",
]
print("THEMATIC FUNDS: first bar, top holdings available?")
for t in themes:
    try:
        h = yf.Ticker(t).history(period="max", auto_adjust=False)
        first = h.index[0].date() if len(h) else None
        try:
            th = yf.Ticker(t).funds_data.top_holdings
            tops = " ".join(
                f"{i}:{r['Holding Percent'] * 100:.0f}" for i, r in th.head(6).iterrows()
            )
        except Exception as e:
            tops = f"no holdings ({type(e).__name__})"
        print(f"  {t:5s} bars={len(h):5d} first={first} | {tops}")
    except Exception as e:
        print(f"  {t:5s} FAILED {type(e).__name__}")
syms = ["NVDA", "NBIS", "CRWV", "IREN", "SMH", "XLK", "SPY"]
px = yf.download(syms, start="2024-10-21", auto_adjust=True, progress=False)["Close"]
r = px.pct_change().dropna(how="all")


def beta(y, x):
    d = pd.concat([y, x], axis=1).dropna()
    if len(d) < 30:
        return np.nan, len(d)
    return float(np.cov(d.iloc[:, 0], d.iloc[:, 1])[0, 1] / d.iloc[:, 1].var()), len(d)


print("\nFOLLOWERS AGAINST NVDA, daily closes since 2024-10-21")
print(
    "  name   days  corr  beta-all  beta on NVDA down days  beta on NVDA up days  beta on NVDA's 30 worst days | vs SMH beta | vs SPY beta"
)
for f in ["NBIS", "CRWV", "IREN", "SMH", "XLK"]:
    d = pd.concat([r[f], r["NVDA"]], axis=1).dropna()
    b, n = beta(d[f], d["NVDA"])
    bd, _ = beta(d[f][d["NVDA"] < 0], d["NVDA"][d["NVDA"] < 0])
    bu, _ = beta(d[f][d["NVDA"] > 0], d["NVDA"][d["NVDA"] > 0])
    worst = d.nsmallest(30, "NVDA")
    cap = float((worst[f].sum()) / (worst["NVDA"].sum()))
    best = d.nlargest(30, "NVDA")
    capu = float((best[f].sum()) / (best["NVDA"].sum()))
    bs, _ = beta(r[f], r["SMH"])
    bp, _ = beta(r[f], r["SPY"])
    print(
        f"  {f:5s} {n:5d}  {d[f].corr(d['NVDA']):.2f}   {b:5.2f}        {bd:5.2f}                 {bu:5.2f}            capture worst-30 {cap:4.2f} / best-30 {capu:4.2f} | {bs:5.2f} | {bp:5.2f}"
    )
    if f in ("NBIS", "CRWV", "IREN"):
        own = d[f].std() * np.sqrt(252)
        resid = (d[f] - b * d["NVDA"]).std() * np.sqrt(252)
        print(
            f"         yearly swing {100 * own:.0f}% of which NOT explained by NVDA {100 * resid:.0f}% | days it moved the OPPOSITE way to NVDA on NVDA's 30 worst days: {int((worst[f] > 0).sum())} of 30"
        )
# rolling stability of the NBIS beta
d = pd.concat([r["NBIS"], r["NVDA"]], axis=1).dropna()
roll = d["NBIS"].rolling(60).cov(d["NVDA"]) / d["NVDA"].rolling(60).var()
print(
    "\nNBIS beta to NVDA over rolling 60 days: min %.2f, median %.2f, max %.2f, latest %.2f"
    % (roll.min(), roll.median(), roll.max(), roll.iloc[-1])
)
