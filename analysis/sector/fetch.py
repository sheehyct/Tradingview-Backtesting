import sys
import yfinance as yf
import pandas as pd

out = sys.argv[1]
syms = ["XLK", "XLE", "XLF", "XLV", "XLY", "XLP", "XLI", "XLB", "XLU", "XLRE", "XLC", "SPY", "RSP"]
for s in syms:
    df = yf.download(s, start="1998-01-01", auto_adjust=False, progress=False, threads=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    df.to_csv(f"{out}/{s}.csv")
    print(
        s, len(df), df.index[0].date(), df.index[-1].date(), round(float(df["Close"].iloc[-1]), 2)
    )
