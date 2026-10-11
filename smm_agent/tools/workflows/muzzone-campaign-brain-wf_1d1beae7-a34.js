export const meta = {
  name: 'muzzone-campaign-brain',
  description: 'Mine real evidence, design 4 competing campaigns, have persona critics try to prove each useless, synthesize one grounded campaign + generic agent plan, then audit every claim against the data files',
  whenToUse: 'When a marketing-agent output looks polished but may be useless: force evidence-grounded design and adversarial usefulness review',
  phases: [
    { title: 'Evidence', detail: '6 independent lenses over real Muzzone + peer data' },
    { title: 'Design', detail: '4 competing campaign designs from different strategic angles' },
    { title: 'Review', detail: '4 persona critics per design try to prove it useless' },
    { title: 'Synthesize', detail: 'merge winner + best grafts, re-attack, revise' },
    { title: 'Plan', detail: 'generic agent plan from what is built vs missing' },
    { title: 'Audit', detail: 'verify every factual claim against the data files' },
  ],
}

const REPO = '/home/user/flystuff/smm_agent'
const SCRATCH = '/tmp/claude-0/-home-user-flystuff/ed90e34e-b470-5816-9bae-4695c8c48b9b/scratchpad'

const CONTEXT = `
PROJECT. MetaPrompt is building an AUTONOMOUS marketing agent. Its final product, as the owner defines it: a full plan plus as much working agent as possible that CREATES MARKETING CAMPAIGNS FROM VARIOUS INPUTS. It must (1) get data (the #1 problem), (2) transform it and fit it to current trends or into content, (3) build a marketing campaign around it, (4) EXECUTE by creating videos partly with AI and partly with help of in-store workers, who have only a mediocre iPhone and about 20 MINUTES A WEEK of free time, (5) then edit everything and upload everything with AI, with no human in the creative loop. It must adapt to each client. Muzzone is the first live test, not the goal.
CLIENT. Muzzone (muzzone.kz): musical-instrument and pro-audio retailer in Astana, Kazakhstan. Russian-speaking audience. WhatsApp +7 701 0987734 is its sales channel. Website has a 535-item site-wide "Финальная распродажа" (reason and end date UNKNOWN). Only ~43% of sampled listed products are in stock, median 2 units. YouTube channel is near-dormant (last upload 2026-05-10), no TikTok link.
THE FAILURE WE MUST AVOID. A first batch of "motion-graphic price slides" was built from real photos and prices. It looks polished and the owner called it USELESS: any shop can make that in CapCut in 5 minutes; it contains no marketing judgment (no reason a specific person would watch, no story, no tie to customer questions, trends or this week's sellable stock). Do not produce more of that.
READ FIRST: ${REPO}/NOTES.md (verified facts, two experiments, honest limits). Data files are under ${REPO}/clients/muzzone/research/ and ${REPO}/experiments/. Code in ${REPO}/smm/.
HARD RULES. (a) Read-only: do NOT modify, create or delete anything under /home/user/flystuff. Scratch work only in ${SCRATCH}. (b) Never invent facts: every claim cites a file path + field/row or a URL you actually opened; if unknown say "unknown". (c) Do not contact anyone, post anything, or spend Higgsfield credits (generation tools are off-limits). (d) Raw numbers must come from code you ran (python3), not from memory. (e) Rails: AI footage may never show Muzzone's real product/people/interior as if real; no invented prices, quotes or claims; no scarcity/urgency claims the client has not made; humor must be flagged. (f) Audience-facing copy is in Russian; analysis in English.
KNOWN EVIDENCE LIMITS (do not contradict without data): a blind text judge predicts YouTube LONG-form performance (rho 0.44) but short-form only weakly (rho 0.11); title patterns like "для начинающих" and "vs" won on Muzzone long-form but did NOT replicate in 1,172 peer Shorts. So semantic CONTENT TYPE and real-world fit matter more than title tricks, and audience data must pick winners.`

const EVIDENCE_SCHEMA = {
  type: 'object',
  properties: {
    lens: { type: 'string' },
    findings: { type: 'array', items: { type: 'object', properties: {
      id: { type: 'string' }, claim: { type: 'string' },
      evidence: { type: 'array', items: { type: 'string' } },
      confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
      implication: { type: 'string' } },
      required: ['id', 'claim', 'evidence', 'confidence', 'implication'] } },
    limits: { type: 'array', items: { type: 'string' } },
    data_gaps: { type: 'array', items: { type: 'string' } },
  },
  required: ['lens', 'findings', 'limits'],
}

const LENSES = [
  { key: 'own', prompt: `LENS own-channel. Read ${REPO}/clients/muzzone/research/youtube_channel.json (371 videos with views; pos 0 = newest). Classify EVERY video by reading its title into content types you define (e.g. product demo/review by brand, head-to-head, lesson, artist interview, brand-supplied promo clip, event, other). Per type: n, median views, 2-3 example titles with views. Identify the evergreen winners and map them to products Muzzone CURRENTLY sells and has IN STOCK (use ${REPO}/clients/muzzone/research/catalog_listings.json and stock_sample.json; match by brand/model) -> a table "proven topic x available inventory". Say clearly what is search-intent product-name traffic versus feed-style content, and what does NOT transfer to short-form. Finding ids start with "own-".` },
  { key: 'peer', prompt: `LENS peer-shorts. Read ${REPO}/experiments/002_shorts_scores_and_labels.json (1,172 YouTube Shorts from 13 peer RU/UA music channels; fields: title, views, channel_median_views, duration, channel_id) and ${REPO}/clients/muzzone/research/peer_channels_meta.json (vertical: retail/review/lessons). For each channel take the top 10% and bottom 10% by views/channel_median. READ the titles and infer the underlying CONTENT TYPE of each (person talking, sound/riff test, comparison, story, joke/meme, trend/sound-driven, tutorial, unboxing, price/offer, etc.). Quantify which content types are over-represented in top vs bottom across >=3 channels and by vertical; report duration vs performance. Be explicit that your classification is a model judgement from titles only and say what cannot be concluded. Finding ids start with "peer-".` },
  { key: 'audience', prompt: `LENS audience demand and language. Use WebSearch/WebFetch (results may be weak/US-skewed; say so) to find what Russian-/Kazakh-speaking buyers actually ask and fear when choosing a first guitar, ukulele, digital piano or synth for themselves or a child; price anchors in Kazakhstan; typical objections (service, fake brands, "will my child quit", used vs new, Kaspi vs shop). Collect VERBATIM phrases with the exact URL you opened. Include which questions a shop staffer could answer on camera in 20 seconds. If a source is thin, report that rather than padding. Finding ids start with "aud-".` },
  { key: 'inventory', prompt: `LENS inventory and offer reality. Read ${REPO}/clients/muzzone/research/catalog_listings.json, stock_sample.json, products_batch001.json and (if present) ${REPO}/clients/muzzone/facts.jsonl. With python3, build inventory CLUSTERS that could anchor a campaign: category x price band x stock depth x on-sale, with counts. Identify clusters that are genuinely sellable now (in stock, qty>=2) and clusters that must NOT be promoted (mostly out of stock, e.g. acoustic guitars ~12% in stock). Quantify sale depth by category. State what the unknown "Финальная распродажа" meaning forbids us to claim. Note the sampling error (sample sizes) on every share you report. Finding ids start with "inv-".` },
  { key: 'calendar', prompt: `LENS calendar and trends for Kazakhstan, 2026-10 to 2027-01. Use WebSearch/WebFetch to find dated moments relevant to instrument buying: school/music-school start, International Music Day (Oct 1), Teachers' Day, Independence Day (Dec 16), New Year gifting, 11.11/Black Friday and Kaspi sale events, winter holidays, local concerts/festivals in Astana. Give each with date + source URL, and mark unknown/uncertain ones. Also report what is actually trending in short-form for instrument content right now (only what you can verify with URLs; otherwise say "cannot verify"). Finding ids start with "cal-".` },
  { key: 'production', prompt: `LENS production feasibility. (1) What can a non-professional shop worker shoot on an OLD iPhone in <=20 min/week that is still compelling, for a shop whose product is SOUND? Estimate minutes per format and failure modes. (2) What can AI/automation do reliably TODAY versus not: video generation, voice-over/TTS in RU/KZ, subtitles/translation, upscaling/reframing, auto-edit/jump-cuts, scheduling/publishing via TikTok/IG/YouTube APIs. Read ${REPO}/smm/*.py and ${REPO}/NOTES.md to see what is already built and its limits (Higgsfield credits are 0; the Higgsfield TikTok publish tool requires a human to submit the form; yt-dlp per-video access is bot-blocked). (3) A "what AI must never fake" list for a retailer (honesty, R5, AI labels, consent of staff on camera). Finding ids start with "prod-".` },
]

const DESIGN_SCHEMA = {
  type: 'object',
  properties: {
    name: { type: 'string' }, angle: { type: 'string' },
    objective: { type: 'object', properties: { metric: { type: 'string' }, target_hypothesis: { type: 'string' }, how_measured: { type: 'string' } }, required: ['metric', 'how_measured'] },
    audience_segments: { type: 'array', items: { type: 'object', properties: { who: { type: 'string' }, trigger: { type: 'string' }, fear: { type: 'string' }, evidence_ids: { type: 'array', items: { type: 'string' } } }, required: ['who', 'trigger', 'fear', 'evidence_ids'] } },
    core_insight: { type: 'object', properties: { statement: { type: 'string' }, evidence_ids: { type: 'array', items: { type: 'string' } } }, required: ['statement', 'evidence_ids'] },
    why_not_generic: { type: 'string' },
    four_week_arc: { type: 'array', items: { type: 'object', properties: { week: { type: 'integer' }, theme: { type: 'string' }, posts: { type: 'array', items: { type: 'object', properties: { format: { type: 'string' }, real_vs_ai: { type: 'string' }, purpose: { type: 'string' }, product_cluster: { type: 'string' }, evidence_ids: { type: 'array', items: { type: 'string' } } }, required: ['format', 'real_vs_ai', 'purpose'] } } }, required: ['week', 'theme', 'posts'] } },
    weekly_shoot_card: { type: 'object', properties: { total_minutes: { type: 'number' }, shots: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, location: { type: 'string' }, what: { type: 'string' }, seconds: { type: 'number' }, takes: { type: 'number' }, why: { type: 'string' } }, required: ['id', 'what', 'seconds', 'why'] } } }, required: ['total_minutes', 'shots'] },
    ai_pipeline: { type: 'array', items: { type: 'object', properties: { step: { type: 'string' }, tool: { type: 'string' }, input: { type: 'string' }, output: { type: 'string' }, human_needed: { type: 'string' } }, required: ['step', 'tool', 'output'] } },
    edit_recipes: { type: 'array', items: { type: 'object', properties: { format: { type: 'string' }, recipe: { type: 'string' } }, required: ['format', 'recipe'] } },
    example_videos: { type: 'array', items: { type: 'object', properties: { title: { type: 'string' }, hook_spoken_ru: { type: 'string' }, onscreen_ru: { type: 'string' }, beats: { type: 'array', items: { type: 'object', properties: { t: { type: 'string' }, visual: { type: 'string' }, spoken_ru: { type: 'string' }, onscreen_ru: { type: 'string' } }, required: ['t', 'visual'] } }, cta: { type: 'string' }, footage_needed: { type: 'string' }, ai_parts: { type: 'string' }, why_someone_watches: { type: 'string' } }, required: ['title', 'hook_spoken_ru', 'beats', 'cta', 'why_someone_watches'] } },
    experiment_arms: { type: 'array', items: { type: 'object', properties: { arm: { type: 'string' }, hypothesis: { type: 'string' }, metric: { type: 'string' } }, required: ['arm', 'hypothesis'] } },
    guardrails: { type: 'array', items: { type: 'string' } },
    risks: { type: 'array', items: { type: 'object', properties: { risk: { type: 'string' }, mitigation: { type: 'string' } }, required: ['risk', 'mitigation'] } },
    reusable_for_other_clients: { type: 'array', items: { type: 'string' } },
    muzzone_specific: { type: 'array', items: { type: 'string' } },
  },
  required: ['name', 'angle', 'objective', 'audience_segments', 'core_insight', 'why_not_generic', 'four_week_arc', 'weekly_shoot_card', 'ai_pipeline', 'edit_recipes', 'example_videos', 'experiment_arms', 'guardrails', 'risks', 'reusable_for_other_clients', 'muzzone_specific'],
}

const ANGLES = [
  { key: 'parents-first-instrument', brief: 'Segment: parents and adult beginners buying a FIRST instrument. Reduce the fear of choosing wrong and of the child quitting; make the shop the trusted guide. Respect that only some categories are actually in stock.' },
  { key: 'sound-first', brief: 'Build on the content types that actually won on Muzzone\'s own channel (real instrument sound, honest head-to-heads, search-style product questions), re-cut for short-form, with staff playing/pressing keys on an old iPhone. The product is SOUND; make the sound the hook.' },
  { key: 'clearance-with-proof', brief: 'Use the real site-wide sale and the in-stock inventory as the engine, but with PROOF and honesty instead of price slides: why this item, who it is for, what you hear/see, stock-aware drops. No urgency or closure claims the client has not made.' },
  { key: 'expert-series', brief: 'A recurring series with one or two named staff members answering REAL customer questions on camera (a human face and voice), where each episode is a decision aid and ends in a concrete in-stock recommendation.' },
]

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    persona: { type: 'string' },
    usefulness_score: { type: 'integer', minimum: 1, maximum: 10 },
    would_ship: { type: 'boolean' },
    verdict: { type: 'string' },
    refutations: { type: 'array', items: { type: 'object', properties: { claim: { type: 'string' }, why_fails: { type: 'string' }, severity: { type: 'string', enum: ['fatal', 'major', 'minor'] }, fix: { type: 'string' } }, required: ['claim', 'why_fails', 'severity', 'fix'] } },
    strongest_parts: { type: 'array', items: { type: 'string' } },
    missing_evidence: { type: 'array', items: { type: 'string' } },
  },
  required: ['persona', 'usefulness_score', 'would_ship', 'verdict', 'refutations'],
}

const PERSONAS = [
  { key: 'kz-retail-smm', desc: 'a senior social-media manager who has run WhatsApp-led retail accounts in Kazakhstan for 10 years and has seen hundreds of campaigns fail. You know what actually produces inquiries and what only produces compliments.' },
  { key: 'store-worker', desc: 'a Muzzone sales assistant in Astana with an old iPhone, no creative training, 20 free minutes a week, and shy about being on camera. You judge whether you could actually execute the shoot card and instructions tomorrow without help.' },
  { key: 'owner', desc: 'the Muzzone owner/manager: cares about sales, margin, reputation and not looking foolish; low attention span; fears anything that over-promises, misstates stock/price, or embarrasses staff. You decide whether to approve.' },
  { key: 'tiktok-native', desc: 'a 22-year-old in Astana who plays guitar casually and scrolls Shorts/TikTok daily. You decide in 1.5 seconds whether to keep watching, and whether you would ever save, share or DM. You despise ads that look like ads.' },
]

const CRITERIA = `USEFULNESS CRITERIA (score each mentally, then give one overall 1-10):
U1 Specific insight: who/why-now stated with evidence, not generic ("show prices", "post consistently").
U2 Executable: shoot card truly <= ~17 min incl. setup/retakes; instructions unambiguous for a non-professional; AI/automation steps are things tools can do TODAY (not hoped-for).
U3 Measurable: a KPI collectable with data we can actually get (WhatsApp inquiries are hard to attribute: is there an honest method?) and a decision rule.
U4 Safe/true: no invented claims, no R5 violation, stock-aware, owner-approvable.
U5 Better than baseline: clearly beats "post price slides" and "do nothing"; a human SMM manager would be impressed, not bored.
U6 Generalizable: states which parts are reusable for another client and which are Muzzone-specific.
The specific failure to hunt: output that is POLISHED BUT USELESS. Be harsh and concrete: quote the exact element you refute, say why it fails in the real world, rate severity (fatal = would not ship / would waste the 20 minutes; major = materially weakens; minor = polish) and give a concrete fix. Score 8+ only if you would genuinely ship it.`

phase('Evidence')
const evidence = (await parallel(LENSES.map(l => () =>
  agent(`${CONTEXT}\n\n${l.prompt}\n\nReturn structured findings. Prefer 6-12 high-value findings with exact evidence over many weak ones. State limits honestly.`,
        { label: `evidence:${l.key}`, phase: 'Evidence', schema: EVIDENCE_SCHEMA })))).filter(Boolean)
log(`evidence lenses returned: ${evidence.length}/${LENSES.length}; findings: ${evidence.reduce((n, e) => n + e.findings.length, 0)}`)
const evidenceJson = JSON.stringify(evidence)

phase('Design')
const designs = (await parallel(ANGLES.map(a => () =>
  agent(`${CONTEXT}\n\nYOU ARE A CAMPAIGN DESIGNER. Angle: ${a.key}. ${a.brief}\n\nDesign ONE 4-week campaign for Muzzone using ONLY the evidence below (cite finding ids; where evidence is missing say so rather than inventing). It must be executable by the workers' 20 minutes/week plus automation, and it must be something a smart SMM manager would be proud of, not a price-slide series. Include 3 fully written example videos in Russian (hook, beats with visual + spoken + on-screen text, CTA, footage needed, AI parts) and, for each, WHY a specific person would watch to the end. The weekly shoot card must sum to <= 17 minutes using this model: 2 min fixed + 1 min per location + per shot (seconds*takes/60 + 0.5 min). State how success is measured honestly given WhatsApp-led sales. Mark which parts are reusable for other clients.\n\nEVIDENCE (JSON):\n${evidenceJson}`,
        { label: `design:${a.key}`, phase: 'Design', schema: DESIGN_SCHEMA })))).filter(Boolean)
log(`designs returned: ${designs.length}/${ANGLES.length}`)

phase('Review')
const reviewed = await pipeline(designs,
  d => parallel(PERSONAS.map(p => () =>
    agent(`${CONTEXT}\n\nYOU ARE ${p.desc}\n\nAttack this campaign design. ${CRITERIA}\n\nEVIDENCE the designer had (for checking their citations):\n${evidenceJson}\n\nDESIGN UNDER REVIEW:\n${JSON.stringify(d)}`,
          { label: `review:${d.angle}:${p.key}`, phase: 'Review', schema: REVIEW_SCHEMA }))).then(rs => ({ design: d, reviews: rs.filter(Boolean) })))
const board = reviewed.filter(Boolean).map(r => ({
  angle: r.design.angle, name: r.design.name,
  mean: r.reviews.length ? r.reviews.reduce((s, x) => s + x.usefulness_score, 0) / r.reviews.length : 0,
  ship_votes: r.reviews.filter(x => x.would_ship).length,
  fatal: r.reviews.reduce((n, x) => n + x.refutations.filter(f => f.severity === 'fatal').length, 0),
  major: r.reviews.reduce((n, x) => n + x.refutations.filter(f => f.severity === 'major').length, 0),
}))
log('scoreboard: ' + JSON.stringify(board))

phase('Synthesize')
const SYNTH_RULES = `Produce the FINAL campaign design in the same schema. Pick the strongest base by scores AND by fatal/major refutations (not by eloquence), graft the best ideas from the other designs, and RESOLVE every fatal and major refutation explicitly (list them in your design's guardrails/risks with what you changed; if one cannot be resolved with available evidence, say so and mark the item as an experiment, do not hide it). Keep the shoot card <= 17 minutes by the stated model. Keep 3 fully written Russian example videos and the honest measurement method. Evidence ids must exist in the evidence.`
let final = await agent(`${CONTEXT}\n\nYOU ARE THE SYNTHESIS LEAD.\n${SYNTH_RULES}\n\nEVIDENCE:\n${evidenceJson}\n\nDESIGNS AND ALL REVIEWS:\n${JSON.stringify(reviewed.filter(Boolean))}`,
  { label: 'synthesize', phase: 'Synthesize', schema: DESIGN_SCHEMA })

let round2 = []
for (let round = 1; round <= 2; round++) {
  round2 = (await parallel(PERSONAS.map(p => () =>
    agent(`${CONTEXT}\n\nYOU ARE ${p.desc}\n\nThis is the SYNTHESIZED final campaign after one revision cycle (round ${round}). Attack it as before. ${CRITERIA}\n\nEVIDENCE:\n${evidenceJson}\n\nFINAL DESIGN:\n${JSON.stringify(final)}`,
          { label: `attack${round}:${p.key}`, phase: 'Synthesize', schema: REVIEW_SCHEMA })))).filter(Boolean)
  const fatal = round2.reduce((n, x) => n + x.refutations.filter(f => f.severity === 'fatal').length, 0)
  const major = round2.reduce((n, x) => n + x.refutations.filter(f => f.severity === 'major').length, 0)
  const mean = round2.length ? round2.reduce((s, x) => s + x.usefulness_score, 0) / round2.length : 0
  log(`round ${round}: mean=${mean.toFixed(1)} fatal=${fatal} major=${major}`)
  if (fatal === 0 && major <= 2) break
  if (round === 2) break
  final = await agent(`${CONTEXT}\n\nYOU ARE THE SYNTHESIS LEAD, REVISION PASS. Fix every fatal and major refutation below by changing the design (not by arguing). Return the full revised design in the same schema.\n\nCURRENT DESIGN:\n${JSON.stringify(final)}\n\nREFUTATIONS:\n${JSON.stringify(round2.map(r => ({ persona: r.persona, score: r.usefulness_score, refutations: r.refutations.filter(f => f.severity !== 'minor') })))}\n\nEVIDENCE:\n${evidenceJson}`,
    { label: `revise${round}`, phase: 'Synthesize', schema: DESIGN_SCHEMA })
}

phase('Plan')
const planMd = await agent(`${CONTEXT}\n\nYOU ARE THE PLAN WRITER. Read ${REPO}/NOTES.md and list ${REPO}/smm/*.py and ${REPO}/tests/*.py to see EXACTLY what is built and tested. Write the FULL PRODUCT PLAN (markdown, returned as your final text, NOT written to a file) for the autonomous campaign agent that works for ANY client, using the final Muzzone campaign below as the worked example. Required sections: 1) What the agent is and the pipeline (inputs -> insight -> campaign -> briefs -> production (AI + worker 20 min) -> edit -> publish -> measure -> learn); 2) Problem #1 DATA: ranked input sources by yield per minute of client time, how each is acquired (automated vs one-time owner action), what is blocked today and the workaround; 3) How trends/inspiration are used and their honest confidence; 4) Campaign generation method (how insight is mined and how a campaign is formed; where the model is trusted vs where audience data decides; the experiment engine); 5) Worker workflow (shoot card, iPhone rules, upload path, retake requests), with the 20-minute budget model; 6) AI production tiers and what AI must never fake; 7) Auto-edit and publishing options with their real limits (e.g. human submit in the Higgsfield TikTok form vs official APIs); 8) Measurement and learning loop (power numbers from NOTES: ~30 posts/arm for 2x effects; how to learn faster: pooling across clients, lower-variance metrics); 9) Risks/ethics/approvals (R2 hash-bound approvals, R3 offers, AI labels); 10) A table: component | status (built+tested / built untested / missing) | evidence | next step, based on what you actually find in the repo; 11) Roadmap with milestones and the blockers that need a human (accounts, credits, contact). Be candid about what is verified versus hypothesis. No filler.\n\nFINAL MUZZONE CAMPAIGN:\n${JSON.stringify(final)}\n\nREVIEW BOARD:\n${JSON.stringify(board)}`,
  { label: 'plan-writer', phase: 'Plan' })

phase('Audit')
const AUDIT_SCHEMA = {
  type: 'object',
  properties: { checked: { type: 'array', items: { type: 'object', properties: { claim: { type: 'string' }, status: { type: 'string', enum: ['verified', 'unsupported', 'contradicted'] }, evidence: { type: 'string' } }, required: ['claim', 'status', 'evidence'] } }, summary: { type: 'string' } },
  required: ['checked', 'summary'],
}
const SLICES = [
  { key: 'numbers', task: 'every NUMBER, price, count, share, stock figure and date in the design and the plan' },
  { key: 'citations', task: 'every evidence_id cited: does it exist in the evidence and does it actually support the claim it is attached to' },
  { key: 'feasibility', task: 'every step in ai_pipeline, shoot card arithmetic (recompute minutes with: 2 + 1*locations + sum(seconds*takes/60 + 0.5)), and every capability claim about tools; flag anything that needs credits/accounts/human submit that the design treats as automatic' },
]
const audits = (await parallel(SLICES.map(s => () =>
  agent(`${CONTEXT}\n\nYOU ARE AN AUDITOR. Check ${s.task}. Verify against the data files and code with python3 where numeric. Report each item as verified / unsupported / contradicted with the exact evidence. Be exhaustive on your slice.\n\nFINAL DESIGN:\n${JSON.stringify(final)}\n\nPLAN:\n${planMd}\n\nEVIDENCE:\n${evidenceJson}`,
        { label: `audit:${s.key}`, phase: 'Audit', schema: AUDIT_SCHEMA })))).filter(Boolean)
const tally = audits.flatMap(a => a.checked).reduce((t, c) => { t[c.status] = (t[c.status] || 0) + 1; return t }, {})
log('audit tally: ' + JSON.stringify(tally))

return { board, evidence, designs, reviewed, final, round2, planMarkdown: planMd, audits, tally }
