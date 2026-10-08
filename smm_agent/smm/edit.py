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

    a = audio_stats(path) if has_audio else {}
    shake = shake_px(path) if kind in ("demo", "talk", "hook", "detail", "process") else None
    problems = []
    if a.get("clipped_samples", 0) > CLIP_SAMPLES:
        problems.append(f"sound clipped ({a['clipped_samples']} samples at 0 dB): move the phone ~1 m from the amp or play softer, then reshoot")
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
            "brightness": brightness, "mean_db": mean_db, "max_db": max_db, "audio": a, "shake_px": shake,
            "problems": problems}


TARGET_LUFS = -14.0          # typical short-form platform target; linear gain only, no dynamic compression
LIMIT_LINEAR = 0.89          # ~ -1 dBTP true-peak ceiling after gain
CLIP_SAMPLES = 50            # samples at 0 dBFS above this = the phone mic clipped (unfixable -> retake)
NOISY_FLOOR_DB = -50.0       # speech noise floor above this -> light denoise
SHAKE_PX = 6.0               # median frame-to-frame motion (px at 360p) above this -> stabilise.
                             # Measured: test pattern with moving content = 3.0, synthetic handheld jitter = 30.9.
                             # Heuristic until re-tuned on real worker footage.


def audio_stats(path: str | Path, start: float = 0.0, dur: float | None = None) -> dict:
    """Integrated loudness (LUFS), clipping (samples at 0 dBFS) and noise floor of a clip range."""
    rng = ["-ss", f"{start}"] + (["-t", f"{dur}"] if dur else [])
    r = _run(["ffmpeg", "-nostats", *rng, "-i", str(path), "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"])
    lufs = re.findall(r"\bI:\s+(-?[\d.]+) LUFS", r.stderr)
    tp = re.findall(r"Peak:\s+(-?[\d.]+|-inf) dBFS", r.stderr)
    r2 = _run(["ffmpeg", "-nostats", *rng, "-i", str(path), "-af", "volumedetect,astats=measure_perchannel=none",
               "-vn", "-f", "null", "-"])
    h0 = re.search(r"histogram_0db:\s*(\d+)", r2.stderr)
    nf = re.findall(r"Noise floor dB:\s*(-?[\d.]+|-inf)", r2.stderr)
    return {"lufs": float(lufs[-1]) if lufs else None,
            "true_peak_db": float(tp[-1]) if tp and tp[-1] != "-inf" else None,
            "clipped_samples": int(h0.group(1)) if h0 else 0,
            "noise_floor_db": float(nf[-1]) if nf and nf[-1] != "-inf" else None}


def shake_px(path: str | Path, start: float = 0.0, dur: float | None = None, tmp: Path | None = None) -> float | None:
    """Median frame-to-frame camera motion in pixels at 360p, from vidstabdetect's local motions."""
    tmpdir = Path(tmp or tempfile.mkdtemp())
    trf = tmpdir / f"{Path(path).stem}_{int(start * 1000)}.trf"
    rng = ["-ss", f"{start}"] + (["-t", f"{dur}"] if dur else [])
    _run(["ffmpeg", "-nostats", *rng, "-i", str(path), "-vf",
          f"scale=-2:360,vidstabdetect=shakiness=6:accuracy=9:result={trf}", "-an", "-f", "null", "-"])
    if not trf.exists():
        return None
    mags = []
    for line in trf.read_text(errors="replace").splitlines():
        lm = re.findall(r"\(LM\s+(-?\d+)\s+(-?\d+)", line)
        if lm:
            dx = sorted(int(a) for a, _ in lm)[len(lm) // 2]
            dy = sorted(int(b) for _, b in lm)[len(lm) // 2]
            mags.append((dx * dx + dy * dy) ** 0.5)
    return sorted(mags)[len(mags) // 2] if mags else 0.0


def speech_segments(path: str | Path, noise_db: float = -35.0, min_silence: float = 0.7) -> list[tuple[float, float]]:
    """Non-silent stretches (start, end) using silencedetect."""
    r = _run(["ffmpeg", "-nostats", "-i", str(path), "-af", f"silencedetect=noise={noise_db}dB:d={min_silence}",
              "-vn", "-f", "null", "-"])
    total = float(_ffprobe_json(path)["format"]["duration"])
    starts = [float(x) for x in re.findall(r"silence_start:\s*(-?[\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*([\d.]+)", r.stderr)]
    segs, cur = [], 0.0
    for i, st in enumerate(starts):
        if st - cur > 0.15:
            segs.append((round(max(0.0, cur), 2), round(st, 2)))
        cur = ends[i] if i < len(ends) else total
    if total - cur > 0.15:
        segs.append((round(cur, 2), round(total, 2)))
    return segs


def pick_last_take(path: str | Path, need_seconds: float, min_share: float = 0.6) -> tuple[float, float] | None:
    """Workers are told: after a mistake, pause 2 seconds and repeat the whole line. So the LAST
    non-silent stretch that is long enough is the clean take. Returns (start, duration) or None."""
    segs = [s for s in speech_segments(path) if s[1] - s[0] >= min_share * need_seconds]
    if not segs:
        return None
    a, b = segs[-1]
    a = max(0.0, a - 0.15)                       # keep the breath before the first word
    return a, min(b - a + 0.2, need_seconds + 1.5)


def caption_layer(text: str, path: Path, start: int = 84) -> Path:
    """Transparent PNG: bold white text with a heavy black outline in the lower third (the native short-form
    look), inside the platform safe area. No dark slab over the footage."""
    from PIL import ImageFont
    from .render import fit_text, FONT_BOLD
    box = (SAFE["left"], H - SAFE["bottom"] - 440, W - SAFE["right"], H - SAFE["bottom"])
    font, lines = fit_text(text, box[2] - box[0], box[3] - box[1], start=start)
    lh = int(font.size * 1.25)
    y0 = box[1] + (box[3] - box[1] - lh * len(lines)) // 2
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i, ln in enumerate(lines):
        w = font.getlength(ln)
        d.text(((W - w) / 2, y0 + i * lh), ln, font=font, fill=(255, 255, 255, 255),
               stroke_width=max(4, font.size // 11), stroke_fill=(0, 0, 0, 255))
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
    zoom = float(seg.get("zoom", 1.0))
    punch = f",scale=iw*{zoom}:ih*{zoom},crop={W}:{H}" if zoom > 1.0 else ""
    grade = ",eq=contrast=1.06:saturation=1.12:gamma=0.98,unsharp=5:5:0.6:5:5:0.0" if seg.get("grade", True) else ""
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}{punch}{grade},fps={FPS},setsar=1,format=yuv420p")
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
        # One gain per SOURCE clip (computed in assemble), so jump-cut pieces of the same take never jump in level.
        # Linear gain + true-peak limiter keeps music dynamics intact (single-pass loudnorm would pump).
        gain = float(seg.get("gain_db", 0.0))
        clean = ""
        if seg.get("kind") == "talk":
            clean = "highpass=f=80,"
            if (seg.get("noise_floor_db") or -99) > NOISY_FLOOR_DB:
                clean += f"afftdn=nf={max(-80, min(-20, int(seg['noise_floor_db'])))},"
        fc += (f";[0:a]{clean}volume={gain:.2f}dB,alimiter=limit={LIMIT_LINEAR}:attack=5:release=50,"
               f"aresample=44100,aformat=channel_layouts=stereo[a]")
    else:
        cmd += ["-f", "lavfi", "-t", f"{dur}", "-i", "anullsrc=r=44100:cl=stereo"]
        fc += f";[{n_in}:a]anull[a]"
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{dur}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2", str(dst)]
    r = _run(cmd)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed on {src}: {r.stderr[-400:]}")


def expand_jumpcuts(segments: list[dict], punch: float = 1.14) -> list[dict]:
    """A segment with "jump": N is split every N seconds; every second piece is punched in (zoom).
    This is the standard way to add pace to a long static demo or talking shot. Use N <= 1.0 for the
    opening of a video: the pacing rule wants a visible change every <= 1.2 s in the first 3 s, and
    1.5 s jumps measurably fail it (see tests/test_edit.py). Pieces are
    contiguous in source time, so nothing is cut out, and captions stay on the first piece only."""
    out: list[dict] = []
    for seg in segments:
        n = float(seg.get("jump", 0) or 0)
        if n <= 0 or float(seg["dur"]) <= n * 1.3:
            out.append(seg)
            continue
        t, i = 0.0, 0
        total = float(seg["dur"])
        while t < total - 0.05:
            d = min(n, total - t)
            if total - (t + d) < 0.4:           # absorb a tiny tail instead of a 0.2 s flash
                d = total - t
            piece = {k: v for k, v in seg.items() if k != "jump"}
            piece.update(start=float(seg.get("start", 0.0)) + t, dur=d, zoom=punch if i % 2 else 1.0)
            if i > 0:
                piece.pop("text", None)
            out.append(piece)
            t += d
            i += 1
    return out


def assemble(segments: list[dict], out_path: str | Path) -> dict:
    """segments: [{"path", "start"(s, default 0), "dur"(s), "text"(optional caption)}...].
    Returns facts about the result (probed, not assumed)."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not found")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        prepared = []
        for j, seg in enumerate(segments):
            seg = dict(seg)
            if seg.get("kind") == "talk" and seg.get("auto_take", True) and seg.get("need_seconds"):
                take = pick_last_take(seg["path"], float(seg["need_seconds"]))
                if take:
                    seg["start"], seg["dur"] = take
                    seg["take"] = "last_take"
            st, du = float(seg.get("start", 0.0)), float(seg["dur"])
            a = audio_stats(seg["path"], st, du)
            if a["lufs"] is not None:
                seg["gain_db"] = max(-20.0, min(20.0, TARGET_LUFS - a["lufs"]))
                seg["noise_floor_db"] = a["noise_floor_db"]
            if seg.get("stabilize", "auto") != "off":
                sh = shake_px(seg["path"], st, du, tmp)
                if sh is not None and (sh > SHAKE_PX or seg.get("stabilize") == "on"):
                    trf = tmp / f"stab{j}.trf"
                    _run(["ffmpeg", "-nostats", "-ss", f"{st}", "-t", f"{du}", "-i", str(seg["path"]), "-vf",
                          f"vidstabdetect=shakiness=6:accuracy=9:result={trf}", "-an", "-f", "null", "-"])
                    stable = tmp / f"stab{j}.mp4"
                    r = _run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{st}", "-t", f"{du}", "-i", str(seg["path"]),
                              "-vf", f"vidstabtransform=input={trf}:smoothing=15:zoom=6:optzoom=0",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-c:a", "copy", str(stable)])
                    if trf.exists() and r.returncode == 0:
                        # pieces are cut from the stabilised take, so transform frames always line up
                        seg.update(path=str(stable), start=0.0, shake_px=sh, stabilized=True)
            prepared.append(seg)
        parts = []
        for i, seg in enumerate(expand_jumpcuts(prepared)):
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
