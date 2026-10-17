"""The trade viewer's data side: hourly normalisation, the compact bar shape, the row slimming,
and the page's calendar bucketing (JavaScript) against the census's own (Python)."""

from __future__ import annotations

import re
import shutil
import subprocess
from datetime import datetime, timezone

import pytest

from analysis.domino import census
from analysis.domino.census import HOUR, normalize_hourly
from analysis.domino.trade_viewer import VIEWER, _bool, _num, compact

DAY = census.DAY


def _ms(text: str) -> int:
    return int(
        datetime.strptime(text, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp() * 1000
    )


def bar(t: int, o=1.0, h=2.0, lo=0.5, c=1.5, v=3.0) -> dict:
    return {"t": t, "o": str(o), "h": str(h), "l": str(lo), "c": str(c), "v": str(v)}


def test_normalize_hourly_keeps_closed_aligned_hours_last_copy_wins():
    t0 = _ms("2026-10-09 10:00")
    now = _ms("2026-10-09 12:30")  # 12:00 is forming
    rows = [
        bar(t0, c=1.1),
        bar(t0 + 30 * 60 * 1000),  # not an hour start: dropped
        bar(t0 + HOUR, c=1.2),
        bar(t0 + HOUR, c=1.25),  # duplicate: last copy wins
        bar(t0 + 2 * HOUR, c=1.3),  # forming at `now`: cut
        bar(t0 - HOUR, c=0.9),  # out of order: sorted
    ]
    out = normalize_hourly(rows, now)
    assert [b["t"] for b in out] == [t0 - HOUR, t0, t0 + HOUR]
    assert [b["c"] for b in out] == [0.9, 1.1, 1.25]
    assert all(isinstance(b["o"], float) for b in out)


def test_compact_is_seconds_then_ohlcv():
    t = _ms("2026-10-09 00:00")
    assert compact([{"t": t, "o": 1.0, "h": 2.0, "l": 0.5, "c": 1.5, "v": 7.0}]) == [
        [t // 1000, 1.0, 2.0, 0.5, 1.5, 7.0]
    ]


def test_csv_cell_parsing_treats_nan_and_blank_as_missing():
    assert _num("nan") is None and _num("") is None and _num("None") is None
    assert _num("3.5") == 3.5 and _num("-2") == -2.0
    assert _bool("True") is True and _bool("False") is False and _bool("nan") is None


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_page_calendar_buckets_match_the_census():
    """weekStart / monthStart in core.js give the census's keys for every day of two years."""
    src = (VIEWER / "core.js").read_text(encoding="utf-8")
    fns = {}
    for name in ("weekStart", "monthStart"):
        m = re.search(rf"function {name}\(t\) \{{.*?\}}\s*$", src, re.M)
        assert m, name
        fns[name] = m.group(0)
    days = list(
        range(_ms("2024-01-01 00:00") // 1000, _ms("2026-01-01 00:00") // 1000, DAY // 1000)
    )
    script = (
        "const DAY = 86400;\n"
        + "\n".join(fns.values())
        + "\nconst days = "
        + str(days)
        + ";\nprocess.stdout.write(JSON.stringify(days.map(t => [weekStart(t), monthStart(t)])));"
    )
    out = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout
    import json

    got = json.loads(out)
    want = [
        [census.week_start(t * 1000) // 1000, census.month_start(t * 1000) // 1000] for t in days
    ]
    assert got == want
