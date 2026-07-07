"""Phase-4 seam: resampler cross-checked against the committed TV 60m/1D files.

Known residuals carried from TVB-6 (not resampler bugs): exactly one traded
15m bar is missing from the committed 15m file (Jun-28, volume reconciles to
the decimal), so a handful of aggregated rows may differ from TV's own
higher-TF bars. Thresholds below encode that, tightly.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tfc.resample import period_start, resample  # noqa: E402
from tfc.tv_reference import load_bars  # noqa: E402


def _compare(agg, ref, v_rel=1e-9):
    common, ai, ri = np.intersect1d(agg.ts, ref.ts, return_indices=True)
    exact = 0
    for k in range(len(common)):
        a, r = ai[k], ri[k]
        if (
            agg.open[a] == ref.open[r]
            and agg.high[a] == ref.high[r]
            and agg.low[a] == ref.low[r]
            and agg.close[a] == ref.close[r]
            and abs(agg.volume[a] - ref.volume[r]) <= v_rel * max(1.0, ref.volume[r])
        ):
            exact += 1
    return len(common), exact, len(agg), len(ref)


def test_15m_to_60m_matches_committed_tv_60m():
    b15 = load_bars("tvb6_tv_xyzMSTR_15m.json")
    ref = load_bars("tvb6_tv_xyzMSTR_60m.json")
    agg = resample(b15, "60")
    common, exact, n_agg, n_ref = _compare(agg, ref, v_rel=1e-6)
    assert n_ref == 5103
    assert common >= 5100  # near-total timestamp coverage
    assert exact >= common - 3  # TVB-6: 5102/5103 internal aggregation
    assert agg.ts[0] == ref.ts[0] == 1764687600  # 2025-12-02T15:00Z


def test_15m_to_1d_matches_committed_tv_1d():
    b15 = load_bars("tvb6_tv_xyzMSTR_15m.json")
    ref = load_bars("tvb6_tv_xyzMSTR_1D.json")
    agg = resample(b15, "D")
    common, exact, n_agg, n_ref = _compare(agg, ref, v_rel=1e-6)
    assert n_ref == 214 and n_agg == n_ref and common == n_ref
    assert exact >= n_ref - 2
    # partial first day is timestamped at PERIOD START, exactly as TV does
    assert agg.ts[0] == ref.ts[0] == 1764633600  # 2025-12-02T00:00Z


def test_period_start_inverts_ids():
    from tfc.periods import period_ids

    ts = np.array([1764687600, 1764720000, 1765152000, 1767225600], dtype=np.int64)
    for tf in ("15", "60", "240", "D", "W", "M"):
        pid = period_ids(ts, tf)
        st = period_start(pid, tf)
        assert (st <= ts).all()
        assert (period_ids(st, tf) == pid).all()
