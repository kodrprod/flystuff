"""WhatsApp attribution: which video actually produced a conversation.

Muzzone (like most local retailers in Kazakhstan) sells through WhatsApp chats, so views are not the goal and
"likes" are noise. Each post gets a short code; the CTA asks people to message that code (and the wa.me link
pre-fills it where links are clickable: bio link, Stories link sticker, YouTube description, ads).
Counting codes in a WhatsApp chat export gives inquiries per video - the metric the owner cares about.

Codes use only characters that look the same in Latin and Cyrillic (A B C E H K M O P T X) plus digits 2-9,
because buyers type on a Russian keyboard: "КТ27" typed in Cyrillic still matches "KT27".
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote

LETTERS = "ABCEHKMOPTX"
DIGITS = "23456789"
CYR2LAT = str.maketrans({"А": "A", "В": "B", "С": "C", "Е": "E", "Н": "H", "К": "K", "М": "M", "О": "O",
                         "Р": "P", "Т": "T", "Х": "X", "а": "A", "в": "B", "с": "C", "е": "E", "н": "H",
                         "к": "K", "м": "M", "о": "O", "р": "P", "т": "T", "х": "X"})


def make_code(campaign_index: int, post_index: int) -> str:
    """Deterministic, short, typeable code, e.g. 'KT27'. Unique for campaign_index < 121 and post_index < 64."""
    a = LETTERS[campaign_index % len(LETTERS)]
    b = LETTERS[(campaign_index // len(LETTERS)) % len(LETTERS)]
    d1 = DIGITS[(post_index // len(DIGITS)) % len(DIGITS)]
    d2 = DIGITS[post_index % len(DIGITS)]
    return f"{a}{b}{d1}{d2}"


def normalize(s: str) -> str:
    return re.sub(r"[\s\-_.#№]", "", s.translate(CYR2LAT).upper())


def wa_link(phone: str, code: str, product: str | None = None) -> str:
    digits = re.sub(r"\D", "", phone)
    text = f"Здравствуйте! Пишу по видео {code}" + (f" ({product})" if product else "")
    return f"https://wa.me/{digits}?text={quote(text)}"


def cta_text(code: str) -> str:
    return f"Напишите в WhatsApp код {code} — подскажем и проверим наличие"


@dataclass
class Msg:
    at: datetime
    sender: str
    text: str


_ANDROID = re.compile(r"^(\d{1,2})[./](\d{1,2})[./](\d{2,4}),?\s+(\d{1,2}):(\d{2})(?::\d{2})?\s*[-–]\s*([^:]+?):\s(.*)$")
_IOS = re.compile(r"^\[(\d{1,2})[./](\d{1,2})[./](\d{2,4}),?\s+(\d{1,2}):(\d{2})(?::\d{2})?\]\s*([^:]+?):\s(.*)$")


def parse_whatsapp_export(text: str) -> list[Msg]:
    """Android ('08.10.2026, 14:03 - Имя: текст') and iOS ('[08.10.2026, 14:03:12] Имя: текст') exports.
    Continuation lines are appended to the previous message. System lines without a sender are skipped."""
    out: list[Msg] = []
    for raw in text.splitlines():
        line = raw.replace("‎", "").strip()
        m = _IOS.match(line) or _ANDROID.match(line)
        if m:
            d, mo, y, h, mi, sender, body = m.groups()
            y = int(y) + (2000 if len(y) == 2 else 0)
            out.append(Msg(datetime(y, int(mo), int(d), int(h), int(mi)), sender.strip(), body))
        elif out and line:
            out[-1].text += "\n" + line
    return out


def count_inquiries(msgs: list[Msg], codes: list[str], shop_senders: set[str]) -> dict[str, dict]:
    """Per code: number of distinct customers whose message contained the code, and first contact time.
    The shop's own messages never count. One customer counts once per code."""
    want = {normalize(c): c for c in codes}
    seen: dict[str, set[str]] = defaultdict(set)
    first: dict[str, datetime] = {}
    for m in msgs:
        if m.sender in shop_senders:
            continue
        flat = normalize(m.text)
        for nc, c in want.items():
            if nc in flat and m.sender not in seen[c]:
                seen[c].add(m.sender)
                first[c] = min(first.get(c, m.at), m.at)
    return {c: {"customers": len(seen[c]), "first_contact": first[c].isoformat() if c in first else None} for c in codes}
