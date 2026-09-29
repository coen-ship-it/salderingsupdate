"""
Centrale registry voor alle affiliate-links van salderingsupdate.nl.

Waarom dit bestand bestaat
--------------------------
Voorheen stonden de Awin-links los in 26 HTML-bestanden, allemaal wijzend naar
de homepage van de adverteerder en zonder clickref. Daardoor was niet te zien
welke pagina klikken oplevert, en landde de bezoeker steeds een stap te ver van
zijn eigen vraag.

Hier staat elke partner één keer, met:
  * de juiste deeplink (categoriepagina die past bij de zoekintentie),
  * de commissie zoals die in Awin staat (voor prioritering),
  * clickref-tracking per pagina, zodat het Awin Click References-rapport
    laat zien welk artikel de klik heeft opgeleverd.

Gebruik:
    from affiliates import block, link
    html = block("batterij_kopen", slug="subsidie-thuisbatterij-2027-overzicht")
"""

from __future__ import annotations

import re
from html import escape

AWIN_AFFID = "2848379"
AWIN_BASE = "https://www.awin1.com/cread.php"


# --------------------------------------------------------------------------
# Partners
# --------------------------------------------------------------------------
# 'fee' is puur documentatie: het tarief zoals het op 29 sep 2026 in de Awin
# Commission Manager stond. Handig bij het kiezen welk blok je waar zet.

PARTNERS: dict[str, dict] = {
    "energiekiezer_zon": {
        "mid": "68288",
        "name": "EnergieKiezer",
        "url": "https://www.energiekiezer.nl/energie-vergelijken/zonnepanelen",
        "fee": "EUR 22,00 vast",
    },
    "energiekiezer_geen_terugleverkosten": {
        "mid": "68288",
        "name": "EnergieKiezer",
        "url": "https://www.energiekiezer.nl/energie-vergelijken/zonnepanelen/zonder-terugleverkosten",
        "fee": "EUR 22,00 vast",
    },
    "energiekiezer_beste_leverancier": {
        "mid": "68288",
        "name": "EnergieKiezer",
        "url": "https://www.energiekiezer.nl/energie-vergelijken/zonnepanelen/beste-energieleverancier",
        "fee": "EUR 22,00 vast",
    },
    "coolblue_energie": {
        "mid": "85163",
        "name": "Coolblue Energie",
        "url": "https://www.coolblue.nl/energiecontracten/bereken-maandbedrag",
        "fee": "EUR 0,00 - 50,00 per aanvraag",
    },
    "coolblue_thuisbatterij": {
        "mid": "85161",
        "name": "Coolblue",
        "url": "https://www.coolblue.nl/thuisbatterijen",
        "fee": "2% - 15% van orderbedrag",
    },
    "coolblue_zonnepanelen": {
        "mid": "85161",
        "name": "Coolblue",
        "url": "https://www.coolblue.nl/zonnepanelen",
        "fee": "2% - 15% van orderbedrag",
    },
    "gaslicht": {
        "mid": "8520",
        "name": "Gaslicht.com",
        "url": "https://www.gaslicht.com/energievergelijken",
        "fee": "EUR 9,46 vast",
    },
    "overstappen": {
        "mid": "65020",
        "name": "Overstappen.nl",
        "url": "https://www.overstappen.nl/energie/",
        "fee": "EUR 0,00 - 35,00",
    },
    "ecoflow": {
        "mid": "123332",
        "name": "EcoFlow",
        "url": "https://www.ecoflow.com/nl/series/home-battery",
        "fee": "5% van orderbedrag",
    },
    "ecoflow_stream": {
        "mid": "123332",
        "name": "EcoFlow",
        "url": "https://www.ecoflow.com/nl/series/stream-series",
        "fee": "5% van orderbedrag",
    },
    "allpowers": {
        "mid": "125964",
        "name": "ALLPOWERS",
        "url": "https://iallpowers.nl/collections/bs-pro-energieopslag",
        "fee": "5% van orderbedrag",
    },
    "vatrer": {
        "mid": "119703",
        "name": "Vatrer",
        "url": "https://www.vatrerpower.com/en-de/collections/home-energy-storage-battery",
        "fee": "3% - 10% van orderbedrag",
    },
}


def _safe_ref(value: str) -> str:
    """Awin accepteert alleen eenvoudige tekens in clickref."""
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value or "").strip("-")
    return value[:80] or "onbekend"


def _quote(url: str) -> str:
    from urllib.parse import quote

    return quote(url, safe="")


def link(partner: str, slug: str, position: str = "") -> str:
    """Bouwt een Awin-deeplink met clickref, zodat de klik herleidbaar is.

    clickref-formaat: <slug>__<positie>  (bijv. 'subsidie-thuisbatterij-2027__intro')
    Terug te vinden in Awin onder Reports > Click References.
    """
    p = PARTNERS[partner]
    ref = _safe_ref(f"{slug}__{position}" if position else slug)
    return (
        f"{AWIN_BASE}?awinmid={p['mid']}&awinaffid={AWIN_AFFID}"
        f"&clickref={ref}&ued={_quote(p['url'])}"
    )


# --------------------------------------------------------------------------
# Blokken
# --------------------------------------------------------------------------
# Elk blok hoort bij één zoekintentie. De kop stelt de vraag die de lezer op
# dat punt in het artikel heeft; de knoptekst zegt wat er gebeurt na de klik.

_BLOCKS: dict[str, dict] = {
    "batterij_kopen": {
        "title": "Wat kost een thuisbatterij nu werkelijk?",
        "intro": (
            "Prijzen bewegen hard richting 2027. Vergelijk een compleet geplaatst systeem, "
            "modulaire thuisopslag en losse LiFePO4-opslag voor een compatibele omvormer."
        ),
        "buttons": [
            ("coolblue_thuisbatterij", "Thuisbatterijen en prijzen bij Coolblue"),
            ("ecoflow", "EcoFlow thuisbatterijen bekijken"),
            ("vatrer", "Vatrer LiFePO4-opslag bekijken"),
        ],
    },
    "batterij_budget": {
        "title": "Goedkoper alternatief: plug-in opslag",
        "intro": (
            "Een volledige thuisbatterij is niet voor iedereen rendabel. Plug-in systemen "
            "kosten een fractie en zijn zonder installateur te plaatsen."
        ),
        "buttons": [
            ("ecoflow_stream", "EcoFlow STREAM plug-in batterijen"),
            ("allpowers", "ALLPOWERS energieopslag"),
        ],
    },
    "contract_zon": {
        "title": "Welk energiecontract past bij jouw zonnepanelen?",
        "intro": (
            "Vanaf 1 januari 2027 bepaalt je terugleververgoeding wat je panelen nog opleveren. "
            "Vergelijk specifiek op zonnepanelen, niet op het standaardtarief."
        ),
        "buttons": [
            ("gaslicht", "Vergelijk leveranciers op Gaslicht.com"),
            ("energiekiezer_zon", "Vergelijk contracten voor zonnepanelen"),
        ],
    },
    "terugleverkosten": {
        "title": "Leveranciers zonder terugleverkosten",
        "intro": (
            "Terugleverkosten kunnen honderden euro's per jaar schelen. Deze vergelijking "
            "filtert direct op leveranciers die ze niet rekenen."
        ),
        "buttons": [
            ("energiekiezer_geen_terugleverkosten", "Bekijk contracten zonder terugleverkosten"),
            ("gaslicht", "Vergelijk alle leveranciers op Gaslicht.com"),
        ],
    },
    "beste_leverancier": {
        "title": "Beste energieleverancier met zonnepanelen",
        "intro": (
            "De ranglijst verschilt sterk als je teruglevert. Deze vergelijking rekent met "
            "je opwek in plaats van alleen je verbruik."
        ),
        "buttons": [
            ("gaslicht", "Vergelijk leveranciers op Gaslicht.com"),
            ("energiekiezer_beste_leverancier", "Vergelijk specifiek voor zonnepanelen"),
        ],
    },
    "zonnepanelen_kopen": {
        "title": "Zonnepanelen aanschaffen of uitbreiden",
        "intro": "Actuele pakketprijzen inclusief installatie en garantie.",
        "buttons": [
            ("coolblue_zonnepanelen", "Zonnepanelen bij Coolblue"),
        ],
    },
}

# Welk blok hoort bij welke artikelcategorie (agent.py gebruikt dit voor
# nieuwe artikelen). Categorie komt uit articles.json.
CATEGORY_BLOCKS: dict[str, str] = {
    "Batterijen": "batterij_kopen",
    "Thuisbatterij": "batterij_kopen",
    "Subsidies": "batterij_kopen",
    "Contracten": "contract_zon",
    "Terugleveren": "terugleverkosten",
    "Regelgeving": "contract_zon",
    "Nieuws": "contract_zon",
    "Zonnepanelen": "zonnepanelen_kopen",
}

DEFAULT_BLOCK = "contract_zon"


def block(kind: str, slug: str, position: str = "body") -> str:
    """Rendert één affiliate-blok als HTML-string."""
    spec = _BLOCKS.get(kind) or _BLOCKS[DEFAULT_BLOCK]
    buttons = "\n".join(
        f'        <a class="affiliate-btn" href="{escape(link(p, slug, position), quote=True)}"'
        f' target="_blank" rel="sponsored nofollow noopener">{label}</a>'
        for p, label in spec["buttons"]
    )
    return (
        '    <aside class="affiliate-block" data-intent="%s">\n'
        "      <h3>%s</h3>\n"
        "      <p>%s</p>\n"
        "%s\n"
        '      <p class="affiliate-note">Advertentie &middot; wij ontvangen een vergoeding '
        "als je via deze links een contract afsluit of iets koopt. Dat kost jou niets extra "
        "en heeft geen invloed op wat hierboven staat.</p>\n"
        "    </aside>"
    ) % (kind, spec["title"], spec["intro"], buttons)


def block_for_category(category: str, slug: str, position: str = "body") -> str:
    return block(CATEGORY_BLOCKS.get(category, DEFAULT_BLOCK), slug, position)
