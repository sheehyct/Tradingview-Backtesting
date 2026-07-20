"""TVB-15 paper-trading twin: Python replica of pine/tfc_bf_watch.pine v6.

Replays the deployed tier-1 watch indicator (TV USER;7c28fa0b, 5m chart) over
archived Hyperliquid bars so the week's paper entries/exits are recorded
automatically. This module is the twin of record for the week-1 protocol
(docs/experiments/tvb15_paper_week1_protocol.md); the live TV instance is the
human surface and the week-end parity reference.

Fidelity contract (line refs = pine/tfc_bf_watch.pine v6):
- Gate (:112-120): close vs the D/W/M period OPEN -- the strat-methodology
  skill 4.1 bias predicate, per the TVB-1 charter reconciliation. Full
  alignment in a direction permits entries that way.
- Arm clock (:122-137, :475-478): entry tests the PRIOR COMPLETED arm-TF
  extremes; the snapshot rolls AFTER entry evaluation (audit-C1 corrected
  clock).
- Triggers (:463-473): strict break of the prior completed arm-TF extreme
  +/- 1 tick (R10: equality never breaks). Long is checked before short;
  entries only from flat, never on a bar that exited.
- Pools (f_pool :162-351): rolling compound-3 per base TF. At each base-TF
  close the envelope of the last N closed candles strictly takes out BOTH
  sides of the prior N's envelope (N ascending, smallest wins). Novelty vs
  the last formation, supersede on re-anchored left anchors, per-side ghost
  on duplicate-anywhere-in-pool or anchor separation < min_sep base periods,
  oldest-formation eviction beyond pool_cap. Wick-time anchors: the bar time
  of the bar that set the extreme (strict update only, first extreme wins).
- Per-bar scan (:297-351): line value extrapolated at the bar OPEN time; per
  line COLLECT exit candidates first, then transition state -- ANY
  containment touch consumes (even while flat); else a confirmed close
  beyond crosses. Replay bars are closed bars, so every bar is confirmed
  (TV historical-recompute semantics for the deployed 5m chart).
- Exit race (:432-461): same-bar precedence bf (harvest touch, direction-
  relative: short exits at the highest touched alive lower line below entry,
  long mirror) -> brk (confirmed close through an adverse alive line) ->
  flip (full opposite gate at a confirmed close). Cross-pool combine keeps
  the nearest candidate, pools iterated 12h, D, W, M with strict-improvement
  replacement (:353-430).

Deliberately not modeled (visual-only in the Pine): heads-up proximity
chars, status table, background tint. Known fidelity deltas (anchor-time
resolution of warm-up bars, TV-vs-HL wick variance, tick-live vs 5m-bar
evaluation) are declared in the protocol doc, not hidden here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

DAY = 86400
# timeframe.in_seconds("1M"): TV's average-month constant (30.4167 days).
# Only used for the M pool's min_sep gap; pool boundaries use calendar keys.
MONTH_S = 2628003


def key_12h(t: int) -> int:
    return t - t % (12 * 3600)


def key_1d(t: int) -> int:
    return t - t % DAY


def key_1w(t: int) -> int:
    """Monday 00:00 UTC anchored week start (fixture wstart)."""
    dt = datetime.fromtimestamp(t, tz=timezone.utc)
    mid = int(datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc).timestamp())
    return mid - dt.weekday() * DAY


def key_1mo(t: int) -> int:
    dt = datetime.fromtimestamp(t, tz=timezone.utc)
    return int(datetime(dt.year, dt.month, 1, tzinfo=timezone.utc).timestamp())


def line_val(t1: int, v1: float, t2: int, v2: float, t: int) -> float:
    """f_val (:140-141): linear extrapolation through the two anchors."""
    return v2 if t2 == t1 else v2 + (v2 - v1) / (t2 - t1) * (t - t2)


@dataclass
class Side:
    """One line of a formation. state: alive|consumed|crossed|superseded|ghost."""

    t1: int
    v1: float
    t2: int
    v2: float
    state: str = "alive"
    state_ts: int | None = None

    def val(self, t: int) -> float:
        return line_val(self.t1, self.v1, self.t2, self.v2, t)

    def anchors(self) -> tuple[int, float, int, float]:
        return (self.t1, self.v1, self.t2, self.v2)


@dataclass
class Formation:
    born: int
    N: int
    lo: Side
    up: Side


def _envelope(candles: list[tuple[float, float, int, int]]):
    """Max-high / min-low with wick times; first extreme wins ties (Pine
    iterates ascending and updates on strict comparison only)."""
    hm, lm, hmt, lmt = candles[0]
    for hh, ll, ht, lt in candles[1:]:
        if hh > hm:
            hm, hmt = hh, ht
        if ll < lm:
            lm, lmt = ll, lt
    return hm, hmt, lm, lmt


class Pool:
    """One rolling compound-3 pool on base TF `name` (f_pool :162-351).

    process_bar() performs the full per-bar pass in Pine order: base-candle
    completion + sweep on a period boundary, accumulation update, then the
    lifecycle/exit-candidate scan against the position standing at bar start.
    pool_cap=None disables eviction (fixture-parity mode; the deployed v6
    default is 12).
    """

    def __init__(
        self,
        name: str,
        key_fn,
        period_s: int,
        n_max: int = 6,
        min_sep: float = 1.0,
        pool_cap: int | None = 12,
    ):
        self.name = name
        self.key_fn = key_fn
        self.n_max = n_max
        self.min_gap = int(period_s * min_sep)
        self.pool_cap = pool_cap
        self.candles: list[tuple[float, float, int, int]] = []  # (hi, lo, hiT, loT)
        self.cur: list | None = None  # [key, hi, lo, hiT, loT]
        self.formations: list[Formation] = []

    def _sweep(self, born: int) -> None:
        """Completed-candle push + rolling compound-3 scan (:187-284)."""
        _, hi, lo, hiT, loT = self.cur
        self.candles.append((hi, lo, hiT, loT))
        if len(self.candles) > 2 * self.n_max:
            self.candles.pop(0)
        cnt = len(self.candles)
        for n in range(1, self.n_max + 1):
            if cnt < 2 * n:
                break
            a_hm, a_hmt, a_lm, a_lmt = _envelope(self.candles[cnt - n :])
            b_hm, b_hmt, b_lm, b_lmt = _envelope(self.candles[cnt - 2 * n : cnt - n])
            if not (a_hm > b_hm and a_lm < b_lm):  # R10 strict both-sides takeout
                continue
            lo_t = (b_lmt, b_lm, a_lmt, a_lm)
            up_t = (b_hmt, b_hm, a_hmt, a_hm)
            if self.formations:
                last = self.formations[-1]
                if last.lo.anchors() == lo_t and last.up.anchors() == up_t:
                    break  # identical to the newest formation: nothing new (:228-231)
                if last.lo.anchors()[:2] == lo_t[:2] and last.up.anchors()[:2] == up_t[:2]:
                    # same left anchors re-anchored -> supersede (:232-239)
                    if last.lo.state == "alive":
                        last.lo.state, last.lo.state_ts = "superseded", born
                    if last.up.state == "alive":
                        last.up.state, last.up.state_ts = "superseded", born
            lo_ghost = a_lmt - b_lmt < self.min_gap
            up_ghost = a_hmt - b_hmt < self.min_gap
            for g in self.formations:  # duplicate-anywhere scan (:245-250)
                if g.lo.anchors() == lo_t:
                    lo_ghost = True
                if g.up.anchors() == up_t:
                    up_ghost = True
            if not (lo_ghost and up_ghost):
                self.formations.append(
                    Formation(
                        born=born,
                        N=n,
                        lo=Side(*lo_t, state="ghost" if lo_ghost else "alive"),
                        up=Side(*up_t, state="ghost" if up_ghost else "alive"),
                    )
                )
                if self.pool_cap is not None and len(self.formations) > self.pool_cap:
                    self.formations.pop(0)  # oldest-formation eviction (:265-284)
            break  # smallest qualifying N wins

    def process_bar(
        self,
        ts: int,
        h: float,
        l: float,
        c: float,
        pos: int,
        entry_px: float | None,
        confirmed: bool = True,
    ) -> dict:
        """One bar through the pool. pos/entry_px = state at BAR START."""
        k = self.key_fn(ts)
        boundary = self.cur is not None and k != self.cur[0]
        if boundary:
            self._sweep(born=k)
        if self.cur is None or boundary:
            self.cur = [k, h, l, ts, ts]
        else:
            if h > self.cur[1]:
                self.cur[1], self.cur[3] = h, ts
            if l < self.cur[2]:
                self.cur[2], self.cur[4] = l, ts
        # lifecycle + exit-candidate scan (:297-351): collect, then transition
        xs = xl = None  # (value, N) harvest candidates
        brk_lo = brk_up = None
        n_alive = 0
        for fm in self.formations:
            side = fm.lo
            if side.state == "alive":
                v = side.val(ts)
                n_alive += 1
                touched = l <= v <= h
                if pos == -1 and touched and entry_px is not None and v < entry_px:
                    if xs is None or v > xs[0]:
                        xs = (v, fm.N)
                if pos == 1 and confirmed and c < v:
                    if brk_lo is None or v > brk_lo:
                        brk_lo = v
                if touched:
                    side.state, side.state_ts = "consumed", ts
                elif confirmed and c < v:
                    side.state, side.state_ts = "crossed", ts
            side = fm.up
            if side.state == "alive":
                v = side.val(ts)
                n_alive += 1
                touched = l <= v <= h
                if pos == 1 and touched and entry_px is not None and v > entry_px:
                    if xl is None or v < xl[0]:
                        xl = (v, fm.N)
                if pos == -1 and confirmed and c > v:
                    if brk_up is None or v < brk_up:
                        brk_up = v
                if touched:
                    side.state, side.state_ts = "consumed", ts
                elif confirmed and c > v:
                    side.state, side.state_ts = "crossed", ts
        return {"xs": xs, "xl": xl, "brk_lo": brk_lo, "brk_up": brk_up, "n_alive": n_alive}


GATE_TFS: tuple[tuple[str, object], ...] = (("D", key_1d), ("W", key_1w), ("M", key_1mo))
POOL_SPECS: tuple[tuple[str, object, int], ...] = (
    ("12h", key_12h, 12 * 3600),
    ("D", key_1d, DAY),
    ("W", key_1w, 7 * DAY),
    ("M", key_1mo, MONTH_S),
)


@dataclass
class TwinConfig:
    symbol: str
    mintick: float
    allow_long: bool = True
    allow_short: bool = True
    flip_backstop: bool = True
    brk_exit: bool = True
    n_max: int = 6
    min_sep: float = 1.0
    pool_cap: int | None = 12
    arm_tf_s: int = 900


@dataclass
class Twin:
    """One symbol's v6 replica: four pools + gates + arm clock + position."""

    cfg: TwinConfig
    pools: list[Pool] = field(default_factory=list)
    pos: int = 0
    entry_px: float | None = None
    entry_ts: int | None = None
    gate_open: dict = field(default_factory=lambda: {"D": None, "W": None, "M": None})
    gate_key: dict = field(default_factory=lambda: {"D": None, "W": None, "M": None})
    arm_key: int | None = None
    a_hi: float | None = None
    a_lo: float | None = None
    prev_ah: float | None = None
    prev_al: float | None = None

    def __post_init__(self):
        if not self.pools:
            self.pools = [
                Pool(name, kf, ps, self.cfg.n_max, self.cfg.min_sep, self.cfg.pool_cap)
                for name, kf, ps in POOL_SPECS
            ]

    def pool(self, name: str) -> Pool:
        return next(p for p in self.pools if p.name == name)

    def warm_pool(self, name: str, rows) -> None:
        """Phase A: feed one pool coarse bars (flat; lifecycle only)."""
        p = self.pool(name)
        for r in rows:
            ts, _o, h, l, c = int(r[0]), r[1], r[2], r[3], r[4]
            p.process_bar(ts, h, l, c, pos=0, entry_px=None)

    def seed_gates(self, rows) -> None:
        """Track D/W/M period opens across a bar stream (no other effects)."""
        for r in rows:
            ts, o = int(r[0]), r[1]
            for name, kf in GATE_TFS:
                k = kf(ts)
                if k != self.gate_key[name]:
                    self.gate_key[name], self.gate_open[name] = k, o

    def seed_arm(self, prev_ah: float, prev_al: float) -> None:
        """Set the prior completed arm-TF extremes at the replay start."""
        self.prev_ah, self.prev_al = prev_ah, prev_al

    def _position_step(
        self,
        ts: int,
        h: float,
        l: float,
        c: float,
        xs,
        xs_tf,
        xl,
        xl_tf,
        brk_lo,
        brk_lo_tf,
        brk_up,
        brk_up_tf,
        gate_up: bool,
        gate_dn: bool,
    ) -> list[dict]:
        """Exit race then entry, Pine order (:432-473). Mutates position."""
        cfg = self.cfg
        events: list[dict] = []

        def close_out(direction: str, kind: str, price: float, line_tf=None, line_n=None):
            sign = 1.0 if direction == "long" else -1.0
            events.append(
                {
                    "ts": ts,
                    "sym": cfg.symbol,
                    "action": "exit",
                    "dir": direction,
                    "kind": kind,
                    "price": price,
                    "line_tf": line_tf,
                    "line_N": line_n,
                    "entry_ts": self.entry_ts,
                    "entry_px": self.entry_px,
                    "pnl_pct": sign * (price - self.entry_px) / self.entry_px * 100.0,
                }
            )
            self.pos, self.entry_px, self.entry_ts = 0, None, None

        if self.pos == -1 and xs is not None:
            close_out("short", "bf", xs[0], xs_tf, xs[1])
        if self.pos == 1 and xl is not None:
            close_out("long", "bf", xl[0], xl_tf, xl[1])
        if cfg.brk_exit and self.pos == 1 and brk_lo is not None:
            close_out("long", "brk", c, brk_lo_tf)
        if cfg.brk_exit and self.pos == -1 and brk_up is not None:
            close_out("short", "brk", c, brk_up_tf)
        if self.pos == 1 and cfg.flip_backstop and gate_dn:
            close_out("long", "flip", c)
        if self.pos == -1 and cfg.flip_backstop and gate_up:
            close_out("short", "flip", c)
        exited = bool(events)

        if self.pos == 0 and not exited:
            if (
                cfg.allow_long
                and gate_up
                and self.prev_ah is not None
                and h >= self.prev_ah + cfg.mintick
            ):
                self.pos, self.entry_px, self.entry_ts = 1, self.prev_ah + cfg.mintick, ts
                events.append(
                    {
                        "ts": ts,
                        "sym": cfg.symbol,
                        "action": "enter",
                        "dir": "long",
                        "price": self.entry_px,
                    }
                )
            elif (
                cfg.allow_short
                and gate_dn
                and self.prev_al is not None
                and l <= self.prev_al - cfg.mintick
            ):
                self.pos, self.entry_px, self.entry_ts = -1, self.prev_al - cfg.mintick, ts
                events.append(
                    {
                        "ts": ts,
                        "sym": cfg.symbol,
                        "action": "enter",
                        "dir": "short",
                        "price": self.entry_px,
                    }
                )
        return events

    def replay_bar(self, ts: int, o: float, h: float, l: float, c: float, bar_s: int = 300):
        """Phase B: one closed chart bar through the full v6 pass."""
        # gate opens (f_open :112-117), then gate state on this bar's close
        for name, kf in GATE_TFS:
            k = kf(ts)
            if k != self.gate_key[name]:
                self.gate_key[name], self.gate_open[name] = k, o
        go = self.gate_open
        ready = all(v is not None for v in go.values())
        gate_up = ready and c > go["D"] and c > go["W"] and c > go["M"]
        gate_dn = ready and c < go["D"] and c < go["W"] and c < go["M"]
        # arm accumulation (:129-134)
        ak = ts - ts % self.cfg.arm_tf_s
        if ak != self.arm_key:
            self.arm_key, self.a_hi, self.a_lo = ak, h, l
        else:
            self.a_hi, self.a_lo = max(self.a_hi, h), min(self.a_lo, l)
        # pools see the position standing at bar start (:354-360)
        pos0, entry0 = self.pos, self.entry_px
        xs = xl = None
        xs_tf = xl_tf = brk_lo_tf = brk_up_tf = None
        brk_lo = brk_up = None
        for p in self.pools:
            r = p.process_bar(ts, h, l, c, pos0, entry0)
            if r["xs"] is not None and (xs is None or r["xs"][0] > xs[0]):
                xs, xs_tf = r["xs"], p.name
            if r["xl"] is not None and (xl is None or r["xl"][0] < xl[0]):
                xl, xl_tf = r["xl"], p.name
            if r["brk_lo"] is not None and (brk_lo is None or r["brk_lo"] > brk_lo):
                brk_lo, brk_lo_tf = r["brk_lo"], p.name
            if r["brk_up"] is not None and (brk_up is None or r["brk_up"] < brk_up):
                brk_up, brk_up_tf = r["brk_up"], p.name
        events = self._position_step(
            ts,
            h,
            l,
            c,
            xs,
            xs_tf,
            xl,
            xl_tf,
            brk_lo,
            brk_lo_tf,
            brk_up,
            brk_up_tf,
            gate_up,
            gate_dn,
        )
        # roll the arm snapshot LAST (corrected clock, :475-478)
        if (ts + bar_s) % self.cfg.arm_tf_s == 0:
            self.prev_ah, self.prev_al = self.a_hi, self.a_lo
        return events
