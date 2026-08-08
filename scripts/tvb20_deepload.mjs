// TVB-20 control-port deep-load -- load the ACTIVE strategy chart's history to
// the data floor and report the first/last loaded bar. The parity contract
// slices the twin's TV-bar feed to start at first_bar_ts, so both sides share
// the same cold-start warm-up (see docs/experiments/ tvb20 parity doc).
// Reuses the TVB-19 harvest mechanics (requestMoreData + STABLE_ROUNDS floor).
// Usage: node scripts/tvb20_deepload.mjs <COIN>   (e.g. GOOGL, TSLA, DRAM)
// Prints one JSON line; exit 1 unless the floor was reached cleanly.
import { evaluate, disconnect } from 'file:///C:/Strat_Trading_Bot/tradingview-mcp-jackson/src/connection.js';

const COIN = process.argv[2];
if (!COIN) {
  console.error('usage: node scripts/tvb20_deepload.mjs <COIN>');
  process.exit(2);
}
const TV_SYM = `HIP3XYZ:${COIN}USDC.P`;
const CHART = 'window.TradingViewApi._activeChartWidgetWV.value()';
const MS = `${CHART}._chartWidget.model().model().mainSeries()`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const STABLE_ROUNDS = 3;

async function poll(exprCheck, timeoutMs, label) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeoutMs) {
    try {
      if (await evaluate(exprCheck)) return true;
    } catch {}
    await sleep(1000);
  }
  console.error(`timeout: ${label}`);
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

try {
  if (!(await setSymbol(TV_SYM))) {
    console.log(JSON.stringify({ coin: COIN, error: 'symbol did not load' }));
    process.exitCode = 1;
  } else if (!(await setResolution('5'))) {
    console.log(JSON.stringify({ coin: COIN, error: 'resolution did not load' }));
    process.exitCode = 1;
  } else {
    const hist = await loadHistory();
    const edges = await evaluate(EDGES);
    const out = { coin: COIN, tv_symbol: TV_SYM, history: hist, ...edges };
    if (hist.state !== 'floor' || !edges || edges.error || edges.pro_symbol !== TV_SYM) {
      out.failed = true;
      process.exitCode = 1;
    } else {
      out.firstISO = new Date(edges.first_bar_ts * 1000).toISOString();
      out.lastISO = new Date(edges.last_bar_ts * 1000).toISOString();
    }
    console.log(JSON.stringify(out));
  }
} finally {
  await disconnect();
}
