/* stats.js: arithmetic on the recorded rows for the Compare tab and the calendar. Equal-size
   trades at the size box, summed by entry date; no leverage, fees or funding (same as the receipt). */
window.DV = window.DV || {};
(function (DV) {
  "use strict";
  const C = DV.core;
  const { BOOKS, BOOK_RET, BOOK_HIT, BOOK_DAYS, dateMs } = C;

  function hitOf(t, book) {
    if (book === "ref") return t.out5 === "one_r";
    const k = BOOK_HIT[book];
    return k ? !!t[k] : null;
  }
  function daysOf(t, book) {
    if (book === "C") return t.exit_k != null ? t.exit_k : t.days != null ? t.days : null;
    const v = t[BOOK_DAYS[book]];
    return v == null ? null : v;
  }
  function median(sorted) { const n = sorted.length; if (!n) return null; return n % 2 ? sorted[(n - 1) / 2] : (sorted[n / 2 - 1] + sorted[n / 2]) / 2; }

  function maxDrawdown(values) {
    // peak-to-trough on a sequence of end-of-day equity values, the peak never below zero (the engine's clip)
    let peak = 0, dd = 0;
    for (const v of values) { peak = Math.max(peak, v); dd = Math.max(dd, peak - v); }
    return dd;
  }
  function monthSummary(map, startTs, endTs) {
    // TVB-40 audit F5: a month's trade count, the count WITH a recorded result, the dollar total and the average over
    // the filled rows only (a censored row is not a zero return); avg is null when nothing is filled
    let n = 0, filled = 0, usd = 0, pct = 0;
    for (const [date, e] of map) { const ts = dateMs(date) / 1000; if (ts < startTs || ts >= endTs) continue; n += e.n; filled += e.filled; usd += e.usd; pct += e.sum; }
    return { n, filled, usd, avg: filled ? pct / filled : null };
  }
  function bookStats(items, book, size) {
    // one book over a list of {coin, t}: the equity curve by entry date and the headline figures. The drawdown is
    // measured on the completed daily sums, as the engine's book_stats does (TVB-40 audit F1): same-day trades have
    // no observed order, so no intra-day path is scored, and the number is the same whatever the table's sort
    const rows = items.map((it) => ({ t: it.t, coin: it.coin, r: it.t[BOOK_RET[book]] })).filter((x) => x.r != null);
    rows.sort((a, b) => (a.t.date < b.t.date ? -1 : a.t.date > b.t.date ? 1 : a.coin < b.coin ? -1 : a.coin > b.coin ? 1 : (a.t._i || 0) - (b.t._i || 0)));
    let sum = 0, wins = 0, cum = 0, targets = 0, withTarget = 0;
    const curve = [], rets = [], days = [];
    let last = null;
    for (const x of rows) {
      cum += x.r / 100 * size; sum += x.r; if (x.r > 0) wins++; rets.push(x.r);
      if (x.t.date === last) curve[curve.length - 1].v = cum; else curve.push({ t: dateMs(x.t.date), v: cum });
      last = x.t.date;
      const h = hitOf(x.t, book);
      if (h != null) { withTarget++; if (h) targets++; }
      const d = daysOf(x.t, book); if (d != null) days.push(d);
    }
    const dd = maxDrawdown(curve.map((pt) => pt.v));
    rets.sort((a, b) => a - b); days.sort((a, b) => a - b);
    const filled = rows.length;
    const avgWin = rets.filter((r) => r > 0), avgLoss = rets.filter((r) => r < 0);
    return {
      book, n: items.length, filled, win: filled ? wins / filled : null, avg: filled ? sum / filled : null, med: median(rets), total: cum, maxDD: dd,
      target: withTarget ? targets / withTarget : null, medDays: median(days), curve,
      avgWin: avgWin.length ? avgWin.reduce((a, b) => a + b, 0) / avgWin.length : null, avgLoss: avgLoss.length ? avgLoss.reduce((a, b) => a + b, 0) / avgLoss.length : null,
      best: rets.length ? rets[rets.length - 1] : null, worst: rets.length ? rets[0] : null,
    };
  }
  function allBooks(items, size) { const out = {}; for (const b of BOOKS) out[b] = bookStats(items, b, size); return out; }

  function bySetup(items) {
    // rows: unit timeframe x setup kind; columns: each book's average, and D5 minus the chance book paired on the rows that have both
    const groups = new Map();
    const key = (t) => t.tf + "|" + t.kind;
    for (const it of items) { const k = key(it.t); if (!groups.has(k)) groups.set(k, []); groups.get(k).push(it.t); }
    const order = ["D|reversal", "D|continuation", "D|inside", "D|outside", "W|reversal", "W|continuation", "W|inside", "W|outside", "M|reversal", "M|continuation", "M|inside", "M|outside"];
    const line = (label, ts) => {
      const row = { label, n: ts.length, avg: {}, swap: null, swapN: 0 };
      for (const b of BOOKS) { const v = ts.map((t) => t[BOOK_RET[b]]).filter((x) => x != null); row.avg[b] = v.length ? v.reduce((a, c) => a + c, 0) / v.length : null; row["n" + b] = v.length; }
      const pairs = ts.filter((t) => t.ret_D5 != null && t.ret5 != null);
      row.swapN = pairs.length;
      row.swap = pairs.length ? pairs.reduce((a, t) => a + (t.ret_D5 - t.ret5), 0) / pairs.length : null;
      return row;
    };
    const rows = [line("all shown", items.map((it) => it.t))];
    for (const k of order) if (groups.has(k)) { const [tf, kind] = k.split("|"); rows.push(line(C.TF_LABEL[tf] + " " + C.KIND_LABEL[kind], groups.get(k))); }
    return rows;
  }

  function histogram(items, bookA, bookB, lo, hi) {
    // one-percent bins from lo to hi (the ends collect everything beyond), as a share of each book's filled trades
    const bins = [];
    for (let b = lo; b < hi; b++) bins.push({ bin: (b >= 0 ? "+" : "") + b, lo: b, a: 0, b: 0 });
    const count = (book, field) => {
      let n = 0;
      for (const it of items) {
        const r = it.t[BOOK_RET[book]]; if (r == null) continue; n++;
        const idx = Math.min(bins.length - 1, Math.max(0, Math.floor(r) - lo));
        bins[idx][field]++;
      }
      if (n) for (const x of bins) x[field] = x[field] / n * 100;
    };
    count(bookA, "a"); count(bookB, "b");
    return bins;
  }

  function calendarDays(items, book, size) {
    // date -> { n, sum (percent), usd, items }
    const map = new Map();
    for (const it of items) {
      const r = it.t[BOOK_RET[book]];
      let e = map.get(it.t.date);
      if (!e) { e = { n: 0, sum: 0, usd: 0, filled: 0, items: [] }; map.set(it.t.date, e); }
      e.n++; e.items.push(it);
      if (r != null) { e.sum += r; e.usd += r / 100 * size; e.filled++; }
    }
    return map;
  }
  function fromUniverse(u) {
    // data/universe.json (trade_viewer build): one columnar table of every coin's rows, decoded into the same row
    // shape the per-coin files use for the fields the Compare tab and the calendar read (nothing else is there)
    const c = u.cols, K = u.codes, epoch = dateMs(u.epoch) / 1000, out = new Array(u.n);
    const int = (v) => v == null || v < 0 ? null : v;
    const flag = (v) => v == null || v < 0 ? null : v === 1;
    for (let i = 0; i < u.n; i++) {
      out[i] = {
        _i: i, coin: u.coins[c.coin[i]], date: C.iso(epoch + c.date[i] * C.DAY),
        tf: K.tf[c.tf[i]], kind: K.kind[c.kind[i]], direction: K.dir[c.dir[i]], status: K.status[c.status[i]], out5: K.out5[c.out5[i]],
        cls: K.cls[c.cls[i]], flag: K.flag[c.flag[i]], liquid: c.liquid[i] === 1, t1: c.t1[i] === 1 ? 1 : null, exit_k: int(c.exit_k[i]),
        ret_C: c.ret_C[i], ret_A: c.ret_A[i], ret_B: c.ret_B[i], ret_D: c.ret_D[i], ret_D5: c.ret_D5[i], ret5: c.ret5[i],
        hit_A: flag(c.hit_A[i]), hit_B: flag(c.hit_B[i]), hit_D: flag(c.hit_D[i]), hit_D5: flag(c.hit_D5[i]),
        days_A: int(c.days_A[i]), days_B: int(c.days_B[i]), days_D: int(c.days_D[i]), days_D5: int(c.days_D5[i]), days_ref: int(c.days_ref[i]),
      };
    }
    return out;
  }

  DV.stats = { bookStats, allBooks, bySetup, histogram, calendarDays, fromUniverse, hitOf, daysOf, maxDrawdown, monthSummary };
})(window.DV);
