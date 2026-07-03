"""Unit tests for analysis/fee_rates_by_dex.py (sanitized fee-rate summary).

Fixtures are SYNTHETIC FILL RECORDS for the parser/aggregator only (fee-field
plumbing, not market data): dex namespacing, `crossed` classification, rate math,
and the sanitization property that output rows carry counts and rates only.
"""

from analysis.fee_rates_by_dex import dex_of, render, summarize


def make_fill(coin, crossed, px, sz, fee):
    return {"coin": coin, "crossed": crossed, "px": px, "sz": sz, "fee": fee}


def test_dex_of_namespacing():
    assert dex_of("xyz:MSTR") == "xyz"
    assert dex_of("cash:AAPL") == "cash"
    assert dex_of("BTC") == "crypto"


def test_summarize_groups_and_rates():
    fills = [
        # xyz taker at 0.0086% of notional: fee = 0.000086 * (100 * 2)
        make_fill("xyz:MSTR", True, "100", "2", "0.0172"),
        make_fill("xyz:MSTR", True, "200", "1", "0.0172"),
        # xyz maker at 0.0029%
        make_fill("xyz:MSTR", False, "100", "1", "0.0029"),
        # native crypto taker at 0.0432%
        make_fill("BTC", True, "50000", "0.01", "0.216"),
    ]
    rows = summarize(fills)
    by_key = {(r["dex"], r["liquidity"]): r for r in rows}

    xyz_taker = by_key[("xyz", "taker")]
    assert xyz_taker["fills"] == 2
    assert abs(xyz_taker["modal_pct"] - 0.0086) < 1e-9
    assert abs(xyz_taker["notional_wtd_pct"] - 0.0086) < 1e-6

    assert by_key[("xyz", "maker")]["fills"] == 1
    assert abs(by_key[("crypto", "taker")]["modal_pct"] - 0.0432) < 1e-9


def test_summarize_skips_malformed_and_zero_notional():
    fills = [
        make_fill("xyz:MSTR", True, "100", "1", "0.0086"),
        make_fill("xyz:MSTR", True, "100", "0", "0.0"),  # zero notional
        {"coin": "xyz:MSTR", "crossed": True},  # missing fields
    ]
    rows = summarize(fills)
    counted = [r for r in rows if r["liquidity"] in ("taker", "maker")]
    skipped = [r for r in rows if r["liquidity"] == "-"]
    assert sum(r["fills"] for r in counted) == 1
    assert skipped and skipped[0]["fills"] == 2


def test_output_is_sanitized():
    fills = [make_fill("xyz:MSTR", True, "123.45", "81.5", "0.8653")]
    rows = summarize(fills)
    text = render(rows)
    # No absolute notionals or fee totals may appear -- only counts and rates.
    notional = 123.45 * 81.5
    assert f"{notional:.2f}" not in text
    assert "0.8653" not in text
    for row in rows:
        assert set(row) <= {
            "dex",
            "liquidity",
            "fills",
            "modal_pct",
            "mean_pct",
            "notional_wtd_pct",
        }
