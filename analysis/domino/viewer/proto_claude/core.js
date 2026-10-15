/* core.js: constants, the census calendar, formatting and the row geometry (settle / tradeSpan /
   stackLevels / setupDays: the reference viewer's logic with the calendar passed in instead of
   read from a global), plus the STRAT type of the last CLOSED week and month before an entry.
   Nothing here re-runs trade logic: every price, day and fill is read off the row. */
window.DV = window.DV || {};
(function (DV) {
  "use strict";
  const DAY = 86400, HOUR = 3600, CAP = 20, MS = 1000;
  const COL = {
    gray: "#4b5160", grayWick: "#3d4350",
    up: "#22c55e", down: "#ef4444",
    setup: "#f59e0b", ref: "#b7791f",
    level: "#3b82f6", exit: "#f43f5e", target: "#22c55e", oneR: "#a78bfa", stop: "#9ca3af", mm: "#f59e0b",
    week: "#38bdf8", violet: "#a78bfa",
  };
  const BOOKS = ["C", "A", "B", "D", "D5", "ref"];
  const BOOK_RET = { C: "ret_C", A: "ret_A", B: "ret_B", D: "ret_D", D5: "ret_D5", ref: "ret5" };
  const BOOK_HIT = { A: "hit_A", B: "hit_B", D: "hit_D", D5: "hit_D5" };
  const BOOK_DAYS = { A: "days_A", B: "days_B", D: "days_D", D5: "days_D5", ref: "days_ref" };
  const BOOK_NAME = { C: "C: exit only", A: "A: all out at T1", B: "B: hold through T2", D: "D: one R or the exit", D5: "D5: one R or the exit, 5 bars", ref: "Chance book: setup-bar stop" };
  const BOOK_SHORT = { C: "exit only", A: "all out at T1", B: "hold through T2", D: "one R or the exit", D5: "one R or the exit, 5 bars", ref: "chance book" };
  const BOOK_LINE = {
    C: "No target. Hold until a daily close goes against the trade with the week against it at that close.",
    A: "Everything out at T1, the pattern's own magnitude. Otherwise the exit.",
    B: "Hold through T2 with the exit live. T1 is not a decision.",
    D: "One R or the exit, whichever comes first, inside the 20-day cap.",
    D5: "One R or the exit inside five bars: the chance book's own horizon, so only the stop differs.",
    ref: "The chance book itself: one R or the setup-bar stop, marked at bar five.",
  };
  const BOOK_COL = { C: "#3b82f6", A: "#22c55e", B: "#a78bfa", D: "#f59e0b", D5: "#fb923c", ref: "#9ca3af" };
  const CLS_LABEL = { exact_shared: "same price", exact_plain: "same price", near: "near, within 0.25%", within1: "within 1%", spread: "spread, more than 1% apart" };
  const KIND_LABEL = { reversal: "2-2 reversal", continuation: "2-2 continuation", inside: "inside break", outside: "outside break" };
  const KIND_SHORT = { reversal: "Rev", continuation: "Cont", inside: "Inside", outside: "Outside" };
  const TF_LABEL = { D: "daily", W: "weekly", M: "monthly" };
  const TF_WORD = { D: "day", W: "week", M: "month" };
  const DASH = { 0: [], 1: [1, 3], 2: [5, 3], 3: [9, 4], 4: [2, 6] };
  const INTERVAL = { "1H": { timeUnit: "hour", count: 1 }, "1D": { timeUnit: "day", count: 1 }, "1W": { timeUnit: "week", count: 1 }, "1M": { timeUnit: "month", count: 1 } };
  const BT_CLASS = { "1": "t1", "2U": "t2u", "2D": "t2d", "3": "t3", "?": "tq" };
  const BT_WORD = { "1": "inside bar", "2U": "2 up (broke the high only)", "2D": "2 down (broke the low only)", "3": "outside bar", "?": "unknown" };

  const $ = (id) => document.getElementById(id);

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
  function makeCalendar(d) {
    // per-coin day index + week / month buckets + the week's open for any day
    const weeks = aggregate(d.daily, "W"), months = aggregate(d.daily, "M");
    const wo = new Map(); for (const w of weeks) for (const di of w.days) wo.set(d.daily[di][0], w.o);
    return { daily: d.daily, hourly: d.hourly || [], dayIdx: new Map(d.daily.map((b, i) => [iso(b[0]), i])), weeks, months, weekOpenAt: (t) => wo.get(t - (t % DAY)) ?? null };
  }
  const iso = (t) => new Date(t * 1000).toISOString().slice(0, 10);
  const isoH = (t) => new Date(t * 1000).toISOString().slice(0, 16).replace("T", " ");
  const dateMs = (s) => Date.parse(s + "T00:00:00Z");
  function longDate(s) { return new Date(s + "T00:00:00Z").toLocaleDateString("en-US", { timeZone: "UTC", month: "long", day: "numeric", year: "numeric" }); }
  function shortDate(s) { return new Date(s + "T00:00:00Z").toLocaleDateString("en-US", { timeZone: "UTC", month: "short", day: "numeric" }); }
  function monthName(y, m) { return new Date(Date.UTC(y, m, 1)).toLocaleDateString("en-US", { timeZone: "UTC", month: "long", year: "numeric" }); }
  function weekdayOf(s) { return new Date(s + "T00:00:00Z").toLocaleDateString("en-US", { timeZone: "UTC", weekday: "long" }); }

  // ---------------------------------------------------------------- formatting
  function decimalsOf(x) { if (x == null) return 0; const s = String(x); if (s.includes("e")) return 8; const i = s.indexOf("."); return i < 0 ? 0 : Math.min(8, s.length - i - 1); }
  function precisionFor(daily, trade) {
    let p = 2;
    for (const b of daily.slice(-60)) p = Math.max(p, decimalsOf(b[4]));
    if (trade) for (const k of ["level", "t1", "stop"]) p = Math.max(p, decimalsOf(trade[k]));
    return Math.min(p, 8);
  }
  function fmtPrice(x, p) { return x == null ? "-" : Number(x).toLocaleString("en-US", { minimumFractionDigits: p, maximumFractionDigits: p }); }
  function fmtPct(x, d) { if (x == null) return "n/a"; const s = x >= 0 ? "+" : ""; return s + x.toFixed(d == null ? 2 : d) + "%"; }
  function fmtUsd(x, size) { if (x == null) return ""; const v = x / 100 * size; const s = v >= 0 ? "+" : "-"; return s + Math.abs(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " USD"; }
  function fmtUsd0(v) { if (v == null) return "-"; const s = v >= 0 ? "+" : "-"; return s + Math.abs(v).toLocaleString("en-US", { maximumFractionDigits: 0 }); }
  const cls = (x) => x == null ? "flat" : x > 0 ? "pos" : x < 0 ? "neg" : "flat";
  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");

  // ---------------------------------------------------------------- trade geometry (from the row)
  function settle(t, book) {
    const b = book || "C";
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
  function tradeSpan(t, book, cal) {
    const i = cal.dayIdx.get(t.date);
    if (i == null) return null;
    const end = Math.min(i + settle(t, book).k, cal.daily.length - 1);
    return { i, end };
  }
  function stackLevels(t, i, cal) {
    const long = t.direction === "up";
    const out = [];
    for (const tf of (t.stack || t.tf).split("+")) {
      let bar = null;
      if (tf === "D") { if (i - 1 >= 0) bar = { h: cal.daily[i - 1][2], l: cal.daily[i - 1][3] }; }
      else { const buckets = tf === "W" ? cal.weeks : cal.months; const bi = buckets.findIndex((b) => b.days.includes(i)); if (bi > 0) bar = buckets[bi - 1]; }
      if (bar) out.push({ tf, price: long ? bar.h : bar.l });
    }
    return out;
  }
  function setupDays(t, i, cal) {
    const setup = new Set(), ref = new Set();
    if (t.tf === "D") { if (i - 1 >= 0) setup.add(i - 1); if (i - 2 >= 0) ref.add(i - 2); return { setup, ref }; }
    const buckets = t.tf === "W" ? cal.weeks : cal.months;
    const bi = buckets.findIndex((b) => b.days.includes(i));
    if (bi > 0) buckets[bi - 1].days.forEach((d) => setup.add(d));
    if (bi > 1) buckets[bi - 2].days.forEach((d) => ref.add(d));
    return { setup, ref };
  }
  function oneR(t) { if (t.stop == null || t.level == null) return null; const r = Math.abs(t.level - t.stop); return t.direction === "up" ? t.level + r : t.level - r; }

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
  function btChip(tf, r) { return '<span class="chip bt ' + BT_CLASS[r.code] + '" title="' + esc(r.title) + '">' + tf + " " + r.code + "</span>"; }

  DV.core = { DAY, HOUR, CAP, MS, COL, BOOKS, BOOK_RET, BOOK_HIT, BOOK_DAYS, BOOK_NAME, BOOK_SHORT, BOOK_LINE, BOOK_COL, CLS_LABEL, KIND_LABEL, KIND_SHORT,
    TF_LABEL, TF_WORD, DASH, INTERVAL, BT_CLASS, BT_WORD, $, weekStart, monthStart, nextMonth, aggregate, makeCalendar, iso, isoH, dateMs, longDate, shortDate,
    monthName, weekdayOf, decimalsOf, precisionFor, fmtPrice, fmtPct, fmtUsd, fmtUsd0, cls, esc, settle, tradeSpan, stackLevels, setupDays, oneR, barType, htfType, btChip };
})(window.DV);
