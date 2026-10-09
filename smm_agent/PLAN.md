# Plan: from here to an agent that runs clients on its own

*2026-10-09. Companion to SUMMARY.md (how it works) and HANDOFF.md (what only a human can give).*

## The weekly loop the agent runs for every client

| Day | Agent | Humans (time cap) |
|---|---|---|
| Mon | Ingest last week's metrics and WhatsApp codes, update the experiment engine, re-rank insights, generate ≥20 new ideas, select the week's slate, write the shoot card | — |
| Tue | — | Staff: one shoot, ≤20 min, from the card |
| Tue–Wed | Clean and cut footage (`edit.py`), AI motion design per video (`designer.py`), AI scenes where allowed (Higgsfield), hook variants, all checks | — |
| Wed | Send the batch for approval: one message, one tap per video (the approval is bound to the exact file hash) | Owner: ≤5 min |
| Wed–Sun | Publish on schedule (drafts until accounts are linked), pin/repost winners per the decision rules | — |
| Every day | Read WhatsApp codes; draft replies to comments for approval | Whoever answers WhatsApp: weekly export, 1 min |
| Monthly | Pool learnings across clients (`knowledge/`), re-fit rubric weights, re-calibrate the judge on our own posts | — |

## Rollout

**Phase 0: brain proven on paper (now).**
- Method v2 stress-tested on 7 requests across 5 industries; BRAIN.md written.
- `agent plan` produces a Muzzone campaign from real data.

Exit: Andrey reads one campaign and says "I would send this to the client."

**Phase 1: first real posts, MetaPrompt test account (week 1–2 after the account and credits exist).**
- 8–12 posts across ≥5 idea engines, organic only.
- The real phone test (3 clips) goes first, so that the edit chain is verified on the store phone.

Exit:
- ≥8 posts live with 48 h and 7 d metrics ingested;
- first-pass approval rate measured;
- edit chain verified on real footage.

**Phase 2: Muzzone live (weeks 3–6).** Needs the Muzzone contact, staff consent and the meaning of the sale.
- The agent introduces itself to staff as an AI assistant and sends the weekly card.
- Codes are counted from the WhatsApp export.
- Thompson allocation starts from week 3.

Exit:
- 4 consecutive weeks with the card done within 20 min;
- coded inquiries counted every week;
- owner time ≤5 min/week.

**Phase 3: clients 2–5 (from week 6).** One new client folder each: `clients/<slug>/profile.json`, a crawl into
`facts.jsonl`, the onboarding card. The same brain runs; only inputs differ. Pooled learnings start to beat neutral
priors once there are ≈30 posts per engine × vertical.

Exit: a new client goes from request to first approved batch in ≤5 working days, with ≤15 owner minutes.

## Build list (what is left, in order)

1. Align `brain.py` checks to the final method (producibility limits, diversity rules, "not an ad" gate) and run
   the 7 stress cases through the code path, not only through the workflow.
2. `agent produce`: shoot-card manifest → clips → `edit.assemble` → `designer.design_video` → checks → approval card.
   Run the designer loop end to end with the real model (not done yet).
3. `agent publish` / `agent metrics`: publish package (drafts) → metrics CSV and WhatsApp export → engine state →
   learnings. All parts exist and are tested separately; only the wiring is missing.
4. Input connectors in order of value: WhatsApp chat export parser (have), Kaspi shop/reviews, 2GIS reviews (blocked
   anonymously → owner screenshot), Instagram/TikTok insights via official APIs once accounts are linked.
5. Higgsfield: fill `knowledge/higgsfield_models.json` with real application ids once the key exists; one paid test
   per job kind with a small cap.
6. Scheduler: a weekly routine per client (Mon plan, Wed approval, daily codes) on the subscription CLI.

## KPIs the system is judged by

- **Business:** coded WhatsApp inquiries per week per client, and sales attributed where the owner logs them.
- **Agent quality:**
  - first-pass approval rate of videos by the owner (target ≥70% by week 6);
  - share of staff cards completed within 20 min;
  - owner minutes per week.
- **Learning:** P(beats median) per engine × vertical with intervals. Never "winner" without one.
- **Truth:** zero published claims without a sourced fact. Enforced in code; counted anyway.

## Main risks and what we do about them

| Risk | Mitigation |
|---|---|
| Ideas that look smart on paper do not spread | Many cheap diverse shots, audience data decides, rescue reposts with hook variants, pooled learning |
| Staff skip the card | 20-min cap enforced by the optimiser, one free shot, log which asks fail and simplify them |
| Owner never answers | Every question has a default; nothing outward-facing happens without approval (`handoff.NEVER_AUTO`) |
| Subscription usage limits | Steps park and resume (`UsageLimitError`); the API backend exists for scale |
| Platform rules (music rights on business accounts, AI labels) | Commercial-library sounds only; AI disclosure in captions where AI scenes are used |
| AI content mistaken for real product | Rule R5 in code (Higgsfield adapter refuses), labelled AI scenes only after the owner relaxes R5 |
