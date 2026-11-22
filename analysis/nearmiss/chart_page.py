"""The private chart page for the near-miss study: example trades drawn on daily candles, the
how-far-they-got bars and the owner's what-if table.

Run after run_htf.py and whatif.py (it reads their row files):
    uv run python -m analysis.nearmiss.run_htf
    uv run python -m analysis.nearmiss.whatif --exit 0.40 --min-target 4
    uv run python -m analysis.nearmiss.chart_page

Writes analysis/nearmiss/data/nearmiss_page.html (gitignored) for publishing as a private page,
and nearmiss_page_preview.html (the same content wrapped as a full document, for a local look).
The published page is never linked in this public repo. The page draws only numbers that are in
RECEIPT.md; the example trades are picked by a rule, not by looks (see KINDS).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.nearmiss.core import classify
from analysis.nearmiss.htf import aggregate, candidates, enter, walk_sub

HERE = Path(__file__).parent
DATA = HERE / "data"
EXIT = 0.40
MIN_TARGET = 4.0
# a fixed list of well-known names, so the examples are not picked by looks
NAMES = [
    "NVDA",
    "AAPL",
    "MSFT",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
    "AMD",
    "AVGO",
    "MU",
    "JPM",
    "XOM",
    "SPY",
    "QQQ",
    "XLK",
    "XLE",
    "XLF",
]
# (timeframe, family or None for any, ending, heading). For each, the MOST RECENT trade in
# NAMES with MIN_TARGET or more to the target, on a symbol not already used.
KINDS = [
    ("W", "2-2 reversal", "won", "A weekly 2-2 reversal that reached its target"),
    ("W", "2-1-2 reversal", "won", "A weekly 2-1-2 reversal that reached its target"),
    ("W", "2-2 reversal", "early", "Stopped out before it got 40% of the way"),
    ("W", None, "mid", "Stopped out after it got past 40% of the way"),
    ("W", None, "near", "A near miss: 90% of the way or more, then stopped"),
    ("W", "2-1-2 reversal", "went3", "Went 3 after the entry"),
    ("W", "3-2-2 reversal", "any", "A weekly 3-2-2, stop at the 3 bar's extreme"),
    ("M", "2-2 reversal", "won", "A monthly 2-2 reversal that reached its target"),
    ("M", None, "mid", "A monthly pattern stopped after it got past 40% of the way"),
    ("M", None, "went3", "A monthly pattern that went 3 after the entry"),
]
UNIT = {"W": "week", "M": "month"}
CODE = {0: "ref", 1: "1", 2: "2U", -2: "2D", 3: "3"}
KIND_WORDS = {1: "an inside", 2: "a 2-up", -2: "a 2-down", 3: "an outside"}


def day(d) -> str:
    return f"{d:%b} {d.day}, {d.year}"


def bar_name(tf: str, d, cap: bool = True) -> str:
    if tf == "M":
        return f"{d:%B %Y}"
    return f"{'The' if cap else 'the'} week of {d:%b} {d.day}"


def later(n: int) -> str:
    return "the same day" if n == 0 else "1 session later" if n == 1 else f"{n} sessions later"


def px(x: float) -> str:
    return f"{x:,.2f}"


def signed(x: float) -> str:
    return f"{x:+.1f}%"


def matches(ending: str, w1, w40) -> bool:
    if ending == "won":
        return w1.outcome == "won"
    if ending == "early":
        return w1.outcome == "failed" and w1.p_hi < EXIT and w40.outcome != "won"
    if ending == "mid":
        return w1.outcome == "failed" and EXIT <= w1.p_lo < 0.90 and w40.outcome == "won"
    if ending == "near":
        return w1.outcome == "failed" and w1.p_lo >= 0.90
    if ending == "went3":
        return w1.outcome == "went3"
    return w1.outcome in ("won", "failed", "went3")


def collect() -> list[dict]:
    """Every resolved weekly / monthly trade in NAMES with MIN_TARGET or more to the target."""
    out = []
    for sym in NAMES:
        df = pd.read_csv(DATA / f"{sym}.csv", index_col=0, parse_dates=True).round(4)
        df = df[(df.High >= df.Low) & (df.Low > 0)]
        o, h, l, c = (df[x].values for x in ("Open", "High", "Low", "Close"))
        for tf in ("W", "M"):
            big = aggregate(df.index, o, h, l, c, tf)
            types = classify(big[1], big[2])
            for cd in candidates(*big[:4]):
                if cd.family == "3-1-2 flat":
                    continue
                d0, d1 = int(big[4][cd.i]), int(big[5][cd.i])
                status, e, entry = enter(cd, o, h, l, c, d0, d1)
                if status != "triggered":
                    continue
                if 100 * abs(cd.target - entry) / entry < MIN_TARGET:
                    continue
                w1 = walk_sub(o, h, l, c, cd, e, entry, d1, 1.0)
                w40 = walk_sub(o, h, l, c, cd, e, entry, d1, EXIT)
                if w1.outcome not in ("won", "failed", "went3"):
                    continue
                out.append(
                    dict(sym=sym, tf=tf, cd=cd, e=e, entry=entry, d1=d1, w1=w1, w40=w40,
                         df=df, big=big, types=types)
                )  # fmt: skip
    return sorted(out, key=lambda t: t["df"].index[t["e"]], reverse=True)


def story(t: dict) -> dict:
    cd, tf, df, big = t["cd"], t["tf"], t["df"], t["big"]
    unit = UNIT[tf]
    a, s = cd.i - 2, cd.i - 1
    first = big[4]
    name_a, name_s = bar_name(tf, df.index[first[a]]), bar_name(tf, df.index[first[s]])
    long = cd.side > 0
    near, far = ("high", "low") if long else ("low", "high")
    through = "up through" if long else "down through"
    pos = "long" if long else "short"
    against = "2 down" if long else "2 up"
    entry, e = t["entry"], t["e"]
    dist = 100 * abs(cd.target - entry) / entry
    risk = 100 * abs(entry - cd.stop) / entry
    on = day(df.index[e])
    if cd.family == "2-2 reversal":
        kind_a = KIND_WORDS[int(t["types"][a])]
        setup = f"{name_a} was {kind_a} {unit}. {name_s} went {against}: the setup bar."
        trig = f"On {on}, inside the next {unit}, price traded {through} the setup {unit}'s {near} at {px(cd.trigger)}: {pos}."
        levels = (
            f"Target {px(cd.target)}: the {near} of the {unit} before the setup, {dist:.1f}% away. "
            f"Stop {px(cd.stop)}: the setup {unit}'s {far}, {risk:.1f}% away."
        )
    elif cd.family == "2-1-2 reversal":
        setup = f"{name_a} went {against}. {name_s} stayed inside it."
        trig = (
            f"On {on} price traded {through} the inside {unit}'s {near} at {px(cd.trigger)}: {pos}."
        )
        levels = (
            f"Target {px(cd.target)}: the {against} {unit}'s {near}, {dist:.1f}% away. "
            f"Stop {px(cd.stop)}: that {unit}'s {far}, not the inside {unit}'s, {risk:.1f}% away."
        )
    elif cd.family.startswith("3-1-2"):
        colour = "red" if big[3][a] < big[0][a] else "green"
        way = "against" if cd.family.endswith("reversal") else "with"
        setup = f"{name_a} was an outside {unit} that closed {colour}. {name_s} stayed inside it."
        trig = (
            f"On {on} price traded {through} the inside {unit}'s {near} at {px(cd.trigger)}: "
            f"{pos}, {way} the outside {unit}'s close."
        )
        levels = (
            f"Target {px(cd.target)}: the outside {unit}'s {near}, {dist:.1f}% away. "
            f"Stop {px(cd.stop)}: its {far}, {risk:.1f}% away."
        )
    else:  # 3-2-2
        setup = f"{name_a} was an outside {unit}. {name_s} went {against} through its {far}."
        trig = (
            f"On {on} price traded back {through} that {unit}'s {near} at {px(cd.trigger)}: {pos}."
        )
        levels = (
            f"Target {px(cd.target)}: the outside {unit}'s {near}, {dist:.1f}% away. "
            f"Stop {px(cd.stop)}: the outside {unit}'s {far}, {risk:.1f}% away. The {against} "
            f"{unit} had already traded through that level before the entry; no trade was on "
            f"yet, so it does not count."
        )
    if entry != cd.trigger:
        trig += f" It gapped through the trigger, so the fill is that day's open, {px(entry)}."

    w1, w40 = t["w1"], t["w40"]
    pl1 = 100 * cd.side * (w1.fill - entry) / entry
    pl40 = 100 * cd.side * (w40.fill - entry) / entry
    when1 = f"{day(df.index[w1.j])} ({later(w1.j - e)})"
    got = f"{100 * max(w1.p_lo, 0):.0f}%"
    if w1.outcome == "won":
        held = f"Held to the target: reached on {when1}, {signed(pl1)}."
        pill = "reached the target"
    elif w1.outcome == "failed":
        held = f"Held to the target: got {got} of the way, then broke the stop on {when1}, {signed(pl1)}."
        pill = "stopped out"
    else:
        held = (
            f"Held to the target: got {got} of the way. On {when1}, still inside the entry "
            f"{unit}, price took out the setup {unit}'s {far} at {px(cd.other)}: the entry "
            f"{unit} went 3. Out there, {signed(pl1)}."
        )
        pill = "went 3 after entry"
    level40 = entry + EXIT * (cd.target - entry)
    if w40.outcome == "won":
        early = (
            f"Out at 40% of the way ({px(level40)}): filled on {day(df.index[w40.j])} "
            f"({later(w40.j - e)}), {signed(pl40)}."
        )
    else:
        early = f"Out at 40% of the way ({px(level40)}): never reached, so the same exit, {signed(pl40)}."
    return dict(setup=setup, trig=trig, levels=levels, held=held, early=early, pill=pill,
                pl1=pl1, pl40=pl40, level40=level40)  # fmt: skip


def example(t: dict, heading: str) -> dict:
    cd, tf, df, big = t["cd"], t["tf"], t["df"], t["big"]
    first, last = big[4], big[5]
    a, s, i = cd.i - 2, cd.i - 1, cd.i
    e, w1, w40 = t["e"], t["w1"], t["w40"]
    pad = 8 if tf == "W" else 15
    x_from = int(first[max(a - 1, 0)])
    x_to = int(min(len(df) - 1, max(w1.j, w40.j, int(last[i])) + pad))
    win = df.iloc[x_from : x_to + 1]
    bars = [
        [f"{d:%Y-%m-%d}", float(r.Open), float(r.High), float(r.Low), float(r.Close)]
        for d, r in win.iterrows()
    ]

    def rel(x: int) -> int:
        return int(min(max(x, x_from), x_to) - x_from)

    boxes = []
    for j, label in ((a, CODE[int(t["types"][a])]), (s, CODE[int(t["types"][s])]), (i, "entry")):
        boxes.append(
            dict(x0=rel(int(first[j])), x1=rel(int(last[j])), lo=float(big[2][j]),
                 hi=float(big[1][j]), label=label)
        )  # fmt: skip
    st = story(t)
    exit_x = rel(w1.j)
    lines = [
        dict(
            key="target", label="target", price=float(cd.target), x0=rel(int(first[a])), x1=exit_x
        ),
        dict(key="entry", label="entry", price=float(t["entry"]), x0=rel(int(first[s])), x1=exit_x),
        dict(
            key="stop",
            label="stop",
            price=float(cd.stop),
            x0=rel(int(first[s if cd.family == "2-2 reversal" else a])),
            x1=exit_x,
        ),
        dict(key="k40", label="40%", price=float(st["level40"]), x0=rel(e), x1=exit_x),
    ]
    if cd.other != cd.stop and cd.family != "3-2-2 reversal":
        lines.append(
            dict(key="other", label="goes 3 at", price=float(cd.other), x0=rel(int(first[s])),
                 x1=rel(int(last[i])))
        )  # fmt: skip
    ends = {"won": "target reached", "failed": "stop broken", "went3": "went 3: out"}
    marks = [dict(key="entry", x=rel(e), price=float(t["entry"]), label="entry")]
    marks.append(dict(key="exit", x=exit_x, price=float(w1.fill), label=ends[w1.outcome]))
    if w40.outcome == "won":
        marks.append(dict(key="k40", x=rel(w40.j), price=float(w40.fill), label="40% exit filled"))
    unit = UNIT[tf]
    return dict(
        heading=heading,
        title=f"{t['sym']}: {unit}ly {cd.family}, {'long' if cd.side > 0 else 'short'}",
        unit=unit,
        side=cd.side,
        bars=bars,
        boxes=boxes,
        lines=lines,
        marks=marks,
        entry_x=rel(e),
        exit_x=exit_x,
        entry=float(t["entry"]),
        target=float(cd.target),
        **{k: st[k] for k in ("setup", "trig", "levels", "held", "early", "pill")},
        pl1=round(st["pl1"], 1),
        pl40=round(st["pl40"], 1),
    )


def pick_examples() -> list[dict]:
    trades = collect()
    used: set[str] = set()
    out = []
    for tf, family, ending, heading in KINDS:
        pool = [
            t
            for t in trades
            if t["tf"] == tf
            and (family is None or t["cd"].family == family)
            and matches(ending, t["w1"], t["w40"])
        ]
        fresh = [t for t in pool if t["sym"] not in used]
        chosen = (fresh or pool)[:1]
        for t in chosen:
            used.add(t["sym"])
            out.append(example(t, heading))
    return out


def whatif_rows() -> list[dict]:
    r = pd.read_csv(DATA / f"rows_whatif_{EXIT:.2f}.csv", low_memory=False)
    r = r[r.dist_pct >= MIN_TARGET]
    rows = []
    for tf, name in (("W", "Week"), ("M", "Month"), ("Q", "Quarter")):
        d = r[r.tf == tf]
        row = dict(name=name, n=len(d))
        for tag, key in ((f"{EXIT:.2f}", "a"), ("1.00", "b")):
            won = d[f"out_{tag}"] == "won"
            pl = d[f"pl_{tag}"]
            row[key] = dict(
                wins=100 * won.mean(),
                win=pl[won].mean(),
                loss=pl[~won].mean(),
                per=pl.mean(),
                longs=pl[d.side > 0].mean(),
                shorts=pl[d.side < 0].mean(),
            )
        rows.append(row)
    return rows


def how_far() -> list[dict]:
    r = pd.read_csv(DATA / "rows_htf.csv", low_memory=False)
    out = []
    for tf, name in (("W", "Week"), ("M", "Month"), ("Q", "Quarter")):
        d = r[(r.tf == tf) & r["out_1.00"].isin(["failed", "went3"])]
        hist = np.histogram(d.p_lo.clip(0, 0.9999), bins=np.arange(0, 1.0001, 0.1))[0] / len(d)
        out.append(dict(name=name, n=int(len(d)), steps=[round(100 * x, 1) for x in hist]))
    return out


def table_html(rows: list[dict]) -> str:
    def cells(v: dict) -> str:
        return (
            f"<td class='num'>{v['wins']:.1f}%</td><td class='num'>{v['win']:+.2f}%</td>"
            f"<td class='num'>{v['loss']:+.2f}%</td><td class='num strong'>{v['per']:+.2f}%</td>"
        )

    body = "".join(
        f"<tr><th scope='row'>{r['name']}</th><td class='num'>{r['n']:,}</td>{cells(r['a'])}"
        f"{cells(r['b'])}</tr>"
        for r in rows
    )
    sides = "".join(
        f"<tr><th scope='row'>{r['name']}</th><td class='num'>{r['a']['longs']:+.2f}%</td>"
        f"<td class='num'>{r['b']['longs']:+.2f}%</td><td class='num'>{r['a']['shorts']:+.2f}%</td>"
        f"<td class='num'>{r['b']['shorts']:+.2f}%</td></tr>"
        for r in rows
    )
    return f"""
<div class="scroll"><table>
<thead>
<tr><th rowspan="2">Pattern timeframe</th><th rowspan="2" class="num">Trades</th>
<th colspan="4" class="group">Out at 40% of the way</th><th colspan="4" class="group">Held to the target</th></tr>
<tr><th class="num">Wins</th><th class="num">Avg win</th><th class="num">Avg loss</th><th class="num">Per trade</th>
<th class="num">Wins</th><th class="num">Avg win</th><th class="num">Avg loss</th><th class="num">Per trade</th></tr>
</thead><tbody>{body}</tbody></table></div>
<h3>The same trades, per trade, by side</h3>
<div class="scroll"><table class="narrow">
<thead><tr><th>Pattern timeframe</th><th class="num">Longs, out at 40%</th><th class="num">Longs, to target</th>
<th class="num">Shorts, out at 40%</th><th class="num">Shorts, to target</th></tr></thead>
<tbody>{sides}</tbody></table></div>"""


def how_far_table(hist: list[dict]) -> str:
    head = "".join(f"<th class='num'>{10 * i}-{10 * i + 10}%</th>" for i in range(10))
    body = "".join(
        f"<tr><th scope='row'>{h['name']} ({h['n']:,})</th>"
        + "".join(f"<td class='num'>{v:.1f}%</td>" for v in h["steps"])
        + "</tr>"
        for h in hist
    )
    return (
        f"<div class='scroll'><table><thead><tr><th>Share of the way reached</th>{head}</tr>"
        f"</thead><tbody>{body}</tbody></table></div>"
    )


def articles(examples: list[dict]) -> str:
    parts = []
    for n, ex in enumerate(examples):
        parts.append(
            f"""<article class="trade">
<p class="eyebrow">{ex["heading"]}</p>
<h3>{ex["title"]} <span class="pill">{ex["pill"]}</span></h3>
<div class="chart" id="trade{n}"></div>
<ol class="story">
<li><b>The setup.</b> {ex["setup"]}</li>
<li><b>The entry.</b> {ex["trig"]}</li>
<li><b>The levels.</b> {ex["levels"]}</li>
<li><b>What happened.</b> {ex["held"]}</li>
<li><b>Your what-if.</b> {ex["early"]}</li>
</ol>
</article>"""
        )
    return "\n".join(parts)


TEMPLATE = r"""<title>Near-Miss Trade Examples</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* layout: one reading column; charts are wide diagrams that scroll sideways on a phone */
:root {
  --bg: #f6f5f1; --panel: #fffefb; --fg: #1d2430; --muted: #5d667a; --rule: #d9d6cc; --grid: #e6e3da;
  --entry: #2a78d6; --stop: #eb6834; --target: #6250d6; --up: #008300; --down: #e34948;
  --box: rgba(29, 36, 48, 0.055); --box-line: rgba(29, 36, 48, 0.28);
  --font-body: "IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
  --font-mono: "IBM Plex Mono", "SFMono-Regular", Consolas, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #12161d; --panel: #1a2029; --fg: #e8e6df; --muted: #9aa3b5; --rule: #2b3340; --grid: #262d38;
  --entry: #3987e5; --stop: #d95926; --target: #9085e9; --up: #0ca30c; --down: #e66767;
  --box: rgba(232, 230, 223, 0.06); --box-line: rgba(232, 230, 223, 0.30); color-scheme: dark; } }
:root[data-theme="dark"] {
  --bg: #12161d; --panel: #1a2029; --fg: #e8e6df; --muted: #9aa3b5; --rule: #2b3340; --grid: #262d38;
  --entry: #3987e5; --stop: #d95926; --target: #9085e9; --up: #0ca30c; --down: #e66767;
  --box: rgba(232, 230, 223, 0.06); --box-line: rgba(232, 230, 223, 0.30); color-scheme: dark; }
body { background: var(--bg); color: var(--fg); font-family: var(--font-body); font-size: 15px; line-height: 1.55; margin: 0; }
.wrap { max-width: 1040px; margin: 0 auto; padding-block: 28px 56px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: flex; flex-direction: column; gap: 36px; }
section, header, footer { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
h1 { font-size: 1.9rem; line-height: 1.15; font-weight: 600; margin: 0; text-wrap: balance; }
h2 { font-size: 1.25rem; line-height: 1.25; font-weight: 600; margin: 0; text-wrap: balance; }
h3 { font-size: 1.02rem; font-weight: 600; margin: 0; }
p { margin: 0; max-width: 68ch; }
.eyebrow { font-family: var(--font-mono); font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); }
.lede { font-size: 1.05rem; }
.note { color: var(--muted); font-size: 0.9rem; }
.scroll { overflow-x: auto; }
table { border-collapse: collapse; font-size: 0.88rem; min-width: 720px; width: 100%; }
table.narrow { min-width: 520px; }
th, td { padding: 7px 10px; border-bottom: 1px solid var(--rule); text-align: left; white-space: nowrap; }
thead th { font-family: var(--font-mono); font-size: 0.7rem; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted); font-weight: 500; }
th.group { text-align: center; border-left: 1px solid var(--rule); }
td.num, th.num { text-align: right; font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
td.strong { font-weight: 500; color: var(--fg); }
tbody th { font-weight: 500; }
.keys { list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 8px 22px; font-size: 0.9rem; }
.keys li { display: flex; align-items: center; gap: 8px; }
.keys svg { flex: none; }
.hists { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }
.hist, .chart { background: var(--panel); border: 1px solid var(--rule); border-radius: 6px; position: relative; }
.hist { padding: 12px 12px 6px; }
.hist h3 { font-size: 0.92rem; }
.hist p { font-size: 0.8rem; color: var(--muted); }
.chart { overflow-x: auto; }
.trade { display: flex; flex-direction: column; gap: 10px; min-width: 0; padding-top: 22px; border-top: 1px solid var(--rule); }
.pill { font-family: var(--font-mono); font-size: 0.7rem; font-weight: 500; letter-spacing: 0.04em; border: 1px solid var(--rule);
  border-radius: 999px; padding: 2px 9px; margin-left: 6px; color: var(--muted); white-space: nowrap; vertical-align: 2px; }
.story { margin: 0; padding-left: 1.2rem; display: flex; flex-direction: column; gap: 4px; max-width: 78ch; }
.story b { font-weight: 600; }
details summary { cursor: pointer; color: var(--muted); font-size: 0.88rem; }
svg text { font-family: var(--font-mono); font-size: 11px; fill: var(--muted); }
svg text.tag { fill: var(--fg); font-size: 11.5px; }
svg text.boxlabel { fill: var(--fg); font-size: 11px; font-weight: 500; }
svg text.val { fill: var(--fg); }
svg:focus-visible { outline: 2px solid var(--entry); outline-offset: -2px; }
.gridline { stroke: var(--grid); stroke-width: 1; }
.axisline { stroke: var(--rule); stroke-width: 1; }
.wick { stroke-width: 1; }
.up { stroke: var(--up); fill: var(--panel); }
.down { stroke: var(--down); fill: var(--down); }
.htf { fill: var(--box); stroke: var(--box-line); stroke-width: 1; }
.ln { stroke-width: 2; fill: none; }
.ln.faint { stroke-width: 1; opacity: 0.45; }
.ln-entry { stroke: var(--entry); } .ln-stop { stroke: var(--stop); } .ln-target { stroke: var(--target); }
.ln-k40 { stroke: var(--fg); stroke-dasharray: 5 4; } .ln-other { stroke: var(--muted); stroke-dasharray: 2 3; }
.mk { stroke: var(--panel); stroke-width: 2; }
.mk-entry { fill: var(--entry); } .mk-exit { fill: var(--fg); } .mk-k40 { fill: var(--panel); stroke: var(--fg); }
.cross { stroke: var(--muted); stroke-width: 1; pointer-events: none; }
.bar { fill: var(--entry); }
.bar.hot { opacity: 0.75; }
.tip { position: absolute; pointer-events: none; background: var(--panel); border: 1px solid var(--rule); border-radius: 6px;
  padding: 7px 10px; font-family: var(--font-mono); font-size: 11.5px; line-height: 1.5; color: var(--muted); white-space: nowrap;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.14); z-index: 5; }
.tip b { color: var(--fg); font-weight: 500; }
.tip .when { color: var(--fg); font-weight: 500; }
@media (prefers-reduced-motion: no-preference) { .bar { transition: opacity 120ms; } }
</style>

<main class="wrap">
<header>
  <p class="eyebrow">TVB-46 / exploratory / private</p>
  <h1>Near-miss study: example trades and the 40% what-if</h1>
  <p class="lede">Real trades from the study, drawn on daily candles, so you can check that the pattern, the entry, the target and the stop are where you expect them. Then your what-if in numbers, and how far the trades that missed actually got.</p>
  <p class="note">Every figure here is in the study's receipt. Equal size on every trade, no leverage, no fees, fills at the levels. Daily bars from Yahoo, split-adjusted, 142 of today's names back to 2000, so survivors only.</p>
</header>

<section>
  <h2>How to read a chart</h2>
  <ul class="keys">
    <li><svg width="30" height="16" aria-hidden="true"><rect x="1" y="2" width="28" height="12" class="htf"/></svg>the pattern's three bars on its own timeframe, labelled 2U, 2D, 1, 3 or entry</li>
    <li><svg width="30" height="16" aria-hidden="true"><line x1="1" y1="8" x2="29" y2="8" class="ln ln-entry"/></svg>entry: the trigger level</li>
    <li><svg width="30" height="16" aria-hidden="true"><line x1="1" y1="8" x2="29" y2="8" class="ln ln-target"/></svg>target</li>
    <li><svg width="30" height="16" aria-hidden="true"><line x1="1" y1="8" x2="29" y2="8" class="ln ln-stop"/></svg>stop</li>
    <li><svg width="30" height="16" aria-hidden="true"><line x1="1" y1="8" x2="29" y2="8" class="ln ln-k40"/></svg>40% of the way to the target</li>
    <li><svg width="30" height="16" aria-hidden="true"><line x1="1" y1="8" x2="29" y2="8" class="ln ln-other"/></svg>the level that makes the entry bar a 3, live only until that bar closes</li>
    <li><svg width="16" height="16" aria-hidden="true"><path d="M8 2 L14 13 L2 13 Z" class="mk mk-entry"/></svg>entry</li>
    <li><svg width="16" height="16" aria-hidden="true"><circle cx="8" cy="8" r="5" class="mk mk-exit"/></svg>exit when held to the target</li>
    <li><svg width="16" height="16" aria-hidden="true"><path d="M8 2 L14 8 L8 14 L2 8 Z" class="mk mk-k40"/></svg>where the 40% exit fills</li>
    <li><svg width="22" height="16" aria-hidden="true"><line x1="5" y1="1" x2="5" y2="15" class="wick up"/><rect x="2" y="4" width="6" height="8" class="up"/><line x1="16" y1="1" x2="16" y2="15" class="wick down"/><rect x="13" y="4" width="6" height="8" class="down"/></svg>hollow candle closed up, filled closed down</li>
  </ul>
  <p class="note">Each line is drawn heavy while it is live and faint afterwards. Move the pointer over a chart, or focus it and use the arrow keys, to read each day and how far toward the target the trade had got by then.</p>
</section>

<section>
  <h2>Your what-if: out at 40% of the way, only setups with 4% or more to the target</h2>
  <p>The stop and the went-3 exit stay where the pattern puts them. Only the profit exit moves in, and only setups with at least 4% of price between entry and target are taken.</p>
  __WHATIF__
  <p class="note">Longs gain and shorts lose under both exits because today's large names rose for 25 years. The daily timeframe is left out: on one day in five the entry bar goes outside and daily bars cannot say which side broke first.</p>
</section>

<section>
  <h2>How far the trades that missed their target got</h2>
  <p>Every trade that was stopped out or went 3 after the entry, by the furthest point it reached, as a share of the way from entry to target. All five pattern families, no minimum distance.</p>
  <div class="hists" id="hists"></div>
  <details><summary>The same numbers as a table</summary>__HOWFAR__</details>
</section>

<section>
  <h2>Example trades</h2>
  <p>Picked by a rule, not by looks: from a fixed list of 17 well-known names, the most recent weekly or monthly trade of each kind with 4% or more to the target, never the same name twice.</p>
  __ARTICLES__
</section>

<footer>
  <p class="note">Exploratory research: no pre-registration, no external audit. Nothing here is a rule or a recommendation. Prices are split-adjusted, so older charts will not match the prices printed at the time.</p>
</footer>
</main>

<script>
const DATA = __DATA__;
const NS = "http://www.w3.org/2000/svg";
function el(name, attrs, parent) {
  const e = document.createElementNS(NS, name);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
function txt(parent, x, y, s, cls, anchor) {
  const t = el("text", { x: x, y: y, "text-anchor": anchor || "start" }, parent);
  if (cls) t.setAttribute("class", cls);
  t.textContent = s;
  return t;
}
function money(v) { return v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
function niceTicks(lo, hi, count) {
  const raw = (hi - lo) / count, mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const norm = raw / mag, step = (norm < 1.5 ? 1 : norm < 3 ? 2 : norm < 7 ? 5 : 10) * mag;
  const out = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(v);
  return { ticks: out, step: step };
}
function fmtDate(s, opts) {
  return new Date(s + "T00:00:00Z").toLocaleDateString("en-US", Object.assign({ timeZone: "UTC" }, opts));
}
function tipRow(tip, label, value) {
  const row = document.createElement("div");
  const b = document.createElement("b");
  b.textContent = value;
  row.appendChild(b);
  row.appendChild(document.createTextNode(" " + label));
  tip.appendChild(row);
}
function placeTip(host, tip, px, py) {
  const w = tip.offsetWidth, h = tip.offsetHeight;
  const left = px + 14 + w > host.scrollLeft + host.clientWidth ? px - 14 - w : px + 14;
  tip.style.left = Math.max(host.scrollLeft + 4, left) + "px";
  tip.style.top = Math.max(4, Math.min(py - h / 2, host.clientHeight - h - 4)) + "px";
}

function drawTrade(host, ex) {
  host.textContent = "";
  const W = Math.max(host.clientWidth, 700), H = 410;
  const m = { l: 56, r: 150, t: 34, b: 30 };
  const svg = el("svg", { width: W, height: H, viewBox: "0 0 " + W + " " + H, role: "img", tabindex: 0,
    "aria-label": ex.title + ", " + ex.pill + ". " + ex.held }, host);
  const n = ex.bars.length, pw = W - m.l - m.r, ph = H - m.t - m.b, step = pw / n;
  const x = function (i) { return m.l + (i + 0.5) * step; };
  let lo = Infinity, hi = -Infinity;
  ex.bars.forEach(function (b) { lo = Math.min(lo, b[3]); hi = Math.max(hi, b[2]); });
  ex.lines.forEach(function (ln) { lo = Math.min(lo, ln.price); hi = Math.max(hi, ln.price); });
  const pad = (hi - lo) * 0.06; lo -= pad; hi += pad;
  const y = function (p) { return m.t + (hi - p) / (hi - lo) * ph; };

  const nt = niceTicks(lo, hi, 5);
  const dec = nt.step < 1 ? 2 : nt.step < 10 ? 1 : 0;
  nt.ticks.forEach(function (v) {
    el("line", { x1: m.l, x2: m.l + pw, y1: y(v), y2: y(v), class: "gridline" }, svg);
    txt(svg, m.l - 8, y(v) + 4, v.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec }), "", "end");
  });
  el("line", { x1: m.l, x2: m.l + pw, y1: m.t + ph, y2: m.t + ph, class: "axisline" }, svg);

  // date ticks: week starts on a short window, month starts on a long one
  let lastX = -1e9, prev = null;
  ex.bars.forEach(function (b, i) {
    const d = new Date(b[0] + "T00:00:00Z");
    const key = n <= 75 ? Math.floor((d.getTime() / 864e5 + 3) / 7) : d.getUTCFullYear() * 12 + d.getUTCMonth();
    if (prev !== null && key !== prev && x(i) - lastX >= 58) {
      const label = n <= 75 ? fmtDate(b[0], { month: "short", day: "numeric" })
        : fmtDate(b[0], { month: "short" }) + (d.getUTCMonth() === 0 ? " " + d.getUTCFullYear() : "");
      el("line", { x1: x(i) - step / 2, x2: x(i) - step / 2, y1: m.t + ph, y2: m.t + ph + 4, class: "axisline" }, svg);
      txt(svg, x(i) - step / 2 + 2, H - 10, label);
      lastX = x(i);
    }
    prev = key;
  });
  txt(svg, m.l, H - 10, fmtDate(ex.bars[0][0], { month: "short", year: "numeric" })).setAttribute("opacity", lastX - m.l < 160 && lastX > 0 ? 0 : 1);

  // the pattern's bars on its own timeframe
  ex.boxes.forEach(function (b) {
    const x0 = m.l + b.x0 * step, x1 = m.l + (b.x1 + 1) * step;
    el("rect", { x: x0 + 0.5, y: y(b.hi), width: Math.max(x1 - x0 - 1, 1), height: Math.max(y(b.lo) - y(b.hi), 1), class: "htf" }, svg);
    txt(svg, (x0 + x1) / 2, m.t - 12, b.label, "boxlabel", "middle");
    el("line", { x1: (x0 + x1) / 2, x2: (x0 + x1) / 2, y1: m.t - 8, y2: Math.max(y(b.hi) - 2, m.t - 8), class: "axisline" }, svg);
  });

  // candles: hollow closed up, filled closed down
  const bw = Math.max(1, Math.min(step * 0.62, 11));
  ex.bars.forEach(function (b, i) {
    const cls = b[4] >= b[1] ? "up" : "down";
    el("line", { x1: x(i), x2: x(i), y1: y(b[2]), y2: y(b[3]), class: "wick " + cls }, svg);
    const top = y(Math.max(b[1], b[4])), bot = y(Math.min(b[1], b[4]));
    el("rect", { x: x(i) - bw / 2, y: top, width: bw, height: Math.max(bot - top, 1), class: cls }, svg);
  });

  // levels: heavy while live, faint afterwards, tagged at the right edge
  const tags = [];
  ex.lines.forEach(function (ln) {
    const xa = m.l + ln.x0 * step, xb = m.l + (ln.x1 + 1) * step, yy = y(ln.price);
    el("line", { x1: xa, x2: xb, y1: yy, y2: yy, class: "ln ln-" + ln.key }, svg);
    if (xb < m.l + pw) el("line", { x1: xb, x2: m.l + pw, y1: yy, y2: yy, class: "ln faint ln-" + ln.key }, svg);
    tags.push({ ln: ln, y: yy, at: yy });
  });
  tags.sort(function (a, b) { return a.y - b.y; });
  for (let i = 1; i < tags.length; i++) if (tags[i].at - tags[i - 1].at < 16) tags[i].at = tags[i - 1].at + 16;
  const over = tags.length ? tags[tags.length - 1].at - (m.t + ph) : 0;
  if (over > 0) {
    tags[tags.length - 1].at -= over;
    for (let i = tags.length - 2; i >= 0; i--) if (tags[i + 1].at - tags[i].at < 16) tags[i].at = tags[i + 1].at - 16;
  }
  tags.forEach(function (t) {
    const x0 = m.l + pw;
    el("path", { d: "M" + x0 + " " + t.y + " L" + (x0 + 8) + " " + t.at + " L" + (x0 + 24) + " " + t.at, class: "ln ln-" + t.ln.key }, svg);
    txt(svg, x0 + 29, t.at + 4, t.ln.label + " " + money(t.ln.price), "tag");
  });

  // entry and exits
  ex.marks.forEach(function (mk) {
    const cx = x(mk.x), cy = y(mk.price);
    if (mk.key === "entry") {
      const up = ex.side > 0 ? 1 : -1;
      el("path", { d: "M" + cx + " " + (cy - 7 * up) + " L" + (cx + 6.5) + " " + (cy + 5 * up) + " L" + (cx - 6.5) + " " + (cy + 5 * up) + " Z", class: "mk mk-entry" }, svg);
    } else if (mk.key === "exit") {
      el("circle", { cx: cx, cy: cy, r: 5.5, class: "mk mk-exit" }, svg);
    } else {
      el("path", { d: "M" + cx + " " + (cy - 6.5) + " L" + (cx + 6.5) + " " + cy + " L" + cx + " " + (cy + 6.5) + " L" + (cx - 6.5) + " " + cy + " Z", class: "mk mk-k40" }, svg);
    }
  });

  // hover and keyboard: a crosshair that snaps to the day, one readout
  const cross = el("line", { y1: m.t, y2: m.t + ph, class: "cross", visibility: "hidden" }, svg);
  const tip = document.createElement("div");
  tip.className = "tip"; tip.hidden = true; host.appendChild(tip);
  let cur = -1;
  function show(i, py) {
    cur = Math.max(0, Math.min(n - 1, i));
    const b = ex.bars[cur];
    cross.setAttribute("x1", x(cur)); cross.setAttribute("x2", x(cur)); cross.setAttribute("visibility", "visible");
    tip.textContent = "";
    const when = document.createElement("div");
    when.className = "when";
    when.textContent = fmtDate(b[0], { weekday: "short", month: "short", day: "numeric", year: "numeric" });
    tip.appendChild(when);
    tipRow(tip, "open", money(b[1])); tipRow(tip, "high", money(b[2])); tipRow(tip, "low", money(b[3])); tipRow(tip, "close", money(b[4]));
    if (cur >= ex.entry_x && cur <= ex.exit_x) {
      let best = ex.side > 0 ? -Infinity : Infinity;
      for (let j = ex.entry_x; j <= cur; j++) best = ex.side > 0 ? Math.max(best, ex.bars[j][2]) : Math.min(best, ex.bars[j][3]);
      const p = Math.max(0, Math.min(1, (best - ex.entry) / (ex.target - ex.entry)));
      tipRow(tip, "of the way to the target so far", Math.round(100 * p) + "%");
    }
    ex.marks.forEach(function (mk) { if (mk.x === cur) tipRow(tip, mk.label, money(mk.price)); });
    tip.hidden = false;
    placeTip(host, tip, x(cur), py === undefined ? m.t + 60 : py);
  }
  function hide() { cross.setAttribute("visibility", "hidden"); tip.hidden = true; cur = -1; }
  svg.addEventListener("pointermove", function (ev) {
    const r = svg.getBoundingClientRect(), px = ev.clientX - r.left;
    if (px < m.l || px > m.l + pw) { hide(); return; }
    show(Math.floor((px - m.l) / step), ev.clientY - r.top);
  });
  svg.addEventListener("pointerleave", hide);
  svg.addEventListener("focus", function () { if (cur < 0) show(ex.entry_x); });
  svg.addEventListener("blur", hide);
  svg.addEventListener("keydown", function (ev) {
    if (ev.key === "ArrowRight") { show(cur + 1); ev.preventDefault(); }
    else if (ev.key === "ArrowLeft") { show(cur - 1); ev.preventDefault(); }
    else if (ev.key === "Escape") hide();
  });
}

function drawHist(card, h) {
  // the card is already in the grid, so its width is final when measured here
  const title = document.createElement("h3");
  title.textContent = h.name + " patterns";
  const sub = document.createElement("p");
  sub.textContent = h.n.toLocaleString("en-US") + " trades that did not reach the target";
  card.appendChild(title); card.appendChild(sub);
  const W = Math.max(card.clientWidth - 26, 236), H = 204, m = { l: 34, r: 8, t: 16, b: 44 };
  const svg = el("svg", { width: W, height: H, viewBox: "0 0 " + W + " " + H, role: "img",
    "aria-label": h.name + " patterns: share of missed trades by how far they got, from " + h.steps[0] + "% in the first tenth of the way to " + h.steps[9] + "% in the last" }, card);
  const pw = W - m.l - m.r, ph = H - m.t - m.b, band = pw / 10, bw = Math.min(24, band - 4);
  const y = function (v) { return m.t + (20 - v) / 20 * ph; };
  [0, 5, 10, 15, 20].forEach(function (v) {
    el("line", { x1: m.l, x2: m.l + pw, y1: y(v), y2: y(v), class: v === 0 ? "axisline" : "gridline" }, svg);
    txt(svg, m.l - 6, y(v) + 4, v + "%", "", "end");
  });
  const tip = document.createElement("div");
  tip.className = "tip"; tip.hidden = true; card.appendChild(tip);
  h.steps.forEach(function (v, i) {
    const cx = m.l + (i + 0.5) * band, top = y(v);
    const bar = el("path", { class: "bar", d: "M" + (cx - bw / 2) + " " + y(0) + " V" + (top + 4) + " Q" + (cx - bw / 2) + " " + top + " " + (cx - bw / 2 + 4) + " " + top +
      " H" + (cx + bw / 2 - 4) + " Q" + (cx + bw / 2) + " " + top + " " + (cx + bw / 2) + " " + (top + 4) + " V" + y(0) + " Z" }, svg);
    if (i === 0 || i === 9) txt(svg, cx, top - 5, v.toFixed(1) + "%", "val", "middle");
    if (i % 3 === 0) txt(svg, cx, H - 26, 10 * i + "-" + (10 * i + 10), "", "middle");
    const hit = el("rect", { x: cx - band / 2, y: m.t, width: band, height: ph, fill: "transparent", tabindex: 0,
      "aria-label": 10 * i + " to " + (10 * i + 10) + " percent of the way: " + v.toFixed(1) + " percent of missed trades" }, svg);
    function on() {
      bar.classList.add("hot");
      tip.textContent = "";
      tipRow(tip, "of the trades that missed", v.toFixed(1) + "%");
      tipRow(tip, "of the way to the target", 10 * i + " to " + (10 * i + 10) + "%");
      tip.hidden = false;
      placeTip(card, tip, cx + 12, top + 30);
    }
    function off() { bar.classList.remove("hot"); tip.hidden = true; }
    hit.addEventListener("pointerenter", on); hit.addEventListener("pointerleave", off);
    hit.addEventListener("focus", on); hit.addEventListener("blur", off);
  });
  txt(svg, m.l + pw / 2, H - 7, "share of the way to the target, %", "", "middle");
}

function drawAll() {
  const hists = document.getElementById("hists");
  hists.textContent = "";
  const cards = DATA.howfar.map(function () {
    const card = document.createElement("div");
    card.className = "hist";
    hists.appendChild(card);
    return card;
  });
  DATA.howfar.forEach(function (h, i) { drawHist(cards[i], h); });
  DATA.examples.forEach(function (ex, i) { drawTrade(document.getElementById("trade" + i), ex); });
}
drawAll();
let timer = null, lastW = window.innerWidth;
window.addEventListener("resize", function () {
  if (window.innerWidth === lastW) return;
  lastW = window.innerWidth;
  clearTimeout(timer);
  timer = setTimeout(drawAll, 150);
});
</script>
"""


def main() -> None:
    examples = pick_examples()
    data = dict(examples=examples, howfar=how_far())
    page = (
        TEMPLATE.replace("__WHATIF__", table_html(whatif_rows()))
        .replace("__HOWFAR__", how_far_table(data["howfar"]))
        .replace("__ARTICLES__", articles(examples))
        .replace("__DATA__", json.dumps(data, separators=(",", ":")))
    )
    (DATA / "nearmiss_page.html").write_text(page, encoding="utf-8")
    wrapped = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'></head><body>"
        f"{page}</body></html>"
    )
    (DATA / "nearmiss_page_preview.html").write_text(wrapped, encoding="utf-8")
    print(f"{len(examples)} examples, {len(page) / 1024:.0f} KB")
    for ex in examples:
        print(
            f"  {ex['heading']:62s} {ex['title']:44s} {ex['bars'][ex['entry_x']][0]}  {ex['pill']:20s} {ex['pl1']:+.1f}% / {ex['pl40']:+.1f}%"
        )


if __name__ == "__main__":
    main()
