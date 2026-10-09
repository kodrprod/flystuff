"""Command line for the agent. One client folder per business under clients/<slug>/.

  python -m smm.agent plan   --client muzzone --request "Нужно продать цифровые пианино до Нового года."
        runs the brain (intake -> inputs -> insights -> ideas -> code selection -> campaign -> attack -> revision)
        and writes clients/<slug>/campaigns/<run>/ : campaign.md (owner), *.json (every step), questions.json,
        shoot_card_week1_ru.txt (staff). Judgment calls go through the `claude` CLI on the subscription by default.
  python -m smm.agent questions --client muzzone [--run <id>]
        the batched owner message for the latest (or given) run: one message, everything we need, minutes each.
  python -m smm.agent status --client muzzone
        what exists for the client: facts usable/stale, runs, open questions.

--llm cli (default, subscription) | api (per-token, needs ANTHROPIC_API_KEY) | recorded (replay a tape, no tokens).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import brain
from .llm import CLIBackend, LLM, RecordedBackend, Tape, UsageLimitError, get_llm


def _latest_run(client: brain.Client, run: str | None) -> Path:
    runs = sorted((client.dir / "campaigns").glob("*/campaign.json"))
    if run:
        p = client.dir / "campaigns" / run
        if not p.is_dir():
            raise SystemExit(f"no run {run}")
        return p
    if not runs:
        raise SystemExit("no campaign runs yet: run `plan` first")
    return runs[-1].parent


def cmd_plan(a) -> int:
    client = brain.Client.load(a.client)
    tape = Path(a.tape) if a.tape else client.dir / "campaigns" / "tape.jsonl"
    if a.llm == "cli":
        # the brain may open the client's research files itself (Read only, inside the client folder)
        llm = LLM(CLIBackend(allowed_tools="Read", add_dirs=[str(client.dir)]), Tape(tape))
    elif a.llm == "recorded":
        llm = LLM(RecordedBackend(Tape(tape)), Tape(Path(str(tape) + ".replay")))
    else:
        llm = get_llm(a.llm, tape)
    try:
        br = brain.run(client, a.request, llm, n_ideas=a.ideas, slate=a.slate, capacity_min=a.minutes,
                       critique=not a.no_critique, run_id=a.run_id)
    except UsageLimitError as e:
        print(f"PARKED: the model is usage-limited right now ({e}). Re-run the same command later; finished "
              f"steps are on the tape and are not paid for twice when replayed with --llm recorded.", file=sys.stderr)
        return 75
    print(f"campaign: {br.out_dir / 'campaign.md'}")
    print(f"questions for the owner: {len(br.questions)}  (python -m smm.agent questions --client {a.client})")
    sel = br.steps["selection"]
    print(f"slate: {[s['id'] for s in sel['slate']]}; week 1 filmed {sel['week1_filmed']} in {sel['week1_minutes']} min")
    return 0


def owner_message(questions: list[dict], client_name: str) -> str:
    """One batched message. Most valuable first; each item says why and how long it takes."""
    seen, items = set(), []
    for q in questions:
        k = q["q"].strip().lower()
        if k not in seen:
            seen.add(k)
            items.append(q)
    order = {"intake": 0, "campaign": 1, "inputs": 2, "facts": 3}
    items.sort(key=lambda q: order.get(q.get("from"), 9))
    lines = [f"Здравствуйте! Это ИИ-ассистент MetaPrompt, я готовлю кампанию для {client_name}. "
             "Чтобы не дёргать вас по одному вопросу, здесь всё сразу. Можно ответить голосовым.", ""]
    for n, q in enumerate(items, 1):
        extra = f" (~{q['minutes']:g} мин)" if isinstance(q.get("minutes"), (int, float)) else ""
        lines.append(f"{n}. {q['q']}{extra}")
    lines += ["", "Если на что-то нет ответа — пропустите: я продолжу с безопасным допущением и ничего не опубликую без вашего согласия."]
    return "\n".join(lines)


def cmd_questions(a) -> int:
    client = brain.Client.load(a.client)
    d = _latest_run(client, a.run)
    qs = json.loads((d / "questions.json").read_text(encoding="utf-8"))
    print(owner_message(qs, client.profile.get("name", client.slug)))
    return 0


def cmd_status(a) -> int:
    client = brain.Client.load(a.client)
    usable = client.ledger.usable()
    stale = client.ledger.report()
    runs = sorted(p.name for p in (client.dir / "campaigns").glob("*") if (p / "campaign.json").exists()) \
        if (client.dir / "campaigns").is_dir() else []
    print(f"{client.profile.get('name', client.slug)}: {len(usable)} usable facts, {len(stale)} not usable")
    for i, p in list(stale.items())[:10]:
        print(f"  not usable: {i}: {'; '.join(p)}")
    print(f"campaign runs: {runs or 'none'}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="smm.agent", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--client", required=True)
    p.add_argument("--request", required=True)
    p.add_argument("--llm", default="cli", choices=["cli", "api", "recorded"])
    p.add_argument("--tape")
    p.add_argument("--ideas", type=int, default=24)
    p.add_argument("--slate", type=int, default=8)
    p.add_argument("--minutes", type=float, default=20.0)
    p.add_argument("--no-critique", action="store_true")
    p.add_argument("--run-id")
    p.set_defaults(fn=cmd_plan)
    q = sub.add_parser("questions")
    q.add_argument("--client", required=True)
    q.add_argument("--run")
    q.set_defaults(fn=cmd_questions)
    s = sub.add_parser("status")
    s.add_argument("--client", required=True)
    s.set_defaults(fn=cmd_status)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
