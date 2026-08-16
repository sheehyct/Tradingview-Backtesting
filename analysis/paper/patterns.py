"""Pine-exact port of the Magnitude+Targets detection layer (TVB-21).

Source of truth: pine/strat_magnitude_targets_plus.pine lines 135-587 (the
logic-identical fork of the partner-authored original), ported for the Tier B
pattern arms per docs/experiments/tvb21_tier_b_prereg.md. This module covers
TIMEFRAME AGGREGATION -> CLASSIFY -> PMG -> SIGNAL DETECTION -> LADDER; the
pine's REMEMBER/CHOP/status sections are display-layer and are deliberately
NOT ported (the Tier B chop veto is the flip-level rule in the engine, not
the pine's reversal counter).

Fidelity notes (all pinned in the pre-reg):
- Break flags keep the pine's subtraction form (``curH - H1 >= thr``), its
  warm-up guards, and its thresholds verbatim; thr = mintick.
- Detection is LIVE on the developing signal-TF bar: flags are monotone
  within the bar (curH ratchets up, curL down); color (g0/r0) and therefore
  the signal can flicker until the bar closes -- by design.
- DOCUMENTED divergences vs the strat-methodology skill (user-ruled
  pine-exact, 2026-08-08): 1-3 triggers at the inside bar's completion side
  (skill R22 prefers the reclaim); 1-3-2 hammer close is label/flag only
  (skill R17 requires it); entries are color-gated (the skill triggers on
  the raw break).
- Completed-bar history is capped at 250 signal-TF bars, like the pine; the
  ladder cannot reach further back.

The detector consumes chart bars (the twin's 5m stream) via update() and
returns the live signal for the CURRENT developing signal-TF bar, or None.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Setup keys (stable snake ids) -> the pine's toggle inputs.
SETUP_KEYS = (
    "gap",  # enGap      Gap-Up Sell / Gap-Down Buy
    "t1312",  # en1_3_1_2  1-3-1-2 Contract-Expand-Contract-Expand
    "randy",  # enRandy    Randy Jackson (1-2-2-2)
    "rev132",  # en1_3_2    2-Bar Rev-Strat (1-3-2, hammer/shooter label)
    "t32",  # en3_2      3-2 (Boom flagged on hammer/shooter)
    "shotgun",  # enShotgun  Shot-Gun (2-2-2)
    "t322",  # en3_2_2    3-2-2
    "t312",  # en3_1_2    3-1-2 Chicago (reversal / continuation)
    "rev212",  # en2_1_2rev 2-1-2 Reversal
    "momo212",  # en2_1_2momo 2-1-2 Momentum (continuation)
    "rev13",  # en1_3      1-Bar Rev-Strat (1-3u / 1-3d)
    "rev122",  # en2Bar     2-Bar Rev-Strat (1-2-2)
    "bare22",  # en2_2      2-2 Reversal (bare)
    "insidebo",  # enInsideBO Inside-Bar Breakout (1-2 continuation)
    "out3",  # enOut3     Outside-Bar Continuation
    "going3",  # enGoing3   Going-3 single / potential 1-bar Rev-Strat
)

# The user's a-priori live dictionary (pre-reg ruling 2): 10 setups ON.
USER_DICTIONARY = frozenset(
    (
        "rev122",
        "bare22",
        "rev13",
        "rev132",
        "t32",
        "t322",
        "t312",
        "rev212",
        "momo212",
        "t1312",
    )
)


@dataclass
class PatternConfig:
    mintick: float
    tf_s: int = 3600  # signal timeframe (pre-reg: 1H only)
    ext_targets: int = 5  # pine extTargets default; maxLevels = +1
    pmg_bars: int = 5  # pine pmgBars default
    pmg_flag: bool = True  # enPMG (prefix/flag only, never a gate)
    enabled: frozenset = USER_DICTIONARY


@dataclass
class Signal:
    dir: int  # +1 long / -1 short
    trig: float  # the in-force / entry level
    name: str  # pine zipcode (nameS), PMG+ prefixed if hit
    rev: bool  # isRev
    star: bool  # pizazz (high-priority trigger styling)
    weak: bool  # weakSig (going-3 family)
    fragile: bool  # gap family
    boom: bool  # 3-2 whose outside bar passes the shape rule
    pmg: bool  # reversal fired into a matching PMG run
    ladder: list = field(default_factory=list)  # T1 first, strictly monotone
    # TVB-25 structural stop layer (prereg table + 2026-08-16 amendment).
    # Computed per detection from the skill 5.2 anchors; the ENGINE freezes
    # the first-detection value per identity. None -> ATR fallback (D2).
    stop_anchor: float | None = None
    stop_src: str | None = None  # "closed[-1]" | "closed[-2]" | "developing"


def _is_hammer(o: float, h: float, l: float, c: float) -> bool:  # noqa: E741
    return h - l > 0 and min(o, c) - l >= 0.5 * (h - l) and abs(c - o) <= 0.4 * (h - l)


def _is_shooter(o: float, h: float, l: float, c: float) -> bool:  # noqa: E741
    return h - l > 0 and h - max(o, c) >= 0.5 * (h - l) and abs(c - o) <= 0.4 * (h - l)


class PatternDetector:
    """Local signal-TF aggregation + the pine detection chain."""

    HISTORY_CAP = 250  # pine: completed signal-TF bars retained

    def __init__(self, cfg: PatternConfig):
        self.cfg = cfg
        self.arr_h: list[float] = []
        self.arr_l: list[float] = []
        self.arr_o: list[float] = []
        self.arr_c: list[float] = []
        self.key: int | None = None
        self.cur_o = self.cur_h = self.cur_l = self.cur_c = None

    def seed_history(self, bars) -> None:
        """Warm the completed-bar history from archived signal-TF bars.

        bars: iterable of (ts, o, h, l, c) COMPLETED signal-TF bars, oldest
        first, all strictly before the replay window. No developing bar is
        seeded; the first update() starts one fresh (pine cold-start shape).
        """
        for r in bars:
            self.arr_o.append(r[1])
            self.arr_h.append(r[2])
            self.arr_l.append(r[3])
            self.arr_c.append(r[4])
        excess = len(self.arr_h) - self.HISTORY_CAP
        if excess > 0:
            del self.arr_o[:excess]
            del self.arr_h[:excess]
            del self.arr_l[:excess]
            del self.arr_c[:excess]

    def update(self, ts: int, o: float, h: float, l: float, c: float):  # noqa: E741
        """Feed one chart bar (the twin's 5m bar); return Signal or None."""
        k = ts - ts % self.cfg.tf_s
        if self.key is None or k != self.key:
            if self.key is not None and self.cur_h is not None:
                self.arr_o.append(self.cur_o)
                self.arr_h.append(self.cur_h)
                self.arr_l.append(self.cur_l)
                self.arr_c.append(self.cur_c)
                if len(self.arr_h) > self.HISTORY_CAP:
                    del self.arr_o[0]
                    del self.arr_h[0]
                    del self.arr_l[0]
                    del self.arr_c[0]
            self.key = k
            self.cur_o, self.cur_h, self.cur_l, self.cur_c = o, h, l, c
        else:
            self.cur_h = max(self.cur_h, h)
            self.cur_l = min(self.cur_l, l)
            self.cur_c = c
        return self._detect()

    def health_flags(self) -> dict | None:
        """Developing-bar flags for the M+T position-health predicates.

        TVB-23 retracement census (read-only; detection never consults
        this). Pine-exact reads of the status inputs (pine :192-206,
        :694-716): one-sided break flags of the developing signal-TF bar
        vs the last completed bar, plus live color. Note the as-built
        edge (prereg correction 2026-08-10): d0/u0 are ONE-SIDED, so a
        bar that has broken both sides (out0) sets neither.
        """
        n = len(self.arr_h)
        if n < 1 or self.cur_h is None:
            return None
        thr = self.cfg.mintick
        bh0 = self.cur_h - self.arr_h[n - 1] >= thr
        bl0 = self.arr_l[n - 1] - self.cur_l >= thr
        return {
            "in0": not bh0 and not bl0,
            "u0": bh0 and not bl0,
            "d0": bl0 and not bh0,
            "out0": bh0 and bl0,
            "g0": self.cur_c > self.cur_o,
            "r0": self.cur_c < self.cur_o,
        }

    # ------------------------------------------------------------------
    def _detect(self):  # noqa: C901 -- the pine chain is one long else-if
        cfg = self.cfg
        thr = cfg.mintick
        en = cfg.enabled
        arr_h, arr_l, arr_o, arr_c = self.arr_h, self.arr_l, self.arr_o, self.arr_c
        n = len(arr_h)
        cur_h, cur_l, cur_o, cur_c = self.cur_h, self.cur_l, self.cur_o, self.cur_c

        H1 = arr_h[n - 1] if n >= 1 else None
        L1 = arr_l[n - 1] if n >= 1 else None
        H2 = arr_h[n - 2] if n >= 2 else None
        L2 = arr_l[n - 2] if n >= 2 else None
        H3 = arr_h[n - 3] if n >= 3 else None
        L3 = arr_l[n - 3] if n >= 3 else None
        H4 = arr_h[n - 4] if n >= 4 else None
        L4 = arr_l[n - 4] if n >= 4 else None
        O1 = arr_o[n - 1] if n >= 1 else None
        C1 = arr_c[n - 1] if n >= 1 else None
        O2 = arr_o[n - 2] if n >= 2 else None
        C2 = arr_c[n - 2] if n >= 2 else None

        # break/inside flags, pine subtraction form + warm-up guards
        bh0 = H1 is not None and cur_h - H1 >= thr
        bl0 = L1 is not None and L1 - cur_l >= thr
        bh1 = H2 is not None and H1 - H2 >= thr
        bl1 = L2 is not None and L2 - L1 >= thr
        in1 = n >= 2 and not bh1 and not bl1
        u1 = bh1 and not bl1
        d1 = bl1 and not bh1
        out1 = bh1 and bl1
        bh2 = H3 is not None and H2 - H3 >= thr
        bl2 = L3 is not None and L3 - L2 >= thr
        in2 = n >= 3 and not bh2 and not bl2
        u0 = bh0 and not bl0
        d0 = bl0 and not bh0
        in0 = n >= 1 and not bh0 and not bl0  # noqa: F841 -- pine parity, unused here
        out0 = bh0 and bl0
        g0 = cur_c > cur_o
        r0 = cur_c < cur_o
        u2 = bh2 and not bl2
        d2 = bl2 and not bh2
        out2 = bh2 and bl2
        bh3 = H4 is not None and H3 - H4 >= thr
        bl3 = L4 is not None and L4 - L3 >= thr
        in3 = n >= 4 and not bh3 and not bl3
        g2 = C2 is not None and O2 is not None and C2 > O2
        r2 = C2 is not None and O2 is not None and C2 < O2
        ham1 = O1 is not None and _is_hammer(O1, H1, L1, C1)
        sho1 = O1 is not None and _is_shooter(O1, H1, L1, C1)

        # PMG streaks (consecutive lower-highs = bullish, higher-lows = bearish)
        lh_run = 0
        prev_h = cur_h
        for i in range(n - 1, -1, -1):
            hh = arr_h[i]
            if hh > prev_h + thr:
                lh_run += 1
                prev_h = hh
            else:
                break
        hl_run = 0
        prev_l = cur_l
        for i in range(n - 1, -1, -1):
            ll = arr_l[i]
            if ll < prev_l - thr:
                hl_run += 1
                prev_l = ll
            else:
                break
        bull_pmg = cfg.pmg_flag and lh_run >= cfg.pmg_bars
        bear_pmg = cfg.pmg_flag and hl_run >= cfg.pmg_bars
        gap_up = H1 is not None and cur_o > H1 + thr
        gap_dn = L1 is not None and cur_o < L1 - thr

        # signal detection: the pine else-if chain, order preserved
        sig_dir = 0
        trig = None
        anchor = None
        anchor2 = None
        weak = False
        fragile = False
        is_rev = False
        star = False
        boom = False
        name = None

        if "gap" in en and gap_up and r0:
            sig_dir, trig, anchor = -1, cur_o, H1
            is_rev, fragile, name = True, True, "GAP-Sell"
        elif "gap" in en and gap_dn and g0:
            sig_dir, trig, anchor = 1, cur_o, L1
            is_rev, fragile, name = True, True, "GAP-Buy"
        elif "t1312" in en and in3 and out2 and in1 and u0 and g0:
            sig_dir, trig, anchor, is_rev, name = 1, H1, H2, True, "1-3-1-2u"
        elif "t1312" in en and in3 and out2 and in1 and d0 and r0:
            sig_dir, trig, anchor, is_rev, name = -1, L1, L2, True, "1-3-1-2d"
        elif "randy" in en and in3 and u2 and d1 and u0 and g0:
            sig_dir, trig, anchor, is_rev, star, name = 1, H1, H2, True, True, "1-2-2-2u"
        elif "randy" in en and in3 and d2 and u1 and d0 and r0:
            sig_dir, trig, anchor, is_rev, star, name = -1, L1, L2, True, True, "1-2-2-2d"
        elif "rev132" in en and in2 and out1 and u0 and g0:
            sig_dir, trig, anchor, is_rev, star, name = 1, H1, H3, True, True, "1-3-2u"
        elif "rev132" in en and in2 and out1 and d0 and r0:
            sig_dir, trig, anchor, is_rev, star, name = -1, L1, L3, True, True, "1-3-2d"
        elif "t32" in en and out1 and u0 and g0:
            sig_dir, trig, is_rev, name = 1, H1, True, "3-2u"
            star = boom = ham1
        elif "t32" in en and out1 and d0 and r0:
            sig_dir, trig, is_rev, name = -1, L1, True, "3-2d"
            star = boom = sho1
        elif "shotgun" in en and u2 and d1 and u0 and g0:
            sig_dir, trig, anchor, is_rev, star, name = 1, H1, H2, True, True, "2-2-2u"
        elif "shotgun" in en and d2 and u1 and d0 and r0:
            sig_dir, trig, anchor, is_rev, star, name = -1, L1, L2, True, True, "2-2-2d"
        elif "t322" in en and out2 and d1 and u0 and g0:
            sig_dir, trig, anchor, is_rev, name = 1, H1, H2, True, "3-2-2u"
        elif "t322" in en and out2 and u1 and d0 and r0:
            sig_dir, trig, anchor, is_rev, name = -1, L1, L2, True, "3-2-2d"
        elif "t312" in en and out2 and in1 and u0 and g0:
            sig_dir, trig, anchor, is_rev, name = 1, H1, H2, r2, "3-1-2u"
        elif "t312" in en and out2 and in1 and d0 and r0:
            sig_dir, trig, anchor, is_rev, name = -1, L1, L2, g2, "3-1-2d"
        elif "rev212" in en and d2 and in1 and u0 and g0:
            sig_dir, trig, anchor, is_rev, name = 1, H1, H2, True, "2-1-2u"
        elif "rev212" in en and u2 and in1 and d0 and r0:
            sig_dir, trig, anchor, is_rev, name = -1, L1, L2, True, "2-1-2d"
        elif "momo212" in en and u2 and in1 and u0 and g0 and (H1 + L1) / 2 >= (H2 + L2) / 2:
            sig_dir, trig, is_rev, name = 1, H1, False, "2-1-2u"
        elif "momo212" in en and d2 and in1 and d0 and r0 and (H1 + L1) / 2 <= (H2 + L2) / 2:
            sig_dir, trig, is_rev, name = -1, L1, False, "2-1-2d"
        elif "rev13" in en and in1 and out0 and g0:
            sig_dir, trig, anchor, is_rev, star, name = 1, H1, H2, True, True, "1-3u"
        elif "rev13" in en and in1 and out0 and r0:
            sig_dir, trig, anchor, is_rev, star, name = -1, L1, L2, True, True, "1-3d"
        elif "rev122" in en and in2 and d1 and u0 and g0:
            sig_dir, trig, anchor, is_rev, star, name = 1, H1, H2, True, True, "1-2d-2u"
            anchor2 = H3 if H3 is not None and L1 < L3 - thr else None
        elif "rev122" in en and in2 and u1 and d0 and r0:
            sig_dir, trig, anchor, is_rev, star, name = -1, L1, L2, True, True, "1-2u-2d"
            anchor2 = L3 if L3 is not None and H1 > H3 + thr else None
        elif "bare22" in en and d1 and u0 and g0:
            sig_dir, trig, anchor, is_rev, name = 1, H1, H2, True, "2-2u"
        elif "bare22" in en and u1 and d0 and r0:
            sig_dir, trig, anchor, is_rev, name = -1, L1, L2, True, "2-2d"
        elif "insidebo" in en and in1 and u0 and g0:
            sig_dir, trig, anchor, is_rev, name = 1, H1, H2, False, "1-2u"
        elif "insidebo" in en and in1 and d0 and r0:
            sig_dir, trig, anchor, is_rev, name = -1, L1, L2, False, "1-2d"
        elif "out3" in en and out0 and g0:
            sig_dir, trig, is_rev, name = 1, H1, False, "x-3u"
        elif "out3" in en and out0 and r0:
            sig_dir, trig, is_rev, name = -1, L1, False, "x-3d"
        elif "going3" in en and u0 and r0:
            sig_dir, trig, anchor, weak, is_rev = -1, H1, L1, True, True
            name = "1-2u(r)" if in1 else "2u>3"
        elif "going3" in en and d0 and g0:
            sig_dir, trig, anchor, weak, is_rev = 1, L1, H1, True, True
            name = "1-2d(g)" if in1 else "2d>3"

        if sig_dir == 0:
            return None

        # TVB-25 structural stop anchor (prereg per-setup table; 2026-08-16
        # amendment). Keyed on the base zipcode BEFORE the PMG+ prefix. The
        # 1-3 rows anchor on the DEVELOPING bar's own extreme (the 3 itself)
        # -- the prereg's declared "chosen experimental anchor"; the engine
        # freezes the first-detection value. Setups outside the table get
        # None (ATR fallback, D2).
        stop_map = (
            {
                "1-2d-2u": (L1, "closed[-1]"),
                "2-2u": (L1, "closed[-1]"),
                "1-3u": (cur_l, "developing"),
                "1-3-2u": (L1, "closed[-1]"),
                "3-2u": (L1, "closed[-1]"),
                "3-2-2u": (L2, "closed[-2]"),
                "3-1-2u": (L2, "closed[-2]"),
                "2-1-2u": (L2, "closed[-2]"),
                "1-3-1-2u": (L2, "closed[-2]"),
            }
            if sig_dir == 1
            else {
                "1-2u-2d": (H1, "closed[-1]"),
                "2-2d": (H1, "closed[-1]"),
                "1-3d": (cur_h, "developing"),
                "1-3-2d": (H1, "closed[-1]"),
                "3-2d": (H1, "closed[-1]"),
                "3-2-2d": (H2, "closed[-2]"),
                "3-1-2d": (H2, "closed[-2]"),
                "2-1-2d": (H2, "closed[-2]"),
                "1-3-1-2d": (H2, "closed[-2]"),
            }
        )
        stop_anchor = stop_src = None
        hit = stop_map.get(name)
        if hit is not None and hit[0] is not None:
            stop_anchor, stop_src = hit

        pmg_hit = is_rev and (sig_dir == 1 and bull_pmg or sig_dir == -1 and bear_pmg)
        if pmg_hit:
            name = "PMG+" + name

        # ladder: anchors first, then prior extremes not yet taken out
        max_levels = cfg.ext_targets + 1
        ladder: list[float] = []
        if anchor is not None:
            ladder.append(anchor)
        if anchor2 is not None:
            ladder.append(anchor2)
        if sig_dir == 1:
            run_max = (
                anchor2
                if anchor2 is not None
                else anchor
                if anchor is not None
                else trig
                if (trig is not None and not weak)
                else cur_h
            )
            for j in range(n - 1, -1, -1):
                if len(ladder) >= max_levels:
                    break
                hv = arr_h[j]
                if hv > run_max + thr:
                    ladder.append(hv)
                    run_max = hv
        else:
            run_min = (
                anchor2
                if anchor2 is not None
                else anchor
                if anchor is not None
                else trig
                if (trig is not None and not weak)
                else cur_l
            )
            for j in range(n - 1, -1, -1):
                if len(ladder) >= max_levels:
                    break
                lv = arr_l[j]
                if lv < run_min - thr:
                    ladder.append(lv)
                    run_min = lv

        return Signal(
            dir=sig_dir,
            trig=trig,
            name=name,
            rev=is_rev,
            star=star,
            weak=weak,
            fragile=fragile,
            boom=boom,
            pmg=pmg_hit,
            ladder=ladder,
            stop_anchor=stop_anchor,
            stop_src=stop_src,
        )
