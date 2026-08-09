"""TVB-21 engine-extension tests: pattern entries, vetoes, target exits.

The invariance half of the contract (entry_mode="arm" defaults leave every
pre-existing path bit-identical) is carried by the rest of the suite -- the
paper-engine behavior tests and the committed-GOOGL port-parity pin all run
on default configs. These tests cover the pattern-arm path itself.
"""

from analysis.paper.engine import Twin, TwinConfig
from analysis.paper.patterns import Signal

HOUR = 3600
NONES8 = (None,) * 8  # xs, xs_tf, xl, xl_tf, brk_lo, brk_lo_tf, brk_up, brk_up_tf


def _twin(**kw):
    return Twin(TwinConfig(symbol="SYN", mintick=0.01, entry_mode="pattern", **kw))


def _sig(direction=1, trig=104.9, ladder=(), name="2-2u"):
    return Signal(
        dir=direction,
        trig=trig,
        name=name,
        rev=True,
        star=False,
        weak=False,
        fragile=False,
        boom=False,
        pmg=False,
        ladder=list(ladder),
    )


def test_default_arm_mode_builds_no_detector():
    tw = Twin(TwinConfig(symbol="SYN", mintick=0.01))
    assert tw.pattern is None
    assert tw.replay_bar(0, 100, 101, 99, 100.5) == []


def test_pattern_entry_end_to_end_via_replay_bar():
    tw = _twin()
    assert tw.pattern is not None
    feed = [
        (0, 100, 103, 99, 102),  # sets D/W/M opens at 100
        (HOUR, 102.5, 105, 100, 104.5),  # 2u
        (2 * HOUR, 104, 104.9, 99.8, 100.5),  # 2d
    ]
    for ts, o, h, l, c in feed:  # noqa: E741
        assert tw.replay_bar(ts, o, h, l, c) == []
    ev = tw.replay_bar(3 * HOUR, 100.6, 105.0, 100.4, 104.9)  # 2u green, gate up
    assert len(ev) == 1 and ev[0]["action"] == "enter" and ev[0]["dir"] == "long"
    assert ev[0]["pattern"] == "2-2u"
    assert abs(ev[0]["price"] - 104.91) < 1e-9  # trigger 104.9 + tick
    assert tw.veto_counts["entries"] == 1 and tw.veto_counts["candidates"] == 1


def test_bf_prox_veto_long_and_pass_through():
    tw = _twin(bf_prox_veto_pct=1.0)
    sig = _sig(ladder=[110.0])
    # nearest alive upper line 0.85% above fill -> veto
    ev = tw._position_step(
        0, 105.0, 100.4, 104.9, *NONES8, True, False, o=100.6, sig=sig, prox_vals=[105.8]
    )
    assert ev == [] and tw.pos == 0 and tw.veto_counts["bf_prox"] == 1
    # 1.5% away -> enters; a line BELOW fill is not on the long harvest side
    ev = tw._position_step(
        0, 105.0, 100.4, 104.9, *NONES8, True, False, o=100.6, sig=sig, prox_vals=[106.5, 104.0]
    )
    assert len(ev) == 1 and tw.pos == 1
    assert abs(ev[0]["price"] - 104.91) < 1e-9


def test_bf_prox_veto_short_mirror():
    tw = _twin(bf_prox_veto_pct=1.0)
    sig = _sig(direction=-1, trig=95.1, name="2-2d", ladder=[90.0])
    ev = tw._position_step(
        0, 99.5, 94.9, 95.0, *NONES8, False, True, o=99.0, sig=sig, prox_vals=[94.3]
    )
    assert ev == [] and tw.veto_counts["bf_prox"] == 1  # 0.83% below fill 95.09
    ev = tw._position_step(
        0, 99.5, 94.9, 95.0, *NONES8, False, True, o=99.0, sig=sig, prox_vals=[93.5]
    )
    assert len(ev) == 1 and tw.pos == -1
    assert abs(ev[0]["price"] - 95.09) < 1e-9  # trigger 95.1 - tick


def test_chop_veto_and_both_bucket():
    tw = _twin(chop_veto_pct=2.0)
    tw.gate_open = {"D": 104.0, "W": 90.0, "M": 80.0}  # D open 0.87% from fill
    ev = tw._position_step(
        0,
        105.0,
        100.4,
        104.9,
        *NONES8,
        True,
        False,
        o=100.6,
        sig=_sig(ladder=[110.0]),
        prox_vals=None,
    )
    assert ev == [] and tw.veto_counts["chop"] == 1
    tw2 = _twin(chop_veto_pct=2.0, bf_prox_veto_pct=1.0)
    tw2.gate_open = {"D": 104.0, "W": 90.0, "M": 80.0}
    ev = tw2._position_step(
        0,
        105.0,
        100.4,
        104.9,
        *NONES8,
        True,
        False,
        o=100.6,
        sig=_sig(ladder=[110.0]),
        prox_vals=[105.5],
    )
    assert ev == [] and tw2.veto_counts["both"] == 1
    tw3 = _twin(chop_veto_pct=2.0)
    tw3.gate_open = {"D": 96.0, "W": 90.0, "M": 80.0}  # all > 2% away
    ev = tw3._position_step(
        0,
        105.0,
        100.4,
        104.9,
        *NONES8,
        True,
        False,
        o=100.6,
        sig=_sig(ladder=[110.0]),
        prox_vals=None,
    )
    assert len(ev) == 1 and tw3.pos == 1


def test_target_exit_t1_replaces_bf_and_fills_at_level():
    tw = _twin(exit_targets=1, bf_harvest_exit=False)
    ev = tw._position_step(
        0,
        105.0,
        100.4,
        104.9,
        *NONES8,
        True,
        False,
        o=100.6,
        sig=_sig(ladder=[106.0, 108.0]),
        prox_vals=None,
    )
    assert tw.pos == 1 and tw.tgt_px == 106.0 and tw.tgt_rung == 1
    assert ev[0]["tgt_rung"] == 1 and ev[0]["ladder"] == [106.0, 108.0]
    # next bar touches the level; a bf candidate would be ignored (targets own the slot)
    ev = tw._position_step(
        300, 106.2, 104.5, 106.1, *NONES8, False, False, o=104.9, sig=None, prox_vals=None
    )
    assert len(ev) == 1 and ev[0]["kind"] == "tgt" and ev[0]["price"] == 106.0
    assert ev[0]["line_N"] == 1 and ev[0]["pnl_pct"] > 0
    assert tw.pos == 0 and tw.tgt_px is None and tw.tgt_rung is None


def test_target_exit_t2_and_fallback_to_t1():
    tw = _twin(exit_targets=2, bf_harvest_exit=False)
    tw._position_step(
        0,
        105.0,
        100.4,
        104.9,
        *NONES8,
        True,
        False,
        o=100.6,
        sig=_sig(ladder=[106.0, 108.0]),
        prox_vals=None,
    )
    assert tw.tgt_px == 108.0 and tw.tgt_rung == 2
    tw2 = _twin(exit_targets=2, bf_harvest_exit=False)
    tw2._position_step(
        0,
        105.0,
        100.4,
        104.9,
        *NONES8,
        True,
        False,
        o=100.6,
        sig=_sig(ladder=[106.0]),
        prox_vals=None,
    )
    assert tw2.tgt_px == 106.0 and tw2.tgt_rung == 1  # no rung 2 -> T1 fallback


def test_no_target_candidate_is_skipped_in_package_arms():
    tw = _twin(exit_targets=1, bf_harvest_exit=False)
    ev = tw._position_step(
        0, 105.0, 100.4, 104.9, *NONES8, True, False, o=100.6, sig=_sig(ladder=[]), prox_vals=None
    )
    assert ev == [] and tw.pos == 0 and tw.veto_counts["no_target"] == 1
    # isolation-arm config (C1 exits) takes the same signal without a ladder
    tw2 = _twin()
    ev = tw2._position_step(
        0, 105.0, 100.4, 104.9, *NONES8, True, False, o=100.6, sig=_sig(ladder=[]), prox_vals=None
    )
    assert len(ev) == 1 and tw2.pos == 1


def test_target_containment_born_beyond_long():
    # TVB-22 amendment (audit F1): a long BORN BEYOND its frozen T1 must NOT
    # exit on a bar wholly above the level (the as-built one-sided h >= tgt
    # booked a fill the bar never traded); it exits at the first bar whose
    # range contains the level, at the level, for a real structural loss.
    tw = _twin(exit_targets=1, bf_harvest_exit=False)
    tw._position_step(
        0,
        105.0,
        100.4,
        104.9,
        *NONES8,
        True,
        False,
        o=100.6,
        sig=_sig(ladder=[103.0]),
        prox_vals=None,
    )
    assert tw.pos == 1 and tw.entry_px > tw.tgt_px  # born beyond
    ev = tw._position_step(
        300, 105.5, 104.0, 105.0, *NONES8, False, False, o=104.9, sig=None, prox_vals=None
    )
    assert ev == [] and tw.pos == 1  # bar wholly above the level: no exit
    ev = tw._position_step(
        600, 104.2, 102.8, 103.5, *NONES8, False, False, o=104.0, sig=None, prox_vals=None
    )
    assert len(ev) == 1 and ev[0]["kind"] == "tgt" and ev[0]["price"] == 103.0
    assert ev[0]["pnl_pct"] < 0  # real containment fill, structural loss


def test_target_containment_born_beyond_short_mirror():
    tw = _twin(exit_targets=1, bf_harvest_exit=False)
    tw._position_step(
        0,
        99.5,
        94.9,
        95.0,
        *NONES8,
        False,
        True,
        o=99.0,
        sig=_sig(direction=-1, trig=95.1, name="2-2d", ladder=[97.0]),
        prox_vals=None,
    )
    assert tw.pos == -1 and tw.entry_px < tw.tgt_px  # born beyond
    ev = tw._position_step(
        300, 94.5, 93.0, 93.5, *NONES8, False, False, o=94.4, sig=None, prox_vals=None
    )
    assert ev == [] and tw.pos == -1  # bar wholly below the level: no exit
    ev = tw._position_step(
        600, 97.5, 96.5, 97.0, *NONES8, False, False, o=96.6, sig=None, prox_vals=None
    )
    assert len(ev) == 1 and ev[0]["kind"] == "tgt" and ev[0]["price"] == 97.0
    assert ev[0]["pnl_pct"] < 0


def test_target_gap_past_favorable_side_waits_for_containment():
    # The gap-past edge is pinned deliberately (same convention as the C1 bf
    # containment touch): a bar wholly beyond a FAVORABLE target does not
    # exit either; the exit fires when the level actually trades.
    tw = _twin(exit_targets=1, bf_harvest_exit=False)
    tw._position_step(
        0,
        105.0,
        100.4,
        104.9,
        *NONES8,
        True,
        False,
        o=100.6,
        sig=_sig(ladder=[106.0]),
        prox_vals=None,
    )
    assert tw.pos == 1 and tw.tgt_px == 106.0
    ev = tw._position_step(
        300, 107.5, 106.4, 107.0, *NONES8, False, False, o=106.5, sig=None, prox_vals=None
    )
    assert ev == [] and tw.pos == 1  # gapped past the level: no containment
    ev = tw._position_step(
        600, 106.8, 105.9, 106.2, *NONES8, False, False, o=106.7, sig=None, prox_vals=None
    )
    assert len(ev) == 1 and ev[0]["kind"] == "tgt" and ev[0]["price"] == 106.0


def test_no_target_vetoed_overlap_counter():
    # TVB-22 amendment (audit F2): vetoes are evaluated for every candidate
    # BEFORE the structural no-target skip; the overlap is logged so
    # entries = candidates - (vetoed + no_target - no_target_vetoed).
    tw = _twin(exit_targets=1, bf_harvest_exit=False, bf_prox_veto_pct=1.0)
    ev = tw._position_step(
        0,
        105.0,
        100.4,
        104.9,
        *NONES8,
        True,
        False,
        o=100.6,
        sig=_sig(ladder=[]),
        prox_vals=[105.5],
    )
    assert ev == [] and tw.pos == 0
    vc = tw.veto_counts
    assert vc["no_target"] == 1 and vc["bf_prox"] == 1 and vc["no_target_vetoed"] == 1
    # unvetoed no-target candidate: skip logged, overlap unchanged
    ev = tw._position_step(
        0,
        105.0,
        100.4,
        104.9,
        *NONES8,
        True,
        False,
        o=100.6,
        sig=_sig(ladder=[]),
        prox_vals=[120.0],
    )
    assert ev == [] and vc["no_target"] == 2 and vc["no_target_vetoed"] == 1
    assert vc["candidates"] == 2 and vc["entries"] == 0


def test_late_entry_fills_at_bar_open_not_stale_level():
    tw = _twin()
    ev = tw._position_step(
        0,
        106.5,
        105.2,
        106.4,
        *NONES8,
        True,
        False,
        o=105.6,
        sig=_sig(ladder=[110.0]),
        prox_vals=None,
    )
    assert len(ev) == 1
    assert abs(ev[0]["price"] - 105.6) < 1e-9  # max(104.91, open 105.6)
