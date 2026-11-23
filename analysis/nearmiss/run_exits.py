"""Exit lab run: the four reversal families on one pattern timeframe, every exit mode on the SAME
entries (count only, exploratory).

Run after fetch.py:  uv run python -m analysis.nearmiss.run_exits            (month patterns)
                     uv run python -m analysis.nearmiss.run_exits --tf W     (week patterns)

Equal size, no leverage, no fees. Entries, targets, stops and the went-3 exit are run_htf.py's;
exits.py states each mode and its fill convention. A win here is a trade that made money, not a
trade that reached the target. Beta is each symbol's whole-history daily beta to SPY (hindsight).
"""

from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

from analysis.nearmiss.exits import MODES, Params, indicators, walk_exit
from analysis.nearmiss.htf import aggregate, candidates, enter
from analysis.nearmiss.run_htf import DATA

FAMILIES = ("2-2 reversal", "2-1-2 reversal", "3-1-2 reversal", "3-2-2 reversal")
NAMES = {
    "pattern": "pattern only (control)",
    "fraction": "40% of the way",
    "prior_day": "prior day's low / high",
    "giveback": "give-back trail (Guardian)",
    "chandelier": "Chandelier 3 x ATR(22)",
    "ema": "close through the 9 EMA",
    "rsi": "RSI(14) loses 50",
    "bollinger": "Bollinger band tag",
    "time": "time stop, 10 sessions",
}


def load(sym: str) -> pd.DataFrame | None:
    path = DATA / f"{sym.replace('/', '-')}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, index_col=0, parse_dates=True).round(4)
    return df[(df.High >= df.Low) & (df.Low > 0)]


def build(tf: str, p: Params = Params()) -> pd.DataFrame:
    uni = json.load(open(DATA / "universe.json"))
    kind = {s: "fund" for s in uni["funds"] + uni["index"]} | {s: "name" for s in uni["names"]}
    spy = load("SPY").Close.pct_change()
    rows = []
    for sym, group in kind.items():
        df = load(sym)
        if df is None:
            continue
        both = pd.concat(
            [df.Close.pct_change(), spy], axis=1, keys=["s", "m"], sort=True
        ).dropna()
        beta = both.s.cov(both.m) / both.m.var() if len(both) > 250 else np.nan
        o, h, l, c = (df[x].values for x in ("Open", "High", "Low", "Close"))
        ind = indicators(h, l, c, p)
        big_o, big_h, big_l, big_c, first, last = aggregate(df.index, o, h, l, c, tf)
        for cd in candidates(big_o, big_h, big_l, big_c):
            if cd.family not in FAMILIES:
                continue
            d0, d1 = int(first[cd.i]), int(last[cd.i])
            status, e, entry = enter(cd, o, h, l, c, d0, d1)
            if status != "triggered":
                continue
            row = dict(
                sym=sym,
                group=group,
                beta=beta,
                date=df.index[e],
                family=cd.family,
                side=cd.side,
                dist_pct=100 * abs(cd.target - entry) / entry,
                risk_pct=100 * abs(entry - cd.stop) / entry,
            )
            for mode in MODES:
                w = walk_exit(o, h, l, c, cd, e, entry, d1, mode, ind, p)
                row[f"out_{mode}"] = w.outcome
                row[f"days_{mode}"] = w.j - e
                row[f"pl_{mode}"] = 100 * cd.side * (w.fill - entry) / entry
            rows.append(row)
    return pd.DataFrame(rows)


def line(mode: str, r: pd.DataFrame) -> str:
    pl, out = r[f"pl_{mode}"], r[f"out_{mode}"]
    won = pl > 0
    share = out.value_counts(normalize=True)
    return (
        f"   {NAMES[mode]:28s} wins {100 * won.mean():5.1f}%  avg win {pl[won].mean():+6.2f}%  "
        f"avg loss {pl[~won].mean():+6.2f}%  per trade {pl.mean():+.3f}%  held "
        f"{r[f'days_{mode}'].median():3.0f}  | out by: target {100 * share.get('won', 0):4.1f}%  "
        f"rule {100 * share.get('rule', 0):4.1f}%  went 3 {100 * share.get('went3', 0):4.1f}%  "
        f"stop {100 * share.get('failed', 0):4.1f}%  tie {100 * share.get('both', 0):3.1f}%"
    )


def per_trade(label: str, r: pd.DataFrame) -> str:
    cells = "  ".join(f"{r[f'pl_{m}'].mean():+7.3f}" for m in MODES)
    return f"   {label:26s} {len(r):6d}  {cells}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tf", default="M", choices=["W", "M", "Q"])
    a = ap.parse_args()
    R = build(a.tf)
    R = R[R.out_pattern != "open"]  # an added exit only ends a trade sooner: all modes resolved
    R.to_csv(DATA / f"rows_exits_{a.tf}.csv", index=False)
    name = {"W": "WEEK", "M": "MONTH", "Q": "QUARTER"}[a.tf]
    print(f"EXIT LAB: {name} patterns walked on daily bars, four reversal families")
    print(
        f"{len(R)} entries, {R.sym.nunique()} symbols, {R.date.min():%Y-%m} to {R.date.max():%Y-%m}; "
        f"medians: target {R.dist_pct.median():.1f}% away, stop {R.risk_pct.median():.1f}% away"
    )

    print("\n1. EVERY ENTRY, EACH EXIT (same entries in every row; held = median sessions)")
    for mode in MODES:
        print(line(mode, R))

    print("\n2. WHAT EACH EXIT DID TO THE CONTROL'S WINNERS AND LOSERS (points per trade)")
    won = R.pl_pattern > 0
    for mode in MODES[1:]:
        d = R[f"pl_{mode}"] - R.pl_pattern
        cut = (d < 0) & won
        better = (d > 0) & ~won
        print(
            f"   {NAMES[mode]:28s} winners: {100 * cut.sum() / won.sum():4.1f}% made less, "
            f"{d[won].mean():+.2f} each on average | losers: {100 * better.sum() / (~won).sum():4.1f}% "
            f"lost less, {d[~won].mean():+.2f} each on average | net {d.mean():+.3f}"
        )

    head = "  ".join(f"{m[:7]:>7s}" for m in MODES)
    print(f"\n3. PER TRADE, % OF PRICE, BY CUT\n   {'cut':26s} trades  {head}")
    names = R[R.group == "name"]
    lo, hi = names.beta.quantile([1 / 3, 2 / 3])
    cuts = [
        ("all", R),
        ("longs", R[R.side > 0]),
        ("shorts", R[R.side < 0]),
        (f"names, beta under {lo:.2f}", names[names.beta < lo]),
        (f"names, beta {lo:.2f} to {hi:.2f}", names[(names.beta >= lo) & (names.beta <= hi)]),
        (f"names, beta over {hi:.2f}", names[names.beta > hi]),
        ("funds and indices", R[R.group == "fund"]),
        ("4%+ to the target", R[R.dist_pct >= 4]),
        ("under 4% to the target", R[R.dist_pct < 4]),
        ("since 2020", R[R.date >= "2020-01-01"]),
        ("before 2020", R[R.date < "2020-01-01"]),
    ] + [(fam, R[R.family == fam]) for fam in FAMILIES]
    for label, r in cuts:
        print(per_trade(label, r))

    print(f"\n4. WIN RATE BY BETA THIRD (single names)\n   {'cut':26s} trades  {head}")
    for label, r in cuts[3:6]:
        cells = "  ".join(f"{100 * (r[f'pl_{m}'] > 0).mean():6.1f}%" for m in MODES)
        print(f"   {label:26s} {len(r):6d}  {cells}")


if __name__ == "__main__":
    main()
