import json
from datetime import datetime, timezone

from smm import acquire as A
from smm.checks import check_text
from smm.facts import Ledger

NOW = datetime(2026, 10, 9, 6, 0, tzinfo=timezone.utc)
PAGE = '''<html><script type="application/ld+json">{"@type":"Product","name":"Цифровое пианино Estrada EDP-220BK",
"offers":{"price":200720,"priceCurrency":"KZT","availability":"https://schema.org/InStock"}}</script>
<div class="stock"><span>В наличии:</span> 9 шт</div></html>'''


def client(tmp_path):
    d = tmp_path / "c"
    (d / "research").mkdir(parents=True)
    (d / "research" / "stock.json").write_text(json.dumps([
        {"url": "https://shop.kz/cifrovoe-pianino-estrada-edp-220bk.html", "name": "Цифровое пианино Estrada EDP-220BK"},
        {"url": "https://shop.kz/other.html", "name": "Гитара Alston AS-100BK"}], ensure_ascii=False), encoding="utf-8")
    return d


def test_known_product_price_is_fetched_instead_of_asked(tmp_path):
    d, lg = client(tmp_path), Ledger()
    hook = "Estrada EDP-220BK за 200 720 ₸: хватит ли для музыкалки?"
    assert check_text(hook, lg, now=NOW)                                   # not backed yet
    calls = []
    got = A.fill_facts(lg, d / "facts.jsonl", d, [hook], fetch=lambda u: calls.append(u) or PAGE, now=NOW)
    assert calls == ["https://shop.kz/cifrovoe-pianino-estrada-edp-220bk.html"]   # only the product mentioned
    assert not check_text(hook, lg, now=NOW)                               # now backed by a fresh, sourced fact
    assert not check_text("В наличии 9 шт", lg, now=NOW)
    saved = Ledger.load(d / "facts.jsonl")
    f = saved.facts["web_cifrovoe_pianino_estrada_edp_220bk_price"]
    assert f.source.endswith("edp-220bk.html") and f.provenance == "web" and f.ttl_days == 7     # price: 7 days
    assert saved.facts["web_cifrovoe_pianino_estrada_edp_220bk_qty"].ttl_days == 2                  # stock: 48 h
    assert set(got["added"]) >= {"web_cifrovoe_pianino_estrada_edp_220bk_price", "web_cifrovoe_pianino_estrada_edp_220bk_qty"}


def test_the_site_price_wins_over_the_idea(tmp_path):
    d, lg = client(tmp_path), Ledger()
    hook = "Estrada EDP-220BK за 180 000 ₸"                               # model guessed the price
    A.fill_facts(lg, None, d, [hook], fetch=lambda u: PAGE, now=NOW)
    assert check_text(hook, lg, now=NOW)                                   # still flagged -> owner question / fix


def test_fetch_failure_is_reported_not_raised(tmp_path):
    d, lg = client(tmp_path), Ledger()

    def boom(u):
        raise TimeoutError()
    got = A.fill_facts(lg, d / "facts.jsonl", d, ["Estrada EDP-220BK"], fetch=boom, now=NOW)
    assert got["added"] == [] and "TimeoutError" in got["failed"][0] and not (d / "facts.jsonl").exists()


def test_refetch_replaces_stale_fact(tmp_path):
    d, lg = client(tmp_path), Ledger()
    A.fill_facts(lg, None, d, ["Estrada EDP-220BK"], fetch=lambda u: PAGE, now=datetime(2026, 9, 1, tzinfo=timezone.utc))
    assert check_text("200 720 ₸", lg, now=NOW)                            # 7-day price TTL: stale by Oct 9
    A.fill_facts(lg, None, d, ["Estrada EDP-220BK"], fetch=lambda u: PAGE, now=NOW)
    assert not check_text("200 720 ₸", lg, now=NOW)


def test_shortened_model_code_still_matches_but_unrelated_text_does_not():
    idx = {"px-s1100bkc7": {"url": "u1", "name": "Casio Privia PX-S1100BKC7"}, "as-100bk": {"url": "u2", "name": "Alston AS-100BK"}}
    assert [r["url"] for r in A.mentioned(["Casio PX-S1100BK — для дома"], idx)] == ["u1"]
    assert A.mentioned(["Пианино за 300 тысяч: что внутри?"], idx) == []
