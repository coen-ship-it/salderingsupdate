#!/usr/bin/env python3
"""Controleert de site op de fouten die eerder verkeer kostten.

Draait zonder netwerk en zonder API-keys. Geeft exitcode 1 bij een fout, zodat
dit ook in CI kan draaien vóór er iets live gaat.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools import lib

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def all_html() -> list[Path]:
    return sorted(lib.SITE_DIR.glob("*.html")) + sorted(lib.ARTICLES_DIR.glob("*.html"))


def expected_url(path: Path) -> str | None:
    if path.parent.name == "articles":
        return f"{lib.BASE_URL}/articles/{path.stem}"
    name = path.stem
    if name == "artikel":
        return None  # template
    if name == "index":
        return f"{lib.BASE_URL}/"
    return f"{lib.BASE_URL}/{name}"


def check_pages() -> None:
    for f in all_html():
        html = f.read_text(encoding="utf-8")
        rel = f.relative_to(lib.SITE_DIR)

        if f.name == "artikel.html":
            if "noindex" in html:
                err(f"{rel}: template zet artikelen op noindex")
            for var in ("{{ title }}", "{{ content_html }}", "{{ slug }}"):
                if var not in html:
                    err(f"{rel}: template mist {var}")
            continue

        if re.search(r'name="robots"[^>]*noindex', html):
            err(f"{rel}: staat op noindex")

        want = expected_url(f)
        m = re.search(r'<link rel="canonical" href="([^"]+)">', html)
        if not m:
            err(f"{rel}: geen canonical")
        elif want and m.group(1) != want:
            err(f"{rel}: canonical is {m.group(1)}, verwacht {want}")

        og = re.search(r'<meta property="og:url" content="([^"]+)">', html)
        if og and want and og.group(1) != want:
            err(f"{rel}: og:url ({og.group(1)}) wijkt af van canonical ({want})")

        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        if not blocks:
            warn(f"{rel}: geen gestructureerde data")
        for b in blocks:
            try:
                json.loads(b)
            except json.JSONDecodeError as exc:
                err(f"{rel}: ongeldige JSON-LD ({exc})")

        for bad in re.findall(r'href="(/?[a-z0-9/\-]+\.html)"', html):
            err(f"{rel}: interne link naar .html-URL: {bad}")

        if not re.search(r'<meta name="description" content="\S', html):
            err(f"{rel}: geen meta description")

        if f.name != "index.html" and 'href="/nieuws"' not in html:
            warn(f"{rel}: linkt niet naar het nieuwsarchief")


def check_internal_links() -> None:
    """Elke interne link moet naar een bestaande pagina wijzen."""
    known = {"/"}
    for path in lib.STATIC_PAGES:
        known.add(path)
    for art in lib.load_articles():
        known.add(art["url"])

    for f in all_html():
        if f.name == "artikel.html":
            continue
        html = f.read_text(encoding="utf-8")
        rel = f.relative_to(lib.SITE_DIR)
        for href in set(re.findall(r'href="(/[^"#?]*)(?:[#?][^"]*)?"', html)):
            if href in known or href.startswith("/og-image"):
                continue
            err(f"{rel}: link naar onbekende pagina {href}")


def check_sitemap() -> None:
    sm = (lib.SITE_DIR / "sitemap.xml").read_text(encoding="utf-8")
    locs = set(re.findall(r"<loc>([^<]+)</loc>", sm))

    for art in lib.load_articles():
        url = f"{lib.BASE_URL}{art['url']}"
        if url not in locs:
            err(f"sitemap: artikel ontbreekt — {url}")
    for path in lib.STATIC_PAGES:
        url = f"{lib.BASE_URL}{path}" if path != "/" else f"{lib.BASE_URL}/"
        if url not in locs:
            err(f"sitemap: pagina ontbreekt — {url}")
    for loc in locs:
        if loc.endswith(".html"):
            err(f"sitemap: bevat .html-URL — {loc}")

    dates = set(re.findall(r"<lastmod>([^<]+)</lastmod>", sm))
    if len(dates) == 1 and len(locs) > 5:
        warn("sitemap: alle pagina's hebben dezelfde lastmod — dat is geen updatesignaal")


def check_articles_json() -> None:
    on_disk = {p.stem for p in lib.article_files()}
    in_index = {a["file"].rsplit("/", 1)[-1].removesuffix(".html")
                for a in lib.load_articles()}
    for missing in sorted(on_disk - in_index):
        err(f"articles.json: artikel ontbreekt in de index — {missing}")
    for ghost in sorted(in_index - on_disk):
        err(f"articles.json: verwijst naar een bestand dat niet bestaat — {ghost}")


def check_redirects() -> None:
    text = (lib.SITE_DIR / "_redirects").read_text(encoding="utf-8")
    for art in lib.load_articles():
        slug = art["file"].rsplit("/", 1)[-1].removesuffix(".html")
        if f"/articles/{slug}.html" not in text:
            err(f"_redirects: geen 301 voor /articles/{slug}.html")


def main() -> int:
    check_pages()
    check_internal_links()
    check_sitemap()
    check_articles_json()
    check_redirects()

    for w in warnings:
        print(f"  let op: {w}")
    for e in errors:
        print(f"  FOUT: {e}")

    print(f"\n{len(errors)} fouten, {len(warnings)} aandachtspunten "
          f"over {len(all_html())} pagina's.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
