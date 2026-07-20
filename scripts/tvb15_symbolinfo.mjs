// TVB-15 symbolInfo capture for the frozen week-1 roster.
// Same mechanism as tvb9_symbolinfo.mjs (the approved PRIMARY mintick
// source): set each TV symbol, wait for the main series to resolve,
// capture minmov/pricescale/mintick, then restore the resting symbol
// (the user's DRAM front chart).
// Usage: node tvb15_symbolinfo.mjs <out.json>
import { writeFileSync } from 'node:fs';
import { evaluate, disconnect } from 'file:///C:/Strat_Trading_Bot/tradingview-mcp-jackson/src/connection.js';

const CHART = 'window.TradingViewApi._activeChartWidgetWV.value()';
const RESTING = 'HIP3XYZ:DRAMUSDC.P';
const SYMBOLS = [
  { coin: 'xyz:MRVL',  tv: 'HIP3XYZ:MRVLUSDC.P' },
  { coin: 'xyz:GOOGL', tv: 'HIP3XYZ:GOOGLUSDC.P' },
  { coin: 'xyz:AMZN',  tv: 'HIP3XYZ:AMZNUSDC.P' },
  { coin: 'xyz:MSFT',  tv: 'HIP3XYZ:MSFTUSDC.P' },
  { coin: 'xyz:GOLD',  tv: 'HIP3XYZ:GOLDUSDC.P' },
  { coin: 'xyz:AAPL',  tv: 'HIP3XYZ:AAPLUSDC.P' },
  { coin: 'xyz:SKHX',  tv: 'HIP3XYZ:SKHXUSDC.P' },
  { coin: 'xyz:SKHY',  tv: 'HIP3XYZ:SKHYUSDC.P' },
  { coin: 'xyz:NBIS',  tv: 'HIP3XYZ:NBISUSDC.P' },
  { coin: 'xyz:TSLA',  tv: 'HIP3XYZ:TSLAUSDC.P' },
  { coin: 'xyz:DRAM',  tv: 'HIP3XYZ:DRAMUSDC.P' },
];

const out = process.argv[2];
if (!out) { console.error('usage: node tvb15_symbolinfo.mjs <out.json>'); process.exit(1); }

const sleep = ms => new Promise(r => setTimeout(r, ms));

const INFO_EXPR = `(function(){
  try {
    var si = ${CHART}._chartWidget.model().model().mainSeries().symbolInfo();
    if (!si) return { pending: true };
    return {
      name: si.name, pro_name: si.pro_name, full_name: si.full_name,
      exchange: si.exchange, type: si.type, currency: si.currency_code || si.currency || null,
      minmov: si.minmov, pricescale: si.pricescale,
      mintick: si.minmov && si.pricescale ? si.minmov / si.pricescale : null
    };
  } catch(e){ return { error: e.message }; }
})()`;

async function setSymbol(sym) {
  await evaluate(`${CHART}.setSymbol(${JSON.stringify(sym)}, {})`);
}

async function captureFor(sym, timeoutMs = 25000) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeoutMs) {
    const r = await evaluate(INFO_EXPR);
    if (r && r.pro_name === sym && r.mintick) return r;
    await sleep(500);
  }
  return { error: `timeout waiting for ${sym} to resolve` };
}

const captured = [];
try {
  for (const s of SYMBOLS) {
    await setSymbol(s.tv);
    const r = await captureFor(s.tv);
    if (r.error) {
      console.error(`${s.coin} (${s.tv}): ${r.error}`);
      captured.push({ coin: s.coin, tv_symbol: s.tv, error: r.error });
    } else {
      captured.push({ coin: s.coin, tv_symbol: r.pro_name, exchange: r.exchange,
        type: r.type, currency: r.currency, minmov: r.minmov,
        pricescale: r.pricescale, mintick: r.mintick });
      console.log(`${s.coin}: ${r.pro_name} minmov ${r.minmov} pricescale ${r.pricescale} mintick ${r.mintick}`);
    }
  }
  await setSymbol(RESTING);
  await captureFor(RESTING);
  console.log(`restored resting symbol ${RESTING}`);
  const doc = {
    purpose: 'TVB-15 week-1 roster: per-symbol TV tick metadata (PRIMARY mintick source). Captured live via CDP symbolInfo().',
    captured_at: new Date().toISOString(),
    symbols: captured,
  };
  writeFileSync(out, JSON.stringify(doc, null, 1));
  console.log(`wrote ${out}`);
  if (captured.some(c => c.error)) process.exit(1);
} finally {
  await disconnect();
}
