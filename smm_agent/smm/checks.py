"""Deterministic content checks (rails R4, R5, R6).

Only what can be decided by rule is decided here. Taste is not: that is the
calibrated judge's job (`calibration.py`). Every check returns Violations; the
pipeline must not show a hook/script/caption to anyone while `error`s remain.

Number policy (R6 "never invent client facts"): a number in client-facing text
must match a usable ledger value, *with its unit* when it has one ("14 дней" is
not backed by "14 мес"). Plain numbers below 10, years, and numbers glued to
model names (PX-770, X100) are ignored.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .facts import Ledger
from .textutil import words


@dataclass
class Violation:
    rule: str
    severity: str  # "error" blocks; "warn" is shown but does not block
    message: str
    where: str = ""

    def __str__(self) -> str:
        loc = f" [{self.where}]" if self.where else ""
        return f"{self.severity.upper()} {self.rule}{loc}: {self.message}"


# ---------------------------------------------------------------- patterns
CHILDISH = re.compile(
    r"угадай|отгадай|спорим|пиши\s*[«\"']?\s*[12]\b|\b1\s*или\s*2\b|"
    r"\bguess\b|comment\s*[12]\b|ставь\s+(лайк|❤)",
    re.I,
)
AD_VOICE = re.compile(
    r"спешите|успейте|не\s+упустите|только\s+у\s+нас|лучшие\s+цены|"
    r"уникальное\s+предложение|выгодное\s+предложение|мы\s+рады\s+предложить|"
    r"don'?t\s+miss|limited\s+offer",
    re.I,
)
SCARCITY = re.compile(
    r"только\s+сегодня|последний\s+день|последние\s+\w+|осталось\s+\d+|"
    r"до\s+конца\s+(месяца|недели|года|сезона)|ограниченн\w+\s+(тираж|количество|предложение)|"
    r"успей\w*|распродан[оа]?\s+скоро|закрываемся|закрытие\s+магазина",
    re.I,
)
ABSOLUTE_CLAIM = re.compile(
    r"лучш\w+|самы[йяео]\s+\w+|№\s*1|номер\s+один|единственн\w+|гарантируем|"
    r"идеальн\w+|дешевле\s+всех|\b100\s*%\s*\w+|best\b|#1\b",
    re.I,
)
PHONE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().\-]{8,}\d)(?!\d)")
URL = re.compile(r"(?:https?://)?(?:www\.)?[a-z0-9\-]+\.(?:kz|com|ru|org|net)(?:/[^\s]*)?", re.I)
HANDLE = re.compile(r"(?<![\w.])@[a-z0-9_.]{3,}", re.I)

UNIT_MAP = {
    "₸": "₸", "тг": "₸", "тенге": "₸", "kzt": "₸",
    "%": "%", "процент": "%", "процентов": "%",
    "дн": "дн", "дня": "дн", "дней": "дн", "день": "дн",
    "мес": "мес", "месяц": "мес", "месяца": "мес", "месяцев": "мес",
    "год": "год", "года": "год", "лет": "год",
    "кг": "кг", "шт": "шт",
}
NUM = re.compile(
    r"(?<![\w\-./])(\d{1,3}(?:[  ]\d{3})+|\d+)(?:[.,](\d+))?\s*(₸|тенге|тг|kzt|%|процент\w*|дней|дня|день|дн\.?|месяц\w*|мес\.?|года|год|лет|кг|шт\.?)?(?![\w])",
    re.I,
)


def _norm_num(whole: str, frac: str | None) -> str:
    s = re.sub(r"[  ]", "", whole)
    return f"{s}.{frac}" if frac else s


def numbers_in(text: str) -> list[tuple[str, str, str]]:
    """(normalized number, normalized unit or '', raw match) for each standalone number."""
    out = []
    for m in NUM.finditer(text):
        # skip phone-like long digit runs; those are handled as phones
        digits = re.sub(r"\D", "", m.group(0))
        if len(digits) >= 10:
            continue
        unit = (m.group(3) or "").lower().rstrip(".")
        out.append((_norm_num(m.group(1), m.group(2)), UNIT_MAP.get(unit, ""), m.group(0).strip()))
    return out


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)


def _allowed_numbers(values: set[str]) -> tuple[set[tuple[str, str]], set[str]]:
    pairs: set[tuple[str, str]] = set()
    nums: set[str] = set()
    for v in values:
        for n, u, _ in numbers_in(v):
            pairs.add((n, u))
            nums.add(n)
    return pairs, nums


# ------------------------------------------------------------------ checks
def check_hook(spoken: str, on_screen: str = "", max_words: int = 8) -> list[Violation]:
    out: list[Violation] = []
    wl = words(spoken)
    if not wl:
        out.append(Violation("H0", "error", "empty spoken hook", "hook"))
    if len(wl) > max_words:
        out.append(Violation("H1", "error", f"hook has {len(wl)} words, max {max_words}", "hook"))
    for label, txt in (("spoken", spoken), ("on_screen", on_screen)):
        if CHILDISH.search(txt):
            out.append(Violation("H2", "error", "childish/engagement-bait game", f"hook.{label}"))
        if AD_VOICE.search(txt):
            out.append(Violation("H3", "warn", "ad voice", f"hook.{label}"))
    if wl and not (re.search(r"\d", spoken) or re.search(r"[A-Za-z]{2,}", spoken)):
        out.append(Violation("H4", "warn", "no number or model/brand token: is it specific?", "hook"))
    return out


def check_text(text: str, ledger: Ledger, where: str = "text", now=None) -> list[Violation]:
    """R6: numbers, absolute claims, scarcity and contacts must be backed by usable facts."""
    out: list[Violation] = []
    values = ledger.usable_values(now)
    pairs, nums = _allowed_numbers(values)

    # Phones are validated as contacts below; mask them so their digit groups
    # are not mistaken for prices/quantities.
    masked = PHONE.sub(lambda m: " " * len(m.group(0)) if len(_digits(m.group(0))) >= 10 else m.group(0), text)
    for n, u, raw in numbers_in(masked):
        if not u and re.fullmatch(r"\d{4}", n) and 1900 <= int(n) <= 2100:
            continue
        if not u and float(n) < 10:
            continue
        if u:
            ok = (n, u) in pairs
        else:
            ok = n in nums
        if not ok:
            out.append(Violation("R6-NUM", "error", f"number {raw!r} not backed by a usable fact", where))

    for rx, rule, sev, msg in (
        (ABSOLUTE_CLAIM, "R6-CLAIM", "error", "absolute/superlative claim without a backing fact"),
        (SCARCITY, "R6-SCARCITY", "error", "scarcity/urgency claim without a backing fact"),
    ):
        for m in rx.finditer(text):
            phrase = m.group(0).lower().strip()
            if not any(phrase in v for v in values):
                out.append(Violation(rule, sev, f"{msg}: {m.group(0)!r}", where))

    if CHILDISH.search(text):
        out.append(Violation("H2", "error", "childish/engagement-bait game", where))
    if AD_VOICE.search(text):
        out.append(Violation("H3", "warn", "ad voice", where))

    contact_values = {_digits(v) for v in values if len(_digits(v)) >= 10} | {v for v in values}
    for m in PHONE.finditer(text):
        d = _digits(m.group(0))
        if len(d) >= 10 and not any(d.endswith(cv[-10:]) for cv in contact_values if len(cv) >= 10 and cv.isdigit()):
            out.append(Violation("R6-CONTACT", "error", f"phone {m.group(0).strip()!r} not in ledger", where))
    for m in HANDLE.finditer(text):
        if m.group(0).lower() not in values:
            out.append(Violation("R6-CONTACT", "error", f"handle {m.group(0)!r} not in ledger", where))
    for m in URL.finditer(text):
        u = m.group(0).lower().rstrip(".,)")
        if not any(u in v or v in u for v in values if "." in v):
            out.append(Violation("R6-CONTACT", "error", f"url {m.group(0)!r} not in ledger", where))
    return out


def check_shots(shots: list[dict]) -> list[Violation]:
    """R5: AI footage may never show the client's real product, dishes, interior or people."""
    out = []
    banned = {"client_product", "client_interior", "client_people", "client_dish"}
    for i, s in enumerate(shots):
        if s.get("kind") == "ai" and banned & set(s.get("depicts", [])):
            out.append(Violation("R5", "error",
                                 f"AI shot depicts {sorted(banned & set(s['depicts']))}", f"shots[{i}]"))
    return out


def check_script(script: dict, ledger: Ledger, now=None) -> list[Violation]:
    """Run every applicable check on a script dict (see tests for the shape)."""
    out: list[Violation] = []
    out += check_hook(script.get("hook_spoken", ""), script.get("hook_onscreen", ""))
    out += check_text(script.get("hook_spoken", ""), ledger, "hook_spoken", now)
    out += check_text(script.get("hook_onscreen", ""), ledger, "hook_onscreen", now)
    beats = script.get("beats", [])
    for i, b in enumerate(beats):
        # every string that can end up on screen is checked, including card prices
        for k in ("spoken", "onscreen", "text", "price", "price2", "old_price"):
            if b.get(k):
                out += check_text(b[k], ledger, f"beats[{i}].{k}", now)
    first = (beats[0].get("onscreen") or beats[0].get("text") or "") if beats else ""
    if script.get("hook_onscreen") and first.strip() != script["hook_onscreen"].strip():
        out.append(Violation("H5", "error", "first beat must show the hook text (first frame = what the words say)", "beats[0]"))
    out += check_text(script.get("caption", ""), ledger, "caption", now)
    cta = script.get("cta", {})
    if not cta.get("text"):
        out.append(Violation("R4-CTA", "error", "no CTA", "cta"))
    else:
        out += check_text(cta["text"], ledger, "cta", now)
        if not (cta.get("fact_id") and cta["fact_id"] in ledger.usable(now)):
            out.append(Violation("R4-CTA", "error", "CTA must cite a usable ledger fact (fact_id)", "cta"))
    out += check_shots(script.get("shots", []))
    return out


def errors(vs: list[Violation]) -> list[Violation]:
    return [v for v in vs if v.severity == "error"]
