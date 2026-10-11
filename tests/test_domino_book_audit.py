"""Vectors added after the TVB-37 close-out Codex audit (docs/reviews/tvb37-close-codex-audit.md):
F1 zero-seeded drawdown, F2 R-matched coverage, F3 per-horizon denominators and greying (book,
chance tables, chart page), F8 strict JSON, plus the offline cached-universe rerun path.
"""

import json
import math

import numpy as np
import pandas as pd
import pytest

from analysis.domino import census, chance, chart_page
from analysis.domino.book import book_cell, matched_txt, r_matched, strict_json, table_r_matched


def _strict_loads(text: str) -> object:
    def refuse(token):
        raise ValueError(f"non-standard JSON token {token}")

    return json.loads(text, parse_constant=refuse)


# ----------------------------------------------------------------------------- F1 drawdown


def _book(dates, rets):
    return pd.DataFrame(
        {
            "date": dates,
            "ret5": rets,
            "rr5": [1.0 if r > 0 else -1.0 for r in rets],
            "out5": ["one_r" if r > 0 else "stop" for r in rets],
            "r_pct": [abs(r) for r in rets],
        }
    )


def test_drawdown_counts_a_loss_from_the_zero_start():  # F1
    # one losing trade of 2% on the 1,000-dollar unit: the book is 20 dollars under its start
    c, _ = book_cell(_book(["2026-01-01"], [-2.0]), 5)
    assert c["max_dd_usd"] == pytest.approx(-20.0)
    # 2% then 3% lost on two dates: 50 dollars under the start (the old formula said -30)
    c, cum = book_cell(_book(["2026-01-01", "2026-01-02"], [-2.0, -3.0]), 5)
    assert list(cum.round(2)) == [-20.0, -50.0]
    assert c["max_dd_usd"] == pytest.approx(-50.0)


def test_drawdown_unchanged_when_the_book_starts_positive():  # F1, the existing case
    c, _ = book_cell(_book(["2026-01-01", "2026-01-02", "2026-01-03"], [1.0, -3.0, 4.0]), 5)
    assert c["max_dd_usd"] == pytest.approx(-30.0)  # peak +10, trough -20
    c, _ = book_cell(_book(["2026-01-01", "2026-01-02"], [1.0, 2.0]), 5)
    assert c["max_dd_usd"] == 0.0  # never under water


# ----------------------------------------------------------------------------- F2 coverage


def _rm_frame(base_rows, stk_rows):
    df = pd.DataFrame(base_rows + stk_rows)
    df["tf"], df["kind"], df["flag"] = "D", "continuation", "none"
    return df


BASE30 = [{"cls": "plain", "r_pct": 10.0, "out3": "one_r" if k < 15 else "stop"} for k in range(30)]


def test_r_matched_disjoint_bins_is_unavailable_not_a_crash():  # F2
    stk = [{"cls": "near", "r_pct": 1.0, "out3": "one_r" if k < 5 else "stop"} for k in range(10)]
    r = r_matched(_rm_frame(BASE30, stk), "D", "continuation", "all", "stacked", 3)
    assert r["available"] is False and r["covered"] == 0.0 and r["n_effective"] == 0
    assert math.isnan(r["matched"]) and math.isnan(r["lo"]) and math.isnan(r["hi"])
    assert r["raw"] == pytest.approx(0.5 - 0.5)  # the raw gap is still defined
    assert matched_txt(r).startswith("unavailable")


def test_r_matched_partial_cover_is_conditional():  # F2
    stk = [{"cls": "near", "r_pct": 1.0, "out3": "stop"} for _ in range(9)]
    stk.append({"cls": "near", "r_pct": 10.0, "out3": "one_r"})  # the one unit with base support
    r = r_matched(_rm_frame(BASE30, stk), "D", "continuation", "all", "stacked", 3)
    assert r["available"] is True and r["conditional"] is True
    assert r["covered"] == pytest.approx(0.1) and r["n_effective"] == 1
    assert r["matched"] == pytest.approx(1.0 - 0.5)  # the covered bin's difference, renormalised
    se = math.sqrt(0.5 * 0.5 / 30)  # the stacked side has p=1 (zero variance)
    assert r["lo"] == pytest.approx(0.5 - 1.96 * se) and r["hi"] == pytest.approx(0.5 + 1.96 * se)
    assert r["raw"] == pytest.approx(0.1 - 0.5)
    assert "conditional on 10% of stacked" in matched_txt(r)


def test_r_matched_full_cover_is_not_conditional():
    stk = [{"cls": "near", "r_pct": 10.0, "out3": "one_r"} for _ in range(5)]
    r = r_matched(_rm_frame(BASE30, stk), "D", "continuation", "all", "stacked", 3)
    assert r["covered"] == 1.0 and r["conditional"] is False and r["n_effective"] == 5
    assert "conditional" not in matched_txt(r)


# ----------------------------------------------------------------------------- F3 denominators


def test_table_r_matched_greys_each_horizon_on_its_own_valid_count():  # F3
    # monthly reversal shape of the audit: 33 stacked valid by 3, only 27 by 5 (6 censored at 5)
    rows = [
        {
            "cls": "within1",
            "r_pct": 1.0 + k % 5,
            "out3": "one_r" if k % 3 else "stop",
            "out5": "stop",
        }
        for k in range(60)
    ]
    rows += [
        {
            "cls": "exact_shared",
            "r_pct": 1.0 + k % 5,
            "out3": "one_r" if k % 2 else "stop",
            "out5": "censored" if k < 6 else "one_r",
        }
        for k in range(33)
    ]
    df = pd.DataFrame(rows)
    df["tf"], df["kind"], df["flag"] = "M", "reversal", "none"
    lines, results = table_r_matched(df)
    row = next(ln for ln in lines if ln.startswith("| M | reversal | all | exact_shared |"))
    cols = [c.strip() for c in row.strip("|").split("|")]
    assert cols[4] == "within1 + spread"  # the base is named
    assert cols[5] == "33 / 27" and cols[6] == "60 / 60"  # valid counts at each horizon
    assert cols[7] == "100.0% / 100.0%"  # covered
    assert not cols[8].startswith("(") and not cols[9].startswith("(")  # 33 valid by 3: read
    assert cols[10].startswith("(") and cols[11].startswith("(")  # 27 valid by 5: greyed
    assert results  # the rows feed book.json


def _unit(cls, out, kind="reversal", flag="none", date="2026-01-05"):
    return {
        "tf": "D",
        "kind": kind,
        "flag": flag,
        "cls": cls,
        "date": date,
        "r_pct": 2.0,
        "stop0": False,
        "next_bar": "n/a",
        **{f"out{n}": out[i] for i, n in enumerate(chance.HORIZONS)},
        **{f"mfe{n}": 0.0 for n in chance.HORIZONS},
        **{f"mae{n}": 0.0 for n in chance.HORIZONS},
    }


def _chance_frame():
    rows = [_unit("plain", ("one_r", "one_r", "stop")) for _ in range(40)]
    rows += [_unit("plain", ("stop", "stop", "censored")) for _ in range(5)]
    rows += [_unit("exact_shared", ("one_r", "stop", "stop")) for _ in range(35)]
    rows += [_unit("exact_shared", ("stop", "censored", "censored")) for _ in range(10)]
    rows += [_unit("near", ("one_r", "one_r", "one_r")) for _ in range(31)]
    return pd.DataFrame(rows)


def test_chance_difference_rows_print_every_horizons_valid_count():  # F3
    lines = chance.table_differences(_chance_frame(), "D", "t")
    row = next(ln for ln in lines if "| reversal | all | exact_shared vs plain |" in ln)
    assert "45 (45 / 35 / 35)" in row  # exact shared: 45 units, valid 45 / 35 / 35
    assert "45 (45 / 45 / 40)" in row  # plain: 45 units, valid 45 / 45 / 40


def test_hypothesis1_own_chance_carries_its_interval():  # F3 / prereg A4
    lines = chance.table_hypothesis1(_chance_frame())
    row = next(ln for ln in lines if ln.startswith("| reversal | all |"))
    cols = [c.strip() for c in row.strip("|").split("|")]
    lo, hi = chance.wilson(35, 45)
    assert cols[3].split(" / ")[0] == f"77.8% [{100 * lo:.0f}, {100 * hi:.0f}] n=45"
    assert cols[2] == "45 (45 / 35 / 35)" and cols[4] == "45 (45 / 45 / 40)"
    assert cols[6] == "31 (31 / 31 / 31)"


# ----------------------------------------------------------------------------- F8 strict JSON


def test_strict_json_encodes_non_finite_values_and_open_bin_edges():  # F8
    stk = [{"cls": "near", "r_pct": 10.0, "out3": "one_r"} for _ in range(5)]
    r = r_matched(_rm_frame(BASE30, stk), "D", "continuation", "all", "stacked", 3)
    top = r["bins"][-1]
    assert top["r_to"] is None and top["r_to_unbounded"] is True
    assert all(b["r_to_unbounded"] is False for b in r["bins"][:-1])
    payload = {"r": r, "x": [math.nan, math.inf, -math.inf, np.float64(1.5), np.int64(3)]}
    text = json.dumps(strict_json(payload), allow_nan=False)
    back = _strict_loads(text)
    assert back["x"] == [None, None, None, 1.5, 3]
    assert back["r"]["bins"][-1]["r_to"] is None
    with pytest.raises(ValueError):
        json.dumps(payload, allow_nan=False)  # unnormalised, the strict writer refuses


# ----------------------------------------------------------------------------- chart page


def _write_results(tmp_path):
    chance_json = {
        "as_of_utc": "2026-10-10",
        "units": {"venue_era": 100},
        "cells": {
            "venue_era": [
                {
                    "tf": "D",
                    "kind": "reversal",
                    "flag": "all",
                    "cls": "plain",
                    "n": 100,
                    "n3": 25,
                    "one_r3": 0.4,
                    "lo3": 0.2,
                    "hi3": 0.6,
                    "stop3": 0.5,
                },
                {
                    "tf": "D",
                    "kind": "inside",
                    "flag": "all",
                    "cls": "plain",
                    "n": 100,
                    "n3": 90,
                    "one_r3": 0.4,
                    "lo3": 0.3,
                    "hi3": 0.5,
                    "stop3": 0.5,
                },
            ]
        },
    }
    rm = {
        "flag": "all",
        "n_stacked": 40,
        "raw": -0.05,
        "matched": -0.03,
        "lo": -0.1,
        "hi": 0.04,
        "n_effective": 36,
        "covered": 0.9,
        "available": True,
        "conditional": True,
    }
    book_json = {
        "unit_usd": 1000.0,
        "cells": [
            {
                "tf": "D",
                "kind": "reversal",
                "flag": "all",
                "cls": "plain",
                "h5": {
                    "n": 20,
                    "avg_pct": -0.1,
                    "hit": 0.3,
                    "stop": 0.5,
                    "exp_r": -0.1,
                    "total_usd": -20.0,
                    "max_dd_usd": -40.0,
                    "avg_r_pct": 2.0,
                },
            }
        ],
        "curves": {},
        "r_matched": [
            rm
            | {
                "tf": "W",
                "kind": "continuation",
                "cls": "exact_shared",
                "base": "within1 + spread",
            },
            rm
            | {
                "tf": "D",
                "kind": "continuation",
                "cls": "stacked",
                "base": "plain",
                "conditional": False,
                "covered": 1.0,
                "n_effective": 40,
            },
            rm
            | {
                "tf": "D",
                "kind": "inside",
                "cls": "near",
                "base": "plain",
                "available": False,
                "conditional": False,
                "covered": 0.0,
                "n_effective": 0,
                "matched": None,
                "lo": None,
                "hi": None,
            },
        ],
    }
    (tmp_path / "chance.json").write_text(json.dumps(chance_json))
    (tmp_path / "book.json").write_text(json.dumps(book_json, allow_nan=False))


def test_chart_page_uses_valid_counts_small_cells_and_named_bases(tmp_path):  # F3, F4, F2
    _write_results(tmp_path)
    data = chart_page.build_data(tmp_path)
    rev = data["daily"]["reversal"]["plain"]
    assert rev["n"] == 25 and rev["small"] is True  # valid by 3, not the 100 units
    assert data["daily"]["inside"]["plain"]["small"] is False
    assert data["book"][0]["small"] is True
    w, d, u = data["matched"]
    assert "vs the rest (within 1% + spread)" in w["label"] and "conditional on 90%" in w["label"]
    assert d["label"].endswith("vs plain") and d["base"] == "plain"
    assert "unavailable" in u["label"] and u["matched"] is None
    json.dumps(data, allow_nan=False)  # the page payload is strict too


# ----------------------------------------------------------------------------- offline rerun


def test_cached_universe_reads_the_stamp_and_maps_the_xyz_prefix(tmp_path, monkeypatch):
    for name in ("BTC", "xyz_AAPL", "ETH"):
        (tmp_path / f"{name}_1d_20261010.json").write_text("[]")
    (tmp_path / "SOL_1d_20261011.json").write_text("[]")  # another day's snapshot: ignored
    monkeypatch.setattr(census, "CACHE", tmp_path)  # the helper moved into census (TVB-38)
    uni = chance.cached_universe(chance.parse_as_of("2026-10-10"))
    assert uni == [
        {"coin": "BTC", "dex": "main"},
        {"coin": "ETH", "dex": "main"},
        {"coin": "xyz:AAPL", "dex": "xyz"},
    ]
    with pytest.raises(FileNotFoundError):
        chance.cached_universe(chance.parse_as_of("2026-10-09"))
