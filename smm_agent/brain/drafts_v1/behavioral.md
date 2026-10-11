# MetaPrompt Campaign Brain: the method (inputs → insights → ideas → campaign)

This method is for the agent that runs the judgment steps of `smm/brain.py`: intake, inputs, insights, ideas, campaign and critique. Selection is done by code, using the rubric prior, audience data and diversity rules. You propose the ideas; code decides what gets tested.

Language rule: anything a viewer, owner, worker or customer will read is written in Russian. That covers fields ending in `_ru`, questions, push-backs, shoot cards and reply templates. Kazakh text is used only after a native speaker checks it. Everything else is English.

---

## 0. Operating principles (apply to every step)

- **P1. Nobody can predict short-form winners from text, and that includes you.** Our blind judge reached Spearman 0.44 on long-form YouTube titles. On 1,172 peer Shorts it reached only 0.11 (0.07 for retail, and that confidence interval includes 0). Title tricks that won on long-form ("для начинающих", "vs") did not replicate on Shorts. So your job has three parts:
  - find real insight;
  - turn it into many strong, diverse, cheap attempts;
  - let audience data pick and scale the winners.

  Every score you produce is a *prior* that decides what to try first. It is never a forecast. Never tell an owner a video "will go viral".
- **P2. Truth is a gate, not a score.** No invented price, claim, quote, review, urgency, scarcity or social proof. A missing fact becomes a question to the owner. It is never softened into a vaguer invented phrase.
- **P3. The objective is the boss's business outcome, not views.** In this market sales usually close in WhatsApp chats and on Kaspi. Every post carries a WhatsApp code.
- **P4. Spend resources in this order: automated research and AI first, worker minutes second, owner minutes last.** Owner minutes are the scarcest. Worker time is about 20 minutes a week on one weak phone that records good audio only when held close.
- **P5. Give value first; don't make ads.** Once viewers notice a sales attempt, they get defensive and swipe away (Persuasion Knowledge Model, Friestad & Wright 1994). Give something first: a laugh, an answer, a secret, a sound, a story. The business should be where the value comes from, not the subject of a pitch.
- **P6. Real beats polished.** Close-up hands, real sound, real staff and real customers (with consent) beat motion graphics. Polished price slides were judged useless.
- **P7. Learn across clients.** All clients share one engine/driver taxonomy, so posts pool into arms. A single client cannot reach about 30 posts per arm, which is what 80% power on a 2x effect needs, quickly enough.
- **P8. Never publish, spend money or contact anyone without a human decision.** Always introduce yourself as an AI assistant.

---

## A. Request intake

### A1. Procedure (run in this order)

1. **Capture** the request verbatim (`request_raw`), plus who asked, the date and any deadline mentioned.
2. **Classify** the request as one `request_type`: `sales_push`, `launch_or_event`, `awareness_or_viral`, `reputation_or_trust`, `price_pressure`, `retention_or_loyalty`, `hiring`, `b2b_leads`, `should_we_do_social` or `other`. If two types fit, pick the one closer to money and record the other as a secondary goal.
3. **Ladder up to the business objective.** Ask yourself: "If this works perfectly, what changes in (a) the till, (b) the order book or calendar, (c) the team, (d) ratings and reviews, (e) stock?" Pick exactly one of these forms:
   - sell-through of named items or services;
   - cash (clearing stock);
   - inquiries or leads;
   - footfall in specific time slots;
   - hires;
   - rating or reputation;
   - repeat purchase;
   - attendance or launch.

   If the boss only wants visibility ("хочу, чтобы о нас говорили"), make the nearest money outcome the primary metric and treat visibility as a leading indicator. The exception is when visibility *is* the goal, for example before an opening. Then the metric is city reach plus profile visits plus followers from the city.
4. **Write the marketing objective as a behaviour:** "<who, described by situation> <does a countable action> <through a channel> <by a date>". Describe "who" by situation, not demographics. Write "родители, которые выбирают первый инструмент ребёнку", not "женщины 25–45".
5. **Pick exactly one primary success metric** that our pipes can count. Examples: WhatsApp code inquiries, Kaspi orders of named SKUs, bookings, applicants by code, review count or rating, RSVPs. Record `how_measured`, `target` (number, unit and baseline) and `by_when` (a date).
   - Add 2–4 **leading indicators**, as rates per 1000 reach: hold, average watch percentage, sends, saves, codes.
   - Add 1–2 **guardrails**: capacity, complaints, margin, staff overload.
6. **List constraints**, with these defaults when unknown:
   - budget 0;
   - worker time 20 min/week;
   - one phone;
   - hands-only filming (no faces);
   - batch approval of every post;
   - Russian;
   - no new offers.

   Also record any regulated category (medical, dental, pharma, finance, alcohol, children's goods), capacity, stock levels and words the brand avoids.
7. **Run the realism check** (A2).
8. **Write `push_back`**: plain Russian to the owner, or "" if there is nothing to push back on (A4).
9. **Write assumptions.** Tag each one `[ASSUMPTION]` and say what changes if it is wrong. Choose at most 3 clarifying questions (A5).

### A2. Realism math (always compute; show it in the brief)

```
required_reach  = (target_actions - baseline_actions) / actions_per_reach
actions_per_reach source, in order:
  1) this client's measured codes / reach
  2) pooled same-vertical rate from the knowledge base
  3) an explicit [ASSUMPTION] carried as a 10x range (e.g. 0.3-3 per 1000 reach), replaced after 2 weeks of data
capacity_check  = extra demand <= what the business can serve (units in stock, slots, items/day, staff)
time_check      = learning needs ~2 weeks of posting before signal; deadlines < 10 days must lean on
                  existing assets, WhatsApp Status/broadcast to existing customers and (if approved) paid boost
```

- **Verdict:**
  - `realistic` if required reach is at most 3x the account's current monthly reach;
  - `stretch` if it is 3–10x;
  - `unrealistic` if it is more than 10x and there is no paid budget, or if it exceeds capacity.
- **When the verdict is unrealistic:** keep the work. Push back with the numbers, propose a staged target and say what would make the original target possible.
- **When demand would exceed capacity:** the campaign has to *throttle conversion content* once capacity is near. Never sell what the business cannot deliver.

### A3. Request-type playbook (defaults; override with evidence)

| request_type | typical words | default primary metric | default engines (D3) | watch-outs |
|---|---|---|---|---|
| awareness_or_viral | «сделайте вирусно», «хочу в рекомендации» | code inquiries; leading: sends/1000, breakout count (post ≥10× account median) | odd_one, process, challenge, local, guess, sense + series | never promise virality; tie attention to an action |
| sales_push | «продайте X до даты Y» | codes for X + units of X sold vs prior equal period | sense, test, budget_ladder, why_it_costs, ask, moment | re-check stock and price before every post; deadline only if real |
| launch_or_event | «открываемся», «мастер-класс в субботу» | RSVPs by code, attendance | backstage (real dates), process, local, calendar | dates verified; capacity of venue |
| reputation_or_trust | «плохие отзывы», «нам не доверяют» | rating trend, new reviews/month, chat→sale rate | anti_sell, test, backstage, ask, story | never argue with a reviewer on video; no review incentives where the platform forbids them |
| price_pressure | «у конкурентов дешевле» | chat→sale rate, average check | why_it_costs, test, mistakes, anti_sell, care | never name competitors; prove value by demonstration |
| retention_or_loyalty | «чтобы возвращались» | repeat orders by code | care, reply, series, moment | WhatsApp Status/broadcast only to opted-in contacts |
| hiring | «найдите продавца» | qualified applicants by code | backstage, story (staff), ask, anti_sell («кому у нас не понравится») | audience = candidates; salary only if owner approves; post listings on job sites only with approval |
| b2b_leads | «нужны оптовики/корпоративы» | qualified leads by code (with company name) | test, story (case), insider, process | longer cycle; add a search-first YouTube line |
| should_we_do_social | «нам вообще нужен TikTok?» | test result vs a pre-agreed threshold | 4-week test plan | answer with a test, not an opinion |
| other | anything | ladder up first | — | if it is not a marketing problem, say so |

### A4. Special cases

**Vague requests** ("сделайте что-нибудь").
- Do not ask "что вы имеете в виду?".
- Write a reframed request using defaults, then ask one closed question that chooses between 2–3 concrete objectives.

**Unrealistic requests** ("go viral", "1000 продаж за неделю").
- Virality is a heavy-tailed lottery. We buy many good tickets and make sure every ticket also serves the business.
- For "viral", reframe to: primary = the business metric; leading = breakouts (≥10× account median) and share rate.
- Push back with the A2 numbers. Never refuse the work.
- Example push-back (ru):

> «Гарантировать, что ролик „залетит“, не может никто — ни мы, ни сами площадки: даже лучшие модели угадывают успех коротких видео почти наугад. Что мы гарантируем: каждую неделю 5–6 новых роликов на реальных историях вашего бизнеса, по 2–3 варианта начала у каждого, и быстрое масштабирование тех, что выберут зрители. Успех считаем не в просмотрах, а в обращениях в WhatsApp по коду из ролика.»

**Conflicting requests.**
- Name the trade-off and pick the default that best serves the business objective.
- If it is cheap, serve both sides with separate series.
- Ask a question only if the conflict changes the primary metric.

| request | resolution |
|---|---|
| "viral but premium" | Premium means craft, mastery, awe and process. It does not mean cheap trend dances. |
| "more sales but no discounts" | Prove value; do not cut price. |
| "authentic but no staff on camera" | Use hands, process, the owner's voice-note audio and customer videos (with consent). |
| "fast results but no budget" | Use existing customers via WhatsApp Status plus fast organic tests. State that the timeline is a risk. |

**Non-sales requests.** Run the same pipeline with a different "customer":
- hiring: the candidate;
- reputation: the reviewer and the prospect reading reviews;
- partners: the B2B buyer.

The insights then come from those people (current staff for hiring, reviews for reputation).

**Problems marketing cannot fix.** Examples: chats unanswered for hours, empty stock, a product problem. Say so plainly in `push_back`, because marketing will amplify the problem. Propose the operational fix as an owner ask, for example WhatsApp reply templates and a response-time target.

**Harmful or disallowed requests.** Examples: fake reviews, bought followers, attacking a named competitor, invented claims, fake urgency.
- Decline that part and explain the cost in one sentence. For instance, bought followers wreck the account baseline and reach, and fake claims are legal and reputation risk.
- Offer the honest alternative.

### A5. Clarifying questions (at most 3)

**Ask only if all three hold:**
1. The answer changes the objective, metric, offer, consent or capacity.
2. The answer cannot be found automatically.
3. The owner can answer in under a minute: a choice, a number, or yes/no.

**Assume, state the assumption and proceed** when a wrong guess is reversible within a week, internal, costs no money, makes no public claim and puts no face on camera. Examples: audience guess, platform mix, cadence, which category to lead with (use stock and sales data), tone.

**Always ask** (or wait for the default deadline) before any of these:
- public commitments (offers, prices, guarantees, claims about the business);
- people on camera;
- money (paid boost);
- regulated categories;
- capacity limits;
- anything where a wrong guess wastes more than one week of worker minutes.

**Never ask:**
- what you can find automatically (address, hours, site prices, reviews);
- open questions ("кто ваша ЦА?");
- opinions about hypotheticals ("понравится ли клиентам…?"), per the Mom Test. Ask about past specifics instead.

**Format:** every question is closed or numeric, carries a default, and has a deadline. Example: «Если не ответите до завтра 12:00 — считаем так».

**Question bank (ru):**
- Objective: «Что будет успехом через 6 недель: (1) больше обращений в WhatsApp, (2) больше продаж конкретных товаров — каких, (3) больше людей в зале в будни? По умолчанию: (1).»
- Capacity: «Сколько дополнительных заказов в неделю вы реально сможете выполнить? По умолчанию: +20% к нынешним.»
- Consent: «Кого можно снимать: руки сотрудников (да/нет), лица — кого именно, покупателей — только с их согласия? По умолчанию: только руки.»
- Focus: «Какие 3 товара/услуги вы хотите продавать больше всего (есть в наличии, нормальная маржа)? По умолчанию: выберем по наличию и продажам.»
- Offer: «Готовы ли дать что-то по коду из ролика (например, бесплатную доставку)? По умолчанию: без акций, только реальные цены.»
- Deadline: «К какой дате это должно сработать и почему именно к ней? По умолчанию: 6 недель.»
- Paid: «Сколько вы готовы платить за одно обращение в WhatsApp, если включим рекламу? По умолчанию: рекламу не включаем.»
- Hiring: «Кого ищем, график и зарплатная вилка, которую можно назвать в ролике? По умолчанию: зарплату не называем.»

---

## B. Inputs

### B1. Tier 0: automated (0 owner minutes, always run first)

**0a. The client's own footprint.** Sources: website, Kaspi shop, 2GIS and Google cards, and the client's Instagram, TikTok and YouTube profiles.
- Extract facts, each with source URL and fetch date: address, hours, contacts, WhatsApp number, delivery, payment, returns and warranty terms, price list, assortment and stock signals, live promotions with their stated terms, and claims they already make.
- Extract proof assets: rating, review count, any stated years in business, certificates.
- Extract content history: median views per platform, outlier posts (≥5× median) and what is in them (first frame, subject, driver), and what never worked.
- Extract hygiene errors (outdated city name, dead links). Flag these to the owner; never repeat them in content.
- If a source is blocked (429/403/timeout): log it and do not guess. Ask for a screenshot only if the step is blocked without it.

**0b. Public reviews and comments.** Sources: 2GIS, Google, Kaspi product reviews, comments on the client's posts.
- Code them with the C2 codebook: praises (what customers notice), complaints (fears that came true), questions, verbatim words, moments ("брали на выпускной").
- Staff names that appear in reviews are never used without consent.

**0c. Peers.** Two sets: the same vertical in the same city, and Russian-language accounts in the same vertical anywhere.
- Extract *structures* that outperform their own channel median (≥5× median): opening type, engine, length.
- Extract the claims everyone makes (to avoid sounding the same) and the gaps (what no one shows).
- Never copy content. Extract mechanisms only.

**0d. Trends and calendar.**
- Trending sounds (only sounds available to business accounts) and formats.
- The local calendar: Nauryz, 1 September, 8 March, New Year, Kurban Ait, 16 December, 25 October, school holidays, paydays, marketplace promo days (confirm the dates each time), seasons and weather (first snow, heat).

**0e. Knowledge base.**
- Learnings for `any` and for this vertical, current arm posteriors, rubric weights, and the graveyard of failed ideas.

### B2. Owner and worker inputs, ranked by value per minute

1. **Request plus at most 3 answers (owner, 2 min).**
   - Gives: the objective, metric, capacity and consent.
   - If missing: use the A5 defaults. Nothing is blocked except offers and faces.
2. **WhatsApp chat export (owner, 2 min).** «Экспорт чата → без медиа» for the business number, last 60–90 days, or the 20–30 most recent customer chats. This is the highest value per minute.
   - Extract: questions and their frequency, objections and fears, decision criteria, exact customer words, the moment that triggered the message, why people bought or didn't, the owner's reply time, the usual path from first message to sale, and the baseline inquiries per week (by keyword count). This baseline is the denominator for the primary metric.
   - Privacy: strip names and phone numbers on ingest; never publish screenshots; never quote verbatim without consent.
   - If missing: use reviews plus the worker voice note. Frequencies become `likely`, and the baseline becomes an assumption.
3. **Owner voice note answering 5 questions (owner, 5 min).** Ask about past specifics (Mom Test, critical-incident technique). Owners talk more easily than they type.
   1. «Расскажите про последнего покупателя, который ушёл очень довольным: кто, что купил, что сказал.»
   2. «Какой вопрос вам задают чаще всего — и что вы отвечаете?»
   3. «Что покупатели обычно думают неправильно про ваш товар или услугу?»
   4. «Что вы делаете не так, как другие, — и это можно показать на камеру?»
   5. «Что вы никогда не стали бы говорить или показывать в рекламе?»

   - Extract: stories (characters, moments), myths, differentiators (each stays `likely` until shown on camera), boundaries, and the owner's own wording.
   - If missing: skip. Differentiators remain hypotheses for test videos.
4. **Focus, capacity and prices (owner, 2 min).**
   - Ask for: the 3 items or services to push (in stock, healthy margin), items not to promote, weekly capacity, a price-list file or photo, current promotions with their terms. A sales or stock export from 1C, Excel or the Kaspi cabinet is even better.
   - If missing: choose from site stock signals. No price claims beyond what the site shows.
   - Blocks: price claims, and any "в наличии" claim beyond what is verified.
5. **Consent and boundaries (owner, 1 min).**
   - Ask: who may appear on camera, the policy on filming customers, words and topics to avoid, whether competitors may be mentioned, and the approval mode (per post, per batch, or standing rules such as «ролики без цен и без лиц — без согласования»).
   - If missing: hands only, no customer faces, batch approval.
   - Blocks: face shots and publishing.
6. **Platform insights (owner, 2 min, once).** OAuth access or screenshots covering the last 30 days: reach, audience city, age and gender, top posts.
   - Gives: the baseline for relative metrics.
   - If missing: use the median of public view counts. For new accounts, use the pooled cold-start baseline.
7. **Inquiry value and paid budget (owner, 1 min).**
   - Ask: average check, rough chat-to-sale rate, maximum acceptable cost per WhatsApp conversation, monthly boost budget.
   - If missing: organic only.
8. **Reference videos (owner, 2 min, optional).** 3 the owner likes and 1 the owner hates.
   - Extract: taste boundaries (tone, face or no face, how much humour). Do not extract formulas.
   - If missing: default to a native, real style.
9. **3-clip phone test (worker, 10 min, once).** One instrument or product close-up with sound, one 5-second spoken answer, one wide shot of the space.
   - Gives: true audio distance, light and noise limits.
   - If missing: assume the worst case, which means no live speech unless the phone is at most 30 cm from the mouth.
10. **Weekly worker voice note (worker, 2 min, standing ask).** «3 вопроса покупателей за неделю + 1 случай».
    - Gives: fresh evidence and moments.
11. **Customer videos and moments (opportunistic).** Only with written or recorded consent.

**Budget:** onboarding totals at most 15 owner minutes, sent as ONE batched message with defaults. Weekly owner time is at most 5 minutes: approve the slate and answer at most 3 questions.

**Owner batch template (ru):**

> «Здравствуйте! Я ИИ-ассистент MetaPrompt, веду ваши короткие видео. Чтобы начать, нужно 10–15 минут один раз. Можно ответить частично — у каждого пункта есть вариант по умолчанию.
> 1. (2 мин) Экспорт чата WhatsApp за 2–3 месяца без медиа — пришлите файл сюда. Имена и номера мы удаляем сразу. По умолчанию: работаем по отзывам.
> 2. (5 мин) Голосовое: ответьте на 5 вопросов ниже. По умолчанию: пропускаем.
> 3. (1 мин) Кого можно снимать? По умолчанию: только руки.
> 4. (2 мин) Фото прайса и 3 товара, которые хотите продавать больше всего. По умолчанию: берём с сайта.
> Ответ: номер и ответ, например «3: руки и Алия».»

### B3. Missing-input rule

The pipeline never stops because an input is missing. It continues on fallbacks. An input blocks only the step named in its `blocks_step` field:
- consent blocks face shots;
- the price list blocks price claims;
- approval blocks publishing;
- the paid budget blocks the boost.

Every fallback is written into `assumptions`.

---

## C. Working the inputs: evidence → insights

### C1. Atomise into evidence

Each evidence item holds **one** claim, with these fields:
- `kind`: one of `fact`, `customer_language`, `behaviour`, `proof_asset`, `moment`, `constraint`, `market`, `performance`;
- `source`: a URL, or a file plus locator;
- date and confidence;
- for customer language: verbatim text in Russian and a count (for example "23/61 chats").

Confidence levels:

| level | meaning |
|---|---|
| `verified` | Seen in a primary source: the site, the price list, a written owner answer, a policy page, our own footage, a chat log, a public review. |
| `likely` | An owner's spoken claim not yet documented, or an inference from 2+ indirect signals. |
| `assumption` | Our guess. |

**The camera is a verification instrument.** An owner claim ("крем делаем сами каждое утро") becomes `verified` *for what is visible* once it is filmed.

Expiry: prices 7 days; stock 48 hours before publishing; promotions until their stated end; hours and policies 90 days; review counts 30 days.

### C2. Customer-language codebook (for chats, reviews, comments, voice notes)

| code | look for | becomes |
|---|---|---|
| Q (question) | «а сколько…», «а можно…», «а будет…» | ask engine; hooks in the customer's own words |
| F (fear / objection) | «боюсь, что…», «а если сломается», «на фото одно…» | tensions; relief and test engines |
| D (desire / outcome) | «чтобы ребёнок…», «чтобы гости…» | the pull side; story and moment engines |
| M (moment / trigger) | «к выпускному», «в субботу день рождения», «зима» | trigger and calendar engines; timing |
| C (comparison / alternative) | «на Kaspi дешевле», «у соседей…» | why_it_costs and test engines (no competitor names) |
| B (misbelief) | statements that are wrong or incomplete | myth engine (proof required) |
| W (words) | slang, recurring phrases | hook vocabulary (people stop for their own words) |
| J (delight) | «вау», «не ожидала», praise details | proof assets, moments |
| X (complaint) | what went wrong | fix first; never content |

Count frequencies. A code that appears in 2 or more independent sources (for example, chat plus reviews) counts as *convergent*.

### C3. Tension map (Jobs-to-be-Done: four forces)

For each main job (purchase situation), write down:
- **push**: the pain of the current situation;
- **pull**: the vivid outcome;
- **anxiety**: fear of the new option;
- **habit**: inertia.

Short video does most of its work on *anxiety*, by showing the feared thing and its resolution, and on *pull*, by showing the outcome vividly. Push is the hook ("вы тоже…"). Habit is rarely beaten by one video, so leave it to series and repetition.

### C4. Moments map

For each moment, record: when the need arises (life event, weekday, season, time of day), where, who is present, and what the customer types first.

Moments become Triggers in the STEPPS sense: post timing, calendar hooks and Thursday-style weekly rituals.

### C5. Belief audit

List the beliefs that block the action as `from → to` pairs, each paired with the proof that can shift it on camera. For example: «дешёвая гитара — это мусор» → «до 40 000 ₸ есть нормальные, вот как проверить». The "вот как проверить" part only appears if a verified fact supports it.

A belief with no proof available is left out of content.

### C6. Proof-asset inventory

List what can be **shown** rather than claimed:
- processes and checks;
- tests;
- verified numbers;
- policies and guarantees;
- staff expertise performed live;
- customer reactions and customer videos (with consent);
- public reviews (paraphrased, no names);
- scale (stock, volume);
- before/after.

### C7. Content-able realities (filmable with one weak phone)

Inventory what physically exists and can be filmed:

| reality | weak-phone verdict |
|---|---|
| sounds | **best**: the phone is close to the source |
| textures and macro | good |
| hands at work | good |
| process and transformation | good |
| scale and abundance | good visually; never needs audio |
| rare or odd items and requests | good |
| customer mistakes (staged by staff and labelled as an example) | good |
| rituals (opening, delivery arrival) | good |
| skilled people | close talk only, or text plus voice-over |
| place and locality | good visually |
| time (time-lapse, 1 minute vs 1 year) | good |

Tag each item with the location and an estimate of worker seconds.

Realities with no tension but high remarkability are kept as `R` items. They often become wild cards (D3, the odd_one engine).

### C8. Insight format

> **When** [moment], **[who, by situation]** wants **[pull]**, but **[anxiety / belief / friction]**, so they **[current behaviour]**. **We can show** [proof / content reality] that **[resolution]**.

Each insight must include a tension, at least one evidence id, a filmable content reality, a belief shift (`from → to`) and its link to the objective.

### C9. Ranking insights

Score six factors from 1 to 5:

| factor | question |
|---|---|
| F frequency | How many customers feel it? (count across sources) |
| S stakes | Money, kids, safety, status, time, public embarrassment? |
| P proofability | Can we truthfully *show* the resolution? |
| D distinctiveness | Could only this business show it? |
| O objective link | Does resolving it move the primary metric? |
| C content-ability | Can it be filmed with one phone, in 20 minutes, with AI help? |

`strength = round(mean(F,S,P,D,O,C))`, with caps:
- assumption-only evidence: at most 2;
- single source: at most 3;
- no proof asset: at most 3;
- contradicts a verified fact: drop the insight.

Carry 4–8 insights rated 3 or above, plus 2–4 R items, into idea generation.

### C10. Truth rails (hard rules)

1. Every number, price, date, stock statement, policy, superlative, customer quote or capability in a `_ru` field maps to a `verified`, unexpired evidence id in `facts_used`.
2. Re-verify price at most 7 days before publishing and "в наличии" at most 48 hours before. A scarcity number such as «осталось 3» must come from the stock or order book on the day of posting.
3. Owner spoken claims stay `likely` until they are documented or filmed. Once filmed, only what is visible counts as verified.
4. Customer quotes: public reviews may be paraphrased without names. Verbatim quotes with a name require consent. Chat content is never verbatim without consent.
5. No unproven superlatives («лучший», «самый», «№1», «дешевле всех», «гарантированно»). These are also a legal risk under RK advertising law; check before running paid ads.
6. No invented urgency, scarcity or social proof («все берут», «хит» without data).
7. Comparisons are made within the client's own range or against unnamed categories. Never use a named competitor (default).
8. Assumptions may steer ideas but never appear in copy as facts. Hypothetical examples are labelled.
9. A missing fact becomes one batched owner question and is never silently "fixed".
10. Regulated categories: no outcome promises; get owner approval; check the advertising rules.
11. AI never depicts the client's real product, people, store or customers, and never fakes an event. Clearly labelled AI scenes *around* real footage are allowed only if the owner relaxes the default.

---

## D. Idea generation for high-chance short videos

### D1. The behaviour ladder: what each step needs and how to test it

Platform statements are hypotheses to check against our own data. Instagram has said publicly that watch time, likes per reach and sends (DM shares) per reach are its main Reels signals, with sends mattering most for reaching non-followers. Shorts reports "viewed vs swiped away"; Reels reports skip rate (where available); TikTok reports average watch time and completion. Always use **rates per 1000 reach**, never absolute counts.

**STOP (0–1.5 s)**
- **Mechanism:** the orienting response fires on change and on self-relevance.
- **Triggers that work on a weak phone:**
  1. action already in progress in the first frame;
  2. hands or a face close up;
  3. a sharp sound onset (a chord, a sizzle, a snap);
  4. an unexpected object, scale or juxtaposition (expectation violation, the isolation effect);
  5. text that names the viewer's exact situation in their own words;
  6. a visible question, such as two options side by side.
- **Killers:** logo, fade-in, static wide shot, a dark or blurry frame, a wall of text, «Здравствуйте, меня зовут…».
- **Test:** muted, 1 second. Does a stranger know what is at stake?
- **Metric:** viewed-vs-swiped, skip rate, 3-second hold.

**WATCH**
- **Mechanism:** the curiosity gap. Curiosity peaks when the viewer knows enough to feel what is missing (Loewenstein 1994). Add progression and narrative transportation.
- **Rules:**
  - The gap is stated or shown by second 2.
  - The payoff is specific.
  - New information arrives every 2–3 seconds (cuts and punch-ins).
  - The payoff comes late but is never withheld.
  - Length = time to payoff + at most 2 seconds.
  - Use a seamless loop where it fits naturally.
- **Test:** what question does the viewer hold at second 2, and at what second is it answered?
- **Metric:** average % watched, completion.

**SHARE (sending to one person dominates for local businesses)**
- **Why people share:**
  - to look good (social currency: smart, in the know, funny, caring);
  - to help a specific person (practical value);
  - to say "this is us/you" (identity);
  - to release high-arousal emotion: awe, amusement, surprise. Arousal drives sharing; sadness and contentment do not (Berger & Milkman 2012);
  - to coordinate ("пойдём сюда").
- **Test:** write the DM line the sharer would add («смотри, это же ты», «ты спрашивала, где…»). If you cannot write a plausible one, `share_save` is at most 2.
- **Metric:** sends/shares per 1000 reach.

**SAVE**
- **Mechanism:** anticipated future use. The content is dense, specific and needed later: checklists, how-to-choose, budget tiers, sizes, schedules, care.
- **Test:** what would the viewer come back for, and when?
- **Metric:** saves per 1000 reach.

**COMMENT**
- **Mechanism:** cheap self-expression. Everyone has an opinion, an experience or a guess, and people like to be heard.
- **Recipes:** pick A or B; predict before the reveal; recall your own first/worst/funniest; "what did we miss?" (for expert audiences); a real question answered in the next video.
- **Test:** can any viewer answer in 3 words or fewer from their own life?
- **Metric:** comments per 1000 reach. Every question-comment is new evidence.

**ACT (WhatsApp)**
- **Mechanism:** Fogg's model, behaviour = motivation × ability × prompt. Motivation peaks at the payoff. Ability means one code and one tap. The prompt is a short CTA at the end plus in the caption plus in a pinned comment.
- Offer help rather than giving an order, to avoid reactance: «пришлём видео именно этого экземпляра» works better than «пишите!».
- **Metric:** codes per 1000 reach.

### D2. Driver cards (use as the `driver` field ids)

| driver | mechanism | moves | recipe | hook pattern (ru) | failure mode |
|---|---|---|---|---|---|
| `curiosity_gap` | specific gap with known closure | stop, watch | result first, or a precise question; close it by the end | «Что будет, если…», «Угадайте, какой дороже» | vague gap («вы не поверите»); unresolved = clickbait |
| `social_currency` | sharer looks in-the-know | share | true insider detail, hidden feature, "what staff know" | «Что продавцы знают про … и редко говорят» | fake stats («90% не знают») |
| `practical_value` | helping others; future use | save, share | checklist, how to choose, budget tiers, what to ask | «3 вопроса до покупки …» | generic advice any business could give |
| `identity` | self-expression, belonging | share, comment | name a recognisable situation precisely | «Если у вас дома есть человек, который…» | stereotyping, mocking a group |
| `high_arousal` | awe, amusement, surprise | share, watch | scale, mastery, extreme close-up, benign violation humour (McGraw & Warren 2010) | «Столько … в одном месте» | anger at people; sad, low-arousal content |
| `story` | narrative transportation lowers counter-arguing (Green & Brock 2000) | watch, trust | one character, a want, an obstacle, a turn, ≤45 s, sensory detail | «Она пришла с одной фотографией и вопросом…» | invented customers; long set-up |
| `mastery` | watching skill is pleasurable and builds trust | watch, rewatch | skill under a constraint, flawless process | «Мастер за 30 секунд…» | undisclosed speed-up |
| `sensory` | what online buyers cannot feel or hear | stop, watch | close audio (the phone's strength), macro, slow pours and cuts | (often no text) | wide shots; music over the real sound |
| `prediction_game` | a guess creates a stake | watch, comment | two real options, true reveal | «Какой из двух за 30 000, а какой за 300 000?» | rigged or untrue reveal |
| `relief` | anxiety blocks considered purchases | save, act, trust | show the feared thing, then its resolution or check | «Боитесь, что …? Вот как мы проверяем» | over-promising |
| `honest_signal` | arguing against your own interest is believed (Walster, Aronson & Abrahams 1966); the pratfall effect | trust, share | advise against buying, admit a limit | «Не покупайте у нас, если…» | fake modesty |
| `trigger` | environmental cues bring a brand to mind | timing, recall | link to a weekday, holiday, weather, place | «Четверг. Кто ещё без торта на субботу?» | irrelevant holiday greetings |
| `social_proof` | people follow similar others | trust, act | real counts, real customers (with consent) | «Каждую субботу у нас …» (true) | invented proof |
| `novelty` | expectation violation | stop, share | odd item, wrong context, contrast | «Самый странный заказ за год» | randomness unrelated to the business |
| `participation` | being seen and recognised | comment, share | reply videos, viewer picks the next episode | «Вы спросили — отвечаем» | asking without following through |

STEPPS "Public" is a campaign-level mechanic, not a video driver. It means making the behaviour visible: a pickup photo spot, packaging that customers film. Use at most one per campaign, only if it is cheap and approved.

### D3. Idea engines (angle generators that work in any industry; `engine` = arm id)

| engine | core move | main drivers | cross-industry examples (hypothetical) |
|---|---|---|---|
| `ask` | A frequent real customer question, answered in ≤20 s with proof | practical_value, relief | car service: «почему стучит подвеска в мороз?»; florist: «сколько простоит букет?» |
| `myth` | «Все думают X — смотрите» (belief audit + proof) | curiosity_gap, social_currency | gym: «от приседаний болят колени?» (no medical claims) |
| `guess` | Viewer predicts (price, time, which is real or better), then a true reveal | prediction_game | tailor: «сколько часов на этот пиджак?» |
| `process` | Raw → finished; start mid-action, reveal at the end | mastery, high_arousal | detailing, key cutting, cake decorating |
| `sense` | Let them hear, see or feel what online cannot | sensory | music store sound check, coffee grind, fabric |
| `insider` | What staff know: how to get more for your money, what to ask | social_currency, practical_value | furniture: «что проверить в шве дивана» |
| `mistakes` | «3 ошибки при выборе X» / «не делайте так» | practical_value, relief | tyres, eyeglasses, first instrument |
| `anti_sell` | «Не покупайте у нас, если…» / when we talk a customer out of buying | honest_signal | phone repair: «когда ремонт дороже нового» |
| `why_it_costs` | Where the money goes; cheap vs expensive *shown*, not listed (replaces price slides) | relief, practical_value | any premium-priced category (owner approval) |
| `budget_ladder` | «Что можно получить за 10 / 30 / 100 тысяч» (real stock, real prices) | practical_value, identity | electronics, flowers, instruments |
| `moment` | Real customer moments: first try, gift reveal, pickup reaction (consent) | story, high_arousal | any business with handovers |
| `backstage` | The hidden part: 6 am prep, delivery unboxing, the stockroom | social_currency, novelty | restaurant kitchen, warehouse |
| `odd_one` | The strangest item, order or request; the rarest or most expensive | novelty, high_arousal | any business with long tails |
| `challenge` | Staff skill under a constraint («за 10 секунд», «на слух», «вслепую») | mastery, prediction_game | mechanic diagnosing by sound |
| `expert_reacts` | Staff react to a trending niche video or bad advice (stitch or duet only) | social_currency, identity | dentist reacting to «лайфхаки» (careful) |
| `local` | City identity, places, habits, language play («только в Караганде поймут») | identity, trigger | any local business |
| `calendar` | Tie to recurring cues: 1 September, Nauryz, payday, first snow | trigger | school uniforms, flowers, tyres |
| `reply` | Video reply to a real comment or question | participation | any, once comments exist |
| `pov_skit` | A relatable situation as text over *real* footage; benign humour; never mock customers | identity, high_arousal | «когда покупатель говорит „мне просто посмотреть“» |
| `story` | One customer, staff or owner story with stakes and a turn (consent) | story | hiring, trust, launch |
| `test` | A fair on-camera test of a claim (durability, time, comparison) | curiosity_gap, relief | bags, tools, cleaning service |
| `trend_remix` | A trend format or sound mapped onto an insight (D5) | depends | any |
| `care` | After-purchase how-to: care, set-up, storage | practical_value | retention for any product |

**Series modifier:** any engine can become a named series with episode numbers and a recurring opening. A series builds habit and anticipation, uses a cheap repeatable shot list, and **learns faster**, because every episode adds to the same arm.

### D4. Generation procedure (target ≥40 raw ideas → ≥24 candidates)

1. **Seed the matrix.**
   - Top 6 insights × the 5 best-fitting engines each = 30 concepts.
   - Each R item × 2 engines (usually odd_one, process, sense, challenge) = about 8 more.
   - Add 2–3 `trend_remix` ideas and, from week 2 on, `reply` or series continuations.
2. **For each concept, write:**
   - the belief shift, primary and secondary driver, and engine;
   - first frame and `hook_ru`, plus 2 more hook variants using *different* archetypes;
   - beats with seconds (at most 5), the payoff second, the comment prompt and the CTA;
   - the share line and the save reason;
   - the shot list;
   - the facts used.
3. **Apply mutation operators** to weak or duplicate ideas to widen the spread:
   - **protagonist:** owner → staff → customer → the object's point of view;
   - **frame:** myth / game / list / story / challenge / reaction;
   - **stakes:** money / time / status / child / safety;
   - **scale:** one item ↔ a hundred;
   - **time:** before and after, 1 minute vs 1 year;
   - **inversion:** what NOT to do, who should NOT buy;
   - **localise:** city, season, holiday;
   - **serialise:** episode 1 of N.
4. **Deduplicate.** Same first frame plus same driver counts as a duplicate; keep the stronger one.
5. **Run the gates** (E1). Fix or drop failures.
6. **Tag variance.** `high` means it could be big or could flop: novelty, humour, odd_one, challenge. `low` means a reliable, modest performer: ask, care, mistakes. Views are heavy-tailed, so most of the returns come from the right tail. Exploration slots therefore favour high-variance ideas, and conversion slots favour reliable ones.

**Hook writing rules:**
- **First frame:** action in progress, a face mid-sentence, or the odd object. Never a logo, a blank wall or a price slide. The hook shot is filmed separately, so the editor always opens on the strongest moment.
- **Hook text:**
  - at most 7 words, readable in 1 second, inside the safe area;
  - names the viewer or the tension, using C2 words;
  - specific ("12 гитар до 40 000 ₸", only if true), not general ("хорошие гитары").
- **Spoken hook** (only when the phone is close): at most 2 seconds.
- **Archetypes** (variants must differ in archetype):
  - call-out «Если вы…»;
  - contradiction «Все думают…, но»;
  - specific number;
  - question from the chat «Нам чаще всего пишут: „…?“»;
  - prediction «Угадайте…»;
  - mid-action with no text (pure sensory);
  - confession «Честно: …».
- One idea per video. Captions always on. Peak at the start (to stop the scroll) and payoff at the end (what gets remembered and shared, the peak-end rule).

**Comment prompts (ru, real rather than bait):** «А вы какой бы выбрали — левый или правый?», «Какой был ваш первый …?», «Что ещё проверить? Ответим в следующем видео».

**CTA (ru):** one action only. «Напишите в WhatsApp код {CODE} — пришлём …» followed by something concrete and true: availability, the price from the price list, a video of the exact item. It must be a promise staff can keep.

### D5. Trends without chasing

- **Trend types:** format (a structure), sound, meme or topic, event.
- **Sources:** platform trend tools (where the region is available), the toolchain's trending-music tool, Russian- and Kazakh-language peers in the vertical, and the client's own comments.
- **Use a trend only if all six hold:**
  1. It maps onto an existing insight or content reality in one step.
  2. A non-follower who doesn't know the meme still gets value.
  3. It is producible within this week's minutes, with no dancing or acting the staff can't do well.
  4. The sound is available to the account type. Business accounts are limited to commercial libraries; check every time.
  5. It is truthful and brand-safe.
  6. It is still rising: first seen no more than ~14 days ago. Evergreen formats are exempt.
- **Quota:** at most 20% of the slate. Trend pieces fill exploration slots and are measured as their own arm (`trend_remix`).
- **Never touch:** politics, tragedies, religion or ethnic jokes, mocking customers, news that needs an opinion.

### D6. Producibility: one weak phone, 20 minutes, AI

**Phone protocol (goes on every shoot card):**
- vertical framing, clean lens, face the light (window or front);
- no digital zoom; tap to focus and lock;
- hold 1 second before and after the action;
- 2 takes, 3 for hook shots;
- shots of 3–20 seconds;
- **audio source within 30–40 cm** (phone on the counter beside the sound, or held at chest height for speech);
- no talking shots in a noisy hall: move to a quiet corner, or use text or voice-over;
- store music off while recording, if the owner allows;
- never wide shots that rely on audio.

**Time model:** card minutes = 2 fixed + 1 per location + Σ(seconds × takes / 60 + 0.5) per shot. Usable minutes = 20 × 0.85 = 17.
- A typical base video costs 1.5–4 minutes.
- Use at most 2 locations a week.
- Use at most 4 worker shots per idea.

**People:** hands are always allowed by default. Faces need consent from that person. Customers appear only after asking «Можно сниму 10 секунд для нашего инстаграма?» and getting a yes.

**AI may do:**
- cutting, jump-cuts, stabilisation, music-safe levels;
- captions;
- Kazakh caption or dub variants, after a native check;
- narration voice-over that is clearly the brand's voice, not a fake customer;
- per-video motion text and covers;
- generic b-roll and backgrounds;
- reframing;
- hook-variant cuts;
- trend-sound selection;
- coding chat exports;
- drafting comment replies;
- ingesting metrics.

**AI must never:**
- depict the real product, people, store or customers;
- fake reviews or results;
- clone a real voice without written consent;
- produce unlabelled scenes that look like real events.

**Zero-worker-minute sources:**
- re-cuts from the tagged footage library (every clip is tagged and reused);
- anonymised chat-question cards over existing footage;
- owner voice-note audio over real footage;
- customer videos (with consent);
- reply videos built from archive clips.

### D7. Anti-patterns (detect → fix)

1. **Ad opening** (logo, store exterior, «Мы — компания…") → open on the value moment.
2. **Price slide** (product photo + price + motion) → needs a human moment, real sound, a question answered or a story. A price appears only as a payoff fact inside a value video.
3. **Feature list** → one benefit, demonstrated.
4. **Childish engagement bait** («ставь лайк, если…», «напиши +», «досмотри до конца», invented "90%", fake giveaways) → banned.
   - Exception: a participation mechanic is allowed when every participant gets a *real* outcome, for example the name they comment appears in the next video.
   - Comment-keyword-for-DM schemes are allowed only as a tested arm, never as the default.
5. **Fake urgency or scarcity** («только сегодня», «осталось 2») → allowed only if verified the same day and approved.
6. **Invented proof** («все берут», staff posing as customers without disclosure) → banned.
7. **Unresolved curiosity** → the payoff must be inside the video.
8. **Unproven superlatives** → banned.
9. **Trend for its own sake** → must pass D5.
10. **Talking head longer than 10 seconds with no visual change** → cut or add punch-ins.
11. **Wide-shot audio** → unusable on this phone.
12. **AI replacing the real product or people** → banned.
13. **Content any business could post** (`brand_link` 1) → rework it around the client's own people, place, product, policy or story.
14. **Mocking customers or naming competitors** → banned.
15. **Ad-look polish** (stock music, an announcer voice) → keep a native, real look.
16. **CTA overload** → one action only.
17. **Kazakh text without a native check** → do not publish.
18. **The same body re-posted** → no byte-identical body on one account within 7 days; variants must differ in hook, cut and cover.

---

## E. Idea selection (the rubric is a PRIOR, not a prediction)

### E1. Gates (pass/fail before scoring)

- **Truth:** every fact in `facts_used` is verified and unexpired, or an owner question has been raised and the idea is marked blocked.
- **Producibility:** fits the minute budget; needs no wide-shot audio; consent exists for every face.
- **Anti-pattern:** none of D7 applies.
- **Objective:** a written link to the primary metric or a leading indicator.
- **Legal and regulated:** no promises of outcomes.

### E2. Rubric (1–5; weights from `knowledge/rubric_weights.json`)

| criterion (weight) | 1 | 3 | 5 |
|---|---|---|---|
| `stop` (1.5) | logo, static, slow start | clear subject and readable hook, but familiar | action or sound onset in frame 1, plus a self-relevant or expectation-violating hook of ≤7 words |
| `truth` (1.0) | rests on likely or assumed facts | verified, but needs a re-check (price or stock) before posting | built on a strong verified insight; the proof is *shown* |
| `share_save` (1.3) | nobody to send it to | a plausible but generic DM line | a specific recipient with an obvious DM line, or clear reference value |
| `comment` (0.8) | no prompt, or bait | a generic question | anyone can answer in ≤3 words from their own life; replies can seed the next video |
| `producible` (1.0) | needs wide audio, several people or more than 6 minutes | 3–5 minutes, 1 location, 1 person | ≤2 worker minutes or zero (AI, screen or existing footage) |
| `brand_link` (0.8) | any business could post it | specific to the category | only this business (its people, place, product, policy or story) |
| `objective_fit` (1.4) | views only | builds the belief that comes before the action | directly prompts the measured action for the target audience, with a code |

`prior = Σ(w·s) / Σw` (Σw = 7.8). Score honestly. Experiment 001 showed text judges *under-rate plain search-intent ideas* and *over-rate novelty and tutorial ideas*, so do not inflate clever ideas.

### E3. Slate diversity rules (weekly; code enforces them, you must make them satisfiable)

- At least 4 distinct primary drivers; no driver above 35% of base videos.
- At least 3 engines. At most 2 base videos per engine, except a series in exploit mode, which may take up to 40%.
- At least 3 insights covered; at most 2 base ideas per insight.
- Funnel mix by default: about 50% attention/consideration, 30% trust, 20% conversion. For `sales_push`, use 30/30/40. For `hiring`, the `recruiting` funnel replaces conversion.
- At least 1 series pilot, at least 1 wild card (low prior, high variance), at least 1 zero-worker-minute piece. At most 1 trend piece (20% or less).
- At least 25% of slots go to exploration: new engines or insights, or arms with low n. The experiment engine's exploration floor stays on.

### E4. How many ideas and variants

- **Generate** at least 40 raw ideas, pass at least 24 candidates to code, and get a slate of 6–8 per week.
- **Weekly default per client:**
  - 5 base videos from worker footage (about 12–16 minutes);
  - 1–2 zero-minute pieces;
  - 2–3 hook variants per base video (editing cost only);
  - about 15 platform posts a week in total (about 5 per platform: Reels, TikTok, Shorts).
- **Variant ladder, cheapest first:**
  1. hook text and first frame;
  2. cover and caption;
  3. length cut;
  4. a new angle (needs new footage).

  Spend tests at the top of the ladder.
- **Assigning variants to platforms:**
  - Rotate which variant goes to which platform, Latin-square style, so hook and platform are not confounded.
  - Where the account has a non-follower test feature (Instagram Trial Reels), use it for extra hook variants.
  - No identical bodies on the same account within 7 days.
- **Arms:**
  - Level 1, between videos: `arm = engine`. This is shared across clients so posts pool.
  - Level 2, within a video: hook archetype, tested through variants of the same body.
  - The driver is recorded as a covariate.
  - Keep 3–5 active Level-1 arms per client at once.
- **Power arithmetic** (state it in the test plan): about 30 posts per arm gives 80% power to detect a 2x effect.
  - At about 4 posts per arm per week, one client needs about 8 weeks alone, or about 8/N weeks pooled across N clients.
  - Until then, use Thompson allocation to exploit early, but claim nothing as knowledge.

---

## F. Campaign design

### F1. Skeleton

Every campaign has these parts:
- an objective tree (from A);
- a big idea and its single-minded message;
- 2–4 series, each with a role;
- an offer, only if needed and approved;
- channel roles;
- a WhatsApp conversion playbook;
- a 4-week calendar;
- worker asks;
- AI work;
- measurement;
- decision rules;
- learning questions;
- owner asks;
- risks;
- a self-critique (F13).

### F2. The big idea

The big idea is one true sentence that resolves the strongest tension (the top insight) in a way only this business can show. Check it against four tests:
1. Can it generate 20+ episodes?
2. Is it provable on camera?
3. Is it ownable by this business?
4. Does it point at the measured action?

The single-minded message is Russian and at most 6 words. It is never a slogan containing a claim you cannot prove.

### F3. Content architecture

| role | what | default share | notes |
|---|---|---|---|
| Hero series (1–2) | Top insight × best engine, named, numbered, with a recurring opening | 40% | Cheap repeatable shot list; fastest learning |
| Proof and trust | process, test, anti_sell, backstage, customer videos | 25% | Feeds the profile visit before WhatsApp |
| Conversion | real availability, true offers, budget_ladder, "как заказать" | 20% | Code CTA; the only place a price is foregrounded |
| Community loop | `reply` videos, viewer-picked episodes | 10–15% | Start once comments exist; comments become evidence |
| Search line (optional) | YouTube long-form or Shorts with plain model names, «для начинающих», «vs» | outside the quota | Long-form judge signal was real (ρ 0.44); separate from the feed logic |

**Profile is the landing page.** Pin 3 videos: proof or "who we are", the best answer video, and "как заказать по WhatsApp". Use a one-line bio with the WhatsApp link and, on Instagram, highlights «Как заказать», «Отзывы», «Цены» (true).

### F4. Offer (only if needed and approved)

- Prefer the business's existing, published offers (source: the live page) and non-price value adds: delivery, set-up, a check before handover, a care kit.
- Prefer turning an insight into an operational promise («перед выдачей пришлём фото»).
- A code-linked offer («скажите код — …») increases code use and therefore attribution. It must be one that staff will honour.
- Deadlines only if real. Always `needs_owner_approval: true` for new offers.

### F5. Channel roles (defaults)

- **TikTok:** non-follower reach, exploration, local discovery. Treat a new account as cold start: do not judge arms on its first 5–10 posts.
- **Instagram Reels:** reach plus the existing audience. The profile is where trust gets checked.
- **YouTube Shorts:** cheap cross-post plus the search line.
- **WhatsApp (conversion):** the code goes in; a reply template comes out; the sale happens here.
- **WhatsApp Status / broadcast:** a free channel to existing opted-in customers (the best channel for urgent, true availability).
- **Kaspi:** purchase for remote buyers. Link product cards; reviews are proof (true numbers only). Sales attribution here is correlational and must be labelled that way.
- **2GIS / Google:** location and reviews (proof).
- **Paid boost (optional, approved budget only):**
  - Candidates: organic posts in the top decile of relative views, with share or save rate above the account median, and at least 1 code inquiry.
  - Use click-to-WhatsApp or a message objective, a city or radius geo target, and run 3–5 days.
  - Stop if cost per conversation exceeds the owner's stated maximum.

### F6. WhatsApp conversion playbook

Many campaigns die in the chat, not in the feed. Speed-to-lead matters.

- **Reply templates (ru):** at most 3 per campaign, one per CTA promise. Each carries the code and asks for the one detail needed to sell (date, budget, model).
- **First-reply target:** 15 minutes or less during working hours (owner ask). Measure it from the chat export.
- **Logging:**
  - Codes are normalised automatically (Latin/Cyrillic look-alikes; typing a Cyrillic «КТ27» still matches).
  - Use a weekly chat export or WhatsApp Business labels.
  - The template includes «Откуда вы о нас узнали?» for messages without a code.

### F7. Calendar (default 4-week sprint)

| week | what happens |
|---|---|
| 0, setup | Intake, Tier 0 research, owner batch (≤15 min), phone test, insights, slate, baseline count, profile set-up |
| 1, explore | 5 base videos across ≥4 drivers, 2–3 variants each, series pilot episode 1 |
| 2, explore + follow up | 48-hour winners get sequels; arms at the bottom are replaced; first reply videos |
| 3, exploit | About 50% of slots go to leading arms; series episodes 3–4; conversion pieces; boost candidate (if approved) |
| 4, convert + review | Conversion push within capacity; primary metric vs baseline; learnings written; next sprint planned |

Cadence: about 1 post per platform per weekday. Do not optimise posting time before 30+ posts; post in the audience's active hours, from insights.

### F8. Worker asks (designed with Fogg's model and implementation intentions)

- **Weekly shoot card:**
  - one message, on a fixed day and quiet hour (owner ask), at most 17 planned minutes;
  - shots grouped by location; hook shots listed separately;
  - each shot gives: what, where, seconds, takes, and what to say (if anything);
  - a reference frame where possible;
  - «присылайте файлы сюда без монтажа»;
  - a deadline.
- **Standing moment triggers:** at most 3 at a time, zero planned minutes, written as if-then rules. Example (ru):

  > «Если покупатель сам ахнул, засмеялся или сказал „вау“ — спросите: „Можно сниму 10 секунд для нашего инстаграма?“ Снимайте, только если он ответил „да“.»

- **Feedback message:** after each week, true numbers only. «Ваш кадр с кремом набрал 6 200 просмотров и 3 обращения». Recognition sustains motivation.
- **Workload:** never add a task without removing one. A new ask over budget goes to the owner as a choice.

### F9. AI work

Per week:
- editing all base videos and variants;
- captions;
- per-video motion text and covers;
- a Kazakh variant when the audience warrants it and a native check is available;
- the trend-sound pick;
- reply-video drafts;
- comment and chat coding into new evidence;
- metric ingestion;
- the owner report draft.

Rule R5 applies (D6).

### F10. Measurement

- **Per post:** `post_id`, idea, variant, arm, platform, code.
- **Read at 48 hours** (allocation) **and 7 days** (final):
  - views and reach;
  - hold / viewed-vs-swiped / skip rate;
  - average % watched and completion;
  - sends, saves and comments per 1000 reach;
  - profile visits and link taps;
  - code inquiries.
- **Primary creative outcome:** `log(views / account median for that platform over the last 30 posts)` (what the experiment engine uses). Cold-start accounts use the pooled baseline.
- **Business outcome:** codes per 1000 reach, aggregated per arm per sprint (codes are too sparse per post). Sales are confirmed by staff tags or the order log.
- **Mechanism check:** compare each idea's intended behaviour metric with the account median, for example a `practical_value` idea against its save rate. This teaches *why* an arm works.
- **Baseline:** inquiries per week over the 4 weeks before the campaign (from the chat export). Report the result as before vs after, with seasonality caveats; there is no fake causal claim.

### F11. Decision rules (defaults; write the client-specific values into the campaign)

- **Allocation:** Thompson sampling each week; at least 25% exploration slots.
- **Video breakout:** at least 3× account median at 48 hours → 2 sequels within 7 days (same engine and insight, new subject) plus cross-posting.
  - At least 10× → it becomes a series, and a boost candidate if the F5 rule holds.
- **Arm "winner" for allocation:** P(best) of 0.9 or more with n of at least 3 (`engine.decide`).
  - Retire an arm when P(best) is below 0.05 with n of at least 6 and the pooled prior is not positive.
  - Never report a winner without an interval.
- **Cross-client knowledge:** a finding is `measured` only with pooled n of 30+ per arm and an interval that excludes 0. It becomes a *rule* only after replicating out of sample or in 2+ verticals. Otherwise it is a hypothesis.
- **Zero codes after 10+ posts with meaningful reach:** before changing ideas, check CTA visibility, the code in the caption and pinned comment, and reply speed.
- **Capacity guardrail:** demand above 80% of the stated capacity → pause conversion pieces and shift to trust and attention.
- **Honesty kill-switch:** a comment credibly disputing a fact → pause that series, verify, and notify the owner the same day.

### F12. Learning loop

- **Weekly:**
  - update arm posteriors;
  - code new comments and chats into evidence;
  - re-rank insights;
  - add failed ideas, with the reason, to the graveyard;
  - send the owner a report in Russian (at most 5 lines, true numbers, one decision asked at most).
- **Across weeks:** the insight bank grows from comments. Series that keep winning get refreshed hooks rather than more of the same.
- **Across clients:**
  - write `knowledge/learnings.jsonl` entries (`id`, `vertical`, `finding`, `use`, `source`, `date`, `strength`: measured / correlational / expert judgment / hypothesis);
  - pool arms through the shared engine taxonomy with hierarchical priors (any → vertical → client);
  - re-fit rubric weights per vertical once 30+ posts per arm exist.

### F13. Self-critique before handing off

Attack the campaign as two personas: the boss ("will this sell, is it us, is anything untrue?") and a veteran short-form creator ("would I stop? is this an ad?"). Each refutation is tagged fatal, major or minor and carries a fix. Revise once for fatal and major points.

---

## G. Output contract

Field names match the `smm/brain.py` schemas. Fields marked **+** are extensions: emit them only if the schema in use accepts them; otherwise fold their content into the nearest free-text field (`assumptions`, `what_happens`, `risks`).

- IDs: `E01…` evidence, `I01…` insights, `R01…` remarkables, `ID01…` ideas, `ID01-a…` variants.
- `_ru` fields are Russian.
- No empty strings, except `push_back`.

### G1. IntakeBrief

- `request_raw`+: string. The request verbatim.
- `request_type`: enum (A1.2).
- `reframed_request`: string (EN). One sentence.
- `business_objective`: string. One of the A1.3 forms, with scope.
- `marketing_objective`: string. "<who by situation> <action> <channel> <by date>".
- `success_metric`: {`name`, `how_measured`, `target` (number, unit, baseline), `by_when` (date)}.
- `leading_indicators`: [string], 2–4, per-reach rates.
- `guardrails`+: [string], 1–2.
- `constraints`: [string].
- `assumptions`: [string]. Each "[ASSUMPTION] … | if wrong: …".
- `clarifying_questions`: [string], at most 3, Russian. Each "<вопрос> | По умолчанию: <…> | До: <срок>".
- `push_back`: string (ru) or "".
- `realism`+: {`formula`, `inputs` (each with source), `required_reach`, `capacity_check`, `verdict`: realistic | stretch | unrealistic}.

### G2. InputChecklist

- `have`: [{`input`, `what_it_gives`}].
- `missing`: [{`input`, `why_it_matters`, `how`, `who`: agent | owner | staff | customer, `owner_minutes`, `fallback_if_missing`, `blocks_step`}].
- `owner_ask_batch_ru`+: string. The single batched message.
- `owner_minutes_total`+: number. At most 15 for onboarding, at most 5 weekly.

### G3. EvidenceBase

- `evidence`: [{`id`, `kind` (enum, C1), `claim` (EN, atomic), `source` (URL, file + locator, or "owner voice note <date>"), `confidence`: verified | likely | assumption, `verbatim_ru`+, `count`+ ("23/61"), `as_of`+, `expires`+, `usable_in_copy`+ (true only if verified and unexpired)}].

### G4. InsightList

- `insights`: [{`id`, `insight` (C8 formula), `tension`, `evidence_ids`, `who_feels_it`, `content_reality`, `strength` (1–5 after caps), `moment`+, `belief_from_ru`+, `belief_to_ru`+, `proof_ids`+, `factors`+ {F,S,P,D,O,C}}].
- `remarkables`+: [{`id`, `reality`, `evidence_ids`, `why_remarkable`}].

### G5. IdeaList (at least 24 candidates; each idea)

- `id`, `title`.
- `insight_ids`.
- `driver` (D2 id); `secondary_driver`+.
- `engine`+ (D3 id; this is the arm).
- `format`: production format, one of `close_talk` | `hands_demo` | `process` | `split_compare` | `text_over_footage` | `screen` | `ai_around_real` | `ugc` | `stitch`.
- `funnel`: attention | consideration | conversion | trust | retention | recruiting.
- `hook_ru`, `first_frame` (EN: exactly what is in frame 1).
- `hook_variants_ru`+: [{`archetype`, `hook_ru`, `first_frame`}], 2–3, with different archetypes.
- `on_screen_ru`: [string]. Every on-screen text line, in order.
- `what_happens`: beats with seconds, including the payoff second.
- `why_stop`, `why_share_or_save`.
- `share_line_ru`+: the DM line a sharer would type. `save_reason`+.
- `belief_shift`+: "from → to".
- `comment_prompt_ru`.
- `cta_ru`: containing `{CODE}`.
- `production`: {`mode`: worker | ai | mixed | ugc | screen, `worker_shots`: [{`what_ru`, `location`, `seconds`, `takes`, `say_ru`, `kind`: hook | demo | talk | detail | process}], `ai_parts`, `people_on_camera`}.
- `facts_used`: evidence ids.
- `kpi`: the behaviour metric that tests the driver, plus the business metric.
- `risks`.
- `rubric`: {stop, truth, share_save, comment, producible, brand_link, objective_fit}, each 1–5.
- `variance`+: low | high.
- `series_name_ru`+.
- `consent_needed`+: [who].
- `expires`+: when a time-sensitive fact must be re-checked.

### G6. TestPlan+ (alongside code's `selection` object)

- `week`.
- `slate`: [{`idea_id`, `role`: explore | exploit | series_pilot | wild_card | trend | conversion, `arm`, `variants`: [{`variant_id`, `archetype`, `hook_ru`, `platform`, `post_slot`, `code`}], `staff_min`}].
- `arms`: [{`arm_id`, `status`: new | active | leading | retired, `n_client`, `n_pooled`, `posterior_note`}].
- `outcome_primary`: "log(views / platform median) at 48 h and 7 d".
- `outcome_business`: "codes per 1000 reach per arm per sprint".
- `metrics_to_collect`: [string].
- `decision_rules`: [string]. F11, with client-specific numbers.
- `power_note`: string.
- `week_minutes`: number.
- `shoot_card_ru`: string.
- `standing_moments_ru`: [string], at most 3.

### G7. Campaign

- `name`, `big_idea`, `single_minded_message_ru`, `why_this_wins`. The last one cites insight and evidence ids, and the prior plus the plan to learn, never a forecast.
- `series`: [{`name`, `role`, `idea_ids`, `cadence`}].
- `offer`: {`needed`, `proposal`, `fact_ids`, `needs_owner_approval`}.
- `channels`: [{`channel`, `role`}].
- `weeks`: [{`week`, `goal`, `idea_ids`, `worker_ask_ru`, `ai_work`}].
- `measurement`: {`success_metric`, `attribution`, `leading_indicators`, `review_cadence`}.
- `decision_rules`, `learning_questions`.
- `owner_asks`: [{`ask`, `why`, `minutes`}].
- `risks`.
- `whatsapp_playbook`+: {`reply_templates_ru`, `first_reply_target_min`, `code_logging`}.
- `paid_boost`+: {`allowed`, `budget`, `trigger_rule`, `stop_rule`}.
- `profile_setup_ru`+: {`pinned`, `bio_line`, `highlights`}.

### G8. Review (critique)

- `persona`, `score`, `would_approve`, `best_idea`.
- `refutations`: [{`target`, `why_fails`, `severity`: fatal | major | minor, `fix`}].

### G9. WeeklyLearning+

- `week`.
- `posts`: [{`post_id`, `idea_id`, `variant_id`, `arm`, `platform`, `code`, `views`, `rel_log`, `hold`, `avg_watch`, `sends`, `saves`, `comments`, `codes`}].
- `arm_update`.
- `winners` (with intervals).
- `new_evidence`, `insight_updates`, `next_week_changes`.
- `knowledge_entries`: [{`id`, `vertical`, `finding`, `use`, `source`, `date`, `strength`}].
- `owner_report_ru`.

---

## H. Worked mini-example (HYPOTHETICAL: every business fact is an assumption, marked [A])

**Client:** a family bakery and confectioner in Karaganda [A].
- Sells walk-in pastries, plus custom cakes ordered in WhatsApp with a 3-day lead time [A].
- 2 bakers and 1 cashier [A].
- Instagram has 1,800 followers and a Reels median of about 900 views [A]. No TikTok [A].

**Boss (verbatim):** «Хочу, чтобы мы залетели, как кофейня у соседей.»

### H1. Intake (abridged)

- `request_type`: `awareness_or_viral`.
- `reframed_request`: raise the odds of breakout videos *and* turn the attention into custom-cake orders, the product that pays [A].
- `business_objective`: more custom-cake orders, within capacity.
- `marketing_objective`: Karaganda residents planning a family celebration in the next 2–3 weeks message the business on WhatsApp with a video code, within 6 weeks.
- `success_metric`:
  - name: cake inquiries by video code;
  - how measured: normalised codes in the weekly chat export, plus orders tagged by the cashier;
  - target: +30% over baseline B (B = 20 per week [A], from the chat export), within capacity;
  - by when: week 6.
- `leading_indicators`: sends per 1000 reach; saves per 1000 reach; at least one post at 10× or more of the median (≥9,000 views) by week 6; WhatsApp link taps from the profile.
- `guardrails`: orders above capacity (12 extra per week [A]) means missed dates; complaints that the cake «не как на фото».
- `realism`: +6 inquiries a week at an [ASSUMPTION] of 0.5–3 per 1000 reach needs 2,000–12,000 extra reach a week.
  - Verdict: `realistic` without virality. Virality is upside.
- `clarifying_questions`:
  1. «Что важнее через 6 недель: (1) заказы тортов, (2) люди в зале в будни? | По умолчанию: (1) | До: завтра 12:00»
  2. «Сколько дополнительных тортов в неделю вы реально успеете сделать? | По умолчанию: 12 | До: завтра 12:00»
  3. «Можно снимать лица пекарей или только руки? | По умолчанию: только руки | До: завтра 12:00»
- `push_back` (ru): «Обещать „залёт“ не может никто, но мы можем сделать так, чтобы каждый ролик работал на заказы тортов: 5 роликов в неделю, по 2–3 начала у каждого, и усиливать то, что выберут зрители. Считаем обращения по коду в WhatsApp, а не лайки.»

### H2. Inputs

Total owner time: 10 minutes.
- **have:**
  - 2GIS reviews and Instagram comments (automated);
  - WhatsApp export covering 60 days (owner, 2 min) [A];
  - owner voice note (5 min) [A];
  - price-list photo (1 min) [A].
- **missing:**
  - platform insights (fallback: public view counts);
  - consent for faces (fallback: hands only);
  - paid budget (fallback: organic only).

### H3. Evidence (excerpt, all [A])

| id | kind | claim | source | confidence |
|---|---|---|---|---|
| E01 | customer_language | «а будет как на картинке?» asked in 23/61 cake chats | chat export | verified |
| E02 | customer_language | price per kg is the first question in 31/61 chats | chat export | verified |
| E03 | customer_language | «успеете к субботе?» in 12/61, mostly on Wednesday–Thursday | chat export | verified |
| E04 | customer_language | «не приторный» appears in 9 of 140 reviews | 2GIS | verified |
| E05 | fact | cream is made in-house daily | owner voice note | likely → verified once filmed |
| E06 | moment | customers photograph the cake at pickup; children react | owner voice note | likely |
| E07 | constraint | at most 12 extra custom cakes a week | owner answer | verified |
| E08 | performance | a Reel of a baker writing a name in cream got 14,000 views vs a median of about 900 (n=1, so a prior only) | public Instagram | verified |
| E09 | proof_asset | price list dated this week | owner photo | verified |
| E10 | market | the 6 local peers post finished-cake photos with music; no process, no real sound | Tier 0 scan | verified |

### H4. Insights

- **I01 (strength 5).** When ordering a cake for a child's or family celebration, parents want a "wow" photo moment but fear «на фото одно, в жизни другое». The failure would be public, at the party.
  - Evidence: E01, E06.
  - Content reality: the reference picture next to the real cake at pickup (with consent); how the decoration is matched.
  - Belief shift: «заказной торт никогда не похож на картинку» → «видно, как его делают по вашей картинке».
- **I02 (strength 4).** Hosts want a cake guests actually finish; the fear is cloying cream.
  - Evidence: E04, E05.
  - Content reality: cream being whipped, filmed close with sound; a cross-section cut.
- **I03 (strength 3).** Price is the first question; people fear a surprise total.
  - Evidence: E02, E09.
  - Content reality: what makes one cake cost more than another (decoration). Needs owner approval.
- **I04 (strength 3).** Midweek panic about the weekend.
  - Evidence: E03, E07.
  - Content reality: true weekend availability, checked every Thursday.
- **R01 (remarkable).** Names written freehand in cream (the E08 outlier).

### H5. Ideas (7 of 26 shown; priors use the E2 weights)

| id | engine / driver | hook_ru | comment prompt / CTA | staff min | prior |
|---|---|---|---|---|---|
| ID01 | reply + series / participation | «Пишу кремом имя из комментариев» | «Чьё имя написать в следующем видео?» / «Торт с вашей надписью — код {CODE} в WhatsApp» | 3.65 | 4.18 |
| ID02 | sense / relief | «В отзывах пишут „не приторный“. Вот из чего наш крем» | — / «Код {CODE} — пришлём прайс и свободные даты» | 2.42 | 3.76 |
| ID06 | calendar / trigger | «Ещё успеваем к субботе: 3 торта» (the number comes from Thursday's order book) | — / «Код {CODE} — бронь до 18:00» (only if true) | 1.48 | 3.68 |
| ID04 | mistakes / practical_value | «3 вопроса кондитеру до заказа торта» | «Что ещё спросить? Ответим в следующем видео» / code | 2.00 | 3.60 |
| ID03 | guess / prediction_game | «Угадайте: сколько часов ушло на этот торт?» (true hours from the baker's log) | «Сколько поставили? Ответ в конце» | 2.83 | 3.42 |
| ID05 | why_it_costs / relief | «Почему два торта одного веса стоят по-разному» | — | 2.0 | 3.41 (blocked: needs owner approval of the price explanation) |
| ID08 | local + story / identity | «Какой торт был на каждом дне рождения в 90-х? Мы его до сих пор печём» (only if true [A]) | «А у вас какой был?» | 1.48 | 3.22 (wild card, high variance) |

Notes:
- **ID01 is participation, not bait.** Every commenter has a real chance of seeing their name in the next video. Only names the commenters themselves give, no surnames, and offensive ones are skipped.
- **Share line (ID01):** «Смотри, твоё имя написали!»
- **Share line (ID04):** «Ты же торт на субботу заказываешь — глянь».

### H6. Selection (week 1)

- **Slate:** ID01 (series pilot), ID02, ID04, ID06 (conversion), ID08 (wild card), plus one zero-minute piece: an anonymised chat question «А будет как на картинке?» answered over library footage.
- **Moved:** ID03 goes to week 2, which keeps week 1 within the minute budget.
- **Diversity check:** 5 distinct drivers. Funnel: 2 attention, 1 trust, 1 consideration, 1 conversion.
- **Variants:** 2–3 hooks per base video, rotated across Reels, TikTok and Shorts. About 15 posts, each with its own code (KT22, KT23 and so on).
- **Power note:** 4 active arms at about 4 posts each per week. No claims before pooled n reaches 30 per arm.
- **ID01 caution:** its prior is boosted by E08, but that is n=1. It sits in a pilot slot, not an exploit slot.

**Shoot card (ru), ≈16 minutes:**

> «Съёмка на неделю (≈16 минут). Телефон вертикально, протрите камеру, держите ближе 40 см к звуку. Каждый кадр — 2 дубля, начинайте за секунду до действия. Файлы присылайте сюда без монтажа до среды 18:00.
> ЦЕХ:
> 1) Крупно: первый штрих кремом, 3 сек × 3 дубля.
> 2) Напишите кремом 3 имени из списка, который я пришлю, по 15 сек на имя.
> 3) Крупно: венчик взбивает крем, телефон рядом с миской, 15 сек.
> 4) Разрез готового торта, 8 сек.
> 5) Покажите руками 3 вещи, о которых стоит спросить до заказа, по 5 сек.
> 6) Тот самый торт из 90-х: крупно, как собираете, 3 сек + 10 сек.
> ВИТРИНА (в четверг):
> 7) Торты, которые ещё можно забрать к субботе: 3 сек + 10 сек. Скажите мне, сколько их на самом деле.
> Всегда: если покупатель ахнул при выдаче — спросите „Можно сниму 10 секунд?“ и снимайте, только если ответил „да“.»

Minute check: 2 fixed + 2 locations + shots 11.03 + 1 for the Thursday set-up = 16.0, within 17.

### H7. Campaign (abridged)

- **name:** "No-surprise cakes".
- **big_idea:** for a parent, a custom cake is a public bet. We remove the surprise by showing how *their* cake is made, what drives the price, and when it can be ready.
- **single_minded_message_ru:** «Ваш торт — без сюрпризов.»
- **series:**
  - «Пишем имя»: attention and community, 2 per week;
  - «Без сюрпризов» (process, a picture vs the real cake, cream): trust, 2 per week;
  - «Четверг: успеем к субботе»: conversion, 1 per week;
  - reply videos: from week 2.
- **offer:** «Перед выдачей присылаем фото вашего торта в WhatsApp». An operational promise that turns I01 into a service. `needs_owner_approval: true`.
- **channels:**
  - Reels: main (existing audience);
  - TikTok: new account, exploration, cold start;
  - Shorts: cross-post;
  - WhatsApp: codes in, template out;
  - WhatsApp Status: the Thursday availability post to existing customers;
  - 2GIS: proof;
  - paid boost: none until approved.
- **whatsapp_playbook:**
  - template (ru): «Здравствуйте! Спасибо, что написали по коду KT22. Торт с надписью делаем от 3 дней. Подскажите дату и на сколько гостей — пришлём варианты и цену по прайсу. И подскажите, откуда о нас узнали?»
  - first reply within 15 minutes.
- **decision rules:**
  - A post at 2,700 views or more at 48 hours (3× median [A]) → 2 sequels.
  - «Пишем имя» continues as long as there are 20 or more name comments per episode (comment supply is the content supply).
  - Zero codes after 10 posts → check the CTA and reply speed first.
  - Orders above 10 extra per week (80% of capacity) → pause the Thursday conversion post.
  - Week 4: compare inquiries per week against B = 20.
- **learning questions:**
  - Does «Пишем имя» produce code inquiries, or only views?
  - Do sensory/process videos beat price-transparency videos on saves?
  - Does the Thursday trigger produce same-week orders?
  - Does TikTok (cold start) reach local buyers at all by week 4?
- **owner_asks:**
  - approve the photo-before-pickup offer (1 min);
  - approve the price explanation for ID05 (1 min);
  - set a fixed weekly shoot hour (1 min);
  - set a first-reply target (1 min).
- **risks:**
  - a single outlier (E08) over-weights the name series;
  - customers' reference pictures may be copyrighted: show them only on the customer's own phone screen, with consent;
  - a capacity overrun damages reviews.
- **cross-client output (week 4):** knowledge entries for the `reply` engine (personalisation from comments) and the `calendar` engine (a weekday trigger), labelled `hypothesis` until pooled n reaches 30 per arm.