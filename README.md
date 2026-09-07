# salderingsupdate.nl

Statische nieuwssite voor zonnepaneel-eigenaren over het einde van de Nederlandse
salderingsregeling (1 januari 2027). Artikelen worden gegenereerd via een Python-agent
met Tavily, Qwen en AgentMail, en met de hand geredigeerd vóór publicatie.

---

## Projectstructuur

```
salderingsupdate-site/
├── index.html              # Homepage (artikellijst wordt door agent.py bijgewerkt)
├── nieuws.html             # Nieuwsarchief — gegenereerd uit articles.json
├── regelgeving.html        # Onderwerppagina's
├── thuisbatterijen.html
├── subsidies.html
├── contracten.html
├── terugleverkosten.html   # Vergelijking per leverancier, maandelijks bijwerken
├── faq.html
├── over-ons.html           # Auteur, werkwijze, correctiebeleid, affiliate-beleid
├── privacy.html
├── artikel.html            # Jinja2-template voor artikelpagina's
├── articles/               # Gegenereerde artikelen (HTML)
│   └── JJJJ-MM-DD-slug.html
├── articles.json           # Machine-leesbare artikelindex
├── sitemap.xml             # Gegenereerd — niet met de hand bewerken
├── sitemap-state.json      # Houdt per pagina bij wanneer de inhoud écht wijzigde
├── _redirects              # Gegenereerd — 301 van .html naar de schone URL
├── agent.py                # Artikelgenerator
├── tools/                  # Onderhoudsscripts (zie hieronder)
└── .github/workflows/      # Wekelijkse generatie + controle bij elke PR
```

---

## URL-afspraken

Elke pagina heeft één canonieke URL, **zonder `.html`**:

| Soort | Canonieke URL |
|---|---|
| Homepage | `/` |
| Onderwerppagina | `/thuisbatterijen` |
| Artikel | `/articles/2026-03-01-terugleververgoeding-2026-vergelijking` |

`_redirects` stuurt elke `.html`-variant met een 301 door naar de schone URL. Canonical,
`og:url`, de schema-URL en de sitemap wijzen altijd naar diezelfde schone URL. Voeg je een
pagina toe, draai dan `python tools/build.py` zodat sitemap en redirects meelopen.

---

## Snel starten

### 1. Vereisten installeren

```bash
pip install -r requirements.txt
```

### 2. API-keys instellen

```bash
cp .env.example .env
# Open .env en vul je keys in
```

Benodigde keys:

| Variabele | Waar ophalen |
|---|---|
| `TAVILY_API_KEY` | [app.tavily.com](https://app.tavily.com) |
| `QWEN_API_KEY` | [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com) |
| `AGENTMAIL_API_KEY` | [agentmail.to](https://agentmail.to) |
| `AGENTMAIL_INBOX_ID` | Dashboard AgentMail → Inbox ID |
| `AGENTMAIL_LIST_ID` | Dashboard AgentMail → List ID |

### 3. Eerste artikel genereren

```bash
python agent.py --dry-run     # test zonder opslaan of mailen; werkt zonder keys
python agent.py               # echt uitvoeren
python agent.py --topic "ISDE subsidie thuisbatterij 2026"
```

Het script doet automatisch:

1. Zoekt actueel nieuws via **Tavily** (gefilterd op betrouwbare bronnen)
2. Genereert een artikel via **Qwen** (700–1100 woorden, met koppen en bronvermelding)
3. Slaat het op als `articles/JJJJ-MM-DD-slug.html` via `artikel.html`
4. Werkt `articles.json` en de artikellijst in `index.html` bij
5. Regenereert `nieuws.html`, `sitemap.xml` en `_redirects`
6. Stuurt een nieuwsbrief via **AgentMail**

Het script weigert te publiceren als de template het artikel op `noindex` zou zetten.

---

## Onderhoudsscripts

```bash
python tools/check.py            # controleer de hele site (draait ook in CI)
python tools/build.py            # sitemap.xml + _redirects opnieuw genereren
python tools/make_pages.py       # /nieuws, /over-ons en /terugleverkosten herbouwen
python tools/resync_articles.py  # articles.json opnieuw opbouwen uit articles/
python tools/fix_articles.py     # canonicals, schema, kruimelpad en byline herstellen
python tools/fix_pages.py        # hetzelfde voor index en de onderwerppagina's
```

`tools/check.py` faalt bij een `noindex`, een canonical die niet klopt, ongeldige JSON-LD,
een interne link naar een `.html`-URL of een niet-bestaande pagina, een artikel dat in
`articles.json` of de sitemap ontbreekt, en een ontbrekende 301. Draai hem vóór elke push.

---

## Automatisering

`.github/workflows/wekelijks-artikel.yml` draait elke maandag en donderdag om 08:00
Nederlandse tijd, en is ook handmatig te starten via **Actions → Wekelijks artikel →
Run workflow** (met een eigen onderwerp als je dat wilt).

Voeg de secrets toe via **Settings → Secrets and variables → Actions**:
`TAVILY_API_KEY`, `QWEN_API_KEY`, `AGENTMAIL_API_KEY`, `AGENTMAIL_INBOX_ID`,
`AGENTMAIL_LIST_ID`.

`.github/workflows/controle.yml` draait `tools/check.py` bij elke push en pull request.

---

## Site publiceren

Pure statische HTML. `_redirects` is Netlify-syntax.

| Host | Instructie |
|---|---|
| **Netlify** | `netlify deploy --dir .` of koppel de repo — `_redirects` werkt direct |
| **GitHub Pages** | Repo-settings → Pages → Branch `main`, folder `/` (let op: `_redirects` werkt daar niet) |

---

## Redactionele richtlijnen

- 700–1100 woorden per artikel, verdeeld over vijf tot zeven secties met `<h2>`-koppen
- Elk bedrag, tarief of percentage krijgt een bron **en een peildatum**
- Een titel belooft nooit een vergelijking of tabel die niet in het artikel staat
- Twee tot vier interne links in de lopende tekst, met beschrijvende linktekst
- Bronvermelding naar rijksoverheid.nl, rvo.nl of acm.nl
- Nooit financieel of juridisch advies
- Maximaal twee affiliate-knoppen per artikel, altijd met disclosure
- Altijd de disclaimer: *"Dit is geen financieel of juridisch advies — raadpleeg altijd uw
  installateur of energieleverancier."*

### Maandelijks bijwerken

| Pagina | Wat |
|---|---|
| `/terugleverkosten` | Tarieven per leverancier + peildatum in de tekst en in `tools/make_pages.py` |
| `/articles/2026-03-01-terugleververgoeding-2026-vergelijking` | Tabel in `tools/fix_vergoeding_artikel.py` |

---

## Licentie

© 2026 salderingsupdate.nl — inhoud vrij te gebruiken met bronvermelding.
