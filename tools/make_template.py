#!/usr/bin/env python3
"""Bouwt artikel.html (de Jinja2-template voor agent.py) uit een echt artikel.

De oude template stond op `noindex, nofollow`, had geen canonical, geen schema
en geen navigatie, en verwees met relatieve links naar index.html vanuit
/articles/. Elk artikel dat de agent zou genereren was daarmee onzichtbaar voor
Google en visueel losgeknipt van de rest van de site.

Door de template uit een bestaand artikel af te leiden blijven vormgeving en
opmaak automatisch in de pas lopen met de rest van de site.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools import lib

BASE = lib.ARTICLES_DIR / "2026-03-01-terugleververgoeding-2026-vergelijking.html"
OUT = lib.SITE_DIR / "artikel.html"

ARTICLE_SCHEMA = """<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "headline": {{ title | tojson }},
  "description": {{ meta_description | tojson }},
  "url": "https://salderingsupdate.nl/articles/{{ slug }}",
  "mainEntityOfPage": {"@type": "WebPage", "@id": "https://salderingsupdate.nl/articles/{{ slug }}"},
  "datePublished": "{{ date_iso }}",
  "dateModified": "{{ updated_iso }}",
  "articleSection": {{ category | tojson }},
  "inLanguage": "nl-NL",
  "image": "https://salderingsupdate.nl/og-image.png",
  "author": {"@type": "Person", "name": {{ author | tojson }}, "url": "https://salderingsupdate.nl/over-ons"},
  "publisher": {
    "@type": "Organization",
    "name": "SalderingsUpdate.nl",
    "url": "https://salderingsupdate.nl/",
    "logo": {"@type": "ImageObject", "url": "https://salderingsupdate.nl/og-image.png"}
  }
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://salderingsupdate.nl/"},
    {"@type": "ListItem", "position": 2, "name": {{ category | tojson }}, "item": "https://salderingsupdate.nl{{ category_url }}"},
    {"@type": "ListItem", "position": 3, "name": {{ title | tojson }}, "item": "https://salderingsupdate.nl/articles/{{ slug }}"}
  ]
}
</script>"""

CRUMBS = """<nav class="crumbs" aria-label="Kruimelpad">
<a href="/">Home</a> <span aria-hidden="true">&rsaquo;</span> <a href="{{ category_url }}">{{ category }}</a> <span aria-hidden="true">&rsaquo;</span> <span aria-current="page">{{ title }}</span>
</nav>"""

HEADER = """<div class="article-header">
            <h1>{{ title }}</h1>
            <div class="article-meta byline">
                <span>{{ date_display }}</span>
                <span class="author">{{ author }}</span>
                {%- if updated_iso != date_iso %}
                <span class="updated">Bijgewerkt {{ updated_display }}</span>
                {%- endif %}
                <span><a href="{{ category_url }}" style="color:inherit">{{ category }}</a></span>
            </div>
        </div>"""

RELATED = """<div class="article-related">
<h3>Lees ook</h3>
<ul>
{%- for r in related %}
<li><a href="{{ r.url }}">{{ r.title }}</a></li>
{%- endfor %}
</ul>
</div>"""


def sub_once(pattern: str, repl: str, text: str, label: str) -> str:
    new, n = re.subn(pattern, lambda _m: repl, text, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"Template bouwen mislukt bij: {label}")
    return new


def main() -> int:
    html = BASE.read_text(encoding="utf-8")

    html = sub_once(r"<title>.*?</title>",
                    "<title>{{ title }} | SalderingsUpdate.nl</title>", html, "title")
    html = sub_once(r'<meta name="description" content=".*?">',
                    '<meta name="description" content="{{ meta_description }}">',
                    html, "description")
    html = sub_once(r'<meta name="robots" content=".*?">',
                    '<meta name="robots" content="index, follow">', html, "robots")
    html = sub_once(r'<meta property="og:title" content=".*?">',
                    '<meta property="og:title" content="{{ title }} | SalderingsUpdate.nl">',
                    html, "og:title")
    html = sub_once(r'<meta property="og:description" content=".*?">',
                    '<meta property="og:description" content="{{ meta_description }}">',
                    html, "og:description")
    html = sub_once(r'<meta property="og:url" content=".*?">',
                    '<meta property="og:url" content="https://salderingsupdate.nl/articles/{{ slug }}">',
                    html, "og:url")
    html = sub_once(r'<link rel="canonical" href=".*?">',
                    '<link rel="canonical" href="https://salderingsupdate.nl/articles/{{ slug }}">',
                    html, "canonical")
    html = sub_once(r'<meta name="twitter:title" content=".*?">',
                    '<meta name="twitter:title" content="{{ title }} | SalderingsUpdate.nl">',
                    html, "twitter:title") if 'twitter:title' in html else html
    html = sub_once(r'<meta name="twitter:description" content=".*?">',
                    '<meta name="twitter:description" content="{{ meta_description }}">',
                    html, "twitter:description") if 'twitter:description' in html else html

    # beide bestaande schema-blokken vervangen door één Jinja-blok
    html = sub_once(
        r'<script type="application/ld\+json">.*?</script>\s*'
        r'<script type="application/ld\+json">.*?</script>',
        ARTICLE_SCHEMA, html, "schema")

    html = sub_once(r'<nav class="crumbs".*?</nav>', CRUMBS, html, "kruimelpad")
    html = sub_once(r'<div class="article-header">.*?</div>\s*</div>', HEADER, html, "kop")
    html = sub_once(r'<div class="summary">.*?</div>',
                    '<div class="summary">{{ summary }}</div>', html, "samenvatting")
    html = sub_once(r'<div class="article-body">.*?</div>\s*(?=<div style="background:var\(--black\))',
                    '<div class="article-body">\n{{ content_html }}\n</div>\n', html, "artikeltekst")
    html = sub_once(r'<div class="article-source">.*?</div>',
                    '<div class="article-source"><strong>Bron:</strong> '
                    '<a href="{{ source_url }}" rel="noopener nofollow" target="_blank">'
                    '{{ source_label }}</a></div>', html, "bron")
    html = sub_once(r'<div class="article-related">.*?</div>', RELATED, html, "gerelateerd")

    # Affiliate-blok afslanken: twee knoppen in plaats van zes.
    m = re.search(r'(<div style="background:var\(--black\);color:var\(--white\).*?)(</div>\s*</div>)',
                  html, re.S)
    if m:
        block = m.group(0)
        links = re.findall(r'<a href="[^"]*" class="btn-affiliate"[^>]*>.*?</a>', block, re.S)
        if len(links) > 2:
            for extra in links[2:]:
                block = block.replace(extra, "")
            block = re.sub(r"\n\s*\n", "\n", block)
            html = html[:m.start()] + block + html[m.end():]

    OUT.write_text(html, encoding="utf-8")
    print(f"artikel.html opnieuw gebouwd ({len(html)} tekens)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
