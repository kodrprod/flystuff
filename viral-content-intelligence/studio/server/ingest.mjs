/**
 * Corpus helpers, plus importing a JSON export you already have.
 *
 * The Apify integration is gone — no actor is called, no token is read, nothing
 * here can spend money. What survives is the ability to *read* an export file
 * already sitting on disk, because those reels are paid for and throwing them
 * away would be the second time this project destroyed data it had already
 * bought.
 *
 * The normaliser is therefore a file-format reader, not a scraper. Point it at
 * an `apify/instagram-reel-scraper` dataset dump, or anything with the same
 * shape, and it folds into the same corpus the Graph API writes to.
 */

const POSTER_HUES = [12, 24, 44, 92, 138, 168, 190, 218, 258, 280, 302, 340];
const GLYPHS = ['🍜', '🔥', '🥢', '🍲', '🌿', '🍋', '🫕', '🥟', '🍤', '🧄', '🌶️', '🍚'];

const hash = (s) => [...String(s)].reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 7);

/* ------------------------------------------------------------------ *
 * Flags
 * ------------------------------------------------------------------ */

export const EXCLUSION_LABELS = {
  not_a_reel: 'Not a reel',
  pinned: 'Pinned to the profile',
  sponsored: 'Paid partnership — reach is bought, not earned',
  no_plays: 'No play count returned',
  no_metrics: 'No likes or comments returned',
  likes_hidden: 'Account hides like counts',
  not_on_grid: 'Not on the profile grid (legacy scrape only)',
};

/**
 * Annotates records with the reasons they *could* be excluded. Nothing is
 * dropped here.
 *
 * An earlier version deleted at ingest, and a shallow grid check silently
 * destroyed a third of a 295-reel run. Reels you already have should never be
 * unrecoverable because a heuristic misfired — store everything, flag it, and
 * let the filter panel decide.
 */
export function annotateRecords(records) {
  const kept = [];
  const counts = {};
  const bump = (r) => (counts[r] = (counts[r] || 0) + 1);

  for (const rec of records) {
    if (rec.error) { bump('scrape_error'); continue; } // no post to store
    const flags = [];

    if (rec.productType && rec.productType !== 'clips') flags.push('not_a_reel');
    if (rec.isPinned === true) flags.push('pinned');
    if (rec.paidPartnership === true) flags.push('sponsored');
    if (!(rec.videoPlayCount > 0)) flags.push('no_plays');
    if (!(rec.likesCount > 0) && !(rec.commentsCount > 0)) flags.push('no_metrics');

    flags.forEach(bump);
    rec.__flags = flags;
    kept.push(rec);
  }
  return { kept, counts };
}

/* ------------------------------------------------------------------ *
 * Normalisation
 * ------------------------------------------------------------------ */

/** One record from a scraper export -> the shape the corpus speaks. */
export function normalizeExportedPost(rec, now = Date.now()) {
  const posted = new Date(rec.timestamp).getTime();
  const h = hash(rec.shortCode || rec.id);
  // Instagram hides likes on some accounts; the export reports -1, which would
  // otherwise be read as a real value.
  const likes = rec.likesCount >= 0 ? rec.likesCount : null;
  const comments = rec.commentsCount ?? null;

  return {
    id: rec.shortCode || rec.id,
    creatorId: rec.ownerUsername,
    mediaType: 'reel',
    source: 'import',
    url: rec.url,
    // Reel "views" is videoPlayCount. videoViewCount is a different, much
    // smaller metric — in the sample the two differed by 1.4x to 118x and were
    // not proportional, so mixing them across a baseline is silent corruption.
    views: rec.videoPlayCount,
    playCount: rec.videoPlayCount,
    legacyViewCount: rec.videoViewCount ?? null,
    likes,
    comments,
    engagement: (likes || 0) + (comments || 0),
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
    flags: rec.__flags || [],
    poster: { hue: POSTER_HUES[h % POSTER_HUES.length], glyph: GLYPHS[h % GLYPHS.length] },
    // Filled in later by the extraction and reasoning stages.
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
 * Creators are keyed on `ownerUsername`, never the requested handle. Exports
 * contain posts by other accounts that merely tagged the one you asked for — in
 * the sample, 2 of 47 — and attributing those to the requested account would put
 * a stranger's reach into its baseline.
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

/**
 * History rows the baseline computation needs, derived from the posts we hold.
 *
 * Carries both metrics because a corpus can be mixed — imported reels have play
 * counts, Graph API reels never will — and the scorer decides which one the
 * corpus as a whole can support.
 */
export function buildHistory(posts) {
  const byCreator = {};
  for (const p of posts) {
    (byCreator[p.creatorId] ||= []).push({
      id: p.id,
      mediaType: p.mediaType,
      views: p.views,
      likes: p.likes,
      comments: p.comments,
      engagement: Number.isFinite(p.engagement) ? p.engagement : (p.likes || 0) + (p.comments || 0),
      ageDays: p.ageDays,
      flags: p.flags || [], // the scorer drops excluded reels from baselines too
    });
  }
  return byCreator;
}

/**
 * Reads a dataset dump into normalised posts.
 * Accepts a bare array or the `{ items: [...] }` wrapper exports sometimes use.
 */
export function importDataset(json, now = Date.now()) {
  const records = Array.isArray(json) ? json : json?.items || json?.data || [];
  if (!Array.isArray(records)) throw new Error('Expected a JSON array of reel records.');

  const { kept, counts } = annotateRecords(records);
  const posts = kept.map((r) => normalizeExportedPost(r, now)).filter((p) => p.id && p.creatorId);
  return { posts, creators: buildCreators(kept), flagCounts: counts, read: records.length };
}
