"""TVB-20 control-port parity gate.

Replays the Python twin (analysis/paper/engine.py, deployed-default cell) over
the TV-harvested 5m bars (analysis/reference/tv_deep/) and joins its event
stream against the TFC-BF CONTROL [TVB-20] strategy() trade list harvested by
scripts/tvb20_port_harvest.mjs (analysis/reference/port_parity/).

Pinned conventions (docs/experiments/, TVB-20, user-approved 2026-08-08):
- Fill model is DECISION-EXACT: the strategy emits market orders on the signal
  bar, filled at that bar's close (process_orders_on_close=true). Parity is
  therefore claimed on (bar, direction, kind) for EVERY event, on exact price
  for break/flip exits (both sides fill at the same bar close, same feed), and
  entry/BF-harvest prices carry a DECLARED residual = tv_close - twin_level.
- The twin feed is sliced to the strategy chart's actual first loaded bar so
  both sides share one cold-start warm-up. For the 2026-08 harvest all three
  parity symbols floor at the same first bar as the tv_deep dumps.
- The formal gate window is 2026-07-06 00:00Z .. 2026-08-03 00:00Z, but the
  join runs over the FULL feed overlap: any mismatch before the window would
  corrupt position state inside it, so full-span agreement is the real claim.
- The dump's last row may be a forming bar (dropped). TV trades whose events
  fall after the twin feed ends are counted as beyond_feed, not mismatches.
  An OPEN TV trade (empty exit_signal) contributes only its entry event.

Timestamp convention: TV trade entry/exit times are ms epoch of the FILL bar.
The join tries offsets {0, +300, -300} seconds against the twin's bar-open
event timestamps, picks the best on entry events, and DECLARES the choice --
a constant offset is a reporting convention, a non-constant one is a finding.

Usage: uv run python -m analysis.paper.port_parity [GOOGL TSLA DRAM]
Exit 0 = gate PASS on all symbols (full-span event match, break/flip exact).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median

from analysis.paper.engine import Twin, TwinConfig

ROOT = Path(__file__).resolve().parents[2]
TV_DEEP = ROOT / "analysis" / "reference" / "tv_deep"
PORT = ROOT / "analysis" / "reference" / "port_parity"

WINDOW_START = int(datetime(2026, 7, 6, tzinfo=timezone.utc).timestamp())
WINDOW_END = int(datetime(2026, 8, 3, tzinfo=timezone.utc).timestamp())

KIND_BY_PREFIX = (("BF ", "bf"), ("Break", "brk"), ("Flip", "flip"))


def kind_of(exit_signal: str) -> str:
    for prefix, kind in KIND_BY_PREFIX:
        if exit_signal.startswith(prefix):
            return kind
    raise ValueError(f"unrecognized exit comment: {exit_signal!r}")


def twin_events(coin: str, first_bar_ts: int, mintick: float):
    dump = json.loads((TV_DEEP / f"tvb19_tv_xyz_{coin}_5m.json").read_text())
    bars = dump["bars"][:-1]  # last row may be forming (declared in the dump)
    bars = [b for b in bars if int(b[0]) >= first_bar_ts]
    tw = Twin(TwinConfig(symbol=coin, mintick=mintick, pine_gate_warmup=True))
    events = []
    for b in bars:
        events.extend(tw.replay_bar(int(b[0]), b[1], b[2], b[3], b[4]))
    feed_end = int(bars[-1][0])
    closes = {int(b[0]): b[4] for b in bars}
    return events, feed_end, closes, len(bars)


def tv_events(trades: list[dict]):
    evs = []
    for tr in trades:
        d = "long" if tr["direction"] == "L" else "short"
        evs.append(
            {
                "ts": int(tr["entry_time"] // 1000),
                "action": "enter",
                "dir": d,
                "kind": "entry",
                "price": tr["entry_price"],
                "index": tr["index"],
            }
        )
        sig = tr.get("exit_signal") or ""
        if sig:
            evs.append(
                {
                    "ts": int(tr["exit_time"] // 1000),
                    "action": "exit",
                    "dir": d,
                    "kind": kind_of(sig),
                    "price": tr["exit_price"],
                    "comment": sig,
                    "index": tr["index"],
                }
            )
    return evs


def pick_offset(tv_entries, twin_entry_ts):
    scores = {}
    for off in (0, 300, -300):
        scores[off] = sum(1 for e in tv_entries if (e["ts"] + off) in twin_entry_ts)
    best = max(scores, key=lambda o: scores[o])
    return best, scores


def compare(coin: str) -> dict:
    port = json.loads((PORT / f"tvb20_{coin}_trades.json").read_text())
    mintick = port["chart"]["mintick"]
    first_bar_ts = port["chart"]["first_bar_ts"]
    tw_evs, feed_end, closes, n_bars = twin_events(coin, first_bar_ts, mintick)
    tv_evs = tv_events(port["trades"])

    twin_entry_ts = {e["ts"] for e in tw_evs if e["action"] == "enter"}
    offset, offset_scores = pick_offset(
        [e for e in tv_evs if e["action"] == "enter" and e["ts"] <= feed_end], twin_entry_ts
    )

    in_feed = [dict(e, ts=e["ts"] + offset) for e in tv_evs if e["ts"] + offset <= feed_end]
    beyond_feed = [e for e in tv_evs if e["ts"] + offset > feed_end]

    def key(e):
        return (e["ts"], e["action"], e["dir"], e["kind"] if e["action"] == "exit" else "entry")

    twin_by_key = {key(e): e for e in tw_evs}
    tv_by_key = {key(e): e for e in in_feed}
    matched = sorted(set(twin_by_key) & set(tv_by_key))
    twin_only = sorted(set(twin_by_key) - set(tv_by_key))
    tv_only = sorted(set(tv_by_key) - set(twin_by_key))

    # price layer on matched events
    exact_kinds = {"brk", "flip"}
    exact_bad = []
    exact_max_delta = 0.0
    residuals = []  # (kind, tv - twin)
    for k in matched:
        te, ve = twin_by_key[k], tv_by_key[k]
        delta = ve["price"] - te["price"]
        if ve["action"] == "exit" and ve["kind"] in exact_kinds:
            exact_max_delta = max(exact_max_delta, abs(delta))
            if abs(delta) > mintick / 2:
                exact_bad.append({"key": k, "tv": ve["price"], "twin": te["price"]})
        else:  # entry or bf harvest: declared residual = close-fill vs level
            residuals.append((k[3] if ve["action"] == "exit" else "entry", delta))
            # cross-check the decision-exact claim: TV fill == that bar's close
            bar_close = closes.get(k[0])
            if bar_close is not None and abs(ve["price"] - bar_close) > mintick / 2:
                exact_bad.append(
                    {"key": k, "tv": ve["price"], "bar_close": bar_close, "check": "close-fill"}
                )

    in_window = [k for k in matched if WINDOW_START <= k[0] < WINDOW_END]
    win_twin_only = [k for k in twin_only if WINDOW_START <= k[0] < WINDOW_END]
    win_tv_only = [k for k in tv_only if WINDOW_START <= k[0] < WINDOW_END]

    def fmt(k):
        iso = datetime.fromtimestamp(k[0], tz=timezone.utc).isoformat()
        return {"ts": k[0], "iso": iso, "action": k[1], "dir": k[2], "kind": k[3]}

    abs_res = [abs(r) for _, r in residuals]
    result = {
        "coin": coin,
        "bars_replayed": n_bars,
        "feed_first_ts": first_bar_ts,
        "feed_end_ts": feed_end,
        "mintick": mintick,
        "ts_offset_applied_s": offset,
        "ts_offset_scores": offset_scores,
        "twin_events": len(tw_evs),
        "tv_events_total": len(tv_evs),
        "tv_events_in_feed": len(in_feed),
        "tv_events_beyond_feed": len(beyond_feed),
        "matched": len(matched),
        "twin_only": [fmt(k) for k in twin_only],
        "tv_only": [fmt(k) for k in tv_only],
        "window": {
            "start": WINDOW_START,
            "end": WINDOW_END,
            "matched": len(in_window),
            "twin_only": [fmt(k) for k in win_twin_only],
            "tv_only": [fmt(k) for k in win_tv_only],
        },
        "price_exact_layer": {
            "kinds": sorted(exact_kinds),
            "max_abs_delta": exact_max_delta,
            "violations": exact_bad,
        },
        "declared_residual_layer": {
            "kinds": ["entry", "bf"],
            "n": len(residuals),
            "mean_abs": mean(abs_res) if abs_res else None,
            "median_abs": median(abs_res) if abs_res else None,
            "max_abs": max(abs_res) if abs_res else None,
        },
        "pass": not twin_only and not tv_only and not exact_bad,
    }
    return result


def main(argv: list[str]) -> int:
    coins = argv or ["GOOGL", "TSLA", "DRAM"]
    results = []
    all_pass = True
    for coin in coins:
        r = compare(coin)
        results.append(r)
        all_pass &= r["pass"]
        status = "PASS" if r["pass"] else "MISMATCH"
        print(
            f"{coin}: {status} -- {r['matched']} events matched over {r['bars_replayed']} bars "
            f"(twin_only {len(r['twin_only'])}, tv_only {len(r['tv_only'])}, "
            f"offset {r['ts_offset_applied_s']}s, beyond_feed {r['tv_events_beyond_feed']}); "
            f"break/flip max |dp| {r['price_exact_layer']['max_abs_delta']:.6g}; "
            f"entry+bf residual median |dp| "
            f"{r['declared_residual_layer']['median_abs'] if r['declared_residual_layer']['median_abs'] is not None else float('nan'):.6g}"
        )
        for k in r["twin_only"]:
            print(f"  twin-only: {k['iso']} {k['action']} {k['dir']} {k['kind']}")
        for k in r["tv_only"]:
            print(f"  tv-only:   {k['iso']} {k['action']} {k['dir']} {k['kind']}")
    out = PORT / "tvb20_parity_result.json"
    out.write_text(
        json.dumps(
            {
                "generated_utc": datetime.now(tz=timezone.utc).isoformat(),
                "gate": "TVB-20 control-port parity (decision-exact conventions)",
                "all_pass": all_pass,
                "results": results,
            },
            indent=1,
        )
    )
    print(f"result artifact: {out}")
    print(f"GATE: {'PASS' if all_pass else 'FAIL'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
