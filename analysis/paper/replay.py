"""TVB-15 week-1 replay: the twin recorder over archived HL bars.

Deterministic: the same archived bars always regenerate the same event log
and scoreboard (both files are fully rewritten each run). The final bar of
every archived series is DROPPED before use -- HL candleSnapshot serves the
forming candle, and the twin records CLOSED bars only; the next archive run
completes that bar via the merge.

Per symbol: pools 12h/D/W warm from the 1h archive and M from the 1d archive
up to the week boundary (anchor times at warm-bar resolution -- the declared
fidelity delta); gates seed from the 1h stream; the prior completed 15m arm
window seeds from the last three pre-week 5m bars; then the week's 5m bars
replay through the full v6 pass. Positions start FLAT at the week boundary
(declared; the live chart may carry pre-week state).

Run:
    uv run python -m analysis.paper.replay --roster analysis/paper/roster_week1.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

from analysis.giveback import episode_metrics
from analysis.paper.archive import bars_path
from analysis.paper.engine import Twin, TwinConfig

REPO = Path(__file__).resolve().parents[2]
WEEK_START_DEFAULT = "2026-07-20"
WEEK_DAYS = 7


def load_rows(coin: str, interval: str, bars_dir: Path) -> list[list]:
    rows = json.loads(bars_path(coin, interval, bars_dir).read_text())["bars"]
    return rows[:-1]  # the last archived bar may be the forming candle


def replay_symbol(entry: dict, week_start: int, week_end: int, bars_dir: Path):
    coin = entry["name"]
    tick = entry.get("tv_mintick")
    if not tick:
        raise ValueError(
            f"{coin}: roster has no mintick; run the archive with --update-roster-ticks"
        )
    rows_5m = load_rows(coin, "5m", bars_dir)
    rows_1h = load_rows(coin, "1h", bars_dir)
    rows_1d = load_rows(coin, "1d", bars_dir)
    twin = Twin(TwinConfig(symbol=coin, mintick=float(tick)))
    pre_1h = [r for r in rows_1h if r[0] < week_start]
    for pool_name in ("12h", "D", "W"):
        twin.warm_pool(pool_name, pre_1h)
    twin.warm_pool("M", [r for r in rows_1d if r[0] < week_start])
    twin.seed_gates(pre_1h)
    seed_win = [r for r in rows_5m if week_start - 900 <= r[0] < week_start]
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
    return events, open_pos, week_rows


def _fmt_ts(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%m-%d %H:%M")


def build_scoreboard(roster: dict, per_symbol: dict, week_start: int, week_end: int) -> str:
    lines = [
        "# TVB-15 paper-trading week 1 -- twin scoreboard",
        "",
        f"Week window: {datetime.fromtimestamp(week_start, tz=timezone.utc):%Y-%m-%d %H:%M} -> "
        f"{datetime.fromtimestamp(week_end, tz=timezone.utc):%Y-%m-%d %H:%M} UTC "
        "(v6 defaults frozen; no mid-week tuning)",
        f"Roster frozen: {roster.get('frozen_at_utc')} | rule: {roster.get('rule')}",
        "",
        "Fill conventions (a-priori): entry at trigger; BF exit at the line value;",
        "break/flip exits at the 5m close. 1x, gross, no fees/funding. The twin",
        "records CLOSED 5m bars only and starts FLAT at the week boundary.",
        "",
        "| symbol | tail | data through | trades | bf | brk | flip | wins | sum pnl% | med pnl% | avg MFE% | avg gb pp | open |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    kind_rows: dict[str, list[dict]] = {"bf": [], "brk": [], "flip": []}
    for entry in roster["symbols"]:
        coin = entry["name"]
        events, open_pos, week_rows, rows_5m = per_symbol[coin]
        exits = [e for e in events if e["action"] == "exit"]
        metrics = []
        for e in exits:
            m = episode_metrics(
                rows_5m, e["dir"], e["entry_ts"], e["entry_px"], e["ts"], e["price"]
            )
            m["kind"], m["pnl_pct"] = e["kind"], e["pnl_pct"]
            metrics.append(m)
            kind_rows[e["kind"]].append(m)
        through = _fmt_ts(int(week_rows[-1][0]) + 300) if week_rows else "--"
        open_txt = "--"
        if open_pos:
            open_txt = f"{open_pos['dir']} @{open_pos['entry_px']:.4g} since {_fmt_ts(open_pos['entry_ts'])}"
        n = len(exits)
        kinds = {k: sum(1 for e in exits if e["kind"] == k) for k in ("bf", "brk", "flip")}
        pnls = [e["pnl_pct"] for e in exits]
        lines.append(
            f"| {coin} | {entry['tail']} | {through} | {n} | {kinds['bf']} | {kinds['brk']} | "
            f"{kinds['flip']} | {sum(1 for p in pnls if p > 0)} | "
            f"{sum(pnls):.2f} | {median(pnls):.2f} | "
            if n
            else f"| {coin} | {entry['tail']} | {through} | 0 | 0 | 0 | 0 | 0 | -- | -- | "
        )
        if n:
            lines[-1] += (
                f"{100 * sum(m['mfe'] for m in metrics) / n:.2f} | "
                f"{sum(m['give_back_pp'] for m in metrics) / n:.2f} | {open_txt} |"
            )
        else:
            lines[-1] += f"-- | -- | {open_txt} |"
    lines += [
        "",
        "## By exit class (closed trades, all symbols)",
        "",
        "| exit class | n | win rate | avg pnl% | med pnl% | avg give-back pp |",
        "|---|---|---|---|---|---|",
    ]
    label = {
        "bf": "BF S/L Exit (harvest touch)",
        "brk": "BF Break L/S Exit (adverse close-through)",
        "flip": "Flip S/L Exit (full-gate backstop)",
    }
    for kind in ("bf", "brk", "flip"):
        ms = kind_rows[kind]
        if ms:
            pn = [m["pnl_pct"] for m in ms]
            lines.append(
                f"| {label[kind]} | {len(ms)} | {100 * sum(1 for p in pn if p > 0) / len(ms):.0f}% | "
                f"{sum(pn) / len(ms):.2f} | {median(pn):.2f} | "
                f"{sum(m['give_back_pp'] for m in ms) / len(ms):.2f} |"
            )
        else:
            lines.append(f"| {label[kind]} | 0 | -- | -- | -- | -- |")
    lines += [
        "",
        "Notes: the scanner score SELECTED the roster; the twin's D/W/M gate decides",
        "entries -- different TFC measurements, so zero-entry symbols are the gate",
        "doing its job, not a defect. xyz:DRAM is the parity instrument (live v6",
        "front chart), not rule-selected. Divergences user-vs-twin get numbered",
        "TVB15-D1.. in the protocol doc.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Replay the week through the v6 twin")
    ap.add_argument("--roster", required=True)
    ap.add_argument("--bars-dir", default=str(REPO / "analysis" / "paper" / "bars"))
    ap.add_argument("--week-start", default=WEEK_START_DEFAULT, help="UTC date, e.g. 2026-07-20")
    ap.add_argument("--out-events", default=str(REPO / "analysis" / "paper" / "events_week1.jsonl"))
    ap.add_argument(
        "--out-scoreboard", default=str(REPO / "analysis" / "paper" / "scoreboard_week1.md")
    )
    args = ap.parse_args()
    roster = json.loads(Path(args.roster).read_text())
    bars_dir = Path(args.bars_dir)
    week_start = int(
        datetime.fromisoformat(args.week_start).replace(tzinfo=timezone.utc).timestamp()
    )
    week_end = week_start + WEEK_DAYS * 86400
    per_symbol: dict = {}
    all_events: list[dict] = []
    for entry in roster["symbols"]:
        coin = entry["name"]
        rows_5m = load_rows(coin, "5m", bars_dir)
        events, open_pos, week_rows = replay_symbol(entry, week_start, week_end, bars_dir)
        per_symbol[coin] = (events, open_pos, week_rows, rows_5m)
        all_events.extend(events)
        n_exit = sum(1 for e in events if e["action"] == "exit")
        n_enter = sum(1 for e in events if e["action"] == "enter")
        print(f"{coin:12} entries={n_enter:3} exits={n_exit:3} open={'yes' if open_pos else 'no'}")
    all_events.sort(key=lambda e: (e["ts"], e["sym"], e["action"]))
    with open(args.out_events, "w", encoding="utf-8") as f:
        for e in all_events:
            f.write(json.dumps(e, sort_keys=True) + "\n")
    scoreboard = build_scoreboard(roster, per_symbol, week_start, week_end)
    Path(args.out_scoreboard).write_text(scoreboard, encoding="utf-8")
    print(f"wrote {args.out_events} ({len(all_events)} events) and {args.out_scoreboard}")


if __name__ == "__main__":
    main()
