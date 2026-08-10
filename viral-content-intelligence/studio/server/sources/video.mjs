/**
 * Getting the actual mp4 for the handful of reels that reach Gemini.
 *
 * Two routes, cheapest first:
 *
 *  1. `media_url` straight off the Graph API response. Free, instant, no third
 *     party. Meta signs these and they expire in hours, so they are resolved at
 *     analysis time and never stored.
 *  2. yt-dlp against the public permalink, heavily throttled.
 *
 * Route 2 is deliberately a trickle. Measured behaviour, not caution: three
 * back-to-back unauthenticated requests from one IP succeeded, then Instagram
 * started returning empty media responses — and profile enumeration is blocked
 * outright (429 / broken extractor). That rules yt-dlp out as a bulk scraper,
 * which is exactly why listing comes from the Graph API instead. For ~30
 * finalists at one request every 20s it is fine, and it is free.
 */
import { spawn } from 'node:child_process';

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* ------------------------------------------------------------------ *
 * yt-dlp
 * ------------------------------------------------------------------ */

let ytdlpCmd = null;

/** Resolves how yt-dlp is callable here, or null. Probed once. */
export async function ytdlpAvailable() {
  if (ytdlpCmd !== null) return ytdlpCmd;
  for (const cmd of [['yt-dlp'], ['python3', '-m', 'yt_dlp']]) {
    const ok = await new Promise((resolve) => {
      const p = spawn(cmd[0], [...cmd.slice(1), '--version'], { stdio: 'ignore' });
      p.on('error', () => resolve(false));
      p.on('close', (code) => resolve(code === 0));
    });
    if (ok) return (ytdlpCmd = cmd);
  }
  return (ytdlpCmd = false);
}

function run(cmd, args, { timeoutMs = 120000 } = {}) {
  return new Promise((resolve, reject) => {
    const p = spawn(cmd[0], [...cmd.slice(1), ...args]);
    let out = '', err = '';
    const timer = setTimeout(() => { p.kill('SIGKILL'); reject(new Error('yt-dlp timed out')); }, timeoutMs);
    p.stdout.on('data', (d) => (out += d));
    p.stderr.on('data', (d) => (err += d));
    p.on('error', reject);
    p.on('close', (code) => {
      clearTimeout(timer);
      if (code !== 0) return reject(new Error(cleanYtdlpError(err)));
      resolve(out);
    });
  });
}

/** yt-dlp errors are multi-line essays; the first useful sentence is enough. */
function cleanYtdlpError(err) {
  const line = err.split('\n').find((l) => l.includes('ERROR')) || err.split('\n')[0] || 'yt-dlp failed';
  if (/empty media response|rate|429|login/i.test(line))
    return 'Instagram throttled the anonymous fetch — slow down, or supply cookies.';
  return line.replace(/^ERROR:\s*/, '').slice(0, 200);
}

/**
 * Direct mp4 URL plus whatever metadata comes free with it.
 * `duration` matters: the Graph API omits it and the cost model prices Gemini
 * per second of video.
 */
export async function resolveViaYtdlp(permalink, { cookiesFile = null } = {}) {
  const cmd = await ytdlpAvailable();
  if (!cmd) throw new Error('yt-dlp is not installed (pip3 install yt-dlp)');

  const args = ['--skip-download', '--dump-single-json', '--no-warnings', '--no-playlist'];
  if (cookiesFile) args.push('--cookies', cookiesFile);
  args.push(permalink);

  const json = JSON.parse(await run(cmd, args));
  return {
    videoUrl: json.url || json.formats?.filter((f) => f.vcodec !== 'none').pop()?.url || null,
    durationS: Math.round(json.duration || 0),
    likes: Number.isFinite(json.like_count) ? json.like_count : null,
    comments: Number.isFinite(json.comment_count) ? json.comment_count : null,
    thumbnailUrl: json.thumbnail || null,
    httpHeaders: json.http_headers || null,
  };
}

/* ------------------------------------------------------------------ *
 * Downloading
 * ------------------------------------------------------------------ */

/** Gemini inline uploads share a ~20MB request ceiling. */
const MAX_BYTES = 18 * 1024 * 1024;

async function download(url, headers) {
  const res = await fetch(url, { headers: headers || {} });
  if (!res.ok) throw new Error(`video fetch failed: ${res.status}`);
  const buf = Buffer.from(await res.arrayBuffer());
  if (!buf.length) throw new Error('video fetch returned 0 bytes');
  if (buf.length > MAX_BYTES) throw new Error(`video too large (${(buf.length / 1e6).toFixed(1)}MB)`);
  return buf;
}

/**
 * Bytes for one post, trying the free Graph URL before spending a yt-dlp
 * request against a rate limit we know is tight.
 *
 * Returns the duration too, because a post sourced from Graph has none and the
 * cost estimate is wrong without it.
 */
export async function fetchVideo(post, { cookiesFile = null } = {}) {
  const attempts = [];

  if (post.videoUrl) {
    try {
      return { buffer: await download(post.videoUrl), durationS: post.durationS || 0, via: 'graph' };
    } catch (e) {
      attempts.push(`stored url: ${e.message}`); // signed URLs expire — expected
    }
  }

  if (post.url) {
    try {
      const meta = await resolveViaYtdlp(post.url, { cookiesFile });
      if (!meta.videoUrl) throw new Error('no video stream found');
      return {
        buffer: await download(meta.videoUrl, meta.httpHeaders),
        durationS: meta.durationS || post.durationS || 0,
        via: 'yt-dlp',
        meta,
      };
    } catch (e) {
      attempts.push(`yt-dlp: ${e.message}`);
    }
  }

  throw new Error(`could not fetch video (${attempts.join('; ') || 'no url on post'})`);
}

/**
 * Serial fetch with a gap, for the finalist set.
 *
 * `gapMs` defaults to 20s because that is the cadence that survived testing.
 * Posts already carrying a fresh Graph `media_url` skip the wait entirely —
 * there is nothing to be polite to.
 */
export async function fetchVideos(posts, { gapMs = 20000, cookiesFile = null, onProgress } = {}) {
  const results = new Map();
  for (const [i, post] of posts.entries()) {
    try {
      const v = await fetchVideo(post, { cookiesFile });
      results.set(post.id, v);
      onProgress?.({ i: i + 1, n: posts.length, post, via: v.via });
      if (v.via === 'yt-dlp' && i < posts.length - 1) await sleep(gapMs);
    } catch (e) {
      onProgress?.({ i: i + 1, n: posts.length, post, error: e.message });
    }
  }
  return results;
}
