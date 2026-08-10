import { CLIENTS, CREATORS, POSTS, TONE_LABELS } from './data.js';
import { CONFIG, SCORER_VERSION, scoreAll, labelSpace } from './scoring.js';

const SHORTLIST_SIZE = 6;
const DEFAULTS = JSON.parse(JSON.stringify({ weights: CONFIG.weights, gate: CONFIG.gemniGateMultiplier }));

const state = {
  clientId: CLIENTS[0].id,
  view: 'feed',
  results: [],
  selectedId: null,
};

const $ = (id) => document.getElementById(id);
const client = () => CLIENTS.find((c) => c.id === state.clientId);

const fmt = (n) =>
  n >= 1e6 ? `${(n / 1e6).toFixed(n >= 1e7 ? 0 : 1)}M` : n >= 1e3 ? `${(n / 1e3).toFixed(0)}K` : `${n}`;
const esc = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const pct = (x) => `${Math.round(x * 100)}%`;

/* ------------------------------------------------------------------ *
 * Scoring pass
 * ------------------------------------------------------------------ */

const STAGE_ORDER = { scored: 0, filtered: 1, below_gate: 2, rejected: 3 };

function recompute() {
  const c = client();
  const results = scoreAll(POSTS, CREATORS, c);

  results.sort((a, b) => {
    const s = STAGE_ORDER[a.stage] - STAGE_ORDER[b.stage];
    if (s !== 0) return s;
    if (a.stage === 'scored') return b.opportunity - a.opportunity;
    return (b.outlier.conservative || 0) - (a.outlier.conservative || 0);
  });

  results.forEach((r, i) => {
    r.rank = r.stage === 'scored' ? i + 1 : null;
    r.shortlisted = r.stage === 'scored' && i < SHORTLIST_SIZE;
  });

  state.results = results;
  if (!results.find((r) => r.post.id === state.selectedId)) {
    state.selectedId = results[0]?.post.id ?? null;
  }
  document.documentElement.style.setProperty('--tab-hue', c.accent);
  document.documentElement.style.setProperty('--accent', c.accent);
}

/* ------------------------------------------------------------------ *
 * Header / client bar / funnel
 * ------------------------------------------------------------------ */

function renderClientSwitch() {
  $('clientSwitch').innerHTML = CLIENTS.map(
    (c) => `
    <button class="client-tab ${c.id === state.clientId ? 'is-active' : ''}"
            style="--tab-hue:${c.accent}" data-client="${c.id}" role="tab">
      <strong>${esc(c.name)}</strong>
      <span>${esc(c.cuisine)} · ${esc(c.city)}</span>
    </button>`,
  ).join('');
}

function renderClientBar() {
  const c = client();
  const cap = c.capability;
  const chips = [
    `${cap.staffCount} staff · ${cap.staffAvailableForFilming} free to film`,
    `€${cap.monthlyBudgetEur}/mo · €${Math.round(cap.monthlyBudgetEur / 6)} per concept`,
    `${cap.staffMinutesPerConcept} min per concept`,
    `kit: ${cap.equipment.join(', ')}`,
    `chef on camera: ${cap.chefOnCamera}`,
  ]
    .map((t) => `<span class="chip">${esc(t)}</span>`)
    .join('');

  const yesno = [
    `<span class="chip ${cap.customersOnCamera ? 'yes' : 'no'}">guests on camera: ${cap.customersOnCamera ? 'ok' : 'not allowed'}</span>`,
    ...cap.spaces.map((s) => `<span class="chip yes">${esc(labelSpace(s))}</span>`),
    ...(cap.avoidTones || []).map((t) => `<span class="chip no">avoids ${esc(TONE_LABELS[t] || t)}</span>`),
  ].join('');

  $('clientBar').innerHTML = `
    <div class="cb-brief"><b>Brief.</b> ${esc(c.brief)}</div>
    <div class="cb-caps">${chips}${yesno}</div>`;
}

function renderFunnel() {
  const r = state.results;
  const mature = r.filter((x) => x.outlier.valid).length;
  const gated = r.filter((x) => x.stage !== 'rejected' && x.stage !== 'below_gate').length;
  const scored = r.filter((x) => x.stage === 'scored').length;

  const stages = [
    [POSTS.length, 'discovered', ''],
    [mature, 'in age window', ''],
    [gated, `past ${CONFIG.gemniGateMultiplier}× gate`, ''],
    [scored, 'client-viable', ''],
    [Math.min(SHORTLIST_SIZE, scored), 'shortlist', 'shortlist'],
  ];

  $('funnel').innerHTML = stages
    .map(([n, label, cls]) => `<div class="fstage ${cls}"><b>${n}</b><span>${esc(label)}</span></div>`)
    .join('');
}

/* ------------------------------------------------------------------ *
 * Poster / media
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

  const m = res.outlier.valid ? res.outlier.conservative : 0;
  const tone = res.outlier.valid ? res.outlier.band.tone : 'low';

  return { inner, badge, m, tone, dropped };
}

function dropLabel(res) {
  if (res.stage === 'rejected') return 'OUT OF WINDOW';
  if (res.stage === 'below_gate') return 'BELOW GATE';
  return 'FILTERED';
}

/* ------------------------------------------------------------------ *
 * Feed
 * ------------------------------------------------------------------ */

function renderFeed() {
  const feed = $('feed');
  feed.innerHTML = state.results
    .map((res) => {
      const p = res.post;
      const cr = res.creator;
      const { inner, badge, m, tone, dropped } = mediaHTML(res);

      const dots = p.timeline
        .map(
          (t, i) =>
            `<div class="scrub-dot" style="left:${(t.t / p.durationS) * 100}%" data-post="${p.id}" data-i="${i}" title="${esc(t.label)}"></div>`,
        )
        .join('');

      return `
      <section class="slide" data-post="${p.id}">
        <div class="phone ${dropped ? 'is-dropped' : ''}" data-open="${p.id}">
          ${inner}
          ${badge}
          <div class="ph-top">
            <span class="handle">@${esc(cr.handle)}</span>
            <span class="mult ${tone}">${m ? `${m.toFixed(1)}×` : '—'}</span>
          </div>
          <div class="scrub">
            <div class="scrub-track">${dots}</div>
            <div class="scrub-label" data-label="${p.id}">${esc(p.timeline[0].label)}</div>
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
  $('gallery').innerHTML = state.results
    .map((res) => {
      const p = res.post;
      const { inner, badge, m, tone, dropped } = mediaHTML(res);
      const scoreLine = dropped
        ? `<span class="drop">${esc(dropLabel(res))}</span>`
        : `<span class="op">${res.opportunity.toFixed(1)}</span>`;

      const mini = dropped
        ? ''
        : `<div class="tile-mini">
             ${[['V', res.V, '#60a5fa'], ['R', res.R.score, '#4ade80'], ['F', res.F.score, '#fbbf24'], ['T', res.T.score, '#c084fc']]
               .map(([, v, col]) => `<i><b style="width:${pct(v)};background:${col}"></b></i>`)
               .join('')}
           </div>`;

      return `
      <button class="tile" data-open="${p.id}">
        <div class="tile-media ${dropped ? 'is-dropped' : ''}">
          ${inner}${badge}
          <div class="ph-top"><span class="handle">@${esc(res.creator.handle)}</span>
            <span class="mult ${tone}">${m ? `${m.toFixed(1)}×` : '—'}</span></div>
        </div>
        <div class="tile-stats">
          <div class="tile-title">${esc(p.caption)}</div>
          <div class="tile-line">
            ${scoreLine}
            <span>▶ ${fmt(p.views)}</span>
            <span>${esc(TONE_LABELS[p.attributes.tone] || p.attributes.tone)}</span>
            <span>€${p.attributes.propsCostEur} · ${p.attributes.staffMinutes}m</span>
          </div>
          ${mini}
        </div>
      </button>`;
    })
    .join('');
}

/* ------------------------------------------------------------------ *
 * Detail (panel + sheet share this)
 * ------------------------------------------------------------------ */

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
      <div class="sec"><h4>Mechanism (recorded anyway)</h4><p>${esc(p.mechanism)}</p></div>
      ${attrsHTML(a)}`;
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

    <div class="sec">
      <h4>Why the original worked</h4>
      <p class="lead">${esc(p.mechanism)}</p>
    </div>

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

    <div class="sec"><h4>Transcript</h4><p>${esc(p.transcript)}</p></div>
    ${attrsHTML(a)}`;
}

function attrsHTML(a) {
  const rows = [
    ['Hook', a.hookType],
    ['Format', a.format],
    ['Tone', TONE_LABELS[a.tone] || a.tone],
    ['Edit', a.editComplexity],
    ['Audio', a.audioDependency],
    ['Cuts', `${a.cuts} · avg ${a.avgShotLengthS}s`],
    ['On camera', a.peopleOnCamera],
    ['Trend half-life', a.trendHalfLifeDays ? `${a.trendHalfLifeDays}d` : 'evergreen'],
  ];
  return `<div class="sec"><h4>Extracted attributes (Gemini)</h4><div class="attr-grid">
    ${rows.map(([k, v]) => `<div class="attr"><b>${esc(k)}</b><span>${esc(v)}</span></div>`).join('')}
  </div></div>`;
}

function renderPanel() {
  const res = state.results.find((r) => r.post.id === state.selectedId);
  $('panel').innerHTML = renderDetail(res);
}

/* ------------------------------------------------------------------ *
 * Tune drawer
 * ------------------------------------------------------------------ */

function renderTune() {
  const w = CONFIG.weights;
  const rows = [
    ['V', 'Virality evidence', w.V],
    ['R', 'Replicability', w.R],
    ['F', 'Client fit', w.F],
    ['T', 'Tone fit', w.T],
  ];
  $('tuneBody').innerHTML = `
    ${rows
      .map(
        ([k, label, v]) => `
      <div class="slider">
        <label>${esc(label)} <span>${v.toFixed(2)}</span></label>
        <input type="range" min="0" max="0.7" step="0.01" value="${v}" data-weight="${k}" />
      </div>`,
      )
      .join('')}
    <div class="slider">
      <label>Extraction gate <span>${CONFIG.gemniGateMultiplier.toFixed(0)}×</span></label>
      <input type="range" min="2" max="30" step="1" value="${CONFIG.gemniGateMultiplier}" data-gate="1" />
    </div>
    <p class="tune-note" style="margin:0">
      Weights are normalised to sum to 1 before scoring, so moving one moves the others.
    </p>`;
}

function normaliseWeights() {
  const w = CONFIG.weights;
  const sum = w.V + w.R + w.F + w.T || 1;
  ['V', 'R', 'F', 'T'].forEach((k) => (w[k] = w[k] / sum));
}

/* ------------------------------------------------------------------ *
 * Render + events
 * ------------------------------------------------------------------ */

function renderAll() {
  recompute();
  renderClientSwitch();
  renderClientBar();
  renderFunnel();
  if (state.view === 'feed') renderFeed();
  else renderGallery();
  renderPanel();
}

function setView(v) {
  state.view = v;
  $('feedWrap').hidden = v !== 'feed';
  $('gallery').hidden = v !== 'gallery';
  document.querySelectorAll('#viewSwitch .seg-btn').forEach((b) => b.classList.toggle('is-active', b.dataset.view === v));
  if (v === 'feed') renderFeed();
  else renderGallery();
  renderPanel();
}

function openSheet(postId) {
  const res = state.results.find((r) => r.post.id === postId);
  $('sheetInner').innerHTML = renderDetail(res);
  $('sheet').hidden = false;
}

document.addEventListener('click', (e) => {
  const tab = e.target.closest('[data-client]');
  if (tab) {
    state.clientId = tab.dataset.client;
    state.selectedId = null;
    renderAll();
    return;
  }

  const view = e.target.closest('[data-view]');
  if (view) return setView(view.dataset.view);

  const dot = e.target.closest('.scrub-dot');
  if (dot) {
    const post = POSTS.find((p) => p.id === dot.dataset.post);
    const label = document.querySelector(`[data-label="${dot.dataset.post}"]`);
    if (post && label) label.textContent = post.timeline[+dot.dataset.i].label;
    e.stopPropagation();
    return;
  }

  const open = e.target.closest('[data-open]');
  if (open) {
    const narrow = window.matchMedia('(max-width: 900px)').matches;
    if (state.view === 'gallery' || narrow) openSheet(open.dataset.open);
    else {
      state.selectedId = open.dataset.open;
      renderPanel();
    }
    return;
  }

  if (e.target.id === 'sheetClose' || e.target.id === 'sheet') $('sheet').hidden = true;

  if (e.target.id === 'tuneBtn') {
    const t = $('tune');
    t.hidden = !t.hidden;
    $('tuneBtn').setAttribute('aria-expanded', String(!t.hidden));
    if (!t.hidden) renderTune();
  }
  if (e.target.id === 'tuneClose') $('tune').hidden = true;

  if (e.target.id === 'tuneReset') {
    Object.assign(CONFIG.weights, DEFAULTS.weights);
    CONFIG.gemniGateMultiplier = DEFAULTS.gate;
    renderTune();
    renderAll();
  }
});

document.addEventListener('input', (e) => {
  const wk = e.target.dataset.weight;
  if (wk) {
    CONFIG.weights[wk] = +e.target.value;
    normaliseWeights();
    renderTune();
    renderAll();
    return;
  }
  if (e.target.dataset.gate) {
    CONFIG.gemniGateMultiplier = +e.target.value;
    renderTune();
    renderAll();
  }
});

document.addEventListener('mouseover', (e) => {
  const dot = e.target.closest('.scrub-dot');
  if (!dot) return;
  const post = POSTS.find((p) => p.id === dot.dataset.post);
  const label = document.querySelector(`[data-label="${dot.dataset.post}"]`);
  if (post && label) label.textContent = post.timeline[+dot.dataset.i].label;
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    $('sheet').hidden = true;
    $('tune').hidden = true;
  }
});

$('scorerVersion').textContent = `scorer v${SCORER_VERSION}`;
renderAll();
