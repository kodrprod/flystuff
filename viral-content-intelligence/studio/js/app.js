import { CLIENTS, CREATORS, POSTS, TONE_LABELS } from './data.js';
import { CONFIG, SCORER_VERSION, scoreAll, labelSpace, FLAG_LABELS } from './scoring.js';
import {
  resolveClients, saveClient, deleteClient, isCustomClient, hasOverride, resetClient,
  getOutcome, setOutcome, outcomeSummary, getUI, setUI,
} from './store.js';

const SHORTLIST_SIZE = 6;
const DEFAULTS = JSON.parse(JSON.stringify({
  weights: CONFIG.weights, gate: CONFIG.gateMultiplier, exclude: CONFIG.exclude,
  gateMode: CONFIG.gateMode, topN: CONFIG.topN, minMultiplier: CONFIG.minMultiplier,
  minAgeDays: CONFIG.minAgeDays, maxAgeDays: CONFIG.maxAgeDays,
  minBaselinePosts: CONFIG.minBaselinePosts, minBaselineValue: CONFIG.minBaselineValue,
}));

/**
 * Post-hoc filters over the whole dataset, applied after scoring.
 *
 * Separate from CONFIG on purpose: CONFIG changes what the scorer *believes*
 * and re-ranks everything, whereas these only change what you are looking at.
 * Narrowing to "comedy, under 3 people" should never silently move an
 * opportunity score.
 */
const BLANK_FILTERS = () => ({
  q: '',
  creators: new Set(),
  tones: new Set(),
  formats: new Set(),
  stages: new Set(),
  minMultiplier: 0,
  maxAgeDays: 0,
  maxPeople: 0,
  analysedOnly: false,
  shortlistOnly: false,
});

const SPACES = ['counter', 'small_kitchen', 'full_kitchen', 'dining_room', 'shared_seating', 'outdoor', 'street', 'multi_location'];
const EQUIPMENT = ['phone', 'tripod', 'gimbal', 'light', 'second_camera', 'drone'];
const TONES = Object.keys(TONE_LABELS);

const SAVED = getUI();

const state = {
  clients: resolveClients(CLIENTS),
  clientId: SAVED.clientId || CLIENTS[0].id,
  view: 'feed',
  results: [],
  selectedId: null,
  editing: null,
  // Seeded corpus until the server answers; then whatever has actually been
  // scraped for the active client.
  corpus: { posts: POSTS, creators: CREATORS, live: false },
  status: null,
  filters: BLANK_FILTERS(),
  gateInfo: null,
  estimates: {},
  wiz: {
    query: SAVED.wizQuery || '',
    candidates: null,
    restaurant: SAVED.wizRestaurant || null,
    accounts: SAVED.wizAccounts || null,
    selected: new Set(SAVED.wizSelected || []),
    busy: '',
    log: [],
  },
};

/** Anything that must outlive a reload. */
function persistUI() {
  setUI({
    clientId: state.clientId,
    wizQuery: state.wiz.query,
    wizRestaurant: state.wiz.restaurant,
    wizAccounts: state.wiz.accounts,
    wizSelected: [...state.wiz.selected],
  });
}

/* ---------------- API ---------------- */

const api = async (path, body) => {
  const res = await fetch(path, body
    ? { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) }
    : undefined);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `${res.status}`);
  return data;
};

/** Poll a background job to completion, streaming its log into the wizard. */
async function followJob(jobId, onTick) {
  setUI({ activeJob: jobId });
  try {
    return await pollJob(jobId, onTick);
  } finally {
    setUI({ activeJob: null });
  }
}

async function pollJob(jobId, onTick) {
  for (;;) {
    const job = await api(`/api/job/${jobId}`);
    state.wiz.log = job.log;
    onTick?.(job);
    if (job.status === 'done') return job.result;
    if (job.status === 'error') throw new Error(job.error);
    await new Promise((r) => setTimeout(r, 900));
  }
}

/** Re-attach to a job that was still running when the page was reloaded. */
async function resumeJob() {
  const id = getUI().activeJob;
  if (!id) return;
  try {
    const job = await api(`/api/job/${id}`);
    if (job.status !== 'running') return setUI({ activeJob: null });
    state.wiz.busy = job.label || 'running';
    state.view = 'sources';
    setView('sources');
    await followJob(id, renderSources);
  } catch {
    setUI({ activeJob: null });
  } finally {
    state.wiz.busy = '';
    await refreshStatus();
    await loadCorpus();
    renderAll();
  }
}

async function loadCorpus() {
  if (!state.status?.keys) return;
  try {
    const { posts, creators } = await api(`/api/corpus?clientId=${encodeURIComponent(state.clientId)}`);
    // Fall back to the seeded demo set rather than showing an empty app.
    state.corpus = posts.length ? { posts, creators, live: true } : { posts: POSTS, creators: CREATORS, live: false };
  } catch {
    state.corpus = { posts: POSTS, creators: CREATORS, live: false };
  }
}

const $ = (id) => document.getElementById(id);
const client = () => state.clients.find((c) => c.id === state.clientId) || state.clients[0];

const fmt = (n) =>
  n >= 1e6 ? `${(n / 1e6).toFixed(n >= 1e7 ? 0 : 1)}M` : n >= 1e3 ? `${(n / 1e3).toFixed(0)}K` : `${n}`;
const esc = (s) =>
  String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const pct = (x) => `${Math.round(x * 100)}%`;
const titleCase = (s) => String(s).replace(/_/g, ' ');

/* ------------------------------------------------------------------ *
 * Scoring pass
 * ------------------------------------------------------------------ */

const STAGE_ORDER = { scored: 0, unanalysed: 1, filtered: 2, below_gate: 3, rejected: 4, excluded: 5 };

function recompute() {
  const c = client();
  const results = scoreAll(state.corpus.posts, state.corpus.creators, c);
  state.gateInfo = results.gate;
  state.metric = results.metric;

  results.sort((a, b) => {
    const s = STAGE_ORDER[a.stage] - STAGE_ORDER[b.stage];
    if (s !== 0) return s;
    if (a.stage === 'scored') return b.opportunity - a.opportunity;
    return (b.outlier.conservative || 0) - (a.outlier.conservative || 0);
  });

  results.forEach((r, i) => {
    r.rank = r.stage === 'scored' ? i + 1 : null;
    r.shortlisted = r.stage === 'scored' && i < SHORTLIST_SIZE;
    r.outcome = getOutcome(c.id, r.post.id);
  });

  state.results = results;
  state.visible = applyFilters(results);

  // Keep the selection if it survived the filter; otherwise fall to the top of
  // what is actually on screen, so the detail panel never shows a hidden reel.
  if (!state.visible.find((r) => r.post.id === state.selectedId)) {
    state.selectedId = state.visible[0]?.post.id ?? null;
  }
  document.documentElement.style.setProperty('--tab-hue', c.accent);
  document.documentElement.style.setProperty('--accent', c.accent);
}

/**
 * The cross-dataset filter pass.
 *
 * Runs over every result regardless of stage, because the useful question after
 * a step is usually about the reels that did *not* make it — "show me
 * everything that failed only on space", "what did @x post that scored at all".
 */
function applyFilters(results) {
  const f = state.filters;
  const q = f.q.trim().toLowerCase();

  return results.filter((r) => {
    const p = r.post;
    const a = p.attributes;

    if (f.shortlistOnly && !r.shortlisted) return false;
    if (f.analysedOnly && !a) return false;
    if (f.stages.size && !f.stages.has(r.stage)) return false;
    if (f.creators.size && !f.creators.has(p.creatorId)) return false;
    if (f.minMultiplier && (r.outlier.conservative || 0) < f.minMultiplier) return false;
    if (f.maxAgeDays && p.ageDays > f.maxAgeDays) return false;

    // Attribute filters only bite once a reel has been analysed; applying them
    // to unanalysed reels would hide the very things waiting to be analysed.
    if (a) {
      if (f.tones.size && !f.tones.has(a.tone) && !f.tones.has(a.secondaryTone)) return false;
      if (f.formats.size && !f.formats.has(a.format)) return false;
      if (f.maxPeople && (a.peopleOnCamera || 0) > f.maxPeople) return false;
    } else if (f.tones.size || f.formats.size || f.maxPeople) {
      return false;
    }

    if (q) {
      const hay = [
        p.caption, p.creatorId, p.transcript, r.mechanism, p.mechanism,
        ...(p.hashtags || []), a?.tone, a?.format, a?.hookType,
      ].filter(Boolean).join(' ').toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
}

const filtersActive = () => {
  const f = state.filters;
  return !!(f.q || f.creators.size || f.tones.size || f.formats.size || f.stages.size ||
    f.minMultiplier || f.maxAgeDays || f.maxPeople || f.analysedOnly || f.shortlistOnly);
};

/* ------------------------------------------------------------------ *
 * Header / client bar / funnel
 * ------------------------------------------------------------------ */

function renderClientSwitch() {
  $('clientSwitch').innerHTML =
    state.clients
      .map(
        (c) => `
    <button class="client-tab ${c.id === state.clientId ? 'is-active' : ''}"
            style="--tab-hue:${c.accent}" data-client="${c.id}" role="tab">
      <strong>${esc(c.name)}</strong>
      <span>${esc(c.cuisine)} · ${esc(c.city)}</span>
    </button>`,
      )
      .join('') + `<button class="client-tab add" data-newclient="1" title="Add a client">+</button>`;
}

function renderClientBar() {
  const c = client();
  const cap = c.capability;
  const s = outcomeSummary(c.id, cap.ownBaselineViews);

  const chips = [
    `${cap.staffCount} staff · ${cap.staffAvailableForFilming} free to film`,
    `€${cap.monthlyBudgetEur}/mo · €${Math.round(cap.monthlyBudgetEur / 6)} per concept`,
    `${cap.staffMinutesPerConcept} min per concept`,
    `kit: ${cap.equipment.join(', ')}`,
    `chef on camera: ${cap.chefOnCamera}`,
    `their baseline: ${fmt(cap.ownBaselineViews || 0)} views`,
  ]
    .map((t) => `<span class="chip">${esc(t)}</span>`)
    .join('');

  const yesno = [
    `<span class="chip ${cap.customersOnCamera ? 'yes' : 'no'}">guests on camera: ${cap.customersOnCamera ? 'ok' : 'not allowed'}</span>`,
    ...cap.spaces.map((x) => `<span class="chip yes">${esc(labelSpace(x))}</span>`),
    ...(cap.avoidTones || []).map((t) => `<span class="chip no">avoids ${esc(TONE_LABELS[t] || t)}</span>`),
  ].join('');

  const outcome =
    s.filmed || s.published
      ? `<span class="chip out">logged: ${s.filmed} filmed (${s.published} published)${s.medianRatio ? ` · median ${s.medianRatio.toFixed(1)}× their baseline` : ''}</span>`
      : `<span class="chip">no outcomes logged yet</span>`;

  $('clientBar').innerHTML = `
    <div class="cb-brief">
      <b>Brief.</b> ${esc(c.brief)}
      <div class="cb-actions">
        <button class="mini-btn" data-capstoggle="1" aria-expanded="${state.capsOpen ? 'true' : 'false'}">
          ${state.capsOpen ? 'Hide sliders' : 'Adjust capability'}
        </button>
        <button class="mini-btn" data-editclient="${c.id}">Edit profile</button>
        ${hasOverride(c.id) ? `<button class="mini-btn" data-resetclient="${c.id}">Revert to seeded</button>` : ''}
        ${isCustomClient(c.id) ? `<button class="mini-btn danger" data-deleteclient="${c.id}">Delete</button>` : ''}
        <button class="mini-btn" data-export="1">Export shoot list</button>
      </div>
    </div>
    <div class="cb-caps">${chips}${yesno}${outcome}</div>
    ${state.capsOpen ? capSlidersHTML(c) : ''}`;
}

/**
 * Sliders for the capability numbers the chips above only display.
 *
 * These are the inputs to F (client fit) and to the hard filters, so moving one
 * re-ranks the whole shortlist live — which is the point. The per-concept
 * budget is derived rather than editable because it is defined as the monthly
 * budget over the six concepts the system is built to deliver.
 */
function capSlidersHTML(c) {
  const cap = c.capability;
  const row = (key, label, min, max, step, value, suffix, note) => `
    <label class="cap-row">
      <span class="cap-name">${esc(label)}</span>
      <input type="range" min="${min}" max="${max}" step="${step}" value="${value}" data-cap="${key}" />
      <output class="cap-val">${esc(String(value))}${esc(suffix || '')}</output>
      ${note ? `<em class="cap-note">${esc(note)}</em>` : ''}
    </label>`;

  const chefOrder = ['no', 'low', 'medium', 'high'];

  return `
    <div class="cap-sliders">
      ${row('staffCount', 'Staff, total', 1, 30, 1, cap.staffCount, '')}
      ${row('staffAvailableForFilming', 'Free to film', 0, 12, 1, cap.staffAvailableForFilming, '',
        cap.staffAvailableForFilming > cap.staffCount ? 'more than total staff' : '')}
      ${row('staffMinutesPerConcept', 'Minutes per concept', 5, 240, 5, cap.staffMinutesPerConcept, ' min')}
      ${row('monthlyBudgetEur', 'Monthly budget', 0, 2000, 25, cap.monthlyBudgetEur, ' €',
        `≈ €${Math.round(cap.monthlyBudgetEur / SHORTLIST_SIZE)} per concept ceiling`)}
      ${row('ownBaselineViews', 'Their own baseline', 0, 200000, 500, cap.ownBaselineViews || 0, ' views',
        'only used to grade outcomes you log')}
      <label class="cap-row">
        <span class="cap-name">Chef on camera</span>
        <input type="range" min="0" max="3" step="1" value="${chefOrder.indexOf(cap.chefOnCamera)}" data-cap="chefOnCamera" />
        <output class="cap-val">${esc(cap.chefOnCamera)}</output>
      </label>
      <label class="cap-row toggle">
        <span class="cap-name">Guests on camera</span>
        <input type="checkbox" data-cap="customersOnCamera" ${cap.customersOnCamera ? 'checked' : ''} />
        <output class="cap-val">${cap.customersOnCamera ? 'allowed' : 'not allowed'}</output>
      </label>
      <p class="cap-hint">
        Changes save to this client immediately and re-rank the shortlist.
        ${hasOverride(c.id) ? 'Use “Revert to seeded” to undo.' : ''}
      </p>
    </div>`;
}

/**
 * The funnel doubles as the "why don't I have six" explanation, so each stage is
 * clickable and filters the dataset down to exactly the reels it counts.
 */
function renderFunnel() {
  const r = state.results;
  const mature = r.filter((x) => x.outlier.valid).length;
  const gated = r.filter((x) => x.stage !== 'rejected' && x.stage !== 'below_gate' && x.stage !== 'excluded').length;
  const scored = r.filter((x) => x.stage === 'scored').length;
  const cut = state.gateInfo?.threshold;

  const stages = [
    [state.corpus.posts.length, 'held', '', null],
    [mature, `scoreable ${state.metric?.short || ''}`.trim(), '', null],
    [gated, cut ? `shortlist ≥${cut.toFixed(1)}×` : 'shortlist', '', 'unanalysed'],
    [scored, 'client-viable', scored < SHORTLIST_SIZE ? 'short' : '', 'scored'],
    [Math.min(SHORTLIST_SIZE, scored), `top ${SHORTLIST_SIZE}`, 'shortlist', 'shortlist'],
  ];

  $('funnel').innerHTML = stages
    .map(([n, label, cls, filter]) =>
      `<div class="fstage ${cls}" ${filter ? `data-funnel="${filter}" role="button" tabindex="0"` : ''}>
         <b>${n}</b><span>${esc(label)}</span>
       </div>`)
    .join('') +
    (scored < SHORTLIST_SIZE
      ? `<div class="fstage warn" data-shortfall="1" role="button" tabindex="0">
           <b>${SHORTLIST_SIZE - scored}</b><span>short of ${SHORTLIST_SIZE} — why?</span>
         </div>`
      : '');
}

/* ------------------------------------------------------------------ *
 * Cross-dataset filter bar
 * ------------------------------------------------------------------ */

const STAGE_LABELS = {
  scored: 'client-viable',
  unanalysed: 'shortlisted, not analysed',
  filtered: 'failed client constraints',
  below_gate: 'below shortlist cut',
  rejected: 'no usable baseline',
  excluded: 'excluded at ingest',
};

function renderFilterBar() {
  const el = $('filterBar');
  if (!el) return;
  const f = state.filters;
  const all = state.results;
  const shown = state.visible.length;

  const counts = {};
  for (const r of all) counts[r.stage] = (counts[r.stage] || 0) + 1;

  const creators = [...new Set(all.map((r) => r.post.creatorId))].sort();
  const tones = [...new Set(all.map((r) => r.post.attributes?.tone).filter(Boolean))].sort();
  const formats = [...new Set(all.map((r) => r.post.attributes?.format).filter(Boolean))].sort();

  const pills = (items, set, key, label) =>
    items.length
      ? `<div class="fb-group"><span class="fb-label">${label}</span>${items
          .map((v) => `<button class="fb-pill ${set.has(v) ? 'on' : ''}" data-filter="${key}" data-value="${esc(v)}">
              ${esc(titleCase(v))}${counts[v] != null ? ` <i>${counts[v]}</i>` : ''}</button>`)
          .join('')}</div>`
      : '';

  el.innerHTML = `
    <div class="fb-row">
      <input class="fb-search" id="fbSearch" type="search" placeholder="Search captions, transcripts, mechanisms, hashtags…"
             value="${esc(f.q)}" />
      <span class="fb-count ${shown < all.length ? 'on' : ''}">${shown} of ${all.length}</span>
      ${filtersActive() ? `<button class="mini-btn" data-clearfilters="1">Clear filters</button>` : ''}
    </div>

    <div class="fb-row wrap">
      ${pills(Object.keys(STAGE_LABELS).filter((s) => counts[s]).map((s) => s), f.stages, 'stages', 'Stage')}
    </div>

    <div class="fb-row wrap">
      <div class="fb-group">
        <span class="fb-label">Min multiplier</span>
        <input type="range" min="0" max="10" step="0.5" value="${f.minMultiplier}" data-filter="minMultiplier" />
        <output>${f.minMultiplier ? `${f.minMultiplier}×` : 'any'}</output>
      </div>
      <div class="fb-group">
        <span class="fb-label">Max age</span>
        <input type="range" min="0" max="180" step="5" value="${f.maxAgeDays}" data-filter="maxAgeDays" />
        <output>${f.maxAgeDays ? `${f.maxAgeDays}d` : 'any'}</output>
      </div>
      <div class="fb-group">
        <span class="fb-label">Max cast</span>
        <input type="range" min="0" max="8" step="1" value="${f.maxPeople}" data-filter="maxPeople" />
        <output>${f.maxPeople || 'any'}</output>
      </div>
      <label class="fb-check"><input type="checkbox" data-filter="analysedOnly" ${f.analysedOnly ? 'checked' : ''} /> analysed only</label>
      <label class="fb-check"><input type="checkbox" data-filter="shortlistOnly" ${f.shortlistOnly ? 'checked' : ''} /> shortlist only</label>
    </div>

    <details class="fb-more" ${f.creators.size || f.tones.size || f.formats.size ? 'open' : ''}>
      <summary>Filter by account, tone, format</summary>
      ${pills(creators, f.creators, 'creators', 'Account')}
      ${pills(tones, f.tones, 'tones', 'Tone')}
      ${pills(formats, f.formats, 'formats', 'Format')}
    </details>`;

  // Stage pills carry their own labels; patch them in after the generic render.
  el.querySelectorAll('[data-filter="stages"]').forEach((b) => {
    const s = b.dataset.value;
    b.innerHTML = `${esc(STAGE_LABELS[s] || s)} <i>${counts[s] || 0}</i>`;
    b.classList.toggle('on', f.stages.has(s));
  });
}

/* ------------------------------------------------------------------ *
 * Media
 * ------------------------------------------------------------------ */

function mediaHTML(res) {
  const p = res.post;
  const dropped = res.stage !== 'scored';
  const badge = res.shortlisted
    ? `<div class="badge-rank">SHORTLIST #${res.rank}</div>`
    : dropped
      ? `<div class="badge-drop">${esc(dropLabel(res))}</div>`
      : '';

  const inner = p.videoUrl
    ? `<video src="${esc(p.videoUrl)}" muted loop playsinline preload="metadata"></video>`
    : `<div class="poster" style="--ph:${p.poster.hue}">${p.poster.glyph}</div>`;

  const flag =
    res.outcome?.status === 'published'
      ? '<div class="badge-out published">PUBLISHED</div>'
      : res.outcome?.status === 'filmed'
        ? '<div class="badge-out filmed">FILMED</div>'
        : '';

  const m = res.outlier.valid ? res.outlier.conservative : 0;
  const tone = res.outlier.valid ? res.outlier.band.tone : 'low';
  return { inner, badge, flag, m, tone, dropped };
}

function dropLabel(res) {
  if (res.stage === 'rejected') return 'OUT OF WINDOW';
  if (res.stage === 'below_gate') return 'BELOW GATE';
  if (res.stage === 'unanalysed') return 'NEEDS ANALYSIS';
  if (res.stage === 'excluded') return 'FILTERED OUT';
  return 'FILTERED';
}

/* ------------------------------------------------------------------ *
 * Feed
 * ------------------------------------------------------------------ */

/** Shown when filters hide everything — silence reads as a broken app. */
function emptyStateHTML() {
  return `<div class="empty-state">
    <b>Nothing matches these filters.</b>
    <p>${state.results.length} reels are loaded; the current filters hide all of them.</p>
    <button class="mini-btn" data-clearfilters="1">Clear filters</button>
  </div>`;
}

function renderFeed() {
  if (!state.visible.length) { $('feed').innerHTML = emptyStateHTML(); return; }
  $('feed').innerHTML = state.visible
    .map((res) => {
      const p = res.post;
      const { inner, badge, flag, m, tone, dropped } = mediaHTML(res);
      const dots = (p.timeline || [])
        .map(
          (t, i) =>
            `<div class="scrub-dot" style="left:${(t.t / p.durationS) * 100}%" data-post="${p.id}" data-i="${i}" title="${esc(t.label)}"></div>`,
        )
        .join('');

      return `
      <section class="slide" data-post="${p.id}">
        <div class="phone ${dropped ? 'is-dropped' : ''}" data-open="${p.id}">
          ${inner}${badge}${flag}
          <div class="ph-top">
            <span class="handle">@${esc(res.creator.handle)}</span>
            <span class="mult ${tone}">${m ? `${m.toFixed(1)}×` : '—'}</span>
          </div>
          <div class="scrub">
            <div class="scrub-track">${dots}</div>
            <div class="scrub-label" data-label="${p.id}">${esc(p.timeline?.[0]?.label || '')}</div>
          </div>
          <div class="ph-bot">
            <div class="ph-cap">${esc(p.caption)}</div>
            <div class="ph-stats">
              <span>▶ ${fmt(p.views)}</span><span>♥ ${fmt(p.likes)}</span>
              <span>💬 ${fmt(p.comments)}</span><span>${p.durationS}s</span>
            </div>
          </div>
        </div>
      </section>`;
    })
    .join('');
  observeSlides();
}

let observer;
function observeSlides() {
  observer?.disconnect();
  observer = new IntersectionObserver(
    (entries) => {
      const best = entries.filter((e) => e.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (best) {
        state.selectedId = best.target.dataset.post;
        renderPanel();
      }
    },
    { root: $('feed'), threshold: [0.5, 0.75] },
  );
  document.querySelectorAll('.slide').forEach((el) => observer.observe(el));
}

/* ------------------------------------------------------------------ *
 * Gallery
 * ------------------------------------------------------------------ */

function renderGallery() {
  if (!state.visible.length) { $('gallery').innerHTML = emptyStateHTML(); return; }
  $('gallery').innerHTML = state.visible
    .map((res) => {
      const p = res.post;
      const { inner, badge, flag, m, tone, dropped } = mediaHTML(res);
      const scoreLine = dropped
        ? `<span class="drop">${esc(dropLabel(res))}</span>`
        : `<span class="op">${res.opportunity.toFixed(1)}</span>`;

      const mini = dropped
        ? ''
        : `<div class="tile-mini">
             ${[[res.V, '#60a5fa'], [res.R.score, '#4ade80'], [res.F.score, '#fbbf24'], [res.T.score, '#c084fc']]
               .map(([v, col]) => `<i><b style="width:${pct(v)};background:${col}"></b></i>`)
               .join('')}
           </div>`;

      return `
      <button class="tile" data-open="${p.id}">
        <div class="tile-media ${dropped ? 'is-dropped' : ''}">
          ${inner}${badge}${flag}
          <div class="ph-top"><span class="handle">@${esc(res.creator.handle)}</span>
            <span class="mult ${tone}">${m ? `${m.toFixed(1)}×` : '—'}</span></div>
        </div>
        <div class="tile-stats">
          <div class="tile-title">${esc(p.caption)}</div>
          <div class="tile-line">
            ${scoreLine}
            <span>▶ ${fmt(p.views)}</span>
            ${p.attributes ? `<span>${esc(TONE_LABELS[p.attributes.tone] || p.attributes.tone)}</span>
            <span>€${p.attributes.propsCostEur} · ${p.attributes.staffMinutes}m</span>` : '<span>not analysed</span>'}
          </div>
          ${mini}
        </div>
      </button>`;
    })
    .join('');
}

/* ------------------------------------------------------------------ *
 * Detail
 * ------------------------------------------------------------------ */

function outcomeHTML(res) {
  const o = res.outcome || { status: 'none', views: null };
  const btn = (v, label) =>
    `<button class="out-btn ${o.status === v ? 'on' : ''}" data-outcome="${res.post.id}" data-status="${v}">${label}</button>`;

  const ratio =
    o.status === 'published' && o.views > 0
      ? (o.views / (res.client.capability.ownBaselineViews || 1)).toFixed(1)
      : null;

  return `
    <div class="sec">
      <h4>Outcome</h4>
      <div class="out-row">${btn('none', 'Not picked')}${btn('shortlisted', 'Picked')}${btn('filmed', 'Filmed')}${btn('published', 'Published')}</div>
      ${
        o.status === 'published'
          ? `<div class="out-views">
               <label>Views after 7 days
                 <input type="number" min="0" step="1" value="${o.views ?? ''}" data-outviews="${res.post.id}" placeholder="e.g. 8400" />
               </label>
               <!-- Always present, even when empty: the input handler fills it in
                    place, and re-rendering the panel on each keystroke would
                    steal focus mid-typing. -->
               <span class="out-ratio ${ratio ? (+ratio >= 2 ? 'good' : +ratio >= 1 ? 'mid' : 'bad') : ''}">${
                 ratio ? `${ratio}× their baseline (${fmt(res.client.capability.ownBaselineViews)})` : ''
               }</span>
             </div>`
          : ''
      }
      <p class="hint">Logged locally. This is the only input that can ever calibrate the weights — see PLAN.md §5.5.</p>
    </div>`;
}

function renderDetail(res) {
  if (!res) return '<div class="empty">Nothing selected.</div>';
  const p = res.post;
  const a = p.attributes;
  const c = res.client;
  const adaptation = p.adaptations?.[c.id];

  const head = `
    <h2 class="p-title">${esc(p.caption)}</h2>
    <div class="p-sub">@${esc(res.creator.handle)} · ${p.durationS}s · ${p.ageDays}d old · baseline ${fmt(res.baseline.medianViews)} (n=${res.baseline.nPosts})</div>`;

  if (res.stage !== 'scored') {
    return `${head}
      <div class="sec" style="border-top:0;padding-top:0;margin-top:0">
        <h4>Why it is not on the list</h4>
        <div class="drops"><ul class="ul">${res.dropReasons.map((d) => `<li>${esc(d)}</li>`).join('')}</ul></div>
      </div>
      ${p.mechanism ? `<div class="sec"><h4>Mechanism (recorded anyway)</h4><p>${esc(p.mechanism)}</p></div>` : ''}
      ${a ? attrsHTML(a) : ''}`;
  }

  const bars = [
    ['V — virality evidence', res.V, '#60a5fa', `${res.outlier.conservative.toFixed(1)}× conservative`],
    ['R — replicability', res.R.score, '#4ade80', `${res.R.penalties.length} penalt${res.R.penalties.length === 1 ? 'y' : 'ies'}`],
    ['F — client fit', res.F.score, '#fbbf24', 'capability match'],
    ['T — tone fit', res.T.score, '#c084fc', TONE_LABELS[res.T.primary] || res.T.primary],
  ];

  return `
    ${head}
    <div class="score-hero">
      <div class="score-num" style="color:hsl(${c.accent} 70% 62%)">${res.opportunity.toFixed(1)}</div>
      <div class="score-meta">
        Opportunity for <b>${esc(c.name)}</b><br />
        ${res.shortlisted ? `<b>Shortlisted</b> — rank ${res.rank} of ${state.results.filter((r) => r.stage === 'scored').length}` : `Rank ${res.rank}, below the top ${SHORTLIST_SIZE}`}
      </div>
    </div>

    <div class="bars">
      ${bars
        .map(
          ([lab, v, col, note]) => `
        <div class="bar-row">
          <div class="bar-lab">${esc(lab)}</div>
          <div class="bar-track"><div class="bar-fill" style="width:${pct(v)};background:${col}"></div></div>
          <div class="bar-val">${v.toFixed(2)}</div>
        </div>
        <div class="bar-row"><div></div><div class="bar-val" style="text-align:left;color:var(--fg-3)">${esc(note)}</div><div></div></div>`,
        )
        .join('')}
    </div>

    <div class="sec">
      <h4>Adaptation for ${esc(c.name)}</h4>
      <div class="adapt">
        ${adaptation ? `<p>${esc(adaptation)}</p>` : `<p class="none">Not generated — Claude only runs on the shortlist, and this one placed below it.</p>`}
      </div>
    </div>

    ${outcomeHTML(res)}

    <div class="sec"><h4>Why the original worked</h4><p class="lead">${esc(p.mechanism)}</p></div>

    <div class="sec">
      <h4>Essential — must survive the adaptation</h4>
      <ul class="ul essential">${p.essentialElements.map((e) => `<li>${esc(e)}</li>`).join('')}</ul>
    </div>

    <div class="sec">
      <h4>Incidental — safe to change</h4>
      <ul class="ul incidental">${p.incidentalElements.map((e) => `<li>${esc(e)}</li>`).join('')}</ul>
    </div>

    ${
      res.R.penalties.length
        ? `<div class="sec"><h4>Replicability penalties</h4>
           <ul class="ul penalty">${res.R.penalties
             .map((x) => `<li><span>${esc(x.label)}</span><span class="amt">−${x.amount.toFixed(2)}</span></li>`)
             .join('')}</ul></div>`
        : `<div class="sec"><h4>Replicability penalties</h4><p>None — this is fully within your means.</p></div>`
    }

    <div class="sec">
      <h4>Client-fit breakdown</h4>
      ${res.F.parts
        .map((x) => {
          const cls = x.score >= 0.85 ? 'ok' : x.score >= 0.5 ? 'mid' : 'no';
          return `<div class="fit-row"><span class="l">${esc(x.label)}<br /><span style="color:var(--fg-3);font-size:10.5px">${esc(x.note)}</span></span><span class="r ${cls}">${pct(x.score)}</span></div>`;
        })
        .join('')}
    </div>

    <div class="sec">
      <h4>Production</h4>
      <p>Roughly <b>€${a.propsCostEur}</b> in props and <b>${a.staffMinutes} minutes</b> of staff time. Needs ${esc(labelSpace(a.spaceRequired))}, ${a.peopleOnCamera} on camera, kit: ${esc(a.equipment.join(', '))}.</p>
    </div>

    ${p.transcript ? `<div class="sec"><h4>Transcript</h4><p>${esc(p.transcript)}</p></div>` : ''}
    ${attrsHTML(a)}`;
}

function attrsHTML(a) {
  const rows = [
    ['Hook', a.hookType], ['Format', a.format], ['Tone', TONE_LABELS[a.tone] || a.tone],
    ['Edit', a.editComplexity], ['Audio', a.audioDependency],
    ['Cuts', `${a.cuts} · avg ${a.avgShotLengthS}s`], ['On camera', a.peopleOnCamera],
    ['Trend half-life', a.trendHalfLifeDays ? `${a.trendHalfLifeDays}d` : 'evergreen'],
  ];
  return `<div class="sec"><h4>Extracted attributes (Gemini)</h4><div class="attr-grid">
    ${rows.map(([k, v]) => `<div class="attr"><b>${esc(k)}</b><span>${esc(v)}</span></div>`).join('')}
  </div></div>`;
}

function renderPanel() {
  $('panel').innerHTML = renderDetail(state.results.find((r) => r.post.id === state.selectedId));
}

/* ------------------------------------------------------------------ *
 * Client editor
 * ------------------------------------------------------------------ */

function blankClient() {
  return {
    id: `c${Date.now().toString(36)}`,
    name: '', cuisine: '', city: '', site: '', accent: 265,
    brief: '',
    capability: {
      spaces: ['counter'], chefOnCamera: 'medium', customersOnCamera: true,
      staffCount: 4, staffAvailableForFilming: 2, staffMinutesPerConcept: 60,
      monthlyBudgetEur: 200, ownBaselineViews: 2000,
      equipment: ['phone'],
      preferredTones: Object.fromEntries(TONES.map((t) => [t, 0.5])),
      avoidTones: [], constraints: [],
    },
  };
}

function openEditor(id) {
  state.editing = id
    ? JSON.parse(JSON.stringify(state.clients.find((c) => c.id === id)))
    : blankClient();
  renderEditor();
  $('editor').hidden = false;
}

function renderEditor() {
  const c = state.editing;
  const cap = c.capability;
  const isNew = !state.clients.some((x) => x.id === c.id);

  const text = (k, label, val, ph = '') =>
    `<label class="fld"><span>${label}</span><input data-f="${k}" value="${esc(val)}" placeholder="${esc(ph)}" /></label>`;
  const num = (k, label, val) =>
    `<label class="fld"><span>${label}</span><input type="number" min="0" data-f="${k}" value="${val}" /></label>`;

  $('editorBody').innerHTML = `
    <div class="grid2">
      ${text('name', 'Name', c.name, 'Bosporus Grill')}
      ${text('cuisine', 'Cuisine', c.cuisine, 'Kebab / Turkish grill')}
      ${text('city', 'City', c.city, 'Dresden')}
      ${text('site', 'Site', c.site, 'Food court, Centrum Galerie')}
    </div>

    <label class="fld"><span>Brief — what they want, and the constraint that shapes it</span>
      <textarea data-f="brief" rows="3" placeholder="Fun and jokes. Counter only, no back room…">${esc(c.brief)}</textarea>
    </label>

    <label class="fld"><span>Accent colour</span>
      <input type="range" min="0" max="359" data-f="accent" value="${c.accent}" style="accent-color:hsl(${c.accent} 70% 55%)" />
    </label>

    <h5>Spaces they actually have</h5>
    <div class="checks">
      ${SPACES.map(
        (s) => `<label class="chk"><input type="checkbox" data-space="${s}" ${cap.spaces.includes(s) ? 'checked' : ''} /> ${esc(labelSpace(s))}</label>`,
      ).join('')}
    </div>

    <h5>Kit</h5>
    <div class="checks">
      ${EQUIPMENT.map(
        (e) => `<label class="chk"><input type="checkbox" data-equip="${e}" ${cap.equipment.includes(e) ? 'checked' : ''} /> ${esc(titleCase(e))}</label>`,
      ).join('')}
    </div>

    <h5>Capacity</h5>
    <div class="grid2">
      ${num('cap.staffCount', 'Staff total', cap.staffCount)}
      ${num('cap.staffAvailableForFilming', 'Free to film', cap.staffAvailableForFilming)}
      ${num('cap.staffMinutesPerConcept', 'Minutes per concept', cap.staffMinutesPerConcept)}
      ${num('cap.monthlyBudgetEur', 'Budget €/month', cap.monthlyBudgetEur)}
      ${num('cap.ownBaselineViews', 'Their own median views', cap.ownBaselineViews)}
      <label class="fld"><span>Chef on camera</span>
        <select data-f="cap.chefOnCamera">
          ${['high', 'medium', 'low', 'no'].map((v) => `<option value="${v}" ${cap.chefOnCamera === v ? 'selected' : ''}>${v}</option>`).join('')}
        </select>
      </label>
    </div>
    <label class="chk"><input type="checkbox" data-f="cap.customersOnCamera" ${cap.customersOnCamera ? 'checked' : ''} /> Guests may appear on camera</label>

    <h5>Tone — what register suits them</h5>
    <div class="tones">
      ${TONES.map((t) => {
        const v = cap.preferredTones[t] ?? 0.5;
        const avoid = (cap.avoidTones || []).includes(t);
        return `<div class="tone-row ${avoid ? 'is-avoid' : ''}">
          <span class="tone-name">${esc(TONE_LABELS[t])}</span>
          <input type="range" min="0" max="1" step="0.05" value="${v}" data-tone="${t}" ${avoid ? 'disabled' : ''} />
          <span class="tone-val">${avoid ? '—' : v.toFixed(2)}</span>
          <label class="chk tiny"><input type="checkbox" data-avoid="${t}" ${avoid ? 'checked' : ''} /> avoid</label>
        </div>`;
      }).join('')}
    </div>

    <div class="editor-actions">
      <button class="primary-btn" data-saveclient="1">${isNew ? 'Add client' : 'Save changes'}</button>
      <button class="mini-btn" data-canceledit="1">Cancel</button>
    </div>`;
}

function applyEditorField(el) {
  const c = state.editing;
  const f = el.dataset.f;
  if (f) {
    const val = el.type === 'checkbox' ? el.checked : el.type === 'number' || el.type === 'range' ? +el.value : el.value;
    if (f.startsWith('cap.')) c.capability[f.slice(4)] = val;
    else c[f] = val;
    if (f === 'accent') {
      el.style.accentColor = `hsl(${val} 70% 55%)`;
      return true; // no full re-render, keeps the slider grabbed
    }
    return false;
  }
  if (el.dataset.space) {
    const s = new Set(c.capability.spaces);
    el.checked ? s.add(el.dataset.space) : s.delete(el.dataset.space);
    c.capability.spaces = [...s];
    return true;
  }
  if (el.dataset.equip) {
    const s = new Set(c.capability.equipment);
    el.checked ? s.add(el.dataset.equip) : s.delete(el.dataset.equip);
    c.capability.equipment = [...s];
    return true;
  }
  if (el.dataset.tone) {
    c.capability.preferredTones[el.dataset.tone] = +el.value;
    el.parentElement.querySelector('.tone-val').textContent = (+el.value).toFixed(2);
    return true;
  }
  if (el.dataset.avoid) {
    const s = new Set(c.capability.avoidTones || []);
    el.checked ? s.add(el.dataset.avoid) : s.delete(el.dataset.avoid);
    c.capability.avoidTones = [...s];
    renderEditor();
    return true;
  }
  return false;
}

/* ------------------------------------------------------------------ *
 * Markdown export — the actual deliverable
 * ------------------------------------------------------------------ */

function exportShootList() {
  const c = client();
  const short = state.results.filter((r) => r.stage === 'scored').slice(0, SHORTLIST_SIZE);
  const date = new Date().toISOString().slice(0, 10);

  const lines = [
    `# Shoot list — ${c.name}`,
    ``,
    `${short.length} concepts · generated ${date} · scorer v${SCORER_VERSION}`,
    `${c.cuisine} · ${c.site} · €${c.capability.monthlyBudgetEur}/month · ${c.capability.staffMinutesPerConcept} min per concept`,
    ``,
    `> Scores order the list; they are not calibrated. Judge the adaptation, not the number.`,
    ``,
  ];

  short.forEach((r, i) => {
    const p = r.post;
    const a = p.attributes;
    lines.push(
      `## ${i + 1}. ${p.caption}`,
      ``,
      `**Opportunity ${r.opportunity.toFixed(1)}** · V ${r.V.toFixed(2)} · R ${r.R.score.toFixed(2)} · F ${r.F.score.toFixed(2)} · T ${r.T.score.toFixed(2)}`,
      ``,
      `**Source** @${r.creator.handle} — ${fmt(p.views)} views, ${r.outlier.conservative.toFixed(1)}× their own baseline · ${p.url}`,
      ``,
      `**Why it worked.** ${p.mechanism}`,
      ``,
      `**Do this.** ${p.adaptations?.[c.id] || '(not generated — below the shortlist when this was exported)'}`,
      ``,
      `**Must keep**`,
      ...p.essentialElements.map((e) => `- ${e}`),
      ``,
      `**Safe to change**`,
      ...p.incidentalElements.map((e) => `- ${e}`),
      ``,
      `**Production.** €${a.propsCostEur} props · ${a.staffMinutes} min · ${labelSpace(a.spaceRequired)} · ${a.peopleOnCamera} on camera · ${a.equipment.join(', ')}`,
      ``,
      `**Filmed?** ☐  **Published?** ☐  **Views after 7 days:** ______ (their baseline: ${fmt(c.capability.ownBaselineViews)})`,
      ``,
      `---`,
      ``,
    );
  });

  const blob = new Blob([lines.join('\n')], { type: 'text/markdown' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `shootlist-${c.id}-${date}.md`;
  a.click();
  URL.revokeObjectURL(a.href);
}


/* ------------------------------------------------------------------ *
 * Cost badges
 * ------------------------------------------------------------------ *
 *
 * Every button that spends anything states the amount and the platform it bills
 * to *before* it is pressed. The estimate comes from the server rather than
 * being recomputed here: a UI that quotes one price while the server charges
 * another is exactly how a €0.71 plan became a €5 bill.
 */

/** Renders from cache, and fetches in the background on a miss. */
function costBadge(action, params) {
  const key = `${action}:${JSON.stringify(params)}`;
  const est = state.estimates[key];

  if (!est) {
    if (state.estimates[key] === undefined) {
      state.estimates[key] = null; // in flight — don't refetch on re-render
      api('/api/estimate', { action, params })
        .then((r) => {
          state.estimates[key] = r;
          document.querySelectorAll(`[data-cost="${CSS.escape(key)}"]`).forEach((el) => {
            el.outerHTML = costBadge(action, params);
          });
        })
        .catch(() => { state.estimates[key] = { items: [], totalUsd: 0, free: true, failed: true }; });
    }
    return `<div class="cost-badge pending" data-cost="${esc(key)}">Estimating cost…</div>`;
  }

  if (est.failed) return `<div class="cost-badge" data-cost="${esc(key)}">Cost estimate unavailable</div>`;

  const lines = est.items
    .map((i) => `<li><span>${esc(i.platform)}</span><b>${i.free ? 'free' : `$${i.usd.toFixed(4)}`}</b>
                 <em>${esc(i.detail)}</em>${i.note ? `<span class="cost-note">${esc(i.note)}</span>` : ''}</li>`)
    .join('');

  return `
    <div class="cost-badge ${est.free ? 'free' : 'paid'}" data-cost="${esc(key)}">
      <div class="cost-head">
        <b>${est.free ? '$0.00 · free' : `≈ $${est.totalUsd.toFixed(4)}`}</b>
        <span>${esc([...new Set(est.items.map((i) => i.platform))].join(' · ') || 'no cost')}</span>
      </div>
      ${lines ? `<ul class="cost-items">${lines}</ul>` : ''}
    </div>`;
}

/* ------------------------------------------------------------------ *
 * Sources — restaurant lookup, similar accounts, fetch, analyse
 * ------------------------------------------------------------------ */

function renderSources() {
  const w = state.wiz;
  const c = client();
  const st = state.status;

  if (!st) {
    $('sources').innerHTML = `<div class="src-wrap"><div class="src-card">
      <h3>Offline</h3>
      <p class="src-p">No API server on this origin, so the app is running on the seeded demo corpus.
      Start it with <code>npm start</code> from <code>studio/</code> to enable discovery and scraping.</p>
    </div></div>`;
    return;
  }

  const k = st.keys;
  const keyRow = (ok, name, what, issue) =>
    `<div class="key-row"><span class="dot ${ok ? 'ok' : 'no'}"></span><b>${name}</b>` +
    `<span${ok ? '' : ' class="key-bad"'}>${esc(ok ? what : issue || what)}</span></div>`;

  const searcher = st.models?.reasoner === 'claude' && k.anthropic ? 'Claude' : 'Gemini';

  const step1 = `
    <div class="src-card">
      <h3>1 · Find the restaurant</h3>
      <p class="src-p">Type the name. ${searcher} searches the web and comes back with candidates so you can
      confirm which one you mean before anything gets fetched.</p>
      ${costBadge('discover', { accounts: 1 })}
      <div class="src-row">
        <input id="wizQuery" placeholder="e.g. Sen Vietnamese Dresden" value="${esc(w.query)}" />
        <button class="primary-btn narrow" data-wiz="find" ${!k.gemini && !k.anthropic ? 'disabled' : ''}>Search</button>
      </div>
      ${w.candidates ? renderCandidates(w.candidates) : ''}
    </div>`;

  const step2 = !w.restaurant ? '' : `
    <div class="src-card">
      <h3>2 · Build the source list</h3>
      <p class="src-p">Confirmed: <b>${esc(w.restaurant.name)}</b>, ${esc(w.restaurant.address)}, ${esc(w.restaurant.city)}
      ${w.restaurant.instagram ? ` · @${esc(w.restaurant.instagram)}` : ' · no Instagram found'}</p>
      <p class="src-p">Ask for more than you need — only public <b>Business</b> and <b>Creator</b> accounts can be
      read for free, and private or personal ones will fail at fetch. Depth matters more than breadth:
      four accounts with 30+ reels beat twenty with five.</p>
      ${costBadge('similar', {})}
      <div class="src-row">
        <label class="src-lab">How many accounts <input id="wizCount" type="number" min="10" max="60" value="45" /></label>
        <button class="primary-btn narrow" data-wiz="similar" ${w.busy ? 'disabled' : ''}>Find similar accounts</button>
      </div>
      ${w.accounts ? renderAccounts(w.accounts) : ''}
    </div>`;

  const graphOK = st.sourcesAvailable?.graph;
  const limitVal = state.wizLimit || 50;

  const step3 = !w.accounts?.length ? '' : `
    <div class="src-card">
      <h3>3 · Fetch the reels</h3>
      <p class="src-p"><b>${w.selected.size}</b> accounts selected.
      This uses the official Instagram Graph API, which is <b>free</b> and returns the profile grid —
      so trial and archived reels are excluded automatically, with no second scrape and no guessing.</p>
      ${graphOK
        ? costBadge('graph', { accounts: w.selected.size, limitPerAccount: limitVal })
        : `<div class="cost-badge warn">
             <b>Not connected.</b> Add <code>IG_GRAPH_TOKEN</code> to <code>studio/.env</code> — see
             <code>SETUP-FREE.md</code>. Until then this step can't run.
             ${st.graph?.reason ? `<br><span class="cost-note">${esc(st.graph.reason)}</span>` : ''}
           </div>`}
      <div class="src-row">
        <label class="src-lab">Reels per account
          <input id="wizLimit" type="number" min="12" max="200" step="10" value="${limitVal}" />
        </label>
        <button class="primary-btn narrow" data-wiz="graph" ${w.busy || !w.selected.size || !graphOK ? 'disabled' : ''}>
          Fetch reels — free
        </button>
      </div>
      <details class="src-adv">
        <summary>Import a JSON export you already have</summary>
        <p class="src-p">Reads a dataset dump from disk — including the Apify exports you already paid for.
        Nothing is fetched and nothing is billed.</p>
        <div class="src-row">
          <input id="wizImport" placeholder="/path/to/dataset.json" />
          <button class="mini-btn" data-wiz="import" ${w.busy ? 'disabled' : ''}>Import file</button>
        </div>
      </details>
    </div>`;

  const cut = state.gateInfo?.threshold ?? 0;
  const eligible = state.results.filter((r) => r.outlier.valid && r.outlier.conservative >= cut);
  const todo = eligible.filter((r) => !r.post.attributes || !r.post.adaptations?.[c.id]);
  const best = state.results.filter((r) => r.outlier.valid)
    .sort((a, b) => b.outlier.conservative - a.outlier.conservative)[0];

  const reasoner = st.models?.reasoner === 'claude' && k.anthropic ? 'Claude' : 'Gemini';
  const step4 = `
    <div class="src-card">
      <h3>4 · Analyse the shortlist</h3>
      <p class="src-p">Gemini watches each shortlisted reel and reports observable facts; ${reasoner} works out the
      mechanism and adapts it for <b>${esc(c.name)}</b>. Anything already done is skipped, so re-running costs
      nothing — you never pay twice for the same video.</p>

      <div class="gate-box">
        <label class="src-lab">Analyse the top
          <input id="wizTopN" type="number" min="1" max="120" step="1" value="${CONFIG.topN}" />
          <span>reels by multiplier</span>
        </label>
        <div class="gate-read">
          <b>${eligible.length}</b> shortlisted${cut ? ` at ≥${cut.toFixed(1)}×` : ''} · <b>${todo.length}</b> still to do
          ${best ? ` · best is <b>${best.outlier.conservative.toFixed(1)}×</b>` : ''}
        </div>
      </div>
      <p class="src-note" style="margin-top:6px">
        This number <em>is</em> the budget: it caps how many videos get watched. It can never come back
        empty the way a fixed multiplier gate could — it takes the best you have and tells you what
        multiplier that turned out to be.
      </p>
      ${costBadge('analyze', { videos: todo.length })}

      <div class="src-row" style="margin-top:10px">
        <label class="chk"><input type="checkbox" id="wizForce" /> Redo ones already analysed</label>
        <button class="primary-btn narrow" data-wiz="analyze" ${w.busy ? 'disabled' : ''}>Analyse for ${esc(c.name)}</button>
      </div>
    </div>`;

  const logCard = !w.log.length ? '' : `
    <div class="src-card">
      <h3>${w.busy ? `Running — ${esc(w.busy)}` : 'Last run'}</h3>
      <div class="src-log">${w.log.map((l) => `<div><span>${(l.t / 1000).toFixed(1)}s</span>${esc(l.msg)}</div>`).join('')}</div>
    </div>`;

  $('sources').innerHTML = `<div class="src-wrap">
    <div class="src-card">
      <h3>Status</h3>
      ${keyRow(k.graph, 'Instagram Graph API', st.graph?.self ? `free · as @${st.graph.self.username}` : 'free reel data', st.keyIssues?.graph)}
      ${keyRow(k.gemini, 'Gemini', `${st.models.gemini}${st.geminiFreeTier ? ' · free tier' : ''}`, st.keyIssues?.gemini)}
      ${keyRow(st.sourcesAvailable?.ytdlp, 'yt-dlp', 'free video download', 'not installed — pip3 install yt-dlp')}
      ${keyRow(k.anthropic, 'Claude (optional)', st.models.anthropic, st.keyIssues?.anthropic)}
      <div class="src-stats">
        <div><b>${st.corpus.posts}</b><span>reels held</span></div>
        <div><b>${st.corpus.withBaseline ?? 0}</b><span>scoreable</span></div>
        <div><b>${st.corpus.analysed}</b><span>analysed</span></div>
        <div><b>${st.corpus.sources[c.id] || 0}</b><span>sources for ${esc(c.name)}</span></div>
      </div>
      <p class="src-note">
        Ranking on <b>${esc(st.corpus.metric === 'views' ? 'plays' : 'likes + comments')}</b>, chosen automatically from
        what this corpus carries. Free sources return no play counts, so newly fetched reels rank on engagement.
      </p>
      ${orphanWarning(st, c)}
    </div>
    ${step1}${step2}${step3}${step4}${logCard}
  </div>`;
}

/**
 * The corpus is keyed by client. If reels exist but none belong to the selected
 * client, saying nothing and quietly rendering the demo set reads as data loss.
 */
function orphanWarning(st, c) {
  const mine = st.corpus.sources[c.id] || 0;
  if (mine) return '';
  const others = Object.entries(st.corpus.sources).filter(([, n]) => n > 0);

  if (!st.corpus.posts) {
    return '<p class="src-note">Nothing scraped yet — start at step 1.</p>';
  }
  if (!others.length) {
    return `<div class="warn-box"><b>${st.corpus.posts} reels are stored but not linked to any client.</b>
      <button class="mini-btn" data-adopt="${esc(c.id)}">Link them all to ${esc(c.name)}</button></div>`;
  }
  return `<div class="warn-box">
    <b>Your ${st.corpus.posts} reels are filed under a different client, so this one is showing the demo set.</b>
    <div class="warn-row">${others
      .map(([id, n]) => {
        const known = state.clients.find((x) => x.id === id);
        return `<button class="mini-btn" data-switch="${esc(id)}">${esc(known ? known.name : id)} — ${n} accounts</button>`;
      })
      .join('')}
      <button class="mini-btn" data-adopt="${esc(c.id)}">or link them to ${esc(c.name)}</button>
    </div>
  </div>`;
}

function renderCandidates(list) {
  if (!list.length) return '<p class="src-note">Nothing found. Try adding the city or street.</p>';
  return `<div class="cands">${list
    .map(
      (r, i) => `<div class="cand">
        <div class="cand-main">
          <b>${esc(r.name)}</b>
          <span>${esc(r.address)}${r.address ? ', ' : ''}${esc(r.city)} · ${esc(r.cuisine)}</span>
          <span class="cand-note">${r.instagram ? '@' + esc(r.instagram) : 'no Instagram found'} · ${esc(r.note)}</span>
        </div>
        <div class="cand-side">
          <span class="conf ${esc(r.confidence)}">${esc(r.confidence)}</span>
          <button class="mini-btn" data-pick="${i}">Yes, this one</button>
        </div>
      </div>`,
    )
    .join('')}</div>`;
}

function renderAccounts(list) {
  const groups = { same_cuisine_same_city: 'Same cuisine, same city', same_cuisine_other_city: 'Same cuisine, other cities',
    adjacent_concept: 'Adjacent concepts', food_creator: 'Food creators' };
  const bySec = {};
  list.forEach((a, i) => (bySec[a.category] ||= []).push({ ...a, i }));

  return `<div class="acc-head">
      <button class="mini-btn" data-wiz="all">Select all</button>
      <button class="mini-btn" data-wiz="none">Clear</button>
    </div>` + Object.entries(groups)
    .filter(([k]) => bySec[k]?.length)
    .map(
      ([k, label]) => `<h5 class="acc-sec">${label}</h5>
      <div class="accs">${bySec[k]
        .map(
          (a) => `<label class="acc ${state.wiz.selected.has(a.handle) ? 'on' : ''}">
            <input type="checkbox" data-acc="${esc(a.handle)}" ${state.wiz.selected.has(a.handle) ? 'checked' : ''} />
            <span class="acc-h">@${esc(a.handle)}</span>
            <span class="acc-w">${esc(a.why)}</span>
            <span class="conf ${esc(a.confidence)}">${esc(a.confidence)}</span>
          </label>`,
        )
        .join('')}</div>`,
    )
    .join('');
}

async function runWiz(action) {
  const w = state.wiz;
  try {
    if (action === 'find') {
      w.query = $('wizQuery').value;
      w.busy = 'searching'; w.log = []; renderSources();
      const { jobId } = await api('/api/discover/restaurant', { query: w.query });
      const out = await followJob(jobId, renderSources);
      w.candidates = out.candidates || []; w.restaurant = null; w.accounts = null;
    }

    if (action === 'similar') {
      w.busy = 'finding accounts'; renderSources();
      const { jobId } = await api('/api/discover/similar', { restaurant: w.restaurant, count: +$('wizCount').value });
      const out = await followJob(jobId, renderSources);
      w.accounts = out.accounts || [];
      w.selected = new Set(w.accounts.filter((a) => a.confidence !== 'low').map((a) => a.handle));
    }

    // The free path.
    if (action === 'graph') {
      w.busy = 'reading accounts'; renderSources();
      const { jobId } = await api('/api/graph/fetch', {
        clientId: state.clientId,
        handles: [...w.selected],
        limitPerAccount: +$('wizLimit').value,
      });
      await followJob(jobId, renderSources);
      await refreshStatus();
      await loadCorpus();
    }

    if (action === 'import') {
      w.busy = 'importing'; renderSources();
      const { jobId } = await api('/api/import', {
        clientId: state.clientId,
        path: $('wizImport').value.trim(),
      });
      await followJob(jobId, renderSources);
      await refreshStatus();
      await loadCorpus();
    }

    if (action === 'analyze') {
      const topN = +$('wizTopN').value || CONFIG.topN;
      CONFIG.topN = topN;
      w.busy = 'analysing'; renderSources();
      const { jobId } = await api('/api/analyze', {
        clientId: state.clientId, client: client(),
        topN, limit: topN, force: $('wizForce').checked,
      });
      await followJob(jobId, renderSources);
      await refreshStatus();
      await loadCorpus();
    }
  } catch (e) {
    w.log = [...w.log, { t: 0, msg: `Error: ${e.message}` }];
  } finally {
    w.busy = '';
    persistUI();
    recompute();
    renderClientBar();
    renderFunnel();
    renderSources();
  }
}

async function refreshStatus() {
  try { state.status = await api('/api/status'); } catch { state.status = null; }
}

/* ------------------------------------------------------------------ *
 * Tune drawer
 * ------------------------------------------------------------------ */

function renderTune() {
  const w = CONFIG.weights;
  const r = state.results;
  const count = (st) => r.filter((x) => x.stage === st).length;

  // How many reels each switch is currently removing, so the cost of every
  // filter is visible rather than inferred.
  const flagCounts = {};
  for (const x of r) for (const f of x.post.flags || []) flagCounts[f] = (flagCounts[f] || 0) + 1;

  const num = (key, label, min, max, step, val, note) => `
    <div class="frow">
      <label>${esc(label)}<input type="number" min="${min}" max="${max}" step="${step}" value="${val}" data-cfg="${key}" /></label>
      <span>${esc(note)}</span>
    </div>`;

  $('tuneBody').innerHTML = `
    <h5 class="fsec">Exclude these reels</h5>
    ${Object.keys(CONFIG.exclude)
      .map(
        (f) => `<label class="chk fchk">
          <input type="checkbox" data-exclude="${f}" ${CONFIG.exclude[f] ? 'checked' : ''} />
          ${esc(FLAG_LABELS[f] || f)}
          <b>${flagCounts[f] || 0}</b>
        </label>`,
      )
      .join('')}
    <p class="tune-note">Nothing is deleted — these decide what counts. "Not on the profile grid" only applies to
    the old paid scrape; the Graph API returns the grid itself, so trial reels never enter the corpus.</p>

    <h5 class="fsec">Which reels are scoreable</h5>
    ${num('minAgeDays', 'Youngest age', 0, 60, 1, CONFIG.minAgeDays, 'days — below this, reach is still climbing')}
    ${num('maxAgeDays', 'Oldest age', 20, 365, 5, CONFIG.maxAgeDays, 'days')}
    ${num('minBaselinePosts', 'Min posts for a baseline', 3, 20, 1, CONFIG.minBaselinePosts, 'fewer = noisier median')}

    <h5 class="fsec">Shortlist cut</h5>
    <div class="tune-seg">
      <button class="seg-btn ${CONFIG.gateMode === 'topN' ? 'is-active' : ''}" data-gatemode="topN">Top N</button>
      <button class="seg-btn ${CONFIG.gateMode === 'multiplier' ? 'is-active' : ''}" data-gatemode="multiplier">Fixed ×</button>
    </div>
    ${CONFIG.gateMode === 'topN'
      ? `<div class="slider">
           <label>Analyse the best <span>${CONFIG.topN}</span></label>
           <input type="range" min="5" max="100" step="5" value="${CONFIG.topN}" data-cfg="topN" />
         </div>
         <div class="slider">
           <label>…but never below <span>${CONFIG.minMultiplier}×</span></label>
           <input type="range" min="1" max="5" step="0.1" value="${CONFIG.minMultiplier}" data-cfg="minMultiplier" />
         </div>
         <p class="tune-note">Current cut: <b>${state.gateInfo?.threshold?.toFixed(1) ?? '—'}×</b> from
         ${state.gateInfo?.eligible ?? 0} eligible reels. Top-N can never return nothing, and it caps
         what analysis costs.</p>`
      : `<div class="slider">
           <label>Analyse above <span>${CONFIG.gateMultiplier}×</span></label>
           <input type="range" min="1" max="30" step="0.5" value="${CONFIG.gateMultiplier}" data-gate="1" />
         </div>
         <p class="tune-note">Honest, but can return zero. An 8× cut tuned on plays passes almost nothing on
         engagement, because likes saturate where plays do not.</p>`}

    <h5 class="fsec">Score weights</h5>
    ${[['V', 'Virality evidence'], ['R', 'Replicability'], ['F', 'Client fit'], ['T', 'Tone fit']]
      .map(
        ([k, label]) => `
      <div class="slider">
        <label>${esc(label)} <span>${w[k].toFixed(2)}</span></label>
        <input type="range" min="0" max="0.7" step="0.01" value="${w[k]}" data-weight="${k}" />
      </div>`,
      )
      .join('')}

    <div class="fstats">
      <span><b>${count('scored')}</b> scored</span>
      <span><b>${count('unanalysed')}</b> to analyse</span>
      <span><b>${count('below_gate')}</b> under gate</span>
      <span><b>${count('rejected')}</b> out of window</span>
      <span><b>${count('excluded')}</b> filtered out</span>
    </div>`;
}

function normaliseWeights() {
  const w = CONFIG.weights;
  const sum = w.V + w.R + w.F + w.T || 1;
  ['V', 'R', 'F', 'T'].forEach((k) => (w[k] /= sum));
}

/* ------------------------------------------------------------------ *
 * Render + events
 * ------------------------------------------------------------------ */

function renderAll() {
  recompute();
  renderClientSwitch();
  renderClientBar();
  renderFunnel();
  renderFilterBar();
  if (state.view === 'feed') renderFeed();
  else if (state.view === 'gallery') renderGallery();
  else renderSources();
  renderPanel();
}

function setView(v) {
  state.view = v;
  $('feedWrap').hidden = v !== 'feed';
  $('gallery').hidden = v !== 'gallery';
  $('sources').hidden = v !== 'sources';
  // The filter bar acts on the dataset, so it is meaningless over the wizard.
  $('filterBar').hidden = v === 'sources';
  document.querySelectorAll('#viewSwitch .seg-btn').forEach((b) => b.classList.toggle('is-active', b.dataset.view === v));
  if (v === 'feed') renderFeed();
  else if (v === 'gallery') renderGallery();
  else renderSources();
  renderPanel();
}

function openSheet(postId) {
  $('sheetInner').innerHTML = renderDetail(state.results.find((r) => r.post.id === postId));
  $('sheet').hidden = false;
}

function refreshOpenDetail(postId) {
  renderPanel();
  if (!$('sheet').hidden) openSheet(postId);
}

document.addEventListener('click', (e) => {
  const t = e.target;

  if (t.closest('[data-newclient]')) return openEditor(null);

  const editBtn = t.closest('[data-editclient]');
  if (editBtn) return openEditor(editBtn.dataset.editclient);

  const resetBtn = t.closest('[data-resetclient]');
  if (resetBtn) {
    resetClient(resetBtn.dataset.resetclient);
    state.clients = resolveClients(CLIENTS);
    return renderAll();
  }

  const delBtn = t.closest('[data-deleteclient]');
  if (delBtn) {
    const c = state.clients.find((x) => x.id === delBtn.dataset.deleteclient);
    if (!confirm(`Delete ${c.name} and its logged outcomes? This cannot be undone.`)) return;
    deleteClient(delBtn.dataset.deleteclient);
    state.clients = resolveClients(CLIENTS);
    state.clientId = state.clients[0].id;
    return renderAll();
  }

  if (t.closest('[data-export]')) return exportShootList();

  if (t.closest('[data-saveclient]')) {
    const c = state.editing;
    if (!c.name.trim()) { alert('Give the client a name.'); return; }
    saveClient(c, !CLIENTS.some((x) => x.id === c.id));
    state.clients = resolveClients(CLIENTS);
    state.clientId = c.id;
    $('editor').hidden = true;
    state.editing = null;
    return renderAll();
  }
  if (t.closest('[data-canceledit]') || t.id === 'editorClose') {
    $('editor').hidden = true;
    state.editing = null;
    return;
  }

  const outBtn = t.closest('[data-outcome]');
  if (outBtn) {
    setOutcome(client().id, outBtn.dataset.outcome, { status: outBtn.dataset.status });
    recompute();
    refreshOpenDetail(outBtn.dataset.outcome);
    if (state.view === 'feed') renderFeed(); else renderGallery();
    renderClientBar();
    return;
  }

  const wizBtn = t.closest('[data-wiz]');
  if (wizBtn) {
    const a = wizBtn.dataset.wiz;
    if (a === 'all') { state.wiz.accounts.forEach((x) => state.wiz.selected.add(x.handle)); persistUI(); return renderSources(); }
    if (a === 'none') { state.wiz.selected.clear(); persistUI(); return renderSources(); }
    return runWiz(a);
  }

  const sw = t.closest('[data-switch]');
  if (sw) {
    const id = sw.dataset.switch;
    if (state.clients.some((x) => x.id === id)) {
      state.clientId = id;
      state.selectedId = null;
      persistUI();
      return loadCorpus().then(renderAll);
    }
    alert(`The reels are filed under client id "${id}", which no longer exists in this browser.\nUse "link them to ..." to attach them to the client you want.`);
    return;
  }

  const adopt = t.closest('[data-adopt]');
  if (adopt) {
    (async () => {
      const all = await api('/api/corpus?clientId=__all__');
      const handles = [...new Set((all.allCreators || []).map((x) => x))];
      await api('/api/sources', { clientId: adopt.dataset.adopt, handles });
      await refreshStatus();
      await loadCorpus();
      renderAll();
      renderSources();
    })();
    return;
  }

  const pick = t.closest('[data-pick]');
  if (pick) {
    state.wiz.restaurant = state.wiz.candidates[+pick.dataset.pick];
    state.wiz.candidates = null;
    persistUI();
    return renderSources();
  }

  const tab = t.closest('[data-client]');
  if (tab) {
    state.clientId = tab.dataset.client;
    state.selectedId = null;
    persistUI();
    loadCorpus().then(renderAll);
    return renderAll();
  }

  const view = t.closest('[data-view]');
  if (view) return setView(view.dataset.view);

  const dot = t.closest('.scrub-dot');
  if (dot) {
    const post = state.corpus.posts.find((p) => p.id === dot.dataset.post);
    const label = document.querySelector(`[data-label="${dot.dataset.post}"]`);
    if (post && label) label.textContent = post.timeline[+dot.dataset.i].label;
    e.stopPropagation();
    return;
  }

  const open = t.closest('[data-open]');
  if (open) {
    const narrow = window.matchMedia('(max-width: 900px)').matches;
    if (state.view === 'gallery' || narrow) openSheet(open.dataset.open);
    else {
      state.selectedId = open.dataset.open;
      renderPanel();
    }
    return;
  }

  if (t.id === 'sheetClose' || t.id === 'sheet') $('sheet').hidden = true;

  if (t.id === 'tuneBtn') {
    const d = $('tune');
    d.hidden = !d.hidden;
    $('tuneBtn').setAttribute('aria-expanded', String(!d.hidden));
    if (!d.hidden) renderTune();
  }
  if (t.id === 'tuneClose') $('tune').hidden = true;
  if (t.id === 'tuneReset') {
    Object.assign(CONFIG.weights, DEFAULTS.weights);
    Object.assign(CONFIG.exclude, DEFAULTS.exclude);
    CONFIG.gateMultiplier = DEFAULTS.gate;
    CONFIG.gateMode = DEFAULTS.gateMode;
    CONFIG.topN = DEFAULTS.topN;
    CONFIG.minMultiplier = DEFAULTS.minMultiplier;
    CONFIG.minAgeDays = DEFAULTS.minAgeDays;
    CONFIG.maxAgeDays = DEFAULTS.maxAgeDays;
    CONFIG.minBaselinePosts = DEFAULTS.minBaselinePosts;
    CONFIG.minBaselineValue = DEFAULTS.minBaselineValue;
    renderTune();
    renderAll();
  }
});

/* ---------------- capability sliders + dataset filters ---------------- */

document.addEventListener('click', (e) => {
  const t = e.target;

  if (t.closest('[data-capstoggle]')) {
    state.capsOpen = !state.capsOpen;
    return renderClientBar();
  }

  const gm = t.closest('[data-gatemode]');
  if (gm) {
    CONFIG.gateMode = gm.dataset.gatemode;
    renderAll();
    return renderTune();
  }

  const pill = t.closest('.fb-pill');
  if (pill) {
    const set = state.filters[pill.dataset.filter];
    const v = pill.dataset.value;
    set.has(v) ? set.delete(v) : set.add(v);
    return applyAndRender();
  }

  if (t.closest('[data-clearfilters]')) {
    state.filters = BLANK_FILTERS();
    return applyAndRender();
  }

  // Funnel stages are shortcuts into the same filter set.
  const fs = t.closest('[data-funnel]');
  if (fs) {
    const want = fs.dataset.funnel;
    state.filters = BLANK_FILTERS();
    if (want === 'shortlist') state.filters.shortlistOnly = true;
    else state.filters.stages.add(want);
    return applyAndRender();
  }

  // "Why am I short of six" — show exactly what failed the client, not the data.
  if (t.closest('[data-shortfall]')) {
    state.filters = BLANK_FILTERS();
    state.filters.stages.add('filtered');
    state.filters.stages.add('unanalysed');
    return applyAndRender();
  }
});

function applyAndRender() {
  state.visible = applyFilters(state.results);
  if (!state.visible.find((r) => r.post.id === state.selectedId))
    state.selectedId = state.visible[0]?.post.id ?? null;
  renderFilterBar();
  if (state.view === 'gallery') renderGallery(); else renderFeed();
  renderPanel();
}

document.addEventListener('input', (e) => {
  const el = e.target;

  if (el.id === 'wizTopN') {
    CONFIG.topN = Math.max(1, +el.value || 1);
    recompute();
    renderFunnel();
    const box = document.querySelector('.gate-read');
    if (box) {
      const c2 = client();
      const cut = state.gateInfo?.threshold ?? 0;
      const elig = state.results.filter((r) => r.outlier.valid && r.outlier.conservative >= cut);
      const td = elig.filter((r) => !r.post.attributes || !r.post.adaptations?.[c2.id]);
      box.innerHTML = `<b>${elig.length}</b> shortlisted at ≥${cut.toFixed(1)}× · <b>${td.length}</b> still to do`;
    }
    return;
  }

  if (el.dataset.acc) {
    el.checked ? state.wiz.selected.add(el.dataset.acc) : state.wiz.selected.delete(el.dataset.acc);
    persistUI();
    el.closest('.acc')?.classList.toggle('on', el.checked);
    const n = document.querySelector('[data-wiz="graph"]');
    if (n) renderSources();
    return;
  }

  if (state.editing && el.closest('#editor')) {
    applyEditorField(el);
    return;
  }

  const views = el.dataset.outviews;
  if (views !== undefined) {
    setOutcome(client().id, views, { views: el.value === '' ? null : +el.value });
    recompute();
    const cur = state.results.find((r) => r.post.id === views);
    const ratioEl = el.closest('.out-views')?.querySelector('.out-ratio');
    const ratio = el.value > 0 ? +el.value / (cur.client.capability.ownBaselineViews || 1) : null;
    if (ratioEl) {
      ratioEl.textContent = ratio
        ? `${ratio.toFixed(1)}× their baseline (${fmt(cur.client.capability.ownBaselineViews)})`
        : '';
      ratioEl.className = `out-ratio ${ratio ? (ratio >= 2 ? 'good' : ratio >= 1 ? 'mid' : 'bad') : ''}`;
    }
    renderClientBar();
    return;
  }

  if (el.dataset.exclude) {
    CONFIG.exclude[el.dataset.exclude] = el.checked;
    renderAll();
    renderTune();
    return;
  }
  if (el.dataset.cfg) {
    const v = +el.value;
    if (Number.isFinite(v)) CONFIG[el.dataset.cfg] = v;
    renderAll();
    renderTune();
    return;
  }

  const wk = el.dataset.weight;
  if (wk) {
    CONFIG.weights[wk] = +el.value;
    normaliseWeights();
    renderTune();
    renderAll();
    return;
  }
  if (el.dataset.gate) {
    CONFIG.gateMultiplier = +el.value;
    renderTune();
    renderAll();
    return;
  }

  /* ---- capability sliders ---- */
  if (el.dataset.cap) {
    const key = el.dataset.cap;
    const c = client();
    const cap = { ...c.capability };

    if (key === 'chefOnCamera') cap[key] = ['no', 'low', 'medium', 'high'][+el.value] || 'no';
    else if (key === 'customersOnCamera') cap[key] = el.checked;
    else cap[key] = +el.value;

    // Persist immediately — the previous version lost work on reload and that is
    // not a mistake worth repeating.
    const updated = { ...c, capability: cap };
    saveClient(updated, !CLIENTS.some((x) => x.id === c.id));
    state.clients = resolveClients(CLIENTS);

    // Update the readout in place. A full re-render would tear the slider out
    // from under the pointer mid-drag.
    const out = el.closest('.cap-row')?.querySelector('.cap-val');
    if (out) {
      out.textContent =
        key === 'chefOnCamera' ? cap[key]
          : key === 'customersOnCamera' ? (cap[key] ? 'allowed' : 'not allowed')
            : `${el.value}${{ staffMinutesPerConcept: ' min', monthlyBudgetEur: ' €', ownBaselineViews: ' views' }[key] || ''}`;
    }
    recompute();
    renderFunnel();
    renderFilterBar();
    if (state.view === 'gallery') renderGallery(); else renderFeed();
    renderPanel();
    return;
  }

  /* ---- dataset filters ---- */
  if (el.dataset.filter) {
    const key = el.dataset.filter;
    if (el.type === 'checkbox') state.filters[key] = el.checked;
    else state.filters[key] = +el.value;
    const out = el.closest('.fb-group')?.querySelector('output');
    if (out) {
      out.textContent =
        key === 'minMultiplier' ? (+el.value ? `${el.value}×` : 'any')
          : key === 'maxAgeDays' ? (+el.value ? `${el.value}d` : 'any')
            : (+el.value || 'any');
    }
    state.visible = applyFilters(state.results);
    if (state.view === 'gallery') renderGallery(); else renderFeed();
    const count = document.querySelector('.fb-count');
    if (count) {
      count.textContent = `${state.visible.length} of ${state.results.length}`;
      count.classList.toggle('on', state.visible.length < state.results.length);
    }
    return;
  }

  if (el.id === 'fbSearch') {
    state.filters.q = el.value;
    state.visible = applyFilters(state.results);
    if (state.view === 'gallery') renderGallery(); else renderFeed();
    const count = document.querySelector('.fb-count');
    if (count) {
      count.textContent = `${state.visible.length} of ${state.results.length}`;
      count.classList.toggle('on', state.visible.length < state.results.length);
    }
  }
});

document.addEventListener('mouseover', (e) => {
  const dot = e.target.closest('.scrub-dot');
  if (!dot) return;
  const post = state.corpus.posts.find((p) => p.id === dot.dataset.post);
  const label = document.querySelector(`[data-label="${dot.dataset.post}"]`);
  if (post && label) label.textContent = post.timeline[+dot.dataset.i].label;
});

document.addEventListener('keydown', (e) => {
  if (e.key !== 'Escape') return;
  $('sheet').hidden = true;
  $('tune').hidden = true;
  $('editor').hidden = true;
  state.editing = null;
});

$('scorerVersion').textContent = `scorer v${SCORER_VERSION}`;
renderAll();

// Server is optional: without it the app stays on the seeded corpus.
(async () => {
  await refreshStatus();
  if (!state.status) return;
  await loadCorpus();
  renderAll();
  if (state.view === 'sources') renderSources();
  await resumeJob();
})();
