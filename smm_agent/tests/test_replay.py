"""Regression on a REAL recorded run (method v1, hypothetical dental clinic, 12 model steps on tape): replayed through
the current code with zero model calls, every deliverable must come from the final revised plan."""
import json
from datetime import datetime, timezone
from pathlib import Path

from smm import replay

FIX = Path(__file__).parent / "fixtures"
ROOT = Path(__file__).resolve().parent.parent


def test_recorded_dental_run_replays_and_every_deliverable_follows_the_final_plan(tmp_path):
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "dental.tape.jsonl").write_text((FIX / "dental_v1.tape.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
    case = {"key": "dental", "client": "dental", "real": False, "request": "Нужно больше пациентов на импланты."}
    r = replay.replay_case(case, runs, ROOT / "brain" / "METHOD_v1.md", tmp_path / "out",
                           now=datetime(2026, 10, 10, tzinfo=timezone.utc))
    assert r["model_calls"] == 0 and r["replayed_steps"] >= 10
    assert r["verify_problems"] == []
    assert len(r["week1"]) >= 2 and r["owner_items"] <= 7
    card = (tmp_path / "out" / "dental" / "shoot_card_week1_ru.txt").read_text(encoding="utf-8")
    assert "комбик" not in card and "Отправляйте ролики как файл" in card        # no music-shop template
    assert not (ROOT / "stress" / "clients" / "dental" / "codes.json").exists()   # sandbox: real folder untouched
