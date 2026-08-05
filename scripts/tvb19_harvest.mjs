// TVB-19 deep-window TV-bar harvest -- full loaded-series dumps per symbol/interval.
// The TVB-6 path scripted end-to-end: for each roster symbol and interval, set the
// chart (active chart on the TVB18-parity SCRATCH layout -- never a live layout),
// loop requestMoreData to the data floor (tv_probe.mjs history mechanism), then dump
// the entire main series with tick metadata (tv_bars.mjs mechanism).
// Provenance: TV bars vs HL archive bars differ at the cents/wick level (TVB-6:
// 97-99% float-exact); every dump records pro_symbol + minmov/pricescale.
// Usage: node scripts/tvb19_harvest.mjs [outDir]  (default analysis/reference/tv_deep)
import { mkdirSync, writeFileSync } from 'node:fs';
import { evaluate, disconnect } from 'file:///C:/Strat_Trading_Bot/tradingview-mcp-jackson/src/connection.js';

// TVB19_COINS overrides the roster list for partial re-harvests, e.g.
// TVB19_COINS=SKHYNIX (the TV coin string; xyz:SKHX maps to HIP3XYZ:SKHYNIXUSDC.P --
// TV search does not index HIP3XYZ, discovered by direct chart load 2026-08-05).
const COINS = process.env.TVB19_COINS
  ? process.env.TVB19_COINS.split(',')
  : ['MRVL', 'GOOGL', 'AMZN', 'MSFT', 'GOLD', 'AAPL', 'SKHX', 'SKHY', 'NBIS', 'TSLA', 'DRAM'];
const INTERVALS = ['15', '60', '5'];
const OUT_DIR = process.argv[2] || 'analysis/reference/tv_deep';
const CHART = 'window.TradingViewApi._activeChartWidgetWV.value()';
const MS = `${CHART}._chartWidget.model().model().mainSeries()`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (o) => console.log(JSON.stringify({ t: new Date().toISOString(), ...o }));

async function poll(exprCheck, timeoutMs, label) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeoutMs) {
    try {
      if (await evaluate(exprCheck)) return true;
    } catch {}
    await sleep(1000);
  }
  log({ ev: 'timeout', what: label });
  return false;
}

async function setSymbol(tvSym) {
  await evaluate(`window.TradingViewApi.activeChart().setSymbol(${JSON.stringify(tvSym)}, {})`);
  return poll(
    `(function(){ try { var si = ${MS}.symbolInfo();
       return !!si && si.pro_name === ${JSON.stringify(tvSym)} && ${MS}.bars().size() > 0;
     } catch(e){ return false; } })()`,
    45000,
    `symbol ${tvSym}`
  );
}

async function setResolution(iv) {
  await evaluate(`window.TradingViewApi.activeChart().setResolution(${JSON.stringify(iv)}, {})`);
  return poll(
    `(function(){ try { return ${MS}.interval() === ${JSON.stringify(iv)} && ${MS}.bars().size() > 0; }
     catch(e){ return false; } })()`,
    45000,
    `resolution ${iv}`
  );
}

async function loadHistory() {
  let prev = -1;
  for (let round = 0; round < 400; round++) {
    const r = await evaluate(`(function(){
      try { ${MS}.requestMoreData(500); } catch(e) { return { err: e.message }; }
      return { ok: 1 }; })()`);
    if (r && r.err) return { rounds: round, err: r.err };
    await sleep(700);
    const size = await evaluate(`${MS}.bars().size()`);
    if (size === prev) return { rounds: round, size };
    prev = size;
  }
  return { rounds: 400, size: prev, capped: true };
}

const DUMP = `(function(){
  try {
    var ms = ${MS};
    var bars = ms.bars();
    var first = bars.firstIndex(), last = bars.lastIndex();
    var rows = [];
    for (var i = first; i <= last; i++) {
      var v = bars.valueAt(i);
      if (!v) continue;
      rows.push(v.slice(0, 6));
    }
    var si = null;
    try { si = ms.symbolInfo(); } catch(e){}
    return {
      symbol: si ? (si.full_name || si.name) : null,
      pro_symbol: si ? si.pro_name : null,
      exchange: si ? si.exchange : null,
      minmov: si ? si.minmov : null,
      pricescale: si ? si.pricescale : null,
      mintick: si && si.minmov && si.pricescale ? si.minmov / si.pricescale : null,
      interval: ms.interval ? ms.interval() : null,
      count: rows.length,
      bars: rows
    };
  } catch(e){ return { error: e.message }; }
})()`;

try {
  mkdirSync(OUT_DIR, { recursive: true });
  const summary = [];
  for (const coin of COINS) {
    const tvSym = `HIP3XYZ:${coin}USDC.P`;
    if (!(await setSymbol(tvSym))) {
      log({ ev: 'skip_symbol', coin, tvSym });
      summary.push({ coin, error: 'symbol did not load' });
      continue;
    }
    for (const iv of INTERVALS) {
      if (!(await setResolution(iv))) {
        log({ ev: 'skip_interval', coin, iv });
        summary.push({ coin, iv, error: 'resolution did not load' });
        continue;
      }
      const hist = await loadHistory();
      const dump = await evaluate(DUMP);
      if (!dump || dump.error || !dump.bars || !dump.bars.length) {
        log({ ev: 'dump_failed', coin, iv, error: dump && dump.error });
        summary.push({ coin, iv, error: (dump && dump.error) || 'empty dump' });
        continue;
      }
      if (dump.pro_symbol !== tvSym || dump.interval !== iv) {
        log({ ev: 'identity_mismatch', coin, iv, got: dump.pro_symbol, got_iv: dump.interval });
        summary.push({ coin, iv, error: 'identity mismatch, dump discarded' });
        continue;
      }
      dump.harvested_utc = new Date().toISOString();
      dump.provenance = 'TVB-19 deep harvest; TV loaded series to data floor; '
        + 'TV-vs-HL wick-level variance per TVB-6 (97-99% float-exact)';
      dump.firstISO = new Date(dump.bars[0][0] * 1000).toISOString();
      dump.lastISO = new Date(dump.bars[dump.bars.length - 1][0] * 1000).toISOString();
      const out = `${OUT_DIR}/tvb19_tv_xyz_${coin}_${iv}m.json`;
      writeFileSync(out, JSON.stringify(dump));
      log({ ev: 'dumped', coin, iv, count: dump.count, rounds: hist.rounds,
            first: dump.firstISO, last: dump.lastISO, out });
      summary.push({ coin, iv, count: dump.count, first: dump.firstISO, last: dump.lastISO });
    }
  }
  writeFileSync(`${OUT_DIR}/tvb19_harvest_summary.json`,
    JSON.stringify({ generated_utc: new Date().toISOString(), datasets: summary }, null, 1));
  log({ ev: 'done', datasets: summary.length });
} finally {
  await disconnect();
}
