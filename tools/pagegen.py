#!/usr/bin/env python3
"""Bouwt nieuwe sitepagina's met exact dezelfde vormgeving als de bestaande.

De CSS, het masthead, de navigatie en de footer worden uit regelgeving.html
gelezen, zodat een nieuwe pagina niet visueel gaat afwijken.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools import lib

SOURCE = lib.SITE_DIR / "regelgeving.html"

GTAG = """    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-YVNKE5E8EF"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-YVNKE5E8EF');
    </script>"""

EXTRA_CSS = """
        :root{--border:var(--rule)}

.compare-band{border-top:3px solid var(--sun);border-bottom:1px solid var(--rule);padding:1.5rem 0;margin:1.5rem 0 2rem}
.compare-band h2{font-family:'Playfair Display',serif;font-size:1.3rem;letter-spacing:0;margin-bottom:.5rem}
.compare-band p{font-size:.9rem;margin-bottom:1rem}
.compare-band-links{display:flex;flex-wrap:wrap;gap:.75rem}
.compare-band-links a{display:inline-block;background:var(--sun);color:var(--black);padding:.8rem 1rem;font-size:.85rem;font-weight:600}
.compare-band .compare-band-note{font-size:.75rem;color:var(--mid);margin:.8rem 0 0}
@media(max-width:600px){.compare-band-links{display:grid;grid-template-columns:1fr}.compare-band-links a{text-align:center}}

        .content-grid>*{min-width:0}.nav-inner{overflow-x:auto}.nav-inner a{flex-shrink:0;white-space:nowrap}
        .guide-section{border-bottom:1px solid var(--rule);padding:0 0 1.75rem;margin:0 0 1.75rem}
        .guide-section h2{font-family:'Playfair Display',serif;font-size:1.4rem;margin:1.25rem 0 .8rem;line-height:1.3;letter-spacing:0}
        .guide-section h3{font-size:1.05rem;margin:1.1rem 0 .5rem;letter-spacing:0}
        .guide-section p{margin-bottom:1rem}.guide-section a{color:var(--green);text-decoration:underline}
        .guide-section ul,.guide-section ol{margin:1rem 0 1rem 1.25rem}.guide-section li{margin:.5rem 0}
        .guide-section details{border-top:1px solid var(--rule);padding:.9rem 0}.guide-section summary{cursor:pointer;font-weight:600}
        .guide-section details p{margin:.7rem 0 0}.guide-section .btn-affiliate{color:var(--black);text-decoration:none;text-transform:none;letter-spacing:0}
        .guide-ads{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.75rem;margin:1rem 0}
        .guide-note{font-size:.78rem;color:var(--mid)}
        @media(max-width:600px){.guide-ads{grid-template-columns:1fr}}
        /* ── Gedeelde onderdelen voor nieuwe pagina's ── */
        .crumbs{font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-bottom:1.25rem;display:flex;flex-wrap:wrap;gap:.4rem;align-items:center}
        .crumbs a{color:var(--muted);text-decoration:none;border-bottom:1px solid transparent}
        .crumbs a:hover{color:var(--ink);border-bottom-color:var(--border)}
        .crumbs span[aria-current]{color:var(--ink)}
        .prose{max-width:70ch}
        .prose h2{font-family:'Playfair Display',serif;font-size:1.35rem;font-weight:700;border-bottom:1px solid var(--border);padding-bottom:.4rem;margin:2.25rem 0 .85rem;color:var(--black)}
        .prose h3{font-size:1.02rem;font-weight:700;margin:1.6rem 0 .5rem;color:var(--black)}
        .prose p{margin-bottom:1.05rem}
        .prose ul,.prose ol{margin:.4rem 0 1.15rem 1.4rem}
        .prose li{margin-bottom:.4rem}
        .prose a{color:var(--green);font-weight:600;text-decoration:none}
        .prose a:hover{text-decoration:underline}
        .table-scroll{overflow-x:auto;border:1px solid var(--border);background:var(--white);margin:1.25rem 0}
        table.data{border-collapse:collapse;width:100%;min-width:560px;font-size:.92rem}
        table.data th,table.data td{text-align:left;padding:.6rem .8rem;border-bottom:1px solid var(--border)}
        table.data thead th{background:#f3efe4;font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);white-space:nowrap;border-bottom:2px solid var(--black)}
        table.data tbody tr:last-child td{border-bottom:0}
        table.data td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
        table.data tr.good td{background:#f2f8f3}
        table.data tr.bad  td{background:#fdf4f3}
        .table-note{font-size:.78rem;color:var(--muted);margin:.5rem 0 1.5rem;line-height:1.5}
        .callout{background:#fff9ee;border-left:3px solid var(--sun);padding:.9rem 1.1rem;margin:1.25rem 0;font-size:.95rem}
        .callout strong{color:var(--black)}
        .archive-year{font-family:'Playfair Display',serif;font-size:1.5rem;font-weight:700;margin:2rem 0 .75rem;padding-bottom:.35rem;border-bottom:3px double var(--black)}
        .archive-month{font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:1.5rem 0 .5rem}
        .person{display:flex;gap:1rem;align-items:flex-start;background:var(--white);border:1px solid var(--border);padding:1.1rem 1.25rem;margin:1.25rem 0}
        .person-initials{flex-shrink:0;width:52px;height:52px;border-radius:50%;background:var(--black);color:var(--sun);display:flex;align-items:center;justify-content:center;font-family:'Playfair Display',serif;font-size:1.15rem;font-weight:700}
        .person h3{margin:0 0 .3rem;font-size:1rem}
        .person p{margin:0;font-size:.9rem;color:var(--muted);line-height:1.55}
"""


def _grab(pattern: str, html: str) -> str:
    m = re.search(pattern, html, re.S)
    if not m:
        raise SystemExit(f"Fragment niet gevonden in regelgeving.html: {pattern}")
    return m.group(0)


def chrome() -> dict[str, str]:
    html = SOURCE.read_text(encoding="utf-8")
    style = _grab(r"<style>.*?</style>", html)
    style = style.replace("</style>", EXTRA_CSS + "    </style>")
    return {
        "style": style,
        "breaking": _grab(r'<div class="breaking">.*?</div>\s*</div>', html),
        "masthead": _grab(r'<header class="masthead">.*?</header>', html),
        "nav": _grab(r'<nav class="nav-bar">.*?</nav>', html),
        "footer": _grab(r"<footer>.*?</footer>", html),
        "script": _grab(r"<script>\s*const d = new Date\(\).*?</script>", html),
    }


def page(*, path: str, title: str, description: str, body: str,
         schema: list[str], active: str = "") -> str:
    c = chrome()
    url = f"{lib.BASE_URL}{path}"
    # De nav komt uit regelgeving.html en heeft daar al een actief item staan.
    nav = re.sub(r'\s*class="active"', "", c["nav"])
    if active:
        nav = nav.replace(f'<a href="{active}">', f'<a href="{active}" class="active">')
    schema_blocks = "\n".join(
        f'<script type="application/ld+json">\n{s}\n</script>' for s in schema)
    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{GTAG}
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:site_name" content="SalderingsUpdate.nl">
<meta property="og:image" content="{lib.BASE_URL}/og-image.png">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700&family=Source+Serif+4:ital,wght@0,300;0,400;0,600;1,300;1,400&display=swap" rel="stylesheet">
{c["style"]}
{schema_blocks}
</head>
<body>
{c["breaking"]}
{c["masthead"]}
{nav}
{body}
{c["footer"]}
{c["script"]}
</body>
</html>
"""
