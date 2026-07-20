"""TVB-15 paper twin engine tests.

Parity: the engine's Pool (uncapped) must reproduce the committed TVB-14
acceptance fixture byte-for-byte on the committed DRAM 1h bars. The golden
files are generated straight from the fixture script (no transcription):
    uv run python analysis/tvb14_bf_pool_fixture.py W  > tests/golden/tvb15_pool_W.txt
    uv run python analysis/tvb14_bf_pool_fixture.py D  > tests/golden/tvb15_pool_D.txt
    uv run python analysis/tvb14_bf_pool_fixture.py 12h > tests/golden/tvb15_pool_12h.txt

Mechanics: position-machine exit precedence (bf > brk > flip), R10 trigger
strictness, the corrected arm clock, same-bar edges, direction-relative
eligibility, pool_cap eviction. Boundary vectors are constructed per the
strat-methodology skill section 7 (mandated unit vectors, not market data);
everything bar-series-shaped uses the committed venue bars.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from analysis.paper.engine import (
    DAY,
    Pool,
    Twin,
    TwinConfig,
    key_12h,
    key_1d,
    key_1mo,
    key_1w,
)

REPO = Path(__file__).resolve().parents[1]
GOLDEN = REPO / "tests" / "golden"
BARS = [
    [int(b[0]), b[1], b[2], b[3], b[4]]
    for b in json.loads((REPO / "analysis" / "reference" / "tvb14_dram_1h_hl.json").read_text())[
        "bars"
    ]
]

POOLS = {"W": (key_1w, 7 * DAY), "D": (key_1d, DAY), "12h": (key_12h, 12 * 3600)}


def ds(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%m-%d %H:%M")


def fixture_format(tf, pool, now_ts, n_max=6):
    """Render a Pool exactly like analysis/tvb14_bf_pool_fixture.py prints."""
    out = [
        f"{tf}-pool, data through {ds(now_ts)} UTC (N_MAX={n_max}): "
        f"{len(pool.formations)} formations"
    ]
    for i, f in enumerate(pool.formations):
        out.append(f"  F{i + 1} born {ds(f.born)} N={f.N}")
        for label, side in (("lower", f.lo), ("upper", f.up)):
            st = side.state
            if st in ("consumed", "crossed"):
                st = f"{st} {ds(side.state_ts)}"
            out.append(
                f"     {label} {side.v1:.3f}@{ds(side.t1)} -> {side.v2:.3f}@{ds(side.t2)}"
                f" | now {side.val(now_ts):.2f} | {st}"
            )
    return out


# ---------------------------- pool parity ------------------------------------

# Known fixture-ordering approximations (TVB-15 finding, 2026-07-20): the
# committed fixture applies supersede in a second pass over already-built
# formations, so a side touched BETWEEN its birth and the superseding
# formation's birth still prints "superseded" there. Pine is interleaved --
# the touch consumes the side first (state 0 -> 1), and the later sweep's
# supersede only relabels still-alive sides (pine/tfc_bf_watch.pine:234).
# The engine matches Pine; both states are retired, so exits are unaffected.
FIXTURE_SUPERSEDE_SHADOWS = {
    ("12h", 68): "consumed 06-04 14:00",  # F23 lower; superseder F24 born 06-05 00:00
    ("12h", 116): "consumed 06-29 13:00",  # F39 lower; superseder F40 born 06-30 00:00
}


@pytest.mark.parametrize("tf", ["W", "D", "12h"])
def test_pool_parity_vs_fixture_golden(tf):
    key_fn, period_s = POOLS[tf]
    pool = Pool(tf, key_fn, period_s, n_max=6, min_sep=1.0, pool_cap=None)
    for ts, _o, h, l, c in BARS:
        pool.process_bar(ts, h, l, c, pos=0, entry_px=None)
    got = fixture_format(tf, pool, BARS[-1][0])
    want = (GOLDEN / f"tvb15_pool_{tf}.txt").read_text().splitlines()
    for (etf, idx), engine_state in FIXTURE_SUPERSEDE_SHADOWS.items():
        if etf == tf:
            assert want[idx].endswith("| superseded")
            want[idx] = want[idx].replace("| superseded", f"| {engine_state}")
    assert got == want


def test_supersede_shadow_invariant():
    """Each golden exception must be a touch that PRECEDES the superseding
    formation's birth, on a side sharing that formation's left anchor --
    i.e. exactly the case where Pine's interleaved order consumes first."""
    key_fn, period_s = POOLS["12h"]
    pool = Pool("12h", key_fn, period_s, pool_cap=None)
    for ts, _o, h, l, c in BARS:
        pool.process_bar(ts, h, l, c, 0, None)
    fs = pool.formations
    for shadow_i, superseder_i in ((22, 23), (38, 39)):  # F23/F24, F39/F40
        shadowed, superseder = fs[shadow_i], fs[superseder_i]
        assert shadowed.lo.state == "consumed"
        assert shadowed.lo.state_ts < superseder.born
        assert shadowed.lo.anchors()[:2] == superseder.lo.anchors()[:2]


def test_pool_cap_eviction_bounds_the_pool():
    key_fn, period_s = POOLS["12h"]
    capped = Pool("12h", key_fn, period_s, pool_cap=2)
    uncapped = Pool("12h", key_fn, period_s, pool_cap=None)
    for ts, _o, h, l, c in BARS:
        capped.process_bar(ts, h, l, c, 0, None)
        uncapped.process_bar(ts, h, l, c, 0, None)
    assert len(uncapped.formations) > 2
    assert len(capped.formations) == 2
    borns = [f.born for f in capped.formations]
    assert borns == sorted(borns)


# --------------------------- calendar keys -----------------------------------


def test_calendar_keys():
    wed = int(datetime(2026, 7, 15, 13, 37, tzinfo=timezone.utc).timestamp())
    assert key_1w(wed) == int(datetime(2026, 7, 13, tzinfo=timezone.utc).timestamp())
    assert key_1mo(wed) == int(datetime(2026, 7, 1, tzinfo=timezone.utc).timestamp())
    assert key_1d(wed) == int(datetime(2026, 7, 15, tzinfo=timezone.utc).timestamp())
    assert key_12h(wed) == int(datetime(2026, 7, 15, 12, tzinfo=timezone.utc).timestamp())


def test_gate_seed_matches_reference_scan():
    twin = Twin(TwinConfig(symbol="T", mintick=0.001))
    twin.seed_gates(BARS)
    # independent reference scan for each gate TF
    for name, kf in (("D", key_1d), ("W", key_1w), ("M", key_1mo)):
        last_key, want_open = None, None
        for ts, o, *_ in BARS:
            k = kf(int(ts))
            if k != last_key:
                last_key, want_open = k, o
        assert twin.gate_open[name] == want_open


# ---------------------- pool scan edge semantics -----------------------------


def _mini_pool():
    """One plain scenario-3 formation from three daily candles (real prices
    not required -- pool mechanics vectors). Lower line: 5@d0 -> 3@d1
    (value 1.0 at d2); upper line: 10@d0 -> 12@d1 (value 14.0 at d2)."""
    p = Pool("D", key_1d, DAY, pool_cap=None)
    p.process_bar(0, 10.0, 5.0, 7.0, 0, None)
    p.process_bar(DAY, 12.0, 3.0, 11.0, 0, None)
    return p


def test_touch_while_flat_consumes_silently():
    p = _mini_pool()
    r = p.process_bar(2 * DAY, 2.0, 0.5, 1.5, pos=0, entry_px=None)
    assert len(p.formations) == 1
    f = p.formations[0]
    assert (f.lo.t1, f.lo.v1, f.lo.t2, f.lo.v2) == (0, 5.0, DAY, 3.0)
    assert r["xs"] is None and r["xl"] is None
    assert f.lo.state == "consumed" and f.lo.state_ts == 2 * DAY
    assert f.up.state == "alive"


def test_direction_relative_eligibility():
    # line value 1.0 at d2; a short entered BELOW the line never harvests it
    p = _mini_pool()
    r = p.process_bar(2 * DAY, 2.0, 0.5, 1.5, pos=-1, entry_px=0.8)
    assert r["xs"] is None
    assert p.formations[0].lo.state == "consumed"
    # same touch with entry above the line harvests at the line value
    p2 = _mini_pool()
    r2 = p2.process_bar(2 * DAY, 2.0, 0.5, 1.5, pos=-1, entry_px=5.0)
    assert r2["xs"] == (1.0, 1)


def test_gap_through_crossed_and_break_candidate():
    # bar entirely below the lower line: no touch, confirmed close beyond
    p = _mini_pool()
    r = p.process_bar(2 * DAY, 0.9, 0.4, 0.6, pos=1, entry_px=14.5)
    assert r["brk_lo"] == 1.0
    assert p.formations[0].lo.state == "crossed"


# ------------------------- position machine ----------------------------------


def _twin(**kw):
    cfg = TwinConfig(symbol="TEST", mintick=0.01, **kw)
    return Twin(cfg)


def _step(
    twin,
    ts=1000,
    h=0.0,
    l=0.0,
    c=0.0,
    xs=None,
    xs_tf=None,
    xl=None,
    xl_tf=None,
    brk_lo=None,
    brk_lo_tf=None,
    brk_up=None,
    brk_up_tf=None,
    gate_up=False,
    gate_dn=False,
):
    return twin._position_step(
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


def test_bf_beats_brk_and_flip_and_blocks_reentry():
    twin = _twin()
    twin.pos, twin.entry_px, twin.entry_ts = -1, 100.0, 0
    twin.seed_arm(80.0, 70.0)  # h below would re-trigger long if not blocked
    ev = _step(
        twin,
        h=105.0,
        l=89.0,
        c=95.0,
        xs=(90.0, 2),
        xs_tf="D",
        brk_up=96.0,
        brk_up_tf="12h",
        gate_up=True,
    )
    assert [e["action"] for e in ev] == ["exit"]
    assert ev[0]["kind"] == "bf" and ev[0]["price"] == 90.0 and ev[0]["line_tf"] == "D"
    assert ev[0]["pnl_pct"] == pytest.approx(10.0)
    assert twin.pos == 0  # and no same-bar re-entry despite gate_up + break


def test_brk_exits_at_confirmed_close():
    twin = _twin()
    twin.pos, twin.entry_px, twin.entry_ts = 1, 100.0, 0
    ev = _step(twin, c=94.8, brk_lo=95.0, brk_lo_tf="D")
    assert ev[0]["kind"] == "brk" and ev[0]["price"] == 94.8
    assert ev[0]["pnl_pct"] == pytest.approx(-5.2)


def test_flip_backstop_and_its_toggle():
    twin = _twin()
    twin.pos, twin.entry_px, twin.entry_ts = 1, 100.0, 0
    ev = _step(twin, c=97.0, gate_dn=True)
    assert ev[0]["kind"] == "flip" and ev[0]["price"] == 97.0
    twin2 = _twin(flip_backstop=False)
    twin2.pos, twin2.entry_px, twin2.entry_ts = 1, 100.0, 0
    assert _step(twin2, c=97.0, gate_dn=True) == []


def test_trigger_strictness_r10():
    # equality never breaks: h == prev_ah does not reach prev_ah + mintick
    twin = _twin()
    twin.seed_arm(104.00, 100.00)
    assert _step(twin, h=104.00, l=101.0, gate_up=True) == []
    ev = _step(twin, h=104.01, l=101.0, gate_up=True)
    assert ev[0]["action"] == "enter" and ev[0]["price"] == pytest.approx(104.01)
    # short mirror
    twin2 = _twin()
    twin2.seed_arm(104.00, 100.00)
    assert _step(twin2, h=103.0, l=100.00, gate_dn=True) == []
    ev2 = _step(twin2, h=103.0, l=99.99, gate_dn=True)
    assert ev2[0]["dir"] == "short" and ev2[0]["price"] == pytest.approx(99.99)


def test_long_checked_before_short():
    twin = _twin()
    twin.seed_arm(104.00, 100.00)
    ev = _step(twin, h=104.5, l=99.5, gate_up=True, gate_dn=True)
    assert len(ev) == 1 and ev[0]["dir"] == "long"


def test_corrected_arm_clock_rolls_after_entry():
    """5m bars, 15m arm: the roll at the arm-last bar happens AFTER entry
    evaluation, so entries on every child bar test the PRIOR completed
    period's extremes (audit-C1 clock)."""
    twin = _twin()
    twin.seed_arm(104.00, 100.00)
    # first bar of the 15m period: gate opens seed from this bar's open (50)
    ev0 = twin.replay_bar(0, 50.0, 104.00, 101.0, 60.0)
    assert ev0 == []  # equality never breaks
    ev1 = twin.replay_bar(300, 60.0, 104.01, 101.0, 60.0)
    assert ev1[0]["action"] == "enter" and ev1[0]["price"] == pytest.approx(104.01)
    # arm-last bar: new period high 105 must only become the reference AFTER
    # this bar (rollback semantics)
    twin.replay_bar(600, 60.0, 105.0, 101.0, 60.0)
    assert twin.prev_ah == 105.0 and twin.prev_al == 101.0
    assert twin.pos == 1  # still long; no phantom signals
