// TVB-11 champion-search collector -- direct-CDP batch runner (pre-reg v1.1, P2).
// Drives the "TVB-EXP Champion [TVB-11]" strategy study on the active TV chart via
// the jackson CDP bridge, one pre-registered cell at a time, with the GPT-proven
// echo-validation integrity method: every run is REJECTED unless the strategy's own
// machine-readable METRICS table echoes back exactly the requested cell.
//
// Usage:
//   node scripts/tvb11_champion_collect.mjs status
//   node scripts/tvb11_champion_collect.mjs cells                # print Stage A1 cell list (JSON)
//   node scripts/tvb11_champion_collect.mjs anchor <out.jsonl>   # P3 anchor cells C1/C3/C6 on MU perp
//   node scripts/tvb11_champion_collect.mjs run <cells.json> <out.jsonl> [--limit N] [--start K]
//
// Checkpointing: results append to the JSONL outfile; on restart, cells whose key
// already exists in the outfile are skipped. Every record carries the requested cell,
// the echoed cell, the loaded window, full metrics, and the trade list (reportData)
// plus the raw pine TRADES table rows (profit()/commission/gross -- the P0b probe).
import { evaluate, disconnect } from 'file:///C:/Strat_Trading_Bot/tradingview-mcp-jackson/src/connection.js';
import { setSymbol, setTimeframe, getState } from 'file:///C:/Strat_Trading_Bot/tradingview-mcp-jackson/src/core/chart.js';
import { setInputs } from 'file:///C:/Strat_Trading_Bot/tradingview-mcp-jackson/src/core/indicators.js';
import { getPineTables } from 'file:///C:/Strat_Trading_Bot/tradingview-mcp-jackson/src/core/data.js';
import fs from 'node:fs';

const STUDY_NAME = 'TVB-EXP Champion [TVB-11]';
const SETTLE_POLL_MS = 2000;
const SETTLE_TIMEOUT_MS = 120000;

// ---- input id map (derived 2026-07-14 from the deployed study; declaration order) ----
// If the script gains/loses inputs this map MUST be re-derived (dump getInputValues).
const IN = {
  exit_mode: 'in_0', bf_exit: 'in_1', bf_reentry: 'in_2', arm_tf: 'in_3', exit_tf: 'in_4',
  y1: 'in_5', tf1: 'in_6', y2: 'in_7', tf2: 'in_8', y3: 'in_9', tf3: 'in_10',
  y4: 'in_11', tf4: 'in_12', y5: 'in_13', tf5: 'in_14', y6: 'in_15', tf6: 'in_16',
  allow_long: 'in_17', allow_short: 'in_18',
  reg_mode: 'in_19', rg1: 'in_20', rtf1: 'in_21', rg2: 'in_22', rtf2: 'in_23', rg3: 'in_24', rtf3: 'in_25',
  gov_mode: 'in_26', bf_tf: 'in_27', bf_strength: 'in_28', bf_show_pivots: 'in_29',
  show_table: 'in_30', show_trig: 'in_31',
};

// ---- gate sets (pre-reg Section 5; slots stay 60/120/240/D/W/M, toggles select) ----
const GATE_SETS = {
  full6:  { y1: true,  y2: true,  y3: true,  y4: true, y5: true, y6: true },
  ctrlA4: { y1: true,  y2: false, y3: false, y4: true, y5: true, y6: true },
  slow3:  { y1: false, y2: false, y3: false, y4: true, y5: true, y6: true },
};
const GATE_TFS = { tf1: '60', tf2: '120', tf3: '240', tf4: 'D', tf5: 'W', tf6: 'M' };
const DIRS = { both: { allow_long: true, allow_short: true }, long: { allow_long: true, allow_short: false }, short: { allow_long: false, allow_short: true } };
const BF_CONFIGS = [
  { key: 'off',        bf_exit: 'off',       bf_reentry: 'recycle' },
  { key: 'ss_recycle', bf_exit: 'same_side', bf_reentry: 'recycle' },
  { key: 'ss_ratc',    bf_exit: 'same_side', bf_reentry: 'ratchet_c' },
  { key: 'ss_ratg',    bf_exit: 'same_side', bf_reentry: 'ratchet_g' },
  { key: 'as_recycle', bf_exit: 'any_side',  bf_reentry: 'recycle' },
];
const ARM_EXIT_BY_CHART_TF = {
  '5':  [['15', '15'], ['5', '15'], ['5', '30'], ['15', '60']],
  '15': [['15', '15'], ['15', '30'], ['15', '60']],
  '60': [['60', '60'], ['60', '240']],
};
// A1 fixed axes (pre-reg): regime stand_aside on W+D, governor ratchet, BF-1 30/10.
const A1_FIXED = {
  reg_mode: 'stand_aside', rg1: false, rtf1: 'M', rg2: true, rtf2: 'W', rg3: true, rtf3: 'D',
  gov_mode: 'ratchet', bf_tf: '30', bf_strength: 10, bf_show_pivots: false,
  show_table: false, show_trig: false,
};
const A1_SYMBOLS = ['HIP3XYZ:MUUSDC.P', 'NASDAQ:MU'];

function cellId(c) {
  return [c.symbol, 'tf' + c.chart_tf, c.gate_set, c.exit_mode, c.dir, c.bf_key, 'a' + c.arm_tf, 'x' + c.exit_tf].join('_');
}

function buildStageA1Cells() {
  const cells = [];
  for (const symbol of A1_SYMBOLS)
    for (const chart_tf of Object.keys(ARM_EXIT_BY_CHART_TF))
      for (const [arm_tf, exit_tf] of ARM_EXIT_BY_CHART_TF[chart_tf])
        for (const gate_set of Object.keys(GATE_SETS))
          for (const exit_mode of ['state', 'flip'])
            for (const dir of Object.keys(DIRS))
              for (const bf of BF_CONFIGS)
                cells.push({ stage: 'A1', symbol, chart_tf, gate_set, exit_mode, dir, bf_key: bf.key, bf_exit: bf.bf_exit, bf_reentry: bf.bf_reentry, arm_tf, exit_tf });
  return cells;
}

// P3 anchors: E2 cells C1/C3/C6 on MU perp 5m (full6/flip/both + live fixed axes).
// Committed E2 targets (2026-07-11 window): C1 closed net +5288, C3 +7247, C6 +4301,
// ordering C3 > C1 > C6, first entry 2026-05-04 00:05 UTC. Drift-tolerant gate.
function buildAnchorCells() {
  const base = { stage: 'P3', symbol: 'HIP3XYZ:MUUSDC.P', chart_tf: '5', gate_set: 'full6', exit_mode: 'flip', dir: 'both' };
  return [
    { ...base, anchor: 'C1', bf_key: 'off', bf_exit: 'off', bf_reentry: 'recycle', arm_tf: '15', exit_tf: '15' },
    { ...base, anchor: 'C3', bf_key: 'ss_ratc', bf_exit: 'same_side', bf_reentry: 'ratchet_c', arm_tf: '15', exit_tf: '15' },
    { ...base, anchor: 'C6', bf_key: 'ss_ratc', bf_exit: 'same_side', bf_reentry: 'ratchet_c', arm_tf: '5', exit_tf: '30' },
  ];
}

function cellInputs(c) {
  const gates = GATE_SETS[c.gate_set];
  const dirs = DIRS[c.dir];
  const logical = {
    exit_mode: c.exit_mode, bf_exit: c.bf_exit, bf_reentry: c.bf_reentry,
    arm_tf: c.arm_tf, exit_tf: c.exit_tf,
    ...GATE_TFS, ...gates, ...dirs, ...A1_FIXED,
  };
  const byId = {};
  for (const [k, v] of Object.entries(logical)) byId[IN[k]] = v;
  return byId;
}

// Expected echo, constructed EXACTLY as the Pine builds cell_echo.
function expectedEcho(c) {
  const gates = GATE_SETS[c.gate_set];
  const order = [['y1', '60'], ['y2', '120'], ['y3', '240'], ['y4', 'D'], ['y5', 'W'], ['y6', 'M']];
  let g = '';
  for (const [yk, tf] of order) if (gates[yk]) g += tf + '.';
  const dirs = DIRS[c.dir];
  const d = (dirs.allow_long ? 'L' : '') + (dirs.allow_short ? 'S' : '');
  return `${c.exit_mode};${c.bf_exit};${c.bf_reentry};a${c.arm_tf};x${c.exit_tf};g${g};d${d};r${A1_FIXED.reg_mode};v${A1_FIXED.gov_mode}`;
}

async function findStudyId() {
  const st = await getState();
  const hit = (st.studies || []).find(s => s.name === STUDY_NAME);
  if (!hit) throw new Error(`Study "${STUDY_NAME}" not on the active chart. Add it, then retry.`);
  return hit.id;
}

// reportData metrics + trade list (tv_dump.mjs pattern, incl. closed/open assertions).
const reportExpr = prefix => `(function(){
  var model = window.TradingViewApi._activeChartWidgetWV.value()._chartWidget.model().model();
  var sources = model.dataSources();
  for (var i=0;i<sources.length;i++){ var s=sources[i]; if(!s.metaInfo) continue; var mi=s.metaInfo();
    if ((mi.isTVScriptStrategy===true || typeof s.reportData==='function') && (mi.description||'').indexOf('${prefix}') === 0){
      var rd = s.reportData(); if (rd && typeof rd.value==='function') rd = rd.value();
      if (!rd || !rd.performance) return {pending:true};
      var perf = rd.performance || {};
      var all = perf.all || {}, lng = perf.long || {}, sht = perf.short || {};
      function pick(o){ return {net: o.netProfitPercent, netAbs: o.netProfit, pf: o.profitFactor, trades: o.totalTrades,
        win: o.percentProfitable, dd: perf.maxStrategyDrawDownPercent,
        wins: o.numberOfWiningTrades, losses: o.numberOfLosingTrades, commission: o.commissionPaid}; }
      var tr = rd.trades || [];
      var closedN = all.totalTrades || 0;
      var openN = all.totalOpenTrades || 0;
      var lenOk = tr.length === closedN + openN;
      var list = [];
      for (var j=0;j<tr.length;j++){ var t=tr[j];
        list.push({et: t.e ? t.e.tm : null, xt: t.x ? t.x.tm : null,
                   ep: t.e ? t.e.p : null, xp: t.x ? t.x.p : null,
                   dir: t.e ? t.e.tp : null, pp: t.tp ? t.tp.p : null, q: t.q,
                   open: j >= closedN}); }
      return {net: all.netProfitPercent, netAbs: all.netProfit, trades: all.totalTrades,
              marginCalls: all.marginCalls, openTrades: all.totalOpenTrades,
              buyHold: perf.buyHoldReturnPercent, openPL: perf.openPL,
              assert: {listLen: tr.length, closedN: closedN, openN: openN, lenOk: lenOk},
              all: pick(all), long: pick(lng), short: pick(sht), list: list};
    } }
  return {error:'strategy not found in dataSources'};
})()`;
const REPORT_EXPR = reportExpr('TVB-EXP Champion');

// Engine-side readback: applied input values for the study + main-series symbol/interval.
// This is the settle gate's fallback integrity check when the pine-table echo is not
// materialized (the graphics channel is flaky for strategies behind other panels).
function appliedExpr(entityId) {
  return `(function(){
    var chart = window.TradingViewApi._activeChartWidgetWV.value();
    var study = chart.getStudyById('${entityId}');
    if (!study) return { error: 'study not found' };
    var iv = study.getInputValues();
    var m = {};
    for (var i=0;i<iv.length;i++) m[iv[i].id] = iv[i].value;
    var ms = chart._chartWidget.model().model().mainSeries();
    var sym = null, interval = null;
    try { sym = ms.symbolInfo() ? ms.symbolInfo().full_name || ms.symbolInfo().name : null; } catch(e){}
    try { interval = ms.interval ? ms.interval() : null; } catch(e){}
    return { inputs: m, symbol: sym, interval: interval };
  })()`;
}

function parseMetricsTables(tablesResult) {
  const study = (tablesResult.studies || []).find(s => (s.name || '').indexOf('TVB-EXP Champion') === 0);
  if (!study) return { found: false };
  const metrics = {};
  let tradeRows = [];
  for (const tbl of study.tables) {
    const rows = tbl.rows || [];
    if (rows.some(r => r.startsWith('METRICS'))) {
      for (const r of rows) {
        const idx = r.indexOf(' | ');
        if (idx > 0) metrics[r.slice(0, idx)] = r.slice(idx + 3);
      }
    } else if (rows.length && rows[0] === 'TRADES') {
      tradeRows = rows.slice(1).filter(r => r.startsWith('i='));
    }
  }
  return { found: true, metrics, tradeRows };
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// Load chart history to the floor (tv_probe.mjs pattern). A freshly-set symbol/TF
// loads only ~1 month of 5m bars; the pre-reg requires the DEEPEST loadable window,
// and the E2 anchors were run at the ~21.8k-bar floor. Loops requestMoreData until
// the series stops growing.
async function ensureHistoryLoaded() {
  let prevSize = -1;
  for (let round = 0; round < 250; round++) {
    const r = await evaluate(`(function(){
      var ms = window.TradingViewApi._activeChartWidgetWV.value()._chartWidget.model().model().mainSeries();
      try { ms.requestMoreData(500); } catch(e) { return { err: e.message, size: ms.bars().size() }; }
      return { size: ms.bars().size() };
    })()`);
    if (r && r.err) return { rounds: round, size: r.size, err: r.err };
    await sleep(700);
    const now = await evaluate(`window.TradingViewApi._activeChartWidgetWV.value()._chartWidget.model().model().mainSeries().bars().size()`);
    if (now === prevSize) return { rounds: round, size: now };
    prevSize = now;
  }
  return { rounds: 250, size: prevSize, capped: true };
}

// Settle gate: ECHO-FIRST (the script's own pine-table cell echo -- strongest signal),
// ENGINE-FALLBACK (applied input values + main-series symbol/interval readback) because
// the strategy's table graphics do not reliably re-materialize after input changes.
// Engine-path acceptance additionally requires the report to differ from the
// pre-setInputs snapshot (or 20s+ elapsed) so a stale result cannot be re-read.
async function settleAndRead(cell, entity, preKey) {
  const want = expectedEcho(cell);
  const wantInputs = cellInputs(cell);
  const t0 = Date.now();
  let stable = 0, lastKey = '', best = null;
  while (Date.now() - t0 < SETTLE_TIMEOUT_MS) {
    await sleep(SETTLE_POLL_MS);
    const report = await evaluate(REPORT_EXPR);
    if (!report || report.pending || report.error) continue;
    const parsed = parseMetricsTables(await getPineTables({ study_filter: 'TVB-EXP Champion' }));
    const echoOk = parsed.found && parsed.metrics.cell === want && parsed.metrics.symbol === cell.symbol;
    const applied = await evaluate(appliedExpr(entity));
    let engineOk = false;
    if (applied && applied.inputs) {
      engineOk = Object.entries(wantInputs).every(([k, v]) => String(applied.inputs[k]) === String(v))
        && applied.symbol === cell.symbol && String(applied.interval) === String(cell.chart_tf);
    }
    if (!echoOk && !engineOk) continue;
    const key = `${report.netAbs}|${report.trades}|${report.assert.listLen}`;
    if (key === lastKey) stable += 1; else { stable = 0; lastKey = key; }
    best = { parsed: parsed.found ? parsed : null, report, echoOk, engineOk };
    const changed = !preKey || `${report.netAbs}|${report.trades}` !== preKey;
    if (echoOk && stable >= 1) return { ok: true, via: 'echo', elapsed_ms: Date.now() - t0, ...best };
    if (engineOk && stable >= 2 && (changed || Date.now() - t0 > 20000))
      return { ok: true, via: 'engine', elapsed_ms: Date.now() - t0, ...best };
  }
  return { ok: false, via: null, elapsed_ms: Date.now() - t0, reject: 'settle timeout', ...(best || {}) };
}

function loadDone(outfile) {
  const done = new Set();
  if (fs.existsSync(outfile))
    for (const line of fs.readFileSync(outfile, 'utf8').split('\n'))
      if (line.trim()) { try { done.add(JSON.parse(line).id); } catch { /* skip */ } }
  return done;
}

async function runCells(cells, outfile) {
  const done = loadDone(outfile);
  const entity = await findStudyId();
  console.log(`study ${entity}; ${cells.length} cells requested; ${done.size} already in ${outfile}`);
  let curSymbol = null, curTf = null, i = 0, accepted = 0, rejected = 0;
  for (const cell of cells) {
    i += 1;
    const id = cellId(cell);
    if (done.has(id)) continue;
    let histInfo = null;
    if (cell.symbol !== curSymbol) { await setSymbol({ symbol: cell.symbol }); curSymbol = cell.symbol; curTf = null; await sleep(8000); }
    if (cell.chart_tf !== curTf) {
      await setTimeframe({ timeframe: cell.chart_tf });
      curTf = cell.chart_tf;
      await sleep(5000);
      histInfo = await ensureHistoryLoaded();
      console.log(`  history: ${histInfo.size} bars after ${histInfo.rounds} rounds${histInfo.err ? ' (err: ' + histInfo.err + ')' : ''}`);
    }
    const preRep = await evaluate(REPORT_EXPR);
    const preKey = preRep && !preRep.error && !preRep.pending ? `${preRep.netAbs}|${preRep.trades}` : null;
    await setInputs({ entity_id: entity, inputs: cellInputs(cell) });
    const res = await settleAndRead(cell, entity, preKey);
    const rec = {
      id, ...cell, expected_echo: expectedEcho(cell),
      accepted: res.ok, via: res.via, elapsed_ms: res.elapsed_ms,
      echo: res.parsed ? res.parsed.metrics.cell : null,
      metrics_table: res.parsed ? res.parsed.metrics : null,
      trade_table_rows: res.parsed ? res.parsed.tradeRows : null,
      report: res.report || null,
      reject: res.ok ? null : res.reject,
      collected_utc: new Date().toISOString(),
    };
    fs.appendFileSync(outfile, JSON.stringify(rec) + '\n');
    if (res.ok) { accepted += 1; } else { rejected += 1; }
    const m = res.report && res.report.all ? `net% ${(res.report.net * 100).toFixed(2)} trades ${res.report.trades}` : 'REJECTED';
    console.log(`[${i}/${cells.length}] ${id} -> ${res.ok ? 'OK/' + res.via : 'REJECT'} (${(res.elapsed_ms / 1000).toFixed(1)}s) ${m}`);
  }
  console.log(`done: ${accepted} accepted, ${rejected} rejected (this pass).`);
}

// ---- P3 anchor v2: cross-SCRIPT equivalence on a SHARED window --------------------
// The E2 numbers are not reproducible (TV's 5m data floor slid past May 1 and the
// monthly-open warmup then moves the first tradeable bar to June 1), so the anchor is
// run as a stronger check instead: the unchanged E2 engine ("TVB-EXP BF Exit [Claude]",
// old modulo clocks, 'ratchet') and the Champion (session-robust clocks, 'ratchet_c')
// compute the SAME cells on the SAME loaded bars and must agree trade-for-trade.
// This isolates exactly the P1 changes and IS the pre-registered clock-equivalence proof.
const BASE_NAME = 'TVB-EXP BF Exit [Claude]';
const BASE_REPORT_EXPR = reportExpr('TVB-EXP BF Exit [Claude]');

function baseInputs(cell) {
  const m = { ...cellInputs(cell) };
  if (m[IN.bf_reentry] === 'ratchet_c') m[IN.bf_reentry] = 'ratchet';
  if (m[IN.bf_reentry] === 'ratchet_g') throw new Error('ratchet_g has no base-script equivalent');
  return m;
}

function diffTradeLists(a, b) {
  const ca = (a || []).filter(t => !t.open), cb = (b || []).filter(t => !t.open);
  if (ca.length !== cb.length) return { equal: false, why: `closed counts differ: ${ca.length} vs ${cb.length}` };
  for (let i = 0; i < ca.length; i++) {
    const x = ca[i], y = cb[i];
    if (x.et !== y.et || x.xt !== y.xt || x.dir !== y.dir) return { equal: false, why: `trade ${i} time/dir differ`, a: x, b: y };
    if (Math.abs(x.ep - y.ep) > 1e-9 || Math.abs(x.xp - y.xp) > 1e-9) return { equal: false, why: `trade ${i} prices differ`, a: x, b: y };
    if (Math.abs((x.q ?? 0) - (y.q ?? 0)) > 1e-6) return { equal: false, why: `trade ${i} qty differ`, a: x, b: y };
  }
  return { equal: true, closed: ca.length };
}

async function runAnchor2(outfile) {
  const st = await getState();
  const champ = (st.studies || []).find(s => s.name === STUDY_NAME);
  const base = (st.studies || []).find(s => s.name === BASE_NAME);
  if (!champ) throw new Error('Champion study not on chart');
  if (!base) throw new Error(`"${BASE_NAME}" study not on chart -- add it first`);
  const cells = buildAnchorCells();
  let curSymbol = null, curTf = null;
  for (const cell of cells) {
    if (cell.symbol !== curSymbol) { await setSymbol({ symbol: cell.symbol }); curSymbol = cell.symbol; curTf = null; await sleep(8000); }
    if (cell.chart_tf !== curTf) {
      await setTimeframe({ timeframe: cell.chart_tf }); curTf = cell.chart_tf; await sleep(5000);
      const h = await ensureHistoryLoaded();
      console.log(`  history: ${h.size} bars after ${h.rounds} rounds`);
    }
    const preC = await evaluate(REPORT_EXPR);
    const preKey = preC && !preC.error && !preC.pending ? `${preC.netAbs}|${preC.trades}` : null;
    await setInputs({ entity_id: base.id, inputs: baseInputs(cell) });
    await setInputs({ entity_id: champ.id, inputs: cellInputs(cell) });
    const res = await settleAndRead(cell, champ.id, preKey);
    // base settle: poll until base report stable twice (engine inputs already verified applied)
    let baseRep = null, lastKey = '', stable = 0;
    const t0 = Date.now();
    while (Date.now() - t0 < SETTLE_TIMEOUT_MS) {
      await sleep(SETTLE_POLL_MS);
      const r = await evaluate(BASE_REPORT_EXPR);
      if (!r || r.pending || r.error) continue;
      const key = `${r.netAbs}|${r.trades}`;
      if (key === lastKey) stable += 1; else { stable = 0; lastKey = key; }
      baseRep = r;
      if (stable >= 2) break;
    }
    const diff = res.ok && baseRep ? diffTradeLists(res.report.list, baseRep.list) : { equal: false, why: 'one side failed to settle' };
    const rec = {
      id: cellId(cell) + '_x2', ...cell, anchor_mode: 'cross-script',
      champion_ok: res.ok, via: res.via,
      champion: res.report ? { netAbs: res.report.netAbs, net: res.report.net, trades: res.report.trades, list: res.report.list } : null,
      base: baseRep ? { netAbs: baseRep.netAbs, net: baseRep.net, trades: baseRep.trades, list: baseRep.list } : null,
      trade_table_rows: res.parsed ? res.parsed.tradeRows : null,
      metrics_table: res.parsed ? res.parsed.metrics : null,
      diff,
      collected_utc: new Date().toISOString(),
    };
    fs.appendFileSync(outfile, JSON.stringify(rec) + '\n');
    console.log(`ANCHOR ${cell.anchor}: champion ${res.ok ? 'ok/' + res.via : 'FAIL'} net ${res.report ? res.report.netAbs?.toFixed(2) : 'na'} tr ${res.report ? res.report.trades : 'na'} | base net ${baseRep ? baseRep.netAbs?.toFixed(2) : 'na'} tr ${baseRep ? baseRep.trades : 'na'} | EQUAL: ${diff.equal}${diff.why ? ' (' + diff.why + ')' : ''}`);
  }
}

const cmd = process.argv[2] || 'status';
try {
  if (cmd === 'status') {
    const st = await getState();
    console.log(JSON.stringify(st, null, 2));
    const rep = await evaluate(REPORT_EXPR);
    console.log(JSON.stringify({ trades: rep.trades, netAbs: rep.netAbs, error: rep.error, pending: rep.pending }, null, 2));
  } else if (cmd === 'cells') {
    const cells = buildStageA1Cells();
    console.log(JSON.stringify(cells, null, 1));
    console.error(`total: ${cells.length}`);
  } else if (cmd === 'anchor') {
    const outfile = process.argv[3] || 'docs/experiments/tvb11_champion_anchor.jsonl';
    await runCells(buildAnchorCells(), outfile);
  } else if (cmd === 'anchor2') {
    const outfile = process.argv[3] || 'docs/experiments/tvb11_champion_anchor2.jsonl';
    await runAnchor2(outfile);
  } else if (cmd === 'run') {
    const cellsFile = process.argv[3];
    const outfile = process.argv[4];
    if (!cellsFile || !outfile) { console.error('usage: run <cells.json> <out.jsonl> [--limit N] [--start K]'); process.exit(1); }
    let cells = JSON.parse(fs.readFileSync(cellsFile, 'utf8'));
    const lim = process.argv.indexOf('--limit');
    const sta = process.argv.indexOf('--start');
    if (sta > 0) cells = cells.slice(Number(process.argv[sta + 1]));
    if (lim > 0) cells = cells.slice(0, Number(process.argv[lim + 1]));
    await runCells(cells, outfile);
  } else {
    console.error('unknown cmd:', cmd);
  }
} finally {
  await disconnect();
}
