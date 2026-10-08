"""Zero-credit renderer: script dict -> vertical mp4 (1080x1920, 30 fps, silent AAC track).

Purpose (decision D7): production cheap enough to test many variants, using
the client's *real* product photos plus text, so R5 (no AI stand-ins for the
real product) holds by construction. Audio is intentionally silent: music is
added at publish time (trending audio can't be licensed/checked from here),
and the render reports that as `audio: "needs_publisher"`.

Beat shape::

    {"t0": 0.0, "t1": 2.5, "kind": "photo"|"text"|"card",
     "text": "on-screen text", "image": "<path or url>",      # photo/card
     "price": "71 433 ₸", "old_price": "119 054 ₸",            # card only
     "bg": "#101418", "fg": "#ffffff"}

TikTok/Reels UI covers the bottom ~18% and right ~13%, and the top ~8%; text is
kept inside that safe box.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .textutil import NBSP as _NBSP, protect

W, H = 1080, 1920
FPS = 30
SAFE = {"left": 72, "right": 72 + 60, "top": 150, "bottom": 350}   # px from each edge
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
UA = {"User-Agent": "MetaPromptSMM-render/0.1"}


# ----------------------------------------------------------------- helpers
def load_image(src: str, cache: Path) -> Image.Image:
    p = Path(src)
    if not p.exists():
        cache.mkdir(parents=True, exist_ok=True)
        p = cache / (hashlib.sha1(src.encode()).hexdigest() + Path(src.split("?")[0]).suffix)
        if not p.exists():
            req = urllib.request.Request(src, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                p.write_bytes(r.read())
    return ImageOps.exif_transpose(Image.open(p)).convert("RGB")


def wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    lines: list[str] = []
    for para in protect(text).split("\n"):
        cur = ""
        for word in para.split(" "):
            if not word:
                continue
            trial = f"{cur} {word}".strip()
            if font.getlength(trial) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return [ln.replace(_NBSP, " ") for ln in lines]


def fit_text(text: str, max_w: int, max_h: int, start: int = 112, min_size: int = 48,
             bold: bool = True) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """Largest font (<= start) whose wrapped block fits max_w x max_h; no word is ever split."""
    size = start
    while size >= min_size:
        font = ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)
        lines = wrap(text, font, max_w)
        longest_word = max((font.getlength(w) for w in protect(text).split(" ")), default=0)
        height = int(len(lines) * size * 1.22)
        if height <= max_h and longest_word <= max_w:
            return font, lines
        size -= 4
    raise ValueError(f"text does not fit the safe area even at {min_size}px: {text[:40]!r}")


def cover(img: Image.Image, size: tuple[int, int], zoom: float = 1.0, pan: float = 0.5) -> Image.Image:
    """Cover-fit with an optional slow zoom (Ken Burns)."""
    tw, th = size
    scale = max(tw / img.width, th / img.height) * zoom
    nw, nh = int(img.width * scale) + 1, int(img.height * scale) + 1
    im = img.resize((nw, nh), Image.LANCZOS)
    x = int((nw - tw) * pan)
    y = int((nh - th) * 0.5)
    return im.crop((x, y, x + tw, y + th))


def photo_frame(img: Image.Image, zoom: float = 1.0) -> Image.Image:
    """Whole product visible (never cropped), over a blurred, dimmed copy of itself that fills 9:16."""
    from PIL import ImageEnhance, ImageFilter
    bg = cover(img, (W // 4, H // 4)).filter(ImageFilter.GaussianBlur(10)).resize((W, H), Image.BILINEAR)
    bg = ImageEnhance.Brightness(bg).enhance(0.45)
    fg_w = int(W * min(1.0, 0.92 * zoom))
    fg = ImageOps.contain(img, (fg_w, int(H * 0.6)))
    bg.paste(fg, ((W - fg.width) // 2, int(H * 0.30) - fg.height // 2 + int(H * 0.04)))
    return bg


def _hex(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def text_layer(text: str, fg: str, box: tuple[int, int, int, int], start: int, anchor: str) -> Image.Image:
    """RGBA layer with the text block placed inside `box` (l,t,r,b); anchor: top|center|bottom."""
    l, t, r, b = box
    font, lines = fit_text(text, r - l, b - t, start=start)
    lh = int(font.size * 1.22)
    block_h = lh * len(lines)
    y0 = {"top": t, "center": t + (b - t - block_h) // 2, "bottom": b - block_h}[anchor]
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i, ln in enumerate(lines):
        w = font.getlength(ln)
        x = l + (r - l - w) / 2
        y = y0 + i * lh
        d.text((x + 3, y + 3), ln, font=font, fill=(0, 0, 0, 200))    # soft shadow for legibility
        d.text((x, y), ln, font=font, fill=_hex(fg) + (255,))
    return layer


def scrim(strength: int = 150) -> Image.Image:
    """Dark gradient bottom and top so text stays readable over any photo."""
    g = Image.new("L", (1, H))
    for y in range(H):
        a = max(0.0, (y - H * 0.45) / (H * 0.55))
        top = max(0.0, (H * 0.18 - y) / (H * 0.18)) * 0.6
        g.putpixel((0, y), int(strength * max(a, top)))
    alpha = g.resize((W, H))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.putalpha(alpha)
    return layer


def beat_frame(beat: dict, t_local: float, dur: float, cache: Path, _imgs: dict) -> Image.Image:
    kind = beat.get("kind", "text")
    bg = beat.get("bg", "#101418")
    fg = beat.get("fg", "#ffffff")
    k = t_local / max(dur, 1e-6)
    if kind == "split" and beat.get("image") and beat.get("image2"):
        frame = Image.new("RGB", (W, H), _hex(bg))
        for j, key in enumerate(("image", "image2")):
            src = beat[key]
            if src not in _imgs:
                _imgs[src] = load_image(src, cache)
            half = ImageOps.contain(_imgs[src], (W, H // 2 - 20))
            frame.paste(half, ((W - half.width) // 2, j * (H // 2) + (H // 2 - half.height) // 2))
        rgba = frame.convert("RGBA")
        band = Image.new("RGBA", (W, 330), (10, 14, 18, 215))
        rgba.alpha_composite(band, (0, H // 2 - 165))
        d = ImageDraw.Draw(rgba)
        f_p = ImageFont.truetype(FONT_BOLD, 64)
        for j, key in enumerate(("price", "price2")):
            if beat.get(key):
                pw = f_p.getlength(beat[key])
                y = SAFE["top"] if j == 0 else H - SAFE["bottom"] - 90
                d.rounded_rectangle((SAFE["left"], y - 12, SAFE["left"] + pw + 40, y + 84), 18, fill=(10, 14, 18, 230))
                d.text((SAFE["left"] + 20, y), beat[key], font=f_p, fill=(255, 214, 90, 255))
        text = beat.get("text") or beat.get("onscreen", "")
        if text:
            layer = text_layer(text, fg, (SAFE["left"], H // 2 - 150, W - SAFE["right"], H // 2 + 150), 84, "center")
            layer.putalpha(layer.getchannel("A").point(lambda a: int(a * min(1.0, t_local / 0.25))))
            rgba = Image.alpha_composite(rgba, layer)
        return rgba.convert("RGB")
    if kind in ("photo", "card") and beat.get("image"):
        src = beat["image"]
        if src not in _imgs:
            _imgs[src] = load_image(src, cache)
        if kind == "photo":
            frame = photo_frame(_imgs[src], 1.0 + 0.06 * k)
            frame = Image.alpha_composite(frame.convert("RGBA"), scrim()).convert("RGB")
        else:   # card: photo on a plain background, price block below
            frame = Image.new("RGB", (W, H), _hex(bg))
            ph = ImageOps.contain(_imgs[src], (W - 2 * SAFE["left"], 900))
            frame.paste(ph, ((W - ph.width) // 2, SAFE["top"] + 40))
    else:
        frame = Image.new("RGB", (W, H), _hex(bg))

    rgba = frame.convert("RGBA")
    fade = min(1.0, t_local / 0.25)                       # text pops in over 0.25 s
    text = beat.get("text") or beat.get("onscreen", "")
    if text:
        if kind == "photo":
            box = (SAFE["left"], H - SAFE["bottom"] - 640, W - SAFE["right"], H - SAFE["bottom"])
            layer = text_layer(text, fg, box, 100, "bottom")
        elif kind == "card":
            box = (SAFE["left"], SAFE["top"] + 980, W - SAFE["right"], SAFE["top"] + 1180)
            layer = text_layer(text, fg, box, 72, "top")
        else:
            box = (SAFE["left"], SAFE["top"], W - SAFE["right"], H - SAFE["bottom"])
            layer = text_layer(text, fg, box, 120, "center")
        layer.putalpha(layer.getchannel("A").point(lambda a: int(a * fade)))
        rgba = Image.alpha_composite(rgba, layer)
    if kind == "card" and beat.get("price"):
        y = SAFE["top"] + 1190
        if beat.get("old_price"):
            f_old = ImageFont.truetype(FONT_REG, 56)
            old = beat["old_price"]
            d = ImageDraw.Draw(rgba)
            ow = f_old.getlength(old)
            x = (W - ow) / 2
            d.text((x, y), old, font=f_old, fill=(170, 170, 170, 255))
            d.line((x, y + 34, x + ow, y + 34), fill=(220, 80, 80, 255), width=5)
            y += 80
        f_price = ImageFont.truetype(FONT_BOLD, 120)
        d = ImageDraw.Draw(rgba)
        pw = f_price.getlength(beat["price"])
        d.text(((W - pw) / 2, y), beat["price"], font=f_price, fill=(255, 214, 90, 255))
    return rgba.convert("RGB")


# ------------------------------------------------------------------ render
def validate_timeline(beats: list[dict]) -> float:
    if not beats:
        raise ValueError("no beats")
    prev = 0.0
    for i, b in enumerate(beats):
        if abs(b["t0"] - prev) > 1e-6:
            raise ValueError(f"beat {i} starts at {b['t0']}, expected {prev} (no gaps/overlaps)")
        if b["t1"] <= b["t0"]:
            raise ValueError(f"beat {i} has non-positive length")
        prev = b["t1"]
    return prev


def render_video(script: dict, out_path: str | Path, cache_dir: str | Path = ".render_cache") -> dict:
    """Render `script['beats']` to out_path. Returns facts about the file (from ffprobe, not assumed)."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not found")
    beats = script["beats"]
    total = validate_timeline(beats)
    n_frames = round(total * FPS)
    cache = Path(cache_dir)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "96k", "-shortest", "-movflags", "+faststart", str(out_path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    imgs: dict = {}
    try:
        for f in range(n_frames):
            t = f / FPS
            beat = next(b for b in beats if b["t0"] <= t < b["t1"] or b is beats[-1])
            frame = beat_frame(beat, t - beat["t0"], beat["t1"] - beat["t0"], cache, imgs)
            proc.stdin.write(frame.tobytes())
        proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError("ffmpeg failed")
    except BrokenPipeError:
        raise RuntimeError("ffmpeg closed the pipe early")
    return probe(out_path) | {"audio": "needs_publisher"}


def probe(path: str | Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)],
                       capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    a = [s for s in j["streams"] if s["codec_type"] == "audio"]
    num, den = v["r_frame_rate"].split("/")
    return {"width": v["width"], "height": v["height"], "codec": v["codec_name"],
            "fps": float(num) / float(den), "duration_s": float(j["format"]["duration"]),
            "has_audio_stream": bool(a), "size_bytes": int(j["format"]["size"])}


def tiktok_media_problems(info: dict) -> list[str]:
    """Limits from the TikTok publish tool: MP4/WebM/MOV, <=1 GB, 3-600 s, >=360 px, 23-60 fps."""
    p = []
    if not 3 <= info["duration_s"] <= 600:
        p.append(f"duration {info['duration_s']:.1f}s outside 3-600 s")
    if min(info["width"], info["height"]) < 360:
        p.append("under 360 px")
    if not 23 <= info["fps"] <= 60:
        p.append(f"fps {info['fps']} outside 23-60")
    if info["size_bytes"] > 1_000_000_000:
        p.append("over 1 GB")
    return p
