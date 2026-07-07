"""Phase-4b provider tests.

Offline: parsing, pagination merge, cache round-trip, the OKX HTF guard.
Network (opt-in: TFC_NETWORK=1): live HL fetch cross-checked against the
committed tvb6 HL candles on their overlap; live OKX pagination sanity.
The default suite stays deterministic and offline.
"""

import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tfc.providers import (  # noqa: E402
    bars_from_rows,
    fetch_hl,
    fetch_okx,
    parse_hl_candles,
    parse_okx_pages,
    save_bars,
)
from tfc.tv_reference import REFERENCE_DIR, load_bars  # noqa: E402

NETWORK = os.environ.get("TFC_NETWORK") == "1"


def test_parse_hl_candles_sorts_and_converts():
    candles = [
        {
            "t": 1764688500000,
            "o": "183.12",
            "h": "183.5",
            "l": "182.9",
            "c": "183.3",
            "v": "10.5",
            "n": 3,
        },
        {
            "t": 1764687600000,
            "o": "181.95",
            "h": "183.2",
            "l": "181.05",
            "c": "183.12",
            "v": "1296.743",
            "n": 9,
        },
    ]
    bars = parse_hl_candles(candles, "xyz:MSTR", "15m")
    assert list(bars.ts) == [1764687600, 1764688500]
    assert bars.open[0] == 181.95 and bars.volume[0] == 1296.743


def test_parse_okx_pages_dedup_ascending():
    p1 = [
        ["1764688500000", "183.12", "183.5", "182.9", "183.3", "10.5", "0", "0", "1"],
        ["1764687600000", "181.95", "183.2", "181.05", "183.12", "1296.7", "0", "0", "1"],
    ]
    p2 = [
        ["1764687600000", "181.95", "183.2", "181.05", "183.12", "1296.7", "0", "0", "1"],
        ["1764686700000", "181.0", "182.0", "180.9", "181.9", "50.0", "0", "0", "1"],
    ]
    bars = parse_okx_pages([p1, p2], "MSTR-USDT-SWAP", "15m")
    assert list(bars.ts) == [1764686700, 1764687600, 1764688500]  # deduped, ascending


def test_okx_htf_guard():
    with pytest.raises(ValueError, match="UTC\\+8"):
        fetch_okx("MSTR-USDT-SWAP", "1D", 0, 1)


def test_save_bars_round_trips_through_load_bars(tmp_path):
    bars = bars_from_rows(
        [
            [1764687600, 181.95, 183.2, 181.05, 183.12, 1296.743],
            [1764688500, 183.12, 183.5, 182.9, 183.3, 10.5],
        ],
        symbol="xyz:MSTR",
        interval="15",
    )
    p = tmp_path / "cache_test.json"
    save_bars(bars, {"source": "unit"}, p)
    back = load_bars(p)
    assert list(back.ts) == list(bars.ts)
    assert back.open[0] == bars.open[0] and back.volume[1] == bars.volume[1]
    assert json.loads(p.read_text())["meta"]["source"] == "unit"


@pytest.mark.network
@pytest.mark.skipif(not NETWORK, reason="set TFC_NETWORK=1 for live venue fetches")
def test_live_hl_matches_committed_overlap():
    # the committed HL pull is the RAW candleSnapshot list, not tv_bars schema
    raw = json.loads((REFERENCE_DIR / "tvb6_hl_xyzMSTR_15m.json").read_text())
    ref = parse_hl_candles(raw, "xyz:MSTR", "15m")
    # a 2-day slice well inside both the committed window and HL's ~5000-candle floor
    start_ms = 1782000000 * 1000  # 2026-06-21T00:00:00Z
    end_ms = start_ms + 2 * 86400 * 1000
    bars, meta = fetch_hl("xyz:MSTR", "15m", start_ms, end_ms)
    common, ai, ri = np.intersect1d(bars.ts, ref.ts, return_indices=True)
    assert len(common) >= 150  # placeholder asymmetry allows a few gaps
    exact = sum(
        bars.open[a] == ref.open[r]
        and bars.high[a] == ref.high[r]
        and bars.low[a] == ref.low[r]
        and bars.close[a] == ref.close[r]
        and abs(bars.volume[a] - ref.volume[r]) <= 1e-9 * max(1.0, ref.volume[r])
        for a, r in zip(ai, ri)
    )
    assert exact == len(common), f"{len(common) - exact} overlap rows differ"


@pytest.mark.network
@pytest.mark.skipif(not NETWORK, reason="set TFC_NETWORK=1 for live venue fetches")
def test_live_okx_pagination_sanity():
    end_ms = 1783000000 * 1000  # fixed historical endpoint: 2026-07-02T13:46:40Z
    start_ms = end_ms - 3 * 86400 * 1000
    bars, meta = fetch_okx("MSTR-USDT-SWAP", "15m", start_ms, end_ms)
    assert meta["pages"] >= 2  # forced multi-page (288 bars / 100)
    assert len(bars) >= 250
    assert np.all(np.diff(bars.ts) > 0)
    assert np.all(np.diff(bars.ts) % 900 == 0)
    ticks = np.rint(bars.close / 0.01)  # OKX MSTR mintick 0.01 (tvb7_symbolinfo)
    assert np.allclose(ticks * 0.01, bars.close, atol=1e-9)
