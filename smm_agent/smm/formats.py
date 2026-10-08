"""Format library: the repeatable video formats the agent can plan, each with its marketing job.

A format is not a template for decoration; it states WHICH buyer problem it solves, at which funnel stage,
what the store worker must film (and how long that takes), what AI/automation adds, and what measures it.
The campaign planner may only use formats from this library (so every plan is executable), and the
experiment engine treats formats x angles as arms (so audience data, not taste, decides what stays).

`evidence` says honestly why a format is in the library: measured on the client's own channel, seen in peer
data, or a hypothesis to test. Nothing here is assumed to work.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .shootcard import FIXED_MIN, OVERHEAD_MIN, SETUP_MIN, Shot

FUNNEL = ("awareness", "consideration", "conversion", "trust")


@dataclass(frozen=True)
class ShotTemplate:
    key: str
    what: str            # instruction for the worker, with {product}/{product2}/{question} slots
    location: str
    seconds: int
    kind: str = "demo"
    takes: int = 2
    say: str = ""


@dataclass(frozen=True)
class Format:
    id: str
    name_ru: str
    funnel: str
    job: str                        # the buyer problem it solves
    production: str                 # worker | motion | ugc | mixed
    shots: tuple[ShotTemplate, ...]
    edit: tuple[str, ...]           # ordered edit recipe (segment kinds understood by the editor/renderer)
    kpi: str
    evidence: str
    needs_products: int = 1         # how many in-stock products the brief must name
    ai_allowed: tuple[str, ...] = ()  # which AI steps may be used (never product sound, never fake people)
    risks: tuple[str, ...] = field(default_factory=tuple)

    def worker_minutes(self) -> float:
        """Marginal minutes this format adds to a shoot (fixed card time is shared across the week)."""
        locs = {s.location for s in self.shots}
        return SETUP_MIN * len(locs) + sum(s.seconds * s.takes / 60 + OVERHEAD_MIN for s in self.shots)

    def make_shots(self, prefix: str, **slots) -> list[Shot]:
        return [Shot(f"{prefix}_{t.key}", t.what.format(**slots), t.location, t.seconds, t.kind, t.takes,
                     t.say.format(**slots)) for t in self.shots]


LIB: dict[str, Format] = {f.id: f for f in [
    Format(
        "sound_check", "Как звучит за {price}", "consideration",
        "Buyers cannot hear an instrument online and fear it sounds cheap; let them hear it, honestly, with the price.",
        "worker",
        (ShotTemplate("hook", "{product}: громко сыграйте один аккорд/фразу, камера на руки и гриф/клавиши", "зал", 3, "hook", 3),
         ShotTemplate("demo", "{product}: сыграйте 15 секунд что умеете, телефон в 40 см от инструмента", "зал", 15, "demo")),
        ("hook_clip", "demo_clip+caption", "price_card", "cta_code"),
        "3-s hold, watch-through, saves, WhatsApp inquiries by code",
        "Muzzone's own top YouTube videos are real product demos (e.g. 64k views for a beginner-guitar demo); "
        "short-form transfer is untested.",
        ai_allowed=("captions", "kz_dub_captions", "upscale"),
        risks=("weak sound if the phone is far or the hall is noisy",)),
    Format(
        "same_riff_two_prices", "Одна мелодия — два инструмента", "consideration",
        "The core buying question is 'is the expensive one worth it?'; the same riff on two in-stock instruments answers it by ear.",
        "worker",
        (ShotTemplate("a", "{product}: сыграйте одну и ту же фразу 10 секунд", "зал", 10, "demo"),
         ShotTemplate("b", "{product2}: та же фраза, тот же темп, 10 секунд", "зал", 10, "demo")),
        ("hook_text_over_a", "a_clip", "b_clip", "stat_or_price_duel", "cta_code"),
        "watch-through, comments asking which is better, WhatsApp inquiries",
        "Head-to-head titles won on Muzzone's long-form channel; did not replicate as a title pattern in peer Shorts, "
        "so this is a format hypothesis, not a proven winner.",
        needs_products=2, ai_allowed=("captions", "kz_dub_captions")),
    Format(
        "staff_answers", "Вопрос покупателя — ответ продавца", "consideration",
        "Considered purchases need an expert; a real staff member answering a real buyer question builds trust no ad can.",
        "worker",
        (ShotTemplate("answer", "Ответьте на вопрос покупателя: «{question}». 20 секунд, своими словами, смотрите в камеру", "касса", 20, "talk", 2),),
        ("question_card", "answer_clip+jumpcuts+captions", "product_card", "cta_code"),
        "watch-through, saves, WhatsApp inquiries",
        "Hypothesis. Requires staff consent to appear on camera.",
        needs_products=1, ai_allowed=("captions", "kz_dub_captions", "jumpcuts"),
        risks=("staff may not agree to be filmed", "answer must not invent claims")),
    Format(
        "first_instrument_guide", "Первый инструмент: что проверить", "consideration",
        "Parents and adult beginners fear buying the wrong first instrument; three concrete checks, shown on real stock.",
        "mixed",
        (ShotTemplate("hands", "{product}: покажите вблизи 3 вещи, которые проверяете у новичкового инструмента (по 5 секунд)", "зал", 15, "detail"),),
        ("kinetic_question", "hands_clip+captions", "stat_cards", "price_card", "cta_code"),
        "saves, shares, WhatsApp inquiries",
        "Hypothesis built on Muzzone's 'for beginners' long-form winner; only promote categories that are in stock.",
        ai_allowed=("captions", "voiceover", "kz_dub_captions")),
    Format(
        "before_shipping_check", "Что мы проверяем перед отправкой", "trust",
        "Remote buyers (Kaspi/other cities) fear defects and fakes; showing the real check builds trust.",
        "worker",
        (ShotTemplate("check", "Покажите, как проверяете и настраиваете инструмент перед отправкой, 15 секунд", "склад", 15, "process"),),
        ("hook_text_over_clip", "check_clip+captions", "warranty_card", "cta_code"),
        "watch-through, inquiries from outside Astana",
        "Hypothesis. The site states 'Мы всегда проверяем весь товар перед отправкой' (a client claim we can show).",
        needs_products=0, ai_allowed=("captions",)),
    Format(
        "deal_proof", "Распродажа: проверяем по звуку", "conversion",
        "A sale price alone looks like every ad; 8 seconds of real sound plus the real old/new price makes the deal credible.",
        "mixed",
        (ShotTemplate("play", "{product}: сыграйте 8 секунд, крупно", "зал", 8, "demo"),),
        ("play_clip", "pricedrop", "cta_code"),
        "WhatsApp inquiries by code, stock sell-through",
        "Uses the client's own published sale; motion-only version was judged useless without real sound.",
        ai_allowed=("captions",), risks=("only items with >=2 in stock; re-check stock before publishing",)),
    Format(
        "customer_video", "Видео покупателя", "trust",
        "Real buyers are the most credible voice; the store already compensates return shipping for an honest video review.",
        "ugc", (),
        ("ugc_clip+captions", "cta_code"),
        "trust signals, inquiries",
        "Mechanic exists on muzzone.kz/garantii-i-vozvrat.html; collection flow is new. Requires written consent.",
        needs_products=0, ai_allowed=("captions",), risks=("consent and privacy",)),
]}


def get(fid: str) -> Format:
    if fid not in LIB:
        raise KeyError(f"unknown format {fid!r}; allowed: {sorted(LIB)}")
    return LIB[fid]


def weekly_minutes(format_ids: list[str]) -> float:
    """Upper bound for a week's shoot using these formats (shared locations are counted per format here;
    the shoot-card optimiser merges them and is usually lower)."""
    return FIXED_MIN + sum(get(f).worker_minutes() for f in format_ids)
