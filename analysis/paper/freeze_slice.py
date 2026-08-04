"""Post-roster-freeze sensitivity slice of the week-1 record (audit F1).

The TVB-15 external audit (docs/reviews/tvb15-codex-audit.md, F1 HIGH)
found that the week-1 window opens at 2026-07-20 00:00 UTC while the roster
was frozen at 14:31:21 UTC -- so events before the freeze grade instruments
selected with information that did not exist when they occurred. This tool
splits the committed record at the freeze boundary and reports both slices.
Read-only; the frozen record files stay owned by replay.py.

    uv run python -m analysis.paper.freeze_slice
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FREEZE_DEFAULT = "2026-07-20T14:31:21+00:00"
PARITY = {"xyz:DRAM"}


def fmt(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%m-%d %H:%M")


def class_table(exits: list[dict]) -> None:
    by_kind: dict[str, list[float]] = {}
    for e in exits:
        by_kind.setdefault(e["kind"], []).append(e["pnl_pct"])
    for k in ("bf", "brk", "flip"):
        pn = by_kind.get(k, [])
        if pn:
            wr = 100 * sum(1 for p in pn if p > 0) / len(pn)
            print(
                f"  {k:4} n={len(pn):2} win={wr:3.0f}% "
                f"avg={sum(pn) / len(pn):+.2f} sum={sum(pn):+.2f}"
            )
        else:
            print(f"  {k:4} n= 0")


def main() -> None:
    ap = argparse.ArgumentParser(description="Split week-1 record at roster freeze")
    ap.add_argument("--events", default=str(REPO / "analysis" / "paper" / "events_week1.jsonl"))
    ap.add_argument("--freeze", default=FREEZE_DEFAULT, help="ISO freeze timestamp")
    args = ap.parse_args()
    freeze = int(datetime.fromisoformat(args.freeze).timestamp())
    evs = [
        json.loads(line)
        for line in Path(args.events).read_text(encoding="utf-8").splitlines()
        if line
    ]
    pre_ev = [e for e in evs if e["ts"] < freeze]
    print(f"events: total={len(evs)}  pre-freeze={len(pre_ev)} (freeze {fmt(freeze)} UTC)")
    exits = [e for e in evs if e["action"] == "exit" and e["sym"] not in PARITY]
    pre = [e for e in exits if e["entry_ts"] < freeze]
    post = [e for e in exits if e["entry_ts"] >= freeze]
    print(
        f"\nALL closed (roster, parity excl): n={len(exits)} "
        f"realized={sum(e['pnl_pct'] for e in exits):+.2f}pp"
    )
    class_table(exits)
    print(
        f"\nPRE-FREEZE-ENTRY (selection-lookahead-contaminated): n={len(pre)} "
        f"realized={sum(e['pnl_pct'] for e in pre):+.2f}pp"
    )
    class_table(pre)
    for e in sorted(pre, key=lambda x: x["pnl_pct"]):
        print(
            f"    {e['sym']:10} {e['dir']:5} entry {fmt(e['entry_ts'])} "
            f"exit {fmt(e['ts'])} {e['kind']:4} {e['pnl_pct']:+.2f}%"
        )
    print(
        f"\nPOST-FREEZE-ENTRY (clean-entry slice): n={len(post)} "
        f"realized={sum(e['pnl_pct'] for e in post):+.2f}pp"
    )
    class_table(post)
    opens: dict[str, dict] = {}
    for e in evs:
        if e["action"] == "enter":
            opens[e["sym"]] = e
        elif e["action"] == "exit":
            opens.pop(e["sym"], None)
    print("\nopen at window end (entry vs freeze):")
    for sym, e in sorted(opens.items()):
        tag = "PRE-FREEZE" if e["ts"] < freeze else "post-freeze"
        par = " [parity]" if sym in PARITY else ""
        print(f"  {sym:10} {e['dir']:5} @{e['price']:g} since {fmt(e['ts'])} {tag}{par}")


if __name__ == "__main__":
    main()
