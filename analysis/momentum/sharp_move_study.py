"""Sharp-move event study on Hyperliquid perps: do sharp bars CONTINUE or REVERT? Characterization.

A-PRIORI DEFINITIONS (fixed here BEFORE any number was read, 2026-10-03, TVB-36)

Event definition = tv_indicators/pine/sharp_move_detector_v2.pine defaults, ATR path only:
  ratio = true_range / ATR(14)[1]  (Wilder RMA; the PRIOR bar's ATR, as the script's v2 fix);
  tiers: mild [2, 3), strong [3, 4), extreme >= 4;
  mild and strong additionally require volume >= 1.5 x SMA(20) of volume; extreme has no volume
  condition; direction = sign(close - open) of the event bar (zero-body bars dropped).
  The detector's optional %-move path (2% over 3 bars) is NOT used: its own tooltip calls 2% noise
  on crypto perps and no replacement threshold is chosen here.

Universe: the 40 main-dex perps with the highest median 24h volume in the September decision
  journal (the bot's own universe; selected on volume, never on returns). List in top40_main.json.
Bars: 1h (up to 5000 bars, about 208 days) and 15m (up to 5000 bars, about 52 days), public API.

Outcome: signed forward return from the event bar's CLOSE to the close h bars later,
  h in {1, 4, 12, 24}, signed by the event direction (+ = continuation, - = reversion), in percent.
  Entry at the event close is the earliest price a bar-close detector can act on.
Baseline: the same statistic over ALL bars signed by their own direction.

A-priori splits (four, no others):
  1. tier (mild / strong / extreme);
  2. compression before: Bollinger(20, 2) bandwidth on the bar BEFORE the event in the bottom
     quartile of its own trailing 100 bars (charter S5: compression-then-expansion);
  3. band break: the event bar closes beyond the Bollinger(20, 2) band in the move's direction;
  4. STRAT level: the event bar's close is beyond the PRIOR UTC day's high (up events) / low (down
     events) -- a new extreme beyond a prior pivot, which the methodology calls exhaustion RISK
     (strat-methodology 5.1) -- versus still inside the prior day's range. Strict comparison (R10).

Clustering: sharp bars cluster across coins in the same bar. Every mean is reported per event AND
  per event-bar (events sharing a timestamp averaged first), with a t-stat on the per-bar series.
Nothing is tuned and nothing here is a strategy. One venue, one period, costs excluded.

POST-HOC ADDENDUM (added 2026-10-03 AFTER the first read; NOT in the a-priori list, labeled so):
  the first read showed price rising after sharp bars in BOTH directions, which a direction-signed
  statistic cannot tell apart from drift. Three cuts were added for interpretation only:
  (a) RAW price-direction forward returns after up events, after down events, and for all bars
      (the unconditional drift benchmark);
  (b) direction x band-break, because split 3 may be confounded with direction;
  (c) calendar month, because the owner's observation was about recent tape.
  Overlapping horizons are serially correlated: the h=24 t-stats are overstated.
"""

from __future__ import annotations

import collections
import json
import math
import time
from pathlib import Path

import httpx

HERE = Path(__file__).parent
CACHE = HERE / "data"
CACHE.mkdir(parents=True, exist_ok=True)
INFO = "https://api.hyperliquid.xyz/info"
IV_MS = {"1h": 3_600_000, "15m": 900_000}
HORIZONS = (1, 4, 12, 24)
ATR_LEN, VOL_LEN, VOL_MULT, BB_LEN, BB_K, BW_LOOK = 14, 20, 1.5, 20, 2.0, 100


def fetch(coin: str, iv: str, end: int) -> list[dict]:
    start = end - 5000 * IV_MS[iv]
    p = CACHE / f"{coin}_{iv}_{end}.json"
    if p.exists():
        return json.load(open(p))
    last = None
    for attempt in range(6):
        try:
            r = httpx.post(
                INFO,
                json={
                    "type": "candleSnapshot",
                    "req": {"coin": coin, "interval": iv, "startTime": start, "endTime": end},
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
    raise RuntimeError(f"candles failed {coin} {iv}: {last}")


def events_for(rows: list[dict], iv: str) -> tuple[list[dict], list[dict]]:
    t = [int(r["t"]) for r in rows]
    o = [float(r["o"]) for r in rows]
    h = [float(r["h"]) for r in rows]
    lo = [float(r["l"]) for r in rows]
    c = [float(r["c"]) for r in rows]
    v = [float(r["v"]) for r in rows]
    n = len(rows)
    tr = [h[0] - lo[0]] + [
        max(h[i] - lo[i], abs(h[i] - c[i - 1]), abs(lo[i] - c[i - 1])) for i in range(1, n)
    ]
    atr = [None] * n
    if n > ATR_LEN:
        atr[ATR_LEN - 1] = sum(tr[:ATR_LEN]) / ATR_LEN
        for i in range(ATR_LEN, n):
            atr[i] = (atr[i - 1] * (ATR_LEN - 1) + tr[i]) / ATR_LEN
    # Bollinger and bandwidth
    mid, up, dn, bw = [None] * n, [None] * n, [None] * n, [None] * n
    for i in range(BB_LEN - 1, n):
        win = c[i - BB_LEN + 1 : i + 1]
        m = sum(win) / BB_LEN
        s = math.sqrt(sum((x - m) ** 2 for x in win) / BB_LEN)
        mid[i], up[i], dn[i] = m, m + BB_K * s, m - BB_K * s
        bw[i] = (up[i] - dn[i]) / m if m > 0 else None
    # prior UTC day high/low
    day = [ti // 86_400_000 for ti in t]
    dh, dl = {}, {}
    for i in range(n):
        dh[day[i]] = max(dh.get(day[i], h[i]), h[i])
        dl[day[i]] = min(dl.get(day[i], lo[i]), lo[i])
    first_day = day[0]
    ev, base = [], []
    start = max(ATR_LEN + 1, BB_LEN + BW_LOOK, VOL_LEN)
    for i in range(start, n - max(HORIZONS)):
        body = c[i] - o[i]
        if body == 0 or atr[i - 1] is None or atr[i - 1] <= 0:
            continue
        sign = 1.0 if body > 0 else -1.0
        fwd = {hz: sign * (c[i + hz] / c[i] - 1.0) * 100.0 for hz in HORIZONS}
        base.append(dict(t=t[i], fwd=fwd, sign=sign))
        ratio = tr[i] / atr[i - 1]
        if ratio < 2.0:
            continue
        vsma = sum(v[i - VOL_LEN + 1 : i + 1]) / VOL_LEN
        vol_ok = vsma > 0 and v[i] >= VOL_MULT * vsma
        tier = "extreme" if ratio >= 4.0 else "strong" if ratio >= 3.0 else "mild"
        if tier != "extreme" and not vol_ok:
            continue
        prior_bw = bw[i - 1]
        hist = [x for x in bw[i - BW_LOOK : i] if x is not None]
        compressed = (
            prior_bw is not None
            and len(hist) >= BW_LOOK // 2
            and sum(1 for x in hist if x <= prior_bw) / len(hist) <= 0.25
        )
        band_break = (c[i] > up[i]) if sign > 0 else (c[i] < dn[i])
        pd = day[i] - 1
        beyond = None
        if pd in dh and pd > first_day:  # the first day in the file is partial
            beyond = (c[i] > dh[pd]) if sign > 0 else (c[i] < dl[pd])
        ev.append(
            dict(
                t=t[i],
                tier=tier,
                ratio=ratio,
                sign=sign,
                fwd=fwd,
                compressed=compressed,
                band_break=band_break,
                beyond_pd=beyond,
                atr_pct=atr[i - 1] / c[i - 1] * 100.0,
            )
        )
    return ev, base


def stats(rows: list[dict]) -> dict:
    out = {"n": len(rows), "bars": len({r["t"] for r in rows})}
    for hz in HORIZONS:
        vals = [r["fwd"][hz] for r in rows]
        if not vals:
            out[hz] = None
            continue
        by_t = collections.defaultdict(list)
        for r in rows:
            by_t[r["t"]].append(r["fwd"][hz])
        per_bar = [sum(x) / len(x) for x in by_t.values()]
        m = sum(per_bar) / len(per_bar)
        sd = (
            math.sqrt(sum((x - m) ** 2 for x in per_bar) / (len(per_bar) - 1))
            if len(per_bar) > 1
            else float("nan")
        )
        tstat = m / (sd / math.sqrt(len(per_bar))) if sd and sd > 0 else float("nan")
        out[hz] = dict(
            mean_event=sum(vals) / len(vals),
            mean_bar=m,
            t=tstat,
            cont=sum(1 for x in vals if x > 0) / len(vals),
        )
    return out


def line(name: str, s: dict) -> str:
    cells = []
    for hz in HORIZONS:
        x = s[hz]
        cells.append(
            "        --        "
            if x is None
            else f"{x['mean_event']:+6.2f}% ({x['t']:+5.1f}) {x['cont']:4.0%}"
        )
    return f"  {name:30}{s['n']:>7}{s['bars']:>7}  " + " | ".join(cells)


def main() -> None:
    coins = json.load(open(HERE / "top40_main.json"))
    end = int(json.load(open(HERE / "as_of.json"))["end_ms"])
    results = {}
    for iv in ("1h", "15m"):
        ev, base = [], []
        got = 0
        for coin in coins:
            rows = fetch(coin, iv, end)
            if len(rows) < 500:
                continue
            got += 1
            e, b = events_for(rows, iv)
            for x in e:
                x["coin"] = coin
            ev += e
            base += b
        span_days = (max(x["t"] for x in base) - min(x["t"] for x in base)) / 86_400_000
        print("\n" + "=" * 132)
        print(
            f"{iv} bars | {got} coins | {span_days:.0f} days | {len(base):,} bars in the baseline | {len(ev):,} sharp-move events"
        )
        print(
            "  cell: mean signed forward return per event (t-stat on per-bar means) and share of events that continued"
        )
        print(
            f"  {'':30}{'events':>7}{'bars':>7}  "
            + " | ".join(f"{'h=' + str(hz) + ' bars':^18}" for hz in HORIZONS)
        )
        res = {"baseline (all bars)": stats(base)}
        print(line("baseline (all bars)", res["baseline (all bars)"]))
        groups = collections.OrderedDict()
        groups["ALL sharp events"] = ev
        for tier in ("mild", "strong", "extreme"):
            groups[f"tier {tier}"] = [x for x in ev if x["tier"] == tier]
        groups["up events"] = [x for x in ev if x["sign"] > 0]
        groups["down events"] = [x for x in ev if x["sign"] < 0]
        groups["compression before: yes"] = [x for x in ev if x["compressed"]]
        groups["compression before: no"] = [x for x in ev if not x["compressed"]]
        groups["closes beyond band: yes"] = [x for x in ev if x["band_break"]]
        groups["closes beyond band: no"] = [x for x in ev if not x["band_break"]]
        groups["beyond prior-day H/L: yes"] = [x for x in ev if x["beyond_pd"] is True]
        groups["beyond prior-day H/L: no"] = [x for x in ev if x["beyond_pd"] is False]
        for name, rows in groups.items():
            res[name] = stats(rows)
            print(line(name, res[name]))
        # POST-HOC ADDENDUM (see the module docstring): not in the a-priori list.
        def _raw(rows):
            return [dict(t=r["t"], fwd={hz: r["fwd"][hz] * r["sign"] for hz in HORIZONS}) for r in rows]

        print("  -- post-hoc: RAW price-direction forward returns (drift vs momentum) --")
        for name, rows in (("drift: all bars, raw", _raw(base)), ("after sharp UP bars, raw", _raw([x for x in ev if x["sign"] > 0])), ("after sharp DOWN bars, raw", _raw([x for x in ev if x["sign"] < 0]))):
            res["posthoc " + name] = stats(rows)
            print(line(name, res["posthoc " + name]))
        print("  -- post-hoc: direction x band break (signed by event direction) --")
        for d, dn in ((1.0, "up"), (-1.0, "down")):
            for bb in (True, False):
                name = f"{dn} x beyond band {'yes' if bb else 'no'}"
                res["posthoc " + name] = stats([x for x in ev if x["sign"] == d and x["band_break"] == bb])
                print(line(name, res["posthoc " + name]))
        print("  -- post-hoc: by calendar month, all sharp events (signed by event direction) --")
        bym = collections.defaultdict(list)
        for x in ev:
            bym[time.strftime("%Y-%m", time.gmtime(x["t"] / 1000))].append(x)
        for m in sorted(bym):
            res["posthoc month " + m] = stats(bym[m])
            print(line("month " + m, res["posthoc month " + m]))
        med_atr = sorted(x["atr_pct"] for x in ev)[len(ev) // 2] if ev else float("nan")
        print(f"  median ATR[1] at events: {med_atr:.2f}% of price; taker round trip about 0.086%")
        results[iv] = {k: {str(a): b for a, b in v.items()} for k, v in res.items()}
        results[iv]["_meta"] = dict(
            coins=got,
            days=span_days,
            baseline_bars=len(base),
            events=len(ev),
            median_atr_pct=med_atr,
        )
    json.dump(results, open(HERE / "sharp_move_study.json", "w"), indent=1)


if __name__ == "__main__":
    main()
