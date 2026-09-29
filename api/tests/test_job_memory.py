import unittest

from app.services.job_memory import append_archive, heuristic_reading, previous_work, public_snapshot
from app.services.job_memory import _parse_reading


class JobMemoryTest(unittest.TestCase):
    def test_snapshot_keeps_the_report_and_drops_the_secret(self):
        snap = public_snapshot(
            {
                "generated_at": "2026-09-24T12:00:00+00:00",
                "sale_order_name": "S00247",
                "host": "arkiphere.cloud",
                "fingerprint": {"inject": False, "title": True},
                "changelog": {"solved": ["Título del comercio"], "left": ["Publicado en la tienda"]},
                "progress": {"percent": 75},
                "payload": {
                    "connection": {"connected": True, "api_key": "hidden-secret", "username": "admin"},
                    "inject": {"ok": False, "customer_message": "Odoo rechazó el acceso."},
                    "pack": {"seo": {"title": "Arkiphere", "keywords": ["Odoo"]}, "aeo": {"suggested_title": "Arkiphere"}},
                },
            }
        )
        self.assertEqual(snap["seo"]["title"], "Arkiphere")
        self.assertEqual(snap["inject"]["message"], "Odoo rechazó el acceso.")
        self.assertNotIn("api_key", snap)
        self.assertNotIn("hidden-secret", str(snap))

    def test_same_fingerprint_does_not_add_another_archive(self):
        first = append_archive([], {"fingerprint": {"title": True}, "order": "S00247"})
        second = append_archive(first, {"fingerprint": {"title": True}, "order": "S00247"})
        self.assertEqual(len(second), 1)

    def test_next_interaction_names_the_old_block_and_what_closed(self):
        previous = {
            "changelog": {"left": ["Publicado en la tienda"]},
            "inject": {"ok": False, "message": "Odoo rechazó el acceso."},
        }
        reading = heuristic_reading(
            previous,
            {"solved": ["Publicado en la tienda"], "left": ["Etapa siguiente: Google Merchant"]},
            "es",
        )
        self.assertTrue(reading["ready"])
        self.assertIn("Publicado en la tienda", reading["summary"])
        self.assertIn("Odoo rechazó el acceso.", reading["summary"])
        self.assertNotIn("Merchant", reading["summary"])
        self.assertNotIn("\n", reading["summary"])

    def test_last_saved_cycle_is_the_previous_work(self):
        same = previous_work(
            [],
            [{"fingerprint": {"title": False}}, {"fingerprint": {"title": True, "inject": False}}],
            {"title": True, "inject": False},
            "es",
        )
        self.assertNotIn("Título del comercio", same["changelog"]["left"])
        self.assertIn("Publicado en la tienda", same["changelog"]["left"])

        advanced = previous_work(
            [],
            [{"fingerprint": {"title": True, "inject": False}}],
            {"title": True, "inject": True},
            "es",
        )
        self.assertIn("Publicado en la tienda", advanced["changelog"]["left"])

    def test_engine_reply_is_one_paragraph(self):
        parsed = _parse_reading(
            '{"summary": "Después de otras interacciones, quedó hecho lo que antes no se pudo: Publicado en la tienda."}'
        )
        self.assertIn("Publicado en la tienda", parsed["summary"])
        listed = _parse_reading('{"summary": "[\'Conexión de la tienda\']"}')
        self.assertEqual(listed["summary"], "Conexión de la tienda")

    def test_nothing_new_does_not_repeat_the_open_list(self):
        reading = heuristic_reading(
            {"changelog": {"left": ["Etapa siguiente: Google Merchant"]}, "inject": {"ok": True}},
            {"solved": [], "left": ["Etapa siguiente: Google Merchant y tarjetas de Shopping"]},
            "es",
        )
        self.assertNotIn("Merchant", reading["summary"])
        self.assertIn("no completó nada", reading["summary"])


if __name__ == "__main__":
    unittest.main()
