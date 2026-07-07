"""Phase-2/3 driver: run the simulator against gate cells, print first-mismatch context.

Usage: uv run python scripts/tfc_gate_report.py [cell ...]     (default: all 8)
Exit 0 = every requested cell PASSes trade-for-trade; 2 otherwise.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tfc.equivalence import compare_cell  # noqa: E402
from tfc.tv_reference import REFERENCE_CELLS  # noqa: E402


def main(argv: list[str]) -> int:
    names = argv or list(REFERENCE_CELLS)
    ok = True
    for name in names:
        t0 = time.perf_counter()
        rep = compare_cell(name)
        dt = time.perf_counter() - t0
        print(f"{rep.summary()}  ({dt:.2f}s)")
        ok &= rep.passed
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
