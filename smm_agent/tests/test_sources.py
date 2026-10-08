import json

from smm import sources as S

SITEMAP_INDEX = '<?xml version="1.0"?><sitemapindex><sitemap><loc>https://x.kz/products1.xml</loc></sitemap><sitemap><loc>https://x.kz/pages1.xml</loc></sitemap></sitemapindex>'
URLSET = '<urlset><url><loc>https://x.kz/a.html</loc></url><url><loc>https://x.kz/kk/a.html</loc></url><url><loc>https://x.kz/garantii-i-vozvrat.html</loc></url><url><loc>https://x.kz/dostavka-i-oplata.html</loc></url></urlset>'


def test_sitemap_index_vs_urlset_and_language_duplicates_dropped():
    kids, pages = S.parse_sitemap(SITEMAP_INDEX)
    assert kids == ["https://x.kz/products1.xml", "https://x.kz/pages1.xml"] and pages == []
    kids, pages = S.parse_sitemap(URLSET)
    split = S.split_urls(pages)
    assert split["other"] == ["https://x.kz/a.html"] and len(split["policy"]) == 2


LD = '''<script type="application/ld+json">{"@context":"https://schema.org","@type":"Product","name":"Гитара X","sku":"X1",
"brand":{"@type":"Brand","name":"Cort"},"offers":[{"@type":"Offer","availability":"https://schema.org/InStock","price":98280,
"priceCurrency":"KZT","url":"https://x.kz/g"}],"aggregateRating":{"ratingValue":5,"reviewCount":1}}</script>
<script type="application/ld+json">{"@graph":[{"@type":"Organization","name":"X"},{"@type":"Product","name":"Y","offers":{"price":"100.5"}}]}</script>
<script type="application/ld+json">{ broken json </script>'''


def test_jsonld_products_incl_graph_and_broken_blocks():
    ps = S.parse_jsonld_products(LD)
    assert [p["name"] for p in ps] == ["Гитара X", "Y"]
    assert ps[0]["price"] == 98280 and ps[0]["availability"] == "InStock" and ps[0]["brand"] == "Cort"
    facts = S.product_to_facts("g", ps[0], "2026-10-08")
    assert {f.id for f in facts} == {"g_price", "g_instock"} and facts[0].ttl_days == 2


def test_ytdlp_flat_summary_and_signals():
    raw = json.dumps({"channel": "Shop", "channel_follower_count": 1000, "entries": [
        {"id": "a", "title": "Hit", "view_count": 9000, "duration": 30}, None,
        {"id": "b", "title": "Meh", "view_count": 100, "duration": 20}, {"id": "c", "title": "Mid", "view_count": 500}]})
    s = S.parse_ytdlp_flat(raw)
    assert s["n"] == 3 and s["median_views"] == 500 and s["followers"] == 1000
    assert [v["id"] for v in s["videos"]] == ["a", "b", "c"] and [v["pos"] for v in s["videos"]] == [0, 1, 2]   # None entry skipped
    assert s["videos"][2]["duration"] is None
    sig = S.channel_signals(s, "https://yt/x", "2026-10-08", top_k=1)
    assert sig[0].metrics["x_median"] == 18.0 and sig[0].kind == "performance"


CSV_RU = """Артикул;Название;Продано;Остаток;Цена
A1;Гитара Alston;12;3;59 800
A2;Укулеле Caesar;7;0;22 100
A3;Струны Dunlop;40;100;3 136
A4;Плохая строка;abc;1;1
"""


def test_csv_russian_headers_semicolon_and_bad_rows_reported():
    rows, problems = S.parse_export_csv(CSV_RU)
    assert [r["sku"] for r in rows] == ["A1", "A2", "A3"] and rows[0]["price"] == 59800 and rows[2]["qty_sold"] == 40
    assert len(problems) == 1 and "line 5" in problems[0]


def test_csv_without_product_column_is_rejected_not_guessed():
    rows, problems = S.parse_export_csv("a,b\n1,2\n")
    assert rows == [] and "no product column" in problems[0]


def test_sales_signals_and_stock_facts():
    rows, _ = S.parse_export_csv(CSV_RU)
    sig = S.sales_signals(rows, "sales.csv", "2026-10-08", top_k=1)
    assert sig[0].text.startswith("Хорошо продаётся: Струны Dunlop") and sig[-1].text.startswith("Плохо продаётся: Укулеле")
    assert all(s.confidence == "high" for s in sig)
    facts = S.stock_facts(rows, "sales.csv", "2026-10-08")
    assert {f.id for f in facts} == {"stock_A1", "stock_A3"}          # A2 has 0 in stock
    assert all(f.provenance == "client" and f.ttl_days == 1 for f in facts)


def test_thousands_separators():
    assert S._num("1.234.567") == 1234567 and S._num("1 234,5") == 1234.5 and S._num("59 800") == 59800
