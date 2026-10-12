"""Bouwt de drie gerichte 2027-gidsen met de bestaande paginaonderdelen."""
from __future__ import annotations

import json
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import affiliates
from tools import lib, pagegen

CHECKED = "2026-10-12"
TAX = "https://www.belastingdienst.nl/wps/wcm/connect/nl/btw/content/thuisbatterij-btw"
SOLAR_TAX = "https://www.belastingdienst.nl/wps/wcm/connect/bldcontentnl/belastingdienst/zakelijk/btw/tarieven_en_vrijstellingen/goederen_0_btw/btw-tarief-zonnepanelen"
SALDEREN = "https://www.rijksoverheid.nl/themas/klimaat-milieu-en-natuur/energie-thuis/salderingsregeling"


def ads(slug: str, buttons: list[tuple[str, str]]) -> str:
    links = "".join(
        f'<a class="btn-affiliate" href="{escape(affiliates.link(key, slug, key), quote=True)}" '
        f'target="_blank" rel="sponsored nofollow noopener">{label} &rarr;</a>'
        for key, label in buttons
    )
    return f'<div class="guide-ads">{links}</div><p class="guide-note">Advertentie: bij een aankoop of overstap via deze links kunnen wij een vergoeding ontvangen, zonder meerkosten voor u.</p>'


GUIDES = {
    "btw-thuisbatterij-2027": {
        "title": "Btw thuisbatterij 2027: terugvragen, KOR en voorwaarden",
        "description": "Geen 0% btw op thuisbatterijen. Lees wanneer btw-teruggaaf mogelijk is en welke gevolgen stroomhandel, privégebruik en de KOR hebben.",
        "active": "/subsidies",
        "intro": "Een thuisbatterij valt niet onder het 0%-tarief voor zonnepanelen. Btw terugvragen kan onder voorwaarden; beoordeel ook de verplichtingen daarna.",
        "body": f"""
<h2>0% btw en btw-teruggaaf zijn verschillende dingen</h2>
<p>De <a href="{SOLAR_TAX}" target="_blank" rel="noopener">Belastingdienst sluit thuisbatterijen uit van het nultarief voor zonnepanelen</a>. Ook een gezamenlijke offerte voor panelen en opslag maakt de batterij niet automatisch belastingvrij. Vraag een gespecificeerde offerte waarop de onderdelen afzonderlijk zichtbaar zijn.</p>
<h2>Wanneer kunt u de btw terugvragen?</h2>
<p>Volgens de <a href="{TAX}" target="_blank" rel="noopener">Belastingdienst</a> spelen onder meer stroomhandel, een EMS, een dynamisch contract, de tenaamstelling en de KOR een rol. Alleen privégebruik geeft geen recht op teruggaaf. Bij deelname aan de KOR is btw-aftrek niet mogelijk. Stroomhandel brengt aangifte mee; privégebruik kan tot een correctie leiden. Controleer de volledige voorwaarden vóór aanschaf.</p>
<h2>Reken met het btw-bedrag op de factuur</h2>
<p>Voorbeeld: een complete set kost €6.050 inclusief 21% btw. De prijs zonder btw is dan €5.000 en het btw-bedrag €1.050. Het btw-deel is dus niet 21% van de prijs inclusief btw. Dit rekenvoorbeeld zegt niets over uw recht op teruggaaf en bevat geen voorspelde handelsopbrengst.</p>
<p>Maak twee begrotingen: één met de volledige factuurprijs en één met een eventuele teruggaaf die voor uw situatie is onderbouwd. Neem in beide begrotingen meter, installatie, sturing en abonnementen mee. Reserveer ook aandacht voor administratie. Een koopbeslissing die alleen bij maximale teruggaaf betaalbaar lijkt, vraagt extra controle voordat u tekent.</p>
<h2>Vragen voor de aanbieder en uw adviseur</h2>
<ul><li>Wie staat als koper op de offerte en factuur, en wie heeft het energiecontract?</li><li>Ondersteunt het geleverde EMS de gewenste stroomhandel?</li><li>Welke gegevens ontvangt u voor uw administratie?</li><li>Welke teruggaaf is meegenomen in de geadverteerde nettoprijs?</li><li>Wie berekent eventuele correcties en wie doet aangifte?</li><li>Wat gebeurt er bij een overstap, verhuizing of wijziging van gebruik?</li></ul>
<p>Een verkoper kan productinformatie leveren, maar uw fiscale situatie is persoonlijk. Neem uw contract, offerte en eventuele KOR-status mee wanneer u advies vraagt. Bewaar de onderbouwing bij uw koopbeslissing. Kies niet automatisch een dynamisch contract voor een belastingvoordeel: <a href="/contracten">vergelijk eerst de totale contractkosten</a>.</p>
<h2>Welke batterij past bij het beoogde gebruik?</h2>
<p>Een compacte stekkerbatterij voor eigen zonnestroom heeft een andere toepassing dan een professioneel gestuurd handelssysteem. Vergelijk aansluiting, meetapparatuur, software en het vermogen waarmee het systeem werkelijk op het net kan werken. Een uitbreidingsaccu alleen is geen compleet systeem. Bekijk <a href="/thuisbatterijen">de vergelijking van stekkerbatterijen en vaste opslag</a>.</p>
<p>Bij <a href="/articles/2026-04-28-subsidie-thuisbatterij-2027-overzicht">subsidie voor een thuisbatterij</a> gaat het om een andere vraag: een eventuele bijdrage van een overheid of regeling. Btw-teruggaaf is geen algemene aanschafsubsidie. Laat beide posten apart zien en neem een voordeel pas mee wanneer de voorwaarden zijn gecontroleerd.</p>
<h2>Veelgestelde vragen</h2>
<details><summary>Kan iedere koper 21% korting krijgen?</summary><p>Nee. Teruggaaf hangt af van uw situatie en is niet hetzelfde als korting aan de kassa. Gebruik de officiële voorwaarden als uitgangspunt.</p></details>
<details><summary>Moet een aanbieder de batterij met 0% btw factureren?</summary><p>Een thuisbatterij valt niet onder het nultarief voor zonnepanelen. Vraag naar de aparte prijs en het btw-bedrag.</p></details>
<details><summary>Waar vind ik de actuele regels?</summary><p>Bij de Belastingdienst. De bronlinks hierboven verwijzen rechtstreeks naar de uitleg over thuisbatterijen en het btw-tarief voor zonnepanelen.</p></details>
""",
        "buttons": [("homewizard", "HomeWizard bekijken"), ("zendure", "Zendure sets vergelijken")],
    },
    "energiecontract-zonder-terugleverkosten-2027": {
        "title": "Energiecontract zonder terugleverkosten 2027 vergelijken",
        "description": "Vergelijk contracten zonder aparte terugleverkosten voor 2027. Beoordeel ook terugleververgoeding, vaste kosten en dynamische prijsrisico's.",
        "active": "/contracten",
        "intro": "Geen aparte terugleverkosten is één onderdeel van een aanbod. Vergelijk het saldo van alle kosten en vergoedingen met uw eigen teruglevering.",
        "body": f"""
<h2>Waar vindt u een passend aanbod?</h2>
<p>Gebruik een vergelijking voor huishoudens met zonnepanelen en controleer de ingangsdatum. Vul netafname en teruglevering in aan de hand van uw jaarafrekening. Kies daarna een aanbod zonder aparte terugleverkosten en leg het naast een andere contractvorm. Bewaar van beide aanbiedingen het tarievenblad en de voorwaarden. Een algemene leverancierslijst is geen garantie dat ieder product van die leverancier dezelfde kosten heeft.</p>
<h2>Wat betekent zonder terugleverkosten?</h2>
<p>U wilt weten of het concrete aanbod een afzonderlijke kostenpost voor teruglevering rekent. Bekijk daarnaast de terugleververgoeding, vaste levering en eventuele prijsopslag. Een aanbieder kan een voordeel op één post combineren met een andere kostenstructuur. Vraag schriftelijke uitleg als het onduidelijk is welke onderdelen voor uw zonnepanelen gelden.</p>
<p>Met een dynamisch contract hangt de vergoeding samen met het afgesproken prijsmechanisme en het moment van terugleveren. Een lage of negatieve marktprijs is iets anders dan een vaste kostenstaffel, maar beïnvloedt wel de uitkomst. Kijk daarom niet alleen of een vergelijker een vinkje bij terugleverkosten zet.</p>
<h2>Een controleerbare rekensom</h2>
<p>Voor 2027 vergelijkt u: kosten van netafname + vaste leveringskosten + eventuele terugleverkosten − vergoeding voor teruglevering − een korting waarvoor u in aanmerking komt. Voeg voor een complete rekening gas en overige vaste posten toe. Vul deze posten voor ieder aanbod op dezelfde manier in.</p>
<p>Fictief voorbeeld: bij 1.500 kWh teruglevering ontvangt u met aanbod A €0,08 per kWh en betaalt u €180 terugleverkosten. Het saldo van alleen die twee posten is €120 − €180 = −€60. Aanbod B vergoedt €0,04 en rekent geen aparte terugleverkosten: het saldo is €60. B is op deze twee posten €120 gunstiger. Verschillen in inkoopprijs en vaste levering kunnen die uitkomst weer veranderen. Dit zijn geen actuele leveranciersprijzen.</p>
<h2>Welke invloed heeft 2027?</h2>
<p>Salderen stopt op 1 januari 2027. Voor teruglevering komt een aparte vergoeding; de <a href="{SALDEREN}" target="_blank" rel="noopener">Rijksoverheid beschrijft de vergoeding en toegestane kosten</a>. Vraag bij een contract dat over de jaarwisseling loopt welke voorwaarden daarna gelden. Een contractnaam of reclametekst voor 2026 vertelt niet automatisch wat u in 2027 betaalt.</p>
<h2>Vast en dynamisch vergelijken met dezelfde gegevens</h2>
<p>Een vaste leveringstarief kan prettig zijn voor uw begroting. Een dynamisch aanbod vraagt meer aandacht voor tijdstippen. Uw panelen leveren vaak terug wanneer veel andere panelen dat ook doen. Uw afname kan juist in de avond liggen. Kijk daarom naar uw meetprofiel en de mogelijkheden om auto, vaatwasser of warmtepomp te sturen. Een thuisbatterij hoeft daarvoor niet altijd de eerste stap te zijn.</p>
<p>Heeft u weinig overschot, dan kan een lagere inkoopprijs belangrijker zijn dan de terugleververgoeding. Heeft u veel teruglevering, dan krijgt het saldo van vergoeding en kosten meer gewicht. Vergelijk meerdere scenario's wanneer uw jaarafrekening nog geen volledig zonnejaar bevat. Lees <a href="/contracten">de volledige energiecontractvergelijking voor 2027</a> voor de verschillen tussen vast, variabel en dynamisch.</p>
<h2>Checklist voor u overstapt</h2>
<ul><li>Vergelijk dezelfde startdatum en looptijd.</li><li>Controleer of de kosten voor uw contractvorm gelden.</li><li>Neem vaste levering en voorwaarden van kortingen mee.</li><li>Bekijk uw huidige einddatum en mogelijke opzegkosten.</li><li>Vraag wat er verandert als uw teruglevering toeneemt.</li><li>Bewaar het definitieve aanbod waarop u beslist.</li></ul>
<p>De pagina <a href="/terugleverkosten">terugleverkosten per leverancier</a> geeft achtergrond bij de verschillende berekeningen. Gebruik voor een beslissing altijd het actuele aanbod. Controleer uw resultaten opnieuw als uw verbruik verandert door een elektrische auto of warmtepomp.</p>
<h2>Veelgestelde vragen</h2>
<details><summary>Is een contract zonder terugleverkosten altijd goedkoper?</summary><p>Nee. Het totale saldo van inkoop, vaste kosten en vergoeding bepaalt de uitkomst. Vergelijk met uw eigen gegevens.</p></details>
<details><summary>Mag ik alleen de vergoeding vergelijken?</summary><p>Dan mist u belangrijke kosten. Vergelijk vergoeding en terugleverkosten samen, en voeg de overige contractposten toe.</p></details>
<details><summary>Kan mijn teruglevering na een batterij veranderen?</summary><p>Ja. Gebruik waar mogelijk gemeten cijfers en maak een afzonderlijk scenario voor een geplande batterij. Bekijk eerst <a href="/thuisbatterijen">welk systeem bij uw woning past</a>.</p></details>
""",
        "buttons": [("energiekiezer_geen_terugleverkosten", "Zonder terugleverkosten vergelijken"), ("gaslicht", "Alle energiecontracten vergelijken")],
    },
    "zonnepanelen-offerte-2027": {
        "title": "Zonnepanelen offerte 2027: vergelijk complete installaties",
        "description": "Vergelijk zonnepanelenoffertes voor 2027 op opwek, omvormer, montage, garantie en eigen verbruik. Met een checklist voor een complete prijs.",
        "active": "/thuisbatterijen",
        "intro": "Vraag offertes voor dezelfde woning en uitgangspunten. Vergelijk de complete installatie en de verwachte opwek, inclusief de gevolgen van het einde van salderen.",
        "body": f"""
<h2>Begin met uw dak en verbruik</h2>
<p>Een bruikbare zonnepanelenofferte begint bij uw woning. Geef dakrichting, beschikbare ruimte, schaduw en uw jaarverbruik door. Vertel ook over plannen voor een auto of warmtepomp. Een installateur kan daarmee een ontwerp voorstellen dat aansluit op de situatie. Vergelijk niet alleen het aantal panelen: vermogen per paneel, ligging en het ontwerp bepalen samen de verwachte opbrengst.</p>
<p>Vraag bij iedere partij dezelfde informatie op. U kunt bijvoorbeeld een foto van het dak en de meterkast klaarzetten, maar stuur die alleen naar de partijen bij wie u een aanvraag wilt doen. Spreek af of de offerte na een inspectie nog kan wijzigen en welke werkzaamheden buiten de prijs vallen. Op deze site vult u geen aanvraagformulier met persoonsgegevens in; een eventuele aanvraag doet u bij de aanbieder.</p>
<h2>Welke onderdelen moeten in de prijs staan?</h2>
<ul><li>Merk, type, aantal panelen en totaal vermogen in Wp.</li><li>Omvormer en eventuele optimizers, inclusief argument voor die keuze.</li><li>Montagesysteem, kabels, aansluitwerk en bereikbaarheid van het dak.</li><li>Eventuele aanpassing van de meterkast, steiger of extra werkzaamheden.</li><li>Monitoring, oplevering en uitleg over het gebruik.</li><li>Productgarantie, installatiegarantie en wie problemen oplost.</li></ul>
<p>Laat opties apart prijzen. Zo ziet u of een duurdere offerte andere onderdelen bevat of alleen een andere verkoopprijs heeft. Een batterij, laadpaal of abonnement kan de totaalprijs flink veranderen. Vergelijk het zonnepanelensysteem eerst zelfstandig en beoordeel daarna de meerkosten van de uitbreidingen.</p>
<h2>Hoe vergelijkt u de verwachte opbrengst?</h2>
<p>Vraag hoeveel kWh de installatie naar verwachting per jaar opwekt en welke aannames daarvoor zijn gebruikt. Controleer of schaduw en dakligging in die schatting zitten. Een prognose is geen garantie op precies dezelfde opbrengst in ieder kalenderjaar. Vergelijk bij voorkeur ontwerpen met dezelfde uitgangspunten en vraag uitleg wanneer de opbrengsten sterk uiteenlopen.</p>
<p>Een hogere opbrengst kan nuttig zijn, maar de waarde hangt ook af van het moment waarop u die stroom gebruikt. Bekijk uw dagverbruik en de mogelijkheden om apparaten op zonnige uren te gebruiken. Meer panelen is niet automatisch dezelfde extra besparing. Laat een financieel voorbeeld daarom zowel eigen gebruik als teruglevering laten zien.</p>
<h2>Een offerte doorrekenen voor 2027</h2>
<p>De <a href="{SALDEREN}" target="_blank" rel="noopener">salderingsregeling stopt op 1 januari 2027</a>. Vraag een berekening die daarbij past: directe eigen consumptie, vergoeding voor teruglevering en eventuele terugleverkosten als aparte posten. Een berekening die alle productie tegen de consumentenprijs waardeert, vraagt uitleg wanneer u een groot deel van de zonnestroom teruglevert.</p>
<p>Bekijk daarbij <a href="/contracten">energiecontracten voor zonnepanelen</a> en <a href="/energiecontract-zonder-terugleverkosten-2027">aanbiedingen zonder aparte terugleverkosten</a>. Een contract en installatie zijn verschillende beslissingen. Controleer of een geadverteerd voordeel afhankelijk is van een specifieke leverancier en hoe lang die voorwaarde geldt.</p>
<h2>Btw en een batterij op dezelfde offerte</h2>
<p>Voor zonnepanelen op of bij een woning kan het <a href="{SOLAR_TAX}" target="_blank" rel="noopener">0%-btw-tarief</a> gelden. Een thuisbatterij is daarvan uitgesloten. Vraag bij een gecombineerde offerte om afzonderlijke regels voor panelen, batterij en andere werkzaamheden. Lees <a href="/btw-thuisbatterij-2027">de btw-uitleg voor thuisbatterijen</a> voordat u met een nettoprijs rekent.</p>
<h2>Service na de installatie</h2>
<p>Vraag wie u belt bij een storing, binnen welke regio de partij werkt en hoe een garantieclaim wordt afgehandeld. Controleer wie het installatiewerk uitvoert en of de opleverdocumenten bij de prijs horen. Bewaar de definitieve offerte, serienummers, handleidingen en garantievoorwaarden op één plek. Een heldere serviceafspraak kan belangrijker zijn dan een klein prijsverschil.</p>
<h2>Veelgestelde vragen</h2>
<details><summary>Hoeveel offertes moet ik vergelijken?</summary><p>Vergelijk bij voorkeur meerdere complete offertes voor dezelfde uitgangspunten. Vraag verduidelijking bij grote verschillen in ontwerp of inbegrepen werkzaamheden.</p></details>
<details><summary>Moet ik meteen een thuisbatterij nemen?</summary><p>Dat is een aparte keuze. Meet uw verbruik en vergelijk de extra kosten en aansluitvereisten. Bekijk <a href="/thuisbatterijen">de batterijvergelijking</a> voordat u een combinatie kiest.</p></details>
<details><summary>Kan ik hier een offerte aanvragen?</summary><p>De link hieronder gaat naar de aanbieder. Die toont zijn actuele aanbod, voorwaarden en aanvraagmogelijkheden. Controleer of installatie op uw adres wordt aangeboden.</p></details>
""",
        "buttons": [("coolblue_zonnepanelen", "Zonnepanelenaanbod bij Coolblue")],
    },
}


def build(slug: str, spec: dict) -> str:
    path = "/" + slug
    body = f'''<div class="cat-hero"><div class="cat-hero-inner"><h1>{spec["title"]}</h1><p>{spec["intro"]}</p></div></div>
<main class="page-wrap"><section class="guide-section prose"><p class="guide-note">Gecontroleerd op 12 oktober 2026</p>{spec["body"]}
<h2>Vergelijk passende aanbieders</h2>{ads(slug, spec["buttons"])}</section>
<p class="guide-note">Lees ook <a href="/regelgeving">de regels voor 2027</a>, <a href="/subsidies">het subsidieoverzicht</a> en <a href="/nieuws">het nieuwsarchief</a>.</p></main>'''
    webpage = json.dumps({"@context": "https://schema.org", "@type": "WebPage",
        "name": spec["title"], "description": spec["description"], "url": lib.BASE_URL + path,
        "dateModified": CHECKED, "inLanguage": "nl-NL"}, ensure_ascii=False)
    return pagegen.page(path=path, title=spec["title"], description=spec["description"],
        body=body, schema=[webpage], active=spec["active"])


if __name__ == "__main__":
    for slug, spec in GUIDES.items():
        (lib.SITE_DIR / (slug + ".html")).write_text(build(slug, spec), encoding="utf-8")
        print(slug)
