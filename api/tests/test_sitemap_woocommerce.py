"""WooCommerce sitemap is rebuilt from published products that are not noindex."""
import unittest

from app.services.sitemap_persist import (
    IndexRecord,
    SitemapShop,
    force_native_task,
    persist_sitemap,
)


def _shop() -> SitemapShop:
    return SitemapShop(
        platform="woocommerce",
        origin="https://woo.example",
        records=(
            IndexRecord(path="/product/odoo-enterprise", kind="product", indexable=False),
            IndexRecord(path="/shop", kind="page", indexable=True),
        ),
        file_xml=(
            "<?xml version='1.0'?><urlset>"
            "<url><loc>https://woo.example/product/odoo-enterprise</loc></url>"
            "</urlset>"
        ),
    )


class WooCommerceSitemapPersistTest(unittest.TestCase):
    def test_wp_sitemap_rebuild_drops_a_noindex_product_left_in_the_file(self):
        refreshed = force_native_task(_shop())
        self.assertNotIn("/product/odoo-enterprise", refreshed.file_xml)
        self.assertIn("https://woo.example/shop", refreshed.file_xml)

    def test_publishing_the_product_survives_two_rebuilds(self):
        result = persist_sitemap(_shop(), ["/product/odoo-enterprise"])
        self.assertTrue(result["ok"])
        self.assertEqual(result["native_task"], "wp-sitemap")
        self.assertEqual(result["ran_native_task"], 2)
        self.assertTrue(result["survived_second_refresh"])
        self.assertIn("https://woo.example/product/odoo-enterprise", result["file_xml"])
        self.assertIn("https://woo.example/shop", result["file_xml"])


if __name__ == "__main__":
    unittest.main()
