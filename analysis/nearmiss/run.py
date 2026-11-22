"""Near-miss study: how close failed daily reversal patterns came to their target (count only).

Run after fetch.py:  uv run python -m analysis.nearmiss.run

Exploratory: no prereg, no audit. Definitions are in core.py and RECEIPT.md. Equal size, no
leverage, no fees, entry at the trigger level, exits at the target (or k of the way to it) and
at the stop level (the open when a bar gaps through the stop).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.nearmiss.core import find_setups, walk

HERE = Path(__file__).parent
DATA = HERE / "data"
KS = (1.0, 0.95, 0.90, 0.75, 0.50)
FAMILIES = ("2-2 reversal", "2-1-2 reversal", "3-1-2 reversal", "3-1-2 continuation")
BUCKETS = [(-9, 0.25), (0.25, 0.50), (0.50, 0.75), (0.75, 0.90), (0.90, 0.95), (0.95, 9)]
BUCKET_NAMES = ["under 25%", "25 to 50%", "50 to 75%", "75 to 90%", "90 to 95%", "95% or more"]


def load(sym: str):
    df = pd.read_csv(DATA / f"{sym}.csv", index_col=0, parse_dates=True).round(4)
    df = df[(df.High >= df.Low) & (df.Low > 0)]
    return df


def build() -> tuple[pd.DataFrame, pd.DataFrame]:
    uni = json.load(open(DATA / "universe.json"))
    kind = {s: "fund" for s in uni["funds"] + uni["index"]} | {s: "name" for s in uni["names"]}
    funnel, rows = [], []
    for sym, group in kind.items():
        path = DATA / f"{sym.replace('/', '-')}.csv"
        if not path.exists():
            continue
        df = load(sym.replace("/", "-"))
        o, h, l, c = (df[x].values for x in ("Open", "High", "Low", "Close"))
        for st in find_setups(o, h, l, c):
            funnel.append((st.family, st.side, st.status, st.went3))
            if st.status != "triggered":
                continue
            entry, dist, risk = st.trigger, abs(st.target - st.trigger), abs(st.trigger - st.stop)
            row = dict(
                sym=sym,
                group=group,
                date=df.index[st.i],
                family=st.family,
                side=st.side,
                entry=entry,
                dist_pct=100 * dist / entry,
                risk_pct=100 * risk / entry,
                went3=st.went3,
            )
            if st.went3:
                # the entry day's own reach toward the target; the order against the other
                # side's break is unknown on daily bars
                fav = h[st.i] if st.side > 0 else l[st.i]
                row["p_day"] = (fav - entry) / (st.target - entry)
                row["pl_other"] = 100 * st.side * (st.other - entry) / entry
            else:
                for k in KS:
                    w = walk(o, h, l, st, k)
                    tag = f"{k:.2f}"
                    row[f"out_{tag}"] = w.outcome
                    row[f"days_{tag}"] = w.j - st.i
                    # cautious: a bar that touched both counts as the stop; hopeful: as the target
                    row[f"pl_{tag}"] = 100 * st.side * (w.fill - entry) / entry
                    hopeful = entry + k * (st.target - entry) if w.outcome == "both" else w.fill
                    row[f"plx_{tag}"] = 100 * st.side * (hopeful - entry) / entry
                    if k == 1.0:
                        row["p_lo"], row["p_hi"] = w.p_lo, w.p_hi
            rows.append(row)
    F = pd.DataFrame(funnel, columns=["family", "side", "status", "went3"])
    return F, pd.DataFrame(rows)


def pct(n, d):
    return f"{100 * n / d:.0f}%" if d else "n/a"


def funnel_table(F: pd.DataFrame, R: pd.DataFrame) -> None:
    print("1. THE FUNNEL (both sides pooled; daily bars)")
    print(
        "   family | setups | no room to target | opened past trigger (missed) | opened through "
        "other side | not triggered | TRIGGERED | went 3 on the entry day | won | failed | "
        "one bar touched both | still open"
    )
    for fam in FAMILIES:
        f, r = F[F.family == fam], R[R.family == fam]
        v = f.status.value_counts()
        live = r[~r.went3]
        o = live["out_1.00"].value_counts()
        print(
            f"   {fam:18s} {len(f):6d} | {v.get('no room', 0):5d} | {v.get('gap past trigger', 0):5d}"
            f" | {v.get('opened through', 0):5d} | {v.get('not triggered', 0):6d} | {len(r):6d} | "
            f"{int(r.went3.sum()):5d} ({pct(r.went3.sum(), len(r))}) | {o.get('won', 0):5d} "
            f"({pct(o.get('won', 0), len(live))}) | {o.get('failed', 0):5d} "
            f"({pct(o.get('failed', 0), len(live))}) | {o.get('both', 0):4d} | {o.get('open', 0):3d}"
        )
    print(
        "   geometry of a triggered setup (medians): target distance % of price | stop distance %"
    )
    print("   | target distance in units of the stop distance | sessions to a win | to a failure")
    for fam in FAMILIES:
        r = R[(R.family == fam) & ~R.went3]
        won, failed = r[r["out_1.00"] == "won"], r[r["out_1.00"] == "failed"]
        print(
            f"   {fam:18s} target {r.dist_pct.median():4.2f}% | stop {r.risk_pct.median():4.2f}% | "
            f"{(r.dist_pct / r.risk_pct).median():4.2f} | {won['days_1.00'].median():.0f} | "
            f"{failed['days_1.00'].median():.0f}"
        )
    g = R[R.went3]
    touched = int((g.p_day >= 1).sum())
    print(
        f"   went 3 on the entry day: {len(g)} ({pct(len(g), len(R))} of triggered); the same bar "
        f"also touched the target on {touched} ({pct(touched, len(g))}), order unknown; "
        f"a loss at the setup bar's other side averages {g.pl_other.mean():+.2f}%"
    )


def full_book_table(R: pd.DataFrame) -> None:
    print("\n5. THE WHOLE BOOK: every triggered setup, the went-3 days put back")
    print("   cautious = every went-3 day is a loss at the setup bar's other side; hopeful = a")
    print("   went-3 day that reached the exit level counts as a win there (order unknown).")
    live = R[~R.went3 & R["out_1.00"].isin(["won", "failed", "both"])]
    g = R[R.went3]
    for fam in FAMILIES + ("all four",):
        a = live if fam == "all four" else live[live.family == fam]
        b = g if fam == "all four" else g[g.family == fam]
        n = len(a) + len(b)
        parts = []
        for k in (1.0, 0.95, 0.90, 0.50):
            tag = f"{k:.2f}"
            cautious = (a[f"pl_{tag}"].sum() + b.pl_other.sum()) / n
            win = b.p_day >= k
            hope = (
                a[f"plx_{tag}"].sum() + (k * b.dist_pct[win]).sum() + b.pl_other[~win].sum()
            ) / n
            parts.append(f"{100 * k:.0f}%: {cautious:+.3f}% to {hope:+.3f}%")
        print(f"   {fam:18s} {n:6d} trades   per trade, exit at " + "   ".join(parts))


def progress_table(R: pd.DataFrame, title: str) -> None:
    print(f"\n2. HOW CLOSE THE FAILED PATTERNS CAME ({title})")
    print("   share of failed patterns by the furthest point reached, as a share of the way from")
    print("   entry to target. 'certain' excludes the stop bar; 'possible' includes its extreme.")
    for fam in FAMILIES + ("all four",):
        r = R[~R.went3 & (R["out_1.00"] == "failed")]
        if fam != "all four":
            r = r[r.family == fam]
        if len(r) == 0:
            continue
        lo = [((r.p_lo >= a) & (r.p_lo < b)).mean() for a, b in BUCKETS]
        print(
            f"   {fam:18s} failed {len(r):6d}  median {100 * r.p_lo.median():3.0f}% of the way, "
            f"average {100 * r.p_lo.mean():3.0f}%  | "
            + "  ".join(f"{n} {100 * x:4.1f}%" for n, x in zip(BUCKET_NAMES, lo))
        )
        print(
            f"   {'':18s} reached 90%+: certain {100 * (r.p_lo >= 0.9).mean():4.1f}%, possible "
            f"{100 * (r.p_hi >= 0.9).mean():4.1f}%   reached 95%+: certain "
            f"{100 * (r.p_lo >= 0.95).mean():4.1f}%, possible {100 * (r.p_hi >= 0.95).mean():4.1f}%"
        )


def exit_table(R: pd.DataFrame, title: str) -> None:
    print(f"\n3. THE BOOK BY WHERE THE EXIT SITS ({title})")
    print("   same trades in every row: triggered, did not go 3 on the entry day, resolved at the")
    print("   full target or the stop. Per trade: win rate, average % of price, average in units")
    print("   of the stop distance (R). A bar touching both = the stop [in brackets: the target].")
    for fam in FAMILIES + ("all four",):
        r = R[~R.went3 & R["out_1.00"].isin(["won", "failed", "both"])]
        if fam != "all four":
            r = r[r.family == fam]
        if len(r) == 0:
            continue
        print(f"   {fam}  ({len(r)} trades)")
        for k in KS:
            tag = f"{k:.2f}"
            won = (r[f"out_{tag}"] == "won").mean()
            both = (r[f"out_{tag}"] == "both").mean()
            pl, plx = r[f"pl_{tag}"], r[f"plx_{tag}"]
            print(
                f"     exit at {100 * k:3.0f}% of the way: wins {100 * won:4.1f}% "
                f"[{100 * (won + both):4.1f}%]   {pl.mean():+.3f}% [{plx.mean():+.3f}%] per trade"
                f"   {(pl / r.risk_pct).mean():+.3f}R [{(plx / r.risk_pct).mean():+.3f}R]"
                f"   median sessions held {r[f'days_{tag}'].median():.0f}"
            )


def rescue_table(R: pd.DataFrame) -> None:
    print("\n4. WHAT AN EARLY EXIT RESCUES AND WHAT IT GIVES UP (all four families)")
    r = R[~R.went3 & R["out_1.00"].isin(["won", "failed", "both"])]
    lost = r[r["out_1.00"] != "won"]
    won = r[r["out_1.00"] == "won"]
    for k in (0.95, 0.90):
        tag = f"{k:.2f}"
        saved = lost[lost[f"out_{tag}"] == "won"]
        gain = (saved[f"pl_{tag}"] - saved["pl_1.00"]).sum()
        cost = (won["pl_1.00"] - won[f"pl_{tag}"]).sum()
        print(
            f"   exit at {100 * k:.0f}%: rescues {len(saved)} of {len(lost)} losers "
            f"({pct(len(saved), len(lost))}), worth {gain:+.0f} points of %; gives up "
            f"{cost:.0f} points across {len(won)} winners; net {gain - cost:+.0f} points over "
            f"{len(r)} trades ({(gain - cost) / len(r):+.3f}% per trade)"
        )


def main() -> None:
    F, R = build()
    flat = int((R.family == "3-1-2 flat").sum())
    R = R[R.family.isin(FAMILIES)].reset_index(drop=True)
    R.to_csv(DATA / "rows.csv", index=False)
    print(f"dropped: {flat} 3-1-2 setups whose 3 closed exactly at its open (no colour)")
    syms = R.sym.nunique()
    print(
        f"{syms} symbols, {R.date.min().date()} to {R.date.max().date()}, {len(R)} triggered "
        f"setups on {R.date.nunique()} distinct days\n"
    )
    funnel_table(F, R)
    progress_table(R, "all symbols, both sides")
    exit_table(R, "all symbols, both sides")
    rescue_table(R)
    full_book_table(R)
    f = R[~R.went3 & (R["out_1.00"] == "failed")]
    hist = np.histogram(f.p_lo.clip(0, 0.9999), bins=np.arange(0, 1.0001, 0.05))[0] / len(f)
    print("\n6. FAILED PATTERNS IN 5-POINT STEPS OF THE WAY TO THE TARGET (% of failures per step)")
    print("   " + "  ".join(f"{5 * i}-{5 * i + 5}: {100 * x:.1f}" for i, x in enumerate(hist)))
    for title, sub in (
        ("longs only", R[R.side > 0]),
        ("shorts only", R[R.side < 0]),
        ("the fourteen funds only", R[R.group == "fund"]),
        ("single names only", R[R.group == "name"]),
        ("since 2020", R[R.date >= "2020-01-01"]),
    ):
        print(f"\n===== SPLIT: {title} =====")
        r = sub[~sub.went3 & (sub["out_1.00"] == "failed")]
        res = sub[~sub.went3 & sub["out_1.00"].isin(["won", "failed", "both"])]
        line = "  ".join(
            f"{100 * k:.0f}%: {res[f'pl_{k:.2f}'].mean():+.3f}% ({(res[f'pl_{k:.2f}'] / res.risk_pct).mean():+.3f}R)"
            for k in KS
        )
        print(
            f"   trades {len(res)}, won at the full target {pct((res['out_1.00'] == 'won').sum(), len(res))}; "
            f"failed {len(r)}: median progress {100 * r.p_lo.median():.0f}%, reached 90%+ "
            f"{100 * (r.p_lo >= 0.9).mean():.1f}%, 95%+ {100 * (r.p_lo >= 0.95).mean():.1f}%"
        )
        print(f"   book per trade by exit: {line}")


if __name__ == "__main__":
    main()
