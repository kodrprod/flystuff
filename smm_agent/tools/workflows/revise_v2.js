export const meta = {
  name: 'brain-method-v2',
  description: 'Diagnose 8 real stress-test runs of the marketing brain back to method rules, revise the method to v2, attack v2 from two lenses, finalise',
  whenToUse: 'After smm.stress has produced run folders for method v1',
  phases: [
    { title: 'Diagnose', detail: 'one analyst per stress case: failures -> method cause / code cause' },
    { title: 'Revise', detail: 'method v2 from cross-case failure patterns' },
    { title: 'Attack v2', detail: 'pattern-coverage lens + model-operability lens' },
    { title: 'Finalise', detail: 'patch v2 with the attacks' },
  ],
}

const REPO = '/home/user/flystuff/smm_agent'
const RUNS = args.runs            // folder with one sub-folder per case + board.json
const CASES = args.cases          // [{key, client, request, real}]
const V1 = `${REPO}/brain/METHOD_v1.md`

const CONTEXT = `CONTEXT. MetaPrompt's autonomous marketing agent turns ANY boss request for ANY local business (Kazakhstan/CIS) into a measurable short-video campaign: intake -> inputs -> evidence+insights -> ideas -> (code) selection -> campaign -> boss + veteran-creator attack -> one revision. The model follows the METHOD (${V1}) as its system prompt at every step; code (${REPO}/smm/brain.py) validates schemas, enforces truth rails, recomputes staff minutes, selects the slate, assigns WhatsApp codes and writes the staff shoot card. Constraints of the real world: staff have ONE weak phone (good sound only within ~30 cm) and 20 minutes a week; owners give <=15 min at onboarding and <=5 min/week; nobody can predict short-form winners from text (measured: Spearman 0.07-0.11), so many diverse, cheap, true shots on goal + audience data decide.
RULES: read-only on ${REPO} (do not edit files). Be concrete: quote the run's actual output when you criticise it. Everything in English except quoted Russian.`

const DIAG = {
  type: 'object',
  properties: {
    case: { type: 'string' },
    verdict: { type: 'string' },
    would_a_real_boss_use_it: { type: 'boolean' },
    best_part: { type: 'string' },
    failures: { type: 'array', items: { type: 'object', properties: {
      what: { type: 'string' }, evidence: { type: 'string' },
      severity: { type: 'string', enum: ['fatal', 'major', 'minor'] },
      cause: { type: 'string', enum: ['method', 'code', 'inputs', 'model_noncompliance'] },
      method_section: { type: 'string' }, fix: { type: 'string' } },
      required: ['what', 'evidence', 'severity', 'cause', 'method_section', 'fix'] } },
    code_issues: { type: 'array', items: { type: 'string' } },
  },
  required: ['case', 'verdict', 'would_a_real_boss_use_it', 'best_part', 'failures', 'code_issues'],
}

phase('Diagnose')
const diags = (await parallel(CASES.map(c => () => agent(
  `${CONTEXT}\n\nYOU ARE a senior strategist auditing ONE real run of the agent. Case "${c.key}": client ${c.client}${c.real ? ' (REAL client, real data in ' + REPO + '/clients/' + c.client + ')' : ' (HYPOTHETICAL client, profile in ' + REPO + '/stress/clients/' + c.client + '/profile.json, empty facts ledger)'}; boss request ${JSON.stringify(c.request)}.\nRead every file in ${RUNS}/${c.key}/ (intake, inputs, insights, ideas, selection, campaign, reviews, reviews_after, checks, questions, campaign.md, shoot_card_week1_ru.txt if present) and the case log ${RUNS}/${c.key}.log. Skim ${V1} sections you need.\nJudge it as the boss and as a top short-form strategist would: does it solve the real problem, are the ideas genuinely likely to be watched/shared/saved (not ads, not generic), are they producible by one weak phone in 20 minutes, is everything true, is it measurable, are the owner questions few and sharp?\nFor every failure: quote the evidence, give severity, and the CAUSE: 'method' (a rule of the method produced it or failed to prevent it - name the section), 'code' (schema/check/selection code did it - say what), 'inputs' (data missing - say whether the agent could have fetched it), or 'model_noncompliance' (the method was clear but ignored). Give a concrete fix (a rule change, not advice). If the run did not finish, diagnose what exists and say where it stopped.`,
  { label: `diagnose:${c.key}`, phase: 'Diagnose', schema: DIAG })))).filter(Boolean)
log(`diagnosed ${diags.length}/${CASES.length}`)

const KNOWN = `PATTERNS THE OPERATOR ALREADY CONFIRMED ACROSS RUNS (address each explicitly in v2):
1. Owner overload: 12-15 asks per owner (boss critics: "a real owner answers 2 of them, late, by voice note"). Code now caps the owner card at 7 items / 15 minutes (<=3 clarifying questions + ranked asks + ONE facts item) and routes staff asks to the staff card. v2 must make the model rank asks so the first 4 unlock week 1, and never split one ask into many.
2. Hero content deferred to "NEXT BATCH" because facts were missing -> week 1 had only weak ideas (salon: fatal). v2: week 1 must be producible from facts already usable or from content that needs no facts; fact-dependent ideas go to week 2+.
3. Honesty and privacy: a chat-export ask promised "наружу ничего не попадает" although an AI assistant processes it; a template had the admin sign as the master; dental used medical-record data for marketing messages. v2: every owner/staff/customer message says an AI assistant (MetaPrompt) is involved; no impersonation; no use of health or customer records for outreach without explicit consent; minimal personal data.
4. Price evasion in price-led categories (dental implants, pianos, salon): content that never shows a price loses buyers whose first question is "сколько?". v2: get the price list early (highest-value owner ask) and use honest "от X ₸" / range formats backed by facts.
5. Distribution realism: a new account in one city gets mostly non-local views; B2B buyers search 2GIS/Satu, not feeds; musicians arguing in comments are not Astana buyers. v2: every plan states how the content reaches the LOCAL buyer (geo tags, local search phrases, 2GIS/Kaspi cards, WhatsApp Status of existing contacts, optional geo-boost), and judges reach by local signals.
6. Codes: customers do not type codes. v2: the code is PREFILLED in a wa.me link (bio, caption, pinned comment); a spoken/on-screen code is a backup only.
7. Weak-phone sound: a hero series that depends on hearing a subtle sound/price difference through a phone mic fails. v2: sound engines only where the difference survives a phone mic (loud, distinct, close).
8. Staff-time realism: shoots with many products/setups (7 pianos with presets; a surgeon recording 4 answers x 3 takes in 15 min) do not fit; each product/setup has a real setup cost. v2: <=3 distinct subjects per week-1 shoot, and say the setup in the shot text.
9. Over-engineered plans for small businesses (DR1-DR16, Thompson jargon in owner-facing text). v2: owner-facing text is plain Russian, <=5 decision rules, the rest stays internal.`

phase('Revise')
const v2 = await agent(
  `${CONTEXT}\n\nYOU ARE THE HEAD OF STRATEGY. Method v1 (${V1}, read it in full) was run through the real code on ${CASES.length} very different requests. The scoreboard is in ${RUNS}/board.json (scores from the boss and veteran-creator attacks before and after the agent's own revision). Below are independent audits of every run, and the patterns the operator already confirmed.\n${KNOWN}\nRevise the method into v2:\n- find the FAILURE PATTERNS across cases (not one-off complaints) whose cause is 'method' or 'model_noncompliance', and change rules/steps so they cannot recur (for non-compliance: make the rule shorter, earlier, more checkable, or move it into the step instruction);\n- keep what worked (the audits' best parts);\n- keep the code contract exactly (step schemas, slugs tables the code parses: the heading containing "the \`driver\` field uses these exact slugs" and "the \`format\` field uses these exact slugs" with the slug in the first column of the first table; code-side selection; truth rails);\n- make it SHORTER where possible: a model must follow it literally as a system prompt; cut duplication; target <= 11k words;\n- mark every change inline with "(v2: why)";\n- end with a section "CODE CHANGES REQUESTED" listing the code issues from the audits that code should fix (one line each).\nReturn ONLY the markdown of method v2.\n\nAUDITS:\n${JSON.stringify(diags)}`,
  { label: 'revise-v2', phase: 'Revise' })

phase('Attack v2')
const attacks = (await parallel([
  ['coverage', 'Check v2 against every fatal/major audit failure with cause method or model_noncompliance: is each one now prevented by a specific rule? List the ones that are not, with the exact fix. Also list anything v2 broke that v1 did well.'],
  ['operability', `Read v2 as the model that must follow it at each step with only the step's schema. Find contradictions, rules that cannot be checked, thresholds without numbers, places where two rules conflict, slug tables the code parser would miss (it needs the exact heading phrase and slug in column 1 of the first table), and text that wastes tokens. Give exact replacements.`],
].map(([k, ask]) => () => agent(
  `${CONTEXT}\n\nYOU ARE an adversarial reviewer (${k}). ${ask}\n\nAUDITS:\n${JSON.stringify(diags.map(d => ({ case: d.case, failures: d.failures.filter(f => f.severity !== 'minor') })))}\n\nMETHOD v2:\n${v2}`,
  { label: `attack-v2:${k}`, phase: 'Attack v2' })))).filter(Boolean)

phase('Finalise')
const final = await agent(
  `${CONTEXT}\n\nYOU ARE THE HEAD OF STRATEGY. Apply every valid point of the two attacks to method v2 (reject a point only with a one-line reason in a final "REJECTED REVIEW POINTS" list). Keep the code contract and the "(v2: why)" marks. Return ONLY the full final markdown of method v2.\n\nMETHOD v2:\n${v2}\n\nATTACKS:\n${attacks.map((a, i) => `===== ATTACK ${i + 1} =====\n${a}`).join('\n\n')}`,
  { label: 'finalise-v2', phase: 'Finalise' })

return { method_v2: final, method_v2_draft: v2, diagnoses: diags, attacks }
