// TVB-23 package-mirror parity harvest (prereg step 7) -- per symbol:
// deep-load the ACTIVE strategy chart to the data floor, then for EACH
// TVB-23 arm (D1/DINF/D1ATR) set the package strategy's Arm input in place,
// wait for the Strategy Tester report to settle, and dump the FULL
// reportData().trades list of the TFC-MT PACKAGE [TVB-22] strategy (matched
// by TITLE -- the strategy() title deliberately did NOT change when the
// TVB-23 arms were added, because this harvest and its TVB-22 sibling match
// on it).
// Output: analysis/reference/pkg_parity/tvb23_{coin}_{arm}_trades.json
// Field mapping identical to scripts/tvb22_pkg_harvest.mjs (entry comment =
// pattern zipcode + trigger in trades[].e.c; direction from e.tp le/se).
// PRECONDITIONS: the package strategy (with the TVB-23 arm selector, saved
// v10+) is mounted on the active chart and the Strategy Tester panel is
// open. Optional env TVB_TARGET pins the CDP target by chart-id substring
// (needed when more than one TradingView chart tab is open, e.g. a live
// watch tab that must not be driven).
// Usage: node scripts/tvb23_pkg_harvest.mjs [COIN ...] (default GOOGL TSLA DRAM)
// Exit 1 unless every (symbol, arm) lands floor + settled report.
import { mkdirSync, writeFileSync } from 'node:fs';
import { evaluate, connect, disconnect } from 'file:///C:/Strat_Trading_Bot/tradingview-mcp-jackson/src/connection.js';

const COINS = process.argv.slice(2).length ? process.argv.slice(2) : ['GOOGL', 'TSLA', 'DRAM'];
// Comma-free labels (a comma inside a string input value breaks TV's input
// round-trip; found TVB-22). Values must equal the pine's arm options.
const ARMS = [
  { tag: 'D1', value: 'D1 floored package (T1 exit + fixed vetoes)' },
  { tag: 'DINF', value: 'DINF floored entries (fixed vetoes + C1 exits)' },
  { tag: 'D1ATR', value: 'D1ATR floored package (T1 exit + ATR vetoes)' },
];
// Any arm label, TVB-22 or TVB-23, marks the selector input when scanning
// current values (the input's current value depends on what ran before).
const ARM_VALUE_RE = /^(A[123]|D1|DINF|D1ATR) /;
const STRATEGY_TITLE = 'TFC-MT PACKAGE [TVB-22]';
const OUT_DIR = 'analysis/reference/pkg_parity';
const CHART = 'window.TradingViewApi._activeChartWidgetWV.value()';
const MS = `${CHART}._chartWidget.model().model().mainSeries()`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (o) => console.log(JSON.stringify({ t: new Date().toISOString(), ...o }));
const STABLE_ROUNDS = 3;

if (process.env.TVB_TARGET) {
  const targets = await (await fetch('http://127.0.0.1:9222/json/list')).json();
  const wb = targets.find((t) => t.type === 'page' && t.url.includes(process.env.TVB_TARGET));
  if (!wb) {
    log({ ev: 'fatal', error: `TVB_TARGET ${process.env.TVB_TARGET} not found among CDP targets` });
    process.exit(2);
  }
  await connect(wb.id);
  log({ ev: 'target_pinned', id: wb.id, url: wb.url });
}

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

// Set the package strategy's Arm input in place. The arm selector is found
// by its VALUE shape rather than a generated input id.
// CRITICAL (found TVB-22): setInputValues must receive ONLY the modified
// entry -- re-sending the full getInputValues() array corrupts the study
// ("Can't parse pine" runtime kill).
function setArmExpr(armValue) {
  return `(function(){
    try {
      var chart = window.TradingViewApi.activeChart();
      var studies = chart.getAllStudies();
      var target = null;
      for (var i = 0; i < studies.length; i++) {
        if (studies[i].name === ${JSON.stringify(STRATEGY_TITLE)}) { target = studies[i]; break; }
      }
      if (!target) return { error: 'package study not mounted' };
      var st = chart.getStudyById(target.id);
      var cur = st.getInputValues();
      var hit = null;
      for (var j = 0; j < cur.length; j++) {
        if (${ARM_VALUE_RE}.test(String(cur[j].value))) { hit = cur[j].id; }
      }
      if (!hit) return { error: 'arm input not found among ' + cur.length + ' inputs' };
      st.setInputValues([{ id: hit, value: ${JSON.stringify(armValue)} }]);
      // read the input BACK after setting (TVB-24 audit F4): the dump must
      // prove the arm actually applied, not just that a set call returned
      var after = st.getInputValues(), got = null;
      for (var k = 0; k < after.length; k++) {
        if (after[k].id === hit) { got = String(after[k].value); }
      }
      if (got !== ${JSON.stringify(armValue)}) {
        return { error: 'arm input read-back mismatch: ' + got };
      }
      return { ok: 1, input_id: hit, entity_id: target.id, value_after: got };
    } catch(e){ return { error: e.message }; }
  })()`;
}

// Dump the PACKAGE strategy's trades by title match (never first-computed).
const DUMP_TRADES = `(function(){
  function reportOf(s) {
    try { var rd = s.reportData(); if (rd && typeof rd.value === 'function') rd = rd.value(); return rd; } catch (e) { return null; }
  }
  try {
    var chart = ${CHART}._chartWidget;
    var sources = chart.model().model().dataSources();
    var found = null, count = 0;
    for (var i = 0; i < sources.length; i++) {
      var s = sources[i], mi = null;
      try { mi = s.metaInfo ? s.metaInfo() : null; } catch (e) {}
      var isStrat = mi && (mi.isTVScriptStrategy || mi.is_strategy);
      if (isStrat && mi.description === ${JSON.stringify(STRATEGY_TITLE)} && typeof s.reportData === 'function') {
        count++;
        var rd = reportOf(s);
        if (rd && rd.performance && !found) found = rd;
      }
    }
    if (!found) return { error: 'no computed package report', strategy_count: count };
    var raw = Array.isArray(found.trades) ? found.trades : null;
    if (!raw) return { error: 'reportData().trades unavailable', strategy_count: count };
    var result = [];
    for (var t = 0; t < raw.length; t++) {
      var tr = raw[t];
      var en = tr.e || {}, ex = tr.x || {}, pf = tr.tp || {};
      var tp = String(en.tp || '');
      var dirL = tp.charAt(0) === 'l' ? 'L' : tp.charAt(0) === 's' ? 'S' : null;
      result.push({
        index: t,
        direction: dirL, entry_tp: en.tp,
        entry_signal: en.c,
        qty: tr.q,
        entry_price: en.p, entry_time: en.tm, entry_bar: en.b,
        exit_signal: ex.c, exit_price: ex.p, exit_time: ex.tm, exit_bar: ex.b,
        profit: pf.v, profit_pct: pf.p
      });
    }
    var perfAll = null;
    try { perfAll = found.performance.all || null; } catch (e) {}
    return { strategy: ${JSON.stringify(STRATEGY_TITLE)}, strategy_count: count,
             total_trades: raw.length, trades: result, performance_all: perfAll };
  } catch(e){ return { error: e.message }; }
})()`;

async function settledTrades() {
  let prevKey = null;
  for (let round = 0; round < 45; round++) {
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
  return { error: 'package report did not settle (is the Strategy Tester panel open?)' };
}

try {
  mkdirSync(OUT_DIR, { recursive: true });
  let failures = 0;
  for (const coin of COINS) {
    const tvSym = `HIP3XYZ:${coin}USDC.P`;
    if (!(await setSymbol(tvSym)) || !(await setResolution('5'))) {
      log({ ev: 'skip', coin, error: 'symbol/resolution did not load' });
      failures += ARMS.length;
      continue;
    }
    const hist = await loadHistory();
    if (hist.state !== 'floor') {
      log({ ev: 'history_incomplete', coin, ...hist });
      failures += ARMS.length;
      continue;
    }
    const edges = await evaluate(EDGES);
    if (!edges || edges.error || edges.pro_symbol !== tvSym || edges.interval !== '5') {
      log({ ev: 'edges_failed', coin, edges });
      failures += ARMS.length;
      continue;
    }
    for (const arm of ARMS) {
      const setr = await evaluate(setArmExpr(arm.value));
      if (!setr || setr.error) {
        log({ ev: 'arm_set_failed', coin, arm: arm.tag, error: setr && setr.error });
        failures += 1;
        continue;
      }
      await sleep(4000); // let the recompute start before the settle loop
      const dump = await settledTrades();
      if (dump.error) {
        log({ ev: 'trades_failed', coin, arm: arm.tag, error: dump.error });
        failures += 1;
        continue;
      }
      if (dump.strategy_count !== 1) {
        // exactly one computed copy of the package strategy may be mounted
        // (TVB-24 audit F4): with duplicates the dump's first-match pick is
        // ambiguous, so the cell fails instead of harvesting a guess
        log({ ev: 'strategy_count_bad', coin, arm: arm.tag, count: dump.strategy_count });
        failures += 1;
        continue;
      }
      const bad = dump.trades.filter((tr) => tr.direction !== 'L' && tr.direction !== 'S').length;
      if (bad > 0) log({ ev: 'direction_parse_warning', coin, arm: arm.tag, unparsed: bad });
      const out = {
        coin,
        tv_symbol: tvSym,
        roster_symbol: `xyz:${coin}`,
        arm: arm.tag,
        arm_input: arm.value,
        harvested_utc: new Date().toISOString(),
        strategy: dump.strategy,
        strategy_count: dump.strategy_count,
        chart: { ...edges, history_termination: hist,
                 firstISO: new Date(edges.first_bar_ts * 1000).toISOString(),
                 lastISO: new Date(edges.last_bar_ts * 1000).toISOString() },
        note: 'last trade may be OPEN (empty exit_signal, tip-marked exit); '
          + 'entry/exit times are ms epoch of the FILL bar under '
          + 'process_orders_on_close=true (decision-exact convention); '
          + 'direction from e.tp (le/se), entry_signal = pattern zipcode + trig',
        total_trades: dump.total_trades,
        trades: dump.trades,
        performance_all: dump.performance_all,
      };
      const path = `${OUT_DIR}/tvb23_${coin}_${arm.tag}_trades.json`;
      writeFileSync(path, JSON.stringify(out, null, 1));
      log({ ev: 'dumped', coin, arm: arm.tag, trades: dump.total_trades, bars: edges.count, out: path });
    }
  }
  log({ ev: 'done', failures });
  if (failures > 0) process.exitCode = 1;
} finally {
  await disconnect();
}
