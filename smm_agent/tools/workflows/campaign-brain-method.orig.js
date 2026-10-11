export const meta = {
  name: 'campaign-brain-method',
  description: 'Design and stress-test the agent brain: inputs -> insight -> high-chance viral ideas -> campaign, for any client and any boss request; apply it to Muzzone with real data',
  whenToUse: 'When the core marketing method of an autonomous campaign agent must be designed and proven robust across clients and request types',
  phases: [
    { title: 'Draft methods', detail: '5 experts from different schools draft the full method' },
    { title: 'Synthesize', detail: 'one method v1' },
    { title: 'Stress test', detail: 'apply v1 to 7 very different boss requests' },
    { title: 'Attack cases', detail: 'boss + veteran creator attack each output' },
    { title: 'Revise method', detail: 'fix failure patterns across all cases' },
    { title: 'Re-test', detail: 'hardest cases again with v2' },
    { title: 'Muzzone', detail: 'apply v2 to Muzzone with real data, attack, revise' },
    { title: 'Write BRAIN.md', detail: 'final method + schemas + worked example' },
  ],
}

const REPO = '/home/user/flystuff/smm_agent'
const SCRATCH = '/tmp/claude-0/-home-user-flystuff/ed90e34e-b470-5816-9bae-4695c8c48b9b/scratchpad'

const GOAL = `
THE PRODUCT. MetaPrompt is building an autonomous marketing agent that serves MANY local businesses (any industry) in Kazakhstan/CIS. For each client and for ANY kind of request from the client's boss (vague like "make us viral", specific like "sell product X by date Y", or not even sales-related like "find us a salesperson"), the agent must: (1) know which INPUTS it needs and get them with minimal owner time; (2) extract what matters from them (facts, customer language, fears, desires, proof, moments, constraints); (3) turn that into HIGH-CHANCE short-video ideas (Reels/TikTok/Shorts) - ideas that people stop for, watch, share, save, comment on - not ads; (4) design a marketing CAMPAIGN around the strongest ideas that achieves the boss's real objective and is measurable; (5) hand execution to tools (AI video, editing, publishing) and to in-store workers who have ONE weak phone (good audio only when held close) and ~20 MINUTES A WEEK. The owner of MetaPrompt says: "if you can do the inputs-to-ideas-to-campaign part really well for any client and any request, everything else is just using tools." This is the part we are designing now.
HARD-WON EVIDENCE (do not contradict): a blind LLM judge predicted LONG-form YouTube performance from titles (Spearman 0.44) but SHORT-form performance only weakly (0.11 overall; 0.07 for retail, CI includes 0) across 1,172 peer Shorts; title tricks that won on long-form ("для начинающих", "vs") did NOT replicate in Shorts. So nobody (including you) can reliably predict virality from text: a good method maximises the number of strong, diverse, cheap shots on goal built on real insight, and lets audience data pick and scale winners (an experiment engine exists: Thompson allocation over arms; ~30 posts per arm for 80% power on a 2x effect, so pooling across clients and fast cheap variants matter). Also learned: polished motion-graphic "price slides" were judged useless; truth matters (no invented prices, claims, urgency); sales in this market often happen in WhatsApp chats (we attribute with per-video WhatsApp codes) and on Kaspi.
RULES. Read-only: never create/modify/delete files under /home/user/flystuff (scratch only in ${SCRATCH}). Never invent facts about real businesses; hypothetical cases must label assumptions. Audience-facing copy in Russian; everything else in English. Be concrete and operational (steps, rules, examples, failure modes), no generic marketing platitudes, no filler.`

const METHOD_SPEC = `Write the COMPLETE METHOD as instructions an AI agent will follow, in markdown, with these sections:
A. Request intake: how to turn ANY boss request into a business objective, a marketing objective, a success metric and constraints; how to handle vague, unrealistic ("go viral"), conflicting or non-sales requests; the maximum 3 clarifying questions and when to assume instead of asking.
B. Inputs: the full list of inputs the agent needs, ranked by value per minute of owner time; for each: what exactly to extract from it, how to obtain it (automated vs owner action), and what the agent does if it is missing.
C. Working the inputs: the transformation from raw inputs to an evidence base and then to INSIGHTS (customer tensions, beliefs, moments, proof assets, content-able realities of the business); how to rank insights; how to keep facts true.
D. Idea generation for high-chance short videos: the psychological drivers of stopping, watching, sharing, saving and commenting; idea engines / angle generators that work across industries; how to generate MANY diverse ideas from insights x drivers x formats x trends; how to adapt to platform trends without chasing irrelevant ones; what makes ideas producible with one weak phone + 20 min + AI; anti-patterns (ads, price slides, childish engagement bait, fake urgency).
E. Idea selection: an explicit scoring rubric used as a PRIOR (not a prediction), diversity rules, and how many variants to produce and test.
F. Campaign design: how to build a campaign around the best ideas (hero series / big idea, supporting content, offer if needed and approved, funnel and channel roles incl. WhatsApp and optional paid boost, calendar, worker asks, AI parts, measurement and decision rules, learning loop across weeks and across clients).
G. Output contract: the exact structured objects the agent produces at each step (intake brief, input checklist, evidence base, insight list, idea list with scores, test plan, campaign) - field by field.
H. Worked mini-example for one local business.`

const DRAFTERS = [
  { key: 'strategist', who: 'a brand strategist who builds campaigns on sharp consumer insight and positioning (planner school: tensions, truths, single-minded proposition)' },
  { key: 'viral-creator', who: 'a creative director who has made dozens of viral short-form videos for local businesses and knows the mechanics of hooks, formats, trends, sounds, remixes, comments and shares' },
  { key: 'growth', who: 'a growth/performance marketer obsessed with measurable outcomes, funnels, testing velocity, attribution in WhatsApp-led markets, and cheap paid boosts of proven organic winners' },
  { key: 'behavioral', who: 'a behavioural scientist of sharing and attention (STEPPS, curiosity gap, social currency, identity, emotion/arousal, practical value, narrative transportation) who turns research into operational rules' },
  { key: 'cis-operator', who: 'an operator who has run social media for small businesses in Kazakhstan/CIS on tiny budgets: shy staff, bad phones, WhatsApp/Kaspi sales, owners with no time, Russian/Kazakh audiences' },
]

const CASES = [
  { key: 'muzzone-viral', client: 'Muzzone, musical-instrument and pro-audio shop in Astana (site muzzone.kz; sells via WhatsApp; ~43% of listed items in stock; a site-wide "Финальная распродажа" of unknown reason; dormant YouTube whose best video was a beginner-guitar demo at 64k views; no TikTok)', request: '"Сделайте нас вирусными в TikTok."' },
  { key: 'muzzone-pianos', client: 'Muzzone (as above). Digital pianos in stock, e.g. Casio PX-770 695 913 ₸ (3 units), Casio AP-270 734 886 ₸ (5 units); ~56% of sampled digital pianos in stock', request: '"Нужно продать цифровые пианино до Нового года."' },
  { key: 'muzzone-hiring', client: 'Muzzone (as above)', request: '"Нам нужен продавец-консультант. Найдите через соцсети."' },
  { key: 'dental', client: 'HYPOTHETICAL: a private dental clinic in Almaty (assume: 6 chairs, 2 implant surgeons, Instagram 3k followers, prices above average, patients fear pain and cost; medical advertising rules apply)', request: '"Нужно больше пациентов на импланты."' },
  { key: 'coffee', client: 'HYPOTHETICAL: a specialty coffee shop in Astana with one location (assume: loyal regulars, 2.1k Instagram followers, baristas aged 20-25 willing to be filmed)', request: '"Через 3 недели открываем вторую точку на Левом берегу. Нужен ажиотаж."' },
  { key: 'b2b', client: 'HYPOTHETICAL: a construction-materials supplier in Karaganda selling to contractors and companies (assume: warehouse, delivery trucks, 40 SKUs of dry mixes and insulation, owner skeptical of social media)', request: '"Мы продаём только компаниям. Нам вообще нужны соцсети?"' },
  { key: 'salon', client: 'HYPOTHETICAL: a mid-price beauty salon in Shymkent (assume: 8 masters, competitors nearby are 30% cheaper, good reviews on 2GIS, owner wants to keep prices)', request: '"Конкуренты дешевле, клиенты уходят. Что делать?"' },
]

const CASE_SCHEMA = {
  type: 'object',
  properties: {
    intake: { type: 'object', properties: { business_objective: { type: 'string' }, marketing_objective: { type: 'string' }, success_metric: { type: 'string' }, constraints: { type: 'array', items: { type: 'string' } }, reframed_request: { type: 'string' }, clarifying_questions: { type: 'array', items: { type: 'string' } }, assumptions: { type: 'array', items: { type: 'string' } } }, required: ['business_objective', 'marketing_objective', 'success_metric', 'reframed_request'] },
    inputs_needed: { type: 'array', items: { type: 'object', properties: { input: { type: 'string' }, how: { type: 'string' }, owner_minutes: { type: 'number' }, extract: { type: 'string' } }, required: ['input', 'how', 'extract'] } },
    insights: { type: 'array', items: { type: 'object', properties: { insight: { type: 'string' }, source: { type: 'string' }, tension: { type: 'string' } }, required: ['insight', 'source'] } },
    ideas: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, title: { type: 'string' }, hook_ru: { type: 'string' }, what_happens: { type: 'string' }, driver: { type: 'string' }, why_share_or_save: { type: 'string' }, production: { type: 'string' }, worker_minutes: { type: 'number' }, prior_score: { type: 'number' } }, required: ['id', 'title', 'hook_ru', 'what_happens', 'driver', 'why_share_or_save', 'production', 'prior_score'] } },
    selected: { type: 'array', items: { type: 'string' } },
    test_plan: { type: 'string' },
    campaign: { type: 'object', properties: { name: { type: 'string' }, big_idea: { type: 'string' }, structure: { type: 'string' }, offer: { type: 'string' }, channels: { type: 'string' }, calendar: { type: 'string' }, worker_asks_week1_ru: { type: 'string' }, ai_parts: { type: 'string' }, measurement: { type: 'string' }, decision_rules: { type: 'string' } }, required: ['name', 'big_idea', 'structure', 'channels', 'calendar', 'worker_asks_week1_ru', 'measurement', 'decision_rules'] },
    method_friction: { type: 'array', items: { type: 'string' } },
  },
  required: ['intake', 'inputs_needed', 'insights', 'ideas', 'selected', 'test_plan', 'campaign', 'method_friction'],
}

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    persona: { type: 'string' },
    score: { type: 'integer', minimum: 1, maximum: 10 },
    would_approve: { type: 'boolean' },
    best_idea: { type: 'string' },
    refutations: { type: 'array', items: { type: 'object', properties: {
      target: { type: 'string' }, why_fails: { type: 'string' },
      severity: { type: 'string', enum: ['fatal', 'major', 'minor'] },
      method_cause: { type: 'string' }, fix: { type: 'string' } },
      required: ['target', 'why_fails', 'severity', 'method_cause', 'fix'] } },
  },
  required: ['persona', 'score', 'would_approve', 'refutations'],
}

const critics = (c) => [
  { key: 'boss', desc: `the BOSS of this business (${c.client}) who made the request ${c.request}. You judge: does this actually solve MY problem, would I approve it, is it worth my staff's time and my money, is anything risky, embarrassing or untrue` },
  { key: 'creator', desc: 'a veteran short-form creator and SMM in Kazakhstan/CIS who has made many videos go viral for local businesses and knows instantly which ideas are generic, ad-like, unproducible with a bad phone in 20 minutes, or will not spread; you also judge whether the campaign would produce real inquiries' },
]

phase('Draft methods')
const drafts = (await parallel(DRAFTERS.map(d => () =>
  agent(`${GOAL}\n\nYOU ARE ${d.who}.\n${METHOD_SPEC}\nBring your school's sharpest tools, but write for an AI agent that must work for ANY client and ANY request. Return ONLY the markdown.`,
        { label: `draft:${d.key}`, phase: 'Draft methods' })))).filter(Boolean)
log(`method drafts: ${drafts.length}/${DRAFTERS.length}`)

phase('Synthesize')
const v1 = await agent(`${GOAL}\n\nYOU ARE THE HEAD OF STRATEGY. Five experts from different schools drafted the method. Synthesize ONE method (v1) that keeps the sharpest, most operational parts of each, resolves their conflicts explicitly (say which rule wins and why), and removes anything generic or unverifiable. Same section structure:\n${METHOD_SPEC}\n\nDRAFTS:\n${drafts.map((d, i) => `===== DRAFT ${i + 1} (${DRAFTERS[i] ? DRAFTERS[i].key : 'x'}) =====\n${d}`).join('\n\n')}\n\nReturn ONLY the markdown of method v1.`,
  { label: 'synthesize-v1', phase: 'Synthesize' })

const runCase = (method, c, tag) => agent(`${GOAL}\n\nYOU ARE THE AGENT. Apply the METHOD below strictly and literally to this case. Where the method is unclear, missing or forces something silly, still produce the best output but record the friction in method_friction (this is a stress test of the method).\nCLIENT: ${c.client}\nBOSS REQUEST: ${c.request}\nProduce: intake, the inputs you would need (and how), insights (mark assumed ones), at least 12 diverse ideas with Russian hooks and prior scores, the selected ideas, a test plan, and the campaign incl. week-1 worker asks in Russian (one weak phone, close sound, 20 minutes).\n\nMETHOD:\n${method}`,
  { label: `${tag}:${c.key}`, phase: tag === 'case' ? 'Stress test' : 'Re-test', schema: CASE_SCHEMA })

const attackCase = (out, c, tag) => parallel(critics(c).map(cr => () =>
  agent(`${GOAL}\n\nYOU ARE ${cr.desc}.\nAttack this output. For every weakness: name the target, why it fails in the real world, severity (fatal = you would reject it / it wastes the staff's time / it will not spread or convert; major; minor), the METHOD CAUSE (which step or rule of the method produced the weakness), and a fix to the METHOD (not only to this output). Also name the single best idea. Score 1-10 (8+ only if you would approve it as is).\n\nCLIENT: ${c.client}\nREQUEST: ${c.request}\nOUTPUT:\n${JSON.stringify(out)}`,
        { label: `${tag}-attack:${c.key}:${cr.key}`, phase: tag === 'case' ? 'Attack cases' : (tag === 'muzzone' ? 'Muzzone' : 'Re-test'), schema: REVIEW_SCHEMA })))
  .then(rs => ({ case: c.key, output: out, reviews: rs.filter(Boolean) }))

phase('Stress test')
const round1 = (await pipeline(CASES, c => runCase(v1, c, 'case'), (out, c) => attackCase(out, c, 'case'))).filter(Boolean)
const scoreOf = r => r.reviews.length ? r.reviews.reduce((s, x) => s + x.score, 0) / r.reviews.length : 0
const board1 = round1.map(r => ({ case: r.case, mean: +scoreOf(r).toFixed(1), fatal: r.reviews.reduce((n, x) => n + x.refutations.filter(f => f.severity === 'fatal').length, 0), approve: r.reviews.filter(x => x.would_approve).length }))
log('round 1: ' + JSON.stringify(board1))

phase('Revise method')
const failures = round1.map(r => ({ case: r.case, friction: r.output.method_friction, refutations: r.reviews.flatMap(x => x.refutations.filter(f => f.severity !== 'minor').map(f => ({ persona: x.persona, ...f }))), best_ideas: r.reviews.map(x => x.best_idea) }))
const v2 = await agent(`${GOAL}\n\nYOU ARE THE HEAD OF STRATEGY. Method v1 was stress-tested on ${round1.length} very different cases and attacked by each business's boss and a veteran creator. Revise it into method v2: find the FAILURE PATTERNS across cases (not one-off complaints), change the method's rules/steps so they cannot recur, keep what worked (see the ideas critics called best), and keep it operational for an AI agent. Mark every change with "(v2: why)". Same section structure.\n\nMETHOD v1:\n${v1}\n\nSCOREBOARD:\n${JSON.stringify(board1)}\n\nFAILURES AND FRICTION BY CASE:\n${JSON.stringify(failures)}\n\nReturn ONLY the markdown of method v2.`,
  { label: 'revise-v2', phase: 'Revise method' })

phase('Re-test')
const hardest = [...board1].sort((a, b) => a.mean - b.mean).slice(0, 3).map(b => CASES.find(c => c.key === b.case)).filter(Boolean)
const round2 = (await pipeline(hardest, c => runCase(v2, c, 'retest'), (out, c) => attackCase(out, c, 'retest'))).filter(Boolean)
const board2 = round2.map(r => ({ case: r.case, mean: +scoreOf(r).toFixed(1), fatal: r.reviews.reduce((n, x) => n + x.refutations.filter(f => f.severity === 'fatal').length, 0), approve: r.reviews.filter(x => x.would_approve).length, before: (board1.find(b => b.case === r.case) || {}).mean }))
log('re-test: ' + JSON.stringify(board2))

phase('Muzzone')
const MUZ = { key: 'muzzone-real', client: `Muzzone, Astana. USE THE REAL DATA: read ${REPO}/NOTES.md and the files in ${REPO}/clients/muzzone/research/ (catalog_listings.json, stock_sample.json, products_batch001.json, youtube_channel.json, peer_channels_meta.json) and ${REPO}/experiments/002_shorts_scores_and_labels.json. Cite real facts; mark unknowns; never invent prices or stock.`, request: '"Мы хотим больше продаж через соцсети. У сотрудников есть телефон и 20 минут в неделю."' }
const muzOut = await agent(`${GOAL}\n\nYOU ARE THE AGENT. Apply METHOD v2 strictly to the REAL client below, using the real data files (run python3 to read them where useful). This output will be shown to the owner tomorrow, so it must be specific to Muzzone's actual stock, prices, policies, channel history and audience - not generic. At least 20 diverse ideas, then select, test plan, and a 4-week campaign with a fully written week-1 worker card in Russian (one weak phone, close sound, 20 minutes, minute count).\nCLIENT: ${MUZ.client}\nBOSS REQUEST: ${MUZ.request}\n\nMETHOD v2:\n${v2}`,
  { label: 'muzzone-apply', phase: 'Muzzone', schema: CASE_SCHEMA })
const muzRev = await attackCase(muzOut, MUZ, 'muzzone')
const muzFinal = await agent(`${GOAL}\n\nYOU ARE THE AGENT. Revise the Muzzone output: fix every fatal and major refutation (by changing the output, not arguing), keep it true to the real data, keep the same schema.\n\nOUTPUT:\n${JSON.stringify(muzOut)}\n\nCRITIQUES:\n${JSON.stringify(muzRev.reviews)}\n\nMETHOD v2:\n${v2}`,
  { label: 'muzzone-revise', phase: 'Muzzone', schema: CASE_SCHEMA })

phase('Write BRAIN.md')
const brainMd = await agent(`${GOAL}\n\nYOU ARE THE HEAD OF STRATEGY. Write the final BRAIN.md: the agent's marketing method (from METHOD v2, tightened), followed by: (1) a one-page overview a busy owner can read in 3 minutes (inputs -> what we get -> how we work them -> ideas -> campaign -> learning), placed FIRST; (2) the exact output objects as JSON schemas (intake brief, input checklist, evidence base, insight, idea, test plan, campaign) that code can validate; (3) what the stress test showed (scores before/after, which request types are hardest and how the method handles them); (4) the Muzzone worked example summarised (top insights, top 5 ideas with hooks, campaign skeleton, week-1 worker card). Be honest about what is hypothesis vs evidence. Return ONLY the markdown.\n\nMETHOD v2:\n${v2}\n\nSTRESS TEST round 1: ${JSON.stringify(board1)}\nRE-TEST with v2: ${JSON.stringify(board2)}\n\nMUZZONE FINAL OUTPUT:\n${JSON.stringify(muzFinal)}`,
  { label: 'brain-md', phase: 'Write BRAIN.md' })

return {
  brain_md: brainMd, method_v1: v1, method_v2: v2,
  board1, board2,
  muzzone_scores: muzRev.reviews.map(r => ({ persona: r.persona, score: r.score, would_approve: r.would_approve, best_idea: r.best_idea })),
  muzzone: muzFinal,
  cases: round1.map(r => ({ case: r.case, output: r.output, reviews: r.reviews.map(x => ({ persona: x.persona, score: x.score, best_idea: x.best_idea })) })),
}
