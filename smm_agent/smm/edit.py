"""Auto-editor for raw phone footage (+ rendered scenes) -> one 9:16 video.

What a store worker with an old iPhone and 20 minutes will send: clips of random
orientation/rotation metadata, uneven loudness, shaky starts and ends, sometimes
dark or silent. This module:

  analyze_clip   facts + quality problems (so a retake is requested only when it matters)
  assemble       trim, rotate-aware cover-crop to 1080x1920@30, loudness-normalise,
                 burn the script's caption on each segment, join (real clips and renderer
                 output can be mixed)

Captions come from the *script* (already rule-checked), not from speech recognition,
so no unchecked text can appear in a video.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from .render import FPS, H, SAFE, W, probe, text_layer

TRIM_HEAD = 0.5      # workers are told to start with 1 s of silence
MIN_BRIGHTNESS = 45  # mean luma 0-255 below this = too dark
MIN_MEAN_DB = -38.0  # mean volume below this = no usable sound
MIN_SHORT_SIDE = 720


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def _ffprobe_json(path: str | Path) -> dict:
    import json
    r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)],
                       capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def analyze_clip(path: str | Path, kind: str = "demo", need_seconds: float = 0.0) -> dict:
    j = _ffprobe_json(path)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    has_audio = any(s["codec_type"] == "audio" for s in j["streams"])
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(round(float(sd["rotation"]))) % 360
    w, h = int(v["width"]), int(v["height"])
    dw, dh = (h, w) if rot in (90, 270) else (w, h)
    duration = float(j["format"]["duration"])

    r = _run(["ffmpeg", "-nostats", "-i", str(path), "-vf", "fps=2,signalstats,metadata=mode=print:key=lavfi.signalstats.YAVG:file=-",
              "-an", "-f", "null", "-"])
    ys = [float(x) for x in re.findall(r"lavfi\.signalstats\.YAVG=([\d.]+)", r.stdout + r.stderr)]
    brightness = sum(ys) / len(ys) if ys else None

    mean_db = max_db = None
    if has_audio:
        r = _run(["ffmpeg", "-nostats", "-i", str(path), "-af", "volumedetect", "-vn", "-f", "null", "-"])
        m = re.search(r"mean_volume:\s*(-?[\d.]+) dB", r.stderr)
        x = re.search(r"max_volume:\s*(-?[\d.]+) dB", r.stderr)
        mean_db = float(m.group(1)) if m else None
        max_db = float(x.group(1)) if x else None

    problems = []
    if min(dw, dh) < MIN_SHORT_SIDE:
        problems.append(f"low resolution {dw}x{dh}")
    if brightness is not None and brightness < MIN_BRIGHTNESS:
        problems.append(f"too dark (luma {brightness:.0f}/255): film near a window or lamp")
    if need_seconds and duration < need_seconds + TRIM_HEAD:
        problems.append(f"too short: {duration:.1f}s, need about {need_seconds + TRIM_HEAD:.0f}s")
    if kind in ("demo", "talk"):
        if not has_audio:
            problems.append("no audio track")
        elif mean_db is not None and mean_db < MIN_MEAN_DB:
            problems.append(f"sound too quiet ({mean_db:.0f} dB): move the phone closer to the instrument/speaker")
    return {"width": dw, "height": dh, "rotation": rot, "duration_s": duration, "has_audio": has_audio,
            "brightness": brightness, "mean_db": mean_db, "max_db": max_db, "problems": problems}


def caption_layer(text: str, path: Path, start: int = 76) -> Path:
    """Transparent PNG: dark band + text in the lower third, inside the platform safe area."""
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(band).rectangle((0, H - SAFE["bottom"] - 460, W, H - SAFE["bottom"] + 30), fill=(0, 0, 0, 150))
    box = (SAFE["left"], H - SAFE["bottom"] - 440, W - SAFE["right"], H - SAFE["bottom"])
    layer = Image.alpha_composite(band, text_layer(text, "#ffffff", box, start, "center"))
    layer.save(path)
    return path


def _normalize_segment(seg: dict, dst: Path, tmp: Path) -> None:
    src = str(seg["path"])
    start = float(seg.get("start", 0.0))
    dur = float(seg["dur"])
    info = analyze_clip(src, kind="process")
    avail = info["duration_s"] - start
    dur = min(dur, avail)
    if dur <= 0.2:
        raise ValueError(f"segment {src} has no usable footage after trimming")
    seg["dur_used"] = dur
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1,format=yuv420p")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start}", "-t", f"{dur}", "-i", src]
    n_in = 1
    if seg.get("text"):
        layer = caption_layer(seg["text"], tmp / f"{dst.stem}_cap.png")
        cmd += ["-loop", "1", "-t", f"{dur}", "-i", str(layer)]
        n_in = 2
        fc = f"[0:v]{vf}[b];[b][1:v]overlay=0:0:format=auto,format=yuv420p[v]"
    else:
        fc = f"[0:v]{vf}[v]"
    if info["has_audio"]:
        fc += ";[0:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=44100,aformat=channel_layouts=stereo[a]"
    else:
        cmd += ["-f", "lavfi", "-t", f"{dur}", "-i", "anullsrc=r=44100:cl=stereo"]
        fc += f";[{n_in}:a]anull[a]"
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{dur}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2", str(dst)]
    r = _run(cmd)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed on {src}: {r.stderr[-400:]}")


def assemble(segments: list[dict], out_path: str | Path) -> dict:
    """segments: [{"path", "start"(s, default 0), "dur"(s), "text"(optional caption)}...].
    Returns facts about the result (probed, not assumed)."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not found")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        parts = []
        for i, seg in enumerate(segments):
            seg = dict(seg)
            dst = tmp / f"seg{i:02d}.mp4"
            _normalize_segment(seg, dst, tmp)
            parts.append(dst)
        lst = tmp / "list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
        r = _run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                  "-c", "copy", "-movflags", "+faststart", str(out_path)])
        if r.returncode != 0:
            raise RuntimeError(f"concat failed: {r.stderr[-400:]}")
    return probe(out_path)


def measure_loudness(path: str | Path) -> float | None:
    """Integrated loudness in LUFS (EBU R128) or None if no audio."""
    r = _run(["ffmpeg", "-nostats", "-i", str(path), "-af", "ebur128", "-vn", "-f", "null", "-"])
    m = re.findall(r"\bI:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(m[-1]) if m else None
