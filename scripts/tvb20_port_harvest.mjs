// TVB-20 control-port parity harvest -- per symbol: deep-load the ACTIVE
// strategy chart to the data floor, wait for the Strategy Tester report to
// settle, and dump the FULL reportData().trades list (same field mapping as
// the tradingview MCP's data_get_trades) plus the performance topline.
// Output: analysis/reference/port_parity/tvb20_{coin}_trades.json
// PRECONDITIONS: the TFC-BF CONTROL [TVB-20] strategy is mounted on the
// active chart of the TVB18-parity scratch layout and the Strategy Tester
// panel is open (a hidden strategy or closed panel never computes a report).
// Usage: node scripts/tvb20_port_harvest.mjs [COIN ...]  (default GOOGL TSLA DRAM)
// Exit 1 unless every requested symbol lands floor + settled report.
import { mkdirSync, writeFileSync } from 'node:fs';
import { evaluate, disconnect } from 'file:///C:/Strat_Trading_Bot/tradingview-mcp-jackson/src/connection.js';

const COINS = process.argv.slice(2).length ? process.argv.slice(2) : ['GOOGL', 'TSLA', 'DRAM'];
const OUT_DIR = 'analysis/reference/port_parity';
const CHART = 'window.TradingViewApi._activeChartWidgetWV.value()';
const MS = `${CHART}._chartWidget.model().model().mainSeries()`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (o) => console.log(JSON.stringify({ t: new Date().toISOString(), ...o }));
const STABLE_ROUNDS = 3;

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
  let stable = 0;
  for (let round = 0; round < 400; round++) {
    const r = await evaluate(`(function(){
      try { ${MS}.requestMoreData(500); } catch(e) { return { err: e.message }; }
      return { ok: 1 }; })()`);
    if (r && r.err) return { state: 'err', rounds: round, err: r.err };
    await sleep(900);
    const size = await evaluate(`${MS}.bars().size()`);
    if (size === prev) {
      stable += 1;
      if (stable >= STABLE_ROUNDS) return { state: 'floor', rounds: round, size };
    } else {
      stable = 0;
    }
    prev = size;
  }
  return { state: 'capped', rounds: 400, size: prev };
}

const EDGES = `(function(){
  try {
    var ms = ${MS};
    var bars = ms.bars();
    var fi = bars.firstIndex(), li = bars.lastIndex();
    var fv = bars.valueAt(fi), lv = bars.valueAt(li);
    var si = null;
    try { si = ms.symbolInfo(); } catch(e){}
    return {
      pro_symbol: si ? si.pro_name : null,
      mintick: si && si.minmov && si.pricescale ? si.minmov / si.pricescale : null,
      interval: ms.interval ? ms.interval() : null,
      count: li - fi + 1,
      first_bar_ts: fv ? fv[0] : null,
      last_bar_ts: lv ? lv[0] : null
    };
  } catch(e){ return { error: e.message }; }
})()`;

// Same strategy-locating idiom as tradingview-mcp-jackson src/core/data.js
// (metaInfo().isTVScriptStrategy; prefer the source whose report computed).
const DUMP_TRADES = `(function(){
  function reportOf(s) {
    try { var rd = s.reportData(); if (rd && typeof rd.value === 'function') rd = rd.value(); return rd; } catch (e) { return null; }
  }
  try {
    var chart = ${CHART}._chartWidget;
    var sources = chart.model().model().dataSources();
    var found = null, name = null, count = 0;
    for (var i = 0; i < sources.length; i++) {
      var s = sources[i], mi = null;
      try { mi = s.metaInfo ? s.metaInfo() : null; } catch (e) {}
      var isStrat = mi && (mi.isTVScriptStrategy || mi.is_strategy);
      if (isStrat && typeof s.reportData === 'function') {
        count++;
        var rd = reportOf(s);
        if (rd && rd.performance && !found) { found = rd; name = mi.description; }
      }
    }
    if (!found) return { error: 'no computed strategy report', strategy_count: count };
    var raw = Array.isArray(found.trades) ? found.trades : null;
    if (!raw) return { error: 'reportData().trades unavailable', strategy_count: count };
    var result = [];
    for (var t = 0; t < raw.length; t++) {
      var tr = raw[t];
      var en = tr.e || {}, ex = tr.x || {}, pf = tr.tp || {};
      result.push({
        index: t,
        direction: en.c, qty: tr.q,
        entry_price: en.p, entry_time: en.tm, entry_bar: en.b,
        exit_signal: ex.c, exit_price: ex.p, exit_time: ex.tm, exit_bar: ex.b,
        profit: pf.v, profit_pct: pf.p
      });
    }
    var perfAll = null;
    try { perfAll = found.performance.all || null; } catch (e) {}
    return { strategy: name, strategy_count: count, total_trades: raw.length,
             trades: result, performance_all: perfAll };
  } catch(e){ return { error: e.message }; }
})()`;

async function settledTrades() {
  let prevKey = null;
  for (let round = 0; round < 30; round++) {
    const d = await evaluate(DUMP_TRADES);
    if (d && !d.error && d.trades && d.trades.length) {
      const last = d.trades[d.trades.length - 1];
      const key = `${d.total_trades}|${last.entry_time}|${last.exit_signal || ''}`;
      if (key === prevKey) return d;
      prevKey = key;
    } else {
      prevKey = null;
    }
    await sleep(2000);
  }
  return { error: 'strategy report did not settle (is the Strategy Tester panel open?)' };
}

try {
  mkdirSync(OUT_DIR, { recursive: true });
  let failures = 0;
  for (const coin of COINS) {
    const tvSym = `HIP3XYZ:${coin}USDC.P`;
    if (!(await setSymbol(tvSym)) || !(await setResolution('5'))) {
      log({ ev: 'skip', coin, error: 'symbol/resolution did not load' });
      failures += 1;
      continue;
    }
    const hist = await loadHistory();
    if (hist.state !== 'floor') {
      log({ ev: 'history_incomplete', coin, ...hist });
      failures += 1;
      continue;
    }
    const edges = await evaluate(EDGES);
    if (!edges || edges.error || edges.pro_symbol !== tvSym || edges.interval !== '5') {
      log({ ev: 'edges_failed', coin, edges });
      failures += 1;
      continue;
    }
    const dump = await settledTrades();
    if (dump.error) {
      log({ ev: 'trades_failed', coin, error: dump.error });
      failures += 1;
      continue;
    }
    const out = {
      coin,
      tv_symbol: tvSym,
      roster_symbol: `xyz:${coin}`,
      harvested_utc: new Date().toISOString(),
      strategy: dump.strategy,
      strategy_count: dump.strategy_count,
      chart: { ...edges, history_termination: hist,
               firstISO: new Date(edges.first_bar_ts * 1000).toISOString(),
               lastISO: new Date(edges.last_bar_ts * 1000).toISOString() },
      note: 'last trade may be OPEN (empty exit_signal, tip-marked exit); '
        + 'entry/exit times are ms epoch of the FILL bar under '
        + 'process_orders_on_close=true (decision-exact convention, TVB-20)',
      total_trades: dump.total_trades,
      trades: dump.trades,
      performance_all: dump.performance_all,
    };
    const path = `${OUT_DIR}/tvb20_${coin}_trades.json`;
    writeFileSync(path, JSON.stringify(out, null, 1));
    log({ ev: 'dumped', coin, trades: dump.total_trades, first: out.chart.firstISO,
          last: out.chart.lastISO, bars: edges.count, out: path });
  }
  log({ ev: 'done', failures });
  if (failures > 0) process.exitCode = 1;
} finally {
  await disconnect();
}
