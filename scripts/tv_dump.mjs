// TVB-4/5 run-matrix dump: full metrics + trade list for the strategy on the chart.
// Usage: node scripts/tv_dump.mjs <outfile.json>
// Writes {net, trades, marginCalls, openTrades, metrics:{all,long,short subset},
//         list:[{et,dir,pp,pv,q,open}]} -- list entries with open:true are the
//         mark-to-market open position rows (excluded from the printed L/S split).
import { evaluate, disconnect } from 'file:///C:/Strat_Trading_Bot/tradingview-mcp-jackson/src/connection.js';

const outfile = process.argv[2];
if (!outfile) { console.error('usage: node tvb4_dump.mjs <outfile.json>'); process.exit(1); }

const EXPR = `(function(){
  var model = window.TradingViewApi._activeChartWidgetWV.value()._chartWidget.model().model();
  var sources = model.dataSources();
  for (var i=0;i<sources.length;i++){ var s=sources[i]; if(!s.metaInfo) continue; var mi=s.metaInfo();
    if (mi.isTVScriptStrategy===true || typeof s.reportData==='function'){
      var rd = s.reportData(); if (rd && typeof rd.value==='function') rd = rd.value();
      var perf = rd.performance || {};
      var all = perf.all || {}, lng = perf.long || {}, sht = perf.short || {};
      function pick(o){ return {net: o.netProfitPercent, pf: o.profitFactor, trades: o.totalTrades,
        win: o.percentProfitable, dd: perf.maxStrategyDrawDownPercent, sharpe: perf.sharpeRatio,
        wins: o.numberOfWiningTrades, losses: o.numberOfLosingTrades}; }
      var tr = rd.trades || [];
      // Closed-vs-open basis (Codex TVB-4 LOW 2): the list is entry-ordered and the
      // open trade(s) sit at the END as pseudo-closed rows (x = mark-to-market at a
      // wall-clock ms timestamp, not a bar boundary). performance.all.totalTrades is
      // closed-only, so the first totalTrades entries are the closed set.
      var closedN = all.totalTrades || 0;
      var list = [];
      for (var j=0;j<tr.length;j++){ var t=tr[j];
        list.push({et: t.e ? t.e.tm : null, dir: t.e ? t.e.tp : null, pp: t.tp ? t.tp.p : null,
                   pv: t.tp ? t.tp.v : null, q: t.q, open: j >= closedN}); }
      return {net: all.netProfitPercent, trades: all.totalTrades, marginCalls: all.marginCalls,
              openTrades: all.totalOpenTrades, buyHold: perf.buyHoldReturnPercent,
              all: pick(all), long: pick(lng), short: pick(sht), list: list};
    } }
  return {error:'no strategy'};
})()`;

const out = await evaluate(EXPR);
const fs = await import('node:fs');
fs.writeFileSync(outfile, JSON.stringify(out));
if (out.error) { console.log('ERROR:', out.error); }
else {
  const dirs = {}; out.list.filter(t => !t.open).forEach(t => dirs[t.dir] = (dirs[t.dir]||0)+1);
  console.log('net%:', (out.net*100).toFixed(2), '| trades:', out.trades,
    '| L/S(closed):', JSON.stringify(dirs), '| marginCalls:', out.marginCalls, '| open:', out.openTrades,
    '| PF:', out.all.pf ? out.all.pf.toFixed(3) : 'na', '| DD%:', out.all.dd ? (out.all.dd*100).toFixed(1) : 'na',
    '| Sharpe:', out.all.sharpe ? out.all.sharpe.toFixed(2) : 'na');
  console.log('  long net%:', (out.long.net*100).toFixed(2), 'PF', out.long.pf ? out.long.pf.toFixed(3) : 'na',
    '| short net%:', (out.short.net*100).toFixed(2), 'PF', out.short.pf ? out.short.pf.toFixed(3) : 'na');
}
await disconnect();
