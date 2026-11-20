"""Cache daily bars (unadjusted open / high / low / close) for the sector look.

Run:  uv run --no-project --with yfinance --with pandas \
          python analysis/sector/fetch.py analysis/sector/data [TICKER ...]

With no tickers it fetches the eleven sector funds, SPY, RSP and the four theme funds.
"""

import sys

import pandas as pd
import yfinance as yf

SECTORS = ["XLK", "XLE", "XLF", "XLV", "XLY", "XLP", "XLI", "XLB", "XLU", "XLRE", "XLC"]
REFERENCE = ["SPY", "RSP"]
THEMES = ["SMH", "IGV", "KRE", "ITB"]

out = sys.argv[1]
syms = sys.argv[2:] or SECTORS + REFERENCE + THEMES
for s in syms:
    df = yf.download(s, start="1998-01-01", auto_adjust=False, progress=False, threads=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    df.to_csv(f"{out}/{s}.csv")
    print(
        s, len(df), df.index[0].date(), df.index[-1].date(), round(float(df["Close"].iloc[-1]), 2)
    )
