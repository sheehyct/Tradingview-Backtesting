"""TVB-14 acceptance fixture: DRAM weekly rolling compound-3 pool.

Replays the pool rule that pine/tfc_bf_watch.pine v4 implements, against the
committed venue bars (analysis/reference/tvb14_dram_1h_hl.json, Hyperliquid
public candleSnapshot, fetched 2026-07-19). The rule, user-ratified
2026-07-19: at each weekly close, for N = 1..N_MAX ascending, the envelope
(max high / min low) of the last N CLOSED weeks strictly takes out BOTH
sides of the envelope of the prior N weeks (R10 strict operators; N=1 is
the plain scenario 3, N>1 the compound 3). Smallest qualifying N wins.
Lines anchor wick-to-wick (taken-out extreme -> taking-out extreme, at wick
times). Lifecycle: alive -> consumed (containment touch) or crossed
(confirmed close beyond).

Expected output (verified against the deployed indicator's drawn lines,
TV USER;7c28fa0b v4.0, DRAM 5m, 2026-07-19):
  F1 born Jun-8  N=1  lower 55.000@May-26 -> 52.788@Jun-6   alive
                      upper 66.422@May-31 -> 70.154@Jun-2   alive
  F2 born Jun-29 N=1  lower 67.417@Jun-15 -> 67.184@Jun-24  consumed Jun-29 14:00
                      upper 81.242@Jun-21 -> 82.016@Jun-22  alive
  F3 births at the Jul-20 00:00 UTC weekly roll (N=4, lower 52.788 ->
  48.663@Jul-17, ~48.4 at birth; upper duplicates F2's upper -> ghost).

Run: uv run python analysis/tvb14_bf_pool_fixture.py
"""

import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DAY = 86400
N_MAX = 6

raw = json.loads((REPO / "analysis" / "reference" / "tvb14_dram_1h_hl.json").read_text())
bars = [[int(b[0]), b[1], b[2], b[3], b[4]] for b in raw["bars"]]


def wstart(ts):
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    mid = int(datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc).timestamp())
    return mid - dt.weekday() * DAY


def ds(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%m-%d %H:%M")


weeks = []
cur = None
formations = []

for ts, o, h, l, c in bars:
    k = wstart(ts)
    if cur is None or k != cur["start"]:
        if cur is not None:
            weeks.append(cur)
            for n in range(1, min(N_MAX, len(weeks) // 2) + 1):
                last, prev = weeks[-n:], weeks[-2 * n : -n]
                a_h = max(w["high"] for w in last)
                a_l = min(w["low"] for w in last)
                b_h = max(w["high"] for w in prev)
                b_l = min(w["low"] for w in prev)
                if a_h > b_h and a_l < b_l:
                    lo1 = min(prev, key=lambda w: w["low"])
                    lo2 = min(last, key=lambda w: w["low"])
                    hi1 = max(prev, key=lambda w: w["high"])
                    hi2 = max(last, key=lambda w: w["high"])
                    cand = {
                        "born": k,
                        "N": n,
                        "lo": (lo1["low_t"], lo1["low"], lo2["low_t"], lo2["low"]),
                        "up": (hi1["high_t"], hi1["high"], hi2["high_t"], hi2["high"]),
                        "lo_state": "alive",
                        "up_state": "alive",
                    }
                    if formations:
                        t = formations[-1]
                        if t["lo"] == cand["lo"] and t["up"] == cand["up"]:
                            break
                        if t["lo"][:2] == cand["lo"][:2] and t["up"][:2] == cand["up"][:2]:
                            t["lo_state"] = t["up_state"] = "superseded"
                    formations.append(cand)
                    break
        cur = {"start": k, "high": h, "low": l, "high_t": ts, "low_t": ts}
    else:
        if h > cur["high"]:
            cur["high"], cur["high_t"] = h, ts
        if l < cur["low"]:
            cur["low"], cur["low_t"] = l, ts


def val(a, t):
    t1, v1, t2, v2 = a
    return v2 if t2 == t1 else v2 + (v2 - v1) / (t2 - t1) * (t - t2)


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
print(f"data through {ds(now_ts)} UTC; formations (N_MAX={N_MAX}):")
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
