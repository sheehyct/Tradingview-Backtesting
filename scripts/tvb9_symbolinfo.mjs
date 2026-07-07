// TVB-9 symbolInfo capture for the pre-registered breadth universe.
// Sets each TV symbol on the active chart, waits for the main series to
// resolve it, captures minmov/pricescale/mintick (the approved PRIMARY
// mintick source for the breadth sweep), then restores the resting symbol.
// Reuses jackson's connection.js (same CDP bridge as the MCP).
// Usage: node tvb9_symbolinfo.mjs <out.json>
import { writeFileSync } from 'node:fs';
import { evaluate, disconnect } from 'file:///C:/Strat_Trading_Bot/tradingview-mcp-jackson/src/connection.js';

const CHART = 'window.TradingViewApi._activeChartWidgetWV.value()';
const RESTING = 'HIP3XYZ:MSTRUSDC.P';
const SYMBOLS = [
  { coin: 'xyz:MSTR',   tv: 'HIP3XYZ:MSTRUSDC.P' },
  { coin: 'xyz:XYZ100', tv: 'HIP3XYZ:XYZ100USDC.P' },
  { coin: 'xyz:SP500',  tv: 'HIP3XYZ:SP500USDC.P' },
  { coin: 'BTC',        tv: 'HYPERLIQUID:BTCUSDC.P' },
  { coin: 'xyz:MU',     tv: 'HIP3XYZ:MUUSDC.P' },
  { coin: 'xyz:AMD',    tv: 'HIP3XYZ:AMDUSDC.P' },
  { coin: 'xyz:NVDA',   tv: 'HIP3XYZ:NVDAUSDC.P' },
  { coin: 'xyz:TSLA',   tv: 'HIP3XYZ:TSLAUSDC.P' },
  { coin: 'xyz:CRCL',   tv: 'HIP3XYZ:CRCLUSDC.P' },
];

const out = process.argv[2];
if (!out) { console.error('usage: node tvb9_symbolinfo.mjs <out.json>'); process.exit(1); }

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
    purpose: 'TVB-9 breadth pre-registration: per-symbol TV tick metadata (PRIMARY mintick source, approved 2026-07-07). Captured live via CDP symbolInfo().',
    captured_at: new Date().toISOString(),
    symbols: captured,
  };
  writeFileSync(out, JSON.stringify(doc, null, 1));
  console.log(`wrote ${out}`);
  if (captured.some(c => c.error)) process.exit(1);
} finally {
  await disconnect();
}
