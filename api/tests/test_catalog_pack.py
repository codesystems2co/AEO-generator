import unittest

from app.services.catalog_apply import apply_pack, read_block
from app.services.catalog_offer import PRODUCT_NAME, catalog_offer, queue_window
from app.services.catalog_product import PRODUCT_URL, catalog_product_url
from app.services.catalog_pack import build_pack


class OfferTest(unittest.TestCase):
    def test_catalog_pack_is_optional_until_the_order_line_exists(self):
        offer = catalog_offer(
            order_lines=["AEO / SEO y Optimizador de Búsqueda"],
            host="https://arkiphere.cloud",
            platforms=["odoo"],
        )
        self.assertEqual(offer["product"], PRODUCT_NAME)
        self.assertTrue(offer["optional"])
        self.assertTrue(offer["payable"])
        self.assertFalse(offer["owned"])
        self.assertEqual(offer["host"], "https://arkiphere.cloud")
        self.assertEqual(offer["platforms"], ["odoo"])
        self.assertEqual(catalog_product_url(offer["owned"]), PRODUCT_URL)
        self.assertIn("/shop/product-catalog-aeo-and-seo-pack-with-ia-110", PRODUCT_URL)

    def test_same_host_and_connection_unlock_the_catalog_assistant(self):
        offer = catalog_offer(
            order_lines=["Product Catalog AEO and SEO pack With IA"],
            host="https://shop.example",
            platforms=["odoo", "woocommerce"],
        )
        self.assertTrue(offer["owned"])
        self.assertEqual(offer["platforms"], ["odoo", "woocommerce"])


class QueueTest(unittest.TestCase):
    def test_window_shows_six_and_only_one_analyzing(self):
        pending = [{"id": i, "name": f"P{i}"} for i in range(1, 12)]
        window = queue_window(pending, active_id=3)
        self.assertEqual(len(window), 6)
        self.assertEqual(sum(1 for row in window if row["state"] == "analyzing"), 1)
        self.assertEqual(window[2]["state"], "analyzing")


class PackTest(unittest.TestCase):
    def test_aeo_data_questions_are_about_the_offer_and_keep_the_price(self):
        pack = build_pack(
            {
                "id": 15,
                "name": "AEO data",
                "description": "Servicio que prepara la ficha del comercio para que los buscadores lean el nombre y la descripción de esta oferta.",
                "url": "https://arkiphere.cloud/shop/aeo-data-15",
                "price": 49.0,
                "currency": "USD",
            },
            locale="es",
        )
        self.assertGreaterEqual(len(pack["seo"]["title"]), 30)
        self.assertLessEqual(len(pack["seo"]["title"]), 60)
        self.assertIn("AEO data", pack["seo"]["title"])
        self.assertGreaterEqual(len(pack["seo"]["meta_description"]), 120)
        self.assertLessEqual(len(pack["seo"]["meta_description"]), 160)
        self.assertEqual(pack["seo"]["canonical"], "https://arkiphere.cloud/shop/aeo-data-15")
        self.assertEqual(pack["price"], 49.0)
        questions = [item["question"] for item in pack["faq"]]
        self.assertTrue(any("AEO data" in q for q in questions))
        self.assertFalse(any("motores de búsqueda" in q for q in questions))
        self.assertEqual(pack["schema"]["@type"], "Product")
        self.assertEqual(pack["schema"]["offers"]["price"], 49.0)

    def test_empty_name_is_refused(self):
        with self.assertRaises(ValueError):
            build_pack({"name": "  ", "description": "texto", "url": "https://shop.example/p"})


class _MemoryShop:
    def __init__(self, platform, product, fields):
        self.platform = platform
        self.fields = set(fields)
        self.product = dict(product)
        self.writes = []

    def read_block(self, offset, limit):
        rows = [self.product]
        return rows[offset:offset + limit], 1

    def read_product(self, product_id):
        if product_id != self.product["id"]:
            raise KeyError(product_id)
        return dict(self.product)

    def write_product(self, product_id, values):
        if product_id != self.product["id"]:
            raise KeyError(product_id)
        unknown = set(values) - self.fields
        if unknown:
            raise KeyError(sorted(unknown))
        self.writes.append(dict(values))
        self.product.update(values)


def _product():
    return {
        "id": 15,
        "name": "AEO data",
        "description": "Servicio que prepara la ficha del comercio para que los buscadores lean el nombre y la descripción de esta oferta concreta.",
        "url": "https://shop.example/shop/aeo-data-15",
        "price": 49.0,
        "currency": "USD",
        "link_rewrite": "aeo-data",
    }


class PlatformApplyTest(unittest.TestCase):
    def test_each_platform_writes_native_fields_and_reads_them_back(self):
        cases = {
            "odoo": ["website_meta_title", "website_meta_description", "website_meta_keywords", "website_description"],
            "prestashop": ["meta_title", "meta_description", "description", "link_rewrite"],
            "woocommerce": [
                "description",
                "short_description",
                "_yoast_wpseo_title",
                "_yoast_wpseo_metadesc",
            ],
        }
        for platform, fields in cases.items():
            with self.subTest(platform=platform):
                product = _product()
                if platform == "woocommerce":
                    product["short_description"] = "Resumen corto del cliente — no tocar."
                shop = _MemoryShop(platform, product, fields)
                rows, total = read_block(shop, 0, 20)
                self.assertEqual(total, 1)
                self.assertEqual(rows[0]["id"], 15)
                pack = build_pack(shop.read_product(15), locale="es")
                first = apply_pack(shop, 15, pack, owned=True)
                self.assertTrue(first["ok"], first)
                saved = shop.read_product(15)
                self.assertTrue(first["evaluate"]["ok"], first["evaluate"])
                self.assertEqual(saved["price"], 49.0)
                self.assertIn("¿Qué incluye AEO data?", str(saved))
                if platform == "prestashop":
                    self.assertEqual(saved["link_rewrite"], "aeo-data")
                if platform == "woocommerce":
                    self.assertNotIn("name", shop.writes[0])
                    self.assertNotIn("short_description", shop.writes[0])
                    self.assertEqual(
                        saved["short_description"],
                        "Resumen corto del cliente — no tocar.",
                    )
                    self.assertIn("_yoast_wpseo_title", shop.writes[0])
                second = apply_pack(shop, 15, pack, owned=True)
                self.assertEqual(str(shop.read_product(15)).count("¿Qué incluye AEO data?"), 1)
                self.assertTrue(second["ok"])

    def test_apply_without_the_paid_line_does_not_write(self):
        shop = _MemoryShop("odoo", _product(), ["website_meta_title", "website_description"])
        pack = build_pack(shop.read_product(15), locale="es")
        result = apply_pack(shop, 15, pack, owned=False)
        self.assertFalse(result["ok"])
        self.assertEqual(shop.writes, [])

    def test_unknown_product_is_rejected(self):
        shop = _MemoryShop("odoo", _product(), ["website_meta_title", "website_description"])
        pack = build_pack(_product(), locale="es")
        with self.assertRaises(KeyError):
            apply_pack(shop, 99, pack, owned=True)


if __name__ == "__main__":
    unittest.main()
