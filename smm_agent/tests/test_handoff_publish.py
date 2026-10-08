import subprocess
from datetime import datetime, timedelta, timezone

import pytest

from smm.handoff import LADDER, Queue, batch_message
from smm.publish import ApprovalStore, PublishPackage, problems, sha256_file, to_tiktok_prepare_args

T0 = datetime(2026, 10, 8, 9, 0, tzinfo=timezone.utc)


def mk(q, cid="c1", kind="approval", role="CLIENT", **kw):
    return q.create(id=cid, client="muzzone", stage="10 Approval", role=role, kind=kind, do="Посмотрите видео",
                    paste_back="approved / changes", why="R2", created_at=T0.isoformat(), **kw)


def test_roundtrip_and_batch_message(tmp_path):
    q = Queue(tmp_path)
    mk(q, "a"); mk(q, "b", kind="question", role="BOSS")
    assert [c.id for c in q.all()] == ["a", "b"]
    msg = batch_message(q.open_for("CLIENT"))
    assert msg.startswith("HANDOFF — you are: CLIENT") and "Paste back: approved / changes" in msg
    with pytest.raises(ValueError):
        mk(q, "a")                                   # duplicate id
    with pytest.raises(ValueError):
        q.create(id="x", client="m", stage="s", role="NOBODY", kind="question", do="", paste_back="", why="")


def test_escalation_ladder_is_idempotent_and_ends_parked(tmp_path):
    q = Queue(tmp_path)
    mk(q, "a", due_hours=48)
    assert q.tick(T0 + timedelta(hours=1)) == []
    acts = q.tick(T0 + timedelta(hours=25))
    assert [a for _, a in acts] == ["reminder"]
    assert q.tick(T0 + timedelta(hours=26)) == []    # same level, nothing new
    assert [a for _, a in q.tick(T0 + timedelta(hours=80))] == ["shorten_and_switch_channel"]
    assert [a for _, a in q.tick(T0 + timedelta(hours=200))] == ["parked"]
    assert q.get("a").status == "parked"


def test_gated_kinds_never_default_to_yes(tmp_path):
    q = Queue(tmp_path)
    for k in ("approval", "offer", "publish"):
        c = mk(q, k, kind=k)
        d = q.default_on_timeout(c)
        assert "do not" in d and "approved" not in d.lower().replace("not published", "")
    assert "unknown" in q.default_on_timeout(mk(q, "qq", kind="question", role="BOSS"))


def test_answered_cards_do_not_escalate_and_record_minutes(tmp_path):
    q = Queue(tmp_path)
    mk(q, "a")
    q.answer("a", "approved", minutes=3, now=T0 + timedelta(hours=2))
    assert q.tick(T0 + timedelta(hours=500)) == [] and q.get("a").minutes_spent == 3
    with pytest.raises(ValueError):
        mk(q, "b"); q.answer("b", "  ")


def test_blocked_work_is_traceable(tmp_path):
    q = Queue(tmp_path)
    mk(q, "a", blocks=["video-1"])
    assert [c.id for c in q.blocked_by_open("video-1")] == ["a"]
    q.answer("a", "approved")
    assert q.blocked_by_open("video-1") == []


# ---------------------------------------------------------------- publish gate
@pytest.fixture
def video(tmp_path):
    p = tmp_path / "v.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=1080x1920:r=30:d=4",
                    "-f", "lavfi", "-i", "sine=f=440:d=4", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                    "-shortest", str(p)], check=True)
    return p


def test_no_approval_blocks_publish(tmp_path, video):
    store = ApprovalStore(tmp_path / "ap")
    pkg = PublishPackage(str(video), "Подпись", is_aigc=False)
    assert any(p.startswith("R2") for p in problems(pkg, store, scripts_ok=True))


def test_approval_clears_then_any_edit_voids_it(tmp_path, video):
    store = ApprovalStore(tmp_path / "ap")
    pkg = PublishPackage(str(video), "Подпись", is_aigc=False)
    store.approve(video, "Подпись", "Pavel", "CLIENT")
    assert problems(pkg, store, scripts_ok=True) == []
    # caption edited after approval -> void
    assert any(p.startswith("R2") for p in problems(PublishPackage(str(video), "Другая подпись", is_aigc=False), store, True))
    # video re-edited after approval -> void
    with open(video, "ab") as fh:
        fh.write(b"\0")
    assert any(p.startswith("R2") for p in problems(pkg, store, scripts_ok=True))


def test_other_rails_in_gate(tmp_path, video):
    store = ApprovalStore(tmp_path / "ap")
    store.approve(video, "x" * 200, "P", "CLIENT")
    assert any("AI label" in p for p in problems(PublishPackage(str(video), "x" * 200), store, True))
    assert any("chars > 150" in p for p in problems(PublishPackage(str(video), "x" * 200, is_aigc=False), store, True))
    assert any(p.startswith("R4") for p in problems(PublishPackage(str(video), "x", is_aigc=False), store, scripts_ok=False))
    with pytest.raises(ValueError):
        store.approve(video, "x", "bot", "PUBLISHER")      # only the client side can approve


def test_tiktok_args_default_to_draft(video):
    a = to_tiktok_prepare_args(PublishPackage(str(video), "Подпись", is_aigc=False), "cid", "https://example/v.mp4")
    assert a["mode"] == "UPLOAD_TO_DRAFT" and a["is_aigc"] is False and a["media_type"] == "VIDEO"
