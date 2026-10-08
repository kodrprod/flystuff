"""Data ingestion (problem #1): turn whatever a client can give into ledger facts and signals.

Sources, ordered by yield per minute of the client's time:
  SiteSource        client's own public site: sitemap + schema.org JSON-LD products + policy pages  (0 min)
  ChannelSource     public channel stats (YouTube flat listing; others need OAuth)                   (0 min)
  upload parsers    sales / stock exports (CSV from 1C, Excel, Kaspi cabinet...)                     (~2 min once)
  (planned)         staff voice notes -> speech-to-text; platform APIs via one-time OAuth

Everything returns plain objects with provenance (source + date); nothing here decides content.
Network functions are thin; the parsers are pure and tested offline.
"""
from __future__ import annotations

import csv
import io
import json
import re
import statistics as st
import subprocess
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .facts import Fact

UA = "MetaPromptSMM-research/0.1 (polite, <=2 req/s)"
POLICY_HINTS = ("garant", "vozvrat", "return", "dostavka", "delivery", "oplata", "payment", "about", "o-nas",
                "kontakt", "contact", "faq", "uslovi", "terms", "rassrochk", "kredit")


@dataclass
class Signal:
    """Something observed about demand, competitors or trends. Never a client fact."""
    id: str
    kind: str                 # audience_words | trend | competitor | performance | inventory | sales
    text: str
    source: str
    fetched_at: str
    confidence: str = "low"   # low | medium | high — how far this should steer decisions
    metrics: dict = field(default_factory=dict)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _get(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


# ------------------------------------------------------------------ site (schema.org)
def parse_sitemap(xml: str) -> tuple[list[str], list[str]]:
    """Returns (child_sitemaps, page_urls)."""
    locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml)
    if "<sitemapindex" in xml:
        return locs, []
    return [], locs


def split_urls(urls: list[str]) -> dict[str, list[str]]:
    """Policy-like pages vs the rest; Kazakh/other-language duplicates (/kk/, /en/) are dropped."""
    out = {"policy": [], "other": []}
    for u in urls:
        if re.search(r"/(kk|en|uz|ky)/", u):
            continue
        out["policy" if any(h in u.lower() for h in POLICY_HINTS) else "other"].append(u)
    return out


def parse_jsonld_products(html: str) -> list[dict]:
    """All schema.org Product records on a page (works on most e-commerce platforms)."""
    out = []
    for b in re.findall(r"application/ld\+json[^>]*>(.*?)</script>", html, re.S):
        try:
            j = json.loads(b)
        except ValueError:
            continue
        for node in (j if isinstance(j, list) else j.get("@graph", [j])):
            if isinstance(node, dict) and node.get("@type") in ("Product", ["Product"]):
                offers = node.get("offers") or {}
                o = offers[0] if isinstance(offers, list) and offers else offers
                rating = node.get("aggregateRating") or {}
                out.append({
                    "name": node.get("name"), "sku": node.get("sku"),
                    "brand": (node.get("brand") or {}).get("name") if isinstance(node.get("brand"), dict) else node.get("brand"),
                    "price": o.get("price"), "currency": o.get("priceCurrency"),
                    "availability": (o.get("availability") or "").rsplit("/", 1)[-1] or None,
                    "rating": rating.get("ratingValue"), "review_count": rating.get("reviewCount"),
                    "url": node.get("url") or o.get("url"),
                })
    return out


def product_to_facts(key: str, p: dict, fetched_at: str, ttl_days: int = 2) -> list[Fact]:
    facts = []
    if p.get("price") is not None:
        facts.append(Fact(f"{key}_price", f"{p['name']} — {p['price']} {p.get('currency') or ''}".strip(), "web",
                          p.get("url") or "", fetched_at, values=[f"{int(float(p['price'])):,}".replace(",", " ")],
                          ttl_days=ttl_days))
    if p.get("availability") == "InStock":
        facts.append(Fact(f"{key}_instock", f"{p['name']}: в наличии по данным сайта", "web", p.get("url") or "",
                          fetched_at, ttl_days=ttl_days))
    return facts


# ------------------------------------------------------------------ public channel stats
def parse_ytdlp_flat(json_text: str) -> dict:
    """yt-dlp --flat-playlist -J output -> channel summary + rows (pos 0 = newest)."""
    d = json.loads(json_text)
    rows = [{"id": e.get("id"), "pos": i, "title": e.get("title") or "", "views": e.get("view_count"),
             "duration": e.get("duration")} for i, e in enumerate(e for e in d.get("entries", []) if e)]
    views = [r["views"] for r in rows if r["views"] is not None]
    return {"channel": d.get("channel") or d.get("title"), "followers": d.get("channel_follower_count"),
            "n": len(rows), "median_views": st.median(views) if views else None, "videos": rows}


def fetch_channel(url: str, end: int = 200, ytdlp: str = "yt-dlp") -> dict:
    r = subprocess.run([ytdlp, "--skip-download", "--no-warnings", "--flat-playlist", "--playlist-end", str(end), "-J", url],
                       capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {r.stderr[-300:]}")
    return parse_ytdlp_flat(r.stdout)


def channel_signals(summary: dict, source: str, fetched_at: str, top_k: int = 3) -> list[Signal]:
    med = summary.get("median_views")
    rows = [r for r in summary["videos"] if r["views"] is not None]
    out = []
    if med:
        for r in sorted(rows, key=lambda r: -r["views"])[:top_k]:
            out.append(Signal(f"top_{r['id']}", "performance", f"{r['title']} — {r['views']} просмотров (медиана канала {int(med)})",
                              source, fetched_at, "medium", {"views": r["views"], "x_median": round(r["views"] / med, 1)}))
    return out


# ------------------------------------------------------------------ client uploads (CSV)
ALIASES = {
    "sku": ["sku", "артикул", "код", "код товара", "article"],
    "name": ["name", "название", "наименование", "товар", "product"],
    "qty_sold": ["sold", "продано", "кол-во продаж", "количество продаж", "qty_sold", "units"],
    "revenue": ["revenue", "выручка", "сумма", "сумма продаж", "amount"],
    "stock": ["stock", "остаток", "остатки", "в наличии", "qty", "количество"],
    "price": ["price", "цена"],
}


def _norm_header(h: str) -> str:
    return re.sub(r"\s+", " ", h.strip().lower())


def _num(s: str) -> float:
    """Parse a number from an export cell. Cells with no digits are an error, never 0."""
    raw = str(s).replace("\xa0", "").replace(" ", "")
    if not re.search(r"\d", raw):
        raise ValueError(f"not a number: {str(s)!r}")
    s = re.sub(r"[^\d,.\-]", "", raw).replace(",", ".")
    if s.count(".") > 1:                    # "1.234.567" -> thousands separators
        s = s.replace(".", "")
    return float(s)


def parse_export_csv(text: str) -> tuple[list[dict], list[str]]:
    """Sales/stock export with RU or EN headers, ; or , delimited. Returns (rows, problems).
    Unrecognised columns are ignored; unparsable rows are reported, never guessed."""
    sample = text[:2000]
    delim = ";" if sample.count(";") > sample.count(",") else ","
    rd = csv.reader(io.StringIO(text.strip()), delimiter=delim)
    try:
        header = next(rd)
    except StopIteration:
        return [], ["empty file"]
    col = {}
    for i, h in enumerate(header):
        for canon, names in ALIASES.items():
            if _norm_header(h) in names and canon not in col:
                col[canon] = i
    if "name" not in col and "sku" not in col:
        return [], [f"no product column (sku/name) in header {header}"]
    rows, problems = [], []
    for ln, r in enumerate(rd, start=2):
        if not any(c.strip() for c in r):
            continue
        try:
            row = {k: (r[i].strip() if k in ("sku", "name") else _num(r[i]))
                   for k, i in col.items() if i < len(r) and r[i].strip()}     # empty cell = field absent, not 0
            rows.append(row)
        except ValueError as e:
            problems.append(f"line {ln}: {e}")
    return rows, problems


def sales_signals(rows: list[dict], source: str, fetched_at: str, top_k: int = 5) -> list[Signal]:
    """Best/worst sellers by units (or revenue). These steer what to feature, with client-level confidence."""
    key = "qty_sold" if rows and "qty_sold" in rows[0] else "revenue"
    ranked = [r for r in rows if key in r]
    ranked.sort(key=lambda r: -r[key])
    label = lambda r: r.get("name") or r.get("sku")
    out = [Signal(f"best_{i}", "sales", f"Хорошо продаётся: {label(r)} ({r[key]:g})", source, fetched_at, "high", {key: r[key]})
           for i, r in enumerate(ranked[:top_k])]
    out += [Signal(f"worst_{i}", "sales", f"Плохо продаётся: {label(r)} ({r[key]:g})", source, fetched_at, "high", {key: r[key]})
            for i, r in enumerate(ranked[-top_k:])]
    return out


def stock_facts(rows: list[dict], source: str, fetched_at: str, ttl_days: int = 1) -> list[Fact]:
    out = []
    for i, r in enumerate(rows):
        if "stock" in r and (r.get("name") or r.get("sku")):
            k = re.sub(r"\W+", "_", str(r.get("sku") or r["name"]))[:40] or f"row{i}"
            if r["stock"] > 0:
                out.append(Fact(f"stock_{k}", f"{r.get('name') or r.get('sku')}: в наличии (выгрузка клиента)", "client", source,
                                fetched_at, ttl_days=ttl_days))
    return out
