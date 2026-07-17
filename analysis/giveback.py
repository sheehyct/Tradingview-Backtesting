"""Per-episode MFE / MAE / give-back metrics from a committed bars reference.

TVB-13 exit-arc instrumentation (docs/HANDOFF.md, TVB-13 entry): quantify how
much of a winner's peak open profit each exit rule surrenders. An EPISODE is
(direction, entry_time, entry_price, exit_time, exit_price); BARS are a
committed venue reference JSON (analysis/reference/*.json) with
columns [time_s, open, high, low, close, volume].

Definitions (stated for a SHORT; longs mirror):
  favorable(bar) = (entry_price - low)  / entry_price
  adverse(bar)   = (high - entry_price) / entry_price
  mfe        = max favorable over [entry_time, exit_time]  (fraction, >= 0)
  mae        = max adverse over the same window            (fraction, >= 0)
  realized   = (entry_price - exit_price) / entry_price    (fraction, signed)
  give_back_pp   = (mfe - realized) * 100      -- points of peak surrendered
  give_back_frac = 1 - realized / mfe (mfe > 0) -- > 1.0 means the exit gave
                   back MORE than the whole peak (finished worse than flat)

Acceptance anchor (hand-labeled DRAM June fixture, tests/test_giveback_fixture.py):
re-entry short 65.88 @ 2026-06-04T19:45Z, exit 66.66 @ 2026-06-14T06:45Z ->
MFE 19.87%, bottom 52.788 @ 2026-06-06T02:30Z (30.8h in), MAE 1.21%,
realized -1.18%, give_back 21.06pp. These reproduce the user's live account
of the episode to the decimal.
"""

import argparse
import json
from datetime import datetime


def load_bars(path):
    with open(path) as f:
        doc = json.load(f)
    return doc["bars"]


def _parse_time(value):
    if isinstance(value, (int, float)):
        return int(value)
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def episode_metrics(bars, direction, entry_time, entry_price, exit_time, exit_price):
    """Compute MFE/MAE/realized/give-back for one episode. Times: unix s or ISO."""
    et, xt = _parse_time(entry_time), _parse_time(exit_time)
    if xt <= et:
        raise ValueError("exit_time must be after entry_time")
    win = [b for b in bars if et <= b[0] <= xt]
    if not win:
        raise ValueError("no bars in the episode window")
    ep = float(entry_price)
    if direction == "short":
        fav = [(ep - b[3]) / ep for b in win]
        adv = [(b[2] - ep) / ep for b in win]
        realized = (ep - float(exit_price)) / ep
    elif direction == "long":
        fav = [(b[2] - ep) / ep for b in win]
        adv = [(ep - b[3]) / ep for b in win]
        realized = (float(exit_price) - ep) / ep
    else:
        raise ValueError("direction must be 'long' or 'short'")
    mfe = max(max(fav), 0.0)
    mae = max(max(adv), 0.0)
    mfe_bar = win[fav.index(max(fav))]
    return {
        "direction": direction,
        "entry_time_s": et,
        "exit_time_s": xt,
        "bars": len(win),
        "mfe": mfe,
        "mae": mae,
        "realized": realized,
        "give_back_pp": (mfe - realized) * 100.0,
        "give_back_frac": (1.0 - realized / mfe) if mfe > 0 else None,
        "mfe_time_s": mfe_bar[0],
        "hours_to_mfe": (mfe_bar[0] - et) / 3600.0,
    }


def summarize(rows):
    """Distribution summary over a list of episode_metrics() dicts."""
    if not rows:
        return {}

    def pct(vals, q):
        s = sorted(vals)
        i = max(0, min(len(s) - 1, int(round(q * (len(s) - 1)))))
        return s[i]

    gb = [r["give_back_pp"] for r in rows]
    mfe = [r["mfe"] * 100 for r in rows]
    winners = [r for r in rows if r["mfe"] >= 0.02]
    round_trips = [r for r in winners if r["realized"] <= 0]
    return {
        "episodes": len(rows),
        "mfe_pct": {"median": pct(mfe, 0.5), "p90": pct(mfe, 0.9)},
        "give_back_pp": {"median": pct(gb, 0.5), "p90": pct(gb, 0.9)},
        "winners_2pct_plus": len(winners),
        "full_round_trips": len(round_trips),
    }


def main():
    ap = argparse.ArgumentParser(description="MFE/MAE/give-back per episode")
    ap.add_argument("--bars", required=True, help="bars reference JSON")
    ap.add_argument(
        "--episodes",
        help="JSON file: list of {direction, entry_time, entry_price, exit_time, exit_price}",
    )
    ap.add_argument("--dir", dest="direction", choices=["long", "short"])
    ap.add_argument("--entry-time")
    ap.add_argument("--entry-price", type=float)
    ap.add_argument("--exit-time")
    ap.add_argument("--exit-price", type=float)
    args = ap.parse_args()
    bars = load_bars(args.bars)
    if args.episodes:
        with open(args.episodes) as f:
            eps = json.load(f)
        rows = [
            episode_metrics(
                bars,
                e["direction"],
                e["entry_time"],
                e["entry_price"],
                e["exit_time"],
                e["exit_price"],
            )
            for e in eps
        ]
        print(json.dumps({"episodes": rows, "summary": summarize(rows)}, indent=1))
    else:
        m = episode_metrics(
            bars, args.direction, args.entry_time, args.entry_price, args.exit_time, args.exit_price
        )
        print(json.dumps(m, indent=1))


if __name__ == "__main__":
    main()
