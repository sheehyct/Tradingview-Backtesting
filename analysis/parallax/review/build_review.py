"""Build the data behind the September trade review page (a visual aid, not an analysis).

Reads the committed results of analysis/parallax (lostbook.json, mfe_mae.json, trades_*.json),
fetches public Hyperliquid candles per coin at 15m / 1h / 4h / 1d, and writes:

  ../exports/review/data/<coin>.json   candles per interval, [t_sec, o, h, l, c]
  ../exports/review/trades.json        one row per trade (the page's index)
  ../exports/review/september-trade-review.html   the template with the index inlined

Everything under ../exports is gitignored (owner-local, regenerable). Nothing here is tuned.

One derived tag is computed because it is the thing the owner wants to SEE: for a trade that was
stopped (or exited by the bot), did price touch the ORIGINAL target within 72 hours afterwards.
It is a pointer to charts worth opening, measured on 15m candles; it is not a verdict.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import httpx

HERE = Path(__file__).parent
RES = HERE.parent / "results"
OUT = HERE.parent / "exports" / "review"
DATA = OUT / "data"
CACHE = OUT / "cache"
for d in (DATA, CACHE):
    d.mkdir(parents=True, exist_ok=True)
INFO = "https://api.hyperliquid.xyz/info"
IV_MS = {"15m": 900_000, "1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000}
DAY = 86_400_000
PRE = {"15m": 2 * DAY, "1h": 6 * DAY, "4h": 25 * DAY, "1d": 150 * DAY}
POST = {"15m": 4 * DAY, "1h": 8 * DAY, "4h": 12 * DAY, "1d": 20 * DAY}
LATER_MS = 72 * 3_600_000
ACCOUNT = {"v1_STRAT": "First run", "v2_pilot": "Pilot", "prop_test": "Prop test"}
WHY_LOST = (
    ("Funding/data coverage", "Account was blocked after a missed funding check"),
    ("Execution admission", "Price data was not ready in time"),
    ("At execution", "Order arrived after the 15-second window"),
    ("HIP-3 source transition", "Order arrived after the 15-second window"),
    ("IOC expired", "Order expired before a price was available"),
    ("cancelled", "Order was cancelled"),
)


def fetch(coin: str, iv: str, start: int, end: int) -> list:
    p = CACHE / f"{coin.replace(':', '_')}_{iv}_{start}_{end}.json"
    if p.exists():
        return json.load(open(p))
    last = None
    for attempt in range(7):
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
            time.sleep(0.75)
            return rows
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"candles failed {coin} {iv}: {last}")


def load_trades() -> list[dict]:
    lb = json.load(open(RES / "lostbook.json"))
    mm = json.load(open(RES / "mfe_mae.json"))
    out = []
    for r in lb["lost"]:
        if r["outcome"] == "no_data":
            continue
        why = next(
            (plain for key, plain in WHY_LOST if str(r.get("reason", "")).startswith(key)),
            "Order was not filled",
        )
        outcome = r["outcome"]
        exit_px = r["stop"] if outcome == "stop" else r["target"] if outcome == "target" else None
        out.append(
            dict(
                coin=r["symbol"],
                tf=r["tf"],
                pattern=r["pattern"],
                dir=r["dir"],
                kind=r.get("kind"),
                filled=False,
                seen=[ACCOUNT.get(a, a) for a in r.get("accounts", [])],
                entry_t=int(r["entry_ts"]),
                entry=float(r["entry"]),
                stop=float(r["stop"]),
                target=float(r["target"]) if r.get("target") else None,
                exit_t=int(r["exit_ts"]) if r.get("exit_ts") else None,
                exit=exit_px,
                outcome=outcome,
                r=round(float(r["r"]), 2),
                rr=round(float(r["rr"]), 2) if r.get("rr") else None,
                why=why,
                usd=None,
            )
        )
    for acct, rows in mm.items():
        for r in rows:
            ex = r["exit"]
            outcome = (
                ex if ex in ("stop", "target") else "flip" if ex == "ftfc_flip" else "bot_exit"
            )
            out.append(
                dict(
                    coin=r["coin"],
                    tf=r["tf"],
                    pattern=r["pattern"],
                    dir=r["dir"],
                    kind=None,
                    filled=True,
                    seen=[ACCOUNT.get(acct, acct)],
                    entry_t=int(r["entry_ts"]),
                    entry=float(r["entry_px"]),
                    stop=float(r["stop"]) if r.get("stop") else None,
                    target=float(r["target"]) if r.get("target") else None,
                    exit_t=int(r["exit_ts"]),
                    exit=float(r["exit_px"]),
                    outcome=outcome,
                    r=round(float(r["r"]), 2),
                    rr=round(float(r["rr"]), 2) if r.get("rr") else None,
                    why=None,
                    usd=round(float(r["pnl"]), 2),
                )
            )
    for acct in ("v2_pilot", "prop_test"):  # the two positions still open at export time
        for x in json.load(open(RES / f"trades_{acct}.json")):
            if x.get("open") and "note" not in x and x.get("coin") in ("PYTH", "xyz:CBRS"):
                e, s, t = float(x["entry_px"]), float(x["stop"]), float(x["target"])
                out.append(
                    dict(
                        coin=x["coin"],
                        tf=x["tf"],
                        pattern=x["pattern"],
                        dir=x["dir"],
                        kind=None,
                        filled=True,
                        seen=[ACCOUNT[acct]],
                        entry_t=int(x["entry_ts"]),
                        entry=e,
                        stop=s,
                        target=t,
                        exit_t=None,
                        exit=None,
                        outcome="open",
                        r=None,
                        rr=round(abs(t - e) / abs(e - s), 2),
                        why=None,
                        usd=None,
                    )
                )
    out.sort(key=lambda z: z["entry_t"])
    for i, z in enumerate(out, 1):
        z["id"] = f"t{i:03d}"
    return out


def later(trade: dict, m15: list) -> dict | None:
    """What price did in the 72 h after a stop or a bot exit, on 15m candles."""
    if (
        trade["outcome"] not in ("stop", "flip", "bot_exit")
        or not trade["exit_t"]
        or trade["target"] is None
        or trade["stop"] is None
    ):
        return None
    long = trade["dir"] == "up"
    start, end = trade["exit_t"], trade["exit_t"] + LATER_MS
    seen_last = None
    for c in m15:
        t = int(c["t"])
        if t <= start:
            continue
        if t > end:
            break
        seen_last = t
        hi, lo = float(c["h"]), float(c["l"])
        hit_t = hi >= trade["target"] if long else lo <= trade["target"]
        hit_s = lo <= trade["stop"] if long else hi >= trade["stop"]
        if trade["outcome"] == "stop":
            if hit_t:
                return dict(first="target", hours=round((t - start) / 3.6e6, 1), complete=True)
        elif hit_t or hit_s:
            return dict(
                first="both" if (hit_t and hit_s) else "target" if hit_t else "stop",
                hours=round((t - start) / 3.6e6, 1),
                complete=True,
            )
    complete = seen_last is not None and seen_last >= end - 900_000
    return dict(first="neither", hours=None, complete=complete)


def main() -> None:
    trades = load_trades()
    now = int(time.time() * 1000)
    now -= now % 900_000
    by_coin: dict[str, list[dict]] = {}
    for t in trades:
        by_coin.setdefault(t["coin"], []).append(t)
    total_bytes = 0
    for n, (coin, rows) in enumerate(sorted(by_coin.items()), 1):
        first = min(r["entry_t"] for r in rows)
        last = max((r["exit_t"] or r["entry_t"]) for r in rows)
        pack, m15 = {}, []
        for iv in ("15m", "1h", "4h", "1d"):
            start = first - PRE[iv]
            start -= start % IV_MS[iv]
            end = min(now, last + POST[iv])
            end -= end % 900_000
            raw = fetch(coin, iv, start, end)
            if iv == "15m":
                m15 = raw
            pack[iv] = [
                [int(c["t"]) // 1000, float(c["o"]), float(c["h"]), float(c["l"]), float(c["c"])]
                for c in raw
            ]
        for r in rows:
            r["later"] = later(r, m15)
            r["file"] = coin.replace(":", "_")
        body = json.dumps(pack, separators=(",", ":"))
        (DATA / f"{coin.replace(':', '_')}.json").write_text(body, encoding="utf-8")
        total_bytes += len(body)
        if n % 10 == 0 or n == len(by_coin):
            print(f"  {n}/{len(by_coin)} coins, {total_bytes / 1e6:.1f} MB so far", flush=True)
    for t in trades:
        t["entry_t"] //= 1000
        if t["exit_t"]:
            t["exit_t"] //= 1000
    meta = dict(as_of=now // 1000, trades=len(trades), coins=len(by_coin), later_hours=72)
    (OUT / "trades.json").write_text(
        json.dumps(dict(meta=meta, trades=trades), separators=(",", ":")), encoding="utf-8"
    )
    stopped = [t for t in trades if t["outcome"] == "stop"]
    hit = [t for t in stopped if t["later"] and t["later"]["first"] == "target"]
    print(f"trades {len(trades)} | coins {len(by_coin)} | data {total_bytes / 1e6:.1f} MB")
    print(
        f"stopped {len(stopped)} | reached the original target within 72 h after the stop: {len(hit)}"
    )
    flips = [t for t in trades if t["outcome"] in ("flip", "bot_exit")]
    print("bot exits:", [(t["coin"], t["later"]["first"] if t["later"] else None) for t in flips])
    tpl = HERE / "trade_review.template.html"
    if tpl.exists():
        html = tpl.read_text(encoding="utf-8").replace(
            "/*__TRADES__*/null", json.dumps(dict(meta=meta, trades=trades), separators=(",", ":"))
        )
        (OUT / "september-trade-review.html").write_text(html, encoding="utf-8")
        print("page written:", OUT / "september-trade-review.html", f"{len(html) / 1e3:.0f} KB")


if __name__ == "__main__":
    main()
