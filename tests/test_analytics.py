import tempfile
import unittest
from pathlib import Path

from tools import build, lib, pagegen
from tools.sync_affiliate_tracking import SCRIPTS, add_scripts, config, render_config


class AnalyticsTest(unittest.TestCase):
    def test_script_insertion_is_idempotent_and_templates_keep_it(self):
        html = "<head><title>Test</title></head>"
        once = add_scripts(html)
        self.assertEqual(add_scripts(once), once)
        self.assertIn(SCRIPTS, pagegen.GTAG)
        for path in [*lib.SITE_DIR.glob("*.html"), *lib.ARTICLES_DIR.glob("*.html")]:
            with self.subTest(path=path.name):
                self.assertEqual(path.read_text(encoding="utf-8").count(SCRIPTS), 1)

    def test_generated_config_matches_registry(self):
        self.assertEqual((lib.SITE_DIR / "assets/affiliate-config.js").read_text(encoding="utf-8"), render_config())
        frank = next(p for p in config() if p["campaign"] == "16978")
        self.assertEqual(frank["publisher"], "419918")
        self.assertEqual(frank["host"], "jf79.net")

    def test_measurement_alone_does_not_refresh_editorial_date(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.html"
            html = "<head><title>Test</title></head><h1>Nieuws</h1>"
            path.write_text(html, encoding="utf-8")
            old_hash = build.content_hash(path)
            path.write_text(add_scripts(html), encoding="utf-8")
            self.assertEqual(build.content_hash(path), old_hash)


if __name__ == "__main__":
    unittest.main()
