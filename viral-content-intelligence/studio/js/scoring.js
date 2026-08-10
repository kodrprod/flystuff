/**
 * Deterministic scoring engine.
 *
 * Implements §5 of ../../PLAN.md. The models (Gemini, Claude) never emit a
 * score — they emit observable attributes. Everything numeric happens here,
 * in code you can read, tune and unit-test.
 *
 * Every weight and penalty in this file is a knob. Change it, reload, watch
 * the ranking move. That is the whole point of keeping it out of the LLM.
 *
 * v0.4 changed two load-bearing things, both forced by moving off the paid
 * scraper onto free sources — see METRICS and the gate section below.
 */

export const SCORER_VERSION = '0.4.0';

/* ------------------------------------------------------------------ *
 * Metrics
 * ------------------------------------------------------------------ *
 *
 * Outlier detection needs one number per post that means "how much reach did
 * this get". The free sources do not expose plays: the Instagram Graph API
 * returns view counts only for accounts you own, and anonymous scraping is
 * blocked outright. Engagement is what remains.
 *
 * This is sound rather than a fallback, for one reason: every figure here is a
 * *ratio against the same account's own median*. The unit cancels. What matters
 * is that the metric is consistent within an account, and likes+comments is
 * more consistent than plays ever was — the paid scraper's `videoPlayCount` and
 * `videoViewCount` disagreed by 1.4x to 118x on the same posts (PLAN.md §10).
 *
 * The real consequence is one of *scale*, and it is why the fixed gate had to
 * go: likes saturate where plays do not, so a reel with 40x the plays might
 * show 8-12x the likes. Engagement multipliers are compressed. An 8x threshold
 * tuned on plays passes almost nothing on engagement — which is exactly the
 * "only 2 candidates" failure. See GATE below.
 */

export const METRICS = {
  views: {
    key: 'views',
    label: 'Plays',
    short: 'plays',
    get: (p) => (p.views > 0 ? p.views : null),
    // A dormant account with a 200-play baseline otherwise mints a 50x outlier
    // every time it posts.
    floor: 1000,
    // Added to the denominator so a small baseline cannot explode the ratio.
    smoothing: 100,
  },
  engagement: {
    key: 'engagement',
    label: 'Likes + comments',
    short: 'engagement',
    get: (p) => {
      const e = Number.isFinite(p.engagement) ? p.engagement : (p.likes || 0) + (p.comments || 0);
      return e > 0 ? e : null;
    },
    /**
     * Same guard, rescaled — restaurant reels routinely sit in the tens, so
     * 1000 would reject nearly every real account.
     *
     * 10 rather than 20 because 20 threw out real accounts: @sfizio_dresden has
     * 28 mature reels and a 5,012 median play count, and was rejected purely
     * for a median engagement of 5. Rejecting an account with 28 posts of
     * evidence is the guard misfiring, not working.
     */
    floor: 10,
    // Engagement counts are small enough to be genuinely noisy: a median of 5
    // makes a reel with 40 an "8x outlier" that is really just a good week.
    smoothing: 3,
  },
};

/**
 * Picks the metric a corpus can actually support.
 *
 * Auto rather than hard-coded because a corpus can be mixed: 165 reels here came
 * from the paid scraper and carry plays, everything new comes from the Graph API
 * and does not. Scoring those against each other on different metrics would be
 * silent corruption, so the whole corpus commits to whichever metric the
 * majority supports.
 */
export function resolveMetric(posts = []) {
  if (CONFIG.metric !== 'auto') return METRICS[CONFIG.metric] || METRICS.engagement;
  const withViews = posts.filter((p) => METRICS.views.get(p) !== null).length;
  return withViews >= posts.length * 0.6 && withViews > 0 ? METRICS.views : METRICS.engagement;
}

/* ------------------------------------------------------------------ *
 * Tunables
 * ------------------------------------------------------------------ */

export const CONFIG = {
  // 'auto' | 'views' | 'engagement'
  metric: 'auto',

  // §5.1 baseline guards
  minBaselinePosts: 8,
  /** null = use the metric's own floor. A number overrides it. */
  minBaselineValue: null,

  // §5.2 maturity gate — posts outside this window are not scored at all
  minAgeDays: 14,
  maxAgeDays: 90,

  /* --- GATE ---------------------------------------------------------
   * 'topN'       analyse the N strongest reels in the corpus, whatever their
   *              multiplier. N is simultaneously the quality knob and the
   *              entire cost ceiling, and it can never return zero candidates.
   * 'multiplier' the old fixed threshold, kept because it is the honest way to
   *              ask "is anything here genuinely exceptional".
   *
   * topN is the default because the fixed 8x threshold was arbitrary, was tuned
   * against plays, and produced 2 candidates out of 200 reels when the brief
   * asks for 6 concepts.
   * ------------------------------------------------------------------ */
  gateMode: 'topN',
  topN: 30,
  gateMultiplier: 8,
  /** Never analyse a reel that merely matches its own account's median. */
  minMultiplier: 1.5,

  // §5.3 log ceiling: a 50x outlier saturates V
  viralityCeiling: 50,

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

  /**
   * Which ingest flags exclude a reel. Nothing is deleted at ingest — reels
   * carry their flags and these switches decide what counts, so a filter you
   * disagree with costs a click rather than a re-scrape.
   */
  exclude: {
    pinned: true,
    sponsored: true,
    not_a_reel: true,
    no_plays: false,   // only meaningful on the legacy scraped corpus
    no_metrics: true,  // nothing to score at all
    likes_hidden: false, // comments alone still support a baseline
    not_on_grid: false, // legacy proxy; the Graph API returns the grid directly
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

export const isExcluded = (post) => (post.flags || []).filter((f) => CONFIG.exclude[f]);

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
export function computeBaseline(creator, mediaType, excludePostId = null, metric = METRICS.engagement, k = 12) {
  const pool = (creator.history || [])
    .filter((h) => h.mediaType === mediaType)
    .filter((h) => !(h.flags || []).some((f) => CONFIG.exclude[f]))
    .filter((h) => h.id !== excludePostId)
    .filter((h) => h.ageDays >= CONFIG.minAgeDays)
    .filter((h) => metric.get(h) !== null)
    .sort((a, b) => a.ageDays - b.ageDays)
    .slice(0, k);

  const values = pool.map((p) => metric.get(p));
  const med = median(values);
  const floor = CONFIG.minBaselineValue ?? metric.floor;

  return {
    creatorId: creator.id,
    mediaType,
    metric: metric.key,
    nPosts: pool.length,
    medianValue: med,
    p75Value: percentile(values, 75),
    // Retained under the old name so anything still reading `medianViews` keeps
    // working; it is the median of whichever metric is in force.
    medianViews: med,
    valid: pool.length >= CONFIG.minBaselinePosts && med >= floor,
    floor,
  };
}

/**
 * Outlier multiplier. Ranks on the conservative (p75-based) figure because with
 * k=12 the median is noisy and we don't want to spend extraction on noise.
 */
export function detectOutlier(post, baseline, metric = METRICS.engagement) {
  const age = post.ageDays;
  const matureEnough = age >= CONFIG.minAgeDays && age <= CONFIG.maxAgeDays;
  const value = metric.get(post);

  if (!baseline.valid || !matureEnough || value === null) {
    return {
      valid: false,
      reason:
        value === null
          ? `No ${metric.short} recorded for this reel`
          : !baseline.valid
            ? `Baseline unusable (n=${baseline.nPosts}, median ${metric.short} ${Math.round(baseline.medianValue)}, need ${baseline.nPosts < CONFIG.minBaselinePosts ? `${CONFIG.minBaselinePosts} posts` : `${baseline.floor}`})`
            : age < CONFIG.minAgeDays
              ? `Too recent to score (${age}d < ${CONFIG.minAgeDays}d maturity gate)`
              : `Too old (${age}d > ${CONFIG.maxAgeDays}d)`,
      multiplier: 0,
      conservative: 0,
    };
  }

  // Smoothed denominator. Without it an account with a median of 5 produces
  // "8x outliers" that are inside its own week-to-week noise.
  const k = CONFIG.smoothing ?? metric.smoothing ?? 0;
  const conservative = value / ((baseline.p75Value || baseline.medianValue) + k);

  return {
    valid: true,
    metric: metric.key,
    value,
    multiplier: value / (baseline.medianValue + k),
    conservative,
    band: band(conservative, metric.key),
  };
}

/**
 * Bands are metric-relative. Engagement multipliers compress, so the same
 * labels on the same numbers would call a genuinely exceptional reel "normal".
 */
const BANDS = {
  views: [[50, 'exceptional', 'peak'], [25, 'major outlier', 'high'], [10, 'outlier', 'high'],
    [5, 'strong', 'mid'], [2, 'interesting', 'low']],
  engagement: [[15, 'exceptional', 'peak'], [8, 'major outlier', 'high'], [4, 'outlier', 'high'],
    [2.5, 'strong', 'mid'], [1.5, 'interesting', 'low']],
};

export function band(m, metricKey = 'engagement') {
  for (const [min, label, tone] of BANDS[metricKey] || BANDS.engagement)
    if (m >= min) return { label, tone };
  return { label: 'normal', tone: 'low' };
}

/* ------------------------------------------------------------------ *
 * The gate
 * ------------------------------------------------------------------ */

/**
 * The multiplier a reel must reach to be worth extracting.
 *
 * In topN mode this is derived from the corpus: the Nth best reel sets the bar,
 * so the shortlist is always exactly as long as the budget allows. `floor`
 * still applies — padding a list with reels at 1.1x their own median would be
 * inventing candidates, not finding them.
 */
export function effectiveGate(outliers) {
  if (CONFIG.gateMode === 'multiplier') {
    return { threshold: CONFIG.gateMultiplier, mode: 'multiplier', eligible: null };
  }
  const ranked = outliers
    .filter((o) => o.valid && o.conservative >= CONFIG.minMultiplier)
    .map((o) => o.conservative)
    .sort((a, b) => b - a);

  const nth = ranked[Math.min(CONFIG.topN, ranked.length) - 1];
  return {
    mode: 'topN',
    threshold: ranked.length ? nth : CONFIG.minMultiplier,
    eligible: ranked.length,
    capped: ranked.length > CONFIG.topN,
  };
}

/* ------------------------------------------------------------------ *
 * §5.4  Attributes + client profile -> scores
 * ------------------------------------------------------------------ */

/** V — virality evidence. Log scale: 40x vs 80x is not twice as interesting. */
export function scoreVirality(conservativeMultiplier, metricKey = 'engagement') {
  if (conservativeMultiplier <= 1) return 0;
  // The ceiling scales with the metric for the same reason the bands do.
  const ceiling = metricKey === 'views' ? CONFIG.viralityCeiling : Math.sqrt(CONFIG.viralityCeiling * 3);
  return clamp(0, 1, Math.log10(conservativeMultiplier) / Math.log10(ceiling));
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

export function hardFilters(attrs, client) {
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

export const FLAG_LABELS = {
  pinned: 'Pinned to the profile',
  sponsored: 'Paid partnership',
  not_a_reel: 'Not a reel',
  no_plays: 'No play count',
  no_metrics: 'No likes or comments returned',
  likes_hidden: 'Account hides like counts',
  not_on_grid: 'Not on the profile grid',
};

export function scoreConcept(post, creator, client, opts = {}) {
  const metric = opts.metric || METRICS.engagement;
  const threshold = opts.threshold ?? CONFIG.gateMultiplier;

  const excluded = isExcluded(post);
  if (excluded.length) {
    return {
      post, creator, client, scorerVersion: SCORER_VERSION, metric: metric.key,
      baseline: { medianValue: 0, nPosts: 0, valid: false },
      outlier: { valid: false, multiplier: 0, conservative: 0 },
      stage: 'excluded',
      dropReasons: excluded.map((f) => FLAG_LABELS[f] || f),
      opportunity: 0,
    };
  }

  const baseline = opts.baseline || computeBaseline(creator, post.mediaType, post.id, metric);
  const outlier = opts.outlier || detectOutlier(post, baseline, metric);
  const base = { post, creator, client, baseline, outlier, metric: metric.key, scorerVersion: SCORER_VERSION };

  if (!outlier.valid) return { ...base, stage: 'rejected', dropReasons: [outlier.reason], opportunity: 0 };

  if (outlier.conservative < threshold)
    return {
      ...base,
      stage: 'below_gate',
      dropReasons: [
        `${outlier.conservative.toFixed(1)}× is below the ${threshold.toFixed(1)}× shortlist cut`,
      ],
      opportunity: 0,
    };

  // A reel can clear the gate but not yet have been through Gemini. That is a
  // pipeline state, not a rejection.
  if (!post.attributes)
    return {
      ...base,
      stage: 'unanalysed',
      dropReasons: [`Shortlisted at ${outlier.conservative.toFixed(1)}× — not yet analysed`],
      opportunity: 0,
    };

  const attrs = post.attributes;
  const V = scoreVirality(outlier.conservative, metric.key);
  const R = scoreReplicability(attrs, client);
  const F = scoreFit(attrs, client);
  const T = scoreTone(attrs, client);
  const dropReasons = hardFilters(attrs, client);

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

/**
 * Scores a whole corpus in one pass.
 *
 * Two-phase because the gate is now a property of the corpus rather than of a
 * post: every baseline and multiplier is computed first, the shortlist cut is
 * derived from the resulting distribution, and only then is each post judged
 * against it.
 */
export function scoreAll(posts, creators, client) {
  const metric = resolveMetric(posts);
  const byId = Object.fromEntries(creators.map((c) => [c.id, c]));

  const pre = posts.map((p) => {
    const creator = byId[p.creatorId] || { id: p.creatorId, history: [] };
    if (isExcluded(p).length) return { post: p, creator, baseline: null, outlier: { valid: false } };
    const baseline = computeBaseline(creator, p.mediaType, p.id, metric);
    return { post: p, creator, baseline, outlier: detectOutlier(p, baseline, metric) };
  });

  const gate = effectiveGate(pre.map((x) => x.outlier));

  const results = pre
    .map((x) =>
      scoreConcept(x.post, x.creator, client, {
        metric,
        threshold: gate.threshold,
        baseline: x.baseline,
        outlier: x.outlier,
      }),
    )
    .sort((a, b) => b.opportunity - a.opportunity || b.outlier.conservative - a.outlier.conservative);

  results.gate = gate;
  results.metric = metric;
  return results;
}

/* ------------------------------------------------------------------ *
 * Hitting the target count
 * ------------------------------------------------------------------ */

/**
 * Answers the only question that matters: are there six concepts, and if not,
 * what exactly is standing between us and six?
 *
 * It reports rather than silently loosening. A shortlist padded by quietly
 * dropping the client's constraints is worse than a short one, because the
 * concepts on it cannot actually be filmed.
 */
export function targetReport(results, target = 6) {
  const by = (s) => results.filter((r) => r.stage === s);
  const scored = by('scored');
  const shortfall = Math.max(0, target - scored.length);

  const blockers = [];
  if (shortfall) {
    const filtered = by('filtered');
    const unanalysed = by('unanalysed');
    const rejected = by('rejected');

    if (unanalysed.length)
      blockers.push({
        kind: 'unanalysed',
        n: unanalysed.length,
        fix: `${unanalysed.length} shortlisted reels have not been analysed yet — run Analyse.`,
      });

    if (filtered.length) {
      const tally = {};
      for (const r of filtered) for (const d of r.dropReasons) tally[d] = (tally[d] || 0) + 1;
      const top = Object.entries(tally).sort((a, b) => b[1] - a[1]).slice(0, 3);
      blockers.push({
        kind: 'client_constraints',
        n: filtered.length,
        detail: top.map(([d, n]) => `${n}× ${d}`),
        fix: 'These clear the data gate but fail this client\'s constraints. Relax a constraint on the client bar, or widen the source list.',
      });
    }

    const noBaseline = rejected.filter((r) => /Baseline unusable/.test(r.dropReasons[0] || '')).length;
    if (noBaseline)
      blockers.push({
        kind: 'baselines',
        n: noBaseline,
        fix: `${noBaseline} reels sit on accounts without a usable baseline — pull more reels per account (depth matters more than more accounts).`,
      });

    if (!blockers.length)
      blockers.push({ kind: 'corpus', n: 0, fix: 'Not enough reels in the corpus. Add more source accounts.' });
  }

  return { target, have: scored.length, shortfall, blockers, met: shortfall === 0 };
}
