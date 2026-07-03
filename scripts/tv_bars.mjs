// TVB-6 CDP bar exporter -- dump the active chart's main series OHLCV to JSON.
// Reuses jackson's connection.js (same CDP bridge as the MCP, no MCP restart needed).
// Usage: node tv_bars.mjs <out.json>
// Output: { symbol, interval, count, firstISO, lastISO, bars: [[epochSec,o,h,l,c,(v)] ...] }
// Load history to the data floor FIRST (node tv_probe.mjs history) or the dump is partial.
import { writeFileSync } from 'node:fs';
import { evaluate, disconnect } from 'file:///C:/Strat_Trading_Bot/tradingview-mcp-jackson/src/connection.js';

const CHART = 'window.TradingViewApi._activeChartWidgetWV.value()';
const out = process.argv[2];
if (!out) { console.error('usage: node tv_bars.mjs <out.json>'); process.exit(1); }

const EXPR = `(function(){
  try {
    var ms = ${CHART}._chartWidget.model().model().mainSeries();
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
      interval: ms.interval ? ms.interval() : null,
      count: rows.length,
      bars: rows
    };
  } catch(e){ return { error: e.message }; }
})()`;

try {
  const r = await evaluate(EXPR);
  if (!r || r.error) {
    console.error('export failed:', r && r.error);
    process.exit(1);
  }
  const iso = t => new Date(t * 1000).toISOString();
  r.firstISO = r.bars.length ? iso(r.bars[0][0]) : null;
  r.lastISO = r.bars.length ? iso(r.bars[r.bars.length - 1][0]) : null;
  writeFileSync(out, JSON.stringify(r));
  console.log(JSON.stringify({ symbol: r.symbol, pro_symbol: r.pro_symbol, interval: r.interval,
    count: r.count, firstISO: r.firstISO, lastISO: r.lastISO, out }, null, 2));
} finally {
  await disconnect();
}
