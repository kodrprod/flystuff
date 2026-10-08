"""Handoff queue: every point where a human must act, as a durable file.

Design goals taken from the failures of earlier runs:
  * survives crashes and new sessions (one JSON file per card, no hidden state);
  * a silent human must not stall the system *or* be silently overridden:
    escalation ladder, then PARK the item and keep working on everything else;
  * approvals and offers can never time out into "approved" (rails R2/R3);
  * one message per stage, not a stream of small questions.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROLES = {"BOSS", "STAFF", "CLIENT", "FILMER", "EDITOR", "PUBLISHER", "METRICS", "ANDREY"}
KINDS = {"question", "filming", "approval", "offer", "publish", "metrics", "access"}
NEVER_AUTO = {"approval", "offer", "publish"}          # no timeout may resolve these positively

# hours after `created_at` at which each escalation level triggers
LADDER = [(0, "asked"), (24, "reminder"), (72, "shorten_and_switch_channel"), (168, "parked")]


@dataclass
class Card:
    id: str
    client: str
    stage: str
    role: str
    kind: str
    do: str
    paste_back: str
    why: str
    created_at: str
    due_hours: int = 48
    status: str = "open"                 # open | answered | parked
    level: int = 0                       # index into LADDER
    answer: str = ""
    answered_at: str = ""
    minutes_spent: float | None = None
    blocks: list[str] = field(default_factory=list)   # ids of work items waiting on this

    def __post_init__(self):
        if self.role not in ROLES:
            raise ValueError(f"unknown role {self.role}")
        if self.kind not in KINDS:
            raise ValueError(f"unknown kind {self.kind}")


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(timezone.utc)


def _t(s: str) -> datetime:
    return datetime.fromisoformat(s)


class Queue:
    def __init__(self, directory: str | Path):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, cid: str) -> Path:
        return self.dir / f"{cid}.json"

    def save(self, c: Card) -> None:
        self._path(c.id).write_text(json.dumps(asdict(c), ensure_ascii=False, indent=1), encoding="utf-8")

    def get(self, cid: str) -> Card:
        return Card(**json.loads(self._path(cid).read_text(encoding="utf-8")))

    def all(self) -> list[Card]:
        return [Card(**json.loads(p.read_text(encoding="utf-8"))) for p in sorted(self.dir.glob("*.json"))]

    def create(self, **kw) -> Card:
        kw.setdefault("created_at", _now(None).isoformat(timespec="seconds"))
        c = Card(**kw)
        if self._path(c.id).exists():
            raise ValueError(f"card {c.id} already exists")
        self.save(c)
        return c

    def answer(self, cid: str, text: str, minutes: float | None = None, now: datetime | None = None) -> Card:
        c = self.get(cid)
        if not text.strip():
            raise ValueError("empty answer")
        c.answer, c.status = text.strip(), "answered"
        c.minutes_spent = minutes
        c.answered_at = _now(now).isoformat(timespec="seconds")
        self.save(c)
        return c

    def tick(self, now: datetime | None = None) -> list[tuple[Card, str]]:
        """Advance escalation for open cards. Returns [(card, action)] to carry out
        ('reminder', 'shorten_and_switch_channel', 'parked'). Idempotent per level."""
        now = _now(now)
        actions = []
        for c in self.all():
            if c.status != "open":
                continue
            age_h = (now - _t(c.created_at)).total_seconds() / 3600
            target = max(i for i, (h, _) in enumerate(LADDER) if age_h >= h * max(c.due_hours, 1) / 48)
            if target > c.level:
                c.level = target
                action = LADDER[target][1]
                if action == "parked":
                    c.status = "parked"
                self.save(c)
                actions.append((c, action))
        return actions

    def default_on_timeout(self, c: Card) -> str:
        """What the system may do while a card is parked. Never a positive decision on gated kinds."""
        if c.kind in NEVER_AUTO:
            return "hold: do not publish/offer; continue other work"
        if c.kind == "filming":
            return "skip this week's real footage; use rendered/library material"
        if c.kind == "question":
            return "keep the fact as `unknown`; do not assume (R6)"
        return "hold"

    def open_for(self, role: str) -> list[Card]:
        return [c for c in self.all() if c.role == role and c.status == "open"]

    def blocked_by_open(self, work_id: str) -> list[Card]:
        return [c for c in self.all() if c.status in ("open", "parked") and work_id in c.blocks]


def batch_message(cards: list[Card]) -> str:
    """One message per stage/role in the protocol's card format."""
    out = []
    for c in cards:
        out.append(f"HANDOFF — you are: {c.role}\nClient: {c.client} · Stage: {c.stage}\n"
                   f"Do: {c.do}\nPaste back: {c.paste_back}\nWhy: {c.why}")
    return "\n\n".join(out)
