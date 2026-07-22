"""TVB-16 config ablation: frozen control vs the user's live variant.

Runs the SAME committed week-1 bars through two twin configurations and prints
a side-by-side comparison. Reads only; never writes the frozen week-1 record
(events_week1.jsonl / scoreboard_week1.md stay owned by replay.py).

    control  = arm 15m, pools 12h/D/W/M      (established/shipped defaults)
    variant  = arm 1H,  pools D/W/M          (12h pool OFF -- user live manual)

The 12h pool drives only EXITS (harvest touch + adverse break) and its lines;
entries come from the D/W/M gate + arm break, so dropping it is a surgical
exit-side change. Both configs share the identical engine and bars, so any
delta is attributable to the two knobs (arm TF + the 12h pool) alone.

    uv run python -m analysis.paper.compare_config --roster analysis/paper/roster_week1.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from analysis.giveback import episode_metrics
from analysis.paper.engine import Twin, TwinConfig
from analysis.paper.replay import load_rows

REPO = Path(__file__).resolve().parents[2]
WEEK_START_DEFAULT = "2026-07-20"
WEEK_DAYS = 7

CONFIGS = {
    "control (15m, 12h/D/W/M)": {"arm_s": 900, "drop_12h": False},
    "variant (1H, D/W/M)": {"arm_s": 3600, "drop_12h": True},
}


def replay_cfg(entry, week_start, week_end, bars_dir, arm_s, drop_12h):
    """Replay one symbol under one config. Returns (events, open_pos, rows_5m)."""
    coin = entry["name"]
    tick = entry.get("tv_mintick")
    if not tick:
        raise ValueError(f"{coin}: roster has no mintick")
    rows_5m = load_rows(coin, "5m", bars_dir)
    rows_1h = load_rows(coin, "1h", bars_dir)
    rows_1d = load_rows(coin, "1d", bars_dir)
    twin = Twin(TwinConfig(symbol=coin, mintick=float(tick), arm_tf_s=arm_s))
    if drop_12h:
        twin.pools = [p for p in twin.pools if p.name != "12h"]
    pre_1h = [r for r in rows_1h if r[0] < week_start]
    for name in ("12h", "D", "W"):
        if any(p.name == name for p in twin.pools):
            twin.warm_pool(name, pre_1h)
    twin.warm_pool("M", [r for r in rows_1d if r[0] < week_start])
    twin.seed_gates(pre_1h)
    seed_win = [r for r in rows_5m if week_start - arm_s <= r[0] < week_start]
    if seed_win:
        twin.seed_arm(max(r[2] for r in seed_win), min(r[3] for r in seed_win))
    events: list[dict] = []
    week_rows = [r for r in rows_5m if week_start <= r[0] < week_end]
    for r in week_rows:
        events.extend(twin.replay_bar(int(r[0]), r[1], r[2], r[3], r[4], bar_s=300))
    open_pos = None
    if twin.pos != 0:
        open_pos = {
            "dir": "long" if twin.pos == 1 else "short",
            "entry_ts": twin.entry_ts,
            "entry_px": twin.entry_px,
        }
    return events, open_pos, week_rows, rows_5m


def summarize(roster, week_start, week_end, bars_dir, arm_s, drop_12h):
    """Aggregate one config across the whole roster (DRAM excluded from tails)."""
    kind_pnl: dict[str, list[float]] = {"bf": [], "brk": [], "flip": []}
    kind_gb: dict[str, list[float]] = {"bf": [], "brk": [], "flip": []}
    realized_sum = 0.0
    open_mtm_sum = 0.0
    per_symbol: dict[str, dict] = {}
    for entry in roster["symbols"]:
        coin = entry["name"]
        events, open_pos, _week_rows, rows_5m = replay_cfg(
            entry, week_start, week_end, bars_dir, arm_s, drop_12h
        )
        exits = [e for e in events if e["action"] == "exit"]
        sym_real = 0.0
        for e in exits:
            m = episode_metrics(
                rows_5m, e["dir"], e["entry_ts"], e["entry_px"], e["ts"], e["price"]
            )
            kind_pnl[e["kind"]].append(e["pnl_pct"])
            kind_gb[e["kind"]].append(m["give_back_pp"])
            sym_real += e["pnl_pct"]
        unreal = None
        if open_pos:
            last_c = rows_5m[-1][4]
            sign = 1.0 if open_pos["dir"] == "long" else -1.0
            unreal = sign * (last_c - open_pos["entry_px"]) / open_pos["entry_px"] * 100.0
            if coin != "xyz:DRAM":
                open_mtm_sum += unreal
        if coin != "xyz:DRAM":
            realized_sum += sym_real
        per_symbol[coin] = {
            "n": len(exits),
            "real": sym_real,
            "open": open_pos["dir"] if open_pos else None,
            "unreal": unreal,
        }
    return {
        "kind_pnl": kind_pnl,
        "kind_gb": kind_gb,
        "realized_sum": realized_sum,
        "open_mtm_sum": open_mtm_sum,
        "per_symbol": per_symbol,
    }


def _class_line(label, pnl, gb):
    if not pnl:
        return f"| {label} | 0 | -- | -- | -- |"
    wr = 100 * sum(1 for p in pnl if p > 0) / len(pnl)
    return (
        f"| {label} | {len(pnl)} | {wr:.0f}% | "
        f"{sum(pnl) / len(pnl):+.2f} | {sum(gb) / len(gb):.2f} |"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Ablate frozen control vs live variant")
    ap.add_argument("--roster", required=True)
    ap.add_argument("--bars-dir", default=str(REPO / "analysis" / "paper" / "bars"))
    ap.add_argument("--week-start", default=WEEK_START_DEFAULT)
    args = ap.parse_args()
    roster = json.loads(Path(args.roster).read_text())
    bars_dir = Path(args.bars_dir)
    week_start = int(
        datetime.fromisoformat(args.week_start).replace(tzinfo=timezone.utc).timestamp()
    )
    week_end = week_start + WEEK_DAYS * 86400

    results = {
        name: summarize(roster, week_start, week_end, bars_dir, **cfg)
        for name, cfg in CONFIGS.items()
    }

    labels = {
        "bf": "BF harvest-touch",
        "brk": "BF adverse-break",
        "flip": "Flip backstop",
    }
    print("TVB-16 config ablation -- same committed week-1 bars, two configs\n")
    for name, r in results.items():
        print(f"### {name}")
        print("| exit class | n | win | avg pnl% | give-back pp |")
        print("|---|---|---|---|---|")
        for k in ("bf", "brk", "flip"):
            print(_class_line(labels[k], r["kind_pnl"][k], r["kind_gb"][k]))
        n_closed = sum(len(r["kind_pnl"][k]) for k in r["kind_pnl"])
        print(
            f"\nclosed={n_closed}  realized sum={r['realized_sum']:+.2f}pp  "
            f"open MTM sum={r['open_mtm_sum']:+.2f}pp  "
            f"combined={r['realized_sum'] + r['open_mtm_sum']:+.2f}pp  (roster only, DRAM excl)\n"
        )

    print("### Per-symbol (control -> variant)")
    print("| symbol | ctrl trades | ctrl real | ctrl open | var trades | var real | var open |")
    print("|---|---|---|---|---|---|---|")
    ctrl, var = results.values()
    for entry in roster["symbols"]:
        c = entry["name"]
        a, b = ctrl["per_symbol"][c], var["per_symbol"][c]

        def opentxt(s):
            if not s["open"]:
                return "flat"
            return f"{s['open']} {s['unreal']:+.1f}%"

        print(
            f"| {c} | {a['n']} | {a['real']:+.2f} | {opentxt(a)} "
            f"| {b['n']} | {b['real']:+.2f} | {opentxt(b)} |"
        )


if __name__ == "__main__":
    main()
