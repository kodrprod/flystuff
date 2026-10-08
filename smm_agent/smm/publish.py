"""Publish gate (rail R2 in code): nothing goes live without an approval that is bound
to the exact video and caption bytes. Any later edit changes the hash and voids it.

The package also encodes platform limits, so a rejected file never costs a round trip
(the TikTok publish tool rejects some files only asynchronously, after submission).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .render import probe, tiktok_media_problems

TIKTOK_TITLE_MAX = 150


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class Approval:
    video_sha256: str
    caption_sha256: str
    approver: str
    role: str                 # must be CLIENT (or BOSS if the client named them approver)
    at: str
    note: str = ""


class ApprovalStore:
    def __init__(self, directory: str | Path):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)

    def approve(self, video: str | Path, caption: str, approver: str, role: str, note: str = "",
                now: datetime | None = None) -> Approval:
        if role not in ("CLIENT", "BOSS"):
            raise ValueError("only the client side can approve")
        a = Approval(sha256_file(video), sha256_text(caption), approver, role,
                     (now or datetime.now(timezone.utc)).isoformat(timespec="seconds"), note)
        (self.dir / f"{a.video_sha256[:16]}_{a.caption_sha256[:8]}.json").write_text(
            json.dumps(asdict(a), ensure_ascii=False, indent=1), encoding="utf-8")
        return a

    def find(self, video: str | Path, caption: str) -> Approval | None:
        key = f"{sha256_file(video)[:16]}_{sha256_text(caption)[:8]}.json"
        p = self.dir / key
        return Approval(**json.loads(p.read_text(encoding="utf-8"))) if p.exists() else None


@dataclass
class PublishPackage:
    video: str
    caption: str                    # TikTok "title" (<=150) / Reels caption
    platform: str = "tiktok"
    is_aigc: bool | None = None     # must be set explicitly (True/False); None = unanswered
    privacy: str = "PUBLIC_TO_EVERYONE"
    description: str = ""


def problems(pkg: PublishPackage, store: ApprovalStore, scripts_ok: bool) -> list[str]:
    """Reasons this package may not be published. Empty list = cleared."""
    out: list[str] = []
    if not scripts_ok:
        out.append("R4: script/caption did not pass the content checks")
    if pkg.is_aigc is None:
        out.append("AI label not answered (is_aigc must be True or False)")
    try:
        info = probe(pkg.video)
        out += [f"media: {p}" for p in tiktok_media_problems(info)] if pkg.platform == "tiktok" else []
    except Exception as e:
        out.append(f"media unreadable: {e!r}")
        return out
    if pkg.platform == "tiktok" and len(pkg.caption) > TIKTOK_TITLE_MAX:
        out.append(f"caption {len(pkg.caption)} chars > {TIKTOK_TITLE_MAX}")
    if store.find(pkg.video, pkg.caption) is None:
        out.append("R2: no client approval matches this exact video+caption (edited since approval, or never approved)")
    return out


def to_tiktok_prepare_args(pkg: PublishPackage, connector_id: str, video_url: str, draft: bool = True) -> dict:
    """Arguments for the Higgsfield `tiktok_prepare_publish` tool. NOTE: that tool opens a form that a
    *human must submit*, and `video_url` must be a Higgsfield-hosted asset (upload first). So this path is
    semi-autonomous by design; full autonomy needs TikTok's own Content Posting API (audited app)."""
    return {"connector_id": connector_id, "mode": "UPLOAD_TO_DRAFT" if draft else "DIRECT_POST",
            "media_type": "VIDEO", "video_url": video_url, "title": pkg.caption[:TIKTOK_TITLE_MAX],
            "description": pkg.description, "is_aigc": pkg.is_aigc, "privacy_level": pkg.privacy}
