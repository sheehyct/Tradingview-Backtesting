"""First look, count only: sector continuity states on week/month/quarter/half-year/year.
State per period at each daily close: close > that period's open -> up, else down (flat = down).
FULL UP = all five up; FULL DOWN = all five down; else CONFLICT.
No returns, no P&L, no rule."""

import sys
import json
import pandas as pd
import numpy as np

data, out = sys.argv[1], sys.argv[2]
SECT = {
    "XLK": "Technology",
    "XLE": "Energy",
    "XLF": "Financials",
    "XLV": "Health care",
    "XLY": "Discretionary",
    "XLP": "Staples",
    "XLI": "Industrials",
    "XLB": "Materials",
    "XLU": "Utilities",
    "XLRE": "Real estate",
    "XLC": "Communications",
}
PER = ["W", "M", "Q", "H", "Y"]


def load(s):
    df = pd.read_csv(f"{data}/{s}.csv", index_col=0, parse_dates=True)
    i = df.index
    iso = i.isocalendar()
    keys = {
        "W": iso["year"].astype(int).values * 100 + iso["week"].astype(int).values,
        "M": i.year * 100 + i.month,
        "Q": i.year * 10 + i.quarter,
        "H": i.year * 10 + ((i.month - 1) // 6),
        "Y": i.year,
    }
    for p, k in keys.items():
        k = pd.Series(np.asarray(k), index=i)
        df[p + "_open"] = df.groupby(k)["Open"].transform("first")
        df[p + "_new"] = k.ne(k.shift(1))
        df[p] = (df["Close"] > df[p + "_open"]).astype(int)
    df["n_up"] = df[PER].sum(axis=1)
    df["new_any"] = df[[p + "_new" for p in PER]].any(axis=1)
    return df


frames = {s: load(s) for s in list(SECT) + ["SPY", "RSP"]}
res = {"asof": str(frames["SPY"].index[-1].date()), "sectors": {}, "defs": __doc__}


def episodes(df, full):  # full = 5 (out of FULL UP) or 0 (out of FULL DOWN)
    n = df["n_up"].values
    idx = df.index
    eps = []
    t = 1
    while t < len(n):
        if n[t - 1] == full and n[t] != full:
            start = t
            worst = n[t]
            end = None
            outcome = "open"
            u = t
            while u < len(n):
                worst = min(worst, n[u]) if full == 5 else max(worst, n[u])
                if n[u] == full:
                    outcome = "healed"
                    end = u
                    break
                if n[u] == 5 - full:
                    outcome = "cascaded"
                    end = u
                    break
                u += 1
            first = [p for p in PER if df[p].values[start] != (1 if full == 5 else 0)]
            eps.append(
                {
                    "start": str(idx[start].date()),
                    "days": (end - start) if end else len(n) - start,
                    "outcome": outcome,
                    "depth": int(5 - worst if full == 5 else worst),
                    "new_period_day": bool(df["new_any"].values[start]),
                    "first_flipped": first,
                }
            )
            t = end if end else len(n)
        t += 1
    return eps


for s, name in SECT.items():
    df = frames[s]
    n = df["n_up"]
    eu, ed = episodes(df, 5), episodes(df, 0)

    def summ(eps):
        done = [e for e in eps if e["outcome"] != "open"]
        d = {
            "cracks": len(eps),
            "healed": sum(e["outcome"] == "healed" for e in eps),
            "cascaded": sum(e["outcome"] == "cascaded" for e in eps),
            "open": sum(e["outcome"] == "open" for e in eps),
            "on_new_period_day": sum(e["new_period_day"] for e in eps),
            "depth": {str(k): sum(e["depth"] == k for e in done) for k in range(1, 6)},
            "median_days_healed": float(
                np.median([e["days"] for e in eps if e["outcome"] == "healed"])
            )
            if any(e["outcome"] == "healed" for e in eps)
            else None,
            "median_days_cascaded": float(
                np.median([e["days"] for e in eps if e["outcome"] == "cascaded"])
            )
            if any(e["outcome"] == "cascaded" for e in eps)
            else None,
            "first_flip_week_only": sum(e["first_flipped"] == ["W"] for e in eps),
        }
        return d

    res["sectors"][s] = {
        "name": name,
        "first": str(df.index[0].date()),
        "days": len(df),
        "share_full_up": round(float((n == 5).mean()), 3),
        "share_full_down": round(float((n == 0).mean()), 3),
        "share_conflict": round(float(((n > 0) & (n < 5)).mean()), 3),
        "today": {p: int(df[p].iloc[-1]) for p in PER},
        "today_n_up": int(n.iloc[-1]),
        "from_full_up": summ(eu),
        "from_full_down": summ(ed),
        "open_episode_up": [e for e in eu if e["outcome"] == "open"],
        "open_episode_down": [e for e in ed if e["outcome"] == "open"],
        "last_up_eps": eu[-3:],
        "last_down_eps": ed[-3:],
    }

# breadth across the nine sectors with full history (plus all eleven where present)
nine = [s for s in SECT if s not in ("XLRE", "XLC")]
N = pd.DataFrame({s: frames[s]["n_up"] for s in SECT})
N9 = N[nine].dropna()
fu, fd = (N9 == 5).sum(axis=1), (N9 == 0).sum(axis=1)
res["breadth9"] = {
    "dist_full_up": {str(k): round(float((fu == k).mean()), 3) for k in range(10)},
    "dist_full_down": {str(k): round(float((fd == k).mean()), 3) for k in range(10)},
}
allN = N.dropna()
res["breadth11_today"] = {
    "full_up": int((allN.iloc[-1] == 5).sum()),
    "full_down": int((allN.iloc[-1] == 0).sum()),
    "conflict": int(((allN.iloc[-1] > 0) & (allN.iloc[-1] < 5)).sum()),
}
# weekly strip, last 30 weeks, n_up per sector at each week's last close
wk = N.copy()
iso = wk.index.isocalendar()
wk["k"] = iso["year"].astype(int).values * 100 + iso["week"].astype(int).values
strip = wk.groupby("k").tail(1).drop(columns="k").tail(30)
res["strip_dates"] = [str(d.date()) for d in strip.index]
res["strip"] = {s: [int(v) for v in strip[s].values] for s in SECT}
# full daily state matrix for a chart
N.to_csv(f"{out}/n_up_daily.csv")
for s in ("SPY", "RSP"):
    res[s] = {"today": {p: int(frames[s][p].iloc[-1]) for p in PER}}
json.dump(res, open(f"{out}/census.json", "w"), indent=1)

print("as of", res["asof"])
print("\nTODAY (1 = above that period's open)   W M Q H Y   up-count")
for s in list(SECT) + ["SPY", "RSP"]:
    t = res["sectors"][s]["today"] if s in SECT else res[s]["today"]
    print(f"  {s:5s} {SECT.get(s, ''):15s} {' '.join(str(t[p]) for p in PER)}   {sum(t.values())}")
print("\nSHARE OF DAYS, and cracks out of FULL UP / FULL DOWN")
print(
    "  sym   fullUp conflict fullDn | UP: cracks healed cascaded open newDay wkOnly medHeal medCasc depth1..5 | DOWN: cracks healed cascaded newDay medHeal medCasc depth1..5"
)
tot = {"u": [0, 0, 0, 0], "d": [0, 0, 0, 0]}
for s in SECT:
    r = res["sectors"][s]
    u, d = r["from_full_up"], r["from_full_down"]
    print(
        f"  {s:5s} {r['share_full_up']:.3f} {r['share_conflict']:.3f}   {r['share_full_down']:.3f} | {u['cracks']:4d} {u['healed']:4d} {u['cascaded']:3d} {u['open']} {u['on_new_period_day']:4d} {u['first_flip_week_only']:4d} {u['median_days_healed']} {u['median_days_cascaded']} {list(u['depth'].values())} | {d['cracks']:4d} {d['healed']:4d} {d['cascaded']:3d} {d['on_new_period_day']:4d} {d['median_days_healed']} {d['median_days_cascaded']} {list(d['depth'].values())}"
    )
print(
    "\nBREADTH (nine sectors since 1998): share of days with k sectors FULL UP:",
    res["breadth9"]["dist_full_up"],
)
print("share of days with k sectors FULL DOWN:", res["breadth9"]["dist_full_down"])
print("today, all eleven:", res["breadth11_today"])
print("\nLAST 30 WEEK-ENDS, up-count per sector (5 = full up, 0 = full down)")
print("  week ending    " + " ".join(f"{s:>4s}" for s in SECT))
for i, d in enumerate(res["strip_dates"]):
    print(f"  {d}     " + " ".join(f"{res['strip'][s][i]:>4d}" for s in SECT))
