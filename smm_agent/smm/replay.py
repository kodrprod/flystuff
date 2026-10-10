"""Replay a recorded brain run through the CURRENT code with zero model calls, and verify its deliverables.

    python -m smm.replay --runs <stress dir> --method brain/METHOD_v1.md --out <dir> [--only a,b]

Each step's model output is taken from the run's tape by step name (prompts changed since the recording, so the
prompt hash cannot match; the output is what the model said for that step). The client folder is copied first, so
codes and ledger writes never touch the real client. Then every deliverable is checked against the final plan:
  - the filmed week-1 set is a subset of the final campaign's week-1 ideas, none blocked/dropped/waiting for facts;
  - the manifest and shoot card contain exactly the shots of that set;
  - the owner message holds only the final campaign's asks and Russian fact questions, no Latin labels, no past dates;
  - codes are unique and written into the published ideas;
  - approval follows the method (score >= 7 and no fatal).
It also counts what the OLD code shipped (shots for ideas outside the final week 1), so the fix is measurable.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

from . import brain
from .llm import LLM, Backend, LLMError, Tape

ROOT = Path(__file__).resolve().parent.parent


class StepReplay(Backend):
    """Returns the last successful recorded output for a step name; never calls a model, never invents."""
    name = "step-replay"

    def __init__(self, tape_path: Path):
        self.by_step: dict[str, dict] = {}
        for line in tape_path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r.get("ok"):
                self.by_step[r["step"]] = r["output"]
        self.calls: list[str] = []

    def raw(self, call):
        self.calls.append(call.step)
        step = call.step
        if step not in self.by_step and step.split(":")[0].endswith("-fix"):
            # today's checks asked for a fix round the recording did not need: replay the unfixed output
            step = step.replace("-fix:", ":", 1)
        if step not in self.by_step:
            raise LLMError(f"no recording for step {call.step!r}")
        out = json.loads(json.dumps(self.by_step[step]))
        if "idea_patches" in call.schema.get("required", []) and "idea_patches" not in out:
            out["idea_patches"] = []          # recorded before the revision could patch ideas
        return out


def verify(out_dir: Path, today: str) -> list[str]:
    """Hard checks on the files a human receives. Empty list = every deliverable comes from the final plan."""
    p = []
    ld = lambda n: json.loads((out_dir / n).read_text(encoding="utf-8"))
    camp, ideas, sel, qs = ld("campaign.json"), ld("ideas.json"), ld("selection.json"), ld("questions.json")
    byid = {i["id"]: i for i in ideas}
    final_w1 = set(brain.week1_of(camp))
    week1 = sel["week1_filmed"]
    checks = ld("checks.json").get("campaign", []) if (out_dir / "checks.json").exists() else []
    reserves = {x for c in checks if "reserves added" in c for x in re.findall(r"'([^']+)'", c)}
    for x in week1:
        if x not in final_w1 and final_w1 and x not in reserves:     # only logged reserves may join week 1
            p.append(f"filmed {x} is not in the final campaign's week 1")
        if byid.get(x, {}).get("_dropped"):
            p.append(f"filmed {x} was dropped by the revision")
        if brain.declared_needs(byid.get(x, {})):
            p.append(f"filmed {x} still waits for owner facts")
    man = ld("manifest_week1.json")
    if {m["idea_id"] for m in man} - set(week1):
        p.append(f"manifest has shots for ideas outside week 1: {sorted({m['idea_id'] for m in man} - set(week1))}")
    card = (out_dir / "shoot_card_week1_ru.txt").read_text(encoding="utf-8")
    numbered = re.findall(r"^\d+\. ", card, re.M)
    if len(numbered) != len(man):
        p.append(f"shoot card lists {len(numbered)} shots, manifest {len(man)}")
    asks = {a["ask"] for a in camp.get("owner_asks") or []}
    for q in qs:
        text = q["q"].split(": ", 1)[-1] if q["from"] == "facts" else q["q"]
        if q["from"] == "facts":
            text = text.rsplit("»: ", 1)[-1]          # check the fact itself, not the Russian wrapper around it
        if q["from"] == "campaign" and q["q"] not in asks:
            p.append(f"owner item not from the final campaign: {q['q'][:60]}")
        if brain.latin_share(text) > 0.2:
            p.append(f"owner item not in Russian: {text[:60]}")
        if brain.has_past_date(text, today):
            p.append(f"owner item has a past date: {text[:60]}")
    codes = camp.get("attribution_codes") or {}
    if len(set(codes.values())) != len(codes):
        p.append("duplicate attribution codes")
    for iid, c in codes.items():
        if "{CODE}" in json.dumps(byid.get(iid, {}), ensure_ascii=False):
            p.append(f"{iid}: {{CODE}} placeholder left unfilled")
    for f in ("reviews.json", "reviews_after.json"):
        if (out_dir / f).exists():
            for r in ld(f):
                expect = r["score"] >= 7 and not any(x["severity"] == "fatal" for x in r["refutations"])
                if r["would_approve"] != expect:
                    p.append(f"{f}: approval {r['would_approve']} contradicts score {r['score']}")
    return p


def old_mismatch(old_dir: Path) -> dict:
    """What the OLD code shipped: shots and codes for ideas outside the final campaign's week 1."""
    try:
        camp = json.loads((old_dir / "campaign.json").read_text(encoding="utf-8"))
        man = json.loads((old_dir / "manifest_week1.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    w1 = set(brain.week1_of(camp))
    return {"old_shots": len(man), "old_shots_outside_final_week1": sum(1 for m in man if m["idea_id"] not in w1),
            "old_ideas_outside": sorted({m["idea_id"] for m in man if m["idea_id"] not in w1})}


def replay_case(case: dict, runs: Path, method: Path, out: Path, now=None) -> dict:
    src = (ROOT / "clients" / case["client"]) if case.get("real") else (ROOT / "stress" / "clients" / case["client"])
    sandbox = out / "_clients"
    if (sandbox / case["client"]).exists():
        shutil.rmtree(sandbox / case["client"])
    shutil.copytree(src, sandbox / case["client"], ignore=shutil.ignore_patterns("campaigns"))
    be = StepReplay(runs / f"{case['key']}.tape.jsonl")
    llm = LLM(be, Tape(out / f"{case['key']}.replay.jsonl"), resume=False)
    run_dir = out / case["key"]
    if run_dir.exists():
        shutil.rmtree(run_dir)
    br = brain.run(brain.Client.load(case["client"], sandbox), case["request"], llm, out_root=out, run_id=case["key"],
                   method_path=method, fetch=None, rereview=True, now=now)
    today = (now.date().isoformat() if now else __import__("datetime").date.today().isoformat())
    problems = verify(run_dir, today)
    sel = br.steps["selection"]
    return {"case": case["key"], "model_calls": 0, "replayed_steps": len(be.calls), "verify_problems": problems,
            "week1": sel["week1_filmed"], "week1_minutes": sel["week1_minutes"], "owner_items": len(br.questions),
            "code_checks": br.checks.get("campaign", []), "patches": br.checks.get("patches"),
            **old_mismatch(runs / case["key"])}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="smm.replay")
    ap.add_argument("--runs", required=True)
    ap.add_argument("--method", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="")
    a = ap.parse_args(argv)
    cases = json.loads((ROOT / "stress" / "cases.json").read_text(encoding="utf-8"))
    keep = set(a.only.split(",")) if a.only else None
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for c in cases:
        if keep and c["key"] not in keep or not (Path(a.runs) / c["key"] / "campaign.json").exists():
            continue
        try:
            results.append(replay_case(c, Path(a.runs), Path(a.method), out))
        except Exception as e:                                   # report, keep going
            results.append({"case": c["key"], "error": f"{type(e).__name__}: {e}"[:400]})
    (out / "replay_report.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in results:
        print(json.dumps(r, ensure_ascii=False)[:600])
    return 0 if all(not r.get("error") and not r.get("verify_problems") for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
