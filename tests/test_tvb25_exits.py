"""TVB-25 exit-round engine fixtures (prereg + 2026-08-16 amendment).

Covers the new exit machinery behind the inert defaults: the C0 state stop
(2-against at 1H close, D14 inclusive), intrabar-3 invalidation (level
freeze, entry-hour scope, degenerate entry-bar case), structural/ATR stops
(anchor freeze, degeneracy -> ATR fallback, D3 gap-through fills), the P1/P2
tranche profiles (fold-to-runner, floor arming, T1 retrace, breakeven,
arm-and-fire), X1 arming, and the ruled risk-first collision precedence with
the D9 collision census. The inert-defaults half of the contract is carried
by the rest of the suite (all golden pins run on default configs).
"""

from analysis.paper.engine import Twin, TwinConfig
from analysis.paper.patterns import Signal

HOUR = 3600
NONES8 = (None,) * 8  # xs, xs_tf, xl, xl_tf, brk_lo, brk_lo_tf, brk_up, brk_up_tf


def _twin(**kw):
    return Twin(TwinConfig(symbol="SYN", mintick=0.01, entry_mode="pattern", **kw))


def _sig(
    direction=1,
    trig=104.9,
    ladder=(),
    name="2-2u",
    stop_anchor=None,
    stop_src=None,
    stop_src_ts=None,
):
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
        stop_anchor=stop_anchor,
        stop_src=stop_src,
        stop_src_ts=stop_src_ts,
    )


def _prime_pattern(tw, key=0, prev_h=105.0, prev_l=99.0):
    """Give the detector the prior completed 1H bar the i3 freeze reads."""
    tw.pattern.key = key
    tw.pattern.arr_o = [100.0]
    tw.pattern.arr_h = [prev_h]
    tw.pattern.arr_l = [prev_l]
    tw.pattern.arr_c = [104.0]


def _enter_long(tw, sig, ts=0):
    ev = tw._position_step(ts, 105.0, 100.4, 104.9, *NONES8, True, False, o=100.6, sig=sig)
    assert len(ev) == 1 and ev[0]["action"] == "enter" and tw.pos == 1
    return ev[0]


# --- state stop (C0 2-against at 1H close; S-family) ------------------------


def _state_twin():
    return Twin(
        TwinConfig(
            symbol="SYN",
            mintick=0.01,
            state_stop=True,
            arm_tf_s=3600,
            bf_harvest_exit=False,
            brk_exit=False,
            flip_backstop=False,
        )
    )


def _drive_hours(tw, bars):
    """Feed 1H bars (bar_s=3600): every bar completes its own arm hour."""
    out = []
    for ts, o, h, l, c in bars:  # noqa: E741
        out.extend(tw.replay_bar(ts, o, h, l, c, bar_s=3600))
    return out


def test_state_stop_two_against_exits_at_hour_close():
    tw = _state_twin()
    ev = _drive_hours(
        tw,
        [
            (0, 100.0, 101.0, 99.5, 100.8),  # gates at 100; prev hour 101/99.5
            (HOUR, 100.9, 102.0, 100.5, 101.5),  # long entry through 101.01
            (2 * HOUR, 101.4, 101.6, 100.4, 100.6),  # 2D vs hour-1 low 100.5
        ],
    )
    kinds = [(e["action"], e.get("kind")) for e in ev]
    assert kinds == [("enter", None), ("exit", "state")]
    assert ev[1]["ts"] == 2 * HOUR and ev[1]["price"] == 100.6  # the 1H close


def test_state_stop_inside_hour_does_not_exit():
    tw = _state_twin()
    ev = _drive_hours(
        tw,
        [
            (0, 100.0, 101.0, 99.5, 100.8),
            (HOUR, 100.9, 102.0, 100.5, 101.5),  # long entry
            (2 * HOUR, 101.4, 101.9, 100.6, 101.0),  # inside prior hour: holds
        ],
    )
    assert [e["action"] for e in ev] == ["enter"] and tw.pos == 1


def test_state_stop_type3_hour_also_exits():
    # D14 inclusive reading: an hour that broke BOTH prior extremes still
    # broke the opposite one -- it exits
    tw = _state_twin()
    ev = _drive_hours(
        tw,
        [
            (0, 100.0, 101.0, 99.5, 100.8),
            (HOUR, 100.9, 102.0, 100.5, 101.5),
            (2 * HOUR, 101.4, 102.5, 100.4, 101.8),  # broke high AND low
        ],
    )
    assert ev[-1]["kind"] == "state" and ev[-1]["price"] == 101.8


# --- D14 entry-hour ruling (2026-08-16, TVB-26 audit F3, user-ruled) ---------
# The entry hour COUNTS: an entry on the hour-completing bar of an hour whose
# range broke the prior opposite extreme exits at that same bar's close --
# matching how mid-hour entries already behave and the i3 degenerate shape.


def test_d14_entry_bar_state_degenerate_long():
    tw = _state_twin()
    ev = _drive_hours(
        tw,
        [
            (0, 100.0, 101.0, 99.5, 100.8),  # prev hour 101/99.5; gates at 100
            (HOUR, 100.9, 102.0, 99.0, 101.5),  # breaks BOTH sides: enter + out
        ],
    )
    assert [(e["action"], e.get("kind")) for e in ev] == [("enter", None), ("exit", "state")]
    assert ev[1]["ts"] == HOUR and ev[1]["price"] == 101.5  # that bar's close
    assert ev[1]["state_degenerate"] is True
    assert tw.exit_counters["state_degenerate"] == 1 and tw.pos == 0


def test_d14_entry_bar_state_degenerate_short():
    tw = _state_twin()
    ev = _drive_hours(
        tw,
        [
            (0, 100.0, 101.0, 99.5, 99.2),  # close below the opens: gate down
            (HOUR, 99.3, 101.6, 99.0, 99.1),  # short entry + prior HIGH broken
        ],
    )
    assert [(e["action"], e.get("kind")) for e in ev] == [("enter", None), ("exit", "state")]
    assert ev[0]["dir"] == "short" and ev[1]["price"] == 99.1
    assert tw.exit_counters["state_degenerate"] == 1 and tw.pos == 0


def test_d14_entry_bar_boundary_one_tick():
    # strict-break boundary: exactly one tick beyond fires, less does not
    tw = _state_twin()
    ev = _drive_hours(
        tw,
        [
            (0, 100.0, 101.0, 99.5, 100.8),
            (HOUR, 100.9, 102.0, 99.49, 101.5),  # 99.5 - 99.49 = one tick
        ],
    )
    assert [(e["action"], e.get("kind")) for e in ev] == [("enter", None), ("exit", "state")]
    tw2 = _state_twin()
    ev2 = _drive_hours(
        tw2,
        [
            (0, 100.0, 101.0, 99.5, 100.8),
            (HOUR, 100.9, 102.0, 99.495, 101.5),  # half a tick: no break
        ],
    )
    assert [(e["action"], e.get("kind")) for e in ev2] == [("enter", None)]
    assert tw2.pos == 1 and tw2.exit_counters["state_degenerate"] == 0


# --- intrabar-3 invalidation ------------------------------------------------


def test_i3_exits_on_prior_hour_opposite_break_within_entry_hour():
    tw = _twin(intrabar3_exit=True)
    _prime_pattern(tw, key=0, prev_l=99.0)
    entry = _enter_long(tw, _sig())
    assert entry["i3_level"] == 99.0
    # next 5m bar in the SAME hour breaks the prior hour's low
    ev = tw._position_step(300, 100.0, 98.9, 99.2, *NONES8, True, False, o=100.0)
    assert [e["kind"] for e in ev] == ["i3"]
    assert ev[0]["price"] == 99.2 and tw.pos == 0  # exit at the 5m close


def test_i3_deactivates_when_entry_hour_completes():
    tw = _twin(intrabar3_exit=True)
    _prime_pattern(tw, key=0, prev_l=99.0)
    _enter_long(tw, _sig())
    tw.pattern.key = HOUR  # entry hour completed; a later break is not i3
    ev = tw._position_step(HOUR, 100.0, 98.9, 99.2, *NONES8, True, False, o=100.0)
    assert ev == [] and tw.pos == 1


def test_i3_degenerate_entry_bar_exits_at_close():
    tw = _twin(intrabar3_exit=True)
    _prime_pattern(tw, key=0, prev_l=100.5)  # entry bar low 100.4 breaks it
    ev = tw._position_step(0, 105.0, 100.4, 104.9, *NONES8, True, False, o=100.6, sig=_sig())
    assert [e["action"] for e in ev] == ["enter", "exit"]
    assert ev[1]["kind"] == "i3" and ev[1]["i3_degenerate"] is True
    assert ev[1]["price"] == 104.9 and tw.pos == 0
    assert tw.exit_counters["i3_degenerate"] == 1


# --- structural / ATR stops -------------------------------------------------


def test_structural_stop_containment_and_gap_through_fills():
    tw = _twin(stop_mode="structural")
    entry = _enter_long(tw, _sig(stop_anchor=100.0, stop_src="closed[-1]"))
    assert entry["stop_px"] == 100.0 and entry["stop_kind"] == "structural"
    # containment touch fills AT the level (D3)
    ev = tw._position_step(300, 101.0, 99.8, 100.2, *NONES8, True, False, o=100.9)
    assert ev[0]["kind"] == "stop" and ev[0]["price"] == 100.0
    assert ev[0]["stop_kind"] == "structural"
    # gap-through fills at the bar OPEN (fresh position)
    tw2 = _twin(stop_mode="structural")
    _enter_long(tw2, _sig(stop_anchor=100.0, stop_src="closed[-1]"))
    ev = tw2._position_step(300, 99.5, 98.0, 98.5, *NONES8, True, False, o=99.2)
    assert ev[0]["kind"] == "stop" and ev[0]["price"] == 99.2


def test_stop_src_ts_emitted_on_entry_for_each_source():
    # TVB-26 audit LOW-4: stop_src_ts was implemented and reproduced but not
    # regression-bound -- a deletion or off-by-one could pass the suite.
    for src, src_ts, anchor in (
        ("closed[-1]", -3600, 100.0),
        ("closed[-2]", -7200, 99.5),
        ("developing", 0, 100.2),
    ):
        tw = _twin(stop_mode="structural")
        entry = _enter_long(tw, _sig(stop_anchor=anchor, stop_src=src, stop_src_ts=src_ts))
        assert entry["stop_px"] == anchor and entry["stop_kind"] == "structural"
        assert entry["stop_src"] == src and entry["stop_src_ts"] == src_ts


def test_stop_anchor_freeze_wins_over_redetected_values():
    # TVB-25 amendment: the FIRST detection's (anchor, src, src_ts) tuple is
    # frozen per signal identity; entry consumes the FROZEN tuple even if
    # the live Signal object carries drifted values.
    tw = _twin(stop_mode="structural")
    tw.pattern.key = 0
    tw._anchor_freeze_key = 0
    tw._anchor_freeze[(0, 1, "2-2u")] = (100.0, "closed[-1]", -3600)
    entry = _enter_long(tw, _sig(stop_anchor=101.0, stop_src="closed[-2]", stop_src_ts=-7200))
    assert entry["stop_px"] == 100.0
    assert entry["stop_src"] == "closed[-1]" and entry["stop_src_ts"] == -3600


def test_degenerate_anchor_falls_back_to_atr():
    tw = _twin(stop_mode="structural")
    tw.atr.value = 1.0
    entry = _enter_long(tw, _sig(stop_anchor=105.5, stop_src="closed[-1]"))  # profit side
    assert entry["stop_kind"] == "atr"
    assert abs(entry["stop_px"] - (104.91 - 3.0 * 1.0)) < 1e-9  # D2: fill - 3xATR
    assert tw.exit_counters["stop_degenerate_anchor"] == 1


def test_no_anchor_and_no_atr_means_no_stop_counted():
    tw = _twin(stop_mode="structural")
    entry = _enter_long(tw, _sig())  # no table row -> ATR fallback; ATR unseeded
    assert entry["stop_px"] is None and entry["stop_kind"] is None
    assert tw.exit_counters["stop_atr_unavailable"] == 1


def test_control_entry_gets_atr_stop():
    tw = Twin(TwinConfig(symbol="SYN", mintick=0.01, stop_mode="atr", bf_harvest_exit=False))
    tw.atr.value = 0.5
    tw.prev_ah, tw.prev_al = 104.9, 100.0
    ev = tw._position_step(0, 105.0, 100.4, 104.9, *NONES8, True, False, o=100.6)
    assert ev[0]["action"] == "enter" and ev[0]["stop_kind"] == "atr"
    assert abs(ev[0]["stop_px"] - (104.91 - 1.5)) < 1e-9
    ev = tw.replay_bar(300, 104.0, 104.2, 103.3, 103.5)
    assert ev[0]["kind"] == "stop" and abs(ev[0]["price"] - 103.41) < 1e-9


# --- tranche profiles -------------------------------------------------------


def test_p1_two_piece_bank_then_runner_bf():
    tw = _twin(tranche_profile="P1")
    entry = _enter_long(tw, _sig(ladder=[106.0, 108.0]))
    assert entry["tranches"] == [
        {"frac": 0.5, "level": 106.0, "label": "T1"},
        {"frac": 0.5, "label": "runner"},
    ]
    ev = tw._position_step(300, 106.2, 105.0, 105.8, *NONES8, True, False, o=105.1)
    assert [(e["kind"], e["frac"], e["tranche"]) for e in ev] == [("tgt", 0.5, "T1")]
    assert tw.pos == 1 and tw.runner_frac == 0.5
    # runner exits at the BF harvest touch
    ev = tw._position_step(
        600, 108.0, 105.5, 107.0, None, None, (107.5, 2), "D", None, None, None, None, True, False
    )
    assert [(e["kind"], e["frac"]) for e in ev] == [("bf", 0.5)]
    assert tw.pos == 0


def test_p2_bank_retrace_floor_breakeven_and_bf():
    tw = _twin(tranche_profile="P2")
    entry = _enter_long(tw, _sig(ladder=[105.5, 106.0, 107.0, 108.0, 109.0, 110.0]))
    plan = {t["label"]: t["frac"] for t in entry["tranches"]}
    assert plan == {"T2": 0.4, "T3": 0.2, "T4": 0.2, "T5": 0.1, "runner": 0.1}
    # bank T2 -> floor arms
    ev = tw._position_step(300, 106.3, 105.7, 106.1, *NONES8, True, False, o=105.8)
    assert [(e["kind"], e["tranche"]) for e in ev] == [("tgt", "T2")]
    assert tw.floor_armed and not tw.retrace_done
    # T1 retrace -> middles out at T1, runner survives with breakeven floor
    ev = tw._position_step(600, 105.8, 105.4, 105.6, *NONES8, True, False, o=105.7)
    assert [(e["kind"], e["tranche"], e["price"]) for e in ev] == [
        ("floor", "T3", 105.5),
        ("floor", "T4", 105.5),
        ("floor", "T5", 105.5),
    ]
    assert tw.runner_be_px == tw.entry_px and tw.runner_frac == 0.1
    # runner still harvests the BF touch (ruling A)
    ev = tw._position_step(
        900, 108.0, 105.6, 107.5, None, None, (107.8, 3), "W", None, None, None, None, True, False
    )
    assert [(e["kind"], e["frac"]) for e in ev] == [("bf", 0.1)]
    assert tw.pos == 0


def test_p2_breakeven_floor_protects_runner():
    tw = _twin(tranche_profile="P2")
    _enter_long(tw, _sig(ladder=[105.5, 106.0, 107.0, 108.0, 109.0, 110.0]))
    entry_px = tw.entry_px
    tw._position_step(300, 106.3, 105.7, 106.1, *NONES8, True, False, o=105.8)  # bank T2
    tw._position_step(600, 105.8, 105.4, 105.6, *NONES8, True, False, o=105.7)  # retrace
    ev = tw._position_step(900, 105.6, 104.5, 104.7, *NONES8, True, False, o=105.5)
    assert [(e["kind"], e["price"], e["frac"]) for e in ev] == [("be", entry_px, 0.1)]
    assert tw.pos == 0


def test_p2_same_bar_arm_and_fire():
    # one wide bar banks T2 AND touches T1 AND returns to entry: the floor
    # arms and fires, the middles exit at T1, the runner exits at breakeven
    tw = _twin(tranche_profile="P2")
    _enter_long(tw, _sig(ladder=[105.5, 106.0, 107.0, 108.0, 109.0, 110.0]))
    entry_px = tw.entry_px
    ev = tw._position_step(300, 106.5, 104.5, 105.0, *NONES8, True, False, o=105.2)
    got = [(e["kind"], e["tranche"]) for e in ev]
    assert got == [
        ("tgt", "T2"),
        ("floor", "T3"),
        ("floor", "T4"),
        ("floor", "T5"),
        ("be", "runner"),
    ]
    assert ev[-1]["price"] == entry_px and tw.pos == 0
    assert abs(sum(e["frac"] for e in ev) - 1.0) < 1e-9
    # D9 (TVB-25 audit F1): the bank->floor arm-and-fire bar IS a collision
    # bar -- the bar-start snapshot alone cannot see the just-armed floor
    assert tw.exit_counters["collision_bars"] == 1
    assert tw.collision_pairs == {"prot+tgt": 1}
    # D9 receipt (2026-08-26): the arm-and-fire prot candidate is priced
    (rcpt,) = tw.collision_receipts
    assert rcpt["classes"] == ["prot", "tgt"]
    assert rcpt["candidates"]["prot"]["px"] == 105.5
    assert rcpt["candidates"]["tgt"]["px"] == 106.0
    assert rcpt["executed"][0]["kind"] == "tgt"
    assert rcpt["delta_vs_first_fill_pct"]["prot"] < 0  # floor fill sits below the bank


def test_p2_bank_sweep_that_arms_an_empty_floor_is_not_a_collision():
    # TVB-28 audit MEDIUM-2, user-ruled 2026-08-26 (executable-only): one
    # wide bar banks EVERY middle tranche, so the floor arms with nothing
    # left to exit and the runner's breakeven is not touched. That is an
    # arming transition, not a protective-vs-target collision -- it counts
    # under floor_armed_inert and stays OUT of the D9 census.
    tw = _twin(tranche_profile="P2")
    _enter_long(tw, _sig(ladder=[105.5, 106.0, 107.0, 108.0, 109.0, 110.0]))
    entry_px = tw.entry_px
    ev = tw._position_step(300, 109.5, 105.4, 106.0, *NONES8, True, False, o=105.8)
    assert [(e["kind"], e["tranche"]) for e in ev] == [
        ("tgt", "T2"),
        ("tgt", "T3"),
        ("tgt", "T4"),
        ("tgt", "T5"),
    ]
    assert tw.pos == 1 and abs((tw.runner_frac or 0.0) - 0.1) < 1e-9  # runner rides
    assert tw.retrace_done and tw.runner_be_px == entry_px  # the floor DID arm
    assert tw.exit_counters["floor_armed_inert"] == 1
    assert tw.exit_counters["collision_bars"] == 0
    assert tw.collision_pairs == {} and tw.collision_receipts == []


def test_p2_short_ladder_folds_missing_rungs_into_runner():
    tw = _twin(tranche_profile="P2")
    entry = _enter_long(tw, _sig(ladder=[105.5, 106.0]))  # T1, T2 only
    plan = {t["label"]: t["frac"] for t in entry["tranches"]}
    assert plan["T2"] == 0.4
    assert abs(plan["runner"] - 0.6) < 1e-9  # 0.1 + folded T3/T4/T5
    tw2 = _twin(tranche_profile="P2")
    entry2 = _enter_long(tw2, _sig(ladder=[105.5]))  # no bankable rung at all
    plan2 = {t["label"]: t["frac"] for t in entry2["tranches"]}
    assert abs(plan2["runner"] - 1.0) < 1e-9 and tw2.tranches == []


def test_risk_exit_closes_all_remaining_tranches():
    tw = _twin(tranche_profile="P2", stop_mode="structural")
    _enter_long(tw, _sig(ladder=[105.5, 106.0, 107.0, 108.0, 109.0, 110.0], stop_anchor=100.0))
    tw._position_step(300, 106.3, 105.7, 106.1, *NONES8, True, False, o=105.8)  # bank T2
    ev = tw._position_step(600, 105.9, 99.5, 99.8, *NONES8, True, False, o=105.6)
    # risk-first: the stop closes ALL remaining tranches at its level (D5),
    # ahead of the armed T1 floor that the same bar also touches
    assert ev[0]["kind"] == "stop" and ev[0]["tranche"] == "all"
    assert abs(ev[0]["frac"] - 0.6) < 1e-9 and tw.pos == 0
    assert tw.exit_counters["collision_bars"] == 1


# --- X1 arming --------------------------------------------------------------


def test_x1_bf_gated_until_rung_reach_then_same_bar_fire():
    tw = _twin(bf_arm_rung=3)
    entry = _enter_long(tw, _sig(ladder=[106.0, 107.0, 108.0, 109.0]))
    assert entry["bf_arm_level"] == 108.0 and tw.bf_armed is False
    # BF candidate before rung-3 reach: no exit
    ev = tw._position_step(
        300, 107.5, 105.0, 107.0, None, None, (106.5, 2), "D", None, None, None, None, True, False
    )
    assert ev == [] and tw.pos == 1
    # reach + touch on the SAME bar arm-and-fire (amendment)
    ev = tw._position_step(
        600, 108.2, 106.0, 107.8, None, None, (107.0, 2), "D", None, None, None, None, True, False
    )
    assert [e["kind"] for e in ev] == ["bf"] and tw.pos == 0


def test_x1_short_ladder_never_arms():
    tw = _twin(bf_arm_rung=3)
    entry = _enter_long(tw, _sig(ladder=[106.0, 107.0]))
    assert entry["bf_arm_level"] is None
    ev = tw._position_step(
        300, 120.0, 105.0, 118.0, None, None, (110.0, 2), "D", None, None, None, None, True, False
    )
    assert ev == [] and tw.pos == 1  # declared structural consequence


# --- collision precedence + overlay identity --------------------------------


def test_stop_beats_target_on_collision_bar():
    tw = _twin(stop_mode="structural", exit_targets=1)
    _enter_long(tw, _sig(ladder=[106.0], stop_anchor=100.0))
    ev = tw._position_step(300, 106.5, 99.5, 100.2, *NONES8, True, False, o=105.0)
    assert [e["kind"] for e in ev] == ["stop"] and ev[0]["price"] == 100.0
    assert tw.exit_counters["collision_bars"] == 1
    # D9 receipt (2026-08-26): both classes priced beside the executed fill
    (rcpt,) = tw.collision_receipts
    assert rcpt["classes"] == ["stop", "tgt"]
    assert rcpt["candidates"]["stop"]["px"] == 100.0
    assert rcpt["candidates"]["tgt"]["px"] == 106.0
    assert rcpt["executed"] == [{"kind": "stop", "price": 100.0, "frac": None}]
    assert rcpt["delta_vs_first_fill_pct"]["stop"] == 0.0
    assert rcpt["delta_vs_first_fill_pct"]["tgt"] > 0  # the road not taken paid more


def test_collision_receipt_prices_i3_close_vs_stop_level():
    # The TVB-26/27 audit counterexample class, pinned as a regression: i3
    # fills at the 5m CLOSE while the stop fills at its LEVEL, so the ruled
    # i3-first order can book the BETTER fill. Risk-first is a priority
    # CONVENTION (user re-ruling 2026-08-24), not a per-bar pessimism
    # guarantee -- the receipt prices the road not taken.
    tw = _twin(intrabar3_exit=True, stop_mode="structural")
    _prime_pattern(tw, key=0, prev_l=100.3)  # i3 level = 100.3
    _enter_long(tw, _sig(stop_anchor=100.3, stop_src="closed[-1]"))
    ev = tw._position_step(300, 105.0, 100.2, 104.9, *NONES8, True, False, o=104.5)
    assert [e["kind"] for e in ev] == ["i3"] and ev[0]["price"] == 104.9
    (rcpt,) = tw.collision_receipts
    assert rcpt["classes"] == ["i3", "stop"]
    assert rcpt["candidates"]["i3"]["px"] == 104.9
    assert rcpt["candidates"]["stop"]["px"] == 100.3
    assert rcpt["executed"][0]["kind"] == "i3"
    # the stop would have exited ~4.4pp WORSE than the executed i3 close
    assert rcpt["delta_vs_first_fill_pct"]["stop"] < -4.0


def test_overlay_arm_without_trigger_matches_base_target_exit():
    # D1+i3 minus an i3 event must be decision-identical to D1: the tgt
    # containment exit fills at the level exactly as the incumbent race
    tw = _twin(intrabar3_exit=True, exit_targets=1)
    _prime_pattern(tw, key=0, prev_l=99.0)
    _enter_long(tw, _sig(ladder=[106.0]))
    ev = tw._position_step(300, 106.2, 105.0, 105.8, *NONES8, True, False, o=105.1)
    assert [(e["kind"], e["price"]) for e in ev] == [("tgt", 106.0)]
