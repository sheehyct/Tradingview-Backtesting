/* stats.js: arithmetic on the recorded cards for the Compare tab and the calendar. Equal-size
   trades at the size box, summed by entry date; no leverage, fees or funding (same as the receipt).
   Every figure reads a book entry on the card (ret / how / k / hit); the books are the run's. */
window.DV = window.DV || {};
(function (DV) {
  "use strict";
  const C = DV.core;
  const { dateMs } = C;

  const entry = (t, book) => (t.byBook ? t.byBook[book] : null) || null;
  function retOf(t, book) { const b = entry(t, book); return b && b.ret != null ? b.ret : null; }
  function hitOf(t, book) { const b = entry(t, book); return b && b.hit != null ? !!b.hit : null; }
  function daysOf(t, book) { const b = entry(t, book); return b && b.ret != null && b.k != null ? b.k : null; }
  function howOf(t, book) { const b = entry(t, book); return b ? b.how : null; }
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
    const rows = items.map((it) => ({ t: it.t, coin: it.coin, r: retOf(it.t, book) })).filter((x) => x.r != null);
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
    // "at target" is conditional: the share of the filled trades that HAD a target (hit is null where the book has
    // none) and left there; withTarget is that denominator and targetAll the share of every filled trade, so the
    // page can show the one it names (TVB-42 audit F6)
    return {
      book, n: items.length, filled, win: filled ? wins / filled : null, avg: filled ? sum / filled : null, med: median(rets), total: cum, maxDD: dd,
      target: withTarget ? targets / withTarget : null, withTarget, targets, targetAll: filled ? targets / filled : null, medDays: median(days), curve,
      avgWin: avgWin.length ? avgWin.reduce((a, b) => a + b, 0) / avgWin.length : null, avgLoss: avgLoss.length ? avgLoss.reduce((a, b) => a + b, 0) / avgLoss.length : null,
      best: rets.length ? rets[rets.length - 1] : null, worst: rets.length ? rets[0] : null,
    };
  }
  function allBooks(items, size) { const out = {}; for (const b of C.ladderBooks()) out[b] = bookStats(items, b, size); return out; }

  // the stop swap: the run's five-bar one-R book against its reference, paired on the rows that have both (the
  // management book's H2); only when the run declares both ids
  function swapPair() { const ids = C.bookIds(); return ids.includes("D5") && ids.includes("ref") ? ["D5", "ref"] : null; }

  function bySetup(items) {
    // rows: unit timeframe x setup kind; columns: each ladder book's average, and the stop swap paired on the rows that have both
    const books = C.ladderBooks(), pair = swapPair();
    const groups = new Map();
    const key = (t) => t.tf + "|" + t.kind;
    for (const it of items) { const k = key(it.t); if (!groups.has(k)) groups.set(k, []); groups.get(k).push(it.t); }
    const units = (C.getRun() && C.getRun().units) || ["D", "W", "M"], kinds = ["reversal", "continuation", "inside", "outside"];
    const order = []; for (const u of units) for (const k of kinds) order.push(u + "|" + k);
    const line = (label, ts) => {
      const row = { label, n: ts.length, avg: {}, swap: null, swapN: 0 };
      for (const b of books) { const v = ts.map((t) => retOf(t, b)).filter((x) => x != null); row.avg[b] = v.length ? v.reduce((a, c) => a + c, 0) / v.length : null; row["n" + b] = v.length; }
      if (pair) {
        const pairs = ts.filter((t) => retOf(t, pair[0]) != null && retOf(t, pair[1]) != null);
        row.swapN = pairs.length;
        row.swap = pairs.length ? pairs.reduce((a, t) => a + (retOf(t, pair[0]) - retOf(t, pair[1])), 0) / pairs.length : null;
      }
      return row;
    };
    const rows = [line("all shown", items.map((it) => it.t))];
    for (const k of order) if (groups.has(k)) { const [tf, kind] = k.split("|"); rows.push(line(C.tfLabel(tf) + " " + (C.KIND_LABEL[kind] || kind), groups.get(k))); }
    return rows;
  }

  function histogram(items, bookA, bookB, lo, hi) {
    // one-percent bins from lo to hi (the ends collect everything beyond), as a share of each book's filled trades
    const bins = [];
    for (let b = lo; b < hi; b++) bins.push({ bin: (b >= 0 ? "+" : "") + b, lo: b, a: 0, b: 0 });
    const count = (book, field) => {
      let n = 0;
      for (const it of items) {
        const r = retOf(it.t, book); if (r == null) continue; n++;
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
      const r = retOf(it.t, book);
      let e = map.get(it.t.date);
      if (!e) { e = { n: 0, sum: 0, usd: 0, filled: 0, items: [] }; map.set(it.t.date, e); }
      e.n++; e.items.push(it);
      if (r != null) { e.sum += r; e.usd += r / 100 * size; e.filled++; }
    }
    return map;
  }
  function fromUniverse(u) {
    // runs/<id>/universe.json (the importer): one columnar table of every instrument's cards, decoded into the same row
    // shape the per-instrument files use for the fields the Compare tab and the calendar read (the ladder books'
    // ret / how / days / hit, the setup codes, the flag and short-string extras); nothing else is there
    const c = u.cols, K = u.codes, epoch = dateMs(u.epoch) / 1000, out = new Array(u.n);
    const int = (v) => v == null || v < 0 ? null : v;
    const flag = (v) => v == null || v < 0 ? null : v === 1;
    const code = (key, v) => (v == null || v < 0 || !K[key] ? null : K[key][v]);
    const xcols = Object.keys(c).filter((k) => k.startsWith("x:"));
    for (let i = 0; i < u.n; i++) {
      const t = {
        _i: i, coin: u.instruments[c.instrument[i]], date: C.iso(epoch + c.date[i] * C.DAY),
        tf: code("bar", c.bar[i]), kind: code("kind", c.kind[i]), direction: code("dir", c.dir[i]), cls: code("class", c.class[i]),
        t1: c.t1[i] === 1 ? 1 : null, liquid: false, flag: "none", byBook: {},
      };
      for (const b of u.books) {
        t.byBook[b] = { id: b, ret: c[b + ":ret"][i], how: code("how", c[b + ":how"][i]) || "none", k: int(c[b + ":days"][i]), hit: flag(c[b + ":hit"][i]) };
      }
      for (const k of xcols) {
        const name = k.slice(2), v = c[k][i];
        t[name] = K[k] ? code(k, v) : flag(v);
        if (name === "liquid") t.liquid = v === 1;
        if (name === "flag") t.flag = code(k, v) || "none";
      }
      out[i] = t;
    }
    return out;
  }

  DV.stats = { bookStats, allBooks, bySetup, histogram, calendarDays, fromUniverse, retOf, hitOf, daysOf, howOf, maxDrawdown, monthSummary, swapPair };
})(window.DV);
