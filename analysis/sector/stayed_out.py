"""Is "the theme fund has STAYED out of full agreement" the tell? Counted directly.

themes.py showed that looking back from deep sector cracks the theme fund was usually already
out, while the day the theme first cracks carried no lift. The split by how long the theme had
been out was only implied there. This counts it.

Themes fixed before looking (owner, 2026-11-19): SMH and IGV inside XLK, KRE inside XLF, ITB
inside XLY. Sector cracks are out of full agreement up with three or more distinct levels.
Description only: no trades, no rule.

Run:  uv run --no-project --with pandas --with numpy \
          python analysis/sector/stayed_out.py analysis/sector
      (needs inside.py to have been run first for the count of large names)
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from common import episodes, is_deep, level_state, load

PAIRS = [
    ("SMH", "XLK", "Semiconductors in technology"),
    ("IGV", "XLK", "Software in technology"),
    ("KRE", "XLF", "Regional banks in financials"),
    ("ITB", "XLY", "Homebuilders in discretionary"),
]
RUN_BANDS = (
    (0, 0, "in agreement"),
    (1, 1, "cracked today"),
    (2, 5, "out 2-5 days"),
    (6, 20, "out 6-20 days"),
    (21, 10**6, "out 21+ days"),
)
HORIZON = 10


def out_run(full: np.ndarray) -> np.ndarray:
    """Consecutive days out of full agreement, counted up to and including each day."""
    run = np.zeros(len(full), int)
    for t in range(len(full)):
        run[t] = 0 if full[t] else (run[t - 1] + 1 if t else 1)
    return run


def main(root: str) -> None:
    try:
        inside = load_inside(root)
    except FileNotFoundError:
        inside = None
    crack_rows = []
    for theme, parent, label in PAIRS:
        t_df, p_df = load(f"{root}/data/{theme}.csv"), load(f"{root}/data/{parent}.csv")
        idx = t_df.index.intersection(p_df.index)
        s_t, s_p = level_state(t_df).loc[idx], level_state(p_df).loc[idx]
        parent_full = (s_p.A == s_p.L).values
        run = out_run((s_t.A == s_t.L).values)
        eps = [
            e for e in episodes(s_p, "up") if e["outcome"] != "open" and e["levels_at_crack"] >= 3
        ]
        n = len(idx)
        deep_start, any_start = np.zeros(n, bool), np.zeros(n, bool)
        for e in eps:
            any_start[e["start"]] = True
            deep_start[e["start"]] = is_deep(e)

        print(f"\n=== {label}: {theme} / {parent}, {idx[0].date()} to {idx[-1].date()} ===")
        print("  A. On days the SECTOR is in full agreement up, by the state of the theme fund:")
        print(
            "     theme state        days  separate spells | sector crack within 10 days | DEEP sector crack within 10 days"
        )
        days = [t for t in range(1, n - HORIZON) if parent_full[t]]
        for lo, hi, name in RUN_BANDS:
            sel = [t for t in days if lo <= run[t] <= hi]
            if not sel:
                continue
            spells = sum(1 for k, t in enumerate(sel) if k == 0 or t != sel[k - 1] + 1)
            p_any = np.mean([any_start[t + 1 : t + 1 + HORIZON].any() for t in sel])
            p_deep = np.mean([deep_start[t + 1 : t + 1 + HORIZON].any() for t in sel])
            print(
                f"     {name:16s} {len(sel):6d} {spells:8d}         | {100 * p_any:5.0f}%                       | {100 * p_deep:5.0f}%"
            )
        print(
            "  B. When the sector DOES crack, by how long the theme had already been out the day before:"
        )
        print("     theme state        cracks | heals after one level | goes deep")
        for lo, hi, name in (
            (0, 0, "in agreement"),
            (1, 1, "cracked 1 day ago"),
            (2, 5, "out 2-5 days"),
            (6, 10**6, "out 6+ days"),
        ):
            sel = [e for e in eps if lo <= run[e["start"] - 1] <= hi]
            if not sel:
                continue
            one = np.mean([e["lost_max"] == 1 for e in sel])
            deep = np.mean([is_deep(e) for e in sel])
            print(
                f"     {name:17s} {len(sel):5d}  | {100 * one:5.0f}%                 | {100 * deep:5.0f}%"
            )
        for e in eps:
            crack_rows.append(
                {
                    "parent": parent,
                    "theme": theme,
                    "date": idx[e["start"]],
                    "theme_out_days": int(run[e["start"] - 1]),
                    "deep": int(is_deep(e)),
                    "one_level": int(e["lost_max"] == 1),
                }
            )
    cracks = pd.DataFrame(crack_rows)
    cracks.to_csv(f"{root}/stayed_out.csv", index=False)

    tech = cracks[cracks.parent == "XLK"].pivot_table(
        index="date", columns="theme", values="theme_out_days"
    )
    tech = tech.dropna().join(
        cracks[cracks.theme == "SMH"].set_index("date")[["deep", "one_level"]]
    )
    tech["themes_out"] = (tech["SMH"] >= 2).astype(int) + (tech["IGV"] >= 2).astype(int)
    print("\n=== Technology cracks by how many of its two themes had been out two or more days ===")
    for k, g in tech.groupby("themes_out"):
        print(
            f"     {k} of 2 themes out: cracks {len(g):4d} | heals after one level {100 * g.one_level.mean():3.0f}% | goes deep {100 * g.deep.mean():3.0f}%"
        )

    if inside is not None:
        m = cracks.merge(inside, left_on=["parent", "date"], right_on=["sym", "start"], how="inner")
        m["theme_stayed_out"] = m.theme_out_days >= 2
        m["many_names_out"] = m.n_out >= 5
        print("\n=== Do the two reads stack? Cracks since 2010, the four pairs pooled ===")
        print(
            "     theme stayed out 2+ days | 5+ of the ten largest names out | cracks | goes deep"
        )
        for (a, b), g in m.groupby(["theme_stayed_out", "many_names_out"]):
            print(
                f"     {'yes' if a else 'no ':3s}                      | {'yes' if b else 'no ':3s}                             | {len(g):5d}  | {100 * g.deep.mean():3.0f}%"
            )

    try:
        cushion = pd.read_csv(f"{root}/cushion.csv", parse_dates=["date"])
    except FileNotFoundError:
        return
    cushion = cushion[cushion.side == "up"][["sym", "date", "d3"]]
    k = cracks.merge(cushion, left_on=["parent", "date"], right_on=["sym", "date"], how="inner")
    k["band"] = pd.qcut(k["d3"], 3, labels=["thin", "middle", "thick"])
    k["stayed"] = k.theme_out_days >= 6
    print("\n=== Kill test: is the theme read just the sector's own cushion? Cracks since 2010 ===")
    print("     cushion to the third level | theme in or out under 6 days | theme out 6+ days")
    for band, g in k.groupby("band", observed=True):
        no, yes = g[~g.stayed], g[g.stayed]
        print(
            f"     {band:6s}                      | deep {100 * no.deep.mean():3.0f}% (n={len(no)})"
            f"            | deep {100 * yes.deep.mean():3.0f}% (n={len(yes)})"
        )
    print(
        f"     theme out 6+ days goes with a thinner cushion: median third-level cushion "
        f"{k[k.stayed].d3.median():.1f} daily swings against {k[~k.stayed].d3.median():.1f}"
    )


def load_inside(root: str) -> pd.DataFrame:
    d = pd.read_csv(f"{root}/inside.csv", parse_dates=["start"])
    return d[d.side == "up"][["sym", "start", "n_out"]]


if __name__ == "__main__":
    main(sys.argv[1])
