"""TVB-20 control-port parity regression tests.

The parity gate's single engine change is TwinConfig.pine_gate_warmup: Pine's
gate helper (ta.valuewhen(timeframe.change(tf), open, 0)) has NO value until
the feed contains a period boundary, so a cold-started chart cannot trade
until the first MONTHLY roll inside loaded history. The twin's original
bootstrap adopted the first loaded bar as every period's open and traded from
day one. Both behaviors are pinned here on the committed GOOGL TV-bar dump
(real bars; the boundary date is a property of that dump: feed starts
2026-05-25, first month roll 2026-06-01).
"""

import json
from pathlib import Path

from analysis.paper.engine import Twin, TwinConfig
from analysis.paper.port_parity import kind_of

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
