import sys
import json
import yfinance as yf

out = sys.argv[1]
SECT = ["XLK", "XLE", "XLF", "XLV", "XLY", "XLP", "XLI", "XLB", "XLU", "XLRE", "XLC"]
H = {}
for s in SECT:
    try:
        th = yf.Ticker(s).funds_data.top_holdings
        H[s] = [(str(i), round(float(r["Holding Percent"]) * 100, 2)) for i, r in th.iterrows()]
        print(s, " ".join(f"{t}:{w}" for t, w in H[s]))
    except Exception as e:
        print(s, "FAILED", type(e).__name__, str(e)[:80])
json.dump(H, open(f"{out}/holdings.json", "w"), indent=1)
syms = sorted({t for v in H.values() for t, _ in v})
print("members:", len(syms))
df = yf.download(
    syms, start="2009-06-01", auto_adjust=False, progress=False, group_by="ticker", threads=True
)
ok = 0
for t in syms:
    try:
        d = df[t][["Open", "High", "Low", "Close"]].dropna()
        if len(d) > 200:
            d.to_csv(f"{out}/members/{t.replace('/', '-')}.csv")
            ok += 1
        else:
            print("short/none:", t, len(d))
    except Exception as e:
        print("missing:", t, type(e).__name__)
print("saved", ok)
