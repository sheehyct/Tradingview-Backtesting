"""Rejected-book replay: every strategy-qualified entry the platform never filled, replayed
through its own bracket on public Hyperliquid candles. Bracket-only (no flip exit); a candle
touching both stop and target is a STOP in the headline (conservative) and counted as ambiguous.
Also calibrates the same simulator on the trades that DID fill.
"""

from __future__ import annotations

import collections
import json
import statistics
import time
from decimal import Decimal as D
from pathlib import Path

import httpx

EX = Path(__file__).parent / "exports"  # raw account exports, gitignored
RES = Path(__file__).parent / "results"  # small derived JSON, tracked
RES.mkdir(exist_ok=True)
ACC = {"v1_STRAT": "dca3d279-", "v2_pilot": "532f13a7-", "prop_test": "e386e46a-"}
INFO = "https://api.hyperliquid.xyz/info"
CACHE = EX / "candles_lost"
CACHE.mkdir(exist_ok=True)
IV_MS = {"1m": 60_000, "5m": 300_000, "15m": 900_000, "1h": 3_600_000}
FEE_RT = 0.000864  # journal fee_rt_pct 0.0864% round trip (taker both sides)


def ts(ms):
    return time.strftime("%m-%d %H:%M", time.gmtime(ms / 1000))


def fetch(coin, iv, start, end):
    p = CACHE / f"{coin.replace(':', '_')}_{iv}_{start}_{end}.json"
    if p.exists():
        return json.load(open(p))
    last = None
    for attempt in range(6):
        try:
            r = httpx.post(INFO, json={"type": "candleSnapshot", "req": {"coin": coin, "interval": iv, "startTime": start, "endTime": end}}, timeout=30)
            if r.status_code == 429:
                time.sleep(12 * (attempt + 1))
                last = "429"
                continue
            r.raise_for_status()
            rows = r.json()
            json.dump(rows, open(p, "w"))
            time.sleep(0.7)
            return rows
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"candles failed {coin} {iv}: {last}")


def candles_from(coin, start, end):
    """Finest interval whose history actually begins at or before `start`.
    Public 1m history is only ~3.5 days deep, so older starts begin at 5m."""
    ivs = ("1m", "5m", "15m", "1h") if start >= end - 3 * 86_400_000 else ("5m", "15m", "1h")
    rows = []
    for iv in ivs:
        rows = fetch(coin, iv, start - IV_MS[iv], end)
        if rows and int(rows[0]["t"]) <= start:
            return rows, iv
    return rows or [], iv


def simulate(side, entry, stop, target, candles, entry_ts):
    """Walk candles at/after entry_ts. Returns (outcome, r, ambiguous, exit_ts, bars)."""
    risk = abs(entry - stop) / entry
    rr = (abs(target - entry) / entry / risk) if target else None
    seen = 0
    last_close = entry
    for c in candles:
        t = int(c["t"])
        if t + IV_MS_CUR[0] <= entry_ts:
            continue  # candle fully before entry
        seen += 1
        hi, lo, last_close = float(c["h"]), float(c["l"]), float(c["c"])
        if side == "buy":
            hit_stop, hit_tgt = lo <= stop, (target is not None and hi >= target)
        else:
            hit_stop, hit_tgt = hi >= stop, (target is not None and lo <= target)
        if hit_stop and hit_tgt:
            return "ambiguous", -1.0, True, t, seen, rr
        if hit_stop:
            return "stop", -1.0, False, t, seen, rr
        if hit_tgt:
            return "target", rr, False, t, seen, rr
    move = (last_close - entry) / entry if side == "buy" else (entry - last_close) / entry
    return "open", move / risk, False, None, seen, rr


IV_MS_CUR = [60_000]


def run(label, rows, now_ms):
    """rows: dicts with symbol side entry stop target entry_ts key tf pattern dir reason account(s)."""
    out = []
    for r in rows:
        candles, iv = candles_from(r["symbol"], r["entry_ts"], now_ms)
        IV_MS_CUR[0] = IV_MS[iv]
        if not candles:
            out.append(dict(r, outcome="no_data", r=0.0, iv=iv, bars=0))
            continue
        outcome, rmult, amb, exit_ts, bars, rr = simulate(
            r["side"], r["entry"], r["stop"], r["target"], candles, r["entry_ts"]
        )
        risk = abs(r["entry"] - r["stop"]) / r["entry"]
        out.append(
            dict(
                r,
                outcome=outcome,
                r=rmult,
                r_net=rmult - FEE_RT / risk,
                ambiguous=amb,
                exit_ts=exit_ts,
                bars=bars,
                iv=iv,
                rr=rr,
                risk_pct=risk * 100,
                hold_h=((exit_ts - r["entry_ts"]) / 3.6e6)
                if exit_ts
                else (now_ms - r["entry_ts"]) / 3.6e6,
            )
        )
    return out


def report(title, res, group_keys=("tf", "pattern", "dir", "kind", "reason")):
    print("=" * 110)
    print(title)
    res = [r for r in res if r["outcome"] != "no_data"]
    oc = collections.Counter(r["outcome"] for r in res)
    resolved = [r for r in res if r["outcome"] in ("stop", "target", "ambiguous")]
    opn = [r for r in res if r["outcome"] == "open"]
    cons = sum(r["r"] for r in res)
    opt = cons + sum((r["rr"] + 1.0) for r in res if r["outcome"] == "ambiguous" and r["rr"])
    net = sum(r["r_net"] for r in res)
    print(
        f"  n={len(res)} outcomes={dict(oc)} | resolved {len(resolved)}: target {oc['target']} stop {oc['stop']} ambiguous {oc['ambiguous']} | open {len(opn)} (marked to last close)"
    )
    print(
        f"  sum R conservative {cons:+.2f} (ambiguous=stop) | optimistic {opt:+.2f} (ambiguous=target) | net of fees {net:+.2f} | per trade {cons / len(res):+.3f}R"
    )
    if resolved:
        wr = oc["target"] / len(resolved)
        print(
            f"  resolved win rate {wr:.0%} | median rr of resolved {statistics.median(r['rr'] for r in resolved if r['rr']):.2f} | median risk {statistics.median(r['risk_pct'] for r in resolved):.2f}% | median hold of resolved {statistics.median(r['hold_h'] for r in resolved):.1f}h"
        )
    for key in group_keys:
        agg = collections.defaultdict(lambda: [0, 0, 0, 0.0])
        for r in res:
            a = agg[str(r.get(key))]
            a[0] += 1
            a[1] += r["outcome"] == "target"
            a[2] += r["outcome"] in ("stop", "ambiguous")
            a[3] += r["r"]
        parts = [
            f"{k}: n={v[0]} tgt={v[1]} stp={v[2]} R={v[3]:+.2f}"
            for k, v in sorted(agg.items(), key=lambda kv: -kv[1][0])
        ]
        print(f"  by {key}: " + " | ".join(parts))


def main():
    now_ms = None
    lost = {}
    filled = []
    decisions = {}
    for label, pref in ACC.items():
        d = json.load(open(next(EX.glob(f"export-{pref}*.json")), encoding="utf-8"))
        now_ms = max(now_ms or 0, d["exported_at"])
        for e in d["ledger"]:
            if e["kind"] == "hip3_decision":
                c = e["body"]["candidate"]
                decisions.setdefault(c.get("key"), c)
        fills_by_order = collections.defaultdict(list)
        for f in d["fills"]:
            fills_by_order[f["order_id"]].append(f)
        for o in d["orders"]:
            if o["client_id"].count(":") != 2:
                continue
            br = o.get("bracket") or {}
            sk = br.get("signal_key") or "|||"
            coin, tf, pattern, direction = (sk.split("|") + [""] * 4)[:4]
            base = dict(
                symbol=o["symbol"],
                side=o["side"],
                key=sk,
                tf=tf,
                pattern=pattern,
                dir=direction,
                stop=float(br["stop_price"]) if br.get("stop_price") else None,
                target=float(br["target_price"])
                if br.get("target_price") and float(br["target_price"]) > 0
                else None,
                kind=(decisions.get(sk) or {}).get("kind"),
                lev=o.get("leverage"),
            )
            if o["status"] in ("rejected", "cancelled"):
                reason = (o.get("preflight_refusal") or o.get("reason") or o["status"])[:40]
                row = dict(
                    base,
                    entry=float(o["reference_price"]),
                    entry_ts=o["created_at"],
                    reason=reason,
                    account=label,
                )
                if row["stop"] is None:
                    continue
                prev = lost.get(sk)
                if prev is None or row["entry_ts"] < prev["entry_ts"]:
                    row["accounts"] = sorted(set((prev or {}).get("accounts", [])) | {label})
                    lost[sk] = row
                else:
                    prev["accounts"] = sorted(set(prev["accounts"]) | {label})
            elif o["status"] == "filled":
                fl = sorted(fills_by_order[o["id"]], key=lambda f: f["ts"])
                if not fl or base["stop"] is None:
                    continue
                q = sum(D(f["qty"]) for f in fl)
                px = float(sum(D(f["qty"]) * D(f["price"]) for f in fl) / q)
                filled.append(
                    dict(
                        base,
                        entry=px,
                        entry_ts=fl[0]["ts"],
                        reason="filled",
                        account=label,
                        order_id=o["id"],
                    )
                )
    # actual outcomes for the filled set (from the earlier MFE pass)
    actual = {}
    mm = json.load(open(RES / "mfe_mae.json"))
    for label, rows in mm.items():
        for r in rows:
            actual[(label, r["coin"], int(r["entry_ts"]))] = r
    print(
        f"export time {ts(now_ms)}Z | lost distinct signals {len(lost)} | filled entries {len(filled)}"
    )
    # ---- calibration ----
    cal = run("filled", filled, now_ms)
    print("=" * 110)
    print("CALIBRATION: bracket-only simulator vs what actually happened on the FILLED trades")
    agree = collections.Counter()
    for r in cal:
        a = actual.get((r["account"], r["symbol"], r["entry_ts"]))
        act = a["exit"] if a else "OPEN"
        act_r = float(a["r"]) if a else None
        flag = ""
        if act in ("stop", "target"):
            flag = (
                "AGREE"
                if r["outcome"] == act
                else ("AMBIG" if r["outcome"] == "ambiguous" else "DISAGREE")
            )
        elif act == "OPEN":
            flag = "open"
        else:
            flag = f"flip->{r['outcome']}"
        agree[flag] += 1
        print(
            f"  {r['account']:9} {r['symbol']:12}{r['tf']:3} {r['pattern']:8}{r['dir']:5} {ts(r['entry_ts'])}  sim={r['outcome']:9} simR={r['r']:+.2f}  actual={act:10} actR={'' if act_r is None else f'{act_r:+.2f}'}  {flag} ({r['iv']})"
        )
    print("  summary:", dict(agree))
    flips = [
        r
        for r in cal
        if (actual.get((r["account"], r["symbol"], r["entry_ts"])) or {}).get("exit")
        not in ("stop", "target", None)
    ]
    if flips:
        print(
            f"  flip-exited trades under bracket-only: sum simR {sum(r['r'] for r in flips):+.2f} vs actual {sum(float(actual[(r['account'], r['symbol'], r['entry_ts'])]['r']) for r in flips):+.2f}"
        )
    # ---- lost book ----
    rows = sorted(lost.values(), key=lambda r: r["entry_ts"])
    res = run("lost", rows, now_ms)
    report(
        f"LOST BOOK (union of distinct qualified signals never filled): {len(res)} signals, {ts(rows[0]['entry_ts'])} -> {ts(rows[-1]['entry_ts'])}",
        res,
    )
    for label in ACC:
        sub = [r for r in res if label in r["accounts"]]
        if sub:
            report(
                f"  lost book as seen by {label}: {len(sub)} signals",
                sub,
                group_keys=("tf", "dir", "reason"),
            )
    # era split
    V10 = 1790797560000
    report(
        "  lost signals BEFORE v10 deploy (09-26 19:46Z)",
        [r for r in res if r["entry_ts"] < V10],
        group_keys=("tf",),
    )
    report(
        "  lost signals AFTER v10 deploy",
        [r for r in res if r["entry_ts"] >= V10],
        group_keys=("tf",),
    )
    # pooled: filled actual + lost sim = "what the strategy chose"
    print("=" * 110)
    act_rows = [a for rows_ in mm.values() for a in rows_]
    act_sum = sum(float(a["r"]) for a in act_rows)
    lost_sum = sum(r["r"] for r in res if r["outcome"] != "no_data")
    print(
        f"STRATEGY-CHOSEN BOOK, whole month: filled actual {len(act_rows)} trades {act_sum:+.2f}R  +  lost simulated {len(res)} signals {lost_sum:+.2f}R  =  {act_sum + lost_sum:+.2f}R over {len(act_rows) + len(res)} trades ({(act_sum + lost_sum) / (len(act_rows) + len(res)):+.3f}R/trade)"
    )
    print(
        "  WATERMARKS: lost entries at the order reference price (no slippage); bracket-only, the flip exit is NOT replayed; ambiguous candles = stop; open signals marked to last close; fees ~0.0864% round trip excluded from gross R."
    )
    json.dump(
        {"calibration": cal, "lost": res}, open(RES / "lostbook.json", "w"), indent=1, default=str
    )
    # ---- Asia-session census: underlying_closed refusals by coin and UTC hour ----
    print("=" * 110)
    print(
        "UNDERLYING-CLOSED refusals (distinct signals, both v2 journals): by coin (top 25) and by UTC hour"
    )
    uc = [c for c in decisions.values() if c.get("reason") == "underlying_closed"]
    bycoin = collections.Counter(c["symbol"] for c in uc)
    print("  n distinct:", len(uc))
    print("  by coin:", dict(bycoin.most_common(25)))
    byhour = collections.Counter(time.gmtime(c["ts"] / 1000).tm_hour for c in uc)
    print("  by UTC hour:", {h: byhour.get(h, 0) for h in range(24)})
    bytf = collections.Counter(c["tf"] for c in uc)
    print("  by tf:", dict(bytf))
    # which of those were otherwise fully qualified? (reason is first-refusal; cannot tell) -> state it
    print(
        "  NOTE: the journal records the FIRST refusal only; a signal refused for the session clock may also have failed later gates."
    )


if __name__ == "__main__":
    main()
