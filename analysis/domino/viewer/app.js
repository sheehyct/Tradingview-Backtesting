/* app.js: the Domino trade viewer (TVB-40, amCharts 5). Reads the per-coin JSON that `trade_viewer
   build` writes (data/<coin>.json) and draws each row off the row (core.js carries the TVB-39
   logic; no trade logic is re-run): the layout (calendar + trade table on the left, one or two
   stock panes in the centre, the trade in plain words on the right), the Compare tab across the
   six books (this coin, this day, or the universe from data/universe.json), the Playbook, the
   drawing toolbar with the library's own save / restore keyed per coin and pane, and the magnet
   ray on top of it. */
(function (DV) {
  "use strict";
  const C = DV.core, S = DV.story, ST = DV.stats;
  const { $, DAY, HOUR, MS, COL, BOOKS, BOOK_RET, BOOK_NAME, BOOK_COL, CLS_LABEL, KIND_LABEL, KIND_SHORT, TF_LABEL, DASH, INTERVAL, iso, isoH, longDate, monthName, precisionFor,
    fmtPrice, fmtPct, fmtUsd, fmtUsd0, cls, esc, settle, tradeSpan, stackLevels, setupDays, oneR, htfType, btChip, makeCalendar, weekStart, nextMonth, stackWords, cellIndex } = C;

  const state = {
    index: null, dates: null, coin: null, data: null, cal: null, cals: new Map(),
    tf: new Set(["D", "W", "M"]), kind: new Set(["reversal", "continuation", "inside", "outside"]), dir: new Set(["up", "down"]),
    liquid: false, hasT1: false, book: "C", size: 1000,
    items: [], sel: -1, cur: null, dateMode: null, sort: "date-desc",
    layout: "single", tab: "trade", showSys: true, showMan: true,
    calScope: "coin", calY: null, calM: null,
    panes: {}, cmp: null, cmpDirty: true, cmpScope: "shown", playbookDone: false, hover: "a",
    uni: null, uniItems: null,
    proof: { seed: false, then: null, ray: null },
  };
  const tradeRet = (t) => t[BOOK_RET[state.book]];
  const n2 = (x) => x == null ? "?" : Number(x).toFixed(2);
  const RAY = "#60a5fa";

  // ---------------------------------------------------------------- chart panes (amCharts 5 StockChart)
  function makePane(key) {
    const el = $("pane-" + key), chartEl = el.querySelector(".paneChart"), tools = el.querySelector(".paneTools");
    const empty = chartEl.querySelector(".empty");
    if (!window.am5 || !window.am5xy || !window.am5stock || !window.am5themes_Dark) {
      if (empty) empty.textContent = "amCharts 5 missing: vendor/amcharts5/{index,xy,stock}.js + themes/Dark.js (gitignored; see NOTES.md)";
      return null;
    }
    if (empty) empty.style.display = "none";
    const root = am5.Root.new(chartEl);
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
      // markers that land on the same or a neighbouring bar stack outward (slot 0, 1, 2 ...) instead of printing over each other
      sp.set("dy", (d.above ? -1 : 1) * (9 + (d.slot || 0) * 14));
      return am5.Bullet.new(r, { sprite: sp });
    });
    marks.bullets.push((r, s, di) => {
      const d = di.dataContext;
      return am5.Bullet.new(r, { sprite: am5.Label.new(r, { text: d.text, fill: am5.color(d.color), fontSize: 11, centerX: am5.p50, centerY: am5.p50, dy: (d.above ? -1 : 1) * (23 + (d.slot || 0) * 14), populateText: false }) });
    });
    const cursor = panel.set("cursor", am5xy.XYCursor.new(root, { xAxis, yAxis, behavior: "none" }));
    cursor.lineX.setAll({ stroke: am5.color("#8a90a2"), strokeDasharray: [3, 3] });
    cursor.lineY.setAll({ stroke: am5.color("#8a90a2"), strokeDasharray: [3, 3] });
    // the drawing toolbar and amCharts's own save / restore (DataSaveControl: Save, Restore, Clear, Auto-save, in browser storage)
    const drawing = am5stock.DrawingControl.new(root, { stockChart: stock });
    const save = am5stock.DataSaveControl.new(root, { stockChart: stock, storageId: "domino-proto-" + key });
    am5stock.StockToolbar.new(root, { container: tools, stockChart: stock, controls: [drawing, save, am5stock.SettingsControl.new(root, { stockChart: stock })] });
    const pane = { key, el, chartEl, root, stock, panel, xAxis, yAxis, candles, week, marks, drawing, save, ranges: [], titles: [], bands: [], ready: false, busy: false,
      tf: key === "a" ? "1D" : "1W", note: el.querySelector(".paneNote"), seg: el.querySelector(".seg[data-pane]"), magnet: false, noteText: "" };
    stock.events.on("drawingsupdated", () => { if (pane.ready && !pane.busy) save.saveData(); });
    panel.plotContainer.events.on("boundschanged", () => shiftTitles(pane));
    root.events.on("frameended", () => shiftTitles(pane));
    panel.plotContainer.events.on("click", (ev) => { if (pane.magnet && ev.point) magnetDrop(pane, panel.plotContainer.toLocal(ev.point)); });
    pane.seg.querySelectorAll("button").forEach((b) => { b.onclick = () => setPaneTf(key, b.dataset.v); });
    el.querySelector(".magnet").onclick = () => setMagnet(pane, !pane.magnet);
    el.onmouseenter = () => { state.hover = key; };
    return pane;
  }
  function setMagnet(pane, on) {
    pane.magnet = on;
    pane.el.querySelector(".magnet").classList.toggle("on", on);
    pane.chartEl.classList.toggle("magnet", on);
    if (on) { try { pane.drawing.set("active", false); } catch (e) { /* no tool was active */ } }
    paneNote(pane);
  }
  function paneNote(pane, text) {
    if (text != null) pane.noteText = text;
    pane.note.textContent = (pane.magnet ? "magnet ray: click near a bar's open / high / low / close (R or Esc leaves)" : "") + (pane.magnet && pane.noteText ? "  |  " : "") + pane.noteText;
  }
  function magnetDrop(pane, local) {
    // the magnet ray: the nearest open / high / low / close of the bar under the pointer, on this pane's own bars, dropped as the
    // library's Horizontal Line at exactly that price, so it saves, moves and erases with every other drawing in the coin's slot
    const bs = bars(pane);
    if (!bs.length) return null;
    const xr = pane.xAxis.get("renderer"), yr = pane.yAxis.get("renderer");
    // pixel to axis position: the renderer's own inverse where the build has one, else the start / end formula the renderer uses
    const posOf = (axis, r, coord) => typeof r.coordinateToPosition === "function" ? r.coordinateToPosition(coord) : axis.toAxisPosition(coord / r.axisLength());
    const tMs = pane.xAxis.positionToValue(posOf(pane.xAxis, xr, local.x));
    const b = bs[cellIndex(bs, tMs)];
    const yOf = (price) => yr.positionToCoordinate(pane.yAxis.valueToPosition(price));
    let price = b.c, dist = Infinity;
    for (const v of [b.o, b.h, b.l, b.c]) { const d = Math.abs(yOf(v) - local.y); if (d < dist) { dist = d; price = v; } }
    const g = pane.panel.plotContainer.toGlobal({ x: xr.positionToCoordinate(pane.xAxis.valueToPosition(b.t * MS)), y: yOf(price) });
    const prev = { strokeColor: pane.drawing.get("strokeColor"), strokeWidth: pane.drawing.get("strokeWidth") };
    pane.drawing.setAll({ strokeColor: am5.color(RAY), strokeWidth: 1 });
    try { pane.drawing.addLine("Horizontal Line", pane.panel, g); } finally { pane.drawing.setAll(prev); }
    pane.save.saveData();
    return price;
  }
  function setPaneTf(key, v) {
    const pane = state.panes[key];
    if (!pane || !INTERVAL[v]) return;
    pane.tf = v;
    pane.seg.querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.v === v));
    syncHash();
    drawPane(pane);
    legend();
  }
  function visiblePanes() { return Object.values(state.panes).filter((p) => p && !p.el.hidden); }
  function setLayout(v) {
    state.layout = v;
    $("layout").querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.v === v));
    const dual = v === "dual";
    $("pane-b").hidden = !dual;
    if (dual && !state.panes.b) {
      state.panes.b = makePane("b");
      if (state.panes.b) { state.panes.b.ready = true; if (state.coin) swapDrawings(state.panes.b, state.coin); }
    }
    for (const p of visiblePanes()) p.root.resize();
    syncHash();
    if (dual && state.panes.b) drawPane(state.panes.b);
    legend();
  }

  function swapDrawings(pane, coin) {
    // drawings are the owner's, per coin and per pane: park the current set, point the save control at the new slot, restore
    pane.busy = true;
    try { pane.drawing.clearDrawings(); } catch (e) { /* nothing drawn yet */ }
    pane.save.set("storageId", "domino-" + coin + (pane.key === "a" ? "" : "-" + pane.key));
    try { pane.save.restoreData(); } catch (e) { console.warn("restore failed", e); }
    setTimeout(() => { pane.busy = false; if (!state.showMan) setDrawingsVisible(pane, false); }, 500);
  }
  function setDrawingsVisible(pane, on) {
    const ds = pane.drawing.drawingSeries || {};
    for (const tool in ds) for (const s of ds[tool]) { if (on) s.show(0); else s.hide(0); }
  }

  function clearLines(pane) {
    for (const r of pane.ranges) { pane.yAxis.axisRanges.removeValue(r); if (!r.isDisposed()) r.dispose(); }
    pane.ranges = []; pane.titles = []; pane.bands = [];
  }
  function addLine(pane, price, color, style, title, p) {
    // a system level: an axis range (grid line + price tag on the axis + a title tag inside the plot); not a drawing, so read-only
    if (price == null || !state.showSys) return;
    const c = am5.color(color);
    const r = pane.yAxis.createAxisRange(pane.yAxis.makeDataItem({ value: price }));
    r.get("grid").setAll({ stroke: c, strokeOpacity: 0.9, strokeWidth: 1, strokeDasharray: DASH[style] || [], visible: true });
    r.get("label").setAll({ text: fmtPrice(price, p), fill: am5.color("#0f1117"), fontSize: 11, fontWeight: "600", paddingTop: 1, paddingBottom: 1, paddingLeft: 4, paddingRight: 4,
      background: am5.RoundedRectangle.new(pane.root, { fill: c, cornerRadiusTL: 3, cornerRadiusTR: 3, cornerRadiusBL: 3, cornerRadiusBR: 3 }), visible: true });
    pane.ranges.push(r);
    if (title) {
      // the title tag: a second range whose label the AXIS positions (inside the plot, on the line); the horizontal shift to the
      // plot's left edge and the vertical stacking of tags that would overlap are ours (shiftTitles, every frame)
      const r2 = pane.yAxis.createAxisRange(pane.yAxis.makeDataItem({ value: price }));
      r2.get("grid").set("forceHidden", true);
      const lbl = r2.get("label");
      lbl.setAll({ text: title, inside: true, centerX: am5.p0, centerY: am5.p100, dx: 6 - plotWidth(pane), dy: -1, fill: am5.color("#0f1117"), fontSize: 11,
        paddingTop: 1, paddingBottom: 1, paddingLeft: 5, paddingRight: 5, visible: true,
        background: am5.RoundedRectangle.new(pane.root, { fill: c, fillOpacity: 0.92, cornerRadiusTL: 3, cornerRadiusTR: 3, cornerRadiusBL: 3, cornerRadiusBR: 3 }) });
      pane.ranges.push(r2); pane.titles.push(lbl);
    }
  }
  function plotWidth(pane) { return pane.panel.plotContainer.width(); }
  function shiftTitles(pane) {
    const dx = 6 - plotWidth(pane);
    const rend = pane.yAxis.get("renderer");
    for (const b of pane.bands) {
      if (b.label.isDisposed()) continue;
      // the gap band's label only prints when the band is tall enough to hold it (a thin band keeps its fill and its lines)
      const h = Math.abs(rend.positionToCoordinate(pane.yAxis.valueToPosition(b.hi)) - rend.positionToCoordinate(pane.yAxis.valueToPosition(b.lo)));
      b.label.setAll({ dx, forceHidden: h < 16 });
    }
    // stack the title tags: each sits with its bottom edge on its line; walking up from the lowest one on screen, a tag whose
    // bottom would land on the tag below it is lifted so the two read as a stack instead of one blur
    const H = 17;
    const ls = pane.titles.filter((l) => !l.isDisposed()).map((l) => ({ l, y: l.y() })).sort((a, b) => b.y - a.y);
    let floor = Infinity;
    for (const it of ls) {
      let dy = -1;
      if (it.y + dy > floor) dy = floor - it.y;
      it.l.setAll({ dx, dy });
      floor = it.y + dy - H;
    }
  }
  function addBand(pane, lo, hi, color, text) {
    // the gap band between the same-day triggers of a stack (translucent fill between the lowest and highest trigger)
    if (lo == null || hi == null || lo === hi || !state.showSys) return;
    const c = am5.color(color);
    const r = pane.yAxis.createAxisRange(pane.yAxis.makeDataItem({ value: Math.min(lo, hi), endValue: Math.max(lo, hi) }));
    r.get("grid").set("forceHidden", true);
    r.get("axisFill").setAll({ fill: c, fillOpacity: 0.10, visible: true });
    r.get("label").setAll({ text: text, inside: true, fill: am5.color("#93c5fd"), fontSize: 10, visible: true, centerX: am5.p0, centerY: am5.p0, dx: 6 - plotWidth(pane), dy: 2 });
    pane.ranges.push(r); pane.bands.push({ label: r.get("label"), lo: Math.min(lo, hi), hi: Math.max(lo, hi) });
  }

  function bars(pane) {
    const cal = state.cal;
    if (pane.tf === "1H") return cal.hourly.map((b) => ({ t: b[0], o: b[1], h: b[2], l: b[3], c: b[4], days: [cal.dayIdx.get(iso(b[0]))].filter((x) => x != null), hour: true }));
    if (pane.tf === "1D") return cal.daily.map((b, i) => ({ t: b[0], o: b[1], h: b[2], l: b[3], c: b[4], days: [i] }));
    return (pane.tf === "1W" ? cal.weeks : cal.months).map((b) => ({ t: b.t, o: b.o, h: b.h, l: b.l, c: b.c, days: b.days, complete: b.complete }));
  }

  function drawPane(pane) {
    if (!pane || pane.el.hidden || !state.cal) return;
    const cal = state.cal, t = state.cur;
    const span = t ? tradeSpan(t, state.book, cal) : null;
    const sd = t && span ? setupDays(t, span.i, cal) : null;
    const bs = bars(pane);
    const p = precisionFor(cal.daily, t);
    pane.yAxis.set("numberFormat", p ? "#,###." + "0".repeat(p) : "#,###");
    pane.xAxis.set("baseInterval", INTERVAL[pane.tf]);
    pane.xAxis.set("tooltipDateFormat", pane.tf === "1H" ? "yyyy-MM-dd HH:mm" : "yyyy-MM-dd");
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
    pane.candles.data.setAll(data);
    if (pane.tf === "1H" || pane.tf === "1D") pane.week.data.setAll(bs.map((b) => ({ t: b.t * MS, v: cal.weekOpenAt(b.t) })).filter((x) => x.v != null));
    else pane.week.data.setAll([]);
    clearLines(pane);
    const markers = [];
    if (t && span && state.showSys) {
      const long = t.direction === "up";
      const st = settle(t, state.book);
      const hs = tradeSpan(t, "C", cal);
      const levels = stackLevels(t, span.i, cal);
      const sw = stackWords(t, levels);
      const domino = sw.conv.length > 1 && t.cls !== "spread";
      addLine(pane, t.level, COL.level, 0, domino ? "Position opened: domino " + sw.conv.map((l) => l.tf).join("+") + " (" + (CLS_LABEL[t.cls] || t.cls) + ")" : "Position opened (" + TF_LABEL[t.tf] + " trigger)", p);
      for (const l of sw.conv) if (l.tf !== t.tf) addLine(pane, l.price, COL.level, 2, TF_LABEL[l.tf] + " trigger, broke the same day", p);
      for (const l of sw.far) addLine(pane, l.price, COL.level, 2, TF_LABEL[l.tf] + " trigger, broke the same day, " + (l.gap >= 0 ? "+" : "") + l.gap.toFixed(2) + "% beyond the entry (not part of the converged stack)", p);
      if (sw.conv.length > 1) {
        const prices = sw.conv.map((l) => l.price), lo = Math.min(...prices), hi = Math.max(...prices);
        addBand(pane, lo, hi, COL.level, "gap " + ((hi - lo) / lo * 100).toFixed(2) + "% (" + (CLS_LABEL[t.cls] || t.cls) + ")");
      }
      if (st.price != null) addLine(pane, st.price, COL.exit, 2, "Position closed: " + st.book + " " + st.how, p);
      addLine(pane, t.t1, COL.target, 2, "T1 " + (t.t1_src || ""), p);
      addLine(pane, t.t2, COL.target, 2, "T2 " + (t.t2_src || ""), p);
      addLine(pane, t.t3, COL.target, 2, "T3 " + (t.t3_src || ""), p);
      if (t.stop != null && t.level != null) {
        addLine(pane, oneR(t), COL.oneR, 1, "one R", p);
        addLine(pane, t.stop, COL.stop, 1, "setup-bar stop (chance book)", p);
      }
      if (t.mm_t1 != null) addLine(pane, t.mm_t1, COL.mm, 4, "measured move", p);
      const barOfDay = (d, pick) => {
        const ks = []; bs.forEach((b, k) => { if (b.days.includes(d)) ks.push(k); });
        if (!ks.length) return null;
        if (!pick || ks.length === 1) return ks[0];
        return pick(ks);
      };
      // a touch is the RECORDED price (level, target, one R, stop as the engine wrote it) against the bar's own high / low,
      // with a one-part-in-a-billion tolerance for the cached bars' float; the fill reconstructed from the return is never a
      // touch threshold (TVB-39 audit F4). When no bar of the day reaches the price, the marker sits on the day's last bar
      // and says so instead of the day's first bar.
      const near = (a, b) => Math.abs(a - b) <= Math.abs(b) * 1e-9;
      const lastBar = (d) => barOfDay(d, (ks) => ks[ks.length - 1]);
      const touchBar = (d, price, side) => barOfDay(d, (ks) => ks.find((k) => side === "hi" ? bs[k].h >= price || near(bs[k].h, price) : bs[k].l <= price || near(bs[k].l, price)));
      const put = (k, text, above, color, shape) => { if (k != null) markers.push({ t: bs[k].t * MS, y: above ? bs[k].h : bs[k].l, above, text, color, shape }); };
      const putTouch = (d, price, side, text, above, color, shape) => { const k = touchBar(d, price, side); if (k != null) put(k, text, above, color, shape); else put(lastBar(d), text + " (no bar of the day reaches the price)", above, color, shape); };
      putTouch(span.i, t.level, long ? "hi" : "lo", "in " + fmtPrice(t.level, p), !long, COL.level, long ? "arrowUp" : "arrowDown");
      const touches = [["t1_k", "T1", t.t1], ["t2_k", "T2", t.t2], ["t3_k", "T3", t.t3], ["one_r_k", "1R", oneR(t)], ["mm1_k", "MM", t.mm_t1]];
      for (const [key, label, price] of touches) {
        if (t[key] == null || price == null) continue;
        const d = span.i + t[key];
        if (d > span.end) continue;
        putTouch(d, price, long ? "hi" : "lo", label, long, key === "one_r_k" ? COL.oneR : key === "mm1_k" ? COL.mm : COL.target, "circle");
      }
      if (t.stop_k != null && span.i + t.stop_k <= span.end) putTouch(span.i + t.stop_k, t.stop, long ? "lo" : "hi", "stop", !long, COL.stop, "circle");
      const outText = "out " + fmtPrice(st.price, p) + (st.book === "C" ? "" : " (" + st.how + ")");
      if (st.price != null && st.target && st.at != null) putTouch(span.end, st.at, long ? "hi" : "lo", outText, long, COL.exit, long ? "arrowDown" : "arrowUp");
      else if (st.price != null && st.stop && st.at != null) putTouch(span.end, st.at, long ? "lo" : "hi", outText + (st.k === 0 ? "; entry day: the daily bar does not order the entry and the stop, the engine takes the stop first" : ""), long, COL.exit, long ? "arrowDown" : "arrowUp");
      else if (st.price != null) put(lastBar(span.end), outText, long, COL.exit, long ? "arrowDown" : "arrowUp");
      else if (st.missing && st.book !== "C") put(lastBar(span.end), "data ends: book " + st.book + " has " + st.how, long, COL.stop, "square");
      else put(lastBar(span.end), "data ends", long, COL.stop, "square");
      if (st.book !== "C" && hs && hs.end !== span.end && t.status === "exit") put(barOfDay(hs.end, (ks) => ks[ks.length - 1]), "daily clock out", long, COL.stop, "square");
      if (t.status_u === "exit" && t.exit_k_u != null && t.exit_k_u !== t.exit_k) {
        const ku = Math.min(span.i + t.exit_k_u, cal.daily.length - 1);
        put(barOfDay(ku, (ks) => ks[ks.length - 1]), "out: under water", long, COL.violet, "square");
      }
      if (pane.tf === "1H" && t.status_h === "exit" && t.entry_h != null && t.exit_h != null) {
        const t0 = cal.daily[span.i][0] + t.entry_h * HOUR + t.exit_h * HOUR;
        const kh = bs.findIndex((b) => b.t === t0);
        if (kh >= 0) put(kh, "out: hourly clock", long, COL.mm, "square");
      }
      markers.sort((a, b) => a.t - b.t);
      // collision slots: a marker within a bar and a half of the previous one on the same side stacks one step further out
      const stepT = bs.length > 1 ? (bs[1].t - bs[0].t) * MS : DAY * MS;
      const lastOn = { above: null, below: null };
      for (const m of markers) {
        const side = m.above ? "above" : "below", prev = lastOn[side];
        m.slot = prev && m.t - prev.t <= stepT * 1.5 ? prev.slot + 1 : 0;
        lastOn[side] = m;
      }
    }
    pane.marks.data.setAll(markers);
    // zoom to the trade (or the latest bars) once the new data is in; drawings keep their own timestamps across the swap
    let from, to;
    const PAD = { "1H": [48, 24], "1D": [40, 15], "1W": [20, 8], "1M": [10, 4] };
    if (span && firstIn >= 0) { const [pb, pa] = PAD[pane.tf]; from = Math.max(0, firstIn - pb); to = Math.min(bs.length - 1, lastIn + pa); }
    else if (bs.length) { from = Math.max(0, bs.length - 160); to = bs.length - 1; }
    if (bs.length) {
      const step = bs.length > 1 ? (bs[1].t - bs[0].t) * MS : DAY * MS;
      pane.candles.events.once("datavalidated", () => {
        pane.xAxis.zoomToDates(new Date(bs[from].t * MS), new Date(bs[to].t * MS + step * 4));
        if (pane.key === "a") pane.root.events.once("frameended", () => proofStep(pane, t, span, bs));
      });
    }
    // pane notes (hourly window)
    let note = "";
    if (pane.tf === "1H" && !cal.hourly.length) note = "no hourly bars cached for this coin: `trade_viewer hourly --as-of ... " + state.coin + "` then `build`";
    else if (pane.tf === "1H" && t && span && cal.hourly.length && cal.daily[span.i][0] < cal.hourly[0][0]) note = "this trade predates the hourly window (the venue serves about 208 days)";
    else if (!bs.length) note = "no bars";
    paneNote(pane, note);
  }

  function proofStep(pane, t, span, bs) {
    const pf = state.proof;
    if ((pf.seed || pf.ray) && t && span) {
      const seed = pf.seed, ray = pf.ray;
      pf.seed = false; pf.ray = null;
      setTimeout(() => {
        const k = bs.findIndex((b) => b.days.includes(span.i));
        const xr = pane.xAxis.get("renderer"), yr = pane.yAxis.get("renderer");
        const pt = (tMs, price) => pane.panel.plotContainer.toGlobal({ x: xr.positionToCoordinate(pane.xAxis.valueToPosition(tMs)), y: yr.positionToCoordinate(pane.yAxis.valueToPosition(price)) });
        if (seed) {
          if (k >= 0 && t.stop != null) pane.drawing.addLine("Horizontal Line", pane.panel, pt(bs[k].t * MS, t.stop));
          if (k >= 0) pane.drawing.addLine("Vertical Line", pane.panel, pt(bs[k].t * MS, t.level));
          pane.save.saveData();
        }
        if (ray && k >= 0) {
          // &ray=open|high|low|close: a magnet click 4 px off that price of the entry bar; the line must land exactly on it
          const want = { open: bs[k].o, high: bs[k].h, low: bs[k].l, close: bs[k].c }[ray];
          if (want != null) {
            const local = { x: xr.positionToCoordinate(pane.xAxis.valueToPosition(bs[k].t * MS)) + 3, y: yr.positionToCoordinate(pane.yAxis.valueToPosition(want)) - 4 };
            const got = magnetDrop(pane, local);
            console.log("magnet proof: wanted " + ray + " " + want + ", snapped to " + got + (got === want ? " (exact)" : " (MISMATCH)"));
          }
        }
        if (pf.then) setTimeout(() => setPaneTf("a", pf.then), 400);
        pf.then = null;
      }, 100);
    } else if (pf.then) {
      const v = pf.then; pf.then = null;
      setTimeout(() => setPaneTf("a", v), 400);
    }
  }

  function draw() {
    syncHash();
    for (const pane of visiblePanes()) drawPane(pane);
    strip(); side(); legend();
  }

  function legend() {
    const bits = ['<span><i style="background:' + COL.gray + '"></i>not in a trade</span>',
      '<span><i style="background:' + COL.setup + '"></i>setup bar</span>', '<span><i style="background:' + COL.ref + '"></i>bar before it</span>',
      '<span><i style="background:' + COL.up + '"></i><i style="background:' + COL.down + '"></i>in the trade</span>',
      '<span><i style="background:' + COL.week + '"></i>week open</span>'];
    if (!state.showSys) bits.push("<span style='color:#f59e0b'>system levels hidden</span>");
    if (!state.showMan) bits.push("<span style='color:#f59e0b'>your drawings hidden</span>");
    bits.push('<span class="hint"><kbd>&larr;</kbd> <kbd>&rarr;</kbd> previous / next trade &middot; <kbd>R</kbd> magnet ray &middot; <kbd>Esc</kbd> leave / clear &middot; drawings: toolbar, saved per coin and pane (autosave on)</span>');
    $("legend").innerHTML = bits.join("");
  }

  // ---------------------------------------------------------------- the header strip, the story, the ladder, the context
  function strip() {
    const t = state.cur, el = $("strip"), cal = state.cal;
    if (!t || !cal) { el.innerHTML = '<span class="dim">Pick a trade in the table or on the calendar, or press the arrow keys.</span>'; return; }
    const long = t.direction === "up", p = precisionFor(cal.daily, t), st = settle(t, state.book), span = tradeSpan(t, state.book, cal);
    if (!span) { el.innerHTML = '<span class="dim">This trade\'s entry day is not in the coin\'s bars.</span>'; return; }
    const exitDate = iso(cal.daily[span.end][0]);
    const wt = htfType(cal, "W", span.i), mt = htfType(cal, "M", span.i);
    const stackChip = t.stack && t.stack !== t.tf ? ' <span class="chip flag">' + esc(stackWords(t, stackLevels(t, span.i, cal)).text) + "</span>" : "";
    const facts = [
      ["Trade", esc(state.coin) + ' <span class="chip ' + (long ? "long" : "short") + '">' + (long ? "LONG" : "SHORT") + "</span>"],
      ["Setup", TF_LABEL[t.tf] + " " + KIND_LABEL[t.kind] + stackChip + (t.flag && t.flag !== "none" ? ' <span class="chip flag">hammer</span>' : "")],
      ["Entry", t.date + ' <span class="sm">at</span> ' + fmtPrice(t.level, p)],
      ["Exit, book " + esc(state.book), st.price != null ? exitDate + ' <span class="sm">at</span> ' + fmtPrice(st.price, p) + ' <span class="sm">' + esc(st.how) + "</span>" : '<span class="sm">' + esc(st.how) + "</span>"],
      ["Held", (span.end - span.i) + " day" + (span.end - span.i === 1 ? "" : "s")],
      ["Result", '<span class="' + cls(st.ret) + '">' + fmtPct(st.ret) + '</span> <span class="sm">' + fmtUsd(st.ret, state.size) + "</span>"],
      ["Best / worst travel <span class=\"sm\">(book C window)</span>", '<span class="pos">+' + n2(t.mfe_x) + '%</span> <span class="sm">/</span> <span class="neg">-' + n2(t.mae_x) + "%</span>"],
      ["Week at entry", t.w_support === "with" ? '<span class="pos">with</span>' : '<span class="neg">against</span>'],
      ["Closed bars", btChip("W", wt) + " " + btChip("M", mt)],
    ];
    el.innerHTML = facts.map((f) => '<div class="fact"><div class="fl">' + f[0] + '</div><div class="fv">' + f[1] + "</div></div>").join("");
  }
  function side() {
    const t = state.cur, cal = state.cal;
    if (!t || !cal || cal.dayIdx.get(t.date) == null) {
      $("story").innerHTML = '<p class="dim">No trade selected.</p>'; $("ladder").innerHTML = ""; $("context").innerHTML = ""; return;
    }
    const ctx = { t, coin: state.coin, cal, book: state.book, size: state.size, p: precisionFor(cal.daily, t) };
    $("story").innerHTML = S.narrate(ctx);
    $("ladder").innerHTML = S.ladder(ctx);
    $("context").innerHTML = S.context(ctx);
    $("ladder").querySelectorAll("tr[data-book]").forEach((tr) => { tr.onclick = () => setBook(tr.dataset.book); });
  }
  function setBook(b) {
    if (!BOOK_RET[b]) return;
    state.book = b; $("book").value = b;
    sortItems();
    draw(); renderTable(); renderCalendar(); renderCompare();
  }

  // ---------------------------------------------------------------- the calendar
  function calMap() {
    if (state.calScope === "all") return state.uni ? ST.calendarDays(universeItems(), state.book, state.size) : new Map();
    return ST.calendarDays(state.items, state.book, state.size);
  }
  async function loadUniverse() {
    // data/universe.json: every coin's rows, decoded once; the filters apply to it like to a coin's rows
    if (!state.uni) {
      $("meta").textContent = "loading the universe table...";
      state.uni = ST.fromUniverse(await (await fetch("data/universe.json")).json());
      state.uniItems = null;
      $("meta").textContent = state.uni.length.toLocaleString("en-US") + " rows across " + new Set(state.uni.map((t) => t.coin)).size + " coins loaded";
    }
    return state.uni;
  }
  function universeItems() {
    if (!state.uni) return [];
    if (!state.uniItems) state.uniItems = filtered(state.uni).map((t) => ({ coin: t.coin, t }));
    return state.uniItems;
  }
  function calGoto(date) { state.calY = +date.slice(0, 4); state.calM = +date.slice(5, 7) - 1; }
  function renderCalendar() {
    const map = calMap();
    if (state.calY == null) calGoto(state.cur ? state.cur.date : state.items.length ? state.items[0].t.date : iso(Date.now() / 1000));
    const y = state.calY, m = state.calM;
    // cells carry the day's equal-size dollars (the size box per trade) and the trade count; shading is relative to the month's largest day
    const fmtK = (v) => { const s = v > 0 ? "+" : v < 0 ? "-" : ""; const a = Math.abs(v); return s + (a >= 10000 ? (a / 1000).toFixed(0) + "k" : a >= 1000 ? (a / 1000).toFixed(1) + "k" : a.toFixed(0)); };
    const shade = (v, max) => { if (!v || !max) return ""; const a = 0.1 + 0.45 * Math.min(1, Math.abs(v) / max); return "background:rgba(" + (v > 0 ? "34,197,94" : "239,68,68") + "," + a.toFixed(2) + ")"; };
    // the year strip
    const ms = Array(12).fill(0), mn = Array(12).fill(0);
    for (const [date, e] of map) if (+date.slice(0, 4) === y) { const k = +date.slice(5, 7) - 1; ms[k] += e.usd; mn[k] += e.n; }
    const yMax = Math.max(...ms.map(Math.abs));
    $("yearStrip").innerHTML = ms.map((s, k) => '<div class="ym ' + (k === m ? "on" : "") + '" data-m="' + k + '" style="' + shade(s, yMax) + '" title="' + (mn[k] ? mn[k] + " trades, " + fmtUsd0(s) + " USD at equal size" : "no trades") + '">' + "JFMAMJJASOND"[k] + "</div>").join("");
    $("yearStrip").querySelectorAll(".ym").forEach((d) => { d.onclick = () => { state.calM = +d.dataset.m; renderCalendar(); }; });
    // the month grid, census weeks (Monday first), a week-total column on the right
    const first = Date.UTC(y, m, 1) / 1000, end = nextMonth(first), start = weekStart(first);
    let dMax = 0;
    for (let ts = first; ts < end; ts += DAY) { const e = map.get(iso(ts)); if (e) dMax = Math.max(dMax, Math.abs(e.usd)); }
    let html = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun", "Week"].map((h) => '<div class="cd hd">' + h + "</div>").join("");
    for (let w = start; w < end; w += 7 * DAY) {
      let wSum = 0, wN = 0;
      for (let d = 0; d < 7; d++) {
        const ts = w + d * DAY, date = iso(ts), e = map.get(date), out = ts < first || ts >= end;
        const sel = state.cur && state.cur.date === date || state.dateMode && state.dateMode.date === date;
        const title = e ? e.n + " trade" + (e.n === 1 ? "" : "s") + ": " + fmtUsd0(e.usd) + " USD at " + state.size.toLocaleString("en-US") + " each, " + fmtPct(e.sum) + " summed" + (e.filled ? ", " + fmtPct(e.sum / e.filled) + " average" : "") : "";
        html += '<div class="cd' + (out ? " out" : "") + (sel ? " sel" : "") + '" data-date="' + date + '" style="' + (e ? shade(e.usd, dMax) : "") + '" title="' + esc(title) + '"><span class="dn">' + new Date(ts * 1000).getUTCDate() + "</span>" +
          (e ? '<span class="dc">' + e.n + '</span><span class="dv ' + cls(e.usd) + '">' + fmtK(e.usd) + "</span>" : "") + "</div>";
        if (e && !out) { wSum += e.usd; wN += e.n; }
      }
      html += '<div class="cd wk"><span class="dn">wk</span>' + (wN ? '<span class="dc">' + wN + '</span><span class="dv ' + cls(wSum) + '">' + fmtK(wSum) + "</span>" : "") + "</div>";
    }
    $("cal").innerHTML = html;
    $("cal").querySelectorAll(".cd[data-date]").forEach((d) => { d.onclick = () => calClick(d.dataset.date); });
    $("calTitle").textContent = monthName(y, m);
    const msum = ST.monthSummary(map, first, end);
    $("calFoot").innerHTML = msum.n ? msum.n + " trades" + (msum.filled < msum.n ? " (" + msum.filled + " with a result)" : "") + ", <b class=\"" + cls(msum.usd) + '">' + fmtUsd0(msum.usd) + "</b> USD, avg " + (msum.avg == null ? "n/a" : fmtPct(msum.avg) + " over the " + msum.filled + " with a result") : "no trades this month";
    $("calFoot2").textContent = (state.calScope === "all" ? "every coin, book " + state.book : "book " + state.book) + ", " + state.size.toLocaleString("en-US") + " USD each";
  }
  async function calClick(date) {
    if (state.calScope === "all") { $("dateBox").value = date; await applyDate(date); return; }
    const ks = []; state.items.forEach((it, k) => { if (it.t.date === date) ks.push(k); });
    if (!ks.length) { calGoto(date); renderCalendar(); return; }
    const pos = ks.indexOf(state.sel);
    select(ks[(pos + 1) % ks.length]);
  }
  function calStep(n) { let m = state.calM + n, y = state.calY; while (m < 0) { m += 12; y--; } while (m > 11) { m -= 12; y++; } state.calM = m; state.calY = y; renderCalendar(); }

  // ---------------------------------------------------------------- the trade table
  function filtered(rows) {
    return rows.filter((t) => state.tf.has(t.tf) && state.kind.has(t.kind) && state.dir.has(t.direction) && (!state.liquid || t.liquid) && (!state.hasT1 || t.t1 != null));
  }
  function sortItems() {
    const r = (it) => { const v = tradeRet(it.t); return v == null ? null : v; };
    const d = (it) => ST.daysOf(it.t, state.book);
    const byDate = (a, b) => a.t.date.localeCompare(b.t.date) || a.coin.localeCompare(b.coin) || a.t.tf.localeCompare(b.t.tf) || a.t.direction.localeCompare(b.t.direction);
    const cmp = {
      "date-desc": (a, b) => -byDate(a, b), "date-asc": byDate,
      "ret-desc": (a, b) => ((r(b) ?? -1e9) - (r(a) ?? -1e9)) || byDate(a, b), "ret-asc": (a, b) => ((r(a) ?? 1e9) - (r(b) ?? 1e9)) || byDate(a, b),
      "days-desc": (a, b) => ((d(b) ?? -1) - (d(a) ?? -1)) || byDate(a, b),
    }[state.sort] || byDate;
    state.items.sort(cmp);
    state.sel = state.cur ? state.items.findIndex((it) => it.t === state.cur) : -1;
  }
  function renderTable() {
    const tb = $("tbody");
    $("trades").classList.toggle("withCoin", !!state.dateMode);
    let html = "";
    state.items.forEach((it, k) => {
      const t = it.t, long = t.direction === "up", v = tradeRet(t), cal = state.cals.get(it.coin), i = cal ? cal.dayIdx.get(t.date) : null;
      const bt = cal && i != null ? btChip("W", htfType(cal, "W", i)) + " " + btChip("M", htfType(cal, "M", i)) : "";
      const days = ST.daysOf(t, state.book), st = settle(t, state.book);
      html += '<tr data-k="' + k + '"' + (k === state.sel ? ' class="sel"' : "") + ' title="' + esc(TF_LABEL[t.tf] + " " + KIND_LABEL[t.kind] + (t.stack && t.stack !== t.tf ? ", stack " + t.stack : "") + "; book " + state.book + ": " + st.how + (days == null ? "" : ", " + days + " day" + (days === 1 ? "" : "s"))) + '"><td>' + t.date + '</td><td class="coinCol">' + esc(it.coin) +
        '</td><td><span class="' + (long ? "pos" : "neg") + '">' + (long ? "Long" : "Short") + "</span> " + t.tf + " " + KIND_SHORT[t.kind] + (t.stack && t.stack !== t.tf ? ' <span class="dim">+</span>' : "") + "</td><td>" + bt + '</td><td class="num ' + cls(v) + '">' + fmtPct(v) + "</td></tr>";
    });
    tb.innerHTML = html;
    tb.querySelectorAll("tr").forEach((tr) => { tr.onclick = () => select(+tr.dataset.k); });
    const sel = tb.querySelector("tr.sel");
    if (sel) sel.scrollIntoView({ block: "nearest" });
    const n = state.items.length, rets = state.items.map((it) => tradeRet(it.t)).filter((x) => x != null);
    const avg = rets.length ? rets.reduce((a, b) => a + b, 0) / rets.length : null, sum = rets.reduce((a, b) => a + b, 0);
    $("tableTitle").innerHTML = (state.dateMode ? "Entered " + longDate(state.dateMode.date) + ", all coins" : esc(state.coin || "") + " trades") + ' <span class="right" style="text-transform:none;letter-spacing:0">' + n + " shown &middot; avg <b class=\"" + cls(avg) + '">' + fmtPct(avg) + "</b> &middot; <b class=\"" + cls(sum) + '">' + fmtUsd(sum, state.size) + "</b></span>";
  }

  // ---------------------------------------------------------------- the Compare tab
  function makeCompareCharts() {
    const r1 = am5.Root.new("eq"); r1.utc = true; r1.setThemes([am5themes_Dark.new(r1)]);
    r1.numberFormatter.set("numberFormat", "#,###");
    const ch = r1.container.children.push(am5xy.XYChart.new(r1, { panX: false, panY: false, wheelY: "none", layout: r1.verticalLayout, paddingLeft: 0, paddingRight: 8 }));
    const x = ch.xAxes.push(am5xy.DateAxis.new(r1, { baseInterval: { timeUnit: "day", count: 1 }, renderer: am5xy.AxisRendererX.new(r1, { minGridDistance: 80, minorGridEnabled: false }), tooltip: am5.Tooltip.new(r1, {}) }));
    const y = ch.yAxes.push(am5xy.ValueAxis.new(r1, { renderer: am5xy.AxisRendererY.new(r1, {}) }));
    y.get("renderer").grid.template.setAll({ stroke: am5.color("#1b2030"), strokeOpacity: 1 });
    x.get("renderer").grid.template.setAll({ stroke: am5.color("#161a23"), strokeOpacity: 1 });
    const zero = y.createAxisRange(y.makeDataItem({ value: 0 }));
    zero.get("grid").setAll({ stroke: am5.color("#8b93a7"), strokeOpacity: 0.6, strokeDasharray: [3, 3], visible: true });
    const series = {};
    for (const b of BOOKS) {
      const s = ch.series.push(am5xy.LineSeries.new(r1, { name: BOOK_NAME[b], xAxis: x, yAxis: y, valueXField: "t", valueYField: "v", stroke: am5.color(BOOK_COL[b]),
        tooltip: am5.Tooltip.new(r1, { labelText: "{name}: {valueY.formatNumber('#,###')} USD" }) }));
      s.strokes.template.setAll({ strokeWidth: 1.25 });
      series[b] = s;
    }
    const legend = ch.children.push(am5.Legend.new(r1, { centerX: am5.p50, x: am5.p50, marginTop: 4 }));
    legend.labels.template.setAll({ fontSize: 11 }); legend.markers.template.setAll({ width: 10, height: 10 });
    legend.data.setAll(ch.series.values);
    ch.set("cursor", am5xy.XYCursor.new(r1, { behavior: "none", xAxis: x }));
    // the distribution: one-percent bins, the page's book against the chance book
    const r2 = am5.Root.new("hist"); r2.setThemes([am5themes_Dark.new(r2)]);
    const hc = r2.container.children.push(am5xy.XYChart.new(r2, { panX: false, panY: false, wheelY: "none", layout: r2.verticalLayout, paddingLeft: 0, paddingRight: 8 }));
    const hx = hc.xAxes.push(am5xy.CategoryAxis.new(r2, { categoryField: "bin", renderer: am5xy.AxisRendererX.new(r2, { minGridDistance: 24, minorGridEnabled: false }) }));
    hx.get("renderer").labels.template.setAll({ fontSize: 10 });
    hx.get("renderer").grid.template.set("forceHidden", true);
    const hy = hc.yAxes.push(am5xy.ValueAxis.new(r2, { renderer: am5xy.AxisRendererY.new(r2, {}), numberFormat: "#'%'" }));
    hy.get("renderer").grid.template.setAll({ stroke: am5.color("#1b2030"), strokeOpacity: 1 });
    const mk = (field, color) => {
      const s = hc.series.push(am5xy.ColumnSeries.new(r2, { name: "", xAxis: hx, yAxis: hy, valueYField: field, categoryXField: "bin", fill: am5.color(color), stroke: am5.color(color),
        tooltip: am5.Tooltip.new(r2, { labelText: "{name} {categoryX}%: {valueY.formatNumber('#.0')}% of trades" }) }));
      s.columns.template.setAll({ width: am5.percent(80), fillOpacity: 0.85, strokeOpacity: 0 });
      return s;
    };
    const hA = mk("a", BOOK_COL.C), hB = mk("b", BOOK_COL.ref);
    const hl = hc.children.push(am5.Legend.new(r2, { centerX: am5.p50, x: am5.p50, marginTop: 4 }));
    hl.labels.template.setAll({ fontSize: 11 }); hl.markers.template.setAll({ width: 10, height: 10 });
    state.cmp = { r1, series, r2, hx, hA, hB, hl };
  }
  function kpiCard(s, b, sel) {
    const g = (label, val) => "<div><i>" + label + "</i>" + val + "</div>";
    return '<div class="kpi' + (sel ? " sel" : "") + '" data-book="' + b + '"><div class="kh"><span class="dot" style="background:' + BOOK_COL[b] + '"></span>' + esc(BOOK_NAME[b]) + "</div>" +
      '<div class="kbig ' + cls(s.avg) + '">' + fmtPct(s.avg) + "</div><div class=\"ksub\">avg per trade &middot; " + s.filled + " filled" + (s.filled !== s.n ? " of " + s.n : "") + "</div>" +
      '<div class="kgrid">' + g("green", s.win == null ? "-" : (s.win * 100).toFixed(0) + "%") + g("median", '<span class="' + cls(s.med) + '">' + fmtPct(s.med) + "</span>") +
      g("total USD", '<span class="' + cls(s.total) + '">' + fmtUsd0(s.total) + "</span>") + g("max drawdown", '<span class="neg">' + (s.maxDD ? "-" + fmtUsd0(s.maxDD).slice(1) : "0") + "</span>") +
      g("at target", s.target == null ? "-" : (s.target * 100).toFixed(0) + "%") + g("median days", s.medDays == null ? "-" : s.medDays) +
      g("avg win / loss", (s.avgWin == null ? "-" : fmtPct(s.avgWin, 1)) + " / " + (s.avgLoss == null ? "-" : fmtPct(s.avgLoss, 1))) + g("best / worst", (s.best == null ? "-" : fmtPct(s.best, 1)) + " / " + (s.worst == null ? "-" : fmtPct(s.worst, 1))) +
      "</div></div>";
  }
  function renderCompare() {
    if (state.tab !== "compare") { state.cmpDirty = true; return; }
    state.cmpDirty = false;
    if (!state.cmp) makeCompareCharts();
    const universe = state.cmpScope === "universe" && state.uni;
    const items = universe ? universeItems() : state.items;
    $("cmpScopeNote").textContent = universe ? items.length.toLocaleString("en-US") + " rows across every coin, filters applied (returns to three decimals in the universe table)" : state.cmpScope === "universe" ? "loading the universe table..." : "";
    const stats = ST.allBooks(items, state.size);
    $("kpis").innerHTML = BOOKS.map((b) => kpiCard(stats[b], b, b === state.book)).join("");
    $("kpis").querySelectorAll(".kpi").forEach((k) => { k.onclick = () => setBook(k.dataset.book); });
    for (const b of BOOKS) {
      const s = state.cmp.series[b];
      s.data.setAll(stats[b].curve);
      s.strokes.template.setAll({ strokeWidth: b === state.book ? 3 : 1.25, strokeOpacity: b === state.book ? 1 : 0.8 });
    }
    const other = state.book === "ref" ? "C" : "ref";
    const bins = ST.histogram(items, state.book, other, -15, 15);
    state.cmp.hx.data.setAll(bins);
    state.cmp.hA.set("name", BOOK_NAME[state.book]); state.cmp.hA.set("fill", am5.color(BOOK_COL[state.book])); state.cmp.hA.set("stroke", am5.color(BOOK_COL[state.book]));
    state.cmp.hB.set("name", BOOK_NAME[other]); state.cmp.hB.set("fill", am5.color(BOOK_COL[other])); state.cmp.hB.set("stroke", am5.color(BOOK_COL[other]));
    state.cmp.hA.data.setAll(bins); state.cmp.hB.data.setAll(bins);
    state.cmp.hl.data.setAll([state.cmp.hA, state.cmp.hB]);
    const scope = universe ? "every coin, filters applied" : state.dateMode ? "every trade entered " + longDate(state.dateMode.date) + " across coins" : (state.coin || "") + ", filters applied";
    $("eqNote").textContent = scope + ", " + state.size.toLocaleString("en-US") + " USD per trade";
    $("histNote").textContent = "one-percent bins, share of filled trades; the end bins collect everything beyond";
    // by setup
    const rows = ST.bySetup(items);
    const cell = (v, n) => { if (v == null) return "<td>-</td>"; const a = Math.min(0.45, Math.abs(v) / 4); return '<td style="background:rgba(' + (v > 0 ? "34,197,94" : "239,68,68") + "," + a.toFixed(2) + ')" title="' + n + ' filled">' + fmtPct(v) + "</td>"; };
    $("bySetup").innerHTML = '<table class="setup"><thead><tr><th>setup</th><th>trades</th>' + BOOKS.map((b) => "<th>" + esc(BOOK_NAME[b]) + "</th>").join("") + "<th>D5 - chance</th></tr></thead><tbody>" +
      rows.map((r, k) => "<tr" + (k === 0 ? ' class="head"' : "") + "><td>" + esc(r.label) + "</td><td>" + r.n + "</td>" + BOOKS.map((b) => cell(r.avg[b], r["n" + b])).join("") + cell(r.swap, r.swapN) + "</tr>").join("") + "</tbody></table>";
    $("cmpNote").innerHTML = "Equal-size trades at the size box, no leverage, fees or funding; totals are sums, never an account. The chance book and D5 settle at five bars, the others at the 20-day cap; " +
      "\"at target\" is the share of filled trades that left at the book's target (one R for D, D5 and the chance book). The receipt's own tables (every coin, every unit) are in analysis/domino/results/manage_tables.md.";
  }

  // ---------------------------------------------------------------- tabs, data, selection
  function setTab(v) {
    state.tab = v;
    document.body.className = "tab-" + v;
    $("tabs").querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.v === v));
    document.querySelectorAll(".view").forEach((el) => el.classList.toggle("on", el.id === "view-" + v));
    if (v === "compare") renderCompare();
    if (v === "playbook" && !state.playbookDone) { $("playbook").innerHTML = S.playbook(); state.playbookDone = true; }
    if (v === "trade") for (const p of visiblePanes()) p.root.resize();
    syncHash();
  }

  async function loadCoin(coin) {
    const entry = state.index.coins.find((c) => c.coin === coin);
    if (!entry) return false;
    const d = await (await fetch("data/" + entry.file)).json();
    d.trades.forEach((t, i) => { t._i = i; });
    if (!state.cals.has(coin)) state.cals.set(coin, makeCalendar(d));
    state.coin = coin; state.data = d; state.cal = state.cals.get(coin);
    $("meta").textContent = coin + ": " + d.daily.length + " daily bars " + iso(d.daily[0][0]) + " to " + iso(d.daily[d.daily.length - 1][0]) + (d.hourly.length ? ", hourly from " + isoH(d.hourly[0][0]) : ", no hourly bars") + ", " + d.trades.length + " trades, as of " + d.as_of;
    for (const pane of Object.values(state.panes)) if (pane) { pane.seg.querySelector('[data-v="1H"]').disabled = !d.hourly.length; swapDrawings(pane, coin); }
    return true;
  }
  async function select(k) {
    const it = state.items[k];
    if (!it) return;
    if (state.coin !== it.coin) await loadCoin(it.coin);
    state.sel = k; state.cur = it.t;
    calGoto(it.t.date);
    draw(); renderTable(); renderCalendar();
  }
  function syncHash() {
    // the reference page's address form (#coin=BTC&date=2025-06-17&tf=D&dir=down&view=1D&book=C) plus this page's layout keys
    const t = state.cur, q = [];
    if (state.dateMode) q.push("day=" + state.dateMode.date);
    if (state.coin) q.push("coin=" + encodeURIComponent(state.coin));
    if (t) q.push("date=" + t.date, "tf=" + t.tf, "dir=" + t.direction);
    if (state.panes.a) q.push("view=" + state.panes.a.tf);
    q.push("book=" + state.book);
    if (state.layout === "dual") q.push("layout=dual", "view2=" + (state.panes.b ? state.panes.b.tf : "1W"));
    if (state.tab !== "trade") q.push("tab=" + state.tab);
    if (state.cmpScope === "universe") q.push("cmp=universe");
    if (state.calScope === "all") q.push("cal=all");
    history.replaceState(null, "", "#" + q.join("&"));
  }
  function fromHash() {
    const q = new URLSearchParams(location.hash.slice(1));
    const g = (k) => q.get(k);
    return { coin: g("coin"), date: g("date"), tf: g("tf"), dir: g("dir"), view: g("view"), book: g("book"), seed: g("seed"), then: g("then"), ray: g("ray"), show: g("show"), layout: g("layout"), view2: g("view2"), tab: g("tab"), day: g("day"), cal: g("cal"), cmp: g("cmp") };
  }
  function lastSettled(items) { for (let k = 0; k < items.length; k++) if (items[k].t.status === "exit") return k; return items.length ? 0 : -1; }

  function rebuildItems() {
    if (state.dateMode) state.items = state.dateMode.items.slice();
    else if (state.data) state.items = filtered(state.data.trades).map((t) => ({ coin: state.coin, t }));
    else state.items = [];
    state.uniItems = null;
    sortItems();
    if (state.sel < 0) state.cur = null;
  }
  async function refilter() {
    if (state.dateMode) { await applyDate(state.dateMode.date); return; }
    rebuildItems();
    draw(); renderTable(); renderCalendar(); renderCompare();
  }
  async function loadDates() { if (!state.dates) state.dates = await (await fetch("data/dates.json")).json(); return state.dates; }
  async function applyDate(date) {
    await loadDates();
    const rows = state.dates[date] || [];
    const want = [];
    for (const r of rows) {
      const [coin, direction, tf, kind] = r;
      if (!state.tf.has(tf) || !state.kind.has(kind) || !state.dir.has(direction)) continue;
      want.push({ coin, tf, direction });
    }
    const byCoin = new Map();
    for (const w of want) if (!byCoin.has(w.coin)) byCoin.set(w.coin, fetch("data/" + state.index.coins.find((c) => c.coin === w.coin).file).then((r) => r.json()));
    const items = [];
    for (const w of want) {
      const d = await byCoin.get(w.coin);
      if (d.trades[0] && d.trades[0]._i == null) d.trades.forEach((t, i) => { t._i = i; });
      if (!state.cals.has(w.coin)) state.cals.set(w.coin, makeCalendar(d));
      const t = d.trades.find((x) => x.date === date && x.tf === w.tf && x.direction === w.direction);
      if (t && (!state.liquid || t.liquid) && (!state.hasT1 || t.t1 != null)) items.push({ coin: w.coin, t });
    }
    state.dateMode = { date, items };
    state.sel = -1; state.cur = null;
    rebuildItems();
    calGoto(date);
    $("meta").textContent = items.length + " trades entered " + longDate(date) + " (filters applied)";
    if (state.items.length) await select(0); else { draw(); renderTable(); renderCalendar(); }
    renderCompare();
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
    state.panes.a = makePane("a");
    state.index = await (await fetch("data/index.json")).json();
    const dl = $("coinList");
    for (const c of state.index.coins) { const o = document.createElement("option"); o.value = c.coin; o.label = c.n + " trades"; dl.appendChild(o); }
    $("meta").textContent = state.index.coins.length + " coins, " + state.index.trades.toLocaleString() + " trades, as of " + state.index.as_of;
    seg("fTf", () => { state.tf = setOf("fTf"); refilter(); }, true);
    seg("fKind", () => { state.kind = setOf("fKind"); refilter(); }, true);
    seg("fDir", () => { state.dir = setOf("fDir"); refilter(); }, true);
    seg("fLiq", (v, on) => { state.liquid = on; refilter(); }, true);
    seg("fT1", (v, on) => { state.hasT1 = on; refilter(); }, true);
    seg("layout", (v) => setLayout(v), false);
    seg("tabs", (v) => setTab(v), false);
    seg("calScope", async (v) => { state.calScope = v; if (v === "all") await loadUniverse(); syncHash(); renderCalendar(); }, false);
    seg("cmpScope", async (v) => { state.cmpScope = v; if (v === "universe") { renderCompare(); await loadUniverse(); } syncHash(); renderCompare(); }, false);
    seg("fShow", (v, on) => {
      if (v === "sys") { state.showSys = on; draw(); }
      else { state.showMan = on; for (const p of visiblePanes()) setDrawingsVisible(p, on); legend(); }
    }, true);
    $("book").onchange = (e) => setBook(e.target.value);
    $("size").onchange = (e) => { state.size = Number(e.target.value) || 1000; draw(); renderTable(); renderCalendar(); renderCompare(); };
    $("sort").onchange = (e) => { state.sort = e.target.value; sortItems(); renderTable(); };
    $("calPrev").onclick = () => calStep(-1); $("calNext").onclick = () => calStep(1);
    $("coinBox").onchange = async (e) => {
      const v = e.target.value.trim().toUpperCase();
      if (!v) return;
      state.dateMode = null; $("dateBox").value = "";
      if (await loadCoin(v)) { state.cur = null; rebuildItems(); state.sel = lastSettled(state.items); state.cur = state.items[state.sel] ? state.items[state.sel].t : null; if (state.cur) calGoto(state.cur.date); draw(); renderTable(); renderCalendar(); renderCompare(); }
      else $("meta").textContent = "no such coin in the viewer data: " + v;
    };
    $("dateBox").onchange = (e) => { if (e.target.value) applyDate(e.target.value); };
    document.addEventListener("keydown", (e) => {
      if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || e.target.tagName === "TEXTAREA") return;
      const n = state.items.length;
      const magnets = visiblePanes().filter((p) => p.magnet);
      if (e.key === "ArrowRight" && state.sel < n - 1) { select(state.sel + 1); e.preventDefault(); }
      else if (e.key === "ArrowLeft" && state.sel > 0) { select(state.sel - 1); e.preventDefault(); }
      else if (e.key === "r" || e.key === "R") { const p = state.panes[state.hover] && !state.panes[state.hover].el.hidden ? state.panes[state.hover] : state.panes.a; if (p) setMagnet(p, !p.magnet); }
      else if (e.key === "Escape" && magnets.length) { for (const p of magnets) setMagnet(p, false); }
      else if (e.key === "Escape") { state.sel = -1; state.cur = null; draw(); renderTable(); renderCalendar(); }
    });
    const want = fromHash();
    state.proof.seed = want.seed === "1"; state.proof.then = INTERVAL[want.then] ? want.then : null;
    state.proof.ray = ["open", "high", "low", "close"].includes(want.ray) ? want.ray : null;
    if (want.cmp === "universe") { state.cmpScope = "universe"; $("cmpScope").querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.v === "universe")); }
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
    if (want.view && INTERVAL[want.view] && state.panes.a) { state.panes.a.tf = want.view; state.panes.a.seg.querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.v === want.view)); }
    if (want.layout === "dual") {
      setLayout("dual");
      if (want.view2 && INTERVAL[want.view2] && state.panes.b) { state.panes.b.tf = want.view2; state.panes.b.seg.querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.v === want.view2)); }
    }
    rebuildItems();
    state.sel = want.date ? state.items.findIndex((it) => it.t.date === want.date && (!want.tf || it.t.tf === want.tf) && (!want.dir || it.t.direction === want.dir)) : -1;
    if (state.sel < 0) state.sel = lastSettled(state.items);
    state.cur = state.items[state.sel] ? state.items[state.sel].t : null;
    if (state.cur) calGoto(state.cur.date);
    for (const p of Object.values(state.panes)) if (p) p.ready = true;
    if (want.cal === "all") { state.calScope = "all"; $("calScope").querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.v === "all")); }
    if (want.cal === "all" || want.cmp === "universe") await loadUniverse();
    draw(); renderTable(); renderCalendar();
    if (want.day && /^\d{4}-\d{2}-\d{2}$/.test(want.day)) {
      // &day=YYYY-MM-DD: every trade entered that day across coins (the date box), the coin / tf / dir keys picking one of them
      $("dateBox").value = want.day;
      await applyDate(want.day);
      const k = want.coin ? state.items.findIndex((it) => it.coin === want.coin && (!want.tf || it.t.tf === want.tf) && (!want.dir || it.t.direction === want.dir)) : -1;
      if (k >= 0) await select(k);
    }
    if (want.tab === "compare" || want.tab === "playbook") setTab(want.tab); else renderCompare();
  }
  init().catch((e) => { const em = document.querySelector("#pane-a .empty"); if (em) { em.style.display = "flex"; em.textContent = "failed to load: " + e; } console.error(e); });
})(window.DV);
