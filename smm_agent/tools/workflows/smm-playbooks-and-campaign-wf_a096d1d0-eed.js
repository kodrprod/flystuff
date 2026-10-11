export const meta = {
  name: 'smm-playbooks-and-campaign',
  description: 'Write the agent\'s strong instructions (marketing, worker asks, AI editor, reviewer) with expert drafters, attack each with the people it affects, revise, then build and attack a Muzzone campaign under real constraints',
  whenToUse: 'When an autonomous marketing agent needs its judgment encoded as instructions rather than hard-wired templates',
  phases: [
    { title: 'Draft', detail: '4 expert drafters, one playbook each' },
    { title: 'Attack', detail: 'critics from the people each playbook affects' },
    { title: 'Revise', detail: 'address every fatal/major critique' },
    { title: 'Campaign', detail: 'Muzzone 4-week campaign from the revised playbooks' },
    { title: 'Campaign attack', detail: 'owner, worker, KZ SMM, viewer try to prove it useless' },
    { title: 'Campaign revise', detail: 'final campaign' },
  ],
}

const REPO = '/home/user/flystuff/smm_agent'
const SCRATCH = '/tmp/claude-0/-home-user-flystuff/ed90e34e-b470-5816-9bae-4695c8c48b9b/scratchpad'

const CONTEXT = `
WHAT WE ARE BUILDING. An autonomous marketing agent for MetaPrompt's clients (local businesses; first client: Muzzone, a musical-instrument and pro-audio shop in Astana, Kazakhstan, Russian-speaking, sells through WhatsApp +7 701 0987734, site muzzone.kz). From various inputs it gets data, turns it into insight, fits it to trends or content, builds a marketing campaign, and executes it: short vertical videos made partly by AI and partly from footage shot by in-store workers, then edited and uploaded by AI, with no human in the creative loop except: (a) the workers' capture and (b) the owner's approval before anything is published.
HARD REALITY (owner's words, non-negotiable):
- Workers have ONE not-so-good phone. Video and audio quality are poor. Audio is only good when the phone is held CLOSE to the instrument (20-30 cm). They have about 20 MINUTES A WEEK for anything we ask.
- Editing must be done by AI that understands psychology: how the text looks and feels, what makes a viewer stop and stay. NOT hard-wired templates (they break and look generic; a first batch of motion-graphic price slides was judged "looks good but useless").
- The agent runs via the claude CLI on a subscription (token-frugal). Higgsfield (video-native AI: generation, editing workflows, voice, dubbing, upscaling) is the chosen AI video vendor, via its Python SDK and editing workflows; credits are currently 0 (assume they will be bought).
ARCHITECTURE DECISION (already made): AI decides (idea, hook, moments, text and its feeling, pacing) under strong written playbooks; a video-native AI executes styled edits/enhancement/voice/dubbing; thin code guardrails stay: exact rendering of facts (prices, phone, WhatsApp codes - generative video garbles Cyrillic text), audio physics (clipping/loudness measured; a naive normalisation flattened a 21.6 dB musical dynamic to 0), truth rules (no invented prices/claims/scarcity; AI never shows the real product/people as if real without approval and labels), owner approval bound to the exact file, WhatsApp code attribution. Audience data (experiment engine) decides winners, not taste: a blind text judge predicted long-form YouTube views (rho 0.44) but short-form only weakly (rho 0.11, retail 0.07).
EVIDENCE YOU CAN USE (details and sources in ${REPO}/NOTES.md - read it): Muzzone's own YouTube (3,620 subs, 371 videos, median 2,300 views, dormant since 2026-05-10): top video "CORT X100 - Электрогитара для начинающих" 64k; real product demos and head-to-heads won, brand cymbal clips (median 390) and interviews (118) flopped. Site: 535-item "Финальная распродажа" (reason unknown - never claim closure/urgency), ~43% of sampled products in stock (median 2 units; acoustic guitars ~12% in stock, digital pianos ~56%, sale list ~72%); 14-day returns; warranty 12 months min (Casio 2 years, service only in Almaty); free delivery over 100 000 ₸; pickup reserve 3 working days; Kaspi QR/Pay; the returns page compensates return shipping for an honest review/video from the buyer (an existing UGC mechanic). In-stock examples with real prices: Alston AS-100BK electric guitar 59 800 ₸ (11 in stock), Caesar U-246 concert ukulele 22 100 ₸ (4), Casio PX-770 695 913 ₸ (3), Casio AP-270 734 886 ₸ (5), Hibilly Retro 30R amp 56 576 ₸ (was 70 720, 2 in stock), Mapex Comet kit 283 296 ₸ (was 354 120, 1). Product data: ${REPO}/clients/muzzone/research/*.json. Existing code you may reference by name: smm/formats.py (format library), smm/attribution.py (WhatsApp codes like KT27 typed in Cyrillic still match), smm/shootcard.py (20-minute budget model: 2 min fixed + 1 min per location + per shot seconds*takes/60 + 0.5), smm/checks.py (truth rails), smm/experiments.py (Thompson allocation; ~30 posts per arm needed for 80% power on a 2x effect).
RULES FOR YOU: read-only (never create/modify/delete files under /home/user/flystuff; scratch only in ${SCRATCH}); never invent facts (cite NOTES.md / data files or say unknown); do not contact anyone or spend Higgsfield credits; audience-facing copy in Russian, everything else in English. Be concrete: rules, examples, numbers, failure modes. No filler, no generic marketing platitudes.`

const PLAYBOOKS = [
  { key: 'marketing', title: 'Marketing brain playbook',
    expert: 'a performance and brand marketer who has grown local retailers in Kazakhstan/CIS that sell through WhatsApp and Kaspi, and who thinks in buyer psychology, offers and measurable inquiries',
    brief: `How the agent must think as a marketer for ANY local client, step by step: business diagnosis (purchase type, decision journey, where the sale actually happens), buyer segments with their real fears/triggers, the single insight a campaign rests on, positioning versus alternatives (marketplaces, grey imports), offer design (and when an offer needs owner approval), funnel roles of content, channel roles (Instagram, TikTok, YouTube Shorts and search, WhatsApp, paid Click-to-WhatsApp as an option with budget approval), how to turn existing client mechanics into content (e.g. Muzzone's review-for-shipping compensation), measurement with WhatsApp codes, and anti-patterns (price slides, generic "post consistently", invented urgency). Include decision rules and a worked Muzzone example. End with the exact INPUTS the agent needs per client and how to get each with minimal owner time.`,
    critics: [
      { key: 'kz-retail-smm', desc: 'a senior SMM who has run WhatsApp-led retail accounts in Kazakhstan for 10 years and knows what produces inquiries versus compliments' },
    ] },
  { key: 'worker', title: 'Worker-asks playbook (20 minutes, one weak phone)',
    expert: 'a field producer who has trained shop staff with cheap phones to capture usable content in minutes, with a sound engineer\'s ear for close-miking acoustic and electric instruments on phone mics',
    brief: `How the agent writes the weekly request to workers: what to ask (a close-up shot vocabulary that turns the weak phone's only strength - close sound and close detail - into the content: hands on strings/keys at 20-30 cm, one-sentence selfie-distance lines, detail shots), what never to ask (wide shots, long talking heads, anything far from the mic), how to fit 6-10 tasks into 20 minutes by location, phone settings that matter on a cheap iPhone/Android (mic mode, resolution, focus/exposure lock, lens), loud-amp/drum distance to avoid clipping, the retake protocol (pause 2 s, repeat the whole line - the editor keeps the last take), consent for anyone on camera, how to send the clips, and how retake requests are phrased when a clip fails (clipped, too dark, too quiet). Write it so a shy, untrained worker can follow it in Russian. Include a complete example weekly card in Russian for Muzzone using real in-stock products, with a minute count by the budget model.`,
    critics: [
      { key: 'store-worker', desc: 'a Muzzone sales assistant with an old phone, no creative training, 20 free minutes a week, shy on camera; you judge whether you could follow this tomorrow without help' },
      { key: 'sound-engineer', desc: 'a live-sound and recording engineer who knows exactly what a phone mic does with a guitar amp, a digital piano speaker, an acoustic guitar body and a drum kit at different distances' },
    ] },
  { key: 'editor', title: 'AI editor playbook (psychology of short-form editing)',
    expert: 'a top short-form editor and creative director who has cut thousands of Reels/TikToks/Shorts for retail and music brands and can explain WHY each cut and each word on screen works',
    brief: `The instructions an AI editor follows to turn the workers' weak, close-up phone clips (plus optional AI voice-over, AI atmosphere b-roll that never fakes the real product, and exact fact overlays) into short videos people watch and act on. Cover: the first second (what the first frame must show, sound-first openings for instruments), hook mechanics (curiosity gap, specific number, tension of a buying question) and when each fits; pacing for weak footage; music-specific rules (never cut mid-phrase, let the riff breathe, never lay music under an instrument demo); TEXT PSYCHOLOGY - what on-screen text is for, how many words, word choice and tone in Russian (spoken, not ad voice), size/weight/contrast/position in the platform safe zone, timing per word, emphasis, what text must never do; captions vs headline text; when to use AI voice-over; KZ-language versions; the end card and WhatsApp-code CTA; what the editor must hand to code for exact rendering (prices, phone, codes); how the editor reviews its own draft from frames and a transcript before handing it to the owner; and the OUTPUT the editor must produce: a precise edit decision list (segments with source clip, in/out seconds, purpose, on-screen text with timing and style intent, voice-over lines, b-roll requests, audio notes) that either Higgsfield's editing workflow or a simple executor can carry out. Include one fully worked example EDL for a Muzzone sound-demo video.`,
    critics: [
      { key: 'tiktok-native', desc: 'a 22-year-old in Astana who plays guitar casually and scrolls Shorts/TikTok daily; you decide in 1.5 seconds whether to keep watching and despise ads that look like ads' },
      { key: 'senior-editor', desc: 'a senior human editor who would be replaced by this AI editor; you know every way an AI edit looks cheap, robotic or tone-deaf, especially Russian on-screen text' },
    ] },
  { key: 'reviewer', title: 'Reviewer/critic playbook (no polished-but-useless output)',
    expert: 'a demanding creative and growth reviewer who has killed many beautiful but ineffective campaigns, and who insists on evidence and measurable outcomes',
    brief: `The instructions for the agent's internal critic that reviews every campaign, brief and edited draft BEFORE the owner sees it: the usefulness rubric (specific insight with evidence; executable in 20 minutes with one weak phone; measurable via WhatsApp codes; true and stock-aware; clearly better than price slides and doing nothing; reusable vs client-specific), the persona panel it must simulate (owner, worker, local SMM, target viewer) and how to aggregate their votes, severity levels and what blocks shipping, how it reviews a video draft from frames + transcript + audio measurements (since it cannot hear), how it avoids rewarding eloquence over substance, and how its verdicts are calibrated later against real post results (it is a filter, not a judge of winners). Include a filled example review of a weak draft and a strong one.`,
    critics: [
      { key: 'skeptic-analyst', desc: 'a skeptical analyst who checks whether a review process can actually be followed by an AI, whether it is calibrated against data, and whether it will just rubber-stamp' },
    ] },
]

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    persona: { type: 'string' },
    score: { type: 'integer', minimum: 1, maximum: 10 },
    would_use: { type: 'boolean' },
    refutations: { type: 'array', items: { type: 'object', properties: {
      quote: { type: 'string' }, why_fails: { type: 'string' },
      severity: { type: 'string', enum: ['fatal', 'major', 'minor'] }, fix: { type: 'string' } },
      required: ['quote', 'why_fails', 'severity', 'fix'] } },
    missing: { type: 'array', items: { type: 'string' } },
  },
  required: ['persona', 'score', 'would_use', 'refutations'],
}

const REVISED = await pipeline(PLAYBOOKS,
  pb => agent(`${CONTEXT}\n\nYOU ARE ${pb.expert}.\nWrite the "${pb.title}" as a markdown document the agent will follow literally as its instructions.\n${pb.brief}\nReturn ONLY the markdown document.`,
              { label: `draft:${pb.key}`, phase: 'Draft' }),
  (draft, pb) => parallel(pb.critics.map(c => () =>
      agent(`${CONTEXT}\n\nYOU ARE ${c.desc}.\nAttack this playbook. Find every place where following it literally would produce useless, fake-looking, unexecutable, untrue or unmeasurable results. Quote the exact passage, say why it fails in the real world, rate severity (fatal = would waste the 20 minutes or publish something bad; major = materially weakens; minor = polish) and give a concrete fix. Score 1-10 (8+ only if you would genuinely use it).\n\nPLAYBOOK "${pb.title}":\n${draft}`,
            { label: `attack:${pb.key}:${c.key}`, phase: 'Attack', schema: REVIEW_SCHEMA })))
    .then(reviews => ({ draft, reviews: reviews.filter(Boolean) })),
  (dr, pb) => agent(`${CONTEXT}\n\nYOU ARE ${pb.expert}.\nRevise your playbook "${pb.title}". Resolve EVERY fatal and major refutation by changing the text (not by arguing); apply minor ones where cheap. Where a refutation cannot be resolved with available evidence, say so explicitly in the document as an open question or an experiment. Return ONLY the full revised markdown.\n\nYOUR DRAFT:\n${dr.draft}\n\nCRITIQUES:\n${JSON.stringify(dr.reviews)}`,
              { label: `revise:${pb.key}`, phase: 'Revise' }).then(text => ({ key: pb.key, title: pb.title, text, reviews: dr.reviews })))

const books = REVISED.filter(Boolean)
log(`playbooks revised: ${books.map(b => b.key).join(', ')}`)
const booksText = books.map(b => `===== ${b.title} =====\n${b.text}`).join('\n\n')

const CAMPAIGN_SCHEMA = {
  type: 'object',
  properties: {
    name: { type: 'string' },
    objective: { type: 'string' },
    insight: { type: 'string' },
    evidence: { type: 'array', items: { type: 'string' } },
    segments: { type: 'array', items: { type: 'object', properties: { who: { type: 'string' }, fear_or_trigger: { type: 'string' }, message: { type: 'string' } }, required: ['who', 'fear_or_trigger', 'message'] } },
    offer: { type: 'object', properties: { proposal: { type: 'string' }, needs_owner_approval: { type: 'boolean' }, why: { type: 'string' } }, required: ['proposal', 'needs_owner_approval', 'why'] },
    channels: { type: 'array', items: { type: 'object', properties: { channel: { type: 'string' }, role: { type: 'string' } }, required: ['channel', 'role'] } },
    measurement: { type: 'string' },
    weeks: { type: 'array', items: { type: 'object', properties: {
      week: { type: 'integer' }, theme: { type: 'string' },
      worker_card_ru: { type: 'string' }, worker_minutes: { type: 'number' },
      posts: { type: 'array', items: { type: 'object', properties: {
        id: { type: 'string' }, format: { type: 'string' }, arm: { type: 'string' }, product: { type: 'string' },
        hook_ru: { type: 'string' }, why_watch: { type: 'string' },
        edit_plan: { type: 'string' }, onscreen_text_ru: { type: 'array', items: { type: 'string' } },
        voiceover_ru: { type: 'string' }, caption_ru: { type: 'string' }, cta_ru: { type: 'string' },
        ai_parts: { type: 'string' }, footage_from_card: { type: 'array', items: { type: 'string' } } },
        required: ['id', 'format', 'arm', 'hook_ru', 'why_watch', 'edit_plan', 'onscreen_text_ru', 'caption_ru', 'cta_ru', 'footage_from_card'] } } },
      required: ['week', 'theme', 'worker_card_ru', 'worker_minutes', 'posts'] } },
    experiment_arms: { type: 'array', items: { type: 'object', properties: { arm: { type: 'string' }, hypothesis: { type: 'string' } }, required: ['arm', 'hypothesis'] } },
    risks: { type: 'array', items: { type: 'string' } },
    open_questions_for_owner: { type: 'array', items: { type: 'string' } },
  },
  required: ['name', 'objective', 'insight', 'evidence', 'segments', 'offer', 'channels', 'measurement', 'weeks', 'experiment_arms', 'risks', 'open_questions_for_owner'],
}

phase('Campaign')
let campaign = await agent(`${CONTEXT}\n\nYOU ARE THE AGENT, following the playbooks below literally. Build Muzzone's first 4-week campaign. Week 1 must be fully specified (worker card in Russian with a minute count by the budget model, <=17 min; every post with hook, why someone watches, edit plan in the editor playbook's terms, exact on-screen texts, caption, WhatsApp-code CTA, which card footage it uses, AI parts). Weeks 2-4 may be lighter but concrete. Use only in-stock products and facts from the evidence; mark anything needing owner approval. Experiment arms must be explicit so audience data can choose.\n\nPLAYBOOKS:\n${booksText}`,
  { label: 'campaign', phase: 'Campaign', schema: CAMPAIGN_SCHEMA })

const CAMPAIGN_CRITICS = [
  { key: 'owner', desc: 'the Muzzone owner/manager: cares about sales, margin, reputation, not looking foolish; fears over-promising, wrong prices/stock, embarrassing staff; low attention' },
  { key: 'store-worker', desc: 'the Muzzone sales assistant with one weak phone and 20 minutes; you judge the week-1 card line by line' },
  { key: 'kz-retail-smm', desc: 'a senior Kazakhstan retail SMM who knows what produces WhatsApp inquiries' },
  { key: 'tiktok-native', desc: 'a 22-year-old guitarist in Astana scrolling Shorts; you judge each week-1 hook and whether you would stop, watch, save or message' },
]
phase('Campaign attack')
const cReviews = (await parallel(CAMPAIGN_CRITICS.map(c => () =>
  agent(`${CONTEXT}\n\nYOU ARE ${c.desc}.\nAttack this campaign. Hunt especially for POLISHED BUT USELESS: things that look smart but would not produce inquiries, could not be executed with one weak phone in 20 minutes, or are untrue/not in stock. Quote, explain, rate severity, fix. Score 1-10.\n\nCAMPAIGN:\n${JSON.stringify(campaign)}`,
        { label: `campaign-attack:${c.key}`, phase: 'Campaign attack', schema: REVIEW_SCHEMA })))).filter(Boolean)
const fatal = cReviews.reduce((n, r) => n + r.refutations.filter(f => f.severity === 'fatal').length, 0)
const major = cReviews.reduce((n, r) => n + r.refutations.filter(f => f.severity === 'major').length, 0)
log(`campaign attack: mean score ${(cReviews.reduce((s, r) => s + r.score, 0) / Math.max(1, cReviews.length)).toFixed(1)}, fatal ${fatal}, major ${major}`)

phase('Campaign revise')
const finalCampaign = await agent(`${CONTEXT}\n\nYOU ARE THE AGENT. Revise the campaign: resolve every fatal and major refutation by changing it; keep the same schema; keep week 1 fully specified; list anything unresolved as an open question for the owner or as an experiment.\n\nCAMPAIGN:\n${JSON.stringify(campaign)}\n\nCRITIQUES:\n${JSON.stringify(cReviews)}\n\nPLAYBOOKS:\n${booksText}`,
  { label: 'campaign-revise', phase: 'Campaign revise', schema: CAMPAIGN_SCHEMA })

return {
  playbooks: books.map(b => ({ key: b.key, title: b.title, text: b.text,
    review_scores: b.reviews.map(r => ({ persona: r.persona, score: r.score, fatal: r.refutations.filter(f => f.severity === 'fatal').length, major: r.refutations.filter(f => f.severity === 'major').length })) })),
  campaign_v0_scores: cReviews.map(r => ({ persona: r.persona, score: r.score, would_use: r.would_use })),
  campaign: finalCampaign,
}
