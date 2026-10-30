"""The trade viewer's page logic (core.js / stats.js / story.js) run under node against the
recorded-row contract: the TVB-39 and TVB-40 audit repairs, each with the audit's named shape.

Rows here are hand vectors in the engine's column names; the bars are unit-test fixtures for the
words and the geometry only (no research number is derived from them)."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from analysis.domino.trade_viewer import VIEWER

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")

DAY = 86400
T0 = 1_767_225_600  # 2026-01-01 00:00 UTC


def _daily(n: int, start: int = T0) -> list[list[float]]:
    # a flat tape: every bar opens 100, high 101, low 99, closes 100 (the words read the ROW, not these bars)
    return [[start + i * DAY, 100.0, 101.0, 99.0, 100.0, 1.0] for i in range(n)]


def run_js(body: str) -> dict:
    """Load the three page modules with a window shim and run `body`, which must assign `out`."""
    files = "".join(
        (VIEWER / f).read_text(encoding="utf-8") + "\n" for f in ("core.js", "stats.js", "story.js")
    )
    script = (
        "const window = {}; const document = { getElementById: () => null };\n"
        + files
        + "const DV = window.DV; const C = DV.core, ST = DV.stats, S = DV.story;\n"
        + "let out = {};\n"
        + body
        + "\nprocess.stdout.write(JSON.stringify(out));"
    )
    # a file, not `node -e`: the three modules exceed the Windows command-line length
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "page_probe.js"
        path.write_text(script, encoding="utf-8")
        r = subprocess.run(["node", str(path)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def row(**kw) -> dict:
    base = {
        "date": "2026-01-10",
        "direction": "up",
        "tf": "D",
        "kind": "reversal",
        "cls": "plain",
        "stack": "D",
        "level": 100.0,
        "stop": 98.0,
        "r_pct": 2.0,
        "t1": 103.0,
        "t1_src": "anchor",
        "t1_k": None,
        "t2": None,
        "t3": None,
        "status": "exit",
        "exit_k": 3,
        "days": 3,
        "ret_C": 1.0,
        "ret_A": 1.0,
        "days_A": 3,
        "hit_A": False,
        "ret_B": None,
        "days_B": None,
        "hit_B": None,
        "ret_D": 1.0,
        "days_D": 3,
        "hit_D": False,
        "ret_D5": 1.0,
        "days_D5": 3,
        "hit_D5": False,
        "ret5": -2.0,
        "days_ref": 1,
        "out5": "stop",
        "stop_k": 1,
        "one_r_k": None,
        "w_support": "with",
        "mfe_x": 2.5,
        "mae_x": 1.0,
        "status_u": None,
        "status_h": None,
        "status_own": None,
        "next_bar": None,
    }
    base.update(kw)
    return base


# ---------------------------------------------------------------- core.js


def test_settle_keeps_the_selected_book_when_it_has_no_result():
    """TVB-39 F6: 0G 2026-05-17 shape, the chance book censored while book C has a result."""
    t = row(ret5=None, days_ref=None, out5=None, status5="censored")
    out = run_js(
        f"const t = {json.dumps(t)}; out.ref = C.settle(t, 'ref'); out.c = C.settle(t, 'C');"
    )
    assert out["ref"]["book"] == "ref" and out["ref"]["missing"] is True
    assert out["ref"]["ret"] is None and out["ref"]["price"] is None
    assert out["ref"]["k"] == 5  # the window it would have run, never book C's holding days
    assert out["c"]["book"] == "C" and out["c"]["ret"] == 1.0


def test_settle_carries_the_recorded_exit_price_for_the_marker_search():
    """TVB-39 F4 / F5: the out arrow searches the recorded target / stop, not the reconstructed fill."""
    a = row(hit_A=True, ret_A=3.0, days_A=2, t1_k=2)
    ref = row(out5="stop", stop_k=0, days_ref=0)
    one_r = row(out5="one_r", one_r_k=2, days_ref=2, ret5=2.0)
    out = run_js(
        f"out.a = C.settle({json.dumps(a)}, 'A'); out.s = C.settle({json.dumps(ref)}, 'ref'); out.r = C.settle({json.dumps(one_r)}, 'ref');"
    )
    assert out["a"]["target"] is True and out["a"]["at"] == 103.0
    assert out["s"]["stop"] is True and out["s"]["at"] == 98.0 and out["s"]["k"] == 0
    assert out["r"]["target"] is True and out["r"]["at"] == 102.0  # one R = level + (level - stop)


def test_stack_subset_separates_the_converged_levels_from_the_far_ones():
    """TVB-39 F7: 0G 2026-08-31 shape, D = W exact and M 34.59% away, class exact_shared."""
    t = row(cls="exact_shared", stack="D+W+M", level=0.17296)
    levels = [
        {"tf": "D", "price": 0.17296},
        {"tf": "W", "price": 0.17296},
        {"tf": "M", "price": 0.23279},
    ]
    out = run_js(
        f"out.s = C.stackSubset({json.dumps(t)}, {json.dumps(levels)}); out.w = C.stackWords({json.dumps(t)}, {json.dumps(levels)}).text;"
    )
    assert [l["tf"] for l in out["s"]["conv"]] == ["D", "W"]
    assert [l["tf"] for l in out["s"]["far"]] == ["M"]
    assert abs(out["s"]["far"][0]["gap"] - 34.59) < 0.01
    assert out["w"].startswith("D+W same price; M +34.59% beyond")


def test_stack_subset_near_band_and_weekly_rows():
    near = row(cls="near", stack="D+W", level=100.0)
    lv = [{"tf": "D", "price": 100.0}, {"tf": "W", "price": 100.2}, {"tf": "M", "price": 100.9}]
    weekly = row(tf="W", cls="within1", stack="W+M", level=100.0)
    out = run_js(
        f"out.n = C.stackSubset({json.dumps(near)}, {json.dumps(lv)}); out.w = C.stackSubset({json.dumps(weekly)}, {json.dumps(lv[1:])});"
    )
    assert [l["tf"] for l in out["n"]["conv"]] == ["D", "W"] and [
        l["tf"] for l in out["n"]["far"]
    ] == ["M"]
    assert (
        len(out["w"]["conv"]) == 2 and out["w"]["far"] == []
    )  # weekly / monthly rows are classed on the whole stack


def test_cell_index_keeps_the_candle_on_both_sides_of_its_centre():
    """TVB-40 F2: 49% and 51% of the way through a day's cell both belong to that day."""
    bs = [{"t": T0 + i * DAY} for i in range(5)]
    out = run_js(
        f"const bs = {json.dumps(bs)}; const ms = (f) => (bs[2].t + f * {DAY}) * 1000;"
        "out.a = C.cellIndex(bs, ms(0.49)); out.b = C.cellIndex(bs, ms(0.51)); out.c = C.cellIndex(bs, ms(0.999)); out.d = C.cellIndex(bs, ms(1.0)); out.e = C.cellIndex(bs, (bs[0].t - 5) * 1000);"
    )
    assert out["a"] == 2 and out["b"] == 2 and out["c"] == 2
    assert out["d"] == 3 and out["e"] == 0


# ---------------------------------------------------------------- stats.js


def test_drawdown_runs_on_daily_sums_not_within_the_day():
    """TVB-40 F1: +5% then -5% on the same day is a flat day (the engine's book_stats), not a 50-dollar dip."""
    items = [
        {"coin": "A", "t": row(ret_C=5.0)},
        {"coin": "B", "t": row(ret_C=-5.0)},
        {"coin": "A", "t": row(date="2026-01-11", ret_C=-3.0)},
    ]
    out = run_js(
        f"const s = ST.bookStats({json.dumps(items)}, 'C', 1000); out = {{ dd: s.maxDD, total: s.total, curve: s.curve.map(p => p.v) }};"
    )
    assert out["curve"] == [0.0, -30.0]
    assert (
        out["dd"] == 30.0
    )  # peak 0 (clipped), trough -30 on day two; the within-day -50 is never scored


def test_month_summary_averages_over_filled_rows_only():
    """TVB-40 F5: a censored row is not a zero return."""
    items = [
        {"coin": "A", "t": row(ret_C=-4.0)},
        {"coin": "B", "t": row(ret_C=None, status="censored")},
        {"coin": "C", "t": row(date="2026-02-02", ret_C=1.0)},
    ]
    out = run_js(
        f"const m = ST.calendarDays({json.dumps(items)}, 'C', 1000); out.jan = ST.monthSummary(m, {T0}, {T0 + 31 * DAY}); out.feb = ST.monthSummary(m, {T0 + 31 * DAY}, {T0 + 59 * DAY});"
        f"out.none = ST.monthSummary(ST.calendarDays([{{coin:'X', t:{json.dumps(row(ret_C=None, status='censored'))}}}], 'C', 1000), {T0}, {T0 + 31 * DAY});"
    )
    assert out["jan"] == {"n": 2, "filled": 1, "usd": -40.0, "avg": -4.0}
    assert out["feb"]["n"] == 1 and out["feb"]["avg"] == 1.0
    assert out["none"]["n"] == 1 and out["none"]["filled"] == 0 and out["none"]["avg"] is None


# ---------------------------------------------------------------- story.js


def _story(t: dict, book: str, n_days: int = 40) -> str:
    return run_js(
        f"const cal = C.makeCalendar({{ daily: {json.dumps(_daily(n_days))}, hourly: [] }});"
        f"out.s = S.narrate({{ t: {json.dumps(t)}, coin: 'X', cal, book: '{book}', size: 1000, p: 2 }});"
    )["s"]


def test_hourly_clock_is_worded_in_the_trade_s_own_colours():
    """TVB-40 F3: BTC 2026-03-18 daily short shape: a short leaves on a GREEN hour in a GREEN day."""
    short = row(direction="down", status_h="exit", entry_h=11, exit_h=37, ret_C_h=-1.2)
    long_ = row(status_h="exit", entry_h=2, exit_h=5, ret_C_h=0.4)
    assert "first green hour while the day is green" in _story(short, "C")
    assert "first red hour while the day is red" in _story(long_, "C")


def test_open_row_without_a_target_is_not_told_it_left_with_the_clock():
    """TVB-40 F3: ADA 2024-01-30 book A shape: open at the cap, T1 never touched."""
    t = row(
        status="open", exit_k=None, days=20, ret_C=0.5, ret_A=0.5, days_A=20, hit_A=False, t1_k=None
    )
    s = _story(t, "A")
    assert "left with the daily clock" not in s
    assert "marked at the day-20 close" in s


def test_same_day_stop_and_one_r_tie_is_not_told_as_stop_first():
    """TVB-40 F3: BTC 2023-04-09 chance-book shape: stop_k = one_r_k = 0."""
    t = row(out5="stop", stop_k=0, one_r_k=0, days_ref=0)
    s = _story(t, "ref")
    assert "before one R" not in s
    assert "cannot say which came first" in s and "takes the stop" in s
    plain = _story(row(out5="stop", stop_k=1, one_r_k=None), "ref")
    assert "before one R" in plain


def test_missing_book_is_named_not_borrowed():
    """TVB-39 F6 in words: the chance book censored while book C exited."""
    t = row(ret5=None, days_ref=None, out5=None)
    s = _story(t, "ref")
    assert "The chance book has no result" in s
    assert "daily-close" not in s.split("What book ref did.")[1].split("</p>")[0]


def test_travel_is_labelled_as_book_c_s_window():
    """TVB-40 F4: the travel columns are measured through the headline exit whatever book is selected."""
    assert "book C's exit" in _story(row(), "ref")


def test_stack_sentence_names_the_converged_subset_and_the_far_level_apart():
    """TVB-39 F7 in words: D = W exact, M far."""
    t = row(cls="exact_shared", stack="D+W+M", level=100.0, date="2026-01-21")
    # a tape from December 2025 so a complete week and month sit before the entry; every high is 100, so the day's and
    # the week's levels are 100 (exact); the month before is then given a high of 130 (far)
    daily = _daily(70, start=T0 - 31 * DAY)
    for b in daily:
        b[2] = 100.0
    out = run_js(
        f"const daily = {json.dumps(daily)}; const cal = C.makeCalendar({{ daily, hourly: [] }});"
        "const i = cal.dayIdx.get('2026-01-21'); const w = cal.weeks.find(b => b.days.includes(i)); const m = cal.months.find(b => b.days.includes(i));"
        "const mi = cal.months.indexOf(m); cal.months[mi - 1].h = 130.0;"
        f"out.levels = C.stackLevels({json.dumps(t)}, i, cal); out.s = S.narrate({{ t: {json.dumps(t)}, coin: 'X', cal, book: 'C', size: 1000, p: 2 }});"
    )
    assert [l["price"] for l in out["levels"]] == [100.0, 100.0, 130.0]
    assert "the week's level 100.00 (same price" in out["s"]
    assert "the month's level 130.00 also broke the same day, +30.00% beyond the entry" in out["s"]
    assert "not part of the converged stack" in out["s"]


def test_app_resorts_on_a_book_change_and_uses_the_cell_index():
    """TVB-40 F6 / F2 wiring in app.js (DOM-bound, so checked at the source)."""
    src = (VIEWER / "app.js").read_text(encoding="utf-8")
    set_book = src.split("function setBook(b) {")[1].split("}")[0]
    assert "sortItems();" in set_book
    magnet = src.split("function magnetDrop(pane, local) {")[1].split("pane.save.saveData();")[0]
    assert "cellIndex(bs, tMs)" in magnet and "Math.abs(b.t * MS - tMs)" not in magnet
    assert "?? ks[0]" not in src  # no first-candle fallback for a touch marker
