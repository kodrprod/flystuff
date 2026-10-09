"""Higgsfield adapter: the agent's AI image/video generation, with the three guards the business needs.

  1. Money: nothing is spent without a credit budget (HF_MONTHLY_CREDITS or the client profile) and an SDK key
     (HF_KEY, or HF_API_KEY + HF_API_SECRET). Without them every job is a DRY RUN: the job is written to disk with
     its prompt and purpose and the call stops there.
  2. Truth (rule R5): AI never depicts the client's real product, staff, customers or store as real. A job whose
     prompt names a product from the facts ledger, or that is flagged as showing the real product, is refused.
  3. Audit: every job (planned, run, refused, failed) is appended to a JSONL log with its result URLs.

Which Higgsfield application (model) to call is configuration, not code: knowledge/higgsfield_models.json maps a
job kind ("image", "video_from_image", ...) to an application id. Fill it once from the Higgsfield dashboard/docs
when the key exists; until then jobs are planned with application=None.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .facts import Ledger

ROOT = Path(__file__).resolve().parent.parent
MODELS_FILE = ROOT / "knowledge" / "higgsfield_models.json"


@dataclass
class Job:
    idea_id: str
    kind: str                                   # image | video_from_image | video_from_text | edit
    prompt: str
    purpose: str                                # why the video needs it (b-roll metaphor, background, ...)
    inputs: dict = field(default_factory=dict)  # e.g. {"image_url": ...}
    depicts_real_product: bool = False          # must stay False (R5)
    est_credits: float | None = None


def has_key() -> bool:
    return bool(os.environ.get("HF_KEY") or (os.environ.get("HF_API_KEY") and os.environ.get("HF_API_SECRET")))


def product_names(ledger: Ledger) -> list[str]:
    """Brands and model codes of the client's real products: "Бренд: Casio" in spec facts, and tokens with both
    letters and digits (PX-770, AS-100BK) in product facts. Generic words ("Cream", "Retro") are not included."""
    names = set()
    for f in ledger.facts.values():
        for b in re.findall(r"Бренд:\s*([^;]+)", f.text):
            names.add(b.strip().lower())
        m = re.match(r"^(.*?)\s+—\s+[\d\s]+₸", f.text)
        if m:
            names.update(w.lower() for w in m.group(1).split()
                         if re.search(r"[A-Za-z]", w) and re.search(r"\d", w) and len(w) >= 4)
    return sorted(n for n in names if n)


def r5_problems(job: Job, ledger: Ledger) -> list[str]:
    out = []
    if job.depicts_real_product:
        out.append("R5: the job is flagged as showing the client's real product; film it instead")
    low = job.prompt.lower()
    hits = [n for n in product_names(ledger) if n in low]
    if hits:
        out.append(f"R5: prompt names real products {hits}; AI must not depict them as real")
    if re.search(r"\b(наш|our)\s+(магазин|store|shop|staff|продавец|сотрудник)", low):
        out.append("R5: prompt depicts the client's own store or staff")
    return out


class Budget:
    """Credits spent this calendar month, from the job log."""

    def __init__(self, log: Path, monthly_cap: float | None):
        self.log, self.cap = log, monthly_cap

    def spent(self, month: str | None = None) -> float:
        month = month or time.strftime("%Y-%m", time.gmtime())
        tot = 0.0
        if self.log.exists():
            for line in self.log.read_text(encoding="utf-8").splitlines():
                r = json.loads(line)
                if r.get("status") == "done" and r.get("at", "").startswith(month):
                    tot += float(r.get("credits") or r.get("est_credits") or 0)
        return tot

    def allows(self, est: float | None) -> tuple[bool, str]:
        if self.cap is None:
            return False, "no credit budget approved (HF_MONTHLY_CREDITS / profile.higgsfield_monthly_credits)"
        if est is None:
            return False, "no credit estimate for this job; quote it first"
        left = self.cap - self.spent()
        return (est <= left, f"estimate {est} vs {left:.0f} credits left this month")


def models() -> dict:
    return json.loads(MODELS_FILE.read_text(encoding="utf-8")) if MODELS_FILE.exists() else {}


def run(job: Job, ledger: Ledger, log: Path, monthly_cap: float | None = None, dry_run: bool | None = None,
        client=None) -> dict:
    """Plan or execute one generation. Returns the log record. `client` is injectable for tests
    (anything with .subscribe(application, arguments))."""
    cap = monthly_cap if monthly_cap is not None else (float(os.environ["HF_MONTHLY_CREDITS"])
                                                       if os.environ.get("HF_MONTHLY_CREDITS") else None)
    rec = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **asdict(job)}
    app = models().get(job.kind)
    rec["application"] = app
    probs = r5_problems(job, ledger)
    log.parent.mkdir(parents=True, exist_ok=True)

    def done(status: str, **kw) -> dict:
        rec.update(status=status, **kw)
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

    if probs:
        return done("refused", reasons=probs)
    ok, why = Budget(log, cap).allows(job.est_credits)
    live = (client is not None or has_key()) and app and ok
    if dry_run or not live:
        reasons = [r for r, bad in (("dry_run requested", dry_run), ("no SDK key", client is None and not has_key()),
                                    (f"no application configured for kind {job.kind!r}", not app), (why, not ok)) if bad]
        return done("planned", reasons=reasons)
    if client is None:
        import higgsfield_client as client                     # noqa: N813  (module exposes subscribe())
    args = {"prompt": job.prompt, **job.inputs}
    try:
        res = client.subscribe(app, arguments=args)
    except Exception as e:                                     # InsufficientCreditsError, HTTP errors, NSFW ...
        return done("failed", error=f"{type(e).__name__}: {e}"[:400])
    urls = sorted(set(re.findall(r"https?://[^\s\"']+", json.dumps(res))))
    return done("done", result=res, urls=urls, credits=job.est_credits)
