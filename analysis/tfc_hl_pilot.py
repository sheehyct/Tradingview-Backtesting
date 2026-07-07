"""TVB-9 Phase 5a: xyz-MSTR-on-HL-bars pilot -- venue-bar drift calibration.

Runs the a-priori breadth cells (ctrlA M/W/D/60; R1E3 240/120/60 + M/W/D
stand_aside; R1E3+gov2) x fees {0, 0.0125% per fill} x slip {1, 10} ticks on
the SAME time window from two bar sources:

  TV chart bars   analysis/reference/tvb6_tv_xyzMSTR_60m.json  (gate substrate)
  HL venue candles analysis/reference/tvb6_hl_xyzMSTR_1h.json  (raw candleSnapshot)

and reports the paired economics drift. Purpose (TVB-9 directive): calibrate
the venue-bar drift band BEFORE any new-symbol HL-bar number is read, so a
surprising breadth number can be decomposed into bar-source effect vs symbol
effect.

Source choice: the committed TVB-6 HL 1h pull (captured 2026-07-03) reaches
back to 2025-12-07; HL's ~5,000-candle cap slides daily, so a fresh fetch
cannot reproduce that early window. The committed pull is therefore the HL
source; --network additionally live-fetches via tfc.providers and cross-checks
the interior overlap (exercises the breadth-pass instrument end to end and
records served-window/floor_hit meta).

Both committed files share a live-at-capture final bar (2026-07-03T19:00Z);
the common window drops it. Both sim runs inside a pair share identical
period-open seeds because the window is identical -- trimmed-window TV numbers
intentionally differ from the full-window gate-record numbers; the gate anchor
lines re-assert the full-window record separately.

Usage:
    uv run --no-sync python analysis/tfc_hl_pilot.py [--network] [--out FILE]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tfc.config import TFCConfig  # noqa: E402
from tfc.equivalence import compare_cell  # noqa: E402
from tfc.providers import fetch_hl, parse_hl_candles  # noqa: E402
from tfc.simulator import simulate  # noqa: E402
from tfc.tv_reference import REFERENCE_DIR, Bars, load_bars  # noqa: E402

TV_FILE = "tvb6_tv_xyzMSTR_60m.json"
HL_FILE = "tvb6_hl_xyzMSTR_1h.json"
HL_COIN = "xyz:MSTR"
MINTICK = 0.001  # HIP3XYZ:MSTRUSDC.P (committed tvb7_symbolinfo.json)

_FEE = 0.000125  # commission_value 0.0125 (percent per fill) as a rate

# The a-priori breadth cells (TVB-9 pre-registration grid; fixed from the record).
CELLS: dict[str, dict] = {
    "ctrlA": dict(chart_tf="60", exec_tfs=("M", "W", "D", "60")),
    "R1E3": dict(chart_tf="60", exec_tfs=("240", "120", "60"), reg_mode="stand_aside"),
    "R1E3gov2": dict(
        chart_tf="60",
        exec_tfs=("240", "120", "60"),
        reg_mode="stand_aside",
        gov_mode="ratchet",
    ),
}
FEES = (0.0, _FEE)
SLIPS = (1, 10)
GATE_ANCHOR_CELLS = ("ctrlA_0125_s1", "R1E3_0125_s1")


def iso(sec: int) -> str:
    return datetime.fromtimestamp(int(sec), tz=timezone.utc).isoformat().replace("+00:00", "Z")


def slice_bars(bars: Bars, t0: int, t1: int) -> Bars:
    keep = (bars.ts >= t0) & (bars.ts <= t1)
    return Bars(
        symbol=bars.symbol,
        interval=bars.interval,
        ts=bars.ts[keep],
        open=bars.open[keep],
        high=bars.high[keep],
        low=bars.low[keep],
        close=bars.close[keep],
        volume=bars.volume[keep],
    )


def bar_agreement(tv: Bars, hl: Bars) -> dict:
    """OHLCV agreement on the timestamp intersection + set differences."""
    common, ti, hi = np.intersect1d(tv.ts, hl.ts, return_indices=True)
    exact = 0
    worst_close_ticks = 0.0
    for a, b in zip(ti, hi):
        ohlc_eq = (
            tv.open[a] == hl.open[b]
            and tv.high[a] == hl.high[b]
            and tv.low[a] == hl.low[b]
            and tv.close[a] == hl.close[b]
        )
        vol_eq = abs(tv.volume[a] - hl.volume[b]) <= 1e-9 * max(1.0, hl.volume[b])
        if ohlc_eq and vol_eq:
            exact += 1
        worst_close_ticks = max(worst_close_ticks, abs(tv.close[a] - hl.close[b]) / MINTICK)
    return {
        "common": int(len(common)),
        "exact_ohlcv": int(exact),
        "exact_pct": round(100.0 * exact / len(common), 2),
        "worst_close_diff_ticks": round(worst_close_ticks, 3),
        "tv_only_bars": int(len(tv) - len(common)),
        "hl_only_bars": int(len(hl) - len(common)),
    }


def run_metrics(res) -> dict:
    pv = np.array([r["pv"] for r in res.closed])
    wins = pv[pv > 0.0]
    losses = pv[pv < 0.0]
    initial = res.final_equity - pv.sum()  # closed-trade chaining (equity chains pv)
    eq_path = np.r_[initial, initial + np.cumsum(pv)]
    peaks = np.maximum.accumulate(eq_path)
    maxdd = float(np.max(1.0 - eq_path / peaks)) if len(pv) else 0.0
    return {
        "net_pct": round(100.0 * res.net, 4),
        "trades": len(res.closed),
        "pf": round(float(wins.sum() / -losses.sum()), 4) if len(losses) else None,
        "win_pct": round(100.0 * len(wins) / len(pv), 2) if len(pv) else None,
        "maxdd_closed_pct": round(100.0 * maxdd, 2),
        "open_at_end": res.open_trade is not None,
    }


def trade_alignment(res_tv, res_hl) -> dict:
    """Are the two runs the SAME trades? Match closed trades by entry time."""
    tv_by_et = {r["et"]: r for r in res_tv.closed}
    hl_by_et = {r["et"]: r for r in res_hl.closed}
    common = sorted(set(tv_by_et) & set(hl_by_et))
    only_tv = sorted(set(tv_by_et) - set(hl_by_et))
    only_hl = sorted(set(hl_by_et) - set(tv_by_et))
    same_shape = sum(
        1
        for et in common
        if tv_by_et[et]["xt"] == hl_by_et[et]["xt"] and tv_by_et[et]["dir"] == hl_by_et[et]["dir"]
    )
    ep_diff = [abs(hl_by_et[et]["ep"] - tv_by_et[et]["ep"]) / MINTICK for et in common]
    xp_diff = [
        abs(hl_by_et[et]["xp"] - tv_by_et[et]["xp"]) / MINTICK
        for et in common
        if tv_by_et[et]["xt"] == hl_by_et[et]["xt"]
    ]
    unmatched = only_tv + only_hl
    return {
        "matched_et": len(common),
        "same_et_xt_dir": same_shape,
        "tv_only_trades": len(only_tv),
        "hl_only_trades": len(only_hl),
        "max_ep_diff_ticks": round(max(ep_diff), 3) if ep_diff else 0.0,
        "max_xp_diff_ticks": round(max(xp_diff), 3) if xp_diff else 0.0,
        "first_divergence": iso(min(unmatched) // 1000) if unmatched else None,
    }


def live_crosscheck(committed: Bars) -> dict:
    """Live HL fetch via tfc.providers vs the committed pull, interior overlap."""
    start_ms = int(committed.ts[0]) * 1000
    end_ms = int(time.time() * 1000)
    bars, meta = fetch_hl(HL_COIN, "1h", start_ms, end_ms)
    # interior overlap: exclude the committed capture's final (live) candle
    interior = committed.ts < committed.ts[-1]
    common, li, ci = np.intersect1d(bars.ts, committed.ts[interior], return_indices=True)
    mismatch = [
        int(common[k])
        for k, (a, b) in enumerate(zip(li, np.flatnonzero(interior)[ci]))
        if not (
            bars.open[a] == committed.open[b]
            and bars.high[a] == committed.high[b]
            and bars.low[a] == committed.low[b]
            and bars.close[a] == committed.close[b]
            and abs(bars.volume[a] - committed.volume[b]) <= 1e-9 * max(1.0, committed.volume[b])
        )
    ]
    return {
        "meta": meta,
        "overlap_bars": int(len(common)),
        "mismatched_bars": len(mismatch),
        "mismatched_ts": [iso(t) for t in mismatch[:10]],
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--network", action="store_true", help="also live-fetch HL and cross-check")
    ap.add_argument("--out", default=str(REFERENCE_DIR / "tvb9_hl_pilot_MSTR.json"))
    args = ap.parse_args(argv)

    tv_full = load_bars(TV_FILE)
    hl_raw = json.loads((REFERENCE_DIR / HL_FILE).read_text())
    hl_full = parse_hl_candles(hl_raw, HL_COIN, "60")

    # gate anchor: the full-window record must still hold before any pilot read
    anchors = {}
    for name in GATE_ANCHOR_CELLS:
        rep = compare_cell(name)
        anchors[name] = rep.passed
        print(f"gate anchor {name}: {'PASS' if rep.passed else 'FAIL'}")
    if not all(anchors.values()):
        print("ABORT: gate anchor failed -- no pilot number may be read")
        return 2

    # common window; drop the shared live-at-capture final bar
    t0 = int(max(tv_full.ts[0], hl_full.ts[0]))
    t1 = int(min(tv_full.ts[-1], hl_full.ts[-1]))
    tv = slice_bars(tv_full, t0, t1)
    hl = slice_bars(hl_full, t0, t1)
    assert tv.ts[-1] == hl.ts[-1] == t1, "expected shared final bar"
    tv = slice_bars(tv, t0, t1 - 1)
    hl = slice_bars(hl, t0, t1 - 1)
    window = {"start": iso(int(tv.ts[0])), "end": iso(int(max(tv.ts[-1], hl.ts[-1])))}
    print(f"common window {window['start']} .. {window['end']}  tv={len(tv)} hl={len(hl)} bars")

    agree = bar_agreement(tv, hl)
    print(
        f"bar agreement: {agree['exact_ohlcv']}/{agree['common']} exact OHLCV "
        f"({agree['exact_pct']}%), worst close diff {agree['worst_close_diff_ticks']} ticks, "
        f"tv-only {agree['tv_only_bars']}, hl-only {agree['hl_only_bars']}"
    )

    net_check = live_crosscheck(hl_full) if args.network else None
    if net_check:
        m = net_check["meta"]
        print(
            f"live fetch: served {iso(m['served_start_ms'] // 1000)} .. "
            f"{iso(m['served_end_ms'] // 1000)} ({m['served_count']} bars, "
            f"floor_hit={m['floor_hit']}); overlap {net_check['overlap_bars']} bars, "
            f"{net_check['mismatched_bars']} mismatched"
        )

    rows = []
    hdr = (
        f"{'cell':<9} {'fee':>7} {'slip':>4} | {'TV net%':>9} {'tr':>5} | "
        f"{'HL net%':>9} {'tr':>5} | {'d_net pp':>9} {'d_tr':>5}"
    )
    print(hdr)
    print("-" * len(hdr))
    for cell, kw in CELLS.items():
        for fee in FEES:
            for s in SLIPS:
                cfg = TFCConfig(comm_rate=fee, slip_ticks=s, mintick=MINTICK, **kw)
                res_tv = simulate(tv, cfg)
                res_hl = simulate(hl, cfg)
                mtv = run_metrics(res_tv)
                mhl = run_metrics(res_hl)
                align = trade_alignment(res_tv, res_hl)
                d_net = round(mhl["net_pct"] - mtv["net_pct"], 4)
                d_tr = mhl["trades"] - mtv["trades"]
                rows.append(
                    {
                        "cell": cell,
                        "fee_rate": fee,
                        "slip_ticks": s,
                        "tv": mtv,
                        "hl": mhl,
                        "delta_net_pp": d_net,
                        "delta_trades": d_tr,
                        "alignment": align,
                    }
                )
                fee_lbl = f"{fee * 100:.4f}".rstrip("0").rstrip(".")
                print(
                    f"{cell:<9} {fee_lbl:>7} {s:>4} | {mtv['net_pct']:>9.2f} "
                    f"{mtv['trades']:>5} | {mhl['net_pct']:>9.2f} {mhl['trades']:>5} | "
                    f"{d_net:>9.2f} {d_tr:>5} | et={align['matched_et']} "
                    f"etxt={align['same_et_xt_dir']} "
                    f"+tv{align['tv_only_trades']}/+hl{align['hl_only_trades']} "
                    f"ep<={align['max_ep_diff_ticks']}t xp<={align['max_xp_diff_ticks']}t"
                )

    doc = {
        "purpose": "TVB-9 Phase 5a venue-bar drift pilot (TV chart bars vs HL venue candles)",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources": {"tv": TV_FILE, "hl": HL_FILE, "mintick": MINTICK, "coin": HL_COIN},
        "window": window,
        "gate_anchor": anchors,
        "bar_agreement": agree,
        "live_crosscheck": net_check,
        "runs": rows,
    }
    Path(args.out).write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
