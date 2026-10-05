"""Catalog ficha metering: allowance, re-apply free, persist, zero blocks writes."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from app.services import catalog_metering
from app.services.catalog_apply import apply_pack
from app.services.catalog_pack import build_pack
from app.services.catalog_product import PRODUCT_URL, catalog_product_url
from app.services.catalog_session import publish_fixture, start_session, tick_session


class _MemoryShop:
    platform = "odoo"
    fields = {
        "website_meta_title",
        "website_meta_description",
        "website_meta_keywords",
        "website_description",
    }

    def __init__(self, n=5):
        self.rows = [
            {
                "id": i,
                "name": f"P{i}",
                "description": (
                    "Servicio que prepara la ficha del comercio para que los buscadores "
                    "lean el nombre y la descripción de esta oferta concreta."
                ),
                "url": f"https://shop.example/shop/p{i}",
                "price": 10.0,
                "currency": "USD",
                "is_published": True,
            }
            for i in range(1, n + 1)
        ]
        self.writes = []

    def count(self):
        return len(self.rows)

    def fetch(self, offset, limit):
        return [dict(row) for row in self.rows[offset : offset + limit]]

    def read_block(self, offset, limit):
        return self.fetch(offset, limit), self.count()

    def read_product(self, product_id):
        for row in self.rows:
            if row["id"] == product_id:
                return dict(row)
        raise KeyError(product_id)

    def write_product(self, product_id, values):
        self.writes.append((product_id, dict(values)))
        for row in self.rows:
            if row["id"] == product_id:
                row.update(values)


def _catalog_line(qty, host=None, tmpl=110):
    row = {
        "name": "Product Catalog AEO and SEO pack With IA",
        "product_id": [999, "Product Catalog AEO and SEO pack With IA"],
        "product_uom_qty": qty,
        "product_template_id": [tmpl, "Product Catalog AEO and SEO pack With IA"],
    }
    if host:
        row["aeo_site_url"] = host
    return row


class AllowanceTest(unittest.TestCase):
    def test_s00247_style_order_without_catalog_line_is_zero(self):
        rows = [
            {
                "name": "AEO / SEO y Optimizador de Búsqueda",
                "product_id": [109, "AEO / SEO y Optimizador de Búsqueda"],
                "product_uom_qty": 1.0,
                "product_template_id": [109, "AEO / SEO"],
            }
        ]
        self.assertEqual(catalog_metering.allowance_from_rows(rows, "https://shop.example"), 0)

    def test_sums_catalog_qty_and_prefers_same_hostname(self):
        rows = [
            _catalog_line(3, host="https://a.example"),
            _catalog_line(7, host="https://b.example"),
            {
                "name": "Other",
                "product_id": [1, "Other"],
                "product_uom_qty": 99,
            },
        ]
        self.assertEqual(catalog_metering.allowance_from_rows(rows, "https://b.example"), 7)
        self.assertEqual(catalog_metering.allowance_from_rows(rows, None), 10)

    def test_unbound_catalog_line_does_not_credit_session_host(self):
        """S00734-style: catalog SO without aeo_site_url must not credit S00247 host."""
        rows = [
            _catalog_line(12, host=None),
            _catalog_line(5, host="https://other.example"),
        ]
        self.assertEqual(
            catalog_metering.allowance_from_rows(rows, "https://shop.example"),
            0,
        )

    def test_sums_matching_host_across_separate_partner_orders(self):
        """Catalog qty on a separate Arki SO still credits when aeo_site_url matches."""
        rows = [
            _catalog_line(4, host="https://shop.example"),
            _catalog_line(6, host="https://shop.example"),
            _catalog_line(9, host="https://other.example"),
        ]
        self.assertEqual(
            catalog_metering.allowance_from_rows(rows, "https://shop.example"),
            10,
        )

    def test_detects_template_id_110(self):
        rows = [
            {
                "name": "Catalog pack",
                "product_id": [500, "Catalog pack"],
                "product_uom_qty": 4,
                "product_template_id": [110, "Catalog"],
            }
        ]
        self.assertEqual(catalog_metering.allowance_from_rows(rows), 4)


class _StoreCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "catalog_metering.json")
        self._prev = os.environ.get("CATALOG_METERING_STORE")
        os.environ["CATALOG_METERING_STORE"] = self.path
        try:
            from app.config import settings

            self._settings = settings
            self._prev_setting = getattr(settings, "CATALOG_METERING_STORE", None)
            settings.CATALOG_METERING_STORE = self.path
        except Exception:
            self._settings = None
            self._prev_setting = None

    def tearDown(self):
        if self._settings is not None:
            self._settings.CATALOG_METERING_STORE = self._prev_setting
        if self._prev is None:
            os.environ.pop("CATALOG_METERING_STORE", None)
        else:
            os.environ["CATALOG_METERING_STORE"] = self._prev
        self.tmp.cleanup()


class PersistTest(_StoreCase):
    def test_save_load_round_trip(self):
        self.assertTrue(catalog_metering.record_applied("lic-1", "https://shop.example", 15))
        self.assertTrue(catalog_metering.is_processed("lic-1", "https://shop.example", 15))
        self.assertFalse(catalog_metering.record_applied("lic-1", "https://shop.example", 15))
        self.assertEqual(catalog_metering.used_count("lic-1", "https://shop.example"), 1)
        self.assertTrue(Path(self.path).is_file())
        reloaded = catalog_metering.processed_ids("lic-1", "shop.example")
        self.assertEqual(reloaded, {"15"})

    def test_snapshot_fields(self):
        catalog_metering.record_applied("lic-s", "https://shop.example", 1)
        snap = catalog_metering.metering_snapshot("lic-s", "https://shop.example", 5)
        self.assertEqual(snap["allowance"], 5)
        self.assertEqual(snap["used"], 1)
        self.assertEqual(snap["remaining"], 4)
        self.assertEqual(snap["processed_ids"], 1)
        self.assertIn("hostname=shop.example", snap["acquire_url"])
        self.assertTrue(snap["acquire_url"].startswith(PRODUCT_URL))


class ApplyCreditsTest(_StoreCase):
    def test_allowance_n_blocks_extra_new_ids(self):
        shop = _MemoryShop(5)
        start_session("lic-m", shop, owned=True, locale="es", batch_ids=[1, 2, 3, 4, 5])
        for _ in range(5):
            tick_session("lic-m")
        result = publish_fixture(
            "lic-m",
            host="https://shop.example",
            allowance=2,
        )
        ok_ids = [row.get("product_id") for row in result["written"] if row.get("ok")]
        blocked = [row for row in result["written"] if row.get("reason") == "no_credits"]
        self.assertEqual(len(ok_ids), 2)
        self.assertEqual(len(blocked), 3)
        self.assertEqual(result.get("reason"), "no_credits")
        self.assertEqual(catalog_metering.used_count("lic-m", "https://shop.example"), 2)

    def test_reprocess_processed_id_costs_zero(self):
        shop = _MemoryShop(1)
        product = shop.read_product(1)
        pack = build_pack(product, locale="es")
        first = apply_pack(
            shop,
            1,
            pack,
            owned=True,
            license_key="lic-r",
            host="https://shop.example",
            allowance=1,
        )
        self.assertTrue(first["ok"])
        self.assertEqual(catalog_metering.used_count("lic-r", "https://shop.example"), 1)
        second = apply_pack(
            shop,
            1,
            pack,
            owned=True,
            license_key="lic-r",
            host="https://shop.example",
            allowance=1,
        )
        self.assertTrue(second["ok"])
        self.assertEqual(catalog_metering.used_count("lic-r", "https://shop.example"), 1)
        self.assertEqual(catalog_metering.remaining("lic-r", "https://shop.example", 1), 0)

    def test_zero_allowance_blocks_new_writes_analysis_untouched(self):
        shop = _MemoryShop(2)
        start_session("lic-z", shop, owned=True, locale="es", batch_ids=[1, 2])
        tick_session("lic-z")
        tick_session("lic-z")
        self.assertEqual(catalog_metering.used_count("lic-z", "https://shop.example"), 0)
        result = publish_fixture(
            "lic-z",
            host="https://shop.example",
            allowance=0,
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result.get("reason"), "no_credits")
        self.assertEqual(shop.writes, [])
        self.assertEqual(catalog_metering.used_count("lic-z", "https://shop.example"), 0)


class AcquireUrlTest(unittest.TestCase):
    def test_acquire_url_stays_when_owned(self):
        self.assertEqual(catalog_product_url(True), PRODUCT_URL)
        self.assertEqual(catalog_product_url(False), PRODUCT_URL)

    def test_acquire_url_includes_session_hostname_and_qty(self):
        url = catalog_product_url(
            False,
            host="https://www.shop.example",
            quantity=8,
        )
        self.assertIn("aeo_site_url=", url)
        self.assertIn("hostname=shop.example", url)
        self.assertIn("qty=8", url)
        self.assertTrue(url.startswith(PRODUCT_URL))

    def test_snapshot_acquire_url_binds_host(self):
        snap = catalog_metering.metering_snapshot(
            "lic-acq",
            "https://shop.example",
            0,
            needed_qty=3,
        )
        self.assertIn("hostname=shop.example", snap["acquire_url"])
        self.assertIn("qty=3", snap["acquire_url"])


if __name__ == "__main__":
    unittest.main()
