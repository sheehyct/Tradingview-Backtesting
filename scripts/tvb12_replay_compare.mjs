// TVB-12 replay-vs-original comparison (docs/experiments/tvb12_replay_plan.md).
// For every accepted replay record with an original counterpart (same cell id in
// the TVB-11 a1/a2/b JSONLs), compares the CLOSED trade lists on the overlap
// window and emits a per-cell verdict:
//   CLEAN   -- every overlap trade matches (entry/exit time + direction, prices
//              within tick tolerance)
//   DRIFT   -- differences exist but are confined to the window boundary /
//              path-dependent state (quantified: matched fraction, net delta)
//   SUSPECT -- wholesale mismatch (the F1 contamination signature)
// R4 cells (new evidence) are listed separately with no reproduction target.
//
// Overlap start: max(original loaded_first_ms, replay loaded_first_ms) when the
// original has window evidence (echo-path records); engine-path originals have
// none (the audit's F1 gap), so the replay window start is used and the record
// is flagged original_window_unknown.
//
// Usage: node scripts/tvb12_replay_compare.mjs <replay.jsonl> [out.json]
import fs from 'node:fs';

const ORIGINALS = [
  'docs/experiments/tvb11_champion_a1.jsonl',
  'docs/experiments/tvb11_champion_a2.jsonl',
  'docs/experiments/tvb11_champion_b.jsonl',
];

function loadJsonl(path) {
  if (!fs.existsSync(path)) return [];
  return fs.readFileSync(path, 'utf8').split('\n').filter(l => l.trim()).map(l => JSON.parse(l));
}

const originals = new Map();
for (const f of ORIGINALS)
  for (const r of loadJsonl(f))
    if (r.accepted && !r.variant) originals.set(r.id, { ...r, src: f });

const replayFile = process.argv[2];
if (!replayFile) { console.error('usage: node scripts/tvb12_replay_compare.mjs <replay.jsonl> [out.json]'); process.exit(1); }
const replays = loadJsonl(replayFile).filter(r => r.accepted);

function closed(list) { return (list || []).filter(t => !t.open && t.et != null && t.xt != null); }

function compareCell(rep, orig) {
  const repWin = rep.metrics_table ? Number(rep.metrics_table.loaded_first_ms) : null;
  const origWin = orig.metrics_table ? Number(orig.metrics_table.loaded_first_ms) : null;
  const overlapStart = Math.max(repWin ?? 0, origWin ?? 0);
  const rTrades = closed(rep.report && rep.report.list).filter(t => t.et >= overlapStart);
  const oTrades = closed(orig.report && orig.report.list).filter(t => t.et >= overlapStart);
  // Match by entry time + direction; prices within 1e-6 relative.
  const oByKey = new Map();
  for (const t of oTrades) oByKey.set(`${t.et}|${t.dir}`, t);
  let matched = 0, priceMismatch = 0;
  for (const t of rTrades) {
    const o = oByKey.get(`${t.et}|${t.dir}`);
    if (!o) continue;
    const pxOk = Math.abs(t.ep - o.ep) <= Math.abs(o.ep) * 1e-6 && Math.abs(t.xp - o.xp) <= Math.abs(o.xp) * 1e-6 && t.xt === o.xt;
    if (pxOk) matched += 1; else priceMismatch += 1;
  }
  const union = Math.max(rTrades.length, oTrades.length);
  const frac = union === 0 ? 1 : matched / union;
  const verdict = frac === 1 ? 'CLEAN' : frac >= 0.8 ? 'DRIFT' : 'SUSPECT';
  return {
    id: rep.id, tag: rep.tag || null, src: orig.src.split('/').pop(),
    original_window_unknown: origWin === null,
    overlap_start_ms: overlapStart,
    replay: { net: rep.report?.net, trades: rep.report?.trades, overlap_trades: rTrades.length },
    original: { net: orig.report?.net, trades: orig.report?.trades, overlap_trades: oTrades.length },
    matched, price_or_exit_mismatch: priceMismatch,
    matched_fraction: Number(frac.toFixed(4)),
    net_delta_pp: rep.report && orig.report ? Number(((rep.report.net - orig.report.net) * 100).toFixed(3)) : null,
    verdict,
  };
}

const compared = [], newEvidence = [];
for (const rep of replays) {
  const orig = originals.get(rep.id);
  if (orig) compared.push(compareCell(rep, orig));
  else newEvidence.push({ id: rep.id, tag: rep.tag || null, net: rep.report?.net, trades: rep.report?.trades,
    window_first_ms: rep.metrics_table ? Number(rep.metrics_table.loaded_first_ms) : null });
}

const counts = {};
for (const c of compared) counts[c.verdict] = (counts[c.verdict] || 0) + 1;
const out = { replay_file: replayFile, compared_cells: compared.length, verdict_counts: counts, compared, new_evidence: newEvidence };
const outFile = process.argv[3];
if (outFile) fs.writeFileSync(outFile, JSON.stringify(out, null, 1));
console.log(JSON.stringify({ compared_cells: compared.length, verdict_counts: counts, new_evidence_cells: newEvidence.length }, null, 1));
for (const c of compared.filter(x => x.verdict !== 'CLEAN')) console.log(`${c.verdict} ${c.id} matched=${c.matched_fraction} netDelta=${c.net_delta_pp}pp`);
