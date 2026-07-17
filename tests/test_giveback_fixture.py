"""Hand-labeled DRAM June fixture as the give-back acceptance test (TVB-13).

The labels reproduce the user's live account of the episode (memory
project-exit-arc-tvb13; HANDOFF TVB-12/13 entries) from committed Hyperliquid
venue bars: re-entry short 65.88 caught the -20% move; the strategy exit at
66.66 was a -1.2% loss on a +19.87% open winner. Derivation of the pinned
timestamps: entry = LAST downward cross of 65.88 before the June 6 bottom;
exit = FIRST touch of 66.66 after it (2026-07-17 session).
"""

from analysis.giveback import episode_metrics, load_bars, summarize

BARS_PATH = "analysis/reference/tvb13_dram_jun_15m_hl.json"


def test_fixture_reentry_episode():
    bars = load_bars(BARS_PATH)
    m = episode_metrics(
        bars,
        direction="short",
        entry_time="2026-06-04T19:45:00Z",
        entry_price=65.88,
        exit_time="2026-06-14T06:45:00Z",
        exit_price=66.66,
    )
    # The user's own numbers, reproduced from venue bars.
    assert abs(m["mfe"] * 100 - 19.87) < 0.05, m["mfe"]
    assert abs(m["mae"] * 100 - 1.21) < 0.05, m["mae"]
    assert abs(m["realized"] * 100 - (-1.18)) < 0.02, m["realized"]
    assert abs(m["give_back_pp"] - 21.06) < 0.10, m["give_back_pp"]
    # Peak was the 52.788 bottom, 2026-06-06T02:30Z, ~30.8h after entry.
    assert abs(m["hours_to_mfe"] - 30.75) < 0.30, m["hours_to_mfe"]
    assert m["mfe_time_s"] == 1780713000
    # The exit surrendered MORE than the entire peak (finished worse than flat).
    assert m["give_back_frac"] > 1.0


def test_fixture_bottom_price_in_bars():
    bars = load_bars(BARS_PATH)
    assert abs(min(b[3] for b in bars) - 52.788) < 1e-9


def test_summarize_flags_round_trip():
    bars = load_bars(BARS_PATH)
    m = episode_metrics(bars, "short", "2026-06-04T19:45:00Z", 65.88, "2026-06-14T06:45:00Z", 66.66)
    s = summarize([m])
    assert s["episodes"] == 1
    assert s["winners_2pct_plus"] == 1
    assert s["full_round_trips"] == 1
