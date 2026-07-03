// TVB-4 CDP probe -- status / history loading for the bar-magnifier fidelity check.
// Reuses jackson's connection.js (same CDP bridge as the MCP, no MCP restart needed).
// Usage: node tvb4_probe.mjs status | node tvb4_probe.mjs history
import { evaluate, disconnect } from 'file:///C:/Strat_Trading_Bot/tradingview-mcp-jackson/src/connection.js';

const CHART = 'window.TradingViewApi._activeChartWidgetWV.value()';
const cmd = process.argv[2] || 'status';

const STATUS_EXPR = `(function(){
  try {
    var cw = ${CHART}._chartWidget;
    var model = cw.model().model();
    var ms = model.mainSeries();
    var bars = ms.bars();
    var out = { dataSize: bars.size(), firstTime: null, lastTime: null, msMoreMethods: [] };
    try { var f = bars.valueAt(bars.firstIndex()); out.firstTime = f ? f[0] : null; } catch(e){}
    try { var l = bars.valueAt(bars.lastIndex()); out.lastTime = l ? l[0] : null; } catch(e){}
    try { out.symbol = ms.symbolInfo() ? ms.symbolInfo().name : null; } catch(e){}
    try { out.interval = ms.interval ? ms.interval() : null; } catch(e){}
    var proto = Object.getPrototypeOf(ms), names = [];
    while (proto && proto !== Object.prototype) {
      names = names.concat(Object.getOwnPropertyNames(proto));
      proto = Object.getPrototypeOf(proto);
    }
    out.msMoreMethods = names.filter(function(k){ return /more|request/i.test(k); });
    var sources = model.dataSources();
    for (var i = 0; i < sources.length; i++) {
      var s = sources[i];
      if (!s.metaInfo) continue;
      var mi = s.metaInfo();
      if (mi.isTVScriptStrategy === true || typeof s.reportData === 'function') {
        var st = { id: (typeof s.id === 'function' ? s.id() : null), desc: mi.description };
        try { st.status = typeof s.status === 'function' ? s.status() : null; } catch(e){ st.status = 'err:' + e.message; }
        try {
          var rd = s.reportData();
          if (rd && typeof rd.value === 'function') rd = rd.value();
          if (rd && rd.performance) {
            var all = rd.performance.all || {};
            st.totalTrades = all.totalTrades;
            st.netProfitPercent = all.netProfitPercent;
            st.marginCalls = all.marginCalls;
            st.totalOpenTrades = all.totalOpenTrades;
          } else { st.report = 'no performance'; }
        } catch(e){ st.reportErr = e.message; }
        out.strategy = st;
        break;
      }
    }
    return out;
  } catch(e){ return { error: e.message }; }
})()`;

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function status() {
  const s = await evaluate(STATUS_EXPR);
  print(s);
  return s;
}

function print(s) {
  const fmt = t => (t ? new Date(t * 1000).toISOString() : null);
  console.log(JSON.stringify({ ...s, firstTimeISO: fmt(s.firstTime), lastTimeISO: fmt(s.lastTime) }, null, 2));
}

async function history() {
  // Loop requestMoreData until the series stops growing (data floor reached).
  let prevSize = -1;
  for (let round = 0; round < 200; round++) {
    const size = await evaluate(`(function(){
      var ms = ${CHART}._chartWidget.model().model().mainSeries();
      try { ms.requestMoreData(500); } catch(e) { return { err: e.message }; }
      return { size: ms.bars().size() };
    })()`);
    if (size && size.err) { console.log('requestMoreData error:', size.err); break; }
    await sleep(700);
    const now = await evaluate(`${CHART}._chartWidget.model().model().mainSeries().bars().size()`);
    process.stdout.write(`round ${round}: size ${now}\n`);
    if (now === prevSize) { console.log('size stable -- floor reached (or no more data).'); break; }
    prevSize = now;
  }
  await status();
}

try {
  if (cmd === 'status') await status();
  else if (cmd === 'history') await history();
  else console.log('unknown cmd:', cmd);
} finally {
  await disconnect();
}
