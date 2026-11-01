"""The run and trade-card contract (`viewer/CONTRACT.md`): the validator, the files the page
reads beside a run (index, dates, universe) and the importer.

No trade logic lives here. A run is read from a folder, a single JSON file or a zip, checked in
plain words (a card is named in every message), laid out under `viewer/data/runs/<id>/` and
listed in `viewer/data/runs.json`. Anything that writes the shape, in this workspace or on a
phone, goes through the same gate as the management book's own export.
"""

from __future__ import annotations

import json
import math
import shutil
import tempfile
import zipfile
from bisect import bisect_right
from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator
from datetime import datetime, timezone
from pathlib import Path

CONTRACT = 1
HOW = ("target", "one_r", "stop", "clock", "cap", "censored", "none")
HOW_PRICED = ("target", "one_r", "stop", "clock")  # these need a time, a price and a return
ROLES = ("headline", "target", "stop", "clock", "reference")
LADDER_ROLES = ("headline", "target", "stop", "reference")  # the books Compare lines up
RESOLUTIONS = ("day", "hour", "minute")
CALENDARS = (
    "utc_day",
    "session",
)  # every calendar day is a bar | sparse sessions (no weekend, holidays)
KINDS = ("reversal", "continuation", "inside", "outside")
DIRECTIONS = ("up", "down")
DERIVED = ("index.json", "dates.json", "universe.json")
UNI_EPOCH = datetime(2020, 1, 1, tzinfo=timezone.utc)
UNI_MAX_CODES = 16  # an extras key with more distinct strings than this stays off the table
DAY = 86_400
SIZE_SECONDS = {"m": 60, "h": 3_600, "d": DAY}


class ContractError(ValueError):
    """A run that does not fit the contract; `.problems` lists what, card by card."""

    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


# ----------------------------------------------------------------------------- small checks


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _time(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v > 0


def _price(v) -> bool:
    return _num(v) and v > 0


# Windows names a file or folder by these words whatever follows the dot (NUL.json is the device)
RESERVED = (
    {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(10)} | {f"LPT{i}" for i in range(10)}
)


def _reserved(stem: str) -> bool:
    return stem.split(".")[0].upper() in RESERVED


def _slug(s) -> bool:
    """A run or book id: letters, digits, dot, dash or underscore, STARTING and ENDING with a
    letter or a digit, and not a Windows device name. So no id can name the runs folder itself or
    anything above it ("." and ".." are refused, TVB-42 audit F1) and no two accepted ids fold
    onto one folder by a trailing dot (Windows drops it); ids that differ only by case are one
    folder on Windows and are treated as one run by the listing (`register`)."""
    return (
        isinstance(s, str)
        and bool(s)
        and s[0].isalnum()
        and s[-1].isalnum()
        and all(ch.isalnum() or ch in "._-" for ch in s)
        and not _reserved(s)
    )


valid_id = _slug
ID_RULE = (
    "id must be letters, digits, dot, dash or underscore, starting and ending with a letter or "
    "digit (not a Windows device name)"
)


def iso(t: int | None) -> str:
    if not _time(t):
        return "?"
    return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def day_of(t: int) -> str:
    return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d")


def size_seconds(size: str) -> int | None:
    """'1d' -> 86400, '4h' -> 14400, '5m' -> 300; None for a size the gap check cannot read."""
    if not isinstance(size, str) or len(size) < 2 or size[-1] not in SIZE_SECONDS:
        return None
    try:
        n = int(size[:-1])
    except ValueError:
        return None
    return n * SIZE_SECONDS[size[-1]] if n > 0 else None


# ----------------------------------------------------------------------------- validation


def validate_run(run: dict) -> list[str]:
    """Run-level problems (the card, the clock, the books). Empty when the run card fits."""
    p: list[str] = []
    if not isinstance(run, dict):
        return ["run: run.json must be an object"]
    if run.get("contract") != CONTRACT:
        p.append(
            f"run: contract version {run.get('contract')!r}; this page reads version {CONTRACT}"
        )
    if not _slug(run.get("id")):
        p.append("run: " + ID_RULE)
    for key in ("name", "as_of"):
        if not isinstance(run.get(key), str) or not run[key]:
            p.append(f"run: {key} missing")
    if isinstance(run.get("as_of"), str):
        try:
            datetime.strptime(run["as_of"], "%Y-%m-%d")
        except ValueError:
            p.append("run: as_of must be a day, YYYY-MM-DD")
    clock = run.get("clock")
    if not isinstance(clock, dict):
        p.append("run: clock missing (day_roll and resolution)")
    else:
        if not isinstance(clock.get("day_roll"), str) or not clock["day_roll"]:
            p.append("run: clock.day_roll missing (for example '00:00 UTC' or '18:00 ET')")
        if clock.get("resolution") not in RESOLUTIONS:
            p.append("run: clock.resolution must be day, hour or minute")
        shift = clock.get("label_shift_hours", 0)
        if not (isinstance(shift, int) and not isinstance(shift, bool) and -23 <= shift <= 23):
            p.append(
                "run: clock.label_shift_hours must be a whole number of hours from -23 to 23 (added to "
                "a bar's open before its calendar date names the session; 6 for the Globex day)"
            )
        if clock.get("calendar", "utc_day") not in CALENDARS:
            p.append(
                "run: clock.calendar must be utc_day (every calendar day is a bar) or session "
                "(sparse: no weekend, holidays)"
            )
    units = run.get("units")
    if not isinstance(units, list) or not units or not all(isinstance(u, str) and u for u in units):
        p.append("run: units must list the setup bar names the cards use (for example D, W, M)")
    bars = run.get("bars", [])
    if not isinstance(bars, list) or not all(isinstance(b, str) and b for b in bars):
        p.append("run: bars must list the candle sizes shipped (for example 1h, 1d)")
    books = run.get("books")
    if not isinstance(books, list) or not books:
        p.append("run: books missing (at least the headline book)")
        return p
    ids: set[str] = set()
    heads = 0
    for n, b in enumerate(books):
        tag = f"run: book #{n + 1}"
        if not isinstance(b, dict):
            p.append(f"{tag} is not an object")
            continue
        bid = b.get("id")
        if not _slug(bid):
            p.append(f"{tag}: {ID_RULE}")
        elif bid in ids:
            p.append(f"{tag}: id {bid!r} is declared twice")
        else:
            ids.add(bid)
        tag = f"run: book {bid!r}"
        for key in ("name", "rule"):
            if not isinstance(b.get(key), str) or not b[key]:
                p.append(f"{tag}: {key} missing (words)")
        if b.get("role") not in ROLES:
            p.append(f"{tag}: role must be one of {', '.join(ROLES)}")
        heads += b.get("role") == "headline"
        if "resolution" in b and b["resolution"] not in RESOLUTIONS:
            p.append(f"{tag}: resolution must be day, hour or minute")
        if "group" in b and (not isinstance(b["group"], str) or not b["group"]):
            p.append(f"{tag}: group must be words")
        if "target" in b and (not isinstance(b["target"], str) or not b["target"]):
            p.append(f"{tag}: target must name the target the book takes (T1, T2, mm, one_r)")
    if heads != 1:
        p.append(f"run: {heads} headline books; there must be exactly one")
    return p


def _check_bars(inst: str, size: str, rows, p: list[str], w: list[str]) -> None:
    if not isinstance(rows, list):
        p.append(f"{inst}: {size} bars must be a list of [t, open, high, low, close, volume]")
        return
    prev = None
    gaps = 0
    step = size_seconds(size)
    for n, r in enumerate(rows):
        if not isinstance(r, list) or len(r) != 6 or not all(_num(x) for x in r):
            p.append(f"{inst}: {size} bar #{n + 1} is not [t, open, high, low, close, volume]")
            return
        t = r[0]
        if prev is not None and t <= prev:
            p.append(f"{inst}: {size} bars are not in time order at #{n + 1} ({iso(int(t))})")
            return
        if prev is not None and step and t - prev != step:
            gaps += 1
        prev = t
    if gaps:
        w.append(f"{inst}: {size} bars have {gaps} gaps")


def validate_file(run: dict, fname: str, doc: dict, seen: set[str]) -> tuple[list[str], list[str]]:
    """One instrument file's problems and warnings; `seen` collects card ids across files."""
    p: list[str] = []
    w: list[str] = []
    if not isinstance(doc, dict):
        return [f"{fname}: must be an object with instrument, bars and trades"], w
    inst = doc.get("instrument")
    if not isinstance(inst, str) or not inst:
        return [f"{fname}: instrument missing"], w
    bars = doc.get("bars", {})
    if not isinstance(bars, dict):
        p.append(f"{inst}: bars must be an object of candle size -> rows")
    else:
        for size, rows in bars.items():
            _check_bars(inst, size, rows, p, w)
        if not any(bars.values()):
            w.append(
                f"{inst}: no bars for this run (the page shows the story and the ladder without a chart)"
            )
    trades = doc.get("trades")
    if not isinstance(trades, list):
        p.append(f"{inst}: trades must be a list of cards")
        return p, w
    book_ids = {b.get("id") for b in run.get("books", []) if isinstance(b, dict)}
    units = run.get("units") if isinstance(run.get("units"), list) else []
    for n, c in enumerate(trades):
        _check_card(book_ids, units, inst, n, c, seen, p)
    return p, w


def _check_card(
    book_ids: set, units: list, inst: str, n: int, c, seen: set[str], p: list[str]
) -> None:
    if not isinstance(c, dict):
        p.append(f"{inst} card #{n + 1}: not an object")
        return
    cid = c.get("id") if isinstance(c.get("id"), str) and c.get("id") else f"#{n + 1}"
    tag = f"{inst} card {cid}"
    if cid in seen:
        p.append(f"{tag}: duplicate card id")
    seen.add(cid)
    if c.get("instrument") != inst:
        p.append(f"{tag}: instrument {c.get('instrument')!r} inside {inst}'s file")
    if units and c.get("bar") not in units:
        p.append(f"{tag}: bar {c.get('bar')!r} is not one of the run's units ({', '.join(units)})")
    if c.get("kind") not in KINDS:
        p.append(f"{tag}: kind must be one of {', '.join(KINDS)}")
    if c.get("direction") not in DIRECTIONS:
        p.append(f"{tag}: direction must be up or down")
    if not isinstance(c.get("pattern"), str) or not c["pattern"]:
        p.append(f"{tag}: pattern missing (words, for example '2-2 reversal')")
    entry = c.get("entry")
    t0 = entry.get("t") if isinstance(entry, dict) else None
    if not isinstance(entry, dict):
        p.append(f"{tag}: entry missing (t and price)")
    else:
        if not _time(t0):
            p.append(f"{tag}: entry.t must be a UTC timestamp in seconds")
        if not _price(entry.get("price")):
            p.append(f"{tag}: entry.price must be a positive number")
    for key in ("far", "one_r"):
        if c.get(key) is not None and not _price(c[key]):
            p.append(f"{tag}: {key} must be a positive number or null")
    if c.get("r_pct") is not None and not (_num(c["r_pct"]) and c["r_pct"] >= 0):
        p.append(f"{tag}: r_pct must be a number at or above zero, or null")
    targets = c.get("targets", [])
    if not isinstance(targets, list):
        p.append(f"{tag}: targets must be a list")
        targets = []
    for m, tg in enumerate(targets):
        if not isinstance(tg, dict) or not isinstance(tg.get("name"), str) or not tg.get("name"):
            p.append(f"{tag}: target #{m + 1} needs a name")
            continue
        if not _price(tg.get("price")):
            p.append(f"{tag}: target {tg['name']} must have a positive price")
        if not isinstance(tg.get("source"), str):
            p.append(f"{tag}: target {tg['name']} needs a source (words)")
        tt = tg.get("touched")
        if tt is not None and not _time(tt):
            p.append(f"{tag}: target {tg['name']} touched must be a timestamp or null")
        elif _time(tt) and _time(t0) and tt < t0:
            p.append(f"{tag}: target {tg['name']} touched {iso(tt)}, before the entry {iso(t0)}")
    touches = c.get("touches", {})
    if not isinstance(touches, dict):
        p.append(f"{tag}: touches must be an object")
        touches = {}
    for key, tt in touches.items():
        if tt is not None and not _time(tt):
            p.append(f"{tag}: touches.{key} must be a timestamp or null")
        elif _time(tt) and _time(t0) and tt < t0:
            p.append(f"{tag}: touches.{key} {iso(tt)} is before the entry {iso(t0)}")
    books = c.get("books")
    if not isinstance(books, list):
        p.append(f"{tag}: books missing (a list, one entry per declared book that applies)")
        return
    seen_b: set = set()
    touched_times = [
        tg["touched"] for tg in targets if isinstance(tg, dict) and _time(tg.get("touched"))
    ]
    for b in books:
        if not isinstance(b, dict):
            p.append(f"{tag}: a book entry is not an object")
            continue
        bid = b.get("id")
        if bid not in book_ids:
            p.append(f"{tag}: book {bid!r} is not declared in the run")
            continue
        if bid in seen_b:
            p.append(f"{tag}: book {bid} appears twice")
        seen_b.add(bid)
        how = b.get("how")
        if how not in HOW:
            p.append(f"{tag}: book {bid} left by {how!r}, not one of {', '.join(HOW)}")
            continue
        at, price, ret = b.get("at"), b.get("price"), b.get("ret")
        if how in HOW_PRICED:
            if not _time(at):
                p.append(f"{tag}: book {bid} left by {how} but has no time")
            if not _price(price):
                p.append(f"{tag}: book {bid} left by {how} but has no price")
            if not _num(ret):
                p.append(f"{tag}: book {bid} left by {how} but has no return")
        elif how == "cap":
            if not _time(at):
                p.append(f"{tag}: book {bid} is marked at the cap but has no cap time")
            if not _num(ret):
                p.append(f"{tag}: book {bid} is marked at the cap but has no return")
            if price is not None and not _price(price):
                p.append(f"{tag}: book {bid} cap price must be a positive number or null")
        elif at is not None or price is not None or ret is not None:
            p.append(f"{tag}: book {bid} left by {how} must carry no time, price or return")
        if b.get("hit") is not None and not isinstance(b["hit"], bool):
            p.append(f"{tag}: book {bid} hit must be true, false or null")
        if "resolution" in b and b["resolution"] not in RESOLUTIONS:
            p.append(f"{tag}: book {bid} resolution must be day, hour or minute")
        if "note" in b and b["note"] is not None and not isinstance(b["note"], str):
            p.append(f"{tag}: book {bid} note must be words")
        if _time(at) and _time(t0) and at < t0:
            p.append(f"{tag}: book {bid} leaves at {iso(at)}, before the entry {iso(t0)}")
        be = b.get("entry")
        if be is not None:
            if not _time(be):
                p.append(f"{tag}: book {bid} entry must be a timestamp or absent")
            elif _time(t0) and be < t0:
                p.append(
                    f"{tag}: book {bid} enters at {iso(be)}, before the card's entry {iso(t0)}"
                )
            elif _time(at) and be > at:
                p.append(f"{tag}: book {bid} enters at {iso(be)}, after it leaves {iso(at)}")
        if how == "target" and _time(at) and not any(tt <= at for tt in touched_times):
            p.append(
                f"{tag}: book {bid} left by target at {iso(at)} but no target is recorded as touched by then"
            )
        if how == "one_r" and _time(at):
            tr = touches.get("one_r")
            if _time(tr) and tr > at:
                p.append(
                    f"{tag}: book {bid} left at one R at {iso(at)}, before one R's first touch {iso(tr)}"
                )
    for key in ("travel", "context", "extras"):
        if c.get(key) is not None and not isinstance(c[key], dict):
            p.append(f"{tag}: {key} must be an object")


def validate(run: dict, files: dict[str, dict]) -> tuple[list[str], list[str]]:
    """Every problem and warning of a run held in memory (tests and small runs)."""
    problems = validate_run(run)
    warnings: list[str] = []
    seen: set[str] = set()
    for fname, doc in files.items():
        p, w = validate_file(run, fname, doc, seen)
        problems += p
        warnings += w
    return problems, warnings


# ----------------------------------------------------------------------------- derived files


def headline_id(run: dict) -> str | None:
    for b in run.get("books", []):
        if isinstance(b, dict) and b.get("role") == "headline":
            return b.get("id")
    return None


def ladder_books(run: dict) -> list[str]:
    """The books Compare lines up: ladder roles, not grouped variants (the other clocks stay on
    the cards)."""
    return [
        b["id"]
        for b in run.get("books", [])
        if isinstance(b, dict) and b.get("role") in LADDER_ROLES and not b.get("group")
    ]


class Derive:
    """Accumulates index, dates and the universe table file by file (a run can be large)."""

    def __init__(self, run: dict):
        self.run = run
        self.head = headline_id(run)
        self.books = ladder_books(run)
        self.instruments: list[dict] = []
        self.dates: dict[str, list] = defaultdict(list)
        self.cols: dict[str, list] = defaultdict(list)
        self.classes: list[str] = []
        self.extras: dict[str, dict] = {}  # key -> {"kind": "flag"|"code", "codes": [...]}
        self.n = 0
        clock = run.get("clock") if isinstance(run.get("clock"), dict) else {}
        # the label shift (CONTRACT.md section 4): the universe's date column and the dates file
        # carry the SESSION'S label, the same date the page prints for the card
        self.shift = int(clock.get("label_shift_hours") or 0) * 3_600

    def add(self, fname: str, doc: dict) -> None:
        inst = doc["instrument"]
        bars = doc.get("bars") or {}
        daily = bars.get("1d") or []
        opens = [int(b[0]) for b in daily]

        def session(ts) -> int | None:
            # the bar whose open is the latest at or before ts (the page's sessionOf), None without bars
            if ts is None or not opens or ts < opens[0]:
                return None
            return bisect_right(opens, ts) - 1

        ci = len(self.instruments)
        self.instruments.append(
            {
                "instrument": inst,
                "file": fname,
                "n": len(doc.get("trades", [])),
                "first": int(daily[0][0]) if daily else None,
                "last": int(daily[-1][0]) if daily else None,
                "bars": [s for s, rows in bars.items() if rows],
            }
        )
        units = self.run.get("units", [])
        for c in doc.get("trades", []):
            t0 = c["entry"]["t"]
            s0 = session(t0)
            label_t = (opens[s0] if s0 is not None else t0) + self.shift
            by_id = {b["id"]: b for b in c["books"]}
            head = by_id.get(self.head, {})
            self.dates[day_of(label_t)].append(
                [inst, c["direction"], c["bar"], c["kind"], head.get("ret"), head.get("how")]
            )
            cols = self.cols
            cols["instrument"].append(ci)
            cols["date"].append((label_t - int(UNI_EPOCH.timestamp())) // DAY)
            cols["bar"].append(units.index(c["bar"]) if c["bar"] in units else -1)
            cols["kind"].append(KINDS.index(c["kind"]))
            cols["dir"].append(DIRECTIONS.index(c["direction"]))
            cls = c.get("class")
            if cls is not None and cls not in self.classes:
                self.classes.append(cls)
            cols["class"].append(-1 if cls is None else self.classes.index(cls))
            cols["t1"].append(
                1 if any(tg.get("name") == "T1" for tg in c.get("targets", [])) else 0
            )
            for bid in self.books:
                b = by_id.get(bid)
                r = None if b is None else b.get("ret")
                cols[bid + ":ret"].append(None if r is None else round(r, 3))
                cols[bid + ":how"].append(-1 if b is None else HOW.index(b["how"]))
                at = None if b is None else b.get("at")
                # the offset in BARS from the entry's bar to the bar holding the exit (the page's k);
                # calendar days only when the file ships no daily bars
                sj = session(at)
                if at is None:
                    k = -1
                elif sj is not None and s0 is not None:
                    k = sj - s0
                else:
                    k = (at - t0) // DAY
                cols[bid + ":days"].append(k)
                hit = None if b is None else b.get("hit")
                cols[bid + ":hit"].append(-1 if hit is None else int(hit))
            self._extras(c.get("extras") or {})
            self.n += 1

    def _extras(self, ex: dict) -> None:
        # flags and short categorical strings become columns; the rest stays on the cards
        for key, v in ex.items():
            spec = self.extras.get(key)
            col = "x:" + key
            if spec is None:
                if isinstance(v, bool) or v is None:
                    spec = {"kind": "flag"}
                elif isinstance(v, str):
                    spec = {"kind": "code", "codes": []}
                else:
                    spec = {"kind": "skip"}
                self.extras[key] = spec
                if spec["kind"] != "skip":
                    # a key first seen on this card was absent on every card before it: the
                    # column starts with that many "absent" marks, so values stay on their own
                    # rows (TVB-42 audit F4)
                    self.cols[col] = [-1] * self.n
            if spec["kind"] == "flag":
                if v is None or isinstance(v, bool):
                    self.cols[col].append(-1 if v is None else int(v))
                else:
                    spec["kind"] = "skip"
            elif spec["kind"] == "code":
                if isinstance(v, str):
                    if v not in spec["codes"]:
                        if len(spec["codes"]) >= UNI_MAX_CODES:
                            spec["kind"] = "skip"
                            continue
                        spec["codes"].append(v)
                    self.cols[col].append(spec["codes"].index(v))
                elif v is None:
                    self.cols[col].append(-1)
                else:
                    spec["kind"] = "skip"
        for key, spec in self.extras.items():
            col = "x:" + key
            if spec["kind"] == "skip":
                self.cols.pop(col, None)
            elif len(self.cols[col]) < self.n + 1:
                self.cols[col].append(-1)  # the key is absent on this card

    def index(self, built: str) -> dict:
        return {
            "id": self.run["id"],
            "as_of": self.run["as_of"],
            "built": built,
            "instruments": self.instruments,
            "trades": sum(i["n"] for i in self.instruments),
        }

    def universe(self) -> dict:
        codes = {
            "bar": list(self.run.get("units", [])),
            "kind": list(KINDS),
            "dir": list(DIRECTIONS),
            "how": list(HOW),
            "class": self.classes,
        }
        for key, spec in self.extras.items():
            if spec["kind"] == "code":
                codes["x:" + key] = spec["codes"]
        return {
            "epoch": UNI_EPOCH.strftime("%Y-%m-%d"),
            "instruments": [i["instrument"] for i in self.instruments],
            "books": self.books,
            "codes": codes,
            "n": self.n,
            "cols": {k: v for k, v in self.cols.items() if len(v) == self.n},
        }


# ----------------------------------------------------------------------------- sources


def _fname(instrument: str) -> str:
    """The file an instrument's cards live under: every character that is not a letter, digit,
    dot, dash or underscore becomes an underscore (a colon, a slash, a backslash, a space), so
    the name is a plain file name inside the run folder and never a path; leading and trailing
    dots go; a name the importer reserves gets a suffix (TVB-42 audit F1)."""
    stem = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in instrument).strip(".")
    stem = stem or "instrument"
    if _reserved(stem):
        stem = "_" + stem  # NUL.json would be the Windows device, not a file
    name = stem + ".json"
    if _reserved_file(name):
        name = stem + "_instrument.json"
    return name


def _reserved_file(fname: str) -> bool:
    """run.json and the derived files, compared without case (Windows folds RUN.json onto run.json)."""
    return fname.casefold() in {n.casefold() for n in ("run.json", *DERIVED)}


def _plain_name(fname: str) -> bool:
    """A file name the importer will write: a single path component ending in .json, not a
    reserved file and not a Windows device name."""
    return (
        isinstance(fname, str)
        and fname.endswith(".json")
        and fname not in (".json", "..json")
        and "/" not in fname
        and "\\" not in fname
        and fname.strip(".") != ""
        and Path(fname).name == fname
        and not _reserved(fname)
        and not _reserved_file(fname)
    )


def _split_single(doc: dict) -> tuple[dict, dict[str, dict]]:
    """A single-file run: `instruments` entries carry their bars and trades inline. Two
    instruments whose names map to one file are refused (the second would overwrite the first)."""
    files: dict[str, dict] = {}
    owner: dict[str, str] = {}
    for item in doc.get("instruments", []):
        if not isinstance(item, dict) or not isinstance(item.get("instrument"), str):
            raise ContractError(["run: every inline instrument needs an instrument name"])
        name = _fname(item["instrument"])
        key = name.casefold()  # BTC.json and btc.json are one file on Windows
        if key in owner:
            raise ContractError(
                [
                    f"run: instruments {owner[key]!r} and {item['instrument']!r} would share the file {name}"
                ]
            )
        owner[key] = item["instrument"]
        files[name] = {
            "instrument": item["instrument"],
            "bars": item.get("bars") or {},
            "trades": item.get("trades") or [],
        }
    run = {k: v for k, v in doc.items() if k != "instruments"}
    return run, files


def _is_inline(doc: dict) -> bool:
    items = doc.get("instruments")
    return (
        bool(items)
        and isinstance(items, list)
        and isinstance(items[0], dict)
        and "trades" in items[0]
    )


def load_source(path: Path | str) -> tuple[dict, Callable[[], Iterator[tuple[str, dict]]]]:
    """A run's card and a factory of (file name, instrument doc) iterators. A folder streams its
    files one at a time; a single file or a zip is read into memory."""
    path = Path(path)
    if path.is_dir():
        run_path = path / "run.json"
        if not run_path.exists():
            raise ContractError([f"{path}: no run.json in the folder"])
        run = json.loads(run_path.read_text(encoding="utf-8"))
        names = sorted(
            p.name for p in path.glob("*.json") if p.name != "run.json" and p.name not in DERIVED
        )
        if isinstance(run, dict) and _is_inline(run):
            # the single-file flavour sitting in a folder (or a zip): split it like a direct
            # file; a folder that mixes the two flavours is refused (TVB-42 audit F3)
            if names:
                raise ContractError(
                    [
                        f"{path}: run.json carries its instruments inline and the folder also holds "
                        f"instrument files ({', '.join(names[:3])}); use one flavour"
                    ]
                )
            run, files = _split_single(run)
            return run, lambda: iter(files.items())

        def folder() -> Iterator[tuple[str, dict]]:
            for name in names:
                yield name, json.loads((path / name).read_text(encoding="utf-8"))

        return run, folder
    if path.suffix.lower() == ".zip":
        with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(path) as z:
            z.extractall(tmp)
            hits = list(Path(tmp).rglob("run.json"))
            if len(hits) != 1:
                raise ContractError(
                    [f"{path}: a zip must hold exactly one run.json ({len(hits)} found)"]
                )
            run, factory = load_source(hits[0].parent)
            files = dict(factory())  # read before the temp folder goes away
        return run, lambda: iter(files.items())
    if path.suffix.lower() == ".json":
        doc = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(doc, dict) and _is_inline(doc):
            run, files = _split_single(doc)
            return run, lambda: iter(files.items())
        if path.name == "run.json":
            return load_source(path.parent)
        return doc, lambda: iter(())
    raise ContractError([f"{path}: not a folder, a .json file or a .zip"])


# ----------------------------------------------------------------------------- import


def _write(path: Path, doc) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, separators=(",", ":"))


def register(root: Path, entry: dict) -> list[dict]:
    """Add or replace a run in `runs.json`; newest built first. Ids that differ only by case
    are one folder on Windows, so they are one listing too (the newer id's words win)."""
    listing = root / "runs.json"
    runs = json.loads(listing.read_text(encoding="utf-8")) if listing.exists() else []
    key = str(entry["id"]).casefold()
    runs = [r for r in runs if str(r.get("id")).casefold() != key] + [entry]
    runs.sort(key=lambda r: r.get("built", ""), reverse=True)
    _write(listing, runs)
    return runs


def _inside(path: Path, folder: Path) -> bool:
    """True when `path` resolves to a child of `folder` (never the folder itself)."""
    try:
        rel = path.resolve().relative_to(folder.resolve())
    except ValueError:
        return False
    return str(rel) not in ("", ".")


def _source_dir(path: Path) -> Path | None:
    """The folder a source reads its instrument files from: the folder itself, or the parent of
    a folder-style `run.json`; None for a zip or an inline single file (read whole, up front)."""
    if path.is_dir():
        return path
    if path.suffix.lower() == ".json" and path.name == "run.json" and path.exists():
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return None if isinstance(doc, dict) and _is_inline(doc) else path.parent
    return None


def _stamp(built: str) -> str:
    return built.replace(":", "").replace("-", "")  # no dash: the id before it may hold dashes


def recover(runs_dir: Path, log: Callable[[str], None] = print) -> None:
    """Repair what an interrupted import left behind. A staging folder (`.import-*`) is never the
    only copy of anything and goes. A stepped-aside run (`.old-<id>-<stamp>`) is the ONLY copy
    when the import died between its two renames: if `runs/<id>` is missing, the old run is put
    back under its name; if `runs/<id>` exists, the swap had completed and the old copy goes."""
    for p in runs_dir.glob(".import-*"):
        shutil.rmtree(p, ignore_errors=True)
    for p in runs_dir.glob(".old-*"):
        rid = p.name[len(".old-") :].rsplit("-", 1)[0]
        dest = runs_dir / rid
        if rid and not dest.exists():
            p.rename(dest)
            log(f"run {rid}: restored from an interrupted import")
        else:
            shutil.rmtree(p, ignore_errors=True)


def import_run(
    source: Path | str,
    root: Path,
    run_id: str | None = None,
    bars_lookup: Callable[[str], dict | None] | None = None,
    log: Callable[[str], None] = print,
) -> str:
    """Validate a run and lay it out under `root/runs/<id>/` with its derived files; refuse it
    with every problem named. `bars_lookup(instrument)` may supply bars for a file that ships
    none.

    The run is built in a staging folder beside the runs and swapped in only after every card
    has passed, so a refused replacement never disturbs the run it would have replaced, and the
    listing names only runs whose files exist (TVB-42 audit F2). The source may be the
    destination folder itself, or its `run.json` (an export in place): its files are read
    before the swap. Problems stop after the instrument file that takes the count past 200."""
    source = Path(source)
    run, factory = load_source(source)
    if run_id:
        run["id"] = run_id
    problems = validate_run(run)
    if problems:
        raise ContractError(problems)
    runs_dir = root / "runs"
    dest = runs_dir / run["id"]
    if not _inside(dest, runs_dir):  # _slug already refuses "." and ".."; belt and braces
        raise ContractError([f"run: id {run['id']!r} does not name a folder inside {runs_dir}"])
    runs_dir.mkdir(parents=True, exist_ok=True)
    recover(runs_dir, log)
    stage: Path | None = Path(tempfile.mkdtemp(prefix=".import-", dir=runs_dir))
    try:
        built = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        derive = Derive(run)
        seen: set[str] = set()
        warnings: list[str] = []
        for fname, doc in factory():
            if not _plain_name(fname) or not _inside(stage / fname, stage):
                problems.append(f"{fname}: not a plain file name inside the run folder")
                continue
            if bars_lookup and isinstance(doc, dict) and not any((doc.get("bars") or {}).values()):
                found = bars_lookup(doc.get("instrument", ""))
                if found:
                    doc["bars"] = found
                    log(f"{doc.get('instrument')}: bars filled from the cache")
            p, w = validate_file(run, fname, doc, seen)
            warnings += w
            if p:
                problems += p
                if len(problems) > 200:
                    break
                continue
            derive.add(fname, doc)
            _write(stage / fname, doc)
        if problems:
            raise ContractError(problems)
        for w in warnings:
            log("warning: " + w)
        index = derive.index(built)
        run["built"] = built
        run["instruments"] = index["instruments"]
        _write(stage / "run.json", run)
        _write(stage / "index.json", index)
        _write(stage / "dates.json", dict(derive.dates))
        _write(stage / "universe.json", derive.universe())
        # the swap: the old run (if any) steps aside, the staged one takes its name, the old one
        # goes. If the second rename fails the old run is put straight back; if the process dies
        # between the two, the next import's `recover` puts it back.
        old: Path | None = None
        if dest.exists():
            old = runs_dir / (".old-" + run["id"] + "-" + _stamp(built))
            dest.rename(old)
        try:
            stage.rename(dest)
        except OSError:
            if old is not None and not dest.exists():
                old.rename(dest)
            raise
        stage = None
        if old is not None:
            shutil.rmtree(old, ignore_errors=True)
    finally:
        if stage is not None:
            shutil.rmtree(stage, ignore_errors=True)
    register(
        root,
        {
            "id": run["id"],
            "name": run["name"],
            "as_of": run["as_of"],
            "built": built,
            "trades": index["trades"],
            "instruments": len(index["instruments"]),
            "dir": "runs/" + run["id"],
        },
    )
    log(
        f"run {run['id']}: {len(index['instruments'])} instruments, {index['trades']:,} trades, "
        f"{len(warnings)} warnings -> {dest}"
    )
    return run["id"]


def check(source: Path | str, log: Callable[[str], None] = print) -> tuple[list[str], list[str]]:
    """Validate without importing; returns (problems, warnings) and logs them."""
    run, factory = load_source(source)
    problems = validate_run(run)
    warnings: list[str] = []
    seen: set[str] = set()
    n_files = n_cards = 0
    if not problems:
        for fname, doc in factory():
            p, w = validate_file(run, fname, doc, seen)
            problems += p
            warnings += w
            n_files += 1
            n_cards += len(doc.get("trades", [])) if isinstance(doc, dict) else 0
    for w in warnings:
        log("warning: " + w)
    for p in problems:
        log("problem: " + p)
    log(
        f"{'FITS' if not problems else 'DOES NOT FIT'}: {n_files} instrument files, {n_cards:,} cards, "
        f"{len(problems)} problems, {len(warnings)} warnings"
    )
    return problems, warnings


def iter_files(root: Path, run_id: str) -> Iterable[tuple[str, dict]]:
    """The instrument files of an imported run, in index order."""
    dest = root / "runs" / run_id
    index = json.loads((dest / "index.json").read_text(encoding="utf-8"))
    for item in index["instruments"]:
        yield item["file"], json.loads((dest / item["file"]).read_text(encoding="utf-8"))
