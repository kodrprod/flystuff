"""Weekly shoot card: fit real footage into the store workers' time budget.

Constraint from the brief: staff have one mediocre iPhone and ~20 minutes a week.
So the planner decides *which videos are worth real footage this week* and gives
a numbered, location-ordered checklist that fits the budget — including setup,
retakes and upload, not just the clip lengths.

Model (minutes):
  fixed          reading the card + uploading                      = FIXED_MIN
  per location   walking/setting up the first time at a location   = SETUP_MIN
  per shot       seconds_of_footage * takes / 60 + OVERHEAD_MIN
Budget used = capacity * (1 - safety). A video (script) is produced only if ALL
its required shots are filmed; shots shared between videos are filmed once.

Selection is exact (subset search) for <= EXACT_MAX videos, greedy beyond.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field

FIXED_MIN = 2.0
SETUP_MIN = 1.0
OVERHEAD_MIN = 0.5
EXACT_MAX = 18


@dataclass(frozen=True)
class Shot:
    id: str
    what: str                  # one sentence the worker understands
    location: str              # e.g. "стена с гитарами"
    seconds: int               # footage needed (final, after trimming)
    kind: str = "demo"         # demo | talk | detail | process
    takes: int = 2
    say: str = ""              # exact words for talk shots (kept short)


@dataclass
class Video:
    id: str
    value: float               # priority (e.g. from the experiment engine / campaign plan)
    shots: list[str] = field(default_factory=list)   # required Shot ids


def hook_shot(id: str, product: str, location: str, action: str) -> Shot:
    """The first 2 seconds of a real-footage video. It is filmed separately so a bad take costs 3 seconds,
    not a whole demo, and the editor can always open the video with the strongest moment."""
    return Shot(id, f"{product}: {action}", location, 3, "hook", takes=3)


def shot_minutes(s: Shot) -> float:
    return s.seconds * s.takes / 60.0 + OVERHEAD_MIN


def session_minutes(shots: list[Shot]) -> float:
    locs = {s.location for s in shots}
    return (FIXED_MIN if shots else 0.0) + SETUP_MIN * len(locs) + sum(shot_minutes(s) for s in shots)


def _shots_for(videos: list[Video], by_id: dict[str, Shot]) -> list[Shot]:
    ids = sorted({i for v in videos for i in v.shots})
    return [by_id[i] for i in ids]


def plan(videos: list[Video], shots: list[Shot], capacity_min: float = 20.0, safety: float = 0.15):
    """Return (chosen_videos, chosen_shots_in_order, minutes). Maximises total value within
    capacity*(1-safety); ties broken by fewer minutes."""
    by_id = {s.id: s for s in shots}
    for v in videos:
        missing = [i for i in v.shots if i not in by_id]
        if missing:
            raise KeyError(f"video {v.id} needs unknown shots {missing}")
    budget = capacity_min * (1 - safety)
    cands = [v for v in videos if session_minutes(_shots_for([v], by_id)) <= budget]   # a video that alone busts the budget is never choosable
    best: tuple[float, float, list[Video]] = (0.0, 0.0, [])
    if len(cands) <= EXACT_MAX:
        for r in range(1, len(cands) + 1):
            for combo in itertools.combinations(cands, r):
                m = session_minutes(_shots_for(list(combo), by_id))
                if m <= budget:
                    val = sum(v.value for v in combo)
                    if (val, -m) > (best[0], -best[1]):
                        best = (val, m, list(combo))
        chosen = best[2]
    else:                                                           # greedy on marginal value per marginal minute
        chosen, remaining = [], list(cands)
        while remaining:
            cur = session_minutes(_shots_for(chosen, by_id))
            scored = []
            for v in remaining:
                m = session_minutes(_shots_for(chosen + [v], by_id)) - cur
                if cur + m <= budget:
                    scored.append((v.value / max(m, 1e-6), v))
            if not scored:
                break
            _, pick = max(scored, key=lambda t: t[0])
            chosen.append(pick)
            remaining.remove(pick)
    shots_out = order_by_location(_shots_for(chosen, by_id))
    return chosen, shots_out, session_minutes(shots_out)


def order_by_location(shots: list[Shot]) -> list[Shot]:
    """Group by location (no walking back), talk shots after demos at the same place."""
    rank = {"hook": 0, "demo": 1, "detail": 2, "process": 3, "talk": 4}
    first_seen: dict[str, int] = {}
    for s in shots:
        first_seen.setdefault(s.location, len(first_seen))
    return sorted(shots, key=lambda s: (first_seen[s.location], rank.get(s.kind, 9), s.id))


TIPS_RU = [
    "Телефон строго вертикально, основная камера (не фронтальная), без зума пальцами — просто подойдите ближе.",
    "Протрите объектив салфеткой. Свет — от окна или лампы за вашей спиной, не против света.",
    "Держите телефон двумя руками, локти прижаты. Начните запись, молча 1 секунду, потом действие, в конце снова 1 секунду тишины.",
    "Ошиблись — не останавливайте запись: пауза и повторите фразу/действие сразу. Монтаж уберёт лишнее.",
    "Звук важен: инструмент на расстоянии 30–50 см от телефона, музыку в зале выключить, рядом не разговаривать.",
]


def render_card_ru(week: str, shots: list[Shot], minutes: float, capacity_min: float = 20.0) -> str:
    """Plain-text card for WhatsApp/Telegram. Short on purpose."""
    lines = ["Это ИИ-ассистент MetaPrompt: я веду соцсети магазина вместе с владельцем.",
             f"🎬 Съёмка на неделю {week}. Всего ~{round(minutes)} мин из {round(capacity_min)}.", ""]
    n, last_loc = 0, None
    for s in shots:
        if s.location != last_loc:
            lines.append(f"📍 {s.location}")
            last_loc = s.location
        n += 1
        extra = f" Скажите: «{s.say}»" if s.say else ""
        star = "⭐ САМОЕ ВАЖНОЕ (первые 2 секунды ролика): " if s.kind == "hook" else ""
        lines.append(f"{n}. {star}{s.what} — {s.seconds} сек.{extra}")
    lines += ["", "Как снимать:"] + [f"• {t}" for t in TIPS_RU]
    lines += ["", "Когда закончите — отправьте все ролики в этот чат в том же порядке. Я смонтирую, а опубликую только после согласования с владельцем."]
    return "\n".join(lines)


def manifest(shots: list[Shot]) -> list[dict]:
    """Order-based mapping the editor uses to match raw clips to shots."""
    return [{"n": i + 1, "shot_id": s.id, "seconds": s.seconds, "kind": s.kind} for i, s in enumerate(shots)]
