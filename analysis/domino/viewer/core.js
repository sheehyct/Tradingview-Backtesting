/* core.js: the run registry (the books a run declares, with roles and colours), the census
   calendar, formatting and the card geometry (prep / settle / tradeSpan / stackLevels /
   setupDays: the reference viewer's logic over the run contract's cards), plus the STRAT type of
   the last CLOSED week and month before an entry. Nothing here re-runs trade logic: every price,
   time and fill is read off the card (viewer/CONTRACT.md); the page only derives day offsets
   from the recorded times against the run's own bars. */
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
  // ladder books take the classic six colours in the run's order; grouped books share their group's colour
  const LADDER_PALETTE = ["#3b82f6", "#22c55e", "#a78bfa", "#f59e0b", "#fb923c", "#9ca3af", "#38bdf8", "#f472b6", "#34d399", "#fbbf24"];
  const GROUP_PALETTE = ["#f59e0b", "#a78bfa", "#38bdf8", "#f472b6", "#34d399", "#c084fc", "#fbbf24", "#60a5fa"];
  const ROLE_WORD = { headline: "headline", target: "target book", stop: "stop book", clock: "another clock", reference: "reference" };
  const HOW_SHORT = { target: "at its target", one_r: "one R", stop: "its stop", clock: "clock exit", cap: "marked at the cap", censored: "censored (data ends)", none: "not scored" };
  const CLS_LABEL = { exact_shared: "same price", exact_plain: "same price", near: "near, within 0.25%", within1: "within 1%", spread: "spread, more than 1% apart", plain: "plain, no fresh higher level within 1%" };
  const KIND_LABEL = { reversal: "2-2 reversal", continuation: "2-2 continuation", inside: "inside break", outside: "outside break" };
  const KIND_SHORT = { reversal: "Rev", continuation: "Cont", inside: "Inside", outside: "Outside" };
  const TF_LABEL = { D: "daily", W: "weekly", M: "monthly" };
  const TF_WORD = { D: "day", W: "week", M: "month" };
  const tfLabel = (tf) => TF_LABEL[tf] || tf;
  const tfWord = (tf) => TF_WORD[tf] || tf;
  const DASH = { 0: [], 1: [1, 3], 2: [5, 3], 3: [9, 4], 4: [2, 6] };
  const INTERVAL = { "1H": { timeUnit: "hour", count: 1 }, "1D": { timeUnit: "day", count: 1 }, "1W": { timeUnit: "week", count: 1 }, "1M": { timeUnit: "month", count: 1 } };
  const BT_CLASS = { "1": "t1", "2U": "t2u", "2D": "t2d", "3": "t3", "?": "tq" };
  const BT_WORD = { "1": "inside bar", "2U": "2 up (broke the high only)", "2D": "2 down (broke the low only)", "3": "outside bar", "?": "unknown" };

  const $ = (id) => document.getElementById(id);

  // ---------------------------------------------------------------- the run: its books, roles, colours
  const RUN = { run: null, ids: [], byId: {}, ladder: [], groups: [], head: null, ref: null, col: {}, shift: 0, session: false };
  function setRun(run) {
    RUN.run = run; RUN.ids = []; RUN.byId = {}; RUN.ladder = []; RUN.groups = []; RUN.head = null; RUN.ref = null; RUN.col = {};
    // a run on another day roll (the Globex session opens 18:00 ET, 22:00 or 23:00 UTC, and is named by the NEXT
    // calendar day) declares `clock.label_shift_hours`: the hours added to a bar's open before its calendar date is read
    // as the session's label. `clock.calendar: "session"` says sessions are sparse (no weekend, holidays), so a week or
    // month is complete when the data runs past it, not when every calendar day is present (CONTRACT.md sections 2, 4, 6)
    const clock = run.clock || {};
    RUN.shift = (Number(clock.label_shift_hours) || 0) * HOUR;
    RUN.session = clock.calendar === "session";
    let li = 0;
    for (const b of run.books || []) {
      RUN.ids.push(b.id); RUN.byId[b.id] = b;
      if (b.role === "headline" && !RUN.head) RUN.head = b.id;
      if (b.role === "reference" && !RUN.ref) RUN.ref = b.id;
      if (b.group) {
        if (!RUN.groups.includes(b.group)) RUN.groups.push(b.group);
        RUN.col[b.id] = GROUP_PALETTE[RUN.groups.indexOf(b.group) % GROUP_PALETTE.length];
      } else if (["headline", "target", "stop", "reference"].includes(b.role)) {
        RUN.ladder.push(b.id);
        RUN.col[b.id] = b.role === "reference" ? "#9ca3af" : LADDER_PALETTE[li++ % LADDER_PALETTE.length];
      } else {
        RUN.col[b.id] = GROUP_PALETTE[0];
      }
    }
    return RUN;
  }
  const getRun = () => RUN.run;
  const bookIds = () => RUN.ids.slice();
  const ladderBooks = () => RUN.ladder.slice();
  const groupNames = () => RUN.groups.slice();
  const groupBooks = (g) => RUN.ids.filter((id) => RUN.byId[id].group === g);
  const bookOf = (id) => RUN.byId[id] || null;
  const bookName = (id) => (RUN.byId[id] ? RUN.byId[id].name : id);
  const bookRule = (id) => (RUN.byId[id] ? RUN.byId[id].rule : "");
  const bookRole = (id) => (RUN.byId[id] ? RUN.byId[id].role : null);
  const bookGroup = (id) => (RUN.byId[id] ? RUN.byId[id].group || null : null);
  const bookTarget = (id) => (RUN.byId[id] ? RUN.byId[id].target || null : null);
  const bookCol = (id) => RUN.col[id] || "#9ca3af";
  const bookRes = (id) => (RUN.byId[id] && RUN.byId[id].resolution) || (RUN.run && RUN.run.clock && RUN.run.clock.resolution) || "day";
  // a book entry on a card may be known less finely than its book (CONTRACT.md section 3): the entry's own resolution wins
  const entryRes = (id, b) => (b && b.resolution) || bookRes(id);
  const headline = () => RUN.head;
  const reference = () => RUN.ref;
  // "Book A" for the house books, the name for the chance book and the grouped ones
  const bookLabel = (id) => (bookRole(id) === "reference" ? "The " + bookName(id) : "Book " + id);

  // ---------------------------------------------------------------- calendar (census rules)
  function weekStart(t) { const dse = Math.floor(t / DAY); const wd = (dse + 4) % 7; return (dse - (wd + 6) % 7) * DAY; }
  function monthStart(t) { const d = new Date(t * 1000); return Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1) / 1000; }
  function nextMonth(t) { const d = new Date(t * 1000); return Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 1) / 1000; }
  // the calendar date a bar or a time is labelled with: its open plus the run's label shift (0 for a 00:00 UTC day)
  const dayFloor = (t) => t - (t % DAY);
  const labelOf = (t) => iso(t + RUN.shift);
  function aggregate(daily, tf, shipped) {
    // week / month buckets of the daily bars, keyed by the LABEL date (so a Sunday-evening Globex open sits in Monday's
    // week); `shipped` = the run's own weekly or monthly bars, whose open / high / low / close replace the aggregate
    // when a bar's label week (month) matches (the exchange's bar, not a re-aggregation)
    const start = tf === "W" ? weekStart : monthStart;
    const out = [];
    daily.forEach((b, i) => {
      const k = start(b[0] + RUN.shift);
      if (!out.length || out[out.length - 1].t !== k) {
        out.push({ t: k, end: tf === "W" ? k + 7 * DAY : nextMonth(k), o: b[1], h: b[2], l: b[3], c: b[4], v: b[5], days: [i] });
      } else {
        const x = out[out.length - 1];
        x.h = Math.max(x.h, b[2]); x.l = Math.min(x.l, b[3]); x.c = b[4]; x.v += b[5]; x.days.push(i);
      }
    });
    if (shipped && shipped.length) {
      const byKey = new Map(shipped.map((s) => [start(s[0] + RUN.shift), s]));
      for (const x of out) { const s = byKey.get(x.t); if (s) { x.o = s[1]; x.h = s[2]; x.l = s[3]; x.c = s[4]; x.v = s[5]; x.shipped = true; } }
    }
    const lastEnd = daily.length ? dayFloor(daily[daily.length - 1][0] + RUN.shift) + DAY : 0;
    out.forEach((x, n) => {
      // complete = the bar is closed: the data runs past its end; a 24/7 run also wants every calendar day present
      // (a missing day is a data gap there); a session calendar is complete once a later bucket has begun
      const closed = x.end <= lastEnd || (RUN.session && n < out.length - 1);
      x.complete = closed && (RUN.session || x.days.length === (x.end - x.t) / DAY);
    });
    return out;
  }
  function makeCalendar(d) {
    // per-instrument day index + week / month buckets + the week's open for any time; `d` is { daily, hourly } or a run
    // file ({ bars }). A time belongs to the SESSION whose open is the latest at or before it (an hour of a Globex
    // session that crosses midnight UTC stays with its session); the day index is keyed by the label date.
    const bars = d.bars || {};
    const daily = d.daily || bars["1d"] || [], hourly = d.hourly || bars["1h"] || [];
    const weeks = aggregate(daily, "W", bars["1w"]), months = aggregate(daily, "M", bars["1M"]);
    const opens = daily.map((b) => b[0]);
    const sessionOf = (t) => {
      if (t == null || !opens.length || t < opens[0]) return null;
      let lo = 0, hi = opens.length - 1;
      while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (opens[mid] <= t) lo = mid; else hi = mid - 1; }
      return lo;
    };
    const weekOpen = new Array(daily.length), firstOfWeek = new Set();
    for (const w of weeks) { for (const di of w.days) weekOpen[di] = w.o; firstOfWeek.add(w.days[0]); }
    return { daily, hourly, dayIdx: new Map(daily.map((b, i) => [labelOf(b[0]), i])), weeks, months, sessionOf, firstOfWeek,
      dateOf: (i) => (i == null || !daily[i] ? null : labelOf(daily[i][0])),
      weekOpenAt: (t) => { const i = sessionOf(t); return i == null || weekOpen[i] == null ? null : weekOpen[i]; } };
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

  // ---------------------------------------------------------------- the card, prepared for the page
  function prep(t, cal) {
    // the page's derived view of a card: flat aliases for the setup fields the words and the filters read, and the
    // day offset of every recorded time against the run's own bars (the inverse of the exporter: an offset is bars, not
    // calendar days, because the census fills no gaps). Nothing here changes what the card says.
    const t0 = t.entry.t;
    // the entry's label date: the session holding the entry time (an hour-resolution entry inside a Globex session
    // still labels as that session); without bars, the shifted calendar date
    const s0 = cal ? cal.sessionOf(t0) : null;
    t.date = s0 != null ? cal.dateOf(s0) : labelOf(t0);
    t.tf = t.bar; t.level = t.entry.price; t.stop = t.far == null ? null : t.far;
    t.cls = t.class == null ? null : t.class;
    const ex = t.extras || {};
    t.near_tf = ex.near_tf == null ? null : ex.near_tf; t.liquid = !!ex.liquid; t.flag = ex.flag == null ? "none" : ex.flag;
    t.anchor = ex.anchor == null ? null : ex.anchor; t.dex = ex.dex == null ? null : ex.dex; t.one_r_raw = ex.one_r_raw == null ? null : ex.one_r_raw;
    // a session tape can open past the trigger (the bench's extras.gap: "open" / "untraded"); run one's cards carry neither key
    t.gap = ex.gap == null ? null : ex.gap; t.session_open = ex.session_open == null ? null : ex.session_open;
    const cx = t.context || {}, tv = t.travel || {};
    t.w_support = cx.week_side == null ? null : cx.week_side; t.m_support = cx.month_side == null ? null : cx.month_side;
    t.mfe_x = tv.mfe == null ? null : tv.mfe; t.mae_x = tv.mae == null ? null : tv.mae; t.next_bar = tv.next_bar == null ? null : tv.next_bar;
    t.window = tv.window || RUN.head;
    const i = cal ? cal.dayIdx.get(t.date) : null;
    const kOf = (ts) => {
      // the offset in BARS (sessions) from the entry's bar to the bar holding `ts`; calendar days only without bars
      if (ts == null) return null;
      if (cal && i != null) { const j = cal.sessionOf(ts); if (j != null) return j - i; }
      return Math.floor((ts - t0) / DAY);
    };
    t.kOf = kOf;
    const byName = {}; for (const tg of t.targets || []) byName[tg.name] = tg;
    for (const [name, key, kk] of [["T1", "t1", "t1_k"], ["T2", "t2", "t2_k"], ["T3", "t3", "t3_k"], ["mm", "mm_t1", "mm1_k"]]) {
      const x = byName[name];
      t[key] = x ? x.price : null; t[key + "_src"] = x ? x.source : null; t[kk] = x ? kOf(x.touched) : null;
    }
    const tc = t.touches || {};
    t.one_r_k = kOf(tc.one_r); t.stop_k = kOf(tc.far);
    t.stackList = (t.stack || []).map((s) => (typeof s === "string" ? s : s.bar));
    t.stackStr = t.stackList.length ? t.stackList.join("+") : t.tf;
    t.byBook = {};
    for (const b of t.books || []) t.byBook[b.id] = Object.assign({}, b, { k: kOf(b.at), entry_k: kOf(b.entry) });
    return t;
  }
  function targetName(t, price) {
    if (price == null) return null;
    const tg = (t.targets || []).find((x) => x.price != null && Math.abs(x.price - price) <= Math.abs(price) * 1e-9);
    return tg ? tg.name : null;
  }
  function howWords(t, b) {
    // the ladder's "how it left" words from the vocabulary; the book's rule says what they mean for that book
    if (b.how === "target") { const n = targetName(t, b.price); return "all out at " + (n || "its target"); }
    if (b.how === "none") return "not scored" + (b.note ? ": " + b.note : "");
    return HOW_SHORT[b.how] || b.how;
  }

  // ---------------------------------------------------------------- trade geometry (from the card)
  function settle(t, book) {
    const id = book || RUN.head;
    const b = t.byBook ? t.byBook[id] : null;
    const base = { book: id, k: 0, ret: null, target: false, stop: false, missing: true, price: null, at: null, t: null, entry: null, res: entryRes(id, b) };
    if (!b) return Object.assign(base, { absent: true, how: "does not apply to this trade" });
    if (b.how === "none" || b.how === "censored") return Object.assign(base, { how: howWords(t, b), note: b.note || null });
    const touch = b.how === "target" || b.how === "one_r" || b.how === "stop";
    // `at` is the recorded price the book left on (the target, one R or the stop as the engine wrote it): the marker
    // search uses it; a clock exit's price is the bar's close, found by time (TVB-39 audit F4)
    return { book: id, k: b.k == null ? 0 : b.k, ret: b.ret, target: b.how === "target" || b.how === "one_r", stop: b.how === "stop", missing: false,
      how: howWords(t, b), price: b.price == null ? null : b.price, at: touch ? b.price : null, t: b.at == null ? null : b.at, entry: b.entry == null ? null : b.entry,
      cap: b.how === "cap", clock: b.how === "clock", hit: b.hit == null ? null : b.hit, note: b.note || null, res: entryRes(id, b) };
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
    for (const tf of (t.stackList && t.stackList.length ? t.stackList : [t.tf])) {
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
  function stackSubset(t, levels) {
    // TVB-39 audit F7: `stack` lists every level that broke on the entry day; the class describes a PAIR. For a daily
    // card it is the daily level against the nearest fresh higher level at entry (`near_tf`, chance.entry_class); for a
    // weekly / monthly card it is the unit's own level against the daily level (chance.stack_class). The converged
    // stack is that pair when both broke; the other same-day breaks are listed apart with their distance from the entry.
    // Read from the card (near_tf, class, bar): no band is re-derived here.
    const long = t.direction === "up";
    const out = levels.map((l) => ({ ...l, gap: t.level ? (long ? l.price - t.level : t.level - l.price) / t.level * 100 : null }));
    const pairTf = t.tf === "D" ? (t.cls && t.cls !== "plain" && t.cls !== "spread" ? t.near_tf : null) : "D";
    const conv = out.filter((l) => l.tf === t.tf || (pairTf != null && l.tf === pairTf));
    const far = out.filter((l) => !conv.includes(l));
    return { conv, far };
  }
  function stackWords(t, levels) {
    // the stack chip's text: the converged subset with its class, then the other same-day breaks with their distance
    const { conv, far } = stackSubset(t, levels);
    const convTxt = conv.length > 1 ? conv.map((l) => l.tf).join("+") + " " + (CLS_LABEL[t.cls] || t.cls) : null;
    const farTxt = far.map((l) => l.tf + " " + (l.gap == null ? "" : (l.gap >= 0 ? "+" : "") + l.gap.toFixed(2) + "%") + " beyond, broke the same day");
    return { conv, far, text: [convTxt, ...farTxt].filter(Boolean).join("; ") || t.stackStr };
  }
  function cellIndex(bs, tMs) {
    // TVB-40 audit F2: the bar whose axis cell holds the time (the last bar opening at or before it), not the bar whose
    // open is nearest; a candle is drawn centred in its cell, so "nearest open" flips to the next bar past the midpoint
    let k = 0;
    for (let i = 0; i < bs.length; i++) { if (bs[i].t * MS <= tMs) k = i; else break; }
    return k;
  }
  // one R as the card records it (null when the engine's one R is unreachable, e.g. below zero for a short)
  function oneR(t) { return t.one_r == null ? null : t.one_r; }

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
    if (bi < 2 || !buckets[bi - 1].complete || !buckets[bi - 2].complete) return { code: "?", title: "no two complete " + tfLabel(tf) + " bars before the entry (the data starts too late)" };
    const bar = buckets[bi - 1], prev = buckets[bi - 2];
    const code = barType(bar, prev);
    return { code, bar, prev, title: "last closed " + tfLabel(tf) + " bar (" + iso(bar.t) + " to " + iso(bar.end - DAY) + "): " + BT_WORD[code] +
      " against the " + tfLabel(tf) + " bar before it (high " + bar.h + " vs " + prev.h + ", low " + bar.l + " vs " + prev.l + ")" };
  }
  function btChip(tf, r) { return '<span class="chip bt ' + BT_CLASS[r.code] + '" title="' + esc(r.title) + '">' + tf + " " + r.code + "</span>"; }

  DV.core = { DAY, HOUR, CAP, MS, COL, ROLE_WORD, HOW_SHORT, CLS_LABEL, KIND_LABEL, KIND_SHORT, TF_LABEL, TF_WORD, tfLabel, tfWord, DASH, INTERVAL, BT_CLASS, BT_WORD, $,
    setRun, getRun, bookIds, ladderBooks, groupNames, groupBooks, bookOf, bookName, bookRule, bookRole, bookGroup, bookTarget, bookCol, bookRes, entryRes, headline, reference, bookLabel,
    weekStart, monthStart, nextMonth, aggregate, makeCalendar, labelOf, dayFloor, iso, isoH, dateMs, longDate, shortDate, monthName, weekdayOf, decimalsOf, precisionFor, fmtPrice, fmtPct, fmtUsd, fmtUsd0, cls, esc,
    prep, targetName, howWords, settle, tradeSpan, stackLevels, setupDays, oneR, barType, htfType, btChip, stackSubset, stackWords, cellIndex };
})(window.DV);
