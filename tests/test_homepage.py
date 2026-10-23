import json
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class ArticleTeasers(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_teaser = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.in_teaser = "stream-excerpt" in dict(attrs).get("class", "").split()

    def handle_endtag(self, tag):
        if tag == "p":
            self.in_teaser = False

    def handle_data(self, data):
        if self.in_teaser:
            self.parts.append(data)


class HomepageTest(unittest.TestCase):
    def test_subsidy_title_matches_article_index(self):
        articles = json.loads((ROOT / "articles.json").read_text(encoding="utf-8"))
        article = next(a for a in articles if a["slug"] == "subsidie-thuisbatterij-2027-overzicht")
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn(article["title"], homepage)
        self.assertIn(article["summary"], homepage)

    def test_teasers_do_not_promise_zero_vat_or_municipal_amounts(self):
        parser = ArticleTeasers()
        parser.feed((ROOT / "index.html").read_text(encoding="utf-8"))
        teasers = " ".join(parser.parts)
        self.assertNotIn("0%", teasers)
        self.assertNotIn("1.500", teasers)


if __name__ == "__main__":
    unittest.main()
