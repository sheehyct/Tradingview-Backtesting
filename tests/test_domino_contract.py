"""The run and trade-card contract (viewer/CONTRACT.md): the validator refuses what does not fit
and names the card; the derived files have the page's shape; a single-file or zipped run
imports; the management book's rows map to cards exactly (times from the bar list by index,
prices from the recorded return)."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from analysis.domino import contract as K
from analysis.domino import run_export as X

DAY = 86_400
HOUR = 3_600
T0 = 1_767_225_600  # 2026-01-01 00:00 UTC


def bars(
    n: int, start: int = T0, step: int = DAY, skip: set[int] | None = None
) -> list[list[float]]:
    out = []
    for i in range(n):
        if skip and i in skip:
            continue
        out.append([start + i * step, 100.0, 101.0, 99.0, 100.0 + i, 1.0])
    return out


def run_doc(**kw) -> dict:
    base = {
        "contract": K.CONTRACT,
        "id": "test-run",
        "name": "a hand-made run",
        "as_of": "2026-01-31",
        "clock": {"day_roll": "00:00 UTC", "resolution": "day"},
        "units": ["D", "W"],
        "bars": ["1d"],
        "books": [
            {"id": "C", "name": "exit only", "role": "headline", "rule": "hold to the clock"},
            {"id": "A", "name": "all out at T1", "role": "target", "rule": "T1 or the exit"},
            {
                "id": "C_h",
                "name": "hourly clock",
                "role": "clock",
                "rule": "the hourly exit",
                "group": "hourly clock",
            },
        ],
    }
    base.update(kw)
    return base


def card(**kw) -> dict:
    base = {
        "id": "X-2026-01-03-D-reversal-up",
        "instrument": "X",
        "bar": "D",
        "pattern": "2-2 reversal",
        "kind": "reversal",
        "direction": "up",
        "class": "plain",
        "entry": {"t": T0 + 2 * DAY, "price": 100.0},
        "far": 98.0,
        "one_r": 102.0,
        "r_pct": 2.0,
        "targets": [{"name": "T1", "price": 103.0, "source": "anchor", "touched": T0 + 4 * DAY}],
        "touches": {"one_r": T0 + 3 * DAY, "far": None},
        "books": [
            {
                "id": "C",
                "how": "clock",
                "at": T0 + 5 * DAY,
                "price": 104.0,
                "ret": 4.0,
                "hit": None,
            },
            {
                "id": "A",
                "how": "target",
                "at": T0 + 4 * DAY,
                "price": 103.0,
                "ret": 3.0,
                "hit": True,
            },
            {
                "id": "C_h",
                "how": "none",
                "at": None,
                "price": None,
                "ret": None,
                "hit": None,
                "note": "outside the window",
            },
        ],
        "travel": {"mfe": 5.0, "mae": 0.5, "window": "C", "next_bar": "with"},
        "context": {"week_side": "with", "month_side": "against"},
        "extras": {"liquid": True, "flag": "none"},
    }
    base.update(kw)
    return base


def files_doc(cards: list[dict] | None = None, with_bars: bool = True) -> dict[str, dict]:
    return {
        "X.json": {
            "instrument": "X",
            "bars": {"1d": bars(10) if with_bars else []},
            "trades": cards or [card()],
        }
    }


# ---------------------------------------------------------------- the validator


def test_a_valid_run_has_no_problems():
    problems, warnings = K.validate(run_doc(), files_doc())
    assert problems == [] and warnings == []


@pytest.mark.parametrize(
    "mutate, expect",
    [
        (lambda r, f: r.update(contract=2), "contract version"),
        (lambda r, f: r.update(id="bad id"), "id must be"),
        (lambda r, f: r.pop("units"), "units must list"),
        (lambda r, f: r["clock"].update(resolution="tick"), "resolution must be"),
        (lambda r, f: r["books"][0].update(role="target"), "0 headline books"),
        (lambda r, f: r["books"][1].update(role="headline"), "2 headline books"),
        (lambda r, f: r["books"][1].update(id="C"), "declared twice"),
        (
            lambda r, f: f["X.json"]["trades"][0]["books"].append(
                {"id": "Z", "how": "clock", "at": T0 + 5 * DAY, "price": 1.0, "ret": 0.0}
            ),
            "book 'Z' is not declared",
        ),
        (lambda r, f: f["X.json"]["trades"][0]["books"][0].update(how="left"), "left by 'left'"),
        (
            lambda r, f: f["X.json"]["trades"][0]["books"][1].update(price=None),
            "book A left by target but has no price",
        ),
        (lambda r, f: f["X.json"]["trades"][0]["books"][0].update(at=T0), "before the entry"),
        (
            lambda r, f: f["X.json"]["trades"][0]["targets"][0].update(touched=None),
            "no target is recorded as touched by then",
        ),
        (
            lambda r, f: f["X.json"]["trades"][0]["books"][2].update(ret=1.0),
            "left by none must carry no time, price or return",
        ),
        (lambda r, f: f["X.json"]["trades"][0].update(kind="hammer"), "kind must be one of"),
        (
            lambda r, f: f["X.json"]["trades"][0].update(bar="M"),
            "bar 'M' is not one of the run's units",
        ),
        (lambda r, f: f["X.json"]["trades"].append(card()), "duplicate card id"),
        (
            lambda r, f: f["X.json"]["trades"][0].update(instrument="Y"),
            "instrument 'Y' inside X's file",
        ),
        (lambda r, f: f["X.json"]["bars"]["1d"].reverse(), "not in time order"),
        (
            lambda r, f: f["X.json"]["trades"][0]["entry"].update(price=-1),
            "entry.price must be a positive number",
        ),
        (
            lambda r, f: (
                f["X.json"]["trades"][0].update(touches={"one_r": T0 + 9 * DAY})
                or f["X.json"]["trades"][0]["books"].append(
                    {"id": "A", "how": "one_r", "at": T0 + 3 * DAY, "price": 102.0, "ret": 2.0}
                )
                or f["X.json"]["trades"][0]["books"].pop(1)
            ),
            "before one R's first touch",
        ),
    ],
)
def test_each_refusal_names_the_card_or_the_run(mutate, expect):
    run, files = run_doc(), files_doc()
    mutate(run, files)
    problems, _ = K.validate(run, files)
    assert any(expect in p for p in problems), problems
    assert all(p.startswith(("run:", "X card ", "X:")) for p in problems), problems


def test_warnings_for_no_bars_and_gaps():
    _, w = K.validate(run_doc(), files_doc(with_bars=False))
    assert any("no bars" in x for x in w)
    f = files_doc()
    f["X.json"]["bars"]["1d"] = bars(10, skip={4})
    _, w = K.validate(run_doc(), f)
    assert any("1 gaps" in x for x in w)


# ---------------------------------------------------------------- the derived files


def test_derived_files_have_the_page_shape():
    run = run_doc()
    d = K.Derive(run)
    d.add("X.json", files_doc()["X.json"])
    idx = d.index("2026-01-31T00:00:00Z")
    assert (
        idx["trades"] == 1
        and idx["instruments"][0]["first"] == T0
        and idx["instruments"][0]["bars"] == ["1d"]
    )
    assert d.dates["2026-01-03"] == [["X", "up", "D", "reversal", 4.0, "clock"]]
    u = d.universe()
    assert u["books"] == ["C", "A"]  # the grouped clock book stays on the cards
    assert (
        u["n"] == 1
        and u["cols"]["C:days"] == [3]
        and u["cols"]["A:hit"] == [1]
        and u["cols"]["A:ret"] == [3.0]
    )
    assert (
        u["cols"]["x:liquid"] == [1]
        and u["codes"]["x:flag"] == ["none"]
        and u["cols"]["x:flag"] == [0]
    )
    assert u["cols"]["date"] == [(T0 + 2 * DAY - int(K.UNI_EPOCH.timestamp())) // DAY]


# ---------------------------------------------------------------- import


def _single_file(tmp: Path) -> Path:
    doc = run_doc()
    doc["instruments"] = [{"instrument": "X", "bars": {"1d": bars(10)}, "trades": [card()]}]
    p = tmp / "phone_run.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    return p


def test_single_file_run_imports_and_is_listed(tmp_path: Path):
    root = tmp_path / "data"
    rid = K.import_run(_single_file(tmp_path), root, log=lambda s: None)
    dest = root / "runs" / rid
    assert {p.name for p in dest.iterdir()} == {
        "run.json",
        "X.json",
        "index.json",
        "dates.json",
        "universe.json",
    }
    runs = json.loads((root / "runs.json").read_text())
    assert runs[0]["id"] == "test-run" and runs[0]["trades"] == 1
    run = json.loads((dest / "run.json").read_text())
    assert run["instruments"][0]["file"] == "X.json" and "built" in run
    # re-import under another id adds a second listing; the same id replaces
    K.import_run(_single_file(tmp_path), root, run_id="again", log=lambda s: None)
    K.import_run(_single_file(tmp_path), root, log=lambda s: None)
    assert sorted(r["id"] for r in json.loads((root / "runs.json").read_text())) == [
        "again",
        "test-run",
    ]


def test_zip_and_folder_import_and_in_place_reimport(tmp_path: Path):
    folder = tmp_path / "src"
    folder.mkdir()
    (folder / "run.json").write_text(json.dumps(run_doc()), encoding="utf-8")
    (folder / "X.json").write_text(json.dumps(files_doc()["X.json"]), encoding="utf-8")
    z = tmp_path / "run.zip"
    with zipfile.ZipFile(z, "w") as zf:
        for p in folder.iterdir():
            zf.write(p, "inner/" + p.name)
    root = tmp_path / "data"
    assert K.import_run(z, root, log=lambda s: None) == "test-run"
    # an export in place: the source folder is the destination
    dest = root / "runs" / "test-run"
    assert K.import_run(dest, root, log=lambda s: None) == "test-run"
    assert (dest / "X.json").exists() and (dest / "universe.json").exists()


def test_an_unfit_run_is_refused_with_the_problems(tmp_path: Path):
    doc = run_doc()
    bad = card()
    bad["books"][1]["price"] = None
    doc["instruments"] = [{"instrument": "X", "bars": {}, "trades": [bad]}]
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(K.ContractError) as e:
        K.import_run(p, tmp_path / "data", log=lambda s: None)
    assert any("book A left by target but has no price" in x for x in e.value.problems)
    assert not (tmp_path / "data" / "runs" / "test-run").exists()
    problems, _ = K.check(p, log=lambda s: None)
    assert problems


# ---------------------------------------------------------------- the management book's mapping


def row(**kw) -> dict:
    base = {
        "date": "2026-01-03",
        "tf": "D",
        "kind": "reversal",
        "direction": "up",
        "cls": "plain",
        "stack": "D",
        "near_tf": None,
        "level": 100.0,
        "stop": 98.0,
        "r_pct": 2.0,
        "t1": 103.0,
        "t1_src": "anchor",
        "t2": None,
        "t2_src": None,
        "t3": None,
        "t3_src": None,
        "t1_k": 2,
        "t2_k": None,
        "t3_k": None,
        "one_r_k": 1,
        "mm1_k": None,
        "stop_k": None,
        "mm_t1": None,
        "status": "exit",
        "exit_k": 3,
        "days": 3,
        "ret_C": 4.0,
        "ret_A": 3.0,
        "hit_A": True,
        "ret_B": 4.0,
        "hit_B": False,
        "ret_D": 2.0,
        "hit_D": True,
        "status5": "exit",
        "ret_D5": 2.0,
        "hit_D5": True,
        "days_D5": 1,
        "out5": "stop",
        "ret5": -2.0,
        "days_ref": 1,
        "ref_k": 5,
        "status_h": None,
        "status_u": "exit",
        "exit_k_u": 3,
        "days_u": 3,
        "ret_C_u": 4.0,
        "ret_A_u": 3.0,
        "hit_A_u": True,
        "ret_D_u": 2.0,
        "hit_D_u": True,
        "mfe_x": 5.0,
        "mae_x": 0.5,
        "next_bar": "with",
        "w_support": "with",
        "m_support": "against",
        "liquid": True,
        "flag": "none",
        "anchor": "anchor",
        "ladder_len": 1,
        "reached1": True,
        "reached2": False,
        "reached3": False,
    }
    base.update(kw)
    return base


def tape_with_gap() -> X.Tape:
    # the entry day is index 2; index 4 is missing one calendar day (the census fills no gaps)
    daily = bars(12, skip={4})
    return X.Tape(daily, bars(24 * 12, step=HOUR))


def test_card_times_come_from_the_bar_list_by_index_and_prices_from_the_return():
    tape = tape_with_gap()
    c = X.card_from_row(row(), "X", "main", tape)
    t0 = T0 + 2 * DAY
    assert c["entry"] == {"t": t0, "price": 100.0} and c["one_r"] == 102.0 and c["far"] == 98.0
    by = {b["id"]: b for b in c["books"]}
    # exit_k = 3 index steps after the entry = bars[2 + 3]; with the gap at 4 that is day 6, not day 5
    assert (
        by["C"]["how"] == "clock"
        and by["C"]["at"] == T0 + 6 * DAY
        and by["C"]["price"] == 104.0
        and by["C"]["ret"] == 4.0
    )
    assert (
        by["A"]["how"] == "target"
        and by["A"]["at"] == T0 + 5 * DAY
        and by["A"]["price"] == 103.0
        and by["A"]["hit"] is True
    )
    assert (
        by["B"]["how"] == "clock"
        and by["B"]["at"] == by["C"]["at"]
        and by["B"]["ret"] == 4.0
        and by["B"]["hit"] is None
    )  # no T2
    assert by["D"]["how"] == "one_r" and by["D"]["at"] == T0 + 3 * DAY and by["D"]["price"] == 102.0
    assert (
        by["D5"]["how"] == "one_r"
        and by["ref"]["how"] == "stop"
        and by["ref"]["price"] == 98.0
        and by["ref"]["at"] == T0 + 3 * DAY
    )
    assert (
        by["C_h"]["how"] == "none"
        and "hourly window" in by["C_h"]["note"]
        and by["A_h"]["how"] == "none"
    )
    assert by["C_u"]["how"] == "clock" and by["D_u"]["how"] == "one_r"
    assert "C_own" not in by and "A_mm" not in by  # a daily unit, no measured move on this row
    assert c["targets"][0]["touched"] == T0 + 5 * DAY and c["touches"]["one_r"] == T0 + 3 * DAY
    assert c["extras"]["dex"] == "main" and c["context"] == {
        "week_side": "with",
        "month_side": "against",
    }
    run = X.run_card(1_791_504_000_000)
    assert (
        K.validate(run, {"X.json": {"instrument": "X", "bars": {"1d": tape.daily}, "trades": [c]}})[
            0
        ]
        == []
    )


def test_card_open_headline_with_d5_exit_later_and_the_hourly_clock():
    """The BLUR 2026-07-24 shape: the headline open at day 20, D5 out on its own day; the hourly
    clock entered at hour 2 and left 7 hours later."""
    tape = X.Tape(bars(40), bars(24 * 40, step=HOUR))
    r = row(
        tf="W",
        status="open",
        exit_k=None,
        days=20,
        ret_C=12.8,
        ret_A=12.8,
        hit_A=False,
        ret_D=12.8,
        hit_D=False,
        status5="exit",
        hit_D5=False,
        ret_D5=13.1,
        days_D5=24,
        out5="neither",
        ret5=1.5,
        days_ref=35,
        one_r_k=None,
        t1_k=None,
        status_h="exit",
        entry_h=2,
        hours_h=7,
        exit_h=7,
        ret_C_h=-0.4,
        ret_A_h=-0.4,
        hit_A_h=False,
        ret_D_h=-0.4,
        hit_D_h=False,
        t1_h=None,
        status_u="open",
        exit_k_u=None,
        days_u=20,
        ret_C_u=12.8,
        hit_A_u=False,
        hit_D_u=False,
        ret_A_u=12.8,
        ret_D_u=12.8,
        status_own="exit",
        days_own=27,
        ret_C_own=10.0,
        ret_A_own=10.0,
        reached1_own=False,
        status_long="open",
        days_long=140,
        ret_C_long=20.0,
        ret_A_long=20.0,
        reached1_long=False,
    )
    c = X.card_from_row(r, "BLUR", "main", tape)
    t0 = T0 + 2 * DAY
    by = {b["id"]: b for b in c["books"]}
    assert (
        by["C"]["how"] == "cap"
        and by["C"]["at"] == t0 + 20 * DAY
        and abs(by["C"]["price"] - 112.8) < 1e-9
    )
    assert (
        by["D5"]["how"] == "clock" and by["D5"]["at"] == t0 + 24 * DAY and by["D5"]["hit"] is False
    )
    assert by["ref"]["how"] == "cap" and by["ref"]["at"] == t0 + 35 * DAY
    assert (
        by["C_h"]["how"] == "clock"
        and by["C_h"]["at"] == t0 + 2 * HOUR + 7 * HOUR
        and abs(by["C_h"]["price"] - 99.6) < 1e-9
    )
    assert (
        by["A_h"]["how"] == "clock"
        and by["A_h"]["at"] == by["C_h"]["at"]
        and by["A_h"]["hit"] is False
    )
    assert (
        by["C_u"]["how"] == "cap"
        and by["C_own"]["how"] == "clock"
        and by["C_own"]["at"] == t0 + 27 * DAY
    )
    assert (
        by["C_long"]["how"] == "cap"
        and by["A_long"]["how"] == "cap"
        and by["A_long"]["ret"] == 20.0
    )
    assert c["bar"] == "W"
    assert (
        K.validate(
            X.run_card(1_791_504_000_000),
            {"BLUR.json": {"instrument": "BLUR", "bars": {"1d": tape.daily}, "trades": [c]}},
        )[0]
        == []
    )


def test_card_with_a_censored_headline_keeps_the_chance_book_and_says_why_the_rest_is_unscored():
    tape = X.Tape(bars(12), [])
    r = row(
        status="censored",
        exit_k=None,
        days=None,
        ret_C=None,
        ret_A=None,
        hit_A=None,
        ret_B=None,
        hit_B=None,
        ret_D=None,
        hit_D=None,
        status5=None,
        ret_D5=None,
        hit_D5=None,
        days_D5=None,
        status_u=None,
        ret_C_u=None,
        out5="one_r",
        ret5=2.0,
        days_ref=1,
        mfe_x=None,
        mae_x=None,
    )
    c = X.card_from_row(r, "X", "xyz", tape)
    by = {b["id"]: b for b in c["books"]}
    assert (
        by["C"]["how"] == "censored"
        and by["A"]["how"] == "censored"
        and by["D"]["how"] == "censored"
    )
    assert by["D5"]["how"] == "none" and "headline row is censored" in by["D5"]["note"]
    assert by["C_u"]["how"] == "none" and by["A_u"]["how"] == "none"
    assert by["ref"]["how"] == "one_r" and by["ref"]["price"] == 102.0 and by["ref"]["ret"] == 2.0
    assert (
        K.validate(
            X.run_card(1_791_504_000_000),
            {"X.json": {"instrument": "X", "bars": {"1d": tape.daily}, "trades": [c]}},
        )[0]
        == []
    )


def test_a_short_whose_one_r_lies_below_zero_carries_no_one_r_price():
    """339 monthly / weekly shorts in the management book have a setup range larger than the
    price: the engine's one R is at or below zero and can never fill. The card says so instead
    of carrying a negative price (the validator refuses one); the raw numbers stay in extras."""
    tape = X.Tape(bars(12), [])
    r = row(
        direction="down",
        stop=260.0,
        r_pct=160.0,
        one_r_k=None,
        hit_D=False,
        hit_D5=False,
        ret_D=4.0,
        ret_D5=4.0,
        days_D5=3,
        out5="neither",
        ret5=1.0,
        days_ref=5,
        mm_t1=-3.0,
        hit_A_mm=False,
        ret_A_mm=4.0,
        hit_D_u=False,
    )
    c = X.card_from_row(r, "BRETT", "main", tape)
    by = {b["id"]: b for b in c["books"]}
    assert c["one_r"] is None and c["far"] == 260.0
    assert c["extras"]["one_r_raw"] == -60.0 and c["extras"]["mm_raw"] == -3.0
    assert (
        by["D"]["how"] == "clock" and by["D"]["hit"] is None and "no one-R fill" in by["D"]["note"]
    )
    assert by["D5"]["how"] == "clock" and by["D5"]["hit"] is None
    assert by["D_u"]["hit"] is None and "no one-R fill" in by["D_u"]["note"]
    assert by["ref"]["how"] == "cap" and by["ref"]["ret"] == 1.0
    assert "A_mm" not in by and not any(t["name"] == "mm" for t in c["targets"])
    assert (
        K.validate(
            X.run_card(1_791_504_000_000),
            {"BRETT.json": {"instrument": "BRETT", "bars": {"1d": tape.daily}, "trades": [c]}},
        )[0]
        == []
    )


def test_run_card_declares_every_book_the_cards_use_and_one_headline():
    run = X.run_card(1_791_504_000_000, "mb")
    assert run["id"] == "mb" and K.validate_run(run) == []
    assert sum(b["role"] == "headline" for b in run["books"]) == 1
    assert K.ladder_books(run) == ["C", "A", "B", "D", "D5", "ref"]
