#!/usr/bin/env python3
"""Vult het artikel over de terugleververgoeding met de tabel die de titel belooft.

De titel vroeg "welke leverancier betaalt het meest?" maar de tekst noemde alleen
een bandbreedte van EUR 0,07-0,09 en geen enkele leverancier met een tarief.
Zoekintentie en pagina liepen daardoor uit elkaar.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools import lib

TARGET = lib.ARTICLES_DIR / "2026-03-01-terugleververgoeding-2026-vergelijking.html"
PEILDATUM = "5 juni 2026"

# Bron: kennisbank van Salderen Uitgelegd, peildatum 5 juni 2026.
RIJEN = [
    ("Greenchoice",    "6 – 9 ct",              "Variabel (min. 2 jaar)", "Premie tot 2.000 kWh per jaar, daarna staffel", "beste"),
    ("Eneco",          "5 – 8 ct",              "Vast of dynamisch",      "Dynamische variant volgt EPEX Spot", ""),
    ("Essent",         "5 – 8 ct",              "Vast jaarcontract",      "Losgekoppeld van de spotmarkt", ""),
    ("ANWB Energie",   "5 – 8 ct",              "Vast of variabel",       "Vergelijkbaar met het Eneco-segment", ""),
    ("Vattenfall",     "4 – 7 ct",              "Variabel",               "Volgt de day-ahead prijs", ""),
    ("Budget Energie", "3 – 6 ct",              "Variabel",               "Vergoeding op kostenbasis", ""),
    ("Vandebron",      "daggemiddelde + 1 – 3 ct", "Variabel (min. 2 jaar)", "Premie vervalt bij netcongestie", ""),
    ("Tibber",         "day-ahead − 0,5 – 1,5 ct", "Dynamisch (uurprijs)",   "Negatieve prijzen mogelijk op zonnige uren", ""),
]

NIEUWE_SECTIE = """<h2>Vergelijking per leverancier: wat betalen zij per kWh?</h2>
<p>Onderstaande tarieven zijn bandbreedtes, geen vaste bedragen. Wat u precies krijgt hangt af
van uw contractvorm, de looptijd en het moment waarop u tekent. Gebruik de tabel om te zien in
welke orde van grootte een leverancier zit, en controleer daarna het actuele tarievenblad.</p>

<table class="vergelijk-tabel">
<thead>
<tr><th>Leverancier</th><th>Terugleververgoeding</th><th>Contractvorm</th><th>Bijzonderheden</th></tr>
</thead>
<tbody>
{rijen}
</tbody>
</table>
<p style="font-size:.82rem;color:var(--muted);font-style:italic;margin-top:-.5rem">
Peildatum: {peildatum}. Bedragen in eurocent per teruggeleverde kilowattuur. Bron:
<a href="https://salderenuitgelegd.nl/kennisbank/terugleververgoeding-2027-per-energieleverancier/" rel="noopener nofollow" target="_blank">Salderen Uitgelegd</a>.
Tarieven wijzigen regelmatig; deze tabel wordt maandelijks gecontroleerd.
</p>

<h2>Kijk naar het saldo, niet naar de vergoeding alleen</h2>
<p>Een hoge terugleververgoeding zegt weinig zolang u de kosten niet meerekent. Veel leveranciers
brengen namelijk <a href="/terugleverkosten">terugleverkosten</a> in rekening: een bedrag dat u
juist bétaalt om te mogen terugleveren. Bij de duurste leverancier loopt dat op tot ruim
&euro;&nbsp;380 per jaar bij 2.500 kWh teruglevering; andere leveranciers rekenen niets.</p>

<p>De rekensom die telt is dus:</p>
<div class="tip-box">
<strong>Netto-opbrengst = (teruggeleverde kWh &times; vergoeding per kWh) &minus; terugleverkosten</strong>
</div>

<p>Bij dynamische contracten zit er nog een derde post in: de meeste aanbieders houden een
verkoopvergoeding in van ongeveer 1,3 tot 3,1 eurocent per kWh op de marktprijs. Dat is geen
terugleverkostenpost, maar het drukt uw opbrengst wel. Vraag er expliciet naar voordat u tekent.</p>
"""


def main() -> int:
    html = TARGET.read_text(encoding="utf-8")
    def rij(naam, tarief, vorm, bijz, cls):
        klasse = ' class="%s"' % cls if cls else ""
        return (f"<tr{klasse}><td>{naam}</td><td>{tarief}</td>"
                f"<td>{vorm}</td><td>{bijz}</td></tr>")

    rijen = "\n".join(rij(*r) for r in RIJEN)
    nieuw = NIEUWE_SECTIE.format(rijen=rijen, peildatum=PEILDATUM)

    # De vage sectie vervangen door de echte vergelijking.
    pattern = (r"<h2>Vergelijking per leverancier: Vattenfall, Eneco, Greenchoice en ANWB</h2>"
               r"\s*<p>.*?</p>")
    html, n = re.subn(pattern, lambda _m: nieuw, html, count=1, flags=re.S)
    if n != 1:
        print("  let op: de te vervangen sectie is niet gevonden — artikel ongewijzigd")
        return 1

    # Affiliate-blok afslanken van zes knoppen naar twee.
    m = re.search(r'<div style="background:var\(--black\);color:var\(--white\).*?</div>\s*</div>',
                  html, re.S)
    if m:
        block = m.group(0)
        links = re.findall(r'<a href="[^"]*" class="btn-affiliate"[^>]*>.*?</a>', block, re.S)
        for extra in links[2:]:
            block = block.replace(extra, "")
        block = re.sub(r"\n\s*\n", "\n", block)
        html = html[:m.start()] + block + html[m.end():]

    # dateModified bijwerken zodat de update ook in het schema zichtbaar is.
    html = re.sub(r'"dateModified": "[^"]*"', '"dateModified": "2026-08-25"', html)

    TARGET.write_text(html, encoding="utf-8")
    print(f"artikel bijgewerkt: {TARGET.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
