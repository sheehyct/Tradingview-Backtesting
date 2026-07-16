// TVB-12 bounded-replay collector -- FAIL-CLOSED rework of the TVB-11 collector
// (scripts/tvb11_champion_collect.mjs, kept untouched as the record of what ran).
// Audit remediation (docs/reviews/tvb11-codex-audit.md Findings 1/2/4):
//
//   F1: acceptance is nonce-bound and fail-closed. Every attempt applies a fresh
//       nonce input; the strategy echoes it in its METRICS table. A run is accepted
//       ONLY when ALL of the following hold on >=2 consecutive stable polls:
//         echoOk   -- pine table echoes nonce + cell + symbol + chart_tf + session
//                     + bf_tf + bf_strength exactly as requested;
//         engineOk -- entity-bound applied-input readback matches every requested
//                     input (incl. the nonce) AND main-series symbol/interval/
//                     subsession match;
//         bindOk   -- the reportData totals equal the pine table's totals from the
//                     SAME compute pass (trades, net_abs, open PL, open trades) --
//                     this chains report -> table -> nonce -> inputs causally.
//       There is NO engine-only path, NO elapsed-time escape. Reject -> retry with
//       a fresh nonce (max 3 attempts), then record the rejection. Every accepted
//       record persists the full metrics table (incl. loaded window), the applied
//       readback, the nonce, and the trade list.
//   F2: the replay cell list (buildReplayCells) restores the omitted 5m short
//       champion and adds matched long/short/both + BF-off direction controls.
//   F4: anchor2 verifies the BASE study's applied inputs via entity readback
//       (the TVB-11 version only set them and polled for stability).
//
// Requires the [TVB-12r] artifact (pine/tvb_exp_champion.pine v2, nonce input
// in_32) deployed via fresh Make-a-copy and added to the chart.
//
// Usage:
//   node scripts/tvb12_replay_collect.mjs status
//   node scripts/tvb12_replay_collect.mjs inputs                # dump applied input ids (IN-map verification)
//   node scripts/tvb12_replay_collect.mjs cells                 # print replay cell list (JSON)
//   node scripts/tvb12_replay_collect.mjs anchor2 <out.jsonl>   # cross-script anchors C1/C3/C6, hardened
//   node scripts/tvb12_replay_collect.mjs run <cells.json> <out.jsonl> [--limit N] [--start K] [--tags R1,R4]
//
// Checkpointing: accepted ids in the outfile are skipped on resume (rejects re-run).
import { evaluate, disconnect } from 'file:///C:/Strat_Trading_Bot/tradingview-mcp-jackson/src/connection.js';
import { setSymbol, setTimeframe, getState } from 'file:///C:/Strat_Trading_Bot/tradingview-mcp-jackson/src/core/chart.js';
import { setInputs } from 'file:///C:/Strat_Trading_Bot/tradingview-mcp-jackson/src/core/indicators.js';
import { getPineTables } from 'file:///C:/Strat_Trading_Bot/tradingview-mcp-jackson/src/core/data.js';
import fs from 'node:fs';

const STUDY_NAME = 'TVB-EXP Champion [TVB-12r]';
const BASE_NAME = 'TVB-EXP BF Exit [Claude]';
const SETTLE_POLL_MS = 2000;
const SETTLE_TIMEOUT_MS = 120000;
const MAX_ATTEMPTS = 3;

// ---- input id map (MUST be re-verified against the deployed [TVB-12r] artifact with
// the `inputs` command before any run; declaration order, nonce appended LAST) ----
const IN = {
  exit_mode: 'in_0', bf_exit: 'in_1', bf_reentry: 'in_2', arm_tf: 'in_3', exit_tf: 'in_4',
  y1: 'in_5', tf1: 'in_6', y2: 'in_7', tf2: 'in_8', y3: 'in_9', tf3: 'in_10',
  y4: 'in_11', tf4: 'in_12', y5: 'in_13', tf5: 'in_14', y6: 'in_15', tf6: 'in_16',
  allow_long: 'in_17', allow_short: 'in_18',
  reg_mode: 'in_19', rg1: 'in_20', rtf1: 'in_21', rg2: 'in_22', rtf2: 'in_23', rg3: 'in_24', rtf3: 'in_25',
  gov_mode: 'in_26', bf_tf: 'in_27', bf_strength: 'in_28', bf_show_pivots: 'in_29',
  show_table: 'in_30', show_trig: 'in_31', nonce: 'in_32',
};

const GATE_SETS = {
  full6:  { y1: true,  y2: true,  y3: true,  y4: true, y5: true, y6: true },
  ctrlA4: { y1: true,  y2: false, y3: false, y4: true, y5: true, y6: true },
  slow3:  { y1: false, y2: false, y3: false, y4: true, y5: true, y6: true },
};
const GATE_TFS = { tf1: '60', tf2: '120', tf3: '240', tf4: 'D', tf5: 'W', tf6: 'M' };
const DIRS = { both: { allow_long: true, allow_short: true }, long: { allow_long: true, allow_short: false }, short: { allow_long: false, allow_short: true } };
const FIXED = {
  reg_mode: 'stand_aside', rg1: false, rtf1: 'M', rg2: true, rtf2: 'W', rg3: true, rtf3: 'D',
  gov_mode: 'ratchet', bf_tf: '30', bf_strength: 10, bf_show_pivots: false,
  show_table: false, show_trig: false,
};
const BFK = {
  off:        { bf_exit: 'off',       bf_reentry: 'recycle' },
  ss_recycle: { bf_exit: 'same_side', bf_reentry: 'recycle' },
  ss_ratc:    { bf_exit: 'same_side', bf_reentry: 'ratchet_c' },
  ss_ratg:    { bf_exit: 'same_side', bf_reentry: 'ratchet_g' },
  as_recycle: { bf_exit: 'any_side',  bf_reentry: 'recycle' },
};

function cellId(c) {
  return [c.symbol, 'tf' + c.chart_tf, c.gate_set, c.exit_mode, c.dir, c.bf_key, 'a' + c.arm_tf, 'x' + c.exit_tf].join('_');
}
function isRthMirror(symbol) { return /^(NASDAQ|NYSE|AMEX):/.test(symbol); }
function expectedBfTf(c) { return c.chart_tf === '60' && c.bf_exit === 'off' ? '60' : '30'; }

function cellInputs(c) {
  const logical = {
    exit_mode: c.exit_mode, bf_exit: c.bf_exit, bf_reentry: c.bf_reentry,
    arm_tf: c.arm_tf, exit_tf: c.exit_tf,
    ...GATE_TFS, ...GATE_SETS[c.gate_set], ...DIRS[c.dir], ...FIXED,
  };
  // 60m BF-off neutralization (TVB-11 amendment): unused BF pivot TF raised to the
  // chart TF; a trading no-op verified by the TVB-11 audit.
  if (c.chart_tf === '60' && c.bf_exit === 'off') logical.bf_tf = '60';
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
  return `${c.exit_mode};${c.bf_exit};${c.bf_reentry};a${c.arm_tf};x${c.exit_tf};g${g};d${d};r${FIXED.reg_mode};v${FIXED.gov_mode}`;
}

// ---- replay cell list (docs/experiments/tvb12_replay_plan.md) ----
const PERP = 'HIP3XYZ:MUUSDC.P', MIR = 'NASDAQ:MU';
const ROSTER = ['HIP3XYZ:HOODUSDC.P', 'HIP3XYZ:HIMSUSDC.P', 'HIP3XYZ:RKLBUSDC.P',
  'HIP3XYZ:ORCLUSDC.P', 'HIP3XYZ:NFLXUSDC.P', 'HIP3XYZ:MRVLUSDC.P', 'HIP3XYZ:SILVERUSDC.P'];
const R3_FULL = ROSTER.slice(0, 3);   // all 10 finalists
const R3_GEN = ROSTER.slice(3);       // generalizer config only

// Stage B's 10 finalist configs VERBATIM (docs/experiments/tvb11_champion_cells_b.json):
// [chart_tf, gate_set, exit_mode, dir, bf_key, arm_tf, exit_tf]
const FINALISTS = [
  ['15', 'slow3',  'flip', 'long', 'ss_recycle', '15', '60'],
  ['15', 'full6',  'flip', 'long', 'ss_recycle', '15', '60'],
  ['15', 'ctrlA4', 'flip', 'long', 'ss_recycle', '15', '60'],
  ['15', 'slow3',  'flip', 'long', 'ss_ratc',    '15', '60'],
  ['15', 'full6',  'flip', 'long', 'ss_ratc',    '15', '60'],
  ['15', 'ctrlA4', 'flip', 'long', 'ss_ratc',    '15', '60'],
  ['15', 'slow3',  'flip', 'long', 'ss_recycle', '15', '15'],
  ['60', 'ctrlA4', 'flip', 'long', 'off',        '60', '60'],
  ['60', 'slow3',  'flip', 'long', 'off',        '60', '60'],
  ['60', 'full6',  'flip', 'long', 'off',        '60', '60'],
];
const GEN = ['15', 'slow3', 'flip', 'long', 'ss_ratc', '15', '60']; // the "Generalizer"

function C(tag, symbol, chart_tf, gate_set, exit_mode, dir, bf_key, arm_tf, exit_tf) {
  return { stage: 'R', tag, symbol, chart_tf, gate_set, exit_mode, dir, bf_key, ...BFK[bf_key], arm_tf, exit_tf };
}
function fromF(tag, symbol, f, dirOverride) {
  const [tf, g, x, d, b, a, e] = f;
  return C(tag, symbol, tf, g, x, dirOverride || d, b, a, e);
}

function buildReplayCells() {
  const cells = [];
  // R1 -- per-TF champions (incl. the omitted 5m SHORT champion, a1.jsonl:343).
  cells.push(C('R1', PERP, '5', 'slow3', 'state', 'short', 'ss_ratc', '15', '60'));
  cells.push(C('R1', PERP, '15', 'slow3', 'flip', 'long', 'ss_recycle', '15', '60'));
  cells.push(C('R1', PERP, '60', 'ctrlA4', 'flip', 'long', 'off', '60', '60'));
  cells.push(C('R1', MIR, '5', 'slow3', 'flip', 'long', 'off', '5', '30'));
  cells.push(C('R1', MIR, '15', 'slow3', 'flip', 'long', 'off', '15', '30'));
  cells.push(C('R1', MIR, '60', 'slow3', 'flip', 'long', 'off', '60', '60'));
  // R2 -- ctrlA-equivalent controls, both venues.
  for (const sym of [PERP, MIR]) {
    cells.push(C('R2', sym, '5', 'ctrlA4', 'state', 'both', 'off', '15', '15'));
    cells.push(C('R2', sym, '15', 'ctrlA4', 'state', 'both', 'off', '15', '15'));
    cells.push(C('R2', sym, '60', 'ctrlA4', 'state', 'both', 'off', '60', '60'));
  }
  // R3 -- Stage B finalists on a 3-symbol subset + generalizer on the remaining 4.
  for (const sym of R3_FULL) for (const f of FINALISTS) cells.push(fromF('R3', sym, f));
  for (const sym of R3_GEN) cells.push(fromF('R3', sym, GEN));
  // R4 -- direction repair (NEW evidence, audit F2).
  cells.push(C('R4', PERP, '5', 'slow3', 'state', 'long', 'ss_ratc', '15', '60'));
  cells.push(C('R4', PERP, '5', 'slow3', 'state', 'both', 'ss_ratc', '15', '60'));
  for (const d of ['long', 'short', 'both']) cells.push(fromF('R4', PERP, GEN, d));
  for (const sym of ROSTER) for (const d of ['short', 'both']) cells.push(fromF('R4', sym, GEN, d));
  for (const d of ['long', 'short', 'both']) cells.push(C('R4', PERP, '15', 'slow3', 'flip', d, 'off', '15', '60'));
  // Dedupe guard: a config+symbol pair must appear exactly once.
  const seen = new Set();
  for (const c of cells) {
    const id = cellId(c);
    if (seen.has(id)) throw new Error('duplicate replay cell: ' + id);
    seen.add(id);
  }
  // Minimal symbol/TF switching.
  const symOrder = [PERP, MIR, ...ROSTER];
  cells.sort((a, b) => symOrder.indexOf(a.symbol) - symOrder.indexOf(b.symbol) || Number(a.chart_tf) - Number(b.chart_tf));
  return cells;
}

// P3 anchors: E2 cells C1/C3/C6 on MU perp 5m.
function buildAnchorCells() {
  const base = { stage: 'P3r', tag: 'R0', symbol: PERP, chart_tf: '5', gate_set: 'full6', exit_mode: 'flip', dir: 'both' };
  return [
    { ...base, anchor: 'C1', bf_key: 'off', bf_exit: 'off', bf_reentry: 'recycle', arm_tf: '15', exit_tf: '15' },
    { ...base, anchor: 'C3', bf_key: 'ss_ratc', bf_exit: 'same_side', bf_reentry: 'ratchet_c', arm_tf: '15', exit_tf: '15' },
    { ...base, anchor: 'C6', bf_key: 'ss_ratc', bf_exit: 'same_side', bf_reentry: 'ratchet_c', arm_tf: '5', exit_tf: '30' },
  ];
}

// ---- chart/report plumbing ----
async function findStudyByName(name) {
  const st = await getState();
  const hit = (st.studies || []).find(s => s.name === name);
  if (!hit) throw new Error(`Study "${name}" not on the active chart. Add it, then retry.`);
  return hit.id;
}

// Entity-bound report read: prefer the dataSource whose id matches the study entity;
// fall back to EXACT description match (unique -- the [TVB-12r] name is versioned).
function reportExpr(entityId, exactName) {
  return `(function(){
  var model = window.TradingViewApi._activeChartWidgetWV.value()._chartWidget.model().model();
  var sources = model.dataSources();
  var byId = null, byName = null;
  for (var i=0;i<sources.length;i++){ var s=sources[i]; if(!s.metaInfo) continue; var mi=s.metaInfo();
    if (!(mi.isTVScriptStrategy===true || typeof s.reportData==='function')) continue;
    var sid = null;
    try { sid = typeof s.id==='function' ? s.id() : (s._id !== undefined ? s._id : null); } catch(e){}
    if (sid === '${entityId}') { byId = s; break; }
    if ((mi.description||'') === '${exactName}' && !byName) byName = s;
  }
  var src = byId || byName;
  if (!src) return {error:'strategy not found by entity id or exact name'};
  var rd = src.reportData(); if (rd && typeof rd.value==='function') rd = rd.value();
  if (!rd || !rd.performance) return {pending:true};
  var perf = rd.performance || {};
  var all = perf.all || {}, lng = perf.long || {}, sht = perf.short || {};
  function pick(o){ return {net: o.netProfitPercent, netAbs: o.netProfit, pf: o.profitFactor, trades: o.totalTrades,
    win: o.percentProfitable, dd: perf.maxStrategyDrawDownPercent,
    wins: o.numberOfWiningTrades, losses: o.numberOfLosingTrades, commission: o.commissionPaid}; }
  var tr = rd.trades || [];
  var closedN = all.totalTrades || 0;
  var openN = all.totalOpenTrades || 0;
  var list = [];
  for (var j=0;j<tr.length;j++){ var t=tr[j];
    list.push({et: t.e ? t.e.tm : null, xt: t.x ? t.x.tm : null,
               ep: t.e ? t.e.p : null, xp: t.x ? t.x.p : null,
               dir: t.e ? t.e.tp : null, pp: t.tp ? t.tp.p : null, q: t.q,
               open: j >= closedN}); }
  return {bound: byId ? 'id' : 'name',
          net: all.netProfitPercent, netAbs: all.netProfit, trades: all.totalTrades,
          marginCalls: all.marginCalls, openTrades: all.totalOpenTrades,
          buyHold: perf.buyHoldReturnPercent, openPL: perf.openPL,
          assert: {listLen: tr.length, closedN: closedN, openN: openN, lenOk: tr.length === closedN + openN},
          all: pick(all), long: pick(lng), short: pick(sht), list: list};
})()`;
}

function appliedExpr(entityId) {
  return `(function(){
    var chart = window.TradingViewApi._activeChartWidgetWV.value();
    var study = chart.getStudyById('${entityId}');
    if (!study) return { error: 'study not found' };
    var iv = study.getInputValues();
    var m = {};
    for (var i=0;i<iv.length;i++) m[iv[i].id] = iv[i].value;
    var ms = chart._chartWidget.model().model().mainSeries();
    var sym = null, interval = null, subsession = null;
    try { sym = ms.symbolInfo() ? ms.symbolInfo().full_name || ms.symbolInfo().name : null; } catch(e){}
    try { interval = ms.interval ? ms.interval() : null; } catch(e){}
    try { subsession = ms.symbolInfo() ? ms.symbolInfo().subsession_id : null; } catch(e){}
    return { inputs: m, symbol: sym, interval: interval, subsession: subsession };
  })()`;
}

function parseMetricsTables(tablesResult) {
  const study = (tablesResult.studies || []).find(s => (s.name || '') === STUDY_NAME);
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

// FAIL-CLOSED settle gate. One attempt = one fresh nonce applied with the cell inputs;
// acceptance requires echoOk AND engineOk AND bindOk on >=2 consecutive stable polls.
async function settleAndRead(cell, entity, attempt) {
  const nonce = `r${Date.now().toString(36)}_${attempt}_${Math.floor(Math.random() * 1e6)}`;
  const wantInputs = { ...cellInputs(cell), [IN.nonce]: nonce };
  await setInputs({ entity_id: entity, inputs: wantInputs });
  const want = expectedEcho(cell);
  const bfTf = expectedBfTf(cell);
  const t0 = Date.now();
  let stable = 0, lastKey = '', best = null, lastWhy = 'no accepted poll';
  while (Date.now() - t0 < SETTLE_TIMEOUT_MS) {
    await sleep(SETTLE_POLL_MS);
    const report = await evaluate(reportExpr(entity, STUDY_NAME));
    if (!report || report.pending || report.error) { lastWhy = 'report pending/error'; continue; }
    const parsed = parseMetricsTables(await getPineTables({ study_filter: STUDY_NAME }));
    const m = parsed.found ? parsed.metrics : {};
    const echoOk = parsed.found
      && m.nonce === nonce
      && m.cell === want
      && m.symbol === cell.symbol
      && String(m.chart_tf) === String(cell.chart_tf)
      && m.bf_tf === bfTf
      && String(m.bf_strength) === '10'
      && (!isRthMirror(cell.symbol) || m.session === 'regular');
    const applied = await evaluate(appliedExpr(entity));
    let engineOk = false;
    if (applied && applied.inputs) {
      engineOk = Object.entries(wantInputs).every(([k, v]) => String(applied.inputs[k]) === String(v))
        && applied.symbol === cell.symbol && String(applied.interval) === String(cell.chart_tf)
        && (!isRthMirror(cell.symbol) || applied.subsession === 'regular');
    }
    // report<->table binding: totals must agree with the SAME pass that echoed the nonce.
    const bindOk = parsed.found
      && report.trades === Number(m.closed_trades)
      && report.openTrades === Number(m.open_trades)
      && Math.abs(report.netAbs - Number(m.net_abs)) < 0.01
      && Math.abs((report.openPL ?? 0) - Number(m.open_pl_abs)) < 0.01;
    if (!echoOk || !engineOk || !bindOk) {
      lastWhy = `echoOk=${echoOk} engineOk=${engineOk} bindOk=${bindOk}` + (parsed.found ? ` nonce=${m.nonce === nonce}` : ' table-missing');
      stable = 0; lastKey = '';
      continue;
    }
    const key = `${report.netAbs}|${report.trades}|${report.assert.listLen}|${m.total_net_abs}`;
    if (key === lastKey) stable += 1; else { stable = 0; lastKey = key; }
    best = { parsed, report, applied, nonce };
    if (stable >= 2) return { ok: true, via: 'nonce+engine+bind', elapsed_ms: Date.now() - t0, ...best };
  }
  return { ok: false, via: null, elapsed_ms: Date.now() - t0, reject: `settle timeout (fail-closed): ${lastWhy}`, nonce, ...(best || {}) };
}

function loadDone(outfile) {
  const done = new Set();
  if (fs.existsSync(outfile))
    for (const line of fs.readFileSync(outfile, 'utf8').split('\n'))
      if (line.trim()) { try { const r = JSON.parse(line); if (r.accepted) done.add(r.id); } catch { /* skip */ } }
  return done;
}

async function preflight(cell, cur) {
  if (cell.symbol !== cur.symbol) {
    await setSymbol({ symbol: cell.symbol });
    cur.symbol = cell.symbol; cur.tf = null;
    await sleep(8000);
    if (isRthMirror(cell.symbol)) {
      const s = await evaluate(`(function(){
        var ms = window.TradingViewApi._activeChartWidgetWV.value()._chartWidget.model().model().mainSeries();
        try { ms.sessionIdProxyProperty().setValue('regular'); } catch(e){ return { err: e.message }; }
        return { ok: true };
      })()`);
      if (s && s.err) throw new Error('could not set regular session: ' + s.err);
      await sleep(6000);
    }
  }
  if (cell.chart_tf !== cur.tf) {
    await setTimeframe({ timeframe: cell.chart_tf });
    cur.tf = cell.chart_tf;
    await sleep(5000);
    const h = await ensureHistoryLoaded();
    console.log(`  history: ${h.size} bars after ${h.rounds} rounds${h.err ? ' (err: ' + h.err + ')' : ''}`);
  }
}

async function runCells(cells, outfile) {
  const done = loadDone(outfile);
  const entity = await findStudyByName(STUDY_NAME);
  console.log(`study ${entity} ("${STUDY_NAME}"); ${cells.length} cells requested; ${done.size} already in ${outfile}`);
  const cur = { symbol: null, tf: null };
  let i = 0, accepted = 0, rejected = 0;
  for (const cell of cells) {
    i += 1;
    const id = cellId(cell);
    if (done.has(id)) continue;
    await preflight(cell, cur);
    let res = null, attempts = 0;
    for (let a = 1; a <= MAX_ATTEMPTS; a++) {
      attempts = a;
      res = await settleAndRead(cell, entity, a);
      if (res.ok) break;
      console.log(`  attempt ${a} rejected: ${res.reject}`);
    }
    const rec = {
      id, ...cell, expected_echo: expectedEcho(cell),
      accepted: res.ok, via: res.via, attempts, nonce: res.nonce, elapsed_ms: res.elapsed_ms,
      echo: res.parsed ? res.parsed.metrics.cell : null,
      metrics_table: res.parsed ? res.parsed.metrics : null,
      trade_table_rows: res.parsed ? res.parsed.tradeRows : null,
      applied: res.applied || null,
      report: res.report || null,
      reject: res.ok ? null : res.reject,
      collected_utc: new Date().toISOString(),
    };
    fs.appendFileSync(outfile, JSON.stringify(rec) + '\n');
    if (res.ok) { accepted += 1; } else { rejected += 1; }
    const msg = res.report && res.report.all ? `net% ${(res.report.net * 100).toFixed(2)} trades ${res.report.trades}` : 'REJECTED';
    console.log(`[${i}/${cells.length}] ${id} -> ${res.ok ? 'OK/' + res.via : 'REJECT'} (${(res.elapsed_ms / 1000).toFixed(1)}s, try ${attempts}) ${msg}`);
  }
  console.log(`done: ${accepted} accepted, ${rejected} rejected (this pass).`);
}

// ---- anchor2: cross-script equivalence, hardened with BASE entity readback (F4) ----
function baseInputs(cell) {
  const m = { ...cellInputs(cell) };
  delete m[IN.nonce];
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
  const champ = await findStudyByName(STUDY_NAME);
  const base = await findStudyByName(BASE_NAME);
  const cells = buildAnchorCells();
  const cur = { symbol: null, tf: null };
  for (const cell of cells) {
    await preflight(cell, cur);
    const bWant = baseInputs(cell);
    await setInputs({ entity_id: base, inputs: bWant });
    // F4 fix: actual entity readback on the base study, not just set-and-wait.
    await sleep(2000);
    const bApplied = await evaluate(appliedExpr(base));
    const baseAppliedOk = bApplied && bApplied.inputs
      && Object.entries(bWant).every(([k, v]) => String(bApplied.inputs[k]) === String(v))
      && bApplied.symbol === cell.symbol && String(bApplied.interval) === String(cell.chart_tf);
    let res = null;
    for (let a = 1; a <= MAX_ATTEMPTS; a++) { res = await settleAndRead(cell, champ, a); if (res.ok) break; }
    // Base settle: entity-bound report, stable twice, applied inputs re-verified.
    let baseRep = null, lastKey = '', stable = 0;
    const t0 = Date.now();
    while (Date.now() - t0 < SETTLE_TIMEOUT_MS) {
      await sleep(SETTLE_POLL_MS);
      const r = await evaluate(reportExpr(base, BASE_NAME));
      if (!r || r.pending || r.error) continue;
      const key = `${r.netAbs}|${r.trades}`;
      if (key === lastKey) stable += 1; else { stable = 0; lastKey = key; }
      baseRep = r;
      if (stable >= 2) break;
    }
    const bApplied2 = await evaluate(appliedExpr(base));
    const baseAppliedOk2 = bApplied2 && bApplied2.inputs
      && Object.entries(bWant).every(([k, v]) => String(bApplied2.inputs[k]) === String(v));
    const diff = res.ok && baseRep && baseAppliedOk && baseAppliedOk2
      ? diffTradeLists(res.report.list, baseRep.list)
      : { equal: false, why: !res.ok ? 'champion failed to settle' : !baseRep ? 'base failed to settle' : 'base applied-input readback failed' };
    const rec = {
      id: cellId(cell) + '_x2r', ...cell, anchor_mode: 'cross-script-hardened',
      champion_ok: res.ok, via: res.via, nonce: res.nonce,
      base_applied_ok: !!(baseAppliedOk && baseAppliedOk2), base_bound: baseRep ? baseRep.bound : null,
      champion: res.report ? { netAbs: res.report.netAbs, net: res.report.net, trades: res.report.trades, list: res.report.list } : null,
      base: baseRep ? { netAbs: baseRep.netAbs, net: baseRep.net, trades: baseRep.trades, list: baseRep.list } : null,
      metrics_table: res.parsed ? res.parsed.metrics : null,
      applied: res.applied || null,
      diff,
      collected_utc: new Date().toISOString(),
    };
    fs.appendFileSync(outfile, JSON.stringify(rec) + '\n');
    console.log(`ANCHOR ${cell.anchor}: champ ${res.ok ? 'ok/' + res.via : 'FAIL'} net ${res.report ? res.report.netAbs?.toFixed(2) : 'na'} tr ${res.report ? res.report.trades : 'na'} | base(applied ${rec.base_applied_ok}) net ${baseRep ? baseRep.netAbs?.toFixed(2) : 'na'} tr ${baseRep ? baseRep.trades : 'na'} | EQUAL: ${diff.equal}${diff.why ? ' (' + diff.why + ')' : ''}`);
  }
}

const cmd = process.argv[2] || 'status';
try {
  if (cmd === 'status') {
    const st = await getState();
    console.log(JSON.stringify((st.studies || []).map(s => ({ id: s.id, name: s.name })), null, 2));
  } else if (cmd === 'inputs') {
    const entity = await findStudyByName(STUDY_NAME);
    const applied = await evaluate(appliedExpr(entity));
    console.log(JSON.stringify(applied, null, 2));
  } else if (cmd === 'cells') {
    const cells = buildReplayCells();
    console.log(JSON.stringify(cells, null, 1));
    console.error(`total: ${cells.length}`);
  } else if (cmd === 'anchor2') {
    const outfile = process.argv[3] || 'docs/experiments/tvb12_replay_anchor2.jsonl';
    await runAnchor2(outfile);
  } else if (cmd === 'run') {
    const cellsFile = process.argv[3];
    const outfile = process.argv[4];
    if (!cellsFile || !outfile) { console.error('usage: run <cells.json> <out.jsonl> [--limit N] [--start K] [--tags R1,R4]'); process.exit(1); }
    let cells = JSON.parse(fs.readFileSync(cellsFile, 'utf8'));
    const tags = process.argv.indexOf('--tags');
    if (tags > 0) { const want = new Set(process.argv[tags + 1].split(',')); cells = cells.filter(c => want.has(c.tag)); }
    const sta = process.argv.indexOf('--start');
    if (sta > 0) cells = cells.slice(Number(process.argv[sta + 1]));
    const lim = process.argv.indexOf('--limit');
    if (lim > 0) cells = cells.slice(0, Number(process.argv[lim + 1]));
    await runCells(cells, outfile);
  } else {
    console.error('unknown cmd:', cmd);
  }
} finally {
  await disconnect();
}
