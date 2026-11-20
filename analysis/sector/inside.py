"""Look inside each sector at its ten largest holdings (TODAY'S list and weights: hindsight).
Same level rule: distinct opens among week/month/quarter/half-year/year count once.
At each day a sector fund leaves full agreement, how many of its ten largest names had ALREADY left it?
Count only: states, no returns, no rule."""

import sys
import json
import pandas as pd
import numpy as np

root = sys.argv[1]
PER = ["W", "M", "Q", "H", "Y"]
H = json.load(open(f"{root}/holdings.json"))


def states(path, start=None):
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    i = df.index
    iso = i.isocalendar()
    keys = {
        "W": iso["year"].astype(int).values * 100 + iso["week"].astype(int).values,
        "M": i.year * 100 + i.month,
        "Q": i.year * 10 + i.quarter,
        "H": i.year * 10 + ((i.month - 1) // 6),
        "Y": i.year,
    }
    O = np.column_stack(
        [
            df.groupby(pd.Series(np.asarray(k), index=i))["Open"].transform("first").round(4).values
            for k in keys.values()
        ]
    )
    C = df["Close"].values
    L = np.array([len(set(r)) for r in O])
    A = np.array([len({x for x in r if c > x}) for r, c in zip(O, C)])
    return pd.DataFrame({"L": L, "A": A, "close": C}, index=i)


rows = []
for s, hold in H.items():
    etf = states(f"{root}/data/{s}.csv")
    etf = etf[etf.index >= "2010-01-01"]
    mem = {t: states(f"{root}/members/{t.replace('/', '-')}.csv") for t, _ in hold}
    wt = dict(hold)
    top1 = hold[0][0]
    top3 = [t for t, _ in hold[:3]]
    L, A, idx = etf["L"].values, etf["A"].values, etf.index
    for side in ("up", "down"):
        full = (A == L) if side == "up" else (A == 0)
        opp = (A == 0) if side == "up" else (A == L)
        t = 1
        while t < len(A):
            if full[t - 1] and not full[t]:
                st = t
                lost_max = 0
                end = None
                outc = "open"
                u = t
                while u < len(A):
                    lost = (L[u] - A[u]) if side == "up" else A[u]
                    lost_max = max(lost_max, lost)
                    if full[u]:
                        outc, end = "healed", u
                        break
                    if opp[u]:
                        outc, end = "every level", u
                        break
                    u += 1
                last = end if end is not None else len(A) - 1
                prev = idx[st - 1]
                n_have = 0
                n_out = 0
                w_have = 0.0
                w_out = 0.0
                top1_out = None
                top3_out = 0
                lead_days = []
                for tk, m in mem.items():
                    if prev not in m.index:
                        continue
                    r = m.loc[prev]
                    n_have += 1
                    w_have += wt[tk]
                    mfull = (r.A == r.L) if side == "up" else (r.A == 0)
                    if not mfull:
                        n_out += 1
                        w_out += wt[tk]
                        if tk in top3:
                            top3_out += 1
                        # how many trading days has this name been out of full agreement
                        mm = m.loc[:prev]
                        f = ((mm.A == mm.L) if side == "up" else (mm.A == 0)).values
                        k = 0
                        while k < len(f) and not f[-1 - k]:
                            k += 1
                        lead_days.append(k)
                    if tk == top1:
                        top1_out = not mfull
                if n_have >= 6:
                    rows.append(
                        dict(
                            sym=s,
                            side=side,
                            start=idx[st],
                            L=int(L[st]),
                            lost_max=int(lost_max),
                            outcome=outc,
                            days=last - st,
                            n_have=n_have,
                            n_out=n_out,
                            w_share=round(w_out / w_have, 3),
                            top1_out=top1_out,
                            top3_out=top3_out,
                            lead_med=float(np.median(lead_days)) if lead_days else 0.0,
                        )
                    )
                t = last
            t += 1
E = pd.DataFrame(rows)
E.to_csv(f"{root}/inside.csv", index=False)


def deep(x):
    return (x.lost_max >= 3) | (x.outcome == "every level")


for side, nm in (
    ("up", "SECTOR LEAVES FULL AGREEMENT UP"),
    ("down", "SECTOR LEAVES FULL AGREEMENT DOWN"),
):
    d = E[(E.side == side) & (E.outcome != "open") & (E.L >= 3)]
    print(
        f"\n{nm}  (since 2010, 3+ distinct levels, n={len(d)}; distinct crack dates {d.start.nunique()})"
    )
    print(
        f"  base rate: healed after one level {100 * (d.lost_max == 1).mean():.0f}% | lost 3+ levels or every level {100 * deep(d).mean():.0f}%"
    )
    print("  by how many of the ten largest had ALREADY left full agreement the day before:")
    for lo, hi in ((0, 2), (3, 4), (5, 6), (7, 10)):
        x = d[(d.n_out >= lo) & (d.n_out <= hi)]
        if len(x):
            print(
                f"    {lo}-{hi} names: n={len(x):4d} | healed after one level {100 * (x.lost_max == 1).mean():3.0f}% | deep {100 * deep(x).mean():3.0f}% | median days in crack {x.days.median():.0f}"
            )
    print("  by share of top-ten WEIGHT already out:")
    for lo, hi in ((0, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 1.01)):
        x = d[(d.w_share >= lo) & (d.w_share < hi)]
        if len(x):
            print(
                f"    {int(lo * 100):3d}-{int(min(hi, 1) * 100):3d}%: n={len(x):4d} | healed after one level {100 * (x.lost_max == 1).mean():3.0f}% | deep {100 * deep(x).mean():3.0f}%"
            )
    for flag, lab in (
        (True, "largest name already out"),
        (False, "largest name still in full agreement"),
    ):
        x = d[d.top1_out == flag]
        if len(x):
            print(
                f"    {lab}: n={len(x):4d} | healed after one level {100 * (x.lost_max == 1).mean():3.0f}% | deep {100 * deep(x).mean():3.0f}%"
            )
    print(
        f"  typical picture the day before a sector crack: {d.n_out.median():.0f} of {d.n_have.median():.0f} largest names already out; {100 * d.w_share.median():.0f}% of top-ten weight; largest name already out in {100 * d.top1_out.mean():.0f}% of cracks"
    )
    print(
        "  per sector: median names already out | share of cracks where the largest name was already out"
    )
    print(
        "   ",
        " ".join(
            f"{s}:{g.n_out.median():.0f}|{100 * g.top1_out.mean():.0f}%"
            for s, g in d.groupby("sym")
        ),
    )
print("\nOPEN CRACKS TODAY, the inside read the day before each began:")
print(
    E[E.outcome == "open"][
        ["sym", "side", "start", "L", "lost_max", "n_out", "n_have", "w_share", "top1_out"]
    ].to_string(index=False)
)
# today's member states
print(
    "\nTODAY, ten largest per sector: names above ALL of their own levels / above none / in between; and the largest name's count"
)
for s, hold in H.items():
    fu = fd = mid = 0
    lab = ""
    for k, (tk, w) in enumerate(hold):
        m = states(f"{root}/members/{tk.replace('/', '-')}.csv").iloc[-1]
        if m.A == m.L:
            fu += 1
        elif m.A == 0:
            fd += 1
        else:
            mid += 1
        if k < 3:
            lab += f" {tk} {int(m.A)}/{int(m.L)}"
    print(f"  {s:5s} full up {fu} | full down {fd} | in conflict {mid} | three largest:{lab}")
