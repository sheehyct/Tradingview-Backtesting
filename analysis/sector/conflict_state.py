"""All nine long-history sectors in conflict: what followed, since 1999 (count only, exploratory).

Run after nov_fetch.py:
    uv run --no-project --with pandas --with numpy python analysis/sector/conflict_state.py analysis/sector

Definitions, fixed before the count was run (2026-11-21): the STATE is a day on which none of
the nine long-history sector funds is in full agreement up or down. The unit is a SPELL (the
first day in the state after a day out of it). The control is a day with SPY the same distance
off its one-year high close. Run with the week level and without it. See RECEIPT.md item 11.
"""

import sys

import numpy as np
import pandas as pd
from common import open_matrix

root = sys.argv[1]
data = f"{root}/nov_data"

NINE = ["XLK", "XLE", "XLF", "XLV", "XLY", "XLP", "XLI", "XLB", "XLU"]
HZ = [5, 10, 20, 40]
BANDS = [
    (-0.03, 0.01, "within 3% of the high"),
    (-0.10, -0.03, "3 to 10% off the high"),
    (-1.0, -0.10, "more than 10% off"),
]

px = {s: pd.read_csv(f"{data}/{s}.csv", index_col=0, parse_dates=True) for s in NINE + ["SPY"]}


def state(df, cols):
    opens = open_matrix(df)[:, cols]
    c = df["Close"].values
    n_levels = np.array([len(set(r)) for r in opens])
    n_above = np.array([len({x for x in r if cc > x}) for r, cc in zip(opens, c)])
    return pd.DataFrame({"L": n_levels, "A": n_above}, index=df.index)


def run(label, cols, list_long):
    st = {s: state(px[s], cols) for s in NINE}
    idx = px["SPY"].index
    for s in NINE:
        idx = idx.intersection(st[s].index)
    idx = idx[idx >= "1999-01-04"]
    up = pd.concat([(st[s].A == st[s].L).reindex(idx) for s in NINE], axis=1).sum(axis=1)
    dn = pd.concat([(st[s].A == 0).reindex(idx) for s in NINE], axis=1).sum(axis=1)
    lost = pd.concat([(st[s].L - st[s].A).reindex(idx) for s in NINE], axis=1).sum(axis=1)
    tot = pd.concat([st[s].L.reindex(idx) for s in NINE], axis=1).sum(axis=1)
    a = px["SPY"]["Adj Close"].reindex(idx)
    in_state = (up == 0) & (dn == 0)
    F = pd.DataFrame({f"f{h}": a.shift(-h) / a - 1 for h in HZ})
    F["low20"] = a[::-1].rolling(20).min()[::-1].shift(-1) / a - 1
    F["off"] = a / a.rolling(252, min_periods=60).max() - 1
    F["S"] = in_state
    F["start"] = in_state & ~in_state.shift(1, fill_value=False)
    F["up"], F["dn"], F["lost"], F["tot"], F["a"] = up, dn, lost, tot, a
    F = F.dropna(subset=["off"])

    print(f"\n===== {label} =====")
    print(
        f"days {len(F)}; in the state {int(F.S.sum())} ({100 * F.S.mean():.1f}%); "
        f"separate spells {int(F.start.sum())}"
    )
    sv, upv, dnv, av = F.S.values, F.up.values, F.dn.values, F.a.values
    spells = []
    for p in np.flatnonzero(F.start.values):
        q = p
        while q < len(sv) and sv[q]:
            q += 1
        if q >= len(sv):
            end = "open"
        elif upv[q] > 0 and dnv[q] == 0:
            end = "UP"
        elif dnv[q] > 0 and upv[q] == 0:
            end = "DOWN"
        else:
            end = "both"
        spells.append((p, q - p, end))
    lens = np.array([n for _, n, _ in spells])
    ends = np.array([e for _, _, e in spells])
    print(
        f"spell length in sessions: median {np.median(lens):.0f}, three in four end within "
        f"{np.percentile(lens, 75):.0f}, longest {lens.max()}; five or more sessions: {int((lens >= 5).sum())}"
    )
    print(
        f"how a spell ends: a sector back in full agreement UP first {100 * (ends == 'UP').mean():.0f}%, "
        f"one in full agreement DOWN first {100 * (ends == 'DOWN').mean():.0f}%"
    )
    day5 = pd.Series(False, index=F.index)
    for p, n, _ in spells:
        if n >= 5:
            day5.iloc[p + 4] = True

    def line(tag, d):
        if len(d) < 5:
            print(f"  {tag:46s} n {len(d):4d}  (too few)")
            return
        parts = "  ".join(
            f"{h:2d}d {100 * d[f'f{h}'].mean():+5.2f}% (up {100 * (d[f'f{h}'] > 0).mean():3.0f}%)"
            for h in HZ
        )
        print(
            f"  {tag:46s} n {len(d):4d}  {parts}  | a close 5%+ lower within 20: "
            f"{100 * (d.low20 <= -0.05).mean():4.1f}%"
        )

    print(
        "SPY afterwards: average and share of times higher (rows with no future yet count as not higher)"
    )
    line("every day (baseline)", F)
    line("spell start: first day all nine in conflict", F[F.start])
    line("fifth day of a spell (it has persisted)", F[day5])
    print("the kill test: same distance off the high, state against no state")
    for lo, hi, name in BANDS:
        b = F[(F.off > lo) & (F.off <= hi)]
        line(f"{name}: spell starts", b[b.start])
        line(f"{name}: fifth day of a spell", b[day5.reindex(b.index)])
        line(f"{name}: all other days", b[~b.S])
    last = F.index[-1]
    print(
        f"now ({last.date()}): in the state {bool(F.S.iloc[-1])}; in full agreement up {int(F.up.iloc[-1])}, "
        f"down {int(F.dn.iloc[-1])}; SPY {100 * F.off.iloc[-1]:+.1f}% off its one-year high close"
    )
    if not list_long:
        return
    print("every spell of five or more sessions, read at the close of day five:")
    print(
        "  start | sessions | ends | SPY off high | levels lost | SPY next 5 / 20 / 40 | lowest close"
    )
    print("  within 20 | how it was entered | SPY over the five days | day five at a 20-day low")
    for p, n, end in spells:
        if n < 5:
            continue
        k = p + 4

        def f(h, k=k):
            return f"{100 * (av[k + h] / av[k] - 1):+5.1f}%" if k + h < len(av) else "  n/a"

        low = (
            f"{100 * (av[k + 1 : k + 21].min() / av[k] - 1):+5.1f}%"
            if k + 20 < len(av)
            else "  n/a"
        )
        if upv[p - 1] > 0 and dnv[p - 1] == 0:
            came = "from UP"
        elif dnv[p - 1] > 0 and upv[p - 1] == 0:
            came = "from DOWN"
        else:
            came = "mixed"
        at_low = av[k] <= av[k - 19 : k + 1].min() * 1.005
        print(
            f"  {F.index[p].date()}  {n:3d}  {end:5s} {100 * F.off.iloc[k]:+6.1f}%  "
            f"{int(F.lost.iloc[k]):2d}/{int(F.tot.iloc[k]):2d}  {f(5)} {f(20)} {f(40)}  low {low}  "
            f"{came:9s} {100 * (av[k] / av[p - 1] - 1):+5.1f}%  {at_low}"
        )


run("WITH the week: week, month, quarter, half-year, year", [0, 1, 2, 3, 4], list_long=True)
run("WITHOUT the week: month, quarter, half-year, year", [1, 2, 3, 4], list_long=False)
