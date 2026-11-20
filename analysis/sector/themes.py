"""Narrow look agreed with the owner 2026-11-19. Themes fixed up front: SMH and IGV under XLK,
KRE under XLF, ITB under XLY. Shared opens = one level. Daily closes. Count / description only.
Q1: does the thematic fund leave full agreement up BEFORE its parent sector does?
Q2: when the sector is weak, do followers fall more than their calm-day beta predicts?
Follower rule: among the thematic fund's top holdings (TODAY'S list: hindsight), drop the parent
sector fund's ten largest, require median 60-day dollar volume >= $50M, keep the three highest
betas to the thematic fund (last two years)."""

import sys
import json
import warnings
import yfinance as yf
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")
root = sys.argv[1]
PAIRS = [
    ("SMH", "XLK", "Semiconductors"),
    ("IGV", "XLK", "Software"),
    ("KRE", "XLF", "Regional banks"),
    ("ITB", "XLY", "Homebuilders"),
]
H = json.load(open(f"{root}/holdings.json"))


def fetch(t, start="1998-01-01"):
    df = yf.download(t, start=start, auto_adjust=False, progress=False, threads=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]].dropna()


def states(df):
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
    return pd.DataFrame({"L": L, "A": A}, index=i)


def episodes(st):  # leaving full up
    L, A = st["L"].values, st["A"].values
    full = A == L
    opp = A == 0
    out = []
    t = 1
    while t < len(A):
        if full[t - 1] and not full[t]:
            s0 = t
            lost_max = 0
            end = None
            outc = "open"
            u = t
            while u < len(A):
                lost_max = max(lost_max, L[u] - A[u])
                if full[u]:
                    outc, end = "healed", u
                    break
                if opp[u]:
                    outc, end = "every level", u
                    break
                u += 1
            last = end if end is not None else len(A) - 1
            out.append((s0, last, int(lost_max), outc, int(L[s0])))
            t = last
        t += 1
    return out


def slope(y, x):
    d = pd.concat([y, x], axis=1).dropna()
    return (
        (float(np.cov(d.iloc[:, 0], d.iloc[:, 1])[0, 1] / d.iloc[:, 1].var()), len(d))
        if len(d) >= 40
        else (np.nan, len(d))
    )


cache = {}


def get(t):
    if t not in cache:
        cache[t] = fetch(t)
    return cache[t]


for theme, parent, label in PAIRS:
    T, P = get(theme), get(parent)
    idx = T.index.intersection(P.index)
    sT, sP = states(T).loc[idx], states(P).loc[idx]
    pf = (sP.A == sP.L).values
    tf = (sT.A == sT.L).values
    n = len(idx)
    eps = [e for e in episodes(sP) if e[4] >= 3 and e[3] != "open"]
    deep = [e for e in eps if e[2] >= 3 or e[3] == "every level"]
    shallow = [e for e in eps if e[2] == 1]

    def out_before(E):
        return np.mean([not tf[e[0] - 1] for e in E]) if E else np.nan

    def lead(E):
        v = []
        for e in E:
            k = 0
            j = e[0] - 1
            while j - k >= 0 and not tf[j - k]:
                k += 1
            v.append(k)
        return np.median(v) if v else np.nan

    print(
        f"\n=== {label}: {theme} inside {parent}  ({idx[0].date()} to {idx[-1].date()}, {n} days) ==="
    )
    print("Q1  theme fund already out of full agreement up ...")
    print(
        f"    on any day the sector is in full agreement up (baseline): {100 * np.mean(~tf[pf]):.0f}%"
    )
    print(
        f"    the day before a sector crack that healed after one level (n={len(shallow)}): {100 * out_before(shallow):.0f}%"
    )
    print(
        f"    the day before a sector crack that went deep (n={len(deep)}): {100 * out_before(deep):.0f}%   median days the theme had already been out: {lead(deep):.0f} (shallow: {lead(shallow):.0f})"
    )
    # forward: theme cracks first while sector still in full agreement
    deep_start = np.zeros(n, bool)
    any_start = np.zeros(n, bool)
    for e in deep:
        deep_start[e[0]] = True
    for e in eps:
        any_start[e[0]] = True

    def fwd(arr, t, k=10):
        return arr[t + 1 : t + 1 + k].any()

    base_days = [t for t in range(1, n - 10) if pf[t]]
    first = [t for t in range(1, n - 10) if pf[t] and tf[t - 1] and not tf[t]]
    stay = [t for t in range(1, n - 10) if pf[t] and tf[t]]
    print(
        f"    sector starts a DEEP crack within 10 days: from any full-agreement day {100 * np.mean([fwd(deep_start, t) for t in base_days]):.0f}% | on days the theme cracks first (n={len(first)}) {100 * np.mean([fwd(deep_start, t) for t in first]):.0f}% | while the theme is also in full agreement {100 * np.mean([fwd(deep_start, t) for t in stay]):.0f}%"
    )
    # followers
    try:
        th = yf.Ticker(theme).funds_data.top_holdings
    except Exception as e:
        print("   no holdings", e)
        continue
    ptop = {t for t, _ in H[parent]}
    cands = []
    rT = T["Adj Close"].pct_change()
    for tk, row in th.iterrows():
        tk = str(tk)
        if tk in ptop or not tk.replace("-", "").isalpha():
            continue
        try:
            d = get(tk)
        except Exception:
            continue
        if len(d) < 300:
            continue
        dv = float((d["Close"] * d["Volume"]).tail(60).median()) / 1e6
        b, _ = slope(d["Adj Close"].pct_change().tail(504), rT.tail(504))
        cands.append((tk, round(float(row["Holding Percent"]) * 100, 1), round(b, 2), round(dv)))
    cands.sort(key=lambda x: -x[2])
    print(
        "Q2  candidates (ticker, weight % in the theme fund, beta to the theme fund, median $M traded/day):",
        cands,
    )
    picks = [c for c in cands if c[3] >= 50][:3]
    print(
        "    followers kept:",
        [c[0] for c in picks],
        "| dropped as parent top-ten:",
        sorted(ptop & {str(t) for t in th.index}),
    )
    rP = P["Adj Close"].pct_change()
    weak_prev = (
        pd.Series(((sP.L - sP.A) >= 2).values, index=idx).shift(1).fillna(False).astype(bool)
    )
    calm_prev = pd.Series(pf, index=idx).shift(1).fillna(False).astype(bool)
    in_deep = pd.Series(False, index=idx)
    for e in deep:
        in_deep.iloc[e[0] : e[1] + 1] = True
    print(
        "    name   since     beta: calm days | sector-weak days | sector down days | up days || on sector-weak days: sector avg/day, follower avg/day, what calm beta predicts, gap || inside deep cracks (hindsight label): follower move per 1% sector move"
    )
    for tk, w, b2, dv in picks:
        d = get(tk)
        rf = d["Adj Close"].pct_change().reindex(idx)
        rp = rP.reindex(idx)
        ok = rf.notna() & rp.notna()
        bc, nc = slope(rf[ok & calm_prev], rp[ok & calm_prev])
        bw, nw = slope(rf[ok & weak_prev], rp[ok & weak_prev])
        bd, _ = slope(rf[ok & (rp < 0)], rp[ok & (rp < 0)])
        bu, _ = slope(rf[ok & (rp > 0)], rp[ok & (rp > 0)])
        m = ok & weak_prev
        ms, mf = rp[m].mean() * 1e4, rf[m].mean() * 1e4
        gap = mf - bc * ms
        se = (rf[m] - bc * rp[m]).std() / np.sqrt(m.sum()) * 1e4
        dd = ok & in_deep
        cap = rf[dd].sum() / rp[dd].sum() if rp[dd].sum() != 0 else np.nan
        print(
            f"    {tk:5s} {str(rf[ok].index[0].date())}   {bc:4.2f} (n={nc}) | {bw:4.2f} (n={nw}) | {bd:4.2f} | {bu:4.2f} || {ms:+.1f}bp, {mf:+.1f}bp, {bc * ms:+.1f}bp, gap {gap:+.1f}bp/day (+/-{2 * se:.1f}) || {cap:4.2f} over {int(dd.sum())} days"
        )
