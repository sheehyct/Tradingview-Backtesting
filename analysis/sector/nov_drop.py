"""What the sector read showed ahead of the November 2026 index drop (count only, exploratory).

Run after nov_fetch.py:
    uv run --no-project --with pandas --with numpy python analysis/sector/nov_drop.py analysis/sector

Sections: A the index path; B the daily breadth strip; C each sector's last crack and what was
knowable the day before; D every crack since June priced as a short (the false alarms count);
E three ways to express a crack (fund, ten largest names, followers) and the pair against SPY;
F the base rate for a narrow tape at an index high. See RECEIPT.md items 8 to 10.
"""

import json
import sys

import numpy as np
import pandas as pd
from common import episodes, is_deep, level_state, open_matrix

root = sys.argv[1]
data = f"{root}/nov_data"

SECTORS = ["XLK", "XLE", "XLF", "XLV", "XLY", "XLP", "XLI", "XLB", "XLU", "XLRE", "XLC"]
NINE = ["XLK", "XLE", "XLF", "XLV", "XLY", "XLP", "XLI", "XLB", "XLU"]
THEMES = {"XLK": ["SMH", "IGV"], "XLF": ["KRE"], "XLY": ["ITB"]}
START = "2026-07-01"
FROM = pd.Timestamp("2026-06-01")


def load(s):
    return pd.read_csv(f"{data}/{s.replace('/', '-')}.csv", index_col=0, parse_dates=True)


px = {s: load(s) for s in SECTORS + ["SPY", "QQQ", "RSP", "IWM", "SMH", "IGV", "KRE", "ITB"]}
st = {s: level_state(px[s]) for s in px}
hold = json.load(open(f"{root}/holdings.json"))
foll = json.load(open(f"{root}/followers.json"))
mem = {t: level_state(load(t)) for s in SECTORS for t, _ in hold[s]}
spy = px["SPY"]["Adj Close"]
spy_peak = spy.loc[START:].idxmax()


def cushion(sym, i):
    """Distance from the close to the nearest and to the third level, in daily swings."""
    df = px[sym]
    c = df["Close"].iloc[i]
    sd = df["Adj Close"].pct_change().iloc[i - 19 : i + 1].std()
    below = sorted({x for x in open_matrix(df)[i] if x < c}, reverse=True)
    if not below:
        return np.nan, np.nan
    return (c / below[0] - 1) / sd, (c / below[min(3, len(below)) - 1] - 1) / sd


def out_days(sym, day):
    """Sessions in a row the fund has been out of full agreement up, counting this day."""
    s = st[sym]
    full = (s.A == s.L).values
    i = s.index.get_loc(day)
    n = 0
    while i - n >= 0 and not full[i - n]:
        n += 1
    return n


def names_out(sym, day):
    return sum(
        1 for t, _ in hold[sym] if day in mem[t].index and mem[t].loc[day].A < mem[t].loc[day].L
    )


def section_a():
    print("A. INDEX PATH (closes, dividends included)")
    for s in ("SPY", "QQQ", "RSP", "IWM"):
        a = px[s]["Adj Close"].loc[START:]
        pk = a.idxmax()
        print(
            f"  {s}: high close {pk.date()}  last {a.index[-1].date()}  "
            f"from high {100 * (a.iloc[-1] / a.loc[pk] - 1):+.1f}%"
        )
    print("  the index funds against their own period opens (W M Q H Y):")
    for s in ("SMH", "SPY", "QQQ"):
        om = open_matrix(px[s])
        for d in (spy_peak, px[s].index[-1]):
            i = px[s].index.get_loc(d)
            c = px[s]["Close"].iloc[i]
            tags = " ".join(f"{p}:{'above' if c > o else 'BELOW'}" for p, o in zip("WMQHY", om[i]))
            print(f"    {s} {d.date()} close {c:8.2f}  {tags}")


def section_b():
    idx = px["SPY"].loc["2026-09-15":].index
    print(
        "\nB. BREADTH STRIP: sectors of eleven in full agreement up / in conflict / full agreement"
    )
    print("   down; levels lost of levels in play; SPY % from its high close; SPY day %")
    hi = spy.loc[START:].cummax()
    day = 100 * spy.pct_change()
    for d in idx:
        up = dn = lost = tot = 0
        for s in SECTORS:
            r = st[s].loc[d]
            tot += r.L
            lost += r.L - r.A
            up += r.A == r.L
            dn += r.A == 0
        mark = "  <- SPY high close" if d == spy_peak else ""
        print(
            f"  {d.date()} {d.day_name()[:3]}  up {up:2d}  conf {11 - up - dn:2d}  down {dn:2d}"
            f"   lost {lost:2d}/{tot:2d}   SPY {100 * (spy.loc[d] / hi.loc[d] - 1):+5.1f}%"
            f"  day {day.loc[d]:+5.1f}%{mark}"
        )


def section_c():
    print(
        "\nC. EACH SECTOR'S LAST CRACK OUT OF FULL AGREEMENT UP (the day before = what was knowable)"
    )
    rows = []
    for s in SECTORS:
        e = episodes(st[s], "up")[-1]
        d0 = st[s].index[e["start"]]
        prev = st[s].index[e["start"] - 1]
        d1, d3 = cushion(s, e["start"] - 1)
        th = ", ".join(f"{t} {out_days(t, prev)}d" for t in THEMES.get(s, []))
        now = st[s].iloc[-1]
        a = px[s]["Adj Close"]
        rows.append(
            (d0, s, d1, d3, names_out(s, prev), th, e, now, 100 * (a.iloc[-1] / a.loc[d0] - 1))
        )
    for d0, s, d1, d3, n_out, th, e, now, since in sorted(rows, key=lambda r: r[0]):
        print(
            f"  {s:5s} {d0.date()}  cushion nearest {d1:4.1f} / third {d3:5.1f} daily swings   "
            f"big names out {n_out}/10   {th:16s} lost {e['lost_max']} at worst, "
            f"{int(now.L - now.A)}/{int(now.L)} now ({e['outcome']})   fund since crack close {since:+5.1f}%"
        )
    print("  theme funds, sessions out of full agreement up at the SPY high close and now:")
    for t in ("SMH", "IGV", "KRE", "ITB"):
        print(
            f"    {t}: at the SPY high {out_days(t, spy_peak)}, now {out_days(t, st[t].index[-1])}"
        )


def section_d():
    cu = pd.read_csv(f"{root}/cushion.csv")
    q1, q2 = cu[cu.side == "up"].d3.quantile([1 / 3, 2 / 3])
    rows = []
    for s in SECTORS:
        a = px[s]["Adj Close"]
        for e in episodes(st[s], "up"):
            d0 = st[s].index[e["start"]]
            if d0 < FROM:
                continue
            prev = st[s].index[e["start"] - 1]
            d1, d3 = cushion(s, e["start"] - 1)
            d_end = st[s].index[e["end"]]
            rows.append(
                dict(
                    sym=s,
                    date=d0,
                    days=e["end"] - e["start"],
                    lost=e["lost_max"],
                    outcome=e["outcome"],
                    deep=is_deep(e),
                    d1=d1,
                    d3=d3,
                    n_out=names_out(s, prev),
                    theme_out=max([out_days(t, prev) for t in THEMES.get(s, [])], default=-1),
                    pl=-100 * (a.loc[d_end] / a.loc[d0] - 1),
                    heat=100 * (a.loc[d0:d_end].max() / a.loc[d0] - 1),
                )
            )
    R = pd.DataFrame(rows)
    R["band"] = np.where(R.d3 < q1, "thin", np.where(R.d3 > q2, "thick", "middle"))
    print(
        "\nD. EVERY CRACK SINCE 2026-06-01: short the sector fund at the crack close, cover at the"
    )
    print(
        "   close of the day it heals (or hold to the last close). Equal size, no leverage, no fees."
    )
    print(
        f"   cushion bands from cushion.csv: thin under {q1:.1f} daily swings, thick over {q2:.1f}"
    )
    for s in SECTORS:
        d = R[R.sym == s]
        if len(d) == 0:
            print(f"  {s:5s} no crack (out of agreement the whole time)")
            continue
        h, o = d[d.outcome == "healed"], d[d.outcome != "healed"]
        print(
            f"  {s:5s} {len(d):2d} cracks  book {d.pl.sum():+6.1f}%   healed: {len(h):2d} trades "
            f"{h.pl.sum():+6.1f}%   not healed: {o.pl.sum():+6.1f}%"
        )
    h, o = R[R.outcome == "healed"], R[R.outcome != "healed"]
    print(
        f"  ALL   {len(R)} cracks  book {R.pl.sum():+.1f}%  per crack {R.pl.mean():+.2f}%  |  "
        f"{len(h)} healed: {h.pl.sum():+.1f}% total, {h.pl.mean():+.2f}% each, median {h.days.median():.0f} "
        f"sessions, {100 * (h.pl > 0).mean():.0f}% profitable  |  {len(o)} not healed: {o.pl.sum():+.1f}%"
    )
    print("   by what was known the day before (one autumn, clustered, a description not a rule):")
    cuts = (
        ("cushion thin", R[R.band == "thin"]),
        ("cushion middle", R[R.band == "middle"]),
        ("cushion thick", R[R.band == "thick"]),
        ("0-2 big names out", R[R.n_out <= 2]),
        ("3-6 out", R[(R.n_out >= 3) & (R.n_out <= 6)]),
        ("7-10 out", R[R.n_out >= 7]),
        ("theme out 6+ days", R[R.theme_out >= 6]),
        ("theme in or out under 6", R[(R.theme_out >= 0) & (R.theme_out < 6)]),
    )
    for lab, d in cuts:
        one = int(((d.outcome == "healed") & (d.lost <= 1)).sum())
        print(
            f"  {lab:24s} cracks {len(d):2d}  deep {int(d.deep.sum()):2d}  healed after one level {one:2d}"
            f"  book {d.pl.sum():+6.1f}%  largest single trade {d.pl.max():+5.1f}%"
        )
    print("   technology, every crack since June (the day before, then what happened):")
    for _, r in R[R.sym == "XLK"].iterrows():
        prev = st["XLK"].index[st["XLK"].index.get_loc(r.date) - 1]
        print(
            f"  {r.date.date()}  cushion {r.d1:4.1f} / {r.d3:5.1f} ({r.band:6s})  big names out {r.n_out}/10  "
            f"SMH {out_days('SMH', prev):3d}d IGV {out_days('IGV', prev):3d}d  ->  lost {r.lost}, "
            f"{r.outcome}, {r.days} sessions, short {r.pl:+5.1f}%"
        )


def basket(series_list, d0):
    """Equal-weight basket from the d0 close: short P/L % at the end, worst close against it."""
    rets = [
        a.loc[d0:] / a.loc[d0] - 1 for a in series_list if d0 in a.index and len(a.loc[d0:]) > 1
    ]
    if not rets:
        return np.nan, np.nan, 0
    b = pd.concat(rets, axis=1).mean(axis=1)
    return -100 * b.iloc[-1], 100 * b.max(), len(rets)


def section_e():
    print(
        "\nE. SHORT FROM THE LAST CRACK'S CLOSE TO THE LAST CLOSE (HINDSIGHT: this is the crack that"
    )
    print(
        "   did not heal). Equal size, no leverage, no fees. P/L %, worst close against the short."
    )
    for s in sorted(SECTORS, key=lambda x: st[x].index[episodes(st[x], "up")[-1]["start"]]):
        d0 = st[s].index[episodes(st[s], "up")[-1]["start"]]
        f_pl, f_heat, _ = basket([px[s]["Adj Close"]], d0)
        m_pl, m_heat, _ = basket([load(t)["Adj Close"] for t, _ in hold[s]], d0)
        o_pl, o_heat, o_n = basket([load(d["ticker"])["Adj Close"] for d in foll.get(s, [])], d0)
        spy_pl, _, _ = basket([spy], d0)
        fo = f"followers {o_pl:+6.1f}% heat {o_heat:4.1f}% (n{o_n})" if o_n else "followers none"
        print(
            f"  {s:5s} {d0.date()}  fund {f_pl:+6.1f}% heat {f_heat:4.1f}%   ten largest {m_pl:+6.1f}% "
            f"heat {m_heat:4.1f}%   {fo}   short fund, long SPY {f_pl - spy_pl:+6.1f}%"
        )
    d0 = st["XLK"].index[episodes(st["XLK"], "up")[-1]["start"]]
    print(f"   technology name by name from the {d0.date()} close (short P/L %):")
    groups = (
        ("ten largest", [t for t, _ in hold["XLK"]]),
        ("followers", [d["ticker"] for d in foll["XLK"]]),
    )
    for label, names in groups:
        out = []
        for t in names:
            a = load(t)["Adj Close"].loc[d0:]
            out.append((round(-100 * (a.iloc[-1] / a.iloc[0] - 1), 1), t))
        print(f"   {label}: " + ", ".join(f"{t} {v:+.1f}" for v, t in sorted(out, reverse=True)))


def section_f():
    idx = spy.index
    for s in NINE:
        idx = idx.intersection(st[s].index)
    full = pd.concat([(st[s].A == st[s].L).reindex(idx) for s in NINE], axis=1).sum(axis=1)
    a = spy.reindex(idx)
    near = a >= 0.99 * a.rolling(252).max()
    low40 = a[::-1].rolling(40).min()[::-1].shift(-1) / a - 1
    D = pd.DataFrame(
        {"full": full, "near": near, "f20": a.shift(-20) / a - 1, "low40": low40}
    ).dropna()
    D = D[D.near]
    print("\nF. BASE RATE since 1999, nine long-history sectors: days SPY closed within 1% of its")
    print(
        f"   one-year high close ({len(D)} days). On {spy_peak.date()}: {int(full.loc[spy_peak])} of nine in full agreement up."
    )
    g = pd.cut(
        D.full, bins=[-1, 2, 4, 6, 9], labels=["0 to 2 of nine", "3 to 4", "5 to 6", "7 to 9"]
    )
    for lab in g.cat.categories:
        d = D[g == lab]
        spells = int((d.index.to_series().diff().dt.days > 10).sum() + 1)
        print(
            f"   {lab:15s} days {len(d):4d} (about {spells:3d} spells)  next 20 sessions mean "
            f"{100 * d.f20.mean():+.1f}%  a close 7%+ lower within 40 sessions {100 * (d.low40 <= -0.07).mean():4.1f}%"
        )
    print(
        f"   all such days: a close 7%+ lower within 40 sessions {100 * (D.low40 <= -0.07).mean():.1f}%"
    )


for section in (section_a, section_b, section_c, section_d, section_e, section_f):
    section()
