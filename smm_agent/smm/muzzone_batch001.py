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
    """Motion-first scripts (about 10-12 s). Every shot is <= ~2.8 s and starts with a visible change."""
    img = {k: v["images"][0] for k, v in r.items()}
    p = {k: kzt(v["price"]) for k, v in r.items()}
    old = {k: kzt(v["old_price"]) for k, v in r.items() if v.get("old_price")}
    diff_uke = kzt(abs(r["uf330"]["price"] - r["usc40"]["price"]))
    diff_pno = kzt(abs(r["ap270"]["price"] - r["px770"]["price"]))

    def S(id, arm, hook, beats, caption, products, floor=False):
        return {"id": id, "arm": arm, "products": products, "hook_spoken": hook, "hook_onscreen": hook,
                "beats": beats, "caption": caption, "cta": CTA, "shots": REAL_PHOTO, "is_aigc": False,
                "audio": "synthesised SFX only; publisher adds licensed/trending music",
                "tier": "floor: replace with real worker footage when available" if floor else "motion graphics from real photos"}

    def timed(beats):
        t, out = 0.0, []
        for dur, b in beats:
            out.append({"t0": round(t, 2), "t1": round(t + dur, 2), **b})
            t += dur
        return out

    cta = (2.2, {"kind": "kinetic", "onscreen": CTA["text"], "palette": 0})
    sc = []
    # ---- sale ---------------------------------------------------------------
    h = f"Комбик 30 Вт: было {old['hib']}, стало {p['hib']}"
    sc.append(S("sale-1-hibilly", "sale", h, timed([
        (1.1, {"kind": "hook", "image": img["hib"], "onscreen": h}),
        (2.4, {"kind": "cuts", "image": img["hib"], "texts": ["Hibilly Retro 30R", "Транзисторный", "30 Вт"]}),
        (2.8, {"kind": "pricedrop", "image": img["hib"], "old_price": old["hib"], "price": p["hib"], "badge": "-20%", "onscreen": "Hibilly Retro 30R"}),
        (1.6, {"kind": "kinetic", "onscreen": "Скидка 20%\nна распродаже muzzone.kz", "palette": 1}), cta,
    ]), _caption(f"Комбоусилитель Hibilly Retro 30R: {p['hib']} вместо {old['hib']} на распродаже."), ["hib"]))

    h = f"Ударная установка Mapex: {p['mapex']} вместо {old['mapex']}"
    sc.append(S("sale-2-mapex", "sale", h, timed([
        (1.1, {"kind": "hook", "image": img["mapex"], "onscreen": h}),
        (2.4, {"kind": "cuts", "image": img["mapex"], "texts": ["Mapex Comet", "5 барабанов", "Корпус из тополя"]}),
        (2.8, {"kind": "pricedrop", "image": img["mapex"], "old_price": old["mapex"], "price": p["mapex"], "badge": "-20%", "onscreen": "Mapex Comet CM5295"}),
        (1.6, {"kind": "kinetic", "onscreen": "Скидка 20%\nна распродаже muzzone.kz", "palette": 1}), cta,
    ]), _caption(f"Ударная установка Mapex Comet CM5295: {p['mapex']} вместо {old['mapex']} на распродаже."), ["mapex"]))

    # ---- price point ----------------------------------------------------------
    h = f"Электрогитара за {p['as100']}: что получаешь?"
    sc.append(S("price-1-alston-as100", "price_point", h, timed([
        (1.1, {"kind": "hook", "image": img["as100"], "onscreen": h}),
        (2.6, {"kind": "cuts", "image": img["as100"], "texts": ["Alston AS-100BK", "Форма Stratocaster", "Датчики HSS"]}),
        (1.8, {"kind": "kinetic", "onscreen": "Корпус из тополя\nгриф из клёна", "palette": 1}),
        (1.8, {"kind": "hook", "image": img["as100"], "onscreen": f"Alston AS-100BK {p['as100']}"}), cta,
    ]), _caption(f"Alston AS-100BK: форма Stratocaster, датчики HSS, тополь и клён. {p['as100']}."), ["as100"]))

    h = f"Укулеле за {p['u246']}: что внутри?"
    sc.append(S("price-2-caesar-u246", "price_point", h, timed([
        (1.1, {"kind": "hook", "image": img["u246"], "onscreen": h}),
        (2.6, {"kind": "cuts", "image": img["u246"], "texts": ["Caesar U-246", "Верхняя дека — ель", "Красное дерево"]}),
        (1.8, {"kind": "kinetic", "onscreen": "Чехол в комплекте", "palette": 1}),
        (1.8, {"kind": "hook", "image": img["u246"], "onscreen": f"Caesar U-246 {p['u246']}"}), cta,
    ]), _caption(f"Концертное укулеле Caesar U-246: ель, красное дерево, чехол в комплекте. {p['u246']}."), ["u246"]))

    # ---- head-to-head ---------------------------------------------------------
    h = f"Два укулеле: {p['usc40']} против {p['uf330']}"
    sc.append(S("vs-1-ukuleles", "vs", h, timed([
        (1.4, {"kind": "versus", "image": img["usc40"], "image2": img["uf330"], "price": p["usc40"], "price2": p["uf330"], "onscreen": h}),
        (2.2, {"kind": "stat", "label": "Верхняя дека", "left": "Массив ели", "right": "Клён", "left_name": "Caesar\nUS-C40", "right_name": "Alston\nUF-330", "palette": 1}),
        (1.8, {"kind": "kinetic", "onscreen": f"Разница в цене:\n{diff_uke}", "palette": 2}), cta,
    ]), _caption(f"Концертные укулеле Caesar US-C40 ({p['usc40']}) и Alston UF-330 ({p['uf330']}): разница в цене {diff_uke}."), ["usc40", "uf330"]))

    h = "Casio PX-770 или AP-270: чем отличаются?"
    sc.append(S("vs-2-casio-pianos", "vs", h, timed([
        (1.4, {"kind": "versus", "image": img["px770"], "image2": img["ap270"], "price": p["px770"], "price2": p["ap270"], "onscreen": h}),
        (2.0, {"kind": "stat", "label": "Клавиш", "left": "88", "right": "88", "left_name": "PX-770", "right_name": "AP-270", "palette": 3}),
        (2.2, {"kind": "stat", "label": "Полифония, голосов", "left": "128", "right": "192", "left_name": "PX-770", "right_name": "AP-270", "palette": 1}),
        (1.8, {"kind": "kinetic", "onscreen": f"Разница в цене:\n{diff_pno}", "palette": 2}), cta,
    ]), _caption(f"Цифровые пианино Casio PX-770 ({p['px770']}) и Celviano AP-270 ({p['ap270']}): разница {diff_pno}."), ["px770", "ap270"]))

    # ---- policy (floor tier: best made with a real person on camera) -------------
    h = "14 дней на возврат: что нужно сохранить?"
    sc.append(S("policy-1-returns", "policy", h, timed([
        (1.8, {"kind": "kinetic", "onscreen": h, "palette": 0}),
        (1.8, {"kind": "kinetic", "onscreen": "Товар не использовали,\nсохранили товарный вид", "palette": 1}),
        (1.8, {"kind": "kinetic", "onscreen": "Нужны упаковка, ярлыки\nи документ о покупке", "palette": 3}),
        (2.2, {"kind": "kinetic", "onscreen": "Если товар без брака,\nудерживается доставка в оба конца", "palette": 2}), cta,
    ]), _caption("Возврат в течение 14 дней: товар не использован, сохранены товарный вид, упаковка, ярлыки и документ о покупке."), [], floor=True))

    h = "Самовывоз: резерв заказа на 3 рабочих дня"
    sc.append(S("policy-2-reserve", "policy", h, timed([
        (1.8, {"kind": "kinetic", "onscreen": h, "palette": 0}),
        (1.8, {"kind": "kinetic", "onscreen": "Оформили заказ —\nзабираете: Кажымукана, 14", "palette": 1}),
        (1.8, {"kind": "kinetic", "onscreen": "Не успели? Напишите —\nпродлим резерв", "palette": 3}),
        (2.2, {"kind": "kinetic", "onscreen": "Оплата: Kaspi QR, Kaspi Pay,\nкарта или наличные при получении", "palette": 2}), cta,
    ]), _caption("Самовывоз в Астане: резерв заказа действует 3 рабочих дня, при необходимости продлим."), [], floor=True))
    return sc


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
    from .pacing import analyze_pacing
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
            pace = analyze_pacing(out / "drafts" / f"{s['id']}.mp4")
            row["render"] = {**info, "platform_problems": tiktok_media_problems(info),
                             "pacing_problems": pace["problems"], "first2_motion": round(pace["first2_motion"], 2),
                             "events": pace["n_events"], "tier": s["tier"]}
    return rows
