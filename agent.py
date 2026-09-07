#!/usr/bin/env python3
"""
SalderingsUpdate — Wekelijkse artikelgenerator
===============================================
Zoekt actueel nieuws over saldering/batterijen/subsidies,
genereert een artikel via Qwen, publiceert het als HTML-pagina
en stuurt een nieuwsbrief via AgentMail.

Gebruik:
    python agent.py                  # één artikel genereren
    python agent.py --dry-run        # testen zonder opslaan of mailen
    python agent.py --topic "isde"   # specifiek onderwerp forceren

Cron (wekelijks, elke maandag 09:00):
    0 9 * * 1 cd /pad/naar/site && python agent.py >> logs/agent.log 2>&1

Vereisten:
    pip install tavily-python openai jinja2 python-dotenv requests
"""

import argparse
import json
import os
import re
import sys
import textwrap
from datetime import date, datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from openai import OpenAI
from tavily import TavilyClient

# ── Pad naar de site-map ─────────────────────────────────────────────────────
SITE_DIR      = Path(__file__).parent.resolve()
ARTICLES_DIR  = SITE_DIR / "articles"
ARTICLES_JSON = SITE_DIR / "articles.json"
TEMPLATE_FILE = SITE_DIR / "artikel.html"
INDEX_FILE    = SITE_DIR / "index.html"

# ── Laad .env ────────────────────────────────────────────────────────────────
load_dotenv(SITE_DIR / ".env")

TAVILY_API_KEY      = os.environ.get("TAVILY_API_KEY", "")
QWEN_API_KEY        = os.environ.get("QWEN_API_KEY", "")
AGENTMAIL_API_KEY   = os.environ.get("AGENTMAIL_API_KEY", "")
AGENTMAIL_INBOX_ID  = os.environ.get("AGENTMAIL_INBOX_ID", "")
AGENTMAIL_LIST_ID   = os.environ.get("AGENTMAIL_LIST_ID", "")
SITE_BASE_URL       = os.environ.get("SITE_BASE_URL", "https://salderingsupdate.nl")

# ── Zoekonderwerpen ───────────────────────────────────────────────────────────
SEARCH_TOPICS = [
    "salderingsregeling 2027 wijziging nieuws site:rijksoverheid.nl OR site:rvo.nl OR site:acm.nl",
    "ISDE subsidie thuisbatterij 2026 aanvragen voorwaarden",
    "terugleververgoeding zonnepanelen 2026 energieleverancier",
    "netcongestie terugleveren zonnepanelen regio",
    "dynamische energiecontracten zonnepanelen voordeel",
    "SDE++ saldering thuisbatterij 2026",
    "terugleverkosten energieleverancier zonnepanelen tarief",
    "ACM onderzoek terugleverkosten modelcontract zonnestroom",
    "Prinsjesdag Belastingplan energiebelasting zonnepanelen",
    "zelfverbruik zonnestroom verhogen zonder batterij",
]

TRUSTED_DOMAINS = [
    "rijksoverheid.nl", "rvo.nl", "acm.nl",
    "eigenhuis.nl", "consumentenbond.nl",
    "solarmagazine.nl", "energiegids.nl", "zonneplan.nl",
]

# ── Qwen client (OpenAI-compatible) ──────────────────────────────────────────
# Lui opgebouwd: zonder deze omweg crasht `python agent.py --dry-run` meteen
# op een ontbrekende sleutel, terwijl dry-run juist bedoeld is om zonder keys
# te kunnen testen.
_qwen_client: OpenAI | None = None


def qwen() -> OpenAI:
    global _qwen_client
    if _qwen_client is None:
        if not QWEN_API_KEY:
            raise RuntimeError("QWEN_API_KEY ontbreekt — stel hem in via .env.")
        _qwen_client = OpenAI(
            api_key=QWEN_API_KEY,
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        )
    return _qwen_client

# ── Systeem-prompt voor Qwen ─────────────────────────────────────────────────
SYSTEM_PROMPT = textwrap.dedent("""
    Je bent redacteur van salderingsupdate.nl.

    DOELGROEP: Nederlandse huiseigenaren 35-65 jaar met zonnepanelen op het dak.
    Niet technisch onderlegd. Bezorgd over maandlasten na 1 januari 2027, wanneer de
    salderingsregeling stopt. Willen praktische informatie waar ze iets mee kunnen.

    LENGTE EN OPBOUW
    - 700 tot 1100 woorden in content_html. Korter dan 700 woorden beantwoordt de
      vraag van de lezer niet en is voor ons geen publicabel artikel.
    - Vijf tot zeven secties, elk met een <h2> die een concrete vraag beantwoordt.
      Geen algemene koppen als "Inleiding" of "Conclusie".
    - Open met de kern: wat is er aan de hand en wat betekent het voor de lezer.
      Geen aanloop, geen herhaling van de titel.
    - Gebruik <ul>/<ol> waar een opsomming echt helpt en <table class="vergelijk-tabel">
      waar je bedragen of leveranciers naast elkaar zet. Zet in een tabel altijd een
      kolom of onderschrift met de peildatum.
    - Sluit af met een sectie die zegt wat de lezer nu concreet kan doen.

    STIJL
    - Nederlands, neutraal en feitelijk. Spreek de lezer aan met "u".
    - Geen reclametaal, geen bangmakerij, geen superlatieven, geen uitroeptekens.
    - Korte zinnen. Schrijf getallen uit zoals mensen ze lezen: "2.500 kWh", "EUR 0,08 per kWh".
    - Geen affiliate-suggesties of aanbevelingen van merken in de lopende tekst.

    FEITEN EN BRONNEN
    - Gebruik alleen informatie uit de aangeleverde bronnen. Verzin niets.
    - Elk bedrag, tarief of percentage krijgt een bron en een peildatum in de tekst.
      Weet je de peildatum niet, noem het bedrag dan niet.
    - Weet je iets niet zeker, schrijf het niet op.
    - Geef geen financieel of juridisch advies. Leg uit wat de regels zijn en wat de
      gevolgen kunnen zijn; de afweging is aan de lezer.

    INTERNE LINKS
    - Verwijs twee tot vier keer in de lopende tekst naar een relevante pagina op de
      eigen site, met beschrijvende linktekst (dus niet "lees meer").
      Beschikbare pagina's: /regelgeving, /thuisbatterijen, /subsidies, /contracten,
      /terugleverkosten, /faq, /nieuws.

    VERPLICHT OUTPUT-FORMAAT (strikt JSON, niets anders):
    {
      "title": "Volledige, informatieve titel (max 80 tekens). Belooft niets wat het artikel niet levert.",
      "slug": "url-vriendelijke-slug-zonder-datumprefix",
      "meta_description": "SEO-omschrijving van 140-160 tekens",
      "summary": "Korte samenvatting van 1-2 zinnen (max 45 woorden)",
      "content_html": "<h2>...</h2><p>...</p> ... (700-1100 woorden)",
      "category": "Regelgeving|Thuisbatterijen|Subsidies|Contracten|Netcongestie|Vergoeding|Terugleverkosten",
      "source_label": "Leesbare naam van de primaire bron",
      "source_url": "https://volledig-url-van-de-bron"
    }

    VERBODEN
    - Een titel die een vergelijking of tabel belooft die niet in het artikel staat.
    - Beweringen zonder bron, of bedragen zonder peildatum.
    - Financieel of juridisch advies.
    - Reclame of affiliate-suggesties in de tekst.
    - Minder dan 700 woorden.
""").strip()


# ─────────────────────────────────────────────────────────────────────────────
# Stap 1: Zoeken met Tavily
# ─────────────────────────────────────────────────────────────────────────────

def search_news(topic: str, dry_run: bool = False) -> list[dict]:
    """Zoekt via Tavily naar relevante nieuwsresultaten."""
    if dry_run:
        print(f"  [dry-run] Tavily-zoekopdracht overgeslagen voor: {topic!r}")
        return [{
            "title": "Testresultaat — Salderingsregeling update",
            "url": "https://www.rijksoverheid.nl/test",
            "content": "Dit is een testresultaat. De salderingsregeling stopt op 1 januari 2027.",
            "score": 0.9,
        }]

    client = TavilyClient(api_key=TAVILY_API_KEY)
    response = client.search(
        query=topic,
        search_depth="advanced",
        max_results=5,
        include_domains=TRUSTED_DOMAINS,
    )
    results = response.get("results", [])
    print(f"  Tavily: {len(results)} resultaten voor {topic!r}")
    return results


def pick_best_result(results: list[dict]) -> dict | None:
    """Kiest het meest relevante zoekresultaat op basis van Tavily-score."""
    if not results:
        return None
    return max(results, key=lambda r: r.get("score", 0))


# ─────────────────────────────────────────────────────────────────────────────
# Stap 2: Artikel genereren met Qwen
# ─────────────────────────────────────────────────────────────────────────────

def build_user_prompt(topic: str, results: list[dict]) -> str:
    """Bouwt de user-prompt op met zoekresultaten als context."""
    sources_text = "\n\n".join(
        f"Bron {i+1}: {r['title']}\nURL: {r['url']}\nInhoud: {r['content'][:800]}"
        for i, r in enumerate(results[:3])
    )
    return (
        f"Schrijf een artikel voor salderingsupdate.nl over het volgende onderwerp:\n"
        f"Onderwerp: {topic}\n\n"
        f"Beschikbare bronnen:\n{sources_text}\n\n"
        f"Gebruik bovenstaande bronnen. Vernoem de primaire bron in source_label en source_url."
    )


def generate_article(topic: str, results: list[dict], dry_run: bool = False) -> dict:
    """Laat Qwen een artikel genereren op basis van zoekresultaten."""
    if dry_run:
        print("  [dry-run] Qwen-generatie overgeslagen.")
        return {
            "title": "Testartikeltitel: Salderingsregeling stopt in 2027",
            "slug": "test-salderingsregeling-2027",
            "meta_description": "Testomschrijving van de salderingsregeling die stopt per 1 januari 2027.",
            "summary": "Dit is een testartikel voor de dry-run modus.",
            "category": "Regelgeving",
            "content_html": "<p>Dit is een testartikel. De salderingsregeling stopt op 1 januari 2027.</p>",
            "source_label": "Rijksoverheid.nl (testbron)",
            "source_url": "https://www.rijksoverheid.nl",
        }

    user_prompt = build_user_prompt(topic, results)

    response = qwen().chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=6000,
    )

    raw = response.choices[0].message.content
    article = json.loads(raw)

    # Basisvalidatie
    required = ["title", "slug", "meta_description", "summary", "content_html",
                "category", "source_label", "source_url"]
    for field in required:
        if field not in article:
            raise ValueError(f"Qwen-antwoord mist verplicht veld: {field!r}")

    # Slug opschonen: alleen letters, cijfers en koppeltekens
    article["slug"] = re.sub(r"[^a-z0-9-]", "-", article["slug"].lower()).strip("-")
    return article


# ─────────────────────────────────────────────────────────────────────────────
# Stap 3: HTML-bestand aanmaken
# ─────────────────────────────────────────────────────────────────────────────

AUTHOR_NAME = "Coen van der Bijl"

MONTHS_NL = ["januari", "februari", "maart", "april", "mei", "juni",
             "juli", "augustus", "september", "oktober", "november", "december"]

CATEGORY_PAGE = {
    "Thuisbatterijen": "/thuisbatterijen",
    "Subsidies":       "/subsidies",
    "Subsidie":        "/subsidies",
    "Contracten":      "/contracten",
    "Vergoeding":      "/contracten",
    "Terugleverkosten": "/terugleverkosten",
    "Netcongestie":    "/regelgeving",
    "Regelgeving":     "/regelgeving",
}


def date_display(d: date) -> str:
    """'25 augustus 2026' — niet afhankelijk van de locale van de server."""
    return f"{d.day} {MONTHS_NL[d.month - 1]} {d.year}"


def pick_related(article: dict, articles: list[dict], limit: int = 3) -> list[dict]:
    """Kiest gerelateerde artikelen: eerst dezelfde categorie, dan de nieuwste."""
    category = article.get("category", "")
    same = [a for a in articles if a.get("category") == category][:limit]
    rest = [a for a in articles if a not in same][: limit - len(same)]
    return [{"url": a.get("url") or "/" + a["file"].removesuffix(".html"),
             "title": a["title"]}
            for a in (same + rest)[:limit]]


def render_article_html(article: dict, article_date: date,
                        articles: list[dict] | None = None) -> str:
    """Rendert de artikel.html Jinja2-template met de artikeldata."""
    env = Environment(loader=FileSystemLoader(str(SITE_DIR)), autoescape=False)
    template = env.get_template("artikel.html")

    category = article.get("category", "Regelgeving")
    slug = f"{article_date.isoformat()}-{article['slug']}"

    return template.render(
        title=article["title"],
        meta_description=article["meta_description"],
        slug=slug,
        category=category,
        category_url=CATEGORY_PAGE.get(category, "/nieuws"),
        author=AUTHOR_NAME,
        date_iso=article_date.isoformat(),
        date_display=date_display(article_date),
        updated_iso=article_date.isoformat(),
        updated_display=date_display(article_date),
        summary=article["summary"],
        content_html=article["content_html"],
        source_label=article["source_label"],
        source_url=article["source_url"],
        related=pick_related(article, articles or []),
    )


def save_article(article: dict, article_date: date, dry_run: bool = False,
                 articles: list[dict] | None = None) -> Path:
    """Slaat het gegenereerde artikel op als HTML-bestand."""
    filename = f"{article_date.isoformat()}-{article['slug']}.html"
    filepath = ARTICLES_DIR / filename

    html = render_article_html(article, article_date, articles)

    if "noindex" in html:
        raise RuntimeError(
            "De template zet dit artikel op noindex — publicatie afgebroken. "
            "Controleer de robots-meta in artikel.html."
        )

    if dry_run:
        print(f"  [dry-run] Zou opslaan als: {filepath}")
        print(f"  [dry-run] Eerste 200 tekens HTML: {html[:200]}")
        return filepath

    ARTICLES_DIR.mkdir(exist_ok=True)
    filepath.write_text(html, encoding="utf-8")
    print(f"  Artikel opgeslagen: {filepath}")
    return filepath


# ─────────────────────────────────────────────────────────────────────────────
# Stap 4: articles.json en index.html bijwerken
# ─────────────────────────────────────────────────────────────────────────────

def load_articles() -> list[dict]:
    """Laadt de bestaande artikelindex."""
    if ARTICLES_JSON.exists():
        return json.loads(ARTICLES_JSON.read_text(encoding="utf-8"))
    return []


def save_articles(articles: list[dict], dry_run: bool = False) -> None:
    """Slaat de bijgewerkte artikelindex op."""
    if dry_run:
        print(f"  [dry-run] articles.json niet bijgewerkt ({len(articles)} artikelen).")
        return
    ARTICLES_JSON.write_text(
        json.dumps(articles, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  articles.json bijgewerkt ({len(articles)} artikelen).")


CATEGORY_CSS = {
    "Regelgeving":    "regelgeving",
    "Thuisbatterijen":"batterij",
    "Subsidie":       "subsidie",
    "Netcongestie":   "netcongestie",
    "Contracten":     "contracten",
    "Vergoeding":     "vergoeding",
}


def date_short(d: date) -> str:
    """Formateert datum als '12 MRT 2026'."""
    months = ["JAN","FEB","MRT","APR","MEI","JUN","JUL","AUG","SEP","OKT","NOV","DEC"]
    return f"{d.day} {months[d.month - 1]} {d.year}"


def build_article_list_html(articles: list[dict]) -> str:
    """Genereert de HTML voor de artikellijst op de homepage (stream-artikel formaat)."""
    if not articles:
        return '<p style="color:#888;font-style:italic;padding:1.5rem 0">Nog geen artikelen beschikbaar.</p>'

    items = []
    for a in articles:
        cat       = a.get("category", "Nieuws")
        css_class = CATEGORY_CSS.get(cat, "")
        cat_span  = f'<span class="stream-cat {css_class}">{cat}</span>' if css_class else f'<span class="stream-cat">{cat}</span>'
        date_lbl  = a.get("date_short", a.get("date_display", ""))
        items.append(
            f'<article class="stream-article" onclick="location.href=\'{a["file"]}\'">\n'
            f'  <div>\n'
            f'    {cat_span}\n'
            f'    <h3>{a["title"]}</h3>\n'
            f'    <p class="stream-excerpt">{a["summary"]}</p>\n'
            f'  </div>\n'
            f'  <span class="stream-date">{date_lbl}</span>\n'
            f'</article>'
        )
    return "\n        ".join(items)


def update_index(articles: list[dict], dry_run: bool = False) -> None:
    """Vervangt de artikellijst in index.html."""
    index_html = INDEX_FILE.read_text(encoding="utf-8")

    start_marker = "<!-- ARTICLE_LIST_START -->"
    end_marker   = "<!-- ARTICLE_LIST_END -->"

    if start_marker not in index_html or end_marker not in index_html:
        print("  ⚠️  Markeringen niet gevonden in index.html — index niet bijgewerkt.")
        return

    new_list = build_article_list_html(articles)
    new_html = (
        index_html.split(start_marker)[0]
        + start_marker + "\n      "
        + new_list + "\n      "
        + end_marker
        + index_html.split(end_marker)[1]
    )

    if dry_run:
        print("  [dry-run] index.html niet bijgewerkt.")
        return

    INDEX_FILE.write_text(new_html, encoding="utf-8")
    print("  index.html bijgewerkt.")


# ─────────────────────────────────────────────────────────────────────────────
# Stap 5: Nieuwsbrief via AgentMail
# ─────────────────────────────────────────────────────────────────────────────

def get_agentmail_subscribers() -> list[str]:
    """
    Haalt abonnees op uit AgentMail.
    Documentatie: https://docs.agentmail.to
    """
    if not AGENTMAIL_API_KEY or not AGENTMAIL_LIST_ID:
        return []

    url = f"https://api.agentmail.to/v0/lists/{AGENTMAIL_LIST_ID}/subscribers"
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {AGENTMAIL_API_KEY}"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return [s["email"] for s in data.get("subscribers", [])]


def send_newsletter(article: dict, article_file: Path, dry_run: bool = False) -> None:
    """Stuurt nieuwsbrief via AgentMail naar alle abonnees."""
    if not AGENTMAIL_API_KEY or not AGENTMAIL_INBOX_ID:
        print("  AgentMail niet geconfigureerd — nieuwsbrief overgeslagen.")
        return

    article_url = f"{SITE_BASE_URL.rstrip('/')}/articles/{article_file.stem}"

    html_body = f"""
    <div style="font-family: 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; color: #1a1a1a;">
      <div style="background: #2a588a; color: white; padding: 1.5rem; text-align: center;">
        <h1 style="margin:0; font-size:1.3rem;">salderingsupdate.nl</h1>
        <p style="margin:.5rem 0 0; font-size:.85rem; opacity:.85;">Nieuw artikel</p>
      </div>
      <div style="padding: 1.5rem;">
        <h2 style="color: #2a588a; font-size: 1.2rem; margin-bottom:.75rem;">{article['title']}</h2>
        <p style="color: #555; font-style: italic; border-left: 3px solid #2a588a; padding-left: .75rem;">
          {article['summary']}
        </p>
        <p style="margin-top: 1.5rem;">
          <a href="{article_url}"
             style="background:#2a588a; color:white; padding:.7rem 1.4rem; border-radius:6px; text-decoration:none; font-weight:600;">
            Lees het volledige artikel →
          </a>
        </p>
        <hr style="border:none; border-top:1px solid #dde6f0; margin: 2rem 0;">
        <p style="font-size:.78rem; color:#888; font-style:italic;">
          Dit is geen financieel of juridisch advies — raadpleeg altijd uw installateur of energieleverancier.<br>
          Afmelden? Stuur een e-mail naar afmelden@salderingsupdate.nl
        </p>
      </div>
    </div>
    """.strip()

    text_body = (
        f"Nieuw artikel op salderingsupdate.nl\n\n"
        f"{article['title']}\n\n"
        f"{article['summary']}\n\n"
        f"Lees meer: {article_url}\n\n"
        f"---\n"
        f"Dit is geen financieel of juridisch advies."
    )

    if dry_run:
        print(f"  [dry-run] Nieuwsbrief niet verzonden. Onderwerp: {article['title']!r}")
        return

    try:
        subscribers = get_agentmail_subscribers()
    except Exception as exc:
        print(f"  ⚠️  Kon abonnees niet ophalen: {exc}")
        subscribers = []

    if not subscribers:
        print("  Geen abonnees gevonden — nieuwsbrief overgeslagen.")
        return

    send_url = f"https://api.agentmail.to/v0/inboxes/{AGENTMAIL_INBOX_ID}/messages"
    headers  = {
        "Authorization": f"Bearer {AGENTMAIL_API_KEY}",
        "Content-Type":  "application/json",
    }

    success = 0
    for email in subscribers:
        payload = {
            "to":      [email],
            "subject": f"Nieuw: {article['title']}",
            "html":    html_body,
            "text":    text_body,
        }
        try:
            resp = requests.post(send_url, headers=headers, json=payload, timeout=10)
            resp.raise_for_status()
            success += 1
        except Exception as exc:
            print(f"  ⚠️  Kon e-mail niet sturen naar {email}: {exc}")

    print(f"  Nieuwsbrief verstuurd naar {success}/{len(subscribers)} abonnees.")


# ─────────────────────────────────────────────────────────────────────────────
# Stap 4b: afgeleide bestanden opnieuw genereren
# ─────────────────────────────────────────────────────────────────────────────

def rebuild_site(dry_run: bool = False) -> None:
    """Regenereert /nieuws, sitemap.xml en _redirects.

    Zonder deze stap belandt een nieuw artikel nooit in de sitemap en blijft het
    nieuwsarchief achter — precies wat er eerder misging.
    """
    if dry_run:
        print("  [dry-run] nieuws.html, sitemap.xml en _redirects niet bijgewerkt.")
        return
    try:
        sys.path.insert(0, str(SITE_DIR))
        from tools import build as build_tool
        from tools import make_pages
        make_pages._main()
        build_tool.main()
    except Exception as exc:  # noqa: BLE001 — mag de publicatie niet blokkeren
        print(f"  ⚠️  Afgeleide bestanden niet bijgewerkt: {exc}")
        print("     Draai handmatig: python tools/make_pages.py && python tools/build.py")


# ─────────────────────────────────────────────────────────────────────────────
# Duplicate-check
# ─────────────────────────────────────────────────────────────────────────────

def is_duplicate(slug: str, articles: list[dict]) -> bool:
    """Controleert of er al een artikel bestaat met dezelfde slug."""
    today = date.today().isoformat()
    return any(
        a["slug"] == slug or a["file"] == f"articles/{today}-{slug}.html"
        for a in articles
    )


# ─────────────────────────────────────────────────────────────────────────────
# Hoofdfunctie
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SalderingsUpdate artikelgenerator")
    parser.add_argument("--dry-run",  action="store_true", help="Test zonder opslaan of mailen")
    parser.add_argument("--topic",    type=str, default=None, help="Forceer een specifiek zoekonderwerp")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"SalderingsUpdate Agent — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Dry-run: {args.dry_run}")
    print(f"{'='*60}\n")

    # Valideer API-keys
    if not args.dry_run:
        missing = [k for k, v in {
            "TAVILY_API_KEY": TAVILY_API_KEY,
            "QWEN_API_KEY":   QWEN_API_KEY,
        }.items() if not v]
        if missing:
            print(f"❌ Ontbrekende API-keys: {', '.join(missing)}")
            print("   Stel ze in via .env of omgevingsvariabelen.")
            sys.exit(1)

    articles   = load_articles()
    today      = date.today()
    topics     = [args.topic] if args.topic else SEARCH_TOPICS

    for topic in topics:
        print(f"🔍 Zoeken: {topic!r}")

        # Stap 1: Zoeken
        results = search_news(topic, dry_run=args.dry_run)
        best    = pick_best_result(results)
        if not best:
            print("  Geen resultaten gevonden, volgende onderwerp...")
            continue

        print(f"  Beste resultaat: {best['title']!r} ({best['url']})")

        # Stap 2: Genereren
        print("🤖 Artikel genereren via Qwen...")
        try:
            article = generate_article(topic, results, dry_run=args.dry_run)
        except Exception as exc:
            print(f"  ❌ Generatie mislukt: {exc}")
            continue

        print(f"  Titel: {article['title']!r}")
        print(f"  Slug:  {article['slug']!r}")

        # Duplicate-check
        if is_duplicate(article["slug"], articles):
            print(f"  ⏭️  Al gepubliceerd (slug={article['slug']!r}), overgeslagen.")
            continue

        # Stap 3: Opslaan
        print("💾 Artikel opslaan...")
        article_file = save_article(article, today, dry_run=args.dry_run,
                                    articles=articles)

        # Stap 4: Index bijwerken
        print("📋 Index bijwerken...")
        slug_full = article_file.stem
        articles.insert(0, {
            "title":        article["title"],
            "slug":         article["slug"],
            "category":     article.get("category", "Regelgeving"),
            "date":         today.isoformat(),
            "date_display": date_display(today),
            "date_short":   date_short(today),
            "updated":      today.isoformat(),
            "summary":      article["summary"],
            "file":         f"articles/{article_file.name}",
            "url":          f"/articles/{slug_full}",
            "source_label": article["source_label"],
            "source_url":   article["source_url"],
        })
        save_articles(articles, dry_run=args.dry_run)
        update_index(articles, dry_run=args.dry_run)

        # Stap 4b: nieuwsarchief, sitemap en redirects opnieuw genereren
        print("🗺️  Archief, sitemap en redirects bijwerken...")
        rebuild_site(dry_run=args.dry_run)

        # Stap 5: Nieuwsbrief
        print("📧 Nieuwsbrief versturen...")
        send_newsletter(article, article_file, dry_run=args.dry_run)

        print(f"\n✅ Klaar! Nieuw artikel: {article_file.name}\n")

        # Één artikel per run is genoeg
        break

    print("Agent klaar.\n")


if __name__ == "__main__":
    main()
