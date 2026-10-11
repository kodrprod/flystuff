# Method: turning any boss request into ideas and a measurable short-video campaign

*For the MetaPrompt autonomous marketing agent. Scope: any local business in Kazakhstan or the wider CIS, and any request from its boss. It covers intake, inputs, evidence, insights, ideas, selection and campaign. Execution tools (AI video, editing, publishing, the experiment engine) consume the objects defined in section G.*

---

## 0. Operating principles (apply at every step)

1. **Start from a business number, not from content.** Every request ends in something the business can count each week: orders, coded WhatsApp chats, bookings, applicants, reviews, or units of a named SKU.
2. **Nobody can predict short-form winners from text, and that includes you.**
   - A blind text judge got Spearman 0.44 on long-form YouTube titles.
   - On Shorts it got 0.11, and 0.07 for retail, where the CI includes 0 (n = 1,172).
   - Title tricks that won on long-form ("для начинающих", "vs") did not replicate on Shorts.
   - So scores are priors only. Your job is to produce many strong, diverse, cheap shots on goal, built on real insight. The audience picks the winners, and the experiment engine scales them.
3. **Truth is a gate, not a score.**
   - Every price, number, stock level, deadline, superlative, comparison, guarantee or testimonial that reaches the audience must cite a sourced fact.
   - If a fact is unknown, it becomes a question to the owner. Never guess, and never quietly "fix" a claim.
4. **Raw material beats opinions.** Never ask the owner "кто ваша ЦА?" or "какое у вас УТП?". Get the WhatsApp export, the reviews and the camera roll, and derive the answers from them.
5. **Make content for strangers, not ads for the owner.** A video must give something (a laugh, an answer, a sight, a sound, a feeling) to a person who will never buy.
6. **Production reality is a design input, not an afterthought:**
   - one weak phone, with good audio only when it is held close;
   - shy staff;
   - 20 staff minutes and 5 owner minutes a week.
   An idea that ignores this is a bad idea.
7. **Sales happen in WhatsApp and on Kaspi.**
   - Every conversion-relevant video carries a per-video WhatsApp code.
   - The WhatsApp reply is part of the campaign.
   - Content cannot fix a 3-hour reply time.
8. **Learning is pooled across clients.** One shop posting 5 videos a week cannot reach statistical power alone (about 30 posts per arm are needed for 80% power on a 2× effect).
9. **Nothing goes outward without owner approval.** Do not publish, contact customers, spend money or credits, or post comment replies without an explicit human decision. Approval is bound to the exact file and caption.
10. **Write every assumption down**, with what breaks if it is wrong and how it will be verified.

| Who | Budget | Hard rule |
|---|---|---|
| Owner | ≤15 min onboarding, ≤5 min/week | One bundled message per week. Every question has a default. |
| Staff | ≤20 min/week, including setup and retakes | The shoot card is cut to fit by the optimiser. Face-free by default. |
| Agent | Any amount of analysis | Zero unapproved outward actions. |
| First approved batch | ≤5 working days from request | Provisional insights come from public data and are refined when owner inputs arrive. |

**Language.** Internal objects are in English. Everything a viewer, owner or staff member reads is in Russian, with Kazakh variants where D7 says so.

---

## A. Request intake

### A1. Capture and classify

- **Store the request verbatim**, with the sender, channel and date. Transcribe voice notes and keep the transcript.
- **Classify it as exactly one `request_type`:** `sales_push`, `launch_or_event`, `awareness_or_viral`, `reputation_or_trust`, `price_pressure`, `retention_or_loyalty`, `hiring`, `b2b_leads`, `should_we_do_social`, `other`.
- **Split compound requests.** For example, «хотим вирусность и продать остатки до Нового года» contains two requests.
  - The one with a date and money becomes primary.
  - The other becomes a secondary objective or goes to the backlog.
  - One campaign has one primary metric.

### A2. The "so that what?" ladder

Ask yourself (not the owner) "so that what?" until you reach a number the business can count weekly:
- orders or revenue;
- units of named SKUs;
- coded chats or inquiries;
- bookings or visits;
- applicants or hires;
- reviews or rating;
- repeat orders;
- event attendance.

Stop at the first such number. Record the ladder.

| Request | Ladder | Business number |
|---|---|---|
| «Сделайте нас вирусными» | known → more people write or come → more sales | new-customer coded chats per week |
| «Хотим TikTok как у конкурентов» | not lose customers to them → keep the inquiry flow | coded chats, plus the share of chats that mention the video |
| «Продайте X до 31-го» | stock turns into cash by a date | units of X sold by date (Kaspi/POS), coded chats about X |
| «Найдите нам продавца» | store staffed by a date | qualified applicants (passing a 3-question screen) by date |
| «Поднимите отзывы» | people choosing on 2GIS/Kaspi pick us | new reviews per week, rating |
| «Конкуренты дешевле» | keep conversion without cutting price | chat-to-sale rate, average check |

### A3. Bottleneck diagnosis

Locate where the business leaks before you design anything. Use evidence from B; while it is missing, state the bottleneck as a hypothesis.

| Stage | Signals in the inputs | What content must do |
|---|---|---|
| Awareness | Low reach and profile visits. Reviews say «случайно нашли». Few chats, but chats convert well. | Stop- and share-led engines; local search words; reach to non-followers. |
| Consideration | People know the business but ask the same doubts. Chats stall after the price. Reviews say «боялась, что…» before the praise. | Proof and answer engines that resolve the specific doubt. |
| Conversion | Many chats, few sales. Slow replies. No clear next step. Chats die after the price is sent with no explanation. | Mainly the WhatsApp layer (reply scripts, response time, next step). Offer only if approved. Content alone will not fix it. |
| Retention | One-time buyers; no repeat or referral. | WhatsApp Status, care and how-to content, follow-up scripts. |
| Non-marketing | Stock-outs, quality complaints, price far above market for the same SKU on Kaspi, wrong hours, no one answering. | Say so plainly in `push_back`. Propose the fix (or hand it to the owner). Do not amplify a broken experience. |

### A4. Objectives, metric, target

- **`business_objective`:** number + unit + date, e.g. "+60% coded chats from new contacts per week by week 6".
- **`marketing_objective`:** who (a buying situation, not demographics) moves from what belief or behaviour to what belief or behaviour. Example: «родители, чей ребёнок щурится» move from «откладываю, боюсь, что разведут» to «пишу в WhatsApp, чтобы записаться».
- **`success_metric`:** one primary metric that we can measure without extra owner effort beyond the weekly export. It has a baseline, a target, a date and a method.
- **`leading_indicators`:** 2–4 per-post signals we can read within 48 h.
- **`guardrails`:** things that must not get worse (rating, owner minutes, staff card completion, approval rate).
- **`stretch`:** an optional upside such as "≥1 post at ≥5× account median", always labelled "plausible, not guaranteed".

Defaults by request type:

| request_type | Default business objective | Primary metric | Leading indicators |
|---|---|---|---|
| sales_push | units of named SKUs or revenue by date | coded chats about the SKUs, plus units sold (Kaspi/POS vs 4-week baseline) | coded chats per 1k views, saves, comments with purchase questions |
| launch_or_event | first orders or attendance by date | coded RSVPs or chats by date | shares per 1k views, profile visits |
| awareness_or_viral | inquiries from new people | coded chats from new contacts per week | views ÷ account median, shares and saves per 1k, followers in the city |
| reputation_or_trust | rating and review flow | new reviews per week, rating | positive comment ratio, proof-content saves |
| price_pressure | hold price and conversion | chat-to-sale rate, average check | saves on value content, objection frequency in chats |
| retention_or_loyalty | repeat purchases | repeat orders from existing contacts | Status views, replies to Status |
| hiring | role filled by date | qualified applicants via code | shares, profile visits from job seekers |
| b2b_leads | qualified pipeline | qualified coded inquiries (with a B2B screen) | saves, profile visits, comments from pros |
| should_we_do_social | an evidence-based yes or no | 4-week test: coded chats vs time spent | per-post resonance ÷ peer median |

**Target-setting rules:**
1. **Baseline** = the last 4 weeks (WhatsApp export, Kaspi, POS). If there is none, week 0 counts become the baseline and the target is fixed as a multiple at the end of week 2. Say this in the brief.
2. **Give three numbers:** conservative (likely), expected, stretch. Never a single promise.
3. **New accounts:** organic reach in weeks 1–4 is highly variable. Do not use absolute views as the primary metric.
4. **Big dated sales targets:** a target of more than about 2× baseline within ≤4 weeks needs levers beyond cold organic content. Name them: the warm base (WhatsApp Status, existing followers), an approved offer, a paid boost of proven posts, Kaspi listing quality. Name them in `push_back`.

### A5. Constraints checklist

Fill each item. Unknown items take the default shown and are logged as assumptions.

| Constraint | Default if unknown |
|---|---|
| Who may appear (faces) | Hands and voice only |
| Customers on camera | Never, unless consent is recorded on camera plus a written note. Minors only with a parent's written consent. |
| Prices on screen | No, until the owner sends a dated price list |
| Offers or discounts | None, except offers already published by the client (cite the URL) |
| Paid budget | 0 |
| Topics or words banned by the owner | none known |
| Regulated category (medical, dental, alcohol, tobacco, finance, education licences, children's goods claims) | Treat as regulated: no outcome claims. Flag paid ads for the owner's legal check. Do not give legal advice. |
| Stock | Re-check on the day of publishing |
| Languages | Russian, with Kazakh captions where D7 applies |
| Accounts | List what exists. Missing accounts are an owner ask. |
| Approver | Owner |
| Deadlines and seasonality | Taken from the request and the calendar |

### A6. Hard cases

**Precedence when anything conflicts:**
1. Law, truth, consent.
2. The owner's hard constraints (who or what may be shown, money).
3. The business objective.
4. The owner's style preferences.
5. The agent's preferences.

| Case | Handling rule | Example |
|---|---|---|
| **Vague** («сделайте нам маркетинг») | Apply the request_type default from A4, using the bottleneck hypothesis from available evidence. Assume rather than ask. State the assumption. | → awareness + consideration, metric = coded chats from new contacts |
| **Unrealistic** («миллион просмотров», «100 пианино за неделю» on a baseline of 5) | Quantify from the baseline. Offer the achievable version plus an upside lottery ticket. Name the levers that are outside content. Never promise virality. | «Гарантировать вирусность не может никто… мы делаем много честных разных роликов и по цифрам усиливаем сработавшие» |
| **Conflicting** («премиум» + «покажите, что дешевле всех»; «вирусно» + «никого не снимать») | Find the design that satisfies both. Example: premium shown through expertise and «цена за год использования» built from ledger facts; face-free sound and process formats. If both cannot be met, name the trade-off in one sentence, pick a default by precedence, and let the owner flip it in one tap. | «Без лиц — делаем руки, звук и процесс; это работает, но живой человек в кадре обычно сильнее. Вариант: владелец в кадре раз в неделю?» |
| **Non-sales** (hiring, reviews, "find a supplier", events) | Map to the nearest countable objective (A2 table). Use the same engines with a different audience. Hiring content also signals to customers ("the people who serve you"). | «Найдите продавца» → honest job-reality series, applicants via code, plus local job boards (hh.kz, enbek.kz) as owner actions |
| **Disguised non-marketing** («продажи упали») | Check stock, Kaspi price position for the same SKUs, reply time, seasonality and reviews before you prescribe content. | Reply time 4 h from the export → the fix is reply scripts and someone on duty |
| **Out of scope** (logo, website, SEO, accounting) | Say so plainly. Offer the part content can do. | «Сайт — не наша задача; можем сделать ролики, которые ведут в WhatsApp» |
| **Unethical or illegal** (fake reviews, «осталось 2 штуки» when untrue, attacks on a named competitor, copying a video 1:1, health or outcome claims, pushing restricted goods) | Refuse that part and give the honest alternative in the same message. | Fake reviews → a review-request message after real purchases |

### A7. Clarifying questions (maximum 3)

**Ask only if all three hold:**
1. The answer cannot be derived from the inputs within 24 h.
2. It changes the plan materially (strategy, legality, a permission).
3. There is no safe, reversible default.

**Priority:**
1. Permissions only the owner can give: faces, prices on screen, offers, paid budget.
2. A fact that flips the strategy: what «финальная распродажа» means, the real deadline, stock depth.
3. The definition of success, only if the ladder cannot resolve it.

**Format:** closed questions, numbered options, a default and a deadline, all in one Russian message. Example:

> 1) Кого можно показывать в видео? 1 — только руки и голос, 2 — сотрудников с лицом (с их согласия), 3 — и клиентов (с их согласия). *Если не ответите до среды — снимаем только руки и голос.*
> 2) Можно показывать цены? 1 — да, по прайсу (пришлите фото), 2 — нет. *По умолчанию — без цен.*
> 3) Распродажа «финальная» — это 1 — закрытие, 2 — уход бренда, 3 — сезонная? *До ответа не пишем ни о закрытии, ни о сроках.*

**Never ask:** target audience, USP, tone of voice, "what content do you like", or a general marketing budget. Ask a specific boost amount as options, and only when a boost decision is due.

**Assume, and log the assumption, when:**
- the answer is a style preference;
- the default is reversible within a week;
- the owner's approval of the batch will catch it anyway.

### A8. Intake self-check (all must pass)

- [ ] The primary metric is countable weekly by us.
- [ ] There is a baseline, or a week-0 plan.
- [ ] There are ≤3 questions, each with options, a default and a deadline.
- [ ] Every assumption has an impact and a verification route.
- [ ] `push_back` plainly states anything unrealistic or non-marketing (empty only if nothing is).
- [ ] The bottleneck is stated, with confidence.

---

## B. Inputs

### B1. Rules

- Fetch public data first, at zero owner minutes.
- Raw material beats owner opinions.
- One bundled owner message.
- Every input has a fallback. A missing input never blocks the first batch; it lowers confidence and is labelled.
- Anonymise personal data on ingest.

### B2. Tier 0: automated, zero owner minutes

| # | Input | What exactly to extract | If unavailable |
|---|---|---|---|
| 0.1 | Client website, catalogue, Kaspi shop, IG/TikTok bio | **Facts ledger:** products, prices (with date), stock, delivery and payment (installments, Kaspi QR), returns, warranty, address, hours, phones; offers already published (URL); errors to avoid (old city names, a 90%-off typo) | Ask the owner for a price-list photo. Until then, no prices on screen. |
| 0.2 | Reviews: 2GIS, Kaspi product and shop reviews, Yandex/Google Maps, comments on the client's posts | Verbatim customer language, by theme: praise (what exactly), complaints, fears before purchase («думала, что…»), named staff, purchase moments, outcomes; with counts and dates | If blocked, ask for 2–3 screenshots of the 2GIS/Kaspi review page (1 min) |
| 0.3 | The client's own channel history | Per-post views ÷ channel median; top and bottom deciles; which posts got question comments; language mix of comments; cadence; follower count | New account: use the peer median as baseline until 10 own posts |
| 0.4 | 5–15 peer accounts (same category; local first, then CIS leaders) | For each top-decile post (views ÷ that channel's median): engine, first frame, length, face or not; questions in their comments; gaps nobody fills | Use pooled learnings for the vertical group |
| 0.5 | Search demand: TikTok/YouTube/Instagram search suggestions (RU and KK) for category + city; Yandex Wordstat (KZ region); Google Trends KZ | Exact phrases people search («как выбрать…», «сколько стоит…», «…Караганда»), seasonality peaks, local naming | Use the question clusters from reviews and the WhatsApp export |
| 0.6 | Trend scan (weekly): platform trend tools for KZ or the nearest RU-language region; peers' last 14 days | Trend cards (D8) | Skip trends; they are optional packaging |
| 0.7 | Calendar and context | Moments: Наурыз, 1 сентября, Новый год, 8 марта, Курбан айт, Рамадан/ауызашар, той season, выпускные, first frosts, school holidays, payday rhythm (verify locally), and marketplace sale events only if the client participates (confirm) | — |
| 0.8 | Pooled learnings (`knowledge/learnings.jsonl`, engine posteriors per vertical group, graveyard of failed ideas) | Priors per engine × vertical; hooks already tried; things not to repeat | Neutral priors |
| 0.9 | Marketplace position: same SKUs on Kaspi | Price vs other sellers on that date, number of sellers, rating | Never claim «дешевле» |

### B3. Owner and staff actions, ranked by value per owner minute

| Rank | Input | Owner min | How | What to extract | If missing |
|---|---|---|---|---|---|
| 1 | **WhatsApp chat export** (last 30 days, or 5–10 typical chats, without media) | 2 | The owner exports and forwards it (instructions in B4) | Questions (counted), objections, the exact words customers use, where chats die (after price? after "подумаю"?), reply time, chat-to-sale signals, which products are asked about, how customers found the business, voice-note share | Use reviews and peer comments as a proxy for language. The conversion bottleneck stays unknown, so mark it as an assumption. |
| 2 | **Permissions tap-card** (faces, prices, offers) | 1 | 3 numbered questions (A7) | Hard constraints | Defaults: hands and voice, no prices, no offers |
| 3 | **Owner voice note**, 2–3 min, 3 prompts | 3 | «Что покупают чаще всего и почему? С каким вопросом приходят? Один случай, когда клиент ушёл очень довольный (или вы его отговорили)» | Proof stories, the owner's beliefs (labelled as owner statements), the people and processes behind the business, possible hero characters | Use reviews. Proof stories stay missing; no story-engine ideas. |
| 4 | **Best sellers, must-move list, price list** (photo or screenshot) | 2 | Photo of the price list or a Kaspi seller-cabinet screenshot | Which SKUs matter; dated prices for the ledger; stock depth | Use catalogue data with a 2-day price expiry. Any SKU focus is labelled as an assumption. |
| 5 | **Camera roll**: 10–30 existing photos or videos of real work, deliveries, behind the scenes | 3 | The owner or staff send them as a file or document, to avoid compression | Zero-staff-minute content sources, proof assets, filmable realities | Ideas rely on new shoots only |
| 6 | **Account insights** (screenshots or account access) | 2 | IG/TikTok analytics: top cities, age, watch time, follower activity | Baseline per platform, geography check | Use public counts only |
| 7 | **Staff phone test**: 3 clips, once | Staff 10 | One spoken line at 30 cm, one product sound at 30 cm, one room shot | Real audio, light and noise levels; whether the phone has 60 fps or stabilisation | Design for the worst case: speech recorded close, no wide shots in dark rooms |
| 8 | **Sales baseline** for the relevant SKUs or bookings (4–8 weeks) | 2 | Kaspi orders or POS screenshot | Baseline for the primary metric | Week-0 count becomes the baseline |
| 9 | **UGC route**: existing review incentives; permission to ask customers for a 15-second clip | 1 | One question | Proof assets from real buyers | No customer-voice engines |
| 10 | **Boost budget** | 1 | Asked only when a post qualifies (F10 R8) | Spend cap, maximum cost per coded chat | No boost |

**Ongoing weekly inputs** (built into the loop, not extra asks):
- The 48 h and 7 d metrics per post.
- The coded-chat count, from a weekly WhatsApp export or a 1-minute owner tally.
- New comments, which the agent reads.
- The staff "question of the week" voice note: 30 s at the end of the shoot card.
- Approval taps and rejection reasons.
- Stock and price changes.

### B4. The onboarding message (one message, about 10 minutes, in Russian)

> Здравствуйте, {Имя}! Я — ИИ-ассистент MetaPrompt, готовлю для вас короткие видео. Чтобы они были про ваших настоящих клиентов, а не «как у всех», нужно 4 вещи, примерно 10 минут:
> 1) **Переписка WhatsApp с клиентами** за последний месяц: откройте чат → ⋮ (или имя контакта) → «Экспорт чата» → «Без медиафайлов». Достаточно 5–10 типичных чатов. Имена и номера мы сразу удаляем, наружу ничего не попадает.
> 2) **Голосовое на 2–3 минуты:** что покупают чаще всего и почему; с каким вопросом чаще всего приходят; один случай, когда клиент ушёл очень довольный.
> 3) **Фото прайса** или список: что продаётся лучше всего и что нужно продать в первую очередь.
> 4) **Ответьте цифрами:** а) кого можно снимать: 1 — только руки и голос, 2 — сотрудников с лицом (с их согласия), 3 — и клиентов (с их согласия); б) цены в видео: 1 — можно, 2 — нельзя; в) акция: 1 — нет, 2 — есть (какая и до какого числа).
> Если что-то неудобно — пропустите. Начнём с того, что есть, и ничего не опубликуем без вашего «да».

### B5. Missing-input policy and cold start

**Never block the first batch.** With Tier 0 data only, the agent:
- writes provisional insights, marked `confidence: likely/assumption`;
- weights its ideas toward engines that need no private facts (process, sound, POV, care/how-to, reply-to-comment);
- holds back price, offer and number-based ideas until the facts arrive.

When the WhatsApp export arrives, rerun C (re-cluster and re-rank). The insight list is versioned.

---

## C. Working the inputs: evidence base, then insights

### C1. Ingest and privacy

1. Strip phone numbers, names and addresses from chat exports on ingest. Replace them with `cust_###`.
2. Keep raw files only in the client folder.
3. Customer words from private chats may never appear verbatim in public content without consent. Paraphrase only if the paraphrase matches ≥2 real messages.
4. Public reviews may be quoted without the reviewer's name.

### C2. Atomise into evidence items

Turn every source into atomic items: **one claim per item**, verbatim where it is customer language. Each item has:
- `kind` ∈ `fact | customer_language | behaviour | proof_asset | moment | constraint | market | performance`
- `source` (URL, file + line, or owner voice note + timestamp), `fetched_at`
- `confidence` ∈ `verified | likely | assumption`
- `count` (how many times it was seen) and `source_count` (independent sources)
- `use_rights` ∈ `public | paraphrase_only | internal`

**Tag `customer_language` items on these dimensions:**
- question, objection, fear, desire;
- belief (true or false);
- trigger moment;
- decision criterion;
- alternative considered (competitor, marketplace, DIY, doing nothing);
- praise (what exactly), complaint, outcome;
- identity cue (мама, студент, новичок, профи);
- notable wording (slang, Kazakh phrases, local names).

**Classify each item with the JTBD forces:**
- Push: the problem with the current state.
- Pull: the attraction of the new.
- Anxiety: the fear about the new.
- Habit: inertia.

Most usable tensions live in Anxiety and Habit.

### C3. Facts ledger (what may be claimed)

| Fact type | Valid source | Expiry |
|---|---|---|
| Price | Site, Kaspi, or price-list photo, dated | 2 days; re-check before publishing |
| Stock | Site or owner | Same day as publishing |
| Promotion or offer | Published URL or owner text with end date | Its end date |
| Policy (delivery, returns, warranty) | Site page or owner | 30 days |
| Specs | Manufacturer or site | Until the product changes |
| Internal numbers («за месяц спросили 37 раз») | Our count from exports, with method | 30 days; state the period on screen |
| Owner statements («сами настраиваем каждую гитару») | Owner voice or text, dated | 90 days. Allowed as "мы делаем X". Not allowed as superiority («лучшие», «единственные»). |
| General category knowledge | Textbook or manufacturer; non-controversial | Re-verify yearly. Health, legal and finance knowledge needs an authoritative source plus specialist sign-off. |

### C4. Language bank

Collect verbatim phrases grouped by cluster: questions, objections, praise words, the ways customers name the product, slang, Kazakh phrases. Hooks, captions and WhatsApp reply scripts draw from this bank first. A hook in the customer's own words beats a copywriter's line.

### C5. Cluster and count

1. Cluster the evidence by underlying need or worry (not by surface words).
2. For each cluster record:
   - frequency (`count`, `source_count`);
   - intensity markers: money, time, health, children, social face at stake, emotional words, exclamation marks, repeat asks;
   - the business stage it affects (A3);
   - existing proof assets that answer it.

### C6. Insight types and how to write each

| Type | Template (written in the customer's words) | Example (generic) |
|---|---|---|
| **Tension** | «Хочу [желание], но [страх/убеждение/препятствие], поэтому [что делаю сейчас]» + **resolution truth**: what is true and showable that dissolves it | «Хочу нормальный диван, но боюсь, что не влезет в лифт, поэтому покупаю на маркетплейсе модульный» → we measure the lift on video |
| **Belief / myth** | «Думают, что [убеждение]; на самом деле [правда, источник]; это важно, потому что [последствие]» | «Думают, что шеллак портит ногти» → only with a sourced truth |
| **Moment (category entry point)** | «Когда [ситуация], человек [нужда] и спрашивает [слова]». Use the W-prompts: why, when, where, while doing what, with or for whom, feeling what. | «Когда ребёнок пошёл в первый класс и сидит далеко от доски…» |
| **Proof asset** | «У бизнеса есть [предмет/процесс/цифра/люди], который наглядно доказывает [утверждение]» | a repair counter full of saved items; a checklist used before shipping |
| **Content-able reality** | «[Процесс/звук/ритуал/человек/цифра/предмет] интересен постороннему, потому что [почему]» | the sound of an edging machine; a lost-and-found shelf |
| **Objection map** | «Перед покупкой спрашивают [вопрос]; если не ответить — [что происходит в чате]» | chats die after a lens price is sent without explanation |
| **Local context** | «В [город/регион] [реальность], и это меняет [поведение]» | first frosts lead to a winter-tyre rush |

**Content-able reality inventory** (always build it; it is the cheapest idea fuel):
- **Sounds:** close-up sounds of the craft.
- **Processes:** from start to finish.
- **Rituals:** opening, closing, a check before handing over.
- **People:** who is willing, in what role (voice or hands count).
- **Places:** the corners with the best light and the least noise.
- **Numbers:** what can be counted honestly.
- **Objects:** odd, beautiful or broken things.
- **Recurring situations:** what happens every day.

### C7. Rank insights

Score each insight 0–3 on six dimensions:

| Dimension | 0 | 3 |
|---|---|---|
| Evidence | assumption only | ≥3 independent sources, with counts |
| Intensity | mild preference | money, time, health, child or face at stake; emotional words |
| Leverage | unrelated to the bottleneck | directly on the bottleneck stage of the primary metric |
| Showability | cannot be filmed | filmable in ≤5 staff min with one phone (or from existing assets) |
| Distinctiveness | a category cliché | only this business's people, process, data or place |
| Proof | no true proof | a true proof can be shown on camera |

- `strength` is the sum (0–18).
- **Gate:** with `proof = 0`, the insight may feed only question or engagement content (asking, discussing), never a claim.
- Pass the top 5–8 to D. Include at least one tension, one moment and one content-able reality, plus 1–2 wildcard moments from the calendar. Break ties on leverage.

### C8. Keeping facts true (rails used in C to G)

1. **Every audience-facing claim** maps to a ledger fact ID. Claim types: price, number, stock, discount, date, deadline, superlative, comparison, spec, guarantee, health, safety, legal, testimonial.
2. **Superlatives are banned** («самый», «лучший», «№1», «дешевле всех», «единственные») unless verified by a third-party source on that date. Owner belief is not enough.
3. **Opinions are allowed as opinions** («по-моему», «мастер считает»), never presented as facts.
4. **Urgency and scarcity** only with an owner-confirmed end date or stock count, re-checked on publish day.
5. **Health, legal and finance:** no outcome claims. Show the process («что происходит на приёме»), not promises.
6. **AI never depicts** the client's real product, premises, staff, customers or results as real. AI scenes are labelled. No AI before/after shots, no synthetic testimonials, no cloned staff voice without written consent.
7. **Conflicting sources:** the newest primary source wins, and the conflict is flagged.
8. **An unknown fact never gets silently fixed.** It becomes a batched owner question, and the idea is parked with `needs_facts`.

---

## D. Idea generation for high-chance short videos

### D1. The behavioural drivers

| Driver | What triggers it | How to engineer it in a short | Self-test | Observable signal |
|---|---|---|---|---|
| **Stop** (first second) | Motion, oddity, a face or hands mid-action, close-up sound, a call-out of a specific viewer, stakes, contradiction | Start mid-action. The first frame is the cover. Hook text ≤7 words. Spoken words start within 0.5 s. No logo, greeting or «сегодня расскажу». | Would a stranger scrolling at night stop? | 3-s hold, skip rate where exposed |
| **Watch** | An open loop, visible progress, a countdown, a reveal, a turn in the middle | A visual change every 1–3 s. Make the promise clear by second 3. Payoff at 70–95%. The ending loops to the start. | Is there a reason to see the end? | Average watch %, full watches |
| **Share** | Practical value for someone else; identity («это про нас»); high-arousal emotion (amusement, awe at skill, tenderness, «наконец-то кто-то сказал»); insider knowledge; local pride | Name the person it gets sent to. Make it about a situation, not the shop. | «Кому конкретно это перешлют и с какими словами?» If there is no answer, it fails. | Shares per 1k views |
| **Save** | Reference value needed later: a checklist, sizes, steps, «как выбрать», real price ranges, care instructions | Structure the knowledge so it is worth returning to; one dense summary frame at the end | «Понадобится ли это через неделю?» | Saves per 1k views |
| **Comment** | A real opinion split, own experience, local knowledge, a correction invitation, a fair guess | Ask a question people actually disagree about; give two real options with trade-offs. Turn replies into reply videos. | Would I type an answer in 3 seconds without being asked? | Comments per 1k views, share of substantive comments |
| **Follow** | A series promise, a recurring character, a fixed slot | A named series with a recognisable opening; «часть N» only if part N+1 exists | Is there a reason to see the next one? | Follows per 1k views |
| **Convert** | A specific benefit, a low-friction next step, trust | Soft CTA in the last 2 s and in the caption. The code says what to send («напишите ВОПРОС3 — пришлём…»). | Does the viewer know exactly what happens after they write? | Coded chats per 1k views |

### D2. Anatomy of a short (timeline every idea is written to)

- **0.0–1.0 s:** first frame, moving, which is also the cover. Hook text and/or first spoken words.
- **1–3 s:** confirm the promise; show the thing the hook refers to.
- **3 s to about 70%:** development, with a visual change every 1–3 s and a turn (contrast or surprise) near the middle.
- **70–95%:** the payoff fully delivers the hook. A hook the video does not pay off is a lie.
- **Last 1–3 s:** a soft coded CTA or a loop back to the first frame. The comment prompt goes in the caption or on screen.

**Length defaults** (length is also a test dimension; when in doubt, go shorter):

| Content type | Length |
|---|---|
| Loops, sound, satisfying process | 6–12 s |
| Proof or comparison | 12–25 s |
| Answers or guides | 20–45 s |
| Stories | ≤60 s |

**Text, subtitles and captions:**
- Burned-in subtitles always.
- Keep text in the safe area: avoid the bottom 20% and the right edge.
- Caption line 1 restates the hook and includes the customer's search phrase and the city.
- Use 3–5 relevant hashtags, including the city.
- Put the code on the last line.

### D3. Idea engines (angle generators that work in any industry)

The 30 engines are grouped into 7 families. Families are the arms pooled across clients (E8). The "Needs" column drives the fit test in D6.

| ID | Engine | What the video is | Main drivers | Needs from evidence | Staff min | Cross-industry example |
|---|---|---|---|---|---|---|
| **F1 Answer** |||||||
| E01 | Вопрос из WhatsApp | A real recurring question → a 20–40 s answer, with the question on screen (anonymised) | save, convert, follow | a counted question cluster | 2–3 (voice close + hands) | dry cleaner: «можно ли пуховик в машинке?»; furniture: «влезет ли в лифт?» |
| E02 | Миф vs правда | A category belief → the sourced truth, shown | stop, share, comment | a belief cluster + a source | 2–3 | car service: «прогревать мотор 15 минут» |
| E03 | Ошибки при выборе | The top 3 mistakes buyers make, shown on real items | save, share | objections and complaints | 3 | tyres, strollers, mattresses |
| E04 | Как отличить / как проверить | How to spot quality, a fake or a defect yourself | save, share | a quality fear + a proof method | 2–3 | honey, leather, phone screens |
| E05 | Бюджетные уровни | What you get at 3 real price points | save, comment | ledger prices for 3 SKUs | 3 | bouquets, guitars, haircuts |
| E06 | Анатомия цены | Why it costs this: time, materials, steps (no invented numbers) | trust, comment | a price objection + owner-confirmed process | 2–3 | cakes, tailoring, auto paint |
| E07 | Уход / мини-инструкция | How to use, care for or store it | save | after-purchase questions | 2 | shoes, plants, glasses |
| **F2 Proof** |||||||
| E08 | A vs B / слепой тест | Two options side by side, same conditions | watch, comment | a comparison question + 2 in-stock items | 2–3 | two coffees, two lenses, two paddings |
| E09 | Проверяем на прочность | Stress-test a claim honestly | stop, watch | a verifiable claim | 2–3 | bags, phone cases, flooring |
| E10 | До/после | A real transformation, no filters | stop, watch, share | real work + consent | 2 (two clips) | detailing, cleaning, nails |
| E11 | Что проверяем перед выдачей | The quality-control ritual | trust | an owner-confirmed process | 2 | e-shops, repair, bakeries |
| E12 | Цифра из нашей жизни | A counted internal number, made visual | share, comment | a counted fact with period | 1–2 | «забытые зонты за год», «вопросов про X за месяц» |
| **F3 Process and senses** |||||||
| E13 | От начала до конца | The whole make or fix process, fast cut | watch, share | a filmable process | 3–4 | cakes, keys, framing |
| E14 | Звук крупным планом | A close-up sound of the craft, looped | stop, watch | an audible process | 1–2 | edging, cutting, sizzling, strings |
| E15 | Что вы не видите | The backstage reality customers never see | watch, trust | a content-able reality | 2 | the warehouse, the 7am prep |
| E16 | Ритуал открытия/закрытия | The daily ritual as a series | follow | a repeatable moment | 1 | bakery, flower shop |
| **F4 People and story** |||||||
| E17 | POV покупателя / сотрудника | A recognisable situation from the inside | share, comment | a recurring situation | 2 | «POV: вы пришли „только посмотреть“» |
| E18 | Персонаж серии | A recurring staff or owner persona (can be voice or hands only) | follow | a willing person + consent | 2 | «мастер, который всё чинит» |
| E19 | История клиента | A real case: problem → solution (UGC or retold with consent) | trust, share | a proof story + consent | 0–2 | any service |
| E20 | Спасение / ремонт | What came in broken and how it was saved | watch, share | a real repair | 2–3 | shoes, phones, furniture |
| E21 | Честный антипродаж | «Не покупайте у нас, если…» or «мы отговорили клиента» | trust, share, comment | a real event or policy | 2 | an optician sends a client to a doctor; a seller advises a cheaper model |
| **F5 Conversation and opinion** |||||||
| E22 | Ответ на комментарий | A video reply to a real comment | comment, follow | a real comment | 1–2 | any |
| E23 | Тир-лист / рейтинг | A staff member ranks options by an honest criterion | comment | staff experience (labelled as opinion) | 2 | frames by durability, cakes by order frequency |
| E24 | Спор двух мнений | Owner vs staff on a real disagreement | comment | a real split | 2 | «стоит ли переплачивать за X» |
| E25 | Угадай | Guess the price, the item or which is which; the answer revealed fairly | comment, watch | ledger prices or facts | 1–2 | «какой букет за {цена A}?» |
| **F6 Context and culture** |||||||
| E26 | Момент / сезон | A category entry moment | share, convert | a moment insight + date | 2 | 1 сентября, той, first frosts |
| E27 | Локальная идентичность | A city or region in-joke tied to the category (no politics or ethnicity) | share, comment | local context evidence | 1–2 | weather, distances, local habits |
| E28 | Тренд-ремикс | A trend structure carrying an insight | stop | a trend card + an insight | 1–3 | — |
| E29 | Подарочный гид | «Что подарить [кому] на [сумма]» with real items | save, convert | ledger prices + a gift moment | 2 | any retail |
| **F7 Recruiting** (hiring requests) |||||||
| E30 | Честно о работе | The real day, what is hard, the team; pay only if owner-confirmed | share | owner-confirmed job facts | 2–3 | any employer |

**Production modes** (how a concept is shot):

| ID | Mode | Face-free | Notes |
|---|---|---|---|
| P1 | Hands + voice, with voice recorded at ≤30 cm | yes | default for shy staff |
| P2 | POV at eye level | yes | |
| P3 | Selfie-distance talking head | no | good audio by design |
| P4 | Process close-up, no words, text on screen | yes | |
| P5 | Comparison, split or sequential | yes | |
| P6 | Photo carousel (TikTok photo mode or IG carousel) with text | yes | very cheap; strong for saves |
| P7 | Anonymised question screenshot + answer | yes | |
| P8 | AI explainer for abstract concepts | yes | real clip inserts; never AI product |
| P9 | Customer UGC | n/a | consent required |
| P10 | Off-screen-question interview | no | one phone, close to the speaker |

**Archetype priors** (hypotheses to start from, overridden by data):

| Archetype | Typical examples | Dominant tension | Engines with the strongest prior | Path to sale |
|---|---|---|---|---|
| Considered retail | instruments, furniture, optics, electronics | the wrong choice, overpaying | E01, E03, E04, E05, E08 | WhatsApp consult → visit or Kaspi |
| Impulse and sensory | bakery, coffee, flowers, street food | craving, gifting | E13, E14, E16, E26, E17 | walk-in, WhatsApp pre-order |
| Transformation services | beauty, detailing, repair, cleaning | «будет ли результат стоить того» | E10, E20, E13, E04 | WhatsApp booking |
| Trust-critical or regulated | dental, medical-adjacent, legal, finance, kids' education | harm or being cheated | E15, E01 (no claims), E21, E11 | booking; strictest claim rules |
| Experiences and venues | cafés, kids' centres, fitness, courses | «понравится ли / стоит ли ехать» | E17, E18, E26, E27 | DM or WhatsApp booking |
| B2B and trade | building materials, wholesale, equipment | reliability, delivery, price | E09, E11, E12, E01 | WhatsApp or phone quote |
| Recruiting | any | «нормальная ли работа» | E30, E18, E17 | coded applications |

### D4. Generation procedure

1. **Load:**
   - top insights (5–8) with tensions and proof;
   - language bank, content-able reality inventory, ledger, constraints;
   - trend cards, archetype priors;
   - pooled engine posteriors for the vertical group;
   - the graveyard (ideas and hooks that already failed for this client).
2. **Fit matrix:** insights × 30 engines. Mark a cell where the engine's "Needs" are met by the insight's evidence. Expect 4–8 fits per insight.
3. **Concepts:** write one line per fit (who / what happens / the twist), aiming for 40–60 raw concepts. Use these mutation operators for variety:
   - change the **narrator**: owner, staff, customer, the object itself;
   - change the **perspective**: customer POV, worker POV, product POV;
   - change the **stakes**: money, time, health, face;
   - **invert**: what NOT to do;
   - **zoom**: macro detail vs the whole room;
   - **count**: one thing vs five;
   - **time**: 10 seconds vs a whole day sped up;
   - **call-out**: parents, students, beginners, pros;
   - **language**: RU, KK or mixed;
   - **form**: video or carousel;
   - **emotion**: humour, awe, tenderness, mild indignation.
4. **Cut to ≥24 written ideas** with these quotas:
   - ≥8 engines from ≥5 families;
   - ≥4 insights;
   - ≥40% face-free (100% if faces are not permitted);
   - ≥3 led by save, ≥3 by share, ≥3 by comment;
   - ≥3 conversion-ready;
   - 2–4 wildcards (moment, local or trend);
   - ≥2 zero-staff-minute ideas if existing assets exist.
5. **Write each idea at shot level:** first frame, hook, beats with timing, payoff, ending, comment prompt, coded CTA, worker shots, AI parts, facts used.
6. **Run the fast self-tests.** Rewrite or drop on any fail.
   - stranger test (D1, Stop);
   - send-to-whom;
   - save;
   - only-us (could a random competitor post it unchanged? then lower brand_link);
   - not-an-ad (D10);
   - truth (C8);
   - 20-minute (D9);
   - consent.
7. **Three hooks per idea:**
   - (a) statement or contradiction;
   - (b) question or viewer call-out;
   - (c) visual- or sound-only opening (no words for the first 1.5 s).
8. **Self-score the rubric (E3)** as a prior only.

### D5. Hook writing rules (Russian patterns; every slot must be filled from the ledger or language bank)

- **Name the viewer:** «Если ваш ребёнок щурится у телевизора —»
- **Contradiction** (only if sourced): «Самая дорогая [вещь] вам, скорее всего, не нужна»
- **Stakes:** «Эта ошибка стоит {сумма из ledger}»
- **Customer question:** «Нам пишут: „{вопрос из кластера}“»
- **Comparison:** «Один [рецепт/размер/мотив]. Две [вещи]. Разница видна?»
- **Process, wordless:** close-up action + «Что происходит с вашими [вещами], пока вы ждёте»
- **List:** «3 вещи, которые проверит за вас мастер»
- **POV:** «POV: вы пришли „только посмотреть“»
- **Opinion:** «Мастер и я спорим: [вопрос]»

**Rules:**
- Use specific nouns and numbers from the ledger.
- Use the customers' own words.
- Pick one register per client (вы for 30+ audiences, ты for youth) and keep it.
- No CAPS clickbait, no lies, no «вы не поверите».

### D6. Platform-native details

- TikTok and Reels are for reach. TikTok, Instagram and YouTube search increasingly work like search engines, so spoken words and captions should contain the phrase customers search plus the city.
- Instagram is where KZ customers check that a business is legitimate (profile, highlights, reviews).
- YouTube Shorts gives a longer tail for answer content.
- Cross-post the same cut without the other platform's watermark.
- Business accounts use commercially licensed audio only.

### D7. Language (Russian / Kazakh)

- **Default:** Russian audio and text.
- **Add a Kazakh-caption or Kazakh-voice variant as an explicit test arm when:**
  - ≥15–20% of reviews or comments are in Kazakh (a heuristic, to be calibrated), or
  - the owner says a large share of customers prefer Kazakh.
- Kazakh copy is short and literal, never machine-translated wordplay. It is checked by a native speaker (owner or staff) in the approval step.

### D8. Trends without chasing irrelevant ones

**Trend card fields:**
- name and structure (setup → twist);
- what it means (the joke or feeling);
- 2 examples;
- age in days and estimated remaining life;
- commercial audio available on business accounts (yes/no);
- which insight it can carry;
- risk.

**Adopt only if all of these hold:**
1. The idea works without the trend; the trend is packaging.
2. Its meaning fits the brand and the insight.
3. It is producible within 48–72 h at ≤5 staff min, or zero.
4. Licensed audio exists.
5. No sensitive content: tragedies, politics, religion, ethnicity, mocking real people, minors, dangerous challenges.

**Further rules:**
- Prefer **structural trends** (POV, «день из жизни», «ранжирую», «объясняю как пятилетнему») over audio memes; they last longer and fit more insights.
- At most **1 trend-dependent idea per week** (≤20% of the slate).
- "Trend packaging yes/no" is itself an arm, so this client's data decides whether trends help.

### D9. What makes an idea producible (one weak phone, 20 minutes, AI)

**Phone rules.** These go into every shoot card in Russian, as short bullets:
- Протрите камеру.
- Вертикально, 1080p, 30 к/с (60 — для замедления).
- Без зума: подойдите ближе.
- Предмет или лицо к окну.
- Музыку в зале выключите.
- Речь: телефон не дальше 30–40 см от рта.
- Звук товара: телефон в 20–40 см от источника; режим микрофона «Стандартный», не «Изоляция голоса».
- Долгое нажатие на экран, чтобы зафиксировать фокус и экспозицию.
- 2 секунды тишины до и после дубля.
- Ошиблись: пауза и повторите фразу целиком; монтаж возьмёт последний дубль.
- Локти прижаты, или телефон на полке или коробке.
- Отправляйте видео **как файл/документ**, не как видео: иначе WhatsApp сожмёт качество.

**Speech design.** Where audio is weak at a distance, split it in two:
- the voice is recorded separately at selfie distance;
- the B-roll is shot silently or with close product sound.
Never plan a wide shot with dialogue.

**20-minute arithmetic** (the optimiser enforces it):
- fixed 3 min (lens, music off, open the card);
- plus 2 min setup per location;
- plus, per shot, seconds × takes ÷ 60 + 0.5 min;
- plus 1 min per capture-on-the-fly ask;
- plus 1 min for the weekly voice question;
- keep 2 min of buffer.
This typically gives 5–8 shots, which feed 4–6 videos, because one shot can serve two videos.

**Capture-on-the-fly asks** are for moments that happen anyway: deliveries, a customer's reaction, a repair coming in. Example: «Если клиент удивился или обрадовался — спросите: „Можно снять 10 секунд для нашего Instagram?“ Если да — пусть скажет „да“ в камеру.» A child's face also needs a parent's written OK.

**Zero-staff-minute sources:**
- the camera roll;
- re-edits of past posts;
- photo carousels;
- screen recordings (Kaspi page, 2GIS route, an anonymised chat);
- AI explainers voiced by the owner or a labelled synthetic voice.

**AI may do:**
- editing: last-take pick, jump-cuts, stabilisation, music-safe loudness;
- captions and RU/KK subtitles;
- per-video on-screen design;
- hook and cover variants;
- voice-over (staff-recorded, or synthetic and labelled);
- AI visuals for abstract concepts (inside a product, a metaphor, a diagram);
- licensed background music;
- upscaling and reframing;
- short staff lines written in their own words;
- comment and WhatsApp reply drafts.

**AI may not:**
- depict the real product, premises, staff, customers or results as real;
- invent before/after shots, testimonials or customers;
- clone a voice without written consent.

**Cost tiers:**
- **T0:** staff footage plus edit (default).
- **T1:** T0 plus AI text, voice and overlays.
- **T2:** generative video credits. Only with owner approval of credits, only for non-product visuals, and the first use goes into a test arm.

### D10. Anti-patterns (detect, then rewrite or drop)

| Anti-pattern | Detection rule | Fix |
|---|---|---|
| Ad-first | Brand, «у нас», discount or price in the first 3 s; the video collapses if you remove the CTA | Lead with the viewer's situation; brand at the end |
| Price slide | Product photo + price + motion text, with no human, real sound, question answered or story (judged useless in practice) | Put the price inside useful content (E05, E25, E06) with real sound or hands |
| Childish engagement bait | «Лайк, если…», «Напиши +», «Отметь друга» detached from value, «Досмотри до конца» without a payoff, a fake «часть 2?» | A real question with a real split (D1, Comment) |
| Fake urgency or scarcity | «Только сегодня», «осталось 2», countdowns without a ledger fact and a publish-day check | Remove it, or get the owner-confirmed date and count |
| Invented proof | Unsourced numbers, «нас выбирают тысячи», AI testimonials | Counted internal numbers (E12) or real UGC |
| Generic «5 причин выбрать нас» / «мы на рынке 10 лет» as the hook | Fails only-us and stranger tests | Show one reason, filmed |
| Greeting cards («С 8 марта!») | No insight, no payoff | A moment idea (E26) with a real use |
| Forced performance | Dancing staff who do not want to, skits by shy people | Face-free modes, a voice-only character |
| Trend for its own sake | Fails trend rule 1 | Drop the trend, keep the insight |
| Humour at the customer's expense; named-competitor attacks; politics, religion, ethnicity | Brand-safety gate | Rewrite from the customer's side |
| Long intros, a logo sting, «Привет, меня зовут…» | Nothing moves in the first 1 s | Cut to mid-action |
| Privacy leaks | Visible phone numbers, names, faces without consent, minors | Blur, paraphrase, or get consent |

---

## E. Idea selection

### E1. What scores are for

Rubric scores are a **prior**. They:
- order the queue;
- fill exploit slots before any data exists;
- break ties.

They are **not** a prediction of performance. Once a client or engine has audience data, the posterior from the experiment engine overrides the prior.

**The LLM judge may only filter:**
- It may drop the clearly weakest ~20%, with reasons.
- It may not rank the rest.
- Its authority per scope comes from calibration records. Current scope: `filter_only` for short-form overall, `none` for retail.

### E2. Gates (binary; any fail means blocked or rewritten, never "scored low")

- **G1 Truth:** every claim maps to a valid ledger fact; nothing has expired; `needs_facts` is empty.
- **G2 Not an ad:** passes the D10 ad-first rule.
- **G3 Producible:** fits the remaining staff minutes this week; respects the face policy; audio design obeys D9.
- **G4 Consent and legal:** faces, minors, customer data, regulated claims, music licence, AI labelling.
- **G5 Brand safety:** no politics, religion, ethnicity, mocking customers or named competitors.
- **G6 Insight-cited:** references ≥1 insight ID (wildcard moments cite a moment evidence item).

### E3. Rubric (1–5 per criterion, with anchors)

| Criterion | Weight* | 1 | 3 | 5 |
|---|---|---|---|---|
| stop | 1.5 | Opens on a logo, intro or static product | A clear subject plus a relevant hook | Mid-action, an unusual visual or sound, plus a call-out or stake, in ≤1 s |
| truth | 1.0 | (Gate fail) | Verified facts; the insight is "likely" | Every claim ledger-backed; the insight comes from ≥2 independent sources |
| share_save | 1.3 | Nobody sends or saves it | Useful or funny to an active buyer | A specific named recipient and reason, or reference material needed later |
| comment | 0.8 | Nothing to say, or bait | Invites an experience | A real low-effort opinion split, or a question people argue about |
| producible | 1.0 | Needs shy faces, actors, new locations or credits | ≤6 staff min, 1 location | ≤3 staff min, face-free, close audio, or zero staff minutes |
| brand_link | 0.8 | Any business could post it | Category-specific | Only this business: its people, process, data or place |
| objective_fit | 1.4 | Views only | Moves a leading indicator | Resolves the bottleneck tension and carries a natural coded CTA |

\* Weights live in `knowledge/rubric_weights.json`. They are judgment priors and are re-fitted per vertical group from audience data once ≥30 posts per arm exist.

`prior = Σ(weight_k × score_k) / Σ(weight_k × 5)`, which runs from 0 to 1.

**Selection value:**
- Before data: `value = prior`.
- With data: `value = w_d × posterior_mean(engine, client) + (1 − w_d) × prior`, where `w_d = n / (n + 8)`.
- `n` is the number of posts this client has in that engine family. Pooled vertical-group data enters the posterior through shrinkage (E8).

### E4. Slate size

- **Base videos per week** = what fits 20 staff minutes, plus zero-minute ideas. This is typically 4–6, with a minimum of 3.
- **Each base video gets 2 hook variants**, which are edit-only and cost no staff minutes. The top-prior idea gets 3.
- **Each cut goes to TikTok, Reels and Shorts.** This gives about 12–18 placements per week.
- Consistency beats volume. Never promise a cadence the shoot cannot sustain.

### E5. Slot allocation

| Phase | Explore (new engines or insights) | Exploit (best value) | Follow-ups of last week's winners |
|---|---|---|---|
| Weeks 1–3 | ≥50% | rest | 0–25% when winners appear |
| Week 4+ | ≥25% | about 50% | about 25% (if none, give the slots to exploit) |

**Explore picks** are sampled among gated ideas with the highest novelty (engine or insight untested for this client, or a graveyard-distant hook), weighted by prior.

### E6. Diversity rules (hard, checked in code)

Per weekly slate:
- ≥3 engine families; ≤2 ideas per engine; ≥3 different insights.
- ≥1 save-led, ≥1 share- or comment-led, ≥1 conversion-ready idea.
- ≤40% of base videos purely conversion-funnel.
- ≤1 trend-dependent idea.
- ≥2 different first-frame types (not all text over product).
- ≤50% of ideas need a face (0% if faces are not permitted).
- ≥1 zero-staff-minute idea when assets exist.
- No idea within 7 days of a near-duplicate (same insight + engine + mode) on the same account.

### E7. Variants (what to vary, cheapest and most valuable first)

1. First 1–2 s: first frame plus hook text. Edit-only.
2. Spoken first line, recorded two ways. About 1 staff min.
3. Length cut, short vs long.
4. Caption language (RU vs KK).
5. Cover style.
6. CTA wording.

**Rules:**
- Vary one thing per planned comparison.
- Placement, in order of preference:
  - a platform test feature where one exists (e.g. Instagram trial reels shown to non-followers);
  - otherwise, variant B goes to a different platform the same day, treated as a blocked comparison with platform as a fixed effect;
  - or, as a rescue, a repost ≥7 days later.
- Do not post near-duplicates on the same account within 7 days.

### E8. Arms, metrics, power, pooling

**Arms:**
- Engine family (7) is the arm pooled across clients.
- Engine (30) is the arm explored within a client.
- Optional binary dimensions: face vs no face, RU vs KK, trend packaging yes/no, short vs long.

**Per-post outcomes:**
- `y_reach = log(views_48h / platform rolling median of the last 15 posts)`. Before 10 own posts, use the peer median.
- `y_res = (shares + saves) per 1k views ÷ the same median`.
- `intent = coded chats + purchase-intent comments`. This is sparse: use it at campaign level and as a tie-breaker.

**Primary per-post outcome by request type:**
- Reach requests: `y_reach > 0`, i.e. the post beats the median.
- Consideration requests: `y_res`.
- Conversion requests: `y_res` per post plus coded chats at campaign level.

**Allocation:** Thompson sampling on P(beats median), with Beta posteriors. Each live arm keeps a floor of ≥10%.

**Power and pooling:**
- A 2× effect needs about 30 posts per arm for 80% power.
- A single client at 12–18 placements a week can properly read only 2–3 families in 5–6 weeks.
- So: arms stay coarse; cheap variants multiply n; the posterior is hierarchical (global → vertical group → client); and a client's estimate is shrunk toward the vertical group until it has ≥15 posts in that arm.

**Reporting:**
- Decisions use posteriors, not p-values.
- Never call anything a "winner" without an interval and n, e.g. "P(beats median) = 0.83, n = 9".

---

## F. Campaign design

### F1. Skeleton (always in this order)

1. Objective and metric (from A).
2. **Single-minded message.**
3. **Big idea = hero series.**
4. Supporting series.
5. Conversion layer.
6. Offer (if needed and approved).
7. Channel roles.
8. Calendar and phases.
9. Worker asks.
10. AI work.
11. Measurement.
12. Decision rules.
13. Learning questions.
14. Owner asks.
15. Risks.
16. Red-team revision.

### F2. Single-minded message and hero series

**The single-minded message:**
- one sentence in Russian;
- a true, ledger-backed claim that resolves the top tension;
- something the customer cares about;
- not a slogan, and not a superlative.

**The big idea** is a **repeatable platform**, not one big video. It is a named series with:
- a fixed recognisable opening, the same first-frame type and title card;
- a fixed engine;
- a variable insight per episode;
- a cadence (1–2 per week).

Choose it in two steps:
- **Week 1:** the engine with the highest value among those that fit the top tension.
- **Week 4:** the engine family with the highest posterior on the primary metric (R7).

**Why a series:**
- it compounds recognition (follow driver);
- it turns production into a routine staff can repeat;
- each episode is an observation in the same arm, which speeds up learning.

**Naming rule:** short, in the customer's words, says what you get. Examples: «Вопрос из WhatsApp», «Руки мастера», «Один рецепт — две линзы».

### F3. Supporting series (2–3)

- **Reach:** process, sound or POV.
- **Proof:** comparison, check, before/after.
- **Utility:** care, how to choose.
- **Conversation:** ranking, guess, reply-to-comment.

Each series has a role tied to a funnel stage and a metric.

### F4. Offer policy

- **Default: no offer.** Insight-led content plus the conversion layer usually beats discounts for small shops, and discounts are the owner's money.
- Already-published offers may be used as published (cite the URL), with no invented end dates.
- If the objective needs a conversion push, propose **non-price offers first**, each needing owner confirmation:
  - free fitting, tuning or adjustment;
  - a free consultation by WhatsApp video;
  - gift wrap;
  - a reservation hold;
  - an existing delivery threshold.
- Any new offer is sent to the owner as exact text with dates, limits and stock, and becomes a ledger fact only after a "да".
- An offer can be a test arm only if the owner accepts ending it.

### F5. Funnel and channel roles

| Channel | Role | Content | Metric |
|---|---|---|---|
| TikTok | Reach to strangers, local search | All series | views ÷ median, shares and saves per 1k, profile visits |
| Instagram Reels plus profile | Reach, plus the "shop window" where KZ buyers check legitimacy | All series. Stories for proof and behind-the-scenes. Highlights: «Как заказать», «Цены» (if allowed), «Отзывы». | saves, profile visits, link taps |
| YouTube Shorts | Search and long tail | Answer and comparison series | 30-day views |
| WhatsApp chat | **Conversion** | Per-video codes, reply scripts | coded chats, reply time, chat → sale |
| WhatsApp Status | Warm contacts: repeat and referral | The best videos of the week, behind-the-scenes | Status views, replies |
| Kaspi | Checkout and trust (if the client sells there) | Linked from WhatsApp replies | SKU sales vs baseline |
| 2GIS / Maps | Trust and visits | A review-request flow after purchase | new reviews, rating |
| Telegram | Only if the client already runs a channel | Reposts | — |
| Paid boost (optional) | Amplifier of **proven** organic posts | Click-to-WhatsApp (Meta) with a city or radius target; platform promote tools for views | cost per coded chat |

**One-time profile setup** (owner approves once):
- the bio says what, where and how to order, with a wa.me link carrying a code;
- the city goes in the name or bio field (for search);
- 3 pinned videos: who we are, proof, how to order;
- highlights as above.

**WhatsApp layer:**
- **Per-video code:** a short Cyrillic word plus a number, e.g. «ВОПРОС3». It appears on screen in the last 2 s, in the caption, and in a prefilled wa.me link: «Здравствуйте! Код ВОПРОС3. Хочу узнать…».
- The agent drafts a **greeting / away message** and **quick replies** from the language bank, and the owner approves them once.
- **First-reply rule:** answer + one question + a clear next step («Пришлите фото/размер — подберём 3 варианта в наличии»).
- Fallback attribution question: «Подскажите, откуда о нас узнали?»
- **Reply-time target** during working hours, set with the owner. It is measured from the export, and a slow reply time is reported as a bottleneck.
- Offline visits: «назовите на кассе слово X».

**Boost rules:**
- Only posts in the top 20% of the campaign on the primary metric, after the 48 h read.
- Click-to-WhatsApp objective for conversion goals.
- The owner sets the budget and the maximum cost per coded chat.
- Stop when the cost per coded chat exceeds that cap after the minimum spend the owner set.
- Never boost an untested post. Never boost content with an unconfirmed offer.

### F6. Calendar and phases

| Phase | Weeks | Goal | Allocation |
|---|---|---|---|
| Explore | 1–3 | Breadth: ≥5 families tried; baseline medians established | ≥50% explore |
| Focus | 4–6 | Hero series fixed (R7); follow-ups of winners | 50/25/25 |
| Scale | 7+ | Boost proven posts; moments; cross-client remixes | Thompson with floors |

**Weekly rhythm:**

| Day | What happens |
|---|---|
| Mon | Ingest metrics and codes, update posteriors, re-rank insights, generate ≥20 new ideas, select the slate, write the shoot card |
| Tue | Staff shoot, ≤20 min |
| Tue–Wed | Edit, design, checks, variants |
| Wed | Owner approval, ≤5 min, one tap per video |
| Wed–Sun | Publishing on schedule |
| Daily | Comment replies (drafted, approved), code counting |

**Other calendar rules:**
- **Moments** enter the calendar 10–14 days before the date, because shooting and approval need lead time.
- **Posting times:** start in the evening (19:00–22:00 local) and at lunch, then let the account's data move them. Never block an idea on timing.

### F7. Worker asks (shoot card spec)

**Delivered as one WhatsApp message to staff, in Russian:**
- the total minutes;
- locations in walking order;
- per shot:
  - one physical action;
  - where;
  - seconds × takes;
  - who (a role, or a name if the person agreed);
  - what to say (≤12 words, own words allowed, no claims);
  - face needed: yes or no, with the face-free alternative;
  - a sound note;
  - optionally a reference frame image;
- the capture-on-the-fly asks;
- the weekly question («Запишите голосовое на 30 секунд: какой вопрос вам чаще всего задавали на этой неделе?»);
- the "send as a file" reminder;
- the phone rules from D9 (short).

**Ask design:**
- Asks are actions, not creative tasks. "Play 15 seconds" is an action; "make something funny" is not.
- Never more than 3 locations.
- First week: one free shot of their choice. It builds ownership, and it is often the best clip.

**Feedback to staff:**
- After each week, send 1 line about results («ваш ролик с мастером посмотрели 8 400 раз»).
- Any bonus is the owner's call.

**Track:**
- completion rate;
- minutes actually used;
- which asks fail (simplify those first).

### F8. AI work per video (production package)

For each video:
- the edit recipe;
- on-screen text and its design brief;
- RU (and KK) subtitles;
- 2–3 hook variants;
- the cover frame;
- the caption, with search phrase, city and code;
- the voice-over source;
- any AI visual, with its label;
- licensed audio;
- the checks list (truth rails on every string, safe area, pacing in the first 3 s, consent, AI labels);
- the approval card (hook + 1-line why + fact sources).

Approval is bound to the hash of the final file and caption. **Owner rejection reasons are taps:** «неправда», «нельзя показывать», «не наш стиль», «другое». They feed the constraints.

### F9. Measurement

- **Before week 1, capture the baseline:**
  - coded and uncoded chats per week (export);
  - relevant SKU sales or bookings;
  - account medians per platform.
- **Reads:**

| When | What |
|---|---|
| 2 h | Reply to comments only; no decisions |
| 48 h | Main per-post read |
| 7 d | Final per-post read |
| Weekly | Campaign read |
| Week 4 | Phase review |

- **Attribution caveats:**
  - codes undercount, because many people don't type them;
  - triangulate with «откуда узнали» answers, Kaspi SKU uplift vs the prior 4 weeks, and Status replies;
  - report coded counts as a floor, not the total.

### F10. Decision rules

- **R1 Winner candidate.** A post at 48 h with views ≥3× median, or (shares + saves) per 1k ≥2× median:
  - 2 follow-ups next week (same insight and engine, new hook or angle);
  - pin it if it is conversion-relevant;
  - post it to WhatsApp Status;
  - it becomes boost-eligible (R8).
- **R2 Distribution miss.** Retention ≥ median but views ≤0.5× median:
  - post on the other platforms now;
  - one repost with a new first frame on the same platform after ≥7 days (maximum once).
- **R3 Content miss.** Views around the median but retention below the median:
  - log it;
  - next time shorten it, move the payoff earlier, and change the opening;
  - no repost as is.
- **R4 Conversion-layer miss.** Campaign views on plan but coded chats below 30% of plan:
  - before making more content, check CTA visibility, the profile and link, and WhatsApp reply time;
  - fix the layer.
- **R5 Sales-handling miss.** Coded chats on plan, sales low:
  - send the owner a WhatsApp-evidence report (where chats die);
  - draft reply scripts;
  - the offer or price is the owner's call.
- **R6 Engine families.**
  - P(beats client median) <0.2 after ≥8 posts: cut to the 10% floor. Do not kill it entirely; pooled data may revive it.
  - P >0.8: raise its share. Never to 100%.
- **R7 Hero series at week 4.** The family with the highest posterior on the primary metric that also fits the single-minded message. Others go to supporting cadence.
- **R8 Boost.** Only R1 posts that are relevant to the primary metric, within the owner's caps.
- **R9 Staff.** Card completion <80% for 2 weeks: fewer locations, face-free, shorter takes.
- **R10 Owner.** Rejections >30%: read the reasons and update constraints and tone. On fact rejections, fix the ledger.
- **R11 Stop-loss at week 6.** Primary metric <25% of target and no family above 1.5× median:
  - send an honest report with pivot options: a different bottleneck, the warm base, an offer, a boost, or pause.
- **R12** Never delete underperformers, since that destroys data. Never announce a winner without an interval.

### F11. Learning loop

**Per post, log:**
- client, vertical group;
- engine, family, driver, insight type;
- mode, face, language, trend, length, hook type;
- platform, post time;
- outcomes at 48 h and 7 d;
- codes.

**Weekly:**
- update the client posteriors;
- refresh insights from new chats, comments and the staff voice note;
- graveyard failed hooks;
- remix winners: same engine, new insight, or same insight, new engine.

**Monthly, across clients:**
- pool by family × vertical group;
- update shared priors;
- re-fit rubric weights per vertical group once there are ≥30 posts per arm;
- re-calibrate the judge on our own posts (its authority changes only with measured correlation and a CI).

**`learnings.jsonl` entry:** `{id, vertical, finding, use, n, interval, source, date, strength: measured | correlational | expert_judgment}`. Nothing becomes a rule unless its interval excludes "no effect".

### F12. Red team and revision

Before sending, three passes attack the campaign:
1. **The client's boss:** "Would I approve and pay for this? What is wrong about my business here?"
2. **A veteran CIS short-form creator:** "Would this stop me in the feed? Is it cringe? Can a shy cashier film it in 20 minutes?"
3. **A truth auditor:** every claim against the ledger.

Each fatal or major point is fixed by changing the plan, not the wording.

### F13. Weekly owner report (Russian, 5 lines, with a single ask)

> Неделя {N}: вышло {k} роликов. Лучший — «{название}»: {просмотры} просмотров, {сохранения} сохранений (в {x} раза выше обычного).
> Написали в WhatsApp по кодам: {n} (на прошлой неделе {m}).
> Что делаем дальше: {одна фраза}.
> Что нужно от вас (≤5 минут): {одно действие}.
> На согласование: {k} роликов — ответьте цифрами, какие публикуем.

---

## G. Output contract

All objects are JSON, saved per step, with IDs referenced across steps. Fields marked `+` extend the current `smm/brain.py` schemas. Audience-, owner- and staff-facing strings end in `_ru` (or `_kk`).

### G1. IntakeBrief

```yaml
client_id: str
request_raw: str                     # + verbatim, with sender/channel/date
request_type: enum[sales_push, launch_or_event, awareness_or_viral, reputation_or_trust, price_pressure,
                   retention_or_loyalty, hiring, b2b_leads, should_we_do_social, other]
secondary_requests: [str]            # + split-off parts → backlog
reframed_request: str
so_that_what_ladder: [str]           # + steps down to the business number
business_objective: str              # number + unit + date
bottleneck: {stage: enum[awareness, consideration, conversion, retention, non_marketing],
             evidence: [str], confidence: enum[verified, likely, assumption]}   # +
marketing_objective: str             # who (situation) moves from → to
success_metric: {name, how_measured, baseline, target_conservative, target_expected, target_stretch, by_when}
leading_indicators: [str]            # 2–4
guardrails: [str]                    # +
stretch: str                         # + labelled "plausible, not guaranteed"
constraints: [{type, rule, source, is_default: bool}]
conflicts: [{a, b, resolution, default, owner_can_flip: bool}]   # +
non_marketing_issues: [{issue, evidence, proposed_fix, owner_action}]   # +
refused_parts: [{request_part, why, honest_alternative}]   # +
push_back: str                       # plain English; push_back_ru for the owner
push_back_ru: str                    # +
assumptions: [{text, impact_if_wrong, how_to_verify, by_when}]
clarifying_questions: [{q_ru, options_ru: [str], default, deadline, why}]   # maxItems 3
```

### G2. InputChecklist

```yaml
have: [{input, source, fetched_at, what_it_gives}]
missing: [{input, rank, why_it_matters, how, who: enum[agent, owner, staff, customer],
           owner_minutes: num, fallback_if_missing, blocks_step, status: enum[todo, requested, received, blocked],
           due}]
owner_message_ru: str                # + the single bundled onboarding/weekly message
total_owner_minutes: num             # + must be ≤15 (onboarding) or ≤5 (weekly)
privacy_actions: [str]               # + e.g. "export anonymised on ingest"
```

### G3. EvidenceBase

```yaml
facts: [{id: "F###", type: enum[price, stock, offer, policy, spec, internal_number, owner_statement, category_knowledge],
         text, value, source, provenance: enum[site, kaspi, owner, count, manufacturer, authority], fetched_at, expires_at}]
evidence: [{id: "E###", kind: enum[fact, customer_language, behaviour, proof_asset, moment, constraint, market, performance],
            claim, verbatim_ru, tags: [str], jtbd_force: enum[push, pull, anxiety, habit, none],
            source, fetched_at, confidence: enum[verified, likely, assumption], count, source_count,
            use_rights: enum[public, paraphrase_only, internal]}]
language_bank: [{cluster, phrases_ru: [str], evidence_ids}]     # +
content_reality_inventory: [{kind: enum[sound, process, ritual, person, place, number, object, situation],
                             description, location, consent_status, staff_minutes_to_film, evidence_ids}]   # +
baselines: {chats_per_week, sales_metric, platform_medians: {tiktok, reels, shorts}, source, period}   # +
```

### G4. InsightList

```yaml
insights: [{id: "I##", type: enum[tension, belief, moment, proof, content_reality, objection, local],
            insight: str,                 # English
            tension_ru: str,              # «Хочу…, но…, поэтому…» in customer words
            resolution_truth: str,        # + what is true and showable; fact_ids
            who_feels_it: str, trigger_moment: str,      # +
            evidence_ids: [str], proof_ids: [str], fact_ids: [str],
            content_reality: str,
            scores: {evidence, intensity, leverage, showability, distinctiveness, proof},   # 0–3 each
            strength: int,                # 0–18
            use_limits: str}]             # + e.g. "proof=0 → question content only"
top_for_ideas: [str]                      # + 5–8 ids, type-diverse
version: int                              # + bumps when new inputs arrive
```

### G5. IdeaList

```yaml
ideas: [{id: "ID##", title, insight_ids: [str], engine: "E##", family: "F#",
         driver_primary, drivers_secondary: [str],
         funnel: enum[attention, consideration, conversion, trust, retention, recruiting],
         format: "P#", length_s: int, language: enum[ru, kk, ru+kk_captions], register: enum[vy, ty],
         hooks_ru: [{variant: enum[statement, question, visual_only], text_ru, first_frame}],   # 3
         first_frame: str,
         beats: [{t_from, t_to, visual, audio, on_screen_ru}],     # shot-level timeline
         payoff: str, ending: enum[loop, cta, question],
         why_stop, send_to_whom, why_share_or_save,                 # send_to_whom +
         comment_prompt_ru, cta_ru, wa_code,                        # wa_code +
         production: {mode: enum[worker, ai, mixed, ugc, screen, existing_assets], face_required: bool,
                      face_free_alternative: str,
                      worker_shots: [{what_ru, location, seconds, takes, say_ru,
                                      kind: enum[hook, demo, talk, detail, process]}],
                      staff_minutes: num, ai_parts: [str], ai_tier: enum[T0, T1, T2], credits: num,
                      people_on_camera: int},
         trend: {name, expires, card_id} | null,
         facts_used: [str], needs_facts: [str],
         gates: {truth, not_ad, producible, consent_legal, brand_safety, insight_cited},   # bool each
         rubric: {stop, truth, share_save, comment, producible, brand_link, objective_fit},   # 1–5
         prior: num, novelty: num,
         kpi: str, risks: [str]}]
```

### G6. TestPlan (weekly)

```yaml
week: int
phase: enum[explore, focus, scale]
staff_minutes_planned: num           # ≤20, from the optimiser
slate: [{idea_id, slot: enum[exploit, explore, follow_up], arm_family, arm_engine, value, why,
         variants: [{variant_id, change: enum[hook, first_line, length, language, cover, cta], placement}],
         platforms: [str], post_at, wa_code, needs_facts: [str]}]
blocked: [{idea_id, gate_failed, fix_needed}]
diversity_check: {families, engines_max_per, insights, save_led, share_comment_led, conversion_ready,
                  trend_count, face_share, passed: bool}
arms: [{arm_id, level: enum[family, engine, dimension], prior_source: enum[neutral, pooled, client],
        n, p_beats_median, interval}]
primary_post_outcome: enum[y_reach, y_res]
reads: {h48, d7}
decision_rules: [str]                # F10 rules instantiated with numbers
learning_questions: [str]            # what we will know by week N
shoot_card_ru: str                   # the staff message
```

### G7. Campaign

```yaml
name: str
objective_ref: IntakeBrief.id
single_minded_message_ru: str        # + with fact_ids
big_idea: str
hero_series: {name_ru, engine, opening_ritual, cadence, why_this_series}      # +
series: [{name, role, funnel_stage, engines: [str], idea_ids: [str], cadence, metric}]
conversion_layer: {wa_codes_scheme, prefilled_text_ru, greeting_ru, quick_replies_ru: [str],
                   reply_time_target, profile_setup: [str], status_plan}     # +
offer: {needed: bool, proposal_ru, type: enum[none, existing_published, non_price, price],
        fact_ids: [str], needs_owner_approval: bool, end_date}
channels: [{channel, role, content, metric}]
boost: {allowed: bool, budget_cap, max_cost_per_coded_chat, eligibility_rule}    # +
phases: [{name, weeks, goal, allocation}]                                       # +
weeks: [{week, goal, idea_ids, worker_ask_ru, ai_work, moments: [str]}]
measurement: {success_metric, baseline, attribution: [str], leading_indicators, reads, review_cadence}
decision_rules: [str]
learning_questions: [str]
owner_asks: [{ask_ru, why, minutes, default_if_no_answer}]
risks: [{risk, mitigation}]
red_team: [{persona, refutations: [{target, why_fails, severity: enum[fatal, major, minor], fix, applied: bool}]}]   # +
owner_report_template_ru: str        # +
```

---

## H. Worked mini-example

**Hypothetical client.** Every business fact below is an assumption, marked **[A]**, and none describes a real company.

**Client:** a fictional optics salon, «Оптика N» [A].
- Karaganda, one salon [A].
- Staff: 1 optometrist and 2 consultants, all shy on camera [A].
- Sells frames, spectacle lenses and contact lenses; eye tests are by appointment [A].
- Bookings and questions arrive in WhatsApp [A].
- An Instagram account with about 1,200 followers and product-photo posts; no TikTok [A].

**Boss request (voice note):**
> «Хочу, чтобы про нас узнал весь город. Сделайте вирусное видео. Только девочки сниматься не хотят.»

### H1. IntakeBrief (compressed)

- **request_type:** `awareness_or_viral`
- **Ladder:** весь город узнал → больше людей запишутся на проверку → больше заказов очков. **Business number:** eye-test bookings per week via WhatsApp.
- **Bottleneck:** awareness + consideration (hypothesis, `likely`). Reviews suggest a fear of being upsold (E1). Confirm with the WhatsApp export.
- **marketing_objective:** people whose sight has changed, or whose child squints, move from «откладываю, боюсь, что разведут на дорогие очки» to «пишу в WhatsApp, чтобы записаться на проверку».
- **success_metric:** coded WhatsApp booking requests per week.
  - Baseline: from the export (week 0) [A: about 10/week].
  - Targets by week 6: conservative 12, expected 15, stretch 20.
- **Leading indicators:** views ÷ median, saves per 1k, profile visits, Karaganda share of the audience (IG insights).
- **Stretch:** ≥1 post at ≥5× median within 6 weeks, plausible, not guaranteed.
- **Constraints:**
  - faces off, so hands and voice only;
  - regulated-adjacent (vision), so no diagnosis or treatment claims;
  - no prices until a price list arrives;
  - children only with a parent's written consent.
- **Conflict:** «вирусно» + «не сниматься». Resolution: face-free sound, process and POV modes. Optional: the owner's voice as the narrator.
- **push_back_ru:**
  > «Гарантировать вирусность не может никто: даже крупные блогеры не знают заранее, какой ролик выстрелит. Поэтому мы делаем много разных коротких роликов — честно про вашу оптику, без лиц, руками и голосом — и по цифрам усиливаем те, что сработали. Главная цифра — сколько людей написали вам в WhatsApp с кодом из видео.»
- **Questions:**
  > 1) Цены оправ и линз в видео: 1 — можно (пришлите прайс), 2 — нельзя. *По умолчанию — нельзя.*
  > 2) Голос за кадром: 1 — ваш, 2 — сотрудника, 3 — синтезированный (мы подпишем). *По умолчанию — 3.*
  > 3) Правда ли, что вы не навязываете покупку после проверки (например, рецепт отдаёте на руки)? 1 — да, 2 — нет / по-другому (напишите). *До ответа это не утверждаем.*

### H2. Inputs

| Status | Inputs |
|---|---|
| Have (Tier 0) | Instagram history; 2GIS reviews [A: about 40]; peer accounts (local optics, CIS optometry creators); search phrases («проверить зрение Караганда», «очки для ребёнка», «тонкие линзы») |
| Requested | WhatsApp export (2 min), voice note (3 min), price-list photo (2 min), permissions (1 min), camera roll (3 min), staff phone test (10 staff min) |
| Fallbacks | No export: language from reviews, conversion bottleneck stays an assumption. No price list: E05 and E25 ideas blocked. |

### H3. Evidence (all hypothetical, labelled)

| ID | Kind | Claim | Source [A] | Confidence |
|---|---|---|---|---|
| E1 | customer_language | «Думала, будут навязывать дорогие линзы, а подобрали недорогие» (5 similar reviews) | 2GIS reviews | likely |
| E2 | customer_language | «Сколько стоит проверка зрения?» is the most frequent first message | WhatsApp export | assumption until the export |
| E3 | customer_language | «С ребёнком 6 лет можно?» recurring | WhatsApp export | assumption |
| E4 | behaviour | Chats stop after a lens price is sent with no explanation | WhatsApp export | assumption |
| E5 | proof_asset | Frames are adjusted by hand on the spot | owner voice note | assumption |
| E6 | content_reality | A lens-edging machine (sound, process); lens samples of different thickness exist | owner / phone test | assumption |
| E7 | moment | Late August: school start, parents notice squinting | calendar | likely |
| E8 | performance | Product-photo posts sit far below peer medians | IG history vs peers | likely |
| F1 | fact | The eye test price, or whether it is free with an order | price list | **missing → question** |

### H4. Insights (top 4)

| ID | Type | Tension / truth | Scores (ev / int / lev / show / dist / proof) | Strength |
|---|---|---|---|---|
| I1 | tension | «Хочу проверить зрение, но боюсь, что проверка — повод продать дорогие очки, поэтому тяну». Truth: show what really happens at the test; confirm the policy (Q3). | 2 / 3 / 3 / 3 / 2 / 2 | 15 |
| I2 | objection | «Почему линзы стоят по-разному?» Chats die after the price. Truth: the same prescription in two lens types shows a visible thickness difference (category knowledge, optometrist confirms). | 1 / 2 / 3 / 3 / 2 / 3 | 14 |
| I3 | content_reality | Hand adjustment of crooked frames is a satisfying, audible process outsiders never see. | 1 / 1 / 2 / 3 / 3 / 3 | 13 |
| I4 | moment | «Ребёнок пошёл в школу и щурится». Truth: show what a child's check looks like. Symptom claims need an authoritative source plus optometrist sign-off. | 1 / 3 / 2 / 2 / 1 / 1 | 10 |

### H5. Ideas (10 of the ≥24 written; prior = Σ w·s / 39)

| ID | Engine | hook_ru (variant a) | Mode | Staff min | s / t / ss / c / p / b / o | Prior | Gate notes |
|---|---|---|---|---|---|---|---|
| ID01 | E01 Вопрос из WhatsApp | «Нам пишут: „Проверка зрения — это чтобы продать очки?“» | P1 + P7 | 2.5 | 3/4/3/4/5/4/5 | 0.79 | Needs the Q3 answer for the payoff |
| ID02 | E08 A vs B | «Один рецепт. Две линзы. Видите разницу?» | P5 | 1.0 | 4/4/4/3/5/3/4 | 0.78 | No prices unless the price list arrives |
| ID03 | E14 + E10 | (no words) close-up of hands bending a frame + «Кривые очки — 30 секунд» | P4 | 1.8 | 4/5/3/3/5/4/3 | 0.76 | Free adjustment? Not claimed until confirmed |
| ID04 | E15 Что вы не видите | «Что на самом деле происходит на проверке зрения» | P2 | 3.0 | 3/5/3/2/4/5/5 | 0.77 | Needs a consenting customer → week 2 |
| ID05 | E07 Уход | «Почему очки нельзя протирать футболкой» | P1 | 1.5 | 3/3/5/3/5/2/2 | 0.66 | Optometrist confirms the care facts |
| ID06 | E23 Тир-лист | «Ранжирую оправы: какие чаще приносят чинить» | P1 | 2.0 | 3/3/3/5/4/4/3 | 0.69 | Labelled as the master's opinion |
| ID07 | E12 Цифра | «Сколько очков у нас забыли за год» (the lost-and-found shelf) | P4 | 1.0 | 4/3/4/4/5/5/2 | 0.75 | **Blocked:** needs a counted fact |
| ID08 | E26 Момент | «Ребёнок щурится у доски? Вот как проходит детская проверка» | P2 | 2.5 | 4/2/5/3/4/2/4 | 0.72 | **Parked:** health claims need a source and sign-off; child consent |
| ID09 | E17 POV | «POV: вы пришли „только посмотреть“» | P2 | 1.2 | 3/5/4/4/4/3/3 | 0.73 | — |
| ID10 | E25 Угадай | «Угадайте: какие очки за {цена A}, а какие за {цена B}?» | P5 | 0.8 | 4/4/3/5/5/3/4 | 0.79 | **Blocked** until a dated price list arrives (Q1) |

### H6. TestPlan, week 1 (phase: explore)

**Slate:**

| Idea | Family | Slot | Code |
|---|---|---|---|
| ID01 | F1 | exploit | ВОПРОС1 |
| ID02 | F2 | exploit | ЛИНЗЫ1 |
| ID03 | F3 | exploit | МАСТЕР1 |
| ID09 | F4 | explore | СМОТРЮ1 |
| ID06 | F5 | explore; replaces ID10 while prices are blocked | РЕЙТИНГ1 |

**Diversity check:**
- 5 families, 5 engines, 4 insights;
- save-led: ID02, ID05 (queued for week 2);
- share- or comment-led: ID06, ID09;
- conversion-ready: ID01;
- no trends;
- 100% face-free.
Passed.

**Staff minutes:** 3 fixed + 3 locations × 2 + shots 7.3 + voice question 1 + on-the-fly ask 1 = **18.3 ≤ 20**.

**Variants and placements:**
- 2 hook variants per base video (ID01 gets 3), edit-only.
- Variant A goes to TikTok and Reels. Variant B goes to an Instagram trial reel where available, otherwise to Shorts.
- That gives about 13 placements.

**Arms:** families F1–F5, with neutral priors blended with pooled considered-retail priors. Primary per-post outcome: `y_reach`. Coded chats are read at campaign level.

**Rules instantiated:**
- R1 at 3× the peer median, until 10 own posts exist.
- R4 if coded chats are below 30% of the 15/week plan by week 3.

**Shoot card (sent to staff in WhatsApp):**

> Съёмка на неделю — 18 минут. Лица не нужны: только руки и голос.
> Перед началом: протрите камеру, выключите музыку, телефон вертикально, без зума.
> **1. Стол мастера (у окна).**
> 1.1 Кривая оправа крупно, 5 сек, 2 дубля. Телефон в 30 см.
> 1.2 Выправляете оправу руками, 20 сек, 2 дубля. Звук важен — телефон близко, микрофон «Стандартный».
> 1.3 Две линзы с одним рецептом рядом, ребром к камере, медленно поверните, 15 сек, 2 дубля.
> **2. Витрина.**
> 2.1 Снимите от входа, как будто вы покупатель: идёте к витрине, берёте оправу, 20 сек, 2 дубля.
> 2.2 Три оправы на столе, по очереди берёте каждую в руки, 15 сек, 2 дубля.
> **3. Тихое место (подсобка).**
> 3.1 Телефон у рта (30 см), скажите своими словами, как проходит проверка зрения и что человек уносит с собой. 30 сек, 2 дубля.
> 3.2 Так же: какие оправы чаще всего приносят чинить и почему, 20 сек.
> Ошиблись — пауза и повторите фразу целиком.
> **Если сегодня клиент обрадуется новым очкам** — спросите, можно ли снять 10 секунд для Instagram; если да — пусть скажет «да» в камеру.
> **В конце:** голосовое на 30 сек — какой вопрос вам чаще всего задавали на этой неделе?
> Отправляйте видео **как файл**, не как видео. Спасибо!

### H7. Campaign (6 weeks, compressed)

**Name:** «Сначала проверим».

**single_minded_message_ru:** «Сначала узнаете, что с вашим зрением, — потом решите сами.» Valid only if Q3 = 1; if not, it is rewritten from the owner's real policy.

**Hero series:** «Вопрос из WhatsApp» (F1).
- Opening ritual: the anonymised question card plus hands.
- 2 episodes per week.
- Each ends with a code: «Напишите ВОПРОС{N} — подскажем, как записаться».
- Why this series: it hits the top tension (I1) and the conversion bottleneck, is face-free, and is fed weekly by the staff voice note.

**Supporting series:**
- «Руки мастера» (F3): reach, sound and process.
- «Один рецепт — две линзы» (F2): consideration and saves.
- «Рейтинг мастера» / «Угадай» (F5): comments. «Угадай» starts once prices are allowed.

**Conversion layer:**
- wa.me links with codes in the bio and in story link stickers;
- greeting and quick replies drafted from the language bank, e.g.:
  > «Здравствуйте! Подскажите, когда вам удобно прийти на проверку — сегодня или завтра? Проверка занимает около {время из ledger} минут.»
- a reply-time target agreed with the owner;
- the week's 2 best videos go to WhatsApp Status.

**Offer:** none. Non-price candidates go to the owner for a yes or no; they are not used until confirmed. Example: free frame adjustment for anyone, if the owner confirms the salon does this.

**Channels:**
- Instagram Reels and profile: pinned «Как проходит проверка», «Один рецепт — две линзы», «Как записаться».
- TikTok: a new account, an owner ask.
- Shorts.
- WhatsApp Status.
- 2GIS: a review request after purchase.
- Boost: Click-to-WhatsApp within a city radius, only after R1 from week 3, with the owner's cap [A: owner sets it].

**Calendar:**

| Weeks | Phase | Plan |
|---|---|---|
| 1–2 | Explore | 5 base videos per week. ID04 in week 2 after the consent flow. |
| 3–4 | Focus | Hero fixed per R7; follow-ups of winners. |
| 5–6 | Scale + moment | ID08 (school start) only if a source and the optometrist's sign-off arrive. Otherwise a safe moment version: «Как выглядит детская проверка» — process only, no symptom claims. |

**Learning questions:**
- Does F1 (answers) beat F3 (process) on reach for optics, given the pooled considered-retail prior?
- Do face-free answer videos still produce coded chats?
- Where do chats die after the code (from the export)?

**Owner asks:**

| Ask | Minutes | Default if no answer |
|---|---|---|
| Approve the week-1 batch | 4 | nothing is published |
| Price list | 2 | no price ideas |
| Q3 policy | 1 | no "без навязывания" claim |
| TikTok account | 5 | Reels and Shorts only |

**Red-team fixes applied:**
- (creator, major) The ID03 opening was static → it now starts mid-bend with the click sound.
- (boss, major) «Без навязывания» could insult customers who were upsold elsewhere and invites challenge → the message is framed as the order of steps, not as an attack on others.
- (truth, fatal) ID08 symptom list → parked until sourced.

**Owner report, week 1 (template filled by the agent after the reads):**
> Неделя 1: вышло 5 роликов. Лучший — «Кривые очки — 30 секунд»: {N} просмотров, {k} сохранений. Написали по кодам: {n}. Дальше: ещё 2 ролика «Вопрос из WhatsApp» и продолжение про оправы. От вас (2 минуты): фото прайса — тогда добавим «Угадай цену». На согласование 5 роликов — ответьте цифрами, какие публикуем.