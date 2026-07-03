"""TVB-6 xyz backfill verification: TV HIP3XYZ:MSTRUSDC.P bars vs HL xyz:MSTR candles.

Method: bar-by-bar OHLCV comparison on timestamp intersection at 15m/60m/1D, plus
two closure checks for the HL API's recent-5000-candle cap (15m floor 2026-05-12,
1h floor 2025-12-07): (a) TV 60m aggregated to 4h vs HL's uncapped 4h candles over
the pre-Dec-7 hole; (b) TV 15m aggregated to 60m vs TV's own (HL-verified) 60m
series over the full window, which pins the pre-May-12 15m subdivision to the same
data stream.

Evidence files (analysis/reference/tvb6_*.json) are TIME-PERISHABLE: the HL candle
endpoint serves only the most-recent ~5000 candles per interval, so the raw pulls
committed 2026-07-03 cannot be re-fetched later. Re-running this script against the
committed files reproduces the verdict tables in the datasheet (TVB-6 section).

Usage:
    uv run python analysis/verify_xyz_backfill.py [--dir analysis/reference] [--prefix tvb6_]

TV bar rows are [epochSec, o, h, l, c, v] (scripts/tv_bars.mjs); HL candles are
{t: ms, o/h/l/c/v: str, n: int} (POST /info candleSnapshot).
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

HOUR_MS = 3_600_000
H4_MS = 4 * HOUR_MS


def load_tv_bars(path: str | Path) -> dict[int, list[float]]:
    """tv_bars.mjs export -> {epoch_ms: [o, h, l, c, v]}."""
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    out = {}
    for b in d["bars"]:
        row = [float(x) for x in b[1:6]]
        while len(row) < 5:
            row.append(0.0)
        out[int(b[0]) * 1000] = row
    return out


def load_hl_candles(path: str | Path) -> dict[int, list[float]]:
    """HL candleSnapshot JSON -> {epoch_ms: [o, h, l, c, v, n]}."""
    with open(path, encoding="utf-8") as f:
        candles = json.load(f)
    return {
        int(c["t"]): [
            float(c["o"]),
            float(c["h"]),
            float(c["l"]),
            float(c["c"]),
            float(c["v"]),
            float(c["n"]),
        ]
        for c in candles
    }


def aggregate(bars: dict[int, list[float]], step_ms: int) -> dict[int, list[float]]:
    """Aggregate {ms: [o,h,l,c,v]} into UTC-aligned buckets of step_ms.

    Iterates in timestamp order so bucket open/close are the first/last
    sub-bar regardless of input dict order.
    """
    out: dict[int, list[float]] = {}
    for ts in sorted(bars):
        o, h, l, c, v = bars[ts][:5]
        bucket = ts - (ts % step_ms)
        cur = out.get(bucket)
        if cur is None:
            out[bucket] = [o, h, l, c, v]
        else:
            cur[1] = max(cur[1], h)
            cur[2] = min(cur[2], l)
            cur[3] = c
            cur[4] += v
    return out


def rel_err(a: float, b: float) -> float:
    return abs(a - b) / max(abs(a), abs(b), 1e-12)


def diff_stats(
    tv: dict[int, list[float]], hl: dict[int, list[float]], vol_tol: float = 1e-6
) -> dict:
    """Per-field exact/rel-err stats over the timestamp intersection.

    Returns overlap/only counts, per-field exact counts + max rel err, the
    all-4-exact count, volume matches within vol_tol (relative), the worst
    bars by max field rel-err, and the HL-only split into zero-trade
    placeholders vs bars with trades (n > 0).
    """
    both = sorted(set(tv) & set(hl))
    hl_only = sorted(set(hl) - set(tv))
    fields = ["open", "high", "low", "close"]
    per_field = {f: {"exact": 0, "max_rel": 0.0} for f in fields}
    all4 = 0
    vol_ok = 0
    worst: list[tuple[float, int]] = []
    for t in both:
        a, b = tv[t], hl[t]
        bar_max = 0.0
        exact = True
        for i, f in enumerate(fields):
            if a[i] == b[i]:
                per_field[f]["exact"] += 1
            else:
                exact = False
            e = rel_err(a[i], b[i])
            per_field[f]["max_rel"] = max(per_field[f]["max_rel"], e)
            bar_max = max(bar_max, e)
        all4 += exact
        if abs(a[4] - b[4]) <= vol_tol * max(abs(b[4]), 1.0):
            vol_ok += 1
        worst.append((bar_max, t))
    worst.sort(reverse=True)
    placeholders = sum(1 for t in hl_only if len(hl[t]) > 5 and hl[t][5] == 0)
    return {
        "overlap": len(both),
        "tv_only": len(tv) - len(both),
        "hl_only": len(hl_only),
        "hl_only_placeholders": placeholders,
        "hl_only_traded": [t for t in hl_only if len(hl[t]) > 5 and hl[t][5] > 0],
        "per_field": per_field,
        "all4_exact": all4,
        "vol_match": vol_ok,
        "worst": worst[:6],
    }


def _iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def _print_report(label: str, s: dict) -> None:
    n = s["overlap"]
    print(f"\n=== {label} ===")
    print(
        f"overlap {n} | tv_only {s['tv_only']} | hl_only {s['hl_only']} "
        f"({s['hl_only_placeholders']} zero-trade placeholders, "
        f"{len(s['hl_only_traded'])} with trades)"
    )
    for t in s["hl_only_traded"][:5]:
        print(f"  HL-only traded bar: {_iso(t)}Z")
    if n == 0:
        return
    for f, st in s["per_field"].items():
        print(
            f"  {f:5s}: exact {st['exact']}/{n} ({100 * st['exact'] / n:.2f}%)  max_rel {st['max_rel']:.3e}"
        )
    print(
        f"  all-4-exact {s['all4_exact']}/{n} ({100 * s['all4_exact'] / n:.2f}%)  vol-match {s['vol_match']}/{n}"
    )
    print(
        "  worst bars:",
        ", ".join(f"{_iso(t)}Z rel={e:.2e}" for e, t in s["worst"] if e > 0) or "none",
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default="analysis/reference", help="evidence directory")
    ap.add_argument("--prefix", default="tvb6_", help="evidence filename prefix")
    args = ap.parse_args()
    base = Path(args.dir)
    p = args.prefix

    tv15 = load_tv_bars(base / f"{p}tv_xyzMSTR_15m.json")
    tv60 = load_tv_bars(base / f"{p}tv_xyzMSTR_60m.json")
    tv1d = load_tv_bars(base / f"{p}tv_xyzMSTR_1D.json")
    hl15 = load_hl_candles(base / f"{p}hl_xyzMSTR_15m.json")
    hl1h = load_hl_candles(base / f"{p}hl_xyzMSTR_1h.json")
    hl4h = load_hl_candles(base / f"{p}hl_xyzMSTR_4h.json")
    hl1d = load_hl_candles(base / f"{p}hl_xyzMSTR_1d.json")

    _print_report("15m native (HL floor 2026-05-12)", diff_stats(tv15, hl15))
    _print_report("60m native (HL floor 2025-12-07)", diff_stats(tv60, hl1h))
    _print_report("1D native (full window)", diff_stats(tv1d, hl1d))

    agg4h = aggregate(tv60, H4_MS)
    hl1h_floor = min(hl1h)
    pre = {t: v for t, v in agg4h.items() if t < hl1h_floor}
    hl4h_pre = {t: v for t, v in hl4h.items() if t < hl1h_floor}
    _print_report("4h closure: TV60m->4h vs HL 4h, pre-Dec-7 hole", diff_stats(pre, hl4h_pre))

    agg60 = aggregate(tv15, HOUR_MS)
    _print_report("internal: TV15m->60m vs TV 60m (full window)", diff_stats(agg60, tv60))


if __name__ == "__main__":
    main()
