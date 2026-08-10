# Viral Content Studio

A working front end for the system in [`../PLAN.md`](../PLAN.md), so the scoring
and the review experience can be judged before the ingestion pipeline exists.

**What is real:** the scoring engine, the client profiles, the hard filters, the
funnel counts, both view modes, and the live weight tuning. Switching client
genuinely re-scores and re-ranks everything.

**What is stubbed:** the data. `js/data.js` holds a seeded corpus of 22 posts
across 12 creators, shaped exactly like the output the Apify → Gemini → Claude
stages are specified to produce. Swapping in the real pipeline is a data-source
change, not a rewrite.

---

## Run it

```bash
cp .env.example .env    # add your Apify / Anthropic / Gemini keys
npm start               # http://localhost:4173
```

Without `.env` the app still runs — it just stays on the seeded demo corpus and
the Sources tab tells you so. With keys, the Sources tab does the real work:

1. **Find the restaurant.** Type a name. Claude searches the web and returns
   candidates with address and Instagram handle, so you confirm *which* one
   before spending anything. Asked for "Sen Vietnamese Dresden Neustadt" it
   correctly answered that SEN is on Wilsdruffer Str. in Altstadt, and offered
   two Neustadt alternatives in case the street mattered more than the name.
2. **Build the source list.** Claude finds ~45 similar accounts — same cuisine
   nearby, same cuisine elsewhere, adjacent concepts, food creators — each with
   a reason and a confidence. Low-confidence ones start unticked.
3. **Scrape.** Apify, with the exclusions below.
4. **Analyse.** Gemini watches every reel past the gate, Claude works out the
   mechanism and adapts it for the selected client.

If you want a file you can double-click or email to someone (demo corpus only,
no server, no API):

```bash
npm run build   # -> dist/studio.html, one self-contained file, no server
```

```bash
npm run check   # scoring assertions (funnel behaviour, per-client divergence)
```

---

## What to look at

**Switch client in the header.** Bosporus (mall kebab counter) and Sen
(Vietnamese sit-down) share a corpus and agree on almost nothing:

| | Bosporus top 3 | Sen top 3 |
|---|---|---|
| 1 | €10 chef challenge | Grandmother's recipe, unchanged since 1974 |
| 2 | Cheese-pull payoff | Nonna corrects the chef |
| 3 | Weirdest order ever | Cheese-pull payoff |

That divergence is the product. The same 22 videos, two different briefs.

**Feed** is the TikTok-style review mode — vertical snap scrolling, info panel
on the right that follows whichever card you land on. Hover the dots on the
scrubber to step through the extracted hook timeline.

**Gallery** is the scanning mode — grid with the opportunity score, view count,
tone, cost and staff time under each card, plus a four-bar V/R/F/T mini
breakdown.

**Tune** opens the live weight editor. Move a slider and the ranking re-sorts
immediately. These are the numbers a normal implementation would bury in a
config file; they are exposed here because picking them is the actual work.

**Edit profile** opens the client intake form — spaces, kit, capacity, budget,
guest-consent rule, and a tone slider per register. Every field feeds `F` or
`T` directly, so a vague profile produces a vague shortlist. Zeroing a client's
comedy and challenge sliders and maxing craft and story is enough to move their
top pick from the €10 chef challenge to the cheese-pull payoff. Seeded clients
can be edited and reverted; clients you add are yours to delete.

**Log the outcome** on any concept: picked → filmed → published, plus views
after 7 days. The app divides that by the client's own median to get a
performance ratio, and the client bar shows the running median across
everything logged. This is the only input that can ever calibrate the weights
(PLAN.md §5.5), and it cannot be reconstructed later — so it is here from the
first version rather than deferred to Phase 3.

**Export shoot list** downloads the shortlist as Markdown: mechanism, the
client-specific adaptation, what must survive, what is safe to change, the
production line, and a tick-box for filmed/published/views. That file is the
actual deliverable — the app is scaffolding around producing it.

**The rejects are visible on purpose.** Dimmed cards at the bottom show what the
funnel threw away and why — a 12-day-old post that hasn't matured, a celebrity
walk-in that scores 47× and is worthless to you, a €200 drone shoot, a trend
with a 6-day half-life. Seeing the drops is how you tell whether the filters are
set correctly.

---

## Structure

```
server/index.mjs   API + static server, background jobs
server/apify.mjs   scraping, exclusions, normalisation
server/ai.mjs      Claude discovery + reasoning, Gemini extraction
server/lib.mjs     env, http retry, corpus on disk
js/scoring.js   deterministic engine — baselines, outliers, V/R/F/T, filters
js/data.js      seeded corpus + client capability profiles
js/store.js     localStorage: client edits, custom clients, outcome logs
js/app.js       UI
build.mjs       inlines everything into dist/studio.html
check.mjs       assertions over the scoring engine
```

`scoring.js` has no DOM dependency and no imports. It is meant to be ported to
Python more or less line by line when the real pipeline is built, or called
directly if the backend ends up in TypeScript.

---

## Wiring in real data

Replace the `POSTS` export in `js/data.js` with a fetch. The contract per post:

```js
{
  id, creatorId, mediaType, url, views, likes, comments, ageDays, durationS,
  caption, poster: { hue, glyph }, videoUrl,
  attributes: {                      // Gemini, structured output
    hookType, format, tone, secondaryTone,
    peopleOnCamera, chefOnCamera, customersOnCamera,
    namedPersonDependency, locationType, spaceRequired,
    equipment[], editComplexity, audioDependency,
    trendHalfLifeDays, propsCostEur, staffMinutes, cuts, avgShotLengthS
  },
  transcript, timeline: [{ t, label }],
  mechanism, essentialElements[], incidentalElements[],   // Claude
  adaptations: { [clientId]: string }                     // Claude, per client
}
```

`creators[].history` needs ~12 mature posts of the same media type per creator
for the baseline to be usable — below 8 the guard in `computeBaseline` marks it
invalid and everything from that creator is dropped.

**Video playback.** Set `videoUrl` on a post and the player swaps the poster
frame for a real `<video>` with no layout change. Any host works — a GCS bucket,
a signed Drive link, local files under `studio/media/`. Leave it `null` and you
get the gradient poster, which is enough to judge layout and pacing.

---

## Known gaps

- **Scores cluster in the 85–96 band.** With a corpus this cheap to film, `R` and
  `F` sit near 1.0 and only `V` varies, so the geometric mean compresses. The
  ordering is meaningful; the absolute number is not calibrated and should not
  be shown to clients yet. See PLAN.md §5.5 — it stays uncalibrated until the
  outcomes table has ~50 filmed concepts in it.
- **Tuned weights reset on reload.** Client profiles and outcomes persist;
  weights deliberately do not, so you always start from the committed defaults.
- **Storage is localStorage, per browser.** Nothing syncs between your laptop and
  your phone, and clearing site data wipes the outcome log. Fine for testing,
  not fine once real shoots are being tracked — that is the point at which the
  `clients` and `outcomes` tables need to move to Postgres.
- **The outcome loop is captured but not yet used.** Logged results do not feed
  back into the weights automatically; that is the regression described in
  PLAN.md §5.5 and it needs ~50 filmed concepts before it means anything.


---

## What gets excluded when scraping

Applied in `server/apify.mjs`, and reported per run in the Sources log:

| Rule | Why |
|---|---|
| `isPinned` | Pinned reels sit at the top of a profile for months and accumulate plays that have nothing to do with the reel. Confirmed live: **7 excluded from a 160-record run.** |
| `paidPartnership` | Reach was bought. The mechanism isn't transferable. |
| `productType !== 'clips'` | Not a reel. |
| No play count | Nothing to score against. |
| Not on the profile grid | Best available proxy for a trial or archived reel — see below. |

### Trial reels

**The reel actor exposes no trial flag.** `productType` was `clips` for all 47
records in your export and `isPinned` was false for every one of them. So trial
reels cannot be detected directly.

The grid cross-reference is the closest honest signal: Instagram serves trial
reels only to non-followers and does not show them on the profile grid, so a
reel present in the reel feed but absent from the grid is likely a trial (it
also catches archived reels, which you equally don't want in a baseline). Tick
**Detect unlisted / trial reels** to enable it — it costs a second Apify run per
account, which is why it is a toggle rather than always-on.

What it deliberately does *not* do is guess from engagement shape. Trial reels
have odd view-to-follower ratios; so do genuine outliers. A heuristic there
would delete exactly what the system exists to find.

---

## What the real data showed

Run against your Vietnamese-restaurant export and a live scrape, Aug 2026:

- **`videoPlayCount` is the view metric, not `videoViewCount`.** They differ by
  1.4×–118× and are not proportional. The normaliser uses `videoPlayCount` and
  keeps the other as `legacyViewCount` for reference. Mixing them across a
  baseline is silent corruption, and it is the single easiest way to make this
  whole system produce confident nonsense.
- **Creators are keyed on `ownerUsername`, never `inputUrl`.** The actor returns
  reels by *other* accounts that tagged the one you asked for — 2 of 47 in your
  export. Attributing those to the requested account puts a stranger's reach
  into its baseline.
- **`likesCount` is `-1` when likes are hidden** (9 of 47). Stored as `null`,
  not as a number.
- **Depth per account matters more than account count.** At 12 reels/account
  across 3 accounts, the best multiplier was 1.69× — nothing to analyse. At 40
  reels/account across 4 accounts, one reel cleared 8×. The default is 36.
- **Roughly 1 outlier per 47 posts**, which is close to the 1-in-50 the plan
  assumed.
