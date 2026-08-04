"""TVB-18 week-end parity: twin end-state dump at the archive tip.

Replays a symbol from the week boundary to the last confirmed archived 5m
bar under the chosen config and prints the state the live v6.1 chart table
shows at read time: position, D/W/M gates, per-pool alive counts,
evict-alive counters, and the nearest alive lines around the last close.
Read-only; never touches the frozen week-1 record (events_week1.jsonl /
scoreboard_week1.md stay owned by replay.py).

    uv run python -m analysis.paper.parity_state --config control
    uv run python -m analysis.paper.parity_state --symbols xyz:DRAM --config variant

Used for the TVB-18 week-end parity pass (fresh-mount chart reads vs twin
tip state; see docs/experiments/tvb15_paper_week1_protocol.md).
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from analysis.paper.engine import Twin, TwinConfig
from analysis.paper.replay import load_rows

REPO = Path(__file__).resolve().parents[2]
WEEK_START = int(datetime.fromisoformat("2026-07-20").replace(tzinfo=timezone.utc).timestamp())


def fmt_ts(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%m-%d %H:%M")


def run(entry: dict, arm_s: int, drop_12h: bool, bars_dir: Path) -> None:
    coin = entry["name"]
    tick = float(entry["tv_mintick"])
    rows_5m = load_rows(coin, "5m", bars_dir)
    rows_1h = load_rows(coin, "1h", bars_dir)
    rows_1d = load_rows(coin, "1d", bars_dir)
    twin = Twin(TwinConfig(symbol=coin, mintick=tick, arm_tf_s=arm_s))
    if drop_12h:
        twin.pools = [p for p in twin.pools if p.name != "12h"]
    pre_1h = [r for r in rows_1h if r[0] < WEEK_START]
    for name in ("12h", "D", "W"):
        if any(p.name == name for p in twin.pools):
            twin.warm_pool(name, pre_1h)
    twin.warm_pool("M", [r for r in rows_1d if r[0] < WEEK_START])
    twin.seed_gates(pre_1h)
    seed_win = [r for r in rows_5m if WEEK_START - arm_s <= r[0] < WEEK_START]
    if seed_win:
        twin.seed_arm(max(r[2] for r in seed_win), min(r[3] for r in seed_win))
    rows = [r for r in rows_5m if r[0] >= WEEK_START]
    for r in rows:
        twin.replay_bar(int(r[0]), r[1], r[2], r[3], r[4], bar_s=300)
    t, c = int(rows[-1][0]), rows[-1][4]
    cfg_txt = "1H, D/W/M (variant)" if drop_12h else "15m, 12h/D/W/M (control)"
    print(f"\n=== {coin}  config: {cfg_txt}")
    print(f"last confirmed 5m bar: {fmt_ts(t)} UTC  close={c:g}")
    if twin.pos == 0:
        print("position: FLAT")
    else:
        d = "LONG" if twin.pos == 1 else "SHORT"
        upnl = (1 if twin.pos == 1 else -1) * (c - twin.entry_px) / twin.entry_px * 100
        print(f"position: {d} @{twin.entry_px:g} since {fmt_ts(twin.entry_ts)} ({upnl:+.2f}%)")
    gates = []
    for name in ("D", "W", "M"):
        o = twin.gate_open.get(name)
        if o is None:
            gates.append(f"{name}=?")
        else:
            d = "up" if c > o else ("down" if c < o else "flat")
            gates.append(f"{name}={d}({o:g})")
    print("gates: " + "  ".join(gates))
    lines = []
    for p in twin.pools:
        n_alive = 0
        for f in p.formations:
            for side_name, side in (("lo", f.lo), ("up", f.up)):
                if side.state == "alive":
                    n_alive += 1
                    lines.append((side.val(t), p.name, f.N, side_name))
        print(f"pool {p.name:3}: alive={n_alive:2}  evict_alive={p.evict_alive}")
    above = sorted(x for x in lines if x[0] >= c)[:4]
    below = sorted((x for x in lines if x[0] < c), reverse=True)[:4]
    for v, pn, n, sn in above[::-1]:
        print(f"   above: {v:<12.6g} ({pn} N={n} {sn})")
    print(f"   PRICE: {c:g}")
    for v, pn, n, sn in below:
        print(f"   below: {v:<12.6g} ({pn} N={n} {sn})")


def main() -> None:
    ap = argparse.ArgumentParser(description="Twin end-state dump for parity reads")
    ap.add_argument("--symbols", default="xyz:DRAM,xyz:TSLA,xyz:GOOGL")
    ap.add_argument("--config", choices=["control", "variant"], default="control")
    ap.add_argument("--roster", default=str(REPO / "analysis/paper/roster_week1.json"))
    ap.add_argument("--bars-dir", default=str(REPO / "analysis" / "paper" / "bars"))
    args = ap.parse_args()
    roster = json.loads(Path(args.roster).read_text())
    entries = {e["name"]: e for e in roster["symbols"]}
    arm_s, drop = (900, False) if args.config == "control" else (3600, True)
    for s in args.symbols.split(","):
        run(entries[s], arm_s, drop, Path(args.bars_dir))


if __name__ == "__main__":
    main()
