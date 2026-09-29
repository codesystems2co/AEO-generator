"""Catalog report is a separate tree and a second PDF in one download."""
import unittest
import zipfile
from io import BytesIO

from app.services.catalog_pack import build_pack
from app.services.catalog_report import (
    CATALOG_FIELD_NAMES,
    build_catalog_tree,
    bundle_reports,
    render_catalog_pdf,
)
from app.services.pdf_report_service import render_job_pdf


def _product(name="AEO data"):
    return {
        "id": 15,
        "name": name,
        "description": "Servicio que prepara la ficha del comercio para que los buscadores lean el nombre y la descripción de esta oferta concreta.",
        "url": "https://arkiphere.cloud/shop/aeo-data-15",
        "price": 49.0,
        "currency": "USD",
    }


class CatalogTreeTest(unittest.TestCase):
    def test_tree_names_the_real_written_field(self):
        pack = build_pack(_product(), locale="es")
        cases = {
            "odoo": "website_meta_title",
            "prestashop": "meta_title",
            "woocommerce": "_yoast_wpseo_title",
        }
        for platform, field in cases.items():
            with self.subTest(platform=platform):
                tree = build_catalog_tree(
                    [
                        {
                            **_product(),
                            "pack": pack,
                            "written": {
                                field: pack["seo"]["title"],
                                CATALOG_FIELD_NAMES[platform]["meta"]: pack["seo"]["meta_description"],
                            },
                            "platform": platform,
                        }
                    ],
                    complete=False,
                )
                blob = str(tree)
                self.assertIn(field, blob)
                self.assertIn("AEO data", blob)
                self.assertIn("¿Qué incluye AEO data?", blob)
                self.assertTrue(tree[0]["incomplete"])

    def test_bundle_delivers_general_and_catalog_pdfs(self):
        general = render_job_pdf(
            {
                "locale": "es",
                "sale_order_name": "S00247",
                "host": "arkiphere.cloud",
                "site_url": "https://arkiphere.cloud",
                "summary": "Informe general del comercio.",
                "progress": {"percent": 80, "items": []},
                "tree": [],
                "payload": {},
            }
        )
        pack = build_pack(_product(), locale="es")
        catalog = render_catalog_pdf(
            {
                "locale": "es",
                "sale_order_name": "S00247",
                "host": "arkiphere.cloud",
                "complete": False,
                "products": [
                    {
                        **_product(),
                        "pack": pack,
                        "written": {"website_meta_title": pack["seo"]["title"]},
                        "platform": "odoo",
                    }
                ],
            }
        )
        zipped = bundle_reports(general, catalog, locale="es", order="S00247", host="arkiphere.cloud")
        archive = zipfile.ZipFile(BytesIO(zipped))
        names = archive.namelist()
        self.assertTrue(any(name.startswith("informe-optimizator-") and name.endswith(".pdf") for name in names))
        self.assertTrue(any(name.startswith("informe-catalogo-") and name.endswith(".pdf") for name in names))
        catalog_pdf = archive.read([name for name in names if name.startswith("informe-catalogo-")][0])
        self.assertIn(b"AEO data", catalog_pdf)
        self.assertIn("parcial".encode("utf-8"), catalog_pdf.lower())


if __name__ == "__main__":
    unittest.main()
