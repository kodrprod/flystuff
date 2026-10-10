"""The marketing brain: any client, any boss request -> a campaign that can be executed and measured.

    request + client folder
      1 intake      the request as a business objective, a marketing objective, ONE success metric, constraints
      2 inputs      what is already in hand (code inventories the folder) vs what is missing and how to get it
      3 insights    evidence base (every item cites a fact id or file) -> ranked insights (tensions, moments, proof)
      4 ideas       many diverse short-video ideas from insights x drivers x formats, each scored on a rubric
      5 selection   CODE, not the model: rubric prior + audience data + diversity -> the test slate
      6 campaign    the plan around the slate: big idea, roles, offer (needs approval), calendar, worker asks,
                    measurement and decision rules
      7 critique    the boss and a veteran creator attack it; one revision fixes fatal/major points

Judgment (1-4, 6, 7) is done by the model following the method in brain/METHOD.md, which is a document the
agent reads, not code. Code does only what code is better at:
  * assembling the inputs from the client folder (facts ledger, research files, past metrics, learnings),
  * validating every step against its schema,
  * truth: every audience-facing string is checked against the facts ledger (numbers, claims, contacts);
    a string that needs an unconfirmed fact becomes a question to the owner, never a guess,
  * feasibility: worker minutes are recomputed from the shot list with the shoot-card model and the week is cut to
    the real budget,
  * selection and exploration: experiment 002 showed nobody predicts short-form winners from text (rho 0.07 for
    retail), so the model's scores are only a PRIOR; audience data and diversity decide what is tested.
"""
from __future__ import annotations

import json
import os
import re
import time
from datetime import date, datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path

from . import acquire, shootcard
from .attribution import make_code
from .checks import check_hook, check_text
from .facts import Ledger
from .llm import LLM

ROOT = Path(__file__).resolve().parent.parent
METHOD_PATH = ROOT / "brain" / "METHOD.md"
KNOWLEDGE = ROOT / "knowledge"
INPUT_DIRS = ("research", "inputs", "metrics", "uploads")     # what the client/owner gave us; never our own outputs

# ----------------------------------------------------------------- schemas (one per judgment step)


def obj(props: dict, required: list[str] | None = None) -> dict:
    return {"type": "object", "properties": props, "required": required if required is not None else list(props),
            "additionalProperties": False}


S, N, I, B = {"type": "string"}, {"type": "number"}, {"type": "integer"}, {"type": "boolean"}


def arr(items: dict, **kw) -> dict:
    return {"type": "array", "items": items, **kw}


REQUEST_TYPES = ["sales_push", "launch_or_event", "awareness_or_viral", "reputation_or_trust", "price_pressure",
                 "retention_or_loyalty", "hiring", "b2b_leads", "should_we_do_social", "other"]

INTAKE_SCHEMA = obj({
    "request_type": {"type": "string", "enum": REQUEST_TYPES},
    "reframed_request": S,
    "business_objective": S,
    "marketing_objective": S,
    "success_metric": obj({"name": S, "how_measured": S, "target": S, "by_when": S}),
    "leading_indicators": arr(S),
    "constraints": arr(S),
    "assumptions": arr(S),
    "clarifying_questions": arr(S, maxItems=3),
    "push_back": S,                       # where the request itself is wrong / unrealistic, said plainly ("" if none)
})

INPUTS_SCHEMA = obj({
    "have": arr(obj({"input": S, "what_it_gives": S})),
    "missing": arr(obj({"input": S, "why_it_matters": S, "how": S, "who": {"type": "string", "enum": ["agent", "owner", "staff", "customer"]},
                        "owner_minutes": N, "fallback_if_missing": S, "blocks_step": S})),
})

INSIGHTS_SCHEMA = obj({
    "evidence": arr(obj({"id": S, "kind": {"type": "string", "enum": [
        "fact", "customer_language", "behaviour", "proof_asset", "moment", "constraint", "market", "performance"]},
        "claim": S, "source": S, "confidence": {"type": "string", "enum": ["verified", "likely", "assumption"]}})),
    "insights": arr(obj({"id": S, "insight": S, "tension": S, "evidence_ids": arr(S), "who_feels_it": S,
                         "content_reality": S, "strength": I})),
})

def engine_key(idea: dict) -> str:
    """Categorical engine (the `format` slug) for diversity and experiment arms. If a model ever returns prose
    ('E09 blind test ...'), the first token is used, so free text cannot make every idea look unique."""
    v = (idea.get("format") or "?").strip()
    m = re.match(r"([A-Za-z]{1,3}\d{1,3})\b", v)
    return (m.group(1) if m else (v.split() or ["?"])[0]).lower().strip(".,:;")[:32]


RUBRIC = ["stop", "truth", "share_save", "comment", "producible", "brand_link", "objective_fit"]
RUBRIC_HELP = {
    "stop": "would a stranger stop in the first second (first frame + first words)?",
    "truth": "rooted in a verified insight/fact, nothing invented",
    "share_save": "would someone send it to a friend or save it (practical value, identity, emotion, story)?",
    "comment": "does it invite a real comment (opinion, experience, choice), not bait?",
    "producible": "one weak phone, sound only close-up, staff minutes + AI, no credits risk",
    "brand_link": "could ONLY this business have made it?",
    "objective_fit": "does it move the success metric, not just views?",
}

IDEA = obj({
    "id": S, "title": S, "insight_ids": arr(S),
    "driver": S, "format": S, "funnel": {"type": "string", "enum": [
        "attention", "consideration", "conversion", "trust", "retention", "recruiting"]},
    "hook_ru": S, "first_frame": S, "on_screen_ru": arr(S), "what_happens": S, "why_stop": S, "why_share_or_save": S,
    "comment_prompt_ru": S, "cta_ru": S,
    "production": obj({"mode": {"type": "string", "enum": ["worker", "ai", "mixed", "ugc", "screen"]},
                       "worker_shots": arr(obj({"what_ru": S, "location": S, "seconds": I, "takes": I, "say_ru": S,
                                                "kind": {"type": "string", "enum": ["hook", "demo", "talk", "detail", "process"]}})),
                       "ai_parts": S, "people_on_camera": I}),
    "facts_used": arr(S),
    "kpi": S,
    "risks": arr(S),
    "rubric": obj({k: I for k in RUBRIC}),
})
IDEAS_SCHEMA = obj({"ideas": arr(IDEA, minItems=8)})


def method_vocab(method: str) -> dict[str, list[str]]:
    """The categorical vocabulary the method defines: the first column of the table under the heading that says
    "the `driver` field uses these exact slugs" (and the same for `format`). The method document is the single
    source of truth, so a revised method cannot drift from the code's arms. Empty list = not found (free text)."""
    out = {}
    for field in ("driver", "format"):
        m = re.search(r"^#{2,4} .*`%s` field[^\n]*\n(.*?)(?=^#{2,4} )" % field, method, re.M | re.S)
        table = re.search(r"((?:^\|.*\n?)+)", m.group(1), re.M) if m else None     # first table only
        slugs = re.findall(r"^\|\s*([a-z][a-z0-9_]+)\s*\|", table.group(1), re.M) if table else []
        out[field] = [x for x in dict.fromkeys(slugs) if x not in (field, "behaviour", "insight")]
    return out


def ideas_schema(vocab: dict[str, list[str]] | None = None) -> dict:
    """IDEAS_SCHEMA with driver/format restricted to the method's slugs when the method defines them."""
    if not vocab or not (vocab.get("driver") or vocab.get("format")):
        return IDEAS_SCHEMA
    idea = json.loads(json.dumps(IDEA))
    for f in ("driver", "format"):
        if vocab.get(f):
            idea["properties"][f] = {"type": "string", "enum": vocab[f]}
    return obj({"ideas": arr(idea, minItems=8)})

CAMPAIGN_SCHEMA = obj({
    "name": S, "big_idea": S, "single_minded_message_ru": S, "why_this_wins": S,
    "series": arr(obj({"name": S, "role": S, "idea_ids": arr(S), "cadence": S})),
    "offer": obj({"needed": B, "proposal": S, "fact_ids": arr(S), "needs_owner_approval": B}),
    "channels": arr(obj({"channel": S, "role": S})),
    "weeks": arr(obj({"week": I, "goal": S, "idea_ids": arr(S), "worker_ask_ru": S, "ai_work": S})),
    "measurement": obj({"success_metric": S, "attribution": S, "leading_indicators": arr(S), "review_cadence": S}),
    "decision_rules": arr(S),
    "learning_questions": arr(S),
    "owner_asks": arr(obj({"ask": S, "why": S, "minutes": N})),
    "risks": arr(S),
})

PATCH_FIELDS = ("hook_ru", "first_frame", "on_screen_ru", "what_happens", "cta_ru", "comment_prompt_ru", "facts_used", "risks")
REVISION_SCHEMA = json.loads(json.dumps(CAMPAIGN_SCHEMA))
REVISION_SCHEMA["properties"]["idea_patches"] = arr(obj(
    {"id": S, "drop": B, **{k: (arr(S) if k in ("on_screen_ru", "facts_used", "risks") else S) for k in PATCH_FIELDS},
     "worker_shots": IDEA["properties"]["production"]["properties"]["worker_shots"]}, required=["id"]))
REVISION_SCHEMA["required"] = list(REVISION_SCHEMA["required"]) + ["idea_patches"]

REVIEW_SCHEMA = obj({
    "persona": S, "score": I, "would_approve": B, "best_idea": S,
    "refutations": arr(obj({"target": S, "why_fails": S, "severity": {"type": "string", "enum": ["fatal", "major", "minor"]},
                            "fix": S})),
})

# ----------------------------------------------------------------- inputs (code)


@dataclass
class Client:
    slug: str
    dir: Path
    profile: dict
    ledger: Ledger

    @classmethod
    def load(cls, slug: str, base: Path | None = None) -> "Client":
        d = (base or Path(os.environ.get("SMM_CLIENTS_DIR") or ROOT / "clients")) / slug
        if not d.is_dir():
            raise FileNotFoundError(f"no client folder {d}")
        prof = json.loads((d / "profile.json").read_text(encoding="utf-8")) if (d / "profile.json").exists() else {"name": slug}
        led = Ledger.load(d / "facts.jsonl") if (d / "facts.jsonl").exists() else Ledger()
        return cls(slug, d, prof, led)


def _preview(p: Path, max_chars: int = 700) -> str:
    """Shape of a research file so the model knows what is there; it can Read the file for detail."""
    try:
        if p.suffix == ".json":
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, list):
                head = json.dumps(data[:2], ensure_ascii=False)[:max_chars]
                return f"list of {len(data)} records; first: {head}"
            if isinstance(data, dict):
                keys = ", ".join(f"{k}({type(v).__name__}{'[' + str(len(v)) + ']' if isinstance(v, (list, dict)) else ''})"
                                 for k, v in list(data.items())[:25])
                return f"object with keys: {keys}"[:max_chars]
        return p.read_text(encoding="utf-8", errors="replace")[:max_chars]
    except (ValueError, OSError) as e:
        return f"(unreadable: {e})"


def inventory(client: Client, now=None) -> dict:
    """Everything the agent already has for this client, without asking anyone."""
    usable = list(client.ledger.usable(now).values())
    probs = client.ledger.report(now)
    files = []
    for sub in INPUT_DIRS:
        for p in sorted((client.dir / sub).rglob("*")) if (client.dir / sub).is_dir() else []:
            if p.is_file() and p.suffix in (".json", ".jsonl", ".csv", ".md", ".txt") and p.stat().st_size < 50_000_000:
                files.append({"path": str(p), "bytes": p.stat().st_size, "preview": _preview(p)})
    learn = []
    lf = KNOWLEDGE / "learnings.jsonl"
    if lf.exists():
        vert = (client.profile.get("vertical") or "").lower()
        for line in lf.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                if not vert or r.get("vertical", "").lower() in (vert, "any"):
                    learn.append(r)
    return {
        "profile": client.profile,
        "facts_usable": [{"id": f.id, "text": f.text, "provenance": f.provenance, "source": f.source,
                          "as_of": f.fetched_at} for f in usable],
        "facts_not_usable": [{"id": i, "why": p} for i, p in probs.items()][:40],
        "files": files,
        "learnings": learn[-60:],
    }


# ----------------------------------------------------------------- deterministic checks


def worker_shots(idea: dict, prefix: str) -> list[shootcard.Shot]:
    out = []
    for j, s in enumerate(idea.get("production", {}).get("worker_shots") or []):
        out.append(shootcard.Shot(f"{prefix}_{j}", s.get("what_ru", ""), s.get("location") or "магазин",
                                  max(1, int(s.get("seconds") or 1)), s.get("kind") or "demo",
                                  max(1, int(s.get("takes") or 2)), s.get("say_ru") or ""))
    return out


def idea_minutes(idea: dict) -> float:
    """Marginal minutes this idea costs the staff (the shoot-card model; fixed card time is shared)."""
    shots = worker_shots(idea, "x")
    if not shots:
        return 0.0
    return shootcard.session_minutes(shots) - shootcard.FIXED_MIN


def audience_strings(idea: dict) -> list[tuple[str, str]]:
    out = [("hook_ru", idea.get("hook_ru", "")), ("cta_ru", idea.get("cta_ru", "")),
           ("comment_prompt_ru", idea.get("comment_prompt_ru", ""))]
    out += [(f"on_screen_ru[{i}]", s) for i, s in enumerate(idea.get("on_screen_ru") or [])]
    out += [(f"say_ru[{i}]", s.get("say_ru", "")) for i, s in enumerate(idea.get("production", {}).get("worker_shots") or [])]
    return [(k, v) for k, v in out if v]


def check_idea(idea: dict, ledger: Ledger, insight_ids: set[str], now=None) -> dict:
    """Returns {'errors': [...], 'needs_facts': [...], 'warnings': [...]} for one idea."""
    errs, needs, warns = [], [], []
    for k, txt in audience_strings(idea):
        for v in check_text(txt, ledger, where=f"{idea['id']}.{k}", now=now):
            if v.rule.startswith("R6"):
                needs.append(f"{v.where}: {v.message}")          # becomes an owner question, not a silent edit
            elif v.severity == "error":
                errs.append(f"{v.where}: {v.rule} {v.message}")
            else:
                warns.append(f"{v.where}: {v.rule} {v.message}")
    for v in check_hook(idea.get("hook_ru", "")):
        (errs if v.severity == "error" else warns).append(f"{idea['id']}.hook: {v.rule} {v.message}")
    missing = [i for i in idea.get("insight_ids") or [] if i not in insight_ids]
    if missing:
        errs.append(f"{idea['id']}: cites unknown insights {missing}")
    if not idea.get("insight_ids"):
        errs.append(f"{idea['id']}: not rooted in any insight")
    m = idea_minutes(idea)
    if m > 17:
        errs.append(f"{idea['id']}: needs {m:.1f} staff minutes alone (budget 20/week incl. setup)")
    mode = idea.get("production", {}).get("mode")
    if mode in ("worker", "mixed") and not idea.get("production", {}).get("worker_shots"):
        errs.append(f"{idea['id']}: mode {mode} but no worker shots")
    for k in RUBRIC:
        val = idea.get("rubric", {}).get(k)
        if not isinstance(val, int) or not 1 <= val <= 5:
            errs.append(f"{idea['id']}: rubric.{k} must be 1-5")
    return {"errors": errs, "needs_facts": needs, "warnings": warns}


def source_is_real(src: str, ledger: Ledger, files: set[str]) -> bool:
    """`fact:<id>` in the ledger, `file:<path>[#locator]` among the files the agent was given, a URL, or the
    request/profile itself. A bare fact id or path is accepted too."""
    s = (src or "").strip()
    low = s.lower()
    if low.startswith(("http://", "https://", "request", "profile", "intake")):
        return True
    if low.startswith("fact:"):
        return s[5:].strip() in ledger.facts
    if low.startswith("file:"):
        s = s[5:].strip()
    path = s.split("#", 1)[0].strip()
    return s in ledger.facts or any(path and (f == path or f.endswith("/" + path.lstrip("./")) or path.endswith(f))
                                    for f in files)


def check_insights(ins: dict, ledger: Ledger, files: set[str]) -> list[str]:
    """Every evidence item must point at something real (see source_is_real) or be labelled an assumption."""
    out = []
    ev_ids = {e["id"] for e in ins["evidence"]}
    for e in ins["evidence"]:
        src = e.get("source", "")
        if e.get("confidence") != "assumption" and not src.lower().startswith("assumption") \
                and not source_is_real(src, ledger, files):
            out.append(f"evidence {e['id']}: source {src!r} is not a fact id, file or URL; label it an assumption")
    for i in ins["insights"]:
        bad = [x for x in i.get("evidence_ids") or [] if x not in ev_ids]
        if bad or not i.get("evidence_ids"):
            out.append(f"insight {i['id']}: evidence {bad or 'none'} not in the evidence base")
    return out


# ----------------------------------------------------------------- selection (code: prior + data + diversity)


def load_weights() -> dict[str, float]:
    f = KNOWLEDGE / "rubric_weights.json"
    if f.exists():
        return {k: float(v) for k, v in json.loads(f.read_text(encoding="utf-8")).items() if not k.startswith("_")}
    return {"stop": 1.5, "truth": 1.0, "share_save": 1.3, "comment": 0.8, "producible": 1.0, "brand_link": 0.8,
            "objective_fit": 1.4}


def prior_score(idea: dict, weights: dict[str, float]) -> float:
    r = idea.get("rubric", {})
    tot = sum(weights.values())
    return round(sum(weights[k] * r.get(k, 1) for k in weights) / tot, 3)


def data_bonus(idea: dict, arm_stats: dict[str, dict] | None) -> float:
    """Audience data beats the prior: posterior mean (log-relative views) of the idea's driver/format arm,
    shrunk by its uncertainty. 0 without data."""
    if not arm_stats:
        return 0.0
    b = 0.0
    for key in (f"driver:{idea.get('driver', '').lower()}", f"engine:{engine_key(idea)}"):
        st = arm_stats.get(key)
        if st and st.get("n", 0) > 0:
            b += st["mean"] / (1 + st["sd"])
    return b


def select(ideas: list[dict], k: int, weights: dict[str, float], arm_stats: dict | None = None,
           explore_share: float = 0.25, blocked: set[str] = frozenset()) -> list[dict]:
    """Greedy max-marginal-relevance slate: high prior, but each repeat of a driver/format/mode costs, and about
    a quarter of the slots go to the most *different* remaining ideas (exploration), because the prior is weak."""
    pool = [i for i in ideas if i["id"] not in blocked]
    for i in pool:
        i["_prior"] = prior_score(i, weights)
        i["_value"] = i["_prior"] + data_bonus(i, arm_stats)
    chosen: list[dict] = []
    n_explore = max(1, round(k * explore_share)) if k >= 4 else 0
    while pool and len(chosen) < k - n_explore:
        def mmr(i):
            rep = sum((c.get("driver") == i.get("driver")) * 0.6 + (engine_key(c) == engine_key(i)) * 0.5 +
                      (c["production"]["mode"] == i["production"]["mode"]) * 0.15 for c in chosen)
            return i["_value"] - rep
        best = max(pool, key=mmr)
        best["_why"] = "prior+data"
        chosen.append(best)
        pool.remove(best)
    while pool and len(chosen) < k:                           # exploration: maximise novelty, prior as tie-break
        def novelty(i):
            return (int(i.get("driver") not in {c.get("driver") for c in chosen}) * 2
                    + int(engine_key(i) not in {engine_key(c) for c in chosen}), i["_prior"])
        best = max(pool, key=novelty)
        best["_why"] = "explore"
        chosen.append(best)
        pool.remove(best)
    return chosen


def plan_week(chosen: list[dict], capacity_min: float = 20.0) -> tuple[list[str], list[shootcard.Shot], float]:
    """Which selected ideas get real footage this week, within the staff budget (exact optimiser)."""
    shots, videos = [], []
    for i in chosen:
        ws = worker_shots(i, i["id"])
        if ws:
            shots += ws
            videos.append(shootcard.Video(i["id"], i.get("_value", 1.0), [s.id for s in ws]))
    if not videos:
        return [], [], 0.0
    vids, sh, mins = shootcard.plan(videos, shots, capacity_min)
    return [v.id for v in vids], sh, mins


# ----------------------------------------------------------------- the owner card (code)

OWNER_MINUTES_CAP = 15          # onboarding batch; later weeks <= 5 (method L5)
MIN_WEEK1 = 2                   # at least this many ready (fact-complete) ideas are filmed/published in week 1
OWNER_MAX_ITEMS = 7             # stress test: owners answered 2 of 8+ asks; a card longer than this is not read
MIN_ITEM_MINUTES = 1.0          # reading and answering anything costs at least a minute, whatever the model claims


def owner_card(questions: list[dict], minutes_cap: float = OWNER_MINUTES_CAP) -> tuple[list[dict], list[dict]]:
    """One message the owner can answer in <= minutes_cap minutes: clarifying questions first (they change the plan),
    then the other asks in the order the brain ranked them (value per owner minute) while minutes fit, then ONE item
    listing the facts to confirm. Everything else is deferred, not dropped. Returns (card, deferred)."""
    seen, uniq = set(), []
    for q in questions:
        k = " ".join(q["q"].lower().split())[:120]
        if k not in seen:
            seen.add(k)
            uniq.append(q)
    intake = [q for q in uniq if q.get("from") == "intake"]
    clar, extra_clar = intake[:3], intake[3:]                       # method A8: at most 3 clarifying questions
    facts = [q for q in uniq if q.get("from") == "facts"]
    rest = [q for q in uniq if q.get("from") not in ("intake", "facts")]
    card, deferred, used = list(clar), list(extra_clar), 1.0 * len(clar)
    budget = minutes_cap - (2.0 if facts else 0.0)                  # the facts item below costs ~2 minutes
    slots = OWNER_MAX_ITEMS - len(clar) - (1 if facts else 0)
    for q in rest:
        m = q.get("minutes")
        m = max(MIN_ITEM_MINUTES, float(m) if isinstance(m, (int, float)) else 2.0)
        if used + m <= budget and slots > 0:
            slots -= 1
            card.append(q)
            used += m
        else:
            deferred.append(q)
    if facts:
        shown = facts[:6]
        card.append({"from": "facts", "minutes": 2.0, "q": "Подтвердите или поправьте, пожалуйста, факты для роликов:\n" +
                     "\n".join("   — " + f["q"].split(": ", 1)[-1] for f in shown) +
                     (f"\n   (и ещё {len(facts) - 6} — пришлю после ответа)" if len(facts) > 6 else "")})
        deferred += facts[6:]
    return card, deferred


# ----------------------------------------------------------------- final deliverables (code)


def method_section(method: str, code: str) -> str:
    """The text of one method section by its code (e.g. 'F13'), so a step gets the rules it is judged by."""
    m = re.search(r"^(#{2,4}) %s\b.*?(?=^#{2,4} |\Z)" % re.escape(code), method, re.M | re.S)
    return m.group(0).strip() if m else ""


def week1_of(camp: dict) -> list[str]:
    weeks = camp.get("weeks") or []
    w1 = [w for w in weeks if w.get("week") == 1] or ([min(weeks, key=lambda w: w.get("week", 99))] if weeks else [])
    return list(dict.fromkeys(x for w in w1 for x in w.get("idea_ids") or []))


def approval_gate(review: dict) -> dict:
    """Method F13: approval needs score >= 7 and no fatal point. Code decides, not the reviewer's own flag."""
    review = json.loads(json.dumps(review))          # never mutate the model/tape output
    review["model_would_approve"] = review.get("would_approve")
    review["would_approve"] = bool(review.get("score", 0) >= 7 and
                                   not any(r.get("severity") == "fatal" for r in review.get("refutations") or []))
    return review


def apply_patches(ideas: list[dict], patches: list[dict], ledger: Ledger, now=None) -> dict:
    """The revision's idea-level fixes are applied to the ideas themselves, so the copy staff film and the editor burns
    in is the revised one (stress test: every case shipped pre-revision copy). Patched ideas are re-checked by the caller."""
    byid = {i["id"]: i for i in ideas}
    done = {"patched": [], "dropped": [], "unknown": []}
    for pt in patches or []:
        idea = byid.get(pt.get("id"))
        if idea is None:
            done["unknown"].append(pt.get("id"))
            continue
        if pt.get("drop"):
            idea["_dropped"] = True
            done["dropped"].append(idea["id"])
            continue
        for k in PATCH_FIELDS:
            if k in pt:
                idea[k] = pt[k]
        if "worker_shots" in pt:
            idea.setdefault("production", {})["worker_shots"] = pt["worker_shots"]
        done["patched"].append(idea["id"])
    return done


def declared_needs(idea: dict) -> list[str]:
    """'NEEDS FACT: ...' the model itself wrote in risks (method C6.2). Facts the agent can fetch itself are tagged
    '(agent ...)' and are not owner questions."""
    out = []
    for r in idea.get("risks") or []:
        if r.strip().upper().startswith("NEEDS FACT") and "(agent" not in r.lower():
            out.append(r.split(":", 1)[-1].strip())
    return out


def latin_share(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    return sum(c.isascii() for c in letters) / len(letters) if letters else 0.0


def has_past_date(text: str, today: str) -> bool:
    t = date.fromisoformat(today)
    for d, m, y in re.findall(r"\b(\d{1,2})\.(\d{1,2})(?:\.(\d{2,4}))?\b", text):
        try:
            yy = int(y) + (2000 if y and len(y) == 2 else 0) if y else t.year
            if date(yy, int(m), int(d)) < t:
                return True
        except ValueError:
            continue
    return False


def fact_question_ru(violation: str, hook: str) -> str | None:
    """A truth-rail hit becomes a plain Russian question for the owner; rail messages are never sent verbatim."""
    m = re.search(r"'([^']+)'", violation)
    x = m.group(1) if m else ""
    if "R6-NUM" in violation or "number" in violation:
        return f"Верна ли цифра «{x}» для ролика «{hook}»? Если да — откуда она (прайс, сайт, ваш учёт)?"
    if "R6-SCARCITY" in violation or "scarcity" in violation:
        return f"Есть ли подтверждённый срок или остаток для «{x}» (ролик «{hook}»)? Без него фразу уберём."
    if "R6-CLAIM" in violation or "claim" in violation:
        return f"Можно ли в ролике «{hook}» утверждать «{x}» и чем это подтверждается? Без подтверждения уберём."
    if "R6-CONTACT" in violation or "contact" in violation:
        return f"Верен ли контакт «{x}» для ролика «{hook}»?"
    return None


def assign_codes(client_dir: Path, ids: list[str], preview: bool = False) -> dict[str, str]:
    """One WhatsApp code per idea that will be published, from a per-client campaign counter, so codes never repeat
    across runs (stress test: every run reused the same codes)."""
    f = client_dir / "codes.json"
    st = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"campaigns": 0, "issued": {}}
    idx = st["campaigns"] + 1
    codes = {iid: make_code(idx, n + 1) for n, iid in enumerate(ids)}
    if not preview and ids:
        st["campaigns"] = idx
        for iid, c in codes.items():
            st["issued"][c] = {"idea": iid, "campaign": idx, "at": time.strftime("%Y-%m-%d", time.gmtime())}
        f.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    return codes


def deliverables(client: Client, camp: dict, ideas: list[dict], blocked: set, gated: set, slate_ids: list[str],
                 capacity_min: float, today: str, codes_preview: bool = False) -> dict:
    """Everything a human receives, built from ONE source of truth: the campaign's week-1 filming set and owner asks,
    over the (patched, re-checked) ideas. Used for the review preview and, after the revision, for the final files."""
    byid = {i["id"]: i for i in ideas}
    want, problems = week1_of(camp), []
    if not want:
        want = [x for x in slate_ids if x not in blocked]
        problems.append("campaign named no week-1 ideas; the code slate is used")
    for x in want:
        if x not in byid:
            problems.append(f"week 1 names unknown idea {x}")
        elif x in blocked:
            problems.append(f"week 1 idea {x} is blocked (failed checks or dropped by the revision)")
        elif x in gated:
            problems.append(f"week 1 idea {x} waits for owner facts and is not filmed until they are confirmed")
    film = [byid[x] for x in want if x in byid and x not in blocked and x not in gated]
    if len(film) < MIN_WEEK1:
        # stress test: when every planned idea waits for facts, week 1 was empty. Fill it with the best ideas that
        # need no unconfirmed fact (reserves), so the staff still film something true this week.
        w = load_weights()
        reserves = sorted((i for i in ideas if i["id"] not in blocked and i["id"] not in gated and not i.get("_dropped")
                           and i["id"] not in {f["id"] for f in film}), key=lambda i: -prior_score(i, w))
        add = reserves[:MIN_WEEK1 - len(film)]
        film += add
        if add:
            problems.append(f"week 1 had {len(film) - len(add)} ready ideas; reserves added: {[i['id'] for i in add]}")
    for f in film:
        f.setdefault("_value", prior_score(f, load_weights()))
    filmed_ids, shots, minutes = plan_week(film, capacity_min)
    for f in film:
        if worker_shots(f, f["id"]) and f["id"] not in filmed_ids:
            problems.append(f"week 1 idea {f['id']} does not fit the staff minutes and moves to week 2")
    week1 = [f["id"] for f in film if f["id"] in filmed_ids or not worker_shots(f, f["id"])]
    publish_ids = week1 + [x for x in slate_ids if x not in week1 and x not in blocked]
    codes = assign_codes(client.dir, publish_ids, preview=codes_preview)
    if not codes_preview:
        for iid, code in codes.items():
            i = byid[iid]
            for k in ("cta_ru", "comment_prompt_ru"):
                i[k] = (i.get(k) or "").replace("{CODE}", code)
            i["on_screen_ru"] = [t.replace("{CODE}", code) for t in i.get("on_screen_ru") or []]
    consent = any((byid[x].get("production") or {}).get("people_on_camera", 0) for x in week1)
    card = shootcard.render_card_ru("1", shots, minutes, capacity_min, business=client.profile.get("name", ""),
                                    extra_tips=client.profile.get("card_tips_ru"), consent=consent) if shots else \
        "Это ИИ-ассистент MetaPrompt. На этой неделе съёмка не нужна."
    manifest = [dict(m, idea_id=m["shot_id"].rsplit("_", 1)[0]) for m in shootcard.manifest(shots)]

    # owner message: the final campaign's asks are the source; facts only for ideas we intend to publish
    items = [{"from": "campaign", "q": a["ask"], "why": a.get("why", ""), "minutes": a.get("minutes")}
             for a in camp.get("owner_asks") or []]
    for x in [*want, *publish_ids]:
        if x in byid and x not in blocked:
            idea = byid[x]
            for v in check_idea(idea, client.ledger, {i for i in [*(idea.get("insight_ids") or [])]}, None)["needs_facts"]:
                q = fact_question_ru(v, idea.get("hook_ru", ""))
                if q:
                    items.append({"from": "facts", "q": f"{x}: {q}"})
            for need in declared_needs(idea):
                if latin_share(need) > 0.2:          # the model wrote the fact in English: never shown to the owner
                    problems.append(f"{x}: NEEDS FACT not in Russian, kept internal: {need[:80]}")
                    continue
                items.append({"from": "facts", "q": f"{x}: Подтвердите для ролика «{idea.get('hook_ru', '')}»: {need}"})
    seen, clean = set(), []
    for q in items:
        text = q["q"].split(": ", 1)[-1] if q["from"] == "facts" else q["q"]
        if latin_share(text) > 0.2:
            problems.append(f"owner item not in Russian, not sent: {text[:80]}")
        elif has_past_date(text, today):
            problems.append(f"owner item has a date before {today}, not sent: {text[:80]}")
        elif text not in seen:
            seen.add(text)
            clean.append(q)
    card_items, deferred = owner_card(clean)
    msg = "\n".join(f"{n}. {q['q'].split(': ', 1)[-1] if q['from'] == 'facts' else q['q']}" for n, q in enumerate(card_items, 1))
    return {"week1": week1, "minutes": minutes, "shots": shots, "manifest": manifest, "card": card, "codes": codes,
            "owner_card": card_items, "owner_deferred": deferred, "problems": problems,
            "for_review": {"WEEK1_SHOOT_CARD_RU": card, "OWNER_MESSAGE_RU": msg, "CODE_PROBLEMS": problems}}


# ----------------------------------------------------------------- the run


@dataclass
class BrainRun:
    client: str
    request: str
    out_dir: Path
    steps: dict = field(default_factory=dict)
    checks: dict = field(default_factory=dict)
    questions: list = field(default_factory=list)       # for the owner, batched
    staff_asks: list = field(default_factory=list)      # go on the staff card, never in the owner's message

    def save(self, name: str, data) -> None:
        self.steps[name] = data
        (self.out_dir / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def method_text(path: Path | None = None) -> str:
    """The active method: brain/METHOD.md, else the newest brain/METHOD_v<N>.md (an explicit path must exist)."""
    p = path or METHOD_PATH
    if not p.exists() and path is None:
        versions = sorted(METHOD_PATH.parent.glob("METHOD_v*.md"),
                          key=lambda f: int(re.sub(r"\D", "", f.stem) or 0))
        p = versions[-1] if versions else p
    if not p.exists():
        raise FileNotFoundError(f"method not found: {p} (the brain needs brain/METHOD.md)")
    return p.read_text(encoding="utf-8")


def _sys(method: str, step: str) -> str:
    return ("You are the marketing brain of an autonomous short-video marketing agent for local businesses. "
            "Follow the METHOD literally; when it does not cover something, use the judgment of a top strategist "
            "and say so in the output. Never invent facts about the business: use only the inputs; "
            "anything else is labelled an assumption. Audience-facing copy in Russian (or the client's language); "
            f"everything else in English.\n\nCURRENT STEP: {step}\n\nMETHOD:\n{method}")


def run(client: Client, request: str, llm: LLM, out_root: Path | None = None, n_ideas: int = 24,
        slate: int = 8, capacity_min: float = 20.0, critique: bool = True, method_path: Path | None = None,
        now=None, run_id: str | None = None, fetch=acquire._get, rereview: bool = False) -> BrainRun:
    """fetch: how the agent re-fetches product pages it already knows (None = never fetch)."""
    method = method_text(method_path)
    rid = run_id or time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    today = (now or datetime.now(timezone.utc)).date().isoformat()
    out = (out_root or client.dir / "campaigns") / rid
    out.mkdir(parents=True, exist_ok=True)
    br = BrainRun(client.slug, request, out)
    # A run's inputs are frozen at its first start: resuming the same run id replays its finished steps even if the
    # ledger changed meanwhile (e.g. this run's own fact fetch). A new run id takes a fresh snapshot.
    snap = out / "inventory.json"
    inv = json.loads(snap.read_text(encoding="utf-8")) if snap.exists() else inventory(client, now)
    br.save("inventory", inv)
    files = {f["path"] for f in inv["files"]}
    ctx = ("CLIENT INPUTS (JSON; files can be opened with the Read tool for detail):\n" +
           json.dumps(inv, ensure_ascii=False, indent=1) + f"\n\nTHE BOSS'S REQUEST, verbatim: {request}")

    # 1 intake
    intake = llm.json(f"intake:{client.slug}", _sys(method, "A. Request intake"), ctx +
                      "\n\nTurn the request into the intake object. Ask at most 3 questions; assume where the answer "
                      "would not change the plan.", INTAKE_SCHEMA)
    br.save("intake", intake)
    br.questions += [{"from": "intake", "q": q} for q in intake.get("clarifying_questions") or []]

    # 2 inputs
    inputs = llm.json(f"inputs:{client.slug}", _sys(method, "B. Inputs"), ctx + "\n\nINTAKE:\n" +
                      json.dumps(intake, ensure_ascii=False) +
                      "\n\nList what is already in hand and what is missing, ranked by value per owner minute.", INPUTS_SCHEMA)
    br.save("inputs", inputs)
    br.questions += [{"from": "inputs", "q": m["input"], "how": m["how"], "minutes": m.get("owner_minutes")}
                     for m in inputs["missing"] if m["who"] == "owner"]
    br.staff_asks += [{"q": m["input"], "how": m["how"]} for m in inputs["missing"] if m["who"] == "staff"]

    # 3 evidence + insights (one revision if sources do not hold)
    prompt3 = (ctx + "\n\nINTAKE:\n" + json.dumps(intake, ensure_ascii=False) +
               "\n\nBuild the evidence base (cite fact ids, file paths or URLs as source) and the ranked insights.")
    ins = llm.json(f"insights:{client.slug}", _sys(method, "C. Working the inputs"), prompt3, INSIGHTS_SCHEMA)
    p3 = check_insights(ins, client.ledger, files)
    if p3:
        ins = llm.json(f"insights-fix:{client.slug}", _sys(method, "C. Working the inputs"), prompt3 +
                       "\n\nYOUR PREVIOUS ANSWER:\n" + json.dumps(ins, ensure_ascii=False) +
                       "\n\nTHESE ITEMS FAILED THE SOURCE CHECK, fix them:\n- " + "\n- ".join(p3), INSIGHTS_SCHEMA)
        p3 = check_insights(ins, client.ledger, files)
    br.save("insights", ins)
    br.checks["insights"] = p3

    # 4 ideas
    rub = "\n".join(f"- {k}: {v}" for k, v in RUBRIC_HELP.items())
    prompt4 = (ctx + "\n\nINTAKE:\n" + json.dumps(intake, ensure_ascii=False) + "\n\nINSIGHTS:\n" +
               json.dumps(ins, ensure_ascii=False) +
               f"\n\nGenerate {n_ideas} short-video ideas, as diverse as the method demands (drivers, formats, production "
               f"modes, funnel stages). Score each 1-5 on this rubric (a prior, not a prediction):\n{rub}\n"
               "driver and format are the method's exact slugs (D2/D3): code uses them as experiment arms and to "
               "spread the test slate, so they must be honest categories. Write {CODE} where the WhatsApp code goes; "
               "code fills it in.\n"
               f"Staff: one weak phone (good sound only close-up), {capacity_min:g} minutes a week in total. "
               "Prices, numbers, contacts on screen only if they are in facts_usable; otherwise write the idea without "
               "them or mark the fact as needed in facts_used as 'NEEDED: ...'.")
    isch = ideas_schema(method_vocab(method))
    ideas = llm.json(f"ideas:{client.slug}", _sys(method, "D. Idea generation"), prompt4, isch)["ideas"]
    iids = {i["id"] for i in ins["insights"] if (i.get("strength") or 0) > 0}    # rejected insights cannot be cited
    report = {i["id"]: check_idea(i, client.ledger, iids, now) for i in ideas}
    bad = {k: v["errors"] for k, v in report.items() if v["errors"]}
    if bad:
        fixed = llm.json(f"ideas-fix:{client.slug}", _sys(method, "D. Idea generation"), prompt4 +
                         "\n\nYOUR IDEAS:\n" + json.dumps(ideas, ensure_ascii=False) +
                         "\n\nTHESE FAILED THE AUTOMATIC CHECKS. Return the full list with every failing idea fixed or "
                         "replaced:\n" + json.dumps(bad, ensure_ascii=False, indent=1), isch)["ideas"]
        ideas = fixed
        report = {i["id"]: check_idea(i, client.ledger, iids, now) for i in ideas}
    # facts the agent can get itself (known product pages) are fetched now instead of asking the owner
    need = [i for i in ideas if report[i["id"]]["needs_facts"]]
    if need and fetch is not None:
        got = acquire.fill_facts(client.ledger, client.dir / "facts.jsonl", client.dir,
                                 [t for i in need for _, t in audience_strings(i)], fetch, now)
        br.checks["fetched_facts"] = got
        if got["added"]:
            report = {i["id"]: check_idea(i, client.ledger, iids, now) for i in ideas}
    br.save("ideas", ideas)
    br.checks["ideas"] = report
    for iid, r in report.items():
        for n in r["needs_facts"]:
            br.questions.append({"from": "facts", "q": f"Confirm before idea {iid} can be produced: {n}"})

    # 5 selection (code)
    arm_stats = None
    eng_file = client.dir / "engine_state.json"
    if eng_file.exists():
        arm_stats = json.loads(eng_file.read_text(encoding="utf-8")).get("summary")
    blocked = {k for k, v in report.items() if v["errors"]}
    chosen = select(ideas, slate, load_weights(), arm_stats, blocked=blocked)
    week_ids, week_shots, week_min = plan_week(chosen, capacity_min)
    selection = {"slate": [{"id": c["id"], "prior": c["_prior"], "value": round(c["_value"], 3), "why": c["_why"],
                            "driver": c.get("driver"), "engine": engine_key(c), "staff_min": round(idea_minutes(c), 1),
                            "needs_facts": report[c["id"]]["needs_facts"]} for c in chosen],
                 "blocked": sorted(blocked), "week1_filmed": week_ids, "week1_minutes": round(week_min, 1),
                 "note": "prior = weighted rubric; audience data (engine_state.json) overrides it as posts accumulate"}
    br.save("selection", selection)

    # 6 campaign: sees the whole checked pool (not only the code slate) and the asks it must merge
    slate_ids = [c["id"] for c in chosen]
    pool = [i for i in ideas if i["id"] not in blocked]
    pending = [q for q in br.questions if q.get("from") in ("intake", "inputs")]
    prompt6 = (ctx + f"\n\nTODAY: {today}. Never write a date before today; write deadlines as «в течение 24 часов»." +
               "\n\nINTAKE:\n" + json.dumps(intake, ensure_ascii=False) + "\n\nINSIGHTS:\n" +
               json.dumps(ins["insights"], ensure_ascii=False) +
               "\n\nIDEA POOL (every idea that passed the code checks; ids are stable):\n" + json.dumps(pool, ensure_ascii=False) +
               f"\n\nSLATE CHOSEN BY CODE (default test set): {slate_ids}"
               f"\nWEEK 1 FILMING THAT FITS THE STAFF BUDGET ({week_min:.1f} of {capacity_min:g} min): {week_ids}"
               "\nweeks[week=1].idea_ids is the FILMING SET for week 1: only pool ids; code rebuilds the staff card from it."
               "\n\nPENDING OWNER ASKS from intake and inputs (owner_asks must absorb every one you still need, rewritten "
               "in plain Russian with a default; anything you leave out is NOT asked):\n" + json.dumps(pending, ensure_ascii=False) +
               "\n\nDesign the campaign. Any offer that is not already in facts_usable needs owner approval.")
    camp = llm.json(f"campaign:{client.slug}", _sys(method, "F. Campaign design"), prompt6, CAMPAIGN_SCHEMA)
    gated = {i["id"] for i in ideas if report.get(i["id"], {}).get("needs_facts") or declared_needs(i)}
    preview = deliverables(client, camp, ideas, blocked, gated, slate_ids, capacity_min, today, codes_preview=True)

    # 7 critique (method F13 + the actual deliverables) -> one revision that may patch ideas -> re-attack
    reviews = []
    personas = (f"the BOSS of {client.profile.get('name', client.slug)} (persona: boss), who asked: {request}. Does this "
                "solve MY problem, is it worth my staff's time and money, is anything risky, embarrassing or untrue?",
                "a veteran short-form creator and SMM for local businesses in Kazakhstan/CIS (persona: veteran_creator): "
                "is anything generic, ad-like, unproducible with one weak phone in 20 minutes, or unlikely to spread or "
                "bring inquiries?")
    review_sys = ("Attack the plan; be concrete; severity fatal = you would reject it. Judge the DELIVERABLES (the staff "
                  "shoot card and the owner message) as well as the plan.\n\n" + method_section(method, "F13") +
                  "\n" + method_section(method, "G6"))

    def attack(c, tag):
        b = json.dumps({"intake": intake, "slate": [i for i in ideas if i["id"] in set(slate_ids) | set(week1_of(c))],
                        "campaign": c, **deliverables(client, c, ideas, blocked, gated, slate_ids, capacity_min, today,
                                                      codes_preview=True)["for_review"]}, ensure_ascii=False)
        return [approval_gate(llm.json(f"{tag}:{client.slug}:{persona[:12]}", "You are " + persona + " " + review_sys,
                                       b, REVIEW_SCHEMA, effort="medium")) for persona in personas]
    if critique:
        reviews = attack(camp, "review")
        serious = [r for rv in reviews for r in rv["refutations"] if r["severity"] in ("fatal", "major")]
        if serious:
            rev = llm.json(f"campaign-revise:{client.slug}", _sys(method, "F. Campaign design (revision)"), prompt6 +
                           "\n\nYOUR CAMPAIGN:\n" + json.dumps(camp, ensure_ascii=False) +
                           "\n\nFIX EVERY ONE OF THESE BY CHANGING THE PLAN (not by arguing). A fix to an idea's content goes "
                           "in idea_patches (only the fields that change; drop=true removes it); weeks[week=1].idea_ids is "
                           "the final filming set:\n" + json.dumps(serious, ensure_ascii=False, indent=1), REVISION_SCHEMA)
            br.checks["patches"] = apply_patches(ideas, rev.pop("idea_patches", []), client.ledger, now)
            report = {i["id"]: check_idea(i, client.ledger, iids, now) for i in ideas}
            blocked |= {k for k, v in report.items() if v["errors"]} | {i["id"] for i in ideas if i.get("_dropped")}
            gated = {i["id"] for i in ideas if report.get(i["id"], {}).get("needs_facts") or declared_needs(i)}
            camp = rev
            if rereview:
                br.save("reviews_after", attack(camp, "review-after"))
    br.save("reviews", reviews)

    # deliverables, built ONLY from the final campaign and the (patched) ideas
    if not camp.get("owner_asks"):
        camp["owner_asks"] = [{"ask": q["q"], "why": "", "minutes": q.get("minutes") or 1} for q in pending]
    final = deliverables(client, camp, ideas, blocked, gated, slate_ids, capacity_min, today)
    camp["attribution_codes"] = final["codes"]
    br.checks["campaign"] = final["problems"]
    br.checks["ideas_final"] = {k: v for k, v in report.items() if v["errors"] or v["needs_facts"]}
    br.save("ideas", ideas)
    br.save("campaign", camp)
    br.steps["selection"]["week1_filmed"], br.steps["selection"]["week1_minutes"] = final["week1"], round(final["minutes"], 1)
    br.save("selection", br.steps["selection"])
    (out / "manifest_week1.json").write_text(json.dumps(final["manifest"], ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "shoot_card_week1_ru.txt").write_text(final["card"], encoding="utf-8")
    br.questions = final["owner_card"]
    br.save("checks", br.checks)
    br.save("questions", final["owner_card"])
    br.save("questions_deferred", final["owner_deferred"])
    br.save("staff_asks", br.staff_asks)
    (out / "campaign.md").write_text(render_md(br, ideas, final), encoding="utf-8")
    return br


# ----------------------------------------------------------------- owner-facing summary


def render_md(br: BrainRun, ideas: list[dict], final: dict) -> str:
    """Internal summary for MetaPrompt (English, with Russian quotes). Built from the FINAL campaign, the final week-1
    set and both review rounds, so it never shows a plan that was revised away."""
    it, cp, sel = br.steps["intake"], br.steps["campaign"], br.steps["selection"]
    byid = {i["id"]: i for i in ideas}
    last = br.steps.get("reviews_after") or br.steps.get("reviews") or []
    approved = bool(last) and all(r["would_approve"] for r in last)
    L = [f"# {cp['name']}  (internal, for MetaPrompt)", ""]
    if last and not approved:
        L += [f"**NOT APPROVED by the attack:** " + ", ".join(f"{r['persona'][:20]} {r['score']}/10" for r in last) +
              " (approval needs >=7 and no fatal point). Open points are listed at the end.", ""]
    L += [f"**Request:** {br.request}", f"**Reframed:** {it['reframed_request']}",
          f"**Success metric:** {it['success_metric']['name']} — target {it['success_metric']['target']} by "
          f"{it['success_metric']['by_when']} ({it['success_metric']['how_measured']})", ""]
    if it.get("push_back"):
        L += [f"**Push back (to the owner):** {it['push_back']}", ""]
    L += ["## Big idea", cp["big_idea"], "", f"> {cp['single_minded_message_ru']}", "", cp["why_this_wins"], "",
          f"## Week 1: filmed and published ({len(final['week1'])} videos, {final['minutes']:.1f} staff min)", ""]
    planned = set(week1_of(cp))
    for iid in final["week1"]:
        i = byid[iid]
        L += [f"### {iid} · {i.get('title', '')}" + ("" if iid in planned else "  (RESERVE: the plan's week-1 ideas wait for facts)"),
              f"- Hook: «{i.get('hook_ru', '')}»  — first frame: {i.get('first_frame', '')}",
              f"- What happens: {i.get('what_happens', '')}",
              f"- Driver · format · funnel: {i.get('driver')} · {i.get('format')} · {i.get('funnel')}",
              f"- WhatsApp code: {final['codes'].get(iid, '—')}; KPI: {i.get('kpi', '')}", ""]
    rest = [s_["id"] for s_ in sel["slate"] if s_["id"] not in final["week1"]]
    if rest:
        L += ["## Rest of the test slate (code selection: rubric prior + data + diversity)", ""]
        L += [f"- {x}: «{byid[x].get('hook_ru', '')}» ({byid[x].get('driver')}/{byid[x].get('format')})" for x in rest if x in byid]
    L += ["", "## Weeks", ""] + [f"- **Week {w['week']}** — {w['goal']}: {', '.join(w['idea_ids']) or '—'}. Staff: "
                                 f"{w['worker_ask_ru']}. AI: {w['ai_work']}" for w in cp["weeks"]]
    L += ["", "## Measurement and decisions", f"- Metric: {cp['measurement']['success_metric']}",
          f"- Attribution: {cp['measurement']['attribution']}", f"- Review: {cp['measurement']['review_cadence']}"]
    L += [f"- Rule: {r}" for r in cp["decision_rules"]]
    off = cp.get("offer") or {}
    if off.get("needed"):
        L += ["", "## Offer", off["proposal"] + ("  **(needs owner approval)**" if off.get("needs_owner_approval") else "")]
    L += ["", "## Owner message (Russian, one batch)"] + [f"{n}. {q['q'].split(': ', 1)[-1] if q['from'] == 'facts' else q['q']}"
                                                          for n, q in enumerate(final["owner_card"], 1)]
    if final["problems"]:
        L += ["", "## Code checks on the deliverables"] + [f"- {x}" for x in final["problems"]]
    for title, rv in (("Attack before revision", br.steps.get("reviews") or []), ("Attack after revision", br.steps.get("reviews_after") or [])):
        if rv:
            L += ["", f"## {title}"] + [f"- {r['persona'][:30]}: {r['score']}/10, approved={r['would_approve']}" for r in rv]
    if last:
        open_pts = [f"- [{f['severity']}] {f['target']}: {f['why_fails']}" for r in last for f in r["refutations"] if f["severity"] != "minor"]
        if open_pts:
            L += ["", "## Open points from the last attack"] + open_pts
    return "\n".join(L) + "\n"
