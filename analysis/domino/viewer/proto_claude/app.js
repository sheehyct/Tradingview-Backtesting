/* Domino Trade Viewer, amCharts 5 Stock Chart prototype (proto_claude).
   Reads the SAME per-coin JSON as the reference page (../data/<coin>.json) and draws the rows
   exactly as the reference app.js does: settle(), tradeSpan(), stackLevels(), setupDays() and
   the calendar bucketing are copied verbatim, so no trade logic is re-run here either. What is
   new is the chart engine (amCharts 5 StockChart on a GaplessDateAxis with data grouping OFF),
   its drawing toolbar with the built-in DataSaveControl (save / restore / autosave to browser
   storage, keyed per coin), and two chips per trade: the STRAT type of the last CLOSED week and
   month before the entry day (R10 operators: strict breaks, equality never breaks). */
(function () {
  "use strict";
  const DAY = 86400, HOUR = 3600, CAP = 20, MS = 1000;
  const COL = {
    gray: "#5a5f6e", grayWick: "#474b58",
    up: "#22c55e", down: "#ef4444",
    setup: "#f59e0b", ref: "#b7791f",
    level: "#3b82f6", exit: "#f43f5e", target: "#22c55e", oneR: "#a78bfa", stop: "#9ca3af", mm: "#f59e0b",
    week: "#38bdf8", violet: "#a78bfa",
  };
  const BOOK_RET = { C: "ret_C", A: "ret_A", B: "ret_B", D: "ret_D", D5: "ret_D5", ref: "ret5" };
  const BOOK_HIT = { A: "hit_A", B: "hit_B", D: "hit_D", D5: "hit_D5" };
  const BOOK_DAYS = { A: "days_A", B: "days_B", D: "days_D", D5: "days_D5", ref: "days_ref" };
  const CLS_LABEL = { exact_shared: "same price", near: "near, within 0.25%", within1: "within 1%", spread: "spread, more than 1% apart" };
  const KIND_LABEL = { reversal: "reversal", continuation: "continuation", inside: "inside break", outside: "outside break" };
  const TF_LABEL = { D: "daily", W: "weekly", M: "monthly" };
  const DASH = { 0: [], 1: [1, 3], 2: [5, 3], 3: [9, 4], 4: [2, 6] };          // lightweight-charts line styles, as dash arrays
  const INTERVAL = { "1H": { timeUnit: "hour", count: 1 }, "1D": { timeUnit: "day", count: 1 }, "1W": { timeUnit: "week", count: 1 }, "1M": { timeUnit: "month", count: 1 } };
  const BT_CLASS = { "1": "t1", "2U": "t2u", "2D": "t2d", "3": "t3", "?": "tq" };
  const BT_WORD = { "1": "inside bar", "2U": "2 up (broke the high only)", "2D": "2 down (broke the low only)", "3": "outside bar", "?": "unknown" };

  const $ = (id) => document.getElementById(id);
  const state = {
    index: null, dates: null, coin: null, data: null, daily: [], hourly: [], cal: new Map(),
    chartTf: "1D", tf: new Set(["D", "W", "M"]), kind: new Set(["reversal", "continuation", "inside", "outside"]),
    dir: new Set(["up", "down"]), liquid: false, hasT1: false, book: "C", size: 1000,
    list: [], sel: -1, cur: null, dateMode: null, am: null, showSys: true, showMan: true,
    proof: { seed: false, then: null },
  };

  // ---------------------------------------------------------------- calendar (census rules; verbatim from the reference page)
  function weekStart(t) { const dse = Math.floor(t / DAY); const wd = (dse + 4) % 7; return (dse - (wd + 6) % 7) * DAY; }
  function monthStart(t) { const d = new Date(t * 1000); return Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1) / 1000; }
  function nextMonth(t) { const d = new Date(t * 1000); return Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 1) / 1000; }
  function aggregate(daily, tf) {
    const start = tf === "W" ? weekStart : monthStart;
    const out = [];
    daily.forEach((b, i) => {
      const k = start(b[0]);
      if (!out.length || out[out.length - 1].t !== k) {
        out.push({ t: k, end: tf === "W" ? k + 7 * DAY : nextMonth(k), o: b[1], h: b[2], l: b[3], c: b[4], v: b[5], days: [i] });
      } else {
        const x = out[out.length - 1];
        x.h = Math.max(x.h, b[2]); x.l = Math.min(x.l, b[3]); x.c = b[4]; x.v += b[5]; x.days.push(i);
      }
    });
    const lastEnd = daily.length ? daily[daily.length - 1][0] + DAY : 0;
    for (const x of out) x.complete = x.end <= lastEnd && x.days.length === (x.end - x.t) / DAY;
    return out;
  }
  function calendarFor(coin, d) {
    // per-coin day index + week / month buckets, cached so the all-coins day view can type its cards too
    if (!state.cal.has(coin)) {
      const weeks = aggregate(d.daily, "W"), months = aggregate(d.daily, "M");
      const wo = new Map(); for (const w of weeks) for (const di of w.days) wo.set(d.daily[di][0], w.o);
      state.cal.set(coin, { dayIdx: new Map(d.daily.map((b, i) => [iso(b[0]), i])), weeks, months, weekOpenAt: (t) => wo.get(t - (t % DAY)) ?? null });
    }
    return state.cal.get(coin);
  }
  const iso = (t) => new Date(t * 1000).toISOString().slice(0, 10);
  const isoH = (t) => new Date(t * 1000).toISOString().slice(0, 16).replace("T", " ");
  function longDate(s) { return new Date(s + "T00:00:00Z").toLocaleDateString("en-US", { timeZone: "UTC", month: "long", day: "numeric", year: "numeric" }); }

  // ---------------------------------------------------------------- formatting
  function decimalsOf(x) { if (x == null) return 0; const s = String(x); if (s.includes("e")) return 8; const i = s.indexOf("."); return i < 0 ? 0 : Math.min(8, s.length - i - 1); }
  function precisionFor(daily, trade) {
    let p = 2;
    for (const b of daily.slice(-60)) p = Math.max(p, decimalsOf(b[4]));
    if (trade) for (const k of ["level", "t1", "stop"]) p = Math.max(p, decimalsOf(trade[k]));
    return Math.min(p, 8);
  }
  function fmtPrice(x, p) { return x == null ? "-" : Number(x).toLocaleString("en-US", { minimumFractionDigits: p, maximumFractionDigits: p }); }
  function fmtPct(x) { if (x == null) return "n/a"; const s = x >= 0 ? "+" : ""; return s + x.toFixed(2) + "%"; }
  function fmtUsd(x) { if (x == null) return ""; const v = x / 100 * state.size; const s = v >= 0 ? "+" : "-"; return s + Math.abs(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " USD"; }
  const cls = (x) => x == null ? "flat" : x > 0 ? "pos" : x < 0 ? "neg" : "flat";
  function tradeRet(t) { return t[BOOK_RET[state.book]]; }

  // ---------------------------------------------------------------- trade geometry (from the row; verbatim from the reference page)
  function settle(t, book) {
    const b = book || state.book;
    const long = t.direction === "up";
    const fill = (ret) => ret == null ? null : t.level * (1 + (long ? 1 : -1) * ret / 100);
    const head = { book: "C", k: t.exit_k != null ? t.exit_k : t.days != null ? t.days : CAP, ret: t.ret_C, target: false,
      how: t.status === "exit" ? "daily-close exit" : t.status === "open" ? "marked at the 20-day cap" : "censored (data ends)" };
    head.price = t.status === "exit" || t.status === "open" ? fill(t.ret_C) : null;
    const ret = t[BOOK_RET[b]];
    if (b === "C" || ret == null || t[BOOK_DAYS[b]] == null) return head;
    const k = t[BOOK_DAYS[b]];
    let how, target = false;
    if (b === "A") { target = !!t.hit_A; how = target ? "all out at T1" : head.how; }
    else if (b === "B") { target = !!t.hit_B; how = target ? "all out at T2" : head.how; }
    else if (b === "D") { target = !!t.hit_D; how = target ? "one R" : head.how; }
    else if (b === "D5") { target = !!t.hit_D5; how = target ? "one R" : k === head.k && t.status === "exit" ? "daily-close exit" : "marked at the 5-bar horizon"; }
    else { target = t.out5 === "one_r"; how = t.out5 === "stop" ? "setup-bar stop" : target ? "one R" : t.out5 === "neither" ? "marked at bar 5" : "censored (data ends)"; }
    return { book: b, k, ret, target, how, price: fill(ret) };
  }
  function tradeSpan(t, book) {
    const i = state.dayIdx.get(t.date);
    if (i == null) return null;
    const end = Math.min(i + settle(t, book).k, state.daily.length - 1);
    return { i, end };
  }
  function stackLevels(t, i) {
    const long = t.direction === "up";
    const out = [];
    for (const tf of (t.stack || t.tf).split("+")) {
      let bar = null;
      if (tf === "D") { if (i - 1 >= 0) bar = { h: state.daily[i - 1][2], l: state.daily[i - 1][3] }; }
      else { const buckets = tf === "W" ? state.weeks : state.months; const bi = buckets.findIndex((b) => b.days.includes(i)); if (bi > 0) bar = buckets[bi - 1]; }
      if (bar) out.push({ tf, price: long ? bar.h : bar.l });
    }
    return out;
  }
  function setupDays(t, i) {
    const setup = new Set(), ref = new Set();
    if (t.tf === "D") { if (i - 1 >= 0) setup.add(i - 1); if (i - 2 >= 0) ref.add(i - 2); return { setup, ref }; }
    const buckets = t.tf === "W" ? state.weeks : state.months;
    const bi = buckets.findIndex((b) => b.days.includes(i));
    if (bi > 0) buckets[bi - 1].days.forEach((d) => setup.add(d));
    if (bi > 1) buckets[bi - 2].days.forEach((d) => ref.add(d));
    return { setup, ref };
  }

  // ---------------------------------------------------------------- the week's / month's bar type at entry (closed bars only)
  function barType(b, p) {
    // STRAT type of bar b against the bar before it, p (ruling R10: strict breaks; an equal high or low never breaks)
    const bh = b.h > p.h, bl = b.l < p.l;
    return bh && bl ? "3" : bh ? "2U" : bl ? "2D" : "1";
  }
  function htfType(cal, tf, i) {
    // the last CLOSED bar of that timeframe before the entry day i, typed against the complete bar before it;
    // the bar the entry sits in is still forming, so it is never typed here (closed bars only)
    const buckets = tf === "W" ? cal.weeks : cal.months;
    const bi = buckets.findIndex((b) => b.days.includes(i));
    if (bi < 2 || !buckets[bi - 1].complete || !buckets[bi - 2].complete) return { code: "?", title: "no two complete " + TF_LABEL[tf] + " bars before the entry (the data starts too late)" };
    const bar = buckets[bi - 1], prev = buckets[bi - 2];
    const code = barType(bar, prev);
    return { code, bar, prev, title: "last closed " + TF_LABEL[tf] + " bar (" + iso(bar.t) + " to " + iso(bar.end - DAY) + "): " + BT_WORD[code] +
      " against the " + TF_LABEL[tf] + " bar before it (high " + bar.h + " vs " + prev.h + ", low " + bar.l + " vs " + prev.l + ")" };
  }
  function btChip(tf, r) { return '<span class="chip bt ' + BT_CLASS[r.code] + '" title="' + r.title.replace(/"/g, "&quot;") + '">' + tf + " " + r.code + "</span>"; }

  // ---------------------------------------------------------------- chart (amCharts 5 StockChart)
  function makeChart() {
    if (!window.am5 || !window.am5xy || !window.am5stock || !window.am5themes_Dark) {
      $("empty").textContent = "amCharts 5 missing: vendor/amcharts5/{index,xy,stock}.js + themes/Dark.js (gitignored; see NOTES.md)"; return;
    }
    const root = am5.Root.new("chart");
    root.utc = true;                       // the census calendar is UTC: days roll 00:00, weeks start Monday 00:00
    root.locale.firstDayOfWeek = 1;
    root.setThemes([am5themes_Dark.new(root)]);
    root.numberFormatter.set("numberFormat", "#,###.00");
    root.dateFormatter.set("dateFormat", "yyyy-MM-dd");
    const stock = root.container.children.push(am5stock.StockChart.new(root, { paddingLeft: 0, paddingRight: 0, paddingTop: 0, paddingBottom: 0 }));
    const panel = stock.panels.push(am5stock.StockPanel.new(root, { wheelY: "zoomX", panX: true, panY: false, pinchZoomX: true, paddingLeft: 0, paddingTop: 6 }));
    const yAxis = panel.yAxes.push(am5xy.ValueAxis.new(root, {
      renderer: am5xy.AxisRendererY.new(root, { pan: "zoom", minGridDistance: 30 }), tooltip: am5.Tooltip.new(root, {}), extraTooltipPrecision: 0,
    }));
    const xAxis = panel.xAxes.push(am5xy.GaplessDateAxis.new(root, {
      baseInterval: INTERVAL["1D"],
      groupData: false,                    // NEVER aggregate on zoom: the bars are the census's bars, whatever the zoom level
      renderer: am5xy.AxisRendererX.new(root, { minGridDistance: 70, minorGridEnabled: false }), tooltip: am5.Tooltip.new(root, {}),
    }));
    xAxis.set("dateFormats", { minute: "HH:mm", hour: "HH:mm", day: "MMM d", week: "MMM d", month: "MMM yyyy", year: "yyyy" });
    xAxis.set("periodChangeDateFormats", { minute: "MMM d", hour: "MMM d", day: "MMM yyyy", week: "MMM yyyy", month: "yyyy", year: "yyyy" });
    xAxis.get("renderer").grid.template.setAll({ stroke: am5.color("#161a23"), strokeOpacity: 1 });
    yAxis.get("renderer").grid.template.setAll({ stroke: am5.color("#1b2030"), strokeOpacity: 1, strokeDasharray: [2, 3] });
    const candles = panel.series.push(am5xy.CandlestickSeries.new(root, {
      name: "candles", clustered: false, valueXField: "t", valueYField: "c", highValueYField: "h", lowValueYField: "l", openValueYField: "o",
      calculateAggregates: false, xAxis, yAxis,
      legendValueText: "open [bold]{openValueY}[/]  high [bold]{highValueY}[/]  low [bold]{lowValueY}[/]  close [bold]{valueY}[/]",
    }));
    candles.columns.template.setAll({ strokeWidth: 1 });
    // each bar carries its own colour (grey outside a trade, amber setup bar, green / red inside the trade), as the reference page does
    candles.columns.template.adapters.add("fill", (fill, target) => { const d = target.dataItem && target.dataItem.dataContext; return d && d.color ? am5.color(d.color) : fill; });
    candles.columns.template.adapters.add("stroke", (stroke, target) => { const d = target.dataItem && target.dataItem.dataContext; return d && d.wick ? am5.color(d.wick) : stroke; });
    stock.set("stockSeries", candles);
    const week = panel.series.push(am5xy.StepLineSeries.new(root, { name: "week open", xAxis, yAxis, valueXField: "t", valueYField: "v", noRisers: true, stroke: am5.color(COL.week) }));
    week.strokes.template.setAll({ strokeDasharray: [2, 3], strokeWidth: 1, strokeOpacity: 0.9 });
    const marks = panel.series.push(am5xy.LineSeries.new(root, { name: "markers", xAxis, yAxis, valueXField: "t", valueYField: "y" }));
    marks.strokes.template.set("forceHidden", true);
    marks.bullets.push((r, s, di) => {
      const d = di.dataContext, c = am5.color(d.color);
      let sp;
      if (d.shape === "arrowUp" || d.shape === "arrowDown") sp = am5.Triangle.new(r, { width: 12, height: 10, fill: c, rotation: d.shape === "arrowDown" ? 180 : 0, centerX: am5.p50, centerY: am5.p50 });
      else if (d.shape === "circle") sp = am5.Circle.new(r, { radius: 5, fill: c });
      else sp = am5.Rectangle.new(r, { width: 9, height: 9, fill: c, centerX: am5.p50, centerY: am5.p50 });
      sp.set("dy", d.above ? -9 : 9);
      return am5.Bullet.new(r, { sprite: sp });
    });
    marks.bullets.push((r, s, di) => {
      const d = di.dataContext;
      return am5.Bullet.new(r, { sprite: am5.Label.new(r, { text: d.text, fill: am5.color(d.color), fontSize: 11, centerX: am5.p50, centerY: am5.p50, dy: d.above ? -23 : 23, populateText: false }) });
    });
    const cursor = panel.set("cursor", am5xy.XYCursor.new(root, { xAxis, yAxis, behavior: "none" }));
    cursor.lineX.setAll({ stroke: am5.color("#8a90a2"), strokeDasharray: [3, 3] });
    cursor.lineY.setAll({ stroke: am5.color("#8a90a2"), strokeDasharray: [3, 3] });
    // the drawing toolbar and amCharts's own save / restore (DataSaveControl: Save, Restore, Clear, Auto-save, in browser storage)
    const drawing = am5stock.DrawingControl.new(root, { stockChart: stock });
    const save = am5stock.DataSaveControl.new(root, { stockChart: stock, storageId: "domino-proto" });
    const toolbar = am5stock.StockToolbar.new(root, { container: $("toolbar"), stockChart: stock, controls: [drawing, save, am5stock.SettingsControl.new(root, { stockChart: stock })] });
    stock.events.on("drawingsupdated", () => { if (state.am.ready && !state.am.busy) save.saveData(); });
    state.am = { root, stock, panel, xAxis, yAxis, candles, week, marks, drawing, save, toolbar, ranges: [], titles: [], ready: false, busy: false };
    panel.plotContainer.events.on("boundschanged", shiftTitles);
    root.events.on("frameended", shiftTitles);
    $("empty").style.display = "none";
  }

  function swapDrawings(coin) {
    // drawings are the owner's, per coin: park the current coin's, point the save control at the new coin's slot, restore
    const am = state.am; if (!am) return;
    am.busy = true;
    try { am.drawing.clearDrawings(); } catch (e) { /* nothing drawn yet */ }
    am.save.set("storageId", "domino-" + coin);
    try { am.save.restoreData(); } catch (e) { console.warn("restore failed", e); }
    setTimeout(() => { am.busy = false; if (!state.showMan) setDrawingsVisible(false); }, 500);
  }
  function setDrawingsVisible(on) {
    const am = state.am; if (!am) return;
    const ds = am.drawing.drawingSeries || {};
    for (const tool in ds) for (const s of ds[tool]) { if (on) s.show(0); else s.hide(0); }
  }

  function clearLines() {
    const am = state.am;
    for (const r of am.ranges) { am.yAxis.axisRanges.removeValue(r); if (!r.isDisposed()) r.dispose(); }
    am.ranges = []; am.titles = [];
  }
  function addLine(price, color, style, title, p) {
    // a system level: an axis range (grid line + price tag on the axis + a title tag inside the plot); not a drawing, so read-only
    const am = state.am;
    if (price == null || !state.showSys) return;
    const c = am5.color(color);
    const r = am.yAxis.createAxisRange(am.yAxis.makeDataItem({ value: price }));
    r.get("grid").setAll({ stroke: c, strokeOpacity: 0.9, strokeWidth: 1, strokeDasharray: DASH[style] || [], visible: true });
    r.get("label").setAll({ text: fmtPrice(price, p), fill: am5.color("#0f1117"), fontSize: 11, fontWeight: "600", paddingTop: 1, paddingBottom: 1, paddingLeft: 4, paddingRight: 4,
      background: am5.RoundedRectangle.new(am.root, { fill: c, cornerRadiusTL: 3, cornerRadiusTR: 3, cornerRadiusBL: 3, cornerRadiusBR: 3 }), visible: true });
    am.ranges.push(r);
    if (title) {
      // the title tag: a second range whose label the AXIS positions (inside the plot, on the line); only its
      // horizontal shift is ours -- to the plot's left edge, like the reference page (re-shifted on resize)
      const r2 = am.yAxis.createAxisRange(am.yAxis.makeDataItem({ value: price }));
      r2.get("grid").set("forceHidden", true);
      const lbl = r2.get("label");
      lbl.setAll({ text: title, inside: true, centerX: am5.p0, centerY: am5.p100, dx: 6 - plotWidth(), dy: -1, fill: am5.color("#0f1117"), fontSize: 11,
        paddingTop: 1, paddingBottom: 1, paddingLeft: 5, paddingRight: 5, visible: true,
        background: am5.RoundedRectangle.new(am.root, { fill: c, fillOpacity: 0.92, cornerRadiusTL: 3, cornerRadiusTR: 3, cornerRadiusBL: 3, cornerRadiusBR: 3 }) });
      am.ranges.push(r2); am.titles.push(lbl);
    }
  }
  function plotWidth() { const am = state.am; return am ? am.panel.plotContainer.width() : 0; }
  function shiftTitles() { const dx = 6 - plotWidth(); for (const l of state.am.titles) if (!l.isDisposed()) l.set("dx", dx); }
  function addBand(lo, hi, color, text) {
    // the gap band between the same-day triggers of a stack (translucent fill between the lowest and highest trigger)
    const am = state.am;
    if (lo == null || hi == null || lo === hi || !state.showSys) return;
    const c = am5.color(color);
    const r = am.yAxis.createAxisRange(am.yAxis.makeDataItem({ value: Math.min(lo, hi), endValue: Math.max(lo, hi) }));
    r.get("grid").set("forceHidden", true);
    r.get("axisFill").setAll({ fill: c, fillOpacity: 0.10, visible: true });
    r.get("label").setAll({ text: text, inside: true, fill: am5.color("#93c5fd"), fontSize: 10, visible: true, centerX: am5.p0, centerY: am5.p0, dx: 6 - plotWidth(), dy: 2 });
    am.ranges.push(r); am.titles.push(r.get("label"));
  }

  function bars() {
    if (state.chartTf === "1H") return state.hourly.map((b) => ({ t: b[0], o: b[1], h: b[2], l: b[3], c: b[4], days: [state.dayIdx.get(iso(b[0]))].filter((x) => x != null), hour: true }));
    if (state.chartTf === "1D") return state.daily.map((b, i) => ({ t: b[0], o: b[1], h: b[2], l: b[3], c: b[4], days: [i] }));
    return (state.chartTf === "1W" ? state.weeks : state.months).map((b) => ({ t: b.t, o: b.o, h: b.h, l: b.l, c: b.c, days: b.days, complete: b.complete }));
  }

  function draw() {
    const am = state.am;
    if (!am) return;
    syncHash();
    const t = state.cur;
    const span = t ? tradeSpan(t) : null;
    const sd = t && span ? setupDays(t, span.i) : null;
    const bs = bars();
    const p = precisionFor(state.daily, t);
    am.yAxis.set("numberFormat", p ? "#,###." + "0".repeat(p) : "#,###");
    am.xAxis.set("baseInterval", INTERVAL[state.chartTf]);
    am.xAxis.set("tooltipDateFormat", state.chartTf === "1H" ? "yyyy-MM-dd HH:mm" : "yyyy-MM-dd");
    const data = [];
    let firstIn = -1, lastIn = -1;
    bs.forEach((b, k) => {
      let role = "gray";
      if (span) {
        for (const d of b.days) {
          if (d >= span.i && d <= span.end) { role = "in"; break; }
          if (sd.setup.has(d)) role = "setup";
          else if (role === "gray" && sd.ref.has(d)) role = "ref";
        }
      }
      let color = COL.gray, wick = COL.grayWick;
      if (role === "in") { color = b.c >= b.o ? COL.up : COL.down; wick = color; if (firstIn < 0) firstIn = k; lastIn = k; }
      else if (role === "setup") { color = COL.setup; wick = color; }
      else if (role === "ref") { color = COL.ref; wick = color; }
      data.push({ t: b.t * MS, o: b.o, h: b.h, l: b.l, c: b.c, color, wick });
    });
    am.candles.data.setAll(data);
    if (state.chartTf === "1H" || state.chartTf === "1D") am.week.data.setAll(bs.map((b) => ({ t: b.t * MS, v: state.weekOpenAt(b.t) })).filter((x) => x.v != null));
    else am.week.data.setAll([]);
    clearLines();
    const markers = [];
    if (t && span && state.showSys) {
      const long = t.direction === "up";
      const st = settle(t);
      const hs = tradeSpan(t, "C");
      const levels = stackLevels(t, span.i);
      const domino = levels.length > 1 && CLS_LABEL[t.cls] && t.cls !== "spread";
      addLine(t.level, COL.level, 0, domino ? "Position opened: domino " + t.stack + " (" + CLS_LABEL[t.cls] + ")" : "Position opened (" + TF_LABEL[t.tf] + " trigger)", p);
      for (const l of levels) if (l.tf !== t.tf) addLine(l.price, COL.level, 2, TF_LABEL[l.tf] + " trigger, broke the same day", p);
      if (levels.length > 1) {
        const prices = levels.map((l) => l.price), lo = Math.min(...prices), hi = Math.max(...prices);
        addBand(lo, hi, COL.level, "gap " + ((hi - lo) / lo * 100).toFixed(2) + "% (" + (CLS_LABEL[t.cls] || t.cls) + ")");
      }
      if (st.price != null) addLine(st.price, COL.exit, 2, "Position closed: " + st.book + " " + st.how, p);
      addLine(t.t1, COL.target, 2, "T1 " + (t.t1_src || ""), p);
      addLine(t.t2, COL.target, 2, "T2 " + (t.t2_src || ""), p);
      addLine(t.t3, COL.target, 2, "T3 " + (t.t3_src || ""), p);
      if (t.stop != null && t.level != null) {
        const r = Math.abs(t.level - t.stop);
        addLine(long ? t.level + r : t.level - r, COL.oneR, 1, "one R", p);
        addLine(t.stop, COL.stop, 1, "setup-bar stop (chance book)", p);
      }
      if (t.mm_t1 != null) addLine(t.mm_t1, COL.mm, 4, "measured move", p);
      const barOfDay = (d, pick) => {
        const ks = []; bs.forEach((b, k) => { if (b.days.includes(d)) ks.push(k); });
        if (!ks.length) return null;
        if (!pick || ks.length === 1) return ks[0];
        return pick(ks);
      };
      const touchBar = (d, price, side) => barOfDay(d, (ks) => ks.find((k) => side === "hi" ? bs[k].h >= price : bs[k].l <= price) ?? ks[0]);
      const put = (k, text, above, color, shape) => { if (k != null) markers.push({ t: bs[k].t * MS, y: above ? bs[k].h : bs[k].l, above, text, color, shape }); };
      put(touchBar(span.i, t.level, long ? "hi" : "lo"), "in " + fmtPrice(t.level, p), !long, COL.level, long ? "arrowUp" : "arrowDown");
      const touches = [["t1_k", "T1", t.t1], ["t2_k", "T2", t.t2], ["t3_k", "T3", t.t3], ["one_r_k", "1R", t.stop != null ? (long ? t.level + Math.abs(t.level - t.stop) : t.level - Math.abs(t.level - t.stop)) : null], ["mm1_k", "MM", t.mm_t1]];
      for (const [key, label, price] of touches) {
        if (t[key] == null || price == null) continue;
        const d = span.i + t[key];
        if (d > span.end) continue;
        put(touchBar(d, price, long ? "hi" : "lo"), label, long, key === "one_r_k" ? COL.oneR : key === "mm1_k" ? COL.mm : COL.target, "circle");
      }
      if (t.stop_k != null && span.i + t.stop_k <= span.end) put(touchBar(span.i + t.stop_k, t.stop, long ? "lo" : "hi"), "stop", !long, COL.stop, "circle");
      if (st.price != null && st.target) put(touchBar(span.end, st.price, long ? "hi" : "lo"), "out " + fmtPrice(st.price, p) + " (" + st.how + ")", long, COL.exit, long ? "arrowDown" : "arrowUp");
      else if (st.price != null) put(barOfDay(span.end, (ks) => ks[ks.length - 1]), "out " + fmtPrice(st.price, p) + (st.book === "C" ? "" : " (" + st.how + ")"), long, COL.exit, long ? "arrowDown" : "arrowUp");
      else put(barOfDay(span.end, (ks) => ks[ks.length - 1]), "data ends", long, COL.stop, "square");
      if (st.book !== "C" && hs && hs.end !== span.end && t.status === "exit") put(barOfDay(hs.end, (ks) => ks[ks.length - 1]), "daily clock out", long, COL.stop, "square");
      if (t.status_u === "exit" && t.exit_k_u != null && t.exit_k_u !== t.exit_k) {
        const ku = Math.min(span.i + t.exit_k_u, state.daily.length - 1);
        put(barOfDay(ku, (ks) => ks[ks.length - 1]), "out: under water", long, COL.violet, "square");
      }
      if (state.chartTf === "1H" && t.status_h === "exit" && t.entry_h != null && t.exit_h != null) {
        const t0 = state.daily[span.i][0] + t.entry_h * HOUR + t.exit_h * HOUR;
        const kh = bs.findIndex((b) => b.t === t0);
        if (kh >= 0) put(kh, "out: hourly clock", long, COL.mm, "square");
      }
      markers.sort((a, b) => a.t - b.t);
    }
    am.marks.data.setAll(markers);
    // zoom to the trade (or the latest bars) once the new data is in; drawings keep their own timestamps across the swap
    let from, to;
    if (span && firstIn >= 0) { from = Math.max(0, firstIn - (state.chartTf === "1H" ? 48 : 40)); to = Math.min(bs.length - 1, lastIn + (state.chartTf === "1H" ? 24 : 15)); }
    else if (bs.length) { from = Math.max(0, bs.length - 160); to = bs.length - 1; }
    if (bs.length) {
      const step = bs.length > 1 ? (bs[1].t - bs[0].t) * MS : DAY * MS;
      am.candles.events.once("datavalidated", () => {
        am.xAxis.zoomToDates(new Date(bs[from].t * MS), new Date(bs[to].t * MS + step * 4));
        am.root.events.once("frameended", () => proofStep(t, span, bs));
      });
    }
    legend(t, span, bs.length);
    details(t, span, p);
  }

  function proofStep(t, span, bs) {
    const am = state.am, pf = state.proof;
    if (pf.seed && t && span) {
      pf.seed = false;
      setTimeout(() => {
        const k = bs.findIndex((b) => b.days.includes(span.i));
        const pt = (tMs, price) => {
          const x = am.xAxis.get("renderer").positionToCoordinate(am.xAxis.valueToPosition(tMs));
          const y = am.yAxis.get("renderer").positionToCoordinate(am.yAxis.valueToPosition(price));
          return am.panel.plotContainer.toGlobal({ x, y });
        };
        if (k >= 0 && t.stop != null) am.drawing.addLine("Horizontal Line", am.panel, pt(bs[k].t * MS, t.stop));
        if (k >= 0) am.drawing.addLine("Vertical Line", am.panel, pt(bs[k].t * MS, t.level));
        am.save.saveData();
        if (pf.then) setTimeout(() => switchTf(pf.then), 400);
        pf.then = null;
      }, 100);
    } else if (pf.then) {
      const v = pf.then; pf.then = null;
      setTimeout(() => switchTf(v), 400);
    }
  }
  function switchTf(v) {
    if (!INTERVAL[v]) return;
    state.chartTf = v;
    $("chartTf").querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.v === v));
    draw();
  }

  function legend(t, span, n) {
    const bits = ['<span><i style="background:' + COL.gray + '"></i>not in a trade</span>',
      '<span><i style="background:' + COL.setup + '"></i>setup bar</span>', '<span><i style="background:' + COL.ref + '"></i>bar before it</span>',
      '<span><i style="background:' + COL.up + '"></i><i style="background:' + COL.down + '"></i>in the trade</span>',
      '<span><i style="background:' + COL.week + '"></i>week open</span>'];
    if (state.chartTf === "1H" && !state.hourly.length) bits.push("<span style='color:#f59e0b'>no hourly bars cached for this coin: `trade_viewer hourly --as-of ... " + state.coin + "` then `build`</span>");
    else if (state.chartTf === "1H" && t && span && state.hourly.length && state.daily[span.i][0] < state.hourly[0][0]) bits.push("<span style='color:#f59e0b'>this trade predates the hourly window (the venue serves about 208 days)</span>");
    if (!n) bits.push("<span style='color:#f59e0b'>no bars</span>");
    if (!state.showSys) bits.push("<span style='color:#f59e0b'>system levels hidden</span>");
    if (!state.showMan) bits.push("<span style='color:#f59e0b'>your drawings hidden</span>");
    $("legend").innerHTML = bits.join("");
  }

  function details(t, span, p) {
    const el = $("trade");
    if (!t || !span) { el.innerHTML = '<span class="k">Pick a trade below (or press &rarr;).</span>'; return; }
    const long = t.direction === "up";
    const st = settle(t);
    const hs = tradeSpan(t, "C") || span;
    const endBar = state.daily[hs.end];
    const cal = state.cal.get(state.coin);
    const chips = ['<span class="chip ' + (long ? "long" : "short") + '">' + (long ? "LONG" : "SHORT") + "</span>",
      '<span class="chip tf">' + TF_LABEL[t.tf] + "</span>", '<span class="chip kind">' + KIND_LABEL[t.kind] + "</span>"];
    if (t.cls && t.cls !== "plain") chips.push('<span class="chip flag">' + t.cls + (t.stack && t.stack !== t.tf ? " " + t.stack : "") + "</span>");
    if (t.flag && t.flag !== "none") chips.push('<span class="chip flag">' + t.flag + "</span>");
    if (t.liquid) chips.push('<span class="chip tf">liquid</span>');
    const wt = htfType(cal, "W", span.i), mt = htfType(cal, "M", span.i);
    chips.push('<span class="k" style="margin-left:6px">closed bar at entry:</span> ' + btChip("W", wt) + " " + btChip("M", mt));
    const r = t.stop != null ? Math.abs(t.level - t.stop) : null;
    const oneR = r == null ? null : long ? t.level + r : t.level - r;
    const dayAt = (k) => k == null ? "" : " (day " + k + ", " + iso(state.daily[Math.min(span.i + k, state.daily.length - 1)][0]) + ")";
    const line2 = ['<span class="k">entry</span> ' + t.date + " at " + fmtPrice(t.level, p) + ' <span class="k">week at entry</span> ' + (t.w_support || "?"),
      '<span class="k">T1</span> ' + fmtPrice(t.t1, p) + (t.t1_src ? " [" + t.t1_src + "]" : "") + dayAt(t.t1_k),
      t.t2 != null ? '<span class="k">T2</span> ' + fmtPrice(t.t2, p) + " [" + t.t2_src + "]" + dayAt(t.t2_k) : "",
      t.t3 != null ? '<span class="k">T3</span> ' + fmtPrice(t.t3, p) + " [" + t.t3_src + "]" + dayAt(t.t3_k) : "",
      oneR != null ? '<span class="k">one R</span> ' + fmtPrice(oneR, p) + " (" + (t.r_pct != null ? t.r_pct.toFixed(2) + "% of price" : "") + ")" + dayAt(t.one_r_k) : "",
      t.stop != null ? '<span class="k">setup-bar stop</span> ' + fmtPrice(t.stop, p) + (t.stop_k != null ? dayAt(t.stop_k) : " (never hit inside the window)") : "",
      t.mm_t1 != null ? '<span class="k">measured move</span> ' + fmtPrice(t.mm_t1, p) + dayAt(t.mm1_k) : ""].filter(Boolean).join(" &middot; ");
    const levels = stackLevels(t, span.i);
    let stackTxt = "";
    if (levels.length > 1) {
      const prices = levels.map((l) => l.price), gap = (Math.max(...prices) - Math.min(...prices)) / Math.min(...prices) * 100;
      stackTxt = '<span class="k">stack</span> ' + t.stack + ": " + levels.map((l) => TF_LABEL[l.tf] + " trigger " + fmtPrice(l.price, p)).join(", ") +
        " &middot; gap " + gap.toFixed(2) + "% (" + (CLS_LABEL[t.cls] || t.cls) + ")";
    } else stackTxt = '<span class="k">stack</span> ' + TF_LABEL[t.tf] + " alone that day";
    const own = levels.find((l) => l.tf === t.tf);
    if (own && t.level != null && Math.abs(own.price - t.level) > Math.pow(10, -p) / 2) stackTxt += ' <span style="color:#f59e0b">row level ' + fmtPrice(t.level, p) + " differs from the chart's " + TF_LABEL[t.tf] + " level " + fmtPrice(own.price, p) + ": bug hypothesis</span>";
    stackTxt += ' &middot; <span class="k">last closed week</span> ' + BT_WORD[wt.code] + ' &middot; <span class="k">last closed month</span> ' + BT_WORD[mt.code];
    let exitTxt = '<span class="k">book ' + st.book + "</span> " + st.how + (st.price != null ? " on day " + st.k + " (" + iso(state.daily[span.end][0]) + ") at " + fmtPrice(st.price, p) + " <b class=\"" + cls(st.ret) + '">' + fmtPct(st.ret) + "</b>" : "") + " &middot; ";
    if (t.status === "exit") {
      const wo = state.weekOpenAt(endBar[0]);
      exitTxt += '<span class="k">daily clock</span> out day ' + (hs.end - hs.i) + " (" + iso(endBar[0]) + ") at the close " + fmtPrice(endBar[4], p) +
        ": day open " + fmtPrice(endBar[1], p) + " (" + (endBar[4] < endBar[1] ? "red" : endBar[4] > endBar[1] ? "green" : "flat") + ")" +
        ", week open " + fmtPrice(wo, p) + " (" + (wo == null ? "?" : endBar[4] < wo ? "red" : endBar[4] > wo ? "green" : "flat") + ")";
    } else if (t.status === "open") exitTxt += '<span class="k">daily clock</span> no exit inside the 20-day cap; marked at the day-20 close ' + fmtPrice(endBar[4], p);
    else exitTxt += '<span class="k">daily clock</span> censored (the data ends before the cap)';
    const alt = [];
    if (t.status_u === "exit" && t.exit_k_u != null) alt.push('<span class="k">under-water clock</span> day ' + t.exit_k_u + " " + fmtPct(t.ret_C_u));
    else if (t.status_u === "open") alt.push('<span class="k">under-water clock</span> open at the cap ' + fmtPct(t.ret_C_u));
    if (t.status_h === "exit" && t.exit_h != null) alt.push('<span class="k">hourly clock</span> in at hour ' + t.entry_h + ", out " + t.exit_h + "h later " + fmtPct(t.ret_C_h));
    else if (t.status_h === "open") alt.push('<span class="k">hourly clock</span> open at the cap ' + fmtPct(t.ret_C_h));
    if (alt.length) exitTxt += " &middot; " + alt.join(" &middot; ");
    const books = ["C", "A", "B", "D", "D5", "ref"].map((b) => {
      const v = t[BOOK_RET[b]];
      const hit = BOOK_HIT[b] ? (t[BOOK_HIT[b]] ? " target" : " exit") : b === "ref" ? " " + (t.out5 || "") : "";
      return '<span class="k">' + b + "</span> <b class=\"" + cls(v) + '">' + fmtPct(v) + "</b>" + '<span class="k">' + hit + "</span>";
    }).join(" &middot; ");
    const extra = '<span class="k">travel to the exit</span> +' + (t.mfe_x != null ? t.mfe_x.toFixed(2) : "?") + "% / -" + (t.mae_x != null ? t.mae_x.toFixed(2) : "?") + "%";
    el.innerHTML = chips.join(" ") + "<br>" + line2 + "<br>" + stackTxt + "<br>" + exitTxt + " &middot; " + extra + "<br>" + books;
  }

  // ---------------------------------------------------------------- lists, cards, filters
  function filtered(rows) {
    return rows.filter((t) => state.tf.has(t.tf) && state.kind.has(t.kind) && state.dir.has(t.direction) && (!state.liquid || t.liquid) && (!state.hasT1 || t.t1 != null));
  }
  function card(t, coin, k) {
    const v = tradeRet(t), long = t.direction === "up";
    const span = state.coin === coin ? tradeSpan(t) : null;
    const endTxt = span ? iso(state.daily[span.end][0]) + " &middot; " + (span.end - span.i) + "d" : "";
    const cal = state.cal.get(coin);
    const i = cal ? cal.dayIdx.get(t.date) : null;
    const bt = cal && i != null ? btChip("W", htfType(cal, "W", i)) + btChip("M", htfType(cal, "M", i)) : "";
    const el = document.createElement("div");
    el.className = "card" + (k === state.sel ? " sel" : "");
    el.innerHTML = '<div class="top"><span>' + coin + '</span><span class="chip ' + (long ? "long" : "short") + '">' + (long ? "Long" : "Short") + "</span></div>" +
      '<div class="when">' + t.date + (endTxt ? " &rarr; " + endTxt : "") + "</div>" +
      '<div class="what">' + TF_LABEL[t.tf] + " " + KIND_LABEL[t.kind] + (t.cls && t.cls !== "plain" ? " &middot; " + t.cls : "") + (t.flag && t.flag !== "none" ? " &middot; " + t.flag : "") + "</div>" +
      (bt ? '<div class="bt" title="the last CLOSED week / month before the entry, as a STRAT bar type">' + bt + "</div>" : "") +
      '<div class="pl ' + cls(v) + '">' + fmtPct(v) + ' <span style="font-size:12px;font-weight:500">' + fmtUsd(v) + "</span></div>" +
      '<div class="st">' + settle(t).how + "</div>";
    el.onclick = () => select(k, coin);
    return el;
  }
  function renderCards() {
    const box = $("cards"); box.innerHTML = "";
    const items = state.dateMode ? state.dateMode.items : state.list.map((t) => ({ coin: state.coin, t }));
    items.forEach((it, k) => box.appendChild(card(it.t, it.coin, k)));
    const sel = box.children[state.sel];
    if (sel) sel.scrollIntoView({ inline: "center", block: "nearest" });
    const n = items.length, rets = items.map((it) => tradeRet(it.t)).filter((x) => x != null);
    const avg = rets.length ? rets.reduce((a, b) => a + b, 0) / rets.length : null, green = rets.length ? rets.filter((x) => x > 0).length / rets.length * 100 : null;
    const sum = rets.reduce((a, b) => a + b, 0);
    $("summary").innerHTML = "<b>" + n + "</b> trades shown &middot; book " + state.book + ": avg <b class=\"" + cls(avg) + '">' + fmtPct(avg) + "</b> &middot; " +
      (green != null ? green.toFixed(0) + "% green" : "") + " &middot; equal size " + state.size + " USD each: <b class=\"" + cls(sum) + '">' + fmtUsd(sum) + "</b> over " + rets.length + " filled";
    $("cardsTitle").textContent = state.dateMode ? "every trade entered on " + longDate(state.dateMode.date) + " (all coins, filters applied)" : (state.coin || "") + " trades, oldest first";
  }

  async function loadCoin(coin) {
    const entry = state.index.coins.find((c) => c.coin === coin);
    if (!entry) return false;
    const res = await fetch("../data/" + entry.file);
    const d = await res.json();
    state.coin = coin; state.data = d; state.daily = d.daily; state.hourly = d.hourly;
    const cal = calendarFor(coin, d);
    state.dayIdx = cal.dayIdx; state.weeks = cal.weeks; state.months = cal.months; state.weekOpenAt = cal.weekOpenAt;
    state.list = filtered(d.trades);
    $("title").textContent = coin;
    $("meta").textContent = d.daily.length + " daily bars " + iso(d.daily[0][0]) + " to " + iso(d.daily[d.daily.length - 1][0]) + (d.hourly.length ? " · " + d.hourly.length + " hourly bars from " + isoH(d.hourly[0][0]) : " · no hourly bars cached") + " · " + d.trades.length + " trades · as of " + d.as_of;
    $("chartTf").querySelector('[data-v="1H"]').disabled = !d.hourly.length;
    swapDrawings(coin);
    return true;
  }

  async function select(k, coin) {
    if (state.dateMode) {
      const it = state.dateMode.items[k];
      if (!it) return;
      if (state.coin !== it.coin) await loadCoin(it.coin);
      state.sel = k; state.cur = it.t;
      draw(); renderCards();
      return;
    }
    state.sel = k; state.cur = state.list[k] || null; draw(); renderCards();
  }
  function syncHash() {
    // the same bookmarkable address as the reference page: #coin=BTC&date=2025-06-17&tf=D&dir=down&view=1D&book=C
    const t = state.cur;
    const h = t ? "coin=" + encodeURIComponent(state.coin) + "&date=" + t.date + "&tf=" + t.tf + "&dir=" + t.direction + "&view=" + state.chartTf + "&book=" + state.book : state.coin ? "coin=" + encodeURIComponent(state.coin) + "&view=" + state.chartTf : "";
    history.replaceState(null, "", h ? "#" + h : location.pathname);
  }
  function fromHash() {
    const q = new URLSearchParams(location.hash.slice(1));
    return { coin: q.get("coin"), date: q.get("date"), tf: q.get("tf"), dir: q.get("dir"), view: q.get("view"), book: q.get("book"), seed: q.get("seed"), then: q.get("then"), show: q.get("show") };
  }
  function lastSettled(list) { for (let k = list.length - 1; k >= 0; k--) if (list[k].status === "exit") return k; return list.length - 1; }

  function refilter() {
    if (state.dateMode) { applyDate(state.dateMode.date); return; }
    if (!state.data) return;
    state.list = filtered(state.data.trades);
    state.sel = state.cur ? state.list.indexOf(state.cur) : -1;
    if (state.sel < 0) state.cur = null;
    draw(); renderCards();
  }

  async function applyDate(date) {
    if (!state.dates) state.dates = await (await fetch("../data/dates.json")).json();
    const rows = state.dates[date] || [];
    const items = [];
    for (const r of rows) {
      const [coin, direction, tf, kind] = r;
      if (!state.tf.has(tf) || !state.kind.has(kind) || !state.dir.has(direction)) continue;
      items.push({ coin, key: [date, tf, direction] });
    }
    const byCoin = new Map();
    for (const it of items) { if (!byCoin.has(it.coin)) byCoin.set(it.coin, fetch("../data/" + state.index.coins.find((c) => c.coin === it.coin).file).then((r) => r.json())); }
    const full = [];
    for (const it of items) {
      const d = await byCoin.get(it.coin);
      calendarFor(it.coin, d);
      const t = d.trades.find((x) => x.date === date && x.tf === it.key[1] && x.direction === it.key[2]);
      if (t && (!state.liquid || t.liquid) && (!state.hasT1 || t.t1 != null)) full.push({ coin: it.coin, t });
    }
    state.dateMode = { date, items: full };
    state.sel = -1; state.cur = null; state.list = [];
    $("title").textContent = longDate(date); $("meta").textContent = full.length + " trades entered that day";
    if (full.length) await select(0, full[0].coin); else { draw(); renderCards(); }
  }

  // ---------------------------------------------------------------- wiring
  function seg(id, onPick, multi) {
    const el = $(id);
    el.querySelectorAll("button").forEach((b) => b.onclick = () => {
      if (multi) b.classList.toggle("on"); else { el.querySelectorAll("button").forEach((x) => x.classList.remove("on")); b.classList.add("on"); }
      onPick(b.dataset.v, b.classList.contains("on"));
    });
  }
  function setOf(id) { return new Set([...$(id).querySelectorAll("button.on")].map((b) => b.dataset.v)); }

  async function init() {
    makeChart();
    state.index = await (await fetch("../data/index.json")).json();
    const dl = $("coinList");
    for (const c of state.index.coins) { const o = document.createElement("option"); o.value = c.coin; o.label = c.n + " trades"; dl.appendChild(o); }
    $("meta").textContent = state.index.coins.length + " coins · " + state.index.trades.toLocaleString() + " trades · as of " + state.index.as_of + " · built " + state.index.built;
    seg("chartTf", (v) => { state.chartTf = v; draw(); }, false);
    seg("fTf", () => { state.tf = setOf("fTf"); refilter(); }, true);
    seg("fKind", () => { state.kind = setOf("fKind"); refilter(); }, true);
    seg("fDir", () => { state.dir = setOf("fDir"); refilter(); }, true);
    seg("fLiq", (v, on) => { state.liquid = on; refilter(); }, true);
    seg("fT1", (v, on) => { state.hasT1 = on; refilter(); }, true);
    seg("fShow", (v, on) => { if (v === "sys") { state.showSys = on; draw(); } else { state.showMan = on; setDrawingsVisible(on); legend(state.cur, state.cur ? tradeSpan(state.cur) : null, bars().length); } }, true);
    $("book").onchange = (e) => { state.book = e.target.value; draw(); renderCards(); };
    $("size").onchange = (e) => { state.size = Number(e.target.value) || 1000; renderCards(); };
    $("coinBox").onchange = async (e) => {
      const v = e.target.value.trim();
      if (!v) return;
      state.dateMode = null; $("dateBox").value = "";
      if (await loadCoin(v)) { state.sel = lastSettled(state.list); state.cur = state.list[state.sel] || null; draw(); renderCards(); }
      else $("meta").textContent = "no such coin in the viewer data: " + v;
    };
    $("dateBox").onchange = (e) => { if (e.target.value) applyDate(e.target.value); };
    document.addEventListener("keydown", (e) => {
      if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
      const n = state.dateMode ? state.dateMode.items.length : state.list.length;
      if (e.key === "ArrowRight" && state.sel < n - 1) { select(state.sel + 1, state.dateMode ? state.dateMode.items[state.sel + 1].coin : state.coin); e.preventDefault(); }
      else if (e.key === "ArrowLeft" && state.sel > 0) { select(state.sel - 1, state.dateMode ? state.dateMode.items[state.sel - 1].coin : state.coin); e.preventDefault(); }
      else if (e.key === "Escape") { state.sel = -1; state.cur = null; draw(); renderCards(); }
    });
    const want = fromHash();
    state.proof.seed = want.seed === "1"; state.proof.then = INTERVAL[want.then] ? want.then : null;
    if (want.show === "sys" || want.show === "man" || want.show === "none") {
      // &show= in the address: sys (rows only), man (your drawings only), none -- the same two toggles, preset on load
      state.showSys = want.show === "sys"; state.showMan = want.show === "man";
      $("fShow").querySelector('[data-v="sys"]').classList.toggle("on", state.showSys);
      $("fShow").querySelector('[data-v="man"]').classList.toggle("on", state.showMan);
    }
    if (want.book && BOOK_RET[want.book]) { state.book = want.book; $("book").value = want.book; }
    const first = state.index.coins.find((c) => c.coin === (want.coin || "BTC")) || state.index.coins[0];
    $("coinBox").value = first.coin;
    await loadCoin(first.coin);
    if (want.view && INTERVAL[want.view]) {
      state.chartTf = want.view;
      $("chartTf").querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.v === want.view));
    }
    state.sel = want.date ? state.list.findIndex((t) => t.date === want.date && (!want.tf || t.tf === want.tf) && (!want.dir || t.direction === want.dir)) : -1;
    if (state.sel < 0) state.sel = lastSettled(state.list);
    state.cur = state.list[state.sel] || null;
    if (state.am) state.am.ready = true;
    draw(); renderCards();
  }
  init().catch((e) => { $("empty").style.display = "flex"; $("empty").textContent = "failed to load: " + e; console.error(e); });
})();
