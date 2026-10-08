import pytest
from PIL import Image, ImageFont

from smm import render as R


def test_wrap_never_splits_words_and_respects_width():
    font = ImageFont.truetype(R.FONT_BOLD, 60)
    lines = R.wrap("Цифровое пианино Casio PX-770 за 695 913 ₸", font, 500)
    assert all(font.getlength(l) <= 500 or " " not in l for l in lines)
    assert " ".join(lines) == "Цифровое пианино Casio PX-770 за 695 913 ₸"


def test_fit_text_shrinks_and_refuses_impossible():
    font, lines = R.fit_text("Как выбрать первую электрогитару и не переплатить", 800, 600)
    assert font.size >= 48 and len(lines) >= 2
    with pytest.raises(ValueError):
        R.fit_text("слово " * 80, 400, 120)


def test_timeline_validation():
    assert R.validate_timeline([{"t0": 0, "t1": 1}, {"t0": 1, "t1": 2.5}]) == 2.5
    for bad in ([], [{"t0": 0, "t1": 1}, {"t0": 1.2, "t1": 2}], [{"t0": 0, "t1": 0}]):
        with pytest.raises(ValueError):
            R.validate_timeline(bad)


def test_end_to_end_render_meets_platform_limits(tmp_path):
    img = Image.new("RGB", (800, 600), (40, 90, 160))
    img_path = tmp_path / "p.png"
    img.save(img_path)
    script = {"beats": [
        {"t0": 0, "t1": 1.2, "kind": "photo", "image": str(img_path), "text": "Первая гитара: сколько это стоит?"},
        {"t0": 1.2, "t1": 2.4, "kind": "card", "image": str(img_path), "text": "Squier Bullet Strat",
         "price": "71 433 ₸", "old_price": "119 054 ₸"},
        {"t0": 2.4, "t1": 3.6, "kind": "text", "text": "WhatsApp +7 701 0987734"},
    ]}
    out = tmp_path / "v.mp4"
    info = R.render_video(script, out, cache_dir=tmp_path / "c")
    assert (info["width"], info["height"]) == (1080, 1920)
    assert info["codec"] == "h264" and info["has_audio_stream"]
    assert abs(info["fps"] - 30) < 0.01 and abs(info["duration_s"] - 3.6) < 0.15
    assert R.tiktok_media_problems(info) == []
    assert info["audio"] == "needs_publisher"


def test_prices_and_phones_never_break_across_lines():
    font = ImageFont.truetype(R.FONT_BOLD, 100)
    for text, token in [("Casio PX-770: стоит ли 695 913 ₸?", "695 913 ₸"),
                        ("88 клавиш, молоточковая механика\nWhatsApp +7 701 0987734", "+7 701 0987734"),
                        ("Возврат в течение 14 дней", "14 дней")]:
        lines = R.wrap(text, font, 640)
        assert any(token in ln for ln in lines), (token, lines)


def test_split_scene_renders(tmp_path):
    a = tmp_path / "a.png"; b = tmp_path / "b.png"
    Image.new("RGB", (600, 600), (200, 60, 60)).save(a)
    Image.new("RGB", (600, 400), (60, 60, 200)).save(b)
    script = {"beats": [{"t0": 0, "t1": 1.0, "kind": "split", "image": str(a), "image2": str(b),
                         "price": "32 901 ₸", "price2": "64 501 ₸", "text": "Два укулеле: 32 901 ₸ против 64 501 ₸"},
                        {"t0": 1.0, "t1": 3.2, "kind": "text", "text": "ok"}]}
    info = R.render_video(script, tmp_path / "s.mp4", cache_dir=tmp_path / "c")
    assert (info["width"], info["height"]) == (1080, 1920) and R.tiktok_media_problems(info) == []
