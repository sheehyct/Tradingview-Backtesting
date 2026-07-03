"""Sanitized fee-rate summary from a LOCAL Hyperliquid fills export (Codex TVB-2 finding 2).

Reproduces the TVB-2 ground-truth fee classification -- counts and RATES by
{dex, liquidity flag} -- from a local `userFills` JSON export, classified by HL's
authoritative `crossed` flag (true = taker), NEVER by backing out fee/notional
against assumed reference rates (the method that produced the wrong "97% maker"
read in TVB-2).

SANITIZATION CONTRACT (this repo has a PUBLIC remote):
- The fills export stays LOCAL. Never commit it. Pass its path as argv[1].
- Output contains COUNTS and RATES only -- no absolute notionals, no fee totals,
  no order ids, no hashes, no timestamps.

Usage:
    uv run python analysis/fee_rates_by_dex.py <path-to-userFills.json>

Input shape: JSON array of HL fill objects. Fields used: `coin` (str; HIP-3
builder-perp coins are "{dex}:{COIN}", native coins have no prefix), `crossed`
(bool), `fee` (str/num), `px` (str/num), `sz` (str/num). Extra fields ignored.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation


def dex_of(coin: str) -> str:
    """HIP-3 builder-perp coins are namespaced '{dex}:{COIN}'; native HL = 'crypto'."""
    if ":" in coin:
        return coin.split(":", 1)[0]
    return "crypto"


def to_decimal(value) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"non-numeric field value: {value!r}") from exc


def summarize(fills: list[dict]) -> list[dict]:
    """Aggregate to one row per {dex, crossed}: count + rate stats (percent units).

    Rates are fee / (px * sz) per fill. Notionals are used INTERNALLY as weights
    and never surfaced. Modal rate = most common value of the rate rounded to
    4 decimal places (in percent), the same bucketing TVB-2 used.
    """
    groups: dict[tuple[str, bool], list[tuple[Decimal, Decimal]]] = defaultdict(list)
    skipped = 0
    for f in fills:
        try:
            px = to_decimal(f["px"])
            sz = to_decimal(f["sz"])
            fee = to_decimal(f["fee"])
            crossed = bool(f["crossed"])
            coin = str(f["coin"])
        except (KeyError, ValueError):
            skipped += 1
            continue
        notional = px * sz
        if notional == 0:
            skipped += 1
            continue
        groups[(dex_of(coin), crossed)].append((fee / notional, notional))

    rows = []
    for (dex, crossed), pairs in sorted(groups.items()):
        rates = [r for r, _ in pairs]
        weights = [w for _, w in pairs]
        pct = [r * 100 for r in rates]  # percent units
        modal = Counter(round(p, 4) for p in pct).most_common(1)[0][0]
        mean = sum(pct) / len(pct)
        wmean = sum(p * w for p, w in zip(pct, weights)) / sum(weights)
        rows.append(
            {
                "dex": dex,
                "liquidity": "taker" if crossed else "maker",
                "fills": len(rates),
                "modal_pct": float(modal),
                "mean_pct": float(round(mean, 5)),
                "notional_wtd_pct": float(round(wmean, 5)),
            }
        )
    if skipped:
        rows.append(
            {
                "dex": "(skipped malformed/zero-notional fills)",
                "liquidity": "-",
                "fills": skipped,
                "modal_pct": None,
                "mean_pct": None,
                "notional_wtd_pct": None,
            }
        )
    return rows


def render(rows: list[dict]) -> str:
    header = f"{'dex':<12} {'liq':<6} {'fills':>6} {'modal%':>9} {'mean%':>9} {'ntl-wtd%':>9}"
    lines = [header, "-" * len(header)]
    for r in rows:
        fmt = lambda v: "-" if v is None else f"{v:.4f}"
        lines.append(
            f"{r['dex']:<12} {r['liquidity']:<6} {r['fills']:>6} "
            f"{fmt(r['modal_pct']):>9} {fmt(r['mean_pct']):>9} {fmt(r['notional_wtd_pct']):>9}"
        )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    with open(argv[1], "r", encoding="utf-8") as fh:
        fills = json.load(fh)
    if not isinstance(fills, list):
        print("ERROR: expected a JSON array of fill objects", file=sys.stderr)
        return 1
    print(render(summarize(fills)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
