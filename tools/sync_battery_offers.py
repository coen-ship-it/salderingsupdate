"""Synchroniseer de gecontroleerde, tijdelijk zichtbare batterijaanbiedingen.

Hercontroleer prijzen EN netwerkvoorwaarden voor een nieuwe geldigheidsperiode.
De zichtbaarheidstermijn is onze hercontrolegrens, niet de einddatum van de sale.
"""
from html import escape
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import affiliates

ROOT = Path(__file__).resolve().parent.parent
START = "<!-- battery-offers:start -->"
END = "<!-- battery-offers:end -->"
UNTIL = "2026-11-21T00:00:00+01:00"
RESOURCES = ('<link rel="stylesheet" href="/assets/battery-offers.css">\n'
             '<script defer src="/assets/battery-offers.js"></script>\n')


def render(slug, compact=False):
    def url(partner, placement):
        return escape(affiliates.link(partner, slug, placement), quote=True)

    tag = "h3" if compact else "h2"
    card_tag = "h4" if compact else "h3"
    other = (f'<p class="deal-note">Andere optie: <a href="{url("nextenergy_batterij", "bf2026-nextenergy-alternatief")}" '
             'target="_blank" rel="sponsored nofollow noopener">NextEnergy stekkerbatterij</a>. '
             'De aangeboden terugverdiengarantie heeft contractvoorwaarden, waaronder een dynamisch '
             'stroomcontract bij NextEnergy. Vergelijk ook die contractkosten.</p>') if compact else ""
    return f'''{START}
<section class="battery-deals" id="tijdelijke-batterijprijzen" aria-labelledby="deal-heading" data-offer-until="{UNTIL}" hidden>
  <p class="deal-label">Black Friday · gecontroleerd op <time datetime="2026-11-14">14 november 2026</time></p>
  <{tag} id="deal-heading">Vergelijk tijdelijke batterijprijzen</{tag}>
  <p>Een lagere aankoopprijs is geen subsidie of garantie op rendement. Kies eerst de passende opslag en aansluiting. Prijzen hieronder zijn inclusief btw; controleer de actuele totaalprijs en levering bij de aanbieder.</p>
  <div class="deal-list">
    <article class="deal-card">
      <{card_tag}>HomeWizard Plug-In Battery</{card_tag}>
      <p class="deal-type">Met stekker · 2,7 kWh</p>
      <p class="deal-price">€ 1.075</p>
      <p>P1-meter nodig. Nog geen geschikte meter? De P1-meter kost € 19,95: samen € 1.094,95 vóór eventuele extra benodigdheden of verzendkosten.</p>
      <a class="deal-button" href="{url('homewizard', 'bf2026-homewizard')}" target="_blank" rel="sponsored nofollow noopener">Bekijk HomeWizard-prijs →</a>
    </article>
    <article class="deal-card">
      <{card_tag}>Zendure SolarFlow 2400 AC+</{card_tag}>
      <p class="deal-type">Ingebouwde opslag · 2,4 kWh</p>
      <p class="deal-price">€ 849</p>
      <p>Werkt naast bestaande zonnepanelen. Controleer de meegeleverde meter en de stroomgroep. Uitbreidbaar met passende AB3000L-accu's.</p>
      <p><strong>Code KQ135 geldt niet voor dit model.</strong></p>
      <a class="deal-button" href="{url('zendure_black_friday', 'bf2026-zendure-ac-plus')}" target="_blank" rel="sponsored nofollow noopener">Bekijk Zendure-actie →</a>
    </article>
    <article class="deal-card">
      <{card_tag}>Zendure 2400 AC + 2× AB3000X</{card_tag}>
      <p class="deal-type">Modulaire set · 5,76 kWh</p>
      <p class="deal-price">€ 1.209</p>
      <p>Dit is de set mét twee accu's. Andere serie dan de AC+: let bij uitbreiding op passende modules, meter en aansluiting.</p>
      <p><strong>Actiecode: <code>KQ135</code></strong> — 8% extra op geselecteerde producten, waaronder de 2400 AC. Controleer de gekozen set en korting bij afrekenen; bovenstaande prijs is vóór de code.</p>
      <a class="deal-button" href="{url('zendure_black_friday', 'bf2026-zendure-ac-set')}" target="_blank" rel="sponsored nofollow noopener">Bekijk set en codevoorwaarden →</a>
    </article>
  </div>
  <p class="deal-note"><strong>Advertentie:</strong> via deze links kunnen wij bij aankoop een vergoeding ontvangen, zonder meerkosten voor u. KQ135 is volgens de netwerkpromotie actief t/m 7 december 2026; de 2400 AC+, 2400 Pro en Mix 4000 Pro zijn uitgesloten. Voorraad, prijzen en acties kunnen eerder wijzigen. Cadeaus en eventuele installatiekosten zijn niet in de vergelijking meegerekend.</p>
  <p class="deal-note">Prijsbronnen: <a href="https://www.homewizard.com/nl/plug-in-battery/" target="_blank" rel="noopener">HomeWizard batterij</a> · <a href="https://www.homewizard.com/nl/shop/wi-fi-p1-meter/" target="_blank" rel="noopener">P1-meter</a> · <a href="https://www.zendure.nl/pages/black-friday" target="_blank" rel="noopener">Zendure actiepagina</a>. <a href="/thuisbatterijen#batterij-aanbieders">Bekijk ook de verschillen tussen batterijtypen en aanbieders</a>.</p>
{other}
</section>
{END}'''


def main():
    pages = [
        (ROOT / "thuisbatterijen.html", "thuisbatterijen", False),
        (ROOT / "articles/2026-04-28-subsidie-thuisbatterij-2027-overzicht.html",
         "subsidie-thuisbatterij-2027-overzicht", True),
    ]
    changed = 0
    for path, slug, compact in pages:
        original = path.read_text(encoding="utf-8")
        html = original
        block = render(slug, compact)
        if START in html:
            html = re.sub(re.escape(START) + r".*?" + re.escape(END),
                          lambda _: block, html, count=1, flags=re.S)
        elif compact:
            html, count = re.subn(r'<aside class="affiliate-block" data-intent="batterij_kopen">.*?</aside>',
                                 lambda _: block, html, count=1, flags=re.S)
            if count != 1:
                raise ValueError(f"Batterijblok ontbreekt: {path}")
        else:
            marker = '<section class="battery-guide" id="batterij-aanbieders"'
            if marker not in html:
                raise ValueError(f"Vergelijking ontbreekt: {path}")
            html = html.replace(marker, block + "\n      " + marker, 1)
        if RESOURCES not in html:
            html = html.replace("</head>", RESOURCES + "</head>", 1)
        if html != original:
            path.write_text(html, encoding="utf-8")
            changed += 1
    print(f"Batterijaanbiedingen: {changed} pagina's gewijzigd.")


if __name__ == "__main__":
    main()
