"""Index continuity as a regime label on the September strategy-chosen book -- characterization.

A-PRIORI DEFINITIONS (fixed here BEFORE any number was read, 2026-10-03, TVB-36)

The charter's slow layer (S3.3): the same continuity measurement applied to a REFERENCE instead of
the traded coin. No macro data, no human input; both references trade 24/7 on the bot's own feed.

Reference per trade:
  main-dex crypto coins                     -> BTC
  xyz equity / ETF / index / intl-equity    -> xyz:XYZ100 (the venue's Nasdaq-100 perp)
  xyz commodity, FX and energy-linked names -> unmapped (reported separately, never aligned)

Bias per timeframe (strat-methodology 4.1): reference price vs that timeframe's OWN OPEN.
  day = 00:00 UTC, week = Monday 00:00 UTC, month = the 1st 00:00 UTC (the venue's candle
  boundaries, the same opens the scanner's dots use). Price = the last 15m close at or before the
  entry instant. Equality reads as no bias (mixed).

Regime labels, two declared variants and no others:
  DWM = day, week and month all green -> up; all red -> down; else mixed  (charter M/W/D layer)
  WM  = week and month only, because the executor's BTC drift veto already enforces the DAY on
        crypto entries, so D carries no information for that universe.
Alignment per trade: with (trade direction == regime) / against / mixed / unmapped.

Coupling (skill 4.5): on a Monday the week and day share an open, and on the 1st all three do; those
are one observation, not three. Trades entered on such days are counted and flagged, not removed.

Outcomes: analysis/parallax results (116 lost signals, bracket-only; 24 filled, actual). Wins and
the random-walk expectation use bracket-resolved trades; R sums use every trade.

CHARACTERIZATION ONLY: one month, about 140 trades, and the references' month had ONE dominant
state. This shows where the month's losses sat against the label; it cannot validate a filter.
"""

from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

HERE = Path(__file__).parent
PARALLAX = HERE.parent / "parallax" / "results"
CACHE = HERE / "data" / "index_continuity"
CACHE.mkdir(parents=True, exist_ok=True)
INFO = "https://api.hyperliquid.xyz/info"
BAR = 900_000
UNMAPPED = {
    "xyz:CL",
    "xyz:BRENTOIL",
    "xyz:NATGAS",
    "xyz:HO",
    "xyz:GOLD",
    "xyz:SILVER",
    "xyz:COPPER",
    "xyz:PLATINUM",
    "xyz:PALLADIUM",
    "xyz:JPY",
    "xyz:EUR",
    "xyz:GBP",
    "xyz:XLE",
    "xyz:CVX",
    "xyz:URNM",
    "xyz:USAR",
}


def fetch(coin: str, iv: str, start: int, end: int) -> list[dict]:
    p = CACHE / f"{coin.replace(':', '_')}_{iv}_{start}_{end}.json"
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


def load_trades() -> list[dict]:
    lb = json.load(open(PARALLAX / "lostbook.json"))
    mm = json.load(open(PARALLAX / "mfe_mae.json"))
    trades = []
    for r in lb["lost"]:
        if r["outcome"] != "no_data":
            trades.append(
                dict(
                    symbol=r["symbol"],
                    dir=r["dir"],
                    t=int(r["entry_ts"]),
                    r=float(r["r"]),
                    rr=r.get("rr"),
                    resolved=r["outcome"] in ("stop", "target"),
                    win=r["outcome"] == "target",
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
                )
            )
    return trades


def opens_at(daily: dict[int, float], t: int) -> tuple[float | None, float | None, float | None]:
    d = datetime.fromtimestamp(t / 1000, timezone.utc)
    day0 = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() * 1000)
    week0 = day0 - d.weekday() * 86_400_000
    month0 = int(datetime(d.year, d.month, 1, tzinfo=timezone.utc).timestamp() * 1000)
    return daily.get(day0), daily.get(week0), daily.get(month0)


def table(title: str, groups: dict[str, list[dict]]) -> dict:
    print(f"\n  {title}")
    print(
        f"  {'cell':26}{'n':>5}{'resolved':>10}{'wins':>6}{'random exp':>12}{'z':>7}{'sum R':>9}{'R/trade':>9}"
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
            f"  {name:26}{len(rows):>5}{len(res):>10}{wins:>6}{exp:>12.1f}{z:>+7.2f}{sr:>+9.2f}{(sr / len(rows) if rows else 0):>+9.3f}"
        )
        out[name] = dict(n=len(rows), resolved=len(res), wins=wins, expected=exp, z=z, sum_r=sr)
    return out


def main() -> None:
    trades = load_trades()
    t0 = min(x["t"] for x in trades) - 45 * 86_400_000
    t1 = max(x["t"] for x in trades) + BAR
    refs = {}
    for ref in ("BTC", "xyz:XYZ100"):
        daily = {int(r["t"]): float(r["o"]) for r in fetch(ref, "1d", t0, t1)}
        m15 = fetch(ref, "15m", min(x["t"] for x in trades) - 4 * BAR, t1)
        refs[ref] = (daily, [int(r["t"]) for r in m15], [float(r["c"]) for r in m15])
        print(f"{ref:12} daily opens {len(daily)}, 15m bars {len(m15)}")
    out = {}
    for x in trades:
        if x["symbol"] in UNMAPPED:
            x["ref"] = None
            x["dwm"] = x["wm"] = "unmapped"
            continue
        x["ref"] = "xyz:XYZ100" if x["symbol"].startswith("xyz:") else "BTC"
        daily, ts, cs = refs[x["ref"]]
        g = (x["t"] // BAR) * BAR - BAR  # last 15m bar CLOSED at or before entry
        px = next((c for tt, c in zip(reversed(ts), reversed(cs)) if tt <= g), None)
        d_o, w_o, m_o = opens_at(daily, x["t"])

        def bias(o):
            return None if (px is None or o is None or px == o) else ("up" if px > o else "down")

        b = [bias(d_o), bias(w_o), bias(m_o)]
        x["bias"] = b
        x["dwm"] = b[0] if (b[0] and b[0] == b[1] == b[2]) else "mixed"
        x["wm"] = b[1] if (b[1] and b[1] == b[2]) else "mixed"
        dt = datetime.fromtimestamp(x["t"] / 1000, timezone.utc)
        x["coupled"] = dt.weekday() == 0 or dt.day == 1
    mapped = [x for x in trades if x["ref"]]
    print(
        f"\ntrades {len(trades)} | mapped {len(mapped)} (BTC ref {sum(1 for x in mapped if x['ref'] == 'BTC')}, XYZ100 ref {sum(1 for x in mapped if x['ref'] != 'BTC')}) | unmapped {len(trades) - len(mapped)} | entered on a coupled day (Monday or the 1st) {sum(1 for x in mapped if x['coupled'])}"
    )
    for key, name in (("dwm", "DWM (day+week+month)"), ("wm", "WM (week+month)")):
        print("\n" + "=" * 100)
        print(f"Regime variant {name}")
        from collections import Counter

        print("  reference regime at entry:", dict(Counter(x[key] for x in mapped)))

        def align(x):
            return "mixed" if x[key] == "mixed" else ("with" if x[key] == x["dir"] else "against")

        r1 = table(
            "By alignment (trade direction vs reference regime)",
            {k: [x for x in mapped if align(x) == k] for k in ("with", "mixed", "against")},
        )
        r2 = table(
            "By reference regime x trade direction",
            {
                f"ref {reg} | trade {d}": [x for x in mapped if x[key] == reg and x["dir"] == d]
                for reg in ("up", "mixed", "down")
                for d in ("up", "down")
            },
        )
        r3 = table(
            "Crypto only (BTC reference), by alignment",
            {
                k: [x for x in mapped if x["ref"] == "BTC" and align(x) == k]
                for k in ("with", "mixed", "against")
            },
        )
        out[key] = dict(alignment=r1, regime_x_dir=r2, crypto_alignment=r3)
    json.dump(out, open(HERE / "index_continuity.json", "w"), indent=1)


if __name__ == "__main__":
    main()
