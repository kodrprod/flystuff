/** Env loading, HTTP helpers, and the on-disk corpus. */
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');

/* ---------------- env ---------------- */

/** Trim, and strip the quotes people leave behind when pasting into .env. */
const clean = (v) => String(v ?? '').trim().replace(/^["']|["']$/g, '');

export function loadEnv() {
  const p = join(ROOT, '.env');
  if (existsSync(p)) {
    for (const line of readFileSync(p, 'utf8').split('\n')) {
      if (/^\s*#/.test(line)) continue;
      const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
      if (m && !process.env[m[1]]) process.env[m[1]] = clean(m[2]);
    }
  }
  return {
    // Free path. IG_USER_ID is optional — resolved from the token on first use.
    graph: clean(process.env.IG_GRAPH_TOKEN),
    igUserId: clean(process.env.IG_USER_ID),

    // Paid, opt-in only.
    apify: clean(process.env.APIFY_TOKEN),

    anthropic: clean(process.env.ANTHROPIC_API_KEY),
    gemini: clean(process.env.GEMINI_API_KEY),
    anthropicModel: process.env.ANTHROPIC_MODEL || 'claude-opus-5',
    geminiModel: process.env.GEMINI_MODEL || 'gemini-3.5-flash',
    // 'gemini' | 'claude'. Gemini by default: it is ~20x cheaper and has a free
    // tier, which matters more here than the quality edge.
    reasoner: (process.env.REASONER || 'gemini').toLowerCase(),
    geminiFreeTier: /^(1|true|yes)$/i.test(process.env.GEMINI_FREE_TIER || ''),
    // Optional cookies.txt, only if the anonymous yt-dlp path gets throttled.
    cookiesFile: clean(process.env.IG_COOKIES_FILE),
    port: +(process.env.PORT || 4173),
  };
}

/**
 * Credentials must be present AND sendable as an HTTP header.
 *
 * The failure this exists for: the Anthropic and Google consoles display keys
 * masked with U+2022 bullets, and a masked value pasted into .env throws
 * "Cannot convert argument to a ByteString ... value 8226" from deep inside
 * fetch — which says nothing about which key or why.
 */
const HEADER_SAFE = /^[\x21-\x7E]+$/;

export function keyIssue(value, name) {
  if (!value) return `${name} is missing from .env`;
  if (/[\u2022\u00b7\u2219\u25cf*]/.test(value))
    return `${name} contains mask characters (•) — you copied the hidden version the console shows, not the real key. Keys are only shown in full once, at creation; if you've lost it, create a new one.`;
  if (!HEADER_SAFE.test(value))
    return `${name} has characters that cannot go in an HTTP header (a space, quote, newline or smart character). Re-paste it as plain text.`;
  return null;
}

const KEYS = {
  graph: 'IG_GRAPH_TOKEN',
  gemini: 'GEMINI_API_KEY',
  anthropic: 'ANTHROPIC_API_KEY',
  apify: 'APIFY_TOKEN',
};

/** Which credentials are usable — never returns the values themselves. */
export function keyStatus(env) {
  return Object.fromEntries(Object.entries(KEYS).map(([k, label]) => [k, !keyIssue(env[k], label)]));
}

export function keyIssues(env) {
  return Object.fromEntries(Object.entries(KEYS).map(([k, label]) => [k, keyIssue(env[k], label)]));
}

/** Throw a readable error before a bad key reaches fetch(). */
export function assertKey(env, which, label) {
  const issue = keyIssue(env[which], label);
  if (issue) throw new Error(issue);
}

/* ---------------- http ---------------- */

export class HttpError extends Error {
  constructor(status, body, url) {
    super(`${status} from ${url}: ${String(body).slice(0, 400)}`);
    this.status = status;
  }
}

export async function jsonFetch(url, opts = {}, { retries = 3, timeoutMs = 180000 } = {}) {
  let lastErr;
  for (let attempt = 0; attempt <= retries; attempt++) {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), timeoutMs);
    try {
      const res = await fetch(url, { ...opts, signal: ctrl.signal });
      const text = await res.text();
      if (!res.ok) {
        // 4xx other than 429 is a bad request — retrying just burns quota.
        if (res.status < 500 && res.status !== 429) throw new HttpError(res.status, text, url);
        throw Object.assign(new HttpError(res.status, text, url), { retryable: true });
      }
      return text ? JSON.parse(text) : null;
    } catch (e) {
      lastErr = e;
      const retryable = e.retryable || e.name === 'AbortError' || e.name === 'TypeError';
      if (!retryable || attempt === retries) throw e;
      await sleep(800 * 2 ** attempt);
    } finally {
      clearTimeout(timer);
    }
  }
  throw lastErr;
}

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* ---------------- corpus ---------------- */

const DATA = join(ROOT, 'data');
const CORPUS = join(DATA, 'corpus.json');

const EMPTY_CORPUS = { creators: {}, posts: [], sources: {}, runs: [] };

export function readCorpus() {
  if (!existsSync(CORPUS)) return structuredClone(EMPTY_CORPUS);
  try {
    return { ...structuredClone(EMPTY_CORPUS), ...JSON.parse(readFileSync(CORPUS, 'utf8')) };
  } catch {
    return structuredClone(EMPTY_CORPUS);
  }
}

export function writeCorpus(c) {
  mkdirSync(DATA, { recursive: true });
  writeFileSync(CORPUS, JSON.stringify(c, null, 1));
  return c;
}

/** Timestamped copy of the corpus, so a reset or bad run is never terminal. */
export function backupCorpus() {
  if (!existsSync(CORPUS)) return null;
  mkdirSync(join(DATA, 'backups'), { recursive: true });
  const name = `corpus-${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
  const dest = join(DATA, 'backups', name);
  writeFileSync(dest, readFileSync(CORPUS));
  return dest;
}

export function logRun(corpus, type, stats) {
  corpus.runs.unshift({ type, at: new Date().toISOString(), ...stats });
  corpus.runs = corpus.runs.slice(0, 60);
}
