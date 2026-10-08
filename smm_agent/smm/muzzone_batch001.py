"""Muzzone batch 001: 8 draft short videos, 2 variants x 4 arms, built ONLY from the ledger.

Arms (hypotheses to be tested by the experiment engine, not winners):
  sale        the owner's own published sale (muzzone.kz/rasprodazha.html), in-stock items only
  price_point "what you get for N ₸" on cheap in-stock instruments (Muzzone's own best YouTube
              videos were beginner product videos; this did NOT replicate in peer Shorts, so it stays a hypothesis)
  vs          head-to-head of two real in-stock products using only the site's spec tables
  policy      the client's real policies that remove purchase fears (returns, pickup reserve)

Nothing here is published. Output = scripts + QA report + local mp4 drafts. R2: a CLIENT
approval handoff is still required before anything goes live.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .checks import check_script, errors
from .facts import Ledger
from .muzzone_facts import build_ledger, kzt, price_diff_fact

KEYS = {
    "hib": "Hibilly Retro 30R",
    "mapex": "Mapex Comet CM5295",
    "as100": "Alston AS-100BK",
    "u246": "Caesar U-246",
    "usc40": "Caesar US-C40",
    "uf330": "Alston UF-330",
    "px770": "Casio PX-770 BKC7",
    "ap270": "Celviano AP-270 BKC7",
}
CTA = {"text": "Написать в WhatsApp\n+7 701 0987734", "fact_id": "wa"}
REAL_PHOTO = [{"kind": "real", "depicts": ["client_product"]}]   # the client's own product photos, R5-safe


def _caption(core: str) -> str:
    return f"{core} Пишите в WhatsApp +7 701 0987734 или на muzzone.kz"


def build_scripts(r: dict[str, dict]) -> list[dict]:
    img = {k: v["images"][0] for k, v in r.items()}
    p = {k: kzt(v["price"]) for k, v in r.items()}
    old = {k: kzt(v["old_price"]) for k, v in r.items() if v.get("old_price")}
    diff_uke = kzt(abs(r["uf330"]["price"] - r["usc40"]["price"]))
    diff_pno = kzt(abs(r["ap270"]["price"] - r["px770"]["price"]))

    def S(id, arm, hook, beats, caption, products):
        return {"id": id, "arm": arm, "products": products, "hook_spoken": hook, "hook_onscreen": hook,
                "beats": beats, "caption": caption, "cta": CTA, "shots": REAL_PHOTO, "is_aigc": False,
                "audio": "none in render; publisher adds licensed/trending audio"}

    def timed(beats):
        t = 0.0
        out = []
        for dur, b in beats:
            out.append({"t0": round(t, 2), "t1": round(t + dur, 2), **b})
            t += dur
        return out

    scripts = []
    # ---- sale ---------------------------------------------------------------
    h1 = f"Комбик 30 Вт: было {old['hib']}, стало {p['hib']}"
    scripts.append(S("sale-1-hibilly", "sale", h1, timed([
        (2.8, {"kind": "photo", "image": img["hib"], "onscreen": h1}),
        (3.5, {"kind": "card", "image": img["hib"], "onscreen": "Hibilly Retro 30R", "price": p["hib"], "old_price": old["hib"]}),
        (3.5, {"kind": "text", "onscreen": "Транзисторный комбоусилитель\nдля электрогитары, 30 Вт", "bg": "#14202b"}),
        (3.2, {"kind": "text", "onscreen": "Скидка 20%\nна распродаже muzzone.kz", "bg": "#1b2a1f"}),
        (3.5, {"kind": "text", "onscreen": CTA["text"], "bg": "#101418"}),
    ]), _caption(f"Комбоусилитель Hibilly Retro 30R: {p['hib']} вместо {old['hib']} на распродаже."), ["hib"]))

    h2 = f"Ударная установка Mapex: {p['mapex']} вместо {old['mapex']}"
    scripts.append(S("sale-2-mapex", "sale", h2, timed([
        (2.8, {"kind": "photo", "image": img["mapex"], "onscreen": h2}),
        (3.5, {"kind": "card", "image": img["mapex"], "onscreen": "Mapex Comet CM5295", "price": p["mapex"], "old_price": old["mapex"]}),
        (3.5, {"kind": "text", "onscreen": "5 барабанов\nкорпус из тополя", "bg": "#14202b"}),
        (3.2, {"kind": "text", "onscreen": "Скидка 20%\nна распродаже muzzone.kz", "bg": "#1b2a1f"}),
        (3.5, {"kind": "text", "onscreen": CTA["text"], "bg": "#101418"}),
    ]), _caption(f"Ударная установка Mapex Comet CM5295: {p['mapex']} вместо {old['mapex']} на распродаже."), ["mapex"]))

    # ---- price point ----------------------------------------------------------
    h3 = f"Электрогитара за {p['as100']}: что получаешь?"
    scripts.append(S("price-1-alston-as100", "price_point", h3, timed([
        (2.8, {"kind": "photo", "image": img["as100"], "onscreen": h3}),
        (3.2, {"kind": "text", "onscreen": "Форма Stratocaster\nдатчики HSS", "bg": "#14202b"}),
        (3.2, {"kind": "text", "onscreen": "Корпус из тополя\nгриф из клёна", "bg": "#1b2a1f"}),
        (3.5, {"kind": "card", "image": img["as100"], "onscreen": "Alston AS-100BK", "price": p["as100"]}),
        (3.5, {"kind": "text", "onscreen": CTA["text"], "bg": "#101418"}),
    ]), _caption(f"Alston AS-100BK: форма Stratocaster, датчики HSS, тополь и клён. {p['as100']}."), ["as100"]))

    h4 = f"Укулеле за {p['u246']}: что внутри?"
    scripts.append(S("price-2-caesar-u246", "price_point", h4, timed([
        (2.8, {"kind": "photo", "image": img["u246"], "onscreen": h4}),
        (3.4, {"kind": "text", "onscreen": "Верхняя дека — ель\nкорпус — красное дерево", "bg": "#14202b"}),
        (3.0, {"kind": "text", "onscreen": "Чехол в комплекте", "bg": "#1b2a1f"}),
        (3.5, {"kind": "card", "image": img["u246"], "onscreen": "Caesar U-246, концертное", "price": p["u246"]}),
        (3.5, {"kind": "text", "onscreen": CTA["text"], "bg": "#101418"}),
    ]), _caption(f"Концертное укулеле Caesar U-246: ель, красное дерево, чехол в комплекте. {p['u246']}."), ["u246"]))

    # ---- head-to-head ---------------------------------------------------------
    h5 = f"Два укулеле: {p['usc40']} против {p['uf330']}"
    scripts.append(S("vs-1-ukuleles", "vs", h5, timed([
        (3.0, {"kind": "split", "image": img["usc40"], "image2": img["uf330"], "price": p["usc40"], "price2": p["uf330"], "onscreen": h5}),
        (3.4, {"kind": "text", "onscreen": "Caesar US-C40:\nверхняя дека — массив ели", "bg": "#14202b"}),
        (3.4, {"kind": "text", "onscreen": "Alston UF-330:\nверхняя дека — клён", "bg": "#1b2a1f"}),
        (3.2, {"kind": "text", "onscreen": f"Разница в цене: {diff_uke}", "bg": "#2a1f14"}),
        (3.5, {"kind": "text", "onscreen": CTA["text"], "bg": "#101418"}),
    ]), _caption(f"Концертные укулеле Caesar US-C40 ({p['usc40']}) и Alston UF-330 ({p['uf330']}): разница в цене {diff_uke}."), ["usc40", "uf330"]))

    h6 = "Casio PX-770 или AP-270: чем отличаются?"
    scripts.append(S("vs-2-casio-pianos", "vs", h6, timed([
        (3.0, {"kind": "split", "image": img["px770"], "image2": img["ap270"], "price": p["px770"], "price2": p["ap270"], "onscreen": h6}),
        (3.2, {"kind": "text", "onscreen": "Клавиш: 88 и 88", "bg": "#14202b"}),
        (3.4, {"kind": "text", "onscreen": "Полифония:\n128 и 192 голоса", "bg": "#1b2a1f"}),
        (3.4, {"kind": "text", "onscreen": f"Разница в цене: {diff_pno}", "bg": "#2a1f14"}),
        (3.5, {"kind": "text", "onscreen": CTA["text"], "bg": "#101418"}),
    ]), _caption(f"Цифровые пианино Casio PX-770 ({p['px770']}) и Celviano AP-270 ({p['ap270']}): разница {diff_pno}."), ["px770", "ap270"]))

    # ---- policy (fear removal) -----------------------------------------------
    h7 = "14 дней на возврат: что нужно сохранить?"
    scripts.append(S("policy-1-returns", "policy", h7, timed([
        (3.0, {"kind": "text", "onscreen": h7, "bg": "#14202b"}),
        (3.6, {"kind": "text", "onscreen": "Товар не использовали,\nсохранили товарный вид", "bg": "#1b2a1f"}),
        (3.6, {"kind": "text", "onscreen": "Нужны упаковка, ярлыки\nи документ о покупке", "bg": "#14202b"}),
        (4.0, {"kind": "text", "onscreen": "Если товар без брака,\nудерживается доставка в оба конца", "bg": "#2a1f14"}),
        (3.5, {"kind": "text", "onscreen": CTA["text"], "bg": "#101418"}),
    ]), _caption("Возврат в течение 14 дней: товар не использован, сохранены товарный вид, упаковка, ярлыки и документ о покупке."), []))

    h8 = "Самовывоз: резерв заказа на 3 рабочих дня"
    scripts.append(S("policy-2-reserve", "policy", h8, timed([
        (3.0, {"kind": "text", "onscreen": h8, "bg": "#14202b"}),
        (3.4, {"kind": "text", "onscreen": "Оформили заказ —\nзабираете: Кажымукана, 14", "bg": "#1b2a1f"}),
        (3.6, {"kind": "text", "onscreen": "Не успели? Напишите —\nпродлим резерв", "bg": "#14202b"}),
        (3.8, {"kind": "text", "onscreen": "Оплата: Kaspi QR, Kaspi Pay,\nкарта или наличные при получении", "bg": "#2a1f14"}),
        (3.5, {"kind": "text", "onscreen": CTA["text"], "bg": "#101418"}),
    ]), _caption("Самовывоз в Астане: резерв заказа действует 3 рабочих дня, при необходимости продлим."), []))
    return scripts


def make_ledger(products_json: str | Path) -> tuple[Ledger, dict[str, dict]]:
    lg, recs = build_ledger(products_json, KEYS)
    lg.add(price_diff_fact("diff_uke", "usc40", recs["usc40"], "uf330", recs["uf330"]))
    lg.add(price_diff_fact("diff_pno", "px770", recs["px770"], "ap270", recs["ap270"]))
    return lg, recs


def qa(scripts: list[dict], lg: Ledger, recs: dict[str, dict], now: datetime) -> list[dict]:
    rows = []
    usable = lg.usable(now)
    for s in scripts:
        missing_stock = [k for k in s["products"] if f"{k}_instock" not in usable]
        vs = check_script(s, lg, now=now)
        rows.append({"id": s["id"], "arm": s["arm"], "hook": s["hook_spoken"],
                     "errors": [str(v) for v in errors(vs)]
                               + [f"STOCK: {k} has no usable in-stock fact" for k in missing_stock],
                     "warnings": [str(v) for v in vs if v.severity == "warn"]})
    return rows


def run(products_json: str, out_dir: str, now: datetime | None = None, render: bool = True) -> list[dict]:
    from .render import probe, render_video, tiktok_media_problems   # PIL only needed for rendering
    now = now or datetime.now(timezone.utc)
    out = Path(out_dir)
    (out / "scripts").mkdir(parents=True, exist_ok=True)
    (out / "drafts").mkdir(parents=True, exist_ok=True)
    lg, recs = make_ledger(products_json)
    lg.dump(out.parent / "facts.jsonl")
    scripts = build_scripts(recs)
    rows = qa(scripts, lg, recs, now)
    for s, row in zip(scripts, rows):
        (out / "scripts" / f"{s['id']}.json").write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
        row["render"] = None
        if render and not row["errors"]:
            info = render_video(s, out / "drafts" / f"{s['id']}.mp4", cache_dir=out.parent.parent.parent / ".render_cache")
            row["render"] = {**info, "platform_problems": tiktok_media_problems(info)}
    return rows
