"""Same count with shared opens treated as ONE level (the skill's coupling rule).
Levels = the distinct open prices among week/month/quarter/half-year/year on that day.
FULL UP = close above every distinct level; FULL DOWN = close at or below every one. Count only."""

import sys
import pandas as pd
import numpy as np

data, out = sys.argv[1], sys.argv[2]
SECT = ["XLK", "XLE", "XLF", "XLV", "XLY", "XLP", "XLI", "XLB", "XLU", "XLRE", "XLC"]
PER = ["W", "M", "Q", "H", "Y"]
rows = []
lv_share = []
for s in SECT:
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
    opens = {}
    newp = {}
    for p, k in keys.items():
        k = pd.Series(np.asarray(k), index=i)
        opens[p] = df.groupby(k)["Open"].transform("first").round(4).values
        newp[p] = k.ne(k.shift(1)).values
    O = np.column_stack([opens[p] for p in PER])
    C = df["Close"].values
    L = np.array([len(set(r)) for r in O])
    A = np.array([len({x for x in r if c > x}) for r, c in zip(O, C)])
    anynew = np.column_stack([newp[p] for p in PER]).any(axis=1)
    lv_share.append(pd.Series(L).value_counts(normalize=True))
    for full_up in (True, False):
        isfull = (A == L) if full_up else (A == 0)
        isopp = (A == 0) if full_up else (A == L)
        t = 1
        while t < len(C):
            if isfull[t - 1] and not isfull[t]:
                st = t
                lost_max = 0
                end = None
                outc = "open"
                u = t
                while u < len(C):
                    lost = (L[u] - A[u]) if full_up else A[u]
                    lost_max = max(lost_max, lost)
                    if isfull[u]:
                        outc, end = "healed", u
                        break
                    if isopp[u]:
                        outc, end = "all the way", u
                        break
                    u += 1
                last = end if end is not None else len(C) - 1
                rows.append(
                    dict(
                        sym=s,
                        side="up" if full_up else "down",
                        start=i[st],
                        L=int(L[st]),
                        lost_first=int((L[st] - A[st]) if full_up else A[st]),
                        lost_max=int(lost_max),
                        outcome=outc,
                        days=last - st,
                        fresh=bool(anynew[st]),
                        month=i[st].month,
                        year=i[st].year,
                    )
                )
                t = last
            t += 1
E = pd.DataFrame(rows)
E.to_csv(f"{out}/episodes_levels.csv", index=False)
print(
    "distinct levels on a day (share of days, pooled):",
    (pd.concat(lv_share, axis=1).mean(axis=1).sort_index() * 100).round(1).to_dict(),
)
for side, nm in (("up", "LEAVING FULL UP"), ("down", "LEAVING FULL DOWN")):
    d = E[(E.side == side) & (E.outcome != "open")]
    print(f"\n{nm}: {len(d)} cracks, {int(d.fresh.sum())} on a day a period opened new")
    for Lk in (2, 3, 4, 5):
        x = d[d.L == Lk]
        if len(x) < 30:
            continue
        one = (x.lost_max == 1).mean()
        allw = (x.outcome == "all the way").mean()
        print(
            f"  {Lk} distinct levels at the crack: n={len(x):4d} | healed after losing just one {100 * one:4.0f}% | healed after losing more {100 * (1 - one - allw):4.0f}% | lost every level {100 * allw:4.0f}% | median days: healed {x[x.outcome == 'healed'].days.median():.0f}, every level {x[x.outcome == 'all the way'].days.median():.0f}"
        )
    x = d[d.L >= 4]
    for k in (1, 2, 3):
        a = x[x.lost_max >= k]
        b = x[x.lost_max >= k + 1]
        print(
            f"  with 4+ distinct levels: of cracks that lost at least {k} (n={len(a)}), {100 * len(b) / max(len(a), 1):.0f}% went on to lose {k + 1} or more"
        )
    print(
        "  with 4+ levels, lost every level, count by year:",
        x[x.outcome == "all the way"].year.value_counts().sort_index().to_dict(),
    )
# open episodes today
print("\nOPEN TODAY:")
print(
    E[E.outcome == "open"][["sym", "side", "start", "L", "lost_max", "days"]].to_string(index=False)
)
