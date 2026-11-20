"""Shared helpers for the sector continuity look (see RECEIPT.md for the definitions).

A level is a period's opening price (week, month, quarter, half-year, year). Periods that
opened at the same price are ONE level. Full agreement up = the daily close is above every
distinct level; full agreement down = at or below every one.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

PERIODS = ["W", "M", "Q", "H", "Y"]


def load(path: str) -> pd.DataFrame:
    return pd.read_csv(path, index_col=0, parse_dates=True)


def open_matrix(df: pd.DataFrame) -> np.ndarray:
    """One column per period: that period's opening price on each day."""
    i = df.index
    iso = i.isocalendar()
    keys = {
        "W": iso["year"].astype(int).values * 100 + iso["week"].astype(int).values,
        "M": i.year * 100 + i.month,
        "Q": i.year * 10 + i.quarter,
        "H": i.year * 10 + ((i.month - 1) // 6),
        "Y": i.year,
    }
    return np.column_stack(
        [
            df.groupby(pd.Series(np.asarray(k), index=i))["Open"].transform("first").round(4).values
            for k in keys.values()
        ]
    )


def level_state(df: pd.DataFrame) -> pd.DataFrame:
    """L = distinct levels that day, A = how many of them the close is above."""
    opens = open_matrix(df)
    close = df["Close"].values
    n_levels = np.array([len(set(row)) for row in opens])
    n_above = np.array([len({x for x in row if c > x}) for row, c in zip(opens, close)])
    return pd.DataFrame({"L": n_levels, "A": n_above}, index=df.index)


def episodes(state: pd.DataFrame, side: str = "up") -> list[dict]:
    """Every crack out of full agreement on one side, with how far it went.

    lost_max counts distinct levels lost (side up) or regained (side down) at the worst point.
    outcome is 'healed' (back to the same full agreement), 'every level' (full agreement the
    other way) or 'open' (still unresolved at the end of the data).
    """
    n_levels, n_above = state["L"].values, state["A"].values
    full = (n_above == n_levels) if side == "up" else (n_above == 0)
    opposite = (n_above == 0) if side == "up" else (n_above == n_levels)
    out = []
    t = 1
    while t < len(n_above):
        if full[t - 1] and not full[t]:
            start, lost_max, end, outcome = t, 0, None, "open"
            u = t
            while u < len(n_above):
                lost = (n_levels[u] - n_above[u]) if side == "up" else n_above[u]
                lost_max = max(lost_max, lost)
                if full[u]:
                    outcome, end = "healed", u
                    break
                if opposite[u]:
                    outcome, end = "every level", u
                    break
                u += 1
            last = end if end is not None else len(n_above) - 1
            out.append(
                {
                    "start": start,
                    "end": last,
                    "lost_max": int(lost_max),
                    "outcome": outcome,
                    "levels_at_crack": int(n_levels[start]),
                }
            )
            t = last
        t += 1
    return out


def is_deep(ep: dict) -> bool:
    return ep["lost_max"] >= 3 or ep["outcome"] == "every level"
