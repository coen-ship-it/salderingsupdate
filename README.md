# salderingsupdate.nl

Statische nieuwssite voor zonnepaneel-eigenaren over het einde van de Nederlandse salderingsregeling (1 januari 2027). Artikelen worden wekelijks automatisch gegenereerd via een Python-agent met Tavily, Qwen en AgentMail.

---

## Projectstructuur

```
salderingsupdate-site/
├── index.html          # Homepage (wordt bijgewerkt door agent.py)
├── artikel.html        # Jinja2-template voor artikelpagina's
├── articles/           # Gegenereerde artikelen (HTML)
│   └── JJJJ-MM-DD-slug.html
├── articles.json       # Machine-leesbare artikelindex
├── agent.py            # Wekelijkse artikelgenerator
├── .env                # Jouw API-keys (niet in Git)
├── .env.example        # Voorbeeld met alle benodigde keys
└── README.md
```

---

## Snel starten

### 1. Vereisten installeren

```bash
pip install tavily-python openai jinja2 python-dotenv requests
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
# Dry-run: test zonder opslaan of mailen
python agent.py --dry-run

# Echt uitvoeren
python agent.py
```

Het script doet automatisch:
1. Zoekt actueel nieuws via **Tavily** (gefilterd op betrouwbare bronnen)
2. Genereert een artikel via **Qwen** (max 250 woorden, neutraal, met bronvermelding)
3. Slaat het op als `articles/JJJJ-MM-DD-slug.html`
4. Werkt `articles.json` en `index.html` bij
5. Stuurt een nieuwsbrief via **AgentMail**

---

## Wekelijkse automatisering

### Cron (Linux/Mac)

```bash
# Elke maandag om 09:00 lokale tijd
crontab -e
0 9 * * 1 cd /pad/naar/salderingsupdate-site && python agent.py >> logs/agent.log 2>&1
```

### GitHub Actions

Maak `.github/workflows/weekly-artikel.yml` aan:

```yaml
name: Wekelijks artikel genereren

on:
  schedule:
    - cron: '0 8 * * 1'   # Elke maandag 08:00 UTC
  workflow_dispatch:        # Handmatig starten

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - run: pip install tavily-python openai jinja2 python-dotenv requests

      - run: python agent.py
        env:
          TAVILY_API_KEY:     ${{ secrets.TAVILY_API_KEY }}
          QWEN_API_KEY:       ${{ secrets.QWEN_API_KEY }}
          AGENTMAIL_API_KEY:  ${{ secrets.AGENTMAIL_API_KEY }}
          AGENTMAIL_INBOX_ID: ${{ secrets.AGENTMAIL_INBOX_ID }}
          AGENTMAIL_LIST_ID:  ${{ secrets.AGENTMAIL_LIST_ID }}
          SITE_BASE_URL:      https://salderingsupdate.nl

      - name: Commit nieuwe artikelen
        run: |
          git config user.name  "salderingsupdate-bot"
          git config user.email "bot@salderingsupdate.nl"
          git add articles/ articles.json index.html
          git diff --staged --quiet || git commit -m "Nieuw artikel: $(date +%Y-%m-%d)"
          git push
```

> Voeg secrets toe via: GitHub repo → Settings → Secrets and variables → Actions

---

## Handmatig specifiek onderwerp

```bash
python agent.py --topic "ISDE subsidie thuisbatterij 2026"
python agent.py --topic "netcongestie terugleverkosten regio"
```

---

## Site publiceren

De site bestaat uit puur statische HTML en werkt op elke host:

| Host | Instructie |
|---|---|
| **GitHub Pages** | Repo-settings → Pages → Branch: `main`, folder: `/` |
| **Netlify** | `netlify deploy --dir .` of drag & drop op [app.netlify.com](https://app.netlify.com) |
| **Replit** | Upload map, stel domein in op `salderingsupdate.nl` |

---

## Redactionele richtlijnen

- Maximaal 250 woorden per artikel (excl. titel/samenvatting)
- Altijd bronvermelding naar rijksoverheid.nl, rvo.nl of acm.nl
- Nooit financieel of juridisch advies
- Nooit concrete bedragen zonder bron en voorbehoud
- Altijd disclaimer: *"Dit is geen financieel of juridisch advies — raadpleeg altijd uw installateur of energieleverancier."*

---

## Licentie

© 2026 salderingsupdate.nl — inhoud vrij te gebruiken met bronvermelding.
