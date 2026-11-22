"""A what-if on the near-miss entries: put the exit at a share of the way to the target and keep
only setups with a minimum distance to the target. One point on a curve, never a rule.

Run:  uv run python -m analysis.nearmiss.whatif --exit 0.40 --min-target 4

Same entries, stops and went-3 exits as run_htf.py; equal size, no leverage, no fees, fills at
the levels. A day that touched both the exit and the adverse level counts as the loss.
"""

from __future__ import annotations

import argparse

import pandas as pd

from analysis.nearmiss.run_htf import DATA, RESOLVED, TFS, build


def line(label: str, r: pd.DataFrame, tag: str) -> str:
    if len(r) == 0:
        return f"   {label:34s} no trades"
    won = r[f"out_{tag}"] == "won"
    pl = r[f"pl_{tag}"]
    return (
        f"   {label:34s} trades {len(r):6d}  wins {100 * won.mean():5.1f}%  average win "
        f"{pl[won].mean():+6.2f}%  average loss {pl[~won].mean():+6.2f}%  per trade "
        f"{pl.mean():+.3f}%  sum {pl.sum():+8.0f} points  median sessions held "
        f"{r[f'days_{tag}'].median():.0f}"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exit", type=float, default=0.40, help="share of the way to the target")
    ap.add_argument("--min-target", type=float, default=4.0, help="minimum distance, % of price")
    a = ap.parse_args()
    tag = f"{a.exit:.2f}"
    _, R = build(ks=(1.0, a.exit))
    R = R[R["out_1.00"].isin(RESOLVED)]
    R.to_csv(DATA / f"rows_whatif_{tag}.csv", index=False)
    print(
        f"WHAT-IF: out at {100 * a.exit:.0f}% of the way to the target; only setups with "
        f"{a.min_target:g}% or more of price between entry and target"
    )
    for tf, name in TFS:
        every = R[R.tf == tf]
        kept = every[every.dist_pct >= a.min_target]
        print(
            f"\n{name}: {len(kept)} of {len(every)} entries have {a.min_target:g}%+ to the target "
            f"({100 * len(kept) / len(every):.0f}%); medians for those: target "
            f"{kept.dist_pct.median():.1f}% away, stop {kept.risk_pct.median():.1f}% away"
        )
        print(line(f"kept, out at {100 * a.exit:.0f}% of the way", kept, tag))
        print(line("kept, held to the target", kept, "1.00"))
        print(line(f"  longs, out at {100 * a.exit:.0f}%", kept[kept.side > 0], tag))
        print(line("  longs, held to the target", kept[kept.side > 0], "1.00"))
        print(line(f"  shorts, out at {100 * a.exit:.0f}%", kept[kept.side < 0], tag))
        print(line("  shorts, held to the target", kept[kept.side < 0], "1.00"))
        print(line(f"every entry, out at {100 * a.exit:.0f}%", every, tag))
        print(line("every entry, held to the target", every, "1.00"))
        for fam in sorted(kept.family.unique()):
            print(line(f"  {fam}, out at {100 * a.exit:.0f}%", kept[kept.family == fam], tag))


if __name__ == "__main__":
    main()
