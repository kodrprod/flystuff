/**
 * Model calls: Claude for discovery and reasoning, Gemini for video.
 *
 * Neither model is ever asked for a score. Gemini returns observable facts,
 * Claude returns a mechanism and an adaptation, and the deterministic engine in
 * js/scoring.js turns those into numbers. See PLAN.md §1.
 */
import { jsonFetch } from './lib.mjs';

/* ------------------------------------------------------------------ *
 * Shared vocabularies — must match js/data.js and js/scoring.js
 * ------------------------------------------------------------------ */

export const TONES = ['comedy', 'challenge', 'satisfying', 'craft', 'story', 'heartwarming',
  'educational', 'transformation', 'energetic', 'shock', 'luxury'];
const SPACES = ['counter', 'small_kitchen', 'full_kitchen', 'dining_room', 'shared_seating',
  'outdoor', 'street', 'multi_location'];
const EQUIPMENT = ['phone', 'tripod', 'gimbal', 'light', 'second_camera', 'drone'];
const EDITS = ['single_take', 'simple_cuts', 'heavy_cuts_captions', 'vfx_motion_graphics'];
const AUDIO = ['none', 'trending_sound', 'original_dialogue', 'licensed_music'];
const HOOKS = ['curiosity', 'surprise', 'controversy', 'transformation', 'story', 'relatability',
  'authority', 'visual_spectacle'];
const FORMATS = ['pov', 'talking_head', 'b_roll', 'customer_reaction', 'behind_the_scenes',
  'challenge', 'interview', 'food_preparation', 'before_after', 'customer_interaction'];

/* ------------------------------------------------------------------ *
 * Claude
 * ------------------------------------------------------------------ */

/**
 * Runs Claude and returns the input of the first call to `tool.name`.
 *
 * A tool call is used rather than `output_config.format` because structured
 * outputs are rejected alongside citations, and web search returns cited
 * results. The tool gives the same schema guarantee without that conflict.
 */
async function claudeTool(env, { system, user, tool, webSearch = false, maxTokens = 8000 }) {
  const tools = [tool];
  if (webSearch) tools.unshift({ type: 'web_search_20260209', name: 'web_search', max_uses: 8 });

  const messages = [{ role: 'user', content: user }];

  for (let turn = 0; turn < 4; turn++) {
    const res = await jsonFetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'x-api-key': env.anthropic,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
      },
      body: JSON.stringify({
        model: env.anthropicModel,
        max_tokens: maxTokens,
        system,
        tools,
        messages,
        output_config: { effort: 'medium' },
      }),
    });

    if (res.stop_reason === 'refusal') throw new Error('Claude declined this request.');

    const call = res.content.find((b) => b.type === 'tool_use' && b.name === tool.name);
    if (call) return call.input;

    // A long server-tool turn can stop with pause_turn; resume by echoing it back.
    if (res.stop_reason === 'pause_turn') {
      messages.push({ role: 'assistant', content: res.content });
      continue;
    }

    // Model answered in prose without calling the tool — push it to commit.
    messages.push({ role: 'assistant', content: res.content });
    messages.push({ role: 'user', content: `Now call ${tool.name} with your findings.` });
  }
  throw new Error(`Claude never called ${tool.name}`);
}

/* ---------------- restaurant lookup ---------------- */

const RESTAURANT_TOOL = {
  name: 'return_candidates',
  description: 'Return the candidate restaurants you found, best match first.',
  input_schema: {
    type: 'object',
    properties: {
      candidates: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            name: { type: 'string' },
            address: { type: 'string', description: 'Street and number if known' },
            city: { type: 'string' },
            cuisine: { type: 'string' },
            instagram: { type: 'string', description: 'Handle without @, or empty if none found' },
            confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
            note: { type: 'string', description: 'One line: how you identified it' },
          },
          required: ['name', 'address', 'city', 'cuisine', 'instagram', 'confidence', 'note'],
          additionalProperties: false,
        },
      },
    },
    required: ['candidates'],
    additionalProperties: false,
  },
};

export function findRestaurant(env, query) {
  return claudeTool(env, {
    webSearch: true,
    system:
      'You identify restaurants from partial names and find their Instagram accounts. ' +
      'Search the web before answering. Return up to 5 candidates, best match first. ' +
      'Only report an Instagram handle you actually saw; leave it empty rather than guessing. ' +
      'If the query names a city or street, weight that heavily.',
    user: `Find the restaurant: "${query}". I need the street address and the Instagram handle so I can disambiguate.`,
    tool: RESTAURANT_TOOL,
  });
}

/* ---------------- similar restaurants ---------------- */

const SIMILAR_TOOL = {
  name: 'return_accounts',
  description: 'Return Instagram accounts worth scraping for outlier reels.',
  input_schema: {
    type: 'object',
    properties: {
      accounts: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            handle: { type: 'string', description: 'Instagram handle without @' },
            name: { type: 'string' },
            city: { type: 'string' },
            category: {
              type: 'string',
              enum: ['same_cuisine_same_city', 'same_cuisine_other_city', 'adjacent_concept', 'food_creator'],
            },
            why: { type: 'string', description: 'One line on why this account is a useful source' },
            confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
          },
          required: ['handle', 'name', 'city', 'category', 'why', 'confidence'],
          additionalProperties: false,
        },
      },
    },
    required: ['accounts'],
    additionalProperties: false,
  },
};

export function findSimilarAccounts(env, restaurant, count = 45) {
  return claudeTool(env, {
    webSearch: true,
    maxTokens: 12000,
    system:
      'You build source lists for a short-form video research pipeline. Given a restaurant, ' +
      'find Instagram accounts whose reels are worth mining for repeatable ideas.\n\n' +
      'Rules that matter:\n' +
      '- The account must post reels regularly. An account that posts static photos is useless here.\n' +
      '- Prefer independent restaurants of a similar size and price band over chains and franchises.\n' +
      '- Mix the list: same cuisine in the same city, the same cuisine in comparable cities, ' +
      'adjacent concepts with the same service model, and a few food creators who reliably produce outliers.\n' +
      '- Only return handles you actually saw in search results. A wrong handle costs a scrape credit ' +
      'and returns nothing, so leave a slot empty rather than inventing one.\n' +
      '- Do not include the subject restaurant itself.',
    user:
      `Build a source list of about ${count} Instagram accounts for this restaurant:\n\n` +
      `Name: ${restaurant.name}\nCity: ${restaurant.city}\nCuisine: ${restaurant.cuisine}\n` +
      `Address: ${restaurant.address}\nTheir Instagram: ${restaurant.instagram || 'unknown'}\n\n` +
      `Search thoroughly, then call ${SIMILAR_TOOL.name}.`,
    tool: SIMILAR_TOOL,
  });
}

/* ---------------- reasoning over an extracted reel ---------------- */

const REASON_TOOL = {
  name: 'return_analysis',
  description: 'Return the viral mechanism and a client-specific adaptation.',
  input_schema: {
    type: 'object',
    properties: {
      mechanism: { type: 'string', description: 'Why this outperformed. Two or three sentences.' },
      essentialElements: { type: 'array', items: { type: 'string' } },
      incidentalElements: { type: 'array', items: { type: 'string' } },
      adaptation: {
        type: 'string',
        description: 'Concrete instruction for this client, referencing their actual constraints.',
      },
    },
    required: ['mechanism', 'essentialElements', 'incidentalElements', 'adaptation'],
    additionalProperties: false,
  },
};

export function reasonAboutPost(env, post, client) {
  const cap = client.capability;
  return claudeTool(env, {
    maxTokens: 4000,
    system:
      'You separate the transferable mechanism of a high-performing short video from its incidental ' +
      'execution, then adapt it for one specific restaurant.\n\n' +
      'The literal action is rarely the mechanism. "Chef throws dough" is execution; ' +
      '"expectation violated, then a visible reaction" is mechanism. Adapt the mechanism, never copy the execution — ' +
      'a near-copy is a brand risk for the client.\n\n' +
      'The adaptation must be filmable inside the stated constraints and specific enough to shoot from. ' +
      'Do not score anything and do not use adjectives like "viral" or "engaging".',
    user:
      `## The video that outperformed\n` +
      `Caption: ${post.caption}\n` +
      `Duration: ${post.durationS}s\n` +
      `Plays: ${post.views} (${post.outlierMultiplier?.toFixed(1) ?? '?'}x this account's own median)\n` +
      `Transcript: ${post.transcript || '(none)'}\n` +
      `Observed structure: ${JSON.stringify(post.attributes)}\n` +
      `Beat-by-beat: ${(post.timeline || []).map((t) => `${t.t}s ${t.label}`).join(' | ')}\n\n` +
      `## The client\n` +
      `${client.name} — ${client.cuisine}, ${client.site}, ${client.city}\n` +
      `Brief: ${client.brief}\n` +
      `Spaces: ${cap.spaces.join(', ')}\n` +
      `Kit: ${cap.equipment.join(', ')}\n` +
      `Staff: ${cap.staffCount} total, ${cap.staffAvailableForFilming} free to film, ` +
      `${cap.staffMinutesPerConcept} min per concept\n` +
      `Budget: EUR ${cap.monthlyBudgetEur}/month, so about EUR ${Math.round(cap.monthlyBudgetEur / 6)} per concept\n` +
      `Chef on camera: ${cap.chefOnCamera}. Guests on camera: ${cap.customersOnCamera ? 'allowed' : 'NOT allowed'}\n` +
      `Hard constraints: ${(cap.constraints || []).join('; ') || 'none stated'}`,
    tool: REASON_TOOL,
  });
}

/* ------------------------------------------------------------------ *
 * Gemini — video to observable attributes
 * ------------------------------------------------------------------ */

const GEMINI_SCHEMA = {
  type: 'object',
  properties: {
    transcript: { type: 'string' },
    hookType: { type: 'string', enum: HOOKS },
    format: { type: 'string', enum: FORMATS },
    tone: { type: 'string', enum: TONES },
    secondaryTone: { type: 'string', enum: TONES },
    peopleOnCamera: { type: 'integer' },
    chefOnCamera: { type: 'boolean' },
    customersOnCamera: { type: 'boolean' },
    namedPersonDependency: { type: 'boolean' },
    spaceRequired: { type: 'string', enum: SPACES },
    equipment: { type: 'array', items: { type: 'string', enum: EQUIPMENT } },
    editComplexity: { type: 'string', enum: EDITS },
    audioDependency: { type: 'string', enum: AUDIO },
    trendHalfLifeDays: { type: 'integer', description: '0 if evergreen' },
    propsCostEur: { type: 'integer' },
    staffMinutes: { type: 'integer' },
    cuts: { type: 'integer' },
    timeline: {
      type: 'array',
      items: {
        type: 'object',
        properties: { t: { type: 'integer' }, label: { type: 'string' } },
        required: ['t', 'label'],
      },
    },
  },
  required: ['transcript', 'hookType', 'format', 'tone', 'secondaryTone', 'peopleOnCamera',
    'chefOnCamera', 'customersOnCamera', 'namedPersonDependency', 'spaceRequired', 'equipment',
    'editComplexity', 'audioDependency', 'trendHalfLifeDays', 'propsCostEur', 'staffMinutes',
    'cuts', 'timeline'],
};

const GEMINI_PROMPT = `Watch this restaurant video and report only what is observable.

Transcribe all speech verbatim (keep the original language). If there is no speech, return an empty string.

Then describe the production requirements as if someone had to reshoot it:
- peopleOnCamera: how many distinct people appear
- namedPersonDependency: true ONLY if it needs a specific recognisable person (a celebrity, a named influencer). A generic chef or customer is false.
- spaceRequired: the smallest space this could be shot in
- equipment: the minimum kit. Assume "phone" unless the footage clearly needs more. Stabilised movement implies gimbal, aerial implies drone, controlled lighting implies light.
- propsCostEur: what a restaurant would spend on props and wasted food to reshoot it, in euros
- staffMinutes: total staff time to shoot it, including setup
- trendHalfLifeDays: 0 if the idea is evergreen; otherwise how many days until this specific trend or audio is stale
- timeline: 4 to 6 beats with second offsets

Do not rate, score, or judge quality. Report facts.`;

export async function extractWithGemini(env, post) {
  if (!post.videoUrl) throw new Error('no videoUrl on post');

  const res = await fetch(post.videoUrl);
  if (!res.ok) throw new Error(`video fetch failed: ${res.status}`);
  const buf = Buffer.from(await res.arrayBuffer());
  // Inline uploads share the ~20MB request ceiling; reels are far smaller, but
  // a long one can breach it and the resulting 400 is unhelpful.
  if (buf.length > 18 * 1024 * 1024) throw new Error(`video too large (${(buf.length / 1e6).toFixed(1)}MB)`);

  const out = await jsonFetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${env.geminiModel}:generateContent`,
    {
      method: 'POST',
      headers: { 'x-goog-api-key': env.gemini, 'content-type': 'application/json' },
      body: JSON.stringify({
        contents: [
          {
            parts: [
              { inline_data: { mime_type: 'video/mp4', data: buf.toString('base64') } },
              { text: GEMINI_PROMPT },
            ],
          },
        ],
        generationConfig: {
          responseMimeType: 'application/json',
          responseSchema: GEMINI_SCHEMA,
          temperature: 0.2,
        },
      }),
    },
    { retries: 2, timeoutMs: 240000 },
  );

  const text = out?.candidates?.[0]?.content?.parts?.[0]?.text;
  if (!text) throw new Error('Gemini returned no content');
  const a = JSON.parse(text);

  return {
    transcript: a.transcript || '',
    timeline: (a.timeline || []).slice(0, 6),
    attributes: {
      hookType: a.hookType,
      format: a.format,
      tone: a.tone,
      secondaryTone: a.secondaryTone,
      peopleOnCamera: a.peopleOnCamera ?? 1,
      chefOnCamera: !!a.chefOnCamera,
      customersOnCamera: !!a.customersOnCamera,
      namedPersonDependency: !!a.namedPersonDependency,
      locationType: a.spaceRequired,
      spaceRequired: a.spaceRequired,
      equipment: a.equipment?.length ? a.equipment : ['phone'],
      editComplexity: a.editComplexity,
      audioDependency: a.audioDependency,
      // The schema uses 0 for evergreen because JSON Schema enums can't express
      // null cleanly here; the scorer expects null.
      trendHalfLifeDays: a.trendHalfLifeDays > 0 ? a.trendHalfLifeDays : null,
      propsCostEur: Math.max(0, a.propsCostEur ?? 0),
      staffMinutes: Math.max(5, a.staffMinutes ?? 30),
      cuts: a.cuts ?? 0,
      avgShotLengthS: a.cuts > 0 ? +(post.durationS / a.cuts).toFixed(1) : post.durationS,
    },
  };
}
