// TVB-4/5/6 run-matrix dump: full metrics + trade list for the strategy on the chart.
// Usage: node scripts/tv_dump.mjs <outfile.json>
// Writes {net, trades, marginCalls, openTrades, assert, metrics:{all,long,short},
//         list:[{et,xt,ep,xp,dir,pp,pv,q,ddp,rnp,open}]} -- open:true rows are the
//         mark-to-market open position rows (excluded from the printed L/S split).
// TVB-6 fields: xt/xp exit time+price, ep entry price, ddp/rnp = TV's per-trade
// max drawdown / run-up percent (MAE/MFE inputs for the solvency analysis).
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
      // Fail-loud guards (Codex TVB-5 LOW 1): assert the convention at dump time and
      // preserve the raw exit timestamp (xt) per row so the split can be re-derived
      // if TradingView ever changes the ordering.
      var closedN = all.totalTrades || 0;
      var openN = all.totalOpenTrades || 0;
      var lenOk = tr.length === closedN + openN;
      var orderOk = true;
      for (var k=1;k<tr.length;k++){
        var a = tr[k-1].e ? tr[k-1].e.tm : null, b = tr[k].e ? tr[k].e.tm : null;
        if (a !== null && b !== null && b < a) { orderOk = false; break; } }
      var list = [];
      for (var j=0;j<tr.length;j++){ var t=tr[j];
        list.push({et: t.e ? t.e.tm : null, xt: t.x ? t.x.tm : null,
                   ep: t.e ? t.e.p : null, xp: t.x ? t.x.p : null,
                   dir: t.e ? t.e.tp : null, pp: t.tp ? t.tp.p : null,
                   pv: t.tp ? t.tp.v : null, q: t.q,
                   ddp: t.dd ? t.dd.p : null, rnp: t.rn ? t.rn.p : null,
                   open: j >= closedN}); }
      return {net: all.netProfitPercent, trades: all.totalTrades, marginCalls: all.marginCalls,
              openTrades: all.totalOpenTrades, buyHold: perf.buyHoldReturnPercent,
              assert: {listLen: tr.length, closedN: closedN, openN: openN,
                       lenOk: lenOk, entryOrderOk: orderOk},
              all: pick(all), long: pick(lng), short: pick(sht), list: list};
    } }
  return {error:'no strategy'};
})()`;

const out = await evaluate(EXPR);
const fs = await import('node:fs');
fs.writeFileSync(outfile, JSON.stringify(out));
if (out.error) { console.log('ERROR:', out.error); }
else {
  const a = out.assert || {};
  if (!a.lenOk || !a.entryOrderOk) {
    console.log('ASSERTION FAILED -- reportData().trades convention changed:',
      JSON.stringify(a), '-- closed/open split in this dump is UNTRUSTWORTHY.');
    process.exitCode = 2;
  }
  const dirs = {}; out.list.filter(t => !t.open).forEach(t => dirs[t.dir] = (dirs[t.dir]||0)+1);
  console.log('net%:', (out.net*100).toFixed(2), '| trades:', out.trades,
    '| L/S(closed):', JSON.stringify(dirs), '| marginCalls:', out.marginCalls, '| open:', out.openTrades,
    '| PF:', out.all.pf ? out.all.pf.toFixed(3) : 'na', '| DD%:', out.all.dd ? (out.all.dd*100).toFixed(1) : 'na',
    '| Sharpe:', out.all.sharpe ? out.all.sharpe.toFixed(2) : 'na');
  console.log('  long net%:', (out.long.net*100).toFixed(2), 'PF', out.long.pf ? out.long.pf.toFixed(3) : 'na',
    '| short net%:', (out.short.net*100).toFixed(2), 'PF', out.short.pf ? out.short.pf.toFixed(3) : 'na');
}
await disconnect();
