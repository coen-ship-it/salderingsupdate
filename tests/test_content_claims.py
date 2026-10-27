import json
import unittest
from decimal import Decimal
from html import unescape
from html.parser import HTMLParser

from tools import lib


def normalize(text):
    return " ".join(text.split())


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.ignored = None
        self.ld = False
        self.json_text = []
        self.schemas = []
        self.text = []
        self.faq_section = False
        self.capture = None
        self.parts = []
        self.question = None
        self.faq = {}
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.ignored = tag
            self.ld = tag == "script" and dict(attrs).get("type") == "application/ld+json"
            self.json_text = []
        if tag == "h2" or self.faq_section and tag in ("h3", "p"):
            self.capture = tag
            self.parts = []

    def handle_endtag(self, tag):
        if tag == self.ignored:
            if self.ld:
                self.schemas.append(json.loads("".join(self.json_text)))
            self.ignored = None
            self.ld = False
        if tag != self.capture:
            return
        text = normalize("".join(self.parts))
        if tag == "h2":
            self.faq_section = text.startswith("Veelgestelde vragen")
        elif tag == "h3":
            self.question = text
        elif tag == "p" and self.question:
            self.faq[self.question] = text
        self.capture = None

    def handle_data(self, data):
        if self.ignored:
            if self.ld:
                self.json_text.append(data)
            return
        self.text.append(data)
        if self.capture:
            self.parts.append(data)


def nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from nodes(child)


class Table(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.active = False
        self.cell = None
        self.row = []
        self.rows = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.active = "vergelijk-tabel" in dict(attrs).get("class", "").split()
        if not self.active:
            return
        if tag == "tr":
            self.row = []
        elif tag == "td":
            self.cell = []

    def handle_endtag(self, tag):
        if tag == "td" and self.cell is not None:
            self.row.append(normalize("".join(self.cell)))
            self.cell = None
        elif tag == "tr" and self.active and self.row:
            self.rows.append(self.row)
        elif tag == "table":
            self.active = False

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)


class ContentClaimsTest(unittest.TestCase):
    def test_subsidy_faq_schema_matches_visible_questions_and_answers(self):
        html = (lib.ARTICLES_DIR / "2026-04-28-subsidie-thuisbatterij-2027-overzicht.html").read_text(encoding="utf-8")
        page = Page(html)
        faq = next(item for item in nodes(page.schemas) if item.get("@type") == "FAQPage")
        answers = {item["name"]: normalize(item["acceptedAnswer"]["text"]) for item in faq["mainEntity"]}
        self.assertEqual(len(answers), 3)
        self.assertEqual(answers, page.faq)
        self.assertIn("<title>Subsidie thuisbatterij 2027: regelingen en btw-teruggaaf</title>", html)

    def test_main_faq_financial_answers_are_visible(self):
        page = Page((lib.SITE_DIR / "faq.html").read_text(encoding="utf-8"))
        text = normalize("".join(page.text))
        questions = {"Krijg ik subsidie voor een thuisbatterij?", "Is een thuisbatterij een goede investering?", "Krijg ik nog wel iets voor mijn teruggeleverde stroom?"}
        selected = [item for item in nodes(page.schemas) if item.get("@type") == "Question" and item.get("name") in questions]
        self.assertEqual(len(selected), 3)
        for item in selected:
            self.assertIn(normalize(item["acceptedAnswer"]["text"]), text)

    def test_old_unverified_municipal_ranges_and_vat_promises_do_not_return(self):
        for path in [*lib.SITE_DIR.glob("*.html"), *lib.ARTICLES_DIR.glob("*.html")]:
            with self.subTest(path=path.name):
                html = unescape(path.read_text(encoding="utf-8")).lower()
                self.assertNotRegex(html, r"€\s*200\s*(?:–|tot|-)\s*€?\s*1[.,]500")
                for claim in ("mogelijk 0% btw als de batterij", "wél 0% btw bij combinatie", "soms 0%-btw bij gecombineerde"):
                    self.assertNotIn(claim, html)

    def test_solar_example_values_follow_displayed_assumptions(self):
        html = (lib.ARTICLES_DIR / "2026-05-13-zonnepanelen-rendabel-na-2027.html").read_text(encoding="utf-8")
        rows = Table(html).rows
        self.assertEqual(len(rows), 3)
        def number(value):
            return Decimal(value.replace("kWh", "").replace("€", "").replace(".", "").replace(",", ".").strip())
        for row in rows:
            production, own, returned, annual = map(number, row[1:])
            self.assertEqual(own, production * Decimal("0.45"))
            self.assertEqual(own + returned, production)
            self.assertEqual(annual, own * Decimal("0.30") + returned * Decimal("0.09"))
        self.assertIn("circa 9,3 jaar", html)
        self.assertEqual((Decimal("6000") / number(rows[1][4])).quantize(Decimal("0.1")), Decimal("9.3"))


if __name__ == "__main__":
    unittest.main()
