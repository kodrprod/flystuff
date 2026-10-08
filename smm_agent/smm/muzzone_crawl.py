"""Polite crawler for muzzone.kz (CS-Cart storefront).

Pure parsers (`parse_listing`, `parse_product`) take HTML text and return plain
dicts so they can be unit-tested offline. The `crawl_*` helpers do the network
part with a fixed delay between requests and a descriptive User-Agent.

Why this exists: facts about the client (prices, stock, policies) must come
from a source with a URL and a fetch date, never from memory or simulation.
"""
from __future__ import annotations

import html as _html
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

BASE = "https://muzzone.kz"
UA = "MetaPromptSMM-research/0.1 (+contact: info@metaprompt; polite, <=2 req/s)"
DELAY_S = 0.6


# One price token: not glued to a preceding digit, thousands groups of exactly
# three digits ("472 680 ₸"). Matched per line so SKUs/ratings on neighbouring
# lines can never be absorbed into a price.
_PRICE_RE = re.compile(r"(?<![\d.\-])(\d{1,3}(?: \d{3})+|\d+)\s*₸")


def _num(s: str) -> int:
    return int(re.sub(r"\D", "", s))


def fetch(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def _clean_lines(fragment: str) -> list[str]:
    s = re.sub(r"<(script|style|noscript|svg)[^>]*>.*?</\1>", "", fragment, flags=re.S)
    s = re.sub(r"<(br|/p|/div|/li|/h\d|/tr|/a)[^>]*>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = _html.unescape(s)
    lines = [re.sub(r"[ \t\xa0]+", " ", ln).strip() for ln in s.split("\n")]
    return [ln for ln in lines if ln]


def parse_listing(page_html: str) -> list[dict]:
    """Product cards from a CS-Cart category/sale listing.

    Cards are the `<form name="product_form_<id>">` blocks. Price is the last
    `N ₸` in the card; if two prices are present the first is the old one.
    """
    out: list[dict] = []
    for m in re.finditer(r'<form[^>]*name="product_form_(\d+)"[^>]*>(.*?)</form>', page_html, re.S):
        pid, blk = m.group(1), m.group(2)
        href = re.search(r'<a[^>]+href="(https://muzzone\.kz/[^"]+\.html)"', blk)
        title = re.search(r'title="([^"]+)"', blk)
        lines = _clean_lines(blk)
        prices = [_num(p) for ln in lines for p in _PRICE_RE.findall(ln) if _num(p) > 0]
        if not href or not prices:
            continue
        item = {
            "id": pid,
            "url": href.group(1),
            "name": _html.unescape(title.group(1)) if title else lines[0],
            "price": prices[-1],
            "old_price": prices[0] if len(prices) >= 2 and prices[0] > prices[-1] else None,
        }
        if item["old_price"]:
            item["discount_pct"] = round(100 * (item["old_price"] - item["price"]) / item["old_price"])
        out.append(item)
    return out


def parse_product(page_html: str) -> dict:
    """Facts from a product page: JSON-LD Product + visible stock quantity."""
    rec: dict = {}
    for b in re.findall(r'application/ld\+json[^>]*>(.*?)</script>', page_html, re.S):
        try:
            j = json.loads(b)
        except ValueError:
            continue
        if j.get("@type") != "Product":
            continue
        offers = j.get("offers") or [{}]
        o = offers[0] if isinstance(offers, list) else offers
        rating = j.get("aggregateRating") or {}
        rec = {
            "name": j.get("name"),
            "sku": j.get("sku"),
            "brand": (j.get("brand") or {}).get("name"),
            "category": j.get("category"),
            "price": o.get("price"),
            "currency": o.get("priceCurrency"),
            "availability": (o.get("availability") or "").rsplit("/", 1)[-1] or None,
            "rating": rating.get("ratingValue"),
            "review_count": rating.get("reviewCount"),
            "url": j.get("url"),
        }
        break
    text = " ".join(_clean_lines(re.sub(r"<script.*?</script>", "", page_html, flags=re.S)))
    m = re.search(r"В наличии:\s*(\d[\d\s]*)\s*шт", text)
    rec["stock_qty"] = _num(m.group(1)) if m else None
    return rec


def crawl_listing(path: str, per_page: int = 128, max_pages: int = 30) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()
    for page in range(1, max_pages + 1):
        sep = "&" if "?" in path else "?"
        url = f"{BASE}{path}{sep}items_per_page={per_page}&page={page}"
        try:
            page_html = fetch(url)
        except urllib.error.HTTPError as e:
            if e.code == 404 and page > 1:  # CS-Cart 404s past the last page
                break
            raise
        cards = [c for c in parse_listing(page_html) if c["id"] not in seen]
        if not cards:
            break
        for c in cards:
            seen.add(c["id"])
        items.extend(cards)
        time.sleep(DELAY_S)
    return items


def crawl_products(urls: list[str]) -> list[dict]:
    out = []
    for u in urls:
        try:
            rec = parse_product(fetch(u))
        except Exception as e:  # network/parse errors are data, not crashes
            rec = {"error": repr(e)}
        rec["url"] = rec.get("url") or u
        rec["fetched_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        out.append(rec)
        time.sleep(DELAY_S)
    return out
