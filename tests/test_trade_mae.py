"""Unit tests for analysis/trade_mae.py (MAE + margin-solvency helpers)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

from trade_mae import liq_threshold_short, max_survivable_leverage, trade_maes

MM = 0.05  # xyz:MSTR maxLev 10 -> maintenance 1/(2*10)

# bars: [t_ms, o, h, l, c]
BARS = [
    [1000, 100.0, 101.0, 99.0, 100.5],
    [2000, 100.5, 105.0, 100.0, 104.0],
    [3000, 104.0, 104.5, 95.0, 96.0],
    [4000, 96.0, 97.0, 94.0, 95.0],
]


def _t(et, xt, ep, d, **kw):
    return {"et": et, "xt": xt, "ep": ep, "dir": d, "open": False, **kw}


def test_short_mae_is_max_high_vs_entry():
    rows = trade_maes([_t(1000, 3000, 100.0, "se")], BARS)
    assert len(rows) == 1
    assert abs(rows[0]["mae"] - (105.0 / 100.0 - 1.0)) < 1e-12  # high on bar 2


def test_long_mae_is_min_low_vs_entry_and_span_is_inclusive():
    rows = trade_maes([_t(2000, 4000, 100.0, "le")], BARS)
    assert abs(rows[0]["mae"] - (1.0 - 94.0 / 100.0)) < 1e-12  # low on bar 4
    # span excludes bars outside [et, xt]
    rows2 = trade_maes([_t(2000, 2000, 100.0, "le")], BARS)
    assert abs(rows2[0]["mae"] - 0.0) < 1e-12  # bar-2 low 100.0 == entry


def test_open_and_malformed_trades_skipped():
    rows = trade_maes(
        [
            _t(1000, 2000, 100.0, "se"),
            {"et": 1000, "xt": 2000, "ep": 100.0, "dir": "se", "open": True},
            {"et": None, "xt": 2000, "ep": 100.0, "dir": "se", "open": False},
            _t(1000, 2000, None, "se"),
        ],
        BARS,
    )
    assert len(rows) == 1


def test_liquidation_thresholds_hl_model():
    # 1x short with mm=5% liquidates at +90.48% adverse
    assert abs(liq_threshold_short(1, MM) - (2.0 / 1.05 - 1.0)) < 1e-12
    assert abs(liq_threshold_short(2, MM) - (3.0 / 2.1 - 1.0)) < 1e-12
    # inverse: worst MAE exactly at the 1x threshold -> L_max == 1
    thr = liq_threshold_short(1, MM)
    assert abs(max_survivable_leverage(thr, MM) - 1.0) < 1e-9
    # tiny MAE -> huge survivable leverage
    assert max_survivable_leverage(0.001, MM) > 15
