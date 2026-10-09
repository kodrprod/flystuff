"""Stress test of the brain through the real code path: many very different boss requests, in parallel, each a
full `agent plan` run (intake -> ... -> campaign -> boss + veteran-creator attack -> revision -> re-attack).

    python -m smm.stress --method brain/METHOD_v1.md --out <dir> [--only key1,key2] [--parallel 8]

Cases live in stress/cases.json; hypothetical clients in stress/clients/ (labelled, empty ledgers). Each run keeps
its own tape, so a run parked by a usage limit resumes when the same command is re-run. The scoreboard is computed
from the saved run folders, so it can be rebuilt at any time with --board-only.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def case_cmd(c: dict, method: Path, out: Path) -> list[str]:
    cmd = [sys.executable, "-m", "smm.agent", "plan", "--client", c["client"], "--request", c["request"],
           "--method", str(method), "--out", str(out), "--tape", str(out / f"{c['key']}.tape.jsonl"),
           "--run-id", c["key"], "--rereview"]
    if not c.get("real"):
        cmd += ["--clients-dir", str(ROOT / "stress" / "clients"), "--no-fetch"]
    return cmd


def run_cases(cases: list[dict], method: Path, out: Path, parallel: int) -> dict[str, int]:
    out.mkdir(parents=True, exist_ok=True)
    pending, running, codes = list(cases), {}, {}
    while pending or running:
        while pending and len(running) < parallel:
            c = pending.pop(0)
            log = open(out / f"{c['key']}.log", "w")
            running[c["key"]] = (subprocess.Popen(case_cmd(c, method, out), cwd=ROOT, stdout=log, stderr=log), log)
        for k, (p, log) in list(running.items()):
            if p.poll() is not None:
                codes[k] = p.returncode
                log.close()
                del running[k]
        time.sleep(5)
    return codes


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def board(out: Path, cases: list[dict]) -> list[dict]:
    rows = []
    for c in cases:
        d = out / c["key"]
        rv, rv2 = _load(d / "reviews.json") or [], _load(d / "reviews_after.json") or []
        sel, chk, qs = _load(d / "selection.json") or {}, _load(d / "checks.json") or {}, _load(d / "questions.json") or []
        ideas = _load(d / "ideas.json") or []

        def score(rs):
            return round(sum(r["score"] for r in rs) / len(rs), 1) if rs else None

        def count(rs, sev):
            return sum(1 for r in rs for f in r["refutations"] if f["severity"] == sev)
        rows.append({
            "case": c["key"], "real": c.get("real", False), "done": (d / "campaign.json").exists(),
            "score": score(rv), "score_after": score(rv2),
            "approve": sum(r["would_approve"] for r in rv), "approve_after": sum(r["would_approve"] for r in rv2),
            "fatal": count(rv, "fatal"), "major": count(rv, "major"),
            "fatal_after": count(rv2, "fatal"), "major_after": count(rv2, "major"),
            "ideas": len(ideas), "blocked": len(sel.get("blocked", [])),
            "drivers": len({i.get("driver") for i in ideas}), "engines": len({i.get("format") for i in ideas}),
            "slate": len(sel.get("slate", [])), "week1_min": sel.get("week1_minutes"),
            "needs_facts": sum(len(v.get("needs_facts", [])) for v in (chk.get("ideas") or {}).values()),
            "owner_questions": len(qs), "insight_check_left": len(chk.get("insights") or []),
        })
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="smm.stress")
    ap.add_argument("--method", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="")
    ap.add_argument("--parallel", type=int, default=8)
    ap.add_argument("--board-only", action="store_true")
    a = ap.parse_args(argv)
    cases = json.loads((ROOT / "stress" / "cases.json").read_text(encoding="utf-8"))
    if a.only:
        keep = set(a.only.split(","))
        cases = [c for c in cases if c["key"] in keep]
    out = Path(a.out)
    if not a.board_only:
        codes = run_cases(cases, Path(a.method).resolve(), out, a.parallel)
        print(json.dumps(codes))
    rows = board(out, cases)
    (out / "board.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
