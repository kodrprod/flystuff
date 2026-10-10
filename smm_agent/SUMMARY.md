# MetaPrompt marketing agent: how it works (5-minute read)

*State: 2026-10-09. Branch `claude/festive-hypatia-yifkyo`, folder `smm_agent/`. Nothing has been published and no one
has been contacted.*

## What it is

You give it a client and any request from the client's boss: "make us viral", "sell pianos before New Year", "find
us a salesperson", "competitors are cheaper". It returns a campaign that can be measured, in three parts:
- the short videos to make and why each should work;
- a 20-minute shoot card for the store staff;
- what the AI makes and edits.

It then learns from real audience numbers which ideas to scale.

One command: `python -m smm.agent plan --client muzzone --request "…"`.

## 1. The brain (the part that matters most)

The brain is a written method (`brain/METHOD.md`) that the model follows step by step, plus thin code that checks
its work. Each step's output is saved as JSON, so a run is auditable and replayable.

| Step | What happens | What code checks |
|---|---|---|
| **1. Intake** | Any request is turned into a business number with a date ("so that what?" until it hits orders, units, hires or rating), a bottleneck (awareness, consideration, conversion, or a non-marketing problem such as stock or slow WhatsApp replies), **one** success metric and constraints. "Go viral" becomes "N coded WhatsApp chats a week, plus at least one post at 5× our median: likely, not guaranteed." At most 3 closed questions, each with a default; otherwise the agent assumes and writes the assumption down. | Schema; at most 3 questions |
| **2. Inputs** | Everything public is fetched first: site, prices, stock, policies, reviews, the client's own channels, peer channels. Then one owner message asks for ≤15 minutes of raw material, never opinions: a WhatsApp chat export (the richest input: real questions, objections, where chats die), what may be filmed, what sells best, 20 photos of real work. | Inventory built by code from the client folder |
| **3. Insights** | Raw material is broken into quotes and observations, tagged (fear, belief, moment, question, proof, filmable reality, …), clustered and turned into **tensions** ("I want X but fear Y, so I do Z"), in the customer's own words. Each insight is ranked on evidence, intensity, business leverage, showability, distinctiveness and whether a true proof exists. | Every evidence item must cite a ledger fact, a file or a URL, or be labelled an assumption |
| **4. Ideas** | Many ideas, written at shot level (first frame, on-screen hook, beats, payoff), from insights × ~24 idea engines (myth vs truth, blind test, "question from WhatsApp", behind the counter, close-up sound, budget tiers, POV moment, …) × behavioural drivers (stop, watch, share, save, comment, follow, convert). Trends only as packaging, and only if the idea survives without them. | Truth rails on every audience-facing string (prices, numbers, claims, phones, scarcity); staff minutes recomputed from the shot list; must cite insights |
| **5. Selection** | **Done by code, not by the model.** Rubric scores are only a prior; diversity rules and exploration slots (~25%) spread bets; audience data overrides the prior as soon as it exists. | Deterministic, tested |
| **6. Campaign** | One single-minded message, a named hero series (a repeatable "platform idea", not one big video), supporting proof/utility series, channel roles (TikTok/Reels for reach, YouTube for search, **WhatsApp for sales** with a code per video, Kaspi), calendar and phases (explore, then focus, then scale), offer rules (none unless the owner approves), decision rules. | The week's filming is cut to the real 20-minute budget by an exact optimiser; offers not on the client's site are flagged for approval |
| **7. Attack and revision** | The client's boss and a veteran CIS short-form creator attack the plan; every fatal or major point is fixed by changing the plan. | — |

**Why selection is code.** We measured it.
- A blind AI judge predicted long-form YouTube views from titles reasonably well (Spearman 0.44, n=371).
- It was nearly blind on Shorts (0.11; 0.07 for retail, n=1,172 peer Shorts).
- Title tricks that won on long-form did not replicate in Shorts.

So nobody, AI or human, reliably picks short-form winners in advance. The brain therefore maximises strong, diverse,
cheap shots on goal built on real insight, and lets the experiment engine (Thompson sampling with an exploration
floor; it never names a winner without an interval) decide what to scale. Learnings are pooled across clients
(`knowledge/`), because one shop posting 5 videos a week cannot reach statistical power alone.

**Truth is enforced in code.** Every price, number, phone or claim on screen must match a sourced fact in the
client's ledger (prices expire after 2 days). A missing fact becomes a question to the owner; the agent never
guesses. AI never depicts the client's real product, staff or customers as real.

## 2. The tools (execution)

- **Staff shoot card (Russian).** Ordered by location; fits 20 minutes including setup and retakes. It includes:
  - phone tips: mic mode not "voice isolation", the instrument 30–50 cm away, a loud amp ≥1 m, AE/AF lock;
  - "if you make a mistake, pause and repeat": the editor keeps the last take automatically.
- **Footage editor** (`edit.py`):
  - music-safe loudness: one gain per take plus a true-peak limiter, which keeps the instrument's dynamics;
  - clipping detection and stabilisation;
  - last-take pick;
  - jump-cuts so the opening seconds move;
  - outlined captions;
  - pacing checks on the first 3 seconds.
- **Motion design per video** (`htmlmotion.py`, `designer.py`). No template library. For each video an AI writes its
  own HTML/CSS/GSAP design, rendered frame-exactly in a headless browser with real Cyrillic fonts. Code reads
  every on-screen string back from the page and checks it against the facts. A critic model looks at the rendered
  frames and orders revisions.
- **AI video:** Higgsfield (generation and its editor). Credits are spent only after a decision.
- **Approval and publishing.** The owner's approval is bound to a hash of the exact video and caption, so any edit
  voids it. Publishing goes to TikTok drafts only.
- **Attribution.** Each video gets a WhatsApp code and a prefilled wa.me link. The weekly WhatsApp chat export is
  parsed to count inquiries per video.
- **Learning.** Metrics CSV → experiment engine → next week's allocation and cross-client learnings.

All judgment calls run through the `claude` CLI on the subscription, with no per-token bill. Measured cost: about
100 s and ~$0.70 of usage per brain step, so a full campaign is roughly 10 calls.

## 3. Verified vs not (honest)

| Verified | Not yet |
|---|---|
| Real Muzzone data: 49 sourced facts, catalogue, stock sample, sale page, YouTube history | No real post exists yet, so there is no audience ground truth for our own content |
| Judge calibration experiments 001/002 | Real store-phone footage through the editor (only synthetic test clips so far) |
| 117 automated tests (truth rails, selection, shoot card, editor audio and stabilisation, pacing, approvals, attribution parser, LLM client) | Higgsfield generation and editing (no SDK key or credits) |
| One brain step through the real CLI (intake for "sell pianos": it opened the stock file itself) | `designer.py` loop end to end with the real model |
| | The method itself: v1 (`brain/METHOD.md` = `brain/METHOD_v1.md`) ran through the real code on 6 requests (scores 5.5–6/10 from the boss/creator attack); v2 and `BRAIN.md` (the human-readable brain overview) are not written yet |

## 4. What the owner must provide (see HANDOFF.md)

1. A TikTok/Reels test account and Higgsfield credits plus an SDK key: the only path to real ground truth.
2. What "Финальная распродажа" means: closure, brand exit or seasonal. It changes the whole Muzzone campaign.
3. A Muzzone contact and staff consent to appear on camera (the agent introduces itself as an AI assistant).
4. A 10-minute real phone test: 3 clips with the store phone.
5. Data: a WhatsApp chat export, best sellers, account insights.
6. Decisions: a paid-boost budget (Click-to-WhatsApp), and whether AI scenes may surround real product footage.
