"""Kill test: does the count of large names already cracked say anything the sector fund's own
cushion does not? Description only: no trades, no rule.

A sector fund is the weighted sum of its members. If most large names are already below their
opens, the fund already sits close to its own, so "many names out -> the crack goes deep" could
be arithmetic. The cushion is measured the day BEFORE the crack, in units of the fund's own
daily swing (20-day standard deviation of daily returns):

  d1 = distance from the close down to the NEAREST level
  d3 = distance down to the THIRD level (the line a crack must reach to count as deep);
       the lowest level if fewer than three are distinct that day

Test: within cushion bands, does the count still separate shallow from deep? And does adding
the count to a cushion-only model improve its ranking of cracks it has not seen (fit on cracks
up to 2018, scored on cracks after)?

Run:  uv run --no-project --with pandas --with numpy --with scikit-learn \
          python analysis/sector/cushion.py analysis/sector
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
from common import episodes, is_deep, level_state, load, open_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

SPLIT = "2019-01-01"
BUCKETS = ((0, 2), (3, 4), (5, 6), (7, 10))


def build(root: str) -> pd.DataFrame:
    holdings = json.load(open(f"{root}/holdings.json"))
    rows = []
    for sym, hold in holdings.items():
        etf = load(f"{root}/data/{sym}.csv")
        etf = etf[etf.index >= "2009-06-01"]
        state = level_state(etf)
        opens = open_matrix(etf)
        close = etf["Close"].values
        vol = etf["Close"].pct_change().rolling(20).std().values
        members = {}
        for ticker, _ in hold:
            m = load(f"{root}/members/{ticker.replace('/', '-')}.csv")
            members[ticker] = level_state(m)
        idx = etf.index
        for side in ("up", "down"):
            for ep in episodes(state, side):
                s0 = ep["start"]
                prev = s0 - 1
                if ep["outcome"] == "open" or ep["levels_at_crack"] < 3:
                    continue
                if idx[s0] < pd.Timestamp("2010-01-01") or not np.isfinite(vol[prev]):
                    continue
                levels = sorted(set(opens[prev]), reverse=(side == "up"))
                third = levels[min(2, len(levels) - 1)]
                sign = 1.0 if side == "up" else -1.0
                d1 = sign * (close[prev] - levels[0]) / close[prev] / vol[prev]
                d3 = sign * (close[prev] - third) / close[prev] / vol[prev]
                have = out = 0
                for st in members.values():
                    if idx[prev] not in st.index:
                        continue
                    r = st.loc[idx[prev]]
                    have += 1
                    member_full = (r.A == r.L) if side == "up" else (r.A == 0)
                    out += int(not member_full)
                if have < 6:
                    continue
                rows.append(
                    {
                        "sym": sym,
                        "side": side,
                        "date": idx[s0],
                        "d1": d1,
                        "d3": d3,
                        "n_out": out,
                        "levels": len(levels),
                        "deep": int(is_deep(ep)),
                        "one_level": int(ep["lost_max"] == 1),
                    }
                )
    return pd.DataFrame(rows)


def auc_pair(train: pd.DataFrame, test: pd.DataFrame, cols: list[str]) -> float:
    mu, sd = train[cols].mean(), train[cols].std()
    model = LogisticRegression(max_iter=1000).fit((train[cols] - mu) / sd, train["deep"])
    return float(roc_auc_score(test["deep"], model.predict_proba((test[cols] - mu) / sd)[:, 1]))


def report(d: pd.DataFrame, label: str) -> None:
    print(
        f"\n=== {label}: {len(d)} cracks on {d.date.nunique()} dates, deep {100 * d.deep.mean():.0f}% ==="
    )
    for col, name in (("d1", "nearest level"), ("d3", "third level")):
        bands = pd.qcut(d[col], 3, labels=["thin", "middle", "thick"])
        parts = [
            f"{b} {100 * g.deep.mean():.0f}% (n={len(g)}, median {g[col].median():.1f} daily swings)"
            for b, g in d.groupby(bands, observed=True)
        ]
        print(f"  deep rate by cushion to the {name}: " + " | ".join(parts))
    print("  deep rate by count of large names already out, INSIDE each third-level cushion band:")
    bands = pd.qcut(d["d3"], 3, labels=["thin", "middle", "thick"])
    for band, g in d.groupby(bands, observed=True):
        cells = []
        for lo, hi in BUCKETS:
            x = g[(g.n_out >= lo) & (g.n_out <= hi)]
            cells.append(
                f"{lo}-{hi}: {100 * x.deep.mean():3.0f}% (n={len(x)})"
                if len(x) >= 15
                else f"{lo}-{hi}: thin (n={len(x)})"
            )
        print(f"    {band:6s} cushion  " + " | ".join(cells))
    print(
        f"  count and cushion move together: correlation of count with d1 {d.n_out.corr(d.d1):+.2f}, with d3 {d.n_out.corr(d.d3):+.2f}"
    )

    base = ["d1", "d3", "levels"]
    z = (d[base + ["n_out"]] - d[base + ["n_out"]].mean()) / d[base + ["n_out"]].std()
    model = LogisticRegression(max_iter=1000).fit(z, d["deep"])
    coef = dict(zip(base + ["n_out"], model.coef_[0]))
    rng = np.random.default_rng(7)
    dates = d.date.unique()
    boots = []
    for _ in range(400):
        pick = rng.choice(dates, size=len(dates), replace=True)
        b = pd.concat([d[d.date == p] for p in pick])
        if b.deep.nunique() < 2:
            continue
        zb = (b[base + ["n_out"]] - b[base + ["n_out"]].mean()) / b[base + ["n_out"]].std()
        boots.append(LogisticRegression(max_iter=1000).fit(zb, b["deep"]).coef_[0][-1])
    lo, hi = np.percentile(boots, [5, 95])
    print(
        "  all cracks, one model (each input in its own standard units; minus = protects, plus = "
        f"raises deep odds): nearest {coef['d1']:+.2f}, third {coef['d3']:+.2f}, "
        f"levels {coef['levels']:+.2f}, COUNT {coef['n_out']:+.2f} "
        f"[90% range resampling whole dates: {lo:+.2f} to {hi:+.2f}]"
    )
    train, test = d[d.date < SPLIT], d[d.date >= SPLIT]
    if train.deep.nunique() == 2 and test.deep.nunique() == 2:
        a0 = auc_pair(train, test, base)
        a1 = auc_pair(train, test, base + ["n_out"])
        a2 = auc_pair(train, test, ["n_out"])
        print(
            f"  ranking cracks after {SPLIT[:4]} with a model fit before it (0.50 = coin flip): "
            f"cushion only {a0:.3f} | cushion + count {a1:.3f} | count only {a2:.3f} "
            f"(train {len(train)}, test {len(test)})"
        )


def main(root: str) -> None:
    d = build(root)
    d.to_csv(f"{root}/cushion.csv", index=False)
    report(d[d.side == "up"], "SECTOR LEAVES FULL AGREEMENT UP")
    report(d[d.side == "down"], "SECTOR LEAVES FULL AGREEMENT DOWN")


if __name__ == "__main__":
    main(sys.argv[1])
