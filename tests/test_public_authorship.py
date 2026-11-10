import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class PublicAuthorshipTest(unittest.TestCase):
    def test_public_authors_use_site_identity(self):
        def check(value):
            if isinstance(value, dict):
                if isinstance(value.get("author"), dict):
                    self.assertEqual(value["author"]["@type"], "Organization")
                    self.assertEqual(value["author"]["name"], "SalderingsUpdate.nl")
                for child in value.values():
                    check(child)
            elif isinstance(value, list):
                for child in value:
                    check(child)

        for page in [*ROOT.glob("*.html"), *(ROOT / "articles").glob("*.html")]:
            if page.name == "artikel.html":
                continue
            with self.subTest(page=page.name):
                for data in re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                                       page.read_text(encoding="utf-8"), re.S):
                    check(json.loads(data))
        about = (ROOT / "over-ons.html").read_text(encoding="utf-8")
        self.assertNotIn('"founder"', about)
        self.assertNotIn('<div class="person">', about)
