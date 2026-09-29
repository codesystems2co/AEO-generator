"""Odoo regenerates /sitemap.xml from published pages and products."""
import unittest

from app.services.sitemap_persist import (
    IndexRecord,
    SitemapShop,
    SitemapUrlError,
    force_native_task,
    include_existing,
    persist_sitemap,
)


def _shop() -> SitemapShop:
    return SitemapShop(
        platform="odoo",
        origin="https://arkiphere.cloud",
        records=(
            IndexRecord(path="/shop/odoo-18", kind="product", indexable=False),
            IndexRecord(path="/", kind="page", indexable=True),
        ),
        file_xml=(
            "<?xml version='1.0'?><urlset>"
            "<url><loc>https://arkiphere.cloud/shop/odoo-18</loc></url>"
            "</urlset>"
        ),
    )


class OdooSitemapPersistTest(unittest.TestCase):
    def test_native_task_overwrites_a_file_edit(self):
        refreshed = force_native_task(_shop())
        self.assertNotIn("/shop/odoo-18", refreshed.file_xml)
        self.assertIn("https://arkiphere.cloud/", refreshed.file_xml)

    def test_record_update_survives_two_native_runs(self):
        result = persist_sitemap(_shop(), ["/shop/odoo-18"])
        self.assertTrue(result["ok"])
        self.assertEqual(result["ran_native_task"], 2)
        self.assertTrue(result["survived_second_refresh"])
        self.assertIn("https://arkiphere.cloud/shop/odoo-18", result["file_xml"])
        self.assertIn("https://arkiphere.cloud/", result["file_xml"])
        self.assertTrue(result["records"][0]["indexable"])

    def test_unknown_url_is_rejected(self):
        with self.assertRaises(SitemapUrlError):
            include_existing(_shop(), ["/shop/invented"])


if __name__ == "__main__":
    unittest.main()
