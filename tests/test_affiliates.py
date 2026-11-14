import unittest
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

import affiliates
from tools.upgrade_affiliate_links import rewrite_links


class AffiliateLinksTest(unittest.TestCase):
    def test_black_friday_links_keep_the_promotion_creative_and_tracking(self):
        from tools.sync_battery_offers import render
        from tools.sync_affiliate_tracking import config
        import re
        from html import unescape
        for slug in ("thuisbatterijen", "subsidie-thuisbatterij-2027-overzicht"):
            html = render(slug)
            for href in re.findall(r'href="([^"]+)"', html):
                url = urlsplit(unescape(href))
                if url.netloc != "glp8.net":
                    continue
                params = parse_qs(url.query)
                self.assertEqual(params["li"], ["1990714"])
                self.assertEqual(params["wi"], ["419918"])
                self.assertTrue(params["ws"][0].startswith(slug + "__bf2026-"))
                self.assertEqual(params["dl"], ["pages/black-friday"])
                self.assertTrue(any(p["host"] == url.netloc and p["campaign"] == params["si"][0]
                                    for p in config()), "New creative must still be measured")

    def test_daisycon_keeps_media_campaign_destination_and_subid(self):
        for key in ("homewizard", "zendure", "zendure_balkon", "frank_energie", "nextenergy_batterij"):
            with self.subTest(partner=key):
                partner = affiliates.PARTNERS[key]
                result = urlsplit(affiliates.link(key, "batterij", "keuze"))
                params = parse_qs(result.query, keep_blank_values=True)
                self.assertEqual(result.netloc, urlsplit(partner["base"]).netloc)
                self.assertEqual(params["si"], [partner["si"]])
                self.assertEqual(params["li"], [partner["li"]])
                self.assertEqual(params["wi"], ["419918"])
                self.assertEqual(params["ws"], ["batterij__keuze"])
                self.assertEqual(params["dl"], [urlsplit(partner["url"]).path.lstrip("/")])

    def test_migration_preserves_stream_destination_and_position(self):
        for key in ("ecoflow_stream", "ecoflow_stream_ac"):
            url = affiliates.link(key, "batterij", "vergelijking").replace("&", "&amp;")
            html = f'<a href="{url}">Bekijk</a>'
            rewritten, count = rewrite_links(html, "batterij")
            self.assertEqual(count, 1)
            self.assertEqual(rewritten, html)

    def test_generated_battery_blocks_use_daisycon_without_old_partner(self):
        html = affiliates.block("batterij_kopen", "nieuw-artikel")
        self.assertIn("wi=419918", html)
        self.assertIn("ws=nieuw-artikel__body", html)
        self.assertNotIn("119703", html)
        self.assertIn('rel="sponsored nofollow noopener"', html)

    def test_removed_battery_destination_is_not_promoted_or_generated(self):
        broken = "www.coolblue.nl/thuisbatterijen"
        for partner in affiliates.PARTNERS.values():
            self.assertNotIn(broken, partner["url"])
        root = Path(__file__).resolve().parent.parent
        for path in [*root.glob("*.html"), *root.glob("articles/*.html")]:
            with self.subTest(page=path.name):
                self.assertNotIn(broken, unquote(path.read_text(encoding="utf-8")))

    def test_unknown_coolblue_destination_is_not_changed_to_other_product(self):
        from tools.upgrade_affiliate_links import partner_for_query
        self.assertIsNone(partner_for_query("awinmid=85161&ued=https%3A%2F%2Fwww.coolblue.nl%2Fthuisbatterijen"))
        self.assertEqual(partner_for_query("awinmid=85161&ued=https%3A%2F%2Fwww.coolblue.nl%2Fzonnepanelen"), "coolblue_zonnepanelen")


if __name__ == "__main__":
    unittest.main()
