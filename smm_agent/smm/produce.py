"""Production: staff clips -> clean cut -> AI motion design -> checks -> one approval card per video.

    manifest_week1.json (from the brain run)   which shot is which, in the order the card asked for them
    clips folder                               what the staff sent back, in the same order
      -> match clips to shots                  a count mismatch is a question to the staff, never a guess
      -> per idea: cut plan                    last good take of every shot (sound-based), shot order from the idea
      -> edit.assemble                         music-safe loudness, stabilisation, jump-cuts, 9:16
      -> designer.design_video                 the AI designs this video's text/motion over the footage; rails,
                                               safe area and pacing are checked; a critic looks at the frames
      -> approval card                         the owner approves the exact file (hash-bound) or it never posts
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from . import designer, edit
from .facts import Ledger
from .handoff import Queue
from .llm import LLM
from .publish import sha256_file

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".3gp", ".webm"}


@dataclass
class Produced:
    idea_id: str
    ok: bool
    video: Path | None
    notes: list = field(default_factory=list)


def clip_files(folder: Path) -> list[Path]:
    """Clips in the order they were sent. Messengers name files by time, so name order is send order."""
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in VIDEO_EXT)


def match(manifest: list[dict], clips: list[Path]) -> tuple[dict[str, Path], list[str]]:
    if len(clips) != len(manifest):
        return {}, [f"expected {len(manifest)} clips in card order, got {len(clips)}: ask the staff which is which"]
    return {m["shot_id"]: c for m, c in zip(manifest, clips)}, []


def duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def cut_plan(idea: dict, shots: dict[str, Path], manifest: list[dict]) -> list[dict]:
    """One segment per filmed shot of this idea, in the idea's order. The take is chosen by sound (the card says:
    after a mistake pause and repeat, so the last long non-silent stretch is the keeper); silent shots use the
    middle of the clip, skipping the 1-second pauses the card asks for at both ends."""
    segs = []
    for m in [m for m in manifest if m["idea_id"] == idea["id"]]:
        path, need = shots[m["shot_id"]], float(m["seconds"])
        take = edit.pick_last_take(path, need)
        if take:
            start, dur = take
        else:
            total = duration(path)
            dur = min(need, max(0.5, total - 2.0))
            start = max(0.0, (total - dur) / 2)
        seg = {"path": str(path), "start": round(start, 2), "dur": round(dur, 2), "shot_id": m["shot_id"]}
        if m["kind"] == "talk":
            seg.update(kind="talk")            # speech clean-up only for talking; instruments keep their sound
        segs.append(seg)
    # pace: a visible change every <=1.2 s in the first 3 s (measured rule P3, see edit.expand_jumpcuts), every
    # ~2 s after. Jump-cuts keep source time contiguous, so nothing the staff filmed is lost.
    t = 0.0
    for seg in segs:
        if t < 3.0 and seg["dur"] > 1.3:
            seg["jump"] = 1.0
        elif seg["dur"] > 2.9:
            seg["jump"] = 2.0
        t += seg["dur"]
    return segs


def brief_for(idea: dict, code: str | None, ledger: Ledger, now=None) -> dict:
    vals = sorted(ledger.usable_values(now))
    text = " ".join([idea.get("hook_ru", "")] + list(idea.get("on_screen_ru") or []) + [idea.get("cta_ru", "")]).lower()
    return {"id": idea["id"], "hook": idea.get("hook_ru", ""), "first_frame": idea.get("first_frame", ""),
            "onscreen_texts": idea.get("on_screen_ru") or [], "cta": idea.get("cta_ru", ""), "cta_code": code,
            "facts": [v for v in vals if v and v in text], "edit_plan": idea.get("what_happens", ""),
            "why_watch": idea.get("why_stop", ""), "why_share": idea.get("why_share_or_save", ""), "images": []}


def frames_of(video: Path, out_dir: Path, n: int = 4) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    d, outs = duration(video), []
    for i in range(n):
        f = out_dir / f"look_{i}.jpg"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{d * (i + 0.5) / n:.2f}", "-i", str(video),
                        "-frames:v", "1", "-vf", "scale=540:-1", str(f)], check=True)
        outs.append(f)
    return outs


def produce_week(run_dir: Path, clips_dir: Path, ledger: Ledger, playbook: str, llm: LLM | None = None,
                 queue: Queue | None = None, client: str = "", now=None) -> list[Produced]:
    manifest = json.loads((run_dir / "manifest_week1.json").read_text(encoding="utf-8"))
    ideas = {i["id"]: i for i in json.loads((run_dir / "ideas.json").read_text(encoding="utf-8"))}
    codes = json.loads((run_dir / "campaign.json").read_text(encoding="utf-8")).get("attribution_codes", {})
    shots, probs = match(manifest, clip_files(clips_dir))
    queue = queue or Queue(run_dir / "cards")
    if probs:
        queue.create(id=f"{run_dir.name}-clips", client=client, stage="production", role="STAFF", kind="question",
                     do=probs[0], paste_back="номера роликов по порядку карточки", why="match clips to shots")
        return [Produced("*", False, None, probs)]
    out = []
    for iid in dict.fromkeys(m["idea_id"] for m in manifest):
        idea = ideas[iid]
        wd = run_dir / "produce" / iid
        base = wd / "base.mp4"
        info = edit.assemble(cut_plan(idea, shots, manifest), base)
        res = designer.design_video(brief_for(idea, codes.get(iid), ledger, now), wd / "design", ledger, playbook,
                                    llm, llm, background=base, frames_for_designer=frames_of(base, wd / "look"),
                                    now=now)
        notes = [f"edit: {info.get('duration_s')} s, audio {info.get('audio', {})}" if isinstance(info, dict) else "edit ok",
                 res.reason]
        p = Produced(iid, res.ok, res.video, notes)
        if res.video:
            queue.create(id=f"{run_dir.name}-{iid}-approve", client=client, stage="approval", role="BOSS",
                         kind="approval", do=f"Посмотрите ролик {res.video.name} ({iid}) и ответьте: ДА / НЕТ / что исправить",
                         paste_back="ДА | НЕТ | правка", why=f"video sha256 {sha256_file(res.video)[:16]}; "
                         + ("design shipped by critic" if res.ok else "critic did not ship: human decides"))
        out.append(p)
    return out
