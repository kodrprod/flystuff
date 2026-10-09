"""The learning half of the weekly loop: what happened -> what the agent believes -> what it does next week.

  metrics CSV (one row per published post; `arm` = the idea id the post was made from)
      -> observations.jsonl              each post once (idempotent re-pastes), with its idea's driver and format
      -> experiment engine               y = ln(views / the account's own median views on that platform)
      -> engine_state.json               posterior per arm "driver:<slug>" and "engine:<format slug>";
                                         brain.select() reads it next week, so audience data overrides the prior
  WhatsApp chat export
      -> leads.json                      distinct customers per attribution code (the business metric)
  learn()
      -> knowledge/learnings.jsonl       per-vertical arm estimates with intervals, pooled across clients;
                                         never a "winner" without the engine's decision rule

Nothing here is simulated: if there are no posts there are no observations, and the state says so.
"""
from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

from .attribution import count_inquiries, parse_whatsapp_export
from .experiments import Arm, Engine, parse_metrics_csv, relative_log

ROOT = Path(__file__).resolve().parent.parent
MIN_BASELINE_POSTS = 5          # below this the account median is too noisy; the profile's stated median is used


def _ideas_index(client_dir: Path) -> dict[str, dict]:
    idx = {}
    for f in sorted((client_dir / "campaigns").glob("*/ideas.json")) if (client_dir / "campaigns").is_dir() else []:
        for i in json.loads(f.read_text(encoding="utf-8")):
            idx[i["id"]] = {"driver": i.get("driver"), "format": i.get("format"), "run": f.parent.name}
    return idx


def _read_jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def baseline(obs: list[dict], platform: str, profile: dict) -> float | None:
    """The account's own typical views on this platform: median of its last 20 posts, or the profile's stated
    median until there are enough posts."""
    views = [o["views"] for o in obs if o["platform"] == platform][-20:]
    if len(views) >= MIN_BASELINE_POSTS:
        return float(statistics.median(views))
    stated = (profile.get("baselines") or {}).get(platform)
    return float(stated) if stated else (float(statistics.median(views)) if views else None)


def record_metrics(client_dir: Path, csv_text: str, profile: dict | None = None) -> dict:
    profile = profile or {}
    rows, problems = parse_metrics_csv(csv_text)
    obs_path = client_dir / "metrics" / "observations.jsonl"
    obs = _read_jsonl(obs_path)
    seen = {o["post_id"] for o in obs}
    ideas = _ideas_index(client_dir)
    added, notes = [], []
    for r in rows:
        if r.post_id in seen:
            notes.append(f"{r.post_id}: already recorded")
            continue
        meta = ideas.get(r.arm)
        if not meta:
            notes.append(f"{r.post_id}: arm {r.arm!r} is not an idea id of any campaign run; not recorded")
            continue
        rec = {"post_id": r.post_id, "idea_id": r.arm, "driver": meta["driver"], "format": meta["format"],
               "run": meta["run"], "platform": r.platform, "posted_at": r.posted_at, "views": r.views, **r.extras}
        obs.append(rec)
        seen.add(r.post_id)
        added.append(r.post_id)
    if added:
        obs_path.parent.mkdir(parents=True, exist_ok=True)
        obs_path.write_text("".join(json.dumps(o, ensure_ascii=False) + "\n" for o in obs), encoding="utf-8")
    state = engine_state(client_dir, obs, profile)
    return {"added": added, "problems": problems, "notes": notes, "arms": len(state["summary"])}


def engine_state(client_dir: Path, obs: list[dict], profile: dict) -> dict:
    """Rebuild the posterior from all observations (cheap, and never drifts from the raw data)."""
    eng = Engine([])
    skipped = 0
    for o in obs:
        b = baseline([x for x in obs if x["posted_at"] <= o["posted_at"]], o["platform"], profile)
        if not b:
            skipped += 1
            continue
        y = relative_log(o["views"], b)
        for arm in (f"driver:{o['driver']}", f"engine:{o['format']}"):
            eng.arms.setdefault(arm, Arm(arm))
            eng.observe(arm, y)
    state = {"updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "posts": len(obs),
             "skipped_no_baseline": skipped, "summary": eng.summary() if eng.arms else {},
             "decision": eng.decide() if len(eng.arms) >= 2 else {"status": "undecided", "reason": "fewer than 2 arms"}}
    (client_dir / "engine_state.json").write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    return state


def record_leads(client_dir: Path, export_text: str, shop_senders: set[str]) -> dict:
    """Coded WhatsApp inquiries per idea, from every campaign run's attribution codes."""
    code_to_idea = {}
    for f in sorted((client_dir / "campaigns").glob("*/campaign.json")) if (client_dir / "campaigns").is_dir() else []:
        for iid, code in (json.loads(f.read_text(encoding="utf-8")).get("attribution_codes") or {}).items():
            code_to_idea[code] = iid
    counts = count_inquiries(parse_whatsapp_export(export_text), list(code_to_idea), shop_senders)
    out = {code_to_idea[c]: {"code": c, **v} for c, v in counts.items()}
    (client_dir / "metrics").mkdir(parents=True, exist_ok=True)
    (client_dir / "metrics" / "leads.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def learn(client_dir: Path, profile: dict, knowledge: Path | None = None, min_n: int = 3) -> list[dict]:
    """Pool what this client's audience showed into the cross-client knowledge base, per vertical. Only arms with
    at least `min_n` posts; every entry carries n, the interval and the client, so the next client can weigh it."""
    st_path = client_dir / "engine_state.json"
    if not st_path.exists():
        return []
    st = json.loads(st_path.read_text(encoding="utf-8"))
    kb = (knowledge or ROOT / "knowledge") / "learnings.jsonl"
    old = _read_jsonl(kb)
    slug = client_dir.name
    keep = [x for x in old if not (x.get("client") == slug and x.get("kind") == "arm_estimate")]
    new = []
    for arm, s in sorted(st["summary"].items()):
        if s["n"] < min_n:
            continue
        new.append({"id": f"A-{slug}-{arm}", "kind": "arm_estimate", "client": slug,
                    "vertical": profile.get("vertical", "any"), "arm": arm, "n": s["n"],
                    "x_vs_baseline": round(s["x_vs_baseline"], 2),
                    "interval90_x": [round(2.718281828 ** s["lo90"], 2), round(2.718281828 ** s["hi90"], 2)],
                    "finding": f"{arm}: {s['x_vs_baseline']:.2f}x the account's median views over {s['n']} posts",
                    "use": "prior for this arm in the same vertical; shrink toward 1x for other verticals",
                    "source": f"clients/{slug}/metrics/observations.jsonl", "date": st["updated"][:10],
                    "strength": "measured (own posts)"})
    kb.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in keep + new), encoding="utf-8")
    return new
