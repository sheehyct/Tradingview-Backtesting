"""Tests for analysis/funding_model.py (event join and adjustment arithmetic)."""

from analysis.funding_model import summarize, trade_funding

EVENTS = [
    {"time": 1000, "fundingRate": 1e-4},
    {"time": 2000, "fundingRate": 2e-4},
    {"time": 3000, "fundingRate": -5e-4},
]


def test_window_half_open_et_exclusive_xt_inclusive():
    # event at et must be EXCLUDED, event at xt INCLUDED
    rows = trade_funding([{"et": 1000, "xt": 3000, "dir": "le", "pp": 0.0}], EVENTS)
    assert len(rows) == 1
    r = rows[0]
    assert r["n_events"] == 2  # 2000 and 3000; 1000 excluded
    assert abs(r["fund"] - (2e-4 - 5e-4)) < 1e-15


def test_sign_conventions_long_pays_short_receives():
    trades = [
        {"et": 500, "xt": 2500, "dir": "le", "pp": 0.0},
        {"et": 500, "xt": 2500, "dir": "se", "pp": 0.0},
    ]
    rows = trade_funding(trades, EVENTS)
    long_r, short_r = rows[0], rows[1]
    # window (500, 2500] -> events at 1000 and 2000, sum +3e-4
    assert abs(long_r["fund"] - 3e-4) < 1e-15  # long pays positive rates
    assert abs(short_r["fund"] + 3e-4) < 1e-15  # short receives (negative cost)


def test_open_and_malformed_rows_skipped():
    trades = [
        {"et": 500, "xt": 2500, "dir": "le", "pp": 0.01, "open": True},
        {"et": None, "xt": 2500, "dir": "le", "pp": 0.01},
        {"et": 500, "xt": 2500, "dir": "??", "pp": 0.01},
        {"et": 500, "xt": 2500, "dir": "se", "pp": 0.01},
    ]
    rows = trade_funding(trades, EVENTS)
    assert len(rows) == 1
    assert rows[0]["dir"] == "se"


def test_summarize_compounding_adjustment():
    rows = [
        {"pp": 0.10, "fund": 0.01, "n_events": 2},
        {"pp": -0.05, "fund": -0.02, "n_events": 1},
        {"pp": 0.03, "fund": 0.0, "n_events": 0},
    ]
    s = summarize(rows)
    assert s["n"] == 3
    assert s["n_with_events"] == 2
    base = 1.10 * 0.95 * 1.03 - 1.0
    adj = (1.0 + 0.10 - 0.01) * (1.0 - 0.05 + 0.02) * 1.03 - 1.0
    assert abs(s["base_ret"] - base) < 1e-12
    assert abs(s["adj_ret"] - adj) < 1e-12
    assert abs(s["fund_total_frac"] - (-0.01)) < 1e-12
