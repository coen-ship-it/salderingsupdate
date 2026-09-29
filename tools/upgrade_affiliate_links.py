#!/usr/bin/env python3
"""
Eenmalige migratie van de bestaande HTML-pagina's.

Doet drie dingen:
  1. Vervangt elke Awin-link door de variant uit affiliates.py: juiste deeplink
     (categoriepagina in plaats van homepage) plus clickref, zodat in Awin
     zichtbaar wordt welke pagina de klik heeft opgeleverd.
  2. Zet rel="sponsored nofollow noopener" op alle affiliate-links.
  3. Voegt een korte advertentie-vermelding toe onder elk affiliate-blok en de
     bijbehorende CSS, als die er nog niet staat.

Idempotent: twee keer draaien verandert niets extra.

    python3 tools/upgrade_affiliate_links.py [--dry-run]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import affiliates  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# Awin-programma-ID -> partnersleutel in affiliates.PARTNERS
MID_TO_PARTNER = {
    "123332": "ecoflow",
    "125964": "allpowers",
    "119703": "vatrer",
    "85163": "coolblue_energie",
    "85161": "coolblue_thuisbatterij",
    "8520": "gaslicht",
    "68288": "energiekiezer_zon",
    "65020": "overstappen",
}


def partner_for_query(query: str) -> str | None:
    """Kiest binnen een Awin-programma de juiste deeplinkvariant."""
    params = parse_qs(query)
    mid = params.get("awinmid", [""])[0]
    destination = params.get("ued", [""])[0]

    if mid == "68288":
        if "zonder-terugleverkosten" in destination:
            return "energiekiezer_geen_terugleverkosten"
        if "beste-energieleverancier" in destination:
            return "energiekiezer_beste_leverancier"
    if mid == "85161" and "/zonnepanelen" in destination:
        return "coolblue_zonnepanelen"
    return MID_TO_PARTNER.get(mid)

AWIN_RE = re.compile(r'href="https://www\.awin1\.com/cread\.php\?([^"]*)"')
REL_RE = re.compile(r'(<a class="affiliate-btn"[^>]*?)rel="[^"]*"')

NOTE_HTML = (
    '      <p class="affiliate-note">Advertentie &middot; wij ontvangen een vergoeding als je '
    "via deze link een contract afsluit of iets koopt. Dat kost jou niets extra en heeft geen "
    "invloed op de inhoud hierboven.</p>\n"
)
NOTE_CSS = (
    ".affiliate-block{position:relative}"
    ".affiliate-note{font-size:.72rem;color:var(--muted);margin:.9rem 0 0;line-height:1.45}"
)


def slug_for(path: Path) -> str:
    """Bestandsnaam -> clickref-slug, zonder datumprefix."""
    stem = path.stem
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", stem)


def rewrite_links(html: str, slug: str) -> tuple[str, int]:
    count = 0

    def repl(m: re.Match) -> str:
        nonlocal count
        query = m.group(1).replace("&amp;", "&")
        partner = partner_for_query(query)
        if not partner:
            return m.group(0)
        # Een clickref die er al staat blijft staan: die is bewust gezet
        # (bijvoorbeeld '__na-isde' voor een blok hoger in het artikel).
        existing = re.search(r"clickref=([^&]+)", query)
        position = ""
        if existing and "__" in existing.group(1):
            position = existing.group(1).split("__", 1)[1]
        count += 1
        url = affiliates.link(partner, slug, position or "body").replace("&", "&amp;")
        return f'href="{url}"'

    return AWIN_RE.sub(repl, html), count


def upgrade_rel(html: str) -> str:
    return REL_RE.sub(r'\1rel="sponsored nofollow noopener"', html)


def add_notes(html: str) -> str:
    """Zet één advertentie-vermelding onderaan elk affiliate-blok."""
    if "affiliate-note" in html:
        return html
    out, idx = [], 0
    for m in re.finditer(r'<div class="affiliate-block">.*?</div>', html, re.S):
        block = m.group(0)
        if "affiliate-btn" not in block:
            continue
        new_block = block[: block.rfind("</div>")] + NOTE_HTML + "    </div>"
        out.append(html[idx : m.start()])
        out.append(new_block)
        idx = m.end()
    out.append(html[idx:])
    return "".join(out)


def add_css(html: str) -> str:
    if "affiliate-note{" in html or ".affiliate-block{" not in html:
        return html
    return html.replace(
        ".affiliate-btn+.affiliate-btn{margin-left:.75rem}",
        ".affiliate-btn+.affiliate-btn{margin-left:.75rem}" + NOTE_CSS,
        1,
    )


def main() -> None:
    dry = "--dry-run" in sys.argv
    targets = sorted(ROOT.glob("articles/*.html")) + sorted(ROOT.glob("*.html"))
    total_links = 0
    for path in targets:
        if path.name == "artikel.html":  # template, gaat via agent.py
            continue
        original = path.read_text(encoding="utf-8")
        if "awin1.com" not in original:
            continue
        html, n = rewrite_links(original, slug_for(path))
        html = upgrade_rel(html)
        html = add_notes(html)
        html = add_css(html)
        if html != original:
            total_links += n
            print(f"  {path.relative_to(ROOT)}: {n} link(s)")
            if not dry:
                path.write_text(html, encoding="utf-8")
    print(f"\n{'[dry-run] ' if dry else ''}{total_links} affiliate-links bijgewerkt.")


if __name__ == "__main__":
    main()
