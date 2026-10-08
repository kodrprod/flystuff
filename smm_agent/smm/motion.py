"""Motion scenes: things move on frame 0 and something changes every ~1 s.

Replaces static "photo + caption" slides. Scene kinds (beat["kind"]):

  hook       product photo punches in (1.22x -> 1.0x in 0.35 s), words pop in from frame 0
  cuts       hard cuts through detail crops of the *real* photo (picked by edge energy), one caption per cut
  pricedrop  old price struck through, number counts down to the new price, badge pops, "ding"
  kinetic    words pop one by one on a fast-changing colour field (text-only scenes)
  versus     two product photos slide in from opposite sides, price tags pop
  stat       two big numbers pop from opposite sides under a label ("Полифония": 128 | 192)

Every visible string lives in beat fields that `checks.check_script` validates. No scene invents text.
Pure PIL; each function returns an RGB frame for time t (seconds from scene start).
"""
from __future__ import annotations

import re

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

from .render import FONT_BOLD, FONT_REG, H, SAFE, W, _hex, cover, fit_text, load_image
from .textutil import protect, NBSP

YELLOW = (255, 214, 90)
WHITE = (255, 255, 255)
PALETTE = ["#14202b", "#1b2a1f", "#2a1f14", "#241a2e", "#0f2a2e", "#2e1a1a"]


# ------------------------------------------------------------------ easing
def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def ease_out(x: float) -> float:
    x = clamp(x)
    return 1 - (1 - x) ** 3


# ------------------------------------------------------------------ words
_HILITE = re.compile(r"\d|₸|%")


def layout_words(text: str, box: tuple[int, int, int, int], start: int, anchor: str = "center"):
    """-> (font, [(token, x, y)], line_height). Grouped prices/phones stay one token."""
    l, t, r, b = box
    font, lines = fit_text(text, r - l, b - t, start=start)
    lh = int(font.size * 1.22)
    block = lh * len(lines)
    y0 = {"top": t, "center": t + (b - t - block) // 2, "bottom": b - block}[anchor]
    out = []
    for i, ln in enumerate(lines):
        toks = protect(ln).split(" ")
        widths = [font.getlength(tk.replace(NBSP, " ")) for tk in toks]
        space = font.getlength(" ")
        total = sum(widths) + space * (len(toks) - 1)
        x = l + (r - l - total) / 2
        for tk, w in zip(toks, widths):
            out.append((tk.replace(NBSP, " "), x, y0 + i * lh))
            x += w + space
    return font, out, lh


def draw_words(frame: Image.Image, text: str, t: float, box, start: int, anchor="center",
               step: float = 0.12, pop: float = 0.18, from_scale: float = 1.22, t0: float = 0.0) -> Image.Image:
    """Words pop in sequentially (first word at t0, visible on frame 0 when t0 == 0)."""
    font, words, lh = layout_words(text, box, start, anchor)
    rgba = frame.convert("RGBA")
    for i, (tok, x, y) in enumerate(words):
        a = t - (t0 + i * step)
        if a < 0:
            continue
        p = ease_out(a / pop)
        scale = from_scale + (1 - from_scale) * p
        color = YELLOW if _HILITE.search(tok) else WHITE
        w, h = int(font.getlength(tok)) + 24, lh + 24
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.text((14, 14), tok, font=font, fill=(0, 0, 0, 210))          # shadow
        d.text((12, 12), tok, font=font, fill=color + (255,))
        if abs(scale - 1) > 1e-3:
            layer = layer.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.BILINEAR)
        layer.putalpha(layer.getchannel("A").point(lambda v, p=p: int(v * min(1.0, 0.35 + p))))
        cx, cy = x - 12 + w / 2, y - 12 + h / 2
        rgba.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))
    return rgba.convert("RGB")


# ------------------------------------------------------------------ backgrounds
def _pixels(im: Image.Image):
    return im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata()


def dominant_color(img: Image.Image) -> tuple[int, int, int]:
    """Average colour of the product itself (opaque, non-white pixels)."""
    small = img.convert("RGBA").resize((48, 48))
    px = [p for p in _pixels(small) if p[3] > 200 and not (p[0] > 235 and p[1] > 235 and p[2] > 235)]
    if not px:
        return (90, 90, 100)
    n = len(px)
    return tuple(sum(p[i] for p in px) // n for i in range(3))


def gradient_bg(color: tuple[int, int, int]) -> Image.Image:
    """Clean studio backdrop: product-tinted, dark, lighter at the top, vignetted. No photo ghosts."""
    import colorsys
    h, l, sat = colorsys.rgb_to_hls(*(c / 255 for c in color))
    sat = min(0.55, max(0.18, sat * 1.1))

    def col(light):
        r, g, b = colorsys.hls_to_rgb(h, light, sat)
        return (int(r * 255), int(g * 255), int(b * 255))

    top, bot = col(0.34), col(0.10)
    col_img = Image.new("RGB", (1, H))
    for y in range(H):
        k = y / (H - 1)
        col_img.putpixel((0, y), tuple(int(top[i] + (bot[i] - top[i]) * k) for i in range(3)))
    bg = col_img.resize((W, H))
    vig = Image.new("L", (W // 8, H // 8), 0)
    ImageDraw.Draw(vig).ellipse((-W // 16, -H // 16, W // 8 + W // 16, H // 8 + H // 16), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(14)).resize((W, H), Image.BILINEAR)
    return Image.composite(bg, Image.new("RGB", (W, H), (0, 0, 0)), vig.point(lambda v: 120 + v * 135 // 255))


def blur_bg(img: Image.Image, dim: float = 0.45) -> Image.Image:        # kept for compatibility
    return gradient_bg(dominant_color(img))


def color_field(idx: int, t: float) -> Image.Image:
    """Solid scene colour with a soft moving highlight so even text-only scenes are never frozen."""
    base = Image.new("RGB", (W, H), _hex(PALETTE[idx % len(PALETTE)]))
    glow = Image.new("L", (W // 6, H // 6), 0)
    cx = int((0.5 + 0.35 * __import__("math").sin(t * 2.2 + idx)) * glow.width)
    ImageDraw.Draw(glow).ellipse((cx - 70, 40, cx + 70, glow.height - 40), fill=70)
    glow = glow.filter(ImageFilter.GaussianBlur(25)).resize((W, H), Image.BILINEAR)
    return Image.composite(Image.new("RGB", (W, H), (255, 255, 255)), base, glow)


def cutout(img: Image.Image) -> Image.Image:
    """Remove a white studio background (only white connected to the border), crop tight to the
    product, keep a soft edge. Falls back to the plain photo if there is no clean white background."""
    rgb = img.convert("RGB")
    g = rgb.convert("L")
    mask = g.point(lambda v: 255 if v > 238 else 0)
    w, h = mask.size
    px = mask.load()
    seeds = [(x, y) for x in range(0, w, max(1, w // 8)) for y in (0, h - 1)] + \
            [(x, y) for y in range(0, h, max(1, h // 8)) for x in (0, w - 1)]
    for sx, sy in seeds:
        if px[sx, sy] == 255:
            ImageDraw.floodfill(mask, (sx, sy), 128)
    bg = mask.point(lambda v: 255 if v == 128 else 0)
    if sum(_pixels(bg.resize((50, 50)))) / (255 * 2500) < 0.25:       # not a clean white backdrop
        return rgb.convert("RGBA")
    alpha = ImageOps.invert(bg).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.3))
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    box = alpha.point(lambda v: 255 if v > 40 else 0).getbbox()
    if box:
        pad = int(0.02 * max(w, h))
        out = out.crop((max(0, box[0] - pad), max(0, box[1] - pad), min(w, box[2] + pad), min(h, box[3] + pad)))
    return out


def paste_center(bg: Image.Image, fg: Image.Image, cx: int, cy: int, shadow: bool = True) -> None:
    x, y = cx - fg.width // 2, cy - fg.height // 2
    if fg.mode == "RGBA" and shadow:
        sh = Image.new("L", (fg.width, 90), 0)
        ImageDraw.Draw(sh).ellipse((fg.width * 0.08, 20, fg.width * 0.92, 70), fill=150)
        sh = sh.filter(ImageFilter.GaussianBlur(14))
        bg.paste((0, 0, 0), (x, y + fg.height - 45), sh)
    bg.paste(fg, (x, y), fg if fg.mode == "RGBA" else None)


def product_fg(img: Image.Image, width: int, max_h: int, zoom: float) -> Image.Image:
    return ImageOps.contain(img, (int(width * zoom), int(max_h * zoom)))


# ------------------------------------------------------------------ detail crops
def detail_boxes(img: Image.Image, n: int = 3, frac: float = 0.5, min_rel: float = 0.7) -> list[tuple[int, int, int, int]]:
    """Top-n non-overlapping windows with feature-rich detail (knobs, logos, strings, keys).
    Score = edge energy x (1 + variation across the window's quadrants): uniform texture such as a
    speaker grille has high edge energy but no variation, so it loses to windows with distinct parts."""
    base = img.convert("RGB")
    small = base.convert("L").resize((160, max(1, int(160 * img.height / img.width))))
    edges = small.filter(ImageFilter.FIND_EDGES)
    sw, sh = small.size
    ww, wh = int(sw * frac), int(sh * frac)
    px = edges.load()
    alpha = img.getchannel("A").resize((sw, sh)).load() if img.mode == "RGBA" else None
    scored = []
    step = max(1, sw // 16)
    for y in range(0, sh - wh + 1, step):
        for x in range(0, sw - ww + 1, step):
            quads = []
            for qy in (0, 1):
                for qx in (0, 1):
                    q = 0
                    for yy in range(y + qy * wh // 2, y + (qy + 1) * wh // 2, 3):
                        for xx in range(x + qx * ww // 2, x + (qx + 1) * ww // 2, 3):
                            if alpha is None or alpha[xx, yy] > 100:       # ignore transparent backdrop
                                q += px[xx, yy]
                    quads.append(q)
            tot = sum(quads)
            mean = tot / 4 or 1
            cv = (sum((q - mean) ** 2 for q in quads) / 4) ** 0.5 / mean
            scored.append((tot * (1 + cv), x, y))
    scored.sort(reverse=True)
    chosen: list[tuple[float, int, int]] = []
    for s_, x, y in scored:
        if all(abs(x - cx) > ww * 0.45 or abs(y - cy) > wh * 0.45 for _, cx, cy in chosen):
            chosen.append((s_, x, y))
        if len(chosen) == n:
            break
    k = img.width / sw
    top = chosen[0][0] if chosen else 0
    return [(int(x * k), int(y * k), int((x + ww) * k), int((y + wh) * k)) for sc, x, y in chosen if sc >= min_rel * top]


# ------------------------------------------------------------------ scenes
def scene_hook(beat: dict, t: float, dur: float, ctx: dict) -> Image.Image:
    img = ctx["img"](beat["image"])
    key = ("bg", beat["image"])
    bg = ctx["cache"].setdefault(key, blur_bg(img))
    frame = bg.copy()
    zoom = 1.0 + 0.22 * (1 - ease_out(t / 0.35)) + 0.05 * (t / max(dur, 0.1))
    fg = product_fg(ctx["cut"](beat["image"]), int(W * 0.98), int(H * 0.50), zoom)
    paste_center(frame, fg, W // 2, int(H * 0.33))
    box = (SAFE["left"], int(H * 0.61), W - SAFE["right"], H - SAFE["bottom"])
    return draw_words(frame, beat["onscreen"], t, box, 120, "top", step=0.11)


def scene_cuts(beat: dict, t: float, dur: float, ctx: dict) -> Image.Image:
    img = ctx["img"](beat["image"])
    cut = ctx["cut"](beat["image"])
    texts = beat.get("texts") or [beat.get("onscreen", "")]
    boxes = ctx["cache"].setdefault(("boxes", beat["image"], len(texts)), detail_boxes(cut, n=max(1, len(texts) - 1)))
    shots = [None] + boxes[: len(texts) - 1]                      # first shot = whole product
    texts = texts[: len(shots)]
    n = len(shots)
    i = min(n - 1, int(t / (dur / n)))
    tl = t - i * (dur / n)
    src = cut if shots[i] is None else cut.crop(shots[i])
    bg = ctx["cache"].setdefault(("cbg", beat["image"], i), gradient_bg(dominant_color(src)))
    frame = bg.copy()
    zoom = 1.0 + 0.16 * (1 - ease_out(tl / 0.3)) + 0.04 * tl
    fg = product_fg(src, int(W * 0.98), int(H * 0.50), zoom)
    paste_center(frame, fg, W // 2, int(H * 0.33))
    box = (SAFE["left"], int(H * 0.61), W - SAFE["right"], H - SAFE["bottom"])
    return draw_words(frame, texts[i], tl, box, 120, "top", step=0.10)


def _fmt_int(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def _to_int(s: str) -> int:
    return int(re.sub(r"\D", "", s))


def scene_pricedrop(beat: dict, t: float, dur: float, ctx: dict) -> Image.Image:
    old_s, new_s = beat["old_price"], beat["price"]
    old, new = _to_int(old_s), _to_int(new_s)
    img = ctx["img"](beat["image"])
    frame = ctx["cache"].setdefault(("bg", beat["image"]), blur_bg(img, 0.35)).copy()
    fg = product_fg(ctx["cut"](beat["image"]), int(W * 0.82), int(H * 0.30), 1.0 + 0.04 * (t / max(dur, 0.1)))
    paste_center(frame, fg, W // 2, int(H * 0.22))
    d = ImageDraw.Draw(frame)
    f_old = ImageFont.truetype(FONT_BOLD, 96)
    f_new = ImageFont.truetype(FONT_BOLD, 168)
    cx = W // 2
    ow = f_old.getlength(old_s)
    y_old = int(H * 0.42)
    d.text((cx - ow / 2 + 3, y_old + 3), old_s, font=f_old, fill=(0, 0, 0))
    d.text((cx - ow / 2, y_old), old_s, font=f_old, fill=(200, 200, 200))
    if t > 0.3:
        k = ease_out((t - 0.3) / 0.25)
        d.line((cx - ow / 2 - 10, y_old + 58, cx - ow / 2 - 10 + (ow + 20) * k, y_old + 58), fill=(235, 70, 70), width=10)
    if t > 0.65:
        k = ease_out((t - 0.65) / 0.85)
        s_ = f"{_fmt_int(int(old + (new - old) * k))} ₸"
        scale = 1.0 + (0.28 * (1 - ease_out((t - 1.5) / 0.25)) if t >= 1.5 else 0.0)
        layer = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        sw = f_new.getlength(s_)
        ld.text(((W - sw) / 2 + 4, 24), s_, font=f_new, fill=(0, 0, 0, 220))
        ld.text(((W - sw) / 2, 20), s_, font=f_new, fill=YELLOW + (255,))
        if scale != 1.0:
            layer = layer.resize((int(layer.width * scale), int(layer.height * scale)), Image.BILINEAR)
        rgba = frame.convert("RGBA")
        rgba.alpha_composite(layer, (int((W - layer.width) / 2), int(H * 0.49) - int((layer.height - 260) / 2)))
        frame = rgba.convert("RGB")
    if t > 1.5 and beat.get("badge"):
        pr = ease_out((t - 1.5) / 0.22)
        bw, bh = int(360 * (0.6 + 0.4 * pr)), int(120 * (0.6 + 0.4 * pr))
        badge = Image.new("RGBA", (360, 120), (0, 0, 0, 0))
        bd = ImageDraw.Draw(badge)
        bd.rounded_rectangle((0, 0, 359, 119), 30, fill=(220, 50, 50, 255))
        f_b = ImageFont.truetype(FONT_BOLD, 78)
        bd.text(((360 - f_b.getlength(beat["badge"])) / 2, 16), beat["badge"], font=f_b, fill=(255, 255, 255, 255))
        badge = badge.resize((bw, bh), Image.BILINEAR)
        rgba = frame.convert("RGBA")
        rgba.alpha_composite(badge, (W // 2 - bw // 2, int(H * 0.625) + (120 - bh) // 2))
        frame = rgba.convert("RGB")
    name = beat.get("onscreen")
    if name:
        frame = draw_words(frame, name, t, (SAFE["left"], int(H * 0.74), W - SAFE["right"], H - SAFE["bottom"]), 72, "top", step=0.08)
    return frame


def scene_kinetic(beat: dict, t: float, dur: float, ctx: dict) -> Image.Image:
    idx = int(beat.get("palette", 0))
    if beat.get("image"):
        img = ctx["img"](beat["image"])
        frame = ctx["cache"].setdefault(("bg", beat["image"]), blur_bg(img)).copy()
    else:
        frame = color_field(idx, t)
    box = (SAFE["left"], SAFE["top"] + 120, W - SAFE["right"], H - SAFE["bottom"] - 80)
    return draw_words(frame, beat["onscreen"], t, box, 120, "center", step=beat.get("step", 0.13))


def slide(frame: Image.Image, layer: Image.Image, target: tuple[int, int], p: float, from_dx: int) -> None:
    x = int(target[0] + from_dx * (1 - ease_out(p)))
    frame.paste(layer, (x, target[1]))


def scene_versus(beat: dict, t: float, dur: float, ctx: dict) -> Image.Image:
    a, b = ctx["img"](beat["image"]), ctx["img"](beat["image2"])
    frame = Image.new("RGB", (W, H), _hex("#0f1418"))
    ha = ImageOps.contain(a, (W, H // 2 - 30))
    hb = ImageOps.contain(b, (W, H // 2 - 30))
    slide(frame, ha, ((W - ha.width) // 2, (H // 2 - ha.height) // 2), t / 0.28, -W // 3)
    slide(frame, hb, ((W - hb.width) // 2, H // 2 + (H // 2 - hb.height) // 2), (t - 0.1) / 0.28, W // 3)
    rgba = frame.convert("RGBA")
    d = ImageDraw.Draw(rgba)
    f_p = ImageFont.truetype(FONT_BOLD, 66)
    for j, (key, t_in) in enumerate((("price", 0.35), ("price2", 0.5))):
        if beat.get(key) and t > t_in:
            s = 0.6 + 0.4 * ease_out((t - t_in) / 0.18)
            lab = Image.new("RGBA", (460, 100), (0, 0, 0, 0))
            ld = ImageDraw.Draw(lab)
            ld.rounded_rectangle((0, 0, 459, 99), 20, fill=(10, 14, 18, 235))
            ld.text((22, 12), beat[key], font=f_p, fill=YELLOW + (255,))
            lab = lab.resize((int(460 * s), int(100 * s)), Image.BILINEAR)
            y = SAFE["top"] if j == 0 else H - SAFE["bottom"] - 110
            rgba.alpha_composite(lab, (SAFE["left"], y))
    frame = rgba.convert("RGB")
    band = Image.new("RGBA", (W, 300), (10, 14, 18, 215))
    rgba = frame.convert("RGBA")
    rgba.alpha_composite(band, (0, H // 2 - 150))
    return draw_words(rgba.convert("RGB"), beat["onscreen"], t, (SAFE["left"], H // 2 - 140, W - SAFE["right"], H // 2 + 140), 80, "center", step=0.09)


def _fit_font(txt: str, max_w: int, start: int, floor: int = 56) -> ImageFont.FreeTypeFont:
    size = start
    while size > floor and ImageFont.truetype(FONT_BOLD, size).getlength(txt) > max_w:
        size -= 4
    return ImageFont.truetype(FONT_BOLD, size)


def scene_stat(beat: dict, t: float, dur: float, ctx: dict) -> Image.Image:
    frame = color_field(int(beat.get("palette", 1)), t)
    frame = draw_words(frame, beat["label"], t, (SAFE["left"], SAFE["top"] + 60, W - SAFE["right"], SAFE["top"] + 360), 92, "center", step=0.1)
    rgba = frame.convert("RGBA")
    stacked = max(len(beat["left"]), len(beat["right"])) > 6          # words, not numbers -> one row each
    f_name = ImageFont.truetype(FONT_BOLD, 56)
    items = ((beat["left"], beat.get("left_name", ""), 0.25), (beat["right"], beat.get("right_name", ""), 0.55))
    for k, (val, name, t_in) in enumerate(items):
        if t < t_in:
            continue
        p = ease_out((t - t_in) / 0.22)
        name1 = name.replace("\n", " ")
        if stacked:
            f_big = _fit_font(val, W - SAFE["left"] - SAFE["right"], 150)
            layer = Image.new("RGBA", (W, 330), (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            nw = f_name.getlength(name1)
            ld.text(((W - nw) / 2, 10), name1, font=f_name, fill=WHITE + (255,))
            vw = f_big.getlength(val)
            ld.text(((W - vw) / 2 + 4, 94), val, font=f_big, fill=(0, 0, 0, 220))
            ld.text(((W - vw) / 2, 90), val, font=f_big, fill=YELLOW + (255,))
            x = int(-W * 0.5 * (1 - p)) if k == 0 else int(W * 0.5 * (1 - p))
            rgba.alpha_composite(layer, (x, int(H * 0.34) + k * 400))
        else:
            f_big = _fit_font(val, W // 2 - 60, 230)
            layer = Image.new("RGBA", (W // 2, 420), (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            vw = f_big.getlength(val)
            ld.text(((W // 2 - vw) / 2 + 5, 25), val, font=f_big, fill=(0, 0, 0, 220))
            ld.text(((W // 2 - vw) / 2, 20), val, font=f_big, fill=YELLOW + (255,))
            for li, ln in enumerate(name.split("\n")):
                nw = f_name.getlength(ln)
                ld.text(((W // 2 - nw) / 2, 280 + li * 64), ln, font=f_name, fill=WHITE + (255,))
            dx = (-420 if k == 0 else 420) * (1 - p)
            rgba.alpha_composite(layer, (int(k * W // 2 + dx), int(H * 0.42)))
    return rgba.convert("RGB")


SCENES = {"hook": scene_hook, "cuts": scene_cuts, "pricedrop": scene_pricedrop, "kinetic": scene_kinetic,
          "versus": scene_versus, "stat": scene_stat}


def make_ctx(cache_dir) -> dict:
    imgs: dict = {}

    def get(src: str) -> Image.Image:
        if src not in imgs:
            imgs[src] = load_image(src, cache_dir)
        return imgs[src]

    cuts: dict = {}

    def cut(src: str) -> Image.Image:
        if src not in cuts:
            cuts[src] = cutout(get(src))
        return cuts[src]

    return {"img": get, "cut": cut, "cache": {}}


def scene_sfx(beat: dict) -> list[dict]:
    """Sound effects implied by a scene (times relative to scene start). Synthesised, no licensing."""
    k = beat["kind"]
    if k == "pricedrop":
        return [{"t": 0.0, "kind": "whoosh"}, {"t": 1.5, "kind": "ding"}]
    if k == "cuts":
        n = len(beat.get("texts") or [1])
        dur = beat["t1"] - beat["t0"]
        return [{"t": i * dur / n, "kind": "whoosh"} for i in range(n)]
    return [{"t": 0.0, "kind": "whoosh"}]
