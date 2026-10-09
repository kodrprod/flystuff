import json
import subprocess
from datetime import datetime

import pytest

from smm import attribution as A
from smm import formats as F
from smm import llm as L

SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}, "n": {"type": "integer", "minimum": 0},
          "tags": {"type": "array", "items": {"type": "string"}, "minItems": 1}},
          "required": ["ok", "n", "tags"], "additionalProperties": False}


# ------------------------------------------------------------------ validate
def test_validate_catches_the_usual_model_output_failures():
    assert L.validate({"ok": True, "n": 2, "tags": ["a"]}, SCHEMA) == []
    errs = L.validate({"ok": "yes", "n": -1, "tags": [], "extra": 1}, SCHEMA)
    joined = " ".join(errs)
    assert "expected boolean" in joined and "< 0" in joined and "fewer than 1" in joined and "unexpected key" in joined
    assert "missing required 'tags'" in " ".join(L.validate({"ok": True, "n": 1}, SCHEMA))
    assert L.validate(True, {"type": "integer"}) != []          # bool is not an integer


# ------------------------------------------------------------------ CLI backend (fake runner, no tokens)
class FakeRun:
    def __init__(self, envelopes):
        self.envelopes = list(envelopes)
        self.calls = []

    def __call__(self, cmd, input, capture_output, text, timeout):
        self.calls.append((cmd, input))
        env = self.envelopes.pop(0)
        if isinstance(env, tuple):          # (returncode, stdout, stderr)
            return subprocess.CompletedProcess(cmd, env[0], env[1], env[2])
        return subprocess.CompletedProcess(cmd, 0, json.dumps(env), "")


def test_cli_backend_uses_structured_output_and_low_overhead_flags(tmp_path):
    run = FakeRun([{"type": "result", "is_error": False, "result": "{}", "structured_output": {"ok": True, "n": 1, "tags": ["x"]},
                    "total_cost_usd": 0.01}])
    llm = L.LLM(L.CLIBackend(binary="claude", runner=run), L.Tape(tmp_path / "t.jsonl"))
    assert llm.json("diagnosis", "SYS", "PROMPT", SCHEMA) == {"ok": True, "n": 1, "tags": ["x"]}
    cmd, stdin = run.calls[0]
    assert cmd[:2] == ["claude", "-p"] and "--json-schema" in cmd and stdin == "PROMPT"
    assert cmd[cmd.index("--system-prompt") + 1] == "SYS"            # default Claude Code prompt replaced
    assert cmd[cmd.index("--tools") + 1] == ""                        # no tools on judgment steps
    assert "--bare" not in cmd                                       # measured: --bare breaks subscription auth


def test_invalid_output_is_retried_with_the_errors_then_succeeds(tmp_path):
    run = FakeRun([{"is_error": False, "structured_output": {"ok": True, "n": -5, "tags": []}},
                   {"is_error": False, "structured_output": {"ok": True, "n": 5, "tags": ["fixed"]}}])
    llm = L.LLM(L.CLIBackend(runner=run), L.Tape(tmp_path / "t.jsonl"))
    assert llm.json("s", "", "P", SCHEMA)["tags"] == ["fixed"]
    assert "FAILED VALIDATION" in run.calls[1][1]
    tape = [json.loads(l) for l in (tmp_path / "t.jsonl").read_text().splitlines()]
    assert [t["ok"] for t in tape] == [False, True] and tape[0]["key"] == tape[1]["key"]


def test_still_invalid_raises(tmp_path):
    bad = {"is_error": False, "structured_output": {"ok": 1}}
    llm = L.LLM(L.CLIBackend(runner=FakeRun([bad, bad])), L.Tape(tmp_path / "t.jsonl"))
    with pytest.raises(L.LLMError):
        llm.json("s", "", "P", SCHEMA)


def test_usage_limit_is_a_distinct_resumable_error(tmp_path):
    run = FakeRun([(1, "", "Claude usage limit reached. Your limit will reset at 5pm")])
    llm = L.LLM(L.CLIBackend(runner=run), L.Tape(tmp_path / "t.jsonl"))
    with pytest.raises(L.UsageLimitError):
        llm.json("s", "", "P", SCHEMA)


def test_recorded_backend_replays_by_prompt_and_never_invents(tmp_path):
    tape = L.Tape(tmp_path / "t.jsonl")
    live = L.LLM(L.CLIBackend(runner=FakeRun([{"is_error": False, "structured_output": {"ok": True, "n": 3, "tags": ["r"]}}])), tape)
    live.json("s", "SYS", "P", SCHEMA)
    rec = L.get_llm("recorded", tmp_path / "t.jsonl")
    assert rec.json("s", "SYS", "P", SCHEMA)["n"] == 3
    with pytest.raises(L.LLMError, match="no recording"):
        rec.json("s", "SYS", "a different prompt", SCHEMA)


def test_parked_run_resumes_from_the_tape_without_paying_twice(tmp_path):
    ok = {"is_error": False, "structured_output": {"ok": True, "n": 1, "tags": ["t"]}}
    # the exact envelope the CLI printed when the subscription hit its limit on 2026-10-09
    limit = {"type": "result", "subtype": "success", "is_error": True, "api_error_status": 429,
             "api_error": "usage_limit_reached", "result": "You've hit your session limit · resets 8:10am (UTC)"}
    first = FakeRun([ok, limit])
    llm = L.LLM(L.CLIBackend(runner=first), L.Tape(tmp_path / "t.jsonl"))
    llm.json("step1", "S", "P1", SCHEMA)
    with pytest.raises(L.UsageLimitError):
        llm.json("step2", "S", "P2", SCHEMA)
    second = FakeRun([ok])                                          # limit reset: re-run the same command
    llm2 = L.LLM(L.CLIBackend(runner=second), L.Tape(tmp_path / "t.jsonl"))
    llm2.json("step1", "S", "P1", SCHEMA)                           # replayed, no model call
    llm2.json("step2", "S", "P2", SCHEMA)                           # the parked step runs live
    assert len(second.calls) == 1 and second.calls[0][1] == "P2" and llm2.replayed == ["step1"]
    llm3 = L.LLM(L.CLIBackend(runner=FakeRun([ok])), L.Tape(tmp_path / "t.jsonl"), resume=False)
    llm3.json("step1", "S", "P1", SCHEMA)
    assert llm3.replayed == []                                      # resume can be switched off


def test_numbers_that_contain_429_are_not_a_usage_limit(tmp_path):
    ok = {"type": "result", "is_error": False, "api_error_status": None, "duration_ms": 14290,
          "usage": {"cache_creation_input_tokens": 42901}, "structured_output": {"ok": True, "n": 1, "tags": ["t"]}}
    llm = L.LLM(L.CLIBackend(runner=FakeRun([ok])), L.Tape(tmp_path / "t.jsonl"))
    assert llm.json("s", "", "P", SCHEMA)["ok"] is True
    for msg in ("Error: HTTP 429 Too Many Requests", "Claude usage limit reached"):
        with pytest.raises(L.UsageLimitError):
            L.LLM(L.CLIBackend(runner=FakeRun([(1, "", msg)])), L.Tape(tmp_path / "u.jsonl")).json("s", "", "P", SCHEMA)


# ------------------------------------------------------------------ attribution
def test_codes_are_unique_short_and_keyboard_safe():
    codes = {A.make_code(c, p) for c in range(20) for p in range(40)}
    assert len(codes) == 800
    assert all(len(c) == 4 and set(c) <= set(A.LETTERS + A.DIGITS) for c in codes)


def test_cyrillic_typed_code_matches_and_shop_messages_do_not_count():
    export = """08.10.2026, 14:03 - Muzzone: Здравствуйте! Код KT27 действует
08.10.2026, 14:05 - Айгерим: Здравствуйте, пишу по видео кт 27
08.10.2026, 14:06 - Айгерим: КТ27 ещё раз
[09.10.2026, 09:12:44] Данияр: Добрый день, KT-27 есть в наличии?
и вторая строка
09.10.2026, 10:00 - Олжас: просто вопрос без кода"""
    msgs = A.parse_whatsapp_export(export)
    assert len(msgs) == 5 and msgs[3].text.endswith("вторая строка")
    res = A.count_inquiries(msgs, ["KT27", "MO35"], shop_senders={"Muzzone"})
    assert res["KT27"]["customers"] == 2 and res["KT27"]["first_contact"].startswith("2026-10-08T14:05")
    assert res["MO35"]["customers"] == 0


def test_wa_link_prefills_the_code():
    link = A.wa_link("+7 701 0987734", "KT27", "Alston AS-100BK")
    assert link.startswith("https://wa.me/77010987734?text=") and "KT27" in link
    assert "KT27" in A.cta_text("KT27")


# ------------------------------------------------------------------ formats
def test_format_library_is_executable_within_the_weekly_budget():
    for f in F.LIB.values():
        assert f.funnel in F.FUNNEL and f.job and f.kpi and f.evidence
        assert f.worker_minutes() <= 6.0, f.id            # any single format fits easily in 20 minutes
    week = ["sound_check", "same_riff_two_prices", "staff_answers", "deal_proof"]
    assert F.weekly_minutes(week) <= 17                     # conservative upper bound
    shots = F.get("same_riff_two_prices").make_shots("w1p2", product="Alston AS-100BK", product2="Cort X100")
    assert [s.id for s in shots] == ["w1p2_a", "w1p2_b"] and "Cort X100" in shots[1].what
    with pytest.raises(KeyError):
        F.get("viral_dance")
