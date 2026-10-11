"""Build the private chart page for the TVB-37 chance comparison and book view (prereg A3).

Reads results/chance.json (chances with intervals) and results/book.json (the equal-size book,
curves, R-matched check) and writes results/chance_book_page.html, a self-contained page that
shows ONLY numbers present in those files. The page is a view for the owner; the receipts are the
record. The published link is never written into this repository (it is public).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from analysis.domino.chance import MIN_CELL

HERE = Path(__file__).parent
RESULTS = HERE / "results"
KINDS = ("reversal", "continuation", "inside", "outside")
KIND_LABEL = {
    "reversal": "2-2 reversal",
    "continuation": "2-2 continuation",
    "inside": "inside break (1-2)",
    "outside": "outside break (3-2)",
}
CLS_LABEL = {
    "plain": "plain (no level within 1%)",
    "exact_shared": "same price, Monday / 1st open",
    "exact_plain": "same price, plain day",
    "near": "level within 0.25% beyond",
    "within1": "level within 1% beyond",
    "spread": "level more than 1% beyond",
    "rest": "the rest (within 1% + spread)",
    "stacked": "stacked (exact or near)",
}


BASE_LABEL = {"plain": "plain", "within1 + spread": "the rest (within 1% + spread)"}


BOOK_KEYS = ("A", "B", "C", "D", "D5", "ref")


def management_data(m: dict) -> dict:
    """The product-3 numbers the page draws, read from manage.json and nothing else: reach bars
    (T1 before the exit vs any time inside the cap), the five books per daily cell, the curves
    for the declared cells and the hypothesis read-out."""
    cells = {(c["tf"], c["kind"], c["flag"], c["cls"]): c for c in m["cells"]}

    def reach(c: dict, key: str) -> dict | None:
        r = c.get(key)
        if not r or not r.get("n"):
            return None
        return {"p": r["p"], "lo": r["lo"], "hi": r["hi"], "n": r["n"], "small": r["n"] < MIN_CELL}

    reach_rows = {}
    for kind in KINDS:
        c = cells.get(("D", kind, "all", "plain"))
        if not c or not c.get("n"):
            continue
        reach_rows[kind] = {
            "exit": reach(c, "reach1"),
            "cap": reach(c, "ceil1"),
            "t2": reach(c, "reach2"),
        }
    book_rows = []
    hyp = []
    for kind in KINDS:
        for cls in ("plain", "near", "within1"):
            c = cells.get(("D", kind, "all", cls))
            if not c or not c.get("book_rows"):
                continue
            for b in BOOK_KEYS:
                st = c["books"][b]
                if not st.get("n"):
                    continue
                d = c["diff"].get(f"{b}_minus_ref") if b != "ref" else None
                book_rows.append(
                    {
                        "setup": KIND_LABEL[kind],
                        "cls": CLS_LABEL[cls],
                        "book": m["book_label"][b],
                        "n": st["n"],
                        "small": st["n"] < MIN_CELL,
                        "avg": st["avg_pct"],
                        "med": st["med_pct"],
                        "win": st["win"],
                        "at_target": st["at_target"],
                        "total": st["total_usd"],
                        "dd": st["max_dd_usd"],
                        "days": st["med_days"],
                        "diff": None if d is None else d["diff"],
                        "lo": None if d is None else d["lo"],
                        "hi": None if d is None else d["hi"],
                    }
                )
            if cls == "plain":
                d = c["diff"]["D_minus_ref"]
                d5 = c["diff"]["D5_minus_ref"]
                died = c["died"]
                # every share carries its own denominator; the row fades when the paired n is
                # small and each share cell fades on its own n (audit F8)
                hyp.append(
                    {
                        "setup": KIND_LABEL[kind],
                        "n": d5["n"],
                        "small": d5["n"] < MIN_CELL,
                        "diff5": d5["diff"],
                        "lo5": d5["lo"],
                        "hi5": d5["hi"],
                        "diff": d["diff"],
                        "lo": d["lo"],
                        "hi": d["hi"],
                        "later_r5": c["died_r"]["later_r5"],
                        "later1": died["later1"],
                        "stop_saw": died["stop_saw"],
                        "tail1": c["tail"]["mae_gt1"],
                        "tail2": c["tail"]["mae_gt2"],
                        "worst": c["tail"]["worst_pct"],
                    }
                )
    return {
        "cap": m["cap_daily_bars"],
        "units": m["units"],
        "book_label": m["book_label"],
        "reach": reach_rows,
        "books": book_rows,
        "hyp": hyp,
        "curves": m["curves"],
    }


def build_data(results: Path = RESULTS) -> dict:
    """The page's numbers, read from chance.json and book.json and nothing else.

    Close-out audit folds: a bar's n is the VALID count at the displayed horizon and cells under
    MIN_CELL valid are flagged `small` (F3); R-matched rows name their base and carry coverage,
    the effective count and the conditional / unavailable state (F2, F4).
    """
    chance = json.load(open(results / "chance.json"))
    book = json.load(open(results / "book.json"))
    cells = {(c["tf"], c["kind"], c["flag"], c["cls"]): c for c in chance["cells"]["venue_era"]}

    def bar(tf: str, kind: str, flag: str, cls: str, n: int = 3) -> dict | None:
        c = cells.get((tf, kind, flag, cls))
        if not c or not c.get(f"n{n}"):
            return None
        return {
            "p": c[f"one_r{n}"],
            "lo": c[f"lo{n}"],
            "hi": c[f"hi{n}"],
            "n": c[f"n{n}"],  # the valid count at THIS horizon, not every unit (audit F3)
            "small": c[f"n{n}"] < MIN_CELL,
            "stop": c[f"stop{n}"],
        }

    bcells = {(c["tf"], c["kind"], c["flag"], c["cls"]): c for c in book["cells"]}
    book_rows = []
    for kind in KINDS:
        for cls in ("plain", "exact_shared", "near", "within1"):
            c = bcells.get(("D", kind, "all", cls))
            if not c or not c["h5"].get("n"):
                continue
            h = c["h5"]
            book_rows.append(
                {
                    "setup": KIND_LABEL[kind],
                    "cls": CLS_LABEL[cls],
                    "n": h["n"],
                    "small": h["n"] < MIN_CELL,
                    "avg": h["avg_pct"],
                    "hit": h["hit"],
                    "stop": h["stop"],
                    "exp_r": h["exp_r"],
                    "total": h["total_usd"],
                    "dd": h["max_dd_usd"],
                    "r": h["avg_r_pct"],
                }
            )
    matched = []
    for r in book["r_matched"]:  # the top level of each row is the 3-bar result, as drawn
        if r["flag"] != "all" or r["n_stacked"] < MIN_CELL or r["raw"] is None:
            continue
        base = BASE_LABEL[r["base"]]
        label = f"{r['tf']} {KIND_LABEL[r['kind']]}: {CLS_LABEL[r['cls']]} vs {base}"
        if not r["available"]:
            label += " (no shared bar-size bin: unavailable)"
        elif r["conditional"]:
            label += f" (conditional on {100 * r['covered']:.0f}% of stacked)"
        matched.append(
            {
                "label": label,
                "base": base,
                "raw": r["raw"],
                "matched": r["matched"],
                "lo": r["lo"],
                "hi": r["hi"],
                "n": r["n_stacked"],
                "n_effective": r["n_effective"],
                "covered": r["covered"],
                "available": r["available"],
                "conditional": r["conditional"],
            }
        )
    manage = None
    if (results / "manage.json").exists():
        manage = management_data(json.load(open(results / "manage.json")))
    return {
        "as_of": chance["as_of_utc"],
        "manage": manage,
        "units": chance["units"]["venue_era"],
        "unit_usd": book["unit_usd"],
        "kind_label": KIND_LABEL,
        "cls_label": CLS_LABEL,
        "daily": {
            k: {c: bar("D", k, "all", c) for c in ("plain", "exact_shared", "near", "within1")}
            for k in KINDS
        },
        "weekly": {
            k: {c: bar("W", k, "all", c) for c in ("exact_shared", "near", "within1", "spread")}
            for k in KINDS
        },
        "hammer": {
            k: {f: bar("D", k, f, "plain") for f in ("all", "third", "strict")}
            for k in ("reversal", "continuation", "inside")
        },
        "curves": book["curves"],
        "book": book_rows,
        "matched": matched,
    }


TEMPLATE = r"""<title>Domino Chance Book</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* layout: one reading column of charts, each chart with its own one-line reading; numbers in mono */
:root {
  --bg: #f6f5f1; --panel: #fffefb; --fg: #1d2430; --muted: #5d667a; --rule: #d9d6cc;
  --plain: #3b6e8f; --stack: #c7791a; --near: #2f8f6b; --within: #8c6bb1; --spread: #9a9a9a;
  --loss: #b3452f; --grid: #e6e3da;
  --font-body: "IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
  --font-mono: "IBM Plex Mono", "SFMono-Regular", Consolas, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #12161d; --panel: #1a2029; --fg: #e8e6df; --muted: #9aa3b5; --rule: #2b3340;
  --plain: #6fa7cb; --stack: #e9a04a; --near: #5fc39a; --within: #b497d6; --spread: #7a7f8a;
  --loss: #e0745c; --grid: #262d38; color-scheme: dark; } }
:root[data-theme="dark"] {
  --bg: #12161d; --panel: #1a2029; --fg: #e8e6df; --muted: #9aa3b5; --rule: #2b3340;
  --plain: #6fa7cb; --stack: #e9a04a; --near: #5fc39a; --within: #b497d6; --spread: #7a7f8a;
  --loss: #e0745c; --grid: #262d38; color-scheme: dark; }
body { background: var(--bg); color: var(--fg); font-family: var(--font-body); font-size: 15px; line-height: 1.5; margin: 0; }
.wrap { max-width: 980px; margin: 0 auto; padding-block: 28px 56px; padding-inline: 16px; }
header h1 { font-size: 1.7rem; font-weight: 600; margin: 0 0 6px; text-wrap: balance; letter-spacing: -0.01em; }
header p { margin: 0; color: var(--muted); max-width: 70ch; }
.eyebrow { font-family: var(--font-mono); font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); }
section { margin-top: 36px; }
section h2 { font-size: 1.15rem; font-weight: 600; margin: 0 0 4px; text-wrap: balance; }
section .read { color: var(--muted); margin: 0 0 12px; max-width: 75ch; }
.panel { background: var(--panel); border: 1px solid var(--rule); border-radius: 6px; padding: 14px 14px 8px; }
.chart { position: relative; height: 340px; }
.chart.tall { height: 380px; }
.legend { display: flex; flex-wrap: wrap; gap: 6px 16px; margin: 8px 0 0; padding: 0; list-style: none; font-size: 0.85rem; color: var(--muted); }
.legend li::before { content: ""; display: inline-block; width: 12px; height: 12px; border-radius: 2px; margin-right: 6px; vertical-align: -2px; background: var(--c); }
.tbl { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 0.88rem; font-variant-numeric: tabular-nums; }
th, td { text-align: right; padding: 7px 10px; border-bottom: 1px solid var(--rule); white-space: nowrap; }
th:first-child, td:first-child, th:nth-child(2), td:nth-child(2) { text-align: left; white-space: normal; }
th { font-family: var(--font-mono); font-size: 0.72rem; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted); font-weight: 500; }
td.num { font-family: var(--font-mono); }
td.neg { color: var(--loss); }
tr.small td { opacity: 0.45; }
.notes { color: var(--muted); font-size: 0.9rem; max-width: 75ch; }
.notes li { margin-bottom: 6px; }
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
</style>

<div class="wrap">
<header>
  <div class="eyebrow">TVB-37 &middot; venue era &middot; as of __ASOF__ UTC</div>
  <h1>Domino Chance Book</h1>
  <p>Every daily, weekly and monthly level break on 292 live perps, traded at one unit each with the stop at the other side of the setup bar and a one-R target. No leverage, no fees, no funding. The same STRAT pattern is shown plain and stacked on a higher-timeframe level. Numbers are the receipt's; this page only draws them. The management book (no stop, a close exit, a ladder of targets) sits at the bottom.</p>
</header>

<section>
  <h2>Daily triggers: chance of one R before the stop, by 3 bars</h2>
  <p class="read">Each bar is one setup in one stack class. The thin line is the 95% interval; n in the tooltip is the valid count by 3 bars. Faded bars hold fewer than 30 valid trades: counted, not read. Plain means no unbroken weekly or monthly level within 1% beyond yesterday's level at the moment it broke.</p>
  <div class="panel"><div class="chart"><canvas id="barsDaily"></canvas></div>
  <ul class="legend"><li style="--c:var(--plain)">plain</li><li style="--c:var(--stack)">same price at the Monday / 1st open</li><li style="--c:var(--near)">level within 0.25% beyond</li><li style="--c:var(--within)">level within 1% beyond</li></ul></div>
</section>

<section>
  <h2>The book: daily 2-2 continuation, plain against stacked</h2>
  <p class="read">Cumulative P/L on a book that takes every trade at 1,000 dollars, closes at one R or the stop, and marks the rest at the close of the fifth bar. Each trade's final return is placed on its ENTRY date, although it was only known up to five bars later, and many trades overlap: the line is the sum of equal-size trades by entry date, not an equity path or an account balance. The drawn line is sampled; the drawdown in the table uses every date.</p>
  <div class="panel"><div class="chart tall"><canvas id="curvesDaily"></canvas></div>
  <ul class="legend" id="legendDaily"></ul></div>
</section>

<section>
  <h2>The hammer shape on plain daily setups</h2>
  <p class="read">Same pattern, split by whether the setup bar closed in its far third (THIRD) or did so with only a sliver of wick (STRICT). Left: one-R chance by 3 bars. Right: the book for the 2-2 reversal and the inside break, all setups against the hammer-flagged ones.</p>
  <div class="panel"><div class="chart"><canvas id="barsHammer"></canvas></div>
  <ul class="legend"><li style="--c:var(--spread)">all setup bars</li><li style="--c:var(--plain)">THIRD</li><li style="--c:var(--near)">STRICT</li></ul></div>
  <div class="panel" style="margin-top:12px"><div class="chart tall"><canvas id="curvesHammer"></canvas></div>
  <ul class="legend" id="legendHammer"></ul></div>
</section>

<section>
  <h2>Weekly triggers: chance of one R by 3 weeks</h2>
  <p class="read">Entry at last week's level. Same price at the Monday open means Sunday's high (or low) was the old week's high (or low) and Monday opened the new week: the old week made its extreme on its last day, which is not the same as closing there. Faded bars hold fewer than 30 valid trades by 3 weeks.</p>
  <div class="panel"><div class="chart"><canvas id="barsWeekly"></canvas></div>
  <ul class="legend"><li style="--c:var(--stack)">same price at the Monday / 1st open</li><li style="--c:var(--near)">within 0.25%</li><li style="--c:var(--within)">within 1%</li><li style="--c:var(--spread)">more than 1% (the day already ran)</li></ul></div>
  <div class="panel" style="margin-top:12px"><div class="chart tall"><canvas id="curvesWeekly"></canvas></div>
  <ul class="legend" id="legendWeekly"></ul></div>
</section>

<section>
  <h2>Is it the stack or the bar size? The R-matched check</h2>
  <p class="read">Stacked minus base one-R chance by 3 bars, in percentage points. The base is plain for daily setups and the rest (level within 1% or more than 1% beyond) for weekly and monthly setups; each row names its base. The pale bar is the raw gap; the solid bar reweights the base to the stacked group's setup-bar sizes, with its 95% interval. Where the solid bar is nearer zero, the gap shrinks after reweighting to the stacked group's bar sizes: that is attenuation, not proof that bar size caused the gap. A row marked conditional matches only part of the stacked group.</p>
  <div class="panel"><div class="chart tall"><canvas id="barsMatched"></canvas></div>
  <ul class="legend"><li style="--c:var(--spread)">raw difference</li><li style="--c:var(--stack)">R-matched difference</li></ul></div>
</section>

<section>
  <h2>The book by cell, daily triggers, 5 bars</h2>
  <div class="panel tbl"><table id="bookTable"><thead><tr><th>setup</th><th>class</th><th>trades</th><th>avg % / trade</th><th>hit</th><th>stopped</th><th>exp. R</th><th>total $</th><th>max DD $</th><th>median R %</th></tr></thead><tbody></tbody></table></div>
</section>

<section id="manage" hidden>
  <h2>The management book: no stop, a close exit, a ladder of targets</h2>
  <p class="read">Same trades, managed the STRAT way instead of with a setup-bar stop: no price stop; out at the close of a day that closed red with the week red at that close (under Monday's open), filled at that close; T1 = the pattern's own magnitude (the far side of the bar before the pattern for a reversal; the first unbroken weekly or monthly level for the 2-2 continuation, the with-trend inside bar and the 3-2), T2 and T3 the next unbroken higher levels; trades still open after 20 days marked there. Plain daily setups. The left bar of each group is the share that touched T1 before the exit; the middle bar ignores the exit (touched any time inside 20 days): the gap between them is what the exit costs in targets.</p>
  <div class="panel"><div class="chart"><canvas id="barsReach"></canvas></div>
  <ul class="legend"><li style="--c:var(--plain)">T1 before the exit</li><li style="--c:var(--spread)">T1 any time in 20 days</li><li style="--c:var(--near)">T2 after T1, before the exit</li></ul></div>
</section>

<section id="manageCurves" hidden>
  <h2>Five books on the same trades: plain daily setups</h2>
  <p class="read">A takes everything off at T1. B passes through T1 and takes T2 (or the exit). C has no target, the exit only. D keeps the chance book's one-R target and swaps the stop for the close exit, with the 20-day cap; D5 does the same swap at the chance book's own five-bar horizon, so between D5 and the reference only the stop changes. The reference is the chance book itself (one R or the setup-bar stop, marked at the fifth bar) on the identical trades. Each trade's final return sits on its ENTRY date; the lines are sums of equal-size trades, not an account.</p>
  <div class="panel"><div class="chart tall"><canvas id="curvesManageRev"></canvas></div>
  <ul class="legend" id="legendManageRev"></ul></div>
  <div class="panel" style="margin-top:12px"><div class="chart tall"><canvas id="curvesManageCont"></canvas></div>
  <ul class="legend" id="legendManageCont"></ul></div>
  <div class="panel" style="margin-top:12px"><div class="chart tall"><canvas id="curvesManageIns"></canvas></div>
  <ul class="legend" id="legendManageIns"></ul></div>
</section>

<section id="manageHyp" hidden>
  <h2>The suspect, read as declared</h2>
  <p class="read">H2 (the owner's): swap the stop for the close exit and keep everything else. D5 keeps the chance book's one-R target AND its five-bar horizon, so only the stop changes (average % per trade minus the reference, paired on the same trades, 95% interval); D is the same swap with the 20-day cap. H3 (the lead's counter): the close exit is itself an early exit; of the trades D5 closed before one R, how many touched one R inside the same five bars, beside the chance book's stopped-then-saw-one-R share on the same trades. The tail columns are where a stopless book bleeds: trades whose adverse travel passed one and two setup-bar R before the exit, and the worst single trade. Cells in parentheses rest on fewer than 30 trades.</p>
  <div class="panel tbl"><table id="hypTable"><thead><tr><th>setup</th><th>trades</th><th>D5 minus reference (stop only)</th><th>D minus reference (20 days)</th><th>D5 exited, saw one R in 5 bars</th><th>stopped, saw one R in 5 bars</th><th>MAE over 1R</th><th>over 2R</th><th>worst trade</th></tr></thead><tbody></tbody></table></div>
</section>

<section id="manageTable" hidden>
  <h2>The management books by cell, daily triggers</h2>
  <div class="panel tbl"><table id="manageBookTable"><thead><tr><th>setup</th><th>class</th><th>book</th><th>trades</th><th>avg % / trade</th><th>median %</th><th>in profit</th><th>at target</th><th>total $</th><th>max DD $</th><th>days</th><th>minus reference</th></tr></thead><tbody></tbody></table></div>
</section>

<section>
  <h2>Read with these in mind</h2>
  <ul class="notes">
    <li>A day whose range traded both the stop and the target counts as a stop; so does a stop level traded on the entry day even if it came before the break. Between 13.9% (outside break) and 32.2% (inside break) of plain daily triggers did that.</li>
    <li>The curves place each trade's final return on its entry date; they are not an equity path.</li>
    <li>Faded bars and table rows hold fewer than 30 valid trades at the horizon shown: counted, not read.</li>
    <li>Units on the same day across coins move together; the intervals are tighter than the truth.</li>
    <li>Survivors only (coins listed today), venue era only (each coin from its first traded day). No fees, funding, slippage or sizing. Nothing here is a rule.</li>
    <li>The management book has no price stop: its losses are bounded only by the close exit and the 20-day cap; nothing here sizes against liquidation. Days held differ by book (shown), so a book against the reference is rule against rule; only D isolates the stop.</li>
    <li>Record: analysis/domino/CHANCE_RECEIPT.md, BOOK_RECEIPT.md and MANAGE_RECEIPT.md in the research repo.</li>
  </ul>
</section>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<script>
const DATA = __DATA__;
const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const pct = (x) => (x == null ? "-" : (100 * x).toFixed(1) + "%");
const usd = (x) => (x == null ? "-" : (x >= 0 ? "+" : "-") + Math.abs(x).toLocaleString("en-US", { maximumFractionDigits: 0 }));

// thin 95% interval lines on top of bars
const intervalPlugin = {
  id: "intervals",
  afterDatasetsDraw(chart) {
    const { ctx } = chart;
    chart.data.datasets.forEach((ds, di) => {
      if (!ds.intervals) return;
      const meta = chart.getDatasetMeta(di);
      meta.data.forEach((bar, i) => {
        const iv = ds.intervals[i];
        if (!iv) return;
        const y1 = chart.scales.y.getPixelForValue(iv[0]);
        const y2 = chart.scales.y.getPixelForValue(iv[1]);
        ctx.save();
        ctx.strokeStyle = css("--fg");
        ctx.globalAlpha = 0.7;
        ctx.lineWidth = 1.2;
        ctx.beginPath(); ctx.moveTo(bar.x, y1); ctx.lineTo(bar.x, y2); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(bar.x - 4, y1); ctx.lineTo(bar.x + 4, y1); ctx.moveTo(bar.x - 4, y2); ctx.lineTo(bar.x + 4, y2); ctx.stroke();
        ctx.restore();
      });
    });
  },
};
Chart.register(intervalPlugin);

const charts = [];
function baseOptions(yTitle, yMin, yMax) {
  return {
    responsive: true, maintainAspectRatio: false, animation: false,
    plugins: { legend: { display: false }, tooltip: { callbacks: {} } },
    scales: {
      x: { grid: { display: false }, ticks: { color: css("--muted"), font: { family: css("--font-body"), size: 12 } } },
      y: { min: yMin, max: yMax, grid: { color: css("--grid") }, ticks: { color: css("--muted"), font: { family: css("--font-mono"), size: 11 } },
           title: { display: true, text: yTitle, color: css("--muted"), font: { family: css("--font-body"), size: 12 } } },
    },
  };
}

function groupedBars(id, groups, series, yTitle, yMax) {
  // groups: [{label, cells: {key: bar}}]; series: [{key, color}]
  // a cell under 30 valid trades is drawn faded (alpha 0x4d) and its tooltip is parenthesised, as the tables grey it
  const datasets = series.map((s) => ({
    label: s.label, borderRadius: 2, maxBarThickness: 44,
    backgroundColor: groups.map((g) => css(s.color) + (g.cells[s.key] && g.cells[s.key].small ? "4d" : "")),
    data: groups.map((g) => (g.cells[s.key] ? 100 * g.cells[s.key].p : null)),
    intervals: groups.map((g) => (g.cells[s.key] ? [100 * g.cells[s.key].lo, 100 * g.cells[s.key].hi] : null)),
    ns: groups.map((g) => (g.cells[s.key] ? g.cells[s.key].n : null)),
    small: groups.map((g) => (g.cells[s.key] ? g.cells[s.key].small : false)),
  }));
  const opts = baseOptions(yTitle, 0, yMax);
  opts.plugins.tooltip.callbacks.label = (c) => {
    const ds = c.dataset; const iv = ds.intervals[c.dataIndex];
    const txt = `${ds.label}: ${c.parsed.y.toFixed(1)}% [${iv[0].toFixed(0)}, ${iv[1].toFixed(0)}], valid n ${ds.ns[c.dataIndex].toLocaleString()}`;
    return ds.small[c.dataIndex] ? `(${txt}; under 30 valid, counted not read)` : txt;
  };
  charts.push(new Chart(document.getElementById(id), { type: "bar", data: { labels: groups.map((g) => g.label), datasets }, options: opts }));
}

function curves(id, legendId, lines, yTitle) {
  // lines: [{label, color, points: [[date, usd], ...]}]; x = days since the earliest date in any line
  const t0 = Math.min(...lines.flatMap((l) => l.points.map((p) => Date.parse(p[0]))));
  const toDay = (d) => Math.round((Date.parse(d) - t0) / 86400000);
  const datasets = lines.map((l) => ({
    label: l.label, borderColor: css(l.color), backgroundColor: css(l.color), borderWidth: 1.8, pointRadius: 0, tension: 0,
    data: l.points.map((p) => ({ x: toDay(p[0]), y: p[1] })),
  }));
  const opts = baseOptions(yTitle);
  opts.scales.x = { type: "linear", grid: { display: false }, ticks: { color: css("--muted"), maxTicksLimit: 8, font: { family: css("--font-mono"), size: 11 },
    callback: (v) => new Date(t0 + v * 86400000).toISOString().slice(0, 7) } };
  opts.scales.y.ticks.callback = (v) => (v / 1000).toFixed(0) + "k";
  opts.plugins.tooltip.callbacks.title = (items) => new Date(t0 + items[0].parsed.x * 86400000).toISOString().slice(0, 10);
  opts.plugins.tooltip.callbacks.label = (c) => `${c.dataset.label}: ${usd(c.parsed.y)} $`;
  opts.interaction = { mode: "nearest", intersect: false };
  charts.push(new Chart(document.getElementById(id), { type: "line", data: { datasets }, options: opts }));
  const ul = document.getElementById(legendId);
  ul.innerHTML = lines.map((l) => `<li style="--c:${css(l.color)}">${l.label} (${l.points.length ? usd(l.points[l.points.length - 1][1]) + " $" : "no data"})</li>`).join("");
}

function matchedBars(id) {
  const rows = DATA.matched;
  const opts = baseOptions("percentage points, stacked minus base", undefined, undefined);
  opts.indexAxis = "y";
  opts.scales = {
    y: { grid: { display: false }, ticks: { color: css("--muted"), font: { family: css("--font-body"), size: 11 }, autoSkip: false } },
    x: { grid: { color: css("--grid") }, ticks: { color: css("--muted"), font: { family: css("--font-mono"), size: 11 } },
         title: { display: true, text: "percentage points, stacked minus base, one R by 3 bars", color: css("--muted") } },
  };
  const hPlugin = {
    id: "hIntervals",
    afterDatasetsDraw(chart) {
      const ds = chart.data.datasets[1]; const meta = chart.getDatasetMeta(1); const { ctx } = chart;
      meta.data.forEach((bar, i) => {
        if (rows[i].lo == null || rows[i].hi == null) return;  // unavailable: no interval to draw
        const x1 = chart.scales.x.getPixelForValue(100 * rows[i].lo), x2 = chart.scales.x.getPixelForValue(100 * rows[i].hi);
        ctx.save(); ctx.strokeStyle = css("--fg"); ctx.globalAlpha = 0.7; ctx.lineWidth = 1.2;
        ctx.beginPath(); ctx.moveTo(x1, bar.y); ctx.lineTo(x2, bar.y); ctx.moveTo(x1, bar.y - 4); ctx.lineTo(x1, bar.y + 4); ctx.moveTo(x2, bar.y - 4); ctx.lineTo(x2, bar.y + 4); ctx.stroke(); ctx.restore();
      });
    },
  };
  opts.plugins.tooltip.callbacks.label = (c) => {
    const r = rows[c.dataIndex];
    const cover = r.covered == null ? "" : `, covered ${(100 * r.covered).toFixed(0)}% (${r.n_effective.toLocaleString()} matched)`;
    return `${c.dataset.label}: ${c.parsed.x >= 0 ? "+" : ""}${c.parsed.x.toFixed(1)} pts vs ${r.base}, valid n stacked ${r.n.toLocaleString()}${cover}`;
  };
  charts.push(new Chart(document.getElementById(id), {
    type: "bar",
    data: { labels: rows.map((r) => r.label), datasets: [
      { label: "raw", data: rows.map((r) => 100 * r.raw), backgroundColor: css("--spread"), maxBarThickness: 14 },
      { label: "R-matched", data: rows.map((r) => (r.matched == null ? null : 100 * r.matched)), backgroundColor: css("--stack"), maxBarThickness: 14 },
    ] },
    options: opts, plugins: [hPlugin],
  }));
}

function table() {
  const tb = document.querySelector("#bookTable tbody");
  tb.innerHTML = DATA.book.map((r) => `<tr class="${r.small ? "small" : ""}"><td>${r.setup}</td><td>${r.cls}</td><td class="num">${r.n.toLocaleString()}</td>
    <td class="num ${r.avg < 0 ? "neg" : ""}">${r.avg >= 0 ? "+" : ""}${r.avg.toFixed(2)}%</td><td class="num">${pct(r.hit)}</td><td class="num">${pct(r.stop)}</td>
    <td class="num ${r.exp_r < 0 ? "neg" : ""}">${r.exp_r >= 0 ? "+" : ""}${r.exp_r.toFixed(3)}</td><td class="num ${r.total < 0 ? "neg" : ""}">${usd(r.total)}</td>
    <td class="num neg">${usd(r.dd)}</td><td class="num">${r.r.toFixed(2)}</td></tr>`).join("");
}

const sgn = (x, d) => (x == null ? "-" : (x >= 0 ? "+" : "") + x.toFixed(d));

function manageCurves(id, legendId, key) {
  const C = DATA.manage.curves[key] || {};
  const L = DATA.manage.book_label;
  const col = { A: "--near", B: "--within", C: "--plain", D: "--stack", D5: "--loss", ref: "--spread" };
  curves(id, legendId, ["A", "B", "C", "D", "D5", "ref"].filter((b) => C[b]).map((b) => ({ label: L[b], color: col[b], points: C[b] })), "cumulative P/L, 1,000 $ per trade");
}

function manage() {
  const M = DATA.manage;
  if (!M) return;
  ["manage", "manageCurves", "manageHyp", "manageTable"].forEach((id) => { document.getElementById(id).hidden = false; });
  const K = DATA.kind_label;
  groupedBars("barsReach", Object.keys(M.reach).map((k) => ({ label: K[k], cells: M.reach[k] })),
    [{ key: "exit", color: "--plain", label: "T1 before the exit" }, { key: "cap", color: "--spread", label: "T1 any time in 20 days" },
     { key: "t2", color: "--near", label: "T2 after T1" }], "share of trades (%)", 100);
  manageCurves("curvesManageRev", "legendManageRev", "D|reversal|all|plain");
  manageCurves("curvesManageCont", "legendManageCont", "D|continuation|all|plain");
  manageCurves("curvesManageIns", "legendManageIns", "D|inside|all|plain");
  const ht = document.querySelector("#hypTable tbody");
  const sh = (x) => (x && x.n ? (x.n < 30 ? `(${pct(x.p)}, n ${x.n.toLocaleString()})` : `${pct(x.p)} (n ${x.n.toLocaleString()})`) : "-");
  ht.innerHTML = M.hyp.map((r) => `<tr class="${r.small ? "small" : ""}"><td>${r.setup}</td><td class="num">${r.n.toLocaleString()}</td>
    <td class="num ${r.diff5 < 0 ? "neg" : ""}">${sgn(r.diff5, 2)}% [${sgn(r.lo5, 2)}, ${sgn(r.hi5, 2)}]</td>
    <td class="num ${r.diff < 0 ? "neg" : ""}">${sgn(r.diff, 2)}% [${sgn(r.lo, 2)}, ${sgn(r.hi, 2)}]</td>
    <td class="num">${sh(r.later_r5)}</td><td class="num">${sh(r.stop_saw)}</td>
    <td class="num">${pct(r.tail1)}</td><td class="num">${pct(r.tail2)}</td><td class="num neg">${sgn(r.worst, 1)}%</td></tr>`).join("");
  const tb = document.querySelector("#manageBookTable tbody");
  tb.innerHTML = M.books.map((r) => `<tr class="${r.small ? "small" : ""}"><td>${r.setup}</td><td>${r.cls}</td><td>${r.book}</td><td class="num">${r.n.toLocaleString()}</td>
    <td class="num ${r.avg < 0 ? "neg" : ""}">${sgn(r.avg, 2)}%</td><td class="num ${r.med < 0 ? "neg" : ""}">${sgn(r.med, 2)}%</td><td class="num">${pct(r.win)}</td><td class="num">${pct(r.at_target)}</td>
    <td class="num ${r.total < 0 ? "neg" : ""}">${usd(r.total)}</td><td class="num neg">${usd(r.dd)}</td><td class="num">${r.days.toFixed(0)}</td>
    <td class="num">${r.diff == null ? "-" : sgn(r.diff, 2) + " [" + sgn(r.lo, 2) + ", " + sgn(r.hi, 2) + "]"}</td></tr>`).join("");
}

function draw() {
  charts.splice(0).forEach((c) => c.destroy());
  const K = DATA.kind_label;
  groupedBars("barsDaily", ["reversal", "continuation", "inside", "outside"].map((k) => ({ label: K[k], cells: DATA.daily[k] })),
    [{ key: "plain", color: "--plain", label: "plain" }, { key: "exact_shared", color: "--stack", label: "same price at the open" },
     { key: "near", color: "--near", label: "within 0.25%" }, { key: "within1", color: "--within", label: "within 1%" }], "one R before the stop, by 3 bars (%)", 60);
  groupedBars("barsWeekly", ["reversal", "continuation", "inside", "outside"].map((k) => ({ label: K[k], cells: DATA.weekly[k] })),
    [{ key: "exact_shared", color: "--stack", label: "same price at the open" }, { key: "near", color: "--near", label: "within 0.25%" },
     { key: "within1", color: "--within", label: "within 1%" }, { key: "spread", color: "--spread", label: "more than 1%" }], "one R before the stop, by 3 weeks (%)", 60);
  groupedBars("barsHammer", ["reversal", "continuation", "inside"].map((k) => ({ label: K[k], cells: DATA.hammer[k] })),
    [{ key: "all", color: "--spread", label: "all setup bars" }, { key: "third", color: "--plain", label: "THIRD" }, { key: "strict", color: "--near", label: "STRICT" }], "one R before the stop, by 3 bars (%)", 60);
  const C = DATA.curves;
  curves("curvesDaily", "legendDaily", [
    { label: "plain", color: "--plain", points: C["D|continuation|all|plain"] || [] },
    { label: "same price at the open", color: "--stack", points: C["D|continuation|all|exact_shared"] || [] },
    { label: "within 0.25% beyond", color: "--near", points: C["D|continuation|all|near"] || [] },
    { label: "within 1% beyond", color: "--within", points: C["D|continuation|all|within1"] || [] },
  ], "cumulative P/L, 1,000 $ per trade");
  curves("curvesHammer", "legendHammer", [
    { label: "2-2 reversal, all", color: "--spread", points: C["D|reversal|all|plain"] || [] },
    { label: "2-2 reversal, THIRD", color: "--plain", points: C["D|reversal|third|plain"] || [] },
    { label: "inside break, all", color: "--within", points: C["D|inside|all|plain"] || [] },
    { label: "inside break, THIRD", color: "--near", points: C["D|inside|third|plain"] || [] },
  ], "cumulative P/L, 1,000 $ per trade");
  curves("curvesWeekly", "legendWeekly", [
    { label: "2-2 continuation, same price at the open", color: "--stack", points: C["W|continuation|all|exact_shared"] || [] },
    { label: "2-2 continuation, the rest", color: "--plain", points: C["W|continuation|all|rest"] || [] },
    { label: "2-2 reversal, same price at the open", color: "--loss", points: C["W|reversal|all|exact_shared"] || [] },
    { label: "2-2 reversal, the rest", color: "--near", points: C["W|reversal|all|rest"] || [] },
  ], "cumulative P/L, 1,000 $ per trade");
  matchedBars("barsMatched");
  table();
  manage();
}
draw();
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", draw);
</script>
"""


def main() -> None:
    data = build_data()
    html = TEMPLATE.replace("__ASOF__", data["as_of"]).replace(
        "__DATA__", json.dumps(data, allow_nan=False)
    )
    out = RESULTS / "chance_book_page.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({len(html):,} bytes)")


if __name__ == "__main__":
    sys.exit(main())
