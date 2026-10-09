import json

from smm import higgsfield as H
from smm.facts import Fact, Ledger

LG = Ledger([Fact("p", "Цифровое пианино Casio PX-770 BKC7 — 695 913 ₸", "web", "u", "2026-10-08", ["695 913 ₸"], 2),
             Fact("s", "Пианино: Бренд: Casio; Количество клавиш: 88", "web", "u", "2026-10-08", [], 30)])


class FakeHF:
    def __init__(self):
        self.calls = []

    def subscribe(self, application, arguments):
        self.calls.append((application, arguments))
        return {"images": [{"url": "https://cdn.example/img1.png"}]}


def job(**kw):
    d = dict(idea_id="i1", kind="image", prompt="warm living room at night, snow outside the window, no people",
             purpose="background for a New Year story", est_credits=2.0)
    d.update(kw)
    return H.Job(**d)


def test_real_product_in_prompt_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(H, "models", lambda: {"image": "some/app"})
    fake = FakeHF()
    r = H.run(job(prompt="a Casio PX-770 piano in a cozy room"), LG, tmp_path / "log.jsonl", 100, client=fake)
    assert r["status"] == "refused" and not fake.calls
    r = H.run(job(depicts_real_product=True), LG, tmp_path / "log.jsonl", 100, client=fake)
    assert r["status"] == "refused"


def test_generic_words_from_product_names_are_not_blocked(tmp_path, monkeypatch):
    monkeypatch.setattr(H, "models", lambda: {"image": "some/app"})
    assert not H.r5_problems(job(prompt="cream-coloured retro wallpaper, soft light"), LG)


def test_no_key_or_budget_means_dry_run(tmp_path, monkeypatch):
    monkeypatch.delenv("HF_KEY", raising=False)
    monkeypatch.delenv("HF_API_KEY", raising=False)
    monkeypatch.setattr(H, "models", lambda: {"image": "some/app"})
    r = H.run(job(), LG, tmp_path / "log.jsonl", 100)
    assert r["status"] == "planned" and any("SDK key" in x for x in r["reasons"])
    fake = FakeHF()
    r = H.run(job(), LG, tmp_path / "log.jsonl", None, client=fake)            # key-equivalent but no budget
    assert r["status"] == "planned" and not fake.calls and any("budget" in x for x in r["reasons"])


def test_runs_within_budget_and_stops_at_the_cap(tmp_path, monkeypatch):
    monkeypatch.setattr(H, "models", lambda: {"image": "some/app"})
    monkeypatch.delenv("HF_MONTHLY_CREDITS", raising=False)
    fake, log = FakeHF(), tmp_path / "log.jsonl"
    r1 = H.run(job(est_credits=6), LG, log, 10, client=fake)
    assert r1["status"] == "done" and r1["urls"] == ["https://cdn.example/img1.png"]
    r2 = H.run(job(est_credits=6), LG, log, 10, client=fake)                  # 6 spent, 4 left
    assert r2["status"] == "planned" and len(fake.calls) == 1
    assert [json.loads(x)["status"] for x in log.read_text().splitlines()] == ["done", "planned"]


def test_failure_is_logged_not_raised(tmp_path, monkeypatch):
    monkeypatch.setattr(H, "models", lambda: {"image": "some/app"})

    class Broke:
        def subscribe(self, application, arguments):
            raise RuntimeError("InsufficientCredits")
    r = H.run(job(), LG, tmp_path / "log.jsonl", 100, client=Broke())
    assert r["status"] == "failed" and "InsufficientCredits" in r["error"]
