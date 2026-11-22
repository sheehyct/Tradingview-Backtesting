"""Daily bars for the near-miss study (split-adjusted, not dividend-adjusted OHLC from 2000).

Run:  uv run --no-project --with yfinance --with pandas python analysis/nearmiss/fetch.py

The names are the sector look's: the eleven sector funds, three index funds, each fund's ten
largest holdings (analysis/sector/holdings.json) and the high-beta followers (followers.json).
Today's lists, so survivors only. Files land in analysis/nearmiss/data/ (gitignored); existing
files are kept, delete the folder to refresh.
"""

import json
import os
from pathlib import Path

import pandas as pd
import yfinance as yf

HERE = Path(__file__).parent
SECTOR = HERE.parent / "sector"
OUT = HERE / "data"
FUNDS = ["XLK", "XLE", "XLF", "XLV", "XLY", "XLP", "XLI", "XLB", "XLU", "XLRE", "XLC"]
INDEX = ["SPY", "QQQ", "IWM"]

hold = json.load(open(SECTOR / "holdings.json"))
foll = json.load(open(SECTOR / "followers.json"))
names = sorted(
    {t for v in hold.values() for t, _ in v} | {d["ticker"] for v in foll.values() for d in v}
)
os.makedirs(OUT, exist_ok=True)
bad = []
for s in FUNDS + INDEX + names:
    path = OUT / f"{s.replace('/', '-')}.csv"
    if path.exists():
        continue
    try:
        df = yf.download(s, start="2000-01-01", auto_adjust=False, progress=False, threads=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
        if len(df) < 60:
            raise ValueError(f"only {len(df)} bars")
        df.to_csv(path)
    except Exception as e:  # noqa: BLE001
        bad.append((s, str(e)[:60]))
json.dump({"funds": FUNDS, "index": INDEX, "names": names}, open(OUT / "universe.json", "w"))
print("funds", len(FUNDS), "index", len(INDEX), "names", len(names), "failed", bad)
