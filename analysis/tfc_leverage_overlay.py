"""TVB-9 leverage-extreme overlay: survival-max isolated leverage + $500 account.

User request (2026-07-07): push leverage to the edge -- find the multiplier
where the position still survives the sample (even if barely) -- and show a
$500 small account run through the recorded 60m breadth cells.

METHOD (MAE-clearance, per the user's leverage philosophy: isolated margin =
defined-risk premium; leverage = capital-efficiency OUTPUT, not a return
dial). This is a POST-PROCESSING overlay on the gate-locked simulator's
trade lists -- the simulator itself is untouched (gate stays 8/8):

- Per closed trade, MAE vs entry from bar extremes over the exposure window
  (FULL entry bar through exit-bar-minus-1, plus the exit fill). Including
  the pre-fill part of the entry bar is deliberate conservatism.
- HL isolated liquidation: adverse fraction x_liq(L) = 1/L - mm, with
  mm = 1/(2*maxLeverage) (maintenance = half max-initial; maxLeverage per
  coin from the live HL meta). Survival-max L = 1/(worst_MAE + mm), per
  direction and combined.
- $500 account, 100%-of-equity as isolated margin each trade: equity
  compounds by (1 + L*pp) per trade (pp = calibrated cost-basis net return
  at 1x; fees scale with notional, so return-on-margin = L*pp). A trade
  whose MAE >= x_liq(L) LIQUIDATES: the posted margin is gone, account
  dead. Below HL's $10 min order notional the account is also dead.
- sample-Kelly L* = argmax sum log(1+L*pp) over the no-liquidation range
  (0.1 grid) -- reported ONLY as sample characterization.

APPROXIMATIONS (all recorded): qty-step re-quantization at small equity
ignored (~0.6% worst granularity on XYZ100 at $500); funding ignored and it
scales LINEARLY with L (TVB-7: MSTR slow cells ~-5pp at 1x over the sample
-> ~-25pp at 5x -- deployability math must charge it); liquidation uses bar
extremes of the LAST-trade price, not HL's mark price; partial-liq dust
ignored (death is total). EVERY survival/Kelly number here is IN-SAMPLE BY
CONSTRUCTION -- the sample-worst MAE is only the worst seen, not the worst
possible. Characterization, not sizing advice (charter S0).

Usage:
    uv run --no-sync python analysis/tfc_leverage_overlay.py [--out FILE]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis.tfc_hl_pilot import iso  # noqa: E402
from scripts.tfc_breadth_sweep import CONFIGS, UNIVERSE, load_symbolinfo  # noqa: E402
from tfc.config import TFCConfig  # noqa: E402
from tfc.simulator import simulate  # noqa: E402
from tfc.tv_reference import REFERENCE_DIR, Bars, load_bars  # noqa: E402

HL_INFO_URL = "https://api.hyperliquid.xyz/info"
RESULTS_FILE = "tvb9_leverage_overlay.json"
START_CASH = 500.0
MIN_NOTIONAL = 10.0  # HL minimum order value (USD)
FEE = 0.000125
BASE_LEVERS = (1.0, 2.0, 3.0, 5.0, 10.0)


def hl_max_leverage() -> dict[str, int]:
    out: dict[str, int] = {}
    for dex in ("", "xyz"):
        body: dict = {"type": "meta"}
        if dex:
            body["dex"] = dex
        r = requests.post(HL_INFO_URL, json=body, timeout=30)
        r.raise_for_status()
        for a in r.json()["universe"]:
            out[a["name"]] = int(a["maxLeverage"])
    return out


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


def trade_maes(bars: Bars, closed: list[dict]) -> np.ndarray:
    """Adverse excursion fraction vs entry, per closed trade."""
    idx = bars.index_of_ms()
    maes = np.empty(len(closed))
    for k, r in enumerate(closed):
        ie, ix = idx[r["et"]], idx[r["xt"]]
        if r["dir"] == "le":
            worst = min(float(bars.low[ie:ix].min()), r["xp"])
            maes[k] = max(0.0, (r["ep"] - worst) / r["ep"])
        else:
            worst = max(float(bars.high[ie:ix].max()), r["xp"])
            maes[k] = max(0.0, (worst - r["ep"]) / r["ep"])
    return maes


def account_path(pp: np.ndarray, maes: np.ndarray, lever: float, mm: float) -> dict:
    """$500 all-in-margin compounding at leverage `lever` with liquidation."""
    x_liq = 1.0 / lever - mm
    eq = START_CASH
    peak = eq
    maxdd = 0.0
    for k in range(len(pp)):
        if lever * eq < MIN_NOTIONAL:
            return {"final": round(eq, 2), "dead": "below $10 min notional", "at_trade": k}
        if maes[k] >= x_liq:
            return {"final": 0.0, "dead": "LIQUIDATED", "at_trade": k, "maxdd_pct": 100.0}
        eq *= 1.0 + lever * pp[k]
        if eq <= 0:
            return {"final": 0.0, "dead": "equity wiped", "at_trade": k, "maxdd_pct": 100.0}
        peak = max(peak, eq)
        maxdd = max(maxdd, 1.0 - eq / peak)
    return {"final": round(eq, 2), "dead": None, "maxdd_pct": round(100.0 * maxdd, 1)}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(REFERENCE_DIR / RESULTS_FILE))
    args = ap.parse_args(argv)

    sinfo = load_symbolinfo()
    maxlev = hl_max_leverage()
    rows = []

    for coin, u in UNIVERSE.items():
        info = sinfo[coin]
        ml = maxlev[coin if coin in maxlev else coin.split(":")[-1]]
        mm = 1.0 / (2.0 * ml)
        bars = drop_last(load_bars(f"tvb9_hl_{u['slug']}_1h.json"))
        for cell, kw in CONFIGS.items():
            cfg = TFCConfig(comm_rate=FEE, slip_ticks=1, mintick=float(info["mintick"]), **kw)
            res = simulate(bars, cfg)
            if not res.closed:
                continue
            pp = np.array([r["pp"] for r in res.closed])
            maes = trade_maes(bars, res.closed)
            dirs = np.array([r["dir"] for r in res.closed])
            worst_all = float(maes.max())
            worst_by = {
                d: (float(maes[dirs == d].max()) if (dirs == d).any() else None)
                for d in ("le", "se")
            }
            l_surv = 1.0 / (worst_all + mm)
            # sample-Kelly on the no-liq range
            grid = np.arange(0.1, min(l_surv, ml) + 1e-9, 0.1)
            growth = [
                (float(np.sum(np.log1p(lv * pp))) if (maes < 1.0 / lv - mm).all() else -np.inf)
                for lv in grid
            ]
            l_kelly = float(grid[int(np.argmax(growth))]) if len(grid) else None
            levers = sorted({*BASE_LEVERS, float(ml), round(min(l_surv * 0.99, ml), 1)} - {0.0})
            acct = {f"{lv:g}x": account_path(pp, maes, lv, mm) for lv in levers if lv >= 1.0}
            wk = int(np.argmax(maes))
            rows.append(
                {
                    "symbol": coin,
                    "cell": cell,
                    "venue_max_leverage": ml,
                    "mm_pct": round(100 * mm, 3),
                    "trades": len(pp),
                    "worst_mae_pct": round(100 * worst_all, 2),
                    "worst_mae_dir": str(dirs[wk]),
                    "worst_mae_date": iso(res.closed[wk]["et"] // 1000)[:10],
                    "worst_mae_by_dir_pct": {
                        d: (round(100 * v, 2) if v is not None else None)
                        for d, v in worst_by.items()
                    },
                    "survival_max_L": round(l_surv, 2),
                    "sample_kelly_L": l_kelly,
                    "account_500": acct,
                }
            )
            edge = acct.get(f"{round(min(l_surv * 0.99, ml), 1):g}x", {})
            print(
                f"{coin:<11} {cell:<9} worstMAE {100 * worst_all:5.2f}% ({str(dirs[wk])}) "
                f"L_surv {l_surv:5.2f} (venue max {ml}) kelly~{l_kelly} "
                f"$500@edge -> {edge.get('final')} {edge.get('dead') or ''}"
            )

    doc = {
        "purpose": "TVB-9 leverage-extreme overlay (survival-max L + $500 account)",
        "method": "MAE-clearance vs HL isolated liq (x_liq = 1/L - mm); see module docstring",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fee_rate": FEE,
        "start_cash": START_CASH,
        "rows": rows,
    }
    Path(args.out).write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"wrote {args.out} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
