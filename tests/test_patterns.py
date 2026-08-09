"""TVB-21 pattern-layer fixture tests (pine-exact port of the M+T detector).

Vectors combine the strat-methodology skill's section-7 style cases with
pine-derived behaviors that the pre-registration pins: the 1-2-2 conditional
anchor2, the 3-1-2 color router, the 2-1-2 momentum midpoint gate, precedence
rerouting when toggles are off, the 3-2 Boom shape flag, live intrabar
monotone updates on the developing signal-TF bar, and the as-built PMG quirk
(the developing bar's own break resets the streak walk, so PMG+ is
unreachable for the user's 10-setup dictionary -- documented, not "fixed").
"""

from analysis.paper.patterns import (
    USER_DICTIONARY,
    PatternConfig,
    PatternDetector,
)

MT = 0.01  # mintick
HOUR = 3600


def _det(enabled=None, **kw):
    cfg = PatternConfig(mintick=MT, tf_s=HOUR, enabled=enabled or USER_DICTIONARY, **kw)
    return PatternDetector(cfg)


def _feed(det, bars):
    """Feed one update per hour; each bar = (o, h, l, c). Returns last result."""
    out = None
    for i, (o, h, l, c) in enumerate(bars):  # noqa: E741
        out = det.update(i * HOUR, o, h, l, c)
    return out


def test_equal_boundary_never_breaks():
    det = _det()
    # prev H105/L98; developing equal high + inside low -> Type 1, no signal
    assert _feed(det, [(100, 105, 98, 104), (104, 105, 99, 104.5)]) is None
    # sub-tick poke (0.005 < mintick) still no break
    det2 = _det()
    assert _feed(det2, [(100, 105, 98, 104), (104, 105.005, 99, 104.5)]) is None


def test_warmup_guards_no_spurious_signals():
    det = _det()
    assert det.update(0, 100, 101, 99, 100.5) is None  # n=0: nothing to break
    # n=1: a clean 2u green exists but no enabled setup matches yet
    assert det.update(HOUR, 100.5, 102, 100, 101.5) is None


def test_212_reversal_bull():
    det = _det()
    sig = _feed(
        det,
        [
            (95, 100, 90, 96),  # ref
            (96, 99.5, 88, 89),  # 2d
            (89, 99, 89, 98),  # inside (of the 2d)
            (98.9, 99.2, 89.5, 99.1),  # developing 2u green
        ],
    )
    assert sig is not None and sig.name == "2-1-2u" and sig.dir == 1
    assert sig.trig == 99.0  # inside bar high
    assert sig.ladder[0] == 99.5  # anchor = the 2d bar high
    assert sig.ladder == [99.5, 100]


def test_122_revstrat_trap_trigger_and_conditional_anchor2():
    det = _det()
    sig = _feed(
        det,
        [
            (105, 110, 100, 106),  # mother (skill bar 0)
            (106, 108, 103, 104),  # inside
            (104, 107.9, 99, 100.5),  # trap 2d, round-trips below mother low
            (107.0, 108.5, 101, 108.4),  # developing 2u green through trap high
        ],
    )
    assert sig is not None and sig.name == "1-2d-2u" and sig.star
    assert sig.trig == 107.9  # trap bar high (skill-agreeing)
    assert sig.ladder == [108, 110]  # T1 reclaim, T2 = mother wick
    # without the round-trip the mother rung is NOT pre-seeded as anchor2
    det2 = _det()
    sig2 = _feed(
        det2,
        [
            (105, 110, 100, 106),
            (106, 108, 103, 104),
            (104, 107.9, 100.5, 101),  # trap holds above mother low
            (107.0, 108.5, 101, 108.4),
        ],
    )
    assert sig2 is not None and sig2.name == "1-2d-2u"
    assert sig2.ladder == [108, 110]  # 110 still enters via the ladder walk


def test_132_takes_precedence_over_32_and_anchors_mother():
    det = _det()
    sig = _feed(
        det,
        [
            (105, 110, 100, 106),  # mother
            (106, 108, 103, 104),  # inside
            (104, 109, 101, 108.5),  # 3 that round-trips the inside bar
            (108.6, 109.5, 102, 109.4),  # developing 2u green through the 3's high
        ],
    )
    assert sig is not None and sig.name == "1-3-2u"
    assert sig.trig == 109  # the 3's high
    assert sig.ladder == [110]  # mother wick


def test_32_boom_flag_and_pivot_ladder():
    det = _det()
    sig = _feed(
        det,
        [
            (96, 100, 95, 97),  # prior bar
            (100.5, 101, 94, 100.8),  # outside bar, hammer shape
            (100.9, 101.5, 95.5, 101.4),  # developing 2u green
        ],
    )
    assert sig is not None and sig.name == "3-2u"
    assert sig.boom is True and sig.star is True
    assert sig.ladder == []  # no anchor, no prior high above the trigger
    det2 = _det()
    sig2 = _feed(
        det2,
        [
            (96, 100, 95, 97),
            (100.9, 101, 94, 94.5),  # outside bar, red full-body (no shape)
            (94.6, 101.5, 94.4, 101.4),  # developing 2u green
        ],
    )
    assert sig2 is not None and sig2.name == "3-2u" and sig2.boom is False


def test_312_color_router_reversal_vs_continuation():
    red3 = [
        (95, 100, 90, 96),
        (100.5, 101, 89, 89.5),  # RED 3
        (89.6, 100.5, 90.5, 99),  # inside
        (99.1, 100.8, 91, 100.7),  # developing 2u green
    ]
    sig = _feed(_det(), red3)
    assert sig is not None and sig.name == "3-1-2u" and sig.rev is True
    green3 = [row[:] for row in (list(r) for r in red3)]
    green3[1] = (89.5, 101, 89, 100.5)  # GREEN 3, same range
    sig2 = _feed(_det(), [tuple(r) for r in green3])
    assert sig2 is not None and sig2.name == "3-1-2u" and sig2.rev is False


def test_momo_midpoint_gate():
    base = [(98, 103, 99, 102), (102.5, 105, 100, 104.5)]  # ref, then 2u
    top_half_inside = base + [(104, 104.8, 103, 104.2), (104.3, 105.2, 103.5, 105.1)]
    sig = _feed(_det(), top_half_inside)
    assert sig is not None and sig.name == "2-1-2u" and sig.rev is False
    bottom_half_inside = base + [(101, 101.5, 100.2, 101.2), (101.3, 102, 100.5, 101.9)]
    assert _feed(_det(), bottom_half_inside) is None  # momo gated, no coarser setup on


def test_precedence_reroute_shotgun_shape():
    bars = [
        (98, 103, 99, 102),
        (102.5, 105, 100, 104.5),  # 2u
        (104, 104.9, 98, 99),  # 2d
        (99.1, 105.0, 99.0, 104.9),  # developing 2u green through the 2d high
    ]
    sig = _feed(_det(), bars)  # shotgun OFF in the user dictionary
    assert sig is not None and sig.name == "2-2u"
    assert sig.trig == 104.9 and sig.ladder[0] == 105
    sig2 = _feed(_det(enabled=USER_DICTIONARY | {"shotgun"}), bars)
    assert sig2 is not None and sig2.name == "2-2-2u" and sig2.star


def test_13_live_intrabar_within_one_developing_hour():
    det = _det()
    assert det.update(0, 105, 110, 100, 106) is None  # mother
    assert det.update(HOUR, 106, 108, 103, 104) is None  # inside
    # hour 2, first 5m bar: breaks the inside LOW only, red -> no signal yet
    assert det.update(2 * HOUR, 107, 107.5, 102.5, 102.6) is None
    # hour 2, later 5m bar: high side breaks too -> live 3, close green
    sig = det.update(2 * HOUR + 300, 102.6, 108.6, 102.8, 108.5)
    assert sig is not None and sig.name == "1-3u"
    assert sig.trig == 108  # inside bar high: the as-built completion side
    assert sig.ladder == [110]


def test_pmg_prefix_unreachable_for_u0_signals():
    # five successive lower highs, then a bullish 2-2 reversal: the developing
    # bar's own break seeds the streak walk at curH, so lhRun == 0 and the
    # PMG+ prefix cannot fire for break-directional setups (as-built quirk).
    bars = [
        (108, 110, 105, 106),
        (106, 108, 103, 104),
        (104, 106, 101, 102),
        (102, 104, 99, 100),
        (100, 102, 97, 98),
        (98, 100, 95, 96),  # 2d (last completed)
        (96, 100.6, 95.5, 100.5),  # developing 2u green through 100
    ]
    sig = _feed(_det(), bars)
    assert sig is not None and sig.name == "2-2u"
    assert sig.pmg is False


def test_seed_history_and_cap():
    det = _det()
    det.seed_history([(i * HOUR, 100 + i, 101 + i, 99 + i, 100.5 + i) for i in range(260)])
    assert len(det.arr_h) == 250
    # first live update starts a developing bar without pushing a duplicate
    det.update(300 * HOUR, 400, 401, 399, 400.5)
    assert len(det.arr_h) == 250
    # crossing to the next hour pushes exactly one completed bar (cap holds)
    det.update(301 * HOUR, 400.5, 402, 400, 401.5)
    assert len(det.arr_h) == 250
