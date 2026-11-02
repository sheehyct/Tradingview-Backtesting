"""The trade viewer's page logic (core.js / stats.js / story.js) run under node against the run
contract's cards (viewer/CONTRACT.md): the TVB-39 and TVB-40 audit repairs, the TVB-41 cold
review's fold and the TVB-41 Codex audit's F1, each with the audit's named shape, on the card
shape the page now reads (stage 2 of the contract).

Cards here are hand vectors in the contract's field names; the bars are unit-test fixtures for
the words and the geometry only (no research number is derived from them)."""

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
HOUR = 3600
T0 = 1_767_225_600  # 2026-01-01 00:00 UTC
E = T0 + 9 * DAY  # the default card's entry day, 2026-01-10

RUN = {
    "contract": 1,
    "id": "test",
    "name": "a test run",
    "as_of": "2026-03-01",
    "clock": {"day_roll": "00:00 UTC", "resolution": "day"},
    "units": ["D", "W", "M"],
    "bars": ["1d", "1h"],
    "books": [
        {
            "id": "C",
            "name": "exit only",
            "role": "headline",
            "rule": "No target. Hold until the daily clock fires; 20-day cap.",
        },
        {
            "id": "A",
            "name": "all out at T1",
            "role": "target",
            "target": "T1",
            "rule": "Everything out at T1. Otherwise the exit.",
        },
        {
            "id": "B",
            "name": "hold through T2",
            "role": "target",
            "target": "T2",
            "rule": "Hold through T2 with the exit live.",
        },
        {
            "id": "D",
            "name": "one R or the exit",
            "role": "target",
            "target": "one_r",
            "rule": "One R or the exit, whichever first.",
        },
        {
            "id": "D5",
            "name": "one R or the exit, 5 bars",
            "role": "target",
            "target": "one_r",
            "rule": "One R or the exit inside five bars.",
        },
        {
            "id": "ref",
            "name": "chance book",
            "role": "reference",
            "target": "one_r",
            "rule": "One R or the setup-bar stop, marked at bar five.",
        },
        {
            "id": "C_h",
            "name": "hourly clock",
            "role": "clock",
            "resolution": "hour",
            "group": "hourly clock",
            "rule": "Exit only on the hourly clock.",
        },
        {
            "id": "C_u",
            "name": "under water",
            "role": "clock",
            "group": "under water",
            "rule": "Exit only, reading against as under water.",
        },
    ],
}


def _daily(n: int, start: int = T0) -> list[list[float]]:
    # a flat tape: every bar opens 100, high 101, low 99, closes 100 (the words read the CARD, not these bars)
    return [[start + i * DAY, 100.0, 101.0, 99.0, 100.0, 1.0] for i in range(n)]


def _hourly(n_days: int, start: int = T0) -> list[list[float]]:
    return [[start + i * HOUR, 100.0, 101.0, 99.0, 100.0, 1.0] for i in range(24 * n_days)]


def run_js(body: str) -> dict:
    """Load the three page modules with a window shim, set the test run, and run `body`, which
    must assign `out`."""
    files = "".join(
        (VIEWER / f).read_text(encoding="utf-8") + "\n" for f in ("core.js", "stats.js", "story.js")
    )
    script = (
        "const window = {}; const document = { getElementById: () => null };\n"
        + files
        + "const DV = window.DV; const C = DV.core, ST = DV.stats, S = DV.story;\n"
        + f"C.setRun({json.dumps(RUN)});\n"
        + "const prep = (t, cal) => C.prep(t, cal || null);\n"
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


def book(bid: str, how: str, at=None, price=None, ret=None, hit=None, **kw) -> dict:
    b = {"id": bid, "how": how, "at": at, "price": price, "ret": ret, "hit": hit}
    b.update(kw)
    return b


def card(**kw) -> dict:
    """The default card: a daily long, T1 touched on day 2, one R on day 1, the headline clock on
    day 3, the chance book stopped on day 1, the hourly clock outside its window."""
    base = {
        "id": "X-2026-01-10-D-reversal-up",
        "instrument": "X",
        "bar": "D",
        "pattern": "2-2 reversal",
        "kind": "reversal",
        "direction": "up",
        "class": "plain",
        "stack": [{"bar": "D"}],
        "entry": {"t": E, "price": 100.0},
        "far": 98.0,
        "one_r": 102.0,
        "r_pct": 2.0,
        "targets": [{"name": "T1", "price": 103.0, "source": "anchor", "touched": E + 2 * DAY}],
        "touches": {"one_r": E + DAY, "far": E + DAY},
        "books": [
            book("C", "clock", E + 3 * DAY, 101.0, 1.0),
            book("A", "target", E + 2 * DAY, 103.0, 3.0, True),
            book("B", "clock", E + 3 * DAY, 101.0, 1.0, None),
            book("D", "one_r", E + DAY, 102.0, 2.0, True),
            book("D5", "one_r", E + DAY, 102.0, 2.0, True),
            book("ref", "stop", E + DAY, 98.0, -2.0, False),
            book("C_h", "none", note="outside the venue's hourly window"),
            book("C_u", "clock", E + 3 * DAY, 101.0, 1.0),
        ],
        "travel": {"mfe": 2.5, "mae": 1.0, "window": "C", "next_bar": "with"},
        "context": {"week_side": "with", "month_side": "against"},
        "extras": {"liquid": True, "flag": "none", "anchor": "anchor", "dex": "main"},
    }
    base.update(kw)
    return base


def with_books(c: dict, **by_id) -> dict:
    """Replace or add book entries on a card by id."""
    books = [by_id.pop(b["id"]) if b["id"] in by_id else b for b in c["books"]]
    books += list(by_id.values())
    return dict(c, books=books)


# ---------------------------------------------------------------- core.js


def test_prep_derives_day_offsets_from_the_bars_by_index():
    """The census fills no gaps: an offset is bars, not calendar days. With day 11 missing, a
    touch on the 13th is two bars after the 10th, not three."""
    daily = [b for b in _daily(40) if b[0] != T0 + 10 * DAY]
    out = run_js(
        f"const cal = C.makeCalendar({{ daily: {json.dumps(daily)}, hourly: [] }});"
        f"const t = prep({json.dumps(card())}, cal); out = {{ t1k: t.t1_k, ck: t.byBook.C.k, ak: t.byBook.A.k, date: t.date, level: t.level, stop: t.stop, stack: t.stackStr }};"
    )
    assert (
        out["date"] == "2026-01-10"
        and out["level"] == 100.0
        and out["stop"] == 98.0
        and out["stack"] == "D"
    )
    assert (
        out["t1k"] == 1 and out["ak"] == 1 and out["ck"] == 2
    )  # the 12th is index +1, the 13th index +2


GLOBEX_SUN = 1_767_564_000  # 2026-01-04 22:00 UTC: the Monday 2026-01-05 session's open


def _globex(weeks: int = 3) -> list[list[float]]:
    # daily bars opening Sunday to Thursday 22:00 UTC (Monday to Friday sessions), no weekend bars
    out = []
    for w in range(weeks):
        for d in range(5):
            out.append([GLOBEX_SUN + (7 * w + d) * DAY, 100.0, 101.0, 99.0, 100.0 + 5 * w + d, 1.0])
    return out


def test_session_runs_label_bars_bucket_weeks_and_hold_hours_by_session():
    """The bench prereg's page side: a Globex run declares a 6-hour label shift and a session
    calendar. The Sunday 22:00 UTC bar is Monday; a week holds five sessions and is complete; an
    hour at Monday 20:00 UTC (16:00 ET, inside Monday's session) belongs to Monday, not Tuesday;
    offsets count sessions; shipped weekly bars replace the aggregate's prices; a 00:00 UTC run
    reads exactly as before."""
    run = dict(
        RUN,
        clock={
            "day_roll": "18:00 ET",
            "resolution": "day",
            "label_shift_hours": 6,
            "calendar": "session",
        },
    )
    daily = _globex()
    hourly = [[GLOBEX_SUN + 22 * HOUR, 100.0, 101.0, 99.0, 100.5, 1.0]]  # Monday 20:00 UTC
    weekly = [
        [GLOBEX_SUN, 100.0, 150.0, 90.0, 104.0, 5.0]
    ]  # the exchange's own first week, a higher high
    fri, mon = GLOBEX_SUN + 4 * DAY, GLOBEX_SUN + 7 * DAY
    c = card(
        entry={"t": fri, "price": 100.0},
        targets=[{"name": "T1", "price": 103.0, "source": "anchor", "touched": mon}],
        touches={"one_r": mon, "far": None},
        books=[
            book("C", "clock", mon, 104.0, 4.0),
            book("A", "target", mon, 103.0, 3.0, True),
            book("ref", "cap", mon + DAY, 100.0, 0.0, False),
        ],
    )
    out = run_js(
        f"C.setRun({json.dumps(run)});"
        f"const cal = C.makeCalendar({{ bars: {{ '1d': {json.dumps(daily)}, '1h': {json.dumps(hourly)}, '1w': {json.dumps(weekly)} }} }});"
        f"const t = prep({json.dumps(c)}, cal);"
        "out = { keys: [...cal.dayIdx.keys()].slice(0, 6), weekDays: cal.weeks.map(w => w.days.length), complete: cal.weeks.map(w => w.complete),"
        f" hourSession: cal.sessionOf({GLOBEX_SUN + 22 * HOUR}), friSession: cal.sessionOf({fri}), date: t.date, ck: t.byBook.C.k, ak: t.byBook.A.k, t1k: t.t1_k,"
        " weekHigh: cal.weeks[0].h, shipped: !!cal.weeks[0].shipped, firstOfWeek: [...cal.firstOfWeek], dateOf4: cal.dateOf(4),"
        f" weekOpenAtHour: cal.weekOpenAt({GLOBEX_SUN + 22 * HOUR}) }};"
        "C.setRun(" + json.dumps(RUN) + ");"
        f"const cal0 = C.makeCalendar({{ daily: {json.dumps(_daily(21))}, hourly: [] }}); const t0 = prep({json.dumps(card())}, cal0);"
        "out.plain = { keys: [...cal0.dayIdx.keys()].slice(0, 2), weekDays: cal0.weeks.map(w => w.days.length), complete: cal0.weeks.map(w => w.complete), date: t0.date, ck: t0.byBook.C.k };"
    )
    assert out["keys"] == [
        "2026-01-05",
        "2026-01-06",
        "2026-01-07",
        "2026-01-08",
        "2026-01-09",
        "2026-01-12",
    ]
    assert out["weekDays"] == [5, 5, 5] and out["complete"] == [True, True, False]
    assert out["hourSession"] == 0 and out["friSession"] == 4 and out["weekOpenAtHour"] == 100.0
    assert out["date"] == "2026-01-09" and out["ck"] == 1 and out["ak"] == 1 and out["t1k"] == 1
    assert out["weekHigh"] == 150.0 and out["shipped"] is True
    assert out["firstOfWeek"] == [0, 5, 10] and out["dateOf4"] == "2026-01-09"
    # the 24/7 run: calendar-day keys, seven-day weeks complete only when every day is present, offsets by bar
    assert (
        out["plain"]["keys"] == ["2026-01-01", "2026-01-02"]
        and out["plain"]["date"] == "2026-01-10"
        and out["plain"]["ck"] == 3
    )
    assert (
        out["plain"]["weekDays"][1] == 7
        and out["plain"]["complete"][1] is True
        and out["plain"]["complete"][0] is False
    )


def test_settle_keeps_the_selected_book_when_it_has_no_result():
    """TVB-39 F6: the chance book censored while book C has a result. The missing book borrows no
    window (k = 0) and states the card's own reason; a book absent from the card says so."""
    c = with_books(card(), ref=book("ref", "censored"))
    out = run_js(
        f"const t = prep({json.dumps(c)}); out.ref = C.settle(t, 'ref'); out.c = C.settle(t, 'C'); out.z = C.settle(t, 'C_u');"
        f"const t2 = prep({json.dumps(dict(card(), books=[b for b in card()['books'] if b['id'] != 'C_u']))}); out.absent = C.settle(t2, 'C_u');"
    )
    assert out["ref"]["book"] == "ref" and out["ref"]["missing"] is True
    assert out["ref"]["ret"] is None and out["ref"]["price"] is None and out["ref"]["k"] == 0
    assert "censored" in out["ref"]["how"]
    assert out["c"]["book"] == "C" and out["c"]["ret"] == 1.0 and out["c"]["k"] == 3
    assert out["z"]["missing"] is False
    assert out["absent"]["missing"] is True and out["absent"]["absent"] is True


def test_missing_book_d5_reads_its_reason_from_the_card():
    """Cold review M2: a headline-censored card's D5 is `none` with the engine's note, not a
    five-bar-window story; its k is 0."""
    c = with_books(
        card(),
        C=book("C", "censored"),
        A=book("A", "censored"),
        D5=book("D5", "none", note="not scored: the headline row is censored"),
    )
    out = run_js(
        f"const t = prep({json.dumps(c)}); out.d5 = C.settle(t, 'D5'); out.a = C.settle(t, 'A');"
    )
    assert "not scored" in out["d5"]["how"] and "five-bar" not in out["d5"]["how"]
    assert out["d5"]["k"] == 0 and out["a"]["k"] == 0
    assert "censored" in out["a"]["how"]


def test_settle_carries_the_recorded_exit_price_for_the_marker_search():
    """TVB-39 F4 / F5: the out arrow searches the recorded target / stop (`at`), never a fill
    reconstructed from the return; a clock exit has a price but no touch price."""
    c = with_books(card(), ref=book("ref", "stop", E, 98.0, -2.0, False))
    out = run_js(
        f"const t = prep({json.dumps(c)}); out.a = C.settle(t, 'A'); out.s = C.settle(t, 'ref'); out.d = C.settle(t, 'D'); out.c = C.settle(t, 'C');"
    )
    assert (
        out["a"]["target"] is True
        and out["a"]["at"] == 103.0
        and out["a"]["how"] == "all out at T1"
    )
    assert out["s"]["stop"] is True and out["s"]["at"] == 98.0 and out["s"]["k"] == 0
    assert out["d"]["target"] is True and out["d"]["at"] == 102.0 and out["d"]["how"] == "one R"
    assert out["c"]["at"] is None and out["c"]["price"] == 101.0 and out["c"]["clock"] is True


def test_stack_subset_is_the_classed_pair_read_from_the_card():
    """TVB-39 F7: 0G 2026-08-31 shape, D = W exact (near_tf W) and M 34.59% away, class
    exact_shared: the converged stack is D+W, M is listed apart. A plain daily card with a far W:
    no pair."""
    c = card(
        **{
            "class": "exact_shared",
            "stack": [{"bar": "D"}, {"bar": "W"}, {"bar": "M"}],
            "entry": {"t": E, "price": 0.17296},
        }
    )
    c["extras"]["near_tf"] = "W"
    levels = [
        {"tf": "D", "price": 0.17296},
        {"tf": "W", "price": 0.17296},
        {"tf": "M", "price": 0.23279},
    ]
    plain = card(**{"class": "plain", "stack": [{"bar": "D"}, {"bar": "W"}]})
    out = run_js(
        f"const t = prep({json.dumps(c)}); out.s = C.stackSubset(t, {json.dumps(levels)}); out.w = C.stackWords(t, {json.dumps(levels)}).text;"
        f"out.p = C.stackSubset(prep({json.dumps(plain)}), {json.dumps([{'tf': 'D', 'price': 100.0}, {'tf': 'W', 'price': 102.0}])});"
    )
    assert [lv["tf"] for lv in out["s"]["conv"]] == ["D", "W"]
    assert [lv["tf"] for lv in out["s"]["far"]] == ["M"]
    assert abs(out["s"]["far"][0]["gap"] - 34.59) < 0.01
    assert out["w"].startswith("D+W same price; M +34.59% beyond")
    assert [lv["tf"] for lv in out["p"]["conv"]] == ["D"] and [
        lv["tf"] for lv in out["p"]["far"]
    ] == ["W"]


def test_stack_subset_weekly_card_pairs_its_own_level_with_the_daily_only():
    """Cold review M3: a weekly unit is classed on its own level against the daily level
    (chance.stack_class); a monthly level in the same day's stack is listed apart."""
    weekly = card(
        bar="W", **{"class": "within1", "stack": [{"bar": "D"}, {"bar": "W"}, {"bar": "M"}]}
    )
    lv = [{"tf": "D", "price": 99.5}, {"tf": "W", "price": 100.0}, {"tf": "M", "price": 105.0}]
    out = run_js(
        f"const t = prep({json.dumps(weekly)}); out.w = C.stackSubset(t, {json.dumps(lv)}); out.t = C.stackWords(t, {json.dumps(lv)}).text;"
    )
    assert sorted(x["tf"] for x in out["w"]["conv"]) == ["D", "W"]
    assert [x["tf"] for x in out["w"]["far"]] == ["M"] and abs(
        out["w"]["far"][0]["gap"] - 5.0
    ) < 1e-9
    assert out["t"].startswith("D+W within 1%; M +5.00% beyond")


def test_cell_index_keeps_the_candle_on_both_sides_of_its_centre():
    """TVB-40 F2: 49% and 51% of the way through a cell both belong to that bar, on day bars and
    on month bars of unequal length."""
    bs = [{"t": T0 + i * DAY} for i in range(5)]
    months = [
        {"t": T0},
        {"t": T0 + 31 * DAY},
        {"t": T0 + 59 * DAY},
        {"t": T0 + 90 * DAY},
    ]  # Jan, Feb (28), Mar, Apr
    out = run_js(
        f"const bs = {json.dumps(bs)}; const ms = (f) => (bs[2].t + f * {DAY}) * 1000;"
        "out.a = C.cellIndex(bs, ms(0.49)); out.b = C.cellIndex(bs, ms(0.51)); out.c = C.cellIndex(bs, ms(0.999)); out.d = C.cellIndex(bs, ms(1.0)); out.e = C.cellIndex(bs, (bs[0].t - 5) * 1000);"
        f"const mb = {json.dumps(months)}; const feb = (f) => (mb[1].t + f * 28 * {DAY}) * 1000;"
        "out.f = C.cellIndex(mb, feb(0.49)); out.g = C.cellIndex(mb, feb(0.51)); out.h = C.cellIndex(mb, feb(0.999)); out.i = C.cellIndex(mb, feb(1.0)); out.j = C.cellIndex(mb, (mb[3].t + 40 * 86400) * 1000);"
    )
    assert out["a"] == 2 and out["b"] == 2 and out["c"] == 2
    assert out["d"] == 3 and out["e"] == 0
    assert out["f"] == 1 and out["g"] == 1 and out["h"] == 1 and out["i"] == 2 and out["j"] == 3


def test_run_registry_ladder_groups_and_colours():
    out = run_js(
        "out = { ladder: C.ladderBooks(), groups: C.groupNames(), hb: C.groupBooks('hourly clock'), head: C.headline(), ref: C.reference(), col: C.bookCol('C'), tgt: C.bookTarget('A'), res: C.bookRes('C_h') };"
    )
    assert out["ladder"] == ["C", "A", "B", "D", "D5", "ref"] and out["groups"] == [
        "hourly clock",
        "under water",
    ]
    assert (
        out["hb"] == ["C_h"]
        and out["head"] == "C"
        and out["ref"] == "ref"
        and out["col"] == "#3b82f6"
    )
    assert out["tgt"] == "T1" and out["res"] == "hour"


# ---------------------------------------------------------------- stats.js


def _items(*cards: dict) -> str:
    return (
        "["
        + ",".join(
            f"{{ coin: '{c.get('instrument', 'X')}', t: prep({json.dumps(c)}) }}" for c in cards
        )
        + "]"
    )


def test_drawdown_runs_on_daily_sums_not_within_the_day():
    """TVB-40 F1: +5% then -5% on the same day is a flat day (the engine's book_stats), not a 50-dollar dip."""
    a = with_books(card(instrument="A"), C=book("C", "clock", E + 3 * DAY, 105.0, 5.0))
    b = with_books(card(instrument="B"), C=book("C", "clock", E + 3 * DAY, 95.0, -5.0))
    a2 = with_books(
        card(instrument="A", entry={"t": E + DAY, "price": 100.0}),
        C=book("C", "clock", E + 4 * DAY, 97.0, -3.0),
    )
    out = run_js(
        f"const s = ST.bookStats({_items(a, b, a2)}, 'C', 1000); out = {{ dd: s.maxDD, total: s.total, curve: s.curve.map(p => p.v) }};"
    )
    assert out["curve"] == [0.0, -30.0]
    assert (
        out["dd"] == 30.0
    )  # peak 0 (clipped), trough -30 on day two; the within-day -50 is never scored


def test_month_summary_averages_over_filled_rows_only():
    """TVB-40 F5: a censored row is not a zero return."""
    a = with_books(card(instrument="A"), C=book("C", "clock", E + 3 * DAY, 96.0, -4.0))
    b = with_books(card(instrument="B"), C=book("C", "censored"))
    c = with_books(
        card(instrument="C", entry={"t": T0 + 32 * DAY, "price": 100.0}),
        C=book("C", "clock", T0 + 35 * DAY, 101.0, 1.0),
    )
    out = run_js(
        f"const m = ST.calendarDays({_items(a, b, c)}, 'C', 1000); out.jan = ST.monthSummary(m, {T0}, {T0 + 31 * DAY}); out.feb = ST.monthSummary(m, {T0 + 31 * DAY}, {T0 + 59 * DAY});"
        f"out.none = ST.monthSummary(ST.calendarDays({_items(b)}, 'C', 1000), {T0}, {T0 + 31 * DAY});"
    )
    assert out["jan"] == {"n": 2, "filled": 1, "usd": -40.0, "avg": -4.0}
    assert out["feb"]["n"] == 1 and out["feb"]["avg"] == 1.0
    assert out["none"]["n"] == 1 and out["none"]["filled"] == 0 and out["none"]["avg"] is None


def test_universe_table_decodes_into_rows_with_book_entries():
    u = {
        "epoch": "2020-01-01",
        "instruments": ["X", "Y"],
        "books": ["C", "A"],
        "codes": {
            "bar": ["D", "W", "M"],
            "kind": ["reversal", "continuation", "inside", "outside"],
            "dir": ["up", "down"],
            "how": ["target", "one_r", "stop", "clock", "cap", "censored", "none"],
            "class": ["plain"],
            "x:flag": ["none", "third"],
        },
        "n": 2,
        "cols": {
            "instrument": [0, 1],
            "date": [2200, 2201],
            "bar": [0, 1],
            "kind": [0, 2],
            "dir": [0, 1],
            "class": [0, -1],
            "t1": [1, 0],
            "C:ret": [1.0, None],
            "C:how": [3, 5],
            "C:days": [3, -1],
            "C:hit": [-1, -1],
            "A:ret": [3.0, None],
            "A:how": [0, 5],
            "A:days": [2, -1],
            "A:hit": [1, -1],
            "x:liquid": [1, 0],
            "x:flag": [0, 1],
        },
    }
    out = run_js(
        f"const rows = ST.fromUniverse({json.dumps(u)}); out = {{ a: rows[0], b: rows[1], r: ST.retOf(rows[0], 'A'), d: ST.daysOf(rows[0], 'C'), h: ST.hitOf(rows[0], 'A') }};"
    )
    assert (
        out["a"]["coin"] == "X"
        and out["a"]["tf"] == "D"
        and out["a"]["kind"] == "reversal"
        and out["a"]["liquid"] is True
        and out["a"]["flag"] == "none"
    )
    assert (
        out["b"]["tf"] == "W"
        and out["b"]["direction"] == "down"
        and out["b"]["cls"] is None
        and out["b"]["flag"] == "third"
        and out["b"]["t1"] is None
    )
    assert out["r"] == 3.0 and out["d"] == 3 and out["h"] is True
    assert out["b"]["byBook"]["C"]["how"] == "censored" and out["b"]["byBook"]["C"]["ret"] is None


# ---------------------------------------------------------------- story.js


def _story(c: dict, book: str, n_days: int = 40, hourly: bool = False) -> str:
    return run_js(
        f"const cal = C.makeCalendar({{ daily: {json.dumps(_daily(n_days))}, hourly: {json.dumps(_hourly(n_days) if hourly else [])} }});"
        f"out.s = S.narrate({{ t: prep({json.dumps(c)}, cal), coin: 'X', cal, book: '{book}', size: 1000, p: 2 }});"
    )["s"]


def _book_paragraph(s: str, book: str) -> str:
    return s.split("What book " + book + " did.")[1].split("</p>")[0].replace("</b>", "").strip()


def test_book_d5_narrates_its_own_exit_day_never_book_c_s_clock():
    """TVB-41 Codex audit F1 (BLUR 2026-07-24 W short shape): the headline is open at day 20 while
    D5 leaves on the daily clock on day 24; the D5 paragraph names day 24 and the headline's cap,
    never the day-20 marking sentence. A monthly unit the same; a daily unit where both clocks
    are one exit carries no headline sentence."""
    for unit, k in (("W", 24), ("M", 45)):
        c = with_books(
            card(
                bar=unit,
                direction="down",
                one_r=None,
                touches={"one_r": None, "far": None},
                targets=[],
            ),
            C=book("C", "cap", E + 20 * DAY, 112.8, 12.8),
            A=book("A", "cap", E + 20 * DAY, 112.8, 12.8, None),
            D=book("D", "cap", E + 20 * DAY, 112.8, 12.8, False),
            D5=book("D5", "clock", E + k * DAY, 113.1, 13.1, False),
            ref=book("ref", "cap", E + 35 * DAY, 101.5, 1.5, False),
        )
        para = _book_paragraph(_story(c, "D5", n_days=70), "D5")
        assert (
            f"on day {k}" in para
            and "past the headline's cap (day 20)" in para
            and "book c is marked open" in para.lower()
        )
        assert "marked at the cap" not in para.split("That is past")[0] and "+13.10%" in para
    same = _book_paragraph(
        _story(with_books(card(), D5=book("D5", "clock", E + 3 * DAY, 101.0, 1.0, False)), "D5"),
        "D5",
    )
    assert (
        "on day 3" in same
        and "headline" not in same
        and "One R at 102.00 was not touched before the exit" in same
    )


def test_hourly_clock_is_worded_in_the_trade_s_own_colours():
    """TVB-40 F3 (BTC 2026-03-18 daily short shape): the hour's close is read against its open in
    the trade's direction; the entry hour and the hours held come from the card."""
    tape_up = _hourly(40)
    tape_up[9 * 24 + 7][4] = (
        100.5  # the exit hour for the short closes above its open: green, against a short
    )
    short = with_books(
        card(direction="down"),
        C_h=book("C_h", "clock", E + 7 * HOUR, 100.5, -0.5, entry=E + 2 * HOUR),
    )
    s = run_js(
        f"const cal = C.makeCalendar({{ daily: {json.dumps(_daily(40))}, hourly: {json.dumps(tape_up)} }});"
        f"out.s = S.narrate({{ t: prep({json.dumps(short)}, cal), coin: 'X', cal, book: 'C_h', size: 1000, p: 2 }});"
    )["s"]
    para = _book_paragraph(s, "C_h")
    assert (
        "5 hours after its entry hour" in para and "closed green at 100.50, above its open" in para
    )
    assert "Hourly clock (entered at 2026-01-10 02:00 UTC): exit only: out after 5 h, -0.50%." in s
    # a one-R fill known only to the day inside an hourly book: no hours are claimed for it
    dayres = with_books(
        short,
        D_h=book(
            "D_h",
            "one_r",
            E + 2 * HOUR,
            98.0,
            2.0,
            True,
            entry=E + 2 * HOUR,
            resolution="day",
            note="the touch hour is not in the row; the day is (day resolution)",
        ),
    )
    s2 = run_js(
        f"const cal = C.makeCalendar({{ daily: {json.dumps(_daily(40))}, hourly: {json.dumps(tape_up)} }});"
        "C.setRun(Object.assign({}, C.getRun(), { books: C.getRun().books.concat([{ id: 'D_h', name: 'one R, hourly clock', role: 'clock', resolution: 'hour', group: 'hourly clock', target: 'one_r', rule: 'One R or the hourly exit.' }]) }));"
        f"out.s = S.narrate({{ t: prep({json.dumps(dayres)}, cal), coin: 'X', cal, book: 'D_h', size: 1000, p: 2 }});"
    )["s"]
    assert "one R: one R on the entry day, +2.00%" in s2 and "after -" not in s2
    assert "One R at 98.00 was touched on the entry day" in _book_paragraph(s2, "D_h")


def test_clock_sentences_read_the_bar_not_the_trade_direction():
    """TVB-42 audit F5 (0G 2025-10-01 daily long, under water): the exit day closed GREEN above
    its open, yet the sentence said "below its open" because the word came from the trade's
    direction. Every stated relationship now comes from the two prices compared. The hourly
    branch says which side the day was on AT THE EXIT HOUR (the hour's close against the day's
    open), not where the day finally closed."""
    daily = _daily(40)
    daily[9 + 3][1] = 100.0
    daily[9 + 3][4] = 101.0  # day 3 closes green, above its open
    c = with_books(card(), C_u=book("C_u", "clock", E + 3 * DAY, 99.0, -1.0))
    s = run_js(
        f"const cal = C.makeCalendar({{ daily: {json.dumps(daily)}, hourly: [] }});"
        f"out.s = S.narrate({{ t: prep({json.dumps(c)}, cal), coin: 'X', cal, book: 'C_u', size: 1000, p: 2 }});"
    )["s"]
    para = _book_paragraph(s, "C_u")
    assert "closed green at 101.00, above its open 100.00" in para
    assert "below its open" not in para and "two tests are one" not in para
    # the hourly branch: the exit hour closes above the day's open while the day's final close is below it
    hourly = _hourly(40)
    k = 9 * 24 + 7
    hourly[k][4] = 100.5  # the exit hour closes green, above the day's open 100
    daily2 = _daily(40)
    daily2[9][4] = 99.0  # the day later closes red
    short = with_books(
        card(direction="down"),
        C_h=book("C_h", "clock", E + 7 * HOUR, 100.5, -0.5, entry=E + 2 * HOUR),
    )
    s2 = run_js(
        f"const cal = C.makeCalendar({{ daily: {json.dumps(daily2)}, hourly: {json.dumps(hourly)} }});"
        f"out.s = S.narrate({{ t: prep({json.dumps(short)}, cal), coin: 'X', cal, book: 'C_h', size: 1000, p: 2 }});"
    )["s"]
    para2 = _book_paragraph(s2, "C_h")
    assert "with the day green at that hour (above the day's open 100.00)" in para2
    assert "with the day red" not in para2
    # a flat hour reads level with its open, never a direction word
    hourly[k][4] = 100.0
    s3 = run_js(
        f"const cal = C.makeCalendar({{ daily: {json.dumps(daily2)}, hourly: {json.dumps(hourly)} }});"
        f"out.s = S.narrate({{ t: prep({json.dumps(short)}, cal), coin: 'X', cal, book: 'C_h', size: 1000, p: 2 }});"
    )["s"]
    assert "closed flat at 100.00, level with its open" in _book_paragraph(s3, "C_h")


def test_target_share_carries_its_denominator():
    """TVB-42 audit F6: "at target" divides by the filled trades that HAD a target (hit null =
    no target), so the page shows that count beside the share and names it in the note."""
    a = with_books(card(instrument="A"), B=book("B", "clock", E + 3 * DAY, 101.0, 1.0, None))
    b = with_books(
        card(
            instrument="B",
            targets=[
                {"name": "T1", "price": 103.0, "source": "anchor", "touched": E + 2 * DAY},
                {"name": "T2", "price": 105.0, "source": "W", "touched": E + 2 * DAY},
            ],
        ),
        B=book("B", "target", E + 2 * DAY, 105.0, 5.0, True),
    )
    out = run_js(f"const s = ST.bookStats({_items(a, b)}, 'B', 1000); out = s;")
    assert out["filled"] == 2 and out["withTarget"] == 1 and out["targets"] == 1
    assert out["target"] == 1.0 and out["targetAll"] == 0.5
    src = (VIEWER / "app.js").read_text(encoding="utf-8")
    assert "fmtCount(s.withTarget)" in src and "with one" in src
    assert "share of the book's filled trades that had a target" in src
    assert "share of filled trades that left at the book's target" not in src


def test_run_switch_reloads_the_universe_and_drops_stale_loads():
    """TVB-42 audit F7 (DOM-bound, checked at the source): loadRun bumps a generation every
    async load compares before writing state, and reloads the universe when a retained scope
    (Compare on every instrument, the all-instrument calendar) needs it."""
    src = (VIEWER / "app.js").read_text(encoding="utf-8")
    load_run = src.split("async function loadRun(id) {")[1].split("async function openCoin")[0]
    assert "++state.gen" in load_run and "if (gen !== state.gen) return false;" in load_run
    assert 'state.cmpScope === "universe" || state.calScope === "all"' in load_run
    assert "await loadUniverse()" in load_run
    uni = src.split("async function loadUniverse() {")[1].split("function universeItems")[0]
    assert "const gen = state.gen" in uni and "if (gen !== state.gen) return null;" in uni
    assert "state.uniLoading" in uni
    coin = src.split("async function loadCoin(coin) {")[1].split("async function select")[0]
    assert "if (gen !== state.gen) return false;" in coin
    assert "if (!(await loadRun(e.target.value))) return;" in src
    # the in-session Codex review of the fold (#5-#7): while a switch is in flight no loader has a
    # base to read (the generation alone was not enough: a load could capture the new generation
    # with the old address); select and applyDate commit nothing when the run changed under them;
    # a failed universe load is said on the page, not spun on
    assert "state.runId = null; state.base = null; state.index = null;" in load_run
    assert "if (!state.base) return null;" in uni and "state.uniError" in uni
    assert "if (!state.index || !state.base) return false;" in coin
    sel = src.split("async function select(k) {")[1].split("function syncHash")[0]
    assert "!(await loadCoin(it.coin))) return;" in sel
    apply = src.split("async function applyDate(date) {")[1].split("// ---")[0]
    assert "if (gen !== state.gen) return;" in apply
    assert "the universe table failed to load" in src


def test_compare_across_runs_lines_books_up_by_role():
    """Stage 3: another run's ladder books line up with this run's by ROLE, in each run's order,
    whatever the ids; a side with fewer books of a role leaves a gap. The page wires an
    "Against run" select, a by-role table over both universe tables and a dashed headline curve."""
    a = [
        {"id": "C", "role": "headline", "name": "exit only"},
        {"id": "A", "role": "target", "name": "all out at T1"},
        {"id": "B", "role": "target", "name": "hold through T2"},
        {"id": "ref", "role": "reference", "name": "chance book"},
    ]
    b = [
        {"id": "H", "role": "headline", "name": "session clock"},
        {"id": "T", "role": "target", "name": "T1"},
        {"id": "S", "role": "stop", "name": "setup stop"},
    ]
    out = run_js(
        f"out.r = ST.roleRows({json.dumps(a)}, {json.dumps(b)}).map(r => [r.role, r.a && r.a.id, r.b && r.b.id]);"
    )
    assert out["r"] == [
        ["headline", "C", "H"],
        ["target", "A", "T"],
        ["target", "B", None],
        ["stop", None, "S"],
        ["reference", "ref", None],
    ]
    src = (VIEWER / "app.js").read_text(encoding="utf-8")
    html = (VIEWER / "index.html").read_text(encoding="utf-8")
    assert 'id="cmpRun"' in html and 'id="byRoleCard"' in html
    assert "async function loadOther(" in src and "function renderByRole(" in src
    assert "ST.roleRows(ladderBooks().map((id) => bookOf(id)), o.books)" in src
    assert 'q.push("cmpRun="' in src and 'cmpRun: g("cmpRun")' in src and "fillRunCompare();" in src
    assert "otherS.strokes.template.setAll({ strokeWidth: 1.5, strokeDasharray: [4, 3] })" in src


def test_open_card_without_a_target_is_not_told_it_left_with_the_clock():
    """TVB-40 F3 (ADA 2024-01-30 book A shape): open at the cap, T1 never touched."""
    c = with_books(
        card(targets=[{"name": "T1", "price": 103.0, "source": "anchor", "touched": None}]),
        C=book("C", "cap", E + 20 * DAY, 100.5, 0.5),
        A=book("A", "cap", E + 20 * DAY, 100.5, 0.5, False),
    )
    para = _book_paragraph(_story(c, "A"), "A")
    assert "T1 at 103.00 was never touched inside the window, so it rode the exit" in para
    assert "marked at the cap on day 20" in para and "exit clock fired" not in para


def test_same_day_stop_and_one_r_tie_is_not_told_as_stop_first():
    """TVB-40 F3 (BTC 2023-04-09 chance-book shape): the stop and one R touched the same day."""
    tie = with_books(
        card(touches={"one_r": E, "far": E}), ref=book("ref", "stop", E, 98.0, -2.0, False)
    )
    s = _story(tie, "ref")
    assert "before one R" not in s and "cannot say which came first" in s and "takes the stop" in s
    later = _story(
        with_books(
            card(touches={"one_r": E + 3 * DAY, "far": E + DAY}),
            ref=book("ref", "stop", E + DAY, 98.0, -2.0, False),
        ),
        "ref",
    )
    assert "before one R" in later
    never = _story(
        with_books(
            card(touches={"one_r": None, "far": E + DAY}),
            ref=book("ref", "stop", E + DAY, 98.0, -2.0, False),
        ),
        "ref",
    )
    assert "before one R" not in never and "never touched" in never


def test_missing_book_is_named_not_borrowed():
    """TVB-39 F6 in words: the chance book censored while book C exited at -1.09% on day 1; the
    chance paragraph names its own status and carries none of book C's figures."""
    c = with_books(card(), C=book("C", "clock", E + DAY, 98.91, -1.09), ref=book("ref", "censored"))
    para = _book_paragraph(_story(c, "ref"), "ref")
    assert para.startswith("The chance book has no result")
    assert "-1.09" not in para and "exit clock" not in para and "day 1" not in para
    d5 = with_books(
        card(),
        C=book("C", "censored"),
        D5=book("D5", "none", note="not scored: the headline row is censored"),
    )
    assert "not scored: the headline row is censored" in _book_paragraph(_story(d5, "D5"), "D5")


def test_travel_is_labelled_as_the_headline_window():
    """TVB-40 F4: the travel columns are measured through the headline exit whatever book is selected."""
    assert "book C's exit (the headline window" in _story(card(), "ref")


def test_stack_sentence_names_the_converged_subset_and_the_far_level_apart():
    """TVB-39 F7 in words: D = W exact (near_tf W), M far."""
    c = card(
        **{
            "class": "exact_shared",
            "stack": [{"bar": "D"}, {"bar": "W"}, {"bar": "M"}],
            "entry": {"t": T0 + 20 * DAY, "price": 100.0},
        }
    )
    c["extras"]["near_tf"] = "W"
    for b in c["books"]:
        if b["at"] is not None:
            b["at"] += 11 * DAY
    c["targets"][0]["touched"] += 11 * DAY
    c["touches"] = {"one_r": T0 + 21 * DAY, "far": T0 + 21 * DAY}
    # a tape from December 2025 so a complete week and month sit before the entry; every high is 100, so the day's and
    # the week's levels are 100 (exact); the month before is then given a high of 130 (far)
    daily = _daily(70, start=T0 - 31 * DAY)
    for b in daily:
        b[2] = 100.0
    out = run_js(
        f"const daily = {json.dumps(daily)}; const cal = C.makeCalendar({{ daily, hourly: [] }});"
        "const i = cal.dayIdx.get('2026-01-21'); const m = cal.months.find(b => b.days.includes(i));"
        "const mi = cal.months.indexOf(m); cal.months[mi - 1].h = 130.0;"
        f"const t = prep({json.dumps(c)}, cal); out.levels = C.stackLevels(t, i, cal); out.s = S.narrate({{ t, coin: 'X', cal, book: 'C', size: 1000, p: 2 }});"
    )
    assert [lv["price"] for lv in out["levels"]] == [100.0, 100.0, 130.0]
    assert "the week's level 100.00 (same price" in out["s"]
    assert "the month's level 130.00 also broke the same day, +30.00% beyond the entry" in out["s"]
    assert "not part of the converged stack" in out["s"]


def test_unreachable_one_r_is_said_in_words_not_as_a_price():
    """339 shorts carry a one R at or below zero: the card has no one-R price; the plan says why,
    the D book says it rides the exit."""
    c = with_books(
        card(
            direction="down",
            far=260.0,
            one_r=None,
            r_pct=160.0,
            touches={"one_r": None, "far": None},
            extras={
                "liquid": True,
                "flag": "none",
                "anchor": "anchor",
                "dex": "main",
                "one_r_raw": -60.0,
            },
        ),
        D=book(
            "D",
            "clock",
            E + 3 * DAY,
            99.0,
            1.0,
            None,
            note="one R lies at or below zero for this short: no one-R fill is possible",
        ),
    )
    s = _story(c, "D")
    assert "one R would lie at or below zero" in s and "the engine's figure: -60.00" in s
    para = _book_paragraph(s, "D")
    assert "This trade has no one R (it lies at or below zero), so the book rides the exit" in para


def test_ladder_lists_ladder_books_then_groups_and_the_playbook_reads_the_run():
    out = run_js(
        f"const cal = C.makeCalendar({{ daily: {json.dumps(_daily(40))}, hourly: [] }});"
        f"const t = prep({json.dumps(card())}, cal); out.l = S.ladder({{ t, cal, book: 'A', size: 1000, p: 2 }}); out.p = S.playbook(C.getRun());"
    )
    ladder = out["l"]
    assert (
        ladder.index('data-book="C"')
        < ladder.index('data-book="A"')
        < ladder.index('data-book="ref"')
        < ladder.index("hourly clock")
        < ladder.index('data-book="C_h"')
    )
    assert (
        "all out at T1" in ladder
        and "not scored: outside the venue's hourly window" in ladder
        and "book A fills at 103.00" in ladder
    )
    assert "<h1>a test run</h1>" in out["p"] and "takes T1" in out["p"] and "00:00 UTC" in out["p"]


def test_app_wiring_resort_cell_index_entry_hour_no_fallback_runs():
    """TVB-40 F6 / F2, the cold review's M1 and stage 2 in app.js (DOM-bound, so checked at the source)."""
    src = (VIEWER / "app.js").read_text(encoding="utf-8")
    set_book = src.split("function setBook(b) {")[1].split("}")[0]
    assert "sortItems();" in set_book
    magnet = src.split("function magnetDrop(pane, local) {")[1].split("pane.save.saveData();")[0]
    assert "cellIndex(bs, tMs)" in magnet and "Math.abs(b.t * MS - tMs)" not in magnet
    assert (
        "?? ks[0]" not in src and "|| ks[0]" not in src
    )  # no first-candle fallback for a touch marker
    assert (
        "hourEntry(t, st)" in src and "bs[k].h > t.level" in src
    )  # the 1H entry arrow at the recorded entry hour, else a strict break
    assert (
        'getJson("data/runs.json")' in src and '"data/runs/" + id + "/"' in src
    )  # the page reads runs
    assert (
        'fetch(url, { cache: "no-cache" })' in src and "await (await fetch(" not in src
    )  # every JSON revalidated
    assert (
        "ret_C" not in src and "exit_k" not in src and "status_h" not in src
    )  # no engine column names survive in the page
    for f in ("core.js", "story.js", "stats.js"):
        js = (VIEWER / f).read_text(encoding="utf-8")
        assert "ret_C" not in js and "hit_A" not in js and "status5" not in js, f


def test_run_switch_restarts_a_pending_comparison_under_the_new_generation():
    """TVB-43 audit F3 (DOM-bound, checked at the source): a comparison load that a run switch
    overtook was dropped by its generation check and nobody cleared its loading state, so Compare
    read "loading run B..." until the user touched the select. loadRun now restarts a comparison
    that has no table yet (loading or failed) under the new generation, after fillRunCompare has
    dropped one that became the current run."""
    src = (VIEWER / "app.js").read_text(encoding="utf-8")
    load_run = src.split("async function loadRun(id) {")[1].split("async function openCoin")[0]
    # the in-session Codex pass (TVB-44): the restart runs on the FAILED switch too (the catch restored the
    # old run and left the comparison loading), it comes after the page's metadata writes (no await between
    # the generation check and those writes, so a later switch cannot be overwritten), and it re-checks the
    # generation before the universe load
    catch_path = load_run.split("} catch (e) {")[1].split("if (gen !== state.gen) return false;")[0]
    assert "Object.assign(state, prev);" in catch_path and "await resumeOther(gen);" in catch_path
    after = load_run.split("fillRunCompare();")[1]
    meta, rest = after.split("await resumeOther(gen);")
    code = "\n".join(ln for ln in meta.splitlines() if not ln.strip().startswith("//"))
    assert (
        '$("meta").textContent' in code
        and 'localStorage.setItem("domino-run", id)' in code
        and "await " not in code
    )
    assert rest.lstrip().startswith("if (gen !== state.gen) return false;")
    resume = src.split("async function resumeOther(gen) {")[1].split("function renderByRole")[0]
    assert "state.other.uni" in resume and "await loadOther(oid);" in resume
    assert "if (oid === state.runId) { state.other = null; return; }" in resume
    # every comparison request carries its own number: a stale request for the SAME run under the same
    # generation can neither overwrite a newer success nor turn it into an error
    other = src.split("async function loadOther(id) {")[1].split("async function resumeOther")[0]
    assert "req = ++state.otherReq" in other and "state.other.req === req" in other
    assert (
        "if (!mine()) return null;" in other
        and "if (mine()) state.other = { id, req, error:" in other
    )
    assert "otherReq: 0" in src
    fill = src.split("function fillRunCompare() {")[1].split("sel.value = state.other")[0]
    assert "if (state.other && state.other.id === state.runId) state.other = null;" in fill


def test_a_card_whose_session_opened_past_the_trigger_says_so():
    """TVB-43 audit F1, the card side (the bench's prereg amendment 2026-11-02): a session tape
    can open past the trigger; the card carries `extras.gap` (open / untraded) and
    `extras.session_open`, and the story says the fill at the trigger was not on offer at the
    open, in the trade's own words (a short's gap opens BELOW the trigger). Run one's cards carry
    neither key and read as before."""
    daily = _daily(40)
    cal_js = f"const cal = C.makeCalendar({{ daily: {json.dumps(daily)}, hourly: [] }});"
    c = card()
    c["extras"] = dict(c.get("extras") or {}, gap="untraded", session_open=102.0)
    s = run_js(
        cal_js
        + f"out.s = S.narrate({{ t: prep({json.dumps(c)}, cal), coin: 'X', cal, book: 'C', size: 1000, p: 2 }});"
    )["s"]
    assert (
        "The session opened at 102.00, above the trigger, so a fill at the trigger was not on offer at the open"
        in s
    )
    assert "did not print at all that session" in s and "open-fill and missed-entry" in s
    o = card()
    o["extras"] = dict(o.get("extras") or {}, gap="open", session_open=101.0)
    s2 = run_js(
        cal_js
        + f"out.s = S.narrate({{ t: prep({json.dumps(o)}, cal), coin: 'X', cal, book: 'C', size: 1000, p: 2 }});"
    )["s"]
    assert "The session opened at 101.00, above the trigger" in s2 and "did not print" not in s2
    sh = card(direction="down")
    sh["extras"] = dict(sh.get("extras") or {}, gap="open", session_open=98.0)
    s3 = run_js(
        cal_js
        + f"out.s = S.narrate({{ t: prep({json.dumps(sh)}, cal), coin: 'X', cal, book: 'C', size: 1000, p: 2 }});"
    )["s"]
    assert "The session opened at 98.00, below the trigger" in s3
    plain = run_js(
        cal_js
        + f"out.s = S.narrate({{ t: prep({json.dumps(card())}, cal), coin: 'X', cal, book: 'C', size: 1000, p: 2 }});"
    )["s"]
    assert "session opened" not in plain
