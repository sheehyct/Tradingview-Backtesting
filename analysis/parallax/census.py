"""Random-walk baseline, chase-distance diagnostic, and named-cluster session census
over the Parallax PAPER exports (reads exports/ + lostbook.json + mfe_mae.json)."""

from __future__ import annotations

import collections
import json
import math
import statistics
import time
from pathlib import Path

EX = Path(__file__).parent / "exports"  # raw account exports, gitignored
RES = Path(__file__).parent / "results"  # small derived JSON, tracked
RES.mkdir(exist_ok=True)
lb = json.load(open(RES / "lostbook.json"))
mm = json.load(open(RES / "mfe_mae.json"))
lost = [r for r in lb["lost"] if r["outcome"] in ("stop", "target")]
out = {}


def baseline(rows, rr_key, win_key):
    """Expected wins if each trade were a driftless random walk inside its bracket:
    P(target first) = stop_dist / (stop_dist + target_dist) = 1 / (1 + rr)."""
    ps = [1 / (1 + float(r[rr_key])) for r in rows if r.get(rr_key)]
    exp = sum(ps)
    var = sum(p * (1 - p) for p in ps)
    wins = sum(1 for r in rows if win_key(r))
    z = (wins - exp) / math.sqrt(var) if var else float("nan")
    return len(rows), wins, exp, z


n, w, e, z = baseline(lost, "rr", lambda r: r["outcome"] == "target")
print(
    f"A. LOST BOOK resolved: n={n} wins={w} ({w / n:.0%}) | random-walk expectation {e:.1f} ({e / n:.0%}) | z={z:+.2f}"
)
out["lost_vs_random"] = dict(n=n, wins=w, expected=e, z=z)
filled = [r for rows in mm.values() for r in rows if r["exit"] in ("stop", "target")]
n2, w2, e2, z2 = baseline(filled, "rr", lambda r: r["exit"] == "target")
print(
    f"   FILLED stop/target only: n={n2} wins={w2} ({w2 / n2:.0%}) | random expectation {e2:.1f} | z={z2:+.2f}"
)
out["filled_vs_random"] = dict(n=n2, wins=w2, expected=e2, z=z2)
allr = lost + [dict(r, outcome=r["exit"]) for r in filled]
n3, w3, e3, z3 = baseline(allr, "rr", lambda r: r["outcome"] == "target")
print(
    f"   POOLED bracket-resolved: n={n3} wins={w3} ({w3 / n3:.0%}) | random expectation {e3:.1f} ({e3 / n3:.0%}) | z={z3:+.2f}"
)
out["pooled_vs_random"] = dict(n=n3, wins=w3, expected=e3, z=z3)
out["lost_by"] = {}
for key in ("tf", "dir", "kind", "pattern"):
    agg = collections.defaultdict(list)
    for r in lost:
        agg[str(r.get(key))].append(r)
    parts = []
    out["lost_by"][key] = {}
    for k, v in sorted(agg.items(), key=lambda kv: -len(kv[1])):
        if len(v) < 5:
            continue
        nn, ww, ee, zz = baseline(v, "rr", lambda r: r["outcome"] == "target")
        parts.append(f"{k}: {ww}/{nn} vs {ee:.1f} exp (z {zz:+.1f})")
        out["lost_by"][key][k] = dict(n=nn, wins=ww, expected=ee, z=zz)
    print(f"   lost by {key}: " + " | ".join(parts))

# ---- B. chase distance from the decision journal ----
dec = {}
for pref in ("532f13a7-", "e386e46a-"):
    d = json.load(open(next(EX.glob(f"export-{pref}*.json")), encoding="utf-8"))
    for ev in d["ledger"]:
        if ev["kind"] == "hip3_decision":
            c = ev["body"]["candidate"]
            dec.setdefault(c.get("key"), c)


def chase(c):
    mid, trig, stop = c.get("mid"), c.get("trigger"), c.get("stop")
    if not all(isinstance(x, (int, float)) for x in (mid, trig, stop)) or mid == stop:
        return None
    return abs(mid - trig) / abs(mid - stop)


rows = []
for r in lb["lost"]:
    c = dec.get(r["key"])
    ch = chase(c) if c else None
    if ch is not None:
        rows.append((ch, r["outcome"], r.get("rr") or 0))
srt = sorted(x[0] for x in rows)
print(
    f"\nB. CHASE at decision (|mid-trigger| / |mid-stop|), lost book n={len(rows)}: median {statistics.median(srt):.2f}R, p25 {srt[len(srt) // 4]:.2f}, p75 {srt[3 * len(srt) // 4]:.2f}"
)
out["chase"] = dict(
    n=len(rows), median=statistics.median(srt), p75=srt[3 * len(srt) // 4], buckets={}
)
res = [x for x in rows if x[1] in ("stop", "target")]
for lo, hi, name in (
    (0, 0.1, "<0.10R"),
    (0.1, 0.25, "0.10-0.25R"),
    (0.25, 0.5, "0.25-0.50R"),
    (0.5, 9, ">0.50R"),
):
    sub = [x for x in res if lo <= x[0] < hi]
    if sub:
        wins = sum(1 for x in sub if x[1] == "target")
        exp = sum(1 / (1 + x[2]) for x in sub if x[2])
        print(
            f"   chase {name:11}: n={len(sub):3} wins={wins:2} ({wins / len(sub):.0%}) random exp {exp:.1f} ({exp / len(sub):.0%})"
        )
        out["chase"]["buckets"][name] = dict(n=len(sub), wins=wins, expected=exp)

# ---- C. named clusters ----
clusters = {
    "Korea": [
        "xyz:EWY",
        "xyz:DRAM",
        "xyz:SMSN",
        "xyz:SKHX",
        "xyz:SKHY",
        "xyz:KR200",
        "xyz:KORU",
        "xyz:HYUNDAI",
    ],
    "Asia/EU ETF+ADR": [
        "xyz:EWT",
        "xyz:EWJ",
        "xyz:JP225",
        "xyz:ASML",
        "xyz:ZHIPU",
        "xyz:MINIMAX",
        "xyz:NOK",
        "xyz:EWZ",
        "xyz:BABA",
        "xyz:TSM",
        "xyz:SOFTBANK",
        "xyz:KIOXIA",
    ],
    "Oil/metals/FX": [
        "xyz:CL",
        "xyz:BRENTOIL",
        "xyz:NATGAS",
        "xyz:GOLD",
        "xyz:SILVER",
        "xyz:COPPER",
        "xyz:PLATINUM",
        "xyz:PALLADIUM",
        "xyz:GBP",
        "xyz:EUR",
        "xyz:JPY",
        "xyz:XLE",
        "xyz:USAR",
    ],
}
print("\nC. NAMED CLUSTERS (distinct signals, both v2 journals; first-refusal reason)")
allcoins = collections.Counter(c["symbol"] for c in dec.values())
out["clusters"] = {}
for name, coins in clusters.items():
    present = [c for c in coins if c in allcoins]
    print(f"  {name}: present {present}")
    out["clusters"][name] = {}
    for coin in present:
        cs = [c for c in dec.values() if c["symbol"] == coin]
        reasons = collections.Counter(c.get("reason") for c in cs)
        hrs = collections.Counter(
            time.gmtime(c["ts"] / 1000).tm_hour
            for c in cs
            if c.get("reason") == "underlying_closed"
        )
        top_h = ",".join(f"{h:02d}z:{n}" for h, n in hrs.most_common(4))
        print(
            f"    {coin:14} n={len(cs):4} | {dict(reasons.most_common(4))} | closed-refusal peak hours {top_h}"
        )
        out["clusters"][name][coin] = dict(n=len(cs), reasons=dict(reasons), closed_hours=dict(hrs))
xyz = [c for c in dec.values() if c.get("uni") == "xyz"]
closed = sum(1 for c in xyz if c.get("reason") == "underlying_closed")
print(
    f"\n  xyz distinct signals {len(xyz)} across {len({c['symbol'] for c in xyz})} coins; underlying_closed {closed} ({closed / len(xyz):.0%}); qualified {sum(1 for c in xyz if c.get('verdict') == 'intent')}"
)
out["xyz"] = dict(
    signals=len(xyz),
    coins=len({c["symbol"] for c in xyz}),
    underlying_closed=closed,
    qualified=sum(1 for c in xyz if c.get("verdict") == "intent"),
)
uc = [c for c in dec.values() if c.get("reason") == "underlying_closed"]
out["underlying_closed_by_hour"] = {
    h: n
    for h, n in sorted(collections.Counter(time.gmtime(c["ts"] / 1000).tm_hour for c in uc).items())
}
out["underlying_closed_by_coin_top25"] = dict(
    collections.Counter(c["symbol"] for c in uc).most_common(25)
)
json.dump(out, open(RES / "census.json", "w"), indent=1)
