"""Round-trip reconstruction + rejection census from Parallax HIP-3 exports (read-only)."""

from __future__ import annotations

import collections
import json
import time
from decimal import Decimal as D
from pathlib import Path

EXPORTS = Path(__file__).parent / "exports"  # raw account exports, gitignored
RES = Path(__file__).parent / "results"  # small derived JSON, tracked
RES.mkdir(exist_ok=True)
ACCOUNTS = {"v1_STRAT": "dca3d279-", "v2_pilot": "532f13a7-", "prop_test": "e386e46a-"}
V10_DEPLOY_MS = 1790797560000  # 2026-09-26T19:46Z worker upload


def ts(ms):
    return time.strftime("%m-%d %H:%M", time.gmtime(ms / 1000)) if ms else "-"


def load(pref):
    p = next(EXPORTS.glob(f"export-{pref}*.json"))
    return json.load(open(p, encoding="utf-8"))


def round_trips(d):
    """Group fills by entry client_id root: 'hip3:entry:<hash>' (+ ':stop' / ':target' / exit variants)."""
    orders = {o["id"]: o for o in d["orders"]}
    groups = collections.defaultdict(list)
    for f in d["fills"]:
        root = (
            f["client_id"].split(":")[2]
            if f["client_id"].startswith("hip3:entry:")
            else f["client_id"]
        )
        groups[root].append(f)
    trades = []
    for root, fills in groups.items():
        fills.sort(key=lambda f: f["ts"])
        entry = [f for f in fills if f["client_id"] == f"hip3:entry:{root}"]
        exits = [f for f in fills if f["client_id"] != f"hip3:entry:{root}"]
        if not entry:
            trades.append({"root": root, "note": "exit-only fills", "fills": fills})
            continue
        e0 = entry[0]
        eo = orders.get(e0["order_id"], {})
        br = eo.get("bracket", {})
        sk = br.get("signal_key", "|||")
        coin, tf, pattern, direction, _bar = (sk.split("|") + ["", "", "", "", ""])[:5]
        eq = sum(D(f["qty"]) for f in entry)
        ep = sum(D(f["qty"]) * D(f["price"]) for f in entry) / eq if eq else None
        xq = sum(D(f["qty"]) for f in exits)
        xp = sum(D(f["qty"]) * D(f["price"]) for f in exits) / xq if xq else None
        pnl = sum(D(f["realized_pnl"]) for f in fills)
        fees = sum(D(f["fee"]) for f in fills)
        kinds = collections.Counter(
            f["client_id"].split(":")[-1] if f["client_id"].count(":") >= 3 else "entry"
            for f in exits
        )
        stop, target = br.get("stop_price"), br.get("target_price")
        side = e0["side"]
        risk_dist = (abs(ep - D(stop)) / ep) if (ep and stop) else None
        tgt_dist = (abs(D(target) - ep) / ep) if (ep and target and D(target) > 0) else None
        if ep and xp:
            move = (xp - ep) / ep if side == "buy" else (ep - xp) / ep
        else:
            move = None
        trades.append(
            {
                "root": root,
                "coin": coin or e0["symbol"],
                "tf": tf,
                "pattern": pattern,
                "dir": direction,
                "side": side,
                "entry_ts": e0["ts"],
                "exit_ts": exits[-1]["ts"] if exits else None,
                "hold_h": round((exits[-1]["ts"] - e0["ts"]) / 3.6e6, 2) if exits else None,
                "entry_px": ep,
                "exit_px": xp,
                "qty": eq,
                "closed_qty": xq,
                "stop": stop,
                "target": target,
                "risk_pct": risk_dist,
                "target_pct": tgt_dist,
                "rr": (tgt_dist / risk_dist) if (risk_dist and tgt_dist) else None,
                "move_pct": move,
                "r_mult": (move / risk_dist) if (move is not None and risk_dist) else None,
                "pnl": pnl,
                "fees": fees,
                "exit_kinds": dict(kinds),
                "lev": eo.get("leverage"),
                "notional": (eq * ep) if ep else None,
                "open": xq < eq,
            }
        )
    trades.sort(key=lambda t: t.get("entry_ts") or 0)
    return trades


def fmt(x, nd=2):
    if x is None:
        return "-"
    if isinstance(x, D):
        return f"{x:.{nd}f}"
    return f"{x:.{nd}f}" if isinstance(x, float) else str(x)


def pct(x):
    return "-" if x is None else f"{float(x) * 100:.2f}%"


for label, pref in ACCOUNTS.items():
    d = load(pref)
    print("=" * 110)
    print(
        f"{label}: created {ts(d['created_at'])} status {d['status']} realized {d.get('realized_pnl')} fees {d.get('fees')} funding {d['metrics'].get('funding')}"
    )
    trades = round_trips(d)
    print(
        f"{'coin':12}{'tf':4}{'pattern':10}{'dir':5}{'entry':13}{'hold_h':7}{'risk%':8}{'tgt%':8}{'rr':6}{'move%':8}{'R':7}{'pnl$':8}{'lev':4} exit"
    )
    for t in trades:
        if "note" in t:
            print("  ", t["note"], [f["client_id"] for f in t["fills"]])
            continue
        print(
            f"{t['coin']:12}{t['tf']:4}{t['pattern']:10}{t['dir']:5}{ts(t['entry_ts']):13}{fmt(t['hold_h']):7}{pct(t['risk_pct']):8}{pct(t['target_pct']):8}{fmt(t['rr']):6}{pct(t['move_pct']):8}{fmt(t['r_mult']):7}{fmt(t['pnl']):8}{str(t['lev']):4}{'OPEN ' if t['open'] else ''}{t['exit_kinds']}"
        )
    closed = [t for t in trades if "note" not in t and not t["open"]]
    print(
        f"\n closed {len(closed)} | wins {sum(1 for t in closed if t['pnl'] > 0)} | sum pnl {sum(t['pnl'] for t in closed):.2f} | sum R {sum(float(t['r_mult']) for t in closed if t['r_mult'] is not None):.2f}"
    )
    for key in ("tf", "pattern", "dir"):
        agg = collections.defaultdict(lambda: [0, 0, D(0), 0.0])
        for t in closed:
            a = agg[t[key]]
            a[0] += 1
            a[1] += t["pnl"] > 0
            a[2] += t["pnl"]
            a[3] += float(t["r_mult"] or 0)
        print(
            f"  by {key}: "
            + " | ".join(
                f"{k}: n={v[0]} w={v[1]} ${v[2]:.2f} R={v[3]:.2f}" for k, v in sorted(agg.items())
            )
        )
    # rejections on ORDERS (platform-side), split at v10
    rej = collections.Counter()
    for o in d["orders"]:
        if o["status"] == "rejected":
            era = "post-v10" if o["created_at"] >= V10_DEPLOY_MS else "pre-v10"
            reason = (o.get("preflight_refusal") or o.get("reason") or "?")[:90]
            rej[(era, reason)] += 1
    print("\n ORDER rejections (platform side):")
    for (era, reason), n in sorted(rej.items()):
        print(f"   {era:9} {n:4}  {reason}")
    ent = [o for o in d["orders"] if o["client_id"].count(":") == 2]
    print(
        f" entry orders {len(ent)}: "
        + ", ".join(f"{k}={v}" for k, v in collections.Counter(o["status"] for o in ent).items())
    )
    for era_name, pred in (
        ("pre-v10", lambda o: o["created_at"] < V10_DEPLOY_MS),
        ("post-v10", lambda o: o["created_at"] >= V10_DEPLOY_MS),
    ):
        sub = [o for o in ent if pred(o)]
        if sub:
            print(
                f"   {era_name}: "
                + ", ".join(
                    f"{k}={v}" for k, v in collections.Counter(o["status"] for o in sub).items()
                )
            )
    # decision journal schema
    dec = [e for e in d["ledger"] if e["kind"] == "hip3_decision"]
    cb = [e for e in d["ledger"] if e["kind"] == "hip3_callback"]
    if dec:
        print(f"\n hip3_decision n={len(dec)} span {ts(dec[-1]['ts'])} -> {ts(dec[0]['ts'])}")
        print("   body keys:", sorted(dec[0]["body"].keys()))
        print("   sample:", json.dumps(dec[0]["body"])[:900])
        reasons = collections.Counter(
            str(e["body"].get("reason") or e["body"].get("outcome") or e["body"].get("status"))
            for e in dec
        )
        print("   by reason/outcome:", dict(reasons.most_common(20)))
    if cb:
        print(f"\n hip3_callback n={len(cb)}")
        print("   body keys:", sorted(cb[0]["body"].keys()))
        print("   sample:", json.dumps(cb[0]["body"])[:700])
    json.dump(
        [
            {k: (str(v) if isinstance(v, D) else v) for k, v in t.items() if k != "fills"}
            for t in trades
        ],
        open(RES / f"trades_{label}.json", "w"),
        indent=1,
        default=str,
    )
