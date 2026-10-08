"""Quality claims of the editor, each measured on synthetic signals (real-footage validation still pending)."""
import subprocess
from pathlib import Path

import pytest

from smm import edit as E


def ff(*args):
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def window_lufs(path, start, dur):
    return E.audio_stats(path, start, dur)["lufs"]


@pytest.fixture(scope="module")
def media(tmp_path_factory):
    d = tmp_path_factory.mktemp("av")
    v = ["-f", "lavfi", "-i", "testsrc2=s=1280x720:r=30:d={d}"]
    # clipped: sine driven far past full scale
    ff("-f", "lavfi", "-i", "testsrc2=s=1280x720:r=30:d=3", "-f", "lavfi", "-i", "sine=f=220:d=3",
       "-af", "volume=12", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-shortest", str(d / "clipped.mov"))
    ff("-f", "lavfi", "-i", "testsrc2=s=1280x720:r=30:d=3", "-f", "lavfi", "-i", "sine=f=220:d=3",
       "-af", "volume=0.4", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-shortest", str(d / "clean.mov"))
    # dynamics: 2 s quiet then 2 s loud (a real playing dynamic)
    ff("-f", "lavfi", "-i", "testsrc2=s=1280x720:r=30:d=4", "-f", "lavfi",
       "-i", "aevalsrc='if(lt(t,2),0.05,0.6)*sin(2*PI*330*t)':d=4:s=44100",
       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-shortest", str(d / "dynamics.mov"))
    # two takes separated by silence (worker repeated the line)
    ff("-f", "lavfi", "-i", "testsrc2=s=1280x720:r=30:d=7", "-f", "lavfi",
       "-i", "aevalsrc='if(lt(t,2),0.5,if(lt(t,3.6),0,0.5))*sin(2*PI*300*t)':d=7:s=44100",
       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-shortest", str(d / "takes.mov"))
    # shaky handheld simulation
    ff("-f", "lavfi", "-i", "testsrc2=s=1600x1000:r=30:d=4", "-f", "lavfi", "-i", "sine=f=440:d=4",
       "-vf", "crop=1280:720:x='160+120*sin(n*1.3)':y='140+100*cos(n*1.9)'", "-c:v", "libx264", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-shortest", str(d / "shaky.mp4"))
    return d


def test_clipping_is_detected_and_triggers_a_retake_request(media):
    assert E.audio_stats(media / "clipped.mov")["clipped_samples"] > E.CLIP_SAMPLES
    assert E.audio_stats(media / "clean.mov")["clipped_samples"] <= E.CLIP_SAMPLES
    probs = " ".join(E.analyze_clip(media / "clipped.mov", "demo")["problems"])
    assert "clipped" in probs and "reshoot" in probs
    assert not any("clipped" in p for p in E.analyze_clip(media / "clean.mov", "demo")["problems"])


def test_one_gain_per_take_preserves_dynamics_across_jumpcuts(media, tmp_path):
    src = media / "dynamics.mov"
    diff_src = window_lufs(src, 2.2, 1.6) - window_lufs(src, 0.2, 1.6)
    out = tmp_path / "dyn.mp4"
    E.assemble([{"path": src, "start": 0.0, "dur": 4.0, "jump": 1.0, "kind": "demo", "grade": False, "stabilize": "off"}], out)
    diff_out = window_lufs(out, 2.2, 1.6) - window_lufs(out, 0.2, 1.6)
    assert diff_src > 15                                  # the quiet->loud contrast is real
    assert abs(diff_out - diff_src) < 2.0, (diff_src, diff_out)   # ...and survives the edit (no pumping/flattening)
    assert abs(E.audio_stats(out)["lufs"] - E.TARGET_LUFS) < 2.0
    assert E.audio_stats(out)["true_peak_db"] <= 0.0


def test_last_take_is_picked_from_a_repeated_line(media):
    segs = E.speech_segments(media / "takes.mov")
    assert len(segs) == 2
    start, dur = E.pick_last_take(media / "takes.mov", need_seconds=3.0)
    assert 3.3 < start < 3.7 and 3.0 < dur < 3.8


def test_talk_segment_uses_the_last_take_automatically(media, tmp_path):
    info = E.assemble([{"path": media / "takes.mov", "dur": 3.0, "kind": "talk", "need_seconds": 3.0,
                        "grade": False, "stabilize": "off"}], tmp_path / "talk.mp4")
    assert 3.0 < info["duration_s"] < 3.9


def test_stabilisation_reduces_measured_shake(media, tmp_path):
    before = E.shake_px(media / "shaky.mp4", tmp=tmp_path)
    E.assemble([{"path": media / "shaky.mp4", "start": 0.0, "dur": 3.5, "grade": False}], tmp_path / "stab.mp4")
    after = E.shake_px(tmp_path / "stab.mp4", tmp=tmp_path)
    assert before > E.SHAKE_PX and after < before * 0.5, (before, after)


def test_captions_are_outlined_not_a_dark_slab(tmp_path):
    from PIL import Image
    p = E.caption_layer("Alston AS-100BK: 59 800 ₸", tmp_path / "c.png")
    im = Image.open(p)
    alpha = im.getchannel("A")
    covered = sum(1 for v in alpha.resize((108, 192)).getdata() if v > 0) / (108 * 192)
    assert covered < 0.12            # only the letters + outline, not a full-width band
