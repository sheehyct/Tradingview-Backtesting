"""TVB-15 week-1 roster: scanner-fed selection, frozen a-priori.

Rule (ratified with the user 2026-07-20): xyz universe only; liquidity floors
vol24 >= $5M and OI >= $3M; then the score tails -- up to 5 most-positive
(score > 0) and up to 5 most-negative (score < 0) at freeze time. The score is
the scanner's signed heat triage (hip3-scanner src/metrics.js: 45% FTFC
dot-net over {15m,1h,4h,1d} + 35% r60 momentum + 20% net live patterns,
scaled by rvol; its own comment: "NOT a signal"). It SELECTS instruments in
motion; the twin's D/W/M gate still decides entries -- two different TFC
measurements by construction, so a high-score symbol with zero entries is the
M/W/D gate doing its job, not a bug.

Both directions stay enabled on every roster symbol regardless of tail.
Frozen for week 1: no re-selection until 2026-07-27 00:00 UTC.

Freeze run:
    uv run python -m analysis.paper.roster --out analysis/paper/roster_week1.json

tv_mintick is filled after the freeze from TradingView symbol_info (the
parity-correct tick source for the +/- 1 tick triggers); if TV is
unavailable, it is inferred from HL price granularity and the provenance
field says so.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

STATE_URL = "https://hip3-alerts-production.up.railway.app/api/state"

DEFAULT_RULE = {
    "universe": "xyz",
    "min_vol_usd": 5_000_000.0,
    "min_oi_usd": 3_000_000.0,
    "tail_size": 5,
}

KEEP = ("name", "sym", "uni", "score", "vol", "oiUsd", "mid", "ftfc", "chg24", "rvol", "funding")


def _trim(coin: dict) -> dict:
    return {k: coin.get(k) for k in KEEP}


def select_roster(state: dict, rule: dict | None = None) -> dict:
    """Apply the frozen rule to a /api/state document."""
    rule = dict(DEFAULT_RULE, **(rule or {}))
    floor = [
        c
        for c in state["coins"]
        if c.get("uni") == rule["universe"]
        and (c.get("vol") or 0) >= rule["min_vol_usd"]
        and (c.get("oiUsd") or 0) >= rule["min_oi_usd"]
        and c.get("score") is not None
    ]
    n = rule["tail_size"]
    long_tail = [c for c in sorted(floor, key=lambda c: -c["score"]) if c["score"] > 0][:n]
    short_tail = [c for c in sorted(floor, key=lambda c: c["score"]) if c["score"] < 0][:n]
    symbols = [dict(_trim(c), tail="long", tv_mintick=None, mintick_source=None) for c in long_tail]
    symbols += [
        dict(_trim(c), tail="short", tv_mintick=None, mintick_source=None) for c in short_tail
    ]
    return {
        "rule": rule,
        "source_ts": state.get("ts"),
        "long_names": [c["name"] for c in long_tail],
        "short_names": [c["name"] for c in short_tail],
        "symbols": symbols,
    }


def freeze(out_path: str | Path, state: dict | None = None, rule: dict | None = None) -> dict:
    if state is None:
        import requests

        state = requests.get(STATE_URL, timeout=30).json()
    roster = select_roster(state, rule)
    roster["frozen_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    Path(out_path).write_text(json.dumps(roster, indent=1) + "\n")
    return roster


def main() -> None:
    ap = argparse.ArgumentParser(description="Freeze the TVB-15 week-1 roster")
    ap.add_argument("--out", required=True)
    ap.add_argument("--state-file", help="offline /api/state JSON instead of the live fetch")
    args = ap.parse_args()
    state = json.loads(Path(args.state_file).read_text()) if args.state_file else None
    roster = freeze(args.out, state=state)
    print(f"frozen {len(roster['symbols'])} symbols -> {args.out}")
    for c in roster["symbols"]:
        print(
            f"  {c['tail']:5} {c['name']:14} score={c['score']:>4} "
            f"vol=${c['vol'] / 1e6:8.1f}M oi=${c['oiUsd'] / 1e6:7.1f}M"
        )


if __name__ == "__main__":
    main()
