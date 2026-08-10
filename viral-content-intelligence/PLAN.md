# Viral Content Intelligence System — Build Plan

**Status:** planning · **Date:** 2026-08-10 · **Source:** `viralcontentintelligencesystemfullconversation.md`

---

## 1. What this is

A pipeline that finds short-form videos which massively outperformed their own creator's
baseline, works out *why* they outperformed, and converts the mechanism into a filmable
concept for a specific restaurant client.

**Target output:** 6 filmable concepts per client per month, each with a brief the client's
crew can shoot without further interpretation.

**What it is not:** a viral-video database, a trend feed, or a copy machine. The deliverable
is a short ranked list with adaptation instructions. If it produces 200 rows of "interesting
Reels," it has failed.

### The one non-obvious idea worth protecting

From the source conversation, and easy to lose during implementation:

> The model should extract observable attributes; your own scoring engine should calculate
> the final score.

Claude and Gemini must never emit the score. They emit **facts about the video** (how many
people are on camera, is a named person required, what equipment, how many cuts). A
deterministic scorer in your code turns those facts into numbers. This is what makes the
system tunable, auditable, and improvable over time — an LLM emitting "replicability: 9/10"
is a number you can neither debug nor calibrate.

---

## 2. Decisions to lock before writing code

| # | Decision | Recommendation | Why it matters |
|---|---|---|---|
| 1 | Platforms at launch | **Instagram only** | Each platform is a separate scraper, separate baseline semantics, separate view-count definition. Add TikTok in Phase 4 once the scoring is calibrated. |
| 2 | Pilot client | **One real restaurant, named** | Client-fit scoring is untestable in the abstract. Pick the client whose crew will actually film. |
| 3 | Who curates the creator list | **A human, monthly** | See §7 — this is the real bottleneck, not the pipeline. |
| 4 | Output surface | **Markdown briefs first**, dashboard later | Next.js dashboard is Phase 4, not Phase 1. A generated brief per concept is the actual deliverable. |
| 5 | Build vs buy | **Don't build below ~8 clients** | See §9. |

---

## 3. Architecture

Five stages. Stages 1–2 are cheap arithmetic over metadata; stages 3–5 are the only ones
that cost real money, and they only ever see ~30 videos.

```
[1] INGEST        Apify → raw_posts        45 creators × ~33 posts = ~1,500 posts
       ↓                                    metadata only, no video files
[2] DETECT        per-account baselines     pure SQL/Python, no AI
       ↓          → outlier multipliers     ~1,500 → ~30 confirmed outliers
[3] EXTRACT       Gemini 2.5 Flash          transcript + structured observations
       ↓          → video_attributes        30 videos, one pass each
[4] REASON        Claude Sonnet 5           mechanism, essential vs incidental,
       ↓          → mechanism + adaptation  client-specific adaptation (top ~15)
[5] SCORE         deterministic scorer      attributes + client profile → ranked list
       ↓                                    → 6 concept briefs
```

The funnel shape is the entire cost strategy: filter with maths before you filter with
models. Never send a video to Gemini that arithmetic could have rejected.

### Stack

| Layer | Choice | Note |
|---|---|---|
| Social data | Apify (`apidojo/instagram-scraper`) | $0.47–0.50 / 1k posts, verified 2026-08-10. Normalize fields at ingest so a second actor can be swapped in. |
| Database | Postgres (Supabase) | Free tier is ample at this volume. |
| Backend | Python | |
| Video understanding | Gemini 2.5 Flash | $0.30/M in, $2.50/M out. **Not** Gemini 3.6 Flash ($1.50/$7.50) — 5× input cost for a transcription-and-observation job. |
| Reasoning | Claude Sonnet 5 (`claude-sonnet-5`) | $3/$15 per MTok ($2/$10 intro through 2026-08-31). Consider Opus 5 for the final 6 only. |
| Scheduling | Cron | n8n adds a moving part you don't need yet. |
| Output | Generated Markdown | Dashboard deferred. |

---

## 4. Data model

```
creators          id, platform, handle, external_id, niche, added_at,
                  curated_by, active, last_fetched_at

posts             id, creator_id, platform_post_id, url, posted_at, media_type,
                  duration_s, caption, audio_id, views, likes, comments, shares, saves,
                  fetched_at, raw JSONB

baselines         creator_id, media_type, computed_at, n_posts, median_views,
                  p75_views, mad            -- recomputed, never overwritten in place

outliers          post_id, baseline_id, views_normalized, outlier_multiplier,
                  confidence_lower, detected_at

video_attributes  post_id, transcript, hook_type, format, people_on_camera,
                  named_person_dependency, location_type, equipment[], edit_complexity,
                  audio_dependency, trend_half_life_days, props_cost_eur, staff_minutes,
                  visual_timeline JSONB, extracted_at, model_version

mechanisms        post_id, viral_mechanism, essential_elements[], incidental_elements[],
                  reasoned_at, model_version

clients           id, name, city, cuisine, staff_count, monthly_budget_eur,
                  capability JSONB          -- mirrors video_attributes fields

concepts          id, post_id, client_id, title, adaptation, est_cost_eur,
                  score_v, score_r, score_f, opportunity, scorer_version, created_at

outcomes          concept_id, filmed(bool), filmed_at, published_at, post_url,
                  views_at_7d, client_baseline_at_publish, performance_ratio
```

Two things to note:

- `baselines` is **append-only with a `computed_at`**. You need to know what baseline a
  post was scored against at the time, or you can never reproduce a decision.
- `outcomes` exists from day one even though nothing writes to it for months. It is the
  only table that can eventually tell you whether your scoring works, and it cannot be
  backfilled.

---

## 5. The scoring engine

This is the actual product. Everything else is plumbing.

### 5.1 Baseline

For creator `a` and media type `m`:

```
B(a, m) = median(views of the k most recent posts of type m,
                 aged ≥ M days, excluding the candidate)
```

- `k = 12`, `M = 14 days`
- **Same media type only.** Reels and carousels have completely different reach
  mechanics; mixing them produces phantom outliers.
- **Exclude the candidate** from its own baseline.
- **Median, not mean** — one prior viral post destroys a mean. (Correctly identified in
  the source conversation.)
- **Guards:** require `n_posts ≥ 8` and `B ≥ 1,000` views. Without the floor, a dormant
  account with a 200-view baseline generates a "50× outlier" every time it posts.

### 5.2 The age confound — the biggest flaw in the source model

The source conversation compares raw view counts across posts of wildly different ages.
A 3-day-old Reel and a 60-day-old Reel are not comparable measurements: views accrue
heavily in the first 48–96h and then tail for weeks. Score them against the same baseline
and you systematically **under-detect recent posts** — precisely the ones worth copying.

Two fixes:

- **MVP (do this now):** only score posts aged **14–90 days**. Simple, correct, costs you
  two weeks of recency. Acceptable — concept-to-film turnaround is a week anyway.
- **Phase 4:** estimate a growth curve `g(age)` from your own corpus (median views at age
  *d* ÷ median views at age 30d), then `views_normalized = views / g(age)`. This buys back
  the recency window. It needs ~2 months of your own collected data to fit, which is
  another reason to start collecting now.

### 5.3 Outlier multiplier

```
OM            = views_normalized / B(a, m)
OM_conservative = views_normalized / p75(baseline posts)
```

Rank on `OM_conservative`. With k=12 the median is noisy; ranking on a conservative
estimate stops you burning Gemini calls on measurement noise. Report both.

Bands (from the source, kept as-is — they're reasonable starting heuristics):
`<2×` normal · `2–5×` interesting · `5–10×` strong · `10–25×` outlier · `25–50×` major ·
`50×+` exceptional. Gate to Gemini at **≥ 8×**.

### 5.4 Attributes → scores, deterministically

Gemini and Claude fill `video_attributes`. Your code turns them into numbers. Nothing
else does.

**V — virality evidence** (log scale; 40× vs 80× is not twice as interesting):

```
V = min(1, log10(OM_conservative) / log10(50))
```

**R — replicability**, from a penalty table in a config file:

```
R = clamp(0, 1, 1 - Σ penalties)

named_person_dependency      → 0.45      edit_complexity=vfx        → 0.20
location_type=unique_venue   → 0.35      edit_complexity=heavy      → 0.10
people_on_camera > 3         → 0.15      audio=licensed_music       → 0.15
equipment ∉ client kit       → 0.20      trend_half_life < 14d      → 0.15
```

**F — client fit**, a compatibility check against `clients.capability`, not a vibe:

```
F = weighted fraction of required capabilities the client actually has
    (chef willing on camera? outdoor space? open kitchen? staff hours available?)
```

**Hard filters, applied before scoring** — these are drops, not deductions:
`est_cost_eur > monthly_budget / 6` · required capability the client lacks ·
`trend_half_life_days < days_to_film`.

**Opportunity:**

```
Opportunity = 100 × V^0.40 × R^0.35 × F^0.25
```

Weighted geometric mean. A zero in any dimension kills the concept (which is what the
source's multiplicative intent wanted), but the score stays bounded and no single factor
can swamp the others.

> **Why not the source's `V × R × F / D`:** production difficulty `D` in a denominator is
> unbounded — `D → 0` gives an infinite score — and a raw triple product of 0–10 values
> produces a distribution so skewed that ranking is dominated by noise in whichever factor
> happens to be largest. Production difficulty belongs in `R` as a penalty and in the hard
> filters as a budget ceiling, not as a divisor.

### 5.5 Calibration loop

Every score component is logged with a `scorer_version`. After ~50 filmed concepts, the
`outcomes` table gives you supervised labels: regress `performance_ratio` on
`(V, R, F, penalties)` and re-fit the weights. This is the part of the system that gets
better with age and that a competitor buying the same Apify actor cannot copy.

---

## 6. Cost model (re-verified 2026-08-10)

Per client, per month, at 1,500 posts → 30 outliers → 6 concepts.

| Stage | Basis | Cost |
|---|---|---|
| Discovery | 1,500 posts × $0.47/1k | $0.71 |
| Media fetch | 30 × ~30s videos, egress + storage | ~$0.05 |
| Gemini 2.5 Flash | 237k video-input tokens @ $0.30/M | $0.071 |
| — audio track | 28.8k audio tokens @ $1.00/M | $0.029 |
| — output | 30k structured tokens @ $2.50/M | $0.075 |
| Claude Sonnet 5 | ~60k in / 22.5k out @ $3/$15 | $0.52 |
| **Total** | | **≈ $1.45** |

At Sonnet 5's intro rate ($2/$10, through 2026-08-31) this is **≈ $1.29**. The source
conversation's $1.20–1.50 working budget holds up.

**Corrections to the source's figures:**
- Audio tokens were omitted. Gemini bills audio at $1.00/M, ~3× the video rate. Small here,
  but it scales with video length — a shift to 60s videos roughly doubles the Gemini line.
- The $2/$10 Claude rate is not a general Claude price. It is Sonnet 5's introductory rate,
  expiring 2026-08-31. Budget $3/$15 from September.
- Gemini 2.5 Flash-Lite ($0.10/$0.40) is worth benchmarking on the same 30 Reels — if
  extraction quality holds, the Gemini line drops ~3×.

**What the model still excludes:** Postgres/Supabase hosting, dashboard hosting, retry and
re-run waste (budget 1.3× on API lines), and — dominating everything — **engineering time
and creator-list curation**.

> **Stop optimizing credits.** At $1.45/client/month, a 30% saving on API spend is 44 cents.
> One hour of curation time is worth more than a year of that saving across ten clients. The
> cost work in the source conversation is finished; further optimization there is misdirected
> attention.

---

## 7. The real bottleneck: creator curation

The pipeline assumes "45 carefully selected creators." That selection *is* the product's
quality ceiling — a perfect scoring engine over a bad creator list returns nothing worth
filming. Yet nothing in the source conversation specifies how the list is built or refreshed.

**MVP:** a human builds it, per client, in a few hours: competitor restaurants in the same
cuisine and price band, restaurants in comparable cities, and 10–15 accounts outside the
niche that reliably produce food-adjacent outliers. Store `curated_by` and `added_at`.

**Phase 4 (automate the refresh, not the taste):** traverse from known-good creators —
accounts using the same audio, appearing in the same hashtags, or flagged by IG's "similar
accounts" — score candidate accounts on *baseline consistency and outlier frequency*, and
surface the top ones to a human for approval. Never auto-add.

---

## 8. Build phases

### Phase 0 — Validate the funnel by hand (week 1, no code)

The entire cost and volume model rests on two unmeasured assumptions from the source
conversation: **1 outlier per 50 videos**, and **1 filmable concept per 5 outliers**.
Test them before building anything.

1. Pick one pilot client. Hand-curate 45 creators.
2. One Apify run, 1,500 posts (~$0.71).
3. Compute baselines and outlier multipliers in a notebook.
4. A human watches the top 30 and answers: *how many of these could this specific
   restaurant actually film this month?*

**Gate:** fewer than 3 filmable → the 250:1 funnel is wrong. Either the creator list is
wrong or the ratio is, and the volume/cost model needs rebuilding before code exists.
This is a week and one dollar to de-risk a five-week build.

### Phase 1 — Ingest + detect (weeks 2–3)
Apify client with field normalization · Postgres schema · baseline computation with the
age gate · outlier detection · CLI that emits a ranked outlier CSV. **No AI in this phase.**

### Phase 2 — Extract + reason + score (week 4)
Gemini extraction into the attribute schema, using structured outputs so the JSON is
guaranteed parseable — the deterministic scorer depends on it. Claude for mechanism and
adaptation on the top ~15. Deterministic scorer with the penalty table in a YAML config.
Markdown brief generator.

Two API details worth getting right on day one:
- **Structured outputs** (`output_config.format`) on both calls. Schema-guaranteed
  attributes, no regex salvage, no retry loop.
- **Prompt caching** on the stable prefix (rubric + client capability profile) — it's
  identical across all 30 videos in a run, and cache reads are ~10% of input price.

### Phase 3 — Multi-client + operations (weeks 5–6)
Structured client-profile intake · scheduled monthly runs · outcome logging (make it
one click for whoever runs the shoot, or it will not get filled in) · Retool or Metabase
over the Postgres, not a bespoke dashboard.

### Phase 4 — Improve
Recalibrate weights from `outcomes` · fit the age-normalization curve · semi-automated
creator discovery · TikTok ingestion · Flash-Lite benchmark.

---

## 9. Build vs buy

At 1–3 clients this pipeline is not worth building. Sandcastles plus a few hours of manual
work per client produces comparable output for less than five weeks of engineering time.

Build when at least one is true:
- **≥ 8 clients** — per-client marginal cost approaches zero while manual research does not.
- **Client-fit scoring becomes the sales pitch.** "We find viral mechanisms *your kitchen
  can actually execute*" is a differentiator no off-the-shelf tool offers, because none of
  them know the client's capabilities.
- **The outcomes loop is running.** Once you can show a client that concepts scored ≥70 hit
  3× their baseline and ones below 40 don't, the score is an asset, not a heuristic.

Until then, run Phase 0 manually every month. It's ~$1 and a few hours, and it produces the
labelled data the eventual system needs.

---

## 10. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Apify actor breaks or changes schema | High — likely within months | Normalize fields at ingest behind one adapter. Keep a second actor identified. Never let raw actor field names reach the database schema. |
| View-count semantics (`play_count` vs `ig_play_count` vs "views") | Medium — silently corrupts every baseline | Pick one field, document it, assert on it at ingest. A mid-stream change invalidates historical baselines. |
| Age confound under-detects recent posts | High | §5.2 maturity gate. |
| Scoring weights are arbitrary until calibrated | Medium | Ship with the loop instrumented and treat scores as ordering hints, not truth, for the first ~50 concepts. |
| Platform ToS / GDPR | Medium — you're operating in Germany | Store aggregate metrics and post IDs; avoid retaining personal data beyond what scoring needs; don't republish scraped content. Worth a lawyer's hour before client work, not after. |
| Concept too close to the original → client brand risk | Medium | The adaptation step is a safeguard, not decoration. Claude's job is explicitly to separate the *mechanism* from the *execution* and rebuild the execution. Enforce it in review. |
| Over-engineering | High, and the most likely failure | Phase 0 gate. Markdown before dashboards. Don't build creator auto-discovery before the scoring works. |

---

## 11. Open questions

1. Which pilot client, and will their crew commit to filming the output? Without that,
   `outcomes` stays empty and the system never improves.
2. Instagram only at launch — confirmed?
3. Who owns creator curation, and how many hours per client per month are budgeted for it?
4. Internal tool or client-facing product? Changes the Phase 3 output surface entirely.
5. Start with Phase 0 (one week, ~$1, validates the funnel), or go straight to Phase 1?
