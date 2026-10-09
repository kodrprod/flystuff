"""AI design loop: designer writes the video's motion design, the engine renders it, a critic LOOKS at it.

    brief + facts + frames of the real footage
        -> designer (LLM via CLI, may Read the frames)      writes one HTML/GSAP design for THIS video
        -> htmlmotion.render_design                         exact text, composited over footage
        -> automated checks                                 truth rails, safe area, pacing (P1-P4)
        -> contact sheet                                    8 frames incl. the first one
        -> critic (LLM via CLI, Reads the sheet)            ship / revise, with concrete fixes
        -> up to MAX_ROUNDS, best version kept, otherwise handed to a human

Nothing here decides how a video should look: the playbook and the model do. The code only renders, measures
and refuses to pass a design whose facts, safe area or pacing fail.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import htmlmotion
from .llm import LLM, CLIBackend, Tape, LLMError
from .pacing import analyze_pacing

MAX_ROUNDS = 3
SHEET_TIMES = (0.0, 0.25, 0.6, 1.2, 0.35, 0.55, 0.75, 0.95)   # first four absolute seconds, then fractions of duration

DESIGN_SCHEMA = {
    "type": "object",
    "properties": {
        "html": {"type": "string"},
        "duration": {"type": "number", "minimum": 3, "maximum": 60},
        "on_screen_strings": {"type": "array", "items": {"type": "string"}},
        "rationale": {"type": "string"},
    },
    "required": ["html", "duration", "on_screen_strings", "rationale"],
    "additionalProperties": False,
}

CRITIC_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["ship", "revise"]},
        "score": {"type": "integer", "minimum": 1, "maximum": 10},
        "issues": {"type": "array", "items": {"type": "object", "properties": {
            "what": {"type": "string"}, "when": {"type": "string"},
            "severity": {"type": "string", "enum": ["fatal", "major", "minor"]}, "fix": {"type": "string"}},
            "required": ["what", "severity", "fix"], "additionalProperties": False}},
        "summary": {"type": "string"},
    },
    "required": ["verdict", "score", "issues", "summary"],
    "additionalProperties": False,
}

DESIGN_CONTRACT = f"""TECHNICAL CONTRACT (the renderer enforces it):
- Return ONE complete HTML document. Canvas 1080x1920. Background must be transparent when footage is underneath.
- In <head> include exactly: {htmlmotion.head_snippet()}
- Fonts available (Cyrillic+Latin, weights 100-900): Montserrat, Unbounded, Manrope. Nothing from the network.
- Build ONE paused GSAP timeline: window.__tl = gsap.timeline({{paused:true}}); set window.__duration (seconds).
  Everything must be a pure function of time (the engine seeks the timeline frame by frame). No Math.random, no Date.
- Images you may use are only the local files listed in the brief (file:// URLs).
- Platform UI covers: top 150px, bottom 350px, left 72px, right 132px. Keep all text inside that safe box.
- Every price, phone number or code must be typed EXACTLY as given in FACTS. Never invent numbers or claims.
- The first frame (t=0) is the thumbnail and the hook: it must already show readable text and the subject.
- With footage underneath, the video is exactly as long as the footage (brief.footage_duration_s): time every beat to
  the real footage you looked at; after your timeline ends its last state stays on screen."""


@dataclass
class DesignResult:
    ok: bool
    video: Path | None
    rounds: list = field(default_factory=list)
    best_round: int | None = None
    reason: str = ""


def contact_sheet(video: Path, out_png: Path, duration: float) -> Path:
    times = [t for t in SHEET_TIMES[:4] if t < duration] + [round(f * duration, 2) for f in SHEET_TIMES[4:]]
    tiles = []
    for i, t in enumerate(times):
        fp = out_png.parent / f"_sheet_{i}.png"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t}", "-i", str(video), "-frames:v", "1",
                        "-vf", "scale=270:-1", str(fp)], check=True)
        im = Image.open(fp).convert("RGB")
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 70, 26), fill=(0, 0, 0))
        d.text((6, 6), f"{t:.2f}s", fill=(255, 255, 0), font=ImageFont.load_default())
        tiles.append(im)
        fp.unlink(missing_ok=True)
    w, h = tiles[0].size
    sheet = Image.new("RGB", ((w + 6) * 4, (h + 6) * ((len(tiles) + 3) // 4)), (40, 40, 40))
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % 4) * (w + 6), (i // 4) * (h + 6)))
    sheet.save(out_png)
    return out_png


def automated_problems(info: dict, pacing: dict) -> list[str]:
    out = []
    out += [f"RAIL {v}" for v in (info.get("rail_violations") or []) if v.startswith("ERROR")]
    out += [f"LAYOUT {p}" for p in info.get("layout_problems") or []]
    out += [f"PACING {p}" for p in pacing.get("problems") or [] if p[:2] in ("P1", "P2", "P3")]
    return out


def design_video(brief: dict, workdir: Path, ledger, playbook: str, llm_designer: LLM | None = None,
                 llm_critic: LLM | None = None, background: Path | None = None, bg_start: float = 0.0,
                 audio: Path | None = None, frames_for_designer: list[Path] | None = None,
                 tape_path: Path | None = None, max_rounds: int = MAX_ROUNDS, now=None) -> DesignResult:
    """brief: {id, hook, onscreen_texts[], facts[] (exact strings allowed), cta_code, images[] (local paths),
    edit_plan, why_watch}. Returns the best render and the full round history (designs, checks, critiques)."""
    workdir.mkdir(parents=True, exist_ok=True)
    tape = Tape(tape_path or workdir / "tape.jsonl")
    footage_s = None
    if background:
        from .render import probe
        footage_s = round(float(probe(background)["duration_s"]) - bg_start, 2)
        brief = dict(brief, footage_duration_s=footage_s)     # the design must time itself to the real footage
    reads = [str(workdir)] + [str(Path(p).parent) for p in (frames_for_designer or []) + list(brief.get("images", []))]
    llm_designer = llm_designer or LLM(CLIBackend(allowed_tools="Read", add_dirs=sorted(set(reads))), tape)
    llm_critic = llm_critic or LLM(CLIBackend(allowed_tools="Read", add_dirs=sorted(set(reads))), tape)
    system_designer = ("You are the AI editor and motion designer of an autonomous marketing agent. Follow the playbook "
                       "literally; design THIS video from its context, not from a template.\n\nPLAYBOOK:\n" + playbook +
                       "\n\n" + DESIGN_CONTRACT)
    system_critic = ("You are the agent's strict design critic. You judge only what you SEE in the contact sheet and the "
                     "measured check results. Hunt for: unreadable text, text over the subject, weak first frame, ad voice, "
                     "clutter, cheap-looking motion, anything that would make a viewer scroll. Ship only if you would post it.")
    rounds = []
    feedback = ""
    for rnd in range(1, max_rounds + 1):
        rd = workdir / f"round{rnd}"
        rd.mkdir(exist_ok=True)
        prompt = ("BRIEF (JSON):\n" + json.dumps(brief, ensure_ascii=False, indent=1) +
                  ("\n\nFRAMES OF THE FOOTAGE TO LOOK AT (use the Read tool): " + ", ".join(map(str, frames_for_designer))
                   if frames_for_designer else "\n\nNo footage: the background is the design itself (you may use the listed images).") +
                  (f"\n\nPREVIOUS ROUND FEEDBACK - fix all of it:\n{feedback}" if feedback else ""))
        try:
            d = llm_designer.json(f"design:{brief['id']}:r{rnd}", system_designer, prompt, DESIGN_SCHEMA, effort="high")
        except LLMError as e:
            rounds.append({"round": rnd, "error": str(e)})
            break
        html_path = rd / "design.html"
        html_path.write_text(d["html"], encoding="utf-8")
        out = rd / "draft.mp4"
        try:
            info = htmlmotion.render_design(html_path, out, background, bg_start, audio, ledger=ledger, now=now,
                                            duration=footage_s)
        except RuntimeError as e:
            feedback = f"The design failed to render: {e}. Return a valid design."
            rounds.append({"round": rnd, "render_error": str(e)})
            continue
        pace = analyze_pacing(out)
        auto = automated_problems(info, pace)
        sheet = contact_sheet(out, rd / "sheet.png", info["duration_s"])
        crit_prompt = (f"Read the contact sheet {sheet} (frames of a 9:16 video, labelled with seconds; the first tile is the "
                       f"first frame/thumbnail).\nBRIEF: {json.dumps(brief, ensure_ascii=False)}\n"
                       f"AUTOMATED CHECKS (already measured, treat as facts): {json.dumps(auto, ensure_ascii=False) or 'none'}\n"
                       f"On-screen text extracted from the render: {json.dumps(info['on_screen_text'], ensure_ascii=False)}\n"
                       "Judge it and give concrete, visual fixes.")
        try:
            c = llm_critic.json(f"critic:{brief['id']}:r{rnd}", system_critic, crit_prompt, CRITIC_SCHEMA, effort="medium")
        except LLMError as e:
            c = {"verdict": "revise", "score": 0, "issues": [], "summary": f"critic unavailable: {e}"}
        rounds.append({"round": rnd, "video": str(out), "sheet": str(sheet), "auto_problems": auto,
                       "critic": c, "rationale": d.get("rationale"), "on_screen": info["on_screen_text"]})
        if c["verdict"] == "ship" and not auto and c["score"] >= 7:
            return DesignResult(True, out, rounds, rnd, "critic shipped, all checks passed")
        feedback = json.dumps({"automated_problems": auto, "critic": c}, ensure_ascii=False)
    scored = [r for r in rounds if "critic" in r]
    if not scored:
        return DesignResult(False, None, rounds, None, "no renderable design")
    best = max(scored, key=lambda r: (not r["auto_problems"], r["critic"]["score"]))
    return DesignResult(False, Path(best["video"]), rounds, best["round"],
                        "not shipped after max rounds: best version kept for a human decision")
