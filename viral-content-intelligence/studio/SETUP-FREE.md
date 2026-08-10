# Running this for free

The pipeline needs exactly **one** credential you don't already have: an
Instagram Graph API token. It costs nothing, it is the official API, and it
replaces the Apify scraper that spent your €5.

Budget about 15 minutes, once. The token then lasts 60 days and is renewable.

---

## What each key is for

| Key | Needed? | Cost | What it does |
|---|---|---|---|
| `IG_GRAPH_TOKEN` | **yes** | free | Lists competitors' reels + likes/comments |
| `GEMINI_API_KEY` | **yes** | free tier, or ~$0.005/video | Watches the videos, writes the adaptations |
| `ANTHROPIC_API_KEY` | no | ~$0.03/video | Better adaptations. Set `REASONER=claude` to use it |
| `APIFY_TOKEN` | no | $2.60 per 1,000 reels | Only if the Graph API can't reach an account |

yt-dlp is used to download the finalists' video files. It's free and needs no
key: `pip3 install yt-dlp`.

---

## Getting `IG_GRAPH_TOKEN`

The API only reads **public Business and Creator accounts**, and it has to be
called *from* an Instagram account you control. Any of your clients' accounts
works — you're not reading their data, you're using their account as the
vantage point.

### 1. Make sure the account is a Business or Creator account

Instagram app → Settings → Account type and tools → Switch to professional
account. A personal account cannot call this API.

### 2. Connect it to a Facebook Page

Instagram app → Settings → Account type and tools → Sharing to other apps →
Facebook. If the client has no Page, create an empty one — it never has to be
used or published.

### 3. Create a Meta app

1. Go to <https://developers.facebook.com/apps> → **Create app**
2. Use case: **Other** → type: **Business**
3. In the app dashboard, add the **Instagram Graph API** product

### 4. Generate a token

1. Open the [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Pick your app in the top-right dropdown
3. Click **Generate Access Token** and log in as the account that manages the Page
4. Add these four permissions:
   - `instagram_basic`
   - `pages_show_list`
   - `pages_read_engagement`
   - `business_management`
5. Copy the token

That token expires in about an hour. Make it last 60 days:

```bash
node studio/get-token.mjs <app-id> <app-secret> <short-lived-token>
```

It prints a long-lived token, verifies it against the API, and shows which
Instagram accounts it can act as.

### 5. Save it

```bash
cd studio
umask 077
printf 'IG_GRAPH_TOKEN=%s\n' 'EAAG...' >> .env
```

`.env` is gitignored. Never paste a token into a chat, an issue, or a commit.

Restart the server and the Sources tab should show
**Instagram Graph API — free · as @yourhandle**.

---

## What this changes about the numbers

The free API does not return play counts. Instagram only exposes those for
accounts you own. So outlier detection ranks on **likes + comments** instead.

This matters less than it sounds, because every score is a *ratio against the
same account's own median* — the unit cancels out. Checked against your own
165-reel corpus, which happens to carry both metrics, the two rank the same
reels: **5 of the top 8 are identical**, and engagement actually finds slightly
*more* candidates (45 scoreable vs 41).

One real consequence: engagement multipliers are **compressed**, because likes
saturate where plays don't. A reel with 40× the plays might show 8× the likes.
That's why the fixed 8× gate is gone — see below.

---

## Why you now get 6 concepts instead of 2

The old gate analysed anything above 8× its account's median. On your corpus
that was 1 reel. The problem was never the threshold, though — it was depth:

```
account                reels  mature  usable baseline?
cafe_milchmaedchen        40      37  yes
sonaleipzig               36      32  yes
vacay_leipzig             35      32  yes
sfizio_dresden            30      28  yes
...9 more                1-12    1-12  no — too few reels
```

Only **4 accounts** had enough history to say what "normal" looked like for
them. The other nine were mostly strangers who'd tagged the target account.
Four accounts is not enough to find six outliers, at any threshold.

Two changes fix it:

1. **The shortlist is now "the best N reels", not "anything above 8×".** N is
   both the quality dial and the entire cost ceiling, and it can never come back
   empty. The app tells you what multiplier the cut landed on.
2. **Depth is free now.** 40 accounts × 50 reels ≈ 2,000 reels for $0.00. On the
   observed rate that's roughly 130 candidates above 1.5×, which is plenty for a
   top-30 shortlist and 6 surviving concepts.

If you still come up short, the funnel's **"short of 6 — why?"** chip filters the
dataset to exactly the reels that failed, and says whether it was the data or
the client's constraints.

---

## What a month costs now

| Step | Platform | Cost |
|---|---|---|
| Find the restaurant | Gemini | ~$0.01 |
| Find 45 similar accounts | Gemini | ~$0.02 |
| Fetch 40 accounts × 50 reels | Instagram Graph API | **$0.00** |
| Download 30 videos | yt-dlp | **$0.00** |
| Analyse 30 videos | Gemini | ~$0.23 |
| **Total** | | **~$0.26** |

On the Gemini free tier it's **$0.00**, just slower. Set `GEMINI_FREE_TIER=1`
so the cost panel stops quoting you paid rates.

For comparison, the same run through Apify: **$18.80**.

---

## Optional settings

```bash
REASONER=claude          # better adaptations, ~$0.03/video. Default: gemini
GEMINI_FREE_TIER=1       # you're on the free tier — show $0.00, throttle
IG_USER_ID=17841400000   # skips one lookup per run
IG_COOKIES_FILE=/path/cookies.txt   # only if yt-dlp gets throttled
```

### If yt-dlp starts failing

Instagram rate-limits anonymous downloads. Measured: about three back-to-back
requests succeed, then it starts returning empty responses. The app already
spaces requests 20 seconds apart, which is enough for a 30-video run.

If it still fails, export cookies from a logged-in browser session with a
cookies.txt extension and point `IG_COOKIES_FILE` at the file. Use a throwaway
Instagram account, not a client's — automated access can get an account
restricted.

---

## Troubleshooting

**"No Instagram Business account is linked to this token"**
Step 2 didn't take. In Meta Business Suite, confirm the Instagram account is
connected to the Page, then regenerate the token.

**"@x: no such account, or it is personal/private"**
`business_discovery` only reads public Business/Creator accounts. Personal and
private ones are invisible to it. Expect roughly a third of any discovered list
to fail this way — ask for more accounts than you need.

**"Access token expired"**
Long-lived tokens last 60 days. Re-run `get-token.mjs`.

**"Rate limited by Instagram"**
The limit is ~200 calls/hour. One account at 50 reels is one call. If you're
fetching 200+ accounts in an hour, split it across two runs.
