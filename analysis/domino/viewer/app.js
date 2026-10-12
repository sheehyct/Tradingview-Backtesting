/* Domino Trade Viewer -- draws the management book's recorded trades on the cached candles.
   No trade logic lives here: entry day, targets, touch days and the exit day come off the row
   exactly as analysis/domino/manage.py wrote them. The only computation is calendar bucketing
   (Monday 00:00 UTC weeks, calendar months), mirrored from analysis/domino/census.py. */
(function () {
  "use strict";
  const DAY = 86400, HOUR = 3600, CAP = 20;
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
  const RAY = "rgba(59,130,246,0.7)";
  const KIND_LABEL = { reversal: "reversal", continuation: "continuation", inside: "inside break", outside: "outside break" };
  const TF_LABEL = { D: "daily", W: "weekly", M: "monthly" };

  const $ = (id) => document.getElementById(id);
  const state = {
    index: null, dates: null, coin: null, data: null, daily: [], hourly: [],
    chartTf: "1D", tf: new Set(["D", "W", "M"]), kind: new Set(["reversal", "continuation", "inside", "outside"]),
    dir: new Set(["up", "down"]), liquid: false, hasT1: false, book: "C", size: 1000,
    list: [], sel: -1, cur: null, dateMode: null, chart: null, series: null, weekLine: null, lines: [],
    rays: [], rayLines: [], rayMode: false,
  };

  // ---------------------------------------------------------------- calendar (census rules)
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

  // ---------------------------------------------------------------- trade geometry (from the row)
  function settle(t, book) {
    // how a book settled, as the row recorded it: the day held (days_X), the fill (level moved by the
    // recorded return, so it is the engine's own number) and why. Book C is the headline exit clock.
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
    // day index of the entry day, and the last day the given book (default: the book box) held the trade
    const i = state.dayIdx.get(t.date);
    if (i == null) return null;
    const end = Math.min(i + settle(t, book).k, state.daily.length - 1);
    return { i, end };
  }
  function stackLevels(t, i) {
    // the previous complete bar's high / low on each timeframe the row says broke that day (the census's
    // "levels": the day's = yesterday's; the week's = last week's; the month's = last month's)
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
    // the setup bar and the bar before it, as day-index sets, per the unit's own timeframe
    const setup = new Set(), ref = new Set();
    if (t.tf === "D") { if (i - 1 >= 0) setup.add(i - 1); if (i - 2 >= 0) ref.add(i - 2); return { setup, ref }; }
    const buckets = t.tf === "W" ? state.weeks : state.months;
    const bi = buckets.findIndex((b) => b.days.includes(i));
    if (bi > 0) buckets[bi - 1].days.forEach((d) => setup.add(d));
    if (bi > 1) buckets[bi - 2].days.forEach((d) => ref.add(d));
    return { setup, ref };
  }

  // ---------------------------------------------------------------- chart
  function makeChart() {
    const el = $("chart");
    if (!window.LightweightCharts) { $("empty").textContent = "chart library missing: run `trade_viewer build` again (it vendors the library)"; return; }
    state.chart = LightweightCharts.createChart(el, {
      autoSize: true,
      layout: { background: { type: "solid", color: "#0f1117" }, textColor: "#8a90a2", fontSize: 12 },
      grid: { vertLines: { color: "#161a23" }, horzLines: { color: "#1b2030", style: 2 } },
      crosshair: { mode: 0 },
      rightPriceScale: { borderColor: "#262c3a", scaleMargins: { top: 0.08, bottom: 0.08 } },
      timeScale: { borderColor: "#262c3a", timeVisible: false, secondsVisible: false, rightOffset: 6, barSpacing: 8 },
    });
    state.series = state.chart.addCandlestickSeries({
      upColor: COL.gray, downColor: COL.gray, borderVisible: false, wickUpColor: COL.grayWick, wickDownColor: COL.grayWick,
      priceLineVisible: false, lastValueVisible: false,
    });
    state.weekLine = state.chart.addLineSeries({ color: COL.week, lineWidth: 1, lineStyle: 3, lineType: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false });
    state.chart.subscribeClick(onChartClick);
    $("empty").style.display = "none";
  }

  // ---------------------------------------------------------------- rays: a magnet horizontal line, per coin, across every timeframe
  function rayKey() { return "domino-viewer-rays:" + state.coin; }
  function loadRays() { try { state.rays = JSON.parse(localStorage.getItem(rayKey()) || "[]").filter((x) => typeof x === "number"); } catch (e) { state.rays = []; } }
  function saveRays() { try { localStorage.setItem(rayKey(), JSON.stringify(state.rays)); } catch (e) { /* no storage: rays live for the page only */ } }
  function drawRays() {
    if (!state.series) return;
    for (const l of state.rayLines) state.series.removePriceLine(l);
    state.rayLines = state.rays.map((price) => state.series.createPriceLine({ price, color: RAY, lineWidth: 1, lineStyle: 0, axisLabelVisible: true, title: "" }));
    const p = precisionFor(state.daily, state.cur);
    $("rays").innerHTML = state.rays.map((r, k) => '<span class="ray">' + fmtPrice(r, p) + ' <a data-k="' + k + '" title="remove this ray">&times;</a></span>').join("");
    $("rays").querySelectorAll("a").forEach((a) => a.onclick = () => { state.rays.splice(Number(a.dataset.k), 1); saveRays(); drawRays(); });
  }
  function setRayMode(on) {
    state.rayMode = on;
    $("rayMode").classList.toggle("on", on);
    $("chart").classList.toggle("ray", on);
    if (state.chart) state.chart.applyOptions({ crosshair: { mode: on ? 1 : 0 } });
  }
  function onChartClick(param) {
    if (!state.rayMode || !param.point || !state.series) return;
    let price = state.series.coordinateToPrice(param.point.y);
    if (price == null) return;
    const bar = param.seriesData && param.seriesData.get(state.series);
    if (bar && bar.open != null) {
      // strong magnet: the nearest of the bar's open / high / low / close under the cursor, on the active timeframe
      const cands = [bar.open, bar.high, bar.low, bar.close];
      price = cands.reduce((best, x) => Math.abs(x - price) < Math.abs(best - price) ? x : best, cands[0]);
    }
    // a click within 8px of an existing ray moves that ray to the new magnet price; Alt+click removes it; else a new ray
    const near = state.rays.findIndex((r) => Math.abs(state.series.priceToCoordinate(r) - param.point.y) <= 8);
    const alt = !!(param.sourceEvent && param.sourceEvent.altKey);
    if (near >= 0 && alt) state.rays.splice(near, 1);
    else if (near >= 0) state.rays[near] = price;
    else if (!alt) state.rays.push(price);
    saveRays(); drawRays();
  }

  function clearLines() { for (const l of state.lines) state.series.removePriceLine(l); state.lines = []; }
  function addLine(price, color, style, title) {
    if (price == null) return;
    state.lines.push(state.series.createPriceLine({ price, color, lineWidth: 1, lineStyle: style, axisLabelVisible: true, title }));
  }

  function bars() {
    // the bars of the active chart timeframe, each with the day indices it covers
    if (state.chartTf === "1H") return state.hourly.map((b) => ({ t: b[0], o: b[1], h: b[2], l: b[3], c: b[4], days: [state.dayIdx.get(iso(b[0]))].filter((x) => x != null), hour: true }));
    if (state.chartTf === "1D") return state.daily.map((b, i) => ({ t: b[0], o: b[1], h: b[2], l: b[3], c: b[4], days: [i] }));
    return (state.chartTf === "1W" ? state.weeks : state.months).map((b) => ({ t: b.t, o: b.o, h: b.h, l: b.l, c: b.c, days: b.days, complete: b.complete }));
  }

  function draw() {
    if (!state.series) return;
    syncHash();
    const t = state.cur;
    const span = t ? tradeSpan(t) : null;
    const sd = t && span ? setupDays(t, span.i) : null;
    const bs = bars();
    const p = precisionFor(state.daily, t);
    state.series.applyOptions({ priceFormat: { type: "price", precision: p, minMove: Math.pow(10, -p) } });
    state.chart.applyOptions({ timeScale: { timeVisible: state.chartTf === "1H" } });
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
      data.push({ time: b.t, open: b.o, high: b.h, low: b.l, close: b.c, color, borderColor: color, wickColor: wick });
    });
    state.series.setData(data);
    // the week's open under every bar (the exit rule's second test), on the fast views only
    if (state.chartTf === "1H" || state.chartTf === "1D") {
      state.weekLine.setData(bs.map((b) => ({ time: b.t, value: state.weekOpenAt(b.t) })).filter((x) => x.value != null));
    } else state.weekLine.setData([]);
    clearLines();
    const markers = [];
    if (t && span) {
      const long = t.direction === "up";
      const st = settle(t);
      const hs = tradeSpan(t, "C");
      const levels = stackLevels(t, span.i);
      const domino = levels.length > 1 && CLS_LABEL[t.cls] && t.cls !== "spread";
      addLine(t.level, COL.level, 0, domino ? "Position opened: domino " + t.stack + " (" + CLS_LABEL[t.cls] + ")" : "Position opened (" + TF_LABEL[t.tf] + " trigger)");
      for (const l of levels) if (l.tf !== t.tf) addLine(l.price, COL.level, 2, TF_LABEL[l.tf] + " trigger, broke the same day");
      if (st.price != null) addLine(st.price, COL.exit, 2, "Position closed: " + st.book + " " + st.how);
      addLine(t.t1, COL.target, 2, "T1 " + (t.t1_src || ""));
      addLine(t.t2, COL.target, 2, "T2 " + (t.t2_src || ""));
      addLine(t.t3, COL.target, 2, "T3 " + (t.t3_src || ""));
      if (t.stop != null && t.level != null) {
        const r = Math.abs(t.level - t.stop);
        addLine(long ? t.level + r : t.level - r, COL.oneR, 1, "one R");
        addLine(t.stop, COL.stop, 1, "setup-bar stop (chance book)");
      }
      if (t.mm_t1 != null) addLine(t.mm_t1, COL.mm, 4, "measured move");
      // markers: entry, touches, exit -- placed on the bar that covers the engine's day
      const barOfDay = (d, pick) => {
        const ks = []; bs.forEach((b, k) => { if (b.days.includes(d)) ks.push(k); });
        if (!ks.length) return null;
        if (!pick || ks.length === 1) return ks[0];
        return pick(ks);
      };
      const touchBar = (d, price, side) => barOfDay(d, (ks) => ks.find((k) => side === "hi" ? bs[k].h >= price : bs[k].l <= price) ?? ks[0]);
      const put = (k, text, above, color, shape) => { if (k != null) markers.push({ time: bs[k].t, position: above ? "aboveBar" : "belowBar", color, shape, text }); };
      put(touchBar(span.i, t.level, long ? "hi" : "lo"), "in " + fmtPrice(t.level, p), !long, COL.level, long ? "arrowUp" : "arrowDown");
      const touches = [["t1_k", "T1", t.t1], ["t2_k", "T2", t.t2], ["t3_k", "T3", t.t3], ["one_r_k", "1R", t.stop != null ? (long ? t.level + Math.abs(t.level - t.stop) : t.level - Math.abs(t.level - t.stop)) : null], ["mm1_k", "MM", t.mm_t1]];
      for (const [key, label, price] of touches) {
        if (t[key] == null || price == null) continue;
        const d = span.i + t[key];
        if (d > span.end) continue;
        put(touchBar(d, price, long ? "hi" : "lo"), label, long, key === "one_r_k" ? COL.oneR : key === "mm1_k" ? COL.mm : COL.target, "circle");
      }
      if (t.stop_k != null && span.i + t.stop_k <= span.end) put(touchBar(span.i + t.stop_k, t.stop, long ? "lo" : "hi"), "stop", !long, COL.stop, "circle");
      // the selected book's fill: at its target price on the touch bar, else at the settle day's close
      if (st.price != null && st.target) put(touchBar(span.end, st.price, long ? "hi" : "lo"), "out " + fmtPrice(st.price, p) + " (" + st.how + ")", long, COL.exit, long ? "arrowDown" : "arrowUp");
      else if (st.price != null) put(barOfDay(span.end, (ks) => ks[ks.length - 1]), "out " + fmtPrice(st.price, p) + (st.book === "C" ? "" : " (" + st.how + ")"), long, COL.exit, long ? "arrowDown" : "arrowUp");
      else put(barOfDay(span.end, (ks) => ks[ks.length - 1]), "data ends", long, COL.stop, "square");
      // the headline daily clock, when the book box left the trade on another day
      if (st.book !== "C" && hs && hs.end !== span.end && t.status === "exit") put(barOfDay(hs.end, (ks) => ks[ks.length - 1]), "daily clock out", long, COL.stop, "square");
      // the declared alternative clocks (prereg A2): under water on the daily, the hourly clock on the hourly view
      if (t.status_u === "exit" && t.exit_k_u != null && t.exit_k_u !== t.exit_k) {
        const ku = Math.min(span.i + t.exit_k_u, state.daily.length - 1);
        put(barOfDay(ku, (ks) => ks[ks.length - 1]), "out: under water", long, COL.violet, "square");
      }
      if (state.chartTf === "1H" && t.status_h === "exit" && t.entry_h != null && t.exit_h != null) {
        const t0 = state.daily[span.i][0] + t.entry_h * HOUR + t.exit_h * HOUR;
        const kh = bs.findIndex((b) => b.t === t0);
        if (kh >= 0) put(kh, "out: hourly clock", long, COL.mm, "square");
      }
      markers.sort((a, b) => a.time - b.time);
      if (firstIn >= 0) {
        const from = Math.max(0, firstIn - (state.chartTf === "1H" ? 48 : 40)), to = Math.min(bs.length - 1, lastIn + (state.chartTf === "1H" ? 24 : 15));
        state.chart.timeScale().setVisibleLogicalRange({ from, to });
      }
    } else if (bs.length) {
      state.chart.timeScale().setVisibleLogicalRange({ from: Math.max(0, bs.length - 160), to: bs.length + 4 });
    }
    state.series.setMarkers(markers);
    drawRays();
    legend(t, span, bs.length);
    details(t, span, p);
  }

  function legend(t, span, n) {
    const bits = ['<span><i style="background:' + COL.gray + '"></i>not in a trade</span>',
      '<span><i style="background:' + COL.setup + '"></i>setup bar</span>', '<span><i style="background:' + COL.ref + '"></i>bar before it</span>',
      '<span><i style="background:' + COL.up + '"></i><i style="background:' + COL.down + '"></i>in the trade</span>',
      '<span><i style="background:' + COL.week + '"></i>week open</span>'];
    if (state.chartTf === "1H" && !state.hourly.length) bits.push("<span style='color:#f59e0b'>no hourly bars cached for this coin: `trade_viewer hourly --as-of ... " + state.coin + "` then `build`</span>");
    else if (state.chartTf === "1H" && t && span && state.hourly.length && state.daily[span.i][0] < state.hourly[0][0]) bits.push("<span style='color:#f59e0b'>this trade predates the hourly window (the venue serves about 208 days)</span>");
    if (!n) bits.push("<span style='color:#f59e0b'>no bars</span>");
    $("legend").innerHTML = bits.join("");
  }

  function details(t, span, p) {
    const el = $("trade");
    if (!t || !span) { el.innerHTML = '<span class="k">Pick a trade below (or press &rarr;).</span>'; return; }
    const long = t.direction === "up";
    const st = settle(t);
    const hs = tradeSpan(t, "C") || span;
    const endBar = state.daily[hs.end];
    const chips = ['<span class="chip ' + (long ? "long" : "short") + '">' + (long ? "LONG" : "SHORT") + "</span>",
      '<span class="chip tf">' + TF_LABEL[t.tf] + "</span>", '<span class="chip kind">' + KIND_LABEL[t.kind] + "</span>"];
    if (t.cls && t.cls !== "plain") chips.push('<span class="chip flag">' + t.cls + (t.stack && t.stack !== t.tf ? " " + t.stack : "") + "</span>");
    if (t.flag && t.flag !== "none") chips.push('<span class="chip flag">' + t.flag + "</span>");
    if (t.liquid) chips.push('<span class="chip tf">liquid</span>');
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
    const el = document.createElement("div");
    el.className = "card" + (k === state.sel ? " sel" : "");
    el.innerHTML = '<div class="top"><span>' + coin + '</span><span class="chip ' + (long ? "long" : "short") + '">' + (long ? "Long" : "Short") + "</span></div>" +
      '<div class="when">' + t.date + (endTxt ? " &rarr; " + endTxt : "") + "</div>" +
      '<div class="what">' + TF_LABEL[t.tf] + " " + KIND_LABEL[t.kind] + (t.cls && t.cls !== "plain" ? " &middot; " + t.cls : "") + (t.flag && t.flag !== "none" ? " &middot; " + t.flag : "") + "</div>" +
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
    const res = await fetch("data/" + entry.file);
    const d = await res.json();
    state.coin = coin; state.data = d; state.daily = d.daily; state.hourly = d.hourly;
    loadRays();
    state.dayIdx = new Map(d.daily.map((b, i) => [iso(b[0]), i]));
    state.weeks = aggregate(d.daily, "W"); state.months = aggregate(d.daily, "M");
    const wo = new Map(); for (const w of state.weeks) for (const di of w.days) wo.set(d.daily[di][0], w.o);
    state.weekOpenAt = (t) => wo.get(t - (t % DAY)) ?? null;
    state.list = filtered(d.trades);
    $("title").textContent = coin;
    $("meta").textContent = d.daily.length + " daily bars " + iso(d.daily[0][0]) + " to " + iso(d.daily[d.daily.length - 1][0]) + (d.hourly.length ? " · " + d.hourly.length + " hourly bars from " + isoH(d.hourly[0][0]) : " · no hourly bars cached") + " · " + d.trades.length + " trades · as of " + d.as_of;
    $("chartTf").querySelector('[data-v="1H"]').disabled = !d.hourly.length;
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
    // a bookmarkable address for the trade on screen: #coin=BTC&date=2025-06-17&tf=D&dir=down&view=1D
    const t = state.cur;
    const h = t ? "coin=" + encodeURIComponent(state.coin) + "&date=" + t.date + "&tf=" + t.tf + "&dir=" + t.direction + "&view=" + state.chartTf + "&book=" + state.book : state.coin ? "coin=" + encodeURIComponent(state.coin) + "&view=" + state.chartTf : "";
    history.replaceState(null, "", h ? "#" + h : location.pathname);
  }
  function fromHash() {
    const q = new URLSearchParams(location.hash.slice(1));
    return { coin: q.get("coin"), date: q.get("date"), tf: q.get("tf"), dir: q.get("dir"), view: q.get("view"), book: q.get("book") };
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
    if (!state.dates) state.dates = await (await fetch("data/dates.json")).json();
    const rows = state.dates[date] || [];
    // dates.json is a slim index; the full rows come from each coin file on demand, so filter on what it holds
    const items = [];
    for (const r of rows) {
      const [coin, direction, tf, kind] = r;
      if (!state.tf.has(tf) || !state.kind.has(kind) || !state.dir.has(direction)) continue;
      items.push({ coin, key: [date, tf, direction] });
    }
    // resolve the full rows coin by coin (cached fetches; one file per distinct coin)
    const byCoin = new Map();
    for (const it of items) { if (!byCoin.has(it.coin)) byCoin.set(it.coin, fetch("data/" + state.index.coins.find((c) => c.coin === it.coin).file).then((r) => r.json())); }
    const full = [];
    for (const it of items) {
      const d = await byCoin.get(it.coin);
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
    state.index = await (await fetch("data/index.json")).json();
    const dl = $("coinList");
    for (const c of state.index.coins) { const o = document.createElement("option"); o.value = c.coin; o.label = c.n + " trades"; dl.appendChild(o); }
    $("meta").textContent = state.index.coins.length + " coins · " + state.index.trades.toLocaleString() + " trades · as of " + state.index.as_of + " · built " + state.index.built;
    seg("chartTf", (v) => { state.chartTf = v; draw(); }, false);
    seg("fTf", () => { state.tf = setOf("fTf"); refilter(); }, true);
    seg("fKind", () => { state.kind = setOf("fKind"); refilter(); }, true);
    seg("fDir", () => { state.dir = setOf("fDir"); refilter(); }, true);
    seg("fLiq", (v, on) => { state.liquid = on; refilter(); }, true);
    seg("fT1", (v, on) => { state.hasT1 = on; refilter(); }, true);
    $("book").onchange = (e) => { state.book = e.target.value; draw(); renderCards(); };
    $("rayMode").onclick = () => setRayMode(!state.rayMode);
    $("rayClear").onclick = () => { state.rays = []; saveRays(); drawRays(); };
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
      else if (e.key === "Escape") { if (state.rayMode) setRayMode(false); else { state.sel = -1; state.cur = null; draw(); renderCards(); } }
      else if (e.key === "r" || e.key === "R") setRayMode(!state.rayMode);
      else if ((e.key === "Delete" || e.key === "Backspace") && state.rays.length) { state.rays.pop(); saveRays(); drawRays(); }
    });
    const want = fromHash();
    if (want.book && BOOK_RET[want.book]) { state.book = want.book; $("book").value = want.book; }
    const first = state.index.coins.find((c) => c.coin === (want.coin || "BTC")) || state.index.coins[0];
    $("coinBox").value = first.coin;
    await loadCoin(first.coin);
    if (want.view && ["1H", "1D", "1W", "1M"].includes(want.view)) {
      state.chartTf = want.view;
      $("chartTf").querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.v === want.view));
    }
    state.sel = want.date ? state.list.findIndex((t) => t.date === want.date && (!want.tf || t.tf === want.tf) && (!want.dir || t.direction === want.dir)) : -1;
    if (state.sel < 0) state.sel = lastSettled(state.list);
    state.cur = state.list[state.sel] || null;
    draw(); renderCards();
  }
  init().catch((e) => { $("empty").style.display = "flex"; $("empty").textContent = "failed to load: " + e; });
})();
