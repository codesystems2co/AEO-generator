import unittest

from app.services.aeo_block import (
    END,
    START,
    detect_injection,
    has_injected_block,
    merge_block,
    render_faq_html,
    strip_block,
)
from app.services.catalog_pack import build_pack, faq_html
from app.services.odoo_inject import inject_website_seo


class AeoBlockTest(unittest.TestCase):
    def test_append_then_refresh_keeps_client_text(self):
        client = "<p>Texto del cliente intacto.</p>"
        first = merge_block(client, "<details><summary>Q1</summary><p>A1</p></details>")
        self.assertTrue(first.startswith(client))
        self.assertIn(START, first)
        self.assertIn(END, first)
        self.assertEqual(detect_injection(first)["action"], "refresh_block")
        second = merge_block(first, "<details><summary>Q2</summary><p>A2</p></details>")
        self.assertEqual(second.count(START), 1)
        self.assertIn("Q2", second)
        self.assertNotIn("Q1", second)
        self.assertEqual(strip_block(second), client)

    def test_legacy_catalog_markers_are_upgraded(self):
        legacy = "<p>Body</p>\n<!-- aeo-catalog -->\nold\n<!-- /aeo-catalog -->"
        upgraded = merge_block(legacy, "<p>new</p>")
        self.assertIn(START, upgraded)
        self.assertNotIn("aeo-catalog", upgraded)
        self.assertEqual(strip_block(upgraded), "<p>Body</p>")

    def test_details_summary_is_the_default_accordion(self):
        html = render_faq_html(
            [{"question": "¿Qué incluye X?", "answer": "Incluye Y."}],
            {"@type": "FAQPage"},
        )
        self.assertIn("<details>", html)
        self.assertIn("<summary>¿Qué incluye X?</summary>", html)
        self.assertIn("application/ld+json", html)
        self.assertTrue(has_injected_block(merge_block("", html)))


class CatalogFaqHtmlTest(unittest.TestCase):
    def test_pack_uses_details_and_epic_markers_on_apply_path(self):
        pack = build_pack(
            {
                "id": 1,
                "name": "Producto demo",
                "description": "Descripción corta del producto para metas y preguntas frecuentes de la ficha.",
                "url": "https://shop.example/shop/producto-demo-1",
                "price": 10.0,
                "currency": "EUR",
            }
        )
        self.assertIn("<details>", pack["faq_html"])
        self.assertIn("<summary>", pack["faq_html"])
        marked = merge_block("<p>Cliente</p>", pack["faq_html"])
        self.assertIn(START, marked)
        self.assertEqual(faq_html(pack["faq"], pack["schema"]), pack["faq_html"])


class OdooSeoNoFallbackTest(unittest.TestCase):
    def test_missing_target_is_an_explicit_error(self):
        result = inject_website_seo(
            {"url": "https://example.invalid", "database": "db", "username": "u", "api_key": "k"},
            {"title": "Titulo de prueba SEO meta largo", "meta_description": "x" * 130},
            target=None,
        )
        self.assertFalse(result["ok"])
        self.assertIn("Destino no encontrado", result["message"])
        self.assertNotIn("primer", (result.get("message") or "").lower())


class OdooRollbackGuardTest(unittest.TestCase):
    def test_rollback_requires_product_id(self):
        from app.services.odoo_inject import rollback_product_aeo

        result = rollback_product_aeo(
            {"url": "https://example.invalid", "database": "db", "username": "u", "api_key": "k"},
            0,
        )
        self.assertFalse(result["ok"])
        self.assertIn("Destino no encontrado", result["message"])


if __name__ == "__main__":
    unittest.main()
