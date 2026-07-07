"""TVB-9 HTF-index sweep: the regime set (M/W/D) as the entry/exit layer.

Pre-registration (BINDING, committed before this ran): docs/
TVB2_control_AB_rerun.md section "TVB-9: HTF-index pre-registration".
Hypothesis: the indices' 60m dead zone is a per-trade-magnitude problem;
stretching the holding horizon (M/W/D gate on 240m and 1D charts) lifts
per-trade gross above the fee floor. Cells MWD_on240 / MWD_onD, all 9
symbols, expectations H1-H5 declared first.

Windows per symbol:
- matched:  committed tvb9 1h pulls resampled to 240m and 1D (same windows
  as the 60m breadth sweep -- the primary comparison),
- native1d: HL 1d candles since listing (fetched once, committed --
  XYZ100 268d, BTC ~5.9y), cross-checked against the resampled 1D bars on
  interior complete days before use.

Usage:
    uv run --no-sync python scripts/tfc_htf_sweep.py [--symbols xyz:MU ...]
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

from analysis.tfc_hl_pilot import iso, run_metrics  # noqa: E402
from scripts.tfc_breadth_sweep import (  # noqa: E402
    UNIVERSE,
    get_bars,
    hl_sz_decimals,
    load_symbolinfo,
)
from tfc.config import TFCConfig  # noqa: E402
from tfc.providers import fetch_hl, save_bars  # noqa: E402
from tfc.resample import resample  # noqa: E402
from tfc.simulator import simulate  # noqa: E402
from tfc.tv_reference import REFERENCE_DIR, Bars, load_bars  # noqa: E402

RESULTS_FILE = "tvb9_htf_results.json"

CONFIGS: dict[str, dict] = {
    "MWD_on240": dict(chart_tf="240", exec_tfs=("M", "W", "D")),
    "MWD_onD": dict(chart_tf="D", exec_tfs=("M", "W", "D")),
}
FEES = (0.0, 0.000125)
SLIPS = (1, 10)


def drop_last(bars: Bars) -> Bars:
    return Bars(
        symbol=bars.symbol,
        interval=bars.interval,
        ts=bars.ts[:-1],
        open=bars.open[:-1],
        high=bars.high[:-1],
        low=bars.low[:-1],
        close=bars.close[:-1],
        volume=bars.volume[:-1],
    )


def get_native_1d(coin: str, slug: str):
    path = REFERENCE_DIR / f"tvb9_hl_{slug}_1d.json"
    if path.exists():
        return load_bars(path), json.loads(path.read_text())["meta"]
    bars, meta = fetch_hl(coin, "1d", 0, int(time.time() * 1000))
    save_bars(bars, meta, path)
    print(f"  fetched + saved {path.name} ({len(bars)} bars, floor_hit={meta['floor_hit']})")
    return bars, meta


def crosscheck_daily(res_d: Bars, nat_d: Bars) -> dict:
    """Resampled-from-1h vs native 1d on interior complete days."""
    interior = res_d.ts[1:-1]  # first day partial (mid-day window start), last trimmed
    common, ri, ni = np.intersect1d(interior, nat_d.ts, return_indices=True)
    ri = ri + 1  # offset back into res_d
    exact = sum(
        res_d.open[a] == nat_d.open[b]
        and res_d.high[a] == nat_d.high[b]
        and res_d.low[a] == nat_d.low[b]
        and res_d.close[a] == nat_d.close[b]
        for a, b in zip(ri, ni)
    )
    return {"common_days": int(len(common)), "exact_ohlc": int(exact)}


def metrics_plus(res) -> dict:
    m = run_metrics(res)
    app = np.abs([r["pp"] for r in res.closed])
    m["mean_abs_pp_pct"] = round(100.0 * float(app.mean()), 3) if len(app) else None
    m["median_abs_pp_pct"] = round(100.0 * float(np.median(app)), 3) if len(app) else None
    return m


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--symbols", nargs="*", default=list(UNIVERSE))
    ap.add_argument("--out", default=str(REFERENCE_DIR / RESULTS_FILE))
    args = ap.parse_args(argv)

    sinfo = load_symbolinfo()
    szdec = hl_sz_decimals()
    symbols_out: dict[str, dict] = {}
    runs: list[dict] = []

    for coin in args.symbols:
        u = UNIVERSE[coin]
        info = sinfo[coin]
        mintick = float(info["mintick"])
        base = coin.split(":")[-1]
        qty_step = 10.0 ** -szdec[coin if coin in szdec else base]

        h1, meta1 = get_bars(coin, u["slug"])
        h1 = drop_last(h1)
        m240 = resample(h1, "240")
        md = resample(h1, "D")
        nat, metad = get_native_1d(coin, u["slug"])
        nat = drop_last(nat)
        xc = crosscheck_daily(md, nat)
        bar_sets = {
            "matched_240": (m240, meta1),
            "matched_D": (md, meta1),
            "native1d_D": (nat, metad),
        }
        symbols_out[coin] = {
            "role": u["role"],
            "mintick": mintick,
            "qty_step": qty_step,
            "daily_crosscheck": xc,
            "windows": {
                k: {"start": iso(int(b.ts[0])), "end": iso(int(b.ts[-1])), "bars": len(b)}
                for k, (b, _) in bar_sets.items()
            },
        }
        print(
            f"{coin}: matched {len(m240)}x240m/{len(md)}x1D, native1d {len(nat)} "
            f"({iso(int(nat.ts[0]))[:10]}..), daily crosscheck {xc['exact_ohlc']}/{xc['common_days']} exact"
        )
        for setname, (bars, meta) in bar_sets.items():
            chart = "240" if setname == "matched_240" else "D"
            for cell, kw in CONFIGS.items():
                if kw["chart_tf"] != chart:
                    continue
                for fee in FEES:
                    for s in SLIPS:
                        cfg = TFCConfig(
                            comm_rate=fee, slip_ticks=s, mintick=mintick, qty_step=qty_step, **kw
                        )
                        m = metrics_plus(simulate(bars, cfg))
                        runs.append(
                            {
                                "symbol": coin,
                                "bar_set": setname,
                                "cell": cell,
                                "fee_rate": fee,
                                "slip_ticks": s,
                                "floor_hit": meta.get("floor_hit"),
                                **m,
                            }
                        )
        r = [x for x in runs if x["symbol"] == coin and x["fee_rate"] > 0 and x["slip_ticks"] == 1]
        print(
            "   @0.0125 s1: "
            + "  ".join(
                f"{x['bar_set']}/{x['cell']} {x['net_pct']:+.2f}% ({x['trades']}tr, "
                f"med|pp| {x['median_abs_pp_pct']}%)"
                for x in r
            )
        )

    doc = {
        "purpose": "TVB-9 HTF-index sweep (M/W/D as entry/exit layer; pre-registered H1-H5)",
        "prereg": "docs/TVB2_control_AB_rerun.md: TVB-9 HTF-index pre-registration",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "symbols": symbols_out,
        "runs": runs,
    }
    Path(args.out).write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"wrote {args.out} ({len(runs)} runs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
