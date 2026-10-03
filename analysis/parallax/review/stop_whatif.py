"""What if the stop had been wider, or absent? A what-if on the September book -- characterization.

Question from the owner (2026-10-03): 35 of 88 stopped trades later reached their original target.
How would that have changed the overall return?

Two answers, both computed here:
  1. HINDSIGHT: flip only the stopped trades that later reached target into winners. Not tradable:
     no rule knows in advance which stops come back.
  2. A RULE: apply the same wider stop (or no stop) to EVERY trade and let the ones that never come
     back lose more.

DEFINITIONS (fixed before any number was read):
  - Trades: analysis/parallax/exports/review/trades.json (116 replayed + 26 filled), every trade
    re-simulated bracket-only from its entry on 15m candles so all variants share one engine.
  - Stop multiples: 1.0 (as traded), 1.5, 2, 3, and none. The target never moves.
  - A 15m candle touching both levels counts as the stop. A trade unresolved at the end of the
    data is marked to the last close.
  - R = the ORIGINAL stop distance, with the position size unchanged: a 2x stop loses 2R when hit.
    "Resized" divides by the multiple: the same dollars at risk per stop, so a smaller position.
No value is chosen here. This is a spread to read, not a setting to adopt.
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).parent.parent / "exports" / "review"
MULTS = (1.0, 1.5, 2.0, 3.0, None)


def sim(t: dict, bars: list, k: float | None) -> tuple[str, float]:
    long = t["dir"] == "up"
    risk = abs(t["entry"] - t["stop"])
    stop = None if k is None else (t["entry"] - k * risk if long else t["entry"] + k * risk)
    target = t["target"]
    last = t["entry"]
    for b in bars:
        if b[0] + 900 <= t["entry_t"]:
            continue
        hi, lo, last = b[2], b[3], b[4]
        hit_s = stop is not None and (lo <= stop if long else hi >= stop)
        hit_t = target is not None and (hi >= target if long else lo <= target)
        if hit_s:
            return "stop", -k
        if hit_t:
            return "target", abs(target - t["entry"]) / risk
    move = (last - t["entry"]) if long else (t["entry"] - last)
    return "open", move / risk


def main() -> None:
    d = json.load(open(OUT / "trades.json"))
    trades = [t for t in d["trades"] if t["stop"] is not None]
    cache: dict[str, list] = {}
    recorded = [t for t in trades if t["r"] is not None]
    rec_total = sum(t["r"] for t in recorded)
    print(
        f"As recorded (filled = actual, refused = replay): {len(recorded)} trades, {rec_total:+.1f}R, {rec_total / len(recorded):+.3f}R per trade"
    )
    came_back = [
        t
        for t in trades
        if t["outcome"] == "stop" and t.get("later") and t["later"]["first"] == "target"
    ]
    swing = sum((-t["r"]) + t["rr"] for t in came_back)
    print(
        f"HINDSIGHT: the {len(came_back)} stops that later reached target, counted as winners instead: swing {swing:+.1f}R -> {rec_total + swing:+.1f}R, {(rec_total + swing) / len(recorded):+.3f}R per trade"
    )
    print()
    print(
        f"{'stop':>10}{'trades':>8}{'target':>8}{'stopped':>9}{'open':>6}{'win %':>7}{'total R':>10}{'R/trade':>9}{'resized R':>11}{'worst open':>12}"
    )
    out = {}
    for k in MULTS:
        res = []
        for t in trades:
            bars = cache.setdefault(
                t["file"], json.load(open(OUT / "data" / f"{t['file']}.json"))["15m"]
            )
            res.append(sim(t, bars, k))
        n = len(res)
        tg = sum(1 for o, _ in res if o == "target")
        st = sum(1 for o, _ in res if o == "stop")
        op = [r for o, r in res if o == "open"]
        total = sum(r for _, r in res)
        resized = total / k if k else float("nan")
        resolved = tg + st
        name = "none" if k is None else f"{k:g}x"
        print(
            f"{name:>10}{n:>8}{tg:>8}{st:>9}{len(op):>6}{(tg / resolved * 100 if resolved else 0):>6.0f}%{total:>+10.1f}{total / n:>+9.3f}{resized:>+11.1f}{(min(op) if op else 0):>+12.1f}"
        )
        out[name] = dict(
            trades=n,
            target=tg,
            stopped=st,
            open=len(op),
            total_r=total,
            per_trade=total / n,
            resized_r=None if k is None else resized,
            open_sum=sum(op),
            worst_open=min(op) if op else None,
        )
    json.dump(
        dict(
            recorded=dict(trades=len(recorded), total_r=rec_total),
            hindsight=dict(n=len(came_back), swing=swing),
            variants=out,
        ),
        open(Path(__file__).parent.parent / "results" / "stop_whatif.json", "w"),
        indent=1,
    )


if __name__ == "__main__":
    main()
