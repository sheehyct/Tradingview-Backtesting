"""Separate calendar resets from price moves. A crack is a RESET crack when a period that flipped
opened new that same day (price is only below a fresh open). An episode is CLEAN when no new
quarter, half-year or year began between its first day and its last. Count only."""

import sys
import pandas as pd
import numpy as np

data, out = sys.argv[1], sys.argv[2]
SECT = ["XLK", "XLE", "XLF", "XLV", "XLY", "XLP", "XLI", "XLB", "XLU", "XLRE", "XLC"]
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
    return df


rows = []
for s in SECT:
    df = load(s)
    n = df["n_up"].values
    idx = df.index
    for full in (5, 0):
        t = 1
        while t < len(n):
            if n[t - 1] == full and n[t] != full:
                st = t
                worst = n[t]
                end = None
                outc = "open"
                u = t
                while u < len(n):
                    worst = min(worst, n[u]) if full == 5 else max(worst, n[u])
                    if n[u] == full:
                        outc, end = "healed", u
                        break
                    if n[u] == 5 - full:
                        outc, end = "cascaded", u
                        break
                    u += 1
                want = 1 if full == 5 else 0
                flipped = [p for p in PER if df[p].values[st] != want]
                reset = any(df[p + "_new"].values[st] for p in flipped)
                last = end if end is not None else len(n) - 1
                big = bool(df["Q_new"].values[st + 1 : last + 1].any()) or bool(
                    df["Q_new"].values[st] and any(p in flipped for p in ("Q", "H", "Y"))
                )
                rows.append(
                    dict(
                        sym=s,
                        side="up" if full == 5 else "down",
                        start=idx[st],
                        days=(last - st),
                        outcome=outc,
                        depth=int(5 - worst if full == 5 else worst),
                        reset=reset,
                        big_reset=big,
                        first="+".join(flipped),
                        year=idx[st].year,
                    )
                )
                t = last
            t += 1
E = pd.DataFrame(rows)
E.to_csv(f"{out}/episodes.csv", index=False)


def table(df, label):
    done = df[df.outcome != "open"]
    if not len(done):
        return
    dist = [int((done.depth == k).sum()) for k in range(1, 6)]
    pct = [round(100 * x / len(done)) for x in dist]
    print(
        f"  {label:44s} n={len(done):5d}  dominoes fallen 1/2/3/4/5: {pct} %   median days: healed {done[done.outcome == 'healed'].days.median()}, went all the way {done[done.outcome == 'cascaded'].days.median() if (done.outcome == 'cascaded').any() else None}"
    )


for side, nm in (("up", "OUT OF FULL UP"), ("down", "OUT OF FULL DOWN")):
    d = E[E.side == side]
    print(f"\n{nm} (all eleven sectors pooled)")
    table(d, "every crack")
    table(d[d.reset], "crack on a fresh period open (reset)")
    table(d[~d.reset], "crack by price (no fresh open involved)")
    table(d[(~d.reset) & (~d.big_reset)], "by price, no new quarter/half/year inside")
    c = d[(~d.reset)]
    print("   by-price cracks, what flipped first:", c["first"].value_counts().head(6).to_dict())
    for k in (1, 2, 3):
        sub = c[(c.outcome != "open")]
        reached = sub[sub.depth >= k]
        nxt = sub[sub.depth >= k + 1]
        print(
            f"   of by-price cracks that lost at least {k} period(s) (n={len(reached)}), share that went on to lose {k + 1} or more: {round(100 * len(nxt) / max(len(reached), 1))}%"
        )
    deep = c[(c.outcome == "cascaded") & (~c.big_reset)]
    print(
        f"   by-price, went all the way inside one quarter: {len(deep)}; by year: {deep.year.value_counts().sort_index().to_dict()}"
    )
# breadth states
N = pd.read_csv(f"{out}/n_up_daily.csv", index_col=0, parse_dates=True)
nine = [c for c in N.columns if c not in ("XLRE", "XLC")]
N9 = N[nine].dropna()
fu, fd = (N9 == 5).sum(axis=1), (N9 == 0).sum(axis=1)
print("\nBREADTH, nine sectors since 1998")
print(
    "  days with NO sector in full agreement either way (all in conflict):",
    round(100 * float(((fu == 0) & (fd == 0)).mean()), 1),
    "%",
)
print(
    "  days with 5+ sectors full up:",
    round(100 * float((fu >= 5).mean()), 1),
    "%   5+ full down:",
    round(100 * float((fd >= 5).mean()), 1),
    "%",
)
mean_up = N9.mean(axis=1)
print(
    "  average up-count across the nine, today:",
    round(float(mean_up.iloc[-1]), 2),
    " percentile vs history:",
    round(100 * float((mean_up < mean_up.iloc[-1]).mean())),
    " | 30 trading days ago:",
    round(float(mean_up.iloc[-31]), 2),
)
last_all_conf = (fu == 0) & (fd == 0)
runs = (last_all_conf != last_all_conf.shift()).cumsum()
cur = last_all_conf[runs == runs.iloc[-1]]
print(
    "  current all-in-conflict run length (trading days):",
    int(len(cur)) if bool(last_all_conf.iloc[-1]) else 0,
)
