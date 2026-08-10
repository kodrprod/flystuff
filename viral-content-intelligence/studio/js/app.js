import { CLIENTS, CREATORS, POSTS, TONE_LABELS } from './data.js';
import { CONFIG, SCORER_VERSION, scoreAll, labelSpace } from './scoring.js';
import {
  resolveClients, saveClient, deleteClient, isCustomClient, hasOverride, resetClient,
  getOutcome, setOutcome, outcomeSummary,
} from './store.js';

const SHORTLIST_SIZE = 6;
const DEFAULTS = JSON.parse(JSON.stringify({ weights: CONFIG.weights, gate: CONFIG.gemniGateMultiplier }));

const SPACES = ['counter', 'small_kitchen', 'full_kitchen', 'dining_room', 'shared_seating', 'outdoor', 'street', 'multi_location'];
const EQUIPMENT = ['phone', 'tripod', 'gimbal', 'light', 'second_camera', 'drone'];
const TONES = Object.keys(TONE_LABELS);

const state = {
  clients: resolveClients(CLIENTS),
  clientId: CLIENTS[0].id,
  view: 'feed',
  results: [],
  selectedId: null,
  editing: null,
};

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
    r.outcome = getOutcome(c.id, r.post.id);
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
        <button class="mini-btn" data-editclient="${c.id}">Edit profile</button>
        ${hasOverride(c.id) ? `<button class="mini-btn" data-resetclient="${c.id}">Revert to seeded</button>` : ''}
        ${isCustomClient(c.id) ? `<button class="mini-btn danger" data-deleteclient="${c.id}">Delete</button>` : ''}
        <button class="mini-btn" data-export="1">Export shoot list</button>
      </div>
    </div>
    <div class="cb-caps">${chips}${yesno}${outcome}</div>`;
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
  return 'FILTERED';
}

/* ------------------------------------------------------------------ *
 * Feed
 * ------------------------------------------------------------------ */

function renderFeed() {
  $('feed').innerHTML = state.results
    .map((res) => {
      const p = res.post;
      const { inner, badge, flag, m, tone, dropped } = mediaHTML(res);
      const dots = p.timeline
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

    <div class="sec"><h4>Transcript</h4><p>${esc(p.transcript)}</p></div>
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
 * Tune drawer
 * ------------------------------------------------------------------ */

function renderTune() {
  const w = CONFIG.weights;
  $('tuneBody').innerHTML = `
    ${[['V', 'Virality evidence'], ['R', 'Replicability'], ['F', 'Client fit'], ['T', 'Tone fit']]
      .map(
        ([k, label]) => `
      <div class="slider">
        <label>${esc(label)} <span>${w[k].toFixed(2)}</span></label>
        <input type="range" min="0" max="0.7" step="0.01" value="${w[k]}" data-weight="${k}" />
      </div>`,
      )
      .join('')}
    <div class="slider">
      <label>Extraction gate <span>${CONFIG.gemniGateMultiplier.toFixed(0)}×</span></label>
      <input type="range" min="2" max="30" step="1" value="${CONFIG.gemniGateMultiplier}" data-gate="1" />
    </div>
    <p class="tune-note" style="margin:0">Weights are normalised to sum to 1, so moving one moves the others.</p>`;
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

  const tab = t.closest('[data-client]');
  if (tab) {
    state.clientId = tab.dataset.client;
    state.selectedId = null;
    return renderAll();
  }

  const view = t.closest('[data-view]');
  if (view) return setView(view.dataset.view);

  const dot = t.closest('.scrub-dot');
  if (dot) {
    const post = POSTS.find((p) => p.id === dot.dataset.post);
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
    CONFIG.gemniGateMultiplier = DEFAULTS.gate;
    renderTune();
    renderAll();
  }
});

document.addEventListener('input', (e) => {
  const el = e.target;

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

  const wk = el.dataset.weight;
  if (wk) {
    CONFIG.weights[wk] = +el.value;
    normaliseWeights();
    renderTune();
    renderAll();
    return;
  }
  if (el.dataset.gate) {
    CONFIG.gemniGateMultiplier = +el.value;
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
  if (e.key !== 'Escape') return;
  $('sheet').hidden = true;
  $('tune').hidden = true;
  $('editor').hidden = true;
  state.editing = null;
});

$('scorerVersion').textContent = `scorer v${SCORER_VERSION}`;
renderAll();
