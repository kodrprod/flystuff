/**
 * API + static server.
 *
 * Long jobs (scrape, analyse) run in the background and report through
 * /api/job/:id, so the browser never sits on a 4-minute request.
 */
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { randomUUID } from 'node:crypto';

import { ROOT, loadEnv, keyStatus, keyIssues, assertKey, readCorpus, writeCorpus, backupCorpus, logRun, sleep } from './lib.mjs';
import { importDataset, buildHistory, EXCLUSION_LABELS } from './ingest.mjs';
import { resolveSelf, graphStatus, fetchMany, normalizeGraphMedia } from './sources/graph.mjs';
import { fetchVideo, ytdlpAvailable } from './sources/video.mjs';
import {
  findRestaurant, findSimilarAccounts, findRestaurantGemini, findSimilarAccountsGemini,
  reason, extractWithGemini,
} from './ai.mjs';
import { estimate, RATES } from './costs.mjs';
import {
  computeBaseline, detectOutlier, effectiveGate, resolveMetric, isExcluded, CONFIG,
} from '../js/scoring.js';

const env = loadEnv();
const jobs = new Map();

/* ------------------------------------------------------------------ *
 * Jobs
 * ------------------------------------------------------------------ */

function startJob(label, fn) {
  const id = randomUUID().slice(0, 8);
  const job = { id, label, status: 'running', log: [], result: null, error: null, startedAt: Date.now() };
  jobs.set(id, job);
  const say = (msg) => {
    job.log.push({ t: Date.now() - job.startedAt, msg });
    if (job.log.length > 400) job.log.splice(0, 200);
  };
  Promise.resolve(fn(say))
    .then((r) => { job.result = r; job.status = 'done'; say('Done.'); })
    .catch((e) => { job.error = e.message; job.status = 'error'; say(`Failed: ${e.message}`); });
  // Keep finished jobs around briefly so the UI can read the final state.
  setTimeout(() => jobs.delete(id), 20 * 60 * 1000).unref?.();
  return id;
}

/* ------------------------------------------------------------------ *
 * Corpus helpers
 * ------------------------------------------------------------------ */

/**
 * Attach baselines + outlier multipliers using the same engine the UI uses.
 *
 * The metric is resolved from the corpus rather than assumed, because a corpus
 * can hold both scraped reels (which have play counts) and Graph API reels
 * (which never will). Scoring those against each other on different metrics
 * would be silent corruption.
 */
function withOutliers(posts) {
  const metric = resolveMetric(posts);
  const history = buildHistory(posts);
  return posts.map((p) => {
    const creator = { id: p.creatorId, history: history[p.creatorId] || [] };
    if (isExcluded(p).length) return { ...p, outlier: { valid: false }, outlierMultiplier: 0 };
    const baseline = computeBaseline(creator, p.mediaType, p.id, metric);
    const outlier = detectOutlier(p, baseline, metric);
    return {
      ...p,
      metric: metric.key,
      baselineValue: baseline.medianValue,
      baselineViews: baseline.medianValue,
      baselineN: baseline.nPosts,
      outlier,
      outlierMetric: metric.short,
      outlierMultiplier: outlier.valid ? outlier.conservative : 0,
    };
  });
}

/**
 * The shortlist, using the same corpus-relative gate the UI shows.
 *
 * Shared by /api/analyze and /api/shortlist so the count quoted in the cost
 * estimate is the count that actually gets analysed — a preview that disagrees
 * with the run is how the last cost surprise happened.
 */
function shortlist(posts, { gate, topN, limit } = {}) {
  const prev = { mode: CONFIG.gateMode, n: CONFIG.topN, mult: CONFIG.gateMultiplier };
  if (gate > 0) { CONFIG.gateMode = 'multiplier'; CONFIG.gateMultiplier = gate; }
  else if (topN > 0) { CONFIG.gateMode = 'topN'; CONFIG.topN = topN; }

  const g = effectiveGate(posts.map((p) => p.outlier || { valid: false }));
  const picked = posts
    .filter((p) => p.outlier?.valid && p.outlier.conservative >= g.threshold)
    .sort((a, b) => b.outlierMultiplier - a.outlierMultiplier)
    .slice(0, limit || CONFIG.topN);

  Object.assign(CONFIG, { gateMode: prev.mode, topN: prev.n, gateMultiplier: prev.mult });
  return { picked, gate: g };
}

/**
 * Which model does the web search. Gemini unless Claude is explicitly asked for
 * and actually configured, so a missing Anthropic key degrades the search
 * rather than blocking discovery entirely.
 */
function pickSearcher(requested) {
  const want = (requested || env.reasoner || 'gemini').toLowerCase();
  if (want === 'claude' && env.anthropic) return 'claude';
  if (env.gemini) return 'gemini';
  if (env.anthropic) return 'claude';
  throw new Error('No search model configured — set GEMINI_API_KEY in .env');
}

function clientPosts(corpus, clientId) {
  // A client with no source list gets nothing, not everything. Returning the
  // whole corpus would silently score one client's reels against another's
  // brief and look like real results.
  const handles = new Set(corpus.sources[clientId] || []);
  if (!handles.size) return [];
  return withOutliers(corpus.posts.filter((p) => handles.has(p.creatorId)));
}

/* ------------------------------------------------------------------ *
 * Routes
 * ------------------------------------------------------------------ */

const routes = {
  'GET /api/status': async () => {
    const c = readCorpus();
    const [graph, ytdlp] = await Promise.all([graphStatus(env.graph), ytdlpAvailable()]);
    const posts = withOutliers(c.posts);
    return {
      keys: keyStatus(env),
      keyIssues: keyIssues(env),
      models: { anthropic: env.anthropicModel, gemini: env.geminiModel, reasoner: env.reasoner },
      geminiFreeTier: env.geminiFreeTier,
      sourcesAvailable: { graph: graph.ok, ytdlp: !!ytdlp },
      graph,
      corpus: {
        creators: Object.keys(c.creators).length,
        posts: c.posts.length,
        analysed: c.posts.filter((p) => p.attributes).length,
        metric: resolveMetric(c.posts).key,
        withBaseline: posts.filter((p) => p.outlier?.valid).length,
        sources: Object.fromEntries(Object.entries(c.sources).map(([k, v]) => [k, v.length])),
      },
      runs: c.runs.slice(0, 8),
      rates: RATES,
    };
  },

  'POST /api/estimate': async ({ action, params }) =>
    estimate(action, { reasoner: env.reasoner, geminiFreeTier: env.geminiFreeTier, ...(params || {}) }),

  /** Which reels the next Analyse run would actually touch, and what it'd cost. */
  'POST /api/shortlist': async ({ clientId, gate, topN }) => {
    const c = readCorpus();
    const posts = clientPosts(c, clientId);
    const { picked, gate: g } = shortlist(posts, { gate, topN });
    const unanalysed = picked.filter((p) => !p.attributes);
    const avgSeconds = Math.round(
      picked.reduce((a, p) => a + (p.durationS || 30), 0) / Math.max(1, picked.length),
    );
    return {
      gate: g,
      metric: resolveMetric(c.posts).key,
      total: picked.length,
      unanalysed: unanalysed.length,
      cached: picked.length - unanalysed.length,
      posts: picked.map((p) => ({
        id: p.id, creatorId: p.creatorId, caption: p.caption,
        multiplier: p.outlierMultiplier, analysed: !!p.attributes,
        likes: p.likes, comments: p.comments, views: p.views, ageDays: p.ageDays, url: p.url,
      })),
      // Only unanalysed reels cost anything — the rest are already paid for.
      estimate: estimate('analyze', {
        videos: unanalysed.length, avgSeconds,
        reasoner: env.reasoner, geminiFreeTier: env.geminiFreeTier,
      }),
    };
  },

  'GET /api/corpus': async (_body, url) => {
    const clientId = url.searchParams.get('clientId') || '';
    const c = readCorpus();
    // Escape hatch for the UI when reels exist but belong to no known client.
    if (clientId === '__all__') return { posts: [], creators: [], allCreators: Object.keys(c.creators) };
    const posts = clientPosts(c, clientId);
    const history = buildHistory(posts);
    const creators = Object.values(c.creators)
      .filter((cr) => history[cr.id])
      .map((cr) => ({ ...cr, history: history[cr.id] }));
    return { posts, creators, sources: c.sources[clientId] || [] };
  },

  'POST /api/discover/restaurant': async ({ query, reasoner }) => {
    if (!query?.trim()) throw new Error('query required');
    const who = pickSearcher(reasoner);
    // Web search puts this around a minute; too long to hold a request open.
    const jobId = startJob('Finding the restaurant', async (say) => {
      say(`Searching with ${who} for "${query.trim()}"…`);
      const out = who === 'claude'
        ? await findRestaurant(env, query.trim())
        : await findRestaurantGemini(env, query.trim());
      say(`${out.candidates?.length || 0} candidates.`);
      return out;
    });
    return { jobId };
  },

  'POST /api/discover/similar': async ({ restaurant, count, reasoner }) => {
    const who = pickSearcher(reasoner);
    const jobId = startJob('Finding similar accounts', async (say) => {
      say(`Searching with ${who} for accounts like ${restaurant.name}…`);
      const out = who === 'claude'
        ? await findSimilarAccounts(env, restaurant, count || 45)
        : await findSimilarAccountsGemini(env, restaurant, count || 45);
      say(`Found ${out.accounts.length} candidate accounts.`);
      say('Only public Business/Creator accounts can be read — private ones will fail at fetch.');
      return out;
    });
    return { jobId };
  },

  /* ---------------- free ingestion via the Instagram Graph API ------------- */

  'POST /api/graph/accounts': async () => {
    assertKey(env, 'graph', 'IG_GRAPH_TOKEN');
    return { accounts: await resolveSelf(env.graph) };
  },

  /**
   * The free replacement for /api/scrape.
   *
   * Costs nothing, so depth is set high by default: the corpus that produced
   * only two candidates did so because four accounts had enough reels for a
   * baseline, not because the scoring was wrong.
   */
  'POST /api/graph/fetch': async ({ clientId, handles, limitPerAccount, igUserId }) => {
    assertKey(env, 'graph', 'IG_GRAPH_TOKEN');
    if (!handles?.length) throw new Error('handles required');

    const jobId = startJob(`Reading ${handles.length} accounts (free)`, async (say) => {
      const self = igUserId || env.igUserId || (await resolveSelf(env.graph))[0].igUserId;
      const limit = limitPerAccount || 50;
      say(`Instagram Graph API · ${handles.length} accounts × up to ${limit} reels · $0.00`);

      const { accounts, failures } = await fetchMany(env.graph, self, handles, {
        limitPerAccount: limit,
        onProgress: (p) =>
          say(p.error ? `  ✗ @${p.handle}: ${p.error}` : `  [${p.i}/${p.n}] @${p.handle} — ${p.got} media`),
      });

      const now = Date.now();
      const fresh = [];
      for (const acc of accounts) {
        for (const m of acc.media) fresh.push(normalizeGraphMedia(m, acc.handle, now));
      }

      const reels = fresh.filter((p) => !p.flags.includes('not_a_reel'));
      say(`${fresh.length} media · ${reels.length} reels (feed posts and stories flagged, not deleted).`);
      if (failures.length) say(`${failures.length} accounts unreadable — most often private or personal.`);

      const corpus = readCorpus();
      // Never lose analysis already paid for.
      const existing = new Map(corpus.posts.map((p) => [p.id, p]));
      for (const p of fresh) {
        const prev = existing.get(p.id);
        existing.set(p.id, prev?.attributes ? { ...p, ...pickAnalysis(prev) } : p);
      }
      corpus.posts = [...existing.values()];
      for (const acc of accounts) {
        corpus.creators[acc.handle] ||= {
          id: acc.handle, handle: acc.handle, name: acc.handle, niche: '',
          addedAt: new Date().toISOString(),
        };
        corpus.creators[acc.handle].followers = acc.profile?.followers ?? null;
      }
      if (clientId) {
        const owners = accounts.map((a) => a.handle);
        corpus.sources[clientId] = [...new Set([...(corpus.sources[clientId] || []), ...owners])];
      }
      logRun(corpus, 'graph', {
        accounts: handles.length, ok: accounts.length, failed: failures.length,
        media: fresh.length, costUsd: 0,
      });
      writeCorpus(corpus);

      const scored = clientId ? clientPosts(corpus, clientId) : withOutliers(corpus.posts);
      const usable = scored.filter((p) => p.outlier?.valid);
      const { picked, gate } = shortlist(scored, { topN: CONFIG.topN });
      say(`${corpus.posts.length} reels held · ${usable.length} scoreable · shortlist cut ${gate.threshold.toFixed(1)}× → ${picked.length} to analyse.`);

      return {
        accounts: accounts.length, failures, media: fresh.length,
        usable: usable.length, shortlisted: picked.length, costUsd: 0,
      };
    });
    return { jobId };
  },

  /**
   * Import a JSON export you already have on disk.
   *
   * Replaces the Apify integration. Nothing in this server calls a paid actor
   * any more, but reels already bought stay readable — discarding them to make
   * a point about cost would be its own kind of waste.
   */
  'POST /api/import': async ({ clientId, path: filePath, json }) => {
    const jobId = startJob('Importing dataset', async (say) => {
      let data = json;
      if (!data) {
        if (!filePath) throw new Error('Give a file path or inline JSON.');
        const abs = filePath.startsWith('/') ? filePath : join(ROOT, filePath);
        say(`Reading ${abs}…`);
        data = JSON.parse(await readFile(abs, 'utf8'));
      }

      const { posts: fresh, creators, flagCounts, read } = importDataset(data);
      say(`Read ${read} records → ${fresh.length} reels.`);
      Object.entries(flagCounts).forEach(([r, n]) => say(`Flagged ${n}: ${EXCLUSION_LABELS[r] || r}`));
      say('Everything is stored — use Filters to decide what counts.');

      const corpus = readCorpus();
      const existing = new Map(corpus.posts.map((p) => [p.id, p]));
      for (const p of fresh) {
        const prev = existing.get(p.id);
        existing.set(p.id, prev?.attributes ? { ...p, ...pickAnalysis(prev) } : p);
      }
      corpus.posts = [...existing.values()];
      Object.assign(corpus.creators, creators);
      if (clientId) {
        const owners = [...new Set(fresh.map((p) => p.creatorId))];
        corpus.sources[clientId] = [...new Set([...(corpus.sources[clientId] || []), ...owners])];
      }
      logRun(corpus, 'import', { read, kept: fresh.length, flagged: flagCounts, costUsd: 0 });
      writeCorpus(corpus);

      const scored = withOutliers(corpus.posts);
      const usable = scored.filter((p) => p.outlier?.valid);
      const { picked, gate } = shortlist(scored, { topN: CONFIG.topN });
      say(`${corpus.posts.length} reels held · ${usable.length} scoreable · cut ${gate.threshold.toFixed(1)}x -> ${picked.length}.`);
      return { read, kept: fresh.length, usable: usable.length, shortlisted: picked.length, costUsd: 0 };
    });
    return { jobId };
  },

  'POST /api/analyze': async ({ clientId, client, limit, gate, topN, force, reasoner }) => {
    if (!env.gemini) throw new Error('GEMINI_API_KEY missing — it is the only required key.');
    if (!client) throw new Error('client profile required');
    const who = (reasoner || env.reasoner) === 'claude' && env.anthropic ? 'claude' : 'gemini';

    const jobId = startJob('Analysing shortlist', async (say) => {
      const corpus = readCorpus();
      const scored = clientPosts(corpus, clientId);
      const { picked: targets, gate: g } = shortlist(scored, { gate, topN, limit });

      if (!targets.length) {
        say('Nothing to analyse yet — add source accounts and fetch reels first.');
        return { analysed: 0 };
      }

      const todo = force ? targets : targets.filter((t) => !t.attributes || !t.adaptations?.[client.id]);
      const est = estimate('analyze', {
        videos: todo.length,
        avgSeconds: Math.round(todo.reduce((a, p) => a + (p.durationS || 30), 0) / Math.max(1, todo.length)),
        reasoner: who, geminiFreeTier: env.geminiFreeTier,
      });
      say(`${targets.length} shortlisted at ≥${g.threshold.toFixed(1)}× · ${todo.length} need work.`);
      say(`Estimated cost: $${est.totalUsd.toFixed(4)} — ${est.items.map((i) => `${i.platform} $${i.usd.toFixed(4)}`).join(', ')}`);
      say('Video download: yt-dlp / Instagram CDN · $0.00');

      const byId = new Map(corpus.posts.map((p) => [p.id, p]));
      let ok = 0, skipped = 0, failed = 0, ytdlpUsed = 0;

      for (const [i, t] of targets.entries()) {
        const stored = byId.get(t.id);
        const tag = `[${i + 1}/${targets.length}] @${t.creatorId}`;

        // Resume, don't repeat. Extraction is per-video; the adaptation is
        // per-video-per-client, so each is skipped independently unless forced.
        const haveVideo = !!stored.attributes;
        const haveReasoning = !!stored.adaptations?.[client.id];
        if (haveVideo && haveReasoning && !force) {
          skipped++;
          if (skipped <= 3) say(`${tag} — already done, skipping`);
          continue;
        }

        try {
          if (!haveVideo || force) {
            // Politeness gap only when the previous post actually needed the
            // throttled path; a fresh Graph media_url costs Instagram nothing.
            if (ytdlpUsed > 0) await sleep(20000);
            say(`${tag} — fetching video…`);
            const video = await fetchVideo(stored, { cookiesFile: env.cookiesFile });
            if (video.via === 'yt-dlp') ytdlpUsed++;
            // yt-dlp brings back metrics the Graph API does not; keep them.
            if (video.meta?.likes != null && stored.likes == null) stored.likes = video.meta.likes;

            say(`${tag} — Gemini watching (${video.via})…`);
            Object.assign(stored, await extractWithGemini(env, stored, video));
            writeCorpus(corpus); // bank the video pass before spending again
          } else {
            say(`${tag} — extraction cached`);
          }

          say(`${tag} — ${who} adapting…`);
          const r = await reason(
            env,
            { ...stored, outlierMultiplier: t.outlierMultiplier, outlierMetric: t.outlierMetric },
            client,
            who,
          );
          stored.mechanism = r.mechanism;
          stored.essentialElements = r.essentialElements;
          stored.incidentalElements = r.incidentalElements;
          stored.adaptations = { ...(stored.adaptations || {}), [client.id]: r.adaptation };
          ok++;
          writeCorpus(corpus); // checkpoint after every video
        } catch (e) {
          failed++;
          say(`${tag} failed: ${e.message}`);
        }
      }
      if (skipped > 3) say(`…and ${skipped - 3} more already done.`);
      say(`${ok} analysed · ${skipped} skipped · ${failed} failed.`);
      logRun(corpus, 'analyze', {
        targets: targets.length, ok, skipped, failed,
        gate: g.threshold, reasoner: who, costUsd: est.totalUsd,
      });
      writeCorpus(corpus);
      return { analysed: ok, skipped, failed, attempted: targets.length, estimate: est };
    });
    return { jobId };
  },

  'POST /api/sources': async ({ clientId, handles }) => {
    const c = readCorpus();
    c.sources[clientId] = [...new Set(handles)];
    writeCorpus(c);
    return { ok: true, count: c.sources[clientId].length };
  },

  'POST /api/reset': async () => {
    // Snapshot first — losing a scraped-and-analysed corpus means paying for
    // it all again.
    const backup = backupCorpus();
    writeCorpus({ creators: {}, posts: [], sources: {}, runs: [] });
    return { ok: true, backup };
  },

  'POST /api/backup': async () => ({ ok: true, backup: backupCorpus() }),
};

const pickAnalysis = (p) => ({
  attributes: p.attributes, transcript: p.transcript, timeline: p.timeline,
  mechanism: p.mechanism, essentialElements: p.essentialElements,
  incidentalElements: p.incidentalElements, adaptations: p.adaptations,
});

/* ------------------------------------------------------------------ *
 * Server
 * ------------------------------------------------------------------ */

const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript',
  '.json': 'application/json', '.md': 'text/markdown', '.svg': 'image/svg+xml' };

const server = createServer(async (req, res) => {
  const url = new URL(req.url, 'http://localhost');
  const send = (code, body, type = 'application/json') => {
    res.writeHead(code, { 'content-type': type, 'cache-control': 'no-store' });
    // Buffers (static files) must go out raw — JSON.stringify turns them into
    // {"type":"Buffer","data":[...]}, which the browser cheerfully renders as
    // a blank page.
    if (Buffer.isBuffer(body) || typeof body === 'string') res.end(body);
    else res.end(JSON.stringify(body));
  };

  try {
    if (url.pathname.startsWith('/api/job/')) {
      const job = jobs.get(url.pathname.split('/').pop());
      return job ? send(200, job) : send(404, { error: 'unknown job' });
    }

    const handler = routes[`${req.method} ${url.pathname}`];
    if (handler) {
      let body = {};
      if (req.method === 'POST') {
        const chunks = [];
        for await (const c of req) chunks.push(c);
        body = chunks.length ? JSON.parse(Buffer.concat(chunks).toString()) : {};
      }
      return send(200, await handler(body, url));
    }

    if (url.pathname.startsWith('/api/')) return send(404, { error: 'no such route' });

    // Static. normalize() + the ROOT prefix check keeps ../ out of the tree.
    const rel = url.pathname === '/' ? '/index.html' : url.pathname;
    const file = normalize(join(ROOT, rel));
    if (!file.startsWith(ROOT)) return send(403, { error: 'forbidden' });
    return send(200, await readFile(file), MIME[extname(file)] || 'application/octet-stream');
  } catch (e) {
    if (e.code === 'ENOENT') return send(404, { error: 'not found' });
    send(500, { error: e.message });
  }
});

server.listen(env.port, () => {
  const k = keyStatus(env);
  const issues = keyIssues(env);
  console.log(`\n  Viral Content Studio  →  http://localhost:${env.port}\n`);
  console.log(`  instagram ${k.graph ? '✓' : '✗'}   gemini ${k.gemini ? '✓' : '✗'}   claude ${k.anthropic ? '✓ (optional)' : '– (optional)'}`);
  for (const msg of Object.values(issues)) if (msg) console.log(`  ! ${msg}`);
  console.log('');
});
