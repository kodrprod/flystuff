/**
 * Local persistence.
 *
 * Holds the three things that must survive a reload: edits to the seeded client
 * profiles, clients you add yourself, and outcome logs.
 *
 * Outcomes are the reason this file exists at all. PLAN.md §5.5 — the scoring
 * weights stay guesses until roughly 50 filmed concepts have been logged
 * against real results, and that history cannot be reconstructed after the
 * fact. Capture it from the first shoot or never.
 *
 * localStorage is obviously not the long-term home; this is the same shape the
 * `clients` and `outcomes` tables take in PLAN.md §4, so moving it to Postgres
 * is a transport change.
 */

const KEY = 'vcs.v1';

const EMPTY = { clientOverrides: {}, customClients: [], outcomes: {} };

function read() {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? { ...EMPTY, ...JSON.parse(raw) } : { ...EMPTY };
  } catch {
    return { ...EMPTY };
  }
}

function write(db) {
  try {
    localStorage.setItem(KEY, JSON.stringify(db));
  } catch {
    /* private mode / quota — the app still works, it just forgets. */
  }
}

/* ------------------------------------------------------------------ *
 * Clients
 * ------------------------------------------------------------------ */

/** Seeded clients with any local edits applied, plus any client you added. */
export function resolveClients(seeded) {
  const db = read();
  const merged = seeded.map((c) => {
    const o = db.clientOverrides[c.id];
    if (!o) return c;
    return { ...c, ...o, capability: { ...c.capability, ...(o.capability || {}) } };
  });
  return [...merged, ...db.customClients];
}

export function saveClient(client, isCustom) {
  const db = read();
  if (isCustom) {
    const i = db.customClients.findIndex((c) => c.id === client.id);
    if (i >= 0) db.customClients[i] = client;
    else db.customClients.push(client);
  } else {
    db.clientOverrides[client.id] = client;
  }
  write(db);
}

export function deleteClient(id) {
  const db = read();
  db.customClients = db.customClients.filter((c) => c.id !== id);
  delete db.clientOverrides[id];
  Object.keys(db.outcomes)
    .filter((k) => k.startsWith(`${id}:`))
    .forEach((k) => delete db.outcomes[k]);
  write(db);
}

export function isCustomClient(id) {
  return read().customClients.some((c) => c.id === id);
}

export function hasOverride(id) {
  return Boolean(read().clientOverrides[id]);
}

export function resetClient(id) {
  const db = read();
  delete db.clientOverrides[id];
  write(db);
}

/* ------------------------------------------------------------------ *
 * Outcomes
 * ------------------------------------------------------------------ */

export const OUTCOME_STATES = ['none', 'shortlisted', 'filmed', 'published'];

export function getOutcome(clientId, postId) {
  return read().outcomes[`${clientId}:${postId}`] || { status: 'none', views: null, note: '' };
}

export function setOutcome(clientId, postId, patch) {
  const db = read();
  const k = `${clientId}:${postId}`;
  db.outcomes[k] = { ...(db.outcomes[k] || { status: 'none', views: null, note: '' }), ...patch, updatedAt: Date.now() };
  write(db);
}

export function outcomesFor(clientId) {
  const db = read();
  return Object.entries(db.outcomes)
    .filter(([k]) => k.startsWith(`${clientId}:`))
    .map(([k, v]) => ({ postId: k.split(':')[1], ...v }));
}

/**
 * The number this whole system is eventually judged on: did shortlisted
 * concepts actually beat the client's own baseline once filmed?
 */
export function outcomeSummary(clientId, ownBaselineViews) {
  const all = outcomesFor(clientId);
  const filmed = all.filter((o) => o.status === 'filmed' || o.status === 'published');
  const published = all.filter((o) => o.status === 'published' && o.views > 0);
  const ratios = published.map((o) => o.views / (ownBaselineViews || 1)).sort((a, b) => a - b);
  const med = ratios.length
    ? ratios.length % 2
      ? ratios[ratios.length >> 1]
      : (ratios[(ratios.length >> 1) - 1] + ratios[ratios.length >> 1]) / 2
    : null;
  return { filmed: filmed.length, published: published.length, medianRatio: med };
}

export function exportAll() {
  return read();
}
