// TVB-35 macro-reference harvest -- dump the daily / weekly / hourly OHLCV of a
// fixed reference set (dollar index, US 10-year yield, WTI, Brent, S&P 500,
// bitcoin) from the ACTIVE TradingView chart into analysis/regime/data/.
// Same CDP bridge as the MCP (jackson connection.js). Read-only on TradingView
// beyond changing the active chart's symbol/resolution; the original
// symbol/resolution is restored at the end.
//
// Usage: node scripts/tvb35_regime_harvest.mjs [outdir]
// Per file: { symbol, pro_symbol, exchange, interval, count, firstISO, lastISO,
//             mintick, bars: [[epochSec,o,h,l,c,(v)] ...] }
// Loaded history is what TradingView has in the series at dump time (300-ish
// bars at 60m for FX/rates, more for daily/weekly); the ledger windows start
// 2026-08-22 so a 60m dump reaching 2026-08-21 is sufficient for the receipt.
import { writeFileSync, mkdirSync } from 'node:fs';
import { evaluate, evaluateAsync, disconnect, safeString } from 'file:///C:/Strat_Trading_Bot/tradingview-mcp-jackson/src/connection.js';

const CHART = 'window.TradingViewApi._activeChartWidgetWV.value()';
const OUT = process.argv[2] || 'analysis/regime/data';
mkdirSync(OUT, { recursive: true });

const REFS = [
  ['DXY', 'TVC:DXY'],
  ['US10Y', 'TVC:US10Y'],
  ['CL1', 'NYMEX:CL1!'],
  ['BRN1', 'ICEEUR:BRN1!'],
  ['SPX', 'SP:SPX'],
  ['BTCUSD', 'BITSTAMP:BTCUSD'],
];
const TFS = ['60', 'D', 'W'];

const sleep = ms => new Promise(r => setTimeout(r, ms));

const DUMP = `(function(){
  try {
    var ms = ${CHART}._chartWidget.model().model().mainSeries();
    var bars = ms.bars();
    var first = bars.firstIndex(), last = bars.lastIndex();
    var rows = [];
    for (var i = first; i <= last; i++) { var v = bars.valueAt(i); if (v) rows.push(v.slice(0, 6)); }
    var si = null; try { si = ms.symbolInfo(); } catch(e){}
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

async function state() {
  return evaluate(`(function(){ var c = ${CHART}; return { symbol: c.symbol(), resolution: c.resolution() }; })()`);
}
async function setSymbol(sym) {
  await evaluateAsync(`(function(){ var c = ${CHART}; return new Promise(function(res){ c.setSymbol(${safeString(sym)}, {}); setTimeout(res, 500); }); })()`);
}
async function setResolution(tf) {
  await evaluate(`(function(){ ${CHART}.setResolution(${safeString(tf)}, {}); })()`);
}
// Wait until the series reports the requested symbol/interval and the bar
// count stops changing (data settled), or give up after ~20 s.
async function settle(sym, tf) {
  let lastCount = -1, stable = 0;
  for (let i = 0; i < 40; i++) {
    await sleep(500);
    const r = await evaluate(DUMP);
    if (r && !r.error && r.interval === tf && (r.pro_symbol === sym || r.symbol === sym)) {
      if (r.count === lastCount && r.count > 0) { stable += 1; if (stable >= 3) return r; }
      else { stable = 0; lastCount = r.count; }
    }
  }
  return evaluate(DUMP);
}

const iso = t => new Date(t * 1000).toISOString();
const orig = await state();
console.log('original chart:', JSON.stringify(orig));
const manifest = [];
try {
  for (const [key, sym] of REFS) {
    await setSymbol(sym);
    for (const tf of TFS) {
      await setResolution(tf);
      const r = await settle(sym, tf);
      if (!r || r.error) { console.error('FAILED', key, tf, r && r.error); manifest.push({ key, sym, tf, error: r && r.error }); continue; }
      r.firstISO = r.bars.length ? iso(r.bars[0][0]) : null;
      r.lastISO = r.bars.length ? iso(r.bars[r.bars.length - 1][0]) : null;
      r.requested = sym; r.harvested_at = new Date().toISOString();
      const file = `${OUT}/${key}_${tf}.json`;
      writeFileSync(file, JSON.stringify(r));
      const line = { key, sym: r.pro_symbol || r.symbol, tf, count: r.count, first: r.firstISO, last: r.lastISO, file };
      manifest.push(line);
      console.log(JSON.stringify(line));
    }
  }
} finally {
  try { await setSymbol(orig.symbol); await setResolution(orig.resolution); } catch (e) { console.error('restore failed:', e.message); }
  writeFileSync(`${OUT}/MANIFEST.json`, JSON.stringify({ harvested_at: new Date().toISOString(), original_chart: orig, refs: REFS, tfs: TFS, files: manifest }, null, 2));
  await disconnect();
}
