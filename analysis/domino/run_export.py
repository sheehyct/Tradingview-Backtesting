"""The management book (`results/manage_trades.csv.gz`) exported as a run in the viewer's
contract (`viewer/CONTRACT.md`, section 9 is this file's mapping), and the row-for-row check of
that run against the flat viewer data.

Every time on a card is the open of the engine's own bar: the engine's day offsets are INDEX
offsets in the normalised daily list (the census never fills a gap), so `at` is read from the
cached bars by index, never by date arithmetic. Prices for clock exits and cap marks are
recovered from the recorded return, which is how the engine defined them
(`ret = sign * (close - level) / level * 100`).
"""

from __future__ import annotations

import csv
import gzip
import json
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from analysis.domino import contract as K
from analysis.domino.census import cached_universe, normalize, normalize_hourly
from analysis.domino.trade_viewer import DATA, TRADES, cache_path, compact, stamp_of

DAY = 86_400
HOUR = 3_600
UNITS = ("D", "W", "M")

# the books the engine scored, in the ladder's order; the clock variants carry a group so the
# page can fold them (CONTRACT.md section 2)
BOOKS: list[dict] = [
    {
        "id": "C",
        "name": "exit only",
        "role": "headline",
        "rule": "No target. Hold until a daily close goes against the trade with the week against it at that close; 20-day cap.",
    },
    {
        "id": "A",
        "name": "all out at T1",
        "role": "target",
        "rule": "Everything out at T1, the pattern's own magnitude or the first unbroken weekly / monthly level. Otherwise the exit.",
    },
    {
        "id": "B",
        "name": "hold through T2",
        "role": "target",
        "rule": "Hold through T2 with the exit live. T1 is not a decision.",
    },
    {
        "id": "D",
        "name": "one R or the exit",
        "role": "target",
        "rule": "One R or the exit, whichever comes first, inside the 20-day cap.",
    },
    {
        "id": "D5",
        "name": "one R or the exit, 5 bars",
        "role": "target",
        "rule": "One R or the exit inside five bars of the unit, the chance book's own horizon.",
    },
    {
        "id": "ref",
        "name": "chance book",
        "role": "reference",
        "rule": "One R or the setup-bar stop, whichever comes first (the stop first on a shared day), marked at bar five.",
    },
    {
        "id": "C_h",
        "name": "hourly clock",
        "role": "clock",
        "resolution": "hour",
        "group": "hourly clock",
        "rule": "Exit only on the hourly clock: the entry is the same level at the first hour strictly through it; out at the first hour closing against its own open with the day also against, inside the 20-day cap. Scored only inside the venue's hourly window.",
    },
    {
        "id": "A_h",
        "name": "all out at T1, hourly clock",
        "role": "clock",
        "resolution": "hour",
        "group": "hourly clock",
        "rule": "T1 when touched at or before the hourly exit, else the exit hour's close.",
    },
    {
        "id": "D_h",
        "name": "one R, hourly clock",
        "role": "clock",
        "resolution": "hour",
        "group": "hourly clock",
        "rule": "One R when touched at or before the hourly exit, else the exit hour's close.",
    },
    {
        "id": "C_u",
        "name": "under water",
        "role": "clock",
        "group": "under water",
        "rule": "Exit only, reading against as under water: a daily close through the entry price with the week against it at that close; 20-day cap.",
    },
    {
        "id": "A_u",
        "name": "all out at T1, under water",
        "role": "clock",
        "group": "under water",
        "rule": "T1 when touched at or before the under-water exit, else that exit.",
    },
    {
        "id": "D_u",
        "name": "one R, under water",
        "role": "clock",
        "group": "under water",
        "rule": "One R when touched at or before the under-water exit, else that exit.",
    },
    {
        "id": "C_own",
        "name": "own clock",
        "role": "clock",
        "group": "own clock",
        "rule": "Weekly and monthly units only: a weekly close against the week's open with the month also against it (weekly), or a monthly close against the month's open (monthly); cap 20 bars of the unit.",
    },
    {
        "id": "A_own",
        "name": "all out at T1, own clock",
        "role": "clock",
        "group": "own clock",
        "rule": "T1 when touched at or before the own-clock exit, else that exit.",
    },
    {
        "id": "C_long",
        "name": "daily clock, long cap",
        "role": "clock",
        "group": "long cap",
        "rule": "Weekly and monthly units only: the daily clock run to a cap of 20 bars of the unit.",
    },
    {
        "id": "A_long",
        "name": "all out at T1, long cap",
        "role": "clock",
        "group": "long cap",
        "rule": "T1 when touched at or before the long-cap exit, else that exit.",
    },
    {
        "id": "A_mm",
        "name": "all out at the measured move",
        "role": "target",
        "group": "measured move",
        "rule": "Everything out at the measured move (the two-bar range projected from the entry), else the exit.",
    },
]
NOT_EXPORTED = ("B_mm: the row holds neither the second measured-move price nor its touch day",)
RULES = {
    "setup": "2-2 reversal, 2-2 continuation, inside-bar break and outside-bar break on the daily, weekly and monthly bar (the domino census)",
    "entry": "the instant the setup bar's high (low) breaks, strictly; weekly and monthly units on the day their level breaks",
    "stop": "none for the management books; the setup bar's far side for the chance book (and the one-R yardstick for every book)",
    "targets": "T1 the pattern's own magnitude or the first unbroken weekly / monthly level beyond the entry, T2 / T3 the next unbroken levels, fixed at entry; the measured move beside them",
    "exit": "a daily close against the trade with the week also against it at that close; 20-day cap (other clocks as grouped books)",
    "continuity": "none gated; the week's and month's side at entry are recorded on the card",
}
EXTRAS = (
    "liquid",
    "flag",
    "anchor",
    "ladder_len",
    "near_tf",
    "gap_pct",
    "reached1",
    "reached2",
    "reached3",
    "later1",
    "later_r",
    "later_r5",
    "stop_saw",
    "stop0",
    "mfe5",
    "mae5",
)
KIND_WORDS = {
    "reversal": "2-2 reversal",
    "continuation": "2-2 continuation",
    "inside": "inside-bar break",
    "outside": "outside-bar break (3-2)",
}
STATUS_HOW = {"exit": "clock", "open": "cap", "censored": "censored"}
H_NOTE = {
    None: "outside the venue's hourly window",
    "no_entry_hour": "the entry day is fully observed and no hour traded through the level",
    "partial_entry_day": "the entry day's hours are not observed from 00:00 through the entry hour",
}


# ----------------------------------------------------------------------------- rows


def _val(v: str):
    if v in ("", "nan", "None"):
        return None
    if v == "True":
        return True
    if v == "False":
        return False
    try:
        f = float(v)
    except ValueError:
        return v
    return None if f != f else f


def load_rows(path: Path = TRADES) -> dict[str, list[dict]]:
    """Every column of the management book's rows, typed, grouped by coin."""
    by_coin: dict[str, list[dict]] = defaultdict(list)
    with gzip.open(path, "rt", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            row = {k: _val(v) for k, v in r.items()}
            row["date"] = r["date"]
            by_coin[r["coin"]].append(row)
    for rows in by_coin.values():
        rows.sort(key=lambda x: (x["date"], x["tf"], x["direction"]))
    return by_coin


def day_ts(date: str) -> int:
    return int(datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def price_from_ret(level: float, ret: float, direction: str) -> float:
    sign = 1.0 if direction == "up" else -1.0
    return level * (1.0 + sign * ret / 100.0)


def one_r_price(level: float, stop: float | None) -> float | None:
    return None if stop is None else 2.0 * level - stop  # level +/- |level - stop|, both ways


# ----------------------------------------------------------------------------- the card


class Tape:
    """One coin's normalised bars, as the engine indexed them."""

    def __init__(self, daily: list[list[float]], hourly: list[list[float]]):
        self.daily = daily
        self.day_idx = {int(b[0]): i for i, b in enumerate(daily)}
        self.hour_close = {int(b[0]): b[4] for b in hourly}

    def at(self, t0: int, k) -> int:
        """The open time of the bar k index steps after the entry day; arithmetic past the end."""
        i = self.day_idx.get(t0)
        if k is None:
            return None  # type: ignore[return-value]
        j = None if i is None else i + int(k)
        if j is not None and 0 <= j < len(self.daily):
            return int(self.daily[j][0])
        return t0 + int(k) * DAY


def _book(bid: str, how: str, at=None, price=None, ret=None, hit=None, note=None) -> dict:
    b = {"id": bid, "how": how, "at": at, "price": price, "ret": ret, "hit": hit}
    if note:
        b["note"] = note
    return b


def _clock_like(
    bid, status, exit_k, days, ret, level, direction, tape, t0, hit=None, note=None
) -> dict:
    """A book that rides a close-exit clock: clock at the exit day, cap at the mark day, censored."""
    if status == "exit":
        return _book(
            bid, "clock", tape.at(t0, exit_k), price_from_ret(level, ret, direction), ret, hit, note
        )
    if status == "open":
        return _book(
            bid, "cap", tape.at(t0, days), price_from_ret(level, ret, direction), ret, hit, note
        )
    return _book(bid, "censored", note=note)


def _target_like(bid, base: dict, hit, price, touch_k, ret, tape, t0, note=None) -> dict:
    """A target book: its own fill when hit, else the base clock's exit with its own return."""
    if base["how"] == "censored":
        return _book(bid, "censored", note=note)
    if base["how"] == "none":
        return _book(bid, "none", note=base.get("note"))
    if hit:
        return _book(bid, "target", tape.at(t0, touch_k), price, ret, True, note)
    return _book(
        bid, base["how"], base["at"], base["price"], ret, None if price is None else False, note
    )


def card_from_row(r: dict, coin: str, dex: str, tape: Tape) -> dict:
    t0 = day_ts(r["date"])
    level, stop, direction = r["level"], r.get("stop"), r["direction"]
    one_r = one_r_price(level, stop)
    kind, tf = r["kind"], r["tf"]
    extra: dict = {}
    note_r = None
    if one_r is not None and one_r <= 0:
        # a short whose setup range exceeds the price: the engine's one R lies at or below zero
        # and can never fill; the card carries no one-R price and says so (339 rows, all shorts)
        extra["one_r_raw"] = one_r
        one_r = None
        note_r = "one R lies at or below zero for this short (the setup range exceeds the price): no one-R fill is possible"
    mm_ok = r.get("mm_t1") is not None and r["mm_t1"] > 0
    if r.get("mm_t1") is not None and not mm_ok:
        extra["mm_raw"] = r[
            "mm_t1"
        ]  # the same for the measured move (964 rows): no target, no A_mm book
    targets = []
    for name, pk, sk, kk in (
        ("T1", "t1", "t1_src", "t1_k"),
        ("T2", "t2", "t2_src", "t2_k"),
        ("T3", "t3", "t3_src", "t3_k"),
    ):
        if r.get(pk) is not None:
            targets.append(
                {
                    "name": name,
                    "price": r[pk],
                    "source": r.get(sk) or "",
                    "touched": tape.at(t0, r.get(kk)),
                }
            )
    if mm_ok:
        targets.append(
            {
                "name": "mm",
                "price": r["mm_t1"],
                "source": "measured move",
                "touched": tape.at(t0, r.get("mm1_k")),
            }
        )
    status = r.get("status")
    books: list[dict] = []
    C = _clock_like(
        "C", status, r.get("exit_k"), r.get("days"), r.get("ret_C"), level, direction, tape, t0
    )
    books.append(C)
    books.append(
        _target_like("A", C, r.get("hit_A"), r.get("t1"), r.get("t1_k"), r.get("ret_A"), tape, t0)
    )
    books.append(
        _target_like("B", C, r.get("hit_B"), r.get("t2"), r.get("t2_k"), r.get("ret_B"), tape, t0)
    )
    one_r_hit = _book("D", "one_r", tape.at(t0, r.get("one_r_k")), one_r, r.get("ret_D"), True)
    books.append(
        one_r_hit
        if r.get("hit_D") and C["how"] != "censored"
        else _target_like("D", C, False, one_r, None, r.get("ret_D"), tape, t0, note=note_r)
    )
    # D5: its own horizon (status5), the one-R fill when hit
    s5 = r.get("status5")
    if s5 is None:
        books.append(_book("D5", "none", note="not scored: the headline row is censored"))
    elif r.get("hit_D5"):
        books.append(
            _book("D5", "one_r", tape.at(t0, r.get("one_r_k")), one_r, r.get("ret_D5"), True)
        )
    else:
        books.append(
            _clock_like(
                "D5",
                s5,
                r.get("days_D5"),
                r.get("days_D5"),
                r.get("ret_D5"),
                level,
                direction,
                tape,
                t0,
                hit=False if one_r is not None else None,
            )
        )
    # the chance book: the engine's out5 and its own fill day
    out5, dref = r.get("out5"), r.get("days_ref")
    if out5 == "stop":
        books.append(_book("ref", "stop", tape.at(t0, dref), stop, r.get("ret5"), False))
    elif out5 == "one_r":
        books.append(_book("ref", "one_r", tape.at(t0, dref), one_r, r.get("ret5"), True))
    elif out5 == "neither":
        books.append(
            _book(
                "ref",
                "cap",
                tape.at(t0, dref),
                price_from_ret(level, r["ret5"], direction) if r.get("ret5") is not None else None,
                r.get("ret5"),
                False,
            )
        )
    else:
        books.append(_book("ref", "censored"))
    # the hourly clock (resolution hour): the entry hour and the hours held are timestamp steps
    sh = r.get("status_h")
    if sh in H_NOTE:
        base_h = _book("C_h", "none", note=H_NOTE[sh])
    elif sh == "censored":
        base_h = _book("C_h", "censored")
    else:
        entry_ts = t0 + int(r["entry_h"]) * HOUR
        held = int(r["exit_h"] if sh == "exit" else r["hours_h"])
        at_h = entry_ts + held * HOUR
        base_h = _book(
            "C_h",
            "clock" if sh == "exit" else "cap",
            at_h,
            price_from_ret(level, r["ret_C_h"], direction),
            r.get("ret_C_h"),
        )
    books.append(base_h)
    if base_h["how"] in ("clock", "cap"):
        entry_ts = t0 + int(r["entry_h"]) * HOUR
        if r.get("hit_A_h"):
            books.append(
                _book(
                    "A_h",
                    "target",
                    entry_ts + int(r["t1_h"]) * HOUR,
                    r["t1"],
                    r.get("ret_A_h"),
                    True,
                )
            )
        else:
            books.append(
                _book(
                    "A_h",
                    base_h["how"],
                    base_h["at"],
                    base_h["price"],
                    r.get("ret_A_h"),
                    None if r.get("t1") is None else False,
                )
            )
        if r.get("hit_D_h"):
            books.append(
                _book(
                    "D_h",
                    "one_r",
                    tape.at(t0, r.get("one_r_k")),
                    one_r,
                    r.get("ret_D_h"),
                    True,
                    note="the touch hour is not in the row; the day is (day resolution)",
                )
            )
        else:
            books.append(
                _book(
                    "D_h",
                    base_h["how"],
                    base_h["at"],
                    base_h["price"],
                    r.get("ret_D_h"),
                    None if one_r is None else False,
                )
            )
    else:
        books.append(_book("A_h", base_h["how"], note=base_h.get("note")))
        books.append(_book("D_h", base_h["how"], note=base_h.get("note")))
    # under water (amendment A2.5), the same cap
    su = r.get("status_u")
    if su is None:
        base_u = _book("C_u", "none", note="not scored: the headline row is censored")
    else:
        base_u = _clock_like(
            "C_u",
            su,
            r.get("exit_k_u"),
            r.get("days_u"),
            r.get("ret_C_u"),
            level,
            direction,
            tape,
            t0,
        )
    books.append(base_u)
    books.append(
        _target_like(
            "A_u", base_u, r.get("hit_A_u"), r.get("t1"), r.get("t1_k"), r.get("ret_A_u"), tape, t0
        )
    )
    if r.get("hit_D_u") and base_u["how"] not in ("censored", "none"):
        books.append(
            _book("D_u", "one_r", tape.at(t0, r.get("one_r_k")), one_r, r.get("ret_D_u"), True)
        )
    else:
        books.append(
            _target_like("D_u", base_u, False, one_r, None, r.get("ret_D_u"), tape, t0, note=note_r)
        )
    # weekly and monthly units: the own clock and the long cap (fork 2)
    if tf in ("W", "M"):
        so = r.get("status_own")
        if so == "n/a" or so is None:
            base_o = _book(
                "C_own",
                "none",
                note="no month context for the week" if so == "n/a" else "not scored",
            )
        else:
            base_o = _clock_like(
                "C_own",
                so,
                r.get("days_own"),
                r.get("days_own"),
                r.get("ret_C_own"),
                level,
                direction,
                tape,
                t0,
            )
        books.append(base_o)
        books.append(
            _target_like(
                "A_own",
                base_o,
                r.get("reached1_own"),
                r.get("t1"),
                r.get("t1_k"),
                r.get("ret_A_own"),
                tape,
                t0,
            )
        )
        sl = r.get("status_long")
        base_l = (
            _book("C_long", "none", note="not scored")
            if sl is None
            else _clock_like(
                "C_long",
                sl,
                r.get("days_long"),
                r.get("days_long"),
                r.get("ret_C_long"),
                level,
                direction,
                tape,
                t0,
            )
        )
        books.append(base_l)
        books.append(
            _target_like(
                "A_long",
                base_l,
                r.get("reached1_long"),
                r.get("t1"),
                r.get("t1_k"),
                r.get("ret_A_long"),
                tape,
                t0,
            )
        )
    # the measured move as a target (fork 1)
    if mm_ok:
        books.append(
            _target_like(
                "A_mm",
                C,
                r.get("hit_A_mm"),
                r["mm_t1"],
                r.get("mm1_k"),
                r.get("ret_A_mm"),
                tape,
                t0,
            )
        )
    stack = [s for s in str(r.get("stack") or "").split("+") if s]
    return {
        "id": f"{coin}-{r['date']}-{tf}-{kind}-{direction}",
        "instrument": coin,
        "bar": tf,
        "pattern": KIND_WORDS.get(kind, kind),
        "kind": kind,
        "direction": direction,
        "class": r.get("cls"),
        "stack": [{"bar": s} for s in stack],
        "entry": {"t": t0, "price": level},
        "far": stop,
        "one_r": one_r,
        "r_pct": r.get("r_pct"),
        "targets": targets,
        "touches": {"one_r": tape.at(t0, r.get("one_r_k")), "far": tape.at(t0, r.get("stop_k"))},
        "books": books,
        "travel": {
            "mfe": r.get("mfe_x"),
            "mae": r.get("mae_x"),
            "window": "C",
            "next_bar": r.get("next_bar"),
        },
        "context": {"week_side": r.get("w_support"), "month_side": r.get("m_support")},
        "extras": {k: r.get(k) for k in EXTRAS if k in r} | {"dex": dex} | extra,
    }


# ----------------------------------------------------------------------------- the run


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:  # noqa: BLE001 (no git: the card still says so)
        return "unknown"


def run_card(as_of_ms: int, run_id: str | None = None) -> dict:
    as_of = datetime.fromtimestamp(as_of_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    return {
        "contract": K.CONTRACT,
        "id": run_id or f"management-book-{stamp_of(as_of_ms)}",
        "name": f"STRAT management book, Hyperliquid perps, as of {as_of}",
        "as_of": as_of,
        "source": {
            "repo": "tradingview-backtesting",
            "commit": git_commit(),
            "command": f"uv run python -m analysis.domino.trade_viewer export-run --as-of {as_of}",
            "rows": str(TRADES.name),
        },
        "clock": {
            "day_roll": "00:00 UTC",
            "resolution": "day",
            "weeks": "Monday 00:00 UTC",
            "months": "calendar",
        },
        "units": list(UNITS),
        "bars": ["1h", "1d"],
        "returns": "percent of price, equal size, no fees, no leverage",
        "rules": dict(RULES),
        "books": [dict(b) for b in BOOKS],
        "notes": "The management book's rows (analysis/domino/MANAGE_RECEIPT.md) in the viewer's contract; "
        "not exported: "
        + "; ".join(NOT_EXPORTED)
        + ". A book absent from a card does not apply to that trade.",
    }


def export_run(as_of_ms: int, out: Path, run_id: str | None = None, log=print) -> Path:
    """Write the run folder (run.json + one file per coin) from the rows and the cached bars."""
    out.mkdir(parents=True, exist_ok=True)
    rows = load_rows()
    run = run_card(as_of_ms, run_id)
    n = 0
    for meta in cached_universe(as_of_ms):
        coin = meta["coin"]
        daily = compact(normalize(json.load(open(cache_path(coin, "1d", as_of_ms))), as_of_ms))
        hp = cache_path(coin, "1h", as_of_ms)
        hourly = compact(normalize_hourly(json.load(open(hp)), as_of_ms)) if hp.exists() else []
        tape = Tape(daily, hourly)
        cards = [card_from_row(r, coin, meta["dex"], tape) for r in rows.get(coin, [])]
        ids = [c["id"] for c in cards]
        if len(set(ids)) != len(ids):
            raise ValueError(f"{coin}: duplicate card ids")
        doc = {"instrument": coin, "bars": {"1d": daily, "1h": hourly}, "trades": cards}
        with open(out / K._fname(coin), "w", encoding="utf-8") as fh:
            json.dump(doc, fh, separators=(",", ":"))
        n += len(cards)
    with open(out / "run.json", "w", encoding="utf-8") as fh:
        json.dump(run, fh, indent=1)
    log(f"exported {n:,} cards for {len(rows)} coins -> {out}")
    return out


# ----------------------------------------------------------------------------- the check


def check_run(run_id: str, root: Path = DATA, log=print) -> dict:
    """Compare an imported run's cards with the flat viewer data (`data/<coin>.json`) row for
    row: the level, each ladder book's return / reason / day, the touch days. Returns the
    counts; logs the first examples of every kind of difference."""
    counts: dict[str, int] = defaultdict(int)
    examples: dict[str, list[str]] = defaultdict(list)

    def diff(key: str, tag: str) -> None:
        counts[key] += 1
        if len(examples[key]) < 3:
            examples[key].append(tag)

    def same(a, b) -> bool:
        if a is None or b is None:
            return a is None and b is None
        return abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))

    for fname, doc in K.iter_files(root, run_id):
        flat_path = root / fname
        if not flat_path.exists():
            diff("coin missing from the flat data", doc["instrument"])
            continue
        flat = json.loads(flat_path.read_text(encoding="utf-8"))
        daily = flat["daily"]
        idx = {int(b[0]): i for i, b in enumerate(daily)}
        # the flat loader keeps a missing text field as the string "nan" / ""; read those as None
        rows = {
            (r["date"], r["tf"], r["kind"], r["direction"]): {
                k: (None if v in ("", "nan", "None") else v) for k, v in r.items()
            }
            for r in flat["trades"]
        }
        for c in doc["trades"]:
            key = (K.day_of(c["entry"]["t"]), c["bar"], c["kind"], c["direction"])
            r = rows.pop(key, None)
            tag = c["id"]
            if r is None:
                diff("card without a flat row", tag)
                continue
            counts["cards compared"] += 1
            if not same(c["entry"]["price"], r["level"]):
                diff("level", tag)
            i = idx.get(c["entry"]["t"])

            def at_k(k):
                if k is None:
                    return None
                j = None if i is None else i + int(k)
                return (
                    int(daily[j][0])
                    if j is not None and 0 <= j < len(daily)
                    else c["entry"]["t"] + int(k) * DAY
                )

            by_id = {b["id"]: b for b in c["books"]}
            for bid, ret_key, hit_key in (
                ("C", "ret_C", None),
                ("A", "ret_A", "hit_A"),
                ("B", "ret_B", "hit_B"),
                ("D", "ret_D", "hit_D"),
                ("D5", "ret_D5", "hit_D5"),
                ("ref", "ret5", None),
            ):
                b = by_id.get(bid)
                if b is None:
                    diff(f"{bid} absent", tag)
                    continue
                if not same(b["ret"], r.get(ret_key)):
                    diff(f"{bid} return", tag)
                if hit_key and (b["hit"] or False) != (r.get(hit_key) or False):
                    diff(f"{bid} hit", tag)
            C = by_id["C"]
            if C["how"] != STATUS_HOW.get(r["status"]):
                diff("C reason", tag)
            elif C["how"] == "clock" and C["at"] != at_k(r["exit_k"]):
                diff("C exit day", tag)
            elif C["how"] == "cap" and C["at"] != at_k(r["days"]):
                diff("C cap day", tag)
            D5 = by_id["D5"]
            want5 = (
                "one_r"
                if r.get("hit_D5")
                else ("none" if r.get("status5") is None else STATUS_HOW.get(r["status5"]))
            )
            if D5["how"] != want5:
                diff("D5 reason", tag)
            elif D5["how"] in ("clock", "cap") and D5["at"] != at_k(r["days_D5"]):
                diff("D5 day", tag)
            ref = by_id["ref"]
            want_ref = {"stop": "stop", "one_r": "one_r", "neither": "cap"}.get(
                r.get("out5"), "censored"
            )
            if ref["how"] != want_ref:
                diff("ref reason", tag)
            elif ref["how"] != "censored" and ref["at"] != at_k(r["days_ref"]):
                diff("ref day", tag)
            t1 = next((tg for tg in c["targets"] if tg["name"] == "T1"), None)
            if (t1 is None) != (r.get("t1") is None):
                diff("T1 present", tag)
            elif t1 is not None and (
                not same(t1["price"], r["t1"]) or t1["touched"] != at_k(r.get("t1_k"))
            ):
                diff("T1 price or touch day", tag)
            if c["touches"]["one_r"] != at_k(r.get("one_r_k")):
                diff("one R touch day", tag)
            Ch = by_id.get("C_h")
            sh = r.get("status_h")
            want_h = (
                "none" if sh in H_NOTE else ("censored" if sh == "censored" else STATUS_HOW[sh])
            )
            if (
                Ch is None
                or Ch["how"] != want_h
                or (Ch["how"] in ("clock", "cap") and not same(Ch["ret"], r.get("ret_C_h")))
            ):
                diff("hourly clock", tag)
        for key in rows:
            diff("flat row without a card", f"{doc['instrument']} {key}")
    log(f"check-run {run_id}: {counts.get('cards compared', 0):,} cards compared")
    for key, n in sorted(counts.items()):
        if key != "cards compared":
            log(f"  {key}: {n:,}  e.g. {', '.join(examples[key])}")
    if all(k == "cards compared" for k in counts):
        log("  no differences")
    return dict(counts)
