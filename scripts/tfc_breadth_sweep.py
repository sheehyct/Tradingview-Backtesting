"""TVB-9 Phase 5b: pre-registered breadth sweep on HL venue bars.

Pre-registration (BINDING): docs/TVB2_control_AB_rerun.md section "TVB-9:
breadth pre-registration (APPROVED by user 2026-07-07)". Universe, cells,
costs, and expectations are fixed there; this runner only executes them.
Deliverable is a regime ROUGH MAP -- no keep/kill verdicts off young listings.

Per symbol:
1. Bars: committed `analysis/reference/tvb9_hl_{slug}_1h.json` if present
   (idempotent -- HL's ~5,000-candle cap slides daily, so a re-fetch would
   silently change the window); else a fresh `tfc.providers.fetch_hl` pull
   saved there (COMMIT it: the pull is irreproducible evidence). floor_hit +
   served-vs-requested window travel in the artifact (plan risk 5).
2. mintick: TV symbolInfo via CDP (`tvb9_symbolinfo.json`, the approved
   primary), VALIDATED against the bars -- every OHLC price must sit on the
   mintick grid or the symbol is SKIPPED with a flag (pre-reg rule).
   qty_step: 10^-szDecimals from the HL meta (venue lot step; cross-checked
   MSTR = 0.001 = the calibrated gate value).
3. Cells: ctrlA / E3only / R1E3 / R1E3gov2 x fees {0, 0.0125%} x slip
   {1, 10} symbol ticks. Metrics from trades/equity directly; slip_bp and
   window regime descriptors (buy&hold, realized vol) recorded per run.

Usage:
    uv run --no-sync python scripts/tfc_breadth_sweep.py [--symbols xyz:MU ...]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis.tfc_hl_pilot import iso, run_metrics  # noqa: E402
from tfc.config import TFCConfig  # noqa: E402
from tfc.providers import fetch_hl, save_bars  # noqa: E402
from tfc.simulator import simulate  # noqa: E402
from tfc.tv_reference import REFERENCE_DIR, load_bars  # noqa: E402

HL_INFO_URL = "https://api.hyperliquid.xyz/info"
SYMBOLINFO_FILE = "tvb9_symbolinfo.json"
RESULTS_FILE = "tvb9_breadth_results.json"

# The pre-registered universe (a-priori; datasheet table is the record).
UNIVERSE: dict[str, dict] = {
    "xyz:MSTR": {"slug": "xyzMSTR", "role": "anchor crypto-adjacent", "dex": "xyz"},
    "xyz:XYZ100": {"slug": "xyzXYZ100", "role": "crypto index", "dex": "xyz"},
    "xyz:SP500": {"slug": "xyzSP500", "role": "equity index low-vol null", "dex": "xyz"},
    "BTC": {"slug": "BTC", "role": "dead control", "dex": ""},
    "xyz:MU": {"slug": "xyzMU", "role": "memory-cycle semi", "dex": "xyz"},
    "xyz:AMD": {"slug": "xyzAMD", "role": "large-cap semi", "dex": "xyz"},
    "xyz:NVDA": {"slug": "xyzNVDA", "role": "mega-cap semi", "dex": "xyz"},
    "xyz:TSLA": {"slug": "xyzTSLA", "role": "mega-cap high-vol", "dex": "xyz"},
    "xyz:CRCL": {"slug": "xyzCRCL", "role": "crypto-adjacent equity", "dex": "xyz"},
}

# The pre-registered cell grid.
CONFIGS: dict[str, dict] = {
    "ctrlA": dict(chart_tf="60", exec_tfs=("M", "W", "D", "60")),
    "E3only": dict(chart_tf="60", exec_tfs=("240", "120", "60")),
    "R1E3": dict(chart_tf="60", exec_tfs=("240", "120", "60"), reg_mode="stand_aside"),
    "R1E3gov2": dict(
        chart_tf="60",
        exec_tfs=("240", "120", "60"),
        reg_mode="stand_aside",
        gov_mode="ratchet",
    ),
}
FEES = (0.0, 0.000125)
SLIPS = (1, 10)


def hl_sz_decimals() -> dict[str, int]:
    """coin -> szDecimals (lot step 10^-szDecimals), main dex + xyz dex."""
    out: dict[str, int] = {}
    for dex in ("", "xyz"):
        body: dict = {"type": "meta"}
        if dex:
            body["dex"] = dex
        r = requests.post(HL_INFO_URL, json=body, timeout=30)
        r.raise_for_status()
        for a in r.json()["universe"]:
            out[a["name"]] = int(a["szDecimals"])
    return out


def load_symbolinfo() -> dict[str, dict]:
    """coin -> {tv_symbol, mintick, ...} from the committed TV CDP capture."""
    d = json.loads((REFERENCE_DIR / SYMBOLINFO_FILE).read_text())
    return {s["coin"]: s for s in d["symbols"]}


def get_bars(coin: str, slug: str):
    path = REFERENCE_DIR / f"tvb9_hl_{slug}_1h.json"
    if path.exists():
        bars = load_bars(path)
        meta = json.loads(path.read_text())["meta"]
        meta["from_committed_file"] = True
        return bars, meta
    end_ms = int(time.time() * 1000)
    bars, meta = fetch_hl(coin, "1h", 0, end_ms)
    save_bars(bars, meta, path)
    meta["from_committed_file"] = False
    print(f"  fetched + saved {path.name} ({len(bars)} bars, floor_hit={meta['floor_hit']})")
    return bars, meta


def grid_ok(bars, mintick: float) -> tuple[bool, float]:
    """Every OHLC price must sit on the mintick grid (worst residual in ticks)."""
    worst = 0.0
    for a in (bars.open, bars.high, bars.low, bars.close):
        resid = np.abs(a / mintick - np.rint(a / mintick))
        worst = max(worst, float(resid.max()))
    return worst < 1e-6, worst


def regime_descriptors(bars) -> dict:
    lr = np.diff(np.log(bars.close))
    return {
        "buyhold_pct": round(100.0 * (bars.close[-1] / bars.close[0] - 1.0), 2),
        "realized_vol_ann_pct": round(100.0 * float(lr.std() * np.sqrt(24 * 365)), 1),
        "median_close": float(np.median(bars.close)),
    }


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
        info = sinfo.get(coin)
        if info is None:
            print(f"{coin}: SKIP -- no TV symbolInfo captured")
            symbols_out[coin] = {"skipped": "no TV symbolInfo"}
            continue
        mintick = float(info["mintick"])
        base = coin.split(":")[-1]
        qty_step = 10.0 ** -szdec[coin if coin in szdec else base]
        bars, meta = get_bars(coin, u["slug"])
        # drop the live (still-forming) last bar
        bars = type(bars)(
            symbol=bars.symbol,
            interval=bars.interval,
            ts=bars.ts[:-1],
            open=bars.open[:-1],
            high=bars.high[:-1],
            low=bars.low[:-1],
            close=bars.close[:-1],
            volume=bars.volume[:-1],
        )
        ok, worst = grid_ok(bars, mintick)
        desc = regime_descriptors(bars)
        symbols_out[coin] = {
            "role": u["role"],
            "tv_symbol": info["tv_symbol"],
            "mintick": mintick,
            "mintick_source": "tv_symbolinfo_cdp",
            "qty_step": qty_step,
            "grid_ok": ok,
            "grid_worst_resid_ticks": worst,
            "provider_meta": meta,
            "window": {"start": iso(int(bars.ts[0])), "end": iso(int(bars.ts[-1]))},
            "bars": len(bars),
            "descriptors": desc,
        }
        if not ok:
            print(f"{coin}: SKIP -- prices off the TV mintick grid (worst {worst:.3g} ticks)")
            symbols_out[coin]["skipped"] = "mintick grid mismatch (pre-reg rule)"
            continue
        print(
            f"{coin}: {len(bars)} bars {iso(int(bars.ts[0]))} .. {iso(int(bars.ts[-1]))} "
            f"mintick {mintick} step {qty_step} floor_hit={meta['floor_hit']} "
            f"b&h {desc['buyhold_pct']}% vol {desc['realized_vol_ann_pct']}%"
        )
        for cell, kw in CONFIGS.items():
            for fee in FEES:
                for s in SLIPS:
                    cfg = TFCConfig(
                        comm_rate=fee, slip_ticks=s, mintick=mintick, qty_step=qty_step, **kw
                    )
                    m = run_metrics(simulate(bars, cfg))
                    slip_bp = 1e4 * s * mintick / desc["median_close"]
                    runs.append(
                        {
                            "symbol": coin,
                            "cell": cell,
                            "fee_rate": fee,
                            "slip_ticks": s,
                            "slip_bp": round(slip_bp, 3),
                            **m,
                        }
                    )
        r = [x for x in runs if x["symbol"] == coin and x["fee_rate"] > 0 and x["slip_ticks"] == 1]
        print(
            "   @0.0125 s1: "
            + "  ".join(f"{x['cell']} {x['net_pct']:+.2f}% ({x['trades']})" for x in r)
        )

    doc = {
        "purpose": "TVB-9 pre-registered breadth sweep (regime map; no verdicts)",
        "prereg": "docs/TVB2_control_AB_rerun.md: TVB-9 breadth pre-registration",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "symbols": symbols_out,
        "runs": runs,
    }
    Path(args.out).write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"wrote {args.out} ({len(runs)} runs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
