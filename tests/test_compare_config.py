"""Closed-window report invariance (TVB-18 audit F1).

compare_config marks open positions at the last 5m close INSIDE the analysis
window. These tests pin the property that made F1 a bug: appending bars past
the window end (as the rolling archive does) must not change any figure in a
closed-window report.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from analysis.paper import compare_config as cc

REPO = Path(__file__).resolve().parents[1]
BARS = REPO / "analysis" / "paper" / "bars"
ROSTER = REPO / "analysis" / "paper" / "roster_week1.json"
WS = int(datetime.fromisoformat("2026-07-20").replace(tzinfo=timezone.utc).timestamp())
WE = WS + 7 * 86400
SYMS = {"xyz:GOOGL", "xyz:SKHX", "xyz:TSLA"}


def _sub_roster():
    roster = json.loads(ROSTER.read_text())
    return {"symbols": [e for e in roster["symbols"] if e["name"] in SYMS]}


def test_open_marks_are_inside_the_window():
    r = cc.summarize(_sub_roster(), WS, WE, BARS, arm_s=900, drop_12h=False)
    assert r["mark_ts"], "expected at least one open position in the subset"
    assert all(WS <= t < WE for t in r["mark_ts"])


def test_report_invariant_to_appended_post_window_bars(monkeypatch):
    base = cc.summarize(_sub_roster(), WS, WE, BARS, arm_s=900, drop_12h=False)
    real_load = cc.load_rows

    def load_plus_tail(coin, tf, bars_dir):
        rows = real_load(coin, tf, bars_dir)
        if tf == "5m":
            t, c = int(rows[-1][0]), rows[-1][4]
            rows = rows + [
                [t + 300, c, c * 2.0, c * 0.5, c * 1.5, 0.0],
                [t + 600, c * 1.5, c * 3.0, c * 1.4, c * 2.9, 0.0],
            ]
        return rows

    monkeypatch.setattr(cc, "load_rows", load_plus_tail)
    tainted = cc.summarize(_sub_roster(), WS, WE, BARS, arm_s=900, drop_12h=False)
    assert tainted == base


def test_empty_window_fails_loudly():
    entry = _sub_roster()["symbols"][0]
    with pytest.raises(ValueError, match="no 5m bars"):
        cc.replay_cfg(entry, WE + 30 * 86400, WE + 37 * 86400, BARS, 900, False)
