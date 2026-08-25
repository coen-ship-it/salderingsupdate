#!/usr/bin/env python3
"""Herbouwt articles.json op basis van de HTML-bestanden in articles/.

De index liep uit de pas met de bestanden op schijf (17 vs 21). Dit script
leest titel, samenvatting, datum en categorie uit elk artikel en schrijft een
volledige, gesorteerde index terug.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools import lib

# Vaste categorienamen — één schrijfwijze per categorie.
CANONICAL = {
    "batterijen": "Thuisbatterijen", "thuisbatterijen": "Thuisbatterijen",
    "subsidie": "Subsidies", "subsidies": "Subsidies",
    "regelgeving": "Regelgeving", "analyse": "Regelgeving",
    "contracten": "Contracten", "netcongestie": "Netcongestie",
    "vergoeding": "Vergoeding", "terugleverkosten": "Terugleverkosten",
}

# Categorie afleiden uit de slug wanneer het artikel er zelf geen bruikbare noemt.
CATEGORY_RULES = [
    (r"thuisbatterij|batterij|capaciteit|opslag", "Thuisbatterijen"),
    (r"subsidie|isde|sde",                       "Subsidies"),
    (r"terugleverkosten",                        "Terugleverkosten"),
    (r"terugleververgoeding|vergoeding",         "Vergoeding"),
    (r"contract|dynamisch",                      "Contracten"),
    (r"netcongestie",                            "Netcongestie"),
    (r"salderings|afbouw|regeling|rendabel",     "Regelgeving"),
]


def category_for(slug: str, html: str) -> str:
    m = re.search(r'<div class="article-meta">(.*?)</div>', html, re.S)
    if m:
        spans = re.findall(r"<span>([^<]*)</span>", m.group(1))
        for raw in spans:
            key = raw.strip().lower()
            if key in CANONICAL:
                return CANONICAL[key]
    for pattern, cat in CATEGORY_RULES:
        if re.search(pattern, slug):
            return cat
    return "Regelgeving"


def main() -> int:
    existing = {a.get("file", "").rsplit("/", 1)[-1].removesuffix(".html"): a
                for a in lib.load_articles()}

    articles = []
    for path in lib.article_files():
        slug = lib.slug_from_path(path)
        html = path.read_text(encoding="utf-8")
        d = lib.date_from_slug(slug)
        prev = existing.get(slug, {})

        title = lib.h1(html) or prev.get("title", "")
        summary = (lib.summary_text(html)
                   or lib.meta_content(html, name="description")
                   or prev.get("summary", ""))

        ld = lib.first_ld_json(html) or {}
        source_label = prev.get("source_label", "")
        source_url = prev.get("source_url", "")
        if not source_label:
            m = re.search(r'<div class="article-source">.*?<a href="([^"]+)"[^>]*>(.*?)</a>',
                          html, re.S)
            if m:
                source_url, source_label = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()

        articles.append({
            "title": title,
            "slug": re.sub(r"^\d{4}-\d{2}-\d{2}-", "", slug),
            "category": category_for(slug, html),
            "date": d.isoformat(),
            "date_display": lib.date_display(d),
            "date_short": lib.date_short(d),
            "updated": ld.get("dateModified", d.isoformat())[:10],
            "summary": summary,
            "file": f"articles/{slug}.html",
            "url": lib.article_url(slug),
            "source_label": source_label,
            "source_url": source_url,
        })

    articles.sort(key=lambda a: (a["date"], a["slug"]), reverse=True)
    lib.save_articles(articles)
    print(f"articles.json herbouwd: {len(articles)} artikelen "
          f"({articles[-1]['date']} t/m {articles[0]['date']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
