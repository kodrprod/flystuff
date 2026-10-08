from datetime import datetime, timedelta, timezone

import pytest

from smm.checks import check_hook, check_script, check_shots, check_text, errors
from smm.facts import Fact, Ledger

NOW = datetime(2026, 10, 8, tzinfo=timezone.utc)
FRESH = "2026-10-08"


def ledger(**extra) -> Ledger:
    lg = Ledger([
        Fact("price_px770", "Casio PX-770 BKC7 — 695 913 ₸", "web", "https://muzzone.kz/x", FRESH,
             values=["695 913 ₸", "Casio PX-770"], ttl_days=3),
        Fact("returns", "Возврат в течение 14 дней", "web", "https://muzzone.kz/r", FRESH, values=["14 дней"]),
        Fact("wa", "WhatsApp", "web", "https://muzzone.kz/k", FRESH, values=["+7 701 0987734"]),
        Fact("ig", "Instagram", "web", "https://muzzone.kz/", FRESH, values=["@muzzone_astana"]),
        Fact("promo", "Возврат и обмен - без проблем!", "web", "https://muzzone.kz/p", FRESH,
             values=["без проблем"]),
    ])
    return lg


# --- hooks ---------------------------------------------------------------
def test_hook_eight_words_ok_nine_fails():
    ok = "раз два три четыре пять шесть семь восемь"
    assert not [v for v in check_hook(ok) if v.rule == "H1"]
    assert [v for v in check_hook(ok + " девять") if v.rule == "H1"]


def test_childish_games_blocked_in_hook_and_text():
    assert any(v.rule == "H2" for v in check_hook("Угадай, какая гитара дороже"))
    assert any(v.rule == "H2" for v in check_text("Пиши 1 или 2 в комментариях", ledger()))


def test_empty_hook_is_error():
    assert errors(check_hook("   "))


# --- numbers (R6) --------------------------------------------------------
def test_price_backed_by_ledger_passes_unbacked_fails():
    lg = ledger()
    assert not errors(check_text("Casio PX-770 стоит 695 913 ₸", lg, now=NOW))
    bad = errors(check_text("Casio PX-770 стоит 590 000 ₸", lg, now=NOW))
    assert bad and bad[0].rule == "R6-NUM"


def test_units_must_match():
    lg = ledger()
    assert not errors(check_text("Вернём деньги в течение 14 дней", lg, now=NOW))
    assert errors(check_text("Гарантия 14 месяцев", lg, now=NOW))   # 14 дней != 14 мес


def test_model_names_years_and_small_numbers_ignored():
    lg = ledger()
    assert not errors(check_text("PX-770 против X100 в 2026, три причины и 5 минут", lg, now=NOW))


def test_stale_price_fact_does_not_back_numbers():
    lg = ledger()
    later = NOW + timedelta(days=10)       # ttl_days=3
    assert errors(check_text("695 913 ₸", lg, now=later))


def test_simulated_fact_never_backs_text():
    lg = Ledger([Fact("s", "BOSS said price 100 000 ₸", "simulated", "[BOSS]", FRESH, values=["100 000 ₸"])])
    assert errors(check_text("Цена 100 000 ₸", lg, now=NOW))
    assert "simulated" in " ".join(lg.problems(lg.facts["s"], NOW))


def test_unsourced_web_fact_unusable():
    lg = Ledger([Fact("n", "x", "web", "", "", values=["500 ₸"])])
    assert errors(check_text("500 ₸", lg, now=NOW))


def test_do_not_use_fact_unusable():
    lg = Ledger([Fact("bad", "Steinberg 90% off", "web", "u", FRESH, values=["7 051 ₸"], do_not_use=True)])
    assert errors(check_text("всего 7 051 ₸", lg, now=NOW))


# --- claims / scarcity / contacts ----------------------------------------
def test_absolute_claims_need_backing():
    lg = ledger()
    assert errors(check_text("Это лучшая гитара для начинающих", lg, now=NOW))
    assert not errors(check_text("Возврат без проблем", lg, now=NOW))   # phrase is on the site


def test_scarcity_blocked():
    lg = ledger()
    for t in ["Только сегодня скидка", "Осталось 3 штуки", "Успей купить", "Закрываемся навсегда"]:
        assert errors(check_text(t, lg, now=NOW)), t


def test_contacts_must_be_in_ledger():
    lg = ledger()
    assert not errors(check_text("Пишите в WhatsApp +7 701 098 77 34", lg, now=NOW))
    assert errors(check_text("Звоните +7 777 123 45 67", lg, now=NOW))
    assert not errors(check_text("Instagram @muzzone_astana", lg, now=NOW))
    assert errors(check_text("Instagram @someone_else", lg, now=NOW))


# --- R5 ------------------------------------------------------------------
def test_r5_ai_shot_of_real_product_blocked():
    assert errors(check_shots([{"kind": "ai", "depicts": ["client_product"]}]))
    assert not errors(check_shots([{"kind": "ai", "depicts": ["abstract_background"]},
                                   {"kind": "real", "depicts": ["client_product"]}]))


# --- whole script --------------------------------------------------------
def good_script():
    return {
        "hook_spoken": "Casio PX-770: 695 913 ₸ — стоит ли?",
        "hook_onscreen": "PX-770 за 695 913 ₸",
        "beats": [{"onscreen": "PX-770 за 695 913 ₸", "spoken": "Возврат в течение 14 дней"},
                  {"onscreen": "14 дней на возврат"}],
        "caption": "Пишите в WhatsApp +7 701 0987734",
        "cta": {"text": "WhatsApp +7 701 0987734", "fact_id": "wa"},
        "shots": [{"kind": "real", "depicts": ["client_product"]}],
    }


def test_full_good_script_passes():
    assert not errors(check_script(good_script(), ledger(), now=NOW))


@pytest.mark.parametrize("mutate,rule", [
    (lambda s: s.update(cta={}), "R4-CTA"),
    (lambda s: s.update(cta={"text": "WhatsApp +7 701 0987734", "fact_id": "nope"}), "R4-CTA"),
    (lambda s: s.update(caption="Лучшие цены только у нас"), "R6-CLAIM"),
    (lambda s: s.update(shots=[{"kind": "ai", "depicts": ["client_product"]}]), "R5"),
    (lambda s: s["beats"].append({"spoken": "Всего 399 000 ₸"}), "R6-NUM"),
])
def test_script_violations_are_caught(mutate, rule):
    s = good_script()
    mutate(s)
    assert rule in {v.rule for v in errors(check_script(s, ledger(), now=NOW))}


def test_grouped_price_counts_as_one_word_in_hook():
    # 8 words as a viewer reads them, though 10+ whitespace tokens
    assert not [v for v in check_hook("Комбик 30 Вт: было 70 720 ₸, стало 56 576 ₸") if v.rule == "H1"]


def test_card_price_fields_are_checked():
    s = good_script()
    s["beats"].append({"kind": "card", "onscreen": "Гитара", "price": "12 345 ₸"})
    assert any(v.rule == "R6-NUM" and "price" in v.where for v in errors(check_script(s, ledger(), now=NOW)))


def test_first_beat_must_show_hook_text():
    s = good_script()
    s["beats"][0]["onscreen"] = "что-то другое"
    assert "H5" in {v.rule for v in errors(check_script(s, ledger(), now=NOW))}
