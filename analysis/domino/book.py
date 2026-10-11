"""TVB-37 product 2b -- the R-matched check and the book view: two VIEWS of the chance units.

Pre-registration: docs/experiments/tvb37_chance_comparison_prereg.md, amendment A3 (declared
2026-10-10 BEFORE this file existed, at the owner's request for "p/l or percent performance even if
it's a hypothetical account (no leverage, no fees, single buy)"). Nothing here adds a condition or
a cut; it re-reads the units that analysis/domino/chance.py produces.

  R-matched   within each (timeframe, setup): units binned by setup-bar size (R as % of price) into
              five bins at the quintiles of the comparison base; stacked minus base per bin; the
              matched difference = the bin differences weighted by the STACKED group's bin shares
  book        every unit at ONE unit of notional, long or short as the break: no leverage, fees,
              funding or slippage, every trade taken, no compounding; closed at +R% on one R, -R%
              on the stop, else marked to the close of the horizon's last bar (3 and 5 bars);
              per cell: trades, average / median % per trade, hit rate, expectancy in R, total and
              max drawdown on a 1,000-dollar-per-trade book (sum of equal-size trades by entry
              date -- NOT an account balance), distinct dates; curves for a declared handful.
              Drawdown is measured from a zero start: a book that opens by losing shows that
              loss as drawdown.

Close-out audit folds (docs/reviews/tvb37-close-codex-audit.md): F1 zero-seeded drawdown; F2
R-matched coverage (unavailable on zero shared bins, `covered` and the effective count published,
partial cover labelled conditional); F3 each horizon greyed on its OWN valid stacked count; F8
strict JSON (non-finite values to null, the open top bin edge as r_to null + r_to_unbounded true).

Everything here is arithmetic on counts. It is a presentation of the same chances, not a strategy.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.domino.census import aggregate, day_start, fetch_daily, liquid, normalize, universe
from analysis.domino.chance import (
    CLASSES,
    KINDS,
    MIN_CELL,
    PATTERN_TFS,
    STACKED,
    cached_universe,
    coin_units,
    flag_mask,
    horizon_ends,
    parse_as_of,
    venue_era,
)

HERE = Path(__file__).parent
RESULTS = HERE / "results"
BOOK_H = (3, 5)
UNIT_USD = 1000.0
LEVELS = ("all", "third", "strict")
# cells whose cumulative curves are stored (prereg A3), as (tf, kind, flag level, class)
CURVES = (
    ("D", "continuation", "all", "plain"),
    ("D", "continuation", "all", "exact_shared"),
    ("D", "continuation", "all", "near"),
    ("D", "continuation", "all", "within1"),
    ("D", "reversal", "all", "plain"),
    ("D", "reversal", "third", "plain"),
    ("D", "inside", "all", "plain"),
    ("D", "inside", "third", "plain"),
    ("W", "continuation", "all", "exact_shared"),
    ("W", "continuation", "all", "rest"),
    ("W", "reversal", "all", "exact_shared"),
    ("W", "reversal", "all", "rest"),
)


# ----------------------------------------------------------------------------- rows


def coin_book_rows(meta: dict, daily: list[dict]) -> list[dict]:
    """The chance units of one coin with the book's return per horizon attached (prereg A3).

    ret{n} = +R% on one R, -R% on the stop, the signed move from the level to the close of the
    horizon's last bar when neither, None when censored. rr{n} = the same in R.
    """
    units, _counts = coin_units(meta, daily)
    if not units:
        return []
    buckets = {tf: aggregate(daily, tf) for tf in ("W", "M", "Q")}
    bucket_of = {
        tf: {di: b for b, bk in enumerate(buckets[tf]) for di in bk["days"]} for tf in ("W", "M")
    }
    idx = {
        datetime.fromtimestamp(d["t"] / 1000, tz=timezone.utc).strftime("%Y-%m-%d"): k
        for k, d in enumerate(daily)
    }
    for u in units:
        i = idx[u["date"]]
        ends = horizon_ends(u["tf"], i, daily, buckets, bucket_of)
        sign = 1.0 if u["direction"] == "up" else -1.0
        for n in BOOK_H:
            out = u[f"out{n}"]
            if out == "one_r":
                ret, rr = u["r_pct"], 1.0
            elif out == "stop":
                ret, rr = -u["r_pct"], -1.0
            elif out == "neither":
                close = daily[ends[n]]["c"]
                ret = sign * (close - u["level"]) / u["level"] * 100.0
                rr = ret / u["r_pct"]
            else:
                ret, rr = None, None
            u[f"ret{n}"] = ret
            u[f"rr{n}"] = rr
    return units


# ----------------------------------------------------------------------------- the book


def book_cell(df: pd.DataFrame, n: int) -> tuple[dict, pd.Series | None]:
    """Book metrics for one cell at horizon n, plus the cumulative P/L curve by entry date."""
    v = df[df[f"ret{n}"].notna()]
    m = int(len(v))
    if m == 0:
        return {"n": 0}, None
    ret = v[f"ret{n}"].astype(float)
    k = int((v[f"out{n}"] == "one_r").sum())
    by_day = (ret.groupby(v["date"]).sum().sort_index() * UNIT_USD / 100.0).astype(float)
    cum = by_day.cumsum()
    # the book starts at zero: the high-water mark is never below it (close-out audit F1)
    peak = cum.cummax().clip(lower=0.0)
    dd = float(min(0.0, (cum - peak).min()))
    return {
        "n": m,
        "dates": int(v["date"].nunique()),
        "avg_pct": float(ret.mean()),
        "med_pct": float(ret.median()),
        "hit": k / m,
        "stop": float((v[f"out{n}"] == "stop").mean()),
        "neither": float((v[f"out{n}"] == "neither").mean()),
        "exp_r": float(v[f"rr{n}"].astype(float).mean()),
        "total_usd": float(ret.sum() * UNIT_USD / 100.0),
        "max_dd_usd": dd,
        "avg_r_pct": float(v["r_pct"].median()),
    }, cum


def select(df: pd.DataFrame, tf: str, kind: str, level: str, cls: str) -> pd.DataFrame:
    sub = df[(df["tf"] == tf) & (df["kind"] == kind) & flag_mask(df, level)]
    if cls == "rest":
        return sub[~sub["cls"].isin(STACKED)]
    if cls == "stacked":
        return sub[sub["cls"].isin(STACKED)]
    return sub[sub["cls"] == cls]


def _usd(x: float) -> str:
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:+,.0f}"


def _pct(x: float, signed: bool = False) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "-"
    return f"{100 * x:+.1f}%" if signed else f"{100 * x:.1f}%"


def _grey(n: int, text: str) -> str:
    return f"({text})" if n < MIN_CELL else text


def table_book(df: pd.DataFrame, tf: str, title: str, levels: tuple = LEVELS) -> list[str]:
    """Rows = setup x flag x class; the book at 3 and 5 bars."""
    lines = [f"### {title}", ""]
    lines.append(
        "| setup | flag | class | trades (5) | dates | avg % per trade, 3 / 5 | median % (5) | hit (5) | "
        "stopped (5) | expectancy R (5) | total $ at 1,000 per trade (3 / 5) | max drawdown $ (5) | median R % |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    classes = CLASSES if tf == "D" else CLASSES[1:]
    for kind in KINDS:
        for level in levels:
            for cls in classes:
                part = select(df, tf, kind, level, cls)
                if part.empty:
                    continue
                c3, _ = book_cell(part, 3)
                c5, _ = book_cell(part, 5)
                if c5["n"] == 0:
                    continue
                g = lambda t: _grey(c5["n"], t)  # noqa: E731
                lines.append(
                    f"| {kind} | {level} | {cls} | {c5['n']:,} | {c5['dates']:,} | "
                    f"{g(f'{c3.get("avg_pct", math.nan):+.2f} / {c5["avg_pct"]:+.2f}')} | {g(f'{c5["med_pct"]:+.2f}')} | "
                    f"{g(_pct(c5['hit']))} | {g(_pct(c5['stop']))} | {g(f'{c5["exp_r"]:+.3f}')} | "
                    f"{g(f'{_usd(c3.get("total_usd", math.nan))} / {_usd(c5["total_usd"])}')} | {g(_usd(c5['max_dd_usd']))} | "
                    f"{c5['avg_r_pct']:.2f} |"
                )
    lines.append("")
    lines.append(
        "One unit of notional per trade, long or short as the break, no leverage, fees, funding or "
        "slippage, every trade taken, no compounding; open trades marked at the close of the horizon's "
        "last bar. The dollar columns are the SUM of equal-size trades on a 1,000-dollar-per-trade book, "
        "not an account balance (many trades are open at once). Cells in parentheses hold fewer than "
        "30 trades."
    )
    lines.append("")
    return lines


# ----------------------------------------------------------------------------- R-matched


def base_name(tf: str) -> str:
    """The comparison base of the R-matched check: PLAIN for daily units, the rest otherwise."""
    return "plain" if tf == "D" else "within1 + spread"


def r_matched(df: pd.DataFrame, tf: str, kind: str, level: str, cls: str, n: int) -> dict:
    """Stacked-class minus base one-R chance at horizon n, raw and reweighted to the stacked group's
    setup-bar sizes (five bins at the base's R quintiles). Returns the bins too (prereg A3).

    `covered` = the share of stacked units sitting in a bin that also holds base units, and
    `n_effective` = their count (close-out audit F2). The matched difference is taken over the
    covered units only: below full cover it is CONDITIONAL on them (`conditional` true); with no
    covered unit it is unavailable (`available` false, matched and interval NaN), never a
    division by zero. n_stacked / n_base are VALID counts at horizon n (censored excluded).
    """
    sub = df[(df["tf"] == tf) & (df["kind"] == kind) & flag_mask(df, level)]
    sub = sub[sub[f"out{n}"] != "censored"]
    base = sub[sub["cls"] == "plain"] if tf == "D" else sub[~sub["cls"].isin(STACKED)]
    stk = sub[sub["cls"].isin(STACKED)] if cls == "stacked" else sub[sub["cls"] == cls]
    out = {
        "tf": tf,
        "kind": kind,
        "flag": level,
        "cls": cls,
        "base": base_name(tf),
        "n_stacked": int(len(stk)),
        "n_base": int(len(base)),
    }
    unavailable = {
        "matched": math.nan,
        "lo": math.nan,
        "hi": math.nan,
        "available": False,
        "n_effective": 0,
        "conditional": False,
    }
    if len(base) < MIN_CELL or len(stk) == 0:
        out.update({"raw": math.nan, "bins": [], "covered": math.nan} | unavailable)
        return out
    edges = base["r_pct"].quantile([0.2, 0.4, 0.6, 0.8]).to_numpy()
    b_bin = np.searchsorted(edges, base["r_pct"].to_numpy(), side="right")
    s_bin = np.searchsorted(edges, stk["r_pct"].to_numpy(), side="right")
    p_s_all = float((stk[f"out{n}"] == "one_r").mean())
    p_b_all = float((base[f"out{n}"] == "one_r").mean())
    bins = []
    matched = 0.0
    var = 0.0
    used = 0
    for b in range(5):
        sb = stk[s_bin == b]
        bb = base[b_bin == b]
        ns, nb = int(len(sb)), int(len(bb))
        ps = float((sb[f"out{n}"] == "one_r").mean()) if ns else math.nan
        pb = float((bb[f"out{n}"] == "one_r").mean()) if nb else math.nan
        lo_edge = float(edges[b - 1]) if b > 0 else 0.0
        hi_edge = float(edges[b]) if b < 4 else None  # the top bin is open-ended (audit F8)
        bins.append(
            {
                "bin": b,
                "r_from": lo_edge,
                "r_to": hi_edge,
                "r_to_unbounded": b == 4,
                "n_stacked": ns,
                "n_base": nb,
                "p_stacked": ps,
                "p_base": pb,
                "diff": (ps - pb) if ns and nb else math.nan,
            }
        )
        if ns and nb:
            w = ns / len(stk)
            matched += w * (ps - pb)
            var += w * w * (ps * (1 - ps) / ns + pb * (1 - pb) / nb)
            used += ns
    if used == 0:  # no stacked unit shares a bar-size bin with the base: nothing to match on
        out.update({"raw": p_s_all - p_b_all, "bins": bins, "covered": 0.0} | unavailable)
        return out
    if used < len(stk):  # renormalise over the covered units; the estimate is then conditional
        matched *= len(stk) / used
        var *= (len(stk) / used) ** 2
    se = math.sqrt(var)
    out.update(
        {
            "raw": p_s_all - p_b_all,
            "matched": matched,
            "lo": matched - 1.96 * se,
            "hi": matched + 1.96 * se,
            "bins": bins,
            "available": True,
            "covered": used / len(stk),
            "n_effective": int(used),
            "conditional": used < len(stk),
        }
    )
    return out


def matched_txt(r: dict) -> str:
    """The matched difference with its interval, or why there is none; conditional when partial."""
    if not r.get("available"):
        return "unavailable (no shared bar-size bin)" if r.get("covered") == 0.0 else "-"
    txt = f"{_pct(r['matched'], True)} [{100 * r['lo']:+.0f}, {100 * r['hi']:+.0f}]"
    if r["conditional"]:
        txt += f" conditional on {100 * r['covered']:.0f}% of stacked"
    return txt


def table_r_matched(df: pd.DataFrame) -> list[str]:
    lines = [
        "### R-matched check: stacked minus base one-R chance, raw and reweighted to the stacked group's setup-bar sizes",
        "",
    ]
    lines.append(
        "| timeframe | setup | flag | stacked class | base | valid stacked by 3 / 5 | valid base by 3 / 5 | "
        "covered by 3 / 5 | raw diff by 3 | matched by 3 [95%] | raw diff by 5 | matched by 5 [95%] |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    results = []
    for tf in PATTERN_TFS:
        for kind in KINDS:
            for level in ("all", "third"):
                for cls in ("stacked", "exact_shared", "near"):
                    r3 = r_matched(df, tf, kind, level, cls, 3)
                    r5 = r_matched(df, tf, kind, level, cls, 5)
                    if r3["n_stacked"] == 0 or math.isnan(r3["raw"]):
                        continue
                    results.append({"h3": r3, "h5": r5})
                    # each horizon is greyed on ITS OWN valid stacked count (close-out audit F3)
                    g3 = lambda t: _grey(r3["n_stacked"], t)  # noqa: E731
                    g5 = lambda t: _grey(r5["n_stacked"], t)  # noqa: E731
                    lines.append(
                        f"| {tf} | {kind} | {level} | {cls} | {r3['base']} | "
                        f"{r3['n_stacked']:,} / {r5['n_stacked']:,} | {r3['n_base']:,} / {r5['n_base']:,} | "
                        f"{_pct(r3['covered'])} / {_pct(r5['covered'])} | "
                        f"{g3(_pct(r3['raw'], True))} | {g3(matched_txt(r3))} | "
                        f"{g5(_pct(r5['raw'], True))} | {g5(matched_txt(r5))} |"
                    )
    lines.append("")
    lines.append(
        "Base = PLAIN for daily units, WITHIN 1% + SPREAD for weekly and monthly. Bins = the base's R "
        "quintiles; the matched difference weights each bin's difference by the stacked group's share "
        "in that bin. Valid = censored units excluded at that horizon. Covered = the share of stacked "
        "units in a bin that also holds base units; below 100% the matched figure is conditional on "
        "those units, at 0% it is unavailable. Cells in parentheses: fewer than 30 valid stacked units "
        "at THAT horizon. A shrinking matched gap is attenuation after reweighting to the stacked "
        "group's bar sizes, not proof that bar size caused the raw gap."
    )
    lines.append("")
    return lines, results


def table_bins(r: dict, title: str) -> list[str]:
    lines = [f"### {title}", ""]
    lines.append(
        "| setup-bar size (R % of price) | n stacked | n base | stacked one R | base one R | diff |"
    )
    lines.append("|---|---|---|---|---|---|")
    for b in r["bins"]:
        hi = "and up" if b["r_to_unbounded"] else f"to {b['r_to']:.2f}"
        lines.append(
            f"| {b['r_from']:.2f} {hi} | {b['n_stacked']:,} | {b['n_base']:,} | {_pct(b['p_stacked'])} | {_pct(b['p_base'])} | {_pct(b['diff'], True)} |"
        )
    lines.append("")
    return lines


# ----------------------------------------------------------------------------- main


def _curve_points(cum: pd.Series, max_points: int = 300) -> list:
    if cum is None or cum.empty:
        return []
    step = max(1, math.ceil(len(cum) / max_points))
    pts = [[d, round(float(v), 2)] for k, (d, v) in enumerate(cum.items()) if k % step == 0]
    last = [cum.index[-1], round(float(cum.iloc[-1]), 2)]
    if pts[-1][0] != last[0]:
        pts.append(last)
    return pts


def strict_json(x: object) -> object:
    """Non-finite floats to null and numpy scalars to Python, recursively (close-out audit F8)."""
    if isinstance(x, dict):
        return {k: strict_json(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [strict_json(v) for v in x]
    if isinstance(x, np.generic):
        x = x.item()
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return x


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="TVB-37 book view and R-matched check")
    ap.add_argument(
        "--as-of",
        help="YYYY-MM-DD: rerun OFFLINE on the cached candle snapshot of that date (no venue call); "
        "default = today with the live universe and a fresh fetch",
    )
    args = ap.parse_args(argv)
    RESULTS.mkdir(parents=True, exist_ok=True)
    if args.as_of:
        as_of = parse_as_of(args.as_of)
        uni = cached_universe(as_of)
        print(f"universe: {len(uni)} cached perps (offline, as of {args.as_of})", flush=True)
    else:
        as_of = day_start(int(time.time() * 1000))
        uni = universe()
        print(f"universe: {len(uni)} live perps", flush=True)
    rows: list[dict] = []
    excluded = []
    for n, u in enumerate(uni, 1):
        try:
            raw = fetch_daily(u["coin"], as_of)
        except Exception as exc:  # noqa: BLE001
            excluded.append({"coin": u["coin"], "reason": f"fetch failed: {exc}"})
            continue
        st: dict = {}
        daily = normalize(raw, as_of, st)
        if st["gap_days"] or st["duplicates"] or st["unaligned"]:
            excluded.append({"coin": u["coin"], "reason": f"data quality {st}"})
            continue
        meta = {"coin": u["coin"], "dex": u["dex"], "liquid": liquid(daily)}
        rows += coin_book_rows(meta, venue_era(daily))
        if n % 50 == 0:
            print(f"  {n}/{len(uni)} coins, {len(rows):,} units", flush=True)
    df = pd.DataFrame(rows)
    md = [
        f"# Book view and R-matched check, as of {datetime.fromtimestamp(as_of / 1000, tz=timezone.utc):%Y-%m-%d} UTC (generated by analysis/domino/book.py; venue era)",
        "",
    ]
    md.append(
        f"{df['coin'].nunique()} coins, {len(df):,} units ("
        + ", ".join(f"{tf} {int((df.tf == tf).sum()):,}" for tf in PATTERN_TFS)
        + "). Trades at 5 bars exclude censored units."
    )
    md.append("")
    md += table_book(df, "D", "The book, daily units")
    md += table_book(df, "W", "The book, weekly units", levels=("all", "third"))
    md += table_book(df, "M", "The book, monthly units", levels=("all",))
    rm_lines, rm_results = table_r_matched(df)
    md += rm_lines
    head_d = r_matched(df, "D", "continuation", "all", "stacked", 3)
    head_w = r_matched(df, "W", "continuation", "all", "exact_shared", 3)
    head_wr = r_matched(df, "W", "reversal", "all", "exact_shared", 3)
    md += table_bins(head_d, "Bins: daily 2-2 continuation, stacked vs plain, one R by 3 bars")
    md += table_bins(
        head_w, "Bins: weekly 2-2 continuation, exact shared open vs the rest, one R by 3 weeks"
    )
    md += table_bins(
        head_wr, "Bins: weekly 2-2 reversal, exact shared open vs the rest, one R by 3 weeks"
    )
    (RESULTS / "book_tables.md").write_text("\n".join(md), encoding="utf-8")
    cells = []
    curves = {}
    for tf in PATTERN_TFS:
        for kind in KINDS:
            for level in LEVELS:
                for cls in tuple(CLASSES) + ("rest", "stacked"):
                    part = select(df, tf, kind, level, cls)
                    if part.empty:
                        continue
                    rec = {"tf": tf, "kind": kind, "flag": level, "cls": cls}
                    for n in BOOK_H:
                        c, cum = book_cell(part, n)
                        rec[f"h{n}"] = {
                            k: (None if isinstance(v, float) and math.isnan(v) else v)
                            for k, v in c.items()
                        }
                        if n == 5 and (tf, kind, level, cls) in CURVES:
                            curves[f"{tf}|{kind}|{level}|{cls}"] = _curve_points(cum)
                    cells.append(rec)
    out = {
        "as_of_utc": datetime.fromtimestamp(as_of / 1000, tz=timezone.utc).strftime("%Y-%m-%d"),
        "definitions": "docs/experiments/tvb37_chance_comparison_prereg.md (amendment A3)",
        "unit_usd": UNIT_USD,
        "horizons": list(BOOK_H),
        "units": int(len(df)),
        "excluded": excluded,
        "cells": cells,
        "curves": curves,
        "r_matched": [
            {k: (v if k != "bins" else v) for k, v in r["h3"].items()}
            | {"h5": {k: v for k, v in r["h5"].items() if k != "bins"}}
            for r in rm_results
        ],
    }
    with open(RESULTS / "book.json", "w") as fh:
        json.dump(strict_json(out), fh, indent=1, allow_nan=False)
    print("\n".join(md[:40]))
    print(f"... tables written to {RESULTS / 'book_tables.md'}")


if __name__ == "__main__":
    sys.exit(main())
