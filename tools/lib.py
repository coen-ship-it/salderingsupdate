"""Gedeelde helpers voor salderingsupdate.nl."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent
ARTICLES_DIR = SITE_DIR / "articles"
ARTICLES_JSON = SITE_DIR / "articles.json"
BASE_URL = "https://salderingsupdate.nl"

MONTHS_NL = ["januari", "februari", "maart", "april", "mei", "juni",
             "juli", "augustus", "september", "oktober", "november", "december"]
MONTHS_SHORT = ["JAN", "FEB", "MRT", "APR", "MEI", "JUN",
                "JUL", "AUG", "SEP", "OKT", "NOV", "DEC"]

# Statische pagina's: pad -> (prioriteit, changefreq)
STATIC_PAGES = {
    "/":                  ("1.0", "daily"),
    "/nieuws":            ("0.9", "daily"),
    "/regelgeving":       ("0.9", "weekly"),
    "/thuisbatterijen":   ("0.9", "weekly"),
    "/subsidies":         ("0.8", "weekly"),
    "/contracten":        ("0.8", "weekly"),
    "/terugleverkosten":  ("0.9", "weekly"),
    "/faq":               ("0.7", "monthly"),
    "/over-ons":          ("0.5", "monthly"),
    "/privacy":           ("0.3", "yearly"),
}


def date_display(d: date) -> str:
    return f"{d.day} {MONTHS_NL[d.month - 1]} {d.year}"


def date_short(d: date) -> str:
    return f"{d.day} {MONTHS_SHORT[d.month - 1]} {d.year}"


def article_url(slug_with_date: str) -> str:
    """Canonieke (schone) URL van een artikel, zonder .html."""
    return f"/articles/{slug_with_date}"


def load_articles() -> list[dict]:
    if ARTICLES_JSON.exists():
        return json.loads(ARTICLES_JSON.read_text(encoding="utf-8"))
    return []


def save_articles(articles: list[dict]) -> None:
    ARTICLES_JSON.write_text(
        json.dumps(articles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def meta_content(html: str, *, name: str = "", prop: str = "") -> str:
    attr, val = ("name", name) if name else ("property", prop)
    m = re.search(
        rf'<meta\s+{attr}=["\']{re.escape(val)}["\']\s+content=["\'](.*?)["\']\s*/?>',
        html, re.S | re.I)
    return m.group(1).strip() if m else ""


def first_ld_json(html: str) -> dict | None:
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def page_title(html: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    return m.group(1).strip() if m else ""


def h1(html: str) -> str:
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S | re.I)
    return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""


def summary_text(html: str) -> str:
    m = re.search(r'<div class="summary"[^>]*>(.*?)</div>', html, re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""


def article_files() -> list[Path]:
    return sorted(ARTICLES_DIR.glob("*.html"))


def slug_from_path(p: Path) -> str:
    return p.stem


def date_from_slug(slug: str) -> date:
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})-", slug)
    if not m:
        raise ValueError(f"Geen datum in slug: {slug}")
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
