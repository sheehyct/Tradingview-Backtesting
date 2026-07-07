"""Loaders for the committed TV reference artifacts + the gate-cell registry.

The dumps were produced by scripts/tv_dump.mjs (TVB-6 trade format) against
the live Strategy Tester and are the trade-for-trade ground truth for the
Phase-3 equivalence gate. Loaders re-assert the dump's own fail-loud
invariants; a dump that fails them must never silently enter a comparison.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from tfc.config import TFCConfig

__all__ = ["Bars", "Dump", "Cell", "REFERENCE_CELLS", "load_bars", "load_dump", "load_cell"]

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = Path(os.environ.get("TFC_REFERENCE_DIR", REPO_ROOT / "analysis" / "reference"))

_VALID_DIRS = {"le", "se"}  # long entry / short entry (tv_dump.mjs convention)


@dataclass(frozen=True)
class Bars:
    symbol: str
    interval: str
    ts: np.ndarray  # int64 epoch SECONDS, bar OPEN, UTC, strictly increasing
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray

    def __len__(self) -> int:
        return len(self.ts)

    def index_of_ms(self) -> dict[int, int]:
        """bar open time in ms -> bar index (dump et/xt are fill-bar opens, ms)."""
        return {int(t) * 1000: i for i, t in enumerate(self.ts)}


@dataclass(frozen=True)
class Dump:
    path: str
    net: float
    trades: int  # closed trades (performance.all.totalTrades)
    open_trades: int
    rows: list[dict]  # TVB-6 rows {et,xt,ep,xp,dir,pp,pv,q,ddp,rnp,open}, entry-ordered

    @property
    def closed_rows(self) -> list[dict]:
        return [r for r in self.rows if not r["open"]]


def load_bars(path: str | Path) -> Bars:
    p = Path(path) if Path(path).is_absolute() else REFERENCE_DIR / path
    d = json.loads(p.read_text())
    bars = np.asarray(d["bars"], dtype=np.float64)
    if len(bars) != d["count"]:
        raise AssertionError(f"{p.name}: count {d['count']} != len(bars) {len(bars)}")
    ts = bars[:, 0].astype(np.int64)
    if not np.all(np.diff(ts) > 0):
        raise AssertionError(f"{p.name}: bar open times not strictly increasing")
    return Bars(
        symbol=d["symbol"],
        interval=d["interval"],
        ts=ts,
        open=bars[:, 1],
        high=bars[:, 2],
        low=bars[:, 3],
        close=bars[:, 4],
        volume=bars[:, 5],
    )


def load_dump(path: str | Path) -> Dump:
    p = Path(path) if Path(path).is_absolute() else REFERENCE_DIR / path
    d = json.loads(p.read_text())
    a = d["assert"]
    if not (a["lenOk"] and a["entryOrderOk"]):
        raise AssertionError(f"{p.name}: dump self-asserts failed: {a}")
    rows = d["list"]
    if len(rows) != a["listLen"] or a["listLen"] != a["closedN"] + a["openN"]:
        raise AssertionError(f"{p.name}: list length mismatch vs assert block: {a}")
    if d["trades"] != a["closedN"]:
        raise AssertionError(f"{p.name}: trades {d['trades']} != closedN {a['closedN']}")
    if d.get("marginCalls", 0) != 0:
        raise AssertionError(f"{p.name}: marginCalls != 0 (TVB-3 deadlock artifact)")
    bad_dirs = {r["dir"] for r in rows} - _VALID_DIRS
    if bad_dirs:
        raise AssertionError(f"{p.name}: unknown dir codes {bad_dirs}")
    ets = [r["et"] for r in rows]
    if any(b < a_ for a_, b in zip(ets, ets[1:])):
        raise AssertionError(f"{p.name}: rows not entry-time ordered")
    # Single-position strategy: each closed trade exits before the next enters.
    closed = [r for r in rows if not r["open"]]
    for prev, cur in zip(closed, closed[1:]):
        if cur["et"] < prev["xt"]:
            raise AssertionError(f"{p.name}: overlapping trades at et={cur['et']}")
    return Dump(path=str(p), net=d["net"], trades=d["trades"], open_trades=a["openN"], rows=rows)


@dataclass(frozen=True)
class Cell:
    """One equivalence-gate cell: a committed dump + the config that produced it."""

    name: str
    dump_file: str
    bars_file: str
    cfg: TFCConfig
    hard: bool  # hard-gate mechanism cover vs secondary regression cell


_FEE = 0.000125  # commission_value 0.0125 (percent per fill) as a rate
_15M = "tvb6_tv_xyzMSTR_15m.json"
_60M = "tvb6_tv_xyzMSTR_60m.json"
_E1 = ("60", "30", "15")
_E3 = ("240", "120", "60")
_CTRL_A = ("M", "W", "D", "60")

REFERENCE_CELLS: dict[str, Cell] = {
    c.name: c
    for c in [
        # -- hard gate: 4-cell mechanism cover (plan fork 2) --
        Cell(
            "ctrlB_0125_s1",
            "tvb6_WV_ctrlB_0125.json",
            _15M,
            TFCConfig(chart_tf="15", exec_tfs=_E1, comm_rate=_FEE),
            hard=True,
        ),
        Cell(
            "R1E1_0125_s1",
            "tvb6_WV_R1E1_0125.json",
            _15M,
            TFCConfig(chart_tf="15", exec_tfs=_E1, reg_mode="stand_aside", comm_rate=_FEE),
            hard=True,
        ),
        Cell(
            "R1E1gov2_0125_s1",
            "tvb6_WV_R1E1gov2_0125.json",
            _15M,
            TFCConfig(
                chart_tf="15",
                exec_tfs=_E1,
                reg_mode="stand_aside",
                gov_mode="ratchet",
                comm_rate=_FEE,
            ),
            hard=True,
        ),
        Cell(
            "R1E3_0125_s1",
            "tvb6_WV_R1E3_0125.json",
            _60M,
            TFCConfig(chart_tf="60", exec_tfs=_E3, reg_mode="stand_aside", comm_rate=_FEE),
            hard=True,
        ),
        # -- secondary regression cells --
        Cell(
            "ctrlB_0125_s10",
            "tvb6_WV_ctrlB_0125_s10.json",
            _15M,
            TFCConfig(chart_tf="15", exec_tfs=_E1, comm_rate=_FEE, slip_ticks=10),
            hard=False,
        ),
        Cell(
            "ctrlBgov2_0",
            "tvb6_WV_ctrlBgov2_0.json",
            _15M,
            TFCConfig(chart_tf="15", exec_tfs=_E1, gov_mode="ratchet", comm_rate=0.0),
            hard=False,
        ),
        Cell(
            "ctrlBgov2_0125",
            "tvb6_WV_ctrlBgov2_0125.json",
            _15M,
            TFCConfig(chart_tf="15", exec_tfs=_E1, gov_mode="ratchet", comm_rate=_FEE),
            hard=False,
        ),
        Cell(
            "ctrlA_0125_s1",
            "tvb6_WV_ctrlA_0125.json",
            _60M,
            TFCConfig(chart_tf="60", exec_tfs=_CTRL_A, comm_rate=_FEE),
            hard=False,
        ),
    ]
}


def load_cell(name: str) -> tuple[Cell, Bars, Dump]:
    cell = REFERENCE_CELLS[name]
    return cell, load_bars(cell.bars_file), load_dump(cell.dump_file)
