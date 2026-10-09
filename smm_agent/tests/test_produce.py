"""Production leg end to end with synthetic phone clips and a scripted designer/critic (no tokens):
manifest -> clip matching -> last-take cut -> edit -> AI design render + checks -> approval card."""
import json
import shutil
import subprocess

import pytest

from smm import htmlmotion, produce
from smm.facts import Fact, Ledger
from smm.handoff import Queue
from smm.llm import LLM, Backend, Tape

pytestmark = pytest.mark.skipif(not shutil.which("node") or not htmlmotion.GSAP_JS.exists(), reason="needs node")
NOW = __import__("datetime").datetime(2026, 10, 9, tzinfo=__import__("datetime").timezone.utc)
LG = Ledger([Fact("p", "Укулеле Caesar U-246 — 22 100 ₸", "web", "https://muzzone.kz/x", "2026-10-08", ["22 100 ₸"], 30)])


def ff(*a):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *a], check=True)


def design(text):
    return f"""<!doctype html><html><head>{htmlmotion.head_snippet()}</head><body>
<div id="t" style="position:absolute;left:160px;top:300px;width:700px;font:800 80px Montserrat;color:#fff;-webkit-text-stroke:3px #000">{text}</div>
<script>window.__duration=3;const tl=gsap.timeline({{paused:true}});
for (let k = 0; k < 6; k++) tl.set('#t', {{color: k % 2 ? '#ffd400' : '#ffffff', scale: k % 2 ? 1.06 : 1}}, k * 0.9);
window.__tl=tl;</script></body></html>"""


class Scripted(Backend):
    name = "scripted"

    def __init__(self):
        self.steps = []

    def raw(self, call):
        self.steps.append(call.step)
        if call.step.startswith("design:"):
            assert "look_0.jpg" in call.prompt                      # the designer is shown the real footage
            return {"html": design("Как звучит укулеле за 22 100 ₸"), "duration": 3, "on_screen_strings": [], "rationale": "r"}
        return {"verdict": "ship", "score": 8, "issues": [], "summary": "ok"}


@pytest.fixture
def run_dir(tmp_path):
    rd = tmp_path / "run"
    rd.mkdir()
    (rd / "manifest_week1.json").write_text(json.dumps([
        {"n": 1, "shot_id": "i0_0", "seconds": 2, "kind": "hook", "idea_id": "i0"},
        {"n": 2, "shot_id": "i0_1", "seconds": 2, "kind": "demo", "idea_id": "i0"}]), encoding="utf-8")
    (rd / "ideas.json").write_text(json.dumps([{"id": "i0", "hook_ru": "Как звучит укулеле за 22 100 ₸",
                                                 "on_screen_ru": [], "cta_ru": "", "what_happens": "играет",
                                                 "why_stop": "звук", "why_share_or_save": "", "first_frame": "струны"}],
                                               ensure_ascii=False), encoding="utf-8")
    (rd / "campaign.json").write_text(json.dumps({"attribution_codes": {"i0": "UK2"}}), encoding="utf-8")
    clips = tmp_path / "clips"
    clips.mkdir()
    # phone-like clips: 1 s silence, a bad take, a pause, the good take, 1 s silence (the card's protocol)
    for name, f, src in (("VID_001.mp4", 440, "testsrc2=s=1080x1920:r=30:d=8"),
                         ("VID_002.mp4", 523, "mandelbrot=s=1080x1920:r=30,trim=duration=8")):
        ff("-f", "lavfi", "-i", src, "-f", "lavfi", "-i",
           f"sine=f={f}:d=8,volume='if(between(t,1,2)+between(t,4,6.5),0.6,0)':eval=frame",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(clips / name))
    return rd, clips


def test_week_of_clips_becomes_designed_videos_with_approval_cards(run_dir):
    rd, clips = run_dir
    be = Scripted()
    q = Queue(rd / "cards")
    out = produce.produce_week(rd, clips, LG, "playbook", LLM(be, Tape(rd / "tape.jsonl")), q, "test", NOW)
    assert len(out) == 1 and out[0].ok, out[0].notes
    assert out[0].video.exists()
    assert abs(produce.duration(out[0].video) - produce.duration(rd / "produce" / "i0" / "base.mp4")) < 0.2   # full footage
    base = rd / "produce" / "i0" / "base.mp4"
    assert 3.5 < produce.duration(base) < 7.0               # two cut takes, not the whole 16 s of raw footage
    cards = q.all()
    assert len(cards) == 1 and cards[0].kind == "approval" and "sha256" in cards[0].why


def test_last_take_is_used(run_dir):
    rd, clips = run_dir
    m = json.loads((rd / "manifest_week1.json").read_text())
    segs = produce.cut_plan({"id": "i0"}, {"i0_0": clips / "VID_001.mp4", "i0_1": clips / "VID_002.mp4"}, m)
    assert all(3.6 <= s["start"] <= 4.2 for s in segs), segs   # the second (good) take starts at 4 s


def test_wrong_clip_count_asks_the_staff_instead_of_guessing(run_dir):
    rd, clips = run_dir
    (clips / "VID_002.mp4").unlink()
    q = Queue(rd / "cards")
    out = produce.produce_week(rd, clips, LG, "playbook", LLM(Scripted(), Tape(rd / "t.jsonl")), q, "test", NOW)
    assert not out[0].ok and q.all()[0].role == "STAFF" and not (rd / "produce").exists()
