"""Near-miss study on the day, week, month and quarter: patterns on each timeframe's own bars,
walked on daily bars (count only, exploratory).

Run after fetch.py:  uv run python -m analysis.nearmiss.run_htf

Equal size, no leverage, no fees. Entry at the trigger (the open on a mid-bar gap), exits at the
target (or k of the way to it), at the setup bar's other side while the entry bar is still open
(went 3), and at the stop (the open when a day gaps through the level).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.nearmiss.htf import aggregate, candidates, enter, walk_sub

HERE = Path(__file__).parent
DATA = HERE / "data"
TFS = (("D", "DAY"), ("W", "WEEK"), ("M", "MONTH"), ("Q", "QUARTER"))
KS = (1.0, 0.95, 0.90, 0.75, 0.50)
FAMILIES = (
    "2-2 reversal",
    "2-1-2 reversal",
    "3-1-2 reversal",
    "3-1-2 continuation",
    "3-2-2 reversal",
)
RESOLVED = ["won", "went3", "failed", "both"]
STEPS = [(-9, 0.25), (0.25, 0.50), (0.50, 0.75), (0.75, 0.90), (0.90, 0.95), (0.95, 9)]
STEP_NAMES = ["under 25%", "25-50%", "50-75%", "75-90%", "90-95%", "95%+"]


def build() -> tuple[pd.DataFrame, pd.DataFrame]:
    uni = json.load(open(DATA / "universe.json"))
    kind = {s: "fund" for s in uni["funds"] + uni["index"]} | {s: "name" for s in uni["names"]}
    funnel, rows = [], []
    for sym, group in kind.items():
        path = DATA / f"{sym.replace('/', '-')}.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path, index_col=0, parse_dates=True).round(4)
        df = df[(df.High >= df.Low) & (df.Low > 0)]
        o, h, l, c = (df[x].values for x in ("Open", "High", "Low", "Close"))
        for tf, _ in TFS:
            big_o, big_h, big_l, big_c, first, last = aggregate(df.index, o, h, l, c, tf)
            for cd in candidates(big_o, big_h, big_l, big_c):
                if cd.family not in FAMILIES:
                    continue
                d0, d1 = int(first[cd.i]), int(last[cd.i])
                status, e, entry = enter(cd, o, h, l, c, d0, d1)
                funnel.append((tf, cd.family, status))
                if status != "triggered":
                    continue
                row = dict(
                    tf=tf,
                    sym=sym,
                    group=group,
                    date=df.index[e],
                    family=cd.family,
                    side=cd.side,
                    dist_pct=100 * abs(cd.target - entry) / entry,
                    risk_pct=100 * abs(entry - cd.stop) / entry,
                )
                for k in KS:
                    w = walk_sub(o, h, l, c, cd, e, entry, d1, k)
                    tag = f"{k:.2f}"
                    row[f"out_{tag}"] = w.outcome
                    row[f"days_{tag}"] = w.j - e
                    row[f"pl_{tag}"] = 100 * cd.side * (w.fill - entry) / entry
                    hopeful = entry + k * (cd.target - entry) if w.outcome == "both" else w.fill
                    row[f"plx_{tag}"] = 100 * cd.side * (hopeful - entry) / entry
                    if k == 1.0:
                        row["p_lo"], row["p_hi"] = w.p_lo, w.p_hi
                rows.append(row)
    return pd.DataFrame(funnel, columns=["tf", "family", "status"]), pd.DataFrame(rows)


def pct(n, d):
    return f"{100 * n / d:.0f}%" if d else "n/a"


def report(tf: str, name: str, F: pd.DataFrame, R: pd.DataFrame) -> None:
    F, R = F[F.tf == tf], R[R.tf == tf]
    res = R[R["out_1.00"].isin(RESOLVED)]
    print(f"\n{'=' * 100}\n{name}: patterns on {name.lower()} bars, walked on daily bars")
    print(f"{len(R)} entries on {R.date.nunique()} distinct days, {res.sym.nunique()} symbols")

    print("\n1. THE FUNNEL")
    print(
        "   family | setups | missed (bar opened past trigger) | other side broke first | one day "
        "broke both (unknown) | ENTRIES | won | went 3 after entry | stopped | one day both | open"
    )
    for fam in FAMILIES:
        f, r = F[F.family == fam], R[R.family == fam]
        v, o = f.status.value_counts(), r["out_1.00"].value_counts()
        n = len(r)
        print(
            f"   {fam:18s} {len(f):6d} | {v.get('gap past trigger', 0):5d} | "
            f"{v.get('other side first', 0):5d} | {v.get('same day both', 0):5d} | {n:6d} | "
            f"{pct(o.get('won', 0), n):>4s} | {pct(o.get('went3', 0), n):>4s} | "
            f"{pct(o.get('failed', 0), n):>4s} | {o.get('both', 0):4d} | {o.get('open', 0):3d}"
        )
    print("   medians: target distance % of price | stop distance % | target in units of stop |")
    print("   sessions to a win | sessions to a loss")
    for fam in FAMILIES:
        r = res[res.family == fam]
        if len(r) < 20:
            continue
        won, lost = r[r["out_1.00"] == "won"], r[r["out_1.00"] != "won"]
        print(
            f"   {fam:18s} target {r.dist_pct.median():5.2f}% | stop {r.risk_pct.median():5.2f}% | "
            f"{(r.dist_pct / r.risk_pct).median():4.2f} | {won['days_1.00'].median():3.0f} | "
            f"{lost['days_1.00'].median():3.0f}"
        )

    print("\n2. HOW CLOSE THE ONES THAT DID NOT REACH THE TARGET CAME (share of the way, certain)")
    groups = (
        ("stopped (the owner's failed)", res[res["out_1.00"] == "failed"]),
        ("went 3 after entry", res[res["out_1.00"] == "went3"]),
        ("both kinds", res[res["out_1.00"].isin(["failed", "went3"])]),
    )
    for label, r in groups:
        if len(r) < 20:
            continue
        shares = [((r.p_lo >= a) & (r.p_lo < b)).mean() for a, b in STEPS]
        print(
            f"   {label:28s} n {len(r):6d}  median {100 * r.p_lo.median():3.0f}%  average "
            f"{100 * r.p_lo.mean():3.0f}%  | "
            + "  ".join(f"{s} {100 * x:4.1f}%" for s, x in zip(STEP_NAMES, shares))
            + f"  | 90%+ possible {100 * (r.p_hi >= 0.9).mean():4.1f}%"
        )
    for fam in FAMILIES:
        r = res[(res.family == fam) & res["out_1.00"].isin(["failed", "went3"])]
        if len(r) < 20:
            continue
        print(
            f"     {fam:18s} n {len(r):6d}  median {100 * r.p_lo.median():3.0f}%  reached 90%+ "
            f"{100 * (r.p_lo >= 0.9).mean():4.1f}%  95%+ {100 * (r.p_lo >= 0.95).mean():4.1f}%"
        )
    r = res[res["out_1.00"].isin(["failed", "went3"])]
    hist = np.histogram(r.p_lo.clip(0, 0.9999), bins=np.arange(0, 1.0001, 0.1))[0] / len(r)
    print(
        "   in 10-point steps (% of all that did not reach the target): "
        + "  ".join(f"{10 * i}-{10 * i + 10}: {100 * x:.1f}" for i, x in enumerate(hist))
    )

    print("\n3. THE BOOK BY WHERE THE EXIT SITS (every entry that resolved; a day touching both")
    print("   the exit and the adverse level counts as the loss [in brackets: as the win])")
    for fam in FAMILIES + ("all five",):
        r = res if fam == "all five" else res[res.family == fam]
        if len(r) < 20:
            continue
        parts = []
        for k in KS:
            tag = f"{k:.2f}"
            won = (r[f"out_{tag}"] == "won").mean()
            parts.append(
                f"{100 * k:3.0f}%: wins {100 * won:4.1f}%  {r[f'pl_{tag}'].mean():+.3f}% "
                f"[{r[f'plx_{tag}'].mean():+.3f}%]  {(r[f'pl_{tag}'] / r.risk_pct).mean():+.3f}R"
            )
        print(f"   {fam} ({len(r)} trades)\n     " + "\n     ".join(parts))

    print("\n4. WHAT AN EARLY EXIT RESCUES AND GIVES UP (all five families)")
    lost, won = res[res["out_1.00"] != "won"], res[res["out_1.00"] == "won"]
    for k in (0.95, 0.90):
        tag = f"{k:.2f}"
        saved = lost[lost[f"out_{tag}"] == "won"]
        gain = (saved[f"pl_{tag}"] - saved["pl_1.00"]).sum()
        cost = (won["pl_1.00"] - won[f"pl_{tag}"]).sum()
        print(
            f"   exit at {100 * k:.0f}%: rescues {len(saved)} of {len(lost)} losers "
            f"({100 * len(saved) / len(lost):.1f}%), +{gain:.0f} points; gives up {cost:.0f} "
            f"points on {len(won)} winners; net {(gain - cost) / len(res):+.3f}% per trade"
        )

    print("\n5. SPLITS (all five families; per trade at the full target, then at 90% of the way)")
    cuts = (
        ("longs", res[res.side > 0]),
        ("shorts", res[res.side < 0]),
        ("funds", res[res.group == "fund"]),
        ("single names", res[res.group == "name"]),
        ("since 2020", res[res.date >= "2020-01-01"]),
    )
    for label, r in cuts:
        miss = r[r["out_1.00"].isin(["failed", "went3"])]
        print(
            f"   {label:13s} trades {len(r):6d}  won {pct((r['out_1.00'] == 'won').sum(), len(r))}  "
            f"{r['pl_1.00'].mean():+.3f}% -> {r['pl_0.90'].mean():+.3f}%   missed: median "
            f"{100 * miss.p_lo.median():.0f}% of the way, reached 90%+ {100 * (miss.p_lo >= 0.9).mean():.1f}%"
        )


def main() -> None:
    F, R = build()
    R.to_csv(DATA / "rows_htf.csv", index=False)
    for tf, name in TFS:
        report(tf, name, F, R)


if __name__ == "__main__":
    main()
