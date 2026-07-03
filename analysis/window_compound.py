"""Window-compounded returns from tv_dump.mjs trade dumps.

Method (validated in TVB-4 preflight 2): under 100%-of-equity sizing, the correct
aggregate over a subset of trades is product(1 + pp) - 1 over CLOSED trades ENTERED
inside the window. Per-trade pp is size-invariant, so this permits window-sliced
comparisons (venue A vs venue B over a shared window) from full-window runs without
re-running the backtest.

Usage:
    uv run python analysis/window_compound.py <dump.json> [--start ISO] [--end ISO]

Prints overall and per-direction (le/se) compounded returns plus trade counts for
the selected window. Timestamps in dumps are epoch MILLISECONDS (entry time e.tm).
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone


def compound_window(
    trades: list[dict], start_ms: int | None = None, end_ms: int | None = None
) -> dict:
    """Compound product(1+pp)-1 over closed trades entered in [start_ms, end_ms).

    trades: dump list entries {et, dir, pp, open}. Entries with open=True or
    missing pp/et are excluded (mark-to-market rows carry no realized pp basis).
    """
    out = {"n": 0, "le": 0, "se": 0, "ret": 1.0, "ret_le": 1.0, "ret_se": 1.0}
    for t in trades:
        if t.get("open"):
            continue
        et, pp, d = t.get("et"), t.get("pp"), t.get("dir")
        if et is None or pp is None:
            continue
        if start_ms is not None and et < start_ms:
            continue
        if end_ms is not None and et >= end_ms:
            continue
        out["n"] += 1
        out["ret"] *= 1.0 + pp
        if d == "le":
            out["le"] += 1
            out["ret_le"] *= 1.0 + pp
        elif d == "se":
            out["se"] += 1
            out["ret_se"] *= 1.0 + pp
    for k in ("ret", "ret_le", "ret_se"):
        out[k] -= 1.0
    return out


def _iso_to_ms(s: str) -> int:
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dump")
    ap.add_argument("--start", help="ISO UTC window start (entry-time filter)")
    ap.add_argument("--end", help="ISO UTC window end (exclusive)")
    args = ap.parse_args()

    with open(args.dump, encoding="utf-8") as f:
        d = json.load(f)
    start_ms = _iso_to_ms(args.start) if args.start else None
    end_ms = _iso_to_ms(args.end) if args.end else None
    r = compound_window(d.get("list", []), start_ms, end_ms)
    print(f"{args.dump}: window [{args.start or '-inf'}, {args.end or '+inf'})")
    print(
        f"  n={r['n']} (L{r['le']}/S{r['se']})  compounded={r['ret'] * 100:+.2f}%"
        f"  long={r['ret_le'] * 100:+.2f}%  short={r['ret_se'] * 100:+.2f}%"
    )


if __name__ == "__main__":
    main()
