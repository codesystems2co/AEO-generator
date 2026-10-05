"""Scan session: six in the dialog, one analyzing, next block waits."""
import unittest

from app.services.catalog_session import get_session, publish_fixture, report_ready, start_session, tick_session
from app.services.sitemap_persist import IndexRecord, SitemapShop


class _MemoryShop:
    platform = "odoo"
    fields = {
        "website_meta_title",
        "website_meta_description",
        "website_meta_keywords",
        "website_description",
    }

    def __init__(self, n=25):
        self.rows = [
            {
                "id": i,
                "name": "AEO data" if i == 1 else f"P{i}",
                "description": "Servicio que prepara la ficha del comercio para que los buscadores lean el nombre y la descripción de esta oferta concreta.",
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
        return [dict(row) for row in self.rows[offset:offset + limit]]

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


class SessionTest(unittest.TestCase):
    def test_tick_keeps_six_visible_and_one_analyzing(self):
        shop = _MemoryShop(25)
        start = start_session("lic-a", shop, owned=True, locale="es")
        self.assertEqual(len(start["queue"]["window"]), 6)
        self.assertEqual(start["queue"]["analyzing"], 1)
        first = tick_session("lic-a")
        ids = [row["id"] for row in first["queue"]["window"]]
        self.assertEqual(len(ids), 6)
        self.assertNotIn(1, ids)
        self.assertEqual(first["queue"]["analyzing"], 1)
        self.assertEqual(first["analyzed_count"], 1)

    def test_next_block_waits_until_the_first_closes(self):
        shop = _MemoryShop(25)
        start_session("lic-b", shop, owned=True, locale="es")
        for _ in range(20):
            state = tick_session("lic-b")
        self.assertGreaterEqual(state["analyzed_count"], 20)
        self.assertTrue(any(row["id"] == 21 for row in state["queue"]["window"]))
        self.assertIn("bloque 2", state["queue"]["caption"])

    def test_publish_writes_all_analyzed_when_owned(self):
        shop = _MemoryShop(3)
        start_session("lic-c", shop, owned=True, locale="es")
        tick_session("lic-c")
        tick_session("lic-c")
        sitemap = SitemapShop(
            platform="odoo",
            origin="https://shop.example",
            records=(
                IndexRecord(path="/shop/p1", kind="product", indexable=False),
                IndexRecord(path="/shop/p2", kind="product", indexable=False),
            ),
            file_xml="<?xml version='1.0'?><urlset></urlset>",
        )
        result = publish_fixture("lic-c", sitemap)
        self.assertTrue(result["ok"])
        # Full-catalog mode (no batch_ids): every analyzed id is written.
        self.assertEqual([item[0] for item in shop.writes], [1, 2])
        self.assertTrue(result["sitemap"]["ok"])

    def test_batch_publish_writes_only_the_new_sheets(self):
        shop = _MemoryShop(3)
        start_session("lic-e", shop, owned=True, locale="es", batch_ids=[2, 3])
        tick_session("lic-e")
        tick_session("lic-e")
        tick_session("lic-e")
        result = publish_fixture("lic-e")
        self.assertTrue(result["ok"])
        self.assertEqual([item[0] for item in shop.writes], [2, 3])
        self.assertTrue(report_ready("lic-e"))

    def test_publish_without_order_line_does_not_write(self):
        shop = _MemoryShop(2)
        start_session("lic-d", shop, owned=False, locale="es")
        tick_session("lic-d")
        result = publish_fixture("lic-d")
        self.assertFalse(result["ok"])
        self.assertEqual(shop.writes, [])
        self.assertFalse(report_ready("lic-d"))
        self.assertFalse((get_session("lic-d") or {}).get("delivered"))


if __name__ == "__main__":
    unittest.main()
