"""TVB-14 acceptance fixture: DRAM rolling compound-3 pool, any base TF.

Replays the pool rule that pine/tfc_bf_watch.pine implements (v4 weekly-only;
v5 runs the same rule as parallel 12h/D/W/M pools), against the committed
venue bars (analysis/reference/tvb14_dram_1h_hl.json, Hyperliquid public
candleSnapshot, fetched 2026-07-19). The rule, user-ratified 2026-07-19: at
each base-TF close, for N = 1..N_MAX ascending, the envelope (max high /
min low) of the last N CLOSED candles strictly takes out BOTH sides of the
envelope of the prior N (R10 strict operators; N=1 is the plain scenario 3,
N>1 the compound 3). Smallest qualifying N wins. Lines anchor wick-to-wick.
Lifecycle: alive -> consumed (containment touch) or crossed (confirmed
close beyond) or superseded (same left anchors re-anchored).

Weekly expected output (verified against the deployed v4 drawn lines,
TV USER;7c28fa0b, DRAM 5m, 2026-07-19):
  F1 born Jun-8  N=1  lower 55.000@May-26 -> 52.788@Jun-6   alive
                      upper 66.422@May-31 -> 70.154@Jun-2   alive
  F2 born Jun-29 N=1  lower 67.417@Jun-15 -> 67.184@Jun-24  consumed Jun-29 14:00
                      upper 81.242@Jun-21 -> 82.016@Jun-22  alive
  F3 born at the Jul-20 00:00 UTC roll: N=4, lower 52.788 -> 48.663@Jul-17
  (~48.4 at birth; upper duplicates F2's upper -> ghost).

Run: uv run python analysis/tvb14_bf_pool_fixture.py [12h|D|W]
(default W; lifecycle resolution = the 1h bars, so chart-resolution
touch/cross timings may differ by minutes)
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DAY = 86400
N_MAX = 6
MIN_SEP = 1.0  # anchor-separation validity filter, in base periods (v5 default)

raw = json.loads((REPO / "analysis" / "reference" / "tvb14_dram_1h_hl.json").read_text())
bars = [[int(b[0]), b[1], b[2], b[3], b[4]] for b in raw["bars"]]


def wstart(ts):
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    mid = int(datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc).timestamp())
    return mid - dt.weekday() * DAY


KEYS = {
    "12h": lambda t: t - t % (12 * 3600),
    "D": lambda t: t - t % DAY,
    "W": wstart,
}


def ds(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%m-%d %H:%M")


def run_pool(key_fn, period_s):
    """Mirrors the v5 pool: min-anchor-separation validity filter (MIN_SEP
    base periods) ghosts a side at birth; formations with both sides ghost
    are skipped; per-side exact-duplicate lines also ghost."""
    periods = []
    cur = None
    formations = []
    min_gap = int(period_s * MIN_SEP)
    for ts, o, h, l, c in bars:
        k = key_fn(ts)
        if cur is None or k != cur["start"]:
            if cur is not None:
                periods.append(cur)
                for n in range(1, min(N_MAX, len(periods) // 2) + 1):
                    last, prev = periods[-n:], periods[-2 * n : -n]
                    a_h = max(w["high"] for w in last)
                    a_l = min(w["low"] for w in last)
                    b_h = max(w["high"] for w in prev)
                    b_l = min(w["low"] for w in prev)
                    if a_h > b_h and a_l < b_l:
                        lo1 = min(prev, key=lambda w: w["low"])
                        lo2 = min(last, key=lambda w: w["low"])
                        hi1 = max(prev, key=lambda w: w["high"])
                        hi2 = max(last, key=lambda w: w["high"])
                        lo = (lo1["low_t"], lo1["low"], lo2["low_t"], lo2["low"])
                        up = (hi1["high_t"], hi1["high"], hi2["high_t"], hi2["high"])
                        lo_ghost = lo[2] - lo[0] < min_gap or any(f["lo"] == lo for f in formations)
                        up_ghost = up[2] - up[0] < min_gap or any(f["up"] == up for f in formations)
                        cand = {
                            "born": k,
                            "N": n,
                            "lo": lo,
                            "up": up,
                            "lo_state": "ghost" if lo_ghost else "alive",
                            "up_state": "ghost" if up_ghost else "alive",
                        }
                        if formations:
                            t = formations[-1]
                            if t["lo"] == cand["lo"] and t["up"] == cand["up"]:
                                break
                            if t["lo"][:2] == cand["lo"][:2] and t["up"][:2] == cand["up"][:2]:
                                if t["lo_state"] == "alive":
                                    t["lo_state"] = "superseded"
                                if t["up_state"] == "alive":
                                    t["up_state"] = "superseded"
                        if not (lo_ghost and up_ghost):
                            formations.append(cand)
                        break
            cur = {"start": k, "high": h, "low": l, "high_t": ts, "low_t": ts}
        else:
            if h > cur["high"]:
                cur["high"], cur["high_t"] = h, ts
            if l < cur["low"]:
                cur["low"], cur["low_t"] = l, ts
    return formations


def val(a, t):
    t1, v1, t2, v2 = a
    return v2 if t2 == t1 else v2 + (v2 - v1) / (t2 - t1) * (t - t2)


PERIOD_S = {"12h": 12 * 3600, "D": DAY, "W": 7 * DAY}
tf = sys.argv[1] if len(sys.argv) > 1 else "W"
formations = run_pool(KEYS[tf], PERIOD_S[tf])

for f in formations:
    for ts, o, h, l, c in bars:
        if ts < f["born"]:
            continue
        lv, uv = val(f["lo"], ts), val(f["up"], ts)
        if f["lo_state"] == "alive":
            if l <= lv <= h:
                f["lo_state"] = f"consumed {ds(ts)}"
            elif c < lv:
                f["lo_state"] = f"crossed {ds(ts)}"
        if f["up_state"] == "alive":
            if l <= uv <= h:
                f["up_state"] = f"consumed {ds(ts)}"
            elif c > uv:
                f["up_state"] = f"crossed {ds(ts)}"

now_ts = bars[-1][0]
print(f"{tf}-pool, data through {ds(now_ts)} UTC (N_MAX={N_MAX}): {len(formations)} formations")
for i, f in enumerate(formations):
    t1, v1, t2, v2 = f["lo"]
    print(f"  F{i + 1} born {ds(f['born'])} N={f['N']}")
    print(
        f"     lower {v1:.3f}@{ds(t1)} -> {v2:.3f}@{ds(t2)} | now {val(f['lo'], now_ts):.2f} | {f['lo_state']}"
    )
    t1, v1, t2, v2 = f["up"]
    print(
        f"     upper {v1:.3f}@{ds(t1)} -> {v2:.3f}@{ds(t2)} | now {val(f['up'], now_ts):.2f} | {f['up_state']}"
    )
