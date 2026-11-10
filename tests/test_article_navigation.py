import ast
import unittest
from html import escape
from html.parser import HTMLParser
from pathlib import Path

from tools import lib


class ArticleCards(HTMLParser):
    """Read real links from cards without executing their JavaScript."""

    def __init__(self):
        super().__init__()
        self.cards = []
        self.current = None
        self.in_heading = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.current is None and "stream-article" in attrs.get("class", "").split():
            self.current = {"root": tag, "links": [], "title": [], "nested_anchor": False}
        elif self.current is not None and tag == "a" and self.current["root"] == "a":
            self.current["nested_anchor"] = True
        if self.current is not None:
            if tag == "a" and attrs.get("href"):
                self.current["links"].append(attrs["href"])
            if tag == "h3":
                self.in_heading = True

    def handle_endtag(self, tag):
        if tag == "h3":
            self.in_heading = False
        if self.current is not None and tag == self.current["root"]:
            self.cards.append(self.current)
            self.current = None

    def handle_data(self, data):
        if self.current is not None and self.in_heading:
            self.current["title"].append(data)


def homepage_renderer():
    # Load only this pure renderer: importing the article agent would load
    # credentials and require unrelated external service SDKs during CI.
    source = ast.parse((lib.SITE_DIR / "agent.py").read_text(encoding="utf-8"))
    selected = [node for node in source.body if
                (isinstance(node, ast.FunctionDef) and node.name == "build_article_list_html") or
                (isinstance(node, ast.Assign) and any(
                    isinstance(target, ast.Name) and target.id == "CATEGORY_CSS"
                    for target in node.targets))]
    namespace = {"escape": escape}
    exec(compile(ast.Module(body=selected, type_ignores=[]), "agent.py", "exec"), namespace)
    return namespace["build_article_list_html"]


class ArticleNavigationTest(unittest.TestCase):
    def test_documented_updates_keep_publication_and_display_matching_dates(self):
        updated = [a for a in lib.load_articles() if a.get("update_note")]
        self.assertTrue(updated)
        for article in updated:
            with self.subTest(article=article["slug"]):
                html = (lib.SITE_DIR / article["file"]).read_text(encoding="utf-8")
                schema = lib.first_ld_json(html)
                self.assertEqual(schema["datePublished"], article["date"])
                self.assertEqual(schema["dateModified"], article["updated"])
                self.assertIn(f'datetime="{article["date"]}"', html)
                self.assertIn(f'datetime="{article["updated"]}"', html)
                card_date = lib.article_date_html(article)
                self.assertIn(f'datetime="{article["updated"]}"', card_date)
                self.assertIn(card_date, (lib.SITE_DIR / "nieuws.html").read_text(encoding="utf-8"))

    def test_metadata_date_alone_does_not_claim_editorial_update(self):
        self.assertEqual(lib.article_date_html({"date": "2026-01-01",
                         "date_display": "1 januari 2026", "updated": "2026-11-10"}),
                         "1 januari 2026")

    def test_every_published_card_has_a_real_canonical_link(self):
        destinations = {article["url"] for article in lib.load_articles()}
        total = 0
        for page in lib.SITE_DIR.glob("*.html"):
            parser = ArticleCards()
            parser.feed(page.read_text(encoding="utf-8"))
            for card in parser.cards:
                total += 1
                with self.subTest(page=page.name, title="".join(card["title"])):
                    self.assertTrue(card["links"], "A JavaScript click handler is not a link")
                    self.assertTrue("".join(card["title"]).strip())
                    self.assertFalse(card["nested_anchor"])
                    for href in card["links"]:
                        self.assertIn(href, destinations)
        self.assertGreater(total, 0)

    def test_generator_preserves_links_without_javascript_or_html_redirects(self):
        render = homepage_renderer()
        articles = [
            {"url": "/articles/canonical", "file": "articles/unused.html",
             "title": "A & B <vergelijking>", "summary": "<script>Gewone tekst</script>"},
            {"file": "articles/older.html", "title": "Ouder artikel", "summary": "Uitleg"},
        ]
        html = render(articles)
        parser = ArticleCards()
        parser.feed(html)
        self.assertEqual(len(parser.cards), 2)
        self.assertEqual([card["links"] for card in parser.cards],
                         [["/articles/canonical"], ["/articles/older"]])
        self.assertEqual("".join(parser.cards[0]["title"]), articles[0]["title"])
        self.assertNotIn("onclick=", html)
        self.assertNotIn("<script>", html)
        self.assertTrue(all(card["root"] == "a" for card in parser.cards))


if __name__ == "__main__":
    unittest.main()
