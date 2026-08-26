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

TVB-21 Tier B extension (docs/experiments/tvb21_tier_b_prereg.md): behind
inert defaults, TwinConfig can swap the arm trigger for the pine-exact
Magnitude+Targets pattern layer (analysis/paper/patterns.py), add the
BF-proximity / chop entry vetoes, and replace the bf-touch harvest exit with
frozen entry-snapshot target exits. entry_mode="arm" (the default) leaves
every pre-existing code path bit-identical.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone

from analysis.paper.patterns import USER_DICTIONARY, PatternConfig, PatternDetector


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
        supersede_per_side: bool = True,
        evict_retired_first: bool = True,
    ):
        self.name = name
        self.key_fn = key_fn
        self.n_max = n_max
        self.min_gap = int(period_s * min_sep)
        self.pool_cap = pool_cap
        # v6.1 audit fixes; pass False for v6.0-parity replays
        self.supersede_per_side = supersede_per_side
        self.evict_retired_first = evict_retired_first
        self.evict_alive = 0  # alive-at-eviction counter (either mode)
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
                lo_same = last.lo.anchors() == lo_t
                up_same = last.up.anchors() == up_t
                if lo_same and up_same:
                    break  # identical to the newest formation: nothing new (:228-231)
                if last.lo.anchors()[:2] == lo_t[:2] and last.up.anchors()[:2] == up_t[:2]:
                    # same left anchors re-anchored -> supersede (:232-239); v6.1
                    # (audit F1) supersedes ONLY sides that actually re-anchored
                    if (not self.supersede_per_side or not lo_same) and last.lo.state == "alive":
                        last.lo.state, last.lo.state_ts = "superseded", born
                    if (not self.supersede_per_side or not up_same) and last.up.state == "alive":
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
                    # v6.1 (audit F2): oldest fully-RETIRED formation first;
                    # alive only when unavoidable (counted). v6.0: always oldest.
                    ei = 0
                    if self.evict_retired_first:
                        for k, g in enumerate(self.formations):
                            if g.lo.state != "alive" and g.up.state != "alive":
                                ei = k
                                break
                        else:
                            self.evict_alive += 1
                    else:
                        f0 = self.formations[0]
                        if f0.lo.state == "alive" or f0.up.state == "alive":
                            self.evict_alive += 1
                    self.formations.pop(ei)
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
    supersede_per_side: bool = True
    evict_retired_first: bool = True
    arm_tf_s: int = 900
    # Pine's gate helper (ta.valuewhen(timeframe.change(tf), open, 0)) has NO
    # value until the feed contains a period BOUNDARY (timeframe.change is
    # false on the first chart bar), so a cold-started chart is gate-not-ready
    # until the first D/W/M boundary -- the M leg gates trading until the
    # first month roll. True reproduces that (TVB-20 control-port parity);
    # False keeps the twin's original bootstrap (first loaded bar adopted as
    # every period's open), which all pre-TVB-20 replays and sweeps used.
    pine_gate_warmup: bool = False
    # --- TVB-21 Tier B pattern layer (docs/experiments/tvb21_tier_b_prereg.md).
    # Defaults are inert: "arm" never constructs the detector and every veto/
    # target branch is additionally guarded on non-None values.
    entry_mode: str = "arm"  # "arm" (C1 trigger) | "pattern" (Tier B arms)
    pattern_tf_s: int = 3600  # signal TF for the dictionary (pre-reg: 1H)
    pattern_enabled: frozenset | None = None  # None -> patterns.USER_DICTIONARY
    pattern_ext_targets: int = 5  # pine extTargets (ladder = this + 1 levels)
    pattern_pmg_bars: int = 5
    bf_prox_veto_pct: float | None = None  # 1.0 = veto within 1% of nearest alive harvest line
    # the "chop" veto is GATE-OPEN PROXIMITY (prospective fill near a D/W/M
    # period open). The name is historical artifact-key vocabulary; it is NOT
    # the M+T indicator's reversal-streak-since-T1 chop state, which was never
    # ported (naming collision flagged by the 2026-08-14 assessment, P1-3)
    chop_veto_pct: float | None = None  # 2.0 = veto within 2% of any D/W/M gate open
    exit_targets: int | None = None  # None = C1 exits; 1 = T1-always; 2 = rung 2 (fallback T1)
    bf_harvest_exit: bool = True  # False in package arms: targets replace bf-touch
    # --- TVB-23 T1-floor round (docs/experiments/tvb23_t1floor_prereg.md).
    # Defaults inert. The ATR veto forms are mutually exclusive with the pct
    # forms (enforced in Twin.__post_init__); the floor is fee-grounded and
    # stays a fixed percent even in ATR-veto arms (prereg ruling 1).
    t1_floor_pct: float | None = (
        None  # 0.25 = veto entries whose frozen T1 sits < 0.25% beyond fill
    )
    bf_prox_veto_atr: float | None = (
        None  # k: veto within k x ATR (price units) of the nearest line
    )
    chop_veto_atr: float | None = None  # k: veto within k x ATR of any D/W/M gate open
    atr_window: int = 14  # Wilder window over completed signal-TF bars
    retrace_census: bool = False  # read-only M+T position-health first-label stamps
    # --- TVB-25 exit round (docs/experiments/tvb25_exit_round_prereg.md +
    # the 2026-08-16 amendment). Defaults inert: with every field OFF the
    # incumbent race runs verbatim and existing arms stay bit-identical.
    # When ANY is on, _position_step dispatches to the amendment's ruled
    # race: i3 -> stop -> protective -> targets -> BF -> brk -> flip ->
    # state stop (risk exits close ALL remaining tranches, D5).
    state_stop: bool = False  # C0 2-against at 1H close (amendment D14 inclusive)
    intrabar3_exit: bool = False  # i3 invalidation, entry hour only (amendment)
    stop_mode: str | None = None  # None | "structural" (per-setup + ATR fallback) | "atr"
    stop_atr_mult: float = 3.0  # D2: 3 x Wilder ATR(14, 1H), frozen at entry
    tranche_profile: str | None = None  # None | "P1" | "P2" (amendment fold-to-runner)
    bf_arm_rung: int | None = None  # X1: BF harvest armed once rung N reached post-entry


class _Atr:
    """Wilder ATR over completed signal-TF bars (TVB-23 prereg "Mechanics").

    TR = max(h - l, |h - prev_close|, |l - prev_close|); the first bar (no
    prior close) uses h - l. Seed = SMA of the first `window` TRs, then
    Wilder smoothing atr = (atr * (window - 1) + tr) / window. `value` stays
    None until the window fills; the veto layer reads the value as of the
    last COMPLETED bar (the developing bar never contributes). Aggregation
    boundaries mirror the pattern detector's (ts - ts % tf_s).
    """

    def __init__(self, tf_s: int, window: int):
        self.tf_s = tf_s
        self.window = window
        self.key: int | None = None
        self.cur_h: float | None = None
        self.cur_l: float | None = None
        self.cur_c: float | None = None
        self.prev_c: float | None = None
        self._seed_trs: list[float] = []
        self.value: float | None = None

    def push_completed(self, h: float, l: float, c: float) -> None:  # noqa: E741
        tr = (
            h - l if self.prev_c is None else max(h - l, abs(h - self.prev_c), abs(l - self.prev_c))
        )
        if self.value is None:
            self._seed_trs.append(tr)
            if len(self._seed_trs) == self.window:
                self.value = sum(self._seed_trs) / self.window
        else:
            self.value = (self.value * (self.window - 1) + tr) / self.window
        self.prev_c = c

    def seed(self, bars) -> None:
        """Warm from archived COMPLETED signal-TF bars (ts, o, h, l, c)."""
        for r in bars:
            self.push_completed(r[2], r[3], r[4])

    def update(self, ts: int, h: float, l: float, c: float) -> None:  # noqa: E741
        """Feed one chart bar; completes the prior signal-TF bar on rollover."""
        k = ts - ts % self.tf_s
        if self.key is None or k != self.key:
            if self.key is not None and self.cur_h is not None:
                self.push_completed(self.cur_h, self.cur_l, self.cur_c)
            self.key = k
            self.cur_h, self.cur_l, self.cur_c = h, l, c
        else:
            self.cur_h = max(self.cur_h, h)
            self.cur_l = min(self.cur_l, l)
            self.cur_c = c


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
    pattern: PatternDetector | None = None
    tgt_px: float | None = None
    tgt_rung: int | None = None
    atr: _Atr | None = None
    first_retrace_ts: int | None = None
    first_p3_ts: int | None = None
    # --- TVB-25 exit-round position state (amendment 2026-08-16); all None/
    # inert unless the matching TwinConfig feature is on.
    tranches: list | None = None  # pending profit tranches [{frac, level, label}]
    runner_frac: float | None = None
    floor_armed: bool = False  # P2: arms on the first executed bank
    retrace_done: bool = False
    runner_be_px: float | None = None  # P2 post-retrace breakeven floor
    bf_armed: bool = True  # X1: False from entry until rung reach
    arm_rung_level: float | None = None  # X1 frozen arming rung
    i3_level: float | None = None
    i3_key: int | None = None  # signal-TF key of the entry hour
    stop_px: float | None = None
    stop_kind: str | None = None  # "structural" | "atr"
    exit_counters: dict = field(
        default_factory=lambda: {
            "collision_bars": 0,
            "floor_armed_inert": 0,
            "stop_degenerate_anchor": 0,
            "stop_atr_unavailable": 0,
            "i3_degenerate": 0,
            "state_degenerate": 0,
        }
    )
    # D9 additive diagnostic (TVB-26 audit fold): per class-combination
    # collision counts, keyed "cls+cls" sorted -- serves the promised user
    # revisit of the provisional risk-first order (only order-sensitive
    # combinations can bite)
    collision_pairs: dict = field(default_factory=dict)
    # D9 collision receipts (TVB-28 audit fold, 2026-08-26): one row per
    # collision bar recording every executable class's candidate fill
    # beside what actually executed. The TVB-26 audit had to reconstruct
    # candidate fills forensically to show the ruled order does NOT always
    # book the worse fill (user re-ruled it a priority CONVENTION, not a
    # pessimism guarantee, 2026-08-24). SCOPE (TVB-28 audit MEDIUM-3,
    # user-ruled 2026-08-26): this is a FIRST-FILL diagnostic -- deltas
    # compare each one-price candidate to the first executed fill, which
    # is exact for one-fill races but is NOT a path-aware both-ways
    # pricing on multi-fill tranche bars (the executed rows carry the
    # full fraction path; pricing alternative orderings needs a
    # fraction-weighted simulation that only gets built behind a prereg
    # if a ruling will hang on it).
    collision_receipts: list = field(default_factory=list)
    _anchor_freeze: dict = field(default_factory=dict)
    _anchor_freeze_key: int | None = None
    t1_px: float | None = None  # P2 frozen T1 (retrace trigger)
    veto_counts: dict = field(
        default_factory=lambda: {
            "candidates": 0,
            "no_target": 0,
            "no_target_vetoed": 0,
            "bf_prox": 0,
            "chop": 0,
            "both": 0,
            "t1_floor": 0,
            "t1_floor_le0": 0,
            "t1_floor_small": 0,
            "t1_floor_only": 0,
            "entries": 0,
        }
    )

    def __post_init__(self):
        if not self.pools:
            self.pools = [
                Pool(
                    name,
                    kf,
                    ps,
                    self.cfg.n_max,
                    self.cfg.min_sep,
                    self.cfg.pool_cap,
                    supersede_per_side=self.cfg.supersede_per_side,
                    evict_retired_first=self.cfg.evict_retired_first,
                )
                for name, kf, ps in POOL_SPECS
            ]
        if self.cfg.bf_prox_veto_pct is not None and self.cfg.bf_prox_veto_atr is not None:
            raise ValueError("bf_prox_veto_pct and bf_prox_veto_atr are mutually exclusive")
        if self.cfg.chop_veto_pct is not None and self.cfg.chop_veto_atr is not None:
            raise ValueError("chop_veto_pct and chop_veto_atr are mutually exclusive")
        if self.cfg.stop_mode not in (None, "structural", "atr"):
            raise ValueError(f"unknown stop_mode {self.cfg.stop_mode!r}")
        if self.cfg.tranche_profile not in (None, "P1", "P2"):
            raise ValueError(f"unknown tranche_profile {self.cfg.tranche_profile!r}")
        if self.cfg.tranche_profile is not None and self.cfg.exit_targets is not None:
            raise ValueError("tranche_profile replaces exit_targets; set exit_targets=None")
        if self.cfg.bf_arm_rung is not None and not self.cfg.bf_harvest_exit:
            raise ValueError("bf_arm_rung gates the BF harvest exit; enable bf_harvest_exit")
        if self.cfg.state_stop and self.cfg.arm_tf_s != 3600:
            raise ValueError("state_stop is the C0 2-against at 1H close; arm_tf_s must be 3600")
        if (
            self.cfg.bf_prox_veto_atr is not None
            or self.cfg.chop_veto_atr is not None
            or self.cfg.stop_mode is not None
        ) and self.atr is None:
            self.atr = _Atr(self.cfg.pattern_tf_s, self.cfg.atr_window)
        if self.cfg.entry_mode == "pattern" and self.pattern is None:
            self.pattern = PatternDetector(
                PatternConfig(
                    mintick=self.cfg.mintick,
                    tf_s=self.cfg.pattern_tf_s,
                    ext_targets=self.cfg.pattern_ext_targets,
                    pmg_bars=self.cfg.pattern_pmg_bars,
                    enabled=(
                        self.cfg.pattern_enabled
                        if self.cfg.pattern_enabled is not None
                        else USER_DICTIONARY
                    ),
                )
            )

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

    def _alive_harvest_vals(self, ts: int, direction: int) -> list[float]:
        """Alive harvest-side line values at bar-open time (TVB-21 BF-prox veto).

        Long harvest side = upper lines, short = lower lines, across ALL
        enabled pools (pre-reg ruling 6). Must be called BEFORE the pools
        process this bar so the values reflect the bar-open alive set.
        """
        out: list[float] = []
        for p in self.pools:
            for f in p.formations:
                side = f.up if direction == 1 else f.lo
                if side.state == "alive":
                    out.append(side.val(ts))
        return out

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
        o: float | None = None,
        sig=None,
        prox_vals=None,
        hour_end: bool = False,
    ) -> list[dict]:
        """Exit race then entry, Pine order (:432-473). Mutates position.

        o/sig/prox_vals are the TVB-21 pattern-arm inputs (bar open, live
        pattern Signal, bar-open alive harvest-line values); all None on the
        default arm path. hour_end marks the arm-TF-completing bar (TVB-25
        state stop, D14); the default False keeps direct callers inert.
        """
        cfg = self.cfg
        events: list[dict] = []

        def close_out(direction: str, kind: str, price: float, line_tf=None, line_n=None, **extra):
            sign = 1.0 if direction == "long" else -1.0
            ev = {
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
            ev.update(extra)  # TVB-25 fields only; empty on pre-existing paths
            if cfg.retrace_census:
                # TVB-23 census stamps ride the exit event only under the
                # flag so the default event shape (golden-pinned) is untouched
                ev["first_retrace_ts"] = self.first_retrace_ts
                ev["first_p3_ts"] = self.first_p3_ts
            events.append(ev)
            self.pos, self.entry_px, self.entry_ts = 0, None, None
            self.tgt_px = self.tgt_rung = None
            self.first_retrace_ts = self.first_p3_ts = None
            self._clear_tvb25_state()

        tvb25 = (
            cfg.state_stop
            or cfg.intrabar3_exit
            or cfg.stop_mode is not None
            or cfg.tranche_profile is not None
            or cfg.bf_arm_rung is not None
        )
        if tvb25:
            self._tvb25_exit_race(
                ts,
                o,
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
                hour_end,
                events,
                close_out,
            )
        else:
            # incumbent Pine race (parity-pinned; TVB-22/23 arms + controls)
            if cfg.bf_harvest_exit:
                if self.pos == -1 and xs is not None:
                    close_out("short", "bf", xs[0], xs_tf, xs[1])
                if self.pos == 1 and xl is not None:
                    close_out("long", "bf", xl[0], xl_tf, xl[1])
            elif cfg.exit_targets is not None:
                # TVB-21 package arms: the frozen entry-snapshot target occupies
                # the bf slot; touch exits AT the level (bf-touch convention).
                # TVB-22 amendment (audit F1, user-ruled): touch = the bar RANGE
                # CONTAINS the level, never a one-sided reach -- a born-beyond
                # trade exits at the first bar that actually trades the level,
                # and a bar wholly beyond the level does not exit (gap-past
                # edge, same as the C1 bf containment touch).
                if self.pos == 1 and self.tgt_px is not None and l <= self.tgt_px <= h:
                    close_out("long", "tgt", self.tgt_px, None, self.tgt_rung)
                elif self.pos == -1 and self.tgt_px is not None and l <= self.tgt_px <= h:
                    close_out("short", "tgt", self.tgt_px, None, self.tgt_rung)
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
            self._entry_step(ts, o, h, l, gate_up, gate_dn, sig, prox_vals, events)
            if (
                cfg.intrabar3_exit
                and self.pos != 0
                and self.i3_level is not None
                and (
                    self.i3_level - l >= cfg.mintick
                    if self.pos == 1
                    else h - self.i3_level >= cfg.mintick
                )
            ):
                # amendment degenerate case: the ENTRY 5m bar itself completes
                # the Type 3 -- exit at this bar's close, flagged and counted
                self.exit_counters["i3_degenerate"] += 1
                frac = (
                    {"frac": 1.0, "tranche": "all"}
                    if (self.tranches is not None or self.runner_frac is not None)
                    else {}
                )
                close_out("long" if self.pos == 1 else "short", "i3", c, i3_degenerate=True, **frac)
            if (
                cfg.state_stop
                and self.pos != 0
                and hour_end
                and self.prev_ah is not None
                and (
                    self.prev_al - self.a_lo >= cfg.mintick
                    if self.pos == 1
                    else self.a_hi - self.prev_ah >= cfg.mintick
                )
            ):
                # D14 entry-hour ruling (2026-08-16, TVB-26 audit F3, user-
                # ruled literal-inclusive): the ENTRY hour counts. An entry
                # on the hour-completing bar of an hour whose range broke the
                # prior opposite extreme exits at that same bar's close --
                # matching how mid-hour entries already behave and the i3
                # degenerate convention. Ordered after i3 (race steps 1 vs 8).
                self.exit_counters["state_degenerate"] += 1
                frac = (
                    {"frac": 1.0, "tranche": "all"}
                    if (self.tranches is not None or self.runner_frac is not None)
                    else {}
                )
                close_out(
                    "long" if self.pos == 1 else "short",
                    "state",
                    c,
                    state_degenerate=True,
                    **frac,
                )
        return events

    def _entry_step(self, ts, o, h, l, gate_up, gate_dn, sig, prox_vals, events) -> None:  # noqa: E741
        """Entry from flat (extracted verbatim from the Pine-order race)."""
        cfg = self.cfg
        if cfg.entry_mode == "pattern":
            if sig is not None and (
                (sig.dir == 1 and cfg.allow_long and gate_up)
                or (sig.dir == -1 and cfg.allow_short and gate_dn)
            ):
                self._pattern_entry(ts, o, sig, prox_vals, events)
        elif (
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
            if cfg.stop_mode is not None:
                self._tvb25_freeze_control_entry(events)
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
            if cfg.stop_mode is not None:
                self._tvb25_freeze_control_entry(events)

    def _clear_tvb25_state(self) -> None:
        self.tranches = self.runner_frac = None
        self.floor_armed = self.retrace_done = False
        self.runner_be_px = None
        self.bf_armed = True
        self.arm_rung_level = None
        self.i3_level = self.i3_key = None
        self.stop_px = self.stop_kind = None
        self.t1_px = None

    def _clear_position(self) -> None:
        self.pos, self.entry_px, self.entry_ts = 0, None, None
        self.tgt_px = self.tgt_rung = None
        self.first_retrace_ts = self.first_p3_ts = None
        self._clear_tvb25_state()

    def _tvb25_exit_race(
        self,
        ts,
        o,
        h,
        l,  # noqa: E741
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
        hour_end,
        events,
        close_out,
    ) -> None:
        """TVB-25 ruled exit race (prereg 2026-08-16 amendment).

        Order: i3 -> structural/ATR stop -> protective retrace levels ->
        tranche/target profits (ladder order) -> BF harvest -> brk -> flip
        -> state stop. Risk exits close ALL remaining tranches at their
        trigger (D5). Fill classes: protective levels fill at the level on
        containment, at the bar OPEN on gap-through (D3); profit levels are
        containment-only; close-evaluated exits fill at the 5m close. The
        relative order of tgt/bf/brk/flip matches the incumbent race, so an
        overlay arm minus its overlay is decision-identical to its base.
        D9: bars with >= 2 simultaneously satisfiable exit classes are
        counted into exit_counters, with satisfiability accumulated across
        the ordered within-bar transitions (TVB-26 repair of the bar-start
        snapshot; collision_pairs carries the class-combination breakdown).
        Satisfiable means EXECUTABLE (TVB-28 audit MEDIUM-2, user-ruled
        2026-08-26): a floor with no remaining middle tranches is not a
        satisfiable protective class -- those arming-only transitions are
        counted under exit_counters["floor_armed_inert"] instead.
        """
        cfg = self.cfg
        if self.pos == 0:
            return
        d = self.pos
        direction = "long" if d == 1 else "short"
        sign = 1.0 if d == 1 else -1.0
        tick = cfg.mintick
        # Receipt anchors: exits below may clear the position, so snapshot
        # the entry price and the event high-water mark before the race.
        entry_px0 = self.entry_px
        n_ev_before = len(events)

        def frac_exit(kind, price, frac, tranche=None, line_tf=None, line_n=None, **extra):
            ev = {
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
                "frac": frac,
            }
            if tranche is not None:
                ev["tranche"] = tranche
            ev.update(extra)
            if cfg.retrace_census:
                ev["first_retrace_ts"] = self.first_retrace_ts
                ev["first_p3_ts"] = self.first_p3_ts
            events.append(ev)

        def remaining():
            if self.tranches is None and self.runner_frac is None:
                return None  # whole-position arm
            return sum(t["frac"] for t in (self.tranches or [])) + (self.runner_frac or 0.0)

        def full_exit(kind, price, line_tf=None, line_n=None, **extra):
            rem = remaining()
            if rem is None:
                close_out(direction, kind, price, line_tf, line_n, **extra)
            else:
                frac_exit(kind, price, rem, tranche="all", line_tf=line_tf, line_n=line_n, **extra)
                self._clear_position()

        def maybe_flat():
            if (
                (self.tranches is not None or self.runner_frac is not None)
                and not (self.tranches or [])
                and not (self.runner_frac or 0.0)
            ):
                self._clear_position()

        def fire_retrace(fill):
            for t in list(self.tranches or []):
                frac_exit("floor", fill, t["frac"], tranche=t["label"])
            self.tranches = []
            self.retrace_done = True
            self.runner_be_px = self.entry_px
            maybe_flat()

        # X1 arming update (reach convention, entry bar excluded) BEFORE the
        # race so a rung-reach + BF-touch bar can arm-and-fire (amendment)
        if (
            cfg.bf_arm_rung is not None
            and not self.bf_armed
            and self.arm_rung_level is not None
            and ts > self.entry_ts
            and ((d == 1 and h >= self.arm_rung_level) or (d == -1 and l <= self.arm_rung_level))
        ):
            self.bf_armed = True

        # --- D9 collision census: class satisfiability accumulated across
        # the ordered within-bar state transitions (TVB-25 audit F1: a
        # bar-start snapshot cannot see classes the bar itself arms -- the
        # P2 bank->floor and retrace->breakeven chains -- and the amendment
        # pins that D9 counts those bars). The snapshot seeds the set; the
        # arm-and-fire blocks below add "prot" when their live conditions
        # hold; the bar counts once at the end of the race.
        i3_hit = (
            cfg.intrabar3_exit
            and self.i3_level is not None
            and self.pattern is not None
            and self.pattern.key == self.i3_key
            and (self.i3_level - l >= tick if d == 1 else h - self.i3_level >= tick)
        )
        stop_hit = self.stop_px is not None and (l <= self.stop_px if d == 1 else h >= self.stop_px)
        prot_hit = False
        prot_lvl = None
        # D9 executable-only (TVB-28 audit MEDIUM-2, user-ruled 2026-08-26):
        # the floor is a satisfiable protective class only while middle
        # tranches remain for it to exit -- an armed floor with an empty
        # ladder is a state transition, not an exit that can fire.
        if self.floor_armed and not self.retrace_done and self.t1_px is not None and self.tranches:
            prot_hit = l <= self.t1_px if d == 1 else h >= self.t1_px
            if prot_hit:
                prot_lvl = self.t1_px
        if not prot_hit and self.runner_be_px is not None and (self.runner_frac or 0.0) > 0:
            prot_hit = l <= self.runner_be_px if d == 1 else h >= self.runner_be_px
            if prot_hit:
                prot_lvl = self.runner_be_px
        tgt_lvl = None
        if self.tranches:
            tgt_lvl = next((t["level"] for t in self.tranches if l <= t["level"] <= h), None)
            tgt_hit = tgt_lvl is not None
        else:
            tgt_hit = (
                cfg.exit_targets is not None and self.tgt_px is not None and l <= self.tgt_px <= h
            )
            if tgt_hit:
                tgt_lvl = self.tgt_px
        bf_cand, bf_tf = (xl, xl_tf) if d == 1 else (xs, xs_tf)
        bf_hit = (
            cfg.bf_harvest_exit
            and self.bf_armed
            and bf_cand is not None
            and (self.runner_frac is None or self.runner_frac > 0)
        )
        brk_cand, brk_tf = (brk_lo, brk_lo_tf) if d == 1 else (brk_up, brk_up_tf)
        brk_hit = cfg.brk_exit and brk_cand is not None
        flip_hit = cfg.flip_backstop and (gate_dn if d == 1 else gate_up)
        state_hit = bool(
            cfg.state_stop
            and hour_end
            and self.prev_ah is not None
            and (self.prev_al - self.a_lo >= tick if d == 1 else self.a_hi - self.prev_ah >= tick)
        )
        collide = {
            name
            for name, hit in (
                ("i3", i3_hit),
                ("stop", stop_hit),
                ("prot", prot_hit),
                ("tgt", tgt_hit),
                ("bf", bf_hit),
                ("brk", brk_hit),
                ("flip", flip_hit),
                ("state", state_hit),
            )
            if hit
        }
        # Candidate fills per satisfiable class, under the ruled fill rules
        # (protective: level, open on gap-through; profit: containment level;
        # close-evaluated: this bar's close). Feeds the collision receipt.
        cand_fill: dict = {}
        if i3_hit:
            cand_fill["i3"] = c
        if stop_hit:
            cand_fill["stop"] = (
                o if (h < self.stop_px if d == 1 else l > self.stop_px) else self.stop_px
            )
        if prot_hit:
            cand_fill["prot"] = o if (h < prot_lvl if d == 1 else l > prot_lvl) else prot_lvl
        if tgt_hit:
            cand_fill["tgt"] = tgt_lvl
        if bf_hit:
            cand_fill["bf"] = bf_cand[0]
        if brk_hit:
            cand_fill["brk"] = c
        if flip_hit:
            cand_fill["flip"] = c
        if state_hit:
            cand_fill["state"] = c

        # 1) intrabar-3 invalidation (before the stop, skill 5.4)
        if self.pos != 0 and i3_hit:
            full_exit("i3", c)
        # 2) structural/ATR stop -- protective fill class (D3)
        if self.pos != 0 and stop_hit:
            gap = h < self.stop_px if d == 1 else l > self.stop_px
            full_exit("stop", o if gap else self.stop_px, stop_kind=self.stop_kind)
        # 3) protective retrace levels armed at bar start (P2)
        if (
            self.pos != 0
            and self.floor_armed
            and not self.retrace_done
            and self.t1_px is not None
            and (l <= self.t1_px if d == 1 else h >= self.t1_px)
        ):
            gap = h < self.t1_px if d == 1 else l > self.t1_px
            fire_retrace(o if gap else self.t1_px)
        if (
            self.pos != 0
            and self.runner_be_px is not None
            and (self.runner_frac or 0.0) > 0
            and (l <= self.runner_be_px if d == 1 else h >= self.runner_be_px)
        ):
            gap = h < self.runner_be_px if d == 1 else l > self.runner_be_px
            frac_exit("be", o if gap else self.runner_be_px, self.runner_frac, tranche="runner")
            self.runner_frac = 0.0
            maybe_flat()
        # 4) profit targets, ladder order (containment-only fills); the P2
        #    floor arms on the FIRST executed bank
        newly_armed = False
        if self.pos != 0 and self.tranches:
            for t in list(self.tranches):
                if l <= t["level"] <= h:
                    frac_exit("tgt", t["level"], t["frac"], tranche=t["label"])
                    self.tranches.remove(t)
                    if cfg.tranche_profile == "P2" and not self.floor_armed:
                        self.floor_armed = True
                        newly_armed = True
            maybe_flat()
        elif (
            self.pos != 0
            and cfg.exit_targets is not None
            and self.tgt_px is not None
            and l <= self.tgt_px <= h
        ):
            close_out(direction, "tgt", self.tgt_px, None, self.tgt_rung)
        # 4b) amendment arm-and-fire: a bar that banked the first tranche AND
        #     contains T1 fires the just-armed retrace on the SAME bar; a
        #     contained breakeven touch exits the runner on that bar too
        if (
            self.pos != 0
            and newly_armed
            and not self.retrace_done
            and self.t1_px is not None
            and l <= self.t1_px <= h
        ):
            if self.tranches:
                # D9: the bank armed the floor on this bar and middle
                # tranches remain -- an executable collision
                collide.add("prot")
                cand_fill.setdefault("prot", self.t1_px)
            else:
                # Executable-only ruling (2026-08-26): the banks consumed
                # every tranche before the floor armed -- nothing left for
                # the floor to exit. Counted separately, NOT a collision
                # (the runner-breakeven block below still adds "prot" if
                # the breakeven is contained, because that one can fire).
                self.exit_counters["floor_armed_inert"] += 1
            fire_retrace(self.t1_px)
        if (
            self.pos != 0
            and self.runner_be_px is not None
            and (self.runner_frac or 0.0) > 0
            and l <= self.runner_be_px <= h
        ):
            collide.add("prot")  # D9: the retrace armed the breakeven mid-bar
            cand_fill.setdefault("prot", self.runner_be_px)
            frac_exit("be", self.runner_be_px, self.runner_frac, tranche="runner")
            self.runner_frac = 0.0
            maybe_flat()
        # 5) BF harvest touch (runner-scoped on tranche arms; X1 arming gate)
        if self.pos != 0 and bf_hit:
            if self.tranches is None and self.runner_frac is None:
                close_out(direction, "bf", bf_cand[0], bf_tf, bf_cand[1])
            elif (self.runner_frac or 0.0) > 0:
                frac_exit(
                    "bf",
                    bf_cand[0],
                    self.runner_frac,
                    tranche="runner",
                    line_tf=bf_tf,
                    line_n=bf_cand[1],
                )
                self.runner_frac = 0.0
                maybe_flat()
        # 6) brk -- full-position risk exit (D5)
        if self.pos != 0 and brk_hit:
            full_exit("brk", c, line_tf=brk_tf)
        # 7) flip backstop
        if self.pos != 0 and flip_hit:
            full_exit("flip", c)
        # 8) state stop (close-evaluated on the hour-completing bar, D14)
        if self.pos != 0 and state_hit:
            full_exit("state", c)
        # D9: one count per bar with >= 2 satisfiable classes, over the
        # transition-accumulated set
        if len(collide) >= 2:
            self.exit_counters["collision_bars"] += 1
            key = "+".join(sorted(collide))
            self.collision_pairs[key] = self.collision_pairs.get(key, 0) + 1
            # Collision receipt (first-fill diagnostic, ruled 2026-08-26):
            # candidate fill + pnl per satisfiable class, the full executed
            # fill path, and each class's signed delta vs the FIRST executed
            # fill (positive = that class's single fill beats the first
            # executed price). Exact for one-fill races; on multi-fill
            # tranche bars it is NOT a both-ways path pricing.
            fired = [
                {"kind": e["kind"], "price": e["price"], "frac": e.get("frac")}
                for e in events[n_ev_before:]
                if e.get("action") == "exit"
            ]
            exec_px = fired[0]["price"] if fired else None
            self.collision_receipts.append(
                {
                    "ts": ts,
                    "sym": cfg.symbol,
                    "classes": sorted(collide),
                    "candidates": {
                        k: {
                            "px": px,
                            "pnl_pct": round(sign * (px - entry_px0) / entry_px0 * 100.0, 6),
                        }
                        for k, px in cand_fill.items()
                    },
                    "executed": fired,
                    "delta_vs_first_fill_pct": (
                        {
                            k: round(sign * (px - exec_px) / entry_px0 * 100.0, 6)
                            for k, px in cand_fill.items()
                        }
                        if exec_px is not None
                        else None
                    ),
                }
            )

    def _pattern_entry(self, ts: int, o: float, sig, prox_vals, events: list) -> None:
        """TVB-21 pattern-arm entry: vetoes, then fill (pre-reg mechanics).

        Fill = max(trigger + tick, bar open) for longs (min/- for shorts):
        late-in-bar entries (signal persisting after a gate/veto cleared)
        fill at the available price, a declared CONSERVATIVE bias vs the
        controls' level fills. Gate/direction filtering happened at the call
        site; this method owns vetoes, target freezing, and the event.
        """
        cfg = self.cfg
        vc = self.veto_counts
        vc["candidates"] += 1
        fill = max(sig.trig + cfg.mintick, o) if sig.dir == 1 else min(sig.trig - cfg.mintick, o)
        # TVB-22 amendment (audit F2, user-ruled): both vetoes are evaluated
        # for EVERY candidate BEFORE the structural no-target skip, so
        # veto-rate denominators cover all candidates; no_target_vetoed logs
        # the overlap (entries = candidates - (vetoed + no_target -
        # no_target_vetoed)). Entry behavior is unchanged.
        veto_prox = False
        if cfg.bf_prox_veto_pct is not None and prox_vals:
            lim = cfg.bf_prox_veto_pct / 100.0
            if sig.dir == 1:
                above = [v for v in prox_vals if v > fill]
                veto_prox = bool(above) and (min(above) - fill) / fill <= lim
            else:
                below = [v for v in prox_vals if v < fill]
                veto_prox = bool(below) and (fill - max(below)) / fill <= lim
        elif cfg.bf_prox_veto_atr is not None and prox_vals:
            # TVB-23 ATR variant (prereg ruling 4): limit in PRICE units,
            # k x ATR as of the last completed signal-TF bar. ATR is always
            # formed in-window (250-bar seed); a None value vetoes nothing.
            a = self.atr.value if self.atr is not None else None
            if a is not None:
                lim = cfg.bf_prox_veto_atr * a
                if sig.dir == 1:
                    above = [v for v in prox_vals if v > fill]
                    veto_prox = bool(above) and min(above) - fill <= lim
                else:
                    below = [v for v in prox_vals if v < fill]
                    veto_prox = bool(below) and fill - max(below) <= lim
        veto_chop = False
        if cfg.chop_veto_pct is not None:
            lim = cfg.chop_veto_pct / 100.0
            veto_chop = any(
                v is not None and abs(fill - v) / fill <= lim for v in self.gate_open.values()
            )
        elif cfg.chop_veto_atr is not None:
            a = self.atr.value if self.atr is not None else None
            if a is not None:
                lim = cfg.chop_veto_atr * a
                veto_chop = any(
                    v is not None and abs(fill - v) <= lim for v in self.gate_open.values()
                )
        if veto_prox or veto_chop:
            vc["both" if (veto_prox and veto_chop) else "bf_prox" if veto_prox else "chop"] += 1
        # TVB-23 T1-floor veto (prereg ruling 1): directional distance from
        # the prospective fill to the frozen T1 (ladder[0]); d <= 0 is the
        # born-beyond class, 0 < d < floor the tiny class. Evaluated for
        # every candidate with a non-empty snapshot ladder, before the
        # no-target skip.
        veto_floor = False
        if cfg.t1_floor_pct is not None and sig.ladder:
            t1 = sig.ladder[0]
            d = (t1 - fill) / fill if sig.dir == 1 else (fill - t1) / fill
            veto_floor = d < cfg.t1_floor_pct / 100.0
            if veto_floor:
                vc["t1_floor"] += 1
                vc["t1_floor_le0" if d <= 0 else "t1_floor_small"] += 1
                if not (veto_prox or veto_chop):
                    vc["t1_floor_only"] += 1
        if (
            cfg.exit_targets is not None
            or cfg.t1_floor_pct is not None
            or cfg.tranche_profile is not None
        ) and not sig.ladder:
            # A package arm cannot satisfy its exit semantics with no target
            # in the entry snapshot -- and a floor arm has no Target 1 to
            # measure (TVB-23: uniform structural skip across all floor
            # arms, incl. C1-exit ones): structural skip, logged separately.
            vc["no_target"] += 1
            if veto_prox or veto_chop:
                vc["no_target_vetoed"] += 1
            return
        if veto_prox or veto_chop or veto_floor:
            return
        vc["entries"] += 1
        rung = None
        if cfg.exit_targets is not None:
            idx = min(cfg.exit_targets, len(sig.ladder)) - 1
            self.tgt_px, self.tgt_rung = sig.ladder[idx], idx + 1
            rung = self.tgt_rung
        self.pos, self.entry_px, self.entry_ts = sig.dir, fill, ts
        self.first_retrace_ts = self.first_p3_ts = None
        events.append(
            {
                "ts": ts,
                "sym": cfg.symbol,
                "action": "enter",
                "dir": "long" if sig.dir == 1 else "short",
                "price": fill,
                "trig": sig.trig,
                "pattern": sig.name,
                "rev": sig.rev,
                "star": sig.star,
                "boom": sig.boom,
                "pmg": sig.pmg,
                "ladder": list(sig.ladder),
                "tgt_rung": rung,
            }
        )
        if (
            cfg.stop_mode is not None
            or cfg.intrabar3_exit
            or cfg.tranche_profile is not None
            or cfg.bf_arm_rung is not None
        ):
            # TVB-25 entry-time state freezing (amendment 2026-08-16);
            # unreachable on pre-existing arms (all new fields inert)
            self._tvb25_freeze_pattern_entry(sig, fill, events)

    def _tvb25_freeze_pattern_entry(self, sig, fill: float, events: list) -> None:
        """Freeze the TVB-25 exit state at a pattern entry (amendment).

        Structural stops use the identity-frozen first-detection anchor
        (replay_bar maintains _anchor_freeze); a degenerate anchor -- None,
        non-finite, equal to the fill, or on the profit side -- falls back
        to the ATR stop (D2), counted. i3 freezes the prior completed
        signal-TF bar's opposite extreme (the Type-3 completion level).
        Tranche plans follow the amendment's fold-to-runner rule.
        """
        cfg = self.cfg
        d = sig.dir
        ev = events[-1]
        if cfg.stop_mode is not None:
            anchor = src = src_ts = None
            if cfg.stop_mode == "structural":
                ident = (self.pattern.key, sig.dir, sig.name)
                anchor, src, src_ts = self._anchor_freeze.get(
                    ident, (sig.stop_anchor, sig.stop_src, sig.stop_src_ts)
                )
            degenerate = (
                anchor is None
                or not math.isfinite(anchor)
                or (anchor >= fill if d == 1 else anchor <= fill)
            )
            if cfg.stop_mode == "structural" and anchor is not None and degenerate:
                self.exit_counters["stop_degenerate_anchor"] += 1
            if cfg.stop_mode == "structural" and not degenerate:
                self.stop_px, self.stop_kind = anchor, "structural"
                ev["stop_src"] = src
                ev["stop_src_ts"] = src_ts
            else:
                a = self.atr.value if self.atr is not None else None
                if a is None:
                    # D2: no stop until the ATR window fills (counted)
                    self.exit_counters["stop_atr_unavailable"] += 1
                    self.stop_px = self.stop_kind = None
                else:
                    self.stop_px = (
                        fill - cfg.stop_atr_mult * a if d == 1 else fill + cfg.stop_atr_mult * a
                    )
                    self.stop_kind = "atr"
            ev["stop_px"], ev["stop_kind"] = self.stop_px, self.stop_kind
        if cfg.intrabar3_exit:
            arr = self.pattern.arr_l if d == 1 else self.pattern.arr_h
            self.i3_level = arr[-1] if arr else None
            self.i3_key = self.pattern.key
            ev["i3_level"] = self.i3_level
        if cfg.tranche_profile == "P1":
            # P1 two-piece: 50% at frozen T1, 50% runner to the BF touch
            self.tranches = [{"frac": 0.5, "level": sig.ladder[0], "label": "T1"}]
            self.runner_frac = 0.5
        elif cfg.tranche_profile == "P2":
            # P2 runner profile: skip T1; bank 40/20/20/10 at T2-T5; missing
            # rungs FOLD INTO THE RUNNER (amendment); 10% base runner; the
            # floor arms on the first executed bank (T1 retrace machinery)
            fracs = ((1, 0.40), (2, 0.20), (3, 0.20), (4, 0.10))
            self.tranches = [
                {"frac": f, "level": sig.ladder[i], "label": f"T{i + 1}"}
                for i, f in fracs
                if i < len(sig.ladder)
            ]
            self.runner_frac = 0.10 + sum(f for i, f in fracs if i >= len(sig.ladder))
            self.t1_px = sig.ladder[0]
        if cfg.tranche_profile is not None:
            ev["tranches"] = [dict(t) for t in self.tranches] + [
                {"frac": self.runner_frac, "label": "runner"}
            ]
        if cfg.bf_arm_rung is not None:
            self.bf_armed = False
            idx = cfg.bf_arm_rung - 1
            self.arm_rung_level = sig.ladder[idx] if len(sig.ladder) > idx else None
            ev["bf_arm_level"] = self.arm_rung_level

    def _tvb25_freeze_control_entry(self, events: list) -> None:
        """ATR stop for a control entry (prereg stop table: controls -> D2)."""
        cfg = self.cfg
        ev = events[-1]
        a = self.atr.value if self.atr is not None else None
        if a is None:
            self.exit_counters["stop_atr_unavailable"] += 1
            self.stop_px = self.stop_kind = None
        else:
            self.stop_px = (
                self.entry_px - cfg.stop_atr_mult * a
                if self.pos == 1
                else self.entry_px + cfg.stop_atr_mult * a
            )
            self.stop_kind = "atr"
        ev["stop_px"], ev["stop_kind"] = self.stop_px, self.stop_kind

    def replay_bar(self, ts: int, o: float, h: float, l: float, c: float, bar_s: int = 300):
        """Phase B: one closed chart bar through the full v6 pass."""
        # gate opens (f_open :112-117), then gate state on this bar's close
        for name, kf in GATE_TFS:
            k = kf(ts)
            if k != self.gate_key[name]:
                first_bar_of_feed = self.gate_key[name] is None
                self.gate_key[name] = k
                if not (first_bar_of_feed and self.cfg.pine_gate_warmup):
                    self.gate_open[name] = o
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
        # TVB-21 pattern layer: detection on the developing signal-TF bar; the
        # BF-prox veto reads the BAR-OPEN alive set, so collect it before the
        # pools process this bar's lifecycle transitions.
        sig = self.pattern.update(ts, o, h, l, c) if self.pattern is not None else None
        if self.atr is not None:
            self.atr.update(ts, h, l, c)
        if self.cfg.stop_mode == "structural" and self.pattern is not None:
            # TVB-25 amendment: freeze the stop anchor at the FIRST detection
            # of each signal identity; identities die with the signal-TF bar.
            # Closed-bar anchors must never drift across re-detections
            # (asserted); the 1-3 rows anchor the DEVELOPING bar and keep
            # their first-detection snapshot by construction.
            if self._anchor_freeze_key != self.pattern.key:
                self._anchor_freeze_key = self.pattern.key
                self._anchor_freeze.clear()
            if sig is not None:
                ident = (self.pattern.key, sig.dir, sig.name)
                held = self._anchor_freeze.get(ident)
                if held is None:
                    self._anchor_freeze[ident] = (sig.stop_anchor, sig.stop_src, sig.stop_src_ts)
                elif held[1] != "developing" and (
                    held[0] != sig.stop_anchor or held[2] != sig.stop_src_ts
                ):
                    raise AssertionError(
                        f"stop anchor drift for {ident}: {held[0]}@{held[2]} -> "
                        f"{sig.stop_anchor}@{sig.stop_src_ts}"
                    )
        # TVB-23 read-only retracement census (prereg ruling 5): evaluated
        # on the bar-start position BEFORE the position step, so the entry
        # bar is structurally excluded (no position stands yet) and the
        # exit bar is included. Writes nothing the position machine reads.
        if self.cfg.retrace_census and self.pos != 0 and self.pattern is not None:
            fl = self.pattern.health_flags()
            if fl is not None:
                if self.pos == 1:
                    retr = fl["in0"] and fl["r0"]
                    p3 = fl["d0"] or (fl["u0"] and fl["r0"])
                else:
                    retr = fl["in0"] and fl["g0"]
                    p3 = fl["u0"] or (fl["d0"] and fl["g0"])
                if retr and self.first_retrace_ts is None:
                    self.first_retrace_ts = ts
                if p3 and self.first_p3_ts is None:
                    self.first_p3_ts = ts
        prox_vals = None
        if (
            sig is not None
            and self.pos == 0
            and (self.cfg.bf_prox_veto_pct is not None or self.cfg.bf_prox_veto_atr is not None)
        ):
            prox_vals = self._alive_harvest_vals(ts, sig.dir)
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
            o=o,
            sig=sig,
            prox_vals=prox_vals,
            hour_end=(ts + bar_s) % self.cfg.arm_tf_s == 0,
        )
        # roll the arm snapshot LAST (corrected clock, :475-478)
        if (ts + bar_s) % self.cfg.arm_tf_s == 0:
            self.prev_ah, self.prev_al = self.a_hi, self.a_lo
        return events
