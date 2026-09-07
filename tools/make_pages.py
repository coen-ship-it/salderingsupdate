#!/usr/bin/env python3
"""Genereert /nieuws, /over-ons en /terugleverkosten."""
from __future__ import annotations

import itertools
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools import lib, pagegen

AUTHOR = "Coen van der Bijl"
CAT_PAGE = {
    "Thuisbatterijen": "/thuisbatterijen", "Subsidies": "/subsidies",
    "Contracten": "/contracten", "Vergoeding": "/contracten",
    "Terugleverkosten": "/terugleverkosten", "Netcongestie": "/regelgeving",
    "Regelgeving": "/regelgeving",
}
CAT_CSS = {"Thuisbatterijen": "batterij", "Subsidies": "subsidie",
           "Regelgeving": "regelgeving", "Netcongestie": "netcongestie",
           "Contracten": "contracten", "Vergoeding": "vergoeding",
           "Terugleverkosten": "vergoeding"}


def crumbs(*trail: tuple[str, str]) -> str:
    parts = ['<nav class="crumbs" aria-label="Kruimelpad">', '<a href="/">Home</a>']
    for i, (label, href) in enumerate(trail):
        parts.append('<span aria-hidden="true">›</span>')
        if i == len(trail) - 1:
            parts.append(f'<span aria-current="page">{label}</span>')
        else:
            parts.append(f'<a href="{href}">{label}</a>')
    parts.append("</nav>")
    return "\n".join(parts)


def breadcrumb_schema(*trail: tuple[str, str]) -> str:
    items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": f"{lib.BASE_URL}/"}]
    for i, (label, href) in enumerate(trail, start=2):
        items.append({"@type": "ListItem", "position": i, "name": label,
                      "item": f"{lib.BASE_URL}{href}"})
    return json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList",
                       "itemListElement": items}, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# /nieuws — volledig chronologisch archief
# ─────────────────────────────────────────────────────────────────────────────

def build_nieuws() -> str:
    articles = lib.load_articles()
    rows = []
    for year, per_year in itertools.groupby(articles, key=lambda a: a["date"][:4]):
        per_year = list(per_year)
        rows.append(f'<h2 class="archive-year">{year}</h2>')
        for month, per_month in itertools.groupby(per_year, key=lambda a: a["date"][:7]):
            m = int(month[5:7])
            rows.append(f'<div class="archive-month">{lib.MONTHS_NL[m - 1]} {year}</div>')
            for a in per_month:
                cat = a["category"]
                css = CAT_CSS.get(cat, "")
                rows.append(
                    f'<article class="stream-article" onclick="location.href=\'{a["url"]}\'">\n'
                    f'  <div class="stream-content">\n'
                    f'    <span class="stream-cat {css}">{cat}</span>\n'
                    f'    <h3><a href="{a["url"]}" style="color:inherit;text-decoration:none;">{a["title"]}</a></h3>\n'
                    f'    <p class="stream-excerpt">{a["summary"]}</p>\n'
                    f'  </div>\n'
                    f'  <div class="stream-date">{a["date_display"]}</div>\n'
                    f'</article>')

    body = f"""
<div class="cat-hero fade-1">
  <div class="cat-hero-inner">
    <h1>Nieuwsarchief: al het nieuws over het einde van de salderingsregeling</h1>
    <p>Alle {len(articles)} artikelen op volgorde van publicatie. Van de politieke besluitvorming
    over de harde stop op 1 januari 2027 tot thuisbatterijen, subsidies, terugleververgoedingen
    en uw rechten als zonnepaneel-eigenaar.</p>
  </div>
</div>

<div class="page-wrap">
  <div class="content-grid">
    <main>
      {crumbs(("Nieuws", "/nieuws"))}
      <div class="article-stream fade-2">
        {"".join(chr(10) + r for r in rows)}
      </div>
    </main>

    <aside>
      <div class="sidebar-block">
        <h3>Onderwerpen</h3>
        <div class="source-list">
          <a href="/regelgeving">Regelgeving en uw rechten</a>
          <a href="/thuisbatterijen">Thuisbatterijen</a>
          <a href="/subsidies">Subsidies</a>
          <a href="/contracten">Energiecontracten</a>
          <a href="/terugleverkosten">Terugleverkosten per leverancier</a>
          <a href="/faq">Veelgestelde vragen</a>
        </div>
      </div>
      <div class="sidebar-block">
        <h3>Officiële bronnen</h3>
        <div class="source-list">
          <a href="https://www.rijksoverheid.nl/themas/klimaat-milieu-en-natuur/energie-thuis/salderingsregeling" rel="noopener" target="_blank">Rijksoverheid — salderingsregeling</a>
          <a href="https://www.acm.nl" rel="noopener" target="_blank">ACM — toezicht energiemarkt</a>
          <a href="https://www.rvo.nl" rel="noopener" target="_blank">RVO — subsidies</a>
        </div>
      </div>
    </aside>
  </div>
</div>
"""

    collection = json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "Nieuwsarchief salderingsregeling",
        "url": f"{lib.BASE_URL}/nieuws",
        "description": "Alle artikelen van SalderingsUpdate.nl over het einde van de salderingsregeling per 1 januari 2027.",
        "inLanguage": "nl-NL",
        "isPartOf": {"@type": "WebSite", "url": f"{lib.BASE_URL}/"},
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": len(articles),
            "itemListElement": [
                {"@type": "ListItem", "position": i, "url": f"{lib.BASE_URL}{a['url']}",
                 "name": a["title"]}
                for i, a in enumerate(articles, start=1)
            ],
        },
    }, ensure_ascii=False, indent=2)

    return pagegen.page(
        path="/nieuws",
        title="Nieuwsarchief salderingsregeling 2027 | SalderingsUpdate.nl",
        description=f"Alle {len(articles)} artikelen over het einde van de salderingsregeling per 1 januari 2027: regelgeving, thuisbatterijen, subsidies, terugleververgoeding en contracten.",
        body=body,
        schema=[collection, breadcrumb_schema(("Nieuws", "/nieuws"))],
        active="/nieuws",
    )


def _main() -> int:
    for name, builder in (("nieuws.html", build_nieuws),
                          ("over-ons.html", build_over_ons),
                          ("terugleverkosten.html", build_terugleverkosten)):
        (lib.SITE_DIR / name).write_text(builder(), encoding="utf-8")
        print(f"  geschreven: {name}")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# /over-ons — auteur, werkwijze, redactiestatuut
# ─────────────────────────────────────────────────────────────────────────────

def build_over_ons() -> str:
    body = f"""
<div class="cat-hero fade-1">
  <div class="cat-hero-inner">
    <h1>Over SalderingsUpdate.nl</h1>
    <p>Wie deze site maakt, hoe de artikelen tot stand komen en hoe wij met bronnen,
    correcties en affiliate-inkomsten omgaan.</p>
  </div>
</div>

<div class="page-wrap">
  <div class="content-grid">
    <main>
      {crumbs(("Over ons", "/over-ons"))}
      <div class="prose fade-2">

        <p>SalderingsUpdate.nl is een onafhankelijke informatiesite voor Nederlandse
        huiseigenaren met zonnepanelen. Aanleiding is één datum: op
        <strong>1 januari 2027</strong> stopt de salderingsregeling. Geen afbouwpad, geen
        overgangsjaar — een harde stop. Voor ongeveer drie miljoen huishoudens verandert
        daarmee de rekensom onder hun zonnepanelen.</p>

        <p>Deze site verzamelt op één plek wat er verandert, wat het kost en welke keuzes
        u nog kunt maken: regelgeving, terugleververgoeding, terugleverkosten, thuisbatterijen,
        subsidies en energiecontracten.</p>

        <h2>Wie maakt deze site</h2>

        <div class="person">
          <div class="person-initials">CB</div>
          <div>
            <h3>{AUTHOR}</h3>
            <p>Oprichter en redacteur van SalderingsUpdate.nl. Verantwoordelijk voor de
            selectie van onderwerpen, de controle van cijfers en de eindredactie van alle
            artikelen op deze site. Bereikbaar via
            <a href="mailto:info@salderingsupdate.nl">info@salderingsupdate.nl</a>.</p>
          </div>
        </div>

        <h2>Hoe onze artikelen tot stand komen</h2>

        <p>Wij volgen wekelijks de publicaties van Rijksoverheid, RVO, de ACM, netbeheerders
        en de grote energieleveranciers. Nieuwsberichten worden opgesteld op basis van die
        primaire bronnen; bij het samenstellen van concepten gebruiken wij
        AI-hulpmiddelen. <strong>Elk artikel wordt vóór publicatie door een mens
        gecontroleerd op feiten, cijfers en bronvermelding.</strong> Wij vinden dat u dat
        moet weten om te kunnen beoordelen wat u leest.</p>

        <p>Onze werkafspraken:</p>
        <ul>
          <li>Elk bedrag, tarief of percentage krijgt een bron en een peildatum.</li>
          <li>Vergelijkingen van leveranciers vermelden altijd waar de cijfers vandaan komen
              en wanneer ze zijn gecontroleerd.</li>
          <li>Wij geven geen financieel of juridisch advies. Wij leggen uit wat de regels zijn
              en wat de gevolgen kunnen zijn; de afweging blijft aan u en uw adviseur.</li>
          <li>Wat wij niet zeker weten, schrijven wij niet op.</li>
        </ul>

        <h2>Hoe vaak werken wij pagina's bij</h2>

        <div class="table-scroll">
          <table class="data">
            <thead><tr><th>Type pagina</th><th>Frequentie</th></tr></thead>
            <tbody>
              <tr><td>Nieuwsberichten</td><td>doorlopend, minimaal wekelijks</td></tr>
              <tr><td>Tarievenvergelijkingen (terugleververgoeding, terugleverkosten)</td><td>maandelijks</td></tr>
              <tr><td>Onderwerppagina's (regelgeving, batterijen, subsidies, contracten)</td><td>bij elke relevante wijziging</td></tr>
              <tr><td>Veelgestelde vragen</td><td>per kwartaal, en direct bij een wetswijziging</td></tr>
            </tbody>
          </table>
        </div>
        <p class="table-note">Elk artikel toont onderaan de publicatiedatum en, als er iets
        gewijzigd is, de datum van de laatste update.</p>

        <h2>Correcties</h2>

        <p>Ziet u een fout? Meld het via
        <a href="mailto:info@salderingsupdate.nl">info@salderingsupdate.nl</a>. Wij corrigeren
        feitelijke fouten zo snel mogelijk en vermelden bij een inhoudelijke wijziging de
        datum waarop het artikel is aangepast. Wij verwijderen geen artikelen om een fout te
        verbergen.</p>

        <h2>Onafhankelijkheid en affiliate-links</h2>

        <p>Deze site bevat affiliate-links. Sluit u via zo'n link een energiecontract af of
        koopt u een product, dan ontvangen wij een commissie van de betreffende aanbieder.
        <strong>Dit kost u niets extra</strong> — u betaalt dezelfde prijs.</p>

        <p>Wat dat wél en niet betekent:</p>
        <ul>
          <li>Onze redactionele keuzes staan los van de commissies. Wij schrijven niet
              positiever over een aanbieder omdat daar een vergoeding tegenover staat.</li>
          <li>Een leverancier kan zich niet inkopen in een vergelijking of ranglijst.</li>
          <li>Affiliate-links zijn herkenbaar aan de aanduiding bij het blok waarin ze staan.</li>
          <li>Wij nemen geen betaalde artikelen, gesponsorde berichten of advertorials op.</li>
        </ul>

        <div class="callout">
          <strong>Geen advies.</strong> De informatie op deze site is algemeen van aard.
          Uw situatie hangt af van uw verbruik, uw installatie, uw contract en uw netbeheerder.
          Raadpleeg altijd uw installateur, energieleverancier of een onafhankelijk adviseur
          voordat u een beslissing neemt.
        </div>

        <h2>Contact</h2>
        <p>Vragen, tips of correcties:
        <a href="mailto:info@salderingsupdate.nl">info@salderingsupdate.nl</a>.
        Zie ook onze <a href="/privacy">privacyverklaring</a>.</p>

      </div>
    </main>

    <aside>
      <div class="sidebar-block">
        <h3>Kernfeiten</h3>
        <div class="fact-rows">
          <div class="fact-row"><span class="fact-label">Onderwerp</span><span class="fact-value">Einde saldering</span></div>
          <div class="fact-row"><span class="fact-label">Stopdatum</span><span class="fact-value danger">1 jan 2027</span></div>
          <div class="fact-row"><span class="fact-label">Redactie</span><span class="fact-value">{AUTHOR}</span></div>
          <div class="fact-row"><span class="fact-label">Contact</span><span class="fact-value">info@salderingsupdate.nl</span></div>
        </div>
      </div>
      <div class="sidebar-block">
        <h3>Onze bronnen</h3>
        <div class="source-list">
          <a href="https://www.rijksoverheid.nl/themas/klimaat-milieu-en-natuur/energie-thuis/salderingsregeling" rel="noopener" target="_blank">Rijksoverheid</a>
          <a href="https://www.acm.nl" rel="noopener" target="_blank">ACM</a>
          <a href="https://www.rvo.nl" rel="noopener" target="_blank">RVO</a>
          <a href="https://www.milieucentraal.nl" rel="noopener" target="_blank">Milieu Centraal</a>
        </div>
      </div>
    </aside>
  </div>
</div>
"""

    about = json.dumps({
        "@context": "https://schema.org",
        "@type": "AboutPage",
        "url": f"{lib.BASE_URL}/over-ons",
        "name": "Over SalderingsUpdate.nl",
        "inLanguage": "nl-NL",
        "isPartOf": {"@type": "WebSite", "url": f"{lib.BASE_URL}/"},
        "mainEntity": {
            "@type": "Organization",
            "name": "SalderingsUpdate.nl",
            "url": f"{lib.BASE_URL}/",
            "logo": {"@type": "ImageObject", "url": f"{lib.BASE_URL}/og-image.png"},
            "email": "info@salderingsupdate.nl",
            "description": "Onafhankelijke informatiesite over het einde van de Nederlandse salderingsregeling per 1 januari 2027.",
            "founder": {"@type": "Person", "name": AUTHOR, "url": f"{lib.BASE_URL}/over-ons"},
            "publishingPrinciples": f"{lib.BASE_URL}/over-ons",
        },
    }, ensure_ascii=False, indent=2)

    return pagegen.page(
        path="/over-ons",
        title="Over ons: wie maakt SalderingsUpdate.nl | SalderingsUpdate.nl",
        description="Wie achter SalderingsUpdate.nl zit, hoe onze artikelen tot stand komen, hoe vaak wij pagina's bijwerken en hoe wij omgaan met bronnen, correcties en affiliate-links.",
        body=body,
        schema=[about, breadcrumb_schema(("Over ons", "/over-ons"))],
    )


# ─────────────────────────────────────────────────────────────────────────────
# /terugleverkosten — vergelijking per leverancier
# ─────────────────────────────────────────────────────────────────────────────

PEILDATUM = "augustus 2026"
PEILDATUM_ISO = "2026-08-25"

# Bron: vergelijking van Zonneplan, peildatum augustus 2026, gerekend met
# 2.500 kWh teruglevering per jaar. Zonneplan is zelf leverancier in deze lijst.
TERUGLEVERKOSTEN = [
    ("Eneco",                "384,03", "Tarief per teruggeleverde kWh",        "bad"),
    ("Vandebron",            "356,25", "Tarief per teruggeleverde kWh",        ""),
    ("Oxxio",                "342,50", "Tarief per teruggeleverde kWh",        ""),
    ("Greenchoice",          "340,00", "Tarief per teruggeleverde kWh",        ""),
    ("Essent / Energiedirect", "308,76", "Staffel op basis van teruglevering", ""),
    ("Vattenfall",           "293,00", "Staffel op basis van teruglevering",   ""),
    ("Budget Thuis",         "257,73", "Vast bedrag per maand",                ""),
    ("Zonneplan",            "0,00",   "Rekent geen terugleverkosten",         "good"),
]

GEEN_KOSTEN = ["Zonneplan", "ANWB Energie", "Frank Energie (onder voorwaarden)", "Tibber"]

FAQ = [
    ("Wat zijn terugleverkosten precies?",
     "Terugleverkosten zijn kosten die uw energieleverancier bij u in rekening brengt omdat u "
     "stroom teruglevert aan het net. Ze staan los van de terugleververgoeding, die u juist "
     "ontvángt voor die stroom. Leveranciers voeren deze kosten op omdat zij extra kosten maken "
     "voor de onbalans die zonnestroom op het net veroorzaakt."),
    ("Wat is het verschil tussen terugleverkosten, terugleververgoeding en salderen?",
     "Salderen betekent dat uw teruggeleverde stroom wordt weggestreept tegen uw verbruik; dat "
     "stopt op 1 januari 2027. De terugleververgoeding is het bedrag dat u per kWh ontvangt voor "
     "stroom die u teruglevert. Terugleverkosten zijn een kostenpost die daar bovenop komt. Uw "
     "netto-opbrengst is dus: vergoeding min terugleverkosten."),
    ("Mag een leverancier zomaar terugleverkosten rekenen?",
     "Ja, leveranciers mogen deze kosten in rekening brengen, maar de ACM houdt er toezicht op en "
     "heeft de terugleverkosten opgenomen in het modelcontract. De ACM doet doorlopend onderzoek "
     "naar de hoogte en de onderbouwing van deze kosten. Uw leverancier moet de kosten vooraf "
     "duidelijk vermelden in het contract en op het tarievenblad."),
    ("Verdwijnen terugleverkosten als de salderingsregeling stopt?",
     "Nee. De verwachting is juist dat meer leveranciers ze gaan rekenen of de tarieven aanpassen. "
     "Het einde van de salderingsregeling verandert niets aan de reden waarom leveranciers deze "
     "kosten opvoeren."),
    ("Hoe verlaag ik mijn terugleverkosten?",
     "Er zijn drie routes: kies een leverancier die geen of lage terugleverkosten rekent, verhoog "
     "uw eigen verbruik overdag zodat u minder teruglevert, of sla het overschot op in een "
     "thuisbatterij. Bij leveranciers met een staffel of een tarief per kWh scheelt minder "
     "teruglevering direct geld."),
]


def build_terugleverkosten() -> str:
    rows = "\n".join(
        f'<tr class="{cls}"><td>{naam}</td><td class="num">&euro;&nbsp;{bedrag}</td><td>{systematiek}</td></tr>'
        for naam, bedrag, systematiek, cls in TERUGLEVERKOSTEN)

    faq_html = "\n".join(
        f"<h3>{q}</h3>\n<p>{a}</p>" for q, a in FAQ)

    body = f"""
<div class="cat-hero fade-1">
  <div class="cat-hero-inner">
    <h1>Terugleverkosten per leverancier ({PEILDATUM}): wat betaalt u voor terugleveren?</h1>
    <p>Steeds meer energieleveranciers brengen kosten in rekening voor het terugleveren van
    zonnestroom. Het verschil tussen de duurste en de goedkoopste loopt op tot ruim
    &euro;&nbsp;380 per jaar. Hieronder de actuele stand, plus wat u eraan kunt doen.</p>
  </div>
</div>

<div class="page-wrap">
  <div class="content-grid">
    <main>
      {crumbs(("Terugleverkosten", "/terugleverkosten"))}
      <div class="prose fade-2">

        <div class="callout">
          <strong>Kort:</strong> terugleverkosten zijn wat u <em>betaalt</em> om terug te leveren.
          De terugleververgoeding is wat u <em>ontvangt</em> voor die stroom. Twee verschillende
          posten — kijk altijd naar het saldo van de twee, niet naar één van beide.
        </div>

        <h2>Terugleverkosten per leverancier</h2>

        <p>De onderstaande bedragen gelden bij een teruglevering van <strong>2.500 kWh per jaar</strong>,
        ongeveer wat een gemiddelde installatie van tien tot twaalf panelen aan het net levert.
        Levert u meer terug, dan lopen de bedragen bij de meeste leveranciers evenredig op.</p>

        <div class="table-scroll">
          <table class="data">
            <thead>
              <tr>
                <th>Leverancier</th>
                <th style="text-align:right">Kosten per jaar</th>
                <th>Systematiek</th>
              </tr>
            </thead>
            <tbody>
              {rows}
            </tbody>
          </table>
        </div>
        <p class="table-note">
          Peildatum: {PEILDATUM}. Bedragen berekend bij 2.500&nbsp;kWh teruglevering per jaar.
          Bron: de leveranciersvergelijking van
          <a href="https://www.zonneplan.nl/energie/zonnepanelen/terugleverkosten" rel="noopener nofollow" target="_blank">Zonneplan</a>.
          Let op: Zonneplan is zelf een van de leveranciers in deze lijst. Tarieven wijzigen
          regelmatig — controleer altijd het actuele tarievenblad van uw eigen leverancier
          voordat u overstapt. Deze pagina wordt maandelijks bijgewerkt.
        </p>

        <h2>Leveranciers zonder terugleverkosten</h2>

        <p>Een deel van de markt rekent (nog) geen terugleverkosten. Dat zijn vooral aanbieders
        met dynamische contracten, waarbij u per uur het marktprijs-tarief krijgt:</p>
        <ul>
          {"".join(f"<li>{n}</li>" for n in GEEN_KOSTEN)}
        </ul>
        <p>Let op: geen terugleverkosten betekent niet automatisch dat u beter uitkomt. Bij een
        dynamisch contract krijgt u op zonnige uren vaak een láge of zelfs negatieve prijs voor
        uw teruggeleverde stroom. Reken door met uw eigen verbruikspatroon — zie ook onze
        vergelijking van <a href="/contracten">dynamische en vaste contracten</a>.</p>

        <h2>Hoe u de rekensom zelf maakt</h2>

        <p>Wilt u weten wat terugleveren u onder de streep oplevert, reken dan met drie getallen:</p>
        <ol>
          <li><strong>Uw teruglevering per jaar in kWh.</strong> Die staat op uw jaarafrekening,
              of u schat hem: ongeveer 55&nbsp;procent van uw opwek gaat bij een gemiddeld huishouden
              terug het net op.</li>
          <li><strong>De terugleververgoeding per kWh</strong> die uw leverancier betaalt.</li>
          <li><strong>De terugleverkosten</strong> uit de tabel hierboven.</li>
        </ol>
        <p>Vermenigvuldig punt 1 met punt 2, trek punt 3 eraf, en u heeft uw netto-opbrengst.
        Loopt die richting nul of eronder, dan is elke kilowattuur die u zélf verbruikt meer waard
        dan een kilowattuur die u teruglevert.</p>

        <h2>Wat u eraan kunt doen</h2>

        <h3>1. Vergelijk vóór u verlengt</h3>
        <p>Het verschil tussen de duurste en de goedkoopste leverancier in de tabel is ruim
        &euro;&nbsp;380 per jaar bij dezelfde teruglevering. Dat is bij verreweg de meeste
        huishoudens groter dan het verschil in leveringstarief. Neem de terugleverkosten dus mee
        als u een contract afsluit of verlengt.</p>

        <h3>2. Verhoog uw eigen verbruik</h3>
        <p>Elke kilowattuur die u overdag zelf gebruikt, levert geen terugleverkosten op én bespaart
        u het volle leveringstarief. Denk aan het verschuiven van de vaatwasser en wasmachine naar
        de middag, een warmtepompboiler die overdag opwarmt, of het sturen van een laadpaal op
        zonopbrengst.</p>

        <h3>3. Sla het overschot op</h3>
        <p>Een thuisbatterij verlaagt uw teruglevering direct. Bij leveranciers met een tarief per
        kWh of een staffel vertaalt dat zich één op één in lagere terugleverkosten — een
        kostenpost die in de terugverdientijd van een batterij vaak wordt vergeten. Zie
        <a href="/thuisbatterijen">thuisbatterijen</a> en onze uitleg over
        <a href="/articles/2026-02-25-thuisbatterij-capaciteit-berekenen">de juiste capaciteit berekenen</a>.</p>

        <h2>Veelgestelde vragen over terugleverkosten</h2>
        {faq_html}

        <h2>Verder lezen</h2>
        <ul>
          <li><a href="/articles/2026-03-01-terugleververgoeding-2026-vergelijking">Terugleververgoeding per leverancier: wie betaalt het meest?</a></li>
          <li><a href="/articles/2026-02-10-redelijke-terugleververgoeding-acm">Wat is een redelijke terugleververgoeding? Het standpunt van de ACM</a></li>
          <li><a href="/articles/2026-02-18-terugleververgoeding-verplicht-rechten">Terugleververgoeding wordt verplicht: uw rechten</a></li>
          <li><a href="/articles/2026-03-07-dynamisch-vast-contract-zonnepanelen">Dynamisch of vast contract met zonnepanelen?</a></li>
          <li><a href="/regelgeving">Alle regelgeving rond het einde van de salderingsregeling</a></li>
        </ul>

        <div class="callout">
          <strong>Geen advies.</strong> Tarieven en voorwaarden verschillen per contract en
          wijzigen regelmatig. Controleer altijd het tarievenblad van uw eigen leverancier
          voordat u een beslissing neemt.
        </div>

      </div>
    </main>

    <aside>
      <div class="sidebar-block">
        <h3>Kernfeiten</h3>
        <div class="fact-rows">
          <div class="fact-row"><span class="fact-label">Duurste ({PEILDATUM})</span><span class="fact-value danger">&euro; 384/jaar</span></div>
          <div class="fact-row"><span class="fact-label">Goedkoopste</span><span class="fact-value">&euro; 0/jaar</span></div>
          <div class="fact-row"><span class="fact-label">Gerekend met</span><span class="fact-value">2.500 kWh</span></div>
          <div class="fact-row"><span class="fact-label">Toezicht</span><span class="fact-value">ACM</span></div>
          <div class="fact-row"><span class="fact-label">Bijgewerkt</span><span class="fact-value">{PEILDATUM}</span></div>
        </div>
      </div>
      <div class="sidebar-block">
        <h3>Officiële bronnen</h3>
        <div class="source-list">
          <a href="https://www.acm.nl/nl/publicaties/acm-doet-nader-onderzoek-naar-kosten-en-vergoeding-zonnestroom" rel="noopener" target="_blank">ACM — onderzoek terugleverkosten</a>
          <a href="https://www.rijksoverheid.nl/themas/klimaat-milieu-en-natuur/energie-thuis/salderingsregeling" rel="noopener" target="_blank">Rijksoverheid — salderingsregeling</a>
          <a href="https://www.milieucentraal.nl/energie-besparen/zonnepanelen/salderingsregeling-voor-zonnepanelen/" rel="noopener" target="_blank">Milieu Centraal — salderen</a>
        </div>
      </div>
      <div class="sidebar-block">
        <h3>Andere onderwerpen</h3>
        <div class="source-list">
          <a href="/contracten">Energiecontracten</a>
          <a href="/thuisbatterijen">Thuisbatterijen</a>
          <a href="/subsidies">Subsidies</a>
          <a href="/regelgeving">Regelgeving</a>
          <a href="/nieuws">Al het nieuws</a>
        </div>
      </div>
    </aside>
  </div>
</div>
"""

    webpage = json.dumps({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "url": f"{lib.BASE_URL}/terugleverkosten",
        "name": f"Terugleverkosten per leverancier ({PEILDATUM})",
        "description": "Actuele vergelijking van de terugleverkosten per energieleverancier, met uitleg over het verschil met de terugleververgoeding en hoe u de kosten verlaagt.",
        "inLanguage": "nl-NL",
        "isPartOf": {"@type": "WebSite", "url": f"{lib.BASE_URL}/"},
        "dateModified": PEILDATUM_ISO,
        "author": {"@type": "Person", "name": AUTHOR, "url": f"{lib.BASE_URL}/over-ons"},
        "publisher": {"@type": "Organization", "name": "SalderingsUpdate.nl",
                      "url": f"{lib.BASE_URL}/"},
    }, ensure_ascii=False, indent=2)

    faq_schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in FAQ
        ],
    }, ensure_ascii=False, indent=2)

    return pagegen.page(
        path="/terugleverkosten",
        title=f"Terugleverkosten per leverancier {PEILDATUM} | SalderingsUpdate.nl",
        description="Vergelijk de terugleverkosten van Eneco, Vattenfall, Essent, Budget Thuis en anderen. Verschil tot ruim €380 per jaar, plus uitleg en drie manieren om de kosten te verlagen.",
        body=body,
        schema=[webpage, faq_schema, breadcrumb_schema(("Terugleverkosten", "/terugleverkosten"))],
        active="/terugleverkosten",
    )


if __name__ == "__main__":
    raise SystemExit(_main())
