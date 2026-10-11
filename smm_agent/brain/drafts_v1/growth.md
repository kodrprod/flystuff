# MetaPrompt Campaign Brain: the method (growth and performance edition)

This is for the MetaPrompt agent. It covers any local business in Kazakhstan or the CIS, in any industry, and any request from the boss. Copy that viewers or the owner will read is in Russian. Everything else is in English. Field names follow `smm/brain.py` where a schema already exists. New fields are marked **(+)**.

---

## 0. Ground rules the agent never breaks

1. **Views are an input, not the goal.** Every campaign has one primary business number, and the agent must be able to count it itself (coded WhatsApp conversations, orders, applications, bookings).
2. **Nobody can predict short-form winners from text.** Our blind judge reached Spearman 0.44 on long-form titles but 0.11 on 1,172 Shorts (0.07 for retail, where the confidence interval includes 0). "для начинающих" and "vs" won on long-form and did not replicate on Shorts. Trivial features (hashtags, title length, duration) scored about 0.00 to 0.07. So the agent treats every score as a **prior**. It maximises the number of strong, diverse, cheap shots on goal, and audience data picks the winners.
3. **Truth.** Every claim a viewer sees maps to a verified fact in the facts ledger. The agent never invents prices, claims, deadlines, scarcity, testimonials or people. AI footage never stands in for the real product, the real staff or real customers.
4. **Time budgets are hard limits.** The owner gives at most 30 minutes once and at most 5 minutes a week. Staff give at most 20 minutes a week with one weak phone, which records good audio only when held close.
5. **Attribution comes before content.** No campaign starts without per-video WhatsApp codes and a baseline. Without a baseline, no one can claim a lift.
6. **Pre-register every test.** Before anything is posted, write down the hypothesis, the metric and the decision rule. Results never get explained after the fact.
7. **Approvals.** Nothing gets spent, offered or published beyond the approvals set at intake.
8. **Diagnose the funnel before making more content.** If people message and don't buy, the leak is in the chat, not in the video.

---

## A. Request intake

### A1. The objective ladder (fill in every rung, every time)

| Rung | What it answers | Rule |
|---|---|---|
| `request_verbatim` | What the boss literally said | Keep the original wording and language. Never paraphrase it away. |
| `business_objective` | What changes in money, customers, people or time, for what, by when | It must name an object (product, service or role), a direction and a date. Example: "Sell more X" becomes "+N orders of X per week by DD.MM". |
| `marketing_objective` | Which people must do what they do not do now | Define the audience by **situation and place**, not by demographics alone ("родители первоклассников в Астане за 3 недели до 1 сентября"). Define the behaviour as an **observable action** (write on WhatsApp with a code, come in, order on Kaspi, apply). |
| `success_metric` | One number we count ourselves | Give the name, the exact counting method, the baseline, the target and `by_when`. If we cannot count it ourselves, it cannot be the primary metric. |
| `leading_indicators` | What moves within 48 h and predicts the metric | 3 to 5 items, taken from the metric tree in F10. |
| `guardrails` (+) | What must not get worse | Margin, capacity, staff minutes, rating, chat response time, brand no-gos. |
| `capacity` (+) | What the business can actually serve | Units per week that are free. If the business is at capacity, demand gets redirected (other days, other products, pre-orders), not grown. |
| `constraints` | Hard limits | Deadline, spend cap, who and what can be filmed, stock, legal, approvals. |
| `assumptions` | What we are guessing | Each one carries a confidence level, how and when it will be verified, and the default used until then. |

### A2. Request-type playbook

| `request_type` | What the boss says | Reframe to | Default primary metric | Traps |
|---|---|---|---|---|
| `sales_push` | «Продайте X», «нужны продажи», «склад забит» | Orders of named products or services in a window | Orders from coded WhatsApp conversations, or Kaspi orders of the featured SKU | Pushing stock that isn't there. Discounts without approval. Price slides. |
| `launch_or_event` | «Открываемся», «мастер-класс в субботу» | Attendance or registrations by date | Coded registrations, then attendance | Starting less than 10 days before the date. Invented "мест мало". |
| `awareness_or_viral` | «Сделайте вирусным», «хочу как у X» | See A4 | Coded conversations, plus a process metric (hit rate) | Promising virality. Choosing views as the goal. |
| `reputation_or_trust` | «Плохие отзывы», «нам не доверяют» | Rating and the conversion rate of inquiries | Rating trend, new reviews per week, QC→sale rate | Fake reviews (never). Arguing with reviewers in public. |
| `price_pressure` | «Конкуренты дешевле» | Protect conversion and margin | QC→sale rate and average check | Price wars. Naming competitors. Unverifiable "мы дешевле". |
| `retention_or_loyalty` | «Клиенты не возвращаются» | Repeat purchases | Repeat-customer conversations (code "СВОИ" or label) | Feed content written only for existing customers. Use Status and broadcast lists instead. |
| `hiring` | «Найдите продавца» | Qualified applicants interviewed | Coded applications that pass a 3-question screen | Making the job look better than it is. Pay ranges the owner didn't give. Discriminatory requirements (age, gender, ethnicity). |
| `b2b_leads` | «Хотим корпоративных клиентов» | Qualified B2B conversations | Coded B2B inquiries with company and volume | Consumer virality tactics. Leave out entertainment-only ideas. |
| `should_we_do_social` | «Нужен ли нам TikTok?» | A 4-week test with a pre-registered verdict | Coded conversations per staff-hour, compared with the threshold agreed upfront | Answering from opinion instead of a test. |
| `other` | «Переезжаем», «новый филиал», «юбилей» | Map to the nearest change in people, money or time | Defined case by case | Content with no measurable job. |

When a request has several types, pick **one** primary. The others become guardrails or the next sprint.

### A3. Feasibility check: funnel math (required whenever there is a target)

```
QC        = qualified conversation (definition in F5)
req_QC    = target_outcomes / close_rate
req_views = req_QC / (QC_per_1k_views / 1000)
ach_views = posts_in_window × baseline_median_views × mean_to_median
            mean_to_median ≈ 1.6–2.0 (views are heavy-tailed, log-SD ≈ 1–1.2;
            replace with the account's own ratio once ≥15 posts exist)
ratio     = req_views / ach_views
verdict   = feasible (≤1) | stretch (1–3) | unrealistic (>3)
```

- `close_rate` and `QC_per_1k_views` come from the client's baseline (B, input 3) or a pooled vertical prior in the knowledge base. If neither exists, plan with a labelled range, write it as an assumption, and measure it in weeks 1 and 2. Never show a planning range to the owner as a forecast.
- For **stretch**, tell the owner it depends on hits or a boost, and show the boost math from F6 (`CPQC_ceiling × QC gap`).
- For **unrealistic**, write a `push_back` with three options: a longer window, a smaller target, or a boost budget with its expected cost. Add an offer only if the owner approves one.

### A4. "Go viral" and other unrealistic asks

1. Do not promise virality. Do not refuse either. Translate the ask into two commitments:
   - **Process commitment:** N posts a week, ≥4 different angles, and a hit rate (the share of posts reaching ≥3× the account's median views) reported weekly.
   - **Business commitment:** the primary metric from A2. When nothing else is known, use coded conversations.
2. Define "вирусный" for this account in numbers: "a post with ≥10× our median views, or ≥N local inquiries from one post".
3. "Хочу как у X": mine X's outliers (B, input 2) for mechanics, but set targets against **our** baseline. X's account size, budget and history are not ours.
4. "Без съёмки и без людей": switch to AI-explainer, product, screen and reply formats (D3). Note in `assumptions` that the expected ceiling is lower, and test one people-format the moment someone consents.
5. Template for the owner message:

> «Вирусность нельзя заказать — её не может гарантировать никто, мы это проверяли на 1 172 роликах. Что мы можем: делать 5 разных роликов в неделю на основе того, что реально спрашивают ваши клиенты, считать, какой ролик привёл сообщения в WhatsApp (у каждого свой код), и вкладываться в те, что сработали. Цель на 4 недели: [N] обращений с кодом и [M] заказов. Если ролик «выстрелит» — сразу делаем продолжение.»

### A5. Conflicting requests

Resolve in this order: **truth and law, then the boss's money objective, then capacity and guardrails, then style preferences.** Run one primary metric per campaign. When there are two objectives, either run them in sequence (sprint 1, then sprint 2) or split the slots (for example 70/30) and measure each separately.

| Conflict | Default resolution |
|---|---|
| "Viral, but premium and serious" | Craft, process and proof content can be both (D2 engines 6, 7, 17). Leave out humour and skit formats. |
| "Clear the stock, but don't mention discounts" | Ask once (Q2). Until answered, run value and selection content on the overstocked items, with no prices. |
| "Fast results, no budget" | Organic only. At the end of week 2, show the boost math with real data and ask then. |
| "More orders, but we're full" | Redirect to free capacity (weekdays, other products, pre-orders for future dates). Make capacity a guardrail. |
| "Grow the brand and sell X by Friday" | Friday comes first, because it has a date. The brand series starts in sprint 2. |
| "Don't show staff, but make it human" | Use hands, voice, real customer questions and reply videos. People formats are tested when someone volunteers. |

### A6. Non-sales and non-marketing requests

- **Hiring:** the audience is people in the city who could do this job, not customers. Show what the job really involves (a day on shift, real tasks, honest pain points). Use a code for applications (for example "РАБОТА") plus 3 screening questions on WhatsApp, written in Russian by the agent and approved by the owner. Pay and schedule appear only if the owner states them.
- **Reputation:** the agent never writes or solicits fake reviews. Content turns real recurring complaints into "what we changed" videos, but only if the owner confirms the change. Make review requests part of handover (one line in a WhatsApp quick reply).
- **Event or launch:** start ≥10 days out. Plan 3 phases (anticipation, then reasons to come, then the last 48 h of logistics, which is the only point where "завтра" is honest) and a code per phase.
- **"Should we be on social?":** answer with a 4-week test (F7) and a pre-registered verdict. For example: "continue if ≥X coded QC per staff-hour, or a hit rate ≥15%". Thresholds come from the owner's margin.
- **Not marketing** (fix the website, find a supplier, accounting): say plainly that it is outside scope and say what the agent can do instead. Do not stretch a content campaign over a non-marketing problem.

### A7. Clarifying questions: at most 3, usually fewer

Ask a question only if **all three** of these hold:
- (a) the answer changes the objective, the offer, or what can be shown or said;
- (b) it cannot be inferred from the inputs;
- (c) a wrong guess is costly or irreversible (money, legal, a public claim, a person's face).

Otherwise assume, label the assumption, and proceed. Every question is **closed**, carries a **default** and a **deadline**, and goes in **one batched message**. Questions that matter only later are **deferred** until the moment they become decision-relevant. The boost-budget question, for example, waits until there is a winner to boost.

Priority ladder (take from the top and stop at 3):
1. **Win definition**, only if A2 cannot infer it: «Что для вас успех через 4 недели: а) больше сообщений в WhatsApp о [X], б) продажи конкретного товара, в) отклики на вакансию? Если не ответите до [время] — считаю «а».»
2. **Offer and claims authority**, if the request touches price, a promotion or a deadline: «Можно ли предложить [бонус/скидку] и есть ли реальная дата окончания? Без ответа — работаем без скидок и без сроков.»
3. **People on camera**, if the best ideas need a face: «Кто готов быть в кадре: лицом / только руки / только голос? Без ответа — снимаем только руки и товар.»

Defaults used when a question isn't asked or isn't answered:

| Topic | Default |
|---|---|
| Primary metric | Coded QC on WhatsApp, then sales labelled in WhatsApp Business |
| Offer | None. No prices unless they are verified and fresh (≤7 days). |
| Urgency | None |
| People | Hands, product and voice only |
| Volume | 5 posts a week, cross-posted to TikTok, Reels and Shorts |
| Language | Russian. Kazakh subtitles kept as a test variant. |
| Paid boost | 0 ₸ until approved |
| Sprint | 4 weeks |
| Approval | The owner approves the weekly batch in one WhatsApp reply. "Silent approval after 24 h" applies only if the owner opted in at intake, and never covers offers, new faces or spend. |

### A8. Intake failure modes

- Accepting "views" or "followers" as the primary metric.
- Setting a target without a baseline.
- Asking more than 3 questions, or asking open questions without defaults.
- Missing a capacity ceiling. Viral demand on a full Saturday is lost money and bad reviews.
- Treating a conversion problem as a content problem. Check the chat response time first (F5).
- Silently "fixing" an unconfirmed fact instead of turning it into a batched question.

---

## B. Inputs

### B1. Principles

- **Automate first.** Tier-0 inputs cost the owner nothing and are always collected before anything is asked.
- Buy owner minutes in order of **value per minute**. The onboarding pack (B4) caps at 30 minutes.
- **Never block on a missing input**, with three exceptions:
  - no analytics access means measurement can't run, so produce but flag;
  - no filming permission means only no-people formats;
  - an unverifiable claim gets dropped.
- Every input has a named fallback. Every extraction becomes evidence items (C1) with source and date.

### B2. Ranking (value per owner-minute)

| # | Input | Owner min | Staff min | Why it matters | Missing blocks… |
|---|---|---|---|---|---|
| 0a | Public footprint: site, catalogue, socials, maps, Kaspi page | 0 | 0 | Facts, proof, baseline, reviews | Nothing (degrade) |
| 0b | Peer and competitor short-video outliers plus their comments | 0 | 0 | Mechanics, customer language | Nothing |
| 0c | Demand signals: search suggestions, marketplace Q&A, competitor reviews | 0 | 0 | Questions, moments | Nothing |
| 0d | Calendar: holidays, seasonality, local events | 0 | 0 | Moments | Nothing |
| 0e | Cross-client knowledge base and arm stats for the vertical | 0 | 0 | Priors | Nothing |
| 1 | WhatsApp chat export (15 to 20 recent customer chats) | 5 | 0 | Highest-density customer language, objections, the leak | Insight confidence drops |
| 2 | Owner voice note (8 questions) | 10 | 0 | Proof, stories, constraints, no-gos | Constraints get assumed |
| 3 | Baseline numbers (inquiries a week, orders, average check, margin, close rate) | 5 | 0 | Feasibility, CPQC ceiling, lift | Lift claims, boost math |
| 4 | Priority products or services, stock, capacity | 3 | 0 | What to push, what not to | Objective fit |
| 5 | Permissions and rules (faces, claims, offers, spend cap) | 2 | 0 | Hard rails | People and offer ideas |
| 6 | Camera-roll media dump | 5 | 0 | Proof assets, free B-roll, moments | Nothing (staff fill in) |
| 7 | Account access (posting and analytics) and WhatsApp Business labels set up | 5 to 10 once | 0 | Measurement | **The experiment engine** |
| 8 | Store walkthrough video | 0 | 2 once | Filmable locations, light, noise | Producibility guesses |
| 9 | Customer one-question micro-interviews | 0 | 1 each | Verbatim language, proof (with consent) | Nothing |
| 10 | Standing "moment capture" list | 0 | Opportunistic | Real moments | Nothing |
| 11 | Weekly metrics: post stats, code counts, sales labels | 0 to 2 a week | ≤2 a week | The learning loop | Decisions |

### B3. Input cards

**0a. Public footprint**
- *Extract:*
  - prices with as-of date and URL;
  - policies (returns, warranty, delivery, payment, instalments);
  - address, hours, contacts;
  - product range and depth (number of SKUs per category, price bands);
  - review rating distribution, recurring praise (proof) and recurring complaints (tensions or ops issues), quoted verbatim;
  - stale or inconsistent page content (old city names, dead blog) as risks;
  - every own social post with views, likes, comments and date. This gives a **baseline per platform**: the median of the last 15 posts and the account's own outliers (≥3× median).
- *Obtain:* the crawler fetches the client's own domain first, then linked socials and maps. A login wall or a block (for example 403 or 429) goes into `missing` with the fallback "owner screenshot".
- *If missing:* no site means the owner's voice note becomes the fact source (confidence `likely` until a second source confirms it). No social history means the first 10 posts form the baseline, with the vertical prior meanwhile.

**0b. Peer outliers**
- *Extract:*
  - for 10 to 20 RU-language peer accounts in the same vertical (local first, then CIS), posts from the last 90 days at ≥3× that channel's median views;
  - for each outlier: the **mechanic** (engine, format, hook type, length, people on camera), never the script;
  - top comments as customer language.
- *Obtain:* automated listing and metadata. Per-video downloads may be blocked, so work from listings and visible metadata, and don't bypass bot walls.
- *Treat as hypotheses.* Outlier mechanics feed exploration arms; they are not winners. Experiment 002 showed that patterns don't transfer reliably.
- *If missing:* use global engines (D2) with no performance prior.

**0c. Demand signals**
- *Extract:* questions as people phrase them ("какой … выбрать", "… или …", "сколько стоит …", "можно ли …"), moment words ("к 1 сентября", "на свадьбу", "срочно"), and competitor complaints (which become proof needs for us).
- *Obtain:* search autocomplete in Russian, YouTube search suggestions, Q&A on product pages, and competitors' public reviews.
- *If missing:* rely on input 1.

**0d. Calendar**
- *Extract:* national and local dates relevant to the vertical (Новый год, 8 марта, Наурыз 21 to 23 March, 1 сентября, the city day where it applies), the business's own seasonality (owner confirms), and paydays or holiday travel if relevant.
- *Rule:* a moment is used only if it creates a real need for **this** business. "Congratulations" posts are not content.

**0e. Knowledge base**
- *Extract:* `learnings.jsonl` entries for the vertical and "any", with their strength labels, plus pooled arm stats for tags (E5). These set Thompson priors and the rubric weights.
- *Rule:* never carry a finding beyond its strength label. Never carry long-form findings to short-form.

**1. WhatsApp chat export**
- *Extract (after stripping names and phone numbers):*
  - the first message of each chat, which is the clearest intent;
  - question intents with counts (price, availability, how to choose, delivery, timing, comparison, trust);
  - objections and where chats die;
  - verbatim phrases of 12 words or fewer, top 3 per intent;
  - moment words;
  - **median first-response time in working hours**;
  - share of chats ending in a purchase signal ("оплатил", address, booking);
  - lost reasons ("дорого", "подумаю", "нет в наличии").
- *Obtain:* WhatsApp exports one chat at a time. Ask for 15 to 20 recent customer chats without media («чат → ⋮ → Ещё → Экспорт чата → Без медиафайлов»; on iPhone «имя контакта → Экспорт чата»). If the business uses a CRM or a WhatsApp API inbox, export from there instead.
- *Privacy:* chats contain personal data. Keep them client-scoped. Never quote identifiable details in content. Never publish chat screenshots. Paraphrase questions into a generic form («Нам часто пишут: …»). Delete the raw exports after extraction unless the contract says otherwise.
- *If missing:* use reviews, peer comments and the staff voice note (input 11 fallback: «5 вопросов, которые вам задают чаще всего»), with customer language marked `likely`.

**2. Owner voice note** (sent as one WhatsApp message, see B4)
- *Extract:* top sellers and margin hints, beliefs about why customers choose them, proof claims (to verify), 1 or 2 stories, daily watchable realities, no-gos, filming permissions, offer and spend authority.
- *Rule:* "owner says" is `likely` until corroborated. Constraints and no-gos are binding immediately.
- *If missing:* use the A7 defaults and run the campaign on public facts only.

**3. Baseline numbers**
- *Extract:* inquiries a week (an estimate is fine, labelled as such), orders a week, average check, gross margin %, the close rate estimate, and Kaspi orders for the relevant SKUs if the business sells there.
- *Use:* feasibility (A3), the CPQC ceiling (F6), and incrementality (F10).
- *If missing:* the first 2 weeks double as baseline measurement. No lift claims until then. Use labelled assumptions in the math.

**4. Priorities, stock, capacity**
- *Extract:* top 10 by revenue, top 5 by margin, overstock, items that can't be resupplied (never promote those), and free capacity per day or week.
- *If missing:* infer demand from catalogue depth and review counts (labelled `likely`), and add one question to the batch.

**5. Permissions and rules**
- *Extract:* who can appear and how (face, hands, voice); whether customers may be filmed (always with consent at the time); banned topics and words; what the business may claim (warranty terms, "official dealer" only with proof); offer authority; monthly boost cap.
- *If missing:* the A7 defaults.

**6. Media dump**
- *Extract:* proof assets (before and after shots, finished work, volume, awards with dates), moments, people (only those with consent), and reusable B-roll. Tag each by subject, quality and consent.
- *If missing:* staff capture per the moment list (input 10).

**7. Access**
- *Extract:* posting rights, per-post analytics (views, average watch time, completion, shares, saves, profile visits), and WhatsApp Business labels created (for example «Видео», «QC», «Оплачен»).
- *If missing:* a weekly 2-minute screenshot routine. Without either, the engine cannot allocate, so say so in the brief.

**8. Store walkthrough** (staff, one time, 2 min)
- *Extract:* filmable spots (good light, quiet corners), noise sources, hero displays, which processes are visible, and where the phone can rest.
- *If missing:* first-week shots are designed to be robust (hands, close-ups, near a window).

**9. Customer micro-interviews** (staff, 1 min each, consent first)
- One question, phone held close between the two people: «Чего вы боялись перед покупкой?» or «Почему выбрали нас?»
- *Extract:* verbatim fears and reasons, and proof clips (usable on camera only with spoken consent on the recording).

**10. Moment capture list** (standing, in Russian, on the shoot card)
- «Если видите — снимите 10 секунд вертикально, близко: привезли новую партию; клиент удивился или обрадовался; необычный заказ или вопрос; что-то сломалось и вы починили; очередь или самый загруженный час.»

**11. Weekly measurement inputs**
- Post metrics at +48 h and +7 d, code counts from labels or chat exports, sales labels, Kaspi SKU orders, and comments (pulled automatically).

### B4. Owner onboarding pack (one message, 25 to 30 min total)

> «Здравствуйте! Чтобы ролики приводили клиентов, а не просто просмотры, нам нужно от вас 25–30 минут один раз:
> 1) **Голосовое на 10 минут** — ответьте своими словами на вопросы ниже.
> 2) **Экспорт 15–20 последних переписок с клиентами в WhatsApp** (без медиа): чат → ⋮ → Ещё → Экспорт чата → Без медиафайлов. Мы удаляем имена и номера и никогда не публикуем переписки.
> 3) **Скриншоты или цифры**: сколько обращений и заказов в неделю за последний месяц, средний чек, примерная наценка.
> 4) **20–50 фото и видео из телефона**, где видно работу, товар, процесс.
>
> Вопросы для голосового:
> 1. Что покупают чаще всего и на чём вы зарабатываете больше всего?
> 2. Какой вопрос клиенты задают чаще всего? А какой — самый неожиданный?
> 3. Чего клиенты боятся или в чём сомневаются перед покупкой?
> 4. Почему выбирают вас? Чем это можно доказать (гарантия, отзывы, цифры, годы работы)?
> 5. Расскажите одну историю клиента, которую вы помните.
> 6. Что у вас каждый день происходит такого, на что интересно посмотреть — процесс, звук, люди?
> 7. Что нельзя говорить или показывать? Кто из сотрудников готов появляться в кадре?
> 8. Можно ли делать бонусы или акции? Есть ли бюджет на продвижение роликов, которые сработают?»

### B5. Input failure modes

- Asking the owner for things the crawler can get.
- Requesting a 90-day "full export" (it is per chat, so it costs an hour and the owner won't do it).
- Treating owner claims as verified.
- Using competitor content as scripts instead of mechanics.
- Starting production with no analytics path, which produces content nobody can learn from.

---

## C. Working the inputs

### C1. Raw inputs to the evidence base

Atomise everything into **one claim per evidence item**:

| Field | Rule |
|---|---|
| `kind` | One of `fact`, `customer_language`, `behaviour`, `proof_asset`, `moment`, `constraint`, `market`, `performance` |
| `claim` | One sentence in English. Numbers exactly as in the source. |
| `verbatim_ru` (+) | The original customer or owner phrase when the kind is `customer_language`, de-identified |
| `count` (+) | How many times it appeared (for example "11 of 18 chats") |
| `source` and `as_of` (+) | URL, file name or "owner voice note DD.MM" |
| `confidence` | `verified`: a primary public source or two independent sources. `likely`: a single owner or staff statement, or a frequency taken from a small sample. `assumption`: our guess. |
| `audience_usable` (+) | False for internal margins, customer identities, unconfirmed claims, and anything under a no-go |
| `expires` (+) | Prices and stock: 7 days. Promotions: their end date. Policies: 90 days or on change. |

Extraction procedures:
- **Chats:** de-identify, classify intents, count, extract verbatim, measure response time and drop-off. Output: `customer_language` and `behaviour` items, plus one `constraint` item if response time is a leak.
- **Reviews:** cluster praise and complaints, count them, keep the verbatim. Praise becomes `proof_asset` candidates. Complaints become a tension or an ops issue (an ops issue goes to the owner, not into content).
- **Voice note:** split into `fact` (`likely`), `constraint` (binding), stories (`moment`/`proof_asset`, `likely`), and content-able realities.
- **Own and peer posts:** `performance` items with ratio to median, n and date. Peer items are `market` with confidence `likely` at most.
- **Catalogue:** `fact` items for prices, policies and ranges, with an expiry. Suspicious values get excluded and flagged: a 90% "discount" is probably a site error.

### C2. Evidence to insights

An insight is a **usable truth about people and this business that a phone can show**. The insight shapes, which drive engine choice in D2:

| Type | Pattern |
|---|---|
| `tension` | They want X but fear or are blocked by Y |
| `myth` | They believe X; reality is Y, and we can prove it |
| `hidden_knowledge` | Insiders know X; customers pay for not knowing it |
| `moment` | A specific situation or date when the need fires |
| `identity` | Who the customer is or wants to be, and the words of that tribe |
| `proof_asset` | A verifiable strength (policy, process, results, volume, years) |
| `content_reality` | Something visible and repeatable here that is inherently watchable (process, sound, transformation, odd requests, people) |
| `friction` | Something in the purchase path that content can fix (people don't know about delivery, reserving, instalments) |
| `price_value` | Customers misjudge what the price buys |

Statement format:

> **[Who, in what moment]** wants **[desire]** but **[tension or belief]**. The truth we can show: **[fact or proof]**. The camera sees **[content reality]**. It moves **[objective]** because **[link]**. Evidence: [ids].

Rules:
- Every insight cites ≥1 evidence id.
- A `verified` insight needs ≥2 independent evidence items, or 1 verified fact plus 1 customer-language item with count ≥3. Anything less is a `hypothesis`. A hypothesis may feed **exploration** slots only and may never carry a claim.
- An insight with no "camera sees" line is a strategy note, not a content insight. Keep it in the brief and don't generate ideas from it.

### C3. Ranking insights (a prior, like everything else)

Score each insight from 1 to 5 on seven criteria. Default weights are in brackets:
- **Frequency** (1.2): how many customers hit this
- **Intensity** (1.0): money, emotion or risk at stake
- **Objective proximity** (1.4): how close it sits to the primary metric
- **Showability** (1.2): one phone, ≤5 staff minutes
- **Ownability** (0.8): only this business has the right or the proof
- **Proof** (1.0): how strong the evidence is
- **Freshness** (0.6): a moment is near

Keep the top 6 to 10, with a type mix of at least 1 `tension` or `myth`, 1 `proof_asset`, 1 `content_reality` and 1 `moment`.

After every sprint, **re-rank from data**: insights whose ideas produced QC move up regardless of their prior.

### C4. Keeping facts true (truth rails, enforced in code where possible)

1. Every audience string (hook, on-screen text, voice-over, caption, CTA, pinned comment) lists `facts_used` with ledger ids. Code checks every number, price, percentage, date and named policy against the ledger.
2. **Claim ladder:**
   - `verified`: state it.
   - `likely`: use it only as the owner's own words on camera ("мы так работаем") or not at all.
   - `assumption`: never in audience copy.
3. Prices must be ≤7 days old, or shown with «цена на ДД.ММ». Never round in a way that changes meaning. Never compute a "discount" that isn't stated by the source.
4. **No superlatives or rank claims** («лучший», «№1», «самый дешёвый в городе») without a citable source. **No urgency** («только сегодня», «успейте», «осталось N») without an owner-confirmed end date or stock count.
5. No testimonials except public reviews (labelled «из отзыва», no names unless public) or recorded customers with on-camera consent.
6. Staged scenes are never presented as documentary. A dramatised real question is framed truthfully («Нам часто пишут: …», «Типичный вопрос: …»).
7. AI never generates the real product as if filmed, never generates customers or staff, and never clones a staff voice without written consent. AI visuals are allowed for explaining the invisible (diagrams, "inside" views), and are labelled as illustration when that could be confused with reality.
8. Unconfirmed facts are never silently "fixed". They become one batched owner question, and the idea stays blocked until answered.
9. Never name competitors negatively. Comparisons are of product types and price bands, not of named rivals.
10. Third-party images (for example customers' Pinterest references) are not published without rights. Show the result and describe the request instead.

---

## D. Idea generation for high-chance short videos

### D1. What each viewer action needs

| Action | What the viewer must feel in the moment | Mechanisms that cause it | Where it lives | Measured as |
|---|---|---|---|---|
| **Stop** (0 to 1.5 s) | "This is about me", "something is off", "what is that?" | A visible anomaly or tension. A person mid-action or mid-emotion. A callout of a specific situation. An unusual object, scale or sound. On-screen text of ≤7 words naming a tension. Motion in frame 1. Never a logo, greeting or static product. | First frame, first words | 3-s retention or skip rate (where the platform shows it), average watch time |
| **Watch** | "I need to see how this ends" | An open loop with a promised payoff. Visible progression (steps, countdown). Stakes. A reveal held to the end. No dead air longer than 0.7 s. A cut or change every 1 to 2 s in the first 5 s. | Body | Average % watched, completion, retention curve |
| **Share** (mostly sent to one person) | "This is exactly [someone]", "they need this", "look at this" | A relatable situation from real customer life. Utility for a specific other person. Awe or absurdity. Local references. A fair dispute. | Concept | Shares per 1k views |
| **Save** | "I'll need this later" | Reference value (criteria, sizes, steps, price bands, checklist on screen long enough to pause). An upcoming moment. | Body and end card | Saves per 1k views |
| **Comment** | "I have something to say" | A real choice with stakes (A or B, and why). An invitation to share experience rooted in the video. An expertise invitation. A promise that the best questions get a video answer, but only if we really do it. | End and caption | Non-bait comments per 1k views |
| **Message** (convert) | "It's easy and safe to ask" | Trust (real place, real people), specificity, low risk, and a small useful next step: «Напишите «КТ27» — скажем, есть ли в наличии и сколько стоит». | CTA (end, caption, pinned comment) | Coded QC per 1k views |
| **Follow** | "There's more of this" | A series promise (a recurring name or host, "часть 2"). | Series | Follows per 1k views |

### D2. Idea engines (angle generators that work in any industry)

The Russian hooks are illustrations with [placeholders]. Real hooks use only ledger facts.

| # | Engine | Mechanic | Feeds on | Main driver | Example hook (RU) |
|---|---|---|---|---|---|
| 1 | **Вопрос из WhatsApp** | A real recurring question, paraphrased as a chat bubble, answered in ≤25 s by the person who answers it daily | `customer_language`, `friction` | Stop (self-recognition), save, message | «Нам каждую неделю пишут: «[вопрос]». Отвечаем честно.» |
| 2 | **Ошибка до покупки** | The one mistake that costs money, shown happening | `hidden_knowledge`, `tension` | Save, share | «Не покупайте [X], пока не проверите вот это» |
| 3 | **Миф и проверка** | State the belief, test it on camera | `myth` | Watch, comment | «Говорят, [миф]. Проверяем на двух [X]» |
| 4 | **Почему столько стоит** | Real price, then what it pays for, step by step | `price_value` | Watch, share | «Почему [услуга] стоит [цена из базы], а не дешевле — по шагам» |
| 5 | **Испытание** | Stress the product honestly | `proof_asset`, `myth` | Stop, watch | «Выдержит ли [X] [испытание]? Проверяем» |
| 6 | **Процесс целиком** | Start to finish, compressed, with real close sound | `content_reality` | Watch (satisfying) | «Как из [сырья] получается [результат] — за 30 секунд» |
| 7 | **До / после** | The same angle, two states | `content_reality`, `proof_asset` | Stop, share | «Слева — до, справа — после. [N] минут работы» |
| 8 | **Подберите мне** | A budget or situation challenge using real stock | `hidden_knowledge`, `moment` | Save, message | «Собираем [набор] на [сумма] ₸ — что брать, а что нет» |
| 9 | **Честное сравнение** | A vs B with "it depends on you" verdicts. "vs" titles didn't replicate on Shorts, so this is a candidate, not a known winner. | `price_value`, `myth` | Comment, save | «[X] за [цена] и за [цена]: в чём разница на самом деле» |
| 10 | **Эксперт оценивает** | Staff rate customer submissions or popular items | `hidden_knowledge`, `identity` | Comment, share | «Оцениваю ваши [X] из комментариев» |
| 11 | **Угадай** | A guess game with a true reveal (price, sound, which is which) | `content_reality`, `price_value` | Watch, comment | «Угадайте по звуку, какой [X] дороже» |
| 12 | **За кадром / один день** | A real routine with a recurring character | `content_reality`, `identity` | Watch, follow | «6:40 утра. Что происходит, пока город спит» |
| 13 | **Странный заказ** | A real, anonymised, permitted unusual request and the result | `content_reality`, `moment` | Stop, share | «Нам заказали [необычное]. Вот что получилось» |
| 14 | **Момент** | A calendar or situation need, framed practically | `moment` | Save, message | «До [даты] [N] недели. Что реально нужно, а что нет» |
| 15 | **Узнаваемая ситуация (POV)** | A dramatised real customer situation, labelled truthfully | `identity`, `tension` | Share | «POV: вы [типичная ситуация из чатов]» |
| 16 | **Ответ на комментарий** | Turn a real comment into the next video | Any | Comment, follow | «[Цитата комментария] — отвечаем видео» |
| 17 | **Цифры изнутри** | A surprising real business number | `proof_asset` | Stop, share | «За месяц мы [реальная цифра]. Вот что мы поняли» |
| 18 | **Скрытая выгода политики** | Returns, warranty or delivery told as a story | `proof_asset`, `friction` | Message | «Что будет, если [X] не подошёл через [N] дней» |
| 19 | **После покупки** | Use and care, saving the customer money | `hidden_knowledge` | Save | «Как [ухаживать/хранить], чтобы [результат]» |
| 20 | **Урок за 30 секунд** | A micro-skill using the product | `hidden_knowledge` | Save, follow | «[Навык] за 20 секунд — с этого начинают все» |
| 21 | **Ограничение** | A time or money constraint challenge | `content_reality` | Watch | «Успеем [задача] за [N] минут?» |
| 22 | **Трендовая обёртка** | A trend mechanic that carries a real insight (D6) | Any | Stop | Depends on the trend |
| 23 | **Работа изнутри** (hiring) | Honest job realities | `identity` | Share (to job-seekers) | «Как на самом деле выглядит смена [должность]» |

**Fit matrix (insight type to engines to try first):**
- `tension`: 2, 4, 5, 15
- `myth`: 3, 5, 9, 11
- `hidden_knowledge`: 2, 8, 10, 19, 20
- `moment`: 14, 8, 13
- `identity`: 15, 12, 10
- `proof_asset`: 5, 7, 17, 18
- `content_reality`: 6, 7, 11, 12, 21
- `friction`: 1, 18
- `price_value`: 4, 8, 9, 11

### D3. Formats (production containers for one weak phone)

| Code | Format | Audio rule | Staff cost |
|---|---|---|---|
| F-a | Selfie talk, phone ≤40 cm from mouth, quiet corner | Good | Low |
| F-b | Hands demo with close real sound (phone ≤30 cm from the sound source) | Good | Low |
| F-c | Silent B-roll plus a separate voice memo (phone 10 to 20 cm from mouth) | Best | Low |
| F-d | Silent B-roll plus an on-screen text story plus cleared music | n/a | Lowest |
| F-e | Chat or screen recreation (paraphrased bubble) plus an answer clip | Good | Low |
| F-f | Green-screen or stitch over a public review, our product card or our photo | Good | Low |
| F-g | POV walk-through, voice-over recorded later | Best | Low |
| F-h | Before and after: two shots, same angle, phone resting on a surface | n/a | Low |
| F-i | Fixed-phone timelapse or process | n/a | Lowest |
| F-j | AI-visual explainer plus ≥1 real shot for brand link | AI voice-over only if disclosed and not impersonating | 0 to 1 min |
| F-k | Micro-interview, phone held between the speakers, 2 short takes | Good if close | Medium |
| F-l | Reply-to-comment video (F-a or F-b with a comment sticker) | Good | Low |

### D4. Generation algorithm (many diverse ideas from insights, drivers, formats and trends)

1. **Inputs:** the top 6 to 10 insights, the engine fit matrix, feasible formats (permissions plus the walkthrough), 0 to 3 trend candidates that passed D6, the objective's funnel needs, and the pooled arm stats.
2. **Expand:** for each insight, take 3 or 4 fitting engines. For each pair, write a **one-line concept** describing what happens on screen.
3. **Attach:** primary driver, feasible format, funnel role (`attention`, `consideration`, `conversion`, `trust`, `retention`, `recruiting`) and production mode.
4. **Mutate**, which is cheap breadth:
   - swap the person (owner, staff, customer, hands);
   - swap the stakes (cheap item vs expensive);
   - invert (what NOT to buy or do);
   - escalate (1 item to 10);
   - localise (city, weather, holiday);
   - serialise (part 1, 2, 3);
   - flip the point of view (customer vs staff);
   - add a constraint (30 s, a fixed budget);
   - reply (a real comment becomes a video).
5. **Raw pool:** 40 to 60 concepts. Collapse near-duplicates (same insight, engine and format). Keep 24 to 30.
6. **Hooks:** write **3 hooks per kept concept**, each a different hook type. Each hook specifies its first frame, its on-screen text and its first spoken words.
7. **Coverage check** before scoring:
   - ≥5 engines, ≥4 drivers, ≥4 formats, ≥2 production modes;
   - ≥3 funnel roles when the objective is sales;
   - ≥2 wildcards (low prior, high novelty);
   - ≤1 trend-wrapped concept per 5;
   - ≥1 series-able concept for each of the top 3 insights;
   - if YouTube search matters for the vertical, ≥1 search-intent line (plain model or service names, comparisons). Those are a measured long-form prior, a separate content line, not Shorts tactics.

### D5. Hook rules

- Frame 1 shows the subject **in motion** or the **anomaly**. Never a logo, shopfront, greeting or empty product shot.
- On-screen text in frame 1 has ≤7 words, sits inside the safe area, and contains a specific noun or number from the ledger.
- The first spoken line has ≤10 words. Start mid-thought ("Вот почему…", "Это самая частая ошибка…"), not with "Привет, это [бизнес]".
- Call out a situation, not a demographic: «Если вы выбираете [X] впервые…».
- Never ask a question that can lazily be answered "no" («Хотите купить …?»).
- Hook types (rotate them, never repeat one within a weekly slate): callout, contrarian truth, specific number, visual anomaly, in-medias-res, mistake warning, stakes, POV, sound-first.

### D6. Trends without chasing irrelevant ones

- **Sources:**
  - the For You feed of a research account seeded with local and vertical interests;
  - peer outliers from the last 14 days;
  - platform trend lists where they cover the region (for example the Higgsfield trending-music tool, or a platform's creative centre);
  - cross-check that each trend actually appears in RU and KZ feeds.
- **Filter.** All five must pass:
  - (a) the trend's mechanic can carry one of our top insights;
  - (b) it is visible to our audience;
  - (c) we can publish within 72 h;
  - (d) the sound is cleared for business accounts (business accounts are often restricted to commercial sound libraries, so check);
  - (e) there is no brand or ethical risk (nothing mocking groups or customers).
- **Rules:**
  - The trend is the wrapper and the insight is the payload. A trend post that would make sense for any business fails `brand_link`.
  - Trends take ≤20% of the weekly slate. Evergreen insight content is the base.
  - Staff dance or act only if they volunteer. Never pressure a worker.
  - Drop the trend if it can't be published within 72 h.
- **Never spend experiment slots on** posting time or hashtags. Trivial features show about zero signal in our data.

### D7. Producibility (one weak phone, 20 min a week, AI for the rest)

**Hard staff rules (they go on every shoot card):**
- Vertical 9:16. Wipe the lens. Light from a window or from in front. Don't zoom; move closer. Rest the phone on a shelf or box for steady shots. 2 s of lead-in and lead-out per shot.
- Any spoken line: phone ≤40 cm from the mouth, in the quietest spot, with music in the shop off. If the speaker can't be close, record a separate voice memo at 10 to 20 cm and lay it over silent footage.
- When the product's sound is the content (instruments, sizzling, machines, cutting): phone ≤30 cm from the source, and voice isolation or noise suppression off.
- Each shot ≤15 s, 2 or 3 takes. The **last take** is used unless staff mark another. Scripts are ≤2 sentences, and staff may say them in their own words. Staff never memorise.
- No wide shots with dialogue. No two-person dialogue unless the phone is held between the two.
- Staff minutes per shot = `0.5 + takes × (seconds/60 + 0.3)`. Plan ≤16 min a week (80% of 20). The rest is buffer and opportunistic capture.
- **One shoot, many posts:** design every shoot so that each clip is used in ≥2 edits (hook variants, cut-downs, series parts).

**AI does:** scripts, hooks and captions; editing (cuts, punch-ins, pacing, loudness that keeps real dynamics); per-video motion text and graphics; AI explainer visuals (F-j); Kazakh subtitle variants; covers; scheduling and cross-posting; draft replies to comments and WhatsApp messages (staff send them); metrics ingestion and the weekly report.

**AI never does** what C4 rule 7 forbids: fake product footage, fake customers or staff, cloned staff voices without consent, or fake reviews.

### D8. Anti-patterns (each has a deterministic check where possible)

| Anti-pattern | Why it fails | Detection rule | Replace with |
|---|---|---|---|
| Ad-first ("Мы рады…", logo intro, «широкий ассортимент») | Viewers swipe in under 1 s, and it says nothing about them | Business name or logo in the first 2 s. Words like «ассортимент», «качество», «рады» in the hook. | A viewer's tension or a visible anomaly |
| **Price slides** (catalogue photo, price, motion graphics) | The owner judged them useless: they look polished and carry nothing a viewer cares about | Price plus product photo with no person, process, question or story | Engines 4, 8, 9 with real people, sound or a question |
| Childish engagement bait | Cheap, erodes trust, platforms demote it | «поставь лайк», «напиши + », «отметь друга», «подпишись, если…» | A real choice or experience prompt (D1) |
| Fake urgency or scarcity | A truth violation | Urgency lexicon without a ledger end date or stock count | The real reason to act now, if one exists |
| Invented testimonials or AI "customers" | A truth violation | A quote with no review source or consent record | Public reviews (labelled) or consented clips |
| Talking about the business, not the viewer | Nothing to recognise yourself in | "Мы/наш" dominates the first 3 s | "Вы/если вы" plus the situation |
| Generic tips ("5 советов…") with nothing specific | Interchangeable, so no brand link | No ledger fact or local specifics in the body | Engine 2 or 8 with real stock and prices |
| Irrelevant trend-chasing | Views from people who never buy | Fails D6 | An evergreen insight post |
| Mocking customers ("самые глупые вопросы") | Punches down at the people who pay | Contempt lexicon | "The question everyone asks, and it's a good one" |
| More than one CTA, or a CTA in the first 3 s | Kills the watch and confuses the ask | CTA count, CTA timestamp | One CTA at the end, plus caption and pinned comment |
| Wall of text | Unreadable in the feed | >12 words on screen at once | Split into beats |
| Near-duplicate reposts | Platforms may suppress unoriginal or duplicate content | Same first 3 s or caption within 5 days | A hook variant with a different first frame and text (E4) |

---

## E. Idea selection

### E1. Gates (pass or fail, before any scoring)

1. **Truth:** every `facts_used` id is verified and fresh; nothing is implied beyond it. "Needs owner confirmation" means blocked until confirmed.
2. **Producibility:** staff minutes fit the week; the audio rule is met; required people have consented.
3. **Anti-pattern:** passes every D8 check.
4. **Consent and legal:** faces, customers, third-party images, music rights, no named-competitor claims.
5. **Objective link:** has a funnel role, a KPI and a natural next step.
6. **Capacity:** doesn't drive demand the business can't serve.

### E2. Rubric: a prior, not a prediction

Score each criterion 1 to 5. Weights default to `knowledge/rubric_weights.json`: stop 1.5, truth 1.0, share_save 1.3, comment 0.8, producible 1.0, brand_link 0.8, objective_fit 1.4.

`prior = Σ wᵢ·scoreᵢ / Σ wᵢ`

| Criterion | 1 | 3 | 5 |
|---|---|---|---|
| `stop` | Logo, greeting or static product in frame 1 | Clear subject and relevant text, nothing unexpected | A visible anomaly or tension, or a person mid-action, plus ≤7 words a specific viewer recognises as theirs |
| `truth` | Rests on an unverified claim (gate fail) | Needs one owner confirmation (blocked) | Every claim maps to verified, fresh facts |
| `share_save` | Nobody would send or keep it | Generally useful or relatable | An obvious person to send it to, or reference info people will need later |
| `comment` | Nothing to say, or bait | A generic opinion | A real choice or experience with varied answers that we can reply to with a video |
| `producible` | Needs what we don't have | Feasible but ≥6 staff min or tricky audio | ≤3 staff min, close audio, reuses footage, AI does the rest |
| `brand_link` | Any business could post it | Category-specific | Only this business (its people, place, policy, proof) could make it |
| `objective_fit` | Views only | Moves a leading indicator | A direct, natural path to the success metric |

**Authority** comes from calibration records, never from the model's confidence. The current scope:
- Short-form overall: `filter_only`. The prior may drop the bottom 20 to 25% and order the production queue.
- Retail short-form: `none`. The prior is used only for gates, tie-breaks and queue order.
- Long-form YouTube titles: `rank` within the calibrated channel scope.

Also recorded, but outside the prior:
- `novelty`: distance from the last 20 posts by engine, format and hook type.
- `learning_value`: whether the idea tests an open hypothesis or a high-uncertainty arm.
Exploration uses both.

### E3. Diversity rules

- Greedy max-marginal-relevance selection (`smm/brain.py select`). Every repeat of a driver, format or mode within the slate costs value.
- **25% of slots are exploration** (≥1 when the slate has ≥4 slots). They are filled by novelty first, with the prior as tie-break.
- **Caps per weekly slate:**
  - one driver ≤40%;
  - one format ≤35%;
  - one insight ≤2 posts;
  - one engine ≤2 posts;
  - one hook type ≤1.
- **Coverage:**
  - ≥1 idea with people on camera (if consent exists) and ≥1 with no people (robustness);
  - ≥1 conversion-role idea every week of a sales campaign;
  - ≥1 wildcard.

### E4. How many ideas and variants

**Per week, per client** (cross-posted to TikTok, Reels and Shorts by default):
- Generate 24 to 30 concepts. Run the gates (expect 15 to 20 to survive). Score. Select a **slate of 8**: 5 to publish plus 3 in reserve, for blocks, failed shots or fast follow-ups.
- Of the 5 published: about 3 new concepts and about 2 follow-ups. A follow-up is a hook variant, a part 2, or a reply video on a leading arm.

**Per 4-week sprint:** about 20 posts, 12 to 14 distinct concepts, 3 to 5 live **arms** (series or angles).

**Variant types,** cheapest first. They come from the same footage and need no extra filming:
1. **Hook variant:** a different first shot and text over the same body.
2. **Length variant:** 12 to 18 s versus 30 to 45 s.
3. **CTA variant:** code spoken and on screen, versus on screen only.
4. **Language variant:** with or without Kazakh subtitles, or a Kazakh voice if a staff member speaks it and volunteers.
5. **Cover variant** (grid and YouTube).

**Organic variant rules:**
- ≤2 versions of one body per account.
- ≥5 days apart.
- Different first frame, on-screen text and caption.
- Where the platform offers non-follower test distribution (for example Instagram's trial reels for professional accounts, where available), use it for variants.

**Controlled hook tests use paid split tests** (F6): equal budgets and the same audience, so algorithmic luck cancels out. About 1,250 impressions per variant detects a 25% vs 30% 3-second hold rate at 80% power. Cost = 3 × 1,250 impressions at the account's CPM, read from the ads manager, not assumed. Whether paid hook winners transfer to organic is itself an assumption to validate.

### E5. What counts as an arm

- **Within a client,** an arm is a **series or angle** (for example «Вопрос из WhatsApp»). Its posts are observations. The engine allocates the next posts across arms.
- **Across clients,** every post carries **tags**: `driver`, `engine`, `format`, `hook_type`, `people` (face, hands, none), `language`, `length_bucket`, `funnel`, `vertical`, `platform`. Pooled estimates per tag set the priors for new clients' arms (F12).

---

## F. Campaign design

### F1. Anatomy

A campaign is built in this order:
- **Objective** (A), then the **big idea** (one sentence: tension, then truth, then why us);
- **2 or 3 series** (a hero series plus supporting ones), each with a name, a host and a promise;
- a **conversion layer** (WhatsApp codes and handling, plus an offer only if approved);
- an **amplification layer** (boosts of proven winners);
- **measurement and decision rules** (pre-registered);
- the **calendar**, **worker asks**, **AI work list**, the **owner's touchpoints** and the **learning questions**.

### F2. Big idea and series

- **Big idea:** built from the #1 or #2 ranked insight. Test: can it produce ≥10 different videos? If not, it's an idea, not a campaign. The `single_minded_message_ru` is ≤10 words and true.
- **Hero series** (reach and follow): a recurring name and format, ideally a recurring person or hands, publishable 2 or 3 times a week. It takes the most allocation once data supports it.
- **Proof series** (trust and convert): policies, results, process, real numbers. 1 or 2 a week.
- **Utility series** (save): criteria, sizes, care. 1 a week.
- **Reply series** (comment and follow): made from real comments as soon as they exist.

The weekly allocation **across** series is set by the engine (F11), not by the plan. The plan sets only the week-1 split and the floors.

### F3. Offer policy

- The default is **no offer.** A good insight sells without a discount.
- Non-discount offers come first (owner-approved, true): free consultation or selection on WhatsApp, reserve and hold, try in store, a bonus service, delivery terms that already exist.
- A discount is allowed only with owner approval, a real end date, a margin check (`discount ≤ (margin − CPQC_ceiling/close_rate × …)`, worked through with the owner's numbers), and stock confirmed for the window.
- An offer is a **variant**, not a default. Test offer and no-offer CTAs on the same series, because the discount may not be needed.

### F4. Channel roles

| Channel | Role | Metric |
|---|---|---|
| TikTok, Reels, Shorts (the same edit, each platform its own baseline) | Reach to relevant local people, testing ground | Relative views, holds, shares and saves per 1k |
| Profile, bio, Highlights, pinned posts | Bridge: proof plus how to buy | Profile visits, then link taps |
| Stories and WhatsApp Status | Re-reach followers and contacts with winners and proof | Replies, coded messages |
| **WhatsApp Business** | Conversation and close | Coded QC, QC→sale, response time |
| Kaspi (if used) | Transaction | SKU orders in the 72 h after a featured post |
| 2GIS / Google Maps | Local-intent capture and reviews | Rating, new reviews |
| YouTube long-form or search line (optional) | Search demand: plain model or service names, comparisons, beginner guides (a measured long-form prior) | Search views, coded QC |
| Paid boost | Scale proven winners, run controlled hook tests | CPQC, cost per sale |

### F5. WhatsApp conversion layer (most sales here happen in chat)

1. **Codes:** one per post, 4 characters, using letters that look the same in Latin and Cyrillic (A B C E H K M O P T X) plus digits 2 to 9, so «КТ27» typed in Cyrillic matches KT27. Generated by `smm/attribution.py`. The code is **spoken**, **on screen** for ≥2 s, in the **caption** and in the **pinned comment**, so it survives forwards.
2. **Links:** a `wa.me` link with the code pre-filled wherever links are clickable (Stories link sticker, YouTube description, ads). The bio link uses a generic code («БИО»).
3. **CTA wording** (one, at the end, truthful): «Напишите в WhatsApp «КТ27» — подскажем, есть ли в наличии и сколько стоит». Never «успейте».
4. **Admin kit,** drafted in Russian by the agent and approved by the owner. These are WhatsApp Business quick replies:
   - a greeting;
   - a reply to a coded message (answer plus one question that moves toward a sale);
   - «Подскажите, из какого видео вы нас нашли?» for codeless chats;
   - the review request at handover.
5. **Labels:** «Видео» (coded), «QC», «Оплачен». Staff cost is ≤2 minutes a week, because labelling replaces note-taking.
6. **QC definition:** the chat names a product or service and asks about price, availability, booking or delivery, or gives a date or need. These do not count: spam, wrong numbers, job seekers (except in hiring campaigns), and suppliers.
7. **Response-time guardrail:** if the median first response in working hours is >15 min, flag it to the owner as the top leak, with the number, before asking for more content.
8. **Attribution windows:** a code counts toward its post for 30 days. Primary reads happen at +7 d.

### F6. Paid boost (amplify only what organic has proven)

- **Ceiling first:** `CPQC_ceiling = avg_order × gross_margin × close_rate × spend_share`. `spend_share` defaults to 0.3 unless the owner sets it. Cost-per-sale ceiling = `CPQC_ceiling / close_rate`.
- **Eligibility.** All three must hold:
  - relative views ≥2× at +48 h, or retention in the account's top quartile;
  - shares plus saves per 1k ≥ the account median;
  - ≥1 coded QC, or a conversion-role idea.
  Never boost a post that only got views without engagement quality.
- **Setup:**
  - local radius around the business (or service geography);
  - broad age range unless the product requires otherwise;
  - an objective that drives messages where available (for example click-to-WhatsApp on Meta), otherwise profile visits;
  - the code stays in the creative.
  - If paid ads run in Kazakhstan, check the language requirements for advertising with the owner; a Kazakh version may be needed.
- **Stop-loss** (pre-registered):
  - After spend = 5× `CPQC_ceiling`: ≥5 QC means continue and scale budget +50% per step; 3 or 4 QC means extend once to 8×; ≤2 QC means stop.
  - Stop or refresh when CPQC rises for 3 days, or frequency is >3.
- **Approval:** the budget cap is approved by the owner; each boost is proposed in the weekly message with its stop-loss in ₸.

### F7. Calendar (4-week sprint by default)

| Week | Goal | Allocation | Key actions |
|---|---|---|---|
| 0 (2 to 4 days) | Set up | No posts, or 1 or 2 baseline posts | Onboarding pack, codes, labels, quick replies, baseline snapshot, week-1 shoot card |
| 1 | Explore | 1 post per arm plus 1 wildcard (about 5) | Maximum diversity. Measure response time. |
| 2 | Explore and first read | Floor of 1 per arm, extra slots by Thompson | Breakout follow-ups within 72 h. Ask the deferred boost question with data. |
| 3 | Exploit | Thompson with floors. Retire losers (F11). | First boost if eligible. Reply videos. |
| 4 | Scale and harvest | Thompson. Offer variant if approved. | Sprint retro. Learning records. Next sprint's arms. |

Cadence: 5 posts a week. Posting times come from account analytics when available. Don't test posting times.

### F8. Worker asks (≤20 min a week, one batched card)

- **One weekly shoot card** in Russian, ≤8 shots, ≤16 planned minutes. Each shot has: what, where, how close, seconds, takes, what to say (≤2 sentences, own words allowed) and a "done" check. The rest is buffer and moment capture (B3, input 10).
- **Moment capture** is opportunistic and is never counted as an obligation.
- **WhatsApp labelling** takes ≤2 minutes a week.
- Nothing else is asked of workers. If an idea needs more, it fails the producibility gate.

### F9. AI work list (per week)

Concept and hook generation; edits plus 2 or 3 hook variants per concept; motion text; F-j explainers; captions, pinned comments and codes; Kazakh subtitle variants; cross-posting; comment and DM reply drafts; metric ingestion; engine update; weekly owner message; next week's shoot card.

### F10. Measurement

**Metric tree:**

```
Business outcome (orders / applications / bookings)
 └─ QC → sale rate (chat quality, response time)
     └─ Coded QC  (= views × QC per 1k views)
         ├─ Views (distribution)            ← stop + watch + share
         │   ├─ 3-s hold / skip rate        (hook)
         │   ├─ avg % watched, completion   (body)
         │   └─ shares, saves per 1k        (concept value)
         └─ QC per 1k views                 (CTA, offer, trust, relevance)
```

- **Engine outcome per post:** `y = ln(views_48h / baseline)`. The baseline is the median of the last 15 posts on the same platform, recomputed weekly. For new accounts, use a running median from post 1 and the vertical prior until n = 10.
- **Quality:** shares plus saves per 1k views. Comments per 1k, excluding our own and bait.
- **Objective:** coded QC per 1k views, QC→sale, sales.
- **Windows:** +48 h for the engine and early decisions, +7 d for QC and quality, 30 d for code attribution.
- **Incrementality:** weekly total inbound WhatsApp versus the pre-campaign baseline (4 weeks before, adjusted for known seasonality). `codeless_lift = total − baseline − coded`. Report coded QC as a floor and codeless lift as an estimate. For boosts, alternate boost-on and boost-off weeks when the owner accepts that.
- **Velocity KPIs** (for the agent itself): posts shipped against plan, idea-to-post time (target ≤72 h), share of posts with a working code, and decisions made per sprint.

### F11. Decision rules (pre-registered and applied automatically)

| Situation | Rule |
|---|---|
| Next week's slots | Thompson sampling on each arm's posterior of `y`. Floor of 1 post per live arm per week. 25% exploration. ≤50% of slots to one arm. |
| Sales objective with ≥20 coded QC in total | Allocate on expected QC per post (posterior views × posterior QC rate) instead of `y` alone |
| Post ≥3× baseline at +48 h ("breakout") | Within 72 h: a part 2 or hook variant on the same insight, reply videos to the top 2 comments, the code pinned. Check boost eligibility. |
| Post ≤0.3× baseline and hold below the account's p25 | Retire that hook. The body may be reused once with a new hook if its insight is top-3. |
| Arm `P(best) < 0.05` after ≥8 posts | Retire the arm and free its slots for exploration |
| Arm with ≥10k cumulative views and 0 QC while other arms convert | Re-role it to attention-only, capped at 1 post a week |
| No arm separates after 4 weeks | Expected at small n. Keep allocating, don't declare winners, and add the arm tags to the cross-client pool. |
| Total inbound not above baseline by week 3 | Funnel diagnosis before more content: response time, CTA visibility, code use rate, offer, stock |
| "Winner" claims (reports, learning records) | Only with `P(best) ≥ 0.9` and n ≥15 per contender, or pooled n ≥30 per arm. Otherwise say "leading", with the interval. |
| Boost | F6 stop-loss and scale rules |

Power note: about 30 posts per arm are needed for 80% power to detect a 2× effect. One client at 5 posts a week cannot "prove" anything in a sprint. Per-client decisions are therefore **allocation** decisions (where to put the next posts). **Knowledge** decisions come from pooling (F12) and paid split tests.

### F12. Learning loop

**Weekly** (automated, Monday):
1. Ingest the +48 h and +7 d metrics and the code counts.
2. Update the posteriors.
3. Apply F11.
4. Generate new concepts: mutations of leaders (D4 step 4) plus fresh exploration.
5. Select the slate (E).
6. Build the shoot card.
7. Send the owner message.

**Owner message** (≤5 minutes to read and answer), RU template:

> «Неделя [N]. Вышло [5] роликов. Лучший — «[название]»: [X] просмотров (в [k] раз выше обычного), [m] сообщений с кодом [КОД], [s] заказов. Не сработало: «[название]» — убираем этот формат. На этой неделе: [3 темы]. Съёмка — [16] минут, карточка у сотрудника. Вопрос: продвигаем лучший ролик на [бюджет] ₸? Остановим, если за первые [стоп-лосс] ₸ будет меньше [3] обращений. Ответьте «ДА» или «НЕТ».»

**Sprint retro** (every 4 weeks):
- Re-rank insights by realised QC (C3).
- Write learning records (G9) with strength labels.
- Propose the next sprint's arms: keep the leaders, add 1 or 2 new arms from untested engines or insights.
- Refit the rubric weights **only** when ≥30 posts per arm exist for the scope, and record the calibration (Spearman with CI) before changing the judge's authority.

**Across clients:**
- **Pooled tag estimates:** hierarchical shrinkage of `y` (and QC rate) per tag (engine, format, hook_type, people, language, length_bucket) at vertical and global level. A new client's arm `prior_mean` = the pooled estimate for its tags, used only if that tag has ≥30 observations at that level, otherwise 0. The prior SD stays wide.
- **Shared experiment each sprint:** pick one binary factor, for example face in frame 1 vs hands only, code spoken vs on-screen only, or Kazakh subtitles vs none. Every client randomises it per post with a coin flip, balanced within the client. Ten clients at 5 posts a week over 4 weeks gives about 200 observations, enough for factor effects no single client could ever detect.
- **Rule:** never transfer a finding beyond its label (`measured`, `measured (correlational)`, `expert judgment`, `hypothesis`) or beyond its scope (vertical, platform, format, long-form vs short-form).

---

## G. Output contract

Field names follow `smm/brain.py`. **(+)** marks a field to add. Every object carries `client`, `run_id`, `created_at` and `method_version`.

### G1. IntakeBrief

```yaml
IntakeBrief:
  request_verbatim: str (+)            # unedited boss words
  request_type: enum                   # sales_push|launch_or_event|awareness_or_viral|reputation_or_trust|
                                       # price_pressure|retention_or_loyalty|hiring|b2b_leads|should_we_do_social|other
  secondary_types: [enum] (+)
  reframed_request: str                # one sentence, English
  business_objective: str              # object + direction + date
  marketing_objective: str             # who (situation + place) does what (observable action)
  success_metric: {name, how_measured, baseline (+), target, by_when}
  leading_indicators: [str]            # 3–5 from F10
  guardrails: [{metric, limit}] (+)
  capacity: {unit, free_per_week, source, confidence} (+)
  constraints: [str]
  feasibility: (+)
    {req_qc, req_views, ach_views, ratio, verdict: feasible|stretch|unrealistic, assumption_ids: [str]}
  assumptions: [{id, text, confidence: likely|assumption, verify_how, verify_by, default}]   # (+ object form)
  clarifying_questions: [{q_ru, why, default_if_no_answer, deadline}]   # max 3
  deferred_questions: [{q_ru, ask_when}] (+)
  push_back: str                       # "" if none; plain, specific
  approvals: {content: explicit|silent_24h, offers: owner, spend: owner, new_faces: owner} (+)
  owner_message_ru: str (+)
```

### G2. InputChecklist

```yaml
InputChecklist:
  have: [{input, what_it_gives, as_of (+), evidence_ids (+)}]
  missing: [{input, why_it_matters, how, who: agent|owner|staff|customer,
             owner_minutes, staff_minutes (+), fallback_if_missing, blocks_step}]
  owner_ask_batch_ru: str (+)          # the single B4-style message
  total_owner_minutes: number (+)      # must be ≤30 at onboarding, ≤5 weekly
```

### G3. EvidenceBase

```yaml
EvidenceItem:
  id: str                              # E###
  kind: fact|customer_language|behaviour|proof_asset|moment|constraint|market|performance
  claim: str
  verbatim_ru: str (+)                 # de-identified; "" if n/a
  count: str (+)                       # e.g. "11/18 chats"
  source: str                          # URL / file / "owner voice note DD.MM"
  as_of: date (+)
  expires: date|null (+)
  confidence: verified|likely|assumption
  audience_usable: bool (+)
  fact_id: str|null (+)                # facts-ledger id if publishable
```

### G4. InsightList

```yaml
Insight:
  id: str                              # I##
  type: tension|myth|hidden_knowledge|moment|identity|proof_asset|content_reality|friction|price_value (+)
  insight: str                         # C2 statement format
  who_feels_it: str
  moment: str (+)
  tension: str
  truth_we_can_show: str (+)
  evidence_ids: [str]
  proof_ids: [str] (+)
  content_reality: str                 # what the camera sees
  objective_link: str (+)
  scores: {frequency, intensity, objective, showability, ownability, proof, freshness} (+)   # 1–5
  strength: int                        # weighted composite rounded 1–5
  status: verified|hypothesis (+)
```

### G5. IdeaList

```yaml
Idea:
  id: str; title: str; insight_ids: [str]
  engine: str (+)                      # D2 number+name
  driver: str; format: str             # D3 code
  funnel: attention|consideration|conversion|trust|retention|recruiting
  hook_ru: str                         # the primary hook (= hooks[0])
  hooks: [{type, first_frame, on_screen_ru, say_ru}] (+)   # exactly 3, different types
  first_frame: str; on_screen_ru: [str]; what_happens: str
  why_stop: str; why_share_or_save: str
  comment_prompt_ru: str; cta_ru: str  # cta includes {code} placeholder
  length_s: int (+)
  production:
    mode: worker|ai|mixed|ugc|screen
    worker_shots: [{what_ru, location, seconds, takes, say_ru, kind: hook|demo|talk|detail|process, distance_cm (+)}]
    ai_parts: str
    people_on_camera: int
    reuses_media_ids: [str] (+)
  staff_minutes: number (+)            # D7 formula
  facts_used: [str]                    # ledger ids, every number/claim
  kpi: str
  risks: [str]
  gates: {truth, producible, anti_pattern, consent, objective, capacity: pass|fail|blocked} (+)
  needs_facts: [str] (+)               # → batched owner question
  rubric: {stop, truth, share_save, comment, producible, brand_link, objective_fit}   # 1–5
  prior: number (+)
  novelty: number (+); learning_value: str (+)
  tags: {driver, engine, format, hook_type, people, language, length_bucket, funnel, vertical} (+)
  arm_id: str (+)
  wa_code: str (+)                     # assigned at publish
```

### G6. Slate (selection)

```yaml
Slate:
  slate: [{id, prior, value, why: prior+data|explore, staff_min, needs_facts}]
  blocked: [{id, reason}]
  week_filmed: [id]; week_minutes: number   # ≤16
  coverage: {drivers, formats, engines, funnel, modes, people_mix} (+)
  note: "prior = weighted rubric; audience data overrides it as posts accumulate"
```

### G7. TestPlan (+)

```yaml
TestPlan:
  hypotheses: [{id, statement, metric, decision_rule, preregistered_at}]
  arms: [{arm_id, name, tags, prior_mean, prior_sd, prior_source: vertical|global|none, idea_queue: [id], status: live|leading|retired}]
  allocation: {method: thompson, floor_per_arm_week: 1, explore_share: 0.25, max_share_per_arm: 0.5,
               switch_to_qc_allocation_at: 20}
  variants: [{idea_id, type: hook|length|cta|language|cover, differs_in, route: organic|trial|paid_split, earliest_date}]
  metrics: {engine: "ln(views_48h/baseline)", quality: [shares_per_1k, saves_per_1k],
            objective: [qc_per_1k_views, qc_to_sale], hook: [hold_3s_or_skip]}
  baselines: {platform: {median_views, n_posts, as_of}}
  windows: {engine: 48h, quality: 7d, code_attribution: 30d}
  decision_rules: [str]                # F11 rows, with numbers
  power_note: str                      # what can and cannot be concluded at planned n
  shared_experiment: {factor, levels, randomisation: per_post_coin, balance: within_client}
  boost_plan: {eligibility, cpqc_ceiling, budget_cap, stop_loss, scale_rule, needs_approval: true}
```

### G8. Campaign and ShootCard

```yaml
Campaign:
  name; big_idea; single_minded_message_ru; why_this_wins
  series: [{name, role, idea_ids, cadence, host (+), promise_ru (+)}]
  offer: {needed, proposal, fact_ids, needs_owner_approval, end_date (+), margin_check (+)}
  channels: [{channel, role, metric (+)}]
  whatsapp: {code_scheme, greeting_ru, quick_replies_ru: [str], labels: [str], qc_definition,
             response_sla_min, baseline_inbound_per_week} (+)
  boost: <TestPlan.boost_plan> (+)
  weeks: [{week, goal, idea_ids, posts (+), worker_ask_ru, ai_work}]
  measurement: {success_metric, attribution, leading_indicators, review_cadence, baseline (+), windows (+)}
  decision_rules: [str]
  learning_questions: [str]            # what this sprint must teach us
  owner_asks: [{ask, why, minutes}]
  risks: [str]

ShootCard:   (+)
  week; total_minutes                  # ≤16 planned
  rules_ru: [str]                      # D7 rules, short
  shots: [{n, what_ru, where, distance_ru, seconds, takes, say_ru, done_check_ru}]
  moment_list_ru: [str]
```

### G9. WeeklyReview and LearningRecord

```yaml
WeeklyReview:   (+)
  week; posts: [{idea_id, platform, code, views_48h, rel_views, hold, shares_1k, saves_1k, qc, sales}]
  arm_posteriors: [{arm_id, n, mean, sd, p_best}]
  decisions: [{rule, applied_to, action}]
  funnel: {inbound_total, baseline, coded, codeless_lift, median_response_min, qc_to_sale}
  owner_message_ru: str

LearningRecord:                        # appended to knowledge/learnings.jsonl
  id; vertical; finding; use; source; date
  strength: measured|measured (correlational)|expert judgment|hypothesis
  tags (+); n (+); effect (+); ci (+); scope (+)   # platform, format, short/long
```

---

## H. Worked mini-example (hypothetical business; every client fact is an assumption)

> **Label.** «Кондитерская «Пример»» is invented. Facts A1 to A9 are **assumptions for illustration**. In a real run, each would be an evidence item with source and date. Hooks with numbers would ship only after ledger verification.

**Assumed client.**
- A1: one custom-cake bakery in Astana; 4 people (2 confectioners, 1 admin who runs WhatsApp, the owner).
- A2: custom cakes ordered 2+ days ahead, plus a showcase of pastries and cakes sold by the slice.
- A3: average custom order 18,000 ₸; gross margin 50%.
- A4: capacity 12 custom cakes a day. About 5 a day are booked Monday to Thursday; weekends are full.
- A5: Instagram Reels median of 900 views over the last 15 posts; no TikTok.
- A6: about 9 new WhatsApp inquiries a day; the admin estimates 40% become orders.
- A7: the confectioners agree to show hands only; the admin agrees to appear on camera.
- A8: no discounts. The owner would allow a free inscription or topper as a bonus (to be confirmed).
- A9: boost budget unknown.

### H1. Intake

- **Verbatim:** «Сделайте нас вирусными в ТикТоке, как у [конкурент]».
- **Type:** `awareness_or_viral` (primary), with an implicit `sales_push`.
- **Capacity finding:** weekends are full (A4), so viral weekend demand would be wasted. Free capacity is about 7 cakes a day Monday to Thursday, about 28 a week.
- **Business objective:** +30 custom-cake orders over the 4 weeks, picked up Monday to Thursday.
- **Marketing objective:** people in Astana with a weekday occasion in the next 2 to 14 days message us with a code and choose a weekday date. Occasions include colleagues' birthdays at the office and kids' birthdays at school or kindergarten. This last part is a hypothesis to test.
- **Success metric:** coded WhatsApp chats labelled «Оплачен» with a weekday pickup. Baseline 0 (codes are new). Target 30. By the end of week 4.
- **Feasibility (A3):**
  - `req_QC` = 30 / 0.4 = **75**.
  - With a labelled planning range of 0.5 to 1.5 QC per 1k views, `req_views` = 50k to 150k.
  - `ach_views` = 20 posts × 900 × 1.8 ≈ 32k.
  - The ratio is 1.6 to 4.7, so the verdict is **stretch to unrealistic organically.**
- **Push-back** (RU, to the owner): «Органикой 30 заказов за месяц — только если 1–2 ролика «выстрелят». Надёжнее: 4 недели органики + продвижение роликов, которые сработали. Расчёт покажем на второй неделе на реальных цифрах.»
- **Guardrails:** don't drive Saturday or Sunday demand (the CTA says «на будни»); staff ≤20 min a week; rating doesn't fall; median response ≤15 min.
- **Questions (2 of 3):**
  - Q2: «Можно ли давать бесплатную надпись или топпер к заказу на будни? Без ответа — без бонусов.»
  - Q3 is answered by A7, so it isn't asked.
  - Deferred: the boost budget, until week 2 when there is data.

### H2. Inputs

- **Automated:** Instagram posts and comments (the baseline), 2GIS reviews (owner screenshots if the page is blocked), and peer bakery outliers in RU.
- **Owner:** 15 chat exports (5 min), the voice note (10 min), baseline numbers (5 min), and 40 cake photos from the confectioner's phone (5 min). Total 25 min.
- **Staff:** a 2-minute walkthrough.

### H3. Evidence (hypothetical)

| id | kind | claim | conf. |
|---|---|---|---|
| E1 | customer_language | «Можно как на фото, но без мастики?» in 9 of 15 chats | likely |
| E2 | customer_language | «Сколько стоит за кило?» in 12 of 15 chats | likely |
| E3 | tension | «А точно будет похоже?» in 6 of 15 | likely |
| E4 | proof_asset | The confectioner photographs every cake before handover (about 300 photos) | likely |
| E5 | behaviour | Saturday slots fill by Wednesday; most orders come 1 to 3 days ahead | likely |
| E6 | customer_language | Reviews: «не приторный», «очень нежный» (several); complaint «дорого» | likely |
| E7 | constraint | Median first response 22 min during working hours | likely |
| E8 | performance | The account's top 3 Reels were all cross-section cuts | likely |
| E9 | market | Peer outliers: "заказ → результат" mechanics | likely (hypothesis) |

**E7 triggers F5 rule 7.** The owner hears first that a 22-minute reply time leaks orders. Quick replies are drafted before any content goes out.

### H4. Insights (ranked)

- **I1 (`tension`)**, from E1, E3 and E4. People order from a picture and fear it won't look like that. We have about 300 real result photos. The camera sees the order text (paraphrased), then the real cake.
- **I2 (`content_reality`)**, from E8. The cross-section cut and cream smoothing are inherently watchable, with real knife sound close to the phone.
- **I3 (`moment`, hypothesis)**, from A4 and E5. Weekday occasions such as office and school birthdays are under-served, and weekday slots are free. It moves the objective directly.
- **I4 (`price_value`)**, from E2 and E6. «Дорого» against what is inside. This needs owner-confirmed ingredient and labour facts before any number appears.
- **I5 (`hidden_knowledge`)**, from E2. How much cake for N guests is save-worthy. It needs the owner's rule, verified as a fact.

### H5. Ideas (12 of 26 generated, after gates)

| id | Engine / format | Insight | Funnel | Hook (RU) | Staff min | Prior |
|---|---|---|---|---|---|---|
| X1 | 13 Странный заказ / F-e + photo | I1 | consideration | «Заказ: «папа рыбак, но без рыбы». Вот что мы сделали» | 0 (photos) | 3.9 |
| X2 | 6 Процесс / F-b | I2 | attention | Frame 1: the knife entering, with sound. Text: «Разрез, ради которого его заказывают» | 2.0 | 3.8 |
| X3 | 1 Вопрос из WhatsApp / F-a admin | I1 | conversion | «Нам каждый день пишут: «А будет как на фото?» Честно отвечаю» | 1.6 | 3.7 |
| X4 | 14 Момент / F-c | I3 | conversion | «День рождения коллеги во вторник? Торт можно заказать сегодня» (only if lead-time A2 is verified) | 1.2 | 3.6 |
| X5 | 7 До / после / F-h | I2 | attention | «Голые коржи → готовый торт. 3 часа за 20 секунд» (only if the time is verified) | 2.2 | 3.5 |
| X6 | 8 Подберите мне / F-a | I5 | consideration | «Сколько торта нужно на 10 человек — чтобы не переплатить» | 1.6 | 3.4 |
| X7 | 11 Угадай / F-b | I4 | attention | «Угадайте, сколько весит этот торт» (real weight revealed) | 1.4 | 3.2 |
| X8 | 15 POV / F-d | I3 | attention | «POV: вспомнили про день рождения коллеги в 23:40» | 0.8 | 3.1 |
| X9 | 4 Почему столько стоит / F-c | I4 | trust | «Из чего на самом деле складывается цена торта» (blocked: needs owner facts) | 1.8 | — |
| X10 | 12 За кадром / F-i | I2 | attention | «7:00. Кондитерская, пока никого нет» (timelapse) | 0.7 | 3.0 |
| X11 | 16 Ответ на комментарий / F-l | any | retention | Made from week-1 comments | 1.5 | — |
| X12 | 22 Trend wrapper (cleared sound, "expectation vs reality" mechanic carrying I1) | I1 | attention | «Ожидание / реальность — только у нас реальность лучше» (proof: the real photo) | 0.5 | 2.9 |

X9 is blocked by the truth gate and becomes an owner question. X11 waits for comments.

### H6. Week-1 slate and arms

**Arms:**
- **A «Заказ → результат»:** X1, X12 later.
- **B «Звук и разрез»:** X2, X5, X10.
- **C «Вопрос из WhatsApp»:** X3, X6.
- **D «Торт в будни»:** X4, X8 (the I3 hypothesis).
- **Exploration:** X7.

Week 1 publishes **X1, X2, X3, X4, X7**, cross-posted to IG Reels, a new TikTok account and Shorts. The reserve is X5, X8 and X10. Each post gets a code. X1, for example, gets «КТ27». Coverage: 5 engines, 4 formats, 3 funnel roles, faces and no faces.

### H7. Shoot card, week 1 (16.4 planned min)

> **Правила:** телефон вертикально, протрите камеру, свет от окна. Не приближайте зумом — подойдите ближе. Говорите, держа телефон не дальше 40 см. Звук ножа — телефон в 30 см. Каждый кадр 2–3 дубля, берём последний.
> 1. **Разрез** (X2): торт с витрины, который всё равно режут на куски. Телефон на коробке, 30 см. Медленный разрез и показать срез. 12 с × 3 дубля.
> 2. **Выравнивание крема** (X2, X5): руки крупно, звук шпателя. 15 с × 2.
> 3. **Коржи → готовый торт** (X5): тот же угол, телефон не двигать. 2 кадра по 8 с, в начале и в конце сборки.
> 4. **Ответ администратора** (X3): селфи у окна, 35 см. «Нам часто пишут: «будет как на фото?» — да, если…». Своими словами, 20 с × 3.
> 5. **Сколько торта на гостей** (X6): то же место. Правило от владельца на карточке. 20 с × 2.
> 6. **Упаковка торта в коробку** (X4): руки, 10 с × 2. Голос запишем отдельно: голосовое 10 с, телефон у рта.
> 7. **Взвешивание** (X7): торт на весах, крупно цифры. 8 с × 2.
>
> **Если увидите — снимите 10 секунд:** клиент открывает коробку; необычный заказ; утренняя загрузка печи.
> **WhatsApp:** ставьте ярлык «Видео» на сообщения с кодом и «Оплачен» после оплаты.

### H8. Test plan and decisions (pre-registered)

- **Hypotheses:**
  - H1: arm D (weekday moment) yields more coded QC per 1k views than arms A, B and C. This is the objective-critical one.
  - H2: arm B gets the highest relative views, but a low QC rate. If so, it becomes the attention role.
- **Shared cross-client factor this sprint:** hands vs face in frame 1, randomised per post.
- **Ceiling:**
  - `CPQC_ceiling` = 18,000 × 0.5 × 0.4 × 0.3 = **1,080 ₸**.
  - Cost per order ceiling = 2,700 ₸.
  - Boost stop-loss = 5 × 1,080 = **5,400 ₸** of evaluation spend.
- **Decision rules:**
  - Thompson from week 2, with a floor of 1 post per arm.
  - Breakout ≥3× (≥2,700 views at +48 h) means a part 2 within 72 h.
  - Arm D with 0 QC after 8 posts and ≥5k views means drop the I3 hypothesis.
  - Boost proposals are shown with numbers in ₸.
- **Power note:** about 5 posts per arm in 4 weeks gives allocation signal only. No "winner" claims. Tags go to the food-vertical pool.

### H9. Calendar and owner touchpoints

- **Week 0:** quick replies plus the response-time fix (E7), labels, codes.
- **Weeks 1 and 2:** explore.
- **End of week 2:** owner message with the best post's numbers and a boost proposal, for example «продвигаем «КТ27» на 15 000 ₸ на 5 дней в радиусе 5 км; стоп, если за первые 5 400 ₸ меньше 3 обращений». This is also where the X9 price facts get asked.
- **Week 3:** exploit plus a boost if approved; reply videos.
- **Week 4:** the weekday bonus variant (topper), only if Q2 was answered yes; sprint retro; learning records, for example the finding "weekday-moment framing vs process content on coded QC" (strength `hypothesis` until pooled n ≥30).

Owner time for the whole sprint: 25 min at onboarding plus about 4 × 5 min weekly, about 45 min in total. Staff time: ≤20 min a week, including labels.