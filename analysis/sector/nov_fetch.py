"""Fresh daily bars (unadjusted OHLC plus adjusted close) for the November 2026 look.

Run:  uv run --no-project --with yfinance --with pandas --with numpy \
          python analysis/sector/nov_fetch.py analysis/sector

Writes to analysis/sector/nov_data/ (gitignored, re-fetchable): the eleven sector funds, the
index and theme funds from 1998, and every holding and follower named in holdings.json and
followers.json from 2025. Existing files are kept, so delete the folder to refresh.
"""

import json
import os
import sys

import pandas as pd
import yfinance as yf

root = sys.argv[1]
out = f"{root}/nov_data"
os.makedirs(out, exist_ok=True)

SECTORS = ["XLK", "XLE", "XLF", "XLV", "XLY", "XLP", "XLI", "XLB", "XLU", "XLRE", "XLC"]
LONG = SECTORS + ["SPY", "QQQ", "RSP", "IWM", "SMH", "IGV", "KRE", "ITB"]

hold = json.load(open(f"{root}/holdings.json"))
foll = json.load(open(f"{root}/followers.json"))
members = sorted({t for v in hold.values() for t, _ in v})
followers = sorted({d["ticker"] for v in foll.values() for d in v})


def get(sym, start):
    df = yf.download(sym, start=start, auto_adjust=False, progress=False, threads=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]].dropna()


bad = []
for group, start in ((LONG, "1998-01-01"), (members + followers, "2025-01-01")):
    for s in group:
        path = f"{out}/{s.replace('/', '-')}.csv"
        if os.path.exists(path):
            continue
        try:
            df = get(s, start)
            if len(df) == 0:
                raise ValueError("empty")
            df.to_csv(path)
        except Exception as e:  # noqa: BLE001
            bad.append((s, str(e)[:60]))
print("long", len(LONG), "members", len(members), "followers", len(followers), "failed", bad)
for s in ("SPY", "QQQ", "XLK"):
    d = pd.read_csv(f"{out}/{s}.csv", index_col=0, parse_dates=True)
    print(s, len(d), d.index[0].date(), d.index[-1].date(), round(float(d["Close"].iloc[-1]), 2))
