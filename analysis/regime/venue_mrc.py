"""Venue-native MRC "Tightening" label on the September strategy-chosen book -- characterization.

A-PRIORI DEFINITIONS (fixed here BEFORE any number was read, 2026-10-03, TVB-36)

Source math = tv_indicators/pine/macro_risk_conditions_v1_2.pine (MRC-1 v2.0), Tightening sub-score:
  per component: change over CHG_LEN calc bars (log return for prices), z-scored over Z_LEN = 100
  bars (SMA and population stdev of the change, as Pine ta.stdev), clamped to +-3;
  sub-score = mean of the LIVE component z values * (100 / 3); EMA(3) that holds through gaps;
  hot >= +30, cold <= -30, else quiet. Calc timeframe 15m.
  CHG_LEN: both the code default 4 (one hour) and the header's stated working value 8 (two hours)
  are reported. No other value is tried.

Venue-native component substitutes (Hyperliquid xyz perps, 24/7, the feed the bot already consumes):
  rates  -> xyz:TLT, sign NEGATIVE (TLT falling = long yields rising). Replaces mean(z 2Y, z 10Y).
  dollar -> ONE component: basket log change of xyz:EUR (EURUSD, sign -), xyz:JPY (USDJPY, sign +),
            xyz:GBP (GBPUSD, sign -), weights = their DXY index weights renormalized
            (EUR .576, JPY .136, GBP .119 -> .693 / .164 / .143).
  oil    -> xyz:CL (WTI perp), sign +.
  The Fear sub-score is NOT reproducible venue-native (no VIX, VIX3M or credit perp) and is not
  computed. The 3x3 shock label therefore collapses to its Tightening axis: hot / quiet / cold.

Timing: the label at trade time t uses 15m bars CLOSED at or before t. (The Pine script's
  completed-bar fetch can lag one further calc bar; this read is at most one bar fresher.)
Staleness: a component whose newest closed bar is older than 3 calc bars drops out (MRC staleMult).

Direction mapping (the TVB-35 prior, risk-asset reading), fixed:
  Tightening HOT = headwind for longs / tailwind for shorts; COLD = the reverse; QUIET = no lean.
  alignment per trade: with / against / quiet.
  Energy-linked names (xyz:CL, xyz:BRENTOIL, xyz:NATGAS, xyz:XLE, xyz:CVX, xyz:HO, xyz:URNM,
  xyz:USAR) have no a-priori mapping here and are reported as "unmapped".

Outcomes: the September book of analysis/parallax (results/lostbook.json = 116 lost signals,
  bracket-only simulation; results/mfe_mae.json = 24 filled trades, actual). Wins and the
  random-walk expectation use bracket-resolved trades only; R sums use every trade.
Weekend flag: Fri 20:00 -> Sun 20:00 America/New_York is the xyz internal-oracle window, where
  these perps reprice off their own book; the label there is the perp crowd's, not the market's.

CHARACTERIZATION ONLY: about 140 trades in one month cannot validate a regime filter. This shows
whether the label is computable at every trade and where the month's losses sat against it.
"""

from __future__ import annotations

import collections
import json
import math
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

HERE = Path(__file__).parent
PARALLAX = HERE.parent / "parallax" / "results"
CACHE = HERE / "data" / "venue_mrc"
CACHE.mkdir(parents=True, exist_ok=True)
INFO = "https://api.hyperliquid.xyz/info"
BAR = 900_000
Z_LEN, Z_CAP, SMOOTH, STALE_MULT, HOT, COLD = 100, 3.0, 3, 3, 30.0, -30.0
CHG_LENS = (4, 8)
DXY_W = {"xyz:EUR": (-1.0, 0.693), "xyz:JPY": (+1.0, 0.164), "xyz:GBP": (-1.0, 0.143)}
ENERGY = {
    "xyz:CL",
    "xyz:BRENTOIL",
    "xyz:NATGAS",
    "xyz:XLE",
    "xyz:CVX",
    "xyz:HO",
    "xyz:URNM",
    "xyz:USAR",
}
NY = ZoneInfo("America/New_York")


def fetch(coin: str, start: int, end: int) -> list[dict]:
    p = CACHE / f"{coin.replace(':', '_')}_15m_{start}_{end}.json"
    if p.exists():
        return json.load(open(p))
    last = None
    for attempt in range(6):
        try:
            r = httpx.post(
                INFO,
                json={
                    "type": "candleSnapshot",
                    "req": {"coin": coin, "interval": "15m", "startTime": start, "endTime": end},
                },
                timeout=30,
            )
            if r.status_code == 429:
                time.sleep(12 * (attempt + 1))
                continue
            r.raise_for_status()
            rows = r.json()
            json.dump(rows, open(p, "w"))
            time.sleep(0.7)
            return rows
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"candles failed {coin}: {last}")


def z_series(times: list[int], logs: list[float], chg_len: int) -> dict[int, float]:
    """Pine f_z on the symbol's OWN bars: change over chg_len bars, z over Z_LEN, clamp."""
    chg = [None] * len(logs)
    for i in range(chg_len, len(logs)):
        chg[i] = logs[i] - logs[i - chg_len]
    out = {}
    for i in range(chg_len + Z_LEN - 1, len(logs)):
        win = chg[i - Z_LEN + 1 : i + 1]
        m = sum(win) / Z_LEN
        s = math.sqrt(sum((x - m) ** 2 for x in win) / Z_LEN)
        z = (chg[i] - m) / s if s > 0 else 0.0
        out[times[i]] = max(-Z_CAP, min(Z_CAP, z))
    return out


def in_weekend_window(ms: int) -> bool:
    d = datetime.fromtimestamp(ms / 1000, NY)
    wd, minutes = d.weekday(), d.hour * 60 + d.minute  # Mon=0
    return (wd == 4 and minutes >= 1200) or wd == 5 or (wd == 6 and minutes < 1200)


def load_trades() -> list[dict]:
    lb = json.load(open(PARALLAX / "lostbook.json"))
    mm = json.load(open(PARALLAX / "mfe_mae.json"))
    trades = []
    for r in lb["lost"]:
        if r["outcome"] == "no_data":
            continue
        trades.append(
            dict(
                symbol=r["symbol"],
                dir=r["dir"],
                t=int(r["entry_ts"]),
                r=float(r["r"]),
                rr=r.get("rr"),
                resolved=r["outcome"] in ("stop", "target"),
                win=r["outcome"] == "target",
                src="lost",
            )
        )
    for rows in mm.values():
        for r in rows:
            trades.append(
                dict(
                    symbol=r["coin"],
                    dir=r["dir"],
                    t=int(r["entry_ts"]),
                    r=float(r["r"]),
                    rr=r.get("rr"),
                    resolved=r["exit"] in ("stop", "target"),
                    win=r["exit"] == "target",
                    src="filled",
                )
            )
    return trades


def table(title: str, groups: dict[str, list[dict]]) -> dict:
    print(f"\n  {title}")
    print(
        f"  {'cell':22}{'n':>5}{'resolved':>10}{'wins':>6}{'random exp':>12}{'z':>7}{'sum R':>9}{'R/trade':>9}"
    )
    out = {}
    for name, rows in groups.items():
        res = [x for x in rows if x["resolved"] and x.get("rr")]
        ps = [1 / (1 + float(x["rr"])) for x in res]
        exp, var = sum(ps), sum(p * (1 - p) for p in ps)
        wins = sum(1 for x in res if x["win"])
        z = (wins - exp) / math.sqrt(var) if var > 0 else float("nan")
        sr = sum(x["r"] for x in rows)
        print(
            f"  {name:22}{len(rows):>5}{len(res):>10}{wins:>6}{exp:>12.1f}{z:>+7.2f}{sr:>+9.2f}{(sr / len(rows) if rows else 0):>+9.3f}"
        )
        out[name] = dict(n=len(rows), resolved=len(res), wins=wins, expected=exp, z=z, sum_r=sr)
    return out


def main() -> None:
    trades = load_trades()
    t0 = min(x["t"] for x in trades) - (Z_LEN + 40) * BAR
    t1 = max(x["t"] for x in trades) + 2 * BAR
    coins = ["xyz:TLT", "xyz:EUR", "xyz:JPY", "xyz:GBP", "xyz:CL"]
    bars = {}
    for c in coins:
        rows = fetch(c, t0, t1)
        bars[c] = ([int(r["t"]) for r in rows], [math.log(float(r["c"])) for r in rows])
        span = (bars[c][0][-1] - bars[c][0][0]) / BAR + 1 if rows else 0
        print(
            f"{c:10} {len(rows):5} bars, coverage {len(rows) / span:.1%} of the 15m grid"
            if rows
            else f"{c} NO DATA"
        )
    # dollar basket on the intersection of the three FX grids
    common = sorted(set(bars["xyz:EUR"][0]) & set(bars["xyz:JPY"][0]) & set(bars["xyz:GBP"][0]))
    idx = {c: dict(zip(*bars[c])) for c in DXY_W}
    basket = [sum(sign * w * idx[c][t] for c, (sign, w) in DXY_W.items()) for t in common]
    grid = list(range(t0 - t0 % BAR, t1, BAR))
    results = {}
    for chg_len in CHG_LENS:
        zs = {
            "rates": {t: -z for t, z in z_series(*bars["xyz:TLT"], chg_len).items()},
            "dollar": z_series(common, basket, chg_len),
            "oil": z_series(*bars["xyz:CL"], chg_len),
        }
        keys = {k: sorted(v) for k, v in zs.items()}
        ptr = {k: 0 for k in zs}
        score, ema, live_counts = {}, None, collections.Counter()
        alpha = 2.0 / (SMOOTH + 1)
        for g in grid:  # score "as of the close of grid bar g": component bars with open time <= g
            vals = []
            for k in zs:
                ks = keys[k]
                while ptr[k] + 1 < len(ks) and ks[ptr[k] + 1] <= g:
                    ptr[k] += 1
                if ks and ks[ptr[k]] <= g and (g - ks[ptr[k]]) <= STALE_MULT * BAR:
                    vals.append(zs[k][ks[ptr[k]]])
            raw = (sum(vals) / len(vals)) * (100.0 / Z_CAP) if vals else None
            if raw is not None:
                ema = raw if ema is None else ema + alpha * (raw - ema)
            live_counts[len(vals)] += 1
            score[g] = (ema if raw is not None else None, len(vals))

        def label_at(t: int):
            g = (t // BAR) * BAR - BAR  # last grid bar CLOSED at or before t
            s, n = score.get(g, (None, 0))
            if s is None:
                return "offline", None, n
            return ("hot" if s >= HOT else "cold" if s <= COLD else "quiet"), s, n

        window = [
            g for g in grid if min(x["t"] for x in trades) <= g <= max(x["t"] for x in trades)
        ]
        dist = collections.Counter(label_at(g + BAR)[0] for g in window)
        print("\n" + "=" * 100)
        print(
            f"CHG_LEN = {chg_len} ({chg_len * 15} min change), z over {Z_LEN} bars, EMA({SMOOTH}), thresholds +-{HOT:.0f}"
        )
        print(
            "  label share of all 15m bars in the trade window: "
            + ", ".join(f"{k} {v / len(window):.1%}" for k, v in dist.most_common())
        )
        print(
            "  live components per bar: "
            + ", ".join(
                f"{k} live: {v / len(grid):.1%}"
                for k, v in sorted(live_counts.items(), reverse=True)
            )
        )
        for x in trades:
            lab, s, n = label_at(x["t"])
            x["label"], x["score"], x["live"] = lab, s, n
            x["weekend"] = in_weekend_window(x["t"])
            if x["symbol"] in ENERGY:
                x["align"] = "unmapped"
            elif lab in ("offline", "quiet"):
                x["align"] = lab
            else:
                headwind_for_longs = lab == "hot"
                x["align"] = "against" if (x["dir"] == "up") == headwind_for_longs else "with"
        print(
            f"  trades with a defined label: {sum(1 for x in trades if x['label'] != 'offline')} of {len(trades)}; in the weekend oracle window: {sum(1 for x in trades if x['weekend'])}"
        )
        r1 = table(
            "By alignment with the Tightening label",
            {
                k: [x for x in trades if x["align"] == k]
                for k in ("with", "quiet", "against", "unmapped", "offline")
            },
        )
        r2 = table(
            "By label x trade direction",
            {
                f"{lab} | {d}": [
                    x
                    for x in trades
                    if x["label"] == lab and x["dir"] == d and x["align"] != "unmapped"
                ]
                for lab in ("hot", "quiet", "cold")
                for d in ("up", "down")
            },
        )
        wk = [x for x in trades if not x["weekend"]]
        r3 = table(
            "By alignment, weekday tape only (weekend oracle window excluded)",
            {k: [x for x in wk if x["align"] == k] for k in ("with", "quiet", "against")},
        )
        results[f"chg_len_{chg_len}"] = dict(
            label_share=dict(dist), alignment=r1, label_x_dir=r2, alignment_weekday=r3
        )
    json.dump(results, open(HERE / "venue_mrc.json", "w"), indent=1)


if __name__ == "__main__":
    main()
