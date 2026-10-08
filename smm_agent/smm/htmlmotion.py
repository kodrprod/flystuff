"""Per-video motion design: the AI writes the design, the browser renders it exactly.

Why this exists (owner feedback: "it looks like 2015 motion graphics" and "templates break"):
there is NO style library here. For every video an AI designer writes one HTML document (CSS + GSAP)
from the video's context, footage frames and current references. This module only renders that document
frame-exactly with headless Chromium and composites it over the footage.

Two properties the business needs, and how they are guaranteed:
  * modern look: real typography (variable-weight Cyrillic web fonts), CSS effects and GSAP easing -
    the same toolset human motion designers use on the web, chosen per video by the AI;
  * exact facts: text is drawn by the browser's font engine from the document, so the strings in the DOM
    ARE the strings on screen. `verify_text` checks every visible string against the facts ledger
    (prices, phone, WhatsApp codes) - no OCR guesswork, no garbled Cyrillic.

Design contract for the AI designer (also in playbooks/editor.md):
  - a full HTML page 1080x1920, transparent background when composited over footage
  - link the shared fonts: <link rel="stylesheet" href="file://.../motion_engine/fonts.css">
    (families: Montserrat, Unbounded, Manrope; weights 100-900; Cyrillic + Latin)
  - load GSAP from the local file and build ONE paused timeline: window.__tl = gsap.timeline({paused:true})
  - set window.__duration (seconds)
  - no network, no randomness without a fixed seed, no real-time clocks
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ENGINE = Path(__file__).parent / "motion_engine"
FONTS_CSS = ENGINE / "fonts.css"
GSAP_JS = ENGINE / "node_modules" / "gsap" / "dist" / "gsap.min.js"
W, H, FPS = 1080, 1920, 30


def head_snippet() -> str:
    """What a design must include in <head>; given to the AI designer verbatim."""
    return (f'<meta charset="utf-8"><link rel="stylesheet" href="file://{FONTS_CSS}">'
            f'<script src="file://{GSAP_JS}"></script>'
            '<style>html,body{margin:0;width:1080px;height:1920px;overflow:hidden;background:transparent}</style>')


def render_frames(design_html: str | Path, out_dir: str | Path, fps: int = FPS, duration: float | None = None,
                  timeout_s: int = 900) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["node", str(ENGINE / "render_html.mjs"), str(design_html), str(out_dir), str(fps)]
    if duration:
        cmd.append(str(duration))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, cwd=str(ENGINE))
    if r.returncode != 0:
        raise RuntimeError(f"design render failed: {(r.stderr or r.stdout)[-600:]}")
    meta = json.loads((out_dir / "text.json").read_text(encoding="utf-8"))
    if meta.get("errors"):
        raise RuntimeError(f"design has JavaScript errors: {meta['errors'][:3]}")
    return meta


def _has_audio(path: str | Path) -> bool:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return bool(r.stdout.strip())


def composite(frames_dir: str | Path, out_mp4: str | Path, background: str | Path | None = None,
              bg_start: float = 0.0, audio: str | Path | None = None, fps: int = FPS,
              duration: float | None = None, crf: int = 18) -> None:
    """Overlay the transparent design frames on footage (cover-cropped to 9:16) or on black.
    Audio: explicit `audio` file > the footage's own sound > a silent track (platforms need one)."""
    frames = str(Path(frames_dir) / "frame_%05d.png")
    inputs: list[str] = []
    if background:
        inputs += ["-ss", f"{bg_start}", "-i", str(background)]
    else:
        inputs += ["-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r={fps}"]
    inputs += ["-framerate", str(fps), "-i", frames]
    if audio:
        inputs += ["-i", str(audio)]
        amap = "2:a"
    elif background and _has_audio(background):
        amap = "0:a"
    else:
        inputs += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
        amap = "2:a"
    fc = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={fps},setsar=1[bg];"
          f"[bg][1:v]overlay=0:0:eof_action=pass:format=auto,format=yuv420p[v]")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", fc, "-map", "[v]", "-map", amap,
           "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"]
    if duration:
        cmd += ["-t", f"{duration}"]
    cmd.append(str(out_mp4))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"composite failed: {r.stderr[-600:]}")


def visible_strings(meta: dict) -> list[str]:
    seen, out = set(), []
    for fr in meta.get("texts", []):
        for v in fr["visible"]:
            if v["text"] not in seen:
                seen.add(v["text"])
                out.append(v["text"])
    return out


def verify_text(meta: dict, ledger, now=None) -> list:
    """Every string that appears on screen goes through the truth rails (numbers, claims, contacts)."""
    from .checks import check_text
    out = []
    for s in visible_strings(meta):
        out += check_text(s, ledger, where=f"screen:{s[:30]}", now=now)
    return out


def layout_problems(meta: dict, safe=(72, 150, 132, 350)) -> list[str]:
    """Text boxes that leave the platform-safe area (UI covers the edges) at any sampled second."""
    left, top, right, bottom = safe
    probs = []
    for fr in meta.get("texts", []):
        for v in fr["visible"]:
            x0, y0, x1, y1 = v["box"]
            if v["opacity"] < 0.5:
                continue
            if x0 < left - 8 or y0 < top - 8 or x1 > W - right + 8 or y1 > H - bottom + 8:
                probs.append(f"t={fr['t']}s text {v['text'][:24]!r} at {v['box']} leaves the safe area")
    return sorted(set(probs))


def render_design(design_html: str | Path, out_mp4: str | Path, background=None, bg_start: float = 0.0,
                  audio=None, ledger=None, now=None, keep_frames: bool = False) -> dict:
    """Render + composite + verify. Returns facts about the result; raises nothing for rule violations
    (they are returned so the editor can revise the design)."""
    from .render import probe
    tmp = Path(tempfile.mkdtemp(prefix="design_"))
    try:
        meta = render_frames(design_html, tmp / "frames")
        composite(tmp / "frames", out_mp4, background, bg_start, audio, duration=meta["duration"])
        info = probe(out_mp4)
        info["on_screen_text"] = visible_strings(meta)
        info["layout_problems"] = layout_problems(meta)
        info["rail_violations"] = [str(v) for v in verify_text(meta, ledger, now)] if ledger is not None else None
        return info
    finally:
        if not keep_frames:
            shutil.rmtree(tmp, ignore_errors=True)
