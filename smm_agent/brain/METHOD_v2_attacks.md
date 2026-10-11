# Attacks on the method v2 draft (not yet applied)

Two adversarial reviews of `METHOD_v2_draft.md`: (1) coverage of the v1 audit failures, (2) operability for a model following it literally. The finalise step that applies them hit the usage limit; apply them before v2 becomes `METHOD.md`.

## Attack 1

**METHOD v2 coverage review: the 35 audit failures caused by method or model_noncompliance**

In scope are 35 failures: 30 caused by method and 5 by model_noncompliance. All 35 are major. None is fatal, because all 11 fatal failures were caused by code. v2 has a specific rule that prevents 18 of them. The other 17 are not prevented, or only partly; they are in section A, ordered by how much risk is left. Section C lists 12 things v1 did well that v2 drops or weakens.

## A. Not prevented, or only partly (17 failures in 15 entries)

**1. salon (method): the owner was never offered price options. Not prevented, because the options cannot reach the owner.**
- **What v2 has:** A2 says price_pressure "delivers, in `offer.proposal` with `needs_owner_approval: true`, ≤5 Russian lines".
- **Why it still fails:** The owner never sees `offer.proposal`.
  - `brain.deliverables` builds the owner message only from `campaign.owner_asks` plus facts (brain.py 672–685).
  - campaign.md is internal and prints the offer only when `needed` is true (967–969). F4 says "Default `needed: false`".
  - The result repeats the run: «ни один вариант мне не предложили».
- **Fix (A2):** "price_pressure sets `offer.needed: true` and adds the owner ask `[key:offer] [unlocks:week2+]`: «Чтобы не снижать прайс, можно попробовать: 1 — …; 2 — …; 3 — …; 4 — пока ничего не меняем. По умолчанию: 4.»" Add that ask to the F12 checklist.

**2. b2b (method): the test was organic-only. Partly prevented.**
- **What v2 has:** A7 sets up three arms, with arm (b)'s yes/no among the first 4 owner items, and F5 adds a B2B seeding row.
- **Why it still fails:** L8 says "Asks about contacting customers … default to «нет»".
  - Arm (b) is reps forwarding videos to prospects, so it defaults to off.
  - That is the run's own default, «шаблоны не используем, пересылку не делаем», which the creator called "NO almost by construction".
  - With no answer, v2 runs two arms and still gives a verdict.
- **Fix (A7):** "Arm (b)'s ask is item 1 and has no silent default. If it is unanswered after one reminder, arm (b) is reported as «не проверено». The verdict covers only the arms that ran and is worded «органика нового аккаунта за 4 недели не дала…», never «соцсети не нужны»."

**3. b2b (method): the YES threshold was noise. Partly prevented.**
- **Why it still fails:** A4 now needs the owner's margin and hourly cost.
  - Bank question #6, «Средний первый заказ новой компании и ваша маржа, %?», has no «По умолчанию», which breaks A8's own format.
  - Nobody asks for the hourly cost.
  - If the owner does not answer, no verdict can be computed. That loses v1's verdict fixed in advance, which the audit named as b2b's best part.
- **Fix:**
  - Change bank #6 to «Средний первый заказ новой компании (₸), ваша маржа (%) и стоимость часа сотрудника (₸)? По умолчанию: [три числа-допущения агента, названные в вопросе].»
  - A4: "The YES threshold in ₸ is computed at intake into `success_metric.target` and frozen before week 1."

**4. salon (method): the truth score penalises proof ideas that need only a yes/no. Not prevented.**
- **Why it still fails:** The E2 anchor for 3 still reads "Claims need a NEEDS FACT".
  - Salon ID05 «Что происходит до того, как вы сели» needs only the owner's «да» and still scores 3.
  - A claimless ASMR or POV idea meets anchor 5 ("every claim ledger-backed or visibly filmed") because it makes no claims.
  - The audit's fix ("a gate handled by code, not a score penalty") was not adopted.
- **Fix (E2 truth):** "Score as if every `NEEDS FACT (owner|staff)` that is a yes/no confirmation of a filmable routine were answered «да»; code gates the idea until it is. 3 = the message would still rest on a `likely` claim after filming. 1–2 = what it shows would stay unproven after filming."

**5. muzzone-viral (method): the slate was faceless, voiceless and had nothing local. Partly prevented.**
- **What v2 has:** E3 rows: "awareness: ≥3 with one recurring staff voice", "≥3 with a local marker; ≥1 mastery idea".
- **Why it still fails:** These rules apply to the idea pool only.
  - The run's pool already held ID21 (mastery), ID23 (clinic re-cut) and ID10. The failure was in selection and week 1.
  - TAGS carry no voice or local flag. E1's quotas cover only the top insight and the funnel stage. F1 and F12 do not ask for a voice or a local marker.
  - D9 keeps skill ideas at `ready=week2+` until the reality scan. Mastery is therefore barred from week 1, even though the store's channel shows its players (Govan clinic, 39 000).
  - Creator: «None of the 5 week-1 videos says «Астана»… or has a human voice beyond one optional line».
- **Fix:**
  - TAGS: add `voice=yes/no; local=yes/no`.
  - F1/F12 for awareness_or_viral and launch_or_event: "weeks[1] has ≥2 voice=yes ideas by one recurring staff member and ≥1 local=yes idea." Code adds the same slate quota.
  - D9: "A skill idea is ready=week1 when existing footage (own channel, proof folder) already shows that staff member performing. A zero-staff re-cut of an own skill outlier counts as the mastery idea."

**6. coffee (method): exploration slots went to off-objective ideas. Not prevented.**
- **What v2 has:** Only CODE CHANGES #5 ("objective_fit ≥3 for date-bound", still open).
- **Why it still fails:**
  - E1 has no rule for date-bound requests.
  - The launch quota ("≥half attention-stage") is met by generic attention ideas such as ID24 «Странный заказ» (objective_fit 2) and the 6 generic coffee ideas with brand_link 2.
  - Nothing requires slate ideas to carry the launch.
- **Fix:**
  - TAGS: add `dated=yes/no`, meaning the idea shows the new site, the dated product or the moment.
  - E1: "Date-bound requests ≤5 weeks out: ≥60% of the slate is dated=yes; the attention quota counts only dated=yes ideas; exploration draws only from objective_fit ≥3."
  - Code implements this together with #5.

**7. salon (method): the single revision traded one fatal for another. Partly prevented.**
- **What v2 has:** F1 bans NEXT BATCH items in weeks[1].
- **Why it still fails:**
  - F14 still allows exactly one revision and requires no re-attack.
  - `run()` defaults `rereview=False` (brain.py 754, 903). The salon boss score fell from 6 to 5 with a new fatal, «Главных роликов в плане нет», and that kind of drop now ships unmeasured. CODE #23 assumes a re-review that does not run.
  - F14 says "OPEN: … shown to the owner", but campaign.risks is English and code never sends it to the owner.
- **Fix (F14 + code):**
  - Code always re-attacks the revised plan (`rereview` defaults to True).
  - If any score falls or a new fatal appears, code runs one targeted revision on those points only, trying pool swaps first.
  - If a persona is still below 7 or has a fatal, no shoot card is sent, and the owner message opens with «План ещё не утверждён:», then one Russian line per open point.

**8. dental + salon (model_noncompliance): staff, admin and doctor minutes over budget (2 failures). Partly prevented.**
- **What v2 has:** L5, F7 and F12 restate the budget rule that v1's L5 already had.
- **Why it still fails:**
  - The model broke the rule anyway: dental «тратить на это до 15 минут в день»; salon «reactivation messaging (≈10 min/day) is NOT counted».
  - The work hides in `channels` and `owner_asks`, and `worker_ask_ru` is free prose, so CODE #11 cannot sum minutes per role.
  - v2 itself assigns admin work: B3 «администратор раз в неделю заполнит короткую таблицу», and A4 "one weekly admin number". Both contradict L5's "other roles … get 0".
- **Fix:**
  - Section 0.2:
    - Each `worker_ask_ru` line is written «<роль>: <задача> — N мин».
    - Any channel that creates human work ends with `[minutes: <роль> N/week]`.
    - Add the key `role_minutes`, with the default «0 — не поручаем».
  - Code sums minutes per role per week, including the card. It rejects staff over 17 minutes (week 1: card ≤12), and any other role above 0 unless a `role_minutes` ask exists.
  - L5: "The tally and the weekly system-of-record number (≤3 min) are done by whoever answers WhatsApp, inside the 17."

**9. dental (model_noncompliance): patient outreach defaulted to «да». Partly prevented.**
- **Why it still fails:**
  - v2 restates the rule but nothing enforces it; CODE #13 is open.
  - Defaults are not machine-readable.
  - `weeks` and `channels` text can still schedule «первая волна 16.10».
- **Fix (code, #13):**
  - Covered asks: those keyed warm_base, data_option, offer or permissions, plus any ask that mentions ₸ or бюджет.
  - Code rejects such an ask unless its «По умолчанию:» clause starts with «нет»/«не» or names the no-option.
  - Code also rejects weeks/channels text matching «волн|рассылк|напишем (клиент|пациент)|по базе» unless it says «только после „да“» to that ask.
  - Allow one fix pass, then remove the outreach arm.

**10. b2b ID14 + salon ID19 (model_noncompliance): a pinned-utility post and an anti-sell wildcard were scored as mainstream ideas (2 failures). Partly prevented.**
- **What v2 has:** D10 and E2 add caps.
- **Why it still fails:**
  - The caps are applied by the model, which already ignored v1's L4 logo test and "score wildcards honestly low": ID14 got objective_fit 5 and share_save 4; ID19 got stop 4, share_save 4, comment 4.
  - There is no `pinned` tag.
  - ID19's own «Owner approval required before shooting» matches no REQUIRES kind, so code still cannot gate it.
- **Fix:**
  - TAGS: add `pinned=yes/no`. REQUIRES: add `owner_ok:<what>`.
  - Code clamps the scores:
    - wildcard=yes: every criterion except stop ≤3.
    - pinned=yes, or a hook matching «пишите так|как (нам )?написать|как заказать»: share_save ≤2, objective_fit ≤3, excluded from the slate and the verdict count, pinned in week 0.
    - format anti_sell or driver honest_signal under price_pressure or launch_or_event: objective_fit ≤2.
    - owner_ok: not filmed until the owner answers.

**11. salon (method): the privacy promise was false. Partly prevented; v2 brings in a new false promise.**
- **Why it still fails:** v2's B3 text says «имена и номера мы заменяем при загрузке».
  - Nothing in smm/ pseudonymises anything; searching for `cust_` or anonymisation code finds nothing.
  - The model reads raw files through the Read tool.
- **Fix:** Add a code step that replaces names and numbers before any model call. Until it exists, the text should say: «Файлы прочитает ИИ-ассистент MetaPrompt — сервис за пределами вашего бизнеса; имена и номера в них останутся, в роликах их не будет.»

**12. coffee (method): «напомним в день открытия» had no delivery mechanism. Partly prevented.**
- **Why it still fails:** D6 and F5 say "a WhatsApp broadcast reaches only people who messaged that number". In fact a WhatsApp Business broadcast is delivered only to people who saved the business number in their contacts.
  - F5's own cap (≤10 new outbound messages a day for 3 days) also blocks a day-of reminder to 60–250 people.
  - So «напомним в WhatsApp» passes v2 and still fails.
- **Fix (F5/D6):**
  - A WhatsApp reminder promise is allowed only if three things hold:
    - the reply asks «Сохраните наш номер — иначе напоминание не дойдёт»;
    - the F5 ramp starts at least 3 days before the date;
    - the messages are counted in F7 minutes.
  - Otherwise use a Stories countdown, or promise nothing beyond the reply itself.

**13. muzzone-sales (method): the minute model undercounted. Partly prevented.**
- **Why it still fails:**
  - The 1.5× correction lasts only "until a timed week-0 session", and no step defines that session. The week-0 reality scan times 3 test clips, not a card.
  - Weeks 2 and later go back to "≤17", which is about 25 real minutes. The run said «Realistically that is 30–45 minutes».
  - The floor "cable, amp or device 1–3" lets amp + guitar count as 1 minute.
  - Code still plans week 1 to 20 minutes and prints «из 20» (shootcard.render_card_ru, with `capacity_min=20`).
- **Fix (D9):**
  - Every card is ≤12 formula minutes until 2 timed sessions exist. Staff send the start and end time with the files.
  - After that, the cap is 17 ÷ the measured real-to-formula ratio.
  - Floors: amp + instrument 3 minutes; any other powered device 1 minute.
  - Code change #9; restore v1's DR14 (section C, item 4).

**14. dental (method): regulated talk was improvised on camera. Partly prevented.**
- **Why it still fails:** D9 also limits `say_ru` to "≤12 words, the worker's own words", and the card prints `say_ru`.
  - So the approved ≤40-word answer has no field and cannot appear on the card.
  - REQUIRES is not parsed yet (#7).
- **Fix (D9):**
  - In regulated categories, `say_ru` is the approved text verbatim, split across talk shots of ≤14 words each.
  - `facts_used` cites its ledger id.
  - The card prints «Читайте дословно: …», and the captions must match it.

**15. muzzone-sales (method): the hero depended on an unchecked skill and on phone tone. Mostly prevented, with one new unchecked dependency.**
- **Why it still fails:** "Recorded by cable into the phone" depends on two things nobody checks:
  - whether the phone's camera app records from an adapter, which varies by phone;
  - whether the line or headphone level needs attenuating.
- **Fix:**
  - Reality scan (B3 #7) adds a clip: «Кабель от выхода на наушники в телефон через переходник: 10 секунд камерой — звук идёт из кабеля, без хрипа?»
  - Cable ideas stay `ready=week2+` until that clip passes, with setup_min +1.

## B. Prevented by a specific rule (18)

**Prevented outright (15):**
- muzzone-viral, TikTok defaulted away: A1.2, A5 CHANNEL and the F5 TikTok row.
- dental, a persona invented facts about the business: F13 "Never add facts" and F14 `[ASSUMPTION]`.
- dental, warm base was only a fallback: A6 required levers.
- dental, remote X-ray opinion offer: A5 REGULATED and F4.
- dental, undefined metric: A4 and F1.
- coffee, ажиотаж demoted and anti-demand content: A1.2, A5 CAPACITY, D10 and E2.
- coffee, two sites in one session: D9 site/spot, one site per card (code #10).
- coffee, target raised without new realism math: F14 REALISM and F1 (render: code #21).
- coffee, local levers missing: A6, F5 «local reach» and L11.
- coffee, weak offer: F4 hospitality menu.
- b2b, self-incriminating and lecturing ideas: D10 and E2.
- salon, one service line: E3 line row and A7 (slate quota is code #4).
- salon, wrong branch chosen: A1.3 and A1.2.
- salon, partial metric: A4.
- salon, legal minimum used as the hero: D10 and the D3 backstage row.

**Prevented, but the rule needs hardening (3):**
- **salon, impersonation:** covered by L10 and F5. No change needed beyond the rules as written.
- **muzzone-viral channel / bank #3:** Bank #3 `channel_access` has no template text or default. Add «Аккаунта в ТикТоке нет — создадим на номер магазина, перешлите код из СМС. 1 — да, 2 — создам сам. По умолчанию: 1.»
- **coffee, address gate:** G4 still requires `{CODE}` in every `cta_ru`, and code issues BA-style codes, so a walk-in business has no till-word CTA. Add: "walk-in: «Скажите на кассе „{CODE}“»; code renders a word."
- **coffee, defaults versus the hero frame:** F14's "flips" could flip a faces or contact default to «да», which L8 forbids. Restrict flips to elements outside L8 that are backed by L2; otherwise change the hero.

## C. What v2 broke that v1 did well

1. **Field tables (G1–G6) deleted.** v2 says "Schemas are as in v1", but `method_text()` loads one file, so the model never sees v1. Lost rules include:
   - G1: `push_back` is "" when there is nothing to push back on.
   - G2: owner minutes only in `owner_minutes`; narrow `blocks_step` values.
   - G3: `who_feels_it` = situation, not demographics; `content_reality` = what the camera sees plus a named location.
   - G4: `why_stop` = mechanism, not adjectives; `kpi` = driver metric plus business metric.
   - G5: series `role` = funnel + metric + opening ritual.

   Restore the tables with v2's edits.
2. **Worked example cut down.** v1's H1–H6 showed intake with REALISM and push_back, evidence and insight caps, a campaign with the client's numbers, and review refutations. v2 keeps one idea and 3 asks.
   - The audits' best parts (muzzone-viral, dental, b2b) were exactly the intake, measurement and truth layer those examples taught.
   - The surviving hook «Все показывают снаружи. Мы — внутри» breaks v2's own D10 ad-first rule («мы/наш» in the first 2 s).
   - Restore H1 and H3 in v2 terms and rewrite the hook.
3. **Capacity check dropped from REALISM.** v1 A6 had "capacity = extra demand ≤ free capacity, else throttle conversion content". Add it back.
4. **Feedback rules dropped:**
   - DR14 (card completion below 80% → fewer locations, face-free shots, shorter takes). It is the only in-flight correction for the minute undercount.
   - DR15 (owner rejections above 30% → update constraints).
   - The per-idea mechanism check and the shared cross-client experiment.
   - Per-client numbers in the rules (v1's "DR2 at ≥2,700 views").

   Restore them in F9 as internal rules.
5. **Verdict fixed in advance** now depends on numbers the owner may never give (see A3).
6. **Wildcards.** v2 caps wildcards at ≤3 on six criteria, while seeded wildcard exploration (#5) is still open. muzzone-viral already picked 0 of 5 wildcards (ID10 prior 3.038), and v2 pushes their priors lower still. Until #5 ships, drop the blanket cap or have code rank wildcards separately.
7. **Customer-language supply.** v1 ranked the chat export first and had owner and staff voice notes. v2 defaults to a tally and drops both voice notes. Meanwhile C5 caps any insight that has no customer_language or behaviour evidence at 2, and the fetch stage (#1) is open. In practice every insight will score 2:
   - E1's "≥2 on the strongest insight" quota becomes a tie across all insights.
   - A7's diagnostic mode always fires.

   Fix: code the tally's «топ-3 вопроса дословно» as customer_language (`likely`, with counts), and keep the 30-s staff voice note as an alternative to typing.
8. **Attribution.** v1 F9 put prefilled links "wherever links are clickable" and kept the code as the main path. v2 L3 makes the wa.me link primary "in bio, caption, pinned comment" and the code a backup.
   - Links in Instagram and TikTok captions and comments are not clickable, and Shorts description links are not either.
   - So every tap goes through the one bio link, which carries one code, and per-video attribution collapses.
   - Fix (F8):
     - Rotate the bio code to the newest post, or use a link page with one button per live video.
     - Add a Stories link sticker for each video.
     - Keep the on-screen code and «С какого видео вы нас нашли?» as primary.
     - Treat coded counts as a floor.
9. **Hiring guidance.** v1's "Discriminatory requirements" trap, the job-seeker fears (late pay, unpaid trial days) and the job sites (hh.kz, enbek.kz) are gone. Restore them.
10. **Request-type tie-break.** v1 A1.2 said "the one with a date and money attached is primary". v2 has no rule for a request like salon's «Конкуренты дешевле, клиенты уходят». Restore it.
11. **Trend safety.** v1 D7's ban on tragedy, dangerous challenges and mocking real people is gone, and A5 AVOID does not cover it. Restore it.
12. **Shoot-card details.** D9's phone rules (отправлять как файл; секунда до и после; фокус; музыку выключить), "two people talk only with the phone between them", and the D5 register rule (вы for 30+, ты for youth) were dropped. The model writes `what_ru`, and muzzone-sales already missed «отправьте как файл». Restore them.

**Contradictions in v2 that do not match the current code:**
- The step table says code "Runs agent FETCH lines before step 3", but that is still open (#1).
- prompt4 still asks for «NEEDED: …» in `facts_used` (brain.py 810).
- `declared_needs` (brain.py 561) still sends `NEEDS FACT (staff)` to the owner, against section 0.2.

Files:
- /home/user/flystuff/smm_agent/brain/METHOD_v1.md
- /home/user/flystuff/smm_agent/brain/audits_v1.json
- /home/user/flystuff/smm_agent/brain/AUDIT_v1_STATUS.md
- /home/user/flystuff/smm_agent/smm/brain.py
- /home/user/flystuff/smm_agent/smm/shootcard.py

## Attack 2

**Operability review of METHOD v2: 30 findings, each with an exact replacement**

**Overall verdict.** The slug tables parse correctly. The real operability faults fall into four groups:
- Rules the code contradicts or never enforces: the rail on `worker_ask_ru`, reserve ideas, `(agent)` facts, and REQUIRES/ready tags.
- Rules that contradict each other: F14 against L8, D4.6 against D4.7, C4 against C5, a "co-primary" goal against one primary metric, and others.
- Thresholds given as a range or with no number.
- About 15% of the prompt is tokens no model step uses.

Evidence comes from:
- the v1 runs replayed through current code: `scratchpad/brain/replay_v1/<case>/{checks,questions}.json`, with 0 model calls;
- `smm/brain.py` at HEAD 05686ad;
- v2 as it stands in `scratchpad/brain/METHOD_v2.md`.

### 0. Parser check (verified by running the code on v2)

- `brain.method_vocab(v2)` returns 13 driver slugs and 28 format slugs, identical to v1. The heading phrases "the `driver` field" and "the `format` field" match, and the first table in each section is the slug table.
- `method_section(v2,"F13")` returns 1,369 characters and `"G6"` returns 252, so reviewers get both sections.
- Nothing is missed. To keep it that way:
  - Keep D2 and D3 headings unchanged.
  - Never place another table between those headings and their slug table.
  - Never add backticks or bold in column 1.

### A. Deliverable-breaking: the code turns v2 rules into wrong output

**1. C6.1 conflicts with F7 and F6.**
- **Problem:**
  - C6.1 puts `worker_ask_ru` under the number rail.
  - F7 requires minutes in that text: «~11 мин», «Итого ~15 мин».
  - The step-6 prompt always passes TODAY, so F6 allows dates.
  - `deliverables()` runs `check_text` on `weeks[1].worker_ask_ru` and turns every number ≥10 into an owner question.
- **Evidence:** in the replay, the salon owner card says «Верна ли цифра «20.10» для ролика «задание сотрудникам»? Если да — откуда она (прайс, сайт, ваш учёт)?» and «…«10»…». The b2b card says «…«27.10»…». Under v2, every staff minute count ≥10 would do the same.
- **Replace in C6.1:** "`single_minded_message_ru`, `worker_ask_ru`, `offer.proposal` and quoted `channels` texts"
  - **with:** "`single_minded_message_ru`, `offer.proposal` and quoted `channels` texts. `worker_ask_ru` is staff text: only C6.3–C6.4 apply; its minutes and weekdays are not facts."
- **Replace in F6:** "Write «вторник недели 1» unless TODAY is given."
  - **with:** "In `worker_ask_ru` and owner texts write «вторник недели 1», never a calendar date, even when TODAY is given."
- **Code:** CODE CHANGES #15 asks for exactly the check that produces this. Amend it to "rail-check worker_ask_ru for claims and urgency only, not numbers".

**2. Reserve ideas bypass readiness, holds and the one-site rule.** E1 says "if fewer than 2 week-1 ideas are ready, code adds ready reserves".
- **Problem:** code ranks reserves by prior across every idea that is neither blocked nor gated. It reads no `ready=`, REQUIRES or site, and ignores holds the campaign states in prose.
- **Evidence from replay `checks.json`:**
  - b2b: «reserves added: ['ID10']», while its campaign says «ID10 (late-truck POV) is held until delivery facts exist and the owner says «да»».
  - coffee: reserves are ID14, whose risks say «WILDCARD: depends on a windy day», and ID07, which needs barista faces that are not yet permitted.
  - dental: reserve ID12, whose risks say «Audio quality unverified until reality scan».
  - muzzone-sales: reserve ID06 is a week-2 piano-room idea pulled into a one-location guitar-wall week.
- **Replace in E1:** that sentence
  - **with:** "if fewer than 2 week-1 ideas are ready, code adds only the ids you list in campaign `risks` as `RESERVE: IDxx, IDyy` (each `ready=week1`, same site as week 1); with no RESERVE line week 1 stays short."
- **Add to F14:** "An idea you hold for later is `drop: true` or gets a `NEEDS FACT (owner): …` risks patch; anything else may be filmed as a reserve."
- **Add to 0.2:** "Until code parses `REQUIRES` and `ready=`, write every unmet week-1 precondition (face consent, skill, weather, footage, approved script) also as a `NEEDS FACT (staff|owner): <Russian>` line: it is the only gate code enforces today."

**3. 0.2 misstates what code does with NEEDS FACT.**
- **Problem:**
  - `declared_needs()` skips any line containing "(agent". Such ideas are not gated, not asked about and not fetched.
  - So a non-numeric claim such as «есть выход на наушники», tagged `(agent)`, gets filmed without being checked.
  - `(staff)` lines are sent to the owner.
  - English lines still gate the idea, but are never sent. Replay dental: «ID04: NEEDS FACT not in Russian, kept internal: anaesthesia/sensation answer wording…» and «week 1 idea ID04 waits for owner facts».
- **Replace in 0.2:** "Code sends owner and staff lines as «Подтвердите для ролика …: <text>» and keeps the idea out of week-1 filming until answered; agent lines it resolves itself; English text is never sent."
  - **with:** "Each NEEDS FACT is its own `risks` item starting `NEEDS FACT`. Code puts owner AND staff lines into the owner's single facts item (≤6 lines, week-1 ideas first) and keeps the idea out of filming until answered. `(agent)` lines are neither gated, asked nor fetched today: use `(agent)` only for a fact no audience string states; otherwise tag `(owner)`. A line over 20% Latin (English, or a model code like «Casio CDP-S110») is never sent yet still gates: that idea is never filmed. Write products as Russian nouns."

**4. Owner card: the ≤7 cap can be evaded, sentence counts conflict, greetings repeat, asks overlap.**
- **Evidence from the replayed cards:**
  - b2b: one item packs six decisions: «ответьте по пунктам «да/нет»: 1) склад… 6) можно вскрыть один мешок».
  - salon: one item reads «Три коротких вопроса: 1)… 2)… 3)…».
  - The model adds its own greeting (b2b «Здравствуйте, это AI-ассистент…», salon «Здравствуйте, это ИИ-ассистент вашего салона»), although `agent.owner_message` already opens with «Здравствуйте! Это ИИ-ассистент MetaPrompt…».
- **Replacements:**
  - **L5:** "one decision = one item, never split" → "one item = one question mark, except a tap card (≤3 lettered yes/no lines, 1 min) and the fact pack (≤5 yes/no lines, 2 min); any other item counts as one item per question."
  - **L5:** "items 1–4 unlocking week 1" → "asks that unlock week 1 come first".
  - **A8:** "one Russian sentence, closed or numeric" → "≤3 short Russian sentences, closed or numeric". The bank's own `price_list` text is 3 sentences; B3 #8 is 5.
  - **A8 #2:** delete "Б) цены — 1 да / 2 нет;". It duplicates `price_list` and can contradict it. Change «имена мастеров» to «имена сотрудников».
  - **A8 ordering:** "`price_list` first" and "`fact_pack`… item 1 or 2" conflict on an empty ledger in a price-led category (dental, salon). Set the order: "fact_pack (empty ledger) → price_list (price-led) → permissions → channel_access → rest."
  - **F12:** "≤7 items, ≤15 min (≤6 and ≤13 when ideas carry NEEDS FACT (owner)…)" → "≤6 items, ≤13 min: code always adds one 2-minute facts item, and rail hits you cannot foresee land there."
  - **Add to L10:** "`owner_asks[].ask` never greets or introduces the assistant; code's message does."

**5. L3 per-video wa.me links cannot be executed.**
- **Problem:**
  - A profile has one link.
  - Instagram and TikTok captions and Instagram comments are not clickable.
  - With 5 videos live, the D6 CTA «Ссылка на WhatsApp в профиле — … Код {CODE}» sends every chat from that link to a single code.
- **Replace in L3:** "Each idea's code goes prefilled in a wa.me link (bio, caption, pinned comment, Stories)…"
  - **with:** "Each idea's `{CODE}` is on screen ≥2 s and in the caption; the profile wa.me link is prefilled with the code of the week's hero video (one link, one code); a Stories link sticker carries each video's own code. Coded counts are a floor; «Откуда о нас узнали?» covers the rest. You write `{CODE}`."
- **D6 template:** «Ссылка на WhatsApp — в профиле. Напишите код {CODE} — пришлём [конкретное и правдивое]».

**6. F14 and the owner never see "OPEN" lines.**
- **Problem:** code builds the owner card from `owner_asks` plus facts only, and `risks` are English, which L9 forbids in owner text.
- **Replace:** "Every point you could not fix is an `OPEN: …` line, shown to the owner."
  - **with:** "Every unfixed point is an internal `OPEN: …` line in `risks` (campaign.md lists them); if the owner must decide it, it is also an owner_ask."

**7. Price-pressure options and offers never reach the owner.**
- **Problem:**
  - A2 puts the price-pressure options in `offer.proposal`, and F4 costs them there.
  - The owner card is built from `owner_asks` only.
  - When `needed: true`, `offer.proposal` goes through the number rail, so cost estimates become «Верна ли цифра «…» для ролика «предложение»?».
- **Replace A2's price_pressure sentence with:** "**price_pressure:** `offer.needed: true`, `needs_owner_approval: true`; `offer.proposal` names 2–3 moves that keep the list price, with no number that is not a ledger fact; the same moves go to the owner as one `[key:offer]` ask with numbered options, default «ничего не меняем»."
- **In F4:** "costed as …" → "costed in the owner_ask text as «примерно …», never in `offer.proposal`".

### B. Rules that conflict

**8. F14 conflicts with L8.** Flipping a default that bans a hero-frame element would flip a faces or contact default to «да».
- **Replace:** "A default that bans an element of a hero frame scheduled in weeks 1–2 flips, or the hero changes"
  - **with:** "…flips only if L8 does not fix it (address, landmark, prices may flip; faces, contact, data, spend stay «нет»); otherwise the hero frame changes."
- **In A8:** "never forbid a week-1 hero frame (F14)" → "a week-1 hero frame never depends on a permission L8 defaults to «нет»."

**9. D4.6 conflicts with D4.7.** The "ready twin" shares insight, format and first frame, so the dedup rule removes it, and it eats E3's per-format cap.
- **Replace:** "also write a ready version whose payoff is filmed, not claimed"
  - **with:** "write the ready version instead, and put the upgrade in `risks` as `UPGRADE when answered: <Russian line>`."

**10. C4 conflicts with C5, and C5 names an undefined type.**
- **Problem:** with zero fetches, "Tests (rewrite or drop): evidenced…" drops every insight, yet C5 says cap at 2 and output 6–10. C5's "≥1 wildcard" is not one of C4's insight types.
- **Replace:** "**Tests** (rewrite or drop): evidenced (…)"
  - **with:** "**Tests:** evidenced (…), where failing caps strength at 2 (C5) and never drops; failing any other test means rewrite or drop."
- **In C5:** "≥1 wildcard" → "≥1 content_reality (it carries the wildcards)".

**11. A1.2 conflicts with A4.** A1.2 allows a "co-primary" goal; A4 requires one primary metric.
- **Replace in A1.2:** "stays primary or co-primary, re-expressed as a countable number" → "is the primary metric, re-expressed as a countable number; your preferred alternative may only be SECONDARY".
- **Same in A9:** → "Named outcome is the primary metric".

**12. E3 faces conflict with A5.**
- **Problem:** at step 4 no faces are permitted yet, so E3 demands "100% faceless". When the owner then says yes to faces, as A5 recommends, the pool has no face ideas.
- **Replace:** "≥40% faceless (100% if faces not permitted)"
  - **with:** "≥60% faceless; face ideas are `ready=week2+` with `REQUIRES: consent:staff` until `permissions` says yes."

**13. D9 upload term conflicts with F7 and with the code formula.**
- **Problem:** "+ 0.5 × posts uploaded by staff" contradicts F7 ("Workers never … post"). Code's FIXED_MIN already covers «reading the card + uploading».
- **Replace with:** "+ 0.5 × posts × platforms only if `channel_access` is refused and staff publish".
- **Also state in D9:** the card prints code's number (2 + 1 per spot + 0.75 per extra subject per spot + Σ shots), budgeted at 17 and printed «из 20». Until CODE CHANGE #9, the ≤12 week-1 cap is the model's job only.

**14. A regulated talk text of ≤40 words does not fit `say_ru` (≤12 words).**
- **Replace with:** "the owner-approved answer (≤36 words) is split across ≤3 talk shots of ≤12 words, quoted verbatim in `say_ru`; until approved, also `NEEDS FACT (owner): «текст ответа врача утверждён»`."

**15. F1 conflicts with ruling 0.1.1** ("never pick the slate").
- **Replace:** "you may take any ready pool idea instead of a slate idea that is not ready"
  - **with:** "replace a not-ready slate idea by the ready pool idea with the highest `_prior` on the week-1 site that keeps F3; name the swap in `why_this_wins`." The pool passed to step 6 already carries `_prior`.

**16. The step-4 rubric prompt contradicts E2's truth anchor, and the anchors mix two dimensions.**
- **Problem:** `RUBRIC_HELP` in the step-4 prompt (brain.py:99) says "truth: rooted in a verified insight/fact", which contradicts E2's truth anchor.
- **Add to E2:** "E2 overrides the rubric lines in the step prompt."
- **New truth scale:** "5 every claim ledger-backed or visibly filmed · 4 same, insight assumption-only · 3 a claim needs NEEDS FACT · 2 rests on a staged or unconfirmable scene · 1 message unproven after filming."
- **Wildcard cap:** "`wildcard=yes` → ≤3 on share_save, comment, brand_link, objective_fit; truth and producible scored as is". A blanket cap breaks honest scoring.

**17. L9 forbids what the method's own templates contain.**
- **Problem:** A7, B3 #8 and F11 use «WhatsApp» and «MetaPrompt» in Latin.
- **Replace:** "brand names in Cyrillic («Инстаграм», «Каспи», «2ГИС»)" → "…(«Инстаграм», «Тикток», «Каспи», «2ГИС»), except «WhatsApp» and «MetaPrompt»".
- **Also:** "no dates unless the context gives TODAY; relative deadlines" → "deadlines always relative; other dates only when TODAY is in the context". Replayed cards still carry «Ответ до 14.10 12:00».

**18. The H example teaches a D10 anti-pattern.**
- **Problem:** «Все показывают снаружи. Мы — внутри» puts «мы» in the first 2 seconds (D10 "Ad-first").
- **Replace `hook_ru` and `on_screen_ru[0]` with:** «Что внутри торта с витрины?»
- **Capacity default:** «По умолчанию: 20» is an invented number. Use «По умолчанию: +20% к обычной неделе», as in A8 #5.

**19. Reviewers lack the numbers.** Reviewers receive only F13 and G6, so they judge against "20 minutes", not L5.
- **Replace:** "Can staff film the actual card in 20 minutes with set-up? Can I answer the owner message in 15?"
  - **with:** "Is the card 1 site, ≤3 subjects, ≤4 ideas, ≤12 printed minutes, and the staff week ≤17 min with set-up, labels and tally? Is the owner message ≤7 items, one question each, ≤15 min, Russian, with defaults? (Code adds the AI greeting; do not flag its absence.)"
- **Delete** F13's "(v2: review and revision are split…)" note. Reviewers read it as their own prompt.

### C. Unverifiable rules and thresholds without numbers

**20. A6 realism math.**
- **Problem:** with "0.3–3 per 1k", the realism verdict comes out as a range. Coffee wrote «ratio ≈ 1–33».
- **Replace:** "[ASSUMPTION] 1 per 1k (report 0.3–3 as the range; the verdict uses 1)".
- **Add defaults:**
  - "close_rate: measured → owner → [ASSUMPTION] 0.25"
  - "platform_median: own last 15 posts → [ASSUMPTION] 300 for a new or <1,000-follower account"
- **Define "High-ticket multi-step purchase":** "average order ≥100 000 ₸ or a decision taking >7 days".
- **A3:** "Kaspi price far above others" → ">10% above the median of other sellers of the same SKU".

**21. A4 should_we_do_social has no hourly cost and an undefined count.**
- **Problem:** hourly cost is never asked for, and "under 5 cases" is undefined.
- **Replace:** "under 5 cases" → "with fewer than 5 new companies invoiced".
- **A8 #6 →** «Средний первый заказ новой компании (₸), ваша маржа (%) и стоимость часа сотрудника (₸)? По умолчанию: считаем только число новых компаний со счётом.»
- **A7:** arm (b) defaults to «нет» under L8. Add: "if the owner does not say «да», arm (b) is reported «не проводили» and the verdict covers (a) and (c)."

**22. A1.5 and `by_when` need a date the intake step cannot know.**
- **Problem:** intake and inputs prompts get no TODAY (CODE CHANGE #3).
- **Replace:** "number, unit, line, date" → "number, unit, line, and `by_when` as «end of week N» (week 1 = first filming week) unless the context gives TODAY".
- **A9 says "keyed"**, but clarifying questions have no key field. → "each the A8 bank text when one fits".

**23. D9 set-up floors use a range and a minimum.**
- **Replace:** "cable, amp or device 1–3" → "cable or device 1; amp with instrument 3"
- **Replace:** "client-ready state ≥2" → "2"
- **Add:** "exactly one `kind: hook` shot per idea (the card stars every hook shot «⭐ САМОЕ ВАЖНОЕ»); `talk` for every shot with `say_ru`. TAGS `subject=` may be `a+b` for comparisons."

**24. E3 rows cannot be checked as written.**
- **sales:** "sales ≥4 conversion-ready" → "sales_push: ≥4 with funnel `conversion`".
- **hiring:** "hiring `recruiting`" → "hiring: ≥60% funnel `recruiting`".
- **subject:** "No product or service in >3 ideas" is impossible for a single-service brief such as implants → "subject (the physical thing filmed: SKU, tool, room, dish): none in >3 ideas".
- **spots:** "≤3 per site across the batch" is the batch cap the salon audit blamed → "≤3 spots per weekly card; the batch uses ≥3 spots per site where they exist".
- **Add:** "≥5 of the ≥8 `ready=week1` ideas on one site", because D9 limits week 1 to one site.

**25. F3 is incomplete.** It has no rows for retention_or_loyalty, b2b_leads, should_we_do_social or other, and no mapping from its columns to `funnel`.
- **Add mapping:** "hero/reach = `attention`; proof+utility = `consideration`/`trust`; conversion = `conversion`/`retention`/`recruiting`".
- **Proposed rows:**

| request_type | Hero / reach | Proof + utility | Conversion |
|---|---|---|---|
| retention_or_loyalty | 20% | 40% | 40% |
| b2b_leads | 30% | 50% | 20% |
| should_we_do_social | 40% | 40% | 20% |
| other | 40% | 40% | 20% |

**26. Checks the model cannot perform itself.**
- **L9:** "Kazakh only after a native check" → "Kazakh words only with `NEEDS FACT (staff): проверить казахское «…»`; week-1 local markers use city, district or landmark names".
- **D6:** "(checked by 2 staff under 30)" → "propose ≤3 keywords in one `[key:other_keyword]` owner ask".
- **A5 CHANNEL:** "named person" → "a role the owner picks in the `channel_access` ask".
- **D5:** delete "unless a week-0 blind check passed…" (no step runs it) → "never in weeks 1–2".
- **D10 cliché:** "Matches a fetched convention" → "matches a convention in step-3 evidence (fetched or assumed)". Nothing is fetched today, so the rule never fires.
- **F5 boost:** "stop after 5× cap with <3 coded chats" → "stop when spend reaches the cap with <3 coded chats".

**27. D2 self-test answers have no field**, and the schema forbids extra properties.
- **Replace:** "(write the answer; a failure lowers the score)"
  - **with:** "(Stop → `why_stop`; Share/Save → `why_share_or_save`, opening with the DM line in «»; Watch, Comment, Convert → one clause each at the end of `what_happens`)".

**28. Truth-rail lexicon and the price placeholder.**
- **Problem:** errors block an idea outright, while a NEEDS FACT only gates it. The code rejects words C6.3 does not list.
- **Replace C6.3 and merge C6.15 into it:** "No «самый/самые», «лучше/лучший», «идеальный», «единственный», «№1», «дешевле всех», «гарантируем», «100% …»; no «только сегодня», «осталось N», «закрываемся», «успейте»; no «угадай(те)» outside format `guess`, «спорим», «пиши 1/2», «1 или 2», «ставь лайк»."
- **Price ideas on an empty ledger:** E3 "≥2 showing a real price" leads the model to write «от [цена] ₸», which fails the placeholder rail and blocks the idea. Add: "with no usable price, leave the price line out and add `NEEDS FACT (owner): «цена на … от … ₸»`; never a bracket."
- **C6.5:** cover any attributed quote («Покупатели спрашивают», «Частый вопрос», «Вы спрашиваете»). Code's `CUSTOMER_QUOTE` misses these and never checks n≥2.

**29. Week counts that don't add up.**
- **Problem:**
  - F6's date-bound rule ("≥4 base posts … or named NEXT BATCH slots") has nowhere to put the slots, because `idea_ids` must be pool ids.
  - F2 says the hero series runs "2 a week".
  - F6 asks for 5 week-1 videos, but D9 allows ≤4 filmed ideas.
- **Replacements:**
  - Count NEXT BATCH slots in `weeks[n].goal` as «+N NEXT BATCH: I03/why_it_costs», with idea_ids plus slots ≥4.
  - F6 week 1: "4–5 base videos (≤4 filmed + zero-staff if assets exist), ≥3 drivers, hero episode 1".
  - F2: "2 a week from week 2".
  - Check: `series[hero].idea_ids[0]` must be in `weeks[1].idea_ids`.

**30. F14 patch mechanics.**
- **Add:** "A `risks` patch replaces the whole list: repeat `TAGS` first and every open NEEDS FACT. A `hook_ru` patch also sends `on_screen_ru` with [0] = the new hook."

### D. Wasted tokens

The method is about 73k characters (~23k tokens) and goes to every model step: intake, inputs, insights (+fix), ideas (+fix), campaign and revision. About 11k characters (~15%) can move out:

| What | Size | Where it should go |
|---|---|---|
| 88 "(v2: …)" notes | 5,261 chars, ~12k tokens per run | `brain/METHOD_CHANGES.md` |
| CODE CHANGES REQUESTED | 2,902 chars | `AUDIT_v1_STATUS.md` |
| F9 internal rules, F10, F11, E4 | 1,147 + 385 + 436 + 558 chars | `brain/LOOP.md`, with a one-line pointer |
| Header "(v2 …) marks … Both bind equally. v2 keeps what the audits praised…" | — | cut |
| E1 weights "(stop 1.5, …)" | — | cut; the model doesn't need them and they invite score-gaming |
| Pinned-utility and self-incrimination caps in D10 | — | cut; keep them in E2 only |

- Many v2 notes quote the bad outputs verbatim, which can prime the model to repeat them: «Напишите в WhatsApp BA29», «Напишите BA23 — пришлём дату открытия и адрес лично», «Это {имя мастера}…», «Гитара за 59 800 ₸ — игрушка?», «Ответ: [по исходному тесту]».
- The CODE CHANGES block is stale: "uncommitted" items are now commits 5658081 and 05686ad.

### E. Other fixes v2 depends on

**Step-table and heading fixes.**
- **Step table row 2** says "Runs agent `FETCH` lines before step 3", but brain.run goes straight from inputs to insights. → "Stores FETCH lines; no fetch stage yet (CODE CHANGES 1): step 3 sees only files in CLIENT INPUTS".
- **Add to C1:** "A FETCH with no file in CLIENT INPUTS did not run: say so in E01; never cite it."
- **Rename headings to the CURRENT STEP labels code sends:**
  - "## C. Working the inputs: evidence → insights (step 3)"
  - "## F. Campaign design (step 6), review (F13) and revision (F14)"
  - Step-table row 7 should name F14 as the section for «F. Campaign design (revision)».

**Code changes that belong in the backlog.** These are not in CODE CHANGES REQUESTED yet:
- Remove the number rail from `worker_ask_ru` (finding 1).
- Take reserves only from `RESERVE:` ids that are tagged `ready=week1` and on the same site (2).
- Gate `(agent)` NEEDS FACT lines and route each line by its tag (3).
- The stale-fact question shows Latin ledger ids and asks the owner what the agent can re-fetch. Replay muzzone-viral: «Факт для ролика «Три укулеле, один аккорд. Где дорогая?» устарел или снят с сайта (u246_price). Он ещё верен?», three such lines for one idea. → re-fetch first; never an owner line.
- `fact_question_ru` labels staff text «для ролика «задание сотрудникам»».
- The reviewers' copy of the owner message should be `agent.owner_message()` output, which includes the greeting.
- Flag owner asks with more than one «?» outside a tap card.
- Make `RUBRIC_HELP` (brain.py:99–107) match E2.
- Extend `CUSTOMER_QUOTE` to `(?:клиент|покупател|пациент|гост)\w*\s+(?:часто\s+)?(?:пишут|спрашивают)|частый\s+вопрос|вы\s+(?:часто\s+)?спрашиваете`, and require n≥2 in the cited evidence claim.

**Files:**
- /tmp/claude-0/-home-user-flystuff/ed90e34e-b470-5816-9bae-4695c8c48b9b/scratchpad/brain/METHOD_v2.md
- /home/user/flystuff/smm_agent/smm/brain.py (lines 127–137, 474–506, 556–563, 618–711, 858–897)
- /home/user/flystuff/smm_agent/smm/shootcard.py
- /home/user/flystuff/smm_agent/smm/checks.py
- /tmp/claude-0/-home-user-flystuff/ed90e34e-b470-5816-9bae-4695c8c48b9b/scratchpad/brain/replay_v1/{salon,b2b,coffee,dental,muzzone-sales,muzzone-viral}/{checks,questions}.json