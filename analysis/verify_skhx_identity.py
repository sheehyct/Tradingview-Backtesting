"""Executable verifier for the SKHX/SKHYNIX identity claim (TVB-19).

HL `xyz:SKHX` and TV `HIP3XYZ:SKHYNIXUSDC.P` are claimed to be the same
instrument, proven by float-exact overlapping 5m closes. This script computes
that comparison from the two COMMITTED series and writes a small artifact with
counts only (no price rows), so the claim is regenerable instead of prose.

Conventions: both series are compared exactly as committed (the TV series may
end on a forming bar -- its timestamp only overlaps an HL bar once that bar
also exists there). Mismatches are reported as counts + max abs close delta.

    uv run python -m analysis.verify_skhx_identity
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TV_DEFAULT = REPO / "analysis" / "reference" / "tv_deep" / "tvb19_tv_xyz_SKHYNIX_5m.json"
HL_DEFAULT = REPO / "analysis" / "paper" / "bars" / "xyz_SKHX_5m.json"
OUT_DEFAULT = REPO / "analysis" / "reference" / "tv_deep" / "skhx_identity_check.json"


def compare(tv_path: Path, hl_path: Path) -> dict:
    tv = json.loads(tv_path.read_text())
    hl = json.loads(hl_path.read_text())
    tv_by_ts = {int(r[0]): r for r in tv["bars"]}
    hl_by_ts = {int(r[0]): r for r in hl["bars"]}
    overlap = sorted(set(tv_by_ts) & set(hl_by_ts))
    exact = sum(1 for t in overlap if tv_by_ts[t][4] == hl_by_ts[t][4])
    deltas = [
        abs(tv_by_ts[t][4] - hl_by_ts[t][4]) for t in overlap if tv_by_ts[t][4] != hl_by_ts[t][4]
    ]

    def iso(ts: int) -> str:
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

    return {
        "tv_file": tv_path.name,
        "hl_file": hl_path.name,
        "tv_pro_symbol": tv.get("pro_symbol"),
        "hl_symbol": hl.get("symbol") or hl.get("pro_symbol"),
        "tv_bars": len(tv_by_ts),
        "hl_bars": len(hl_by_ts),
        "tv_span": [iso(min(tv_by_ts)), iso(max(tv_by_ts))],
        "hl_span": [iso(min(hl_by_ts)), iso(max(hl_by_ts))],
        "overlap_bars": len(overlap),
        "float_exact_closes": exact,
        "mismatched_closes": len(deltas),
        "max_abs_close_delta": max(deltas) if deltas else 0.0,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Verify SKHX == SKHYNIX from committed bars")
    ap.add_argument("--tv", default=str(TV_DEFAULT))
    ap.add_argument("--hl", default=str(HL_DEFAULT))
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    args = ap.parse_args()
    res = compare(Path(args.tv), Path(args.hl))
    res["generated_utc"] = datetime.now(tz=timezone.utc).isoformat()
    Path(args.out).write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    for k, v in res.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
