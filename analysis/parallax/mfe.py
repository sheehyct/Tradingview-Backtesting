"""MFE/MAE per closed paper trade from Hyperliquid public 1m candles (read-only public API)."""

from __future__ import annotations

import collections
import json
import time
from decimal import Decimal as D
from pathlib import Path

import httpx

EX = Path(__file__).parent / "exports"  # raw account exports, gitignored
RES = Path(__file__).parent / "results"  # small derived JSON, tracked
RES.mkdir(exist_ok=True)
ACC = {"v1_STRAT": "dca3d279-", "v2_pilot": "532f13a7-", "prop_test": "e386e46a-"}
INFO = "https://api.hyperliquid.xyz/info"
cache_dir = EX / "candles"
cache_dir.mkdir(exist_ok=True)


def ts(ms):
    return time.strftime("%m-%d %H:%M", time.gmtime(ms / 1000))


def candles(coin, start, end, interval="1m"):
    p = cache_dir / f"{coin.replace(':', '_')}_{interval}_{start}_{end}.json"
    if p.exists():
        return json.load(open(p))
    r = httpx.post(
        INFO,
        json={
            "type": "candleSnapshot",
            "req": {"coin": coin, "interval": interval, "startTime": start, "endTime": end},
        },
        timeout=30,
    )
    r.raise_for_status()
    rows = r.json()
    json.dump(rows, open(p, "w"))
    time.sleep(0.25)
    return rows


def reconstruct(d):
    orders = {o["id"]: o for o in d["orders"]}
    entries = [
        f
        for f in d["fills"]
        if f["client_id"].count(":") == 2 and f["client_id"].startswith("hip3:entry:")
    ]
    exits = [f for f in d["fills"] if f not in entries]
    exit_logs = [
        json.loads(l["message"])
        for l in d["logs"]
        if str(l.get("message", "")).startswith('{"event":"exit"')
    ]
    trades = []
    for e0 in sorted(entries, key=lambda f: f["ts"]):
        root = e0["client_id"].split(":")[2]
        eo = orders.get(e0["order_id"], {})
        br = eo.get("bracket", {})
        coin, tf, pattern, direction, _ = (br.get("signal_key", "|||").split("|") + [""] * 5)[:5]
        # bracket exits share the root; software exits match by symbol after entry
        xs = [
            f
            for f in exits
            if f["client_id"].split(":")[2] == root
            or (
                f["client_id"].startswith("hip3:exit:")
                and f["symbol"] == e0["symbol"]
                and f["ts"] > e0["ts"]
            )
        ]
        xs = sorted(xs, key=lambda f: f["ts"])
        # stop at the first fill that flattens
        closing = []
        for f in xs:
            closing.append(f)
            if D(f["position_after"]) == 0:
                break
        kinds = [
            f["client_id"].split(":")[-1]
            if f["client_id"].startswith("hip3:entry:")
            else "software"
            for f in closing
        ]
        reason = None
        if "software" in kinds:
            cands = [l["reason"] for l in exit_logs if l["symbol"] == e0["symbol"]]
            reason = cands[-1] if cands else "software?"
        ep = D(e0["price"])
        stop = D(br["stop_price"]) if br.get("stop_price") else None
        risk = abs(ep - stop) / ep if stop else None
        xq = sum(D(f["qty"]) for f in closing)
        xp = sum(D(f["qty"]) * D(f["price"]) for f in closing) / xq if xq else None
        trades.append(
            {
                "coin": e0["symbol"],
                "tf": tf,
                "pattern": pattern,
                "dir": direction,
                "side": e0["side"],
                "entry_ts": e0["ts"],
                "exit_ts": closing[-1]["ts"] if closing else None,
                "entry_px": ep,
                "exit_px": xp,
                "stop": stop,
                "target": D(br["target_price"]) if br.get("target_price") else None,
                "risk": risk,
                "pnl": sum(D(f["realized_pnl"]) for f in [e0] + closing),
                "exit": reason or ("+".join(sorted(set(kinds))) if kinds else "OPEN"),
                "notional": D(e0["qty"]) * ep,
                "lev": eo.get("leverage"),
            }
        )
    return trades


out = {}
for label, pref in ACC.items():
    d = json.load(open(next(EX.glob(f"export-{pref}*.json")), encoding="utf-8"))
    trades = reconstruct(d)
    print("=" * 112)
    print(
        f"{label}  (R = fraction of planned stop distance; MFE/MAE from 1m highs/lows between entry and exit)"
    )
    print(
        f"{'coin':12}{'tf':4}{'pattern':9}{'dir':5}{'entry':13}{'hold_h':8}{'risk%':7}{'rr':6}{'MFE_R':7}{'MAE_R':7}{'R':7}{'pnl$':8}{'exit'}"
    )
    rows = []
    for t in trades:
        if not t["exit_ts"] or not t["risk"]:
            print(
                f"{t['coin']:12}{t['tf']:4}{t['pattern']:9}{t['dir']:5}{ts(t['entry_ts']):13}  OPEN  risk {float(t['risk'] or 0) * 100:.2f}%"
            )
            continue
        c = []
        for iv in ("1m", "5m", "15m", "1h"):
            c = candles(t["coin"], t["entry_ts"] - 60000, t["exit_ts"] + 60000, iv)
            exp = (t["exit_ts"] - t["entry_ts"]) / {"1m": 6e4, "5m": 3e5, "15m": 9e5, "1h": 3.6e6}[iv]
            if c and len(c) >= 0.9 * exp and int(c[0]["t"]) <= t["entry_ts"] + {"1m": 6e4, "5m": 3e5, "15m": 9e5, "1h": 3.6e6}[iv]:
                break
        t["interval"] = iv
        ep = float(t["entry_px"])
        hi = max((float(x["h"]) for x in c), default=ep)
        lo = min((float(x["l"]) for x in c), default=ep)
        if t["side"] == "buy":
            mfe, mae = (hi - ep) / ep, (ep - lo) / ep
        else:
            mfe, mae = (ep - lo) / ep, (hi - ep) / ep
        risk = float(t["risk"])
        move = (
            ((float(t["exit_px"]) - ep) / ep)
            if t["side"] == "buy"
            else ((ep - float(t["exit_px"])) / ep)
        )
        rr = (abs(float(t["target"]) - ep) / ep / risk) if t["target"] else None
        hold = (t["exit_ts"] - t["entry_ts"]) / 3.6e6
        row = dict(
            t,
            hold_h=hold,
            mfe_r=mfe / risk,
            mae_r=mae / risk,
            r=move / risk,
            rr=rr,
            n_candles=len(c),
        )
        rows.append(row)
        print(
            f"{t['coin']:12}{t['tf']:4}{t['pattern']:9}{t['dir']:5}{ts(t['entry_ts']):13}{hold:8.2f}{risk * 100:7.2f}{(rr or 0):6.2f}{mfe / risk:7.2f}{mae / risk:7.2f}{move / risk:7.2f}{float(t['pnl']):8.2f}  {t['exit']}  ({len(c)} 1m bars)"
        )
    out[label] = rows
    if rows:
        w = [r for r in rows if r["r"] > 0]
        l = [r for r in rows if r["r"] <= 0]
        print(
            f"\n  closed {len(rows)} | wins {len(w)} | sum R {sum(r['r'] for r in rows):.2f} | sum $ {sum(float(r['pnl']) for r in rows):.2f}"
        )
        if w:
            print(
                f"  winners: median MFE {sorted(r['mfe_r'] for r in w)[len(w) // 2]:.2f}R, median MAE {sorted(r['mae_r'] for r in w)[len(w) // 2]:.2f}R"
            )
        if l:
            print(
                f"  losers:  median MFE {sorted(r['mfe_r'] for r in l)[len(l) // 2]:.2f}R, median MAE {sorted(r['mae_r'] for r in l)[len(l) // 2]:.2f}R; losers that reached >=0.5R MFE: {sum(1 for r in l if r['mfe_r'] >= 0.5)}, >=1.0R: {sum(1 for r in l if r['mfe_r'] >= 1.0)}"
            )
        for key in ("tf", "pattern", "dir", "exit"):
            agg = collections.defaultdict(lambda: [0, 0, 0.0, 0.0, 0.0])
            for r in rows:
                a = agg[r[key]]
                a[0] += 1
                a[1] += r["r"] > 0
                a[2] += r["r"]
                a[3] += r["mfe_r"]
                a[4] += r["mae_r"]
            print(
                f"  by {key}: "
                + " | ".join(
                    f"{k}: n={v[0]} w={v[1]} R={v[2]:.2f} avgMFE={v[3] / v[0]:.2f} avgMAE={v[4] / v[0]:.2f}"
                    for k, v in sorted(agg.items())
                )
            )
json.dump(out, open(RES / "mfe_mae.json", "w"), indent=1, default=str)
