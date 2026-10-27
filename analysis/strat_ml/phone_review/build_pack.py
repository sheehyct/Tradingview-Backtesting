"""Data pack for the phone review page (page.html beside this file).

The page is published as a private claude.ai artifact (link not in the repo); it fetches one JSON
per coin from a data/ folder next to it: the coin's daily candles for its whole history, hourly
candles from HOURLY_FROM on (so the week and month "as of the trigger hour" can be rebuilt for the
anchor days), and every trade row of the corrected phase-3 event table for that coin with its
entry, stop, target, exit and outcome. Nothing is recomputed in the page: it draws the rows.

  uv run python -m analysis.strat_ml.phone_review.build_pack [--out analysis/strat_ml/data/phone_review] [--coins BTCUSDT ...]

Output is gitignored (the data/ rule); about 1.3-1.5 MB per coin. Publish page.html with the
data/*.json files beside it (the Artifact tool's `files` map) to refresh the page.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.domino.census import DAY, HOUR
from analysis.strat_ml import events as E
from analysis.strat_ml import report_v3 as v3
from analysis.strat_ml.binance_vision import DATA

DEFAULT_OUT = DATA / "phone_review"
COINS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ZECUSDT"]
HOURLY_FROM = "2024-10-01"
# the regime anchor days (phase 3 close-out, 2026-10-25): the whole market failed or ran together
ANCHORS = {
    "2024-11-04": "election eve: shorts everywhere failed",
    "2024-11-05": "election: longs ran",
    "2024-11-06": "election: longs ran",
    "2025-01-30": "longs everywhere failed",
    "2025-01-31": "longs everywhere failed",
    "2025-02-01": "tariff weekend: shorts ran",
    "2025-02-02": "tariff weekend: shorts ran",
    "2025-05-04": "shorts everywhere failed",
    "2025-05-05": "shorts failed",
    "2025-05-06": "shorts failed",
    "2025-05-07": "longs ran",
    "2025-05-08": "longs ran",
    "2025-09-18": "longs everywhere failed",
    "2025-10-10": "liquidation day: the shorts hit the week's level in hours",
    "2025-10-11": "inside day after the crash",
    "2025-10-12": "bounce longs into a red week and month",
    "2026-02-04": "day before the -14% close",
    "2026-02-05": "BTC -14% close",
    "2026-02-06": "day after",
    "2026-09-17": "longs ran",
}
FIELDS = [
    "id", "date", "dir", "pattern", "family", "trig", "hour", "level", "stop", "t1", "t1_src", "rr",
    "touch", "touch_h", "exit_t", "exit_px", "r_net", "r_gross", "cost_r", "atr5", "atr10", "pct5",
    "mfe", "mae", "week", "month", "wcol", "mcol", "tfc", "vol", "tier", "period", "note",
]  # fmt: skip


def _state(types: pd.Series, with_: np.ndarray, against: np.ndarray) -> np.ndarray:
    t = types.astype(str).to_numpy()
    return np.where(
        t == with_,
        "with",
        np.where(
            t == against,
            "against",
            np.where(t == "1", "inside", np.where(t == "3", "outside", "unknown")),
        ),
    )


def _f(v, nd=6):
    return (
        None
        if v is None or (isinstance(v, float) and np.isnan(v)) or pd.isna(v)
        else round(float(v), nd)
    )


def build(out: Path = DEFAULT_OUT, coins: list[str] | None = None, log=print) -> dict:
    coins = coins or COINS
    out.mkdir(parents=True, exist_ok=True)
    _, ev, _ = v3.load_corrected(log=lambda *a: None)
    roster = E._roster()
    ev = ev[ev["symbol"].isin(coins)].copy()
    ev["date"] = ev["day_ts"].dt.strftime("%Y-%m-%d")
    long = ev["direction"].astype(str) == "long"
    sign = np.where(long, 1.0, -1.0)
    with_, against = np.where(long, "2U", "2D"), np.where(long, "2D", "2U")
    ev["week"] = _state(ev["w_partial_type"], with_, against)
    ev["month"] = _state(ev["m_partial_type"], with_, against)
    touched = ev["first_touch"].isin(["stop", "target"])
    ev["exit_t"] = (
        np.where(
            touched,
            ev["trigger_time"] + ev["touch_hours"].fillna(0) * HOUR,
            ev["day"] + 10 * DAY + 23 * HOUR,
        )
        // 1000
    )
    ev["exit_px"] = np.where(
        ev["first_touch"] == "stop",
        ev["stop"],
        np.where(
            ev["first_touch"] == "target", ev["t1"], ev["level"] + sign * ev["r_close_10"] * ev["r"]
        ),
    )
    hourly_from_ms = pd.Timestamp(HOURLY_FROM, tz="UTC").value // 10**6
    sizes = {}
    for c in coins:
        g = ev[ev["symbol"] == c].sort_values("trigger_time")
        hf = E.hourly_frame(c, roster[c]["last_traded"])
        d = E.daily_from_hourly(hf)
        daily = [
            [int(t // 1000), _f(o), _f(h), _f(lo), _f(cl)]
            for t, o, h, lo, cl in zip(d["t"], d["o"], d["h"], d["l"], d["c"])
        ]
        hh = hf[hf["t"] >= hourly_from_ms]
        hourly = [
            [int(t // 1000), _f(o), _f(h), _f(lo), _f(cl)]
            for t, o, h, lo, cl in zip(hh["t"], hh["o"], hh["h"], hh["l"], hh["c"])
        ]
        trades = []
        for r in g.itertuples(index=False):
            trades.append(
                [
                    f"{c}-{r.date}-{r.direction[0]}", r.date, r.direction, r.pattern, r.family, int(r.trigger_time // 1000),
                    int(r.hours_since_daily_open), _f(r.level), _f(r.stop), _f(r.t1), r.t1_source, _f(r.t1_dist_r, 2),
                    r.first_touch, (int(r.touch_hours) if pd.notna(r.touch_hours) else None), int(r.exit_t), _f(r.exit_px),
                    _f(r.r10_net, 3), _f(r.r10, 3), _f(r.cost_r, 3), _f(r.net_atr_5, 2), _f(r.net_atr_10, 2), _f(r.net_pct_5, 2),
                    _f(r.mfe_r_10, 2), _f(r.mae_r_10, 2), r.week, r.month, int(r.w_bias), int(r.m_bias), float(r.tfc_score),
                    (str(r.btc_vol_tercile) if pd.notna(r.btc_vol_tercile) else None), (int(r.liq_tier) if pd.notna(r.liq_tier) else None),
                    "2020-24" if r.train else "2025-26", ANCHORS.get(r.date),
                ]
            )  # fmt: skip
        doc = {
            "coin": c,
            "name": c.replace("USDT", ""),
            "fields": FIELDS,
            "daily": daily,
            "hourly": hourly,
            "hourly_from": HOURLY_FROM,
            "trades": trades,
        }
        s = json.dumps(doc, separators=(",", ":"))
        (out / f"{c}.json").write_text(s, encoding="utf-8")
        sizes[c] = {
            "daily": len(daily),
            "hourly": len(hourly),
            "trades": len(trades),
            "mb": round(len(s) / 1e6, 2),
        }
        log(f"  {c}: {sizes[c]}")
    index = {
        "coins": [
            {"coin": c, "name": c.replace("USDT", ""), "file": f"data/{c}.json", **sizes[c]}
            for c in coins
        ],
        "anchors": ANCHORS,
        "built": pd.Timestamp.now("UTC").strftime("%Y-%m-%d"),
        "source": "phase-3 corrected event table (analysis/strat_ml), Binance USDT-M perps, UTC days",
    }
    (out / "index.json").write_text(json.dumps(index, separators=(",", ":")), encoding="utf-8")
    log(f"  index -> {out / 'index.json'}")
    return sizes


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--coins", nargs="*", default=None)
    a = ap.parse_args(argv)
    build(Path(a.out), a.coins)


if __name__ == "__main__":
    main(sys.argv[1:])
