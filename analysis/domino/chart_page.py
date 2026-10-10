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


def build_data() -> dict:
    chance = json.load(open(RESULTS / "chance.json"))
    book = json.load(open(RESULTS / "book.json"))
    cells = {(c["tf"], c["kind"], c["flag"], c["cls"]): c for c in chance["cells"]["venue_era"]}

    def bar(tf: str, kind: str, flag: str, cls: str, n: int = 3) -> dict | None:
        c = cells.get((tf, kind, flag, cls))
        if not c or not c.get(f"n{n}"):
            return None
        return {
            "p": c[f"one_r{n}"],
            "lo": c[f"lo{n}"],
            "hi": c[f"hi{n}"],
            "n": c["n"],
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
    for r in book["r_matched"]:
        if r["flag"] != "all" or r["n_stacked"] < 30 or r["raw"] is None:
            continue
        matched.append(
            {
                "label": f"{r['tf']} {KIND_LABEL[r['kind']]}: {CLS_LABEL[r['cls']]}",
                "raw": r["raw"],
                "matched": r["matched"],
                "lo": r["lo"],
                "hi": r["hi"],
                "n": r["n_stacked"],
            }
        )
    return {
        "as_of": chance["as_of_utc"],
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
.notes { color: var(--muted); font-size: 0.9rem; max-width: 75ch; }
.notes li { margin-bottom: 6px; }
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
</style>

<div class="wrap">
<header>
  <div class="eyebrow">TVB-37 &middot; venue era &middot; as of __ASOF__ UTC</div>
  <h1>Domino Chance Book</h1>
  <p>Every daily, weekly and monthly level break on 292 live perps, traded at one unit each with the stop at the other side of the setup bar and a one-R target. No leverage, no fees, no funding. The same STRAT pattern is shown plain and stacked on a higher-timeframe level. Numbers are the receipt's; this page only draws them.</p>
</header>

<section>
  <h2>Daily triggers: chance of one R before the stop, by 3 bars</h2>
  <p class="read">Each bar is one setup in one stack class. The thin line is the 95% interval. Plain means no unbroken weekly or monthly level within 1% beyond yesterday's level at the moment it broke.</p>
  <div class="panel"><div class="chart"><canvas id="barsDaily"></canvas></div>
  <ul class="legend"><li style="--c:var(--plain)">plain</li><li style="--c:var(--stack)">same price at the Monday / 1st open</li><li style="--c:var(--near)">level within 0.25% beyond</li><li style="--c:var(--within)">level within 1% beyond</li></ul></div>
</section>

<section>
  <h2>The book: daily 2-2 continuation, plain against stacked</h2>
  <p class="read">Cumulative P/L on a book that takes every trade at 1,000 dollars, closes at one R or the stop, and marks the rest at the close of the fifth bar. Many trades are open at once, so this is the sum of equal-size trades, not an account balance.</p>
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
  <p class="read">Entry at last week's level. Same price at the Monday open means Sunday closed the old week on its extreme and the new week broke it off the open.</p>
  <div class="panel"><div class="chart"><canvas id="barsWeekly"></canvas></div>
  <ul class="legend"><li style="--c:var(--stack)">same price at the Monday / 1st open</li><li style="--c:var(--near)">within 0.25%</li><li style="--c:var(--within)">within 1%</li><li style="--c:var(--spread)">more than 1% (the day already ran)</li></ul></div>
  <div class="panel" style="margin-top:12px"><div class="chart tall"><canvas id="curvesWeekly"></canvas></div>
  <ul class="legend" id="legendWeekly"></ul></div>
</section>

<section>
  <h2>Is it the stack or the bar size? The R-matched check</h2>
  <p class="read">Stacked minus plain one-R chance by 3 bars, in percentage points. The pale bar is the raw gap; the solid bar reweights the plain group to the stacked group's setup-bar sizes, with its 95% interval. If the solid bar shrinks toward zero, the raw gap was bar size.</p>
  <div class="panel"><div class="chart tall"><canvas id="barsMatched"></canvas></div>
  <ul class="legend"><li style="--c:var(--spread)">raw difference</li><li style="--c:var(--stack)">R-matched difference</li></ul></div>
</section>

<section>
  <h2>The book by cell, daily triggers, 5 bars</h2>
  <div class="panel tbl"><table id="bookTable"><thead><tr><th>setup</th><th>class</th><th>trades</th><th>avg % / trade</th><th>hit</th><th>stopped</th><th>exp. R</th><th>total $</th><th>max DD $</th><th>median R %</th></tr></thead><tbody></tbody></table></div>
</section>

<section>
  <h2>Read with these in mind</h2>
  <ul class="notes">
    <li>A day whose range traded both the stop and the target counts as a stop; so does a stop level traded on the entry day even if it came before the break. One in four to one in three plain daily triggers did that.</li>
    <li>Units on the same day across coins move together; the intervals are tighter than the truth.</li>
    <li>Survivors only (coins listed today), venue era only (each coin from its first traded day). No fees, funding, slippage or sizing. Nothing here is a rule.</li>
    <li>Record: analysis/domino/CHANCE_RECEIPT.md and BOOK_RECEIPT.md in the research repo.</li>
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
  const datasets = series.map((s) => ({
    label: s.label, backgroundColor: css(s.color), borderRadius: 2, maxBarThickness: 44,
    data: groups.map((g) => (g.cells[s.key] ? 100 * g.cells[s.key].p : null)),
    intervals: groups.map((g) => (g.cells[s.key] ? [100 * g.cells[s.key].lo, 100 * g.cells[s.key].hi] : null)),
    ns: groups.map((g) => (g.cells[s.key] ? g.cells[s.key].n : null)),
  }));
  const opts = baseOptions(yTitle, 0, yMax);
  opts.plugins.tooltip.callbacks.label = (c) => {
    const ds = c.dataset; const iv = ds.intervals[c.dataIndex];
    return `${ds.label}: ${c.parsed.y.toFixed(1)}% [${iv[0].toFixed(0)}, ${iv[1].toFixed(0)}], n ${ds.ns[c.dataIndex].toLocaleString()}`;
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
  const opts = baseOptions("percentage points, stacked minus plain", undefined, undefined);
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
        const x1 = chart.scales.x.getPixelForValue(100 * rows[i].lo), x2 = chart.scales.x.getPixelForValue(100 * rows[i].hi);
        ctx.save(); ctx.strokeStyle = css("--fg"); ctx.globalAlpha = 0.7; ctx.lineWidth = 1.2;
        ctx.beginPath(); ctx.moveTo(x1, bar.y); ctx.lineTo(x2, bar.y); ctx.moveTo(x1, bar.y - 4); ctx.lineTo(x1, bar.y + 4); ctx.moveTo(x2, bar.y - 4); ctx.lineTo(x2, bar.y + 4); ctx.stroke(); ctx.restore();
      });
    },
  };
  opts.plugins.tooltip.callbacks.label = (c) => `${c.dataset.label}: ${c.parsed.x >= 0 ? "+" : ""}${c.parsed.x.toFixed(1)} pts, n stacked ${rows[c.dataIndex].n.toLocaleString()}`;
  charts.push(new Chart(document.getElementById(id), {
    type: "bar",
    data: { labels: rows.map((r) => r.label), datasets: [
      { label: "raw", data: rows.map((r) => 100 * r.raw), backgroundColor: css("--spread"), maxBarThickness: 14 },
      { label: "R-matched", data: rows.map((r) => 100 * r.matched), backgroundColor: css("--stack"), maxBarThickness: 14 },
    ] },
    options: opts, plugins: [hPlugin],
  }));
}

function table() {
  const tb = document.querySelector("#bookTable tbody");
  tb.innerHTML = DATA.book.map((r) => `<tr><td>${r.setup}</td><td>${r.cls}</td><td class="num">${r.n.toLocaleString()}</td>
    <td class="num ${r.avg < 0 ? "neg" : ""}">${r.avg >= 0 ? "+" : ""}${r.avg.toFixed(2)}%</td><td class="num">${pct(r.hit)}</td><td class="num">${pct(r.stop)}</td>
    <td class="num ${r.exp_r < 0 ? "neg" : ""}">${r.exp_r >= 0 ? "+" : ""}${r.exp_r.toFixed(3)}</td><td class="num ${r.total < 0 ? "neg" : ""}">${usd(r.total)}</td>
    <td class="num neg">${usd(r.dd)}</td><td class="num">${r.r.toFixed(2)}</td></tr>`).join("");
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
}
draw();
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", draw);
</script>
"""


def main() -> None:
    data = build_data()
    html = TEMPLATE.replace("__ASOF__", data["as_of"]).replace("__DATA__", json.dumps(data))
    out = RESULTS / "chance_book_page.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({len(html):,} bytes)")


if __name__ == "__main__":
    sys.exit(main())
