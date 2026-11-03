"""The matched-pair study (analysis/pairs, TVB-44): the variables on hand vectors with their bar
windows strictly before the entry session, the month side from the unit's own trigger, the cells
and terciles, the reach outcome over the units with a target, the "other" group, the pooled
reading on a frame with a known split, the owner's theme rule."""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd

from analysis.domino.census import DAY, use_calendar
from analysis.pairs import cells as X
from analysis.pairs import features as F


def ms(y, m, d):
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1000)


def bars(
    start: int, ranges: list[float], base: float = 100.0, vol: list[float] | None = None
) -> list[dict]:
    """Daily bars with the given high-low ranges around a flat close; the volume given or 1,000."""
    out = []
    for k, r in enumerate(ranges):
        v = vol[k] if vol else 1000.0
        out.append(
            {
                "t": start + k * DAY,
                "o": base,
                "h": base + r / 2,
                "l": base - r / 2,
                "c": base,
                "v": v,
            }
        )
    return out


def test_the_declared_list_as_built():
    assert "liquid" not in F.VARS and "stack" not in F.VARS  # retrospective; outcome-side
    assert "ladder_len" in F.CATEGORY and "near_tf" in F.CATEGORY and "dex" in F.CATEGORY
    assert set(F.BINARY_HIGH) == {"flag", "dex"}


def test_setup_bar_against_normal_reads_r_pct_over_the_bars_strictly_before_the_entry_session():
    # 20 quiet days of range 1, a setup bar of range 3 (an expansion), the entry day of range 9
    # (which must not leak in), and a volume spike on the setup bar
    daily = bars(ms(2026, 1, 1), [1.0] * 20 + [3.0, 9.0], vol=[1000.0] * 20 + [5000.0, 99.0])
    tv = F.TapeVars(daily, "D")
    i = 21  # the entry session
    assert tv.setup_index(i) == 20
    level = daily[20]["h"]
    r_pct = 3.0 / level * 100  # the engine's setup-bar size: percent of the trigger
    v = tv.at(i, "up", level, r_pct)
    assert abs(v["v_setup_vs_norm"] - r_pct / 1.0) < 1e-9  # r_pct against a normal of 1
    assert abs(v["v_runup"] - 1.0) < 1e-9  # the three bars before the setup were normal
    assert abs(v["v_vol_vs_norm"] - 5.0) < 1e-9
    assert tv.at(i, "up", level, None)["v_setup_vs_norm"] is None  # no r_pct, no reading
    # a compression: the setup bar at range 0.5 after 20 of range 1, with the 3 before it at 2 (a run-up)
    daily2 = bars(ms(2026, 1, 1), [1.0] * 17 + [2.0] * 3 + [0.5, 1.0])
    level2 = daily2[20]["h"]
    v2 = F.TapeVars(daily2, "D").at(21, "up", level2, 0.5 / level2 * 100)
    norm = (17 * 1.0 + 3 * 2.0) / 20
    assert abs(v2["v_setup_vs_norm"] - (0.5 / level2 * 100) / norm) < 1e-9
    assert abs(v2["v_runup"] - 2.0 / norm) < 1e-9
    # too few bars behind the setup bar: absent, never filled
    short = bars(ms(2026, 1, 1), [1.0] * 5)
    assert F.TapeVars(short, "D").at(4, "up", 100.5, 1.0)["v_setup_vs_norm"] is None


def test_distance_travelled_is_from_the_20_bar_low_for_a_long_and_high_for_a_short():
    # a rising tape: closes 100, 101, ... 120; ranges 1 (so the 20-bar average range in price is 1)
    daily = [
        {
            "t": ms(2026, 1, 1) + k * DAY,
            "o": 100.0 + k,
            "h": 100.5 + k,
            "l": 99.5 + k,
            "c": 100.0 + k,
            "v": 1.0,
        }
        for k in range(22)
    ]
    tv = F.TapeVars(daily, "D")
    i = 21
    s = 20
    low20 = min(b["l"] for b in daily[s - 19 : s + 1])  # the 20 bars ending WITH the setup bar
    high20 = max(b["h"] for b in daily[s - 19 : s + 1])
    level_long = daily[s]["h"]
    v = tv.at(i, "up", level_long, 1.0)
    assert abs(v["v_travel"] - (level_long - low20) / 1.0) < 1e-9  # late: 20 ranges above the low
    level_short = daily[s]["l"]
    v2 = tv.at(i, "down", level_short, 1.0)
    assert (
        abs(v2["v_travel"] - (high20 - level_short) / 1.0) < 1e-9
    )  # early for a short: one range below the high


def test_weekly_units_read_the_bucket_before_the_entry_week_and_their_own_month_side():
    # 8 weeks of daily bars from a Monday; week 7's bucket is the setup bar of a unit entered in week 8
    mon = ms(2026, 9, 7)
    daily = bars(mon, [1.0] * 56)
    for k in range(49, 56):  # week 8 (the entry week) is wild, it must not leak
        daily[k]["h"], daily[k]["l"] = 110.0, 90.0
    for k in range(42, 49):  # week 7, the setup bar: a 4-point weekly range
        daily[k]["h"], daily[k]["l"] = 102.0, 98.0
    tv = F.TapeVars(daily, "W")
    i = 52  # a Friday of week 8
    s = tv.setup_index(i)
    assert tv.bars[s]["t"] == daily[42]["t"] and tv.bars[s]["h"] == 102.0
    # the normal range needs 20 weekly bars behind the setup week: only 6 here, so absent
    assert tv.at(i, "up", 102.0, 4.0)["v_setup_vs_norm"] is None
    # the month side from the UNIT'S OWN trigger, on a tape whose first complete month is
    # September (the census drops the partial August bucket): October 2026 opens at the tape's
    # flat 100; a weekly long whose trigger is 102 is with the month, a short at 102 against it
    mdaily = bars(ms(2026, 8, 31), [1.0] * 70)
    oct_i = next(k for k, b in enumerate(mdaily) if F.date_of(b["t"]).startswith("2026-10"))
    assert F.month_side(mdaily, oct_i + 3, 102.0, "up") == "with"
    assert F.month_side(mdaily, oct_i + 3, 102.0, "down") == "against"
    assert F.month_side(mdaily, oct_i + 3, 100.0, "up") == "against"  # equality = against
    # September is the first month the census keeps: no month before it, unknown (the engine's rule)
    assert F.month_side(mdaily, 5, 102.0, "up") == "unknown"


def test_room_in_r_week_position_weekday_and_the_index_state():
    assert abs(F.room_r(100.0, 103.0, 1.5) - 2.0) < 1e-9  # 3% of room over a 1.5% setup bar
    assert F.room_r(100.0, None, 1.5) is None and F.room_r(100.0, 103.0, 0.0) is None
    assert F.weekday_of("2026-09-07") == "Mon" and F.weekday_of("2026-09-13") == "Sun"
    # a session week of Monday to Friday, then a holiday week of four
    mon = ms(2026, 9, 7)
    daily = [b for k, b in enumerate(bars(mon, [1.0] * 14)) if k % 7 < 5 and k != 7]
    with use_calendar("session"):
        assert (
            F.week_position(daily, 0) == "first"
            and F.week_position(daily, 2) == "middle"
            and F.week_position(daily, 4) == "last"
        )
        assert (
            F.week_position(daily, 5) == "first"
        )  # the Tuesday after a Monday holiday opens its week
    # bitcoin: the previous session green and above its week's open; the entry day itself never read
    btc = bars(mon, [1.0] * 10)
    btc[1]["c"], btc[1]["o"] = (
        101.0,
        100.0,
    )  # Tuesday green, closes above Monday's open (the week's open)
    btc[2]["c"], btc[2]["o"] = 99.0, 100.0  # Wednesday red, below the week's open
    ix = F.IndexState(btc)
    assert ix.at("2026-09-09") == "green-above"  # Wednesday's unit reads Tuesday
    assert ix.at("2026-09-10") == "red-below"  # Thursday's unit reads Wednesday
    assert ix.at("2026-09-07") is None  # no previous session in the tape
    # the card's categories: the ladder's depth as a word, the nearest level's timeframe, none when absent
    cv = F.card_vars(
        {
            "r_pct": 1.5,
            "level": 100.0,
            "t1": 103.0,
            "ladder_len": 2.0,
            "near_tf": float("nan"),
            "cls": "plain",
            "anchor": "ladder",
            "flag": "none",
            "dex": "main",
        }
    )
    assert cv["ladder_len"] == "2" and cv["near_tf"] == "none" and "liquid" not in cv


def _frame(n_per: int = 300) -> pd.DataFrame:
    """Two cells; in each, units in the top third of `v_travel` reach T1 80% of the time and the
    bottom third 20%, the middle 50%; `ret_C` follows the same split; a category `flag` with the
    flagged units reaching 70% against 40%. Every unit has a target."""
    rng = np.random.default_rng(7)
    rows = []
    for cell in ("reversal", "continuation"):
        for k in range(n_per):
            third = k * 3 // n_per
            p = (0.2, 0.5, 0.8)[third]
            hit = rng.random() < p
            flag = "third" if k % 2 == 0 else "none"
            rows.append(
                {
                    "kind": cell,
                    "tf": "D",
                    "direction": "up",
                    "w_support": "with",
                    "m_support": None,
                    "v_travel": float(k) + rng.random() * 0.1,
                    "flag": flag,
                    "t1": 101.0,
                    "reached1": hit,
                    "ret_C": (1.0 if hit else -1.0) + rng.normal(0, 0.1),
                    "ret_D": 0.5 if hit else -0.5,
                }
            )
    return pd.DataFrame(rows)


def test_terciles_are_cut_inside_each_cell_and_the_pooled_reading_recovers_a_known_split():
    d = X.prepare(_frame())
    assert set(d["m_support"]) == {"unknown"} and d["has_t1"].all()
    t = X.tercile(d, "v_travel")
    assert t.value_counts().to_dict() == {"low": 200, "mid": 200, "high": 200}
    assert set(t[d["kind"] == "reversal"].value_counts().values) == {100}
    r = X.reading(d, "v_travel", min_n=200)
    assert (
        r["cells_read"] == 2 and r["units_read"] == 600 and r["absent"] == 0 and r["other"] is None
    )
    p = r["pooled"]["reach"]
    assert 0.45 < p["diff"] < 0.75 and p["lo"] > 0  # about +60 points, clear of zero
    assert abs(r["pooled"]["has_t1"]["diff"]) < 1e-9  # every unit has a target: no difference
    assert r["pooled"]["C"]["diff"] > 0.8 and r["pooled"]["D"]["lo"] > 0
    assert r["standardized"]["high"]["reach"] > r["standardized"]["low"]["reach"]
    assert r["standardized"]["high"]["has_t1"] == 1.0
    # a cell below the minimum is not read into the pooled difference but is shown as "other"
    small = X.reading(d, "v_travel", min_n=301)
    assert small["cells_read"] == 0 and small["pooled"]["reach"]["cells"] == 0
    assert small["other"]["cells"] == 2 and small["other"]["n"] == 600
    assert (
        small["other"]["levels"]["high"]["reach"]["p"]
        > small["other"]["levels"]["low"]["reach"]["p"]
    )
    # a category with no declared high side reads per level only
    assert X.high_low("anchor", ["ladder", "anchor"]) is None
    assert X.high_low("flag", ["none", "third"]) == (["third"], ["none"])


def test_reach_is_read_over_the_units_with_a_target_and_the_missing_target_is_its_own_fact():
    """The in-session Codex pass: the engine encodes "no target exists" as not reached, so a
    variable that goes with having no target read as "reaches less". The reach outcome is now
    conditioned on a target existing; the share with a target is read beside it."""
    d = _frame()
    # the top third loses its targets on half its units: those units are not "not reached"
    top = d.index[(d.groupby("kind").cumcount() >= 200) & (d.index % 2 == 0)]
    d.loc[top, "t1"] = np.nan
    d.loc[top, "reached1"] = False  # the engine's encoding
    pr = X.prepare(d)
    assert pr["reached1"].isna().sum() == len(top) and pr["has_t1"].sum() == 600 - len(top)
    r = X.reading(pr, "v_travel", min_n=200)
    assert (
        r["pooled"]["has_t1"]["diff"] < -0.4 and r["pooled"]["has_t1"]["hi"] < 0
    )  # the top third has fewer targets
    assert r["pooled"]["reach"]["diff"] > 0.45  # and still reaches the ones it has
    assert 0.45 < r["standardized"]["high"]["has_t1"] < 0.55
    # an all-missing book level is absent, not zero
    d2 = _frame(30)
    d2.loc[d2.index[d2.groupby("kind").cumcount() >= 20], "ret_C"] = np.nan
    pr2 = X.prepare(d2)
    assert len(pr2) == 40  # the units without an exit-only outcome are dropped
    r2 = X.reading(pr2, "v_travel", min_n=10)
    assert (
        "high" not in r2["standardized"]
        or not np.isfinite(r2["standardized"]["high"]["C"])
        or r2["standardized"]["high"]["n"]
    )


def test_theme_rule_needs_the_same_clear_direction_on_crypto_and_an_es_day():
    def rd(diff, clear):
        half = 0.05 if clear else 0.5
        return {
            "v_travel": {
                "pooled": {
                    "reach": {"cells": 2, "diff": diff, "lo": diff - half, "hi": diff + half},
                    "has_t1": {"cells": 2, "diff": -diff, "lo": -diff - half, "hi": -diff + half},
                }
            }
        }

    by = {
        "crypto": rd(0.3, True),
        "es_globex_clean": rd(-0.2, True),
        "es_rth_clean": rd(0.25, True),
    }
    th = X.themes(by, "crypto", ("es_globex_clean", "es_rth_clean"))
    assert th["v_travel"]["theme"] and th["v_travel"]["with"] == "es_rth_clean"
    assert th["v_travel"]["has_t1"]["crypto"]["sign"] == -1  # reported beside, not part of the rule
    by2 = {
        "crypto": rd(0.3, True),
        "es_globex_clean": rd(0.2, False),
        "es_rth_clean": rd(-0.3, True),
    }
    assert not X.themes(by2, "crypto", ("es_globex_clean", "es_rth_clean"))["v_travel"]["theme"]
    by3 = {
        "crypto": rd(0.3, False),
        "es_globex_clean": rd(0.3, True),
        "es_rth_clean": rd(0.3, True),
    }
    assert not X.themes(by3, "crypto", ("es_globex_clean", "es_rth_clean"))["v_travel"]["theme"]
