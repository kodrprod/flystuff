/**
 * Does the metric switch survive contact with the real corpus?
 *
 * The 165 reels on disk came from the paid scraper, so they carry plays *and*
 * likes/comments. That makes them the one dataset where engagement-based
 * ranking can be checked against the play-based ranking it replaces, instead of
 * being taken on faith.
 *
 *   node check-metric.mjs
 */
import { readCorpus } from './server/lib.mjs';
import { CONFIG, METRICS, computeBaseline, detectOutlier, effectiveGate } from './js/scoring.js';

const corpus = readCorpus();
const posts = corpus.posts;
console.log(`corpus: ${posts.length} reels, ${Object.keys(corpus.creators).length} accounts\n`);

/** Rebuilds history with both metrics available on every history row. */
function historyWith(posts) {
  const by = {};
  for (const p of posts) {
    (by[p.creatorId] ||= []).push({
      id: p.id, mediaType: p.mediaType, views: p.views,
      likes: p.likes, comments: p.comments,
      engagement: (p.likes || 0) + (p.comments || 0),
      ageDays: p.ageDays, flags: p.flags || [],
    });
  }
  return by;
}

const history = historyWith(posts);

function run(metric, label) {
  const rows = posts.map((p) => {
    const creator = { id: p.creatorId, history: history[p.creatorId] || [] };
    const baseline = computeBaseline(creator, p.mediaType, p.id, metric);
    return { p, baseline, outlier: detectOutlier(p, baseline, metric) };
  });

  const withBaseline = rows.filter((r) => r.baseline.valid);
  const valid = rows.filter((r) => r.outlier.valid);
  const accounts = new Set(withBaseline.map((r) => r.p.creatorId));

  const gate = effectiveGate(rows.map((r) => r.outlier));
  const past = valid.filter((r) => r.outlier.conservative >= gate.threshold);

  console.log(`── ${label} ${'─'.repeat(46 - label.length)}`);
  console.log(`  accounts with a usable baseline : ${accounts.size} / ${Object.keys(history).length}`);
  console.log(`  reels with a scoreable multiplier: ${valid.length}`);
  console.log(`  shortlist cut (${gate.mode})       : ${gate.threshold.toFixed(2)}×  → ${past.length} reels`);

  const fixed8 = valid.filter((r) => r.outlier.conservative >= 8).length;
  console.log(`  would clear a fixed 8× gate      : ${fixed8}`);

  const top = valid.sort((a, b) => b.outlier.conservative - a.outlier.conservative).slice(0, 8);
  console.log('  top 8:');
  for (const r of top) {
    console.log(
      `    ${r.outlier.conservative.toFixed(1).padStart(6)}×  @${r.p.creatorId.padEnd(24)} ` +
      `${String(metric.get(r.p)).padStart(7)} ${metric.short}  ${r.p.ageDays}d`,
    );
  }
  console.log();
  return { valid, top };
}

CONFIG.gateMode = 'topN';
CONFIG.topN = 30;

const v = run(METRICS.views, 'PLAYS (what the paid scraper gave us)');
const e = run(METRICS.engagement, 'ENGAGEMENT (what the free sources give us)');

/* Do the two metrics agree on which reels are interesting? If they rank the
 * same posts highly, the switch costs nothing. If they disagree wildly, the
 * whole approach needs rethinking rather than shipping. */
const vTop = new Set(v.top.map((r) => r.p.id));
const eTop = new Set(e.top.map((r) => r.p.id));
const overlap = [...vTop].filter((id) => eTop.has(id)).length;
console.log(`── agreement ────────────────────────────────────`);
console.log(`  top-8 overlap between plays and engagement: ${overlap}/8`);

const paired = posts
  .filter((p) => p.views > 0 && (p.likes || 0) + (p.comments || 0) > 0)
  .map((p) => ((p.likes || 0) + (p.comments || 0)) / p.views);
if (paired.length) {
  const s = [...paired].sort((a, b) => a - b);
  console.log(`  engagement rate: median ${(s[s.length >> 1] * 100).toFixed(2)}% of plays (n=${paired.length})`);
}
