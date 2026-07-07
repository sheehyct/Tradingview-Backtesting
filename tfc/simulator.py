"""Bar-loop simulator: Python port of pine/baseline_continuity.pine (pv20).

Execution model (dump-verified in Phase 0 across ~20k trades):
- process_orders_on_close = false: orders decided at bar close execute from
  the NEXT bar. Exits (strategy.close) fill at next-bar open; entry breakout
  STOPs fill intrabar at the stop, or at the open when the bar opens through.
- Slippage is adverse on every fill: buys +slip, sells -slip.
- Entries arm only when FLAT and the stop lives exactly one bar (re-armed
  with fresh levels each close, cancelled when conditions fail).
- Sizing: 100% of equity at the slipped-stop basis (NOT the actual fill on
  gap-throughs), floored to qty_step.
- Governor v2 ratchet: arms on GROSS profit <= 0 (strategy.closedtrades.
  profit() is gross of commission -- TVB-7 adjudication); ratchet level is
  the TRIGGER; reset on winning same-direction exit or full-opposite exec
  alignment, evaluated loss-arm-first on the same bar.

All trigger/stop arithmetic is in integer TICK space: float `high + mintick`
can exceed the true sum and silently miss fills TV takes. Gate comparisons
(close vs period open) stay in raw file floats: pure comparisons of
same-parse values, no arithmetic, so no epsilon is needed (and none exists
in the Pine).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from tfc.config import TFCConfig
from tfc.periods import ftfc, period_open_series
from tfc.tv_reference import Bars

__all__ = ["SimResult", "compute_gates", "simulate"]

Q_FLOOR_EPS = 1e-5  # in qty-step units; see the comment at the floor call


@dataclass(frozen=True)
class SimResult:
    closed: list[dict]  # dump-row schema: et,xt,ep,xp,dir,pp,pv,q (times ms)
    open_trade: dict | None  # {et,dir,ep,q} if a position is open after the last bar
    final_equity: float
    net: float  # (final_equity - initial) / initial, closed trades only


def compute_gates(bars: Bars, cfg: TFCConfig):
    """Per-bar exec-gate flags and regime permits (all evaluated at bar close)."""
    exec_opens = [period_open_series(bars.ts, bars.open, tf) for tf in cfg.exec_tfs]
    up, dn = ftfc(bars.close, exec_opens)
    n = len(bars)
    if cfg.reg_mode == "off":
        long_permit = np.ones(n, dtype=bool)
        short_permit = np.ones(n, dtype=bool)
    else:  # stand_aside: aligned regime permits ONLY that direction; grey blocks both
        reg_opens = [period_open_series(bars.ts, bars.open, tf) for tf in cfg.reg_tfs]
        long_permit, short_permit = ftfc(bars.close, reg_opens)
    return up, dn, long_permit, short_permit


def simulate(bars: Bars, cfg: TFCConfig) -> SimResult:
    up, dn, lp, sp = compute_gates(bars, cfg)

    mt = cfg.mintick
    comm = cfg.comm_rate
    step = cfg.qty_step
    slip_t = cfg.slip_ticks
    o_t = np.rint(bars.open / mt).astype(np.int64)
    h_t = np.rint(bars.high / mt).astype(np.int64)
    l_t = np.rint(bars.low / mt).astype(np.int64)
    ts_ms = bars.ts * 1000

    eq = cfg.initial_capital
    pos = 0  # +1 long, -1 short, 0 flat
    q_open = 0.0
    ep_open = 0.0
    et_open = 0
    pending_exit = False
    armed = 0  # armed stop for the NEXT bar: +1/-1/0
    stop_t = 0  # armed stop level in ticks
    ratchet_long: int | None = None
    ratchet_short: int | None = None
    trig_long_filled: int | None = None
    trig_short_filled: int | None = None
    gov = cfg.gov_mode == "ratchet"
    closed: list[dict] = []

    for i in range(len(bars)):
        pos_prev = pos  # Pine strategy.position_size[1] as seen on bar i
        gross_last = math.nan  # gross profit of a trade closed at THIS bar's open

        # ---------------- Phase A: fills at open[i] ----------------
        if pending_exit:
            xp = (o_t[i] - slip_t) * mt if pos > 0 else (o_t[i] + slip_t) * mt
            sign = 1.0 if pos > 0 else -1.0
            gross_last = q_open * sign * (xp - ep_open)
            pv = gross_last - comm * q_open * (ep_open + xp)
            closed.append(
                {
                    "et": int(ts_ms[et_open]),
                    "xt": int(ts_ms[i]),
                    "ep": ep_open,
                    "xp": xp,
                    "dir": "le" if pos > 0 else "se",
                    "pp": pv / (q_open * ep_open * (1.0 + comm)),
                    "pv": pv,
                    "q": q_open,
                    "open": False,
                }
            )
            eq += pv
            pos = 0
            pending_exit = False
        elif armed != 0:
            fill_t = None
            if armed > 0:
                if o_t[i] > stop_t:
                    fill_t = o_t[i] + slip_t  # opened through: fill at open
                elif h_t[i] >= stop_t:
                    fill_t = stop_t + slip_t  # intrabar breakout fill
                basis = (stop_t + slip_t) * mt  # qty basis = slipped stop
            else:
                if o_t[i] < stop_t:
                    fill_t = o_t[i] - slip_t
                elif l_t[i] <= stop_t:
                    fill_t = stop_t - slip_t
                basis = (stop_t - slip_t) * mt
            if fill_t is not None:
                # Q_FLOOR_EPS (plan risk 1 fallback, adjudicated TVB-8): TV's
                # internal double-precision equity can sit ~1e-6 USD above this
                # chain, flipping an exact-boundary floor. Exactly ONE trade in
                # ~20,300 across all 8 reference cells lands within 2e-5 of a
                # boundary (ctrlB_0125_s10 trade 686, ratio 6.4e-6 BELOW), so
                # eps=1e-5 resolves it and provably cannot false-flip any other
                # reference trade (see scripts/tfc_gate_report.py history).
                q = math.floor(eq / (basis * (1.0 + comm)) / step + Q_FLOOR_EPS) * step
                if q > 0:
                    pos = armed
                    ep_open = fill_t * mt
                    q_open = q
                    et_open = i
        armed = 0  # the stop lives exactly one bar

        # ---------------- Phase B: script logic at close[i] (Pine order) ----------------
        # 1) state-stop exits (fill next bar open)
        if pos > 0 and not up[i]:
            pending_exit = True
        if pos < 0 and not dn[i]:
            pending_exit = True

        # 2) governor bookkeeping (runs regardless of gov_mode, as in the Pine;
        #    gov_mode only gates the entry check)
        if pos > 0 and pos_prev <= 0:
            trig_long_filled = h_t[i - 1] + 1  # the filled trade's trigger
        if pos < 0 and pos_prev >= 0:
            trig_short_filled = l_t[i - 1] - 1
        if pos == 0 and pos_prev > 0:
            ratchet_long = None if gross_last > 0 else trig_long_filled
        if pos == 0 and pos_prev < 0:
            ratchet_short = None if gross_last > 0 else trig_short_filled
        if dn[i]:  # alignment reset AFTER loss-arm
            ratchet_long = None
        if up[i]:
            ratchet_short = None

        # 3) entries: arm a one-bar breakout stop only when flat
        if pos == 0:
            gl_ok = (not gov) or ratchet_long is None or (h_t[i] + 1 > ratchet_long)
            gs_ok = (not gov) or ratchet_short is None or (l_t[i] - 1 < ratchet_short)
            if cfg.allow_long and up[i] and lp[i] and gl_ok:
                armed = 1
                stop_t = h_t[i] + 1
            elif cfg.allow_short and dn[i] and sp[i] and gs_ok:
                armed = -1
                stop_t = l_t[i] - 1

    open_trade = None
    if pos != 0:
        open_trade = {
            "et": int(ts_ms[et_open]),
            "dir": "le" if pos > 0 else "se",
            "ep": ep_open,
            "q": q_open,
        }
    return SimResult(
        closed=closed,
        open_trade=open_trade,
        final_equity=eq,
        net=(eq - cfg.initial_capital) / cfg.initial_capital,
    )
