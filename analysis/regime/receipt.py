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

Availability (amended 2026-10-11, TVB-38, Codex TVB-35 audit F6/F7): at an
instant t only COMPLETED bars are known. Bar timestamps are OPEN times; a 60m
bar becomes known at open + 60 minutes (its close time). Therefore:
  price now   = close of the latest 60m bar whose close time is <= t;
  running day = high/low over the current day's 60m bars completed by t;
  freshness   = if the latest completed 60m bar closed more than FRESH_S
                (2 hours) before t, the reference is CLOSED at t (weekend,
                holiday, session break): its dots read "closed" and its
                running day is unknown. No completed 60m bar at all before t
                (history gap) reads "na".
The period's own open (daily / weekly) is the open of its first 60m bar and
is known once that bar has started (a period stamped before its first trade
reads "closed" until then). SPX 60m bars open on the half hour; its last session bar is
shorter than 60 minutes, so open + 60 makes it known later than it really
was (conservative, never early). Every component and the whipsaw flag are
three-state: True / False / None (unknown); unknown is never coerced to
False. OR rule: any True -> True; else any unknown -> unknown; else False.

Limits stated up front: hourly resolution; each reference keeps ITS OWN
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

H60 = 3600  # a 60m bar is known at its open + H60
FRESH_S = 2 * 3600  # latest completed 60m close older than this = reference closed
LIVE_DOTS = ("up", "down", "flat")

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
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def tri_or(*vals: bool | None) -> bool | None:
    """Three-state OR: any True -> True; else any unknown -> None; else False."""
    if any(v is True for v in vals):
        return True
    if any(v is None for v in vals):
        return None
    return False


def tri(v: bool | None) -> str:
    return "unknown" if v is None else ("true" if v else "false")


class Ref:
    """One reference: 60m / D / W bars [open_ts, o, h, l, c], sorted by OPEN
    time (epoch s). Only bars completed by t are read at t (module docstring).
    Bars may be passed in directly (hand vectors); otherwise they load from DATA."""

    def __init__(
        self, key: str, h: list | None = None, d: list | None = None, w: list | None = None
    ):
        self.key = key
        self.h = self._prep(h) if h is not None else self._load(f"{key}_60.json")
        self.d = self._prep(d) if d is not None else self._load(f"{key}_D.json")
        self.w = self._prep(w) if w is not None else self._load(f"{key}_W.json")
        self.ht = [b[0] for b in self.h]
        self.dt = [b[0] for b in self.d]
        self.wt = [b[0] for b in self.w]

    @staticmethod
    def _prep(bars: list) -> list:
        return sorted(bars, key=lambda b: b[0])

    @classmethod
    def _load(cls, name: str) -> list:
        p = DATA / name
        if not p.exists():
            return []
        return cls._prep(json.loads(p.read_text(encoding="utf-8"))["bars"])

    @staticmethod
    def _last_at(times: list, t: int) -> int:
        """Index of the latest bar whose OPEN is <= t (used for D / W periods,
        of which only the open price and the prior completed bar are read)."""
        return bisect.bisect_right(times, t) - 1

    def last_completed(self, t: int) -> int:
        """Index of the latest 60m bar whose CLOSE (open + H60) is <= t, or -1."""
        return bisect.bisect_right(self.ht, t - H60) - 1

    def hour_state(self, t: int) -> tuple[str, int]:
        """('live', i) / ('closed', i) / ('na', -1) for the latest completed 60m bar."""
        i = self.last_completed(t)
        if i < 0:
            return "na", -1
        # The latest completed bar closed more than FRESH_S ago = the reference
        # is CLOSED at t (weekend, holiday, session break). A frozen Friday close
        # must never masquerade as a live weekend dot (review R18).
        if t - (self.h[i][0] + H60) > FRESH_S:
            return "closed", i
        return "live", i

    def price_at(self, t: int) -> float | None:
        state, i = self.hour_state(t)
        return self.h[i][4] if state == "live" else None

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
        state, i = self.hour_state(t)
        if state != "live":
            return state
        # The period's open price is the open of its first 60m bar, printed when
        # that bar starts. A period stamp can precede its first trade (US10Y's
        # daily bar is stamped 23:00 UTC, its first 60m bar opens 00:00): until
        # that bar has started, the period open is not yet known.
        k = bisect.bisect_left(self.ht, cur[0])
        if k >= len(self.ht) or self.ht[k] > t:
            return "closed"
        px = self.h[i][4]
        if px > cur[1]:
            return "up"
        if px < cur[1]:
            return "down"
        return "flat"

    def running_day(self, t: int) -> dict | None:
        """Running high/low of the current daily bar as of t (from the 60m bars
        inside it COMPLETED by t), vs the prior completed daily bar. None =
        unknown (no history, reference closed, or no completed hour yet today)."""
        cur, prev = self._period_at(self.d, self.dt, t)
        if cur is None or prev is None:
            return None
        state, j = self.hour_state(t)
        if state != "live":
            return None
        lo_i = bisect.bisect_left(self.ht, cur[0])
        inside = self.h[lo_i : j + 1]
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
    # Keep the inputs' availability apart from their agreement (audit F8):
    # unavailable = at least one of the dollar / 10-year daily dots not live;
    # mixed_available = both live but disagreeing or flat; directional = both agree.
    if dx not in LIVE_DOTS or ty not in LIVE_DOTS:
        out["macro_state"] = "unavailable"
    elif out["macro_dir"] == "mixed":
        out["macro_state"] = "mixed_available"
    else:
        out["macro_state"] = "directional"
    dxw, tyw = out["DXY_w"], out["US10Y_w"]
    if dxw == "up" and tyw == "up":
        out["macro_dir_w"] = "headwind"
    elif dxw == "down" and tyw == "down":
        out["macro_dir_w"] = "tailwind"
    else:
        out["macro_dir_w"] = "mixed"
    out["whipsaw"] = tri_or(out["SPX_outside"], out["BTCUSD_outside"])
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


def availability(trades: list) -> dict:
    """How many trades had each input available at entry, plus the daily label
    state split and the three-state whipsaw counts."""
    out: dict = {"n": len(trades)}
    for k in REFS:
        out[f"{k}_daily"] = sum(1 for x in trades if x[f"{k}_d"] in LIVE_DOTS)
        out[f"{k}_weekly"] = sum(1 for x in trades if x[f"{k}_w"] in LIVE_DOTS)
    for k in ("SPX", "BTCUSD"):
        out[f"{k}_running_day"] = sum(1 for x in trades if x[f"{k}_outside"] is not None)
    out["dollar_and_10y_daily"] = sum(
        1 for x in trades if x["DXY_d"] in LIVE_DOTS and x["US10Y_d"] in LIVE_DOTS
    )
    ms = Counter(x["macro_state"] for x in trades)
    out["macro_state"] = {
        s: ms.get(s, 0) for s in ("unavailable", "mixed_available", "directional")
    }
    al = Counter(x["alignment"] for x in trades)
    out["directional_with"] = al.get("with", 0)
    out["directional_against"] = al.get("against", 0)
    ws = Counter(tri(x["whipsaw"]) for x in trades)
    out["whipsaw"] = {s: ws.get(s, 0) for s in ("true", "false", "unknown")}
    return out


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


def harvest_instant() -> int:
    """The 'now' row is labeled at the harvest instant (MANIFEST), so a rerun
    reproduces it instead of labeling a date past the end of the data."""
    p = DATA / "MANIFEST.json"
    if p.exists():
        return ts_of(json.loads(p.read_text(encoding="utf-8"))["harvested_at"])
    return int(datetime.now(UTC).timestamp())


def main() -> None:
    refs = {k: Ref(k) for k in REFS}
    receipt: dict = {
        "generated": datetime.now(UTC).isoformat(),
        "availability_rule": (
            "60m bar known at open+60min; price now = latest completed 60m close; "
            "running day from completed 60m bars; reference closed when its latest "
            "completed 60m close is older than 2h; whipsaw and components true/false/unknown"
        ),
        "refs": {},
        "ledgers": {},
    }
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
        dec_state = Counter()
        enter_lab = Counter()
        enter_align = Counter()
        whip_rows = Counter()
        na_rows = 0
        cache: dict[int, dict] = {}
        for row in decisions:
            t = ts_of(row["ts"])
            if t < open_t or t > close_t:
                continue
            # Labeled at the row's own instant (no hour-floor rounding: SPX
            # bars complete on the half hour).
            lab = cache.get(t)
            if lab is None:
                lab = labels_at(refs, t)
                cache[t] = lab
            if lab["macro_state"] == "unavailable":
                na_rows += 1
            dec_lab[lab["macro_dir"]] += 1
            dec_state[lab["macro_state"]] += 1
            whip_rows[tri(lab["whipsaw"])] += 1
            if row.get("verdict") == "enter":
                enter_lab[lab["macro_dir"]] += 1
                enter_align[alignment(row.get("dir"), lab["macro_dir"])] += 1
        receipt["ledgers"][name] = {
            "window": [spec["open"], spec["close"]],
            "closed_trades": len(trades),
            "decision_rows": sum(dec_lab.values()),
            "decision_rows_macro_na": na_rows,
            "decision_rows_by_macro_dir": dict(dec_lab),
            "decision_rows_by_macro_state": dict(dec_state),
            "decision_rows_by_whipsaw": dict(whip_rows),
            "entries_by_macro_dir": dict(enter_lab),
            "entries_by_alignment": dict(enter_align),
            "trade_availability": availability(trades),
            "trades_by_alignment": summarize(trades, lambda x: x["alignment"]),
            "trades_by_alignment_weekly": summarize(trades, lambda x: x["alignment_w"]),
            "trades_by_whipsaw": summarize(trades, lambda x: tri(x["whipsaw"])),
            "trades_by_macro_dir": summarize(trades, lambda x: x["macro_dir"]),
            "trades_by_macro_state": summarize(trades, lambda x: x["macro_state"]),
        }

    receipt["pooled"] = {
        "closed_trades": len(all_trades),
        "trade_availability": availability(all_trades),
        "by_alignment": summarize(all_trades, lambda x: x["alignment"]),
        "by_alignment_weekly": summarize(all_trades, lambda x: x["alignment_w"]),
        "by_whipsaw": summarize(all_trades, lambda x: tri(x["whipsaw"])),
        "by_macro_dir": summarize(all_trades, lambda x: x["macro_dir"]),
        "by_macro_state": summarize(all_trades, lambda x: x["macro_state"]),
        "by_dir_x_macro": summarize(all_trades, lambda x: f"{x['dir']}|{x['macro_dir']}"),
        "by_whipsaw_x_reason": summarize(
            all_trades, lambda x: f"{tri(x['whipsaw'])}|{x['reason']}"
        ),
    }
    now = harvest_instant()
    receipt["now"] = {"ts": datetime.fromtimestamp(now, UTC).isoformat(), **labels_at(refs, now)}
    receipt["trades"] = all_trades

    (HERE / "receipt.json").write_text(json.dumps(receipt, indent=1, default=str), encoding="utf-8")
    write_md(receipt)
    print(json.dumps(receipt["pooled"]["trade_availability"], indent=1))
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
            f"| {g} | {s['n']} | {s['wins']} | {s['sum_pnl_pct']} | {s['median_pnl_pct']} "
            f"| {s['sum_pnl_usd']} |"
        )
    lines.append("")
    return lines


def _avail_tables(rows: list[tuple[str, dict]]) -> list[str]:
    L = [
        "**Inputs available at entry (trades whose input was live, of n)**",
        "",
        "| ledger | n | dollar d | 10-yr d | dollar AND 10-yr d | WTI d | Brent d | S&P d "
        "| BTC d | dollar w | 10-yr w | S&P running day | BTC running day |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name, a in rows:
        L.append(
            f"| {name} | {a['n']} | {a['DXY_daily']} | {a['US10Y_daily']} "
            f"| {a['dollar_and_10y_daily']} | {a['CL1_daily']} | {a['BRN1_daily']} "
            f"| {a['SPX_daily']} | {a['BTCUSD_daily']} | {a['DXY_weekly']} "
            f"| {a['US10Y_weekly']} | {a['SPX_running_day']} | {a['BTCUSD_running_day']} |"
        )
    L += [
        "",
        "**Daily macro label state at entry, and whipsaw true / false / unknown**",
        "",
        "| ledger | n | unavailable | available but mixed | directional | of which with "
        "| of which against | whipsaw true | whipsaw false | whipsaw unknown |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name, a in rows:
        m, w = a["macro_state"], a["whipsaw"]
        L.append(
            f"| {name} | {a['n']} | {m['unavailable']} | {m['mixed_available']} "
            f"| {m['directional']} | {a['directional_with']} | {a['directional_against']} "
            f"| {w['true']} | {w['false']} | {w['unknown']} |"
        )
    L.append("")
    return L


def write_md(rc: dict) -> None:
    p = rc["pooled"]
    pa = p["trade_availability"]
    L = []
    L.append("# Macro-regime receipt (TVB-35) -- characterization only\n")
    L.append(
        "Amended 2026-10-11 (TVB-38, Codex TVB-35 audit F6/F7): labels now use only bars "
        "completed at entry; whipsaw states are true/false/unknown. Numbers below regenerated.\n"
    )
    L.append(
        "Every closed trade of the three live ledgers labeled with the macro reference\n"
        "set as it was KNOWN at entry time; every decision row labeled at its own instant.\n"
        "Labels were fixed a-priori in `receipt.py`'s docstring before any number was read.\n"
        f"{p['closed_trades']} trades: this shows the labels are computable and maps the\n"
        "ceiling; it validates nothing. Known-at-entry holds by construction: a 60m bar counts\n"
        "only from its close (open + 60 minutes); price now is the latest COMPLETED 60m close;\n"
        "the running day uses only completed 60m bars; a reference whose latest completed\n"
        "60m bar closed more than 2 hours earlier is closed at that instant, and a day or week\n"
        "whose first 60m bar has not started yet has no known open. Each reference keeps its\n"
        "own session clock (daily open hour UTC below).\n"
    )
    L.append("| ref | 60m bars | first | last | daily bar opens (UTC) |")
    L.append("|---|---|---|---|---|")
    for k, v in rc["refs"].items():
        f = datetime.fromtimestamp(v["h60"][1], UTC).strftime("%m-%d %H:%M") if v["h60"][1] else "-"
        last = (
            datetime.fromtimestamp(v["h60"][2], UTC).strftime("%m-%d %H:%M") if v["h60"][2] else "-"
        )
        L.append(f"| {k} | {v['h60'][0]} | {f} | {last} | {v['daily_open_utc_hour']} |")
    L.append("")
    n = rc["now"]
    L.append(
        f"**At harvest ({n['ts'][:16]}Z):** dollar daily {n['DXY_d']} / weekly {n['DXY_w']}; "
        f"10-year daily {n['US10Y_d']} / weekly {n['US10Y_w']}; WTI daily {n['CL1_d']}; "
        f"Brent daily {n['BRN1_d']}; S&P daily {n['SPX_d']}; BTC daily {n['BTCUSD_d']}; "
        f"macro_dir {n['macro_dir']} (weekly {n['macro_dir_w']}); whipsaw {tri(n['whipsaw'])}.\n"
    )
    m, w = pa["macro_state"], pa["whipsaw"]
    L.append(
        f"**Coverage first.** Both the dollar and the 10-year daily dots were live at entry on "
        f"{pa['dollar_and_10y_daily']} of {pa['n']} trades; of those, {m['directional']} had a "
        f"directional label ({pa['directional_with']} with, {pa['directional_against']} against) "
        f"and {m['mixed_available']} disagreed or were flat. The whipsaw flag was true on "
        f"{w['true']}, false on {w['false']}, and unknown on {w['unknown']}. Unknown means a "
        "reference was missing or closed and is never counted as false, so this coverage "
        "supports no reading about the flag's effect.\n"
    )
    L.append("## Pooled (all three ledgers)\n")
    L += _avail_tables(
        [(name, lg["trade_availability"]) for name, lg in rc["ledgers"].items()] + [("pooled", pa)]
    )
    L += _tbl(
        "By alignment with the DAILY dollar+10-year label "
        "(with = long in tailwind / short in headwind)",
        p["by_alignment"],
    )
    L += _tbl(
        "By daily label state (unavailable / available but mixed / directional)",
        p["by_macro_state"],
    )
    L += _tbl("By alignment with the WEEKLY label", p["by_alignment_weekly"])
    L += _tbl(
        "By whipsaw (S&P or BTC running outside day at entry; unknown kept apart)",
        p["by_whipsaw"],
    )
    L += _tbl("By trade direction x daily macro label", p["by_dir_x_macro"])
    for name, lg in rc["ledgers"].items():
        L.append(f"## {name} ({lg['window'][0][:16]}Z .. {lg['window'][1][:16]}Z)\n")
        L.append(
            f"Closed trades {lg['closed_trades']}; decision rows {lg['decision_rows']} "
            f"(dollar or 10-year daily dot unavailable on {lg['decision_rows_macro_na']}); "
            f"rows by label state {lg['decision_rows_by_macro_state']}; rows by macro_dir "
            f"{lg['decision_rows_by_macro_dir']}; rows by whipsaw "
            f"{lg['decision_rows_by_whipsaw']}; entries by macro_dir "
            f"{lg['entries_by_macro_dir']}; entries by alignment {lg['entries_by_alignment']}.\n"
        )
        L += _tbl("Trades by alignment (daily)", lg["trades_by_alignment"])
        L += _tbl("Trades by whipsaw", lg["trades_by_whipsaw"])
    L.append("## Reading rules\n")
    L.append(
        "- A cell with fewer than ~10 trades is a question, not a reading.\n"
        "- `mixed` in the alignment tables pools two different things: an input that was\n"
        "  unavailable (closed or no history) and two live inputs that disagreed or were flat.\n"
        "  The label-state table keeps them apart; read coverage before any alignment cell.\n"
        "- The whipsaw flag is a running check: a day can become an outside day AFTER the entry.\n"
        "  `unknown` means a reference's running day was not computable at entry (no history,\n"
        "  reference closed, or no completed hour yet in its day). It is never folded into false.\n"
        "- Nothing here is a gate. A live label would be shadow-journaled first (the BTC drift\n"
        "  veto is the template) and receipted again on the next tape.\n"
    )
    (HERE / "REGIME_RECEIPT.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
