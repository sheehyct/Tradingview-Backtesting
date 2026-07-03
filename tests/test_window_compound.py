"""Unit tests for analysis/window_compound.py (kind-window compounding method)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

from window_compound import compound_window


def _t(et, pp, d, is_open=False):
    return {"et": et, "pp": pp, "dir": d, "open": is_open}


def test_compound_basic_product():
    trades = [_t(1000, 0.10, "le"), _t(2000, -0.05, "se")]
    r = compound_window(trades)
    assert r["n"] == 2 and r["le"] == 1 and r["se"] == 1
    assert abs(r["ret"] - (1.10 * 0.95 - 1.0)) < 1e-12
    assert abs(r["ret_le"] - 0.10) < 1e-12
    assert abs(r["ret_se"] - (-0.05)) < 1e-12


def test_window_filter_is_entry_time_half_open():
    trades = [_t(1000, 0.10, "le"), _t(2000, 0.10, "le"), _t(3000, 0.10, "le")]
    r = compound_window(trades, start_ms=2000, end_ms=3000)
    assert r["n"] == 1  # start inclusive, end exclusive


def test_open_and_malformed_rows_excluded():
    trades = [
        _t(1000, 0.10, "le"),
        _t(2000, 0.50, "le", is_open=True),  # mark-to-market row
        {"et": None, "pp": 0.2, "dir": "le", "open": False},
        {"et": 3000, "pp": None, "dir": "se", "open": False},
    ]
    r = compound_window(trades)
    assert r["n"] == 1
    assert abs(r["ret"] - 0.10) < 1e-12
