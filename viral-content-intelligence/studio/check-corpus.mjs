/** What is actually on disk. Run: node check-corpus.mjs */
import { readFileSync, existsSync } from 'node:fs';
const f = 'data/corpus.json';
if (!existsSync(f)) { console.log('\n  No data/corpus.json — nothing was ever saved.\n'); process.exit(0); }
const c = JSON.parse(readFileSync(f, 'utf8'));
const analysed = c.posts.filter((p) => p.attributes).length;
console.log(`\n  ${c.posts.length} reels · ${Object.keys(c.creators).length} creators · ${analysed} analysed\n`);
console.log('  source lists by client id:');
for (const [id, handles] of Object.entries(c.sources)) console.log(`    ${id.padEnd(24)} ${handles.length} accounts`);
if (!Object.keys(c.sources).length) console.log('    (none — reels are stored but not linked to a client)');
console.log('\n  recent runs:');
for (const r of c.runs.slice(0, 5)) console.log(`    ${r.at}  ${r.type}  ${JSON.stringify({ ...r, at: undefined, type: undefined })}`);
console.log('');
