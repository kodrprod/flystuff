# Audit of the method-v1 stress runs: code-caused failures and their status

Source: `brain/audits_v1.json` (6 independent per-case audits of real `agent plan` runs, 2026-10-10), scoreboard
`brain/board_v1.json`. Only failures whose cause is **code** are listed (55 of 105; the rest are method,
model compliance or inputs and go into method v2). Verified by `python -m smm.replay` on the 6 recorded runs
(0 model calls) and `tests/test_replay.py`.

**Status: 31 fixed, 18 partial, 6 open.**

| # | case | severity | failure (short) | status | how / what is left |
|---|---|---|---|---|---|
| 1 | muzzone-viral | fatal | The deliverables that actually go out (staff shoot card, slate cards, filming line) are pre-revision. The revision exists only as prose in campaign.we… | fixed | brain.deliverables + idea_patches; replay-verified |
| 2 | muzzone-viral | fatal | The owner card that is actually sent skips every revised owner ask. It reintroduces the chat-export ask that the revision withdrew over privacy, carri… | fixed | owner card = final campaign.owner_asks; Russian-only; no past dates |
| 3 | muzzone-viral | major | The facts item asks the owner, in English developer strings cut off at 90 characters, to confirm facts for an idea that isn't on the slate and arithme… | partial | Russian per-fact questions, publish ideas only, no truncation; derived facts are not re-computed after supersede |
| 4 | muzzone-viral | major | Agent-fetchable Tier-0 inputs were listed as missing and never fetched. The insights therefore rest on zero customer language, the A7 disguised-proble… | open | agent-side research (reviews, peers, demand phrases) needs a web-enabled step: model calls |
| 5 | muzzone-viral | major | Selection ignored the awareness mix and never picked a declared wildcard, so the slate for a 'viral' brief is bottom-funnel and ad-like. The idea the … | partial | reach quota for awareness/launch requests; no wildcard flag in the schema yet |
| 6 | muzzone-viral | major | The staff-minute model is unrealistic: no instrument set-up, no skill prerequisite, no uploads. The card cannot be filmed in the stated time. | partial | 0.75 min set-up per extra product per spot; no skill prerequisites, no upload time |
| 7 | muzzone-viral | major | The shoot card's hard-coded audio tips contradict the weak-phone constraint, the shot instructions and the revision. For a concept built on close soun… | partial | generic 20-30 cm tips + profile card_tips_ru; no per-idea prep_ru field, no tip/shot conflict check |
| 8 | muzzone-viral | major | The review gate is not a gate. Both personas approved at 6/10, which F13 forbids. After the revision both still scored 6/10 with 9 new majors, the pla… | partial | approval decided in code (>=7, no fatal), NOT APPROVED banner; no second revision round |
| 9 | muzzone-viral | major | The model has no clock, so the intake deadlines had passed before the owner could see them and dates conflict across artifacts. | fixed | TODAY in the campaign prompt; owner items with past dates are refused |
| 10 | muzzone-viral | minor | Smaller code defects in what humans read: an empty engine field, garbled week lines, a contingent idea in the week-1 slate, and two conflicting staff … | partial | render uses format; reply/vote formats never in week 1; no available_from_week field |
| 11 | muzzone-sales | fatal | The revision never reaches the files staff and the owner use. The shoot card, manifest, slate copy, attribution codes and owner card are all built fro… | fixed | same as 1 |
| 12 | muzzone-sales | major | The slate's 'diversity' is only diversity of labels. Most picks are the same product pair at the same location, and the diagnostic across 4 lines cann… | open | no line/primary_sku fields; SKU diversity not enforced |
| 13 | muzzone-sales | major | The owner card is stale, duplicated and partly English, and it defers the asks the revision actually needs. | fixed | same as 2 |
| 14 | muzzone-sales | major | There is no customer evidence at all. The Tier-0 fetches the agent planned, all of public data it could have fetched itself, were never run, so the he… | open | same as 4 |
| 15 | muzzone-sales | major | The shoot card contradicts itself and the method, and the shot order breaks the physical sequence. | partial | shots grouped per idea in process order, 'send as file' tip; no product prefix per shot |
| 16 | muzzone-sales | major | The attribution scheme contradicts itself, and the plan's counting depends on account access that the owner card never requests. | open | attribution mode / access consistency not checked |
| 17 | muzzone-sales | major | Several truth problems in the slate get past the rails: dropped fact qualifiers, an implied 'only difference' claim, an unfilled placeholder, and fact… | partial | placeholders and retired cited facts caught; dropped qualifiers / 'only difference' not detected |
| 18 | muzzone-sales | minor | The review step runs without the method and judges prose instead of the deliverables, so the approval flags are meaningless. | fixed | review prompt = method F13+G6 + the real shoot card and owner message |
| 19 | dental | fatal | The week-1 staff shoot card and manifest come from the slate chosen before the review, so they contradict the revised plan. They film the removed pati… | fixed | same as 1 |
| 20 | dental | major | Code never sees the NEEDS FACT items the model declared, so selection treats ideas that cannot be produced as ready. | fixed | declared NEEDS FACT gates filming and becomes an owner question |
| 21 | dental | major | The slate leaves out the price/friction insight on the bottleneck the agent itself hypothesised. Code picked a wildcard and a reply video that can onl… | fixed | top-insight quota; reply/vote not in week 1; pool passed to campaign and revision |
| 22 | dental | major | No evidence was collected. Every insight is the model's prior, so the run never saw the category's real conventions, real patient wording or the actua… | open | same as 4 |
| 23 | dental | major | The owner card is long, duplicated, partly in English and stale. Meanwhile the revised campaign's sharp Russian asks, including permission for the pri… | fixed | same as 2 |
| 24 | dental | major | Idea-level fixes from the review never reach the ideas, so the copy staff film and the editor burns in is the version the reviewers rejected. | fixed | idea_patches applied and re-checked |
| 25 | dental | minor | The shoot card uses the retail/music-shop template in a dental clinic, with a sound-distance rule that contradicts the method. | fixed | generic card + profile tips + business name |
| 26 | dental | minor | Attribution codes are hardcoded to campaign index 1, so every client and every sprint reuses BA23–BA32. | fixed | per-client campaign counter in codes.json |
| 27 | dental | minor | The review gate is not enforced and the owner-facing file hides the remaining problems: the after-review 'approves' at score 6, and campaign.md shows … | partial | approval in code, both rounds rendered; legal/consent majors do not block ideas |
| 28 | dental | minor | Code checks fight the method and the case: the H4 'is it specific?' warning fires on 22 of 24 hooks in a regulated case with an empty ledger, and the … | fixed | H4 silent with empty ledger; «Угадайте» allowed for the guess format |
| 29 | coffee | fatal | The staff shoot card is the pre-revision plan. 8 of its 11 shots film content the revised campaign dropped or rewrote, including the anti-demand line … | fixed | same as 1 |
| 30 | coffee | fatal | The owner message is half English, asks superseded v1 questions with defaults that lock in the rejected mechanic, and defers every critical v2 ask. | fixed | same as 2 |
| 31 | coffee | major | Selection put ideas whose inputs cannot exist in week 1 into the slate, and scheduled two of them for filming. The card also co-schedules contradictor… | partial | facts and prior-post gating; no depends_on / site_state |
| 32 | coffee | major | Later weeks are starved: the campaign step sees only the 8-idea slate, so weeks 2 and 3 (D−11 to D+2, the conversion window) carry 2 posts each. | partial | pool passed to campaign; no per-week selection |
| 33 | coffee | major | Client-independent Tier-0 agent inputs were listed but never fetched, so all 10 insights are assumption-only (strength ≤2) and the 'break the conventi… | open | same as 4 |
| 34 | coffee | major | The shoot card template is the music store's: wrong business noun, instrument and amp distance rules that contradict the shots, and no consent step be… | fixed | vertical tips + consent line when faces are filmed |
| 35 | coffee | major | Campaign-level audience copy never passes the truth and hook rails. | fixed | rails on message, offer, week-1 staff ask |
| 36 | coffee | major | Per-video WhatsApp codes collide across runs, and codes were assigned to ideas the revision dropped. | fixed | codes only for published ideas, never reused |
| 37 | coffee | minor | The reviewers approved at score 6, which F13 forbids, and the stress board counts it as approval. | fixed | same as 8 (gate) |
| 38 | coffee | minor | campaign.md (owner-facing) is English, internally contradictory, and has empty fields. | partial | built from the final plan, labelled internal; owner-facing text is the Russian owner message |
| 39 | b2b | fatal | The week-1 staff shoot card was written before the revision and contradicts the final campaign. Staff would film retired, held, dropped and forbidden … | fixed | same as 1 |
| 40 | b2b | fatal | The owner card ships the pre-revision asks, half as English labels and one with a false privacy promise. All 7 revised owner_asks are deferred, includ… | partial | final asks are the source; no 'blocking' flag |
| 41 | b2b | major | Customer quotes with zero chats behind them pass the rails, and the model's own NEEDS FACT flags do not stop filming. ID07, built on an invented chat … | fixed | R7-QUOTE rail; NEEDS FACT gates filming |
| 42 | b2b | major | Selection and the minute plan ignore what each idea needs before it can exist. An impossible idea takes a slate slot, and filmed ideas depend on foota… | partial | fact/prior-post gating; no footage dependencies |
| 43 | b2b | major | The run's own outputs contradict each other on dates, cost and what counts, which is exactly what a skeptical owner will seize on. | partial | summary from the final campaign; no intake patch |
| 44 | b2b | major | The revision turned ID13 into a different hero idea under the same id. The new concept never went through step-4 checks, and its arm labels are wrong.… | partial | pool offered to the revision; no check against reusing an id for a new concept |
| 45 | b2b | major | The review step runs without the METHOD, so F13's persona checklists and approval rule are never applied. | fixed | same as 18 |
| 46 | b2b | major | The shoot card template is the music-store client's and leaves out what staff need to know. | partial | header and vertical tips; card does not print each shot's exact on-screen text |
| 47 | b2b | minor | Noisy and false-positive checks reach the owner. | fixed | negated claims pass; H4 noise removed |
| 48 | salon | fatal | The week-1 artefacts code writes contradict the revised campaign. The shoot card films the wrong ideas and none of the hero. | fixed | same as 1 |
| 49 | salon | fatal | The owner message that would actually be sent is unreadable, duplicated, and leaves out every approval the final plan depends on. | fixed | same as 2 |
| 50 | salon | fatal | The slate does not answer «why pay more», the boss's actual problem. The pool's price/backstage ideas were never selected, and the campaign step could… | fixed | top-insight quota |
| 51 | salon | major | The shoot card is physically unproducible in 17 minutes. Steps are out of process order and need incompatible nail states. | partial | process order per idea; no needs_state |
| 52 | salon | major | The shoot card text is a hard-coded music-store template. It contradicts the close-sound rule and assumes an iPhone. | fixed | vertical tips; device-neutral wording |
| 53 | salon | major | WhatsApp codes repeat across runs and clients, which will corrupt attribution. | fixed | same as 26 |
| 54 | salon | minor | Truth-rail false positives become nonsense owner questions. | fixed | urgency needs offer/stock/date context |
| 55 | salon | minor | campaign.md misreports the plan. | fixed | same as 1 |
