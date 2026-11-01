"""Rebuild `single_file_run.json`, the example of the contract's single-file flavour
(viewer/CONTRACT.md section 7): one run.json with its instruments inline.

The bars are the venue's REAL daily candles (the last 100 days of run one's BTC file); the six
cards are the engine's own BTC daily cards from run one inside that window, trimmed to three
books. Nothing here is a result: the file exists to show the shape and to prove the import path
end to end (stage 3 of the contract).

    uv run python analysis/domino/viewer/examples/make_example.py
    uv run python -m analysis.domino.trade_viewer validate analysis/domino/viewer/examples/single_file_run.json
    uv run python -m analysis.domino.trade_viewer import analysis/domino/viewer/examples/single_file_run.json
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
RUN_ONE = HERE.parent / "data" / "runs" / "management-book-20261010"
OUT = HERE / "single_file_run.json"
DAY = 86_400
KEEP = ("C", "A", "ref")


def main() -> None:
    run = json.loads((RUN_ONE / "run.json").read_text(encoding="utf-8"))
    btc = json.loads((RUN_ONE / "BTC.json").read_text(encoding="utf-8"))
    daily = btc["bars"]["1d"]
    end = daily[-1][0]
    start = end - 99 * DAY
    bars = [b for b in daily if start <= b[0] <= end]
    cards = []
    for c in btc["trades"]:
        if c["bar"] != "D" or not (start + 10 * DAY <= c["entry"]["t"] <= end - 25 * DAY):
            continue
        cards.append(dict(c, books=[b for b in c["books"] if b["id"] in KEEP]))
    cards = cards[:6]
    doc = {
        "contract": 1,
        "id": "example-single-file",
        "name": "Example: the single-file flavour (BTC, six daily cards copied from run one)",
        "as_of": run["as_of"],
        "source": {
            "repo": "tradingview-backtesting",
            "command": "uv run python analysis/domino/viewer/examples/make_example.py "
            "(cards copied from run one, bars from the census cache)",
        },
        "clock": run["clock"],
        "units": ["D"],
        "bars": ["1d"],
        "returns": run["returns"],
        "rules": run["rules"],
        "books": [dict(b) for b in run["books"] if b["id"] in KEEP],
        "notes": "A hand-assembled example of the single-file flavour (CONTRACT.md section 7): "
        "one run.json with the instruments inline. The bars are the venue's real daily candles "
        "from the census cache; the six cards are the engine's own BTC daily cards from run one, "
        "trimmed to three books. It exists to show the shape and to prove the import path end to "
        "end; it is not a result.",
        "instruments": [{"instrument": "BTC", "bars": {"1d": bars}, "trades": cards}],
    }
    OUT.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"{OUT}: {len(bars)} bars, {len(cards)} cards, {OUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
