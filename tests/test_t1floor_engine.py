"""TVB-23 engine-extension tests: T1-floor veto, ATR vetoes, retracement census.

Prereg: docs/experiments/tvb23_t1floor_prereg.md ("Mechanics"). The
invariance half of the contract (new defaults leave every pre-existing path
bit-identical) is carried by the rest of the suite; these tests cover the
new paths. The retracement fixtures pin the AS-BUILT pine edge documented in
the prereg's 2026-08-10 correction: the position-health flags are one-sided,
so an outside bar whose with-side broke first never labels POTENTIAL 3.
"""

import pytest

from analysis.paper.engine import Twin, TwinConfig, _Atr
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


def _step(tw, sig, prox_vals=None, gate_up=True, gate_dn=False, o=100.6):
    return tw._position_step(
        0, 105.0, 100.4, 104.9, *NONES8, gate_up, gate_dn, o=o, sig=sig, prox_vals=prox_vals
    )


# --- T1-floor veto -----------------------------------------------------------
# fill = max(trig + tick, o) = 104.91 for the default long sig.

FLOOR = dict(t1_floor_pct=0.25, exit_targets=1, bf_harvest_exit=False)


def test_floor_vetoes_born_beyond_long():
    tw = _twin(**FLOOR)
    ev = _step(tw, _sig(ladder=[104.5]))  # T1 behind the fill
    assert ev == [] and tw.pos == 0
    assert tw.veto_counts["t1_floor"] == 1
    assert tw.veto_counts["t1_floor_le0"] == 1 and tw.veto_counts["t1_floor_small"] == 0
    assert tw.veto_counts["t1_floor_only"] == 1


def test_floor_vetoes_tiny_target_long():
    tw = _twin(**FLOOR)
    ev = _step(tw, _sig(ladder=[105.0]))  # d ~ 0.086% < 0.25%
    assert ev == [] and tw.veto_counts["t1_floor_small"] == 1
    assert tw.veto_counts["t1_floor_le0"] == 0


def test_floor_passes_real_target_and_freezes_it():
    tw = _twin(**FLOOR)
    ev = _step(tw, _sig(ladder=[105.4, 106.0]))  # d ~ 0.467%
    assert len(ev) == 1 and tw.pos == 1
    assert tw.tgt_px == 105.4 and tw.tgt_rung == 1
    assert tw.veto_counts["t1_floor"] == 0 and tw.veto_counts["entries"] == 1


def test_floor_boundary_is_strict_less_than():
    # trig 99.99, open 100.0 -> fill exactly 100.0; T1 100.25 -> d == floor
    tw = _twin(**FLOOR)
    ev = tw._position_step(
        0,
        100.4,
        99.5,
        100.2,
        *NONES8,
        True,
        False,
        o=100.0,
        sig=_sig(trig=99.99, ladder=[100.25]),
        prox_vals=None,
    )
    assert len(ev) == 1 and tw.pos == 1  # d < floor is strict: at-floor enters


def test_floor_vetoes_born_beyond_short_mirror():
    tw = _twin(**FLOOR)
    ev = tw._position_step(
        0,
        99.5,
        94.9,
        95.0,
        *NONES8,
        False,
        True,
        o=99.0,
        sig=_sig(direction=-1, trig=95.1, name="2-2d", ladder=[95.5]),
        prox_vals=None,
    )  # fill 95.09; short T1 above the fill = born-beyond
    assert ev == [] and tw.veto_counts["t1_floor_le0"] == 1


def test_floor_applies_under_c1_exits_and_empty_ladder_skips():
    # DINF/A1F shape: no target exits, floor still an entry veto; an empty
    # snapshot ladder is a structural skip (uniform across floor arms).
    tw = _twin(t1_floor_pct=0.25)  # exit_targets None, bf_harvest_exit True
    assert _step(tw, _sig(ladder=[105.0])) == []  # tiny -> floor veto
    assert tw.veto_counts["t1_floor_small"] == 1
    assert _step(tw, _sig(ladder=[])) == []  # no T1 to measure -> skip
    assert tw.veto_counts["no_target"] == 1
    ev = _step(tw, _sig(ladder=[105.4]))
    assert len(ev) == 1 and tw.pos == 1
    assert tw.tgt_px is None  # C1 exits: nothing frozen


def test_floor_only_counter_excludes_prox_overlap():
    tw = _twin(bf_prox_veto_pct=1.0, **FLOOR)
    # floor-vetoed AND prox-vetoed -> t1_floor counted, t1_floor_only not
    ev = _step(tw, _sig(ladder=[105.0]), prox_vals=[105.2])
    assert ev == []
    assert tw.veto_counts["t1_floor"] == 1 and tw.veto_counts["t1_floor_only"] == 0
    assert tw.veto_counts["bf_prox"] == 1


def test_entry_reconciliation_equation():
    tw = _twin(bf_prox_veto_pct=1.0, **FLOOR)
    _step(tw, _sig(ladder=[105.0]))  # floor-only veto
    _step(tw, _sig(ladder=[110.0]), prox_vals=[105.2])  # prox veto
    _step(tw, _sig(ladder=[]), prox_vals=[105.2])  # no_target, prox-vetoed
    _step(tw, _sig(ladder=[]))  # no_target, clean
    ev = _step(tw, _sig(ladder=[110.0]))  # enters
    assert len(ev) == 1
    vc = tw.veto_counts
    assert vc["candidates"] == 5 and vc["entries"] == 1
    assert (
        vc["entries"]
        == vc["candidates"]
        - vc["no_target"]
        - (vc["both"] + vc["bf_prox"] + vc["chop"] - vc["no_target_vetoed"])
        - vc["t1_floor_only"]
    )


# --- ATR ---------------------------------------------------------------------


def test_atr_wilder_math_hand_computed():
    a = _Atr(tf_s=HOUR, window=3)
    a.push_completed(10, 8, 9)  # TR 2 (no prev close)
    assert a.value is None
    a.push_completed(11, 9, 10)  # TR max(2, 2, 0) = 2
    a.push_completed(12, 11, 11.5)  # TR max(1, 2, 1) = 2 -> seed SMA 2.0
    assert a.value == pytest.approx(2.0)
    a.push_completed(12, 10, 11)  # TR max(2, .5, 1.5) = 2 -> (2*2+2)/3
    assert a.value == pytest.approx(2.0)
    a.push_completed(20, 15, 18)  # TR max(5, 9, 4) = 9 -> (2*2+9)/3
    assert a.value == pytest.approx(13 / 3)


def test_atr_update_completes_only_on_rollover():
    a = _Atr(tf_s=HOUR, window=1)
    a.update(0, 10, 8, 9)
    assert a.value is None  # developing bar never contributes
    a.update(300, 11, 9, 10)
    assert a.value is None
    a.update(HOUR, 12, 11, 11.5)  # completes (11, 8, 10): TR 3
    assert a.value == pytest.approx(3.0)


def test_atr_prox_veto_price_units():
    tw = _twin(bf_prox_veto_atr=1.0, **FLOOR)
    assert tw.atr is not None
    tw.atr.value = 1.0  # formed ATR, price units
    ev = _step(tw, _sig(ladder=[110.0]), prox_vals=[105.8])  # 0.89 above fill
    assert ev == [] and tw.veto_counts["bf_prox"] == 1
    ev = _step(tw, _sig(ladder=[110.0]), prox_vals=[106.0])  # 1.09 above
    assert len(ev) == 1 and tw.pos == 1


def test_atr_chop_veto_price_units():
    tw = _twin(chop_veto_atr=2.0, **FLOOR)
    tw.atr.value = 1.0
    tw.gate_open = {"D": 106.5, "W": 90.0, "M": 80.0}  # 1.59 from fill <= 2.0
    assert _step(tw, _sig(ladder=[110.0])) == []
    assert tw.veto_counts["chop"] == 1
    tw2 = _twin(chop_veto_atr=2.0, **FLOOR)
    tw2.atr.value = 1.0
    tw2.gate_open = {"D": 107.5, "W": 90.0, "M": 80.0}  # all > 2.0 away
    assert len(_step(tw2, _sig(ladder=[110.0]))) == 1


def test_atr_and_pct_forms_mutually_exclusive():
    with pytest.raises(ValueError):
        _twin(bf_prox_veto_pct=1.0, bf_prox_veto_atr=1.0)
    with pytest.raises(ValueError):
        _twin(chop_veto_pct=2.0, chop_veto_atr=2.0)


# --- retracement census ------------------------------------------------------
# Feeds run through replay_bar: hour 0 seeds the completed 1H bar
# (o100 h103 l99 c102) and the D/W/M opens at 100; the position is placed
# directly (bar-start position semantics), then hour-1 bars drive the
# developing-bar flags.


def _held(direction=1, **kw):
    tw = _twin(retrace_census=True, **kw)
    assert tw.replay_bar(0, 100, 103, 99, 102) == []
    tw.pos, tw.entry_px, tw.entry_ts = direction, 100.0, 0
    return tw


def test_retracement_label_inside_and_red_while_long():
    tw = _held()
    tw.replay_bar(HOUR, 102, 102.5, 100, 101)  # inside vs 103/99, red
    assert tw.first_retrace_ts == HOUR and tw.first_p3_ts is None


def test_potential3_label_on_against_side_break_while_long():
    tw = _held()
    ev = tw.replay_bar(HOUR, 101, 101.5, 98.9, 99.0)  # takes prior low; red
    assert tw.first_p3_ts is None  # stamps travelled with the exit event
    assert len(ev) == 1 and ev[0]["kind"] == "flip"  # close 99 < all opens
    assert ev[0]["first_p3_ts"] == HOUR and ev[0]["first_retrace_ts"] is None


def test_potential3_label_on_failed_with_side_push_while_long():
    tw = _held()
    tw.replay_bar(HOUR, 102, 103.5, 101, 101.5)  # breaks high, closes red
    assert tw.first_p3_ts == HOUR and tw.first_retrace_ts is None


def test_as_built_edge_with_side_first_outside_bar_never_labels():
    # prereg correction 2026-08-10: with-side (high) breaks first on a green
    # push, then the low breaks too -> flags skip u0 -> out0; one-sided d0
    # never true, so POTENTIAL 3 never fires for the long. Pine-exact.
    tw = _held()
    tw.replay_bar(HOUR, 102, 103.5, 101, 103)  # u0, green: no label
    assert tw.first_p3_ts is None and tw.first_retrace_ts is None
    ev = tw.replay_bar(HOUR + 300, 103, 103.6, 98.9, 99.0)  # now out0
    assert len(ev) == 1 and ev[0]["kind"] == "flip"
    assert ev[0]["first_p3_ts"] is None  # the as-built edge, pinned


def test_clean_2d_red_while_short_stays_unlabeled():
    tw = _held(direction=-1)
    tw.replay_bar(HOUR, 102, 102.2, 98.5, 99.5)  # takes only the low, red
    assert tw.first_p3_ts is None and tw.first_retrace_ts is None


def test_census_off_keeps_exit_event_shape():
    tw = _twin()
    assert tw.replay_bar(0, 100, 103, 99, 102) == []
    tw.pos, tw.entry_px, tw.entry_ts = 1, 100.0, 0
    ev = tw.replay_bar(HOUR, 101, 101.5, 98.9, 99.0)  # flip exit
    assert len(ev) == 1 and ev[0]["kind"] == "flip"
    assert "first_retrace_ts" not in ev[0] and "first_p3_ts" not in ev[0]


def test_stamps_reset_on_entry():
    tw = _twin(retrace_census=True, **FLOOR)
    tw.first_retrace_ts, tw.first_p3_ts = 111, 222  # stale
    ev = _step(tw, _sig(ladder=[105.4]))
    assert len(ev) == 1 and tw.pos == 1
    assert tw.first_retrace_ts is None and tw.first_p3_ts is None
