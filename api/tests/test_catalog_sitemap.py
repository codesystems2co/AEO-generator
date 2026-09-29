"""Published AEO data stays in the sitemap after two native regenerations."""
import unittest

from app.services.catalog_sitemap import include_published_product
from app.services.sitemap_persist import IndexRecord, SitemapShop, SitemapUrlError


def _shop(published=True):
    return SitemapShop(
        platform="odoo",
        origin="https://arkiphere.cloud",
        records=(
            IndexRecord(path="/shop/aeo-data-15", kind="product", indexable=False),
            IndexRecord(path="/", kind="page", indexable=True),
        ),
        file_xml=(
            "<?xml version='1.0'?><urlset>"
            "<url><loc>https://arkiphere.cloud/</loc></url>"
            "</urlset>"
        ),
    )


class CatalogSitemapTest(unittest.TestCase):
    def test_published_product_survives_two_native_runs(self):
        result = include_published_product(
            _shop(True),
            {"url": "https://arkiphere.cloud/shop/aeo-data-15", "is_published": True},
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["ran_native_task"], 2)
        self.assertTrue(result["survived_second_refresh"])
        self.assertEqual(result["native_task"], "website.sitemap")
        self.assertIn("https://arkiphere.cloud/shop/aeo-data-15", result["file_xml"])

    def test_unpublished_product_is_not_added(self):
        result = include_published_product(
            _shop(False),
            {"url": "https://arkiphere.cloud/shop/aeo-data-15", "is_published": False},
        )
        self.assertFalse(result["ok"])
        self.assertNotIn("https://arkiphere.cloud/shop/aeo-data-15", result.get("file_xml") or "")

    def test_foreign_product_url_is_rejected(self):
        with self.assertRaises(SitemapUrlError):
            include_published_product(
                _shop(True),
                {"url": "https://arkiphere.cloud/shop/invented", "is_published": True},
            )


if __name__ == "__main__":
    unittest.main()
