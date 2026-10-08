import subprocess

import pytest
from PIL import Image, ImageStat

from smm import edit as E


def ff(*args):
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


@pytest.fixture(scope="module")
def clips(tmp_path_factory):
    d = tmp_path_factory.mktemp("clips")
    # normal landscape clip with loud tone
    ff("-f", "lavfi", "-i", "testsrc2=s=1920x1080:r=30:d=4", "-f", "lavfi", "-i", "sine=f=440:d=4",
       "-af", "volume=0.8", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(d / "landscape.mp4"))
    # stored landscape with white band on TOP rows, then display-rotated 90 deg (iPhone style)
    ff("-f", "lavfi", "-i", "color=c=black:s=1920x1080:r=30:d=3", "-f", "lavfi", "-i", "sine=f=330:d=3",
       "-vf", "drawbox=x=0:y=0:w=1920:h=200:color=white:t=fill", "-c:v", "libx264", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-shortest", str(d / "band_src.mp4"))
    ff("-display_rotation:v:0", "90", "-i", str(d / "band_src.mp4"), "-c", "copy", str(d / "rotated.mp4"))
    # dark, silent, quiet, short
    ff("-f", "lavfi", "-i", "color=c=0x050505:s=1280x720:r=30:d=3", "-f", "lavfi", "-i", "sine=f=440:d=3",
       "-af", "volume=0.5", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(d / "dark.mp4"))
    ff("-f", "lavfi", "-i", "testsrc2=s=1280x720:r=30:d=3", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(d / "silent.mp4"))
    ff("-f", "lavfi", "-i", "testsrc2=s=1280x720:r=30:d=3", "-f", "lavfi", "-i", "sine=f=440:d=3",
       "-af", "volume=0.001", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(d / "quiet.mp4"))
    ff("-f", "lavfi", "-i", "testsrc2=s=1280x720:r=30:d=1", "-f", "lavfi", "-i", "sine=f=440:d=1",
       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(d / "short.mp4"))
    return d


def frame(path, t, out):
    ff("-ss", str(t), "-i", str(path), "-frames:v", "1", str(out))
    return Image.open(out).convert("L")


def test_analyze_detects_rotation_and_swaps_display_dims(clips):
    a = E.analyze_clip(clips / "rotated.mp4")
    assert a["rotation"] in (90, 270) and (a["width"], a["height"]) == (1080, 1920)


def test_quality_gate_flags_each_problem(clips):
    assert E.analyze_clip(clips / "landscape.mp4", "demo", 3)["problems"] == []
    assert any("too dark" in p for p in E.analyze_clip(clips / "dark.mp4", "process")["problems"])
    assert any("no audio" in p for p in E.analyze_clip(clips / "silent.mp4", "demo")["problems"])
    assert any("too quiet" in p for p in E.analyze_clip(clips / "quiet.mp4", "demo")["problems"])
    assert any("too short" in p for p in E.analyze_clip(clips / "short.mp4", "demo", need_seconds=5)["problems"])
    assert not any("audio" in p or "quiet" in p for p in E.analyze_clip(clips / "silent.mp4", "detail")["problems"])


def test_assemble_outputs_platform_format_with_audio_and_sane_loudness(clips, tmp_path):
    info = E.assemble([
        {"path": clips / "landscape.mp4", "start": 0.5, "dur": 2.0, "text": "Alston AS-100BK: 59 800 ₸"},
        {"path": clips / "silent.mp4", "start": 0.5, "dur": 1.5},
    ], tmp_path / "out.mp4")
    assert (info["width"], info["height"]) == (1080, 1920) and abs(info["fps"] - 30) < 0.01
    assert info["has_audio_stream"] and abs(info["duration_s"] - 3.5) < 0.25
    lufs = E.measure_loudness(tmp_path / "out.mp4")
    assert lufs is not None and -26 < lufs < -9


def test_rotation_is_respected(clips, tmp_path):
    out = tmp_path / "rot.mp4"
    E.assemble([{"path": clips / "rotated.mp4", "start": 0.5, "dur": 1.5}], out)
    g = frame(out, 0.8, tmp_path / "f.png")
    side = max(ImageStat.Stat(g.crop((0, 600, 150, 1300))).mean[0], ImageStat.Stat(g.crop((930, 600, 1080, 1300))).mean[0])
    top = ImageStat.Stat(g.crop((300, 0, 780, 150))).mean[0]
    assert side > 200 and top < 40          # the band that was on top of the stored frame is now at a side


def test_caption_is_burned_in_only_when_given(clips, tmp_path):
    E.assemble([{"path": clips / "landscape.mp4", "start": 0.5, "dur": 1.5, "text": "Скидка 20% на распродаже"}], tmp_path / "a.mp4")
    E.assemble([{"path": clips / "landscape.mp4", "start": 0.5, "dur": 1.5}], tmp_path / "b.mp4")
    ga, gb = frame(tmp_path / "a.mp4", 1.0, tmp_path / "a.png"), frame(tmp_path / "b.mp4", 1.0, tmp_path / "b.png")
    region = (0, 1200, 1080, 1560)
    assert ImageStat.Stat(ga.crop(region)).mean[0] < ImageStat.Stat(gb.crop(region)).mean[0] - 15   # dark caption band


def test_start_past_end_is_an_error(clips, tmp_path):
    with pytest.raises(ValueError):
        E.assemble([{"path": clips / "short.mp4", "start": 5.0, "dur": 2.0}], tmp_path / "x.mp4")
