"""Venue data providers (Phase 4b): Hyperliquid candleSnapshot + OKX history-candles.

Both return the tfc Bars structure (bar OPEN, epoch seconds, UTC) plus a meta
dict that MUST travel with any run artifact built on the data. Plan caveats
baked in:
- HL serves only the most-recent ~5000 candles per interval: meta records the
  requested vs served window so a short history cannot masquerade as a long
  backtest (plan risk 5).
- OKX is fetched INTRADAY ONLY: OKX anchors its HTF candles to UTC+8, so
  D/W/M bars must be built locally with tfc.resample (UTC roll), never fetched.
- 24/7 perps: no calendar filtering anywhere (charter S2/S5).

Cache files use the tv_bars.mjs schema (symbol/interval/count/bars/firstISO/
lastISO) + a `meta` block, so tfc.tv_reference.load_bars reads them directly.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import requests

from tfc.tv_reference import Bars

__all__ = ["fetch_hl", "fetch_okx", "save_bars", "bars_from_rows"]

HL_INFO_URL = "https://api.hyperliquid.xyz/info"
OKX_HISTORY_URL = "https://www.okx.com/api/v5/market/history-candles"
OKX_PAGE_LIMIT = 100
OKX_THROTTLE_S = 0.15  # history-candles is rate-limited per IP; stay well under


def bars_from_rows(rows: list[list[float]], symbol: str, interval: str) -> Bars:
    """rows = [[epochSec, o, h, l, c, v], ...] ascending, unique."""
    a = np.asarray(rows, dtype=np.float64)
    ts = a[:, 0].astype(np.int64)
    if not np.all(np.diff(ts) > 0):
        raise AssertionError("provider rows not strictly increasing by open time")
    return Bars(
        symbol=symbol,
        interval=interval,
        ts=ts,
        open=a[:, 1],
        high=a[:, 2],
        low=a[:, 3],
        close=a[:, 4],
        volume=a[:, 5],
    )


def parse_hl_candles(candles: list[dict], coin: str, interval: str) -> Bars:
    """HL candleSnapshot payload -> Bars. Rows are {t: ms, o/h/l/c/v: str, n}."""
    rows = sorted(
        (
            [
                int(c["t"]) // 1000,
                float(c["o"]),
                float(c["h"]),
                float(c["l"]),
                float(c["c"]),
                float(c["v"]),
            ]
            for c in candles
        ),
        key=lambda r: r[0],
    )
    return bars_from_rows(rows, symbol=coin, interval=interval)


def fetch_hl(
    coin: str, interval: str, start_ms: int, end_ms: int, timeout: float = 30.0
) -> tuple[Bars, dict]:
    """POST /info candleSnapshot. interval: '15m','1h','4h','1d' (HL naming)."""
    body = {
        "type": "candleSnapshot",
        "req": {
            "coin": coin,
            "interval": interval,
            "startTime": int(start_ms),
            "endTime": int(end_ms),
        },
    }
    resp = requests.post(HL_INFO_URL, json=body, timeout=timeout)
    resp.raise_for_status()
    candles = resp.json()
    if not candles:
        raise RuntimeError(f"HL returned no candles for {coin} {interval}")
    bars = parse_hl_candles(candles, coin, interval)
    meta = {
        "source": "hyperliquid_candleSnapshot",
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "requested_start_ms": int(start_ms),
        "requested_end_ms": int(end_ms),
        "served_start_ms": int(bars.ts[0]) * 1000,
        "served_end_ms": int(bars.ts[-1]) * 1000,
        "served_count": len(bars),
        # the ~5000-candle cap: a served start AFTER the requested start means
        # the history floor was hit -- record it loudly
        "floor_hit": int(bars.ts[0]) * 1000 > int(start_ms) + 1,
    }
    return bars, meta


def parse_okx_pages(pages: list[list[list[str]]], inst_id: str, bar: str) -> Bars:
    """OKX history-candles pages (each newest-first) -> ascending deduped Bars.

    Row: [ts_ms, o, h, l, c, vol, volCcy, volCcyQuote, confirm].
    """
    by_ts: dict[int, list[float]] = {}
    for page in pages:
        for r in page:
            t = int(r[0]) // 1000
            by_ts[t] = [t, float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])]
    rows = [by_ts[t] for t in sorted(by_ts)]
    return bars_from_rows(rows, symbol=inst_id, interval=bar)


def fetch_okx(
    inst_id: str, bar: str, start_ms: int, end_ms: int, timeout: float = 30.0, max_pages: int = 400
) -> tuple[Bars, dict]:
    """GET history-candles paginated backwards from end_ms. INTRADAY bars only."""
    if any(x in bar for x in ("D", "W", "M", "Y")):
        raise ValueError(
            f"OKX HTF candles anchor UTC+8 -- fetch intraday only and resample "
            f"locally with tfc.resample (got bar='{bar}')"
        )
    pages: list[list[list[str]]] = []
    after = int(end_ms)
    for _ in range(max_pages):
        resp = requests.get(
            OKX_HISTORY_URL,
            params={
                "instId": inst_id,
                "bar": bar,
                "after": str(after),
                "limit": str(OKX_PAGE_LIMIT),
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("code") != "0":
            raise RuntimeError(f"OKX error {payload.get('code')}: {payload.get('msg')}")
        page = payload["data"]  # newest-first
        if not page:
            break
        pages.append(page)
        oldest = int(page[-1][0])
        if oldest <= start_ms:
            break
        after = oldest
        time.sleep(OKX_THROTTLE_S)
    else:
        raise RuntimeError(f"OKX pagination exceeded max_pages={max_pages}")
    if not pages:
        raise RuntimeError(f"OKX returned no candles for {inst_id} {bar}")
    bars = parse_okx_pages(pages, inst_id, bar)
    keep = (bars.ts * 1000 >= start_ms) & (bars.ts * 1000 <= end_ms)
    bars = Bars(
        symbol=bars.symbol,
        interval=bars.interval,
        ts=bars.ts[keep],
        open=bars.open[keep],
        high=bars.high[keep],
        low=bars.low[keep],
        close=bars.close[keep],
        volume=bars.volume[keep],
    )
    meta = {
        "source": "okx_history_candles",
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "requested_start_ms": int(start_ms),
        "requested_end_ms": int(end_ms),
        "served_start_ms": int(bars.ts[0]) * 1000,
        "served_end_ms": int(bars.ts[-1]) * 1000,
        "served_count": len(bars),
        "pages": len(pages),
        "floor_hit": int(bars.ts[0]) * 1000 > int(start_ms) + 1,
    }
    return bars, meta


def save_bars(bars: Bars, meta: dict, path: str | Path) -> None:
    """Persist in the tv_bars.mjs schema (+meta) so load_bars reads it back."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        [int(t), o, h, l, c, v]
        for t, o, h, l, c, v in zip(
            bars.ts, bars.open, bars.high, bars.low, bars.close, bars.volume
        )
    ]
    doc = {
        "symbol": bars.symbol,
        "pro_symbol": bars.symbol,
        "interval": bars.interval,
        "count": len(rows),
        "bars": rows,
        "firstISO": datetime.fromtimestamp(int(bars.ts[0]), tz=timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z"),
        "lastISO": datetime.fromtimestamp(int(bars.ts[-1]), tz=timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z"),
        "meta": meta,
    }
    path.write_text(json.dumps(doc), encoding="utf-8")
