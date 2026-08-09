"""TVB-20 control-port parity regression tests.

Two concerns are pinned here:

1. Pine gate warm-up (the gate's single engine change). Pine's gate helper
   (ta.valuewhen(timeframe.change(tf), open, 0)) has NO value until the feed
   contains a period boundary, so a cold-started chart cannot trade until the
   first MONTHLY roll inside loaded history. The twin's original bootstrap
   adopted the first loaded bar as every period's open and traded from day
   one. Both behaviors are pinned on the committed GOOGL TV-bar dump (real
   bars; the boundary date is a property of that dump: feed starts
   2026-05-25, first month roll 2026-06-01).

2. Gate fail-closed hardening (TVB-20 external audit F1, returned
   2026-08-08). The join must be injective: duplicate event keys on either
   side, malformed directions, unrecognized exit comments, malformed open-row
   shapes, and cardinality inequality all FAIL the gate. The pre-fix gate
   false-PASSed a duplicated trade row (91 in-feed events vs 89 matched) and
   silently aliased direction 's' to short -- both reproduced on the
   committed GOOGL artifact before the fix. The committed full-feed GOOGL
   result must keep passing the hardened gate with identical counts.
"""

import json
from pathlib import Path

from analysis.paper.engine import Twin, TwinConfig
from analysis.paper.port_parity import compare, gate, kind_of

ROOT = Path(__file__).resolve().parents[1]
DUMP = ROOT / "analysis" / "reference" / "tv_deep" / "tvb19_tv_xyz_GOOGL_5m.json"
JUNE1 = 1780272000  # 2026-06-01T00:00:00Z -- first monthly boundary in the feed


def _replay(pine_gate_warmup: bool):
    bars = json.loads(DUMP.read_text())["bars"][:-1]
    bars = [b for b in bars if int(b[0]) < JUNE1 + 3 * 86400]
    tw = Twin(TwinConfig(symbol="GOOGL", mintick=0.001, pine_gate_warmup=pine_gate_warmup))
    events = []
    for b in bars:
        events.extend(tw.replay_bar(int(b[0]), b[1], b[2], b[3], b[4]))
    return events


def test_pine_gate_warmup_blocks_trading_until_first_month_roll():
    events = _replay(True)
    assert events, "expected events once the June boundary armed the gates"
    assert all(e["ts"] >= JUNE1 for e in events)


def test_default_bootstrap_unchanged_and_trades_before_month_roll():
    events = _replay(False)
    assert any(e["ts"] < JUNE1 for e in events)


def test_exit_comment_kind_mapping():
    assert kind_of("BF 12h N2") == "bf"
    assert kind_of("Break D") == "brk"
    assert kind_of("Flip") == "flip"


# --- gate fail-closed hardening (audit F1) -----------------------------------
# Synthetic two-bar world: entry fills at bar 1000 close 10.0, break exit at
# bar 2000 close 11.0. Twin prices carry the declared trigger-level residual
# on the entry and the exact close on the break exit.

CLOSED_TRADE = {
    "index": 0,
    "direction": "L",
    "entry_time": 1000 * 1000,
    "entry_price": 10.0,
    "exit_signal": "Break D",
    "exit_time": 2000 * 1000,
    "exit_price": 11.0,
}


def _twin():
    return [
        {"ts": 1000, "action": "enter", "dir": "long", "kind": "entry", "price": 9.5},
        {"ts": 2000, "action": "exit", "dir": "long", "kind": "brk", "price": 11.0},
    ]


def _gate(trades, twin=None):
    closes = {1000: 10.0, 2000: 11.0}
    port = {"chart": {"mintick": 0.001, "first_bar_ts": 1000}, "trades": trades}
    return gate("SYN", twin if twin is not None else _twin(), 2000, closes, 2, port)


def test_gate_passes_clean_synthetic_stream():
    r = _gate([dict(CLOSED_TRADE)])
    assert r["pass"] is True
    assert r["structural_violations"] == []
    assert r["twin_events"] == r["tv_events_in_feed"] == r["matched"] == 2


def test_gate_fails_on_duplicate_tv_trade():
    r = _gate([dict(CLOSED_TRADE), dict(CLOSED_TRADE)])
    assert r["pass"] is False
    assert any("duplicate" in v for v in r["structural_violations"])
    assert any("cardinality" in v for v in r["structural_violations"])


def test_gate_fails_on_duplicate_twin_event():
    twin = _twin()
    twin.append(dict(twin[1]))
    r = _gate([dict(CLOSED_TRADE)], twin=twin)
    assert r["pass"] is False
    assert any(v.startswith("twin") and "duplicate" in v for v in r["structural_violations"])


def test_gate_fails_closed_on_invalid_direction():
    r = _gate([dict(CLOSED_TRADE, direction="s")])
    assert r["pass"] is False
    assert any("direction" in v for v in r["structural_violations"])
    assert "matched" not in r  # join skipped: nothing malformed was aliased into events


def test_gate_fails_closed_on_unrecognized_exit_comment():
    r = _gate([dict(CLOSED_TRADE, exit_signal="Take Profit 3")])
    assert r["pass"] is False
    assert any("unrecognized exit comment" in v for v in r["structural_violations"])


def test_gate_fails_on_multiple_open_rows():
    open_a = dict(CLOSED_TRADE, exit_signal="", index=1)
    open_b = dict(CLOSED_TRADE, exit_signal="", index=2)
    r = _gate([dict(CLOSED_TRADE), open_a, open_b])
    assert r["pass"] is False
    assert any("open rows" in v for v in r["structural_violations"])


def test_gate_fails_when_open_row_not_final():
    open_row = dict(CLOSED_TRADE, exit_signal="", index=1)
    r = _gate([open_row, dict(CLOSED_TRADE)])
    assert r["pass"] is False
    assert any("not the final trade row" in v for v in r["structural_violations"])


def test_committed_googl_parity_survives_hardened_gate():
    r = compare("GOOGL")
    assert r["pass"] is True
    assert r["structural_violations"] == []
    assert r["twin_events"] == r["tv_events_in_feed"] == r["matched"] == 89
