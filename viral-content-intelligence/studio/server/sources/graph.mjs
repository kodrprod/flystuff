/**
 * Instagram Graph API — `business_discovery`.
 *
 * This is the free, official replacement for the Apify actors. It costs nothing,
 * has no scraping ToS exposure, and returns a competitor's whole reel history
 * with engagement metrics in one call per 50 reels.
 *
 * Three things it gives us that the paid scraper did not:
 *
 *  - `media_product_type` is an exact REELS/FEED/STORY discriminator, so reel
 *    filtering stops being a `productType === 'clips'` guess.
 *  - It returns the *profile grid*, which is what a trial reel is defined by not
 *    being on. Trial and archived reels are therefore excluded for free, with no
 *    second scrape and no `not_on_grid` proxy. That heuristic — and the €1.53
 *    grid scrape behind it — is gone.
 *  - It is chronological, so a pinned reel is not hoisted to the front of the
 *    list where it would distort a "most recent k posts" baseline.
 *
 * What it does NOT give: play/view counts. Views are only exposed for accounts
 * you own, via /insights. So virality here is measured on engagement — see
 * METRICS in ../../js/scoring.js for why that is sound rather than a compromise.
 */
import { jsonFetch } from '../lib.mjs';

const API = 'https://graph.facebook.com/v23.0';

/* Requested per media node. Kept in one place because the field list is the
 * contract — asking for a field the token can't see fails the whole edge. */
const MEDIA_FIELDS = [
  'id', 'caption', 'like_count', 'comments_count', 'timestamp',
  'permalink', 'media_product_type', 'media_type', 'media_url', 'thumbnail_url',
].join(',');

/* ------------------------------------------------------------------ *
 * Errors
 * ------------------------------------------------------------------ */

/**
 * Meta's error bodies are precise but the messages are not actionable, and every
 * one of these failure modes looks identical from the UI otherwise. Each branch
 * below is a real thing that happens on a first run.
 */
function explain(err, handle) {
  const code = err?.code;
  const sub = err?.error_subcode;
  const msg = err?.message || 'unknown Graph API error';

  if (code === 190 && sub === 463) return 'Access token expired — generate a new long-lived token.';
  if (code === 190) return `Access token rejected: ${msg}`;
  if (code === 10 || code === 200)
    return 'Token lacks instagram_basic / pages_read_engagement. Re-authorise the app with those scopes.';
  if (code === 100 && /does not exist|cannot be loaded|nonexisting/i.test(msg))
    return `@${handle}: no such account, or it is personal/private. business_discovery only sees public Business and Creator accounts.`;
  if (code === 4 || code === 17 || code === 32 || code === 613)
    return 'RATE_LIMIT'; // caller backs off rather than failing the run
  return `${msg}${code ? ` (code ${code})` : ''}`;
}

/* ------------------------------------------------------------------ *
 * Identity
 * ------------------------------------------------------------------ */

/**
 * Resolves the Instagram Business account behind the token, so the user pastes
 * one token and nothing else. business_discovery must be addressed *from* an IG
 * account you control — there is no standalone endpoint.
 */
export async function resolveSelf(token) {
  const pages = await jsonFetch(
    `${API}/me/accounts?fields=name,instagram_business_account{id,username}&access_token=${encodeURIComponent(token)}`,
    {}, { retries: 1, timeoutMs: 30000 },
  );
  if (pages.error) throw new Error(explain(pages.error, 'me'));

  const linked = (pages.data || []).filter((p) => p.instagram_business_account);
  if (!linked.length) {
    throw new Error(
      'No Instagram Business account is linked to this token. In Meta Business Suite, ' +
      'connect the Instagram account to a Facebook Page, then regenerate the token.',
    );
  }
  return linked.map((p) => ({
    pageName: p.name,
    igUserId: p.instagram_business_account.id,
    username: p.instagram_business_account.username,
  }));
}

/** Cheap liveness probe for /api/status — never throws. */
export async function graphStatus(token) {
  if (!token) return { ok: false, reason: 'no token' };
  try {
    const accounts = await resolveSelf(token);
    return { ok: true, accounts, self: accounts[0] };
  } catch (e) {
    return { ok: false, reason: e.message };
  }
}

/* ------------------------------------------------------------------ *
 * Fetching one account
 * ------------------------------------------------------------------ */

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * All reels for one handle, paging the media edge until `limit` or exhaustion.
 *
 * Paging is expressed inside the field spec (`media.limit(n).after(cursor)`)
 * rather than as a top-level `after` param — business_discovery is a nested
 * edge, so the usual paging parameters do not apply to it.
 */
export async function fetchAccount(token, igUserId, handle, { limit = 50, pageSize = 50 } = {}) {
  const out = [];
  let cursor = null;
  let profile = null;

  for (let page = 0; page < 20 && out.length < limit; page++) {
    const media = `media.limit(${pageSize})${cursor ? `.after(${cursor})` : ''}{${MEDIA_FIELDS}}`;
    const fields = `business_discovery.username(${handle}){followers_count,media_count,${media}}`;
    const url = `${API}/${igUserId}?fields=${encodeURIComponent(fields)}&access_token=${encodeURIComponent(token)}`;

    let res = await jsonFetch(url, {}, { retries: 1, timeoutMs: 45000 });

    if (res.error) {
      const why = explain(res.error, handle);
      if (why === 'RATE_LIMIT') {
        // One long backoff beats a tight retry loop: Meta's window is hourly and
        // hammering it extends the block.
        await sleep(60000);
        res = await jsonFetch(url, {}, { retries: 0, timeoutMs: 45000 });
        if (res.error) throw new Error('Rate limited by Instagram — wait an hour, or lower accounts per run.');
      } else {
        throw new Error(why);
      }
    }

    const bd = res.business_discovery;
    if (!bd) throw new Error(`@${handle}: no data returned (likely private, personal, or renamed).`);
    profile ||= { followers: bd.followers_count ?? null, mediaCount: bd.media_count ?? null };

    const batch = bd.media?.data || [];
    out.push(...batch);

    cursor = bd.media?.paging?.cursors?.after || null;
    if (!cursor || !batch.length) break;
  }

  return { handle, profile, media: out.slice(0, limit) };
}

/* ------------------------------------------------------------------ *
 * Normalisation — same shape the rest of the app already speaks
 * ------------------------------------------------------------------ */

const POSTER_HUES = [12, 24, 44, 92, 138, 168, 190, 218, 258, 280, 302, 340];
const GLYPHS = ['🍜', '🔥', '🥢', '🍲', '🌿', '🍋', '🫕', '🥟', '🍤', '🧄', '🌶️', '🍚'];
const hash = (s) => [...String(s)].reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 7);

/** `/p/CODE/` or `/reel/CODE/` -> CODE. The shortcode keys everything downstream. */
export function shortCodeOf(permalink = '') {
  return permalink.match(/\/(?:p|reel|tv)\/([^/?#]+)/)?.[1] || null;
}

export function normalizeGraphMedia(m, handle, now = Date.now()) {
  const id = shortCodeOf(m.permalink) || m.id;
  const h = hash(id);
  const posted = new Date(m.timestamp).getTime();

  const flags = [];
  if (m.media_product_type !== 'REELS') flags.push('not_a_reel');
  // Some accounts hide like counts; Graph then omits the field entirely. That is
  // a real, recoverable state — comments alone still support a baseline — so it
  // is flagged rather than dropped.
  const likes = Number.isFinite(m.like_count) ? m.like_count : null;
  const comments = Number.isFinite(m.comments_count) ? m.comments_count : null;
  if (likes === null) flags.push('likes_hidden');
  if (likes === null && comments === null) flags.push('no_metrics');

  return {
    id,
    creatorId: handle,
    mediaType: 'reel',
    source: 'graph',
    url: m.permalink,
    // No view counts exist on this API for other people's media. Left null on
    // purpose so nothing downstream can quietly treat engagement as reach.
    views: null,
    playCount: null,
    likes,
    comments,
    engagement: (likes || 0) + (comments || 0),
    ageDays: Math.floor((now - posted) / 86400000),
    postedAt: m.timestamp,
    durationS: 0, // Graph does not expose duration; filled in by the video fetch
    caption: (m.caption || '').split('\n')[0].slice(0, 160) || '(no caption)',
    hashtags: [...(m.caption || '').matchAll(/#(\w+)/g)].map((x) => x[1]).slice(0, 20),
    videoUrl: m.media_url || null,
    thumbnailUrl: m.thumbnail_url || m.media_url || null,
    locationName: null,
    music: null,
    flags,
    poster: { hue: POSTER_HUES[h % POSTER_HUES.length], glyph: GLYPHS[h % GLYPHS.length] },
    attributes: null,
    transcript: null,
    timeline: [],
    mechanism: null,
    essentialElements: [],
    incidentalElements: [],
    adaptations: {},
  };
}

/**
 * Fetches many handles, one at a time with a small gap.
 *
 * Sequential on purpose. The rate limit is per IG user, so parallelism buys no
 * throughput and turns a slow run into an hour-long block.
 */
export async function fetchMany(token, igUserId, handles, { limitPerAccount = 50, gapMs = 400, onProgress } = {}) {
  const accounts = [];
  const failures = [];

  for (const [i, handle] of handles.entries()) {
    try {
      const acc = await fetchAccount(token, igUserId, handle, { limit: limitPerAccount });
      accounts.push(acc);
      onProgress?.({ i: i + 1, n: handles.length, handle, got: acc.media.length });
    } catch (e) {
      failures.push({ handle, error: e.message });
      onProgress?.({ i: i + 1, n: handles.length, handle, error: e.message });
    }
    if (i < handles.length - 1) await sleep(gapMs);
  }
  return { accounts, failures };
}
