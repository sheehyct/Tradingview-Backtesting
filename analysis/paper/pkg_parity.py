"""TVB-22 package-port parity gate (TFC-MT PACKAGE [TVB-22] vs twin arms).

Replays the Python twin in each pre-registered pattern arm (A1/A2/A3, the
TVB-21 Tier B configs UNDER the 2026-08-09 containment amendment) over the
TV-harvested 5m bars (analysis/reference/tv_deep/) and joins its event
stream against the TFC-MT PACKAGE [TVB-22] strategy() trade lists harvested
by scripts/tvb22_pkg_harvest.mjs (analysis/reference/pkg_parity/).

Same architecture and hardened contract as the TVB-20 control gate
(analysis/paper/port_parity.py) -- injective join on (bar, direction, kind),
fail-closed on malformed streams, cardinality equality -- with the package
extensions:
- exit kind 'tgt' (comment "Tgt <rung>") joins the DECLARED-RESIDUAL price
  layer (TV fills the signal bar's close; the twin fills AT the frozen
  level), alongside entry and bf. brk/flip stay price-EXACT.
- entry events carry the pattern layer: the TV entry comment is
  "<zipcode> t=<trigger at mintick precision>"; on every matched entry the
  pattern name must equal the twin's and the trigger must agree within
  mintick/2 (format.mintick rounds). A pattern/trig mismatch fails the gate
  -- this is the drift-detection payload the port exists for.
- the twin runs cold from the chart's first loaded bar in PATTERN mode
  (detector unseeded -- the chart shares the same cold start), with
  pine_gate_warmup=True as in the control gate.

The TVB-20 gate module is left untouched: its committed artifacts are a
pinned regression surface.

Usage: uv run python -m analysis.paper.pkg_parity [GOOGL TSLA DRAM]
Exit 0 = gate PASS on all (symbol, arm) cells.
"""

from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median

from analysis.paper.engine import Twin, TwinConfig

ROOT = Path(__file__).resolve().parents[2]
TV_DEEP = ROOT / "analysis" / "reference" / "tv_deep"
PKG = ROOT / "analysis" / "reference" / "pkg_parity"

WINDOW_START = int(datetime(2026, 7, 6, tzinfo=timezone.utc).timestamp())
WINDOW_END = int(datetime(2026, 8, 3, tzinfo=timezone.utc).timestamp())

KIND_BY_PREFIX = (("BF ", "bf"), ("Break", "brk"), ("Flip", "flip"), ("Tgt", "tgt"))
DIR_BY_TV = {"L": "long", "S": "short"}
VALID_DIRS = frozenset(DIR_BY_TV.values())
EXIT_KINDS = frozenset(("bf", "brk", "flip", "tgt"))
ENTRY_SIG_RE = re.compile(r"^(?P<name>.*) t=(?P<trig>[0-9.]+)$")

# Pre-registered pattern arms (tier_b.ARMS minus the controls); every twin
# override beyond (symbol, mintick, pine_gate_warmup) mirrors the runner.
ARM_TWIN = {
    "A1": {"entry_mode": "pattern", "arm_tf_s": 3600},
    "A2": {
        "entry_mode": "pattern",
        "arm_tf_s": 3600,
        "bf_prox_veto_pct": 1.0,
        "chop_veto_pct": 2.0,
        "exit_targets": 1,
        "bf_harvest_exit": False,
    },
    "A3": {
        "entry_mode": "pattern",
        "arm_tf_s": 3600,
        "bf_prox_veto_pct": 1.0,
        "chop_veto_pct": 2.0,
        "exit_targets": 2,
        "bf_harvest_exit": False,
    },
    # TVB-23 arms (prereg step 7; tier_b_t1floor.NEW_ARMS semantics). The
    # runner's retrace_census stays OFF here: it is a read-only stamp layer,
    # decision-identical, and the gate joins on decision events. ATR warm-up
    # note (narrowed 2026-08-16, TVB-24 audit F6): this gate's twin runs
    # COLD from the chart's first loaded bar, so its ATR warms over the same
    # NOMINAL 1H aggregation span as the pine; the 9/9 decision parity is
    # observed evidence of same-seed behavior, but the dump persists neither
    # TV's bar values nor an ATR trace, so literal seed identity is not
    # provable from the artifact. The runner's archived-bar seed differs.
    "D1": {
        "entry_mode": "pattern",
        "arm_tf_s": 3600,
        "bf_prox_veto_pct": 1.0,
        "chop_veto_pct": 2.0,
        "t1_floor_pct": 0.25,
        "exit_targets": 1,
        "bf_harvest_exit": False,
    },
    "DINF": {
        "entry_mode": "pattern",
        "arm_tf_s": 3600,
        "bf_prox_veto_pct": 1.0,
        "chop_veto_pct": 2.0,
        "t1_floor_pct": 0.25,
    },
    "D1ATR": {
        "entry_mode": "pattern",
        "arm_tf_s": 3600,
        "bf_prox_veto_atr": 1.0,
        "chop_veto_atr": 2.0,
        "atr_window": 14,
        "t1_floor_pct": 0.25,
        "exit_targets": 1,
        "bf_harvest_exit": False,
    },
}


# The canonical 3x3 gate matrix per arm generation, in artifact order. Only
# an exact-match run may write {gen}_parity_result.json (audit F4).
CANONICAL_COINS = ("GOOGL", "TSLA", "DRAM")
CANONICAL_ARMS = {"tvb22": ("A1", "A2", "A3"), "tvb23": ("D1", "DINF", "D1ATR")}


# Harvest filename prefix per arm generation (scripts/tvb22_pkg_harvest.mjs
# vs scripts/tvb23_pkg_harvest.mjs).
def _harvest_prefix(arm: str) -> str:
    return "tvb22" if arm.startswith("A") else "tvb23"


def kind_of(exit_signal: str) -> str:
    for prefix, kind in KIND_BY_PREFIX:
        if exit_signal.startswith(prefix):
            return kind
    raise ValueError(f"unrecognized exit comment: {exit_signal!r}")


def key(e: dict) -> tuple:
    return (e["ts"], e["action"], e["dir"], e["kind"] if e["action"] == "exit" else "entry")


def validate_port_wrapper(coin: str, arm: str, port: dict) -> list[str]:
    """Fail-closed dump-metadata validation (2026-08-16, TVB-24 audit F4):
    the harvested dump must BE the requested cell before any event join --
    coin/arm identity, the arm-selector input actually applied, the exact
    symbol and 5m interval, full-history floor termination, a usable
    mintick, exactly one computed strategy, and trade-count reconciliation.
    Previously these fields were recorded by the harvester but sat outside
    the executable PASS predicate."""
    problems = []
    chart = port.get("chart") or {}
    tv_sym = f"HIP3XYZ:{coin}USDC.P"
    for name, got, want in (
        ("coin", port.get("coin"), coin),
        ("arm", port.get("arm"), arm),
        ("roster_symbol", port.get("roster_symbol"), f"xyz:{coin}"),
        ("tv_symbol", port.get("tv_symbol"), tv_sym),
        ("chart.pro_symbol", chart.get("pro_symbol"), tv_sym),
    ):
        if got != want:
            problems.append(f"wrapper: {name} is {got!r}, expected {want!r}")
    if str(chart.get("interval")) != "5":
        problems.append(f"wrapper: chart interval {chart.get('interval')!r}, expected '5'")
    hist = chart.get("history_termination")
    state = hist.get("state") if isinstance(hist, dict) else hist
    if state != "floor":
        problems.append(f"wrapper: history termination {state!r}, expected 'floor'")
    mintick = chart.get("mintick")
    if not isinstance(mintick, (int, float)) or not math.isfinite(mintick) or mintick <= 0:
        problems.append(f"wrapper: mintick {mintick!r} is not a finite positive number")
    if port.get("strategy_count") != 1:
        problems.append(f"wrapper: strategy_count {port.get('strategy_count')!r}, expected 1")
    n_rows = len(port.get("trades") or [])
    if port.get("total_trades") != n_rows:
        problems.append(f"wrapper: total_trades {port.get('total_trades')!r} != {n_rows} rows")
    arm_input = str(port.get("arm_input") or "")
    if not arm_input.startswith(arm + " "):
        problems.append(f"wrapper: arm_input {arm_input!r} does not begin with {arm + ' '!r}")
    return problems


def validate_trades(trades: list[dict]) -> list[str]:
    problems = []
    for i, tr in enumerate(trades):
        if tr.get("direction") not in DIR_BY_TV:
            problems.append(
                f"trades[{i}] (index {tr.get('index')}): direction "
                f"{tr.get('direction')!r} not in {sorted(DIR_BY_TV)}"
            )
        if not ENTRY_SIG_RE.match(tr.get("entry_signal") or ""):
            problems.append(
                f"trades[{i}] (index {tr.get('index')}): entry_signal "
                f"{tr.get('entry_signal')!r} does not parse as '<pattern> t=<trig>'"
            )
        sig = tr.get("exit_signal") or ""
        if sig:
            try:
                kind_of(sig)
            except ValueError as exc:
                problems.append(f"trades[{i}] (index {tr.get('index')}): {exc}")
    open_rows = [i for i, tr in enumerate(trades) if not (tr.get("exit_signal") or "")]
    if len(open_rows) > 1:
        problems.append(
            f"{len(open_rows)} open rows (empty exit_signal) at {open_rows}; at most one is allowed"
        )
    if open_rows and open_rows[-1] != len(trades) - 1:
        problems.append(f"open row at {open_rows[-1]} is not the final trade row")
    return problems


def _finite_number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def validate_events(evs: list[dict], side: str) -> list[str]:
    problems = []
    for e in evs:
        if e["action"] not in ("enter", "exit"):
            problems.append(f"{side}: invalid action {e['action']!r} at ts {e['ts']}")
        elif e["action"] == "exit" and e["kind"] not in EXIT_KINDS:
            problems.append(f"{side}: invalid exit kind {e['kind']!r} at ts {e['ts']}")
        elif e["action"] == "enter":
            # TVB-22 audit F1: the pattern layer is the drift payload; a missing or
            # NaN trig must FAIL the gate, never NaN-compare into a silent pass.
            if not (isinstance(e.get("pattern"), str) and e.get("pattern")):
                problems.append(f"{side}: entry at ts {e['ts']} missing pattern name")
            if not _finite_number(e.get("trig")):
                problems.append(
                    f"{side}: entry at ts {e['ts']} trig {e.get('trig')!r} is not a finite number"
                )
        if e["dir"] not in VALID_DIRS:
            problems.append(f"{side}: invalid dir {e['dir']!r} at ts {e['ts']}")
    for k, n in sorted(Counter(map(key, evs)).items()):
        if n > 1:
            problems.append(f"{side}: duplicate event key {k} (x{n})")
    return problems


def twin_events(coin: str, arm: str, first_bar_ts: int, mintick: float):
    dump = json.loads((TV_DEEP / f"tvb19_tv_xyz_{coin}_5m.json").read_text())
    bars = dump["bars"][:-1]  # last row may be forming (declared in the dump)
    bars = [b for b in bars if int(b[0]) >= first_bar_ts]
    tw = Twin(TwinConfig(symbol=coin, mintick=mintick, pine_gate_warmup=True, **ARM_TWIN[arm]))
    events = []
    for b in bars:
        events.extend(tw.replay_bar(int(b[0]), b[1], b[2], b[3], b[4]))
    feed_end = int(bars[-1][0])
    closes = {int(b[0]): b[4] for b in bars}
    return events, feed_end, closes, len(bars)


def tv_events(trades: list[dict]):
    evs = []
    for tr in trades:
        d = DIR_BY_TV[tr["direction"]]
        m = ENTRY_SIG_RE.match(tr["entry_signal"])  # validate_trades() ran first
        evs.append(
            {
                "ts": int(tr["entry_time"] // 1000),
                "action": "enter",
                "dir": d,
                "kind": "entry",
                "price": tr["entry_price"],
                "pattern": m.group("name"),
                "trig": float(m.group("trig")),
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


def gate(coin: str, arm: str, tw_evs, feed_end: int, closes: dict, n_bars: int, port: dict) -> dict:
    mintick = port["chart"]["mintick"]
    first_bar_ts = port["chart"]["first_bar_ts"]
    violations = validate_trades(port["trades"])
    if violations:
        return {"coin": coin, "arm": arm, "structural_violations": violations, "pass": False}
    tv_evs = tv_events(port["trades"])
    violations += validate_events(tw_evs, "twin")
    violations += validate_events(tv_evs, "tv")

    twin_entry_ts = {e["ts"] for e in tw_evs if e["action"] == "enter"}
    offset, offset_scores = pick_offset(
        [e for e in tv_evs if e["action"] == "enter" and e["ts"] <= feed_end], twin_entry_ts
    )

    in_feed = [dict(e, ts=e["ts"] + offset) for e in tv_evs if e["ts"] + offset <= feed_end]
    beyond_feed = [e for e in tv_evs if e["ts"] + offset > feed_end]

    twin_by_key = {key(e): e for e in tw_evs}
    tv_by_key = {key(e): e for e in in_feed}
    matched = sorted(set(twin_by_key) & set(tv_by_key))
    twin_only = sorted(set(twin_by_key) - set(tv_by_key))
    tv_only = sorted(set(tv_by_key) - set(twin_by_key))

    if not (len(tw_evs) == len(in_feed) == len(matched)):
        violations.append(
            f"cardinality: twin {len(tw_evs)} / tv_in_feed {len(in_feed)} / "
            f"matched {len(matched)} must all be equal for PASS"
        )

    # price + pattern layers on matched events
    exact_kinds = {"brk", "flip"}
    exact_bad = []
    exact_max_delta = 0.0
    residuals = []  # (kind, tv - twin)
    pattern_bad = []
    for k in matched:
        te, ve = twin_by_key[k], tv_by_key[k]
        delta = ve["price"] - te["price"]
        if ve["action"] == "exit" and ve["kind"] in exact_kinds:
            exact_max_delta = max(exact_max_delta, abs(delta))
            if abs(delta) > mintick / 2:
                exact_bad.append({"key": k, "tv": ve["price"], "twin": te["price"]})
        else:  # entry, bf harvest, or frozen target: declared close-fill residual
            residuals.append((k[3] if ve["action"] == "exit" else "entry", delta))
            bar_close = closes.get(k[0])
            if bar_close is not None and abs(ve["price"] - bar_close) > mintick / 2:
                exact_bad.append(
                    {"key": k, "tv": ve["price"], "bar_close": bar_close, "check": "close-fill"}
                )
        if ve["action"] == "enter":
            # drift-detection payload: pattern name exact, trig within tick/2
            if ve["pattern"] != te.get("pattern"):
                pattern_bad.append(
                    {"key": k, "tv_pattern": ve["pattern"], "twin_pattern": te.get("pattern")}
                )
            else:
                # fail-closed even if validation is bypassed: a non-finite twin trig
                # is a violation, not a vacuous comparison (TVB-22 audit F1)
                tw_trig = te.get("trig")
                if not _finite_number(tw_trig) or abs(ve["trig"] - tw_trig) > mintick / 2:
                    pattern_bad.append({"key": k, "tv_trig": ve["trig"], "twin_trig": tw_trig})

    in_window = [k for k in matched if WINDOW_START <= k[0] < WINDOW_END]
    win_twin_only = [k for k in twin_only if WINDOW_START <= k[0] < WINDOW_END]
    win_tv_only = [k for k in tv_only if WINDOW_START <= k[0] < WINDOW_END]

    def fmt(k):
        iso = datetime.fromtimestamp(k[0], tz=timezone.utc).isoformat()
        return {"ts": k[0], "iso": iso, "action": k[1], "dir": k[2], "kind": k[3]}

    abs_res = [abs(r) for _, r in residuals]
    return {
        "coin": coin,
        "arm": arm,
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
            "kinds": ["entry", "bf", "tgt"],
            "n": len(residuals),
            "mean_abs": mean(abs_res) if abs_res else None,
            "median_abs": median(abs_res) if abs_res else None,
            "max_abs": max(abs_res) if abs_res else None,
        },
        "pattern_layer": {
            "checked": sum(1 for k in matched if k[1] == "enter"),
            "violations": pattern_bad,
        },
        "structural_violations": violations,
        "pass": not twin_only
        and not tv_only
        and not exact_bad
        and not pattern_bad
        and not violations,
    }


def compare(coin: str, arm: str) -> dict:
    port = json.loads((PKG / f"{_harvest_prefix(arm)}_{coin}_{arm}_trades.json").read_text())
    wrapper = validate_port_wrapper(coin, arm, port)
    if wrapper:
        return {"coin": coin, "arm": arm, "structural_violations": wrapper, "pass": False}
    tw_evs, feed_end, closes, n_bars = twin_events(
        coin, arm, port["chart"]["first_bar_ts"], port["chart"]["mintick"]
    )
    return gate(coin, arm, tw_evs, feed_end, closes, n_bars, port)


def main(argv: list[str]) -> int:
    # optional --arms D1,DINF,D1ATR selects the TVB-23 cells; default stays
    # the TVB-22 set. The result artifact is named by arm GENERATION so a
    # TVB-23 gate run can never overwrite the committed TVB-22 pin.
    arms = ("A1", "A2", "A3")
    args = list(argv)
    if "--arms" in args:
        i = args.index("--arms")
        arms = tuple(args[i + 1].split(","))
        del args[i : i + 2]
    unknown = [a for a in arms if a not in ARM_TWIN]
    if unknown:
        raise SystemExit(f"unknown arms {unknown}; known: {sorted(ARM_TWIN)}")
    coins = args or ["GOOGL", "TSLA", "DRAM"]
    results = []
    all_pass = True
    for coin in coins:
        for arm in arms:
            r = compare(coin, arm)
            results.append(r)
            all_pass &= r["pass"]
            status = "PASS" if r["pass"] else "MISMATCH"
            if "matched" not in r:
                print(f"{coin}/{arm}: {status} -- structural contract violations, join skipped")
            else:
                print(
                    f"{coin}/{arm}: {status} -- {r['matched']} events matched over "
                    f"{r['bars_replayed']} bars (twin_only {len(r['twin_only'])}, "
                    f"tv_only {len(r['tv_only'])}, offset {r['ts_offset_applied_s']}s, "
                    f"beyond_feed {r['tv_events_beyond_feed']}); "
                    f"break/flip max |dp| {r['price_exact_layer']['max_abs_delta']:.6g}; "
                    f"pattern layer {r['pattern_layer']['checked']} checked "
                    f"{len(r['pattern_layer']['violations'])} bad"
                )
                for k in r["twin_only"]:
                    print(f"  twin-only: {k['iso']} {k['action']} {k['dir']} {k['kind']}")
                for k in r["tv_only"]:
                    print(f"  tv-only:   {k['iso']} {k['action']} {k['dir']} {k['kind']}")
                for p in r["pattern_layer"]["violations"]:
                    print(f"  pattern:   {p}")
            for p in r.get("structural_violations", []):
                print(f"  violation: {p}")
    # Canonical-artifact protection (2026-08-16, TVB-24 audit F4): only the
    # exact declared 3x3 matrix may write the canonical generation artifact.
    # Any subset/reordering is a smoke run and writes a scope-named file, so
    # a passing 1-cell run can never replace the committed 9-cell pin.
    gen = "tvb22" if all(a.startswith("A") for a in arms) else "tvb23"
    canonical = tuple(coins) == CANONICAL_COINS and tuple(arms) == CANONICAL_ARMS[gen]
    if canonical:
        out = PKG / f"{gen}_parity_result.json"
    else:
        out = PKG / f"{gen}_parity_smoke_{'-'.join(arms)}_{'-'.join(coins)}.json"
        print(
            "SMOKE SCOPE: not the canonical "
            f"{CANONICAL_ARMS[gen]} x {CANONICAL_COINS} matrix -- "
            "writing a scope-named artifact, canonical pin untouched"
        )
    out.write_text(
        json.dumps(
            {
                "generated_utc": datetime.now(tz=timezone.utc).isoformat(),
                "gate": f"{gen.upper()} package-port parity (decision-exact + pattern layer)",
                "arms": list(arms),
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
