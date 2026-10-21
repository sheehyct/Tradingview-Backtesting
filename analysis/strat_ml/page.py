"""Assemble the phone page: the report HTML plus the follow-up sections (stop head-to-head,
excursion clock, pivot ladder, ticker census, equity perps) from their JSON receipts, in the
claude.ai artifact page contract (no document skeleton, title + style first, safe-area gutter).

  uv run python -m analysis.strat_ml.page --date 2026-10-20 --out /path/to/page.html
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
REPORTS = HERE / "reports"


def tbl(rows, cols, names=None) -> str:
    names = names or {}
    head = "".join(f"<th>{html.escape(names.get(c, c.replace('_', ' ')))}</th>" for c in cols)
    body = []
    for row in rows:
        cells = []
        for c in cols:
            v = row.get(c)
            if v is None or (isinstance(v, float) and v != v):
                cells.append("<td></td>")
            elif isinstance(v, bool):
                cells.append(f"<td>{'yes' if v else ''}</td>")
            elif isinstance(v, float) and (c.endswith("pct") or c.startswith("by_")):
                cells.append(f"<td>{v:.1f}%</td>")
            elif isinstance(v, float) and c.endswith("share"):
                cells.append(f"<td>{100 * v:.0f}%</td>")
            elif isinstance(v, float) and (
                "mean_r" in c or "median_r" in c or c in ("sum_r", "diff_mean_r", "mean_ret_atr")
            ):
                cells.append(f"<td>{v:+.3f}</td>")
            elif isinstance(v, float):
                cells.append(f"<td>{v:.2f}</td>")
            elif isinstance(v, int):
                cells.append(f"<td>{v:,}</td>")
            else:
                cells.append(f"<td>{html.escape(str(v))}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return f"<div class=tw><table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table></div>"


def plain(text: str) -> str:
    return f"<div class=plain>{text}</div>"


def section_stops(d: dict) -> str:
    names = {
        "mode": "stop",
        "stop_first_pct": "stop first %",
        "tgt_first_pct": "target first %",
        "mean_ret_pct": "mean ret % of price",
        "median_ret_pct": "median ret %",
        "mean_ret_atr": "mean ret (ATR)",
        "median_rr": "median R:R",
        "median_stop_atr": "median stop (ATR)",
    }
    cols = [
        "mode",
        "n",
        "win_pct",
        "stop_first_pct",
        "tgt_first_pct",
        "mean_r",
        "median_r",
        "mean_ret_pct",
        "median_ret_pct",
        "mean_ret_atr",
        "median_rr",
        "median_stop_atr",
    ]
    return (
        "<h2>6. Stop placement head-to-head: setup-bar stop vs bar-0 stop (inside breaks)</h2>"
        + plain(
            "<b>What this is.</b> The same inside-break rows run twice: once with the stop at the far side of the setup bar (the TVB-37 convention) and once with the stop at the far side of bar 0, the bar the inside bar sits inside (the STRAT skill's structural stop). Everything else is identical. Because R changes with the stop, read the columns in <i>percent of price</i> and <i>ATRs</i>: they do not move with the stop."
        )
        + tbl(d["all"], cols, names)
        + plain(
            "<b>Reading.</b> The wider stop lifts the win rate seven points and cuts stop-outs ten points, and the money per trade does not change. The stop decides how the book loses (many small stop-outs, or fewer larger ones), not whether it loses."
        )
        + "<h3>6a. By pattern</h3>"
        + tbl(d["pattern"], ["pattern"] + cols, names)
        + "<h3>6b. By year</h3>"
        + tbl(
            d["year"],
            [
                "year",
                "mode",
                "n",
                "win_pct",
                "stop_first_pct",
                "mean_ret_pct",
                "median_ret_pct",
                "mean_ret_atr",
            ],
            names,
        )
        + "<h3>6c. The whole book (only the inside rows changed)</h3>"
        + tbl(
            d["book"],
            ["mode", "n", "win_pct", "stop_first_pct", "mean_ret_pct", "median_ret_pct"],
            names,
        )
    )


def section_excursion(d: dict) -> str:
    reach_cols = [
        "side",
        "threshold_r",
        "n",
        "by_6h",
        "by_12h",
        "by_24h",
        "by_48h",
        "by_72h",
        "by_240h",
        "median_hours_when_reached",
    ]
    stop_cols = [
        "threshold_r",
        "clock_h",
        "n",
        "reached_pct",
        "exit_now_pct",
        "hold_mean_r",
        "rule_mean_r",
        "reached_mean_r",
        "not_reached_open_mean_r",
        "exit_mark_mean_r",
    ]
    names = {
        "threshold_r": "threshold (R)",
        "clock_h": "clock (h)",
        "median_hours_when_reached": "median hours when reached",
        "reached_pct": "reached by then",
        "exit_now_pct": "rule exits",
        "hold_mean_r": "hold: mean R",
        "rule_mean_r": "rule: mean R",
        "reached_mean_r": "reached: mean R",
        "not_reached_open_mean_r": "laggards: mean R if held",
        "exit_mark_mean_r": "laggards: mark at exit",
        "first_excursion": "first 0.25R move",
        "share_pct": "share",
        "tgt_first_pct": "target first %",
        "stop_first_pct": "stop first %",
        "fav_05_by_24h_pct": "+0.5R within 24h",
        "adv_05_by_24h_pct": "-0.5R within 24h",
        "fav_first_pct": "favourable first %",
        "median_h_fav_05": "median hours to +0.5R",
    }
    ctx = [
        r for r in d["context"] if r["slice"] in ("family", "tfc_score", "hour_bucket", "liq_tier")
    ]
    return (
        "<h2>7. The excursion clock: does the move show up soon?</h2>"
        + plain(
            '<b>What this is.</b> The owner\'s question: STRAT exits are often discretionary ("it turned against me"). Can the data say how soon a good trade shows itself? For every trigger we record the hour at which the trade first reached +0.25R, +0.5R and +1R in its favour, the same against it, and the mark-to-market at fixed hours. Hours are hourly bars after the trigger bar.'
        )
        + "<h3>7a. Share of trades reaching the move within H hours</h3>"
        + tbl(d["reach"], reach_cols, names)
        + plain(
            "Half of all triggers show +0.25R within 6 hours; +0.5R takes about 15 hours for the median trade that gets there at all, and a third of the +1R touches arrive after day 3. The adverse side mirrors it at 0.5R and 1R."
        )
        + "<h3>7b. Which 0.25R move came first, and how those trades ended</h3>"
        + tbl(
            d["first"],
            [
                "first_excursion",
                "n",
                "share_pct",
                "win_pct",
                "tgt_first_pct",
                "stop_first_pct",
                "mean_r",
                "median_r",
            ],
            names,
        )
        + plain(
            "<b>Read with care.</b> This counts the trigger hour's own low against the trade (the low may have printed before the break; the data cannot tell). Ignoring that hour, 70% of trades go in favour first and 27% against first. Which version is true needs 15-minute bars, which the archive has."
        )
        + "<h3>7c. A time-stop rule vs just holding (same rows)</h3><p class=muted>Rule: at hour H, if the trade has not shown +x R and is still open, exit at that hour's close; otherwise manage as before.</p>"
        + tbl(d["time_stop"], stop_cols, names)
        + plain(
            "The split is dramatic, but the rule barely moves the book: by the time a trade has visibly not moved, its price already carries most of the loss. The clock describes laggards well; it does not rescue them."
        )
        + "<h3>7d. Who shows +0.5R within 24 hours</h3>"
        + tbl(
            ctx,
            [
                "slice",
                "value",
                "n",
                "fav_05_by_24h_pct",
                "adv_05_by_24h_pct",
                "fav_first_pct",
                "median_h_fav_05",
                "mean_r",
                "win_pct",
            ],
            names,
        )
        + plain(
            "<b>The continuity score surprise, explained.</b> tfc_score = 1 (week and month both already Type 2 in the trade's direction) has the worst results in every family, and it is the blue-sky cell by construction: both prior levels are already broken, so nothing structural sits beyond the entry. The colour-only version of continuity goes the expected way in every family. Continuity, and exhaustion risk."
        )
    )


def section_ladder(d: dict) -> str:
    rung_cols = [
        "family",
        "n",
        "reached_1_pct",
        "reached_2_pct",
        "reached_3_pct",
        "reached_4_pct",
        "mean_rungs_reached",
        "median_h_rung1",
        "median_h_rung2",
        "median_h_rung3",
        "t1_dist_r_median",
        "t3_dist_r_median",
    ]
    rn = {
        "reached_1_pct": "rung 1 reached",
        "reached_2_pct": "rung 2",
        "reached_3_pct": "rung 3",
        "reached_4_pct": "rung 4",
        "mean_rungs_reached": "mean rungs",
        "median_h_rung1": "hours to rung 1",
        "median_h_rung2": "to rung 2",
        "median_h_rung3": "to rung 3",
        "t1_dist_r_median": "rung 1 R:R",
        "t3_dist_r_median": "rung 3 R:R",
    }
    book_cols = [
        "pattern",
        "n",
        "same_t1_pct",
        "tvb37_rr_median",
        "pine_rr_median",
        "tvb37_tgt_first_pct",
        "pine_tgt_first_pct",
        "tvb37_mean_r",
        "pine_mean_r",
        "diff_mean_r",
    ]
    bn = {
        "same_t1_pct": "same T1",
        "tvb37_rr_median": "TVB-37 R:R",
        "pine_rr_median": "Pine R:R",
        "tvb37_tgt_first_pct": "TVB-37 target first",
        "pine_tgt_first_pct": "Pine target first",
        "tvb37_mean_r": "TVB-37 mean R",
        "pine_mean_r": "Pine mean R",
        "diff_mean_r": "difference",
    }
    return (
        "<h2>8. The pivot ladder: how far price climbs</h2>"
        + plain(
            "<b>What this is.</b> The owner's live indicator projects a ladder: T1 is the reclaim level (the anchor bar's wick) and T2 onward are the prior highs or lows not yet taken out, nearest first. The daily research line had kept only week and month levels. The Pine's ladder is now built for every daily trigger, and we count how many rungs the favourable move reached within 10 bars and how many hours each took."
        )
        + tbl(d["rungs_family"], rung_cols, rn)
        + plain(
            f"Four trades in five reach rung 1 within 10 bars, half reach rung 3, stable year to year. Of the {d['no_target_rows']:,} rows the week / month ladder left without a target, the Pine gives {d['no_target_with_rung']:,} a rung."
        )
        + "<h3>8a. The Pine's T1 against the week / month T1, same rows, same stop</h3>"
        + tbl(d["book_pattern"], book_cols, bn)
        + plain(
            "Reversals already used the same level. For continuations, with-trend inside breaks and outside breaks the Pine's T1 is the nearest untaken daily extreme: much closer, hit far more often, and the mean R improves by a few hundredths while staying at or under zero. The ladder makes the book flatter and busier; it does not make it positive per unit of risk."
        )
    )


def section_census(d: dict) -> str:
    tc = [
        "rank",
        "symbol",
        "n",
        "years",
        "eff_patterns",
        "continuation_share",
        "win_pct",
        "mean_r",
        "sum_r",
        "mean_r_no_stop",
        "z",
        "stable",
    ]
    tn = {
        "eff_patterns": "effective patterns",
        "continuation_share": "continuation share",
        "mean_r_no_stop": "mean R no stop",
        "z": "z (vs own noise)",
    }
    c = d["correlations"]
    return (
        "<h2>9. The overfit and underfit ticker census</h2>"
        + plain(
            f"<b>What this is.</b> Which coins carried the most patterns and did best, which did worst. A labelled overfit census, for picking apart, never for picking. A coin with 1,000 rows and no edge would show a mean R anywhere within about &plusmn;{2 * d['noise_sd_median']:.2f} by chance, so <b>z</b> (mean R divided by the coin's own noise) is the column to read. Coins with at least {d['min_rows']} rows: {d['coins']}."
        )
        + "<h3>9a. The overfit end</h3>"
        + tbl(d["top"], tc, tn)
        + "<h3>9b. The underfit end</h3>"
        + tbl(d["bottom"], tc, tn)
        + plain(
            f"The top coins sit at the edge of noise; the bottom coins are real. USDCUSDT is a stablecoin perp that should not be in the universe at all. Across coins, mean R moves with the continuation share (r = {c['mean_r_vs_continuation_share']:+.2f}) and against pattern diversity (r = {c['mean_r_vs_eff_patterns']:+.2f}): the best coins were the ones that trended."
        )
    )


def section_equity(d: dict) -> str:
    cols = [
        "n",
        "coins",
        "win_pct",
        "tgt_first_pct",
        "stop_first_pct",
        "mean_r",
        "median_r",
        "mean_ret_pct",
        "mean_r_no_stop",
        "mfe_med",
        "mae_med",
    ]
    nm = {
        "tgt_first_pct": "target first %",
        "stop_first_pct": "stop first %",
        "mean_ret_pct": "mean ret % of price",
        "mean_r_no_stop": "mean R no stop",
        "mfe_med": "median MFE (R)",
        "mae_med": "median MAE (R)",
    }
    return (
        "<h2>10. Equity perps two ways: the 24/7 day vs the New York session as the bar</h2>"
        + plain(
            f"<b>What this is.</b> The equity perpetuals on Hyperliquid (HIP-3, the xyz dex). The venue serves about 208 days of hourly bars, so this is {d['window'][0]} to {d['window'][1]} only. Two builds of the same table: the 24/7 UTC day, and the New York regular session (weekday 9:00 to 15:59) as the STRAT daily bar with triggers only inside the session. Same stop, same ladder, same 10-day walk over every hour. Crypto alts in the same months are the control."
        )
        + "<h3>10a. US-listed perps, both ways, against crypto</h3>"
        + tbl(d["two_ways"], ["build"] + cols, nm)
        + plain(
            "On the UTC day the equity perps are the worst cell on this page; most of the damage sits in the 20:00 New York hour, the UTC day roll, while the underlying is closed. On the session day the sign flips in every family: the first positive cell the vessel has produced. Seven months, 76 names that move together, two different trade populations: a lead, not a finding."
        )
        + "<h3>10b. By family</h3>"
        + tbl(d["family"], ["family", "build"] + cols, nm)
        + "<h3>10c. By direction</h3>"
        + tbl(d["direction"], ["direction", "build"] + cols, nm)
        + "<h3>10d. 24/7 build: which session the break happened in</h3>"
        + tbl(d["session"], ["session_class", "trigger_session"] + cols, nm)
    )


def assemble(date: str) -> str:
    src = (REPORTS / f"strat_ml_report_{date}.html").read_text()
    body = re.search(r"<body>(.*)</body>", src, re.S).group(1)
    style = re.search(r"<style>(.*?)</style>", src, re.S).group(1)
    style = style.replace(
        "body{margin:0;padding:16px;",
        "body{margin:0;padding-block:16px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));",
    )
    extra = ""
    for fn, name in (
        (section_stops, "stop_compare"),
        (section_excursion, "excursion"),
        (section_ladder, "pivot_ladder"),
        (section_census, "ticker_census"),
        (section_equity, "equity_perps"),
    ):
        path = REPORTS / f"{name}_{date}.json"
        if path.exists():
            extra += fn(json.loads(path.read_text()))
    marker = "<h2>5. Caveats that travel with every number above</h2>"
    body = body.replace(marker, extra + marker, 1)
    return (
        '<title>STRAT Trigger Research</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n<style>'
        + style
        + "</style>\n"
        + body
    )


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    page = assemble(a.date)
    Path(a.out).write_text(page, encoding="utf-8")
    print(f"{len(page) / 1e6:.2f} MB -> {a.out}")


if __name__ == "__main__":
    main(sys.argv[1:])
