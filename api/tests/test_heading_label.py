import unittest

from app.services.pack_service import build_tree, heading_label


class HeadingLabelTest(unittest.TestCase):
    def test_object_uses_the_text(self):
        self.assertEqual(
            heading_label({"level": 1, "text": "¿Qué es Arkiphere Cloud?"}),
            "¿Qué es Arkiphere Cloud?",
        )

    def test_printed_object_uses_the_text(self):
        raw = "{'level': 2, 'text': 'Facturación IA'}"
        self.assertEqual(heading_label(raw), "Facturación IA")

    def test_plain_heading_stays_plain(self):
        self.assertEqual(heading_label("Introducción"), "Introducción")

    def test_tree_shows_heading_text(self):
        tree = build_tree(
            "Arkiphere",
            {
                "suggested_title": "Arkiphere",
                "structured_sections": [
                    {"level": 2, "text": "Prueba gratuita"},
                    "{'level': 2, 'text': 'Facturación IA'}",
                ],
            },
            {"title": "Arkiphere", "keywords": [], "score": {}},
        )
        h2 = tree[0]["children"][-1]
        labels = [child["label"] for child in h2["children"]]
        self.assertEqual(labels, ["Prueba gratuita", "Facturación IA"])


if __name__ == "__main__":
    unittest.main()
