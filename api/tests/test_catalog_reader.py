"""Catalog is read in closed blocks of 20. A foreign URL is refused."""
import unittest

from app.services.catalog_reader import (
    BLOCK_SIZE,
    BlockOpenError,
    BlockSession,
    ForeignUrlError,
    odoo_count_call,
    odoo_fetch_call,
    prestashop_fetch_params,
    woocommerce_fetch_params,
)


class _Transport:
    def __init__(self, rows, fail_at=None):
        self.rows = list(rows)
        self.fail_at = fail_at
        self.counts = 0
        self.fetches = []

    def count(self):
        self.counts += 1
        return len(self.rows)

    def fetch(self, offset, limit):
        self.fetches.append((offset, limit))
        if self.fail_at is not None and offset == self.fail_at:
            self.fail_at = None
            raise RuntimeError("transient")
        return self.rows[offset:offset + limit]


def _rows(n):
    return [
        {
            "id": i,
            "name": f"P{i}",
            "description": f"Desc {i}",
            "url": f"https://shop.example/shop/p{i}",
            "price": 10.0 + i,
            "currency": "USD",
        }
        for i in range(1, n + 1)
    ]


class BlockSessionTest(unittest.TestCase):
    def test_count_does_not_fetch_bodies(self):
        transport = _Transport(_rows(25))
        session = BlockSession(transport)
        self.assertEqual(session.start(), 25)
        self.assertEqual(transport.counts, 1)
        self.assertEqual(transport.fetches, [])

    def test_block_size_is_twenty_and_next_offset_waits(self):
        transport = _Transport(_rows(45))
        session = BlockSession(transport)
        session.start()
        first, offset = session.open_block()
        self.assertEqual(offset, 0)
        self.assertEqual(len(first), BLOCK_SIZE)
        self.assertEqual(BLOCK_SIZE, 20)
        with self.assertRaises(BlockOpenError):
            session.open_block()
        self.assertEqual(transport.fetches, [(0, 20)])
        session.close_block()
        second, offset = session.open_block()
        self.assertEqual(offset, 20)
        self.assertEqual([row["id"] for row in second], list(range(21, 41)))

    def test_failed_offset_is_retried_not_restarted(self):
        transport = _Transport(_rows(25), fail_at=20)
        session = BlockSession(transport)
        session.start()
        session.open_block()
        session.close_block()
        with self.assertRaises(RuntimeError):
            session.open_block()
        self.assertEqual(session.offset, 20)
        retry, offset = session.open_block()
        self.assertEqual(offset, 20)
        self.assertEqual(retry[0]["id"], 21)
        self.assertEqual(transport.fetches, [(0, 20), (20, 20), (20, 20)])

    def test_foreign_url_is_rejected(self):
        transport = _Transport(_rows(3))
        session = BlockSession(transport)
        session.start()
        session.open_block()
        session.reject_unknown("https://shop.example/shop/p2")
        with self.assertRaises(ForeignUrlError):
            session.reject_unknown("https://shop.example/blog/invented")


class ShopAdapterTest(unittest.TestCase):
    def test_odoo_shop_counts_before_bodies_and_uses_offset(self):
        from app.services.catalog_shop import OdooCatalogShop

        calls = []

        def execute(model, method, *args, **kwargs):
            calls.append((model, method, args, kwargs))
            if method == "search_count":
                return 40
            return [{"id": 21, "name": "AEO data", "website_url": "/shop/aeo-data-21", "is_published": True}]

        shop = OdooCatalogShop(execute, "https://arkiphere.cloud")
        self.assertEqual(shop.count(), 40)
        rows = shop.fetch(20, 20)
        self.assertEqual(rows[0]["name"], "AEO data")
        self.assertEqual(calls[0][1], "search_count")
        self.assertEqual(calls[1][1], "search_read")
        self.assertEqual(calls[1][3]["offset"], 20)
        self.assertEqual(calls[1][3]["limit"], 20)

    def test_woo_and_presta_use_platform_paging(self):
        from app.services.catalog_shop import PrestashopCatalogShop, WooCatalogShop

        seen = []

        def http(method, path, params=None):
            seen.append((method, path, params))
            if "wc" in path:
                return {"products": [{"id": 3, "name": "AEO data", "permalink": "https://shop.example/p/3", "status": "publish"}], "total": 21}
            return {"products": [{"id": 3, "name": "AEO data", "link_rewrite": "aeo-data", "active": "1"}], "total": 21}

        woo = WooCatalogShop(http, "https://shop.example")
        self.assertEqual(woo.count(), 21)
        self.assertEqual(woo.fetch(20, 20)[0]["id"], 3)
        self.assertEqual(seen[-1][2]["page"], 2)
        presta = PrestashopCatalogShop(http, "https://shop.example")
        self.assertEqual(presta.fetch(20, 20)[0]["name"], "AEO data")
        self.assertEqual(seen[-1][2]["limit"], "20,20")


class PlatformCallTest(unittest.TestCase):
    def test_odoo_uses_search_count_and_offset_limit(self):
        count = odoo_count_call()
        fetch = odoo_fetch_call(20, 20)
        self.assertEqual(count["model"], "product.template")
        self.assertEqual(count["method"], "search_count")
        self.assertEqual(fetch["method"], "search_read")
        self.assertEqual(fetch["offset"], 20)
        self.assertEqual(fetch["limit"], 20)
        self.assertIn("website_meta_title", fetch["fields"])
        self.assertIn("is_published", fetch["fields"])

    def test_prestashop_limit_is_offset_size(self):
        self.assertEqual(prestashop_fetch_params(20, 20)["limit"], "20,20")

    def test_woocommerce_uses_page_and_per_page(self):
        params = woocommerce_fetch_params(20, 20)
        self.assertEqual(params["per_page"], 20)
        self.assertEqual(params["page"], 2)


if __name__ == "__main__":
    unittest.main()
