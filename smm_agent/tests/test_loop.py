import json

from smm import brain as B
from smm import loop as L


def client(tmp_path):
    d = tmp_path / "acme"
    run = d / "campaigns" / "r1"
    run.mkdir(parents=True)
    ideas = [{"id": "ID01", "driver": "sensory", "format": "close_sound"},
             {"id": "ID02", "driver": "practical_value", "format": "check_before_buy"}]
    (run / "ideas.json").write_text(json.dumps(ideas), encoding="utf-8")
    (run / "campaign.json").write_text(json.dumps({"attribution_codes": {"ID01": "MK3", "ID02": "PT7"}}), encoding="utf-8")
    return d


CSV = """post_id,arm,platform,posted_at,views,shares,saves
p1,ID01,tiktok,2026-10-12,4000,30,12
p2,ID02,tiktok,2026-10-13,300,1,9
p3,ID01,tiktok,2026-10-14,5200,41,20
p4,ID02,tiktok,2026-10-15,250,0,4
p5,ID01,tiktok,2026-10-16,3900,22,15
p6,ID02,tiktok,2026-10-17,410,2,11
"""


def test_metrics_become_arm_posteriors_that_steer_next_weeks_selection(tmp_path):
    d = client(tmp_path)
    r = L.record_metrics(d, CSV, {"baselines": {"tiktok": 1000}})
    assert r["added"] == ["p1", "p2", "p3", "p4", "p5", "p6"] and not r["problems"]
    again = L.record_metrics(d, CSV + "p7,ID09,tiktok,2026-10-18,100,0,0\n", {"baselines": {"tiktok": 1000}})
    assert again["added"] == [] and any("ID09" in n for n in again["notes"])           # idempotent; unknown idea refused
    st = json.loads((d / "engine_state.json").read_text())
    assert st["summary"]["driver:sensory"]["mean"] > 0 > st["summary"]["driver:practical_value"]["mean"]
    # next week: two equally scored ideas; the data now prefers the sensory/close_sound arm
    a = {"id": "x", "driver": "practical_value", "format": "check_before_buy", "production": {"mode": "worker"},
         "rubric": {k: 4 for k in B.RUBRIC}}
    b = {"id": "y", "driver": "sensory", "format": "close_sound", "production": {"mode": "worker"},
         "rubric": {k: 4 for k in B.RUBRIC}}
    assert B.select([a, b], 1, B.load_weights(), st["summary"], explore_share=0)[0]["id"] == "y"


def test_no_posts_no_beliefs(tmp_path):
    d = client(tmp_path)
    r = L.record_metrics(d, "post_id,arm,platform,posted_at,views\n", {})
    st = json.loads((d / "engine_state.json").read_text())
    assert r["added"] == [] and st["posts"] == 0 and st["summary"] == {}


def test_coded_whatsapp_inquiries_per_idea(tmp_path):
    d = client(tmp_path)
    export = ("12.10.2026, 10:01 - Айгерим: Здравствуйте, МК3, сколько стоит?\n"
              "12.10.2026, 10:05 - Muzzone: Добрый день!\n"
              "13.10.2026, 18:20 - Ерлан: pt7 есть в наличии?\n"
              "13.10.2026, 18:22 - Айгерим: МК3 ещё раз\n")
    out = L.record_leads(d, export, {"Muzzone"})
    assert out["ID01"]["customers"] == 1 and out["ID02"]["customers"] == 1


def test_learnings_are_pooled_with_n_and_interval(tmp_path):
    d = client(tmp_path)
    L.record_metrics(d, CSV, {"baselines": {"tiktok": 1000}})
    kb = tmp_path / "kb"
    kb.mkdir()
    new = L.learn(d, {"vertical": "music_instruments_retail"}, kb)
    arms = {x["arm"] for x in new}
    assert arms == {"driver:sensory", "engine:close_sound", "driver:practical_value", "engine:check_before_buy"}
    assert all(x["n"] == 3 and x["interval90_x"][0] < x["x_vs_baseline"] < x["interval90_x"][1] for x in new)
    L.learn(d, {"vertical": "music_instruments_retail"}, kb)                             # re-run replaces, not appends
    assert len((kb / "learnings.jsonl").read_text().splitlines()) == 4
