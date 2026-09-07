#!/usr/bin/env python3
"""Herschrijft titels en meta-omschrijvingen van de pagina's die vertoningen krijgen.

Aanleiding: Search Console (27 mei - 26 aug 2026) laat zien dat de site goed
rankt maar nauwelijks klikken krijgt. 4.670 vertoningen, 85 klikken, CTR 1,8%
bij gemiddelde positie 9,4. De uitschieters:

    subsidie thuisbatterij 2027   positie 6,4   776 vertoningen   CTR 1,4%
    thuisbatterij subsidie 2027   positie 4,5   165 vertoningen   CTR 1,8%
    thuisbatterij subsidie 2026   positie 2,8     9 vertoningen   CTR 0%
    /contracten                   positie 12,3  2408 vertoningen  CTR 1,1%

Op die posities hoort een veelvoud van die CTR. Dat is geen rankingprobleem
maar een snippetprobleem: de titels beschrijven het onderwerp in plaats van
het antwoord te geven waar de zoeker op uit is.

Twee principes in de nieuwe titels:
  * het antwoord staat in de titel, niet de belofte van een antwoord
    ("0% btw + EUR 200-1.500 via uw gemeente" in plaats van "alle opties op een rij")
  * geen "| SalderingsUpdate.nl" meer op artikelpagina's: dat kost ~20 van de
    ~60 tekens die Google toont, en het merk zegt de zoeker nog niets. Google
    toont de sitenaam sowieso apart boven het resultaat. De homepage houdt hem.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools import lib

# bestand -> (nieuwe title, nieuwe meta description)
CHANGES: dict[str, tuple[str, str]] = {
    # 1.292 vertoningen, positie 5,7, CTR 2,4% — de belangrijkste pagina van de site
    "articles/2026-04-28-subsidie-thuisbatterij-2027-overzicht.html": (
        "Subsidie thuisbatterij 2027: 0% btw + €200–1.500 via uw gemeente",
        "Geen landelijke ISDE voor thuisbatterijen in 2027, wél 0% btw en gemeentelijke "
        "regelingen van €200 tot €1.500. Welke er zijn en hoe u ze aanvraagt.",
    ),
    # 2.408 vertoningen (meer dan de helft van de site), positie 12,3, CTR 1,1%
    "contracten.html": (
        "Energiecontract met zonnepanelen 2027: dynamisch of vast?",
        "Welk contract past bij zonnepanelen als het salderen stopt? Dynamisch, vast en "
        "variabel naast elkaar, inclusief terugleververgoeding en terugleverkosten.",
    ),
    # 443 vertoningen, positie 14,8
    "articles/2026-03-07-dynamisch-vast-contract-zonnepanelen.html": (
        "Dynamisch of vast contract met zonnepanelen na 2027?",
        "Dynamisch, vast of variabel na het einde van de saldering? Vergelijking en een "
        "rekenvoorbeeld: €200–400 per jaar verschil, afhankelijk van uw verbruik.",
    ),
    # 367 vertoningen, positie 7,9 — homepage, houdt de merknaam
    "index.html": (
        "Salderingsregeling 2027: laatste nieuws en wat het u kost",
        "De salderingsregeling stopt op 1 januari 2027 — geen afbouw, maar een harde stop. "
        "Actueel nieuws, wat het u per jaar kost en wat u nu nog kunt regelen.",
    ),
    # 123 vertoningen, positie 6,0, CTR 6,5% — presteert al goed, titel alleen inkorten
    "articles/2026-04-09-impact-saldering-berekenen-hoeveel-verlies-ik.html": (
        "Hoeveel verliest u als het salderen stopt? Bereken uw impact",
        "Bereken wat het einde van de salderingsregeling u per jaar kost. Vul uw aantal "
        "panelen, verbruik en tarief in en zie direct uw persoonlijke bedrag.",
    ),
    # 69 vertoningen, positie 14,8 — zoekwoord 'lokale subsidie thuisbatterij' staat op 32,2
    "articles/2026-02-20-lokale-subsidies-zonnepanelen-batterijen.html": (
        "Lokale subsidie thuisbatterij: €200–1.500 per gemeente",
        "Gemeenten en provincies geven €200 tot €1.500 subsidie op thuisbatterijen en "
        "zonnepanelen. Controleer of uw gemeente een regeling heeft en hoe u die aanvraagt.",
    ),
    # 47 vertoningen, positie 7,8
    "articles/2026-03-03-thuisbatterij-dynamisch-contract.html": (
        "Thuisbatterij met dynamisch contract: wat levert het op?",
        "Met een thuisbatterij en een dynamisch tarief laadt u op goedkope uren en verbruikt "
        "u op dure. Hoe de combinatie werkt en wat het per jaar oplevert.",
    ),
    # 2 vertoningen, positie 24 — titel was 75 tekens en werd afgekapt
    "articles/2026-04-14-thuisbatterij-huren-of-kopen.html": (
        "Thuisbatterij huren of kopen: wat is in 2026 slimmer?",
        "Huren kost niets vooraf maar levert minder op; kopen vraagt €6.000–9.000 en verdient "
        "zich terug. De rekensom en de voorwaarden waar u op moet letten.",
    ),
}

MAX_TITLE = 70
MAX_DESC = 160


def apply(path: Path, title: str, description: str) -> bool:
    html = path.read_text(encoding="utf-8")
    original = html

    html = re.sub(r"<title>.*?</title>", lambda _m: f"<title>{title}</title>",
                  html, count=1, flags=re.S)
    for attr, key, value in (
        ("name", "description", description),
        ("property", "og:title", title),
        ("property", "og:description", description),
        ("name", "twitter:title", title),
        ("name", "twitter:description", description),
    ):
        html = re.sub(
            rf'<meta {attr}="{re.escape(key)}" content="[^"]*"\s*/?>',
            lambda _m: f'<meta {attr}="{key}" content="{value}">',
            html, count=1)

    # headline in het schema gelijktrekken met de nieuwe titel
    html = re.sub(r'"headline": "[^"]*"', lambda _m: f'"headline": "{title}"', html, count=1)

    if html != original:
        path.write_text(html, encoding="utf-8")
        return True
    return False


def main() -> int:
    problems = 0
    for rel, (title, desc) in CHANGES.items():
        if len(title) > MAX_TITLE:
            print(f"  te lang ({len(title)}): {title}")
            problems += 1
        if len(desc) > MAX_DESC:
            print(f"  omschrijving te lang ({len(desc)}): {rel}")
            problems += 1
    if problems:
        return 1

    changed = 0
    for rel, (title, desc) in CHANGES.items():
        path = lib.SITE_DIR / rel
        if not path.exists():
            print(f"  ontbreekt: {rel}")
            problems += 1
            continue
        if apply(path, title, desc):
            changed += 1
            print(f"  {len(title):>2} tekens · {title}")
    print(f"\n{changed} pagina's bijgewerkt.")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
