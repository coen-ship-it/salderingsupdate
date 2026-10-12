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
  * tracking per pagina: clickref voor Awin, ws/sub-ID voor Daisycon.

Gebruik:
    from affiliates import block, link
    html = block("batterij_kopen", slug="subsidie-thuisbatterij-2027-overzicht")
"""

from __future__ import annotations

import re
from html import escape

AWIN_AFFID = "2848379"
AWIN_BASE = "https://www.awin1.com/cread.php"
DAISYCON_MEDIA = "419918"


# --------------------------------------------------------------------------
# Partners
# --------------------------------------------------------------------------
# 'fee' is documentatie, geen garantie: Awin-tarieven gecontroleerd op
# 29 sep 2026; Daisycon-aanmeldstatus opnieuw gecontroleerd op 12 okt 2026.

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
        "url": "https://nl.ecoflow.com/pages/ecoflow-stream-plug-in-thuisbatterij",
        "fee": "5% van orderbedrag",
    },
    "allpowers": {
        "mid": "125964",
        "name": "ALLPOWERS",
        "url": "https://iallpowers.nl/collections/bs-pro-energieopslag",
        "fee": "5% van orderbedrag",
    },
    "ecoflow_stream_ac": {
        "mid": "123332",
        "name": "EcoFlow",
        "url": "https://nl.ecoflow.com/products/stream-ac-solar-battery",
        "fee": "5% van orderbedrag",
    },
    "homewizard": {
        "network": "daisycon",
        "base": "https://partner.homewizard.com/c/",
        "si": "18407",
        "li": "1795784",
        "name": "HomeWizard",
        "url": "https://www.homewizard.com/nl/plug-in-battery/",
        "fee": "Plug-In Battery: 4,2% (campagnevoorwaarden controleren)",
    },
    "zendure": {
        "network": "daisycon",
        "base": "https://glp8.net/c/",
        "si": "20779",
        "li": "1881195",
        "name": "Zendure",
        "url": "https://www.zendure.nl/products/zendure-solarflow-2400-ac",
        "fee": "8% (goedgekeurd op 12 oktober 2026)",
    },
    "zendure_balkon": {
        "network": "daisycon",
        "base": "https://glp8.net/c/",
        "si": "20779",
        "li": "1881195",
        "name": "Zendure",
        "url": "https://www.zendure.nl/products/solarflow-800-plus",
        "fee": "8% (goedgekeurd op 12 oktober 2026)",
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
    """Bouwt een deeplink met clickref (Awin) of ws (Daisycon).

    clickref-formaat: <slug>__<positie>  (bijv. 'subsidie-thuisbatterij-2027__intro')
    Terug te vinden in Awin onder Reports > Click References.
    """
    p = PARTNERS[partner]
    ref = _safe_ref(f"{slug}__{position}" if position else slug)
    if p.get("network") == "daisycon":
        from urllib.parse import urlencode, urlsplit

        # Daisycon's generator encodes the destination relative to the campaign host.
        destination = urlsplit(p["url"])
        path = destination.path.lstrip("/")
        if destination.query:
            path += "?" + destination.query
        return p["base"] + "?" + urlencode({
            "si": p["si"], "li": p["li"], "wi": DAISYCON_MEDIA,
            "ws": ref, "dl": path,
        })
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
            "Begin bij het type systeem: een stekkerbatterij voor bestaand zonnestroomgebruik "
            "of een vaste installatie op maat. Vergelijk de complete set, niet alleen de accu."
        ),
        "buttons": [
            ("homewizard", "HomeWizard stekkerbatterij bekijken"),
            ("zendure", "Zendure modulaire batterijsets vergelijken"),
        ],
    },
    "batterij_budget": {
        "title": "Goedkoper alternatief: plug-in opslag",
        "intro": (
            "Stekkerbatterijen kunnen een kleinere eerste stap zijn. Controleer de "
            "stroomgroep, vereiste energiemeter en handleiding; meer vermogen kan een "
            "aparte groep en elektricien vereisen."
        ),
        "buttons": [
            ("ecoflow_stream", "EcoFlow STREAM plug-in batterijen"),
            ("homewizard", "HomeWizard Plug-In Battery"),
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


def comparison_band(slug: str) -> str:
    """Vergelijkroute voor homepage en terugleverkosten."""
    no_costs = escape(link("energiekiezer_geen_terugleverkosten", slug, "zonder-terugleverkosten"), quote=True)
    gaslicht = escape(link("gaslicht", slug, "gaslicht"), quote=True)
    return f'''<section class="compare-band" aria-label="Energie vergelijken zonder terugleverkosten">
  <div><h2>Vergelijk contracten zonder terugleverkosten</h2><p>Gebruik uw netafname en teruglevering. Bekijk ook vaste kosten en terugleververgoeding voordat u kiest.</p></div>
  <div class="compare-band-links"><a href="{no_costs}" target="_blank" rel="sponsored nofollow noopener">Energiekiezer: zonder terugleverkosten &rarr;</a><a href="{gaslicht}" target="_blank" rel="sponsored nofollow noopener">Gaslicht: alle contracten &rarr;</a></div>
  <p class="compare-band-note">Advertentie: bij een overstap kunnen wij een vergoeding ontvangen, zonder meerkosten voor u. Geen aparte terugleverkosten garandeert niet de laagste totaalprijs.</p>
</section>'''
