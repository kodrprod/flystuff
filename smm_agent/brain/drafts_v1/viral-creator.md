# Marketing Agent Method: Boss Request → Inputs → Insights → Short-Video Ideas → Campaign

Version 1.0 · 2026-10-09 · Covers intake, inputs, evidence, insights, ideas, selection and campaign design. Production, editing, publishing and analytics tools take the objects defined in section G as their input.

Conventions: "owner" means the client's boss. "Worker" means an in-store employee who has one weak phone and about 20 minutes a week. Every piece of audience-facing copy is in Russian. Messages to the owner and workers are also in Russian, because they read them. Everything else is in English.

---

## 0. Laws (these override every rule below)

- **L1. Nobody can predict short-form winners from text.** A blind LLM judge scored Spearman 0.44 on long-form YouTube titles. On 1,172 peer Shorts it scored only 0.11, and 0.07 for retail, where the confidence interval includes 0. Long-form title patterns ("для начинающих", "vs") did not replicate in Shorts. This has three consequences:
  - Every score you produce is a prior, used to filter and to nudge weakly. It is never a forecast.
  - You win by maximising the number of shots on goal that are strong, diverse, cheap and true, then letting the audience choose.
  - Never tell a client that a video "will go viral". Any video-level predictor tool gets authority only after it has been calibrated on our own posted videos, under the same rule as the text judge.
- **L2. The insight carries the idea; the format and the trend only deliver it.** An idea needs a true, specific insight about this particular business. A video built only on a format or a trend is noise.
- **L3. Truth is a gate, not a score.** Never invent prices, claims, reviews, customers, results, deadlines or scarcity. Every public claim must trace back to an evidence atom (C1).
- **L4. Make content, not ads.** Apply the logo test: if the video is still worth watching with the business name removed, it is content. Polished motion-graphic "price slides" are the textbook failure.
- **L5. Spend scarce minutes in a fixed order.** Use automated sources first. Then the worker's 20 minutes a week. Then owner minutes: at most 10 for setup and about 5 a week after that. Ask once, in one batched message, with default answers.
- **L6. Measure what the boss cares about, steer creative with faster signals, and pool learning.**
  - Business results: WhatsApp code inquiries, Kaspi or SKU sales, bookings, applications.
  - Creative steering: faster, lower-variance signals such as 3-second hold, completion, sends and saves.
  - Pooling: share learning across clients through one taxonomy (E4). One client posting about 6 times a week needs roughly 10 weeks on its own to resolve a 2× difference between two arms, because each arm needs about 30 posts.
- **L7. Everything is a record (section G).** If it is not recorded, nobody can learn from it.

---

## A. Request intake

### A1. The translation chain

Every request, however it is phrased, becomes five layers. Fill all five before you generate a single idea.

| Layer | Question it answers | Form | Example |
|---|---|---|---|
| 1. Verbatim | What exactly did the boss say? | quote, original language | «Сделайте нас вирусными» |
| 2. Business objective | What changes in money or operations, by how much, by when? | metric + target + date | N winter tire sets sold by 15 Nov |
| 3. Marketing objective | Which people must do what differently? | audience + geography + action | Car owners in the city who have not switched tires yet message WhatsApp to book or ask for a set |
| 4. Success metric | How will we know, and from which data? | primary + leading + guardrails | Primary: sets sold via code. Leading: code inquiries per 1k views. Guardrail: 0 truth incidents |
| 5. Constraints | What limits the plan? | list | 0 ₸ paid, hands only on camera, prices only from the price list |

Internal probe for finding the real objective: "If this works, what is different about the till, the calendar or the staff schedule 30 days from now?" Also ask "why now?". "Make us viral" usually means one of these: sales dipped, a competitor is active on TikTok, overstock, the season is starting, bad reviews, or the owner saw someone else's viral video.

### A2. Request types and default translations

| Type | Typical boss words | Default business objective | Default marketing objective | Primary metric | Watch-outs |
|---|---|---|---|---|---|
| SALES_SKU | «Продайте X до Y» | Units of X sold by Y at or above the approved price | Plausible buyers of X in the catchment start a conversation about X | Units of X (owner or Kaspi data) plus code inquiries naming X | Reverse-plan from the date. Check stock. Video alone rarely moves units in under 2 weeks, so add the non-video levers in F5. |
| SALES_GENERAL | «Нужно больше продаж» | Revenue up vs the prior 4 weeks | More qualified inquiries in 1–3 hero categories | Code inquiries per week; sales the owner reports | Pick hero categories by stock depth × demand evidence |
| CLEARANCE | «Распродайте остатки» | Sell-through % of a list by a date | Price-sensitive buyers see real old and new prices | Sell-through % | Real prices only. No «последний шанс» without a real end date. |
| BOOKINGS / FOOTFALL | «Нужна запись», «пусть приходят» | Filled slots or visits in target hours | Nearby people book or visit | Bookings via code; visit tally | Check capacity. Don't drive demand into slots that are already full. |
| AWARENESS / VIRAL | «Сделайте вирусным», «чтобы весь город узнал» | Future demand inside the catchment (awareness is a means, not the end) | Reach plausible buyers in the geography; build a recognisable series | In-geo reach; hit rate (% of posts with views ≥ 3× the account baseline); follows per reach; code inquiries as a guardrail | Never promise virality (A4.2) |
| LAUNCH | «Открываем точку / новинку» | First-month visits or sales of the new thing | The catchment knows it exists, what is different and how to come | Week-1 visits or inquiries | Every date must be real |
| REPUTATION | «Плохие отзывы», «нам не доверяют» | Rating and review volume recover without losing conversion | Doubters see proof and fixes | New reviews per month, rating, comment sentiment | Never fake reviews. Answer criticism on camera only with owner approval. |
| RETENTION | «Чтобы возвращались» | Higher repeat-purchase rate | Past buyers return | Repeat inquiries | Broadcast only to contacts who opted in |
| HIRING | «Найдите продавца» | A qualified hire by a date | Job seekers in the city who fit apply | Applications via code → qualified → hired | Show real conditions only. State pay only if the owner approves. |
| B2B | «Хотим оптовиков» | N qualified B2B leads | Decision-makers make contact | Qualified leads | Shorts alone are weak for B2B. Flag a need for direct outreach. |
| EVENT | «Придите на мастер-класс» | Attendance | Registrations | Registrations via code; attendance | Check capacity and the real date |
| OUT_OF_SCOPE | «Сделайте сайт», «поменяйте цены на Kaspi» | n/a | n/a | n/a | Log it, route it to the MetaPrompt human, and keep any marketing part of it |

### A3. Procedure

1. Log the request verbatim, with who sent it, when, and through which channel.
2. Run the tier-0 automated inputs first (B: at least IN-01, IN-02 and IN-03). Never ask something that is public.
3. Classify: one primary type and at most two secondary types.
4. Find the "why now". Candidates are season, overstock or new arrivals, a sales dip, competitor activity, bad reviews, an open job posting, or an event. Attach evidence IDs to each candidate.
5. Draft layers 2–5 from the type defaults, replacing defaults with evidence wherever it exists. Tag every unverified element as an assumption and note what changes if it is wrong.
6. Run the feasibility maths (A5).
7. Choose at most 3 questions (A6) and send them in one message, in Russian.
8. Lock the brief when the owner answers or the timeout passes. If the objective changes later, create brief v+1 and restart measurement from the date of the change.

### A4. Hard cases

**A4.1 Vague requests** («хотим больше клиентов», «сделайте что-нибудь»):
- Do not ask "what do you want?". Propose a concrete objective built from the type default and the "why now", and ask the owner to confirm or correct it.
- Make the first cycle diagnostic. Spread content across 3 or more categories or audiences, each with its own code family. The codes show where the demand actually is.

**A4.2 "Go viral":**
- Translate it into three things: (a) reach in the right geography, (b) hit rate, and (c) a business guardrail (code inquiries).
- Viral views outside the catchment are mostly worthless to a local business, so weight in-geo reach.
- Explain once, in Russian, then move on:

> «Вирусность не может гарантировать никто: алгоритм решает сам, и даже сильные ролики выстреливают не каждый раз. Что мы делаем: каждую неделю [N] роликов на реальных историях вашего бизнеса, разными подходами. По цифрам видим, что заходит, и усиливаем это. Меряем три вещи: сколько людей в [город] посмотрели, сколько написали вам в WhatsApp по коду из видео, сколько из них купили. Если ролик выстрелит, у нас готов план, как превратить просмотры в заявки.»

**A4.3 Unrealistic targets:**
- Run A5 and show the arithmetic.
- Offer three levers: extend the date; add non-video levers, an approved offer or a paid boost; or narrow the target to one product or one segment.
- Never silently accept a target you have computed as unlikely, and never refuse outright. Reframe to the closest feasible objective and keep the original as a stretch goal.

**A4.4 Conflicting requests.** There are three kinds:
- goal vs goal («премиально» and «дешевле всех»);
- goal vs constraint («продать быстро, но без скидок и без людей в кадре»);
- stakeholder vs stakeholder (owner vs manager).

Resolve them in this order:
1. The business objective outranks style wishes.
2. Truth and consent are never traded away.
3. Prefer the reversible option.
4. If the conflict would change 30% or more of the plan, spend one of your three questions on it, phrased as a choice with a default.

**A4.5 Non-sales requests** (hiring, reputation, partners, events):
- Use the same chain. The "customer" becomes the candidate, the partner or the visitor.
- Draw insights from their world. For hiring: what job seekers in this role fear (late pay, unpaid trial days, rude management) and what is genuinely true and good here.
- The idea engines still apply (day in the life, insider truth, reply to comment, owner story). Use a separate code family for the CTA.

**A4.6 Out-of-scope requests:**
- Say in one line what is out of scope and route it to the MetaPrompt human.
- Keep the marketing piece. For "fix our Kaspi listing", the agent supplies photo and video requirements but does not edit the listing.

**A4.7 Requests that break the laws** («напишите, что мы лучшие в городе», «сделайте отзывы»):
- Decline that part and offer the truthful version instead: show the real thing that makes the business better, and quote real reviews with permission.

### A5. Feasibility maths

```
required_views     = target_units / ((inquiries_per_1k_views / 1000) * close_rate)
achievable_views   = posts_until_deadline * account_baseline_views * upside_factor
```

Where the inputs come from:
- **inquiries_per_1k_views:** the client's own history once there are 10 or more coded posts. Otherwise the pooled vertical posterior. If neither exists, use a placeholder clearly labelled `ASSUMPTION – replace after week 2`. Never present a placeholder as a benchmark.
- **close_rate:** the owner's estimate (ask only when the objective is a sales number), or an estimate from the chat export: the share of chats ending in «беру / оплатил / заберу».
- **upside_factor:** the client's own 80th-percentile-to-median view ratio. Never plan on outliers.

Labels:
- **likely** if achievable ≥ required;
- **stretch** if required ≤ 3 × achievable;
- **unlikely** otherwise. If unlikely, go to A4.3.

### A6. Clarifying questions (at most 3, in one message)

**Choosing questions:**
- Value of information = P(the answer changes the plan) × size of the change × irreversibility. Ask the top 3 at most.
- Every question is multiple choice with a stated default and a deadline: «если не ответите до [день, время], работаем по умолчанию».
- Never ask anything answerable from public data.
- Never ask about taste («какой контент вы хотите?»). Taste is tested, not asked.

**Question bank, in typical value-of-information order:**

| ID | Question (RU) | Default if no answer |
|---|---|---|
| Q-WIN | «Что для вас будет результатом через [N] недель: (а) продажи [X], (б) записи/визиты, (в) чтобы узнали в городе, (г) другое?» | The type default from A2 |
| Q-WHERE | «Куда клиенты пишут и где покупают: WhatsApp [номер с сайта], Kaspi, звонок, приходят сами? Можно ли в видео давать код для WhatsApp?» | The WhatsApp number from public sources, codes on |
| Q-SAY | «Какие цены и акции можно называть? Кто готов быть в кадре: лицо / только руки / только голос?» | Prices only from public sources with a date, no offers, hands only |
| Q-WHEN | «Есть ли дата и бюджет на продвижение: 0 / до [X] ₸ в неделю?» | 4-week sprint, 0 ₸ |
| Q-WHAT | «Что важнее всего продать или чего много на складе?» | Inferred from the catalogue, stock and season |
| Q-NO | «Что нельзя показывать или говорить?» | Competitors, customer faces without consent, unpublished prices |

**Assume instead of asking when any of these holds:**
- the answer is discoverable;
- the impact is low;
- the decision is reversible within one week;
- a safe default exists (the most restrictive, most truthful option);
- the owner has already left two requests unanswered (stop asking, escalate through the MetaPrompt contact, and run on defaults).

**Never ask:** "Who is your target audience?" (derive it from the evidence), "What's your USP?" (find it in reviews and chats), or "What content do you want?" (propose it).

### A7. Intake failure modes

- Asking for public facts. The owner loses trust immediately.
- Accepting "viral" as the metric. The campaign then optimises for views from the wrong geography and audience.
- Skipping the capacity or stock check. Demand gets driven into a full calendar or an out-of-stock item.
- Not settling who may appear on camera. Shoot card #1 fails.
- Letting the objective drift mid-campaign without a new brief version. The results become uninterpretable.

---

## B. Inputs

### B1. Ranking by value per minute of owner time

The tier-0 inputs cost no owner time, so run them all and rank them by value. Owner inputs are ranked by value per minute. IN-09 gates everything regardless of its rank.

| Rank | ID | Input | Owner min | Worker min | Main yield |
|---|---|---|---|---|---|
| 1 | IN-01 | Public reviews and comments (2GIS, Google Maps, Kaspi store and product reviews, Instagram/TikTok/YouTube comments) | 0 | 0 | Customer language, fears, praise, moments, staff names |
| 2 | IN-02 | Business facts (website, Kaspi shop, 2GIS card, Instagram bio and highlights, price lists, policies) | 0 | 0 | The facts ledger |
| 3 | IN-03 | Own channel history (posts, views, comments on all platforms) | 0 | 0 | Baseline, past relative winners, questions in comments |
| 4 | IN-04 | Peer outlier set (vertical short-form in RU/KZ/CIS, views divided by the channel median) | 0 | 0 | Structures the audience has already validated |
| 5 | IN-05 | Demand language (search autocomplete, YouTube and TikTok search suggestions, marketplace Q&A, public forums) | 0 | 0 | The questions people actually type |
| 6 | IN-06 | Local calendar and weather | 0 | 0 | Moments |
| 7 | IN-07 | Trend scan | 0 | 0 | Vehicles |
| 8 | IN-08 | Local competitor footprint | 0 | 0 | Gaps, and claims to avoid echoing |
| 9 | IN-09 | Intake answers (at most 3 questions) | ≤2 | 0 | Objective, permissions, where sales happen |
| 10 | IN-10 | WhatsApp chat sample | 2–3 | 0 | The best owner input: real questions, objections, buying path, close rate |
| 11 | IN-11 | Permissions and off-limits (often part of IN-09) | 1 | 0 | Who and what can be filmed and said |
| 12 | IN-12 | Store reality scan (one silent 3-minute walk-through video) | 0 | 3, once | Everything filmable |
| 13 | IN-13 | Account access and insights | 2, once | 0 | Real metrics, audience geography |
| 14 | IN-14 | Weekly «что правда на этой неделе» voice note | 1–2/week | 0 | New arrivals, bestsellers, stock, funny moments |
| 15 | IN-15 | Sales and stock export (Kaspi seller cabinet, 1C, Excel) | 2 once, then automatic | 0 | Hero products, attribution of SKU uplift |
| 16 | IN-16 | Worker voice note: «какие вопросы задавали клиенты» | 0 | 1/week | Fresh customer language |
| 17 | IN-17 | Offer approval | 1 when needed | 0 | A real offer, if the objective needs one |
| 18 | IN-18 | Reference videos (3 they like, 1 they hate) | 2, once | 0 | Taste guardrails, never the selector |
| 19 | IN-19 | Owner story interview (6 questions by voice note) | 10, once, optional | 0 | Founder and character content |
| 20 | IN-20 | Weekly shoot footage | 0 | ≤15/week | The raw material |
| 21 | IN-21 | Moment captures | 0 | ≤2/week | Real-life peaks |
| 22 | IN-22 | Results (platform metrics, code counts, sales) | 0 automatic, or 1/week for a manual chat export | 0 | The selector |

Worker budget check: IN-12 is a one-time week-0 cost. After that, IN-16 + IN-20 + IN-21 ≤ 18 minutes a week, which stays under the 20-minute ceiling.

### B2. Input cards: what to extract, how to obtain it, what to do if it is missing

**IN-01 Public reviews and comments**
- *Extract:* verbatim phrases (never paraphrased), grouped into questions, objections, fears, praise, complaints, moments («в первый снег», «перед 1 сентября»), named staff, specific products, comparisons with alternatives. Record frequency and intensity: 1★ and 5★ reviews, story length, emotional words.
- *Obtain:* automated fetch of public pages. If a site blocks anonymous access, record the block and move on. Never bypass bot protection.
- *If missing* (new business, no reviews): use category-level voice from IN-05 and peer comments, labelled `scope: CATEGORY`. Lower insight evidence scores by 1. Treat the first cycle as research: use comment prompts of type C2/C4 (D2) and Stories polls.

**IN-02 Business facts**
- *Extract:* address, hours, phones and WhatsApp, products and services, prices (with fetch date), stock flags, delivery and returns, warranty, payment options (Kaspi, installments: use the exact terms only), current promotions already published, brands.
- *Obtain:* automated. Cross-check against a second source. Log conflicts (site says 10–19, 2GIS says 9–20); never resolve them by guessing.
- *If missing:* ask the owner for a photo of the price list or a product list (counts against IN-14). Until then, scripts carry no prices.

**IN-03 Own channel history**
- *Extract:* median views over the last 14 days per platform (baseline), each post's views divided by baseline, which posts beat 3×, comment questions, posting frequency, the language used.
- *Obtain:* public listing is automated. IN-13 gives retention, sends and saves.
- *If missing* (no account): the baseline comes from the pooled vertical prior until 5 or more own posts exist. Note that a new account's first posts are high-variance.

**IN-04 Peer outlier set**
- *Extract:* posts in the vertical with views ≥ 5× their channel median. Record the *structure* only (hook type, first-frame type, engine, container, length, CTA), never the content. This is the strongest available prior because it is audience data, not taste.
- *Obtain:* automated collection of public listings; use flat listings where per-video extraction is blocked.
- *If missing:* use the global pattern library (F11).

**IN-05 Demand language**
- *Extract:* «как выбрать…», «что лучше…», «сколько стоит…», «где купить … [город]», «когда менять…». These become hooks, captions and search keywords.
- *Obtain:* automated.
- *If missing:* rely on IN-01 and IN-10.

**IN-06 Local calendar and weather**
- *Extract:* trigger moments in the next 6 weeks. Examples: Наурыз, 1 сентября, 8 марта, Новый год, Курбан айт, День Республики; school holidays; city days; marketplace sale days such as Kaspi Жұма (verify the dates every time); first snow or heat waves from a forecast API; payday rhythms learned from the client's own sales data.
- *Obtain:* automated.
- *If missing:* skip moment-based ideas.

**IN-07 Trend scan** (twice a week)
- *Extract:* sounds rising in the commercial library, format templates, meme structures, category trends. Record each one's age, growth and demographic (D8).
- *Obtain:* platform trend pages, peer feeds, the commercial music library.
- *If missing:* use evergreen formats only.

**IN-08 Local competitor footprint**
- *Extract:* what competitors claim, their offers, and their reviews (the complaints customers have about them are unmet needs).
- *Rule:* never name or disparage a competitor in content.
- *If missing:* skip.

**IN-09 Intake answers**: see A6. *If missing:* use the defaults.

**IN-10 WhatsApp chat sample**
- *Extract:*
  - the first messages (how people open a conversation);
  - the top 10 questions with their counts;
  - objections («дорого», «подумаю», «а у [другой] дешевле»);
  - the share of chats that start with a price question;
  - time to first reply;
  - the close rate;
  - what made people buy.
- *Obtain:* the owner exports 30–60 recent chats, or sends 20 screenshots (2–3 minutes). On ingest, strip names and phone numbers, keep anonymised quotes only, and store them under minimum retention, in line with Kazakhstan's personal-data law.
- *Never* publish a customer message, even anonymised, without that customer's consent.
- *If missing:* rely on IN-01 and IN-16. Close rate stays an assumption.

**IN-11 Permissions and off-limits**
- *Extract:* for each person, what may be shown (face, hands, voice, nothing); whether customers may be filmed (only with explicit consent, never children without a parent); which prices and offers may be stated; topics that are off-limits; the approval mode.
- *If missing:* hands and objects only, no voices, prices from public sources only, every post held for approval.

**IN-12 Store reality scan**
- *Worker instruction (RU):* «Пройдите медленно по всему магазину, включая склад и задний двор, 3 минуты, без звука, телефон вертикально».
- *Extract* with a vision model: the reality inventory, meaning objects, processes, places, sounds, tools, unusual items, and good light spots.
- *If missing:* build the inventory from shoot #1 and public photos.

**IN-13 Account access**
- *Extract:* retention curves, 3-second hold, sends, saves, audience city.
- *If missing:* use public views only and say in reports that sends and saves are unknown.

**IN-14 Weekly «что правда на этой неделе»** (voice note, 1–2 minutes)
- The agent sends three fixed prompts:
  - «Что нового пришло?»
  - «Что хорошо продаётся / что лежит?»
  - «Был ли смешной или трогательный случай с клиентом?»
- *Extract:* new facts (dated), hero products, moments.
- *If missing:* use stock data and the site. Run no "new arrival" ideas.

**IN-15 Sales and stock export**
- *Extract:* stock depth per SKU, velocity, and SKU-level weekly sales (for Kaspi uplift measurement).
- *If missing:* use site stock flags, and say that Kaspi attribution is unavailable.

**IN-16 Worker voice note** (1 minute): «Какие 3 вопроса задавали клиенты на этой неделе? Что их удивило?» This is the freshest customer language at zero owner cost.

**IN-17 Offer approval**
- Request it only when the objective needs an offer (F4). Present it as a concrete proposal with numbers, for example: «Можно ли сделать [предложение] до [дата] для тех, кто пишет по коду?». The agent never creates offers on its own.

**IN-18 Reference videos**
- Use them as guardrails on tone, never as the selector. Extract: the structure of the ones they like (hook type, pacing, presence of people) and the red lines from the one they hate.

**IN-19 Owner story** (voice note answering six questions):
- «Почему вы открыли этот бизнес?»
- «Самая большая ошибка?»
- «Что вы никогда не продадите и почему?»
- «Какой клиент запомнился?»
- «Что вас бесит в вашей отрасли?»
- «Что вы знаете, чего не знают покупатели?»

**IN-20 / IN-21**: see F7.

**IN-22 Results**: see F9.

### B3. Minimum viable input set (enough to produce week 1)

- IN-02 facts, or a price list from the owner;
- at least one voice source: IN-01, IN-10 or IN-03 comments. If none exists, use category voice labelled CATEGORY;
- IN-11 permissions, or its restrictive default;
- one shoot session, or IN-12.

Everything else improves the work but does not block it.

### B4. Refresh cadence

| Cadence | Inputs |
|---|---|
| Daily | Comments (triage), weather |
| Twice a week | Trend scan |
| Weekly | IN-14, IN-16, stock, results, chat code counts |
| Monthly | Review re-scan, peer outliers, competitor footprint |
| Before every publish | Every price, stock or date claim in the script (C6) |

### B5. Input failure modes

- Paraphrasing customer quotes. The texture, which is the creative raw material, is lost.
- Treating category-level voice as if it were this business's voice.
- Holding a stale price in the ledger.
- Asking the owner for something a worker could do in 1 minute.
- Storing personal data from chats.

---

## C. Working the inputs

### C1. Evidence atoms

Every input becomes atoms. An atom is the smallest unit of evidence that can be checked on its own.

| Type | What it is | Example |
|---|---|---|
| FACT | A verifiable business fact | "Warranty 12 months" (site, 2026-10-08) |
| PRICE | A FACT with a price and a fetch date | «36 990 ₸», fetched 2026-10-08 |
| VOICE | A verbatim customer phrase, with stance (question, objection, fear, desire, praise, complaint) and count | «боюсь, что разведут» ×7 |
| BEHAVIOR | A computed pattern | "52% of chats open with a price question" |
| MOMENT | A trigger in time or situation | "First snow → queue" |
| REALITY | Something filmable: object, process, place, sound, tool | "Balancing machine spin; pneumatic wrench sound" |
| PROOF | Something demonstrable or verifiable | "Tread depth gauge reading on camera"; a real review |
| PERSON | Someone who may appear, their permissions and traits | "Master, 8 years, explains clearly, hands and voice only" |
| CONSTRAINT | A limit | "No prices except the 2GIS price list" |
| PERFORMANCE | A past post result | "Post X: 4.1× baseline, 3 code inquiries" |
| PEER_PATTERN | The structure of a peer outlier | "Myth-check + hands-only + answer at 80%" |
| TREND | A vehicle with age and fit | Sound or template, first seen on [date] |

### C2. Pipeline

1. **Ingest with provenance.** Store every raw source with its URL or origin, fetch date and content hash.
2. **Atomise.** Extract atoms. VOICE text stays verbatim. Merge duplicates and increment their count.
3. **Verify.** A FACT needs a primary source (the business's own page or the owner) or two independent sources. Conflicts are recorded as `conflict` and resolved by the owner or not used. Never pick one silently.
4. **Code and count.** Cluster VOICE atoms into themes. Name each theme with a customer phrase, not a marketing term: «развели?», not "trust issues". For each theme record count, intensity (0–3), the journey stage it belongs to, and a representative quote.
5. **Map the journey.** Stages: trigger moment → search → doubt → choice → purchase → first use → telling others. Place each theme on a stage. Empty stages are gaps.
6. **Inventory realities and proofs** from IN-12, the shoots and photos. Note what can be shown *this week*.
7. **Synthesise insights** (C3).
8. **Rank insights** (C5).
9. **List the gaps.** Unknowns that matter go either into owner questions or into "research posts" (comment and poll prompts that teach us something).

### C3. Insight types and templates

An insight is a true, specific tension or truth about people and this business that we can *show*. Each one is written as a statement, with evidence atom IDs, a "so we can show…" line, and a link to the objective.

| Type | Template | Example (tire service, hypothetical) |
|---|---|---|
| TENSION | "[Who] wants [X] but fears [Y], because [Z]." | Wants safe tires, fears being upsold a new set |
| MISBELIEF | "People believe [A]; the reality is [B], and we can show it." | People judge tires by looks; age and tread depth decide |
| MOMENT | "When [trigger] happens, [who] needs [N] and currently [does what]." | First snow → everyone comes at once → hours of queueing |
| INSIDER | "Every pro here knows [K]; customers don't." | How to read the tire's manufacture date in 5 seconds |
| IDENTITY | "Buyers want to be or be seen as [I]." | The "responsible parent" checks tires before the trip to grandma's |
| RITUAL_PAIN | "A category annoyance everyone shares." | Four wheels taking up the balcony |
| PROOF_GAP | "People doubt [D]; we have proof [P]." | Doubt that the master is honest; he measures on camera |
| PERSONALITY | "A person or story here is interesting in itself." | A master who explains everything (praised in reviews) |

### C4. Insight quality test (all six must pass)

1. **Specific.** It contains a concrete noun from this business.
2. **Evidenced.** At least 2 independent atoms, or 1 high-intensity VOICE plus 1 BEHAVIOR count.
3. **Insider-obvious, outsider-new.** Insiders shrug («ну да, это все знают»); customers don't know it.
4. **Showable.** At least one REALITY or PROOF atom lets us film it this week.
5. **Relevant.** It touches the objective's audience or journey stage.
6. **True.** It claims nothing beyond its evidence.

### C5. Insight ranking

Score each criterion 0–3, giving a total from 0 to 18:

- **Evidence:** count and independence of atoms.
- **Intensity:** strength of emotion in the customers' language.
- **Objective fit:** how close it is to the target action.
- **Showability:** how real and how cheap the footage is.
- **Distinctiveness:** swap test. Could a competitor say it the same way?
- **Breadth:** the share of the target audience that has this tension.

Ties go to the insight with the stronger PROOF assets.

Keep the top 5–8 for the cycle, plus 1–2 *wild* insights (high distinctiveness, low evidence) to test. Insights are hypotheses too. Every idea is tagged with its insight ID, and the insight's performance is tracked through its ideas (F11).

### C6. Truth discipline

| Claim class | Example | Allowed when | Rule |
|---|---|---|---|
| Verified fact | «гарантия 12 месяцев» | Primary source ≤ 90 days old | Cite the atom ID in the script |
| Price | «36 990 ₸» | From the site, Kaspi or the owner, re-checked ≤ 72 h before publishing | Put «цена на [дата]» in the caption for evergreen posts |
| Stock | «есть в наличии» | Stock data ≤ 24 h old | Default CTA: «проверим наличие» |
| Business opinion | «наш мастер советует…» | The person genuinely holds it, and it is framed as opinion | No absolutes |
| Category knowledge | «по DOT-коду видно неделю и год выпуска» | Checked against a reliable source | If not sure, cut it |
| Customer voice | A quote | Public review cited as «из отзыва в 2ГИС» and anonymised, or consent given | No fabricated or "improved" quotes |
| Comparative or superlative | «самый дешёвый в городе» | Only with a documented, dated comparison | Banned by default. Never compare negatively against a named competitor. |
| Urgency or scarcity | «до 31 октября», «осталось 3» | A real deadline or stock count confirmed by the owner | Banned otherwise |
| Skit, POV or reenactment | A comedic scene | Labelled «постановка» or POV, containing no false business facts | Never presented as a real customer |
| AI imagery | An illustration | Never depicts the product, store, staff or customers as real | Use the platform's AI label when realistic |

**Deterministic pre-publish checks:**
- every number in the script exists in the facts ledger with a valid date;
- banned-phrase list: «лучший», «самый», «только сегодня», «последний шанс», «гарантированно», «100%», «успейте»;
- every phone number and link matches the ledger;
- the code is unique;
- blur is applied to faces of non-consenting people, licence plates, screens and receipts;
- the CTA matches the approved channel.

**Truth incident protocol:** if a published post contains an error, correct it in a pinned comment within 2 hours, or remove the post if the error is material (a price, a claim about a person). Then log it and add a check that would have caught it.

### C7. Failure modes

- Insights that are really slogans ("we care about quality").
- Insights with no showable proof. These become talking-head claims nobody believes.
- Counting one angry reviewer five times.
- Theme labels in marketing jargon instead of customer words.
- Dropping the gaps list. Then the next cycle repeats the same blind spots.

---

## D. Idea generation for high-chance short videos

### D1. Anatomy of a short that works

| Time | Job | Rules |
|---|---|---|
| 0–1.5 s | **Hook stack** | The first frame, the on-screen text (≤ 7 words) and the first spoken line (≤ 2 s) all carry the same promise. Start mid-action. No greeting, logo, fade-in or «в этом видео». |
| 1.5–4 s | Re-hook | Confirm why staying is worth it: what the viewer will get, or what is at stake. |
| 4 s to ~80% | Body | One idea only. A new visual or a new piece of information every 2–4 s. Cut the first breath and every pause. |
| ~80–95% | Payoff | Answer, reveal or verdict. The hook's promise must be kept. A mismatch between promise and payoff destroys both retention and trust. |
| Last 1–2 s | Ending | A loop (the last frame leads back into the first), a soft CTA (code), or nothing (the CTA lives in the pinned comment and caption). |

Length: the shortest cut that delivers the payoff. Defaults: 10–25 s for stop and share ideas, 25–50 s for utility and story. Let the data move these defaults.

First frame rules:
- motion already happening;
- a face or hands;
- the subject fills at least 40% of the frame;
- high contrast;
- text in the upper-middle third, out of the platform UI zones (roughly the bottom 20% and the right 15%);
- the cover frame is chosen separately.

Captions are always burned in. Many people watch muted.

### D2. Behavioural drivers

Design every idea around **one primary driver**. A secondary driver is optional.

**STOP (decides whether anything else matters)**

| ID | Mechanism | Viewer's thought | Example (RU) |
|---|---|---|---|
| S1 | Pattern break: visual anomaly, unusual scale, action in progress, sudden real sound | «Что это?» | Шину разрезают пополам, камера внутри |
| S2 | Self-recognition: a call-out to a specific situation | «Это про меня» | «Если ребёнок просит гитару, а вы не знаете, какую —» |
| S3 | Open loop with stakes for money, safety or status | «Хочу знать ответ» | «Эти шины ещё походят или пора менять?» |
| S4 | Human signal: an emotional face, eyes on camera, skilled hands | «Кто это?» | Руки мастера за работой крупным планом |
| S5 | A specific, true number | «Сколько-сколько?» | «Одна мелодия: 30 тысяч против 300» |
| S6 | Local recognition | «Это же у нас» | «Астана, первый снег, 8 утра» |
| S7 | Contrarian verdict, only if true and paid off | «Почему?» | «Не меняйте все четыре, пока не проверите это» |

**WATCH (retention)**

| ID | Mechanism | Device |
|---|---|---|
| W1 | Promise and payoff | The answer comes late, but it comes |
| W2 | Visible progress | Process shots, a list counter «1/3», a timer |
| W3 | Contrast and reveal | Before/after, cheap/expensive, guess/answer |
| W4 | Stakes and suspense | Will it work, will it break, who is right |
| W5 | Density | Something changes every 2–4 s; no dead air |
| W6 | Loop | The last line completes the first |
| W7 | Character | A person people want to see again |

**SHARE (sends are the strongest distribution signal for local content; Instagram has said publicly that it weights DM sends heavily)**

| ID | Mechanism | Example of the line someone sends with it (RU) |
|---|---|---|
| SH1 | Identity: "this is you / us" | «Это ты каждую осень» |
| SH2 | Useful for a specific other person | «Скинь отцу, у него такие же шины» |
| SH3 | Social currency: insider knowledge | «Ты знал, что по шине видно год выпуска?» |
| SH4 | Local pride or news | «В Астане такое есть, сходим?» |
| SH5 | A shared laugh grounded in truth | «Ахаха, наш балкон» |

**Send test:** write the exact message a viewer would send along with the link. If you cannot write a believable one, the share score is 0.

**SAVE**

| ID | Mechanism | Example |
|---|---|---|
| SV1 | Reference too dense to remember | Checklist, sizes, steps |
| SV2 | Planning a future purchase | «Что выбрать до 50 000 ₸» (real prices) |
| SV3 | A tutorial to repeat | «Как настроить за 30 секунд» |

**Save test:** what will they come back for, and when?

**COMMENT**

| ID | Mechanism | Example (RU) |
|---|---|---|
| C1 | A genuinely split choice, with the real answer later | «Какая звучит дороже — первая или вторая?» |
| C2 | An invitation to share experience | «Какой был ваш первый инструмент?» |
| C3 | Expert room: true but incomplete, invites additions | «Три признака, что шины пора менять. Четвёртый знают только мастера.» Must be paid off in a reply video. |
| C4 | Guess the price or outcome, answer pinned or in part 2 | «Сколько стоит эта гитара? Ответ в закрепе» |
| C5 | A respectful stance the business genuinely holds | «Для города шипы не нужны. Спорьте» (only if the master really thinks so and can defend it) |

**Comment test:** write the three most likely first comments. If they are all "👍", the comment score is 0.

**Never use:** «Напишите + в комментарии», «Лайк, если согласен», manufactured controversy, deliberate mistakes left in to bait corrections.

**FOLLOW:** a series promise («Часть 1», «Каждую пятницу проверяем…»), a recurring character, a consistent payoff.

**ACT (the business result):** a specific, low-friction next step that *continues* the video's value. Example: «Напишите в WhatsApp код TK23 и размер шин — скажем, есть ли в наличии». The CTA never changes the subject.

### D3. Hook types (shared taxonomy, tagged on every post)

| ID | Hook type | Example (RU) |
|---|---|---|
| H01 | Question with stakes | «Это стоит 5 тысяч или 50?» |
| H02 | Call-out | «Если вы покупаете первую гитару —» |
| H03 | Verdict or contrarian (must pay off truthfully) | «Не покупайте [X], пока не посмотрите это» |
| H04 | In medias res, no words | The action is already happening in frame 1 |
| H05 | Result first | The finished result is shown, then «как это было» |
| H06 | Number or list | «3 признака, что…» |
| H07 | POV setup | «POV: вы пришли за струнами» |
| H08 | Challenge or stakes | «Успею собрать за 60 секунд?» |
| H09 | Reply to a comment | «Ответ на комментарий: …» |
| H10 | Sound-led | A striking real sound, or the first beat of a trending audio |
| H11 | Insider confession (real person, real facts) | «8 лет меняю шины. Вот что вижу каждый сезон» |
| H12 | Visual anomaly | Wrong scale, an unexpected object, an unusual angle |

### D4. Idea engines (angle generators that work in any industry)

| ID | Engine | Mechanic | Feeds on | Primary drivers | Example hook (RU) |
|---|---|---|---|---|---|
| E01 | Insider tip | What a pro tells a friend | INSIDER, PERSON | SH3, SV1 | «Что я говорю друзьям, когда они выбирают [X]» |
| E02 | Mistakes | What not to do, shown with real examples | VOICE complaints, REALITY | SV1, SH2 | «3 ошибки при покупке [X]» |
| E03 | Myth check | A popular belief tested on camera | MISBELIEF, PROOF | S3, W1, C1 | «Говорят, что [миф]. Проверяем» |
| E04 | Live test or proof | Measure, stress or demonstrate | PROOF | W4, S3 | «Проверим на камеру» |
| E05 | Blind comparison or guess | Same task, two products from *this* store | PRICE, REALITY | C1, C4, W3 | «Какая дороже? Ответ в конце» |
| E06 | Budget ladder | What X buys at 3 real price points | PRICE | SV2, S5 | «Что можно купить за 30, 60 и 120 тысяч» |
| E07 | Process or satisfying | Make, repair, pack, set up, clean | REALITY | W2, S1, W6 | Sound and process, no words |
| E08 | Transformation | A real before and after | PROOF | W3 | «Было / стало» |
| E09 | Behind the scenes | What customers never see | REALITY | SH3, W7 | «Как приходит товар» |
| E10 | Character or day in the life | A recurring person and their skill | PERSON | W7, FOLLOW | «День мастера в первый снег» |
| E11 | Customer moment | A real reaction or first time (with consent) | MOMENT, PERSON | SH1, S4 | «Первый раз за рулём на новых шинах» |
| E12 | FAQ or reply to a comment | A real question answered | VOICE questions | ACT, C2 | «Ответ на комментарий: …» |
| E13 | Review reaction | Green screen over a real review, honest answer | VOICE, PROOF | S3, trust | «Нам написали, что мы развели клиента. Разбираем» |
| E14 | POV or relatable skit (labelled) | A true-to-life situation, exaggerated | RITUAL_PAIN | SH1, SH5 | «POV: колёса на балконе, сентябрь» |
| E15 | In-store extremes | The most expensive, oldest or oddest thing *here* | FACT, REALITY | S1, S5 | «Самая дорогая вещь в нашем магазине» (factual within the store) |
| E16 | Honest economics | Why something costs what it costs (owner-approved data only) | FACT | SH3, C5 | «Почему балансировка стоит [цена]» |
| E17 | Moment-jacking | Weather, holiday, city event | MOMENT | S6, SH4 | «Первый снег: два сценария» |
| E18 | Micro-lesson | One skill in 20 seconds | INSIDER | SV3 | «Как проверить [X] за 20 секунд» |
| E19 | Challenge or attempt | A staff attempt with real stakes | PERSON, REALITY | W4, H08 | «Успеет ли мастер за 60 секунд?» |
| E20 | Trend remix | A trending template carrying business cargo | TREND + any insight | Varies | Depends on the template |
| E21 | Stitch or duet correction | Respectful expert reaction to a viral category video | INSIDER | SH3, C3 | «Видео набрало миллион, но есть нюанс» |
| E22 | Owner story | Why, failures, real numbers | IN-19 | W7, trust | «Я открыл магазин после того, как…» |
| E23 | Honest product verdict | Who it is *for* and who it is *not* for | FACT, PROOF | ACT, SV2 | «Кому подойдёт, а кому нет» |
| E24 | Team and hiring | The real job, real people, real conditions | PERSON, FACT | SH2 | «Работа у нас: что правда, а что нет» |

### D5. Generation procedure (target 40–80 raw ideas per client per week)

1. **Angle questions.** For each top insight, answer the 12 questions below. Each answer is a candidate seed.
   1. Who is the hero?
   2. What is the enemy? It must be a mistake, a myth, a moment or a pain, never a competitor.
   3. What would a 10-year insider show a friend?
   4. What is the most extreme *true* instance?
   5. What does the customer never see?
   6. What would the customer say to a friend afterwards?
   7. What happens in the first 5 minutes after buying?
   8. What is the cheapest way and the most expensive way?
   9. What is the before and after?
   10. What is funny about this to insiders?
   11. What question did we hear most this week?
   12. What can we *measure* on camera?
2. **Cross insights × engines.** Keep a cell only if it has a true, showable instance this week. Expect 30–50% of cells to be empty; that is correct.
3. **Specify each candidate:**
   - container: C-HANDS, C-POV, C-TALK, C-VO, C-GREEN, C-REPLY, C-SPLIT, C-TIMELAPSE, C-ASMR, C-TEXT, C-SKIT (labelled) or C-STITCH;
   - production mode (D6);
   - one primary driver;
   - funnel role: reach, trust, consideration or conversion;
   - CTA type: none, code, follow or comment.
4. **Mutate** the top candidates with 2–3 operators each. Variants must differ in *mechanism*, not wording.

   | ID | Operator | Example |
   |---|---|---|
   | M01 | Swap the person | Owner ↔ worker ↔ customer ↔ hands only ↔ the product's "POV" |
   | M02 | Change the scale | One item → the whole shelf; one question → every question this week |
   | M03 | Raise the stakes | A time limit, a budget limit, «дал бы своему ребёнку?» |
   | M04 | Invert | How to choose → how *not* to choose |
   | M05 | Contrast pair | Cheap/expensive, beginner/pro, myth/fact, expectation/reality |
   | M06 | Serialise | Episode N, with a fixed opening line |
   | M07 | Localise | City, weather, neighbourhood, a Kazakh word, a local holiday |
   | M08 | Time-shift | Day one vs one year later |
   | M09 | Constrain the form | No words; one shot; 7 seconds; sound only |
   | M10 | Combine engines | Myth check + reply to comment; ASMR + price reveal |
   | M11 | Change the viewer | For the buyer → for the buyer's parent, spouse or child |
   | M12 | Remix a winner | Same structure with a new product or insight; "part 2" from the top comment |

5. **Write three hooks per idea**, each from a different hook type (D3). Each is a full stack: visual, text and spoken.
6. **Add a trend overlay** where one fits (D8).
7. **Deduplicate and gate.** Merge ideas whose semantic similarity exceeds 0.85, keeping the stronger one. Then apply the E1 gates.
8. **Write each survivor** as an Idea object (G6), with beats and a shot list.

**Series design.** A series is a named, recurring container:
- a fixed opening line (a catchphrase hook);
- one variable per episode (the product, the question, the customer);
- an episode bank of at least 8;
- a consistent payoff.

A series cuts ideation cost, builds follow intent, and works as a clean experiment arm. Every campaign has one hero series (F2).

### D6. Producible with one weak phone, 20 minutes and AI

**Production modes**

| Mode | What | Worker min/idea | Consent risk | Notes |
|---|---|---|---|---|
| PM-W | Hands and objects, no face, no speech | 2–3 | Low | Default |
| PM-V | Voice memo plus B-roll | 3–4 | Low | The phone is held at the mouth like a phone call, in a quiet corner. B-roll is filmed silent and the voice laid over it. |
| PM-T | Talking head | 4–6 | Medium | Only in a quiet spot, phone within arm's length. Otherwise use PM-V. |
| PM-R | Re-cut library footage with new text and voice | 0 | none | Reply videos, re-rolls |
| PM-S | Green screen or screen capture (review, comment, Kaspi page) plus voice | 0–2 | Low | Anonymise the reviewer |
| PM-A | AI-assisted illustration for abstract concepts | 0 | none | Never the product, store or people |
| PM-U | Customer content with consent | 0 | High until consent | Consent logged |

**Shot rules** (for the worker's shoot card):
- **Audio:** speech only with the phone at most 30 cm from the mouth, otherwise as a separate voice memo. Product sounds from 30–50 cm. Turn off store music while recording.
- **Light:** face the window or door. Never shoot against the light.
- **Image:** wipe the lens first (the most common failure). Shoot vertically, 1080p. No zoom; walk closer instead. Brace the phone against your chest or a shelf. Use slow moves only.
- **Shots:** 3–15 s each, 2 takes. Start recording 1 s before the action and stop 1 s after.
- **Acting:** none. Natural actions only. Never ask a worker to dance, play a role or humiliate themselves.
- **Fallbacks:** every shot has one; if a shot isn't possible, the AI edit uses library footage.
- **Library:** every session ends with 60 s of library B-roll (hands, shelves, process, entrance) for reply videos and re-rolls.

**20-minute budget:** about 2 minutes of setup (lens, quiet spot), 4–5 ideas at roughly 3 minutes each grouped by location, 1–2 minutes of library B-roll, and 1 minute for the voice note. Weekly posts beyond 4–5 come from zero-worker-minute modes (PM-R, PM-S), series episodes shot in batch, and moment captures.

**AI does:** cuts, punch-ins, pacing, burned-in captions (RU, plus KZ variants), voice denoise and enhancement, stabilisation, colour, upscaling, reframing, blurring of faces, plates, screens and receipts, hook text, covers, licensed music selection, neutral TTS narration where no human voice is available, illustrative animation for abstract concepts, drafts of comment replies and chat quick replies.

**AI never does:** product footage presented as real; a generated store, staff, customers, reviews or UGC; voice clones or avatars of real people without written consent; altering how a product looks or what condition it is in; generated before/after; price-slide videos as content.

### D7. Producibility checklist (each item is pass or fail)

- Everything in the shots exists in the store *this week*.
- Every shot can be filmed from 1 m or closer.
- No shot is longer than 15 s.
- No acting is required.
- The audio plan works: no speech, close-mic speech, or a voice memo.
- The worker minutes fit the weekly budget.
- Consent is on file for everyone identifiable.
- Every shot has a fallback.

### D8. Trends, sounds, remixes and comments

**Trend fit test** (all five must pass):
1. **Transferable mechanic.** The structure of the trend can carry a true insight about this business.
2. **Cargo rule.** Remove the trend, and the video still says something true and specific about the business.
3. **Speed.** It can be produced within 24–48 h using library footage or at most 5 worker minutes.
4. **Freshness.** Usage is still growing. Default: first seen 7 days ago or less; drop it after about 14 days unless it is an evergreen template.
5. **Safety and fit.** No mockery of religion, ethnicity or tragedy; no politics; the audience overlaps with buyers; the sound is licensed.

**Quota:** at most 25% of weekly slots depend on trends. Evergreen templates (day in the life, POV, ASMR, "what X buys", reply to comment) are more reliable than fleeting sounds.

**Moment kits:** for predictable moments (first snow, 1 September, a holiday), pre-shoot the footage and pre-write the script. Publish within hours of the trigger.

**Sounds:**
- Business accounts are restricted to commercial or licensed music libraries (TikTok's Commercial Music Library; check Instagram's current rules for the region). Never use unlicensed music.
- Original audio (a real voice, a real product sound) is the safest choice and often the most distinctive. It also makes the sound reusable by others.
- Assume a share of viewers watch muted, so the meaning must survive without sound: captions plus visual proof.

**Remixes:**
- Stitch or duet viral category videos with an expert correction (E21, respectful, never mocking a person).
- Remix our own winners (M12) within 72 hours of a spike.
- Transplant patterns that won in other clients (F11).

**Comment-to-content flywheel:**
- Triage comments daily.
- Every real question becomes a reply-video candidate (E12, PM-R/PM-S, zero worker minutes).
- Pin the comment that carries the CTA, or the answer to a guess.
- Reply to early comments fast and in the business's voice. The agent drafts; sensitive replies go to the owner.
- Never delete criticism unless it is abusive or contains personal data.

**Language:** Russian is the default. Kazakh captions or Kazakh-language variants run as an arm where the audience warrants it. Natural local code-switching is allowed only when a real staff member speaks that way.

### D9. Anti-patterns

| Anti-pattern | Why it fails | Do instead |
|---|---|---|
| Ad-shaped videos: logo first, «Мы рады предложить», beauty shots plus music plus a price | Scrolled past as an ad; fails the logo test | Lead with the viewer's question or a proof moment. Put the business in the payoff and CTA. |
| Motion-graphic price slides or catalogue carousels | Judged useless; nothing to watch, feel or share | The budget-ladder engine (E06): real hands, real sound, real price with a date |
| Engagement bait («поставь лайк», «напиши +», "tag 3 friends to win") | Cheap; signals low quality; attracts the wrong audience | Genuine C1–C5 comment triggers |
| Fake urgency or scarcity («только сегодня», countdowns, «осталось 2») | Breaks L3 and burns trust | Real deadlines only, stated plainly |
| Invented or "improved" claims, reviews or customers | Breaks L3; legal risk | PROOF atoms, consented voices |
| Irrelevant trend chasing (staff dancing to nothing) | Fails the cargo rule; attracts non-buyers | Trend fit test (D8) |
| Greeting or slow intro («Привет всем, сегодня…») | The swipe happens at 1 s | A hook stack in frame 1 |
| Talking to everyone | Stops nobody | One specific viewer (S2) |
| Hook–payoff mismatch, clickbait | Retention collapse and distrust | Every promise is kept by about 90% of runtime |
| Walls of text, tiny text, text under the UI | Unreadable | At most 7 words per screen, in safe zones |
| Competitor bashing | Legal and brand risk | Compare products within the same store; attack myths and mistakes |
| Studio over-polish | Looks like an ad; often costs more | A native phone look with clean audio |
| Re-uploading an identical file | Can be flagged as unoriginal; teaches nothing | Re-cut with a new hook (E6 re-roll rule) |
| Filming customers or children without consent; visible plates and receipts | Privacy and legal risk | Consent log plus AI blur |

---

## E. Idea selection

### E1. Gates (any failure means fix or drop)

- **G1 Truth.** Every claim traces to an atom or is labelled opinion or skit (C6).
- **G2 Consent.** Everyone identifiable has consented. Reviews are anonymised or used with permission.
- **G3 Producible.** Passes the D7 checklist; worker minutes fit.
- **G4 Rights and law.** Licensed or original audio. No disparaging competitors. Credit and installment terms copied exactly from the source. For paid boosts, Kazakhstan's advertising rules (including language requirements) are confirmed by the owner, and the agent supplies RU and KZ text.
- **G5 Brand floor.** Nothing the owner marked off-limits. No humiliation. Culturally safe.
- **G6 Not an ad.** Passes the logo test.

### E2. Prior rubric (0–2 per dimension, total S from 0 to 20). This is a prior, not a prediction.

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| P1 Insight strength | Generic | One source | Several independent sources or high intensity |
| P2 First-frame stop | Static, logo or greeting | Decent | Concrete anomaly or action in progress, with an aligned text hook |
| P3 Promise and payoff | No clear promise | Promise kept weakly or late | Clear promise kept by about 90% of runtime |
| P4 Share reason | No believable send line | Generic | Specific recipient and reason |
| P5 Save or comment reason | None | One | Dense reference or a genuine split |
| P6 Objective link | Unrelated | Indirect (trust or awareness) | Direct path to the target action; the CTA is natural |
| P7 Distinctiveness (swap test) | Any business could post it | Category-specific | Only this business can post it: its people, place or proof |
| P8 Native feel | Ad-like or slides | Mixed | Looks like a person filmed it for people |
| P9 Cheapness and speed | More than 8 worker minutes, or credit-heavy | 4–8 | 4 or fewer, or zero worker minutes |
| P10 Series potential | One-off | Repeatable 3 times | Repeatable 10 or more times with new inputs |

Text judges have no measured authority for short-form retail (ρ = 0.07, CI includes 0). So the rubric does only three jobs: drop clear losers (S < 8, unless the idea is the designated wild card), pick which idea fills a slot inside an arm, and add a small nudge to the arm prior.

### E3. From score to prior

- Idea nudge = 0.02 × (S − 10) in log-relative units. That is ±0.2 at most, roughly ±20% of expected views: a nudge, not a verdict.
- **Arm prior when pooled data exists:** pooled posterior mean (global → vertical) × 0.5, with prior sd = max(pooled sd, 0.5).
- **Arm prior when there is no pooled data:** the mean nudge of the arm's scheduled ideas, with prior sd 0.7.
- Log every idea's S and per-dimension scores. They are calibrated against outcomes in E7.

### E4. Arms (a taxonomy shared across all clients, which is what makes pooling possible)

Arms are coarse families, so that every client contributes data to the same buckets:

| Arm ID | Family | Engines |
|---|---|---|
| A-PROOF | Proof, test, comparison | E03 E04 E05 E08 |
| A-UTIL | Utility | E01 E02 E06 E18 |
| A-PROC | Process and behind the scenes | E07 E09 |
| A-PEOPLE | Character and story | E10 E11 E22 E24 |
| A-REACT | Reply, review, stitch | E12 E13 E21 |
| A-HUMOR | POV and skit | E14 E19 |
| A-MOMENT | Moment and trend | E17 E20 |
| A-CONVERT | Verdict, spotlight, offer | E15 E16 E23 |

Hook type (H01–H12), container, production mode, length bucket, person on camera, language and trend flag are *tags*, not arms. Their effects are estimated across clients in the pooled model (F11). One client never has enough data to estimate them alone.

**Allocation:**
- Thompson sampling over 4–6 active arms per client per platform, with an exploration floor of 15%.
- One wild-card slot per week.
- Trend-dependent posts capped at 25%.
- The hero series counts as its own sub-arm under its family.

### E5. Diversity rules (weekly batch of N = 6–9)

- At least 4 distinct engines. No engine more than twice, except the hero series, which may take up to 3 slots.
- At least 3 hook types. No hook type more than 3 times.
- At least 3 distinct insights. No insight above 40% of the batch.
- At least 2 production modes, including at least 1 zero-worker-minute post.
- Primary drivers include at least 1 SHARE, 1 SAVE and 1 COMMENT idea.
- If the objective is sales, bookings or hiring: at least 1 conversion-role post per 3 posts.
- Length mix: at least 1 post of 15 s or less, and at least 1 post of 30 s or more.
- At least 1 wild card: passes the gates, rubric below median, high novelty. This keeps the weak rubric from narrowing the taste.
- If a consenting recurring person exists, at least 1 post features them.

### E6. Volumes and variants

| Stage | Per client per week |
|---|---|
| Raw ideas | 40–80 |
| After gates | 20–30 |
| Shortlist, fully specified | 12–15 |
| Produced bodies | 6–9, plus 2 pre-cut backups |
| Hook variants per body | 3 (A/B/C) |
| Posts per platform | 6–9 |
| Active arms per platform | 4–6 |

**Testing mechanics** (cheapest first):
1. **Arm-level organic Thompson,** per platform, with the platform's own baseline.
2. **Hook randomisation across platforms.** For each body, randomly assign hook variants A/B/C to TikTok, Reels and Shorts, and log the seed. Hook-type effects are then estimated across many posts and clients with platform fixed effects. Copies of the same body are correlated, so treat platforms as blocks, not as three free observations.
3. **Trial Reels,** where available: test 2 hooks on non-followers and publish the winner to followers.
4. **Re-roll rule.** An idea with P1 ≥ 1.5 and P7 = 2 that lands below baseline (y < 0) gets one re-cut after 7 or more days, with a different hook type and different first 3 seconds. Never re-upload an identical file.
5. **Paid micro-tests,** only with an approved budget: 2–4 hook variants of the same body, the same geo audience, an equal small budget, 48 h, compared on 3-second hold rate and cost per inquiry. Impression-level sample sizes resolve hook differences that organic posting cannot. But paid audiences are not organic audiences, so use these results to choose hooks and posts to scale, and never feed them into the organic arm posteriors.

**Power note** for client reports: about 30 posts per arm are needed for 80% power on a 2× effect. One client at 6–9 posts a week on one platform needs about 7–10 weeks per pairwise decision. Ten clients on the shared taxonomy need about a week. Never declare a single client's winner early (F10).

### E7. Rubric calibration (monthly, across all clients)

- For each dimension P1–P10, compute Spearman against y with a CI. This needs 200 or more posts.
- Raise a dimension's weight in the nudge only if its CI excludes 0. Dimensions near ρ ≈ 0 stay in use as gates or diversity tags but contribute nothing to the nudge.
- Publish a calibration record per scope (vertical, platform). Judge authority is read from these records and is never assumed.

---

## F. Campaign design

### F1. Skeleton (every campaign has every part)

1. **Objective block,** copied from the locked brief: primary metric, target, deadline.
2. **Big idea:** one sentence, rooted in the top-ranked insight, true and distinctive. It must be able to generate 10 or more episodes.
3. **Hero series:** named, recurring, 2–3 times a week.
4. **Supporting tracks:** Proof, Utility, People, Reactive, Conversion.
5. **Conversion path:** video → pinned comment, caption or bio with a code and a wa.me link → WhatsApp quick replies → sale.
6. **Offer,** only if needed and approved (F4).
7. **Channel roles,** including WhatsApp, Kaspi, 2GIS and an optional paid boost (F5).
8. **Calendar** (F6).
9. **Worker asks** (F7).
10. **AI tasks** (D6).
11. **Measurement and attribution** (F9).
12. **Decision rules** (F10).
13. **Learning loop** (F11).
14. **Owner reporting** (F12).

### F2. Big idea and hero series

- **Big idea, internal form:** "[Business] is where [the truth that resolves the top tension] — and we prove it on camera."
- **Public series name:** Russian, at most 5 words, and phrased as the viewer's own question where possible («Менять или ещё походят?», «Звучит ли за 30 000?», «Что мастер видит, а вы нет»).
- **Series spec:**
  - a fixed first line;
  - one episode variable;
  - a fixed structure (hook → test or answer → verdict → code);
  - an episode bank of at least 8;
  - each episode filmable in at most 4 worker minutes.
- **Test:** can a stranger predict roughly what episode 7 will be about, and still want to watch it? If yes, the series works.

### F3. Track mix by objective (default share of weekly slots; Thompson shifts it from week 2)

| Track | SALES / CLEARANCE | BOOKINGS / FOOTFALL | AWARENESS | REPUTATION | HIRING |
|---|---|---|---|---|---|
| Hero series | 30% | 30% | 35% | 30% | 30% |
| Proof (A-PROOF) | 15% | 15% | 10% | 30% | 0–10% |
| Utility (A-UTIL) | 15% | 15% | 20% | 10% | 0% |
| People (A-PEOPLE) | 10% | 10% | 15% | 15% | 40% |
| Reactive (A-REACT / A-MOMENT) | 10% | 15% | 20% | 15% | 20% |
| Conversion (A-CONVERT) | 20% | 15% | 0–5% | 0% | 10% (job verdict) |

### F4. Offer rules

- Offers are owner decisions. The agent proposes one concrete option with a reason and a cost estimate, and the owner approves it in one line (IN-17). The agent never invents or implies an offer.
- Prefer offers that cost little and are true: a free check, priority booking for people who write with a code, a bundle the business already does.
- Only a real deadline may be stated. If the offer has no end date, say so: «пока действует».
- Anything already published by the business (for example, a sale page) can be shown with its real old and new prices and its date. Do not add reasons («закрываемся», «последняя партия») that are not confirmed.

### F5. Channel roles

| Channel | Role | Main content | Metric |
|---|---|---|---|
| TikTok | Reach beyond followers; trend vehicle; reply-to-comment videos | All engines | y, 3-second hold, sends, follows, codes |
| Instagram Reels | Reach plus local community; sends; Trial Reels for tests | The same bodies with IG-native text | Sends per reach, saves, codes |
| Instagram Stories | Warm-audience conversion; polls as inputs; link sticker to wa.me with a code | Behind the scenes, reminders, the offer | Link taps, replies |
| YouTube Shorts | Search and long tail; exact product and model names in titles and captions (product-name search intent won on Muzzone's long-form channel; for Shorts it is still a hypothesis) | Utility, verdicts | 30-day views, codes |
| WhatsApp Business | Conversion and sales: quick replies (agent-written, RU), catalogue, broadcast to opted-in contacts only | Chat scripts | Code inquiries, time to first reply, close rate |
| Kaspi | Transaction and reviews | Listing improvements (supplied by the agent, done by the owner) | SKU uplift |
| 2GIS / Google Maps | Local search and proof | Photos, honest review replies | Profile actions, new reviews |
| Paid boost (optional, approved) | Amplify proven posts; hook micro-tests | Only posts in the top 20% by y with a working CTA | Cost per inquiry, under a ceiling the owner sets |

**Quick-reply template** (staff, RU):
> «Здравствуйте! Спасибо, что написали по видео [код]. Подскажите [1 уточняющий вопрос: размер / модель / удобный день] — сразу проверим наличие и время.»

The guardrail is a fast first reply. If the median first reply exceeds 2 hours, tell the owner: views are wasted if nobody answers.

**Non-video levers** (propose them when the deadline is short; each costs owner minutes and needs approval):
- a WhatsApp broadcast to opted-in past buyers;
- Kaspi listing photos and video;
- updating the 2GIS card;
- a printed QR code at the till leading to the series;
- staff asking happy customers for a review.

### F6. Calendar

**Default 4-week sprint:**

| Week | Mode | Content | Other |
|---|---|---|---|
| 0 (days 1–3) | Setup | None published | Intake, inputs, evidence, insights, ideas, test plan, code family, quick replies, store scan, shoot card #1, baseline capture |
| 1 | Explore | 6–9 posts; at least 5 arms; hero series episodes 1–3 | Daily comment triage; 48-hour reads |
| 2 | Explore and learn | Reply videos from week-1 comments; re-rolls; moment kits ready | Thompson starts reallocating |
| 3 | Focus | Slots shift to the leading arms (exploration ≥ 15%); conversion push | Offer if approved; Stories sequence; broadcast if approved; first boost if approved |
| 4 | Scale and harvest | More episodes of the winning series; conversion | Report; refresh insights; plan the next sprint |

**Deadline-driven reverse plan:**
- D−28 to D−15: trust and consideration (hero series, proof, utility).
- D−14 to D−8: conversion content rises to 30–40%.
- D−7 to D: conversion, reminders, broadcast, plus the real deadline if the offer genuinely has one.
- If the deadline is less than 14 days away, push the non-video levers first and treat video as the reach layer.

**Weekly rhythm:**
- Monday 10:00: the agent sends the shoot card.
- Monday–Tuesday: the worker shoots for at most 15 minutes and sends the clips.
- Tuesday: AI edit, checks, approval request.
- Tuesday–Sunday: publish slots. Use the account's own best times once data exists. Until then default to 12:00–14:00 and 18:00–21:00 local time, labelled as an assumption.
- Daily: comment triage.
- Friday: readout to the owner (F12).

### F7. Worker asks (at most 20 minutes a week, all included)

- **Shoot card** (at most 15 minutes): RU, ordered by location, each shot with what to film, distance, seconds, takes, what to say (if anything), and a fallback. Each shot stands alone, so a skipped shot costs one idea, not the batch.
- **Moment triggers** (at most 2 minutes, opportunistic), pre-agreed:
  - «Если клиент удивился или засмеялся — спросите разрешения и снимите 10 секунд»;
  - «Пришла поставка — 10 секунд распаковки»;
  - «Первый снег / очередь — 10 секунд двора, без лиц и номеров».
- **Voice note** (1 minute): «Какие 3 вопроса задавали клиенты?»
- **Never ask workers to:** edit, post, write captions, dance, act, or film themselves if they have not consented.
- **Footage QA:** the agent checks every clip automatically (audio level and clipping, shake, framing, lens haze). If clips fail, send a 1-line fix in Russian next week («Протрите камеру», «Ближе к инструменту, 40 см»). Log repeated failures, and rewrite the shot template that keeps failing.

### F8. AI tasks per campaign

- Scripts and hooks.
- Edit recipes per format.
- Captions in RU and KZ.
- Denoise, stabilise, colour.
- Blurring of faces, plates and screens.
- Covers.
- Licensed music.
- Comment and chat reply drafts.
- Reports.
- Illustrative animation only for abstract concepts.

The forbidden list in D6 applies.

### F9. Measurement and attribution

**Metric hierarchy:**
1. **Business (primary):** units, bookings, applications, sell-through. Sources: owner, Kaspi or 1C export, chat tally.
2. **Attributable demand:** code inquiries in total, per post, and per 1k views; time to first reply; close rate.
3. **Creative (steers allocation):** y = ln(views at 48 h ÷ platform baseline). Secondary: 3-second hold, completion, average watch %, sends per reach, saves per reach, comments per reach, follows per reach, in-geo share of viewers.
4. **Guardrails:** truth incidents (0), consent incidents (0), negative comment share, WhatsApp blocks, worker minutes ≤ 20, owner minutes ≤ the agreed amount.

**Attribution:**
- **WhatsApp codes.** Each post gets a unique code built only from characters that look the same in Latin and Cyrillic (A B C E H K M O P T X) and digits 2–9, so it survives a Russian keyboard. The code appears in the spoken or text CTA, the pinned comment and the caption. Use prefilled wa.me links wherever links are clickable (bio, Stories sticker, YouTube description, ads). Count codes from a weekly chat export or the API, normalising look-alike characters.
- **Uncoded social.** «Видел у вас в TikTok» without a code goes into a separate bucket.
- **Kaspi.** There is no per-video code. Compare weekly SKU sales of featured items against their own prior 4 weeks and against similar non-featured SKUs. Directional only; always labelled as such.
- **Footfall.** Use a «откуда узнали?» tally only when footfall is the objective, and count its cost against the worker budget.
- **Baselines.** The platform baseline is the median of the last 14 days of the account's own posts (at least 5 posts). Before that, use the pooled vertical prior.
- **Read times:** 48 h (creative and allocation) and 7 days (business and long tail).

### F10. Decision rules

- **DR-1 Read.** Read every post at 48 h and at 7 days. Write y and the secondary metrics into the TestPlan.
- **DR-2 Spike protocol.** If y ≥ ln 3 (3× baseline) or code inquiries ≥ 3× the client's per-post median:
  - within 2 hours: pin the CTA comment, reply to the top comments, check that WhatsApp can respond, alert the owner;
  - within 72 hours: publish 2 follow-ups (part 2, and replies to the top comments) using the same engine and hook type;
  - if approved and objective-relevant: boost;
  - log the pattern to the library.
- **DR-3 Allocation.** Rerun Thompson weekly, keeping the exploration floor at 15%. New arms enter with priors from E3.
- **DR-4 Retire an arm** for a client when P(μ > 0) < 0.10 with n ≥ 12 on that platform. The arm stays in the global library.
- **DR-5 Winner.** Declare a winner only when P(best) ≥ 0.90 and every contender has n ≥ 10. Always report the interval. Otherwise report «пока неясно».
- **DR-6 Awareness-only arm.** An arm whose posterior mean is above 0 but with 0 code inquiries after 10 or more posts and 10k or more total views is an awareness arm. Keep it only if awareness is part of the objective; otherwise cap it at 15% of slots.
- **DR-7 Re-roll** (E6, rule 4). One re-roll per idea.
- **DR-8 Paid.** Boost only posts that are in the top 20% by y, have a CTA and are objective-relevant. Stop when cost per inquiry exceeds the owner's ceiling or after 72 hours, whichever comes first.
- **DR-9 Pivot.** If after 3 weeks no arm has P(μ > 0) ≥ 0.6 and inquiries are 0, the problem lies upstream, not in the ideas. Return to C, refresh inputs (especially IN-10 and IN-16), re-rank insights, and check the CTA path and reply speed.
- **DR-10 Flops.** Do not delete underperforming posts; they are data. Delete only for truth, consent or legal problems.

### F11. Learning loop

**Weekly, per client (Friday):**
1. Ingest the results.
2. Update the posteriors.
3. Apply the decision rules.
4. Update insight performance: the mean y and the inquiries of each insight's ideas.
5. Add new comments, chats and voice notes to the evidence base.
6. Generate next week's ideas, with winners' patterns mutated (M12).

**Weekly, across clients:**
- Refit the hierarchical model (global → vertical → client) on the shared tags: arm, engine, hook type, container, production mode, length bucket, person type, language, trend flag, CTA type, platform.
- The **pattern library** records each pattern's posterior, n, and number of clients and verticals.
- **Transplant candidates** are patterns with P(μ > 0) ≥ 0.8 across 3 or more clients in 2 or more verticals. They enter new clients' idea generation with their pooled prior.
- The **vertical insight library** stores anonymised tension *types* (for example, "fear of being upsold" in car services) to speed up C3 for new clients in the vertical.

**Monthly:** rubric calibration (E7) and shoot-template QA (F7).

**Privacy wall:** only tags, structures and anonymised tension types cross between clients. One client's customer quotes, prices or data never appear in another client's work.

### F12. Owner reporting (weekly, Russian, at most 5 lines, at most 1 decision request)

Template (fill only with measured values; never estimate inside a report):
> «Неделя [N]: [X] роликов, [V] просмотров ([g]% — [город]). В WhatsApp по кодам написали [I] человек, из них [S] купили / записались.
> Лучше всего заходит: [серия/подход] — в [k] раз выше обычного (пока [уверенно / рано судить]).
> Следующая неделя: [план одной строкой].
> Нужно от вас (1 мин): [один вопрос с вариантами]. Если не ответите до [срок] — [вариант по умолчанию].»

---

## G. Output contract

Every step emits exactly these objects. Field types: `str`, `int`, `float`, `date`, `datetime`, `enum`, `[list]`, `{object}`. IDs are stable and referenced across objects. RU marks audience-facing or worker-facing Russian text.

### G1. IntakeBrief
```yaml
IntakeBrief:
  id: str                          # BR-<client>-<yyyymmdd>-v<n>
  client_id: str
  version: int
  status: enum[draft, questions_sent, locked]
  request: {verbatim: str, from_role: str, received_at: datetime, channel: enum[whatsapp, call, email, meeting, other]}
  request_types: [enum]            # primary first; values from A2
  why_now: [{hypothesis: str, evidence_ids: [str], confidence: enum[low, med, high]}]
  business_objective: {statement: str, metric: str, baseline: float|null, target: float|null, deadline: date|null, source: enum[stated, inferred]}
  marketing_objective: {audience: str, geography: str, desired_action: str, funnel_focus: [enum[reach, trust, consideration, conversion, retention]]}
  success_metrics:
    primary: {name: str, definition: str, data_source: str, baseline: float|null, target: float|null}
    leading: [{name: str, definition: str}]
    guardrails: [{name: str, threshold: str}]
  feasibility: {required_views: int|null, achievable_views: int|null, inputs_used: {str: float}, label: enum[likely, stretch, unlikely, n/a], options_if_gap: [str]}
  constraints:
    paid_budget_kzt_week: int                 # 0 unless approved
    owner_minutes_week: int
    worker_minutes_week: int                  # ≤ 20
    on_camera: [{person_role: str, allowed: enum[face, hands, voice, none], consent: enum[yes, pending, no]}]
    may_state: {prices: enum[public_only, owner_list, none], offers: [str], off_limits: [str]}
    approval_mode: enum[each_post, preapproved_classes, paused]
    platforms: [{name: str, account: enum[owned, needs_creation, needs_access]}]
    capacity_notes: str
    legal_flags: [str]
  assumptions: [{id: str, statement: str, basis: str, confidence: enum[low, med, high], impact_if_wrong: str, revisit_on: date}]
  questions: [{id: str, text_ru: str, options_ru: [str], default: str, voi_reason: str, answer_by: datetime, answer: str|null}]  # max 3
  conflicts: [{description: str, resolution: str, needs_owner: bool}]
  out_of_scope: [{item: str, routed_to: str}]
```

### G2. InputChecklist
```yaml
InputChecklist:
  client_id: str
  brief_id: str
  items: [{
    input_id: enum[IN-01..IN-22],
    status: enum[done, pending, blocked, missing, not_needed],
    method: enum[automated, owner, worker],
    minutes_cost: float,
    requested_at: datetime|null, received_at: datetime|null,
    request_text_ru: str|null,               # exact ask sent, if human
    fallback_applied: str|null,              # from B2 "if missing"
    block_reason: str|null                   # e.g. "site returns 403; not bypassed"
  }]
  minimum_viable_met: bool
  owner_minutes_used_total: float
```

### G3. EvidenceBase
```yaml
EvidenceBase:
  client_id: str
  version: int
  atoms: [{
    id: str,                                  # EV-<type>-<n>
    type: enum[FACT, PRICE, VOICE, BEHAVIOR, MOMENT, REALITY, PROOF, PERSON, CONSTRAINT, PERFORMANCE, PEER_PATTERN, TREND],
    text: str,                                # verbatim for VOICE
    stance: enum[question, objection, fear, desire, praise, complaint, neutral]|null,
    source: {kind: str, ref: str, fetched_at: datetime, hash: str},
    scope: enum[BUSINESS, CATEGORY],
    count: int, intensity: int,               # 0–3
    verification: enum[primary, two_sources, owner_confirmed, unverified, conflict],
    public_ok: bool,                          # may appear in audience-facing copy
    expires_at: date|null                     # prices/stock
  }]
  themes: [{id: str, label_ru: str, atom_ids: [str], count: int, intensity: float, journey_stage: enum[trigger, search, doubt, choice, purchase, use, tell]}]
  reality_inventory: [{id: str, what: str, location: str, filmable_this_week: bool, sound: bool}]
  proof_inventory: [{id: str, what: str, how_shown: str, atom_ids: [str]}]
  people: [{id: str, role: str, allowed: enum[face, hands, voice, none], traits: str}]
  conflicts: [{atom_ids: [str], note: str, resolution: str|null}]
  gaps: [{question: str, why_it_matters: str, route: enum[owner_question, research_post, wait]}]
```

### G4. InsightList
```yaml
InsightList:
  client_id: str
  version: int
  insights: [{
    id: str,                                  # INS-<n>
    type: enum[TENSION, MISBELIEF, MOMENT, INSIDER, IDENTITY, RITUAL_PAIN, PROOF_GAP, PERSONALITY],
    statement: str,
    customer_words_ru: [str],                 # verbatim, from atoms
    atom_ids: [str],
    show_how: str,                            # "so we can show…"
    proof_ids: [str],
    objective_link: str,
    quality_test: {specific: bool, evidenced: bool, insider_obvious: bool, showable: bool, relevant: bool, true: bool},
    scores: {evidence: int, intensity: int, objective_fit: int, showability: int, distinctiveness: int, breadth: int, total: int},
    rank: int,
    wild: bool,
    performance: {ideas_posted: int, mean_y: float|null, inquiries: int}   # filled by learning loop
  }]
```

### G5. ShootCard (worker-facing, RU)
```yaml
ShootCard:
  id: str
  client_id: str
  week: str
  for_role: str
  total_minutes_est: int                      # ≤ 15
  due: datetime
  delivery_ru: str                            # how to send clips
  prep_ru: [str]                              # lens, quiet spot, vertical, no zoom
  shots: [{
    shot_id: str, idea_id: str, location: str,
    what_ru: str, distance_cm: int, seconds: int, takes: int,
    say_ru: str|null, audio: enum[voice_close, product_sound, none, voice_memo_separate],
    privacy_ru: str|null,                     # e.g. "без лиц клиентов"
    fallback_ru: str
  }]
  library_broll_ru: str                       # 60 s generic
  moment_triggers_ru: [str]
  voice_note_ru: str
```

### G6. IdeaList
```yaml
IdeaList:
  client_id: str
  week: str
  ideas: [{
    id: str,                                  # ID-<week>-<n>
    title_internal: str,
    insight_ids: [str],
    engine: enum[E01..E24], arm: enum[A-PROOF, A-UTIL, A-PROC, A-PEOPLE, A-REACT, A-HUMOR, A-MOMENT, A-CONVERT],
    series_id: str|null, episode: int|null,
    primary_driver: enum[S1..S7, W1..W7, SH1..SH5, SV1..SV3, C1..C5, FOLLOW, ACT], secondary_driver: str|null,
    funnel_role: enum[reach, trust, consideration, conversion],
    container: enum[C-HANDS, C-POV, C-TALK, C-VO, C-GREEN, C-REPLY, C-SPLIT, C-TIMELAPSE, C-ASMR, C-TEXT, C-SKIT, C-STITCH],
    production_mode: enum[PM-W, PM-V, PM-T, PM-R, PM-S, PM-A, PM-U],
    worker_minutes: float, ai_credits_est: float,
    trend: {used: bool, trend_atom_id: str|null, fit_test_passed: bool|null},
    mutations_applied: [enum[M01..M12]],
    hooks: [{variant: enum[A, B, C], hook_type: enum[H01..H12], visual: str, text_ru: str, spoken_ru: str|null}],  # exactly 3
    beats: [{t_from_s: float, t_to_s: float, visual: str, text_ru: str|null, audio: str}],
    payoff: str,
    target_length_s: int,
    cta: {type: enum[none, code, follow, comment], text_ru: str|null, placement: [enum[spoken, onscreen, caption, pinned_comment]]},
    claims: [{text_ru: str, atom_ids: [str], class: enum[fact, price, stock, opinion, category, voice, skit]}],
    label_ru: str|null,                       # «постановка», AI label
    tests: {send_line_ru: str|null, save_reason: str|null, first_comments_ru: [str], logo_test: bool, swap_test: enum[any, category, only_us]},
    gates: {G1: bool, G2: bool, G3: bool, G4: bool, G5: bool, G6: bool, notes: str},
    rubric: {P1: int, P2: int, P3: int, P4: int, P5: int, P6: int, P7: int, P8: int, P9: int, P10: int, S: int},
    prior_nudge: float,                       # 0.02*(S-10)
    wild_card: bool,
    status: enum[candidate, shortlisted, selected, backup, rejected], reject_reason: str|null
  }]
  diversity_check: {engines: int, hook_types: int, insights: int, modes: int, zero_worker_posts: int, drivers_covered: [str], trend_share: float, passed: bool}
```

### G7. PostPackage (one per platform post)
```yaml
PostPackage:
  post_id: str
  idea_id: str
  platform: enum[tiktok, reels, shorts, stories]
  hook_variant: enum[A, B, C]
  randomization_seed: int
  code: str                                   # A B C E H K M O P T X + 2–9
  wa_link: str|null
  caption_ru: str                             # first line extends hook + search keywords
  pinned_comment_ru: str|null
  cover_text_ru: str
  audio: {source: enum[original, commercial_library], id: str|null}
  checks: {facts_fresh: bool, banned_phrases: bool, links_match: bool, blur_done: bool, labels_applied: bool}
  approval: {required: bool, approved_by: str|null, at: datetime|null}
  scheduled_at: datetime
```

### G8. TestPlan
```yaml
TestPlan:
  id: str
  client_id: str
  campaign_id: str
  period: {from: date, to: date}
  platforms: [{name: str, baseline: {value: float, n_posts: int, window_days: int, source: enum[own, pooled_prior]}}]
  arms: [{arm_id: str, active: bool, prior_mean: float, prior_sd: float, prior_source: enum[global, vertical, client, rubric_only], n: int, post_mean: float|null, post_sd: float|null, p_best: float|null, p_above_zero: float|null}]
  allocation: {method: "thompson", explore_floor: 0.15, slots_per_week: int, wild_card_slots: 1, trend_cap: 0.25}
  hook_randomization: {enabled: bool, design: "hook→platform random per body"}
  paid_tests: [{id: str, variants: [str], budget_kzt: int, audience: str, metric: str, stop_rule: str, approved: bool}]
  outcomes:
    creative: "y = ln(views_48h / baseline)"
    secondary: [hold_3s, completion, avg_watch_pct, sends_per_reach, saves_per_reach, comments_per_reach, follows_per_reach, in_geo_share]
    business: [code_inquiries, inquiries_per_1k_views, sales_attributed, bookings, applications]
  read_times: ["48h", "7d"]
  decision_rules: [DR-1..DR-10]
  power_note: str
  results: [{post_id: str, arm_id: str, platform: str, hook_type: str, y: float|null, secondary: {str: float}, inquiries: int, read_at: datetime}]
```

### G9. Campaign
```yaml
Campaign:
  id: str
  client_id: str
  brief_id: str
  objective: {copied from IntakeBrief: business, marketing, success_metrics}
  big_idea: {internal: str, top_insight_id: str}
  hero_series: [{id: str, name_ru: str, opening_line_ru: str, structure: [str], episode_variable: str, episode_bank: [str], cadence_per_week: int, arm: str}]
  tracks: [{track: enum[hero, proof, utility, people, reactive, conversion], share: float, idea_ids: [str]}]
  conversion_path: {cta_template_ru: str, code_family: str, wa_number_atom_id: str, quick_replies_ru: [str], reply_time_guardrail_h: float}
  offer: {exists: bool, text_ru: str|null, terms_atom_ids: [str], start: date|null, end: date|null, approved_by: str|null}
  channel_roles: [{channel: str, role: str, metric: str}]
  non_video_levers: [{lever: str, owner_minutes: int, approved: bool}]
  paid: {budget_kzt_week: int, rules: str, approved: bool}
  calendar: [{date: date, slot: str, platform: str, idea_id: str, post_id: str|null, status: enum[planned, shot, edited, approved, published]}]
  worker_asks: {shoot_card_ids: [str], moment_triggers_ru: [str], minutes_week: int}
  ai_tasks: [str]
  measurement: {primary: str, attribution: [str], dashboards: [str]}
  decision_rules: [str]
  risks: [{risk: str, mitigation: str}]
  approvals_needed: [{item: str, from: str, by: datetime, default: str}]
```

### G10. WeeklyLearningRecord
```yaml
WeeklyLearningRecord:
  client_id: str
  week: str
  posts: int
  totals: {views: int, in_geo_share: float|null, inquiries: int, sales_or_bookings: int|null}
  arm_updates: [{arm_id: str, n: int, post_mean: float, ci90: [float, float], p_best: float, decision: enum[keep, increase, decrease, retire, undecided]}]
  spikes: [{post_id: str, y: float, follow_ups: [str]}]
  insight_updates: [{insight_id: str, mean_y: float, inquiries: int}]
  new_evidence_ids: [str]
  rule_triggers: [str]                        # DR ids fired
  library_contributions: [{pattern_tags: {str: str}, y: float}]
  owner_report_ru: str
  owner_minutes_used: float
  worker_minutes_used: float
  incidents: [{type: enum[truth, consent, legal, quality], post_id: str, fix: str}]
```

---

## H. Worked mini-example: a local tire service

**Everything about this business is a labelled assumption. It is a hypothetical client, not a real business.** Prices appear only as ledger references such as `{PRICE:EV-PRICE-1}`, to show how scripts stay truthful.

**Assumptions:**
- A1: tire-fitting service in Astana, 2 bays, 3 masters.
- A2: also sells winter tire sets and offers seasonal tire storage.
- A3: bookings through WhatsApp; the number is on the 2GIS card.
- A4: about 150 reviews on 2GIS, price list published on 2GIS.
- A5: Instagram with about 900 followers, no TikTok.
- A6: one master agrees to hands and voice, not face.
- A7: paid budget 0.

### H1. Intake

Verbatim (owner, WhatsApp): «Сделайте нам вирусное видео, чтобы про нас весь город узнал. Сезон начинается.»

- **Types:** AWARENESS (primary), SALES_GENERAL, BOOKINGS.
- **Why now:** the seasonal switch to winter tires (MOMENT). Hypothesis: during the peak the bays fill up regardless, so the money is in tire-set sales and storage contracts, plus filling weekday slots *before* the first snow.
- **Draft objectives:**
  - Business: more winter sets and storage contracts sold, and pre-snow weekday slots filled, over the 4 weeks from 12 Oct to 8 Nov 2026.
  - Marketing: car owners in Astana who have not switched yet see that the master is honest, then message WhatsApp with a code to book or to ask about a set.
- **Metrics:**
  - Primary: code inquiries → bookings and sets sold (owner tally in WhatsApp).
  - Leading: code inquiries per 1k views, sends per reach, saves.
  - Awareness: in-city viewer share.
  - Guardrails: 0 truth incidents; median first WhatsApp reply under 2 h.
- **Feasibility:** no numeric target was given, so feasibility is n/a. A5 runs after week 2, once real inquiry rates exist.

Message to the owner (A4.2 explanation plus 3 questions):
> «Вирусность не гарантирует никто, поэтому мы делаем так: каждую неделю 6–8 роликов на реальных историях вашего шиномонтажа, смотрим, что заходит, и усиливаем. Меряем, сколько людей в Астане посмотрели и сколько написали вам в WhatsApp по коду из видео.
> 1) Что важнее в этом сезоне: (а) продать комплекты зимней резины, (б) заполнить запись на будни до снега, (в) хранение шин? По умолчанию: (а)+(б).
> 2) Пишем в видео код для WhatsApp на номер из 2ГИС (например «Напишите код TK23»)? По умолчанию: да.
> 3) Цены называем только из прайса в 2ГИС с датой, мастер в кадре — только руки и голос, без акций? По умолчанию: да.
> Если не ответите до среды 12:00 — работаем по умолчанию.»

### H2. Inputs used (labelled)

| Input | Status | Contents (all assumed) |
|---|---|---|
| IN-01 | Automated | 150 2GIS reviews |
| IN-02 | Automated | Price list (2GIS) |
| IN-05 | Automated | Searches: «когда менять резину на зимнюю», «как проверить износ шин», «хранение шин астана» |
| IN-06 | Automated | Weather forecast: first snow; the 25 October holiday (verify) |
| IN-10 | Owner, 3 min | 60 chats |
| IN-12 | Worker, 3 min | Store scan |

Not yet available: IN-13 insights and IN-15 stock, which degrades to the stock answer in IN-14.

### H3. Evidence base (excerpt, all hypothetical)

| ID | Type | Content | Count / source |
|---|---|---|---|
| EV-VOICE-1 | fear | «Сказали менять все четыре, а другой мастер — ещё сезон походят» | ×7, 2GIS |
| EV-VOICE-2 | complaint | «В первый снег простоял в очереди 3 часа» | ×9, 2GIS |
| EV-VOICE-3 | question | «Сколько стоит переобуть R16?» | ×31 of 60 chats |
| EV-VOICE-4 | pain | «Колёса некуда деть, балкон забит» | ×5, chats |
| EV-VOICE-5 | praise | «Мастер всё показал и объяснил» | ×6, 2GIS |
| EV-BEH-1 | behaviour | 52% of chats open with a price question | computed |
| EV-REAL-1..5 | reality | Tread depth gauge; balancing machine; pneumatic wrench sound; storage racks; pile of damaged tires in the back yard | IN-12 |
| EV-PRICE-1 | price | R16 changeover price | 2GIS, 2026-10-08 |
| EV-FACT-2 | fact | Storage service exists | 2GIS |
| EV-MOM-1 | moment | First snow forecast | weather API |
| EV-PERSON-1 | person | Master, hands and voice only | IN-11 |

Gap: the tire-set stock range is unknown. Route: owner voice note (IN-14).

### H4. Insights (ranked; scores are evidence, intensity, objective fit, showability, distinctiveness, breadth)

| Rank | ID | Type | Statement | Show how | Score |
|---|---|---|---|---|---|
| 1 | INS-1 | TENSION + PROOF_GAP | Drivers want safe tires but fear being upsold a new set (EV-VOICE-1). The master can measure and show the real verdict. | Gauge reading on camera, then an honest verdict | 3+3+3+3+2+3 = **17** |
| 2 | INS-2 | MOMENT | Everyone comes on first-snow day, so people queue for hours (EV-VOICE-2, EV-MOM-1). Booking a weekday slot beforehand means no queue. | The yard on a quiet weekday vs the same yard on a snow day | 3+2+3+2+1+3 = **14** |
| 3 | INS-3 | MISBELIEF + INSIDER | People judge tires by how they look; age (the DOT code) and tread depth decide. | Close-up of the DOT code; gauge | 2+2+2+3+2+3 = **14** |
| 4 | INS-4 | RITUAL_PAIN | Four wheels fill the balcony every season (EV-VOICE-4). | Storage racks; a labelled skit | 2+2+2+2+2+2 = **12** |
| 5 | INS-5 | PERSONALITY | The master who explains everything (EV-VOICE-5). | Hands plus voice as a recurring character | 2+1+2+3+2+2 = **12** |

Wild insight: the price question dominates (EV-BEH-1), so test an honest «из чего складывается цена» video with owner-approved data only.

### H5. Ideas (12 of 48 raw shown; RU hooks are variant A)

| ID | Idea | Engine / arm | Hook A (RU) | Driver | Mode, worker min | S |
|---|---|---|---|---|---|---|
| I-01 | Series «Менять или ещё походят?» ep. 1: a customer's tire (with consent) measured, honest verdict | E04 / A-PROOF (hero) | «Вам сказали менять все четыре. Проверим?» (H01) | S3→SH2 | PM-V, 4 | 17 |
| I-02 | Hero ep. 2: a different tire, the opposite verdict | E04 / hero | «Эта выглядит новой. А по факту?» (H12) | W3 | PM-V, 3 | 16 |
| I-03 | «Как узнать возраст шины за 5 секунд» (DOT) | E18 / A-UTIL | «Год выпуска шины написан на ней. Вот где» (H06) | SV1, SH3 | PM-V, 3 | 15 |
| I-04 | Myth check: the coin test vs the gauge | E03 / A-PROOF | «Проверка монеткой — работает или нет?» (H01) | C1, W1 | PM-V, 3 | 15 |
| I-05 | «Что мастер видит, а вы нет»: damaged tires from the yard, what caused each (real tires only, owner OK) | E02 / A-UTIL | (no words) hand turns a tire with a bulge, text «Это началось с одной ямы» (H04) | S1, SV1 | PM-W, 3 | 14 |
| I-06 | Reply to comment «Сколько стоит переобуть R16?» with `{PRICE:EV-PRICE-1}` and the date | E12 / A-REACT | «Ответ на комментарий: сколько стоит R16» (H09) | ACT | PM-R, 0 | 13 |
| I-07 | Moment kit «Первый снег: два сценария» (quiet weekday yard vs snow-day yard, no faces or plates) | E17 / A-MOMENT | «Первый снег в Астане. Два варианта утра» (H05) | S6, SH1 | PM-W, 2 now + 1 on the trigger | 14 |
| I-08 | Review reaction: green screen over EV-VOICE-1, the master explains how to check for yourself | E13 / A-REACT | «Нам часто пишут: “сказали менять все четыре”» (H09) | trust, SH2 | PM-S, 1 | 13 |
| I-09 | POV skit «Колёса на балконе», labelled «постановка» → storage | E14 / A-HUMOR | «POV: октябрь, и балкон снова ваш» (H07) | SH1, SH5 | PM-W, 4 | 12 |
| I-10 | ASMR «Звук сезона»: wrench, balancing machine, loop | E07 / A-PROC | (sound first) (H10) | S1, W6 | PM-W, 2 | 11 |
| I-11 | Trend remix: an evergreen POV template, cargo = INS-3 | E20 / A-MOMENT | Depends on the template | SH3 | PM-R, 0 | 10 (wild card) |
| I-12 | «Из чего складывается цена переобувки» (only if the owner approves the numbers) | E16 / A-CONVERT | «Почему переобувка стоит столько» (H01) | SH3, C5 | PM-V, 3 | 12, on hold for approval |

**Rubric detail for I-01:** P1 2, P2 2, P3 2, P4 2 (send line: «Скинь отцу, ему тоже говорили менять все четыре»), P5 1, P6 2, P7 2, P8 2, P9 1, P10 2 → S = 18, shown as 17 after the producibility penalty from the consent dependency. Nudge = +0.14.

**Week-1 selection (8 posts):** I-01, I-02, I-03, I-04, I-05, I-06, I-08, I-09. I-07 is pre-shot and held until the trigger; I-10 and I-11 are backups.

Diversity check:
- 7 engines (pass).
- Hook types H01, H12, H06, H04, H09, H07 (pass).
- Insights INS-1, 2, 3, 4 (pass; INS-1 holds 4 of 8 posts, so I-02 can be swapped for I-10 if strict 40% is enforced).
- Modes PM-V, PM-W, PM-R, PM-S, with 2 zero-worker posts (pass).
- Drivers include share, save and comment (pass).
- Conversion: I-06, plus codes on every post (pass).
- Wild card: I-11 is in backup and gets promoted if a fitting template appears in the trend scan.

### H6. Test plan

- **Platforms:** Instagram Reels (existing account; baseline = median of the last 14 days of the client's own posts) and TikTok (new account; needs the owner's consent; pooled vertical prior until 5 posts).
- **Active arms:** A-PROOF (hero), A-UTIL, A-REACT, A-HUMOR, A-MOMENT.
- **Priors:** vertical pooled data if it exists, otherwise 0 plus the rubric nudge, sd 0.7.
- **Hooks:** A/B/C randomised across the two platforms per body; seeds logged.
- **Codes:** TK23, TK24, … (only A B C E H K M O P T X and 2–9).
- **CTA (RU):** «Напишите в WhatsApp код TK23 и размер шин — подскажем по наличию и времени». The pinned comment repeats it.
- **Reads:** 48 h and 7 days.
- **Decision rules:** DR-1 to DR-10.
- **Power note to the owner, in plain words:** «Через 2 недели будет видно направление, уверенный вывод по одному клиенту — через 6–8 недель; быстрее — за счёт данных других клиентов той же сферы.»

### H7. Campaign

- **Big idea (internal):** this is the tire service that measures before it advises, and proves it on camera.
- **Hero series:** «Менять или ещё походят?»
  - Fixed opening line: «Проверим?»
  - Structure: tire → gauge → verdict → code.
  - Episode bank: 10 tires of different ages and conditions, consent per customer, or the shop's own tires.
  - Cadence: 3 per week.
- **Tracks, weeks 1–2:** hero 35%, proof and utility 30%, reactive 20%, humor 10%, conversion through codes in every post and I-06-type replies.
- **Conversion path:** code → WhatsApp quick reply (RU):
  > «Здравствуйте! Вы по видео TK23. Какой размер шин и какой день удобен? Сразу скажем, есть ли окно и комплект в наличии.»

  The guardrail is a first reply within 2 hours.
- **Offer:** none in weeks 1–2. If week-2 data shows demand for sets, propose to the owner one-line options (for example, priority booking for people who write with a code), approved by the owner or not run.
- **Non-video levers** (proposed, each awaiting approval):
  - a WhatsApp broadcast to opted-in past customers: «Запись на будни до снега открыта»;
  - fresh 2GIS photos;
  - asking happy customers for a review.
- **Calendar:**
  - Week 0 (9–11 Oct): setup.
  - Week 1 (12–18 Oct): explore.
  - Week 2 (19–25 Oct): explore and learn; reply videos.
  - Week 3 (26 Oct–1 Nov): focus.
  - Week 4 (2–8 Nov): scale and harvest.
  - Any day the snow forecast fires: I-07 within 3 hours, plus a booking reminder in Stories.

Shoot card, week 1 (RU, worker-facing, ≈14 minutes):
> **Подготовка (2 мин):** протрите камеру. Телефон вертикально. Без зума — подходите ближе. Компрессор и музыку на время записи голоса выключить.
> 1. **[I-01]** Глубиномер вставляют в протектор шины клиента (только если клиент разрешил снимать, без лица и номера машины), 30 см, 5 сек, 2 дубля.
> 2. **[I-01]** Голосовое: встаньте в тихий угол или сядьте в машину, телефон у рта. Честно скажите, что показал замер на этой шине и что вы советуете. 2 дубля. Если клиента нет — снимите нашу старую шину со склада.
> 3. **[I-02]** То же для второй шины, которая «выглядит новой», 5 сек + голосовое.
> 4. **[I-03]** DOT-код на боковине крупно, палец показывает последние 4 цифры, 20 см, 5 сек, 2 дубля.
> 5. **[I-04]** Монетка в протекторе, потом глубиномер в той же канавке, 30 см, по 5 сек.
> 6. **[I-05]** Задний двор: рука медленно поворачивает шину с грыжей, 40 см, 10 сек. Без людей и номеров.
> 7. **[I-09]** Стеллаж хранения, медленная панорама 8 сек; отдельно 4 колеса у стены 5 сек.
> 8. **[I-07, заготовка]** Пустой двор сейчас, 10 сек, без номеров машин.
> 9. **Библиотека (1 мин):** гайковёрт 5 сек с 50 см (звук), балансировочный станок 5 сек, руки мастера 10 сек, въезд 10 сек.
> **Если увидите:** первый снег или очередь — двор 10 сек без лиц и номеров; клиент удивился — спросите разрешения, 10 сек.
> **Голосовое (1 мин):** какие 3 вопроса задавали клиенты на этой неделе?

- **AI tasks:** edit per beats; burned-in RU captions; denoise the voice memos; blur plates and faces; covers; label I-09 «постановка»; draft replies to comments; build PostPackages with codes; check prices against EV-PRICE-1 ≤ 72 h before publishing.
- **Decision rules in this case:**
  - If two hero episodes reach y ≥ 0 and generate code inquiries, the hero goes to 3–4 per week in week 3 (DR-3).
  - If I-07 spikes on snow day (DR-2): reply videos «как записаться без очереди», a Stories reminder, and a boost proposal to the owner.
  - If A-HUMOR draws views but no inquiries after n ≥ 10 posts (DR-6), cap it at 15%.
  - If week 3 shows no arm with P(μ > 0) ≥ 0.6 and zero inquiries (DR-9), re-check WhatsApp reply time and the code placement, then refresh IN-10.

Friday report template (RU; filled only with measured numbers):
> «Неделя 1: [X] роликов, [V] просмотров ([g]% — Астана). По кодам написали [I], записались [B], купили комплект [S].
> Лучше всего: [серия/подход] — [k]× от обычного (рано судить / уверенно).
> Дальше: [план].
> Нужно от вас (1 мин): можно ли называть цену хранения шин из прайса 2ГИС? Если не ответите до среды — не называем.»