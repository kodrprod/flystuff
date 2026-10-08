import subprocess

import pytest
from PIL import Image, ImageDraw, ImageStat

from smm import motion as M
from smm import pacing as P
from smm import render as R


def ff(*args):
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


# ----------------------------------------------------------------- regression: newline in fit_text
def test_text_with_newline_and_phone_fits_large():
    font, lines = R.fit_text("Написать в WhatsApp\n+7 701 0987734", 876, 700, start=120)
    assert font.size >= 84, f"tiny CTA text ({font.size}px): newline-joined 'word' bug is back"
    assert any("+7 701 0987734" in ln for ln in lines)


# ----------------------------------------------------------------- cutout
def product_on_white(path, size=400):
    im = Image.new("RGB", (size, size), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.rectangle((100, 120, 300, 300), fill=(30, 60, 160))          # the "product"
    d.rectangle((150, 160, 250, 200), fill=(255, 255, 255))        # white part INSIDE the product
    im.save(path)
    return im


def test_cutout_removes_border_white_keeps_inner_white_and_crops_tight(tmp_path):
    im = product_on_white(tmp_path / "p.png")
    cut = M.cutout(im)
    assert cut.mode == "RGBA" and cut.width < 260 and cut.height < 260        # cropped to the product
    a = cut.getchannel("A")
    assert a.getpixel((2, 2)) < 30 or a.getpixel((cut.width - 3, 3)) < 30       # outside = transparent
    assert a.getpixel((cut.width // 2, cut.height // 2)) > 200                # inner white part kept


def test_cutout_falls_back_when_no_clean_white_backdrop():
    grey = Image.new("RGB", (300, 300), (120, 120, 120))
    out = M.cutout(grey)
    assert out.size == (300, 300) and out.getchannel("A").getextrema() == (255, 255)


# ----------------------------------------------------------------- detail picker
def test_detail_boxes_prefer_distinct_features_over_uniform_texture():
    im = Image.new("RGB", (400, 400), (200, 170, 110))
    d = ImageDraw.Draw(im)
    for x in range(0, 200, 4):                       # left half: uniform "grille" stripes
        d.line((x, 0, x, 400), fill=(90, 70, 40), width=1)
    for i, (x, y) in enumerate([(230, 40), (300, 50), (250, 110), (320, 130), (270, 70)]):   # right: distinct knobs
        d.ellipse((x, y, x + 34, y + 34), fill=(20, 20, 20))
        d.rectangle((x - 10, y + 150, x + 40, y + 190), outline=(0, 0, 0), width=3)
    box = M.detail_boxes(im, n=1, frac=0.5)[0]
    assert (box[0] + box[2]) / 2 > 200, f"picked the uniform-texture side: {box}"


# ----------------------------------------------------------------- scenes: never blank at t=0, correct size
@pytest.fixture
def ctx(tmp_path):
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    product_on_white(a)
    product_on_white(b, 500)
    return M.make_ctx(tmp_path / "c"), str(a), str(b)


def test_every_scene_shows_content_on_frame_zero(ctx):
    c, a, b = ctx
    beats = [
        {"kind": "hook", "image": a, "onscreen": "Комбик 30 Вт: было 70 720 ₸"},
        {"kind": "cuts", "image": a, "texts": ["Один", "Два"]},
        {"kind": "pricedrop", "image": a, "old_price": "70 720 ₸", "price": "56 576 ₸", "badge": "-20%", "onscreen": "Имя"},
        {"kind": "kinetic", "onscreen": "Скидка 20%", "palette": 1},
        {"kind": "versus", "image": a, "image2": b, "price": "1 ₸", "price2": "2 ₸", "onscreen": "Два укулеле"},
        {"kind": "stat", "label": "Метка", "left": "88", "right": "128", "left_name": "A", "right_name": "B"},
        {"kind": "stat", "label": "Метка", "left": "Массив ели", "right": "Клён", "left_name": "A", "right_name": "B"},
    ]
    for beat in beats:
        f = M.SCENES[beat["kind"]](beat, 0.0, 2.0, c)
        assert f.size == (R.W, R.H) and f.mode == "RGB"
        assert max(ImageStat.Stat(f).stddev) > 8, f"{beat['kind']} is blank at t=0"
        f2 = M.SCENES[beat["kind"]](beat, 1.0, 2.0, c)
        assert ImageStat.Stat(f2.convert("L")).mean != ImageStat.Stat(f.convert("L")).mean or f.tobytes() != f2.tobytes()


def test_pricedrop_counts_down_monotonically_to_the_real_price(ctx):
    c, a, _ = ctx
    beat = {"kind": "pricedrop", "image": a, "old_price": "100 000 ₸", "price": "80 000 ₸"}
    shown = []
    for t in (0.7, 0.9, 1.1, 1.3, 1.6, 2.0):
        # recompute the value shown the same way the scene does
        k = M.ease_out((t - 0.65) / 0.85)
        shown.append(int(100000 + (80000 - 100000) * k))
    assert shown == sorted(shown, reverse=True) and shown[-1] == 80000
    M.SCENES["pricedrop"](beat, 2.0, 2.8, c)      # renders without error at the end state


def test_sfx_for_scenes():
    assert [e["kind"] for e in M.scene_sfx({"kind": "pricedrop", "t0": 0, "t1": 3})] == ["whoosh", "ding"]
    assert len(M.scene_sfx({"kind": "cuts", "t0": 0, "t1": 3, "texts": ["a", "b", "c"]})) == 3


# ----------------------------------------------------------------- pacing
def test_static_slide_fails_pacing(tmp_path):
    # a genuine still: one frame looped for 6 s (the "slideshow" case)
    ff("-f", "lavfi", "-i", "testsrc2=s=360x640:r=30", "-frames:v", "1", str(tmp_path / "still.png"))
    ff("-loop", "1", "-framerate", "30", "-i", str(tmp_path / "still.png"), "-t", "6", "-c:v", "libx264",
       "-pix_fmt", "yuv420p", str(tmp_path / "static.mp4"))
    a = P.analyze_pacing(tmp_path / "static.mp4")
    codes = " ".join(a["problems"])
    assert "P2" in codes and "P3" in codes and "P4" in codes and a["longest_freeze_s"] >= 5.5


def test_fast_cuts_pass_pacing(tmp_path):
    # brightness flips between -0.35 and +0.35 every 0.8 s: a clear visible event every 0.8 s
    ff("-f", "lavfi", "-i", "testsrc2=s=360x640:r=30:d=6", "-vf",
       "eq=brightness='0.35*(mod(floor(t/0.8),2)*2-1)':eval=frame", "-c:v", "libx264", "-pix_fmt", "yuv420p",
       str(tmp_path / "fast.mp4"))
    a = P.analyze_pacing(tmp_path / "fast.mp4")
    assert not any(p.startswith(("P2", "P3", "P4")) for p in a["problems"]), a
    assert a["n_events"] >= 6


def test_black_first_frame_flagged():
    a = P.analyze_series([5.0] * 60, f0_luma=2.0)
    assert any(p.startswith("P1") for p in a["problems"])
