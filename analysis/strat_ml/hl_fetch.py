"""Hyperliquid xyz-dex (HIP-3 equity perps) hourly candles into the vessel's parquet cache.

The venue serves ~5000 candles per interval (about 208 days of hourly bars), so the equity-perp
rows are a short window by construction; the roster records what was served. Uses the census's
own fetcher (`analysis/domino/census.fetch_hourly`, cached under analysis/domino/data) and
writes one parquet per coin in the Binance klines schema so `events.py` runs unchanged.
Symbol id = 'XYZ_' + name (the venue's 'xyz:NAME'). No funding (NaN), no quote volume beyond
price * volume. Research only; no keys, no orders.

  uv run python -m analysis.strat_ml.hl_fetch
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone

import pandas as pd

from analysis.domino import census
from analysis.strat_ml.binance_vision import HERE, PARQUET, parquet_path

ROSTER_PATH = HERE / "xyz_summary.json"

# session classes, by hand, for the regular-hours reading (unknowns stay out of that comparison)
US_LISTED = {
    "TSLA",
    "NVDA",
    "HOOD",
    "INTC",
    "PLTR",
    "COIN",
    "META",
    "AAPL",
    "MSFT",
    "ORCL",
    "GOOGL",
    "AMZN",
    "AMD",
    "MU",
    "SNDK",
    "MSTR",
    "CRCL",
    "NFLX",
    "COST",
    "LLY",
    "TSM",
    "RIVN",
    "BABA",
    "USAR",
    "CRWV",
    "URNM",
    "GME",
    "EWY",
    "EWJ",
    "HIMS",
    "DKNG",
    "LITE",
    "XLE",
    "BX",
    "MRVL",
    "RKLB",
    "EWZ",
    "ZM",
    "EBAY",
    "ARM",
    "EWT",
    "ASML",
    "DELL",
    "IBM",
    "AVGO",
    "NOW",
    "NBIS",
    "WDC",
    "NOK",
    "SMH",
    "BE",
    "QCOM",
    "STRC",
    "AMAT",
    "GEV",
    "KORU",
    "SOXL",
    "MAGS",
    "IREN",
    "NET",
    "CRWD",
    "RDDT",
    "AAOI",
    "MRNA",
    "XBI",
    "BMNR",
    "CVX",
    "TLT",
    "OURA",
    "LRCX",
    "UMC",
    "TWST",
    "GLW",
    "XYZ100",
    "SP500",
    "BB",
    "QNT",
}
NON_US_LISTED = {
    "SMSN",
    "HYUNDAI",
    "KIOXIA",
    "SOFTBANK",
    "SKHX",
    "SKHY",
    "CXMT",
    "CAMBRICON",
    "GIGADEV",
    "UNITREE",
    "ZHIPU",
    "SHAZ",
    "MINIMAX",
    "SHEIN",
    "KR200",
    "JP225",
}
COMMODITY_FX = {
    "GOLD",
    "SILVER",
    "JPY",
    "EUR",
    "GBP",
    "CL",
    "COPPER",
    "NATGAS",
    "PLATINUM",
    "PALLADIUM",
    "BRENTOIL",
}


def session_class(name: str) -> str:
    if name in US_LISTED:
        return "us_listed"
    if name in NON_US_LISTED:
        return "non_us_listed"
    if name in COMMODITY_FX:
        return "commodity_fx"
    return "unknown"


def main(argv: list[str] | None = None) -> None:
    now_ms = int(time.time() * 1000)
    xyz = [u for u in census.universe() if u["dex"] == "xyz"]
    rows = {}
    (PARQUET / "klines").mkdir(parents=True, exist_ok=True)
    for n, u in enumerate(xyz, 1):
        coin = u["coin"]
        name = coin.split(":", 1)[1]
        sym = "XYZ_" + name
        try:
            raw = census.fetch_hourly(coin, now_ms)
        except Exception as e:  # keep going; the roster records the miss
            print(f"  {coin}: fetch failed: {e}", flush=True)
            continue
        if not raw:
            continue
        df = (
            pd.DataFrame(
                {
                    "open_time": pd.to_datetime([int(r["t"]) for r in raw], unit="ms", utc=True),
                    "open": [float(r["o"]) for r in raw],
                    "high": [float(r["h"]) for r in raw],
                    "low": [float(r["l"]) for r in raw],
                    "close": [float(r["c"]) for r in raw],
                    "volume": [float(r.get("v", 0.0)) for r in raw],
                }
            )
            .drop_duplicates("open_time")
            .sort_values("open_time")
        )
        df["close_time"] = df["open_time"] + pd.Timedelta(hours=1) - pd.Timedelta(milliseconds=1)
        df["quote_volume"] = df["volume"] * df["close"]
        df["count"] = pd.array([r.get("n", 0) for r in raw][: len(df)], dtype="Int64")
        df["taker_buy_volume"] = float("nan")
        df["taker_buy_quote_volume"] = float("nan")
        df.to_parquet(parquet_path("klines", sym), index=False)
        traded = df[df["volume"] > 0]
        rows[sym] = {
            "venue_coin": coin,
            "session_class": session_class(name),
            "first_bar": df["open_time"].iloc[0].isoformat(),
            "last_bar": df["open_time"].iloc[-1].isoformat(),
            "last_traded": traded["open_time"].iloc[-1].isoformat() if len(traded) else None,
            "bars": int(len(df)),
            "zero_volume_hours": int((df["volume"] <= 0).sum()),
        }
        if n % 20 == 0 or n == len(xyz):
            print(f"  [{n}/{len(xyz)}] {sym} {len(df)} hours", flush=True)
    doc = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "venue": "hyperliquid xyz dex (HIP-3)",
        "symbols": len(rows),
        "by_class": {
            k: sum(1 for r in rows.values() if r["session_class"] == k)
            for k in ("us_listed", "non_us_listed", "commodity_fx", "unknown")
        },
        "rows": rows,
    }
    ROSTER_PATH.write_text(json.dumps(doc, indent=1, sort_keys=True), encoding="utf-8")
    print(f"{len(rows)} coins -> {ROSTER_PATH}; classes {doc['by_class']}")


if __name__ == "__main__":
    main(sys.argv[1:])
