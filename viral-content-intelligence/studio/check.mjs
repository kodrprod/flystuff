import { CLIENTS, CREATORS, POSTS } from './js/data.js';
import { scoreAll, CONFIG } from './js/scoring.js';

const SHORT_MIN = 6;
let fail = 0;
const assert = (c, m) => { if (!c) { console.log('  FAIL: ' + m); fail++; } };

for (const c of CLIENTS) {
  const r = scoreAll(POSTS, CREATORS, c);
  const scored = r.filter(x => x.stage === 'scored');
  console.log(`\n=== ${c.name} (${c.cuisine}) ===`);
  console.log(`scored ${scored.length} / ${POSTS.length}`);
  scored.slice(0, 6).forEach((x, i) =>
    console.log(
      `  ${i + 1}. ${x.opportunity.toFixed(1)}  ${x.post.id.padEnd(4)} ` +
      `V${x.V.toFixed(2)} R${x.R.score.toFixed(2)} F${x.F.score.toFixed(2)} T${x.T.score.toFixed(2)}  ` +
      `${x.post.caption.slice(0, 44)}`));
  const drops = r.filter(x => x.stage !== 'scored');
  const byStage = {};
  drops.forEach(d => (byStage[d.stage] = (byStage[d.stage] || 0) + 1));
  console.log('  drops:', JSON.stringify(byStage));
  assert(scored.length >= SHORT_MIN, `${c.name}: only ${scored.length} scored`);
}


// Structural assertions
const bos = scoreAll(POSTS, CREATORS, CLIENTS[0]);
const sen = scoreAll(POSTS, CREATORS, CLIENTS[1]);
const top = a => a.filter(x => x.stage === 'scored').slice(0, 6).map(x => x.post.id);
console.log('\nbosporus top6:', top(bos).join(','));
console.log('sen      top6:', top(sen).join(','));
assert(top(bos).join(',') !== top(sen).join(','), 'client switch does not change the shortlist');

const find = (a, id) => a.find(x => x.post.id === id);
assert(find(bos, 'p20').stage === 'rejected', 'p20 (12d old) should hit the maturity gate');
assert(find(bos, 'p21').stage === 'rejected', 'p21 (104d old) should be out of window');
assert(find(bos, 'p19').stage === 'below_gate', 'p19 should fall below the extraction gate');
assert(find(bos, 'p10').stage === 'filtered', 'p10 (drone/outdoor/€200) should be hard-filtered for bosporus');
assert(find(bos, 'p14').stage === 'filtered', 'p14 (6d trend half-life) should be filtered');
assert(find(bos, 'p9').stage === 'scored' && find(bos, 'p9').R.score < 0.4,
  'p9 (named person) should score but be crushed on replicability');
assert(find(sen, 'p15').stage === 'scored', 'p15 (€45) should pass sen budget ceiling');
assert(find(bos, 'p15').stage === 'filtered', 'p15 (€45) should exceed bosporus ceiling');

// weights must sum to 1
const ws = Object.values(CONFIG.weights).reduce((a, b) => a + b, 0);
assert(Math.abs(ws - 1) < 1e-9, `weights sum to ${ws}, not 1`);

console.log(fail ? `\n${fail} FAILURE(S)` : '\nAll assertions passed.');
process.exit(fail ? 1 : 0);
