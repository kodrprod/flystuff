#!/usr/bin/env node
/**
 * Turns the one-hour token the Graph API Explorer hands you into a 60-day one,
 * then proves it works before you paste it into .env.
 *
 *   node get-token.mjs <app-id> <app-secret> <short-lived-token>
 *
 * The verification matters more than the exchange. A token can be valid and
 * still useless here — wrong scopes, or no Instagram account linked to the Page
 * — and both of those fail later with an error that says nothing useful.
 *
 * Nothing is written to disk and the token is only ever printed to your own
 * terminal. Add it to .env yourself, under `umask 077`.
 */
import { resolveSelf } from './server/sources/graph.mjs';

const [appId, appSecret, shortToken] = process.argv.slice(2);

if (!appId || !appSecret || !shortToken) {
  console.error(`
  Usage: node get-token.mjs <app-id> <app-secret> <short-lived-token>

  app-id / app-secret  developers.facebook.com → your app → Settings → Basic
  short-lived-token    developers.facebook.com/tools/explorer → Generate Access Token

  See SETUP-FREE.md for the full walkthrough.`);
  process.exit(1);
}

const API = 'https://graph.facebook.com/v23.0';

const fail = (msg, hint) => {
  console.error(`\n  ✗ ${msg}`);
  if (hint) console.error(`    ${hint}`);
  process.exit(1);
};

console.log('\n  Exchanging for a long-lived token…');

const url =
  `${API}/oauth/access_token?grant_type=fb_exchange_token` +
  `&client_id=${encodeURIComponent(appId)}` +
  `&client_secret=${encodeURIComponent(appSecret)}` +
  `&fb_exchange_token=${encodeURIComponent(shortToken)}`;

const res = await fetch(url).then((r) => r.json()).catch((e) => ({ error: { message: e.message } }));

if (res.error) {
  const m = res.error.message || 'exchange failed';
  fail(m,
    /Invalid OAuth access token|expired/i.test(m)
      ? 'The short-lived token has already expired — generate a fresh one and retry immediately.'
      : /client_secret|client_id/i.test(m)
        ? 'Check the app id and secret under Settings → Basic.'
        : null);
}

const token = res.access_token;
if (!token) fail('No token came back', JSON.stringify(res).slice(0, 200));

const days = res.expires_in ? Math.round(res.expires_in / 86400) : 60;
console.log(`  ✓ Long-lived token issued — valid ~${days} days.`);

console.log('\n  Verifying it can actually read Instagram…');
let accounts;
try {
  accounts = await resolveSelf(token);
} catch (e) {
  fail(e.message,
    /No Instagram Business account/.test(e.message)
      ? 'The token works, but no IG account is linked to a Page. See step 2 of SETUP-FREE.md.'
      : 'Re-generate the token with instagram_basic, pages_show_list, pages_read_engagement and business_management.');
}

console.log(`  ✓ Can act as ${accounts.length} Instagram account${accounts.length === 1 ? '' : 's'}:`);
for (const a of accounts) console.log(`      @${a.username}  (page "${a.pageName}", ig id ${a.igUserId})`);

console.log(`
  Add it to studio/.env:

    umask 077
    printf 'IG_GRAPH_TOKEN=%s\\n' '${token}' >> .env
    printf 'IG_USER_ID=%s\\n' '${accounts[0].igUserId}' >> .env

  Then restart the server. Do not paste this token into a chat or a commit.
`);
