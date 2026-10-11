"""Hand vectors for the TVB-35 macro-regime receipt (analysis/regime/receipt.py).

Codex TVB-35 audit F6: at an instant t only COMPLETED 60m bars are known (a bar
is known at open + 60 minutes). F7: the whipsaw flag and its components are
three-state (true / false / unknown); unknown is never coerced to false.
Bars are [open_ts, open, high, low, close]."""

from analysis.regime.receipt import FRESH_S, H60, REFS, Ref, labels_at, tri, tri_or

DAY = 86400
D0 = (1_790_000_000 // DAY) * DAY  # an arbitrary UTC midnight


def probe_ref() -> Ref:
    """The audit's synthetic hour: the day opens at 99; the hour that opens at
    D0 opens at 101, trades 110 / 90 and closes at 90. The prior day is 105 / 95."""
    return Ref(
        "X",
        h=[
            [D0 - H60, 100, 101, 99, 100],
            [D0, 101, 110, 90, 90],
        ],
        d=[[D0 - DAY, 100, 105, 95, 100], [D0, 99, 110, 90, 90]],
        w=[[D0 - 3 * DAY, 98, 110, 90, 90]],
    )


def test_hour_open_instant_reads_previous_hour_close():
    r = probe_ref()
    assert r.price_at(D0) == 100  # not 90: the hour opening at D0 is still forming
    assert r.dot(D0, "D") == "up"  # 100 vs the day's open 99 (the look-ahead read "down")
    assert r.dot(D0, "W") == "up"


def test_exact_hour_close_reads_that_hour():
    r = probe_ref()
    assert r.price_at(D0 + H60 - 1) == 100
    assert r.price_at(D0 + H60) == 90
    assert r.dot(D0 + H60, "D") == "down"


def test_running_day_excludes_forming_hour():
    r = Ref(
        "X",
        h=[
            [D0 - H60, 100, 101, 99, 100],
            [D0, 100, 104, 96, 100],
            [D0 + H60, 100, 110, 90, 100],
        ],
        d=[[D0 - DAY, 100, 105, 95, 100], [D0, 100, 110, 90, 100]],
        w=[[D0 - 3 * DAY, 100, 110, 90, 100]],
    )
    # The day's open instant: no hour of the day completed yet -> unknown.
    assert r.running_day(D0) is None
    # Mid-way through the second hour: only the first hour (104 / 96) is known.
    rd = r.running_day(D0 + H60 + 1800)
    assert (rd["run_high"], rd["run_low"]) == (104, 96)
    assert rd["outside"] is False and rd["inside"] is True
    # Once the second hour closes its 110 / 90 range is known: outside day.
    rd = r.running_day(D0 + 2 * H60)
    assert (rd["run_high"], rd["run_low"]) == (110, 90)
    assert rd["outside"] is True


def test_freshness_window_applies_to_dots_and_running_day():
    r = probe_ref()
    last_close = D0 + H60
    assert r.dot(last_close + FRESH_S, "D") == "down"
    assert r.running_day(last_close + FRESH_S) is not None
    assert r.dot(last_close + FRESH_S + 1, "D") == "closed"
    assert r.price_at(last_close + FRESH_S + 1) is None
    assert r.running_day(last_close + FRESH_S + 1) is None


def test_no_completed_history_reads_na():
    r = probe_ref()
    assert r.dot(D0 - 30 * 60, "D") == "na"  # the first hour has not completed yet
    assert Ref("X", h=[], d=[], w=[]).dot(D0, "D") == "na"


def test_period_stamped_before_first_trade_is_not_yet_known():
    # US10Y shape: the daily bar is stamped 23:00, its first 60m bar opens 00:00
    # at 4.80 (the daily open); the last pre-break bar closed 22:00 at 4.78.
    r = Ref(
        "US10Y",
        h=[[D0 - 3 * H60, 4.78, 4.78, 4.78, 4.78], [D0, 4.80, 4.81, 4.79, 4.81]],
        d=[[D0 - DAY - H60, 4.70, 4.79, 4.69, 4.78], [D0 - H60, 4.80, 4.81, 4.79, 4.81]],
        w=[[D0 - 3 * DAY, 4.70, 4.81, 4.69, 4.81]],
    )
    assert r.dot(D0 - H60 + 1800, "D") == "closed"  # 23:30: the 4.80 open has not printed
    assert r.dot(D0 + 1800, "D") == "closed"  # 00:30: stale, the 00:00 hour still forming
    assert r.dot(D0 + H60, "D") == "up"  # 01:00: 4.81 close vs the 4.80 open


def test_tri_or_truth_table():
    assert tri_or(True, None) is True
    assert tri_or(None, True) is True
    assert tri_or(False, None) is None
    assert tri_or(None, None) is None
    assert tri_or(False, False) is False
    assert [tri(v) for v in (True, False, None)] == ["true", "false", "unknown"]


def _empty_refs() -> dict:
    return {k: Ref(k, h=[], d=[], w=[]) for k in REFS}


def test_spx_false_btc_unavailable_whipsaw_unknown():
    refs = _empty_refs()
    refs["SPX"] = Ref(
        "SPX",
        h=[[D0, 100, 104, 96, 100], [D0 + H60, 100, 103, 97, 101]],
        d=[[D0 - DAY, 100, 105, 95, 100], [D0, 100, 104, 96, 101]],
        w=[[D0 - 3 * DAY, 100, 105, 95, 101]],
    )
    lab = labels_at(refs, D0 + 2 * H60)
    assert lab["SPX_outside"] is False
    assert lab["BTCUSD_outside"] is None
    assert lab["whipsaw"] is None  # (false, unknown) -> unknown, never false


def test_macro_state_separates_unavailable_from_disagreement():
    refs = _empty_refs()
    up = [[D0, 100, 101, 99, 101]]
    down = [[D0, 100, 101, 99, 99]]
    day = [[D0 - DAY, 100, 105, 95, 100], [D0, 100, 101, 99, 100]]
    week = [[D0 - 3 * DAY, 100, 105, 95, 100]]
    t = D0 + H60
    refs["DXY"] = Ref("DXY", h=up, d=day, w=week)
    lab = labels_at(refs, t)  # 10-year has no history
    assert (lab["macro_dir"], lab["macro_state"]) == ("mixed", "unavailable")
    refs["US10Y"] = Ref("US10Y", h=down, d=day, w=week)
    lab = labels_at(refs, t)
    assert (lab["macro_dir"], lab["macro_state"]) == ("mixed", "mixed_available")
    refs["US10Y"] = Ref("US10Y", h=up, d=day, w=week)
    lab = labels_at(refs, t)
    assert (lab["macro_dir"], lab["macro_state"]) == ("headwind", "directional")
