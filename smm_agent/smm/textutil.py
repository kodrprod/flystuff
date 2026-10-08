"""Text helpers shared by the renderer (line breaking) and the checks (word counting)."""
import re

NBSP = " "
UNBREAKABLE = re.compile(
    r"\+?\d[\d ]{6,}\d"                                   # phones: +7 701 0987734
    r"|\d{1,3}(?: \d{3})+(?: ?(?:₸|тг|тенге|%))?"         # grouped numbers with unit: 695 913 ₸
    r"|\d+ ?(?:₸|тг|тенге|%|дн\w*|мес\w*|кг|шт)"          # 14 дней, 20%
)


def protect(text: str) -> str:
    """Glue digit groups, units and phones with NBSP so they stay one token."""
    return UNBREAKABLE.sub(lambda m: m.group(0).replace(" ", NBSP), text)


def words(text: str) -> list[str]:
    """Words as a viewer reads them: a grouped price or a phone is one word; bare symbols are not words."""
    # split on ordinary whitespace only: str.split() would also split on the NBSP that glues tokens
    return [w for w in re.split(r"[ \t\r\n]+", protect(text.strip())) if re.search(r"\w", w)]
