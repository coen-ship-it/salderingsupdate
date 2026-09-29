# Groeiplan Q4 2026 — salderingsupdate.nl

Opgesteld 7 september 2026, op basis van Search Console (t/m 4 sep), Awin
(year-to-date) en Daisycon (laatste 31 dagen).

De harde deadline is **1 januari 2027**. Alles wat consumenten nu zoeken —
"energiecontract 2027 vergelijken", "subsidie thuisbatterij 2027" — gaat over een
keuze die zij vóór die datum moeten maken. Oktober tot december is de piek, en
content heeft vier tot acht weken nodig om te ranken. Wat in november nog
gepubliceerd moet worden, is te laat.

---

## 1. Waar we vandaan komen

| Bron | Stand |
|---|---|
| Search Console, 28 dagen | 56 klikken, 3.070 vertoningen, CTR 1,8%, positie 8,1 |
| Search Console, groei | 0,72 → 2,0 klikken per dag in twee maanden |
| Awin, year-to-date | 65 uitgaande klikken, 0 transacties, € 0,00 |
| Daisycon, 31 dagen | 3 klikken, 0 transacties, € 0,00 |

Ongeveer de helft van de bezoekers klikt door naar een adverteerder. Het
probleem zit ná de klik, niet ervoor.

Statistisch zegt 0 uit 68 dit: de 95%-bovengrens van de conversie ligt op
3/68 ≈ **4,4%**. Alles tussen 0 en 4% past nog in de data; 5% of meer is al
onwaarschijnlijk. Er is dus nog geen enkel bewijs dát het werkt — daarom staat
meten in stap 2 vóór schalen in stap 3.

---

## 2. Wat er in deze PR is gerepareerd

Vier dingen waren stuk. Ze verklaren niet alle nullen, maar ze zorgden er wel
voor dat werk verdampte.

**De generator publiceerde onvindbare pagina's.** `artikel.html` had
`<meta name="robots" content="noindex, nofollow">`. Elk artikel dat de agent
voortaan maakt zou door Google zijn genegeerd. Nu `index, follow`, met canonical
en NewsArticle-schema.

**De generator publiceerde pagina's zonder verdienmodel.** De template bevatte
geen enkele affiliate-link; de 21 bestaande artikelen zijn achteraf met de hand
aangevuld. Nu krijgt elk nieuw artikel automatisch het blok dat bij zijn
categorie hoort, via `affiliates.py`.

**De homepage werd niet meer bijgewerkt.** `update_index()` zoekt naar
`<!-- ARTICLE_LIST_START -->`, en die markeringen stonden niet in `index.html`.
De functie sloeg elke run stilletjes over. Markeringen toegevoegd; de generator
produceert nu dezelfde crawlbare markup als de handmatige versie.

**De rekentool op de homepage lekte klikken.** De affiliate-URL's stonden in een
`<script>`-blok met `&amp;` erin. Binnen JavaScript worden HTML-entities niet
gedecodeerd, dus Awin kreeg `amp;awinaffid` als parameternaam en zag geen geldig
affiliate-ID. Klikken vanaf de best converterende plek op de site werden
waarschijnlijk niet toegekend.

Daarnaast: sitemap wordt nu automatisch bijgewerkt, de vier nieuwste artikelen
stonden niet in `articles.json`, en één niet-gesloten `<p>` in `faq.html` is
gerepareerd.

---

## 3. Meten: clickref per pagina

Elke affiliate-link heeft nu een `clickref` in de vorm `<slug>__<positie>`,
bijvoorbeeld `subsidie-thuisbatterij-2027-overzicht__na-isde`.

Terug te vinden in **Awin → Reports → Click References**. Binnen twee weken
weet je daarmee welke pagina en welke plek in het artikel klikken opleveren —
en welke niet. Zonder dat blijft elke volgende optimalisatie giswerk.

Wat je wekelijks bijhoudt, met de cijfers van 6 september als nulmeting:

| Meting | Nu | Doel eind december |
|---|---|---|
| Organische klikken per maand | ~70 | 150–200 |
| CTR Search Console | 1,8% | 3%+ |
| Affiliate-klikken per maand | ~12 | 60+ |
| Transacties | 0 | de eerste |

Die eerste transactie is de belangrijkste mijlpaal die er is. Pas daarna weet je
of het model klopt, en is het zinvol om op volume te sturen.

---

## 4. Contentplan oktober – december

Prioritering op basis van vertoningen die je al hebt en waar je niets mee doet.
Alle posities uit Search Console, laatste zes maanden.

### Blok A — publiceren in september (nog op tijd voor de piek)

**A1. "Kun je salderen met een dynamisch contract?"**
Cluster: `salderen met dynamisch contract` (150 vert., pos 74), `salderen
dynamisch contract` (13, pos 91), `dynamisch contract en salderen` (44, pos 58),
`salderen bij dynamisch contract` (8, pos 86), `dynamisch energiecontract en
salderen` (3, pos 92). Samen ~220 vertoningen waar je nergens in de buurt komt.
Er is geen pagina die deze vraag rechtstreeks beantwoordt.
Affiliate-blok: `contract_zon`.

**A2. "Energiecontract zonder terugleverkosten — welke leveranciers?"**
Cluster: `energiecontract zonder terugleverkosten` (25, pos 40),
`energiecontract zonder terugleverboete` (9, pos 40), `vast energiecontract
zonder terugleverkosten` (6, pos 35), `energieleverancier zonder
terugleverkosten 2026/2027` (4, pos 40+). Commercieel de sterkste cluster die je
hebt: EnergieKiezer heeft hier een exacte landingspagina voor en betaalt € 22
vast per overstap.
Affiliate-blok: `terugleverkosten`.

**A3. "Beste energieleverancier met zonnepanelen in 2027"**
Cluster: `beste energiecontract met zonnepanelen 2027` (28, pos 14), `beste
energiecontract 2027` (18, pos 10), `beste energieleverancier met zonnepanelen
2027` (10, pos 11), `welke energieleverancier met zonnepanelen 2027` (2, pos 14).
Je staat hier al net buiten de top 10 — een eigen pagina in plaats van een
zijstraat van `/contracten` kan dit binnenhalen.
Affiliate-blok: `beste_leverancier`.

### Blok B — oktober

**B1. Wekelijkse statuspagina "Salderingsregeling: stand van zaken"**
Cluster: `salderingsregeling nieuws` (22, pos 19), `salderingsregeling laatste
nieuws` (2 klikken, pos 12), `salderingsregeling 2026 status` en varianten
(~60 vert., pos 7–10). Dit is de belofte van het domein, en er is sinds
13 mei niets meer gepubliceerd. Eén URL die elke week wordt bijgewerkt, met de
datum zichtbaar en in `dateModified`, wint dit soort zoekopdrachten.
Dit is ook de natuurlijke taak voor de agent: laat hem deze pagina updaten in
plaats van steeds een nieuw artikel te maken.

**B2. Gemeente-database lokale subsidies**
Cluster: `lokale subsidie thuisbatterij` (58, pos 34), `subsidie thuisbatterij
<gemeente>` (Limburg, Nijmegen, Zaanstad, Zeeland, Alkmaar — elk 1 vertoning,
pos 3–4). Die losse gemeentenamen zijn het signaal: er is een longtail van
honderden gemeenten en je rankt er nu al voor met één alinea. Een echte tabel
met alle gemeenten, per regeling en bedrag, is veel werk maar blijft ook ná
1 januari 2027 relevant.

**B3. "Terugleververgoeding vergelijken 2027"**
Cluster: `terugleververgoeding vergelijken` (6, pos 26),
`terugleververgoedingen vergelijken` (2, pos 20), `hoogste terugleververgoeding
2027` (3, pos 17), `dynamische terugleververgoeding` (4, pos 27). Maandelijks
bij te werken tabel. Sterke aanleiding voor de `terugleverkosten`-CTA.

### Blok C — november, als A en B staan

Verdieping op `dynamisch contract na 2027` (147 vert., pos 29) en
`energie vergelijken vanaf 2027`. Deze cluster is groot maar je staat te ver
weg; hij vraagt eerst autoriteit uit blok A.

### Wat je niet moet doen

Geen nieuwe artikelen over onderwerpen waar je al op positie 2–6 staat
(`subsidie thuisbatterij 2027`, `thuisbatterij subsidie 2026`). Daar is de
winst CTR en conversie, niet meer content — een tweede pagina over hetzelfde
onderwerp concurreert met je eigen resultaat.

---

## 5. Programma-mix

Wat je nu hebt, met de tarieven zoals ze op 6 september in Awin stonden:

| Programma | Tarief | Klikken YTD |
|---|---|---|
| Coolblue Energie NL | € 0 – 50 per aanvraag | 23 |
| Ecoflow NL | 5% van orderbedrag | 12 |
| Gaslicht.com NL | € 9,46 vast | 9 |
| EnergieKiezer NL | € 22,00 vast | 9 |
| ALLPOWERS NL | 5% van orderbedrag | 8 |
| Overstappen NL | € 0 – 35 | 4 |
| Coolblue NL | 2% – 15% | 0 |
| Daisycon: Energievergelijker NL | onbekend | 3 (31 dgn) |

Drie observaties.

**Coolblue NL stond ongebruikt.** Goedgekeurd, 2–15% commissie, en het is het
enige programma waarmee je een thuisbatterij van vier cijfers kunt verkopen.
Nu gekoppeld aan `/thuisbatterijen` en `/zonnepanelen` in `affiliates.py`.

**Gaslicht.com betaalt € 9,46 waar EnergieKiezer € 22 betaalt** voor
vergelijkbaar verkeer. Gaslicht blijft als tweede optie staan, maar EnergieKiezer
is nu de primaire link in de contract-blokken.

**Let op de betaaltermijn van Coolblue Energie.** Auto-validatie 90 dagen,
gemiddelde betaaltermijn 112 dagen, en het programma staat op Exposure Level 2
(adverteerder boven kredietlimiet, geen automatische incasso). Een aanvraag in
oktober is geld in februari. Leun er niet alleen op.

### Uit te zoeken

Zoek in de Awin advertiser directory en de Daisycon marketplace op
*thuisbatterij*, *zonnepanelen*, *dynamisch energiecontract* en *energieopslag*,
en beoordeel elk programma op vier dingen voordat je aanmeldt:

1. vaste vergoeding per lead of percentage van het orderbedrag — bij hardware
   is een percentage bijna altijd beter;
2. validatie- en betaaltermijn;
3. exposure level (kredietwaardigheid van de adverteerder);
4. of er een landingspagina is die past bij de zoekintentie, niet alleen een
   homepage.

Daisycon is nu één campagne. Dat netwerk heeft de meeste Nederlandse
energie-adverteerders; meer campagnes aanvragen is de goedkoopste uitbreiding
die er is.

---

## 6. Volgorde

1. Deze PR mergen en deployen. Daarna in Search Console de
   `subsidie-thuisbatterij-2027`-pagina laten herindexeren, zodat de nieuwe
   titel snel meedraait.
2. Agent weer aanzetten. Hij heeft sinds 13 mei niets gepubliceerd, en dat is
   op een nieuwssite over een deadline in januari het duurste dat er is.
3. Blok A publiceren in september.
4. Na twee weken: Awin Click References openen. Welke pagina levert klikken?
   Als één pagina alle klikken levert en de rest niets, ligt het aan plaatsing.
   Als alle pagina's klikken leveren en niets converteert, ligt het aan de
   bestemming of het programma.
5. Blok B in oktober, blok C in november — mits de meting in stap 4 zegt dat
   het werkt.

---

## Bestanden in deze PR

| Bestand | Wat |
|---|---|
| `affiliates.py` | nieuw — alle partners, deeplinks, tarieven en clickref op één plek |
| `artikel.html` | herschreven template: indexeerbaar, huisstijl, schema, affiliate-blok |
| `agent.py` | canonical + datums, affiliate-blok, sitemap-update, crawlbare artikellijst |
| `tools/upgrade_affiliate_links.py` | eenmalige migratie van 107 bestaande links |
| `index.html` | JS-affiliate-bug, betere aanbevelingen in de rekentool, lijst-markeringen |
| `contracten.html` | titel op zoekintentie, werkende CTA boven de vergelijker |
| `articles/` + hubs | 107 links met deeplink en clickref, advertentie-vermelding |
| `articles.json` | vier ontbrekende artikelen toegevoegd |
