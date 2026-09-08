"""TVB-35 macro-regime RECEIPT (characterization only; never a selection).

Labels every closed trade and every decision row of the three live ledgers
(weekend 1, round 2, round 3-aborted) with the state of a fixed macro
reference set at that instant, using the executor's own continuity idea:
price now vs the reference's forming DAILY open (daily dot) and forming
WEEKLY open (weekly dot), plus a running outside-day check (the charter's
"3" = expansion = whipsaw) on the S&P 500 and bitcoin.

References (TradingView, harvested by scripts/tvb35_regime_harvest.mjs into
analysis/regime/data/): TVC:DXY, TVC:US10Y, NYMEX:CL1!, ICEEUR:BRN1!,
SP:SPX, BITSTAMP:BTCUSD at 60m / D / W.

A-priori composite labels (stated BEFORE any number was read; the mapping
is the charter S2 oracle argument, equity perps inherit their underlying's
macro sensitivity -- it is NOT tuned here):
  macro_dir  headwind  = dollar daily dot UP  and 10-year daily dot UP
             tailwind  = dollar daily dot DOWN and 10-year daily dot DOWN
             mixed     = anything else (incl. a missing / dead-even dot)
  alignment  with      = long in tailwind, or short in headwind
             against   = long in headwind, or short in tailwind
             mixed     = macro_dir mixed
  whipsaw    True when the S&P's OR bitcoin's running day is an outside day
             (running high above the prior day's high AND running low below
             the prior day's low) at that instant.
  oil_dot    WTI daily dot (for the oil-linked names only).

Limits stated up front: price "now" is the close of the last 60m bar at or
before the instant (hourly resolution); each reference keeps ITS OWN
session clock (the daily bar open time TradingView serves); the three
ledgers hold 84 closed trades -- this can show the labels are computable
and map the ceiling, it cannot validate a filter.

Usage: uv run python analysis/regime/receipt.py
Writes analysis/regime/receipt.json and analysis/regime/REGIME_RECEIPT.md.
"""

from __future__ import annotations

import bisect
import json
import statistics
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
EXEC = Path(r"C:\Strat_Trading_Bot\hip3-executor\runs")

REFS = ["DXY", "US10Y", "CL1", "BRN1", "SPX", "BTCUSD"]
LEDGERS = {
    "weekend1": {
        "decisions": EXEC / "2026-08-22_weekend1" / "decisions.jsonl",
        "trades": EXEC / "2026-08-22_weekend1" / "trades.jsonl",
        "open": "2026-08-22T14:26:00+00:00",
        "close": "2026-08-24T21:58:59+00:00",
    },
    "round2": {
        "decisions": EXEC / "2026-08-31_round2" / "decisions_r2.jsonl",
        "trades": EXEC / "2026-08-31_round2" / "trades.jsonl",
        "open": "2026-08-31T15:37:45+00:00",
        "close": "2026-09-04T17:13:32+00:00",
    },
    "round3": {
        "decisions": EXEC / "2026-09-06_round3_aborted" / "decisions_r3.jsonl",
        "trades": EXEC / "2026-09-06_round3_aborted" / "trades_r3.jsonl",
        "open": "2026-09-06T19:52:53+00:00",
        "close": "2026-09-07T19:00:26+00:00",
    },
}


def ts_of(s: str) -> int:
    return int(datetime.fromisoformat(s).timestamp())


class Ref:
    """One reference: 60m / D / W bars, each sorted by open time (epoch s)."""

    def __init__(self, key: str):
        self.key = key
        self.h = self._load(f"{key}_60.json")
        self.d = self._load(f"{key}_D.json")
        self.w = self._load(f"{key}_W.json")
        self.ht = [b[0] for b in self.h]
        self.dt = [b[0] for b in self.d]
        self.wt = [b[0] for b in self.w]

    @staticmethod
    def _load(name: str) -> list:
        p = DATA / name
        if not p.exists():
            return []
        return sorted(json.loads(p.read_text(encoding="utf-8"))["bars"], key=lambda b: b[0])

    def _last_at(self, times: list, t: int) -> int:
        i = bisect.bisect_right(times, t) - 1
        return i

    def price_at(self, t: int) -> float | None:
        i = self._last_at(self.ht, t)
        if i < 0:
            return None
        # No 60m bar opened in the last two hours = the reference is CLOSED at
        # this instant (weekend, holiday, overnight for a session product).
        # A frozen Friday close must never masquerade as a live weekend dot
        # (review R18: name the actual session).
        if t - self.h[i][0] > 2 * 3600:
            return None
        return self.h[i][4]

    def _period_at(self, bars: list, times: list, t: int):
        i = self._last_at(times, t)
        if i < 0:
            return None, None
        return bars[i], (bars[i - 1] if i > 0 else None)

    def dot(self, t: int, period: str) -> str:
        bars, times = (self.d, self.dt) if period == "D" else (self.w, self.wt)
        cur, _ = self._period_at(bars, times, t)
        if cur is None:
            return "na"
        px = self.price_at(t)
        if px is None:
            return "closed"
        if px > cur[1]:
            return "up"
        if px < cur[1]:
            return "down"
        return "flat"

    def running_day(self, t: int) -> dict | None:
        """Running high/low of the current daily bar as of t (from the 60m
        bars inside it), vs the prior completed daily bar."""
        cur, prev = self._period_at(self.d, self.dt, t)
        if cur is None or prev is None:
            return None
        lo_i = bisect.bisect_left(self.ht, cur[0])
        hi_i = bisect.bisect_right(self.ht, t)
        inside = self.h[lo_i:hi_i]
        if not inside:
            return None
        rh = max(b[2] for b in inside)
        rl = min(b[3] for b in inside)
        return {
            "run_high": rh,
            "run_low": rl,
            "prev_high": prev[2],
            "prev_low": prev[3],
            "broke_high": rh > prev[2],
            "broke_low": rl < prev[3],
            "outside": rh > prev[2] and rl < prev[3],
            "inside": rh <= prev[2] and rl >= prev[3],
            "range_vs_prev": round((rh - rl) / (prev[2] - prev[3]), 3)
            if prev[2] > prev[3]
            else None,
        }


def labels_at(refs: dict, t: int) -> dict:
    out = {}
    for k, r in refs.items():
        out[f"{k}_d"] = r.dot(t, "D")
        out[f"{k}_w"] = r.dot(t, "W")
    for k in ("SPX", "BTCUSD"):
        rd = refs[k].running_day(t)
        out[f"{k}_outside"] = None if rd is None else rd["outside"]
        out[f"{k}_inside"] = None if rd is None else rd["inside"]
    dx, ty = out["DXY_d"], out["US10Y_d"]
    if dx == "up" and ty == "up":
        out["macro_dir"] = "headwind"
    elif dx == "down" and ty == "down":
        out["macro_dir"] = "tailwind"
    else:
        out["macro_dir"] = "mixed"
    dxw, tyw = out["DXY_w"], out["US10Y_w"]
    if dxw == "up" and tyw == "up":
        out["macro_dir_w"] = "headwind"
    elif dxw == "down" and tyw == "down":
        out["macro_dir_w"] = "tailwind"
    else:
        out["macro_dir_w"] = "mixed"
    out["whipsaw"] = bool(out["SPX_outside"]) or bool(out["BTCUSD_outside"])
    out["oil_dot"] = out["CL1_d"]
    return out


def alignment(direction: str, macro_dir: str) -> str:
    if macro_dir == "mixed":
        return "mixed"
    if (direction == "up" and macro_dir == "tailwind") or (
        direction == "down" and macro_dir == "headwind"
    ):
        return "with"
    return "against"


def load_rows(p: Path) -> list:
    if not p.exists():
        return []
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def closed_trades(rows: list, open_iso: str, close_iso: str) -> list:
    """Pair entry -> exit per coin in order (the executor holds one position
    per coin), inside the ledger window."""
    open_t, close_t = ts_of(open_iso), ts_of(close_iso)
    pending: dict[str, dict] = {}
    out = []
    for r in rows:
        ev = r.get("event")
        t = ts_of(r["ts"])
        if t < open_t or t > close_t:
            continue
        if ev == "entry":
            pending[r["coin"]] = r
        elif ev == "exit":
            e = pending.pop(r["coin"], None)
            if e is None:
                continue
            out.append(
                {
                    "coin": r["coin"],
                    "dir": e.get("dir"),
                    "tf": e.get("tf"),
                    "signal": e.get("signal"),
                    "kind": e.get("kind"),
                    "entry_ts": e["ts"],
                    "exit_ts": r["ts"],
                    "reason": r.get("reason"),
                    "pnl_pct": r.get("pnl_pct"),
                    "pnl_usd": r.get("pnl_usd"),
                }
            )
    return out


def summarize(trades: list, key) -> dict:
    groups: dict[str, list] = defaultdict(list)
    for tr in trades:
        groups[str(key(tr))].append(tr)
    out = {}
    for g, items in sorted(groups.items()):
        pp = [x["pnl_pct"] for x in items if isinstance(x.get("pnl_pct"), (int, float))]
        usd = [x["pnl_usd"] for x in items if isinstance(x.get("pnl_usd"), (int, float))]
        out[g] = {
            "n": len(items),
            "wins": sum(1 for v in pp if v > 0),
            "sum_pnl_pct": round(sum(pp), 2),
            "median_pnl_pct": round(statistics.median(pp), 3) if pp else None,
            "sum_pnl_usd": round(sum(usd), 2) if usd else None,
        }
    return out


def main() -> None:
    refs = {k: Ref(k) for k in REFS}
    receipt: dict = {"generated": datetime.now(UTC).isoformat(), "refs": {}, "ledgers": {}}
    for k, r in refs.items():
        receipt["refs"][k] = {
            "h60": [len(r.h), r.h[0][0] if r.h else None, r.h[-1][0] if r.h else None],
            "daily_open_utc_hour": (
                datetime.fromtimestamp(r.d[-1][0], UTC).strftime("%H:%M") if r.d else None
            ),
        }

    all_trades: list = []
    for name, spec in LEDGERS.items():
        trades = closed_trades(load_rows(spec["trades"]), spec["open"], spec["close"])
        for tr in trades:
            lab = labels_at(refs, ts_of(tr["entry_ts"]))
            tr.update(lab)
            tr["alignment"] = alignment(tr["dir"], lab["macro_dir"])
            tr["alignment_w"] = alignment(tr["dir"], lab["macro_dir_w"])
            tr["ledger"] = name
        all_trades.extend(trades)

        decisions = load_rows(spec["decisions"])
        open_t, close_t = ts_of(spec["open"]), ts_of(spec["close"])
        dec_lab = Counter()
        enter_lab = Counter()
        enter_align = Counter()
        whip_rows = Counter()
        na_rows = 0
        cache: dict[int, dict] = {}
        for row in decisions:
            t = ts_of(row["ts"])
            if t < open_t or t > close_t:
                continue
            hour = t // 3600 * 3600  # labels at hourly resolution: cache per hour
            lab = cache.get(hour)
            if lab is None:
                lab = labels_at(refs, hour)
                cache[hour] = lab
            if lab["DXY_d"] in ("na", "closed") or lab["US10Y_d"] in ("na", "closed"):
                na_rows += 1
            dec_lab[lab["macro_dir"]] += 1
            whip_rows[bool(lab["whipsaw"])] += 1
            if row.get("verdict") == "enter":
                enter_lab[lab["macro_dir"]] += 1
                enter_align[alignment(row.get("dir"), lab["macro_dir"])] += 1
        receipt["ledgers"][name] = {
            "window": [spec["open"], spec["close"]],
            "closed_trades": len(trades),
            "decision_rows": sum(dec_lab.values()),
            "decision_rows_macro_na": na_rows,
            "decision_rows_by_macro_dir": dict(dec_lab),
            "decision_rows_by_whipsaw": {str(k): v for k, v in whip_rows.items()},
            "entries_by_macro_dir": dict(enter_lab),
            "entries_by_alignment": dict(enter_align),
            "trades_by_alignment": summarize(trades, lambda x: x["alignment"]),
            "trades_by_alignment_weekly": summarize(trades, lambda x: x["alignment_w"]),
            "trades_by_whipsaw": summarize(trades, lambda x: x["whipsaw"]),
            "trades_by_macro_dir": summarize(trades, lambda x: x["macro_dir"]),
        }

    receipt["pooled"] = {
        "closed_trades": len(all_trades),
        "by_alignment": summarize(all_trades, lambda x: x["alignment"]),
        "by_alignment_weekly": summarize(all_trades, lambda x: x["alignment_w"]),
        "by_whipsaw": summarize(all_trades, lambda x: x["whipsaw"]),
        "by_macro_dir": summarize(all_trades, lambda x: x["macro_dir"]),
        "by_dir_x_macro": summarize(all_trades, lambda x: f"{x['dir']}|{x['macro_dir']}"),
        "by_whipsaw_x_reason": summarize(all_trades, lambda x: f"{x['whipsaw']}|{x['reason']}"),
    }
    now = int(datetime.now(UTC).timestamp())
    receipt["now"] = {"ts": datetime.fromtimestamp(now, UTC).isoformat(), **labels_at(refs, now)}
    receipt["trades"] = all_trades

    (HERE / "receipt.json").write_text(json.dumps(receipt, indent=1, default=str), encoding="utf-8")
    write_md(receipt)
    print(
        json.dumps(
            {k: v for k, v in receipt["pooled"].items() if k != "by_whipsaw_x_reason"}, indent=1
        )
    )
    print("now:", {k: v for k, v in receipt["now"].items() if not k.endswith("_inside")})


def _tbl(title: str, groups: dict) -> list[str]:
    lines = [
        f"**{title}**",
        "",
        "| label | n | wins | sum pnl% | median pnl% | sum $ |",
        "|---|---|---|---|---|---|",
    ]
    for g, s in groups.items():
        lines.append(
            f"| {g} | {s['n']} | {s['wins']} | {s['sum_pnl_pct']} | {s['median_pnl_pct']} | {s['sum_pnl_usd']} |"
        )
    lines.append("")
    return lines


def write_md(rc: dict) -> None:
    L = []
    L.append("# Macro-regime receipt (TVB-35) -- characterization only\n")
    L.append(
        "Every closed trade of the three live ledgers labeled with the macro reference\n"
        "set at ENTRY time; every decision row labeled at its hour. Labels were fixed\n"
        "a-priori in `receipt.py`'s docstring before any number was read. 84-ish trades:\n"
        "this shows the labels are computable and maps the ceiling; it validates nothing.\n"
        "Price is the last 60m close at or before the instant; each reference keeps its own\n"
        "session clock (daily open hour UTC below).\n"
    )
    L.append("| ref | 60m bars | first | last | daily bar opens (UTC) |")
    L.append("|---|---|---|---|---|")
    for k, v in rc["refs"].items():
        f = datetime.fromtimestamp(v["h60"][1], UTC).strftime("%m-%d %H:%M") if v["h60"][1] else "-"
        l = datetime.fromtimestamp(v["h60"][2], UTC).strftime("%m-%d %H:%M") if v["h60"][2] else "-"
        L.append(f"| {k} | {v['h60'][0]} | {f} | {l} | {v['daily_open_utc_hour']} |")
    L.append("")
    n = rc["now"]
    L.append(
        f"**Now ({n['ts'][:16]}Z):** dollar daily {n['DXY_d']} / weekly {n['DXY_w']}; "
        f"10-year daily {n['US10Y_d']} / weekly {n['US10Y_w']}; WTI daily {n['CL1_d']}; "
        f"Brent daily {n['BRN1_d']}; S&P daily {n['SPX_d']}; BTC daily {n['BTCUSD_d']}; "
        f"macro_dir {n['macro_dir']} (weekly {n['macro_dir_w']}); whipsaw {n['whipsaw']}.\n"
    )
    L.append("## Pooled (all three ledgers)\n")
    p = rc["pooled"]
    L += _tbl(
        "By alignment with the DAILY dollar+10-year label (with = long in tailwind / short in headwind)",
        p["by_alignment"],
    )
    L += _tbl("By alignment with the WEEKLY label", p["by_alignment_weekly"])
    L += _tbl("By whipsaw (S&P or BTC running outside day at entry)", p["by_whipsaw"])
    L += _tbl("By trade direction x daily macro label", p["by_dir_x_macro"])
    for name, lg in rc["ledgers"].items():
        L.append(f"## {name} ({lg['window'][0][:16]}Z .. {lg['window'][1][:16]}Z)\n")
        L.append(
            f"Closed trades {lg['closed_trades']}; decision rows {lg['decision_rows']} "
            f"(macro label unavailable on {lg['decision_rows_macro_na']}); rows by macro_dir "
            f"{lg['decision_rows_by_macro_dir']}; rows by whipsaw {lg['decision_rows_by_whipsaw']}; "
            f"entries by macro_dir {lg['entries_by_macro_dir']}; entries by alignment "
            f"{lg['entries_by_alignment']}.\n"
        )
        L += _tbl("Trades by alignment (daily)", lg["trades_by_alignment"])
        L += _tbl("Trades by whipsaw", lg["trades_by_whipsaw"])
    L.append("## Reading rules\n")
    L.append(
        "- A cell with fewer than ~10 trades is a question, not a reading.\n"
        "- `mixed` is the honest default: one of the two references disagreed or was closed.\n"
        "- The whipsaw flag is a running check: a day can become an outside day AFTER the entry.\n"
        "- Nothing here is a gate. A live label would be shadow-journaled first (the BTC drift\n"
        "  veto is the template) and receipted again on the next tape.\n"
    )
    (HERE / "REGIME_RECEIPT.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
