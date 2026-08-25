#!/usr/bin/env python3
"""Brengt de bestaande artikelpagina's op orde.

Per artikel:
  * canonical / og:url / schema-url naar de schone URL (zonder .html)
  * NewsArticle-schema aangevuld: auteur als Person, dateModified, mainEntityOfPage
  * BreadcrumbList-schema toegevoegd
  * zichtbaar kruimelpad boven de titel
  * byline met auteur en "laatst bijgewerkt"-datum
  * interne links van /articles/x.html naar /articles/x
  * navigatie: "Nieuws" wijst naar /nieuws, footer krijgt "Over ons"
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools import lib

AUTHOR_NAME = "Coen van der Bijl"
AUTHOR_URL = f"{lib.BASE_URL}/over-ons"

CATEGORY_PAGE = {
    "Thuisbatterijen": "/thuisbatterijen",
    "Subsidies": "/subsidies",
    "Contracten": "/contracten",
    "Vergoeding": "/contracten",
    "Terugleverkosten": "/terugleverkosten",
    "Netcongestie": "/regelgeving",
    "Regelgeving": "/regelgeving",
}

BREADCRUMB_CSS = """
        .crumbs{font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-bottom:1rem;display:flex;flex-wrap:wrap;gap:.4rem;align-items:center}
        .crumbs a{color:var(--muted);text-decoration:none;border-bottom:1px solid transparent}
        .crumbs a:hover{color:var(--ink);border-bottom-color:var(--border)}
        .crumbs span[aria-current]{color:var(--ink)}
        .byline{display:flex;flex-wrap:wrap;gap:.35rem .9rem;align-items:center}
        .byline .author{font-weight:600;color:var(--ink);text-transform:none;letter-spacing:0}
        .byline .updated{color:var(--muted)}
"""


def clean_url(slug: str) -> str:
    return f"{lib.BASE_URL}{lib.article_url(slug)}"


ARTICLE_HREF = re.compile(
    r"(?P<pre>(?:href|location\.href|window\.location\.href)\s*=\s*)"
    r"(?P<q>[\'\"])/?articles/(?P<slug>\d{4}-\d{2}-\d{2}-[A-Za-z0-9\-]+)\.html(?P=q)")

ABS_ARTICLE_URL = re.compile(
    r"https://salderingsupdate\.nl/articles/(?P<slug>\d{4}-\d{2}-\d{2}-[A-Za-z0-9\-]+)\.html")


def relink(html: str) -> str:
    """Interne artikellinks en absolute artikel-URL's naar de schone vorm."""
    html = ARTICLE_HREF.sub(
        lambda m: f"{m.group('pre')}{m.group('q')}/articles/{m.group('slug')}{m.group('q')}",
        html)
    html = ABS_ARTICLE_URL.sub(
        lambda m: f"{lib.BASE_URL}/articles/{m.group('slug')}", html)
    # links binnen dezelfde map, zonder pad: "2026-03-07-slug.html"
    html = re.sub(r"(href=[\'\"])(\d{4}-\d{2}-\d{2}-[A-Za-z0-9\-]+)\.html",
                  r"\g<1>/articles/\g<2>", html)
    for page in ("contracten", "regelgeving", "subsidies", "faq", "thuisbatterijen", "privacy"):
        html = re.sub(rf"(href=[\'\"])/?{page}\.html", rf"\g<1>/{page}", html)
    return html


NAV_ITEM = '<a href="/terugleverkosten">Terugleverkosten</a>'


def fix_nav(html: str) -> str:
    html = html.replace('<a href="/" class="active">Nieuws</a>',
                        '<a href="/nieuws">Nieuws</a>')
    html = html.replace('<a href="/">Nieuws</a>', '<a href="/nieuws">Nieuws</a>')
    if NAV_ITEM not in html:
        html = re.sub(r'(<a href="/contracten"[^>]*>Contracten</a>)',
                      r"\1\n" + NAV_ITEM, html, count=1)
    html = re.sub(r'<a href="#over-ons">Over ons</a>',
                  '<a href="/over-ons">Over ons</a>', html)
    if 'href="/over-ons"' not in html:
        html = html.replace('<a href="mailto:info@salderingsupdate.nl">Contact</a>',
                            '<a href="/over-ons">Over ons</a>\n'
                            '<a href="mailto:info@salderingsupdate.nl">Contact</a>')
    return html


def fix_head(html: str, slug: str) -> str:
    url = clean_url(slug)
    html = re.sub(r'<link rel="canonical" href="[^"]*">',
                  f'<link rel="canonical" href="{url}">', html)
    html = re.sub(r'<meta property="og:url" content="[^"]*">',
                  f'<meta property="og:url" content="{url}">', html)
    if 'rel="canonical"' not in html:
        html = html.replace("<title>", f'<link rel="canonical" href="{url}">\n<title>', 1)
    return html


def fix_schema(html: str, art: dict, slug: str) -> str:
    url = clean_url(slug)
    m = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', html, re.S)
    if not m:
        return html
    try:
        data = json.loads(m.group(2))
    except json.JSONDecodeError:
        return html

    if isinstance(data.get("headline"), str):
        data["headline"] = re.sub(r"\s*\|\s*salderingsupdate\.nl\s*$", "",
                                  data["headline"], flags=re.I)
    data["url"] = url
    data["mainEntityOfPage"] = {"@type": "WebPage", "@id": url}
    data["datePublished"] = art["date"]
    data["dateModified"] = art.get("updated", art["date"])
    data["inLanguage"] = "nl-NL"
    data["author"] = {"@type": "Person", "name": AUTHOR_NAME, "url": AUTHOR_URL}
    data["publisher"] = {
        "@type": "Organization",
        "name": "SalderingsUpdate.nl",
        "url": f"{lib.BASE_URL}/",
        "logo": {"@type": "ImageObject", "url": f"{lib.BASE_URL}/og-image.png"},
    }
    data["articleSection"] = art["category"]
    data.setdefault("image", f"{lib.BASE_URL}/og-image.png")

    cat_page = CATEGORY_PAGE.get(art["category"], "/nieuws")
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{lib.BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": art["category"],
             "item": f"{lib.BASE_URL}{cat_page}"},
            {"@type": "ListItem", "position": 3, "name": art["title"], "item": url},
        ],
    }

    block = (m.group(1) + "\n" + json.dumps(data, ensure_ascii=False, indent=2)
             + "\n" + m.group(3)
             + '\n<script type="application/ld+json">\n'
             + json.dumps(crumbs, ensure_ascii=False, indent=2) + "\n</script>")
    return html[:m.start()] + block + html[m.end():]


def add_css(html: str) -> str:
    if ".crumbs{" in html:
        return html
    return html.replace("</style>", BREADCRUMB_CSS + "    </style>", 1)


def add_breadcrumb_and_byline(html: str, art: dict) -> str:
    cat_page = CATEGORY_PAGE.get(art["category"], "/nieuws")
    if 'class="crumbs"' not in html:
        crumb = (
            '<nav class="crumbs" aria-label="Kruimelpad">\n'
            '<a href="/">Home</a> <span aria-hidden="true">›</span> '
            f'<a href="{cat_page}">{art["category"]}</a> <span aria-hidden="true">›</span> '
            f'<span aria-current="page">{art["title"]}</span>\n'
            "</nav>\n"
        )
        html = re.sub(r'(<div class="article-header">)', crumb + r"\1", html, count=1)

    # byline: auteur + laatst bijgewerkt in de bestaande .article-meta
    def _meta(m: str) -> str:
        inner = m
        if "byline" in inner:
            return inner
        extra = f'<span class="author">{AUTHOR_NAME}</span>'
        if art.get("updated") and art["updated"] != art["date"]:
            from datetime import date as _d
            y, mo, dd = (int(x) for x in art["updated"].split("-"))
            extra += (f'<span class="updated">Bijgewerkt '
                      f'{lib.date_display(_d(y, mo, dd))}</span>')
        inner = inner.replace("<span>salderingsupdate.nl</span>", extra)
        cat_href = CATEGORY_PAGE.get(art["category"], "/nieuws")
        cat_link = f'<span><a href="{cat_href}" style="color:inherit">{art["category"]}</a></span>'
        inner = re.sub(r"<span>(Nieuws|Analyse|salderingsupdate\.nl)</span>",
                       cat_link, inner)
        if "class=\"author\"" not in inner:
            inner = inner.replace("</div>", extra + "</div>")
        return inner.replace('<div class="article-meta">',
                             '<div class="article-meta byline">')

    html = re.sub(r'<div class="article-meta">.*?</div>',
                  lambda mm: _meta(mm.group(0)), html, count=1, flags=re.S)

    # zichtbare updatedatum gelijktrekken met articles.json
    from datetime import date as _date
    if art.get("updated") and art["updated"] != art["date"]:
        y, mo, dd = (int(x) for x in art["updated"].split("-"))
        label = f"Bijgewerkt {lib.date_display(_date(y, mo, dd))}"
        if 'class="updated"' in html:
            html = re.sub(r'<span class="updated">[^<]*</span>',
                          f'<span class="updated">{label}</span>', html, count=1)
        else:
            html = html.replace('<span class="author">' + AUTHOR_NAME + "</span>",
                                '<span class="author">' + AUTHOR_NAME + "</span>"
                                + f'<span class="updated">{label}</span>', 1)
    return html


def main() -> int:
    articles = {a["file"].rsplit("/", 1)[-1].removesuffix(".html"): a
                for a in lib.load_articles()}
    changed = 0
    for path in lib.article_files():
        slug = lib.slug_from_path(path)
        art = articles.get(slug)
        if not art:
            print(f"  overgeslagen (niet in articles.json): {slug}")
            continue
        original = path.read_text(encoding="utf-8")
        html = original
        html = fix_head(html, slug)
        html = fix_schema(html, art, slug)
        html = add_css(html)
        html = add_breadcrumb_and_byline(html, art)
        html = fix_nav(html)
        html = relink(html)
        if html != original:
            path.write_text(html, encoding="utf-8")
            changed += 1
    print(f"{changed} artikelen bijgewerkt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
