/**
 * Apify ingestion + normalisation.
 *
 * Every decision here was made against a real dataset
 * (54 records, 8 accounts, Aug 2026) rather than from the actor docs — see the
 * comments on view counts and pinned/trial handling, which is where this
 * silently goes wrong.
 */
import { jsonFetch } from './lib.mjs';

const REEL_ACTOR = 'apify~instagram-reel-scraper';
const PROFILE_ACTOR = 'apify~instagram-post-scraper';

/* ------------------------------------------------------------------ *
 * Running actors
 * ------------------------------------------------------------------ */

async function runActor(token, actor, input, { timeoutSecs = 300 } = {}) {
  const url =
    `https://api.apify.com/v2/acts/${actor}/run-sync-get-dataset-items` +
    `?token=${encodeURIComponent(token)}&timeout=${timeoutSecs}`;
  const items = await jsonFetch(
    url,
    { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(input) },
    { retries: 2, timeoutMs: (timeoutSecs + 30) * 1000 },
  );
  return Array.isArray(items) ? items : [];
}

export async function scrapeReels(token, handles, { limitPerAccount = 36 } = {}) {
  return runActor(token, REEL_ACTOR, {
    username: handles,
    resultsLimit: limitPerAccount,
  });
}

/**
 * Profile-grid posts, used only to work out which reels are unlisted.
 * See `applyExclusions` — the reel actor exposes no trial flag, so the grid is
 * the only signal available.
 */
export async function scrapeGrid(token, handles, { limitPerAccount = 60 } = {}) {
  return runActor(token, PROFILE_ACTOR, {
    username: handles,
    resultsLimit: limitPerAccount,
  });
}

/* ------------------------------------------------------------------ *
 * Exclusions
 * ------------------------------------------------------------------ */

export const EXCLUSION_LABELS = {
  scrape_error: 'Scraper returned an error for this account',
  not_a_reel: 'Not a reel (productType is not "clips")',
  pinned: 'Pinned to the profile',
  sponsored: 'Paid partnership — reach is bought, not earned',
  no_plays: 'No play count returned',
  suspected_unlisted: 'Not on the profile grid — likely a trial or archived reel',
};

/**
 * `gridShortcodes` is optional. When supplied, any reel whose shortcode is
 * absent from the account's own grid is treated as unlisted.
 *
 * Why this is a proxy rather than a check: the reel actor returns no trial
 * field — `productType` is "clips" for every record and `isPinned` was false
 * across the whole sample. Instagram trial reels are served only to
 * non-followers and do not appear on the profile grid, so grid-absence is the
 * closest observable signal. It also catches archived reels, which you equally
 * do not want in a baseline. Without a grid scrape nothing is excluded on this
 * basis and the flag simply stays off, because guessing from engagement shape
 * would delete exactly the outliers this system exists to find.
 */
export function applyExclusions(records, { gridShortcodes = null, dropUnlisted = true } = {}) {
  const kept = [];
  const dropped = [];
  const drop = (rec, reason) =>
    dropped.push({ reason, username: rec.ownerUsername || rec.username, shortCode: rec.shortCode });

  for (const rec of records) {
    if (rec.error) { drop(rec, 'scrape_error'); continue; }
    if (rec.productType && rec.productType !== 'clips') { drop(rec, 'not_a_reel'); continue; }
    if (rec.isPinned === true) { drop(rec, 'pinned'); continue; }
    if (rec.paidPartnership === true) { drop(rec, 'sponsored'); continue; }
    if (!(rec.videoPlayCount > 0)) { drop(rec, 'no_plays'); continue; }

    if (gridShortcodes) {
      const grid = gridShortcodes[rec.ownerUsername];
      if (grid && grid.size && !grid.has(rec.shortCode)) {
        if (dropUnlisted) { drop(rec, 'suspected_unlisted'); continue; }
        rec.__suspectedUnlisted = true;
      }
    }
    kept.push(rec);
  }
  return { kept, dropped };
}

export function gridIndex(gridRecords) {
  const idx = {};
  for (const r of gridRecords) {
    if (r.error || !r.ownerUsername) continue;
    (idx[r.ownerUsername] ||= new Set()).add(r.shortCode);
  }
  return idx;
}

/* ------------------------------------------------------------------ *
 * Normalisation
 * ------------------------------------------------------------------ */

const POSTER_HUES = [12, 24, 44, 92, 138, 168, 190, 218, 258, 280, 302, 340];
const GLYPHS = ['🍜', '🔥', '🥢', '🍲', '🌿', '🍋', '🫕', '🥟', '🍤', '🧄', '🌶️', '🍚'];

const hash = (s) => [...String(s)].reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 7);

export function normalizePost(rec, now = Date.now()) {
  const posted = new Date(rec.timestamp).getTime();
  const h = hash(rec.shortCode || rec.id);

  return {
    id: rec.shortCode || rec.id,
    creatorId: rec.ownerUsername,
    mediaType: 'reel',
    url: rec.url,
    // Reel "views" is videoPlayCount. videoViewCount is a different, much
    // smaller metric — in the sample the two differed by 1.4x to 118x and were
    // not proportional, so mixing them across a baseline is silent corruption.
    views: rec.videoPlayCount,
    playCount: rec.videoPlayCount,
    legacyViewCount: rec.videoViewCount ?? null,
    // Instagram hides likes on some accounts; the actor reports -1, which would
    // otherwise be read as a real value.
    likes: rec.likesCount >= 0 ? rec.likesCount : null,
    comments: rec.commentsCount ?? null,
    ageDays: Math.floor((now - posted) / 86400000),
    postedAt: rec.timestamp,
    durationS: Math.round(rec.videoDuration || 0),
    caption: (rec.caption || '').split('\n')[0].slice(0, 160) || '(no caption)',
    hashtags: rec.hashtags || [],
    videoUrl: rec.videoUrl || null,
    thumbnailUrl: rec.displayUrl || null,
    locationName: rec.locationName || null,
    music: rec.musicInfo
      ? { song: rec.musicInfo.song_name, artist: rec.musicInfo.artist_name, original: !!rec.musicInfo.uses_original_audio }
      : null,
    suspectedUnlisted: !!rec.__suspectedUnlisted,
    poster: { hue: POSTER_HUES[h % POSTER_HUES.length], glyph: GLYPHS[h % GLYPHS.length] },
    // Filled in later by the Gemini/Claude stages.
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
 * Creators are keyed on `ownerUsername`, never `inputUrl`. The actor returns
 * posts by other accounts that merely tagged the one you asked for — in the
 * sample, 2 of 47 — and attributing those to the requested account would put a
 * stranger's reach into its baseline.
 */
export function buildCreators(records) {
  const out = {};
  for (const rec of records) {
    const u = rec.ownerUsername;
    if (!u) continue;
    out[u] ||= { id: u, handle: u, name: rec.ownerFullName || u, niche: '', addedAt: new Date().toISOString() };
  }
  return out;
}

/** History rows the baseline computation needs, derived from the posts we hold. */
export function buildHistory(posts) {
  const byCreator = {};
  for (const p of posts) {
    (byCreator[p.creatorId] ||= []).push({
      id: p.id,
      mediaType: p.mediaType,
      views: p.views,
      ageDays: p.ageDays,
    });
  }
  return byCreator;
}
