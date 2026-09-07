#!/usr/bin/env python3
"""Brengt de hoofdpagina's (index + pillars) op orde.

  * interne links naar schone URL's (zonder .html)
  * canonical, og:url en schema-url gelijktrekken op de schone URL
  * navigatie: "Nieuws" -> /nieuws, nieuw item "Terugleverkosten"
  * footer: "Over ons" wijst naar de echte pagina
  * BreadcrumbList-schema op de categoriepagina's
  * markeringen in index.html zodat agent.py de artikellijst kan bijwerken
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools import lib
from tools.fix_articles import ARTICLE_HREF, ABS_ARTICLE_URL

PAGES = {
    "index.html": ("/", "Home"),
    "regelgeving.html": ("/regelgeving", "Regelgeving"),
    "thuisbatterijen.html": ("/thuisbatterijen", "Thuisbatterijen"),
    "subsidies.html": ("/subsidies", "Subsidies"),
    "contracten.html": ("/contracten", "Contracten"),
    "faq.html": ("/faq", "FAQ"),
    "privacy.html": ("/privacy", "Privacy"),
}

NAV_ITEM = '<a href="/terugleverkosten">Terugleverkosten</a>'
NAV_CSS = ("\n        .nav-inner{overflow-x:auto;scrollbar-width:none}"
           "\n        .nav-inner::-webkit-scrollbar{display:none}"
           "\n        .nav-inner a{white-space:nowrap}\n")


def relink(html: str) -> str:
    html = ARTICLE_HREF.sub(
        lambda m: f"{m.group('pre')}{m.group('q')}/articles/{m.group('slug')}{m.group('q')}",
        html)
    html = ABS_ARTICLE_URL.sub(lambda m: f"{lib.BASE_URL}/articles/{m.group('slug')}", html)
    for page in ("contracten", "regelgeving", "subsidies", "faq",
                 "thuisbatterijen", "privacy", "index"):
        target = "/" if page == "index" else f"/{page}"
        html = re.sub(rf"(href=[\'\"])/?{page}\.html", rf"\g<1>{target}", html)
    return html


def fix_nav(html: str) -> str:
    html = re.sub(r'<a href="/"(?: class="active")?>Nieuws</a>',
                  '<a href="/nieuws">Nieuws</a>', html)
    if NAV_ITEM not in html:
        html = re.sub(r'(<a href="/contracten"[^>]*>Contracten</a>)',
                      r"\1\n            " + NAV_ITEM, html, count=1)
    html = re.sub(r'<a href="#over-ons">Over ons</a>',
                  '<a href="/over-ons">Over ons</a>', html)
    if 'href="/over-ons"' not in html:
        html = html.replace('<a href="mailto:info@salderingsupdate.nl">Contact</a>',
                            '<a href="/over-ons">Over ons</a>\n'
                            '            <a href="mailto:info@salderingsupdate.nl">Contact</a>')
    if ".nav-inner{overflow-x:auto" not in html:
        html = html.replace("</style>", NAV_CSS + "    </style>", 1)
    return html


def fix_head(html: str, path: str) -> str:
    url = f"{lib.BASE_URL}{path}" if path != "/" else f"{lib.BASE_URL}/"
    html = re.sub(r'<link rel="canonical" href="[^"]*">',
                  f'<link rel="canonical" href="{url}">', html)
    html = re.sub(r'<meta property="og:url" content="[^"]*">',
                  f'<meta property="og:url" content="{url}">', html)
    return html


def fix_schema(html: str, path: str, label: str) -> str:
    url = f"{lib.BASE_URL}{path}" if path != "/" else f"{lib.BASE_URL}/"
    blocks = list(re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S))
    for m in reversed(blocks):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("@type") in ("WebPage", "WebSite", "CollectionPage"):
            data["url"] = url
            data["inLanguage"] = "nl-NL"
            new = ('<script type="application/ld+json">\n'
                   + json.dumps(data, ensure_ascii=False, indent=2) + "\n</script>")
            html = html[:m.start()] + new + html[m.end():]

    if path not in ("/", "/privacy") and '"BreadcrumbList"' not in html:
        crumbs = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{lib.BASE_URL}/"},
                {"@type": "ListItem", "position": 2, "name": label, "item": url},
            ],
        }
        html = html.replace("</head>",
                            '<script type="application/ld+json">\n'
                            + json.dumps(crumbs, ensure_ascii=False, indent=2)
                            + "\n</script>\n</head>", 1)
    return html


def add_index_markers(html: str) -> str:
    """Plaatst de markeringen waar agent.py de artikellijst tussen schrijft."""
    if "ARTICLE_LIST_START" in html:
        return html
    m = re.search(r'(<div class="section-head">\s*<h2>Recente artikelen</h2>\s*</div>)(.*?)'
                  r'(\s*</div>\s*<aside)', html, re.S)
    if not m:
        print("  let op: artikellijst in index.html niet herkend — markeringen niet geplaatst")
        return html
    return (html[:m.end(1)]
            + "\n                <!-- ARTICLE_LIST_START -->"
            + m.group(2).rstrip()
            + "\n                <!-- ARTICLE_LIST_END -->"
            + html[m.end(2):])


def main() -> int:
    changed = 0
    for filename, (path, label) in PAGES.items():
        f = lib.SITE_DIR / filename
        if not f.exists():
            continue
        original = f.read_text(encoding="utf-8")
        html = fix_head(original, path)
        html = fix_schema(html, path, label)
        html = fix_nav(html)
        html = relink(html)
        if filename == "index.html":
            html = add_index_markers(html)
        if html != original:
            f.write_text(html, encoding="utf-8")
            changed += 1
            print(f"  bijgewerkt: {filename}")
    print(f"{changed} pagina's bijgewerkt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
