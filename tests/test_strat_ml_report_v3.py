"""Hand-vector tests for analysis/strat_ml/report_v3.py and m15_check.py (no network, no cache)."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from analysis.domino.census import DAY, HOUR
from analysis.strat_ml import m15_check as m15
from analysis.strat_ml import report_v3 as v3

ROOT = Path(__file__).resolve().parents[1]


def test_glossary_is_verbatim_from_the_brief():
    txt = (ROOT / "docs/experiments/strat_ml_phase3_brief.md").read_text(encoding="utf-8")
    sec = txt.split("## Glossary in trader terms", 1)[1].split("\n## ", 1)[0]
    rows = []
    for line in sec.splitlines():
        if line.startswith("| ") and not line.startswith("| term") and not line.startswith("| ---"):
            rows.append(tuple(c.strip() for c in line.strip().strip("|").split(" | ")))
    assert rows == list(v3.GLOSSARY_ROWS)
    assert len(rows) == 18


def test_table_helper_refuses_without_texts():
    doc = v3.Doc("t")
    df = pd.DataFrame({"n": [1], "mean_r": [0.1]})
    with pytest.raises(ValueError):
        doc.table("k", df, what="", verdict="Verdict: supports -- x, because y.")
    with pytest.raises(ValueError):
        doc.table("k", df, what="one row is ...", verdict="")
    with pytest.raises(ValueError):
        doc.table("k", df, what="one row is ...", verdict="supports -- missing the prefix")
    doc.table("k", df, what="one row is ...", verdict="Verdict: supports -- x, because y.")
    h = doc.html()
    assert "What this means." in h and "Verdict: supports" in h
    md = doc.md()
    assert "| n | mean R no stop |" in md and "*Verdict: supports -- x, because y.*" in md


def test_grey_rows_under_300():
    doc = v3.Doc("t")
    df = pd.DataFrame({"family": ["a", "b"], "n": [299, 300], "mean_r": [0.1, 0.2]})
    doc.table("k", df, what="w", verdict="Verdict: inconclusive -- h, because n.")
    h = doc.html()
    assert "<tr class=grey>" in h and h.count("<tr class=grey>") == 1
    md = doc.md()
    assert "| (a) | (299) | (+0.100) |" in md and "| b | 300 | +0.200 |" in md


def test_clustered_mean_hand_vector():
    # two clusters: day 1 holds [1, 1, 1], day 2 holds [-1]; mean 0.5
    x = np.array([1.0, 1.0, 1.0, -1.0])
    cl = np.array([1, 1, 1, 2])
    cs = v3.clustered_mean(x, cl)
    assert cs["n"] == 4 and cs["days"] == 2 and cs["mean"] == 0.5
    # residual sums: day 1 = 1.5, day 2 = -1.5 -> se = sqrt(1.5^2 + 1.5^2) / 4
    assert abs(cs["se"] - np.sqrt(4.5) / 4) < 1e-12
    assert abs(cs["z"] - 0.5 / (np.sqrt(4.5) / 4)) < 1e-9
    # with one row per cluster it is the ordinary (population) standard error
    cs2 = v3.clustered_mean(x, np.arange(4))
    assert abs(cs2["se"] - x.std() / 2) < 1e-12
    # NaN rows are dropped
    cs3 = v3.clustered_mean(np.array([1.0, np.nan]), np.array([1, 2]))
    assert cs3["n"] == 1 and cs3["days"] == 1


def test_verdict_line_forms():
    hyp = "drift exists"
    assert v3.verdict_line(hyp, [("a", 0.1, 2.5, 1000)]).startswith(
        "Verdict: supports -- drift exists, because a +0.100 ATR, z +2.5, n 1,000"
    )
    assert v3.verdict_line(hyp, [("a", -0.1, -2.5, 1000)]).startswith("Verdict: contradicts --")
    assert v3.verdict_line(hyp, [("a", 0.1, 1.0, 1000)]).startswith("Verdict: inconclusive --")
    assert v3.verdict_line(hyp, [("a", 0.1, 5.0, 100)]).startswith(
        "Verdict: inconclusive --"
    )  # under 300 rows never quoted
    mixed = v3.verdict_line(hyp, [("a", 0.1, 2.5, 1000), ("b", -0.1, -3.0, 1000)])
    assert mixed.startswith("Verdict: supports for a; contradicts for b --")


def test_base_asset_and_stable_names():
    assert v3.base_asset("USDCUSDT") == "USDC" and "USDC" in v3.STABLE_BASES
    assert v3.base_asset("BTCUSDT") == "BTC" and "BTC" not in v3.STABLE_BASES
    assert v3.base_asset("XYZ_AAPL") == "XYZ_AAPL"


def _events(n_funding_marks=4):
    """Two rows (one long, one short) on one coin with a known funding series."""
    day = 19000 * DAY
    trig = day + 5 * HOUR
    return pd.DataFrame(
        {
            "symbol": ["AAAUSDT", "AAAUSDT"],
            "asset_class": ["alt", "alt"],
            "direction": ["long", "short"],
            "liq_tier": [1.0, np.nan],
            "level": [100.0, 100.0],
            "r": [2.0, 2.0],  # stop 2% away -> 1% of price = 0.5R
            "atr": [4.0, 4.0],
            "first_touch": ["target", "stop"],
            "touch_hours": [3.0, 30.0],
            "day": [day, day],
            "trigger_time": [trig, trig],
            "r10": [0.5, -1.0],
            **{f"r_close_{h}": [1.0, -0.5] for h in v3.HORIZONS},
        }
    )


def test_funding_sums_and_cost_columns(monkeypatch):
    ev = _events()
    day = int(ev["day"][0])
    # marks every 8h from the trigger day's 00:00; rate +0.01% each
    marks = pd.DataFrame({"t": [day + k * 8 * HOUR for k in range(40)], "rate": [1e-4] * 40})
    monkeypatch.setattr(v3, "funding_frame", lambda sym: marks)
    out = v3.add_costs(ev, log=lambda *a: None)
    rpf = 100.0 / 2.0  # R per unit fraction of price = 50
    # long, tier 1, target exit (maker, no exit slippage): fees 0.05% + 0.02%, slip 0.02%
    assert abs(out["fees_r"][0] - (0.0005 + 0.0002) * rpf) < 1e-12
    assert abs(out["slip_r"][0] - 0.0002 * rpf) < 1e-12
    # trigger 05:00, exit at 08:00 (touch_hours 3): the 08:00 mark is charged, the 00:00 one is not
    assert abs(out["funding_r"][0] - 1e-4 * rpf) < 1e-12
    # short, tier NaN -> tier 3, stop exit (taker + slippage both legs)
    assert abs(out["fees_r"][1] - 0.001 * rpf) < 1e-12
    assert abs(out["slip_r"][1] - 0.001 * rpf) < 1e-12
    # trigger 05:00, exit 30 h later = 11:00 next day: marks 08:00, 16:00, 00:00, 08:00 = 4; short RECEIVES positive funding
    assert abs(out["funding_r"][1] + 4e-4 * rpf) < 1e-12
    # test-1 hold of 1 bar: exit = close of day D+1 (hour 23 open): marks 08, 16, 00, 08, 16 = 5
    assert abs(out["cost_r_1"][0] - (2 * 0.0005 + 2 * 0.0002 + 5e-4) * rpf) < 1e-12
    # net forward return: r_close 1.0 R = 2% of price; minus cost (0.14% + 0.05%) = 1.81% ; ATR = 1.81 / 4
    assert abs(out["net_pct_1"][0] - (2.0 - 100 * (0.0014 + 5e-4))) < 1e-9
    assert abs(out["net_atr_1"][0] - (0.02 - 0.0014 - 5e-4) * 100 / 4.0) < 1e-9
    assert abs(out["net_r_1"][0] - (1.0 - out["cost_r_1"][0])) < 1e-12
    assert out["funding_known"].all()


def test_funding_missing_series_is_zero_and_flagged(monkeypatch):
    ev = _events()
    monkeypatch.setattr(v3, "funding_frame", lambda sym: pd.DataFrame(columns=["t", "rate"]))
    out = v3.add_costs(ev, log=lambda *a: None)
    assert (out["funding_r"] == 0).all() and not out["funding_known"].any()


def test_m15_first_excursion_vectors():
    # 15m bars from 05:00; level 100, r 2 (0.25R = 0.5); long
    t0 = 19000 * DAY + 5 * HOUR
    t = np.array([t0 + k * 15 * 60_000 for k in range(8)])
    # bar 0: inside (no break); bar 1: breaks the high AND prints low 99.3 (0.35R against) -> adverse counted in the trigger bar
    h = np.array([99.9, 100.2, 100.3, 100.6, 100.4, 100.1, 99.0, 98.0])
    l = np.array([99.5, 99.3, 100.0, 100.1, 99.9, 99.0, 98.5, 97.0])  # noqa: E741
    end = t0 + 24 * HOUR
    counted, ignored = m15.first_excursion(t, h, l, t0, end, 100.0, 2.0, "long")
    assert counted == "adv"  # the trigger bar's own low counts
    assert ignored == "fav"  # ignoring it, +0.5 (bar 3, high 100.6) comes before bar 5's low 99.0
    # short mirror: level 100, break = low < 100 in the trigger hour
    hs = np.array([100.5, 100.4, 100.2, 100.1, 99.8, 100.9, 101.0, 101.5])
    ls = np.array([100.1, 99.9, 99.7, 99.4, 99.6, 100.0, 100.5, 101.0])
    c2, i2 = m15.first_excursion(t, hs, ls, t0, end, 100.0, 2.0, "short")
    assert (
        c2 == "fav" and i2 == "fav"
    )  # 99.4 (0.3R for) at bar 3 before 100.9 (0.45R against) at bar 5
    # no bar in the trigger hour trades through the level -> no_bars
    assert m15.first_excursion(
        t, np.full(8, 99.0), np.full(8, 98.0), t0, end, 100.0, 2.0, "long"
    ) == ("no_bars", "no_bars")
    # neither threshold reached inside the window -> none
    t_short = t[:3]
    assert m15.first_excursion(
        t_short,
        np.array([99.9, 100.2, 100.3]),
        np.array([99.8, 99.9, 100.0]),
        t0,
        end,
        100.0,
        2.0,
        "long",
    ) == ("none", "none")


def test_m15_sample_is_block_random_and_exact():
    ev = pd.DataFrame(
        {
            "symbol": ["A"] * 50 + ["B"] * 50 + ["C"] * 50,
            "trigger_ts": pd.to_datetime(
                ["2024-01-05"] * 50 + ["2024-02-05"] * 50 + ["2024-03-05"] * 50, utc=True
            ),
        }
    )
    s = m15.sample_rows(ev, 70, seed=1)
    assert len(s) == 70
    # at most two blocks were needed to reach 70 rows
    assert (s["symbol"] + s["trigger_ts"].dt.strftime("%Y-%m")).nunique() <= 2


def test_gate_result_rule():
    tt = pd.DataFrame(
        {
            "family": ["all", "continuation", "inside", "outside", "reversal"],
            "n_test": [10000, 4000, 3000, 200, 2000],
            "mean_atr_test": [0.01, -0.02, 0.05, 0.9, 0.03],
            "z_test": [0.5, -1.0, 2.4, 5.0, 1.9],
            "mean_pct_test": [0.0] * 5,
            "mean_r_test": [0.0] * 5,
        }
    )
    ok, fams, line = v3.gate_result(tt)
    assert ok and fams == ["inside"] and line.startswith("Gate: PASSED for inside")
    tt.loc[tt["family"] == "inside", "z_test"] = 1.99
    ok, fams, line = v3.gate_result(tt)
    assert not ok and fams == [] and line.startswith("Gate: FAILED")
