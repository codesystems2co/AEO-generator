"""PrestaShop gsitemap cron rebuilds XML from active products, categories and CMS."""
import unittest

from app.services.sitemap_persist import (
    IndexRecord,
    SitemapShop,
    SitemapUrlError,
    force_native_task,
    persist_sitemap,
)


def _shop() -> SitemapShop:
    return SitemapShop(
        platform="prestashop",
        origin="https://shop.example",
        records=(
            IndexRecord(path="/12-odoo-hosting", kind="product", indexable=False),
            IndexRecord(path="/content/terms", kind="cms", indexable=True),
            IndexRecord(path="/3-hosting", kind="category", indexable=True),
        ),
        file_xml=(
            "<?xml version='1.0'?><urlset>"
            "<url><loc>https://shop.example/12-odoo-hosting</loc></url>"
            "</urlset>"
        ),
    )


class PrestashopSitemapPersistTest(unittest.TestCase):
    def test_gsitemap_cron_drops_inactive_product_written_only_in_xml(self):
        refreshed = force_native_task(_shop())
        self.assertNotIn("/12-odoo-hosting", refreshed.file_xml)
        self.assertIn("/content/terms", refreshed.file_xml)
        self.assertIn("/3-hosting", refreshed.file_xml)

    def test_activating_the_product_survives_two_cron_runs(self):
        result = persist_sitemap(_shop(), ["/12-odoo-hosting"])
        self.assertTrue(result["ok"])
        self.assertEqual(result["native_task"], "gsitemap-cron")
        self.assertEqual(result["ran_native_task"], 2)
        self.assertIn("https://shop.example/12-odoo-hosting", result["file_xml"])
        self.assertIn("https://shop.example/content/terms", result["file_xml"])

    def test_unknown_url_is_rejected(self):
        with self.assertRaises(SitemapUrlError):
            persist_sitemap(_shop(), ["/99-not-in-catalog"])


if __name__ == "__main__":
    unittest.main()
