# Affiliate clicks

`affiliate_click` telt een klik, geen lead, aankoop of commissie. Omzet en de
goedkeuring daarvan blijven afkomstig uit Awin en Daisycon. Tel dit event niet
op bij het bestaande GA4-event `click`: dezelfde actie kan beide activeren.

De meting gebruikt de bestaande Google-tag. De extra parameters bevatten geen
formulierwaarden of volledige tracking-URL. Er worden geen nieuwe cookies of
eigen gebruikers-ID's toegevoegd. Blokkeren van Analytics blijft mogelijk.

De geregistreerde partners komen uit `affiliates.py`. Na een wijziging:

```sh
python tools/sync_affiliate_tracking.py
```

Dit genereert `assets/affiliate-config.js` en plaatst de twee scripts idempotent
in bestaande pagina's en het artikeltemplate. Nieuwe pagegen-pagina's bevatten
de scripts ook. Alleen productie registreert echte klik- en middenklikacties;
lokale tests en Netlify-previews versturen deze extra events niet. De externe
Daisycon-widget zit buiten deze klikmeting; transacties via de tool controleer
je in Daisycon zelf. Bol-links vallen buiten de centrale partnerregistry.

## Rapportage

Filter in GA4 op gebeurtenisnaam `affiliate_click`. Gebruik de bestaande
dimensies Linkdomein (`link_domain`), Link-ID (`link_id`, pagina plus positie)
en Linkklassen (`link_classes`, netwerk). De pagina wordt door GA4 meegegeven.
De aanvullende parameters `affiliate_partner`, `affiliate_network`,
`affiliate_campaign` en `affiliate_placement` staan in Realtime/DebugView;
voor historische uitsplitsing via die namen zijn aangepaste dimensies nodig.
Die accountinstellingen worden niet automatisch gewijzigd door deze code.

De gegevens beginnen bij publicatie, niet met terugwerkende kracht. Gebruik
nooit het verschil tussen netwerkklikken en GA4-klikken als een conversieratio:
periodes, blokkades, testklikken en telmethoden kunnen verschillen.
