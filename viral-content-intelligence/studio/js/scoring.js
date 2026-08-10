/**
 * Deterministic scoring engine.
 *
 * Implements §5 of ../../PLAN.md. The models (Gemini, Claude) never emit a
 * score — they emit observable attributes. Everything numeric happens here,
 * in code you can read, tune and unit-test.
 *
 * Every weight and penalty in this file is a knob. Change it, reload, watch
 * the ranking move. That is the whole point of keeping it out of the LLM.
 */

export const SCORER_VERSION = '0.3.0';

/* ------------------------------------------------------------------ *
 * Tunables
 * ------------------------------------------------------------------ */

export const CONFIG = {
  // §5.1 baseline guards
  minBaselinePosts: 8,
  minBaselineViews: 1000,

  // §5.2 maturity gate — posts outside this window are not scored at all
  minAgeDays: 14,
  maxAgeDays: 90,

  // §5.3 gate to expensive extraction
  gemniGateMultiplier: 8,

  // §5.3 log ceiling: a 50x outlier saturates V
  virailtyCeiling: 50,

  // How long from shortlist to camera. Trends with a shorter half-life are dead
  // before the client can film them.
  daysToFilm: 7,

  // §5.4 opportunity exponents. Must sum to 1.
  weights: { V: 0.35, R: 0.3, F: 0.2, T: 0.15 },

  // §5.4 replicability penalties
  penalties: {
    namedPersonDependency: 0.45,
    uniqueVenue: 0.35,
    manyPeopleOnCamera: 0.15, // > 3 people
    equipmentGapEach: 0.1, // per missing item, capped below
    equipmentGapCap: 0.2,
    editVfx: 0.2,
    editHeavy: 0.1,
    licensedMusic: 0.15,
    shortTrendHalfLife: 0.15, // < 14 days
  },

  // §5.4 client-fit component weights. Must sum to 1.
  fitWeights: {
    space: 0.35,
    chefWillingness: 0.2,
    staffTime: 0.15,
    castSize: 0.15,
    customersOnCamera: 0.15,
  },
};

/* ------------------------------------------------------------------ *
 * Small helpers
 * ------------------------------------------------------------------ */

const clamp = (lo, hi, x) => Math.min(hi, Math.max(lo, x));

export function median(xs) {
  if (!xs.length) return 0;
  const s = [...xs].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

export function percentile(xs, p) {
  if (!xs.length) return 0;
  const s = [...xs].sort((a, b) => a - b);
  const i = clamp(0, s.length - 1, Math.ceil((p / 100) * s.length) - 1);
  return s[i];
}

export const ageDays = (iso, now = Date.now()) =>
  Math.floor((now - new Date(iso).getTime()) / 86400000);

/* ------------------------------------------------------------------ *
 * §5.1 / §5.3  Baseline and outlier detection — no client involved
 * ------------------------------------------------------------------ */

/**
 * Baseline for one creator + media type. Median of the k most recent mature
 * posts of the same type, excluding the candidate.
 *
 * Same media type only: reels and carousels have completely different reach
 * mechanics, and mixing them manufactures outliers that aren't there.
 */
export function computeBaseline(creator, mediaType, excludePostId = null, k = 12) {
  const pool = creator.history
    .filter((h) => h.mediaType === mediaType)
    .filter((h) => h.id !== excludePostId)
    .filter((h) => h.ageDays >= CONFIG.minAgeDays)
    .sort((a, b) => a.ageDays - b.ageDays)
    .slice(0, k);

  const views = pool.map((p) => p.views);
  const med = median(views);

  return {
    creatorId: creator.id,
    mediaType,
    nPosts: pool.length,
    medianViews: med,
    p75Views: percentile(views, 75),
    // Guards: a dormant account with a 200-view baseline otherwise produces a
    // "50x outlier" every time it posts.
    valid: pool.length >= CONFIG.minBaselinePosts && med >= CONFIG.minBaselineViews,
  };
}

/**
 * Outlier multiplier. Ranks on the conservative (p75-based) figure because with
 * k=12 the median is noisy and we don't want to spend Gemini calls on noise.
 */
export function detectOutlier(post, baseline) {
  const age = post.ageDays;
  const matureEnough = age >= CONFIG.minAgeDays && age <= CONFIG.maxAgeDays;

  if (!baseline.valid || !matureEnough) {
    return {
      valid: false,
      reason: !baseline.valid
        ? `Baseline unusable (n=${baseline.nPosts}, median=${baseline.medianViews})`
        : age < CONFIG.minAgeDays
          ? `Too recent to score (${age}d < ${CONFIG.minAgeDays}d maturity gate)`
          : `Too old (${age}d > ${CONFIG.maxAgeDays}d)`,
      multiplier: 0,
      conservative: 0,
    };
  }

  const multiplier = post.views / baseline.medianViews;
  const conservative = post.views / (baseline.p75Views || baseline.medianViews);

  return {
    valid: true,
    multiplier,
    conservative,
    band: band(conservative),
    passesGate: conservative >= CONFIG.gemniGateMultiplier,
  };
}

export function band(m) {
  if (m >= 50) return { label: 'exceptional', tone: 'peak' };
  if (m >= 25) return { label: 'major outlier', tone: 'high' };
  if (m >= 10) return { label: 'outlier', tone: 'high' };
  if (m >= 5) return { label: 'strong', tone: 'mid' };
  if (m >= 2) return { label: 'interesting', tone: 'low' };
  return { label: 'normal', tone: 'low' };
}

/* ------------------------------------------------------------------ *
 * §5.4  Attributes + client profile -> scores
 * ------------------------------------------------------------------ */

/** V — virality evidence. Log scale: 40x vs 80x is not twice as interesting. */
export function scoreVirality(conservativeMultiplier) {
  if (conservativeMultiplier <= 1) return 0;
  return clamp(
    0,
    1,
    Math.log10(conservativeMultiplier) / Math.log10(CONFIG.virailtyCeiling),
  );
}

/** R — replicability. Pure penalty table over extracted attributes. */
export function scoreReplicability(attrs, client) {
  const p = CONFIG.penalties;
  const hits = [];
  let total = 0;

  const add = (amount, label) => {
    total += amount;
    hits.push({ label, amount });
  };

  if (attrs.namedPersonDependency) add(p.namedPersonDependency, 'Needs a specific known person');
  if (attrs.locationType === 'unique_venue') add(p.uniqueVenue, 'Depends on a one-off venue');
  if (attrs.peopleOnCamera > 3) add(p.manyPeopleOnCamera, `Cast of ${attrs.peopleOnCamera}`);

  const missingKit = (attrs.equipment || []).filter(
    (e) => !client.capability.equipment.includes(e),
  );
  if (missingKit.length) {
    add(
      Math.min(p.equipmentGapCap, missingKit.length * p.equipmentGapEach),
      `Kit you don't have: ${missingKit.join(', ')}`,
    );
  }

  if (attrs.editComplexity === 'vfx_motion_graphics') add(p.editVfx, 'VFX / motion graphics edit');
  else if (attrs.editComplexity === 'heavy_cuts_captions') add(p.editHeavy, 'Heavy cut + caption edit');

  if (attrs.audioDependency === 'licensed_music') add(p.licensedMusic, 'Licensed music dependency');
  if (attrs.trendHalfLifeDays && attrs.trendHalfLifeDays < 14)
    add(p.shortTrendHalfLife, `Trend half-life only ${attrs.trendHalfLifeDays}d`);

  return { score: clamp(0, 1, 1 - total), penalties: hits, totalPenalty: total };
}

/**
 * F — client fit. A capability compatibility check, not a vibe. Every component
 * maps to a field the client filled in during intake.
 */
export function scoreFit(attrs, client) {
  const cap = client.capability;
  const w = CONFIG.fitWeights;
  const parts = [];

  // Space
  const hasSpace = cap.spaces.includes(attrs.spaceRequired);
  const substitutable = (SPACE_SUBSTITUTES[attrs.spaceRequired] || []).some((s) =>
    cap.spaces.includes(s),
  );
  const spaceScore = hasSpace ? 1 : substitutable ? 0.55 : 0;
  parts.push({
    key: 'space',
    label: `Needs ${labelSpace(attrs.spaceRequired)}`,
    score: spaceScore,
    weight: w.space,
    note: hasSpace ? 'available' : substitutable ? 'workable substitute' : 'not available',
  });

  // Chef willingness
  const need = attrs.chefOnCamera ? 1 : 0;
  const willing = { high: 1, medium: 0.65, low: 0.3, no: 0 }[cap.chefOnCamera] ?? 0;
  const chefScore = need ? willing : 1;
  parts.push({
    key: 'chefWillingness',
    label: attrs.chefOnCamera ? 'Chef must appear' : 'No chef appearance needed',
    score: chefScore,
    weight: w.chefWillingness,
    note: need ? `willingness: ${cap.chefOnCamera}` : 'n/a',
  });

  // Staff time
  const timeScore = clamp(0, 1, cap.staffMinutesPerConcept / Math.max(1, attrs.staffMinutes));
  parts.push({
    key: 'staffTime',
    label: `${attrs.staffMinutes} min of staff time`,
    score: clamp(0, 1, timeScore),
    weight: w.staffTime,
    note: `budget ${cap.staffMinutesPerConcept} min`,
  });

  // Cast size
  const castScore = clamp(0, 1, cap.staffAvailableForFilming / Math.max(1, attrs.peopleOnCamera));
  parts.push({
    key: 'castSize',
    label: `${attrs.peopleOnCamera} on camera`,
    score: castScore,
    weight: w.castSize,
    note: `${cap.staffAvailableForFilming} available`,
  });

  // Customers on camera
  const custScore = attrs.customersOnCamera ? (cap.customersOnCamera ? 1 : 0.2) : 1;
  parts.push({
    key: 'customersOnCamera',
    label: attrs.customersOnCamera ? 'Films real customers' : 'No customers on camera',
    score: custScore,
    weight: w.customersOnCamera,
    note: attrs.customersOnCamera ? (cap.customersOnCamera ? 'permitted' : 'not permitted') : 'n/a',
  });

  const score = parts.reduce((acc, p) => acc + p.weight * p.score, 0);
  return { score: clamp(0, 1, score), parts };
}

/**
 * T — tone / brand fit.
 *
 * Added beyond PLAN.md §5.4 because clients differ on register, not just
 * capability: a mall kebab counter wants jokes, a sit-down Vietnamese
 * restaurant wants craft and warmth. The same replicable mechanism can be
 * right for one and wrong for the other.
 */
export function scoreTone(attrs, client) {
  const prefs = client.capability.preferredTones || {};
  const primary = prefs[attrs.tone] ?? 0.25;
  const secondary = attrs.secondaryTone ? (prefs[attrs.secondaryTone] ?? 0.25) * 0.4 : 0;
  return {
    score: clamp(0.05, 1, primary + secondary),
    primary: attrs.tone,
    primaryWeight: primary,
    secondary: attrs.secondaryTone || null,
  };
}

const SPACE_SUBSTITUTES = {
  full_kitchen: ['small_kitchen'],
  small_kitchen: ['counter', 'full_kitchen'],
  counter: ['small_kitchen'],
  dining_room: ['shared_seating'],
  shared_seating: ['dining_room'],
};

const SPACE_LABELS = {
  counter: 'service counter',
  small_kitchen: 'small prep kitchen',
  full_kitchen: 'full kitchen',
  dining_room: 'own dining room',
  shared_seating: 'shared seating area',
  outdoor: 'outdoor space',
  street: 'street / public area',
  multi_location: 'multiple locations',
};
export const labelSpace = (s) => SPACE_LABELS[s] || s;

/* ------------------------------------------------------------------ *
 * Hard filters — drops, not deductions
 * ------------------------------------------------------------------ */

export function hardFilters(attrs, client, tone) {
  const cap = client.capability;
  const fails = [];

  const ceiling = cap.monthlyBudgetEur / 6;
  if (attrs.propsCostEur > ceiling)
    fails.push(`Costs €${attrs.propsCostEur} — over the €${Math.round(ceiling)} per-concept ceiling`);

  const hasSpace =
    cap.spaces.includes(attrs.spaceRequired) ||
    (SPACE_SUBSTITUTES[attrs.spaceRequired] || []).some((s) => cap.spaces.includes(s));
  if (!hasSpace) fails.push(`Requires ${labelSpace(attrs.spaceRequired)}, which this site doesn't have`);

  if (attrs.trendHalfLifeDays && attrs.trendHalfLifeDays < CONFIG.daysToFilm)
    fails.push(`Trend dies in ${attrs.trendHalfLifeDays}d, filming takes ${CONFIG.daysToFilm}d`);

  if ((cap.avoidTones || []).includes(attrs.tone))
    fails.push(`Tone "${attrs.tone}" is off-brand for this client`);

  return fails;
}

/* ------------------------------------------------------------------ *
 * Top level
 * ------------------------------------------------------------------ */

export function scoreConcept(post, creator, client, now = Date.now()) {
  const baseline = computeBaseline(creator, post.mediaType, post.id);
  const outlier = detectOutlier(post, baseline);

  const base = { post, creator, client, baseline, outlier, scorerVersion: SCORER_VERSION };

  if (!outlier.valid) return { ...base, stage: 'rejected', dropReasons: [outlier.reason], opportunity: 0 };
  if (!outlier.passesGate)
    return {
      ...base,
      stage: 'below_gate',
      dropReasons: [
        `${outlier.conservative.toFixed(1)}x is under the ${CONFIG.gemniGateMultiplier}x extraction gate`,
      ],
      opportunity: 0,
    };

  const attrs = post.attributes;
  const V = scoreVirality(outlier.conservative);
  const R = scoreReplicability(attrs, client);
  const F = scoreFit(attrs, client);
  const T = scoreTone(attrs, client);
  const dropReasons = hardFilters(attrs, client, T);

  if (dropReasons.length)
    return { ...base, stage: 'filtered', dropReasons, V, R, F, T, opportunity: 0 };

  const w = CONFIG.weights;
  // Weighted geometric mean: a zero in any dimension kills the concept, but the
  // score stays bounded and no single factor can swamp the others.
  const opportunity =
    100 *
    Math.pow(Math.max(V, 1e-6), w.V) *
    Math.pow(Math.max(R.score, 1e-6), w.R) *
    Math.pow(Math.max(F.score, 1e-6), w.F) *
    Math.pow(Math.max(T.score, 1e-6), w.T);

  return { ...base, stage: 'scored', V, R, F, T, dropReasons: [], opportunity };
}

export function scoreAll(posts, creators, client, now = Date.now()) {
  const byId = Object.fromEntries(creators.map((c) => [c.id, c]));
  return posts
    .map((p) => scoreConcept(p, byId[p.creatorId], client, now))
    .sort((a, b) => b.opportunity - a.opportunity);
}
