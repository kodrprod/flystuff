/**
 * Cost model.
 *
 * Every action reports what it costs and which platform it bills to *before* it
 * runs. This exists because the first version of this tool quietly spent a €5
 * monthly allowance against a plan that promised €0.71 — the plan had costed a
 * cheaper actor than the one that shipped, and nothing in the UI showed the
 * difference until the money was gone.
 *
 * Apify prices are the real per-event rates read from their API (FREE tier);
 * Claude's are published list rates. Gemini's are overridable in .env because
 * per-model video rates move around — everything is labelled with its source so
 * an estimate is never mistaken for a quote.
 *
 * The default pipeline no longer bills anything: listing is the Instagram Graph
 * API, video fetching is yt-dlp, and both are free. Apify remains only as an
 * explicit opt-in and is the one thing here that can spend real money.
 */
import { jsonFetch } from './lib.mjs';

export const FREE = 'free';

export const RATES = {
  // apify.com — pay-per-event, FREE tier. Higher plans are cheaper per item.
  apifyReel: 0.0026,       // per reel written to the dataset
  apifyPost: 0.0017,       // per profile-grid post (the trial-reel check)
  apifyStart: 0.001,       // flat, per actor run

  // platform.claude.com/pricing — Opus 5
  claudeInPerM: 5.0,
  claudeOutPerM: 25.0,

  // ai.google.dev/pricing — override with GEMINI_IN_USD_PER_M / _OUT_ in .env
  geminiInPerM: +(process.env.GEMINI_IN_USD_PER_M || 0.3),
  geminiOutPerM: +(process.env.GEMINI_OUT_USD_PER_M || 2.5),

  // Observed on real reels: ~260 video tokens/sec plus ~32 audio tokens/sec.
  geminiTokensPerVideoSecond: 292,
  avgReelSeconds: 30,
  geminiOutTokensPerVideo: 900,

  // A reasoning call carries the attributes, the transcript and the client profile.
  claudeInTokensPerVideo: 2500,
  claudeOutTokensPerVideo: 800,

  // Web search + a long tool result.
  claudeInTokensPerSearch: 12000,
  claudeOutTokensPerSearch: 2500,
};

const usd = (n) => Math.round(n * 10000) / 10000;

/**
 * What a planned action will cost, itemised by the platform it bills to.
 *
 * Free steps still return a line item. "Instagram Graph API — $0.00" is
 * information; an empty panel looks like the estimate failed to load.
 */
export function estimate(action, p = {}) {
  const items = [];
  const add = (platform, detail, amount, note) =>
    items.push({ platform, detail, usd: usd(amount), free: amount === 0, note });

  /* ---- free listing via the official API ---- */
  if (action === 'graph') {
    const accounts = p.accounts || 0;
    const perAccount = Math.ceil((p.limitPerAccount || 50) / 50); // 50 media per call
    const calls = accounts * perAccount;
    add('Instagram Graph API', `${accounts} accounts · ~${calls} API calls`, 0,
      calls > 180 ? `Over ~180 calls/hour Instagram throttles; this run may pause.` : null);
    add('Instagram Graph API', `${accounts * (p.limitPerAccount || 50)} reels listed`, 0);
  }

  /* ---- free video fetch for the finalists ---- */
  if (action === 'video') {
    const n = p.videos || 0;
    const gapMin = Math.round((n * (p.gapMs ?? 20000)) / 60000);
    add('yt-dlp (direct)', `${n} videos downloaded`, 0,
      gapMin > 1 ? `Throttled to avoid a block — allow about ${gapMin} min.` : null);
  }

  if (action === 'scrape') {
    const accounts = p.accounts || 0;
    const reels = accounts * (p.limitPerAccount || 36);
    add('Apify', `${reels} reels @ $${RATES.apifyReel}`, reels * RATES.apifyReel);
    add('Apify', '1 actor start', RATES.apifyStart);
    if (p.gridCheck) {
      const posts = accounts * (p.gridDepth || 200);
      add('Apify', `grid check — up to ${posts} posts @ $${RATES.apifyPost}`, posts * RATES.apifyPost);
      add('Apify', '1 actor start', RATES.apifyStart);
    }
  }

  if (action === 'analyze') {
    const n = p.videos || 0;
    const secs = p.avgSeconds || RATES.avgReelSeconds;
    const freeTier = !!p.geminiFreeTier;

    // Watching the video. On the free tier this is rate-limited rather than
    // billed, so the cost is time.
    const gIn = (n * secs * RATES.geminiTokensPerVideoSecond) / 1e6;
    const gOut = (n * RATES.geminiOutTokensPerVideo) / 1e6;
    const geminiVideoUsd = freeTier ? 0 : gIn * RATES.geminiInPerM + gOut * RATES.geminiOutPerM;
    add('Gemini', `${n} videos × ~${secs}s — extraction`, geminiVideoUsd,
      freeTier ? 'Free tier: no charge, but throttled to a few requests per minute.' : null);

    // Turning the extraction into a filmable concept. Gemini by default: it is
    // an order of magnitude cheaper and the task is well-specified enough that
    // the stronger model is a preference rather than a requirement.
    if ((p.reasoner || 'gemini') === 'claude') {
      const cIn = (n * RATES.claudeInTokensPerVideo) / 1e6;
      const cOut = (n * RATES.claudeOutTokensPerVideo) / 1e6;
      add('Claude', `${n} reasoning calls`, cIn * RATES.claudeInPerM + cOut * RATES.claudeOutPerM);
    } else {
      const rIn = (n * RATES.claudeInTokensPerVideo) / 1e6;
      const rOut = (n * RATES.claudeOutTokensPerVideo) / 1e6;
      add('Gemini', `${n} reasoning calls`,
        freeTier ? 0 : rIn * RATES.geminiInPerM + rOut * RATES.geminiOutPerM);
    }
  }

  if (action === 'discover' || action === 'similar') {
    const n = action === 'similar' ? 2 : 1; // similar searches harder and writes more
    const inUsd = (RATES.claudeInTokensPerSearch / 1e6);
    const outUsd = (RATES.claudeOutTokensPerSearch / 1e6);
    if ((p.reasoner || 'gemini') === 'claude') {
      add('Claude', `web search + ${action}`,
        n * (inUsd * RATES.claudeInPerM + outUsd * RATES.claudeOutPerM));
    } else {
      add('Gemini', `Google Search grounding + ${action}`,
        p.geminiFreeTier ? 0 : n * (inUsd * RATES.geminiInPerM + outUsd * RATES.geminiOutPerM));
    }
  }

  const totalUsd = usd(items.reduce((a, b) => a + b.usd, 0));
  return {
    action,
    items,
    totalUsd,
    // Grouped so the UI can say "$0.00 · Instagram Graph API" without re-deriving it.
    byPlatform: items.reduce((acc, i) => ((acc[i.platform] = usd((acc[i.platform] || 0) + i.usd)), acc), {}),
    free: totalUsd === 0,
  };
}

/** Live Apify balance, so "you have $0.00 left" appears before a run, not after. */
export async function apifyUsage(token) {
  if (!token) return null;
  try {
    const d = await jsonFetch(`https://api.apify.com/v2/users/me/limits?token=${encodeURIComponent(token)}`,
      {}, { retries: 1, timeoutMs: 15000 });
    const used = d?.data?.current?.monthlyUsageUsd ?? null;
    const limit = d?.data?.limits?.maxMonthlyUsageUsd ?? null;
    if (used == null) return null;
    return { usedUsd: Math.round(used * 100) / 100, limitUsd: limit,
      remainingUsd: limit == null ? null : Math.round((limit - used) * 100) / 100 };
  } catch {
    return null;
  }
}
