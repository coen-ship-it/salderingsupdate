import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import build, lib


class SitemapTest(unittest.TestCase):
    def test_unchanged_page_preserves_date_and_retires_old_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page = root / "index.html"
            page.write_text('<h1>Nieuws</h1>', encoding="utf-8")
            state = {"/": {"hash": build.content_hash(page), "lastmod": "2026-08-01"},
                     "/old": {"hash": "retired", "lastmod": "2026-08-01"}}
            with patch.object(lib, "SITE_DIR", root), patch.object(lib, "STATIC_PAGES", {"/": ("1", "daily")}), patch.object(lib, "load_articles", return_value=[]), patch.object(build, "load_state", return_value=state):
                sitemap, new_state = build.build_sitemap("2026-10-12")
                self.assertIn("<lastmod>2026-08-01</lastmod>", sitemap)
                self.assertNotIn("/old", new_state)
                page.write_text('<h1>Nieuwe uitleg</h1>', encoding="utf-8")
                _, changed = build.build_sitemap("2026-10-12")
                self.assertEqual(changed["/"]["lastmod"], "2026-10-12")

    def test_aliases_redirect_directly_with_and_without_html(self):
        rules = {parts[0]: parts[1:] for line in build.build_redirects().splitlines()
                 if not line.startswith("#") and len(parts := line.split()) >= 3}
        for source, destination in lib.REDIRECT_ALIASES.items():
            self.assertNotIn(destination, lib.REDIRECT_ALIASES)
            self.assertEqual(rules[source], [destination, "301"])
            self.assertEqual(rules[source + ".html"], [destination, "301"])
        self.assertEqual(rules["/contracten.html"], ["/contracten", "301!"])


if __name__ == "__main__":
    unittest.main()
