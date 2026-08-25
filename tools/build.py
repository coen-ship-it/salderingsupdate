#!/usr/bin/env python3
"""Genereert sitemap.xml en _redirects uit de werkelijke inhoud van de site.

lastmod wordt bijgehouden in sitemap-state.json: per pagina wordt een hash van
de inhoud bewaard. Verandert de inhoud niet, dan blijft de oude datum staan.
Zo krijgt Google echte updatesignalen in plaats van 28x dezelfde bulk-datum.

Gebruik:
    python tools/build.py                # datum = vandaag voor gewijzigde pagina's
    python tools/build.py --date 2026-09-01
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools import lib

STATE_FILE = lib.SITE_DIR / "sitemap-state.json"
SITEMAP = lib.SITE_DIR / "sitemap.xml"
REDIRECTS = lib.SITE_DIR / "_redirects"

PAGE_FILES = {
    "/": "index.html",
    "/nieuws": "nieuws.html",
    "/regelgeving": "regelgeving.html",
    "/thuisbatterijen": "thuisbatterijen.html",
    "/subsidies": "subsidies.html",
    "/contracten": "contracten.html",
    "/terugleverkosten": "terugleverkosten.html",
    "/faq": "faq.html",
    "/over-ons": "over-ons.html",
    "/privacy": "privacy.html",
}


def content_hash(path: Path) -> str:
    """Hash van de inhoud, zonder de delen die elke build wijzigen."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r'"dateModified":\s*"[^"]*"', "", text)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def build_sitemap(today: str) -> tuple[str, dict]:
    state = load_state()
    entries: list[tuple[str, str, str, str]] = []

    for path, (priority, changefreq) in lib.STATIC_PAGES.items():
        filename = PAGE_FILES.get(path)
        f = lib.SITE_DIR / filename if filename else None
        if not f or not f.exists():
            print(f"  overgeslagen (bestaat nog niet): {path}")
            continue
        h = content_hash(f)
        prev = state.get(path, {})
        lastmod = today if prev.get("hash") != h else prev.get("lastmod", today)
        state[path] = {"hash": h, "lastmod": lastmod}
        entries.append((f"{lib.BASE_URL}{path}", lastmod, changefreq, priority))

    for art in lib.load_articles():
        slug = art["file"].rsplit("/", 1)[-1].removesuffix(".html")
        f = lib.ARTICLES_DIR / f"{slug}.html"
        if not f.exists():
            continue
        key = lib.article_url(slug)
        h = content_hash(f)
        prev = state.get(key, {})
        lastmod = today if prev.get("hash") != h else prev.get("lastmod", art.get("updated") or art["date"])
        state[key] = {"hash": h, "lastmod": lastmod}
        entries.append((f"{lib.BASE_URL}{key}", lastmod, "monthly", "0.7"))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemap.org/schemas/sitemap/0.9">'.replace(
                 "www.sitemap.org", "www.sitemaps.org")]
    for url, lastmod, changefreq, priority in entries:
        lines += ["  <url>",
                  f"    <loc>{url}</loc>",
                  f"    <lastmod>{lastmod}</lastmod>",
                  f"    <changefreq>{changefreq}</changefreq>",
                  f"    <priority>{priority}</priority>",
                  "  </url>"]
    lines.append("</urlset>")
    return "\n".join(lines) + "\n", state


def build_redirects() -> str:
    """301 van .html naar de schone URL, voor elke pagina en elk artikel."""
    out = ["# Automatisch gegenereerd door tools/build.py — niet met de hand bewerken.",
           "# Alle .html-varianten wijzen met een 301 naar de canonieke schone URL.",
           ""]
    for path, filename in PAGE_FILES.items():
        if path == "/" or not (lib.SITE_DIR / filename).exists():
            continue
        out.append(f"/{filename:<24} {path:<26} 301")
    out.append("")
    for art in lib.load_articles():
        slug = art["file"].rsplit("/", 1)[-1].removesuffix(".html")
        if not (lib.ARTICLES_DIR / f"{slug}.html").exists():
            continue
        out.append(f"/articles/{slug}.html  /articles/{slug}  301")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=date.today().isoformat(),
                    help="datum voor gewijzigde pagina's (JJJJ-MM-DD)")
    args = ap.parse_args()

    sitemap, state = build_sitemap(args.date)
    SITEMAP.write_text(sitemap, encoding="utf-8")
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    REDIRECTS.write_text(build_redirects(), encoding="utf-8")

    print(f"sitemap.xml: {sitemap.count('<url>')} URL's")
    print(f"_redirects:  {len([l for l in build_redirects().splitlines() if l.strip().endswith('301')])} regels")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
