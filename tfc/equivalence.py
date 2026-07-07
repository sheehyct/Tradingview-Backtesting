"""Trade-for-trade equivalence between the simulator and a committed TV dump.

Prefix rule: dumps captured later in a session than the bar files carry live
tail-drift trades; only closed rows with xt <= the last committed bar are
comparable. The comparison window ends there, plus one boundary check: if
the dump's next trade ENTERED inside the bar window, the sim must be holding
exactly that position open at the end; otherwise the sim must be flat.

Tolerances (plan + Phase-0 calibration): et/xt/dir EXACT; ep/xp <= 1e-9
(tick-space fills vs same-parse floats differ only by ~1e-13 representation);
q within step/2 (floor-boundary flips are FAILURES to adjudicate, plan risk
1); pv <= 1e-4 absolute (dump serialization); pp <= 2e-8 (corrected
cost-basis formula reproduces dumps to <= 8.3e-9).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tfc.simulator import SimResult, simulate
from tfc.tv_reference import load_cell

__all__ = ["CellReport", "compare_cell"]

EP_TOL = 1e-9
Q_TOL_STEPS = 0.5
PV_TOL = 1e-4
PP_TOL = 2e-8


@dataclass
class CellReport:
    cell: str
    passed: bool
    prefix_trades: int
    sim_trades: int
    tail_skipped: int
    first_mismatch: dict | None = None
    max_err: dict = field(default_factory=dict)
    boundary: str = ""

    def summary(self) -> str:
        s = (
            f"{self.cell:<20} {'PASS' if self.passed else 'FAIL':<5} "
            f"prefix={self.prefix_trades} sim={self.sim_trades} tail={self.tail_skipped} "
            f"ep_err={self.max_err.get('ep', 0):.1e} xp_err={self.max_err.get('xp', 0):.1e} "
            f"pv_err={self.max_err.get('pv', 0):.1e} pp_err={self.max_err.get('pp', 0):.1e} "
            f"[{self.boundary}]"
        )
        if self.first_mismatch:
            s += f"\n  FIRST MISMATCH: {self.first_mismatch}"
        return s


def _row_mismatch(k: int, want: dict, got: dict, step: float) -> tuple[str, object, object] | None:
    if got["et"] != want["et"]:
        return ("et", want["et"], got["et"])
    if got["dir"] != want["dir"]:
        return ("dir", want["dir"], got["dir"])
    if got["xt"] != want["xt"]:
        return ("xt", want["xt"], got["xt"])
    if abs(got["ep"] - want["ep"]) > EP_TOL:
        return ("ep", want["ep"], got["ep"])
    if abs(got["xp"] - want["xp"]) > EP_TOL:
        return ("xp", want["xp"], got["xp"])
    if abs(got["q"] - want["q"]) > Q_TOL_STEPS * step:
        return ("q", want["q"], got["q"])
    if abs(got["pv"] - want["pv"]) > PV_TOL:
        return ("pv", want["pv"], got["pv"])
    if abs(got["pp"] - want["pp"]) > PP_TOL:
        return ("pp", want["pp"], got["pp"])
    return None


def compare_cell(name: str, sim: SimResult | None = None) -> CellReport:
    cell, bars, dump = load_cell(name)
    if sim is None:
        sim = simulate(bars, cell.cfg)
    last_ms = int(bars.ts[-1]) * 1000
    step = cell.cfg.qty_step

    prefix = [r for r in dump.closed_rows if r["xt"] <= last_ms]
    tail = [r for r in dump.rows if r["open"] or r["xt"] > last_ms]
    rep = CellReport(
        cell=name,
        passed=True,
        prefix_trades=len(prefix),
        sim_trades=len(sim.closed),
        tail_skipped=len(tail),
    )

    n = min(len(prefix), len(sim.closed))
    for k in range(n):
        want, got = prefix[k], sim.closed[k]
        for f in ("ep", "xp", "pv", "pp"):
            rep.max_err[f] = max(rep.max_err.get(f, 0.0), abs(got[f] - want[f]))
        m = _row_mismatch(k, want, got, step)
        if m:
            rep.passed = False
            rep.first_mismatch = {
                "trade": k,
                "field": m[0],
                "dump": m[1],
                "sim": m[2],
                "dump_row": {x: want[x] for x in ("et", "xt", "dir", "ep", "xp", "q")},
            }
            return rep

    if len(sim.closed) != len(prefix):
        rep.passed = False
        rep.first_mismatch = {
            "trade": n,
            "field": "count",
            "dump": len(prefix),
            "sim": len(sim.closed),
            "next": (prefix[n] if len(prefix) > n else sim.closed[n]),
        }
        return rep

    # Boundary: the dump's first row beyond the prefix (closed tail or open row)
    nxt = min(tail, key=lambda r: r["et"]) if tail else None
    if nxt is not None and nxt["et"] <= last_ms:
        # entered inside the window, exited after (or still open): sim must hold it
        if sim.open_trade is None:
            rep.passed = False
            rep.boundary = f"dump holds {nxt['dir']} from et={nxt['et']}, sim is flat"
        elif (
            sim.open_trade["et"] != nxt["et"]
            or sim.open_trade["dir"] != nxt["dir"]
            or abs(sim.open_trade["ep"] - nxt["ep"]) > EP_TOL
            or abs(sim.open_trade["q"] - nxt["q"]) > Q_TOL_STEPS * step
        ):
            rep.passed = False
            rep.boundary = f"open-position mismatch: dump={nxt} sim={sim.open_trade}"
        else:
            rep.boundary = "open position matches"
    else:
        if sim.open_trade is not None:
            rep.passed = False
            rep.boundary = f"sim holds {sim.open_trade}, dump has no in-window open trade"
        else:
            rep.boundary = "flat at boundary"
    return rep
