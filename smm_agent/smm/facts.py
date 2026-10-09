"""Facts ledger with provenance (rails R6 and the "simulation leaked into facts" failure).

Every client fact carries where it came from. Anything marked `simulated`, lacking
a source, or older than its time-to-live may be *read* by the agent but can never
back a claim in client-facing text. `Ledger.usable()` is the single gate.

Provenance values:
  client     said or written by the client / an authorised person
  web        read from the client's own public pages (source URL required)
  derived    computed from other facts (inputs listed in `derived_from`)
  simulated  invented for a dry run (e.g. a Wizard-of-Oz [BOSS] line) -> never usable externally
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROVENANCE = {"client", "web", "derived", "simulated"}


@dataclass
class Fact:
    id: str
    text: str                       # human-readable claim, in the client's language
    provenance: str
    source: str = ""                # URL, or "who / when" for client statements
    fetched_at: str = ""            # ISO date or datetime
    values: list[str] = field(default_factory=list)  # literal numbers/strings text may quote, e.g. ["695913", "14"]
    ttl_days: int | None = None     # None = does not expire (e.g. address); prices should set this
    do_not_use: bool = False        # known-bad or sensitive; kept for the record
    note: str = ""
    derived_from: list[str] = field(default_factory=list)


def _parse(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class Ledger:
    def __init__(self, facts: list[Fact] | None = None):
        self.facts: dict[str, Fact] = {}
        for f in facts or []:
            self.add(f)

    # -- io ---------------------------------------------------------------
    @classmethod
    def load(cls, path: str | Path) -> "Ledger":
        lg = cls()
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                lg.add(Fact(**json.loads(line)))
        return lg

    def dump(self, path: str | Path) -> None:
        """Atomic: write a temp file and rename, so parallel runs never leave a half-written ledger."""
        path = Path(path)
        tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            for f in self.facts.values():
                fh.write(json.dumps(asdict(f), ensure_ascii=False) + "\n")
        os.replace(tmp, path)

    # -- editing ----------------------------------------------------------
    def add(self, f: Fact) -> None:
        if f.id in self.facts:
            raise ValueError(f"duplicate fact id {f.id}")
        self.facts[f.id] = f

    # -- the gate ---------------------------------------------------------
    def problems(self, f: Fact, now: datetime | None = None) -> list[str]:
        """Why this fact cannot back external text. Empty list = usable."""
        now = now or datetime.now(timezone.utc)
        out: list[str] = []
        if f.provenance not in PROVENANCE:
            out.append(f"unknown provenance {f.provenance!r}")
        if f.provenance == "simulated":
            out.append("simulated: never usable in client-facing text")
        if f.do_not_use:
            out.append("marked do_not_use")
        if f.provenance in {"client", "web"} and not f.source:
            out.append("no source")
        if f.provenance in {"client", "web"} and not f.fetched_at:
            out.append("no date")
        if f.provenance == "derived":
            missing = [d for d in f.derived_from if d not in self.facts]
            if not f.derived_from or missing:
                out.append(f"derived without resolvable inputs {missing or ''}".strip())
            else:
                for d in f.derived_from:
                    out += [f"input {d}: {p}" for p in self.problems(self.facts[d], now)]
        if f.ttl_days is not None and f.fetched_at:
            if now - _parse(f.fetched_at) > timedelta(days=f.ttl_days):
                out.append(f"stale: older than {f.ttl_days} days")
        return out

    def usable(self, now: datetime | None = None) -> dict[str, Fact]:
        return {i: f for i, f in self.facts.items() if not self.problems(f, now)}

    def usable_values(self, now: datetime | None = None) -> set[str]:
        """Every literal a script may quote (numbers, phones, handles...)."""
        vals: set[str] = set()
        for f in self.usable(now).values():
            vals.update(v.strip().lower() for v in f.values)
        return vals

    def report(self, now: datetime | None = None) -> dict[str, list[str]]:
        return {i: p for i, f in self.facts.items() if (p := self.problems(f, now))}
