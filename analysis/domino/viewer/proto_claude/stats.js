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

  function bookStats(items, book, size) {
    // one book over a list of {coin, t}: the equity curve by entry date and the headline figures
    // by entry date; same-day trades in the file's own order (the engine's), so the drawdown is the same whatever the table's sort
    const rows = items.map((it) => ({ t: it.t, coin: it.coin, r: it.t[BOOK_RET[book]] })).filter((x) => x.r != null);
    rows.sort((a, b) => (a.t.date < b.t.date ? -1 : a.t.date > b.t.date ? 1 : a.coin < b.coin ? -1 : a.coin > b.coin ? 1 : (a.t._i || 0) - (b.t._i || 0)));
    let sum = 0, wins = 0, peak = 0, dd = 0, cum = 0, targets = 0, withTarget = 0;
    const curve = [], rets = [], days = [];
    let last = null;
    for (const x of rows) {
      cum += x.r / 100 * size; sum += x.r; if (x.r > 0) wins++; rets.push(x.r);
      peak = Math.max(peak, cum); dd = Math.max(dd, peak - cum);
      if (x.t.date === last) curve[curve.length - 1].v = cum; else curve.push({ t: dateMs(x.t.date), v: cum });
      last = x.t.date;
      const h = hitOf(x.t, book);
      if (h != null) { withTarget++; if (h) targets++; }
      const d = daysOf(x.t, book); if (d != null) days.push(d);
    }
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
  function calendarAll(dates, filt, size) {
    // the all-coins calendar from dates.json: [coin, direction, tf, kind, ret_C, status] per trade, book C only
    const map = new Map();
    for (const date in dates) {
      for (const r of dates[date]) {
        if (!filt.tf.has(r[2]) || !filt.kind.has(r[3]) || !filt.dir.has(r[1])) continue;
        let e = map.get(date);
        if (!e) { e = { n: 0, sum: 0, usd: 0, filled: 0, items: [] }; map.set(date, e); }
        e.n++;
        if (r[4] != null) { e.sum += r[4]; e.usd += r[4] / 100 * size; e.filled++; }
      }
    }
    return map;
  }

  DV.stats = { bookStats, allBooks, bySetup, histogram, calendarDays, calendarAll, hitOf, daysOf };
})(window.DV);
