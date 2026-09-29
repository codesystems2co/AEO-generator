import unittest

from app.services.job_changelog import append_cycle, compare_cycles, fingerprint


class JobChangelogTest(unittest.TestCase):
    def test_first_cycle_lists_what_this_report_closed_and_what_stays_open(self):
        current = fingerprint(
            {
                "connection": {"connected": True},
                "google_connected": True,
                "pack": {"seo": {"title": "Arkiphere", "meta_description": "PaaS", "keywords": ["odoo"]}},
                "inject": {"ok": False},
                "google": {"gaps": [{"name": "sitemap.xml", "passed": True}, {"name": "robots.txt", "passed": False, "virtual_passed": True}]},
            }
        )
        change = compare_cycles(None, current, "es")
        self.assertTrue(change["first"])
        self.assertIn("Título del comercio", change["solved"])
        self.assertIn("Publicado en la tienda", change["left"])
        self.assertIn("Archivo robots", change["left"])
        self.assertTrue(any("Merchant" in item for item in change["left"]))
        self.assertFalse(any("producto" in item.lower() for item in change["left"]))
        self.assertFalse(any("product" in item.lower() for item in change["left"]))

    def test_second_cycle_shows_what_was_open_and_what_closed(self):
        previous = {"connect": True, "google": True, "title": False, "meta": False, "keywords": False, "inject": False, "sitemap": True, "robots": True}
        current = dict(previous)
        current["title"] = True
        current["meta"] = True
        change = compare_cycles(previous, current, "es")
        self.assertFalse(change["first"])
        self.assertIn("Título del comercio", change["solved"])
        self.assertNotIn("Título del comercio", change["before"])
        self.assertNotIn("Título del comercio", change["left"])
        self.assertNotIn("Conexión de la tienda", change["before"])
        self.assertIn("Palabras clave", change["left"])
        self.assertNotIn("Palabras clave", change["before"])
        self.assertNotIn("Palabras clave", change["solved"])
        self.assertEqual(change["left"].count("Palabras clave"), 1)
        self.assertIn("Publicado en la tienda", change["left"])
        self.assertNotIn("Mapa del sitio", change["left"])

    def test_same_fingerprint_does_not_add_another_cycle(self):
        first = append_cycle([], {"connect": True}, "2026-09-23T10:00:00+00:00")
        second = append_cycle(first, {"connect": True}, "2026-09-23T11:00:00+00:00")
        self.assertEqual(len(second), 1)
        third = append_cycle(second, {"connect": True, "title": True}, "2026-09-23T12:00:00+00:00")
        self.assertEqual(len(third), 2)


if __name__ == "__main__":
    unittest.main()
