# Seen up close, at full price (price_pressure, Шымкент beauty salon, HYPOTHETICAL client, sprint 2026-10-19 → 2026-11-15) — revision 2

**Request:** Конкуренты дешевле, клиенты уходят. Что делать?
**Reframed:** «Конкуренты дешевле, клиенты уходят. Что делать?» → Keep current prices and win back booking volume by finding where clients are lost, then using real hands-and-process content plus a tighter WhatsApp reply layer to show what the price pays for, with coded bookings steered to masters and time slots that have free capacity.
**Success metric:** WhatsApp bookings at current (undiscounted) prices per week. Coded bookings are reported as a floor and total bookings vs baseline as an estimate. — target Conservative: weekly bookings at baseline (decline stopped). Expected: +10% vs baseline. Stretch: +20% vs baseline. All at unchanged prices. Baseline: unknown (ledger empty). It comes from the export of the last 4 weeks, or from the week-0 count if there is no export, and the multiple is fixed at the end of week 2. by 2026-11-15 (Weekly WhatsApp chat export plus admin labels «Видео» and «Записан». Per-video codes are counted in the chats. Total weekly bookings come from the same export, compared with the 4 weeks before 2026-10-19. Chat-to-booking rate = chats labelled «Записан» ÷ all new inbound chats.)

**Push back:** Мы — ИИ-ассистент, и снижать цены вслед за соседями не предлагаем: в роликах мы не сравниваем себя ни с кем и никого не называем, а показываем руками мастеров, за что люди платят у вас. Сначала проверим по переписке, где теряются клиенты: если запись срывается из-за долгого ответа или потому что после цены не предложили следующий шаг, это быстрее исправят готовые ответы в WhatsApp, а не видео. Гарантировать, что ролик «залетит», не может никто; успех считаем по записям в WhatsApp по коду из ролика, а не по просмотрам. За 4 недели только роликами много новых клиентов не придёт, поэтому самый быстрый рычаг — вернуть тех, кто уже был у вас: через статусы и рассылку тем, кто на неё согласился.

## Big idea
A client compares prices because she cannot see what the price pays for: the hygiene before she sits down, the steps and time a careful master takes, and the master's judgment. So every week we show those things up close, at 20 cm, on real hands, with no comparison to anyone. We start with the clients who already know us and the services that have free slots. This gives at least 20 episodes: hygiene and prep steps for each service, the process of each service, what a master refuses, what she checks, care between visits and preparing for a той, across nails, hair and brows. It can be proven on camera because only real routine is filmed. It points at one action: a coded WhatsApp chat asking for a free slot, booked through the salon's own number.

> Смотрите, за что вы платите

This is a plan that lets audience data choose, not a forecast (L1, L001, L003). The message has no price, number or comparison, so it needs no ledger fact (facts_usable is empty). It is true by construction, because every episode only shows routine the owner or master has confirmed and the camera has filmed.

What changed from revision 1, and why:
(1) The fatal gap is closed. The brief is «зачем платить больше», so the hero is now the proof series «Вблизи у мастера» (I01 price_value: E04, E05, E06, E13, E16; I07 content reality: E21, E22). It leads week 1 with a hygiene episode and a process episode. The ASMR loop (ID01) and the anti-sell wildcard (ID19) no longer lead the salon's first public week.
(2) The fastest lever gets the effort. REALISM gives organic reach a ratio of 0.6–5.9, so weeks 1–2 put about 40% of effort into the warm base. That means personal reactivation messages to clients who haven't come in for 6–10 weeks (I10: E32, E05, E03), plus Status. This arm is measured on its own.
(3) The owner's master-flight risk (I08: E26) is built in. By default, masters are not named in public, every episode is salon-branded, and booking goes only through the salon number. The 'meet the master' promise is dropped, so the person series is honestly called «Мастер считает».
(4) Free capacity drives the slate. At least 2 of the 4 week-1 videos are on the service the owner names as having free slots, which is non-nail by default.
(5) Kazakh is the default for the той series. Masters dictate and check the Kazakh lines, which satisfies L9.
(6) Attribution works by tapping. Prefilled wa.me links carry the code, Instagram Direct is added, and the admin's «откуда узнали?» question is the primary source.

Other insights in use: I05 for the той moment (E19, E20), I06 for hidden knowledge (E23, E17, E25, E30), I09 for the honest-signal wildcard (from week 3, only with the owner's «да»).

Caveat: every insight is assumption-only (strength ≤2). Step 3 is rerun on the export and the 2GIS fetch by 2026-10-16, and step 4 is rerun the same day to produce the two hero episodes (NEXT BATCH).

Learning plan: video arms are read by series with relative views plus shares and saves until there are 20 attributed chats. The reactivation arm is read separately by bookings per 100 messages. The bilingual vs KZ-only test runs on the той series.

## Test slate (picked by code: rubric prior + data + diversity)

### ID15 · POV: the той is tomorrow and the nails aren't done  (prior+data, prior 3.487, staff 2.6 min)
- Hook: «POV: завтра той, а маникюра нет»  — first frame: Bare-nailed fingers are already drumming nervously on the table next to a phone calendar. Text upper-middle, plus a small «постановка» label.
- What happens: 0–1 s: nervous drumming. 1–4 s: fingers scrolling chats (screen blurred). 4–10 s: hands now at the manicure table, with the master's hands working. 10–13 s: payoff, the finished nails holding a той-style glass or fabric. 13–15 s: CTA. Staged and labelled. Series «Перед тоем», ep. 2. DM line: «это ты перед каждым тоем».
- Why stop / share: An instantly recognisable local situation in the viewer's own words. Motion from frame 1. / Sent to a sister or friend who always leaves it to the last day.
- Driver · engine · funnel: identity () ·  · attention
- Production: worker; AI: Text beats, «постановка» label, blur on any screen, RU captions. Optional KZ caption after a native check.
- KPI: Driver: shares per 1k. Business: coded chats with event dates.; WhatsApp code: BA23
- **Needs confirmation:** ID15.comment_prompt_ru: scarcity/urgency claim without a backing fact: 'последний день'

### ID19 · WILDCARD anti-sell: when you don't need a salon  (prior+data, prior 3.462, staff 2.2 min)
- Hook: «Честно: иногда салон вам не нужен»  — first frame: The master's hands put the file down and push the tools away (motion in frame 1). Her voice starts at 0.3 s. Text upper-middle.
- What happens: 0–1 s: tools pushed away. 1–12 s: the master's opinion on small things that are fine at home between visits, over hands. 12–20 s: the turn, what she thinks should not be done at home and why. 20–23 s: payoff and CTA. Framed as opinion. No other salon is mentioned or implied. DM line: «вот, даже мастер говорит, можно дома».
- Why stop / share: A salon arguing against its own sale breaks the expected ad voice in the first second. / Saved for home care. Sent to a thrifty friend.
- Driver · engine · funnel: honest_signal () ·  · trust
- Production: mixed; AI: Voice over hands B-roll from library/week1/ (ID01, ID24), labels «Мастер считает», RU captions.
- KPI: Driver: shares and saves per 1k. Business: coded chats and chat→booking rate.; WhatsApp code: BA24

### ID20 · Less than a week to the той: what to book  (prior+data, prior 3.372, staff 2.7 min)
- Hook: «До тоя меньше недели? Что успеть»  — first frame: The master's hands are already holding a colour palette next to a fabric swatch, flipping through the shades. Text upper-middle.
- What happens: 0–1 s: palette flip. 1–14 s: the master's practical advice, each point over a hands shot. 14–18 s: payoff, the chosen shade on the finished nail next to the fabric. 18–21 s: CTA with the event date, steered to free weekday slots once question 3 is answered. Series «Перед тоем», ep. 3. Publish 10–14 days before a peak той weekend.
- Why stop / share: A precise time-bound situation the viewer is in right now. / Saved for the next той. Sent to whoever is organising the women's side of a family той.
- Driver · engine · funnel: moment_trigger () ·  · conversion
- Production: worker; AI: Advice text beats, RU captions, optional KZ caption after a native check. Calendar timing set by the agent.
- KPI: Driver: saves per 1k. Business: coded chats with an event date and bookings on free slots.; WhatsApp code: BA25
- **Needs confirmation:** ID20.on_screen_ru[2]: scarcity/urgency claim without a backing fact: 'последний день'

### ID17 · Master character: what she won't do even if asked  (prior+data, prior 3.256, staff 4.1 min)
- Hook: «Чего мастер не сделает, даже если попросите»  — first frame: Close-up of one master's hands already working at her chair. Her own voice starts at 0.3 s (recorded close in the quiet corner). Text upper-middle.
- What happens: 0–1 s: hands at work, voice starts. 1–15 s: the master names one thing she refuses to do and why, in her own words, over her hands. 15–20 s: payoff, a close-up of her signature detail of work. 20–23 s: CTA steering to this master's free slots. Series «Руки мастера», one master per episode (voice and hands only).
- Why stop / share: A refusal is unexpected from a salon. It promises a firm, personal opinion. / Sent to someone looking for 'a master who won't ruin things'.
- Driver · engine · funnel: mastery () ·  · conversion
- Production: mixed; AI: Voice over hands, punch-ins every 2–3 s, RU captions, cover. The master's first name appears only with her OK.
- KPI: Driver: completion and follows. Business: coded chats naming this master and their booking rate.; WhatsApp code: BA26

### ID24 · Care: make the manicure last until the next visit  (prior+data, prior 3.321, staff 2.7 min)
- Hook: «Что делать, чтобы маникюр дожил до записи»  — first frame: A drop of cuticle oil is already falling onto a finished nail in macro and spreading. Text upper-middle.
- What happens: 0–1 s: oil drop. 1–6 s: oil rubbed in. 6–10 s: hands pulling on rubber gloves. 10–14 s: payoff, a slightly lifted tip edge, the master's hand stops a finger from picking it, and the text tells you to come to the master instead. 14–17 s: CTA. Posted to WhatsApp Status for existing contacts (opted-in broadcast only). Save reason: care routine between visits.
- Why stop / share: A sensory macro drop in frame 1 plus a practical promise for current clients. / Saved by clients right after a visit. Sent to a friend who always picks at her coating.
- Driver · engine · funnel: practical_value () ·  · retention
- Production: worker; AI: Labels «Мастер советует», RU captions, cover = oil drop. A Status-format cut for the warm base.
- KPI: Driver: saves per 1k. Business: repeat bookings from existing contacts (SECONDARY objective).; WhatsApp code: BA27

### ID13 · Myth: removing gel ruins the nail  (prior+data, prior 3.269, staff 2.8 min)
- Hook: «Говорят, снятие гель-лака портит ноготь. Смотрим»  — first frame: Macro: a file is already working on gel coating at 20 cm with the sound audible. Text upper-middle.
- What happens: 0–1 s: file on coating. 1–10 s: careful removal compressed with «Ускорено». 10–15 s: payoff, an unedited macro of the nail plate after removal turned to the light. 15–18 s: the master's opinion line. 18–20 s: CTA. On a staff member's own nail with her consent. DM line: «вот, а ты сама сдираешь».
- Why stop / share: It challenges a common belief and promises to show the hidden result, the bare nail after removal. / Sent to a friend who peels off her gel herself. Saved by people deciding whether to keep doing gel.
- Driver · engine · funnel: curiosity_gap () ·  · consideration
- Production: worker; AI: Speed ramp with label, no colour grading on the after shot, RU captions.
- KPI: Driver: completion and comments per 1k. Business: coded chats per 1k.; WhatsApp code: BA28

### ID01 · Close sound: nail file and gel brush, loop  (explore, prior 3.167, staff 2.7 min)
- Hook: «Так звучит маникюр вблизи»  — first frame: Top-down macro, the file is already moving across a nail edge and fills about 60% of the frame. The rasp is audible from frame 0. Hook text fades in at 1 s, upper-middle.
- What happens: 0–1 s: file strokes with no words, only the real sound. 1–6 s: file passes along the edge, label «Пилка». 6–10 s: a slow brush pull of gel along the nail, label «Кисть с гелем». 10–11 s: payoff, the glossy finished nail turns into the light. 11–12 s: hard cut back to the first file stroke so it loops. No music. Series «Звук кресла», ep. 1. DM line: «послушай, залипательно». Save reason: a relaxing loop people replay.
- Why stop / share: Sound onset and macro motion in frame 1. It breaks the hypothesised category convention of finished nails under trending music (E25), and the weak phone's one strength (≤30 cm audio) carries it. / Sent to a friend who likes ASMR/relaxing clips: «послушай перед сном». It is a reach piece, not a reference save.
- Driver · engine · funnel: sensory () ·  · attention
- Production: worker; AI: Pick the best take, cut on sound peaks, light denoise that keeps the file sound, loop end→start, burned-in RU captions, cover = frame 1. No music. Save raw clips to library/week1/ID01_*.mp4 for reuse in ID06, ID07 and ID22.
- KPI: Driver: average % watched and replays, shares per 1k vs pooled median. Business: coded chats per 1k (expected low; DR7 watch).; WhatsApp code: BA29

### ID09 · Where a master looks first (insider eye)  (explore, prior 3.167, staff 3.4 min)
- Hook: «Куда мастер смотрит в готовом маникюре»  — first frame: Extreme macro: an orange stick is already tapping three spots on a finished nail, and the tap is audible. Text upper-middle.
- What happens: 0–1 s: tapping. 1–10 s: two insider spots, each in extreme macro with a label. 10–13 s: payoff, the nail tilted so the highlight runs straight across. 13–15 s: loop to the tap. Series «Глазами мастера», ep. 1. DM line: «смотри, теперь буду так проверять».
- Why stop / share: Insider framing («what the master sees that you don't») plus extreme macro in frame 1. / Sent so the sender looks in the know. Saved for the next salon visit.
- Driver · engine · funnel: social_currency () ·  · consideration
- Production: worker; AI: Macro labels, RU captions, loop, cover = tap frame.
- KPI: Driver: shares per 1k. Business: coded chats with nail photos.; WhatsApp code: BA32

## Weeks

- **Week 0** — Setup and diagnosis (2026-10-10 → 10-18). No posts. Collect inputs and the baseline, set up prefilled wa.me codes, quick replies, the Direct auto-reply (if available), the profile and the reality scan. By 10-16: rerun step 3 on the export and the 2GIS fetch, then rerun step 4 to produce the 2 hero episodes («Вблизи у мастера» E1 hygiene, E2 process on the free-slot service) and the non-nail ideas (NEXT BATCH). Check non-marketing causes first: reply time, clients leaving with a master, the 2GIS trend. Set up the reactivation arm: the owner approves the template once, and the admin is given the selection rule.: . Staff: Здравствуйте, это ИИ-ассистент салона. Один раз на этой неделе, ~15 минут, лица не нужны: 1) 3 пробных клипа (фраза с телефоном в 30 см, звук пилки в 20 см, общий вид зала) и 2 минуты тихой прогулки по салону с телефоном; 2) голосовое на 2–3 минуты: что вы на самом деле делаете каждый раз до того, как клиентка села в кресло (инструменты, пилка, стол), и какие шаги в услуге, где есть свободные окна; 3) мастер, которой удобно по-казахски: надиктуйте голосом 3 короткие подписи для роликов про той — текст пришлём на русском, переведите своими словами.. AI: Fetch the 2GIS card (rating, count, recurring words, services, hours, published prices with fetch date) and check Instagram/TikTok presence. Read nearby public price lists for internal context only. Ingest and anonymise the chat export (cust_###). Compute where chats die, median first reply, close rate and the 4-week baseline. Draft the 4 quick replies, the reactivation template and the Direct auto-reply. Build prefilled wa.me links per video and per series. Rerun steps 3 and 4: hygiene and process episodes for the hero (only steps the voice note and owner confirm), plus brow and hair episodes. Transcribe the KZ hook lines as dictated, word for word, without editing. Recompute REALISM. If the export shows slow replies or master-linked churn, send the owner a 1-line Russian note that content is not the first fix (DR0).
- **Week 1** — Explore (2026-10-19 → 10-25). Two jobs.

(A) WARM BASE, about 40% of effort. The admin sends approved reactivation messages to clients lapsed 6–10 weeks (up to 20/day, slots confirmed that day), labelled «Возврат». The hygiene episode and ID20 also go to Status.

(B) 4 base videos, published Wed → Sat:
- Wed: hero E1 hygiene «Что происходит до того, как вы сели в кресло» (NEXT BATCH; ID01's file and sound footage is its hook, so ID01 is filmed but not published alone).
- Thu: ID20, bilingual KZ+RU.
- Fri: ID17 «Мастер считает», with a master of the free-slot service, salon-branded and unnamed.
- Sat: hero E2 process on the free-slot service (NEXT BATCH).
At least 2 of the 4 (ID17 and E2) are on the service the owner named in question 3; with no answer, the default is the non-nail service with weekday daytime slots. ID19, ID13 and ID09 are out of week 1. The card is capped at 4 ideas, split into two short windows: before the first client (≈6 min) and the dead hour after lunch (≈7 min). Staged shots use staff members' own nails. Card ≈13 min + KZ check 3 min ≈ 16 planned; code recomputes.

Fallbacks:
- Hygiene routine not confirmed by 10-16 → E1 is not made (we never show what isn't routine) and ID15 takes its slot.
- Process steps not confirmed → E2 is process-only with no duration or «почему» claim.
- No master consents to voice → ID17 is hands plus captions «мастер считает».: ID01, ID20, ID17. Staff: Это ИИ-ассистент салона. Съёмка во вторник 20.10, два коротких окна: утром до первой клиентки (~6 минут) и в тихий час после обеда (~7 минут): маникюрный стол, кресло мастера, тихий угол. Лица не нужны, для постановочных кадров — ваши собственные ногти, карточку пришлём. Плюс 3 минуты: проверить казахские подписи. Администратору отдельно: отправить одобренное сообщение клиенткам, которые не были 6–10 недель (правило отбора пришлём), и ставить метку «Возврат».. AI: Edit 4 bodies with 2 hook variants each (first frame and hook text), all through the truth rails. ID20 gets bilingual KZ-large / RU-small captions using only native-checked KZ text. E1 uses ID01's real file sound as the hook, with no «Включите звук» and no music. Make Status cuts of E1 and ID20. Cross-post to Reels, TikTok and Shorts with a separate cover and caption per platform, put prefilled wa.me links in the story sticker and bio, and the code in the caption and pinned comment. Count «Возврат» replies and bookings daily. Triage comments daily and draft replies (never argue about price, never name anyone). Read every post at 48 h against the pooled beauty median.
- **Week 2** — Explore + follow-up (2026-10-26 → 11-01).

Warm base stays at about 40% of effort: the second reactivation wave, and ID24 on Status. Expand to 10–16 weeks lapsed only if REACT1 allows.

Card capped at 4 ideas:
- ID24 (staff member's own nails);
- ID15 (bilingual; KZ-only variant on another platform the same day);
- hero E3 on the free-slot service (NEXT BATCH);
- ID13, only if the belief source is found in the export or 2GIS; otherwise a «Мастер считает» episode 2 with a second consenting master (ID17).

Other work:
- 2 follow-ups for any DR2 breakout;
- first reply videos from real comments (zero minutes);
- a 2-minute payoff bank of finished work at the end of the shoot day, which replaces the payoff shots inside cards (net-neutral minutes);
- the boost question with real numbers;
- fix the success target as a multiple of the baseline.: ID24, ID15, ID13, ID17. Staff: Это ИИ-ассистент. На неделю (до 17 минут): 1) карточка во вторник — два коротких окна, постановочные кадры на ваших ногтях; 2) в конце дня съёмки 2 минуты: готовые работы крупно у окна; 3) 3 минуты — проверить казахские подписи; 4) голосовое 30 секунд: 3 вопроса клиенток за неделю. Администратору: вторая волна сообщений тем, кто давно не был, метки «Видео», «Записан», «Возврат».. AI: Update the driver × format posteriors at series level. Code new comments, chats and «Возврат» replies into evidence. Add failed hooks to the graveyard. Re-cut and repost any DR3 hook failure (≥7 days later, once only). Edit reply videos from library clips. Compute the boost cap. Draft the owner report (≤5 lines) and the week-2 owner asks (anti-sell «да», photo review «да»). Send staff one true results line, e.g. «Ваш кадр с пакетом инструментов посмотрели N раз, M человек написали».
- **Week 3** — Focus (2026-11-02 → 11-08).

Retention returns to ≤20% of slots: ID24 on Status, and reactivation only if REACT1 showed bookings. Run Thompson allocation by series. Hero «Вблизи у мастера» runs 2/week on services with confirmed free slots. Also in this week:
- ID09 «Мастер считает», with its CTA only if the owner said «да» to photo review;
- ID19 anti-sell wildcard, only with the owner's «да»; otherwise it is dropped;
- ID20 timed to verified той dates.
Keep ≥2 base videos on free-slot services. Run the first boost only if approved and DR9 holds. Test the non-price offer only with the owner's «да» and if chats still stall after the price.: ID09, ID19, ID20, ID17. Staff: Это ИИ-ассистент. Всё как на прошлой неделе: карточка во вторник двумя короткими окнами (до 17 минут вместе с проверкой казахских подписей), голосовое про 3 вопроса клиенток, метки «Видео», «Записан», «Возврат». Новых задач нет.. AI: Run allocation and the DR5/DR6 checks: if attributed chats are under 30% of plan, audit the prefilled links, sticker, bio, Direct auto-reply and reply time before making more content. Draft reply scripts for wherever chats die. Run the boost and monitor it against the stop-loss. Pre-script the New Year corporate-party moment (NEXT BATCH).
- **Week 4** — Convert + review (2026-11-09 → 11-15). Conversion push within capacity (DR10), pointed at services with free slots. Compare weekly bookings at undiscounted prices with the baseline, and report the reactivation arm separately. Write learnings with strength labels. Choose next sprint's arms and decide whether the hero continues.: ID17, ID20, ID24. Staff: Это ИИ-ассистент. Последняя неделя спринта: карточка во вторник двумя окнами (до 17 минут), голосовое про вопросы клиенток, метки «Видео», «Записан», «Возврат». Спасибо — в пятницу пришлём итоги в цифрах.. AI: Final 7-day reads. Report:
- the attributed-booking floor (codes + «видео» answers) and total bookings vs the 4-week baseline as an estimate;
- reactivation bookings per 100 messages;
- chat→booking rate vs baseline;
- the guardrails (reply time, 2GIS rating, zero discounts, opt-outs).
Run the mechanism check of each driver against its own metric. Write learnings.jsonl entries labelled hypothesis or measured (correlational), never «winner» without DR13. Send the owner one decision for the next sprint.

Week 1 filming fits the budget: 16.7 min (ID15, ID19, ID20, ID17, ID24, ID13, ID01).

## Measurement and decisions
- Metric: WhatsApp bookings at current, undiscounted prices per week, 2026-10-19 → 2026-11-15.
- Conservative: at baseline (the decline is stopped).
- Expected: +10% vs baseline.
- Stretch: +20% vs baseline.
The baseline comes from the 4 weeks before 10-19 in the chat export, or from the week-0 count if there is no export; the multiple is fixed at the end of week 2. Sub-metric for the warm-base arm: bookings per 100 reactivation messages (label «Возврат»).
Guardrails:
- chat→booking rate not below baseline;
- median first reply ≤15 min;
- 2GIS rating not below its current level;
- zero price cuts;
- opt-out complaints from reactivation ≤2.
- Attribution: Tap-only codes. Every video's prefilled wa.me link already contains its code, in the story link sticker, the Instagram bio or link-in-bio, the TikTok bio, and wherever links are clickable. The code is also on screen for ≥2 s, in the caption and in the pinned comment.
The PRIMARY source is the admin's «Подскажите, откуда вы о нас узнали?» asked in every chat that has no code, including Instagram Direct chats, labelled «Видео». Coded chats are a floor.
Per-video codes stay as code assigns them, but allocation and decisions read at SERIES level (code + «видео» answers pooled per series) so counts reach a readable size (strategist judgment).
Reactivation messages carry the «Возврат» label and are a separate arm, never mixed with video attribution.
Total weekly bookings vs the 4-week baseline are an estimate. Walk-ins: the admin asks «откуда узнали?» and tallies «видео» (assumption).
Attribution window: 30 days per code. No Kaspi channel.
- Review: Each post is read at 48 h (allocation) and at 7 days (final). The reactivation arm is read daily in weeks 1–2 and weekly after that. Weekly campaign read on Monday, with an owner report of ≤5 lines in Russian, true numbers only and at most 1 decision. Phase review in week 4 (2026-11-13). Code attribution window: 30 days. The allocation metric is relative views plus shares and saves until the client reaches 20 attributed chats in total; after that, attributed chats per 1,000 views, read per series.
- Rule: DR0 (client-specific, week 0): if the export shows a median first reply over 60 min in working hours, or that most lost clients left with a departed master, fixing replies or staffing comes first. Conversion CTAs are held, and the owner is told in one sentence.
- Rule: DR1 Read every post at 48 h and at 7 days, per platform, against that platform's own baseline.
- Rule: DR2 Breakout: ≥3× platform median at 48 h (≈1,500 views on the pooled ~500 median [ASSUMPTION]; switch to the own median after 10 posts), or shares + saves per 1k ≥2× median. Within 7 days: a part 2 or the same insight in a new format, plus a reply to the top comment. Pin it if conversion-relevant, put it on Status, and make it boost-eligible. At ≥10× (≈5,000 views) it becomes a series, and the owner hears «вирусный» described as a tail event.
- Rule: DR3 Hook failure (3-second hold <0.7× account median): re-cut with a different first frame and hook text, and repost ≥7 days later, once only.
- Rule: DR4 Body failure (hold OK, completion <0.7× median): shorten and move the payoff earlier in the next episode. No repost as is.
- Rule: DR5 Conversion-layer miss: views on plan but attributed chats (codes + «видео» answers) under 30% of plan by the end of week 3. Illustrative plan ≈8/week [ASSUMPTION], recomputed after the export. Before more content, check the prefilled links, story sticker, bio, Direct auto-reply and reply time.
- Rule: DR6 Sales-handling miss: attributed chats on plan but chat→booking below baseline. Report where chats die and draft reply scripts. Price stays the owner's call, and we never propose a discount.
- Rule: DR7 Attention-only arm (≥10 posts, ≥10,000 views, 0 attributed chats while other arms convert): cap at 1 post/week and use its footage as B-roll. A bare ASMR loop (ID01 alone) is never published unless it carries a hero proof message.
- Rule: DR8 Retire an arm when P(arm beats client median) <0.10 after ≥8 posts: drop it to the exploration floor; its data stays in the pool.
- Rule: DR9 Boost only DR2 posts with ≥1 attributed chat or a conversion role, within the owner's cap (average check × gross margin × close rate × 0.3, computed in week 2). Stop-loss: stop if spend reaches 5× the cap with fewer than 3 attributed chats, or if cost per chat rises 3 days in a row. Never with an unconfirmed offer.
- Rule: DR10 Capacity and coverage: every week, ≥2 base videos go to services or masters with owner-confirmed free slots. When attributed demand for a master or service reaches ≥80% of her reported free slots, pause CTAs pointing there and redirect to other free slots. CTAs and reactivation messages offer only slots the admin confirmed that day.
- Rule: DR11 Honesty kill-switch: if a comment credibly disputes something shown (a hygiene step, a care tip, the removal opinion), pause that series, verify with the master, and tell the owner the same day. A hygiene step is shown only if it is done for every client. Price-comparison comments get a calm reply draft and are never argued with or answered by naming anyone.
- Rule: DR12 Pivot: if by week 4 no arm has P(beats median) >0.6 and weekly bookings are still below baseline, rerun step 3 with fresh chats and voice notes, diagnose the funnel, and send the owner options: another bottleneck, more warm base, a non-price offer, boost, or pause.
- Rule: DR13 Claims: a «winner» needs P(best) ≥0.9, n ≥10 per contender and an interval. Otherwise it is «лидирует, рано судить». The KZ-only vs bilingual test reports direction only this sprint.
- Rule: DR14 Staff: if card completion is below 80% for 2 weeks, or a window overruns by more than 5 min, go to 3 ideas per card, only «маникюрный стол», staff members' own nails, and more zero-minute reply and re-cut videos. A card never has more than 4 ideas.
- Rule: DR15 Owner: if more than 30% of the batch is rejected, read the reasons and update the constraints. A fact rejection means fixing the ledger first.
- Rule: DR16 Never delete flops, except for truth, consent or legal problems.
- Rule: REACT1 Reactivation [thresholds are ASSUMPTIONS, re-set after the export]: send in waves of ≤20 per day. After the first 40 messages, if ≥4 bookings (≥10%), extend to clients lapsed 10–16 weeks in week 2. If <2 bookings, stop, and in week 3 read the replies for the real reason clients left (price / master / other) as evidence. If ≥2 «не пишите» or complaints, stop and tell the owner the same day. Each client gets at most 1 message per sprint, and the do-not-contact list is permanent.
- Rule: MASTER1 Master-flight guard: a master's name, face or personal account appears in public content only with the owner's separate «да» for that master (and her consent for face and voice). Booking always goes through the salon number. If a featured master leaves, her episodes are unpinned (not deleted, DR16) and her CTA is redirected to the salon.

## Questions for the owner (batched)
- Кто именно уходит? 1 — новые: пишут, узнают цену и не записываются; 2 — постоянные клиенты перестали возвращаться; 3 — клиенты ушли вслед за мастером, который ушёл или работает отдельно; 4 — не знаю. По умолчанию: 1. Ответ до 10.10 12:00.
- Кого можно снимать? 1 — только руки мастеров и голос; 2 — мастеров с лицом (только тех, кто согласен); 3 — и клиентов (если они согласятся на камеру). По умолчанию: 1. Ответ до 10.10 12:00.
- Куда звать новых клиентов? 1 — на будни днём; 2 — к конкретным мастерам или на конкретные услуги, где есть окна (напишите какие); 3 — свободно почти всё. По умолчанию: 1, без обещаний «свободно сегодня». Ответ до 10.10 12:00.
- WhatsApp chat export: 15–30 recent client chats, without media
- Permissions tap card: who leaves, who may be filmed, where to steer bookings, prices in videos
- Money map: price-list photo (dated), 3 services to fill, services not to push, free slots per week by master/day
- Account insights: Instagram/TikTok access or screenshots, and whether accounts exist
- Proof folder: ~20 real photos and videos of masters' work, sent as files
- Staff reality scan: 3 test clips (speech at 30 cm, a tool sound at 30 cm such as a file, clippers or a hair dryer, the room) plus a 2-minute silent walkthrough
- Masters' individual consent to appear (face and/or voice)
- Week-0 baseline tally and WhatsApp labels «Видео» and «Записан»
- Weekly staff voice note: «3 вопроса клиентов за неделю + 1 случай» (from week 1)
- Подтвердите или поправьте, пожалуйста, факты для роликов: ID15.comment_prompt_ru: scarcity/urgency claim without a backing fact: 'последний день'; ID20.on_screen_ru[2]: scarcity/urgency claim without a backing fact: 'последний день'; belief source (C6.11). If it is not found in customer language, reframe as «Нас часто спра; master's actual checks

## Attack before revision
- Владелица салона красоты в Шымкенте (8 м: 6/10, approve=True
- veteran_creator: short-form creator and : 5/10, approve=False
