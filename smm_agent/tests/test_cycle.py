"""One full weekly cycle through the real commands, offline (scripted model, synthetic phone clips, labelled
synthetic metrics): plan -> shoot card -> clips -> produce -> package BLOCKED -> owner approves -> package READY ->
metrics + WhatsApp codes -> engine state -> next week's selection prefers what the audience preferred."""
import json
import shutil
import subprocess

import pytest

from smm import agent, brain, htmlmotion
from smm.facts import Fact, Ledger
from smm.llm import LLM, Backend, Tape

pytestmark = pytest.mark.skipif(not shutil.which("node") or not htmlmotion.GSAP_JS.exists(), reason="needs node")
NOW = __import__("datetime").datetime(2026, 10, 9, tzinfo=__import__("datetime").timezone.utc)


def ff(*a):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *a], check=True)


def idea(i, driver, fmt, hook, loc):
    return {"id": i, "title": i, "insight_ids": ["I01"], "driver": driver, "format": fmt, "funnel": "attention",
            "hook_ru": hook, "first_frame": "руки", "on_screen_ru": [hook], "what_happens": "играет",
            "why_stop": "звук", "why_share_or_save": "другу", "comment_prompt_ru": "", "cta_ru": "Код {CODE} в WhatsApp",
            "production": {"mode": "worker", "worker_shots": [{"what_ru": "сыграть", "location": loc, "seconds": 2,
                                                               "takes": 2, "say_ru": "", "kind": "demo"}],
                           "ai_parts": "", "people_on_camera": 0},
            "facts_used": ["u"], "kpi": "saves", "risks": [], "rubric": {k: 4 for k in brain.RUBRIC}}


DESIGN = f"""<!doctype html><html><head>{htmlmotion.head_snippet()}</head><body>
<div id="b" style="position:absolute;left:0;top:500px;width:1080px;height:600px;background:#000;opacity:.5"></div>
<div style="position:absolute;left:160px;top:600px;width:700px;font:800 80px Montserrat;color:#fff">Укулеле за 22 100 ₸</div>
<script>window.__duration=3;const tl=gsap.timeline({{paused:true}});
for(let k=1;k<9;k++) tl.set('#b',{{opacity:k%2?.15:.5}},k*0.9); window.__tl=tl;</script></body></html>"""


class Scripted(Backend):
    name = "scripted"

    def __init__(self, outs):
        self.outs = outs

    def raw(self, call):
        k = call.step.split(":")[0]
        if k == "design":
            return {"html": DESIGN, "duration": 3, "on_screen_strings": [], "rationale": "r"}
        if k == "critic":
            return {"verdict": "ship", "score": 8, "issues": [], "summary": "ok"}
        return self.outs[k]


def test_one_full_week(tmp_path, monkeypatch):
    clients = tmp_path / "clients"
    cdir = clients / "shop"
    cdir.mkdir(parents=True)
    Ledger([Fact("u", "Укулеле Caesar U-246 — 22 100 ₸", "web", "https://shop.kz/u", "2026-10-08", ["22 100 ₸"], 30)]
           ).dump(cdir / "facts.jsonl")
    (cdir / "profile.json").write_text(json.dumps({"name": "Shop", "vertical": "music", "baselines": {"tiktok": 1000}}),
                                       encoding="utf-8")
    method = tmp_path / "METHOD.md"
    method.write_text("# method", encoding="utf-8")
    monkeypatch.setenv("SMM_CLIENTS_DIR", str(clients))
    ideas = [idea("ID01", "sensory", "close_sound", "Укулеле за 22 100 ₸", "витрина"),
             idea("ID02", "practical_value", "check_before_buy", "Проверьте это до покупки", "склад")]
    ideas += [dict(idea(f"ID0{j}", "story", "real_case", "История покупателя", "зал"),
                   production={"mode": "ai", "worker_shots": [], "ai_parts": "x", "people_on_camera": 0})
              for j in range(3, 9)]
    outs = {
        "intake": {"request_type": "sales_push", "reframed_request": "r", "business_objective": "b", "marketing_objective": "m",
                   "success_metric": {"name": "chats", "how_measured": "codes", "target": "10", "by_when": "2026-12-01"},
                   "leading_indicators": [], "constraints": [], "assumptions": [], "clarifying_questions": [], "push_back": ""},
        "inputs": {"have": [], "missing": []},
        "insights": {"evidence": [{"id": "E01", "kind": "fact", "claim": "c", "source": "fact:u", "confidence": "verified"}],
                     "insights": [{"id": "I01", "insight": "x", "tension": "t", "evidence_ids": ["E01"], "who_feels_it": "w",
                                   "content_reality": "r", "strength": 4}]},
        "ideas": {"ideas": ideas},
        "campaign": {"name": "C", "big_idea": "b", "single_minded_message_ru": "s", "why_this_wins": "w", "series": [],
                     "offer": {"needed": False, "proposal": "", "fact_ids": [], "needs_owner_approval": False},
                     "channels": [], "weeks": [{"week": 1, "goal": "g", "idea_ids": ["ID01", "ID02"], "worker_ask_ru": "x",
                                                "ai_work": "y"}],
                     "measurement": {"success_metric": "chats", "attribution": "codes", "leading_indicators": [],
                                     "review_cadence": "weekly"},
                     "decision_rules": [], "learning_questions": [], "owner_asks": [], "risks": []},
        "review": {"persona": "boss", "score": 8, "would_approve": True, "best_idea": "ID01", "refutations": []},
    }
    llm = LLM(Scripted(outs), Tape(tmp_path / "tape.jsonl"))

    # 1 plan
    br = brain.run(brain.Client.load("shop"), "Продайте больше", llm, method_path=method, slate=8, now=NOW,
                   run_id="w1", fetch=None)
    run = cdir / "campaigns" / "w1"
    manifest = json.loads((run / "manifest_week1.json").read_text())
    assert sorted(m["idea_id"] for m in manifest) == ["ID01", "ID02"]
    assert "Это ИИ-ассистент" in (run / "shoot_card_week1_ru.txt").read_text()

    # 2 the staff send clips in card order
    clips = tmp_path / "clips"
    clips.mkdir()
    for n, (src, f) in enumerate((("testsrc2=s=1080x1920:r=30:d=6", 440), ("mandelbrot=s=1080x1920:r=30,trim=duration=6", 523))):
        ff("-f", "lavfi", "-i", src, "-f", "lavfi", "-i", f"sine=f={f}:d=6,volume='if(between(t,1,4.5),0.6,0)':eval=frame",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(clips / f"VID_{n:03d}.mp4"))

    # 3 produce (the designer/critic are the scripted model)
    from smm import produce
    res = produce.produce_week(run, clips, Ledger.load(cdir / "facts.jsonl"), "playbook", llm, client="shop", now=NOW)
    assert len(res) == 2 and all(r.ok and r.video.exists() for r in res)

    # 4 package without approval: blocked
    assert agent.main(["package", "--client", "shop"]) == 0
    pk = json.loads((run / "publish_packages.json").read_text())
    assert all(any("R2" in p for p in x["problems"]) for x in pk)
    code = br.steps["campaign"]["attribution_codes"]["ID01"]
    assert code in pk[0]["caption"] or code in pk[1]["caption"]

    # 5 owner approves ID01's exact file + caption; package passes for it only
    one = [x for x in pk if x["idea"] == "ID01"][0]
    agent.main(["approve", "--client", "shop", "--video", one["video"], "--caption", one["caption"], "--approver", "owner"])
    agent.main(["package", "--client", "shop"])
    pk = {x["idea"]: x for x in json.loads((run / "publish_packages.json").read_text())}
    assert pk["ID01"]["problems"] == [] and pk["ID01"]["tiktok_draft_args"]["mode"] == "UPLOAD_TO_DRAFT"
    assert pk["ID02"]["problems"]

    # 6 a week of metrics (SYNTHETIC, labelled) + WhatsApp export -> engine -> next week's selection
    csvp = tmp_path / "metrics_SYNTHETIC.csv"
    csvp.write_text("post_id,arm,platform,posted_at,views\n"
                    "a,ID01,tiktok,2026-10-12,5000\nb,ID02,tiktok,2026-10-13,300\n"
                    "c,ID01,tiktok,2026-10-14,4200\nd,ID02,tiktok,2026-10-15,260\n", encoding="utf-8")
    wa = tmp_path / "wa.txt"
    wa.write_text(f"12.10.2026, 10:01 - Клиент: {code} сколько стоит?\n", encoding="utf-8")
    assert agent.main(["metrics", "--client", "shop", "--csv", str(csvp), "--whatsapp", str(wa), "--shop-sender", "Shop"]) == 0
    leads = json.loads((cdir / "metrics" / "leads.json").read_text())
    assert leads["ID01"]["customers"] == 1
    st = json.loads((cdir / "engine_state.json").read_text())
    a, b = (dict(ideas[1], id="next_a"), dict(ideas[0], id="next_b"))
    pick = brain.select([a, b], 1, brain.load_weights(), st["summary"], explore_share=0)[0]["id"]
    assert pick == "next_b"                       # the sensory/close_sound arm the audience preferred
