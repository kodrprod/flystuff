"""Build the Muzzone facts ledger from crawled product records + the policy/contact
pages read on 2026-10-08. Every fact carries its source URL and date.

Prices and stock expire after 2 days (they change; a video must not quote a
price nobody re-checked). Policies/contacts expire after 30 days.
"""
from __future__ import annotations

import json
from pathlib import Path

from .facts import Fact, Ledger

SITE = "https://muzzone.kz"
POLICY_DATE = "2026-10-08"
POLICY_TTL = 30
PRICE_TTL = 2


def kzt(n: int) -> str:
    return f"{n:,}".replace(",", " ") + " ₸"


def static_facts() -> list[Fact]:
    W = "web"

    def f(id, text, src, values, **kw):
        return Fact(id, text, W, f"{SITE}/{src}".rstrip("/"), POLICY_DATE, values=values, ttl_days=POLICY_TTL, **kw)

    return [
        f("site", "Сайт магазина", "", ["muzzone.kz"]),
        f("wa", "WhatsApp магазина +7 701 0987734", "kontakty.html", ["+7 701 0987734"]),
        f("phone_city", "Телефон +7 (7172) 250775", "kontakty.html", ["+7 (7172) 250775"]),
        f("phone_mobile", "Мобильный +7 701 0709003", "kontakty.html", ["+7 701 0709003"]),
        f("ig", "Instagram магазина", "", ["@muzzone_astana"]),
        f("address", "Астана, ул. Кажымукана, 14, НП-6", "kontakty.html", ["Кажымукана, 14", "Кажымукана 14"]),
        f("hours", "Звонки: пн-пт 10:00–19:00, сб 10:00–17:00", "kontakty.html", ["10:00", "19:00", "17:00"]),
        f("returns_14d", "Возврат товара надлежащего качества в течение 14 дней (ст. 30 Закона РК о защите прав потребителей)",
          "garantii-i-vozvrat.html", ["14 дней"]),
        f("returns_conditions",
          "Условия: товар не был в употреблении, сохранены товарный вид, потребительские свойства, ярлыки, упаковка и документ о покупке",
          "garantii-i-vozvrat.html", ["не был в употреблении", "ярлыки", "упаковка"]),
        f("returns_phrase", "Сайт: «вернуть товар в 14-дневный срок без лишних вопросов с нашей стороны»",
          "garantii-i-vozvrat.html", ["без лишних вопросов"]),
        f("returns_cost",
          "При возврате товара надлежащего качества удерживается стоимость доставки в оба конца (+3% при наложенном платеже); "
          "компенсация доставки возможна за честный отзыв в соцсетях или видео",
          "garantii-i-vozvrat.html", ["доставка в оба конца", "3%"]),
        f("warranty", "Минимальная гарантия на товары магазина — 12 месяцев", "garantii-i-vozvrat.html", ["12 месяцев"]),
        f("warranty_casio", "Casio: гарантия производителя 2 года; обслуживание только в сервис-центре Алматы",
          "garantii-i-vozvrat.html", ["2 года"]),
        f("delivery_free_100k", "Бесплатная доставка по Казахстану (наземным транспортом) при заказе свыше 100 000 ₸",
          "dostavka-i-oplata.html", ["100 000 ₸"]),
        f("delivery_astana", "Курьер по Астане бесплатно: вес заказа более 20 кг и стоимость свыше 15 000 ₸",
          "dostavka-i-oplata.html", ["20 кг", "15 000 ₸"]),
        f("pickup_reserve", "Самовывоз: резерв заказа действует 3 рабочих дня, затем отменяется; можно попросить продлить",
          "dostavka-i-oplata.html", ["3 рабочих дня", "продлим"]),
        f("payments", "Оплата: Kaspi QR, Kaspi Pay, Kaspi перевод, карты Visa/MasterCard, Apple Pay, наличные при получении или самовывозе",
          "cifrovoe-pianino-casio-px-770-bkc7.html", ["Kaspi QR", "Kaspi Pay"]),
        f("sale_page", "Раздел «Распродажа» на сайте (на странице называется «Финальная распродажа»; причина и срок неизвестны)",
          "rasprodazha.html", ["распродажа"],
          note="Do NOT use the word 'финальная', end dates or scarcity: the reason and duration are unknown."),
        f("original", "Сайт: «100% оригинальный товар»", "cifrovoe-pianino-casio-px-770-bkc7.html", ["100% оригинальный товар"]),
    ]


def product_facts(key: str, rec: dict) -> list[Fact]:
    """Facts for one crawled product record. Out-of-stock products yield no usable stock fact."""
    fetched = rec["fetched_at"]
    url, name = rec["url"], rec["name"]
    out = [Fact(f"{key}_price", f"{name} — {kzt(rec['price'])}", "web", url, fetched,
                values=[kzt(rec["price"]), name], ttl_days=PRICE_TTL)]
    if rec.get("old_price"):
        out.append(Fact(f"{key}_old", f"{name}: прежняя цена {kzt(rec['old_price'])}", "web", url, fetched,
                        values=[kzt(rec["old_price"])], ttl_days=PRICE_TTL))
        pct = round(100 * (rec["old_price"] - rec["price"]) / rec["old_price"])
        out.append(Fact(f"{key}_disc", f"{name}: скидка {pct}%", "derived", "", "",
                        values=[f"{pct}%"], derived_from=[f"{key}_price", f"{key}_old"], ttl_days=PRICE_TTL))
    if rec.get("availability") == "InStock":
        out.append(Fact(f"{key}_instock", f"{name}: в наличии (по данным сайта)", "web", url, fetched, ttl_days=PRICE_TTL))
    props = rec.get("properties") or {}
    vals = [str(v) for v in props.values() if v not in (None, "")]
    out.append(Fact(f"{key}_specs", f"{name}: " + "; ".join(f"{k}: {v}" for k, v in props.items()), "web", url,
                    fetched, values=vals, ttl_days=POLICY_TTL))
    return out


def price_diff_fact(id: str, a_key: str, a: dict, b_key: str, b: dict) -> Fact:
    d = abs(a["price"] - b["price"])
    return Fact(id, f"Разница цен: {kzt(d)}", "derived", "", "", values=[kzt(d)],
                derived_from=[f"{a_key}_price", f"{b_key}_price"], ttl_days=PRICE_TTL)


def build_ledger(products_json: str | Path, keys: dict[str, str]) -> tuple[Ledger, dict[str, dict]]:
    """keys: short key -> substring of the product name. Returns (ledger, key -> record)."""
    recs = json.loads(Path(products_json).read_text(encoding="utf-8"))
    lg = Ledger(static_facts())
    by_key: dict[str, dict] = {}
    for k, needle in keys.items():
        match = [r for r in recs if needle.lower() in (r.get("name") or "").lower() and not r.get("error")]
        if not match:
            raise KeyError(f"no product record for {needle!r}")
        by_key[k] = match[-1]            # latest fetch wins
        for fct in product_facts(k, by_key[k]):
            lg.add(fct)
    return lg, by_key
