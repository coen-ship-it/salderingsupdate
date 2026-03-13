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
]

TRUSTED_DOMAINS = [
    "rijksoverheid.nl", "rvo.nl", "acm.nl",
    "eigenhuis.nl", "consumentenbond.nl",
    "solarmagazine.nl", "energiegids.nl", "zonneplan.nl",
]

# ── Qwen client (OpenAI-compatible) ──────────────────────────────────────────
qwen_client = OpenAI(
    api_key=QWEN_API_KEY,
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)

# ── Systeem-prompt voor Qwen ─────────────────────────────────────────────────
SYSTEM_PROMPT = textwrap.dedent("""
    Je bent redacteur van salderingsupdate.nl.

    DOELGROEP: Nederlandse huiseigenaren 35–65 jaar met zonnepanelen op het dak.
    Niet technisch onderlegd. Bezorgd over maandlasten na 2027. Willen praktische
    informatie, geen juridisch of financieel advies.

    STIJLREGELS:
    - Schrijf in het Nederlands, neutraal en feitelijk
    - Geen reclametaal, geen bangmakerij, geen superlatieven
    - Maximaal 250 woorden in content_html (exclusief titel en samenvatting)
    - Gebruik alleen informatie uit de aangeleverde bronnen
    - Noem concrete bedragen/percentages alleen met bron en voorbehoud
    - Verwijs bij twijfel naar rvo.nl of rijksoverheid.nl

    VERPLICHT OUTPUT-FORMAAT (strikt JSON, niets anders):
    {
      "title": "Volledige, informatieve titel (max 80 tekens)",
      "slug": "url-vriendelijke-slug-zonder-datumprefix",
      "meta_description": "SEO-omschrijving van 140–160 tekens",
      "summary": "Korte samenvatting van 1–2 zinnen (max 45 woorden)",
      "content_html": "<p>Alinea 1...</p>\\n<p>Alinea 2...</p>\\n<p>Alinea 3...</p>",
      "source_label": "Leesbare naam van de primaire bron",
      "source_url": "https://volledig-url-van-de-bron"
    }

    VERBODEN:
    - Financieel of juridisch advies geven
    - Beweringen zonder bron
    - Reclame of affiliate-suggesties in de tekst
    - Meer dan 3 alinea's in content_html
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
            "content_html": "<p>Dit is een testartikel. De salderingsregeling stopt op 1 januari 2027.</p>",
            "source_label": "Rijksoverheid.nl (testbron)",
            "source_url": "https://www.rijksoverheid.nl",
        }

    user_prompt = build_user_prompt(topic, results)

    response = qwen_client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=1200,
    )

    raw = response.choices[0].message.content
    article = json.loads(raw)

    # Basisvalidatie
    required = ["title", "slug", "meta_description", "summary", "content_html",
                "source_label", "source_url"]
    for field in required:
        if field not in article:
            raise ValueError(f"Qwen-antwoord mist verplicht veld: {field!r}")

    # Slug opschonen: alleen letters, cijfers en koppeltekens
    article["slug"] = re.sub(r"[^a-z0-9-]", "-", article["slug"].lower()).strip("-")
    return article


# ─────────────────────────────────────────────────────────────────────────────
# Stap 3: HTML-bestand aanmaken
# ─────────────────────────────────────────────────────────────────────────────

def render_article_html(article: dict, article_date: date) -> str:
    """Rendert de artikel.html Jinja2-template met de artikeldata."""
    env = Environment(loader=FileSystemLoader(str(SITE_DIR)), autoescape=False)
    template = env.get_template("artikel.html")

    return template.render(
        title=article["title"],
        meta_description=article["meta_description"],
        date_iso=article_date.isoformat(),
        date_display=article_date.strftime("%-d %B %Y").lstrip("0"),
        summary=article["summary"],
        content_html=article["content_html"],
        source_label=article["source_label"],
        source_url=article["source_url"],
    )


def save_article(article: dict, article_date: date, dry_run: bool = False) -> Path:
    """Slaat het gegenereerde artikel op als HTML-bestand."""
    filename = f"{article_date.isoformat()}-{article['slug']}.html"
    filepath = ARTICLES_DIR / filename

    html = render_article_html(article, article_date)

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


def build_article_list_html(articles: list[dict]) -> str:
    """Genereert de HTML voor de artikellijst op de homepage."""
    if not articles:
        return '<p class="no-articles">Nog geen artikelen beschikbaar.</p>'

    items = []
    for a in articles:
        items.append(
            f'<a class="article-card" href="{a["file"]}">\n'
            f'  <div class="article-card-meta">{a["date_display"]}</div>\n'
            f'  <div class="article-card-title">{a["title"]}</div>\n'
            f'  <div class="article-card-summary">{a["summary"]}</div>\n'
            f'</a>'
        )
    return "\n".join(items)


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

    article_url = f"{SITE_BASE_URL.rstrip('/')}/articles/{article_file.name}"

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
        article_file = save_article(article, today, dry_run=args.dry_run)

        # Stap 4: Index bijwerken
        print("📋 Index bijwerken...")
        articles.insert(0, {
            "title":        article["title"],
            "slug":         article["slug"],
            "date":         today.isoformat(),
            "date_display": today.strftime("%-d %B %Y"),
            "summary":      article["summary"],
            "file":         f"articles/{article_file.name}",
            "source_label": article["source_label"],
            "source_url":   article["source_url"],
        })
        save_articles(articles, dry_run=args.dry_run)
        update_index(articles, dry_run=args.dry_run)

        # Stap 5: Nieuwsbrief
        print("📧 Nieuwsbrief versturen...")
        send_newsletter(article, article_file, dry_run=args.dry_run)

        print(f"\n✅ Klaar! Nieuw artikel: {article_file.name}\n")

        # Één artikel per run is genoeg
        break

    print("Agent klaar.\n")


if __name__ == "__main__":
    main()
