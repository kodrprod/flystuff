# SMM agent — working notes (read this first when resuming)

Last updated: 2026-10-08 (session on branch `claude/festive-hypatia-yifkyo`).
This folder lives inside the unrelated `flystuff` (drone sim) repo only because that
was the repo attached to the session. It should move to its own repo — see "Waiting for human".

## 1. Goal and definition of done

**Goal.** An autonomous system that runs short-video social media for MetaPrompt's
clients end to end (strategy → ideas → scripts → production → publish → metrics) with
no human in the *creative* loop, and that adapts to each client instead of copying one taste.
Muzzone (musical-instrument retailer, Astana, muzzone.kz) is the first live test, not the goal.

**"Done" for the system is checkable, in layers:**
1. *Inputs are real.* Every client fact in `clients/<slug>/facts.jsonl` has a source URL and fetch
   date; nothing simulated reaches client-facing text. (Enforced in code: `smm/facts.py`.)
2. *The judge is calibrated per scope.* Its authority (none / filter_only / rank) comes from measured
   rank correlation with real audience outcomes, with a CI, per (client, platform, format).
   (`smm/calibration.py`, experiments in `experiments/`.)
3. *Hard rails are code, not prose.* Checks that can be deterministic are (`smm/checks.py`).
4. *A script can become a video with no human and no credits* (`smm/render.py`) — proves the
   production leg exists even while generation credits are 0.
5. *Humans are asked only for what only they can do,* in one batched card, with timeouts and safe
   defaults (`smm/handoff.py`).
6. *Ground truth from real viewers.* At least one real post per format with measured +48h/+7d metrics
   feeding back into calibration. **Not met** — needs an account (see below).

Nothing is published, nothing was sent to any client or third party.

## 2. What is lost vs. kept from earlier sessions

The earlier sessions' files (protocol v2.4, `real-client-intake.md`, `pilot-design-review.md`,
121-quote corpus, F1–F20 format library, original Muzzone scrape) are **not on disk here**; the
synced `smm-system` skill is only the v2 SKILL.md. The only surviving record is the status report
pasted in the prompt. Treat that report as hearsay: any claim in it that this session did not re-verify
is marked *unverified* below. Re-deliver those files if they exist elsewhere.

## 3. Verified this session (all with source + date 2026-10-08)

**Muzzone, from muzzone.kz (public site):**
- Musical instruments + pro audio retailer, store at Астана, ул. Кажымукана 14, НП-6.
  Phones +7 (7172) 250775, +7 701 0709003; WhatsApp +7 701 0987734; info@muzzone.kz.
  Hours (phone): пн-пт 10–19, сб 10–17.
- Socials linked from site: Instagram `muzzone_astana`, YouTube channel `UC1OaV37g-nq2TmwBBlrmcJA`,
  VK `muzzoneastana`, Facebook `muzzonemusicshop`. **No TikTok link anywhere** (ownership of any TikTok: unknown).
- Returns: 14 days per ZoPP art. 30 (condition rules apply); shipping both ways + 3% withheld on COD
  for non-defective returns; **shipping cost is compensated if the buyer leaves an honest review on
  their socials or sends a video** (stated on /garantii-i-vozvrat.html). Warranty min 12 months,
  Casio 24 months (service only in Almaty, СЦ "Gagarin Records").
- Delivery: free ground delivery in Kazakhstan on orders > 100 000 ₸; Astana courier free for orders
  > 20 kg and > 15 000 ₸; order reserve 3 working days. Payments: Kaspi QR/Pay/transfer, cards, Apple Pay,
  installments ("Рассрочка") and COD advertised on product pages.
- Page hygiene problems: still says "Нур-Султан" in places; blog last post 2021.
- **"Финальная распродажа"** page: 535 SKUs, every one with an old price. Discount depth: 20% (233),
  25% (149), 30% (60), 40% (25), 50% (24), 70% (24), other 20. Brands on it include Sabian (94), Mapex (57),
  Zildjian (52), Blackstar (37), Hibilly (22). *Why* it is "final" is unknown — do not claim closure,
  end date or scarcity in content. One probable site error: Steinberg UR22mkII 70 510 → 7 051 (90% off): **do not use**.
- Catalogue (listings): digital pianos 133 (median 631 280 ₸), ukulele+accessories 163, acoustic guitars 383
  (cheapest full guitars ≈ 29–36k ₸), electric guitars 512, kids' keyboards 3. Data: `clients/muzzone/research/catalog_listings.json`.

**Muzzone YouTube (public flat listing, `youtube_channel.json`):**
- 3 620 subscribers, 379 videos (371 with counts), median 2 300 views, max 64 000
  ("CORT X100 – Электрогитара для начинающих", 147 s). Last upload 2026-05-10 → channel is near-dormant.
- Title patterns vs views (small n, correlational, 7 patterns tried — treat as hypotheses):
  beginner framing n=8 median 15 500; head-to-head "vs/сравнение/battle" n=8 median 16 000;
  Sabian/Paiste/Zildjian brand clips n=48 median 390; interviews n=4 median 118; lessons n=33 median 643.
  Newer videos do not simply get more views (Spearman −0.17), so age is not driving this.
- Instagram blocks anonymous fetch (429); VK/Facebook return HTML but not analysed. Kaspi times out; 2GIS 403.

**Tooling reality:** Higgsfield MCP connected but **0 credits, free plan, no TikTok account linked** → no
generation, no publishing possible right now. yt-dlp works for flat listings; per-video extraction from YouTube is
bot-blocked (needs cookies — not bypassing). Web search works but is US-only/weak for KZ.

## 4. Experiment 001 — can a judge predict real audience response?

Blind LLM raters (4 independent subagents, Read-only, told not to look anything up; saw title + duration +
"typical = 2 300 views"), n=371 Muzzone YouTube titles vs real views:

| metric | value |
|---|---|
| Spearman | **0.44** (95% CI 0.34–0.53) |
| pairwise accuracy, pairs with ≥3× view gap | 71% (chance 50%) |
| top-20% hit rate | 41% (chance 20%) |
| duration-only baseline | 0.25 |
| keyword rules fit *on the same data* (optimistic) | 0.49 |

Reading: the judge has real signal **on this channel's titles**; the old "no ground truth, scores just move
around" diagnosis was a data-access problem. Systematic misses: it **under-rates plain product-name titles that
win on search intent** ("Fender CD 60SCE-12" 23k views, scored 3) and **over-rates tutorial/novelty titles**
("45 гитар в одном соло" 233 views, scored 9). Limits: titles ≠ spoken hooks; YouTube search ≠ TikTok/Reels
feed; possible (small) training-data contamination; one run, no test-retest yet.
**Consequence:** authority is scoped. Granted here: `rank` for *YouTube long-form titles, Muzzone*. **Not** granted
for short-form hooks until calibrated on short-form data.

## 5. Decisions (and why)

- D1. Calibrate on **public outcomes** (the client's own channel, then peer channels) instead of waiting for
  the owner's past videos. Cheap, real, and per-vertical, which is what "adapts to each client" needs.
- D2. Judge authority is **scope-tagged and expires**; the system, not the model's confidence, decides what the
  judge may do.
- D3. Treat the site's existing sale as an **already-published offer** (source: the live page) instead of
  inventing offers a silent owner will reject. Still no end-dates/scarcity claims. R3 for *new* offers unchanged.
- D4. Store provenance on every fact; `simulated` provenance is blocked from external text in code.
- D5. Don't publish anything, contact anyone, or spend credits without a human decision (outward-facing/irreversible).

## 6. Dead ends / bugs found (don't repeat)

- Listing parser glued SKU digits onto prices (→ "100% discount"); fixed by per-line regex; pinned by tests.
- `top_fraction_hit_rate` returned NaN for a flat judge; fixed with expected-value tie handling.
- `pkill -f <pattern>` matched my own shell → killed it. Use the PID.
- yt-dlp per-video metadata on YouTube: "confirm you're not a bot" → use flat listings + RSS only.
- First web search guessed the wrong business: fetch the client's own domain first.

## 7. Waiting for human (batched — see HANDOFF.md)

Owner of each is Andrey unless noted. Work continues meanwhile.
1. A TikTok (and/or IG Reels) **test account owned by MetaPrompt** + Higgsfield credits → only way to get real
   short-form ground truth and to test the render→publish leg. Without it nothing can be published.
2. Real Muzzone contact (via Pavel) and whether "Финальная распродажа" is a closure / brand exit / seasonal.
3. Whether Muzzone owns a TikTok; who may be filmed; scope of the contract.
4. Where this project should live (own repo?).

## 8. Next steps

1. facts ledger + deterministic checks + tests (in progress)  2. short-form calibration set from peer channels
3. renderer (script→mp4, zero credits)  4. first Muzzone batch on real facts, built on proven winners, not published
5. handoff queue with escalation / safe defaults  6. update protocol (v3) + sync to skill.
