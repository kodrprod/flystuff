"""Getting data without asking anyone (problem #1, the agent side).

When an idea quotes a product's price or stock that the ledger cannot back yet, but the product is one the agent
already knows from its research files (a catalogue or stock crawl), the agent re-fetches that product page now and
adds fresh, sourced, dated facts to the ledger. Only what still cannot be backed becomes a question to the owner.

Generic: schema.org Product JSON-LD (most e-commerce platforms) plus the common "В наличии: N шт" stock line.
"""
from __future__ import annotations

import html as htmllib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .facts import Fact, Ledger
from .sources import _get, parse_jsonld_products, product_to_facts

STOCK_QTY = re.compile(r"В\s*наличии:?\s*(\d+)\s*шт", re.I)


def model_tokens(name: str) -> set[str]:
    """Tokens that identify a product: letters+digits (PX-770, EDP-220BK), at least 4 chars."""
    return {w.lower().strip(".,()\"'«»") for w in name.split()
            if re.search(r"[A-Za-z]", w) and re.search(r"\d", w) and len(w) >= 4}


def product_index(client_dir: Path) -> dict[str, dict]:
    """model token -> {url, name} from every research file that lists products."""
    idx: dict[str, dict] = {}
    for p in sorted((client_dir / "research").glob("*.json")) if (client_dir / "research").is_dir() else []:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        rows = data if isinstance(data, list) else [r for v in data.values() if isinstance(v, list) for r in v] \
            if isinstance(data, dict) else []
        for r in rows:
            if isinstance(r, dict) and r.get("url") and r.get("name"):
                for t in model_tokens(r["name"]):
                    idx.setdefault(t, {"url": r["url"], "name": r["name"]})
    return idx


def mentioned(texts: list[str], idx: dict[str, dict]) -> list[dict]:
    """Products whose model code appears in the texts. Copy often drops a colour suffix ("PX-S1100BK" for the
    catalogue's "PX-S1100BKC7"), so a text code of 5+ chars that starts a catalogue code also matches."""
    said = set()
    for t in texts:
        said |= model_tokens(t)
    seen, out = set(), []
    for tok, row in idx.items():
        hit = tok in said or any(len(s) >= 5 and (tok.startswith(s) or s.startswith(tok)) for s in said)
        if hit and row["url"] not in seen:
            seen.add(row["url"])
            out.append(row)
    return out


def key_for(url: str) -> str:
    base = url.rstrip("/").rsplit("/", 1)[-1].rsplit(".", 1)[0]
    return "web_" + re.sub(r"[^a-z0-9]+", "_", base.lower()).strip("_")[:60]


PRICE_TTL_DAYS, STOCK_TTL_DAYS = 7, 2      # method v1, ruling 12: prices <=7 days, stock <=48 h; re-fetched before publishing


def refresh(rows: list[dict], fetch=_get, now: datetime | None = None,
            ttl_days: int = STOCK_TTL_DAYS) -> tuple[list[Fact], list[str]]:
    now = now or datetime.now(timezone.utc)
    at = now.isoformat(timespec="seconds")
    facts, failed = [], []
    for row in rows:
        try:
            html = fetch(row["url"])
        except Exception as e:                                   # network, 404, block
            failed.append(f"{row['url']}: {type(e).__name__}")
            continue
        ps = parse_jsonld_products(html)
        if not ps:
            failed.append(f"{row['url']}: no product data on page")
            continue
        p = dict(ps[0])
        p["url"] = p.get("url") or row["url"]
        k = key_for(row["url"])
        for f in product_to_facts(k, p, at, ttl_days):
            if f.id.endswith("_price"):
                f.ttl_days = max(ttl_days, PRICE_TTL_DAYS)
            facts.append(f)
        text = htmllib.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>", " ", html, flags=re.S)))
        m = STOCK_QTY.search(text)
        if m:
            facts.append(Fact(f"{k}_qty", f"{p['name']}: в наличии {m.group(1)} шт (по данным сайта)", "web", p["url"],
                              at, values=[f"{m.group(1)} шт"], ttl_days=ttl_days))
    return facts, failed


def fill_facts(ledger: Ledger, ledger_path: Path | None, client_dir: Path, texts: list[str], fetch=_get,
               now: datetime | None = None) -> dict:
    """Refresh every known product the texts mention; replace older facts with the same id; save the ledger."""
    rows = mentioned(texts, product_index(client_dir))
    facts, failed = refresh(rows, fetch, now)
    for f in facts:
        ledger.facts.pop(f.id, None)
        ledger.add(f)
    if facts and ledger_path:
        ledger.dump(ledger_path)
    return {"products": [r["url"] for r in rows], "added": [f.id for f in facts], "failed": failed}
