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


def _slug(s) -> bool:
    return isinstance(s, str) and bool(s) and all(ch.isalnum() or ch in "._-" for ch in s)


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
        p.append("run: id must be letters, digits, dot, dash or underscore")
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
            p.append(f"{tag}: id must be letters, digits, dot, dash or underscore")
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
        if "note" in b and b["note"] is not None and not isinstance(b["note"], str):
            p.append(f"{tag}: book {bid} note must be words")
        if _time(at) and _time(t0) and at < t0:
            p.append(f"{tag}: book {bid} leaves at {iso(at)}, before the entry {iso(t0)}")
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

    def add(self, fname: str, doc: dict) -> None:
        inst = doc["instrument"]
        bars = doc.get("bars") or {}
        daily = bars.get("1d") or []
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
            by_id = {b["id"]: b for b in c["books"]}
            head = by_id.get(self.head, {})
            self.dates[day_of(t0)].append(
                [inst, c["direction"], c["bar"], c["kind"], head.get("ret"), head.get("how")]
            )
            cols = self.cols
            cols["instrument"].append(ci)
            cols["date"].append((t0 - int(UNI_EPOCH.timestamp())) // DAY)
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
                cols[bid + ":days"].append(-1 if at is None else (at - t0) // DAY)
                hit = None if b is None else b.get("hit")
                cols[bid + ":hit"].append(-1 if hit is None else int(hit))
            self._extras(c.get("extras") or {})
            self.n += 1

    def _extras(self, ex: dict) -> None:
        # flags and short categorical strings become columns; the rest stays on the cards
        for key, v in ex.items():
            spec = self.extras.get(key)
            if spec is None:
                if isinstance(v, bool) or v is None:
                    spec = {"kind": "flag"}
                elif isinstance(v, str):
                    spec = {"kind": "code", "codes": []}
                else:
                    spec = {"kind": "skip"}
                self.extras[key] = spec
            col = "x:" + key
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
    return instrument.replace(":", "_").replace("/", "_") + ".json"


def _split_single(doc: dict) -> tuple[dict, dict[str, dict]]:
    """A single-file run: `instruments` entries carry their bars and trades inline."""
    files: dict[str, dict] = {}
    for item in doc.get("instruments", []):
        files[_fname(item["instrument"])] = {
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
    """Add or replace a run in `runs.json`; newest built first."""
    listing = root / "runs.json"
    runs = json.loads(listing.read_text(encoding="utf-8")) if listing.exists() else []
    runs = [r for r in runs if r.get("id") != entry["id"]] + [entry]
    runs.sort(key=lambda r: r.get("built", ""), reverse=True)
    _write(listing, runs)
    return runs


def import_run(
    source: Path | str,
    root: Path,
    run_id: str | None = None,
    bars_lookup: Callable[[str], dict | None] | None = None,
    log: Callable[[str], None] = print,
) -> str:
    """Validate a run and lay it out under `root/runs/<id>/` with its derived files; refuse it
    with every problem named. `bars_lookup(instrument)` may supply bars for a file that ships
    none. The source may already be the destination folder (an export in place)."""
    run, factory = load_source(source)
    if run_id:
        run["id"] = run_id
    problems = validate_run(run)
    if problems:
        raise ContractError(problems)
    dest = root / "runs" / run["id"]
    in_place = Path(source).resolve() == dest.resolve() if Path(source).exists() else False
    if dest.exists() and not in_place:
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    built = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    derive = Derive(run)
    seen: set[str] = set()
    warnings: list[str] = []
    written: list[str] = []
    for fname, doc in factory():
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
        _write(dest / fname, doc)
        written.append(fname)
    if problems:
        if not in_place:
            shutil.rmtree(dest, ignore_errors=True)
        raise ContractError(problems)
    for w in warnings:
        log("warning: " + w)
    index = derive.index(built)
    run["built"] = built
    run["instruments"] = index["instruments"]
    _write(dest / "run.json", run)
    _write(dest / "index.json", index)
    _write(dest / "dates.json", dict(derive.dates))
    _write(dest / "universe.json", derive.universe())
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
