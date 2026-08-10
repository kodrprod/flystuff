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

import { ROOT, loadEnv, keyStatus, keyIssues, assertKey, readCorpus, writeCorpus, backupCorpus, logRun } from './lib.mjs';
import {
  scrapeReels, scrapeGrid, gridIndex, applyExclusions, normalizePost,
  buildCreators, buildHistory, EXCLUSION_LABELS,
} from './apify.mjs';
import { findRestaurant, findSimilarAccounts, reasonAboutPost, extractWithGemini } from './ai.mjs';
import { computeBaseline, detectOutlier, CONFIG } from '../js/scoring.js';

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

/** Attach baselines + outlier multipliers using the same engine the UI uses. */
function withOutliers(posts) {
  const history = buildHistory(posts);
  return posts.map((p) => {
    const creator = { id: p.creatorId, history: history[p.creatorId] || [] };
    const baseline = computeBaseline(creator, p.mediaType, p.id);
    const outlier = detectOutlier(p, baseline);
    return { ...p, baselineViews: baseline.medianViews, baselineN: baseline.nPosts, outlier,
      outlierMultiplier: outlier.valid ? outlier.conservative : 0 };
  });
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
    return {
      keys: keyStatus(env),
      keyIssues: keyIssues(env),
      models: { anthropic: env.anthropicModel, gemini: env.geminiModel },
      corpus: {
        creators: Object.keys(c.creators).length,
        posts: c.posts.length,
        analysed: c.posts.filter((p) => p.attributes).length,
        sources: Object.fromEntries(Object.entries(c.sources).map(([k, v]) => [k, v.length])),
      },
      runs: c.runs.slice(0, 8),
    };
  },

  'GET /api/corpus': async (_body, url) => {
    const clientId = url.searchParams.get('clientId') || '';
    const c = readCorpus();
    const posts = clientPosts(c, clientId);
    const history = buildHistory(posts);
    const creators = Object.values(c.creators)
      .filter((cr) => history[cr.id])
      .map((cr) => ({ ...cr, history: history[cr.id] }));
    return { posts, creators, sources: c.sources[clientId] || [] };
  },

  'POST /api/discover/restaurant': async ({ query }) => {
    assertKey(env, 'anthropic', 'ANTHROPIC_API_KEY');
    if (!query?.trim()) throw new Error('query required');
    // Web search puts this around a minute; too long to hold a request open.
    const jobId = startJob('Finding the restaurant', async (say) => {
      say(`Searching the web for "${query.trim()}"…`);
      const out = await findRestaurant(env, query.trim());
      say(`${out.candidates?.length || 0} candidates.`);
      return out;
    });
    return { jobId };
  },

  'POST /api/discover/similar': async ({ restaurant, count }) => {
    assertKey(env, 'anthropic', 'ANTHROPIC_API_KEY');
    const jobId = startJob('Finding similar accounts', async (say) => {
      say(`Searching for accounts like ${restaurant.name}…`);
      const out = await findSimilarAccounts(env, restaurant, count || 45);
      say(`Found ${out.accounts.length} candidate accounts.`);
      return out;
    });
    return { jobId };
  },

  'POST /api/scrape': async ({ clientId, handles, limitPerAccount, gridCheck, gate }) => {
    assertKey(env, 'apify', 'APIFY_TOKEN');
    if (!handles?.length) throw new Error('handles required');

    const jobId = startJob(`Scraping ${handles.length} accounts`, async (say) => {
      const limit = limitPerAccount || 36;
      say(`Requesting up to ${limit} reels from ${handles.length} accounts…`);
      const raw = await scrapeReels(env.apify, handles, { limitPerAccount: limit });
      say(`Actor returned ${raw.length} records.`);

      let grid = null;
      if (gridCheck) {
        say('Scraping profile grids to detect unlisted / trial reels…');
        try {
          grid = gridIndex(await scrapeGrid(env.apify, handles, { limitPerAccount: 60 }));
          say(`Grid indexed for ${Object.keys(grid).length} accounts.`);
        } catch (e) {
          say(`Grid scrape failed (${e.message}) — continuing without unlisted detection.`);
        }
      }

      const { kept, dropped } = applyExclusions(raw, { gridShortcodes: grid, dropUnlisted: true });
      const byReason = {};
      dropped.forEach((d) => (byReason[d.reason] = (byReason[d.reason] || 0) + 1));
      Object.entries(byReason).forEach(([r, n]) => say(`Excluded ${n}: ${EXCLUSION_LABELS[r] || r}`));

      const corpus = readCorpus();
      const now = Date.now();
      const fresh = kept.map((r) => normalizePost(r, now));

      // Keep any analysis already paid for on a re-scrape.
      const existing = new Map(corpus.posts.map((p) => [p.id, p]));
      for (const p of fresh) {
        const prev = existing.get(p.id);
        existing.set(p.id, prev?.attributes ? { ...p, ...pickAnalysis(prev) } : p);
      }
      corpus.posts = [...existing.values()];
      Object.assign(corpus.creators, buildCreators(kept));
      if (clientId) {
        const owners = [...new Set(fresh.map((p) => p.creatorId))];
        corpus.sources[clientId] = [...new Set([...(corpus.sources[clientId] || []), ...owners])];
      }
      logRun(corpus, 'scrape', { accounts: handles.length, records: raw.length, kept: kept.length, dropped: byReason });
      writeCorpus(corpus);

      // Report what actually survives the funnel, not just what was stored.
      const threshold = gate > 0 ? gate : CONFIG.gemniGateMultiplier;
      const scored = withOutliers(corpus.posts);
      const usable = scored.filter((p) => p.outlier.valid);
      const past = usable.filter((p) => p.outlier.conservative >= threshold);
      say(`${corpus.posts.length} reels held · ${usable.length} have a usable baseline · ${past.length} clear the ${threshold}x gate.`);

      return { kept: kept.length, dropped: byReason, usable: usable.length, pastGate: past.length };
    });
    return { jobId };
  },

  'POST /api/analyze': async ({ clientId, client, limit, gate, force }) => {
    if (!env.gemini) throw new Error('GEMINI_API_KEY missing');
    assertKey(env, 'anthropic', 'ANTHROPIC_API_KEY');
    if (!client) throw new Error('client profile required');

    const jobId = startJob('Analysing outliers', async (say) => {
      const corpus = readCorpus();
      const scored = clientPosts(corpus, clientId);
      // The gate comes from the caller: the UI's Tune drawer can move it, and a
      // server-side constant would silently disagree with what the user sees.
      const threshold = gate > 0 ? gate : CONFIG.gemniGateMultiplier;
      const targets = scored
        .filter((p) => p.outlier.valid && p.outlier.conservative >= threshold)
        .sort((a, b) => b.outlierMultiplier - a.outlierMultiplier)
        .slice(0, limit || 30);

      if (!targets.length) {
        say(`Nothing clears the ${threshold}x gate yet — scrape more accounts, or more reels per account.`);
        return { analysed: 0 };
      }
      say(`${targets.length} outliers to analyse.`);

      const byId = new Map(corpus.posts.map((p) => [p.id, p]));
      let ok = 0, skipped = 0, failed = 0;

      for (const [i, t] of targets.entries()) {
        const stored = byId.get(t.id);
        const tag = `[${i + 1}/${targets.length}] @${t.creatorId}`;

        // Resume, don't repeat. Gemini output is per-video and Claude output is
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
            say(`${tag} — Gemini…`);
            Object.assign(stored, await extractWithGemini(env, stored));
            writeCorpus(corpus); // bank the video pass before spending on Claude
          } else {
            say(`${tag} — Gemini cached`);
          }

          say(`${tag} — Claude…`);
          const r = await reasonAboutPost(env, { ...stored, outlierMultiplier: t.outlierMultiplier }, client);
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
      logRun(corpus, 'analyze', { targets: targets.length, ok, skipped, failed, gate: threshold });
      writeCorpus(corpus);
      return { analysed: ok, skipped, failed, attempted: targets.length };
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
  console.log(`  apify ${k.apify ? '✓' : '✗'}   anthropic ${k.anthropic ? '✓' : '✗'}   gemini ${k.gemini ? '✓' : '✗'}`);
  for (const msg of Object.values(issues)) if (msg) console.log(`  ! ${msg}`);
  console.log('');
});
