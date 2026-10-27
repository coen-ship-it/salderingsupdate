import unittest
from urllib.parse import parse_qs, urlsplit

import affiliates
from tools.upgrade_affiliate_links import rewrite_links


class AffiliateLinksTest(unittest.TestCase):
    def test_daisycon_keeps_media_campaign_destination_and_subid(self):
        for key in ("homewizard", "zendure", "zendure_balkon", "frank_energie"):
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


if __name__ == "__main__":
    unittest.main()
