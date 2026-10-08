"""Pacing check: is this a video or a slideshow?

A deterministic *floor*, not a quality score. It cannot tell good from great; it can tell
"static slides with text" from "something moves and changes quickly". Rules (heuristics from
common short-form practice, to be re-tuned on our own measured results):

  P1  frame 0 is not blank/faded-in: visible content from the first frame
  P2  motion in the first 2 s: mean frame-to-frame luma difference above a floor
  P3  a visible *event* (cut, punch-in, price change, word pop) at least every MAX_GAP_FIRST s
      during the first 3 s and every MAX_GAP s afterwards
  P4  no frozen stretch longer than MAX_FREEZE s

Events are frame-to-frame jumps in luma difference (YDIF from ffmpeg signalstats), measured on
a 10 fps downscaled copy so it is fast and compression noise does not count.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

SAMPLE_FPS = 10
EVENT_YDIF = 3.0          # jump size that counts as a visible change
MAX_GAP_FIRST = 1.2       # seconds between events during the first 3 s
MAX_GAP = 2.2             # ...and afterwards
MAX_FREEZE = 1.5          # seconds of near-zero change
FREEZE_YDIF = 0.15
FIRST2_MOTION_MIN = 1.0   # mean YDIF over the first 2 s


def ydif_series(path: str | Path) -> list[float]:
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-vf",
                        f"fps={SAMPLE_FPS},scale=108:-2,signalstats,metadata=mode=print:key=lavfi.signalstats.YDIF:file=-",
                        "-an", "-f", "null", "-"], capture_output=True, text=True)
    return [float(x) for x in re.findall(r"lavfi\.signalstats\.YDIF=([\d.]+)", r.stdout + r.stderr)]


def frame0_luma(path: str | Path) -> float:
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-frames:v", "1", "-vf",
                        "scale=108:-2,signalstats,metadata=mode=print:key=lavfi.signalstats.YAVG:file=-", "-an", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"lavfi\.signalstats\.YAVG=([\d.]+)", r.stdout + r.stderr)
    return float(m.group(1)) if m else 0.0


def analyze_series(y: list[float], f0_luma: float) -> dict:
    dt = 1.0 / SAMPLE_FPS
    events = [i * dt for i, v in enumerate(y) if v >= EVENT_YDIF]
    # collapse adjacent samples of the same event
    ev: list[float] = []
    for t in events:
        if not ev or t - ev[-1] > 2 * dt:
            ev.append(t)
    dur = len(y) * dt
    marks = [0.0] + ev + [dur]
    gaps = [(marks[i], marks[i + 1] - marks[i]) for i in range(len(marks) - 1)]
    first2 = y[: int(2 * SAMPLE_FPS)]
    m2 = sum(first2) / len(first2) if first2 else 0.0
    # longest frozen run
    run = best = 0
    for v in y:
        run = run + 1 if v < FREEZE_YDIF else 0
        best = max(best, run)
    problems = []
    if f0_luma < 12:
        problems.append("P1 first frame is (near) black: content must be visible from frame 0")
    if m2 < FIRST2_MOTION_MIN:
        problems.append(f"P2 little motion in the first 2 s (mean YDIF {m2:.2f} < {FIRST2_MOTION_MIN})")
    for start, g in gaps:
        limit = MAX_GAP_FIRST if start < 3.0 else MAX_GAP
        if g > limit + 1e-9 and (start + g) <= dur + 1e-9 and not (start + g >= dur - 0.2 and g <= limit + 0.6):
            problems.append(f"P3 no visible change for {g:.1f}s starting at {start:.1f}s (limit {limit}s)")
    if best * dt > MAX_FREEZE:
        problems.append(f"P4 frozen for {best * dt:.1f}s")
    return {"duration_s": dur, "events": ev, "n_events": len(ev), "first2_motion": m2,
            "longest_freeze_s": best * dt, "frame0_luma": f0_luma, "problems": problems}


def analyze_pacing(path: str | Path) -> dict:
    return analyze_series(ydif_series(path), frame0_luma(path))
