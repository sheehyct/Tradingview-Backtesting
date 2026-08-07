// TVB-19 deep-window TV-bar harvest -- full loaded-series dumps per symbol/interval.
// The TVB-6 path scripted end-to-end: for each roster symbol and interval, set the
// chart (active chart on the TVB18-parity SCRATCH layout -- never a live layout),
// loop requestMoreData to the data floor (tv_probe.mjs history mechanism), then dump
// the entire main series with tick metadata (tv_bars.mjs mechanism).
// Provenance: TV bars vs HL archive bars differ at the cents/wick level (TVB-6:
// 97-99% float-exact); every dump records pro_symbol + minmov/pricescale.
// The dumped series ends on TV's ACTIVE bar: the last row may still be forming.
// Consumers must drop or close-gate the final row (declared in tv_deep/README.md).
// A run FAILS (exit 1) unless every requested dataset lands with a clean floor;
// the summary merges by (coin, interval) so partial re-harvests never erase rows.
// Usage: node scripts/tvb19_harvest.mjs [outDir]  (default analysis/reference/tv_deep)
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { evaluate, disconnect } from 'file:///C:/Strat_Trading_Bot/tradingview-mcp-jackson/src/connection.js';

// Explicit roster -> TV mapping. The TV coin string can differ from the HL coin:
// xyz:SKHX trades on TV as HIP3XYZ:SKHYNIXUSDC.P (TV search does not index
// HIP3XYZ at all -- direct chart load only). Never derive the TV symbol from the
// roster name alone. TVB19_COINS=<tv_coin,...> still selects a subset for reruns.
const SYMBOL_MAP = [
  { roster: 'xyz:MRVL', coin: 'MRVL' },
  { roster: 'xyz:GOOGL', coin: 'GOOGL' },
  { roster: 'xyz:AMZN', coin: 'AMZN' },
  { roster: 'xyz:MSFT', coin: 'MSFT' },
  { roster: 'xyz:GOLD', coin: 'GOLD' },
  { roster: 'xyz:AAPL', coin: 'AAPL' },
  { roster: 'xyz:SKHX', coin: 'SKHYNIX' },
  { roster: 'xyz:SKHY', coin: 'SKHY' },
  { roster: 'xyz:NBIS', coin: 'NBIS' },
  { roster: 'xyz:TSLA', coin: 'TSLA' },
  { roster: 'xyz:DRAM', coin: 'DRAM' },
];
const ONLY = process.env.TVB19_COINS ? new Set(process.env.TVB19_COINS.split(',')) : null;
const TARGETS = ONLY ? SYMBOL_MAP.filter((s) => ONLY.has(s.coin)) : SYMBOL_MAP;
const INTERVALS = ['15', '60', '5'];
const OUT_DIR = process.argv[2] || 'analysis/reference/tv_deep';
const CHART = 'window.TradingViewApi._activeChartWidgetWV.value()';
const MS = `${CHART}._chartWidget.model().model().mainSeries()`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (o) => console.log(JSON.stringify({ t: new Date().toISOString(), ...o }));

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

// Floor detection needs REPEATED agreement: one unchanged 700ms sample can be a
// slow response, not the floor. Require STABLE_ROUNDS consecutive unchanged sizes
// and report a terminal state the caller must act on: 'floor' | 'err' | 'capped'.
const STABLE_ROUNDS = 3;

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

const DUMP = `(function(){
  try {
    var ms = ${MS};
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
      exchange: si ? si.exchange : null,
      minmov: si ? si.minmov : null,
      pricescale: si ? si.pricescale : null,
      mintick: si && si.minmov && si.pricescale ? si.minmov / si.pricescale : null,
      interval: ms.interval ? ms.interval() : null,
      count: rows.length,
      bars: rows
    };
  } catch(e){ return { error: e.message }; }
})()`;

try {
  mkdirSync(OUT_DIR, { recursive: true });
  const summary = [];
  let failures = 0;
  for (const { roster, coin } of TARGETS) {
    const tvSym = `HIP3XYZ:${coin}USDC.P`;
    if (!(await setSymbol(tvSym))) {
      log({ ev: 'skip_symbol', roster, coin, tvSym });
      for (const iv of INTERVALS) summary.push({ roster, coin, iv, error: 'symbol did not load' });
      failures += INTERVALS.length;
      continue;
    }
    for (const iv of INTERVALS) {
      if (!(await setResolution(iv))) {
        log({ ev: 'skip_interval', roster, coin, iv });
        summary.push({ roster, coin, iv, error: 'resolution did not load' });
        failures += 1;
        continue;
      }
      const hist = await loadHistory();
      if (hist.state !== 'floor') {
        log({ ev: 'history_incomplete', roster, coin, iv, ...hist });
        summary.push({ roster, coin, iv, error: `history ${hist.state}`, history: hist });
        failures += 1;
        continue;
      }
      const dump = await evaluate(DUMP);
      if (!dump || dump.error || !dump.bars || !dump.bars.length) {
        log({ ev: 'dump_failed', roster, coin, iv, error: dump && dump.error });
        summary.push({ roster, coin, iv, error: (dump && dump.error) || 'empty dump' });
        failures += 1;
        continue;
      }
      if (dump.pro_symbol !== tvSym || dump.interval !== iv) {
        log({ ev: 'identity_mismatch', roster, coin, iv, got: dump.pro_symbol, got_iv: dump.interval });
        summary.push({ roster, coin, iv, error: 'identity mismatch, dump discarded' });
        failures += 1;
        continue;
      }
      dump.roster_symbol = roster;
      dump.harvested_utc = new Date().toISOString();
      dump.last_bar_may_be_forming = true;
      dump.history_termination = hist;
      dump.provenance = 'TVB-19 deep harvest; TV loaded series to data floor; '
        + 'TV-vs-HL wick-level variance per TVB-6 (97-99% float-exact)';
      dump.firstISO = new Date(dump.bars[0][0] * 1000).toISOString();
      dump.lastISO = new Date(dump.bars[dump.bars.length - 1][0] * 1000).toISOString();
      const out = `${OUT_DIR}/tvb19_tv_xyz_${coin}_${iv}m.json`;
      writeFileSync(out, JSON.stringify(dump));
      log({ ev: 'dumped', roster, coin, iv, count: dump.count, rounds: hist.rounds,
            first: dump.firstISO, last: dump.lastISO, out });
      summary.push({ roster, coin, iv, count: dump.count, first: dump.firstISO,
                     last: dump.lastISO, history: hist });
    }
  }
  // Merge by (coin, iv) into any existing summary so a partial rerun updates its
  // own rows without erasing the rest of the inventory.
  const sumPath = `${OUT_DIR}/tvb19_harvest_summary.json`;
  let merged = summary;
  if (existsSync(sumPath)) {
    const prior = JSON.parse(readFileSync(sumPath, 'utf8')).datasets || [];
    const key = (r) => `${r.coin}|${r.iv || ''}`;
    const fresh = new Map(summary.map((r) => [key(r), r]));
    merged = prior.map((r) => fresh.get(key(r)) || r);
    for (const r of summary) if (!prior.some((p) => key(p) === key(r))) merged.push(r);
  }
  writeFileSync(sumPath, JSON.stringify(
    { generated_utc: new Date().toISOString(), complete: failures === 0, datasets: merged },
    null, 1));
  log({ ev: 'done', datasets: summary.length, failures });
  if (failures > 0) process.exitCode = 1;
} finally {
  await disconnect();
}
