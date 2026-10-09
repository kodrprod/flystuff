"""The brain's code side: input inventory, truth/feasibility checks, selection, and a full run with a scripted
model (no tokens). The model's judgment itself is not tested here; that is what the stress-test workflow and
real audience data are for."""
import json

import pytest

from smm import brain as B
from smm.facts import Fact, Ledger
from smm.llm import LLM, Backend, Tape


def ledger():
    return Ledger([Fact("price", "Укулеле — 22 100 ₸", "web", "https://x.kz/u", "2026-10-08", ["22 100 ₸"], 30),
                   Fact("wa", "WhatsApp +7 701 0987734", "web", "https://x.kz/c", "2026-10-08", ["+7 701 0987734"], 30)])


def idea(i, driver="watch", fmt="E04", mode="worker", hook="Как звучит укулеле за 22 100 ₸?", shots=None, **kw):
    d = {"id": i, "title": i, "insight_ids": ["in1"], "driver": driver, "format": fmt, "funnel": "attention",
         "hook_ru": hook, "first_frame": "руки на струнах", "on_screen_ru": [], "what_happens": "играет", "why_stop": "звук",
         "why_share_or_save": "полезно", "comment_prompt_ru": "", "cta_ru": "", "production": {
             "mode": mode, "worker_shots": shots if shots is not None else [
                 {"what_ru": "сыграть аккорд", "location": "зал", "seconds": 10, "takes": 2, "say_ru": "", "kind": "demo"}],
             "ai_parts": "", "people_on_camera": 1},
         "facts_used": [], "kpi": "saves", "risks": [], "rubric": {k: 3 for k in B.RUBRIC}}
    d.update(kw)
    return d


NOW = __import__("datetime").datetime(2026, 10, 9, tzinfo=__import__("datetime").timezone.utc)


def test_true_price_passes_invented_price_becomes_owner_question():
    ok = B.check_idea(idea("a"), ledger(), {"in1"}, NOW)
    assert ok == {"errors": [], "needs_facts": [], "warnings": []} or not ok["errors"] and not ok["needs_facts"]
    bad = B.check_idea(idea("b", hook="Укулеле всего за 9 900 ₸!"), ledger(), {"in1"}, NOW)
    assert bad["needs_facts"] and not any("R6" in e for e in bad["errors"])


def test_idea_must_cite_real_insights_and_fit_the_staff_budget():
    r = B.check_idea(idea("c", insight_ids=["nope"]), ledger(), {"in1"}, NOW)
    assert any("unknown insights" in e for e in r["errors"])
    long = [{"what_ru": "длинный дубль", "location": f"l{j}", "seconds": 60, "takes": 3, "say_ru": "", "kind": "demo"} for j in range(5)]
    r = B.check_idea(idea("d", shots=long), ledger(), {"in1"}, NOW)
    assert any("staff minutes" in e for e in r["errors"])
    r = B.check_idea(idea("e", shots=[]), ledger(), {"in1"}, NOW)
    assert any("no worker shots" in e for e in r["errors"])


def test_evidence_must_point_at_something_real():
    ins = {"evidence": [{"id": "e1", "kind": "fact", "claim": "x", "source": "price", "confidence": "verified"},
                        {"id": "e2", "kind": "market", "claim": "y", "source": "my intuition", "confidence": "likely"},
                        {"id": "e3", "kind": "market", "claim": "z", "source": "my intuition", "confidence": "assumption"}],
           "insights": [{"id": "i1", "insight": "", "tension": "", "evidence_ids": ["e1", "e9"], "who_feels_it": "",
                         "content_reality": "", "strength": 3}]}
    p = B.check_insights(ins, ledger(), {"/c/research/a.json"})
    assert any("e2" in x for x in p) and not any("e3" in x for x in p) and any("i1" in x for x in p)


def test_selection_spreads_drivers_and_keeps_exploration_slots():
    ideas = [idea(f"same{j}", driver="convert", fmt="E08", rubric={k: 5 for k in B.RUBRIC}) for j in range(6)]
    ideas += [idea("story", driver="share", fmt="E22"), idea("faq", driver="save", fmt="E05"),
              idea("odd", driver="comment", fmt="E23", rubric={k: 2 for k in B.RUBRIC})]
    sl = B.select(ideas, 6, B.load_weights())
    drivers = [i["driver"] for i in sl]
    assert drivers.count("convert") <= 3 and {"share", "save", "comment"} & set(drivers)
    assert any(i["_why"] == "explore" for i in sl)


def test_audience_data_overrides_the_prior():
    a, b = idea("a", driver="convert", rubric={k: 4 for k in B.RUBRIC}), idea("b", driver="share", rubric={k: 3 for k in B.RUBRIC})
    stats = {"driver:share": {"n": 12, "mean": 1.2, "sd": 0.3}, "driver:convert": {"n": 12, "mean": -0.8, "sd": 0.3}}
    assert B.select([a, b], 1, B.load_weights(), None, explore_share=0)[0]["id"] == "a"
    assert B.select([dict(a), dict(b)], 1, B.load_weights(), stats, explore_share=0)[0]["id"] == "b"


def test_week_plan_respects_the_20_minute_budget():
    ideas = [idea(f"v{j}", shots=[{"what_ru": "x", "location": f"loc{j}", "seconds": 40, "takes": 3, "say_ru": "",
                                  "kind": "demo"}]) for j in range(6)]
    for i in ideas:
        i["_value"] = 1.0
    ids, shots, mins = B.plan_week(ideas, 20.0)
    assert 0 < len(ids) < 6 and mins <= 17.0


class Scripted(Backend):
    """Plays fixed outputs per step prefix; records which steps ran."""
    name = "scripted"

    def __init__(self, outs):
        self.outs, self.calls = outs, []

    def raw(self, call):
        self.calls.append(call.step)
        return self.outs[call.step.split(":")[0]]


def test_full_run_writes_campaign_questions_codes_and_shoot_card(tmp_path):
    cdir = tmp_path / "clients" / "acme"
    (cdir / "research").mkdir(parents=True)
    (cdir / "research" / "sales.json").write_text(json.dumps([{"sku": "u", "units": 3}]), encoding="utf-8")
    ledger().dump(cdir / "facts.jsonl")
    (cdir / "profile.json").write_text(json.dumps({"name": "Acme", "vertical": "music"}), encoding="utf-8")
    method = tmp_path / "METHOD.md"
    method.write_text("# method\nbe good", encoding="utf-8")
    ideas = [idea(f"i{j}", driver=d, fmt=f) for j, (d, f) in enumerate(
        [("watch", "E04"), ("share", "E12"), ("save", "E06"), ("follow", "E14"), ("stop", "E10"),
         ("convert", "E08"), ("comment", "E23"), ("share", "E02"), ("save", "E01")])]
    ideas[1]["hook_ru"] = "Скидка 50% только сегодня"                       # invented -> owner question, not shipped
    ideas[2]["insight_ids"] = ["zzz"]                                      # not rooted -> error -> fix round
    ideas[0]["cta_ru"] = "Напишите в WhatsApp {CODE}"
    ideas[0]["risks"] = ["NEEDS FACT: условия рассрочки"]
    ideas[0]["rubric"] = {k: 5 for k in B.RUBRIC}                          # top prior -> certainly in the slate
    outs = {
        "intake": {"request_type": "sales_push", "reframed_request": "r", "business_objective": "b",
                   "marketing_objective": "m", "success_metric": {"name": "WhatsApp chats", "how_measured": "codes",
                                                                  "target": "30", "by_when": "2026-12-31"},
                   "leading_indicators": ["saves"], "constraints": [], "assumptions": [],
                   "clarifying_questions": ["Есть ли бюджет на рекламу?"], "push_back": ""},
        "inputs": {"have": [{"input": "site", "what_it_gives": "prices"}],
                   "missing": [{"input": "sales by category", "why_it_matters": "focus", "how": "export", "who": "owner",
                                "owner_minutes": 5, "fallback_if_missing": "site stock", "blocks_step": "none"}]},
        "insights": {"evidence": [{"id": "e1", "kind": "fact", "claim": "c", "source": "price", "confidence": "verified"}],
                     "insights": [{"id": "in1", "insight": "x", "tension": "t", "evidence_ids": ["e1"], "who_feels_it": "w",
                                   "content_reality": "r", "strength": 4}]},
        "ideas": {"ideas": ideas},
        "ideas-fix": {"ideas": ideas},
        "campaign": {"name": "Звук решает", "big_idea": "b", "single_minded_message_ru": "s", "why_this_wins": "w",
                     "series": [], "offer": {"needed": False, "proposal": "", "fact_ids": [], "needs_owner_approval": False},
                     "channels": [{"channel": "TikTok", "role": "reach"}],
                     "weeks": [{"week": 1, "goal": "g", "idea_ids": ["i0"], "worker_ask_ru": "снять", "ai_work": "монтаж"}],
                     "measurement": {"success_metric": "chats", "attribution": "codes", "leading_indicators": [],
                                     "review_cadence": "weekly"},
                     "decision_rules": ["scale arms with P(best)>0.9"], "learning_questions": [],
                     "owner_asks": [{"ask": "consent to film staff", "why": "faces", "minutes": 2}], "risks": []},
        "review": {"persona": "boss", "score": 7, "would_approve": True, "best_idea": "i0", "refutations": []},
    }
    be = Scripted(outs)
    llm = LLM(be, Tape(tmp_path / "tape.jsonl"))
    cl = B.Client.load("acme", tmp_path / "clients")
    br = B.run(cl, "Продайте больше укулеле", llm, method_path=method, slate=6, now=NOW, run_id="t1", fetch=None)
    out = cdir / "campaigns" / "t1"
    for f in ("inventory", "intake", "inputs", "insights", "ideas", "selection", "campaign", "questions"):
        assert (out / f"{f}.json").exists(), f
    sel = json.loads((out / "selection.json").read_text())
    assert br.checks["ideas"]["i1"]["needs_facts"] and not br.checks["ideas"]["i1"]["errors"]
    assert "i2" in sel["blocked"] and "ideas-fix:acme" in be.calls      # the fix round ran; still broken -> blocked
    camp = json.loads((out / "campaign.json").read_text())
    assert len(camp["attribution_codes"]) == len(sel["slate"]) and len(set(camp["attribution_codes"].values())) == len(sel["slate"])
    qs = " ".join(q["q"] for q in br.questions)
    assert "бюджет" in qs and "sales by category" in qs and "consent" in qs and "i1" in qs
    assert (out / "shoot_card_week1_ru.txt").read_text().startswith("Это ИИ-ассистент")
    saved = {i["id"]: i for i in json.loads((out / "ideas.json").read_text())}
    assert saved["i0"]["cta_ru"] == "Напишите в WhatsApp " + camp["attribution_codes"]["i0"]
    assert "условия рассрочки" in qs
    md = (out / "campaign.md").read_text()
    assert "Звук решает" in md and "Questions for the owner" in md
    assert "sales.json" in json.dumps(br.steps["inventory"]) and be.calls[0].startswith("intake")


def test_missing_method_is_an_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        B.method_text(tmp_path / "nope.md")


def test_method_defines_the_categorical_vocabulary():
    m = """### D2. Drivers (the `driver` field uses these exact slugs)
| driver | Mechanism |
|---|---|
| sensory | close sound |
| relief | anxiety |

Self-test table:
| behaviour | Test |
| stop | x |

### D3. Engines (the `format` field uses these exact slugs)
| format | Move |
|---|---|
| close_sound | loop |

| Insight type | Engines |
| myth | myth_check |

### D4. Next
"""
    v = B.method_vocab(m)
    assert v == {"driver": ["sensory", "relief"], "format": ["close_sound"]}
    sch = B.ideas_schema(v)["properties"]["ideas"]["items"]["properties"]
    assert sch["driver"]["enum"] == ["sensory", "relief"] and sch["format"]["enum"] == ["close_sound"]
    assert B.ideas_schema(B.method_vocab("no tables")) is B.IDEAS_SCHEMA


def test_evidence_sources_with_method_prefixes():
    lg, files = ledger(), {"/c/research/stock.json"}
    assert B.source_is_real("fact:price", lg, files) and B.source_is_real("file:research/stock.json#row 4", lg, files)
    assert not B.source_is_real("fact:nope", lg, files) and not B.source_is_real("file:other.json", lg, files)
    assert B.source_is_real("https://muzzone.kz/x", lg, files)
