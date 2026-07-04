"""Perp funding cost model over committed tv_dump trade lists.

Question (TVB-6 carry): funding is the one cost leverage does not shrink, and
the TV backtest charges NONE of it. This module joins the venue's hourly
funding history (Hyperliquid public info API, type=fundingHistory) against a
committed tv_dump trade list and reports the funding-adjusted compounded
return next to the recorded one.

Model: at 100%-of-equity 1x sizing, entry notional ~= equity, so a funding
event at rate r while holding a LONG costs ~r of equity (positive rate: longs
pay shorts); a SHORT receives +r (pays when r < 0). Per-trade funding fraction
f = signed sum of hourly rates over events with et < t <= xt; adjusted
compounding = product(1 + pp - f) over closed trades. Approximations, stated
honestly: notional is marked at entry (funding actually accrues on mark price
each hour) and n ratio notional/equity is taken as exactly 1.0; at 1x both
errors are second-order versus the rate sums themselves.

Usage:
    uv run python analysis/funding_model.py fetch --coin xyz:MSTR \\
        --start 2025-12-02T00:00:00Z --out analysis/reference/tvb7_funding_xyzMSTR.json
    uv run python analysis/funding_model.py apply <dump.json> \\
        --funding analysis/reference/tvb7_funding_xyzMSTR.json
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from bisect import bisect_right
from datetime import datetime, timezone

API_URL = "https://api.hyperliquid.xyz/info"
MAX_PAGES = 200  # safety backstop: 200 * 500 hourly records ~= 11 years


def fetch_funding_history(
    coin: str, start_ms: int, end_ms: int | None = None, sleep_s: float = 0.25
) -> list[dict]:
    """Paginated fundingHistory pull -> [{time, fundingRate, premium}, ...].

    HL serves <=500 records per request; the cursor advances past the last
    record's timestamp. Stops on an empty page, a non-advancing cursor, or
    end_ms.
    """
    out: list[dict] = []
    cursor = start_ms
    for _ in range(MAX_PAGES):
        body = json.dumps({"type": "fundingHistory", "coin": coin, "startTime": cursor}).encode()
        req = urllib.request.Request(
            API_URL, data=body, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            page = json.load(resp)
        if not page:
            break
        for rec in page:
            t = int(rec["time"])
            if end_ms is not None and t > end_ms:
                return out
            out.append(
                {
                    "time": t,
                    "fundingRate": float(rec["fundingRate"]),
                    "premium": float(rec.get("premium", 0.0)),
                }
            )
        new_cursor = int(page[-1]["time"]) + 1
        if new_cursor <= cursor:
            break
        cursor = new_cursor
        time.sleep(sleep_s)
    return out


def trade_funding(trades: list[dict], events: list[dict]) -> list[dict]:
    """Per-trade signed funding fraction from hourly events in (et, xt].

    trades: dump list rows {et, xt, dir, pp, open}; open/malformed rows are
    skipped. events: [{time, fundingRate}] sorted by time. Long cost = +sum of
    rates in the holding window; short cost = -sum (negative cost = credit).
    """
    times = [e["time"] for e in events]
    rates = [e["fundingRate"] for e in events]
    out = []
    for t in trades:
        if t.get("open"):
            continue
        et, xt, d, pp = t.get("et"), t.get("xt"), t.get("dir"), t.get("pp")
        if et is None or xt is None or pp is None or d not in ("le", "se"):
            continue
        lo = bisect_right(times, et)
        hi = bisect_right(times, xt)
        rate_sum = sum(rates[lo:hi])
        fund = rate_sum if d == "le" else -rate_sum
        out.append({"et": et, "xt": xt, "dir": d, "pp": pp, "fund": fund, "n_events": hi - lo})
    return out


def summarize(rows: list[dict]) -> dict:
    """Compounded return with and without the funding adjustment."""
    base = 1.0
    adj = 1.0
    fund_total = 0.0
    n_hit = 0
    for r in rows:
        base *= 1.0 + r["pp"]
        adj *= 1.0 + r["pp"] - r["fund"]
        fund_total += r["fund"]
        if r["n_events"]:
            n_hit += 1
    return {
        "n": len(rows),
        "n_with_events": n_hit,
        "base_ret": base - 1.0,
        "adj_ret": adj - 1.0,
        "fund_total_frac": fund_total,
    }


def _iso_to_ms(s: str) -> int:
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="pull funding history to a JSON file")
    f.add_argument("--coin", default="xyz:MSTR")
    f.add_argument("--start", required=True, help="ISO UTC start")
    f.add_argument("--end", help="ISO UTC end (default: now)")
    f.add_argument("--out", required=True)

    a = sub.add_parser("apply", help="funding-adjust a committed dump")
    a.add_argument("dump")
    a.add_argument("--funding", required=True, help="fetch output JSON")
    args = ap.parse_args()

    if args.cmd == "fetch":
        start_ms = _iso_to_ms(args.start)
        end_ms = _iso_to_ms(args.end) if args.end else None
        events = fetch_funding_history(args.coin, start_ms, end_ms)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump({"coin": args.coin, "start_ms": start_ms, "events": events}, fh)
        if events:
            rs = sorted(e["fundingRate"] for e in events)
            first = datetime.fromtimestamp(events[0]["time"] / 1000, tz=timezone.utc)
            last = datetime.fromtimestamp(events[-1]["time"] / 1000, tz=timezone.utc)
            print(
                f"{args.coin}: {len(events)} hourly events "
                f"{first.isoformat()} -> {last.isoformat()}"
            )
            print(
                f"  rate/hr: median {rs[len(rs) // 2]:+.3e}  min {rs[0]:+.3e}  "
                f"max {rs[-1]:+.3e}  mean {sum(rs) / len(rs):+.3e}"
            )
        print(f"-> {args.out}")
        return

    with open(args.dump, encoding="utf-8") as fh:
        dump = json.load(fh)
    with open(args.funding, encoding="utf-8") as fh:
        funding = json.load(fh)
    events = sorted(funding["events"], key=lambda e: e["time"])
    rows = trade_funding(dump.get("list", []), events)
    s = summarize(rows)
    print(f"{args.dump} vs {funding.get('coin')} funding ({len(events)} events)")
    print(f"  n={s['n']} closed trades, {s['n_with_events']} held through >=1 funding event")
    print(
        f"  compounded: recorded {s['base_ret'] * 100:+.2f}%  "
        f"funding-adjusted {s['adj_ret'] * 100:+.2f}%  "
        f"(delta {100 * (s['adj_ret'] - s['base_ret']):+.2f}pp)"
    )
    print(f"  sum of per-trade funding fractions: {s['fund_total_frac'] * 100:+.3f}pp")


if __name__ == "__main__":
    main()
