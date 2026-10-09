"""designer.design_video end to end with a scripted model: real Chromium render, real composite over footage, real
checks and contact sheet. Only the model's taste is scripted."""
import json
import shutil
import subprocess

import pytest

from smm import designer as D
from smm import htmlmotion
from smm.facts import Fact, Ledger
from smm.llm import LLM, Backend, Tape

pytestmark = pytest.mark.skipif(not shutil.which("node") or not htmlmotion.GSAP_JS.exists(),
                                reason="needs node + motion_engine/node_modules")

LG = Ledger([Fact("p", "Укулеле Caesar U-246 — 22 100 ₸", "web", "https://muzzone.kz/x", "2026-10-08", ["22 100 ₸"], 30)])
NOW = __import__("datetime").datetime(2026, 10, 9, tzinfo=__import__("datetime").timezone.utc)


def html(text: str) -> str:
    return f"""<!doctype html><html><head>{htmlmotion.head_snippet()}</head><body>
<div id="band" style="position:absolute;left:0;top:560px;width:1080px;height:640px;background:#000;opacity:0.55"></div>
<div id="t" style="position:absolute;left:160px;top:700px;width:700px;font:800 84px Montserrat;color:#fff;
 -webkit-text-stroke:3px #000">{text}</div>
<script>
window.__duration = 3;
const tl = gsap.timeline({{paused:true}});
tl.fromTo('#t', {{scale:1.0}}, {{scale:1.08, duration:0.6, ease:'power2.out'}}, 0);
// a visible beat about every 0.9 s for as long as the footage runs (pacing rule P3)
for (let k = 1; k < 8; k++) tl.set('#band', {{opacity: k % 2 ? 0.15 : 0.55}}, k * 0.9);
window.__tl = tl;
</script></body></html>"""


class Scripted(Backend):
    name = "scripted"

    def __init__(self, designs, critiques):
        self.designs, self.critiques, self.prompts = list(designs), list(critiques), []

    def raw(self, call):
        self.prompts.append((call.step, call.prompt))
        if call.step.startswith("design:"):
            return {"html": self.designs.pop(0), "duration": 3, "on_screen_strings": [], "rationale": "test"}
        return self.critiques.pop(0)


@pytest.fixture(scope="module")
def footage(tmp_path_factory):
    d = tmp_path_factory.mktemp("bg")
    out = d / "bg.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=1080x1920:r=30:d=4",
                    "-f", "lavfi", "-i", "sine=f=330:d=4", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                    "-shortest", str(out)], check=True)
    return out


SHIP = {"verdict": "ship", "score": 8, "issues": [], "summary": "ok"}
REVISE = {"verdict": "revise", "score": 5, "issues": [{"what": "text too small", "when": "0s", "severity": "major",
                                                        "fix": "bigger"}], "summary": "fix"}
BRIEF = {"id": "u246", "hook": "Как звучит укулеле за 22 100 ₸", "onscreen_texts": [], "facts": ["22 100 ₸"]}


def run(tmp_path, footage, designs, critiques):
    be = Scripted(designs, critiques)
    llm = LLM(be, Tape(tmp_path / "tape.jsonl"))
    res = D.design_video(BRIEF, tmp_path / "w", LG, "playbook", llm, llm, background=footage, now=NOW,
                         max_rounds=len(designs))
    return res, be


def test_true_design_ships_in_one_round(tmp_path, footage):
    res, be = run(tmp_path, footage, [html("Как звучит укулеле за 22 100 ₸")], [SHIP])
    r = res.rounds[0]
    assert res.ok, (res.reason, r.get("auto_problems"), r.get("render_error"))
    assert res.video.exists() and len(res.rounds) == 1
    assert any("22 100" in s for s in r["on_screen"]) and (tmp_path / "w" / "round1" / "sheet.png").exists()
    crit_prompt = [p for s, p in be.prompts if s.startswith("critic:")][0]
    assert "sheet.png" in crit_prompt                      # the critic is told to LOOK at the rendered frames


def test_critic_feedback_reaches_the_next_round(tmp_path, footage):
    res, be = run(tmp_path, footage, [html("Как звучит укулеле"), html("Как звучит укулеле за 22 100 ₸")], [REVISE, SHIP])
    assert res.ok and res.best_round == 2
    second = [p for s, p in be.prompts if s.endswith(":r2")][0]
    assert "text too small" in second


def test_invented_price_never_ships_even_if_the_critic_likes_it(tmp_path, footage):
    res, be = run(tmp_path, footage, [html("Укулеле за 9 900 ₸")] * 2, [SHIP, SHIP])
    assert not res.ok and len(res.rounds) == 2
    assert any("RAIL" in p for p in res.rounds[0]["auto_problems"])
    assert "9 900" in [p for s, p in be.prompts if s.endswith(":r2")][0] or "RAIL" in [p for s, p in be.prompts if s.endswith(":r2")][0]


def test_price_never_breaks_across_lines(tmp_path):
    """A box narrower than '22 100 ₸' must overflow on one line, not wrap into '22' / '100 ₸'."""
    page = f"""<!doctype html><html><head>{htmlmotion.head_snippet()}</head><body>
<div id="p" style="position:absolute;left:200px;top:600px;width:260px;font:800 100px/120px Montserrat;color:#fff">22 100 ₸</div>
<script>window.__duration = 1; window.__tl = gsap.timeline({{paused:true}});</script></body></html>"""
    f = tmp_path / "p.html"
    f.write_text(page, encoding="utf-8")
    meta = htmlmotion.render_frames(f, tmp_path / "frames")
    box = [v["box"] for v in meta["texts"][0]["visible"] if "22" in v["text"]][0]
    assert box[3] - box[1] < 150, box                 # one line (120px), not two or three
    assert meta["texts"][0]["visible"][0]["text"] == "22 100 ₸"   # extraction still matches the ledger literal
