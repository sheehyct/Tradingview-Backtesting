"""The bench runner (`analysis/bench/run_bench.py`), TVB-44: the gap flag and the open-fill
re-measurement of prereg amendment 2026-11-02 (TVB-43 audit F1), the roll flag on the headline
window with the chance book's own beside it (F4), the exporter building its source away from the
registered run (F2), strict JSON (the smaller items)."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from analysis.bench import es_tape, run_bench


def ms(y, m, d, h=0):
    return int(datetime(y, m, d, h, tzinfo=timezone.utc).timestamp() * 1000)


def _row(date, direction, level, **kw):
    return {
        "date": date,
        "direction": direction,
        "level": level,
        "tf": "D",
        "kind": "reversal",
        **kw,
    }


SESSIONS = {
    "2026-09-21": {
        "o": 102.0,
        "h": 104.0,
        "l": 101.0,
        "c": 103.0,
    },  # opens above 100, never prints it
    "2026-09-22": {
        "o": 102.0,
        "h": 104.0,
        "l": 99.0,
        "c": 103.0,
    },  # opens above 100, trades back through
    "2026-09-23": {
        "o": 99.5,
        "h": 104.0,
        "l": 99.0,
        "c": 103.0,
    },  # opens below 100: the trigger prints
    "2026-09-24": {
        "o": 96.0,
        "h": 97.5,
        "l": 94.0,
        "c": 95.0,
    },  # a gap down: a short never prints 100
}


def test_gap_flag_reads_the_entry_session_s_open_against_the_trigger_strictly():
    rows = [
        _row("2026-09-21", "up", 100.0),
        _row("2026-09-22", "up", 100.0),
        _row("2026-09-23", "up", 100.0),
        _row("2026-09-24", "down", 100.0),
        _row("2026-09-21", "down", 100.0),  # a short into a gap UP: the trigger is below the open
        _row("2026-09-23", "up", 99.5),  # the open AT the trigger is not a gap
    ]
    run_bench.gap_flags(rows, SESSIONS)
    assert [r["gap"] for r in rows] == ["untraded", "open", None, "untraded", None, None]
    assert rows[0]["session_open"] == 102.0 and rows[3]["session_open"] == 96.0


def test_open_fill_re_measures_gap_units_from_the_open_and_keeps_the_rest_as_the_control():
    # a long, trigger 100: the session opened 102 and never printed 100; exit only closed at 105
    r = _row(
        "2026-09-21",
        "up",
        100.0,
        gap="untraded",
        session_open=102.0,
        ret_C=5.0,
        ret_A=1.5,
        hit_A=True,  # T1 101.5 was behind the open: reached at the entry
        ret_B=3.0,
        hit_B=True,  # T2 103 was ahead of it: re-measured from the open
        ret_D=5.0,
        hit_D=False,  # not hit: a close exit, re-measured
        ret_ref=-2.0,
        out5="stop",  # the chance book's stop at 98, from the open
        ret_C_h=None,
    )
    run_bench.open_fill([r])
    assert r["of_ret_C"] == pytest.approx((105.0 - 102.0) / 102.0 * 100)
    assert r["of_ret_A"] == 0.0
    assert r["of_ret_B"] == pytest.approx((103.0 - 102.0) / 102.0 * 100)
    assert r["of_ret_D"] == pytest.approx((105.0 - 102.0) / 102.0 * 100)
    assert r["of_ret_ref"] == pytest.approx((98.0 - 102.0) / 102.0 * 100)
    assert r["of_ret_C_h"] is None
    # a short mirrored, trigger 100: the session opened 96; one R at 97 and the chance book's one R
    # were behind the open (above it); exit only closed at 95
    s = _row(
        "2026-09-24",
        "down",
        100.0,
        gap="untraded",
        session_open=96.0,
        ret_C=5.0,
        ret_D=3.0,
        hit_D=True,
        ret_ref=3.0,
        out5="one_r",
    )
    run_bench.open_fill([s])
    assert s["of_ret_C"] == pytest.approx((96.0 - 95.0) / 96.0 * 100)
    assert s["of_ret_D"] == 0.0 and s["of_ret_ref"] == 0.0
    # no gap: the control's values, untouched
    n = _row(
        "2026-09-23", "up", 100.0, gap=None, session_open=99.5, ret_C=5.0, ret_A=1.5, hit_A=True
    )
    run_bench.open_fill([n])
    assert n["of_ret_C"] == 5.0 and n["of_ret_A"] == 1.5


def test_fill_blocks_count_the_gap_units_and_the_targets_behind_the_open():
    rows = [
        _row(
            "2026-09-21", "up", 100.0, ret_C=5.0, ret_A=1.5, hit_A=True, out5="stop", ret_ref=-2.0
        ),
        _row(
            "2026-09-22",
            "up",
            100.0,
            ret_C=-1.0,
            ret_A=-1.0,
            hit_A=False,
            out5="neither",
            ret_ref=-1.0,
        ),
        _row(
            "2026-09-23", "up", 100.0, ret_C=2.0, ret_A=1.5, hit_A=True, out5="one_r", ret_ref=2.0
        ),
        _row(
            "2026-09-24", "down", 100.0, ret_C=5.0, ret_A=1.0, hit_A=True, out5="one_r", ret_ref=3.0
        ),
    ]
    run_bench.gap_flags(rows, SESSIONS)
    run_bench.open_fill(rows)
    fb = run_bench.fill_blocks(pd.DataFrame(rows))
    f = fb["D"]
    assert (f["n"], f["gap"], f["untraded"]) == (4, 3, 2)
    labels = [b["label"] for b in f["blocks"]]
    assert labels[0].startswith("all units, at the trigger") and labels[1].startswith(
        "all units, open-fill"
    )
    assert f["blocks"][2]["n"] == 1 and f["blocks"][3]["n"] == 3 and f["blocks"][5]["n"] == 2
    # A's T1 was behind the open on the first and the fourth unit; the chance book's one R on the fourth
    assert f["reached_at_entry"]["A"] == 2 and f["reached_at_entry"]["ref"] == 1
    assert f["reached_at_entry"]["C"] == 0
    assert f["control_minus_open_fill_on_gap_units"]["C"]["n"] == 3
    md = run_bench.table_fill(fb)
    assert any("reached at the entry (zero)" in line for line in md)


def test_roll_flags_read_the_headline_window_and_the_chance_book_s_own_window():
    dates = [f"2026-09-{d:02d}" for d in range(1, 31)]
    rolls = {"2026-09-10"}
    rows = [
        _row(
            "2026-09-05", "up", 100.0, days=3, days_ref=6
        ),  # C out before the roll, the reference after
        _row("2026-09-05", "down", 100.0, days=6, days_ref=3),  # the other way round
        _row(
            "2026-09-10", "up", 100.0, days=3, days_ref=3
        ),  # the entry session is the roll session
        _row("2026-09-05", "up", 100.0, days=None, days_ref=None),  # censored: no window at all
    ]
    run_bench.roll_flags(rows, dates, rolls)
    assert [(r["roll"], r["roll_ref"]) for r in rows] == [
        (None, "window"),
        ("window", None),
        ("entry", "entry"),
        (None, None),
    ]


def test_summary_json_is_strict_with_no_nan():
    doc = {
        "a": float("nan"),
        "b": [1.0, float("inf")],
        "c": np.int64(3),
        "d": np.bool_(True),
        "e": "x",
    }
    assert (
        json.dumps(run_bench._finite(doc), allow_nan=False)
        == '{"a": null, "b": [1.0, null], "c": 3, "d": true, "e": "x"}'
    )


def _tape() -> es_tape.SessionTape:
    """Three Globex-shaped weeks: real opens Sunday 22:00 UTC, trade dates Monday to Friday."""
    sun = ms(2026, 9, 6, 22) // 1000
    daily, real_daily, real_hourly, opens = [], [], [], {}
    for w in range(3):
        for d in range(5):
            t = sun + (7 * w + d) * 86_400
            date = datetime.fromtimestamp(t + 6 * 3600, tz=timezone.utc).strftime("%Y-%m-%d")
            opens[date] = t
            real_daily.append([t, 100.0, 101.0, 99.0, 100.5, 1.0])
            for h in range(23):
                real_hourly.append([t + h * 3600, 100.0, 100.4, 99.6, 100.2, 1.0])
            daily.append(
                {
                    "t": es_tape.session_ms(date),
                    "o": 100.0,
                    "h": 101.0,
                    "l": 99.0,
                    "c": 100.5,
                    "v": 1.0,
                }
            )
    return es_tape.SessionTape(
        variant="globex",
        symbol="ES.n.0",
        daily=daily,
        hourly=[],
        real_daily=real_daily,
        real_hourly=real_hourly,
        real_weekly=[],
        real_monthly=[],
        opens_by_date=opens,
        roll_dates=set(),
        short_sessions={},
        label_shift_hours=6,
    )


def test_export_run_builds_its_source_away_from_the_registered_run(tmp_path, monkeypatch):
    """TVB-43 audit F2: the exporter opened the live run's files for writing before the staged
    importer could protect them, so a failed write left a truncated run that the listing still
    advertised. The source is now a temporary folder; a write failure on the rerun leaves the
    registered run and the listing byte-identical and no staging debris."""
    data = tmp_path / "data"
    tape = _tape()
    quiet = lambda s: None  # noqa: E731
    rid = run_bench.export_run("globex", tape, [], tape.dates[-1], log=quiet, data=data)
    dest = data / "runs" / rid
    before = {p.name: p.read_bytes() for p in dest.iterdir()}
    listing = (data / "runs.json").read_bytes()
    assert "run.json" in before and "ES.json" in before
    real_dump = json.dump
    calls = {"n": 0}

    def failing(obj, fh, **kw):
        calls["n"] += 1
        if calls["n"] == 2:  # the instrument file, after run.json
            raise OSError("disk full")
        return real_dump(obj, fh, **kw)

    monkeypatch.setattr(run_bench.json, "dump", failing)
    with pytest.raises(OSError):
        run_bench.export_run("globex", tape, [], tape.dates[-1], log=quiet, data=data)
    monkeypatch.undo()
    assert {p.name: p.read_bytes() for p in dest.iterdir()} == before
    assert (data / "runs.json").read_bytes() == listing
    assert not list(data.glob(".export-*")) and not list((data / "runs").glob(".import-*"))
    # a clean rerun replaces the run through the staged swap and keeps one listing entry
    assert run_bench.export_run("globex", tape, [], tape.dates[-1], log=quiet, data=data) == rid
    assert [r["id"] for r in json.loads((data / "runs.json").read_text(encoding="utf-8"))] == [rid]
    assert not list(data.glob(".export-*"))
