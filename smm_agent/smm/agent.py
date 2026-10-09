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
    client = brain.Client.load(a.client, Path(a.clients_dir) if a.clients_dir else None)
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
                       critique=not a.no_critique, run_id=a.run_id,
                       method_path=Path(a.method) if a.method else None, out_root=Path(a.out) if a.out else None,
                       rereview=a.rereview, fetch=None if a.no_fetch else brain.acquire._get)
    except UsageLimitError as e:
        print(f"PARKED: the model is usage-limited right now ({str(e)[-160:]}). Re-run the same command later: "
              f"finished steps are replayed from the tape ({tape}) and not paid for twice.", file=sys.stderr)
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


def cmd_produce(a) -> int:
    from . import produce
    client = brain.Client.load(a.client)
    d = _latest_run(client, a.run)
    method = brain.method_text(Path(a.method) if a.method else None)
    out = produce.produce_week(d, Path(a.clips), client.ledger, method, client=client.slug)
    for p in out:
        print(f"{p.idea_id}: {'shipped by critic' if p.ok else 'needs a human look'} -> {p.video}  {'; '.join(p.notes)}")
    print(f"approval cards: {d / 'cards'}")
    return 0 if all(p.video for p in out) else 1


def cmd_approve(a) -> int:
    """Record the owner's answer for one exact file + caption (any later edit voids it)."""
    from .publish import ApprovalStore
    client = brain.Client.load(a.client)
    d = _latest_run(client, a.run)
    ap = ApprovalStore(d / "approvals").approve(a.video, a.caption, a.approver, "CLIENT", note=a.note or "")
    print(f"approved {a.video} (sha256 {ap.video_sha256[:16]}) by {a.approver}")
    return 0


def caption_for(idea: dict) -> str:
    """Platform caption: the hook plus the coded call to action (codes were filled in by the brain)."""
    parts = [idea.get("hook_ru", "").strip(), idea.get("cta_ru", "").strip(), idea.get("comment_prompt_ru", "").strip()]
    return " ".join(x for x in parts if x)[:150]


def cmd_package(a) -> int:
    """For every produced video: the exact caption, all publish checks, and the TikTok draft arguments.
    Nothing is posted: a human submits the draft (and only an approved file+caption passes the checks)."""
    from .publish import ApprovalStore, PublishPackage, problems, to_tiktok_prepare_args
    client = brain.Client.load(a.client)
    d = _latest_run(client, a.run)
    ideas = {i["id"]: i for i in json.loads((d / "ideas.json").read_text(encoding="utf-8"))}
    store, out = ApprovalStore(d / "approvals"), []
    for vid in sorted((d / "produce").glob("*/design/round*/draft.mp4")):
        iid = vid.parts[-4]
        idea = ideas.get(iid, {})
        mode = idea.get("production", {}).get("mode", "worker")
        pkg = PublishPackage(str(vid), caption_for(idea), is_aigc=mode in ("ai", "mixed"))
        probs = problems(pkg, store, scripts_ok=True)
        out.append({"idea": iid, "video": str(vid), "caption": pkg.caption, "is_aigc": pkg.is_aigc, "problems": probs,
                    "tiktok_draft_args": None if probs else to_tiktok_prepare_args(pkg, "<connector>", "<uploaded url>")})
    (d / "publish_packages.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for o in out:
        print(f"{o['idea']}: {'READY (draft)' if not o['problems'] else 'BLOCKED: ' + '; '.join(o['problems'])}")
    return 0


def cmd_metrics(a) -> int:
    from . import loop
    client = brain.Client.load(a.client)
    r = loop.record_metrics(client.dir, Path(a.csv).read_text(encoding="utf-8"), client.profile)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    if a.whatsapp:
        senders = set(a.shop_sender or []) or {client.profile.get("name", "")}
        print(json.dumps(loop.record_leads(client.dir, Path(a.whatsapp).read_text(encoding="utf-8"), senders),
                         ensure_ascii=False, indent=1))
    if a.learn:
        print(f"learnings written: {len(loop.learn(client.dir, client.profile))}")
    return 1 if r["problems"] else 0


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
    p.add_argument("--method", help="method file (default brain/METHOD.md)")
    p.add_argument("--out", help="folder for runs (default clients/<slug>/campaigns)")
    p.add_argument("--clients-dir", help="where client folders live (default clients/)")
    p.add_argument("--rereview", action="store_true", help="re-run the attack after the revision (stress tests)")
    p.add_argument("--no-fetch", action="store_true", help="never re-fetch product pages")
    p.set_defaults(fn=cmd_plan)
    q = sub.add_parser("questions")
    q.add_argument("--client", required=True)
    q.add_argument("--run")
    q.set_defaults(fn=cmd_questions)
    s = sub.add_parser("status")
    s.add_argument("--client", required=True)
    s.set_defaults(fn=cmd_status)
    pr = sub.add_parser("produce", help="staff clips -> edited, AI-designed videos + approval cards")
    pr.add_argument("--client", required=True)
    pr.add_argument("--clips", required=True, help="folder with the clips in shoot-card order")
    pr.add_argument("--run")
    pr.add_argument("--method", help="playbook given to the designer (default brain/METHOD.md)")
    pr.set_defaults(fn=cmd_produce)
    ap_ = sub.add_parser("approve", help="record the owner's approval of one exact video + caption")
    ap_.add_argument("--client", required=True)
    ap_.add_argument("--video", required=True)
    ap_.add_argument("--caption", required=True)
    ap_.add_argument("--approver", required=True)
    ap_.add_argument("--note")
    ap_.add_argument("--run")
    ap_.set_defaults(fn=cmd_approve)
    pk = sub.add_parser("package", help="captions + publish checks + TikTok draft args (never posts)")
    pk.add_argument("--client", required=True)
    pk.add_argument("--run")
    pk.set_defaults(fn=cmd_package)
    m = sub.add_parser("metrics", help="post metrics (+ WhatsApp export) -> experiment engine -> next week's selection")
    m.add_argument("--client", required=True)
    m.add_argument("--csv", required=True, help="post_id,arm(=idea id),platform,posted_at,views[,shares,saves,...]")
    m.add_argument("--whatsapp", help="WhatsApp chat export (.txt) to count coded inquiries")
    m.add_argument("--shop-sender", action="append", help="the shop's own sender name(s) in the export")
    m.add_argument("--learn", action="store_true", help="also pool arm estimates into knowledge/learnings.jsonl")
    m.set_defaults(fn=cmd_metrics)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
